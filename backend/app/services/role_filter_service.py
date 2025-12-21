"""Role-based filtering service for data access control.

This service provides role-based filtering capabilities to ensure different
user types (admin, coordinator, faculty, clinical_staff) only access data
they are authorized to see.

Role definitions (from PROJECT_STATUS_ASSESSMENT.md):
| Role | Sees | Hidden |
|------|------|--------|
| admin | Everything | - |
| coordinator | Schedules, people, conflicts | User management |
| faculty | Own schedule, swap requests | Other faculty details |
| rn/lpn/msa | Today's manifest, call roster | Academic blocks, compliance |
"""

from datetime import date
from enum import Enum
from typing import Dict, List, Any, Optional, Set


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    FACULTY = "faculty"
    CLINICAL_STAFF = "clinical_staff"  # Unified role for rn, lpn, msa
    RN = "rn"  # Registered Nurse
    LPN = "lpn"  # Licensed Practical Nurse
    MSA = "msa"  # Medical Support Assistant
    RESIDENT = "resident"


class ResourceType(str, Enum):
    """Resource types for access control."""
    SCHEDULES = "schedules"
    PEOPLE = "people"
    CONFLICTS = "conflicts"
    USERS = "users"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    OWN_SCHEDULE = "own_schedule"
    SWAPS = "swaps"
    MANIFEST = "manifest"
    CALL_ROSTER = "call_roster"
    ACADEMIC_BLOCKS = "academic_blocks"


