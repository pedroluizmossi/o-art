from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest
from minio import S3Error

from core.env_core import Envs
from core.minio_core import create_minio_client, create_bucket_if_missing, create_default_bucket, list_all_buckets, \
    upload_file_to_bucket, upload_bytes_to_bucket, download_file_from_bucket


def test_create_minio_client_success():
    with patch("core.minio_core.get_env_variable") as mock_get_env_variable, \
            patch("core.minio_core.Minio") as mock_minio:
        mock_get_env_variable.side_effect = lambda key: {
            Envs.MINIO_ENDPOINT: "http://localhost:9000",
            Envs.MINIO_ACCESS_KEY: "test_access_key",
            Envs.MINIO_SECRET_KEY: "test_secret_key"
        }.get(key, None)
        create_minio_client()
        mock_minio.assert_called_once_with(
            "http://localhost:9000",
            access_key="test_access_key",
            secret_key="test_secret_key",
            secure=False
        )


def test_create_minio_client_missing_env_variable():
    with patch("core.minio_core.get_env_variable",
               side_effect=ValueError("Required env variable missing")) as mock_get_env_variable:
        with pytest.raises(ValueError, match="Required env variable missing"):
            create_minio_client()
        mock_get_env_variable.assert_called()

def test_create_bucket_if_missing_creates_new_bucket():
    minio_client = MagicMock()
    with patch("core.minio_core.minio_client", minio_client):
        minio_client.bucket_exists.return_value = False
        minio_client.make_bucket.return_value = None

        create_bucket_if_missing("test-bucket")

        minio_client.bucket_exists.assert_called_once_with("test-bucket")
        minio_client.make_bucket.assert_called_once_with("test-bucket")


def test_create_bucket_if_missing_bucket_already_exists():
    minio_client = MagicMock()
    with patch("core.minio_core.minio_client", minio_client), patch(
            "core.minio_core.logger"
    ) as logger:
        minio_client.bucket_exists.return_value = True

        create_bucket_if_missing("existing-bucket")

        minio_client.bucket_exists.assert_called_once_with("existing-bucket")
        minio_client.make_bucket.assert_not_called()
        logger.info.assert_called_once_with("Bucket %s already exists.", "existing-bucket")


def test_create_bucket_if_missing_raises_s3_error():
    minio_client = MagicMock()
    with patch("core.minio_core.minio_client", minio_client), patch(
            "core.minio_core.logger"
    ) as logger:
        minio_client.bucket_exists.side_effect = S3Error(
            "ERR", "Bucket error", "resource", "request_id", "host_id", "response"
        )

        with pytest.raises(S3Error):
            create_bucket_if_missing("error-bucket")

        minio_client.bucket_exists.assert_called_once_with("error-bucket")
        logger.error.assert_called_once_with("Error creating bucket: %", minio_client.bucket_exists.side_effect)

def test_create_default_bucket_bucket_does_not_exist():
    with patch("core.minio_core.minio_client") as mock_minio_client, patch("core.minio_core.logger") as mock_logger:
        mock_minio_client.bucket_exists.return_value = False
        mock_minio_client.make_bucket = MagicMock()

        create_default_bucket()

        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.make_bucket.assert_called_once()
        mock_logger.info.assert_called_with("Bucket %s created successfully.",
                                            mock_minio_client.make_bucket.call_args[0][0])


def test_create_default_bucket_bucket_exists():
    with patch("core.minio_core.minio_client") as mock_minio_client, patch("core.minio_core.logger") as mock_logger:
        mock_minio_client.bucket_exists.return_value = True

        create_default_bucket()

        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.make_bucket.assert_not_called()
        mock_logger.info.assert_called_with("Bucket %s already exists.",
                                            mock_minio_client.bucket_exists.call_args[0][0])


def test_list_all_buckets_success():
    mock_minio_client = MagicMock()
    mock_bucket_1 = MagicMock()
    mock_bucket_2 = MagicMock()
    mock_bucket_1.name = "bucket1"
    mock_bucket_2.name = "bucket2"
    mock_minio_client.list_buckets.return_value = [mock_bucket_1, mock_bucket_2]

    with patch("core.minio_core.minio_client", mock_minio_client), patch("core.minio_core.logger") as mock_logger:
        list_all_buckets()
        mock_minio_client.list_buckets.assert_called_once()
        mock_logger.error.assert_not_called()


def test_list_all_buckets_empty():
    mock_minio_client = MagicMock()
    mock_minio_client.list_buckets.return_value = []

    with patch("core.minio_core.minio_client", mock_minio_client), patch("core.minio_core.logger") as mock_logger:
        list_all_buckets()
        mock_minio_client.list_buckets.assert_called_once()
        mock_logger.error.assert_not_called()


