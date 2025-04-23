import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from core.logging_core import setup_logger
from model.model_model import Model

logger = setup_logger(__name__)

MODELS_JSON_PATH = "models.json"

def create_model(session: Session, model_data: Model) -> Model:
    """Adds a new model to the database."""
    try:
        if not model_data.created_at:
            model_data.created_at = datetime.now(timezone.utc)
        model_data.updated_at = model_data.created_at

        session.add(model_data)
        session.commit()
        session.refresh(model_data)
        logger.info("Model created successfully: %s", model_data.id)
        return model_data
    except Exception as e:
        session.rollback()
        logger.exception("Error creating model %s: %s", model_data.name, e)
        raise e

def get_model_by_id(session: Session, model_id: UUID) -> Optional[Model]:
    """Retrieves a model by its ID."""
    try:
        statement = select(Model).where(Model.id == model_id)
        model = session.exec(statement).first()
        return model
    except Exception as e:
        logger.exception("Error retrieving model by ID %s: %s", model_id, e)
        raise e

def update_model(session: Session, model_id: UUID, model_update_data: dict) -> Optional[Model]:
    """Updates an existing model identified by model_id with data from model_update_data."""
    try:
        model = get_model_by_id(session, model_id)
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
            session.commit()
            session.refresh(model)
            logger.info("Model updated successfully: %s", model.id)
            return model
        else:
            logger.info("No changes made to the model %s.", model.id)
            return model
    except Exception as e:
        session.rollback()
        logger.exception("Error updating model %s: %s", model_id, e)
        raise e

def delete_model(session: Session, model_id: UUID) -> bool:
    """Deletes a model from the database."""
    try:
        model = get_model_by_id(session, model_id)
        if not model:
            logger.warning("Model with ID %s not found for deletion.", model_id)
            return False

        session.delete(model)
        session.commit()
        logger.info("Model deleted successfully: %s", model_id)
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error deleting model %s: %s", model_id, e)
        raise e

def seed_model_from_json(session, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    for model_data in models_data:
        name = model_data.get("name")
        exists = session.exec(select(Model).where(Model.name == name)).first()
        if not exists:
            session.add(Model(**model_data))
            print(f"Modelo '{name}' inserido.")
        else:
            print(f"Modelo '{name}' já existe. Pulando inserção.")
    session.commit()

