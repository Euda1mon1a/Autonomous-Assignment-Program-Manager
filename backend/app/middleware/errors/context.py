"""Error context collection for enhanced debugging and monitoring.

This module captures relevant request context when errors occur,
enabling better debugging, monitoring, and error grouping.
"""
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import Request
from starlette.datastructures import Headers


class ErrorContext:
    """Captures and manages error context information."""

    def __init__(self, request: Request, exc: Exception):
        """
        Initialize error context from request and exception.

        Args:
            request: FastAPI request object
            exc: Exception that occurred
        """
        self.request = request
        self.exc = exc
        self.timestamp = datetime.utcnow()

    def get_request_info(self, include_headers: bool = False) -> Dict[str, Any]:
        """
        Extract relevant request information.

        Args:
            include_headers: Whether to include request headers

        Returns:
            Dict with request information
        """
        info = {
            "method": self.request.method,
            "path": self.request.url.path,
            "query_params": dict(self.request.query_params),
        }

        # Add client information
        if self.request.client:
            info["client"] = {
                "host": self.request.client.host,
                "port": self.request.client.port,
            }

        # Add headers if requested (sanitized)
        if include_headers:
            info["headers"] = self._sanitize_headers(self.request.headers)

        # Add request ID if available
        request_id = self.request.headers.get("X-Request-ID")
        if request_id:
            info["request_id"] = request_id

        # Add user information if authenticated
        if hasattr(self.request.state, "user"):
            user = self.request.state.user
            info["user"] = {
                "id": getattr(user, "id", None),
                "role": getattr(user, "role", None),
            }

        return info

    def _sanitize_headers(self, headers: Headers) -> Dict[str, str]:
        """
        Sanitize request headers to remove sensitive information.

        Args:
            headers: Request headers

        Returns:
            Sanitized headers dict
        """
        # List of headers to exclude (case-insensitive)
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "proxy-authorization",
        }

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized

    def get_exception_info(self, include_args: bool = True) -> Dict[str, Any]:
        """
        Extract exception information.

        Args:
            include_args: Whether to include exception arguments

        Returns:
            Dict with exception information
        """
        info = {
            "type": type(self.exc).__name__,
            "module": type(self.exc).__module__,
            "message": str(self.exc),
        }

        # Add exception arguments if requested
        if include_args and hasattr(self.exc, "args"):
            # Filter out potentially sensitive args
            info["args"] = [
                self._sanitize_arg(arg) for arg in self.exc.args
            ]

        # Add custom exception attributes
        if hasattr(self.exc, "status_code"):
            info["status_code"] = self.exc.status_code

        if hasattr(self.exc, "error_code"):
            info["error_code"] = self.exc.error_code

        return info

    def _sanitize_arg(self, arg: Any) -> Any:
        """
        Sanitize exception argument to remove sensitive data.

        Args:
            arg: Exception argument

        Returns:
            Sanitized argument
        """
        # Convert to string
        arg_str = str(arg)

        # Check for sensitive patterns
        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "key",
            "credentials",
        ]

        if any(pattern in arg_str.lower() for pattern in sensitive_patterns):
            return "[REDACTED]"

        # Truncate long arguments
        if len(arg_str) > 200:
            return arg_str[:200] + "..."

        return arg_str

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get environment information.

        Returns:
            Dict with environment info
        """
        from app.core.config import get_settings

        settings = get_settings()

        return {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG,
            "timestamp": self.timestamp.isoformat() + "Z",
        }

    def to_dict(
        self,
        include_headers: bool = False,
        include_exception_args: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert error context to dictionary.

        Args:
            include_headers: Whether to include request headers
            include_exception_args: Whether to include exception args

        Returns:
            Complete error context as dict
        """
        return {
            "request": self.get_request_info(include_headers=include_headers),
            "exception": self.get_exception_info(include_args=include_exception_args),
            "environment": self.get_environment_info(),
        }


