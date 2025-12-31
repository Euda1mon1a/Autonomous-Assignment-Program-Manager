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
    RECORD_NOT_FOUND = "RECORD_NOT_FOUND"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_STATE = "INVALID_STATE"
    INPUT_VALIDATION_ERROR = "INPUT_VALIDATION_ERROR"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"

    # Date validation errors
    DATE_VALIDATION_ERROR = "DATE_VALIDATION_ERROR"
    DATE_OUT_OF_RANGE = "DATE_OUT_OF_RANGE"
    FUTURE_DATE_NOT_ALLOWED = "FUTURE_DATE_NOT_ALLOWED"
    PAST_DATE_NOT_ALLOWED = "PAST_DATE_NOT_ALLOWED"

    # Concurrency errors
    CONFLICT = "CONFLICT"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"

    # Authorization errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_ROLE = "INSUFFICIENT_ROLE"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    MFA_REQUIRED = "MFA_REQUIRED"
    MFA_INVALID = "MFA_INVALID"

    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"

    # Scheduling errors
    SCHEDULING_ERROR = "SCHEDULING_ERROR"
    SCHEDULE_CONFLICT = "SCHEDULE_CONFLICT"
    SCHEDULE_GENERATION_FAILED = "SCHEDULE_GENERATION_FAILED"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"
    CONSTRAINT_VIOLATION_SCHEDULING = "CONSTRAINT_VIOLATION_SCHEDULING"
    INFEASIBLE_SCHEDULE = "INFEASIBLE_SCHEDULE"
    ROTATION_TEMPLATE_ERROR = "ROTATION_TEMPLATE_ERROR"
    BLOCK_ASSIGNMENT_ERROR = "BLOCK_ASSIGNMENT_ERROR"

    # ACGME compliance errors
    ACGME_COMPLIANCE_ERROR = "ACGME_COMPLIANCE_ERROR"
    WORK_HOUR_VIOLATION = "WORK_HOUR_VIOLATION"
    REST_REQUIREMENT_VIOLATION = "REST_REQUIREMENT_VIOLATION"
    SUPERVISION_VIOLATION = "SUPERVISION_VIOLATION"
    SHIFT_LENGTH_VIOLATION = "SHIFT_LENGTH_VIOLATION"
    CALL_FREQUENCY_VIOLATION = "CALL_FREQUENCY_VIOLATION"

    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    INTEGRITY_CONSTRAINT_ERROR = "INTEGRITY_CONSTRAINT_ERROR"
    FOREIGN_KEY_VIOLATION = "FOREIGN_KEY_VIOLATION"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"

    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_TIMEOUT = "SERVICE_TIMEOUT"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    EMAIL_SERVICE_ERROR = "EMAIL_SERVICE_ERROR"
    SMS_SERVICE_ERROR = "SMS_SERVICE_ERROR"
    NOTIFICATION_SERVICE_ERROR = "NOTIFICATION_SERVICE_ERROR"
    CLOUD_STORAGE_ERROR = "CLOUD_STORAGE_ERROR"
    PAYMENT_SERVICE_ERROR = "PAYMENT_SERVICE_ERROR"
    WEBHOOK_DELIVERY_ERROR = "WEBHOOK_DELIVERY_ERROR"

    # Rate limiting errors
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    CONCURRENCY_LIMIT_EXCEEDED = "CONCURRENCY_LIMIT_EXCEEDED"
    BANDWIDTH_LIMIT_EXCEEDED = "BANDWIDTH_LIMIT_EXCEEDED"
    STORAGE_QUOTA_EXCEEDED = "STORAGE_QUOTA_EXCEEDED"

    # Generic error
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Error code to user-friendly description mapping
ERROR_CODE_DESCRIPTIONS: dict[ErrorCode, str] = {
    # Resource errors
    ErrorCode.NOT_FOUND: "The requested resource was not found",
    ErrorCode.ALREADY_EXISTS: "A resource with this information already exists",
    ErrorCode.RECORD_NOT_FOUND: "The requested database record was not found",
    ErrorCode.DUPLICATE_RECORD: "A record with this information already exists",
    # Validation errors
    ErrorCode.VALIDATION_ERROR: "The provided data failed validation",
    ErrorCode.INVALID_STATE: "The resource is in an invalid state for this operation",
    ErrorCode.INPUT_VALIDATION_ERROR: "The input data is invalid",
    ErrorCode.SCHEMA_VALIDATION_ERROR: "The data does not match the required schema",
    ErrorCode.REQUIRED_FIELD: "A required field is missing",
    ErrorCode.INVALID_FORMAT: "The data format is invalid",
    ErrorCode.VALUE_OUT_OF_RANGE: "The value is outside the allowed range",
    # Date validation errors
    ErrorCode.DATE_VALIDATION_ERROR: "The provided date is invalid",
    ErrorCode.DATE_OUT_OF_RANGE: "The date is outside the allowed range",
    ErrorCode.FUTURE_DATE_NOT_ALLOWED: "Future dates are not allowed for this field",
    ErrorCode.PAST_DATE_NOT_ALLOWED: "Past dates are not allowed for this field",
    # Concurrency errors
    ErrorCode.CONFLICT: "The request conflicts with existing data",
    ErrorCode.CONCURRENT_MODIFICATION: "The record was modified by another user",
    # Authorization errors
    ErrorCode.UNAUTHORIZED: "Authentication is required",
    ErrorCode.FORBIDDEN: "You do not have permission for this action",
    ErrorCode.INVALID_CREDENTIALS: "The provided credentials are invalid",
    ErrorCode.TOKEN_EXPIRED: "Your authentication token has expired",
    ErrorCode.INVALID_TOKEN: "The authentication token is invalid",
    ErrorCode.TOKEN_REVOKED: "The authentication token has been revoked",
    ErrorCode.PERMISSION_DENIED: "You do not have permission for this action",
    ErrorCode.INSUFFICIENT_ROLE: "Your role does not allow this action",
    ErrorCode.ACCOUNT_DISABLED: "This account has been disabled",
    ErrorCode.MFA_REQUIRED: "Multi-factor authentication is required",
    ErrorCode.MFA_INVALID: "The multi-factor authentication code is invalid",
    # Business logic errors
    ErrorCode.BUSINESS_RULE_VIOLATION: "A business rule was violated",
    ErrorCode.CONSTRAINT_VIOLATION: "A constraint was violated",
    ErrorCode.INVALID_STATE_TRANSITION: "The requested state transition is not allowed",
    # Scheduling errors
    ErrorCode.SCHEDULING_ERROR: "A scheduling error occurred",
    ErrorCode.SCHEDULE_CONFLICT: "The assignment conflicts with existing schedules",
    ErrorCode.SCHEDULE_GENERATION_FAILED: "Schedule generation failed",
    ErrorCode.SOLVER_TIMEOUT: "Schedule solver timed out",
    ErrorCode.CONSTRAINT_VIOLATION_SCHEDULING: "A scheduling constraint was violated",
    ErrorCode.INFEASIBLE_SCHEDULE: "The schedule requirements cannot be satisfied",
    ErrorCode.ROTATION_TEMPLATE_ERROR: "The rotation template is invalid",
    ErrorCode.BLOCK_ASSIGNMENT_ERROR: "The block assignment is invalid",
    # ACGME compliance errors
    ErrorCode.ACGME_COMPLIANCE_ERROR: "ACGME compliance requirements were violated",
    ErrorCode.WORK_HOUR_VIOLATION: "The 80-hour work week limit was violated",
    ErrorCode.REST_REQUIREMENT_VIOLATION: "The 1-in-7 rest day requirement was violated",
    ErrorCode.SUPERVISION_VIOLATION: "Supervision ratio requirements were violated",
    ErrorCode.SHIFT_LENGTH_VIOLATION: "Maximum shift length was exceeded",
    ErrorCode.CALL_FREQUENCY_VIOLATION: "Call frequency limit was exceeded",
    # Database errors
    ErrorCode.DATABASE_ERROR: "A database error occurred",
    ErrorCode.DATABASE_CONNECTION_ERROR: "Unable to connect to the database",
    ErrorCode.DATABASE_TIMEOUT: "Database operation timed out",
    ErrorCode.INTEGRITY_CONSTRAINT_ERROR: "A database constraint was violated",
    ErrorCode.FOREIGN_KEY_VIOLATION: "The referenced record does not exist",
    ErrorCode.TRANSACTION_ERROR: "Database transaction failed",
    # External service errors
    ErrorCode.EXTERNAL_SERVICE_ERROR: "An external service error occurred",
    ErrorCode.SERVICE_UNAVAILABLE: "The service is temporarily unavailable",
    ErrorCode.SERVICE_TIMEOUT: "The service request timed out",
    ErrorCode.EXTERNAL_API_ERROR: "An external API error occurred",
    ErrorCode.EMAIL_SERVICE_ERROR: "Failed to send email",
    ErrorCode.SMS_SERVICE_ERROR: "Failed to send SMS",
    ErrorCode.NOTIFICATION_SERVICE_ERROR: "Failed to send notification",
    ErrorCode.CLOUD_STORAGE_ERROR: "Cloud storage operation failed",
    ErrorCode.PAYMENT_SERVICE_ERROR: "Payment processing failed",
    ErrorCode.WEBHOOK_DELIVERY_ERROR: "Webhook delivery failed",
    # Rate limiting errors
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
    ErrorCode.QUOTA_EXCEEDED: "Usage quota exceeded",
    ErrorCode.CONCURRENCY_LIMIT_EXCEEDED: "Too many concurrent operations",
    ErrorCode.BANDWIDTH_LIMIT_EXCEEDED: "Bandwidth limit exceeded",
    ErrorCode.STORAGE_QUOTA_EXCEEDED: "Storage quota exceeded",
    # Generic error
    ErrorCode.INTERNAL_ERROR: "An internal server error occurred",
}


