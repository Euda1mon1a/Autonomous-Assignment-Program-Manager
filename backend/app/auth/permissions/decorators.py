"""FastAPI decorators and dependencies for permission checking."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, status

from app.auth.permissions.models import PermissionAction, ResourceType
from app.auth.permissions.resolver import get_permission_resolver
from app.core.security import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)


class PermissionDenied(HTTPException):
    """Custom exception for permission denied errors."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def check_permission_dependency(
    resource: ResourceType | str,
    action: PermissionAction | str,
    resource_id: str | None = None,
    use_cache: bool = True,
) -> Callable:
    """
    Create a FastAPI dependency that checks permissions.

    Usage:
        @router.get("/schedules")
        async def get_schedules(
            current_user: User = Depends(
                check_permission_dependency(ResourceType.SCHEDULE, PermissionAction.READ)
            )
        ):
            ...

    Args:
        resource: Resource type
        action: Action to perform
        resource_id: Optional resource ID
        use_cache: Whether to use cache

    Returns:
        Dependency function
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if current user has required permission."""
        resolver = await get_permission_resolver()

        result = await resolver.check_permission(
            user=current_user,
            resource=resource,
            action=action,
            resource_id=resource_id,
            use_cache=use_cache,
        )

        if not result.allowed:
            logger.warning(
                f"Permission denied for user {current_user.username} "
                f"(role: {current_user.role}): {result.reason}"
            )
            raise PermissionDenied(detail=result.reason or "Permission denied")

        return current_user

    return permission_checker


