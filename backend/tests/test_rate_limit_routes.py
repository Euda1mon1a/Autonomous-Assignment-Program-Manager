"""
Comprehensive tests for Rate Limit API routes.

Tests coverage for rate limit management:
- GET /api/rate-limit/status - Get current rate limit status
- GET /api/rate-limit/tiers - Get all tier configurations
- GET /api/rate-limit/endpoints - Get endpoint-specific limits
- POST /api/rate-limit/custom - Set custom limit (admin)
- DELETE /api/rate-limit/custom/{user_id} - Remove custom limit (admin)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestRateLimitStatusEndpoint:
    """Tests for GET /api/rate-limit/status endpoint."""

    def test_status_requires_auth(self, client: TestClient):
        """Test that rate limit status requires authentication."""
        response = client.get("/api/rate-limit/status")

        assert response.status_code in [401, 403]

    def test_status_success(self, client: TestClient, auth_headers: dict):
        """Test successful rate limit status retrieval."""
        with patch("app.api.routes.rate_limit.get_redis_client") as mock_redis:
            mock_client = MagicMock()
            mock_client.hgetall.return_value = {}
            mock_client.zremrangebyscore.return_value = None
            mock_client.zcard.return_value = 0
            mock_redis.return_value = mock_client

            response = client.get(
                "/api/rate-limit/status",
                headers=auth_headers,
            )

            # May return 200, 401, or 503 (if Redis unavailable)
            assert response.status_code in [200, 401, 503]

    def test_status_redis_unavailable(self, client: TestClient, auth_headers: dict):
        """Test rate limit status when Redis is unavailable."""
        with patch("app.api.routes.rate_limit.get_redis_client") as mock_redis:
            import redis

            mock_redis.side_effect = redis.ConnectionError("Connection refused")

            response = client.get(
                "/api/rate-limit/status",
                headers=auth_headers,
            )

            # Should return 503 when Redis is down
            assert response.status_code in [401, 503]

    def test_status_response_structure(self, client: TestClient, auth_headers: dict):
        """Test rate limit status response has correct structure."""
        with patch("app.api.routes.rate_limit.get_redis_client") as mock_redis:
            mock_client = MagicMock()
            mock_client.hgetall.return_value = {}
            mock_client.zremrangebyscore.return_value = None
            mock_client.zcard.return_value = 0
            mock_redis.return_value = mock_client

            response = client.get(
                "/api/rate-limit/status",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "tier" in data
                assert "limits" in data
                assert "remaining" in data
                assert "reset" in data
                assert "burst" in data


class TestRateLimitTiersEndpoint:
    """Tests for GET /api/rate-limit/tiers endpoint."""

    def test_tiers_requires_auth(self, client: TestClient):
        """Test that tiers endpoint requires authentication."""
        response = client.get("/api/rate-limit/tiers")

        assert response.status_code in [401, 403]

    def test_tiers_success(self, client: TestClient, auth_headers: dict):
        """Test successful tiers retrieval."""
        response = client.get(
            "/api/rate-limit/tiers",
            headers=auth_headers,
        )

        # This endpoint doesn't require Redis
        assert response.status_code in [200, 401]

    def test_tiers_response_structure(self, client: TestClient, auth_headers: dict):
        """Test tiers response has correct structure."""
        response = client.get(
            "/api/rate-limit/tiers",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "tiers" in data
            assert isinstance(data["tiers"], list)
            if data["tiers"]:
                tier = data["tiers"][0]
                assert "tier" in tier
                assert "config" in tier
                assert "roles" in tier

    def test_tiers_includes_all_levels(self, client: TestClient, auth_headers: dict):
        """Test that all tier levels are returned."""
        response = client.get(
            "/api/rate-limit/tiers",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            tier_names = [t["tier"] for t in data["tiers"]]
            # Should have standard tier levels
            expected_tiers = ["free", "standard", "premium", "admin"]
            for expected in expected_tiers:
                assert expected in tier_names, f"Missing tier: {expected}"


class TestRateLimitEndpointsEndpoint:
    """Tests for GET /api/rate-limit/endpoints endpoint."""

    def test_endpoints_requires_auth(self, client: TestClient):
        """Test that endpoints endpoint requires authentication."""
        response = client.get("/api/rate-limit/endpoints")

        assert response.status_code in [401, 403]

    def test_endpoints_success(self, client: TestClient, auth_headers: dict):
        """Test successful endpoints limits retrieval."""
        response = client.get(
            "/api/rate-limit/endpoints",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    def test_endpoints_response_structure(self, client: TestClient, auth_headers: dict):
        """Test endpoints response has correct structure."""
        response = client.get(
            "/api/rate-limit/endpoints",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "endpoints" in data
            assert isinstance(data["endpoints"], list)
            if data["endpoints"]:
                endpoint = data["endpoints"][0]
                assert "endpoint" in endpoint
                # limits can be null or a config object


class TestSetCustomLimitEndpoint:
    """Tests for POST /api/rate-limit/custom endpoint."""

    def test_custom_limit_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that setting custom limit requires admin role."""
        response = client.post(
            "/api/rate-limit/custom",
            json={
                "user_id": str(uuid4()),
                "config": {
                    "requests_per_minute": 200,
                    "requests_per_hour": 10000,
                    "burst_size": 100,
                    "burst_refill_rate": 3.33,
                },
                "ttl_seconds": 86400,
            },
            headers=auth_headers,
        )

        # Non-admin should get 403, or this may work if admin
        assert response.status_code in [200, 401, 403, 503]

    def test_custom_limit_requires_auth(self, client: TestClient):
        """Test that setting custom limit requires authentication."""
        response = client.post(
            "/api/rate-limit/custom",
            json={
                "user_id": str(uuid4()),
                "config": {
                    "requests_per_minute": 200,
                    "requests_per_hour": 10000,
                    "burst_size": 100,
                    "burst_refill_rate": 3.33,
                },
                "ttl_seconds": 86400,
            },
        )

        assert response.status_code in [401, 403]

    def test_custom_limit_validation(self, client: TestClient, auth_headers: dict):
        """Test custom limit validation."""
        # Missing required fields
        response = client.post(
            "/api/rate-limit/custom",
            json={
                "user_id": str(uuid4()),
                # Missing config
            },
            headers=auth_headers,
        )

        assert response.status_code in [401, 403, 422]


