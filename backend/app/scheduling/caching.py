"""
Caching Layer for Scheduling Engine.

Provides Redis-based caching for expensive operations:
- Availability matrix lookups
- Assignment count calculations
- Constraint validation results
- Solver intermediate results
"""
import logging
import pickle
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from threading import RLock
from typing import Any
from uuid import UUID

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ScheduleCache:
    """
    Redis-backed cache for scheduling operations.

    Features:
    - Shared cache across uvicorn workers
    - TTL-based expiration
    - Selective cache invalidation
    - Pre-warming for common queries
    """

    KEY_PREFIX = "scheduler_cache:"

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached entries (unused with Redis)
            ttl_seconds: Time-to-live for cached entries (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = RLock()

        # Redis connection
        settings = get_settings()
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=False)

        # Statistics (per-worker, not shared)
        self._hits = 0
        self._misses = 0

    def get_availability_matrix(
        self,
        person_ids: list[UUID],
        block_ids: list[UUID],
        availability_data: dict,
    ) -> dict[UUID, dict[UUID, dict]]:
        """
        Get availability matrix with caching.

        Args:
            person_ids: List of person UUIDs
            block_ids: List of block UUIDs
            availability_data: Full availability data

        Returns:
            Filtered availability matrix
        """
        # Create cache key from sorted IDs
        cache_key = self._create_key(
            "availability",
            sorted(str(p) for p in person_ids[:10]),  # Limit key size
            sorted(str(b) for b in block_ids[:10]),
        )

        # Try cache first
        cached = self._get(cache_key)
        if cached is not None:
            return cached

        # Build matrix
        matrix = {}
        for person_id in person_ids:
            if person_id in availability_data:
                matrix[person_id] = {
                    block_id: availability_data[person_id][block_id]
                    for block_id in block_ids
                    if block_id in availability_data[person_id]
                }

        # Cache result
        self._put(cache_key, matrix)
        return matrix

    def get_assignment_counts(
        self,
        person_id: UUID,
        assignments: list,
    ) -> dict[str, int]:
        """
        Get cached assignment counts for a person.

        Args:
            person_id: Person UUID
            assignments: List of Assignment objects

        Returns:
            Dictionary with count metrics:
            - total: Total assignments
            - by_week: Assignments per week
            - by_template: Assignments per rotation template
        """
        cache_key = self._create_key("assignment_counts", str(person_id))

        # Try cache
        cached = self._get(cache_key)
        if cached is not None:
            return cached

        # Calculate counts
        total = 0
        by_week = defaultdict(int)
        by_template = defaultdict(int)

        for assignment in assignments:
            if assignment.person_id == person_id:
                total += 1

                # Week counting requires block date lookup
                # For now, just count by template
                if assignment.rotation_template_id:
                    by_template[str(assignment.rotation_template_id)] += 1

        result = {
            "total": total,
            "by_week": dict(by_week),
            "by_template": dict(by_template),
        }

        self._put(cache_key, result)
        return result

    def invalidate(self, keys: list[str] | None = None):
        """
        Invalidate cache entries.

        Args:
            keys: Specific keys to invalidate (None = clear all)
        """
        if keys is None:
            # Clear all scheduler cache entries
            pattern = f"{self.KEY_PREFIX}*"
            cursor = 0
            deleted_count = 0
            while True:
                cursor, matched_keys = self._redis.scan(cursor, match=pattern, count=100)
                if matched_keys:
                    self._redis.delete(*matched_keys)
                    deleted_count += len(matched_keys)
                if cursor == 0:
                    break
            logger.info(f"Cache cleared completely ({deleted_count} entries)")
        else:
            # Remove specific keys
            prefixed_keys = [f"{self.KEY_PREFIX}{key}" for key in keys]
            deleted = self._redis.delete(*prefixed_keys)
            logger.info(f"Invalidated {deleted} cache entries")

    def warm_cache(
        self,
        context,
        availability: dict,
    ):
        """
        Pre-populate cache with common queries.

        Args:
            context: SchedulingContext object
            availability: Availability matrix
        """
        logger.info("Warming cache...")

        # Cache full availability matrix
        self.get_availability_matrix(
            [r.id for r in context.residents],
            [b.id for b in context.blocks],
            availability,
        )

        # Cache resident availability individually
        for resident in context.residents[:50]:  # Limit to first 50
            person_blocks = [b.id for b in context.blocks]
            self.get_availability_matrix(
                [resident.id],
                person_blocks,
                availability,
            )

        # Get approximate cache size from Redis
        pattern = f"{self.KEY_PREFIX}*"
        cursor, keys = self._redis.scan(0, match=pattern, count=1000)
        cache_size = len(keys)
        logger.info(f"Cache warmed with ~{cache_size} entries")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            # Get approximate cache size from Redis
            pattern = f"{self.KEY_PREFIX}*"
            cursor, keys = self._redis.scan(0, match=pattern, count=1000)
            cache_size = len(keys)

            return {
                "size": cache_size,
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "ttl_seconds": self.ttl_seconds,
            }

    def _get(self, key: str) -> Any | None:
        """Get value from cache."""
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

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            with self._lock:
                self._misses += 1
            return None

    def _put(self, key: str, value: Any):
        """Put value in cache with TTL."""
        prefixed_key = f"{self.KEY_PREFIX}{key}"

        try:
            # Serialize with pickle
            data = pickle.dumps(value)

            # Store with TTL
            self._redis.setex(prefixed_key, self.ttl_seconds, data)

        except Exception as e:
            logger.error(f"Cache put error for key {key}: {e}")

    @staticmethod
    def _create_key(*parts) -> str:
        """Create cache key from parts."""
        return ":".join(str(p) for p in parts)


# Global cache instance for module-level caching
_global_cache: ScheduleCache | None = None


def get_global_cache() -> ScheduleCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ScheduleCache()
    return _global_cache


@lru_cache(maxsize=256)
def cached_availability_lookup(
    person_id: str,
    block_id: str,
    availability_hash: int,
) -> bool:
    """
    LRU-cached availability lookup.

    Args:
        person_id: Person UUID as string
        block_id: Block UUID as string
        availability_hash: Hash of availability dict for cache invalidation

    Returns:
        True if person is available for block
    """
    # This is a placeholder - actual implementation would need
    # the availability dict passed in a way that works with lru_cache
    return True
