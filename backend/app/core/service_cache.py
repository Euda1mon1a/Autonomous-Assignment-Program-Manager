"""
Redis-based caching layer for service-level operations.

Provides decorators and utilities for caching database query results
and frequently accessed schedule data.

Features:
- Decorator-based caching for service methods
- TTL-based expiration with configurable timeouts
- Automatic cache key generation from function arguments
- Selective cache invalidation by pattern
- Statistics tracking for cache performance
- Graceful degradation when Redis is unavailable
"""

import functools
import hashlib
import logging
import pickle
from collections.abc import Callable
from datetime import date, datetime
from enum import Enum
from threading import RLock
from typing import Any, ParamSpec, TypeVar
from uuid import UUID

import redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class CachePrefix(str, Enum):
    """Cache key prefixes for different data types."""

    HEATMAP = "heatmap"
    CALENDAR = "calendar"
    ASSIGNMENTS = "assignments"
    PERSONS = "persons"
    ROTATIONS = "rotations"
    BLOCKS = "blocks"
    COVERAGE = "coverage"
    WORKLOAD = "workload"
    SCHEDULE = "schedule"
    GENERAL = "service"


class CacheTTL:
    """Standard TTL values for different cache types."""

    SHORT = 300  # 5 minutes - for rapidly changing data
    MEDIUM = 1800  # 30 minutes - for moderately stable data
    LONG = 3600  # 1 hour - for stable schedule data
    EXTENDED = 14400  # 4 hours - for rarely changing data
    DAY = 86400  # 24 hours - for static reference data
    WEEK = 604800  # 7 days - for very stable configuration


