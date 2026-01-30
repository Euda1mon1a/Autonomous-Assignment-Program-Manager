"""Error response formatters implementing RFC 7807 Problem Details.

RFC 7807 defines a standard format for HTTP API error responses.
This module provides formatters that create consistent, machine-readable
error responses while protecting sensitive information.

Reference: https://tools.ietf.org/html/rfc7807
"""

import traceback
from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from app.core.error_codes import ErrorCode


class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Details response model.

    All fields follow RFC 7807 specification for machine-readable
    error responses in HTTP APIs.
    """

    type: str = Field(
        ...,
        description="URI reference identifying the problem type",
        examples=["https://api.example.com/errors/validation-error"],
    )
    title: str = Field(
        ...,
        description="Short, human-readable summary of the problem type",
        examples=["Validation Failed"],
    )
    status: int = Field(
        ...,
        description="HTTP status code",
        examples=[422],
        ge=100,
        le=599,
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation specific to this occurrence",
        examples=["The 'email' field is required"],
    )
    instance: str = Field(
        ...,
        description="URI reference identifying the specific occurrence",
        examples=["/api/v1/users/123"],
    )

    # Extension members (RFC 7807 allows additional fields)
    error_code: ErrorCode = Field(
        ...,
        description="Machine-readable error code",
        examples=["VALIDATION_ERROR"],
    )
    error_id: str = Field(
        ...,
        description="Unique identifier for this error occurrence",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of error occurrence",
        examples=["2025-12-20T10:30:00Z"],
    )

    # Optional fields for additional context
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="Detailed validation errors (for validation failures)",
    )
    stack_trace: list[str] | None = Field(
        default=None,
        description="Stack trace (only in development mode)",
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID for distributed tracing",
    )
    fingerprint: str | None = Field(
        default=None,
        description="Error fingerprint for grouping similar errors",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.example.com/errors/validation-error",
                "title": "Validation Failed",
                "status": 422,
                "detail": "The request contains invalid data",
                "instance": "/api/v1/users",
                "error_code": "VALIDATION_ERROR",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-20T10:30:00Z",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "location": "body",
                    }
                ],
            }
        }


class ErrorFormatter:
    """Formats exceptions into RFC 7807 Problem Details responses."""

    def __init__(
        self, base_url: str = "https://api.residency-scheduler.example.com"
    ) -> None:
        """
        Initialize error formatter.

        Args:
            base_url: Base URL for error type URIs
        """
        self.base_url = base_url

    def format_error(
        self,
        exc: Exception,
        status_code: int,
        error_code: ErrorCode,
        title: str,
        request_path: str,
        include_details: bool = True,
        include_stack_trace: bool = False,
        request_id: str | None = None,
        fingerprint: str | None = None,
    ) -> dict[str, Any]:
        """
        Format an exception into RFC 7807 Problem Details.

        Args:
            exc: Exception to format
            status_code: HTTP status code
            error_code: Application error code
            title: Error title
            request_path: Request path for instance URI
            include_details: Whether to include exception details
            include_stack_trace: Whether to include stack trace (dev mode)
            request_id: Request ID for tracing
            fingerprint: Error fingerprint

        Returns:
            Dict representation of ProblemDetail
        """
        # Generate unique error ID
        error_id = str(uuid4())

        # Build type URI
        type_uri = (
            f"{self.base_url}/errors/{error_code.value.lower().replace('_', '-')}"
        )

        # Get error detail message
        detail = self._get_error_detail(exc, include_details)

        # Build base problem detail
        problem = ProblemDetail(
            type=type_uri,
            title=title,
            status=status_code,
            detail=detail,
            instance=request_path,
            error_code=error_code,
            error_id=error_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            fingerprint=fingerprint,
        )

        # Add validation errors if Pydantic ValidationError
        if isinstance(exc, PydanticValidationError):
            problem.errors = self._format_validation_errors(exc)

            # Add stack trace in development mode
        if include_stack_trace:
            problem.stack_trace = self._format_stack_trace(exc)

        return problem.model_dump(exclude_none=True)

    def _get_error_detail(self, exc: Exception, include_details: bool) -> str:
        """
        Extract error detail message from exception.

        Args:
            exc: Exception
            include_details: Whether to include exception details

        Returns:
            Error detail string
        """
        # For AppException, use the safe message attribute
        if hasattr(exc, "message"):
            return cast(str, exc.message)

            # For other exceptions, include details only if allowed
        if include_details:
            return str(exc) if str(exc) else "An error occurred"

            # Generic message for exceptions that shouldn't expose details
        return "An internal error occurred. Please contact support."

    def _format_validation_errors(
        self, exc: PydanticValidationError
    ) -> list[dict[str, Any]]:
        """
        Format Pydantic validation errors into structured list.

        Args:
            exc: Pydantic ValidationError

        Returns:
            List of formatted validation errors
        """
        errors = []
        for error in exc.errors():
            formatted_error = {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }

            # Add input value context if available (sanitized)
            if "input" in error and error["input"] is not None:
                # Don't include sensitive values (passwords, tokens, etc.)
                field_name = formatted_error["field"].lower()
                if not any(
                    sensitive in field_name
                    for sensitive in ["password", "secret", "token", "key"]
                ):
                    formatted_error["input"] = str(error["input"])[:100]  # Truncate

            errors.append(formatted_error)

        return errors

    def _format_stack_trace(self, exc: Exception) -> list[str]:
        """
        Format exception stack trace into list of strings.

        Args:
            exc: Exception with traceback

        Returns:
            List of stack trace lines
        """
        if exc.__traceback__ is None:
            return []

            # Format traceback
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)

        # Clean up and return as list
        return [line.rstrip() for line in tb_lines]


class SimpleErrorFormatter:
    """
    Simplified error formatter for non-RFC 7807 responses.

    Use this for backwards compatibility or when RFC 7807 format
    is not required.
    """

    @staticmethod
    def format_simple_error(
        message: str,
        status_code: int,
        error_code: ErrorCode | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Format a simple error response.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Optional error code
            errors: Optional detailed errors

        Returns:
            Simple error response dict
        """
        response = {
            "detail": message,
            "status_code": status_code,
        }

        if error_code:
            response["error_code"] = error_code.value

        if errors:
            response["errors"] = errors

        return response

        # Global formatter instance


_formatter: ErrorFormatter | None = None


def get_formatter() -> ErrorFormatter:
    """
    Get the global error formatter instance.

    Returns:
        Configured ErrorFormatter
    """
    global _formatter
    if _formatter is None:
        _formatter = ErrorFormatter()
    return _formatter


def set_formatter(formatter: ErrorFormatter) -> None:
    """
    Set the global error formatter instance.

    Args:
        formatter: ErrorFormatter to use globally
    """
    global _formatter
    _formatter = formatter
