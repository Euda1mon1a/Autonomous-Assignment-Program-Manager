"""FMIT Assignment CRUD schemas for 52-week planner.

Provides Pydantic schemas for:
- FMIT week assignment create/update/delete operations
- Bulk assignment operations
- Year grid view with all faculty assignments
- Conflict detection and validation responses
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentStatus(str, Enum):
    """Status of an FMIT week assignment."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class FMITAssignmentCreate(BaseModel):
    """Schema for creating an FMIT week assignment."""

    faculty_id: UUID = Field(..., description="UUID of the faculty member to assign")
    week_date: date = Field(
        ..., description="Any date within the target week (normalized to Friday)"
    )
    created_by: str = Field(
        default="system", max_length=255, description="User creating the assignment"
    )
    notes: str | None = Field(None, max_length=2000, description="Optional notes")

    @field_validator("week_date")
    @classmethod
    def validate_week_date(cls, v: date) -> date:
        """Validate week_date is not in the past (allow some flexibility)."""
        from datetime import timedelta

        # Allow assigning up to 30 days in the past for corrections
        min_date = date.today() - timedelta(days=30)
        if v < min_date:
            raise ValueError("week_date cannot be more than 30 days in the past")
        return v


class FMITAssignmentUpdate(BaseModel):
    """Schema for updating an FMIT week assignment."""

    faculty_id: UUID | None = Field(
        None, description="New faculty member (for reassignment)"
    )
    notes: str | None = Field(None, max_length=2000, description="Updated notes")
    status: AssignmentStatus | None = Field(None, description="Update status")


class FMITAssignmentResponse(BaseModel):
    """Response schema for a single FMIT week assignment."""

    faculty_id: UUID = Field(..., description="Faculty member UUID")
    faculty_name: str = Field(..., description="Faculty member name")
    week_start: date = Field(..., description="Week start date (Friday)")
    week_end: date = Field(..., description="Week end date (Thursday)")
    assignment_ids: list[UUID] = Field(
        default_factory=list, description="Individual block assignment IDs"
    )
    rotation_template_id: UUID | None = Field(
        None, description="FMIT rotation template ID"
    )
    is_complete: bool = Field(
        False, description="Whether all 14 blocks are assigned for the week"
    )
    block_count: int = Field(0, description="Number of blocks assigned")
    status: AssignmentStatus = Field(
        default=AssignmentStatus.CONFIRMED, description="Assignment status"
    )
    notes: str | None = Field(None, description="Assignment notes")
    created_at: datetime | None = Field(None, description="When assignment was created")
    created_by: str | None = Field(None, description="Who created the assignment")

    model_config = ConfigDict(from_attributes=True)


