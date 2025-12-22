"""
Rate limit status and management API endpoints.

Provides endpoints for:
- Viewing current rate limit status
- Viewing tier configurations
- Setting custom per-user limits (admin only)
- Viewing endpoint-specific limits
"""
import logging
import time

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit_tiers import (
    ENDPOINT_LIMITS,
    TIER_CONFIGS,
    RateLimitConfig,
    RateLimitTier,
    SlidingWindowCounter,
    TokenBucket,
    get_custom_limit,
    get_tier_config,
    get_tier_for_role,
    set_custom_limit,
)
from app.core.security import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.rate_limit import (
    AllTiersResponse,
    BurstStatus,
    CustomLimitRequest,
    CustomLimitResponse,
    EndpointLimitInfo,
    EndpointLimitsResponse,
    RateLimitLimits,
    RateLimitRemaining,
    RateLimitReset,
    RateLimitStatus,
    TierInfo,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def get_redis_client() -> redis.Redis:
    """
    Get Redis client for rate limiting.

    Returns:
        Redis client instance

    Raises:
        HTTPException: If Redis connection fails
    """
    try:
        redis_url = settings.redis_url_with_password
        client = redis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        client.ping()
        return client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limit service temporarily unavailable",
        )


@router.get("/status", response_model=RateLimitStatus)
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Get current rate limit status for the authenticated user.

    Returns remaining requests, limits, and reset times for the current user's tier.

    **Response Headers:**
    - X-RateLimit-Tier: Current tier
    - X-RateLimit-Limit-Minute: Requests per minute limit
    - X-RateLimit-Remaining-Minute: Remaining requests this minute
    - (and more - see RateLimitHeaders schema)

    **Example Response:**
    ```json
    {
      "tier": "premium",
      "limits": {
        "per_minute": 120,
        "per_hour": 5000,
        "burst_size": 50
      },
      "remaining": {
        "per_minute": 118,
        "per_hour": 4997,
        "burst": 49
      },
      "reset": {
        "minute": 1703001600,
        "hour": 1703004000
      },
      "burst": {
        "tokens": 49.5,
        "capacity": 50,
        "refill_rate": 2.0
      }
    }
    ```
    """
    # Determine tier
    tier = get_tier_for_role(current_user.role)

    # Check for custom limits
    custom_config = get_custom_limit(str(current_user.id), redis_client)
    if custom_config:
        config = custom_config
        logger.debug(f"Using custom limits for user {current_user.id}")
    else:
        config = get_tier_config(tier)

    client_id = f"user:{current_user.id}"

    # Get current status from Redis
    current_time = time.time()

    # Token bucket status
    bucket = TokenBucket(
        redis_client,
        client_id,
        config.burst_size,
        config.burst_refill_rate,
    )
    # Don't consume, just check status
    try:
        bucket_key = f"token_bucket:{client_id}"
        bucket_data = redis_client.hgetall(bucket_key)

        if bucket_data:
            tokens = float(bucket_data.get(b"tokens", config.burst_size))
            last_refill = float(bucket_data.get(b"last_refill", current_time))

            # Calculate refill
            time_passed = current_time - last_refill
            refill = time_passed * config.burst_refill_rate
            tokens = min(config.burst_size, tokens + refill)
        else:
            tokens = float(config.burst_size)

        burst_status = BurstStatus(
            tokens=tokens,
            capacity=config.burst_size,
            refill_rate=config.burst_refill_rate,
        )
    except Exception as e:
        logger.error(f"Error getting burst status: {e}")
        burst_status = BurstStatus(
            tokens=float(config.burst_size),
            capacity=config.burst_size,
            refill_rate=config.burst_refill_rate,
        )

    # Sliding window status (per minute)
    try:
        window_key = f"sliding_window:{client_id}:minute"
        window_start = current_time - 60
        redis_client.zremrangebyscore(window_key, 0, window_start)
        minute_count = redis_client.zcard(window_key)
        remaining_minute = max(0, config.requests_per_minute - minute_count)
    except Exception as e:
        logger.error(f"Error getting minute window status: {e}")
        remaining_minute = config.requests_per_minute

    # Sliding window status (per hour)
    try:
        window_key = f"sliding_window:{client_id}:hour"
        window_start = current_time - 3600
        redis_client.zremrangebyscore(window_key, 0, window_start)
        hour_count = redis_client.zcard(window_key)
        remaining_hour = max(0, config.requests_per_hour - hour_count)
    except Exception as e:
        logger.error(f"Error getting hour window status: {e}")
        remaining_hour = config.requests_per_hour

    return RateLimitStatus(
        tier=tier.value,
        limits=RateLimitLimits(
            per_minute=config.requests_per_minute,
            per_hour=config.requests_per_hour,
            burst_size=config.burst_size,
        ),
        remaining=RateLimitRemaining(
            per_minute=remaining_minute,
            per_hour=remaining_hour,
            burst=int(burst_status.tokens),
        ),
        reset=RateLimitReset(
            minute=int(current_time + 60),
            hour=int(current_time + 3600),
        ),
        burst=burst_status,
    )


@router.get("/tiers", response_model=AllTiersResponse)
async def get_all_tiers(
    current_user: User = Depends(get_current_user),
):
    """
    Get information about all rate limit tiers.

    Shows the configuration for each tier and which user roles get each tier.

    **Example Response:**
    ```json
    {
      "tiers": [
        {
          "tier": "free",
          "config": {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_size": 5,
            "burst_refill_rate": 0.16
          },
          "roles": ["unauthenticated"]
        },
        {
          "tier": "standard",
          "config": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_size": 20,
            "burst_refill_rate": 1.0
          },
          "roles": ["resident", "clinical_staff", "rn", "lpn", "msa"]
        },
        ...
      ]
    }
    ```
    """
    tier_mapping = {
        RateLimitTier.FREE: ["unauthenticated"],
        RateLimitTier.STANDARD: ["resident", "clinical_staff", "rn", "lpn", "msa"],
        RateLimitTier.PREMIUM: ["faculty", "coordinator"],
        RateLimitTier.ADMIN: ["admin"],
        RateLimitTier.INTERNAL: ["internal_service"],
    }

    tiers = []
    for tier, config in TIER_CONFIGS.items():
        tiers.append(
            TierInfo(
                tier=tier.value,
                config=RateLimitConfig(
                    requests_per_minute=config.requests_per_minute,
                    requests_per_hour=config.requests_per_hour,
                    burst_size=config.burst_size,
                    burst_refill_rate=config.burst_refill_rate,
                ),
                roles=tier_mapping.get(tier, []),
            )
        )

    return AllTiersResponse(tiers=tiers)


@router.get("/endpoints", response_model=EndpointLimitsResponse)
async def get_endpoint_limits(
    current_user: User = Depends(get_current_user),
):
    """
    Get endpoint-specific rate limits.

    Some endpoints have custom rate limits that override tier defaults.
    This endpoint lists all such endpoints.

    **Example Response:**
    ```json
    {
      "endpoints": [
        {
          "endpoint": "/api/schedule/generate",
          "limits": {
            "requests_per_minute": 2,
            "requests_per_hour": 20,
            "burst_size": 1,
            "burst_refill_rate": 0.033
          }
        },
        {
          "endpoint": "/api/analytics/complex",
          "limits": {
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "burst_size": 2,
            "burst_refill_rate": 0.083
          }
        }
      ]
    }
    ```
    """
    endpoints = []

    for endpoint_path, limit in ENDPOINT_LIMITS.items():
        config = None
        if (
            limit.requests_per_minute
            or limit.requests_per_hour
            or limit.burst_size
        ):
            refill_rate = (
                limit.requests_per_minute / 60.0
                if limit.requests_per_minute
                else 0.0
            )
            config = RateLimitConfig(
                requests_per_minute=limit.requests_per_minute or 0,
                requests_per_hour=limit.requests_per_hour or 0,
                burst_size=limit.burst_size or 0,
                burst_refill_rate=refill_rate,
            )

        endpoints.append(
            EndpointLimitInfo(
                endpoint=endpoint_path,
                limits=config,
            )
        )

    return EndpointLimitsResponse(endpoints=endpoints)


@router.post("/custom", response_model=CustomLimitResponse)
async def set_custom_user_limit(
    request: CustomLimitRequest,
    current_user: User = Depends(get_admin_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Set custom rate limit for a specific user (admin only).

    Allows administrators to set per-user rate limit overrides,
    useful for VIP users, testing, or temporary increases.

    **Requires:** Admin role

    **Request Body:**
    ```json
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "config": {
        "requests_per_minute": 200,
        "requests_per_hour": 10000,
        "burst_size": 100,
        "burst_refill_rate": 3.33
      },
      "ttl_seconds": 86400
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "message": "Custom rate limit set successfully",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "config": { ... },
      "expires_at": 1703088000
    }
    ```
    """
    config = RateLimitConfig(
        requests_per_minute=request.config.requests_per_minute,
        requests_per_hour=request.config.requests_per_hour,
        burst_size=request.config.burst_size,
        burst_refill_rate=request.config.burst_refill_rate,
    )

    success = set_custom_limit(
        request.user_id,
        redis_client,
        config,
        request.ttl_seconds,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set custom rate limit",
        )

    expires_at = int(time.time() + request.ttl_seconds)

    logger.info(
        f"Admin {current_user.username} set custom rate limit for user {request.user_id}"
    )

    return CustomLimitResponse(
        success=True,
        message="Custom rate limit set successfully",
        user_id=request.user_id,
        config=config,
        expires_at=expires_at,
    )


@router.delete("/custom/{user_id}")
async def remove_custom_user_limit(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Remove custom rate limit for a user (admin only).

    Reverts user back to their tier's default limits.

    **Requires:** Admin role

    **Response:**
    ```json
    {
      "success": true,
      "message": "Custom rate limit removed",
      "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    """
    try:
        key = f"custom_limit:{user_id}"
        redis_client.delete(key)

        logger.info(
            f"Admin {current_user.username} removed custom rate limit for user {user_id}"
        )

        return {
            "success": True,
            "message": "Custom rate limit removed",
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error removing custom limit for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove custom rate limit",
        )
