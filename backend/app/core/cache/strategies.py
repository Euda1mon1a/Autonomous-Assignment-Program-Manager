"""
Cache invalidation strategies.

Provides various strategies for cache invalidation including TTL-based,
tag-based, pattern-based, and write-through invalidation.

This module provides:
- InvalidationStrategy: Base class for invalidation strategies
- TTLStrategy: Time-to-live based invalidation
- TagBasedStrategy: Tag-based invalidation for related entries
- PatternStrategy: Pattern-based invalidation
- WriteThrough: Write-through cache invalidation
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InvalidationTrigger(str, Enum):
    """
    Triggers for cache invalidation.

    Defines when cache entries should be invalidated.
    """

    TTL_EXPIRED = "ttl_expired"  # Time-to-live expired
    WRITE_OPERATION = "write_operation"  # Data was written
    MANUAL = "manual"  # Manual invalidation
    TAG_INVALIDATION = "tag_invalidation"  # Tag-based group invalidation
    PATTERN_MATCH = "pattern_match"  # Pattern-based invalidation
    CACHE_FULL = "cache_full"  # Cache eviction due to size


class InvalidationStrategy(ABC):
    """
    Base class for cache invalidation strategies.

    Subclasses implement specific invalidation logic for different
    caching patterns and requirements.
    """

    def __init__(self, namespace: str):
        """
        Initialize invalidation strategy.

        Args:
            namespace: Cache namespace for this strategy
        """
        self.namespace = namespace
        self.invalidation_count = 0

    @abstractmethod
    async def should_invalidate(
        self, key: str, trigger: InvalidationTrigger, **kwargs: Any
    ) -> bool:
        """
        Determine if a cache entry should be invalidated.

        Args:
            key: Cache key to check
            trigger: What triggered the invalidation check
            **kwargs: Additional context for invalidation decision

        Returns:
            True if entry should be invalidated, False otherwise
        """
        pass

    @abstractmethod
    async def invalidate(
        self, cache_client: Any, key: str | None = None, **kwargs: Any
    ) -> int:
        """
        Execute invalidation for matching entries.

        Args:
            cache_client: Redis client instance
            key: Optional specific key to invalidate
            **kwargs: Additional parameters for invalidation

        Returns:
            Number of entries invalidated
        """
        pass

    def _record_invalidation(self, count: int) -> None:
        """
        Record invalidation for statistics.

        Args:
            count: Number of entries invalidated
        """
        self.invalidation_count += count
        logger.debug(
            f"Strategy {self.__class__.__name__} invalidated {count} entries "
            f"(total: {self.invalidation_count})"
        )


class TTLStrategy(InvalidationStrategy):
    """
    Time-to-live based invalidation strategy.

    Entries are automatically invalidated after a specified TTL.
    Redis handles TTL automatically, but this strategy provides
    programmatic control and monitoring.

    Example:
        strategy = TTLStrategy(namespace="schedule", default_ttl=300)
        await strategy.set_ttl(redis_client, "my_key", ttl=600)
    """

    def __init__(self, namespace: str, default_ttl: int = 300):
        """
        Initialize TTL strategy.

        Args:
            namespace: Cache namespace
            default_ttl: Default time-to-live in seconds
        """
        super().__init__(namespace)
        self.default_ttl = default_ttl

    async def should_invalidate(
        self, key: str, trigger: InvalidationTrigger, **kwargs: Any
    ) -> bool:
        """
        Check if entry should be invalidated based on TTL.

        Args:
            key: Cache key
            trigger: Invalidation trigger
            **kwargs: May contain 'ttl_remaining' parameter

        Returns:
            True if TTL expired, False otherwise
        """
        if trigger == InvalidationTrigger.TTL_EXPIRED:
            return True

        # Check remaining TTL if provided
        ttl_remaining: int = kwargs.get("ttl_remaining", -1)
        return bool(ttl_remaining <= 0)

    async def invalidate(
        self, cache_client: Any, key: str | None = None, **kwargs: Any
    ) -> int:
        """
        Invalidate expired entries (Redis handles automatically).

        Args:
            cache_client: Redis client
            key: Optional specific key to invalidate
            **kwargs: Additional parameters

        Returns:
            Number of entries invalidated
        """
        if key:
            deleted: int = await cache_client.delete(key)
            self._record_invalidation(deleted)
            return deleted

        # For pattern-based TTL invalidation, we'd need to scan
        # but Redis handles TTL automatically, so this is rarely needed
        return 0

    async def set_ttl(
        self, cache_client: Any, key: str, ttl: int | None = None
    ) -> bool:
        """
        Set or update TTL for a cache entry.

        Args:
            cache_client: Redis client
            key: Cache key
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if TTL was set successfully
        """
        ttl_to_use = ttl or self.default_ttl
        result: bool = await cache_client.expire(key, ttl_to_use)
        return result


class TagBasedStrategy(InvalidationStrategy):
    """
    Tag-based invalidation strategy.

    Allows invalidating groups of related cache entries by tag.
    Each cache entry can have multiple tags, and invalidating a tag
    invalidates all entries with that tag.

    Example:
        strategy = TagBasedStrategy(namespace="schedule")
        # When data changes:
        await strategy.invalidate_by_tag(redis_client, "user:123")
        # Invalidates all entries tagged with "user:123"
    """

    def __init__(self, namespace: str):
        """
        Initialize tag-based strategy.

        Args:
            namespace: Cache namespace
        """
        super().__init__(namespace)
        self.tag_prefix = f"cache:tag:{namespace}"

    async def should_invalidate(
        self, key: str, trigger: InvalidationTrigger, **kwargs: Any
    ) -> bool:
        """
        Check if entry should be invalidated based on tags.

        Args:
            key: Cache key
            trigger: Invalidation trigger
            **kwargs: May contain 'tags' parameter

        Returns:
            True if any associated tags are invalidated
        """
        if trigger == InvalidationTrigger.TAG_INVALIDATION:
            return True
        return False

    async def invalidate(
        self, cache_client: Any, key: str | None = None, **kwargs: Any
    ) -> int:
        """
        Invalidate entries by tag or specific key.

        Args:
            cache_client: Redis client
            key: Optional specific key to invalidate
            **kwargs: May contain 'tag' for tag-based invalidation

        Returns:
            Number of entries invalidated
        """
        tag = kwargs.get("tag")

        if tag:
            return await self.invalidate_by_tag(cache_client, tag)
        elif key:
            # Remove key from all tag sets and delete the key
            deleted: int = await cache_client.delete(key)
            self._record_invalidation(deleted)
            return deleted

        return 0

    async def invalidate_by_tag(self, cache_client: Any, tag: str) -> int:
        """
        Invalidate all cache entries associated with a tag.

        Args:
            cache_client: Redis client
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated
        """
        tag_key = f"{self.tag_prefix}:{tag}"

        # Get all keys associated with this tag
        keys = await cache_client.smembers(tag_key)

        if not keys:
            return 0

        # Delete all keys and the tag set
        count: int = await cache_client.delete(*keys, tag_key)
        self._record_invalidation(count)

        logger.info(f"Invalidated {count} entries for tag '{tag}'")
        return count

    async def add_tags(self, cache_client: Any, key: str, tags: list[str]) -> int:
        """
        Associate tags with a cache entry.

        Args:
            cache_client: Redis client
            key: Cache key
            tags: List of tags to associate

        Returns:
            Number of tags added
        """
        count = 0
        for tag in tags:
            tag_key = f"{self.tag_prefix}:{tag}"
            added = await cache_client.sadd(tag_key, key)
            count += added

        return count


class PatternStrategy(InvalidationStrategy):
    """
    Pattern-based invalidation strategy.

    Invalidates cache entries matching a Redis pattern (e.g., "user:*:profile").

    Example:
        strategy = PatternStrategy(namespace="schedule")
        # Invalidate all user profiles:
        await strategy.invalidate_by_pattern(redis_client, "user:*:profile")
    """

    def __init__(self, namespace: str):
        """
        Initialize pattern-based strategy.

        Args:
            namespace: Cache namespace
        """
        super().__init__(namespace)

    async def should_invalidate(
        self, key: str, trigger: InvalidationTrigger, **kwargs: Any
    ) -> bool:
        """
        Check if entry should be invalidated based on pattern.

        Args:
            key: Cache key
            trigger: Invalidation trigger
            **kwargs: May contain 'pattern' parameter

        Returns:
            True if key matches invalidation pattern
        """
        if trigger == InvalidationTrigger.PATTERN_MATCH:
            return True
        return False

    async def invalidate(
        self, cache_client: Any, key: str | None = None, **kwargs: Any
    ) -> int:
        """
        Invalidate entries by pattern.

        Args:
            cache_client: Redis client
            key: Optional specific key to invalidate
            **kwargs: May contain 'pattern' for pattern-based invalidation

        Returns:
            Number of entries invalidated
        """
        pattern = kwargs.get("pattern")

        if pattern:
            return await self.invalidate_by_pattern(cache_client, pattern)
        elif key:
            deleted: int = await cache_client.delete(key)
            self._record_invalidation(deleted)
            return deleted

        return 0

    async def invalidate_by_pattern(
        self, cache_client: Any, pattern: str, batch_size: int = 100
    ) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            cache_client: Redis client
            pattern: Redis pattern (e.g., "cache:schedule:*")
            batch_size: Number of keys to process per iteration

        Returns:
            Number of entries invalidated
        """
        count = 0
        cursor = 0

        while True:
            cursor, keys = await cache_client.scan(
                cursor, match=pattern, count=batch_size
            )

            if keys:
                deleted = await cache_client.delete(*keys)
                count += deleted

            if cursor == 0:
                break

        self._record_invalidation(count)
        logger.info(f"Invalidated {count} entries matching pattern '{pattern}'")
        return count


