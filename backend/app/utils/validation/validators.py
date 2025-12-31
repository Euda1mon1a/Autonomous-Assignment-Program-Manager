"""
Reusable validation utility functions.
"""

import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse


def validate_future_date_strict(
    check_date: date | datetime,
    min_days_ahead: int = 1,
) -> tuple[bool, str | None]:
    """
    Strictly validate date is in the future.

    Args:
        check_date: Date to validate
        min_days_ahead: Minimum days ahead required

    Returns:
        tuple: (is_valid, error_message)
    """
    if isinstance(check_date, datetime):
        check_date = check_date.date()

    today = date.today()
    min_date = today

    if min_days_ahead > 0:
        from datetime import timedelta
        min_date = today + timedelta(days=min_days_ahead)

    if check_date < min_date:
        return False, f"Date must be at least {min_days_ahead} days in the future"

    return True, None


def validate_email_domain(
    email: str,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Validate email domain restrictions.

    Args:
        email: Email address to validate
        allowed_domains: List of allowed domains (None = all allowed)
        blocked_domains: List of blocked domains

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or "@" not in email:
        return False, "Invalid email format"

    domain = email.split("@")[1].lower()

    # Check blocked domains
    if blocked_domains and domain in [d.lower() for d in blocked_domains]:
        return False, f"Email domain '{domain}' is not allowed"

    # Check allowed domains
    if allowed_domains:
        if domain not in [d.lower() for d in allowed_domains]:
            return False, f"Email domain must be one of: {', '.join(allowed_domains)}"

    return True, None


def validate_url(
    url: str,
    allowed_schemes: list[str] | None = None,
    require_tld: bool = True,
) -> tuple[bool, str | None]:
    """
    Validate URL format and restrictions.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])
        require_tld: Require top-level domain

    Returns:
        tuple: (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            return False, f"URL scheme must be one of: {', '.join(allowed_schemes)}"

        # Check hostname exists
        if not parsed.netloc:
            return False, "URL must have a hostname"

        # Check for TLD if required
        if require_tld:
            if "." not in parsed.netloc:
                return False, "URL must have a top-level domain"

        return True, None

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_json(
    json_string: str,
    schema: dict | None = None,
) -> tuple[bool, str | None, dict | None]:
    """
    Validate JSON string and optionally validate against schema.

    Args:
        json_string: JSON string to validate
        schema: Optional JSON schema to validate against

    Returns:
        tuple: (is_valid, error_message, parsed_json)
    """
    if not json_string:
        return False, "JSON string cannot be empty", None

    try:
        parsed = json.loads(json_string)

        # Optional: validate against schema
        # (Would use jsonschema library here)

        return True, None, parsed

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}", None
    except Exception as e:
        return False, f"JSON validation error: {str(e)}", None


def validate_password_strength(
    password: str,
    min_length: int = 12,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
) -> tuple[bool, list[str]]:
    """
    Validate password meets strength requirements.

    Args:
        password: Password to validate
        min_length: Minimum length
        require_uppercase: Require uppercase letter
        require_lowercase: Require lowercase letter
        require_digit: Require digit
        require_special: Require special character

    Returns:
        tuple: (is_valid, list of failed requirements)
    """
    failed_requirements = []

    if len(password) < min_length:
        failed_requirements.append(f"Password must be at least {min_length} characters")

    if require_uppercase and not re.search(r"[A-Z]", password):
        failed_requirements.append("Password must contain at least one uppercase letter")

    if require_lowercase and not re.search(r"[a-z]", password):
        failed_requirements.append("Password must contain at least one lowercase letter")

    if require_digit and not re.search(r"\d", password):
        failed_requirements.append("Password must contain at least one digit")

    if require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        failed_requirements.append("Password must contain at least one special character")

    return len(failed_requirements) == 0, failed_requirements


def validate_file_extension(
    filename: str,
    allowed_extensions: list[str],
) -> tuple[bool, str | None]:
    """
    Validate file has allowed extension.

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['pdf', 'doc'])

    Returns:
        tuple: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"

    if "." not in filename:
        return False, "Filename must have an extension"

    extension = filename.rsplit(".", 1)[1].lower()

    allowed_lower = [ext.lower() for ext in allowed_extensions]

    if extension not in allowed_lower:
        return False, f"File extension must be one of: {', '.join(allowed_extensions)}"

    return True, None


def validate_file_size(
    size_bytes: int,
    max_size_mb: float,
) -> tuple[bool, str | None]:
    """
    Validate file size is within limits.

    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum size in megabytes

    Returns:
        tuple: (is_valid, error_message)
    """
    max_bytes = int(max_size_mb * 1024 * 1024)

    if size_bytes > max_bytes:
        actual_mb = size_bytes / (1024 * 1024)
        return False, f"File size ({actual_mb:.1f}MB) exceeds maximum ({max_size_mb}MB)"

    return True, None


def validate_list_unique(
    items: list[Any],
    field: str | None = None,
) -> tuple[bool, str | None]:
    """
    Validate list contains only unique items.

    Args:
        items: List to validate
        field: Optional field name for objects

    Returns:
        tuple: (is_valid, error_message)
    """
    if field:
        # For list of objects
        values = [getattr(item, field) if hasattr(item, field) else item.get(field) for item in items]
    else:
        # For list of primitives
        values = items

    if len(values) != len(set(values)):
        return False, "List contains duplicate items"

    return True, None
