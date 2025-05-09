from typing import BinaryIO

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

from core.env_core import Envs, get_env_variable
from core.logging_core import setup_logger

load_dotenv()

logger = setup_logger(__name__)

def create_minio_client():
    """
    Create and return a MinIO client instance using environment variables.
    """
    return Minio(
        get_env_variable(Envs.MINIO_ENDPOINT),
        access_key=get_env_variable(Envs.MINIO_ACCESS_KEY),
        secret_key=get_env_variable(Envs.MINIO_SECRET_KEY),
        secure=False,
    )

minio_client = create_minio_client()
default_bucket_name = get_env_variable(Envs.MINIO_BUCKET_NAME, "default")

def create_bucket_if_missing(bucket_name: str):
    """
    Create a bucket in MinIO if it does not already exist.
    Args:
        bucket_name (str): Name of the bucket to create.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info("Bucket %s created successfully.", bucket_name)
        else:
            logger.info("Bucket %s already exists.", bucket_name)
    except S3Error as e:
        logger.error("Error creating bucket: %", e)
        raise e

def create_default_bucket():
    """
    Create the default bucket in MinIO if it does not already exist.
    """
    create_bucket_if_missing(default_bucket_name)

def list_all_buckets():
    """
    List all buckets available in MinIO.
    """
    try:
        buckets = minio_client.list_buckets()
        for bucket in buckets:
            print(bucket.name)
    except S3Error as e:
        logger.error("Error listing buckets: %", e)
        raise e

def upload_file_to_bucket(bucket_name: str, file_path: str, object_name: str):
    """
    Upload a file to a specified bucket in MinIO.
    Args:
        bucket_name (str): Name of the target bucket.
        file_path (str): Local file path to upload.
        object_name (str): Object name to use in MinIO.
    """
    try:
        minio_client.fput_object(bucket_name, object_name, file_path)
        logger.info("File %s uploaded to bucket %.", file_path, bucket_name)
    except S3Error as e:
        logger.error("Error uploading file: %", e)
        raise e


def upload_bytes_to_bucket(
        bucket_name: str,
        data: BinaryIO,
        object_name: str,
        data_max_size: int = 10 * 1024 * 1024 # 10 MB
):
    """
    Upload bytes to a specified bucket in MinIO.

    Args:
        bucket_name (str): Name of the target bucket.
        data (BinaryIO): Binary stream to upload.
        object_name (str): Object name to use in MinIO.
        :param bucket_name: Bucket name to upload to.
        :param data: Binary stream to upload.
        :param object_name: Object name to use in MinIO.
        :param data_max_size: Maximum size of the data in bytes. Default is 10 MB.
    """
    if not binary_size_check(data, data_max_size):
        logger.error("Data size exceeds the maximum limit of % bytes.", data_max_size)
        raise ValueError(f"Data size exceeds the maximum limit of {data_max_size} bytes.")
    try:
        pos = data.tell()
        data.seek(0, 2)
        size = data.tell()
        data.seek(pos)
        minio_client.put_object(bucket_name, object_name, data, size)
        logger.info(f"Bytes uploaded to bucket {bucket_name} as {object_name}.")
    except S3Error as e:
        logger.error("Error uploading bytes: %", e)
        raise e


def download_file_from_bucket(bucket_name: str, object_name: str, file_path: str):
    """
    Download a file from a specified bucket in MinIO.
    Args:
        bucket_name (str): Name of the target bucket.
        object_name (str): Object name in MinIO.
        file_path (str): Local file path to save the downloaded file.
    """
    try:
        minio_client.fget_object(bucket_name, object_name, file_path)
        logger.info(f"File {file_path} downloaded from bucket {bucket_name}.")
    except S3Error as e:
        logger.error("Error downloading file: %", e)
        raise e


def binary_size_check(file: BinaryIO, max_size: int) -> bool:
    """
    Check if the size of a binary file exceeds a specified maximum size.

    Args:
        file (BinaryIO): The binary file to check.
        max_size (int): The maximum allowed size in bytes.

    Returns:
        bool: True if the file size is within the limit, False otherwise.
    """
    pos = file.tell()
    file.seek(0, 2)
    size = file.tell()
    file.seek(pos)
    return size <= max_size