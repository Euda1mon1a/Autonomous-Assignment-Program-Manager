"""Query result caching with Redis.

Provides efficient caching for database query results with automatic invalidation
and performance metrics.
"""

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryCache:
    """Redis-based query result cache with automatic invalidation."""

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize query cache.

        Args:
            redis_client: Optional Redis client. If None, creates new connection.
        """
        self.redis = redis_client or redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        self.default_ttl = timedelta(minutes=15)
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
        }

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl: timedelta | None = None,
        serializer: Callable[[Any], str] = json.dumps,
        deserializer: Callable[[str], Any] = json.loads,
    ) -> Any:
        """Get cached result or fetch and cache.

        Args:
            key: Cache key
            fetch_fn: Async function to fetch data if not cached
            ttl: Time to live for cached value
            serializer: Function to serialize result
            deserializer: Function to deserialize cached value

        Returns:
            Cached or freshly fetched result
        """
        # Try to get from cache
        cached = await self.redis.get(key)
        if cached is not None:
            self.metrics["hits"] += 1
            logger.debug(f"Cache hit for key: {key}")
            return deserializer(cached)

            # Cache miss - fetch fresh data
        self.metrics["misses"] += 1
        logger.debug(f"Cache miss for key: {key}")

        result = await fetch_fn()

        # Cache the result
        ttl_seconds = int((ttl or self.default_ttl).total_seconds())
        await self.redis.setex(key, ttl_seconds, serializer(result))

        return result

    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "schedule:*")

        Returns:
            Number of keys invalidated
        """
        cursor = 0
        count = 0

        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                count += await self.redis.delete(*keys)
            if cursor == 0:
                break

        self.metrics["invalidations"] += count
        logger.info(f"Invalidated {count} cache entries matching {pattern}")
        return count

    async def invalidate_table(self, table_name: str) -> int:
        """Invalidate all cache entries for a table.

        Args:
            table_name: Database table name

        Returns:
            Number of keys invalidated
        """
        return await self.invalidate(f"query:{table_name}:*")

    def generate_key(self, query_str: str, params: dict) -> str:
        """Generate cache key from query and parameters.

        Args:
            query_str: SQL query string
            params: Query parameters

        Returns:
            Cache key hash
        """
        # Create deterministic key from query + params
        content = f"{query_str}:{json.dumps(params, sort_keys=True)}"
        key_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"query:{key_hash}"

    async def get_metrics(self) -> dict:
        """Get cache performance metrics.

        Returns:
            Dictionary with hit rate and other metrics
        """
        total = self.metrics["hits"] + self.metrics["misses"]
        hit_rate = self.metrics["hits"] / total * 100 if total > 0 else 0

        return {
            "hits": self.metrics["hits"],
            "misses": self.metrics["misses"],
            "invalidations": self.metrics["invalidations"],
            "hit_rate": round(hit_rate, 2),
            "total_queries": total,
        }

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()


class CachedQuery:
    """Decorator for caching database queries."""

    def __init__(
        self,
        cache: QueryCache,
        ttl: timedelta | None = None,
        key_prefix: str | None = None,
    ) -> None:
        """Initialize cached query decorator.

        Args:
            cache: QueryCache instance
            ttl: Time to live for cached results
            key_prefix: Optional prefix for cache keys
        """
        self.cache = cache
        self.ttl = ttl
        self.key_prefix = key_prefix or "cached_query"

    def __call__(self, func: Callable) -> Callable:
        """Wrap function with caching logic.

        Args:
            func: Async function to cache

        Returns:
            Wrapped function with caching
        """

        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [self.key_prefix, func.__name__]
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(json.dumps(kwargs, sort_keys=True))

            key = ":".join(key_parts)
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
            cache_key = f"{self.key_prefix}:{key_hash}"

            return await self.cache.get_or_fetch(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl=self.ttl,
            )

        return wrapper

        # Global cache instance


_cache_instance: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """Get global query cache instance.

    Returns:
        QueryCache singleton
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache()
    return _cache_instance
