from datetime import datetime
from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    """Common fields shared across all user models."""
    __tablename__: str = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    username: str
    email_verified: bool = False
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: str(datetime.now()))
    tenant_id: Optional[UUID] = Field(default=None)
    updated_at: Optional[str] = Field(default_factory=lambda: str(datetime.now()))









