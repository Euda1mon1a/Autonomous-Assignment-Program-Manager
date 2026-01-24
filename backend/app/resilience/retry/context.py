"""
Retry context for tracking retry attempts and state.

Provides detailed information about retry execution, including:
- Attempt history
- Exception tracking
- Timing information
- Callbacks for retry events
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetryAttempt:
    """Record of a single retry attempt."""

    attempt_number: int
    timestamp: datetime
    delay_before: float  # Delay before this attempt (seconds)
    exception: Exception | None = None
    success: bool = False
    duration: float = 0.0  # How long the attempt took (seconds)


@dataclass
class RetryContext:
    """
    Context tracking for a retry operation.

    Maintains state across retry attempts and provides callbacks
    for observability.
    """

    operation_name: str
    max_attempts: int
    start_time: datetime = field(default_factory=datetime.utcnow)
    attempts: list[RetryAttempt] = field(default_factory=list)
    last_delay: float = 0.0  # Track for decorrelated jitter

    # Callbacks
    on_retry: Callable[["RetryContext", Exception, int], None] | None = None
    on_success: Callable[["RetryContext", Any], None] | None = None
    on_failure: Callable[["RetryContext", Exception], None] | None = None

    @property
    def attempt_count(self) -> int:
        """Get the current number of attempts made."""
        return len(self.attempts)

    @property
    def elapsed_time(self) -> timedelta:
        """Get the total elapsed time since retry started."""
        return datetime.utcnow() - self.start_time

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return self.elapsed_time.total_seconds()

    @property
    def total_delay(self) -> float:
        """Get the total time spent waiting between retries."""
        return sum(attempt.delay_before for attempt in self.attempts)

    @property
    def last_exception(self) -> Exception | None:
        """Get the most recent exception."""
        if not self.attempts:
            return None
        for attempt in reversed(self.attempts):
            if attempt.exception:
                return attempt.exception
        return None

    def record_attempt(
        self,
        exception: Exception | None = None,
        success: bool = False,
        delay_before: float = 0.0,
        duration: float = 0.0,
    ) -> None:
        """
        Record a retry attempt.

        Args:
            exception: Exception that occurred (if any)
            success: Whether the attempt succeeded
            delay_before: Delay before this attempt
            duration: How long the attempt took
        """
        attempt = RetryAttempt(
            attempt_number=self.attempt_count + 1,
            timestamp=datetime.utcnow(),
            delay_before=delay_before,
            exception=exception,
            success=success,
            duration=duration,
        )
        self.attempts.append(attempt)
        self.last_delay = delay_before

        logger.debug(
            f"Retry attempt {attempt.attempt_number}/{self.max_attempts} "
            f"for {self.operation_name}: "
            f"{'success' if success else f'failed ({type(exception).__name__})'}"
        )

    def trigger_retry_callback(self, exception: Exception, next_delay: float) -> None:
        """
        Trigger the on_retry callback if configured.

        Args:
            exception: The exception that triggered the retry
            next_delay: The delay before the next retry
        """
        if self.on_retry:
            try:
                self.on_retry(self, exception, int(next_delay))
            except Exception as e:
                logger.error(f"Error in retry callback: {e}", exc_info=True)

    def trigger_success_callback(self, result: Any) -> None:
        """
        Trigger the on_success callback if configured.

        Args:
            result: The successful result
        """
        if self.on_success:
            try:
                self.on_success(self, result)
            except Exception as e:
                logger.error(f"Error in success callback: {e}", exc_info=True)

    def trigger_failure_callback(self, exception: Exception) -> None:
        """
        Trigger the on_failure callback if configured.

        Args:
            exception: The final exception after all retries failed
        """
        if self.on_failure:
            try:
                self.on_failure(self, exception)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}", exc_info=True)

    def get_summary(self) -> dict:
        """
        Get a summary of the retry execution.

        Returns:
            Dictionary with retry statistics
        """
        return {
            "operation": self.operation_name,
            "total_attempts": self.attempt_count,
            "max_attempts": self.max_attempts,
            "elapsed_seconds": self.elapsed_seconds,
            "total_delay_seconds": self.total_delay,
            "successful": any(a.success for a in self.attempts),
            "last_exception": (
                type(self.last_exception).__name__ if self.last_exception else None
            ),
            "attempts": [
                {
                    "attempt": a.attempt_number,
                    "timestamp": a.timestamp.isoformat(),
                    "delay_before": a.delay_before,
                    "success": a.success,
                    "exception": type(a.exception).__name__ if a.exception else None,
                    "duration": a.duration,
                }
                for a in self.attempts
            ],
        }

    def __repr__(self) -> str:
        """String representation of retry context."""
        return (
            f"RetryContext(operation={self.operation_name}, "
            f"attempts={self.attempt_count}/{self.max_attempts}, "
            f"elapsed={self.elapsed_seconds:.2f}s)"
        )
