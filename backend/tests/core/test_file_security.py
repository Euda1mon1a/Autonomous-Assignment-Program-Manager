"""Tests for file upload security and validation (pure logic, no DB)."""

from pathlib import Path

import pytest

from app.core.file_security import (
    ALLOWED_EXCEL_EXTENSIONS,
    ALLOWED_EXCEL_MIMETYPES,
    EXTENSION_TO_MIMETYPE,
    MAGIC_AVAILABLE,
    MAX_UPLOAD_SIZE_MB,
    FileSecurityError,
    FileValidationError,
    sanitize_filename,
    sanitize_upload_filename,
    validate_and_sanitize_upload,
    validate_backup_id,
    validate_excel_upload,
    validate_file_path,
)


# -- Constants ---------------------------------------------------------------


class TestConstants:
    def test_allowed_extensions(self):
        assert ".xlsx" in ALLOWED_EXCEL_EXTENSIONS
        assert ".xls" in ALLOWED_EXCEL_EXTENSIONS

    def test_allowed_mimetypes(self):
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in ALLOWED_EXCEL_MIMETYPES
        )
        assert "application/vnd.ms-excel" in ALLOWED_EXCEL_MIMETYPES

    def test_extension_to_mimetype(self):
        assert ".xlsx" in EXTENSION_TO_MIMETYPE
        assert ".xls" in EXTENSION_TO_MIMETYPE

    def test_max_upload_size(self):
        assert MAX_UPLOAD_SIZE_MB > 0


# -- Exception hierarchy -----------------------------------------------------


class TestExceptions:
    def test_file_security_error_is_exception(self):
        assert issubclass(FileSecurityError, Exception)

    def test_file_validation_error_is_exception(self):
        assert issubclass(FileValidationError, Exception)

    def test_file_security_error_message(self):
        err = FileSecurityError("test message")
        assert str(err) == "test message"

    def test_file_validation_error_message(self):
        err = FileValidationError("validation failed")
        assert str(err) == "validation failed"


# -- validate_excel_upload: size checks --------------------------------------


# XLSX magic bytes: PK\x03\x04 followed by enough padding to pass min size
VALID_XLSX_CONTENT = b"PK\x03\x04" + b"\x00" * 200
# XLS magic bytes
VALID_XLS_CONTENT = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 200
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLS_MIME = "application/vnd.ms-excel"


