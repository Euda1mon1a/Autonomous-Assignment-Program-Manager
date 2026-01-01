"""Procedures API routes.

Provides endpoints for managing medical procedures that require credentialed supervision.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

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

router = APIRouter(tags=["procedures"])


@router.get(
    "",
    response_model=ProcedureListResponse,
    summary="List all procedures",
    description="""
    Retrieve a list of medical procedures with optional filtering.

    Procedures can be filtered by:
    - **Specialty**: Medical specialty (e.g., 'Family Medicine', 'Pediatrics')
    - **Category**: Procedure category (e.g., 'Diagnostic', 'Therapeutic')
    - **Active Status**: Whether the procedure is currently active
    - **Complexity Level**: Complexity rating (e.g., 'Basic', 'Intermediate', 'Advanced')

    Returns a paginated list of procedures matching the filter criteria.
    """,
    responses={
        200: {"description": "List of procedures retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
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


@router.get(
    "/specialties",
    response_model=list[str],
    summary="Get all procedure specialties",
    description="""
    Retrieve a list of all unique medical specialties that have associated procedures.

    Useful for populating dropdown filters or understanding the scope of procedures
    available across different specialties.
    """,
    responses={
        200: {"description": "List of unique specialties retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def get_specialties(db=Depends(get_async_db)):
    """Get all unique specialties from procedures."""
    controller = ProcedureController(db)
    return controller.get_specialties()


@router.get(
    "/categories",
    response_model=list[str],
    summary="Get all procedure categories",
    description="""
    Retrieve a list of all unique procedure categories in the system.

    Categories classify procedures by type (e.g., 'Diagnostic', 'Therapeutic',
    'Preventive'). Useful for filtering and organizing procedures.
    """,
    responses={
        200: {"description": "List of unique categories retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def get_categories(db=Depends(get_async_db)):
    """Get all unique categories from procedures."""
    controller = ProcedureController(db)
    return controller.get_categories()


@router.get(
    "/by-name/{name}",
    response_model=ProcedureResponse,
    summary="Get procedure by name",
    description="""
    Retrieve a specific procedure using its exact name.

    This endpoint performs an exact match lookup. For searching by partial name,
    use the list endpoint with filters instead.
    """,
    responses={
        200: {"description": "Procedure found and returned"},
        404: {"description": "Procedure with the specified name not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_procedure_by_name(
    name: str,
    db=Depends(get_async_db),
):
    """Get a procedure by its name."""
    controller = ProcedureController(db)
    return controller.get_procedure_by_name(name)


@router.get(
    "/{procedure_id}",
    response_model=ProcedureResponse,
    summary="Get procedure by ID",
    description="""
    Retrieve a specific procedure using its unique identifier (UUID).

    Returns complete procedure details including name, specialty, category,
    complexity level, credential requirements, and active status.
    """,
    responses={
        200: {"description": "Procedure found and returned"},
        404: {"description": "Procedure with the specified ID not found"},
        422: {"description": "Invalid UUID format"},
        500: {"description": "Internal server error"},
    },
)
async def get_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
):
    """Get a procedure by ID."""
    controller = ProcedureController(db)
    return controller.get_procedure(procedure_id)


@router.post(
    "",
    response_model=ProcedureResponse,
    status_code=201,
    summary="Create a new procedure",
    description="""
    Create a new medical procedure in the system.

    **Authentication Required**: This endpoint requires a valid user session.

    The procedure must include:
    - **Name**: Unique procedure name
    - **Specialty**: Medical specialty (e.g., 'Family Medicine')
    - **Category**: Procedure category (e.g., 'Diagnostic', 'Therapeutic')
    - **Complexity Level**: Skill level required (e.g., 'Basic', 'Advanced')

    Optional fields include credential requirements and description.
    """,
    responses={
        201: {"description": "Procedure created successfully"},
        400: {"description": "Invalid request data or duplicate procedure name"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error in request body"},
        500: {"description": "Internal server error"},
    },
)
async def create_procedure(
    procedure_in: ProcedureCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.create_procedure(procedure_in)


@router.put(
    "/{procedure_id}",
    response_model=ProcedureResponse,
    summary="Update an existing procedure",
    description="""
    Update an existing procedure's details.

    **Authentication Required**: This endpoint requires a valid user session.

    You can update any of the following fields:
    - Name
    - Specialty
    - Category
    - Complexity level
    - Credential requirements
    - Description
    - Active status

    All fields are optional in the update request. Only provided fields will be updated.
    """,
    responses={
        200: {"description": "Procedure updated successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        404: {"description": "Procedure not found"},
        422: {"description": "Validation error in request body"},
        500: {"description": "Internal server error"},
    },
)
async def update_procedure(
    procedure_id: UUID,
    procedure_in: ProcedureUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, procedure_in)


@router.delete(
    "/{procedure_id}",
    status_code=204,
    summary="Delete a procedure",
    description="""
    Permanently delete a procedure from the system.

    **Authentication Required**: This endpoint requires a valid user session.

    **Warning**: This is a hard delete operation. The procedure will be permanently
    removed from the database. Consider using the deactivate endpoint instead for
    a soft delete that preserves historical data.

    This operation cannot be undone.
    """,
    responses={
        204: {"description": "Procedure deleted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Procedure not found"},
        422: {"description": "Invalid UUID format"},
        500: {"description": "Internal server error"},
    },
)
async def delete_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a procedure. Requires authentication."""
    controller = ProcedureController(db)
    controller.delete_procedure(procedure_id)


@router.post(
    "/{procedure_id}/deactivate",
    response_model=ProcedureResponse,
    summary="Deactivate a procedure",
    description="""
    Deactivate a procedure (soft delete).

    **Authentication Required**: This endpoint requires a valid user session.

    This sets the procedure's `is_active` flag to false without deleting it from
    the database. Deactivated procedures:
    - Will not appear in default listings (unless specifically filtered)
    - Preserve historical data and relationships
    - Can be reactivated later using the activate endpoint

    This is the recommended way to remove procedures from active use.
    """,
    responses={
        200: {"description": "Procedure deactivated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Procedure not found"},
        422: {"description": "Invalid UUID format"},
        500: {"description": "Internal server error"},
    },
)
async def deactivate_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a procedure (soft delete). Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, ProcedureUpdate(is_active=False))


@router.post(
    "/{procedure_id}/activate",
    response_model=ProcedureResponse,
    summary="Activate a procedure",
    description="""
    Activate a previously deactivated procedure.

    **Authentication Required**: This endpoint requires a valid user session.

    This sets the procedure's `is_active` flag to true, making it available for
    use in the system again. Activated procedures will:
    - Appear in default listings
    - Be available for assignment and scheduling
    - Resume normal functionality

    Use this to restore procedures that were previously deactivated.
    """,
    responses={
        200: {"description": "Procedure activated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Procedure not found"},
        422: {"description": "Invalid UUID format"},
        500: {"description": "Internal server error"},
    },
)
async def activate_procedure(
    procedure_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Activate a procedure. Requires authentication."""
    controller = ProcedureController(db)
    return controller.update_procedure(procedure_id, ProcedureUpdate(is_active=True))
