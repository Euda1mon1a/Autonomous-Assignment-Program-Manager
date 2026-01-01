"""
Tests for scheduling solution cache.

Comprehensive test suite for ScheduleCache class,
covering Redis-backed caching, invalidation, and performance tracking.
"""

import pytest
from collections import defaultdict
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.scheduling.caching import ScheduleCache, get_global_cache


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.scan.return_value = (0, [])
    return redis_mock


@pytest.fixture
def cache(mock_redis):
    """Create ScheduleCache instance with mocked Redis."""
    with patch("app.scheduling.caching.redis.from_url", return_value=mock_redis):
        cache = ScheduleCache(max_size=1000, ttl_seconds=3600)
        cache._redis = mock_redis
        return cache


class TestScheduleCache:
    """Test suite for ScheduleCache class."""

    def test_initialization(self, cache):
        """Test cache initializes with correct settings."""
        # Assert
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._redis is not None

    def test_get_availability_matrix_cache_miss(self, cache, mock_redis):
        """Test getting availability matrix on cache miss builds and caches result."""
        # Arrange
        person_ids = [uuid4(), uuid4()]
        block_ids = [uuid4(), uuid4()]
        availability_data = {
            person_ids[0]: {block_ids[0]: {"available": True}},
            person_ids[1]: {block_ids[1]: {"available": True}},
        }

        mock_redis.get.return_value = None  # Cache miss

        # Act
        result = cache.get_availability_matrix(person_ids, block_ids, availability_data)

        # Assert
        assert result is not None
        assert person_ids[0] in result
        assert block_ids[0] in result[person_ids[0]]
        # Verify it was stored in cache
        mock_redis.setex.assert_called_once()
        # Verify it was a cache miss
        assert cache._misses == 1
        assert cache._hits == 0

    def test_get_availability_matrix_cache_hit(self, cache, mock_redis):
        """Test getting availability matrix on cache hit returns cached data."""
        # Arrange
        import pickle

        person_ids = [uuid4(), uuid4()]
        block_ids = [uuid4(), uuid4()]
        cached_data = {
            person_ids[0]: {block_ids[0]: {"available": True}},
        }

        mock_redis.get.return_value = pickle.dumps(cached_data)

        # Act
        result = cache.get_availability_matrix(person_ids, block_ids, {})

        # Assert
        assert result == cached_data
        # Verify it was not stored (already in cache)
        mock_redis.setex.assert_not_called()
        # Verify it was a cache hit
        assert cache._hits == 1
        assert cache._misses == 0

    def test_get_assignment_counts_cache_miss(self, cache, mock_redis):
        """Test getting assignment counts on cache miss calculates and caches."""
        # Arrange
        person_id = uuid4()
        assignments = [
            MagicMock(person_id=person_id, rotation_template_id=uuid4()),
            MagicMock(person_id=person_id, rotation_template_id=uuid4()),
            MagicMock(
                person_id=uuid4(), rotation_template_id=uuid4()
            ),  # Different person
        ]

        mock_redis.get.return_value = None

        # Act
        result = cache.get_assignment_counts(person_id, assignments)

        # Assert
        assert "total" in result
        assert "by_week" in result
        assert "by_template" in result
        assert result["total"] == 2  # Only 2 assignments for this person
        # Verify it was stored
        mock_redis.setex.assert_called_once()

    def test_get_assignment_counts_cache_hit(self, cache, mock_redis):
        """Test getting assignment counts on cache hit returns cached data."""
        # Arrange
        import pickle

        person_id = uuid4()
        cached_counts = {"total": 10, "by_week": {}, "by_template": {}}

        mock_redis.get.return_value = pickle.dumps(cached_counts)

        # Act
        result = cache.get_assignment_counts(person_id, [])

        # Assert
        assert result == cached_counts
        mock_redis.setex.assert_not_called()
        assert cache._hits == 1

    def test_invalidate_all_keys(self, cache, mock_redis):
        """Test invalidating all cache keys."""
        # Arrange
        mock_redis.scan.return_value = (0, [b"key1", b"key2", b"key3"])

        # Act
        cache.invalidate(keys=None)

        # Assert
        mock_redis.scan.assert_called_once()
        mock_redis.delete.assert_called_once_with(b"key1", b"key2", b"key3")

    def test_invalidate_specific_keys(self, cache, mock_redis):
        """Test invalidating specific cache keys."""
        # Arrange
        keys_to_invalidate = ["availability:123", "assignment_counts:456"]

        # Act
        cache.invalidate(keys=keys_to_invalidate)

        # Assert
        # Should prefix keys and delete them
        expected_keys = [f"{cache.KEY_PREFIX}{k}" for k in keys_to_invalidate]
        mock_redis.delete.assert_called_once_with(*expected_keys)

    def test_invalidate_handles_scan_pagination(self, cache, mock_redis):
        """Test invalidation handles Redis scan pagination correctly."""
        # Arrange
        # Simulate multiple scan iterations
        mock_redis.scan.side_effect = [
            (1, [b"key1", b"key2"]),
            (2, [b"key3", b"key4"]),
            (0, [b"key5"]),  # cursor=0 indicates end
        ]

        # Act
        cache.invalidate(keys=None)

        # Assert
        assert mock_redis.scan.call_count == 3
        assert mock_redis.delete.call_count == 3

    def test_warm_cache_preloads_data(self, cache, mock_redis):
        """Test cache warming preloads common queries."""
        # Arrange
        context = MagicMock()
        context.residents = [MagicMock(id=uuid4()) for _ in range(10)]
        context.blocks = [MagicMock(id=uuid4()) for _ in range(5)]

        availability = {}

        mock_redis.get.return_value = None
        mock_redis.scan.return_value = (0, [b"key1", b"key2", b"key3"])

        # Act
        cache.warm_cache(context, availability)

        # Assert
        # Should have made multiple cache stores
        assert mock_redis.setex.call_count > 0

    def test_get_stats_returns_metrics(self, cache, mock_redis):
        """Test getting cache statistics."""
        # Arrange
        cache._hits = 100
        cache._misses = 25
        mock_redis.scan.return_value = (0, [b"key1", b"key2", b"key3"])

        # Act
        stats = cache.get_stats()

        # Assert
        assert stats["hits"] == 100
        assert stats["misses"] == 25
        assert stats["hit_rate"] == 0.8  # 100/(100+25)
        assert stats["size"] == 3
        assert stats["max_size"] == 1000
        assert stats["ttl_seconds"] == 3600

    def test_get_stats_handles_zero_requests(self, cache, mock_redis):
        """Test stats handles zero requests gracefully."""
        # Arrange
        cache._hits = 0
        cache._misses = 0
        mock_redis.scan.return_value = (0, [])

        # Act
        stats = cache.get_stats()

        # Assert
        assert stats["hit_rate"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_hash_id_list_creates_consistent_hash(self):
        """Test ID list hashing is consistent and collision-resistant."""
        # Arrange
        ids1 = ["id-1", "id-2", "id-3"]
        ids2 = ["id-1", "id-2", "id-3"]
        ids3 = ["id-1", "id-2", "id-4"]  # Different

        # Act
        hash1 = ScheduleCache._hash_id_list(ids1)
        hash2 = ScheduleCache._hash_id_list(ids2)
        hash3 = ScheduleCache._hash_id_list(ids3)

        # Assert
        assert hash1 == hash2  # Same IDs produce same hash
        assert hash1 != hash3  # Different IDs produce different hash
        assert len(hash1) == 32  # SHA-256 truncated to 32 chars

    def test_create_key_joins_parts(self):
        """Test cache key creation joins parts with colon."""
        # Act
        key = ScheduleCache._create_key("part1", "part2", "part3")

        # Assert
        assert key == "part1:part2:part3"

    def test_cache_get_handles_errors_gracefully(self, cache, mock_redis):
        """Test cache get handles Redis errors gracefully."""
        # Arrange
        mock_redis.get.side_effect = Exception("Redis connection error")

        # Act
        result = cache._get("test_key")

        # Assert
        assert result is None
        assert cache._misses == 1

    def test_cache_put_handles_errors_gracefully(self, cache, mock_redis):
        """Test cache put handles Redis errors gracefully."""
        # Arrange
        mock_redis.setex.side_effect = Exception("Redis connection error")

        # Act - Should not raise
        cache._put("test_key", {"data": "value"})

        # Assert - No exception raised

    def test_get_global_cache_returns_singleton(self):
        """Test global cache returns singleton instance."""
        # Act
        with patch("app.scheduling.caching.redis.from_url"):
            cache1 = get_global_cache()
            cache2 = get_global_cache()

            # Assert
            assert cache1 is cache2  # Same instance


class TestCacheIntegration:
    """Integration tests for cache with realistic data."""

    def test_cache_workflow_realistic(self, cache, mock_redis):
        """Test realistic cache workflow with multiple operations."""
        # Arrange
        import pickle

        person_ids = [uuid4() for _ in range(5)]
        block_ids = [uuid4() for _ in range(10)]
        availability = {
            p: {b: {"available": True} for b in block_ids} for p in person_ids
        }

        # First call: cache miss
        mock_redis.get.return_value = None

        # Act 1: First call builds matrix
        result1 = cache.get_availability_matrix(person_ids, block_ids, availability)

        # Assert 1
        assert cache._misses == 1
        assert cache._hits == 0

        # Setup for second call: cache hit
        mock_redis.get.return_value = pickle.dumps(result1)

        # Act 2: Second call uses cache
        result2 = cache.get_availability_matrix(person_ids, block_ids, availability)

        # Assert 2
        assert result2 == result1
        assert cache._hits == 1
        assert cache._misses == 1  # Still 1, not incremented

    def test_cache_key_prefix_isolation(self, cache):
        """Test cache keys are properly prefixed to avoid collisions."""
        # Arrange
        key1 = cache._create_key("availability", "123")
        key2 = cache._create_key("assignment_counts", "123")

        # Assert
        assert key1 != key2
        assert "availability" in key1
        assert "assignment_counts" in key2
