"""
Data transformation utility functions.

Transforms data between formats:
- Case transformations
- Date format transformations
- Data type transformations
"""

import re
from datetime import date, datetime
from typing import Any


def transform_to_title_case(text: str) -> str:
    """
    Transform text to title case.

    Args:
        text: Text to transform

    Returns:
        str: Title cased text
    """
    if not text:
        return ""

    # Use normalize_name for proper title casing
    from .normalizers import normalize_name

    return normalize_name(text)


def transform_to_snake_case(text: str) -> str:
    """
    Transform text to snake_case.

    Args:
        text: Text to transform

    Returns:
        str: Snake cased text
    """
    if not text:
        return ""

    # Replace spaces and hyphens with underscores
    text = re.sub(r"[\s-]+", "_", text)

    # Insert underscores before capitals (camelCase -> camel_Case)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)

    # Lowercase
    return text.lower()


def transform_to_camel_case(text: str) -> str:
    """
    Transform text to camelCase.

    Args:
        text: Text to transform

    Returns:
        str: Camel cased text
    """
    if not text:
        return ""

    # Split on spaces, hyphens, underscores
    parts = re.split(r"[\s_-]+", text)

    # First part lowercase, rest title case
    if parts:
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    return ""


def transform_to_pascal_case(text: str) -> str:
    """
    Transform text to PascalCase.

    Args:
        text: Text to transform

    Returns:
        str: Pascal cased text
    """
    if not text:
        return ""

    # Split on spaces, hyphens, underscores
    parts = re.split(r"[\s_-]+", text)

    # All parts title case
    return "".join(p.capitalize() for p in parts)


def transform_date_format(
    date_value: date | datetime | str,
    output_format: str = "%Y-%m-%d",
    input_format: str | None = None,
) -> str:
    """
    Transform date to specified format.

    Args:
        date_value: Date to transform (date, datetime, or string)
        output_format: Desired output format
        input_format: Input format (if date_value is string)

    Returns:
        str: Formatted date string
    """
    if isinstance(date_value, str):
        if input_format is None:
            raise ValueError("input_format required when date_value is string")
        dt = datetime.strptime(date_value, input_format)
    elif isinstance(date_value, datetime):
        dt = date_value
    elif isinstance(date_value, date):
        dt = datetime.combine(date_value, datetime.min.time())
    else:
        raise ValueError(f"Unsupported date type: {type(date_value)}")

    return dt.strftime(output_format)


def transform_to_iso_date(date_value: Any) -> str:
    """
    Transform date to ISO format (YYYY-MM-DD).

    Args:
        date_value: Date to transform

    Returns:
        str: ISO formatted date
    """
    return transform_date_format(date_value, output_format="%Y-%m-%d")


def transform_to_display_date(date_value: Any) -> str:
    """
    Transform date to display format (e.g., "Jan 15, 2024").

    Args:
        date_value: Date to transform

    Returns:
        str: Display formatted date
    """
    return transform_date_format(date_value, output_format="%b %d, %Y")


def transform_session_to_time_range(session: str) -> tuple[str, str]:
    """
    Transform session (AM/PM) to time range.

    Args:
        session: Session identifier ("AM" or "PM")

    Returns:
        tuple: (start_time, end_time) as strings

    Raises:
        ValueError: If session is not "AM" or "PM"
    """
    session_upper = session.upper()

    if session_upper == "AM":
        return "08:00", "12:00"
    elif session_upper == "PM":
        return "13:00", "17:00"
    else:
        raise ValueError(f"Invalid session: '{session}'. Must be 'AM' or 'PM'")


def transform_hours_to_blocks(hours: float) -> int:
    """
    Transform hours to number of blocks.

    Assumes each block is 4 hours (half-day).

    Args:
        hours: Hours to transform

    Returns:
        int: Number of blocks
    """
    return int(hours / 4)


def transform_blocks_to_hours(blocks: int) -> float:
    """
    Transform number of blocks to hours.

    Assumes each block is 4 hours (half-day).

    Args:
        blocks: Number of blocks

    Returns:
        float: Hours
    """
    return blocks * 4.0


def transform_to_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Transform decimal to percentage string.

    Args:
        value: Value to transform (0.0-1.0)
        decimal_places: Number of decimal places

    Returns:
        str: Percentage string (e.g., "75.5%")
    """
    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"


def transform_dict_keys(
    data: dict,
    transform_func: callable = transform_to_snake_case,
) -> dict:
    """
    Transform all dictionary keys using transform function.

    Args:
        data: Dictionary to transform
        transform_func: Function to transform keys

    Returns:
        dict: Dictionary with transformed keys
    """
    if not isinstance(data, dict):
        return data

    return {transform_func(k): v for k, v in data.items()}


def transform_list_to_dict(
    items: list,
    key_field: str,
) -> dict:
    """
    Transform list to dictionary using specified key field.

    Args:
        items: List of items (dicts or objects)
        key_field: Field to use as key

    Returns:
        dict: Dictionary keyed by field value
    """
    result = {}

    for item in items:
        if isinstance(item, dict):
            key = item.get(key_field)
        else:
            key = getattr(item, key_field, None)

        if key is not None:
            result[key] = item

    return result
