"""Permission models and enums for role-based access control."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PermissionAction(str, Enum):
    """Permission actions for RBAC."""

    ***REMOVED*** General CRUD actions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    ***REMOVED*** Schedule-specific actions
    GENERATE_SCHEDULE = "generate_schedule"
    APPROVE_SCHEDULE = "approve_schedule"
    PUBLISH_SCHEDULE = "publish_schedule"

    ***REMOVED*** Assignment actions
    ASSIGN = "assign"
    REASSIGN = "reassign"

    ***REMOVED*** Swap actions
    REQUEST_SWAP = "request_swap"
    APPROVE_SWAP = "approve_swap"
    EXECUTE_SWAP = "execute_swap"

    ***REMOVED*** Leave/absence actions
    REQUEST_LEAVE = "request_leave"
    APPROVE_LEAVE = "approve_leave"

    ***REMOVED*** User management
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"

    ***REMOVED*** System administration
    CONFIGURE_SYSTEM = "configure_system"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_TEMPLATES = "manage_templates"

    ***REMOVED*** Analytics and reporting
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    ***REMOVED*** Resilience framework
    VIEW_RESILIENCE = "view_resilience"
    MANAGE_RESILIENCE = "manage_resilience"
    ACTIVATE_FALLBACK = "activate_fallback"


class ResourceType(str, Enum):
    """Resource types for permission checks."""

    SCHEDULE = "schedule"
    ASSIGNMENT = "assignment"
    PERSON = "person"
    USER = "user"
    SWAP = "swap"
    ABSENCE = "absence"
    ROTATION = "rotation"
    BLOCK = "block"
    PROCEDURE = "procedure"
    CERTIFICATION = "certification"
    NOTIFICATION = "notification"
    TEMPLATE = "template"
    ANALYTICS = "analytics"
    RESILIENCE = "resilience"
    SYSTEM = "system"


class UserRole(str, Enum):
    """User roles with hierarchical structure."""

    ***REMOVED*** Highest privilege
    ADMIN = "admin"

    ***REMOVED*** Schedule management
    COORDINATOR = "coordinator"

    ***REMOVED*** Clinical staff
    FACULTY = "faculty"
    RESIDENT = "resident"

    ***REMOVED*** Support staff (grouped)
    CLINICAL_STAFF = "clinical_staff"
    RN = "rn"
    LPN = "lpn"
    MSA = "msa"


class Permission(BaseModel):
    """Represents a single permission."""

    resource: ResourceType
    action: PermissionAction
    conditions: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for caching keys."""
        return f"{self.resource.value}:{self.action.value}"

    def __hash__(self) -> int:
        """Make permission hashable for set operations."""
        return hash(str(self))


class RolePermissions(BaseModel):
    """Permission set for a role."""

    role: UserRole
    permissions: set[str] = Field(default_factory=set)
    inherits_from: list[UserRole] = Field(default_factory=list)

    class Config:
        frozen = True  ***REMOVED*** Make immutable for caching


class PermissionCheckResult(BaseModel):
    """Result of a permission check."""

    allowed: bool
    reason: str | None = None
    cached: bool = False
    checked_at: str | None = None


***REMOVED*** Role hierarchy definition
***REMOVED*** Lower roles in the list inherit from higher roles
***REMOVED*** SECURITY FIX: Faculty does NOT inherit from Coordinator
ROLE_HIERARCHY = {
    UserRole.ADMIN: [],  ***REMOVED*** Admin has no parent roles (top of hierarchy)
    UserRole.COORDINATOR: [UserRole.ADMIN],  ***REMOVED*** Coordinator inherits from admin
    UserRole.FACULTY: [],  ***REMOVED*** INDEPENDENT - no inheritance (SECURITY FIX)
    UserRole.RESIDENT: [],  ***REMOVED*** INDEPENDENT - no inheritance
    UserRole.CLINICAL_STAFF: [],  ***REMOVED*** INDEPENDENT - no inheritance
    UserRole.RN: [UserRole.CLINICAL_STAFF],  ***REMOVED*** RN inherits from clinical_staff
    UserRole.LPN: [UserRole.CLINICAL_STAFF],  ***REMOVED*** LPN inherits from clinical_staff
    UserRole.MSA: [UserRole.CLINICAL_STAFF],  ***REMOVED*** MSA inherits from clinical_staff
}

