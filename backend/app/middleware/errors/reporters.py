"""Error reporting and notification system.

Provides Sentry-style error reporting with integration to the
application's notification system and external monitoring services.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.middleware.errors.context import ErrorContext

logger = logging.getLogger(__name__)


class ErrorReporter(ABC):
    """Abstract base class for error reporters."""

    @abstractmethod
    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report an error.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional reporter-specific arguments

        Returns:
            True if reported successfully, False otherwise
        """
        pass


class LoggingReporter(ErrorReporter):
    """Reports errors to application logs."""

    def __init__(self, logger_name: str = "app.errors") -> None:
        """
        Initialize logging reporter.

        Args:
            logger_name: Logger name to use
        """
        self.logger = logging.getLogger(logger_name)

    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report error to logs.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional arguments

        Returns:
            True (always succeeds)
        """
        # Get context data
        context_data = context.to_dict(
            include_headers=False,
            include_exception_args=True,
        )

        # Build log message
        request_info = context_data["request"]
        message = (
            f"Error in {request_info['method']} {request_info['path']}: "
            f"{type(exc).__name__}: {str(exc)}"
        )

        # Log at appropriate level
        log_level = self._get_log_level(severity)
        self.logger.log(
            log_level,
            message,
            exc_info=exc,
            extra={
                "error_context": context_data,
                "severity": severity,
            },
        )

        return True

    def _get_log_level(self, severity: str) -> int:
        """
        Convert severity to logging level.

        Args:
            severity: Severity string

        Returns:
            Logging level constant
        """
        severity_mapping = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        return severity_mapping.get(severity.lower(), logging.ERROR)


class NotificationReporter(ErrorReporter):
    """Reports errors via the notification system."""

    def __init__(self) -> None:
        """Initialize notification reporter."""
        self.error_thresholds = {
            "critical": 1,  # Notify on first critical error
            "error": 5,  # Notify every 5 errors
            "warning": 10,  # Notify every 10 warnings
        }

    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report error via notifications.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional arguments

        Returns:
            True if notification sent, False otherwise
        """
        try:
            from app.db.session import get_db
            from app.notifications import get_notification_service
            from app.notifications.templates import NotificationType

            # Only notify for critical errors or recurring errors
            if severity != "critical":
                return False

                # Get notification service
            db = next(get_db())
            notification_service = get_notification_service(db)

            # Get recipients from settings
            from app.core.config import get_settings

            settings = get_settings()
            recipients = settings.RESILIENCE_ALERT_RECIPIENTS

            if not recipients:
                logger.warning("No alert recipients configured for error notifications")
                return False

                # Build notification data
            request_info = context.get_request_info()
            notification_data = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "request_path": request_info["path"],
                "request_method": request_info["method"],
                "timestamp": context.timestamp.isoformat(),
                "severity": severity,
            }

            # Send notifications to all recipients
            for recipient_id in recipients:
                try:
                    await notification_service.send_notification(
                        recipient_id=recipient_id,
                        notification_type=NotificationType.SYSTEM_ALERT,
                        data=notification_data,
                        channels=["email"],  # Use email for error alerts
                    )
                except Exception as e:
                    logger.error(f"Failed to send error notification: {e}")

            return True

        except Exception as e:
            logger.error(f"Error in notification reporter: {e}")
            return False


