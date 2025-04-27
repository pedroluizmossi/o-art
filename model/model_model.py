from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates
from sqlmodel import Column, Field, SQLModel


from model.enum.model_type import Model as ModelType

class ModelBase(SQLModel):
    """Base model with common model fields."""
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None, nullable=True)
    os_path: str = Field(index=True, nullable=False)
    model: ModelType = Field(sa_column=Column("model", SqlEnum(ModelType)))
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSONB))

    @validates("name")
    def validate_name(self, key, value):
        if not value:
            raise ValueError("Name cannot be empty")
        return value


class Model(ModelBase, table=True):
    __tablename__: str = "models"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )

class ModelCreate(ModelBase):
    pass

class ModelUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    os_path: Optional[str] = None
    model: Optional[ModelType] = None
    parameters: Optional[dict] = None