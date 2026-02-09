"""Tests for cache utility functions."""

import pytest

from app.utils.cache_utils import (
    deserialize_from_cache,
    generate_cache_key,
    hash_dict,
    serialize_for_cache,
)


class TestGenerateCacheKey:
    """Tests for generate_cache_key."""

    def test_single_arg(self):
        key = generate_cache_key("hello")
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex digest length

    def test_multiple_args(self):
        key = generate_cache_key("hello", "world", 42)
        assert isinstance(key, str)
        assert len(key) == 64

    def test_deterministic(self):
        key1 = generate_cache_key("a", "b", "c")
        key2 = generate_cache_key("a", "b", "c")
        assert key1 == key2

    def test_different_args_different_keys(self):
        key1 = generate_cache_key("a", "b")
        key2 = generate_cache_key("b", "a")
        assert key1 != key2

    def test_no_args(self):
        key = generate_cache_key()
        assert isinstance(key, str)
        assert len(key) == 64

    def test_none_arg(self):
        key = generate_cache_key(None)
        assert isinstance(key, str)
        assert len(key) == 64

    def test_mixed_types(self):
        key = generate_cache_key("str", 42, 3.14, True, None)
        assert isinstance(key, str)


class TestHashDict:
    """Tests for hash_dict."""

    def test_simple_dict(self):
        h = hash_dict({"a": 1, "b": 2})
        assert isinstance(h, str)
        assert len(h) == 64

    def test_deterministic(self):
        h1 = hash_dict({"x": 10, "y": 20})
        h2 = hash_dict({"x": 10, "y": 20})
        assert h1 == h2

    def test_key_order_independent(self):
        h1 = hash_dict({"a": 1, "b": 2})
        h2 = hash_dict({"b": 2, "a": 1})
        assert h1 == h2

    def test_different_values_different_hash(self):
        h1 = hash_dict({"a": 1})
        h2 = hash_dict({"a": 2})
        assert h1 != h2

    def test_different_keys_different_hash(self):
        h1 = hash_dict({"a": 1})
        h2 = hash_dict({"b": 1})
        assert h1 != h2

    def test_empty_dict(self):
        h = hash_dict({})
        assert isinstance(h, str)
        assert len(h) == 64

    def test_nested_dict(self):
        h = hash_dict({"a": {"b": 1}})
        assert isinstance(h, str)


class TestSerializeForCache:
    """Tests for serialize_for_cache."""

    def test_dict(self):
        result = serialize_for_cache({"a": 1, "b": 2})
        assert isinstance(result, str)
        assert '"a": 1' in result

    def test_list(self):
        result = serialize_for_cache([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_string(self):
        result = serialize_for_cache("hello")
        assert result == '"hello"'

    def test_int(self):
        result = serialize_for_cache(42)
        assert result == "42"

    def test_float(self):
        result = serialize_for_cache(3.14)
        assert result == "3.14"

    def test_bool(self):
        assert serialize_for_cache(True) == "true"
        assert serialize_for_cache(False) == "false"

    def test_none(self):
        assert serialize_for_cache(None) == "null"

    def test_sorted_keys(self):
        result = serialize_for_cache({"z": 1, "a": 2})
        assert result.index('"a"') < result.index('"z"')

    def test_non_serializable_uses_str_default(self):
        """Objects that aren't JSON-native get converted via str()."""
        from datetime import date

        result = serialize_for_cache(date(2025, 1, 1))
        assert "2025-01-01" in result

    def test_round_trip(self):
        original = {"key": "value", "num": 42, "nested": [1, 2, 3]}
        serialized = serialize_for_cache(original)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == original


class TestDeserializeFromCache:
    """Tests for deserialize_from_cache."""

    def test_dict(self):
        result = deserialize_from_cache('{"a": 1}')
        assert result == {"a": 1}

    def test_list(self):
        result = deserialize_from_cache("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_string(self):
        result = deserialize_from_cache('"hello"')
        assert result == "hello"

    def test_number(self):
        assert deserialize_from_cache("42") == 42
        assert deserialize_from_cache("3.14") == 3.14

    def test_bool(self):
        assert deserialize_from_cache("true") is True
        assert deserialize_from_cache("false") is False

    def test_null(self):
        assert deserialize_from_cache("null") is None

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            deserialize_from_cache("not valid json")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            deserialize_from_cache("")
