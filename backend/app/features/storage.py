"""Storage backends for feature flags.

Supports multiple storage backends:
- Database (PostgreSQL) - Production-ready, persistent storage
- Redis - Fast, distributed cache with TTL support
- In-memory - Testing and development only
"""

import json
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.feature_flag import FeatureFlag

settings = get_settings()


class FeatureFlagStorageBackend(ABC):
    """Abstract base class for feature flag storage backends."""

    @abstractmethod
    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """
        Get feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            Flag data as dict, or None if not found
        """
        pass

    @abstractmethod
    async def set_flag(self, key: str, data: dict[str, Any]) -> None:
        """
        Set feature flag data.

        Args:
            key: Feature flag key
            data: Flag data to store
        """
        pass

    @abstractmethod
    async def delete_flag(self, key: str) -> bool:
        """
        Delete feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_flags(self) -> list[dict[str, Any]]:
        """
        List all feature flags.

        Returns:
            List of all flags as dicts
        """
        pass

    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all feature flags (for testing)."""
        pass


class DatabaseStorageBackend(FeatureFlagStorageBackend):
    """
    Database storage backend using PostgreSQL.

    Production-ready backend with full ACID guarantees.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize database storage backend.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """Get feature flag from database."""
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        flag = result.scalar_one_or_none()

        if flag is None:
            return None

        return {
            "id": str(flag.id),
            "key": flag.key,
            "name": flag.name,
            "description": flag.description,
            "flag_type": flag.flag_type,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
            "environments": flag.environments,
            "target_user_ids": flag.target_user_ids,
            "target_roles": flag.target_roles,
            "variants": flag.variants,
            "dependencies": flag.dependencies,
            "custom_attributes": flag.custom_attributes,
            "created_by": str(flag.created_by) if flag.created_by else None,
            "created_at": flag.created_at.isoformat() if flag.created_at else None,
            "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
        }

    async def set_flag(self, key: str, data: dict[str, Any]) -> None:
        """Set feature flag in database."""
        # Check if flag exists
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        flag = result.scalar_one_or_none()

        if flag:
            # Update existing flag
            for field, value in data.items():
                if hasattr(flag, field) and field not in [
                    "id",
                    "created_at",
                    "created_by",
                ]:
                    setattr(flag, field, value)
        else:
            # Create new flag
            flag = FeatureFlag(**data)
            self.db.add(flag)

        await self.db.commit()
        await self.db.refresh(flag)

    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag from database."""
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        flag = result.scalar_one_or_none()

        if flag is None:
            return False

        await self.db.delete(flag)
        await self.db.commit()
        return True

    async def list_flags(self) -> list[dict[str, Any]]:
        """List all feature flags from database."""
        result = await self.db.execute(select(FeatureFlag))
        flags = result.scalars().all()

        return [
            {
                "id": str(flag.id),
                "key": flag.key,
                "name": flag.name,
                "description": flag.description,
                "flag_type": flag.flag_type,
                "enabled": flag.enabled,
                "rollout_percentage": flag.rollout_percentage,
                "environments": flag.environments,
                "target_user_ids": flag.target_user_ids,
                "target_roles": flag.target_roles,
                "variants": flag.variants,
                "dependencies": flag.dependencies,
                "custom_attributes": flag.custom_attributes,
                "created_by": str(flag.created_by) if flag.created_by else None,
                "created_at": flag.created_at.isoformat() if flag.created_at else None,
                "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
            }
            for flag in flags
        ]

    async def clear_all(self) -> None:
        """Clear all feature flags (for testing)."""
        await self.db.execute(FeatureFlag.__table__.delete())
        await self.db.commit()


