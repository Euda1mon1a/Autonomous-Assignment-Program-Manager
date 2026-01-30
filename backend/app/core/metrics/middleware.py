"""
Request Metrics Middleware.

FastAPI middleware for capturing HTTP request metrics including:
- Request count by endpoint and status code
- Request latency distribution
- Active requests (in-progress)
- Request/response sizes
- Active connections
- Error rates
"""

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.metrics import get_metrics

logger = logging.getLogger(__name__)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics.

    Records:
    - Request count by method, endpoint, status code
    - Request latency histogram by method and endpoint
    - In-progress requests gauge
    - Active connections gauge
    - Request and response sizes

    Usage:
        app.add_middleware(RequestMetricsMiddleware)
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize request metrics middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.metrics = get_metrics()

        # Track active connections
        self.active_connections = 0

        logger.info("RequestMetricsMiddleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        if not self.metrics._enabled:
            return await call_next(request)

            # Extract route information
        method = request.method
        path = request.url.path

        # Normalize endpoint path (remove IDs for better aggregation)
        endpoint = self._normalize_endpoint(path)

        # Exclude metrics endpoint from being tracked (avoid recursion)
        if path == "/metrics" or path == "/health":
            return await call_next(request)

            # Track active connections and in-progress requests
        self.active_connections += 1
        self.metrics.http_active_connections.set(self.active_connections)
        self.metrics.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint,
        ).inc()

        # Measure request size
        request_size = self._get_request_size(request)
        if request_size > 0:
            self.metrics.http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint,
            ).observe(request_size)

            # Time the request
        start_time = time.perf_counter()
        exception_raised = False

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Record exception and re-raise
            exception_raised = True
            status_code = 500
            logger.error(f"Exception in {method} {endpoint}: {e}", exc_info=True)

            # Record error metrics
            self.metrics.record_error(
                error_type=type(e).__name__,
                severity="error",
                endpoint=endpoint,
            )
            self.metrics.exceptions_unhandled_total.labels(
                exception_type=type(e).__name__,
            ).inc()

            raise
        finally:
            # Calculate duration
            duration = time.perf_counter() - start_time

            # Record metrics
            self.metrics.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            self.metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            # Decrement in-progress counters
            self.metrics.http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint,
            ).dec()

            self.active_connections -= 1
            self.metrics.http_active_connections.set(self.active_connections)

            # Measure response size
        if not exception_raised:
            response_size = self._get_response_size(response)
            if response_size > 0:
                self.metrics.http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(response_size)

                # Record error metrics for 4xx and 5xx responses
            if status_code >= 400:
                severity = "error" if status_code >= 500 else "warning"
                error_type = f"http_{status_code}"
                self.metrics.record_error(
                    error_type=error_type,
                    severity=severity,
                    endpoint=endpoint,
                )

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for better metric aggregation.

        Replaces UUIDs and numeric IDs with placeholders to prevent
        metric explosion from unique paths.

        Args:
            path: Raw request path

        Returns:
            Normalized path with placeholders

        Examples:
            /api/v1/people/123 -> /api/v1/people/{id}
            /api/v1/schedule/abc-123-def -> /api/v1/schedule/{id}
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        # Replace date patterns (YYYY-MM-DD)
        path = re.sub(r"/\d{4}-\d{2}-\d{2}", "/{date}", path)

        # Limit to first 100 chars to prevent extremely long paths
        if len(path) > 100:
            path = path[:100] + "..."

        return path

    def _get_request_size(self, request: Request) -> int:
        """
        Get request body size in bytes.

        Args:
            request: HTTP request

        Returns:
            Request size in bytes (0 if unable to determine)
        """
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                return int(content_length)
        except (ValueError, TypeError):
            pass
        return 0

    def _get_response_size(self, response: Response) -> int:
        """
        Get response body size in bytes.

        Args:
            response: HTTP response

        Returns:
            Response size in bytes (0 if unable to determine)
        """
        try:
            content_length = response.headers.get("content-length")
            if content_length:
                return int(content_length)

                # Try to estimate from body if available
            if hasattr(response, "body") and response.body:
                return len(response.body)
        except (ValueError, TypeError, AttributeError):
            pass
        return 0


class DatabaseMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect database-related metrics per request.

    Tracks:
    - Database queries per request
    - Query duration distribution
    - Connection wait times

    This middleware hooks into SQLAlchemy events to track queries.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize database metrics middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.metrics = get_metrics()
        logger.info("DatabaseMetricsMiddleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track database metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        # Note: Actual query tracking would be done via SQLAlchemy events
        # This middleware primarily exists as a hook point for future enhancements

        response = await call_next(request)
        return response


class CacheMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track cache performance metrics.

    Records:
    - Cache hit/miss ratio
    - Cache operation latencies
    - Cache size

    This middleware can be used to track Redis or in-memory cache performance.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize cache metrics middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.metrics = get_metrics()
        logger.info("CacheMetricsMiddleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track cache metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        # Cache metrics are typically tracked in the cache service layer
        # This middleware exists as a placeholder for future enhancements

        response = await call_next(request)
        return response
