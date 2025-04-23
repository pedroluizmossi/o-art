import io
import json
import os
import re
import uuid
from typing import Any, List, Optional, BinaryIO

from Crypto.Util.RFC1751 import binary
from fastapi import HTTPException, status

from core.minio_core import upload_bytes_to_bucket
from comfy.comfy_core import ComfyUIError, execute_workflow
from core.logging_core import setup_logger
from handler.workflow_handler import load_and_populate_workflow

logger = setup_logger(__name__)

WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "comfy", "workflows")


async def handle_generate_image(
    user_id: str, job_id: str, workflow_id: uuid.uuid4, params: dict[str, Any]
) -> Optional[dict[str, List[bytes]]]:
    logger.info(
        f"Handling image generation for user {user_id}, job {job_id}, workflow {workflow_id}"
    )
    logger.debug(f"Received parameters: {params}")

    try:
        populated_workflow, designated_output_node_id = load_and_populate_workflow(
            workflow_id, params
        )

        all_outputs = await execute_workflow(user_id, job_id, populated_workflow)

        if not all_outputs:
            logger.warning(
                f"Workflow {workflow_id} executed for job {job_id} but returned no outputs from ComfyUI."
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
                bytes_binaryio = io.BytesIO()
                for image in output_images:
                    bytes_binaryio.write(image)
                bytes_binaryio.seek(0)
                upload_bytes_to_bucket(
                    "default",
                    bytes_binaryio,
                    f"{user_id}/{job_id}.png",
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
            f"No image output found in any node for job {job_id} with workflow {workflow_id}."
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
            detail="Internal server error during image generation: " + str(e),
        )
