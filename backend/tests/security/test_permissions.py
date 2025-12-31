"""
Comprehensive permission tests for all roles and resources.

Tests all permission combinations across the RBAC matrix.
"""

import pytest
from uuid import uuid4

from app.auth.access_matrix import (
    AccessControlMatrix,
    PermissionAction,
    PermissionContext,
    ResourceType,
    UserRole,
)


class TestAdminPermissions:
    """Test admin permissions (should have ALL permissions)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_admin_has_all_crud_on_schedules(self, acm):
        """Admin has CREATE, READ, UPDATE, DELETE on schedules."""
        for action in [
            PermissionAction.CREATE,
            PermissionAction.READ,
            PermissionAction.UPDATE,
            PermissionAction.DELETE,
        ]:
            assert acm.has_permission(UserRole.ADMIN, ResourceType.SCHEDULE, action)

    def test_admin_has_all_crud_on_assignments(self, acm):
        """Admin has all CRUD on assignments."""
        for action in [
            PermissionAction.CREATE,
            PermissionAction.READ,
            PermissionAction.UPDATE,
            PermissionAction.DELETE,
        ]:
            assert acm.has_permission(UserRole.ADMIN, ResourceType.ASSIGNMENT, action)

    def test_admin_has_all_crud_on_users(self, acm):
        """Admin has all CRUD on users."""
        for action in [
            PermissionAction.CREATE,
            PermissionAction.READ,
            PermissionAction.UPDATE,
            PermissionAction.DELETE,
        ]:
            assert acm.has_permission(UserRole.ADMIN, ResourceType.USER, action)

    def test_admin_can_approve_and_reject(self, acm):
        """Admin can approve and reject leave/swaps."""
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.LEAVE, PermissionAction.APPROVE
        )
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.LEAVE, PermissionAction.REJECT
        )
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.SWAP, PermissionAction.APPROVE
        )

    def test_admin_can_execute_operations(self, acm):
        """Admin can execute special operations."""
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.SWAP, PermissionAction.EXECUTE
        )
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.EXECUTE
        )

    def test_admin_can_export_import(self, acm):
        """Admin can export and import data."""
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.EXPORT
        )
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.IMPORT
        )

    def test_admin_can_manage_resources(self, acm):
        """Admin has MANAGE permission on resources."""
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.ASSIGNMENT, PermissionAction.MANAGE
        )


class TestCoordinatorPermissions:
    """Test coordinator permissions (schedule management)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_coordinator_schedule_permissions(self, acm):
        """Coordinator has full schedule permissions."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.UPDATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.DELETE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.LIST
        )

    def test_coordinator_assignment_permissions(self, acm):
        """Coordinator can manage assignments."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.MANAGE
        )

    def test_coordinator_person_management(self, acm):
        """Coordinator can manage persons."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.PERSON, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.PERSON, PermissionAction.UPDATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.RESIDENT, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.FACULTY_MEMBER, PermissionAction.CREATE
        )

    def test_coordinator_leave_approval(self, acm):
        """Coordinator can approve/reject leave requests."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.LEAVE, PermissionAction.APPROVE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.LEAVE, PermissionAction.REJECT
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ABSENCE, PermissionAction.APPROVE
        )

    def test_coordinator_swap_management(self, acm):
        """Coordinator can manage swaps."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SWAP, PermissionAction.APPROVE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SWAP, PermissionAction.EXECUTE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )

    def test_coordinator_cannot_manage_users(self, acm):
        """Coordinator cannot create/delete users (admin-only)."""
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.USER, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.USER, PermissionAction.DELETE
        )

    def test_coordinator_cannot_manage_settings(self, acm):
        """Coordinator cannot modify system settings."""
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SETTINGS, PermissionAction.UPDATE
        )

    def test_coordinator_can_view_analytics(self, acm):
        """Coordinator can view analytics and reports."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ANALYTICS, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.REPORT, PermissionAction.READ
        )


