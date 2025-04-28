from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel
from model.map.model_parameter_mapping import Parameters
from model.map.type_parameter_mapping import WorkflowType
from model.map.segment_parameter_mapping import WorkflowSegment
from pydantic import field_validator

class PlanBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: str = Field(default=None)
    price: float = Field(default=0.0)
    is_active: bool = Field(default=True)

class PlanParameters(PlanBase):
    model_parameters: Parameters = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=Parameters
    )
    type_parameters: WorkflowType = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=WorkflowType
    )
    segment_parameters: WorkflowSegment = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=WorkflowSegment
    )

    @field_validator("model_parameters", mode="before")
    def ensure_parameters_rootmodel(cls, v):
        # Already a Parameters model
        if isinstance(v, Parameters):
            return v
        # If value is a dict, wrap it in Parameters
        if isinstance(v, dict):
            return Parameters(root=v)
        # If value is None or something unexpected, raise
        raise TypeError("parameters must be a dict or Parameters instance")

    @field_validator("type_parameters", mode="before")
    def ensure_workflow_type_rootmodel(cls, v):
        # Already a WorkflowType model
        if isinstance(v, WorkflowType):
            return v
        # If value is a dict, wrap it in WorkflowType
        if isinstance(v, dict):
            return WorkflowType(root=v)
        # If value is None or something unexpected, raise
        raise TypeError("workflow_type must be a dict or WorkflowType instance")

    @field_validator("segment_parameters", mode="before")
    def ensure_workflow_segment_rootmodel(cls, v):
        # Already a WorkflowSegment model
        if isinstance(v, WorkflowSegment):
            return v
        # If value is a dict, wrap it in WorkflowSegment
        if isinstance(v, dict):
            return WorkflowSegment(root=v)
        # If value is None or something unexpected, raise
        raise TypeError("workflow_segment must be a dict or WorkflowSegment instance")

class Plan(PlanParameters, table=True):
    __tablename__ = "plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

class PlanCreate(PlanParameters):
    """
    PlanCreate model for creating a new plan.
    """
    pass
