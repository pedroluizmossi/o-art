from sqlmodel import Session
from model.user_model import User
from uuid import UUID
from model.enum.fief_type_webhook import FiefTypeWebhook
from core.logging_core import setup_logger
from fastapi import HTTPException, status

logger = setup_logger(__name__)

def handle_user_webhook(payload: dict, session: Session):
    """
    Parses the webhook payload and inserts a new user into the database.

    Args:
        payload (dict): The webhook payload.
        session (Session): The database session.
    """
    try:
        # Extrai os dados do payload
        type = payload.get("type")
        user_data = payload.get("data", {})
        user = User(
            id=UUID(user_data["id"]),
            email=user_data["email"],
            username=user_data["email"].split("@")[0],  # Usa o prefixo do email como username
            email_verified=user_data["email_verified"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"],
            tenant_id=UUID(user_data["tenant_id"]) if user_data.get("tenant_id") else None
        )

        if type == FiefTypeWebhook.USER_CREATED.value:
            user.insert(session)
            logger.info(f"User created: {user}")
            return None
        elif type == FiefTypeWebhook.USER_UPDATED.value:
            user.update(session)
            logger.info(f"User updated: {user}")
            return None
        elif type == FiefTypeWebhook.USER_DELETED.value:
            user.delete(session)
            logger.info(f"User deleted: {user}")
            return None
        else:
            logger.warning(f"Unknown webhook type: {type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown webhook type: {type}"
            )
    except Exception as e:
        logger.error(f"Error handling user webhook: {e}")
        return e