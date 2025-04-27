import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.workflow_handler import (
    get_all_workflows_handler,
    create_workflow_handler,
    get_workflow_by_id_handler,
    delete_workflow_handler,
    update_workflow_handler,
)
from model.workflow_model import Workflow, WorkflowCreate, WorkflowUpdate

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/workflow",
    tags=["workflow"],
)

@router.get("/", response_model=List[Workflow])
async def get_workflows(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Lists all available workflows.
    """
    return await get_all_workflows_handler()

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: uuid.UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Returns a specific workflow by its ID.
    """
    workflow = await get_workflow_by_id_handler(workflow_id)
    return workflow

@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Creates a new workflow.
    """
    return await create_workflow_handler(workflow_data)

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: uuid.UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
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
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Updates an existing workflow by ID.
    """
    workflow = await update_workflow_handler(workflow_id, workflow_data)
    return workflow