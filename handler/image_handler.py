import io
import json
import os
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from pydantic import ValidationError

from core.comfy.comfy_core import ComfyUIError, execute_workflow
from core.db_core import get_db_session
from core.logging_core import setup_logger
from core.minio_core import default_bucket_name, upload_bytes_to_bucket
from handler.user_handler import get_user_by_id_handler
from handler.workflow_handler import load_and_populate_workflow
from model.image_model import Image
from service.image_service import (
    create_image,
    delete_image,
    get_all_images_by_user_id,
    get_all_images_by_user_id_and_folder_id,
)

logger = setup_logger(__name__)
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "comfy", "workflows")
BUCKET_NAME = default_bucket_name
FILE_EXTENSION = ".png"

async def create_image_handler(
        url: Image.url,
        workflow_id: Image.workflow_id,
        user_id: Image.user_id,
        user_folder_id: Image.user_folder_id,
        parameters: Image.parameters,
) -> Image:
    """
    Handler to create a new image record in the database.
    """
    try:
        async with get_db_session() as session:
            image = Image(
                session=session,
                url=url,
                workflow_id=workflow_id,
                user_id=user_id,
                user_folder_id=user_folder_id,
                parameters=parameters
            )
            await create_image(session, image)
            return image
    except Exception as e:
        logger.error(f"Error creating image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e


async def get_all_images_by_user_id_handler(user_id: uuid.UUID) -> list[Image]:
    """
    Handler to get all images for a specific user.
    """
    try:
        async with get_db_session() as session:
            images = await get_all_images_by_user_id(session, user_id)
            return images
    except Exception as e:
        logger.error(f"Error retrieving images for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_all_images_by_user_id_and_folder_id_handler(
    user_id: uuid.UUID, folder_id: uuid.UUID
) -> list[Image]:
    """
    Handler to get all images for a specific user and folder.
    """
    try:
        async with get_db_session() as session:
            images = await get_all_images_by_user_id_and_folder_id(session, user_id, folder_id)
            return images
    except Exception as e:
        logger.error(f"Error retrieving images for user {user_id} in folder {folder_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def delete_image_handler(image_id: uuid.UUID) -> None:
    """
    Handler to delete an image by its ID.
    """
    try:
        async with get_db_session() as session:
            await delete_image(session, image_id)
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def save_output_images_to_bucket(object_name: str, node_id: str, images: list[bytes]) -> None:
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
    user_id: uuid.UUID,
        folder_id: uuid.UUID,
        job_id: str,
        workflow_id: uuid.UUID,
        params: dict[str, Any]
) -> Optional[dict[str, list[bytes]]]:
    logger.info(f"Handling image generation for user {user_id}, "
                f"job {job_id}, workflow {workflow_id}")
    logger.debug(f"Received parameters: {params}")
    object_name = f"{user_id}/{job_id}"

    try:
        user = await get_user_by_id_handler(user_id)
        plan_id = user.plan_id
        populated_workflow, output_node_id = await load_and_populate_workflow(
            workflow_id,
            params,
            plan_id
        )
        workflow_outputs = await execute_workflow(str(user_id), job_id, populated_workflow)

        if not workflow_outputs:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image generation failed: No output received from ComfyUI backend.",
            )

        return await process_output_images(
            object_name,
            job_id,
            workflow_id,
            workflow_outputs,
            output_node_id,
            folder_id,
            user_id,
            params
        )
    except HTTPException:
        raise
    except (OSError, ValueError, KeyError, ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Workflow definition or parameter error for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow or parameter error: {e}",
        ) from e
    except ComfyUIError as e:
        handle_comfyui_error(e, job_id)
    except Exception as e:
        logger.exception(f"Unexpected error in handle_generate_image for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during image generation: " + str(e),
        ) from e


async def process_output_images(
    object_name: str,
    job_id: str,
    workflow_id: uuid.UUID,
    workflow_outputs: dict[str, list[bytes]],
    output_node_id: Optional[str],
    folder_id: uuid.UUID,
    user_id: uuid.UUID,
    params: dict[str, Any],
) -> Optional[dict[str, list[bytes]]]:
    if output_node_id in workflow_outputs:
        return await get_output_images(
            object_name,
            output_node_id,
            workflow_outputs,
            job_id,
            workflow_id,
            folder_id,
            user_id,
            params
        )

    logger.warning(f"Designated output node {output_node_id} not found or had no images for job "
                   f"{job_id}. Searching fallback nodes.")
    for node_id, _images in workflow_outputs.items():
        try:
            return await get_output_images(
                object_name,
                node_id,
                workflow_outputs,
                job_id,
                workflow_id,
                folder_id,
                user_id,
                params
            )
        except ValueError:
            continue

    logger.error(f"No image output found in any node for job {job_id} with workflow {workflow_id}.")
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Image generation failed: ComfyUI backend did not produce any image output.",
    )


async def get_output_images(
    object_name: str,
    node_id: str,
    workflow_outputs: dict[str, list[bytes]],
    job_id: str,
    workflow_id: uuid.UUID,
    folder_id: uuid.UUID,
    user_id: uuid.UUID,
    params: dict[str, Any],
) -> dict[str, list[bytes]]:
    output_images = workflow_outputs[node_id]
    await save_output_images_to_bucket(object_name, node_id, output_images)
    url = f"{BUCKET_NAME}/{object_name}{FILE_EXTENSION}"
    await create_image_handler(
        url=url,
        workflow_id=workflow_id,
        user_id=user_id,
        user_folder_id=folder_id,
        parameters=params,
    )
    logger.info(f"Image created successfully for job {job_id} in node {node_id}.")
    return {node_id: output_images}


def handle_comfyui_error(e: ComfyUIError, job_id: str):
    logger.error(f"ComfyUI backend error for job {job_id}: {e}")
    if e.status_code == 400:
        detail = f"ComfyUI validation error: {e.details or str(e)}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from e
    else:
        detail = f"ComfyUI backend failed: {e}"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from e
