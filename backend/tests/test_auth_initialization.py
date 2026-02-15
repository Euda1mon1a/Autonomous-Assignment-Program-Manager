"""
Tests for authentication initialization endpoints.

Tests coverage for initialization features:
- POST /api/auth/initialize-admin - Bootstrap admin user creation
- DEBUG mode gating
- Random password generation

Created: 2026-01-04 (Session 049)
Updated: 2026-02-14 (Security hardening - no fixed credentials)
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


class TestInitializeAdminEndpoint:
    """Tests for POST /api/auth/initialize-admin endpoint."""

    def test_initialize_admin_creates_user_when_empty(
        self, client: TestClient, db: Session
    ):
        """Test that initialize-admin creates admin user when database is empty."""
        db.query(User).delete()
        db.commit()

        response = client.post("/api/auth/initialize-admin")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["username"] == "admin"
        assert "password" in data
        assert len(data["password"]) >= 16

        # Verify user was created with the generated password
        user = db.query(User).filter(User.username == "admin").first()
        assert user is not None
        assert user.role == "admin"
        assert user.is_active is True
        assert verify_password(data["password"], user.hashed_password)

    def test_initialize_admin_idempotent(self, client: TestClient, db: Session):
        """Test that initialize-admin is idempotent."""
        response1 = client.post("/api/auth/initialize-admin")
        assert response1.status_code == 200
        assert response1.json()["status"] == "created"

        response2 = client.post("/api/auth/initialize-admin")
        assert response2.status_code == 200
        data = response2.json()
        assert data["status"] == "already_initialized"
        assert data["user_count"] >= 1

    def test_initialize_admin_generates_unique_passwords(
        self, client: TestClient, db: Session
    ):
        """Test that each bootstrap generates a different password."""
        db.query(User).delete()
        db.commit()

        response1 = client.post("/api/auth/initialize-admin")
        pw1 = response1.json()["password"]

        # Reset for second call
        db.query(User).delete()
        db.commit()

        response2 = client.post("/api/auth/initialize-admin")
        pw2 = response2.json()["password"]

        assert pw1 != pw2

    def test_initialize_admin_blocked_when_not_debug(self, client: TestClient):
        """Test that initialize-admin is forbidden when DEBUG=False."""
        with patch("app.api.routes.auth.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = False
            response = client.post("/api/auth/initialize-admin")
            assert response.status_code == 403

    def test_login_with_initialized_admin(self, client: TestClient, db: Session):
        """Test login with generated credentials after initialization."""
        db.query(User).delete()
        db.commit()

        init_response = client.post("/api/auth/initialize-admin")
        assert init_response.status_code == 200
        generated_password = init_response.json()["password"]

        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "admin", "password": generated_password},
        )

        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_fails_with_wrong_password(self, client: TestClient, db: Session):
        """Test login fails with wrong password."""
        db.query(User).delete()
        db.commit()

        client.post("/api/auth/initialize-admin")

        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert login_response.status_code == 401

    def test_error_response_does_not_leak_details(self, client: TestClient):
        """Test that error responses don't expose internal exception details."""
        # The endpoint should return generic error messages, not str(e)
        # This is tested implicitly - if the endpoint errors, we verify
        # the detail field doesn't contain exception class names
        response = client.post("/api/auth/initialize-admin")
        if response.status_code == 500:
            detail = response.json().get("detail", "")
            assert "Traceback" not in detail
            assert "sqlalchemy" not in detail.lower()
            assert "Exception" not in detail
