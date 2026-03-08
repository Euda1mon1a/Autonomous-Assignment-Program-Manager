"""Unified cache manager for application-wide caching.

Provides a central interface for managing caching across different layers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheConfig(BaseModel):
    """Configuration for cache settings."""

    default_ttl: int = 900  # 15 minutes
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class CacheManager:
    """Central cache manager with Redis backend."""

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize cache manager.

        Args:
            config: Cache configuration, defaults if None
        """
        self.config = config or CacheConfig()
        self._redis: redis.Redis | None = None
        self._lock = asyncio.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0,
            "deletes": 0,
        }

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._redis is None:
            async with self._lock:
                if self._redis is None:
                    self._redis = await redis.from_url(
                        settings.REDIS_URL,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=self.config.max_connections,
                        socket_timeout=self.config.socket_timeout,
                        socket_connect_timeout=self.config.socket_connect_timeout,
                        retry_on_timeout=self.config.retry_on_timeout,
                    )
                    logger.info("Redis connection established")

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection, connecting if needed.

        Returns:
            Active Redis connection

        Raises:
            RuntimeError: If connection could not be established
        """
        await self.connect()
        if self._redis is None:
            raise RuntimeError("Failed to establish Redis connection")
        return self._redis

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")

    async def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        r = await self._get_redis()

        try:
            value = await r.get(key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return default
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache get error for key {key}", exc_info=True)
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds, uses default if None

        Returns:
            True if successful
        """
        r = await self._get_redis()

        try:
            ttl_seconds = ttl or self.config.default_ttl
            await r.setex(key, ttl_seconds, value)
            self.stats["sets"] += 1
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache set error for key {key}", exc_info=True)
            return False

    async def delete(self, *keys: str) -> int:
        """Delete keys from cache.

        Args:
            *keys: Cache keys to delete

        Returns:
            Number of keys deleted
        """
        r = await self._get_redis()

        try:
            count = await r.delete(*keys)
            self.stats["deletes"] += count
            logger.debug(f"Cache delete: {count} keys")
            return count
        except Exception as e:
            self.stats["errors"] += 1
            logger.error("Cache delete error", exc_info=True)
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        r = await self._get_redis()

        try:
            return await r.exists(key) > 0
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache exists error for key {key}", exc_info=True)
            return False

    async def get_or_set(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """Get from cache or fetch and cache if not found.

        Args:
            key: Cache key
            fetch_fn: Async function to fetch value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or fetched value
        """
        # Try cache first
        r = await self._get_redis()
        try:
            cached = await r.get(key)
            if cached is not None:
                self.stats["hits"] += 1
                return cached
            self.stats["misses"] += 1
        except Exception:
            self.stats["errors"] += 1

        # Fetch fresh data
        value = await fetch_fn()

        # Cache it
        await self.set(key, value, ttl)

        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "schedule:*")

        Returns:
            Number of keys invalidated
        """
        r = await self._get_redis()

        try:
            cursor = 0
            count = 0

            while True:
                cursor, keys = await r.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted = await r.delete(*keys)
                    count += deleted

                if cursor == 0:
                    break

            self.stats["deletes"] += count
            logger.info(f"Invalidated {count} keys matching {pattern}")
            return count
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache invalidate error for pattern {pattern}", exc_info=True)
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter value.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value
        """
        r = await self._get_redis()

        try:
            new_value = await r.incrby(key, amount)
            logger.debug(f"Cache increment: {key} by {amount} = {new_value}")
            return new_value
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache increment error for key {key}", exc_info=True)
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter value.

        Args:
            key: Cache key
            amount: Amount to decrement

        Returns:
            New value
        """
        r = await self._get_redis()

        try:
            new_value = await r.decrby(key, amount)
            logger.debug(f"Cache decrement: {key} by {amount} = {new_value}")
            return new_value
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache decrement error for key {key}", exc_info=True)
            return 0

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if no expiry, -2 if not exists
        """
        r = await self._get_redis()

        try:
            return await r.ttl(key)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache TTL error for key {key}", exc_info=True)
            return -2

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        r = await self._get_redis()

        try:
            result = await r.expire(key, ttl)
            logger.debug(f"Cache expire: {key} for {ttl}s")
            return result
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache expire error for key {key}", exc_info=True)
            return False

    async def flush_all(self) -> bool:
        """Flush all cache entries (USE WITH CAUTION).

        Returns:
            True if successful
        """
        r = await self._get_redis()

        try:
            await r.flushdb()
            logger.warning("Cache flushed - all entries deleted")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error("Cache flush error", exc_info=True)
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total * 100 if total > 0 else 0

        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "total_operations": total,
        }

    async def health_check(self) -> dict[str, Any]:
        """Check cache health.

        Returns:
            Health status dictionary
        """
        r = await self._get_redis()

        try:
            # Ping Redis
            await r.ping()

            # Get info
            info = await r.info()

            return {
                "healthy": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.error("Cache health check failed", exc_info=True)
            return {
                "healthy": False,
                "error": "Operation failed",
            }

            # Global cache instance


_cache_instance: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance.

    Returns:
        CacheManager singleton
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance
