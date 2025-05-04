from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates
from sqlmodel import Column, Field, SQLModel

from model.enum.model_type import Model
from model.enum.workflow_segment_type import WorkflowSegment
from model.enum.workflow_type import Workflow as WorkflowType


class WorkflowBase(SQLModel):
    """Base model with common workflow fields."""
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None, nullable=True)
    model_type: Model = Field(sa_column=Column("model", SqlEnum(Model)))
    model_id: Optional[UUID] = Field(default=None, foreign_key="models.id")
    workflow_type: WorkflowType = Field(
        sa_column=Column("workflow_type", SqlEnum(WorkflowType)))
    workflow_segment: WorkflowSegment = Field(
        sa_column=Column("workflow_segment", SqlEnum(WorkflowSegment))
    )
    workflow_json: dict = Field(sa_column=Column(JSONB))
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSONB))

    @validates("name")
    def validate_name(self, key, value):
        if not value:
            raise ValueError("Name cannot be empty")
        return value

class Workflow(WorkflowBase, table=True):
    __tablename__ = "workflows"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[Model] = None
    model_id: Optional[UUID] = None
    workflow_type: Optional[WorkflowType] = None
    workflow_segment: Optional[WorkflowSegment] = None
    workflow_json: Optional[dict] = None
    parameters: Optional[dict] = None