"""Notification models for database persistence."""

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
from app.db.types import GUID, JSONType


class Notification(Base):
    """
    Stores delivered notifications for in-app display and history.

    This model tracks all notifications sent to users, their read status,
    and delivery metadata.

    SQLAlchemy Relationships:
        email_logs: One-to-many to EmailLog.
            Back-populates EmailLog.notification.
            Email delivery logs for this notification.
    """

    __tablename__ = "notifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Recipient
    recipient_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification content
    notification_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSONType, default=dict)

    # Priority and channels
    priority = Column(String(20), default="normal")
    channels_delivered = Column(String(200))  # Comma-separated list of channels

    # Read status
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    email_logs = relationship("EmailLog", back_populates="notification")

    __table_args__ = (
        CheckConstraint(
            "priority IN ('high', 'normal', 'low')", name="check_notification_priority"
        ),
    )

    def __repr__(self):
        return f"<Notification(type='{self.notification_type}', recipient={self.recipient_id}, read={self.is_read})>"


class ScheduledNotificationRecord(Base):
    """
    Stores notifications scheduled for future delivery.

    This replaces the in-memory queue with database persistence,
    allowing scheduled notifications to survive server restarts.
    """

    __tablename__ = "scheduled_notifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Recipient
    recipient_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification details
    notification_type = Column(String(50), nullable=False)
    data = Column(JSONType, default=dict)

    # Scheduling
    send_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)

    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')",
            name="check_scheduled_status",
        ),
    )

    def __repr__(self):
        return f"<ScheduledNotification(type='{self.notification_type}', send_at={self.send_at}, status='{self.status}')>"


class NotificationPreferenceRecord(Base):
    """
    Stores user notification preferences.

    Controls which notifications a user receives and through which channels.
    """

    __tablename__ = "notification_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # User (unique - one preference record per user)
    user_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Channel preferences (comma-separated list)
    enabled_channels = Column(String(200), default="in_app,email")

    # Notification type preferences (JSON map of type -> enabled)
    notification_types = Column(JSONType, default=dict)

    # Quiet hours (no notifications during this window)
    quiet_hours_start = Column(Integer, nullable=True)  # Hour (0-23)
    quiet_hours_end = Column(Integer, nullable=True)  # Hour (0-23)

    # Digest preferences
    email_digest_enabled = Column(Boolean, default=False)
    email_digest_frequency = Column(String(20), default="daily")  # daily, weekly

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "quiet_hours_start IS NULL OR (quiet_hours_start >= 0 AND quiet_hours_start <= 23)",
            name="check_quiet_start",
        ),
        CheckConstraint(
            "quiet_hours_end IS NULL OR (quiet_hours_end >= 0 AND quiet_hours_end <= 23)",
            name="check_quiet_end",
        ),
        CheckConstraint(
            "email_digest_frequency IN ('daily', 'weekly')",
            name="check_digest_frequency",
        ),
    )

    def __repr__(self):
        return f"<NotificationPreference(user={self.user_id}, channels='{self.enabled_channels}')>"

    def get_enabled_channels(self) -> list:
        """Return enabled channels as a list."""
        if not self.enabled_channels:
            return ["in_app", "email"]
        return [c.strip() for c in self.enabled_channels.split(",")]

    def is_type_enabled(self, notification_type: str) -> bool:
        """Check if a notification type is enabled."""
        if not self.notification_types:
            return True  # Default to enabled
        return self.notification_types.get(notification_type, True)
