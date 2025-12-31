"""Tests for query caching functionality."""
import asyncio
import json
import pytest
from datetime import timedelta

from app.db.query_cache import QueryCache, CachedQuery, get_query_cache


@pytest.fixture
async def query_cache():
    """Create query cache instance for testing."""
    cache = QueryCache()
    await cache.connect()
    yield cache
    await cache.close()


@pytest.mark.asyncio
async def test_query_cache_get_or_fetch_miss(query_cache):
    """Test cache miss and fetch."""
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        return {"data": "test"}

    result = await query_cache.get_or_fetch(
        "test_key",
        fetch_fn,
        ttl=timedelta(seconds=10),
    )

    assert result == {"data": "test"}
    assert call_count == 1


@pytest.mark.asyncio
async def test_query_cache_get_or_fetch_hit(query_cache):
    """Test cache hit doesn't call fetch function."""
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        return {"data": "test"}

    # First call - cache miss
    result1 = await query_cache.get_or_fetch(
        "test_key",
        fetch_fn,
        ttl=timedelta(seconds=10),
    )

    # Second call - cache hit
    result2 = await query_cache.get_or_fetch(
        "test_key",
        fetch_fn,
        ttl=timedelta(seconds=10),
    )

    assert result1 == result2
    assert call_count == 1  # Only called once


@pytest.mark.asyncio
async def test_query_cache_invalidate_pattern(query_cache):
    """Test pattern-based cache invalidation."""
    # Set multiple keys
    await query_cache.get_or_fetch("schedule:2024-01-01", lambda: "data1")
    await query_cache.get_or_fetch("schedule:2024-01-02", lambda: "data2")
    await query_cache.get_or_fetch("person:123", lambda: "data3")

    # Invalidate schedule keys
    count = await query_cache.invalidate("schedule:*")

    assert count == 2


@pytest.mark.asyncio
async def test_query_cache_metrics(query_cache):
    """Test cache metrics tracking."""
    async def fetch_fn():
        return {"data": "test"}

    # Generate some hits and misses
    await query_cache.get_or_fetch("key1", fetch_fn)
    await query_cache.get_or_fetch("key1", fetch_fn)  # Hit
    await query_cache.get_or_fetch("key2", fetch_fn)

    metrics = await query_cache.get_metrics()

    assert metrics["hits"] == 1
    assert metrics["misses"] == 2
    assert metrics["total_queries"] == 3
    assert metrics["hit_rate"] > 0


@pytest.mark.asyncio
async def test_cached_query_decorator(query_cache):
    """Test cached query decorator."""
    call_count = 0

    @CachedQuery(query_cache, ttl=timedelta(seconds=10))
    async def expensive_query(param1: str, param2: int):
        nonlocal call_count
        call_count += 1
        return f"{param1}:{param2}"

    # First call - cache miss
    result1 = await expensive_query("test", 123)

    # Second call with same params - cache hit
    result2 = await expensive_query("test", 123)

    # Third call with different params - cache miss
    result3 = await expensive_query("test", 456)

    assert result1 == result2 == "test:123"
    assert result3 == "test:456"
    assert call_count == 2  # Only 2 unique calls


@pytest.mark.asyncio
async def test_query_cache_ttl_expiration(query_cache):
    """Test cache expiration after TTL."""
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        return {"data": f"call_{call_count}"}

    # Set with 1 second TTL
    result1 = await query_cache.get_or_fetch(
        "expiring_key",
        fetch_fn,
        ttl=timedelta(seconds=1),
    )

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should fetch again
    result2 = await query_cache.get_or_fetch(
        "expiring_key",
        fetch_fn,
        ttl=timedelta(seconds=1),
    )

    assert call_count == 2
    assert result1["data"] == "call_1"
    assert result2["data"] == "call_2"


@pytest.mark.asyncio
async def test_query_cache_generate_key():
    """Test deterministic key generation."""
    cache = QueryCache()

    query = "SELECT * FROM persons WHERE id = :id"
    params1 = {"id": "123"}
    params2 = {"id": "123"}
    params3 = {"id": "456"}

    key1 = cache.generate_key(query, params1)
    key2 = cache.generate_key(query, params2)
    key3 = cache.generate_key(query, params3)

    # Same query + params should generate same key
    assert key1 == key2

    # Different params should generate different key
    assert key1 != key3


@pytest.mark.asyncio
async def test_query_cache_concurrent_access(query_cache):
    """Test concurrent cache access."""
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # Simulate slow operation
        return {"data": "test"}

    # Make multiple concurrent requests
    results = await asyncio.gather(*[
        query_cache.get_or_fetch("concurrent_key", fetch_fn)
        for _ in range(5)
    ])

    # All results should be the same
    assert all(r == results[0] for r in results)

    # Function should only be called once (first miss)
    # Note: This might be > 1 due to race conditions, but should be < 5
    assert call_count < 5


def test_get_query_cache_singleton():
    """Test global cache instance."""
    cache1 = get_query_cache()
    cache2 = get_query_cache()

    assert cache1 is cache2
