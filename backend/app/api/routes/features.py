"""Feature flag management API routes.

Admin endpoints for managing feature flags:
- Create, read, update, delete flags
- Evaluate flags
- View statistics and audit logs
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_db
from app.features.flags import FeatureFlagService
from app.models.feature_flag import FeatureFlag
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


def _to_flag_mapping(flag: Any) -> dict[str, Any]:
    if isinstance(flag, dict):
        return flag
    raw = getattr(flag, "__dict__", None)
    if isinstance(raw, dict):
        return raw
    return {}


def _to_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _to_datetime(value: Any, *, default: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return default
    return default


def _to_str_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return None


def _to_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return None


def _normalize_variants(value: Any) -> dict[str, float] | None:
    parsed: dict[str, float] = {}

    if value is None:
        return None

    if isinstance(value, dict):
        for key, weight in value.items():
            try:
                parsed[str(key)] = float(weight)
            except (TypeError, ValueError):
                continue
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            weight = item.get("weight")
            if key is None or weight is None:
                continue
            try:
                parsed[str(key)] = float(weight)
            except (TypeError, ValueError):
                continue
    else:
        return None

    if not parsed:
        return None

    total = sum(parsed.values())
    if 1.01 < total <= 100.0:
        parsed = {k: v / 100.0 for k, v in parsed.items()}
        total = sum(parsed.values())

    if not (0.99 <= total <= 1.01):
        return None
    if any(weight < 0.0 or weight > 1.0 for weight in parsed.values()):
        return None
    return parsed


def _normalize_feature_flag(flag: Any) -> FeatureFlagResponse:
    now = datetime.now(UTC)
    data = _to_flag_mapping(flag)

    key = data.get("key")
    if not isinstance(key, str) or not key:
        key = "unknown-feature"

    name = data.get("name")
    if not isinstance(name, str) or not name:
        name = key.replace("-", " ").title()

    flag_type = data.get("flag_type")
    if not isinstance(flag_type, str) or flag_type not in {
        "boolean",
        "percentage",
        "variant",
    }:
        flag_type = "boolean"

    return FeatureFlagResponse(
        id=_to_uuid(data.get("id")) or uuid4(),
        key=key,
        name=name,
        description=data.get("description")
        if isinstance(data.get("description"), str)
        else None,
        flag_type=flag_type,
        enabled=bool(data.get("enabled", False)),
        rollout_percentage=(
            float(data["rollout_percentage"])
            if data.get("rollout_percentage") is not None
            else None
        ),
        environments=_to_str_list(data.get("environments")),
        target_user_ids=_to_str_list(data.get("target_user_ids")),
        target_roles=_to_str_list(data.get("target_roles")),
        variants=_normalize_variants(data.get("variants")),
        dependencies=_to_str_list(data.get("dependencies")),
        custom_attributes=_to_dict(data.get("custom_attributes")),
        created_by=_to_uuid(data.get("created_by")),
        created_at=_to_datetime(data.get("created_at"), default=now),
        updated_at=_to_datetime(data.get("updated_at"), default=now),
    )


@router.post(
    "/", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED
)
async def create_feature_flag(
    flag_in: FeatureFlagCreate,
    db: Session = Depends(get_db),
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
        return _normalize_feature_flag(flag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    enabled_only: bool = Query(False, description="Only return enabled flags"),
    environment: str | None = Query(None, description="Filter by environment"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    List all feature flags with pagination.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)
    flags = await service.list_flags(enabled_only=enabled_only, environment=environment)

    # Manual pagination
    total = len(flags)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_flags = flags[start_idx:end_idx]

    total_pages = (total + page_size - 1) // page_size

    return FeatureFlagListResponse(
        flags=[_normalize_feature_flag(flag) for flag in paginated_flags],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=FeatureFlagStatsResponse)
async def get_feature_flag_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get feature flag statistics.

    Requires admin privileges.
    """
    service = FeatureFlagService(db)
    stats = await service.get_stats()

    # Get flags by environment breakdown
    flags_by_environment = await _get_flags_by_environment(db)

    return FeatureFlagStatsResponse(
        total_flags=int(stats.get("total_flags", 0)),
        enabled_flags=int(stats.get("enabled_flags", 0)),
        disabled_flags=int(stats.get("disabled_flags", 0)),
        percentage_rollout_flags=int(stats.get("percentage_rollout_flags", 0)),
        variant_flags=int(stats.get("variant_flags", 0)),
        flags_by_environment=flags_by_environment,
        recent_evaluations=int(stats.get("recent_evaluations", 0)),
        unique_users=int(stats.get("unique_users", 0)),
    )


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    key: str,
    db: Session = Depends(get_db),
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
            detail=f"Feature flag '{key}' not found",
        )

    return _normalize_feature_flag(flag)


