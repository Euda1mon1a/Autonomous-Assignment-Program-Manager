"""Permission resolver with role hierarchy and inheritance support."""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.permissions.cache import PermissionCache, get_permission_cache
from app.auth.permissions.models import (
    DEFAULT_ROLE_PERMISSIONS,
    ROLE_HIERARCHY,
    Permission,
    PermissionAction,
    PermissionCheckResult,
    ResourceType,
    UserRole,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class PermissionResolver:
    """
    Resolve permissions with role hierarchy and caching.

    Features:
    - Role hierarchy support (inheritance)
    - Redis caching for performance
    - Resource-level permission checks
    - Condition-based permissions
    """

    def __init__(self, cache: PermissionCache | None = None):
        """
        Initialize permission resolver.

        Args:
            cache: Optional PermissionCache instance
        """
        self._cache = cache

    async def get_cache(self) -> PermissionCache:
        """Get permission cache instance."""
        if self._cache is None:
            self._cache = await get_permission_cache()
        return self._cache

    def _resolve_role_hierarchy(self, role: UserRole) -> list[UserRole]:
        """
        Resolve role hierarchy to get all inherited roles.

        Args:
            role: User role

        Returns:
            List of roles including the role itself and all inherited roles
        """
        visited = set()
        roles = []

        def traverse(current_role: UserRole):
            if current_role in visited:
                return
            visited.add(current_role)
            roles.append(current_role)

            # Get parent roles
            parent_roles = ROLE_HIERARCHY.get(current_role, [])
            for parent in parent_roles:
                traverse(parent)

        traverse(role)
        return roles

    async def get_role_permissions(
        self,
        role: UserRole,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get all permissions for a role including inherited permissions.

        Args:
            role: User role
            use_cache: Whether to use cache (default: True)

        Returns:
            Set of permission strings
        """
        cache = await self.get_cache()

        # Try cache first
        if use_cache:
            cached = await cache.get_role_permissions(role)
            if cached is not None:
                logger.debug(f"Cache hit for role {role}")
                return cached

        # Compute permissions with hierarchy
        all_permissions = set()

        # Get all roles in hierarchy
        hierarchy = self._resolve_role_hierarchy(role)

        # Accumulate permissions from all roles
        for inherited_role in hierarchy:
            role_perms = DEFAULT_ROLE_PERMISSIONS.get(inherited_role, set())
            all_permissions.update(role_perms)

        # Cache the result
        if use_cache:
            await cache.set_role_permissions(role, all_permissions)

        logger.debug(
            f"Resolved {len(all_permissions)} permissions for role {role} "
            f"(hierarchy: {[r.value for r in hierarchy]})"
        )

        return all_permissions

    async def get_user_permissions(
        self,
        user: User,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get all permissions for a user.

        Args:
            user: User instance
            use_cache: Whether to use cache (default: True)

        Returns:
            Set of permission strings
        """
        cache = await self.get_cache()
        user_id = str(user.id)

        # Try cache first
        if use_cache:
            cached = await cache.get_user_permissions(user_id)
            if cached is not None:
                logger.debug(f"Cache hit for user {user_id}")
                return cached

        # Get permissions from role
        try:
            role = UserRole(user.role)
        except ValueError:
            logger.warning(f"Invalid role for user {user_id}: {user.role}")
            return set()

        permissions = await self.get_role_permissions(role, use_cache=use_cache)

        # Cache the result
        if use_cache:
            await cache.set_user_permissions(user_id, permissions)

        return permissions

    async def check_permission(
        self,
        user: User,
        resource: ResourceType | str,
        action: PermissionAction | str,
        resource_id: str | None = None,
        conditions: dict[str, Any] | None = None,
        use_cache: bool = True
    ) -> PermissionCheckResult:
        """
        Check if user has permission to perform action on resource.

        Args:
            user: User instance
            resource: Resource type
            action: Action to perform
            resource_id: Optional resource ID for resource-level checks
            conditions: Optional conditions for permission check
            use_cache: Whether to use cache (default: True)

        Returns:
            PermissionCheckResult with allowed status and reason
        """
        # Normalize inputs
        resource_str = resource.value if isinstance(resource, ResourceType) else resource
        action_str = action.value if isinstance(action, PermissionAction) else action

        permission_key = f"{resource_str}:{action_str}"

        # Get user permissions
        user_permissions = await self.get_user_permissions(user, use_cache=use_cache)

        # Check if user has the permission
        allowed = permission_key in user_permissions

        # Apply resource-level checks if needed
        if allowed and resource_id is not None:
            allowed = await self._check_resource_level_permission(
                user, resource_str, action_str, resource_id, conditions
            )

        # Build result
        reason = None
        if not allowed:
            if permission_key not in user_permissions:
                reason = f"User does not have permission: {permission_key}"
            else:
                reason = f"Resource-level permission denied for {resource_str}:{resource_id}"

        return PermissionCheckResult(
            allowed=allowed,
            reason=reason,
            cached=use_cache,
        )

    async def _check_resource_level_permission(
        self,
        user: User,
        resource_type: str,
        action: str,
        resource_id: str,
        conditions: dict[str, Any] | None = None
    ) -> bool:
        """
        Check resource-level permissions.

        This allows for fine-grained access control, e.g., users can only
        modify their own data unless they're admins.

        Args:
            user: User instance
            resource_type: Resource type
            action: Action to perform
            resource_id: Resource ID
            conditions: Optional conditions

        Returns:
            True if permission granted, False otherwise
        """
        # Admin always has access
        if user.is_admin:
            return True

        # Resource-specific checks
        if resource_type == ResourceType.USER.value:
            # Users can only modify their own account unless they're admin
            if action in ["update", "delete"]:
                return str(user.id) == resource_id

        if resource_type == ResourceType.ASSIGNMENT.value:
            # Faculty and residents can view their own assignments
            # but only coordinators can modify them
            if action == "read":
                return True  # Already have read permission
            return user.can_manage_schedules

        if resource_type == ResourceType.SWAP.value:
            # Users can create swaps for their own assignments
            # Coordinators can approve any swap
            if action == "request_swap":
                return True  # Can request swaps for own assignments
            if action == "approve_swap":
                return user.can_manage_schedules

        if resource_type == ResourceType.ABSENCE.value:
            # Users can request leave for themselves
            # Coordinators can approve leave requests
            if action == "request_leave":
                return True
            if action == "approve_leave":
                return user.can_manage_schedules

        # Default: allow if base permission exists
        return True

    async def has_permission(
        self,
        user: User,
        resource: ResourceType | str,
        action: PermissionAction | str,
        resource_id: str | None = None,
        use_cache: bool = True
    ) -> bool:
        """
        Simplified permission check that returns boolean.

        Args:
            user: User instance
            resource: Resource type
            action: Action to perform
            resource_id: Optional resource ID
            use_cache: Whether to use cache

        Returns:
            True if permission granted, False otherwise
        """
        result = await self.check_permission(
            user, resource, action, resource_id, use_cache=use_cache
        )
        return result.allowed

    async def has_any_permission(
        self,
        user: User,
        permissions: list[tuple[ResourceType | str, PermissionAction | str]],
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            user: User instance
            permissions: List of (resource, action) tuples
            use_cache: Whether to use cache

        Returns:
            True if user has at least one permission, False otherwise
        """
        for resource, action in permissions:
            if await self.has_permission(user, resource, action, use_cache=use_cache):
                return True
        return False

    async def has_all_permissions(
        self,
        user: User,
        permissions: list[tuple[ResourceType | str, PermissionAction | str]],
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has all of the specified permissions.

        Args:
            user: User instance
            permissions: List of (resource, action) tuples
            use_cache: Whether to use cache

        Returns:
            True if user has all permissions, False otherwise
        """
        for resource, action in permissions:
            if not await self.has_permission(user, resource, action, use_cache=use_cache):
                return False
        return True

    async def get_permissions_summary(self, user: User) -> dict[str, Any]:
        """
        Get a summary of user's permissions for debugging/display.

        Args:
            user: User instance

        Returns:
            Dictionary with permissions summary
        """
        permissions = await self.get_user_permissions(user)

        # Group permissions by resource type
        by_resource: dict[str, list[str]] = {}
        for perm in permissions:
            if ":" in perm:
                resource, action = perm.split(":", 1)
                if resource not in by_resource:
                    by_resource[resource] = []
                by_resource[resource].append(action)

        # Get role hierarchy
        try:
            role = UserRole(user.role)
            hierarchy = self._resolve_role_hierarchy(role)
        except ValueError:
            role = None
            hierarchy = []

        return {
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role,
            "role_hierarchy": [r.value for r in hierarchy],
            "total_permissions": len(permissions),
            "permissions_by_resource": by_resource,
            "is_admin": user.is_admin,
            "is_coordinator": user.is_coordinator,
            "can_manage_schedules": user.can_manage_schedules,
        }


# Global resolver instance (singleton pattern)
_resolver_instance: PermissionResolver | None = None


async def get_permission_resolver() -> PermissionResolver:
    """
    Get global permission resolver instance.

    Returns:
        PermissionResolver instance
    """
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = PermissionResolver()
    return _resolver_instance
