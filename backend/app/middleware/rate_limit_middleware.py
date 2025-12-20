"""
Enhanced rate limiting middleware with tiered limits and token bucket algorithm.

Implements comprehensive rate limiting with:
- Tier-based limits (free, standard, premium, admin)
- Per-endpoint rate limits
- Token bucket for burst handling
- Sliding window for sustained rate limiting
- Rate limit headers (X-RateLimit-*)
- Graceful degradation
- Bypass for internal services
"""
import logging
import time
from typing import Optional

import redis
from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.rate_limit_tiers import (
    EndpointLimit,
    RateLimitTier,
    SlidingWindowCounter,
    TokenBucket,
    get_custom_limit,
    get_endpoint_limit,
    get_tier_config,
    get_tier_for_role,
)
from app.core.security import ALGORITHM

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive API rate limiting.

    Applies both token bucket (for bursts) and sliding window (for sustained rate)
    algorithms to enforce rate limits based on user tier and endpoint.

    Features:
    - Tiered rate limits based on user role
    - Per-endpoint custom limits
    - Burst handling via token bucket
    - Sliding window for accurate rate limiting
    - Custom per-user limits
    - Bypass for internal services
    - Rate limit headers in all responses
    - Graceful degradation on Redis failure
    """

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client (creates new if not provided)
        """
        super().__init__(app)

        if redis_client is None:
            try:
                redis_url = settings.redis_url_with_password
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=False,  # Keep binary for hash operations
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self.redis.ping()
                logger.info("Rate limit middleware connected to Redis")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Rate limit middleware: Redis connection failed: {e}")
                self.redis = None
        else:
            self.redis = redis_client

    def _extract_user_info(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """
        Extract user ID and role from JWT token.

        Args:
            request: FastAPI request

        Returns:
            Tuple of (user_id, role) or (None, None) if not authenticated
        """
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Check for token in cookie
            cookie = request.cookies.get("access_token")
            if cookie and cookie.startswith("Bearer "):
                token = cookie.split(" ")[1]

        if not token:
            return None, None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            role = payload.get("role")
            return user_id, role
        except JWTError:
            return None, None

    def _get_client_identifier(self, request: Request, user_id: Optional[str]) -> str:
        """
        Get unique identifier for rate limiting.

        Uses user ID if authenticated, otherwise IP address.

        Args:
            request: FastAPI request
            user_id: User ID from token (if authenticated)

        Returns:
            Unique identifier for rate limiting
        """
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        if request.client:
            return f"ip:{request.client.host}"

        return "ip:unknown"

    def _is_internal_service(self, request: Request) -> bool:
        """
        Check if request is from internal service (bypass rate limits).

        Args:
            request: FastAPI request

        Returns:
            True if internal service
        """
        # Check for internal service header
        internal_key = request.headers.get("X-Internal-Service-Key")
        if internal_key:
            # In production, validate against stored key
            # For now, just check if header exists
            expected_key = settings.SECRET_KEY[:32]  # Use part of secret as internal key
            return internal_key == expected_key

        # Check if request is from localhost/internal network
        if request.client:
            internal_ips = ["127.0.0.1", "localhost", "::1"]
            if request.client.host in internal_ips:
                # Only bypass for specific paths (e.g., health checks, metrics)
                internal_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
                if any(request.url.path.startswith(path) for path in internal_paths):
                    return True

        return False

    def _should_skip_rate_limit(self, request: Request) -> bool:
        """
        Check if request should skip rate limiting.

        Args:
            request: FastAPI request

        Returns:
            True if should skip
        """
        # Skip if rate limiting is disabled
        if not settings.RATE_LIMIT_ENABLED:
            return True

        # Skip internal services
        if self._is_internal_service(request):
            return True

        # Skip health check endpoints
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return True

        return False

    def _get_effective_limits(
        self,
        tier: RateLimitTier,
        endpoint: str,
    ) -> tuple[int, int, int, float]:
        """
        Get effective rate limits considering tier and endpoint overrides.

        Args:
            tier: User's rate limit tier
            endpoint: Endpoint path

        Returns:
            Tuple of (requests_per_minute, requests_per_hour, burst_size, refill_rate)
        """
        # Get base tier config
        tier_config = get_tier_config(tier)

        # Check for endpoint-specific limits
        endpoint_limit = get_endpoint_limit(endpoint)

        if endpoint_limit:
            # Use endpoint limits if specified, otherwise tier defaults
            rpm = endpoint_limit.requests_per_minute or tier_config.requests_per_minute
            rph = endpoint_limit.requests_per_hour or tier_config.requests_per_hour
            burst = endpoint_limit.burst_size or tier_config.burst_size
            refill = rpm / 60.0  # Convert to per-second rate
        else:
            rpm = tier_config.requests_per_minute
            rph = tier_config.requests_per_hour
            burst = tier_config.burst_size
            refill = tier_config.burst_refill_rate

        return rpm, rph, burst, refill

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response with rate limit headers
        """
        # Check if should skip
        if self._should_skip_rate_limit(request):
            return await call_next(request)

        # Extract user information
        user_id, role = self._extract_user_info(request)
        client_id = self._get_client_identifier(request, user_id)

        # Determine tier
        tier = get_tier_for_role(role)

        # Check for custom user limits
        if user_id and self.redis:
            custom_config = get_custom_limit(user_id, self.redis)
            if custom_config:
                rpm = custom_config.requests_per_minute
                rph = custom_config.requests_per_hour
                burst = custom_config.burst_size
                refill = custom_config.burst_refill_rate
                logger.debug(f"Using custom limits for user {user_id}")
            else:
                rpm, rph, burst, refill = self._get_effective_limits(
                    tier, request.url.path
                )
        else:
            rpm, rph, burst, refill = self._get_effective_limits(tier, request.url.path)

        # Apply rate limiting
        rate_limit_info = {
            "tier": tier.value,
            "allowed": True,
            "limit_minute": rpm,
            "limit_hour": rph,
            "remaining_minute": rpm,
            "remaining_hour": rph,
            "burst_remaining": burst,
            "reset_minute": int(time.time() + 60),
            "reset_hour": int(time.time() + 3600),
        }

        if self.redis and settings.RATE_LIMIT_ENABLED:
            # Token bucket check (for bursts)
            bucket = TokenBucket(self.redis, client_id, burst, refill)
            burst_allowed, burst_info = bucket.consume(1)

            if not burst_allowed:
                logger.warning(
                    f"Rate limit (burst) exceeded for {client_id} "
                    f"on {request.method} {request.url.path}"
                )
                return self._rate_limit_response(rate_limit_info, "Burst limit exceeded")

            rate_limit_info["burst_remaining"] = int(burst_info.get("tokens", 0))

            # Sliding window check (per minute)
            window_minute = SlidingWindowCounter(
                self.redis,
                f"{client_id}:minute",
                60,
                rpm,
            )
            minute_allowed, minute_info = window_minute.increment()

            if not minute_allowed:
                logger.warning(
                    f"Rate limit (per-minute) exceeded for {client_id} "
                    f"on {request.method} {request.url.path}"
                )
                return self._rate_limit_response(
                    rate_limit_info,
                    f"Rate limit exceeded. Maximum {rpm} requests per minute.",
                )

            rate_limit_info["remaining_minute"] = minute_info.get("remaining", 0)
            rate_limit_info["reset_minute"] = minute_info.get("reset_at", 0)

            # Sliding window check (per hour)
            window_hour = SlidingWindowCounter(
                self.redis,
                f"{client_id}:hour",
                3600,
                rph,
            )
            hour_allowed, hour_info = window_hour.increment()

            if not hour_allowed:
                logger.warning(
                    f"Rate limit (per-hour) exceeded for {client_id} "
                    f"on {request.method} {request.url.path}"
                )
                return self._rate_limit_response(
                    rate_limit_info,
                    f"Rate limit exceeded. Maximum {rph} requests per hour.",
                )

            rate_limit_info["remaining_hour"] = hour_info.get("remaining", 0)
            rate_limit_info["reset_hour"] = hour_info.get("reset_at", 0)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Tier"] = rate_limit_info["tier"]
        response.headers["X-RateLimit-Limit-Minute"] = str(rate_limit_info["limit_minute"])
        response.headers["X-RateLimit-Limit-Hour"] = str(rate_limit_info["limit_hour"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            rate_limit_info["remaining_minute"]
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            rate_limit_info["remaining_hour"]
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(rate_limit_info["reset_minute"])
        response.headers["X-RateLimit-Reset-Hour"] = str(rate_limit_info["reset_hour"])
        response.headers["X-RateLimit-Burst-Remaining"] = str(
            rate_limit_info["burst_remaining"]
        )

        return response

    def _rate_limit_response(self, info: dict, message: str) -> JSONResponse:
        """
        Create rate limit exceeded response.

        Args:
            info: Rate limit information
            message: Error message

        Returns:
            429 Too Many Requests response
        """
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": message,
                "tier": info["tier"],
                "limits": {
                    "per_minute": info["limit_minute"],
                    "per_hour": info["limit_hour"],
                },
                "remaining": {
                    "per_minute": info["remaining_minute"],
                    "per_hour": info["remaining_hour"],
                    "burst": info["burst_remaining"],
                },
                "reset": {
                    "minute": info["reset_minute"],
                    "hour": info["reset_hour"],
                },
            },
            headers={
                "X-RateLimit-Tier": info["tier"],
                "X-RateLimit-Limit-Minute": str(info["limit_minute"]),
                "X-RateLimit-Limit-Hour": str(info["limit_hour"]),
                "X-RateLimit-Remaining-Minute": str(info["remaining_minute"]),
                "X-RateLimit-Remaining-Hour": str(info["remaining_hour"]),
                "X-RateLimit-Reset-Minute": str(info["reset_minute"]),
                "X-RateLimit-Reset-Hour": str(info["reset_hour"]),
                "X-RateLimit-Burst-Remaining": str(info["burst_remaining"]),
                "Retry-After": "60",  # Suggest retry after 1 minute
            },
        )
