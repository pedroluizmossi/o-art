import os
from unittest.mock import patch

import pytest
from core.env_core import get_env_variable, Envs


def test_get_env_variable_existing_variable():
    with patch.dict(os.environ, {"TEST_ENV_VAR": "test_value"}):
        result = get_env_variable("TEST_ENV_VAR")
        assert result == "test_value"


def test_get_env_variable_non_existing_with_default():
    result = get_env_variable("NON_EXISTING_VAR", default_value="default_value")
    assert result == "default_value"


def test_get_env_variable_non_existing_without_default():
    with pytest.raises(ValueError):
        get_env_variable("NON_EXISTING_VAR")


def test_envs_influxdb_token():
    assert Envs.INFLUXDB_TOKEN == "INFLUXDB_TOKEN"


def test_envs_influxdb_org():
    assert Envs.INFLUXDB_ORG == "INFLUXDB_ORG"


def test_envs_influxdb_url():
    assert Envs.INFLUXDB_URL == "INFLUXDB_URL"


def test_envs_influxdb_bucket():
    assert Envs.INFLUXDB_BUCKET == "INFLUXDB_BUCKET"


def test_envs_fief_client_id():
    assert Envs.FIEF_CLIENT_ID == "FIEF_CLIENT_ID"


def test_envs_fief_client_secret():
    assert Envs.FIEF_CLIENT_SECRET == "FIEF_CLIENT_SECRET"


def test_envs_fief_user_webhook_secret():
    assert Envs.FIEF_USER_WEBHOOK_SECRET == "FIEF_USER_WEBHOOK_SECRET"


def test_envs_fief_api_url():
    assert Envs.FIEF_API_URL == "FIEF_API_URL"


def test_envs_fief_api_user_token():
    assert Envs.FIEF_API_USER_TOKEN == "FIEF_API_USER_TOKEN"


def test_envs_postgres_url():
    assert Envs.POSTGRES_URL == "POSTGRES_URL"


def test_envs_minio_endpoint():
    assert Envs.MINIO_ENDPOINT == "MINIO_ENDPOINT"


def test_envs_minio_access_key():
    assert Envs.MINIO_ACCESS_KEY == "MINIO_ACCESS_KEY"


def test_envs_minio_secret_key():
    assert Envs.MINIO_SECRET_KEY == "MINIO_SECRET_KEY"


def test_envs_minio_bucket_name():
    assert Envs.MINIO_BUCKET_NAME == "MINIO_BUCKET_NAME"


def test_envs_minio_api_port():
    assert Envs.MINIO_API_PORT == "MINIO_API_PORT"
