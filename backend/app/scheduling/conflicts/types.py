"""
Conflict Type Definitions.

This module defines the type system for schedule conflicts, including
categories, severity levels, and specific conflict types.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConflictCategory(str, Enum):
    """High-level categories of schedule conflicts."""

    TIME_OVERLAP = "time_overlap"  # Multiple assignments at same time
    RESOURCE_CONTENTION = "resource_contention"  # Insufficient resources
    ACGME_VIOLATION = "acgme_violation"  # ACGME compliance violation
    SUPERVISION_ISSUE = "supervision_issue"  # Inadequate supervision
    AVAILABILITY_CONFLICT = "availability_conflict"  # Assignment during absence
    WORKLOAD_IMBALANCE = "workload_imbalance"  # Unfair distribution
    PATTERN_VIOLATION = "pattern_violation"  # Undesirable patterns


class ConflictSeverity(str, Enum):
    """
    Severity levels for conflicts.

    CRITICAL: Regulatory violation, immediate action required
    HIGH: Significant issue, should be resolved soon
    MEDIUM: Problematic but tolerable short-term
    LOW: Suboptimal but acceptable
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(str, Enum):
    """Specific types of schedule conflicts detected."""

    # Time overlap conflicts
    DOUBLE_BOOKING = "double_booking"  # Person scheduled twice at same time
    OVERLAPPING_SHIFTS = "overlapping_shifts"  # Shifts overlap in time

    # Resource contention
    INSUFFICIENT_COVERAGE = "insufficient_coverage"  # Not enough people
    SUPERVISION_RATIO_VIOLATION = "supervision_ratio_violation"  # Too few faculty
    FACILITY_OVERBOOKED = "facility_overbooked"  # Too many in one location

    # ACGME violations
    EIGHTY_HOUR_VIOLATION = "eighty_hour_violation"  # Exceeds 80 hours/week
    ONE_IN_SEVEN_VIOLATION = "one_in_seven_violation"  # No day off in 7 days
    CONTINUOUS_DUTY_VIOLATION = "continuous_duty_violation"  # Exceeds 24+4 hours
    NIGHT_FLOAT_VIOLATION = "night_float_violation"  # Exceeds 6 consecutive nights
    PGY_SHIFT_LENGTH_VIOLATION = "pgy_shift_length_violation"  # Exceeds PGY limits

    # Supervision issues
    UNSUPERVISED_RESIDENT = "unsupervised_resident"  # Resident without faculty
    INADEQUATE_SUPERVISION = "inadequate_supervision"  # Wrong supervision ratio

    # Availability conflicts
    ASSIGNED_DURING_ABSENCE = "assigned_during_absence"  # Scheduled during leave
    ASSIGNED_DURING_DEPLOYMENT = "assigned_during_deployment"  # Military duty
    ASSIGNED_DURING_TDY = "assigned_during_tdy"  # Temporary duty

    # Workload imbalance
    EXCESSIVE_WORKLOAD = "excessive_workload"  # Too many assignments
    INSUFFICIENT_WORKLOAD = "insufficient_workload"  # Too few assignments
    UNFAIR_CALL_DISTRIBUTION = "unfair_call_distribution"  # Unequal call burden

    # Pattern violations
    EXCESSIVE_CONSECUTIVE_DAYS = "excessive_consecutive_days"  # Too many days in a row
    EXCESSIVE_BACK_TO_BACK = "excessive_back_to_back"  # Too many back-to-back shifts
    POOR_ROTATION_SEQUENCING = "poor_rotation_sequencing"  # Suboptimal rotation order


