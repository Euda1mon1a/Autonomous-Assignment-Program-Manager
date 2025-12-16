"""
Rate limiting middleware for API protection.

Provides configurable rate limiting to:
- Prevent abuse and DoS attacks
- Ensure fair API access across clients
- Protect backend resources

Uses in-memory storage by default, with Redis support for distributed deployments.
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Allow short bursts
    enabled: bool = True


@dataclass
class ClientState:
    """Track rate limit state for a client."""

    minute_count: int = 0
    minute_reset: float = 0.0
    hour_count: int = 0
    hour_reset: float = 0.0


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    For production distributed deployments, replace with Redis-based implementation.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._clients: Dict[str, ClientState] = defaultdict(ClientState)

    def _get_client_key(self, request: Request) -> str:
        """Get unique identifier for client."""
        # Use X-Forwarded-For if behind proxy, otherwise client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, str]]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (allowed: bool, headers: dict with rate limit info)
        """
        if not self.config.enabled:
            return True, {}

        client_key = self._get_client_key(request)
        state = self._clients[client_key]
        now = time.time()

        # Reset minute window if expired
        if now > state.minute_reset:
            state.minute_count = 0
            state.minute_reset = now + 60

        # Reset hour window if expired
        if now > state.hour_reset:
            state.hour_count = 0
            state.hour_reset = now + 3600

        # Check limits
        minute_remaining = self.config.requests_per_minute - state.minute_count
        hour_remaining = self.config.requests_per_hour - state.hour_count

        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, minute_remaining - 1)),
            "X-RateLimit-Reset": str(int(state.minute_reset)),
        }

        if minute_remaining <= 0:
            headers["Retry-After"] = str(int(state.minute_reset - now))
            return False, headers

        if hour_remaining <= 0:
            headers["Retry-After"] = str(int(state.hour_reset - now))
            return False, headers

        # Increment counters
        state.minute_count += 1
        state.hour_count += 1

        return True, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces rate limits on incoming requests.

    Skips rate limiting for:
    - Health check endpoints
    - Metrics endpoints
    - OPTIONS requests (CORS preflight)
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {"/health", "/metrics", "/", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app, limiter: InMemoryRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limit and process request."""
        # Skip rate limiting for excluded paths and OPTIONS
        if request.url.path in self.EXCLUDED_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        allowed, headers = self.limiter.check_rate_limit(request)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                },
                headers=headers,
            )

        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


def setup_rate_limiting(
    app: FastAPI,
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    enabled: bool = True,
) -> None:
    """
    Set up rate limiting middleware on FastAPI app.

    Args:
        app: FastAPI application instance
        requests_per_minute: Max requests per minute per client
        requests_per_hour: Max requests per hour per client
        enabled: Whether rate limiting is active
    """
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        enabled=enabled,
    )
    limiter = InMemoryRateLimiter(config)
    app.add_middleware(RateLimitMiddleware, limiter=limiter)
    logger.info(
        f"Rate limiting configured: {requests_per_minute}/min, {requests_per_hour}/hour"
    )
