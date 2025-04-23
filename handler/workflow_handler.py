import io
import json
import os
import re
from typing import Any, List, Optional, BinaryIO

from sqlmodel import Session, select
from fastapi import HTTPException, status
from core.logging_core import setup_logger
from service.workflow_service import get_all_workflows
from model.workflow_model import Workflow

logger = setup_logger(__name__)


async def get_all_workflows_handler(session: Session) -> List[Workflow]:
    """
    Handler to retrieve all workflows.
    """
    try:
        workflows = get_all_workflows(session)
        return workflows
    except Exception as e:
        logger.exception("Error retrieving workflows: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workflows",
        )
    finally:
        session.close()
        logger.info("Session closed after retrieving workflows.")

