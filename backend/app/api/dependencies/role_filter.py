"""FastAPI dependencies for role-based filtering.

Provides dependency injection functions that can be used in route handlers
to automatically filter data based on the current user's role.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from fastapi import Depends

from app.core.security import get_current_active_user
from app.models.user import User
from app.services.role_filter_service import ResourceType, RoleFilterService


def get_role_filter_service() -> type[RoleFilterService]:
    """Dependency to get RoleFilterService instance.

    Returns:
        RoleFilterService instance
    """
    return RoleFilterService


def require_resource_access(resource: ResourceType) -> Callable:
    """Dependency to require access to a specific resource type.

    Args:
        resource: The resource type to require access for

    Returns:
        Dependency function that checks access

    Example:
        @router.get("/schedules")
        def get_schedules(
            user: User = Depends(get_current_active_user),
            _: None = Depends(require_resource_access(ResourceType.SCHEDULES))
        ):
            # User has been verified to have access to schedules
            pass
    """

    def check_access(current_user: User = Depends(get_current_active_user)) -> None:
        """Check if user has access to the resource.

        Raises:
            HTTPException: If user doesn't have access
        """
        from fastapi import HTTPException, status

        if not RoleFilterService.can_access(resource, cast(str, current_user.role)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Your role '{current_user.role}' cannot access {resource.value}",
            )

    return check_access


def require_admin() -> Callable:
    """Dependency to require admin role.

    Returns:
        Dependency function that checks for admin role

    Example:
        @router.post("/users")
        def create_user(
            user: User = Depends(get_current_active_user),
            _: None = Depends(require_admin())
        ):
            # User has been verified to be admin
            pass
    """

    def check_admin(current_user: User = Depends(get_current_active_user)) -> None:
        """Check if user is admin.

        Raises:
            HTTPException: If user is not admin
        """
        from fastapi import HTTPException, status

        if not RoleFilterService.is_admin(cast(str, current_user.role)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Admin role required",
            )

    return check_admin


def apply_role_filter(
    data: dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Dependency to automatically filter response data based on user role.

    Args:
        data: Raw response data
        current_user: Current authenticated user

    Returns:
        Filtered data based on user's role

    Example:
        @router.get("/dashboard")
        def get_dashboard(
            current_user: User = Depends(get_current_active_user)
        ):
            # Build raw data
            data = {
                "schedules": [...],
                "compliance": [...],
                "users": [...]
            }
            # Apply filtering
            return RoleFilterService.filter_for_role(
                data,
                current_user.role,
                str(current_user.id)
            )
    """
    return RoleFilterService.filter_for_role(
        data, cast(str, current_user.role), str(current_user.id)
    )


def filter_response(filter_func: Callable | None = None) -> Callable:
    """Decorator to automatically filter route responses based on user role.

    This decorator wraps a route handler and filters its response data
    based on the current user's role.

    Args:
        filter_func: Optional custom filter function. If not provided,
                    uses RoleFilterService.filter_for_role

    Returns:
        Decorated function that filters responses

    Example:
        @router.get("/dashboard")
        @filter_response()
        async def get_dashboard(
            current_user: User = Depends(get_current_active_user)
        ):
            # Return raw data - will be filtered automatically
            return {
                "schedules": [...],
                "compliance": [...],
                "users": [...]
            }
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                # Try to find user in args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            # Call the original function
            result = await func(*args, **kwargs)

            # If result is a dict and we have a user, filter it
            if isinstance(result, dict) and current_user:
                if filter_func:
                    return filter_func(
                        result, cast(str, current_user.role), str(current_user.id)
                    )
                else:
                    return RoleFilterService.filter_for_role(
                        result, cast(str, current_user.role), str(current_user.id)
                    )

            return result

        return wrapper

    return decorator


def get_current_user_role(current_user: User = Depends(get_current_active_user)) -> str:
    """Dependency to get current user's role as string.

    Args:
        current_user: Current authenticated user

    Returns:
        User's role as string

    Example:
        @router.get("/my-permissions")
        def get_my_permissions(
            role: str = Depends(get_current_user_role)
        ):
            return {
                "role": role,
                "permissions": RoleFilterService.get_accessible_resources(role)
            }
    """
    return cast(str, current_user.role)


def check_endpoint_access(endpoint_category: str) -> Callable:
    """Dependency to check if user can access an endpoint category.

    Args:
        endpoint_category: The endpoint category to check

    Returns:
        Dependency function that validates access

    Example:
        @router.get("/compliance/report")
        def get_compliance_report(
            _: None = Depends(check_endpoint_access("compliance"))
        ):
            # User has been verified to have access to compliance endpoints
            pass
    """

    def check_access(current_user: User = Depends(get_current_active_user)) -> None:
        """Check if user can access the endpoint category.

        Raises:
            HTTPException: If user doesn't have access
        """
        from fastapi import HTTPException, status

        if not RoleFilterService.can_access_endpoint(
            cast(str, current_user.role), endpoint_category
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Your role '{current_user.role}' cannot access {endpoint_category} endpoints",
            )

    return check_access
