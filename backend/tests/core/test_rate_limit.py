"""Tests for rate limiting module (sliding window + account lockout)."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    AccountLockout,
    RateLimiter,
    _is_trusted_proxy,
    create_rate_limit_dependency,
    get_client_ip,
)


# ==================== RateLimiter (no Redis) ====================


class TestRateLimiterNoRedis:
    def test_no_redis_allows_request(self):
        limiter = RateLimiter(redis_client=None)
        limiter.redis = None
        limited, info = limiter.is_rate_limited("test", 10, 60)
        assert limited is False
        assert info["remaining"] == 10
        assert info["limit"] == 10

    def test_no_redis_reset_returns_false(self):
        limiter = RateLimiter(redis_client=None)
        limiter.redis = None
        assert limiter.reset("test") is False

    @patch("app.core.rate_limit.settings")
    def test_rate_limit_disabled_allows_request(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = False
        mock_redis = MagicMock()
        limiter = RateLimiter(redis_client=mock_redis)
        limited, info = limiter.is_rate_limited("test", 10, 60)
        assert limited is False

    @patch("app.core.rate_limit.settings")
    def test_get_remaining_no_redis(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        limiter = RateLimiter(redis_client=mock_redis)
        limiter.redis = None  # Simulate Redis unavailable after init
        assert limiter.get_remaining("test", 10, 60) == 10


# ==================== RateLimiter (with mock Redis) ====================


class TestRateLimiterWithRedis:
    @patch("app.core.rate_limit.settings")
    def test_not_limited_under_threshold(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 3, None, None]  # 3 requests so far
        mock_redis.pipeline.return_value = mock_pipe

        limiter = RateLimiter(redis_client=mock_redis)
        limited, info = limiter.is_rate_limited("test", 10, 60)
        assert limited is False
        assert info["remaining"] == 6  # 10 - 3 - 1

    @patch("app.core.rate_limit.settings")
    def test_limited_at_threshold(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 10, None, None]  # 10 = max
        mock_redis.pipeline.return_value = mock_pipe

        limiter = RateLimiter(redis_client=mock_redis)
        limited, info = limiter.is_rate_limited("test", 10, 60)
        assert limited is True
        assert info["remaining"] == 0

    @patch("app.core.rate_limit.settings")
    def test_redis_error_fails_open(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.side_effect = Exception("Redis down")
        mock_redis.pipeline.return_value = mock_pipe

        limiter = RateLimiter(redis_client=mock_redis)
        limited, info = limiter.is_rate_limited("test", 10, 60)
        assert limited is False  # Fail open

    @patch("app.core.rate_limit.settings")
    def test_reset_success(self, mock_settings):
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        limiter = RateLimiter(redis_client=mock_redis)
        assert limiter.reset("test") is True

    @patch("app.core.rate_limit.settings")
    def test_reset_error(self, mock_settings):
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = Exception("Redis down")
        limiter = RateLimiter(redis_client=mock_redis)
        assert limiter.reset("test") is False

    @patch("app.core.rate_limit.settings")
    def test_get_remaining_with_redis(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 3]  # 3 requests so far
        mock_redis.pipeline.return_value = mock_pipe

        limiter = RateLimiter(redis_client=mock_redis)
        remaining = limiter.get_remaining("test", 10, 60)
        assert remaining == 7  # 10 - 3


# ==================== AccountLockout constants ====================


class TestAccountLockoutConstants:
    def test_max_failed_attempts(self):
        assert AccountLockout.MAX_FAILED_ATTEMPTS == 5

    def test_base_lockout_seconds(self):
        assert AccountLockout.BASE_LOCKOUT_SECONDS == 60

    def test_max_lockout_seconds(self):
        assert AccountLockout.MAX_LOCKOUT_SECONDS == 3600

    def test_backoff_multiplier(self):
        assert AccountLockout.BACKOFF_MULTIPLIER == 2.0


# ==================== AccountLockout key helpers ====================


class TestAccountLockoutKeys:
    def test_lockout_key_format(self):
        lockout = AccountLockout(redis_client=MagicMock())
        assert lockout._get_lockout_key("Admin") == "account_lockout:admin"

    def test_attempts_key_format(self):
        lockout = AccountLockout(redis_client=MagicMock())
        assert lockout._get_attempts_key("Admin") == "account_attempts:admin"

    def test_case_insensitive(self):
        lockout = AccountLockout(redis_client=MagicMock())
        assert lockout._get_lockout_key("ADMIN") == lockout._get_lockout_key("admin")
        assert lockout._get_attempts_key("ADMIN") == lockout._get_attempts_key("admin")


# ==================== AccountLockout (no Redis) ====================


class TestAccountLockoutNoRedis:
    @patch("app.core.rate_limit.settings")
    def test_record_failed_no_redis(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        lockout = AccountLockout(redis_client=mock_redis)
        lockout.redis = None  # Simulate Redis unavailable after init
        is_locked, remaining, lockout_secs = lockout.record_failed_attempt("user")
        assert is_locked is False
        assert remaining == AccountLockout.MAX_FAILED_ATTEMPTS
        assert lockout_secs == 0

    @patch("app.core.rate_limit.settings")
    def test_check_lockout_no_redis(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        lockout = AccountLockout(redis_client=mock_redis)
        lockout.redis = None  # Simulate Redis unavailable after init
        is_locked, secs = lockout.check_lockout("user")
        assert is_locked is False
        assert secs == 0

    def test_clear_lockout_no_redis(self):
        lockout = AccountLockout(redis_client=None)
        lockout.redis = None
        assert lockout.clear_lockout("user") is False

    def test_get_failed_attempts_no_redis(self):
        lockout = AccountLockout(redis_client=None)
        lockout.redis = None
        assert lockout.get_failed_attempts("user") == 0


# ==================== AccountLockout (mock Redis) ====================


class TestAccountLockoutWithRedis:
    @patch("app.core.rate_limit.settings")
    def test_record_failed_not_locked(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = -2  # No lockout key
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [2, True]  # 2nd attempt
        mock_redis.pipeline.return_value = mock_pipe

        lockout = AccountLockout(redis_client=mock_redis)
        is_locked, remaining, secs = lockout.record_failed_attempt("user")
        assert is_locked is False
        assert remaining == 3  # 5 - 2
        assert secs == 0

    @patch("app.core.rate_limit.settings")
    def test_record_failed_triggers_lockout(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = -2  # No existing lockout
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [5, True]  # 5th attempt = lockout
        mock_redis.pipeline.return_value = mock_pipe

        lockout = AccountLockout(redis_client=mock_redis)
        is_locked, remaining, secs = lockout.record_failed_attempt("user")
        assert is_locked is True
        assert remaining == 0
        assert secs == 60  # BASE_LOCKOUT_SECONDS

    @patch("app.core.rate_limit.settings")
    def test_already_locked_out(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = 45  # 45 seconds remaining

        lockout = AccountLockout(redis_client=mock_redis)
        is_locked, remaining, secs = lockout.record_failed_attempt("user")
        assert is_locked is True
        assert remaining == 0
        assert secs == 45

    @patch("app.core.rate_limit.settings")
    def test_check_lockout_locked(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = 30

        lockout = AccountLockout(redis_client=mock_redis)
        is_locked, secs = lockout.check_lockout("user")
        assert is_locked is True
        assert secs == 30

    @patch("app.core.rate_limit.settings")
    def test_check_lockout_not_locked(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = -2

        lockout = AccountLockout(redis_client=mock_redis)
        is_locked, secs = lockout.check_lockout("user")
        assert is_locked is False
        assert secs == 0

    def test_clear_lockout_success(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        lockout = AccountLockout(redis_client=mock_redis)
        assert lockout.clear_lockout("user") is True
        assert mock_pipe.delete.call_count == 2  # lockout key + attempts key

    def test_get_failed_attempts_with_value(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = "3"

        lockout = AccountLockout(redis_client=mock_redis)
        assert lockout.get_failed_attempts("user") == 3

    def test_get_failed_attempts_no_value(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        lockout = AccountLockout(redis_client=mock_redis)
        assert lockout.get_failed_attempts("user") == 0


# ==================== _is_trusted_proxy ====================


class TestIsTrustedProxy:
    @patch("app.core.rate_limit.settings")
    def test_empty_proxies(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = []
        assert _is_trusted_proxy("10.0.0.1") is False

    @patch("app.core.rate_limit.settings")
    def test_none_proxies(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = None
        assert _is_trusted_proxy("10.0.0.1") is False

    @patch("app.core.rate_limit.settings")
    def test_exact_match(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["10.0.0.1"]
        assert _is_trusted_proxy("10.0.0.1") is True

    @patch("app.core.rate_limit.settings")
    def test_no_match(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["10.0.0.1"]
        assert _is_trusted_proxy("192.168.1.1") is False

    @patch("app.core.rate_limit.settings")
    def test_cidr_match(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["10.0.0.0/8"]
        assert _is_trusted_proxy("10.1.2.3") is True

    @patch("app.core.rate_limit.settings")
    def test_cidr_no_match(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["10.0.0.0/8"]
        assert _is_trusted_proxy("192.168.1.1") is False

    @patch("app.core.rate_limit.settings")
    def test_invalid_ip(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["10.0.0.1"]
        assert _is_trusted_proxy("not-an-ip") is False

    @patch("app.core.rate_limit.settings")
    def test_invalid_proxy_config(self, mock_settings):
        mock_settings.TRUSTED_PROXIES = ["invalid-proxy"]
        assert _is_trusted_proxy("10.0.0.1") is False


# ==================== get_client_ip ====================


class TestGetClientIp:
    def test_direct_ip(self):
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        with patch("app.core.rate_limit._is_trusted_proxy", return_value=False):
            assert get_client_ip(request) == "192.168.1.100"

    def test_no_client(self):
        request = MagicMock()
        request.client = None
        request.headers = {}

        assert get_client_ip(request) == "unknown"

    @patch("app.core.rate_limit._is_trusted_proxy", return_value=True)
    def test_forwarded_for_trusted(self, mock_trusted):
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}

        assert get_client_ip(request) == "203.0.113.50"

    @patch("app.core.rate_limit._is_trusted_proxy", return_value=False)
    def test_forwarded_for_untrusted(self, mock_trusted):
        """X-Forwarded-For is ignored for untrusted proxies."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.headers = {"X-Forwarded-For": "203.0.113.50"}

        assert get_client_ip(request) == "192.168.1.100"


