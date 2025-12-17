"""Tests for file security utilities."""
import pytest
from pathlib import Path
from app.core.file_security import (
    FileSecurityError,
    validate_backup_id,
    validate_file_path,
    sanitize_filename,
)


class TestValidateBackupId:
    """Tests for validate_backup_id function."""

    def test_valid_backup_id(self):
        """Test that valid backup IDs are accepted."""
        valid_ids = [
            "abc123",
            "backup-2024-01-01",
            "test_backup_123",
            "ABC-123-xyz",
            "12345678-1234-1234-1234-123456789012",  # UUID format
        ]
        for backup_id in valid_ids:
            result = validate_backup_id(backup_id)
            assert result == backup_id

    def test_empty_backup_id(self):
        """Test that empty backup ID is rejected."""
        with pytest.raises(FileSecurityError, match="cannot be empty"):
            validate_backup_id("")

    def test_backup_id_with_path_separator(self):
        """Test that backup IDs with path separators are rejected."""
        invalid_ids = [
            "../backup",
            "backup/file",
            "backup\\file",
            "../../etc/passwd",
        ]
        for backup_id in invalid_ids:
            with pytest.raises(FileSecurityError, match="path separators"):
                validate_backup_id(backup_id)

    def test_backup_id_with_special_chars(self):
        """Test that backup IDs with special characters are rejected."""
        invalid_ids = [
            "backup@123",
            "backup#123",
            "backup$123",
            "backup%123",
            "backup&123",
            "backup*123",
            "backup(123)",
            "backup[123]",
        ]
        for backup_id in invalid_ids:
            with pytest.raises(FileSecurityError, match="only alphanumeric"):
                validate_backup_id(backup_id)

    def test_backup_id_with_dot_dot(self):
        """Test that backup IDs with '..' are rejected."""
        with pytest.raises(FileSecurityError, match="'..' are not allowed"):
            validate_backup_id("backup..123")


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_path_within_base(self, tmp_path):
        """Test that valid paths within base directory are accepted."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        file_path = base_dir / "subdir" / "file.txt"
        result = validate_file_path(file_path, base_dir)
        assert result.is_relative_to(base_dir)

    def test_path_traversal_rejected(self, tmp_path):
        """Test that path traversal attempts are rejected."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Try to escape the base directory
        file_path = base_dir / ".." / ".." / "etc" / "passwd"
        with pytest.raises(FileSecurityError, match="outside allowed directory"):
            validate_file_path(file_path, base_dir)

    def test_absolute_path_outside_base(self, tmp_path):
        """Test that absolute paths outside base are rejected."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Absolute path outside base directory
        file_path = Path("/etc/passwd")
        with pytest.raises(FileSecurityError, match="outside allowed directory"):
            validate_file_path(file_path, base_dir)

    def test_symlink_escape_rejected(self, tmp_path):
        """Test that symlinks escaping base directory are rejected."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a target outside the base
        outside_target = tmp_path / "outside" / "target.txt"
        outside_target.parent.mkdir(parents=True)
        outside_target.write_text("secret")

        # Create symlink inside base pointing outside
        symlink_path = base_dir / "link"
        symlink_path.symlink_to(outside_target)

        # Should reject because resolved path is outside base
        with pytest.raises(FileSecurityError, match="outside allowed directory"):
            validate_file_path(symlink_path, base_dir)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_valid_filename(self):
        """Test that valid filenames are sanitized correctly."""
        assert sanitize_filename("file.txt") == "file.txt"
        assert sanitize_filename("my_file-123.csv") == "my_file-123.csv"

    def test_empty_filename(self):
        """Test that empty filename is rejected."""
        with pytest.raises(FileSecurityError, match="cannot be empty"):
            sanitize_filename("")

    def test_path_separators_removed(self):
        """Test that path separators are removed."""
        assert sanitize_filename("path/to/file.txt") == "pathtofile.txt"
        assert sanitize_filename("path\\to\\file.txt") == "pathtofile.txt"

    def test_dot_dot_removed(self):
        """Test that '..' is removed."""
        assert sanitize_filename("..file.txt") == "file.txt"
        assert sanitize_filename("file..txt") == "file.txt"

    def test_null_bytes_removed(self):
        """Test that null bytes are removed."""
        assert sanitize_filename("file\x00.txt") == "file.txt"

    def test_invalid_after_sanitization(self):
        """Test that filename invalid after sanitization is rejected."""
        with pytest.raises(FileSecurityError, match="invalid after sanitization"):
            sanitize_filename("../../")


class TestPathTraversalIntegration:
    """Integration tests simulating real attack scenarios."""

    def test_backup_id_path_traversal_attack(self, tmp_path):
        """Test that path traversal via backup_id is prevented."""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Attacker tries to access /etc/passwd via backup_id
        malicious_id = "../../etc/passwd"
        with pytest.raises(FileSecurityError):
            validate_backup_id(malicious_id)

    def test_csv_path_traversal_attack(self, tmp_path):
        """Test that path traversal via CSV file path is prevented."""
        csv_dir = tmp_path / "csv_files"
        csv_dir.mkdir()

        # Attacker tries to access sensitive file outside allowed directory
        malicious_path = csv_dir / ".." / ".." / "etc" / "passwd"
        with pytest.raises(FileSecurityError):
            validate_file_path(malicious_path, csv_dir)

    def test_windows_path_traversal_attack(self, tmp_path):
        """Test that Windows-style path traversal is prevented."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Windows-style path traversal
        malicious_path = base_dir / "..\\..\\" / "Windows" / "System32"
        with pytest.raises(FileSecurityError):
            validate_file_path(malicious_path, base_dir)
