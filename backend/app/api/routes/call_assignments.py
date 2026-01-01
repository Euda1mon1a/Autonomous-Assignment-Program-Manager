"""Call assignment API routes for overnight and weekend call management.

Endpoints for managing faculty call assignments:
- List, create, update, delete call assignments
- Bulk operations for solver-generated assignments
- Coverage and equity reports

Authorization:
- Read operations: All authenticated users
- Write operations: ADMIN, COORDINATOR, or FACULTY roles
- Reports: ADMIN or COORDINATOR roles
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.permissions.decorators import require_role
from app.controllers.call_assignment_controller import CallAssignmentController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.call_assignment import (
    BulkCallAssignmentCreate,
    BulkCallAssignmentResponse,
    CallAssignmentCreate,
    CallAssignmentListResponse,
    CallAssignmentResponse,
    CallAssignmentUpdate,
    CallCoverageReport,
    CallEquityReport,
)

router = APIRouter(prefix="/call-assignments", tags=["call-assignments"])


@router.get(
    "",
    response_model=CallAssignmentListResponse,
    summary="List call assignments",
    description="List call assignments with optional filters for date range, person, and type.",
)
async def list_call_assignments(
    start_date: date | None = Query(
        None, description="Filter by start date (inclusive)"
    ),
    end_date: date | None = Query(None, description="Filter by end date (inclusive)"),
    person_id: UUID | None = Query(None, description="Filter by person ID"),
    call_type: str | None = Query(None, description="Filter by call type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentListResponse:
    """List call assignments with optional filters."""
    controller = CallAssignmentController(db)
    return await controller.list_call_assignments(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        call_type=call_type,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{call_id}",
    response_model=CallAssignmentResponse,
    summary="Get call assignment",
    description="Get a single call assignment by ID.",
)
async def get_call_assignment(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentResponse:
    """Get a single call assignment by ID."""
    controller = CallAssignmentController(db)
    return await controller.get_call_assignment(call_id)


@router.post(
    "",
    response_model=CallAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create call assignment",
    description="Create a new call assignment. Requires ADMIN, COORDINATOR, or FACULTY role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR", "FACULTY"]))],
)
async def create_call_assignment(
    assignment_in: CallAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentResponse:
    """Create a new call assignment."""
    controller = CallAssignmentController(db)
    return await controller.create_call_assignment(assignment_in)


@router.put(
    "/{call_id}",
    response_model=CallAssignmentResponse,
    summary="Update call assignment",
    description="Update an existing call assignment. Requires ADMIN, COORDINATOR, or FACULTY role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR", "FACULTY"]))],
)
async def update_call_assignment(
    call_id: UUID,
    assignment_in: CallAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentResponse:
    """Update a call assignment."""
    controller = CallAssignmentController(db)
    return await controller.update_call_assignment(call_id, assignment_in)


@router.delete(
    "/{call_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete call assignment",
    description="Delete a call assignment. Requires ADMIN, COORDINATOR, or FACULTY role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR", "FACULTY"]))],
)
async def delete_call_assignment(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a call assignment."""
    controller = CallAssignmentController(db)
    await controller.delete_call_assignment(call_id)


@router.post(
    "/bulk",
    response_model=BulkCallAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create call assignments",
    description="Bulk create multiple call assignments. Used by solver for schedule generation. Requires ADMIN or COORDINATOR role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR"]))],
)
async def bulk_create_call_assignments(
    bulk_data: BulkCallAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BulkCallAssignmentResponse:
    """Bulk create multiple call assignments."""
    controller = CallAssignmentController(db)
    return await controller.bulk_create_call_assignments(bulk_data)


@router.get(
    "/by-person/{person_id}",
    response_model=CallAssignmentListResponse,
    summary="Get call assignments by person",
    description="Get all call assignments for a specific person.",
)
async def get_call_assignments_by_person(
    person_id: UUID,
    start_date: date | None = Query(None, description="Filter by start date"),
    end_date: date | None = Query(None, description="Filter by end date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentListResponse:
    """Get all call assignments for a specific person."""
    controller = CallAssignmentController(db)
    return await controller.get_call_assignments_by_person(
        person_id=person_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/by-date/{on_date}",
    response_model=CallAssignmentListResponse,
    summary="Get call assignments by date",
    description="Get all call assignments for a specific date.",
)
async def get_call_assignments_by_date(
    on_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallAssignmentListResponse:
    """Get all call assignments for a specific date."""
    controller = CallAssignmentController(db)
    return await controller.get_call_assignments_by_date(on_date)


@router.get(
    "/reports/coverage",
    response_model=CallCoverageReport,
    summary="Get call coverage report",
    description="Get a report showing call coverage gaps. Requires ADMIN or COORDINATOR role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR"]))],
)
async def get_coverage_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallCoverageReport:
    """Get call coverage report for a date range."""
    controller = CallAssignmentController(db)
    return await controller.get_coverage_report(start_date, end_date)


@router.get(
    "/reports/equity",
    response_model=CallEquityReport,
    summary="Get call equity report",
    description="Get a report showing call distribution across faculty. Requires ADMIN or COORDINATOR role.",
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR"]))],
)
async def get_equity_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CallEquityReport:
    """Get call equity/distribution report for a date range."""
    controller = CallAssignmentController(db)
    return await controller.get_equity_report(start_date, end_date)