class RoleFilterService:
    """Filter data based on user role.

    Provides methods to filter response data, check resource access permissions,
    and validate user access to specific endpoints based on their role.
    """

    # Define role permissions mapping
    ROLE_PERMISSIONS: Dict[UserRole, Set[ResourceType]] = {
        UserRole.ADMIN: {
            ResourceType.SCHEDULES,
            ResourceType.PEOPLE,
            ResourceType.CONFLICTS,
            ResourceType.USERS,
            ResourceType.COMPLIANCE,
            ResourceType.AUDIT,
            ResourceType.OWN_SCHEDULE,
            ResourceType.SWAPS,
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
            ResourceType.ACADEMIC_BLOCKS,
        },
        UserRole.COORDINATOR: {
            ResourceType.SCHEDULES,
            ResourceType.PEOPLE,
            ResourceType.CONFLICTS,
            ResourceType.OWN_SCHEDULE,
            ResourceType.SWAPS,
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
            ResourceType.ACADEMIC_BLOCKS,
        },
        UserRole.FACULTY: {
            ResourceType.OWN_SCHEDULE,
            ResourceType.SWAPS,
        },
        UserRole.CLINICAL_STAFF: {
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
        },
        UserRole.RN: {
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
        },
        UserRole.LPN: {
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
        },
        UserRole.MSA: {
            ResourceType.MANIFEST,
            ResourceType.CALL_ROSTER,
        },
        UserRole.RESIDENT: {
            ResourceType.OWN_SCHEDULE,
            ResourceType.SWAPS,
            ResourceType.CONFLICTS,
        },
    }

    @classmethod
    def get_role_from_string(cls, role_str: str) -> UserRole:
        """Convert string role to UserRole enum.

        Args:
            role_str: Role as string

        Returns:
            UserRole enum value

        Raises:
            ValueError: If role string is invalid
        """
        try:
            return UserRole(role_str.lower())
        except ValueError:
            raise ValueError(f"Invalid role: {role_str}")

    @classmethod
    def normalize_clinical_staff_role(cls, role: UserRole) -> UserRole:
        """Normalize specific clinical staff roles to unified clinical_staff.

        Args:
            role: User role

        Returns:
            Normalized role (converts rn/lpn/msa to clinical_staff for permission checks)
        """
        if role in (UserRole.RN, UserRole.LPN, UserRole.MSA):
            return UserRole.CLINICAL_STAFF
        return role

    @classmethod
    def can_access(cls, resource: ResourceType, role: str | UserRole) -> bool:
        """Check if role can access a resource type.

        Args:
            resource: Resource type to check access for
            role: User role (string or UserRole enum)

        Returns:
            True if role has access to the resource, False otherwise
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return False

        # Normalize clinical staff roles
        role = cls.normalize_clinical_staff_role(role)

        # Get permissions for role
        permissions = cls.ROLE_PERMISSIONS.get(role, set())
        return resource in permissions

    @classmethod
    def get_permissions(cls, role: str | UserRole) -> Set[ResourceType]:
        """Get all permissions for a given role.

        Args:
            role: User role (string or UserRole enum)

        Returns:
            Set of resource types the role can access
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return set()

        # Normalize clinical staff roles
        role = cls.normalize_clinical_staff_role(role)

        return cls.ROLE_PERMISSIONS.get(role, set())

    @classmethod
    def filter_for_role(
        cls,
        data: Dict[str, Any],
        role: str | UserRole,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Filter response data based on user role.

        Args:
            data: Raw data dictionary to filter
            role: User role (string or UserRole enum)
            user_id: Current user's ID (for filtering own data)

        Returns:
            Filtered data dictionary with only authorized fields
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return {}

        # Start with a copy of the data
        filtered_data = data.copy()

        # Get permissions for this role
        permissions = cls.get_permissions(role)

        # Admin sees everything - no filtering needed
        if role == UserRole.ADMIN:
            return filtered_data

        # Filter schedules based on permissions
        if "schedules" in filtered_data:
            if ResourceType.SCHEDULES not in permissions:
                # Check if they can see their own schedule
                if ResourceType.OWN_SCHEDULE in permissions and user_id:
                    # Filter to only user's own schedules
                    filtered_data["schedules"] = cls._filter_own_schedules(
                        filtered_data["schedules"], user_id
                    )
                else:
                    # Remove schedules entirely
                    filtered_data.pop("schedules", None)

        # Filter people data
        if "people" in filtered_data and ResourceType.PEOPLE not in permissions:
            filtered_data.pop("people", None)

        # Filter conflicts
        if "conflicts" in filtered_data and ResourceType.CONFLICTS not in permissions:
            filtered_data.pop("conflicts", None)

        # Filter user management
        if "users" in filtered_data and ResourceType.USERS not in permissions:
            filtered_data.pop("users", None)

        # Filter compliance data
        if "compliance" in filtered_data and ResourceType.COMPLIANCE not in permissions:
            filtered_data.pop("compliance", None)

        if "mtf_compliance" in filtered_data and ResourceType.COMPLIANCE not in permissions:
            filtered_data.pop("mtf_compliance", None)

        # Filter audit logs
        if "audit" in filtered_data and ResourceType.AUDIT not in permissions:
            filtered_data.pop("audit", None)

        if "audit_logs" in filtered_data and ResourceType.AUDIT not in permissions:
            filtered_data.pop("audit_logs", None)

        # Filter academic blocks
        if "academic_blocks" in filtered_data and ResourceType.ACADEMIC_BLOCKS not in permissions:
            filtered_data.pop("academic_blocks", None)

        # Filter swap management
        if "swap_management" in filtered_data and ResourceType.SWAPS not in permissions:
            filtered_data.pop("swap_management", None)

        # For clinical staff, only keep manifest and call roster
        if role in (UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA):
            allowed_keys = {"manifest", "call_roster", "today_assignments", "daily_manifest"}
            keys_to_remove = [key for key in filtered_data.keys() if key not in allowed_keys]
            for key in keys_to_remove:
                filtered_data.pop(key, None)

        return filtered_data

    @classmethod
    def filter_schedule_list(
        cls,
        schedules: List[Dict[str, Any]],
        role: str | UserRole,
        user_id: Optional[str] = None,
        today_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Filter a list of schedules based on role permissions.

        Args:
            schedules: List of schedule dictionaries
            role: User role (string or UserRole enum)
            user_id: Current user's ID (for filtering own schedules)
            today_only: If True, filter to only today's schedules

        Returns:
            Filtered list of schedules
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return []

        # Get permissions for this role
        permissions = cls.get_permissions(role)

        # Admin and coordinators see everything
        if role in (UserRole.ADMIN, UserRole.COORDINATOR):
            schedules_filtered = schedules
        # Clinical staff sees only today's manifest
        elif role in (UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA):
            today = date.today().isoformat()
            schedules_filtered = [s for s in schedules if s.get("date") == today]
        # Others (faculty, residents) see only their own schedules
        elif ResourceType.OWN_SCHEDULE in permissions and user_id:
            schedules_filtered = cls._filter_own_schedules(schedules, user_id)
        else:
            schedules_filtered = []

        # Apply today filter if requested
        if today_only:
            today = date.today().isoformat()
            schedules_filtered = [s for s in schedules_filtered if s.get("date") == today]

        return schedules_filtered

    @classmethod
    def _filter_own_schedules(
        cls,
        schedules: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Filter schedules to only include those belonging to the user.

        Args:
            schedules: List of schedule dictionaries
            user_id: User ID to filter by

        Returns:
            List of schedules belonging to the user
        """
        return [
            s for s in schedules
            if (s.get("person_id") == user_id or
                s.get("staff_id") == user_id or
                s.get("user_id") == user_id or
                s.get("faculty_id") == user_id)
        ]

    @classmethod
    def can_access_endpoint(
        cls,
        role: str | UserRole,
        endpoint_category: str
    ) -> bool:
        """Check if a role can access a specific endpoint category.

        Args:
            role: User role (string or UserRole enum)
            endpoint_category: Category of endpoint (e.g., 'schedules', 'compliance', 'swaps')

        Returns:
            True if the role can access the endpoint category, False otherwise
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return False

        # Map endpoint categories to resource types
        category_map = {
            "schedules": ResourceType.SCHEDULES,
            "people": ResourceType.PEOPLE,
            "conflicts": ResourceType.CONFLICTS,
            "users": ResourceType.USERS,
            "compliance": ResourceType.COMPLIANCE,
            "audit": ResourceType.AUDIT,
            "swaps": ResourceType.SWAPS,
            "manifest": ResourceType.MANIFEST,
            "call_roster": ResourceType.CALL_ROSTER,
            "academic_blocks": ResourceType.ACADEMIC_BLOCKS,
        }

        resource = category_map.get(endpoint_category.lower())
        if not resource:
            return False

        return cls.can_access(resource, role)

    @classmethod
    def get_accessible_resources(cls, role: str | UserRole) -> List[str]:
        """Get list of resource names accessible to a role.

        Args:
            role: User role (string or UserRole enum)

        Returns:
            List of resource names (as strings) that the role can access
        """
        permissions = cls.get_permissions(role)
        return [resource.value for resource in permissions]

    @classmethod
    def is_admin(cls, role: str | UserRole) -> bool:
        """Check if role is admin.

        Args:
            role: User role (string or UserRole enum)

        Returns:
            True if role is admin, False otherwise
        """
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return False
        return role == UserRole.ADMIN

    @classmethod
    def is_clinical_staff(cls, role: str | UserRole) -> bool:
        """Check if role is clinical staff (rn, lpn, msa, or clinical_staff).

        Args:
            role: User role (string or UserRole enum)

        Returns:
            True if role is any clinical staff type, False otherwise
        """
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return False
        return role in (UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA)

    @classmethod
    def get_role_description(cls, role: str | UserRole) -> Dict[str, Any]:
        """Get human-readable description of a role's permissions.

        Args:
            role: User role (string or UserRole enum)

        Returns:
            Dictionary with role information and permissions description
        """
        # Convert string to UserRole if needed
        if isinstance(role, str):
            try:
                role = cls.get_role_from_string(role)
            except ValueError:
                return {"role": role, "error": "Invalid role"}

        # Role descriptions based on PROJECT_STATUS_ASSESSMENT.md
        descriptions = {
            UserRole.ADMIN: {
                "role": "admin",
                "title": "Administrator",
                "sees": "Everything",
                "hidden": "-",
                "description": "Full system access including user management, compliance, and audit logs"
            },
            UserRole.COORDINATOR: {
                "role": "coordinator",
                "title": "Program Coordinator",
                "sees": "Schedules, people, conflicts",
                "hidden": "User management",
                "description": "Can manage schedules, people, and handle conflicts. Cannot manage users."
            },
            UserRole.FACULTY: {
                "role": "faculty",
                "title": "Faculty Member",
                "sees": "Own schedule, swap requests",
                "hidden": "Other faculty details",
                "description": "Can view their own schedule and participate in swap requests."
            },
            UserRole.CLINICAL_STAFF: {
                "role": "clinical_staff",
                "title": "Clinical Staff (RN/LPN/MSA)",
                "sees": "Today's manifest, call roster",
                "hidden": "Academic blocks, compliance",
                "description": "Can view daily assignments and call roster. No access to academic scheduling."
            },
            UserRole.RN: {
                "role": "rn",
                "title": "Registered Nurse",
                "sees": "Today's manifest, call roster",
                "hidden": "Academic blocks, compliance",
                "description": "Can view daily assignments and call roster. No access to academic scheduling."
            },
            UserRole.LPN: {
                "role": "lpn",
                "title": "Licensed Practical Nurse",
                "sees": "Today's manifest, call roster",
                "hidden": "Academic blocks, compliance",
                "description": "Can view daily assignments and call roster. No access to academic scheduling."
            },
            UserRole.MSA: {
                "role": "msa",
                "title": "Medical Support Assistant",
                "sees": "Today's manifest, call roster",
                "hidden": "Academic blocks, compliance",
                "description": "Can view daily assignments and call roster. No access to academic scheduling."
            },
            UserRole.RESIDENT: {
                "role": "resident",
                "title": "Resident",
                "sees": "Own schedule, swap requests, conflicts",
                "hidden": "Other resident details",
                "description": "Can view their own schedule, participate in swaps, and see conflicts."
            },
        }

        description = descriptions.get(role, {
            "role": str(role),
            "title": "Unknown",
            "sees": "Unknown",
            "hidden": "Unknown",
            "description": "No description available"
        })

        # Add permissions list
        description["permissions"] = cls.get_accessible_resources(role)

        return description
