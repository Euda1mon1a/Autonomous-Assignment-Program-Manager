"""
Input sanitization utilities.

Provides sanitization functions for:
- XSS prevention (HTML/JavaScript injection)
- SQL injection prevention
- Path traversal prevention
- Unicode normalization
- Command injection prevention
"""

import html
import re
import unicodedata
from pathlib import Path
from typing import Any


class SanitizationError(Exception):
    """Exception raised when input cannot be safely sanitized."""

    pass


def sanitize_html(text: str, allow_safe_tags: bool = False) -> str:
    """
    Sanitize HTML input to prevent XSS attacks.

    By default, escapes all HTML entities.
    Optionally allows safe tags (b, i, em, strong).

    Args:
        text: Text that may contain HTML
        allow_safe_tags: Allow safe formatting tags (default: False)

    Returns:
        str: Sanitized text with HTML escaped

    Examples:
        >>> sanitize_html("<script>alert('xss')</script>")
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
        >>> sanitize_html("Hello <b>World</b>", allow_safe_tags=True)
        'Hello <b>World</b>'
    """
    if not text:
        return text

    # Escape all HTML by default
    sanitized = html.escape(text)

    # If allowing safe tags, unescape only those
    if allow_safe_tags:
        safe_tags = ["b", "i", "em", "strong", "u"]
        for tag in safe_tags:
            sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
            sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

    return sanitized


def sanitize_sql_like_pattern(pattern: str) -> str:
    """
    Sanitize SQL LIKE pattern to prevent injection.

    Escapes special SQL LIKE characters: %, _, [, ]

    Args:
        pattern: LIKE pattern to sanitize

    Returns:
        str: Sanitized pattern safe for SQL LIKE

    Examples:
        >>> sanitize_sql_like_pattern("test%_data")
        'test\\\\%\\\\_data'
    """
    if not pattern:
        return pattern

    # Escape SQL LIKE wildcards and special characters
    sanitized = pattern.replace("\\", "\\\\")  # Escape backslash first
    sanitized = sanitized.replace("%", "\\%")
    sanitized = sanitized.replace("_", "\\_")
    sanitized = sanitized.replace("[", "\\[")
    sanitized = sanitized.replace("]", "\\]")

    return sanitized


