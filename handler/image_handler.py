import json
import os
import re
from typing import Any, List, Optional

from fastapi import HTTPException, status

from comfy.comfy_core import ComfyUIError, execute_workflow
from core.logging_core import setup_logger

logger = setup_logger(__name__)

WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "comfy", "workflows")


def replace_placeholders(obj, params):
    """Função recursiva para substituir placeholders em qualquer estrutura."""
    if isinstance(obj, dict):
        return {k: replace_placeholders(v, params) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_placeholders(item, params) for item in obj]
    elif isinstance(obj, str):
        match = re.fullmatch(r"\{\{(\w+)\}\}", obj)
        if match:
            key = match.group(1)
            return params.get(key, obj)
        else:

            def replacer(m):
                return str(params.get(m.group(1), m.group(0)))

            return re.sub(r"\{\{(\w+)\}\}", replacer, obj)
    else:
        return obj


def load_and_populate_workflow(workflow_name: str, params: dict[str, Any]) -> (dict[str, Any], str):
    workflow_path = os.path.join(WORKFLOW_DIR, workflow_name)
    if not os.path.exists(workflow_path):
        logger.error("Workflow file not found: %s", workflow_path)
        raise FileNotFoundError(f"Workflow '{workflow_name}' not found.")

    try:
        with open(workflow_path, encoding="utf-8") as f:
            workflow_template = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse workflow JSON file %s: %s", workflow_path, e)
        raise ValueError(f"Invalid JSON in workflow file '{workflow_name}'.") from e
    except Exception as e:
        logger.error("Failed to read workflow file %s: %s", workflow_path, e)
        raise OSError(f"Could not read workflow file '{workflow_name}'.") from e

    populated_workflow_dict = replace_placeholders(workflow_template, params)

    logger.debug(
        "Populated workflow for job %s: %s",
        params.get("job_id", "N/A"),
        json.dumps(populated_workflow_dict, indent=2),
    )

    output_node_id = None
    save_image_nodes = []
    for node_id, node_data in populated_workflow_dict.items():
        if (
            isinstance(node_data.get("_meta", {}).get("title"), str)
            and "{{output_node_id}}" in node_data["_meta"]["title"]
        ):
            if output_node_id is None:
                output_node_id = node_id
                logger.info(
                    "Designated output node '{{output_node_id}}' found: Node %s",
                    node_id,
                )
            else:
                logger.warning(
                    "Multiple nodes tagged with '{{output_node_id}}' found in workflow '%s'. Using the first one: %s",
                    workflow_name,
                    output_node_id,
                )
        if node_data.get("class_type") == "SaveImage":
            save_image_nodes.append(node_id)

    if not output_node_id:
        logger.warning(
            "No node explicitly marked with '{{output_node_id}}' in workflow '%s'. Will look for SaveImage nodes.",
            workflow_name,
        )
        if save_image_nodes:
            output_node_id = save_image_nodes[0]
            logger.info("Using first SaveImage node as output: Node %s", output_node_id)
        else:
            logger.error(
                "No '{{output_node_id}}' placeholder and no SaveImage nodes found in workflow '%s'. Cannot determine output.",
                workflow_name,
            )
            raise ValueError(
                f"Workflow '{workflow_name}' does not define an output node ('{{output_node_id}}' or SaveImage type)."
            )

    return populated_workflow_dict, output_node_id


async def handle_generate_image(
    user_id: str, job_id: str, workflow_name: str, params: dict[str, Any]
) -> Optional[dict[str, List[bytes]]]:
    logger.info(
        f"Handling image generation for user {user_id}, job {job_id}, workflow {workflow_name}"
    )
    logger.debug(f"Received parameters: {params}")

    try:
        populated_workflow, designated_output_node_id = load_and_populate_workflow(
            workflow_name, params
        )

        all_outputs = await execute_workflow(user_id, job_id, populated_workflow)

        if not all_outputs:
            logger.warning(
                f"Workflow {workflow_name} executed for job {job_id} but returned no outputs from ComfyUI."
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image generation failed: No output received from ComfyUI backend.",
            )

        if designated_output_node_id in all_outputs:
            output_images = all_outputs[designated_output_node_id]
            if (
                isinstance(output_images, list)
                and output_images
                and isinstance(output_images[0], bytes)
            ):
                logger.info(
                    f"Successfully generated {len(output_images)} image(s) from node {designated_output_node_id} for job {job_id}."
                )
                return {designated_output_node_id: output_images}
            else:
                logger.warning(
                    f"Designated output node {designated_output_node_id} for job {job_id} did not contain valid image data."
                )

        logger.warning(
            f"Designated output node {designated_output_node_id} not found in results or had no images for job {job_id}. Searching other nodes."
        )
        for node_id, output_data in all_outputs.items():
            if isinstance(output_data, list) and output_data and isinstance(output_data[0], bytes):
                logger.info(
                    f"Found image output in fallback node {node_id} for job {job_id}. Returning this output."
                )
                return {node_id: output_data}

        logger.error(
            f"No image output found in any node for job {job_id} with workflow {workflow_name}."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image generation failed: ComfyUI backend did not produce any image output.",
        )

    except FileNotFoundError as e:
        logger.error(f"Workflow file error for job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as e:  # Captura erros de load_and_populate
        logger.error(f"Workflow definition or parameter error for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow or parameter error: {e}",
        )
    except ComfyUIError as e:
        logger.error(f"ComfyUI backend error for job {job_id}: {e}")
        if e.status_code == 400:
            detail = f"ComfyUI validation error: {e.details or str(e)}"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        else:
            detail = f"ComfyUI backend failed: {e}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    except Exception as e:
        logger.exception(f"Unexpected error in handle_generate_image for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during image generation.",
        )
