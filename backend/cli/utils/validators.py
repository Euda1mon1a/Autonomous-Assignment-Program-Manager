"""
Input validation utilities for CLI.

Provides validators for:
- Email addresses
- Dates
- UUIDs
- File paths
- URLs
- Military data constraints
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return bool(pattern.match(email))


def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        format: Expected date format

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def validate_file_path(path_str: str, must_exist: bool = False) -> bool:
    """
    Validate file path.

    Args:
        path_str: Path string to validate
        must_exist: If True, path must exist

    Returns:
        True if valid, False otherwise
    """
    try:
        path = Path(path_str)
        if must_exist and not path.exists():
            return False
        return True
    except (ValueError, OSError):
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def validate_pgy_level(level: str) -> bool:
    """
    Validate PGY (Post-Graduate Year) level.

    Args:
        level: PGY level (e.g., "PGY-1", "PGY-2", "PGY-3")

    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r"^PGY-[1-3]$")
    return bool(pattern.match(level))


def validate_role(role: str) -> bool:
    """
    Validate user role.

    Args:
        role: User role

    Returns:
        True if valid, False otherwise
    """
    valid_roles = [
        "ADMIN",
        "COORDINATOR",
        "FACULTY",
        "RESIDENT",
        "CLINICAL_STAFF",
        "RN",
        "LPN",
        "MSA",
    ]
    return role.upper() in valid_roles


def validate_block_number(block: int) -> bool:
    """
    Validate block number (1-12 for academic year).

    Args:
        block: Block number

    Returns:
        True if valid, False otherwise
    """
    return 1 <= block <= 12


def validate_hours(hours: float) -> bool:
    """
    Validate work hours (reasonable range).

    Args:
        hours: Number of hours

    Returns:
        True if valid, False otherwise
    """
    return 0 <= hours <= 168  # Max hours in a week


def validate_percentage(value: float) -> bool:
    """
    Validate percentage value (0-100).

    Args:
        value: Percentage value

    Returns:
        True if valid, False otherwise
    """
    return 0 <= value <= 100


def validate_military_rank(rank: str) -> bool:
    """
    Validate military rank.

    Args:
        rank: Military rank

    Returns:
        True if valid, False otherwise
    """
    valid_ranks = [
        # Enlisted
        "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
        # Officers
        "O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8", "O9", "O10",
        # Warrant Officers
        "W1", "W2", "W3", "W4", "W5",
    ]
    return rank.upper() in valid_ranks


def sanitize_name_for_demo(name: str) -> str:
    """
    Sanitize real name to generic identifier for demo/test data.

    Per OPSEC/PERSEC requirements, never use real names in demos.

    Args:
        name: Real name

    Returns:
        Sanitized identifier (e.g., "PGY1-01", "FAC-PD")
    """
    # This is a placeholder - real implementation would use a mapping
    # or generate consistent identifiers
    return f"USER-{hash(name) % 1000:03d}"


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, field: str, message: str):
        """
        Initialize validation error.

        Args:
            field: Field that failed validation
            message: Error message
        """
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
