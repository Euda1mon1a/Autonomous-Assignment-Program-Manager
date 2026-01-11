"""
Federal Holiday Calendar Utility.

Provides federal holiday detection for military medical residency scheduling.
Based on OPM (Office of Personnel Management) federal holiday calendar.

11 Federal Holidays:
- 5 Fixed: New Year's Day, Juneteenth, Independence Day, Veterans Day, Christmas
- 6 Floating: MLK Day, Presidents Day, Memorial Day, Labor Day, Columbus Day, Thanksgiving

OPM Observed Date Rules:
- If a fixed holiday falls on Saturday, it is observed on Friday
- If a fixed holiday falls on Sunday, it is observed on Monday

Reference: https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/
"""

from datetime import date, timedelta
from typing import NamedTuple


class Holiday(NamedTuple):
    """Represents a federal holiday with observed and actual dates."""

    date: date  # Observed date (when work schedules honor it)
    name: str
    actual_date: date | None = None  # Actual calendar date (if different from observed)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """
    Find the nth occurrence of a weekday in a month.

    Args:
        year: Calendar year
        month: Month (1-12)
        weekday: Day of week (0=Monday, 6=Sunday)
        n: Which occurrence (1=first, 2=second, etc.)

    Returns:
        Date of the nth weekday
    """
    first_day = date(year, month, 1)
    # Find first occurrence of the weekday
    days_until = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day.replace(day=1 + days_until)
    # Add (n-1) weeks to get nth occurrence
    return first_occurrence.replace(day=first_occurrence.day + (n - 1) * 7)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """
    Find the last occurrence of a weekday in a month.

    Args:
        year: Calendar year
        month: Month (1-12)
        weekday: Day of week (0=Monday, 6=Sunday)

    Returns:
        Date of the last weekday
    """
    # Start from next month and go backwards
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    # Go back to last day of target month
    last_day = next_month - timedelta(days=1)
    # Find last occurrence of the weekday
    days_back = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_back)


def _get_observed_date(holiday_date: date) -> date:
    """
    Return OPM observed date for federal holidays.

    Per OPM rules:
    - If holiday falls on Saturday → observed on Friday (day before)
    - If holiday falls on Sunday → observed on Monday (day after)
    - Otherwise → observed on actual date

    Args:
        holiday_date: The actual calendar date of the holiday

    Returns:
        The observed date (may be same as holiday_date)
    """
    weekday = holiday_date.weekday()
    if weekday == 5:  # Saturday
        return holiday_date - timedelta(days=1)  # Friday
    elif weekday == 6:  # Sunday
        return holiday_date + timedelta(days=1)  # Monday
    return holiday_date


def _make_fixed_holiday(actual_date: date, name: str) -> Holiday:
    """Create a Holiday with observed date for fixed holidays."""
    observed = _get_observed_date(actual_date)
    if observed != actual_date:
        return Holiday(date=observed, name=name, actual_date=actual_date)
    return Holiday(date=actual_date, name=name)


def get_federal_holidays(year: int) -> list[Holiday]:
    """
    Get all 11 federal holidays for a calendar year.

    Based on OPM federal holiday schedule:
    https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/

    Fixed holidays use observed dates per OPM rules:
    - Saturday holidays → observed Friday
    - Sunday holidays → observed Monday

    Args:
        year: Calendar year (e.g., 2025)

    Returns:
        List of Holiday named tuples sorted by observed date
    """
    holidays = [
        # Fixed holidays (use observed dates)
        _make_fixed_holiday(date(year, 1, 1), "New Year's Day"),
        _make_fixed_holiday(date(year, 6, 19), "Juneteenth National Independence Day"),
        _make_fixed_holiday(date(year, 7, 4), "Independence Day"),
        _make_fixed_holiday(date(year, 11, 11), "Veterans Day"),
        _make_fixed_holiday(date(year, 12, 25), "Christmas Day"),
        # Floating holidays (always fall on weekdays, no observed shift needed)
        Holiday(
            _nth_weekday_of_month(year, 1, 0, 3), "Martin Luther King Jr. Day"
        ),  # 3rd Monday Jan
        Holiday(
            _nth_weekday_of_month(year, 2, 0, 3), "Presidents Day"
        ),  # 3rd Monday Feb
        Holiday(_last_weekday_of_month(year, 5, 0), "Memorial Day"),  # Last Monday May
        Holiday(_nth_weekday_of_month(year, 9, 0, 1), "Labor Day"),  # 1st Monday Sep
        Holiday(
            _nth_weekday_of_month(year, 10, 0, 2), "Columbus Day"
        ),  # 2nd Monday Oct
        Holiday(
            _nth_weekday_of_month(year, 11, 3, 4), "Thanksgiving Day"
        ),  # 4th Thursday Nov
    ]
    return sorted(holidays, key=lambda h: h.date)


def is_federal_holiday(check_date: date) -> tuple[bool, str | None]:
    """
    Check if a date is a federal holiday.

    Args:
        check_date: Date to check

    Returns:
        Tuple of (is_holiday, holiday_name)
        - (True, "Holiday Name") if it's a holiday
        - (False, None) if not a holiday
    """
    holidays = get_federal_holidays(check_date.year)
    for holiday in holidays:
        if holiday.date == check_date:
            return True, holiday.name
    return False, None


def get_academic_year_holidays(academic_year: int) -> list[Holiday]:
    """
    Get all federal holidays within an academic year (July 1 - June 30).

    Args:
        academic_year: Start year of academic year (e.g., 2025 for AY 2025-2026)

    Returns:
        List of Holiday named tuples sorted by date
    """
    # Academic year spans two calendar years
    # July-December of start year + January-June of next year
    start_year_holidays = [
        h for h in get_federal_holidays(academic_year) if h.date.month >= 7
    ]
    end_year_holidays = [
        h for h in get_federal_holidays(academic_year + 1) if h.date.month <= 6
    ]
    return sorted(start_year_holidays + end_year_holidays, key=lambda h: h.date)
