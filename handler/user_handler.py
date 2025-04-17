from sqlmodel import Session
from model.user_model import User
from uuid import UUID
from model.enum.fief_type_webhook import FiefTypeWebhook
from core.logging_core import setup_logger

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
        return user
    except Exception as e:
        logger.error(f"Error handling user webhook: {e}")
        return e