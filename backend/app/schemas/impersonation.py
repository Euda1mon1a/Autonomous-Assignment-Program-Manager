"""Impersonation schemas for Admin 'View As User' feature.

This module provides Pydantic schemas for the impersonation system that allows
administrators to temporarily assume the identity of other users for
troubleshooting and support purposes.

Security Considerations:
- Only admins can initiate impersonation
- Cannot self-impersonate
- Cannot impersonate while already impersonating
- All impersonation events are logged to the audit trail
- Impersonation tokens have a short TTL (30 minutes default)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class ImpersonateRequest(BaseModel):
    """Request to start impersonating another user.

    Attributes:
        target_user_id: UUID of the user to impersonate.
    """

    target_user_id: UUID = Field(..., description="UUID of the user to impersonate")


class ImpersonateResponse(BaseModel):
    """Response after successfully starting impersonation.

    Attributes:
        impersonation_token: Short-lived JWT token for the impersonation session.
        target_user: Details of the user being impersonated.
        expires_at: When the impersonation session expires.
    """

    impersonation_token: str = Field(
        ..., description="JWT token for the impersonation session"
    )
    target_user: UserResponse = Field(..., description="The user being impersonated")
    expires_at: datetime = Field(
        ..., description="When the impersonation session expires"
    )

    class Config:
        from_attributes = True


class ImpersonationStatus(BaseModel):
    """Current impersonation status for a session.

    Attributes:
        is_impersonating: Whether an impersonation session is active.
        target_user: The user being impersonated (if active).
        original_user: The admin who initiated impersonation (if active).
        expires_at: When the impersonation session expires (if active).
    """

    is_impersonating: bool = Field(
        default=False, description="Whether an impersonation session is active"
    )
    target_user: UserResponse | None = Field(
        default=None, description="The user being impersonated"
    )
    original_user: UserResponse | None = Field(
        default=None, description="The admin who initiated impersonation"
    )
    expires_at: datetime | None = Field(
        default=None, description="When the impersonation session expires"
    )

    class Config:
        from_attributes = True


class EndImpersonationResponse(BaseModel):
    """Response after ending an impersonation session.

    Attributes:
        success: Whether the impersonation was successfully ended.
        message: Human-readable status message.
    """

    success: bool = Field(
        ..., description="Whether the impersonation was successfully ended"
    )
    message: str = Field(
        default="Impersonation ended successfully",
        description="Human-readable status message",
    )
