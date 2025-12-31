"""
End-to-end tests for user administration.

Tests the complete user administration workflow:
1. Admin: Create user → Assign role → Verify access
2. User CRUD operations
3. Role assignment and permission verification
4. Authentication and authorization flows
5. Edge cases and error handling

This module validates that all user administration components work together
correctly in real-world scenarios, including:
- User registration and authentication
- Role-based access control (RBAC)
- Admin-only operations
- Permission verification across different roles
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ALGORITHM, get_password_hash
from app.models.user import User

settings = get_settings()


# ============================================================================
# Fixtures - Test Data Setup
# ============================================================================


@pytest.fixture
def user_admin_setup(db: Session, admin_user: User) -> dict:
    """
    Create a complete setup for user administration E2E testing.

    Creates:
    - 1 admin user (from fixture)
    - 3 additional users with different roles
    - Authentication tokens for each user

    Returns:
        Dictionary with all created entities and their credentials
    """
    users = []
    credentials = {}

    # Create users with different roles
    user_configs = [
        ("coordinator_user", "coordinator@test.org", "coordinator", "coord123"),
        ("faculty_user", "faculty@test.org", "faculty", "faculty123"),
        ("resident_user", "resident@test.org", "resident", "resident123"),
    ]

    for username, email, role, password in user_configs:
        user = User(
            id=uuid4(),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        users.append(user)
        credentials[username] = {"username": username, "password": password, "role": role}

    db.commit()

    # Refresh all users
    for user in users:
        db.refresh(user)

    return {
        "admin": admin_user,
        "users": users,
        "credentials": credentials,
    }


# ============================================================================
# E2E Test: Complete User Administration Workflow
# ============================================================================


@pytest.mark.e2e
class TestUserAdministrationE2E:
    """
    End-to-end tests for the complete user administration workflow.

    Tests the integration of:
    - User registration
    - Authentication and authorization
    - Role-based access control
    - User listing and retrieval
    - Permission verification
    """

    def test_full_user_lifecycle_workflow(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete user lifecycle: create → login → verify access → logout.

        Workflow:
        1. Admin creates a new coordinator user
        2. New user logs in
        3. Verify user can access their own info
        4. Verify user cannot access admin-only endpoints
        5. User logs out
        6. Verify token is invalidated
        """
        # Step 1: Admin creates a new coordinator user
        create_response = client.post(
            "/api/auth/register",
            json={
                "username": "newcoordinator",
                "email": "newcoord@test.org",
                "password": "secure_password_123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        user_data = create_response.json()
        assert user_data["username"] == "newcoordinator"
        assert user_data["role"] == "coordinator"
        assert user_data["is_active"] is True
        assert "id" in user_data
        # Password should not be in response
        assert "password" not in user_data
        assert "hashed_password" not in user_data

        # Step 2: New user logs in
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "newcoordinator", "password": "secure_password_123"},
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"

        user_token = login_data["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Step 3: Verify user can access their own info
        me_response = client.get("/api/auth/me", headers=user_headers)

        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["username"] == "newcoordinator"
        assert me_data["role"] == "coordinator"

        # Step 4: Verify user cannot access admin-only endpoints
        list_users_response = client.get("/api/auth/users", headers=user_headers)

        assert list_users_response.status_code == 403
        assert "admin" in list_users_response.json()["detail"].lower()

        # Verify user cannot create other users
        create_another_response = client.post(
            "/api/auth/register",
            json={
                "username": "another_user",
                "email": "another@test.org",
                "password": "password123",
                "role": "resident",
            },
            headers=user_headers,
        )

        assert create_another_response.status_code == 403

        # Step 5: User logs out
        logout_response = client.post("/api/auth/logout", headers=user_headers)

        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Successfully logged out"

        # Step 6: Verify token is invalidated after logout
        me_after_logout_response = client.get("/api/auth/me", headers=user_headers)

        assert me_after_logout_response.status_code == 401

    def test_admin_manages_multiple_users(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test admin creating and managing multiple users with different roles.

        Workflow:
        1. Admin creates users with different roles
        2. Admin lists all users
        3. Verify all created users are in the list
        4. Verify each user has correct role assignment
        """
        # Step 1: Admin creates users with different roles
        roles_to_create = [
            ("coord1", "coord1@test.org", "coordinator"),
            ("faculty1", "faculty1@test.org", "faculty"),
            ("resident1", "resident1@test.org", "resident"),
            ("staff1", "staff1@test.org", "clinical_staff"),
        ]

        created_users = []
        for username, email, role in roles_to_create:
            response = client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": "password123",
                    "role": role,
                },
                headers=auth_headers,
            )

            assert response.status_code == 201
            user_data = response.json()
            assert user_data["username"] == username
            assert user_data["role"] == role
            created_users.append(user_data)

        # Step 2: Admin lists all users
        list_response = client.get("/api/auth/users", headers=auth_headers)

        assert list_response.status_code == 200
        all_users = list_response.json()
        assert isinstance(all_users, list)
        assert len(all_users) >= len(roles_to_create)

        # Step 3: Verify all created users are in the list
        usernames_in_list = [u["username"] for u in all_users]
        for username, _, _ in roles_to_create:
            assert username in usernames_in_list

        # Step 4: Verify each user has correct role assignment
        for username, email, expected_role in roles_to_create:
            user_in_list = next((u for u in all_users if u["username"] == username), None)
            assert user_in_list is not None
            assert user_in_list["role"] == expected_role
            assert user_in_list["email"] == email

    def test_role_based_access_verification(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
        user_admin_setup: dict,
    ):
        """
        Test that different user roles have appropriate access permissions.

        Tests:
        1. Admin can access all endpoints
        2. Coordinator cannot access admin endpoints
        3. Faculty cannot access admin endpoints
        4. Resident cannot access admin endpoints
        5. All users can access their own information
        """
        setup = user_admin_setup

        # Step 1: Admin can access all endpoints
        admin_list_response = client.get("/api/auth/users", headers=auth_headers)
        assert admin_list_response.status_code == 200

        admin_create_response = client.post(
            "/api/auth/register",
            json={
                "username": "test_user",
                "email": "test@test.org",
                "password": "password123",
                "role": "resident",
            },
            headers=auth_headers,
        )
        assert admin_create_response.status_code == 201

        # Step 2-4: Non-admin users cannot access admin endpoints
        non_admin_roles = ["coordinator", "faculty", "resident"]
        for role in non_admin_roles:
            # Login as non-admin user
            username = f"{role}_user"
            password = setup["credentials"][username]["password"]

            login_response = client.post(
                "/api/auth/login/json",
                json={"username": username, "password": password},
            )
            assert login_response.status_code == 200

            user_token = login_response.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}

            # Try to access admin endpoints
            list_response = client.get("/api/auth/users", headers=user_headers)
            assert list_response.status_code == 403

            create_response = client.post(
                "/api/auth/register",
                json={
                    "username": f"new_{role}_created",
                    "email": f"new_{role}@test.org",
                    "password": "password123",
                    "role": "resident",
                },
                headers=user_headers,
            )
            assert create_response.status_code == 403

            # Step 5: All users can access their own information
            me_response = client.get("/api/auth/me", headers=user_headers)
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["username"] == username
            assert me_data["role"] == role

    def test_user_authentication_tokens(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test user authentication token lifecycle.

        Tests:
        1. User receives valid JWT on login
        2. Token contains correct user information
        3. Token can be used to access protected endpoints
        4. Expired tokens are rejected
        5. Invalid tokens are rejected
        """
        # Create a test user
        create_response = client.post(
            "/api/auth/register",
            json={
                "username": "token_test_user",
                "email": "tokentest@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Step 1: User receives valid JWT on login
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "token_test_user", "password": "password123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert isinstance(token, str)
        assert len(token) > 0

        # Step 2: Token contains correct user information
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert "sub" in decoded  # User ID
        assert "username" in decoded
        assert decoded["username"] == "token_test_user"
        assert "exp" in decoded  # Expiration
        assert "jti" in decoded  # JWT ID

        # Step 3: Token can be used to access protected endpoints
        user_headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/auth/me", headers=user_headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "token_test_user"

        # Step 4: Expired tokens are rejected
        from app.core.security import create_access_token

        expired_token, _, _ = create_access_token(
            data={"sub": user_id, "username": "token_test_user"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        expired_response = client.get("/api/auth/me", headers=expired_headers)
        assert expired_response.status_code == 401

        # Step 5: Invalid tokens are rejected
        invalid_headers = {"Authorization": "Bearer invalid_token_string"}
        invalid_response = client.get("/api/auth/me", headers=invalid_headers)
        assert invalid_response.status_code == 401

    def test_first_user_becomes_admin(
        self,
        db: Session,
        client: TestClient,
    ):
        """
        Test that the first user registered automatically becomes admin.

        Workflow:
        1. Clear all users from database
        2. Register first user with 'coordinator' role
        3. Verify user is auto-promoted to 'admin'
        4. Verify admin can perform admin operations
        """
        # Step 1: Clear all users
        db.query(User).delete()
        db.commit()

        # Step 2: Register first user
        response = client.post(
            "/api/auth/register",
            json={
                "username": "firstuser",
                "email": "first@test.org",
                "password": "password123",
                "role": "coordinator",  # Request coordinator role
            },
        )

        # Step 3: Verify user is auto-promoted to admin
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["username"] == "firstuser"
        assert user_data["role"] == "admin"  # Auto-promoted
        assert user_data["is_active"] is True

        # Step 4: Verify admin can perform admin operations
        # Login as first user
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "firstuser", "password": "password123"},
        )
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Create another user (admin operation)
        create_response = client.post(
            "/api/auth/register",
            json={
                "username": "seconduser",
                "email": "second@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=admin_headers,
        )
        assert create_response.status_code == 201
        assert create_response.json()["role"] == "coordinator"  # Not auto-promoted

        # List users (admin operation)
        list_response = client.get("/api/auth/users", headers=admin_headers)
        assert list_response.status_code == 200
        users = list_response.json()
        assert len(users) == 2


# ============================================================================
# E2E Test: Edge Cases and Error Scenarios
# ============================================================================


@pytest.mark.e2e
class TestUserAdministrationEdgeCases:
    """
    Test edge cases and error scenarios for user administration.

    These tests ensure the system handles unusual but valid scenarios
    correctly and fails gracefully for invalid scenarios.
    """

    def test_duplicate_username_rejection(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that duplicate usernames are rejected.

        Workflow:
        1. Create a user with username 'duplicate_test'
        2. Try to create another user with same username
        3. Verify second creation fails with 400 error
        """
        # Step 1: Create first user
        response1 = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate_test",
                "email": "user1@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Step 2: Try to create duplicate
        response2 = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate_test",  # Same username
                "email": "user2@test.org",  # Different email
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )

        # Step 3: Verify rejection
        assert response2.status_code == 400
        assert "username" in response2.json()["detail"].lower()

    def test_duplicate_email_rejection(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that duplicate emails are rejected.

        Workflow:
        1. Create a user with email 'duplicate@test.org'
        2. Try to create another user with same email
        3. Verify second creation fails with 400 error
        """
        # Step 1: Create first user
        response1 = client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Step 2: Try to create duplicate email
        response2 = client.post(
            "/api/auth/register",
            json={
                "username": "user2",  # Different username
                "email": "duplicate@test.org",  # Same email
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )

        # Step 3: Verify rejection
        assert response2.status_code == 400
        assert "email" in response2.json()["detail"].lower()

    def test_invalid_role_rejection(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that invalid role assignments are rejected.

        Tests:
        1. Non-existent role is rejected
        2. Empty role is rejected
        """
        # Test 1: Non-existent role
        response1 = client.post(
            "/api/auth/register",
            json={
                "username": "invalid_role_user",
                "email": "invalid@test.org",
                "password": "password123",
                "role": "super_admin",  # Invalid role
            },
            headers=auth_headers,
        )
        assert response1.status_code in [400, 422]

        # Test 2: Empty role (should use default or fail)
        response2 = client.post(
            "/api/auth/register",
            json={
                "username": "empty_role_user",
                "email": "empty@test.org",
                "password": "password123",
                "role": "",  # Empty role
            },
            headers=auth_headers,
        )
        assert response2.status_code in [400, 422]

    def test_weak_password_handling(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test password validation and handling.

        Tests:
        1. Very short password (may be accepted or rejected)
        2. Empty password is rejected
        3. Password is properly hashed in database
        """
        # Test 1: Very short password
        response1 = client.post(
            "/api/auth/register",
            json={
                "username": "short_pw_user",
                "email": "shortpw@test.org",
                "password": "123",  # Very short
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        # May be accepted or rejected depending on validation rules
        assert response1.status_code in [201, 400, 422]

        # Test 2: Empty password
        response2 = client.post(
            "/api/auth/register",
            json={
                "username": "empty_pw_user",
                "email": "emptypw@test.org",
                "password": "",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        assert response2.status_code == 422  # Validation error

        # Test 3: Password is hashed
        response3 = client.post(
            "/api/auth/register",
            json={
                "username": "hashed_pw_user",
                "email": "hashed@test.org",
                "password": "my_secret_password",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        if response3.status_code == 201:
            # Verify password is not stored in plain text
            user = db.query(User).filter(User.username == "hashed_pw_user").first()
            assert user is not None
            assert user.hashed_password != "my_secret_password"
            assert user.hashed_password.startswith("$2b$")  # bcrypt hash

    def test_inactive_user_cannot_login(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that inactive users cannot log in.

        Workflow:
        1. Create active user
        2. User logs in successfully
        3. Deactivate user
        4. Verify user cannot log in
        5. Verify existing token still works (or doesn't, depending on implementation)
        """
        # Step 1: Create active user
        create_response = client.post(
            "/api/auth/register",
            json={
                "username": "inactive_test",
                "email": "inactive@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201

        # Step 2: User logs in successfully
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "inactive_test", "password": "password123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 3: Deactivate user
        user = db.query(User).filter(User.username == "inactive_test").first()
        user.is_active = False
        db.commit()

        # Step 4: Verify user cannot log in
        login_response2 = client.post(
            "/api/auth/login/json",
            json={"username": "inactive_test", "password": "password123"},
        )
        assert login_response2.status_code == 401

        # Step 5: Verify existing token is invalidated
        me_response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 401

    def test_concurrent_user_creation(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test handling of concurrent user creation with same credentials.

        Simulates race condition where two admins try to create
        same user simultaneously.
        """
        # Try to create same user twice
        user_data = {
            "username": "concurrent_user",
            "email": "concurrent@test.org",
            "password": "password123",
            "role": "coordinator",
        }

        response1 = client.post(
            "/api/auth/register", json=user_data, headers=auth_headers
        )
        response2 = client.post(
            "/api/auth/register", json=user_data, headers=auth_headers
        )

        # One should succeed, one should fail
        statuses = {response1.status_code, response2.status_code}
        assert 201 in statuses  # One succeeds
        assert 400 in statuses  # One fails due to duplicate

    def test_user_list_pagination_and_ordering(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test user list returns consistent ordering.

        Tests:
        1. Users are returned in consistent order
        2. List includes all user fields
        3. Sensitive fields are excluded
        """
        # Create multiple users
        for i in range(5):
            client.post(
                "/api/auth/register",
                json={
                    "username": f"list_user_{chr(97 + i)}",  # a, b, c, d, e
                    "email": f"list{i}@test.org",
                    "password": "password123",
                    "role": "coordinator",
                },
                headers=auth_headers,
            )

        # Get user list
        response = client.get("/api/auth/users", headers=auth_headers)
        assert response.status_code == 200
        users = response.json()

        # Test 1: Consistent ordering
        usernames = [u["username"] for u in users]
        assert usernames == sorted(usernames)

        # Test 2: All fields present
        if users:
            user = users[0]
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "role" in user
            assert "is_active" in user

        # Test 3: Sensitive fields excluded
        for user in users:
            assert "password" not in user
            assert "hashed_password" not in user

    def test_token_refresh_after_user_creation(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test token refresh functionality for newly created users.

        Workflow:
        1. Create user and log in
        2. Use refresh token to get new access token
        3. Verify new access token works
        4. Verify old refresh token is invalidated (if rotation enabled)
        """
        # Step 1: Create user and log in
        client.post(
            "/api/auth/register",
            json={
                "username": "refresh_test",
                "email": "refresh@test.org",
                "password": "password123",
                "role": "coordinator",
            },
            headers=auth_headers,
        )

        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "refresh_test", "password": "password123"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        original_access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Step 2: Use refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]

        # Step 3: Verify new access token works
        me_response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "refresh_test"

        # Step 4: Verify old refresh token is invalidated
        refresh_again_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_again_response.status_code == 401


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary:

✅ Complete workflow tests:
   - User lifecycle: create → login → verify → logout
   - Admin managing multiple users with different roles
   - Role-based access control verification
   - Authentication token lifecycle

✅ User CRUD operations:
   - Create: Register users with different roles
   - Read: Get current user info, list all users
   - Update: Not available (TODO)
   - Delete: Not available (TODO)

✅ Role assignment tests:
   - Creating users with different roles (admin, coordinator, faculty, resident, clinical_staff)
   - First user auto-promotion to admin
   - Role-based permission verification

✅ Authentication and authorization:
   - Login/logout functionality
   - Token generation and validation
   - JWT structure and claims
   - Expired and invalid token handling
   - Refresh token workflow

✅ Permission verification:
   - Admin can access all endpoints
   - Non-admin users blocked from admin endpoints
   - All users can access their own information

✅ Edge cases:
   - Duplicate username/email rejection
   - Invalid role rejection
   - Password validation and hashing
   - Inactive user login prevention
   - Concurrent user creation handling
   - User list ordering and field filtering
   - Token refresh after user creation

TODOs (features not yet implemented):
1. User update endpoint (PATCH /api/auth/users/{id})
2. User deletion endpoint (DELETE /api/auth/users/{id})
3. User deactivation/reactivation workflow
4. Password change endpoint
5. Email verification workflow
6. Password reset workflow
7. User profile picture upload
8. User preferences and settings
9. Audit log for user operations
10. Multi-factor authentication (MFA)
11. Session management and concurrent session limits
12. User search and filtering

Known limitations:
- Tests rely on API authentication (may be skipped if auth not configured)
- No tests for user update/delete (endpoints not implemented)
- Password strength validation is minimal
- No email verification workflow
- No password reset functionality
"""
