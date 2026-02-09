"""Tests for rate limit schemas (nested models, aliases, Field bounds)."""

import pytest
from pydantic import ValidationError

from app.schemas.rate_limit import (
    RateLimitStatus,
    RateLimitLimits,
    RateLimitRemaining,
    RateLimitReset,
    BurstStatus,
    RateLimitConfig,
    CustomLimitRequest,
    CustomLimitResponse,
    TierInfo,
    AllTiersResponse,
    EndpointLimitInfo,
    EndpointLimitsResponse,
    RateLimitHeaders,
    RateLimitErrorDetail,
)


class TestRateLimitLimits:
    def test_valid(self):
        r = RateLimitLimits(per_minute=60, per_hour=1000, burst_size=10)
        assert r.per_minute == 60


class TestRateLimitRemaining:
    def test_valid(self):
        r = RateLimitRemaining(per_minute=55, per_hour=990, burst=8)
        assert r.per_minute == 55


class TestRateLimitReset:
    def test_valid(self):
        r = RateLimitReset(minute=1709312400, hour=1709316000)
        assert r.minute == 1709312400


class TestBurstStatus:
    def test_valid(self):
        r = BurstStatus(tokens=8.5, capacity=10, refill_rate=1.0)
        assert r.tokens == 8.5


class TestRateLimitStatus:
    def test_valid(self):
        limits = RateLimitLimits(per_minute=60, per_hour=1000, burst_size=10)
        remaining = RateLimitRemaining(per_minute=55, per_hour=990, burst=8)
        reset = RateLimitReset(minute=1709312400, hour=1709316000)
        burst = BurstStatus(tokens=8.5, capacity=10, refill_rate=1.0)
        r = RateLimitStatus(
            tier="standard",
            limits=limits,
            remaining=remaining,
            reset=reset,
            burst=burst,
        )
        assert r.tier == "standard"
        assert r.limits.per_minute == 60


class TestRateLimitConfig:
    def test_valid(self):
        r = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10,
            burst_refill_rate=1.0,
        )
        assert r.requests_per_minute == 60

    # --- requests_per_minute gt=0 ---

    def test_requests_per_minute_zero(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=0,
                requests_per_hour=1000,
                burst_size=10,
                burst_refill_rate=1.0,
            )

    # --- requests_per_hour gt=0 ---

    def test_requests_per_hour_zero(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=0,
                burst_size=10,
                burst_refill_rate=1.0,
            )

    # --- burst_size gt=0 ---

    def test_burst_size_zero(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_size=0,
                burst_refill_rate=1.0,
            )

    # --- burst_refill_rate gt=0 ---

    def test_burst_refill_rate_zero(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_size=10,
                burst_refill_rate=0,
            )

    def test_negative_values(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=-1,
                requests_per_hour=1000,
                burst_size=10,
                burst_refill_rate=1.0,
            )


class TestCustomLimitRequest:
    def _make_config(self):
        return RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_size=20,
            burst_refill_rate=2.0,
        )

    def test_valid_default_ttl(self):
        r = CustomLimitRequest(user_id="user-1", config=self._make_config())
        assert r.ttl_seconds == 86400

    def test_custom_ttl(self):
        r = CustomLimitRequest(
            user_id="user-1", config=self._make_config(), ttl_seconds=3600
        )
        assert r.ttl_seconds == 3600

    # --- ttl_seconds gt=0 ---

    def test_ttl_zero(self):
        with pytest.raises(ValidationError):
            CustomLimitRequest(
                user_id="user-1", config=self._make_config(), ttl_seconds=0
            )


class TestCustomLimitResponse:
    def test_valid(self):
        config = RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_size=20,
            burst_refill_rate=2.0,
        )
        r = CustomLimitResponse(
            success=True,
            message="Custom limit set",
            user_id="user-1",
            config=config,
            expires_at=1709316000,
        )
        assert r.success is True


class TestTierInfo:
    def test_valid(self):
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10,
            burst_refill_rate=1.0,
        )
        r = TierInfo(tier="standard", config=config, roles=["resident", "faculty"])
        assert r.tier == "standard"
        assert len(r.roles) == 2


class TestAllTiersResponse:
    def test_valid(self):
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10,
            burst_refill_rate=1.0,
        )
        tier = TierInfo(tier="standard", config=config, roles=["resident"])
        r = AllTiersResponse(tiers=[tier])
        assert len(r.tiers) == 1


class TestEndpointLimitInfo:
    def test_with_custom_limits(self):
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            burst_size=2,
            burst_refill_rate=0.1,
        )
        r = EndpointLimitInfo(endpoint="/api/v1/schedule/generate", limits=config)
        assert r.limits.requests_per_minute == 5

    def test_tier_defaults(self):
        r = EndpointLimitInfo(endpoint="/api/v1/persons", limits=None)
        assert r.limits is None


class TestEndpointLimitsResponse:
    def test_valid(self):
        ep = EndpointLimitInfo(endpoint="/api/v1/schedule/generate", limits=None)
        r = EndpointLimitsResponse(endpoints=[ep])
        assert len(r.endpoints) == 1


class TestRateLimitHeaders:
    def test_with_aliases(self):
        r = RateLimitHeaders(
            **{
                "X-RateLimit-Tier": "standard",
                "X-RateLimit-Limit-Minute": 60,
                "X-RateLimit-Limit-Hour": 1000,
                "X-RateLimit-Remaining-Minute": 55,
                "X-RateLimit-Remaining-Hour": 990,
                "X-RateLimit-Reset-Minute": 1709312400,
                "X-RateLimit-Reset-Hour": 1709316000,
                "X-RateLimit-Burst-Remaining": 8,
            }
        )
        assert r.x_ratelimit_tier == "standard"
        assert r.x_ratelimit_limit_minute == 60

    def test_with_field_names(self):
        r = RateLimitHeaders(
            x_ratelimit_tier="premium",
            x_ratelimit_limit_minute=120,
            x_ratelimit_limit_hour=2000,
            x_ratelimit_remaining_minute=118,
            x_ratelimit_remaining_hour=1995,
            x_ratelimit_reset_minute=1709312400,
            x_ratelimit_reset_hour=1709316000,
            x_ratelimit_burst_remaining=18,
        )
        assert r.x_ratelimit_tier == "premium"
        assert r.x_ratelimit_limit_minute == 120


class TestRateLimitErrorDetail:
    def test_valid(self):
        r = RateLimitErrorDetail(
            message="Too many requests",
            tier="free",
            limits={"per_minute": 30},
            remaining={"per_minute": 0},
            reset={"minute": 1709312400},
        )
        assert r.error == "Rate limit exceeded"
        assert r.tier == "free"

    def test_custom_error(self):
        r = RateLimitErrorDetail(
            error="Burst limit exceeded",
            message="Burst capacity exhausted",
            tier="standard",
            limits={},
            remaining={},
            reset={},
        )
        assert r.error == "Burst limit exceeded"
