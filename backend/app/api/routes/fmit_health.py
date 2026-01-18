"""FMIT Health Check API routes.

Provides health check and monitoring endpoints for the FMIT (Faculty Member In Training)
subsystem, including:
- Overall health status
- Detailed system status (pending swaps, active alerts, etc.)
- FMIT-specific metrics (total swaps, coverage, etc.)
- Coverage reports by date range
- Alert summaries by severity
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, Session

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType

router = APIRouter()


# ============================================================================
# Response Schemas
# ============================================================================


class FMITHealthStatus(BaseModel):
    """Overall FMIT subsystem health status."""

    timestamp: datetime
    status: str  # "healthy", "degraded", "critical"
    total_swaps_this_month: int
    pending_swap_requests: int
    active_conflict_alerts: int
    coverage_percentage: float
    issues: list[str] = []
    recommendations: list[str] = []


class FMITDetailedStatus(BaseModel):
    """Detailed FMIT system status."""

    timestamp: datetime
    pending_swaps: int
    approved_swaps: int
    executed_swaps: int
    rejected_swaps: int
    cancelled_swaps: int
    rolled_back_swaps: int
    active_alerts: int
    new_alerts: int
    acknowledged_alerts: int
    resolved_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    recent_swap_activity: list[dict]
    recent_alerts: list[dict]


class FMITMetrics(BaseModel):
    """FMIT-specific metrics."""

    timestamp: datetime
    total_swaps_this_month: int
    pending_swap_requests: int
    active_conflict_alerts: int
    coverage_percentage: float
    swap_approval_rate: float
    average_swap_processing_time_hours: float | None
    alert_resolution_rate: float
    critical_alerts_count: int
    one_to_one_swaps_count: int
    absorb_swaps_count: int


class CoverageReportItem(BaseModel):
    """Coverage information for a specific week."""

    week_start: date
    total_fmit_slots: int
    covered_slots: int
    uncovered_slots: int
    coverage_percentage: float
    faculty_assigned: list[str]


class CoverageReport(BaseModel):
    """Coverage report for a date range."""

    start_date: date
    end_date: date
    total_weeks: int
    overall_coverage_percentage: float
    weeks: list[CoverageReportItem]


class AlertSummaryBySeverity(BaseModel):
    """Alert counts grouped by severity."""

    timestamp: datetime
    critical_count: int
    warning_count: int
    info_count: int
    total_count: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    oldest_unresolved: datetime | None
    average_resolution_time_hours: float | None


class CoverageGap(BaseModel):
    """Represents a coverage gap with details."""

    gap_id: str
    date: date
    time_of_day: str
    block_id: str
    severity: str  # "critical", "high", "medium", "low"
    days_until: int
    affected_area: str
    department: str | None
    current_assignments: int
    required_assignments: int
    gap_size: int


class CoverageGapsResponse(BaseModel):
    """Response for coverage gaps endpoint."""

    timestamp: datetime
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    gaps_by_period: dict[str, int]  # "daily", "weekly", "monthly"
    gaps: list[CoverageGap]


class CoverageSuggestion(BaseModel):
    """Auto-suggested solution for a coverage gap."""

    gap_id: str
    suggestion_type: str  # "assign_available", "swap_recommended", "overtime"
    priority: int  # 1-5, 1 being highest
    faculty_candidates: list[str]
    estimated_conflict_score: float
    reasoning: str
    alternative_dates: list[date] | None


class CoverageSuggestionsResponse(BaseModel):
    """Response for coverage suggestions endpoint."""

    timestamp: datetime
    total_suggestions: int
    gaps_addressed: int
    suggestions: list[CoverageSuggestion]


class CoverageForecast(BaseModel):
    """Forecast for future coverage gaps."""

    forecast_date: date
    predicted_coverage_percentage: float
    predicted_gaps: int
    confidence_level: float  # 0-1
    trend: str  # "improving", "stable", "declining"
    risk_factors: list[str]


class CoverageForecastResponse(BaseModel):
    """Response for coverage forecast endpoint."""

    timestamp: datetime
    forecast_start_date: date
    forecast_end_date: date
    overall_trend: str
    average_predicted_coverage: float
    forecasts: list[CoverageForecast]


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_coverage_percentage(
    db: Session, start_date: date, end_date: date
) -> float:
    """Calculate overall coverage percentage for FMIT assignments in date range."""
    # Get all FMIT blocks in the date range
    total_blocks = (
        db.query(Block)
        .filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
                Block.service_type
                == "FMIT",  # Assuming FMIT blocks have this service_type
            )
        )
        .count()
    )

    if total_blocks == 0:
        return 100.0

    # Get covered blocks (those with assignments)
    covered_blocks = (
        db.query(Block)
        .join(Assignment)
        .filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
                Block.service_type == "FMIT",
            )
        )
        .distinct()
        .count()
    )

    return (covered_blocks / total_blocks * 100.0) if total_blocks > 0 else 100.0


def get_health_status(db: Session) -> str:
    """Determine overall health status based on metrics."""
    # Count critical issues
    critical_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    # Check pending swaps
    pending_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.PENDING).count()
    )

    # Calculate recent coverage
    today = date.today()
    coverage = calculate_coverage_percentage(db, today, today + timedelta(days=30))

    # Determine status
    if critical_alerts > 5 or coverage < 70:
        return "critical"
    elif critical_alerts > 0 or pending_swaps > 10 or coverage < 85:
        return "degraded"
    else:
        return "healthy"


def classify_gap_severity(days_until: int, gap_size: int) -> str:
    """Classify gap severity based on urgency and size."""
    if days_until <= 3:
        return "critical"
    elif days_until <= 7:
        return "high" if gap_size > 1 else "medium"
    elif days_until <= 14:
        return "medium" if gap_size > 1 else "low"
    else:
        return "low"


def detect_coverage_gaps(
    db: Session, start_date: date, end_date: date
) -> list[CoverageGap]:
    """Detect all coverage gaps in the date range."""
    gaps = []
    today = date.today()

    # Get all FMIT blocks in range
    # Eager load assignments and rotation_template to avoid N+1 queries
    blocks = (
        db.query(Block)
        .filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
                Block.service_type == "FMIT",
            )
        )
        .limit(100)
        .all()
    )

    # Build a map of block_id -> assignments to avoid N+1
    block_ids = [block.id for block in blocks]
    assignments_by_block = {}
    if block_ids:
        all_assignments = (
            db.query(Assignment)
            .options(joinedload(Assignment.rotation_template))
            .filter(Assignment.block_id.in_(block_ids))
            .all()
        )
        for assignment in all_assignments:
            if assignment.block_id not in assignments_by_block:
                assignments_by_block[assignment.block_id] = []
            assignments_by_block[assignment.block_id].append(assignment)

    for block in blocks:
        # Get assignments for this block from our map
        assignments = assignments_by_block.get(block.id, [])

        current_count = len(assignments)
        required_count = 1  # Minimum required for FMIT coverage

        if current_count < required_count:
            gap_size = required_count - current_count
            days_until = (block.date - today).days
            severity = classify_gap_severity(days_until, gap_size)

            # Determine affected area based on rotation template
            affected_area = "FMIT"
            department = None

            if assignments:
                for assignment in assignments:
                    if assignment.rotation_template:
                        affected_area = assignment.rotation_template.name
                        if assignment.rotation_template.requires_specialty:
                            department = assignment.rotation_template.requires_specialty
                        break

            gaps.append(
                CoverageGap(
                    gap_id=f"{block.id}_{block.date}_{block.time_of_day}",
                    date=block.date,
                    time_of_day=block.time_of_day,
                    block_id=str(block.id),
                    severity=severity,
                    days_until=days_until,
                    affected_area=affected_area,
                    department=department,
                    current_assignments=current_count,
                    required_assignments=required_count,
                    gap_size=gap_size,
                )
            )

    return gaps


def find_available_faculty(
    db: Session, target_date: date, time_of_day: str
) -> list[str]:
    """Find faculty available for a specific date/time."""
    # Get all faculty (people with faculty role)
    all_faculty = (
        db.query(Person)
        .filter(Person.role.in_(["faculty", "attending", "chief"]))
        .limit(100)
        .all()
    )

    if not all_faculty:
        return []

    # Find block for target date/time
    target_block = (
        db.query(Block)
        .filter(and_(Block.date == target_date, Block.time_of_day == time_of_day))
        .first()
    )

    if not target_block:
        return []

    # Pre-fetch: Get all same-time blocks ONCE (prevents N+1)
    same_time_blocks = (
        db.query(Block)
        .filter(and_(Block.date == target_date, Block.time_of_day == time_of_day))
        .all()
    )
    same_time_block_ids = {b.id for b in same_time_blocks}

    # Pre-fetch: Get all assignments for the target block (prevents N+1)
    target_block_assignments = (
        db.query(Assignment).filter(Assignment.block_id == target_block.id).all()
    )
    assigned_person_ids = {a.person_id for a in target_block_assignments}

    # Pre-fetch: Get all faculty assignments on same-time blocks (prevents N+1)
    faculty_ids = [f.id for f in all_faculty]
    conflicting_assignments = (
        db.query(Assignment.person_id)
        .filter(
            and_(
                Assignment.person_id.in_(faculty_ids),
                Assignment.block_id.in_(same_time_block_ids),
            )
        )
        .all()
    )
    faculty_with_conflicts = {a.person_id for a in conflicting_assignments}

    # Now check availability using pre-fetched data (no more queries in loop)
    available = []
    for faculty in all_faculty:
        # Skip if already assigned to target block
        if faculty.id in assigned_person_ids:
            continue

        # Skip if has conflicts on same-time blocks
        if faculty.id in faculty_with_conflicts:
            continue

        available.append(f"{faculty.first_name} {faculty.last_name}")

    return available


def calculate_conflict_score(db: Session, faculty_id: str, target_date: date) -> float:
    """Calculate a conflict score for assigning faculty to a date (0-1, lower is better)."""
    score = 0.0

    # Check assignments in surrounding dates (workload balance)
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)

    week_assignments = (
        db.query(Assignment)
        .join(Block)
        .filter(
            and_(
                Assignment.person_id == faculty_id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
        )
        .count()
    )

    # More assignments = higher score
    score += min(week_assignments / 10.0, 0.5)

    # Check for adjacent day assignments (prefer spacing)
    adjacent_dates = [target_date - timedelta(days=1), target_date + timedelta(days=1)]
    adjacent_assignments = (
        db.query(Assignment)
        .join(Block)
        .filter(
            and_(Assignment.person_id == faculty_id, Block.date.in_(adjacent_dates))
        )
        .count()
    )

    score += adjacent_assignments * 0.15

    # Check for active alerts
    active_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.faculty_id == faculty_id,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    score += min(active_alerts / 5.0, 0.2)

    return min(score, 1.0)


def analyze_coverage_trend(db: Session, weeks_back: int = 12) -> str:
    """Analyze coverage trend over past weeks."""
    today = date.today()
    coverage_samples = []

    for i in range(weeks_back):
        week_start = today - timedelta(days=(weeks_back - i) * 7)
        week_end = week_start + timedelta(days=6)
        coverage = calculate_coverage_percentage(db, week_start, week_end)
        coverage_samples.append(coverage)

    if len(coverage_samples) < 3:
        return "stable"

    # Calculate trend using simple linear regression
    recent_avg = sum(coverage_samples[-4:]) / 4
    older_avg = sum(coverage_samples[:4]) / 4

    diff = recent_avg - older_avg

    if diff > 5:
        return "improving"
    elif diff < -5:
        return "declining"
    else:
        return "stable"


# ============================================================================
# Routes
# ============================================================================


@router.get("/health", response_model=FMITHealthStatus)
async def get_fmit_health(
    db: Session = Depends(get_db),
):
    """
    Get overall FMIT subsystem health status.

    Returns:
    - Overall status (healthy, degraded, critical)
    - Key metrics (swaps, alerts, coverage)
    - Issues and recommendations
    """
    timestamp = datetime.utcnow()

    # Calculate current month range
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(
            days=1
        )
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Get metrics
    total_swaps_this_month = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at
                >= datetime.combine(month_start, datetime.min.time()),
                SwapRecord.requested_at
                <= datetime.combine(month_end, datetime.max.time()),
            )
        )
        .count()
    )

    pending_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.PENDING).count()
    )

    active_alerts = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            )
        )
        .count()
    )

    # Coverage for next 30 days
    coverage = calculate_coverage_percentage(db, today, today + timedelta(days=30))

    # Determine overall status
    status = get_health_status(db)

    # Build issues and recommendations
    issues = []
    recommendations = []

    if pending_swaps > 10:
        issues.append(f"{pending_swaps} pending swap requests require attention")
        recommendations.append("Review and process pending swap requests")

    if active_alerts > 5:
        issues.append(f"{active_alerts} active conflict alerts")
        recommendations.append("Review and resolve active conflict alerts")

    if coverage < 90:
        issues.append(f"Coverage at {coverage:.1f}% (target: 90%+)")
        recommendations.append("Review uncovered FMIT slots and assign faculty")

    critical_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    if critical_alerts > 0:
        issues.append(f"{critical_alerts} critical alerts require immediate attention")
        recommendations.append("Address critical conflicts immediately")

    return FMITHealthStatus(
        timestamp=timestamp,
        status=status,
        total_swaps_this_month=total_swaps_this_month,
        pending_swap_requests=pending_swaps,
        active_conflict_alerts=active_alerts,
        coverage_percentage=coverage,
        issues=issues,
        recommendations=recommendations,
    )


@router.get("/status", response_model=FMITDetailedStatus)
async def get_fmit_detailed_status(
    db: Session = Depends(get_db),
):
    """
    Get detailed FMIT system status.

    Returns:
    - Swap counts by status
    - Alert counts by status and severity
    - Recent activity
    """
    timestamp = datetime.utcnow()

    # Swap counts by status
    pending_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.PENDING).count()
    )
    approved_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.APPROVED).count()
    )
    executed_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.EXECUTED).count()
    )
    rejected_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.REJECTED).count()
    )
    cancelled_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.CANCELLED).count()
    )
    rolled_back_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.ROLLED_BACK).count()
    )

    # Alert counts
    active_alerts = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            )
        )
        .count()
    )
    new_alerts = (
        db.query(ConflictAlert)
        .filter(ConflictAlert.status == ConflictAlertStatus.NEW)
        .count()
    )
    acknowledged_alerts = (
        db.query(ConflictAlert)
        .filter(ConflictAlert.status == ConflictAlertStatus.ACKNOWLEDGED)
        .count()
    )
    resolved_alerts = (
        db.query(ConflictAlert)
        .filter(ConflictAlert.status == ConflictAlertStatus.RESOLVED)
        .count()
    )

    # Alerts by severity
    critical_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )
    warning_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.WARNING,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )
    info_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.INFO,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    # Recent swap activity (last 10)
    recent_swaps = (
        db.query(SwapRecord).order_by(SwapRecord.requested_at.desc()).limit(10).all()
    )
    recent_swap_activity = [
        {
            "id": str(swap.id),
            "status": swap.status.value,
            "swap_type": swap.swap_type.value,
            "requested_at": swap.requested_at.isoformat(),
            "source_faculty_id": str(swap.source_faculty_id),
            "target_faculty_id": str(swap.target_faculty_id),
        }
        for swap in recent_swaps
    ]

    # Recent alerts (last 10)
    recent_alert_list = (
        db.query(ConflictAlert)
        .order_by(ConflictAlert.created_at.desc())
        .limit(10)
        .all()
    )
    recent_alerts = [
        {
            "id": str(alert.id),
            "severity": alert.severity.value,
            "status": alert.status.value,
            "conflict_type": alert.conflict_type.value,
            "created_at": alert.created_at.isoformat(),
            "faculty_id": str(alert.faculty_id),
        }
        for alert in recent_alert_list
    ]

    return FMITDetailedStatus(
        timestamp=timestamp,
        pending_swaps=pending_swaps,
        approved_swaps=approved_swaps,
        executed_swaps=executed_swaps,
        rejected_swaps=rejected_swaps,
        cancelled_swaps=cancelled_swaps,
        rolled_back_swaps=rolled_back_swaps,
        active_alerts=active_alerts,
        new_alerts=new_alerts,
        acknowledged_alerts=acknowledged_alerts,
        resolved_alerts=resolved_alerts,
        critical_alerts=critical_alerts,
        warning_alerts=warning_alerts,
        info_alerts=info_alerts,
        recent_swap_activity=recent_swap_activity,
        recent_alerts=recent_alerts,
    )


@router.get("/metrics", response_model=FMITMetrics)
async def get_fmit_metrics(
    db: Session = Depends(get_db),
):
    """
    Get FMIT-specific metrics.

    Returns detailed metrics including:
    - Total swaps this month
    - Pending swap requests
    - Active conflict alerts
    - Coverage percentage
    - Swap approval rate
    - Average processing time
    - Alert resolution rate
    - Swap type breakdown
    """
    timestamp = datetime.utcnow()

    # Calculate current month range
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(
            days=1
        )
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    month_start_dt = datetime.combine(month_start, datetime.min.time())
    month_end_dt = datetime.combine(month_end, datetime.max.time())

    # Swap metrics
    total_swaps_this_month = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
            )
        )
        .count()
    )

    pending_swaps = (
        db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.PENDING).count()
    )

    # Coverage
    coverage = calculate_coverage_percentage(db, today, today + timedelta(days=30))

    # Approval rate
    completed_swaps = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
                SwapRecord.status.in_(
                    [SwapStatus.APPROVED, SwapStatus.EXECUTED, SwapStatus.REJECTED]
                ),
            )
        )
        .count()
    )

    approved_or_executed = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
                SwapRecord.status.in_([SwapStatus.APPROVED, SwapStatus.EXECUTED]),
            )
        )
        .count()
    )

    approval_rate = (
        (approved_or_executed / completed_swaps * 100.0) if completed_swaps > 0 else 0.0
    )

    # Average processing time (for executed swaps)
    executed_swaps_with_times = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.status == SwapStatus.EXECUTED,
                SwapRecord.executed_at.isnot(None),
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
            )
        )
        .all()
    )

    if executed_swaps_with_times:
        total_hours = sum(
            (swap.executed_at - swap.requested_at).total_seconds() / 3600
            for swap in executed_swaps_with_times
        )
        avg_processing_time = total_hours / len(executed_swaps_with_times)
    else:
        avg_processing_time = None

    # Active alerts
    active_alerts = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            )
        )
        .count()
    )

    # Alert resolution rate
    total_alerts = (
        db.query(ConflictAlert)
        .filter(ConflictAlert.created_at >= month_start_dt)
        .count()
    )

    resolved_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.created_at >= month_start_dt,
                ConflictAlert.status == ConflictAlertStatus.RESOLVED,
            )
        )
        .count()
    )

    alert_resolution_rate = (
        (resolved_alerts / total_alerts * 100.0) if total_alerts > 0 else 0.0
    )

    # Critical alerts
    critical_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    # Swap type breakdown
    one_to_one_count = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
                SwapRecord.swap_type == SwapType.ONE_TO_ONE,
            )
        )
        .count()
    )

    absorb_count = (
        db.query(SwapRecord)
        .filter(
            and_(
                SwapRecord.requested_at >= month_start_dt,
                SwapRecord.requested_at <= month_end_dt,
                SwapRecord.swap_type == SwapType.ABSORB,
            )
        )
        .count()
    )

    return FMITMetrics(
        timestamp=timestamp,
        total_swaps_this_month=total_swaps_this_month,
        pending_swap_requests=pending_swaps,
        active_conflict_alerts=active_alerts,
        coverage_percentage=coverage,
        swap_approval_rate=approval_rate,
        average_swap_processing_time_hours=avg_processing_time,
        alert_resolution_rate=alert_resolution_rate,
        critical_alerts_count=critical_alerts,
        one_to_one_swaps_count=one_to_one_count,
        absorb_swaps_count=absorb_count,
    )


@router.get("/coverage", response_model=CoverageReport)
async def get_coverage_report(
    start_date: date | None = Query(None, description="Start date (default: today)"),
    end_date: date | None = Query(
        None, description="End date (default: 30 days from start)"
    ),
    period: str = Query(
        "weekly", description="Grouping period: daily, weekly, or monthly"
    ),
    db: Session = Depends(get_db),
):
    """
    Get coverage report for FMIT assignments over a date range.

    Enhanced with:
    - Gap detection by time period (daily, weekly, monthly)
    - Gap severity classification
    - Affected areas/departments

    Returns week-by-week coverage data showing:
    - Total FMIT slots
    - Covered/uncovered slots
    - Coverage percentage
    - Faculty assigned
    """
    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Calculate overall coverage
    overall_coverage = calculate_coverage_percentage(db, start_date, end_date)

    # Build report based on period
    weeks = []
    current = start_date

    # Determine period increment
    if period == "daily":
        increment = 1
    elif period == "monthly":
        increment = 30
    else:  # weekly (default)
        increment = 7

    while current <= end_date:
        if period == "monthly":
            # For monthly, use calendar month boundaries
            if current.month == 12:
                week_end = current.replace(
                    year=current.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                week_end = current.replace(month=current.month + 1, day=1) - timedelta(
                    days=1
                )
            week_end = min(week_end, end_date)
        else:
            week_end = min(current + timedelta(days=increment - 1), end_date)

        # Get FMIT blocks for this period
        week_blocks = (
            db.query(Block)
            .filter(
                and_(
                    Block.date >= current,
                    Block.date <= week_end,
                    Block.service_type == "FMIT",
                )
            )
            .limit(100)
            .all()
        )

        total_slots = len(week_blocks)

        # Eager load assignments and person to avoid N+1 queries
        covered_count = 0
        faculty_names = set()

        if week_blocks:
            block_ids = [b.id for b in week_blocks]
            # Load all assignments with person eager-loaded for this period's blocks
            week_assignments = (
                db.query(Assignment)
                .options(joinedload(Assignment.person))
                .filter(Assignment.block_id.in_(block_ids))
                .all()
            )

            # Build map of block_id -> assignments
            block_assignment_map = {}
            for assignment in week_assignments:
                if assignment.block_id not in block_assignment_map:
                    block_assignment_map[assignment.block_id] = []
                block_assignment_map[assignment.block_id].append(assignment)

            # Count coverage and collect faculty names
            for block in week_blocks:
                assignments = block_assignment_map.get(block.id, [])
                if assignments:
                    covered_count += 1
                    for assignment in assignments:
                        if assignment.person:
                            faculty_names.add(
                                f"{assignment.person.first_name} {assignment.person.last_name}"
                            )

        week_coverage = (
            (covered_count / total_slots * 100.0) if total_slots > 0 else 100.0
        )

        weeks.append(
            CoverageReportItem(
                week_start=current,
                total_fmit_slots=total_slots,
                covered_slots=covered_count,
                uncovered_slots=total_slots - covered_count,
                coverage_percentage=week_coverage,
                faculty_assigned=sorted(faculty_names),
            )
        )

        if period == "monthly":
            # Move to first day of next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
        else:
            current = week_end + timedelta(days=1)

    return CoverageReport(
        start_date=start_date,
        end_date=end_date,
        total_weeks=len(weeks),
        overall_coverage_percentage=overall_coverage,
        weeks=weeks,
    )


@router.get("/coverage/gaps", response_model=CoverageGapsResponse)
async def get_coverage_gaps(
    start_date: date | None = Query(None, description="Start date (default: today)"),
    end_date: date | None = Query(
        None, description="End date (default: 60 days from start)"
    ),
    severity_filter: str | None = Query(
        None, description="Filter by severity: critical, high, medium, low"
    ),
    db: Session = Depends(get_db),
):
    """
    List all coverage gaps with detailed analysis.

    Returns:
    - All coverage gaps in date range
    - Gaps classified by severity (critical, high, medium, low)
    - Affected areas and departments
    - Gap statistics by time period
    """
    timestamp = datetime.utcnow()

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=60)

    # Detect all gaps
    all_gaps = detect_coverage_gaps(db, start_date, end_date)

    # Filter by severity if requested
    if severity_filter:
        all_gaps = [gap for gap in all_gaps if gap.severity == severity_filter.lower()]

    # Count gaps by severity
    critical_gaps = sum(1 for gap in all_gaps if gap.severity == "critical")
    high_priority_gaps = sum(1 for gap in all_gaps if gap.severity == "high")
    medium_priority_gaps = sum(1 for gap in all_gaps if gap.severity == "medium")
    low_priority_gaps = sum(1 for gap in all_gaps if gap.severity == "low")

    # Count gaps by period
    gaps_by_period = {
        "daily": sum(1 for gap in all_gaps if gap.days_until <= 1),
        "weekly": sum(1 for gap in all_gaps if 2 <= gap.days_until <= 7),
        "monthly": sum(1 for gap in all_gaps if 8 <= gap.days_until <= 30),
        "future": sum(1 for gap in all_gaps if gap.days_until > 30),
    }

    return CoverageGapsResponse(
        timestamp=timestamp,
        total_gaps=len(all_gaps),
        critical_gaps=critical_gaps,
        high_priority_gaps=high_priority_gaps,
        medium_priority_gaps=medium_priority_gaps,
        low_priority_gaps=low_priority_gaps,
        gaps_by_period=gaps_by_period,
        gaps=all_gaps,
    )


@router.get("/coverage/suggestions", response_model=CoverageSuggestionsResponse)
async def get_coverage_suggestions(
    start_date: date | None = Query(None, description="Start date (default: today)"),
    end_date: date | None = Query(
        None, description="End date (default: 30 days from start)"
    ),
    max_suggestions: int = Query(
        20, description="Maximum number of suggestions to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Auto-suggest coverage solutions for gaps.

    Returns:
    - Suggested faculty assignments for each gap
    - Conflict scores for each suggestion
    - Alternative dates if primary date has conflicts
    - Reasoning for each suggestion
    """
    timestamp = datetime.utcnow()

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Get all gaps in range
    gaps = detect_coverage_gaps(db, start_date, end_date)

    # Sort gaps by severity (critical first)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda g: (severity_order.get(g.severity, 4), g.days_until))

    suggestions = []

    # Generate suggestions for each gap (up to max_suggestions)
    for gap in gaps[:max_suggestions]:
        # Find available faculty for this slot
        available_faculty = find_available_faculty(db, gap.date, gap.time_of_day)

        if not available_faculty:
            # No one available - suggest swap
            suggestion = CoverageSuggestion(
                gap_id=gap.gap_id,
                suggestion_type="swap_recommended",
                priority=1 if gap.severity == "critical" else 2,
                faculty_candidates=[],
                estimated_conflict_score=1.0,
                reasoning=f"No faculty available on {gap.date}. Consider swap with existing assignments.",
                alternative_dates=None,
            )
        else:
            # Calculate conflict scores for available faculty
            faculty_scores = []
            for faculty_name in available_faculty[:5]:  # Top 5 candidates
                # Get faculty person object
                name_parts = faculty_name.split()
                if len(name_parts) >= 2:
                    person = (
                        db.query(Person)
                        .filter(
                            and_(
                                Person.first_name == name_parts[0],
                                Person.last_name == " ".join(name_parts[1:]),
                            )
                        )
                        .first()
                    )

                    if person:
                        score = calculate_conflict_score(db, str(person.id), gap.date)
                        faculty_scores.append((faculty_name, score))

            # Sort by score (lower is better)
            faculty_scores.sort(key=lambda x: x[1])

            if faculty_scores:
                best_score = faculty_scores[0][1]
                reasoning = f"Recommended: {faculty_scores[0][0]} (conflict score: {best_score:.2f})"
                if best_score < 0.3:
                    reasoning += " - Excellent fit, minimal conflicts"
                elif best_score < 0.6:
                    reasoning += " - Good fit, some workload considerations"
                else:
                    reasoning += " - Available but high workload this week"

                suggestion = CoverageSuggestion(
                    gap_id=gap.gap_id,
                    suggestion_type="assign_available",
                    priority=1 if gap.severity == "critical" else 2,
                    faculty_candidates=[name for name, _ in faculty_scores],
                    estimated_conflict_score=best_score,
                    reasoning=reasoning,
                    alternative_dates=None,
                )
            else:
                suggestion = CoverageSuggestion(
                    gap_id=gap.gap_id,
                    suggestion_type="overtime",
                    priority=1,
                    faculty_candidates=available_faculty,
                    estimated_conflict_score=0.8,
                    reasoning="Consider overtime or additional coverage arrangements",
                    alternative_dates=None,
                )

        suggestions.append(suggestion)

    return CoverageSuggestionsResponse(
        timestamp=timestamp,
        total_suggestions=len(suggestions),
        gaps_addressed=len(suggestions),
        suggestions=suggestions,
    )


