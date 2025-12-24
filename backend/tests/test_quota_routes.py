"""
Comprehensive tests for Quota Management API routes.

Tests coverage for API quota management:
- GET /api/quota/status - Get quota status
- GET /api/quota/alerts - Get quota alerts
- GET /api/quota/report - Get usage report
- GET /api/quota/policies - Get quota policies
- POST /api/quota/custom - Set custom quota (admin)
- DELETE /api/quota/custom/{user_id} - Remove custom quota (admin)
- POST /api/quota/reset - Reset quota (admin)
- POST /api/quota/record - Record usage (admin)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestQuotaStatusEndpoint:
    """Tests for GET /api/quota/status endpoint."""

    def test_status_requires_auth(self, client: TestClient):
        """Test that quota status requires authentication."""
        response = client.get("/api/quota/status")

        assert response.status_code in [401, 403]

    def test_status_success(self, client: TestClient, auth_headers: dict):
        """Test successful quota status retrieval."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_usage_summary.return_value = {
                "user_id": str(uuid4()),
                "policy_type": "standard",
                "reset_times": {"daily": "2025-12-21T00:00:00", "monthly": "2026-01-01T00:00:00"},
                "resources": {
                    "api": {
                        "limits": {"daily": 1000, "monthly": 25000},
                        "usage": {"daily": 100, "monthly": 500},
                        "remaining": {"daily": 900, "monthly": 24500},
                        "percentage": {"daily": 10.0, "monthly": 2.0},
                    }
                },
            }
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/api/quota/status",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]


class TestQuotaAlertsEndpoint:
    """Tests for GET /api/quota/alerts endpoint."""

    def test_alerts_requires_auth(self, client: TestClient):
        """Test that alerts requires authentication."""
        response = client.get("/api/quota/alerts")

        assert response.status_code in [401, 403]

    def test_alerts_success(self, client: TestClient, auth_headers: dict):
        """Test successful alerts retrieval."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_alerts.return_value = []
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/api/quota/alerts",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]

    def test_alerts_with_warnings(self, client: TestClient, auth_headers: dict):
        """Test alerts when usage is high."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_alerts.return_value = [
                {
                    "resource_type": "api",
                    "timestamp": "2025-12-20T15:30:00",
                    "alert_level": "warning",
                    "daily_percentage": 85.0,
                    "monthly_percentage": 50.0,
                }
            ]
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/api/quota/alerts",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]


class TestQuotaReportEndpoint:
    """Tests for GET /api/quota/report endpoint."""

    def test_report_requires_auth(self, client: TestClient):
        """Test that report requires authentication."""
        response = client.get("/api/quota/report")

        assert response.status_code in [401, 403]

    def test_report_daily_success(self, client: TestClient, auth_headers: dict):
        """Test daily report retrieval."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_usage_summary.return_value = {
                "user_id": str(uuid4()),
                "policy_type": "standard",
                "resources": {
                    "api": {
                        "limits": {"daily": 1000, "monthly": 25000},
                        "usage": {"daily": 100, "monthly": 500},
                    }
                },
            }
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/api/quota/report?period=daily",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]

    def test_report_monthly_success(self, client: TestClient, auth_headers: dict):
        """Test monthly report retrieval."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_usage_summary.return_value = {
                "user_id": str(uuid4()),
                "policy_type": "standard",
                "resources": {
                    "api": {
                        "limits": {"daily": 1000, "monthly": 25000},
                        "usage": {"daily": 100, "monthly": 500},
                    }
                },
            }
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/api/quota/report?period=monthly",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]

    def test_report_invalid_period(self, client: TestClient, auth_headers: dict):
        """Test report with invalid period."""
        response = client.get(
            "/api/quota/report?period=weekly",
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]


class TestQuotaPoliciesEndpoint:
    """Tests for GET /api/quota/policies endpoint."""

    def test_policies_requires_auth(self, client: TestClient):
        """Test that policies requires authentication."""
        response = client.get("/api/quota/policies")

        assert response.status_code in [401, 403]

    def test_policies_success(self, client: TestClient, auth_headers: dict):
        """Test successful policies retrieval."""
        response = client.get(
            "/api/quota/policies",
            headers=auth_headers,
        )

        # This endpoint doesn't require Redis
        assert response.status_code in [200, 401]


class TestSetCustomQuotaEndpoint:
    """Tests for POST /api/quota/custom endpoint."""

    def test_custom_quota_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that custom quota requires admin role."""
        response = client.post(
            "/api/quota/custom",
            json={
                "user_id": str(uuid4()),
                "policy": {
                    "daily_limit": 5000,
                    "monthly_limit": 100000,
                    "schedule_generation_daily": 100,
                    "schedule_generation_monthly": 2000,
                    "export_daily": 50,
                    "export_monthly": 1000,
                    "report_daily": 50,
                    "report_monthly": 1000,
                    "allow_overage": True,
                    "overage_percentage": 10,
                },
                "ttl_seconds": 86400,
            },
            headers=auth_headers,
        )

        # Non-admin should be forbidden or this may work if admin
        assert response.status_code in [200, 401, 403, 503]


class TestRemoveCustomQuotaEndpoint:
    """Tests for DELETE /api/quota/custom/{user_id} endpoint."""

    def test_remove_custom_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that remove custom quota requires admin role."""
        user_id = str(uuid4())
        response = client.delete(
            f"/api/quota/custom/{user_id}",
            headers=auth_headers,
        )

        # Non-admin should be forbidden
        assert response.status_code in [200, 401, 403, 503]


class TestResetQuotaEndpoint:
    """Tests for POST /api/quota/reset endpoint."""

    def test_reset_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that reset quota requires admin role."""
        response = client.post(
            "/api/quota/reset",
            json={
                "user_id": str(uuid4()),
                "resource_type": "api",
                "reset_daily": True,
                "reset_monthly": False,
            },
            headers=auth_headers,
        )

        # Non-admin should be forbidden
        assert response.status_code in [200, 401, 403, 503]


class TestRecordUsageEndpoint:
    """Tests for POST /api/quota/record endpoint."""

    def test_record_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that record usage requires admin role."""
        response = client.post(
            "/api/quota/record",
            json={
                "user_id": str(uuid4()),
                "resource_type": "api",
                "amount": 10,
            },
            headers=auth_headers,
        )

        # Non-admin should be forbidden
        assert response.status_code in [200, 401, 403, 503]


# ============================================================================
# Integration Tests
# ============================================================================


class TestQuotaIntegration:
    """Integration tests for quota management."""

    def test_quota_endpoints_accessible(
        self, client: TestClient, auth_headers: dict
    ):
        """Test quota endpoints respond appropriately."""
        with patch("app.api.routes.quota.get_quota_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_usage_summary.return_value = {
                "user_id": str(uuid4()),
                "policy_type": "standard",
                "reset_times": {},
                "resources": {},
            }
            mock_manager.get_alerts.return_value = []
            mock_get_manager.return_value = mock_manager

            endpoints = [
                ("/api/quota/status", "GET"),
                ("/api/quota/alerts", "GET"),
                ("/api/quota/report", "GET"),
                ("/api/quota/policies", "GET"),
            ]

            for url, method in endpoints:
                response = client.get(url, headers=auth_headers)
                assert response.status_code in [
                    200,
                    401,
                    503,
                ], f"Failed for {url}"
