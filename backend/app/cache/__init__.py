"""
Cache package for advanced invalidation, warming, and caching features.

This package provides:
- CacheInvalidationService: Comprehensive cache invalidation
- Tag-based, pattern-based, and dependency-aware invalidation
- Invalidation event publishing and metrics tracking
- Batch and cascading invalidation strategies
- CacheWarmer: Intelligent cache warming service
- Priority-based cache warming
- Startup cache population
- Scheduled cache refresh
- Cache hit prediction
- Warming progress tracking
"""

from app.cache.invalidation import (
    CacheInvalidationService,
    InvalidationEvent,
    InvalidationEventType,
    InvalidationMetrics,
    get_invalidation_service,
)
from app.cache.warming import (
    CacheWarmer,
    CacheWarmingConfig,
    CacheWarmingMetrics,
    CacheWarmingProgress,
    WarmingPriority,
    WarmingStrategy,
    get_cache_warmer,
)

__all__ = [
    # Invalidation
    "CacheInvalidationService",
    "InvalidationEvent",
    "InvalidationEventType",
    "InvalidationMetrics",
    "get_invalidation_service",
    # Warming
    "CacheWarmer",
    "CacheWarmingConfig",
    "CacheWarmingMetrics",
    "CacheWarmingProgress",
    "WarmingPriority",
    "WarmingStrategy",
    "get_cache_warmer",
]

__version__ = "1.0.0"
