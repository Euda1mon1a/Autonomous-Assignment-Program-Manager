"""Pydantic schemas for leave management API."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.validators.date_validators import validate_academic_year_date


class LeaveType(str, Enum):
    """
    Leave/absence types with Hawaii-appropriate defaults.

    Blocking types (person cannot be assigned during absence):
    - deployment, tdy, family_emergency, bereavement, emergency_leave,
      convalescent, maternity_paternity

    Duration-based blocking:
    - medical (>7 days), sick (>3 days)

    Non-blocking (tracked but doesn't prevent assignment):
    - vacation, conference
    """

    VACATION = "vacation"
    TDY = "tdy"
    DEPLOYMENT = "deployment"
    CONFERENCE = "conference"
    MEDICAL = "medical"
    FAMILY_EMERGENCY = "family_emergency"
    # New types (Hawaii-appropriate)
    BEREAVEMENT = "bereavement"
    EMERGENCY_LEAVE = "emergency_leave"
    SICK = "sick"
    CONVALESCENT = "convalescent"
    MATERNITY_PATERNITY = "maternity_paternity"


class LeaveWebhookPayload(BaseModel):
    """Payload for leave webhook notifications."""

    event_type: str = Field(..., pattern="^(created|updated|deleted)$")
    faculty_id: UUID
    faculty_name: str
    leave_id: UUID | None = None
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool = True
    description: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LeaveCreateRequest(BaseModel):
    """Request to create a leave record."""

    faculty_id: UUID
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool = True
    description: str | None = Field(None, max_length=500)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LeaveUpdateRequest(BaseModel):
    """Request to update a leave record."""

    start_date: date | None = None
    end_date: date | None = None
    leave_type: LeaveType | None = None
    is_blocking: bool | None = None
    description: str | None = Field(None, max_length=500)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within academic year bounds."""
        if v is not None:
            return validate_academic_year_date(v, field_name="date")
        return v


class LeaveResponse(BaseModel):
    """Response for a leave record."""

    id: UUID
    faculty_id: UUID
    faculty_name: str
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class LeaveListResponse(BaseModel):
    """Paginated list of leave records."""

    items: list[LeaveResponse]
    total: int
    page: int
    page_size: int


class LeaveCalendarEntry(BaseModel):
    """Single entry in leave calendar."""

    faculty_id: UUID
    faculty_name: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    is_blocking: bool
    has_fmit_conflict: bool = False


class LeaveCalendarResponse(BaseModel):
    """Leave calendar for a date range."""

    start_date: date
    end_date: date
    entries: list[LeaveCalendarEntry]
    conflict_count: int = 0


class BulkLeaveImportRequest(BaseModel):
    """Request for bulk leave import."""

    records: list[LeaveCreateRequest]
    skip_duplicates: bool = True


class BulkLeaveImportResponse(BaseModel):
    """Response for bulk leave import."""

    success: bool
    imported_count: int
    skipped_count: int
    error_count: int
    errors: list[str] = []
