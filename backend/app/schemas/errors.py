"""Error response schemas for API responses.

These Pydantic schemas define the structure of error responses returned
by the API, ensuring consistent error formatting across all endpoints.

Based on RFC 7807 Problem Details for HTTP APIs.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.core.error_codes import ErrorCode


class ErrorDetail(BaseModel):
    """Detailed error information for a specific field or validation error."""

    field: str = Field(
        description="Field name that caused the error",
        example="email",
    )
    message: str = Field(
        description="Error message for this field",
        example="Invalid email format",
    )
    type: str | None = Field(
        default=None,
        description="Error type (for validation errors)",
        example="value_error.email",
    )
    location: str | None = Field(
        default=None,
        description="Location of the error (body, query, path, header)",
        example="body",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "type": "value_error.email",
                "location": "body",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response (RFC 7807 Problem Details)."""

    type: str = Field(
        description="URI reference identifying the problem type",
        example="https://api.residency-scheduler.example.com/errors/validation-error",
    )
    title: str = Field(
        description="Short, human-readable summary of the problem type",
        example="Validation Failed",
    )
    status: int = Field(
        description="HTTP status code",
        example=422,
        ge=100,
        le=599,
    )
    detail: str = Field(
        description="Human-readable explanation specific to this occurrence",
        example="The request contains invalid data",
    )
    instance: str = Field(
        description="URI reference identifying the specific occurrence",
        example="/api/v1/users",
    )
    error_code: ErrorCode = Field(
        description="Machine-readable error code",
        example="VALIDATION_ERROR",
    )
    error_id: str = Field(
        description="Unique identifier for this error occurrence",
        example="550e8400-e29b-41d4-a716-446655440000",
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp of error occurrence",
        example="2025-12-31T10:30:00Z",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/validation-error",
                "title": "Validation Failed",
                "status": 422,
                "detail": "The request contains invalid data",
                "instance": "/api/v1/users",
                "error_code": "VALIDATION_ERROR",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Error response with validation details."""

    errors: list[ErrorDetail] = Field(
        description="List of validation errors",
        example=[
            {
                "field": "email",
                "message": "Invalid email format",
                "type": "value_error.email",
                "location": "body",
            }
        ],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/validation-error",
                "title": "Validation Failed",
                "status": 422,
                "detail": "The request contains invalid data",
                "instance": "/api/v1/users",
                "error_code": "VALIDATION_ERROR",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "type": "value_error.email",
                        "location": "body",
                    },
                    {
                        "field": "name",
                        "message": "Field required",
                        "type": "value_error.missing",
                        "location": "body",
                    },
                ],
            }
        }


class ACGMEViolationDetail(BaseModel):
    """Details for ACGME compliance violations."""

    resident_id: str | None = Field(
        default=None,
        description="ID of affected resident",
    )
    violation_date: str | None = Field(
        default=None,
        description="Date of violation",
    )
    period_start: str | None = Field(
        default=None,
        description="Start of evaluation period",
    )
    period_end: str | None = Field(
        default=None,
        description="End of evaluation period",
    )
    actual_hours: float | None = Field(
        default=None,
        description="Actual hours worked",
    )
    limit_hours: float | None = Field(
        default=None,
        description="Hour limit",
    )
    rule_violated: str | None = Field(
        default=None,
        description="ACGME rule that was violated",
    )


class ACGMEComplianceErrorResponse(ErrorResponse):
    """Error response for ACGME compliance violations."""

    violation: ACGMEViolationDetail = Field(
        description="Details of the ACGME compliance violation",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/work-hour-violation",
                "title": "ACGME Work Hour Violation",
                "status": 422,
                "detail": "Assignment would violate the 80-hour work week limit",
                "instance": "/api/v1/assignments",
                "error_code": "WORK_HOUR_VIOLATION",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
                "violation": {
                    "resident_id": "RES-001",
                    "period_start": "2025-12-01",
                    "period_end": "2025-12-28",
                    "actual_hours": 84.5,
                    "limit_hours": 80.0,
                    "rule_violated": "80-hour work week (averaged over 4 weeks)",
                },
            }
        }


class ScheduleConflictDetail(BaseModel):
    """Details for schedule conflicts."""

    conflicting_assignment_id: str | None = Field(
        default=None,
        description="ID of conflicting assignment",
    )
    requested_date: str | None = Field(
        default=None,
        description="Date of requested assignment",
    )
    person_id: str | None = Field(
        default=None,
        description="ID of person being assigned",
    )
    conflict_type: str | None = Field(
        default=None,
        description="Type of conflict (time, location, resource)",
    )


class ScheduleConflictErrorResponse(ErrorResponse):
    """Error response for schedule conflicts."""

    conflict: ScheduleConflictDetail = Field(
        description="Details of the schedule conflict",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/schedule-conflict",
                "title": "Schedule Conflict",
                "status": 409,
                "detail": "Assignment conflicts with existing schedule",
                "instance": "/api/v1/assignments",
                "error_code": "SCHEDULE_CONFLICT",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
                "conflict": {
                    "conflicting_assignment_id": "ASGN-123",
                    "requested_date": "2025-12-31",
                    "person_id": "PER-456",
                    "conflict_type": "time",
                },
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Error response for rate limit violations."""

    limit: int = Field(
        description="Rate limit (requests per window)",
        example=100,
    )
    window_seconds: int = Field(
        description="Time window in seconds",
        example=60,
    )
    retry_after: int = Field(
        description="Seconds until rate limit resets",
        example=45,
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/rate-limit-exceeded",
                "title": "Rate Limit Exceeded",
                "status": 429,
                "detail": "Rate limit exceeded. Please try again later.",
                "instance": "/api/v1/assignments",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
                "limit": 100,
                "window_seconds": 60,
                "retry_after": 45,
            }
        }


