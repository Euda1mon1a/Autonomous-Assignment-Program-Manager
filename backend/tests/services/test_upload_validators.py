"""Tests for upload file validators.

Comprehensive test coverage for file validation logic including:
- File size validation
- MIME type detection and validation
- Filename sanitization and path traversal prevention
- Magic byte verification
- File category classification
"""

import pytest

from app.services.upload.validators import FileValidator, UploadValidationError


class TestFileValidatorInit:
    """Test FileValidator initialization."""

    def test_default_max_size(self):
        v = FileValidator()
        assert v.max_size_bytes == 50 * 1024 * 1024  # 50MB

    def test_custom_max_size(self):
        v = FileValidator(max_size_mb=10)
        assert v.max_size_bytes == 10 * 1024 * 1024

    def test_default_allowed_types_include_images_and_docs(self):
        v = FileValidator()
        assert "image/jpeg" in v.allowed_mime_types
        assert "image/png" in v.allowed_mime_types
        assert "application/pdf" in v.allowed_mime_types
        assert "text/csv" in v.allowed_mime_types

    def test_custom_allowed_types(self):
        v = FileValidator(allowed_mime_types={"image/png"})
        assert v.allowed_mime_types == {"image/png"}
        assert "image/jpeg" not in v.allowed_mime_types


class TestFilenameSanitization:
    """Test _sanitize_filename for security and correctness."""

    def setup_method(self):
        self.validator = FileValidator()

    def test_normal_filename_unchanged(self):
        result = self.validator._sanitize_filename("report.pdf")
        assert result == "report.pdf"

    def test_alphanumeric_with_hyphens_and_underscores(self):
        result = self.validator._sanitize_filename("my-file_v2.docx")
        assert result == "my-file_v2.docx"

    def test_path_traversal_stripped(self):
        result = self.validator._sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result
        assert result == "passwd"

    def test_windows_path_backslashes_sanitized(self):
        """On POSIX, backslashes are treated as filename chars and sanitized."""
        result = self.validator._sanitize_filename("C:\\Users\\data\\file.xlsx")
        # Backslashes become underscores, path is not traversed
        assert "\\" not in result
        assert result.endswith(".xlsx")

    def test_special_characters_replaced(self):
        result = self.validator._sanitize_filename("file (copy) [2].pdf")
        # Spaces and special chars replaced with underscores
        assert "(" not in result
        assert "[" not in result
        assert " " not in result
        assert result.endswith(".pdf")

    def test_hidden_file_prefix_removed(self):
        result = self.validator._sanitize_filename(".htaccess")
        assert not result.startswith(".")
        assert result == "_htaccess"

    def test_empty_filename_raises(self):
        with pytest.raises(UploadValidationError, match="cannot be empty"):
            self.validator._sanitize_filename("")

    def test_long_filename_truncated(self):
        long_name = "a" * 300 + ".pdf"
        result = self.validator._sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".pdf")

    def test_dot_only_raises(self):
        with pytest.raises(UploadValidationError, match="Invalid filename"):
            self.validator._sanitize_filename(".")


class TestFileSizeValidation:
    """Test file size boundary conditions."""

    def test_empty_file_raises(self):
        v = FileValidator()
        with pytest.raises(UploadValidationError, match="empty"):
            v.validate_file(b"", "test.txt")

    def test_file_at_exact_limit(self):
        v = FileValidator(max_size_mb=1)
        # Create a 1MB file with valid JPEG magic bytes
        content = b"\xff\xd8\xff" + b"\x00" * (1 * 1024 * 1024 - 3)
        # This should NOT raise for size, though it may fail MIME validation
        # depending on magic byte detection
        v = FileValidator(
            max_size_mb=1,
            allowed_mime_types={"image/jpeg", "application/octet-stream"},
        )
        result = v.validate_file(content, "test.jpg")
        assert result["valid"] is True

    def test_file_over_limit_raises(self):
        v = FileValidator(max_size_mb=1)
        content = b"\xff\xd8\xff" + b"\x00" * (1 * 1024 * 1024)
        with pytest.raises(UploadValidationError, match="too large"):
            v.validate_file(content, "test.jpg")


class TestMimeTypeDetection:
    """Test MIME type detection from file content."""

    def setup_method(self):
        self.validator = FileValidator()

    def test_jpeg_magic_bytes(self):
        content = b"\xff\xd8\xff" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "image/jpeg"

    def test_png_magic_bytes(self):
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "image/png"

    def test_gif87a_magic_bytes(self):
        content = b"GIF87a" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "image/gif"

    def test_gif89a_magic_bytes(self):
        content = b"GIF89a" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "image/gif"

    def test_pdf_magic_bytes(self):
        content = b"%PDF" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "application/pdf"

    def test_unknown_content_returns_octet_stream(self):
        content = b"\x01\x02\x03\x04" + b"\x00" * 100
        detected = self.validator._detect_mime_type(content)
        assert detected == "application/octet-stream"


