"""Pydantic schemas for audience-scoped token API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AudienceTokenRequest(BaseModel):
    """Request to create an audience-scoped token."""

    audience: str = Field(
        ...,
        description="Operation scope for the token",
        examples=["jobs.abort", "schedule.generate", "swap.execute"],
    )
    ttl_seconds: int = Field(
        default=120,
        ge=30,
        le=600,
        description="Time-to-live in seconds (30-600, default: 120)",
    )

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        """Validate audience is recognized."""
        from app.core.audience_auth import VALID_AUDIENCES

        if v not in VALID_AUDIENCES:
            valid_list = ", ".join(VALID_AUDIENCES.keys())
            raise ValueError(f"Invalid audience: {v}. Valid audiences: {valid_list}")
        return v


class AudienceTokenResponse(BaseModel):
    """Response when creating an audience-scoped token."""

    token: str = Field(..., description="JWT token for the requested operation")
    audience: str = Field(..., description="Operation scope")
    expires_at: datetime = Field(..., description="Token expiration timestamp (UTC)")
    ttl_seconds: int = Field(..., description="Time-to-live in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "audience": "jobs.abort",
                "expires_at": "2025-12-29T15:30:00Z",
                "ttl_seconds": 120,
            }
        }


class AudienceListResponse(BaseModel):
    """Response listing all available audiences."""

    audiences: dict[str, str] = Field(
        ...,
        description="Map of audience keys to descriptions",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "audiences": {
                    "jobs.abort": "Abort running background jobs",
                    "schedule.generate": "Generate new schedules",
                    "swap.execute": "Execute schedule swaps",
                }
            }
        }


class RevokeTokenRequest(BaseModel):
    """Request to revoke an audience-scoped token."""

    jti: str = Field(
        ...,
        description="JWT ID of the token to revoke",
        min_length=32,
    )
    token: str | None = Field(
        default=None,
        description="The actual JWT token (optional, for ownership verification). "
        "If provided, the token is decoded to verify the requester owns it.",
    )
    reason: str = Field(
        default="manual_revocation",
        description="Reason for revocation",
        max_length=255,
    )


class RevokeTokenResponse(BaseModel):
    """Response after revoking a token."""

    success: bool = Field(..., description="Whether revocation succeeded")
    jti: str = Field(..., description="JWT ID that was revoked")
    message: str = Field(..., description="Human-readable message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "message": "Token successfully revoked",
            }
        }
