"""Tests for rate limiting tier definitions and algorithms."""

from app.core.rate_limit_tiers import (
    ENDPOINT_LIMITS,
    TIER_CONFIGS,
    EndpointLimit,
    RateLimitConfig,
    RateLimitTier,
    TokenBucket,
    get_custom_limit,
    get_endpoint_limit,
    get_tier_config,
    get_tier_for_role,
    set_custom_limit,
)


# ==================== RateLimitTier Enum ====================


class TestRateLimitTier:
    def test_free(self):
        assert RateLimitTier.FREE == "free"

    def test_standard(self):
        assert RateLimitTier.STANDARD == "standard"

    def test_premium(self):
        assert RateLimitTier.PREMIUM == "premium"

    def test_admin(self):
        assert RateLimitTier.ADMIN == "admin"

    def test_internal(self):
        assert RateLimitTier.INTERNAL == "internal"

    def test_is_str(self):
        assert isinstance(RateLimitTier.FREE, str)


# ==================== RateLimitConfig Dataclass ====================


class TestRateLimitConfig:
    def test_fields(self):
        c = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=20,
            burst_refill_rate=1.0,
        )
        assert c.requests_per_minute == 60
        assert c.requests_per_hour == 1000
        assert c.burst_size == 20
        assert c.burst_refill_rate == 1.0


# ==================== EndpointLimit Dataclass ====================


class TestEndpointLimit:
    def test_required_fields(self):
        e = EndpointLimit(endpoint="/api/test")
        assert e.endpoint == "/api/test"

    def test_defaults_none(self):
        e = EndpointLimit(endpoint="/api/test")
        assert e.requests_per_minute is None
        assert e.requests_per_hour is None
        assert e.burst_size is None

    def test_custom_values(self):
        e = EndpointLimit(
            endpoint="/api/test",
            requests_per_minute=5,
            requests_per_hour=50,
            burst_size=2,
        )
        assert e.requests_per_minute == 5
        assert e.requests_per_hour == 50
        assert e.burst_size == 2


# ==================== TIER_CONFIGS ====================


class TestTierConfigs:
    def test_all_tiers_configured(self):
        for tier in RateLimitTier:
            assert tier in TIER_CONFIGS, f"{tier.name} missing config"

    def test_free_lowest_limits(self):
        free = TIER_CONFIGS[RateLimitTier.FREE]
        standard = TIER_CONFIGS[RateLimitTier.STANDARD]
        assert free.requests_per_minute < standard.requests_per_minute
        assert free.requests_per_hour < standard.requests_per_hour

    def test_admin_higher_than_standard(self):
        admin = TIER_CONFIGS[RateLimitTier.ADMIN]
        standard = TIER_CONFIGS[RateLimitTier.STANDARD]
        assert admin.requests_per_minute > standard.requests_per_minute

    def test_internal_effectively_unlimited(self):
        internal = TIER_CONFIGS[RateLimitTier.INTERNAL]
        assert internal.requests_per_minute >= 999999

    def test_tier_ordering(self):
        """Limits increase: FREE < STANDARD < PREMIUM < ADMIN < INTERNAL."""
        tiers = [
            RateLimitTier.FREE,
            RateLimitTier.STANDARD,
            RateLimitTier.PREMIUM,
            RateLimitTier.ADMIN,
            RateLimitTier.INTERNAL,
        ]
        for i in range(len(tiers) - 1):
            lower = TIER_CONFIGS[tiers[i]]
            higher = TIER_CONFIGS[tiers[i + 1]]
            assert lower.requests_per_minute <= higher.requests_per_minute


# ==================== ENDPOINT_LIMITS ====================


class TestEndpointLimits:
    def test_schedule_generate_restricted(self):
        limit = ENDPOINT_LIMITS["/api/schedule/generate"]
        assert limit.requests_per_minute == 2
        assert limit.burst_size == 1

    def test_auth_login_restricted(self):
        limit = ENDPOINT_LIMITS["/api/auth/login"]
        assert limit.requests_per_minute == 5

    def test_auth_register_restricted(self):
        limit = ENDPOINT_LIMITS["/api/auth/register"]
        assert limit.requests_per_minute == 3


# ==================== get_tier_for_role ====================


class TestGetTierForRole:
    def test_none_role(self):
        assert get_tier_for_role(None) == RateLimitTier.FREE

    def test_admin(self):
        assert get_tier_for_role("admin") == RateLimitTier.ADMIN

    def test_coordinator(self):
        assert get_tier_for_role("coordinator") == RateLimitTier.PREMIUM

    def test_faculty(self):
        assert get_tier_for_role("faculty") == RateLimitTier.PREMIUM

    def test_resident(self):
        assert get_tier_for_role("resident") == RateLimitTier.STANDARD

    def test_clinical_staff(self):
        assert get_tier_for_role("clinical_staff") == RateLimitTier.STANDARD

    def test_rn(self):
        assert get_tier_for_role("rn") == RateLimitTier.STANDARD

    def test_lpn(self):
        assert get_tier_for_role("lpn") == RateLimitTier.STANDARD

    def test_msa(self):
        assert get_tier_for_role("msa") == RateLimitTier.STANDARD

    def test_unknown_role(self):
        assert get_tier_for_role("unknown") == RateLimitTier.FREE

    def test_case_insensitive(self):
        assert get_tier_for_role("ADMIN") == RateLimitTier.ADMIN
        assert get_tier_for_role("Admin") == RateLimitTier.ADMIN


# ==================== get_tier_config ====================


class TestGetTierConfig:
    def test_returns_config(self):
        config = get_tier_config(RateLimitTier.STANDARD)
        assert isinstance(config, RateLimitConfig)
        assert config.requests_per_minute == 60

    def test_all_tiers(self):
        for tier in RateLimitTier:
            config = get_tier_config(tier)
            assert isinstance(config, RateLimitConfig)


# ==================== get_endpoint_limit ====================


class TestGetEndpointLimit:
    def test_exact_match(self):
        result = get_endpoint_limit("/api/schedule/generate")
        assert result is not None
        assert result.requests_per_minute == 2

    def test_no_match(self):
        result = get_endpoint_limit("/api/unknown/endpoint")
        assert result is None

    def test_auth_login_match(self):
        result = get_endpoint_limit("/api/auth/login")
        assert result is not None
        assert result.requests_per_minute == 5


# ==================== TokenBucket (no Redis) ====================


class TestTokenBucketNoRedis:
    def test_consume_without_redis_always_allowed(self):
        bucket = TokenBucket(
            redis_client=None,
            key="test",
            capacity=10,
            refill_rate=1.0,
        )
        allowed, info = bucket.consume(1)
        assert allowed is True
        assert info["tokens"] == 10
        assert info["capacity"] == 10

    def test_key_prefix(self):
        bucket = TokenBucket(
            redis_client=None,
            key="user:123",
            capacity=10,
            refill_rate=1.0,
        )
        assert bucket.key == "token_bucket:user:123"


# ==================== Custom limits (no Redis) ====================


class TestCustomLimitsNoRedis:
    def test_get_custom_limit_no_redis(self):
        result = get_custom_limit("user123", None)
        assert result is None

    def test_set_custom_limit_no_redis(self):
        config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_size=50,
            burst_refill_rate=2.0,
        )
        result = set_custom_limit("user123", None, config)
        assert result is False
