from sqlmodel import Field, SQLModel, create_engine
from core.env_core import get_env_variable, Envs, load_env_file

from core.logging_core import setup_logger

#Import Table Models
from model.user_model import User

# Set up the logger for this module
logger = setup_logger(__name__)
# Load environment variables from .env file
load_env_file()

postgres_url = get_env_variable(Envs.POSTGRES_URL)

engine = create_engine(postgres_url, echo=True, future=True)

def create_db():
    """
    Create the database and tables if they do not exist.
    """
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database and tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise e
    finally:
        engine.dispose()
        logger.info("Database connection closed.")