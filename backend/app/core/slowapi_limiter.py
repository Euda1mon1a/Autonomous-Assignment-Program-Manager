"""
Global rate limiting module using slowapi.

Implements rate limiting on all API endpoints using slowapi, which provides
a Redis-backed sliding window rate limiter compatible with FastAPI.
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_client_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.

    Uses X-Forwarded-For header first (for proxied requests),
    then falls back to the direct client IP address.

    Args:
        request: The FastAPI request object.

    Returns:
        Client identifier string (IP address or user ID if authenticated).
    """
    # Check for authenticated user first
    if hasattr(request.state, "user") and request.state.user:
        # Use user ID for authenticated requests (more accurate limiting)
        return f"user:{request.state.user.id}"

    # Check X-Forwarded-For for proxied requests
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client IP
    return get_remote_address(request)


def get_redis_url() -> Optional[str]:
    """
    Get Redis URL for rate limiting storage.

    Returns:
        Redis URL if available, None to use in-memory storage.
    """
    if settings.RATE_LIMIT_ENABLED:
        return settings.redis_url_with_password
    return None


# Global rate limiter instance
# Uses Redis if available, falls back to in-memory storage
limiter = Limiter(
    key_func=get_client_identifier,
    storage_uri=get_redis_url(),
    default_limits=["200/minute", "1000/hour"],
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
    strategy="fixed-window",  # Valid strategies: fixed-window, moving-window
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded exceptions.

    Returns a JSON response with rate limit details following RFC 7231.

    Args:
        request: The request that was rate limited.
        exc: The rate limit exception.

    Returns:
        JSON response with 429 status and rate limit headers.
    """
    # Extract retry-after from the exception
    retry_after = getattr(exc, "retry_after", 60)

    logger.warning(
        f"Rate limit exceeded for {get_client_identifier(request)}: "
        f"{exc.detail} on {request.method} {request.url.path}"
    )

    response = JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            "detail": str(exc.detail),
            "retry_after": retry_after,
        },
    )

    # Add standard rate limit headers
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(getattr(exc, "limit", "unknown"))
    response.headers["X-RateLimit-Remaining"] = "0"

    return response


def get_limiter() -> Limiter:
    """
    Get the global limiter instance.

    Returns:
        The configured Limiter instance.
    """
    return limiter


# Rate limit decorators for different endpoint types
# These can be used on individual routes for custom limits

def limit_auth(func: Callable) -> Callable:
    """
    Rate limit decorator for authentication endpoints.

    More restrictive limits to prevent brute force attacks.
    Uses settings-based configuration.
    """
    return limiter.limit(
        f"{settings.RATE_LIMIT_LOGIN_ATTEMPTS}/minute"
    )(func)


def limit_registration(func: Callable) -> Callable:
    """
    Rate limit decorator for registration endpoints.

    Restrictive limits to prevent automated account creation.
    """
    return limiter.limit(
        f"{settings.RATE_LIMIT_REGISTER_ATTEMPTS}/minute"
    )(func)


def limit_read(func: Callable) -> Callable:
    """
    Rate limit decorator for read-heavy endpoints.

    More permissive limits for GET requests.
    """
    return limiter.limit("100/minute")(func)


def limit_write(func: Callable) -> Callable:
    """
    Rate limit decorator for write operations.

    Moderate limits for POST/PUT/DELETE requests.
    """
    return limiter.limit("30/minute")(func)


def limit_expensive(func: Callable) -> Callable:
    """
    Rate limit decorator for computationally expensive endpoints.

    Restrictive limits for operations like schedule generation.
    """
    return limiter.limit("5/minute")(func)


def limit_export(func: Callable) -> Callable:
    """
    Rate limit decorator for export/download endpoints.

    Moderate limits for resource-intensive exports.
    """
    return limiter.limit("10/minute")(func)