@router.get("/coverage/forecast", response_model=CoverageForecastResponse)
async def get_coverage_forecast(
    weeks_ahead: int = Query(12, description="Number of weeks to forecast (1-52)"),
    db: Session = Depends(get_db),
):
    """
    Predict future coverage gaps based on trends.

    Returns:
    - Week-by-week coverage predictions
    - Confidence levels for predictions
    - Trend analysis (improving, stable, declining)
    - Risk factors for each forecast period
    """
    timestamp = datetime.utcnow()
    today = date.today()

    # Limit weeks ahead to reasonable range
    weeks_ahead = min(max(weeks_ahead, 1), 52)

    # Analyze historical trend
    overall_trend = analyze_coverage_trend(db, weeks_back=12)

    # Calculate baseline coverage from recent weeks
    recent_coverage = []
    for i in range(4):
        week_start = today - timedelta(days=(4 - i) * 7)
        week_end = week_start + timedelta(days=6)
        coverage = calculate_coverage_percentage(db, week_start, week_end)
        recent_coverage.append(coverage)

    baseline_coverage = sum(recent_coverage) / len(recent_coverage)

    # Generate forecasts
    forecasts = []
    forecast_coverage_values = []

    for week_num in range(weeks_ahead):
        forecast_date = today + timedelta(days=week_num * 7)
        week_end = forecast_date + timedelta(days=6)

        # Adjust prediction based on trend
        if overall_trend == "improving":
            trend_adjustment = week_num * 0.5
        elif overall_trend == "declining":
            trend_adjustment = -week_num * 0.5
        else:
            trend_adjustment = 0

        predicted_coverage = baseline_coverage + trend_adjustment
        predicted_coverage = max(min(predicted_coverage, 100.0), 0.0)

        # Confidence decreases with time
        confidence = max(0.9 - (week_num * 0.02), 0.5)

        # Calculate predicted gaps based on expected blocks
        expected_blocks_per_week = 10  # Assumption
        predicted_gaps = int(
            expected_blocks_per_week * (100 - predicted_coverage) / 100
        )

        # Identify risk factors
        risk_factors = []

        if predicted_coverage < 85:
            risk_factors.append("Below target coverage threshold (85%)")

        # Check for upcoming holidays or known conflicts
        holiday_blocks = (
            db.query(Block)
            .filter(
                and_(
                    Block.date >= forecast_date,
                    Block.date <= week_end,
                    Block.is_holiday.is_(True),
                )
            )
            .count()
        )

        if holiday_blocks > 0:
            risk_factors.append(
                f"{holiday_blocks} holiday blocks may reduce availability"
            )

        # Check pending swaps affecting this period
        pending_swaps_future = (
            db.query(SwapRecord)
            .filter(
                and_(
                    SwapRecord.status == SwapStatus.PENDING,
                    SwapRecord.created_at
                    <= datetime.combine(week_end, datetime.max.time()),
                )
            )
            .count()
        )

        if pending_swaps_future > 5:
            risk_factors.append(
                f"{pending_swaps_future} pending swaps may impact schedule"
            )

        if week_num > 8 and confidence < 0.7:
            risk_factors.append("Long-range forecast - lower confidence")

        # Determine period trend
        if week_num == 0:
            period_trend = overall_trend
        else:
            prev_coverage = forecasts[-1].predicted_coverage_percentage
            if predicted_coverage > prev_coverage + 2:
                period_trend = "improving"
            elif predicted_coverage < prev_coverage - 2:
                period_trend = "declining"
            else:
                period_trend = "stable"

        forecast = CoverageForecast(
            forecast_date=forecast_date,
            predicted_coverage_percentage=predicted_coverage,
            predicted_gaps=predicted_gaps,
            confidence_level=confidence,
            trend=period_trend,
            risk_factors=risk_factors,
        )

        forecasts.append(forecast)
        forecast_coverage_values.append(predicted_coverage)

    avg_predicted_coverage = sum(forecast_coverage_values) / len(
        forecast_coverage_values
    )

    return CoverageForecastResponse(
        timestamp=timestamp,
        forecast_start_date=today,
        forecast_end_date=today + timedelta(days=weeks_ahead * 7),
        overall_trend=overall_trend,
        average_predicted_coverage=avg_predicted_coverage,
        forecasts=forecasts,
    )