# ==================== create_rate_limit_dependency ====================


class TestCreateRateLimitDependency:
    def test_returns_callable(self):
        dep = create_rate_limit_dependency(
            max_requests=5, window_seconds=60, key_prefix="test"
        )
        assert callable(dep)

    @pytest.mark.asyncio
    @patch("app.core.rate_limit.get_rate_limiter")
    @patch("app.core.rate_limit.get_client_ip", return_value="192.168.1.1")
    async def test_not_limited(self, mock_ip, mock_limiter):
        limiter = MagicMock()
        limiter.is_rate_limited.return_value = (
            False,
            {"remaining": 4, "limit": 5, "reset_at": 0},
        )
        mock_limiter.return_value = limiter

        dep = create_rate_limit_dependency(
            max_requests=5, window_seconds=60, key_prefix="test"
        )
        request = MagicMock()
        # Should not raise
        await dep(request)

    @pytest.mark.asyncio
    @patch("app.core.rate_limit.get_rate_limiter")
    @patch("app.core.rate_limit.get_client_ip", return_value="192.168.1.1")
    async def test_limited_raises_429(self, mock_ip, mock_limiter):
        from fastapi import HTTPException

        limiter = MagicMock()
        limiter.is_rate_limited.return_value = (
            True,
            {"remaining": 0, "limit": 5, "reset_at": 9999},
        )
        mock_limiter.return_value = limiter

        dep = create_rate_limit_dependency(
            max_requests=5, window_seconds=60, key_prefix="test"
        )
        request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await dep(request)
        assert exc_info.value.status_code == 429
