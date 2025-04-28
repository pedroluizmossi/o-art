import uuid
from typing import List

from fastapi import APIRouter, Depends, Response, status

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.workflow_handler import (
    create_workflow_handler,
    delete_workflow_handler,
    get_all_workflows_handler,
    get_workflow_by_id_handler,
    update_workflow_handler,
)
from model.workflow_model import Workflow, WorkflowCreate, WorkflowUpdate

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/workflow",
    tags=["workflow"],
    dependencies=[Depends(auth.authenticated())],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "workflow",
    "description": "Workflow management endpoints.",
}


@router.get("/", response_model=List[Workflow])
async def get_workflows(
):
    """
    Lists all available workflows.
    """
    return await get_all_workflows_handler()

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: uuid.UUID,
):
    """
    Returns a specific workflow by its ID.
    """
    workflow = await get_workflow_by_id_handler(workflow_id)
    return workflow

@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
):
    """
    Creates a new workflow.
    """
    return await create_workflow_handler(workflow_data)

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: uuid.UUID,
):
    """
    Removes a workflow by ID.
    """
    await delete_workflow_handler(workflow_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: uuid.UUID,
    workflow_data: WorkflowUpdate,
):
    """
    Updates an existing workflow by ID.
    """
    workflow = await update_workflow_handler(workflow_id, workflow_data)
    return workflow