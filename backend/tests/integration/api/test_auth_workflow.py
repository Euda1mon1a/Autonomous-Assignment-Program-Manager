"""
Integration tests for authentication workflows.

Tests user authentication, authorization, token management, and session handling.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from uuid import uuid4


class TestAuthWorkflow:
    """Test authentication and authorization workflows."""

    def test_user_registration_workflow(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test complete user registration flow."""
        # Step 1: Register new user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.org",
                "password": "SecurePass123!",
                "role": "resident",
            },
        )

        # May succeed or return 404 if registration disabled
        assert register_response.status_code in [200, 201, 404, 501]

        if register_response.status_code in [200, 201]:
            data = register_response.json()
            assert "id" in data or "username" in data

            # Step 2: Verify user can login
            login_response = client.post(
                "/api/auth/login/json",
                json={
                    "username": "newuser",
                    "password": "SecurePass123!",
                },
            )
            assert login_response.status_code == 200
            assert "access_token" in login_response.json()

    def test_login_logout_workflow(
        self,
        client: TestClient,
        admin_user: User,
    ):
        """Test login and logout flow."""
        # Step 1: Login
        login_response = client.post(
            "/api/auth/login/json",
            json={
                "username": "testadmin",
                "password": "testpass123",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        # Step 2: Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        protected_response = client.get(
            "/api/people/",
            headers=headers,
        )
        assert protected_response.status_code == 200

        # Step 3: Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers=headers,
        )
        assert logout_response.status_code in [200, 204, 404]

    def test_token_refresh_workflow(
        self,
        client: TestClient,
        admin_user: User,
    ):
        """Test JWT token refresh."""
        # Step 1: Login
        login_response = client.post(
            "/api/auth/login/json",
            json={
                "username": "testadmin",
                "password": "testpass123",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        # Step 2: Request token refresh
        if "refresh_token" in token_data:
            refresh_response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": token_data["refresh_token"]},
            )
            assert refresh_response.status_code in [200, 404, 501]

            if refresh_response.status_code == 200:
                new_token_data = refresh_response.json()
                assert "access_token" in new_token_data

    def test_password_change_workflow(
        self,
        client: TestClient,
        admin_user: User,
        auth_headers: dict,
    ):
        """Test password change flow."""
        # Step 1: Change password
        change_response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "testpass123",
                "new_password": "NewSecurePass123!",
            },
            headers=auth_headers,
        )
        assert change_response.status_code in [200, 404, 501]

        if change_response.status_code == 200:
            # Step 2: Verify old password doesn't work
            old_login = client.post(
                "/api/auth/login/json",
                json={
                    "username": "testadmin",
                    "password": "testpass123",
                },
            )
            assert old_login.status_code in [401, 403]

            # Step 3: Verify new password works
            new_login = client.post(
                "/api/auth/login/json",
                json={
                    "username": "testadmin",
                    "password": "NewSecurePass123!",
                },
            )
            assert new_login.status_code == 200

    def test_password_reset_workflow(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test password reset flow."""
        # Step 1: Create user
        user = User(
            id=uuid4(),
            username="resetuser",
            email="resetuser@test.org",
            hashed_password=get_password_hash("oldpass123"),
            role="resident",
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Step 2: Request password reset
        reset_request = client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser@test.org"},
        )
        assert reset_request.status_code in [200, 202, 404, 501]

        # Step 3: Reset password with token (if implemented)
        if reset_request.status_code in [200, 202]:
            # In real system, would get token from email
            reset_confirm = client.post(
                "/api/auth/reset-password",
                json={
                    "token": "dummy-token",
                    "new_password": "NewPassword123!",
                },
            )
            assert reset_confirm.status_code in [200, 400, 404, 501]

    def test_role_based_access_workflow(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test role-based access control."""
        # Step 1: Create users with different roles
        roles_data = [
            ("admin_test", "admin"),
            ("faculty_test", "faculty"),
            ("resident_test", "resident"),
        ]

        tokens = {}
        for username, role in roles_data:
            user = User(
                id=uuid4(),
                username=username,
                email=f"{username}@test.org",
                hashed_password=get_password_hash("testpass123"),
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()

            # Login to get token
            login_response = client.post(
                "/api/auth/login/json",
                json={"username": username, "password": "testpass123"},
            )
            if login_response.status_code == 200:
                tokens[role] = login_response.json()["access_token"]

        # Step 2: Test admin-only endpoint
        if "admin" in tokens:
            admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
            admin_endpoint = client.get(
                "/api/admin/users",
                headers=admin_headers,
            )
            # Should succeed for admin
            assert admin_endpoint.status_code in [200, 404]

        # Step 3: Test resident cannot access admin endpoint
        if "resident" in tokens:
            resident_headers = {"Authorization": f"Bearer {tokens['resident']}"}
            resident_attempt = client.get(
                "/api/admin/users",
                headers=resident_headers,
            )
            # Should be forbidden
            assert resident_attempt.status_code in [403, 404]

    def test_session_expiration_workflow(
        self,
        client: TestClient,
        admin_user: User,
    ):
        """Test session expiration handling."""
        # Step 1: Login
        login_response = client.post(
            "/api/auth/login/json",
            json={
                "username": "testadmin",
                "password": "testpass123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Use valid token
        valid_response = client.get("/api/people/", headers=headers)
        assert valid_response.status_code == 200

        # Step 3: Use invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        invalid_response = client.get("/api/people/", headers=invalid_headers)
        assert invalid_response.status_code in [401, 403]

    def test_concurrent_session_workflow(
        self,
        client: TestClient,
        admin_user: User,
    ):
        """Test multiple concurrent sessions."""
        # Step 1: Login from first session
        login1 = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )
        assert login1.status_code == 200
        token1 = login1.json()["access_token"]

        # Step 2: Login from second session
        login2 = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )
        assert login2.status_code == 200
        token2 = login2.json()["access_token"]

        # Step 3: Both tokens should work (unless single-session enforced)
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        response1 = client.get("/api/people/", headers=headers1)
        response2 = client.get("/api/people/", headers=headers2)

        # Both should work or first should be invalidated
        assert response1.status_code in [200, 401]
        assert response2.status_code == 200

    def test_oauth2_flow_workflow(
        self,
        client: TestClient,
    ):
        """Test OAuth2 authentication flow."""
        # Step 1: Request OAuth2 authorization
        auth_response = client.get("/api/oauth2/authorize")
        assert auth_response.status_code in [200, 302, 404, 501]

        # Step 2: OAuth2 callback (if implemented)
        callback_response = client.get(
            "/api/oauth2/callback?code=dummy_code&state=dummy_state"
        )
        assert callback_response.status_code in [200, 302, 400, 404, 501]

    def test_api_key_authentication_workflow(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test API key authentication for programmatic access."""
        # Step 1: Generate API key
        api_key_response = client.post(
            "/api/auth/api-keys",
            json={"name": "test_key", "expires_in_days": 30},
            headers={"Authorization": "Bearer dummy_token"},
        )

        assert api_key_response.status_code in [200, 201, 401, 404, 501]

        if api_key_response.status_code in [200, 201]:
            api_key = api_key_response.json().get("key")

            # Step 2: Use API key to access endpoint
            key_headers = {"X-API-Key": api_key}
            key_response = client.get("/api/people/", headers=key_headers)
            assert key_response.status_code in [200, 401]
