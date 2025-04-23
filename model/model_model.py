from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


from model.enum.model_type import Model


class Model(SQLModel, table=True):
    __tablename__: str = "models"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None, nullable=True)
    os_path: str = Field(index=True, nullable=False)
    model_type: Model = Field(sa_column=Column("model", SqlEnum(Model)))
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime)
    )
