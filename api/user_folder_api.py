import uuid

from fastapi import APIRouter, Depends

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.user_folder_handler import (
    create_user_folder_handler,
    delete_user_folder_handler,
    get_user_folder_by_name_handler,
    get_user_folder_handler,
    get_user_folders_handler,
)

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/user/folder",
    tags=["user"],
    dependencies=[Depends(auth.authenticated())],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "User Folder",
    "description": "User Folder management endpoints.",
}

@router.get("/")
async def get_user_folders(
    user_id: uuid.UUID
):
    """
    Lists all user folders for a specific user.
    :param user_id:
    :return:
    """
    user_folders = await get_user_folders_handler(user_id)
    return user_folders

@router.get("/{folder_id}")
async def get_user_folder(
    user_id: uuid.UUID,
    folder_id: uuid.UUID,
):
    """
    Returns a specific user folder by its ID.
    :param folder_id:
    :param user_id:
    :return:
    """
    user_folder = await get_user_folder_handler(user_id, folder_id)
    return user_folder

@router.get("/name/{folder_name}")
async def get_user_folder_by_name(
    user_id: uuid.UUID,
    folder_name: str
):
    """
    Returns a specific user folder by its name.
    :param folder_name:
    :param user_id:
    :return:
    """
    user_folder = await get_user_folder_by_name_handler(user_id, folder_name)
    return user_folder

@router.post("/", status_code=201)
async def create_user_folder(
    user_id: uuid.UUID,
    folder_name: str
):
    """
    Creates a new user folder.
    :param user_id:
    :param folder_name:
    :return:
    """
    user_folder = await create_user_folder_handler(user_id, folder_name)
    return user_folder

@router.delete("/{folder_id}", status_code=204)
async def delete_user_folder(
    user_id: uuid.UUID,
    folder_id: uuid.UUID
):
    """
    Deletes a specific user folder by its ID.
    :param folder_id:
    :param user_id:
    :return:
    """
    await delete_user_folder_handler(user_id, folder_id)

