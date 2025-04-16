from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

class UserCommon(SQLModel, table=True):
    """Common fields shared across all user models."""
    __tablename__: str = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr
    full_name: str
    verified: bool = False
    active: bool = True








