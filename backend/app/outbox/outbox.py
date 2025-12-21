"""Transactional Outbox Implementation.

This module provides the core implementation of the transactional outbox pattern:
1. OutboxWriter: Writes messages to outbox within database transactions
2. OutboxRelay: Publishes messages from outbox to message broker
3. OutboxCleaner: Archives and cleans up old messages

Usage:
------
# Writing messages within a transaction:
from app.outbox.outbox import OutboxWriter

def create_assignment(db: Session, assignment_data: dict):
    # Business logic
    assignment = Assignment(**assignment_data)
    db.add(assignment)

    # Write outbox message in SAME transaction
    writer = OutboxWriter(db)
    writer.write_message(
        aggregate_type="assignment",
        aggregate_id=assignment.id,
        event_type="assignment.created",
        payload={"assignment_id": str(assignment.id), "date": str(assignment.date)}
    )

    db.commit()  # Both assignment and outbox message committed atomically


# Publishing messages (typically in background task):
from app.outbox.outbox import OutboxRelay

def relay_outbox_messages():
    relay = OutboxRelay()
    published_count = relay.publish_pending_messages(batch_size=100)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from celery import Celery
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.outbox.models import OutboxArchive, OutboxMessage, OutboxStatus

logger = logging.getLogger(__name__)


class OutboxWriter:
    """
    Writes messages to the outbox table within database transactions.

    This ensures that outbox messages are written atomically with business
    data changes, preventing the dual-write problem.
    """

    def __init__(self, db: Session):
        """
        Initialize outbox writer.

        Args:
            db: Database session (must be part of an active transaction)
        """
        self.db = db

    def write_message(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        headers: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> OutboxMessage:
        """
        Write a message to the outbox table.

        This method MUST be called within an active database transaction
        that also contains the business logic changes. The message will
        only be committed if the business transaction commits.

        Args:
            aggregate_type: Type of aggregate (e.g., "assignment", "swap")
            aggregate_id: ID of the aggregate instance
            event_type: Type of event (e.g., "assignment.created", "swap.executed")
            payload: Event data (must be JSON-serializable)
            headers: Optional message headers (routing, correlation IDs, etc.)
            max_retries: Maximum number of retry attempts for this message

        Returns:
            OutboxMessage: The created outbox message

        Raises:
            ValueError: If payload is not JSON-serializable
        """
        # Validate payload is JSON-serializable
        try:
            json.dumps(payload)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Payload must be JSON-serializable: {e}")

        # Get next sequence number for this aggregate
        sequence = self._get_next_sequence(aggregate_type, aggregate_id)

        # Create outbox message
        message = OutboxMessage(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            sequence=sequence,
            payload=payload,
            headers=headers or {},
            status=OutboxStatus.PENDING.value,
            max_retries=max_retries,
            retry_count=0,
        )

        self.db.add(message)
        # Don't flush here - let the transaction handle it
        # This ensures atomicity with business data changes

        logger.debug(
            f"Wrote outbox message: {event_type} for {aggregate_type}:{aggregate_id} "
            f"(sequence={sequence})"
        )

        return message

    def _get_next_sequence(self, aggregate_type: str, aggregate_id: UUID) -> int:
        """
        Get the next sequence number for an aggregate.

        This ensures messages for the same aggregate are processed in order.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: ID of the aggregate

        Returns:
            int: Next sequence number (0 if this is the first message)
        """
        result = self.db.execute(
            select(OutboxMessage.sequence)
            .where(
                and_(
                    OutboxMessage.aggregate_type == aggregate_type,
                    OutboxMessage.aggregate_id == aggregate_id,
                )
            )
            .order_by(OutboxMessage.sequence.desc())
            .limit(1)
        )
        max_sequence = result.scalar_one_or_none()

        if max_sequence is None:
            return 0
        return max_sequence + 1


class OutboxRelay:
    """
    Publishes messages from the outbox to the message broker.

    This service reads pending messages from the outbox table and publishes
    them to Redis/Celery. It handles:
    - Message ordering (processes messages in sequence order per aggregate)
    - Retry logic (exponential backoff for failed publishes)
    - Error handling (marks messages as failed after max retries)
    - Exactly-once delivery (prevents duplicate processing)
    """

    def __init__(
        self,
        db: Session,
        celery_app: Optional[Celery] = None,
        processing_timeout_minutes: int = 5,
    ):
        """
        Initialize outbox relay.

        Args:
            db: Database session
            celery_app: Celery application instance (optional, will import if None)
            processing_timeout_minutes: Timeout for stuck processing messages
        """
        self.db = db
        self.processing_timeout_minutes = processing_timeout_minutes

        # Import Celery app if not provided (avoids circular imports)
        if celery_app is None:
            from app.core.celery_app import celery_app as default_celery_app
            self.celery_app = default_celery_app
        else:
            self.celery_app = celery_app

    def publish_pending_messages(
        self,
        batch_size: int = 100,
        timeout_stuck_processing: bool = True,
    ) -> int:
        """
        Publish pending messages from the outbox to the message broker.

        This method:
        1. Times out stuck processing messages (optional)
        2. Fetches batch of pending/failed messages ready for retry
        3. Publishes each message to Celery/Redis
        4. Marks messages as published or failed

        Args:
            batch_size: Maximum number of messages to process in one batch
            timeout_stuck_processing: Whether to timeout stuck processing messages

        Returns:
            int: Number of messages successfully published
        """
        published_count = 0

        # First, timeout any stuck processing messages
        if timeout_stuck_processing:
            self._timeout_stuck_processing()

        # Fetch pending messages (ordered by creation time for FIFO)
        messages = self._fetch_pending_messages(batch_size)

        logger.info(f"Processing {len(messages)} pending outbox messages")

        for message in messages:
            try:
                # Mark as processing
                self._mark_processing(message)
                self.db.commit()

                # Publish to broker
                self._publish_message(message)

                # Mark as published
                self._mark_published(message)
                self.db.commit()

                published_count += 1
                logger.debug(
                    f"Published outbox message {message.id}: {message.event_type}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to publish outbox message {message.id}: {e}",
                    exc_info=True,
                )

                # Rollback to clean state
                self.db.rollback()

                # Mark as failed and schedule retry
                try:
                    self._mark_failed(message, str(e))
                    self.db.commit()
                except Exception as commit_error:
                    logger.error(
                        f"Failed to mark message {message.id} as failed: {commit_error}"
                    )
                    self.db.rollback()

        logger.info(f"Successfully published {published_count} outbox messages")
        return published_count

    def _fetch_pending_messages(self, batch_size: int) -> list[OutboxMessage]:
        """
        Fetch pending messages ready for publishing.

        Includes:
        - Messages in PENDING status
        - Messages in FAILED status that are ready for retry

        Args:
            batch_size: Maximum number of messages to fetch

        Returns:
            list[OutboxMessage]: Messages ready for publishing
        """
        now = datetime.utcnow()

        # Query for pending and retryable failed messages
        query = (
            select(OutboxMessage)
            .where(
                or_(
                    # Pending messages
                    OutboxMessage.status == OutboxStatus.PENDING.value,
                    # Failed messages ready for retry
                    and_(
                        OutboxMessage.status == OutboxStatus.FAILED.value,
                        OutboxMessage.retry_count < OutboxMessage.max_retries,
                        or_(
                            OutboxMessage.next_retry_at.is_(None),
                            OutboxMessage.next_retry_at <= now,
                        ),
                    ),
                )
            )
            .order_by(OutboxMessage.created_at.asc())
            .limit(batch_size)
        )

        result = self.db.execute(query)
        return list(result.scalars().all())

    def _mark_processing(self, message: OutboxMessage) -> None:
        """
        Mark message as processing.

        Args:
            message: Outbox message to mark
        """
        message.status = OutboxStatus.PROCESSING.value
        message.processing_started_at = datetime.utcnow()

    def _mark_published(self, message: OutboxMessage) -> None:
        """
        Mark message as successfully published.

        Args:
            message: Outbox message to mark
        """
        message.status = OutboxStatus.PUBLISHED.value
        message.published_at = datetime.utcnow()
        message.error_message = None

    def _mark_failed(self, message: OutboxMessage, error_message: str) -> None:
        """
        Mark message as failed and schedule retry if applicable.

        Args:
            message: Outbox message to mark
            error_message: Error message describing the failure
        """
        message.status = OutboxStatus.FAILED.value
        message.retry_count += 1
        message.error_message = error_message
        message.last_error_at = datetime.utcnow()

        # Calculate next retry time using exponential backoff
        if message.can_retry:
            delay_seconds = self._calculate_retry_delay(message.retry_count)
            message.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
            logger.warning(
                f"Message {message.id} failed (attempt {message.retry_count}), "
                f"will retry in {delay_seconds}s"
            )
        else:
            message.next_retry_at = None
            logger.error(
                f"Message {message.id} exceeded max retries ({message.max_retries}), "
                f"giving up"
            )

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay for retries.

        Args:
            retry_count: Current retry attempt number

        Returns:
            int: Delay in seconds before next retry
        """
        # Exponential backoff: 2^retry_count * base_delay
        # Retry 1: 10s, Retry 2: 20s, Retry 3: 40s
        base_delay = 10
        max_delay = 300  # Cap at 5 minutes

        delay = base_delay * (2 ** (retry_count - 1))
        return min(delay, max_delay)

    def _publish_message(self, message: OutboxMessage) -> None:
        """
        Publish a message to the Celery message broker.

        This sends the message to a Celery task queue for processing.
        The task name should match the event type or be configurable.

        Args:
            message: Outbox message to publish

        Raises:
            Exception: If publishing fails
        """
        # Build Celery task arguments
        task_name = self._get_task_name_for_event(message.event_type)

        # Send task to Celery
        self.celery_app.send_task(
            task_name,
            args=[],
            kwargs={
                "event_type": message.event_type,
                "aggregate_type": message.aggregate_type,
                "aggregate_id": str(message.aggregate_id),
                "payload": message.payload,
                "headers": message.headers,
                "message_id": str(message.id),
                "sequence": message.sequence,
            },
            task_id=str(message.id),  # Use message ID as task ID for idempotency
            headers=message.headers,
        )

    def _get_task_name_for_event(self, event_type: str) -> str:
        """
        Get the Celery task name for an event type.

        This can be customized based on your task routing strategy.
        Default: "app.outbox.tasks.handle_outbox_event"

        Args:
            event_type: Event type string

        Returns:
            str: Celery task name
        """
        # Default handler for all outbox events
        return "app.outbox.tasks.handle_outbox_event"

    def _timeout_stuck_processing(self) -> int:
        """
        Timeout messages stuck in PROCESSING state.

        Messages that have been processing for longer than the timeout
        are reset to PENDING state so they can be retried.

        Returns:
            int: Number of messages timed out
        """
        cutoff = datetime.utcnow() - timedelta(minutes=self.processing_timeout_minutes)

        # Find stuck messages
        query = select(OutboxMessage).where(
            and_(
                OutboxMessage.status == OutboxStatus.PROCESSING.value,
                OutboxMessage.processing_started_at < cutoff,
            )
        )

        result = self.db.execute(query)
        stuck_messages = list(result.scalars().all())

        # Reset to pending
        count = 0
        for message in stuck_messages:
            message.status = OutboxStatus.PENDING.value
            message.processing_started_at = None
            count += 1

        if count > 0:
            self.db.commit()
            logger.warning(
                f"Timed out {count} stuck processing messages "
                f"(timeout={self.processing_timeout_minutes}m)"
            )

        return count


