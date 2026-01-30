"""
Advanced Redis cache service with multi-level caching support.

Provides a comprehensive caching solution with:
- L1 (memory) and L2 (Redis) caching
- Read-through, write-through, and cache-aside patterns
- Tag-based invalidation
- Cache warming
- Statistics tracking

This module provides:
- CacheEntry: Cache entry with metadata
- CacheStats: Cache statistics tracking
- MultiLevelCache: L1 (memory) + L2 (Redis) cache
- get_cache(): Factory function for cache instances
"""

import asyncio
import logging
import pickle
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

import redis.asyncio as redis

from app.core.cache.keys import CacheKeyGenerator, generate_stats_key
from app.core.cache.strategies import (
    PatternStrategy,
    TagBasedStrategy,
    TTLStrategy,
    WriteThroughStrategy,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry with metadata.

    Stores cached value along with creation time, TTL, and tags
    for comprehensive cache management.
    """

    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: int | None = None
    tags: list[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """
        Check if cache entry has expired.

        Returns:
            True if entry has exceeded its TTL, False otherwise
        """
        if self.ttl is None:
            return False

        age = time.time() - self.created_at
        return age > self.ttl

    def touch(self) -> None:
        """
        Update access metadata for LRU tracking.
        """
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheStats:
    """
    Cache statistics for monitoring performance.

    Tracks hits, misses, evictions, and timing for both L1 and L2 caches.
    """

    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_time_ms: float = 0.0

    @property
    def total_hits(self) -> int:
        """Total cache hits across all levels."""
        return self.l1_hits + self.l2_hits

    @property
    def total_misses(self) -> int:
        """Total cache misses across all levels."""
        return self.l1_misses + self.l2_misses

    @property
    def total_requests(self) -> int:
        """Total cache requests."""
        return self.total_hits + self.total_misses

    @property
    def hit_rate(self) -> float:
        """Overall cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_hits / self.total_requests

    @property
    def l1_hit_rate(self) -> float:
        """L1 cache hit rate."""
        l1_total = self.l1_hits + self.l1_misses
        if l1_total == 0:
            return 0.0
        return self.l1_hits / l1_total

    @property
    def l2_hit_rate(self) -> float:
        """L2 cache hit rate (when L1 misses)."""
        if self.l1_misses == 0:
            return 0.0
        return self.l2_hits / self.l1_misses

    @property
    def avg_time_ms(self) -> float:
        """Average request time in milliseconds."""
        if self.total_requests == 0:
            return 0.0
        return self.total_time_ms / self.total_requests

    def to_dict(self) -> dict[str, Any]:
        """
        Convert statistics to dictionary.

        Returns:
            Dictionary with all statistics
        """
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "total_requests": self.total_requests,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 3),
            "l1_hit_rate": round(self.l1_hit_rate, 3),
            "l2_hit_rate": round(self.l2_hit_rate, 3),
            "avg_time_ms": round(self.avg_time_ms, 2),
        }