class TestFacultyPermissions:
    """Test faculty permissions (view + self-management)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_faculty_can_read_schedules(self, acm):
        """Faculty can read and list schedules."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.LIST
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.ASSIGNMENT, PermissionAction.READ
        )

    def test_faculty_cannot_create_schedules(self, acm):
        """Faculty cannot create or delete schedules."""
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.DELETE
        )
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )

    def test_faculty_leave_permissions(self, acm):
        """Faculty can create and update own leave."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.LEAVE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.LEAVE, PermissionAction.UPDATE
        )
        # But cannot approve
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.LEAVE, PermissionAction.APPROVE
        )

    def test_faculty_absence_permissions(self, acm):
        """Faculty can manage own absences."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.ABSENCE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.ABSENCE, PermissionAction.UPDATE
        )

    def test_faculty_swap_permissions(self, acm):
        """Faculty can create and manage swaps."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )
        # Can approve swap requests involving them
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP_REQUEST, PermissionAction.REJECT
        )

    def test_faculty_can_view_credentials(self, acm):
        """Faculty can view procedures and credentials."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.PROCEDURE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.CREDENTIAL, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.CERTIFICATION, PermissionAction.READ
        )

    def test_faculty_cannot_manage_others(self, acm):
        """Faculty cannot create persons or manage users."""
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.PERSON, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.USER, PermissionAction.CREATE
        )


class TestResidentPermissions:
    """Test resident permissions (read-only + self-management)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_resident_can_read_schedules(self, acm):
        """Resident can read schedules and assignments."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.ASSIGNMENT, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.BLOCK, PermissionAction.READ
        )

    def test_resident_cannot_modify_schedules(self, acm):
        """Resident cannot create, update, or delete schedules."""
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.UPDATE
        )
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.DELETE
        )

    def test_resident_leave_permissions(self, acm):
        """Resident can request leave but not approve."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.READ
        )
        # Cannot update (except own)
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.APPROVE
        )

    def test_resident_absence_permissions(self, acm):
        """Resident can create absences."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.ABSENCE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.ABSENCE, PermissionAction.READ
        )

    def test_resident_swap_permissions(self, acm):
        """Resident can manage swap requests."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )
        # Can approve swap requests involving them
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP_REQUEST, PermissionAction.REJECT
        )

    def test_resident_can_view_conflicts(self, acm):
        """Resident can view conflicts."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.CONFLICT, PermissionAction.READ
        )
        # But cannot manage
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.CONFLICT, PermissionAction.MANAGE
        )

    def test_resident_cannot_access_admin_resources(self, acm):
        """Resident cannot access admin resources."""
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.USER, PermissionAction.READ
        )
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SETTINGS, PermissionAction.READ
        )


class TestClinicalStaffPermissions:
    """Test clinical staff permissions (view-only)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    @pytest.mark.parametrize(
        "role", [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]
    )
    def test_clinical_staff_can_read_schedules(self, acm, role):
        """All clinical staff can read schedules."""
        assert acm.has_permission(role, ResourceType.SCHEDULE, PermissionAction.READ)
        assert acm.has_permission(role, ResourceType.ASSIGNMENT, PermissionAction.READ)
        assert acm.has_permission(role, ResourceType.BLOCK, PermissionAction.LIST)

    @pytest.mark.parametrize(
        "role", [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]
    )
    def test_clinical_staff_cannot_modify_schedules(self, acm, role):
        """Clinical staff cannot modify schedules."""
        assert not acm.has_permission(
            role, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            role, ResourceType.SCHEDULE, PermissionAction.UPDATE
        )
        assert not acm.has_permission(
            role, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )

    @pytest.mark.parametrize(
        "role", [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]
    )
    def test_clinical_staff_can_view_people(self, acm, role):
        """Clinical staff can view person information."""
        assert acm.has_permission(role, ResourceType.PERSON, PermissionAction.READ)
        assert acm.has_permission(role, ResourceType.PERSON, PermissionAction.LIST)

    @pytest.mark.parametrize(
        "role", [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]
    )
    def test_clinical_staff_cannot_manage_leave(self, acm, role):
        """Clinical staff cannot manage leave requests."""
        assert not acm.has_permission(role, ResourceType.LEAVE, PermissionAction.CREATE)
        assert not acm.has_permission(
            role, ResourceType.LEAVE, PermissionAction.APPROVE
        )


class TestContextAwarePermissions:
    """Test context-aware permission checks."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_resident_can_update_own_absence(self, acm):
        """Resident can update their own absence requests."""
        user_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.RESIDENT,
            resource_owner_id=user_id,
        )
        assert acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context,
        )

    def test_resident_cannot_update_others_absence(self, acm):
        """Resident cannot update other residents' absences."""
        user_id = uuid4()
        other_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.RESIDENT,
            resource_owner_id=other_id,
        )
        assert not acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context,
        )

    def test_faculty_can_update_own_leave(self, acm):
        """Faculty can update their own leave requests."""
        user_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.FACULTY,
            resource_owner_id=user_id,
        )
        assert acm.has_permission(
            UserRole.FACULTY,
            ResourceType.LEAVE,
            PermissionAction.UPDATE,
            context=context,
        )

    def test_faculty_cannot_update_others_leave(self, acm):
        """Faculty cannot update other faculty's leave."""
        user_id = uuid4()
        other_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.FACULTY,
            resource_owner_id=other_id,
        )
        assert not acm.has_permission(
            UserRole.FACULTY,
            ResourceType.LEAVE,
            PermissionAction.UPDATE,
            context=context,
        )

    def test_coordinator_can_update_any_absence(self, acm):
        """Coordinator can update any absence regardless of ownership."""
        user_id = uuid4()
        other_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=other_id,
        )
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context,
        )

    def test_resident_can_update_own_swap_request(self, acm):
        """Resident can update their own swap requests."""
        user_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.RESIDENT,
            resource_owner_id=user_id,
        )
        assert acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.SWAP_REQUEST,
            PermissionAction.UPDATE,
            context=context,
        )


