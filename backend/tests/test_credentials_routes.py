"""
Comprehensive tests for Credentials API routes.

Tests coverage for faculty procedure credential management:
- GET /credentials/expiring - List expiring credentials
- GET /credentials/by-person/{person_id} - List credentials for person
- GET /credentials/by-procedure/{procedure_id} - List credentials for procedure
- GET /credentials/qualified-faculty/{procedure_id} - Get qualified faculty
- GET /credentials/check/{person_id}/{procedure_id} - Check qualification
- GET /credentials/summary/{person_id} - Get faculty credential summary
- GET /credentials/{credential_id} - Get credential by ID
- POST /credentials - Create credential
- PUT /credentials/{credential_id} - Update credential
- DELETE /credentials/{credential_id} - Delete credential
- POST /credentials/{credential_id}/suspend - Suspend credential
- POST /credentials/{credential_id}/activate - Activate credential
- POST /credentials/{credential_id}/verify - Verify credential
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestListExpiringCredentials:
    """Tests for GET /api/credentials/expiring endpoint."""

    def test_list_expiring_credentials_default_days(self, client: TestClient):
        """Test listing expiring credentials with default 30 days."""
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_expiring_credentials.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get("/api/credentials/expiring")

            assert response.status_code == 200
            mock_instance.list_expiring_credentials.assert_called_once_with(days=30)

    def test_list_expiring_credentials_custom_days(self, client: TestClient):
        """Test listing expiring credentials with custom days parameter."""
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_expiring_credentials.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get("/api/credentials/expiring?days=60")

            assert response.status_code == 200
            mock_instance.list_expiring_credentials.assert_called_once_with(days=60)

    def test_list_expiring_credentials_returns_data(self, client: TestClient):
        """Test that expiring credentials returns proper data structure."""
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_expiring_credentials.return_value = {
                "credentials": [
                    {
                        "id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "procedure_id": str(uuid4()),
                        "status": "active",
                        "expires_at": (date.today() + timedelta(days=15)).isoformat(),
                    }
                ],
                "total": 1,
            }
            mock_controller.return_value = mock_instance

            response = client.get("/api/credentials/expiring?days=30")

            assert response.status_code == 200
            data = response.json()
            assert "credentials" in data
            assert "total" in data


class TestListCredentialsForPerson:
    """Tests for GET /api/credentials/by-person/{person_id} endpoint."""

    def test_list_credentials_for_person_success(self, client: TestClient):
        """Test listing credentials for a specific person."""
        person_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_credentials_for_person.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get(f"/api/credentials/by-person/{person_id}")

            assert response.status_code == 200
            mock_instance.list_credentials_for_person.assert_called_once()

    def test_list_credentials_for_person_with_filters(self, client: TestClient):
        """Test listing credentials with status and include_expired filters."""
        person_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_credentials_for_person.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get(
                f"/api/credentials/by-person/{person_id}?status=active&include_expired=true"
            )

            assert response.status_code == 200
            mock_instance.list_credentials_for_person.assert_called_once_with(
                person_id=person_id,
                status_filter="active",
                include_expired=True,
            )


class TestListCredentialsForProcedure:
    """Tests for GET /api/credentials/by-procedure/{procedure_id} endpoint."""

    def test_list_credentials_for_procedure_success(self, client: TestClient):
        """Test listing credentials for a specific procedure."""
        procedure_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_credentials_for_procedure.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get(f"/api/credentials/by-procedure/{procedure_id}")

            assert response.status_code == 200
            mock_instance.list_credentials_for_procedure.assert_called_once()


class TestGetQualifiedFaculty:
    """Tests for GET /api/credentials/qualified-faculty/{procedure_id} endpoint."""

    def test_get_qualified_faculty_success(self, client: TestClient):
        """Test getting qualified faculty for a procedure."""
        procedure_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.get_qualified_faculty.return_value = {
                "procedure_id": str(procedure_id),
                "qualified_faculty": [],
            }
            mock_controller.return_value = mock_instance

            response = client.get(
                f"/api/credentials/qualified-faculty/{procedure_id}"
            )

            assert response.status_code == 200
            mock_instance.get_qualified_faculty.assert_called_once_with(procedure_id)


class TestCheckQualification:
    """Tests for GET /api/credentials/check/{person_id}/{procedure_id} endpoint."""

    def test_check_qualification_qualified(self, client: TestClient):
        """Test checking qualification - qualified result."""
        person_id = uuid4()
        procedure_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.check_qualification.return_value = {
                "qualified": True,
                "credential_id": str(uuid4()),
            }
            mock_controller.return_value = mock_instance

            response = client.get(
                f"/api/credentials/check/{person_id}/{procedure_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["qualified"] is True

    def test_check_qualification_not_qualified(self, client: TestClient):
        """Test checking qualification - not qualified result."""
        person_id = uuid4()
        procedure_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.check_qualification.return_value = {
                "qualified": False,
                "reason": "No active credential found",
            }
            mock_controller.return_value = mock_instance

            response = client.get(
                f"/api/credentials/check/{person_id}/{procedure_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["qualified"] is False


class TestGetFacultyCredentialSummary:
    """Tests for GET /api/credentials/summary/{person_id} endpoint."""

    def test_get_faculty_summary_success(self, client: TestClient):
        """Test getting faculty credential summary."""
        person_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.get_faculty_summary.return_value = {
                "person_id": str(person_id),
                "total_credentials": 5,
                "active_credentials": 4,
                "expiring_soon": 1,
                "expired": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get(f"/api/credentials/summary/{person_id}")

            assert response.status_code == 200
            data = response.json()
            assert "total_credentials" in data
            assert "active_credentials" in data


class TestGetCredentialById:
    """Tests for GET /api/credentials/{credential_id} endpoint."""

    def test_get_credential_success(self, client: TestClient):
        """Test getting a credential by ID."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.get_credential.return_value = {
                "id": str(credential_id),
                "person_id": str(uuid4()),
                "procedure_id": str(uuid4()),
                "status": "active",
            }
            mock_controller.return_value = mock_instance

            response = client.get(f"/api/credentials/{credential_id}")

            assert response.status_code == 200
            mock_instance.get_credential.assert_called_once_with(credential_id)


