from dotenv import load_dotenv
from fief_client import FiefAsync

from core.config_core import Config
from core.env_core import Envs, get_env_variable
from core.logging_core import setup_logger

load_dotenv()
# Set up the logger for this module
logger = setup_logger(__name__)

config_instance = Config()
# Pega o domínio do config.ini
domain_address = config_instance.get("Fief", "domain", default="http://127.0.0.1:8001")

if not domain_address:
    logger.error("Fief domain not found in config.ini ([Fief] domain). Authentication might fail.")

fief = FiefAsync(
    domain_address,
    # Pega segredos do ambiente
    get_env_variable(Envs.FIEF_CLIENT_ID),
    get_env_variable(Envs.FIEF_CLIENT_SECRET),
)
