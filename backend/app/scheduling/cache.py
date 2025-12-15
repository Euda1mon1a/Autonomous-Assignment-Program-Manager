"""
Caching Layer for Scheduling System.

Provides:
- In-memory caching for schedule computations
- Cache invalidation strategies
- TTL-based cache expiration
- Cache key generation utilities
"""
import time
import hashlib
import json
import threading
import logging
from typing import Any, Optional, Callable, Union
from datetime import datetime, date, timedelta
from collections import OrderedDict
from uuid import UUID
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ==================================================
# CACHE KEY GENERATION
# ==================================================

class CacheKeyGenerator:
    """
    Utilities for generating cache keys from complex objects.

    Features:
    - Handles UUIDs, dates, lists, dicts
    - Deterministic hashing
    - Collision-resistant
    """

    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate a cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash-based cache key string
        """
        key_parts = []

        # Process args
        for arg in args:
            key_parts.append(CacheKeyGenerator._serialize_value(arg))

        # Process kwargs (sorted for determinism)
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            key_parts.append(f"{key}={CacheKeyGenerator._serialize_value(value)}")

        # Create hash
        combined = "|".join(key_parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def _serialize_value(value: Any) -> str:
        """Serialize a value to a string for hashing."""
        if value is None:
            return "None"
        elif isinstance(value, UUID):
            return f"UUID:{value}"
        elif isinstance(value, (date, datetime)):
            return f"DATE:{value.isoformat()}"
        elif isinstance(value, (list, tuple)):
            items = [CacheKeyGenerator._serialize_value(v) for v in value]
            return f"LIST:[{','.join(items)}]"
        elif isinstance(value, dict):
            items = [
                f"{k}={CacheKeyGenerator._serialize_value(v)}"
                for k, v in sorted(value.items())
            ]
            return f"DICT:{{{','.join(items)}}}"
        elif isinstance(value, (int, float, str, bool)):
            return f"{type(value).__name__}:{value}"
        else:
            # Fallback to string representation
            return f"OBJ:{type(value).__name__}:{str(value)}"

    @staticmethod
    def generate_pattern_key(pattern: str, **params) -> str:
        """
        Generate a key based on a pattern.

        Example:
            key = generate_pattern_key(
                "schedule:{org_id}:{start}:{end}",
                org_id=org_id,
                start=start_date,
                end=end_date
            )
        """
        for param_name, param_value in params.items():
            placeholder = f"{{{param_name}}}"
            serialized = CacheKeyGenerator._serialize_value(param_value)
            pattern = pattern.replace(placeholder, serialized)
        return pattern


# ==================================================
# CACHE ENTRY
# ==================================================

@dataclass
class CacheEntry:
    """
    Represents a single cache entry with metadata.
    """
    value: Any
    created_at: float
    ttl: Optional[float]
    access_count: int = 0
    last_accessed: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if the entry has expired based on TTL."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def access(self):
        """Record an access to this entry."""
        self.access_count += 1
        self.last_accessed = time.time()


# ==================================================
# IN-MEMORY CACHE
# ==================================================

class ScheduleCache:
    """
    Thread-safe in-memory cache for schedule computations.

    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Automatic cleanup
    - Cache statistics

    Example:
        cache = ScheduleCache(max_size=1000, default_ttl=300)

        # Store value
        cache.set("key1", value, ttl=600)

        # Retrieve value
        value = cache.get("key1")

        # Invalidate
        cache.invalidate("key1")
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = 300,  # 5 minutes
        cleanup_interval: float = 60,  # 1 minute
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

        # OrderedDict for LRU eviction
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return default

            # Move to end (LRU)
            self._cache.move_to_end(key)
            entry.access()
            self._hits += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = use default)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl

            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )

            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)

            # Evict if over size limit
            if len(self._cache) > self.max_size:
                # Remove oldest (first item)
                self._cache.popitem(last=False)
                self._evictions += 1

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was in cache, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (supports * wildcard)

        Returns:
            Number of keys invalidated
        """
        import re

        # Convert glob pattern to regex
        regex_pattern = pattern.replace("*", ".*")
        regex = re.compile(f"^{regex_pattern}$")

        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if regex.match(key)
            ]

            for key in keys_to_delete:
                del self._cache[key]

            return len(keys_to_delete)

    def invalidate_all(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def _cleanup_loop(self):
        """Background thread to cleanup expired entries."""
        while True:
            time.sleep(self.cleanup_interval)
            self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'requests': total_requests,
            }

    def reset_stats(self):
        """Reset cache statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0


# ==================================================
# CACHE DECORATOR
# ==================================================

