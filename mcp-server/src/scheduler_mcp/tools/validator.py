"""
Input validation utilities for MCP tools.

This module provides common validation functions for tool inputs.
"""

import re
from datetime import date
from typing import Any

from .base import ValidationError


def validate_date_string(value: str, field_name: str = "date") -> str:
    """
    Validate a date string in YYYY-MM-DD format.

    Args:
        value: Date string to validate
        field_name: Name of field for error messages

    Returns:
        Validated date string

    Raises:
        ValidationError: If date is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            details={"field": field_name, "type": type(value).__name__},
        )

    # Check format
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise ValidationError(
            f"{field_name} must be in YYYY-MM-DD format",
            details={"field": field_name, "value": value},
        )

    # Parse to validate
    try:
        date.fromisoformat(value)
    except ValueError as e:
        raise ValidationError(
            f"{field_name} is not a valid date: {e}",
            details={"field": field_name, "value": value},
        )

    return value


def validate_date_range(
    start_date: str, end_date: str, max_days: int | None = None
) -> tuple[str, str]:
    """
    Validate a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_days: Optional maximum range in days

    Returns:
        Tuple of (start_date, end_date)

    Raises:
        ValidationError: If range is invalid
    """
    # Validate individual dates
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    # Parse dates
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    # Check order
    if start > end:
        raise ValidationError(
            "start_date must be before or equal to end_date",
            details={"start_date": start_date, "end_date": end_date},
        )

    # Check max range
    if max_days is not None:
        days = (end - start).days
        if days > max_days:
            raise ValidationError(
                f"Date range exceeds maximum of {max_days} days",
                details={
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days,
                    "max_days": max_days,
                },
            )

    return start_date, end_date


def validate_person_id(value: str, field_name: str = "person_id") -> str:
    """
    Validate a person ID.

    Args:
        value: Person ID to validate
        field_name: Name of field for error messages

    Returns:
        Validated person ID

    Raises:
        ValidationError: If person ID is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            details={"field": field_name, "type": type(value).__name__},
        )

    if not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            details={"field": field_name},
        )

    # Check for dangerous characters
    dangerous_chars = ["'", '"', ";", "&", "|", "$", "`", "<", ">", "\n", "\r"]
    for char in dangerous_chars:
        if char in value:
            raise ValidationError(
                f"{field_name} contains invalid character: {char}",
                details={"field": field_name, "char": char},
            )

    # Must be UUID or alphanumeric with hyphens/underscores
    if not re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        value,
    ) and not re.match(r"^[a-zA-Z0-9_-]{1,64}$", value):
        raise ValidationError(
            f"{field_name} must be a valid UUID or alphanumeric identifier",
            details={"field": field_name, "value": value},
        )

    return value


def validate_schedule_id(value: str) -> str:
    """
    Validate a schedule ID.

    Args:
        value: Schedule ID to validate

    Returns:
        Validated schedule ID

    Raises:
        ValidationError: If schedule ID is invalid
    """
    return validate_person_id(value, "schedule_id")


def validate_positive_int(
    value: Any, field_name: str = "value", max_value: int | None = None
) -> int:
    """
    Validate a positive integer.

    Args:
        value: Value to validate
        field_name: Name of field for error messages
        max_value: Optional maximum value

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be an integer",
                details={"field": field_name, "type": type(value).__name__},
            )

    if value < 0:
        raise ValidationError(
            f"{field_name} must be non-negative",
            details={"field": field_name, "value": value},
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{field_name} cannot exceed {max_value}",
            details={"field": field_name, "value": value, "max": max_value},
        )

    return value


def validate_float_range(
    value: Any,
    field_name: str = "value",
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """
    Validate a float within a range.

    Args:
        value: Value to validate
        field_name: Name of field for error messages
        min_value: Optional minimum value (inclusive)
        max_value: Optional maximum value (inclusive)

    Returns:
        Validated float

    Raises:
        ValidationError: If value is invalid or out of range
    """
    if not isinstance(value, (int, float)):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a number",
                details={"field": field_name, "type": type(value).__name__},
            )

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{field_name} must be at least {min_value}",
            details={"field": field_name, "value": value, "min": min_value},
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{field_name} cannot exceed {max_value}",
            details={"field": field_name, "value": value, "max": max_value},
        )

    return float(value)


def validate_algorithm(value: str) -> str:
    """
    Validate a scheduling algorithm name.

    Args:
        value: Algorithm name to validate

    Returns:
        Validated algorithm name

    Raises:
        ValidationError: If algorithm is invalid
    """
    valid_algorithms = ["greedy", "cp_sat", "pulp", "hybrid"]

    if value not in valid_algorithms:
        raise ValidationError(
            f"Invalid algorithm: {value}",
            details={"value": value, "valid": valid_algorithms},
        )

    return value


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string for safe logging and display.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If string is too long
    """
    if not isinstance(value, str):
        value = str(value)

    # Truncate if too long
    if len(value) > max_length:
        raise ValidationError(
            f"String exceeds maximum length of {max_length}",
            details={"length": len(value), "max": max_length},
        )

    # Remove null bytes and control characters
    value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

    return value
