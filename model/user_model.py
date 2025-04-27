from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    username: str
    email_verified: bool = False
    is_active: bool = True

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),

    )
    tenant_id: Optional[UUID] = Field(default=None, foreign_key=None)

    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )

    def __repr__(self):
        return (
            f"User(id={self.id}, email={self.email}, username={self.username}, "
            f"email_verified={self.email_verified}, is_active={self.is_active}, "
            f"created_at={self.created_at.isoformat() if self.created_at else None}, "
            f"tenant_id={self.tenant_id}, "
            f"updated_at={self.updated_at.isoformat() if self.updated_at else None})"
        )

    def __str__(self):
        return f"User: {self.username} (ID: {self.id})"
