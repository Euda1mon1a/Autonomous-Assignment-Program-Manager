"""Webhook database models."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType, StringArrayType


class WebhookEventType(str, enum.Enum):
    """Webhook event types."""

    # Schedule events
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_UPDATED = "schedule.updated"
    SCHEDULE_DELETED = "schedule.deleted"

    # Assignment events
    ASSIGNMENT_CREATED = "assignment.created"
    ASSIGNMENT_UPDATED = "assignment.updated"
    ASSIGNMENT_DELETED = "assignment.deleted"

    # Swap events
    SWAP_REQUESTED = "swap.requested"
    SWAP_APPROVED = "swap.approved"
    SWAP_REJECTED = "swap.rejected"
    SWAP_EXECUTED = "swap.executed"
    SWAP_CANCELLED = "swap.cancelled"

    # Conflict events
    CONFLICT_DETECTED = "conflict.detected"
    CONFLICT_RESOLVED = "conflict.resolved"

    # Certification events
    CERTIFICATION_EXPIRING = "certification.expiring"
    CERTIFICATION_EXPIRED = "certification.expired"

    # Leave events
    LEAVE_REQUESTED = "leave.requested"
    LEAVE_APPROVED = "leave.approved"
    LEAVE_REJECTED = "leave.rejected"

    # Resilience events
    RESILIENCE_ALERT = "resilience.alert"
    RESILIENCE_THRESHOLD_EXCEEDED = "resilience.threshold_exceeded"


class WebhookStatus(str, enum.Enum):
    """Webhook endpoint status."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class WebhookDeliveryStatus(str, enum.Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"  # Moved to dead letter queue after max retries


class Webhook(Base):
    """
    Webhook endpoint registration.

    Stores webhook endpoints that subscribe to specific events.
    Each webhook can subscribe to multiple event types.
    """
    __tablename__ = "webhooks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Endpoint configuration
    url = Column(String(2048), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Event subscriptions (array of event types)
    event_types = Column(StringArrayType, nullable=False, default=list)

    # Status
    status = Column(
        String(20),
        nullable=False,
        default=WebhookStatus.ACTIVE.value,
        index=True
    )

    # Secret for signature verification (stored encrypted in production)
    secret = Column(String(255), nullable=False)

    # Configuration
    retry_enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=5)
    timeout_seconds = Column(Integer, default=30)

    # Headers to include in requests (e.g., API keys, custom headers)
    custom_headers = Column(JSONType, default=dict)

    # Metadata
    metadata = Column(JSONType, default=dict)

    # Owner (optional - for multi-tenant scenarios)
    owner_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)

    # Relationships
    deliveries = relationship(
        "WebhookDelivery",
        back_populates="webhook",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'disabled')",
            name="check_webhook_status"
        ),
        CheckConstraint(
            "timeout_seconds > 0 AND timeout_seconds <= 300",
            name="check_webhook_timeout"
        ),
        CheckConstraint(
            "max_retries >= 0 AND max_retries <= 10",
            name="check_webhook_max_retries"
        ),
    )

    def __repr__(self):
        return f"<Webhook(name='{self.name}', url='{self.url}', status='{self.status}')>"

    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if webhook is subscribed to a specific event type."""
        return event_type in (self.event_types or [])


class WebhookDelivery(Base):
    """
    Webhook delivery attempt log.

    Tracks all webhook delivery attempts including retries,
    response codes, and error messages.
    """
    __tablename__ = "webhook_deliveries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Webhook reference
    webhook_id = Column(
        GUID(),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, index=True)  # Optional event identifier
    payload = Column(JSONType, nullable=False)

    # Delivery tracking
    status = Column(
        String(20),
        nullable=False,
        default=WebhookDeliveryStatus.PENDING.value,
        index=True
    )

    # Retry tracking
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Response tracking
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    first_attempted_at = Column(DateTime, nullable=True)
    last_attempted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'success', 'failed', 'dead_letter')",
            name="check_delivery_status"
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="check_attempt_count"
        ),
    )

    def __repr__(self):
        return (
            f"<WebhookDelivery("
            f"event='{self.event_type}', "
            f"status='{self.status}', "
            f"attempts={self.attempt_count}"
            f")>"
        )

    @property
    def can_retry(self) -> bool:
        """Check if delivery can be retried."""
        return (
            self.status in [WebhookDeliveryStatus.PENDING.value, WebhookDeliveryStatus.FAILED.value]
            and self.attempt_count < self.max_attempts
        )

    @property
    def is_final(self) -> bool:
        """Check if delivery is in a final state (success or dead letter)."""
        return self.status in [
            WebhookDeliveryStatus.SUCCESS.value,
            WebhookDeliveryStatus.DEAD_LETTER.value
        ]


class WebhookDeadLetter(Base):
    """
    Dead letter queue for failed webhook deliveries.

    Stores webhook deliveries that have exceeded max retries
    for manual review and reprocessing.
    """
    __tablename__ = "webhook_dead_letters"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Original delivery reference
    delivery_id = Column(
        GUID(),
        ForeignKey("webhook_deliveries.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Webhook reference
    webhook_id = Column(
        GUID(),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details (denormalized for quick access)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSONType, nullable=False)

    # Failure details
    total_attempts = Column(Integer, nullable=False)
    last_error_message = Column(Text, nullable=True)
    last_http_status = Column(Integer, nullable=True)

    # Resolution tracking
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True
    )
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        CheckConstraint(
            "total_attempts > 0",
            name="check_total_attempts"
        ),
    )

    def __repr__(self):
        return (
            f"<WebhookDeadLetter("
            f"event='{self.event_type}', "
            f"resolved={self.resolved}"
            f")>"
        )
