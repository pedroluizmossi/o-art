from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from model.plan_model import Plan, PlanCreate, PlanUpdate
from service.plan_service import (
    PlanNotFound,
    create_plan,
    delete_plan,
    get_all_plans,
    get_plan_by_id,
    update_plan,
)

logger = setup_logger(__name__)

async def get_all_plans_handler() -> List[Plan]:
    """
    Handler to retrieve all plans.
    """
    try:
        async with get_db_session() as session:
            plans = await get_all_plans(session)
        return plans
    except Exception as e:
        logger.exception("Error retrieving plans: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving plans",
        )

async def get_plan_by_id_handler(plan_id: UUID) -> Optional[Plan]:
    """
    Handler to retrieve a plan by its ID.
    Returns the plan or raises an HTTP 404 if not found.
    """
    try:
        async with get_db_session() as session:
            plan = await get_plan_by_id(session, plan_id)
        return plan
    except PlanNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan with ID %s not found." % plan_id,
        )
    except Exception as e:
        logger.exception("Unhandled error retrieving plan %s: %s", plan_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving plan with ID %s" % plan_id,
        )

async def create_plan_handler(plan_data: PlanCreate) -> Plan:
    """
    Handler to create a new plan.
    """
    try:
        async with get_db_session() as session:
            plan = await create_plan(session, plan_data)
        return plan
    except ValueError as e:
        logger.exception("Validation error creating plan %s: %s", getattr(plan_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error: %s" % str(e),
        )
    except Exception as e:
        logger.exception("Error creating plan %s: %s", getattr(plan_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating plan",
        )

async def update_plan_handler(plan_id: UUID, plan_update_data: PlanUpdate) -> Optional[Plan]:
    """
    Handler to update a plan by its ID.
    """
    try:
        plan_update_data = plan_update_data.model_dump(exclude_unset=True)
        async with get_db_session() as session:
            plan = await update_plan(session, plan_id, plan_update_data)
        return plan
    except PlanNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan with ID %s not found." % plan_id,
        )
    except ValueError as e:
        logger.exception("Validation error updating plan %s: %s", plan_id, e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error: %s" % str(e),
        )
    except Exception as e:
        logger.exception("Error updating plan %s: %s", plan_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating plan",
        )

async def delete_plan_handler(plan_id: UUID) -> None:
    """
    Handler to delete a plan by its ID.
    """
    try:
        async with get_db_session() as session:
            await delete_plan(session, plan_id)
    except PlanNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan with ID %s not found." % plan_id,
        )
    except Exception as e:
        logger.exception("Error deleting plan %s: %s", plan_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting plan",
        )
