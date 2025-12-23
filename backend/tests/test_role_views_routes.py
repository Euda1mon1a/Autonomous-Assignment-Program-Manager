"""Tests for role views API routes.

Comprehensive test suite covering role-based view permissions, configurations,
access control, and all role views endpoints.
"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


class TestGetRolePermissionsEndpoint:
    """Tests for GET /api/role-views/views/permissions/{role} endpoint."""

    def test_get_role_permissions_admin(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for admin role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/admin", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data
        assert "can_edit_schedules" in data
        assert "can_view_compliance" in data
        assert isinstance(data["can_view_schedules"], bool)

    def test_get_role_permissions_coordinator(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting permissions for coordinator role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/coordinator", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data
        assert "can_edit_schedules" in data
        assert "can_approve_swaps" in data

    def test_get_role_permissions_faculty(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for faculty role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/faculty", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data
        assert "can_request_swaps" in data

    def test_get_role_permissions_resident(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting permissions for resident role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/resident", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data

    def test_get_role_permissions_clinical_staff(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting permissions for clinical staff role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/clinical_staff", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data

    def test_get_role_permissions_rn(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for RN role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/rn", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data

    def test_get_role_permissions_lpn(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for LPN role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/lpn", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data

    def test_get_role_permissions_msa(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for MSA role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/msa", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_view_schedules" in data

    def test_get_role_permissions_unauthenticated(self, client: TestClient):
        """Test getting permissions without authentication."""
        response = client.get("/api/v1/role-views/views/permissions/admin")

        # Should require authentication
        assert response.status_code in [401, 403]

    def test_get_role_permissions_invalid_role(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting permissions for invalid role."""
        response = client.get(
            "/api/v1/role-views/views/permissions/invalid_role", headers=auth_headers
        )

        # Should handle gracefully (either 400 or 422)
        assert response.status_code in [400, 422]


