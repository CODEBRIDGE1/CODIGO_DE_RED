"""
User Schemas - Pydantic models para usuarios
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    tenant_id: Optional[int] = None
    is_superadmin: bool = False


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    id: int
    tenant_id: Optional[int]
    is_superadmin: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithRoles(UserResponse):
    roles: List[str] = []
    permissions: List[str] = []


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
    page: int
    page_size: int
