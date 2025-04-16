import os
from enum import Enum

import dotenv

def load_env_file(env_file_path: str = ".env") -> None:
    """
    Load environment variables from a .env file.

    Args:
        env_file_path (str): Path to the .env file. Default is ".env".
    """
    if os.path.exists(env_file_path):
        dotenv.load_dotenv(env_file_path)
    else:
        raise FileNotFoundError(f"The specified .env file does not exist: {env_file_path}")

def get_env_variable(var_name: str, default_value: str = None) -> str:
    """
    Get an environment variable value.

    Args:
        var_name (str): Name of the environment variable.
        default_value (str): Default value if the variable is not found. Default is None.

    Returns:
        str: Value of the environment variable or default value.
    """
    return os.getenv(var_name, default_value)

def set_env_variable(var_name: str, value: str) -> None:
    """
    Set an environment variable value.

    Args:
        var_name (str): Name of the environment variable.
        value (str): Value to set for the environment variable.
    """
    os.environ[var_name] = value

class Envs:
    """
    Enum class for environment variables.

    Attributes:
        INFLUXDB_TOKEN (str): Token for InfluxDB.
        INFLUXDB_ORG (str): Organization name for InfluxDB.
        INFLUXDB_URL (str): URL for InfluxDB.
    """
    INFLUXDB_TOKEN = "INFLUXDB_TOKEN"
    INFLUXDB_ORG = "INFLUXDB_ORG"
    INFLUXDB_URL = "INFLUXDB_URL"
    INFLUXDB_BUCKET = "INFLUXDB_BUCKET"
    FIEF_DOMAIN = "FIEF_DOMAIN"
    FIEF_CLIENT_ID = "FIEF_CLIENT_ID"
    FIEF_CLIENT_SECRET = "FIEF_CLIENT_SECRET"
    FIEF_USER_WEBHOOK_SECRET = "FIEF_USER_WEBHOOK_SECRET"

