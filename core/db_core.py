from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from core.env_core import Envs, get_env_variable
from core.logging_core import setup_logger
from service.model_service import seed_model_from_json, MODELS_JSON_PATH
from service.workflow_service import seed_workflow_from_json, WORKFLOWS_JSON_PATH

load_dotenv()

# Set up the logger for this module
logger = setup_logger(__name__)
# Set up the database connection using SQLModel
postgres_url = get_env_variable(Envs.POSTGRES_URL)

RESOURCE_PATH = "./resources"
RESOURCE_POSTGRES_PATH = f"{RESOURCE_PATH}/postgres/"
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

def initial_data():
    """
    Initialize the database with initial data.
    """
    try:
        with Session(engine) as session:
            seed_model_from_json(session, RESOURCE_POSTGRES_PATH + MODELS_JSON_PATH)
            seed_workflow_from_json(session, RESOURCE_POSTGRES_PATH + WORKFLOWS_JSON_PATH)
            session.commit()
            logger.info("Initial data loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        raise e

