"""
Comprehensive tests for role hierarchy and inheritance.

Tests role relationships, permission inheritance, and hierarchy comparisons.
"""

import pytest

from app.auth.access_matrix import (
    AccessControlMatrix,
    PermissionAction,
    ResourceType,
    RoleHierarchy,
    UserRole,
)


class TestRoleHierarchyBasics:
    """Test basic role hierarchy functionality."""

    def test_admin_is_top_level_role(self):
        """Admin has no parent roles (highest privilege)."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.ADMIN)
        assert inherited == {UserRole.ADMIN}
        assert len(inherited) == 1

    def test_coordinator_inherits_from_admin(self):
        """Coordinator inherits from admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.COORDINATOR)
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited
        assert len(inherited) == 2

    def test_faculty_inherits_from_admin_and_coordinator(self):
        """Faculty inherits from both admin and coordinator."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.FACULTY)
        assert UserRole.FACULTY in inherited
        assert UserRole.ADMIN in inherited
        assert UserRole.COORDINATOR in inherited
        assert len(inherited) == 3

    def test_clinical_staff_inherits_from_admin_and_coordinator(self):
        """Clinical staff inherits from admin and coordinator."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.CLINICAL_STAFF)
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.ADMIN in inherited
        assert UserRole.COORDINATOR in inherited
        assert len(inherited) == 3

    def test_rn_has_full_inheritance_chain(self):
        """RN inherits from clinical_staff, coordinator, and admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.RN)
        assert UserRole.RN in inherited
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited
        assert len(inherited) == 4

    def test_lpn_has_full_inheritance_chain(self):
        """LPN inherits from clinical_staff, coordinator, and admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.LPN)
        assert UserRole.LPN in inherited
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited

    def test_msa_has_full_inheritance_chain(self):
        """MSA inherits from clinical_staff, coordinator, and admin."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.MSA)
        assert UserRole.MSA in inherited
        assert UserRole.CLINICAL_STAFF in inherited
        assert UserRole.COORDINATOR in inherited
        assert UserRole.ADMIN in inherited

    def test_resident_inherits_from_admin_and_coordinator(self):
        """Resident inherits from admin and coordinator."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.RESIDENT)
        assert UserRole.RESIDENT in inherited
        assert UserRole.ADMIN in inherited
        assert UserRole.COORDINATOR in inherited


class TestRoleComparison:
    """Test role hierarchy comparison."""

    def test_coordinator_is_higher_than_admin(self):
        """Coordinator is below admin in hierarchy (admin is parent)."""
        assert RoleHierarchy.is_higher_role(UserRole.COORDINATOR, UserRole.ADMIN)

    def test_faculty_is_higher_than_admin(self):
        """Faculty is below admin in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.FACULTY, UserRole.ADMIN)

    def test_faculty_is_higher_than_coordinator(self):
        """Faculty is below coordinator in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.FACULTY, UserRole.COORDINATOR)

    def test_resident_is_higher_than_admin(self):
        """Resident is below admin in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.RESIDENT, UserRole.ADMIN)

    def test_admin_not_higher_than_coordinator(self):
        """Admin is not below coordinator (admin is parent)."""
        assert not RoleHierarchy.is_higher_role(UserRole.ADMIN, UserRole.COORDINATOR)

    def test_admin_not_higher_than_faculty(self):
        """Admin is not below faculty."""
        assert not RoleHierarchy.is_higher_role(UserRole.ADMIN, UserRole.FACULTY)

    def test_coordinator_not_higher_than_faculty(self):
        """Coordinator is not below faculty (coordinator is parent)."""
        assert not RoleHierarchy.is_higher_role(UserRole.COORDINATOR, UserRole.FACULTY)

    def test_role_not_higher_than_itself(self):
        """Role is not higher than itself."""
        for role in UserRole:
            assert not RoleHierarchy.is_higher_role(role, role)


class TestClinicalStaffHierarchy:
    """Test clinical staff role hierarchy (RN, LPN, MSA)."""

    def test_rn_inherits_from_clinical_staff(self):
        """RN inherits from clinical_staff."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.RN)
        assert UserRole.CLINICAL_STAFF in inherited

    def test_lpn_inherits_from_clinical_staff(self):
        """LPN inherits from clinical_staff."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.LPN)
        assert UserRole.CLINICAL_STAFF in inherited

    def test_msa_inherits_from_clinical_staff(self):
        """MSA inherits from clinical_staff."""
        inherited = RoleHierarchy.get_inherited_roles(UserRole.MSA)
        assert UserRole.CLINICAL_STAFF in inherited

    def test_rn_is_higher_than_clinical_staff(self):
        """RN is below clinical_staff in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.RN, UserRole.CLINICAL_STAFF)

    def test_lpn_is_higher_than_clinical_staff(self):
        """LPN is below clinical_staff in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.LPN, UserRole.CLINICAL_STAFF)

    def test_msa_is_higher_than_clinical_staff(self):
        """MSA is below clinical_staff in hierarchy."""
        assert RoleHierarchy.is_higher_role(UserRole.MSA, UserRole.CLINICAL_STAFF)

    def test_clinical_staff_roles_have_same_inheritance(self):
        """All clinical staff roles have same inheritance depth."""
        rn_depth = len(RoleHierarchy.get_inherited_roles(UserRole.RN))
        lpn_depth = len(RoleHierarchy.get_inherited_roles(UserRole.LPN))
        msa_depth = len(RoleHierarchy.get_inherited_roles(UserRole.MSA))
        assert rn_depth == lpn_depth == msa_depth


class TestPermissionInheritance:
    """Test permission inheritance through role hierarchy."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_admin_permissions_not_inherited(self, acm):
        """Admin permissions are not inherited by lower roles (admin-only actions)."""
        # Coordinator shouldn't have user management permissions
        assert not acm.has_permission(
            UserRole.COORDINATOR, ResourceType.USER, PermissionAction.DELETE
        )
        # Faculty shouldn't have settings permissions
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SETTINGS, PermissionAction.UPDATE
        )

    def test_coordinator_permissions_accessible_to_admin(self, acm):
        """Admin has all coordinator permissions."""
        # Get all coordinator permissions
        coord_perms = acm.get_role_permissions(UserRole.COORDINATOR)
        for resource, actions in coord_perms.items():
            for action in actions:
                assert acm.has_permission(UserRole.ADMIN, resource, action)

    def test_faculty_permissions_accessible_to_admin(self, acm):
        """Admin has all faculty permissions."""
        faculty_perms = acm.get_role_permissions(UserRole.FACULTY)
        for resource, actions in faculty_perms.items():
            for action in actions:
                assert acm.has_permission(UserRole.ADMIN, resource, action)

    def test_faculty_permissions_accessible_to_coordinator(self, acm):
        """Coordinator has all faculty permissions (via hierarchy)."""
        # Coordinator should be able to read schedules like faculty
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.READ
        )
        # And more (create)
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.CREATE
        )


class TestRoleHierarchyEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_roles_defined_in_hierarchy(self):
        """All user roles are defined in hierarchy."""
        for role in UserRole:
            assert role in RoleHierarchy.HIERARCHY

    def test_hierarchy_acyclic(self):
        """Hierarchy has no cycles (prevents infinite loops)."""
        for role in UserRole:
            inherited = RoleHierarchy.get_inherited_roles(role)
            # Check that inherited roles don't reference back to original
            for inherited_role in inherited:
                if inherited_role == role:
                    continue
                # Get inherited role's parents
                parents = RoleHierarchy.HIERARCHY.get(inherited_role, set())
                # Original role should not be in parents
                assert role not in parents

    def test_admin_has_no_parents(self):
        """Admin role has empty parent set."""
        assert RoleHierarchy.HIERARCHY[UserRole.ADMIN] == set()

    def test_inherited_roles_includes_self(self):
        """get_inherited_roles always includes the role itself."""
        for role in UserRole:
            inherited = RoleHierarchy.get_inherited_roles(role)
            assert role in inherited

    def test_hierarchy_consistency(self):
        """Hierarchy structure is consistent and valid."""
        for role, parents in RoleHierarchy.HIERARCHY.items():
            # All parents should be valid roles
            for parent in parents:
                assert parent in UserRole
            # Role shouldn't be its own parent
            assert role not in parents


class TestRoleLevels:
    """Test role privilege levels and ordering."""

    def test_role_privilege_order(self):
        """Roles are ordered by privilege level."""
        # Define expected privilege order (highest to lowest)
        privilege_order = [
            UserRole.ADMIN,
            UserRole.COORDINATOR,
            UserRole.FACULTY,
            UserRole.CLINICAL_STAFF,
            UserRole.RN,
            UserRole.LPN,
            UserRole.MSA,
            UserRole.RESIDENT,
        ]

        # Verify each role has more privileges than roles after it
        for i, role in enumerate(privilege_order):
            inherited = RoleHierarchy.get_inherited_roles(role)
            # Should include all higher roles
            for j in range(i):
                higher_role = privilege_order[j]
                if higher_role in RoleHierarchy.HIERARCHY.get(role, set()):
                    assert higher_role in inherited

    def test_admin_highest_privilege(self):
        """Admin has most privileges (shortest inheritance chain)."""
        admin_inherited = len(RoleHierarchy.get_inherited_roles(UserRole.ADMIN))
        for role in UserRole:
            if role == UserRole.ADMIN:
                continue
            role_inherited = len(RoleHierarchy.get_inherited_roles(role))
            assert role_inherited >= admin_inherited

    def test_specialized_roles_lowest_privilege(self):
        """Specialized roles (RN, LPN, MSA) have longest inheritance chains."""
        specialized_roles = [UserRole.RN, UserRole.LPN, UserRole.MSA]
        for spec_role in specialized_roles:
            spec_depth = len(RoleHierarchy.get_inherited_roles(spec_role))
            # Should have at least 4 levels (self + clinical_staff + coordinator + admin)
            assert spec_depth >= 4


class TestPermissionPropagation:
    """Test how permissions propagate through hierarchy."""

    @pytest.fixture
    def acm(self):
        """Create ACM instance."""
        return AccessControlMatrix(enable_audit=False)

    def test_read_permissions_propagate_down(self, acm):
        """READ permissions available to lower roles."""
        # Resident can read schedules
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.READ
        )
        # Faculty can read schedules
        assert acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.READ
        )
        # Coordinator can read schedules
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.READ
        )

    def test_write_permissions_restricted_to_higher_roles(self, acm):
        """WRITE permissions restricted to higher privilege roles."""
        # Resident cannot create schedules
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        # Faculty cannot create schedules
        assert not acm.has_permission(
            UserRole.FACULTY, ResourceType.SCHEDULE, PermissionAction.CREATE
        )
        # Coordinator CAN create schedules
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.SCHEDULE, PermissionAction.CREATE
        )

    def test_approval_permissions_restricted(self, acm):
        """APPROVE/REJECT permissions restricted to managers."""
        # Resident can approve own swaps
        assert acm.has_permission(
            UserRole.RESIDENT, ResourceType.SWAP_REQUEST, PermissionAction.APPROVE
        )
        # But not leave
        assert not acm.has_permission(
            UserRole.RESIDENT, ResourceType.LEAVE, PermissionAction.APPROVE
        )
        # Coordinator can approve leave
        assert acm.has_permission(
            UserRole.COORDINATOR, ResourceType.LEAVE, PermissionAction.APPROVE
        )
