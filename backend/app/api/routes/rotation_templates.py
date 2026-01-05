"""Rotation template API routes.

Provides endpoints for:
- CRUD operations on rotation templates
- Weekly pattern management (GET/PUT for patterns)
- Rotation preference management (GET/PUT for preferences)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.rotation_template import (
    BatchTemplateDeleteRequest,
    BatchTemplateResponse,
    BatchTemplateUpdateRequest,
    RotationTemplateCreate,
    RotationTemplateListResponse,
    RotationTemplateResponse,
    RotationTemplateUpdate,
)
from app.schemas.rotation_template_gui import (
    RotationPreferenceCreate,
    RotationPreferenceResponse,
    WeeklyGridUpdate,
    WeeklyPatternResponse,
)
from app.services.rotation_template_service import RotationTemplateService

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


# =============================================================================
# Batch Operation Endpoints
# =============================================================================


@router.delete("/batch", response_model=BatchTemplateResponse)
async def batch_delete_rotation_templates(
    request: BatchTemplateDeleteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete multiple rotation templates atomically.

    Features:
    - Delete up to 100 templates at once
    - Dry-run mode for validation without deleting
    - Atomic operation (all or nothing)

    Args:
        request: BatchTemplateDeleteRequest with list of template IDs
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found

    Example:
        ```json
        {
          "template_ids": ["uuid1", "uuid2", "uuid3"],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        result = await service.batch_delete(request.template_ids, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch delete operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch", response_model=BatchTemplateResponse)
async def batch_update_rotation_templates(
    request: BatchTemplateUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update multiple rotation templates atomically.

    Features:
    - Update up to 100 templates at once
    - Each template can have different update values
    - Dry-run mode for validation without updating
    - Atomic operation (all or nothing)

    Args:
        request: BatchTemplateUpdateRequest with list of template updates
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found or validation fails

    Example:
        ```json
        {
          "templates": [
            {
              "template_id": "uuid1",
              "updates": {"max_residents": 5, "supervision_required": true}
            },
            {
              "template_id": "uuid2",
              "updates": {"activity_type": "inpatient"}
            }
          ],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        # Convert request to dict format expected by service
        updates = [
            {
                "template_id": item.template_id,
                "updates": item.updates.model_dump(exclude_unset=True),
            }
            for item in request.templates
        ]

        result = await service.batch_update(updates, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch update operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Weekly Pattern Endpoints
# =============================================================================


@router.get("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def get_weekly_patterns(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all weekly patterns for a rotation template.

    Returns the 7x2 weekly grid of AM/PM slots defining the rotation pattern.
    Each pattern includes day of week, time of day, and assigned activity type.

    Args:
        template_id: UUID of the rotation template

    Returns:
        List of WeeklyPatternResponse with all patterns for the template

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    patterns = await service.get_patterns_by_template_id(template_id)
    return patterns


@router.put("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def replace_weekly_patterns(
    template_id: UUID,
    grid_update: WeeklyGridUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Atomically replace all weekly patterns for a rotation template.

    This endpoint performs an atomic replacement:
    1. Deletes all existing patterns for the template
    2. Creates new patterns from the provided list
    3. Returns the newly created patterns

    Use this for the visual grid editor to save the entire pattern at once.

    Args:
        template_id: UUID of the rotation template
        grid_update: WeeklyGridUpdate with list of patterns (max 14)

    Returns:
        List of newly created WeeklyPatternResponse

    Raises:
        404: Template not found
        400: Validation error (duplicate slots, invalid data)
    """
    service = RotationTemplateService(db)

    try:
        patterns = await service.replace_patterns(template_id, grid_update.patterns)
        await service.commit()
        return patterns
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Rotation Preference Endpoints
# =============================================================================


@router.get(
    "/{template_id}/preferences", response_model=list[RotationPreferenceResponse]
)
async def get_rotation_preferences(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all scheduling preferences for a rotation template.

    Preferences are soft constraints that guide the scheduling optimizer.
    Each preference has a type, weight (low/medium/high/required), and
    optional configuration parameters.

    Args:
        template_id: UUID of the rotation template

    Returns:
        List of RotationPreferenceResponse with all preferences

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    preferences = await service.get_preferences_by_template_id(template_id)
    return preferences


@router.put(
    "/{template_id}/preferences", response_model=list[RotationPreferenceResponse]
)
async def replace_rotation_preferences(
    template_id: UUID,
    preferences: list[RotationPreferenceCreate],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Atomically replace all preferences for a rotation template.

    This endpoint performs an atomic replacement:
    1. Deletes all existing preferences for the template
    2. Creates new preferences from the provided list
    3. Returns the newly created preferences

    Valid preference types:
    - full_day_grouping: Prefer AM+PM of same activity
    - consecutive_specialty: Group specialty sessions
    - avoid_isolated: Avoid single orphaned half-day sessions
    - preferred_days: Prefer specific activities on specific days
    - avoid_friday_pm: Keep Friday PM open as travel buffer
    - balance_weekly: Distribute activities evenly

    Args:
        template_id: UUID of the rotation template
        preferences: List of RotationPreferenceCreate

    Returns:
        List of newly created RotationPreferenceResponse

    Raises:
        404: Template not found
        400: Validation error (invalid type, duplicate types, etc.)
    """
    service = RotationTemplateService(db)

    try:
        new_preferences = await service.replace_preferences(template_id, preferences)
        await service.commit()
        return new_preferences
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))
