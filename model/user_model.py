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

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, username={self.username}, email_verified={self.email_verified}, is_active={self.is_active}, created_at={self.created_at}, tenant_id={self.tenant_id}, updated_at={self.updated_at})"

    def __str__(self):
        return f"User: {self.username} (ID: {self.id})"

    def insert(self, session):
        """
        Insert a new user into the database.
        """
        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def update(self, session):
        """
        Update an existing user in the database.
        """
        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def delete(self, session):
        """
        Delete a user from the database.
        """
        session.delete(self)
        session.commit()
        return self





