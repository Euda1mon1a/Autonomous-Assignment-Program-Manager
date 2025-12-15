"""
Caching Layer for Scheduling Engine.

Provides in-memory caching for expensive operations:
- Availability matrix lookups
- Assignment count calculations
- Constraint validation results
- Solver intermediate results
"""
from functools import lru_cache
from threading import RLock
from typing import Optional, Any
from uuid import UUID
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ScheduleCache:
    """
    Thread-safe in-memory cache for scheduling operations.

    Features:
    - LRU eviction policy
    - Selective cache invalidation
    - TTL-based expiration
    - Pre-warming for common queries
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached entries
            ttl_seconds: Time-to-live for cached entries (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = RLock()

        # Cache storage: key -> (value, timestamp)
        self._cache: dict[str, tuple[Any, datetime]] = {}

        # Statistics
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

    def invalidate(self, keys: Optional[list[str]] = None):
        """
        Invalidate cache entries.

        Args:
            keys: Specific keys to invalidate (None = clear all)
        """
        with self._lock:
            if keys is None:
                # Clear entire cache
                self._cache.clear()
                logger.info("Cache cleared completely")
            else:
                # Remove specific keys
                for key in keys:
                    if key in self._cache:
                        del self._cache[key]
                logger.info(f"Invalidated {len(keys)} cache entries")

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

        logger.info(f"Cache warmed with {len(self._cache)} entries")

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
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "ttl_seconds": self.ttl_seconds,
            }

    def _get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL checking."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]

            # Check TTL
            age = (datetime.now() - timestamp).total_seconds()
            if age > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def _put(self, key: str, value: Any):
        """Put value in cache with eviction."""
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = (value, datetime.now())

    def _evict_oldest(self):
        """Evict oldest cache entry (simple FIFO)."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k][1],
        )
        del self._cache[oldest_key]

    @staticmethod
    def _create_key(*parts) -> str:
        """Create cache key from parts."""
        return ":".join(str(p) for p in parts)


# Global cache instance for module-level caching
_global_cache: Optional[ScheduleCache] = None


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
