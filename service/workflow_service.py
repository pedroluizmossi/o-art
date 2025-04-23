import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from core.logging_core import setup_logger
from model.workflow_model import Workflow

logger = setup_logger(__name__)

WORKFLOWS_JSON_PATH = "workflows.json"

def create_workflow(session: Session, workflow_data: Workflow) -> Workflow:
    """Adds a new workflow to the database."""
    try:
        if not workflow_data.created_at:
            workflow_data.created_at = datetime.now(timezone.utc)
        workflow_data.updated_at = workflow_data.created_at

        session.add(workflow_data)
        session.commit()
        session.refresh(workflow_data)
        logger.info("Workflow created successfully: %s", workflow_data.id)
        return workflow_data
    except Exception as e:
        session.rollback()
        logger.exception("Error creating workflow %s: %s", getattr(workflow_data, "name", ""), e)
        raise e

def get_all_workflows(session: Session) -> list[Workflow]:
    """Retrieves all workflows from the database."""
    try:
        statement = select(Workflow)
        workflows = session.exec(statement).all()
        return workflows
    except Exception as e:
        logger.exception("Error retrieving all workflows: %s", e)
        raise e

def get_workflow_by_id(session: Session, workflow_id: UUID) -> Optional[Workflow]:
    """Retrieves a workflow by its ID."""
    try:
        statement = select(Workflow).where(Workflow.id == workflow_id)
        workflow = session.exec(statement).first()
        return workflow
    except Exception as e:
        logger.exception("Error retrieving workflow by ID %s: %s", workflow_id, e)
        raise e

def update_workflow(session: Session, workflow_id: UUID, workflow_update_data: dict) -> Optional[Workflow]:
    """Updates an existing workflow identified by workflow_id with data from workflow_update_data."""
    try:
        workflow = get_workflow_by_id(session, workflow_id)
        if not workflow:
            logger.warning("Workflow with ID %s not found for update.", workflow_id)
            return None

        updated = False
        for key, value in workflow_update_data.items():
            if hasattr(workflow, key) and getattr(workflow, key) != value:
                setattr(workflow, key, value)
                updated = True

        if updated:
            workflow.updated_at = datetime.now(timezone.utc)
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
            logger.info("Workflow updated successfully: %s", workflow.id)
            return workflow
        else:
            logger.info("No changes made to the workflow %s.", workflow.id)
            return workflow
    except Exception as e:
        session.rollback()
        logger.exception("Error updating workflow %s: %s", workflow_id, e)
        raise e

def delete_workflow(session: Session, workflow_id: UUID) -> bool:
    """Deletes a workflow from the database."""
    try:
        workflow = get_workflow_by_id(session, workflow_id)
        if not workflow:
            logger.warning("Workflow with ID %s not found for deletion.", workflow_id)
            return False

        session.delete(workflow)
        session.commit()
        logger.info("Workflow deleted successfully: %s", workflow_id)
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error deleting workflow %s: %s", workflow_id, e)
        raise e

def seed_workflow_from_json(session, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        workflows_data = json.load(f)

    for workflow_data in workflows_data:
        name = workflow_data.get("name")
        exists = session.exec(select(Workflow).where(Workflow.name == name)).first()
        if not exists:
            session.add(Workflow(**workflow_data))
            print(f"Workflow '{name}' inserted.")
        else:
            print(f"Workflow '{name}' already exists. Skipping insertion.")
    session.commit()