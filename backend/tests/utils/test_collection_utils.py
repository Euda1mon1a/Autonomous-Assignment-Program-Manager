"""Tests for collection utility functions."""

import pytest

from app.utils.collection_utils import (
    chunk_list,
    flatten,
    group_by,
    safe_get,
    unique_by,
)


class TestChunkList:
    """Tests for chunk_list."""

    def test_even_chunks(self):
        result = chunk_list([1, 2, 3, 4], 2)
        assert result == [[1, 2], [3, 4]]

    def test_uneven_chunks(self):
        result = chunk_list([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_size_equals_list(self):
        result = chunk_list([1, 2, 3], 3)
        assert result == [[1, 2, 3]]

    def test_chunk_size_larger_than_list(self):
        result = chunk_list([1, 2], 5)
        assert result == [[1, 2]]

    def test_chunk_size_of_1(self):
        result = chunk_list([1, 2, 3], 1)
        assert result == [[1], [2], [3]]

    def test_empty_list(self):
        result = chunk_list([], 3)
        assert result == []

    def test_zero_size_raises(self):
        with pytest.raises(ValueError, match="positive"):
            chunk_list([1, 2], 0)

    def test_negative_size_raises(self):
        with pytest.raises(ValueError, match="positive"):
            chunk_list([1, 2], -1)


class TestFlatten:
    """Tests for flatten."""

    def test_simple_flatten(self):
        assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

    def test_empty_sublists(self):
        assert flatten([[], [1], []]) == [1]

    def test_single_sublist(self):
        assert flatten([[1, 2, 3]]) == [1, 2, 3]

    def test_empty_list(self):
        assert flatten([]) == []

    def test_mixed_types(self):
        assert flatten([["a", "b"], [1, 2]]) == ["a", "b", 1, 2]


class TestGroupBy:
    """Tests for group_by."""

    def test_group_by_value(self):
        items = [1, 2, 3, 4, 5, 6]
        result = group_by(items, lambda x: x % 2)
        assert result[0] == [2, 4, 6]
        assert result[1] == [1, 3, 5]

    def test_group_by_key(self):
        items = [
            {"name": "a", "type": "x"},
            {"name": "b", "type": "x"},
            {"name": "c", "type": "y"},
        ]
        result = group_by(items, lambda x: x["type"])
        assert len(result["x"]) == 2
        assert len(result["y"]) == 1

    def test_empty_list(self):
        result = group_by([], lambda x: x)
        assert result == {}

    def test_all_same_group(self):
        result = group_by([1, 2, 3], lambda x: "all")
        assert result["all"] == [1, 2, 3]

    def test_each_unique_group(self):
        result = group_by([1, 2, 3], lambda x: x)
        assert len(result) == 3


class TestUniqueBy:
    """Tests for unique_by."""

    def test_unique_by_value(self):
        result = unique_by([1, 2, 2, 3, 3, 3], lambda x: x)
        assert result == [1, 2, 3]

    def test_preserves_order(self):
        result = unique_by([3, 1, 2, 1, 3], lambda x: x)
        assert result == [3, 1, 2]

    def test_unique_by_key(self):
        items = [{"id": 1, "name": "a"}, {"id": 1, "name": "b"}, {"id": 2, "name": "c"}]
        result = unique_by(items, lambda x: x["id"])
        assert len(result) == 2
        assert result[0]["name"] == "a"  # First occurrence kept

    def test_empty_list(self):
        result = unique_by([], lambda x: x)
        assert result == []

    def test_all_unique(self):
        result = unique_by([1, 2, 3], lambda x: x)
        assert result == [1, 2, 3]


class TestSafeGet:
    """Tests for safe_get."""

    def test_simple_key(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_nested_keys(self):
        data = {"user": {"profile": {"name": "Alice"}}}
        assert safe_get(data, "user", "profile", "name") == "Alice"

    def test_missing_key_returns_default(self):
        assert safe_get({"a": 1}, "b") is None

    def test_custom_default(self):
        assert safe_get({"a": 1}, "b", default="missing") == "missing"

    def test_missing_nested_key(self):
        data = {"user": {"profile": {}}}
        assert safe_get(data, "user", "profile", "name", default="unknown") == "unknown"

    def test_non_dict_intermediate(self):
        data = {"user": "not a dict"}
        assert safe_get(data, "user", "profile") is None

    def test_empty_dict(self):
        assert safe_get({}, "a") is None

    def test_no_keys(self):
        data = {"a": 1}
        assert safe_get(data) == {"a": 1}
