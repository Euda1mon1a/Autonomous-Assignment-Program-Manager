"""
Role permission caching system for improved authorization performance.

This module provides a comprehensive permission management system with:
- Redis-based caching for fast permission lookups
- Role hierarchy with permission inheritance
- Resource-level permission checks
- FastAPI decorators and dependencies
- TTL-based cache invalidation
- Cache warming on startup

Usage Examples:

1. Using decorators:
    ```python
    from app.auth.permissions import require_permission, ResourceType, PermissionAction

    @router.post("/schedules")
    @require_permission(ResourceType.SCHEDULE, PermissionAction.CREATE)
    async def create_schedule(current_user: User = Depends(get_current_active_user)):
        ...
    ```

2. Using dependencies:
    ```python
    from app.auth.permissions import RequireScheduleCreate

    @router.post("/schedules")
    async def create_schedule(current_user: User = RequireScheduleCreate):
        ...
    ```

3. Manual permission checking:
    ```python
    from app.auth.permissions import get_permission_resolver

    resolver = await get_permission_resolver()
    has_perm = await resolver.has_permission(
        user=current_user,
        resource=ResourceType.SCHEDULE,
        action=PermissionAction.CREATE
    )
    ```

4. Cache warming on startup:
    ```python
    from app.auth.permissions import warm_permission_cache

    @app.on_event("startup")
    async def startup():
        await warm_permission_cache()
    ```
"""

from app.auth.permissions.cache import (
    PermissionCache,
    close_permission_cache,
    get_permission_cache,
)
from app.auth.permissions.decorators import (
    PermissionDenied,
    RequireAnalytics,
    RequireAssignmentCreate,
    RequireAssignmentRead,
    RequireResilienceManage,
    RequireResilienceView,
    RequireScheduleCreate,
    RequireScheduleDelete,
    RequireScheduleRead,
    RequireScheduleUpdate,
    RequireUserManagement,
    check_permission_dependency,
    require_all_permissions,
    require_any_permission,
    require_permission,
    require_role,
)
from app.auth.permissions.models import (
    DEFAULT_ROLE_PERMISSIONS,
    ROLE_HIERARCHY,
    ROLE_LEVELS,
    Permission,
    PermissionAction,
    PermissionCheckResult,
    ResourceType,
    RolePermissions,
    UserRole,
)
from app.auth.permissions.resolver import (
    PermissionResolver,
    get_permission_resolver,
)

__all__ = [
    # Models
    "Permission",
    "PermissionAction",
    "PermissionCheckResult",
    "ResourceType",
    "RolePermissions",
    "UserRole",
    "DEFAULT_ROLE_PERMISSIONS",
    "ROLE_HIERARCHY",
    "ROLE_LEVELS",
    # Cache
    "PermissionCache",
    "get_permission_cache",
    "close_permission_cache",
    # Resolver
    "PermissionResolver",
    "get_permission_resolver",
    # Decorators and dependencies
    "PermissionDenied",
    "check_permission_dependency",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_role",
    # Convenience dependencies
    "RequireScheduleRead",
    "RequireScheduleCreate",
    "RequireScheduleUpdate",
    "RequireScheduleDelete",
    "RequireAssignmentRead",
    "RequireAssignmentCreate",
    "RequireUserManagement",
    "RequireAnalytics",
    "RequireResilienceView",
    "RequireResilienceManage",
    # Utilities
    "warm_permission_cache",
    "invalidate_permission_cache",
    "invalidate_user_role_cache",
]


async def warm_permission_cache() -> int:
    """
    Pre-populate permission cache on application startup.

    This improves performance by ensuring frequently accessed permissions
    are already cached before the first request.

    Returns:
        Number of roles successfully cached
    """
    cache = await get_permission_cache()
    resolver = await get_permission_resolver()

    # Build permissions map with hierarchy resolution
    permissions_map = {}
    for role in UserRole:
        permissions = await resolver.get_role_permissions(role, use_cache=False)
        permissions_map[role] = permissions

    # Warm the cache
    cached_count = await cache.warm_cache(permissions_map)

    return cached_count


async def invalidate_permission_cache(
    user_id: str | None = None,
    role: UserRole | str | None = None,
    invalidate_all: bool = False,
) -> bool:
    """
    Invalidate permission cache.

    Use this when permissions change (e.g., role assignments, permission updates).

    Args:
        user_id: Optional user ID to invalidate
        role: Optional role to invalidate
        invalidate_all: Whether to invalidate all cached permissions

    Returns:
        True if invalidation successful, False otherwise
    """
    cache = await get_permission_cache()

    if invalidate_all:
        return await cache.invalidate_all_permissions()
    elif user_id is not None:
        return await cache.invalidate_user_permissions(user_id)
    elif role is not None:
        return await cache.invalidate_role_permissions(role)
    else:
        # No specific target, do nothing
        return False


async def invalidate_user_role_cache(
    user_id: str, old_role: str | None = None, new_role: str | None = None
) -> bool:
    """
    Invalidate permission cache when a user's role changes.

    SECURITY: This MUST be called whenever a user's role is updated to ensure
    they immediately get the correct permissions for their new role.

    Args:
        user_id: User ID whose role changed
        old_role: Previous role (for logging)
        new_role: New role (for logging)

    Returns:
        True if invalidation successful, False otherwise

    Example:
        ```python
        from app.auth.permissions import invalidate_user_role_cache

        # In your user update service/endpoint:
        user.role = "coordinator"
        await db.commit()

        # CRITICAL: Invalidate cache immediately after role change
        await invalidate_user_role_cache(
            user_id=str(user.id),
            old_role="faculty",
            new_role="coordinator"
        )
        ```
    """
    import logging

    logger = logging.getLogger(__name__)

    cache = await get_permission_cache()

    # Invalidate user's permission cache
    success = await cache.invalidate_user_permissions(user_id)

    if success:
        if old_role and new_role:
            logger.info(
                f"SECURITY: Invalidated permission cache for user {user_id} "
                f"after role change: {old_role} -> {new_role}"
            )
        else:
            logger.info(
                f"SECURITY: Invalidated permission cache for user {user_id} "
                f"after role change"
            )
    else:
        logger.warning(
            f"SECURITY WARNING: Failed to invalidate permission cache for user {user_id} "
            f"after role change. Permissions may be stale!"
        )

    return success
