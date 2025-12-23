"""
Tests for the Access Control Matrix (RBAC).

Tests all aspects of the access control system including:
- Static permission checks
- Role hierarchy and inheritance
- Context-aware permissions
- Permission auditing
- Matrix export and visualization
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.auth.access_matrix import (
    AccessControlMatrix,
    PermissionAction,
    PermissionContext,
    PermissionDenied,
    ResourceType,
    RoleHierarchy,
    UserRole,
    get_acm,
    has_permission,
    require_permission,
)


class TestRoleHierarchy:
    """Test role hierarchy and inheritance."""

    def test_get_inherited_roles_admin(self):
        """Admin has no parent roles (top of hierarchy)."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.ADMIN)
        assert inherited == {UserRole.ADMIN}

    def test_get_inherited_roles_coordinator(self):
        """Coordinator inherits from admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.COORDINATOR)
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited

    def test_get_inherited_roles_faculty(self):
        """Faculty inherits from admin and coordinator."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.FACULTY)
        assert UserRole.FACULTY in inherited
        assert UserRole.ADMIN in inherited
        assert UserRole.COORDINATOR in inherited

    def test_get_inherited_roles_clinical_staff(self):
        """Clinical staff inherits from admin and coordinator."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.CLINICAL_STAFF)
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.ADMIN in inherited
        assert UserRole.COORDINATOR in inherited

    def test_get_inherited_roles_rn(self):
        """RN inherits from clinical_staff, coordinator, and admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.RN)
        assert UserRole.RN in inherited
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited

    def test_is_higher_role(self):
        """Test role hierarchy comparison."""
        assert RoleHierarchy.is_higher_role(UserRole.COORDINATOR, UserRole.ADMIN)
        assert RoleHierarchy.is_higher_role(UserRole.FACULTY, UserRole.ADMIN)
        assert RoleHierarchy.is_higher_role(UserRole.RESIDENT, UserRole.ADMIN)
        assert not RoleHierarchy.is_higher_role(UserRole.ADMIN, UserRole.COORDINATOR)


