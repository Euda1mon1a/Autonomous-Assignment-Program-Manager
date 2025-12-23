"""
Rate limiting tier definitions with token bucket and sliding window algorithms.

Implements a multi-tier rate limiting system with per-endpoint limits,
burst handling via token bucket, and graceful degradation.
"""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitTier(str, Enum):
    """
    Rate limit tiers based on user roles.

    Each tier has different rate limits for API consumption.
    Higher tiers get more requests and higher burst capacity.
    """
    FREE = "free"           # Default tier for unauthenticated requests
    STANDARD = "standard"   # Clinical staff, residents
    PREMIUM = "premium"     ***REMOVED***, coordinators
    ADMIN = "admin"         # Admin users
    INTERNAL = "internal"   # Internal services (bypass limits)


@dataclass
class RateLimitConfig:
    """
    Configuration for a specific rate limit tier.

    Uses both sliding window (for sustained rate) and token bucket (for bursts).

    Attributes:
        requests_per_minute: Sustained rate limit (sliding window)
        requests_per_hour: Hourly quota (sliding window)
        burst_size: Maximum burst requests (token bucket capacity)
        burst_refill_rate: Tokens added per second (token bucket refill)
    """
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int
    burst_refill_rate: float  # Tokens per second


@dataclass
class EndpointLimit:
    """
    Per-endpoint rate limit configuration.

    Allows customizing limits for specific endpoints (e.g., tighter limits
    for expensive operations like schedule generation).

    Attributes:
        endpoint: Endpoint path pattern (e.g., "/api/schedule/generate")
        requests_per_minute: Override for this endpoint
        requests_per_hour: Override for this endpoint
        burst_size: Override for burst capacity
    """
    endpoint: str
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    burst_size: Optional[int] = None


# Tier configurations
TIER_CONFIGS = {
    RateLimitTier.FREE: RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        burst_size=5,
        burst_refill_rate=0.16,  # ~10/min = 0.16/sec
    ),
    RateLimitTier.STANDARD: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=20,
        burst_refill_rate=1.0,  # 60/min = 1/sec
    ),
    RateLimitTier.PREMIUM: RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=5000,
        burst_size=50,
        burst_refill_rate=2.0,  # 120/min = 2/sec
    ),
    RateLimitTier.ADMIN: RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        burst_size=100,
        burst_refill_rate=5.0,  # 300/min = 5/sec
    ),
    RateLimitTier.INTERNAL: RateLimitConfig(
        requests_per_minute=999999,  # Effectively unlimited
        requests_per_hour=999999,
        burst_size=999999,
        burst_refill_rate=999999.0,
    ),
}


# Per-endpoint limits (apply to all tiers unless overridden)
ENDPOINT_LIMITS = {
    # Expensive operations get tighter limits
    "/api/schedule/generate": EndpointLimit(
        endpoint="/api/schedule/generate",
        requests_per_minute=2,
        requests_per_hour=20,
        burst_size=1,
    ),
    "/api/analytics/complex": EndpointLimit(
        endpoint="/api/analytics/complex",
        requests_per_minute=5,
        requests_per_hour=50,
        burst_size=2,
    ),
    # Authentication endpoints (already have rate limiting, but adding here for completeness)
    "/api/auth/login": EndpointLimit(
        endpoint="/api/auth/login",
        requests_per_minute=5,
        requests_per_hour=20,
        burst_size=3,
    ),
    "/api/auth/register": EndpointLimit(
        endpoint="/api/auth/register",
        requests_per_minute=3,
        requests_per_hour=10,
        burst_size=2,
    ),
}


def get_tier_for_role(role: Optional[str]) -> RateLimitTier:
    """
    Determine rate limit tier based on user role.

    Args:
        role: User role (admin, coordinator, faculty, etc.)

    Returns:
        RateLimitTier: Appropriate tier for the role
    """
    if role is None:
        return RateLimitTier.FREE

    role_to_tier = {
        "admin": RateLimitTier.ADMIN,
        "coordinator": RateLimitTier.PREMIUM,
        "faculty": RateLimitTier.PREMIUM,
        "resident": RateLimitTier.STANDARD,
        "clinical_staff": RateLimitTier.STANDARD,
        "rn": RateLimitTier.STANDARD,
        "lpn": RateLimitTier.STANDARD,
        "msa": RateLimitTier.STANDARD,
    }

    return role_to_tier.get(role.lower(), RateLimitTier.FREE)


def get_tier_config(tier: RateLimitTier) -> RateLimitConfig:
    """
    Get rate limit configuration for a tier.

    Args:
        tier: Rate limit tier

    Returns:
        RateLimitConfig: Configuration for the tier
    """
    return TIER_CONFIGS[tier]


def get_endpoint_limit(endpoint: str) -> Optional[EndpointLimit]:
    """
    Get endpoint-specific rate limit if configured.

    Args:
        endpoint: Endpoint path

    Returns:
        EndpointLimit or None if no specific limit configured
    """
    # Exact match first
    if endpoint in ENDPOINT_LIMITS:
        return ENDPOINT_LIMITS[endpoint]

    # Pattern matching (e.g., "/api/schedule/*")
    for pattern, limit in ENDPOINT_LIMITS.items():
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if endpoint.startswith(prefix):
                return limit

    return None