def sanitize_path(path_str: str, allow_absolute: bool = False) -> str:
    """
    Sanitize file path to prevent path traversal attacks.

    Removes:
    - .. (parent directory references)
    - Leading / or \\ (absolute paths, unless allowed)
    - Null bytes
    - Control characters

    Args:
        path_str: Path string to sanitize
        allow_absolute: Allow absolute paths (default: False)

    Returns:
        str: Sanitized path

    Raises:
        SanitizationError: If path is unsafe and cannot be sanitized
    """
    if not path_str:
        raise SanitizationError("Path cannot be empty")

    # Remove null bytes
    sanitized = path_str.replace("\x00", "")

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\t\n")

    # Convert to Path for normalization
    try:
        path = Path(sanitized)
    except (ValueError, TypeError) as e:
        raise SanitizationError(f"Invalid path: {path_str}") from e

    # Check for path traversal
    if ".." in path.parts:
        raise SanitizationError(f"Path traversal detected (..): {path_str}")

    # Check for absolute path
    if path.is_absolute() and not allow_absolute:
        raise SanitizationError(f"Absolute paths not allowed: {path_str}")

    return str(path)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.

    Removes:
    - Path separators (/ and \\)
    - Parent directory references (..)
    - Null bytes
    - Control characters
    - Leading/trailing dots and spaces

    Args:
        filename: Filename to sanitize

    Returns:
        str: Safe filename

    Raises:
        SanitizationError: If filename becomes empty after sanitization
    """
    if not filename:
        raise SanitizationError("Filename cannot be empty")

    # Get just the filename (no path components)
    sanitized = Path(filename).name

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char == "\t")

    # Remove path traversal patterns
    sanitized = sanitized.replace("..", "")

    # Remove path separators
    sanitized = sanitized.replace("/", "_").replace("\\", "_")

    # Remove leading dots (hidden files)
    while sanitized.startswith("."):
        sanitized = sanitized[1:]

    # Remove leading/trailing spaces
    sanitized = sanitized.strip()

    # Only allow safe characters: alphanumeric, dots, underscores, hyphens, spaces
    sanitized = re.sub(r"[^a-zA-Z0-9._\-\s]", "_", sanitized)

    # Limit length
    if len(sanitized) > 255:
        # Keep extension, truncate name
        name = Path(sanitized).stem[:240]
        ext = Path(sanitized).suffix
        sanitized = name + ext

    if not sanitized:
        raise SanitizationError(f"Filename is empty after sanitization: {filename}")

    return sanitized


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """
    Normalize Unicode text to prevent unicode-based attacks.

    Unicode normalization forms:
    - NFC: Canonical composition (common for most text)
    - NFD: Canonical decomposition
    - NFKC: Compatibility composition (most restrictive, recommended)
    - NFKD: Compatibility decomposition

    Args:
        text: Text to normalize
        form: Normalization form (default: NFKC)

    Returns:
        str: Normalized Unicode text

    Examples:
        >>> normalize_unicode("café")  # é as single char vs e + combining accent
        'café'
    """
    if not text:
        return text

    # Normalize Unicode
    normalized = unicodedata.normalize(form, text)

    return normalized


def sanitize_email_input(email: str) -> str:
    """
    Sanitize email input for safe processing.

    Removes:
    - Leading/trailing whitespace
    - Control characters
    - Null bytes

    Normalizes:
    - Unicode
    - Converts to lowercase

    Args:
        email: Email address to sanitize

    Returns:
        str: Sanitized email

    Raises:
        SanitizationError: If email is empty after sanitization
    """
    if not email:
        raise SanitizationError("Email cannot be empty")

    # Trim whitespace
    sanitized = email.strip()

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char == "\t")

    # Normalize Unicode
    sanitized = normalize_unicode(sanitized)

    # Convert to lowercase (email local part can be case-sensitive,
    # but for safety and consistency, we normalize)
    sanitized = sanitized.lower()

    if not sanitized:
        raise SanitizationError(f"Email is empty after sanitization: {email}")

    return sanitized


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """
    Sanitize search query input.

    Prevents:
    - Excessively long queries (DoS)
    - SQL injection patterns
    - Command injection patterns
    - Script injection

    Args:
        query: Search query to sanitize
        max_length: Maximum query length (default: 200)

    Returns:
        str: Sanitized query

    Raises:
        SanitizationError: If query is unsafe
    """
    if not query:
        return ""

    # Trim whitespace
    sanitized = query.strip()

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Normalize Unicode
    sanitized = normalize_unicode(sanitized)

    # Check for SQL injection patterns
    sql_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(;.*(-{2}|\/\*))",  # SQL comments after semicolon
    ]

    for pattern in sql_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            raise SanitizationError("Search query contains suspicious SQL patterns")

    # Check for command injection patterns
    cmd_patterns = [
        r"[;&|`$()]",  # Shell metacharacters
        r"\$\{",  # Variable expansion
        r"\$\(",  # Command substitution
    ]

    for pattern in cmd_patterns:
        if re.search(pattern, sanitized):
            raise SanitizationError("Search query contains suspicious command patterns")

    return sanitized


def strip_dangerous_characters(text: str) -> str:
    """
    Strip potentially dangerous characters from text.

    Removes:
    - Null bytes
    - Most control characters (except tab, newline, carriage return)
    - Zero-width characters
    - RTL/LTR override characters

    Args:
        text: Text to clean

    Returns:
        str: Text with dangerous characters removed
    """
    if not text:
        return text

    # Remove null bytes
    cleaned = text.replace("\x00", "")

    # Remove most control characters (keep \t, \n, \r)
    cleaned = "".join(char for char in cleaned if ord(char) >= 32 or char in "\t\n\r")

    # Remove zero-width characters
    zero_width = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\ufeff",  # Zero-width no-break space
    ]
    for char in zero_width:
        cleaned = cleaned.replace(char, "")

    # Remove RTL/LTR override characters (can be used for spoofing)
    direction_chars = [
        "\u202a",  # Left-to-right embedding
        "\u202b",  # Right-to-left embedding
        "\u202c",  # Pop directional formatting
        "\u202d",  # Left-to-right override
        "\u202e",  # Right-to-left override
    ]
    for char in direction_chars:
        cleaned = cleaned.replace(char, "")

    return cleaned


def sanitize_json_input(data: Any) -> Any:
    """
    Recursively sanitize JSON input data.

    Sanitizes all string values in JSON structures (dicts, lists).
    Preserves structure but cleans string content.

    Args:
        data: JSON-like data structure

    Returns:
        Any: Sanitized data structure
    """
    if isinstance(data, str):
        return strip_dangerous_characters(normalize_unicode(data))

    elif isinstance(data, dict):
        return {
            sanitize_json_input(key): sanitize_json_input(value)
            for key, value in data.items()
        }

    elif isinstance(data, list):
        return [sanitize_json_input(item) for item in data]

    else:
        # Numbers, booleans, None - return as is
        return data


def validate_no_script_tags(text: str) -> str:
    """
    Validate that text contains no script tags.

    Args:
        text: Text to validate

    Returns:
        str: Original text if safe

    Raises:
        SanitizationError: If script tags detected
    """
    if not text:
        return text

    # Check for script tags (case-insensitive)
    if re.search(r"<script[^>]*>.*?</script>", text, re.IGNORECASE | re.DOTALL):
        raise SanitizationError("Script tags are not allowed")

    # Check for inline event handlers
    event_handlers = [
        "onclick",
        "onload",
        "onerror",
        "onmouseover",
        "onmouseout",
        "onkeydown",
        "onkeyup",
        "onfocus",
        "onblur",
        "onchange",
        "onsubmit",
    ]

    for handler in event_handlers:
        if re.search(rf"{handler}\s*=", text, re.IGNORECASE):
            raise SanitizationError(f"Inline event handler '{handler}' is not allowed")

    # Check for javascript: protocol
    if re.search(r"javascript:", text, re.IGNORECASE):
        raise SanitizationError("JavaScript protocol is not allowed")

    return text


def sanitize_identifier(identifier: str, max_length: int = 64) -> str:
    """
    Sanitize identifier (variable name, table name, etc.).

    Ensures identifier:
    - Starts with letter or underscore
    - Contains only alphanumeric and underscore
    - Not too long

    Args:
        identifier: Identifier to sanitize
        max_length: Maximum length (default: 64)

    Returns:
        str: Sanitized identifier

    Raises:
        SanitizationError: If identifier is invalid
    """
    if not identifier:
        raise SanitizationError("Identifier cannot be empty")

    # Trim whitespace
    sanitized = identifier.strip()

    # Check length
    if len(sanitized) > max_length:
        raise SanitizationError(
            f"Identifier too long: {len(sanitized)} chars (max: {max_length})"
        )

    # Must start with letter or underscore
    if not re.match(r"^[a-zA-Z_]", sanitized):
        raise SanitizationError("Identifier must start with letter or underscore")

    # Must contain only alphanumeric and underscore
    if not re.match(r"^[a-zA-Z0-9_]+$", sanitized):
        raise SanitizationError(
            "Identifier can only contain letters, numbers, and underscores"
        )

    return sanitized