def get_error_description(error_code: ErrorCode) -> str:
    """
    Get user-friendly description for an error code.

    Args:
        error_code: The error code

    Returns:
        User-friendly description of the error
    """
    return ERROR_CODE_DESCRIPTIONS.get(
        error_code,
        "An error occurred",
    )


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

    # ACGME compliance patterns
    if "acgme" in message_lower or "work hour" in message_lower:
        if "80" in message_lower or "work hour" in message_lower:
            return ErrorCode.WORK_HOUR_VIOLATION
        if "rest" in message_lower or "1-in-7" in message_lower:
            return ErrorCode.REST_REQUIREMENT_VIOLATION
        if "supervision" in message_lower:
            return ErrorCode.SUPERVISION_VIOLATION
        return ErrorCode.ACGME_COMPLIANCE_ERROR

    # Scheduling patterns
    if "schedule" in message_lower or "assignment" in message_lower:
        if "conflict" in message_lower:
            return ErrorCode.SCHEDULE_CONFLICT
        if "timeout" in message_lower or "solver" in message_lower:
            return ErrorCode.SOLVER_TIMEOUT
        if "generate" in message_lower or "generation" in message_lower:
            return ErrorCode.SCHEDULE_GENERATION_FAILED
        return ErrorCode.SCHEDULING_ERROR

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
    if "token expired" in message_lower:
        return ErrorCode.TOKEN_EXPIRED
    if "invalid token" in message_lower:
        return ErrorCode.INVALID_TOKEN
    if "invalid credentials" in message_lower:
        return ErrorCode.INVALID_CREDENTIALS
    if "unauthorized" in message_lower:
        return ErrorCode.UNAUTHORIZED
    if "forbidden" in message_lower or "access denied" in message_lower:
        return ErrorCode.FORBIDDEN
    if "permission" in message_lower:
        return ErrorCode.PERMISSION_DENIED
    if "admin access required" in message_lower:
        return ErrorCode.FORBIDDEN

    # Rate limiting patterns
    if "rate limit" in message_lower:
        return ErrorCode.RATE_LIMIT_EXCEEDED
    if "quota" in message_lower:
        return ErrorCode.QUOTA_EXCEEDED

    # Database patterns
    if "database" in message_lower:
        if "timeout" in message_lower:
            return ErrorCode.DATABASE_TIMEOUT
        if "connection" in message_lower:
            return ErrorCode.DATABASE_CONNECTION_ERROR
        if "constraint" in message_lower:
            return ErrorCode.INTEGRITY_CONSTRAINT_ERROR
        return ErrorCode.DATABASE_ERROR

    # Validation patterns
    if "required" in message_lower:
        return ErrorCode.REQUIRED_FIELD
    if "invalid" in message_lower or "validation" in message_lower:
        return ErrorCode.VALIDATION_ERROR

    # Default to internal error for unknown messages
    return ErrorCode.INTERNAL_ERROR
