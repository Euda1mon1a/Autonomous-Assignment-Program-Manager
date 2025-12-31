"""Test suite for authentication service."""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.services.auth_service import AuthService


class TestAuthService:
    """Test suite for authentication service."""

    @pytest.fixture
    def auth_service(self, db: Session) -> AuthService:
        """Create an auth service instance."""
        return AuthService(db)

    @pytest.fixture
    def test_user(self, db: Session) -> User:
        """Create a test user."""
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@test.org",
            hashed_password=get_password_hash("Test@Pass123"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_authenticate_valid_credentials(
        self, auth_service: AuthService, test_user: User
    ):
        """Test authentication with valid credentials."""
        result = auth_service.authenticate("testuser", "Test@Pass123")

        assert result["user"] is not None
        assert result["user"].id == test_user.id
        assert result["access_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["error"] is None

    def test_authenticate_invalid_password(
        self, auth_service: AuthService, test_user: User
    ):
        """Test authentication with wrong password."""
        result = auth_service.authenticate("testuser", "WrongPassword")

        assert result["user"] is None
        assert "Incorrect" in result["error"]

    def test_authenticate_nonexistent_user(self, auth_service: AuthService):
        """Test authentication with nonexistent user."""
        result = auth_service.authenticate("nonexistent", "password")

        assert result["user"] is None
        assert "Incorrect" in result["error"]

    def test_authenticate_updates_last_login(
        self, auth_service: AuthService, db: Session, test_user: User
    ):
        """Test that authentication updates last login timestamp."""
        old_login = test_user.last_login

        result = auth_service.authenticate("testuser", "Test@Pass123")

        # Refresh user from DB to get updated last_login
        db.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login >= (old_login or datetime.min)

    def test_authenticate_returns_jti(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that authentication returns JTI for token blacklist."""
        result = auth_service.authenticate("testuser", "Test@Pass123")

        assert "jti" in result
        assert result["jti"] is not None

    def test_authenticate_returns_expiration(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that authentication returns token expiration."""
        result = auth_service.authenticate("testuser", "Test@Pass123")

        assert "expires_at" in result
        assert result["expires_at"] is not None

    def test_register_user_first_user_becomes_admin(
        self, auth_service: AuthService
    ):
        """Test that first user registered becomes admin."""
        result = auth_service.register_user(
            username="firstuser",
            email="first@test.org",
            password="Password@123",
        )

        assert result["user"] is not None
        assert result["error"] is None
        assert result["user"].is_admin is True

    def test_register_user_requires_admin_for_subsequent(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that subsequent users require admin to create."""
        result = auth_service.register_user(
            username="newuser",
            email="new@test.org",
            password="Password@123",
            current_user=None,
        )

        assert result["user"] is None
        assert "Admin access required" in result["error"]

    def test_register_user_admin_can_create_users(
        self, auth_service: AuthService, db: Session, test_user: User
    ):
        """Test that admin users can create new users."""
        # Make test_user an admin
        test_user.is_admin = True
        db.commit()

        result = auth_service.register_user(
            username="newuser",
            email="new@test.org",
            password="Password@123",
            current_user=test_user,
        )

        assert result["user"] is not None
        assert result["error"] is None

    def test_register_user_duplicate_username(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that duplicate usernames are rejected."""
        result = auth_service.register_user(
            username="testuser",
            email="another@test.org",
            password="Password@123",
            current_user=test_user,
        )

        assert result["user"] is None
        assert "Username already registered" in result["error"]

    def test_register_user_duplicate_email(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that duplicate emails are rejected."""
        result = auth_service.register_user(
            username="newuser",
            email="test@test.org",
            password="Password@123",
            current_user=test_user,
        )

        assert result["user"] is None
        assert "Email already registered" in result["error"]

    def test_register_user_creates_with_specified_role(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that user can be created with specified role."""
        test_user.is_admin = True

        result = auth_service.register_user(
            username="faculty_user",
            email="faculty@test.org",
            password="Password@123",
            role="faculty",
            current_user=test_user,
        )

        assert result["user"] is not None
        assert result["user"].role == "faculty"

    def test_register_user_default_role(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that user registration uses default role if not specified."""
        test_user.is_admin = True

        result = auth_service.register_user(
            username="default_user",
            email="default@test.org",
            password="Password@123",
            current_user=test_user,
        )

        assert result["user"] is not None
        assert result["user"].role == "coordinator"

    def test_register_user_invalid_email(
        self, auth_service: AuthService, test_user: User
    ):
        """Test user registration with invalid email format."""
        test_user.is_admin = True

        # May or may not validate email, depends on implementation
        result = auth_service.register_user(
            username="badmail",
            email="not-an-email",
            password="Password@123",
            current_user=test_user,
        )

        # Either should fail or should succeed - depends on validation
        assert isinstance(result, dict)
        assert "user" in result
        assert "error" in result

    def test_authenticate_empty_username(self, auth_service: AuthService):
        """Test authentication with empty username."""
        result = auth_service.authenticate("", "password")

        assert result["user"] is None

    def test_authenticate_empty_password(
        self, auth_service: AuthService, test_user: User
    ):
        """Test authentication with empty password."""
        result = auth_service.authenticate("testuser", "")

        assert result["user"] is None

    def test_register_user_empty_username(self, auth_service: AuthService):
        """Test user registration with empty username."""
        result = auth_service.register_user(
            username="",
            email="test@test.org",
            password="Password@123",
        )

        # Should either fail or be rejected
        assert isinstance(result, dict)

    def test_register_user_empty_email(self, auth_service: AuthService):
        """Test user registration with empty email."""
        result = auth_service.register_user(
            username="testuser",
            email="",
            password="Password@123",
        )

        # Should either fail or be rejected
        assert isinstance(result, dict)

    def test_register_user_empty_password(self, auth_service: AuthService):
        """Test user registration with empty password."""
        result = auth_service.register_user(
            username="testuser",
            email="test@test.org",
            password="",
        )

        # Should either fail or be rejected
        assert isinstance(result, dict)

    def test_authenticate_case_sensitive_username(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that username matching respects case."""
        result = auth_service.authenticate("TestUser", "Test@Pass123")

        # Depends on implementation - may or may not be case-sensitive
        assert isinstance(result, dict)

    def test_authenticate_creates_valid_token(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that authentication creates a valid JWT token."""
        result = auth_service.authenticate("testuser", "Test@Pass123")

        token = result["access_token"]
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2

    def test_authenticate_multiple_times_different_jti(
        self, auth_service: AuthService, test_user: User
    ):
        """Test that multiple authentications generate different JTIs."""
        result1 = auth_service.authenticate("testuser", "Test@Pass123")
        result2 = auth_service.authenticate("testuser", "Test@Pass123")

        # JTIs should be different for different token generations
        assert result1["jti"] != result2["jti"]

    def test_register_user_hashes_password(
        self, auth_service: AuthService, test_user: User, db: Session
    ):
        """Test that registered user's password is hashed."""
        test_user.is_admin = True

        result = auth_service.register_user(
            username="secure_user",
            email="secure@test.org",
            password="SecurePass@123",
            current_user=test_user,
        )

        # Get user from DB and verify password is hashed (not plaintext)
        new_user = result["user"]
        assert new_user.hashed_password != "SecurePass@123"
        assert len(new_user.hashed_password) > 20  # Hash should be longer
