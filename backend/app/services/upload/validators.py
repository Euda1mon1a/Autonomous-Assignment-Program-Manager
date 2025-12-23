"""File upload validators.

Provides comprehensive validation for uploaded files including:
- File size validation
- File type validation (MIME type and extension)
- Magic byte verification
- Virus scanning integration
- Filename sanitization
"""

import hashlib
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

import magic

logger = logging.getLogger(__name__)


class UploadValidationError(Exception):
    """Exception raised when file upload validation fails."""

    pass


class FileValidator:
    """
    Comprehensive file validator for uploads.

    Validates files based on:
    - Size limits
    - Allowed MIME types
    - File extensions
    - Magic byte verification
    - Content scanning (optional virus scan)
    """

    # Default file type configurations
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
    }

    ALLOWED_DOCUMENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
    }

    ALLOWED_EXTENSIONS_MAP = {
        "image/jpeg": {".jpg", ".jpeg"},
        "image/png": {".png"},
        "image/gif": {".gif"},
        "image/webp": {".webp"},
        "image/svg+xml": {".svg"},
        "application/pdf": {".pdf"},
        "application/msword": {".doc"},
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
            ".docx"
        },
        "application/vnd.ms-excel": {".xls"},
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {".xlsx"},
        "text/csv": {".csv"},
    }

    # Magic byte signatures for common file types
    MAGIC_SIGNATURES = {
        "image/jpeg": [b"\xff\xd8\xff"],
        "image/png": [b"\x89PNG\r\n\x1a\n"],
        "image/gif": [b"GIF87a", b"GIF89a"],
        "application/pdf": [b"%PDF"],
        "application/zip": [
            b"PK\x03\x04",
            b"PK\x05\x06",
        ],  # DOCX, XLSX are ZIP archives
    }

    def __init__(
        self,
        max_size_mb: int = 50,
        allowed_mime_types: set[str] | None = None,
        enable_virus_scan: bool = False,
    ):
        """
        Initialize file validator.

        Args:
            max_size_mb: Maximum file size in megabytes
            allowed_mime_types: Set of allowed MIME types (None = allow all common types)
            enable_virus_scan: Enable virus scanning integration
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_mime_types = allowed_mime_types or (
            self.ALLOWED_IMAGE_TYPES | self.ALLOWED_DOCUMENT_TYPES
        )
        self.enable_virus_scan = enable_virus_scan

    def validate_file(
        self,
        file_content: bytes,
        filename: str,
        expected_mime_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Validate uploaded file content and metadata.

        Args:
            file_content: Raw bytes of the uploaded file
            filename: Original filename from upload
            expected_mime_type: Expected MIME type (optional, for stricter validation)

        Returns:
            dict: Validation result with metadata
                - valid: bool
                - mime_type: str
                - extension: str
                - size_bytes: int
                - checksum: str (SHA-256)
                - sanitized_filename: str
                - errors: list[str]

        Raises:
            UploadValidationError: If validation fails
        """
        errors = []

        # Validate file size
        size_bytes = len(file_content)
        if size_bytes == 0:
            raise UploadValidationError("File is empty")
        if size_bytes > self.max_size_bytes:
            raise UploadValidationError(
                f"File too large: {size_bytes / (1024 * 1024):.2f}MB "
                f"(max: {self.max_size_bytes / (1024 * 1024):.0f}MB)"
            )

        # Sanitize filename
        sanitized_filename = self._sanitize_filename(filename)
        extension = Path(sanitized_filename).suffix.lower()

        # Detect MIME type from content
        detected_mime = self._detect_mime_type(file_content)

        # Validate MIME type
        if detected_mime not in self.allowed_mime_types:
            raise UploadValidationError(
                f"File type '{detected_mime}' not allowed. "
                f"Allowed types: {', '.join(sorted(self.allowed_mime_types))}"
            )

        # Validate extension matches MIME type
        if detected_mime in self.ALLOWED_EXTENSIONS_MAP:
            allowed_extensions = self.ALLOWED_EXTENSIONS_MAP[detected_mime]
            if extension not in allowed_extensions:
                raise UploadValidationError(
                    f"File extension '{extension}' does not match MIME type '{detected_mime}'. "
                    f"Expected: {', '.join(allowed_extensions)}"
                )

        # Verify magic bytes
        if not self._verify_magic_bytes(file_content, detected_mime):
            errors.append(
                f"File content does not match expected format for '{detected_mime}'"
            )

        # Check expected MIME type if provided
        if expected_mime_type and detected_mime != expected_mime_type:
            raise UploadValidationError(
                f"MIME type mismatch: expected '{expected_mime_type}', "
                f"detected '{detected_mime}'"
            )

        # Virus scan (if enabled)
        if self.enable_virus_scan:
            scan_result = self._scan_for_viruses(file_content, sanitized_filename)
            if not scan_result["clean"]:
                raise UploadValidationError(
                    f"Virus detected: {scan_result.get('threat', 'Unknown threat')}"
                )

        # Calculate checksum
        checksum = hashlib.sha256(file_content).hexdigest()

        return {
            "valid": len(errors) == 0,
            "mime_type": detected_mime,
            "extension": extension,
            "size_bytes": size_bytes,
            "checksum": checksum,
            "sanitized_filename": sanitized_filename,
            "errors": errors,
        }

    def _detect_mime_type(self, file_content: bytes) -> str:
        """
        Detect MIME type from file content using python-magic.

        Args:
            file_content: Raw file bytes

        Returns:
            str: Detected MIME type
        """
        try:
            mime = magic.Magic(mime=True)
            detected = mime.from_buffer(file_content)
            return detected
        except Exception as e:
            logger.warning(f"Failed to detect MIME type with magic: {e}")
            # Fallback to basic detection
            return "application/octet-stream"

    def _verify_magic_bytes(self, file_content: bytes, mime_type: str) -> bool:
        """
        Verify file magic bytes match expected signature.

        Args:
            file_content: Raw file bytes
            mime_type: Expected MIME type

        Returns:
            bool: True if magic bytes match or no signature defined
        """
        # Special handling for Office documents (ZIP-based)
        if mime_type in {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }:
            # These are ZIP archives
            zip_signatures = self.MAGIC_SIGNATURES.get("application/zip", [])
            return any(file_content.startswith(sig) for sig in zip_signatures)

        signatures = self.MAGIC_SIGNATURES.get(mime_type, [])
        if not signatures:
            # No signature defined for this type
            return True

        return any(file_content.startswith(sig) for sig in signatures)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename

        Raises:
            UploadValidationError: If filename is invalid
        """
        if not filename:
            raise UploadValidationError("Filename cannot be empty")

        # Get just the filename without path components
        safe_name = Path(filename).name

        # Remove dangerous characters - only allow alphanumeric, dots, underscores, hyphens
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", safe_name)

        # Prevent hidden files (files starting with .)
        if safe_name.startswith("."):
            safe_name = "_" + safe_name[1:]

        # Ensure we still have a filename
        if not safe_name or safe_name in {".", ".."}:
            raise UploadValidationError("Invalid filename after sanitization")

        # Limit filename length
        if len(safe_name) > 255:
            # Keep extension but truncate the name part
            name_part = Path(safe_name).stem[:240]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part

        return safe_name

    def _scan_for_viruses(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """
        Scan file for viruses using integrated scanner.

        Note: This is a placeholder for virus scanning integration.
        In production, integrate with ClamAV or similar.

        Args:
            file_content: Raw file bytes
            filename: Sanitized filename

        Returns:
            dict: Scan result with 'clean' bool and optional 'threat' string
        """
        # Placeholder implementation
        # In production, integrate with ClamAV or cloud-based scanner
        logger.info(f"Virus scan requested for {filename} ({len(file_content)} bytes)")

        # Example integration points:
        # 1. ClamAV: Use pyclamd library
        # 2. VirusTotal: Use virustotal-python library
        # 3. Cloud scanner: AWS S3 + Lambda with scanner

        return {"clean": True, "threat": None}

    @staticmethod
    def get_file_category(mime_type: str) -> str:
        """
        Categorize file by MIME type.

        Args:
            mime_type: File MIME type

        Returns:
            str: Category ('image', 'document', 'spreadsheet', 'other')
        """
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf" or mime_type in {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }:
            return "document"
        elif mime_type in {
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv",
        }:
            return "spreadsheet"
        else:
            return "other"
