"""Feature flag decorators for controlling access to routes and functions.

Provides decorators to:
- Require feature flags for API endpoints
- Conditionally execute code based on flags
- A/B test different implementations
"""
from functools import wraps
from typing import Any, Callable

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.features.flags import FeatureFlagService
from app.models.user import User


def require_feature_flag(
    flag_key: str,
    enabled_value: bool = True,
    status_code: int = status.HTTP_404_NOT_FOUND,
    detail: str | None = None
):
    """
    Decorator to require a feature flag for a route or function.

    Usage:
        @router.get("/new-feature")
        @require_feature_flag("new_feature", enabled_value=True)
        async def new_feature_endpoint(
            current_user: User = Depends(get_current_active_user),
            db = Depends(get_db),
        ):
            return {"message": "New feature!"}

    Args:
        flag_key: Feature flag key to check
        enabled_value: Required value (True or False)
        status_code: HTTP status code if flag check fails (default: 404)
        detail: Error message (default: "Feature not available")

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract user and db from kwargs (FastAPI dependency injection)
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')

            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )

            # Evaluate feature flag
            service = FeatureFlagService(db)
            user_id = str(current_user.id) if current_user else None
            user_role = current_user.role if current_user else None

            enabled, variant, reason = await service.evaluate_flag(
                key=flag_key,
                user_id=user_id,
                user_role=user_role,
                track_evaluation=True
            )

            # Check if flag matches required value
            if enabled != enabled_value:
                error_detail = detail or "Feature not available"
                raise HTTPException(
                    status_code=status_code,
                    detail=error_detail
                )

            # Flag check passed, execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def feature_flag_gate(
    flag_key: str,
    default_value: Any = None
):
    """
    Decorator to conditionally execute a function based on feature flag.

    If flag is disabled, returns default_value instead of executing function.

    Usage:
        @feature_flag_gate("experimental_algorithm", default_value=[])
        async def experimental_algorithm(data: list) -> list:
            # New experimental logic
            return processed_data

    Args:
        flag_key: Feature flag key to check
        default_value: Value to return if flag is disabled

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Try to get db and user from kwargs
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')

            if db is None:
                # No DB available, execute function normally
                return await func(*args, **kwargs)

            # Evaluate feature flag
            service = FeatureFlagService(db)
            user_id = str(current_user.id) if current_user else None
            user_role = current_user.role if current_user else None

            enabled, _, _ = await service.evaluate_flag(
                key=flag_key,
                user_id=user_id,
                user_role=user_role,
                track_evaluation=False  # Don't track for internal gates
            )

            if enabled:
                # Flag enabled, execute function
                return await func(*args, **kwargs)
            else:
                # Flag disabled, return default value
                return default_value

        return wrapper
    return decorator


def ab_test_variant(
    flag_key: str,
    variants: dict[str, Callable]
):
    """
    Decorator for A/B testing different function implementations.

    Routes to different implementations based on variant assignment.

    Usage:
        async def control_implementation(data):
            return process_old_way(data)

        async def variant_a_implementation(data):
            return process_new_way_a(data)

        async def variant_b_implementation(data):
            return process_new_way_b(data)

        @ab_test_variant("recommendation_algorithm", {
            "control": control_implementation,
            "variant_a": variant_a_implementation,
            "variant_b": variant_b_implementation,
        })
        async def get_recommendations(
            user_id: str,
            db = Depends(get_db),
            current_user: User = Depends(get_current_active_user)
        ):
            # This function body is replaced by variant implementation
            pass

    Args:
        flag_key: Feature flag key for A/B test
        variants: Map of variant name to implementation function

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')

            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available for A/B test"
                )

            # Evaluate feature flag to get variant
            service = FeatureFlagService(db)
            user_id = str(current_user.id) if current_user else None
            user_role = current_user.role if current_user else None

            enabled, variant, reason = await service.evaluate_flag(
                key=flag_key,
                user_id=user_id,
                user_role=user_role,
                track_evaluation=True
            )

            # Get implementation for assigned variant
            if variant and variant in variants:
                implementation = variants[variant]
            elif 'control' in variants:
                # Fallback to control if variant not found
                implementation = variants['control']
            else:
                # No variant assigned and no control, use original function
                return await func(*args, **kwargs)

            # Execute variant implementation
            return await implementation(*args, **kwargs)

        return wrapper
    return decorator


class FeatureFlagContext:
    """
    Context manager for feature flag-gated code blocks.

    Usage:
        async with FeatureFlagContext(db, "new_feature", current_user) as enabled:
            if enabled:
                # New feature code
                do_new_thing()
            else:
                # Fallback code
                do_old_thing()
    """

    def __init__(
        self,
        db: Any,
        flag_key: str,
        user: User | None = None
    ):
        """
        Initialize feature flag context.

        Args:
            db: Database session
            flag_key: Feature flag key
            user: Current user (optional)
        """
        self.db = db
        self.flag_key = flag_key
        self.user = user
        self.enabled = False

    async def __aenter__(self) -> bool:
        """Enter context and evaluate flag."""
        service = FeatureFlagService(self.db)
        user_id = str(self.user.id) if self.user else None
        user_role = self.user.role if self.user else None

        self.enabled, _, _ = await service.evaluate_flag(
            key=self.flag_key,
            user_id=user_id,
            user_role=user_role,
            track_evaluation=False
        )

        return self.enabled

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        return False  # Don't suppress exceptions


def feature_enabled(
    db: Any,
    flag_key: str,
    user: User | None = None
) -> bool:
    """
    Synchronous helper to check if a feature flag is enabled.

    Note: This is a synchronous wrapper and should only be used
    in non-async contexts. Prefer async evaluation when possible.

    Args:
        db: Database session
        flag_key: Feature flag key
        user: Current user (optional)

    Returns:
        True if flag is enabled, False otherwise
    """
    # This is a simplified synchronous check
    # For production use, this should use async evaluation
    import asyncio

    service = FeatureFlagService(db)
    user_id = str(user.id) if user else None
    user_role = user.role if user else None

    try:
        enabled, _, _ = asyncio.run(service.evaluate_flag(
            key=flag_key,
            user_id=user_id,
            user_role=user_role,
            track_evaluation=False
        ))
        return enabled
    except Exception:
        # Default to disabled on error
        return False
