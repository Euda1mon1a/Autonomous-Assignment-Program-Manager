"""Main notification engine orchestrator."""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.notifications.channels import DeliveryResult, NotificationPayload
from app.notifications.engine.batching import BatchingEngine
from app.notifications.engine.deduplication import DeduplicationEngine
from app.notifications.engine.dispatcher import NotificationDispatcher
from app.notifications.engine.preference_manager import PreferenceManager
from app.notifications.engine.priority_handler import PriorityHandler
from app.notifications.engine.queue_manager import NotificationQueueManager
from app.notifications.engine.rate_limiter import NotificationRateLimiter
from app.notifications.engine.retry_handler import RetryHandler
from app.notifications.notification_types import NotificationType, render_notification

logger = get_logger(__name__)


class NotificationEngine:
    """
    Main notification engine orchestrator.

    Coordinates all notification subsystems including queueing, batching,
    deduplication, priority handling, and delivery through multiple channels.

    Architecture:
        1. Receive notification request
        2. Check deduplication
        3. Apply priority rules
        4. Check rate limits
        5. Queue for batching (if applicable)
        6. Dispatch to appropriate channels
        7. Handle retries on failure

    Attributes:
        queue_manager: Manages notification queuing
        dispatcher: Handles channel dispatch
        priority_handler: Manages priority levels
        deduplication: Prevents duplicate notifications
        batching: Aggregates similar notifications
        rate_limiter: Enforces rate limits
        retry_handler: Handles failed deliveries
        preference_manager: Manages user preferences
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the notification engine.

        Args:
            db: Database session for persistence
        """
        self.db = db
        self.queue_manager = NotificationQueueManager()
        self.dispatcher = NotificationDispatcher()
        self.priority_handler = PriorityHandler()
        self.deduplication = DeduplicationEngine()
        self.batching = BatchingEngine()
        self.rate_limiter = NotificationRateLimiter()
        self.retry_handler = RetryHandler()
        self.preference_manager = PreferenceManager(db)

    async def send_notification(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        data: dict[str, Any],
        channels: list[str] | None = None,
        priority: str | None = None,
        batch_key: str | None = None,
    ) -> list[DeliveryResult]:
        """
        Send a notification through the engine pipeline.

        Args:
            recipient_id: UUID of the recipient
            notification_type: Type of notification
            data: Data for template rendering
            channels: Optional list of specific channels
            priority: Optional priority override
            batch_key: Optional key for batching similar notifications

        Returns:
            List of DeliveryResult objects
        """
        # Step 1: Render the notification template
        rendered = render_notification(notification_type, data)
        if not rendered:
            logger.warning(
                "No template found for notification type: %s", notification_type
            )
            return [
                DeliveryResult(
                    success=False,
                    channel="template",
                    message=f"Template not found: {notification_type}",
                )
            ]

        # Step 2: Check deduplication
        if self.deduplication.is_duplicate(
            recipient_id, notification_type, data, window_minutes=60
        ):
            logger.debug(
                "Duplicate notification suppressed: %s for user %s",
                notification_type.value,
                recipient_id,
            )
            return [
                DeliveryResult(
                    success=True,
                    channel="deduplication",
                    message="Notification deduplicated",
                )
            ]

        # Step 3: Get user preferences
        preferences = await self.preference_manager.get_preferences(recipient_id)
        if not await self.preference_manager.should_send(
            preferences, notification_type
        ):
            logger.info(
                "Notification skipped due to user preferences: %s for user %s",
                notification_type.value,
                recipient_id,
            )
            return []

        # Step 4: Determine priority
        final_priority = priority or rendered.get("priority", "normal")
        priority_score = self.priority_handler.calculate_priority_score(
            notification_type, final_priority, data
        )

        # Step 5: Determine target channels
        target_channels = channels or rendered.get("channels", ["in_app"])
        enabled_channels = await self.preference_manager.get_enabled_channels(
            preferences
        )
        target_channels = [c for c in target_channels if c in enabled_channels]

        if not target_channels:
            logger.debug("No enabled channels for user %s", recipient_id)
            return []

        # Step 6: Check rate limits
        if not await self.rate_limiter.check_rate_limit(
            recipient_id, notification_type
        ):
            logger.warning(
                "Rate limit exceeded for user %s, notification type %s",
                recipient_id,
                notification_type.value,
            )
            # Queue for later delivery
            await self.queue_manager.enqueue(
                recipient_id=recipient_id,
                notification_type=notification_type,
                data=data,
                channels=target_channels,
                priority=priority_score,
            )
            return [
                DeliveryResult(
                    success=True,
                    channel="queue",
                    message="Queued due to rate limit",
                )
            ]

        # Step 7: Create notification payload
        payload = NotificationPayload(
            recipient_id=recipient_id,
            notification_type=notification_type.value,
            subject=rendered["subject"],
            body=rendered["body"],
            data=data,
            priority=final_priority,
        )

        # Step 8: Check if batching is enabled
        if batch_key and self.batching.should_batch(notification_type):
            await self.batching.add_to_batch(
                batch_key=batch_key,
                payload=payload,
                channels=target_channels,
            )
            logger.debug(
                "Notification added to batch: %s (key: %s)",
                notification_type.value,
                batch_key,
            )
            return [
                DeliveryResult(
                    success=True,
                    channel="batch",
                    message="Added to batch for delivery",
                )
            ]

        # Step 9: Dispatch immediately
        results = await self.dispatcher.dispatch(
            payload=payload,
            channels=target_channels,
            db=self.db,
        )

        # Step 10: Handle failures with retry
        for result in results:
            if not result.success:
                await self.retry_handler.schedule_retry(
                    payload=payload,
                    channel=result.channel,
                    error=result.message,
                )

        # Step 11: Record for deduplication
        self.deduplication.record_sent(recipient_id, notification_type, data)

        return results

    async def send_bulk(
        self,
        recipient_ids: list[UUID],
        notification_type: NotificationType,
        data: dict[str, Any],
        channels: list[str] | None = None,
    ) -> dict[str, list[DeliveryResult]]:
        """
        Send the same notification to multiple recipients.

        Args:
            recipient_ids: List of recipient UUIDs
            notification_type: Type of notification
            data: Data for template rendering
            channels: Optional list of specific channels

        Returns:
            Dictionary mapping recipient_id to delivery results
        """
        # Batch load preferences to avoid N+1 queries
        await self.preference_manager.preload_preferences(recipient_ids)

        # Send notifications concurrently
        tasks = [
            self.send_notification(
                recipient_id=recipient_id,
                notification_type=notification_type,
                data=data,
                channels=channels,
            )
            for recipient_id in recipient_ids
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Build results dictionary
        results = {}
        for recipient_id, result in zip(recipient_ids, results_list):
            if isinstance(result, Exception):
                logger.error(
                    "Error sending notification to %s: %s",
                    recipient_id,
                    result,
                    exc_info=result,
                )
                results[str(recipient_id)] = [
                    DeliveryResult(
                        success=False,
                        channel="error",
                        message=str(result),
                    )
                ]
            else:
                results[str(recipient_id)] = result

        return results

    async def process_queue(self) -> int:
        """
        Process queued notifications.

        This should be called periodically (e.g., via Celery beat) to process
        notifications that were queued due to rate limiting or batching.

        Returns:
            Number of notifications processed
        """
        processed = 0

        # Process high-priority queue first
        for priority in ["high", "normal", "low"]:
            items = await self.queue_manager.dequeue_batch(priority=priority, limit=100)

            for item in items:
                try:
                    await self.send_notification(
                        recipient_id=item["recipient_id"],
                        notification_type=NotificationType(item["notification_type"]),
                        data=item["data"],
                        channels=item.get("channels"),
                    )
                    processed += 1
                except Exception as e:
                    logger.error(
                        "Error processing queued notification: %s",
                        e,
                        exc_info=True,
                    )

        return processed

    async def process_batches(self) -> int:
        """
        Process and send batched notifications.

        Returns:
            Number of batches processed
        """
        batches = await self.batching.get_ready_batches()
        processed = 0

        for batch in batches:
            try:
                # Create aggregated notification
                aggregated = await self.batching.aggregate_batch(batch)

                # Send to all recipients in batch
                for recipient_id in batch["recipient_ids"]:
                    await self.send_notification(
                        recipient_id=recipient_id,
                        notification_type=NotificationType(batch["notification_type"]),
                        data=aggregated,
                        channels=batch["channels"],
                    )

                processed += 1
                await self.batching.mark_batch_sent(batch["batch_key"])

            except Exception as e:
                logger.error("Error processing batch: %s", e, exc_info=True)

        return processed

    async def process_retries(self) -> int:
        """
        Process failed notifications for retry.

        Returns:
            Number of retries attempted
        """
        return await self.retry_handler.process_retries(self)

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get notification engine statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "queue_size": await self.queue_manager.get_queue_size(),
            "pending_batches": await self.batching.get_pending_count(),
            "pending_retries": await self.retry_handler.get_pending_count(),
            "deduplication_cache_size": self.deduplication.get_cache_size(),
            "timestamp": datetime.utcnow().isoformat(),
        }
