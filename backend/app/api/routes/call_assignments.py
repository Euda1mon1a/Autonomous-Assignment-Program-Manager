"""Call assignment API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.call_assignment_controller import CallAssignmentController
from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.call_assignment import (
    CallAssignmentCreate,
    CallAssignmentListResponse,
    CallAssignmentResponse,
    CallAssignmentUpdate,
)

router = APIRouter()


@router.get("", response_model=CallAssignmentListResponse)
async def list_call_assignments(
    start_date: date | None = Query(None, description="Filter assignments from this date"),
    end_date: date | None = Query(None, description="Filter assignments up to this date"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    call_type: str | None = Query(
        None, description="Filter by call type (overnight, weekend, backup)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List call assignments with optional filters and pagination.

    Requires authentication.

    **Filters:**
    - start_date: Only assignments on or after this date
    - end_date: Only assignments on or before this date
    - person_id: Only assignments for this person
    - call_type: Only assignments of this type (overnight/weekend/backup)

    **Pagination:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 1000)
    """
    controller = CallAssignmentController(db)
    return await controller.list_call_assignments(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        call_type=call_type,
        skip=skip,
        limit=limit,
    )


@router.get("/{call_id}", response_model=CallAssignmentResponse)
async def get_call_assignment(
    call_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a single call assignment by ID.

    Requires authentication.
    """
    controller = CallAssignmentController(db)
    return await controller.get_call_assignment(call_id)


@router.post("", response_model=CallAssignmentResponse, status_code=201)
async def create_call_assignment(
    assignment_in: CallAssignmentCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new call assignment.

    Requires authentication.

    **Request Body:**
    ```json
    {
        "date": "2025-01-15",
        "person_id": "uuid-here",
        "call_type": "overnight",
        "is_weekend": false,
        "is_holiday": false
    }
    ```

    **Valid call_type values:**
    - overnight: Overnight call duty
    - weekend: Weekend call duty
    - backup: Backup call assignment
    """
    controller = CallAssignmentController(db)
    return await controller.create_call_assignment(assignment_in)


@router.put("/{call_id}", response_model=CallAssignmentResponse)
async def update_call_assignment(
    call_id: UUID,
    assignment_in: CallAssignmentUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an existing call assignment.

    Requires authentication.

    All fields are optional. Only provided fields will be updated.
    """
    controller = CallAssignmentController(db)
    return await controller.update_call_assignment(call_id, assignment_in)


@router.delete("/{call_id}", status_code=204)
async def delete_call_assignment(
    call_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a call assignment.

    Requires authentication.
    """
    controller = CallAssignmentController(db)
    await controller.delete_call_assignment(call_id)


@router.get("/person/{person_id}", response_model=CallAssignmentListResponse)
async def get_call_assignments_by_person(
    person_id: UUID,
    start_date: date | None = Query(None, description="Filter from this date"),
    end_date: date | None = Query(None, description="Filter up to this date"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all call assignments for a specific person.

    Requires authentication.

    Optionally filter by date range using start_date and end_date query parameters.
    """
    controller = CallAssignmentController(db)
    return await controller.get_call_assignments_by_person(
        person_id=person_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/date/{on_date}", response_model=CallAssignmentListResponse)
async def get_call_assignments_by_date(
    on_date: date,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all call assignments for a specific date.

    Requires authentication.

    Useful for daily coverage views and shift planning.
    """
    controller = CallAssignmentController(db)
    return await controller.get_call_assignments_by_date(on_date)