class Conflict(BaseModel):
    """
    Base conflict model representing a schedule conflict.

    This is the core data structure for all detected conflicts,
    providing comprehensive information for analysis and resolution.
    """

    # Identification
    conflict_id: str = Field(description="Unique identifier for this conflict")
    category: ConflictCategory
    conflict_type: ConflictType
    severity: ConflictSeverity

    # Description
    title: str = Field(description="Brief title describing the conflict")
    description: str = Field(description="Detailed description of the conflict")

    # Temporal information
    start_date: date
    end_date: date
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # Affected entities
    affected_people: list[UUID] = Field(default_factory=list)
    affected_blocks: list[UUID] = Field(default_factory=list)
    affected_assignments: list[UUID] = Field(default_factory=list)

    # Severity scoring (0.0 - 1.0)
    impact_score: float = Field(ge=0.0, le=1.0, description="Overall impact score")
    urgency_score: float = Field(ge=0.0, le=1.0, description="How urgent to resolve")
    complexity_score: float = Field(
        ge=0.0, le=1.0, description="Complexity of resolution"
    )

    # Context
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context specific to conflict type"
    )

    # Resolution metadata
    is_auto_resolvable: bool = Field(default=False)
    resolution_difficulty: str = Field(default="medium")  # easy, medium, hard
    estimated_resolution_time_minutes: int = Field(default=0)

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflict_id": "conf_123",
                "category": "acgme_violation",
                "conflict_type": "eighty_hour_violation",
                "severity": "critical",
                "title": "80-Hour Work Week Violation",
                "description": "Resident exceeded 80 hours in week starting 2024-01-08",
                "start_date": "2024-01-08",
                "end_date": "2024-01-14",
                "affected_people": ["uuid1", "uuid2"],
                "impact_score": 0.9,
                "urgency_score": 0.95,
                "complexity_score": 0.6,
            }
        }


class TimeOverlapConflict(Conflict):
    """
    Conflict where a person is assigned to multiple things at the same time.

    Examples:
        - Double-booked for clinic and procedure
        - Overlapping on-call and inpatient rotation
    """

    category: ConflictCategory = ConflictCategory.TIME_OVERLAP

    # Specific fields for time overlap
    overlapping_assignment_ids: list[UUID] = Field(default_factory=list)
    overlap_duration_hours: float = Field(default=0.0)

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflict_id": "conf_overlap_123",
                "category": "time_overlap",
                "conflict_type": "double_booking",
                "severity": "high",
                "title": "Double Booking Detected",
                "description": "Dr. Smith scheduled for both clinic and procedure block",
                "overlapping_assignment_ids": ["assignment1", "assignment2"],
                "overlap_duration_hours": 6.0,
            }
        }


class ResourceContentionConflict(Conflict):
    """
    Conflict where there are insufficient resources for requirements.

    Examples:
        - Not enough faculty for supervision ratios
        - Too many residents in one clinic
        - Insufficient backup coverage
    """

    category: ConflictCategory = ConflictCategory.RESOURCE_CONTENTION

    # Resource information
    resource_type: str = Field(
        description="Type of resource (faculty, space, equipment)"
    )
    required_count: int = Field(description="Number required")
    available_count: int = Field(description="Number available")
    deficit: int = Field(description="Shortfall amount")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflict_id": "conf_resource_123",
                "category": "resource_contention",
                "conflict_type": "supervision_ratio_violation",
                "severity": "critical",
                "title": "Insufficient Faculty Coverage",
                "description": "3 PGY-1 residents require 2 faculty, only 1 assigned",
                "resource_type": "faculty",
                "required_count": 2,
                "available_count": 1,
                "deficit": 1,
            }
        }


