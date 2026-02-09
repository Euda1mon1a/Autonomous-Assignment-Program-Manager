"""Tests for Redis-based service cache layer."""

from datetime import date, datetime
from enum import Enum
from unittest.mock import MagicMock, patch
from uuid import UUID

import redis as redis_lib

from app.core.service_cache import CachePrefix, CacheTTL, ServiceCache


# ==================== CachePrefix Enum ====================


class TestCachePrefix:
    def test_is_str_enum(self):
        assert isinstance(CachePrefix.HEATMAP, str)

    def test_heatmap(self):
        assert CachePrefix.HEATMAP == "heatmap"

    def test_calendar(self):
        assert CachePrefix.CALENDAR == "calendar"

    def test_assignments(self):
        assert CachePrefix.ASSIGNMENTS == "assignments"

    def test_persons(self):
        assert CachePrefix.PERSONS == "persons"

    def test_rotations(self):
        assert CachePrefix.ROTATIONS == "rotations"

    def test_blocks(self):
        assert CachePrefix.BLOCKS == "blocks"

    def test_coverage(self):
        assert CachePrefix.COVERAGE == "coverage"

    def test_workload(self):
        assert CachePrefix.WORKLOAD == "workload"

    def test_schedule(self):
        assert CachePrefix.SCHEDULE == "schedule"

    def test_general(self):
        assert CachePrefix.GENERAL == "service"

    def test_all_unique(self):
        values = [p.value for p in CachePrefix]
        assert len(values) == len(set(values))


# ==================== CacheTTL Constants ====================


class TestCacheTTL:
    def test_short(self):
        assert CacheTTL.SHORT == 300

    def test_medium(self):
        assert CacheTTL.MEDIUM == 1800

    def test_long(self):
        assert CacheTTL.LONG == 3600

    def test_extended(self):
        assert CacheTTL.EXTENDED == 14400

    def test_day(self):
        assert CacheTTL.DAY == 86400

    def test_week(self):
        assert CacheTTL.WEEK == 604800

    def test_ordering(self):
        assert CacheTTL.SHORT < CacheTTL.MEDIUM < CacheTTL.LONG
        assert CacheTTL.LONG < CacheTTL.EXTENDED < CacheTTL.DAY < CacheTTL.WEEK


# ==================== ServiceCache constants ====================


class TestServiceCacheConstants:
    def test_key_prefix(self):
        assert ServiceCache.KEY_PREFIX == "svc_cache:"


# ==================== _serialize_arg (static method) ====================


class TestSerializeArg:
    def test_none(self):
        assert ServiceCache._serialize_arg(None) == "None"

    def test_uuid(self):
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert (
            ServiceCache._serialize_arg(uid) == "12345678-1234-5678-1234-567812345678"
        )

    def test_date(self):
        d = date(2025, 3, 15)
        assert ServiceCache._serialize_arg(d) == "2025-03-15"

    def test_datetime(self):
        dt = datetime(2025, 3, 15, 10, 30, 0)
        result = ServiceCache._serialize_arg(dt)
        assert "2025-03-15" in result

    def test_list(self):
        result = ServiceCache._serialize_arg([3, 1, 2])
        assert result.startswith("[")
        assert result.endswith("]")

    def test_list_sorted(self):
        result = ServiceCache._serialize_arg(["c", "a", "b"])
        assert result == "[a,b,c]"

    def test_list_limited(self):
        """Long lists are truncated to 10 items."""
        result = ServiceCache._serialize_arg(list(range(20)))
        items = result.strip("[]").split(",")
        assert len(items) <= 10

    def test_tuple(self):
        result = ServiceCache._serialize_arg((3, 1, 2))
        assert result.startswith("[")

    def test_dict(self):
        result = ServiceCache._serialize_arg({"b": 2, "a": 1})
        assert result.startswith("{")
        assert result.endswith("}")
        # Should be sorted by key
        assert result.index("a") < result.index("b")

    def test_bool_true(self):
        assert ServiceCache._serialize_arg(True) == "true"

    def test_bool_false(self):
        assert ServiceCache._serialize_arg(False) == "false"

    def test_int(self):
        assert ServiceCache._serialize_arg(42) == "42"

    def test_float(self):
        assert ServiceCache._serialize_arg(3.14) == "3.14"

    def test_string(self):
        assert ServiceCache._serialize_arg("hello") == "hello"

    def test_long_string_truncated(self):
        long_str = "a" * 100
        result = ServiceCache._serialize_arg(long_str)
        assert len(result) == 50

    def test_enum(self):
        class Color(Enum):
            RED = "red"

        assert ServiceCache._serialize_arg(Color.RED) == "red"

    def test_unknown_type(self):
        """Unknown types get a hash."""

        class Custom:
            pass

        result = ServiceCache._serialize_arg(Custom())
        assert len(result) == 8  # md5 hex[:8]


