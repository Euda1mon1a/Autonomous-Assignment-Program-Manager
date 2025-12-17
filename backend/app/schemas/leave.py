"""Pydantic schemas for leave management API."""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LeaveType(str, Enum):
    VACATION = "vacation"
    TDY = "tdy"
    DEPLOYMENT = "deployment"
    CONFERENCE = "conference"
    MEDICAL = "medical"
    FAMILY_EMERGENCY = "family_emergency"


class LeaveWebhookPayload(BaseModel):
    """Payload for leave webhook notifications."""
    event_type: str = Field(..., pattern="^(created|updated|deleted)$")
    faculty_id: UUID
    faculty_name: str
    leave_id: Optional[UUID] = None
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool = True
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class LeaveCreateRequest(BaseModel):
    """Request to create a leave record."""
    faculty_id: UUID
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool = True
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class LeaveUpdateRequest(BaseModel):
    """Request to update a leave record."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type: Optional[LeaveType] = None
    is_blocking: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)


class LeaveResponse(BaseModel):
    """Response for a leave record."""
    id: UUID
    faculty_id: UUID
    faculty_name: str
    start_date: date
    end_date: date
    leave_type: LeaveType
    is_blocking: bool
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeaveListResponse(BaseModel):
    """Paginated list of leave records."""
    items: List[LeaveResponse]
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
    entries: List[LeaveCalendarEntry]
    conflict_count: int = 0


class BulkLeaveImportRequest(BaseModel):
    """Request for bulk leave import."""
    records: List[LeaveCreateRequest]
    skip_duplicates: bool = True


class BulkLeaveImportResponse(BaseModel):
    """Response for bulk leave import."""
    success: bool
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[str] = []
