"""
Unit tests for scheduling optimizer and cache modules.
"""
import pytest
import time
from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.optimizer import (
    profile_time,
    profile_detailed,
    MemoizedFunction,
    memoize,
    QueryOptimizer,
    BatchProcessor,
    TimeoutHandler,
    QualityChecker,
    PerformanceStats,
)
from app.scheduling.cache import (
    CacheKeyGenerator,
    CacheEntry,
    ScheduleCache,
    cached,
    PatternInvalidationStrategy,
    AggressiveInvalidationStrategy,
    get_schedule_cache,
)


# ==================================================
# TESTS FOR PROFILING DECORATORS
# ==================================================

class TestProfilingDecorators:
    """Test performance profiling decorators."""

    def test_profile_time_decorator(self, caplog):
        """Test that profile_time logs execution time."""
        @profile_time
        def slow_function():
            time.sleep(0.01)
            return 42

        result = slow_function()
        assert result == 42
        # Check log contains timing info
        assert any("slow_function" in record.message for record in caplog.records)

    def test_profile_detailed_decorator(self, caplog):
        """Test that profile_detailed logs time."""
        @profile_detailed
        def test_function():
            return [i for i in range(1000)]

        result = test_function()
        assert len(result) == 1000
        assert any("test_function" in record.message for record in caplog.records)

    def test_nested_profiling(self, caplog):
        """Test profiling of nested functions."""
        @profile_time
        def outer():
            return inner()

        @profile_time
        def inner():
            return 100

        result = outer()
        assert result == 100


# ==================================================
# TESTS FOR MEMOIZATION
# ==================================================

