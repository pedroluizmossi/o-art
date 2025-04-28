import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.plan_model import Plan, PlanCreate

logger = setup_logger(__name__)

PLANS_JSON_PATH = "plans.json"

class PlanNotFound(Exception):
    """Custom exception for 'plan' not found."""
    def __init__(self, plan_id: UUID):
        self.plan_id = plan_id
        super().__init__(f"Plan with ID {plan_id} not found.")

async def create_plan(session: AsyncSession, plan_data: PlanCreate) -> Plan:
    """Adds a new plan to the database."""
    try:
        now = datetime.now(timezone.utc)
        plan = Plan(
            **plan_data.model_dump(),
            created_at=now,
            updated_at=now
        )

        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        logger.info("Plan created successfully: %s", plan.id)
        return plan
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating plan %s: %s", plan_data.name, e)
        raise e

async def get_all_plans(session: AsyncSession) -> list[Plan]:
    """Retrieves all plans from the database."""
    try:
        statement = select(Plan)
        plans = await session.exec(statement)
        plans = plans.all()
        return plans
    except Exception as e:
        logger.exception("Error retrieving all plans: %s", e)
        raise e

async def get_plan_by_id(session: AsyncSession, plan_id: UUID) -> Optional[Plan]:
    """Retrieves a plan by its ID."""
    try:
        statement = select(Plan).where(Plan.id == plan_id)
        plan = await session.exec(statement)
        plan = plan.first()
        if not plan:
            logger.warning("Plan with ID %s not found.", plan_id)
            raise PlanNotFound(plan_id)
        return plan
    except Exception as e:
        logger.exception("Error retrieving plan by ID %s: %s", plan_id, e)
        raise e

async def update_plan(session: AsyncSession, plan_id: UUID, plan_update_data: dict) -> Optional[Plan]:
    """Updates an existing plan identified by plan_id with data from plan_update_data."""
    try:
        plan = await get_plan_by_id(session, plan_id)
        if not plan:
            logger.warning("Plan with ID %s not found for update.", plan_id)
            raise PlanNotFound(plan_id)

        for key, value in plan_update_data.items():
            setattr(plan, key, value)

        plan.updated_at = datetime.now(timezone.utc)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        logger.info("Plan updated successfully: %s", plan.id)
        return plan
    except Exception as e:
        await session.rollback()
        logger.exception("Error updating plan %s: %s", plan_id, e)
        raise e

async def delete_plan(session: AsyncSession, plan_id: UUID) -> Optional[Plan]:
    """Deletes a plan by its ID."""
    try:
        plan = await get_plan_by_id(session, plan_id)
        if not plan:
            logger.warning("Plan with ID %s not found for deletion.", plan_id)
            raise PlanNotFound(plan_id)

        await session.delete(plan)
        await session.commit()
        logger.info("Plan deleted successfully: %s", plan.id)
        return plan
    except Exception as e:
        await session.rollback()
        logger.exception("Error deleting plan %s: %s", plan_id, e)
        raise e

async def seed_plan_from_json(session, json_path):
    with open(json_path, encoding="utf-8") as f:
        plans_data = json.load(f)

    for plan_data in plans_data:
        name = plan_data.get("name")
        exists = await session.exec(select(Plan).where(Plan.name == name))
        exists = exists.first()
        if not exists:
            session.add(Plan(**plan_data))
            logger.info(f"Model '{name}' inserted.")
        else:
            logger.info(f"Model '{name}' already exists. Skipping insertion.")
    await session.commit()

