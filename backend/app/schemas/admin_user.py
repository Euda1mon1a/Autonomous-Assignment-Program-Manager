"""Admin user management schemas.

Pydantic models for admin user management endpoints including user CRUD,
account locking, activity logging, and bulk operations.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """Available user roles."""

    ADMIN = "admin"
    COORDINATOR = "coordinator"
    FACULTY = "faculty"
    CLINICAL_STAFF = "clinical_staff"
    RN = "rn"
    LPN = "lpn"
    MSA = "msa"
    RESIDENT = "resident"


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"


class BulkAction(str, Enum):
    """Available bulk actions."""

    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    DELETE = "delete"


class ActivityAction(str, Enum):
    """Activity log action types."""

    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    ROLE_CHANGED = "role_changed"
    INVITE_SENT = "invite_sent"
    INVITE_RESENT = "invite_resent"


# ============================================================================
# Admin User Schemas
# ============================================================================


class AdminUserBase(BaseModel):
    """Base schema for admin user data."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.COORDINATOR


class AdminUserCreate(AdminUserBase):
    """Schema for creating a new user via admin."""

    username: str | None = Field(None, min_length=3, max_length=100)
    send_invite: bool = Field(True, description="Send invitation email to user")

    @field_validator("username", mode="before")
    @classmethod
    def set_username_from_email(cls, v: str | None, info) -> str | None:
        """If username not provided, it will be derived from email."""
        return v


class AdminUserUpdate(BaseModel):
    """Schema for updating a user via admin."""

    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    """Schema for user response in admin context."""

    id: UUID
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool
    is_locked: bool = False
    lock_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
    invite_sent_at: datetime | None = None
    invite_accepted_at: datetime | None = None

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """Paginated list of users for admin."""

    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    class Config:
        populate_by_name = True


# ============================================================================
# Account Lock Schemas
# ============================================================================


class AccountLockRequest(BaseModel):
    """Request to lock or unlock a user account."""

    locked: bool = Field(..., description="True to lock, False to unlock")
    reason: str | None = Field(
        None, max_length=500, description="Reason for locking (optional)"
    )


class AccountLockResponse(BaseModel):
    """Response after locking/unlocking account."""

    user_id: UUID = Field(alias="userId")
    is_locked: bool = Field(alias="isLocked")
    lock_reason: str | None = Field(None, alias="lockReason")
    locked_at: datetime | None = Field(None, alias="lockedAt")
    locked_by: str | None = Field(None, alias="lockedBy")
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Invitation Schemas
# ============================================================================


class ResendInviteRequest(BaseModel):
    """Request to resend user invitation."""

    custom_message: str | None = Field(
        None,
        max_length=1000,
        alias="customMessage",
        description="Optional custom message to include in invite",
    )

    class Config:
        populate_by_name = True


class ResendInviteResponse(BaseModel):
    """Response after resending invitation."""

    user_id: UUID = Field(alias="userId")
    email: str
    sent_at: datetime = Field(alias="sentAt")
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Activity Log Schemas
# ============================================================================


class ActivityLogEntry(BaseModel):
    """Single activity log entry."""

    id: UUID
    timestamp: datetime
    user_id: UUID | None = Field(None, alias="userId")
    user_email: str | None = Field(None, alias="userEmail")
    action: str
    target_user_id: UUID | None = Field(None, alias="targetUserId")
    target_user_email: str | None = Field(None, alias="targetUserEmail")
    details: dict | None = None
    ip_address: str | None = Field(None, alias="ipAddress")
    user_agent: str | None = Field(None, alias="userAgent")

    class Config:
        populate_by_name = True


class ActivityLogResponse(BaseModel):
    """Paginated activity log response."""

    items: list[ActivityLogEntry]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    class Config:
        populate_by_name = True


class ActivityLogFilters(BaseModel):
    """Filters for activity log queries."""

    user_id: UUID | None = Field(None, alias="userId")
    action: ActivityAction | None = None
    date_from: datetime | None = Field(None, alias="dateFrom")
    date_to: datetime | None = Field(None, alias="dateTo")

    class Config:
        populate_by_name = True


# ============================================================================
# Bulk Operation Schemas
# ============================================================================


class BulkUserActionRequest(BaseModel):
    """Request for bulk user operations."""

    user_ids: list[UUID] = Field(..., alias="userIds", min_length=1, max_length=100)
    action: BulkAction

    class Config:
        populate_by_name = True


class BulkUserActionResponse(BaseModel):
    """Response for bulk user operations."""

    action: str
    affected_count: int = Field(alias="affectedCount")
    success_ids: list[UUID] = Field(alias="successIds")
    failed_ids: list[UUID] = Field(default_factory=list, alias="failedIds")
    errors: list[str] = Field(default_factory=list)
    message: str

    class Config:
        populate_by_name = True


# ============================================================================
# Query Parameter Schemas
# ============================================================================


class UserListQueryParams(BaseModel):
    """Query parameters for user listing."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100, alias="pageSize")
    role: UserRole | None = None
    status: UserStatus | None = None
    search: str | None = Field(None, max_length=100)

    class Config:
        populate_by_name = True