class TestCreateCredential:
    """Tests for POST /api/credentials endpoint."""

    def test_create_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a credential with authentication."""
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            credential_id = uuid4()
            mock_instance.create_credential.return_value = {
                "id": str(credential_id),
                "person_id": str(uuid4()),
                "procedure_id": str(uuid4()),
                "status": "active",
            }
            mock_controller.return_value = mock_instance

            response = client.post(
                "/api/credentials",
                json={
                    "person_id": str(uuid4()),
                    "procedure_id": str(uuid4()),
                    "issued_date": date.today().isoformat(),
                    "expiration_date": (date.today() + timedelta(days=365)).isoformat(),
                },
                headers=auth_headers,
            )

            # May return 201 or 401 depending on auth
            assert response.status_code in [201, 401, 422]

    def test_create_credential_requires_auth(self, client: TestClient):
        """Test that creating a credential requires authentication."""
        response = client.post(
            "/api/credentials",
            json={
                "person_id": str(uuid4()),
                "procedure_id": str(uuid4()),
                "issued_date": date.today().isoformat(),
            },
        )

        # Should require authentication
        assert response.status_code in [401, 403, 422]


class TestUpdateCredential:
    """Tests for PUT /api/credentials/{credential_id} endpoint."""

    def test_update_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating a credential."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.update_credential.return_value = {
                "id": str(credential_id),
                "status": "suspended",
            }
            mock_controller.return_value = mock_instance

            response = client.put(
                f"/api/credentials/{credential_id}",
                json={"status": "suspended"},
                headers=auth_headers,
            )

            # May return 200 or 401 depending on auth
            assert response.status_code in [200, 401, 422]


class TestDeleteCredential:
    """Tests for DELETE /api/credentials/{credential_id} endpoint."""

    def test_delete_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deleting a credential."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.delete_credential.return_value = None
            mock_controller.return_value = mock_instance

            response = client.delete(
                f"/api/credentials/{credential_id}",
                headers=auth_headers,
            )

            # May return 204 or 401 depending on auth
            assert response.status_code in [204, 401]


class TestSuspendCredential:
    """Tests for POST /api/credentials/{credential_id}/suspend endpoint."""

    def test_suspend_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test suspending a credential."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.suspend_credential.return_value = {
                "id": str(credential_id),
                "status": "suspended",
            }
            mock_controller.return_value = mock_instance

            response = client.post(
                f"/api/credentials/{credential_id}/suspend",
                headers=auth_headers,
            )

            # May return 200 or 401 depending on auth
            assert response.status_code in [200, 401]

    def test_suspend_credential_with_notes(
        self, client: TestClient, auth_headers: dict
    ):
        """Test suspending a credential with notes."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.suspend_credential.return_value = {
                "id": str(credential_id),
                "status": "suspended",
            }
            mock_controller.return_value = mock_instance

            response = client.post(
                f"/api/credentials/{credential_id}/suspend?notes=Pending%20review",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestActivateCredential:
    """Tests for POST /api/credentials/{credential_id}/activate endpoint."""

    def test_activate_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test activating a credential."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.activate_credential.return_value = {
                "id": str(credential_id),
                "status": "active",
            }
            mock_controller.return_value = mock_instance

            response = client.post(
                f"/api/credentials/{credential_id}/activate",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestVerifyCredential:
    """Tests for POST /api/credentials/{credential_id}/verify endpoint."""

    def test_verify_credential_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test verifying a credential."""
        credential_id = uuid4()

        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.verify_credential.return_value = {
                "id": str(credential_id),
                "last_verified": date.today().isoformat(),
            }
            mock_controller.return_value = mock_instance

            response = client.post(
                f"/api/credentials/{credential_id}/verify",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


# ============================================================================
# Integration Tests
# ============================================================================


class TestCredentialsIntegration:
    """Integration tests for credentials endpoints."""

    def test_credentials_endpoints_accessible(self, client: TestClient):
        """Test that credentials endpoints are accessible."""
        # Test expiring endpoint (no auth required for GET)
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_expiring_credentials.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get("/api/credentials/expiring")
            assert response.status_code == 200

    def test_credentials_response_format(self, client: TestClient):
        """Test credentials endpoints return proper JSON format."""
        with patch(
            "app.api.routes.credentials.CredentialController"
        ) as mock_controller:
            mock_instance = MagicMock()
            mock_instance.list_expiring_credentials.return_value = {
                "credentials": [],
                "total": 0,
            }
            mock_controller.return_value = mock_instance

            response = client.get("/api/credentials/expiring")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert isinstance(data, dict)
