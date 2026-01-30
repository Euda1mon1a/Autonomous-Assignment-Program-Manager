"""Activity API routes for slot-level schedule events.

Provides endpoints for:
- CRUD operations on activities
- List activities with filtering

Activities are distinct from Rotations:
- Rotation = Multi-week block assignment (e.g., "Neurology" for 4 weeks)
- Activity = Slot-level event (e.g., "FM Clinic AM", "LEC Wednesday PM")
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
)
from app.services.activity_service import ActivityService

router = APIRouter()


# =============================================================================
# Collection-level endpoints (no path parameters)
# These MUST come before parametric routes to avoid path conflicts
# =============================================================================


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    category: str | None = Query(
        None,
        description="Filter by activity_category (clinical, educational, time_off, administrative)",
    ),
    include_archived: bool = Query(
        False, description="Include archived activities in results"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all activities with optional filtering.

    Args:
        category: Filter by activity_category
        include_archived: Include archived activities (default: False)
        db: Database session
        current_user: Current authenticated user

    Returns:
        ActivityListResponse with filtered activities
    """
    service = ActivityService(db)
    activities = await service.list_activities(
        category=category,
        include_archived=include_archived,
    )
    return ActivityListResponse(
        activities=[ActivityResponse.model_validate(a) for a in activities],
        total=len(activities),
    )


@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    activity_in: ActivityCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new activity.

    Args:
        activity_in: Activity creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created ActivityResponse

    Raises:
        HTTPException: 400 if activity with same name or code exists
    """
    service = ActivityService(db)
    try:
        activity = await service.create_activity(activity_in)
        await db.commit()
        return ActivityResponse.model_validate(activity)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

        # =============================================================================
        # Single Activity Endpoints
        # =============================================================================


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get activity by ID.

    Args:
        activity_id: UUID of the activity
        db: Database session
        current_user: Current authenticated user

    Returns:
        ActivityResponse

    Raises:
        HTTPException: 404 if activity not found
    """
    service = ActivityService(db)
    activity = await service.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityResponse.model_validate(activity)


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    activity_in: ActivityUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an activity.

    Args:
        activity_id: UUID of the activity
        activity_in: Update data (only non-None fields are updated)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated ActivityResponse

    Raises:
        HTTPException: 404 if activity not found
        HTTPException: 400 if name or code conflicts
    """
    service = ActivityService(db)
    try:
        activity = await service.update_activity(activity_id, activity_in)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        await db.commit()
        return ActivityResponse.model_validate(activity)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Hard delete an activity.

    Note: This will fail if the activity is in use by weekly patterns
    or rotation requirements. Use archive instead for soft delete.

    Args:
        activity_id: UUID of the activity
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if activity not found
        HTTPException: 400 if activity is in use
    """
    service = ActivityService(db)
    try:
        deleted = await service.delete_activity(activity_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Activity not found")
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{activity_id}/archive", response_model=ActivityResponse)
async def archive_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Soft delete (archive) an activity.

    Archived activities are hidden from default lists but can still
    be referenced by existing data.

    Args:
        activity_id: UUID of the activity
        db: Database session
        current_user: Current authenticated user

    Returns:
        Archived ActivityResponse

    Raises:
        HTTPException: 404 if activity not found
    """
    service = ActivityService(db)
    activity = await service.archive_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.commit()
    return ActivityResponse.model_validate(activity)
