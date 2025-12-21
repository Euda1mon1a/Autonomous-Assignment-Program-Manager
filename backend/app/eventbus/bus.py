"""
Async Event Bus Implementation

Provides both in-memory and distributed event bus capabilities with:
- Local and Redis pub/sub modes
- Wildcard topic matching
- Event persistence and replay
- Dead letter queue
- Event filtering and transformation
- Automatic retry logic
"""

import asyncio
import fnmatch
import json
import logging
import pickle
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

import redis.asyncio as redis
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


# =============================================================================
# Event Bus Configuration
# =============================================================================


class EventBusMode(str, Enum):
    """Event bus operating mode."""

    IN_MEMORY = "in_memory"  # Local events only (single process)
    DISTRIBUTED = "distributed"  # Redis pub/sub (multi-process)
    HYBRID = "hybrid"  # Both in-memory and distributed


class EventBusException(AppException):
    """Base exception for event bus errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


# =============================================================================
# Event Models
# =============================================================================


class EventMetadata(BaseModel):
    """Event metadata for tracking and auditing."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    version: str = "1.0"
    retry_count: int = 0
    content_type: str = "application/json"


class Event(BaseModel):
    """
    Base event class for all events in the system.

    Attributes:
        topic: Event topic/channel (supports wildcards in subscriptions)
        data: Event payload (any JSON-serializable data)
        metadata: Event metadata for tracking
    """

    topic: str
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "topic": self.topic,
            "data": self.data,
            "metadata": self.metadata.model_dump(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            topic=data["topic"],
            data=data.get("data", {}),
            metadata=EventMetadata(**data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# =============================================================================
# Event Filtering and Transformation
# =============================================================================


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]
EventFilterFunc = Callable[[Event], bool]
EventTransformFunc = Callable[[Event], Event]


class EventFilter:
    """
    Event filtering system for selective event processing.

    Filters can be based on:
    - Topic patterns
    - Data content
    - Metadata attributes
    - Custom filter functions
    """

    def __init__(self):
        """Initialize event filter."""
        self._filters: list[EventFilterFunc] = []

    def add_filter(self, filter_func: EventFilterFunc) -> None:
        """
        Add a filter function.

        Args:
            filter_func: Function that returns True if event should be processed
        """
        self._filters.append(filter_func)

    def filter_by_data(self, key: str, value: Any) -> None:
        """
        Filter events by data field value.

        Args:
            key: Data field key
            value: Expected value
        """
        def filter_func(event: Event) -> bool:
            return event.data.get(key) == value

        self.add_filter(filter_func)

    def filter_by_metadata(self, key: str, value: Any) -> None:
        """
        Filter events by metadata field value.

        Args:
            key: Metadata field key
            value: Expected value
        """
        def filter_func(event: Event) -> bool:
            return getattr(event.metadata, key, None) == value

        self.add_filter(filter_func)

    def filter_by_source(self, source: str) -> None:
        """
        Filter events by source.

        Args:
            source: Event source to filter
        """
        self.filter_by_metadata("source", source)

    def should_process(self, event: Event) -> bool:
        """
        Check if event should be processed based on all filters.

        Args:
            event: Event to check

        Returns:
            True if all filters pass, False otherwise
        """
        return all(f(event) for f in self._filters)


class EventTransformer:
    """
    Event transformation system for modifying events.

    Transformations can:
    - Enrich event data
    - Modify payloads
    - Add metadata
    - Transform event structure
    """

    def __init__(self):
        """Initialize event transformer."""
        self._transformers: list[EventTransformFunc] = []

    def add_transformer(self, transform_func: EventTransformFunc) -> None:
        """
        Add a transformation function.

        Args:
            transform_func: Function that transforms an event
        """
        self._transformers.append(transform_func)

    def enrich_data(self, enrichments: dict[str, Any]) -> None:
        """
        Enrich event data with additional fields.

        Args:
            enrichments: Dictionary of fields to add to event data
        """
        def transform_func(event: Event) -> Event:
            event.data.update(enrichments)
            return event

        self.add_transformer(transform_func)

    def transform(self, event: Event) -> Event:
        """
        Apply all transformations to an event.

        Args:
            event: Event to transform

        Returns:
            Transformed event
        """
        for transformer in self._transformers:
            event = transformer(event)
        return event


# =============================================================================
# Event Subscription
# =============================================================================


class EventSubscription(BaseModel):
    """
    Represents a subscription to an event topic.

    Attributes:
        subscription_id: Unique subscription identifier
        topic_pattern: Topic pattern (supports wildcards)
        handler: Event handler function
        filter: Optional event filter
        transformer: Optional event transformer
        created_at: Subscription creation timestamp
    """

    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic_pattern: str
    handler: Any  # EventHandler (can't serialize Callable)
    filter: Optional[EventFilter] = None
    transformer: Optional[EventTransformer] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    max_retries: int = 3
    dead_letter_enabled: bool = True

    class Config:
        arbitrary_types_allowed = True

    def matches_topic(self, topic: str) -> bool:
        """
        Check if topic matches subscription pattern.

        Supports:
        - Exact match: "user.created"
        - Wildcard: "user.*" matches "user.created", "user.updated"
        - Multi-level wildcard: "user.**" matches "user.profile.updated"
        - Regex: "user\\.\\d+" matches "user.123"

        Args:
            topic: Topic to check

        Returns:
            True if topic matches pattern
        """
        # Exact match
        if self.topic_pattern == topic:
            return True

        # Convert glob pattern to regex
        if "*" in self.topic_pattern:
            # Replace * with appropriate regex
            pattern = self.topic_pattern.replace(".", r"\.")
            pattern = pattern.replace("**", ".*")  # Multi-level wildcard
            pattern = pattern.replace("*", r"[^.]+")  # Single-level wildcard
            pattern = f"^{pattern}$"
            return bool(re.match(pattern, topic))

        # Try as direct regex
        try:
            return bool(re.match(self.topic_pattern, topic))
        except re.error:
            return False


# =============================================================================
# Dead Letter Queue
# =============================================================================


class DeadLetterEvent(BaseModel):
    """Event that failed processing after all retries."""

    event_id: str
    topic: str
    event_data: dict[str, Any]
    error_message: str
    retry_count: int
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_id: str


class DeadLetterQueue:
    """
    Dead letter queue for handling failed events.

    Stores events that failed processing after all retry attempts.
    Supports:
    - Manual replay
    - Automatic reprocessing
    - TTL-based expiration
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize dead letter queue.

        Args:
            redis_client: Optional Redis client for distributed DLQ
        """
        self._memory_queue: list[DeadLetterEvent] = []
        self._redis_client = redis_client
        self._dlq_key = "eventbus:deadletter"

    async def add(self, event: Event, error: Exception, subscription_id: str) -> None:
        """
        Add failed event to dead letter queue.

        Args:
            event: Failed event
            error: Exception that caused failure
            subscription_id: Subscription that failed
        """
        dead_letter = DeadLetterEvent(
            event_id=event.metadata.event_id,
            topic=event.topic,
            event_data=event.to_dict(),
            error_message=str(error),
            retry_count=event.metadata.retry_count,
            subscription_id=subscription_id,
        )

        # Add to memory
        self._memory_queue.append(dead_letter)

        # Add to Redis if available
        if self._redis_client:
            try:
                data = dead_letter.model_dump_json()
                await self._redis_client.lpush(self._dlq_key, data)
                # Set TTL on the list (7 days)
                await self._redis_client.expire(self._dlq_key, 7 * 24 * 3600)
            except Exception as e:
                logger.error(f"Failed to add to Redis DLQ: {e}")

        logger.error(
            f"Event {event.metadata.event_id} added to dead letter queue. "
            f"Topic: {event.topic}, Error: {error}, Retries: {event.metadata.retry_count}"
        )

    async def get_all(self) -> list[DeadLetterEvent]:
        """
        Get all events in dead letter queue.

        Returns:
            List of dead letter events
        """
        events = self._memory_queue.copy()

        # Get from Redis if available
        if self._redis_client:
            try:
                redis_events = await self._redis_client.lrange(self._dlq_key, 0, -1)
                for event_data in redis_events:
                    if isinstance(event_data, bytes):
                        event_data = event_data.decode()
                    dle = DeadLetterEvent.model_validate_json(event_data)
                    if dle not in events:
                        events.append(dle)
            except Exception as e:
                logger.error(f"Failed to get from Redis DLQ: {e}")

        return events

    async def get_by_topic(self, topic: str) -> list[DeadLetterEvent]:
        """
        Get dead letter events for a specific topic.

        Args:
            topic: Topic to filter

        Returns:
            List of dead letter events for topic
        """
        all_events = await self.get_all()
        return [e for e in all_events if e.topic == topic]

    async def remove(self, event_id: str) -> bool:
        """
        Remove event from dead letter queue.

        Args:
            event_id: Event ID to remove

        Returns:
            True if event was removed
        """
        # Remove from memory
        removed = False
        for event in self._memory_queue:
            if event.event_id == event_id:
                self._memory_queue.remove(event)
                removed = True
                break

        # Remove from Redis if available
        if self._redis_client and removed:
            try:
                # This is inefficient but Redis lists don't support removal by value easily
                all_events = await self._redis_client.lrange(self._dlq_key, 0, -1)
                await self._redis_client.delete(self._dlq_key)

                for event_data in all_events:
                    if isinstance(event_data, bytes):
                        event_data = event_data.decode()
                    dle = DeadLetterEvent.model_validate_json(event_data)
                    if dle.event_id != event_id:
                        await self._redis_client.lpush(self._dlq_key, event_data)
            except Exception as e:
                logger.error(f"Failed to remove from Redis DLQ: {e}")

        return removed

    async def clear(self) -> int:
        """
        Clear all events from dead letter queue.

        Returns:
            Number of events cleared
        """
        count = len(self._memory_queue)
        self._memory_queue.clear()

        if self._redis_client:
            try:
                await self._redis_client.delete(self._dlq_key)
            except Exception as e:
                logger.error(f"Failed to clear Redis DLQ: {e}")

        logger.info(f"Cleared {count} events from dead letter queue")
        return count


# =============================================================================
# Event Persistence
# =============================================================================


class EventStore:
    """
    Event persistence layer for event replay.

    Stores events in Redis with:
    - Topic-based indexing
    - Time-based queries
    - Event replay capability
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize event store.

        Args:
            redis_client: Redis client for persistence
        """
        self._redis = redis_client
        self._store_key_prefix = "eventbus:events"
        self._index_key_prefix = "eventbus:index"

    async def store(self, event: Event) -> bool:
        """
        Store event for replay capability.

        Args:
            event: Event to store

        Returns:
            True if stored successfully
        """
        try:
            # Store event data
            event_key = f"{self._store_key_prefix}:{event.metadata.event_id}"
            event_data = event.to_json()
            await self._redis.setex(event_key, 30 * 24 * 3600, event_data)  # 30 days TTL

            # Add to topic index
            topic_index = f"{self._index_key_prefix}:topic:{event.topic}"
            timestamp_score = event.metadata.timestamp.timestamp()
            await self._redis.zadd(
                topic_index,
                {event.metadata.event_id: timestamp_score}
            )
            await self._redis.expire(topic_index, 30 * 24 * 3600)

            # Add to global time index
            time_index = f"{self._index_key_prefix}:time"
            await self._redis.zadd(
                time_index,
                {event.metadata.event_id: timestamp_score}
            )
            await self._redis.expire(time_index, 30 * 24 * 3600)

            return True

        except Exception as e:
            logger.error(f"Failed to store event {event.metadata.event_id}: {e}")
            return False

    async def replay(
        self,
        topic: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[Event]:
        """
        Replay events from store.

        Args:
            topic: Optional topic filter
            from_timestamp: Start time for replay
            to_timestamp: End time for replay
            limit: Maximum number of events to replay

        Returns:
            List of events to replay
        """
        try:
            # Determine which index to use
            if topic:
                index_key = f"{self._index_key_prefix}:topic:{topic}"
            else:
                index_key = f"{self._index_key_prefix}:time"

            # Determine time range
            min_score = from_timestamp.timestamp() if from_timestamp else "-inf"
            max_score = to_timestamp.timestamp() if to_timestamp else "+inf"

            # Get event IDs from index
            event_ids = await self._redis.zrangebyscore(
                index_key,
                min_score,
                max_score,
                start=0,
                num=limit
            )

            # Fetch events
            events = []
            for event_id in event_ids:
                if isinstance(event_id, bytes):
                    event_id = event_id.decode()

                event_key = f"{self._store_key_prefix}:{event_id}"
                event_data = await self._redis.get(event_key)

                if event_data:
                    if isinstance(event_data, bytes):
                        event_data = event_data.decode()
                    event = Event.from_json(event_data)
                    events.append(event)

            logger.info(f"Replayed {len(events)} events from store")
            return events

        except Exception as e:
            logger.error(f"Failed to replay events: {e}")
            return []

    async def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get a specific event by ID.

        Args:
            event_id: Event ID to retrieve

        Returns:
            Event if found, None otherwise
        """
        try:
            event_key = f"{self._store_key_prefix}:{event_id}"
            event_data = await self._redis.get(event_key)

            if event_data:
                if isinstance(event_data, bytes):
                    event_data = event_data.decode()
                return Event.from_json(event_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            return None


# =============================================================================
# Main Event Bus
# =============================================================================


class EventBus:
    """
    Async Event Bus with in-memory and distributed support.

    Features:
    - In-memory event bus for local events
    - Distributed event bus with Redis pub/sub
    - Wildcard topic matching
    - Event replay capability
    - Dead letter handling
    - Event persistence
    - Event filtering and transformation

    Example:
        # Create distributed event bus
        bus = EventBus(mode=EventBusMode.DISTRIBUTED, enable_persistence=True)
        await bus.start()

        # Subscribe to events with wildcard
        async def handler(event: Event):
            print(f"Received: {event.topic} - {event.data}")

        await bus.subscribe("user.*", handler)

        # Publish event
        event = Event(topic="user.created", data={"user_id": 123})
        await bus.publish(event)

        # Replay events
        events = await bus.replay(topic="user.created", from_timestamp=yesterday)

        # Stop event bus
        await bus.stop()
    """

    def __init__(
        self,
        mode: EventBusMode = EventBusMode.IN_MEMORY,
        enable_persistence: bool = False,
        enable_dead_letter: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize event bus.

        Args:
            mode: Event bus operating mode (in_memory, distributed, hybrid)
            enable_persistence: Enable event persistence for replay
            enable_dead_letter: Enable dead letter queue
            max_retries: Maximum retry attempts for failed handlers
        """
        self._mode = mode
        self._enable_persistence = enable_persistence
        self._enable_dead_letter = enable_dead_letter
        self._max_retries = max_retries

        # Subscriptions
        self._subscriptions: dict[str, list[EventSubscription]] = defaultdict(list)
        self._subscription_lock = asyncio.Lock()

        # Redis components
        self._redis_client: Optional[redis.Redis] = None
        self._redis_pubsub: Optional[redis.client.PubSub] = None
        self._pubsub_task: Optional[asyncio.Task] = None

        # Event store and dead letter queue
        self._event_store: Optional[EventStore] = None
        self._dead_letter_queue: Optional[DeadLetterQueue] = None

        # Settings
        self._settings = get_settings()

        # Running state
        self._running = False

    async def start(self) -> None:
        """
        Start the event bus.

        Initializes Redis connections and starts pub/sub listener if in distributed mode.
        """
        if self._running:
            logger.warning("Event bus already running")
            return

        logger.info(f"Starting event bus in {self._mode} mode")

        # Initialize Redis for distributed or hybrid mode
        if self._mode in (EventBusMode.DISTRIBUTED, EventBusMode.HYBRID):
            await self._init_redis()

        # Initialize event store if persistence is enabled
        if self._enable_persistence and self._redis_client:
            self._event_store = EventStore(self._redis_client)
            logger.info("Event persistence enabled")

        # Initialize dead letter queue
        if self._enable_dead_letter:
            self._dead_letter_queue = DeadLetterQueue(self._redis_client)
            logger.info("Dead letter queue enabled")

        # Start pub/sub listener for distributed mode
        if self._mode in (EventBusMode.DISTRIBUTED, EventBusMode.HYBRID):
            await self._start_pubsub_listener()

        self._running = True
        logger.info("Event bus started successfully")

    async def stop(self) -> None:
        """
        Stop the event bus.

        Closes Redis connections and stops pub/sub listener.
        """
        if not self._running:
            return

        logger.info("Stopping event bus")

        # Stop pub/sub listener
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass

        # Close Redis connections
        if self._redis_pubsub:
            await self._redis_pubsub.close()

        if self._redis_client:
            await self._redis_client.close()

        self._running = False
        logger.info("Event bus stopped")

    async def subscribe(
        self,
        topic_pattern: str,
        handler: EventHandler,
        event_filter: Optional[EventFilter] = None,
        event_transformer: Optional[EventTransformer] = None,
        max_retries: Optional[int] = None,
    ) -> str:
        """
        Subscribe to events matching a topic pattern.

        Args:
            topic_pattern: Topic pattern (supports wildcards)
            handler: Async function to handle events
            event_filter: Optional event filter
            event_transformer: Optional event transformer
            max_retries: Optional max retries (uses default if None)

        Returns:
            Subscription ID

        Example:
            # Exact match
            await bus.subscribe("user.created", handler)

            # Wildcard match
            await bus.subscribe("user.*", handler)

            # Multi-level wildcard
            await bus.subscribe("user.**", handler)

            # With filter
            filter = EventFilter()
            filter.filter_by_data("status", "active")
            await bus.subscribe("user.*", handler, event_filter=filter)
        """
        async with self._subscription_lock:
            subscription = EventSubscription(
                topic_pattern=topic_pattern,
                handler=handler,
                filter=event_filter,
                transformer=event_transformer,
                max_retries=max_retries or self._max_retries,
            )

            # Add to subscriptions
            self._subscriptions[topic_pattern].append(subscription)

            # Subscribe to Redis channel if distributed
            if self._mode in (EventBusMode.DISTRIBUTED, EventBusMode.HYBRID):
                if self._redis_pubsub:
                    # Subscribe to actual topics (we'll filter with pattern matching)
                    await self._redis_pubsub.psubscribe(f"eventbus:{topic_pattern}")

            logger.info(
                f"Subscription {subscription.subscription_id} created for pattern '{topic_pattern}'"
            )

            return subscription.subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: Subscription ID to remove

        Returns:
            True if subscription was removed
        """
        async with self._subscription_lock:
            for topic_pattern, subscriptions in self._subscriptions.items():
                for sub in subscriptions:
                    if sub.subscription_id == subscription_id:
                        subscriptions.remove(sub)

                        # Clean up empty pattern lists
                        if not subscriptions:
                            del self._subscriptions[topic_pattern]

                        logger.info(f"Subscription {subscription_id} removed")
                        return True

            logger.warning(f"Subscription {subscription_id} not found")
            return False

    async def publish(
        self,
        event: Event,
        persist: Optional[bool] = None,
    ) -> bool:
        """
        Publish an event to all matching subscribers.

        Args:
            event: Event to publish
            persist: Override persistence setting for this event

        Returns:
            True if event was published successfully

        Example:
            event = Event(
                topic="user.created",
                data={"user_id": 123, "email": "user@example.com"}
            )
            await bus.publish(event)
        """
        if not self._running:
            raise EventBusException("Event bus is not running. Call start() first.")

        try:
            # Persist event if enabled
            should_persist = persist if persist is not None else self._enable_persistence
            if should_persist and self._event_store:
                await self._event_store.store(event)

            # Publish to in-memory subscribers (in-memory and hybrid modes)
            if self._mode in (EventBusMode.IN_MEMORY, EventBusMode.HYBRID):
                await self._publish_in_memory(event)

            # Publish to Redis (distributed and hybrid modes)
            if self._mode in (EventBusMode.DISTRIBUTED, EventBusMode.HYBRID):
                await self._publish_to_redis(event)

            logger.debug(f"Published event {event.metadata.event_id} to topic '{event.topic}'")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def publish_batch(self, events: list[Event]) -> int:
        """
        Publish multiple events.

        Args:
            events: List of events to publish

        Returns:
            Number of events successfully published
        """
        published_count = 0
        for event in events:
            if await self.publish(event):
                published_count += 1

        return published_count

    async def replay(
        self,
        topic: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[Event]:
        """
        Replay events from the event store.

        Args:
            topic: Optional topic filter
            from_timestamp: Start time for replay
            to_timestamp: End time for replay
            limit: Maximum number of events to replay

        Returns:
            List of replayed events

        Example:
            # Replay all events from last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            events = await bus.replay(from_timestamp=one_hour_ago)

            # Replay specific topic
            events = await bus.replay(topic="user.created", limit=100)
        """
        if not self._event_store:
            logger.warning("Event persistence is not enabled. Cannot replay events.")
            return []

        return await self._event_store.replay(topic, from_timestamp, to_timestamp, limit)

    async def replay_and_publish(
        self,
        topic: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 1000,
    ) -> int:
        """
        Replay events and republish them to current subscribers.

        Args:
            topic: Optional topic filter
            from_timestamp: Start time for replay
            to_timestamp: End time for replay
            limit: Maximum number of events to replay

        Returns:
            Number of events replayed and published
        """
        events = await self.replay(topic, from_timestamp, to_timestamp, limit)

        published_count = 0
        for event in events:
            # Don't persist replayed events again
            if await self.publish(event, persist=False):
                published_count += 1

        logger.info(f"Replayed and published {published_count} events")
        return published_count

    def get_subscriptions(self, topic_pattern: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Get current subscriptions.

        Args:
            topic_pattern: Optional filter by topic pattern

        Returns:
            List of subscription information
        """
        subscriptions = []

        for pattern, subs in self._subscriptions.items():
            if topic_pattern and pattern != topic_pattern:
                continue

            for sub in subs:
                subscriptions.append({
                    "subscription_id": sub.subscription_id,
                    "topic_pattern": sub.topic_pattern,
                    "created_at": sub.created_at,
                    "max_retries": sub.max_retries,
                    "has_filter": sub.filter is not None,
                    "has_transformer": sub.transformer is not None,
                })

        return subscriptions

    async def get_dead_letter_events(
        self,
        topic: Optional[str] = None,
    ) -> list[DeadLetterEvent]:
        """
        Get events from dead letter queue.

        Args:
            topic: Optional topic filter

        Returns:
            List of dead letter events
        """
        if not self._dead_letter_queue:
            return []

        if topic:
            return await self._dead_letter_queue.get_by_topic(topic)
        else:
            return await self._dead_letter_queue.get_all()

    async def retry_dead_letter_event(self, event_id: str) -> bool:
        """
        Retry a failed event from the dead letter queue.

        Args:
            event_id: Event ID to retry

        Returns:
            True if event was successfully retried
        """
        if not self._dead_letter_queue:
            return False

        # Get all dead letter events
        dead_letters = await self._dead_letter_queue.get_all()

        # Find the event
        for dle in dead_letters:
            if dle.event_id == event_id:
                # Reconstruct event
                event = Event.from_dict(dle.event_data)

                # Reset retry count
                event.metadata.retry_count = 0

                # Republish
                success = await self.publish(event, persist=False)

                if success:
                    # Remove from dead letter queue
                    await self._dead_letter_queue.remove(event_id)
                    logger.info(f"Successfully retried dead letter event {event_id}")
                    return True

                return False

        logger.warning(f"Dead letter event {event_id} not found")
        return False

    async def clear_dead_letter_queue(self) -> int:
        """
        Clear all events from dead letter queue.

        Returns:
            Number of events cleared
        """
        if not self._dead_letter_queue:
            return 0

        return await self._dead_letter_queue.clear()

    def get_stats(self) -> dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary with statistics
        """
        total_subscriptions = sum(
            len(subs) for subs in self._subscriptions.values()
        )

        return {
            "mode": self._mode,
            "running": self._running,
            "total_subscriptions": total_subscriptions,
            "subscriptions_by_pattern": {
                pattern: len(subs)
                for pattern, subs in self._subscriptions.items()
            },
            "persistence_enabled": self._enable_persistence,
            "dead_letter_enabled": self._enable_dead_letter,
        }

    # Private methods

    async def _init_redis(self) -> None:
        """Initialize Redis client and pub/sub."""
        try:
            redis_url = self._settings.redis_url_with_password
            self._redis_client = redis.from_url(redis_url, decode_responses=False)

            # Test connection
            await self._redis_client.ping()

            # Create pub/sub client
            self._redis_pubsub = self._redis_client.pubsub()

            logger.info("Redis initialized for distributed event bus")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise EventBusException(f"Failed to connect to Redis: {e}")

    async def _start_pubsub_listener(self) -> None:
        """Start Redis pub/sub listener task."""
        if not self._redis_pubsub:
            return

        self._pubsub_task = asyncio.create_task(self._pubsub_listener())
        logger.info("Started Redis pub/sub listener")

    async def _pubsub_listener(self) -> None:
        """Listen for Redis pub/sub messages."""
        try:
            async for message in self._redis_pubsub.listen():
                if message["type"] in ("message", "pmessage"):
                    try:
                        # Decode message data
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode()

                        # Deserialize event
                        event = Event.from_json(data)

                        # Process in-memory
                        await self._publish_in_memory(event)

                    except Exception as e:
                        logger.error(f"Error processing pub/sub message: {e}")

        except asyncio.CancelledError:
            logger.info("Pub/sub listener cancelled")
        except Exception as e:
            logger.error(f"Pub/sub listener error: {e}")

    async def _publish_in_memory(self, event: Event) -> None:
        """
        Publish event to in-memory subscribers.

        Args:
            event: Event to publish
        """
        matching_subscriptions = self._get_matching_subscriptions(event.topic)

        if not matching_subscriptions:
            logger.debug(f"No subscribers for topic '{event.topic}'")
            return

        # Process all matching subscriptions concurrently
        tasks = [
            self._handle_subscription(subscription, event)
            for subscription in matching_subscriptions
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _publish_to_redis(self, event: Event) -> None:
        """
        Publish event to Redis pub/sub.

        Args:
            event: Event to publish
        """
        if not self._redis_client:
            return

        try:
            channel = f"eventbus:{event.topic}"
            message = event.to_json()
            await self._redis_client.publish(channel, message)

        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    def _get_matching_subscriptions(self, topic: str) -> list[EventSubscription]:
        """
        Get subscriptions matching a topic.

        Args:
            topic: Event topic

        Returns:
            List of matching subscriptions
        """
        matching = []

        for pattern, subscriptions in self._subscriptions.items():
            for sub in subscriptions:
                if sub.matches_topic(topic):
                    matching.append(sub)

        return matching

    async def _handle_subscription(
        self,
        subscription: EventSubscription,
        event: Event,
    ) -> None:
        """
        Handle event for a subscription with retry logic.

        Args:
            subscription: Subscription to handle
            event: Event to process
        """
        # Apply filter if present
        if subscription.filter and not subscription.filter.should_process(event):
            logger.debug(
                f"Event {event.metadata.event_id} filtered out for subscription "
                f"{subscription.subscription_id}"
            )
            return

        # Apply transformer if present
        if subscription.transformer:
            event = subscription.transformer.transform(event)

        # Try to process with retries
        retry_count = 0
        last_error = None

        while retry_count <= subscription.max_retries:
            try:
                await subscription.handler(event)
                logger.debug(
                    f"Event {event.metadata.event_id} processed by subscription "
                    f"{subscription.subscription_id}"
                )
                return  # Success

            except Exception as e:
                last_error = e
                retry_count += 1
                event.metadata.retry_count = retry_count

                logger.warning(
                    f"Error processing event {event.metadata.event_id} "
                    f"(attempt {retry_count}/{subscription.max_retries + 1}): {e}"
                )

                if retry_count <= subscription.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2 ** retry_count)

        # All retries failed - add to dead letter queue
        logger.error(
            f"Failed to process event {event.metadata.event_id} after "
            f"{retry_count} attempts. Error: {last_error}"
        )

        if subscription.dead_letter_enabled and self._dead_letter_queue:
            await self._dead_letter_queue.add(
                event,
                last_error,
                subscription.subscription_id
            )


# =============================================================================
# Global Event Bus Instance
# =============================================================================


_event_bus_instance: Optional[EventBus] = None


def get_event_bus(
    mode: EventBusMode = EventBusMode.IN_MEMORY,
    **kwargs
) -> EventBus:
    """
    Get or create global event bus instance.

    Args:
        mode: Event bus mode
        **kwargs: Additional EventBus configuration

    Returns:
        EventBus instance

    Example:
        bus = get_event_bus(mode=EventBusMode.DISTRIBUTED)
        await bus.start()
    """
    global _event_bus_instance

    if _event_bus_instance is None:
        _event_bus_instance = EventBus(mode=mode, **kwargs)

    return _event_bus_instance