class RedisStorageBackend(FeatureFlagStorageBackend):
    """
    Redis storage backend for fast, distributed feature flag access.

    Uses Redis for caching with optional TTL and fallback to database.
    """

    def __init__(self, redis_client: Any, ttl: int = 300):
        """
        Initialize Redis storage backend.

        Args:
            redis_client: Redis client instance
            ttl: Time-to-live for cache entries in seconds (default: 5 minutes)
        """
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "feature_flag:"

    def _get_key(self, flag_key: str) -> str:
        """Get Redis key with prefix."""
        return f"{self.prefix}{flag_key}"

    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """Get feature flag from Redis."""
        redis_key = self._get_key(key)
        data = await self.redis.get(redis_key)

        if data is None:
            return None

        return json.loads(data)

    async def set_flag(self, key: str, data: dict[str, Any]) -> None:
        """Set feature flag in Redis with TTL."""
        redis_key = self._get_key(key)
        json_data = json.dumps(data)

        if self.ttl > 0:
            await self.redis.setex(redis_key, self.ttl, json_data)
        else:
            await self.redis.set(redis_key, json_data)

    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag from Redis."""
        redis_key = self._get_key(key)
        result = await self.redis.delete(redis_key)
        return result > 0

    async def list_flags(self) -> list[dict[str, Any]]:
        """List all feature flags from Redis."""
        pattern = f"{self.prefix}*"
        keys = await self.redis.keys(pattern)

        flags = []
        for redis_key in keys:
            data = await self.redis.get(redis_key)
            if data:
                flags.append(json.loads(data))

        return flags

    async def clear_all(self) -> None:
        """Clear all feature flags from Redis."""
        pattern = f"{self.prefix}*"
        keys = await self.redis.keys(pattern)

        if keys:
            await self.redis.delete(*keys)


class InMemoryStorageBackend(FeatureFlagStorageBackend):
    """
    In-memory storage backend for testing and development.

    WARNING: Not suitable for production. Data is lost on restart.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._flags: dict[str, dict[str, Any]] = {}

    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """Get feature flag from memory."""
        return self._flags.get(key)

    async def set_flag(self, key: str, data: dict[str, Any]) -> None:
        """Set feature flag in memory."""
        self._flags[key] = data

    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag from memory."""
        if key in self._flags:
            del self._flags[key]
            return True
        return False

    async def list_flags(self) -> list[dict[str, Any]]:
        """List all feature flags from memory."""
        return list(self._flags.values())

    async def clear_all(self) -> None:
        """Clear all feature flags from memory."""
        self._flags.clear()


class CachedDatabaseStorageBackend(FeatureFlagStorageBackend):
    """
    Two-tier storage backend with Redis cache and database fallback.

    Reads: Check Redis first, fall back to database if miss
    Writes: Write to both Redis and database
    Deletes: Delete from both Redis and database

    This provides the best of both worlds:
    - Fast reads from Redis
    - Persistent storage in database
    - Automatic cache warming on miss
    """

    def __init__(self, db: AsyncSession, redis_client: Any, ttl: int = 300):
        """
        Initialize cached database storage backend.

        Args:
            db: Async database session
            redis_client: Redis client instance
            ttl: Redis cache TTL in seconds (default: 5 minutes)
        """
        self.db_backend = DatabaseStorageBackend(db)
        self.redis_backend = RedisStorageBackend(redis_client, ttl)

    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """Get feature flag from Redis cache, fall back to database."""
        # Try cache first
        data = await self.redis_backend.get_flag(key)
        if data is not None:
            return data

        # Cache miss, try database
        data = await self.db_backend.get_flag(key)
        if data is not None:
            # Warm the cache
            await self.redis_backend.set_flag(key, data)

        return data

    async def set_flag(self, key: str, data: dict[str, Any]) -> None:
        """Set feature flag in both database and cache."""
        # Write to database (source of truth)
        await self.db_backend.set_flag(key, data)

        # Update cache
        await self.redis_backend.set_flag(key, data)

    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag from both database and cache."""
        # Delete from database
        db_deleted = await self.db_backend.delete_flag(key)

        # Delete from cache (even if not in database)
        await self.redis_backend.delete_flag(key)

        return db_deleted

    async def list_flags(self) -> list[dict[str, Any]]:
        """List all feature flags from database."""
        # Always use database as source of truth for listing
        return await self.db_backend.list_flags()

    async def clear_all(self) -> None:
        """Clear all feature flags from both database and cache."""
        await self.db_backend.clear_all()
        await self.redis_backend.clear_all()
