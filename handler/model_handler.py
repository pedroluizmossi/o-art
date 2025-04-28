from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from model.model_model import Model, ModelCreate, ModelUpdate
from service.model_service import (
    ModelNotFound,
    create_model,
    delete_model,
    get_all_models,
    get_model_by_id,
    update_model,
)

logger = setup_logger(__name__)

async def get_all_models_handler() -> List[Model]:
    """
    Handler to retrieve all models.
    """
    try:
        async with get_db_session() as session:
            models = await get_all_models(session)
        return models
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving models",
        )

async def get_model_by_id_handler(model_id: UUID) -> Optional[Model]:
    """
    Handler to retrieve a model by its ID.
    Returns the model or raises an HTTP 404 if not found.
    """
    try:
        async with get_db_session() as session:
            model = await get_model_by_id(session, model_id)
        return model
    except ModelNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model with ID %s not found." % model_id,
        )
    except Exception as e:
        logger.exception("Unhandled error retrieving model %s: %s", model_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model with ID %s" % model_id,
        )

async def create_model_handler(model_data: ModelCreate) -> Model:
    """
    Handler to create a new model.
    """
    try:
        async with get_db_session() as session:
            model = await create_model(session, model_data)
        return model
    except ValueError as e:
        logger.exception("Validation error creating model %s: %s", getattr(model_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error: %s" % str(e),
        )
    except Exception as e:
        logger.exception("Error creating model %s: %s", getattr(model_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating model",
        )

async def update_model_handler(model_id: UUID, model_update_data: ModelUpdate) -> Optional[Model]:
    """
    Handler to update a model by its ID.
    """
    try:
        model_update_data = model_update_data.model_dump(exclude_unset=True)
        async with get_db_session() as session:
            model = await update_model(session, model_id, model_update_data)
        return model
    except ModelNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model with ID %s not found." % model_id,
        )
    except ValueError as e:
        logger.exception("Validation error updating model %s: %s", model_id, e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error: %s" % str(e),
        )
    except Exception as e:
        logger.exception("Error updating model %s: %s", model_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating model",
        )

async def delete_model_handler(model_id: UUID) -> None:
    """
    Handler to delete a model by its ID.
    """
    try:
        async with get_db_session() as session:
            await delete_model(session, model_id)
    except ModelNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model with ID %s not found." % model_id,
        )
    except Exception as e:
        logger.exception("Error deleting model %s: %s", model_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting model",
        )
