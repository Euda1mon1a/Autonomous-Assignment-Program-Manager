"""Transactional Outbox Models.

The transactional outbox pattern ensures reliable message delivery by:
1. Writing messages to the database within the same transaction as business data
2. Reliably publishing messages from the database to the message broker
3. Providing exactly-once delivery semantics

This prevents the dual-write problem where:
- Business transaction succeeds but message fails to publish
- Message publishes but business transaction fails

References:
- https://microservices.io/patterns/data/transactional-outbox.html
- Enterprise Integration Patterns (Hohpe & Woolf)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)

from app.db.base import Base
from app.db.types import GUID, JSONType


class OutboxStatus(str, enum.Enum):
    """Status of an outbox message."""

    PENDING = "pending"  # Waiting to be published
    PROCESSING = "processing"  # Currently being published
    PUBLISHED = "published"  # Successfully published to broker
    FAILED = "failed"  # Publishing failed (will retry)
    ARCHIVED = "archived"  # Moved to archive (no longer active)


class OutboxMessage(Base):
    """
    Transactional outbox message for reliable event publishing.

    Messages are written to this table within the same database transaction
    as business data changes. A separate relay process reads pending messages
    and publishes them to the message broker (Redis/Celery).

    Lifecycle:
    1. PENDING: Message created in same transaction as business data
    2. PROCESSING: Relay picked up message for publishing
    3. PUBLISHED: Successfully published to broker
    4. FAILED: Publishing failed, will retry based on retry policy
    5. ARCHIVED: Published message moved to archive after retention period

    Features:
    - Exactly-once delivery: Message ID prevents duplicate processing
    - Message ordering: Sequence number maintains order within aggregates
    - Retry logic: Exponential backoff for failed publishes
    - Dead letter: Max retries exceeded moves to failed state
    - Cleanup: Archive old published messages to prevent table growth
    """

    __tablename__ = "outbox_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Message metadata
    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(GUID(), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)

    # Sequence number for ordering (per aggregate)
    # Ensures messages for same aggregate are processed in order
    sequence = Column(Integer, nullable=False, default=0)

    # Message payload
    payload = Column(JSONType, nullable=False)

    # Message headers (routing, correlation IDs, etc.)
    headers = Column(JSONType, default=dict)

    # Publishing metadata
    status = Column(
        String(20), nullable=False, default=OutboxStatus.PENDING.value, index=True
    )

    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Publishing tracking
    published_at = Column(DateTime, nullable=True, index=True)
    processing_started_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        # Ensure valid status values
        CheckConstraint(
            "status IN ('pending', 'processing', 'published', 'failed', 'archived')",
            name="check_outbox_status",
        ),
        # Composite index for efficient polling of pending messages
        Index(
            "idx_outbox_pending_messages",
            "status",
            "created_at",
        ),
        # Index for retry processing
        Index(
            "idx_outbox_retry",
            "status",
            "next_retry_at",
        ),
        # Index for ordering within aggregate
        Index(
            "idx_outbox_aggregate_sequence",
            "aggregate_type",
            "aggregate_id",
            "sequence",
        ),
        # Index for cleanup of old messages
        Index(
            "idx_outbox_published_cleanup",
            "status",
            "published_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OutboxMessage("
            f"id={self.id}, "
            f"event_type='{self.event_type}', "
            f"status='{self.status}', "
            f"aggregate={self.aggregate_type}:{self.aggregate_id}"
            f")>"
        )

    @property
    def is_pending(self) -> bool:
        """Check if message is pending publication."""
        return self.status == OutboxStatus.PENDING.value

    @property
    def is_processing(self) -> bool:
        """Check if message is being processed."""
        return self.status == OutboxStatus.PROCESSING.value

    @property
    def is_published(self) -> bool:
        """Check if message was successfully published."""
        return self.status == OutboxStatus.PUBLISHED.value

    @property
    def is_failed(self) -> bool:
        """Check if message publishing failed."""
        return self.status == OutboxStatus.FAILED.value

    @property
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.retry_count < self.max_retries

    @property
    def should_retry_now(self) -> bool:
        """Check if message is ready for retry."""
        if not self.can_retry:
            return False
        if not self.next_retry_at:
            return True
        return datetime.utcnow() >= self.next_retry_at


class OutboxArchive(Base):
    """
    Archive for successfully published outbox messages.

    Messages are moved here after successful publication to keep the
    main outbox table small and performant. Archive can be periodically
    purged based on retention policies.
    """

    __tablename__ = "outbox_archive"

    id = Column(GUID(), primary_key=True)

    # Same fields as OutboxMessage
    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(GUID(), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    payload = Column(JSONType, nullable=False)
    headers = Column(JSONType, default=dict)

    # Original timestamps
    created_at = Column(DateTime, nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)

    # Archive timestamp
    archived_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        # Index for retention cleanup
        Index("idx_archive_retention", "archived_at"),
        # Index for event type queries
        Index("idx_archive_event_type", "event_type", "archived_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<OutboxArchive("
            f"id={self.id}, "
            f"event_type='{self.event_type}', "
            f"archived_at={self.archived_at}"
            f")>"
        )
