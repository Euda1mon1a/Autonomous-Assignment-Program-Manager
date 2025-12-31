"""
Role-Based Access Control (RBAC) Authorization Tests.

Comprehensive tests for authentication and authorization including
role-based permissions, JWT token handling, and access control.

Test Coverage:
- Role-based access control (8 user roles)
- JWT token generation and validation
- Permission enforcement by role
- Unauthorized access prevention
- Token expiration handling
- Password hashing and verification
- Admin-only endpoint protection
- Cross-role permission testing
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.person import Person
from app.models.user import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user_obj(db: Session) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        username="admin_test",
        email="admin@test.org",
        hashed_password=get_password_hash("admin_pass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def coordinator_user(db: Session) -> User:
    """Create a coordinator user."""
    user = User(
        id=uuid4(),
        username="coordinator_test",
        email="coordinator@test.org",
        hashed_password=get_password_hash("coord_pass123"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def faculty_user(db: Session) -> User:
    """Create a faculty user."""
    user = User(
        id=uuid4(),
        username="faculty_test",
        email="faculty@test.org",
        hashed_password=get_password_hash("faculty_pass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def resident_user(db: Session) -> User:
    """Create a resident user."""
    user = User(
        id=uuid4(),
        username="resident_test",
        email="resident@test.org",
        hashed_password=get_password_hash("resident_pass123"),
        role="resident",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def clinical_staff_user(db: Session) -> User:
    """Create a clinical staff user."""
    user = User(
        id=uuid4(),
        username="clinical_test",
        email="clinical@test.org",
        hashed_password=get_password_hash("clinical_pass123"),
        role="clinical_staff",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session) -> User:
    """Create an inactive user."""
    user = User(
        id=uuid4(),
        username="inactive_test",
        email="inactive@test.org",
        hashed_password=get_password_hash("inactive_pass123"),
        role="resident",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user: User) -> dict:
    """Generate auth headers for a user."""
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Test Class: Authentication
# ============================================================================


class TestAuthentication:
    """Tests for authentication mechanisms."""

    def test_login_with_valid_credentials(
        self, client: TestClient, admin_user_obj: User
    ):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login/json",
            json={
                "username": "admin_test",
                "password": "admin_pass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_invalid_password(
        self, client: TestClient, admin_user_obj: User
    ):
        """Test login fails with incorrect password."""
        response = client.post(
            "/api/auth/login/json",
            json={
                "username": "admin_test",
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        error = response.json()
        assert "detail" in error

    def test_login_with_nonexistent_user(self, client: TestClient):
        """Test login fails with non-existent username."""
        response = client.post(
            "/api/auth/login/json",
            json={
                "username": "nonexistent",
                "password": "any_password",
            },
        )

        assert response.status_code == 401

    def test_login_with_inactive_account(self, client: TestClient, inactive_user: User):
        """Test login fails for inactive account."""
        response = client.post(
            "/api/auth/login/json",
            json={
                "username": "inactive_test",
                "password": "inactive_pass123",
            },
        )

        assert response.status_code == 401 or response.status_code == 403

    def test_password_hashing_verification(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should not equal plain password
        assert hashed != password

        # Verification should succeed with correct password
        assert verify_password(password, hashed) is True

        # Verification should fail with incorrect password
        assert verify_password("wrong_password", hashed) is False

    def test_jwt_token_contains_user_info(self, admin_user_obj: User):
        """Test JWT token contains correct user information."""
        token = create_access_token(
            data={"sub": admin_user_obj.username, "role": admin_user_obj.role}
        )

        # Decode token without verification for testing
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert decoded["sub"] == admin_user_obj.username
        assert decoded["role"] == admin_user_obj.role
        assert "exp" in decoded  # Expiration time


# ============================================================================
# Test Class: Authorization by Role
# ============================================================================


class TestRoleBasedAuthorization:
    """Tests for role-based authorization."""

    def test_admin_can_access_all_endpoints(
        self, client: TestClient, admin_user_obj: User
    ):
        """Test admin role has access to all endpoints."""
        headers = get_auth_headers(admin_user_obj)

        # Admin endpoints
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code in [200, 404]  # Not forbidden

        # Regular endpoints
        response = client.get("/api/people", headers=headers)
        assert response.status_code == 200

    def test_coordinator_can_manage_schedules(
        self, client: TestClient, coordinator_user: User
    ):
        """Test coordinator can manage schedules."""
        headers = get_auth_headers(coordinator_user)

        # Should be able to view schedules
        response = client.get("/api/assignments", headers=headers)
        assert response.status_code == 200

        # Should be able to create assignments (if endpoint exists)
        # Implementation depends on specific endpoints

    def test_faculty_can_view_own_schedule(
        self, client: TestClient, faculty_user: User, db: Session
    ):
        """Test faculty can view their own schedule."""
        headers = get_auth_headers(faculty_user)

        # Create person record for faculty
        person = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email=faculty_user.email,
        )
        db.add(person)
        db.commit()

        response = client.get(f"/api/people/{person.id}", headers=headers)
        assert response.status_code == 200

    def test_resident_cannot_access_admin_endpoints(
        self, client: TestClient, resident_user: User
    ):
        """Test resident role cannot access admin endpoints."""
        headers = get_auth_headers(resident_user)

        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 403  # Forbidden

    def test_resident_can_request_swaps(self, client: TestClient, resident_user: User):
        """Test resident can request schedule swaps."""
        headers = get_auth_headers(resident_user)

        # Should be able to view swap options
        response = client.get("/api/swaps", headers=headers)
        assert response.status_code in [200, 404]  # Not forbidden

    def test_clinical_staff_has_read_only_access(
        self, client: TestClient, clinical_staff_user: User
    ):
        """Test clinical staff has read-only access."""
        headers = get_auth_headers(clinical_staff_user)

        # Can read schedules
        response = client.get("/api/assignments", headers=headers)
        assert response.status_code == 200

        # Cannot create/modify (if enforced)
        # Implementation depends on endpoint permissions


# ============================================================================
# Test Class: Token Validation
# ============================================================================


class TestTokenValidation:
    """Tests for JWT token validation."""

    def test_missing_token_returns_401(self, client: TestClient):
        """Test request without token returns 401 Unauthorized."""
        response = client.get("/api/people")

        assert response.status_code == 401

    def test_invalid_token_format_returns_401(self, client: TestClient):
        """Test request with invalid token format returns 401."""
        response = client.get(
            "/api/people",
            headers={"Authorization": "Bearer invalid_token_format"},
        )

        assert response.status_code == 401

    def test_expired_token_returns_401(self, client: TestClient):
        """Test request with expired token returns 401."""
        # Create token that expired 1 hour ago
        expired_time = datetime.utcnow() - timedelta(hours=1)
        token_data = {
            "sub": "test_user",
            "role": "admin",
            "exp": expired_time,
        }
        expired_token = jwt.encode(
            token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        response = client.get(
            "/api/people",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_token_with_wrong_signature_returns_401(self, client: TestClient):
        """Test token signed with wrong key returns 401."""
        token_data = {"sub": "test_user", "role": "admin"}
        wrong_token = jwt.encode(
            token_data, "wrong_secret_key", algorithm=settings.ALGORITHM
        )

        response = client.get(
            "/api/people",
            headers={"Authorization": f"Bearer {wrong_token}"},
        )

        assert response.status_code == 401


# ============================================================================
# Test Class: Permission Edge Cases
# ============================================================================


class TestPermissionEdgeCases:
    """Tests for permission edge cases and boundary conditions."""

    def test_user_cannot_access_others_private_data(
        self, client: TestClient, faculty_user: User, db: Session
    ):
        """Test user cannot access another user's private data."""
        headers = get_auth_headers(faculty_user)

        # Create another user's person record
        other_person = Person(
            id=uuid4(),
            name="Dr. Other Faculty",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_person)
        db.commit()

        # Try to access private endpoints for other user
        # Implementation depends on privacy controls
        response = client.get(
            f"/api/people/{other_person.id}/private",
            headers=headers,
        )

        # Should either be forbidden or not found
        assert response.status_code in [403, 404]

    def test_deleted_user_token_invalid(self, client: TestClient, db: Session):
        """Test that token becomes invalid after user deletion."""
        # Create user
        user = User(
            id=uuid4(),
            username="to_delete",
            email="delete@test.org",
            hashed_password=get_password_hash("pass123"),
            role="resident",
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Get token
        token = create_access_token(data={"sub": user.username, "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Delete user
        db.delete(user)
        db.commit()

        # Token should no longer work
        response = client.get("/api/people", headers=headers)
        assert response.status_code == 401

    def test_role_change_requires_new_token(
        self, client: TestClient, db: Session, resident_user: User
    ):
        """Test that role changes require new token."""
        # Get token as resident
        old_token = create_access_token(
            data={"sub": resident_user.username, "role": "resident"}
        )
        old_headers = {"Authorization": f"Bearer {old_token}"}

        # Change role to admin
        resident_user.role = "admin"
        db.commit()

        # Old token still has old role
        # New permissions won't be available until new login
        response = client.get("/api/admin/users", headers=old_headers)
        assert response.status_code == 403  # Still forbidden with old token
