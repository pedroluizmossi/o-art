import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import load_only
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.workflow_model import Workflow, WorkflowCreate

logger = setup_logger(__name__)

WORKFLOWS_JSON_PATH = "workflows.json"

class WorkflowNotFound(Exception):
    """Custom exception for workflow not found."""
    def __init__(self, workflow_id: UUID):
        self.workflow_id = workflow_id
        super().__init__(f"Workflow with ID {workflow_id} not found.")

async def create_workflow(session: AsyncSession, workflow_data: WorkflowCreate) -> Workflow:
    """Adds a new workflow to the database."""
    try:
        now = datetime.now(timezone.utc)
        workflow = Workflow(
            **workflow_data.model_dump(),
            created_at=now,
            updated_at=now
        )

        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        logger.info("Workflow created successfully: %s", workflow.id)
        return workflow
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating workflow %s: %s",
                         getattr(workflow_data, "name", ""), e)
        raise e


async def get_all_workflows(session: AsyncSession) -> list[Workflow]:
    """Retrieves all workflows from the database."""
    try:
        statement = select(Workflow)
        workflows = await session.exec(statement)
        workflows = workflows.all()
        return workflows
    except Exception as e:
        logger.exception("Error retrieving all workflows: %s", e)
        raise e

async def get_all_workflows_simplified(session: AsyncSession) -> list[Workflow]:
    """Retrieves all workflows from the database."""
    try:
        statement = select(Workflow).options(
            load_only(
                Workflow.id,
                Workflow.name,
                Workflow.description,
                Workflow.model_type,
                Workflow.model_id,
                Workflow.created_at,
            )
        )
        workflows = await session.exec(statement)
        workflows = workflows.all()
        return workflows
    except Exception as e:
        logger.exception("Error retrieving all workflows: %s", e)
        raise e


async def get_workflow_by_id(session: AsyncSession, workflow_id: UUID) -> Optional[Workflow]:
    """Retrieves a workflow by its ID."""
    try:
        statement = select(Workflow).where(Workflow.id == workflow_id)
        workflow = await session.exec(statement)
        workflow = workflow.first()
        if not workflow:
            logger.warning("Workflow with ID %s not found.", workflow_id)
            raise WorkflowNotFound(workflow_id)
        return workflow
    except Exception as e:
        logger.exception("Error retrieving workflow %s: %s", workflow_id, e)
        raise e



async def update_workflow(session: AsyncSession,
                          workflow_id: UUID,
                          workflow_update_data: dict) -> Optional[Workflow]:
    try:
        workflow = await get_workflow_by_id(session, workflow_id)
        if not workflow:
            logger.warning("Workflow with ID %s not found for update.", workflow_id)
            raise WorkflowNotFound(workflow_id)

        updated = False
        for key, value in workflow_update_data.items():
            if hasattr(workflow, key) and getattr(workflow, key) != value:
                setattr(workflow, key, value)
                updated = True

        if updated:
            workflow.updated_at = datetime.now(timezone.utc)
            session.add(workflow)
            await session.commit()
            await session.refresh(workflow)
            logger.info("Workflow updated successfully: %s", workflow.id)
            return workflow
        else:
            logger.info("No changes made to the workflow %s.", workflow.id)
            return workflow
    except Exception as e:
        await session.rollback()
        logger.exception("Error updating workflow %s: %s", workflow_id, e)
        raise e

async def delete_workflow(session: AsyncSession, workflow_id: UUID) -> bool:
    """Deletes a workflow from the database."""
    try:
        workflow = await get_workflow_by_id(session, workflow_id)
        if not workflow:
            logger.warning("Workflow with ID %s not found for deletion.", workflow_id)
            raise WorkflowNotFound(workflow_id)

        await session.delete(workflow)
        await session.commit()
        logger.info("Workflow deleted successfully: %s", workflow_id)
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error deleting workflow %s: %s", workflow_id, e)
        raise e

async def seed_workflow_from_json(session, json_path):
    with open(json_path, encoding="utf-8") as f:
        workflows_data = json.load(f)

    for workflow_data in workflows_data:
        name = workflow_data.get("name")
        exists = await session.exec(select(Workflow).where(Workflow.name == name))
        exists = exists.first()
        if not exists:
            session.add(Workflow(**workflow_data))
            print(f"Workflow '{name}' inserted.")
        else:
            print(f"Workflow '{name}' already exists. Skipping insertion.")
    await session.commit()