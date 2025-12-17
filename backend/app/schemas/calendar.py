"""Calendar export schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class CalendarExportRequest(BaseModel):
    """Schema for calendar export request."""

    person_id: UUID
    start_date: date
    end_date: date
    include_types: Optional[list[str]] = None  # Filter by activity types

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
    expires_at: Optional[datetime] = None


class CalendarSubscriptionCreate(BaseModel):
    """Schema for creating a calendar subscription."""

    person_id: UUID
    expires_days: Optional[int] = None  # None = never expires


class CalendarSubscriptionResponse(BaseModel):
    """Schema for calendar subscription response."""

    token: str
    subscription_url: str
    person_id: UUID
    created_at: datetime
    expires_at: Optional[datetime] = None
