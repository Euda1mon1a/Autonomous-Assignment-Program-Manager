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
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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
    2. COORDINATOR (90) - Schedule management, inherits from ADMIN
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
        UserRole.COORDINATOR: {UserRole.ADMIN},  # Inherits from admin only
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
            ResourceType.ABSENCE: {PermissionAction.CREATE, PermissionAction.READ},
            ResourceType.LEAVE: {PermissionAction.CREATE, PermissionAction.READ},
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

    def __init__(self, enable_audit: bool = True):
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

        # Apply context-aware checks if context is provided
        if context and has_static_permission:
            has_permission = self._check_context_permission(
                role, resource, action, context
            )
        else:
            has_permission = has_static_permission

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
                    return self._context_evaluators["is_own_resource"](context)

        return True  # No additional context restrictions

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

        entry = PermissionAuditEntry(
            action="checked",
            role=role if isinstance(role, UserRole) else UserRole(role),
            resource=(
                resource
                if isinstance(resource, ResourceType)
                else ResourceType(resource)
            ),
            permission=(
                action
                if isinstance(action, PermissionAction)
                else PermissionAction(action)
            ),
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


# Global ACM instance
_acm_instance: AccessControlMatrix | None = None


def get_acm() -> AccessControlMatrix:
    """Get the global Access Control Matrix instance."""
    global _acm_instance
    if _acm_instance is None:
        _acm_instance = AccessControlMatrix()
    return _acm_instance


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
    ):
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
):
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
        async def wrapper(*args, **kwargs):
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

            # Check permission
            if not has_permission(user.role, resource, action, context):
                raise PermissionDenied(resource, action)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
