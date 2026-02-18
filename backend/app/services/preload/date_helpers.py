"""Pure date helper functions for preload service."""

from __future__ import annotations

from datetime import date, timedelta


def is_last_wednesday(current_date: date, block_end: date) -> bool:
    """Return True if the date is the last Wednesday of the block."""
    if current_date.weekday() != 2:
        return False
    return current_date + timedelta(days=7) > block_end


def pattern_week_number(current_date: date, block_start: date) -> int:
    """1-indexed week number within a block."""
    return ((current_date - block_start).days // 7) + 1


def pattern_day_of_week(current_date: date) -> int:
    """Convert Python weekday (Mon=0..Sun=6) to weekly_pattern (Sun=0..Sat=6)."""
    return (current_date.weekday() + 1) % 7