class ServiceCache:
    """
    Redis-backed caching service for database query results.

    Provides a centralized caching mechanism for service-layer operations,
    with support for automatic cache key generation, TTL management,
    and selective invalidation.

    Example usage:
        cache = get_service_cache()

        # Using decorator
        @cache.cached(prefix=CachePrefix.HEATMAP, ttl=CacheTTL.LONG)
        def get_heatmap(start_date: date, end_date: date) -> dict:
            # Expensive database query
            return {"data": ...}

        # Manual caching
        result = cache.get("heatmap:2024-01-01:2024-01-31")
        if result is None:
            result = expensive_query()
            cache.set("heatmap:2024-01-01:2024-01-31", result, ttl=3600)
    """

    KEY_PREFIX = "svc_cache:"

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl: int = CacheTTL.LONG,
        enabled: bool = True,
    ):
        """
        Initialize the service cache.

        Args:
            redis_url: Redis connection URL. If None, uses settings.
            default_ttl: Default TTL in seconds for cached items.
            enabled: Whether caching is enabled (for testing/debugging).
        """
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._lock = RLock()

        # Statistics (per-worker, not shared across processes)
        self._hits = 0
        self._misses = 0
        self._errors = 0

        # Initialize Redis connection
        settings = get_settings()
        url = redis_url or settings.redis_url_with_password

        try:
            self._redis: redis.Redis = redis.from_url(
                url,
                decode_responses=False,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
            )
            # Test connection
            self._redis.ping()
            self._available = True
            logger.info("Service cache connected to Redis")
        except RedisError as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self._redis = None  # type: ignore
            self._available = False

    @property
    def is_available(self) -> bool:
        """Check if Redis is available for caching."""
        return self._available and self.enabled

    def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key (without prefix).

        Returns:
            Cached value or None if not found/expired.
        """
        if not self.is_available:
            return None

        prefixed_key = f"{self.KEY_PREFIX}{key}"

        try:
            data = self._redis.get(prefixed_key)
            if data is None:
                with self._lock:
                    self._misses += 1
                return None

            # Deserialize
            value = pickle.loads(data)
            with self._lock:
                self._hits += 1
            return value

        except (RedisError, pickle.UnpicklingError) as e:
            logger.debug(f"Cache get error for {key}: {e}")
            with self._lock:
                self._errors += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key (without prefix).
            value: Value to cache (must be picklable).
            ttl: Time-to-live in seconds. Uses default if None.

        Returns:
            True if successfully cached, False otherwise.
        """
        if not self.is_available:
            return False

        prefixed_key = f"{self.KEY_PREFIX}{key}"
        ttl = ttl if ttl is not None else self.default_ttl

        try:
            data = pickle.dumps(value)
            self._redis.setex(prefixed_key, ttl, data)
            return True

        except (RedisError, pickle.PicklingError) as e:
            logger.debug(f"Cache set error for {key}: {e}")
            with self._lock:
                self._errors += 1
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a specific cache entry.

        Args:
            key: Cache key (without prefix).

        Returns:
            True if deleted, False otherwise.
        """
        if not self.is_available:
            return False

        prefixed_key = f"{self.KEY_PREFIX}{key}"

        try:
            deleted = self._redis.delete(prefixed_key)
            return deleted > 0

        except RedisError as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "heatmap:*", "assignments:person:*").

        Returns:
            Number of entries invalidated.
        """
        if not self.is_available:
            return 0

        full_pattern = f"{self.KEY_PREFIX}{pattern}"
        deleted_count = 0

        try:
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(
                    cursor,
                    match=full_pattern,
                    count=100,
                )
                if keys:
                    deleted_count += self._redis.delete(*keys)
                if cursor == 0:
                    break

            logger.info(
                f"Invalidated {deleted_count} cache entries matching '{pattern}'"
            )
            return deleted_count

        except RedisError as e:
            logger.warning(f"Cache invalidation error for pattern {pattern}: {e}")
            return 0

    def invalidate_by_prefix(self, prefix: CachePrefix) -> int:
        """
        Invalidate all cache entries for a specific prefix.

        Args:
            prefix: Cache prefix to invalidate.

        Returns:
            Number of entries invalidated.
        """
        return self.invalidate_pattern(f"{prefix.value}:*")

    def invalidate_all(self) -> int:
        """
        Invalidate all service cache entries.

        Returns:
            Number of entries invalidated.
        """
        return self.invalidate_pattern("*")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            # Get approximate cache size from Redis
            cache_size = 0
            if self.is_available:
                try:
                    cursor, keys = self._redis.scan(
                        0,
                        match=f"{self.KEY_PREFIX}*",
                        count=1000,
                    )
                    cache_size = len(keys)
                except RedisError:
                    pass

            return {
                "available": self.is_available,
                "enabled": self.enabled,
                "hits": self._hits,
                "misses": self._misses,
                "errors": self._errors,
                "hit_rate": round(hit_rate, 4),
                "approximate_size": cache_size,
                "default_ttl": self.default_ttl,
            }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._errors = 0

    def cached(
        self,
        prefix: CachePrefix = CachePrefix.GENERAL,
        ttl: int | None = None,
        key_builder: Callable[..., str] | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorator for caching function results.

        Args:
            prefix: Cache key prefix for categorization.
            ttl: Time-to-live in seconds. Uses default if None.
            key_builder: Optional function to build cache key from arguments.
                         If None, uses automatic key generation.

        Returns:
            Decorated function with caching.

        Example:
            @cache.cached(prefix=CachePrefix.HEATMAP, ttl=3600)
            def get_heatmap(db, start_date: date, end_date: date) -> dict:
                return {...}
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Build cache key
                if key_builder:
                    cache_key = f"{prefix.value}:{key_builder(*args, **kwargs)}"
                else:
                    cache_key = self._build_cache_key(prefix.value, func, args, kwargs)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_value

                # Execute function and cache result
                result = func(*args, **kwargs)

                # Cache the result
                effective_ttl = ttl if ttl is not None else self.default_ttl
                self.set(cache_key, result, effective_ttl)
                logger.debug(f"Cached result for {cache_key} (TTL: {effective_ttl}s)")

                return result

            # Add cache management methods to the wrapper
            wrapper.cache_invalidate = lambda: self.invalidate_pattern(  # type: ignore
                f"{prefix.value}:{func.__name__}:*"
            )

            return wrapper

        return decorator

    def _build_cache_key(
        self,
        prefix: str,
        func: Callable,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """
        Build a cache key from function arguments.

        Handles special types like UUID, date, datetime, and SQLAlchemy sessions.
        """
        key_parts = [prefix, func.__name__]

        # Process positional arguments (skip 'self' and db session)
        for i, arg in enumerate(args):
            # Skip SQLAlchemy Session and 'self' reference
            if hasattr(arg, "execute") or hasattr(arg, "__self__"):
                continue
            key_parts.append(self._serialize_arg(arg))

        # Process keyword arguments (sorted for consistency)
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            # Skip db session
            if k == "db" or hasattr(v, "execute"):
                continue
            key_parts.append(f"{k}={self._serialize_arg(v)}")

        # Join and hash if too long
        key = ":".join(key_parts)
        if len(key) > 200:
            # Hash long keys to keep them manageable
            hash_suffix = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()[
                :12
            ]
            key = f"{prefix}:{func.__name__}:{hash_suffix}"

        return key

    @staticmethod
    def _serialize_arg(arg: Any) -> str:
        """Serialize an argument to a string for cache key."""
        if arg is None:
            return "None"
        elif isinstance(arg, UUID):
            return str(arg)
        elif isinstance(arg, (date, datetime)):
            return arg.isoformat()
        elif isinstance(arg, (list, tuple)):
            # Sort UUIDs for consistent ordering
            items = sorted(str(item) for item in arg)
            return f"[{','.join(items[:10])}]"  # Limit to first 10 items
        elif isinstance(arg, dict):
            # Create deterministic string representation
            sorted_items = sorted((str(k), str(v)) for k, v in arg.items())
            return f"{{{','.join(f'{k}:{v}' for k, v in sorted_items[:10])}}}"
        elif isinstance(arg, bool):
            return str(arg).lower()
        elif isinstance(arg, (int, float)):
            return str(arg)
        elif isinstance(arg, str):
            return arg[:50]  # Truncate long strings
        elif isinstance(arg, Enum):
            return arg.value
        else:
            # For other types, use hash of string representation
            return hashlib.md5(str(arg).encode(), usedforsecurity=False).hexdigest()[:8]


# Global cache instance
_service_cache: ServiceCache | None = None
_cache_lock = RLock()


def get_service_cache() -> ServiceCache:
    """
    Get or create the global service cache instance.

    Returns:
        ServiceCache: Singleton cache instance.
    """
    global _service_cache

    with _cache_lock:
        if _service_cache is None:
            _service_cache = ServiceCache()
        return _service_cache


def invalidate_schedule_cache() -> int:
    """
    Invalidate all schedule-related cache entries.

    Call this when assignments, blocks, or schedules are modified.

    Returns:
        Number of entries invalidated.
    """
    cache = get_service_cache()
    count = 0
    count += cache.invalidate_by_prefix(CachePrefix.HEATMAP)
    count += cache.invalidate_by_prefix(CachePrefix.CALENDAR)
    count += cache.invalidate_by_prefix(CachePrefix.ASSIGNMENTS)
    count += cache.invalidate_by_prefix(CachePrefix.COVERAGE)
    count += cache.invalidate_by_prefix(CachePrefix.WORKLOAD)
    count += cache.invalidate_by_prefix(CachePrefix.SCHEDULE)
    logger.info(f"Invalidated {count} schedule-related cache entries")
    return count


def invalidate_person_cache(person_id: UUID | None = None) -> int:
    """
    Invalidate person-related cache entries.

    Args:
        person_id: Specific person to invalidate, or all if None.

    Returns:
        Number of entries invalidated.
    """
    cache = get_service_cache()
    if person_id:
        pattern = f"*:{person_id}*"
        return cache.invalidate_pattern(pattern)
    return cache.invalidate_by_prefix(CachePrefix.PERSONS)


def invalidate_rotation_cache() -> int:
    """
    Invalidate rotation template cache entries.

    Returns:
        Number of entries invalidated.
    """
    cache = get_service_cache()
    return cache.invalidate_by_prefix(CachePrefix.ROTATIONS)