class ACGMEViolationConflict(Conflict):
    """
    Conflict representing an ACGME compliance violation.

    Examples:
        - Exceeding 80-hour work week
        - Working more than 6 consecutive days
        - Exceeding 24+4 continuous duty hours
    """

    category: ConflictCategory = ConflictCategory.ACGME_VIOLATION
    severity: ConflictSeverity = ConflictSeverity.CRITICAL  # Always critical

    # ACGME-specific information
    acgme_rule: str = Field(description="Which ACGME rule is violated")
    person_id: UUID
    person_name: str
    pgy_level: int | None = None

    # Violation details
    threshold_value: float = Field(description="Maximum allowed value")
    actual_value: float = Field(description="Actual value detected")
    excess_amount: float = Field(description="Amount over threshold")

    # Duty hour details (if applicable)
    total_hours: float | None = None
    average_weekly_hours: float | None = None
    consecutive_days: int | None = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflict_id": "conf_acgme_123",
                "category": "acgme_violation",
                "conflict_type": "eighty_hour_violation",
                "severity": "critical",
                "title": "80-Hour Rule Violation",
                "description": "Resident exceeded weekly duty hour limit",
                "acgme_rule": "80-hour work week",
                "person_id": "uuid_resident",
                "person_name": "Dr. Johnson",
                "pgy_level": 2,
                "threshold_value": 80.0,
                "actual_value": 86.5,
                "excess_amount": 6.5,
                "average_weekly_hours": 86.5,
            }
        }


class SupervisionConflict(Conflict):
    """
    Conflict related to supervision requirements.

    Examples:
        - PGY-1 residents without adequate supervision
        - Wrong faculty-to-resident ratio
        - No attending present
    """

    category: ConflictCategory = ConflictCategory.SUPERVISION_ISSUE

    # Supervision details
    resident_ids: list[UUID] = Field(default_factory=list)
    pgy1_count: int = Field(default=0)
    pgy2_3_count: int = Field(default=0)
    faculty_ids: list[UUID] = Field(default_factory=list)
    faculty_count: int = Field(default=0)
    required_faculty_count: int = Field(default=0)

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflict_id": "conf_supervision_123",
                "category": "supervision_issue",
                "conflict_type": "inadequate_supervision",
                "severity": "critical",
                "title": "Inadequate Faculty Supervision",
                "description": "2 PGY-1 residents require 1 faculty, none assigned",
                "pgy1_count": 2,
                "pgy2_3_count": 1,
                "faculty_count": 0,
                "required_faculty_count": 1,
            }
        }


class ConflictSummary(BaseModel):
    """
    Summary statistics for a set of conflicts.

    Used for dashboard displays and reporting.
    """

    total_conflicts: int = 0

    # By severity
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # By category
    by_category: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)

    # By entity
    affected_people_count: int = 0
    affected_blocks_count: int = 0

    # Resolution metrics
    auto_resolvable_count: int = 0
    requires_manual_count: int = 0

    # Scores
    average_impact_score: float = 0.0
    average_urgency_score: float = 0.0
    average_complexity_score: float = 0.0

    # Timeline
    earliest_date: date | None = None
    latest_date: date | None = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_conflicts": 15,
                "critical_count": 3,
                "high_count": 5,
                "medium_count": 4,
                "low_count": 3,
                "affected_people_count": 8,
                "auto_resolvable_count": 6,
                "average_impact_score": 0.65,
            }
        }


class ConflictTimeline(BaseModel):
    """
    Timeline representation of conflicts for visualization.

    Used to generate Gantt charts and timeline views showing
    when conflicts occur and their severity over time.
    """

    # Timeline parameters
    start_date: date
    end_date: date

    # Timeline data points
    timeline_entries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of {date, conflicts[], severity_score} entries",
    )

    # Severity heatmap (date -> severity score 0-1)
    severity_by_date: dict[str, float] = Field(default_factory=dict)

    # Conflict count by date
    count_by_date: dict[str, int] = Field(default_factory=dict)

    # People timeline (person_id -> list of conflict dates)
    conflicts_by_person: dict[str, list[str]] = Field(default_factory=dict)

    # Category distribution over time
    category_timeline: list[dict[str, Any]] = Field(
        default_factory=list, description="Category distribution per week/day"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "severity_by_date": {
                    "2024-01-08": 0.85,
                    "2024-01-15": 0.62,
                },
                "count_by_date": {
                    "2024-01-08": 3,
                    "2024-01-15": 2,
                },
            }
        }
