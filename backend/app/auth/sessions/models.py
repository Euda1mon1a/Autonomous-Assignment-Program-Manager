"""
Session models and schemas.

Defines Pydantic models for session management including:
- Session data structure
- Device information tracking
- Activity logging
- Session lifecycle events
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"


class DeviceType(str, Enum):
    """Device type enumeration."""

    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    API = "api"
    UNKNOWN = "unknown"


class SessionActivityType(str, Enum):
    """Session activity type enumeration."""

    LOGIN = "login"
    REFRESH = "refresh"
    ACTIVITY = "activity"
    LOGOUT = "logout"
    FORCE_LOGOUT = "force_logout"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DeviceInfo(BaseModel):
    """
    Device information for session tracking.

    Captures device details for security auditing and
    multi-device session management.
    """

    device_type: DeviceType = DeviceType.UNKNOWN
    user_agent: str | None = None
    ip_address: str | None = None
    platform: str | None = None
    browser: str | None = None
    os: str | None = None

    class Config:
        use_enum_values = True


class SessionData(BaseModel):
    """
    Core session data structure.

    Stores all information about an active user session including
    authentication details, device info, and activity tracking.
    """

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username for display")
    jti: str | None = Field(None, description="JWT token ID")

    # Session lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    status: SessionStatus = SessionStatus.ACTIVE

    # Device tracking
    device_info: DeviceInfo = Field(default_factory=DeviceInfo)

    # Activity tracking
    request_count: int = Field(default=0, description="Number of requests in this session")
    last_ip: str | None = None

    # Custom data
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is a valid UUID string."""
        try:
            UUID(v)
        except ValueError:
            raise ValueError("user_id must be a valid UUID")
        return v

    def is_expired(self, current_time: datetime | None = None) -> bool:
        """
        Check if session has expired.

        Args:
            current_time: Current time for comparison (defaults to utcnow)

        Returns:
            True if session is expired
        """
        if self.status != SessionStatus.ACTIVE:
            return True

        if self.expires_at is None:
            return False

        current = current_time or datetime.utcnow()
        return current >= self.expires_at

    def update_activity(self, ip_address: str | None = None) -> None:
        """
        Update session activity timestamp and metrics.

        Args:
            ip_address: Optional IP address of current request
        """
        self.last_activity = datetime.utcnow()
        self.request_count += 1
        if ip_address:
            self.last_ip = ip_address


class SessionCreate(BaseModel):
    """Request schema for creating a new session."""

    user_id: str
    username: str
    jti: str | None = None
    device_info: DeviceInfo | None = None
    timeout_minutes: int = Field(default=1440, ge=1, le=43200)  # 1 min to 30 days
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response schema for session data."""

    session_id: str
    user_id: str
    username: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime | None
    status: SessionStatus
    device_info: DeviceInfo
    request_count: int

    class Config:
        use_enum_values = True


class SessionListResponse(BaseModel):
    """Response schema for listing sessions."""

    sessions: list[SessionResponse]
    total: int
    active_count: int


class SessionActivity(BaseModel):
    """
    Session activity log entry.

    Records important session lifecycle events for auditing.
    """

    session_id: str
    user_id: str
    activity_type: SessionActivityType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class SessionStats(BaseModel):
    """
    Session statistics for monitoring.

    Provides metrics about active sessions, concurrent users,
    and session activity patterns.
    """

    total_active_sessions: int = 0
    unique_active_users: int = 0
    sessions_by_device: dict[str, int] = Field(default_factory=dict)
    sessions_created_today: int = 0
    sessions_expired_today: int = 0
    average_session_duration_minutes: float = 0.0

    class Config:
        use_enum_values = True
