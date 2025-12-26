"""Tests for credentials API routes.

Tests the faculty procedure credentials functionality including:
- Credential CRUD operations
- Expiring credential tracking
- Qualification checks
- Credential status management (suspend, activate, verify)
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestCredentialRoutes:
    """Test suite for credential API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_create_credential_requires_auth(self, client: TestClient):
        """Test that creating credential requires authentication."""
        response = client.post(
            "/api/credentials",
            json={
                "person_id": str(uuid4()),
                "procedure_id": str(uuid4()),
                "status": "active",
            },
        )
        assert response.status_code == 401

    def test_update_credential_requires_auth(self, client: TestClient):
        """Test that updating credential requires authentication."""
        response = client.put(
            f"/api/credentials/{uuid4()}",
            json={"status": "suspended"},
        )
        assert response.status_code == 401

    def test_delete_credential_requires_auth(self, client: TestClient):
        """Test that deleting credential requires authentication."""
        response = client.delete(f"/api/credentials/{uuid4()}")
        assert response.status_code == 401

    def test_suspend_credential_requires_auth(self, client: TestClient):
        """Test that suspending credential requires authentication."""
        response = client.post(f"/api/credentials/{uuid4()}/suspend")
        assert response.status_code == 401

    def test_activate_credential_requires_auth(self, client: TestClient):
        """Test that activating credential requires authentication."""
        response = client.post(f"/api/credentials/{uuid4()}/activate")
        assert response.status_code == 401

    def test_verify_credential_requires_auth(self, client: TestClient):
        """Test that verifying credential requires authentication."""
        response = client.post(f"/api/credentials/{uuid4()}/verify")
        assert response.status_code == 401

    # ========================================================================
    # List Expiring Credentials Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_list_expiring_credentials_default(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test listing expiring credentials with default 30 days."""
        mock_controller = MagicMock()
        mock_controller.list_expiring_credentials.return_value = {
            "credentials": [
                {
                    "id": str(uuid4()),
                    "person_id": str(uuid4()),
                    "procedure_id": str(uuid4()),
                    "expires_at": (date.today() + timedelta(days=15)).isoformat(),
                    "status": "active",
                }
            ],
            "total": 1,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get("/api/credentials/expiring")
        assert response.status_code == 200

        mock_controller.list_expiring_credentials.assert_called_once_with(days=30)

    @patch("app.api.routes.credentials.CredentialController")
    def test_list_expiring_credentials_custom_days(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test listing expiring credentials with custom days parameter."""
        mock_controller = MagicMock()
        mock_controller.list_expiring_credentials.return_value = {
            "credentials": [],
            "total": 0,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get("/api/credentials/expiring?days=60")
        assert response.status_code == 200

        mock_controller.list_expiring_credentials.assert_called_once_with(days=60)

    # ========================================================================
    # List Credentials by Person Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_list_credentials_for_person_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test listing credentials for a specific person."""
        person_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.list_credentials_for_person.return_value = {
            "credentials": [
                {
                    "id": str(uuid4()),
                    "person_id": str(person_id),
                    "procedure_id": str(uuid4()),
                    "procedure_name": "Colonoscopy",
                    "status": "active",
                }
            ],
            "total": 1,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/by-person/{person_id}")
        assert response.status_code == 200

        data = response.json()
        assert "credentials" in data

    @patch("app.api.routes.credentials.CredentialController")
    def test_list_credentials_for_person_with_filters(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test listing credentials with status filter and include_expired."""
        person_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.list_credentials_for_person.return_value = {
            "credentials": [],
            "total": 0,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(
            f"/api/credentials/by-person/{person_id}?status=active&include_expired=true"
        )
        assert response.status_code == 200

        mock_controller.list_credentials_for_person.assert_called_once_with(
            person_id=person_id,
            status_filter="active",
            include_expired=True,
        )

    # ========================================================================
    # List Credentials by Procedure Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_list_credentials_for_procedure_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test listing credentials for a specific procedure."""
        procedure_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.list_credentials_for_procedure.return_value = {
            "credentials": [
                {
                    "id": str(uuid4()),
                    "person_id": str(uuid4()),
                    "procedure_id": str(procedure_id),
                    "person_name": "Dr. Smith",
                    "status": "active",
                }
            ],
            "total": 1,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/by-procedure/{procedure_id}")
        assert response.status_code == 200

    # ========================================================================
    # Qualified Faculty Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_get_qualified_faculty_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test getting qualified faculty for a procedure."""
        procedure_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.get_qualified_faculty.return_value = {
            "procedure_id": str(procedure_id),
            "procedure_name": "EGD",
            "qualified_faculty": [
                {"person_id": str(uuid4()), "name": "Dr. Smith"},
                {"person_id": str(uuid4()), "name": "Dr. Jones"},
            ],
            "count": 2,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/qualified-faculty/{procedure_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 2
        assert len(data["qualified_faculty"]) == 2

    @patch("app.api.routes.credentials.CredentialController")
    def test_get_qualified_faculty_none(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test getting qualified faculty when none exist."""
        procedure_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.get_qualified_faculty.return_value = {
            "procedure_id": str(procedure_id),
            "procedure_name": "Rare Procedure",
            "qualified_faculty": [],
            "count": 0,
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/qualified-faculty/{procedure_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0

    # ========================================================================
    # Check Qualification Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_check_qualification_qualified(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test checking qualification when faculty is qualified."""
        person_id = uuid4()
        procedure_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.check_qualification.return_value = {
            "person_id": str(person_id),
            "procedure_id": str(procedure_id),
            "is_qualified": True,
            "credential_status": "active",
            "expires_at": (date.today() + timedelta(days=365)).isoformat(),
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/check/{person_id}/{procedure_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["is_qualified"] is True

    @patch("app.api.routes.credentials.CredentialController")
    def test_check_qualification_not_qualified(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test checking qualification when faculty is not qualified."""
        person_id = uuid4()
        procedure_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.check_qualification.return_value = {
            "person_id": str(person_id),
            "procedure_id": str(procedure_id),
            "is_qualified": False,
            "reason": "No credential found",
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/check/{person_id}/{procedure_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["is_qualified"] is False

    # ========================================================================
    # Faculty Credential Summary Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_get_faculty_summary_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test getting faculty credential summary."""
        person_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.get_faculty_summary.return_value = {
            "person_id": str(person_id),
            "person_name": "Dr. Smith",
            "total_credentials": 5,
            "active_credentials": 4,
            "suspended_credentials": 0,
            "expired_credentials": 1,
            "expiring_soon": 2,
            "procedures": [
                {"name": "Colonoscopy", "status": "active"},
                {"name": "EGD", "status": "active"},
            ],
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/summary/{person_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total_credentials"] == 5
        assert data["active_credentials"] == 4

    # ========================================================================
    # Get Single Credential Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_get_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
    ):
        """Test getting a credential by ID."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.get_credential.return_value = {
            "id": str(credential_id),
            "person_id": str(uuid4()),
            "procedure_id": str(uuid4()),
            "status": "active",
            "issued_at": date.today().isoformat(),
            "expires_at": (date.today() + timedelta(days=365)).isoformat(),
        }
        mock_controller_class.return_value = mock_controller

        response = client.get(f"/api/credentials/{credential_id}")
        assert response.status_code == 200

    # ========================================================================
    # Create Credential Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_create_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful credential creation."""
        person_id = uuid4()
        procedure_id = uuid4()
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.create_credential.return_value = {
            "id": str(credential_id),
            "person_id": str(person_id),
            "procedure_id": str(procedure_id),
            "status": "active",
            "issued_at": date.today().isoformat(),
            "expires_at": (date.today() + timedelta(days=365)).isoformat(),
        }
        mock_controller_class.return_value = mock_controller

        response = client.post(
            "/api/credentials",
            headers=auth_headers,
            json={
                "person_id": str(person_id),
                "procedure_id": str(procedure_id),
                "status": "active",
                "expires_at": (date.today() + timedelta(days=365)).isoformat(),
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["person_id"] == str(person_id)

    # ========================================================================
    # Update Credential Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_update_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful credential update."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.update_credential.return_value = {
            "id": str(credential_id),
            "person_id": str(uuid4()),
            "procedure_id": str(uuid4()),
            "status": "suspended",
            "notes": "Under review",
        }
        mock_controller_class.return_value = mock_controller

        response = client.put(
            f"/api/credentials/{credential_id}",
            headers=auth_headers,
            json={
                "status": "suspended",
                "notes": "Under review",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "suspended"

    # ========================================================================
    # Delete Credential Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_delete_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful credential deletion."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.delete_credential.return_value = None
        mock_controller_class.return_value = mock_controller

        response = client.delete(
            f"/api/credentials/{credential_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    # ========================================================================
    # Suspend/Activate/Verify Credential Tests
    # ========================================================================

    @patch("app.api.routes.credentials.CredentialController")
    def test_suspend_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test suspending a credential."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.suspend_credential.return_value = {
            "id": str(credential_id),
            "status": "suspended",
            "notes": "Administrative suspension",
        }
        mock_controller_class.return_value = mock_controller

        response = client.post(
            f"/api/credentials/{credential_id}/suspend?notes=Administrative%20suspension",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "suspended"

    @patch("app.api.routes.credentials.CredentialController")
    def test_activate_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test activating a credential."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.activate_credential.return_value = {
            "id": str(credential_id),
            "status": "active",
        }
        mock_controller_class.return_value = mock_controller

        response = client.post(
            f"/api/credentials/{credential_id}/activate",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "active"

    @patch("app.api.routes.credentials.CredentialController")
    def test_verify_credential_success(
        self,
        mock_controller_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test verifying a credential."""
        credential_id = uuid4()
        mock_controller = MagicMock()
        mock_controller.verify_credential.return_value = {
            "id": str(credential_id),
            "status": "active",
            "last_verified_at": date.today().isoformat(),
        }
        mock_controller_class.return_value = mock_controller

        response = client.post(
            f"/api/credentials/{credential_id}/verify",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "last_verified_at" in data
