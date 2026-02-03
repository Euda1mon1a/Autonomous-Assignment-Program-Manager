"""
Access Control Matrix for Role-Based Access Control (RBAC).

This module provides a comprehensive access control matrix that defines:
- Role-permission mappings
- Resource-action relationships
- Hierarchical role support
- Context-aware permissions
- Permission inheritance
- Audit logging for permission changes

Usage:
    from app.auth.access_matrix import AccessControlMatrix, require_permission

    # Check permissions
    acm = AccessControlMatrix()
    if acm.has_permission(user_role, "schedule", "create"):
        # Perform action
        pass

    # Use as decorator
    @require_permission("schedule", "update")
    async def update_schedule():
        pass
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, cast
from uuid import UUID, uuid4

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.security import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================================
# Enums and Constants
# ============================================================================


class UserRole(str, Enum):
    """
    User roles with hierarchical structure.

    Hierarchy (highest to lowest):
    - ADMIN: Full system access
    - COORDINATOR: Schedule management
    - FACULTY: Limited management + view
    - CLINICAL_STAFF: Clinical view access (parent of RN, LPN, MSA)
    - RN: Registered Nurse
    - LPN: Licensed Practical Nurse
    - MSA: Medical Support Assistant
    - RESIDENT: Basic view + self-management
    """

    ADMIN = "admin"
    COORDINATOR = "coordinator"
    FACULTY = "faculty"
    CLINICAL_STAFF = "clinical_staff"
    RN = "rn"
    LPN = "lpn"
    MSA = "msa"
    RESIDENT = "resident"


class ResourceType(str, Enum):
    """Resource types in the system."""

    # Core scheduling resources
    SCHEDULE = "schedule"
    ASSIGNMENT = "assignment"
    BLOCK = "block"
    ROTATION = "rotation"

    # People management
    PERSON = "person"
    RESIDENT = "resident"
    FACULTY_MEMBER = "faculty_member"

    # Leave and absence
    ABSENCE = "absence"
    LEAVE = "leave"

    # Swap system
    SWAP = "swap"
    SWAP_REQUEST = "swap_request"

    # Procedures and credentials
    PROCEDURE = "procedure"
    CREDENTIAL = "credential"
    CERTIFICATION = "certification"

    # Conflict management
    CONFLICT = "conflict"
    CONFLICT_ALERT = "conflict_alert"

    # System administration
    USER = "user"
    SETTINGS = "settings"
    FEATURE_FLAG = "feature_flag"

    # Analytics and reporting
    REPORT = "report"
    ANALYTICS = "analytics"
    AUDIT_LOG = "audit_log"

    # Notifications
    NOTIFICATION = "notification"
    EMAIL_TEMPLATE = "email_template"

    # Resilience
    RESILIENCE_METRIC = "resilience_metric"
    CONTINGENCY_PLAN = "contingency_plan"


class PermissionAction(str, Enum):
    """Permission actions that can be performed on resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    APPROVE = "approve"
    REJECT = "reject"
    EXECUTE = "execute"
    EXPORT = "export"
    IMPORT = "import"
    MANAGE = "manage"  # All CRUD operations


