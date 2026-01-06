"""Credentials API routes.

Provides endpoints for managing faculty procedure credentials.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.credential_controller import CredentialController
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.procedure_credential import (
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
    CredentialUpdate,
    FacultyCredentialSummary,
    QualifiedFacultyResponse,
)

router = APIRouter()


@router.get("/expiring", response_model=CredentialListResponse)
async def list_expiring_credentials(
    days: int = Query(30, description="Number of days to look ahead"),
    db=Depends(get_db),
):
    """List credentials expiring within the specified number of days."""
    controller = CredentialController(db)
    return controller.list_expiring_credentials(days=days)


@router.get("/by-person/{person_id}", response_model=CredentialListResponse)
async def list_credentials_for_person(
    person_id: UUID,
    status: str | None = Query(None, description="Filter by status"),
    include_expired: bool = Query(False, description="Include expired credentials"),
    db=Depends(get_db),
):
    """List all credentials for a specific person (faculty)."""
    controller = CredentialController(db)
    return controller.list_credentials_for_person(
        person_id=person_id,
        status_filter=status,
        include_expired=include_expired,
    )


@router.get("/by-procedure/{procedure_id}", response_model=CredentialListResponse)
async def list_credentials_for_procedure(
    procedure_id: UUID,
    status: str | None = Query(None, description="Filter by status"),
    include_expired: bool = Query(False, description="Include expired credentials"),
    db=Depends(get_db),
):
    """List all credentials for a specific procedure (who can supervise it)."""
    controller = CredentialController(db)
    return controller.list_credentials_for_procedure(
        procedure_id=procedure_id,
        status_filter=status,
        include_expired=include_expired,
    )


@router.get(
    "/qualified-faculty/{procedure_id}", response_model=QualifiedFacultyResponse
)
async def get_qualified_faculty(
    procedure_id: UUID,
    db=Depends(get_db),
):
    """Get all faculty members qualified to supervise a specific procedure."""
    controller = CredentialController(db)
    return controller.get_qualified_faculty(procedure_id)


@router.get("/check/{person_id}/{procedure_id}")
async def check_qualification(
    person_id: UUID,
    procedure_id: UUID,
    db=Depends(get_db),
):
    """Check if a faculty member is qualified to supervise a specific procedure."""
    controller = CredentialController(db)
    return controller.check_qualification(person_id, procedure_id)


@router.get("/summary/{person_id}", response_model=FacultyCredentialSummary)
async def get_faculty_credential_summary(
    person_id: UUID,
    db=Depends(get_db),
):
    """Get a summary of a faculty member's credentials."""
    controller = CredentialController(db)
    return controller.get_faculty_summary(person_id)


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: UUID,
    db=Depends(get_db),
):
    """Get a credential by ID."""
    controller = CredentialController(db)
    return controller.get_credential(credential_id)


@router.post("", response_model=CredentialResponse, status_code=201)
async def create_credential(
    credential_in: CredentialCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new credential for a faculty member. Requires authentication."""
    controller = CredentialController(db)
    return controller.create_credential(credential_in)


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: UUID,
    credential_in: CredentialUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing credential. Requires authentication."""
    controller = CredentialController(db)
    return controller.update_credential(credential_id, credential_in)


@router.delete("/{credential_id}", status_code=204)
async def delete_credential(
    credential_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a credential. Requires authentication."""
    controller = CredentialController(db)
    await controller.delete_credential(credential_id)


@router.post("/{credential_id}/suspend", response_model=CredentialResponse)
async def suspend_credential(
    credential_id: UUID,
    notes: str | None = Query(None, description="Suspension notes"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Suspend a credential. Requires authentication."""
    controller = CredentialController(db)
    return controller.suspend_credential(credential_id, notes)


@router.post("/{credential_id}/activate", response_model=CredentialResponse)
async def activate_credential(
    credential_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Activate a credential. Requires authentication."""
    controller = CredentialController(db)
    return controller.activate_credential(credential_id)


@router.post("/{credential_id}/verify", response_model=CredentialResponse)
async def verify_credential(
    credential_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a credential as verified today. Requires authentication."""
    controller = CredentialController(db)
    return controller.verify_credential(credential_id)
