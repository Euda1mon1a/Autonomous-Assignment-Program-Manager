"""
Core type definitions for the Residency Scheduler.

This module provides TypedDict definitions for common data structures
used throughout the application, improving type safety and IDE support.
"""

from datetime import date
from typing import Literal, NotRequired, TypedDict


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
    end: str  # ISO format date string


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


class SwapMatchResult(TypedDict):
    """
    Result of swap candidate matching.

    Contains compatibility analysis for potential schedule swap partners,
    including overall score and breakdown of match factors.
    """

    candidate_id: str
    compatibility_score: float
    match_factors: dict[str, float]
    is_eligible: bool


class ACGMEViolation(TypedDict):
    """
    ACGME compliance violation details.

    Documents specific violations of ACGME work hour rules,
    including severity, affected parties, and dates.
    """

    rule_id: str
    rule_name: str
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    affected_person_id: NotRequired[str]
    affected_date: NotRequired[date]


class NotificationPayload(TypedDict):
    """
    Notification message payload.

    Structured data for sending notifications to users via
    various channels (email, in-app, etc.).
    """

    recipient_id: str
    notification_type: str
    title: str
    message: str
    data: NotRequired[dict[str, str]]


class SwapDetails(TypedDict):
    """
    Comprehensive swap execution details.

    Extended information about swap requests and execution,
    including validation results, timestamps, and status tracking.
    """

    swap_id: str
    success: bool
    source_faculty_id: str
    source_faculty_name: NotRequired[str]
    target_faculty_id: NotRequired[str]
    target_faculty_name: NotRequired[str]
    source_week: str  # ISO format date
    target_week: NotRequired[str]  # ISO format date
    swap_type: Literal["one_to_one", "absorb"]
    status: Literal[
        "pending", "approved", "executed", "rejected", "cancelled", "rolled_back"
    ]
    executed_at: NotRequired[str]  # ISO format datetime
    rolled_back_at: NotRequired[str]  # ISO format datetime
    rollback_reason: NotRequired[str]
    can_rollback: NotRequired[bool]
    message: NotRequired[str]
    error_code: NotRequired[str]


class CoverageReportItem(TypedDict):
    """
    Coverage information for a specific time period.

    Detailed coverage statistics for a block, week, or other time unit.
    """

    period_start: str  # ISO format date
    period_end: str  # ISO format date
    total_blocks: int
    covered_blocks: int
    uncovered_blocks: int
    coverage_percentage: float
    faculty_assigned: NotRequired[list[str]]


class CoverageReport(TypedDict):
    """
    Schedule coverage statistics report.

    Comprehensive coverage analysis for a date range,
    including overall statistics and period breakdowns.
    """

    start_date: str  # ISO format date
    end_date: str  # ISO format date
    overall_coverage_percentage: float
    total_blocks: int
    covered_blocks: int
    uncovered_blocks: int
    coverage_by_period: NotRequired[list[CoverageReportItem]]
    gaps: NotRequired[list[dict[str, str]]]
    recommendations: NotRequired[list[str]]


class ValidationResultDict(TypedDict):
    """
    General validation result (TypedDict version).

    Generic validation result structure for schedule validation,
    ACGME compliance checks, and other validation operations.
    Note: Use this for dict returns; Pydantic ValidationResult
    exists in schemas.schedule for API responses.
    """

    valid: bool
    errors: list[str]
    warnings: NotRequired[list[str]]
    total_violations: NotRequired[int]
    coverage_rate: NotRequired[float]
    statistics: NotRequired[dict[str, int | float]]


class ScheduleGenerationMetrics(TypedDict):
    """
    Detailed metrics from schedule generation.

    Comprehensive statistics about the schedule generation process,
    including solver performance, constraint satisfaction, and quality metrics.
    """

    status: Literal["success", "partial", "failed"]
    total_assignments: int
    total_blocks: int
    coverage_percentage: float
    violation_count: int
    fairness_score: NotRequired[float]
    solver_time_seconds: NotRequired[float]
    solver_status: NotRequired[str]
    branches_explored: NotRequired[int]
    conflicts_detected: NotRequired[int]
    acgme_compliant: NotRequired[bool]
    generated_at: NotRequired[str]  # ISO format datetime


class ResilienceAnalysisResult(TypedDict):
    """
    Resilience framework analysis result.

    Extended resilience metrics including N-1/N-2 contingency analysis,
    defense levels, and system health indicators.
    """

    utilization_rate: float
    safety_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]
    defense_level: NotRequired[int]  # 1-5
    n1_vulnerabilities: int
    n2_vulnerabilities: int
    n1_pass: bool
    n2_pass: bool
    buffer_remaining: NotRequired[float]
    load_shedding_active: NotRequired[bool]
    fallback_schedules_available: NotRequired[int]
    immediate_actions: NotRequired[list[str]]
    watch_items: NotRequired[list[str]]


class WorkloadDistribution(TypedDict):
    """
    Workload distribution for a person.

    Statistics about individual workload including assignments,
    utilization, and fairness metrics.
    """

    person_id: str
    person_name: str
    pgy_level: NotRequired[int]
    target_blocks: int
    actual_blocks: int
    utilization_percent: float
    variance: int  # actual - target
    fairness_score: NotRequired[float]


class AnalyticsReport(TypedDict):
    """
    General analytics report structure.

    Common structure for various analytics reports including
    monthly summaries, compliance reports, and workload analysis.
    """

    report_type: str
    period_start: str  # ISO format date
    period_end: str  # ISO format date
    summary: dict[str, int | float | str]
    metrics: NotRequired[dict[str, dict[str, float | str]]]
    charts: NotRequired[dict[str, list[dict]]]
    recommendations: NotRequired[list[str]]
    generated_at: str  # ISO format datetime
