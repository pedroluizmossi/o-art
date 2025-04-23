import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from fief_client import FiefAccessTokenInfo
from pydantic import BaseModel, Field
from sqlmodel import Session

from api.auth_api import auth
from core.db_core import get_session
from core.logging_core import setup_logger

from handler.workflow_handler import get_all_workflows_handler


logger = setup_logger(__name__)

router = APIRouter(
    prefix="/workflow",
    tags=["workflow"],
)


@router.get("/")
async def get_workflows(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Endpoint to retrieve all workflows.
    """
    try:
        workflows = await get_all_workflows_handler()
        return workflows
    except Exception as e:
        logger.exception("Error retrieving workflows: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error retrieving workflows",
        )
    finally:
        logger.info("Session closed after retrieving workflows.")
