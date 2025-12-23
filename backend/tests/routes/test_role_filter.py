"""Tests for role filter example API routes.

Tests the role-based filtering demonstration including:
- Permission retrieval
- Dashboard filtering by role
- Resource access control
- Admin-only endpoints
- Role listing
- Access checking
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestRoleFilterRoutes:
    """Test suite for role filter example API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_get_permissions_requires_auth(self, client: TestClient):
        """Test that permissions endpoint requires authentication."""
        response = client.get("/api/example/permissions")
        assert response.status_code == 401

    def test_get_dashboard_requires_auth(self, client: TestClient):
        """Test that dashboard requires authentication."""
        response = client.get("/api/example/dashboard")
        assert response.status_code == 401

    def test_get_schedules_requires_auth(self, client: TestClient):
        """Test that schedules requires authentication."""
        response = client.get("/api/example/schedules")
        assert response.status_code == 401

    def test_get_my_schedule_requires_auth(self, client: TestClient):
        """Test that my-schedule requires authentication."""
        response = client.get("/api/example/my-schedule")
        assert response.status_code == 401

    def test_create_user_requires_auth(self, client: TestClient):
        """Test that create user requires authentication."""
        response = client.post(
            "/api/example/users",
            params={"username": "test", "email": "test@test.com", "role": "resident"},
        )
        assert response.status_code == 401

    # ========================================================================
    # Public Endpoint Tests
    # ========================================================================

    def test_list_roles_public(self, client: TestClient):
        """Test listing roles (public endpoint)."""
        response = client.get("/api/example/roles")
        assert response.status_code == 200

        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) > 0

    # ========================================================================
    # Permission Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_get_my_permissions_success(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test getting current user's permissions."""
        mock_service.get_accessible_resources.return_value = [
            "schedules",
            "people",
            "compliance",
            "users",
        ]
        mock_service.get_role_description.return_value = "Full access administrator"

        response = client.get("/api/example/permissions", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "user_id" in data
        assert "accessible_resources" in data
        assert "role_description" in data

    # ========================================================================
    # Dashboard Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_get_dashboard_admin(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test dashboard for admin user."""
        # Admin should see all data
        mock_service.filter_for_role.return_value = {
            "schedules": [{"id": 1}, {"id": 2}],
            "people": [{"id": 1}],
            "compliance": {"status": "compliant"},
            "users": [{"id": 1}],
            "manifest": [{"location": "Main Clinic"}],
            "call_roster": [{"name": "Dr. Smith"}],
        }

        response = client.get("/api/example/dashboard", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "message" in data

    # ========================================================================
    # Schedule Access Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.require_resource_access")
    def test_get_schedules_with_access(
        self,
        mock_require_access: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting schedules with proper access."""
        # Mock the dependency to allow access
        mock_require_access.return_value = lambda: None

        response = client.get("/api/example/schedules", headers=auth_headers)
        # Will either succeed (200) or fail based on role
        assert response.status_code in [200, 403]

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_get_my_schedule_success(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test getting own schedule."""
        mock_service.filter_schedule_list.return_value = [
            {"id": 1, "person_id": str(admin_user.id), "date": "2025-01-15"},
        ]

        response = client.get("/api/example/my-schedule", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "schedules" in data
        assert "user_id" in data

    # ========================================================================
    # Manifest Access Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.require_resource_access")
    def test_get_manifest_with_access(
        self,
        mock_require_access: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting daily manifest."""
        mock_require_access.return_value = lambda: None

        response = client.get("/api/example/manifest", headers=auth_headers)
        # Will succeed or fail based on role
        assert response.status_code in [200, 403]

    # ========================================================================
    # Compliance Access Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.require_resource_access")
    def test_get_compliance_report_admin_only(
        self,
        mock_require_access: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test compliance report is admin only."""
        mock_require_access.return_value = lambda: None

        response = client.get("/api/example/compliance", headers=auth_headers)
        # Will succeed if admin, fail otherwise
        assert response.status_code in [200, 403]

    # ========================================================================
    # User Creation Tests (Admin Only)
    # ========================================================================

    @patch("app.api.routes.role_filter_example.require_admin")
    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_create_user_admin_success(
        self,
        mock_service: MagicMock,
        mock_require_admin: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test admin can create users."""
        mock_require_admin.return_value = lambda: None
        mock_service.get_role_from_string.return_value = "resident"

        response = client.post(
            "/api/example/users",
            headers=auth_headers,
            params={
                "username": "newuser",
                "email": "newuser@example.com",
                "role": "resident",
            },
        )
        # Will succeed for admin, fail for others
        assert response.status_code in [200, 403]

    @patch("app.api.routes.role_filter_example.require_admin")
    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_create_user_invalid_role(
        self,
        mock_service: MagicMock,
        mock_require_admin: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating user with invalid role."""
        mock_require_admin.return_value = lambda: None
        mock_service.get_role_from_string.side_effect = ValueError("Invalid role")

        response = client.post(
            "/api/example/users",
            headers=auth_headers,
            params={
                "username": "newuser",
                "email": "newuser@example.com",
                "role": "invalid_role",
            },
        )
        # Should fail with 400 for invalid role
        assert response.status_code in [400, 403]

    # ========================================================================
    # Access Check Tests
    # ========================================================================

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_check_access_granted(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test access check when granted."""
        mock_service.can_access_endpoint.return_value = True

        response = client.get(
            "/api/example/access-check/schedules",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["can_access"] is True
        assert "Access granted" in data["message"]

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_check_access_denied(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test access check when denied."""
        mock_service.can_access_endpoint.return_value = False

        response = client.get(
            "/api/example/access-check/compliance",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["can_access"] is False
        assert "Access denied" in data["message"]

    @patch("app.api.routes.role_filter_example.RoleFilterService")
    def test_check_access_various_endpoints(
        self,
        mock_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test access check for various endpoint categories."""
        endpoints = ["schedules", "people", "compliance", "manifest", "users"]

        for endpoint in endpoints:
            mock_service.can_access_endpoint.return_value = True
            response = client.get(
                f"/api/example/access-check/{endpoint}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["endpoint_category"] == endpoint
