import uuid
from typing import Optional

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from model.user_folder_model import UserFolder
from service.user_folder_service import (
    create_user_folder,
    delete_user_folder,
    get_user_folder,
    get_user_folder_by_name,
    get_user_folders,
)

logger = setup_logger(__name__)

async def create_user_folder_handler(
    user_id: uuid.UUID,
    name: str,
) -> UserFolder:
    """
    Handler to create a new user folder.
    """
    try:
        async with get_db_session() as session:
            # Check if the folder name already exists
            existing_folder = await get_user_folder_by_name_handler(
                user_id=user_id,
                name=name
            )
            if existing_folder:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folder name already exists"
                )
            # Create the new folder
            user_folder = await create_user_folder(
                session=session,
                user_id=user_id,
                name=name
            )
            return user_folder
    except Exception as e:
        logger.error(f"Error creating user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folder_handler(
    user_id: uuid.UUID,
    folder_id: uuid.UUID
) -> Optional[UserFolder]:
    """
    Handler to get a user folder by its ID.
    """
    try:
        async with get_db_session() as session:
            user_folder = await get_user_folder(
                session=session,
                user_id=user_id,
                folder_id=folder_id
            )
            return user_folder
    except Exception as e:
        logger.error(f"Error getting user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folders_handler(
    user_id: uuid.UUID
) -> list[UserFolder]:
    """
    Handler to get all user folders.
    """
    try:
        async with get_db_session() as session:
            user_folders = await get_user_folders(
                session=session,
                user_id=user_id
            )
            return user_folders
    except Exception as e:
        logger.error(f"Error getting user folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folder_by_name_handler(
    user_id: uuid.UUID,
    name: str
) -> Optional[UserFolder]:
    """
    Handler to get a user folder by its name.
    """
    try:
        async with get_db_session() as session:
            user_folder = await get_user_folder_by_name(
                session=session,
                user_id=user_id,
                name=name
            )
            return user_folder
    except Exception as e:
        logger.error(f"Error getting user folder by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def delete_user_folder_handler(
    user_id: uuid.UUID,
    folder_id: uuid.UUID
) -> bool:
    """
    Handler to delete a user folder.
    """
    try:
        async with get_db_session() as session:
            result = await delete_user_folder(
                session=session,
                user_id=user_id,
                folder_id=folder_id
            )
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e