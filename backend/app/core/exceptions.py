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

    def __init__(self, message: str, status_code: int = 400):
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

    def __init__(self, message: str = "Resource not found"):
        """Initialize not found error.

        Args:
            message: User-friendly error message describing what was not found
        """
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """Validation error for invalid input (HTTP 422)."""

    def __init__(self, message: str):
        """Initialize validation error.

        Args:
            message: User-friendly validation error message
        """
        super().__init__(message, status_code=422)


class ConflictError(AppException):
    """Resource conflict error (HTTP 409)."""

    def __init__(self, message: str):
        """Initialize conflict error.

        Args:
            message: User-friendly conflict description
        """
        super().__init__(message, status_code=409)


class UnauthorizedError(AppException):
    """Unauthorized access error (HTTP 401)."""

    def __init__(self, message: str = "Authentication required"):
        """Initialize unauthorized error.

        Args:
            message: User-friendly authentication error message
        """
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Forbidden access error (HTTP 403)."""

    def __init__(self, message: str = "Access forbidden"):
        """Initialize forbidden error.

        Args:
            message: User-friendly authorization error message
        """
        super().__init__(message, status_code=403)