class MultiLevelCache:
    """
    Multi-level cache with L1 (memory) and L2 (Redis) support.

    Implements read-through, write-through, and cache-aside patterns
    with automatic promotion from L2 to L1 on cache hits.

    Example:
        cache = MultiLevelCache(
            namespace="schedule",
            l1_max_size=1000,
            default_ttl=300
        )

        # Cache-aside pattern
        value = await cache.get("my_key")
        if value is None:
            value = await fetch_from_database()
            await cache.set("my_key", value, ttl=300)

        # Read-through pattern
        value = await cache.get_or_fetch(
            "my_key",
            fetch_func=fetch_from_database,
            ttl=300
        )
    """

    def __init__(
        self,
        namespace: str = "cache",
        l1_enabled: bool = True,
        l1_max_size: int = 1000,
        l2_enabled: bool = True,
        default_ttl: int = 300,
        key_prefix: str = "cache",
        version: str = "v1",
    ) -> None:
        """
        Initialize multi-level cache.

        Args:
            namespace: Cache namespace for key organization
            l1_enabled: Enable L1 (memory) cache
            l1_max_size: Maximum number of entries in L1 cache
            l2_enabled: Enable L2 (Redis) cache
            default_ttl: Default time-to-live in seconds
            key_prefix: Global prefix for all cache keys
            version: Cache version for invalidation
        """
        self.namespace = namespace
        self.l1_enabled = l1_enabled
        self.l1_max_size = l1_max_size
        self.l2_enabled = l2_enabled
        self.default_ttl = default_ttl

        # L1 cache (LRU OrderedDict)
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._l1_lock = RLock()

        # L2 cache (Redis)
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

        # Key generation
        self.key_generator = CacheKeyGenerator(
            namespace=namespace, version=version, prefix=key_prefix
        )

        # Statistics
        self.stats = CacheStats()
        self._stats_lock = RLock()

        # Invalidation strategies
        self.ttl_strategy = TTLStrategy(namespace, default_ttl)
        self.tag_strategy = TagBasedStrategy(namespace)
        self.pattern_strategy = PatternStrategy(namespace)
        self.write_strategy = WriteThroughStrategy(namespace)

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

    async def get(
        self, key: str, use_l1: bool = True, use_l2: bool = True
    ) -> Any | None:
        """
        Get value from cache (L1 then L2).

        Args:
            key: Cache key (without prefix)
            use_l1: Check L1 cache
            use_l2: Check L2 cache if L1 misses

        Returns:
            Cached value or None if not found

        Example:
            value = await cache.get("user:123:profile")
        """
        start_time = time.time()

        try:
            # Try L1 cache first
            if self.l1_enabled and use_l1:
                value = self._get_from_l1(key)
                if value is not None:
                    self._record_l1_hit()
                    return value
                self._record_l1_miss()

                # Try L2 cache (Redis)
            if self.l2_enabled and use_l2:
                value = await self._get_from_l2(key)
                if value is not None:
                    self._record_l2_hit()

                    # Promote to L1
                    if self.l1_enabled and use_l1:
                        self._set_in_l1(key, value)

                    return value
                self._record_l2_miss()

            return None

        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_time(elapsed_ms)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: list[str] | None = None,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> bool:
        """
        Set value in cache (both L1 and L2).

        Args:
            key: Cache key (without prefix)
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            tags: Optional tags for tag-based invalidation
            use_l1: Store in L1 cache
            use_l2: Store in L2 cache

        Returns:
            True if value was cached successfully

        Example:
            await cache.set("user:123:profile", user_data, ttl=300, tags=["user:123"])
        """
        ttl = ttl or self.default_ttl
        tags = tags or []

        success = True

        # Set in L1
        if self.l1_enabled and use_l1:
            entry = CacheEntry(value=value, ttl=ttl, tags=tags)
            self._set_in_l1(key, entry)

            # Set in L2
        if self.l2_enabled and use_l2:
            success = await self._set_in_l2(key, value, ttl, tags)

        if success:
            self._record_set()

        return success

    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int | None = None,
        tags: list[str] | None = None,
        *args,
        **kwargs,
    ) -> Any:
        """
        Read-through cache pattern: get from cache or fetch and cache.

        Args:
            key: Cache key
            fetch_func: Async function to call if cache misses
            ttl: Time-to-live for cached value
            tags: Tags for invalidation
            *args: Arguments to pass to fetch_func
            **kwargs: Keyword arguments to pass to fetch_func

        Returns:
            Cached or fetched value

        Example:
            async def fetch_user(user_id: int):
                return await db.get_user(user_id)

            user = await cache.get_or_fetch(
                "user:123",
                fetch_user,
                ttl=300,
                user_id=123
            )
        """
        # Try cache first
        value = await self.get(key)
        if value is not None:
            return value

            # Cache miss - fetch value
        if asyncio.iscoroutinefunction(fetch_func):
            value = await fetch_func(*args, **kwargs)
        else:
            value = fetch_func(*args, **kwargs)

            # Cache the fetched value
        if value is not None:
            await self.set(key, value, ttl=ttl, tags=tags)

        return value

    async def delete(self, key: str) -> bool:
        """
        Delete entry from both L1 and L2 caches.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted

        Example:
            await cache.delete("user:123:profile")
        """
        deleted = False

        # Delete from L1
        if self.l1_enabled:
            deleted = self._delete_from_l1(key) or deleted

            # Delete from L2
        if self.l2_enabled:
            deleted = await self._delete_from_l2(key) or deleted

        if deleted:
            self._record_delete()

        return deleted

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with a specific tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated

        Example:
            # Invalidate all cache entries for user 123
            count = await cache.invalidate_by_tag("user:123")
        """
        if not self.l2_enabled:
            return 0

        redis_client = await self._get_redis()
        count = await self.tag_strategy.invalidate_by_tag(redis_client, tag)

        # Also clear L1 (since we don't have perfect tag tracking in L1)
        self._clear_l1()

        return count

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "user:*:profile")

        Returns:
            Number of entries invalidated

        Example:
            # Invalidate all user profiles
            count = await cache.invalidate_by_pattern("user:*:profile")
        """
        if not self.l2_enabled:
            return 0

        redis_client = await self._get_redis()

        # Build full pattern with namespace
        full_pattern = self.key_generator.generate_pattern() + pattern

        count = await self.pattern_strategy.invalidate_by_pattern(
            redis_client, full_pattern
        )

        # Also clear L1
        self._clear_l1()

        return count

    async def clear(self) -> int:
        """
        Clear all cache entries in this namespace.

        Returns:
            Number of entries cleared

        Example:
            count = await cache.clear()
        """
        count = 0

        # Clear L1
        if self.l1_enabled:
            count += len(self._l1_cache)
            self._clear_l1()

            # Clear L2
        if self.l2_enabled:
            pattern = self.key_generator.generate_pattern()
            redis_client = await self._get_redis()
            count += await self.pattern_strategy.invalidate_by_pattern(
                redis_client, pattern
            )

        logger.info(f"Cleared {count} entries from cache namespace '{self.namespace}'")
        return count

    async def warm(self, entries: dict[str, Any], ttl: int | None = None) -> int:
        """
        Warm cache with pre-computed values.

        Args:
            entries: Dictionary of {key: value} to cache
            ttl: Time-to-live for all entries

        Returns:
            Number of entries cached

        Example:
            # Pre-warm cache on startup
            await cache.warm({
                "config:settings": settings_dict,
                "config:features": features_dict
            }, ttl=3600)
        """
        count = 0
        ttl = ttl or self.default_ttl

        for key, value in entries.items():
            success = await self.set(key, value, ttl=ttl)
            if success:
                count += 1

        logger.info(f"Cache warmed with {count} entries")
        return count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with performance metrics

        Example:
            stats = cache.get_stats()
            print(f"Hit rate: {stats['hit_rate']:.2%}")
        """
        with self._stats_lock:
            stats_dict = self.stats.to_dict()
            stats_dict.update(
                {
                    "namespace": self.namespace,
                    "l1_enabled": self.l1_enabled,
                    "l1_size": len(self._l1_cache),
                    "l1_max_size": self.l1_max_size,
                    "l2_enabled": self.l2_enabled,
                }
            )
            return stats_dict

    async def persist_stats(self) -> bool:
        """
        Persist statistics to Redis.

        Returns:
            True if statistics were persisted successfully
        """
        if not self.l2_enabled:
            return False

        try:
            redis_client = await self._get_redis()
            stats_key = generate_stats_key(self.namespace)
            stats_data = pickle.dumps(self.stats)

            await redis_client.set(stats_key, stats_data, ex=86400)  # 24 hours
            return True

        except Exception as e:
            logger.error(f"Failed to persist cache stats: {e}")
            return False

            # L1 cache operations

    def _get_from_l1(self, key: str) -> Any | None:
        """
        Get value from L1 cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._l1_lock:
            if key not in self._l1_cache:
                return None

            entry = self._l1_cache[key]

            # Check expiration
            if entry.is_expired():
                del self._l1_cache[key]
                return None

                # Touch for LRU
            entry.touch()

            # Move to end for LRU
            self._l1_cache.move_to_end(key)

            return entry.value

    def _set_in_l1(self, key: str, value: Any) -> None:
        """
        Set value in L1 cache with LRU eviction.

        Args:
            key: Cache key
            value: Value to cache (can be CacheEntry or raw value)
        """
        with self._l1_lock:
            # Convert to CacheEntry if needed
            if not isinstance(value, CacheEntry):
                value = CacheEntry(value=value)

                # Check size limit and evict oldest if needed
            if len(self._l1_cache) >= self.l1_max_size:
                oldest_key, _ = self._l1_cache.popitem(last=False)
                self._record_eviction()
                logger.debug(f"L1 evicted key: {oldest_key}")

            self._l1_cache[key] = value

    def _delete_from_l1(self, key: str) -> bool:
        """
        Delete key from L1 cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        with self._l1_lock:
            if key in self._l1_cache:
                del self._l1_cache[key]
                return True
            return False

    def _clear_l1(self) -> None:
        """Clear all entries from L1 cache."""
        with self._l1_lock:
            self._l1_cache.clear()

            # L2 cache operations

    async def _get_from_l2(self, key: str) -> Any | None:
        """
        Get value from L2 (Redis) cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            redis_client = await self._get_redis()
            prefixed_key = self.key_generator.generate(key, include_version=True)

            data = await redis_client.get(prefixed_key)
            if data is None:
                return None

                # Deserialize
            value = pickle.loads(data)
            return value

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on get: {e}")
            return None
        except Exception as e:
            logger.error(f"L2 cache get error for key {key}: {e}")
            return None

    async def _set_in_l2(self, key: str, value: Any, ttl: int, tags: list[str]) -> bool:
        """
        Set value in L2 (Redis) cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            tags: Tags for invalidation

        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis()
            prefixed_key = self.key_generator.generate(key, include_version=True)

            # Serialize value
            data = pickle.dumps(value)

            # Set with TTL
            await redis_client.setex(prefixed_key, ttl, data)

            # Add tags if provided
            if tags:
                await self.tag_strategy.add_tags(redis_client, prefixed_key, tags)

            return True

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on set: {e}")
            return False
        except Exception as e:
            logger.error(f"L2 cache set error for key {key}: {e}")
            return False

    async def _delete_from_l2(self, key: str) -> bool:
        """
        Delete key from L2 (Redis) cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        try:
            redis_client = await self._get_redis()
            prefixed_key = self.key_generator.generate(key, include_version=True)

            deleted = await redis_client.delete(prefixed_key)
            return deleted > 0

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on delete: {e}")
            return False
        except Exception as e:
            logger.error(f"L2 cache delete error for key {key}: {e}")
            return False

            # Statistics tracking

    def _record_l1_hit(self) -> None:
        """Record L1 cache hit."""
        with self._stats_lock:
            self.stats.l1_hits += 1

    def _record_l1_miss(self) -> None:
        """Record L1 cache miss."""
        with self._stats_lock:
            self.stats.l1_misses += 1

    def _record_l2_hit(self) -> None:
        """Record L2 cache hit."""
        with self._stats_lock:
            self.stats.l2_hits += 1

    def _record_l2_miss(self) -> None:
        """Record L2 cache miss."""
        with self._stats_lock:
            self.stats.l2_misses += 1

    def _record_set(self) -> None:
        """Record cache set operation."""
        with self._stats_lock:
            self.stats.sets += 1

    def _record_delete(self) -> None:
        """Record cache delete operation."""
        with self._stats_lock:
            self.stats.deletes += 1

    def _record_eviction(self) -> None:
        """Record cache eviction."""
        with self._stats_lock:
            self.stats.evictions += 1

    def _record_time(self, elapsed_ms: float) -> None:
        """Record request time."""
        with self._stats_lock:
            self.stats.total_time_ms += elapsed_ms

            # Global cache instances by namespace


_cache_instances: dict[str, MultiLevelCache] = {}
_cache_lock = RLock()


def get_cache(namespace: str = "default", **kwargs) -> MultiLevelCache:
    """
    Get or create a cache instance for a namespace.

    Args:
        namespace: Cache namespace
        **kwargs: Additional arguments for MultiLevelCache

    Returns:
        MultiLevelCache instance for the namespace

    Example:
        # Get cache for schedule namespace
        schedule_cache = get_cache("schedule", l1_max_size=2000)

        # Use the cache
        await schedule_cache.set("key", "value", ttl=300)
    """
    global _cache_instances

    with _cache_lock:
        if namespace not in _cache_instances:
            _cache_instances[namespace] = MultiLevelCache(namespace=namespace, **kwargs)

        return _cache_instances[namespace]
