"""File upload security and validation module."""
import re
from pathlib import Path
from typing import Optional

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class FileSecurityError(Exception):
    """Exception raised for file security violations."""
    pass


# Allowed file extensions for Excel uploads
ALLOWED_EXCEL_EXTENSIONS = {'.xlsx', '.xls'}

# MIME types for Excel files
ALLOWED_EXCEL_MIMETYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel'  # .xls
}

# Extension to expected MIME type mapping
EXTENSION_TO_MIMETYPE = {
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
}

# Maximum upload size in MB
MAX_UPLOAD_SIZE_MB = 10


class FileValidationError(Exception):
    """Exception raised when file validation fails."""
    pass


def _detect_mime_type(file_content: bytes) -> Optional[str]:
    """
    Detect MIME type from file content using magic bytes.

    Args:
        file_content: Raw bytes of the file

    Returns:
        Detected MIME type string, or None if detection fails
    """
    if not MAGIC_AVAILABLE:
        return None

    try:
        mime = magic.Magic(mime=True)
        detected_type = mime.from_buffer(file_content)
        return detected_type
    except Exception:
        # If magic detection fails, return None
        return None


def validate_excel_upload(
    file_content: bytes,
    filename: str,
    content_type: Optional[str] = None
) -> None:
    """
    Validate uploaded Excel file for type, size, and content.

    Performs comprehensive security checks:
    - Validates file size against MAX_UPLOAD_SIZE_MB limit
    - Checks file extension is in ALLOWED_EXCEL_EXTENSIONS
    - Verifies Content-Type header matches expected MIME type
    - Detects actual MIME type from magic bytes (if python-magic available)
    - Cross-validates extension, Content-Type header, and detected MIME type
    - Verifies magic bytes to prevent content-type spoofing

    Args:
        file_content: Raw bytes of the uploaded file
        filename: Original filename from the upload
        content_type: Content-Type header from the upload (optional)

    Raises:
        FileValidationError: If any validation check fails
    """
    # Check size
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise FileValidationError(
            f"File too large: {size_mb:.2f}MB (max: {MAX_UPLOAD_SIZE_MB}MB)"
        )

    # Check minimum size (empty files are suspicious)
    if len(file_content) < 100:
        raise FileValidationError("File is too small to be a valid Excel file")

    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXCEL_EXTENSIONS:
        raise FileValidationError(
            f"Invalid file type '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXCEL_EXTENSIONS)}"
        )

    # Get expected MIME type based on extension
    expected_mime = EXTENSION_TO_MIMETYPE.get(ext)

    # Validate Content-Type header if provided
    if content_type:
        # Normalize content type (remove parameters like charset)
        normalized_content_type = content_type.split(';')[0].strip().lower()

        # Check if Content-Type matches expected MIME type
        if normalized_content_type not in ALLOWED_EXCEL_MIMETYPES:
            raise FileValidationError(
                f"Invalid Content-Type header '{content_type}'. "
                f"Expected one of: {', '.join(ALLOWED_EXCEL_MIMETYPES)}"
            )

        # Verify Content-Type matches the file extension
        if expected_mime and normalized_content_type != expected_mime:
            raise FileValidationError(
                f"Content-Type '{normalized_content_type}' does not match "
                f"file extension '{ext}' (expected '{expected_mime}')"
            )

    # Detect MIME type from magic bytes
    detected_mime = _detect_mime_type(file_content)
    if detected_mime:
        # Normalize detected MIME type
        detected_mime = detected_mime.lower().strip()

        # For XLSX files, python-magic may return 'application/zip'
        # since XLSX is a ZIP archive format
        if ext == '.xlsx' and detected_mime == 'application/zip':
            # This is acceptable - XLSX files are ZIP archives
            # We'll verify the PK signature below
            pass
        elif detected_mime not in ALLOWED_EXCEL_MIMETYPES:
            raise FileValidationError(
                f"Detected file type '{detected_mime}' does not match "
                f"allowed Excel MIME types. File may be corrupted or spoofed."
            )

        # Verify detected MIME type matches extension
        if expected_mime and detected_mime != expected_mime:
            # Special case: XLSX as ZIP is acceptable
            if not (ext == '.xlsx' and detected_mime == 'application/zip'):
                raise FileValidationError(
                    f"Detected MIME type '{detected_mime}' does not match "
                    f"file extension '{ext}' (expected '{expected_mime}')"
                )

    # Check magic bytes for XLSX (ZIP archive with PK header)
    # XLSX files are essentially ZIP archives, so they start with PK\x03\x04
    if ext == '.xlsx':
        if not file_content.startswith(b'PK\x03\x04'):
            raise FileValidationError(
                "Invalid Excel file format: file does not match XLSX signature"
            )

    # Check magic bytes for XLS (OLE2/CFB format)
    # XLS files start with D0 CF 11 E0 A1 B1 1A E1
    elif ext == '.xls':
        xls_signature = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
        if not file_content.startswith(xls_signature):
            raise FileValidationError(
                "Invalid Excel file format: file does not match XLS signature"
            )