class TokenBucket:
    """
    Token bucket algorithm for handling burst traffic.

    Allows clients to make bursts of requests up to bucket capacity,
    with tokens refilling at a constant rate.

    Reference:
    - https://en.wikipedia.org/wiki/Token_bucket
    - Used by AWS API Gateway, Stripe API, etc.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key: str,
        capacity: int,
        refill_rate: float,
    ):
        """
        Initialize token bucket.

        Args:
            redis_client: Redis client for storing bucket state
            key: Redis key for this bucket
            capacity: Maximum tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.redis = redis_client
        self.key = f"token_bucket:{key}"
        self.capacity = capacity
        self.refill_rate = refill_rate

    def consume(self, tokens: int = 1) -> tuple[bool, dict]:
        """
        Try to consume tokens from the bucket.

        Uses Lua script for atomic operations.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (allowed, info_dict) where:
                - allowed: True if tokens were available
                - info_dict: Current bucket state
        """
        if self.redis is None:
            return True, {"tokens": self.capacity, "capacity": self.capacity}

        current_time = time.time()

        # Lua script for atomic token bucket operations
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local requested = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])

        -- Get current state (tokens, last_refill)
        local state = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(state[1]) or capacity
        local last_refill = tonumber(state[2]) or current_time

        -- Calculate refill
        local time_passed = current_time - last_refill
        local refill = time_passed * refill_rate
        tokens = math.min(capacity, tokens + refill)

        -- Try to consume
        local allowed = 0
        if tokens >= requested then
            tokens = tokens - requested
            allowed = 1
        end

        -- Save state
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
        redis.call('EXPIRE', key, 3600)  -- 1 hour TTL

        return {allowed, tokens, capacity}
        """

        try:
            result = self.redis.eval(
                lua_script,
                1,
                self.key,
                self.capacity,
                self.refill_rate,
                tokens,
                current_time,
            )

            allowed = bool(result[0])
            remaining = float(result[1])
            capacity = int(result[2])

            return allowed, {
                "tokens": remaining,
                "capacity": capacity,
                "refill_rate": self.refill_rate,
            }

        except Exception as e:
            logger.error(f"Token bucket error for key {self.key}: {e}")
            # Fail open
            return True, {"tokens": self.capacity, "capacity": self.capacity}


class SlidingWindowCounter:
    """
    Sliding window counter for accurate rate limiting.

    More accurate than fixed windows as it considers requests
    in a true sliding time window.

    Uses Redis sorted sets with timestamps as scores.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key: str,
        window_seconds: int,
        max_requests: int,
    ):
        """
        Initialize sliding window counter.

        Args:
            redis_client: Redis client
            key: Redis key for this window
            window_seconds: Window size in seconds
            max_requests: Maximum requests in window
        """
        self.redis = redis_client
        self.key = f"sliding_window:{key}"
        self.window_seconds = window_seconds
        self.max_requests = max_requests

    def increment(self) -> tuple[bool, dict]:
        """
        Increment counter and check if limit exceeded.

        Returns:
            Tuple of (allowed, info_dict)
        """
        if self.redis is None or not settings.RATE_LIMIT_ENABLED:
            return True, {
                "remaining": self.max_requests,
                "limit": self.max_requests,
            }

        current_time = time.time()
        window_start = current_time - self.window_seconds

        try:
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(self.key, 0, window_start)

            # Count current requests
            pipe.zcard(self.key)

            # Add current request
            pipe.zadd(self.key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(self.key, self.window_seconds + 10)

            results = pipe.execute()
            current_count = results[1]

            allowed = current_count < self.max_requests
            remaining = max(0, self.max_requests - current_count - 1)

            return allowed, {
                "remaining": remaining,
                "limit": self.max_requests,
                "window": self.window_seconds,
                "reset_at": int(current_time + self.window_seconds),
            }

        except Exception as e:
            logger.error(f"Sliding window error for key {self.key}: {e}")
            # Fail open
            return True, {
                "remaining": self.max_requests,
                "limit": self.max_requests,
            }


def get_custom_limit(user_id: str, redis_client: redis.Redis) -> Optional[RateLimitConfig]:
    """
    Get custom rate limit for a specific user if configured.

    Allows setting per-user overrides (e.g., for VIP users or testing).

    Args:
        user_id: User identifier
        redis_client: Redis client

    Returns:
        RateLimitConfig or None if no custom limit set
    """
    if redis_client is None:
        return None

    try:
        key = f"custom_limit:{user_id}"
        limit_data = redis_client.hgetall(key)

        if not limit_data:
            return None

        return RateLimitConfig(
            requests_per_minute=int(limit_data.get(b"requests_per_minute", 0)),
            requests_per_hour=int(limit_data.get(b"requests_per_hour", 0)),
            burst_size=int(limit_data.get(b"burst_size", 0)),
            burst_refill_rate=float(limit_data.get(b"burst_refill_rate", 0)),
        )

    except Exception as e:
        logger.error(f"Error getting custom limit for user {user_id}: {e}")
        return None


def set_custom_limit(
    user_id: str,
    redis_client: redis.Redis,
    config: RateLimitConfig,
    ttl_seconds: int = 86400,  # 24 hours
) -> bool:
    """
    Set custom rate limit for a specific user.

    Args:
        user_id: User identifier
        redis_client: Redis client
        config: Custom rate limit configuration
        ttl_seconds: Time-to-live for custom limit (default: 24 hours)

    Returns:
        True if successful
    """
    if redis_client is None:
        return False

    try:
        key = f"custom_limit:{user_id}"
        redis_client.hset(
            key,
            mapping={
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "burst_size": config.burst_size,
                "burst_refill_rate": config.burst_refill_rate,
            },
        )
        redis_client.expire(key, ttl_seconds)
        logger.info(f"Set custom rate limit for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error setting custom limit for user {user_id}: {e}")
        return False
