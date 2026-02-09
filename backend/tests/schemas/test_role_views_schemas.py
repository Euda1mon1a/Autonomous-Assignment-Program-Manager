"""Tests for role-based view schemas (enum, defaults, model composition)."""

from app.schemas.role_views import StaffRole, ViewPermissions, RoleViewConfig


class TestStaffRole:
    def test_values(self):
        assert StaffRole.ADMIN.value == "admin"
        assert StaffRole.COORDINATOR.value == "coordinator"
        assert StaffRole.FACULTY.value == "faculty"
        assert StaffRole.CLINICAL_STAFF.value == "clinical_staff"
        assert StaffRole.RESIDENT.value == "resident"

    def test_count(self):
        assert len(StaffRole) == 5

    def test_is_str(self):
        assert isinstance(StaffRole.ADMIN, str)


class TestViewPermissions:
    def test_defaults(self):
        r = ViewPermissions()
        assert r.can_view_all_schedules is False
        assert r.can_view_own_schedule is True
        assert r.can_view_manifest is True
        assert r.can_view_call_roster is True
        assert r.can_view_academic_blocks is False
        assert r.can_view_compliance is False
        assert r.can_view_conflicts is False
        assert r.can_manage_swaps is False

    def test_admin_overrides(self):
        r = ViewPermissions(
            can_view_all_schedules=True,
            can_view_academic_blocks=True,
            can_view_compliance=True,
            can_view_conflicts=True,
            can_manage_swaps=True,
        )
        assert r.can_view_all_schedules is True
        assert r.can_manage_swaps is True


class TestRoleViewConfig:
    def test_valid(self):
        perms = ViewPermissions(can_view_all_schedules=True)
        r = RoleViewConfig(role=StaffRole.ADMIN, permissions=perms)
        assert r.role == StaffRole.ADMIN
        assert r.permissions.can_view_all_schedules is True