***REMOVED*** Role privilege levels (higher = more privileged)
ROLE_LEVELS = {
    UserRole.ADMIN: 100,
    UserRole.COORDINATOR: 90,
    UserRole.FACULTY: 80,
    UserRole.RESIDENT: 70,
    UserRole.CLINICAL_STAFF: 60,
    UserRole.RN: 50,
    UserRole.LPN: 40,
    UserRole.MSA: 30,
}


***REMOVED*** Default permission sets for each role
***REMOVED*** These are the base permissions before inheritance
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        ***REMOVED*** Full system access
        f"{ResourceType.SYSTEM.value}:{PermissionAction.CONFIGURE_SYSTEM.value}",
        f"{ResourceType.SYSTEM.value}:{PermissionAction.VIEW_AUDIT_LOG.value}",
        f"{ResourceType.USER.value}:{PermissionAction.MANAGE_USERS.value}",
        f"{ResourceType.USER.value}:{PermissionAction.MANAGE_ROLES.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.CREATE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.DELETE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.GENERATE_SCHEDULE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.APPROVE_SCHEDULE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.PUBLISH_SCHEDULE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.CREATE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.DELETE.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.CREATE.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.READ.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.DELETE.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.APPROVE_SWAP.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.EXECUTE_SWAP.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.APPROVE_LEAVE.value}",
        f"{ResourceType.ANALYTICS.value}:{PermissionAction.VIEW_ANALYTICS.value}",
        f"{ResourceType.ANALYTICS.value}:{PermissionAction.EXPORT_DATA.value}",
        f"{ResourceType.RESILIENCE.value}:{PermissionAction.VIEW_RESILIENCE.value}",
        f"{ResourceType.RESILIENCE.value}:{PermissionAction.MANAGE_RESILIENCE.value}",
        f"{ResourceType.RESILIENCE.value}:{PermissionAction.ACTIVATE_FALLBACK.value}",
        f"{ResourceType.TEMPLATE.value}:{PermissionAction.MANAGE_TEMPLATES.value}",
    },
    UserRole.COORDINATOR: {
        ***REMOVED*** Schedule and assignment management
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.CREATE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.GENERATE_SCHEDULE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.APPROVE_SCHEDULE.value}",
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.PUBLISH_SCHEDULE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.CREATE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.ASSIGN.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.REASSIGN.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.READ.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.UPDATE.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.APPROVE_SWAP.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.APPROVE_LEAVE.value}",
        f"{ResourceType.ANALYTICS.value}:{PermissionAction.VIEW_ANALYTICS.value}",
        f"{ResourceType.RESILIENCE.value}:{PermissionAction.VIEW_RESILIENCE.value}",
        f"{ResourceType.TEMPLATE.value}:{PermissionAction.READ.value}",
    },
    UserRole.FACULTY: {
        ***REMOVED*** View schedules, manage own assignments and swaps
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.READ.value}",
        f"{ResourceType.PERSON.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.REQUEST_SWAP.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.REQUEST_LEAVE.value}",
        f"{ResourceType.PROCEDURE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.CERTIFICATION.value}:{PermissionAction.READ.value}",
        f"{ResourceType.NOTIFICATION.value}:{PermissionAction.READ.value}",
    },
    UserRole.RESIDENT: {
        ***REMOVED*** View own schedule and request changes
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.READ.value}",
        f"{ResourceType.SWAP.value}:{PermissionAction.REQUEST_SWAP.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ABSENCE.value}:{PermissionAction.REQUEST_LEAVE.value}",
        f"{ResourceType.NOTIFICATION.value}:{PermissionAction.READ.value}",
    },
    UserRole.CLINICAL_STAFF: {
        ***REMOVED*** Basic schedule viewing
        f"{ResourceType.SCHEDULE.value}:{PermissionAction.READ.value}",
        f"{ResourceType.ASSIGNMENT.value}:{PermissionAction.READ.value}",
        f"{ResourceType.NOTIFICATION.value}:{PermissionAction.READ.value}",
    },
    UserRole.RN: {
        ***REMOVED*** RN-specific permissions (inherits from CLINICAL_STAFF)
        f"{ResourceType.PROCEDURE.value}:{PermissionAction.READ.value}",
    },
    UserRole.LPN: {
        ***REMOVED*** LPN-specific permissions (inherits from CLINICAL_STAFF)
    },
    UserRole.MSA: {
        ***REMOVED*** MSA-specific permissions (inherits from CLINICAL_STAFF)
    },
}
