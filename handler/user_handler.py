from uuid import UUID

from fastapi import HTTPException, Response, status
from pydantic import ValidationError
from sqlmodel import Session

from core.logging_core import setup_logger
from model.enum.fief_type_webhook import FiefTypeWebhook
from model.user_model import User
from service.user_service import create_user, delete_user, update_user

logger = setup_logger(__name__)


def handle_user_webhook(payload: dict, session: Session):
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
            user = User(**user_model_data)
            created_user = create_user(session, user)
            logger.info(f"User creation handled via service: {created_user.id}")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        elif webhook_type == FiefTypeWebhook.USER_UPDATED.value:
            updated_user = update_user(session, user_id, user_model_data)
            if updated_user:
                logger.info(f"User update handled via service: {updated_user.id}")
            else:
                logger.info(
                    f"User update handled via service for {user_id}, but user not found or no changes."
                )
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        elif webhook_type == FiefTypeWebhook.USER_DELETED.value:
            deleted = delete_user(session, user_id)
            if deleted:
                logger.info(f"User deletion handled via service: {user_id}")
            else:
                logger.info(
                    f"User deletion handled via service for {user_id}, but user not found."
                )
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
