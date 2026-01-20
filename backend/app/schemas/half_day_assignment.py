"""Pydantic schemas for HalfDayAssignment API responses."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HalfDayAssignmentRead(BaseModel):
    """Schema for reading a half-day assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_id: UUID
    person_name: str | None = None
    person_type: str | None = None
    pgy_level: int | None = None
    date: date
    time_of_day: str  # "AM" or "PM"
    activity_id: UUID | None = None
    activity_code: str | None = None
    activity_name: str | None = None
    display_abbreviation: str | None = None
    source: str  # "preload", "manual", "solver", "template"
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime


class HalfDayAssignmentListResponse(BaseModel):
    """Response for listing half-day assignments."""

    assignments: list[HalfDayAssignmentRead]
    total: int
    block_number: int | None = None
    academic_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
