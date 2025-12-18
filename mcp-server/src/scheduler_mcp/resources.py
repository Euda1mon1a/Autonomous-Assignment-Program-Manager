"""
Resource definitions for the Scheduler MCP server.

Resources provide read-only access to scheduling data and system state.
They are automatically refreshed and can be subscribed to for updates.
"""

import logging
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Response Models


class AssignmentInfo(BaseModel):
    """Information about a single assignment."""

    assignment_id: str
    person_id: str
    person_name: str
    block_name: str
    rotation: str
    start_date: date
    end_date: date
    is_supervising: bool
    pgy_level: int | None = None


class CoverageMetrics(BaseModel):
    """Coverage metrics for a time period."""

    total_days: int
    covered_days: int
    coverage_rate: float = Field(ge=0.0, le=1.0)
    understaffed_days: int
    overstaffed_days: int
    average_faculty_per_day: float
    average_residents_per_day: float


class ScheduleStatusResource(BaseModel):
    """Current schedule status resource."""

    query_timestamp: datetime
    date_range_start: date
    date_range_end: date
    total_assignments: int
    active_conflicts: int
    pending_swaps: int
    coverage_metrics: CoverageMetrics
    assignments: list[AssignmentInfo]
    last_generated: datetime | None = None
    generation_algorithm: str | None = None


class ViolationInfo(BaseModel):
    """Information about a compliance violation."""

    violation_type: str
    severity: str  # "critical", "warning", "info"
    person_id: str
    person_name: str
    date_range: tuple[date, date]
    description: str
    details: dict[str, Any]


class ComplianceMetrics(BaseModel):
    """ACGME compliance metrics."""

    overall_compliance_rate: float = Field(ge=0.0, le=1.0)
    work_hour_violations: int
    consecutive_duty_violations: int
    rest_period_violations: int
    supervision_violations: int
    total_violations: int
    residents_affected: int


class ComplianceSummaryResource(BaseModel):
    """ACGME compliance summary resource."""

    query_timestamp: datetime
    date_range_start: date
    date_range_end: date
    metrics: ComplianceMetrics
    violations: list[ViolationInfo]
    warnings: list[ViolationInfo]
    recommendations: list[str]


# Resource Functions


async def get_schedule_status(
    start_date: date | None = None,
    end_date: date | None = None,
) -> ScheduleStatusResource:
    """
    Get current schedule status including assignments and coverage metrics.

    This resource provides a comprehensive view of the current schedule state,
    including all assignments, coverage statistics, and active issues.

    Args:
        start_date: Start date for schedule query (defaults to today)
        end_date: End date for schedule query (defaults to 30 days from start)

    Returns:
        ScheduleStatusResource containing current schedule state

    Raises:
        ValueError: If date range is invalid
    """
    from datetime import timedelta

    # Set defaults
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(f"Fetching schedule status for {start_date} to {end_date}")

    # TODO: Replace with actual database queries
    # This is a placeholder implementation
    dummy_assignments = [
        AssignmentInfo(
            assignment_id="assign-001",
            person_id="person-001",
            person_name="Dr. Smith",
            block_name="Block A",
            rotation="Emergency Medicine",
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            is_supervising=True,
            pgy_level=None,
        ),
        AssignmentInfo(
            assignment_id="assign-002",
            person_id="person-002",
            person_name="Dr. Johnson",
            block_name="Block B",
            rotation="Internal Medicine",
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            is_supervising=False,
            pgy_level=2,
        ),
    ]

    coverage = CoverageMetrics(
        total_days=(end_date - start_date).days,
        covered_days=(end_date - start_date).days,
        coverage_rate=0.98,
        understaffed_days=2,
        overstaffed_days=0,
        average_faculty_per_day=3.5,
        average_residents_per_day=8.2,
    )

    return ScheduleStatusResource(
        query_timestamp=datetime.now(),
        date_range_start=start_date,
        date_range_end=end_date,
        total_assignments=len(dummy_assignments),
        active_conflicts=0,
        pending_swaps=1,
        coverage_metrics=coverage,
        assignments=dummy_assignments,
        last_generated=datetime.now() - timedelta(hours=2),
        generation_algorithm="hybrid",
    )


async def get_compliance_summary(
    start_date: date | None = None,
    end_date: date | None = None,
) -> ComplianceSummaryResource:
    """
    Get ACGME compliance summary for a date range.

    This resource analyzes the schedule for ACGME work hour violations,
    supervision requirements, and duty hour restrictions.

    Args:
        start_date: Start date for compliance analysis (defaults to today)
        end_date: End date for compliance analysis (defaults to 30 days from start)

    Returns:
        ComplianceSummaryResource containing compliance metrics and violations

    Raises:
        ValueError: If date range is invalid
    """
    from datetime import timedelta

    # Set defaults
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(f"Fetching compliance summary for {start_date} to {end_date}")

    # TODO: Replace with actual compliance validation logic
    # This is a placeholder implementation
    dummy_violations = [
        ViolationInfo(
            violation_type="work_hour_limit",
            severity="warning",
            person_id="person-003",
            person_name="Dr. Williams",
            date_range=(start_date, start_date + timedelta(days=7)),
            description="Exceeded 80-hour weekly work limit",
            details={"hours_worked": 82, "limit": 80},
        )
    ]

    metrics = ComplianceMetrics(
        overall_compliance_rate=0.95,
        work_hour_violations=1,
        consecutive_duty_violations=0,
        rest_period_violations=0,
        supervision_violations=0,
        total_violations=1,
        residents_affected=1,
    )

    recommendations = [
        "Consider redistributing hours from Dr. Williams to reduce workload",
        "Monitor upcoming week for potential violations",
    ]

    return ComplianceSummaryResource(
        query_timestamp=datetime.now(),
        date_range_start=start_date,
        date_range_end=end_date,
        metrics=metrics,
        violations=dummy_violations,
        warnings=[],
        recommendations=recommendations,
    )
