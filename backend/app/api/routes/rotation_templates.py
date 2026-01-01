"""Rotation template API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.rotation_template import (
    RotationTemplateCreate,
    RotationTemplateListResponse,
    RotationTemplateResponse,
    RotationTemplateUpdate,
)

router = APIRouter()


@router.get("", response_model=RotationTemplateListResponse)
async def list_rotation_templates(
    activity_type: str | None = Query(None, description="Filter by activity type"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all rotation templates with optional filtering.

    Args:
        activity_type: Filter by activity type (e.g., 'clinic', 'inpatient', 'procedures', 'on_call').
        db: Database session.
        current_user: Authenticated user.

    Returns:
        RotationTemplateListResponse with list of templates and total count, sorted by name.

    Security:
        Requires authentication.

    Note:
        Rotation templates define reusable rotation configurations:
        - Activity type (clinic, inpatient, procedures, conference, etc.)
        - Default duration
        - Required credentials
        - Supervision requirements

        Templates are used during schedule generation to create assignments.

    Example Query:
        GET /api/rotation-templates?activity_type=clinic

    Status Codes:
        - 200: Templates retrieved successfully
    """
    query = select(RotationTemplate)

    if activity_type:
        query = query.where(RotationTemplate.activity_type == activity_type)

    query = query.order_by(RotationTemplate.name)
    result = await db.execute(query)
    templates = result.scalars().all()
    return RotationTemplateListResponse(items=templates, total=len(templates))


@router.get("/{template_id}", response_model=RotationTemplateResponse)
async def get_rotation_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a rotation template by ID.

    Args:
        template_id: UUID of the template to retrieve.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        RotationTemplateResponse with full template details including:
        - Name and description
        - Activity type
        - Default duration
        - Required credentials
        - Supervision requirements

    Security:
        Requires authentication.

    Note:
        Use this endpoint to retrieve detailed configuration for a specific
        rotation template before applying it to schedule assignments.

    Raises:
        HTTPException: 404 if template not found.

    Status Codes:
        - 200: Template retrieved successfully
        - 404: Template not found
    """
    template = (
        (await db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))).scalar_one_or_none()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")
    return template


@router.post("", response_model=RotationTemplateResponse, status_code=201)
async def create_rotation_template(
    template_in: RotationTemplateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new rotation template.

    Args:
        template_in: Template creation payload including:
            - name: Unique template name
            - description: Template purpose/details
            - activity_type: Type of activity (clinic, inpatient, etc.)
            - default_duration: Default duration in blocks
            - required_credentials: List of required credentials (optional)
        db: Database session.
        current_user: Authenticated user.

    Returns:
        RotationTemplateResponse with created template details.

    Security:
        Requires authentication.

    Note:
        Templates define reusable rotation configurations that can be applied
        during schedule generation. They enforce credential requirements and
        standardize rotation definitions across the academic year.

    Example Request Body:
        {
            "name": "Pediatric Clinic",
            "description": "Outpatient pediatric clinic rotation",
            "activity_type": "clinic",
            "default_duration": 10,
            "required_credentials": ["PALS", "BLS"]
        }

    Status Codes:
        - 201: Template created successfully
        - 400: Invalid template data
        - 409: Template with same name already exists
    """
    template = RotationTemplate(**template_in.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/{template_id}", response_model=RotationTemplateResponse)
async def update_rotation_template(
    template_id: UUID,
    template_in: RotationTemplateUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing rotation template.

    Args:
        template_id: UUID of the template to update.
        template_in: Template update payload with fields to modify.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        RotationTemplateResponse with updated template details.

    Security:
        Requires authentication.

    Note:
        Only provided fields will be updated (partial updates supported).
        Updating a template does not affect existing assignments created
        from this template - only future schedule generations.

    Example Request Body (partial update):
        {
            "default_duration": 15,
            "required_credentials": ["PALS", "BLS", "NRP"]
        }

    Raises:
        HTTPException: 404 if template not found.

    Status Codes:
        - 200: Template updated successfully
        - 400: Invalid update data
        - 404: Template not found
        - 409: Update creates name conflict
    """
    template = (
        (await db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))).scalar_one_or_none()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_rotation_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a rotation template.

    Args:
        template_id: UUID of the template to delete.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        No content (204).

    Security:
        Requires authentication.

    Warning:
        Deleting a template does not delete assignments created from it,
        but future schedule generations will not be able to use this template.

    Note:
        Only delete templates that are:
        - No longer used in your program
        - Created in error
        - Being replaced by a newer version

        Consider deactivating instead of deletion if you want to preserve
        historical template configurations.

    Raises:
        HTTPException:
            - 404: Template not found
            - 409: Cannot delete template currently in use (if constraint enabled)

    Status Codes:
        - 204: Template deleted successfully
        - 404: Template not found
        - 409: Conflict (template in active use)
    """
    template = (
        (await db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))).scalar_one_or_none()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    await db.delete(template)
    await db.commit()