class PermissionContext(BaseModel):
    """
    Context for evaluating permissions.

    Allows for context-aware permission checks (e.g., "own" resources).
    """

    user_id: UUID
    user_role: UserRole
    resource_owner_id: UUID | None = None
    resource_metadata: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PermissionAuditEntry(BaseModel):
    """Audit entry for permission changes."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str  # "granted", "revoked", "checked", "denied"
    role: UserRole
    resource: ResourceType
    permission: PermissionAction
    user_id: UUID | None = None
    context: dict[str, Any] | None = None
    result: bool
    reason: str | None = None

    # ============================================================================
    # Role Hierarchy
    # ============================================================================


class RoleHierarchy:
    """
    Manages hierarchical role relationships and inheritance.

    Higher roles inherit all permissions from lower roles.

    Role Hierarchy (highest to lowest privilege):
    1. ADMIN (100) - Full system access
    2. COORDINATOR (90) - Schedule management, no inheritance
    3. FACULTY (80) - Limited management, INDEPENDENT (no inheritance)
    4. RESIDENT (70) - Basic view + self-management, INDEPENDENT
    5. CLINICAL_STAFF (60) - Clinical view access, INDEPENDENT
    6. RN (50) - Inherits from CLINICAL_STAFF
    7. LPN (40) - Inherits from CLINICAL_STAFF
    8. MSA (30) - Inherits from CLINICAL_STAFF
    """

    # Role level constants for comparison
    ROLE_LEVELS: dict[UserRole, int] = {
        UserRole.ADMIN: 100,
        UserRole.COORDINATOR: 90,
        UserRole.FACULTY: 80,
        UserRole.RESIDENT: 70,
        UserRole.CLINICAL_STAFF: 60,
        UserRole.RN: 50,
        UserRole.LPN: 40,
        UserRole.MSA: 30,
    }

    # Role hierarchy map (role -> parent roles)
    # SECURITY FIX: Faculty does NOT inherit from Coordinator
    HIERARCHY: dict[UserRole, set[UserRole]] = {
        UserRole.ADMIN: set(),  # Top level, no parents
        UserRole.COORDINATOR: set(),  # No inheritance
        UserRole.FACULTY: set(),  # INDEPENDENT - no inheritance
        UserRole.CLINICAL_STAFF: set(),  # INDEPENDENT - no inheritance
        UserRole.RN: {UserRole.CLINICAL_STAFF},  # Inherits from clinical_staff
        UserRole.LPN: {UserRole.CLINICAL_STAFF},  # Inherits from clinical_staff
        UserRole.MSA: {UserRole.CLINICAL_STAFF},  # Inherits from clinical_staff
        UserRole.RESIDENT: set(),  # INDEPENDENT - no inheritance
    }

    @classmethod
    def get_inherited_roles(cls, role: UserRole) -> set[UserRole]:
        """
        Get all roles that the given role inherits from.

        Args:
            role: The role to check

        Returns:
            Set of roles that have higher or equal privileges
        """
        inherited = {role}
        if role in cls.HIERARCHY:
            inherited.update(cls.HIERARCHY[role])
        return inherited

    @classmethod
    def is_higher_role(cls, role: UserRole, compared_to: UserRole) -> bool:
        """
        Check if one role is higher in hierarchy than another.

        Args:
            role: Role to check
            compared_to: Role to compare against

        Returns:
            True if role is higher than compared_to

        Note:
            Uses role levels for comparison. Higher numeric level = higher privilege.
        """
        role_level = cls.ROLE_LEVELS.get(role, 0)
        compared_level = cls.ROLE_LEVELS.get(compared_to, 0)
        return role_level > compared_level

    @classmethod
    def get_role_level(cls, role: UserRole) -> int:
        """
        Get the numeric privilege level for a role.

        Args:
            role: Role to check

        Returns:
            Numeric privilege level (higher = more privileged)
        """
        return cls.ROLE_LEVELS.get(role, 0)

    @classmethod
    def is_equal_or_higher_role(cls, role: UserRole, compared_to: UserRole) -> bool:
        """
        Check if role has equal or higher privilege than compared_to.

        Args:
            role: Role to check
            compared_to: Role to compare against

        Returns:
            True if role >= compared_to in privilege level
        """
        return cls.get_role_level(role) >= cls.get_role_level(compared_to)

    @classmethod
    def can_manage_role(cls, manager_role: UserRole, target_role: UserRole) -> bool:
        """
        Check if a manager role can manage a target role.

        Only admins can manage coordinators.
        Coordinators can manage faculty and below.

        Args:
            manager_role: Role attempting management
            target_role: Role being managed

        Returns:
            True if management is allowed
        """
        # Admin can manage all roles
        if manager_role == UserRole.ADMIN:
            return True

            # Coordinator can manage all except Admin and Coordinator
        if manager_role == UserRole.COORDINATOR:
            return target_role not in {UserRole.ADMIN, UserRole.COORDINATOR}

            # All other roles cannot manage others
        return False

        # ============================================================================
        # Access Control Matrix
        # ============================================================================


class AccessControlMatrix:
    """
    Central access control matrix for RBAC.

    Defines all role-resource-action permissions with support for:
    - Static permissions (defined in matrix)
    - Dynamic permissions (evaluated at runtime)
    - Context-aware permissions (e.g., "own" resources)
    - Permission inheritance through role hierarchy
    - Audit logging of permission checks
    """

    # Core permission matrix: {role: {resource: {actions}}}
    PERMISSION_MATRIX: dict[UserRole, dict[ResourceType, set[PermissionAction]]] = {
        # ADMIN: Full access to everything
        UserRole.ADMIN: {
            resource: {action for action in PermissionAction}
            for resource in ResourceType
        },
        # COORDINATOR: Schedule management and oversight
        UserRole.COORDINATOR: {
            ResourceType.SCHEDULE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
                PermissionAction.EXPORT,
                PermissionAction.IMPORT,
                PermissionAction.EXECUTE,
            },
            ResourceType.ASSIGNMENT: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
                PermissionAction.MANAGE,
            },
            ResourceType.BLOCK: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
            },
            ResourceType.ROTATION: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
            },
            ResourceType.PERSON: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
            },
            ResourceType.RESIDENT: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
            },
            ResourceType.FACULTY_MEMBER: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
            },
            ResourceType.ABSENCE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
            },
            ResourceType.LEAVE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
            },
            ResourceType.SWAP: {
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
                PermissionAction.EXECUTE,
            },
            ResourceType.SWAP_REQUEST: {
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
            },
            ResourceType.CONFLICT: {
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.MANAGE,
            },
            ResourceType.CONFLICT_ALERT: {
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.MANAGE,
            },
            ResourceType.REPORT: {
                PermissionAction.READ,
                PermissionAction.LIST,
                PermissionAction.EXPORT,
            },
            ResourceType.ANALYTICS: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.LIST,
            },
            ResourceType.RESILIENCE_METRIC: {
                PermissionAction.READ,
                PermissionAction.LIST,
            },
            ResourceType.CONTINGENCY_PLAN: {
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
            },
        },
        # FACULTY: View schedules, manage own availability and swaps
        UserRole.FACULTY: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ},  # Own profile
            ResourceType.ABSENCE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
            },
            ResourceType.LEAVE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
            },
            ResourceType.SWAP: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
            },
            ResourceType.SWAP_REQUEST: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
            },
            ResourceType.PROCEDURE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.CREDENTIAL: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.CERTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
        # CLINICAL_STAFF: View access to schedules and manifests
        UserRole.CLINICAL_STAFF: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
        # RN, LPN, MSA: Same as CLINICAL_STAFF (inherit via hierarchy)
        UserRole.RN: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
        UserRole.LPN: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
        UserRole.MSA: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
        # RESIDENT: View own schedule, manage own swaps
        UserRole.RESIDENT: {
            ResourceType.SCHEDULE: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ASSIGNMENT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.BLOCK: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.ROTATION: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.PERSON: {PermissionAction.READ},  # Own profile
            ResourceType.ABSENCE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
            },
            ResourceType.LEAVE: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
            },
            ResourceType.SWAP: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
            },
            ResourceType.SWAP_REQUEST: {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.LIST,
                PermissionAction.APPROVE,
                PermissionAction.REJECT,
            },
            ResourceType.CONFLICT: {PermissionAction.READ, PermissionAction.LIST},
            ResourceType.NOTIFICATION: {PermissionAction.READ, PermissionAction.LIST},
        },
    }

    def __init__(self, enable_audit: bool = True) -> None:
        """
        Initialize the Access Control Matrix.

        Args:
            enable_audit: Whether to enable audit logging
        """
        self.enable_audit = enable_audit
        self.audit_log: list[PermissionAuditEntry] = []
        self._context_evaluators: dict[str, Callable] = {}
        self._register_default_context_evaluators()

    def _register_default_context_evaluators(self) -> None:
        """Register default context-aware permission evaluators."""

        def is_own_resource(context: PermissionContext) -> bool:
            """Check if user is accessing their own resource."""
            return (
                context.resource_owner_id is not None
                and context.user_id == context.resource_owner_id
            )

        def is_supervisor(context: PermissionContext) -> bool:
            """Check if user is a supervisor of the resource owner."""
            # This would typically check database relationships
            # For now, coordinators and admins are supervisors
            return context.user_role in {UserRole.ADMIN, UserRole.COORDINATOR}

        self._context_evaluators["is_own_resource"] = is_own_resource
        self._context_evaluators["is_supervisor"] = is_supervisor

    def has_permission(
        self,
        role: UserRole | str,
        resource: ResourceType | str,
        action: PermissionAction | str,
        context: PermissionContext | None = None,
    ) -> bool:
        """
        Check if a role has permission to perform an action on a resource.

        Args:
            role: User role
            resource: Resource type
            action: Permission action
            context: Optional context for dynamic permission evaluation

        Returns:
            True if permission is granted, False otherwise
        """
        # Convert strings to enums
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                logger.warning(f"Invalid role: {role}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid role"
                )
                return False

        if isinstance(resource, str):
            try:
                resource = ResourceType(resource)
            except ValueError:
                logger.warning(f"Invalid resource: {resource}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid resource"
                )
                return False

        if isinstance(action, str):
            try:
                action = PermissionAction(action)
            except ValueError:
                logger.warning(f"Invalid action: {action}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid action"
                )
                return False

        # Check static permissions in matrix
        has_static_permission = self._check_static_permission(role, resource, action)

        # Check inherited permissions from role hierarchy
        if not has_static_permission:
            inherited_roles = RoleHierarchy.get_inherited_roles(role)
            for inherited_role in inherited_roles:
                if self._check_static_permission(inherited_role, resource, action):
                    has_static_permission = True
                    break

        if has_static_permission:
            if context:
                has_permission = self._check_context_permission(
                    role, resource, action, context
                )
            else:
                # Strict guard: self-service updates/deletes require context.
                if role in {UserRole.RESIDENT, UserRole.FACULTY} and action in {
                    PermissionAction.UPDATE,
                    PermissionAction.DELETE,
                }:
                    if resource in {
                        ResourceType.ABSENCE,
                        ResourceType.LEAVE,
                        ResourceType.SWAP_REQUEST,
                        ResourceType.PERSON,
                    }:
                        has_permission = False
                    else:
                        has_permission = True
                else:
                    has_permission = True
        else:
            has_permission = False

            # Audit the permission check
        self._audit_permission_check(
            role,
            resource,
            action,
            has_permission,
            context=context.model_dump() if context else None,
        )

        return has_permission

    def _check_static_permission(
        self,
        role: UserRole,
        resource: ResourceType,
        action: PermissionAction,
    ) -> bool:
        """Check static permission in matrix."""
        role_permissions = self.PERMISSION_MATRIX.get(role, {})
        resource_permissions = role_permissions.get(resource, set())

        # MANAGE action includes all CRUD operations
        if (
            action
            in {
                PermissionAction.CREATE,
                PermissionAction.READ,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
            }
            and PermissionAction.MANAGE in resource_permissions
        ):
            return True

        return action in resource_permissions

    def _check_context_permission(
        self,
        role: UserRole,
        resource: ResourceType,
        action: PermissionAction,
        context: PermissionContext,
    ) -> bool:
        """
        Apply context-aware permission checks.

        For example:
        - Residents can only update their own absence requests
        - Faculty can approve swaps involving them
        - APPROVE/REJECT actions require resource context validation
        """
        # SECURITY: APPROVE/REJECT actions require context validation
        if action in {PermissionAction.APPROVE, PermissionAction.REJECT}:
            if not self._validate_approval_context(role, resource, action, context):
                return False

                # Own resource rule: Users with limited permissions can modify their own resources
        if role in {UserRole.RESIDENT, UserRole.FACULTY}:
            if action in {PermissionAction.UPDATE, PermissionAction.DELETE}:
                if resource in {
                    ResourceType.ABSENCE,
                    ResourceType.LEAVE,
                    ResourceType.SWAP_REQUEST,
                    ResourceType.PERSON,
                }:
                    # Must be their own resource
                    return cast(
                        bool, self._context_evaluators["is_own_resource"](context)
                    )

        return True  # No additional context restrictions

    def _flatten_permissions(
        self, permissions: dict[ResourceType, set[PermissionAction]]
    ) -> set[str]:
        """Convert permission map to a set of resource:action strings."""
        flattened: set[str] = set()
        for resource, actions in permissions.items():
            for action in actions:
                flattened.add(f"{resource.value}:{action.value}")
        return flattened

    def _check_permission_set(
        self,
        permissions: set[str],
        resource: ResourceType,
        action: PermissionAction,
    ) -> bool:
        """Check if permission set allows an action on a resource."""
        key = f"{resource.value}:{action.value}"
        if key in permissions:
            return True
        if action in {
            PermissionAction.CREATE,
            PermissionAction.READ,
            PermissionAction.UPDATE,
            PermissionAction.DELETE,
        }:
            manage_key = f"{resource.value}:{PermissionAction.MANAGE.value}"
            return manage_key in permissions
        return False

    async def _get_role_permission_set(
        self, role: UserRole, use_cache: bool = True
    ) -> set[str]:
        """Get flattened permissions for a role, optionally cached."""
        if not use_cache:
            return self._flatten_permissions(self.get_role_permissions(role))

        try:
            cache = await get_permission_cache()
            cached = await cache.get_role_permissions(role)
            if cached is not None:
                return cached

            permissions = self._flatten_permissions(self.get_role_permissions(role))
            await cache.set_role_permissions(role, permissions)
            return permissions
        except Exception as exc:  # noqa: BLE001 - cache should never block auth
            logger.warning(f"Permission cache unavailable, falling back: {exc}")
            return self._flatten_permissions(self.get_role_permissions(role))

    async def has_permission_async(
        self,
        role: UserRole | str,
        resource: ResourceType | str,
        action: PermissionAction | str,
        context: PermissionContext | None = None,
        use_cache: bool = True,
    ) -> bool:
        """
        Async permission check with optional Redis caching.

        Args:
            role: User role
            resource: Resource type
            action: Permission action
            context: Optional context for dynamic evaluation
            use_cache: Whether to use Redis cache for role permissions

        Returns:
            True if permission is granted, False otherwise
        """
        # Convert strings to enums
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                logger.warning(f"Invalid role: {role}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid role"
                )
                return False

        if isinstance(resource, str):
            try:
                resource = ResourceType(resource)
            except ValueError:
                logger.warning(f"Invalid resource: {resource}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid resource"
                )
                return False

        if isinstance(action, str):
            try:
                action = PermissionAction(action)
            except ValueError:
                logger.warning(f"Invalid action: {action}")
                self._audit_permission_check(
                    role, resource, action, False, "Invalid action"
                )
                return False

        permissions = await self._get_role_permission_set(role, use_cache=use_cache)
        has_static_permission = self._check_permission_set(
            permissions, resource, action
        )

        if has_static_permission:
            if context:
                has_permission = self._check_context_permission(
                    role, resource, action, context
                )
            else:
                # Strict guard: self-service updates/deletes require context.
                if role in {UserRole.RESIDENT, UserRole.FACULTY} and action in {
                    PermissionAction.UPDATE,
                    PermissionAction.DELETE,
                }:
                    if resource in {
                        ResourceType.ABSENCE,
                        ResourceType.LEAVE,
                        ResourceType.SWAP_REQUEST,
                        ResourceType.PERSON,
                    }:
                        has_permission = False
                    else:
                        has_permission = True
                else:
                    has_permission = True
        else:
            has_permission = False

        # Audit the permission check
        self._audit_permission_check(
            role,
            resource,
            action,
            has_permission,
            context=context.model_dump() if context else None,
        )

        return has_permission

    def _validate_approval_context(
        self,
        role: UserRole,
        resource: ResourceType,
        action: PermissionAction,
        context: PermissionContext,
    ) -> bool:
        """
        Validate context for APPROVE/REJECT actions.

        SECURITY REQUIREMENT: All approvals must have proper context.

        Args:
            role: User role performing action
            resource: Resource being approved/rejected
            action: APPROVE or REJECT
            context: Permission context with resource metadata

        Returns:
            True if approval context is valid, False otherwise
        """
        # Admin can approve anything
        if role == UserRole.ADMIN:
            return True

            # Validate resource owner is set for approvals
        if context.resource_owner_id is None:
            logger.warning(
                f"APPROVAL DENIED: No resource_owner_id for {action} on {resource}"
            )
            return False

            # Validate resource metadata exists
        if not context.resource_metadata:
            logger.warning(
                f"APPROVAL DENIED: No resource_metadata for {action} on {resource}"
            )
            return False

            # Resource-specific validation
        if resource in {ResourceType.ABSENCE, ResourceType.LEAVE}:
            # Must specify department/unit for leave approvals
            if "department" not in context.resource_metadata:
                logger.warning(
                    f"APPROVAL DENIED: No department in metadata for {resource}"
                )
                return False

        if resource in {ResourceType.SWAP, ResourceType.SWAP_REQUEST}:
            # Must specify both parties involved in swap
            required_keys = {"requesting_user_id", "target_user_id"}
            if not required_keys.issubset(context.resource_metadata.keys()):
                logger.warning(
                    f"APPROVAL DENIED: Missing swap parties in metadata. "
                    f"Required: {required_keys}, "
                    f"Got: {set(context.resource_metadata.keys())}"
                )
                return False

                # Coordinator role check for swap approvals
            if role != UserRole.COORDINATOR:
                # Faculty can only approve swaps they're involved in
                if role == UserRole.FACULTY:
                    user_id = str(context.user_id)
                    involved = {
                        str(context.resource_metadata.get("requesting_user_id")),
                        str(context.resource_metadata.get("target_user_id")),
                    }
                    if user_id not in involved:
                        logger.warning(
                            f"APPROVAL DENIED: Faculty {user_id} not involved in swap"
                        )
                        return False

                        # Check supervisor relationship for non-admin approvals
        if role == UserRole.COORDINATOR:
            # Coordinators must be supervisor of the resource owner
            if not self._context_evaluators["is_supervisor"](context):
                logger.warning(
                    "APPROVAL DENIED: Coordinator not supervisor of resource owner"
                )
                return False

        return True

    def _audit_permission_check(
        self,
        role: UserRole | str,
        resource: ResourceType | str,
        action: PermissionAction | str,
        result: bool,
        reason: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Audit a permission check."""
        if not self.enable_audit:
            return

        try:
            role_value = role if isinstance(role, UserRole) else UserRole(role)
            resource_value = (
                resource
                if isinstance(resource, ResourceType)
                else ResourceType(resource)
            )
            action_value = (
                action
                if isinstance(action, PermissionAction)
                else PermissionAction(action)
            )
        except ValueError as exc:
            logger.warning(f"Skipping audit for invalid permission check: {exc}")
            return

        entry = PermissionAuditEntry(
            action="checked",
            role=role_value,
            resource=resource_value,
            permission=action_value,
            result=result,
            reason=reason,
            context=context,
        )

        self.audit_log.append(entry)
        logger.info(
            f"Permission check: role={role}, resource={resource}, "
            f"action={action}, result={result}"
        )

    def get_role_permissions(
        self, role: UserRole | str
    ) -> dict[ResourceType, set[PermissionAction]]:
        """
        Get all permissions for a role, including inherited permissions.

        Args:
            role: User role

        Returns:
            Dictionary of resource -> actions
        """
        if isinstance(role, str):
            role = UserRole(role)

            # Start with direct permissions
        permissions = {}
        if role in self.PERMISSION_MATRIX:
            for resource, actions in self.PERMISSION_MATRIX[role].items():
                permissions[resource] = actions.copy()

                # Add inherited permissions
        inherited_roles = RoleHierarchy.get_inherited_roles(role)
        for inherited_role in inherited_roles:
            if inherited_role == role:
                continue
            if inherited_role in self.PERMISSION_MATRIX:
                for resource, actions in self.PERMISSION_MATRIX[inherited_role].items():
                    if resource not in permissions:
                        permissions[resource] = set()
                    permissions[resource].update(actions)

        return permissions

    def get_resource_permissions(
        self, resource: ResourceType | str
    ) -> dict[UserRole, set[PermissionAction]]:
        """
        Get all role permissions for a specific resource.

        Args:
            resource: Resource type

        Returns:
            Dictionary of role -> actions
        """
        if isinstance(resource, str):
            resource = ResourceType(resource)

        result = {}
        for role in UserRole:
            permissions = self.get_role_permissions(role)
            if resource in permissions:
                result[role] = permissions[resource]

        return result

    def export_matrix(self, format: str = "json") -> str:
        """
        Export the access control matrix for visualization.

        Args:
            format: Export format ("json", "csv", "markdown")

        Returns:
            Formatted string representation of the matrix
        """
        if format == "json":
            return self._export_json()
        elif format == "csv":
            return self._export_csv()
        elif format == "markdown":
            return self._export_markdown()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self) -> str:
        """Export matrix as JSON."""
        matrix = {}
        for role in UserRole:
            role_perms = self.get_role_permissions(role)
            matrix[role.value] = {
                resource.value: [action.value for action in actions]
                for resource, actions in role_perms.items()
            }
        return json.dumps(matrix, indent=2)

    def _export_csv(self) -> str:
        """Export matrix as CSV."""
        lines = ["Role,Resource,Actions"]
        for role in UserRole:
            role_perms = self.get_role_permissions(role)
            for resource, actions in sorted(
                role_perms.items(), key=lambda x: x[0].value
            ):
                action_str = ";".join(sorted(a.value for a in actions))
                lines.append(f"{role.value},{resource.value},{action_str}")
        return "\n".join(lines)

    def _export_markdown(self) -> str:
        """Export matrix as Markdown table."""
        lines = [
            "# Access Control Matrix",
            "",
            "## Role Permissions",
            "",
        ]

        for role in UserRole:
            lines.append(f"### {role.value.upper()}")
            lines.append("")
            lines.append("| Resource | Actions |")
            lines.append("|----------|---------|")

            role_perms = self.get_role_permissions(role)
            for resource, actions in sorted(
                role_perms.items(), key=lambda x: x[0].value
            ):
                action_str = ", ".join(sorted(a.value for a in actions))
                lines.append(f"| {resource.value} | {action_str} |")

            lines.append("")

        return "\n".join(lines)

    def get_audit_log(
        self,
        limit: int | None = None,
        role: UserRole | None = None,
        resource: ResourceType | None = None,
    ) -> list[PermissionAuditEntry]:
        """
        Get audit log entries with optional filtering.

        Args:
            limit: Maximum number of entries to return
            role: Filter by role
            resource: Filter by resource

        Returns:
            List of audit entries
        """
        entries = self.audit_log

        if role:
            entries = [e for e in entries if e.role == role]
        if resource:
            entries = [e for e in entries if e.resource == resource]

        if limit:
            entries = entries[-limit:]

        return entries

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self.audit_log.clear()

        # ============================================================================
        # Global Instance and Helpers
        # ============================================================================

