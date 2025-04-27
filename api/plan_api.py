import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from core.logging_core import setup_logger
from model.plan_model import Plan, PlanCreate

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/plan",
    tags=["plan"],
)


@router.get("/", response_model=List[Plan])
async def get_plans(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    pass

@router.post("/", response_model=Plan, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan: PlanCreate,
):
    pass