class TestValidateExcelUploadSize:
    def test_too_large_raises(self):
        # Create content exceeding MAX_UPLOAD_SIZE_MB
        large_content = b"PK\x03\x04" + b"\x00" * (MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        with pytest.raises(FileValidationError, match="File too large"):
            validate_excel_upload(large_content, "test.xlsx", XLSX_MIME)

    def test_too_small_raises(self):
        tiny_content = b"PK\x03\x04" + b"\x00" * 10  # Only 14 bytes
        with pytest.raises(FileValidationError, match="too small"):
            validate_excel_upload(tiny_content, "test.xlsx", XLSX_MIME)


# -- validate_excel_upload: extension checks ---------------------------------


class TestValidateExcelUploadExtension:
    def test_xlsx_extension_ok(self):
        # Should not raise
        validate_excel_upload(VALID_XLSX_CONTENT, "report.xlsx", XLSX_MIME)

    def test_xls_extension_ok(self):
        validate_excel_upload(VALID_XLS_CONTENT, "report.xls", XLS_MIME)

    def test_csv_extension_rejected(self):
        with pytest.raises(FileValidationError, match="Invalid file type"):
            validate_excel_upload(VALID_XLSX_CONTENT, "data.csv", XLSX_MIME)

    def test_txt_extension_rejected(self):
        with pytest.raises(FileValidationError, match="Invalid file type"):
            validate_excel_upload(VALID_XLSX_CONTENT, "file.txt")

    def test_no_extension_rejected(self):
        with pytest.raises(FileValidationError, match="Invalid file type"):
            validate_excel_upload(VALID_XLSX_CONTENT, "noextension")

    def test_uppercase_extension_ok(self):
        validate_excel_upload(VALID_XLSX_CONTENT, "REPORT.XLSX", XLSX_MIME)


# -- validate_excel_upload: content type checks ------------------------------


class TestValidateExcelUploadContentType:
    def test_no_content_type_ok(self):
        # Should not raise when content_type is None
        validate_excel_upload(VALID_XLSX_CONTENT, "test.xlsx")

    def test_valid_xlsx_content_type(self):
        validate_excel_upload(VALID_XLSX_CONTENT, "test.xlsx", XLSX_MIME)

    def test_valid_xls_content_type(self):
        validate_excel_upload(VALID_XLS_CONTENT, "test.xls", XLS_MIME)

    def test_invalid_content_type_rejected(self):
        with pytest.raises(FileValidationError, match="Invalid Content-Type"):
            validate_excel_upload(VALID_XLSX_CONTENT, "test.xlsx", "text/plain")

    def test_content_type_with_charset_ok(self):
        # Content-Type with charset parameter should still work
        validate_excel_upload(
            VALID_XLSX_CONTENT,
            "test.xlsx",
            f"{XLSX_MIME}; charset=utf-8",
        )

    def test_content_type_extension_mismatch_rejected(self):
        # XLS content type for .xlsx file
        with pytest.raises(FileValidationError, match="does not match"):
            validate_excel_upload(VALID_XLSX_CONTENT, "test.xlsx", XLS_MIME)


# -- validate_excel_upload: magic bytes checks --------------------------------


class TestValidateExcelUploadMagicBytes:
    def test_valid_xlsx_magic_bytes(self):
        validate_excel_upload(VALID_XLSX_CONTENT, "test.xlsx", XLSX_MIME)

    def test_valid_xls_magic_bytes(self):
        validate_excel_upload(VALID_XLS_CONTENT, "test.xls", XLS_MIME)

    def test_invalid_xlsx_magic_bytes(self):
        bad_content = b"\x00" * 200  # Not PK header
        with pytest.raises(FileValidationError, match="XLSX signature"):
            validate_excel_upload(bad_content, "test.xlsx", XLSX_MIME)

    def test_invalid_xls_magic_bytes(self):
        bad_content = b"\x00" * 200  # Not OLE2 header
        with pytest.raises(FileValidationError, match="XLS signature"):
            validate_excel_upload(bad_content, "test.xls", XLS_MIME)


# -- sanitize_upload_filename ------------------------------------------------


class TestSanitizeUploadFilename:
    def test_normal_filename(self):
        assert sanitize_upload_filename("report.xlsx") == "report.xlsx"

    def test_strips_path_components(self):
        assert sanitize_upload_filename("/etc/passwd") == "passwd"

    def test_strips_windows_path(self):
        result = sanitize_upload_filename("C:\\Users\\data\\report.xlsx")
        assert "/" not in result
        assert "\\" not in result
        assert "report.xlsx" in result

    def test_removes_dangerous_characters(self):
        result = sanitize_upload_filename("file name <script>.xlsx")
        assert "<" not in result
        assert ">" not in result
        assert " " not in result

    def test_prevents_hidden_files(self):
        result = sanitize_upload_filename(".hidden.xlsx")
        assert not result.startswith(".")
        assert result.startswith("_")

    def test_empty_filename_raises(self):
        with pytest.raises(FileValidationError, match="Invalid filename"):
            sanitize_upload_filename("")

    def test_dots_only_raises(self):
        with pytest.raises(FileValidationError, match="Invalid filename"):
            sanitize_upload_filename(".")

    def test_double_dots_sanitized(self):
        # ".." gets leading dot replaced with "_", yielding "_."
        result = sanitize_upload_filename("..")
        assert not result.startswith(".")
        assert ".." not in result

    def test_long_filename_truncated(self):
        long_name = "a" * 300 + ".xlsx"
        result = sanitize_upload_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".xlsx")

    def test_preserves_underscores_hyphens(self):
        assert sanitize_upload_filename("my_report-2024.xlsx") == "my_report-2024.xlsx"

    def test_special_chars_replaced_with_underscore(self):
        result = sanitize_upload_filename("file@#$%.xlsx")
        # Special chars should be replaced with _
        assert "@" not in result
        assert "#" not in result
        assert result.endswith(".xlsx")


