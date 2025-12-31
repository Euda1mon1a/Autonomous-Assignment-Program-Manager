"""Tests for RoleViewService."""

from datetime import date

import pytest

from app.schemas.role_views import RoleViewConfig, StaffRole, ViewPermissions
from app.services.role_view_service import ROLE_PERMISSIONS, RoleViewService


class TestRoleViewService:
    """Test suite for RoleViewService."""

    # ========================================================================
    # Get Permissions Tests
    # ========================================================================

    def test_get_permissions_admin(self):
        """Test admin has full permissions."""
        permissions = RoleViewService.get_permissions(StaffRole.ADMIN)

        assert permissions.can_view_all_schedules is True
        assert permissions.can_view_academic_blocks is True
        assert permissions.can_view_compliance is True
        assert permissions.can_view_conflicts is True
        assert permissions.can_manage_swaps is True

    def test_get_permissions_coordinator(self):
        """Test coordinator has broad view permissions but not compliance."""
        permissions = RoleViewService.get_permissions(StaffRole.COORDINATOR)

        assert permissions.can_view_all_schedules is True
        assert permissions.can_view_academic_blocks is True
        assert permissions.can_view_conflicts is True
        assert permissions.can_manage_swaps is True
        assert permissions.can_view_compliance is False

    def test_get_permissions_faculty(self):
        """Test faculty has limited permissions."""
        permissions = RoleViewService.get_permissions(StaffRole.FACULTY)

        assert permissions.can_view_all_schedules is False
        assert permissions.can_view_academic_blocks is False
        assert permissions.can_view_compliance is False
        assert permissions.can_view_conflicts is True
        assert permissions.can_manage_swaps is True

    def test_get_permissions_clinical_staff(self):
        """Test clinical staff has minimal permissions."""
        permissions = RoleViewService.get_permissions(StaffRole.CLINICAL_STAFF)

        assert permissions.can_view_all_schedules is False
        assert permissions.can_view_academic_blocks is False
        assert permissions.can_view_compliance is False
        # Default ViewPermissions have manifest and call roster access
        assert permissions.can_view_manifest is True
        assert permissions.can_view_call_roster is True

    def test_get_permissions_resident(self):
        """Test resident has swap and conflict permissions."""
        permissions = RoleViewService.get_permissions(StaffRole.RESIDENT)

        assert permissions.can_view_all_schedules is False
        assert permissions.can_view_academic_blocks is False
        assert permissions.can_view_compliance is False
        assert permissions.can_view_conflicts is True
        assert permissions.can_manage_swaps is True

    def test_get_permissions_unknown_role_returns_default(self):
        """Test unknown role returns default empty permissions."""
        # Create a mock role that doesn't exist in ROLE_PERMISSIONS
        # Since we can't add new enum values, we'll test the fallback behavior
        # by directly checking ROLE_PERMISSIONS.get behavior
        default_perms = ROLE_PERMISSIONS.get("nonexistent", ViewPermissions())

        assert default_perms.can_view_all_schedules is False
        assert default_perms.can_view_academic_blocks is False
        assert default_perms.can_view_compliance is False

    # ========================================================================
    # Filter Response for Role Tests
    # ========================================================================

    def test_filter_response_admin_sees_everything(self):
        """Test admin role sees all data without filtering."""
        data = {
            "schedules": [{"id": 1}, {"id": 2}],
            "academic_blocks": [{"block": 1}],
            "compliance": {"status": "compliant"},
            "mtf_compliance": {"mtf": "compliant"},
            "conflicts": [{"conflict": 1}],
            "swap_management": {"swaps": []},
        }

        filtered = RoleViewService.filter_response_for_role(data, StaffRole.ADMIN)

        # Admin should see everything
        assert filtered == data
        assert "schedules" in filtered
        assert "academic_blocks" in filtered
        assert "compliance" in filtered
        assert "mtf_compliance" in filtered
        assert "conflicts" in filtered
        assert "swap_management" in filtered

    def test_filter_response_coordinator_no_compliance(self):
        """Test coordinator cannot see compliance data."""
        data = {
            "schedules": [{"id": 1}],
            "academic_blocks": [{"block": 1}],
            "compliance": {"status": "compliant"},
            "mtf_compliance": {"mtf": "compliant"},
            "conflicts": [{"conflict": 1}],
            "swap_management": {"swaps": []},
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.COORDINATOR
        )

        # Coordinator sees everything except compliance
        assert "schedules" in filtered
        assert "academic_blocks" in filtered
        assert "compliance" not in filtered
        assert "mtf_compliance" not in filtered
        assert "conflicts" in filtered
        assert "swap_management" in filtered

    def test_filter_response_faculty_own_schedule_only(self):
        """Test faculty sees only their own schedules."""
        data = {
            "schedules": [
                {"id": 1, "person_id": 100},
                {"id": 2, "person_id": 200},
                {"id": 3, "staff_id": 100},
            ],
            "academic_blocks": [{"block": 1}],
            "compliance": {"status": "compliant"},
            "conflicts": [{"conflict": 1}],
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.FACULTY, user_id=100
        )

        # Faculty sees only their own schedules
        assert "schedules" in filtered
        assert len(filtered["schedules"]) == 2
        assert filtered["schedules"][0]["person_id"] == 100
        assert filtered["schedules"][1]["staff_id"] == 100
        # Cannot see academic blocks or compliance
        assert "academic_blocks" not in filtered
        assert "compliance" not in filtered
        # Can see conflicts
        assert "conflicts" in filtered

    def test_filter_response_faculty_without_user_id_removes_schedules(self):
        """Test faculty without user_id has schedules removed."""
        data = {
            "schedules": [{"id": 1}, {"id": 2}],
            "conflicts": [{"conflict": 1}],
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.FACULTY, user_id=None
        )

        # Without user_id, schedules should be removed
        assert "schedules" not in filtered
        # But can still see conflicts
        assert "conflicts" in filtered

    def test_filter_response_resident_own_schedule_only(self):
        """Test resident sees only their own schedules."""
        data = {
            "schedules": [
                {"id": 1, "person_id": 50},
                {"id": 2, "person_id": 60},
                {"id": 3, "person_id": 50},
            ],
            "conflicts": [{"conflict": 1}],
            "swap_management": {"swaps": []},
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.RESIDENT, user_id=50
        )

        # Resident sees only their own schedules
        assert "schedules" in filtered
        assert len(filtered["schedules"]) == 2
        assert all(s["person_id"] == 50 for s in filtered["schedules"])
        # Can see conflicts and swap management
        assert "conflicts" in filtered
        assert "swap_management" in filtered

    def test_filter_response_clinical_staff_manifest_only(self):
        """Test clinical staff only sees manifest and call roster."""
        data = {
            "manifest": [{"location": "ICU"}],
            "call_roster": [{"name": "Dr. Smith"}],
            "today_assignments": [{"assignment": 1}],
            "schedules": [{"id": 1}],
            "academic_blocks": [{"block": 1}],
            "compliance": {"status": "compliant"},
            "conflicts": [{"conflict": 1}],
            "swap_management": {"swaps": []},
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.CLINICAL_STAFF
        )

        # Clinical staff only sees manifest, call_roster, and today_assignments
        assert "manifest" in filtered
        assert "call_roster" in filtered
        assert "today_assignments" in filtered
        # Everything else is filtered out
        assert "schedules" not in filtered
        assert "academic_blocks" not in filtered
        assert "compliance" not in filtered
        assert "conflicts" not in filtered
        assert "swap_management" not in filtered

    def test_filter_response_clinical_staff_removes_all_except_allowed(self):
        """Test clinical staff filtering removes all keys except allowed ones."""
        data = {
            "manifest": [{"location": "ICU"}],
            "call_roster": [{"name": "Dr. Smith"}],
            "today_assignments": [{"assignment": 1}],
            "other_data": {"some": "data"},
            "random_key": "value",
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.CLINICAL_STAFF
        )

        # Only allowed keys remain
        assert set(filtered.keys()) <= {"manifest", "call_roster", "today_assignments"}
        assert "other_data" not in filtered
        assert "random_key" not in filtered

    def test_filter_response_empty_data(self):
        """Test filtering empty data dictionary."""
        data = {}

        filtered = RoleViewService.filter_response_for_role(data, StaffRole.ADMIN)

        assert filtered == {}

    def test_filter_response_preserves_unrelated_keys_for_admin(self):
        """Test admin filtering preserves all keys including unrelated ones."""
        data = {
            "schedules": [{"id": 1}],
            "custom_field": "value",
            "another_field": [1, 2, 3],
        }

        filtered = RoleViewService.filter_response_for_role(data, StaffRole.ADMIN)

        # Admin sees everything, including custom fields
        assert filtered == data
        assert "custom_field" in filtered
        assert "another_field" in filtered

    # ========================================================================
    # Filter Schedule List Tests
    # ========================================================================

    def test_filter_schedule_list_admin_sees_all(self):
        """Test admin sees all schedules."""
        schedules = [
            {"id": 1, "person_id": 100, "date": "2025-01-15"},
            {"id": 2, "person_id": 200, "date": "2025-01-16"},
            {"id": 3, "person_id": 300, "date": "2025-01-17"},
        ]

        filtered = RoleViewService.filter_schedule_list(schedules, StaffRole.ADMIN)

        assert len(filtered) == 3
        assert filtered == schedules

    def test_filter_schedule_list_coordinator_sees_all(self):
        """Test coordinator sees all schedules."""
        schedules = [
            {"id": 1, "person_id": 100},
            {"id": 2, "person_id": 200},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.COORDINATOR
        )

        assert len(filtered) == 2
        assert filtered == schedules

    def test_filter_schedule_list_faculty_sees_own(self):
        """Test faculty sees only their own schedules."""
        schedules = [
            {"id": 1, "person_id": 100},
            {"id": 2, "person_id": 200},
            {"id": 3, "staff_id": 100},
            {"id": 4, "person_id": 300},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.FACULTY, user_id=100
        )

        assert len(filtered) == 2
        assert filtered[0]["person_id"] == 100
        assert filtered[1]["staff_id"] == 100

    def test_filter_schedule_list_resident_sees_own(self):
        """Test resident sees only their own schedules."""
        schedules = [
            {"id": 1, "person_id": 50},
            {"id": 2, "person_id": 60},
            {"id": 3, "person_id": 50},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.RESIDENT, user_id=50
        )

        assert len(filtered) == 2
        assert all(s["person_id"] == 50 for s in filtered)

    def test_filter_schedule_list_clinical_staff_today_only(self):
        """Test clinical staff sees only today's schedules."""
        today = date.today().isoformat()
        tomorrow = "2025-12-31"

        schedules = [
            {"id": 1, "person_id": 100, "date": today},
            {"id": 2, "person_id": 200, "date": tomorrow},
            {"id": 3, "person_id": 300, "date": today},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.CLINICAL_STAFF
        )

        assert len(filtered) == 2
        assert all(s["date"] == today for s in filtered)

    def test_filter_schedule_list_faculty_no_user_id_returns_empty(self):
        """Test faculty without user_id gets empty list."""
        schedules = [
            {"id": 1, "person_id": 100},
            {"id": 2, "person_id": 200},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.FACULTY, user_id=None
        )

        assert filtered == []

    def test_filter_schedule_list_resident_no_user_id_returns_empty(self):
        """Test resident without user_id gets empty list."""
        schedules = [
            {"id": 1, "person_id": 50},
            {"id": 2, "person_id": 60},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.RESIDENT, user_id=None
        )

        assert filtered == []

    def test_filter_schedule_list_empty_list(self):
        """Test filtering empty schedule list."""
        schedules = []

        filtered = RoleViewService.filter_schedule_list(schedules, StaffRole.ADMIN)

        assert filtered == []

    def test_filter_schedule_list_matches_staff_id(self):
        """Test filtering works with staff_id field."""
        schedules = [
            {"id": 1, "staff_id": 100},
            {"id": 2, "staff_id": 200},
            {"id": 3, "staff_id": 100},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.FACULTY, user_id=100
        )

        assert len(filtered) == 2
        assert all(s["staff_id"] == 100 for s in filtered)

    def test_filter_schedule_list_no_matching_schedules(self):
        """Test filtering when user has no matching schedules."""
        schedules = [
            {"id": 1, "person_id": 100},
            {"id": 2, "person_id": 200},
        ]

        filtered = RoleViewService.filter_schedule_list(
            schedules, StaffRole.FACULTY, user_id=999
        )

        assert filtered == []

    # ========================================================================
    # Can Access Endpoint Tests
    # ========================================================================

    def test_can_access_endpoint_admin_full_access(self):
        """Test admin can access all endpoint categories."""
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "schedules") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "manifest") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "call_roster") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "academic_blocks")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "compliance") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "conflicts") is True
        )
        assert RoleViewService.can_access_endpoint(StaffRole.ADMIN, "swaps") is True

    def test_can_access_endpoint_coordinator_no_compliance(self):
        """Test coordinator can access most endpoints except compliance."""
        assert (
            RoleViewService.can_access_endpoint(StaffRole.COORDINATOR, "schedules")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.COORDINATOR, "academic_blocks")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.COORDINATOR, "conflicts")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.COORDINATOR, "swaps") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.COORDINATOR, "compliance")
            is False
        )

    def test_can_access_endpoint_faculty_limited_access(self):
        """Test faculty has limited endpoint access."""
        # Faculty cannot view all schedules
        assert (
            RoleViewService.can_access_endpoint(StaffRole.FACULTY, "schedules")
            is True
        )  # Because can_view_own_schedule is True by default
        assert (
            RoleViewService.can_access_endpoint(StaffRole.FACULTY, "academic_blocks")
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.FACULTY, "compliance")
            is False
        )
        # But can access conflicts and swaps
        assert (
            RoleViewService.can_access_endpoint(StaffRole.FACULTY, "conflicts") is True
        )
        assert RoleViewService.can_access_endpoint(StaffRole.FACULTY, "swaps") is True

    def test_can_access_endpoint_resident_swap_and_conflict_access(self):
        """Test resident can access swaps and conflicts."""
        assert (
            RoleViewService.can_access_endpoint(StaffRole.RESIDENT, "schedules")
            is True
        )  # can_view_own_schedule
        assert (
            RoleViewService.can_access_endpoint(StaffRole.RESIDENT, "conflicts")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.RESIDENT, "swaps") is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.RESIDENT, "academic_blocks")
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.RESIDENT, "compliance")
            is False
        )

    def test_can_access_endpoint_clinical_staff_manifest_only(self):
        """Test clinical staff can only access manifest and call roster."""
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "manifest")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "call_roster")
            is True
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "schedules")
            is True
        )  # can_view_own_schedule
        assert (
            RoleViewService.can_access_endpoint(
                StaffRole.CLINICAL_STAFF, "academic_blocks"
            )
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "compliance")
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "conflicts")
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(StaffRole.CLINICAL_STAFF, "swaps")
            is False
        )

    def test_can_access_endpoint_unknown_category_returns_false(self):
        """Test unknown endpoint category returns False."""
        assert (
            RoleViewService.can_access_endpoint(StaffRole.ADMIN, "unknown_endpoint")
            is False
        )
        assert (
            RoleViewService.can_access_endpoint(
                StaffRole.COORDINATOR, "nonexistent_category"
            )
            is False
        )

    def test_can_access_endpoint_manifest_and_call_roster(self):
        """Test manifest and call_roster access for various roles."""
        # All roles should have manifest and call_roster access by default
        for role in [
            StaffRole.ADMIN,
            StaffRole.COORDINATOR,
            StaffRole.FACULTY,
            StaffRole.CLINICAL_STAFF,
            StaffRole.RESIDENT,
        ]:
            assert RoleViewService.can_access_endpoint(role, "manifest") is True
            assert RoleViewService.can_access_endpoint(role, "call_roster") is True

    # ========================================================================
    # Get Role Config Tests
    # ========================================================================

    def test_get_role_config_returns_correct_structure(self):
        """Test get_role_config returns RoleViewConfig with role and permissions."""
        config = RoleViewService.get_role_config(StaffRole.ADMIN)

        assert isinstance(config, RoleViewConfig)
        assert config.role == StaffRole.ADMIN
        assert isinstance(config.permissions, ViewPermissions)

    def test_get_role_config_admin(self):
        """Test get_role_config for admin role."""
        config = RoleViewService.get_role_config(StaffRole.ADMIN)

        assert config.role == StaffRole.ADMIN
        assert config.permissions.can_view_all_schedules is True
        assert config.permissions.can_view_compliance is True

    def test_get_role_config_coordinator(self):
        """Test get_role_config for coordinator role."""
        config = RoleViewService.get_role_config(StaffRole.COORDINATOR)

        assert config.role == StaffRole.COORDINATOR
        assert config.permissions.can_view_all_schedules is True
        assert config.permissions.can_view_compliance is False

    def test_get_role_config_faculty(self):
        """Test get_role_config for faculty role."""
        config = RoleViewService.get_role_config(StaffRole.FACULTY)

        assert config.role == StaffRole.FACULTY
        assert config.permissions.can_view_all_schedules is False
        assert config.permissions.can_manage_swaps is True

    def test_get_role_config_clinical_staff(self):
        """Test get_role_config for clinical staff role."""
        config = RoleViewService.get_role_config(StaffRole.CLINICAL_STAFF)

        assert config.role == StaffRole.CLINICAL_STAFF
        assert config.permissions.can_view_all_schedules is False
        assert config.permissions.can_view_manifest is True

    def test_get_role_config_resident(self):
        """Test get_role_config for resident role."""
        config = RoleViewService.get_role_config(StaffRole.RESIDENT)

        assert config.role == StaffRole.RESIDENT
        assert config.permissions.can_view_conflicts is True
        assert config.permissions.can_manage_swaps is True

    # ========================================================================
    # Edge Cases and Complex Scenarios
    # ========================================================================

    def test_filter_response_multiple_schedule_filters(self):
        """Test filtering schedules with both person_id and staff_id."""
        data = {
            "schedules": [
                {"id": 1, "person_id": 100},
                {"id": 2, "staff_id": 100},
                {"id": 3, "person_id": 200, "staff_id": 200},
                {"id": 4, "person_id": 100, "staff_id": 200},
            ]
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.FACULTY, user_id=100
        )

        # Should match items where person_id=100 OR staff_id=100
        assert len(filtered["schedules"]) == 3
        assert filtered["schedules"][0]["id"] == 1
        assert filtered["schedules"][1]["id"] == 2
        assert filtered["schedules"][2]["id"] == 4

    def test_filter_response_does_not_mutate_original(self):
        """Test that filtering doesn't mutate the original data dictionary."""
        data = {
            "schedules": [{"id": 1}, {"id": 2}],
            "compliance": {"status": "compliant"},
        }
        original_keys = set(data.keys())

        RoleViewService.filter_response_for_role(data, StaffRole.COORDINATOR)

        # Original data should be unchanged
        assert set(data.keys()) == original_keys
        assert "compliance" in data

    def test_filter_schedule_list_does_not_mutate_original(self):
        """Test that filtering doesn't mutate the original schedule list."""
        schedules = [
            {"id": 1, "person_id": 100},
            {"id": 2, "person_id": 200},
        ]
        original_length = len(schedules)

        RoleViewService.filter_schedule_list(schedules, StaffRole.FACULTY, user_id=100)

        # Original list should be unchanged
        assert len(schedules) == original_length

    def test_filter_response_clinical_staff_with_empty_allowed_fields(self):
        """Test clinical staff filtering when allowed fields are missing."""
        data = {
            "schedules": [{"id": 1}],
            "academic_blocks": [{"block": 1}],
        }

        filtered = RoleViewService.filter_response_for_role(
            data, StaffRole.CLINICAL_STAFF
        )

        # Should be empty since no allowed fields present
        assert filtered == {}

    def test_permissions_hierarchy(self):
        """Test permissions hierarchy across roles."""
        admin_perms = RoleViewService.get_permissions(StaffRole.ADMIN)
        coordinator_perms = RoleViewService.get_permissions(StaffRole.COORDINATOR)
        faculty_perms = RoleViewService.get_permissions(StaffRole.FACULTY)
        clinical_perms = RoleViewService.get_permissions(StaffRole.CLINICAL_STAFF)

        # Admin should have more permissions than coordinator
        assert admin_perms.can_view_compliance is True
        assert coordinator_perms.can_view_compliance is False

        # Coordinator should have more schedule access than faculty
        assert coordinator_perms.can_view_all_schedules is True
        assert faculty_perms.can_view_all_schedules is False

        # Faculty should have swap management, clinical staff should not
        assert faculty_perms.can_manage_swaps is True
        assert clinical_perms.can_manage_swaps is False

    def test_all_roles_have_defined_permissions(self):
        """Test that all StaffRole enum values have defined permissions."""
        for role in StaffRole:
            permissions = RoleViewService.get_permissions(role)
            assert isinstance(permissions, ViewPermissions)
