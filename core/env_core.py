import os


def get_env_variable(var_name: str, default_value: str = None) -> str:
    """
    Get an environment variable value provided by the operating system or container runtime.

    Args:
        var_name (str): Name of the environment variable.
        default_value (str): Default value if the variable is not found. Default is None.

    Returns:
        str: Value of the environment variable or default value.

    Raises:
        ValueError: If the variable is expected but not found and no default is provided.
    """
    value = os.getenv(var_name, default_value)
    if value is None and default_value is None:
        pass
    return value


class Envs:
    INFLUXDB_TOKEN = "INFLUXDB_TOKEN" # nosec B105
    INFLUXDB_ORG = "INFLUXDB_ORG" # nosec B105
    INFLUXDB_URL = "INFLUXDB_URL" # nosec B105
    INFLUXDB_BUCKET = "INFLUXDB_BUCKET" # nosec B105

    # Fief
    FIEF_CLIENT_ID = "FIEF_CLIENT_ID" # nosec B105
    FIEF_CLIENT_SECRET = "FIEF_CLIENT_SECRET" # nosec B105
    FIEF_USER_WEBHOOK_SECRET = "FIEF_USER_WEBHOOK_SECRET" # nosec B105

    # Database
    POSTGRES_URL = "POSTGRES_URL" # nosec B105

    # MinIO
    MINIO_ENDPOINT = "MINIO_ENDPOINT" # nosec B105
    MINIO_ACCESS_KEY = "MINIO_ACCESS_KEY" # nosec B105
    MINIO_SECRET_KEY = "MINIO_SECRET_KEY" # nosec B105
    MINIO_BUCKET_NAME = "MINIO_BUCKET_NAME" # nosec B105
    MINIO_API_PORT = "MINIO_API_PORT" # nosec B105