class TestAccessControlMatrix:
    """Test the Access Control Matrix."""

    @pytest.fixture
    def acm(self):
        """Create a fresh ACM instance for each test."""
        return AccessControlMatrix(enable_audit=True)

    # ========================================================================
    # Admin Permissions
    # ========================================================================

    def test_admin_has_all_permissions(self, acm):
        """Admin role has all permissions on all resources."""
        for resource in ResourceType:
            for action in PermissionAction:
                assert acm.has_permission(
                    UserRole.ADMIN, resource, action
                ), f"Admin should have {action} on {resource}"

    # ========================================================================
    # Coordinator Permissions
    # ========================================================================

    def test_coordinator_can_manage_schedules(self, acm):
        """Coordinator can create, read, update schedules."""
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

    def test_coordinator_can_manage_assignments(self, acm):
        """Coordinator can manage assignments."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.UPDATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.DELETE
        )

    def test_coordinator_can_approve_leave(self, acm):
        """Coordinator can approve and reject leave requests."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.LEAVE, PermissionAction.APPROVE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.LEAVE, PermissionAction.REJECT
        )

    def test_coordinator_can_manage_swaps(self, acm):
        """Coordinator can approve and execute swaps."""
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SWAP, PermissionAction.APPROVE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SWAP, PermissionAction.EXECUTE
        )

    def test_coordinator_cannot_manage_users(self, acm):
        """Coordinator cannot manage users (admin-only)."""
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.USER, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.USER, PermissionAction.DELETE
        )

    # ========================================================================
    # Faculty Permissions
    # ========================================================================

    def test_faculty_can_read_schedules(self, acm):
        """Faculty can read and list schedules."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.LIST
        )

    def test_faculty_cannot_create_schedules(self, acm):
        """Faculty cannot create schedules."""
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.DELETE
        )

    def test_faculty_can_manage_own_leave(self, acm):
        """Faculty can create and update leave requests."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.LEAVE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.LEAVE, PermissionAction.UPDATE
        )

    def test_faculty_can_manage_swaps(self, acm):
        """Faculty can create and manage swap requests."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )

    def test_faculty_can_view_procedures(self, acm):
        """Faculty can view procedures and credentials."""
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.PROCEDURE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.CREDENTIAL, PermissionAction.READ
        )

    # ========================================================================
    # Clinical Staff Permissions (RN, LPN, MSA)
    # ========================================================================

    def test_clinical_staff_can_read_schedules(self, acm):
        """Clinical staff can read schedules."""
        for role in [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]:
            assert acm.has_permission(
                role, ResourceType.SCHEDULE, PermissionAction.READ
            )
            assert acm.has_permission(
                role, ResourceType.ASSIGNMENT, PermissionAction.READ
            )

    def test_clinical_staff_cannot_modify_schedules(self, acm):
        """Clinical staff cannot modify schedules."""
        for role in [UserRole.CLINICAL_STAFF, UserRole.RN, UserRole.LPN, UserRole.MSA]:
            assert not acm.has_permission(
                role, ResourceType.SCHEDULE, PermissionAction.CREATE
            )
            assert not acm.has_permission(
                role, ResourceType.SCHEDULE, PermissionAction.UPDATE
            )

    def test_rn_inherits_clinical_staff_permissions(self, acm):
        """RN inherits all clinical_staff permissions."""
        # Both should have same permissions on schedules
        assert acm.has_permission(
            UserRole.RN, ResourceType.SCHEDULE, PermissionAction.READ
        ) == acm.has_permission(
            UserRole.CLINICAL_STAFF, ResourceType.SCHEDULE, PermissionAction.READ
        )

    # ========================================================================
    # Resident Permissions
    # ========================================================================

    def test_resident_can_read_own_schedule(self, acm):
        """Resident can read schedules."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.ASSIGNMENT, PermissionAction.READ
        )

    def test_resident_cannot_modify_schedules(self, acm):
        """Resident cannot modify schedules."""
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.UPDATE
        )

    def test_resident_can_request_leave(self, acm):
        """Resident can create leave requests."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.READ
        )

    def test_resident_cannot_approve_leave(self, acm):
        """Resident cannot approve leave."""
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.APPROVE
        )

    def test_resident_can_manage_swaps(self, acm):
        """Resident can create and manage swap requests."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )

    def test_resident_can_view_conflicts(self, acm):
        """Resident can view conflicts."""
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.CONFLICT, PermissionAction.READ
        )

    # ========================================================================
    # String Role/Resource/Action Support
    # ========================================================================

    def test_string_role_support(self, acm):
        """Permission checks work with string roles."""
        assert acm.has_permission(
            "admin", ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert acm.has_permission(
            "coordinator", ResourceType.SCHEDULE, PermissionAction.CREATE
        )

    def test_string_resource_support(self, acm):
        """Permission checks work with string resources."""
        assert acm.has_permission(UserRole.ADMIN, "schedule", PermissionAction.CREATE)

    def test_string_action_support(self, acm):
        """Permission checks work with string actions."""
        assert acm.has_permission(UserRole.ADMIN, ResourceType.SCHEDULE, "create")

    def test_invalid_string_role(self, acm):
        """Invalid string role returns False."""
        assert not acm.has_permission(
            "invalid_role", ResourceType.SCHEDULE, PermissionAction.READ
        )

    # ========================================================================
    # Context-Aware Permissions
    # ========================================================================

    def test_context_own_resource_resident(self, acm):
        """Resident can update own absence but not others'."""
        user_id = uuid4()
        other_user_id = uuid4()

        # Own resource
        context_own = PermissionContext(
            user_id=user_id,
            user_role=UserRole.RESIDENT,
            resource_owner_id=user_id,
        )
        assert acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context_own,
        )

        # Other's resource
        context_other = PermissionContext(
            user_id=user_id,
            user_role=UserRole.RESIDENT,
            resource_owner_id=other_user_id,
        )
        assert not acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context_other,
        )

    def test_context_coordinator_can_update_any(self, acm):
        """Coordinator can update any resource regardless of ownership."""
        user_id = uuid4()
        other_user_id = uuid4()

        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=other_user_id,
        )
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.ABSENCE,
            PermissionAction.UPDATE,
            context=context,
        )

    # ========================================================================
    # Permission Inheritance and Hierarchy
    # ========================================================================

    def test_manage_permission_includes_crud(self, acm):
        """MANAGE permission includes all CRUD operations."""
        # Coordinator has MANAGE on assignments
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.MANAGE
        )
        # Should also have individual CRUD permissions
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.READ
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.UPDATE
        )
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.ASSIGNMENT, PermissionAction.DELETE
        )

    # ========================================================================
    # Get Role Permissions
    # ========================================================================

    def test_get_role_permissions(self, acm):
        """Get all permissions for a role."""
        permissions = acm.get_role_permissions(UserRole.COORDINATOR)
        assert ResourceType.SCHEDULE in permissions
        assert PermissionAction.CREATE in permissions[ResourceType.SCHEDULE]

    def test_get_role_permissions_includes_inherited(self, acm):
        """Role permissions include inherited permissions from hierarchy."""
        permissions = acm.get_role_permissions(UserRole.COORDINATOR)
        # Coordinator should have some admin permissions via inheritance
        assert len(permissions) > 0

    def test_get_role_permissions_string_role(self, acm):
        """Get permissions with string role."""
        permissions = acm.get_role_permissions("coordinator")
        assert ResourceType.SCHEDULE in permissions

    # ========================================================================
    # Get Resource Permissions
    # ========================================================================

    def test_get_resource_permissions(self, acm):
        """Get all role permissions for a resource."""
        permissions = acm.get_resource_permissions(ResourceType.SCHEDULE)
        assert UserRole.ADMIN in permissions
        assert PermissionAction.CREATE in permissions[UserRole.ADMIN]

    def test_get_resource_permissions_string_resource(self, acm):
        """Get resource permissions with string resource."""
        permissions = acm.get_resource_permissions("schedule")
        assert UserRole.ADMIN in permissions

    # ========================================================================
    # Audit Logging
    # ========================================================================

    def test_audit_log_enabled(self, acm):
        """Audit log records permission checks."""
        acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert len(acm.audit_log) > 0
        entry = acm.audit_log[-1]
        assert entry.role == UserRole.ADMIN
        assert entry.resource == ResourceType.SCHEDULE
        assert entry.permission == PermissionAction.CREATE
        assert entry.result is True

    def test_audit_log_denied_permission(self, acm):
        """Audit log records denied permissions."""
        acm.has_permission(
            UserRole.RESIDENT, ResourceType.USER, PermissionAction.CREATE
        )
        entry = acm.audit_log[-1]
        assert entry.result is False

    def test_get_audit_log_filtered_by_role(self, acm):
        """Get audit log filtered by role."""
        acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.READ
        )

        admin_logs = acm.get_audit_log(role=UserRole.ADMIN)
        assert all(entry.role == UserRole.ADMIN for entry in admin_logs)

    def test_get_audit_log_filtered_by_resource(self, acm):
        """Get audit log filtered by resource."""
        acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        acm.has_permission(
            UserRole.ADMIN, ResourceType.ASSIGNMENT, PermissionAction.CREATE
        )

        schedule_logs = acm.get_audit_log(resource=ResourceType.SCHEDULE)
        assert all(entry.resource == ResourceType.SCHEDULE for entry in schedule_logs)

    def test_get_audit_log_with_limit(self, acm):
        """Get audit log with limit."""
        for _ in range(10):
            acm.has_permission(
                UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
            )

        logs = acm.get_audit_log(limit=5)
        assert len(logs) == 5

    def test_clear_audit_log(self, acm):
        """Clear audit log."""
        acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert len(acm.audit_log) > 0
        acm.clear_audit_log()
        assert len(acm.audit_log) == 0

    def test_audit_disabled(self):
        """ACM with audit disabled doesn't record logs."""
        acm = AccessControlMatrix(enable_audit=False)
        acm.has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert len(acm.audit_log) == 0

    # ========================================================================
    # Matrix Export
    # ========================================================================

    def test_export_matrix_json(self, acm):
        """Export matrix as JSON."""
        json_output = acm.export_matrix(format="json")
        data = json.loads(json_output)
        assert "admin" in data
        assert "schedule" in data["admin"]
        assert isinstance(data["admin"]["schedule"], list)

    def test_export_matrix_csv(self, acm):
        """Export matrix as CSV."""
        csv_output = acm.export_matrix(format="csv")
        lines = csv_output.split("\n")
        assert lines[0] == "Role,Resource,Actions"
        assert len(lines) > 1

    def test_export_matrix_markdown(self, acm):
        """Export matrix as Markdown."""
        md_output = acm.export_matrix(format="markdown")
        assert "# Access Control Matrix" in md_output
        assert "## Role Permissions" in md_output
        assert "### ADMIN" in md_output
        assert "| Resource | Actions |" in md_output

    def test_export_matrix_invalid_format(self, acm):
        """Invalid export format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            acm.export_matrix(format="invalid")


class TestGlobalACM:
    """Test global ACM instance and helpers."""

    def test_get_acm_singleton(self):
        """get_acm returns singleton instance."""
        acm1 = get_acm()
        acm2 = get_acm()
        assert acm1 is acm2

    def test_has_permission_global(self):
        """Global has_permission function works."""
        assert has_permission(
            UserRole.ADMIN, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        assert has_permission("admin", "schedule", "create")


class TestPermissionDenied:
    """Test PermissionDenied exception."""

    def test_permission_denied_message(self):
        """PermissionDenied exception has correct message."""
        exc = PermissionDenied(ResourceType.SCHEDULE, PermissionAction.CREATE)
        assert "schedule" in exc.detail.lower()
        assert "create" in exc.detail.lower()

    def test_permission_denied_custom_detail(self):
        """PermissionDenied can have custom detail."""
        exc = PermissionDenied(
            ResourceType.SCHEDULE,
            PermissionAction.CREATE,
            detail="Custom error message",
        )
        assert exc.detail == "Custom error message"

    def test_permission_denied_status_code(self):
        """PermissionDenied has 403 status code."""
        exc = PermissionDenied(ResourceType.SCHEDULE, PermissionAction.CREATE)
        assert exc.status_code == 403


class TestRequirePermissionDecorator:
    """Test require_permission decorator."""

    def test_decorator_with_permission(self):
        """Decorator allows access with permission."""
        from uuid import uuid4

        from app.models.user import User

        @require_permission(ResourceType.SCHEDULE, PermissionAction.READ)
        async def test_func(current_user: User):
            return "success"

        # Create mock user with admin role
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@test.com",
            hashed_password="fake",
            role="admin",
        )

        # Should work for admin
        import asyncio

        result = asyncio.run(test_func(current_user=user))
        assert result == "success"

    def test_decorator_without_permission(self):
        """Decorator denies access without permission."""
        from uuid import uuid4

        from app.models.user import User

        @require_permission(ResourceType.USER, PermissionAction.CREATE)
        async def test_func(current_user: User):
            return "success"

        # Create mock user with resident role (no user creation permission)
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@test.com",
            hashed_password="fake",
            role="resident",
        )

        # Should raise PermissionDenied
        import asyncio

        with pytest.raises(PermissionDenied):
            asyncio.run(test_func(current_user=user))

    def test_decorator_without_user(self):
        """Decorator requires authenticated user."""

        @require_permission(ResourceType.SCHEDULE, PermissionAction.READ)
        async def test_func():
            return "success"

        import asyncio

        with pytest.raises(PermissionDenied, match="Authentication required"):
            asyncio.run(test_func())


class TestPermissionContext:
    """Test PermissionContext model."""

    def test_permission_context_creation(self):
        """Create PermissionContext."""
        user_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.FACULTY,
            resource_owner_id=user_id,
        )
        assert context.user_id == user_id
        assert context.user_role == UserRole.FACULTY
        assert context.resource_owner_id == user_id

    def test_permission_context_defaults(self):
        """PermissionContext has sensible defaults."""
        user_id = uuid4()
        context = PermissionContext(
            user_id=user_id,
            user_role=UserRole.ADMIN,
        )
        assert context.resource_owner_id is None
        assert context.resource_metadata == {}
        assert context.ip_address is None
        assert isinstance(context.timestamp, datetime)

    def test_permission_context_metadata(self):
        """PermissionContext can store metadata."""
        context = PermissionContext(
            user_id=uuid4(),
            user_role=UserRole.COORDINATOR,
            resource_metadata={"department": "Medicine", "location": "Hospital A"},
        )
        assert context.resource_metadata["department"] == "Medicine"


class TestPermissionAuditEntry:
    """Test PermissionAuditEntry model."""

    def test_audit_entry_creation(self):
        """Create PermissionAuditEntry."""
        entry = PermissionAuditEntry(
            action="checked",
            role=UserRole.ADMIN,
            resource=ResourceType.SCHEDULE,
            permission=PermissionAction.CREATE,
            result=True,
        )
        assert entry.action == "checked"
        assert entry.role == UserRole.ADMIN
        assert entry.result is True

    def test_audit_entry_with_context(self):
        """PermissionAuditEntry can store context."""
        context = {"ip": "192.168.1.1", "session": "abc123"}
        entry = PermissionAuditEntry(
            action="granted",
            role=UserRole.COORDINATOR,
            resource=ResourceType.ASSIGNMENT,
            permission=PermissionAction.UPDATE,
            result=True,
            context=context,
            reason="Authorized by policy",
        )
        assert entry.context == context
        assert entry.reason == "Authorized by policy"
