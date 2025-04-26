from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


from model.enum.model_type import Model
from model.enum.workflow_type import Workflow as WorkflowType
from model.enum.workflow_segment_type import WorkflowSegment


class WorkflowBase(SQLModel):
    """Base model with common workflow fields."""
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None, nullable=True)
    model_type: Model = Field(sa_column=Column("model", SqlEnum(Model)))
    model_id: Optional[UUID] = Field(default=None, foreign_key="models.id")
    workflow_type: WorkflowType = Field(sa_column=Column("workflow_type", SqlEnum(WorkflowType)))
    workflow_segment: WorkflowSegment = Field(
        sa_column=Column("workflow_segment", SqlEnum(WorkflowSegment))
    )
    workflow_json: dict = Field(sa_column=Column(JSONB))
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSONB))

class Workflow(WorkflowBase, table=True):
    __tablename__ = "workflows"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime)
    )

class WorkflowCreate(WorkflowBase):
    pass