import io
import json
import os
import uuid
from typing import Any, List, Optional, BinaryIO

from fastapi import HTTPException, status
from sqlmodel import Session

from core.db_core import engine
from core.minio_core import upload_bytes_to_bucket
from comfy.comfy_core import ComfyUIError, execute_workflow
from core.logging_core import setup_logger
from handler.workflow_handler import load_and_populate_workflow
from model.image_model import Image

logger = setup_logger(__name__)
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "comfy", "workflows")
BUCKET_NAME = "default"
FILE_EXTENSION = ".png"

def save_output_images_to_bucket(object_name: str, node_id: str, images: List[bytes]) -> None:
    if isinstance(images, list) and images and isinstance(images[0], bytes):
        logger.info(f"Saving output images to bucket for node {node_id}.")
        byte_stream = io.BytesIO()
        for img in images:
            byte_stream.write(img)
        byte_stream.seek(0)
        upload_bytes_to_bucket(
            BUCKET_NAME,
            byte_stream,
            f"{object_name}{FILE_EXTENSION}",
        )
    else:
        raise ValueError("Output images are not valid bytes list.")

async def handle_generate_image(
    user_id: str, job_id: str, workflow_id: uuid.UUID, params: dict[str, Any]
) -> Optional[dict[str, List[bytes]]]:
    logger.info(
        f"Handling image generation for user {user_id}, job {job_id}, workflow {workflow_id}"
    )
    logger.debug(f"Received parameters: {params}")
    object_name = f"{user_id}/{job_id}"

    try:
        populated_workflow, output_node_id = load_and_populate_workflow(
            workflow_id,
            params
        )
        workflow_outputs = await execute_workflow(user_id, job_id, populated_workflow)

        if not workflow_outputs:
            logger.warning(
                f"Workflow {workflow_id} executed for job {job_id} but returned no outputs from ComfyUI."
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image generation failed: No output received from ComfyUI backend.",
            )

        if output_node_id in workflow_outputs:
            output_images = workflow_outputs[output_node_id]
            try:
                save_output_images_to_bucket(object_name, output_node_id, output_images)
                image = Image(
                    url=f"{BUCKET_NAME}/{object_name}{FILE_EXTENSION}",
                    workflow_id=workflow_id,
                    user_id=user_id,
                    parameters=params,
                )
                with Session(engine) as session:
                    session.add(image)
                    session.commit()
                    session.refresh(image)
                logger.info(
                    f"Image saved successfully for job {job_id}: {image.id}"
                )
                return {output_node_id: output_images}
            except ValueError:
                logger.warning(
                    f"Designated output node {output_node_id} for job {job_id} did not contain valid image data."
                )

        logger.warning(
            f"Designated output node {output_node_id} not found or had no images for job {job_id}. Searching other nodes."
        )
        for node_id, images in workflow_outputs.items():
            try:
                save_output_images_to_bucket(user_id, job_id, node_id, images)
                logger.info(
                    f"Found image output in fallback node {node_id} for job {job_id}. Returning this output."
                )
                return {node_id: images}
            except ValueError:
                continue

        logger.error(
            f"No image output found in any node for job {job_id} with workflow {workflow_id}."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image generation failed: ComfyUI backend did not produce any image output.",
        )

    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
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