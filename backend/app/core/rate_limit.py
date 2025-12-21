"""
Rate limiting module for API endpoints.

Implements a sliding window rate limiter using Redis to prevent brute force attacks
and API abuse. Uses Redis sorted sets for efficient time-based tracking.
"""
import time
from typing import Optional

import redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Sliding window rate limiter using Redis.

    Uses Redis sorted sets with timestamps as scores to implement
    a sliding window algorithm. This provides accurate rate limiting
    without the step-function behavior of fixed windows.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the rate limiter.

        Args:
            redis_client: Optional Redis client. If not provided, creates a new one.
        """
        if redis_client is None:
            try:
                # Use authenticated Redis URL if password is configured
                redis_url = settings.redis_url_with_password
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None
        else:
            self.redis = redis_client

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, dict]:
        """
        Check if a request should be rate limited using sliding window.

        Args:
            key: Unique identifier for the rate limit (e.g., "login:192.168.1.1")
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, info_dict) where:
                - is_limited: True if rate limit exceeded
                - info_dict: Dictionary with rate limit info (remaining, reset_at, etc.)
        """
        # If Redis is not available or rate limiting is disabled, allow the request
        if self.redis is None or not settings.RATE_LIMIT_ENABLED:
            return False, {
                "remaining": max_requests,
                "limit": max_requests,
                "reset_at": int(time.time() + window_seconds),
            }

        current_time = time.time()
        window_start = current_time - window_seconds

        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in the window
            pipe.zcard(key)

            # Add current request with timestamp as score
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration on the key (cleanup)
            pipe.expire(key, window_seconds + 10)

            # Execute pipeline
            results = pipe.execute()

            # Get count before adding current request
            current_count = results[1]

            # Check if limit exceeded (count before current request)
            is_limited = current_count >= max_requests
            remaining = max(0, max_requests - current_count - 1)
            reset_at = int(current_time + window_seconds)

            info = {
                "remaining": remaining,
                "limit": max_requests,
                "reset_at": reset_at,
                "current_count": current_count + 1,
            }

            if is_limited:
                logger.warning(
                    f"Rate limit exceeded for key: {key} "
                    f"({current_count + 1}/{max_requests} in {window_seconds}s)"
                )

            return is_limited, info

        except Exception as e:
            logger.error(f"Rate limiting error for key {key}: {e}")
            # Fail open: allow request if Redis fails
            return False, {
                "remaining": max_requests,
                "limit": max_requests,
                "reset_at": int(current_time + window_seconds),
            }

    def reset(self, key: str) -> bool:
        """
        Reset rate limit for a specific key.

        Args:
            key: The rate limit key to reset

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit for key {key}: {e}")
            return False

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """
        Get remaining requests for a key without incrementing.

        Args:
            key: The rate limit key
            max_requests: Maximum allowed requests
            window_seconds: Time window in seconds

        Returns:
            Number of remaining requests
        """
        if self.redis is None or not settings.RATE_LIMIT_ENABLED:
            return max_requests

        try:
            current_time = time.time()
            window_start = current_time - window_seconds

            # Remove old entries and count current
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()

            current_count = results[1]
            return max(0, max_requests - current_count)

        except Exception as e:
            logger.error(f"Error getting remaining requests for key {key}: {e}")
            return max_requests


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def _is_trusted_proxy(ip: str) -> bool:
    """
    Check if an IP address is a trusted proxy.

    Args:
        ip: IP address to check

    Returns:
        True if IP is in the trusted proxies list
    """
    import ipaddress

    trusted_proxies = settings.TRUSTED_PROXIES
    if not trusted_proxies:
        return False

    try:
        client_ip = ipaddress.ip_address(ip)
        for proxy in trusted_proxies:
            try:
                # Check if it's a network (CIDR notation) or single IP
                if "/" in proxy:
                    network = ipaddress.ip_network(proxy, strict=False)
                    if client_ip in network:
                        return True
                else:
                    if client_ip == ipaddress.ip_address(proxy):
                        return True
            except ValueError:
                logger.warning(f"Invalid trusted proxy configuration: {proxy}")
                continue
        return False
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        return False


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Only trusts X-Forwarded-For header when the direct client IP is from
    a configured trusted proxy. This prevents rate limit bypass via header
    spoofing attacks.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Get direct client IP first
    direct_ip = request.client.host if request.client else None

    # Only trust X-Forwarded-For if request comes from a trusted proxy
    if direct_ip and _is_trusted_proxy(direct_ip):
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client IP)
            return forwarded_for.split(",")[0].strip()

    # Use direct client IP (no trusted proxy or no X-Forwarded-For)
    if direct_ip:
        return direct_ip

    # Default fallback
    return "unknown"


def create_rate_limit_dependency(
    max_requests: int,
    window_seconds: int,
    key_prefix: str,
):
    """
    Create a FastAPI dependency for rate limiting.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        key_prefix: Prefix for the rate limit key (e.g., "login", "register")

    Returns:
        FastAPI dependency function

    Example:
        ```python
        rate_limit_login = create_rate_limit_dependency(
            max_requests=5,
            window_seconds=60,
            key_prefix="login"
        )

        @router.post("/login")
        async def login(
            _rate_limit: None = Depends(rate_limit_login),
            ...
        ):
            ...
        ```
    """

    async def rate_limit_dependency(request: Request):
        """Rate limit dependency that checks and enforces limits."""
        limiter = get_rate_limiter()
        client_ip = get_client_ip(request)
        key = f"rate_limit:{key_prefix}:{client_ip}"

        is_limited, info = limiter.is_rate_limited(
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if is_limited:
            # Return 429 Too Many Requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {window_seconds} seconds.",
                    "limit": info["limit"],
                    "remaining": info["remaining"],
                    "reset_at": info["reset_at"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset_at"]),
                    "Retry-After": str(window_seconds),
                },
            )

        # Add rate limit headers to response (even when not limited)
        # Note: These will be visible in middleware/response processing
        request.state.rate_limit_info = info

    return rate_limit_dependency
