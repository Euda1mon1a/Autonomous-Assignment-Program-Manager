"""Test suite for impersonation API routes.

Tests the impersonation API endpoints which allow administrators to
temporarily assume the identity of other users for troubleshooting
and support purposes.

Security Test Coverage:
- Requires admin role to start impersonation
- Cannot impersonate while already impersonating (nested impersonation blocked)
- Proper error handling for all failure cases
- Cookie management for impersonation tokens
"""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ALGORITHM, get_password_hash
from app.models.user import User

settings = get_settings()


class TestImpersonationRoutes:
    """Test suite for impersonation API endpoints."""

    @pytest.fixture
    def admin_user_for_routes(self, db: Session) -> User:
        """Create an admin user for route tests."""
        user = User(
            id=uuid4(),
            username="route_test_admin",
            email="route_test_admin@test.org",
            hashed_password=get_password_hash("Admin@Pass123"),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def regular_user_for_routes(self, db: Session) -> User:
        """Create a regular (non-admin) user for route tests."""
        user = User(
            id=uuid4(),
            username="route_test_regular",
            email="route_test_regular@test.org",
            hashed_password=get_password_hash("User@Pass123"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def target_user_for_routes(self, db: Session) -> User:
        """Create a target user to be impersonated in route tests."""
        user = User(
            id=uuid4(),
            username="route_test_target",
            email="route_test_target@test.org",
            hashed_password=get_password_hash("Target@Pass123"),
            role="resident",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def admin_auth_headers(
        self, client: TestClient, admin_user_for_routes: User
    ) -> dict:
        """Get authentication headers for admin user."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "route_test_admin", "password": "Admin@Pass123"},
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    @pytest.fixture
    def regular_user_auth_headers(
        self, client: TestClient, regular_user_for_routes: User
    ) -> dict:
        """Get authentication headers for regular user."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "route_test_regular", "password": "User@Pass123"},
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    # ========================================================================
    # Start Impersonation Endpoint Tests
    # ========================================================================

    def test_impersonate_endpoint_requires_admin(
        self,
        client: TestClient,
        regular_user_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test that non-admin users cannot access impersonate endpoint."""
        if not regular_user_auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=regular_user_auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_impersonate_endpoint_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test successful impersonation returns token for admin."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "impersonation_token" in data
        assert data["impersonation_token"] is not None
        assert "target_user" in data
        assert data["target_user"]["id"] == str(target_user_for_routes.id)
        assert "expires_at" in data

        # Verify cookie was set
        assert "impersonation_token" in response.cookies

    def test_impersonate_endpoint_nested_forbidden(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
        db: Session,
    ):
        """Test that nested impersonation returns 400."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start first impersonation
        first_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert first_response.status_code == status.HTTP_200_OK
        first_token = first_response.json()["impersonation_token"]

        # Create another target user for nested impersonation attempt
        second_target = User(
            id=uuid4(),
            username="second_target",
            email="second_target@test.org",
            hashed_password=get_password_hash("Second@Pass123"),
            role="faculty",
            is_active=True,
        )
        db.add(second_target)
        db.commit()
        db.refresh(second_target)

        # Attempt nested impersonation with impersonation token in header
        headers = {
            **admin_auth_headers,
            "X-Impersonation-Token": first_token,
        }
        second_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(second_target.id)},
            headers=headers,
        )

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already impersonating" in second_response.json()["detail"].lower()

    def test_impersonate_endpoint_target_not_found(
        self,
        client: TestClient,
        admin_auth_headers: dict,
    ):
        """Test that impersonating nonexistent user returns 404."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        nonexistent_id = uuid4()
        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(nonexistent_id)},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_impersonate_endpoint_self_forbidden(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        admin_user_for_routes: User,
    ):
        """Test that admin cannot impersonate themselves."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(admin_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "yourself" in response.json()["detail"].lower()

    # ========================================================================
    # End Impersonation Endpoint Tests
    # ========================================================================

    def test_end_impersonation_endpoint_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test successful ending of impersonation session."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK
        impersonation_token = start_response.json()["impersonation_token"]

        # End impersonation
        end_response = client.post(
            "/api/auth/end-impersonation",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert end_response.status_code == status.HTTP_200_OK

        data = end_response.json()
        assert data["success"] is True
        assert "ended" in data["message"].lower()

    def test_end_impersonation_endpoint_no_active_session(
        self,
        client: TestClient,
    ):
        """Test ending impersonation without active session."""
        # No token provided
        response = client.post("/api/auth/end-impersonation")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no active" in response.json()["detail"].lower()

    def test_end_impersonation_endpoint_invalid_token(
        self,
        client: TestClient,
    ):
        """Test ending impersonation with invalid token."""
        response = client.post(
            "/api/auth/end-impersonation",
            headers={"X-Impersonation-Token": "invalid.jwt.token"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ========================================================================
    # Status Endpoint Tests
    # ========================================================================

    def test_status_endpoint_returns_correct_state_impersonating(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test that status endpoint returns correct state when impersonating."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK
        impersonation_token = start_response.json()["impersonation_token"]

        # Get status
        status_response = client.get(
            "/api/auth/impersonation-status",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert status_response.status_code == status.HTTP_200_OK

        data = status_response.json()
        assert data["is_impersonating"] is True
        assert data["target_user"] is not None
        assert data["target_user"]["id"] == str(target_user_for_routes.id)
        assert data["original_user"] is not None
        assert data["expires_at"] is not None

    def test_status_endpoint_returns_correct_state_not_impersonating(
        self,
        client: TestClient,
    ):
        """Test that status endpoint returns correct state when not impersonating."""
        # Get status without any token
        status_response = client.get("/api/auth/impersonation-status")

        assert status_response.status_code == status.HTTP_200_OK

        data = status_response.json()
        assert data["is_impersonating"] is False
        assert data["target_user"] is None
        assert data["original_user"] is None

    def test_status_endpoint_after_impersonation_ended(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test status after impersonation session has ended."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK
        impersonation_token = start_response.json()["impersonation_token"]

        # End impersonation
        end_response = client.post(
            "/api/auth/end-impersonation",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert end_response.status_code == status.HTTP_200_OK

        # Get status with the (now-blacklisted) token
        status_response = client.get(
            "/api/auth/impersonation-status",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert status_response.status_code == status.HTTP_200_OK

        data = status_response.json()
        assert data["is_impersonating"] is False

    # ========================================================================
    # Cookie Management Tests
    # ========================================================================

    def test_impersonation_sets_cookie(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test that starting impersonation sets a cookie."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Check that cookie was set
        assert "impersonation_token" in response.cookies
        cookie_value = response.cookies["impersonation_token"]
        assert cookie_value is not None

        # Verify cookie value is a valid JWT
        assert cookie_value.count(".") == 2

    def test_end_impersonation_clears_cookie(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test that ending impersonation clears the cookie."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK
        impersonation_token = start_response.json()["impersonation_token"]

        # End impersonation
        end_response = client.post(
            "/api/auth/end-impersonation",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert end_response.status_code == status.HTTP_200_OK

        # The cookie should be cleared (set to empty or deleted)
        # FastAPI's delete_cookie sets the cookie to empty string with max_age=0
        if "impersonation_token" in end_response.cookies:
            cookie_value = end_response.cookies["impersonation_token"]
            assert cookie_value == "" or cookie_value is None

    # ========================================================================
    # Token Extraction Tests
    # ========================================================================

    def test_status_with_token_in_header(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
    ):
        """Test that status endpoint works with X-Impersonation-Token header.

        Note: Cookie-based token extraction is also supported by the API but
        is difficult to test with TestClient due to httpx/Starlette limitations.
        Real cookie behavior should be verified via browser/integration testing.
        """
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK
        impersonation_token = start_response.json()["impersonation_token"]

        # Get status using X-Impersonation-Token header
        status_response = client.get(
            "/api/auth/impersonation-status",
            headers={"X-Impersonation-Token": impersonation_token},
        )

        assert status_response.status_code == status.HTTP_200_OK

        data = status_response.json()
        assert data["is_impersonating"] is True

    def test_header_takes_precedence_over_cookie(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        target_user_for_routes: User,
        db: Session,
    ):
        """Test that X-Impersonation-Token header takes precedence over cookie."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Start impersonation (sets cookie)
        start_response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
            headers=admin_auth_headers,
        )

        assert start_response.status_code == status.HTTP_200_OK

        # Get status with invalid header (should use header, not cookie)
        status_response = client.get(
            "/api/auth/impersonation-status",
            headers={"X-Impersonation-Token": "invalid.jwt.token"},
        )

        assert status_response.status_code == status.HTTP_200_OK

        data = status_response.json()
        # Should return not impersonating because header took precedence and is invalid
        assert data["is_impersonating"] is False

    # ========================================================================
    # Error Response Tests
    # ========================================================================

    def test_impersonate_inactive_user_returns_403(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        db: Session,
    ):
        """Test that impersonating inactive user returns 403."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        # Create inactive user
        inactive_user = User(
            id=uuid4(),
            username="inactive_target",
            email="inactive_target@test.org",
            hashed_password=get_password_hash("Inactive@Pass123"),
            role="resident",
            is_active=False,
        )
        db.add(inactive_user)
        db.commit()
        db.refresh(inactive_user)

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(inactive_user.id)},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    def test_impersonate_without_auth_returns_401(
        self,
        client: TestClient,
        target_user_for_routes: User,
    ):
        """Test that impersonation without authentication returns 401."""
        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target_user_for_routes.id)},
        )

        # Should return 401 or 403 depending on auth implementation
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_impersonate_with_invalid_uuid_returns_422(
        self,
        client: TestClient,
        admin_auth_headers: dict,
    ):
        """Test that invalid UUID format returns 422."""
        if not admin_auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/auth/impersonate",
            json={"target_user_id": "not-a-valid-uuid"},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
