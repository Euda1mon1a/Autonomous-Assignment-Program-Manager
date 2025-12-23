"""
Structured error codes for service layer responses.

These error codes allow controllers to determine the appropriate HTTP status
without fragile string matching on error messages.

Usage in services:
    return {"error": "Person not found", "error_code": ErrorCode.NOT_FOUND}

Usage in controllers:
    if result.get("error_code") == ErrorCode.NOT_FOUND:
        raise HTTPException(status_code=404, detail=result["error"])
"""

from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for service layer responses."""

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_STATE = "INVALID_STATE"

    # Concurrency errors
    CONFLICT = "CONFLICT"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"

    # Authorization errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # Generic error
    INTERNAL_ERROR = "INTERNAL_ERROR"


def get_error_code_from_message(error_message: str) -> ErrorCode:
    """
    Extract an error code from an error message string.

    This is a compatibility helper for services that haven't been updated
    to return structured error codes yet. Controllers should prefer checking
    result.get("error_code") first, then fall back to this function.

    Args:
        error_message: The error message string from a service

    Returns:
        An ErrorCode based on common patterns in the message
    """
    if not error_message:
        return ErrorCode.INTERNAL_ERROR

    message_lower = error_message.lower()

    # Not found patterns
    if "not found" in message_lower:
        return ErrorCode.NOT_FOUND

    # Concurrency patterns
    if "modified by another user" in message_lower:
        return ErrorCode.CONCURRENT_MODIFICATION
    if "concurrent" in message_lower or "conflict" in message_lower:
        return ErrorCode.CONFLICT

    # Already exists patterns
    if "already exists" in message_lower or "duplicate" in message_lower:
        return ErrorCode.ALREADY_EXISTS

    # Authorization patterns
    if "unauthorized" in message_lower:
        return ErrorCode.UNAUTHORIZED
    if "forbidden" in message_lower or "access denied" in message_lower:
        return ErrorCode.FORBIDDEN
    if "admin access required" in message_lower:
        return ErrorCode.FORBIDDEN

    # Validation patterns
    if "required" in message_lower or "invalid" in message_lower:
        return ErrorCode.VALIDATION_ERROR

    # Default to validation error for unknown messages
    return ErrorCode.VALIDATION_ERROR
