"""Absence API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.absence_controller import AbsenceController
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.absence import AbsenceCreate, AbsenceResponse, AbsenceUpdate

router = APIRouter()


@router.get("")
def list_absences(
    start_date: date | None = Query(None, description="Filter absences starting from"),
    end_date: date | None = Query(None, description="Filter absences ending by"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    absence_type: str | None = Query(None, description="Filter by absence type"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List absences with optional filters. Requires authentication."""
    controller = AbsenceController(db)
    return controller.list_absences(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        absence_type=absence_type,
    )


@router.get("/{absence_id}", response_model=AbsenceResponse)
def get_absence(
    absence_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an absence by ID. Requires authentication."""
    controller = AbsenceController(db)
    return controller.get_absence(absence_id)


@router.post("", response_model=AbsenceResponse, status_code=201)
def create_absence(
    absence_in: AbsenceCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.create_absence(absence_in)


@router.put("/{absence_id}", response_model=AbsenceResponse)
def update_absence(
    absence_id: UUID,
    absence_in: AbsenceUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.update_absence(absence_id, absence_in)


@router.delete("/{absence_id}", status_code=204)
def delete_absence(
    absence_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an absence. Requires authentication."""
    controller = AbsenceController(db)
    controller.delete_absence(absence_id)
