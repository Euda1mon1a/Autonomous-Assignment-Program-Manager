"""
Data formatting utilities for CLI output.
"""

from datetime import datetime, date
from typing import Any


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date(d: date) -> str:
    """Format date for display."""
    if d is None:
        return "-"
    return d.strftime("%Y-%m-%d")


def format_bool(value: bool) -> str:
    """Format boolean for display."""
    return "✓" if value else "✗"


def format_percentage(value: float) -> str:
    """Format percentage for display."""
    if value is None:
        return "-"
    return f"{value:.1f}%"


def format_hours(hours: float) -> str:
    """Format hours for display."""
    if hours is None:
        return "-"
    return f"{hours:.1f}h"


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text to max length."""
    if text is None:
        return "-"
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_list(items: list, max_items: int = 5) -> str:
    """Format list for display."""
    if not items:
        return "-"
    if len(items) <= max_items:
        return ", ".join(str(item) for item in items)
    shown = ", ".join(str(item) for item in items[:max_items])
    return f"{shown}, ... (+{len(items) - max_items} more)"