class TestMagicByteVerification:
    """Test _verify_magic_bytes for content validation."""

    def setup_method(self):
        self.validator = FileValidator()

    def test_valid_jpeg_passes(self):
        content = b"\xff\xd8\xff" + b"\x00" * 100
        assert self.validator._verify_magic_bytes(content, "image/jpeg") is True

    def test_invalid_jpeg_fails(self):
        content = b"\x00\x00\x00" + b"\x00" * 100
        assert self.validator._verify_magic_bytes(content, "image/jpeg") is False

    def test_valid_png_passes(self):
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert self.validator._verify_magic_bytes(content, "image/png") is True

    def test_office_docx_zip_based(self):
        content = b"PK\x03\x04" + b"\x00" * 100
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert self.validator._verify_magic_bytes(content, mime) is True

    def test_office_xlsx_zip_based(self):
        content = b"PK\x03\x04" + b"\x00" * 100
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert self.validator._verify_magic_bytes(content, mime) is True

    def test_unknown_type_passes(self):
        """Types without defined signatures should pass verification."""
        content = b"\x00" * 100
        assert self.validator._verify_magic_bytes(content, "text/plain") is True


class TestValidateFile:
    """Test the main validate_file method end-to-end."""

    def setup_method(self):
        self.validator = FileValidator()

    def test_valid_jpeg(self):
        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = self.validator.validate_file(content, "photo.jpg")
        assert result["valid"] is True
        assert result["mime_type"] == "image/jpeg"
        assert result["extension"] == ".jpg"
        assert result["size_bytes"] == 103
        assert len(result["checksum"]) == 64  # SHA-256 hex digest
        assert result["sanitized_filename"] == "photo.jpg"

    def test_valid_png(self):
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = self.validator.validate_file(content, "image.png")
        assert result["valid"] is True
        assert result["mime_type"] == "image/png"
        assert result["extension"] == ".png"

    def test_valid_pdf(self):
        content = b"%PDF" + b"\x00" * 100
        result = self.validator.validate_file(content, "document.pdf")
        assert result["valid"] is True
        assert result["mime_type"] == "application/pdf"
        assert result["extension"] == ".pdf"

    def test_disallowed_mime_type_raises(self):
        v = FileValidator(allowed_mime_types={"image/png"})
        content = b"\xff\xd8\xff" + b"\x00" * 100
        with pytest.raises(UploadValidationError, match="not allowed"):
            v.validate_file(content, "photo.jpg")

    def test_extension_mismatch_raises(self):
        """JPEG content with .png extension should fail."""
        content = b"\xff\xd8\xff" + b"\x00" * 100
        with pytest.raises(UploadValidationError, match="does not match"):
            self.validator.validate_file(content, "photo.png")

    def test_expected_mime_type_mismatch_raises(self):
        content = b"\xff\xd8\xff" + b"\x00" * 100
        with pytest.raises(UploadValidationError, match="MIME type mismatch"):
            self.validator.validate_file(
                content, "photo.jpg", expected_mime_type="image/png"
            )

    def test_checksum_is_sha256(self):
        import hashlib

        content = b"\xff\xd8\xff" + b"\x00" * 100
        expected = hashlib.sha256(content).hexdigest()
        result = self.validator.validate_file(content, "photo.jpg")
        assert result["checksum"] == expected

    def test_filename_is_sanitized(self):
        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = self.validator.validate_file(content, "../../hack/photo.jpg")
        assert "/" not in result["sanitized_filename"]
        assert result["sanitized_filename"] == "photo.jpg"


class TestFileCategory:
    """Test get_file_category static method."""

    def test_image_category(self):
        assert FileValidator.get_file_category("image/jpeg") == "image"
        assert FileValidator.get_file_category("image/png") == "image"
        assert FileValidator.get_file_category("image/gif") == "image"

    def test_document_category(self):
        assert FileValidator.get_file_category("application/pdf") == "document"
        assert FileValidator.get_file_category("application/msword") == "document"
        docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert FileValidator.get_file_category(docx) == "document"

    def test_spreadsheet_category(self):
        assert (
            FileValidator.get_file_category("application/vnd.ms-excel") == "spreadsheet"
        )
        xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert FileValidator.get_file_category(xlsx) == "spreadsheet"
        assert FileValidator.get_file_category("text/csv") == "spreadsheet"

    def test_other_category(self):
        assert FileValidator.get_file_category("text/plain") == "other"
        assert FileValidator.get_file_category("application/octet-stream") == "other"


class TestVirusScan:
    """Test placeholder virus scan integration."""

    def test_placeholder_returns_clean(self):
        v = FileValidator()
        result = v._scan_for_viruses(b"content", "file.txt")
        assert result["clean"] is True
        assert result["threat"] is None
