"""Assignment API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.controllers.assignment_controller import AssignmentController
from app.core.security import get_current_active_user, get_scheduler_user
from app.db.session import get_db
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
    response: Response,
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
    """List schedule assignments with filters and pagination.

    Args:
        response: FastAPI Response object for adding headers.
        start_date: Filter assignments starting on or after this date.
        end_date: Filter assignments ending on or before this date.
        person_id: Filter assignments for a specific person.
        role: Filter by assignment role.
        activity_type: Filter by activity type (e.g., 'on_call', 'clinic', 'inpatient').
        page: Page number (1-indexed).
        page_size: Number of items per page (max 500).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        AssignmentListResponse with items, total count, and pagination metadata.

    Security:
        Requires authentication.

    PHI/OPSEC Warning:
        This endpoint returns schedule patterns that link person_id to duty assignments,
        revealing operational patterns (OPSEC-sensitive for military medical personnel).
        Notes and override_reason fields may contain PHI. X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "person_id,notes,override_reason"

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
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a schedule assignment by ID.

    Args:
        assignment_id: UUID of the assignment to retrieve.
        response: FastAPI Response object for adding headers.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        AssignmentResponse with full assignment details including person and block info.

    Security:
        Requires authentication.

    PHI/OPSEC Warning:
        This endpoint returns schedule patterns that link person_id to duty assignments,
        revealing operational patterns (OPSEC-sensitive for military medical personnel).
        Notes and override_reason fields may contain PHI. X-Contains-PHI header is set.

    Raises:
        HTTPException: 404 if assignment not found.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "person_id,notes,override_reason"

    controller = AssignmentController(db)
    return controller.get_assignment(assignment_id)


@router.post("", response_model=AssignmentWithWarnings, status_code=201)
async def create_assignment(
    assignment_in: AssignmentCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """Create a new schedule assignment with ACGME validation.

    Args:
        assignment_in: Assignment creation payload (block, person, role, etc.).
        db: Database session.
        current_user: Authenticated user (must have scheduler role).

    Returns:
        AssignmentWithWarnings containing the created assignment and any ACGME warnings.

    Security:
        Requires scheduler role (admin or coordinator).

    Note:
        ACGME compliance violations generate warnings but do not block creation.
        Use override_reason field to acknowledge and document violations.

    Status Codes:
        - 201: Assignment created successfully
        - 403: Insufficient permissions
        - 409: Conflict (person already assigned to block)
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
    """Update an existing assignment with optimistic locking and ACGME validation.

    Args:
        assignment_id: UUID of the assignment to update.
        assignment_in: Assignment update payload with updated_at for optimistic locking.
        db: Database session.
        current_user: Authenticated user (must have scheduler role).

    Returns:
        AssignmentWithWarnings containing the updated assignment and any ACGME warnings.

    Security:
        Requires scheduler role (admin or coordinator).

    Note:
        Uses optimistic locking via updated_at field to prevent concurrent modifications.
        ACGME violations generate warnings but do not block updates.

    Raises:
        HTTPException:
            - 404: Assignment not found
            - 409: Optimistic locking conflict (assignment modified by another user)
            - 403: Insufficient permissions
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
    await controller.delete_assignments_bulk(start_date, end_date)
