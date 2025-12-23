"""
Request logging middleware.

Logs incoming HTTP requests with:
- Request headers (filtered for sensitive data)
- Request body (with size limits and sensitive data masking)
- Client information (IP, user agent)
- Request ID for correlation
- User ID (if authenticated)
"""

import json
import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.middleware.logging.filters import SensitiveDataFilter
from app.middleware.logging.storage import LogStorage, get_storage_backend

logger = logging.getLogger(__name__)


class RequestLoggingConfig:
    """Configuration for request logging."""

    def __init__(
        self,
        enabled: bool = True,
        log_headers: bool = True,
        log_body: bool = True,
        max_body_size: int = 10 * 1024,  # 10 KB
        log_response: bool = True,
        max_response_size: int = 10 * 1024,  # 10 KB
        excluded_paths: set[str] | None = None,
        sample_rate: float = 1.0,  # 1.0 = log all, 0.5 = log 50%
        log_levels: dict[str, str] | None = None,
        storage_backend: LogStorage | None = None,
        sensitive_filter: SensitiveDataFilter | None = None,
    ):
        """
        Initialize request logging configuration.

        Args:
            enabled: Enable/disable request logging
            log_headers: Log request headers
            log_body: Log request body
            max_body_size: Maximum request body size to log (bytes)
            log_response: Log response data
            max_response_size: Maximum response body size to log (bytes)
            excluded_paths: Set of paths to exclude from logging
            sample_rate: Sampling rate for high-traffic endpoints (0.0-1.0)
            log_levels: Custom log levels per path prefix (e.g., {"/api/v1/health": "DEBUG"})
            storage_backend: Custom storage backend (default: in-memory)
            sensitive_filter: Custom sensitive data filter
        """
        self.enabled = enabled
        self.log_headers = log_headers
        self.log_body = log_body
        self.max_body_size = max_body_size
        self.log_response = log_response
        self.max_response_size = max_response_size
        self.excluded_paths = excluded_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        }
        self.sample_rate = sample_rate
        self.log_levels = log_levels or {}
        self.storage = storage_backend or get_storage_backend("memory")
        self.filter = sensitive_filter or SensitiveDataFilter()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request logging.

    Features:
    - Request/response body logging with size limits
    - Sensitive data masking
    - Request ID correlation
    - Sampling for high-traffic endpoints
    - Configurable log levels per endpoint
    - Multiple storage backends
    """

    def __init__(self, app, config: RequestLoggingConfig | None = None):
        """
        Initialize request logging middleware.

        Args:
            app: FastAPI application
            config: Request logging configuration
        """
        super().__init__(app)
        self.config = config or RequestLoggingConfig()
        self._request_counter = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Skip if logging disabled
        if not self.config.enabled:
            return await call_next(request)

        # Skip excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

        # Apply sampling
        if not self._should_sample():
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Get request ID (from RequestIDMiddleware or generate new)
        request_id = request.headers.get("X-Request-ID", "unknown")

        # Extract user ID if available
        user_id = self._extract_user_id(request)

        # Log request
        request_data = await self._log_request(request, request_id, user_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log response
            await self._log_response(
                request,
                response,
                request_id,
                user_id,
                duration_ms,
                request_data,
            )

            return response

        except Exception as e:
            # Log error
            duration_ms = (time.perf_counter() - start_time) * 1000
            await self._log_error(request, request_id, user_id, duration_ms, e)
            raise

    def _is_excluded(self, path: str) -> bool:
        """Check if path should be excluded from logging."""
        return any(path.startswith(excluded) for excluded in self.config.excluded_paths)

    def _should_sample(self) -> bool:
        """Determine if request should be logged based on sample rate."""
        if self.config.sample_rate >= 1.0:
            return True

        self._request_counter += 1
        return (self._request_counter % int(1 / self.config.sample_rate)) == 0

    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from request state."""
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            if hasattr(user, "id"):
                return str(user.id)
            if isinstance(user, dict) and "id" in user:
                return str(user["id"])
        return None

    async def _log_request(
        self, request: Request, request_id: str, user_id: str | None
    ) -> dict[str, Any]:
        """Log incoming request."""
        # Build log entry
        log_entry = {
            "type": "request",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id,
        }

        # Log headers (filtered)
        if self.config.log_headers:
            headers_dict = dict(request.headers)
            filtered_headers = self.config.filter.filter_headers(headers_dict)
            log_entry["headers"] = filtered_headers

        # Log body (filtered and size-limited)
        body_data = None
        if self.config.log_body and request.method in ["POST", "PUT", "PATCH"]:
            body_data = await self._read_request_body(request)
            if body_data:
                log_entry["body"] = body_data

        # Determine log level
        log_level = self._get_log_level(request.url.path)

        # Log to logger
        logger.log(
            logging.getLevelName(log_level),
            f"Incoming request: {request.method} {request.url.path}",
            extra=log_entry,
        )

        # Store in backend
        try:
            self.config.storage.store(log_entry)
        except Exception as e:
            logger.error(f"Failed to store request log: {e}")

        return log_entry

    async def _read_request_body(self, request: Request) -> dict[str, Any] | None:
        """
        Read and parse request body.

        Returns:
            Dict with body data or None if body cannot be read/parsed
        """
        try:
            # Check if body should be logged for this path
            if not self.config.filter.should_log_body(request.url.path, request.method):
                return {"_note": "Body not logged for security"}

            # Read body (this consumes the stream)
            body_bytes = await request.body()

            # Check size limit
            if len(body_bytes) > self.config.max_body_size:
                return {
                    "_note": f"Body too large ({len(body_bytes)} bytes, max {self.config.max_body_size})"
                }

            # Parse JSON if content-type is application/json
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body_json = json.loads(body_bytes)
                    # Filter sensitive data
                    filtered_body = self.config.filter.filter_dict(body_json)
                    return filtered_body
                except json.JSONDecodeError:
                    return {
                        "_note": "Invalid JSON",
                        "_raw": body_bytes[:200].decode("utf-8", errors="ignore"),
                    }
            else:
                # For non-JSON, just indicate presence
                return {
                    "_note": f"Non-JSON body ({content_type})",
                    "_size": len(body_bytes),
                }

        except Exception as e:
            logger.error(f"Error reading request body: {e}")
            return None

    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        user_id: str | None,
        duration_ms: float,
        request_data: dict[str, Any],
    ) -> None:
        """Log response."""
        log_entry = {
            "type": "response",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
        }

        # Log response headers (filtered)
        if self.config.log_headers:
            headers_dict = dict(response.headers)
            filtered_headers = self.config.filter.filter_headers(headers_dict)
            log_entry["response_headers"] = filtered_headers

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "ERROR"
        elif response.status_code >= 400:
            log_level = "WARNING"
        else:
            log_level = self._get_log_level(request.url.path)

        # Log to logger
        logger.log(
            logging.getLevelName(log_level),
            f"Response: {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
            extra=log_entry,
        )

        # Store in backend
        try:
            self.config.storage.store(log_entry)
        except Exception as e:
            logger.error(f"Failed to store response log: {e}")

    async def _log_error(
        self,
        request: Request,
        request_id: str,
        user_id: str | None,
        duration_ms: float,
        error: Exception,
    ) -> None:
        """Log request error."""
        log_entry = {
            "type": "error",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        logger.error(
            f"Request error: {request.method} {request.url.path} - {error}",
            extra=log_entry,
            exc_info=True,
        )

        # Store in backend
        try:
            self.config.storage.store(log_entry)
        except Exception as e:
            logger.error(f"Failed to store error log: {e}")

    def _get_log_level(self, path: str) -> str:
        """Get log level for path."""
        # Check custom log levels
        for prefix, level in self.config.log_levels.items():
            if path.startswith(prefix):
                return level

        # Default to INFO
        return "INFO"


# Default middleware instance
default_middleware = RequestLoggingMiddleware