class TestGetRoleConfigEndpoint:
    """Tests for GET /api/role-views/views/config/{role} endpoint."""

    def test_get_role_config_admin(self, client: TestClient, auth_headers: dict):
        """Test getting full config for admin role."""
        response = client.get(
            "/api/v1/role-views/views/config/admin", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert "permissions" in data
        assert data["role"] == "admin"
        assert isinstance(data["permissions"], dict)

    def test_get_role_config_coordinator(self, client: TestClient, auth_headers: dict):
        """Test getting full config for coordinator role."""
        response = client.get(
            "/api/v1/role-views/views/config/coordinator", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "coordinator"
        assert "permissions" in data

    def test_get_role_config_faculty(self, client: TestClient, auth_headers: dict):
        """Test getting full config for faculty role."""
        response = client.get(
            "/api/v1/role-views/views/config/faculty", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "faculty"
        assert "permissions" in data

    def test_get_role_config_resident(self, client: TestClient, auth_headers: dict):
        """Test getting full config for resident role."""
        response = client.get(
            "/api/v1/role-views/views/config/resident", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "resident"
        assert "permissions" in data

    def test_get_role_config_unauthenticated(self, client: TestClient):
        """Test getting config without authentication."""
        response = client.get("/api/v1/role-views/views/config/admin")

        assert response.status_code in [401, 403]

    def test_get_role_config_invalid_role(self, client: TestClient, auth_headers: dict):
        """Test getting config for invalid role."""
        response = client.get(
            "/api/v1/role-views/views/config/nonexistent_role", headers=auth_headers
        )

        assert response.status_code in [400, 422]


class TestGetCurrentUserViewConfigEndpoint:
    """Tests for GET /api/role-views/views/config endpoint."""

    def test_get_current_user_config_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting config for authenticated admin user."""
        response = client.get("/api/v1/role-views/views/config", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert "permissions" in data
        assert data["role"] == "admin"

    def test_get_current_user_config_coordinator(self, client: TestClient, db: Session):
        """Test getting config for coordinator user."""
        # Create coordinator user
        coordinator = User(
            id=uuid4(),
            username="testcoordinator",
            email="coordinator@test.org",
            hashed_password=get_password_hash("testpass123"),
            role="coordinator",
            is_active=True,
        )
        db.add(coordinator)
        db.commit()

        # Login as coordinator
        login_response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "testcoordinator", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get config
        response = client.get("/api/v1/role-views/views/config", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "coordinator"
        assert "permissions" in data

    def test_get_current_user_config_faculty(self, client: TestClient, db: Session):
        """Test getting config for faculty user."""
        # Create faculty user
        faculty = User(
            id=uuid4(),
            username="testfaculty",
            email="faculty@test.org",
            hashed_password=get_password_hash("testpass123"),
            role="faculty",
            is_active=True,
        )
        db.add(faculty)
        db.commit()

        # Login as faculty
        login_response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "testfaculty", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get config
        response = client.get("/api/v1/role-views/views/config", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "faculty"

    def test_get_current_user_config_unauthenticated(self, client: TestClient):
        """Test getting config without authentication."""
        response = client.get("/api/v1/role-views/views/config")

        assert response.status_code in [401, 403]


class TestCheckEndpointAccessEndpoint:
    """Tests for POST /api/role-views/views/check-access endpoint."""

    def test_check_access_admin_schedules(self, client: TestClient, auth_headers: dict):
        """Test checking admin access to schedules endpoint."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "admin", "endpoint_category": "schedules"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert "endpoint_category" in data
        assert "can_access" in data
        assert "permissions" in data
        assert data["role"] == "admin"
        assert data["endpoint_category"] == "schedules"
        assert isinstance(data["can_access"], bool)

    def test_check_access_coordinator_compliance(
        self, client: TestClient, auth_headers: dict
    ):
        """Test checking coordinator access to compliance endpoint."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "coordinator", "endpoint_category": "compliance"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "coordinator"
        assert data["endpoint_category"] == "compliance"
        assert "can_access" in data

    def test_check_access_faculty_swaps(self, client: TestClient, auth_headers: dict):
        """Test checking faculty access to swaps endpoint."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "faculty", "endpoint_category": "swaps"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "faculty"
        assert data["endpoint_category"] == "swaps"

    def test_check_access_resident_schedules(
        self, client: TestClient, auth_headers: dict
    ):
        """Test checking resident access to schedules."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "resident", "endpoint_category": "schedules"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "resident"
        assert data["endpoint_category"] == "schedules"

    def test_check_access_multiple_categories(
        self, client: TestClient, auth_headers: dict
    ):
        """Test checking access for various endpoint categories."""
        categories = ["schedules", "compliance", "swaps", "assignments", "reports"]

        for category in categories:
            response = client.post(
                "/api/v1/role-views/views/check-access",
                headers=auth_headers,
                params={"role": "admin", "endpoint_category": category},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["endpoint_category"] == category

    def test_check_access_unauthenticated(self, client: TestClient):
        """Test checking access without authentication."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            params={"role": "admin", "endpoint_category": "schedules"},
        )

        assert response.status_code in [401, 403]

    def test_check_access_invalid_role(self, client: TestClient, auth_headers: dict):
        """Test checking access with invalid role."""
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "invalid_role", "endpoint_category": "schedules"},
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_check_access_missing_parameters(
        self, client: TestClient, auth_headers: dict
    ):
        """Test checking access with missing parameters."""
        # Missing endpoint_category
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "admin"},
        )

        assert response.status_code == 422  # Validation error


