"""Exception to HTTP status code mappings.

This module provides structured mappings between Python exceptions,
custom application exceptions, and HTTP status codes according to
RFC 7231 and RFC 7807 standards.
"""

from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import (
    DatabaseError,
    DataError,
    IntegrityError,
    OperationalError,
)

from app.core.error_codes import ErrorCode
from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.exceptions import (
    ValidationError as AppValidationError,
)


class ExceptionMapping:
    """Mapping configuration for exception to HTTP status translation."""

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        default_title: str,
        include_details: bool = True,
    ):
        """
        Initialize exception mapping.

        Args:
            status_code: HTTP status code to return
            error_code: Application error code
            default_title: Default error title for RFC 7807
            include_details: Whether to include exception details in response
        """
        self.status_code = status_code
        self.error_code = error_code
        self.default_title = default_title
        self.include_details = include_details


# Exception type to mapping configuration
EXCEPTION_MAPPINGS: dict[type[Exception], ExceptionMapping] = {
    # Application exceptions (custom hierarchy)
    NotFoundError: ExceptionMapping(
        status_code=404,
        error_code=ErrorCode.NOT_FOUND,
        default_title="Resource Not Found",
        include_details=True,
    ),
    AppValidationError: ExceptionMapping(
        status_code=422,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Validation Failed",
        include_details=True,
    ),
    ConflictError: ExceptionMapping(
        status_code=409,
        error_code=ErrorCode.CONFLICT,
        default_title="Resource Conflict",
        include_details=True,
    ),
    UnauthorizedError: ExceptionMapping(
        status_code=401,
        error_code=ErrorCode.UNAUTHORIZED,
        default_title="Authentication Required",
        include_details=True,
    ),
    ForbiddenError: ExceptionMapping(
        status_code=403,
        error_code=ErrorCode.FORBIDDEN,
        default_title="Access Forbidden",
        include_details=True,
    ),
    # Generic AppException (fallback)
    AppException: ExceptionMapping(
        status_code=400,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Bad Request",
        include_details=True,
    ),
    # FastAPI HTTPException
    HTTPException: ExceptionMapping(
        status_code=500,  # Will be overridden by exception's status_code
        error_code=ErrorCode.INTERNAL_ERROR,
        default_title="HTTP Error",
        include_details=True,
    ),
    # Pydantic validation errors
    PydanticValidationError: ExceptionMapping(
        status_code=422,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Request Validation Failed",
        include_details=True,
    ),
    # Database exceptions (SQLAlchemy)
    IntegrityError: ExceptionMapping(
        status_code=409,
        error_code=ErrorCode.CONSTRAINT_VIOLATION,
        default_title="Database Constraint Violation",
        include_details=False,  # Don't leak DB schema details
    ),
    DataError: ExceptionMapping(
        status_code=422,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Invalid Data Format",
        include_details=False,
    ),
    OperationalError: ExceptionMapping(
        status_code=503,
        error_code=ErrorCode.INTERNAL_ERROR,
        default_title="Database Operation Failed",
        include_details=False,
    ),
    DatabaseError: ExceptionMapping(
        status_code=500,
        error_code=ErrorCode.INTERNAL_ERROR,
        default_title="Database Error",
        include_details=False,
    ),
    # Python built-in exceptions
    ValueError: ExceptionMapping(
        status_code=400,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Invalid Value",
        include_details=False,
    ),
    TypeError: ExceptionMapping(
        status_code=400,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Invalid Type",
        include_details=False,
    ),
    KeyError: ExceptionMapping(
        status_code=400,
        error_code=ErrorCode.VALIDATION_ERROR,
        default_title="Missing Required Field",
        include_details=False,
    ),
    AttributeError: ExceptionMapping(
        status_code=500,
        error_code=ErrorCode.INTERNAL_ERROR,
        default_title="Internal Server Error",
        include_details=False,
    ),
    # Catch-all for unexpected exceptions
    Exception: ExceptionMapping(
        status_code=500,
        error_code=ErrorCode.INTERNAL_ERROR,
        default_title="Internal Server Error",
        include_details=False,
    ),
}


def get_exception_mapping(exc: Exception) -> ExceptionMapping:
    """
    Get the appropriate mapping for an exception.

    Walks the exception's MRO (method resolution order) to find
    the most specific mapping available.

    Args:
        exc: Exception to map

    Returns:
        ExceptionMapping for the exception type
    """
    exc_type = type(exc)

    # Try exact match first
    if exc_type in EXCEPTION_MAPPINGS:
        return EXCEPTION_MAPPINGS[exc_type]

    # Walk the MRO to find closest parent class with mapping
    for base_class in exc_type.__mro__:
        if base_class in EXCEPTION_MAPPINGS:
            return EXCEPTION_MAPPINGS[base_class]

    # Fallback to generic Exception mapping
    return EXCEPTION_MAPPINGS[Exception]


def get_status_code_title(status_code: int) -> str:
    """
    Get the standard title for an HTTP status code.

    Args:
        status_code: HTTP status code

    Returns:
        Standard HTTP status title
    """
    STATUS_CODE_TITLES = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return STATUS_CODE_TITLES.get(status_code, "Error")
