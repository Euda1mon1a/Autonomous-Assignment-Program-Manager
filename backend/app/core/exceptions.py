"""Custom exception classes for application errors.

These exceptions are designed to be safe to expose to end users,
unlike generic Python exceptions which may leak internal details.
"""


class AppException(Exception):
    """Base exception for application errors that are safe to show to users.

    All application-specific exceptions should inherit from this class.
    These exceptions will be handled specially by the global exception
    handler to return appropriate HTTP error responses.
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        """Initialize application exception.

        Args:
            message: User-friendly error message (safe to expose)
            status_code: HTTP status code to return
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found error (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize not found error.

        Args:
            message: User-friendly error message describing what was not found
        """
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """Validation error for invalid input (HTTP 422)."""

    def __init__(self, message: str) -> None:
        """Initialize validation error.

        Args:
            message: User-friendly validation error message
        """
        super().__init__(message, status_code=422)


class ConflictError(AppException):
    """Resource conflict error (HTTP 409)."""

    def __init__(self, message: str) -> None:
        """Initialize conflict error.

        Args:
            message: User-friendly conflict description
        """
        super().__init__(message, status_code=409)


class UnauthorizedError(AppException):
    """Unauthorized access error (HTTP 401)."""

    def __init__(self, message: str = "Authentication required") -> None:
        """Initialize unauthorized error.

        Args:
            message: User-friendly authentication error message
        """
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Forbidden access error (HTTP 403)."""

    def __init__(self, message: str = "Access forbidden") -> None:
        """Initialize forbidden error.

        Args:
            message: User-friendly authorization error message
        """
        super().__init__(message, status_code=403)


class ActivityNotFoundError(AppException):
    """Activity code not found in database (HTTP 422).

    Raised during schedule generation when an activity code (e.g., 'LEC', 'C', 'FMIT')
    cannot be resolved to an Activity record. This prevents silent failures that
    would result in NULL activity_id in half_day_assignments.

    Recovery:
        Run preflight check: ./scripts/preflight-block10.sh
        This verifies all required activity codes exist before generation.
    """

    def __init__(self, code: str, context: str = "") -> None:
        """Initialize activity not found error.

        Args:
            code: The activity code that was not found (e.g., 'LEC', 'C', 'FMIT')
            context: Optional context about where the lookup occurred
        """
        self.code = code
        self.context = context
        message = f"Activity code '{code}' not found in database."
        if context:
            message += f" Context: {context}"
        message += " Run preflight check: ./scripts/preflight-block10.sh"
        super().__init__(message, status_code=422)
