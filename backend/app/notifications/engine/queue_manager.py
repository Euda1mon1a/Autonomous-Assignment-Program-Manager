"""Notification queue management."""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class QueuedNotification(BaseModel):
    """
    Represents a queued notification.

    Attributes:
        id: Unique identifier
        recipient_id: UUID of recipient
        notification_type: Type of notification
        data: Notification data
        channels: List of channels to use
        priority: Priority score (higher = more important)
        queued_at: When notification was queued
        retry_count: Number of retry attempts
    """

    id: UUID = Field(default_factory=uuid4)
    recipient_id: UUID
    notification_type: str
    data: dict[str, Any]
    channels: list[str]
    priority: int = 0
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0


class NotificationQueueManager:
    """
    Manages notification queuing with priority handling.

    Implements a multi-priority queue system where notifications
    are organized by priority level (high, normal, low).

    Queuing is used for:
    - Rate-limited notifications
    - Batch processing
    - Retry after failure
    - Off-peak delivery
    """

    def __init__(self):
        """Initialize the queue manager."""
        # Separate queues for each priority level
        self._high_priority: list[QueuedNotification] = []
        self._normal_priority: list[QueuedNotification] = []
        self._low_priority: list[QueuedNotification] = []

        # Index for fast lookup by ID
        self._index: dict[UUID, QueuedNotification] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
        channels: list[str],
        priority: int = 0,
    ) -> UUID:
        """
        Add a notification to the queue.

        Args:
            recipient_id: UUID of recipient
            notification_type: Type of notification
            data: Notification data
            channels: List of channels
            priority: Priority score (0-100, higher = more important)

        Returns:
            UUID of queued notification
        """
        async with self._lock:
            notification = QueuedNotification(
                recipient_id=recipient_id,
                notification_type=notification_type.value,
                data=data,
                channels=channels,
                priority=priority,
            )

            # Determine which queue to use based on priority
            if priority >= 75:
                self._high_priority.append(notification)
                queue_name = "high"
            elif priority >= 25:
                self._normal_priority.append(notification)
                queue_name = "normal"
            else:
                self._low_priority.append(notification)
                queue_name = "low"

            # Add to index
            self._index[notification.id] = notification

            logger.debug(
                "Notification queued: %s (priority: %s, queue: %s)",
                notification.id,
                priority,
                queue_name,
            )

            return notification.id

    async def dequeue(self, priority: str = "high") -> QueuedNotification | None:
        """
        Remove and return the next notification from specified priority queue.

        Args:
            priority: Priority queue to dequeue from ('high', 'normal', 'low')

        Returns:
            QueuedNotification or None if queue is empty
        """
        async with self._lock:
            queue = self._get_queue(priority)

            if not queue:
                return None

            # Get oldest notification (FIFO within priority)
            notification = queue.pop(0)

            # Remove from index
            if notification.id in self._index:
                del self._index[notification.id]

            logger.debug(
                "Notification dequeued: %s (priority: %s)",
                notification.id,
                priority,
            )

            return notification

    async def dequeue_batch(
        self, priority: str = "high", limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Dequeue multiple notifications at once.

        Args:
            priority: Priority queue to dequeue from
            limit: Maximum number to dequeue

        Returns:
            List of notification dictionaries
        """
        notifications = []

        for _ in range(limit):
            notification = await self.dequeue(priority)
            if not notification:
                break

            notifications.append(notification.model_dump())

        logger.info(
            "Dequeued %d notifications from %s priority queue",
            len(notifications),
            priority,
        )

        return notifications

    async def get_queue_size(self, priority: str | None = None) -> int:
        """
        Get the size of queue(s).

        Args:
            priority: Specific priority queue, or None for total

        Returns:
            Number of queued notifications
        """
        async with self._lock:
            if priority:
                queue = self._get_queue(priority)
                return len(queue)
            else:
                return (
                    len(self._high_priority)
                    + len(self._normal_priority)
                    + len(self._low_priority)
                )

    async def peek(self, priority: str = "high") -> QueuedNotification | None:
        """
        View the next notification without removing it.

        Args:
            priority: Priority queue to peek at

        Returns:
            QueuedNotification or None if queue is empty
        """
        async with self._lock:
            queue = self._get_queue(priority)
            return queue[0] if queue else None

    async def remove(self, notification_id: UUID) -> bool:
        """
        Remove a specific notification from the queue.

        Args:
            notification_id: ID of notification to remove

        Returns:
            True if removed, False if not found
        """
        async with self._lock:
            if notification_id not in self._index:
                return False

            notification = self._index[notification_id]

            # Find and remove from appropriate queue
            for queue in [
                self._high_priority,
                self._normal_priority,
                self._low_priority,
            ]:
                if notification in queue:
                    queue.remove(notification)
                    break

            # Remove from index
            del self._index[notification_id]

            logger.debug("Notification removed from queue: %s", notification_id)
            return True

    async def clear(self, priority: str | None = None) -> int:
        """
        Clear queue(s).

        Args:
            priority: Specific priority queue to clear, or None for all

        Returns:
            Number of notifications cleared
        """
        async with self._lock:
            if priority:
                queue = self._get_queue(priority)
                count = len(queue)
                queue.clear()

                # Remove from index
                for notification in queue:
                    if notification.id in self._index:
                        del self._index[notification.id]

                logger.info("Cleared %d notifications from %s queue", count, priority)
                return count
            else:
                count = len(self._index)
                self._high_priority.clear()
                self._normal_priority.clear()
                self._low_priority.clear()
                self._index.clear()

                logger.info("Cleared all %d notifications from all queues", count)
                return count

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary of statistics
        """
        async with self._lock:
            # Count by notification type
            type_counts = defaultdict(int)
            for notification in self._index.values():
                type_counts[notification.notification_type] += 1

            # Age statistics
            now = datetime.utcnow()
            ages = [(now - n.queued_at).total_seconds() for n in self._index.values()]

            return {
                "total": len(self._index),
                "high_priority": len(self._high_priority),
                "normal_priority": len(self._normal_priority),
                "low_priority": len(self._low_priority),
                "by_type": dict(type_counts),
                "oldest_age_seconds": max(ages) if ages else 0,
                "average_age_seconds": sum(ages) / len(ages) if ages else 0,
            }

    def _get_queue(self, priority: str) -> list[QueuedNotification]:
        """
        Get the queue list for a priority level.

        Args:
            priority: Priority level name

        Returns:
            Queue list
        """
        if priority == "high":
            return self._high_priority
        elif priority == "normal":
            return self._normal_priority
        elif priority == "low":
            return self._low_priority
        else:
            return self._normal_priority  # Default