@router.put("/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    flag_update: FeatureFlagUpdate,
    reason: str | None = Query(None, description="Reason for update"),
    db: Session = Depends(get_db),
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="No updates provided"
        )

    try:
        flag = await service.update_flag(
            key=key, updates=updates, updated_by=str(current_user.id), reason=reason
        )
        return _normalize_feature_flag(flag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for deletion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> None:
    """
    Delete a feature flag.

    Requires admin privileges. Deletion is logged for audit.
    """
    service = FeatureFlagService(db)

    deleted = await service.delete_flag(
        key=key, deleted_by=str(current_user.id), reason=reason
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found",
        )


@router.post("/evaluate", response_model=FeatureFlagEvaluationResponse)
async def evaluate_feature_flag(
    evaluation_request: FeatureFlagEvaluationRequest,
    db: Session = Depends(get_db),
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
        track_evaluation=True,
    )

    # Get flag to determine type
    flag = await service.get_flag(evaluation_request.flag_key)
    flag_type = flag.flag_type if flag else "boolean"

    return FeatureFlagEvaluationResponse(
        enabled=enabled, variant=variant, flag_type=flag_type, reason=reason
    )


@router.post("/evaluate/bulk", response_model=FeatureFlagBulkEvaluationResponse)
async def evaluate_feature_flags_bulk(
    evaluation_request: FeatureFlagBulkEvaluationRequest,
    db: Session = Depends(get_db),
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
        track_evaluation=False,  # Don't track bulk evaluations to reduce DB load
    )

    # Convert results to response format
    flag_responses = {}
    for flag_key, (enabled, variant, reason) in results.items():
        # Get flag to determine type
        flag = await service.get_flag(flag_key)
        flag_type = flag.flag_type if flag else "boolean"

        flag_responses[flag_key] = FeatureFlagEvaluationResponse(
            enabled=enabled, variant=variant, flag_type=flag_type, reason=reason
        )

    return FeatureFlagBulkEvaluationResponse(flags=flag_responses)


@router.post("/{key}/enable", response_model=FeatureFlagResponse)
async def enable_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for enabling"),
    db: Session = Depends(get_db),
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
            updates={"enabled": True},
            updated_by=str(current_user.id),
            reason=reason or "Flag enabled via API",
        )
        return _normalize_feature_flag(flag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{key}/disable", response_model=FeatureFlagResponse)
async def disable_feature_flag(
    key: str,
    reason: str | None = Query(None, description="Reason for disabling"),
    db: Session = Depends(get_db),
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
            updates={"enabled": False},
            updated_by=str(current_user.id),
            reason=reason or "Flag disabled via API",
        )
        return _normalize_feature_flag(flag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


async def _get_flags_by_environment(db: Session) -> dict[str, Any]:
    """
    Get feature flags breakdown by environment.

    Returns:
        Dictionary mapping environments to their feature flag statistics
    """
    environments = ["development", "staging", "production"]
    result = {}

    for env in environments:
        # Get all flags
        all_flags_result = db.execute(select(FeatureFlag))
        all_flags = all_flags_result.scalars().all()

        # Filter flags for this environment
        env_flags = []
        for flag in all_flags:
            # If flag.environments is None, it applies to all environments
            # If flag.environments is a list, check if env is in it
            if flag.environments is None or env in flag.environments:
                env_flags.append(flag)

                # Categorize flags
        enabled = [f.key for f in env_flags if f.enabled]
        disabled = [f.key for f in env_flags if not f.enabled]
        rollout_percentages = {}

        for flag in env_flags:
            if flag.rollout_percentage is not None and flag.rollout_percentage < 1.0:
                rollout_percentages[flag.key] = int(flag.rollout_percentage * 100)

        result[env] = {
            "total": len(env_flags),
            "enabled": enabled,
            "disabled": disabled,
            "rollout_percentages": rollout_percentages,
        }

    return result