class ErrorResponseWithSuggestions(ErrorResponse):
    """Error response with suggested solutions."""

    suggestions: list[str] = Field(
        description="Suggested actions to resolve the error",
        example=[
            "Check that all required fields are provided",
            "Ensure the email format is valid",
        ],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "https://api.residency-scheduler.example.com/errors/validation-error",
                "title": "Validation Failed",
                "status": 422,
                "detail": "The request contains invalid data",
                "instance": "/api/v1/users",
                "error_code": "VALIDATION_ERROR",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-31T10:30:00Z",
                "suggestions": [
                    "Check that all required fields are provided",
                    "Ensure the email format is valid (user@example.com)",
                    "Make sure the date is in ISO 8601 format (YYYY-MM-DD)",
                ],
            }
        }


class MultiErrorResponse(BaseModel):
    """Response containing multiple errors (for batch operations)."""

    errors: list[ErrorResponse] = Field(
        description="List of errors that occurred",
    )
    total_errors: int = Field(
        description="Total number of errors",
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp",
        example="2025-12-31T10:30:00Z",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "errors": [
                    {
                        "type": "https://api.residency-scheduler.example.com/errors/validation-error",
                        "title": "Validation Failed",
                        "status": 422,
                        "detail": "Invalid email format for user 1",
                        "instance": "/api/v1/users/batch",
                        "error_code": "VALIDATION_ERROR",
                        "error_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-12-31T10:30:00Z",
                    },
                    {
                        "type": "https://api.residency-scheduler.example.com/errors/duplicate-record",
                        "title": "Duplicate Record",
                        "status": 409,
                        "detail": "User with this email already exists",
                        "instance": "/api/v1/users/batch",
                        "error_code": "DUPLICATE_RECORD",
                        "error_id": "550e8400-e29b-41d4-a716-446655440001",
                        "timestamp": "2025-12-31T10:30:00Z",
                    },
                ],
                "total_errors": 2,
                "timestamp": "2025-12-31T10:30:00Z",
            }
        }


# Legacy simple error response (for backwards compatibility)
class SimpleErrorResponse(BaseModel):
    """Simple error response (legacy format)."""

    detail: str = Field(
        description="Error message",
        example="Resource not found",
    )
    status_code: int = Field(
        description="HTTP status code",
        example=404,
    )
    error_code: str | None = Field(
        default=None,
        description="Error code",
        example="NOT_FOUND",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "status_code": 404,
                "error_code": "NOT_FOUND",
            }
        }
