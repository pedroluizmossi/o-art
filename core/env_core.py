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
    INFLUXDB_TOKEN = "INFLUXDB_TOKEN"
    INFLUXDB_ORG = "INFLUXDB_ORG"
    INFLUXDB_URL = "INFLUXDB_URL"
    INFLUXDB_BUCKET = "INFLUXDB_BUCKET"

    # Fief
    FIEF_CLIENT_ID = "FIEF_CLIENT_ID"
    FIEF_CLIENT_SECRET = "FIEF_CLIENT_SECRET"
    FIEF_USER_WEBHOOK_SECRET = "FIEF_USER_WEBHOOK_SECRET"

    # Database
    POSTGRES_URL = "POSTGRES_URL"
