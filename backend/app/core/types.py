"""
Core type definitions for the Residency Scheduler.

This module provides TypedDict definitions for common data structures
used throughout the application, improving type safety and IDE support.
"""
from typing import TypedDict, NotRequired, Literal
from datetime import date, datetime
from uuid import UUID


class ScheduleMetrics(TypedDict):
    """Metrics for a generated schedule."""
    total_assignments: int
    coverage_percentage: float
    violation_count: int
    fairness_score: NotRequired[float]


class ComplianceResult(TypedDict):
    """Result of an ACGME compliance check."""
    is_compliant: bool
    violations: list[str]
    score: float
    severity: Literal["critical", "high", "medium", "low"]


class ValidationContext(TypedDict):
    """Context for validation operations."""
    schedule_id: str
    person_id: NotRequired[str]
    start_date: date
    end_date: date


class PersonInfo(TypedDict):
    """Basic person information."""
    id: str
    name: str
    email: str
    person_type: Literal["resident", "faculty"]
    pgy_level: NotRequired[int]


class AssignmentInfo(TypedDict):
    """Assignment information for scheduling."""
    block_id: str
    person_id: str
    rotation_template_id: str
    role: Literal["primary", "supervising", "backup"]


class BlockInfo(TypedDict):
    """Schedule block information."""
    id: str
    date: date
    time_of_day: Literal["AM", "PM"]


class SwapInfo(TypedDict):
    """Swap request information."""
    source_faculty_id: str
    target_faculty_id: NotRequired[str]
    week_start: date
    week_end: date
    status: Literal["pending", "approved", "rejected", "completed"]


class ResilienceMetrics(TypedDict):
    """Resilience framework metrics."""
    utilization_rate: float
    safety_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]
    n1_vulnerabilities: int
    n2_vulnerabilities: int


class APIResponse(TypedDict):
    """Standard API response structure."""
    success: bool
    data: NotRequired[dict]
    error: NotRequired[str]
    message: NotRequired[str]


class DutyHoursPeriod(TypedDict):
    """Period information for duty hours breakdown."""
    start: str  # ISO format date string
    end: str    # ISO format date string


class DutyHoursDetails(TypedDict):
    """Detailed duty hours statistics."""
    total: float
    average_weekly: float
    weekend: float
    night: float
    weekday: float


class DutyHoursDays(TypedDict):
    """Days worked statistics."""
    worked: int
    total_in_period: int


class DutyHoursBreakdown(TypedDict):
    """
    Comprehensive duty hours breakdown for ACGME compliance tracking.

    Returned by advanced ACGME validator to provide detailed analysis
    of resident work hours including total, weekend, and night hours.
    """
    person_id: str
    person_name: str
    pgy_level: NotRequired[int]
    period: DutyHoursPeriod
    hours: DutyHoursDetails
    days: DutyHoursDays


class FatigueFactors(TypedDict):
    """Contributing factors to fatigue score."""
    consecutive_days: int
    night_shifts: int
    weekend_days: int
    days_since_off: int
    total_hours_14d: float


class FatigueScore(TypedDict):
    """
    Fatigue assessment result for a resident.

    Tracks workload intensity and fatigue risk based on consecutive
    duty days, night shifts, weekend work, and total hours.
    """
    person_id: str
    person_name: str
    pgy_level: NotRequired[int]
    date: str  # ISO format date string
    fatigue_score: float
    risk_level: Literal["NONE", "LOW", "MODERATE", "HIGH"]
    factors: FatigueFactors
    error: NotRequired[str]


class RecoveryNeeds(TypedDict):
    """
    Recommended recovery time for a fatigued resident.

    Calculates rest hours needed and consecutive days off based
    on current fatigue levels and work intensity.
    """
    person_id: str
    person_name: NotRequired[str]
    current_fatigue_score: float
    recovery_hours_needed: float
    recommended_days_off: int
    risk_level: Literal["NONE", "LOW", "MODERATE", "HIGH"]


class FatiguePredictionDay(TypedDict):
    """Single day fatigue prediction."""
    date: str  # ISO format date string
    fatigue_score: float
    risk_level: Literal["NONE", "LOW", "MODERATE", "HIGH"]


class FatigueTrend(TypedDict):
    """
    Multi-day fatigue trend forecast.

    Projects fatigue levels across upcoming days based on current
    schedule and historical patterns.
    """
    person_id: str
    person_name: str
    start_date: str  # ISO format date string
    days_ahead: int
    current_fatigue: float
    trend: Literal["INCREASING", "DECREASING", "STABLE"]
    predictions: list[FatiguePredictionDay]
    error: NotRequired[str]


class HighRiskResident(TypedDict):
    """
    High-risk resident fatigue alert.

    Detailed information about residents approaching or exceeding
    safe fatigue thresholds.
    """
    person_id: str
    person_name: str
    pgy_level: NotRequired[int]
    fatigue_score: float
    risk_level: Literal["NONE", "LOW", "MODERATE", "HIGH"]
    recovery_hours_needed: float
    recommended_days_off: int
    factors: FatigueFactors


class AuditStatistics(TypedDict):
    """
    Audit log statistics summary.

    Aggregated counts and metrics for audit trail analysis,
    including breakdowns by action, entity type, and severity.
    """
    totalEntries: int
    entriesByAction: dict[str, int]
    entriesByEntityType: dict[str, int]
    entriesBySeverity: dict[str, int]
    acgmeOverrideCount: int
    uniqueUsers: int
