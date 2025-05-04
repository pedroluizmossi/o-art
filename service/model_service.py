import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.model_model import Model, ModelCreate

logger = setup_logger(__name__)

MODELS_JSON_PATH = "models.json"

class ModelNotFound(Exception):
    """Custom exception for 'model' not found."""
    def __init__(self, model_id: UUID):
        self.model_id = model_id
        super().__init__(f"Model with ID {model_id} not found.")

async def create_model(session: AsyncSession, model_data: ModelCreate) -> Model:
    """Adds a new model to the database."""
    try:
        now = datetime.now(timezone.utc)
        model = Model(
            **model_data.model_dump(),
            created_at=now,
            updated_at=now
        )

        session.add(model)
        await session.commit()
        await session.refresh(model)
        logger.info("Model created successfully: %s", model.id)
        return model
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating model %s: %s", model_data.name, e)
        raise e

async def get_all_models(session: AsyncSession) -> list[Model]:
    """Retrieves all models from the database."""
    try:
        statement = select(Model)
        models = await session.exec(statement)
        models = models.all()
        return models
    except Exception as e:
        logger.exception("Error retrieving all models: %s", e)
        raise e

async def get_model_by_id(session: AsyncSession, model_id: UUID) -> Optional[Model]:
    """Retrieves a model by its ID."""
    try:
        statement = select(Model).where(Model.id == model_id)
        model = await session.exec(statement)
        model = model.first()
        if not model:
            logger.warning("Model with ID %s not found.", model_id)
            raise ModelNotFound(model_id)
        return model
    except Exception as e:
        logger.exception("Error retrieving model by ID %s: %s", model_id, e)
        raise e

async def update_model(session: AsyncSession,
                       model_id: UUID, model_update_data: dict) -> Optional[Model]:
    """Updates an existing model identified by model_id with data from model_update_data."""
    try:
        model = await get_model_by_id(session, model_id)
        if not model:
            logger.warning("Model with ID %s not found for update.", model_id)
            raise ModelNotFound(model_id)

        updated = False
        for key, value in model_update_data.items():
            if hasattr(model, key) and getattr(model, key) != value:
                setattr(model, key, value)
                updated = True

        if updated:
            model.updated_at = datetime.now(timezone.utc)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            logger.info("Model updated successfully: %s", model.id)
            return model
        else:
            logger.info("No changes made to the model %s.", model.id)
            return model
    except Exception as e:
        await session.rollback()
        logger.exception("Error updating model %s: %s", model_id, e)
        raise e

async def delete_model(session: AsyncSession, model_id: UUID) -> bool:
    """Deletes a model from the database."""
    try:
        model = await get_model_by_id(session, model_id)
        if not model:
            logger.warning("Model with ID %s not found for deletion.", model_id)
            raise ModelNotFound(model_id)

        await session.delete(model)
        await session.commit()
        logger.info("Model deleted successfully: %s", model_id)
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error deleting model %s: %s", model_id, e)
        raise e

async def seed_model_from_json(session, json_path):
    with open(json_path, encoding="utf-8") as f:
        models_data = json.load(f)

    for model_data in models_data:
        name = model_data.get("name")
        exists = await session.exec(select(Model).where(Model.name == name))
        exists = exists.first()
        if not exists:
            session.add(Model(**model_data))
            logger.info(f"Model '{name}' inserted.")
        else:
            logger.info(f"Model '{name}' already exists. Skipping insertion.")
    await session.commit()