class WriteThroughStrategy(InvalidationStrategy):
    """
    Write-through cache invalidation strategy.

    Invalidates cache entries immediately when underlying data is written.
    Ensures cache consistency by invalidating before or after writes.

    Example:
        strategy = WriteThroughStrategy(namespace="schedule")
        # Before writing to database:
        await strategy.invalidate_on_write(redis_client, affected_keys)
        # Write to database...
    """

    def __init__(self, namespace: str, invalidate_before_write: bool = True):
        """
        Initialize write-through strategy.

        Args:
            namespace: Cache namespace
            invalidate_before_write: If True, invalidate before write;
                                    if False, invalidate after write
        """
        super().__init__(namespace)
        self.invalidate_before_write = invalidate_before_write

    async def should_invalidate(
        self, key: str, trigger: InvalidationTrigger, **kwargs: Any
    ) -> bool:
        """
        Check if entry should be invalidated on write.

        Args:
            key: Cache key
            trigger: Invalidation trigger
            **kwargs: Additional context

        Returns:
            True if write operation triggers invalidation
        """
        return trigger == InvalidationTrigger.WRITE_OPERATION

    async def invalidate(
        self, cache_client: Any, key: str | None = None, **kwargs: Any
    ) -> int:
        """
        Invalidate cache entries on write operation.

        Args:
            cache_client: Redis client
            key: Optional specific key to invalidate
            **kwargs: May contain 'keys' for batch invalidation

        Returns:
            Number of entries invalidated
        """
        keys_list: list[str] = kwargs.get("keys", [])

        if key:
            keys_list.append(key)

        if not keys_list:
            return 0

        count: int = await cache_client.delete(*keys_list)
        self._record_invalidation(count)
        return count

    async def invalidate_on_write(self, cache_client: Any, keys: list[str]) -> int:
        """
        Invalidate cache entries for a write operation.

        Args:
            cache_client: Redis client
            keys: List of cache keys to invalidate

        Returns:
            Number of entries invalidated
        """
        if not keys:
            return 0

        count: int = await cache_client.delete(*keys)
        self._record_invalidation(count)

        logger.debug(f"Write-through invalidated {count} entries")
        return count
