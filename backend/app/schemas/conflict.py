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
    faculty_id: UUID
    faculty_name: str
    conflict_type: ConflictTypeEnum
    severity: ConflictSeverityEnum
    description: str

    # Related entities
    fmit_week: date | None = None
    leave_id: UUID | None = None
    assignment_id: UUID | None = None
    residency_block_id: UUID | None = None


class ConflictInfo(ConflictBase):
    """Detailed conflict information for detection results."""
    # Additional metadata for grouping and analysis
    start_date: date | None = None
    end_date: date | None = None
    affected_blocks: list[UUID] = Field(default_factory=list)
    related_people: list[UUID] = Field(default_factory=list)

    # ACGME-specific data
    hours_worked: float | None = None
    consecutive_days: int | None = None
    supervision_ratio: float | None = None

    # Recommendations
    suggested_resolution: str | None = None


class ConflictAlertCreate(BaseModel):
    """Schema for creating a conflict alert."""
    faculty_id: UUID
    conflict_type: ConflictTypeEnum
    severity: ConflictSeverityEnum
    fmit_week: date
    description: str
    leave_id: UUID | None = None
    swap_id: UUID | None = None


class ConflictAlertUpdate(BaseModel):
    """Schema for updating a conflict alert."""
    status: ConflictStatusEnum | None = None
    resolution_notes: str | None = None


class ConflictAlertResponse(BaseModel):
    """Schema for conflict alert response."""
    id: UUID
    faculty_id: UUID
    conflict_type: ConflictTypeEnum
    severity: ConflictSeverityEnum
    fmit_week: date
    description: str
    status: ConflictStatusEnum

    # Related entities
    leave_id: UUID | None = None
    swap_id: UUID | None = None

    # Status tracking
    created_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by_id: UUID | None = None
    resolved_at: datetime | None = None
    resolved_by_id: UUID | None = None
    resolution_notes: str | None = None

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
    person_id: UUID
    person_name: str
    check_period_start: date
    check_period_end: date

    # 80-hour work week compliance
    weekly_hours: dict[str, float] = Field(default_factory=dict)  # week_start -> hours
    hours_violations: list[str] = Field(default_factory=list)

    # 1-in-7 day off compliance
    consecutive_work_days: list[dict] = Field(default_factory=list)  # [{start, end, days}]
    rest_day_violations: list[str] = Field(default_factory=list)

    # Overall compliance
    is_compliant: bool = True
    violation_count: int = 0


class SupervisionRatioCheck(BaseModel):
    """Schema for supervision ratio checking results."""
    block_id: UUID
    block_date: date
    block_time: str
    rotation_name: str

    # Counts
    resident_count: int
    pgy1_count: int
    pgy2_3_count: int
    faculty_count: int

    # Ratios (actual vs required)
    pgy1_ratio_actual: float | None = None
    pgy1_ratio_required: float = 2.0  # 1:2 for PGY-1
    pgy2_3_ratio_actual: float | None = None
    pgy2_3_ratio_required: float = 4.0  # 1:4 for PGY-2/3

    # Compliance
    is_compliant: bool = True
    violations: list[str] = Field(default_factory=list)
