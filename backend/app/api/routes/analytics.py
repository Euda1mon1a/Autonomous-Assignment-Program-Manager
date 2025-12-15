"""Analytics API routes."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.analytics import AnalyticsService, ReportGenerator, ReportType, ReportFormat
from pydantic import BaseModel, Field


# Pydantic schemas for request/response
class DateRangeParams(BaseModel):
    """Query parameters for date range."""
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")


class OverviewResponse(BaseModel):
    """Response schema for overview metrics."""
    date_range: dict
    coverage: dict
    workload: dict
    absences: dict
    compliance: dict


class WorkloadResponse(BaseModel):
    """Response schema for workload metrics."""
    data: list


class AbsenceResponse(BaseModel):
    """Response schema for absence patterns."""
    summary: dict
    by_person: list
    by_type: dict
    time_series: list


class ComplianceResponse(BaseModel):
    """Response schema for compliance metrics."""
    summary: dict
    by_algorithm: dict
    time_series: list


class UtilizationResponse(BaseModel):
    """Response schema for utilization metrics."""
    summary: dict
    by_day_type: dict
    by_rotation: dict
    time_series: list


class ReportResponse(BaseModel):
    """Response schema for generated reports."""
    report_type: str
    date_range: dict
    generated_at: str
    sections: dict


router = APIRouter()


@router.get("/overview", response_model=OverviewResponse)
async def get_overview_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Get high-level dashboard metrics for a date range.

    Returns:
    - Total assignments and coverage rate
    - Average workload per resident
    - Absence statistics
    - ACGME compliance rate
    - Schedule generation success rate

    This endpoint provides a comprehensive overview suitable for
    dashboard displays and executive summaries.
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
            )

        service = AnalyticsService(db)
        metrics = service.get_overview_metrics(start_date, end_date)

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workload", response_model=WorkloadResponse)
async def get_workload_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    person_id: Optional[UUID] = Query(None, description="Filter by specific person"),
    db: Session = Depends(get_db),
):
    """
    Get detailed workload statistics per person.

    Returns for each person:
    - Total assignments compared to target
    - Breakdown by rotation type
    - Weekend/holiday assignment counts
    - Role distribution (primary, supervising, backup)
    - Utilization percentage

    Useful for:
    - Identifying workload imbalances
    - Tracking individual utilization
    - Ensuring equitable distribution
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
            )

        service = AnalyticsService(db)
        workload = service.get_person_workload(start_date, end_date, person_id)

        return {"data": workload}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/absences", response_model=AbsenceResponse)
async def get_absence_patterns(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Analyze absence patterns and trends.

    Returns:
    - Absence frequency by person
    - Absence types distribution
    - Military vs non-military absences
    - Blocking vs partial absences
    - Monthly time-series data

    Useful for:
    - Identifying high-absence periods
    - Planning for deployments/TDY
    - Understanding absence impact on scheduling
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
            )

        service = AnalyticsService(db)
        patterns = service.get_absence_patterns(start_date, end_date)

        return patterns

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance", response_model=ComplianceResponse)
async def get_compliance_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Calculate ACGME compliance rates and violation trends.

    Returns:
    - Overall compliance rate
    - Violation breakdown by type
    - Success rate by algorithm
    - Override statistics
    - Time-series trends

    Useful for:
    - Monitoring ACGME compliance
    - Identifying recurring violations
    - Evaluating algorithm performance
    - Tracking improvement over time
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
            )

        service = AnalyticsService(db)
        compliance = service.get_compliance_metrics(start_date, end_date)

        return compliance

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/utilization", response_model=UtilizationResponse)
async def get_utilization_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Calculate schedule utilization metrics.

    Returns:
    - Overall utilization rate
    - Utilization by rotation type
    - Utilization by day type (weekday/weekend/holiday)
    - Daily time-series data

    Useful for:
    - Identifying underutilized blocks
    - Optimizing schedule capacity
    - Balancing rotation assignments
    - Tracking utilization trends
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
            )

        service = AnalyticsService(db)
        utilization = service.get_utilization_metrics(start_date, end_date)

        return utilization

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_type}", response_model=ReportResponse)
async def generate_report(
    report_type: ReportType,
    reference_date: Optional[date] = Query(
        None,
        description="Reference date for weekly/monthly/quarterly reports (defaults to today)"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom reports (required if report_type=custom)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom reports (required if report_type=custom)"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate a comprehensive analytics report.

    Report types:
    - weekly: Monday-Sunday report for the reference week
    - monthly: Full month report for the reference month
    - quarterly: 3-month report for the reference quarter
    - custom: Custom date range (requires start_date and end_date)

    Returns all analytics sections:
    - Overview metrics
    - Workload by person
    - Absence patterns
    - Compliance metrics
    - Utilization metrics

    Use /reports/{type}/export for CSV/JSON export.
    """
    try:
        generator = ReportGenerator(db)

        if report_type == ReportType.CUSTOM:
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Custom reports require start_date and end_date parameters"
                )
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
                )

        report = generator.generate_report(
            report_type=report_type,
            reference_date=reference_date,
            start_date=start_date,
            end_date=end_date,
        )

        return report

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_type}/export")
async def export_report(
    report_type: ReportType,
    format: ReportFormat = Query(ReportFormat.JSON, description="Export format (json or csv)"),
    reference_date: Optional[date] = Query(
        None,
        description="Reference date for weekly/monthly/quarterly reports (defaults to today)"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom reports (required if report_type=custom)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom reports (required if report_type=custom)"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate and export a report in the specified format.

    Export formats:
    - json: Structured JSON (default)
    - csv: Comma-separated values (suitable for Excel)

    The exported file will be returned with appropriate Content-Type
    and Content-Disposition headers for download.
    """
    try:
        generator = ReportGenerator(db)

        if report_type == ReportType.CUSTOM:
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Custom reports require start_date and end_date parameters"
                )
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
                )

        # Generate report
        report = generator.generate_report(
            report_type=report_type,
            reference_date=reference_date,
            start_date=start_date,
            end_date=end_date,
        )

        # Export in requested format
        exported = generator.export_report(report, format)

        # Determine filename and content type
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if format == ReportFormat.JSON:
            filename = f"analytics_report_{report_type.value}_{timestamp}.json"
            content_type = "application/json"
        else:  # CSV
            filename = f"analytics_report_{report_type.value}_{timestamp}.csv"
            content_type = "text/csv"

        # Return as downloadable file
        return Response(
            content=exported,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/scheduled/configure")
async def configure_scheduled_report(
    report_type: ReportType = Query(..., description="Type of report to schedule"),
    frequency: str = Query(..., description="Frequency: daily, weekly, or monthly"),
    db: Session = Depends(get_db),
):
    """
    Configure a scheduled report (placeholder).

    This endpoint returns a configuration for scheduled reports.
    Actual implementation would require a task queue (e.g., Celery, APScheduler).

    Args:
    - report_type: Type of report to schedule
    - frequency: How often to generate (daily, weekly, monthly)

    Returns:
    - Schedule configuration
    """
    if frequency not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="frequency must be one of: daily, weekly, monthly"
        )

    generator = ReportGenerator(db)
    config = generator.schedule_report(report_type, frequency)

    return config
