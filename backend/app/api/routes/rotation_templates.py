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
    """List all rotation templates, optionally filtered by activity type. Requires authentication."""
    query = db.query(RotationTemplate)

    if activity_type:
        query = query.filter(RotationTemplate.activity_type == activity_type)

    templates = query.order_by(RotationTemplate.name).all()
    return RotationTemplateListResponse(items=templates, total=len(templates))


@router.get("/{template_id}", response_model=RotationTemplateResponse)
async def get_rotation_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a rotation template by ID. Requires authentication."""
    template = (
        await db.execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")
    return template


@router.post("", response_model=RotationTemplateResponse, status_code=201)
async def create_rotation_template(
    template_in: RotationTemplateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new rotation template. Requires authentication."""
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
    """Update an existing rotation template. Requires authentication."""
    template = (
        await db.execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
    ).scalar_one_or_none()
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
    """Delete a rotation template. Requires authentication."""
    template = (
        await db.execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    db.delete(template)
    await db.commit()
