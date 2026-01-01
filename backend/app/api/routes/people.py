"""People API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.credential_controller import CredentialController
from app.controllers.person_controller import PersonController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
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
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all people (residents and faculty) with optional filters.

    Args:
        type: Filter by person type ('resident' or 'faculty').
        pgy_level: Filter residents by PGY level (1, 2, or 3).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of people and total count.

    Security:
        Requires authentication.
    """
    controller = PersonController(db)
    return controller.list_people(type=type, pgy_level=pgy_level)


@router.get("/residents", response_model=PersonListResponse)
async def list_residents(
    pgy_level: int | None = Query(None, description="Filter by PGY level (1, 2, or 3)"),
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all residents with optional PGY level filter.

    Args:
        pgy_level: Filter by PGY level (1, 2, or 3).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of residents and total count.

    Security:
        Requires authentication.
    """
    controller = PersonController(db)
    return controller.list_residents(pgy_level=pgy_level)


@router.get("/faculty", response_model=PersonListResponse)
async def list_faculty(
    specialty: str | None = Query(None, description="Filter by specialty"),
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all faculty with optional specialty filter.

    Args:
        specialty: Filter by medical specialty (e.g., 'Family Medicine', 'Pediatrics').
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of faculty and total count.

    Security:
        Requires authentication.
    """
    controller = PersonController(db)
    return controller.list_faculty(specialty=specialty)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a person (resident or faculty) by ID.

    Args:
        person_id: UUID of the person to retrieve.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonResponse with full person details.

    Security:
        Requires authentication.

    Raises:
        HTTPException: 404 if person not found.
    """
    controller = PersonController(db)
    return controller.get_person(person_id)


@router.post("", response_model=PersonResponse, status_code=201)
async def create_person(
    person_in: PersonCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new person (resident or faculty).

    Args:
        person_in: Person creation payload (name, type, email, pgy_level, etc.).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonResponse with created person details.

    Security:
        Requires authentication.

    Note:
        - Residents require pgy_level field
        - Faculty can specify specialties and procedure credentials

    Status Codes:
        - 201: Person created successfully
        - 400: Validation error (e.g., resident without PGY level)
    """
    controller = PersonController(db)
    return controller.create_person(person_in)


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    person_in: PersonUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing person's information.

    Args:
        person_id: UUID of the person to update.
        person_in: Person update payload with fields to modify.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonResponse with updated person details.

    Security:
        Requires authentication.

    Raises:
        HTTPException: 404 if person not found.
    """
    controller = PersonController(db)
    return controller.update_person(person_id, person_in)


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a person (resident or faculty).

    Args:
        person_id: UUID of the person to delete.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        No content (204).

    Security:
        Requires authentication.

    Warning:
        Deleting a person will cascade delete:
        - All their schedule assignments
        - Their credentials (for faculty)
        - Their absence records
        - Their swap requests
        This operation cannot be undone.

    Note:
        Consider deactivating the person instead of deletion to preserve historical data.

    Raises:
        HTTPException:
            - 404: Person not found
            - 409: Cannot delete person with active assignments (if cascade disabled)

    Status Codes:
        - 204: Person deleted successfully
        - 404: Person not found
        - 409: Conflict (active assignments exist)
    """
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
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all procedure credentials for a faculty member.

    Args:
        person_id: UUID of the faculty member.
        status: Filter by credential status ('active', 'expiring_soon', 'expired').
        include_expired: If True, include expired credentials in results.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        CredentialListResponse with list of credentials and total count.

    Security:
        Requires authentication.

    Note:
        Credentials determine which procedures a faculty member can supervise.
        Expired credentials prevent assignment to procedure-based rotations.

    Example Query:
        GET /api/people/{person_id}/credentials?status=expiring_soon&include_expired=false

    Status Codes:
        - 200: Credentials retrieved successfully
        - 404: Person not found
    """
    controller = CredentialController(db)
    return controller.list_credentials_for_person(
        person_id=person_id,
        status_filter=status,
        include_expired=include_expired,
    )


@router.get("/{person_id}/credentials/summary", response_model=FacultyCredentialSummary)
async def get_person_credential_summary(
    person_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a comprehensive summary of a faculty member's credential status.

    Args:
        person_id: UUID of the faculty member.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        FacultyCredentialSummary with:
        - Total credential count
        - Active credentials count
        - Expiring soon credentials (within 30 days)
        - Expired credentials count
        - List of procedures they can supervise

    Security:
        Requires authentication.

    Note:
        Use this endpoint for dashboard views showing faculty readiness status.
        Useful for identifying faculty who need credential renewals.

    Status Codes:
        - 200: Summary retrieved successfully
        - 404: Person not found or person is not faculty
    """
    controller = CredentialController(db)
    return controller.get_faculty_summary(person_id)


@router.get("/{person_id}/procedures", response_model=ProcedureListResponse)
async def get_person_procedures(
    person_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all procedures a faculty member is qualified to supervise.

    Args:
        person_id: UUID of the faculty member.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        ProcedureListResponse with list of procedures and total count.

    Security:
        Requires authentication.

    Note:
        Only returns procedures for which the faculty member has:
        - Active (non-expired) credentials
        - Valid certification status

        This list determines which procedure-based rotations the faculty
        member can be assigned to supervise.

    Example Use Cases:
        - Validating faculty eligibility for procedure assignments
        - Displaying supervision capabilities on faculty profiles
        - Filtering available faculty for specific procedure types

    Status Codes:
        - 200: Procedures retrieved successfully
        - 404: Person not found or person is not faculty
    """
    service = CredentialService(db)
    result = service.list_procedures_for_faculty(person_id)
    return ProcedureListResponse(items=result["items"], total=result["total"])
