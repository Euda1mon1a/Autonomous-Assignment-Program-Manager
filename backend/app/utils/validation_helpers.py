"""Validation helper functions for input sanitization and verification."""

import re
from datetime import date
from uuid import UUID


def validate_uuid(value: str) -> bool:
    """
    Validate if a string is a valid UUID.

    Args:
        value: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_email_format(value: str) -> bool:
    """
    Validate if a string matches email format.

    Uses a simple but robust regex pattern. Does not verify domain existence.

    Args:
        value: Email string to validate

    Returns:
        True if valid email format, False otherwise
    """
    if not value or not isinstance(value, str):
        return False

    # Simple but robust email regex
    # Allows: letters, numbers, dots, hyphens, underscores before @
    # Requires @ symbol
    # Allows: letters, numbers, dots, hyphens after @
    # Requires at least one dot after @
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that a date range is logical (start <= end).

    Args:
        start_date: Range start date
        end_date: Range end date

    Returns:
        True if start_date <= end_date, False otherwise
    """
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return False
    return start_date <= end_date


def sanitize_string(value: str, max_length: int | None = None) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.

    Removes:
    - Leading/trailing whitespace
    - Control characters
    - Null bytes

    Args:
        value: String to sanitize
        max_length: Optional maximum length to truncate to

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""

    # Remove control characters and null bytes
    sanitized = "".join(char for char in value if char.isprintable())

    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def normalize_name(value: str) -> str:
    """
    Normalize a person's name for consistent storage.

    - Capitalizes first letter of each word
    - Removes extra whitespace
    - Handles common prefixes (Dr., Mr., Mrs., etc.)

    Args:
        value: Name string to normalize

    Returns:
        Normalized name string
    """
    if not isinstance(value, str):
        return ""

    # Remove extra whitespace and strip
    normalized = " ".join(value.split())

    # Title case (capitalizes first letter of each word)
    normalized = normalized.title()

    # Handle common prefixes that should be capitalized differently
    prefixes = ["Mc", "Mac", "O'"]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            # Capitalize letter after prefix
            if len(normalized) > len(prefix):
                normalized = prefix + normalized[len(prefix)].upper() + normalized[len(prefix) + 1:]

    return normalized