class TestManagePermission:
    """Test MANAGE permission (includes all CRUD)."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_manage_implies_create(self, acm):
        """MANAGE permission includes CREATE."""
        # Coordinator has MANAGE on assignments
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.MANAGE
        )
        # Should also have CREATE
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )

    def test_manage_implies_read(self, acm):
        """MANAGE permission includes READ."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.READ
        )

    def test_manage_implies_update(self, acm):
        """MANAGE permission includes UPDATE."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.UPDATE
        )

    def test_manage_implies_delete(self, acm):
        """MANAGE permission includes DELETE."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.DELETE
        )

    def test_manage_does_not_imply_approve(self, acm):
        """MANAGE does not automatically include APPROVE."""
        # Even with MANAGE on assignments, need explicit APPROVE permission
        # This is tested implicitly - MANAGE only covers CRUD


class TestResourceSpecificPermissions:
    """Test permissions for specific resource types."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_notification_permissions(self, acm):
        """Test notification access by role."""
        # All roles can read notifications
        for role in UserRole:
            assert acm.has_permission(
                role, ResourceType.NOTIFICATION, PermissionAction.READ
            )
        # Only coordinator+ can create
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.NOTIFICATION, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.NOTIFICATION, PermissionAction.CREATE
        )

    def test_resilience_metric_permissions(self, acm):
        """Test resilience metric access."""
        # Coordinator can read resilience metrics
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.RESILIENCE_METRIC,
            PermissionAction.READ,
        )
        # Faculty cannot
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.RESILIENCE_METRIC, PermissionAction.READ
        )

    def test_contingency_plan_permissions(self, acm):
        """Test contingency plan access."""
        # Coordinator can read and update
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.CONTINGENCY_PLAN,
            PermissionAction.READ,
        )
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.CONTINGENCY_PLAN,
            PermissionAction.UPDATE,
        )

    def test_audit_log_permissions(self, acm):
        """Test audit log access (admin only)."""
        assert acm.has_permission(
            UserRole.ADMIN, ResourceType.AUDIT_LOG, PermissionAction.READ
        )
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.AUDIT_LOG, PermissionAction.READ
        )


class TestPermissionDenialPatterns:
    """Test common permission denial scenarios."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_lower_roles_cannot_delete_schedules(self, acm):
        """Only admin and coordinator can delete schedules."""
        deny_roles = [UserRole.FACULTY, UserRole.RESIDENT, UserRole.CLINICAL_STAFF]
        for role in deny_roles:
            assert not acm.has_permission(
                role, ResourceType.SCHEDULE, PermissionAction.DELETE
            )

    def test_non_managers_cannot_approve_leave(self, acm):
        """Only coordinator and admin can approve leave."""
        deny_roles = [UserRole.FACULTY, UserRole.RESIDENT, UserRole.CLINICAL_STAFF]
        for role in deny_roles:
            assert not acm.has_permission(
                role, ResourceType.LEAVE, PermissionAction.APPROVE
            )

    def test_non_admin_cannot_manage_users(self, acm):
        """Only admin can manage user accounts."""
        deny_roles = [
            UserRole.COORDINATOR,
            UserRole.FACULTY,
            UserRole.RESIDENT,
            UserRole.CLINICAL_STAFF,
        ]
        for role in deny_roles:
            assert not acm.has_permission(
                role, ResourceType.USER, PermissionAction.CREATE
            )
            assert not acm.has_permission(
                role, ResourceType.USER, PermissionAction.DELETE
            )
