"""Conflict detection schemas."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ConflictSeverityEnum(str, Enum):
    """Severity level of a conflict."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictTypeEnum(str, Enum):
    """Type of schedule conflict."""

    # Cross-system conflicts
    LEAVE_FMIT_OVERLAP = "leave_fmit_overlap"
    RESIDENCY_FMIT_DOUBLE_BOOKING = "residency_fmit_double_booking"

    # Schedule pattern conflicts
    BACK_TO_BACK = "back_to_back"
    EXCESSIVE_ALTERNATING = "excessive_alternating"

    # ACGME compliance violations
    WORK_HOUR_VIOLATION = "work_hour_violation"  # 80-hour weekly limit
    REST_DAY_VIOLATION = "rest_day_violation"  # 1-in-7 day off requirement

    # Supervision conflicts
    SUPERVISION_RATIO_VIOLATION = "supervision_ratio_violation"
    MISSING_SUPERVISION = "missing_supervision"

    # Other conflicts
    CALL_CASCADE = "call_cascade"
    EXTERNAL_COMMITMENT = "external_commitment"


class ConflictStatusEnum(str, Enum):
    """Status of a conflict alert."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ConflictBase(BaseModel):
    """Base conflict information schema."""

    faculty_id: UUID = Field(..., description="Faculty member UUID")
    faculty_name: str = Field(
        ..., min_length=1, max_length=200, description="Faculty member name"
    )
    conflict_type: ConflictTypeEnum = Field(..., description="Type of conflict")
    severity: ConflictSeverityEnum = Field(..., description="Severity level")
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Conflict description"
    )

    # Related entities
    fmit_week: date | None = Field(None, description="FMIT week date")
    leave_id: UUID | None = Field(None, description="Related leave ID")
    assignment_id: UUID | None = Field(None, description="Related assignment ID")
    residency_block_id: UUID | None = Field(None, description="Related block ID")


class ConflictInfo(ConflictBase):
    """Detailed conflict information for detection results."""

    # Additional metadata for grouping and analysis
    start_date: date | None = Field(None, description="Conflict start date")
    end_date: date | None = Field(None, description="Conflict end date")
    affected_blocks: list[UUID] = Field(
        default_factory=list, max_length=100, description="List of affected block UUIDs"
    )
    related_people: list[UUID] = Field(
        default_factory=list, max_length=50, description="List of related person UUIDs"
    )

    # ACGME-specific data
    hours_worked: float | None = Field(None, ge=0, description="Hours worked")
    consecutive_days: int | None = Field(None, ge=0, description="Consecutive work days")
    supervision_ratio: float | None = Field(
        None, ge=0, description="Supervision ratio"
    )

    # Recommendations
    suggested_resolution: str | None = Field(
        None, max_length=500, description="Suggested resolution for conflict"
    )


class ConflictAlertCreate(BaseModel):
    """Schema for creating a conflict alert."""

    faculty_id: UUID = Field(..., description="Faculty member UUID")
    conflict_type: ConflictTypeEnum = Field(..., description="Type of conflict")
    severity: ConflictSeverityEnum = Field(..., description="Severity level")
    fmit_week: date = Field(..., description="FMIT week date")
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Conflict description"
    )
    leave_id: UUID | None = Field(None, description="Related leave ID")
    swap_id: UUID | None = Field(None, description="Related swap ID")


class ConflictAlertUpdate(BaseModel):
    """Schema for updating a conflict alert."""

    status: ConflictStatusEnum | None = Field(None, description="Conflict status")
    resolution_notes: str | None = Field(
        None, max_length=1000, description="Resolution notes"
    )


class ConflictAlertResponse(BaseModel):
    """Schema for conflict alert response."""

    id: UUID = Field(..., description="Conflict alert UUID")
    faculty_id: UUID = Field(..., description="Faculty member UUID")
    conflict_type: ConflictTypeEnum = Field(..., description="Type of conflict")
    severity: ConflictSeverityEnum = Field(..., description="Severity level")
    fmit_week: date = Field(..., description="FMIT week date")
    description: str = Field(..., description="Conflict description")
    status: ConflictStatusEnum = Field(..., description="Current status")

    # Related entities
    leave_id: UUID | None = Field(None, description="Related leave ID")
    swap_id: UUID | None = Field(None, description="Related swap ID")

    # Status tracking
    created_at: datetime = Field(..., description="Creation timestamp")
    acknowledged_at: datetime | None = Field(None, description="Acknowledgment timestamp")
    acknowledged_by_id: UUID | None = Field(None, description="ID of acknowledger")
    resolved_at: datetime | None = Field(None, description="Resolution timestamp")
    resolved_by_id: UUID | None = Field(None, description="ID of resolver")
    resolution_notes: str | None = Field(None, description="Resolution notes")

    class Config:
        from_attributes = True


class ConflictGroup(BaseModel):
    """Schema for grouped conflicts."""

    group_by: str  # "type", "person", "severity", "date"
    group_key: str  # The value being grouped by
    conflict_count: int
    conflicts: list[ConflictInfo]

    # Summary statistics
    severity_breakdown: dict[str, int] = Field(default_factory=dict)
    earliest_date: date | None = None
    latest_date: date | None = None


class ConflictDetectionRequest(BaseModel):
    """Request schema for conflict detection."""

    faculty_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    include_resolved: bool = False
    group_by: str | None = None  # "type", "person", "severity", "date"


class ConflictDetectionResponse(BaseModel):
    """Response schema for conflict detection."""

    total_conflicts: int
    conflicts: list[ConflictInfo]
    groups: list[ConflictGroup] | None = None

    # Summary statistics
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    affected_faculty_count: int = 0


class ACGMEComplianceCheck(BaseModel):
    """Schema for ACGME compliance checking results."""

    person_id: UUID = Field(..., description="Person UUID")
    person_name: str = Field(
        ..., min_length=1, max_length=200, description="Person name"
    )
    check_period_start: date = Field(..., description="Check period start date")
    check_period_end: date = Field(..., description="Check period end date")

    # 80-hour work week compliance
    weekly_hours: dict[str, float] = Field(
        default_factory=dict, description="Weekly hours (week_start -> hours)"
    )
    hours_violations: list[str] = Field(
        default_factory=list, max_length=100, description="List of hour violations"
    )

    # 1-in-7 day off compliance
    consecutive_work_days: list[dict] = Field(
        default_factory=list,
        max_length=100,
        description="Consecutive work periods [{start, end, days}]",
    )
    rest_day_violations: list[str] = Field(
        default_factory=list, max_length=100, description="Rest day violations"
    )

    # Overall compliance
    is_compliant: bool = Field(True, description="Overall compliance status")
    violation_count: int = Field(0, ge=0, description="Total violation count")


class SupervisionRatioCheck(BaseModel):
    """Schema for supervision ratio checking results."""

    block_id: UUID = Field(..., description="Block UUID")
    block_date: date = Field(..., description="Block date")
    block_time: str = Field(..., max_length=20, description="Block time (AM/PM)")
    rotation_name: str = Field(
        ..., min_length=1, max_length=200, description="Rotation name"
    )

    # Counts
    resident_count: int = Field(..., ge=0, description="Total resident count")
    pgy1_count: int = Field(..., ge=0, description="PGY-1 resident count")
    pgy2_3_count: int = Field(..., ge=0, description="PGY-2/3 resident count")
    faculty_count: int = Field(..., ge=0, description="Faculty count")

    # Ratios (actual vs required)
    pgy1_ratio_actual: float | None = Field(None, ge=0, description="Actual PGY-1 ratio")
    pgy1_ratio_required: float = Field(
        2.0, ge=0, description="Required PGY-1 ratio (1:2)"
    )
    pgy2_3_ratio_actual: float | None = Field(
        None, ge=0, description="Actual PGY-2/3 ratio"
    )
    pgy2_3_ratio_required: float = Field(
        4.0, ge=0, description="Required PGY-2/3 ratio (1:4)"
    )

    # Compliance
    is_compliant: bool = Field(True, description="Compliance status")
    violations: list[str] = Field(
        default_factory=list, max_length=50, description="List of violations"
    )
