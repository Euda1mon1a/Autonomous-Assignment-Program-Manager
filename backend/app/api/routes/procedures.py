"""Procedures API routes.

Provides endpoints for managing medical procedures that require credentialed supervision.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.procedure_controller import ProcedureController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureListResponse,
    ProcedureResponse,
    ProcedureUpdate,
)

router = APIRouter()


@router.get("", response_model=ProcedureListResponse)
async def list_procedures(
    specialty: str | None = Query(None, description="Filter by specialty"),
    category: str | None = Query(None, description="Filter by category"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    complexity_level: str | None = Query(
        None, description="Filter by complexity level"
    ),
    db=Depends(get_async_db),
):
    """List all procedures with optional filters."""
    controller = ProcedureController(db)
    return controller.list_procedures(
        specialty=specialty,
        category=category,
        is_active=is_active,
        complexity_level=complexity_level,
    )


@router.get("/specialties", response_model=list[str])
async def get_specialties(db=Depends(get_async_db)):
    """Get all unique specialties from procedures."""
    controller = ProcedureController(db)
    return controller.get_specialties()


@router.get("/categories", response_model=list[str])
async def get_categories(db=Depends(get_async_db)):
    """Get all unique categories from procedures."""
    controller = ProcedureController(db)
    return controller.get_categories()


@router.get("/by-name/{name}", response_model=ProcedureResponse)
async def get_procedure_by_name(
    name: str,
    db=Depends(get_async_db),
):
    """Get a procedure by its name."""
    controller = ProcedureController(db)
    return controller.get_procedure_by_name(name)


@router.get("/{procedure_id}", response_model=ProcedureResponse)
async def get_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
):
    """Get a procedure by ID."""
    controller = ProcedureController(db)
    return controller.get_procedure(procedure_id)


@router.post("", response_model=ProcedureResponse, status_code=201)
async def create_procedure(
    procedure_in: ProcedureCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.create_procedure(procedure_in)


@router.put("/{procedure_id}", response_model=ProcedureResponse)
async def update_procedure(
    procedure_id: UUID,
    procedure_in: ProcedureUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, procedure_in)


@router.delete("/{procedure_id}", status_code=204)
async def delete_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a procedure. Requires authentication."""
    controller = ProcedureController(db)
    controller.delete_procedure(procedure_id)


@router.post("/{procedure_id}/deactivate", response_model=ProcedureResponse)
async def deactivate_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a procedure (soft delete). Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, ProcedureUpdate(is_active=False))


@router.post("/{procedure_id}/activate", response_model=ProcedureResponse)
async def activate_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Activate a procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, ProcedureUpdate(is_active=True))
