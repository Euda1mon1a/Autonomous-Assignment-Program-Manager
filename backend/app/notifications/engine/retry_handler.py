"""Retry handler for failed notifications."""

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.notifications.channels import NotificationPayload

if TYPE_CHECKING:
    from app.notifications.engine.notification_engine import NotificationEngine

logger = get_logger(__name__)


class RetryAttempt(BaseModel):
    """
    Represents a retry attempt for a failed notification.

    Attributes:
        id: Unique identifier
        payload: Original notification payload
        channel: Channel that failed
        error: Error message
        attempt_count: Number of retry attempts
        max_attempts: Maximum retries allowed
        next_retry: When to retry next
        created_at: When retry was scheduled
        status: Current status
    """

    id: UUID = Field(default_factory=uuid4)
    payload: NotificationPayload
    channel: str
    error: str
    attempt_count: int = 0
    max_attempts: int = 3
    next_retry: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, retrying, failed, succeeded


class RetryHandler:
    """
    Handles retries for failed notification deliveries.

    Retry Strategy:
    1. Exponential backoff: 1 min, 5 min, 15 min
    2. Max 3 attempts per notification
    3. Different strategies by failure type:
       - Transient errors (network): Aggressive retry
       - Rate limits: Longer backoff
       - Invalid data: No retry
    4. Dead letter queue for permanent failures

    Retry intervals by attempt:
    - Attempt 1: 1 minute
    - Attempt 2: 5 minutes
    - Attempt 3: 15 minutes
    - After 3: Move to dead letter queue
    """

    # Retry delays (in minutes) by attempt number
    RETRY_DELAYS = {
        1: 1,
        2: 5,
        3: 15,
    }

    # Errors that should not be retried
    NON_RETRYABLE_ERRORS = {
        "invalid_data",
        "invalid_recipient",
        "channel_not_found",
        "template_not_found",
    }

    def __init__(self):
        """Initialize the retry handler."""
        # Pending retries: retry_id -> RetryAttempt
        self._retries: dict[UUID, RetryAttempt] = {}

        # Dead letter queue: permanently failed notifications
        self._dead_letter: list[RetryAttempt] = []

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def schedule_retry(
        self,
        payload: NotificationPayload,
        channel: str,
        error: str,
        max_attempts: int = 3,
    ) -> UUID | None:
        """
        Schedule a retry for a failed notification.

        Args:
            payload: Original notification payload
            channel: Channel that failed
            error: Error message
            max_attempts: Maximum retry attempts

        Returns:
            UUID of retry attempt, or None if not retryable
        """
        # Check if error is retryable
        if not self._is_retryable(error):
            logger.info(
                "Error not retryable, skipping retry: %s",
                error,
            )
            return None

        async with self._lock:
            # Calculate next retry time
            next_retry = datetime.utcnow() + timedelta(
                minutes=self.RETRY_DELAYS.get(1, 1)
            )

            retry = RetryAttempt(
                payload=payload,
                channel=channel,
                error=error,
                max_attempts=max_attempts,
                next_retry=next_retry,
            )

            self._retries[retry.id] = retry

            logger.info(
                "Scheduled retry for notification %s (channel: %s, next: %s)",
                payload.id,
                channel,
                next_retry,
            )

            return retry.id

    async def process_retries(self, engine: "NotificationEngine") -> int:
        """
        Process due retries.

        Args:
            engine: Notification engine to use for sending

        Returns:
            Number of retries processed
        """
        processed = 0
        now = datetime.utcnow()

        # Get due retries
        due_retries = await self._get_due_retries(now)

        for retry in due_retries:
            try:
                # Mark as retrying
                await self._update_status(retry.id, "retrying")

                # Attempt delivery through dispatcher
                results = await engine.dispatcher.dispatch(
                    payload=retry.payload,
                    channels=[retry.channel],
                    db=engine.db,
                )

                # Check if successful
                if results and results[0].success:
                    # Success! Remove from retries
                    await self._mark_succeeded(retry.id)
                    logger.info(
                        "Retry succeeded for notification %s (attempt %d)",
                        retry.payload.id,
                        retry.attempt_count + 1,
                    )
                else:
                    # Failed again
                    await self._handle_retry_failure(retry, results[0].message if results else "Unknown error")

                processed += 1

            except Exception as e:
                logger.error(
                    "Error processing retry %s: %s",
                    retry.id,
                    e,
                    exc_info=True,
                )
                await self._handle_retry_failure(retry, str(e))

        return processed

    async def _get_due_retries(self, now: datetime) -> list[RetryAttempt]:
        """Get retries that are due for processing."""
        async with self._lock:
            due = [
                retry
                for retry in self._retries.values()
                if retry.status == "pending" and retry.next_retry <= now
            ]

            return due

    async def _handle_retry_failure(self, retry: RetryAttempt, error: str) -> None:
        """Handle a failed retry attempt."""
        async with self._lock:
            retry.attempt_count += 1
            retry.error = error

            if retry.attempt_count >= retry.max_attempts:
                # Move to dead letter queue
                retry.status = "failed"
                self._dead_letter.append(retry)
                del self._retries[retry.id]

                logger.warning(
                    "Retry exhausted for notification %s after %d attempts",
                    retry.payload.id,
                    retry.attempt_count,
                )
            else:
                # Schedule next retry
                delay_minutes = self.RETRY_DELAYS.get(retry.attempt_count + 1, 15)
                retry.next_retry = datetime.utcnow() + timedelta(minutes=delay_minutes)
                retry.status = "pending"

                logger.info(
                    "Retry failed, rescheduling (attempt %d/%d, next: %s)",
                    retry.attempt_count,
                    retry.max_attempts,
                    retry.next_retry,
                )

    async def _update_status(self, retry_id: UUID, status: str) -> None:
        """Update retry status."""
        async with self._lock:
            if retry_id in self._retries:
                self._retries[retry_id].status = status

    async def _mark_succeeded(self, retry_id: UUID) -> None:
        """Mark retry as succeeded and remove."""
        async with self._lock:
            if retry_id in self._retries:
                del self._retries[retry_id]

    def _is_retryable(self, error: str) -> bool:
        """Check if error is retryable."""
        error_lower = error.lower()

        # Check for non-retryable patterns
        for pattern in self.NON_RETRYABLE_ERRORS:
            if pattern in error_lower:
                return False

        return True

    async def get_pending_count(self) -> int:
        """
        Get count of pending retries.

        Returns:
            Number of pending retries
        """
        async with self._lock:
            return len(self._retries)

    async def get_dead_letter_count(self) -> int:
        """
        Get count of dead letter notifications.

        Returns:
            Number of permanently failed notifications
        """
        async with self._lock:
            return len(self._dead_letter)

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get retry statistics.

        Returns:
            Dictionary of statistics
        """
        async with self._lock:
            by_attempt = {1: 0, 2: 0, 3: 0}
            for retry in self._retries.values():
                attempt = retry.attempt_count + 1
                if attempt in by_attempt:
                    by_attempt[attempt] += 1

            return {
                "pending_retries": len(self._retries),
                "dead_letter_count": len(self._dead_letter),
                "by_attempt": by_attempt,
            }

    async def clear_dead_letter(self) -> int:
        """
        Clear dead letter queue.

        Returns:
            Number of items cleared
        """
        async with self._lock:
            count = len(self._dead_letter)
            self._dead_letter.clear()
            logger.info("Cleared %d items from dead letter queue", count)
            return count

    async def retry_dead_letter(self, retry_id: UUID) -> bool:
        """
        Move an item from dead letter back to retry queue.

        Args:
            retry_id: ID of retry to move

        Returns:
            True if moved, False if not found
        """
        async with self._lock:
            for retry in self._dead_letter:
                if retry.id == retry_id:
                    # Reset and move back to retry queue
                    retry.attempt_count = 0
                    retry.status = "pending"
                    retry.next_retry = datetime.utcnow() + timedelta(minutes=1)

                    self._dead_letter.remove(retry)
                    self._retries[retry.id] = retry

                    logger.info("Moved retry %s from dead letter back to queue", retry_id)
                    return True

            return False
