"""
Timeout middleware for FastAPI.

Provides global request timeout handling with:
- Configurable default timeout
- Per-endpoint timeout override
- Timeout headers in response
- Graceful cancellation
- Timeout metrics
"""

import asyncio
import builtins
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.timeout.handler import TimeoutError, timeout_ctx, timeout_start_ctx

logger = logging.getLogger(__name__)

# Try to import Prometheus metrics
try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True

    # Timeout metrics
    timeout_requests = Counter(
        "http_request_timeouts_total",
        "Total HTTP requests that timed out",
        ["method", "path", "timeout_type"],
    )

    timeout_duration = Histogram(
        "http_request_timeout_duration_seconds",
        "Duration of requests that timed out",
        ["method", "path"],
        buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    )

except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.debug("prometheus_client not available - timeout metrics disabled")


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware for global request timeout handling.

    Features:
    - Sets default timeout for all requests
    - Supports per-endpoint timeout override via route metadata
    - Adds timeout headers to responses (X-Timeout-Limit, X-Timeout-Elapsed)
    - Gracefully handles timeout cancellation
    - Records timeout metrics

    Configuration:
        app.add_middleware(
            TimeoutMiddleware,
            default_timeout=30.0,  # 30 second default
            timeout_header=True,   # Include timeout headers
        )

    Per-endpoint override:
        @app.get("/long-operation", timeout=60.0)
        async def long_operation():
            pass
    """

    def __init__(
        self,
        app,
        default_timeout: float = 30.0,
        timeout_header: bool = True,
        exclude_paths: list[str] | None = None,
    ) -> None:
        """
        Initialize timeout middleware.

        Args:
            app: FastAPI application
            default_timeout: Default timeout in seconds (default: 30.0)
            timeout_header: Whether to add timeout headers to responses
            exclude_paths: Paths to exclude from timeout (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.default_timeout = default_timeout
        self.timeout_header = timeout_header
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout handling.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response: HTTP response with timeout headers
        """
        # Skip timeout for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

            # Get endpoint-specific timeout if configured
        timeout = self._get_endpoint_timeout(request) or self.default_timeout

        start_time = time.monotonic()
        token_remaining = timeout_ctx.set(timeout)
        token_start = timeout_start_ctx.set(start_time)

        try:
            # Execute request with timeout
            response = await asyncio.wait_for(call_next(request), timeout=timeout)

            # Add timeout headers if enabled
            if self.timeout_header:
                elapsed = time.monotonic() - start_time
                response.headers["X-Timeout-Limit"] = str(timeout)
                response.headers["X-Timeout-Elapsed"] = f"{elapsed:.3f}"
                remaining = max(0, timeout - elapsed)
                response.headers["X-Timeout-Remaining"] = f"{remaining:.3f}"

            return response

        except builtins.TimeoutError:
            elapsed = time.monotonic() - start_time

            # Log timeout
            logger.warning(
                f"Request timeout: {request.method} {request.url.path} "
                f"(timeout: {timeout}s, elapsed: {elapsed:.2f}s)"
            )

            # Record metrics
            if PROMETHEUS_AVAILABLE:
                timeout_requests.labels(
                    method=request.method, path=request.url.path, timeout_type="global"
                ).inc()
                timeout_duration.labels(
                    method=request.method, path=request.url.path
                ).observe(elapsed)

                # Return timeout error response
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request exceeded timeout of {timeout}s",
                    "timeout": timeout,
                    "elapsed": round(elapsed, 3),
                },
                headers={
                    "X-Timeout-Limit": str(timeout),
                    "X-Timeout-Elapsed": f"{elapsed:.3f}",
                },
            )

        except TimeoutError as e:
            # Handle TimeoutError from handler
            elapsed = time.monotonic() - start_time

            logger.warning(
                f"Request timeout (handler): {request.method} {request.url.path} "
                f"(timeout: {e.timeout}s, elapsed: {elapsed:.2f}s)"
            )

            # Record metrics
            if PROMETHEUS_AVAILABLE:
                timeout_requests.labels(
                    method=request.method, path=request.url.path, timeout_type="handler"
                ).inc()
                timeout_duration.labels(
                    method=request.method, path=request.url.path
                ).observe(elapsed)

            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=504,
                content={
                    "detail": e.message,
                    "timeout": e.timeout,
                    "elapsed": round(elapsed, 3),
                },
                headers={
                    "X-Timeout-Limit": str(e.timeout),
                    "X-Timeout-Elapsed": f"{elapsed:.3f}",
                },
            )

        finally:
            # Reset context variables
            timeout_ctx.reset(token_remaining)
            timeout_start_ctx.reset(token_start)

    def _get_endpoint_timeout(self, request: Request) -> float | None:
        """
        Get endpoint-specific timeout from route metadata.

        Args:
            request: HTTP request

        Returns:
            Optional[float]: Endpoint timeout in seconds, or None
        """
        # Check if route has timeout metadata
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "timeout"):
                return route.timeout

        return None
