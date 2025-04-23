from typing import BinaryIO
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

from core.env_core import get_env_variable, Envs
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
            logger.info(f"Bucket S% created successfully.", bucket_name)
        else:
            logger.info(f"Bucket S% already exists.", bucket_name)
    except S3Error as e:
        logger.error(f"Error creating bucket: %", e)

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
        logger.error(f"Error listing buckets: %", e)
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
        logger.info(f"File S% uploaded to bucket S%.", file_path, bucket_name)
    except S3Error as e:
        logger.error(f"Error uploading file: S%", e)
        raise e


def upload_bytes_to_bucket(bucket_name: str, data: BinaryIO, object_name: str):
    """
    Upload bytes to a specified bucket in MinIO.

    Args:
        bucket_name (str): Name of the target bucket.
        data (BinaryIO): Binary stream to upload.
        object_name (str): Object name to use in MinIO.
    """
    try:
        pos = data.tell()
        data.seek(0, 2)
        size = data.tell()
        data.seek(pos)
        minio_client.put_object(bucket_name, object_name, data, size)
        logger.info(f"Bytes uploaded to bucket S% as S%.", bucket_name, object_name)
    except S3Error as e:
        logger.error(f"Error uploading bytes: %", e)
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
        logger.info(f"File S% downloaded from bucket S%.", file_path, bucket_name)
    except S3Error as e:
        logger.error(f"Error downloading file: %", e)
        raise e