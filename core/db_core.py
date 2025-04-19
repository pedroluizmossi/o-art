from sqlmodel import Field, SQLModel, create_engine, Session
from core.env_core import get_env_variable, Envs

from core.logging_core import setup_logger

from dotenv import load_dotenv

load_dotenv()

# Set up the logger for this module
logger = setup_logger(__name__)
# Set up the database connection using SQLModel
postgres_url = get_env_variable(Envs.POSTGRES_URL)
if not postgres_url:
    logger.critical(
        "Database URL not found in environment variables "
        "(POSTGRES_URL). Cannot connect to database."
    )
    raise ValueError("Missing POSTGRES_URL environment variable.")

engine = create_engine(postgres_url, echo=False, future=True)


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


def get_session():
    with Session(engine) as session:
        yield session
