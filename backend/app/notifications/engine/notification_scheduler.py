"""Scheduling logic for delayed notifications."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class ScheduledNotificationItem(BaseModel):
    """Scheduled notification item."""

    id: UUID
    recipient_id: UUID
    notification_type: NotificationType
    data: dict[str, Any]
    channels: list[str]
    scheduled_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


class NotificationScheduler:
    """
    Schedules notifications for future delivery.

    Features:
    - Delay notifications
    - Recurring notifications
    - Scheduled digests
    - Reminder sequences
    """

    def __init__(self):
        """Initialize scheduler."""
        self._scheduled: dict[UUID, ScheduledNotificationItem] = {}

    async def schedule(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
        scheduled_time: datetime,
        channels: list[str] | None = None,
    ) -> UUID:
        """
        Schedule a notification.

        Args:
            recipient_id: Recipient UUID
            notification_type: Type of notification
            data: Notification data
            scheduled_time: When to send
            channels: Channels to use

        Returns:
            Scheduled notification ID
        """
        from uuid import uuid4

        item = ScheduledNotificationItem(
            id=uuid4(),
            recipient_id=recipient_id,
            notification_type=notification_type,
            data=data,
            channels=channels or ["in_app"],
            scheduled_time=scheduled_time,
        )

        self._scheduled[item.id] = item

        logger.info(
            "Scheduled notification %s for %s",
            item.id,
            scheduled_time.isoformat(),
        )

        return item.id

    async def get_due_notifications(self) -> list[ScheduledNotificationItem]:
        """Get notifications due for sending."""
        now = datetime.utcnow()

        due = [
            item
            for item in self._scheduled.values()
            if item.status == "pending" and item.scheduled_time <= now
        ]

        return due

    async def cancel(self, notification_id: UUID) -> bool:
        """Cancel a scheduled notification."""
        if notification_id in self._scheduled:
            del self._scheduled[notification_id]
            logger.info("Cancelled scheduled notification %s", notification_id)
            return True

        return False

    async def mark_sent(self, notification_id: UUID) -> None:
        """Mark notification as sent."""
        if notification_id in self._scheduled:
            self._scheduled[notification_id].status = "sent"

    def get_pending_count(self) -> int:
        """Get count of pending scheduled notifications."""
        return sum(
            1 for item in self._scheduled.values() if item.status == "pending"
        )
