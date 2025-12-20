"""
Service-level caching module for Redis-backed operations.

Provides a unified caching interface for service layer operations
including heatmaps, calendars, and schedule queries.

This module provides:
- CachePrefix: Enum for cache key namespacing
- CacheTTL: Constants for cache time-to-live values
- ServiceCache: Redis-backed cache for service operations
- get_service_cache(): Factory function for cache instances
- invalidate_schedule_cache(): Utility to clear schedule-related caches
"""
import logging
import pickle
from enum import Enum
from threading import RLock
from typing import Any

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CachePrefix(str, Enum):
    """
    Cache key prefixes for different cache domains.

    Using prefixes enables selective cache invalidation
    and prevents key collisions between different services.
    """

    HEATMAP = "svc:heatmap"
    COVERAGE = "svc:coverage"
    WORKLOAD = "svc:workload"
    CALENDAR = "svc:calendar"
    SCHEDULE = "svc:schedule"
    VALIDATION = "svc:validation"


class CacheTTL:
    """
    Default TTL values for different cache types.

    These can be overridden by settings but provide sensible defaults.
    All values are in seconds.
    """

    # Short-lived caches (frequently changing data)
    SHORT = 60  # 1 minute

    # Medium-lived caches (heatmaps, calendars)
    MEDIUM = 300  # 5 minutes

    # Long-lived caches (rarely changing data)
    LONG = 3600  # 1 hour

    # Very long-lived caches (static reference data)
    EXTENDED = 86400  # 24 hours


class ServiceCache:
    """
    Redis-backed cache for service layer operations.

    Provides a simple key-value cache with TTL support,
    prefix-based namespacing, and pattern-based invalidation.

    Example:
        cache = get_service_cache()
        cache.set("my_key", {"data": "value"}, ttl=300)
        result = cache.get("my_key")
    """

    def __init__(self, key_prefix: str = "svc:"):
        """
        Initialize service cache.

        Args:
            key_prefix: Global prefix for all cache keys
        """
        self._key_prefix = key_prefix
        self._lock = RLock()
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

        # Statistics
        self._hits = 0
        self._misses = 0

    def _get_redis(self) -> redis.Redis:
        """
        Get or create Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=False)
        return self._redis

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            Cached value or None if not found/expired
        """
        prefixed_key = f"{self._key_prefix}{key}"

        try:
            redis_client = self._get_redis()
            data = redis_client.get(prefixed_key)

            if data is None:
                with self._lock:
                    self._misses += 1
                return None

            # Deserialize
            value = pickle.loads(data)

            with self._lock:
                self._hits += 1

            return value

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on get: {e}")
            with self._lock:
                self._misses += 1
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            with self._lock:
                self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key (without prefix)
            value: Value to cache (must be picklable)
            ttl: Time-to-live in seconds (default: MEDIUM)

        Returns:
            True if successful, False otherwise
        """
        if ttl is None:
            ttl = CacheTTL.MEDIUM

        prefixed_key = f"{self._key_prefix}{key}"

        try:
            redis_client = self._get_redis()
            data = pickle.dumps(value)
            redis_client.setex(prefixed_key, ttl, data)
            return True

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on set: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a specific key from cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            True if key was deleted, False otherwise
        """
        prefixed_key = f"{self._key_prefix}{key}"

        try:
            redis_client = self._get_redis()
            deleted = redis_client.delete(prefixed_key)
            return deleted > 0

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on delete: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def invalidate_by_prefix(self, prefix: CachePrefix | str) -> int:
        """
        Invalidate all cache entries with a given prefix.

        Args:
            prefix: CachePrefix enum or string prefix

        Returns:
            Number of entries invalidated
        """
        if isinstance(prefix, CachePrefix):
            prefix = prefix.value

        pattern = f"{self._key_prefix}{prefix}:*"

        try:
            redis_client = self._get_redis()
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    redis_client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted_count} cache entries with prefix {prefix}")
            return deleted_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on invalidate: {e}")
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error for prefix {prefix}: {e}")
            return 0

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Redis SCAN pattern (e.g., "svc:calendar:*:user-123:*")

        Returns:
            Number of entries invalidated
        """
        try:
            redis_client = self._get_redis()
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    redis_client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            logger.debug(f"Invalidated {deleted_count} cache entries matching {pattern}")
            return deleted_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on pattern invalidate: {e}")
            return 0
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear all service cache entries.

        Returns:
            Number of entries cleared
        """
        pattern = f"{self._key_prefix}*"

        try:
            redis_client = self._get_redis()
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    redis_client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            logger.info(f"Cleared all {deleted_count} service cache entries")
            return deleted_count

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error on clear: {e}")
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "total_requests": total_requests,
            }


# Global cache instance
_service_cache: ServiceCache | None = None


def get_service_cache() -> ServiceCache:
    """
    Get the global service cache instance.

    Returns:
        ServiceCache instance (lazily initialized)

    Example:
        cache = get_service_cache()
        cache.set("key", "value", ttl=300)
    """
    global _service_cache
    if _service_cache is None:
        _service_cache = ServiceCache()
    return _service_cache


def invalidate_schedule_cache() -> int:
    """
    Invalidate all schedule-related cache entries.

    This should be called when schedule data is modified
    to ensure stale data is not served.

    Returns:
        Total number of entries invalidated

    Example:
        # After modifying assignments
        count = invalidate_schedule_cache()
        logger.info(f"Invalidated {count} cache entries")
    """
    cache = get_service_cache()
    total = 0

    # Invalidate all schedule-related prefixes
    for prefix in [
        CachePrefix.SCHEDULE,
        CachePrefix.HEATMAP,
        CachePrefix.COVERAGE,
        CachePrefix.WORKLOAD,
        CachePrefix.CALENDAR,
        CachePrefix.VALIDATION,
    ]:
        total += cache.invalidate_by_prefix(prefix)

    logger.info(f"Invalidated {total} schedule-related cache entries")
    return total
