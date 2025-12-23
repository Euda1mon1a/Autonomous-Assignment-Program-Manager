"""Global error handler middleware implementing RFC 7807 Problem Details.

This module provides comprehensive error handling for the FastAPI application,
including:
- RFC 7807 Problem Details formatting
- Exception hierarchy handling
- Stack traces in development mode
- Error context collection
- Error fingerprinting and rate limiting
- Integration with notification and reporting systems
"""

import logging
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import get_settings
from app.middleware.errors.context import (
    ErrorContext,
    ErrorFingerprinter,
    get_rate_limiter,
)
from app.middleware.errors.formatters import get_formatter
from app.middleware.errors.mappings import get_exception_mapping
from app.middleware.errors.reporters import (
    ErrorSeverityClassifier,
    get_reporter,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error handling.

    Catches all unhandled exceptions and formats them according to
    RFC 7807 Problem Details specification.
    """

    def __init__(self, app: FastAPI, enable_reporting: bool = True):
        """
        Initialize error handler middleware.

        Args:
            app: FastAPI application
            enable_reporting: Whether to enable error reporting
        """
        super().__init__(app)
        self.enable_reporting = enable_reporting
        self.formatter = get_formatter()
        self.reporter = get_reporter() if enable_reporting else None
        self.rate_limiter = get_rate_limiter()
        self.fingerprinter = ErrorFingerprinter()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request and handle any errors.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response (error response if exception occurred)
        """
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            return await self.handle_error(request, exc)

    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle an exception and return formatted error response.

        Args:
            request: Request that caused the error
            exc: Exception that occurred

        Returns:
            JSONResponse with RFC 7807 Problem Details
        """
        # Get exception mapping
        mapping = get_exception_mapping(exc)

        # Override status code for HTTPException
        from fastapi import HTTPException

        if isinstance(exc, HTTPException):
            status_code = exc.status_code
        else:
            status_code = mapping.status_code

        # Create error context
        context = ErrorContext(request, exc)

        # Generate error fingerprint
        fingerprint = self.fingerprinter.generate_fingerprint(
            exc=exc,
            request_path=request.url.path,
            include_message=True,
        )

        # Get request ID if available
        request_id = request.headers.get("X-Request-ID")

        # Determine if we should include details
        include_details = mapping.include_details or settings.DEBUG

        # Determine if we should include stack trace
        include_stack_trace = settings.DEBUG

        # Format error response
        error_response = self.formatter.format_error(
            exc=exc,
            status_code=status_code,
            error_code=mapping.error_code,
            title=mapping.default_title,
            request_path=request.url.path,
            include_details=include_details,
            include_stack_trace=include_stack_trace,
            request_id=request_id,
            fingerprint=fingerprint,
        )

        # Report error if enabled
        if self.enable_reporting and self.reporter:
            await self._report_error(exc, context, status_code, fingerprint)

        # Return JSON response
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={
                "Content-Type": "application/problem+json",
            },
        )

    async def _report_error(
        self,
        exc: Exception,
        context: ErrorContext,
        status_code: int,
        fingerprint: str,
    ) -> None:
        """
        Report error to configured reporters.

        Args:
            exc: Exception
            context: Error context
            status_code: HTTP status code
            fingerprint: Error fingerprint
        """
        try:
            # Classify severity
            severity = ErrorSeverityClassifier.classify(exc, status_code)

            # Check rate limiting
            should_report = self.rate_limiter.should_report(fingerprint)

            if should_report:
                # Report to all configured reporters
                await self.reporter.report(
                    exc=exc,
                    context=context,
                    severity=severity,
                )
            else:
                # Log that we're rate limiting
                error_count = self.rate_limiter.get_error_count(fingerprint)
                logger.debug(
                    f"Rate limiting error reporting for fingerprint {fingerprint} "
                    f"(count: {error_count})"
                )

        except Exception as e:
            # Never let error reporting crash the request
            logger.error(f"Error in error reporting: {e}", exc_info=True)


def create_error_handler(exc_type: type) -> Callable:
    """
    Create an exception handler function for a specific exception type.

    This is used for registering exception handlers with FastAPI's
    exception_handler decorator.

    Args:
        exc_type: Exception type to handle

    Returns:
        Async exception handler function
    """

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle specific exception type."""
        # Create error handler middleware instance
        middleware = ErrorHandlerMiddleware(
            app=request.app,
            enable_reporting=True,
        )

        # Handle the error
        return await middleware.handle_error(request, exc)

    return handler


def install_error_handlers(app: FastAPI, enable_middleware: bool = True) -> None:
    """
    Install error handlers on FastAPI application.

    This can be used in two ways:
    1. As middleware (catches all exceptions)
    2. As exception handlers (for specific exception types)

    Args:
        app: FastAPI application
        enable_middleware: Whether to install as middleware
    """
    if enable_middleware:
        # Install as middleware (recommended)
        app.add_middleware(ErrorHandlerMiddleware, enable_reporting=True)
        logger.info("Error handler middleware installed")

    else:
        # Install as exception handlers
        from fastapi import HTTPException
        from pydantic import ValidationError as PydanticValidationError

        from app.core.exceptions import (
            AppException,
            ConflictError,
            ForbiddenError,
            NotFoundError,
            UnauthorizedError,
            ValidationError,
        )

        # Register handlers for specific exception types
        exception_types = [
            AppException,
            NotFoundError,
            ValidationError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
            HTTPException,
            PydanticValidationError,
            Exception,  # Catch-all
        ]

        for exc_type in exception_types:
            handler = create_error_handler(exc_type)
            app.add_exception_handler(exc_type, handler)

        logger.info(f"Registered {len(exception_types)} exception handlers")


class ErrorHandlingConfig:
    """Configuration for error handling behavior."""

    def __init__(
        self,
        enable_reporting: bool = True,
        enable_notifications: bool = True,
        enable_rate_limiting: bool = True,
        max_errors_per_minute: int = 10,
        include_stack_trace_in_dev: bool = True,
    ):
        """
        Initialize error handling configuration.

        Args:
            enable_reporting: Enable error reporting to logs/metrics
            enable_notifications: Enable error notifications
            enable_rate_limiting: Enable rate limiting for error reports
            max_errors_per_minute: Maximum errors to report per minute
            include_stack_trace_in_dev: Include stack traces in dev mode
        """
        self.enable_reporting = enable_reporting
        self.enable_notifications = enable_notifications
        self.enable_rate_limiting = enable_rate_limiting
        self.max_errors_per_minute = max_errors_per_minute
        self.include_stack_trace_in_dev = include_stack_trace_in_dev


# Global configuration
_config: ErrorHandlingConfig | None = None


def get_config() -> ErrorHandlingConfig:
    """
    Get error handling configuration.

    Returns:
        ErrorHandlingConfig instance
    """
    global _config
    if _config is None:
        _config = ErrorHandlingConfig()
    return _config


def set_config(config: ErrorHandlingConfig) -> None:
    """
    Set error handling configuration.

    Args:
        config: ErrorHandlingConfig to use
    """
    global _config
    _config = config


# Convenience function for backward compatibility
async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Legacy exception handler for AppException.

    This maintains backward compatibility with the existing error handler
    in main.py while using the new comprehensive error handling system.

    Args:
        request: Request that caused the error
        exc: AppException that occurred

    Returns:
        JSONResponse with error details
    """
    middleware = ErrorHandlerMiddleware(
        app=request.app,
        enable_reporting=True,
    )
    return await middleware.handle_error(request, exc)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Legacy global exception handler.

    This maintains backward compatibility with the existing error handler
    in main.py while using the new comprehensive error handling system.

    Args:
        request: Request that caused the error
        exc: Exception that occurred

    Returns:
        JSONResponse with error details
    """
    middleware = ErrorHandlerMiddleware(
        app=request.app,
        enable_reporting=True,
    )
    return await middleware.handle_error(request, exc)
