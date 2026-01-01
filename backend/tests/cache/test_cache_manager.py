"""Tests for CacheManager."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import timedelta

from app.cache.cache_manager import CacheManager, CacheConfig


class TestCacheConfig:
    """Test suite for CacheConfig."""

    def test_default_config(self):
        """Test default cache configuration values."""
        config = CacheConfig()

        assert config.default_ttl == 900  # 15 minutes
        assert config.max_connections == 50
        assert config.socket_timeout == 5
        assert config.socket_connect_timeout == 5
        assert config.retry_on_timeout is True
        assert config.health_check_interval == 30

    def test_custom_config(self):
        """Test creating cache config with custom values."""
        config = CacheConfig(
            default_ttl=300,
            max_connections=100,
            socket_timeout=10,
        )

        assert config.default_ttl == 300
        assert config.max_connections == 100
        assert config.socket_timeout == 10


class TestCacheManager:
    """Test suite for CacheManager."""

    # ========================================================================
    # Connection Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_connect_success(self, mock_from_url):
        """Test successful Redis connection."""
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        assert manager._redis is not None
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_connect_multiple_calls(self, mock_from_url):
        """Test that multiple connect calls don't create multiple connections."""
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()
        await manager.connect()
        await manager.connect()

        # Should only call from_url once
        assert mock_from_url.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Redis."""
        manager = CacheManager()
        manager._redis = AsyncMock()

        await manager.disconnect()

        manager._redis.close.assert_called_once()
        assert manager._redis is None

    # ========================================================================
    # Get Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_get_hit(self, mock_from_url):
        """Test cache hit on get."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "cached_value"
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        value = await manager.get("test_key")

        assert value == "cached_value"
        assert manager.stats["hits"] == 1
        assert manager.stats["misses"] == 0
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_get_miss(self, mock_from_url):
        """Test cache miss on get."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        value = await manager.get("test_key")

        assert value is None
        assert manager.stats["hits"] == 0
        assert manager.stats["misses"] == 1

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_get_with_default(self, mock_from_url):
        """Test get with default value on cache miss."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        value = await manager.get("test_key", default="default_value")

        assert value == "default_value"
        assert manager.stats["misses"] == 1

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_get_error_handling(self, mock_from_url):
        """Test error handling in get operation."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        value = await manager.get("test_key", default="fallback")

        assert value == "fallback"
        assert manager.stats["errors"] == 1

    # ========================================================================
    # Set Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_set_success(self, mock_from_url):
        """Test successful cache set."""
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        result = await manager.set("test_key", "test_value")

        assert result is True
        assert manager.stats["sets"] == 1
        mock_redis.setex.assert_called_once_with("test_key", 900, "test_value")

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_set_with_custom_ttl(self, mock_from_url):
        """Test set with custom TTL."""
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        result = await manager.set("test_key", "test_value", ttl=300)

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 300, "test_value")

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_set_error_handling(self, mock_from_url):
        """Test error handling in set operation."""
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        result = await manager.set("test_key", "test_value")

        assert result is False
        assert manager.stats["errors"] == 1

    # ========================================================================
    # Delete Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_delete_single_key(self, mock_from_url):
        """Test deleting a single key."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        count = await manager.delete("test_key")

        assert count == 1
        assert manager.stats["deletes"] == 1
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_delete_multiple_keys(self, mock_from_url):
        """Test deleting multiple keys at once."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 3
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        count = await manager.delete("key1", "key2", "key3")

        assert count == 3
        assert manager.stats["deletes"] == 3
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_delete_error_handling(self, mock_from_url):
        """Test error handling in delete operation."""
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis error")
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        count = await manager.delete("test_key")

        # Should return 0 on error
        assert count == 0 or count is None  # Depending on implementation
        assert manager.stats["errors"] >= 1

    # ========================================================================
    # Stats Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.cache_manager.redis.from_url")
    async def test_stats_tracking(self, mock_from_url):
        """Test that stats are correctly tracked."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ["value1", None, "value2"]
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 2
        mock_from_url.return_value = mock_redis

        manager = CacheManager()
        await manager.connect()

        # Perform operations
        await manager.get("key1")  # Hit
        await manager.get("key2")  # Miss
        await manager.get("key3")  # Hit
        await manager.set("key4", "value")  # Set
        await manager.delete("key5", "key6")  # Delete

        assert manager.stats["hits"] == 2
        assert manager.stats["misses"] == 1
        assert manager.stats["sets"] == 1
        assert manager.stats["deletes"] == 2

    def test_initial_stats(self):
        """Test that stats are initialized correctly."""
        manager = CacheManager()

        assert manager.stats["hits"] == 0
        assert manager.stats["misses"] == 0
        assert manager.stats["errors"] == 0
        assert manager.stats["sets"] == 0
        assert manager.stats["deletes"] == 0
