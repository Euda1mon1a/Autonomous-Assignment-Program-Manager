"""Tests for cache invalidation strategies."""

from unittest.mock import AsyncMock

import pytest

from app.core.cache.strategies import (
    InvalidationStrategy,
    InvalidationTrigger,
    PatternStrategy,
    TTLStrategy,
    TagBasedStrategy,
    WriteThroughStrategy,
)


# ==================== InvalidationTrigger enum ====================


class TestInvalidationTrigger:
    def test_is_str_enum(self):
        assert isinstance(InvalidationTrigger.TTL_EXPIRED, str)

    def test_values(self):
        assert InvalidationTrigger.TTL_EXPIRED == "ttl_expired"
        assert InvalidationTrigger.WRITE_OPERATION == "write_operation"
        assert InvalidationTrigger.MANUAL == "manual"
        assert InvalidationTrigger.TAG_INVALIDATION == "tag_invalidation"
        assert InvalidationTrigger.PATTERN_MATCH == "pattern_match"
        assert InvalidationTrigger.CACHE_FULL == "cache_full"

    def test_all_unique(self):
        values = [t.value for t in InvalidationTrigger]
        assert len(values) == len(set(values))

    def test_count(self):
        assert len(InvalidationTrigger) == 6


# ==================== InvalidationStrategy base ====================


class TestInvalidationStrategyBase:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            InvalidationStrategy("test")

    def test_record_invalidation(self):
        strategy = TTLStrategy(namespace="test")
        assert strategy.invalidation_count == 0
        strategy._record_invalidation(5)
        assert strategy.invalidation_count == 5
        strategy._record_invalidation(3)
        assert strategy.invalidation_count == 8


# ==================== TTLStrategy ====================


class TestTTLStrategy:
    def test_init_defaults(self):
        s = TTLStrategy(namespace="test")
        assert s.namespace == "test"
        assert s.default_ttl == 300
        assert s.invalidation_count == 0

    def test_init_custom_ttl(self):
        s = TTLStrategy(namespace="test", default_ttl=600)
        assert s.default_ttl == 600

    @pytest.mark.asyncio
    async def test_should_invalidate_ttl_expired(self):
        s = TTLStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.TTL_EXPIRED)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_invalidate_other_trigger_no_ttl(self):
        s = TTLStrategy(namespace="test")
        # No ttl_remaining kwarg, defaults to -1 which is <= 0
        result = await s.should_invalidate("key", InvalidationTrigger.MANUAL)
        assert result is True  # -1 <= 0 -> True

    @pytest.mark.asyncio
    async def test_invalidate_with_key(self):
        s = TTLStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 1
        count = await s.invalidate(client, key="mykey")
        assert count == 1
        client.delete.assert_called_once_with("mykey")
        assert s.invalidation_count == 1

    @pytest.mark.asyncio
    async def test_invalidate_without_key(self):
        s = TTLStrategy(namespace="test")
        client = AsyncMock()
        count = await s.invalidate(client)
        assert count == 0

    @pytest.mark.asyncio
    async def test_set_ttl_default(self):
        s = TTLStrategy(namespace="test", default_ttl=300)
        client = AsyncMock()
        client.expire.return_value = True
        result = await s.set_ttl(client, "mykey")
        assert result is True
        client.expire.assert_called_once_with("mykey", 300)

    @pytest.mark.asyncio
    async def test_set_ttl_custom(self):
        s = TTLStrategy(namespace="test", default_ttl=300)
        client = AsyncMock()
        client.expire.return_value = True
        result = await s.set_ttl(client, "mykey", ttl=600)
        assert result is True
        client.expire.assert_called_once_with("mykey", 600)


# ==================== TagBasedStrategy ====================


