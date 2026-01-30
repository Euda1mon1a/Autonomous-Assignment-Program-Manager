"""Channel dispatcher for notifications."""

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.notifications.channels import DeliveryResult, NotificationPayload, get_channel

logger = get_logger(__name__)


class NotificationDispatcher:
    """
    Dispatches notifications to appropriate delivery channels.

    Handles parallel delivery to multiple channels, error handling,
    and result aggregation.
    """

    def __init__(self) -> None:
        """Initialize the dispatcher."""
        self._channel_cache: dict[str, Any] = {}

    async def dispatch(
        self,
        payload: NotificationPayload,
        channels: list[str],
        db: AsyncSession | None = None,
    ) -> list[DeliveryResult]:
        """
        Dispatch notification to multiple channels concurrently.

        Args:
            payload: The notification to deliver
            channels: List of channel names to use
            db: Optional database session for channels that need it

        Returns:
            List of DeliveryResult objects, one per channel
        """
        if not channels:
            logger.warning("No channels specified for notification %s", payload.id)
            return []

            # Create delivery tasks for each channel
        tasks = []
        for channel_name in channels:
            task = self._deliver_to_channel(
                payload=payload,
                channel_name=channel_name,
                db=db,
            )
            tasks.append(task)

            # Execute all deliveries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        final_results = []
        for channel_name, result in zip(channels, results):
            if isinstance(result, Exception):
                logger.error(
                    "Exception delivering to channel %s: %s",
                    channel_name,
                    result,
                    exc_info=result,
                )
                final_results.append(
                    DeliveryResult(
                        success=False,
                        channel=channel_name,
                        message=f"Exception: {str(result)}",
                    )
                )
            else:
                final_results.append(result)

                # Log summary
        success_count = sum(1 for r in final_results if r.success)
        logger.info(
            "Notification %s delivered: %d/%d channels successful",
            payload.id,
            success_count,
            len(channels),
        )

        return final_results

    async def _deliver_to_channel(
        self,
        payload: NotificationPayload,
        channel_name: str,
        db: AsyncSession | None,
    ) -> DeliveryResult:
        """
        Deliver notification to a single channel.

        Args:
            payload: The notification to deliver
            channel_name: Name of the channel
            db: Optional database session

        Returns:
            DeliveryResult for this channel
        """
        try:
            # Get channel instance (with caching)
            channel = self._get_channel(channel_name)
            if not channel:
                return DeliveryResult(
                    success=False,
                    channel=channel_name,
                    message=f"Channel not found: {channel_name}",
                )

                # Deliver through channel
            result = await channel.deliver(payload, db)
            return result

        except Exception as e:
            logger.error(
                "Error delivering to channel %s: %s",
                channel_name,
                e,
                exc_info=True,
            )
            return DeliveryResult(
                success=False,
                channel=channel_name,
                message=f"Delivery error: {str(e)}",
            )

    def _get_channel(self, channel_name: str) -> Any:
        """
        Get channel instance with caching.

        Args:
            channel_name: Name of the channel

        Returns:
            Channel instance or None
        """
        if channel_name not in self._channel_cache:
            channel = get_channel(channel_name)
            if channel:
                self._channel_cache[channel_name] = channel
            return channel

        return self._channel_cache[channel_name]

    def clear_cache(self) -> None:
        """Clear the channel cache."""
        self._channel_cache.clear()