def sanitize_upload_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent path traversal and other attacks.

    Security measures:
    - Strips any directory path components
    - Removes dangerous characters
    - Prevents hidden files
    - Ensures filename is not empty after sanitization

    Args:
        filename: Original filename from upload

    Returns:
        Sanitized filename safe for storage

    Raises:
        FileValidationError: If filename becomes empty after sanitization
    """
    # Get just the filename without any path components
    safe_name = Path(filename).name

    # Remove dangerous characters - only allow alphanumeric, dots, underscores, and hyphens
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_name)

    # Prevent hidden files (files starting with .)
    if safe_name.startswith('.'):
        safe_name = '_' + safe_name[1:]

    # Ensure we still have a filename after sanitization
    if not safe_name or safe_name in {'.', '..'}:
        raise FileValidationError("Invalid filename after sanitization")

    # Limit filename length to prevent issues
    if len(safe_name) > 255:
        # Keep extension but truncate the name part
        name_part = Path(safe_name).stem[:240]
        ext_part = Path(safe_name).suffix
        safe_name = name_part + ext_part

    return safe_name


def validate_and_sanitize_upload(
    file_content: bytes,
    filename: str,
    content_type: Optional[str] = None
) -> tuple[bytes, str]:
    """
    Perform both validation and sanitization on an uploaded file.

    Convenience function that combines validation and filename sanitization.

    Args:
        file_content: Raw bytes of the uploaded file
        filename: Original filename from the upload
        content_type: Content-Type header from the upload (optional)

    Returns:
        Tuple of (validated_content, sanitized_filename)

    Raises:
        FileValidationError: If validation or sanitization fails
    """
    # Validate the file content
    validate_excel_upload(file_content, filename, content_type)

    # Sanitize the filename
    safe_filename = sanitize_upload_filename(filename)

    return file_content, safe_filename


# Path Traversal Prevention Functions

def validate_backup_id(backup_id: str) -> str:
    """
    Validate backup ID to prevent path traversal attacks.

    Only allows alphanumeric characters, hyphens, and underscores.
    Rejects path separators and ".." sequences.

    Args:
        backup_id: The backup ID to validate

    Returns:
        The validated backup ID

    Raises:
        FileSecurityError: If the backup ID contains invalid characters
    """
    if not backup_id:
        raise FileSecurityError("Backup ID cannot be empty")

    # Only allow alphanumeric, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', backup_id):
        raise FileSecurityError(
            f"Invalid backup ID '{backup_id}': only alphanumeric characters, "
            "hyphens, and underscores are allowed"
        )

    # Additional check for path traversal patterns
    if '..' in backup_id or '/' in backup_id or '\\' in backup_id:
        raise FileSecurityError(
            f"Invalid backup ID '{backup_id}': path separators and '..' are not allowed"
        )

    return backup_id


def validate_file_path(file_path: Path, allowed_base: Path) -> Path:
    """
    Validate that a file path is within the allowed base directory.

    Resolves the path and verifies it's within the allowed base directory,
    preventing path traversal attacks.

    Args:
        file_path: The file path to validate
        allowed_base: The allowed base directory

    Returns:
        The resolved file path

    Raises:
        FileSecurityError: If the path is outside the allowed base directory
    """
    try:
        # Resolve both paths to absolute paths
        resolved_base = allowed_base.resolve()
        resolved_path = file_path.resolve()

        # Check if the resolved path is within the base directory
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise FileSecurityError(
                f"Path '{file_path}' is outside allowed directory '{allowed_base}'"
            )

        return resolved_path
    except (OSError, RuntimeError) as e:
        raise FileSecurityError(f"Error validating path '{file_path}': {e}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing path components and dangerous characters.

    Removes directory separators and path traversal sequences.

    Args:
        filename: The filename to sanitize

    Returns:
        The sanitized filename

    Raises:
        FileSecurityError: If the filename is empty after sanitization
    """
    if not filename:
        raise FileSecurityError("Filename cannot be empty")

    # Remove any path separators (both Unix and Windows)
    sanitized = filename.replace('/', '').replace('\\', '')

    # Remove path traversal patterns
    sanitized = sanitized.replace('..', '')

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    if not sanitized:
        raise FileSecurityError(
            f"Filename '{filename}' is invalid after sanitization"
        )

    return sanitized
