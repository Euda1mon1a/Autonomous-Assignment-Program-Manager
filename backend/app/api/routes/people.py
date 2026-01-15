"""People API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.controllers.credential_controller import CredentialController
from app.controllers.person_controller import PersonController
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.person import (
    BatchPersonCreateRequest,
    BatchPersonDeleteRequest,
    BatchPersonResponse,
    BatchPersonUpdateRequest,
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
    response: Response,
    type: str | None = Query(
        None, description="Filter by type: 'resident' or 'faculty'"
    ),
    pgy_level: int | None = Query(None, description="Filter residents by PGY level"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all people (residents and faculty) with optional filters.

    Args:
        response: FastAPI Response object for adding headers.
        type: Filter by person type ('resident' or 'faculty').
        pgy_level: Filter residents by PGY level (1, 2, or 3).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of people and total count.

    Security:
        Requires authentication.

    PHI Warning:
        This endpoint returns Protected Health Information (PHI) including
        person names and email addresses. X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)
    return controller.list_people(type=type, pgy_level=pgy_level)


@router.get("/residents", response_model=PersonListResponse)
async def list_residents(
    response: Response,
    pgy_level: int | None = Query(None, description="Filter by PGY level (1, 2, or 3)"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all residents with optional PGY level filter.

    Args:
        response: FastAPI Response object for adding headers.
        pgy_level: Filter by PGY level (1, 2, or 3).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of residents and total count.

    Security:
        Requires authentication.

    PHI Warning:
        This endpoint returns Protected Health Information (PHI) including
        resident names and email addresses. X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)
    return controller.list_residents(pgy_level=pgy_level)


@router.get("/faculty", response_model=PersonListResponse)
async def list_faculty(
    response: Response,
    specialty: str | None = Query(None, description="Filter by specialty"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all faculty with optional specialty filter.

    Args:
        response: FastAPI Response object for adding headers.
        specialty: Filter by medical specialty (e.g., 'Family Medicine', 'Pediatrics').
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonListResponse with list of faculty and total count.

    Security:
        Requires authentication.

    PHI Warning:
        This endpoint returns Protected Health Information (PHI) including
        faculty names and email addresses. X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)
    return controller.list_faculty(specialty=specialty)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a person (resident or faculty) by ID.

    Args:
        person_id: UUID of the person to retrieve.
        response: FastAPI Response object for adding headers.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        PersonResponse with full person details.

    Security:
        Requires authentication.

    PHI Warning:
        This endpoint returns Protected Health Information (PHI) including
        person name and email address. X-Contains-PHI header is set.

    Raises:
        HTTPException: 404 if person not found.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)
    return controller.get_person(person_id)


@router.post("", response_model=PersonResponse, status_code=201)
async def create_person(
    person_in: PersonCreate,
    db=Depends(get_db),
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
    db=Depends(get_db),
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


# ============================================================================
# Batch operations for people
# ============================================================================


@router.post("/batch", response_model=BatchPersonResponse, status_code=201)
async def batch_create_people(
    request: BatchPersonCreateRequest,
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch create multiple people atomically.

    Features:
    - Create up to 100 people at once
    - Dry-run mode for validation without creating
    - Atomic operation (all or nothing)
    - Duplicate email detection within batch and database
    - Validates resident PGY level requirements

    Args:
        request: BatchPersonCreateRequest with list of people to create
        response: FastAPI Response object for adding headers
        db: Database session
        current_user: Authenticated user

    Returns:
        BatchPersonResponse with operation results

    Security:
        Requires authentication

    PHI Warning:
        This endpoint creates Protected Health Information (PHI).
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)

    # Convert Pydantic models to dicts
    people_data = [person.model_dump() for person in request.people]

    return controller.batch_create_people(people_data, request.dry_run)


@router.put("/batch", response_model=BatchPersonResponse)
async def batch_update_people(
    request: BatchPersonUpdateRequest,
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch update multiple people atomically.

    Features:
    - Update up to 100 people at once
    - Dry-run mode for validation without updating
    - Atomic operation (all or nothing)
    - Per-person update tracking

    Args:
        request: BatchPersonUpdateRequest with list of person updates
        response: FastAPI Response object for adding headers
        db: Database session
        current_user: Authenticated user

    Returns:
        BatchPersonResponse with operation results

    Security:
        Requires authentication

    PHI Warning:
        This endpoint updates Protected Health Information (PHI).
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)

    # Convert Pydantic models to dicts
    updates = [
        {
            "person_id": item.person_id,
            "updates": item.updates.model_dump(exclude_unset=True),
        }
        for item in request.people
    ]

    return controller.batch_update_people(updates, request.dry_run)


@router.post("/batch/delete", response_model=BatchPersonResponse)
async def batch_delete_people(
    request: BatchPersonDeleteRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch delete multiple people atomically.

    Features:
    - Delete up to 100 people at once
    - Dry-run mode for validation without deleting
    - Atomic operation (all or nothing)
    - Validates all people exist before deletion

    Args:
        request: BatchPersonDeleteRequest with list of person IDs to delete
        db: Database session
        current_user: Authenticated user

    Returns:
        BatchPersonResponse with operation results

    Security:
        Requires authentication
    """
    controller = PersonController(db)
    return controller.batch_delete_people(request.person_ids, request.dry_run)
