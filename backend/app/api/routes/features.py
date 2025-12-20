"""Feature flag management API routes.

Admin endpoints for managing feature flags:
- Create, read, update, delete flags
- Evaluate flags
- View statistics and audit logs
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_db
from app.features.flags import FeatureFlagService
from app.models.user import User
from app.schemas.feature_flag import (
    FeatureFlagBulkEvaluationRequest,
    FeatureFlagBulkEvaluationResponse,
    FeatureFlagCreate,
    FeatureFlagEvaluationRequest,
    FeatureFlagEvaluationResponse,
    FeatureFlagListResponse,
    FeatureFlagResponse,
    FeatureFlagStatsResponse,
    FeatureFlagUpdate,
)

router = APIRouter()


@router.post("/", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    flag_in: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Create a new feature flag.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)

    try:
        flag = await service.create_flag(
            key=flag_in.key,
            name=flag_in.name,
            description=flag_in.description,
            flag_type=flag_in.flag_type,
            enabled=flag_in.enabled,
            rollout_percentage=flag_in.rollout_percentage,
            environments=flag_in.environments,
            target_user_ids=flag_in.target_user_ids,
            target_roles=flag_in.target_roles,
            variants=flag_in.variants,
            dependencies=flag_in.dependencies,
            custom_attributes=flag_in.custom_attributes,
            created_by=str(current_user.id),
        )
        return flag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    enabled_only: bool = Query(False, description="Only return enabled flags"),
    environment: str | None = Query(None, description="Filter by environment"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    List all feature flags with pagination.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)
    flags = await service.list_flags(
        enabled_only=enabled_only,
        environment=environment
    )

    # Manual pagination
    total = len(flags)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_flags = flags[start_idx:end_idx]

    total_pages = (total + page_size - 1) // page_size

    return FeatureFlagListResponse(
        flags=paginated_flags,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/stats", response_model=FeatureFlagStatsResponse)
async def get_feature_flag_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get feature flag statistics.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)
    stats = await service.get_stats()
    return FeatureFlagStatsResponse(
        total_flags=stats['total_flags'],
        enabled_flags=stats['enabled_flags'],
        disabled_flags=stats['disabled_flags'],
        percentage_rollout_flags=stats['percentage_rollout_flags'],
        variant_flags=stats['variant_flags'],
        flags_by_environment={},  # TODO: Implement environment breakdown
        recent_evaluations=stats['recent_evaluations'],
        unique_users=stats['unique_users']
    )


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get a specific feature flag by key.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)
    flag = await service.get_flag(key)

    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found"
        )

    return flag


@router.put("/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    flag_update: FeatureFlagUpdate,
    reason: str | None = Query(None, description="Reason for update"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Update a feature flag.

    Requires admin privileges. All changes are logged for audit.
    """
    service = FeatureFlagService(db)

    # Convert Pydantic model to dict, excluding None values
    updates = flag_update.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    try:
        flag = await service.update_flag(
            key=key,
            updates=updates,
            updated_by=str(current_user.id),
            reason=reason
        )
        return flag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for deletion"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Delete a feature flag.

    Requires admin privileges. Deletion is logged for audit.
    """
    service = FeatureFlagService(db)

    deleted = await service.delete_flag(
        key=key,
        deleted_by=str(current_user.id),
        reason=reason
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found"
        )


@router.post("/evaluate", response_model=FeatureFlagEvaluationResponse)
async def evaluate_feature_flag(
    evaluation_request: FeatureFlagEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Evaluate a feature flag for the current user.

    Any authenticated user can evaluate flags for themselves.
    """
    service = FeatureFlagService(db)

    # Use current user's ID and role if not explicitly provided
    user_id = evaluation_request.user_id or str(current_user.id)
    user_role = evaluation_request.user_role or current_user.role

    enabled, variant, reason = await service.evaluate_flag(
        key=evaluation_request.flag_key,
        user_id=user_id,
        user_role=user_role,
        context=evaluation_request.context,
        track_evaluation=True
    )

    # Get flag to determine type
    flag = await service.get_flag(evaluation_request.flag_key)
    flag_type = flag.flag_type if flag else 'boolean'

    return FeatureFlagEvaluationResponse(
        enabled=enabled,
        variant=variant,
        flag_type=flag_type,
        reason=reason
    )


@router.post("/evaluate/bulk", response_model=FeatureFlagBulkEvaluationResponse)
async def evaluate_feature_flags_bulk(
    evaluation_request: FeatureFlagBulkEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Evaluate multiple feature flags at once.

    Useful for initializing client-side feature flag state.
    Any authenticated user can evaluate flags for themselves.
    """
    service = FeatureFlagService(db)

    # Use current user's ID and role if not explicitly provided
    user_id = evaluation_request.user_id or str(current_user.id)
    user_role = evaluation_request.user_role or current_user.role

    results = await service.evaluate_flags_bulk(
        flag_keys=evaluation_request.flag_keys,
        user_id=user_id,
        user_role=user_role,
        context=evaluation_request.context,
        track_evaluation=False  # Don't track bulk evaluations to reduce DB load
    )

    # Convert results to response format
    flag_responses = {}
    for flag_key, (enabled, variant, reason) in results.items():
        # Get flag to determine type
        flag = await service.get_flag(flag_key)
        flag_type = flag.flag_type if flag else 'boolean'

        flag_responses[flag_key] = FeatureFlagEvaluationResponse(
            enabled=enabled,
            variant=variant,
            flag_type=flag_type,
            reason=reason
        )

    return FeatureFlagBulkEvaluationResponse(flags=flag_responses)


@router.post("/{key}/enable", response_model=FeatureFlagResponse)
async def enable_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for enabling"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Enable a feature flag.

    Shortcut endpoint for toggling a flag on.
    Requires admin privileges.
    """
    service = FeatureFlagService(db)

    try:
        flag = await service.update_flag(
            key=key,
            updates={'enabled': True},
            updated_by=str(current_user.id),
            reason=reason or "Flag enabled via API"
        )
        return flag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{key}/disable", response_model=FeatureFlagResponse)
async def disable_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for disabling"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Disable a feature flag.

    Shortcut endpoint for toggling a flag off.
    Requires admin privileges.
    """
    service = FeatureFlagService(db)

    try:
        flag = await service.update_flag(
            key=key,
            updates={'enabled': False},
            updated_by=str(current_user.id),
            reason=reason or "Flag disabled via API"
        )
        return flag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
