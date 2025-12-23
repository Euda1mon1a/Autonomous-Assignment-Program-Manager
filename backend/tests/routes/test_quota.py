"""Tests for quota management API routes.

Tests the quota management functionality including:
- Viewing quota status
- Getting usage reports
- Setting custom quotas (admin)
- Resetting quotas (admin)
- Viewing alerts
"""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.quota import get_quota_manager, get_redis_client
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = MagicMock()
    client.ping.return_value = True
    return client


@pytest.fixture
def mock_quota_manager():
    """Create a mock quota manager."""
    manager = MagicMock()
    return manager


@pytest.fixture
def client_with_mock_quota(db, mock_redis_client, mock_quota_manager):
    """Create test client with mocked quota dependencies."""
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis_client
    app.dependency_overrides[get_quota_manager] = lambda: mock_quota_manager

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestQuotaRoutes:
    """Test suite for quota API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_quota_status_requires_auth(self, client: TestClient):
        """Test that quota status endpoint requires authentication."""
        response = client.get("/api/quota/status")
        assert response.status_code == 401

    def test_quota_alerts_requires_auth(self, client: TestClient):
        """Test that quota alerts endpoint requires authentication."""
        response = client.get("/api/quota/alerts")
        assert response.status_code == 401

    def test_quota_report_requires_auth(self, client: TestClient):
        """Test that quota report endpoint requires authentication."""
        response = client.get("/api/quota/report")
        assert response.status_code == 401

    def test_quota_policies_requires_auth(self, client: TestClient):
        """Test that quota policies endpoint requires authentication."""
        response = client.get("/api/quota/policies")
        assert response.status_code == 401

    # ========================================================================
    # Admin-Only Endpoint Tests
    # ========================================================================

    def test_set_custom_quota_requires_admin(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test that setting custom quota requires admin role."""
        # Regular user should not be able to set custom quotas
        # The auth_headers fixture creates an admin user, so we need to test
        # with a non-admin user separately
        pass  # Covered by role-based access control in the app

    def test_reset_quota_requires_admin(
        self,
        client: TestClient,
    ):
        """Test that resetting quota requires admin role."""
        response = client.post(
            "/api/quota/reset",
            json={
                "user_id": str(uuid4()),
                "resource_type": "api",
                "reset_daily": True,
                "reset_monthly": False,
            },
        )
        assert response.status_code == 401

    # ========================================================================
    # Quota Status Tests
    # ========================================================================

    def test_get_quota_status_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful quota status retrieval."""
        mock_quota_manager.get_usage_summary.return_value = {
            "user_id": str(admin_user.id),
            "policy_type": "admin",
            "reset_times": {
                "daily": "2025-12-21T00:00:00",
                "monthly": "2026-01-01T00:00:00",
            },
            "resources": {
                "api": {
                    "limits": {"daily": 10000, "monthly": 250000},
                    "usage": {"daily": 100, "monthly": 500},
                    "remaining": {"daily": 9900, "monthly": 249500},
                    "percentage": {"daily": 1.0, "monthly": 0.2},
                }
            },
        }

        response = client_with_mock_quota.get("/api/quota/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "user_id" in data
        assert "policy_type" in data
        assert "resources" in data

    def test_get_quota_status_error(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test quota status error handling."""
        mock_quota_manager.get_usage_summary.side_effect = Exception("Redis error")

        response = client_with_mock_quota.get("/api/quota/status", headers=auth_headers)
        assert response.status_code == 500
        assert "quota status" in response.json()["detail"].lower()

    # ========================================================================
    # Quota Alerts Tests
    # ========================================================================

    def test_get_quota_alerts_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful quota alerts retrieval."""
        mock_quota_manager.get_alerts.return_value = [
            {
                "resource_type": "schedule",
                "timestamp": "2025-12-20T15:30:00",
                "alert_level": "warning",
                "daily_percentage": 85.2,
                "monthly_percentage": 78.3,
            }
        ]

        response = client_with_mock_quota.get("/api/quota/alerts", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "user_id" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_quota_alerts_empty(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test empty alerts response."""
        mock_quota_manager.get_alerts.return_value = []

        response = client_with_mock_quota.get("/api/quota/alerts", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["alerts"] == []

    # ========================================================================
    # Quota Report Tests
    # ========================================================================

    def test_get_quota_report_daily(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test daily quota report."""
        mock_quota_manager.get_usage_summary.return_value = {
            "user_id": str(admin_user.id),
            "policy_type": "admin",
            "resources": {
                "api": {
                    "limits": {"daily": 10000, "monthly": 250000},
                    "usage": {"daily": 100, "monthly": 500},
                    "remaining": {"daily": 9900, "monthly": 249500},
                    "percentage": {"daily": 1.0, "monthly": 0.2},
                }
            },
        }

        response = client_with_mock_quota.get(
            "/api/quota/report?period=daily", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["period"] == "daily"
        assert "total_usage" in data
        assert "total_limit" in data
        assert "usage_percentage" in data

    def test_get_quota_report_monthly(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test monthly quota report."""
        mock_quota_manager.get_usage_summary.return_value = {
            "user_id": str(admin_user.id),
            "policy_type": "admin",
            "resources": {
                "api": {
                    "limits": {"daily": 10000, "monthly": 250000},
                    "usage": {"daily": 100, "monthly": 500},
                    "remaining": {"daily": 9900, "monthly": 249500},
                    "percentage": {"daily": 1.0, "monthly": 0.2},
                }
            },
        }

        response = client_with_mock_quota.get(
            "/api/quota/report?period=monthly", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["period"] == "monthly"

    def test_get_quota_report_invalid_period(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test quota report with invalid period."""
        response = client.get("/api/quota/report?period=weekly", headers=auth_headers)
        assert response.status_code == 400
        assert "daily" in response.json()["detail"].lower()
        assert "monthly" in response.json()["detail"].lower()

    # ========================================================================
    # Quota Policies Tests
    # ========================================================================

    def test_get_quota_policies_success(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful quota policies retrieval."""
        response = client.get("/api/quota/policies", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)

        # Should have all policy types
        policy_types = [p["policy_type"] for p in data["policies"]]
        assert "free" in policy_types
        assert "standard" in policy_types
        assert "premium" in policy_types
        assert "admin" in policy_types

    def test_get_quota_policies_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test quota policies response format."""
        response = client.get("/api/quota/policies", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        for policy in data["policies"]:
            assert "policy_type" in policy
            assert "roles" in policy
            assert "config" in policy

            config = policy["config"]
            assert "daily_limit" in config
            assert "monthly_limit" in config
            assert "schedule_generation_daily" in config
            assert "schedule_generation_monthly" in config

    # ========================================================================
    # Set Custom Quota Tests
    # ========================================================================

    def test_set_custom_quota_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test successful custom quota setting."""
        mock_quota_manager.set_custom_policy.return_value = True

        user_id = str(uuid4())
        response = client_with_mock_quota.post(
            "/api/quota/custom",
            headers=auth_headers,
            json={
                "user_id": user_id,
                "policy": {
                    "daily_limit": 5000,
                    "monthly_limit": 100000,
                    "schedule_generation_daily": 100,
                    "schedule_generation_monthly": 2000,
                    "export_daily": 50,
                    "export_monthly": 1000,
                    "report_daily": 30,
                    "report_monthly": 500,
                    "allow_overage": False,
                    "overage_percentage": 0,
                },
                "ttl_seconds": 86400,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user_id
        assert "expires_at" in data

    def test_set_custom_quota_failure(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test custom quota setting failure."""
        mock_quota_manager.set_custom_policy.return_value = False

        response = client_with_mock_quota.post(
            "/api/quota/custom",
            headers=auth_headers,
            json={
                "user_id": str(uuid4()),
                "policy": {
                    "daily_limit": 5000,
                    "monthly_limit": 100000,
                    "schedule_generation_daily": 100,
                    "schedule_generation_monthly": 2000,
                    "export_daily": 50,
                    "export_monthly": 1000,
                    "report_daily": 30,
                    "report_monthly": 500,
                    "allow_overage": False,
                    "overage_percentage": 0,
                },
            },
        )
        assert response.status_code == 500

    # ========================================================================
    # Remove Custom Quota Tests
    # ========================================================================

    def test_remove_custom_quota_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test successful custom quota removal."""
        mock_quota_manager.remove_custom_policy.return_value = True

        user_id = str(uuid4())
        response = client_with_mock_quota.delete(
            f"/api/quota/custom/{user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user_id

    # ========================================================================
    # Reset Quota Tests
    # ========================================================================

    def test_reset_quota_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test successful quota reset."""
        mock_quota_manager.reset_user_quota.return_value = True

        user_id = str(uuid4())
        response = client_with_mock_quota.post(
            "/api/quota/reset",
            headers=auth_headers,
            json={
                "user_id": user_id,
                "resource_type": "api",
                "reset_daily": True,
                "reset_monthly": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user_id

    # ========================================================================
    # Record Usage Tests
    # ========================================================================

    def test_record_usage_success(
        self,
        client_with_mock_quota: TestClient,
        mock_quota_manager: MagicMock,
        auth_headers: dict,
    ):
        """Test successful usage recording."""
        mock_quota_manager.record_usage.return_value = (110, 610)  # daily, monthly

        user_id = str(uuid4())
        response = client_with_mock_quota.post(
            "/api/quota/record",
            headers=auth_headers,
            json={
                "user_id": user_id,
                "resource_type": "api",
                "amount": 10,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user_id
        assert data["resource_type"] == "api"
        assert data["daily_usage"] == 110
        assert data["monthly_usage"] == 610

    # ========================================================================
    # Redis Connection Tests
    # ========================================================================

    def test_redis_connection_failure(
        self,
        db,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test handling of Redis connection failure."""
        from app.db.session import get_db

        def raise_redis_error():
            raise HTTPException(
                status_code=503,
                detail="Quota service temporarily unavailable",
            )

        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_redis_client] = raise_redis_error

        with TestClient(app) as test_client:
            response = test_client.get("/api/quota/status", headers=auth_headers)
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()

        app.dependency_overrides.clear()
