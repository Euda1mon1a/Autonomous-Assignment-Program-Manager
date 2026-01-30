"""Batching engine for notifications."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.notifications.channels import NotificationPayload
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class NotificationBatch(BaseModel):
    """
    Represents a batch of notifications.

    Attributes:
        batch_key: Unique key for this batch
        notification_type: Type of notifications in batch
        recipient_ids: List of recipient UUIDs
        payloads: List of notification payloads
        channels: Channels to use for delivery
        created_at: When batch was created
        scheduled_send: When to send the batch
    """

    batch_key: str
    notification_type: str
    recipient_ids: list[UUID] = Field(default_factory=list)
    payloads: list[NotificationPayload] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_send: datetime | None = None


class BatchingEngine:
    """
    Aggregates similar notifications for batch delivery.

    Batching Strategy:
    1. Group similar notifications by batch_key
    2. Wait for batch window to collect notifications
    3. Aggregate into single notification or digest
    4. Deliver to all recipients at once

    Use Cases:
    - Daily digests (all updates from past 24 hours)
    - Shift reminder summaries (all shifts for the week)
    - Multiple assignment changes (combined into one notification)

    Batching Rules:
    - High priority notifications: No batching
    - Normal priority: 5-15 minute batch window
    - Low priority: 1-24 hour batch window
    """

    # Notification types that support batching
    BATCHABLE_TYPES = {
        NotificationType.ASSIGNMENT_CHANGED,
        NotificationType.SHIFT_REMINDER_24H,
        NotificationType.ABSENCE_APPROVED,
        NotificationType.ABSENCE_REJECTED,
    }

    # Default batch windows (in minutes) by type
    DEFAULT_WINDOWS = {
        NotificationType.ASSIGNMENT_CHANGED: 15,  # 15 minutes
        NotificationType.SHIFT_REMINDER_24H: 60,  # 1 hour
        NotificationType.ABSENCE_APPROVED: 30,  # 30 minutes
        NotificationType.ABSENCE_REJECTED: 30,  # 30 minutes
    }

    def __init__(self) -> None:
        """Initialize the batching engine."""
        # Active batches: batch_key -> NotificationBatch
        self._batches: dict[str, NotificationBatch] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    def should_batch(self, notification_type: NotificationType) -> bool:
        """
        Check if notification type supports batching.

        Args:
            notification_type: Type of notification

        Returns:
            True if batchable
        """
        return notification_type in self.BATCHABLE_TYPES

    async def add_to_batch(
        self,
        batch_key: str,
        payload: NotificationPayload,
        channels: list[str],
    ) -> None:
        """
        Add a notification to a batch.

        Args:
            batch_key: Unique key for grouping notifications
            payload: Notification payload
            channels: Channels to use for delivery
        """
        async with self._lock:
            if batch_key not in self._batches:
                # Create new batch
                notification_type = NotificationType(payload.notification_type)
                window_minutes = self.DEFAULT_WINDOWS.get(notification_type, 15)

                batch = NotificationBatch(
                    batch_key=batch_key,
                    notification_type=payload.notification_type,
                    channels=channels,
                    scheduled_send=datetime.utcnow()
                    + timedelta(minutes=window_minutes),
                )
                self._batches[batch_key] = batch

                logger.debug(
                    "Created new batch: %s (window: %d min)",
                    batch_key,
                    window_minutes,
                )

                # Add to batch
            batch = self._batches[batch_key]
            batch.recipient_ids.append(payload.recipient_id)
            batch.payloads.append(payload)

            logger.debug(
                "Added notification to batch %s (size: %d)",
                batch_key,
                len(batch.payloads),
            )

    async def get_ready_batches(self) -> list[dict[str, Any]]:
        """
        Get batches that are ready to send.

        Returns:
            List of batch dictionaries
        """
        async with self._lock:
            now = datetime.utcnow()
            ready = []

            for batch_key, batch in list(self._batches.items()):
                if batch.scheduled_send and batch.scheduled_send <= now:
                    ready.append(batch.model_dump())
                    logger.info(
                        "Batch ready for delivery: %s (size: %d)",
                        batch_key,
                        len(batch.payloads),
                    )

            return ready

    async def mark_batch_sent(self, batch_key: str) -> bool:
        """
        Mark a batch as sent and remove from active batches.

        Args:
            batch_key: Key of batch to mark sent

        Returns:
            True if batch was found and removed
        """
        async with self._lock:
            if batch_key in self._batches:
                del self._batches[batch_key]
                logger.debug("Batch marked as sent: %s", batch_key)
                return True

            return False

    async def aggregate_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        """
        Aggregate multiple notifications into a single message.

        Args:
            batch: Batch dictionary

        Returns:
            Aggregated data dictionary
        """
        notification_type = NotificationType(batch["notification_type"])
        payloads = [NotificationPayload(**p) for p in batch["payloads"]]

        # Different aggregation strategies by type
        if notification_type == NotificationType.ASSIGNMENT_CHANGED:
            return self._aggregate_assignment_changes(payloads)

        elif notification_type == NotificationType.SHIFT_REMINDER_24H:
            return self._aggregate_shift_reminders(payloads)

        elif notification_type in [
            NotificationType.ABSENCE_APPROVED,
            NotificationType.ABSENCE_REJECTED,
        ]:
            return self._aggregate_absence_notifications(payloads)

        else:
            # Default: Just combine bodies
            return {
                "count": len(payloads),
                "notifications": [p.data for p in payloads if p.data],
            }

    def _aggregate_assignment_changes(
        self, payloads: list[NotificationPayload]
    ) -> dict[str, Any]:
        """Aggregate multiple assignment changes."""
        changes = []
        for payload in payloads:
            if payload.data:
                changes.append(
                    {
                        "rotation": payload.data.get("rotation_name"),
                        "block": payload.data.get("block_name"),
                        "date_range": f"{payload.data.get('start_date')} to {payload.data.get('end_date')}",
                    }
                )

        return {
            "change_count": len(changes),
            "changes": changes,
            "aggregated_message": f"You have {len(changes)} assignment changes",
        }

    def _aggregate_shift_reminders(
        self, payloads: list[NotificationPayload]
    ) -> dict[str, Any]:
        """Aggregate multiple shift reminders."""
        shifts = []
        for payload in payloads:
            if payload.data:
                shifts.append(
                    {
                        "rotation": payload.data.get("rotation_name"),
                        "location": payload.data.get("location"),
                        "start_date": payload.data.get("start_date"),
                    }
                )

        return {
            "shift_count": len(shifts),
            "shifts": shifts,
            "aggregated_message": f"You have {len(shifts)} upcoming shifts",
        }

    def _aggregate_absence_notifications(
        self, payloads: list[NotificationPayload]
    ) -> dict[str, Any]:
        """Aggregate multiple absence notifications."""
        absences = []
        for payload in payloads:
            if payload.data:
                absences.append(
                    {
                        "type": payload.data.get("absence_type"),
                        "period": f"{payload.data.get('start_date')} to {payload.data.get('end_date')}",
                        "status": "approved"
                        if "approved" in payload.notification_type
                        else "rejected",
                    }
                )

        return {
            "absence_count": len(absences),
            "absences": absences,
            "aggregated_message": f"Status update for {len(absences)} absence requests",
        }

    async def get_pending_count(self) -> int:
        """
        Get count of pending batches.

        Returns:
            Number of pending batches
        """
        async with self._lock:
            return len(self._batches)

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get batching statistics.

        Returns:
            Dictionary of statistics
        """
        async with self._lock:
            total_notifications = sum(len(b.payloads) for b in self._batches.values())

            by_type = defaultdict(int)
            for batch in self._batches.values():
                by_type[batch.notification_type] += len(batch.payloads)

            return {
                "active_batches": len(self._batches),
                "total_notifications": total_notifications,
                "by_type": dict(by_type),
                "average_batch_size": (
                    total_notifications / len(self._batches) if self._batches else 0
                ),
            }

    async def clear(self) -> int:
        """
        Clear all batches.

        Returns:
            Number of batches cleared
        """
        async with self._lock:
            count = len(self._batches)
            self._batches.clear()
            logger.info("Cleared all %d batches", count)
            return count