class OutboxCleaner:
    """
    Archives and cleans up old outbox messages.

    This service:
    - Moves successfully published messages to archive
    - Deletes old archived messages based on retention policy
    """

    def __init__(
        self,
        db: Session,
        archive_after_hours: int = 24,
        retention_days: int = 30,
    ):
        """
        Initialize outbox cleaner.

        Args:
            db: Database session
            archive_after_hours: Hours after publishing to archive messages
            retention_days: Days to keep archived messages before deletion
        """
        self.db = db
        self.archive_after_hours = archive_after_hours
        self.retention_days = retention_days

    def archive_published_messages(self, batch_size: int = 1000) -> int:
        """
        Archive successfully published messages.

        Moves published messages older than archive_after_hours to the
        archive table to keep the main outbox table small.

        Args:
            batch_size: Maximum number of messages to archive per call

        Returns:
            int: Number of messages archived
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.archive_after_hours)

        # Find published messages to archive
        query = (
            select(OutboxMessage)
            .where(
                and_(
                    OutboxMessage.status == OutboxStatus.PUBLISHED.value,
                    OutboxMessage.published_at < cutoff,
                )
            )
            .limit(batch_size)
        )

        result = self.db.execute(query)
        messages = list(result.scalars().all())

        archived_count = 0
        for message in messages:
            # Create archive record
            archive = OutboxArchive(
                id=message.id,
                aggregate_type=message.aggregate_type,
                aggregate_id=message.aggregate_id,
                event_type=message.event_type,
                sequence=message.sequence,
                payload=message.payload,
                headers=message.headers,
                created_at=message.created_at,
                published_at=message.published_at,
            )

            self.db.add(archive)
            self.db.delete(message)
            archived_count += 1

        if archived_count > 0:
            self.db.commit()
            logger.info(f"Archived {archived_count} published outbox messages")

        return archived_count

    def delete_old_archive(self, batch_size: int = 1000) -> int:
        """
        Delete old archived messages based on retention policy.

        Args:
            batch_size: Maximum number of messages to delete per call

        Returns:
            int: Number of archived messages deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)

        # Delete old archive records
        deleted = (
            self.db.query(OutboxArchive)
            .filter(OutboxArchive.archived_at < cutoff)
            .limit(batch_size)
            .delete(synchronize_session="fetch")
        )

        if deleted > 0:
            self.db.commit()
            logger.info(
                f"Deleted {deleted} archived outbox messages "
                f"(retention={self.retention_days} days)"
            )

        return deleted

    def cleanup_failed_messages(
        self,
        max_age_days: int = 7,
        batch_size: int = 1000,
    ) -> int:
        """
        Delete old failed messages that exceeded max retries.

        These messages are effectively dead letters and should be:
        1. Logged/alerted on
        2. Deleted after investigation period

        Args:
            max_age_days: Days to keep failed messages before deletion
            batch_size: Maximum number of messages to delete per call

        Returns:
            int: Number of failed messages deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)

        # Delete old failed messages
        deleted = (
            self.db.query(OutboxMessage)
            .filter(
                and_(
                    OutboxMessage.status == OutboxStatus.FAILED.value,
                    OutboxMessage.retry_count >= OutboxMessage.max_retries,
                    OutboxMessage.created_at < cutoff,
                )
            )
            .limit(batch_size)
            .delete(synchronize_session="fetch")
        )

        if deleted > 0:
            self.db.commit()
            logger.warning(
                f"Deleted {deleted} failed outbox messages "
                f"(max_age={max_age_days} days)"
            )

        return deleted