class TestMemoization:
    """Test memoization utilities."""

    def test_memoized_function_basic(self):
        """Test basic memoization functionality."""
        call_count = 0

        @MemoizedFunction(max_size=10)
        def expensive_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call - should execute
        result1 = expensive_func(2, 3)
        assert result1 == 5
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = expensive_func(2, 3)
        assert result2 == 5
        assert call_count == 1  # Not incremented

        # Different args - should execute
        result3 = expensive_func(3, 4)
        assert result3 == 7
        assert call_count == 2

    def test_memoized_function_ttl(self):
        """Test TTL-based expiration."""
        call_count = 0

        @MemoizedFunction(max_size=10, ttl_seconds=0.1)
        def func_with_ttl(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = func_with_ttl(5)
        assert result1 == 10
        assert call_count == 1

        # Immediate second call - cached
        result2 = func_with_ttl(5)
        assert call_count == 1

        # Wait for TTL to expire
        time.sleep(0.15)

        # Should re-execute
        result3 = func_with_ttl(5)
        assert result3 == 10
        assert call_count == 2

    def test_memoized_function_max_size(self):
        """Test LRU eviction when max size exceeded."""
        @MemoizedFunction(max_size=3)
        def cached_func(x):
            return x ** 2

        # Fill cache
        cached_func(1)  # 1
        cached_func(2)  # 4
        cached_func(3)  # 9

        # All should be cached
        info = cached_func.cache_info()
        assert info['size'] == 3

        # Add one more - should evict oldest (1)
        cached_func(4)  # 16

        info = cached_func.cache_info()
        assert info['size'] == 3  # Still 3

    def test_memoize_decorator(self):
        """Test simple memoize decorator."""
        counter = 0

        @memoize
        def fibonacci(n):
            nonlocal counter
            counter += 1
            if n < 2:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        result = fibonacci(10)
        assert result == 55
        # Without memoization, would be ~177 calls
        # With memoization, should be ~11 calls
        assert counter < 20

    def test_cache_info(self):
        """Test cache statistics."""
        @MemoizedFunction(max_size=10)
        def func(x):
            return x * 2

        # Generate some hits and misses
        func(1)  # miss
        func(1)  # hit
        func(2)  # miss
        func(1)  # hit

        info = func.cache_info()
        assert info['hits'] == 2
        assert info['misses'] == 2
        assert info['size'] == 2
        assert info['hit_rate'] == 0.5

    def test_cache_clear(self):
        """Test cache clearing."""
        @MemoizedFunction(max_size=10)
        def func(x):
            return x * 2

        func(1)
        func(2)
        assert func.cache_info()['size'] == 2

        func.cache_clear()
        assert func.cache_info()['size'] == 0
        assert func.cache_info()['hits'] == 0


# ==================================================
# TESTS FOR TIMEOUT AND QUALITY CHECKERS
# ==================================================

class TestTimeoutHandler:
    """Test timeout handler."""

    def test_timeout_basic(self):
        """Test basic timeout functionality."""
        handler = TimeoutHandler(timeout_seconds=0.1)

        assert not handler.should_terminate()
        time.sleep(0.15)
        assert handler.should_terminate()

    def test_elapsed_and_remaining(self):
        """Test elapsed and remaining time."""
        handler = TimeoutHandler(timeout_seconds=1.0)

        time.sleep(0.1)
        elapsed = handler.elapsed()
        remaining = handler.remaining()

        assert 0.09 < elapsed < 0.2
        assert 0.8 < remaining < 0.91

    def test_reset(self):
        """Test resetting the timeout."""
        handler = TimeoutHandler(timeout_seconds=0.1)

        time.sleep(0.05)
        handler.reset()

        assert handler.elapsed() < 0.01
        assert not handler.should_terminate()


class TestQualityChecker:
    """Test quality checker for early termination."""

    def test_quality_basic(self):
        """Test basic quality checking."""
        checker = QualityChecker(target_quality=0.9, min_iterations=5)

        # First few iterations - shouldn't satisfy even if quality is high
        assert not checker.is_satisfied(0.95)
        assert not checker.is_satisfied(0.95)
        assert not checker.is_satisfied(0.95)
        assert not checker.is_satisfied(0.95)

        # After min iterations, should satisfy
        assert checker.is_satisfied(0.95)

    def test_quality_insufficient(self):
        """Test that low quality doesn't satisfy."""
        checker = QualityChecker(target_quality=0.9, min_iterations=5)

        for _ in range(10):
            assert not checker.is_satisfied(0.5)

    def test_quality_statistics(self):
        """Test quality statistics."""
        checker = QualityChecker(target_quality=0.9, min_iterations=3)

        checker.update(0.5)
        checker.update(0.7)
        checker.update(0.9)

        stats = checker.get_statistics()
        assert stats['iterations'] == 3
        assert stats['best_quality'] == 0.9
        assert stats['current_quality'] == 0.9
        assert stats['improvement'] == 0.4


# ==================================================
# TESTS FOR PERFORMANCE STATS
# ==================================================

class TestPerformanceStats:
    """Test performance statistics tracking."""

    def test_measure_context(self):
        """Test measurement context manager."""
        stats = PerformanceStats()

        with stats.measure("operation1"):
            time.sleep(0.01)

        timing = stats.get_timing("operation1")
        assert timing['count'] == 1
        assert timing['total'] > 0.009

    def test_multiple_measurements(self):
        """Test multiple measurements of same operation."""
        stats = PerformanceStats()

        for _ in range(3):
            with stats.measure("op"):
                time.sleep(0.01)

        timing = stats.get_timing("op")
        assert timing['count'] == 3
        assert timing['avg'] > 0.009

    def test_counters(self):
        """Test counter tracking."""
        stats = PerformanceStats()

        stats.increment("items_processed")
        stats.increment("items_processed", 5)
        stats.increment("errors", 2)

        assert stats.counters["items_processed"] == 6
        assert stats.counters["errors"] == 2

    def test_report(self):
        """Test report generation."""
        stats = PerformanceStats()

        with stats.measure("phase1"):
            time.sleep(0.01)

        stats.increment("count", 10)

        report = stats.report()
        assert "Performance Statistics" in report
        assert "phase1" in report
        assert "count" in report


# ==================================================
# TESTS FOR CACHE KEY GENERATION
# ==================================================

class TestCacheKeyGenerator:
    """Test cache key generation."""

    def test_generate_key_basic(self):
        """Test basic key generation."""
        key1 = CacheKeyGenerator.generate_key(1, 2, 3)
        key2 = CacheKeyGenerator.generate_key(1, 2, 3)
        key3 = CacheKeyGenerator.generate_key(1, 2, 4)

        # Same inputs should produce same key
        assert key1 == key2
        # Different inputs should produce different key
        assert key1 != key3

    def test_generate_key_with_uuid(self):
        """Test key generation with UUIDs."""
        uuid1 = uuid4()
        uuid2 = uuid4()

        key1 = CacheKeyGenerator.generate_key(uuid1)
        key2 = CacheKeyGenerator.generate_key(uuid1)
        key3 = CacheKeyGenerator.generate_key(uuid2)

        assert key1 == key2
        assert key1 != key3

    def test_generate_key_with_dates(self):
        """Test key generation with dates."""
        date1 = date(2024, 1, 1)
        date2 = date(2024, 1, 1)
        date3 = date(2024, 1, 2)

        key1 = CacheKeyGenerator.generate_key(date1)
        key2 = CacheKeyGenerator.generate_key(date2)
        key3 = CacheKeyGenerator.generate_key(date3)

        assert key1 == key2
        assert key1 != key3

    def test_generate_key_with_kwargs(self):
        """Test key generation with keyword arguments."""
        key1 = CacheKeyGenerator.generate_key(a=1, b=2)
        key2 = CacheKeyGenerator.generate_key(b=2, a=1)  # Different order
        key3 = CacheKeyGenerator.generate_key(a=1, b=3)

        # Order shouldn't matter for kwargs
        assert key1 == key2
        assert key1 != key3

    def test_generate_pattern_key(self):
        """Test pattern-based key generation."""
        org_id = uuid4()
        start_date = date(2024, 1, 1)

        key = CacheKeyGenerator.generate_pattern_key(
            "schedule:{org_id}:{start}",
            org_id=org_id,
            start=start_date
        )

        assert "schedule:" in key
        assert str(org_id) in key


# ==================================================
# TESTS FOR CACHE ENTRY
# ==================================================

class TestCacheEntry:
    """Test cache entry."""

    def test_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            value="test_data",
            created_at=time.time(),
            ttl=60.0
        )

        assert entry.value == "test_data"
        assert not entry.is_expired()
        assert entry.access_count == 0

    def test_entry_expiration(self):
        """Test entry expiration."""
        entry = CacheEntry(
            value="test_data",
            created_at=time.time() - 100,  # 100 seconds ago
            ttl=10.0  # 10 second TTL
        )

        assert entry.is_expired()

    def test_entry_no_ttl(self):
        """Test entry without TTL never expires."""
        entry = CacheEntry(
            value="test_data",
            created_at=time.time() - 1000,
            ttl=None
        )

        assert not entry.is_expired()

    def test_entry_access(self):
        """Test entry access tracking."""
        entry = CacheEntry(
            value="test_data",
            created_at=time.time(),
            ttl=60.0
        )

        assert entry.access_count == 0
        assert entry.last_accessed is None

        entry.access()
        assert entry.access_count == 1
        assert entry.last_accessed is not None


