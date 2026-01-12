"""Fairness audit API routes.

Provides endpoints for faculty workload fairness analysis
across call, FMIT, clinic, admin, and academic time.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.fairness_audit_service import FairnessAuditService

router = APIRouter(prefix="/fairness", tags=["fairness"])


@router.get("/audit")
async def get_fairness_audit(
    start_date: date = Query(..., description="Start date for audit period"),
    end_date: date = Query(..., description="End date for audit period"),
    include_titled_faculty: bool = Query(
        False, description="Include PD, APD, OIC, Dept Chief in analysis"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get fairness audit report for date range.

    Returns workload statistics across 5 categories:
    - call: Overnight call shifts
    - fmit: FMIT weeks
    - clinic: Clinic half-days
    - admin: Admin half-days (GME, DFM)
    - academic: Academic half-days (LEC, ADV)

    Also includes:
    - Jain's fairness index (0-1, where 1 is perfectly fair)
    - Outlier detection (faculty > 1.25x or < 0.75x mean)
    - Per-faculty workload breakdown
    """
    if start_date > end_date:
        raise HTTPException(400, "start_date must be before end_date")

    service = FairnessAuditService(db)
    report = await service.generate_audit_report(
        start_date, end_date, include_titled_faculty
    )
    return report.to_dict()


@router.get("/faculty/{faculty_id}/workload")
async def get_faculty_workload(
    faculty_id: str,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    include_titled_faculty: bool = Query(
        True,
        description="Include PD, APD, OIC, Dept Chief (default True for individual lookup)",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get workload breakdown for a specific faculty member.

    Returns counts for each workload category and total weighted score.
    Note: include_titled_faculty defaults to True here so PD/APD can look up their own workload.
    """
    if start_date > end_date:
        raise HTTPException(400, "start_date must be before end_date")

    service = FairnessAuditService(db)
    report = await service.generate_audit_report(
        start_date, end_date, include_titled_faculty
    )

    # Find this faculty in report
    for workload in report.workloads:
        if workload.person_id == faculty_id:
            return workload.to_dict()

    raise HTTPException(404, f"Faculty {faculty_id} not found in workload data")


@router.get("/summary")
async def get_fairness_summary(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get a compact fairness summary (lighter than full audit).

    Returns key metrics without per-faculty breakdown.
    """
    if start_date > end_date:
        raise HTTPException(400, "start_date must be before end_date")

    service = FairnessAuditService(db)
    report = await service.generate_audit_report(start_date, end_date)

    return {
        "period": {
            "start": str(report.period_start),
            "end": str(report.period_end),
        },
        "faculty_count": report.faculty_count,
        "fairness_index": round(report.fairness_index, 3),
        "workload_spread": report.workload_stats.spread,
        "outlier_count": {
            "high": len(report.high_workload_faculty),
            "low": len(report.low_workload_faculty),
        },
    }
