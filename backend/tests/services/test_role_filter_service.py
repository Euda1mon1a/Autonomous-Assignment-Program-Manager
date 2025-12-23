"""Tests for RoleFilterService."""

from datetime import date

import pytest

from app.services.role_filter_service import (
    ResourceType,
    RoleFilterService,
    UserRole,
)


class TestRoleFilterService:
    """Test suite for RoleFilterService."""

    def test_get_role_from_string(self):
        """Test converting string to UserRole enum."""
        assert RoleFilterService.get_role_from_string("admin") == UserRole.ADMIN
        assert (
            RoleFilterService.get_role_from_string("coordinator")
            == UserRole.COORDINATOR
        )
        assert RoleFilterService.get_role_from_string("faculty") == UserRole.FACULTY
        assert RoleFilterService.get_role_from_string("rn") == UserRole.RN
        assert RoleFilterService.get_role_from_string("lpn") == UserRole.LPN
        assert RoleFilterService.get_role_from_string("msa") == UserRole.MSA

        with pytest.raises(ValueError):
            RoleFilterService.get_role_from_string("invalid_role")

    def test_normalize_clinical_staff_role(self):
        """Test normalizing clinical staff roles."""
        assert (
            RoleFilterService.normalize_clinical_staff_role(UserRole.RN)
            == UserRole.CLINICAL_STAFF
        )
        assert (
            RoleFilterService.normalize_clinical_staff_role(UserRole.LPN)
            == UserRole.CLINICAL_STAFF
        )
        assert (
            RoleFilterService.normalize_clinical_staff_role(UserRole.MSA)
            == UserRole.CLINICAL_STAFF
        )
        assert (
            RoleFilterService.normalize_clinical_staff_role(UserRole.ADMIN)
            == UserRole.ADMIN
        )
        assert (
            RoleFilterService.normalize_clinical_staff_role(UserRole.FACULTY)
            == UserRole.FACULTY
        )

    def test_admin_permissions(self):
        """Test admin has access to everything."""
        assert RoleFilterService.can_access(ResourceType.SCHEDULES, UserRole.ADMIN)
        assert RoleFilterService.can_access(ResourceType.PEOPLE, UserRole.ADMIN)
        assert RoleFilterService.can_access(ResourceType.CONFLICTS, UserRole.ADMIN)
        assert RoleFilterService.can_access(ResourceType.USERS, UserRole.ADMIN)
        assert RoleFilterService.can_access(ResourceType.COMPLIANCE, UserRole.ADMIN)
        assert RoleFilterService.can_access(ResourceType.AUDIT, UserRole.ADMIN)
        assert RoleFilterService.can_access(
            ResourceType.ACADEMIC_BLOCKS, UserRole.ADMIN
        )

    def test_coordinator_permissions(self):
        """Test coordinator permissions."""
        assert RoleFilterService.can_access(
            ResourceType.SCHEDULES, UserRole.COORDINATOR
        )
        assert RoleFilterService.can_access(ResourceType.PEOPLE, UserRole.COORDINATOR)
        assert RoleFilterService.can_access(
            ResourceType.CONFLICTS, UserRole.COORDINATOR
        )
        assert not RoleFilterService.can_access(
            ResourceType.USERS, UserRole.COORDINATOR
        )
        assert not RoleFilterService.can_access(
            ResourceType.COMPLIANCE, UserRole.COORDINATOR
        )
        assert not RoleFilterService.can_access(
            ResourceType.AUDIT, UserRole.COORDINATOR
        )

    def test_faculty_permissions(self):
        """Test faculty permissions."""
        assert not RoleFilterService.can_access(
            ResourceType.SCHEDULES, UserRole.FACULTY
        )
        assert RoleFilterService.can_access(ResourceType.OWN_SCHEDULE, UserRole.FACULTY)
        assert RoleFilterService.can_access(ResourceType.SWAPS, UserRole.FACULTY)
        assert not RoleFilterService.can_access(ResourceType.PEOPLE, UserRole.FACULTY)
        assert not RoleFilterService.can_access(
            ResourceType.COMPLIANCE, UserRole.FACULTY
        )

    def test_clinical_staff_permissions(self):
        """Test clinical staff permissions (rn, lpn, msa)."""
        for role in [UserRole.RN, UserRole.LPN, UserRole.MSA, UserRole.CLINICAL_STAFF]:
            assert RoleFilterService.can_access(ResourceType.MANIFEST, role)
            assert RoleFilterService.can_access(ResourceType.CALL_ROSTER, role)
            assert not RoleFilterService.can_access(ResourceType.SCHEDULES, role)
            assert not RoleFilterService.can_access(ResourceType.ACADEMIC_BLOCKS, role)
            assert not RoleFilterService.can_access(ResourceType.COMPLIANCE, role)

    def test_filter_for_admin(self):
        """Test filtering for admin role - should see everything."""
        data = {
            "schedules": [{"id": 1}],
            "people": [{"id": 2}],
            "compliance": {"status": "compliant"},
            "users": [{"id": 3}],
        }

        filtered = RoleFilterService.filter_for_role(data, UserRole.ADMIN)
        assert filtered == data  # Admin sees everything

    def test_filter_for_coordinator(self):
        """Test filtering for coordinator role."""
        data = {
            "schedules": [{"id": 1}],
            "people": [{"id": 2}],
            "compliance": {"status": "compliant"},
            "users": [{"id": 3}],
        }

        filtered = RoleFilterService.filter_for_role(data, UserRole.COORDINATOR)
        assert "schedules" in filtered
        assert "people" in filtered
        assert "compliance" not in filtered  # Coordinator can't see compliance
        assert "users" not in filtered  # Coordinator can't manage users

    def test_filter_for_faculty(self):
        """Test filtering for faculty role."""
        data = {
            "schedules": [
                {"id": 1, "person_id": "user-123"},
                {"id": 2, "person_id": "user-456"},
            ],
            "compliance": {"status": "compliant"},
            "people": [{"id": 2}],
        }

        filtered = RoleFilterService.filter_for_role(data, UserRole.FACULTY, "user-123")
        assert "schedules" in filtered
        assert len(filtered["schedules"]) == 1  # Only their own schedule
        assert filtered["schedules"][0]["person_id"] == "user-123"
        assert "compliance" not in filtered
        assert "people" not in filtered

    def test_filter_for_clinical_staff(self):
        """Test filtering for clinical staff - only manifest and call roster."""
        data = {
            "manifest": [{"location": "ICU", "staff": []}],
            "call_roster": [{"name": "Dr. Smith"}],
            "schedules": [{"id": 1}],
            "academic_blocks": [{"block": 1}],
            "compliance": {"status": "compliant"},
        }

        for role in [UserRole.RN, UserRole.LPN, UserRole.MSA]:
            filtered = RoleFilterService.filter_for_role(data, role)
            assert "manifest" in filtered
            assert "call_roster" in filtered
            assert "schedules" not in filtered
            assert "academic_blocks" not in filtered
            assert "compliance" not in filtered

    def test_filter_schedule_list_for_admin(self):
        """Test schedule list filtering for admin."""
        schedules = [
            {"id": 1, "person_id": "user-1", "date": "2025-01-15"},
            {"id": 2, "person_id": "user-2", "date": "2025-01-15"},
        ]

        filtered = RoleFilterService.filter_schedule_list(schedules, UserRole.ADMIN)
        assert len(filtered) == 2  # Admin sees all

    def test_filter_schedule_list_for_faculty(self):
        """Test schedule list filtering for faculty - only own schedules."""
        schedules = [
            {"id": 1, "person_id": "user-1", "date": "2025-01-15"},
            {"id": 2, "person_id": "user-2", "date": "2025-01-15"},
            {"id": 3, "person_id": "user-1", "date": "2025-01-16"},
        ]

        filtered = RoleFilterService.filter_schedule_list(
            schedules, UserRole.FACULTY, "user-1"
        )
        assert len(filtered) == 2  # Only schedules for user-1
        assert all(s["person_id"] == "user-1" for s in filtered)

    def test_filter_schedule_list_for_clinical_staff_today_only(self):
        """Test schedule list filtering for clinical staff - only today."""
        today = date.today().isoformat()
        schedules = [
            {"id": 1, "person_id": "user-1", "date": today},
            {"id": 2, "person_id": "user-2", "date": "2025-01-15"},
            {"id": 3, "person_id": "user-3", "date": today},
        ]

        filtered = RoleFilterService.filter_schedule_list(schedules, UserRole.RN)
        assert len(filtered) == 2  # Only today's schedules
        assert all(s["date"] == today for s in filtered)

    def test_can_access_endpoint(self):
        """Test endpoint access checking."""
        assert RoleFilterService.can_access_endpoint(UserRole.ADMIN, "schedules")
        assert RoleFilterService.can_access_endpoint(UserRole.ADMIN, "compliance")
        assert RoleFilterService.can_access_endpoint(UserRole.COORDINATOR, "schedules")
        assert not RoleFilterService.can_access_endpoint(
            UserRole.COORDINATOR, "compliance"
        )
        assert not RoleFilterService.can_access_endpoint(UserRole.FACULTY, "schedules")
        assert RoleFilterService.can_access_endpoint(UserRole.RN, "manifest")
        assert not RoleFilterService.can_access_endpoint(UserRole.RN, "compliance")

    def test_get_accessible_resources(self):
        """Test getting list of accessible resources."""
        admin_resources = RoleFilterService.get_accessible_resources(UserRole.ADMIN)
        assert len(admin_resources) > 0
        assert "schedules" in admin_resources
        assert "users" in admin_resources

        faculty_resources = RoleFilterService.get_accessible_resources(UserRole.FACULTY)
        assert "own_schedule" in faculty_resources
        assert "swaps" in faculty_resources
        assert "schedules" not in faculty_resources

        clinical_resources = RoleFilterService.get_accessible_resources(UserRole.RN)
        assert "manifest" in clinical_resources
        assert "call_roster" in clinical_resources
        assert "compliance" not in clinical_resources

    def test_is_admin(self):
        """Test admin role checking."""
        assert RoleFilterService.is_admin(UserRole.ADMIN)
        assert RoleFilterService.is_admin("admin")
        assert not RoleFilterService.is_admin(UserRole.COORDINATOR)
        assert not RoleFilterService.is_admin("coordinator")

    def test_is_clinical_staff(self):
        """Test clinical staff role checking."""
        assert RoleFilterService.is_clinical_staff(UserRole.RN)
        assert RoleFilterService.is_clinical_staff(UserRole.LPN)
        assert RoleFilterService.is_clinical_staff(UserRole.MSA)
        assert RoleFilterService.is_clinical_staff(UserRole.CLINICAL_STAFF)
        assert not RoleFilterService.is_clinical_staff(UserRole.ADMIN)
        assert not RoleFilterService.is_clinical_staff(UserRole.FACULTY)

    def test_get_role_description(self):
        """Test getting role descriptions."""
        admin_desc = RoleFilterService.get_role_description(UserRole.ADMIN)
        assert admin_desc["role"] == "admin"
        assert admin_desc["title"] == "Administrator"
        assert "permissions" in admin_desc
        assert len(admin_desc["permissions"]) > 0

        rn_desc = RoleFilterService.get_role_description(UserRole.RN)
        assert rn_desc["role"] == "rn"
        assert rn_desc["title"] == "Registered Nurse"
        assert rn_desc["sees"] == "Today's manifest, call roster"
        assert rn_desc["hidden"] == "Academic blocks, compliance"

    def test_string_role_conversion(self):
        """Test that string roles work correctly."""
        # Test can_access with string role
        assert RoleFilterService.can_access(ResourceType.SCHEDULES, "admin")
        assert not RoleFilterService.can_access(ResourceType.USERS, "coordinator")

        # Test filter_for_role with string role
        data = {"schedules": [{"id": 1}], "users": [{"id": 2}]}
        filtered = RoleFilterService.filter_for_role(data, "coordinator")
        assert "schedules" in filtered
        assert "users" not in filtered

    def test_get_permissions(self):
        """Test getting permissions set for a role."""
        admin_perms = RoleFilterService.get_permissions(UserRole.ADMIN)
        assert ResourceType.SCHEDULES in admin_perms
        assert ResourceType.USERS in admin_perms
        assert ResourceType.COMPLIANCE in admin_perms

        faculty_perms = RoleFilterService.get_permissions(UserRole.FACULTY)
        assert ResourceType.OWN_SCHEDULE in faculty_perms
        assert ResourceType.SWAPS in faculty_perms
        assert ResourceType.SCHEDULES not in faculty_perms

        clinical_perms = RoleFilterService.get_permissions("rn")
        assert ResourceType.MANIFEST in clinical_perms
        assert ResourceType.CALL_ROSTER in clinical_perms
        assert ResourceType.COMPLIANCE not in clinical_perms
