"""
Security tests for profiling endpoints.

Tests that all profiling endpoints require admin authentication and properly
reject unauthenticated or non-admin users.

CRITICAL: Profiling data contains sensitive information including SQL queries,
request patterns, and system internals. These endpoints MUST be admin-only.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def regular_user_token(db):
    """Create a regular (non-admin) user and return their token."""
    from app.core.security import create_access_token, get_password_hash

    user = User(
        username="regular_user",
        email="regular@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="RESIDENT",  # Non-admin role
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token, _, _ = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    return token


@pytest.fixture
def admin_user_token(db):
    """Create an admin user and return their token."""
    from app.core.security import create_access_token, get_password_hash

    user = User(
        username="admin_user",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role="ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token, _, _ = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    return token


class TestProfilingEndpointSecurity:
    """Test suite for profiling endpoint authentication and authorization."""

    # All profiling endpoints that must be admin-only
    PROFILING_ENDPOINTS = [
        ("GET", "/profiling/status"),
        ("POST", "/profiling/start"),
        ("POST", "/profiling/stop"),
        ("GET", "/profiling/report"),
        ("GET", "/profiling/queries"),
        ("GET", "/profiling/requests"),
        ("GET", "/profiling/traces"),
        ("GET", "/profiling/bottlenecks"),
        ("GET", "/profiling/flamegraph"),
        ("POST", "/profiling/analyze"),
        ("DELETE", "/profiling/clear"),
    ]

    @pytest.mark.parametrize("method,endpoint", PROFILING_ENDPOINTS)
    def test_profiling_endpoints_require_authentication(self, client, method, endpoint):
        """
        SECURITY: Test that profiling endpoints reject unauthenticated requests.

        All profiling endpoints MUST return 401 Unauthorized when called without
        a valid JWT token.
        """
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"SECURITY VIOLATION: {endpoint} allowed unauthenticated access! "
            f"Profiling data contains sensitive system internals."
        )

    @pytest.mark.parametrize("method,endpoint", PROFILING_ENDPOINTS)
    def test_profiling_endpoints_require_admin_role(
        self, client, regular_user_token, method, endpoint
    ):
        """
        SECURITY: Test that profiling endpoints reject non-admin users.

        All profiling endpoints MUST return 403 Forbidden when called by
        authenticated users who are not admins.
        """
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, json={}, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"SECURITY VIOLATION: {endpoint} allowed non-admin access! "
            f"Profiling data should only be accessible to admins."
        )

    @pytest.mark.parametrize("method,endpoint", PROFILING_ENDPOINTS)
    def test_profiling_endpoints_allow_admin_access(
        self, client, admin_user_token, method, endpoint
    ):
        """
        Test that profiling endpoints allow admin users.

        Admin users should be able to access profiling endpoints successfully
        (may return 200, 404, or other valid responses, but NOT 401 or 403).
        """
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            # Some endpoints need specific payloads
            if endpoint == "/profiling/start":
                payload = {"cpu": True, "memory": True}
            elif endpoint == "/profiling/analyze":
                payload = {"cpu_threshold_percent": 80.0}
            else:
                payload = {}
            response = client.post(endpoint, json=payload, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            pytest.fail(f"Unsupported method: {method}")

        # Admin should NOT get authentication/authorization errors
        assert response.status_code not in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ], (
            f"Admin user was denied access to {endpoint}. "
            f"Expected admin to have access to profiling endpoints."
        )

    def test_profiling_data_not_leaked_in_error_messages(self, client):
        """
        SECURITY: Test that profiling data is not leaked in error responses.

        Unauthenticated requests should receive generic error messages that
        don't reveal information about the profiling system.
        """
        response = client.get("/profiling/status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Error message should be generic
        detail = response.json().get("detail", "")
        assert "profiling" not in detail.lower(), (
            "Error message leaks information about profiling system"
        )
        assert "sql" not in detail.lower(), "Error message leaks SQL information"
        assert "query" not in detail.lower(), "Error message leaks query information"


class TestProfilingRateLimiting:
    """Test rate limiting on profiling endpoints (if implemented)."""

    @pytest.mark.skip(
        reason="Rate limiting for profiling endpoints not yet implemented"
    )
    def test_profiling_endpoints_have_rate_limits(self, client, admin_user_token):
        """
        RECOMMENDED: Profiling endpoints should have rate limiting.

        Even for admin users, profiling operations can be resource-intensive.
        Consider adding rate limits to prevent abuse or accidental overload.
        """
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        # Make multiple rapid requests
        for _ in range(100):
            response = client.post(
                "/profiling/start", json={"cpu": True}, headers=headers
            )

        # Should eventually get rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestProfilingAuditLogging:
    """Test that profiling access is logged for audit trails."""

    @pytest.mark.skip(reason="Audit logging for profiling not yet implemented")
    def test_profiling_access_is_logged(self, client, admin_user_token, db):
        """
        RECOMMENDED: Log profiling endpoint access for security audits.

        Track who accessed profiling data and when for security monitoring.
        """
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        response = client.get("/profiling/status", headers=headers)

        # Check that access was logged
        # (implementation depends on your audit logging system)
        assert response.status_code in [200, 404]
        # TODO: Verify audit log entry was created
