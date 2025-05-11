from typing import BinaryIO
from uuid import UUID

from fastapi import HTTPException, Response, status
from pydantic import ValidationError
from pydantic.v1.datetime_parse import parse_datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db_core import get_db_session
from core.fief_core import FiefHttpClient
from core.logging_core import setup_logger
from core.minio_core import default_bucket_name, upload_bytes_to_bucket
from handler.user_folder_handler import create_user_folder_handler
from model.enum.fief_type_webhook import FiefTypeWebhook
from model.user_model import User
from service.user_service import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_id,
    update_user,
    user_update_profile_image_url,
)

logger = setup_logger(__name__)

MISSING_USER_ID_ERROR = "Webhook payload missing user ID in 'data'."
BUCKET_NAME = default_bucket_name
PROFILE_IMAGE_SIZE = 512 * 1024  # 512 KB


async def get_user_by_id_handler(user_id: UUID) -> User:
    """
    Handler to retrieve a user by their ID.
    """
    try:
        async with get_db_session() as session:
            user = await get_user_by_id(session, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found.",
                )
            return user
    except Exception as e:
        logger.exception(f"Error retrieving user by ID {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving user.",
        ) from e

async def user_update_profile_image_url_handler(
        user_id: UUID,
        data: BinaryIO,
        filename: str,
) -> User:
    """
    Handler to update the user's profile image URL.
    """
    try:
        object_name = f"{user_id}/profile_images/{filename}"
        upload_bytes_to_bucket(BUCKET_NAME, data, object_name, PROFILE_IMAGE_SIZE)
        async with get_db_session() as session:
            user = await user_update_profile_image_url(session, user_id, object_name)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found.",
                )
            return user
    except ValueError as e:
        logger.exception(f"Validation error updating profile image URL for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=("Validation error: %s", str(e)),
        ) from e
    except Exception as e:
        logger.exception(f"Error updating profile image URL for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating profile image URL.",
        ) from e

async def create_user_handler(user_data: User) -> User:
    """
    Handler to create a new user.
    """
    try:
        async with get_db_session() as session:
            try:
                user = await create_user(session, user_data)
                await create_user_folder_handler(
                    user_id=user.id,
                    name="Default",
                )
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating user: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal Server Error") from e

    except ValueError as e:
        logger.exception("Validation error creating user %s: %s",
                         getattr(user_data, "email", ""), e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=("Validation error: %s", str(e)),
        ) from e
    except Exception as e:
        logger.exception("Error creating user %s: %s",
                         getattr(user_data, "email", ""), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user",
        ) from e

async def handle_user_webhook(payload: dict, session: AsyncSession):
    """
    Parses the webhook payload and uses the user service to manage users.
    """
    try:
        webhook_type = payload.get("type")
        user_data_payload = payload.get("data", {})
        user_id_str = user_data_payload.get("id")

        if not user_id_str:
            raise ValueError("Webhook payload missing user ID in 'data'.")
        user_id = UUID(user_id_str)

        user_model_data = {
            "id": user_id,
            "email": user_data_payload.get("email"),
            "username": user_data_payload.get("email", "").split("@")[0],
            "email_verified": user_data_payload.get("email_verified", False),
            "is_active": user_data_payload.get("is_active", True),
            "created_at": user_data_payload.get("created_at"),
            "updated_at": user_data_payload.get("updated_at"),
            "tenant_id": UUID(user_data_payload["tenant_id"])
            if user_data_payload.get("tenant_id")
            else None,
        }
        user_model_data = {k: v for k, v in user_model_data.items() if v is not None}

        if webhook_type == FiefTypeWebhook.USER_CREATED.value:
            user = await create_user_handler(user_model_data)
            if user:
                logger.info(f"User creation handled via service: {user.id}")
            else:
                logger.info(f"User creation handled via service for {user_id}, but user not found.")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        elif webhook_type == FiefTypeWebhook.USER_UPDATED.value:
            updated_user = update_user(session, user_id, user_model_data)
            if updated_user:
                logger.info(f"User update handled via service: {updated_user.id}")
            else:
                logger.info(
                    f"User update handled via service for {user_id}, "
                    f"but user not found or no changes."
                )
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        elif webhook_type == FiefTypeWebhook.USER_DELETED.value:
            deleted = delete_user(session, user_id)
            if deleted:
                logger.info(f"User deletion handled via service: {user_id}")
            else:
                logger.info(f"User deletion handled via service for {user_id}, but user not found.")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        else:
            logger.warning(f"Unknown webhook type received: {webhook_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown webhook type: {webhook_type}",
            )

    except (ValueError, KeyError, TypeError, ValidationError) as e:
        logger.error(f"Error processing user webhook payload: {e}. Payload: {payload}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {e}",
        ) from e
    except Exception as e:
        logger.exception(f"Error handling user webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing user webhook.",
        ) from e

async def get_all_users_handler() -> list[User]:
    """
    Handler to retrieve all users.
    """
    try:
        async with get_db_session() as session:
            users = await get_all_users(session)
            return users
    except Exception as e:
        logger.exception(f"Error retrieving all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving all users.",
        ) from e

def construct_user_model_data(user: dict) -> User:
    user_id = UUID(user["id"])
    return User(
        id=user_id,
        email=user.get("email"),
        username=user.get("email", "").split("@")[0],
        email_verified=user.get("email_verified", False),
        is_active=user.get("is_active", True),
        created_at=parse_datetime(user.get("created_at")),
        updated_at=parse_datetime(user.get("updated_at")),
        tenant_id=UUID(user["tenant_id"]) if user.get("tenant_id") else None,
    )


async def sync_users_handler() -> None:
    try:
        fief_client = FiefHttpClient()
        users = fief_client.get_all_users()
        all_local_users = await get_all_users_handler()
        local_user_ids = {str(existing_user.id) for existing_user in all_local_users} \
            if all_local_users else set()

        for user in users["results"]:
            user_external_id = user.get("id")
            if not user_external_id:
                raise ValueError(MISSING_USER_ID_ERROR)
            if user_external_id in local_user_ids:
                continue
            user_data = construct_user_model_data(user)
            await create_user_handler(user_data)
    except Exception as e:
        logger.error(f"An error occurred while syncing users: {str(e)}")
        raise
