"""Tests for pure static methods in ScheduleCache (no Redis, no DB)."""

import hashlib

from app.scheduling.caching import ScheduleCache


class TestCreateKey:
    """Tests for ScheduleCache._create_key static method."""

    def test_single_part(self):
        assert ScheduleCache._create_key("availability") == "availability"

    def test_two_parts(self):
        assert (
            ScheduleCache._create_key("availability", "abc123") == "availability:abc123"
        )

    def test_three_parts(self):
        result = ScheduleCache._create_key("availability", "person_hash", "block_hash")
        assert result == "availability:person_hash:block_hash"

    def test_integer_parts_converted(self):
        result = ScheduleCache._create_key("counts", 42)
        assert result == "counts:42"

    def test_uuid_like_string(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        result = ScheduleCache._create_key("assignment_counts", uid)
        assert result == f"assignment_counts:{uid}"

    def test_empty_string_part(self):
        result = ScheduleCache._create_key("prefix", "", "suffix")
        assert result == "prefix::suffix"

    def test_no_parts(self):
        result = ScheduleCache._create_key()
        assert result == ""


class TestHashIdList:
    """Tests for ScheduleCache._hash_id_list static method."""

    def test_returns_32_char_hex(self):
        result = ScheduleCache._hash_id_list(["id1", "id2", "id3"])
        assert isinstance(result, str)
        assert len(result) == 32

    def test_deterministic(self):
        ids = ["abc", "def", "ghi"]
        hash1 = ScheduleCache._hash_id_list(ids)
        hash2 = ScheduleCache._hash_id_list(ids)
        assert hash1 == hash2

    def test_different_lists_different_hash(self):
        hash1 = ScheduleCache._hash_id_list(["a", "b", "c"])
        hash2 = ScheduleCache._hash_id_list(["d", "e", "f"])
        assert hash1 != hash2

    def test_order_matters(self):
        hash1 = ScheduleCache._hash_id_list(["a", "b", "c"])
        hash2 = ScheduleCache._hash_id_list(["c", "b", "a"])
        assert hash1 != hash2

    def test_single_id(self):
        result = ScheduleCache._hash_id_list(["only_one"])
        assert len(result) == 32

    def test_empty_list(self):
        result = ScheduleCache._hash_id_list([])
        assert isinstance(result, str)
        assert len(result) == 32

    def test_matches_manual_sha256(self):
        ids = ["id1", "id2", "id3"]
        result = ScheduleCache._hash_id_list(ids)

        expected = hashlib.sha256(b"id1,id2,id3").hexdigest()[:32]
        assert result == expected

    def test_uuid_strings(self):
        uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        ]
        result = ScheduleCache._hash_id_list(uuids)
        assert len(result) == 32

    def test_large_list(self):
        ids = [f"id_{i}" for i in range(1000)]
        result = ScheduleCache._hash_id_list(ids)
        assert len(result) == 32

    def test_hex_characters_only(self):
        result = ScheduleCache._hash_id_list(["test"])
        assert all(c in "0123456789abcdef" for c in result)
