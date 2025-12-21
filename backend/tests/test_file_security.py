"""Tests for file security utilities."""
import pytest
from pathlib import Path
from app.core.file_security import (
    FileSecurityError,
    FileValidationError,
    validate_backup_id,
    validate_file_path,
    sanitize_filename,
    validate_excel_upload,
    ALLOWED_EXCEL_MIMETYPES,
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


class TestValidateExcelUpload:
    """Tests for validate_excel_upload function with MIME type validation."""

    def test_valid_xlsx_file(self):
        """Test that valid XLSX file with correct magic bytes passes validation."""
        # XLSX files start with PK\x03\x04 (ZIP signature)
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        # Should pass without content_type
        validate_excel_upload(valid_xlsx, "test.xlsx")

        # Should pass with correct content_type
        validate_excel_upload(
            valid_xlsx,
            "test.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_valid_xls_file(self):
        """Test that valid XLS file with correct magic bytes passes validation."""
        # XLS files start with D0 CF 11 E0 A1 B1 1A E1 (OLE2 signature)
        valid_xls = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1' + b'\x00' * 100

        # Should pass without content_type
        validate_excel_upload(valid_xls, "test.xls")

        # Should pass with correct content_type
        validate_excel_upload(
            valid_xls,
            "test.xls",
            "application/vnd.ms-excel"
        )

    def test_content_type_with_charset(self):
        """Test that content_type with charset parameter is normalized correctly."""
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        # Content-Type with charset should be accepted
        validate_excel_upload(
            valid_xlsx,
            "test.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"
        )

    def test_file_too_large(self):
        """Test that files exceeding size limit are rejected."""
        # Create 11 MB file (exceeds 10 MB limit)
        large_file = b'PK\x03\x04' + b'\x00' * (11 * 1024 * 1024)

        with pytest.raises(FileValidationError, match="File too large"):
            validate_excel_upload(large_file, "test.xlsx")

    def test_file_too_small(self):
        """Test that suspiciously small files are rejected."""
        tiny_file = b'PK\x03\x04'

        with pytest.raises(FileValidationError, match="too small"):
            validate_excel_upload(tiny_file, "test.xlsx")

    def test_invalid_extension(self):
        """Test that non-Excel extensions are rejected."""
        file_content = b'PK\x03\x04' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="Invalid file type"):
            validate_excel_upload(file_content, "test.pdf")

        with pytest.raises(FileValidationError, match="Invalid file type"):
            validate_excel_upload(file_content, "test.docx")

    def test_xlsx_wrong_magic_bytes(self):
        """Test that XLSX file with wrong magic bytes is rejected."""
        # XLSX with wrong signature
        invalid_xlsx = b'NOT_ZIP_FILE' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="does not match XLSX signature"):
            validate_excel_upload(invalid_xlsx, "test.xlsx")

    def test_xls_wrong_magic_bytes(self):
        """Test that XLS file with wrong magic bytes is rejected."""
        # XLS with wrong signature
        invalid_xls = b'NOT_OLE2_FILE' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="does not match XLS signature"):
            validate_excel_upload(invalid_xls, "test.xls")

    def test_content_type_mismatch_extension(self):
        """Test that Content-Type not matching extension is rejected."""
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        # XLSX file but XLS content type
        with pytest.raises(FileValidationError, match="does not match file extension"):
            validate_excel_upload(
                valid_xlsx,
                "test.xlsx",
                "application/vnd.ms-excel"  # XLS content type for XLSX file
            )

    def test_invalid_content_type(self):
        """Test that invalid Content-Type header is rejected."""
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="Invalid Content-Type header"):
            validate_excel_upload(valid_xlsx, "test.xlsx", "application/pdf")

        with pytest.raises(FileValidationError, match="Invalid Content-Type header"):
            validate_excel_upload(valid_xlsx, "test.xlsx", "text/plain")

    def test_extension_spoofing_attack(self):
        """Test that files with spoofed extensions are rejected."""
        # PDF file masquerading as XLSX
        pdf_file = b'%PDF-1.4' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="does not match XLSX signature"):
            validate_excel_upload(pdf_file, "malicious.xlsx")

    def test_content_type_spoofing_attack(self):
        """Test that Content-Type spoofing is detected."""
        # Text file with Excel extension and content-type
        text_file = b'This is a text file, not Excel' + b'\x00' * 100

        with pytest.raises(FileValidationError, match="does not match XLSX signature"):
            validate_excel_upload(
                text_file,
                "fake.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    def test_double_extension_attack(self):
        """Test that double extension attacks are handled."""
        # File with double extension
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        # Should use the last extension (.xlsx)
        validate_excel_upload(valid_xlsx, "document.pdf.xlsx")

    def test_case_insensitive_extension(self):
        """Test that extension checking is case-insensitive."""
        valid_xlsx = b'PK\x03\x04' + b'\x00' * 100

        # Uppercase extension should work
        validate_excel_upload(valid_xlsx, "test.XLSX")
        validate_excel_upload(valid_xlsx, "test.XLS".replace("XLS", "xlsx"))

        # Mixed case should work
        validate_excel_upload(valid_xlsx, "test.XlSx")
