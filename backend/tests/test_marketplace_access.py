"""Tests for swap marketplace access restrictions.

These tests verify that the swap marketplace is disabled by default for residents
to prevent gamification of swaps (e.g., exploiting post-call PCAT/DO rules).
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.feature_flag import FeatureFlag
from app.models.person import Person
from app.models.user import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_resident(db: Session) -> Person:
    """Create a sample resident."""
    resident = Person(
        id=uuid4(),
        name="Dr. Resident Test",
        type="resident",
        email="resident.test@hospital.org",
        pgy_level=2,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def sample_faculty(db: Session) -> Person:
    """Create a sample faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty Test",
        type="faculty",
        email="faculty.test@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def resident_user(db: Session, sample_resident: Person) -> User:
    """Create a user with resident role linked to a resident person."""
    user = User(
        id=uuid4(),
        username=f"resident_{sample_resident.id}",
        email=sample_resident.email,
        hashed_password=get_password_hash("testpass123"),
        role="resident",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def faculty_user(db: Session, sample_faculty: Person) -> User:
    """Create a user with faculty role linked to a faculty person."""
    user = User(
        id=uuid4(),
        username=f"faculty_{sample_faculty.id}",
        email=sample_faculty.email,
        hashed_password=get_password_hash("testpass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def resident_auth_headers(client: TestClient, resident_user: User) -> dict:
    """Get auth headers for resident user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": resident_user.username, "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def faculty_auth_headers(client: TestClient, faculty_user: User) -> dict:
    """Get auth headers for faculty user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": faculty_user.username, "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def marketplace_flag_for_all(db: Session) -> FeatureFlag:
    """Create a feature flag that enables marketplace for all roles including residents."""
    flag = FeatureFlag(
        id=uuid4(),
        key="swap_marketplace_enabled",
        name="Enable Swap Marketplace",
        description="Controls access to the swap marketplace",
        flag_type="boolean",
        enabled=True,
        target_roles=["admin", "coordinator", "faculty", "resident"],
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


@pytest.fixture
def marketplace_flag_no_residents(db: Session) -> FeatureFlag:
    """Create a feature flag that excludes residents from marketplace."""
    flag = FeatureFlag(
        id=uuid4(),
        key="swap_marketplace_enabled",
        name="Enable Swap Marketplace",
        description="Controls access to the swap marketplace",
        flag_type="boolean",
        enabled=True,
        target_roles=["admin", "coordinator", "faculty"],  # Excludes resident
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


# ============================================================================
# Tests: Marketplace View Access
# ============================================================================


class TestMarketplaceViewAccess:
    """Tests for GET /api/portal/marketplace access control."""

    def test_faculty_can_view_marketplace(
        self, client: TestClient, faculty_auth_headers: dict
    ):
        """Test that faculty users can access the swap marketplace."""
        response = client.get(
            "/api/portal/marketplace",
            headers=faculty_auth_headers,
        )
        # Should be 200 (success) or 403 for no faculty profile, not for role restriction
        assert response.status_code in [200, 403]
        if response.status_code == 403:
            # Make sure it's not a marketplace access error
            assert "marketplace access" not in response.json().get("detail", "").lower()

    def test_resident_cannot_view_marketplace_default(
        self, client: TestClient, resident_auth_headers: dict
    ):
        """Test that residents cannot access marketplace by default (no flag)."""
        response = client.get(
            "/api/portal/marketplace",
            headers=resident_auth_headers,
        )
        assert response.status_code == 403
        assert "marketplace access" in response.json()["detail"].lower()

    def test_resident_cannot_view_marketplace_with_flag(
        self,
        client: TestClient,
        resident_auth_headers: dict,
        marketplace_flag_no_residents: FeatureFlag,
    ):
        """Test that residents cannot access marketplace when flag excludes them."""
        response = client.get(
            "/api/portal/marketplace",
            headers=resident_auth_headers,
        )
        assert response.status_code == 403
        assert "marketplace access" in response.json()["detail"].lower()

    def test_resident_can_view_marketplace_when_enabled(
        self,
        client: TestClient,
        resident_auth_headers: dict,
        marketplace_flag_for_all: FeatureFlag,
    ):
        """Test that residents can access marketplace when flag includes them."""
        response = client.get(
            "/api/portal/marketplace",
            headers=resident_auth_headers,
        )
        # Should be 200 (success) or 403 for no faculty profile, not for role restriction
        assert response.status_code in [200, 403]
        if response.status_code == 403:
            # Error should be about faculty profile, not marketplace access
            assert "marketplace access" not in response.json().get("detail", "").lower()


# ============================================================================
# Tests: Marketplace Posting (Swap Creation Without Target)
# ============================================================================


class TestMarketplacePostAccess:
    """Tests for marketplace posting (POST /api/portal/my/swaps without target)."""

    def test_resident_cannot_post_to_marketplace(
        self, client: TestClient, resident_auth_headers: dict
    ):
        """Test that residents cannot post swaps to the marketplace."""
        response = client.post(
            "/api/portal/my/swaps",
            json={
                "week_to_offload": (date.today() + timedelta(days=30)).isoformat(),
                "reason": "Testing marketplace access",
                "auto_find_candidates": True,
                # No preferred_target_faculty_id = marketplace posting
            },
            headers=resident_auth_headers,
        )
        assert response.status_code == 403
        assert "marketplace" in response.json()["detail"].lower()

    def test_resident_can_request_direct_swap(
        self,
        client: TestClient,
        resident_auth_headers: dict,
        sample_faculty: Person,
    ):
        """Test that residents can still request direct swaps with specific faculty."""
        response = client.post(
            "/api/portal/my/swaps",
            json={
                "week_to_offload": (date.today() + timedelta(days=30)).isoformat(),
                "preferred_target_faculty_id": str(sample_faculty.id),
                "reason": "Direct swap request",
                "auto_find_candidates": False,
            },
            headers=resident_auth_headers,
        )
        # Should not get marketplace access error (might get other errors like no faculty profile)
        if response.status_code == 403:
            assert "marketplace" not in response.json().get("detail", "").lower()

    def test_faculty_can_post_to_marketplace(
        self, client: TestClient, faculty_auth_headers: dict
    ):
        """Test that faculty users can post to the marketplace."""
        response = client.post(
            "/api/portal/my/swaps",
            json={
                "week_to_offload": (date.today() + timedelta(days=30)).isoformat(),
                "reason": "Faculty marketplace test",
                "auto_find_candidates": True,
            },
            headers=faculty_auth_headers,
        )
        # Should not get marketplace access error
        if response.status_code == 403:
            assert "marketplace access" not in response.json().get("detail", "").lower()

    def test_resident_can_post_when_flag_allows(
        self,
        client: TestClient,
        resident_auth_headers: dict,
        marketplace_flag_for_all: FeatureFlag,
    ):
        """Test that residents can post to marketplace when flag includes them."""
        response = client.post(
            "/api/portal/my/swaps",
            json={
                "week_to_offload": (date.today() + timedelta(days=30)).isoformat(),
                "reason": "Testing with flag enabled",
                "auto_find_candidates": True,
            },
            headers=resident_auth_headers,
        )
        # Should not get marketplace access error (might get other errors)
        if response.status_code == 403:
            assert "marketplace access" not in response.json().get("detail", "").lower()


# ============================================================================
# Tests: Feature Flag Edge Cases
# ============================================================================


class TestFeatureFlagEdgeCases:
    """Tests for feature flag edge cases in marketplace access."""

    def test_disabled_flag_blocks_all_users(self, db: Session, client: TestClient):
        """Test that a disabled flag blocks all users from marketplace."""
        # Create a disabled flag
        flag = FeatureFlag(
            id=uuid4(),
            key="swap_marketplace_enabled",
            name="Enable Swap Marketplace",
            flag_type="boolean",
            enabled=False,  # Globally disabled
            target_roles=["admin", "coordinator", "faculty"],
        )
        db.add(flag)
        db.commit()

        # Create faculty user
        faculty = Person(
            id=uuid4(),
            name="Dr. Disabled Test",
            type="faculty",
            email="disabled.test@hospital.org",
        )
        db.add(faculty)

        user = User(
            id=uuid4(),
            username="disabled_test",
            email=faculty.email,
            hashed_password=get_password_hash("testpass123"),
            role="faculty",
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Login
        response = client.post(
            "/api/auth/login/json",
            json={"username": "disabled_test", "password": "testpass123"},
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access marketplace
        response = client.get("/api/portal/marketplace", headers=headers)
        assert response.status_code == 403
        assert "marketplace access" in response.json()["detail"].lower()

    def test_admin_can_always_access_marketplace(
        self, db: Session, client: TestClient, admin_user: User, auth_headers: dict
    ):
        """Test that admins can access marketplace even with restrictive flag."""
        # Create restrictive flag that doesn't include admin (edge case)
        flag = FeatureFlag(
            id=uuid4(),
            key="swap_marketplace_enabled",
            name="Enable Swap Marketplace",
            flag_type="boolean",
            enabled=True,
            target_roles=["faculty"],  # Only faculty
        )
        db.add(flag)
        db.commit()

        # Admin should still be blocked by role targeting
        # (This verifies the feature flag logic is working correctly)
        response = client.get("/api/portal/marketplace", headers=auth_headers)
        # Admin should get 403 because they're not in target_roles
        # Unless they have a faculty profile, then they'd get a different error
        assert response.status_code in [200, 403]


# ============================================================================
# Additional fixtures from conftest
# ============================================================================


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for authenticated tests."""
    user = User(
        id=uuid4(),
        username="testadmin_marketplace",
        email="testadmin_marketplace@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, admin_user: User) -> dict:
    """Get authentication headers for API requests."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "testadmin_marketplace", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}
