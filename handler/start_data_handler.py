from core.db_core import RESOURCE_POSTGRES_PATH, get_db_session
from core.logging_core import setup_logger
from handler.user_handler import sync_users_handler
from service.model_service import MODELS_JSON_PATH, seed_model_from_json
from service.workflow_service import seed_workflow_from_json, WORKFLOWS_JSON_PATH


logger = setup_logger(__name__)

async def initial_data():
    """
    Initialize the database with initial data.
    """
    try:
        await sync_users_handler()
    except Exception as e:
        logger.error(f"Error syncing users: {e}")
        raise e
    try:
        async with get_db_session() as session:
            await seed_model_from_json(session, RESOURCE_POSTGRES_PATH + MODELS_JSON_PATH)
            await seed_workflow_from_json(session, RESOURCE_POSTGRES_PATH + WORKFLOWS_JSON_PATH)
            await session.commit()
            logger.info("Initial data loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        raise e