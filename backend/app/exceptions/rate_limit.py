"""Rate limiting and quota exceptions.

These exceptions are raised when rate limits or quotas are exceeded.
"""

from typing import Any

from app.core.exceptions import AppException


class RateLimitExceededError(AppException):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        limit: int | None = None,
        window_seconds: int | None = None,
        retry_after: int | None = None,
        endpoint: str | None = None,
        **context: Any,
    ):
        """Initialize rate limit exceeded error.

        Args:
            message: User-friendly error message
            limit: Rate limit (requests per window)
            window_seconds: Time window in seconds
            retry_after: Seconds until rate limit resets
            endpoint: API endpoint
            **context: Additional context
        """
        super().__init__(message, status_code=429)
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
        self.endpoint = endpoint
        self.context = context


class QuotaExceededError(AppException):
    """Raised when usage quota is exceeded."""

    def __init__(
        self,
        message: str = "Usage quota exceeded",
        quota_type: str | None = None,
        current_usage: int | float | None = None,
        quota_limit: int | float | None = None,
        reset_at: str | None = None,
        **context: Any,
    ):
        """Initialize quota exceeded error.

        Args:
            message: User-friendly error message
            quota_type: Type of quota (requests, storage, compute)
            current_usage: Current usage amount
            quota_limit: Quota limit
            reset_at: When the quota resets
            **context: Additional context
        """
        super().__init__(message, status_code=429)
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.reset_at = reset_at
        self.context = context


class ConcurrencyLimitError(AppException):
    """Raised when concurrent operation limit is exceeded."""

    def __init__(
        self,
        message: str = "Too many concurrent operations. Please try again later.",
        operation_type: str | None = None,
        current_count: int | None = None,
        max_concurrent: int | None = None,
        **context: Any,
    ):
        """Initialize concurrency limit error.

        Args:
            message: User-friendly error message
            operation_type: Type of operation
            current_count: Current concurrent operations
            max_concurrent: Maximum allowed concurrent operations
            **context: Additional context
        """
        super().__init__(message, status_code=429)
        self.operation_type = operation_type
        self.current_count = current_count
        self.max_concurrent = max_concurrent
        self.context = context


class BandwidthLimitError(AppException):
    """Raised when bandwidth limit is exceeded."""

    def __init__(
        self,
        message: str = "Bandwidth limit exceeded",
        current_usage_bytes: int | None = None,
        limit_bytes: int | None = None,
        reset_at: str | None = None,
        **context: Any,
    ):
        """Initialize bandwidth limit error.

        Args:
            message: User-friendly error message
            current_usage_bytes: Current bandwidth usage in bytes
            limit_bytes: Bandwidth limit in bytes
            reset_at: When the limit resets
            **context: Additional context
        """
        super().__init__(message, status_code=429)
        self.current_usage_bytes = current_usage_bytes
        self.limit_bytes = limit_bytes
        self.reset_at = reset_at
        self.context = context


class StorageQuotaExceededError(QuotaExceededError):
    """Raised when storage quota is exceeded."""

    def __init__(
        self,
        message: str = "Storage quota exceeded",
        current_usage_bytes: int | None = None,
        quota_bytes: int | None = None,
        **context: Any,
    ):
        """Initialize storage quota exceeded error.

        Args:
            message: User-friendly error message
            current_usage_bytes: Current storage usage in bytes
            quota_bytes: Storage quota in bytes
            **context: Additional context
        """
        super().__init__(
            message=message,
            quota_type="storage",
            current_usage=current_usage_bytes,
            quota_limit=quota_bytes,
            **context,
        )