class MetricsReporter(ErrorReporter):
    """Reports errors to metrics/monitoring system."""

    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report error to metrics.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional arguments

        Returns:
            True if metrics recorded, False otherwise
        """
        try:
            # Import Prometheus metrics if available
            from prometheus_client import Counter

            # Define error counter metric
            error_counter = Counter(
                "http_errors_total",
                "Total HTTP errors",
                ["error_type", "status_code", "path", "severity"],
            )

            # Extract labels
            error_type = type(exc).__name__
            status_code = getattr(exc, "status_code", 500)
            request_info = context.get_request_info()
            path = request_info.get("path", "unknown")

            # Increment counter
            error_counter.labels(
                error_type=error_type,
                status_code=str(status_code),
                path=path,
                severity=severity,
            ).inc()

            return True

        except ImportError:
            # Prometheus not available
            return False
        except Exception as e:
            logger.error(f"Error in metrics reporter: {e}")
            return False


class SentryReporter(ErrorReporter):
    """
    Reports errors to Sentry (or Sentry-compatible service).

    Note: Requires sentry-sdk to be installed.
    """

    def __init__(self, dsn: str | None = None) -> None:
        """
        Initialize Sentry reporter.

        Args:
            dsn: Sentry DSN (Data Source Name)
        """
        self.dsn = dsn
        self.enabled = False

        if dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(dsn=dsn)
                self.enabled = True
                logger.info("Sentry error reporting enabled")
            except ImportError:
                logger.warning("sentry-sdk not installed, Sentry reporting disabled")
        else:
            logger.info("No Sentry DSN configured, Sentry reporting disabled")

    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report error to Sentry.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional arguments

        Returns:
            True if reported to Sentry, False otherwise
        """
        if not self.enabled:
            return False

        try:
            import sentry_sdk

            # Set context
            request_info = context.get_request_info()

            with sentry_sdk.push_scope() as scope:
                # Set request context
                scope.set_context("request", request_info)

                # Set user context if available
                if "user" in request_info:
                    scope.set_user(request_info["user"])

                    # Set tags
                scope.set_tag("severity", severity)
                scope.set_tag("request_method", request_info["method"])
                scope.set_tag("request_path", request_info["path"])

                # Set level
                scope.level = severity

                # Capture exception
                sentry_sdk.capture_exception(exc)

            return True

        except Exception as e:
            logger.error(f"Error reporting to Sentry: {e}")
            return False


class CompositeReporter(ErrorReporter):
    """
    Composite reporter that delegates to multiple reporters.

    Allows reporting errors to multiple destinations (logs, metrics, Sentry, etc.).
    """

    def __init__(self, reporters: list[ErrorReporter] | None = None) -> None:
        """
        Initialize composite reporter.

        Args:
            reporters: List of error reporters to use
        """
        self.reporters = reporters or []

    def add_reporter(self, reporter: ErrorReporter) -> None:
        """
        Add a reporter.

        Args:
            reporter: ErrorReporter to add
        """
        self.reporters.append(reporter)

    async def report(
        self,
        exc: Exception,
        context: ErrorContext,
        severity: str = "error",
        **kwargs: Any,
    ) -> bool:
        """
        Report error to all configured reporters.

        Args:
            exc: Exception to report
            context: Error context
            severity: Error severity level
            **kwargs: Additional arguments

        Returns:
            True if at least one reporter succeeded, False otherwise
        """
        results = []

        for reporter in self.reporters:
            try:
                result = await reporter.report(exc, context, severity, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Reporter {type(reporter).__name__} failed: {e}")
                results.append(False)

        return any(results)


class ErrorSeverityClassifier:
    """
    Classifies error severity based on exception type and context.

    Helps determine which errors require immediate attention vs. logging.
    """

    @staticmethod
    def classify(exc: Exception, status_code: int) -> str:
        """
        Classify error severity.

        Args:
            exc: Exception
            status_code: HTTP status code

        Returns:
            Severity level: "debug", "info", "warning", "error", or "critical"
        """
        # Critical errors (5xx server errors)
        if status_code >= 500:
            # Database errors are critical
            if "database" in type(exc).__name__.lower():
                return "critical"
                # Generic 500 errors are critical
            if status_code == 500:
                return "critical"
                # Service unavailable is critical
            if status_code == 503:
                return "critical"
            return "error"

            # Client errors (4xx)
        if status_code >= 400:
            # Authentication/authorization errors
            if status_code in (401, 403):
                return "warning"
                # Not found is info (normal)
            if status_code == 404:
                return "info"
                # Validation errors are info (normal user errors)
            if status_code == 422:
                return "info"
                # Other client errors are warnings
            return "warning"

            # Default to error
        return "error"

        # Global reporter instance


_reporter: ErrorReporter | None = None


def get_reporter() -> ErrorReporter:
    """
    Get the global error reporter.

    Returns:
        Configured ErrorReporter instance
    """
    global _reporter
    if _reporter is None:
        # Build composite reporter with default reporters
        composite = CompositeReporter()

        # Always add logging reporter
        composite.add_reporter(LoggingReporter())

        # Add metrics reporter if available
        composite.add_reporter(MetricsReporter())

        # Add notification reporter for critical errors
        composite.add_reporter(NotificationReporter())

        # Add Sentry reporter if configured
        # (DSN would come from environment variable)
        import os

        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            composite.add_reporter(SentryReporter(dsn=sentry_dsn))

        _reporter = composite

    return _reporter


def set_reporter(reporter: ErrorReporter) -> None:
    """
    Set the global error reporter.

    Args:
        reporter: ErrorReporter to use globally
    """
    global _reporter
    _reporter = reporter
