from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.image_handler import (
    delete_image_handler,
    get_all_images_by_user_id_and_folder_id_handler,
    get_all_images_by_user_id_handler,
)

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/user/image",
    tags=["user"],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "User Image",
    "description": "User Image management endpoints.",
}


@router.get("/")
async def get_user_images(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),  # noqa: B008
):
    user_id = access_token_info["id"]
    try:
        images = await get_all_images_by_user_id_handler(user_id)
        return images
    except Exception as e:
        logger.error(f"Error retrieving images for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        ) from e

@router.get("/{folder_id}")
async def get_user_images_by_folder(
    folder_id: UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),  # noqa: B008
):
    user_id = access_token_info["id"]
    try:
        images = await get_all_images_by_user_id_and_folder_id_handler(user_id, folder_id)
        return images
    except Exception as e:
        logger.error(f"Error retrieving images for user {user_id} in folder {folder_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        ) from e

@router.delete("/{image_id}")
async def delete_user_image(
    image_id: UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),  # noqa: B008
):
    user_id = access_token_info["id"]
    try:
        await delete_image_handler(image_id)
        return {"message": "Image deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting image {image_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        ) from e