@router.get("/alerts/summary", response_model=AlertSummaryBySeverity)
async def get_alert_summary(
    db: Session = Depends(get_db),
):
    """
    Get summary of conflict alerts grouped by severity.

    Returns:
    - Counts by severity level (critical, warning, info)
    - Counts by conflict type
    - Counts by status
    - Oldest unresolved alert timestamp
    - Average resolution time
    """
    timestamp = datetime.utcnow()

    # Counts by severity (active only)
    critical_count = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    warning_count = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.WARNING,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    info_count = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.severity == ConflictSeverity.INFO,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
        )
        .count()
    )

    total_count = critical_count + warning_count + info_count

    # Counts by type (active only)
    by_type = {}
    for conflict_type in ConflictType:
        count = (
            db.query(ConflictAlert)
            .filter(
                and_(
                    ConflictAlert.conflict_type == conflict_type,
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
            )
            .count()
        )
        by_type[conflict_type.value] = count

    # Counts by status (all)
    by_status = {}
    for status in ConflictAlertStatus:
        count = db.query(ConflictAlert).filter(ConflictAlert.status == status).count()
        by_status[status.value] = count

    # Oldest unresolved alert
    oldest_unresolved_alert = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            )
        )
        .order_by(ConflictAlert.created_at.asc())
        .first()
    )

    oldest_unresolved = (
        oldest_unresolved_alert.created_at if oldest_unresolved_alert else None
    )

    # Average resolution time (for resolved alerts in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    resolved_alerts = (
        db.query(ConflictAlert)
        .filter(
            and_(
                ConflictAlert.status == ConflictAlertStatus.RESOLVED,
                ConflictAlert.resolved_at.isnot(None),
                ConflictAlert.created_at >= thirty_days_ago,
            )
        )
        .all()
    )

    if resolved_alerts:
        total_resolution_hours = sum(
            (alert.resolved_at - alert.created_at).total_seconds() / 3600
            for alert in resolved_alerts
        )
        avg_resolution_time = total_resolution_hours / len(resolved_alerts)
    else:
        avg_resolution_time = None

    return AlertSummaryBySeverity(
        timestamp=timestamp,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        total_count=total_count,
        by_type=by_type,
        by_status=by_status,
        oldest_unresolved=oldest_unresolved,
        average_resolution_time_hours=avg_resolution_time,
    )
