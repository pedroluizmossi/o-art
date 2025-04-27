from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.user_model import User

logger = setup_logger(__name__)


async def create_user(session: AsyncSession, user_data: User) -> User:
    """Adds a new user to the database."""
    try:
        if not user_data.created_at:
            user_data.created_at = datetime.now(timezone.utc)
        user_data.updated_at = user_data.created_at

        session.add(user_data)
        await session.commit()
        await session.refresh(user_data)
        logger.info("User created successfully: %s", user_data.id)
        return user_data
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating user %s: %s", user_data.email, e)
        raise e


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """Retrieves a user by their ID."""
    try:
        statement = select(User).where(User.id == user_id)
        user = await session.exec(statement)
        user = user.first()
        return user
    except Exception as e:
        logger.exception("Error retrieving user by ID %s: %s", user_id, e)
        raise e


async def update_user(session: AsyncSession, user_id: UUID, user_update_data: dict) -> Optional[User]:
    """Updates an existing user identified by user_id with data from user_update_data."""
    try:
        user = await get_user_by_id(session, user_id)
        if not user:
            logger.warning("User with ID %s not found for update.", user_id)
            return None

        updated = False
        for key, value in user_update_data.items():
            if hasattr(user, key) and getattr(user, key) != value:
                setattr(user, key, value)
                updated = True

        if updated:
            user.updated_at = datetime.now(timezone.utc)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("User updated successfully: %s", user_id)
        else:
            logger.info("No changes detected for user %s. Update skipped.", user_id)

        return user
    except Exception as e:
        await session.rollback()
        logger.exception("Error updating user %s: %s", user_id, e)
        raise e


async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
    """Deletes a user by their ID. Returns True if deleted, False otherwise."""
    try:
        user = await get_user_by_id(session, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            logger.info("User deleted successfully: %s", user_id)
            return True
        else:
            logger.warning("User with ID %s not found for deletion.", user_id)
            return False
    except Exception as e:
        await session.rollback()
        logger.exception("Error deleting user %s: %s", user_id, e)
        raise e
