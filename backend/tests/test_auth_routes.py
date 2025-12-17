"""Comprehensive tests for authentication API routes.

Tests all auth endpoints with various scenarios including:
- Login/logout functionality
- Token validation
- Authentication failures
- Edge cases and error handling
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ALGORITHM, create_access_token, get_password_hash
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User

settings = get_settings()


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def inactive_user(db: Session) -> User:
    """Create an inactive user for testing."""
    user = User(
        id=uuid4(),
        username="inactive_user",
        email="inactive@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="coordinator",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db: Session) -> User:
    """Create a regular (non-admin) user for testing."""
    user = User(
        id=uuid4(),
        username="regularuser",
        email="regular@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user_headers(client: TestClient, regular_user: User) -> dict:
    """Get authentication headers for regular user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "regularuser", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def faculty_user(db: Session) -> User:
    """Create a faculty user for testing."""
    user = User(
        id=uuid4(),
        username="facultyuser",
        email="faculty@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# Login Endpoint Tests (OAuth2 Form)
# ============================================================================


class TestLoginEndpoint:
    """Tests for POST /api/auth/login endpoint (OAuth2 form)."""

    def test_login_success(self, client: TestClient, admin_user: User):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, admin_user: User):
        """Test login fails with incorrect password."""
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()
        assert "password" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails with non-existent username."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "testpass123"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """Test login fails for inactive user."""
        response = client.post(
            "/api/auth/login",
            data={"username": "inactive_user", "password": "testpass123"},
        )

        assert response.status_code == 401

    def test_login_missing_username(self, client: TestClient):
        """Test login fails when username is missing."""
        response = client.post(
            "/api/auth/login",
            data={"password": "testpass123"},
        )

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self, client: TestClient):
        """Test login fails when password is missing."""
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin"},
        )

        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self, client: TestClient):
        """Test login fails with empty credentials."""
        response = client.post(
            "/api/auth/login",
            data={"username": "", "password": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_login_updates_last_login(self, client: TestClient, admin_user: User, db: Session):
        """Test that successful login updates last_login timestamp."""
        # Record original last_login
        original_last_login = admin_user.last_login

        # Perform login
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "testpass123"},
        )

        assert response.status_code == 200

        # Refresh user from database
        db.refresh(admin_user)

        # Verify last_login was updated
        assert admin_user.last_login is not None
        if original_last_login:
            assert admin_user.last_login > original_last_login

    def test_login_token_is_valid_jwt(self, client: TestClient, admin_user: User):
        """Test that returned token is a valid JWT."""
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "testpass123"},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode token without verification to check structure
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": True}
        )

        assert "sub" in decoded  # User ID
        assert "username" in decoded
        assert "exp" in decoded  # Expiration
        assert "jti" in decoded  # JWT ID
        assert decoded["username"] == "testadmin"


# ============================================================================
# Login JSON Endpoint Tests
# ============================================================================


class TestLoginJsonEndpoint:
    """Tests for POST /api/auth/login/json endpoint."""

    def test_login_json_success(self, client: TestClient, admin_user: User):
        """Test successful login with JSON credentials."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_wrong_password(self, client: TestClient, admin_user: User):
        """Test JSON login fails with incorrect password."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_json_case_sensitive_username(self, client: TestClient, admin_user: User):
        """Test that username is case-sensitive."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "TestAdmin", "password": "testpass123"},
        )

        # Should fail because username is case-sensitive
        assert response.status_code == 401

    def test_login_json_with_extra_fields(self, client: TestClient, admin_user: User):
        """Test login with extra fields in JSON body."""
        response = client.post(
            "/api/auth/login/json",
            json={
                "username": "testadmin",
                "password": "testpass123",
                "extra_field": "should_be_ignored"
            },
        )

        # Should succeed, extra fields are ignored
        assert response.status_code == 200

    def test_login_json_invalid_json(self, client: TestClient):
        """Test login fails with invalid JSON."""
        response = client.post(
            "/api/auth/login/json",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_login_json_missing_fields(self, client: TestClient):
        """Test login fails when required fields are missing."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin"},
        )

        assert response.status_code == 422


# ============================================================================
# Logout Endpoint Tests
# ============================================================================


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, auth_headers: dict, db: Session):
        """Test successful logout blacklists the token."""
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

        # Verify token was added to blacklist
        token = auth_headers["Authorization"].replace("Bearer ", "")
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        jti = decoded.get("jti")

        # Check blacklist
        blacklisted = db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).first()
        assert blacklisted is not None
        assert blacklisted.reason == "logout"

    def test_logout_requires_authentication(self, client: TestClient):
        """Test logout requires valid authentication."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401

    def test_logout_with_invalid_token(self, client: TestClient):
        """Test logout with invalid token."""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_logout_token_unusable_after_logout(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that token cannot be used after logout."""
        # First, logout
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200

        # Try to use the same token
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 401

    def test_logout_without_bearer_prefix(self, client: TestClient):
        """Test logout fails without Bearer prefix in Authorization header."""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "some_token"}
        )

        assert response.status_code == 401

    def test_logout_inactive_user_token(
        self, client: TestClient, inactive_user: User, db: Session
    ):
        """Test logout with token from inactive user."""
        # Create token for inactive user
        token, jti, expires = create_access_token(
            data={"sub": str(inactive_user.id), "username": inactive_user.username}
        )

        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail because user is inactive
        assert response.status_code == 401


# ============================================================================
# Get Current User Endpoint Tests
# ============================================================================


class TestGetCurrentUserEndpoint:
    """Tests for GET /api/auth/me endpoint."""

    def test_get_me_success(self, client: TestClient, auth_headers: dict, admin_user: User):
        """Test getting current user information."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == admin_user.username
        assert data["email"] == admin_user.email
        assert data["role"] == admin_user.role
        assert data["is_active"] is True
        assert "id" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_me_requires_authentication(self, client: TestClient):
        """Test /me endpoint requires authentication."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, client: TestClient):
        """Test /me with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_get_me_with_expired_token(self, client: TestClient, admin_user: User, db: Session):
        """Test /me with expired token."""
        # Create an expired token
        expired_token, _, _ = create_access_token(
            data={"sub": str(admin_user.id), "username": admin_user.username},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_get_me_with_blacklisted_token(
        self, client: TestClient, auth_headers: dict
    ):
        """Test /me with blacklisted token."""
        # First logout to blacklist the token
        client.post("/api/auth/logout", headers=auth_headers)

        # Try to use the blacklisted token
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 401

    def test_get_me_different_roles(
        self, client: TestClient, faculty_user: User, db: Session
    ):
        """Test /me returns correct info for different user roles."""
        # Login as faculty user
        response = client.post(
            "/api/auth/login/json",
            json={"username": "facultyuser", "password": "testpass123"},
        )
        token = response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "faculty"
        assert data["username"] == "facultyuser"


# ============================================================================
# Register User Endpoint Tests
# ============================================================================


class TestRegisterUserEndpoint:
    """Tests for POST /api/auth/register endpoint."""

    def test_register_first_user_becomes_admin(self, client: TestClient, db: Session):
        """Test that first user automatically becomes admin."""
        # Clear all users
        db.query(User).delete()
        db.commit()

        response = client.post(
            "/api/auth/register",
            json={
                "username": "firstuser",
                "email": "first@test.org",
                "password": "password123",
                "role": "coordinator"  # Should be overridden to admin
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "firstuser"
        assert data["role"] == "admin"  # First user becomes admin
        assert data["is_active"] is True

    def test_register_subsequent_user_requires_admin(
        self, client: TestClient, admin_user: User, auth_headers: dict
    ):
        """Test that subsequent users require admin authentication."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "coordinator"  # Not admin

    def test_register_without_auth_when_users_exist(
        self, client: TestClient, admin_user: User
    ):
        """Test registration without auth fails when users exist."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.org",
                "password": "password123",
                "role": "coordinator"
            },
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_register_non_admin_cannot_create_users(
        self, client: TestClient, regular_user_headers: dict, admin_user: User
    ):
        """Test that non-admin users cannot create new users."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "anotheruser",
                "email": "another@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=regular_user_headers
        )

        assert response.status_code == 403

    def test_register_duplicate_username(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testadmin",  # Already exists
                "email": "different@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_duplicate_email(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": "testadmin@test.org",  # Already exists
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_invalid_email(
        self, client: TestClient, auth_headers: dict
    ):
        """Test registration fails with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_role(
        self, client: TestClient, auth_headers: dict
    ):
        """Test registration with invalid role."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.org",
                "password": "password123",
                "role": "invalid_role"
            },
            headers=auth_headers
        )

        # Should create user but may fail database constraint
        assert response.status_code in [400, 422]

    def test_register_missing_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test registration fails when required fields are missing."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                # Missing email and password
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_register_valid_roles(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test registration with various valid roles."""
        roles = ["coordinator", "faculty", "resident", "clinical_staff"]

        for i, role in enumerate(roles):
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"user_{role}_{i}",
                    "email": f"{role}{i}@test.org",
                    "password": "password123",
                    "role": role
                },
                headers=auth_headers
            )

            assert response.status_code == 201
            assert response.json()["role"] == role

    def test_register_password_is_hashed(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that password is properly hashed in database."""
        plain_password = "mysecretpassword"

        response = client.post(
            "/api/auth/register",
            json={
                "username": "hasheduser",
                "email": "hashed@test.org",
                "password": plain_password,
                "role": "coordinator"
            },
            headers=auth_headers
        )

        assert response.status_code == 201

        # Verify password is hashed in database
        user = db.query(User).filter(User.username == "hasheduser").first()
        assert user is not None
        assert user.hashed_password != plain_password
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash


# ============================================================================
# List Users Endpoint Tests
# ============================================================================


class TestListUsersEndpoint:
    """Tests for GET /api/auth/users endpoint."""

    def test_list_users_success(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test listing all users as admin."""
        response = client.get("/api/auth/users", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Should include admin user
        usernames = [u["username"] for u in data]
        assert "testadmin" in usernames

    def test_list_users_requires_authentication(self, client: TestClient):
        """Test listing users requires authentication."""
        response = client.get("/api/auth/users")

        assert response.status_code == 401

    def test_list_users_requires_admin(
        self, client: TestClient, regular_user_headers: dict, admin_user: User
    ):
        """Test listing users requires admin role."""
        response = client.get("/api/auth/users", headers=regular_user_headers)

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_list_users_response_structure(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test that user list response has correct structure."""
        response = client.get("/api/auth/users", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        if data:
            user = data[0]
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "role" in user
            assert "is_active" in user
            # Password should not be in response
            assert "password" not in user
            assert "hashed_password" not in user

    def test_list_users_ordered(
        self, client: TestClient, auth_headers: dict, admin_user: User, db: Session
    ):
        """Test that users are returned in a consistent order."""
        # Create additional users
        for i in range(3):
            user = User(
                id=uuid4(),
                username=f"user_{chr(97 + i)}",  # user_a, user_b, user_c
                email=f"user{i}@test.org",
                hashed_password=get_password_hash("pass"),
                role="coordinator",
            )
            db.add(user)
        db.commit()

        response = client.get("/api/auth/users", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        usernames = [u["username"] for u in data]

        # Should be ordered by username
        assert usernames == sorted(usernames)


# ============================================================================
# Token Security Tests
# ============================================================================


class TestTokenSecurity:
    """Tests for token security and validation."""

    def test_token_contains_jti(self, client: TestClient, admin_user: User):
        """Test that tokens contain a unique JTI."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        token = response.json()["access_token"]
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        assert "jti" in decoded
        assert isinstance(decoded["jti"], str)
        assert len(decoded["jti"]) > 0

    def test_token_jti_is_unique(self, client: TestClient, admin_user: User):
        """Test that each login generates a unique JTI."""
        # Login twice
        response1 = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )
        response2 = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        decoded1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=[ALGORITHM])
        decoded2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # JTIs should be different
        assert decoded1["jti"] != decoded2["jti"]

    def test_token_has_expiration(self, client: TestClient, admin_user: User):
        """Test that tokens have an expiration time."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        token = response.json()["access_token"]
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        assert "exp" in decoded
        assert "iat" in decoded  # Issued at

        # Expiration should be in the future
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        iat_time = datetime.utcfromtimestamp(decoded["iat"])
        assert exp_time > iat_time

    def test_tampered_token_rejected(self, client: TestClient, admin_user: User):
        """Test that tampered tokens are rejected."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        token = response.json()["access_token"]

        # Tamper with token by changing a character
        tampered_token = token[:-5] + "XXXXX"

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401

    def test_token_with_wrong_secret_rejected(
        self, client: TestClient, admin_user: User
    ):
        """Test that tokens signed with wrong secret are rejected."""
        # Create token with wrong secret
        fake_token = jwt.encode(
            {
                "sub": str(admin_user.id),
                "username": admin_user.username,
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            "wrong_secret_key",
            algorithm=ALGORITHM
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {fake_token}"}
        )

        assert response.status_code == 401


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestAuthEdgeCases:
    """Tests for edge cases and error handling."""

    def test_login_with_special_characters_in_password(
        self, client: TestClient, db: Session
    ):
        """Test login with special characters in password."""
        special_password = "p@$$w0rd!#%&*()[]{}|;:',.<>?/~`"

        # Create user with special password
        user = User(
            id=uuid4(),
            username="specialuser",
            email="special@test.org",
            hashed_password=get_password_hash(special_password),
            role="coordinator",
        )
        db.add(user)
        db.commit()

        # Login should work
        response = client.post(
            "/api/auth/login/json",
            json={"username": "specialuser", "password": special_password},
        )

        assert response.status_code == 200

    def test_login_with_unicode_characters(
        self, client: TestClient, db: Session
    ):
        """Test login with unicode characters in username."""
        # Create user with unicode username
        user = User(
            id=uuid4(),
            username="user_中文_🚀",
            email="unicode@test.org",
            hashed_password=get_password_hash("testpass"),
            role="coordinator",
        )
        db.add(user)
        db.commit()

        # Login should work
        response = client.post(
            "/api/auth/login/json",
            json={"username": "user_中文_🚀", "password": "testpass"},
        )

        assert response.status_code == 200

    def test_register_with_very_long_username(
        self, client: TestClient, auth_headers: dict
    ):
        """Test registration with very long username."""
        long_username = "a" * 150  # Longer than 100 char limit

        response = client.post(
            "/api/auth/register",
            json={
                "username": long_username,
                "email": "longuser@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        # Should fail validation or database constraint
        assert response.status_code in [400, 422]

    def test_concurrent_registrations_same_username(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that concurrent registrations with same username are handled."""
        # First registration
        response1 = client.post(
            "/api/auth/register",
            json={
                "username": "concurrent",
                "email": "concurrent1@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        # Second registration with same username
        response2 = client.post(
            "/api/auth/register",
            json={
                "username": "concurrent",
                "email": "concurrent2@test.org",
                "password": "password123",
                "role": "coordinator"
            },
            headers=auth_headers
        )

        # One should succeed, one should fail
        statuses = {response1.status_code, response2.status_code}
        assert 201 in statuses
        assert 400 in statuses

    def test_logout_multiple_times(self, client: TestClient, auth_headers: dict):
        """Test logging out multiple times with same token."""
        # First logout
        response1 = client.post("/api/auth/logout", headers=auth_headers)
        assert response1.status_code == 200

        # Second logout with same token should fail
        response2 = client.post("/api/auth/logout", headers=auth_headers)
        assert response2.status_code == 401

    def test_get_me_with_deleted_user_token(
        self, client: TestClient, regular_user: User, db: Session
    ):
        """Test using token after user is deleted."""
        # Login to get token
        response = client.post(
            "/api/auth/login/json",
            json={"username": "regularuser", "password": "testpass123"},
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Delete user
        db.delete(regular_user)
        db.commit()

        # Try to use token
        response = client.get("/api/auth/me", headers=headers)

        # Should fail because user no longer exists
        assert response.status_code == 401

    def test_empty_authorization_header(self, client: TestClient):
        """Test request with empty Authorization header."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": ""}
        )

        assert response.status_code == 401

    def test_malformed_authorization_header(self, client: TestClient):
        """Test request with malformed Authorization header."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "NotBearer token123"}
        )

        assert response.status_code == 401