class cached:
    """
    Decorator for caching function results.

    Example:
        cache = ScheduleCache()

        @cached(cache, ttl=300, key_prefix="solver")
        def expensive_solver_operation(context, algorithm):
            # ... computation
            return result
    """

    def __init__(
        self,
        cache: ScheduleCache,
        ttl: Optional[float] = None,
        key_prefix: str = "",
        key_func: Optional[Callable] = None
    ):
        self.cache = cache
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.key_func = key_func

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            if self.key_func:
                cache_key = self.key_func(*args, **kwargs)
            else:
                cache_key = CacheKeyGenerator.generate_key(*args, **kwargs)

            # Add prefix
            if self.key_prefix:
                cache_key = f"{self.key_prefix}:{cache_key}"

            # Check cache
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Compute and cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result, ttl=self.ttl)

            return result

        return wrapper


# ==================================================
# INVALIDATION STRATEGIES
# ==================================================

class CacheInvalidationStrategy:
    """
    Base class for cache invalidation strategies.
    """

    def __init__(self, cache: ScheduleCache):
        self.cache = cache

    def on_assignment_created(self, assignment):
        """Called when an assignment is created."""
        pass

    def on_assignment_updated(self, assignment):
        """Called when an assignment is updated."""
        pass

    def on_assignment_deleted(self, assignment):
        """Called when an assignment is deleted."""
        pass

    def on_schedule_generated(self, start_date, end_date):
        """Called when a new schedule is generated."""
        pass


class PatternInvalidationStrategy(CacheInvalidationStrategy):
    """
    Invalidation strategy based on pattern matching.

    Invalidates cache entries matching specific patterns
    when schedule data changes.
    """

    def on_assignment_created(self, assignment):
        """Invalidate caches related to the assignment's block."""
        # Invalidate block-specific caches
        self.cache.invalidate_pattern(f"*:block:{assignment.block_id}:*")
        # Invalidate person-specific caches
        self.cache.invalidate_pattern(f"*:person:{assignment.person_id}:*")
        logger.debug(f"Invalidated caches for assignment creation")

    def on_assignment_updated(self, assignment):
        """Invalidate caches related to the updated assignment."""
        self.on_assignment_created(assignment)

    def on_assignment_deleted(self, assignment):
        """Invalidate caches related to the deleted assignment."""
        self.on_assignment_created(assignment)

    def on_schedule_generated(self, start_date, end_date):
        """Invalidate all schedule-related caches for the date range."""
        # Invalidate schedule caches
        self.cache.invalidate_pattern(f"schedule:*")
        self.cache.invalidate_pattern(f"availability:*")
        logger.info(f"Invalidated schedule caches for {start_date} to {end_date}")


class TimeBasedInvalidationStrategy(CacheInvalidationStrategy):
    """
    Invalidation strategy that relies purely on TTL.

    No manual invalidation - entries expire based on TTL only.
    Simple and safe, but may serve stale data.
    """

    def __init__(self, cache: ScheduleCache, default_ttl: float = 300):
        super().__init__(cache)
        self.default_ttl = default_ttl
        logger.info(f"Using time-based invalidation with TTL={default_ttl}s")

    # No-op implementations - rely on TTL
    def on_assignment_created(self, assignment):
        pass

    def on_assignment_updated(self, assignment):
        pass

    def on_assignment_deleted(self, assignment):
        pass

    def on_schedule_generated(self, start_date, end_date):
        pass


class AggressiveInvalidationStrategy(CacheInvalidationStrategy):
    """
    Invalidation strategy that clears entire cache on any change.

    Safe but not optimal for performance.
    Use when cache coherence is critical.
    """

    def on_assignment_created(self, assignment):
        self.cache.invalidate_all()
        logger.debug("Aggressive invalidation: cleared all caches")

    def on_assignment_updated(self, assignment):
        self.cache.invalidate_all()

    def on_assignment_deleted(self, assignment):
        self.cache.invalidate_all()

    def on_schedule_generated(self, start_date, end_date):
        self.cache.invalidate_all()


# ==================================================
# GLOBAL CACHE INSTANCE
# ==================================================

# Singleton cache instance for application-wide use
_global_cache: Optional[ScheduleCache] = None


def get_schedule_cache(
    max_size: int = 1000,
    default_ttl: float = 300
) -> ScheduleCache:
    """
    Get or create the global schedule cache instance.

    Args:
        max_size: Maximum cache size
        default_ttl: Default TTL in seconds

    Returns:
        Global ScheduleCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = ScheduleCache(
            max_size=max_size,
            default_ttl=default_ttl
        )
        logger.info(f"Initialized global schedule cache (max_size={max_size}, ttl={default_ttl}s)")

    return _global_cache


def clear_global_cache():
    """Clear the global cache if it exists."""
    global _global_cache

    if _global_cache is not None:
        _global_cache.invalidate_all()
