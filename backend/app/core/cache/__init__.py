"""
Advanced Redis caching package.

Provides comprehensive caching solutions with multi-level caching,
tag-based invalidation, and easy-to-use decorators.

This package provides:
- MultiLevelCache: L1 (memory) + L2 (Redis) cache implementation
- Cache decorators: @cached, @cache_invalidate, @cache_warm
- Invalidation strategies: TTL, tag-based, pattern-based, write-through
- Cache key generators: Consistent key generation with versioning

Quick Start:
    from app.core.cache import get_cache, cached, cache_invalidate

    # Get a cache instance
    cache = get_cache("schedule")

    # Use the cache
    await cache.set("key", "value", ttl=300)
    value = await cache.get("key")

    # Use decorators
    @cached(namespace="schedule", ttl=300, tags=["schedule"])
    async def get_schedule(user_id: int):
        return await db.fetch_schedule(user_id)

    @cache_invalidate(namespace="schedule", tags=["schedule"])
    async def update_schedule(user_id: int, data: dict):
        await db.update_schedule(user_id, data)

Patterns Supported:
    - Cache-aside: Manual cache management
    - Read-through: Automatic caching on reads
    - Write-through: Automatic invalidation on writes
    - Multi-level: L1 (memory) + L2 (Redis) for optimal performance

Features:
    - TTL-based expiration
    - Tag-based invalidation
    - Pattern-based invalidation
    - LRU eviction in L1 cache
    - Cache warming on startup
    - Statistics tracking
    - Async/await support
"""

from enum import Enum


class CachePrefix(Enum):
    """Cache key prefixes for different services."""
    SCHEDULE = "schedule"
    HEATMAP = "heatmap"
    COVERAGE = "coverage"
    CALENDAR = "calendar"
    PERSON = "person"
    ASSIGNMENT = "assignment"
    BLOCK = "block"
    ROTATION = "rotation"
    SEARCH = "search"
    FACETS = "facets"
    AUTOCOMPLETE = "autocomplete"


class CacheTTL:
    """Standard cache TTL values in seconds."""
    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 900  # 15 minutes
    HOUR = 3600  # 1 hour
    DAY = 86400  # 24 hours


# Global service cache instance
_service_cache = None


def get_service_cache():
    """Get or create the global service cache instance."""
    global _service_cache
    if _service_cache is None:
        _service_cache = get_cache("service")
    return _service_cache

# Core cache classes
from app.core.cache.redis_cache import (
    CacheEntry,
    CacheStats,
    MultiLevelCache,
    get_cache,
)

# Cache key generators
from app.core.cache.keys import (
    CacheKeyGenerator,
    generate_cache_key,
    generate_stats_key,
    generate_tag_key,
)

# Invalidation strategies
from app.core.cache.strategies import (
    InvalidationStrategy,
    InvalidationTrigger,
    PatternStrategy,
    TagBasedStrategy,
    TTLStrategy,
    WriteThroughStrategy,
)

# Decorators
from app.core.cache.decorators import (
    cache_invalidate,
    cache_warm,
    cached,
    cached_property_async,
    invalidate_on_write,
    read_through,
    write_through,
)

# Utility functions
from app.core.cache.utils import invalidate_schedule_cache

__all__ = [
    # Cache prefixes and TTL
    "CachePrefix",
    "CacheTTL",
    "get_service_cache",
    # Core cache
    "CacheEntry",
    "CacheStats",
    "MultiLevelCache",
    "get_cache",
    # Key generators
    "CacheKeyGenerator",
    "generate_cache_key",
    "generate_tag_key",
    "generate_stats_key",
    # Strategies
    "InvalidationStrategy",
    "InvalidationTrigger",
    "TTLStrategy",
    "TagBasedStrategy",
    "PatternStrategy",
    "WriteThroughStrategy",
    # Decorators
    "cached",
    "cache_invalidate",
    "cache_warm",
    "invalidate_on_write",
    "cached_property_async",
    "read_through",
    "write_through",
    # Utility functions
    "invalidate_schedule_cache",
]

# Version
__version__ = "1.0.0"
