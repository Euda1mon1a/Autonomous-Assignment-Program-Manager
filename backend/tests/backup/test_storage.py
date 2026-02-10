"""Tests for backup storage backends (no DB, no external deps)."""

from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from app.backup.storage import BackupStorage, LocalStorage


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing ABC helpers
# ---------------------------------------------------------------------------


class _ConcreteStorage(BackupStorage):
    """Minimal concrete subclass to test BackupStorage helper methods."""

    def save_backup(self, backup_id: str, backup_data: dict[str, Any]) -> bool:
        return True

    def get_backup(self, backup_id: str) -> dict[str, Any]:
        return {}

    def delete_backup(self, backup_id: str) -> bool:
        return True

    def list_backups(
        self, backup_type: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return []

    def verify_backup(self, backup_id: str) -> bool:
        return True

    def get_backup_size(self, backup_id: str) -> int:
        return 0


# ---------------------------------------------------------------------------
# BackupStorage._calculate_checksum
# ---------------------------------------------------------------------------


class TestCalculateChecksum:
    def setup_method(self):
        self.storage = _ConcreteStorage()

    def test_empty_bytes(self):
        result = self.storage._calculate_checksum(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hello_bytes(self):
        data = b"hello world"
        result = self.storage._calculate_checksum(data)
        expected = hashlib.sha256(data).hexdigest()
        assert result == expected

    def test_returns_hex_string(self):
        result = self.storage._calculate_checksum(b"test")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest length

    def test_deterministic(self):
        data = b"deterministic"
        r1 = self.storage._calculate_checksum(data)
        r2 = self.storage._calculate_checksum(data)
        assert r1 == r2

    def test_different_data_different_checksum(self):
        r1 = self.storage._calculate_checksum(b"aaa")
        r2 = self.storage._calculate_checksum(b"bbb")
        assert r1 != r2

    def test_large_data(self):
        data = b"x" * 1_000_000
        result = self.storage._calculate_checksum(data)
        assert len(result) == 64


# ---------------------------------------------------------------------------
# BackupStorage._compress_backup / _decompress_backup
# ---------------------------------------------------------------------------


class TestCompressDecompress:
    def setup_method(self):
        self.storage = _ConcreteStorage()

    def test_compress_returns_bytes(self):
        result = self.storage._compress_backup({"key": "value"})
        assert isinstance(result, bytes)

    def test_compress_is_gzip(self):
        compressed = self.storage._compress_backup({"a": 1})
        # Gzip magic number
        assert compressed[:2] == b"\x1f\x8b"

    def test_roundtrip_simple(self):
        original = {"name": "test", "count": 42}
        compressed = self.storage._compress_backup(original)
        restored = self.storage._decompress_backup(compressed)
        assert restored == original

    def test_roundtrip_nested(self):
        original = {"outer": {"inner": [1, 2, 3]}, "flag": True}
        compressed = self.storage._compress_backup(original)
        restored = self.storage._decompress_backup(compressed)
        assert restored == original

    def test_roundtrip_empty_dict(self):
        original = {}
        compressed = self.storage._compress_backup(original)
        restored = self.storage._decompress_backup(compressed)
        assert restored == original

    def test_compress_uses_json_default_str(self):
        """Non-serializable types are converted to str via default=str."""
        from datetime import datetime

        data = {"ts": datetime(2026, 1, 1, 12, 0)}
        compressed = self.storage._compress_backup(data)
        restored = self.storage._decompress_backup(compressed)
        assert "2026" in restored["ts"]

    def test_decompress_invalid_data_raises(self):
        with pytest.raises(ValueError, match="Failed to decompress"):
            self.storage._decompress_backup(b"not gzip data")

    def test_decompress_empty_bytes_raises(self):
        with pytest.raises(ValueError, match="Failed to decompress"):
            self.storage._decompress_backup(b"")

    def test_decompress_valid_gzip_invalid_json_raises(self):
        bad_gzip = gzip.compress(b"not json")
        with pytest.raises(ValueError, match="Failed to decompress"):
            self.storage._decompress_backup(bad_gzip)

    def test_compressed_smaller_than_raw(self):
        large_data = {"data": "a" * 10000}
        compressed = self.storage._compress_backup(large_data)
        raw = json.dumps(large_data).encode("utf-8")
        assert len(compressed) < len(raw)


# ---------------------------------------------------------------------------
# LocalStorage.__init__ and directory structure
# ---------------------------------------------------------------------------


class TestLocalStorageInit:
    def test_default_dir_uses_tempdir(self):
        storage = LocalStorage()
        assert storage.backup_dir.exists()

    def test_custom_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(backup_dir=tmpdir)
            assert storage.backup_dir == Path(tmpdir)

    def test_creates_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom = Path(tmpdir) / "backups"
            storage = LocalStorage(backup_dir=custom)
            assert (storage.backup_dir / "full").is_dir()
            assert (storage.backup_dir / "incremental").is_dir()
            assert (storage.backup_dir / "differential").is_dir()

    def test_accepts_path_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(backup_dir=Path(tmpdir))
            assert storage.backup_dir == Path(tmpdir)

    def test_accepts_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(backup_dir=tmpdir)
            assert storage.backup_dir == Path(tmpdir)

    def test_idempotent_init(self):
        """Calling init twice on the same dir doesn't fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom = Path(tmpdir) / "backups"
            LocalStorage(backup_dir=custom)
            LocalStorage(backup_dir=custom)
            assert (custom / "full").is_dir()


# ---------------------------------------------------------------------------
# LocalStorage._get_backup_path / _get_metadata_path
# ---------------------------------------------------------------------------


class TestLocalStoragePaths:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_backup_path_default_type(self):
        path = self.storage._get_backup_path("abc123")
        assert path == Path(self.tmpdir) / "full" / "backup_abc123.json.gz"

    def test_backup_path_incremental(self):
        path = self.storage._get_backup_path("abc123", "incremental")
        assert path == Path(self.tmpdir) / "incremental" / "backup_abc123.json.gz"

    def test_backup_path_differential(self):
        path = self.storage._get_backup_path("abc123", "differential")
        assert path == Path(self.tmpdir) / "differential" / "backup_abc123.json.gz"

    def test_metadata_path_default_type(self):
        path = self.storage._get_metadata_path("abc123")
        assert path == Path(self.tmpdir) / "full" / "backup_abc123.meta.json"

    def test_metadata_path_incremental(self):
        path = self.storage._get_metadata_path("abc123", "incremental")
        assert path == Path(self.tmpdir) / "incremental" / "backup_abc123.meta.json"


# ---------------------------------------------------------------------------
# LocalStorage.save_backup
# ---------------------------------------------------------------------------


class TestLocalStorageSaveBackup:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_save_returns_true(self):
        data = {"key": "value"}
        assert self.storage.save_backup("id1", data) is True

    def test_save_creates_backup_file(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        path = self.storage._get_backup_path("id1", "full")
        assert path.exists()

    def test_save_creates_metadata_file(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        meta_path = self.storage._get_metadata_path("id1", "full")
        assert meta_path.exists()

    def test_save_backup_is_gzipped(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        path = self.storage._get_backup_path("id1", "full")
        content = path.read_bytes()
        assert content[:2] == b"\x1f\x8b"

    def test_save_metadata_is_json(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        meta_path = self.storage._get_metadata_path("id1", "full")
        metadata = json.loads(meta_path.read_text())
        assert metadata["backup_id"] == "id1"

    def test_save_metadata_has_checksum(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        meta_path = self.storage._get_metadata_path("id1", "full")
        metadata = json.loads(meta_path.read_text())
        assert "checksum" in metadata
        assert len(metadata["checksum"]) == 64

    def test_save_metadata_has_size_bytes(self):
        data = {"key": "value"}
        self.storage.save_backup("id1", data)
        meta_path = self.storage._get_metadata_path("id1", "full")
        metadata = json.loads(meta_path.read_text())
        assert metadata["size_bytes"] > 0

    def test_save_incremental_type(self):
        data = {"key": "value", "backup_type": "incremental"}
        self.storage.save_backup("id2", data)
        path = self.storage._get_backup_path("id2", "incremental")
        assert path.exists()

    def test_save_differential_type(self):
        data = {"key": "value", "backup_type": "differential"}
        self.storage.save_backup("id3", data)
        path = self.storage._get_backup_path("id3", "differential")
        assert path.exists()

    def test_save_default_type_is_full(self):
        data = {"key": "value"}
        self.storage.save_backup("id4", data)
        path = self.storage._get_backup_path("id4", "full")
        assert path.exists()

    def test_save_metadata_has_backup_type(self):
        data = {"key": "value", "backup_type": "incremental"}
        self.storage.save_backup("id5", data)
        meta_path = self.storage._get_metadata_path("id5", "incremental")
        metadata = json.loads(meta_path.read_text())
        assert metadata["backup_type"] == "incremental"

    def test_save_metadata_includes_table_count(self):
        data = {"key": "v", "metadata": {"table_count": 5, "total_rows": 100}}
        self.storage.save_backup("id6", data)
        meta_path = self.storage._get_metadata_path("id6", "full")
        metadata = json.loads(meta_path.read_text())
        assert metadata["table_count"] == 5
        assert metadata["total_rows"] == 100

    def test_save_with_created_at(self):
        data = {"key": "v", "created_at": "2026-01-01T00:00:00"}
        self.storage.save_backup("id7", data)
        meta_path = self.storage._get_metadata_path("id7", "full")
        metadata = json.loads(meta_path.read_text())
        assert metadata["created_at"] == "2026-01-01T00:00:00"

    def test_save_with_strategy(self):
        data = {"key": "v", "strategy": "daily"}
        self.storage.save_backup("id8", data)
        meta_path = self.storage._get_metadata_path("id8", "full")
        metadata = json.loads(meta_path.read_text())
        assert metadata["strategy"] == "daily"


# ---------------------------------------------------------------------------
# LocalStorage.get_backup
# ---------------------------------------------------------------------------


class TestLocalStorageGetBackup:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_get_roundtrip(self):
        data = {"name": "test", "values": [1, 2, 3]}
        self.storage.save_backup("rt1", data)
        result = self.storage.get_backup("rt1")
        assert result == data

    def test_get_incremental_roundtrip(self):
        data = {"name": "incr", "backup_type": "incremental"}
        self.storage.save_backup("rt2", data)
        result = self.storage.get_backup("rt2")
        assert result == data

    def test_get_differential_roundtrip(self):
        data = {"name": "diff", "backup_type": "differential"}
        self.storage.save_backup("rt3", data)
        result = self.storage.get_backup("rt3")
        assert result == data

    def test_get_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self.storage.get_backup("nonexistent")

    def test_get_large_backup(self):
        data = {"rows": [{"id": i, "name": f"row_{i}"} for i in range(500)]}
        self.storage.save_backup("large1", data)
        result = self.storage.get_backup("large1")
        assert len(result["rows"]) == 500


# ---------------------------------------------------------------------------
# LocalStorage.delete_backup
# ---------------------------------------------------------------------------


class TestLocalStorageDeleteBackup:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_delete_returns_true(self):
        self.storage.save_backup("del1", {"key": "v"})
        assert self.storage.delete_backup("del1") is True

    def test_delete_removes_backup_file(self):
        self.storage.save_backup("del2", {"key": "v"})
        self.storage.delete_backup("del2")
        path = self.storage._get_backup_path("del2", "full")
        assert not path.exists()

    def test_delete_removes_metadata_file(self):
        self.storage.save_backup("del3", {"key": "v"})
        self.storage.delete_backup("del3")
        meta_path = self.storage._get_metadata_path("del3", "full")
        assert not meta_path.exists()

    def test_delete_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self.storage.delete_backup("nonexistent")

    def test_delete_incremental(self):
        data = {"key": "v", "backup_type": "incremental"}
        self.storage.save_backup("del4", data)
        self.storage.delete_backup("del4")
        path = self.storage._get_backup_path("del4", "incremental")
        assert not path.exists()

    def test_delete_then_get_raises(self):
        self.storage.save_backup("del5", {"key": "v"})
        self.storage.delete_backup("del5")
        with pytest.raises(ValueError, match="not found"):
            self.storage.get_backup("del5")


# ---------------------------------------------------------------------------
# LocalStorage.list_backups
# ---------------------------------------------------------------------------


class TestLocalStorageListBackups:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_list_empty(self):
        result = self.storage.list_backups()
        assert result == []

    def test_list_one_backup(self):
        self.storage.save_backup("list1", {"key": "v"})
        result = self.storage.list_backups()
        assert len(result) == 1
        assert result[0]["backup_id"] == "list1"

    def test_list_multiple(self):
        for i in range(3):
            self.storage.save_backup(
                f"list_{i}", {"key": "v", "created_at": f"2026-01-0{i + 1}"}
            )
        result = self.storage.list_backups()
        assert len(result) == 3

    def test_list_sorted_by_created_at_desc(self):
        self.storage.save_backup("old", {"key": "v", "created_at": "2026-01-01"})
        self.storage.save_backup("new", {"key": "v", "created_at": "2026-01-10"})
        result = self.storage.list_backups()
        assert result[0]["backup_id"] == "new"
        assert result[1]["backup_id"] == "old"

    def test_list_filter_by_type(self):
        self.storage.save_backup("full1", {"key": "v"})
        self.storage.save_backup("incr1", {"key": "v", "backup_type": "incremental"})
        result = self.storage.list_backups(backup_type="incremental")
        assert len(result) == 1
        assert result[0]["backup_id"] == "incr1"

    def test_list_filter_full_only(self):
        self.storage.save_backup("full1", {"key": "v"})
        self.storage.save_backup("incr1", {"key": "v", "backup_type": "incremental"})
        result = self.storage.list_backups(backup_type="full")
        assert len(result) == 1
        assert result[0]["backup_id"] == "full1"

    def test_list_respects_limit(self):
        for i in range(5):
            self.storage.save_backup(
                f"lim_{i}", {"key": "v", "created_at": f"2026-01-{i + 1:02d}"}
            )
        result = self.storage.list_backups(limit=3)
        assert len(result) == 3

    def test_list_limit_returns_newest_first(self):
        for i in range(5):
            self.storage.save_backup(
                f"lim_{i}", {"key": "v", "created_at": f"2026-01-{i + 1:02d}"}
            )
        result = self.storage.list_backups(limit=2)
        assert result[0]["backup_id"] == "lim_4"
        assert result[1]["backup_id"] == "lim_3"

    def test_list_all_types(self):
        self.storage.save_backup("f1", {"key": "v"})
        self.storage.save_backup("i1", {"key": "v", "backup_type": "incremental"})
        self.storage.save_backup("d1", {"key": "v", "backup_type": "differential"})
        result = self.storage.list_backups()
        assert len(result) == 3

    def test_list_nonexistent_type_returns_empty(self):
        self.storage.save_backup("f1", {"key": "v"})
        result = self.storage.list_backups(backup_type="incremental")
        assert result == []


# ---------------------------------------------------------------------------
# LocalStorage.verify_backup
# ---------------------------------------------------------------------------


class TestLocalStorageVerifyBackup:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_verify_valid_backup(self):
        self.storage.save_backup("v1", {"key": "value"})
        assert self.storage.verify_backup("v1") is True

    def test_verify_incremental(self):
        self.storage.save_backup("v2", {"key": "v", "backup_type": "incremental"})
        assert self.storage.verify_backup("v2") is True

    def test_verify_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self.storage.verify_backup("nonexistent")

    def test_verify_corrupted_backup_returns_false(self):
        """Tamper with backup data after saving to trigger checksum mismatch."""
        self.storage.save_backup("v3", {"key": "value"})
        path = self.storage._get_backup_path("v3", "full")
        # Overwrite with different compressed data
        path.write_bytes(gzip.compress(b'{"tampered": true}'))
        assert self.storage.verify_backup("v3") is False

    def test_verify_missing_checksum_in_metadata_returns_false(self):
        """Metadata without checksum field should return False."""
        self.storage.save_backup("v4", {"key": "value"})
        meta_path = self.storage._get_metadata_path("v4", "full")
        metadata = json.loads(meta_path.read_text())
        del metadata["checksum"]
        meta_path.write_text(json.dumps(metadata))
        assert self.storage.verify_backup("v4") is False

    def test_verify_after_save_get_cycle(self):
        """Verify still works after data has been read (non-destructive)."""
        data = {"key": "value"}
        self.storage.save_backup("v5", data)
        self.storage.get_backup("v5")
        assert self.storage.verify_backup("v5") is True


# ---------------------------------------------------------------------------
# LocalStorage.get_backup_size
# ---------------------------------------------------------------------------


class TestLocalStorageGetBackupSize:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_size_is_positive(self):
        self.storage.save_backup("sz1", {"key": "value"})
        size = self.storage.get_backup_size("sz1")
        assert size > 0

    def test_size_is_int(self):
        self.storage.save_backup("sz2", {"key": "value"})
        size = self.storage.get_backup_size("sz2")
        assert isinstance(size, int)

    def test_size_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self.storage.get_backup_size("nonexistent")

    def test_larger_data_has_larger_size(self):
        small = {"x": "a"}
        large = {"x": "a" * 10000}
        self.storage.save_backup("small", small)
        self.storage.save_backup("large", large)
        assert self.storage.get_backup_size("large") > self.storage.get_backup_size(
            "small"
        )

    def test_size_matches_file_stat(self):
        data = {"key": "value"}
        self.storage.save_backup("sz3", data)
        path = self.storage._get_backup_path("sz3", "full")
        assert self.storage.get_backup_size("sz3") == path.stat().st_size

    def test_size_incremental_type(self):
        data = {"key": "v", "backup_type": "incremental"}
        self.storage.save_backup("sz4", data)
        size = self.storage.get_backup_size("sz4")
        assert size > 0


# ---------------------------------------------------------------------------
# End-to-end lifecycle
# ---------------------------------------------------------------------------


class TestLocalStorageLifecycle:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_full_lifecycle(self):
        """save -> list -> verify -> get -> size -> delete -> list empty"""
        data = {
            "tables": {"users": [1, 2, 3]},
            "metadata": {"table_count": 1, "total_rows": 3},
        }
        bid = "lifecycle1"

        # Save
        assert self.storage.save_backup(bid, data) is True

        # List
        backups = self.storage.list_backups()
        assert len(backups) == 1
        assert backups[0]["backup_id"] == bid

        # Verify
        assert self.storage.verify_backup(bid) is True

        # Get
        restored = self.storage.get_backup(bid)
        assert restored == data

        # Size
        size = self.storage.get_backup_size(bid)
        assert size > 0

        # Delete
        assert self.storage.delete_backup(bid) is True

        # List empty
        assert self.storage.list_backups() == []

    def test_multiple_types_lifecycle(self):
        """Save full, incremental, differential, list all, filter each."""
        self.storage.save_backup("f1", {"key": "full"})
        self.storage.save_backup("i1", {"key": "incr", "backup_type": "incremental"})
        self.storage.save_backup("d1", {"key": "diff", "backup_type": "differential"})

        # All
        assert len(self.storage.list_backups()) == 3

        # Each type
        assert len(self.storage.list_backups(backup_type="full")) == 1
        assert len(self.storage.list_backups(backup_type="incremental")) == 1
        assert len(self.storage.list_backups(backup_type="differential")) == 1

        # Verify each
        assert self.storage.verify_backup("f1") is True
        assert self.storage.verify_backup("i1") is True
        assert self.storage.verify_backup("d1") is True

    def test_overwrite_existing_backup(self):
        """Saving with same ID overwrites the backup."""
        self.storage.save_backup("ow1", {"version": 1})
        self.storage.save_backup("ow1", {"version": 2})
        result = self.storage.get_backup("ow1")
        assert result["version"] == 2

    def test_many_backups(self):
        """Save and list many backups."""
        for i in range(20):
            self.storage.save_backup(
                f"many_{i}", {"idx": i, "created_at": f"2026-01-{i + 1:02d}"}
            )
        all_backups = self.storage.list_backups()
        assert len(all_backups) == 20
        # First should be newest
        assert all_backups[0]["backup_id"] == "many_19"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestLocalStorageEdgeCases:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = LocalStorage(backup_dir=self.tmpdir)

    def test_empty_backup_data(self):
        self.storage.save_backup("empty", {})
        result = self.storage.get_backup("empty")
        assert result == {}

    def test_unicode_in_data(self):
        data = {"name": "Dr. Müller-Schröder", "notes": "日本語テスト"}
        self.storage.save_backup("unicode", data)
        result = self.storage.get_backup("unicode")
        assert result["name"] == "Dr. Müller-Schröder"
        assert result["notes"] == "日本語テスト"

    def test_special_chars_in_values(self):
        data = {"html": "has <tags> & \"quotes\" 'single'"}
        self.storage.save_backup("special", data)
        result = self.storage.get_backup("special")
        assert result == data

    def test_deeply_nested_data(self):
        data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        self.storage.save_backup("deep", data)
        result = self.storage.get_backup("deep")
        assert result["a"]["b"]["c"]["d"]["e"] == "deep"

    def test_list_with_no_metadata_still_works(self):
        """If backup file exists without metadata, list should skip it gracefully."""
        # Create a bare backup file with no metadata
        path = self.storage._get_backup_path("bare", "full")
        path.write_bytes(gzip.compress(b'{"bare": true}'))
        # list_backups only reads .meta.json files, so this should return empty
        result = self.storage.list_backups()
        assert result == []

    def test_null_values_in_data(self):
        data = {"field": None, "nested": {"also_null": None}}
        self.storage.save_backup("nulls", data)
        result = self.storage.get_backup("nulls")
        assert result["field"] is None
        assert result["nested"]["also_null"] is None

    def test_numeric_keys_in_data(self):
        """JSON converts int keys to strings."""
        data = {"numbers": {1: "one", 2: "two"}}
        self.storage.save_backup("numkeys", data)
        result = self.storage.get_backup("numkeys")
        assert result["numbers"]["1"] == "one"

    def test_large_backup_roundtrip(self):
        data = {"rows": [{"id": i, "data": f"row_{i}" * 100} for i in range(1000)]}
        self.storage.save_backup("large", data)
        result = self.storage.get_backup("large")
        assert len(result["rows"]) == 1000
        assert result["rows"][999]["id"] == 999
