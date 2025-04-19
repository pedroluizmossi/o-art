from typing import Optional

from sqlmodel import Session, select
from model.user_model import User
from uuid import UUID
from core.logging_core import setup_logger
from datetime import datetime, timezone # Import datetime/timezone

logger = setup_logger(__name__)

def create_user(session: Session, user_data: User) -> User:
    """Adds a new user to the database."""
    try:
        if not user_data.created_at:
             user_data.created_at = datetime.now(timezone.utc)
        user_data.updated_at = user_data.created_at

        session.add(user_data)
        session.commit()
        session.refresh(user_data)
        logger.info(f"User created successfully: {user_data.id}")
        return user_data
    except Exception as e:
        session.rollback()
        logger.exception(f"Error creating user {user_data.email}: {e}")
        raise e

def get_user_by_id(session: Session, user_id: UUID) -> Optional[User]:
    """Retrieves a user by their ID."""
    try:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        return user
    except Exception as e:
        logger.exception(f"Error retrieving user by ID {user_id}: {e}")
        raise e

def update_user(session: Session, user_id: UUID, user_update_data: dict) -> Optional[User]:
    """Updates an existing user identified by user_id with data from user_update_data."""
    try:
        user = get_user_by_id(session, user_id)
        if not user:
            logger.warning(f"User with ID {user_id} not found for update.")
            return None

        updated = False
        for key, value in user_update_data.items():
             if hasattr(user, key) and getattr(user, key) != value:
                  setattr(user, key, value)
                  updated = True

        if updated:
             user.updated_at = datetime.now(timezone.utc)
             session.add(user)
             session.commit()
             session.refresh(user)
             logger.info(f"User updated successfully: {user_id}")
        else:
             logger.info(f"No changes detected for user {user_id}. Update skipped.")

        return user
    except Exception as e:
        session.rollback()
        logger.exception(f"Error updating user {user_id}: {e}")
        raise e


def delete_user(session: Session, user_id: UUID) -> bool:
    """Deletes a user by their ID. Returns True if deleted, False otherwise."""
    try:
        user = get_user_by_id(session, user_id)
        if user:
            session.delete(user)
            session.commit()
            logger.info(f"User deleted successfully: {user_id}")
            return True
        else:
            logger.warning(f"User with ID {user_id} not found for deletion.")
            return False
    except Exception as e:
        session.rollback()
        logger.exception(f"Error deleting user {user_id}: {e}")
        raise e