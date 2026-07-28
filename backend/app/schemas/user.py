from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str]
    avatar_url: Optional[str]
    credit_balance: int
    plan: str
    role: str
    country: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
