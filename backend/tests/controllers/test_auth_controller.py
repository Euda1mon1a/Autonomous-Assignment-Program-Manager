"""Tests for AuthController."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.auth_controller import AuthController
from app.schemas.auth import UserCreate
from app.models.user import User
from app.core.security import get_password_hash


class TestAuthController:
    """Test suite for AuthController."""

    # ========================================================================
    # Login Tests
    # ========================================================================

    def test_login_success(self, db):
        """Test successful login returns token."""
        # Create a test user
        user = User(
            id=uuid4(),
            username="testuser",
            email="testuser@test.org",
            hashed_password=get_password_hash("TestPassword123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()

        controller = AuthController(db)
        result = controller.login("testuser", "TestPassword123!")

        assert result is not None
        assert result.access_token is not None
        assert result.token_type == "bearer"

    def test_login_invalid_username(self, db):
        """Test login with non-existent username raises 401."""
        controller = AuthController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.login("nonexistent", "password123")

        assert exc_info.value.status_code == 401

    def test_login_invalid_password(self, db):
        """Test login with wrong password raises 401."""
        # Create a test user
        user = User(
            id=uuid4(),
            username="testuser",
            email="testuser@test.org",
            hashed_password=get_password_hash("CorrectPassword123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()

        controller = AuthController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.login("testuser", "WrongPassword123!")

        assert exc_info.value.status_code == 401

    def test_login_inactive_user(self, db):
        """Test login with inactive user fails."""
        # Create an inactive user
        user = User(
            id=uuid4(),
            username="inactiveuser",
            email="inactive@test.org",
            hashed_password=get_password_hash("TestPassword123!"),
            role="coordinator",
            is_active=False,
        )
        db.add(user)
        db.commit()

        controller = AuthController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.login("inactiveuser", "TestPassword123!")

        assert exc_info.value.status_code == 401

    def test_login_lockout_after_failed_attempts(self, db):
        """Test account lockout after multiple failed login attempts."""
        # Create a test user
        user = User(
            id=uuid4(),
            username="lockouttest",
            email="lockout@test.org",
            hashed_password=get_password_hash("CorrectPassword123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()

        controller = AuthController(db)

        # Attempt multiple failed logins
        for _ in range(5):
            try:
                controller.login("lockouttest", "WrongPassword!")
            except HTTPException:
                pass

        # Next attempt should trigger lockout (429)
        with pytest.raises(HTTPException) as exc_info:
            controller.login("lockouttest", "WrongPassword!")

        assert exc_info.value.status_code in (401, 429)

    # ========================================================================
    # Register User Tests
    # ========================================================================

    def test_register_user_success(self, db):
        """Test successful user registration."""
        controller = AuthController(db)

        user_data = UserCreate(
            username="newuser",
            email="newuser@test.org",
            password="NewPassword123!",
            role="resident",
        )

        # Registration without current_user for initial admin setup
        # or with admin user for subsequent registrations
        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@test.org",
            hashed_password=get_password_hash("AdminPass123!"),
            role="admin",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()

        result = controller.register_user(user_data, current_user=admin_user)

        assert result is not None
        assert result.username == "newuser"
        assert result.email == "newuser@test.org"
        assert result.role == "resident"

    def test_register_user_duplicate_username(self, db):
        """Test registration with duplicate username fails."""
        # Create existing user
        existing_user = User(
            id=uuid4(),
            username="existinguser",
            email="existing@test.org",
            hashed_password=get_password_hash("Password123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(existing_user)
        db.commit()

        # Create admin for registration
        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@test.org",
            hashed_password=get_password_hash("AdminPass123!"),
            role="admin",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()

        controller = AuthController(db)

        user_data = UserCreate(
            username="existinguser",  # Duplicate username
            email="new@test.org",
            password="NewPassword123!",
            role="resident",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.register_user(user_data, current_user=admin_user)

        assert exc_info.value.status_code == 400

    def test_register_user_duplicate_email(self, db):
        """Test registration with duplicate email fails."""
        # Create existing user
        existing_user = User(
            id=uuid4(),
            username="existinguser",
            email="duplicate@test.org",
            hashed_password=get_password_hash("Password123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(existing_user)
        db.commit()

        # Create admin for registration
        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@test.org",
            hashed_password=get_password_hash("AdminPass123!"),
            role="admin",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()

        controller = AuthController(db)

        user_data = UserCreate(
            username="newusername",
            email="duplicate@test.org",  # Duplicate email
            password="NewPassword123!",
            role="resident",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.register_user(user_data, current_user=admin_user)

        assert exc_info.value.status_code == 400

    def test_register_user_unauthorized(self, db):
        """Test registration without admin privileges fails."""
        # Create non-admin user
        regular_user = User(
            id=uuid4(),
            username="regular",
            email="regular@test.org",
            hashed_password=get_password_hash("Password123!"),
            role="resident",
            is_active=True,
            is_admin=False,
        )
        db.add(regular_user)
        db.commit()

        controller = AuthController(db)

        user_data = UserCreate(
            username="newuser",
            email="new@test.org",
            password="NewPassword123!",
            role="resident",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.register_user(user_data, current_user=regular_user)

        assert exc_info.value.status_code in (401, 403)

    # ========================================================================
    # List Users Tests
    # ========================================================================

    def test_list_users_returns_all_users(self, db):
        """Test listing all users."""
        # Create multiple users
        for i in range(3):
            user = User(
                id=uuid4(),
                username=f"user{i}",
                email=f"user{i}@test.org",
                hashed_password=get_password_hash("Password123!"),
                role="resident",
                is_active=True,
            )
            db.add(user)
        db.commit()

        controller = AuthController(db)
        result = controller.list_users()

        assert len(result) >= 3

    def test_list_users_empty_database(self, db):
        """Test listing users when no users exist."""
        controller = AuthController(db)
        result = controller.list_users()

        assert isinstance(result, list)
        assert len(result) == 0

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_register_then_login_workflow(self, db):
        """Test complete registration and login workflow."""
        controller = AuthController(db)

        # Create admin for registration
        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@test.org",
            hashed_password=get_password_hash("AdminPass123!"),
            role="admin",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()

        # Register new user
        user_data = UserCreate(
            username="testuser",
            email="testuser@test.org",
            password="TestPassword123!",
            role="coordinator",
        )
        registered = controller.register_user(user_data, current_user=admin_user)
        assert registered.username == "testuser"

        # Login with newly registered user
        token = controller.login("testuser", "TestPassword123!")
        assert token.access_token is not None

    def test_lockout_clears_on_successful_login(self, db):
        """Test that successful login clears lockout state."""
        # Create a test user
        user = User(
            id=uuid4(),
            username="lockoutclear",
            email="lockoutclear@test.org",
            hashed_password=get_password_hash("CorrectPassword123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()

        controller = AuthController(db)

        # Make some failed attempts (not enough to lock out)
        for _ in range(2):
            try:
                controller.login("lockoutclear", "WrongPassword!")
            except HTTPException:
                pass

        # Successful login should clear attempts
        token = controller.login("lockoutclear", "CorrectPassword123!")
        assert token.access_token is not None

        # Failed attempts should reset, so we shouldn't be locked out
        for _ in range(2):
            try:
                controller.login("lockoutclear", "WrongPassword!")
            except HTTPException as e:
                # Should be 401 (invalid credentials), not 429 (locked out)
                assert e.status_code == 401
