"""Assignment API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.assignment_controller import AssignmentController
from app.core.security import get_current_active_user, get_scheduler_user
from app.db.session import get_async_db, get_db
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
    AssignmentWithWarnings,
)

router = APIRouter()


@router.get("", response_model=AssignmentListResponse)
async def list_assignments(
    start_date: date | None = Query(None, description="Filter from this date"),
    end_date: date | None = Query(None, description="Filter until this date"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    role: str | None = Query(None, description="Filter by role"),
    activity_type: str | None = Query(
        None, description="Filter by activity type (e.g., on_call, clinic, inpatient)"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page (max 500)"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List assignments with optional filters and pagination. Requires authentication."""
    controller = AssignmentController(db)
    return controller.list_assignments(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        role=role,
        activity_type=activity_type,
        page=page,
        page_size=page_size,
    )


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an assignment by ID. Requires authentication."""
    controller = AssignmentController(db)
    return controller.get_assignment(assignment_id)


@router.post("", response_model=AssignmentWithWarnings, status_code=201)
async def create_assignment(
    assignment_in: AssignmentCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Create a new assignment. Requires scheduler role (admin or coordinator).

    Validates ACGME compliance and returns warnings if violations exist.
    Violations do not block creation but should be acknowledged with override_reason.
    """
    controller = AssignmentController(db)
    return await controller.create_assignment(assignment_in, current_user)


@router.put("/{assignment_id}", response_model=AssignmentWithWarnings)
async def update_assignment(
    assignment_id: UUID,
    assignment_in: AssignmentUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Update an existing assignment with optimistic locking.
    Requires scheduler role (admin or coordinator).

    Validates ACGME compliance and returns warnings if violations exist.
    Violations do not block update but should be acknowledged with override_reason.
    """
    controller = AssignmentController(db)
    return await controller.update_assignment(assignment_id, assignment_in)


@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """Delete an assignment. Requires scheduler role (admin or coordinator)."""
    controller = AssignmentController(db)
    await controller.delete_assignment(assignment_id)


@router.delete("", status_code=204)
async def delete_assignments_bulk(
    start_date: date = Query(..., description="Delete assignments from this date"),
    end_date: date = Query(..., description="Delete assignments until this date"),
    db=Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """Delete all assignments in a date range. Requires scheduler role (admin or coordinator)."""
    controller = AssignmentController(db)
    return controller.delete_assignments_bulk(start_date, end_date)
