"""Pydantic schemas for call assignment API contracts."""

from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CallType(str, Enum):
    """Types of call assignments."""

    OVERNIGHT = "overnight"
    WEEKEND = "weekend"
    BACKUP = "backup"


class CallAssignmentBase(BaseModel):
    """Base schema for call assignment data."""

    call_date: date = Field(..., description="Date of the call assignment")
    person_id: UUID = Field(..., description="Faculty member assigned to call")
    call_type: str = Field(
        default="overnight",
        description="Type of call: overnight, weekend, or backup",
    )
    is_weekend: bool = Field(
        default=False, description="Whether this is a weekend call"
    )
    is_holiday: bool = Field(
        default=False, description="Whether this is a holiday call"
    )

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: str) -> str:
        """Validate call_type is one of the valid types."""
        if v not in ("overnight", "weekend", "backup"):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class CallAssignmentCreate(CallAssignmentBase):
    """Schema for creating a new call assignment."""

    pass


class CallAssignmentUpdate(BaseModel):
    """Schema for updating an existing call assignment."""

    call_date: date | None = None
    person_id: UUID | None = None
    call_type: str | None = None
    is_weekend: bool | None = None
    is_holiday: bool | None = None

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: str | None) -> str | None:
        """Validate call_type is one of the valid types."""
        if v is not None and v not in ("overnight", "weekend", "backup"):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class PersonBrief(BaseModel):
    """Brief person info for embedding in responses."""

    id: UUID
    name: str
    faculty_role: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CallAssignmentResponse(BaseModel):
    """Schema for call assignment response."""

    id: UUID
    call_date: date
    person_id: UUID
    call_type: str
    is_weekend: bool
    is_holiday: bool
    person: PersonBrief | None = None

    model_config = ConfigDict(from_attributes=True)


class CallAssignmentListResponse(BaseModel):
    """Schema for paginated list of call assignments."""

    items: list[CallAssignmentResponse]
    total: int
    skip: int = 0
    limit: int = 100


class BulkCallAssignmentCreate(BaseModel):
    """Schema for bulk creating call assignments."""

    assignments: list[CallAssignmentCreate] = Field(
        ..., description="List of call assignments to create"
    )
    replace_existing: bool = Field(
        default=False,
        description="If true, delete existing assignments in the date range first",
    )

    @field_validator("assignments")
    @classmethod
    def validate_not_empty(cls, v: list[CallAssignmentCreate]) -> list[CallAssignmentCreate]:
        """Ensure assignments list is not empty."""
        if not v:
            raise ValueError("assignments list cannot be empty")
        return v


class BulkCallAssignmentResponse(BaseModel):
    """Schema for bulk creation response."""

    created: int = Field(..., description="Number of assignments created")
    errors: list[str] = Field(
        default_factory=list, description="Error messages for failed creations"
    )


class CallCoverageReport(BaseModel):
    """Schema for call coverage report."""

    start_date: date
    end_date: date
    total_expected_nights: int = Field(
        ..., description="Total nights requiring coverage (Sun-Thu)"
    )
    covered_nights: int = Field(..., description="Nights with call assignments")
    coverage_percentage: float = Field(
        ..., description="Percentage of nights covered (0-100)"
    )
    gaps: list[date] = Field(
        default_factory=list, description="Dates without call coverage"
    )


class CallEquityReport(BaseModel):
    """Schema for call equity/distribution report."""

    start_date: date
    end_date: date
    faculty_count: int = Field(
        ..., description="Number of faculty with call assignments"
    )
    total_overnight_calls: int = Field(
        ..., description="Total overnight call assignments"
    )
    sunday_call_stats: dict[str, Any] = Field(
        ..., description="Statistics for Sunday calls (min, max, mean, stdev)"
    )
    weekday_call_stats: dict[str, Any] = Field(
        ..., description="Statistics for Mon-Thu calls (min, max, mean, stdev)"
    )
    distribution: list[dict[str, Any]] = Field(
        ..., description="Per-faculty call distribution details"
    )