class FMITAssignmentDeleteResponse(BaseModel):
    """Response schema for deleting FMIT assignment."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Result message")
    deleted_assignment_ids: list[UUID] = Field(
        default_factory=list, description="IDs of deleted block assignments"
    )
    deleted_count: int = Field(0, description="Number of block assignments deleted")


# =============================================================================
# Bulk Operations Schemas
# =============================================================================


class FMITBulkAssignmentItem(BaseModel):
    """Single item in bulk assignment request."""

    faculty_id: UUID = Field(..., description="Faculty member UUID")
    week_date: date = Field(..., description="Target week date")
    notes: str | None = Field(None, max_length=500, description="Optional notes")


class FMITBulkAssignmentRequest(BaseModel):
    """Request schema for bulk FMIT assignments."""

    assignments: list[FMITBulkAssignmentItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of assignments to create (max 100)",
    )
    created_by: str = Field(
        default="system", max_length=255, description="User creating assignments"
    )
    skip_conflicts: bool = Field(
        False, description="Skip assignments that conflict instead of failing"
    )
    dry_run: bool = Field(False, description="Validate only, don't create assignments")


class FMITBulkAssignmentResult(BaseModel):
    """Result for a single item in bulk assignment."""

    faculty_id: UUID
    week_date: date
    success: bool
    message: str
    assignment_ids: list[UUID] = Field(default_factory=list)
    error_code: str | None = None


class FMITBulkAssignmentResponse(BaseModel):
    """Response schema for bulk FMIT assignments."""

    total_requested: int = Field(..., description="Total assignments requested")
    successful_count: int = Field(0, description="Successfully created")
    failed_count: int = Field(0, description="Failed to create")
    skipped_count: int = Field(0, description="Skipped due to conflicts")
    results: list[FMITBulkAssignmentResult] = Field(
        default_factory=list, description="Per-item results"
    )
    dry_run: bool = Field(False, description="Was this a dry run?")
    warnings: list[str] = Field(default_factory=list, description="Warnings")


# =============================================================================
# Year Grid Schemas
# =============================================================================


class WeekSlot(BaseModel):
    """Represents a single week slot in the year grid."""

    week_number: int = Field(..., ge=1, le=53, description="Week number (1-53)")
    week_start: date = Field(..., description="Week start date (Friday)")
    week_end: date = Field(..., description="Week end date (Thursday)")
    is_current_week: bool = Field(False, description="Is this the current week")
    is_past: bool = Field(False, description="Is this week in the past")
    faculty_id: UUID | None = Field(None, description="Assigned faculty ID")
    faculty_name: str | None = Field(None, description="Assigned faculty name")
    is_complete: bool = Field(False, description="All blocks assigned")
    has_conflict: bool = Field(False, description="Has scheduling conflict")
    conflict_reason: str | None = Field(None, description="Conflict description")


class FacultyYearSummary(BaseModel):
    """Summary of a faculty member's FMIT load for the year."""

    faculty_id: UUID
    faculty_name: str
    total_weeks: int = Field(0, description="Total weeks assigned this year")
    completed_weeks: int = Field(0, description="Weeks already completed")
    upcoming_weeks: int = Field(0, description="Future weeks scheduled")
    target_weeks: float = Field(0.0, description="Fair share target")
    variance: float = Field(0.0, description="Deviation from target")
    is_balanced: bool = Field(True, description="Within acceptable range")
    week_dates: list[date] = Field(
        default_factory=list, description="All assigned week start dates"
    )


class YearGridResponse(BaseModel):
    """Response schema for 52-week year grid view."""

    year: int = Field(..., description="Calendar year")
    academic_year_start: date = Field(..., description="Academic year start (July 1)")
    academic_year_end: date = Field(..., description="Academic year end (June 30)")
    weeks: list[WeekSlot] = Field(
        default_factory=list, description="All weeks in the year"
    )
    faculty_summaries: list[FacultyYearSummary] = Field(
        default_factory=list, description="Per-faculty load summaries"
    )
    total_weeks: int = Field(52, description="Total weeks in year")
    assigned_weeks: int = Field(0, description="Weeks with assignments")
    unassigned_weeks: int = Field(0, description="Weeks without assignments")
    coverage_percentage: float = Field(0.0, description="Coverage rate")
    fairness_index: float = Field(
        0.0, description="Jain's fairness index (0-1, higher is better)"
    )
    generated_at: datetime = Field(..., description="Generation timestamp")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Conflict Detection Schemas
# =============================================================================


class ConflictType(str, Enum):
    """Types of FMIT scheduling conflicts."""

    LEAVE_OVERLAP = "leave_overlap"
    BACK_TO_BACK = "back_to_back"
    ALREADY_ASSIGNED = "already_assigned"
    OVERLOAD = "overload"
    UNAVAILABLE = "unavailable"


class ConflictDetail(BaseModel):
    """Details about a scheduling conflict."""

    conflict_type: ConflictType
    severity: str = Field(..., description="critical, warning, or info")
    description: str
    faculty_id: UUID | None = None
    faculty_name: str | None = None
    week_date: date | None = None
    blocking_absence_id: UUID | None = None
    blocking_absence_type: str | None = None


class ConflictCheckResponse(BaseModel):
    """Response for conflict checking before assignment."""

    can_assign: bool = Field(..., description="Whether assignment can proceed")
    conflicts: list[ConflictDetail] = Field(
        default_factory=list, description="Detected conflicts"
    )
    warnings: list[str] = Field(default_factory=list, description="Warnings")
    suggestions: list[str] = Field(
        default_factory=list, description="Alternative suggestions"
    )


# =============================================================================
# Operation Result Schemas
# =============================================================================


class FMITOperationResult(BaseModel):
    """Generic operation result for FMIT actions."""

    success: bool
    message: str
    assignment_ids: list[UUID] = Field(default_factory=list)
    error_code: str | None = None
    warnings: list[str] = Field(default_factory=list)
