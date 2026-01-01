"""People API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.credential_controller import CredentialController
from app.controllers.person_controller import PersonController
from app.core.security import get_current_active_user
from app.db.session import get_async_db, get_db
from app.models.user import User
from app.schemas.person import (
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
)
from app.schemas.procedure import ProcedureListResponse
from app.schemas.procedure_credential import (
    CredentialListResponse,
    FacultyCredentialSummary,
)
from app.services.credential_service import CredentialService

router = APIRouter()


@router.get("", response_model=PersonListResponse)
async def list_people(
    type: str | None = Query(
        None, description="Filter by type: 'resident' or 'faculty'"
    ),
    pgy_level: int | None = Query(None, description="Filter residents by PGY level"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all people, optionally filtered by type or PGY level. Requires authentication."""
    controller = PersonController(db)
    return controller.list_people(type=type, pgy_level=pgy_level)


@router.get("/residents", response_model=PersonListResponse)
async def list_residents(
    pgy_level: int | None = Query(None, description="Filter by PGY level (1, 2, or 3)"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all residents, optionally filtered by PGY level. Requires authentication."""
    controller = PersonController(db)
    return controller.list_residents(pgy_level=pgy_level)


@router.get("/faculty", response_model=PersonListResponse)
async def list_faculty(
    specialty: str | None = Query(None, description="Filter by specialty"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all faculty, optionally filtered by specialty. Requires authentication."""
    controller = PersonController(db)
    return controller.list_faculty(specialty=specialty)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a person by ID. Requires authentication."""
    controller = PersonController(db)
    return controller.get_person(person_id)


@router.post("", response_model=PersonResponse, status_code=201)
async def create_person(
    person_in: PersonCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new person (resident or faculty). Requires authentication."""
    controller = PersonController(db)
    return controller.create_person(person_in)


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    person_in: PersonUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing person. Requires authentication."""
    controller = PersonController(db)
    return controller.update_person(person_id, person_in)


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a person. Requires authentication."""
    controller = PersonController(db)
    controller.delete_person(person_id)


# ============================================================================
# Credential-related endpoints for faculty
# ============================================================================


@router.get("/{person_id}/credentials", response_model=CredentialListResponse)
async def get_person_credentials(
    person_id: UUID,
    status: str | None = Query(None, description="Filter by status"),
    include_expired: bool = Query(False, description="Include expired credentials"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all credentials for a faculty member. Requires authentication."""
    controller = CredentialController(db)
    return controller.list_credentials_for_person(
        person_id=person_id,
        status_filter=status,
        include_expired=include_expired,
    )


@router.get("/{person_id}/credentials/summary", response_model=FacultyCredentialSummary)
async def get_person_credential_summary(
    person_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a summary of a faculty member's credentials. Requires authentication."""
    controller = CredentialController(db)
    return controller.get_faculty_summary(person_id)


@router.get("/{person_id}/procedures", response_model=ProcedureListResponse)
async def get_person_procedures(
    person_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all procedures a faculty member is qualified to supervise. Requires authentication."""
    service = CredentialService(db)
    result = service.list_procedures_for_faculty(person_id)
    return ProcedureListResponse(items=result["items"], total=result["total"])
