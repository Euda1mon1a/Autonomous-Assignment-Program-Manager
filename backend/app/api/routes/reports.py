"""Report generation API routes for PDF reports."""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_db
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
from app.services.block_quality_report_service import BlockQualityReportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/schedule", response_model=ReportResponse)
async def generate_schedule_report(
    request: ScheduleReportRequest,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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


@router.get("/block-quality")
async def get_block_quality_report(
    block_number: int = Query(..., ge=0, le=13),
    academic_year: int | None = Query(None),
    format: str = Query("summary", pattern="^(summary|full|markdown)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a block quality report (summary/full/markdown)."""
    if academic_year is None:
        today = date.today()
        academic_year = today.year if today.month >= 7 else today.year - 1

    try:
        service = BlockQualityReportService(db)
        report = service.generate_report(block_number, academic_year)

        if format == "markdown":
            return {
                "status": "ok",
                "block_number": block_number,
                "academic_year": academic_year,
                "format": "markdown",
                "content": service.to_markdown(report),
            }

        if format == "summary":
            return {
                "status": "ok",
                "block_number": block_number,
                "academic_year": academic_year,
                "block_dates": report.block_dates.model_dump(),
                "executive_summary": report.executive_summary.model_dump(),
            }

        return report.model_dump()

    except Exception as e:
        logger.error(f"Error generating block quality report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate block quality report"
        )


@router.get("/block-quality/multi")
async def get_multi_block_quality_report(
    blocks: str = Query(
        ..., description="Comma-separated or range, e.g. 10,11 or 10-13"
    ),
    academic_year: int | None = Query(None),
    include_summary: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate block quality summaries for multiple blocks."""
    if academic_year is None:
        today = date.today()
        academic_year = today.year if today.month >= 7 else today.year - 1

    def _parse_blocks(spec: str) -> list[int]:
        items: list[int] = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = part.split("-")
                items.extend(range(int(start), int(end) + 1))
            else:
                items.append(int(part))
        return sorted(set(items))

    try:
        block_numbers = _parse_blocks(blocks)
        service = BlockQualityReportService(db)

        block_reports = []
        for block_num in block_numbers:
            report = service.generate_report(block_num, academic_year)
            block_reports.append(
                {
                    "block_number": block_num,
                    "block_dates": report.block_dates.model_dump(),
                    "executive_summary": report.executive_summary.model_dump(),
                }
            )

        summary = (
            service.generate_summary(block_numbers, academic_year)
            if include_summary
            else None
        )

        return {
            "status": "ok",
            "academic_year": academic_year,
            "blocks": block_reports,
            "summary": summary.model_dump() if summary else None,
        }

    except Exception as e:
        logger.error(f"Error generating multi-block quality report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate multi-block quality report"
        )
