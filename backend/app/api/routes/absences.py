"""Absence API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.controllers.absence_controller import AbsenceController
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.absence import (
    AbsenceCreate,
    AbsenceBulkApply,
    AbsenceBulkCreate,
    AbsenceBulkPreview,
    AbsenceListResponse,
    AbsenceResponse,
    AbsenceUpdate,
)

router = APIRouter()


@router.get("", response_model=AbsenceListResponse)
async def list_absences(
    response: Response,
    start_date: date | None = Query(None, description="Filter absences starting from"),
    end_date: date | None = Query(None, description="Filter absences ending by"),
    person_id: UUID | None = Query(None, description="Filter by person"),
    absence_type: str | None = Query(None, description="Filter by absence type"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page (max 500)"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List absences with optional filters and pagination.

    Security:
        Requires authentication.

    PHI/OPSEC Warning:
        This endpoint returns Protected Health Information (PHI) and OPSEC-sensitive
        data including absence types (medical), deployment orders, and TDY locations.
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = (
        "person_id,absence_type,deployment_orders,tdy_location,notes"
    )

    controller = AbsenceController(db)
    return controller.list_absences(
        start_date=start_date,
        end_date=end_date,
        person_id=person_id,
        absence_type=absence_type,
        page=page,
        page_size=page_size,
    )


@router.get("/{absence_id}", response_model=AbsenceResponse)
async def get_absence(
    absence_id: UUID,
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an absence by ID.

    Security:
        Requires authentication.

    PHI/OPSEC Warning:
        This endpoint returns Protected Health Information (PHI) and OPSEC-sensitive
        data including absence types (medical), deployment orders, and TDY locations.
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = (
        "person_id,absence_type,deployment_orders,tdy_location,notes"
    )

    controller = AbsenceController(db)
    return controller.get_absence(absence_id)


@router.post("", response_model=AbsenceResponse, status_code=201)
async def create_absence(
    absence_in: AbsenceCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.create_absence(absence_in)


@router.put("/{absence_id}", response_model=AbsenceResponse)
async def update_absence(
    absence_id: UUID,
    absence_in: AbsenceUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing absence. Requires authentication."""
    controller = AbsenceController(db)
    return controller.update_absence(absence_id, absence_in)


@router.delete("/{absence_id}", status_code=204)
async def delete_absence(
    absence_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an absence. Requires authentication."""
    controller = AbsenceController(db)
    await controller.delete_absence(absence_id)


# ============================================================================
# Bulk Import Endpoints
# ============================================================================


@router.post(
    "/bulk/preview",
    response_model=AbsenceBulkPreview,
    summary="Preview bulk absence import",
    description="Validate bulk absences and return preview with errors and summary.",
)
async def preview_bulk_absences(
    bulk_data: AbsenceBulkCreate,
    response: Response,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Preview bulk absence import before applying.

    Validates each absence in the list and returns:
    - valid: List of absences that passed validation
    - errors: List of validation errors with index, field, and message
    - summary: Counts by type, date range, unique persons

    Security:
        Requires authentication.

    PHI/OPSEC Warning:
        This endpoint processes Protected Health Information (PHI) and OPSEC-sensitive
        data including absence types (medical), deployment orders, and TDY locations.
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = (
        "person_id,absence_type,deployment_orders,tdy_location,notes"
    )

    controller = AbsenceController(db)
    return controller.preview_bulk_absences(bulk_data)


@router.post(
    "/bulk/apply",
    response_model=AbsenceBulkApply,
    status_code=201,
    summary="Apply bulk absence import",
    description="Create validated absences from bulk import.",
)
async def apply_bulk_absences(
    bulk_data: AbsenceBulkCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply bulk absence import.

    Creates all valid absences, skipping those with conflicts. Returns:
    - created: Number of absences successfully created
    - skipped: Number of absences skipped due to validation errors or conflicts
    - errors: List of errors encountered during apply

    Security:
        Requires authentication.
    """
    controller = AbsenceController(db)
    return controller.apply_bulk_absences(bulk_data)