# ==================== _build_cache_key ====================


class TestBuildCacheKey:
    def _make_cache(self):
        """Create a ServiceCache with disabled Redis."""
        with (
            patch("app.core.service_cache.get_settings") as mock_settings,
            patch("app.core.service_cache.redis.from_url") as mock_redis,
        ):
            settings = MagicMock()
            settings.redis_url_with_password = "redis://localhost:6379/0"
            mock_settings.return_value = settings
            mock_client = MagicMock()
            mock_client.ping.side_effect = redis_lib.RedisError("no redis")
            mock_redis.return_value = mock_client
            cache = ServiceCache(enabled=False)
        return cache

    def test_basic_key(self):
        cache = self._make_cache()

        def my_func(x):
            pass

        key = cache._build_cache_key("test", my_func, (42,), {})
        assert "test" in key
        assert "my_func" in key
        assert "42" in key

    def test_skips_db_session(self):
        cache = self._make_cache()

        def my_func(db, x):
            pass

        db_mock = MagicMock()
        db_mock.execute = MagicMock()  # Has 'execute' attr -> skipped
        key = cache._build_cache_key("test", my_func, (db_mock, 5), {})
        assert "5" in key

    def test_kwargs_sorted(self):
        cache = self._make_cache()

        def my_func(**kwargs):
            pass

        key = cache._build_cache_key("test", my_func, (), {"b": 2, "a": 1})
        assert key.index("a=") < key.index("b=")

    def test_long_key_hashed(self):
        cache = self._make_cache()

        def my_func(x):
            pass

        long_arg = "x" * 300
        key = cache._build_cache_key("test", my_func, (long_arg,), {})
        assert len(key) <= 200


# ==================== ServiceCache disabled path ====================


class TestServiceCacheDisabled:
    def _make_disabled_cache(self):
        with (
            patch("app.core.service_cache.get_settings") as mock_settings,
            patch("app.core.service_cache.redis.from_url") as mock_redis,
        ):
            settings = MagicMock()
            settings.redis_url_with_password = "redis://localhost:6379/0"
            mock_settings.return_value = settings
            mock_client = MagicMock()
            mock_client.ping.side_effect = redis_lib.RedisError("no redis")
            mock_redis.return_value = mock_client
            cache = ServiceCache(enabled=False)
        return cache

    def test_not_available(self):
        cache = self._make_disabled_cache()
        assert cache.is_available is False

    def test_get_returns_none(self):
        cache = self._make_disabled_cache()
        assert cache.get("test") is None

    def test_set_returns_false(self):
        cache = self._make_disabled_cache()
        assert cache.set("test", "value") is False

    def test_delete_returns_false(self):
        cache = self._make_disabled_cache()
        assert cache.delete("test") is False

    def test_invalidate_pattern_returns_zero(self):
        cache = self._make_disabled_cache()
        assert cache.invalidate_pattern("*") == 0

    def test_invalidate_by_prefix(self):
        cache = self._make_disabled_cache()
        assert cache.invalidate_by_prefix(CachePrefix.HEATMAP) == 0

    def test_invalidate_all(self):
        cache = self._make_disabled_cache()
        assert cache.invalidate_all() == 0

    def test_get_stats(self):
        cache = self._make_disabled_cache()
        stats = cache.get_stats()
        assert stats["available"] is False
        assert stats["enabled"] is False
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_reset_stats(self):
        cache = self._make_disabled_cache()
        cache._hits = 10
        cache._misses = 5
        cache._errors = 2
        cache.reset_stats()
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._errors == 0
