"""
Event Bus Implementation

Provides pub/sub messaging for real-time event distribution:
- Publish events to multiple subscribers
- Type-safe event handlers
- Async event processing
- Error handling and retry logic
- Dead letter queue for failed events

The event bus enables loose coupling between components.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.events.event_types import BaseEvent, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# Event Handler Types
# =============================================================================


EventHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]


class EventSubscription(BaseModel):
    """Represents a subscription to an event type."""

    subscriber_id: str
    event_type: str
    handler: Any  # EventHandler (can't serialize Callable)
    created_at: datetime

    class Config:
        arbitrary_types_allowed = True


class DeadLetterEvent(BaseModel):
    """Event that failed processing."""

    event_id: str
    event_type: str
    event_data: dict[str, Any]
    error_message: str
    retry_count: int
    failed_at: datetime


# =============================================================================
# Event Bus
# =============================================================================


class EventBus:
    """
    Event Bus for publishing and subscribing to events.

    Implements the pub/sub pattern for loose coupling between components.
    """

    def __init__(self, enable_retry: bool = True, max_retries: int = 3):
        """
        Initialize Event Bus.

        Args:
            enable_retry: Enable automatic retry on failures
            max_retries: Maximum number of retry attempts
        """
        self._subscriptions: dict[str, list[EventSubscription]] = defaultdict(list)
        self._enable_retry = enable_retry
        self._max_retries = max_retries
        self._dead_letter_queue: list[DeadLetterEvent] = []
        self._subscriber_counter = 0

    def subscribe(
        self,
        event_type: str | EventType,
        handler: EventHandler,
        subscriber_id: str | None = None,
    ) -> str:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
            subscriber_id: Optional custom subscriber ID

        Returns:
            Subscription ID

        Example:
            async def on_schedule_created(event: ScheduleCreatedEvent):
                print(f"New schedule: {event.schedule_id}")

            bus.subscribe(EventType.SCHEDULE_CREATED, on_schedule_created)
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value

        if not subscriber_id:
            self._subscriber_counter += 1
            subscriber_id = f"subscriber-{self._subscriber_counter}"

        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_type=event_type,
            handler=handler,
            created_at=datetime.utcnow(),
        )

        self._subscriptions[event_type].append(subscription)

        logger.info(
            f"Subscriber {subscriber_id} registered for {event_type} "
            f"({len(self._subscriptions[event_type])} total subscribers)"
        )

        return subscriber_id

    def subscribe_to_multiple(
        self,
        event_types: list[str | EventType],
        handler: EventHandler,
        subscriber_id: str | None = None,
    ) -> str:
        """
        Subscribe to multiple event types with one handler.

        Args:
            event_types: List of event types
            handler: Handler function
            subscriber_id: Optional subscriber ID

        Returns:
            Subscriber ID
        """
        for event_type in event_types:
            subscriber_id = self.subscribe(event_type, handler, subscriber_id)

        return subscriber_id

    def unsubscribe(self, subscriber_id: str, event_type: str | None = None):
        """
        Unsubscribe from events.

        Args:
            subscriber_id: Subscriber to remove
            event_type: Optional specific event type (if None, remove from all)
        """
        if event_type:
            self._subscriptions[event_type] = [
                sub
                for sub in self._subscriptions[event_type]
                if sub.subscriber_id != subscriber_id
            ]
            logger.info(f"Unsubscribed {subscriber_id} from {event_type}")
        else:
            # Unsubscribe from all event types
            for evt_type in list(self._subscriptions.keys()):
                self._subscriptions[evt_type] = [
                    sub
                    for sub in self._subscriptions[evt_type]
                    if sub.subscriber_id != subscriber_id
                ]
            logger.info(f"Unsubscribed {subscriber_id} from all events")

    async def publish(self, event: BaseEvent, async_mode: bool = True):
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
            async_mode: If True, handlers run concurrently; if False, sequentially

        Example:
            event = ScheduleCreatedEvent(
                aggregate_id="schedule-123",
                schedule_id="schedule-123",
                created_by="user-456"
            )
            await bus.publish(event)
        """
        event_type = event.metadata.event_type
        subscribers = self._subscriptions.get(event_type, [])

        if not subscribers:
            logger.debug(f"No subscribers for {event_type}")
            return

        logger.info(f"Publishing {event_type} to {len(subscribers)} subscriber(s)")

        if async_mode:
            # Run all handlers concurrently
            tasks = [self._handle_event_with_retry(sub, event) for sub in subscribers]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run handlers sequentially
            for sub in subscribers:
                await self._handle_event_with_retry(sub, event)

    async def publish_batch(self, events: list[BaseEvent]):
        """
        Publish multiple events.

        Args:
            events: List of events to publish
        """
        for event in events:
            await self.publish(event)

    async def _handle_event_with_retry(
        self,
        subscription: EventSubscription,
        event: BaseEvent,
    ):
        """
        Handle event with retry logic.

        Args:
            subscription: Subscription info
            event: Event to handle
        """
        retry_count = 0
        last_error = None

        while retry_count <= self._max_retries:
            try:
                await subscription.handler(event)
                logger.debug(
                    f"Event {event.metadata.event_type} "
                    f"handled by {subscription.subscriber_id}"
                )
                return  # Success
            except Exception as e:
                last_error = e
                retry_count += 1

                logger.warning(
                    f"Error handling {event.metadata.event_type} "
                    f"by {subscription.subscriber_id} "
                    f"(attempt {retry_count}/{self._max_retries + 1}): {e}"
                )

                if retry_count <= self._max_retries and self._enable_retry:
                    # Exponential backoff
                    await asyncio.sleep(2**retry_count)
                else:
                    break

        # All retries failed
        logger.error(
            f"Failed to handle {event.metadata.event_type} "
            f"by {subscription.subscriber_id} after {retry_count} attempts: "
            f"{last_error}"
        )

        # Add to dead letter queue
        dead_letter = DeadLetterEvent(
            event_id=event.metadata.event_id,
            event_type=event.metadata.event_type,
            event_data=event.to_dict(),
            error_message=str(last_error),
            retry_count=retry_count,
            failed_at=datetime.utcnow(),
        )
        self._dead_letter_queue.append(dead_letter)

    def get_subscriptions(self, event_type: str | None = None) -> list[dict]:
        """
        Get list of current subscriptions.

        Args:
            event_type: Optional filter by event type

        Returns:
            List of subscription info
        """
        if event_type:
            subs = self._subscriptions.get(event_type, [])
            return [
                {
                    "subscriber_id": sub.subscriber_id,
                    "event_type": sub.event_type,
                    "created_at": sub.created_at,
                }
                for sub in subs
            ]

        # All subscriptions
        all_subs = []
        for event_type, subs in self._subscriptions.items():
            for sub in subs:
                all_subs.append(
                    {
                        "subscriber_id": sub.subscriber_id,
                        "event_type": sub.event_type,
                        "created_at": sub.created_at,
                    }
                )
        return all_subs

    def get_dead_letter_queue(self) -> list[DeadLetterEvent]:
        """Get events that failed processing."""
        return self._dead_letter_queue.copy()

    def clear_dead_letter_queue(self):
        """Clear the dead letter queue."""
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        logger.info(f"Cleared {count} events from dead letter queue")

    async def replay_dead_letter_event(self, event_id: str) -> bool:
        """
        Retry processing a failed event.

        Args:
            event_id: ID of the failed event

        Returns:
            True if retry succeeded, False otherwise
        """
        # Find the event in dead letter queue
        dead_letter = None
        for dle in self._dead_letter_queue:
            if dle.event_id == event_id:
                dead_letter = dle
                break

        if not dead_letter:
            logger.warning(f"Event {event_id} not found in dead letter queue")
            return False

        # Reconstruct event
        from app.events.event_types import get_event_class

        try:
            event_class = get_event_class(dead_letter.event_type)
            event = event_class.from_dict(dead_letter.event_data)

            # Try to publish again
            await self.publish(event)

            # Remove from dead letter queue
            self._dead_letter_queue.remove(dead_letter)

            logger.info(f"Successfully replayed event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to replay event {event_id}: {e}")
            return False


# =============================================================================
# Global Event Bus Instance
# =============================================================================


_event_bus_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get global EventBus instance (singleton).

    Returns:
        EventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


# =============================================================================
# Convenience Decorators
# =============================================================================


def event_handler(event_type: str | EventType):
    """
    Decorator to register an event handler.

    Example:
        @event_handler(EventType.SCHEDULE_CREATED)
        async def on_schedule_created(event: ScheduleCreatedEvent):
            print(f"Schedule created: {event.schedule_id}")
    """

    def decorator(func: EventHandler):
        bus = get_event_bus()
        bus.subscribe(event_type, func, subscriber_id=func.__name__)
        return func

    return decorator


# =============================================================================
# Event Bus Statistics
# =============================================================================


def get_event_bus_stats(bus: EventBus | None = None) -> dict[str, Any]:
    """
    Get statistics about the event bus.

    Args:
        bus: Optional EventBus instance (uses global if None)

    Returns:
        Dictionary with statistics
    """
    if bus is None:
        bus = get_event_bus()

    stats = {
        "total_subscriptions": 0,
        "subscriptions_by_type": {},
        "dead_letter_count": len(bus._dead_letter_queue),
    }

    for event_type, subs in bus._subscriptions.items():
        stats["subscriptions_by_type"][event_type] = len(subs)
        stats["total_subscriptions"] += len(subs)

    return stats