class ErrorFingerprinter:
    """
    Generates fingerprints for errors to enable grouping of similar errors.

    Fingerprints help identify recurring errors and group error occurrences
    for better monitoring and alerting.
    """

    @staticmethod
    def generate_fingerprint(
        exc: Exception,
        request_path: str,
        include_message: bool = False,
    ) -> str:
        """
        Generate a fingerprint for an error.

        The fingerprint is based on:
        - Exception type
        - Request path (normalized)
        - Optionally: exception message (for different error conditions)

        Args:
            exc: Exception
            request_path: Request path
            include_message: Whether to include exception message

        Returns:
            SHA-256 fingerprint hash
        """
        # Build fingerprint components
        components = [
            type(exc).__name__,
            ErrorFingerprinter._normalize_path(request_path),
        ]

        # Optionally include message for more specific grouping
        if include_message:
            # Normalize message to group similar errors
            normalized_message = ErrorFingerprinter._normalize_message(str(exc))
            if normalized_message:
                components.append(normalized_message)

        # Generate hash
        fingerprint_data = ":".join(components)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize request path for fingerprinting.

        Replaces IDs and UUIDs with placeholders to group similar paths.

        Args:
            path: Request path

        Returns:
            Normalized path
        """
        import re

        # Replace UUIDs with placeholder
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{uuid}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs with placeholder
        path = re.sub(r"/\d+(/|$)", r"/{id}\1", path)

        return path

    @staticmethod
    def _normalize_message(message: str) -> str:
        """
        Normalize error message for fingerprinting.

        Removes variable parts (IDs, timestamps, etc.) to group similar errors.

        Args:
            message: Error message

        Returns:
            Normalized message
        """
        import re

        # Remove UUIDs
        message = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{uuid}",
            message,
            flags=re.IGNORECASE,
        )

        # Remove numeric IDs
        message = re.sub(r"\b\d{4,}\b", "{id}", message)

        # Remove timestamps (various formats)
        message = re.sub(
            r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}",
            "{timestamp}",
            message,
        )

        # Truncate long messages
        if len(message) > 100:
            message = message[:100]

        return message


class ErrorRateLimiter:
    """
    Rate limiter for error notifications and reporting.

    Prevents notification spam when errors occur rapidly.
    """

    def __init__(self, max_errors: int = 10, window_seconds: int = 60):
        """
        Initialize error rate limiter.

        Args:
            max_errors: Maximum errors per window
            window_seconds: Time window in seconds
        """
        self.max_errors = max_errors
        self.window_seconds = window_seconds
        self._error_counts: Dict[str, list] = {}

    def should_report(self, fingerprint: str) -> bool:
        """
        Check if an error should be reported based on rate limiting.

        Args:
            fingerprint: Error fingerprint

        Returns:
            True if error should be reported, False if rate limited
        """
        now = datetime.utcnow()

        # Initialize or get existing timestamps for this fingerprint
        if fingerprint not in self._error_counts:
            self._error_counts[fingerprint] = []

        timestamps = self._error_counts[fingerprint]

        # Remove timestamps outside the window
        cutoff = now.timestamp() - self.window_seconds
        timestamps[:] = [ts for ts in timestamps if ts > cutoff]

        # Check if we're under the limit
        if len(timestamps) < self.max_errors:
            timestamps.append(now.timestamp())
            return True

        return False

    def get_error_count(self, fingerprint: str) -> int:
        """
        Get current error count for a fingerprint.

        Args:
            fingerprint: Error fingerprint

        Returns:
            Number of errors in current window
        """
        if fingerprint not in self._error_counts:
            return 0

        now = datetime.utcnow()
        cutoff = now.timestamp() - self.window_seconds

        # Clean up old timestamps
        timestamps = self._error_counts[fingerprint]
        timestamps[:] = [ts for ts in timestamps if ts > cutoff]

        return len(timestamps)


# Global rate limiter instance
_rate_limiter: Optional[ErrorRateLimiter] = None


def get_rate_limiter() -> ErrorRateLimiter:
    """
    Get the global error rate limiter.

    Returns:
        ErrorRateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = ErrorRateLimiter()
    return _rate_limiter