def test_list_all_buckets_error():
    mock_minio_client = MagicMock()
    mock_minio_client.list_buckets.side_effect = S3Error(
        "ERR", "Bucket error", "resource", "request_id", "host_id", "response"
    )

    with patch("core.minio_core.minio_client", mock_minio_client), patch("core.minio_core.logger") as mock_logger:
        with pytest.raises(S3Error):
            list_all_buckets()
        mock_minio_client.list_buckets.assert_called_once()
        mock_logger.error.assert_called_once()

def test_upload_file_to_bucket_success():
    bucket_name = "test-bucket"
    file_path = "/path/to/test-file.txt"
    object_name = "test-file.txt"

    minio_client_mock = MagicMock()
    logger_mock = MagicMock()

    with patch("core.minio_core.minio_client", minio_client_mock), patch("core.minio_core.logger", logger_mock):
        upload_file_to_bucket(bucket_name, file_path, object_name)

        minio_client_mock.fput_object.assert_called_once_with(bucket_name, object_name, file_path)
        logger_mock.info.assert_called_once_with("File %s uploaded to bucket %.", file_path, bucket_name)


def test_upload_file_to_bucket_s3_error():
    bucket_name = "test-bucket"
    file_path = "/path/to/test-file.txt"
    object_name = "test-file.txt"

    minio_client_mock = MagicMock()
    logger_mock = MagicMock()
    test_error = S3Error(
        "ERR", "File upload error", "resource", "request_id", "host_id", "response"
    )

    with patch("core.minio_core.minio_client", minio_client_mock), patch("core.minio_core.logger", logger_mock):
        minio_client_mock.fput_object.side_effect = test_error

        with pytest.raises(S3Error) as excinfo:
            upload_file_to_bucket(bucket_name, file_path, object_name)

        assert excinfo.value == test_error
        minio_client_mock.fput_object.assert_called_once_with(bucket_name, object_name, file_path)
        logger_mock.error.assert_called_once_with("Error uploading file: %", test_error)

def test_upload_bytes_to_bucket_success():
    # Arrange
    bucket_name = "test-bucket"
    object_name = "test-object"
    data = BytesIO(b"test data")

    mock_minio_client = MagicMock()
    patched_logger = MagicMock()

    with patch("core.minio_core.minio_client", mock_minio_client), patch("core.minio_core.logger", patched_logger):
        # Act
        upload_bytes_to_bucket(bucket_name, data, object_name)

        # Assert
        mock_minio_client.put_object.assert_called_once()
        mock_minio_client.put_object.assert_called_with(bucket_name, object_name, data, len(data.getvalue()))
        patched_logger.info.assert_called_once_with(f"Bytes uploaded to bucket {bucket_name} as {object_name}.")


def test_upload_bytes_to_bucket_s3_error():
    # Arrange
    bucket_name = "test-bucket"
    object_name = "test-object"
    data = BytesIO(b"test data")

    mock_minio_client = MagicMock()
    patched_logger = MagicMock()

    with patch("core.minio_core.minio_client", mock_minio_client), patch("core.minio_core.logger", patched_logger):
        mock_minio_client.put_object.side_effect = S3Error(
            "ERR", "Upload error", "resource", "request_id", "host_id", "response"
        )

        # Act and Assert
        with pytest.raises(S3Error):
            upload_bytes_to_bucket(bucket_name, data, object_name)

        mock_minio_client.put_object.assert_called_once()
        patched_logger.error.assert_called_once()

def test_download_file_success():
    bucket_name = "test-bucket"
    object_name = "test-object"
    file_path = "test-path"

    mock_minio_client = MagicMock()
    with patch("core.minio_core.minio_client", mock_minio_client):
        with patch("core.minio_core.logger.info") as mock_logger:
            download_file_from_bucket(bucket_name, object_name, file_path)
            mock_minio_client.fget_object.assert_called_once_with(bucket_name, object_name, file_path)
            mock_logger.assert_called_once_with(f"File {file_path} downloaded from bucket {bucket_name}.")


def test_download_file_s3_error():
    bucket_name = "test-bucket"
    object_name = "test-object"
    file_path = "test-path"

    mock_minio_client = MagicMock()
    mock_minio_client.fget_object.side_effect = S3Error(
        "ERR", "Download error", "resource", "request_id", "host_id", "response"
    )

    with patch("core.minio_core.minio_client", mock_minio_client):
        with patch("core.minio_core.logger.error") as mock_logger:
            with pytest.raises(S3Error):
                download_file_from_bucket(bucket_name, object_name, file_path)
            mock_logger.assert_called_once()
            assert "Error downloading file:" in mock_logger.call_args[0][0]