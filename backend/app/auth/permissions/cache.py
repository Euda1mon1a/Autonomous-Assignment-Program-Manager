"""Redis-based permission caching for improved authorization performance."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.auth.permissions.models import UserRole
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PermissionCache:
    """
    Redis-based cache for role permissions.

    Features:
    - TTL-based invalidation
    - Automatic cache warming on startup
    - Graceful degradation if Redis unavailable
    - Separate namespaces for different cache types
    """

    # Cache key prefixes
    ROLE_PERMISSIONS_PREFIX = "perm:role"
    USER_PERMISSIONS_PREFIX = "perm:user"
    RESOURCE_PERMISSIONS_PREFIX = "perm:resource"

    # Cache TTL (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    ROLE_TTL = 86400  # 24 hours (roles change infrequently)
    USER_TTL = 3600  # 1 hour (user roles can change)

    def __init__(self, redis_client: aioredis.Redis | None = None) -> None:
        """
        Initialize permission cache.

        Args:
            redis_client: Optional Redis client. If None, creates new connection.
        """
        self._redis = redis_client
        self._fallback_mode = False

    async def get_redis_client(self) -> aioredis.Redis | None:
        """
        Get Redis client, creating connection if needed.

        Returns:
            Redis client or None if connection fails
        """
        if self._redis is not None:
            return self._redis

        try:
            self._redis = aioredis.from_url(
                settings.redis_url_with_password,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self._redis.ping()
            self._fallback_mode = False
            logger.info("Permission cache connected to Redis")
            return self._redis
        except (RedisError, OSError) as e:
            logger.warning(f"Failed to connect to Redis for permission cache: {e}")
            self._fallback_mode = True
            self._redis = None
            return None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    def _make_role_key(self, role: UserRole | str) -> str:
        """
        Create cache key for role permissions.

        Args:
            role: User role

        Returns:
            Cache key string
        """
        role_str = role.value if isinstance(role, UserRole) else role
        return f"{self.ROLE_PERMISSIONS_PREFIX}:{role_str}"

    def _make_user_key(self, user_id: str) -> str:
        """
        Create cache key for user permissions.

        Args:
            user_id: User ID

        Returns:
            Cache key string
        """
        return f"{self.USER_PERMISSIONS_PREFIX}:{user_id}"

    def _make_resource_key(self, resource_type: str, resource_id: str) -> str:
        """
        Create cache key for resource permissions.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID

        Returns:
            Cache key string
        """
        return f"{self.RESOURCE_PERMISSIONS_PREFIX}:{resource_type}:{resource_id}"

    async def get_role_permissions(self, role: UserRole | str) -> set[str] | None:
        """
        Get cached permissions for a role.

        Args:
            role: User role

        Returns:
            Set of permission strings or None if not cached
        """
        redis = await self.get_redis_client()
        if redis is None:
            return None

        try:
            key = self._make_role_key(role)
            data = await redis.get(key)
            if data is None:
                return None

            permissions = json.loads(data)
            return set(permissions)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to get role permissions from cache: {e}")
            return None

    async def set_role_permissions(
        self, role: UserRole | str, permissions: set[str], ttl: int | None = None
    ) -> bool:
        """
        Cache permissions for a role.

        Args:
            role: User role
            permissions: Set of permission strings
            ttl: Time to live in seconds (None = use ROLE_TTL)

        Returns:
            True if cached successfully, False otherwise
        """
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_role_key(role)
            data = json.dumps(list(permissions))
            ttl = ttl or self.ROLE_TTL
            await redis.setex(key, ttl, data)
            logger.debug(f"Cached permissions for role {role} (TTL: {ttl}s)")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to cache role permissions: {e}")
            return False

    async def get_user_permissions(self, user_id: str) -> set[str] | None:
        """
        Get cached permissions for a user.

        Args:
            user_id: User ID

        Returns:
            Set of permission strings or None if not cached
        """
        redis = await self.get_redis_client()
        if redis is None:
            return None

        try:
            key = self._make_user_key(user_id)
            data = await redis.get(key)
            if data is None:
                return None

            permissions = json.loads(data)
            return set(permissions)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to get user permissions from cache: {e}")
            return None

    async def set_user_permissions(
        self, user_id: str, permissions: set[str], ttl: int | None = None
    ) -> bool:
        """
        Cache permissions for a user.

        Args:
            user_id: User ID
            permissions: Set of permission strings
            ttl: Time to live in seconds (None = use USER_TTL)

        Returns:
            True if cached successfully, False otherwise
        """
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_user_key(user_id)
            data = json.dumps(list(permissions))
            ttl = ttl or self.USER_TTL
            await redis.setex(key, ttl, data)
            logger.debug(f"Cached permissions for user {user_id} (TTL: {ttl}s)")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to cache user permissions: {e}")
            return False

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        """
        Invalidate cached permissions for a user.

        Args:
            user_id: User ID

        Returns:
            True if invalidated successfully, False otherwise
        """
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_user_key(user_id)
            await redis.delete(key)
            logger.debug(f"Invalidated permissions cache for user {user_id}")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate user permissions: {e}")
            return False

    async def invalidate_role_permissions(self, role: UserRole | str) -> bool:
        """
        Invalidate cached permissions for a role.

        Args:
            role: User role

        Returns:
            True if invalidated successfully, False otherwise
        """
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            key = self._make_role_key(role)
            await redis.delete(key)
            logger.debug(f"Invalidated permissions cache for role {role}")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate role permissions: {e}")
            return False

    async def invalidate_all_permissions(self) -> bool:
        """
        Invalidate all cached permissions.

        Returns:
            True if invalidated successfully, False otherwise
        """
        redis = await self.get_redis_client()
        if redis is None:
            return False

        try:
            # Delete all keys matching permission patterns
            patterns = [
                f"{self.ROLE_PERMISSIONS_PREFIX}:*",
                f"{self.USER_PERMISSIONS_PREFIX}:*",
                f"{self.RESOURCE_PERMISSIONS_PREFIX}:*",
            ]

            deleted_count = 0
            for pattern in patterns:
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        deleted_count += await redis.delete(*keys)
                    if cursor == 0:
                        break

            logger.info(f"Invalidated {deleted_count} permission cache entries")
            return True
        except RedisError as e:
            logger.warning(f"Failed to invalidate all permissions: {e}")
            return False

    async def warm_cache(self, permissions_map: dict[UserRole, set[str]]) -> int:
        """
        Pre-populate cache with role permissions (cache warming).

        This should be called on application startup to ensure
        frequently accessed permissions are already cached.

        Args:
            permissions_map: Mapping of roles to their permissions

        Returns:
            Number of roles successfully cached
        """
        if self._fallback_mode:
            logger.info("Skipping cache warming in fallback mode")
            return 0

        cached_count = 0
        for role, permissions in permissions_map.items():
            if await self.set_role_permissions(role, permissions):
                cached_count += 1

        logger.info(
            f"Cache warming completed: {cached_count}/{len(permissions_map)} roles cached"
        )
        return cached_count

    async def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        redis = await self.get_redis_client()
        if redis is None:
            return {
                "status": "unavailable",
                "fallback_mode": True,
            }

        try:
            info = await redis.info("stats")
            keyspace = await redis.info("keyspace")

            # Count permission keys
            role_count = 0
            user_count = 0
            resource_count = 0

            for pattern, counter in [
                (f"{self.ROLE_PERMISSIONS_PREFIX}:*", "role_count"),
                (f"{self.USER_PERMISSIONS_PREFIX}:*", "user_count"),
                (f"{self.RESOURCE_PERMISSIONS_PREFIX}:*", "resource_count"),
            ]:
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    count += len(keys)
                    if cursor == 0:
                        break

                if counter == "role_count":
                    role_count = count
                elif counter == "user_count":
                    user_count = count
                elif counter == "resource_count":
                    resource_count = count

            return {
                "status": "connected",
                "fallback_mode": False,
                "role_permissions_cached": role_count,
                "user_permissions_cached": user_count,
                "resource_permissions_cached": resource_count,
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except RedisError as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_mode": True,
            }

    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return round(hits / total * 100, 2) if total > 0 else 0.0

        # Global cache instance (singleton pattern)


_cache_instance: PermissionCache | None = None


async def get_permission_cache() -> PermissionCache:
    """
    Get global permission cache instance.

    Returns:
        PermissionCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PermissionCache()
        # Ensure Redis connection is established
        await _cache_instance.get_redis_client()
    return _cache_instance


async def close_permission_cache() -> None:
    """Close global permission cache instance."""
    global _cache_instance
    if _cache_instance is not None:
        await _cache_instance.close()
        _cache_instance = None