# ==================================================
# TESTS FOR SCHEDULE CACHE
# ==================================================

class TestScheduleCache:
    """Test schedule cache."""

    def test_cache_set_get(self):
        """Test basic set and get operations."""
        cache = ScheduleCache(max_size=100, default_ttl=None)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_cache_with_default(self):
        """Test get with default value."""
        cache = ScheduleCache()

        value = cache.get("nonexistent", default="default_value")
        assert value == "default_value"

    def test_cache_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = ScheduleCache(default_ttl=0.1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_cache_custom_ttl(self):
        """Test custom TTL per entry."""
        cache = ScheduleCache(default_ttl=10.0)

        cache.set("key1", "value1", ttl=0.1)
        assert cache.get("key1") == "value1"

        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size exceeded."""
        cache = ScheduleCache(max_size=3, default_ttl=None)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Cache should have 3 items
        stats = cache.stats()
        assert stats['size'] == 3

        # Add one more - should evict oldest (key1)
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_invalidate(self):
        """Test invalidating a single key."""
        cache = ScheduleCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        result = cache.invalidate("key1")
        assert result is True
        assert cache.get("key1") is None

        # Invalidating nonexistent key
        result = cache.invalidate("key2")
        assert result is False

    def test_cache_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        cache = ScheduleCache()

        cache.set("schedule:2024:01", "data1")
        cache.set("schedule:2024:02", "data2")
        cache.set("schedule:2024:03", "data3")
        cache.set("other:key", "data4")

        count = cache.invalidate_pattern("schedule:*")
        assert count == 3

        assert cache.get("schedule:2024:01") is None
        assert cache.get("schedule:2024:02") is None
        assert cache.get("other:key") == "data4"

    def test_cache_invalidate_all(self):
        """Test clearing entire cache."""
        cache = ScheduleCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.invalidate_all()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = ScheduleCache(max_size=100)

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        stats = cache.stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['size'] == 1
        assert stats['hit_rate'] == 2/3

    def test_cache_reset_stats(self):
        """Test resetting statistics."""
        cache = ScheduleCache()

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        cache.reset_stats()

        stats = cache.stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0


# ==================================================
# TESTS FOR CACHE DECORATOR
# ==================================================

class TestCachedDecorator:
    """Test cached decorator."""

    def test_cached_decorator_basic(self):
        """Test basic cached decorator."""
        cache = ScheduleCache()
        call_count = 0

        @cached(cache, ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = expensive_function(2, 3)
        assert result1 == 5
        assert call_count == 1

        result2 = expensive_function(2, 3)
        assert result2 == 5
        assert call_count == 1  # Cached

    def test_cached_decorator_with_prefix(self):
        """Test cached decorator with key prefix."""
        cache = ScheduleCache()

        @cached(cache, key_prefix="solver")
        def solver_func(x):
            return x * 2

        result = solver_func(5)
        assert result == 10


# ==================================================
# TESTS FOR INVALIDATION STRATEGIES
# ==================================================

class TestInvalidationStrategies:
    """Test cache invalidation strategies."""

    def test_pattern_invalidation_strategy(self):
        """Test pattern-based invalidation."""
        cache = ScheduleCache()
        strategy = PatternInvalidationStrategy(cache)

        # Set up some cached data
        cache.set("schedule:block:123:data", "value1")
        cache.set("schedule:person:456:data", "value2")
        cache.set("other:data", "value3")

        # Simulate assignment creation
        class MockAssignment:
            block_id = uuid4()
            person_id = uuid4()

        assignment = MockAssignment()
        cache.set(f"schedule:block:{assignment.block_id}:data", "value")

        strategy.on_assignment_created(assignment)

        # Block-specific cache should be invalidated
        assert cache.get(f"schedule:block:{assignment.block_id}:data") is None

    def test_aggressive_invalidation_strategy(self):
        """Test aggressive invalidation."""
        cache = ScheduleCache()
        strategy = AggressiveInvalidationStrategy(cache)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        class MockAssignment:
            block_id = uuid4()
            person_id = uuid4()

        strategy.on_assignment_created(MockAssignment())

        # All caches should be cleared
        assert cache.get("key1") is None
        assert cache.get("key2") is None


# ==================================================
# TESTS FOR GLOBAL CACHE
# ==================================================

class TestGlobalCache:
    """Test global cache utilities."""

    def test_get_schedule_cache_singleton(self):
        """Test that get_schedule_cache returns singleton."""
        cache1 = get_schedule_cache()
        cache2 = get_schedule_cache()

        assert cache1 is cache2


# ==================================================
# INTEGRATION TESTS
# ==================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_optimizer_with_cache(self):
        """Test using optimizer with cache."""
        cache = ScheduleCache(max_size=100, default_ttl=300)
        call_count = 0

        @cached(cache, ttl=60, key_prefix="test")
        @profile_time
        def complex_operation(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)
            return x * y

        result1 = complex_operation(3, 4)
        assert result1 == 12
        assert call_count == 1

        result2 = complex_operation(3, 4)
        assert result2 == 12
        assert call_count == 1  # Should use cache

    def test_performance_stats_with_memoization(self):
        """Test performance stats with memoized functions."""
        stats = PerformanceStats()

        @memoize
        def cached_func(n):
            with stats.measure("computation"):
                return n ** 2

        # First call - should measure
        result1 = cached_func(5)
        assert result1 == 25

        timing1 = stats.get_timing("computation")
        assert timing1['count'] == 1

        # Second call - should use cache, no new measurement
        result2 = cached_func(5)
        assert result2 == 25

        timing2 = stats.get_timing("computation")
        assert timing2['count'] == 1  # Still 1, used cache