class TestTagBasedStrategy:
    def test_init(self):
        s = TagBasedStrategy(namespace="schedule")
        assert s.namespace == "schedule"
        assert s.tag_prefix == "cache:tag:schedule"

    @pytest.mark.asyncio
    async def test_should_invalidate_tag_trigger(self):
        s = TagBasedStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.TAG_INVALIDATION)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_invalidate_other_trigger(self):
        s = TagBasedStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.MANUAL)
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_by_tag(self):
        s = TagBasedStrategy(namespace="test")
        client = AsyncMock()
        client.smembers.return_value = {"key1", "key2"}
        client.delete.return_value = 3  # 2 keys + tag key
        count = await s.invalidate(client, tag="user:1")
        assert count == 3

    @pytest.mark.asyncio
    async def test_invalidate_by_tag_empty(self):
        s = TagBasedStrategy(namespace="test")
        client = AsyncMock()
        client.smembers.return_value = set()
        count = await s.invalidate(client, tag="user:1")
        assert count == 0

    @pytest.mark.asyncio
    async def test_invalidate_by_key(self):
        s = TagBasedStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 1
        count = await s.invalidate(client, key="mykey")
        assert count == 1

    @pytest.mark.asyncio
    async def test_invalidate_no_args(self):
        s = TagBasedStrategy(namespace="test")
        client = AsyncMock()
        count = await s.invalidate(client)
        assert count == 0

    @pytest.mark.asyncio
    async def test_add_tags(self):
        s = TagBasedStrategy(namespace="test")
        client = AsyncMock()
        client.sadd.return_value = 1
        count = await s.add_tags(client, "mykey", ["tag1", "tag2"])
        assert count == 2
        assert client.sadd.call_count == 2


# ==================== PatternStrategy ====================


class TestPatternStrategy:
    def test_init(self):
        s = PatternStrategy(namespace="test")
        assert s.namespace == "test"

    @pytest.mark.asyncio
    async def test_should_invalidate_pattern_trigger(self):
        s = PatternStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.PATTERN_MATCH)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_invalidate_other_trigger(self):
        s = PatternStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.MANUAL)
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self):
        s = PatternStrategy(namespace="test")
        client = AsyncMock()
        # Simulate scan returning keys then cursor 0
        client.scan.return_value = (0, ["key1", "key2"])
        client.delete.return_value = 2
        count = await s.invalidate(client, pattern="cache:*")
        assert count == 2
        assert s.invalidation_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern_empty(self):
        s = PatternStrategy(namespace="test")
        client = AsyncMock()
        client.scan.return_value = (0, [])
        count = await s.invalidate(client, pattern="cache:*")
        assert count == 0

    @pytest.mark.asyncio
    async def test_invalidate_by_key(self):
        s = PatternStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 1
        count = await s.invalidate(client, key="mykey")
        assert count == 1

    @pytest.mark.asyncio
    async def test_invalidate_no_args(self):
        s = PatternStrategy(namespace="test")
        client = AsyncMock()
        count = await s.invalidate(client)
        assert count == 0

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern_multi_batch(self):
        s = PatternStrategy(namespace="test")
        client = AsyncMock()
        # Two scan iterations: first returns cursor 5 with keys, second returns 0
        client.scan.side_effect = [
            (5, ["key1", "key2"]),
            (0, ["key3"]),
        ]
        client.delete.side_effect = [2, 1]
        count = await s.invalidate_by_pattern(client, "cache:*")
        assert count == 3


# ==================== WriteThroughStrategy ====================


class TestWriteThroughStrategy:
    def test_init_defaults(self):
        s = WriteThroughStrategy(namespace="test")
        assert s.namespace == "test"
        assert s.invalidate_before_write is True

    def test_init_custom(self):
        s = WriteThroughStrategy(namespace="test", invalidate_before_write=False)
        assert s.invalidate_before_write is False

    @pytest.mark.asyncio
    async def test_should_invalidate_write(self):
        s = WriteThroughStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.WRITE_OPERATION)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_invalidate_other(self):
        s = WriteThroughStrategy(namespace="test")
        result = await s.should_invalidate("key", InvalidationTrigger.MANUAL)
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_with_key(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 1
        count = await s.invalidate(client, key="mykey")
        assert count == 1

    @pytest.mark.asyncio
    async def test_invalidate_with_keys_list(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 2
        count = await s.invalidate(client, keys=["k1", "k2"])
        assert count == 2

    @pytest.mark.asyncio
    async def test_invalidate_with_key_and_keys(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 3
        count = await s.invalidate(client, key="k0", keys=["k1", "k2"])
        assert count == 3
        # k0 appended to keys list
        client.delete.assert_called_once_with("k1", "k2", "k0")

    @pytest.mark.asyncio
    async def test_invalidate_no_args(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        count = await s.invalidate(client)
        assert count == 0

    @pytest.mark.asyncio
    async def test_invalidate_on_write(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        client.delete.return_value = 2
        count = await s.invalidate_on_write(client, ["k1", "k2"])
        assert count == 2
        assert s.invalidation_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_on_write_empty(self):
        s = WriteThroughStrategy(namespace="test")
        client = AsyncMock()
        count = await s.invalidate_on_write(client, [])
        assert count == 0
