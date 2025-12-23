"""Calendar export schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CalendarExportRequest(BaseModel):
    """Schema for calendar export request."""

    person_id: UUID
    start_date: date
    end_date: date
    include_types: list[str] | None = None  # Filter by activity types

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info: dict) -> date:
        """Validate end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class CalendarSubscriptionToken(BaseModel):
    """Schema for calendar subscription token."""

    token: str
    person_id: UUID
    created_at: datetime
    expires_at: datetime | None = None


class CalendarSubscriptionCreate(BaseModel):
    """Schema for creating a calendar subscription."""

    person_id: UUID
    label: str | None = Field(
        None, max_length=255, description="Optional label for the subscription"
    )
    expires_days: int | None = Field(
        None, ge=1, le=365, description="Days until expiration (1-365, None = never)"
    )


class CalendarSubscriptionResponse(BaseModel):
    """Schema for calendar subscription response."""

    token: str
    subscription_url: str
    webcal_url: str  # webcal:// protocol URL for calendar apps
    person_id: UUID
    label: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_accessed_at: datetime | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


class CalendarSubscriptionListResponse(BaseModel):
    """Schema for listing calendar subscriptions."""

    subscriptions: list[CalendarSubscriptionResponse]
    total: int


class CalendarSubscriptionRevokeResponse(BaseModel):
    """Schema for revoke response."""

    success: bool
    message: str