# ============================================================================
# Permission Cache (Redis-backed)
# ============================================================================


class PermissionCache:
    """
    Redis-based cache for role permissions.

    Features:
    - TTL-based invalidation
    - Cache warming on startup
    - Graceful degradation if Redis unavailable
    """

    ROLE_PERMISSIONS_PREFIX = "perm:role"
    USER_PERMISSIONS_PREFIX = "perm:user"
    RESOURCE_PERMISSIONS_PREFIX = "perm:resource"

    DEFAULT_TTL = 3600  # 1 hour
    ROLE_TTL = 86400  # 24 hours
    USER_TTL = 3600  # 1 hour

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._redis = redis_client
        self._fallback_mode = False

    async def get_redis_client(self) -> aioredis.Redis | None:
        if self._redis is not None:
            return self._redis

        try:
            self._redis = aioredis.from_url(
                settings.redis_url_with_password,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self._redis.ping()
            self._fallback_mode = False
            logger.info("Permission cache connected to Redis")
            return self._redis
        except (RedisError, OSError) as e:
            logger.warning(f"Failed to connect to Redis for permission cache: {e}")
            self._fallback_mode = True
            self._redis = None
            return None

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    def _make_role_key(self, role: UserRole | str) -> str:
        role_str = role.value if isinstance(role, UserRole) else role
        return f"{self.ROLE_PERMISSIONS_PREFIX}:{role_str}"

    def _make_user_key(self, user_id: str) -> str:
        return f"{self.USER_PERMISSIONS_PREFIX}:{user_id}"

    def _make_resource_key(self, resource_type: str, resource_id: str) -> str:
        return f"{self.RESOURCE_PERMISSIONS_PREFIX}:{resource_type}:{resource_id}"

    async def get_role_permissions(self, role: UserRole | str) -> set[str] | None:
        redis = await self.get_redis_client()
        if redis is None:
            return None

        try:
            key = self._make_role_key(role)
            data = await redis.get(key)
            if data is None:
                return None
            permissions = json.loads(data)
            return set(permissions)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to get role permissions from cache: {e}")
            return None

    async def set_role_permissions(
        self, role: UserRole | str, permissions: set[str], ttl: int | None = None
    ) -> bool:
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_role_key(role)
            data = json.dumps(list(permissions))
            ttl = ttl or self.ROLE_TTL
            await redis.setex(key, ttl, data)
            logger.debug(f"Cached permissions for role {role} (TTL: {ttl}s)")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to cache role permissions: {e}")
            return False

    async def get_user_permissions(self, user_id: str) -> set[str] | None:
        redis = await self.get_redis_client()
        if redis is None:
            return None

        try:
            key = self._make_user_key(user_id)
            data = await redis.get(key)
            if data is None:
                return None
            permissions = json.loads(data)
            return set(permissions)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to get user permissions from cache: {e}")
            return None

    async def set_user_permissions(
        self, user_id: str, permissions: set[str], ttl: int | None = None
    ) -> bool:
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_user_key(user_id)
            data = json.dumps(list(permissions))
            ttl = ttl or self.USER_TTL
            await redis.setex(key, ttl, data)
            logger.debug(f"Cached permissions for user {user_id} (TTL: {ttl}s)")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to cache user permissions: {e}")
            return False

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_user_key(user_id)
            await redis.delete(key)
            logger.debug(f"Invalidated permissions cache for user {user_id}")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate user permissions: {e}")
            return False

    async def invalidate_role_permissions(self, role: UserRole | str) -> bool:
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_role_key(role)
            await redis.delete(key)
            logger.debug(f"Invalidated permissions cache for role {role}")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate role permissions: {e}")
            return False

    async def invalidate_all_permissions(self) -> bool:
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            patterns = [
                f"{self.ROLE_PERMISSIONS_PREFIX}:*",
                f"{self.USER_PERMISSIONS_PREFIX}:*",
                f"{self.RESOURCE_PERMISSIONS_PREFIX}:*",
            ]

            deleted_count = 0
            for pattern in patterns:
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        deleted_count += await redis.delete(*keys)
                    if cursor == 0:
                        break

            logger.info(f"Invalidated {deleted_count} permission cache entries")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate all permissions: {e}")
            return False

    async def warm_cache(self, permissions_map: dict[UserRole, set[str]]) -> int:
        if self._fallback_mode:
            logger.info("Skipping cache warming in fallback mode")
            return 0

        cached_count = 0
        for role, permissions in permissions_map.items():
            if await self.set_role_permissions(role, permissions):
                cached_count += 1

        logger.info(
            f"Cache warming completed: {cached_count}/{len(permissions_map)} roles cached"
        )
        return cached_count

    async def get_cache_stats(self) -> dict[str, Any]:
        redis = await self.get_redis_client()
        if redis is None:
            return {
                "status": "unavailable",
                "fallback_mode": True,
            }

        try:
            info = await redis.info("stats")

            role_count = 0
            user_count = 0
            resource_count = 0

            for pattern, counter in [
                (f"{self.ROLE_PERMISSIONS_PREFIX}:*", "role_count"),
                (f"{self.USER_PERMISSIONS_PREFIX}:*", "user_count"),
                (f"{self.RESOURCE_PERMISSIONS_PREFIX}:*", "resource_count"),
            ]:
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    count += len(keys)
                    if cursor == 0:
                        break

                if counter == "role_count":
                    role_count = count
                elif counter == "user_count":
                    user_count = count
                elif counter == "resource_count":
                    resource_count = count

            return {
                "status": "connected",
                "fallback_mode": False,
                "role_permissions_cached": role_count,
                "user_permissions_cached": user_count,
                "resource_permissions_cached": resource_count,
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except RedisError as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_mode": True,
            }

    def _calculate_hit_rate(self, info: dict) -> float:
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return round(hits / total * 100, 2) if total > 0 else 0.0


# ============================================================================
# Global Instance and Helpers
# ============================================================================


_acm_instance: AccessControlMatrix | None = None
_cache_instance: PermissionCache | None = None


def get_acm() -> AccessControlMatrix:
    """Get the global Access Control Matrix instance."""
    global _acm_instance
    if _acm_instance is None:
        _acm_instance = AccessControlMatrix()
    return _acm_instance


async def get_permission_cache() -> PermissionCache:
    """
    Get global permission cache instance.

    Returns:
        PermissionCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PermissionCache()
        await _cache_instance.get_redis_client()
    return _cache_instance


async def close_permission_cache() -> None:
    """Close global permission cache instance."""
    global _cache_instance
    if _cache_instance is not None:
        await _cache_instance.close()
        _cache_instance = None


def has_permission(
    role: UserRole | str,
    resource: ResourceType | str,
    action: PermissionAction | str,
    context: PermissionContext | None = None,
) -> bool:
    """
    Convenience function to check permissions using global ACM.

    Args:
        role: User role
        resource: Resource type
        action: Permission action
        context: Optional context for dynamic evaluation

    Returns:
        True if permission is granted
    """
    acm = get_acm()
    return acm.has_permission(role, resource, action, context)


class PermissionDenied(HTTPException):
    """Exception raised when permission is denied."""

    def __init__(
        self,
        resource: ResourceType | str,
        action: PermissionAction | str,
        detail: str | None = None,
    ) -> None:
        """
        Initialize permission denied exception.

        Args:
            resource: Resource that was accessed
            action: Action that was attempted
            detail: Optional additional detail
        """
        if detail is None:
            detail = f"Permission denied for action '{action}' on resource '{resource}'"

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def require_permission(
    resource: ResourceType | str,
    action: PermissionAction | str,
    context_builder: Callable | None = None,
) -> Callable:
    """
    Decorator to require specific permissions for a route.

    Args:
        resource: Resource type required
        action: Action required
        context_builder: Optional function to build PermissionContext from request

    Usage:
        @require_permission(ResourceType.SCHEDULE, PermissionAction.CREATE)
        async def create_schedule(user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract user from kwargs (assuming it's a dependency)
            user = kwargs.get("current_user") or kwargs.get("user")
            if not user:
                raise PermissionDenied(
                    resource, action, detail="Authentication required"
                )

                # Build context if builder provided
            context = None
            if context_builder:
                context = context_builder(*args, **kwargs)

            # Check permission (cached async path)
            acm = get_acm()
            if not await acm.has_permission_async(
                user.role, resource, action, context=context
            ):
                raise PermissionDenied(resource, action)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(roles: list[str] | str, allow_admin: bool = True):
    """
    Create a FastAPI dependency that checks user roles.

    Args:
        roles: List of allowed role names (or single role string)
        allow_admin: Whether to allow ADMIN role regardless (default: True)

    Returns:
        Dependency function that checks roles
    """
    if isinstance(roles, str):
        role_set = {roles.upper()}
    else:
        role_set = {str(r).upper() for r in roles}

    if allow_admin:
        role_set.add("ADMIN")

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role = current_user.role.upper() if current_user.role else ""

        if user_role not in role_set:
            logger.warning(
                f"Role check failed for user {current_user.username} "
                f"(role: {current_user.role}). Required: {role_set}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(sorted(role_set))}",
            )

        return current_user

    return role_checker


async def warm_permission_cache() -> int:
    """
    Pre-populate permission cache on application startup.

    Returns:
        Number of roles successfully cached
    """
    cache = await get_permission_cache()
    acm = get_acm()

    permissions_map: dict[UserRole, set[str]] = {}
    for role in UserRole:
        permissions = acm._flatten_permissions(acm.get_role_permissions(role))
        permissions_map[role] = permissions

    cached_count = await cache.warm_cache(permissions_map)
    return cached_count


async def invalidate_permission_cache(
    user_id: str | None = None,
    role: UserRole | str | None = None,
    invalidate_all: bool = False,
) -> bool:
    """
    Invalidate permission cache.

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
    if user_id is not None:
        return await cache.invalidate_user_permissions(user_id)
    if role is not None:
        return await cache.invalidate_role_permissions(role)
    return False


async def invalidate_user_role_cache(
    user_id: str, old_role: str | None = None, new_role: str | None = None
) -> bool:
    """
    Invalidate permission cache when a user's role changes.
    """
    cache = await get_permission_cache()
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