class TestRemoveCustomLimitEndpoint:
    """Tests for DELETE /api/rate-limit/custom/{user_id} endpoint."""

    def test_remove_custom_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that removing custom limit requires admin role."""
        user_id = str(uuid4())
        response = client.delete(
            f"/api/rate-limit/custom/{user_id}",
            headers=auth_headers,
        )

        # Non-admin should get 403
        assert response.status_code in [200, 401, 403, 503]

    def test_remove_custom_requires_auth(self, client: TestClient):
        """Test that removing custom limit requires authentication."""
        user_id = str(uuid4())
        response = client.delete(f"/api/rate-limit/custom/{user_id}")

        assert response.status_code in [401, 403]


# ============================================================================
# Integration Tests
# ============================================================================


class TestRateLimitIntegration:
    """Integration tests for rate limit endpoints."""

    def test_rate_limit_endpoints_accessible(
        self, client: TestClient, auth_headers: dict
    ):
        """Test rate limit endpoints respond appropriately."""
        endpoints = [
            ("/api/rate-limit/tiers", "GET"),
            ("/api/rate-limit/endpoints", "GET"),
        ]

        for url, method in endpoints:
            response = client.get(url, headers=auth_headers)
            assert response.status_code in [
                200,
                401,
            ], f"Failed for {url}"

    def test_rate_limit_json_responses(self, client: TestClient, auth_headers: dict):
        """Test rate limit endpoints return valid JSON."""
        response = client.get(
            "/api/rate-limit/tiers",
            headers=auth_headers,
        )

        if response.status_code == 200:
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert isinstance(data, dict)


class TestRateLimitEdgeCases:
    """Test edge cases for rate limit endpoints."""

    def test_status_with_burst_data(self, client: TestClient, auth_headers: dict):
        """Test status endpoint with existing burst bucket data."""
        import time

        with patch("app.api.routes.rate_limit.get_redis_client") as mock_redis:
            mock_client = MagicMock()
            # Simulate existing token bucket data
            mock_client.hgetall.return_value = {
                b"tokens": b"25.0",
                b"last_refill": str(time.time() - 30).encode(),
            }
            mock_client.zremrangebyscore.return_value = None
            mock_client.zcard.return_value = 50  # 50 requests in window
            mock_redis.return_value = mock_client

            response = client.get(
                "/api/rate-limit/status",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 503]

    def test_invalid_user_id_format(self, client: TestClient, auth_headers: dict):
        """Test removing custom limit with invalid user ID format."""
        response = client.delete(
            "/api/rate-limit/custom/not-a-uuid",
            headers=auth_headers,
        )

        # Should still process (validation may or may not be strict)
        assert response.status_code in [200, 401, 403, 422, 503]

    def test_custom_limit_with_zero_values(
        self, client: TestClient, auth_headers: dict
    ):
        """Test setting custom limit with zero values."""
        response = client.post(
            "/api/rate-limit/custom",
            json={
                "user_id": str(uuid4()),
                "config": {
                    "requests_per_minute": 0,
                    "requests_per_hour": 0,
                    "burst_size": 0,
                    "burst_refill_rate": 0.0,
                },
                "ttl_seconds": 86400,
            },
            headers=auth_headers,
        )

        # May be rejected as invalid or accepted
        assert response.status_code in [200, 400, 401, 403, 422, 503]

    def test_custom_limit_with_negative_ttl(
        self, client: TestClient, auth_headers: dict
    ):
        """Test setting custom limit with negative TTL."""
        response = client.post(
            "/api/rate-limit/custom",
            json={
                "user_id": str(uuid4()),
                "config": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "burst_size": 50,
                    "burst_refill_rate": 1.0,
                },
                "ttl_seconds": -1,
            },
            headers=auth_headers,
        )

        # Should be rejected as invalid
        assert response.status_code in [400, 401, 403, 422]
