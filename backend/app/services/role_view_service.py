"""Role-based view filtering service."""

from typing import Any, Dict, List, Optional

from app.schemas.role_views import RoleViewConfig, StaffRole, ViewPermissions

ROLE_PERMISSIONS = {
    StaffRole.ADMIN: ViewPermissions(
        can_view_all_schedules=True,
        can_view_academic_blocks=True,
        can_view_compliance=True,
        can_view_conflicts=True,
        can_manage_swaps=True,
    ),
    StaffRole.COORDINATOR: ViewPermissions(
        can_view_all_schedules=True,
        can_view_academic_blocks=True,
        can_view_conflicts=True,
        can_manage_swaps=True,
    ),
    StaffRole.FACULTY: ViewPermissions(
        can_view_conflicts=True,
        can_manage_swaps=True,
    ),
    StaffRole.CLINICAL_STAFF: ViewPermissions(
        can_view_all_schedules=False,
        can_view_academic_blocks=False,
        can_view_compliance=False,
    ),
    StaffRole.RESIDENT: ViewPermissions(
        can_view_conflicts=True,
        can_manage_swaps=True,
    ),
}


class RoleViewService:
    """Service for filtering views based on user roles."""

    @staticmethod
    def get_permissions(role: StaffRole) -> ViewPermissions:
        """Get permissions for a given role."""
        return ROLE_PERMISSIONS.get(role, ViewPermissions())

    @staticmethod
    def filter_response_for_role(
        data: dict[str, Any], role: StaffRole, user_id: int | None = None
    ) -> dict[str, Any]:
        """
        Filter API response based on role permissions.

        Args:
            data: The raw data dictionary to filter
            role: The user's role
            user_id: The user's ID (for filtering own data)

        Returns:
            Filtered data dictionary based on role permissions
        """
        permissions = RoleViewService.get_permissions(role)
        filtered_data = data.copy()

        # Filter schedules based on permissions
        if "schedules" in filtered_data and not permissions.can_view_all_schedules:
            if user_id and permissions.can_view_own_schedule:
                # Only show user's own schedules
                filtered_data["schedules"] = [
                    schedule
                    for schedule in filtered_data["schedules"]
                    if schedule.get("person_id") == user_id
                    or schedule.get("staff_id") == user_id
                ]
            else:
                # Remove schedules entirely if no permission
                filtered_data.pop("schedules", None)

        # Filter academic blocks
        if (
            "academic_blocks" in filtered_data
            and not permissions.can_view_academic_blocks
        ):
            filtered_data.pop("academic_blocks", None)

        # Filter compliance data
        if "compliance" in filtered_data and not permissions.can_view_compliance:
            filtered_data.pop("compliance", None)

        if "mtf_compliance" in filtered_data and not permissions.can_view_compliance:
            filtered_data.pop("mtf_compliance", None)

        # Filter conflicts
        if "conflicts" in filtered_data and not permissions.can_view_conflicts:
            filtered_data.pop("conflicts", None)

        # Filter swap management features
        if "swap_management" in filtered_data and not permissions.can_manage_swaps:
            filtered_data.pop("swap_management", None)

        # For clinical staff, limit to manifest and call roster
        if role == StaffRole.CLINICAL_STAFF:
            # Keep only manifest and call roster
            allowed_keys = {"manifest", "call_roster", "today_assignments"}
            keys_to_remove = [
                key for key in filtered_data.keys() if key not in allowed_keys
            ]
            for key in keys_to_remove:
                filtered_data.pop(key, None)

        return filtered_data

    @staticmethod
    def filter_schedule_list(
        schedules: list[dict[str, Any]], role: StaffRole, user_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Filter a list of schedules based on role permissions.

        Args:
            schedules: List of schedule dictionaries
            role: The user's role
            user_id: The user's ID (for filtering own schedules)

        Returns:
            Filtered list of schedules
        """
        permissions = RoleViewService.get_permissions(role)

        # Admin and coordinators see everything
        if permissions.can_view_all_schedules:
            return schedules

        # Clinical staff sees only today's manifest
        if role == StaffRole.CLINICAL_STAFF:
            from datetime import date

            today = date.today().isoformat()
            return [s for s in schedules if s.get("date") == today]

        # Others (faculty, residents) see only their own schedules
        if user_id and permissions.can_view_own_schedule:
            return [
                s
                for s in schedules
                if s.get("person_id") == user_id or s.get("staff_id") == user_id
            ]

        return []

    @staticmethod
    def can_access_endpoint(role: StaffRole, endpoint_category: str) -> bool:
        """
        Check if a role can access a specific endpoint category.

        Args:
            role: The user's role
            endpoint_category: Category of endpoint (e.g., 'schedules', 'compliance', 'swaps')

        Returns:
            True if the role can access the endpoint, False otherwise
        """
        permissions = RoleViewService.get_permissions(role)

        access_map = {
            "schedules": permissions.can_view_all_schedules
            or permissions.can_view_own_schedule,
            "manifest": permissions.can_view_manifest,
            "call_roster": permissions.can_view_call_roster,
            "academic_blocks": permissions.can_view_academic_blocks,
            "compliance": permissions.can_view_compliance,
            "conflicts": permissions.can_view_conflicts,
            "swaps": permissions.can_manage_swaps,
        }

        return access_map.get(endpoint_category, False)

    @staticmethod
    def get_role_config(role: StaffRole) -> RoleViewConfig:
        """
        Get the complete role configuration.

        Args:
            role: The user's role

        Returns:
            RoleViewConfig object with role and permissions
        """
        return RoleViewConfig(
            role=role, permissions=RoleViewService.get_permissions(role)
        )
