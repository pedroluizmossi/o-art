from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from core.env_core import Envs, get_env_variable
from core.fief_core import FiefHttpClient
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

async_engine = create_async_engine(
    postgres_url,
    echo=False,
    future=True
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

async def create_db():
    """
    Create the database and tables if they do not exist.
    """
    async def async_create_all():
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    try:
        await async_create_all()
        logger.info("Database and tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise e
    finally:
        # Dispose of engine properly for async usage
        await async_engine.dispose()
        logger.info("Database connection closed.")

@asynccontextmanager
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

