"""
Rate limiting middleware using slowapi.

Provides rate limiting to protect against abuse and ensure fair resource usage.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request


# Create limiter instance with IP-based key function
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute
    headers_enabled=True,  # Include rate limit headers in response
    header_name_mapping={
        "X-RateLimit-Limit": "X-RateLimit-Limit",
        "X-RateLimit-Remaining": "X-RateLimit-Remaining",
        "X-RateLimit-Reset": "X-RateLimit-Reset",
    },
)


def get_user_identifier(request: Request) -> str:
    """
    Get rate limit key based on authenticated user or IP.

    Authenticated users get per-user limits, anonymous users get per-IP limits.
    """
    # Check for authenticated user (if auth is implemented)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Attach limiter to app state for access in route decorators
    app.state.limiter = limiter

    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add the SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)


# Decorator functions for route-specific limits
def limit_schedule_generation(request: Request) -> str:
    """Rate limit key for schedule generation (resource-intensive)."""
    return get_user_identifier(request)


def limit_auth_login(request: Request) -> str:
    """Rate limit key for login attempts (brute-force protection)."""
    return get_remote_address(request)


def limit_auth_register(request: Request) -> str:
    """Rate limit key for registration (abuse prevention)."""
    return get_remote_address(request)


def limit_export(request: Request) -> str:
    """Rate limit key for export operations."""
    return get_user_identifier(request)


# Common rate limit strings for use with @limiter.limit() decorator
RATE_LIMITS = {
    "default": "100/minute",
    "authenticated": "1000/hour",
    "schedule_generate": "10/hour",
    "auth_login": "5/minute",
    "auth_register": "3/hour",
    "export": "20/hour",
    "bulk_operations": "30/hour",
}
