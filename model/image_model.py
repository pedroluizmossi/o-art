from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


class Image(SQLModel, table=True):
    __tablename__: str = "images"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    url: str = Field(index=True, nullable=False)
    workflow_id: UUID = Field(foreign_key="workflows.id", nullable=False)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    parameters: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )