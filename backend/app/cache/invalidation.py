"""
Cache invalidation service with advanced invalidation strategies.

Provides comprehensive cache invalidation with:
- Tag-based invalidation: Invalidate by tags for related entries
- Pattern-based invalidation: Invalidate by key patterns
- Dependency-aware invalidation: Track and invalidate dependent entries
- Cascading invalidation: Automatic propagation to related caches
- Event publishing: Publish invalidation events for subscribers
- Detailed logging: Track all invalidation operations
- Batch invalidation: Efficiently invalidate multiple entries
- Metrics tracking: Monitor invalidation performance

Example:
    service = get_invalidation_service()

    # Tag-based invalidation
    await service.invalidate_by_tag("user:123")

    # Pattern-based invalidation
    await service.invalidate_by_pattern("schedule:*:assignments")

    # Dependency-aware invalidation
    await service.register_dependency("schedule:main", "schedule:user:123")
    await service.invalidate_with_dependencies("schedule:main")

    # Batch invalidation
    await service.batch_invalidate(["key1", "key2", "key3"])
"""

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import RLock
from typing import Any

import redis.asyncio as redis

from app.core.cache.keys import generate_tag_key
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class InvalidationEventType(str, Enum):
    """
    Types of invalidation events.

    Used for event publishing and metrics tracking.
    """

    TAG_INVALIDATION = "tag_invalidation"
    PATTERN_INVALIDATION = "pattern_invalidation"
    DEPENDENCY_INVALIDATION = "dependency_invalidation"
    CASCADING_INVALIDATION = "cascading_invalidation"
    BATCH_INVALIDATION = "batch_invalidation"
    MANUAL_INVALIDATION = "manual_invalidation"


@dataclass
class InvalidationEvent:
    """
    Event representing a cache invalidation operation.

    Published to event subscribers for monitoring and auditing.

    Attributes:
        event_type: Type of invalidation event
        keys_invalidated: Number of keys invalidated
        pattern: Pattern used for pattern-based invalidation
        tag: Tag used for tag-based invalidation
        dependencies: List of dependent keys invalidated
        timestamp: When the invalidation occurred
        duration_ms: How long the invalidation took
        metadata: Additional event metadata
    """

    event_type: InvalidationEventType
    keys_invalidated: int
    pattern: str | None = None
    tag: str | None = None
    dependencies: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": self.event_type.value,
            "keys_invalidated": self.keys_invalidated,
            "pattern": self.pattern,
            "tag": self.tag,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


@dataclass
class InvalidationMetrics:
    """
    Metrics for cache invalidation operations.

    Tracks performance and volume of invalidation operations.
    """

    total_invalidations: int = 0
    total_keys_invalidated: int = 0
    tag_invalidations: int = 0
    pattern_invalidations: int = 0
    dependency_invalidations: int = 0
    cascading_invalidations: int = 0
    batch_invalidations: int = 0
    total_duration_ms: float = 0.0

    @property
    def avg_duration_ms(self) -> float:
        """Average duration per invalidation operation."""
        if self.total_invalidations == 0:
            return 0.0
        return self.total_duration_ms / self.total_invalidations

    @property
    def avg_keys_per_invalidation(self) -> float:
        """Average number of keys invalidated per operation."""
        if self.total_invalidations == 0:
            return 0.0
        return self.total_keys_invalidated / self.total_invalidations

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metrics to dictionary.

        Returns:
            Dictionary with all metrics
        """
        return {
            "total_invalidations": self.total_invalidations,
            "total_keys_invalidated": self.total_keys_invalidated,
            "tag_invalidations": self.tag_invalidations,
            "pattern_invalidations": self.pattern_invalidations,
            "dependency_invalidations": self.dependency_invalidations,
            "cascading_invalidations": self.cascading_invalidations,
            "batch_invalidations": self.batch_invalidations,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "avg_keys_per_invalidation": round(self.avg_keys_per_invalidation, 2),
        }


class CacheInvalidationService:
    """
    Comprehensive cache invalidation service.

    Provides advanced invalidation strategies with event publishing,
    dependency tracking, and cascading invalidation.

    Features:
    - Tag-based invalidation: Invalidate all entries with a tag
    - Pattern-based invalidation: Invalidate entries matching a pattern
    - Dependency tracking: Automatically invalidate dependent entries
    - Cascading invalidation: Propagate invalidation to related caches
    - Event publishing: Notify subscribers of invalidation events
    - Batch processing: Efficiently invalidate multiple entries
    - Metrics tracking: Monitor invalidation performance

    Example:
        service = CacheInvalidationService(namespace="schedule")

        # Register dependencies
        await service.register_dependency(
            "schedule:main",
            "schedule:user:123"
        )

        # Invalidate with dependencies
        await service.invalidate_with_dependencies("schedule:main")

        # Subscribe to invalidation events
        service.subscribe(my_event_handler)
    """

    def __init__(
        self,
        namespace: str = "cache",
        key_prefix: str = "cache",
        enable_event_publishing: bool = True,
        enable_metrics: bool = True,
    ):
        """
        Initialize cache invalidation service.

        Args:
            namespace: Cache namespace for key organization
            key_prefix: Global prefix for all cache keys
            enable_event_publishing: Enable event publishing to subscribers
            enable_metrics: Enable metrics tracking
        """
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.enable_event_publishing = enable_event_publishing
        self.enable_metrics = enable_metrics

        # Redis connection
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

        # Dependency tracking (key -> list of dependent keys)
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._reverse_dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependency_lock = RLock()

        # Event subscribers
        self._event_subscribers: list[Callable[[InvalidationEvent], None]] = []
        self._subscriber_lock = RLock()

        # Metrics
        self.metrics = InvalidationMetrics()
        self._metrics_lock = RLock()

        # Event history (last 1000 events)
        self._event_history: list[InvalidationEvent] = []
        self._max_history_size = 1000
        self._history_lock = RLock()

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=False)

        return self._redis

    # Tag-based invalidation

    async def invalidate_by_tag(
        self, tag: str, cascade: bool = True, publish_event: bool = True
    ) -> int:
        """
        Invalidate all cache entries associated with a tag.

        Args:
            tag: Tag to invalidate
            cascade: If True, also invalidate dependent entries
            publish_event: If True, publish invalidation event

        Returns:
            Number of keys invalidated

        Example:
            # Invalidate all cache entries for user 123
            count = await service.invalidate_by_tag("user:123")
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()
            tag_key = generate_tag_key(self.namespace, tag, prefix=self.key_prefix)

            # Get all keys associated with this tag
            keys = await redis_client.smembers(tag_key)

            if not keys:
                logger.debug(f"No keys found for tag '{tag}'")
                return 0

            # Convert bytes to strings
            key_strings = [k.decode() if isinstance(k, bytes) else k for k in keys]

            # Delete all keys and the tag set
            count = await redis_client.delete(*keys, tag_key)

            logger.info(f"Invalidated {count} entries for tag '{tag}'")

            # Cascade invalidation to dependencies if enabled
            cascaded_count = 0
            if cascade:
                for key in key_strings:
                    cascaded_count += await self._invalidate_dependencies(
                        key, publish_event=False
                    )

            total_count = count + cascaded_count

            # Record metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_invalidation(
                    InvalidationEventType.TAG_INVALIDATION, total_count, duration_ms
                )

            # Publish event
            if publish_event and self.enable_event_publishing:
                event = InvalidationEvent(
                    event_type=InvalidationEventType.TAG_INVALIDATION,
                    keys_invalidated=total_count,
                    tag=tag,
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"cascaded": cascade, "cascaded_count": cascaded_count},
                )
                await self._publish_event(event)

            return total_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error during tag invalidation: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error invalidating tag '{tag}': {e}", exc_info=True)
            return 0

    async def invalidate_by_tags(
        self, tags: list[str], cascade: bool = True, publish_event: bool = True
    ) -> int:
        """
        Invalidate cache entries for multiple tags.

        Args:
            tags: List of tags to invalidate
            cascade: If True, also invalidate dependent entries
            publish_event: If True, publish invalidation event

        Returns:
            Total number of keys invalidated

        Example:
            # Invalidate multiple tags
            count = await service.invalidate_by_tags(["user:123", "schedule:2024"])
        """
        total_count = 0

        for tag in tags:
            count = await self.invalidate_by_tag(
                tag, cascade=cascade, publish_event=False
            )
            total_count += count

        # Publish single event for batch operation
        if publish_event and self.enable_event_publishing:
            event = InvalidationEvent(
                event_type=InvalidationEventType.BATCH_INVALIDATION,
                keys_invalidated=total_count,
                duration_ms=0.0,
                metadata={"tags": tags, "cascaded": cascade},
            )
            await self._publish_event(event)

        return total_count

    # Pattern-based invalidation

    async def invalidate_by_pattern(
        self,
        pattern: str,
        batch_size: int = 100,
        cascade: bool = True,
        publish_event: bool = True,
    ) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "cache:schedule:*")
            batch_size: Number of keys to process per iteration
            cascade: If True, also invalidate dependent entries
            publish_event: If True, publish invalidation event

        Returns:
            Number of keys invalidated

        Example:
            # Invalidate all schedule-related cache entries
            count = await service.invalidate_by_pattern("cache:schedule:*")
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()
            count = 0
            cursor = 0
            invalidated_keys = []

            while True:
                cursor, keys = await redis_client.scan(
                    cursor, match=pattern, count=batch_size
                )

                if keys:
                    deleted = await redis_client.delete(*keys)
                    count += deleted

                    # Track keys for dependency invalidation
                    if cascade:
                        invalidated_keys.extend(
                            k.decode() if isinstance(k, bytes) else k for k in keys
                        )

                if cursor == 0:
                    break

            logger.info(f"Invalidated {count} entries matching pattern '{pattern}'")

            # Cascade invalidation to dependencies if enabled
            cascaded_count = 0
            if cascade:
                for key in invalidated_keys:
                    cascaded_count += await self._invalidate_dependencies(
                        key, publish_event=False
                    )

            total_count = count + cascaded_count

            # Record metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_invalidation(
                    InvalidationEventType.PATTERN_INVALIDATION, total_count, duration_ms
                )

            # Publish event
            if publish_event and self.enable_event_publishing:
                event = InvalidationEvent(
                    event_type=InvalidationEventType.PATTERN_INVALIDATION,
                    keys_invalidated=total_count,
                    pattern=pattern,
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"cascaded": cascade, "cascaded_count": cascaded_count},
                )
                await self._publish_event(event)

            return total_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error during pattern invalidation: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error invalidating pattern '{pattern}': {e}", exc_info=True)
            return 0

    # Dependency-aware invalidation

    def register_dependency(self, key: str, dependent_key: str) -> None:
        """
        Register a dependency between cache entries.

        When 'key' is invalidated, 'dependent_key' will also be invalidated.

        Args:
            key: Primary cache key
            dependent_key: Key that depends on the primary key

        Example:
            # When schedule:main is invalidated, also invalidate schedule:user:123
            service.register_dependency("schedule:main", "schedule:user:123")
        """
        with self._dependency_lock:
            self._dependencies[key].add(dependent_key)
            self._reverse_dependencies[dependent_key].add(key)

        logger.debug(f"Registered dependency: {key} -> {dependent_key}")

    def unregister_dependency(self, key: str, dependent_key: str) -> None:
        """
        Unregister a dependency between cache entries.

        Args:
            key: Primary cache key
            dependent_key: Key that depends on the primary key
        """
        with self._dependency_lock:
            self._dependencies[key].discard(dependent_key)
            self._reverse_dependencies[dependent_key].discard(key)

        logger.debug(f"Unregistered dependency: {key} -> {dependent_key}")

    def register_dependencies(self, key: str, dependent_keys: list[str]) -> None:
        """
        Register multiple dependencies for a cache entry.

        Args:
            key: Primary cache key
            dependent_keys: List of keys that depend on the primary key

        Example:
            service.register_dependencies(
                "schedule:main",
                ["schedule:user:123", "schedule:user:456"]
            )
        """
        for dependent_key in dependent_keys:
            self.register_dependency(key, dependent_key)

    def get_dependencies(self, key: str) -> set[str]:
        """
        Get all dependencies for a cache key.

        Args:
            key: Cache key

        Returns:
            Set of dependent keys
        """
        with self._dependency_lock:
            return self._dependencies.get(key, set()).copy()

    def clear_dependencies(self, key: str) -> None:
        """
        Clear all dependencies for a cache key.

        Args:
            key: Cache key
        """
        with self._dependency_lock:
            # Remove from dependencies
            dependent_keys = self._dependencies.pop(key, set())

            # Remove from reverse dependencies
            for dependent_key in dependent_keys:
                self._reverse_dependencies[dependent_key].discard(key)

        logger.debug(f"Cleared dependencies for key: {key}")

    async def invalidate_with_dependencies(
        self, key: str, max_depth: int = 10, publish_event: bool = True
    ) -> int:
        """
        Invalidate a cache entry and all its dependencies.

        Args:
            key: Cache key to invalidate
            max_depth: Maximum depth for recursive dependency invalidation
            publish_event: If True, publish invalidation event

        Returns:
            Total number of keys invalidated

        Example:
            # Invalidate schedule:main and all dependent entries
            count = await service.invalidate_with_dependencies("schedule:main")
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()

            # Track invalidated keys to avoid cycles
            invalidated = set()
            to_invalidate = [key]
            depth = 0

            while to_invalidate and depth < max_depth:
                current_key = to_invalidate.pop(0)

                if current_key in invalidated:
                    continue

                # Delete the key
                deleted = await redis_client.delete(current_key)
                if deleted > 0:
                    invalidated.add(current_key)
                    logger.debug(f"Invalidated key with dependencies: {current_key}")

                # Add dependencies to queue
                dependencies = self.get_dependencies(current_key)
                for dep_key in dependencies:
                    if dep_key not in invalidated:
                        to_invalidate.append(dep_key)

                depth += 1

            count = len(invalidated)

            if depth >= max_depth and to_invalidate:
                logger.warning(
                    f"Reached maximum dependency depth ({max_depth}) "
                    f"with {len(to_invalidate)} keys remaining"
                )

            logger.info(
                f"Invalidated {count} entries including dependencies for key '{key}'"
            )

            # Record metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_invalidation(
                    InvalidationEventType.DEPENDENCY_INVALIDATION, count, duration_ms
                )

            # Publish event
            if publish_event and self.enable_event_publishing:
                event = InvalidationEvent(
                    event_type=InvalidationEventType.DEPENDENCY_INVALIDATION,
                    keys_invalidated=count,
                    dependencies=list(invalidated),
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"max_depth": max_depth, "depth_reached": depth},
                )
                await self._publish_event(event)

            return count

        except redis.ConnectionError as e:
            logger.warning(
                f"Redis connection error during dependency invalidation: {e}"
            )
            return 0
        except Exception as e:
            logger.error(
                f"Error invalidating key with dependencies '{key}': {e}", exc_info=True
            )
            return 0

    async def _invalidate_dependencies(
        self, key: str, publish_event: bool = False
    ) -> int:
        """
        Internal method to invalidate dependencies for a key.

        Args:
            key: Cache key
            publish_event: If True, publish invalidation event

        Returns:
            Number of dependent keys invalidated
        """
        dependencies = self.get_dependencies(key)

        if not dependencies:
            return 0

        try:
            redis_client = await self._get_redis()
            count = await redis_client.delete(*dependencies)

            if count > 0:
                logger.debug(f"Invalidated {count} dependencies for key '{key}'")

            return count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error invalidating dependencies: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error invalidating dependencies: {e}")
            return 0

    # Batch invalidation

    async def batch_invalidate(
        self,
        keys: list[str],
        cascade: bool = True,
        batch_size: int = 100,
        publish_event: bool = True,
    ) -> int:
        """
        Efficiently invalidate multiple cache entries in batches.

        Args:
            keys: List of cache keys to invalidate
            cascade: If True, also invalidate dependent entries
            batch_size: Number of keys to process per batch
            publish_event: If True, publish invalidation event

        Returns:
            Total number of keys invalidated

        Example:
            keys = ["key1", "key2", "key3", "key4"]
            count = await service.batch_invalidate(keys, batch_size=2)
        """
        start_time = time.time()

        if not keys:
            return 0

        try:
            redis_client = await self._get_redis()
            total_count = 0

            # Process in batches
            for i in range(0, len(keys), batch_size):
                batch = keys[i : i + batch_size]
                deleted = await redis_client.delete(*batch)
                total_count += deleted

                # Cascade invalidation if enabled
                if cascade:
                    for key in batch:
                        cascaded = await self._invalidate_dependencies(
                            key, publish_event=False
                        )
                        total_count += cascaded

            logger.info(f"Batch invalidated {total_count} entries ({len(keys)} keys)")

            # Record metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_invalidation(
                    InvalidationEventType.BATCH_INVALIDATION, total_count, duration_ms
                )

            # Publish event
            if publish_event and self.enable_event_publishing:
                event = InvalidationEvent(
                    event_type=InvalidationEventType.BATCH_INVALIDATION,
                    keys_invalidated=total_count,
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "keys_requested": len(keys),
                        "batch_size": batch_size,
                        "cascaded": cascade,
                    },
                )
                await self._publish_event(event)

            return total_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error during batch invalidation: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error during batch invalidation: {e}", exc_info=True)
            return 0

    # Cascading invalidation

    async def cascade_invalidate(
        self, key: str, related_patterns: list[str], publish_event: bool = True
    ) -> int:
        """
        Invalidate a key and all related cache entries matching patterns.

        Useful for invalidating a primary entry and all derived/related entries.

        Args:
            key: Primary cache key to invalidate
            related_patterns: List of patterns for related entries to invalidate
            publish_event: If True, publish invalidation event

        Returns:
            Total number of keys invalidated

        Example:
            # Invalidate schedule and all related cached views
            count = await service.cascade_invalidate(
                "schedule:main",
                ["schedule:*:view", "schedule:*:summary"]
            )
        """
        start_time = time.time()

        try:
            redis_client = await self._get_redis()

            # Invalidate primary key
            count = await redis_client.delete(key)
            logger.debug(f"Invalidated primary key: {key}")

            # Invalidate related patterns
            for pattern in related_patterns:
                pattern_count = await self.invalidate_by_pattern(
                    pattern, cascade=False, publish_event=False
                )
                count += pattern_count

            logger.info(
                f"Cascade invalidated {count} entries "
                f"(1 primary + {len(related_patterns)} patterns)"
            )

            # Record metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_invalidation(
                    InvalidationEventType.CASCADING_INVALIDATION, count, duration_ms
                )

            # Publish event
            if publish_event and self.enable_event_publishing:
                event = InvalidationEvent(
                    event_type=InvalidationEventType.CASCADING_INVALIDATION,
                    keys_invalidated=count,
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"primary_key": key, "related_patterns": related_patterns},
                )
                await self._publish_event(event)

            return count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error during cascade invalidation: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error during cascade invalidation: {e}", exc_info=True)
            return 0

    # Event publishing

    def subscribe(self, callback: Callable[[InvalidationEvent], None]) -> None:
        """
        Subscribe to invalidation events.

        The callback will be called for each invalidation event.

        Args:
            callback: Function to call with InvalidationEvent

        Example:
            def on_invalidation(event: InvalidationEvent):
                print(f"Invalidated {event.keys_invalidated} keys")

            service.subscribe(on_invalidation)
        """
        with self._subscriber_lock:
            self._event_subscribers.append(callback)

        logger.debug(f"Added invalidation event subscriber: {callback.__name__}")

    def unsubscribe(self, callback: Callable[[InvalidationEvent], None]) -> None:
        """
        Unsubscribe from invalidation events.

        Args:
            callback: Previously subscribed callback function
        """
        with self._subscriber_lock:
            if callback in self._event_subscribers:
                self._event_subscribers.remove(callback)

        logger.debug(f"Removed invalidation event subscriber: {callback.__name__}")

    async def _publish_event(self, event: InvalidationEvent) -> None:
        """
        Publish invalidation event to all subscribers.

        Args:
            event: Invalidation event to publish
        """
        # Add to history
        with self._history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)

        # Notify subscribers
        with self._subscriber_lock:
            subscribers = self._event_subscribers.copy()

        for subscriber in subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                logger.error(
                    f"Error in invalidation event subscriber "
                    f"{subscriber.__name__}: {e}",
                    exc_info=True,
                )

        logger.debug(
            f"Published invalidation event: {event.event_type.value} "
            f"({event.keys_invalidated} keys)"
        )

    def get_event_history(self, limit: int | None = None) -> list[InvalidationEvent]:
        """
        Get recent invalidation event history.

        Args:
            limit: Maximum number of events to return (default: all)

        Returns:
            List of recent invalidation events
        """
        with self._history_lock:
            if limit is None:
                return self._event_history.copy()
            return self._event_history[-limit:]

    def clear_event_history(self) -> None:
        """Clear invalidation event history."""
        with self._history_lock:
            self._event_history.clear()

        logger.debug("Cleared invalidation event history")

    # Metrics

    def _record_invalidation(
        self, event_type: InvalidationEventType, count: int, duration_ms: float
    ) -> None:
        """
        Record invalidation metrics.

        Args:
            event_type: Type of invalidation
            count: Number of keys invalidated
            duration_ms: Duration of operation in milliseconds
        """
        with self._metrics_lock:
            self.metrics.total_invalidations += 1
            self.metrics.total_keys_invalidated += count
            self.metrics.total_duration_ms += duration_ms

            if event_type == InvalidationEventType.TAG_INVALIDATION:
                self.metrics.tag_invalidations += 1
            elif event_type == InvalidationEventType.PATTERN_INVALIDATION:
                self.metrics.pattern_invalidations += 1
            elif event_type == InvalidationEventType.DEPENDENCY_INVALIDATION:
                self.metrics.dependency_invalidations += 1
            elif event_type == InvalidationEventType.CASCADING_INVALIDATION:
                self.metrics.cascading_invalidations += 1
            elif event_type == InvalidationEventType.BATCH_INVALIDATION:
                self.metrics.batch_invalidations += 1

    def get_metrics(self) -> dict[str, Any]:
        """
        Get invalidation metrics.

        Returns:
            Dictionary with all metrics

        Example:
            metrics = service.get_metrics()
            print(f"Total invalidations: {metrics['total_invalidations']}")
        """
        with self._metrics_lock:
            return self.metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        with self._metrics_lock:
            self.metrics = InvalidationMetrics()

        logger.debug("Reset invalidation metrics")


# Global service instance
_invalidation_service: CacheInvalidationService | None = None
_service_lock = RLock()


def get_invalidation_service(
    namespace: str = "cache", **kwargs
) -> CacheInvalidationService:
    """
    Get or create the global cache invalidation service instance.

    Args:
        namespace: Cache namespace
        **kwargs: Additional arguments for CacheInvalidationService

    Returns:
        CacheInvalidationService instance

    Example:
        service = get_invalidation_service("schedule")
        await service.invalidate_by_tag("user:123")
    """
    global _invalidation_service

    with _service_lock:
        if _invalidation_service is None:
            _invalidation_service = CacheInvalidationService(
                namespace=namespace, **kwargs
            )

        return _invalidation_service
