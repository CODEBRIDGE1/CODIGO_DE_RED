"""
Authentication Schemas
Pydantic models para autenticación
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    tenant_id: int | None
    tenant_name: str | None
    photo_url: str | None = None
    roles: list[str] = []
    permissions: dict[str, list[str]] = {}  # {module: [actions]}
    security_modules: list[str] = []  # module keys from the user's security level
    security_level_id: int | None = None
    security_level_name: str | None = None

    class Config:
        from_attributes = True
