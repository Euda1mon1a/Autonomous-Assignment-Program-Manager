"""Absence API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.absence_controller import AbsenceController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.absence import (
    AbsenceCreate,
    AbsenceListResponse,
    AbsenceResponse,
    AbsenceUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=AbsenceListResponse,
    summary="List absences",
    description="Retrieve a paginated list of absences with optional filters. "
    "Supports filtering by date range, person, and absence type. "
    "Useful for displaying absence calendars and generating reports.",
    tags=["absences"],
    responses={
        200: {"description": "Absences retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def list_absences(
    start_date: date | None = Query(None, description="Filter absences starting from"),
    end_date: date | None = Query(None, description="Filter absences ending by"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    absence_type: str | None = Query(None, description="Filter by absence type"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page (max 500)"),
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List absences with optional filters and pagination. Requires authentication."""
    controller = AbsenceController(db)
    return controller.list_absences(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        absence_type=absence_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{absence_id}",
    response_model=AbsenceResponse,
    summary="Get absence by ID",
    description="Retrieve detailed information about a specific absence record. "
    "Includes person details, absence type, date range, status, and any approval information.",
    tags=["absences"],
    responses={
        200: {"description": "Absence retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Absence not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_absence(
    absence_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an absence by ID. Requires authentication."""
    controller = AbsenceController(db)
    return controller.get_absence(absence_id)


@router.post(
    "",
    response_model=AbsenceResponse,
    status_code=201,
    summary="Create absence",
    description="Create a new absence record for a person. "
    "Validates date ranges and checks for conflicts with existing assignments. "
    "Can trigger automatic schedule conflict detection and notifications.",
    tags=["absences"],
    responses={
        201: {"description": "Absence created successfully"},
        400: {"description": "Invalid input data or date range conflict"},
        401: {"description": "Authentication required"},
        409: {"description": "Conflicts with existing schedule"},
        500: {"description": "Internal server error"},
    },
)
async def create_absence(
    absence_in: AbsenceCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.create_absence(absence_in)


@router.put(
    "/{absence_id}",
    response_model=AbsenceResponse,
    summary="Update absence",
    description="Update an existing absence record. "
    "Can modify date ranges, absence type, or approval status. "
    "Changes may trigger schedule conflict re-validation.",
    tags=["absences"],
    responses={
        200: {"description": "Absence updated successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        404: {"description": "Absence not found"},
        409: {"description": "Update would create schedule conflicts"},
        500: {"description": "Internal server error"},
    },
)
async def update_absence(
    absence_id: UUID,
    absence_in: AbsenceUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.update_absence(absence_id, absence_in)


@router.delete(
    "/{absence_id}",
    status_code=204,
    summary="Delete absence",
    description="Permanently delete an absence record. "
    "This operation cannot be undone. "
    "Deleting an absence may affect schedule conflict detection.",
    tags=["absences"],
    responses={
        204: {"description": "Absence deleted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Absence not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_absence(
    absence_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an absence. Requires authentication."""
    controller = AbsenceController(db)
    await controller.delete_absence(absence_id)
