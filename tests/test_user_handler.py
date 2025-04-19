import pytest
from fastapi import HTTPException
from handler.user_handler import handle_user_webhook
from model.enum.fief_type_webhook import FiefTypeWebhook
from model.user_model import User  # Import User model
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID  # Import UUID


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def valid_payload():
    user_id = uuid4()
    tenant_id = uuid4()
    return {
        "type": FiefTypeWebhook.USER_CREATED.value,
        "data": {
            "id": str(user_id),
            "email": "test@example.com",
            "email_verified": True,
            "is_active": True,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "tenant_id": str(tenant_id),
        },
    }


def test_handle_user_webhook_user_created(mock_session, valid_payload):
    # Recrie o objeto User como ele seria dentro do handler para obter a string esperada
    user_data = valid_payload["data"]
    # Certifique-se que a lógica aqui (especialmente para username) corresponde à do handler
    expected_user_str = (
        f"User: {user_data['email'].split('@')[0]} (ID: {user_data['id']})"
    )
    expected_log_message = f"User created: {expected_user_str}"

    with (
        patch("handler.user_handler.User.insert") as mock_insert,
        patch("handler.user_handler.logger.info") as mock_logger,
    ):
        handle_user_webhook(valid_payload, mock_session)

        mock_insert.assert_called_once()
        mock_logger.assert_called_once_with(expected_log_message)


def test_handle_user_webhook_user_updated(mock_session, valid_payload):
    valid_payload["type"] = FiefTypeWebhook.USER_UPDATED.value
    user_data = valid_payload["data"]
    expected_user_str = (
        f"User: {user_data['email'].split('@')[0]} (ID: {user_data['id']})"
    )
    expected_log_message = f"User updated: {expected_user_str}"

    with (
        patch("handler.user_handler.User.update") as mock_update,
        patch("handler.user_handler.logger.info") as mock_logger,
    ):
        handle_user_webhook(valid_payload, mock_session)
        mock_update.assert_called_once()
        mock_logger.assert_called_once_with(
            expected_log_message
        )  # Atualize esta asserção também


def test_handle_user_webhook_user_deleted(mock_session, valid_payload):
    valid_payload["type"] = FiefTypeWebhook.USER_DELETED.value
    user_data = valid_payload["data"]
    # Crie a string esperada também para este teste
    expected_user_str = (
        f"User: {user_data['email'].split('@')[0]} (ID: {user_data['id']})"
    )
    expected_log_message = f"User deleted: {expected_user_str}"

    with (
        patch("handler.user_handler.User.delete") as mock_delete,
        patch("handler.user_handler.logger.info") as mock_logger,
    ):
        handle_user_webhook(valid_payload, mock_session)
        mock_delete.assert_called_once()
        mock_logger.assert_called_once_with(
            expected_log_message
        )  # Atualize esta asserção também


def test_handle_user_webhook_unknown_type(mock_session, valid_payload):
    valid_payload["type"] = "unknown.type"
    with patch("handler.user_handler.logger.warning") as mock_logger:
        with pytest.raises(HTTPException) as excinfo:
            handle_user_webhook(valid_payload, mock_session)
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Unknown webhook type: unknown.type"
        mock_logger.assert_called_once_with("Unknown webhook type: unknown.type")


def test_handle_user_webhook_unknown_type(mock_session, valid_payload):
    valid_payload["type"] = "unknown.type"
    with (
        patch("handler.user_handler.logger.warning") as mock_warning_logger,
        patch("handler.user_handler.logger.error") as mock_error_logger,
    ):  # Também mock o logger de erro
        result = handle_user_webhook(valid_payload, mock_session)

        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        assert result.detail == "Unknown webhook type: unknown.type"

        mock_warning_logger.assert_called_once_with(
            "Unknown webhook type: unknown.type"
        )
        mock_error_logger.assert_called_once()
