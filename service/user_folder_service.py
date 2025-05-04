from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.user_folder_model import UserFolder

logger = setup_logger(__name__)

async def create_user_folder(
    session: AsyncSession,
    user_id: UUID,
    name: str
) -> UserFolder:
    """
    Create a new user folder.
    """
    try:
        user_folder = UserFolder(
            name=name,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(user_folder)
        await session.commit()
        await session.refresh(user_folder)
        return user_folder
    except Exception as e:
        logger.error(f"Error creating user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folder(
    session: AsyncSession,
    user_id: UUID,
    folder_id: UUID
) -> Optional[UserFolder]:
    """
    Get a user folder by its ID.
    """
    try:
        statement = select(UserFolder).where(
            UserFolder.id == folder_id,
            UserFolder.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folders(
    session: AsyncSession,
    user_id: UUID
) -> list[UserFolder]:
    """
    Get all folders for a user.
    """
    try:
        statement = select(UserFolder).where(
            UserFolder.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting user folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def get_user_folder_by_name(
    session: AsyncSession,
    user_id: UUID,
    name: str
) -> Optional[UserFolder]:
    """
    Get a user folder by its name.
    """
    try:
        name = name.lower()
        statement = select(UserFolder).where(
            UserFolder.name.ilike(f"%{name}%"),
            UserFolder.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user folder by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e

async def delete_user_folder(
    session: AsyncSession,
    user_id: UUID,
    folder_id: UUID
) -> bool:
    """
    Delete a user folder.
    """
    try:
        user_folder = await get_user_folder(session, user_id, folder_id)
        if user_folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        await session.delete(user_folder)
        await session.commit()
        return True
    except HTTPException as e:
        logger.error(f"Error deleting user folder: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error deleting user folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error") from e