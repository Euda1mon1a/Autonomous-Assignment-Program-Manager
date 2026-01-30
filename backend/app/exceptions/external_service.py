"""External service and third-party API exceptions.

These exceptions are raised when external services fail, timeout,
or return errors. Includes integrations like email services, SMS,
Sentry, and other third-party APIs.
"""

from typing import Any

from app.core.exceptions import AppException


class ExternalServiceError(AppException):
    """Base exception for external service failures."""

    def __init__(
        self,
        message: str = "External service error",
        service_name: str | None = None,
        status_code: int = 502,
        **context: Any,
    ) -> None:
        """Initialize external service error.

        Args:
            message: User-friendly error message
            service_name: Name of external service
            status_code: HTTP status code
            **context: Additional context
        """
        super().__init__(message, status_code)
        self.service_name = service_name
        self.context = context


class ServiceUnavailableError(ExternalServiceError):
    """Raised when an external service is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: str | None = None,
        retry_after: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize service unavailable error.

        Args:
            message: User-friendly error message
            service_name: Name of unavailable service
            retry_after: Seconds until service may be available
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name=service_name,
            status_code=503,
            **context,
        )
        self.retry_after = retry_after


class ServiceTimeoutError(ExternalServiceError):
    """Raised when an external service request times out."""

    def __init__(
        self,
        message: str = "Service request timed out",
        service_name: str | None = None,
        timeout_seconds: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize service timeout error.

        Args:
            message: User-friendly error message
            service_name: Name of service that timed out
            timeout_seconds: Timeout limit in seconds
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name=service_name,
            status_code=504,
            **context,
        )
        self.timeout_seconds = timeout_seconds


class ExternalAPIError(ExternalServiceError):
    """Raised when an external API returns an error."""

    def __init__(
        self,
        message: str = "External API error",
        service_name: str | None = None,
        api_status_code: int | None = None,
        api_error_code: str | None = None,
        api_error_message: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize external API error.

        Args:
            message: User-friendly error message
            service_name: Name of external service/API
            api_status_code: HTTP status code from external API
            api_error_code: Error code from external API
            api_error_message: Error message from external API
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name=service_name,
            status_code=502,
            **context,
        )
        self.api_status_code = api_status_code
        self.api_error_code = api_error_code
        self.api_error_message = api_error_message


class EmailServiceError(ExternalServiceError):
    """Raised when email sending fails."""

    def __init__(
        self,
        message: str = "Failed to send email",
        recipient: str | None = None,
        error_reason: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize email service error.

        Args:
            message: User-friendly error message
            recipient: Email recipient
            error_reason: Reason for failure
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="email",
            status_code=502,
            **context,
        )
        self.recipient = recipient
        self.error_reason = error_reason


class SMSServiceError(ExternalServiceError):
    """Raised when SMS sending fails."""

    def __init__(
        self,
        message: str = "Failed to send SMS",
        phone_number: str | None = None,
        error_reason: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize SMS service error.

        Args:
            message: User-friendly error message
            phone_number: Phone number (last 4 digits for privacy)
            error_reason: Reason for failure
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="sms",
            status_code=502,
            **context,
        )
        self.phone_number = phone_number
        self.error_reason = error_reason


class NotificationServiceError(ExternalServiceError):
    """Raised when notification delivery fails."""

    def __init__(
        self,
        message: str = "Failed to send notification",
        notification_type: str | None = None,
        channel: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize notification service error.

        Args:
            message: User-friendly error message
            notification_type: Type of notification
            channel: Delivery channel (email, sms, push)
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="notification",
            status_code=502,
            **context,
        )
        self.notification_type = notification_type
        self.channel = channel


class CloudStorageError(ExternalServiceError):
    """Raised when cloud storage operations fail."""

    def __init__(
        self,
        message: str = "Cloud storage operation failed",
        operation: str | None = None,
        file_path: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize cloud storage error.

        Args:
            message: User-friendly error message
            operation: Storage operation (upload, download, delete)
            file_path: File path
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="cloud_storage",
            status_code=502,
            **context,
        )
        self.operation = operation
        self.file_path = file_path


class PaymentServiceError(ExternalServiceError):
    """Raised when payment processing fails."""

    def __init__(
        self,
        message: str = "Payment processing failed",
        transaction_id: str | None = None,
        error_code: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize payment service error.

        Args:
            message: User-friendly error message
            transaction_id: Transaction identifier
            error_code: Payment gateway error code
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="payment",
            status_code=502,
            **context,
        )
        self.transaction_id = transaction_id
        self.error_code = error_code


class WebhookDeliveryError(ExternalServiceError):
    """Raised when webhook delivery fails."""

    def __init__(
        self,
        message: str = "Webhook delivery failed",
        webhook_url: str | None = None,
        attempt_count: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize webhook delivery error.

        Args:
            message: User-friendly error message
            webhook_url: Webhook URL
            attempt_count: Number of delivery attempts
            **context: Additional context
        """
        super().__init__(
            message=message,
            service_name="webhook",
            status_code=502,
            **context,
        )
        self.webhook_url = webhook_url
        self.attempt_count = attempt_count
