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

    @field_validator("call_date")
    @classmethod
    def validate_call_date_not_future(cls, v: date | None) -> date | None:
        """Validate call date is not too far in future."""
        if v is not None:
            from datetime import date as dt_date, timedelta

            max_future = dt_date.today() + timedelta(days=730)  # 2 years
            if v > max_future:
                raise ValueError("call_date cannot be more than 2 years in the future")
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
    call_date: date = Field(..., description="Date of the call assignment")
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
    def validate_not_empty(
        cls, v: list[CallAssignmentCreate]
    ) -> list[CallAssignmentCreate]:
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


# ============================================================================
# Bulk Update Schemas
# ============================================================================


class BulkCallAssignmentUpdateInput(BaseModel):
    """Schema for bulk update input - what fields can be updated."""

    person_id: UUID | None = Field(None, description="New person ID to reassign to")


class BulkCallAssignmentUpdateRequest(BaseModel):
    """Schema for bulk updating multiple call assignments."""

    assignment_ids: list[UUID] = Field(
        ..., description="List of call assignment IDs to update"
    )
    updates: BulkCallAssignmentUpdateInput = Field(
        ..., description="Fields to update on all selected assignments"
    )

    @field_validator("assignment_ids")
    @classmethod
    def validate_not_empty(cls, v: list[UUID]) -> list[UUID]:
        """Ensure assignment_ids list is not empty."""
        if not v:
            raise ValueError("assignment_ids list cannot be empty")
        return v


class BulkCallAssignmentUpdateResponse(BaseModel):
    """Schema for bulk update response."""

    updated: int = Field(..., description="Number of assignments updated")
    errors: list[str] = Field(
        default_factory=list, description="Error messages for failed updates"
    )
    assignments: list[CallAssignmentResponse] = Field(
        default_factory=list, description="Updated assignments"
    )


# ============================================================================
# PCAT Generation Schemas
# ============================================================================


class PCATGenerationRequest(BaseModel):
    """Schema for triggering PCAT/DO auto-assignment."""

    assignment_ids: list[UUID] = Field(
        ..., description="Call assignment IDs to generate PCAT/DO for"
    )

    @field_validator("assignment_ids")
    @classmethod
    def validate_not_empty(cls, v: list[UUID]) -> list[UUID]:
        """Ensure assignment_ids list is not empty."""
        if not v:
            raise ValueError("assignment_ids list cannot be empty")
        return v


class PCATAssignmentResult(BaseModel):
    """Schema for a single PCAT/DO assignment result."""

    call_assignment_id: UUID = Field(
        ..., description="Original call assignment ID"
    )
    call_date: date = Field(..., description="Date of the call")
    person_id: UUID = Field(..., description="Person ID")
    person_name: str | None = Field(None, description="Person name")
    pcat_created: bool = Field(
        default=False, description="Whether PCAT assignment was created"
    )
    do_created: bool = Field(
        default=False, description="Whether DO assignment was created"
    )
    pcat_assignment_id: UUID | None = Field(
        None, description="Created PCAT assignment ID"
    )
    do_assignment_id: UUID | None = Field(
        None, description="Created DO assignment ID"
    )
    error: str | None = Field(None, description="Error message if failed")


class PCATGenerationResponse(BaseModel):
    """Schema for PCAT generation response."""

    processed: int = Field(..., description="Number of call assignments processed")
    pcat_created: int = Field(..., description="Number of PCAT assignments created")
    do_created: int = Field(..., description="Number of DO assignments created")
    errors: list[str] = Field(
        default_factory=list, description="Error messages for failed operations"
    )
    results: list[PCATAssignmentResult] = Field(
        default_factory=list, description="Detailed results per call assignment"
    )


# ============================================================================
# Equity Preview Schemas
# ============================================================================


class SimulatedChange(BaseModel):
    """Schema for a simulated change in equity preview."""

    assignment_id: UUID | None = Field(
        None, description="Existing assignment to modify (None for new)"
    )
    call_date: date | None = Field(None, description="Date of call (for new)")
    old_person_id: UUID | None = Field(None, description="Current person (for swap)")
    new_person_id: UUID = Field(..., description="New person to assign")
    call_type: str = Field(default="overnight", description="Type of call")


class EquityPreviewRequest(BaseModel):
    """Schema for equity preview with simulated changes."""

    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")
    simulated_changes: list[SimulatedChange] = Field(
        default_factory=list, description="Simulated changes to preview"
    )


class FacultyEquityDetail(BaseModel):
    """Schema for per-faculty equity details in preview."""

    person_id: UUID = Field(..., description="Faculty person ID")
    name: str = Field(..., description="Faculty name")
    current_sunday_calls: int = Field(
        ..., description="Current Sunday call count"
    )
    current_weekday_calls: int = Field(
        ..., description="Current weekday call count"
    )
    current_total_calls: int = Field(..., description="Current total call count")
    projected_sunday_calls: int = Field(
        ..., description="Projected Sunday calls after changes"
    )
    projected_weekday_calls: int = Field(
        ..., description="Projected weekday calls after changes"
    )
    projected_total_calls: int = Field(
        ..., description="Projected total calls after changes"
    )
    delta: int = Field(..., description="Change in total calls")


class EquityPreviewResponse(BaseModel):
    """Schema for equity preview response."""

    start_date: date
    end_date: date
    current_equity: CallEquityReport = Field(
        ..., description="Current equity distribution"
    )
    projected_equity: CallEquityReport = Field(
        ..., description="Projected equity after simulated changes"
    )
    faculty_details: list[FacultyEquityDetail] = Field(
        default_factory=list, description="Per-faculty current vs projected"
    )
    improvement_score: float = Field(
        ...,
        description="Score indicating equity improvement (-1 to 1, positive is better)",
    )
