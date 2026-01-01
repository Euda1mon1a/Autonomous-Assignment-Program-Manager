"""Date utility functions for schedule management."""

from datetime import date, timedelta
from typing import Tuple


def get_week_bounds(target_date: date) -> tuple[date, date]:
    """
    Get the start (Monday) and end (Sunday) dates of the week containing the target date.

    Args:
        target_date: The date to find week bounds for

    Returns:
        Tuple of (week_start, week_end) where start is Monday and end is Sunday
    """
    # weekday() returns 0 for Monday, 6 for Sunday
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_rolling_window_dates(target_date: date, weeks: int = 4) -> list[date]:
    """
    Get all dates in a rolling window for ACGME compliance calculations.

    Args:
        target_date: The end date of the window
        weeks: Number of weeks to look back (default: 4 for ACGME)

    Returns:
        List of dates in chronological order covering the window
    """
    start_date = target_date - timedelta(weeks=weeks)
    dates = []
    current = start_date
    while current <= target_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def is_weekend(target_date: date) -> bool:
    """
    Check if a date falls on a weekend (Saturday or Sunday).

    Args:
        target_date: The date to check

    Returns:
        True if the date is Saturday (5) or Sunday (6)
    """
    return target_date.weekday() in (5, 6)


def get_academic_year(target_date: date) -> int:
    """
    Get the academic year for a given date.

    Academic years start July 1st. For example:
    - 2024-06-30 -> 2023 (academic year 2023-2024)
    - 2024-07-01 -> 2024 (academic year 2024-2025)

    Args:
        target_date: The date to determine academic year for

    Returns:
        The starting year of the academic year
    """
    if target_date.month >= 7:
        return target_date.year
    else:
        return target_date.year - 1


def days_between(start_date: date, end_date: date) -> int:
    """
    Calculate the number of days between two dates (inclusive).

    Args:
        start_date: The starting date
        end_date: The ending date

    Returns:
        Number of days between dates (inclusive). Returns 0 if end < start.
    """
    if end_date < start_date:
        return 0
    delta = end_date - start_date
    return delta.days + 1  # +1 to make it inclusive
