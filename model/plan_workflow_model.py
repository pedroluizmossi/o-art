from uuid import UUID

from sqlmodel import Field, SQLModel


class PlanWorkflow(SQLModel, table=True):
    __tablename__: str = "plans_workflows"
    plan_id: UUID = Field(foreign_key="plans.id", nullable=False, primary_key=True)
    workflow_id: UUID = Field(foreign_key="workflows.id", nullable=False, primary_key=True)

