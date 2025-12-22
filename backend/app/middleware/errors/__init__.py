"""Comprehensive error handling middleware package.

This package provides RFC 7807 Problem Details compliant error handling
with the following features:

- RFC 7807 Problem Details formatting
- Exception hierarchy handling
- Stack traces in development mode
- Error codes catalog integration
- Request context capture
- Error fingerprinting for grouping
- Error rate limiting
- Multi-channel error reporting (logs, metrics, notifications)
- Sentry-style error tracking

Usage:
    from fastapi import FastAPI
    from app.middleware.errors import install_error_handlers

    app = FastAPI()

    # Install error handling middleware
    install_error_handlers(app, enable_middleware=True)

The middleware will automatically:
1. Catch all unhandled exceptions
2. Format them according to RFC 7807
3. Include appropriate context (request info, user, etc.)
4. Report errors to configured channels
5. Rate limit duplicate errors
6. Generate fingerprints for error grouping

Example error response:
    {
        "type": "https://api.example.com/errors/validation-error",
        "title": "Validation Failed",
        "status": 422,
        "detail": "The email field is required",
        "instance": "/api/v1/users",
        "error_code": "VALIDATION_ERROR",
        "error_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-12-20T10:30:00Z",
        "errors": [
            {
                "field": "email",
                "message": "Field required",
                "type": "missing"
            }
        ]
    }
"""

from app.middleware.errors.context import (
    ErrorContext,
    ErrorFingerprinter,
    ErrorRateLimiter,
    get_rate_limiter,
)
from app.middleware.errors.formatters import (
    ErrorFormatter,
    ProblemDetail,
    SimpleErrorFormatter,
    get_formatter,
    set_formatter,
)
from app.middleware.errors.handler import (
    ErrorHandlerMiddleware,
    ErrorHandlingConfig,
    app_exception_handler,
    create_error_handler,
    get_config,
    global_exception_handler,
    install_error_handlers,
    set_config,
)
from app.middleware.errors.mappings import (
    ExceptionMapping,
    get_exception_mapping,
    get_status_code_title,
    EXCEPTION_MAPPINGS,
)
from app.middleware.errors.reporters import (
    CompositeReporter,
    ErrorReporter,
    ErrorSeverityClassifier,
    LoggingReporter,
    MetricsReporter,
    NotificationReporter,
    SentryReporter,
    get_reporter,
    set_reporter,
)

__all__ = [
    # Main handler
    "ErrorHandlerMiddleware",
    "install_error_handlers",
    "create_error_handler",
    "app_exception_handler",
    "global_exception_handler",
    # Configuration
    "ErrorHandlingConfig",
    "get_config",
    "set_config",
    # Formatters
    "ErrorFormatter",
    "SimpleErrorFormatter",
    "ProblemDetail",
    "get_formatter",
    "set_formatter",
    # Mappings
    "ExceptionMapping",
    "get_exception_mapping",
    "get_status_code_title",
    "EXCEPTION_MAPPINGS",
    # Context
    "ErrorContext",
    "ErrorFingerprinter",
    "ErrorRateLimiter",
    "get_rate_limiter",
    # Reporters
    "ErrorReporter",
    "LoggingReporter",
    "MetricsReporter",
    "NotificationReporter",
    "SentryReporter",
    "CompositeReporter",
    "ErrorSeverityClassifier",
    "get_reporter",
    "set_reporter",
]


# Version info
__version__ = "1.0.0"
__author__ = "Residency Scheduler Team"
__description__ = "Comprehensive error handling middleware with RFC 7807 support"
