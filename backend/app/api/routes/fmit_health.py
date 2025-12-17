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
from sqlalchemy import and_
from sqlalchemy.orm import Session

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


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_coverage_percentage(db: Session, start_date: date, end_date: date) -> float:
    """Calculate overall coverage percentage for FMIT assignments in date range."""
    # Get all FMIT blocks in the date range
    total_blocks = db.query(Block).filter(
        and_(
            Block.date >= start_date,
            Block.date <= end_date,
            Block.service_type == "FMIT"  # Assuming FMIT blocks have this service_type
        )
    ).count()

    if total_blocks == 0:
        return 100.0

    # Get covered blocks (those with assignments)
    covered_blocks = db.query(Block).join(Assignment).filter(
        and_(
            Block.date >= start_date,
            Block.date <= end_date,
            Block.service_type == "FMIT"
        )
    ).distinct().count()

    return (covered_blocks / total_blocks * 100.0) if total_blocks > 0 else 100.0


def get_health_status(db: Session) -> str:
    """Determine overall health status based on metrics."""
    # Count critical issues
    critical_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    # Check pending swaps
    pending_swaps = db.query(SwapRecord).filter(
        SwapRecord.status == SwapStatus.PENDING
    ).count()

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
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Get metrics
    total_swaps_this_month = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= datetime.combine(month_start, datetime.min.time()),
            SwapRecord.requested_at <= datetime.combine(month_end, datetime.max.time())
        )
    ).count()

    pending_swaps = db.query(SwapRecord).filter(
        SwapRecord.status == SwapStatus.PENDING
    ).count()

    active_alerts = db.query(ConflictAlert).filter(
        ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
    ).count()

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

    critical_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

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
    pending_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.PENDING).count()
    approved_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.APPROVED).count()
    executed_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.EXECUTED).count()
    rejected_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.REJECTED).count()
    cancelled_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.CANCELLED).count()
    rolled_back_swaps = db.query(SwapRecord).filter(SwapRecord.status == SwapStatus.ROLLED_BACK).count()

    # Alert counts
    active_alerts = db.query(ConflictAlert).filter(
        ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
    ).count()
    new_alerts = db.query(ConflictAlert).filter(ConflictAlert.status == ConflictAlertStatus.NEW).count()
    acknowledged_alerts = db.query(ConflictAlert).filter(ConflictAlert.status == ConflictAlertStatus.ACKNOWLEDGED).count()
    resolved_alerts = db.query(ConflictAlert).filter(ConflictAlert.status == ConflictAlertStatus.RESOLVED).count()

    # Alerts by severity
    critical_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()
    warning_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.WARNING,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()
    info_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.INFO,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    # Recent swap activity (last 10)
    recent_swaps = db.query(SwapRecord).order_by(SwapRecord.requested_at.desc()).limit(10).all()
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
    recent_alert_list = db.query(ConflictAlert).order_by(ConflictAlert.created_at.desc()).limit(10).all()
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
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    month_start_dt = datetime.combine(month_start, datetime.min.time())
    month_end_dt = datetime.combine(month_end, datetime.max.time())

    # Swap metrics
    total_swaps_this_month = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt
        )
    ).count()

    pending_swaps = db.query(SwapRecord).filter(
        SwapRecord.status == SwapStatus.PENDING
    ).count()

    # Coverage
    coverage = calculate_coverage_percentage(db, today, today + timedelta(days=30))

    # Approval rate
    completed_swaps = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt,
            SwapRecord.status.in_([SwapStatus.APPROVED, SwapStatus.EXECUTED, SwapStatus.REJECTED])
        )
    ).count()

    approved_or_executed = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt,
            SwapRecord.status.in_([SwapStatus.APPROVED, SwapStatus.EXECUTED])
        )
    ).count()

    approval_rate = (approved_or_executed / completed_swaps * 100.0) if completed_swaps > 0 else 0.0

    # Average processing time (for executed swaps)
    executed_swaps_with_times = db.query(SwapRecord).filter(
        and_(
            SwapRecord.status == SwapStatus.EXECUTED,
            SwapRecord.executed_at.isnot(None),
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt
        )
    ).all()

    if executed_swaps_with_times:
        total_hours = sum(
            (swap.executed_at - swap.requested_at).total_seconds() / 3600
            for swap in executed_swaps_with_times
        )
        avg_processing_time = total_hours / len(executed_swaps_with_times)
    else:
        avg_processing_time = None

    # Active alerts
    active_alerts = db.query(ConflictAlert).filter(
        ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
    ).count()

    # Alert resolution rate
    total_alerts = db.query(ConflictAlert).filter(
        ConflictAlert.created_at >= month_start_dt
    ).count()

    resolved_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.created_at >= month_start_dt,
            ConflictAlert.status == ConflictAlertStatus.RESOLVED
        )
    ).count()

    alert_resolution_rate = (resolved_alerts / total_alerts * 100.0) if total_alerts > 0 else 0.0

    # Critical alerts
    critical_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    # Swap type breakdown
    one_to_one_count = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt,
            SwapRecord.swap_type == SwapType.ONE_TO_ONE
        )
    ).count()

    absorb_count = db.query(SwapRecord).filter(
        and_(
            SwapRecord.requested_at >= month_start_dt,
            SwapRecord.requested_at <= month_end_dt,
            SwapRecord.swap_type == SwapType.ABSORB
        )
    ).count()

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
    end_date: date | None = Query(None, description="End date (default: 30 days from start)"),
    db: Session = Depends(get_db),
):
    """
    Get coverage report for FMIT assignments over a date range.

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

    # Build week-by-week report
    weeks = []
    current = start_date

    while current <= end_date:
        week_end = min(current + timedelta(days=6), end_date)

        # Get FMIT blocks for this week
        week_blocks = db.query(Block).filter(
            and_(
                Block.date >= current,
                Block.date <= week_end,
                Block.service_type == "FMIT"
            )
        ).all()

        total_slots = len(week_blocks)

        # Get covered blocks (with assignments)
        covered_count = 0
        faculty_names = set()

        for block in week_blocks:
            assignments = db.query(Assignment).filter(Assignment.block_id == block.id).all()
            if assignments:
                covered_count += 1
                for assignment in assignments:
                    person = db.query(Person).filter(Person.id == assignment.person_id).first()
                    if person:
                        faculty_names.add(f"{person.first_name} {person.last_name}")

        week_coverage = (covered_count / total_slots * 100.0) if total_slots > 0 else 100.0

        weeks.append(CoverageReportItem(
            week_start=current,
            total_fmit_slots=total_slots,
            covered_slots=covered_count,
            uncovered_slots=total_slots - covered_count,
            coverage_percentage=week_coverage,
            faculty_assigned=sorted(faculty_names),
        ))

        current = week_end + timedelta(days=1)

    return CoverageReport(
        start_date=start_date,
        end_date=end_date,
        total_weeks=len(weeks),
        overall_coverage_percentage=overall_coverage,
        weeks=weeks,
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
    critical_count = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    warning_count = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.WARNING,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    info_count = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.severity == ConflictSeverity.INFO,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )
    ).count()

    total_count = critical_count + warning_count + info_count

    # Counts by type (active only)
    by_type = {}
    for conflict_type in ConflictType:
        count = db.query(ConflictAlert).filter(
            and_(
                ConflictAlert.conflict_type == conflict_type,
                ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
            )
        ).count()
        by_type[conflict_type.value] = count

    # Counts by status (all)
    by_status = {}
    for status in ConflictAlertStatus:
        count = db.query(ConflictAlert).filter(ConflictAlert.status == status).count()
        by_status[status.value] = count

    # Oldest unresolved alert
    oldest_unresolved_alert = db.query(ConflictAlert).filter(
        ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
    ).order_by(ConflictAlert.created_at.asc()).first()

    oldest_unresolved = oldest_unresolved_alert.created_at if oldest_unresolved_alert else None

    # Average resolution time (for resolved alerts in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    resolved_alerts = db.query(ConflictAlert).filter(
        and_(
            ConflictAlert.status == ConflictAlertStatus.RESOLVED,
            ConflictAlert.resolved_at.isnot(None),
            ConflictAlert.created_at >= thirty_days_ago
        )
    ).all()

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
