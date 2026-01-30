"""
Timing middleware for request duration tracking.

Features:
- Request timing with high precision
- Performance metrics collection
- Slow request detection and logging
- Integration with performance logger
"""

import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging.performance_logger import get_performance_logger
from loguru import logger


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking request timing and performance metrics.

    Features:
    - High-precision timing using perf_counter
    - Automatic slow request detection
    - Performance metrics integration
    - Configurable thresholds per endpoint
    """

    def __init__(
        self,
        app,
        slow_threshold_ms: float = 1000.0,
        warn_threshold_ms: float = 5000.0,
        enable_performance_logger: bool = True,
        excluded_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize timing middleware.

        Args:
            app: FastAPI application
            slow_threshold_ms: Threshold for logging slow requests (ms)
            warn_threshold_ms: Threshold for warning about very slow requests (ms)
            enable_performance_logger: Enable performance logger integration
            excluded_paths: Paths to exclude from timing (e.g., /health, /metrics)
        """
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
        self.warn_threshold_ms = warn_threshold_ms
        self.enable_performance_logger = enable_performance_logger
        self.excluded_paths = excluded_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        }
        self.perf_logger = (
            get_performance_logger() if enable_performance_logger else None
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track timing.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response with timing header
        """
        # Skip excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

            # Start timing
        start_time = time.perf_counter()
        start_timestamp = time.time()

        # Get request ID for correlation
        request_id = request.headers.get("X-Request-ID", "unknown")

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add timing header to response
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Log timing information
            self._log_timing(
                request=request,
                response=response,
                duration_ms=duration_ms,
                request_id=request_id,
            )

            # Log to performance logger
            if self.perf_logger:
                self.perf_logger.log_api_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                )

            return response

        except Exception as e:
            # Log error with timing
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                f"Request failed after {duration_ms:.2f}ms: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
                error=str(e),
            )

            raise

    def _is_excluded(self, path: str) -> bool:
        """Check if path should be excluded from timing."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def _log_timing(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str,
    ) -> None:
        """
        Log timing information at appropriate level.

        Args:
            request: HTTP request
            response: HTTP response
            duration_ms: Request duration in milliseconds
            request_id: Request correlation ID
        """
        # Build log context
        log_context = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "request_id": request_id,
        }

        # Log at appropriate level based on duration and status
        if response.status_code >= 500:
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"-> {response.status_code} ({duration_ms:.2f}ms)",
                **log_context,
            )
        elif duration_ms > self.warn_threshold_ms:
            logger.warning(
                f"Very slow request: {request.method} {request.url.path} "
                f"({duration_ms:.2f}ms)",
                **log_context,
            )
        elif duration_ms > self.slow_threshold_ms:
            logger.info(
                f"Slow request: {request.method} {request.url.path} "
                f"({duration_ms:.2f}ms)",
                **log_context,
            )
        else:
            logger.debug(
                f"Request completed: {request.method} {request.url.path} "
                f"({duration_ms:.2f}ms)",
                **log_context,
            )


class DetailedTimingMiddleware(TimingMiddleware):
    """
    Enhanced timing middleware with detailed performance breakdown.

    Tracks:
    - Total request time
    - Time to first byte (TTFB)
    - Response generation time
    - Additional performance metrics
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with detailed timing.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response with detailed timing headers
        """
        # Skip excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

            # Timing markers
        request_start = time.perf_counter()

        # Process request
        try:
            response = await call_next(request)

            # Calculate timings
            total_time = (time.perf_counter() - request_start) * 1000

            # Add detailed timing headers
            response.headers["X-Response-Time"] = f"{total_time:.2f}ms"
            response.headers["X-Request-Start"] = f"{request_start}"

            # Log detailed timing
            self._log_detailed_timing(
                request=request,
                response=response,
                total_time=total_time,
            )

            return response

        except Exception as e:
            total_time = (time.perf_counter() - request_start) * 1000

            logger.error(
                f"Request failed after {total_time:.2f}ms",
                method=request.method,
                path=request.url.path,
                total_time=round(total_time, 2),
                error=str(e),
            )

            raise

    def _log_detailed_timing(
        self,
        request: Request,
        response: Response,
        total_time: float,
    ) -> None:
        """
        Log detailed timing breakdown.

        Args:
            request: HTTP request
            response: HTTP response
            total_time: Total request time
        """
        logger.debug(
            f"Detailed timing: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            total_time_ms=round(total_time, 2),
        )


def create_timing_middleware(
    slow_threshold_ms: float = 1000.0,
    warn_threshold_ms: float = 5000.0,
    enable_performance_logger: bool = True,
) -> type[TimingMiddleware]:
    """
    Create timing middleware factory.

    Args:
        slow_threshold_ms: Threshold for slow request logging
        warn_threshold_ms: Threshold for warning logging
        enable_performance_logger: Enable performance logger

    Returns:
        TimingMiddleware class configured with parameters
    """

    class ConfiguredTimingMiddleware(TimingMiddleware):
        def __init__(self, app) -> None:
            super().__init__(
                app,
                slow_threshold_ms=slow_threshold_ms,
                warn_threshold_ms=warn_threshold_ms,
                enable_performance_logger=enable_performance_logger,
            )

    return ConfiguredTimingMiddleware
