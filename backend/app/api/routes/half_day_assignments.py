"""Half-day assignments API routes.

Provides endpoints for reading expanded half-day schedule data.
This is the frontend-facing API for daily schedule views.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_async_db
from app.schemas.half_day_assignment import (
    HalfDayAssignmentListResponse,
    HalfDayAssignmentRead,
)
from app.services.half_day_schedule_service import HalfDayScheduleService
from app.utils.academic_blocks import get_block_dates

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=HalfDayAssignmentListResponse)
async def list_half_day_assignments(
    block_number: int | None = Query(None, ge=0, le=13, description="Block number"),
    academic_year: int | None = Query(None, description="Academic year (e.g., 2025)"),
    start_date: date | None = Query(None, description="Start date"),
    end_date: date | None = Query(None, description="End date"),
    person_type: str | None = Query(None, description="Filter by person type"),
    db: AsyncSession = Depends(get_async_db),
) -> HalfDayAssignmentListResponse:
    """
    List half-day assignments for a block or date range.

    Either provide (block_number + academic_year) OR (start_date + end_date).

    This endpoint returns the expanded half-day schedule data,
    which includes day-specific patterns like:
    - LEC on Wednesday PM
    - Intern continuity on Wednesday AM
    - Kapiolani rotation patterns
    - Mid-block transitions

    Args:
        block_number: Block number (0-13)
        academic_year: Academic year (e.g., 2025 for AY 2025-2026)
        start_date: Start date for date range query
        end_date: End date for date range query
        person_type: Optional filter ('resident' or 'faculty')

    Returns:
        HalfDayAssignmentListResponse with assignments
    """
    service = HalfDayScheduleService(db)

    # Determine date range
    if block_number is not None and academic_year is not None:
        try:
            block_dates = get_block_dates(block_number, academic_year)
            start_date = block_dates.start_date
            end_date = block_dates.end_date
        except (ValueError, KeyError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid block_number or academic_year: {e}",
            )
    elif start_date is None or end_date is None:
        raise HTTPException(
            status_code=400,
            detail="Either (block_number + academic_year) or (start_date + end_date) required",
        )

    # Fetch assignments
    assignments = await service.get_schedule_by_date_range(
        start_date=start_date,
        end_date=end_date,
        person_type=person_type,
    )

    # Convert to response schema
    assignment_reads = []
    for a in assignments:
        assignment_reads.append(
            HalfDayAssignmentRead(
                id=a.id,
                person_id=a.person_id,
                person_name=a.person.name if a.person else None,
                person_type=a.person.type if a.person else None,
                pgy_level=a.person.pgy_level if a.person else None,
                date=a.date,
                time_of_day=a.time_of_day,
                activity_id=a.activity_id,
                activity_code=a.activity.code if a.activity else None,
                activity_name=a.activity.name if a.activity else None,
                display_abbreviation=a.activity.display_abbreviation
                if a.activity
                else None,
                source=a.source,
                is_locked=a.is_locked,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )

    return HalfDayAssignmentListResponse(
        assignments=assignment_reads,
        total=len(assignment_reads),
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
    )
