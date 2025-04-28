import uuid
from typing import List

from fastapi import APIRouter, Depends, Response, status
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.plan_handler import (
    get_all_plans_handler,
    create_plan_handler,
    get_plan_by_id_handler,
    delete_plan_handler,
    update_plan_handler,
)
from model.plan_model import Plan, PlanUpdate, PlanCreate

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/plan",
    tags=["plan"],
    dependencies=[Depends(auth.authenticated())],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "plan",
    "description": "Plan management endpoints.",
}

@router.get("/", response_model=List[Plan])
async def get_plans(
):
    """
    Lists all available plans.
    """
    return await get_all_plans_handler()

@router.get("/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: uuid.UUID,
):
    """
    Returns a specific plan by its ID.
    """
    plan = await get_plan_by_id_handler(plan_id)
    return plan

@router.post("/", response_model=Plan, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
):
    """
    Creates a new plan.
    """
    return await create_plan_handler(plan_data)

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
):
    """
    Deletes a specific plan by its ID.
    """
    await delete_plan_handler(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: uuid.UUID,
    plan_update_data: PlanUpdate,
):
    """
    Updates a specific plan by its ID.
    """
    plan = await update_plan_handler(plan_id, plan_update_data)
    return plan