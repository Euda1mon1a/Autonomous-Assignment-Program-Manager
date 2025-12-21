"""
Retry-specific exceptions.

Defines custom exceptions for retry mechanisms and retry-related errors.
"""

from typing import Any, Optional


class RetryError(Exception):
    """Base exception for retry-related errors."""

    def __init__(
        self,
        message: str,
        attempts: int = 0,
        last_exception: Optional[Exception] = None,
    ):
        """
        Initialize retry error.

        Args:
            message: Error message
            attempts: Number of attempts made
            last_exception: The last exception that caused retry failure
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class MaxRetriesExceeded(RetryError):
    """Raised when maximum retry attempts have been exceeded."""

    def __init__(
        self,
        attempts: int,
        last_exception: Optional[Exception] = None,
        operation: str = "operation",
    ):
        """
        Initialize max retries exceeded error.

        Args:
            attempts: Number of attempts made
            last_exception: The last exception that caused retry failure
            operation: Name of the operation that failed
        """
        message = (
            f"Maximum retry attempts ({attempts}) exceeded for {operation}"
        )
        super().__init__(message, attempts=attempts, last_exception=last_exception)
        self.operation = operation


class NonRetryableError(RetryError):
    """Raised when an error is explicitly marked as non-retryable."""

    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize non-retryable error.

        Args:
            message: Error message
            original_exception: The original exception that should not be retried
        """
        super().__init__(message, attempts=0, last_exception=original_exception)
        self.original_exception = original_exception


class RetryTimeoutError(RetryError):
    """Raised when retry operation exceeds maximum allowed time."""

    def __init__(
        self,
        timeout_seconds: float,
        attempts: int = 0,
        last_exception: Optional[Exception] = None,
    ):
        """
        Initialize retry timeout error.

        Args:
            timeout_seconds: The timeout that was exceeded
            attempts: Number of attempts made before timeout
            last_exception: The last exception before timeout
        """
        message = f"Retry operation timed out after {timeout_seconds}s ({attempts} attempts)"
        super().__init__(message, attempts=attempts, last_exception=last_exception)
        self.timeout_seconds = timeout_seconds


class InvalidRetryConfigError(RetryError):
    """Raised when retry configuration is invalid."""

    def __init__(self, message: str, config_field: Optional[str] = None):
        """
        Initialize invalid config error.

        Args:
            message: Error message describing the invalid configuration
            config_field: The specific config field that is invalid
        """
        super().__init__(message)
        self.config_field = config_field
