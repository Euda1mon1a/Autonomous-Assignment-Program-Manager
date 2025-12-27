"""API routes for call assignments."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.call_assignment import (
    BulkCallAssignmentCreate,
    CallAssignmentCreate,
    CallAssignmentResponse,
    CallCoverageReport,
    CallEquityReport,
)
from app.services.call_assignment_service import CallAssignmentService

router = APIRouter(prefix="/call-assignments", tags=["call-assignments"])


@router.get("/", response_model=list[CallAssignmentResponse])
async def list_call_assignments(
    start_date: date | None = Query(None, description="Filter by start date"),
    end_date: date | None = Query(None, description="Filter by end date"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    call_type: str | None = Query(None, description="Filter by call type"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
) -> list[CallAssignmentResponse]:
    """
    List call assignments with optional filters.

    - **start_date**: Filter by start date (inclusive)
    - **end_date**: Filter by end date (inclusive)
    - **person_id**: Filter by specific person
    - **call_type**: Filter by call type (overnight, weekend, backup)
    """
    service = CallAssignmentService(db)
    assignments = service.list_call_assignments(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        call_type=call_type,
    )

    return [
        CallAssignmentResponse(
            id=a.id,
            date=a.date,
            person_id=a.person_id,
            call_type=a.call_type,
            is_weekend=a.is_weekend,
            is_holiday=a.is_holiday,
            created_at=a.created_at,
            person_name=a.person.name if a.person else None,
            day_of_week=a.date.strftime("%A"),
        )
        for a in assignments
    ]


@router.get("/{assignment_id}", response_model=CallAssignmentResponse)
async def get_call_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
) -> CallAssignmentResponse:
    """Get a specific call assignment by ID."""
    service = CallAssignmentService(db)
    assignment = service.get_call_assignment(assignment_id)

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call assignment not found",
        )

    return CallAssignmentResponse(
        id=assignment.id,
        date=assignment.date,
        person_id=assignment.person_id,
        call_type=assignment.call_type,
        is_weekend=assignment.is_weekend,
        is_holiday=assignment.is_holiday,
        created_at=assignment.created_at,
        person_name=assignment.person.name if assignment.person else None,
        day_of_week=assignment.date.strftime("%A"),
    )


@router.post(
    "/", response_model=CallAssignmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_call_assignment(
    data: CallAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentResponse:
    """
    Create a new call assignment.

    This is used for manual assignment (e.g., adding adjunct faculty to call).
    Solver-generated assignments use the bulk endpoint.
    """
    service = CallAssignmentService(db)

    try:
        assignment = service.create_call_assignment(data)
        db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Reload to get person relationship
    db.refresh(assignment)

    return CallAssignmentResponse(
        id=assignment.id,
        date=assignment.date,
        person_id=assignment.person_id,
        call_type=assignment.call_type,
        is_weekend=assignment.is_weekend,
        is_holiday=assignment.is_holiday,
        created_at=assignment.created_at,
        person_name=assignment.person.name if assignment.person else None,
        day_of_week=assignment.date.strftime("%A"),
    )


@router.post("/bulk", response_model=dict)
async def bulk_create_call_assignments(
    data: BulkCallAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Bulk create call assignments from solver output.

    This endpoint is used after schedule generation to persist
    the solver's call assignment decisions.

    - **assignments**: List of call assignments to create
    - **replace_existing**: If true, delete existing assignments in date range first
    """
    service = CallAssignmentService(db)

    assignments = service.bulk_create_call_assignments(
        assignments=data.assignments,
        replace_existing=data.replace_existing,
    )
    db.commit()

    return {
        "created": len(assignments),
        "schedule_run_id": str(data.schedule_run_id) if data.schedule_run_id else None,
    }


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a call assignment."""
    service = CallAssignmentService(db)

    if not service.delete_call_assignment(assignment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call assignment not found",
        )

    db.commit()


@router.get("/reports/coverage", response_model=CallCoverageReport)
async def get_coverage_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
) -> CallCoverageReport:
    """
    Get call coverage report for a date range.

    Shows coverage percentage and identifies gaps in overnight call coverage.
    Only checks Sun-Thurs nights (Fri-Sat handled by FMIT).
    """
    service = CallAssignmentService(db)
    return service.get_coverage_report(start_date, end_date)


@router.get("/reports/equity", response_model=CallEquityReport)
async def get_equity_report(
    year: int = Query(..., description="Year for report"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
) -> CallEquityReport:
    """
    Get call equity report for a year.

    Shows call distribution across faculty with statistics.
    Includes:
    - Per-faculty call counts (Sunday vs weekday)
    - Statistics (min, max, mean, stddev)
    - Equity score (0-1, higher is better)
    """
    service = CallAssignmentService(db)
    return service.get_equity_report(year)
