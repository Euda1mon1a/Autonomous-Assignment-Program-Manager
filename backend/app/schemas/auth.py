"""Authentication schemas."""

import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456",
    "12345678",
    "qwerty",
    "admin",
    "welcome",
}


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenWithRefresh(BaseModel):
    """JWT token response with refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token using refresh token."""

    refresh_token: str


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: str | None = None
    username: str | None = None
    jti: str | None = None  # JWT ID for blacklist support


class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username for authentication"
    )
    password: str = Field(..., min_length=1, description="Password for authentication")


class UserCreate(BaseModel):
    """User creation request.

    Supported roles:
    - admin: Full system access
    - coordinator: Manage schedules, people, conflicts
    - faculty: View own schedule, manage swaps
    - clinical_staff: View manifest and call roster
    - rn: Registered Nurse (same permissions as clinical_staff)
    - lpn: Licensed Practical Nurse (same permissions as clinical_staff)
    - msa: Medical Support Assistant (same permissions as clinical_staff)
    - resident: View own schedule, manage swaps, view conflicts
    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Unique username"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., description="Password (min 12 chars, complexity required)")
    role: str = Field(
        "coordinator",
        description="User role (admin, coordinator, faculty, resident, etc.)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")

        has_lower = bool(re.search(r"[a-z]", v))
        has_upper = bool(re.search(r"[A-Z]", v))
        has_digit = bool(re.search(r"\d", v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))

        if sum([has_lower, has_upper, has_digit, has_special]) < 3:
            raise ValueError(
                "Password must contain at least 3 of: lowercase, uppercase, numbers, special characters"
            )

        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("Password is too common")

        return v


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
