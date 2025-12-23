"""
Comprehensive tests for the Redis caching layer.

Tests the ServiceCache module and its integration with schedule services.
Covers:
- Basic cache operations (get, set, delete)
- TTL-based expiration
- Cache key generation
- Pattern-based invalidation
- Graceful degradation when Redis unavailable
- Decorator-based caching
- Cache statistics
"""

import time
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
import redis

from app.core.cache import (
    CachePrefix,
    CacheTTL,
    ServiceCache,
    get_service_cache,
    invalidate_person_cache,
    invalidate_schedule_cache,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    mock = MagicMock(spec=redis.Redis)
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.scan.return_value = (0, [])
    return mock


@pytest.fixture
def service_cache(mock_redis):
    """Create a ServiceCache instance with mock Redis."""
    with patch("app.core.cache.redis.from_url", return_value=mock_redis):
        cache = ServiceCache(enabled=True)
        cache._redis = mock_redis
        cache._available = True
        return cache


@pytest.fixture
def real_redis_cache():
    """
    Create a ServiceCache with real Redis connection.

    Note: Requires Redis to be running. Tests will be skipped if Redis is unavailable.
    """
    try:
        cache = ServiceCache()
        if cache.is_available:
            # Clean up any existing test keys
            cache.invalidate_all()
            return cache
        pytest.skip("Redis not available")
    except Exception:
        pytest.skip("Redis not available")


# ============================================================================
# Unit Tests - ServiceCache Class
# ============================================================================


class TestServiceCache:
    """Test the ServiceCache class directly."""

    def test_cache_initialization_with_mock(self, service_cache):
        """Test cache initializes correctly with mocked Redis."""
        assert service_cache.is_available is True
        assert service_cache.enabled is True

    def test_cache_initialization_redis_unavailable(self):
        """Test cache handles Redis unavailability gracefully."""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping.side_effect = redis.RedisError(
                "Connection refused"
            )
            cache = ServiceCache()
            assert cache.is_available is False

    def test_get_returns_none_when_unavailable(self, service_cache):
        """Test get returns None when cache is unavailable."""
        service_cache._available = False
        result = service_cache.get("test_key")
        assert result is None

    def test_set_returns_false_when_unavailable(self, service_cache):
        """Test set returns False when cache is unavailable."""
        service_cache._available = False
        result = service_cache.set("test_key", {"data": "value"})
        assert result is False

    def test_set_with_custom_ttl(self, service_cache, mock_redis):
        """Test set uses custom TTL when provided."""

        service_cache.set("test_key", {"data": "value"}, ttl=300)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # TTL is second positional arg

    def test_set_with_default_ttl(self, service_cache, mock_redis):
        """Test set uses default TTL when not provided."""
        service_cache.set("test_key", {"data": "value"})
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == service_cache.default_ttl

    def test_delete_key(self, service_cache, mock_redis):
        """Test deleting a specific cache key."""
        result = service_cache.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once()

    def test_delete_returns_false_when_unavailable(self, service_cache):
        """Test delete returns False when cache is unavailable."""
        service_cache._available = False
        result = service_cache.delete("test_key")
        assert result is False


class TestCacheKeyGeneration:
    """Test cache key generation logic."""

    def test_serialize_uuid(self, service_cache):
        """Test UUID serialization for cache keys."""
        test_uuid = uuid4()
        result = service_cache._serialize_arg(test_uuid)
        assert result == str(test_uuid)

    def test_serialize_date(self, service_cache):
        """Test date serialization for cache keys."""
        test_date = date(2024, 1, 15)
        result = service_cache._serialize_arg(test_date)
        assert result == "2024-01-15"

    def test_serialize_list(self, service_cache):
        """Test list serialization for cache keys."""
        test_list = ["c", "a", "b"]
        result = service_cache._serialize_arg(test_list)
        assert result == "[a,b,c]"  # Sorted

    def test_serialize_list_of_uuids(self, service_cache):
        """Test list of UUIDs serialization."""
        uuid1 = UUID("00000000-0000-0000-0000-000000000001")
        uuid2 = UUID("00000000-0000-0000-0000-000000000002")
        result = service_cache._serialize_arg([uuid2, uuid1])
        # Should be sorted
        assert "00000000-0000-0000-0000-000000000001" in result
        assert "00000000-0000-0000-0000-000000000002" in result

    def test_serialize_bool(self, service_cache):
        """Test boolean serialization."""
        assert service_cache._serialize_arg(True) == "true"
        assert service_cache._serialize_arg(False) == "false"

    def test_serialize_none(self, service_cache):
        """Test None serialization."""
        assert service_cache._serialize_arg(None) == "None"


class TestCacheInvalidation:
    """Test cache invalidation methods."""

    def test_invalidate_pattern(self, service_cache, mock_redis):
        """Test pattern-based cache invalidation."""
        mock_redis.scan.return_value = (
            0,
            [b"svc_cache:heatmap:test1", b"svc_cache:heatmap:test2"],
        )
        mock_redis.delete.return_value = 2

        count = service_cache.invalidate_pattern("heatmap:*")
        assert count == 2

    def test_invalidate_by_prefix(self, service_cache, mock_redis):
        """Test prefix-based cache invalidation."""
        mock_redis.scan.return_value = (
            0,
            [b"svc_cache:heatmap:1", b"svc_cache:heatmap:2"],
        )
        mock_redis.delete.return_value = 2

        count = service_cache.invalidate_by_prefix(CachePrefix.HEATMAP)
        assert count == 2

    def test_invalidate_all(self, service_cache, mock_redis):
        """Test clearing all cache entries."""
        mock_redis.scan.return_value = (
            0,
            [b"svc_cache:key1", b"svc_cache:key2", b"svc_cache:key3"],
        )
        mock_redis.delete.return_value = 3

        count = service_cache.invalidate_all()
        assert count == 3


class TestCacheDecorator:
    """Test the @cache.cached decorator."""

    def test_decorator_caches_result(self, service_cache, mock_redis):
        """Test that decorator caches function results."""

        # Setup mock to return None (cache miss), then return cached value
        mock_redis.get.return_value = None

        @service_cache.cached(prefix=CachePrefix.GENERAL, ttl=300)
        def expensive_function(x: int) -> int:
            return x * 2

        result = expensive_function(5)
        assert result == 10
        mock_redis.setex.assert_called_once()

    def test_decorator_returns_cached_value(self, service_cache, mock_redis):
        """Test that decorator returns cached value on hit."""
        import pickle

        cached_value = {"result": 42}
        mock_redis.get.return_value = pickle.dumps(cached_value)

        @service_cache.cached(prefix=CachePrefix.GENERAL)
        def expensive_function() -> dict:
            return {"result": 0}  # Should not be called

        result = expensive_function()
        assert result == cached_value

    def test_decorator_skips_db_session_in_key(self, service_cache, mock_redis):
        """Test that decorator properly skips db session argument."""
        mock_redis.get.return_value = None

        class MockSession:
            def execute(self):
                pass

        @service_cache.cached(prefix=CachePrefix.GENERAL)
        def query_function(db, start_date: date) -> dict:
            return {"data": "value"}

        db = MockSession()
        result = query_function(db, date(2024, 1, 1))
        assert result == {"data": "value"}

        # The db session should not be in the cache key
        call_args = mock_redis.setex.call_args
        cache_key = call_args[0][0]
        assert "MockSession" not in cache_key


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_stats_initialized_to_zero(self, service_cache):
        """Test statistics start at zero."""
        stats = service_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0

    def test_stats_incremented_on_hit(self, service_cache, mock_redis):
        """Test hit counter incremented on cache hit."""
        import pickle

        mock_redis.get.return_value = pickle.dumps({"data": "cached"})

        service_cache.get("test_key")
        stats = service_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_stats_incremented_on_miss(self, service_cache, mock_redis):
        """Test miss counter incremented on cache miss."""
        mock_redis.get.return_value = None

        service_cache.get("test_key")
        stats = service_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    def test_hit_rate_calculation(self, service_cache, mock_redis):
        """Test hit rate is calculated correctly."""
        import pickle

        # 2 hits
        mock_redis.get.return_value = pickle.dumps({"data": "cached"})
        service_cache.get("key1")
        service_cache.get("key2")

        # 2 misses
        mock_redis.get.return_value = None
        service_cache.get("key3")
        service_cache.get("key4")

        stats = service_cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5

    def test_reset_stats(self, service_cache, mock_redis):
        """Test statistics can be reset."""
        import pickle

        mock_redis.get.return_value = pickle.dumps({"data": "cached"})
        service_cache.get("key1")

        service_cache.reset_stats()
        stats = service_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Test module-level helper functions."""

    def test_get_service_cache_singleton(self):
        """Test get_service_cache returns singleton instance."""
        with patch("app.core.cache.ServiceCache") as MockCache:
            MockCache.return_value._available = False
            # Reset the global cache
            import app.core.cache

            app.core.cache._service_cache = None

            cache1 = get_service_cache()
            cache2 = get_service_cache()
            assert cache1 is cache2

    def test_invalidate_schedule_cache(self, mock_redis):
        """Test schedule cache invalidation helper."""
        with patch("app.core.cache.get_service_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate_by_prefix.return_value = 5
            mock_get_cache.return_value = mock_cache

            count = invalidate_schedule_cache()
            assert count > 0
            assert mock_cache.invalidate_by_prefix.call_count >= 1

    def test_invalidate_person_cache_all(self, mock_redis):
        """Test person cache invalidation for all persons."""
        with patch("app.core.cache.get_service_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate_by_prefix.return_value = 3
            mock_get_cache.return_value = mock_cache

            count = invalidate_person_cache()
            assert count == 3
            mock_cache.invalidate_by_prefix.assert_called_once_with(CachePrefix.PERSONS)

    def test_invalidate_person_cache_specific(self, mock_redis):
        """Test person cache invalidation for specific person."""
        person_id = uuid4()
        with patch("app.core.cache.get_service_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate_pattern.return_value = 2
            mock_get_cache.return_value = mock_cache

            count = invalidate_person_cache(person_id)
            assert count == 2
            mock_cache.invalidate_pattern.assert_called_once()


# ============================================================================
# Integration Tests with Real Redis
# ============================================================================


class TestCacheIntegration:
    """Integration tests with real Redis (skipped if unavailable)."""

    def test_real_redis_set_and_get(self, real_redis_cache):
        """Test actual set and get operations with Redis."""
        test_data = {"key": "value", "nested": {"inner": 123}}

        # Set value
        success = real_redis_cache.set("integration_test", test_data, ttl=60)
        assert success is True

        # Get value back
        result = real_redis_cache.get("integration_test")
        assert result == test_data

    def test_real_redis_cache_miss(self, real_redis_cache):
        """Test cache miss returns None."""
        result = real_redis_cache.get("nonexistent_key")
        assert result is None

    def test_real_redis_delete(self, real_redis_cache):
        """Test deleting a cached value."""
        real_redis_cache.set("to_delete", {"data": 1}, ttl=60)
        assert real_redis_cache.get("to_delete") is not None

        deleted = real_redis_cache.delete("to_delete")
        assert deleted is True
        assert real_redis_cache.get("to_delete") is None

    def test_real_redis_pattern_invalidation(self, real_redis_cache):
        """Test pattern-based invalidation."""
        # Set multiple values with common prefix
        real_redis_cache.set("test_pattern:1", {"data": 1}, ttl=60)
        real_redis_cache.set("test_pattern:2", {"data": 2}, ttl=60)
        real_redis_cache.set("other:3", {"data": 3}, ttl=60)

        # Invalidate only test_pattern keys
        count = real_redis_cache.invalidate_pattern("test_pattern:*")
        assert count == 2

        # Verify test_pattern keys are gone
        assert real_redis_cache.get("test_pattern:1") is None
        assert real_redis_cache.get("test_pattern:2") is None

        # Verify other key still exists
        assert real_redis_cache.get("other:3") is not None

    def test_real_redis_ttl_expiration(self, real_redis_cache):
        """Test TTL-based cache expiration."""
        # Set with 1 second TTL
        real_redis_cache.set("short_lived", {"data": 1}, ttl=1)
        assert real_redis_cache.get("short_lived") is not None

        # Wait for expiration
        time.sleep(1.5)
        assert real_redis_cache.get("short_lived") is None


# ============================================================================
# Cache TTL Constants Tests
# ============================================================================


class TestCacheTTL:
    """Test cache TTL constant values."""

    def test_ttl_values_are_sensible(self):
        """Test that TTL values are reasonable."""
        assert CacheTTL.SHORT < CacheTTL.MEDIUM
        assert CacheTTL.MEDIUM < CacheTTL.LONG
        assert CacheTTL.LONG < CacheTTL.EXTENDED
        assert CacheTTL.EXTENDED < CacheTTL.DAY
        assert CacheTTL.DAY < CacheTTL.WEEK

    def test_ttl_values(self):
        """Test specific TTL values."""
        assert CacheTTL.SHORT == 300  # 5 minutes
        assert CacheTTL.MEDIUM == 1800  # 30 minutes
        assert CacheTTL.LONG == 3600  # 1 hour
        assert CacheTTL.DAY == 86400  # 24 hours


# ============================================================================
# Cache Prefix Tests
# ============================================================================


class TestCachePrefix:
    """Test cache prefix enumeration."""

    def test_all_prefixes_are_strings(self):
        """Test all prefixes are string values."""
        for prefix in CachePrefix:
            assert isinstance(prefix.value, str)

    def test_prefixes_are_unique(self):
        """Test all prefix values are unique."""
        values = [prefix.value for prefix in CachePrefix]
        assert len(values) == len(set(values))
