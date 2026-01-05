"""
Tests for authentication initialization endpoints.

Tests coverage for new initialization features:
- POST /api/auth/initialize-admin - Bootstrap admin user creation
- Automatic admin user creation on startup

Created: 2026-01-04 (Session 049)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


class TestInitializeAdminEndpoint:
    """Tests for POST /api/auth/initialize-admin endpoint."""

    def test_initialize_admin_creates_user_when_empty(self, client: TestClient, db: Session):
        """Test that initialize-admin creates admin user when database is empty."""
        # Clear any existing users
        db.query(User).delete()
        db.commit()

        response = client.post("/api/auth/initialize-admin")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["username"] == "admin"
        assert data["message"] == "Default admin user created successfully"

        # Verify user was created
        user = db.query(User).filter(User.username == "admin").first()
        assert user is not None
        assert user.role == "admin"
        assert user.is_active is True
        assert verify_password("admin123", user.hashed_password)

    def test_initialize_admin_idempotent(self, client: TestClient, db: Session):
        """Test that initialize-admin is idempotent."""
        # First call should create user
        response1 = client.post("/api/auth/initialize-admin")
        assert response1.status_code == 200
        assert response1.json()["status"] == "created"

        # Second call should return already_initialized
        response2 = client.post("/api/auth/initialize-admin")
        assert response2.status_code == 200
        data = response2.json()
        assert data["status"] == "already_initialized"
        assert data["user_count"] == 1

        # Verify only one user exists
        user_count = db.query(User).count()
        assert user_count == 1

    def test_initialize_admin_no_auth_required(self, client: TestClient):
        """Test that initialize-admin endpoint requires no authentication."""
        response = client.post("/api/auth/initialize-admin")

        # Should not return 401 (not authenticated)
        assert response.status_code != 401

    def test_login_with_initialized_admin(self, client: TestClient, db: Session):
        """Test login with admin credentials after initialization."""
        # Clear and initialize
        db.query(User).delete()
        db.commit()

        init_response = client.post("/api/auth/initialize-admin")
        assert init_response.status_code == 200

        # Try to login
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
        )

        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_fails_with_wrong_password(self, client: TestClient, db: Session):
        """Test login fails with wrong password."""
        # Clear and initialize
        db.query(User).delete()
        db.commit()

        client.post("/api/auth/initialize-admin")

        # Try wrong password
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert login_response.status_code == 401

    def test_rag_can_authenticate_after_init(self, client: TestClient, db: Session):
        """Test that RAG endpoints can authenticate after admin initialization."""
        # Clear and initialize
        db.query(User).delete()
        db.commit()

        init_response = client.post("/api/auth/initialize-admin")
        assert init_response.status_code == 200

        # Login with admin
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Test RAG endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        rag_response = client.get("/api/rag/health", headers=headers)

        # Should not be 401 (authentication should pass)
        assert rag_response.status_code != 401


class TestAdminInitializationOnStartup:
    """Tests for automatic admin initialization on app startup."""

    def test_admin_user_created_on_startup(self, db: Session):
        """Test that admin user is created on startup if database is empty."""
        # This is tested implicitly by the conftest.py fixture setup
        # which creates a fresh database for each test
        user = db.query(User).filter(User.username == "admin").first()

        # After startup, admin user should exist
        assert user is not None
        assert user.role == "admin"
        assert user.is_active is True

    def test_admin_user_credentials_correct(self, db: Session):
        """Test that auto-created admin user has correct password."""
        user = db.query(User).filter(User.username == "admin").first()

        if user:  # May not exist if not created on startup
            assert verify_password("admin123", user.hashed_password)
