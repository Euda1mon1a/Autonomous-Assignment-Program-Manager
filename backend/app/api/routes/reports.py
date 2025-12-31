"""Report generation API routes for PDF reports."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.reports import (
    AnalyticsReportRequest,
    ComplianceReportRequest,
    FacultySummaryReportRequest,
    ReportResponse,
    ScheduleReportRequest,
)
from app.services.reports.templates.analytics_report import AnalyticsReportTemplate
from app.services.reports.templates.compliance_report import ComplianceReportTemplate
from app.services.reports.templates.faculty_summary_report import (
    FacultySummaryReportTemplate,
)
from app.services.reports.templates.schedule_report import ScheduleReportTemplate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/schedule", response_model=ReportResponse)
async def generate_schedule_report(
    request: ScheduleReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Generate schedule overview PDF report.

    Generates a comprehensive schedule report showing:
    - Overall schedule statistics
    - Assignment details by person
    - Coverage summary by rotation
    - Optional detailed daily breakdown

    Args:
        request: Schedule report request parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file as streaming response

    Example:
        POST /api/reports/schedule
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "include_details": true,
            "include_logo": true,
            "include_page_numbers": true
        }
    """
    try:
        logger.info(
            f"User {current_user.email} generating schedule report "
            f"from {request.start_date} to {request.end_date}"
        )

        # Generate report
        template = ScheduleReportTemplate(db)
        pdf_bytes = template.generate(request)

        # Create filename
        filename = f"schedule_report_{request.start_date}_to_{request.end_date}.pdf"

        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error generating schedule report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate schedule report",
        )


@router.post("/compliance", response_model=ReportResponse)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Generate ACGME compliance PDF report.

    Generates a detailed compliance report showing:
    - Overall compliance status
    - Violations by resident and type
    - 80-hour rule compliance
    - 1-in-7 rule compliance
    - Supervision ratio analysis

    Args:
        request: Compliance report request parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file as streaming response

    Example:
        POST /api/reports/compliance
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "pgy_levels": [1, 2, 3],
            "include_violations_only": false,
            "include_logo": true,
            "include_page_numbers": true
        }
    """
    try:
        logger.info(
            f"User {current_user.email} generating compliance report "
            f"from {request.start_date} to {request.end_date}"
        )

        # Generate report
        template = ComplianceReportTemplate(db)
        pdf_bytes = template.generate(request)

        # Create filename
        filename = f"compliance_report_{request.start_date}_to_{request.end_date}.pdf"

        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error generating compliance report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate compliance report",
        )


@router.post("/analytics", response_model=ReportResponse)
async def generate_analytics_report(
    request: AnalyticsReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Generate workload analytics PDF report.

    Generates a comprehensive analytics report showing:
    - Workload distribution statistics
    - Fairness metrics (Gini coefficient, std dev)
    - Rotation distribution analysis
    - Faculty supervision metrics

    Args:
        request: Analytics report request parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file as streaming response

    Example:
        POST /api/reports/analytics
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "include_charts": true,
            "include_fairness_metrics": true,
            "include_trends": true,
            "include_logo": true,
            "include_page_numbers": true
        }
    """
    try:
        logger.info(
            f"User {current_user.email} generating analytics report "
            f"from {request.start_date} to {request.end_date}"
        )

        # Generate report
        template = AnalyticsReportTemplate(db)
        pdf_bytes = template.generate(request)

        # Create filename
        filename = f"analytics_report_{request.start_date}_to_{request.end_date}.pdf"

        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error generating analytics report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate analytics report",
        )


@router.post("/faculty-summary", response_model=ReportResponse)
async def generate_faculty_summary_report(
    request: FacultySummaryReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Generate faculty summary PDF report.

    Generates a summary report for faculty members showing:
    - Individual faculty workload statistics
    - Supervision metrics
    - Assignment distribution
    - Performance indicators

    Note: This endpoint currently returns analytics data.
    A dedicated FacultySummaryReportTemplate can be implemented
    for more specialized faculty reporting.

    Args:
        request: Faculty summary report request parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file as streaming response

    Example:
        POST /api/reports/faculty-summary
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "faculty_ids": ["uuid1", "uuid2"],
            "include_workload": true,
            "include_supervision": true,
            "include_logo": true,
            "include_page_numbers": true
        }
    """
    try:
        logger.info(
            f"User {current_user.email} generating faculty summary report "
            f"from {request.start_date} to {request.end_date}"
        )

        # Use dedicated faculty summary template
        template = FacultySummaryReportTemplate(db)
        pdf_bytes = template.generate(request)

        # Create filename
        filename = f"faculty_summary_{request.start_date}_to_{request.end_date}.pdf"

        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(
            f"Error generating faculty summary report: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate faculty summary report",
        )
