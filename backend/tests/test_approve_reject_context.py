"""
Tests for APPROVE/REJECT context validation.

SECURITY REQUIREMENT: All approval actions must have proper context validation.
"""

from uuid import uuid4

import pytest

from app.auth.access_matrix import (
    AccessControlMatrix,
    PermissionAction,
    PermissionContext,
    ResourceType,
    UserRole,
)


class TestApprovalContextValidation:
    """Test context validation for APPROVE/REJECT actions."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance with audit enabled."""
        return AccessControlMatrix(enable_audit=True)

    # ========================================================================
    # Leave/Absence Approval Tests
    # ========================================================================

    def test_coordinator_approve_leave_with_valid_context(self, acm):
        """Coordinator can approve leave with valid context."""
        requester_id = uuid4()
        coordinator_id = uuid4()

        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=requester_id,
            resource_metadata={"department": "Medicine"},
        )

        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_coordinator_approve_leave_without_department(self, acm):
        """Coordinator CANNOT approve leave without department in metadata."""
        requester_id = uuid4()
        coordinator_id = uuid4()

        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=requester_id,
            resource_metadata={},  # Missing department
        )

        # Should fail validation
        assert not acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_coordinator_approve_leave_without_resource_owner(self, acm):
        """Coordinator CANNOT approve leave without resource_owner_id."""
        coordinator_id = uuid4()

        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=None,  # Missing
            resource_metadata={"department": "Medicine"},
        )

        # Should fail validation
        assert not acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_admin_approve_leave_bypasses_context_checks(self, acm):
        """Admin can approve leave without strict context validation."""
        admin_id = uuid4()

        # Minimal context - admin should still be allowed
        context = PermissionContext(
            user_id=admin_id,
            user_role=UserRole.ADMIN,
            resource_owner_id=uuid4(),
            resource_metadata={"department": "Medicine"},
        )

        assert acm.has_permission(
            UserRole.ADMIN,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
            context=context,
        )

    # ========================================================================
    # Swap Approval Tests
    # ========================================================================

    def test_coordinator_approve_swap_with_valid_context(self, acm):
        """Coordinator can approve swap with valid context."""
        requester_id = uuid4()
        target_id = uuid4()
        coordinator_id = uuid4()

        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=requester_id,
            resource_metadata={
                "requesting_user_id": str(requester_id),
                "target_user_id": str(target_id),
            },
        )

        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.SWAP,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_coordinator_approve_swap_missing_parties(self, acm):
        """Coordinator CANNOT approve swap without both parties in metadata."""
        coordinator_id = uuid4()

        # Missing target_user_id
        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=uuid4(),
            resource_metadata={
                "requesting_user_id": str(uuid4()),
                # Missing target_user_id
            },
        )

        assert not acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.SWAP,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_faculty_approve_swap_involved(self, acm):
        """Faculty can approve swap if they're involved in it."""
        faculty_id = uuid4()
        other_faculty_id = uuid4()

        context = PermissionContext(
            user_id=faculty_id,
            user_role=UserRole.FACULTY,
            resource_owner_id=faculty_id,
            resource_metadata={
                "requesting_user_id": str(faculty_id),  # Faculty is involved
                "target_user_id": str(other_faculty_id),
            },
        )

        assert acm.has_permission(
            UserRole.FACULTY,
            ResourceType.SWAP_REQUEST,
            PermissionAction.APPROVE,
            context=context,
        )

    def test_faculty_cannot_approve_swap_not_involved(self, acm):
        """Faculty CANNOT approve swap if they're not involved."""
        faculty_id = uuid4()
        requester_id = uuid4()
        target_id = uuid4()

        context = PermissionContext(
            user_id=faculty_id,
            user_role=UserRole.FACULTY,
            resource_owner_id=requester_id,
            resource_metadata={
                "requesting_user_id": str(requester_id),
                "target_user_id": str(target_id),
                # Faculty not in either party
            },
        )

        assert not acm.has_permission(
            UserRole.FACULTY,
            ResourceType.SWAP_REQUEST,
            PermissionAction.APPROVE,
            context=context,
        )

    # ========================================================================
    # Reject Action Tests (same validation as APPROVE)
    # ========================================================================

    def test_reject_requires_same_context_as_approve(self, acm):
        """REJECT action requires same context validation as APPROVE."""
        coordinator_id = uuid4()
        requester_id = uuid4()

        # Valid context
        valid_context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=requester_id,
            resource_metadata={"department": "Medicine"},
        )

        # REJECT should work with valid context
        assert acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.REJECT,
            context=valid_context,
        )

        # Invalid context (missing department)
        invalid_context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=requester_id,
            resource_metadata={},  # Missing department
        )

        # REJECT should fail with invalid context
        assert not acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.REJECT,
            context=invalid_context,
        )

    # ========================================================================
    # Audit Log Tests
    # ========================================================================

    def test_approval_denial_logged(self, acm):
        """Failed approval attempts are logged in audit log."""
        coordinator_id = uuid4()

        # Attempt approval without proper context
        context = PermissionContext(
            user_id=coordinator_id,
            user_role=UserRole.COORDINATOR,
            resource_owner_id=None,  # Missing - will fail
            resource_metadata={"department": "Medicine"},
        )

        result = acm.has_permission(
            UserRole.COORDINATOR,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
            context=context,
        )

        assert not result
        assert len(acm.audit_log) > 0
        # Check that the denial was logged
        last_entry = acm.audit_log[-1]
        assert last_entry.action == "checked"
        assert last_entry.result is False
        assert last_entry.permission == PermissionAction.APPROVE


class TestRolePermissionIsolation:
    """Test that roles don't inherit permissions they shouldn't have."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_faculty_cannot_approve_leave(self, acm):
        """Faculty does NOT have leave approval permission (no coordinator inheritance)."""
        # Faculty should NOT be able to approve leave
        assert not acm.has_permission(
            UserRole.FACULTY,
            ResourceType.LEAVE,
            PermissionAction.APPROVE,
        )

    def test_faculty_cannot_create_schedules(self, acm):
        """Faculty cannot create schedules (no coordinator inheritance)."""
        assert not acm.has_permission(
            UserRole.FACULTY,
            ResourceType.SCHEDULE,
            PermissionAction.CREATE,
        )

    def test_faculty_cannot_delete_assignments(self, acm):
        """Faculty cannot delete assignments (no coordinator inheritance)."""
        assert not acm.has_permission(
            UserRole.FACULTY,
            ResourceType.ASSIGNMENT,
            PermissionAction.DELETE,
        )

    def test_resident_cannot_approve_swaps(self, acm):
        """Residents cannot approve swaps (only SWAP_REQUEST approvals)."""
        # Resident can approve SWAP_REQUEST (between residents)
        assert acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.SWAP_REQUEST,
            PermissionAction.APPROVE,
        )

        # But CANNOT approve SWAP (coordinator-level resource)
        # Note: SWAP and SWAP_REQUEST have different permission rules
        assert not acm.has_permission(
            UserRole.RESIDENT,
            ResourceType.SWAP,
            PermissionAction.APPROVE,
        )

    def test_clinical_staff_cannot_approve_anything(self, acm):
        """Clinical staff cannot approve any resources."""
        for resource in [
            ResourceType.LEAVE,
            ResourceType.ABSENCE,
            ResourceType.SWAP,
            ResourceType.SCHEDULE,
        ]:
            assert not acm.has_permission(
                UserRole.CLINICAL_STAFF,
                resource,
                PermissionAction.APPROVE,
            )