def require_permission(
    resource: ResourceType | str,
    action: PermissionAction | str,
    resource_id_param: str | None = None,
    use_cache: bool = True,
):
    """
    Decorator for route handlers to require specific permissions.

    Usage:
        @router.post("/schedules")
        @require_permission(ResourceType.SCHEDULE, PermissionAction.CREATE)
        async def create_schedule(
            current_user: User = Depends(get_current_active_user),
            ...
        ):
            ...

        # With resource ID from path parameter
        @router.put("/schedules/{schedule_id}")
        @require_permission(
            ResourceType.SCHEDULE,
            PermissionAction.UPDATE,
            resource_id_param="schedule_id"
        )
        async def update_schedule(
            schedule_id: str,
            current_user: User = Depends(get_current_active_user),
            ...
        ):
            ...

    Args:
        resource: Resource type
        action: Action to perform
        resource_id_param: Name of parameter containing resource ID
        use_cache: Whether to use cache

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = str(kwargs[resource_id_param])

            # Check permission
            resolver = await get_permission_resolver()
            result = await resolver.check_permission(
                user=current_user,
                resource=resource,
                action=action,
                resource_id=resource_id,
                use_cache=use_cache,
            )

            if not result.allowed:
                logger.warning(
                    f"Permission denied for user {current_user.username} "
                    f"(role: {current_user.role}): {result.reason}"
                )
                raise PermissionDenied(detail=result.reason or "Permission denied")

            # Call the actual route handler
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(
    *permissions: tuple[ResourceType | str, PermissionAction | str],
    use_cache: bool = True,
):
    """
    Decorator to require any of the specified permissions.

    Usage:
        @router.get("/data")
        @require_any_permission(
            (ResourceType.SCHEDULE, PermissionAction.READ),
            (ResourceType.ANALYTICS, PermissionAction.VIEW_ANALYTICS),
        )
        async def get_data(current_user: User = Depends(get_current_active_user)):
            ...

    Args:
        *permissions: Variable number of (resource, action) tuples
        use_cache: Whether to use cache

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check if user has any of the permissions
            resolver = await get_permission_resolver()
            has_permission = await resolver.has_any_permission(
                user=current_user,
                permissions=list(permissions),
                use_cache=use_cache,
            )

            if not has_permission:
                perm_strs = [f"{r}:{a}" for r, a in permissions]
                logger.warning(
                    f"Permission denied for user {current_user.username} "
                    f"(role: {current_user.role}). Required any of: {perm_strs}"
                )
                raise PermissionDenied(
                    detail=f"Requires any of: {', '.join(perm_strs)}"
                )

            # Call the actual route handler
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(
    *permissions: tuple[ResourceType | str, PermissionAction | str],
    use_cache: bool = True,
):
    """
    Decorator to require all of the specified permissions.

    Usage:
        @router.post("/critical-operation")
        @require_all_permissions(
            (ResourceType.SCHEDULE, PermissionAction.CREATE),
            (ResourceType.ASSIGNMENT, PermissionAction.CREATE),
        )
        async def critical_operation(
            current_user: User = Depends(get_current_active_user)
        ):
            ...

    Args:
        *permissions: Variable number of (resource, action) tuples
        use_cache: Whether to use cache

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check if user has all of the permissions
            resolver = await get_permission_resolver()
            has_permissions = await resolver.has_all_permissions(
                user=current_user,
                permissions=list(permissions),
                use_cache=use_cache,
            )

            if not has_permissions:
                perm_strs = [f"{r}:{a}" for r, a in permissions]
                logger.warning(
                    f"Permission denied for user {current_user.username} "
                    f"(role: {current_user.role}). Required all of: {perm_strs}"
                )
                raise PermissionDenied(
                    detail=f"Requires all of: {', '.join(perm_strs)}"
                )

            # Call the actual route handler
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(roles: list[str] | str, allow_admin: bool = True):
    """
    Create a FastAPI dependency that checks user roles.

    Can be used in route dependencies for role-based access control.

    Usage:
        # As a route dependency
        @router.post(
            "/admin-only",
            dependencies=[Depends(require_role(["ADMIN"]))]
        )
        async def admin_only(...):
            ...

        # Or with multiple roles
        @router.post(
            "/staff-area",
            dependencies=[Depends(require_role(["COORDINATOR", "FACULTY"]))]
        )
        async def staff_area(...):
            ...

    Args:
        roles: List of allowed role names (or single role string)
        allow_admin: Whether to allow ADMIN role regardless (default: True)

    Returns:
        Dependency function that checks roles
    """
    # Normalize roles to a set
    if isinstance(roles, str):
        role_set = {roles.upper()}
    else:
        role_set = {r.upper() for r in roles}

    if allow_admin:
        role_set.add("ADMIN")

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if current user has required role."""
        user_role = current_user.role.upper() if current_user.role else ""

        if user_role not in role_set:
            logger.warning(
                f"Role check failed for user {current_user.username} "
                f"(role: {current_user.role}). Required: {role_set}"
            )
            raise PermissionDenied(
                detail=f"Requires role: {' or '.join(sorted(role_set))}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common permission checks
RequireScheduleRead = Depends(
    lambda: check_permission_dependency(ResourceType.SCHEDULE, PermissionAction.READ)
)
RequireScheduleCreate = Depends(
    lambda: check_permission_dependency(ResourceType.SCHEDULE, PermissionAction.CREATE)
)
RequireScheduleUpdate = Depends(
    lambda: check_permission_dependency(ResourceType.SCHEDULE, PermissionAction.UPDATE)
)
RequireScheduleDelete = Depends(
    lambda: check_permission_dependency(ResourceType.SCHEDULE, PermissionAction.DELETE)
)

RequireAssignmentRead = Depends(
    lambda: check_permission_dependency(ResourceType.ASSIGNMENT, PermissionAction.READ)
)
RequireAssignmentCreate = Depends(
    lambda: check_permission_dependency(
        ResourceType.ASSIGNMENT, PermissionAction.CREATE
    )
)

RequireUserManagement = Depends(
    lambda: check_permission_dependency(
        ResourceType.USER, PermissionAction.MANAGE_USERS
    )
)

RequireAnalytics = Depends(
    lambda: check_permission_dependency(
        ResourceType.ANALYTICS, PermissionAction.VIEW_ANALYTICS
    )
)

RequireResilienceView = Depends(
    lambda: check_permission_dependency(
        ResourceType.RESILIENCE, PermissionAction.VIEW_RESILIENCE
    )
)

RequireResilienceManage = Depends(
    lambda: check_permission_dependency(
        ResourceType.RESILIENCE, PermissionAction.MANAGE_RESILIENCE
    )
)
