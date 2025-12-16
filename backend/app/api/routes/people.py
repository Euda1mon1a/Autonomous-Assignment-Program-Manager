"""People API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.models.user import User
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse, PersonListResponse
from app.core.security import get_current_active_user
from app.controllers.person_controller import PersonController

router = APIRouter()


@router.get("", response_model=PersonListResponse)
def list_people(
    type: Optional[str] = Query(None, description="Filter by type: 'resident' or 'faculty'"),
    pgy_level: Optional[int] = Query(None, description="Filter residents by PGY level"),
    db=Depends(get_db),
):
    """List all people, optionally filtered by type or PGY level."""
    controller = PersonController(db)
    return controller.list_people(type=type, pgy_level=pgy_level)


@router.get("/residents", response_model=PersonListResponse)
def list_residents(
    pgy_level: Optional[int] = Query(None, description="Filter by PGY level (1, 2, or 3)"),
    db=Depends(get_db),
):
    """List all residents, optionally filtered by PGY level."""
    controller = PersonController(db)
    return controller.list_residents(pgy_level=pgy_level)


@router.get("/faculty", response_model=PersonListResponse)
def list_faculty(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db=Depends(get_db),
):
    """List all faculty, optionally filtered by specialty."""
    controller = PersonController(db)
    return controller.list_faculty(specialty=specialty)


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(
    person_id: UUID,
    db=Depends(get_db),
):
    """Get a person by ID."""
    controller = PersonController(db)
    return controller.get_person(person_id)


@router.post("", response_model=PersonResponse, status_code=201)
def create_person(
    person_in: PersonCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new person (resident or faculty). Requires authentication."""
    controller = PersonController(db)
    return controller.create_person(person_in)


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: UUID,
    person_in: PersonUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing person. Requires authentication."""
    controller = PersonController(db)
    return controller.update_person(person_id, person_in)


@router.delete("/{person_id}", status_code=204)
def delete_person(
    person_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a person. Requires authentication."""
    controller = PersonController(db)
    controller.delete_person(person_id)
