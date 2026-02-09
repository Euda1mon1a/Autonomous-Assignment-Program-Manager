"""Tests for cache key generation utilities."""

from app.core.cache.keys import (
    CacheKeyGenerator,
    generate_cache_key,
    generate_stats_key,
    generate_tag_key,
)


# ==================== CacheKeyGenerator init ====================


class TestCacheKeyGeneratorInit:
    def test_defaults(self):
        gen = CacheKeyGenerator()
        assert gen.namespace == "cache"
        assert gen.version == "v1"
        assert gen.prefix == "cache"
        assert gen.separator == ":"

    def test_custom_namespace(self):
        gen = CacheKeyGenerator(namespace="schedule")
        assert gen.namespace == "schedule"

    def test_custom_version(self):
        gen = CacheKeyGenerator(version="v2")
        assert gen.version == "v2"

    def test_custom_prefix(self):
        gen = CacheKeyGenerator(prefix="myapp")
        assert gen.prefix == "myapp"

    def test_custom_separator(self):
        gen = CacheKeyGenerator(separator="-")
        assert gen.separator == "-"


# ==================== CacheKeyGenerator.generate ====================


class TestCacheKeyGeneratorGenerate:
    def test_basic_key(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        key = gen.generate("get_assignments")
        assert key == "cache:schedule:v1:get_assignments"

    def test_key_with_params(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        key = gen.generate("get_assignments", user_id=123)
        assert key.startswith("cache:schedule:v1:get_assignments:")
        # Last component is a 12-char hash
        parts = key.split(":")
        assert len(parts) == 5
        assert len(parts[-1]) == 12

    def test_no_namespace(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        key = gen.generate("get_user", include_namespace=False)
        assert "schedule" not in key
        assert key == "cache:v1:get_user"

    def test_no_version(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        key = gen.generate("get_user", include_version=False)
        assert "v1" not in key
        assert key == "cache:schedule:get_user"

    def test_no_namespace_no_version(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        key = gen.generate("get_user", include_namespace=False, include_version=False)
        assert key == "cache:get_user"

    def test_custom_separator_in_key(self):
        gen = CacheKeyGenerator(namespace="ns", version="v1", separator="-")
        key = gen.generate("func")
        assert key == "cache-ns-v1-func"

    def test_same_params_same_hash(self):
        gen = CacheKeyGenerator(namespace="ns")
        key1 = gen.generate("f", a=1, b=2)
        key2 = gen.generate("f", a=1, b=2)
        assert key1 == key2

    def test_different_params_different_hash(self):
        gen = CacheKeyGenerator(namespace="ns")
        key1 = gen.generate("f", a=1)
        key2 = gen.generate("f", a=2)
        assert key1 != key2

    def test_param_order_irrelevant(self):
        gen = CacheKeyGenerator(namespace="ns")
        key1 = gen.generate("f", a=1, b=2)
        key2 = gen.generate("f", b=2, a=1)
        assert key1 == key2


# ==================== CacheKeyGenerator.generate_tagged ====================


class TestCacheKeyGeneratorGenerateTagged:
    def test_returns_tuple(self):
        gen = CacheKeyGenerator(namespace="schedule")
        result = gen.generate_tagged("get_schedule", tags=["user:1"])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_cache_key(self):
        gen = CacheKeyGenerator(namespace="schedule")
        key, _ = gen.generate_tagged("get_schedule", tags=["user:1"])
        assert key.startswith("cache:schedule:v1:get_schedule")

    def test_tag_keys(self):
        gen = CacheKeyGenerator(namespace="schedule")
        _, tag_keys = gen.generate_tagged("get_schedule", tags=["user:1", "block:10"])
        assert len(tag_keys) == 2
        assert "cache:tag:schedule:user:1" in tag_keys
        assert "cache:tag:schedule:block:10" in tag_keys

    def test_tagged_with_params(self):
        gen = CacheKeyGenerator(namespace="schedule")
        key, _ = gen.generate_tagged("get_schedule", tags=["t1"], date="2024-01-01")
        parts = key.split(":")
        assert len(parts) == 5  # prefix:ns:ver:func:hash

    def test_empty_tags(self):
        gen = CacheKeyGenerator(namespace="schedule")
        _, tag_keys = gen.generate_tagged("f", tags=[])
        assert tag_keys == []


# ==================== CacheKeyGenerator.generate_pattern ====================


class TestCacheKeyGeneratorGeneratePattern:
    def test_pattern_with_function(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        pattern = gen.generate_pattern("get_user")
        assert pattern == "cache:schedule:v1:get_user:*"

    def test_pattern_without_function(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        pattern = gen.generate_pattern()
        assert pattern == "cache:schedule:v1:*"

    def test_pattern_no_namespace(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        pattern = gen.generate_pattern("f", include_namespace=False)
        assert pattern == "cache:v1:f:*"

    def test_pattern_no_version(self):
        gen = CacheKeyGenerator(namespace="schedule", version="v1")
        pattern = gen.generate_pattern("f", include_version=False)
        assert pattern == "cache:schedule:f:*"

    def test_pattern_bare(self):
        gen = CacheKeyGenerator(namespace="ns", version="v1")
        pattern = gen.generate_pattern(include_namespace=False, include_version=False)
        assert pattern == "cache:*"


# ==================== CacheKeyGenerator._hash_params ====================


class TestHashParams:
    def test_returns_12_chars(self):
        gen = CacheKeyGenerator()
        result = gen._hash_params({"a": 1})
        assert len(result) == 12

    def test_hex_only(self):
        gen = CacheKeyGenerator()
        result = gen._hash_params({"key": "value"})
        assert all(c in "0123456789abcdef" for c in result)

    def test_sorted_consistency(self):
        gen = CacheKeyGenerator()
        h1 = gen._hash_params({"b": 2, "a": 1})
        h2 = gen._hash_params({"a": 1, "b": 2})
        assert h1 == h2

    def test_different_values_different_hash(self):
        gen = CacheKeyGenerator()
        h1 = gen._hash_params({"x": 1})
        h2 = gen._hash_params({"x": 2})
        assert h1 != h2

    def test_handles_non_serializable(self):
        gen = CacheKeyGenerator()
        # json.dumps with default=str handles non-serializable types
        result = gen._hash_params({"obj": object()})
        assert len(result) == 12


# ==================== generate_cache_key helper ====================


class TestGenerateCacheKey:
    def test_basic(self):
        key = generate_cache_key("schedule", "get_assignments")
        assert key == "cache:schedule:v1:get_assignments"

    def test_with_params(self):
        key = generate_cache_key("schedule", "get_assignments", user_id=123)
        assert key.startswith("cache:schedule:v1:get_assignments:")

    def test_custom_version(self):
        key = generate_cache_key("schedule", "get_assignments", version="v2")
        assert "v2" in key

    def test_default_version(self):
        key = generate_cache_key("schedule", "func")
        assert ":v1:" in key


# ==================== generate_tag_key helper ====================


class TestGenerateTagKey:
    def test_basic(self):
        key = generate_tag_key("schedule", "user:123")
        assert key == "cache:tag:schedule:user:123"

    def test_custom_prefix(self):
        key = generate_tag_key("schedule", "user:123", prefix="myapp")
        assert key == "myapp:tag:schedule:user:123"

    def test_default_prefix(self):
        key = generate_tag_key("ns", "tag1")
        assert key.startswith("cache:")


# ==================== generate_stats_key helper ====================


class TestGenerateStatsKey:
    def test_basic(self):
        key = generate_stats_key("schedule")
        assert key == "cache:stats:schedule"

    def test_custom_prefix(self):
        key = generate_stats_key("schedule", prefix="myapp")
        assert key == "myapp:stats:schedule"

    def test_default_prefix(self):
        key = generate_stats_key("ns")
        assert key.startswith("cache:")
