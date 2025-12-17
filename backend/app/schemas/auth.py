"""Authentication schemas."""
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: str | None = None
    username: str | None = None
    jti: str | None = None  # JWT ID for blacklist support


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class UserCreate(BaseModel):
    """User creation request."""
    username: str
    email: EmailStr
    password: str
    role: str = "coordinator"  # 'admin', 'coordinator', 'faculty'


class UserUpdate(BaseModel):
    """User update request."""
    email: EmailStr | None = None
    password: str | None = None
    role: str | None = None


class UserResponse(BaseModel):
    """User response (without password)."""
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool = True

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """User with hashed password (internal use)."""
    hashed_password: str
