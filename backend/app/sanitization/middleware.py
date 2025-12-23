"""
Sanitization middleware for automatic input sanitization in FastAPI.

This middleware automatically sanitizes request data to prevent XSS, SQL injection,
and other injection attacks. It processes:
- Query parameters
- Path parameters
- Request body (JSON)
- Headers (configurable)

The middleware can be configured with different sanitization rules and exclusions.
"""

import json
import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.sanitization.html import sanitize_html, strip_all_tags
from app.sanitization.sql import detect_sql_injection
from app.sanitization.xss import detect_xss, normalize_unicode

logger = logging.getLogger(__name__)


class SanitizationConfig:
    """
    Configuration for sanitization middleware.

    Attributes:
        enabled: Enable/disable sanitization
        strict_mode: Use strict detection (more false positives)
        normalize_unicode: Normalize Unicode characters
        max_string_length: Maximum length for string inputs
        sanitize_query_params: Sanitize URL query parameters
        sanitize_path_params: Sanitize URL path parameters
        sanitize_body: Sanitize request body
        sanitize_headers: Sanitize request headers
        allowed_html_fields: Fields that allow HTML content
        excluded_paths: Paths to exclude from sanitization
        excluded_fields: Field names to exclude from sanitization
        detect_only: Only detect and log, don't modify
    """

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = True,
        normalize_unicode: bool = True,
        max_string_length: int = 10000,
        sanitize_query_params: bool = True,
        sanitize_path_params: bool = True,
        sanitize_body: bool = True,
        sanitize_headers: bool = False,
        allowed_html_fields: set[str] | None = None,
        excluded_paths: set[str] | None = None,
        excluded_fields: set[str] | None = None,
        detect_only: bool = False,
    ):
        """
        Initialize sanitization configuration.

        Args:
            enabled: Enable/disable sanitization
            strict_mode: Use strict detection (more false positives)
            normalize_unicode: Normalize Unicode characters
            max_string_length: Maximum length for string inputs
            sanitize_query_params: Sanitize URL query parameters
            sanitize_path_params: Sanitize URL path parameters
            sanitize_body: Sanitize request body
            sanitize_headers: Sanitize request headers
            allowed_html_fields: Fields that allow HTML (description, notes, etc.)
            excluded_paths: API paths to exclude (like /docs, /openapi.json)
            excluded_fields: Field names to never sanitize (hashed_password, etc.)
            detect_only: Only detect and log threats, don't modify data
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.normalize_unicode = normalize_unicode
        self.max_string_length = max_string_length
        self.sanitize_query_params = sanitize_query_params
        self.sanitize_path_params = sanitize_path_params
        self.sanitize_body = sanitize_body
        self.sanitize_headers = sanitize_headers
        self.allowed_html_fields = allowed_html_fields or {
            "description",
            "notes",
            "comments",
            "content",
            "body",
        }
        self.excluded_paths = excluded_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/health",
        }
        self.excluded_fields = excluded_fields or {
            "password",
            "hashed_password",
            "token",
            "secret",
            "api_key",
        }
        self.detect_only = detect_only


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic input sanitization.

    This middleware intercepts requests and sanitizes input data to prevent
    injection attacks. It can be configured to sanitize different parts of
    the request and exclude certain paths or fields.

    Example:
        ```python
        from fastapi import FastAPI
        from app.sanitization.middleware import SanitizationMiddleware, SanitizationConfig

        app = FastAPI()

        config = SanitizationConfig(
            strict_mode=True,
            allowed_html_fields={'description', 'notes'}
        )
        app.add_middleware(SanitizationMiddleware, config=config)
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        config: SanitizationConfig | None = None,
    ):
        """
        Initialize sanitization middleware.

        Args:
            app: ASGI application
            config: Sanitization configuration
        """
        super().__init__(app)
        self.config = config or SanitizationConfig()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and sanitize inputs.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from the application
        """
        # Skip if disabled
        if not self.config.enabled:
            return await call_next(request)

        # Skip excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        try:
            # Sanitize request data
            await self._sanitize_request(request)

            # Continue processing
            response = await call_next(request)
            return response

        except Exception as e:
            # Log error but don't break the request
            logger.error(
                f"Error in sanitization middleware: {e}",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            # Continue without sanitization if middleware fails
            return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if path should be excluded from sanitization.

        Args:
            path: Request path

        Returns:
            True if path should be excluded
        """
        return any(path.startswith(excluded) for excluded in self.config.excluded_paths)

    def _is_excluded_field(self, field_name: str) -> bool:
        """
        Check if field should be excluded from sanitization.

        Args:
            field_name: Field name

        Returns:
            True if field should be excluded
        """
        return field_name.lower() in {f.lower() for f in self.config.excluded_fields}

    async def _sanitize_request(self, request: Request) -> None:
        """
        Sanitize all parts of the request.

        Args:
            request: FastAPI request object
        """
        # Sanitize query parameters
        if self.config.sanitize_query_params and request.query_params:
            await self._sanitize_query_params(request)

        # Sanitize path parameters
        if self.config.sanitize_path_params and hasattr(request, "path_params"):
            await self._sanitize_path_params(request)

        # Sanitize request body
        if self.config.sanitize_body and request.method in {"POST", "PUT", "PATCH"}:
            await self._sanitize_body(request)

    async def _sanitize_query_params(self, request: Request) -> None:
        """
        Sanitize URL query parameters.

        Args:
            request: FastAPI request object
        """
        try:
            sanitized_params = {}
            for key, value in request.query_params.items():
                if self._is_excluded_field(key):
                    sanitized_params[key] = value
                else:
                    sanitized_value = self._sanitize_value(key, value)
                    sanitized_params[key] = sanitized_value

            # Update query params (note: this modifies the request scope)
            request._query_params = sanitized_params
        except Exception as e:
            logger.error(f"Error sanitizing query params: {e}")

    async def _sanitize_path_params(self, request: Request) -> None:
        """
        Sanitize URL path parameters.

        Args:
            request: FastAPI request object
        """
        try:
            if hasattr(request, "path_params") and request.path_params:
                sanitized_params = {}
                for key, value in request.path_params.items():
                    if isinstance(value, str) and not self._is_excluded_field(key):
                        sanitized_value = self._sanitize_value(key, value)
                        sanitized_params[key] = sanitized_value
                    else:
                        sanitized_params[key] = value

                request.path_params = sanitized_params
        except Exception as e:
            logger.error(f"Error sanitizing path params: {e}")

    async def _sanitize_body(self, request: Request) -> None:
        """
        Sanitize request body (JSON).

        Args:
            request: FastAPI request object
        """
        try:
            # Read body
            body = await request.body()
            if not body:
                return

            # Try to parse as JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Not JSON, skip sanitization
                return

            # Sanitize data
            sanitized_data = self._sanitize_dict(data)

            # Update request body
            request._body = json.dumps(sanitized_data).encode()

        except Exception as e:
            logger.error(f"Error sanitizing request body: {e}")

    def _sanitize_dict(self, data: dict) -> dict:
        """
        Recursively sanitize dictionary data.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if self._is_excluded_field(key):
                sanitized[key] = value
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_value(key, value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(key, value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, field_name: str, data: list) -> list:
        """
        Recursively sanitize list data.

        Args:
            field_name: Name of the field containing this list
            data: List to sanitize

        Returns:
            Sanitized list
        """
        if not isinstance(data, list):
            return data

        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self._sanitize_value(field_name, item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(field_name, item))
            else:
                sanitized.append(item)

        return sanitized

    def _sanitize_value(self, field_name: str, value: str) -> str:
        """
        Sanitize a string value based on field name and configuration.

        Args:
            field_name: Name of the field
            value: Value to sanitize

        Returns:
            Sanitized value
        """
        if not isinstance(value, str) or not value:
            return value

        # Check for attacks first
        threats_detected = []

        if detect_xss(value, strict=self.config.strict_mode):
            threats_detected.append("XSS")

        if detect_sql_injection(value, strict=self.config.strict_mode):
            threats_detected.append("SQL Injection")

        # Log threats
        if threats_detected:
            logger.warning(
                f"Potential threats detected in field '{field_name}': "
                f"{', '.join(threats_detected)}",
                extra={
                    "field": field_name,
                    "threats": threats_detected,
                    "value_preview": value[:100] if len(value) > 100 else value,
                },
            )

            # If detect_only mode, just log and return original
            if self.config.detect_only:
                return value

        # Normalize Unicode
        if self.config.normalize_unicode:
            value = normalize_unicode(value)

        # Truncate if too long
        if len(value) > self.config.max_string_length:
            value = value[: self.config.max_string_length]
            logger.warning(
                f"Truncated field '{field_name}' from {len(value)} to "
                f"{self.config.max_string_length} characters"
            )

        # Sanitize based on field type
        allow_html = field_name.lower() in {
            f.lower() for f in self.config.allowed_html_fields
        }

        if allow_html:
            # Allow safe HTML
            value = sanitize_html(value, strip_tags=False)
        else:
            # Strip all HTML
            value = strip_all_tags(value)

        return value


def create_sanitization_middleware(
    strict_mode: bool = True,
    detect_only: bool = False,
    allowed_html_fields: set[str] | None = None,
) -> SanitizationMiddleware:
    """
    Factory function to create sanitization middleware with custom config.

    Args:
        strict_mode: Use strict detection mode
        detect_only: Only detect and log, don't modify data
        allowed_html_fields: Fields that allow HTML content

    Returns:
        Configured SanitizationMiddleware instance

    Example:
        ```python
        app = FastAPI()
        app.add_middleware(
            create_sanitization_middleware(
                strict_mode=True,
                allowed_html_fields={'description', 'notes'}
            )
        )
        ```
    """
    config = SanitizationConfig(
        strict_mode=strict_mode,
        detect_only=detect_only,
        allowed_html_fields=allowed_html_fields,
    )

    return lambda app: SanitizationMiddleware(app, config=config)
