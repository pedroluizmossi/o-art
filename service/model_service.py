import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.model_model import Model

logger = setup_logger(__name__)

MODELS_JSON_PATH = "models.json"

async def create_model(session: AsyncSession, model_data: Model) -> Model:
    """Adds a new model to the database."""
    try:
        if not model_data.created_at:
            model_data.created_at = datetime.now(timezone.utc)
        model_data.updated_at = model_data.created_at

        session.add(model_data)
        await session.commit()
        await session.refresh(model_data)
        logger.info("Model created successfully: %s", model_data.id)
        return model_data
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating model %s: %s", model_data.name, e)
        raise e

async def get_model_by_id(session: AsyncSession, model_id: UUID) -> Optional[Model]:
    """Retrieves a model by its ID."""
    try:
        statement = select(Model).where(Model.id == model_id)
        model = await session.exec(statement)
        model = model.first()
        return model
    except Exception as e:
        logger.exception("Error retrieving model by ID %s: %s", model_id, e)
        raise e

async def update_model(session: AsyncSession, model_id: UUID, model_update_data: dict) -> Optional[Model]:
    """Updates an existing model identified by model_id with data from model_update_data."""
    try:
        model = await get_model_by_id(session, model_id)
        if not model:
            logger.warning("Model with ID %s not found for update.", model_id)
            return None

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
            return False

        await session.delete(model)
        await session.commit()
        logger.info("Model deleted successfully: %s", model_id)
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error deleting model %s: %s", model_id, e)
        raise e

async def seed_model_from_json(session, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
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

