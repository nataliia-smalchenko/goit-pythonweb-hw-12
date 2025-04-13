from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.entity.models import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="Username")
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=30, description="Password")


class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
