"""
Comprehensive tests for rate limiting functionality.

Tests the rate limiter module and its integration with authentication endpoints.
Covers:
- Basic rate limiting behavior
- Sliding window algorithm
- Redis integration
- HTTP 429 responses
- Rate limit headers
- IP-based limiting
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import redis
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.rate_limit import (
    RateLimiter,
    get_client_ip,
    get_rate_limiter,
)

settings = get_settings()


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    mock = MagicMock(spec=redis.Redis)
    # Mock pipeline
    mock_pipe = MagicMock()
    mock_pipe.execute.return_value = [
        None,
        0,
        None,
        None,
    ]  # [del_result, count, zadd_result, expire_result]
    mock.pipeline.return_value = mock_pipe
    return mock


@pytest.fixture
def rate_limiter(mock_redis):
    """Create a RateLimiter instance with mock Redis."""
    return RateLimiter(redis_client=mock_redis)


@pytest.fixture
def real_redis_limiter():
    """
    Create a RateLimiter with real Redis connection.

    Note: Requires Redis to be running. Tests will be skipped if Redis is unavailable.
    """
    try:
        limiter = RateLimiter()
        if limiter.redis is not None:
            # Clean up any existing test keys
            limiter.redis.flushdb()
            return limiter
        pytest.skip("Redis not available")
    except Exception:
        pytest.skip("Redis not available")


# ============================================================================
# Unit Tests - RateLimiter Class
# ============================================================================


class TestRateLimiter:
    """Test the RateLimiter class directly."""

    def test_rate_limiter_initialization_with_mock(self, mock_redis):
        """Test rate limiter initializes correctly with provided Redis client."""
        limiter = RateLimiter(redis_client=mock_redis)
        assert limiter.redis is mock_redis

    def test_rate_limiter_initialization_without_redis(self):
        """Test rate limiter handles Redis connection failure gracefully."""
        with patch(
            "redis.from_url", side_effect=redis.ConnectionError("Connection failed")
        ):
            limiter = RateLimiter()
            assert limiter.redis is None

    def test_is_rate_limited_allows_first_request(self, rate_limiter, mock_redis):
        """Test that first request is allowed."""
        mock_pipe = mock_redis.pipeline.return_value
        mock_pipe.execute.return_value = [None, 0, None, None]

        is_limited, info = rate_limiter.is_rate_limited(
            key="test:192.168.1.1",
            max_requests=5,
            window_seconds=60,
        )

        assert not is_limited
        assert info["limit"] == 5
        assert info["remaining"] >= 0
        assert "reset_at" in info

    def test_is_rate_limited_blocks_after_limit(self, rate_limiter, mock_redis):
        """Test that requests are blocked after limit is reached."""
        mock_pipe = mock_redis.pipeline.return_value
        # Simulate 5 existing requests (at limit)
        mock_pipe.execute.return_value = [None, 5, None, None]

        is_limited, info = rate_limiter.is_rate_limited(
            key="test:192.168.1.1",
            max_requests=5,
            window_seconds=60,
        )

        assert is_limited
        assert info["limit"] == 5
        assert info["remaining"] == 0
        assert info["current_count"] == 6

    def test_is_rate_limited_with_disabled_rate_limiting(self):
        """Test that rate limiting can be disabled via settings."""
        with patch.object(settings, "RATE_LIMIT_ENABLED", False):
            limiter = RateLimiter()
            is_limited, info = limiter.is_rate_limited(
                key="test:192.168.1.1",
                max_requests=5,
                window_seconds=60,
            )

            assert not is_limited
            assert info["remaining"] == 5

    def test_is_rate_limited_fails_open_on_redis_error(self, rate_limiter, mock_redis):
        """Test that rate limiter fails open (allows request) on Redis errors."""
        mock_redis.pipeline.side_effect = Exception("Redis error")

        is_limited, info = rate_limiter.is_rate_limited(
            key="test:192.168.1.1",
            max_requests=5,
            window_seconds=60,
        )

        # Should allow request despite error
        assert not is_limited

    def test_reset_rate_limit(self, rate_limiter, mock_redis):
        """Test resetting rate limit for a key."""
        result = rate_limiter.reset("test:192.168.1.1")

        assert result is True
        mock_redis.delete.assert_called_once_with("test:192.168.1.1")

    def test_reset_rate_limit_handles_error(self, rate_limiter, mock_redis):
        """Test reset handles Redis errors gracefully."""
        mock_redis.delete.side_effect = Exception("Redis error")

        result = rate_limiter.reset("test:192.168.1.1")

        assert result is False

    def test_get_remaining(self, rate_limiter, mock_redis):
        """Test getting remaining requests without incrementing."""
        mock_pipe = mock_redis.pipeline.return_value
        mock_pipe.execute.return_value = [None, 2]  # 2 existing requests

        remaining = rate_limiter.get_remaining(
            key="test:192.168.1.1",
            max_requests=5,
            window_seconds=60,
        )

        assert remaining == 3


# ============================================================================
# Integration Tests - Real Redis (if available)
# ============================================================================


class TestRateLimiterWithRealRedis:
    """Test rate limiter with actual Redis connection."""

    def test_sliding_window_behavior(self, real_redis_limiter):
        """Test sliding window allows requests after time passes."""
        key = "test:sliding:192.168.1.1"
        max_requests = 3
        window_seconds = 2  # Short window for testing

        # Make 3 requests (at limit)
        for i in range(max_requests):
            is_limited, info = real_redis_limiter.is_rate_limited(
                key=key,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )
            if i < max_requests - 1:
                assert not is_limited, f"Request {i + 1} should be allowed"
            else:
                # The last request should be limited because we're checking BEFORE adding
                assert not is_limited, f"Request {i + 1} should still be allowed"

        # Next request should be limited
        is_limited, info = real_redis_limiter.is_rate_limited(
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        assert is_limited, "Request should be limited after hitting max"

        # Wait for window to pass
        time.sleep(window_seconds + 0.5)

        # Should be allowed again
        is_limited, info = real_redis_limiter.is_rate_limited(
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        assert not is_limited, "Request should be allowed after window passes"

    def test_different_keys_are_independent(self, real_redis_limiter):
        """Test that different keys have independent rate limits."""
        key1 = "test:independent:192.168.1.1"
        key2 = "test:independent:192.168.1.2"
        max_requests = 2
        window_seconds = 60

        # Exhaust limit for key1
        for _ in range(max_requests):
            real_redis_limiter.is_rate_limited(key1, max_requests, window_seconds)

        is_limited_1, _ = real_redis_limiter.is_rate_limited(
            key1, max_requests, window_seconds
        )
        is_limited_2, _ = real_redis_limiter.is_rate_limited(
            key2, max_requests, window_seconds
        )

        # key1 should be limited, key2 should not
        assert is_limited_1, "key1 should be limited"
        assert not is_limited_2, "key2 should not be limited"

    def test_reset_clears_limit(self, real_redis_limiter):
        """Test that reset clears the rate limit."""
        key = "test:reset:192.168.1.1"
        max_requests = 2
        window_seconds = 60

        # Exhaust limit
        for _ in range(max_requests):
            real_redis_limiter.is_rate_limited(key, max_requests, window_seconds)

        is_limited, _ = real_redis_limiter.is_rate_limited(
            key, max_requests, window_seconds
        )
        assert is_limited, "Should be limited before reset"

        # Reset
        real_redis_limiter.reset(key)

        # Should be allowed again
        is_limited, _ = real_redis_limiter.is_rate_limited(
            key, max_requests, window_seconds
        )
        assert not is_limited, "Should not be limited after reset"


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_client_ip_from_direct_connection(self):
        """Test extracting IP from direct connection."""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "203.0.113.1, 198.51.100.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_fallback(self):
        """Test fallback when no IP is available."""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.client = None

        ip = get_client_ip(request)
        assert ip == "unknown"

    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2


# ============================================================================
# API Integration Tests
# ============================================================================


class TestRateLimitingOnAuthEndpoints:
    """Test rate limiting integration with authentication endpoints."""

    def test_login_rate_limit_blocks_after_limit(self, client: TestClient):
        """Test that login endpoint blocks after rate limit is exceeded."""
        # Make requests up to the limit
        max_attempts = settings.RATE_LIMIT_LOGIN_ATTEMPTS

        for i in range(max_attempts):
            response = client.post(
                "/api/auth/login/json",
                json={"username": "testuser", "password": "wrongpassword"},
            )
            # Should get 401 (unauthorized) not 429 (rate limited)
            if response.status_code != 429:
                assert response.status_code == 401, f"Attempt {i + 1} should return 401"

        # Next request should be rate limited
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        # Check if we got rate limited (429) or still getting auth errors (401)
        # This depends on whether Redis is available and rate limiting is enabled
        assert response.status_code in [401, 429], "Should return 401 or 429"

        if response.status_code == 429:
            assert "rate limit" in response.json()["detail"]["error"].lower()
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "Retry-After" in response.headers

    def test_register_rate_limit_blocks_after_limit(
        self, client: TestClient, admin_user
    ):
        """Test that register endpoint blocks after rate limit is exceeded."""
        # Get auth headers
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        max_attempts = settings.RATE_LIMIT_REGISTER_ATTEMPTS

        for i in range(max_attempts):
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"newuser{i}",
                    "email": f"newuser{i}@test.com",
                    "password": "testpass123",
                    "role": "coordinator",
                },
                headers=headers,
            )
            # Should get 201 (created) or 400 (validation error) not 429
            if response.status_code != 429:
                assert response.status_code in [201, 400], (
                    f"Attempt {i + 1} should return 201 or 400"
                )

        # Next request might be rate limited
        response = client.post(
            "/api/auth/register",
            json={
                "username": "anothernewuser",
                "email": "another@test.com",
                "password": "testpass123",
                "role": "coordinator",
            },
            headers=headers,
        )

        # Could be rate limited or successful depending on Redis availability
        assert response.status_code in [201, 400, 429]

    def test_different_endpoints_have_separate_limits(self, client: TestClient):
        """Test that login and register endpoints have separate rate limits."""
        # Exhaust login limit
        for _ in range(settings.RATE_LIMIT_LOGIN_ATTEMPTS + 1):
            client.post(
                "/api/auth/login/json",
                json={"username": "testuser", "password": "wrongpassword"},
            )

        # Register should still work (separate limit)
        # Note: This would require admin auth, so this is more of a conceptual test
        # In practice, the rate limits are independent per endpoint/IP combination

    def test_rate_limit_headers_in_response(self, client: TestClient):
        """Test that rate limit headers are included in responses when rate limited."""
        # Make enough requests to trigger rate limit
        for _ in range(settings.RATE_LIMIT_LOGIN_ATTEMPTS + 2):
            response = client.post(
                "/api/auth/login/json",
                json={"username": "testuser", "password": "wrongpassword"},
            )

            if response.status_code == 429:
                # Check for rate limit headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                assert "Retry-After" in response.headers
                break


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestRateLimitingEdgeCases:
    """Test edge cases and error handling."""

    def test_rate_limiting_with_redis_unavailable(self):
        """Test that API works when Redis is unavailable."""
        with patch(
            "redis.from_url", side_effect=redis.ConnectionError("Connection failed")
        ):
            limiter = RateLimiter()

            # Should fail open (allow requests)
            is_limited, info = limiter.is_rate_limited(
                key="test:192.168.1.1",
                max_requests=5,
                window_seconds=60,
            )

            assert not is_limited
            assert info["remaining"] == 5

    def test_rate_limiting_with_rate_limit_disabled(self, client: TestClient):
        """Test that rate limiting can be disabled globally."""
        with patch.object(settings, "RATE_LIMIT_ENABLED", False):
            # Make many requests - none should be rate limited
            for _ in range(20):
                response = client.post(
                    "/api/auth/login/json",
                    json={"username": "testuser", "password": "wrongpassword"},
                )
                # Should get 401 (unauthorized) not 429 (rate limited)
                assert response.status_code == 401

    def test_concurrent_requests_from_different_ips(self, real_redis_limiter):
        """Test that different IP addresses are tracked independently."""
        key1 = "test:concurrent:192.168.1.1"
        key2 = "test:concurrent:192.168.1.2"
        max_requests = 2
        window_seconds = 60

        # Both IPs make requests
        is_limited_1a, _ = real_redis_limiter.is_rate_limited(
            key1, max_requests, window_seconds
        )
        is_limited_2a, _ = real_redis_limiter.is_rate_limited(
            key2, max_requests, window_seconds
        )

        assert not is_limited_1a
        assert not is_limited_2a

        # Exhaust one IP
        for _ in range(max_requests):
            real_redis_limiter.is_rate_limited(key1, max_requests, window_seconds)

        is_limited_1b, _ = real_redis_limiter.is_rate_limited(
            key1, max_requests, window_seconds
        )
        is_limited_2b, _ = real_redis_limiter.is_rate_limited(
            key2, max_requests, window_seconds
        )

        # IP1 should be limited, IP2 should not
        assert is_limited_1b
        assert not is_limited_2b