# -- validate_and_sanitize_upload -------------------------------------------


class TestValidateAndSanitizeUpload:
    def test_returns_content_and_filename(self):
        content, filename = validate_and_sanitize_upload(
            VALID_XLSX_CONTENT, "report.xlsx", XLSX_MIME
        )
        assert content == VALID_XLSX_CONTENT
        assert filename == "report.xlsx"

    def test_sanitizes_filename(self):
        _, filename = validate_and_sanitize_upload(
            VALID_XLSX_CONTENT, "/etc/report.xlsx", XLSX_MIME
        )
        assert "/" not in filename
        assert filename == "report.xlsx"

    def test_validation_failure_raises(self):
        with pytest.raises(FileValidationError):
            validate_and_sanitize_upload(b"tiny", "test.xlsx", XLSX_MIME)


# -- validate_backup_id -----------------------------------------------------


class TestValidateBackupId:
    def test_valid_alphanumeric(self):
        assert validate_backup_id("abc123") == "abc123"

    def test_valid_with_hyphens(self):
        assert validate_backup_id("backup-2024-01-15") == "backup-2024-01-15"

    def test_valid_with_underscores(self):
        assert validate_backup_id("backup_latest") == "backup_latest"

    def test_empty_raises(self):
        with pytest.raises(FileSecurityError, match="cannot be empty"):
            validate_backup_id("")

    def test_path_traversal_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("../../../etc/passwd")

    def test_slash_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("path/to/backup")

    def test_backslash_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("path\\to\\backup")

    def test_dots_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("backup.tar.gz")

    def test_spaces_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("backup name")

    def test_special_chars_raises(self):
        with pytest.raises(FileSecurityError, match="only alphanumeric"):
            validate_backup_id("backup;rm -rf /")


# -- validate_file_path -----------------------------------------------------


class TestValidateFilePath:
    def test_valid_path_within_base(self, tmp_path):
        sub = tmp_path / "data"
        sub.mkdir()
        result = validate_file_path(sub / "file.txt", tmp_path)
        assert result.is_relative_to(tmp_path)

    def test_path_traversal_rejected(self, tmp_path):
        with pytest.raises(FileSecurityError, match="outside allowed"):
            validate_file_path(tmp_path / ".." / ".." / "etc" / "passwd", tmp_path)

    def test_exact_base_allowed(self, tmp_path):
        result = validate_file_path(tmp_path, tmp_path)
        assert result == tmp_path.resolve()

    def test_returns_resolved_path(self, tmp_path):
        result = validate_file_path(tmp_path / "data" / ".." / "file.txt", tmp_path)
        # Resolved path should not contain ".."
        assert ".." not in str(result)


# -- sanitize_filename -------------------------------------------------------


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_filename("report.xlsx") == "report.xlsx"

    def test_removes_slashes(self):
        assert sanitize_filename("path/to/file.txt") == "pathtofile.txt"

    def test_removes_backslashes(self):
        assert sanitize_filename("path\\to\\file.txt") == "pathtofile.txt"

    def test_removes_double_dots(self):
        assert sanitize_filename("../../etc/passwd") == "etcpasswd"

    def test_removes_null_bytes(self):
        assert sanitize_filename("file\x00.txt") == "file.txt"

    def test_empty_string_raises(self):
        with pytest.raises(FileSecurityError, match="cannot be empty"):
            sanitize_filename("")

    def test_only_slashes_raises(self):
        with pytest.raises(FileSecurityError, match="invalid after sanitization"):
            sanitize_filename("///")

    def test_only_dots_raises(self):
        with pytest.raises(FileSecurityError, match="invalid after sanitization"):
            sanitize_filename("..")

    def test_preserves_valid_chars(self):
        assert sanitize_filename("my-report_v2.xlsx") == "my-report_v2.xlsx"

    def test_combined_attacks(self):
        result = sanitize_filename("../../../\x00etc/passwd")
        assert "/" not in result
        assert "\\" not in result
        assert ".." not in result
        assert "\x00" not in result
