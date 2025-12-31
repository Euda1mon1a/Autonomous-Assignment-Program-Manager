"""
Filter parameter schemas for API requests.

Provides reusable filter schemas for common filtering patterns:
- Date range filters
- Status filters
- Search filters
- Type filters
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DateRangeFilter(BaseModel):
    """Filter by date range."""

    start_date: date | None = Field(None, description="Start date (inclusive)")
    end_date: date | None = Field(None, description="End date (inclusive)")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date | None, info) -> date | None:
        """Validate end_date is after start_date."""
        if v is not None and info.data.get("start_date") is not None:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class DateTimeRangeFilter(BaseModel):
    """Filter by datetime range."""

    start_datetime: datetime | None = Field(None, description="Start datetime (inclusive)")
    end_datetime: datetime | None = Field(None, description="End datetime (inclusive)")

    @field_validator("end_datetime")
    @classmethod
    def validate_end_datetime(cls, v: datetime | None, info) -> datetime | None:
        """Validate end_datetime is after start_datetime."""
        if v is not None and info.data.get("start_datetime") is not None:
            if v < info.data["start_datetime"]:
                raise ValueError("end_datetime must be after start_datetime")
        return v


class PersonFilter(BaseModel):
    """Filter for person queries."""

    person_type: str | None = Field(None, description="Person type (resident, faculty)")
    pgy_level: int | None = Field(None, ge=1, le=3, description="PGY level (1-3)")
    faculty_role: str | None = Field(None, description="Faculty role")
    specialties: list[str] | None = Field(None, description="Specialties filter")
    performs_procedures: bool | None = Field(None, description="Performs procedures flag")

    @field_validator("person_type")
    @classmethod
    def validate_person_type(cls, v: str | None) -> str | None:
        """Validate person_type is valid."""
        if v is not None and v not in ("resident", "faculty"):
            raise ValueError("person_type must be 'resident' or 'faculty'")
        return v


class AssignmentFilter(BaseModel):
    """Filter for assignment queries."""

    person_id: UUID | None = Field(None, description="Filter by person")
    block_id: UUID | None = Field(None, description="Filter by block")
    rotation_template_id: UUID | None = Field(None, description="Filter by rotation template")
    role: str | None = Field(None, description="Assignment role")
    date_range: DateRangeFilter | None = Field(None, description="Filter by date range")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """Validate role is valid."""
        if v is not None and v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class BlockFilter(BaseModel):
    """Filter for block queries."""

    date_range: DateRangeFilter | None = Field(None, description="Filter by date range")
    session: str | None = Field(None, description="Block session (AM, PM)")

    @field_validator("session")
    @classmethod
    def validate_session(cls, v: str | None) -> str | None:
        """Validate session is valid."""
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ("AM", "PM"):
                raise ValueError("session must be 'AM' or 'PM'")
            return v_upper
        return v


class SwapFilter(BaseModel):
    """Filter for swap queries."""

    requester_id: UUID | None = Field(None, description="Filter by requester")
    target_id: UUID | None = Field(None, description="Filter by target")
    status: str | None = Field(None, description="Swap status")
    swap_type: str | None = Field(None, description="Swap type")
    date_range: DateRangeFilter | None = Field(None, description="Filter by date range")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status is valid."""
        valid_statuses = ["pending", "approved", "executed", "rejected", "cancelled", "rolled_back"]
        if v is not None and v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v

    @field_validator("swap_type")
    @classmethod
    def validate_swap_type(cls, v: str | None) -> str | None:
        """Validate swap_type is valid."""
        valid_types = ["one_to_one", "absorb", "multi_way"]
        if v is not None and v not in valid_types:
            raise ValueError(f"swap_type must be one of {valid_types}")
        return v


class SearchFilter(BaseModel):
    """General search filter."""

    query: str | None = Field(None, description="Search query string", min_length=1, max_length=255)
    fields: list[str] | None = Field(None, description="Fields to search in")


class StatusFilter(BaseModel):
    """Filter by status."""

    status: str | list[str] | None = Field(None, description="Status or list of statuses")
    exclude_status: str | list[str] | None = Field(
        None,
        description="Status or list of statuses to exclude"
    )


class IdListFilter(BaseModel):
    """Filter by list of IDs."""

    ids: list[UUID] = Field(..., description="List of IDs to filter by", min_length=1, max_length=1000)

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate ID list is not too long."""
        if len(v) > 1000:
            raise ValueError("ids list cannot exceed 1000 items")
        return v


class BooleanFilter(BaseModel):
    """Generic boolean filter."""

    value: bool = Field(..., description="Boolean filter value")


class NumericRangeFilter(BaseModel):
    """Filter by numeric range."""

    min_value: float | None = Field(None, description="Minimum value (inclusive)")
    max_value: float | None = Field(None, description="Maximum value (inclusive)")

    @field_validator("max_value")
    @classmethod
    def validate_max_value(cls, v: float | None, info) -> float | None:
        """Validate max_value is greater than min_value."""
        if v is not None and info.data.get("min_value") is not None:
            if v < info.data["min_value"]:
                raise ValueError("max_value must be greater than min_value")
        return v
