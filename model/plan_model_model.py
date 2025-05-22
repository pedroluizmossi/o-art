from uuid import UUID

from sqlmodel import Field, SQLModel


class PlanModel(SQLModel, table=True):
    __tablename__: str = "plans_models"
    """Associative table for many-to-many relationship between plans and models."""
    plan_id: UUID = Field(foreign_key="plans.id", nullable=False, primary_key=True)
    model_id: UUID = Field(foreign_key="models.id", nullable=False, primary_key=True)