class TestListAllRolesEndpoint:
    """Tests for GET /api/role-views/views/roles endpoint."""

    def test_list_all_roles(self, client: TestClient, auth_headers: dict):
        """Test listing all available staff roles."""
        response = client.get("/api/v1/role-views/views/roles", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Should contain expected roles
        expected_roles = ["admin", "coordinator", "faculty", "resident"]
        for role in expected_roles:
            assert role in data

    def test_list_all_roles_contains_all_8_roles(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that all 8 roles are returned."""
        response = client.get("/api/v1/role-views/views/roles", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Per CLAUDE.md: 8 user roles
        all_roles = [
            "admin",
            "coordinator",
            "faculty",
            "resident",
            "clinical_staff",
            "rn",
            "lpn",
            "msa",
        ]

        for role in all_roles:
            assert role in data

    def test_list_all_roles_unauthenticated(self, client: TestClient):
        """Test listing roles without authentication."""
        response = client.get("/api/v1/role-views/views/roles")

        assert response.status_code in [401, 403]


class TestGetAllRolePermissionsEndpoint:
    """Tests for GET /api/role-views/views/permissions endpoint."""

    def test_get_all_role_permissions(self, client: TestClient, auth_headers: dict):
        """Test getting permissions for all roles."""
        response = client.get(
            "/api/v1/role-views/views/permissions", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Should contain permissions for all roles
        expected_roles = ["admin", "coordinator", "faculty", "resident"]
        for role in expected_roles:
            assert role in data
            assert isinstance(data[role], dict)

    def test_get_all_permissions_structure(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that all role permissions have proper structure."""
        response = client.get(
            "/api/v1/role-views/views/permissions", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        for role, permissions in data.items():
            assert isinstance(permissions, dict)
            # Verify common permission fields exist
            assert "can_view_schedules" in permissions

    def test_get_all_permissions_admin_has_most_permissions(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that admin role has the most permissions."""
        response = client.get(
            "/api/v1/role-views/views/permissions", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        if "admin" in data:
            admin_perms = data["admin"]
            # Count True permissions
            admin_true_count = sum(1 for v in admin_perms.values() if v is True)

            # Admin should have more permissions than other roles
            for role, perms in data.items():
                if role != "admin":
                    role_true_count = sum(1 for v in perms.values() if v is True)
                    assert admin_true_count >= role_true_count

    def test_get_all_permissions_unauthenticated(self, client: TestClient):
        """Test getting all permissions without authentication."""
        response = client.get("/api/v1/role-views/views/permissions")

        assert response.status_code in [401, 403]


class TestRoleViewsErrorHandling:
    """Tests for error handling in role views endpoints."""

    def test_server_error_handling(self, client: TestClient, auth_headers: dict):
        """Test that server errors are handled gracefully."""
        # Try to trigger errors with extreme values or edge cases
        response = client.get(
            "/api/v1/role-views/views/permissions/admin", headers=auth_headers
        )

        # Should either succeed or return a proper error
        assert response.status_code in [200, 400, 500]

        if response.status_code == 500:
            data = response.json()
            assert "detail" in data
            # Should not leak sensitive information
            assert "An error occurred" in data["detail"]

    def test_malformed_request(self, client: TestClient, auth_headers: dict):
        """Test handling of malformed requests."""
        # Send invalid JSON
        response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            data="invalid json",
        )

        # Should return validation error
        assert response.status_code in [400, 422]


class TestRoleViewsIntegration:
    """Integration tests for role views endpoints."""

    def test_full_role_workflow_admin(self, client: TestClient, auth_headers: dict):
        """Test complete workflow for admin role."""
        # 1. List all roles
        roles_response = client.get(
            "/api/v1/role-views/views/roles", headers=auth_headers
        )
        assert roles_response.status_code == 200
        roles = roles_response.json()
        assert "admin" in roles

        # 2. Get admin config
        config_response = client.get(
            "/api/v1/role-views/views/config/admin", headers=auth_headers
        )
        assert config_response.status_code == 200
        config = config_response.json()
        assert config["role"] == "admin"

        # 3. Check access to schedules
        access_response = client.post(
            "/api/v1/role-views/views/check-access",
            headers=auth_headers,
            params={"role": "admin", "endpoint_category": "schedules"},
        )
        assert access_response.status_code == 200
        access_data = access_response.json()
        assert access_data["can_access"] is True

    def test_full_role_workflow_faculty(self, client: TestClient, db: Session):
        """Test complete workflow for faculty role."""
        # Create faculty user
        faculty = User(
            id=uuid4(),
            username="workflowfaculty",
            email="workflow@test.org",
            hashed_password=get_password_hash("testpass123"),
            role="faculty",
            is_active=True,
        )
        db.add(faculty)
        db.commit()

        # Login
        login_response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "workflowfaculty", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get current user config
        config_response = client.get("/api/v1/role-views/views/config", headers=headers)
        assert config_response.status_code == 200
        assert config_response.json()["role"] == "faculty"

        # 2. Get faculty permissions
        perms_response = client.get(
            "/api/v1/role-views/views/permissions/faculty", headers=headers
        )
        assert perms_response.status_code == 200

        # 3. Get all permissions
        all_perms_response = client.get(
            "/api/v1/role-views/views/permissions", headers=headers
        )
        assert all_perms_response.status_code == 200
        assert "faculty" in all_perms_response.json()

    def test_permission_hierarchy(self, client: TestClient, auth_headers: dict):
        """Test that permission hierarchy is enforced."""
        # Get all permissions
        response = client.get(
            "/api/v1/role-views/views/permissions", headers=auth_headers
        )

        assert response.status_code == 200
        all_perms = response.json()

        # Admin should have more or equal permissions compared to coordinator
        if "admin" in all_perms and "coordinator" in all_perms:
            admin_can_edit = all_perms["admin"].get("can_edit_schedules", False)
            # Admin should be able to edit schedules
            assert admin_can_edit is True

        # Resident should have limited permissions
        if "resident" in all_perms:
            resident_perms = all_perms["resident"]
            resident_can_view = resident_perms.get("can_view_schedules", False)
            assert isinstance(resident_can_view, bool)
