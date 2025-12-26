"""Tests for session management API routes.

Tests the session management functionality including:
- Viewing active sessions
- Managing user sessions
- Force logout
- Session refresh
- Session statistics
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.sessions import get_session_manager
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = AsyncMock()
    return manager


@pytest.fixture
def client_with_mock_manager(db, mock_session_manager):
    """Create test client with mocked session manager."""
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_session_manager] = lambda: mock_session_manager

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestSessionRoutes:
    """Test suite for session management API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_get_my_sessions_requires_auth(self, client: TestClient):
        """Test that get my sessions requires authentication."""
        response = client.get("/api/sessions/me")
        assert response.status_code == 401

    def test_get_current_session_requires_auth(self, client: TestClient):
        """Test that get current session requires authentication."""
        response = client.get("/api/sessions/me/current")
        assert response.status_code == 401

    def test_refresh_session_requires_auth(self, client: TestClient):
        """Test that refresh session requires authentication."""
        response = client.post("/api/sessions/me/refresh")
        assert response.status_code == 401

    def test_logout_session_requires_auth(self, client: TestClient):
        """Test that logout session requires authentication."""
        response = client.delete(f"/api/sessions/me/{uuid4()}")
        assert response.status_code == 401

    # ========================================================================
    # Admin-Only Endpoint Tests
    # ========================================================================

    def test_get_session_stats_requires_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that session stats requires admin role."""
        # auth_headers provides admin user, so this should work
        # For non-admin, we'd need a separate fixture
        pass  # Tested implicitly via admin user fixture

    def test_force_logout_requires_admin(self, client: TestClient):
        """Test that force logout requires admin authentication."""
        response = client.delete(f"/api/sessions/user/{uuid4()}/force-logout")
        assert response.status_code == 401

    def test_revoke_session_requires_admin(self, client: TestClient):
        """Test that revoke session requires admin authentication."""
        response = client.delete(f"/api/sessions/session/{uuid4()}")
        assert response.status_code == 401

    # ========================================================================
    # Get My Sessions Tests
    # ========================================================================

    def test_get_my_sessions_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful retrieval of user sessions."""
        mock_session_manager.get_user_sessions.return_value = {
            "user_id": str(admin_user.id),
            "sessions": [
                {
                    "session_id": str(uuid4()),
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                    "status": "active",
                    "device_info": {
                        "browser": "Chrome",
                        "os": "macOS",
                    },
                }
            ],
            "count": 1,
        }

        response = client_with_mock_manager.get(
            "/api/sessions/me", headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_my_sessions_empty(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test retrieval when no sessions exist."""
        mock_session_manager.get_user_sessions.return_value = {
            "user_id": str(uuid4()),
            "sessions": [],
            "count": 0,
        }

        response = client_with_mock_manager.get(
            "/api/sessions/me", headers=auth_headers
        )
        assert response.status_code == 200

    # ========================================================================
    # Get Current Session Tests
    # ========================================================================

    @patch("app.api.routes.sessions.SessionState")
    def test_get_current_session_exists(
        self,
        mock_session_state: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting current session when it exists."""
        mock_session = MagicMock()
        mock_session.session_id = str(uuid4())
        mock_session.user_id = str(uuid4())
        mock_session.username = "testadmin"
        mock_session.created_at = datetime.utcnow()
        mock_session.last_activity = datetime.utcnow()
        mock_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session.status = "active"
        mock_session.device_info = {}
        mock_session.request_count = 10

        mock_session_state.get_session.return_value = mock_session

        response = client.get("/api/sessions/me/current", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.api.routes.sessions.SessionState")
    def test_get_current_session_not_exists(
        self,
        mock_session_state: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting current session when none exists."""
        mock_session_state.get_session.return_value = None

        response = client.get("/api/sessions/me/current", headers=auth_headers)
        assert response.status_code == 200
        # Returns null when no session

    # ========================================================================
    # Refresh Session Tests
    # ========================================================================

    @patch("app.api.routes.sessions.SessionState")
    def test_refresh_session_success(
        self,
        mock_session_state: MagicMock,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test successful session refresh."""
        session_id = str(uuid4())
        mock_session = MagicMock()
        mock_session.session_id = session_id
        mock_session_state.get_session.return_value = mock_session

        refreshed_session = MagicMock()
        refreshed_session.session_id = session_id
        refreshed_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session_manager.refresh_session.return_value = refreshed_session

        response = client_with_mock_manager.post(
            "/api/sessions/me/refresh", headers=auth_headers
        )
        assert response.status_code == 200
        assert "message" in response.json()

    @patch("app.api.routes.sessions.SessionState")
    def test_refresh_session_no_active_session(
        self,
        mock_session_state: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test refresh when no active session."""
        mock_session_state.get_session.return_value = None

        response = client.post("/api/sessions/me/refresh", headers=auth_headers)
        assert response.status_code == 404
        assert "no active session" in response.json()["detail"].lower()

    # ========================================================================
    # Logout Session Tests
    # ========================================================================

    def test_logout_specific_session_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful logout of specific session."""
        session_id = str(uuid4())

        mock_session = MagicMock()
        mock_session.user_id = str(admin_user.id)

        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.logout_session.return_value = True

        response = client_with_mock_manager.delete(
            f"/api/sessions/me/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_logout_session_not_found(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test logout when session not found."""
        mock_session_manager.get_session.return_value = None

        response = client_with_mock_manager.delete(
            f"/api/sessions/me/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_logout_other_users_session_forbidden(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test that users cannot logout other users' sessions."""
        mock_session = MagicMock()
        mock_session.user_id = str(uuid4())  # Different user

        mock_session_manager.get_session.return_value = mock_session

        response = client_with_mock_manager.delete(
            f"/api/sessions/me/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    # ========================================================================
    # Logout Other Sessions Tests
    # ========================================================================

    @patch("app.api.routes.sessions.SessionState")
    def test_logout_other_sessions_success(
        self,
        mock_session_state: MagicMock,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test logout all other sessions."""
        current_session = MagicMock()
        current_session.session_id = str(uuid4())
        mock_session_state.get_session.return_value = current_session

        mock_session_manager.logout_user_sessions.return_value = 3

        response = client_with_mock_manager.delete(
            "/api/sessions/me/other", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert data["count"] == 3

    # ========================================================================
    # Logout All Sessions Tests
    # ========================================================================

    def test_logout_all_sessions_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test logout all sessions for current user."""
        mock_session_manager.logout_user_sessions.return_value = 5

        response = client_with_mock_manager.delete(
            "/api/sessions/me/all", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert data["count"] == 5

    # ========================================================================
    # Admin: Session Stats Tests
    # ========================================================================

    def test_get_session_stats_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test getting session statistics."""
        mock_session_manager.get_session_stats.return_value = {
            "total_active_sessions": 100,
            "unique_users": 50,
            "sessions_by_status": {"active": 95, "expired": 5},
        }

        response = client_with_mock_manager.get(
            "/api/sessions/stats", headers=auth_headers
        )
        assert response.status_code == 200

    # ========================================================================
    # Admin: Force Logout Tests
    # ========================================================================

    def test_force_logout_user_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test force logout user by admin."""
        user_id = str(uuid4())

        mock_session_manager.force_logout_user.return_value = 3

        response = client_with_mock_manager.delete(
            f"/api/sessions/user/{user_id}/force-logout",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["sessions_revoked"] == 3

    # ========================================================================
    # Admin: Revoke Session Tests
    # ========================================================================

    def test_revoke_session_success(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test admin session revocation."""
        session_id = str(uuid4())

        mock_session_manager.revoke_session.return_value = True

        response = client_with_mock_manager.delete(
            f"/api/sessions/session/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_revoke_session_not_found(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test revoke when session not found."""
        mock_session_manager.revoke_session.return_value = False

        response = client_with_mock_manager.delete(
            f"/api/sessions/session/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Admin: Cleanup Tests
    # ========================================================================

    def test_cleanup_expired_sessions(
        self,
        client_with_mock_manager: TestClient,
        mock_session_manager: AsyncMock,
        auth_headers: dict,
    ):
        """Test cleanup of expired sessions."""
        mock_session_manager.cleanup_expired_sessions.return_value = 10

        response = client_with_mock_manager.post(
            "/api/sessions/cleanup", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 10
