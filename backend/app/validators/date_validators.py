"""
Date and time validation functions.

Provides validators for:
- Date range validation
- Time period validation
- Academic year validation
- Block date validation
- ACGME work period validation
"""

from datetime import date, datetime, timedelta
from typing import Optional

from app.validators.common import ValidationError


def validate_date_not_null(
    value: date | datetime | None, field_name: str = "Date"
) -> date:
    """
    Validate date is not None and convert to date if datetime.

    Args:
        value: Date or datetime to validate
        field_name: Name of field for error messages

    Returns:
        date: Validated date

    Raises:
        ValidationError: If date is None
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be null")

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    raise ValidationError(f"{field_name} must be a date, got {type(value).__name__}")


def validate_date_range(
    start_date: date | datetime,
    end_date: date | datetime,
    allow_same_day: bool = True,
    max_days: int | None = None,
    start_field_name: str = "Start date",
    end_field_name: str = "End date",
) -> tuple[date, date]:
    """
    Validate date range is valid.

    Checks:
    - Both dates are not null
    - End date is not before start date
    - Range does not exceed maximum days (if specified)

    Args:
        start_date: Range start date
        end_date: Range end date
        allow_same_day: Allow start and end to be same day (default: True)
        max_days: Maximum allowed range in days (optional)
        start_field_name: Name of start field for error messages
        end_field_name: Name of end field for error messages

    Returns:
        tuple[date, date]: Validated (start_date, end_date) as date objects

    Raises:
        ValidationError: If date range is invalid
    """
    # Convert to dates if needed
    start = validate_date_not_null(start_date, start_field_name)
    end = validate_date_not_null(end_date, end_field_name)

    # Check chronological order
    if end < start:
        raise ValidationError(
            f"{end_field_name} ({end}) cannot be before {start_field_name} ({start})"
        )

    # Check same day if not allowed
    if not allow_same_day and end == start:
        raise ValidationError(
            f"{end_field_name} cannot be the same as {start_field_name}"
        )

    # Check maximum range
    if max_days is not None:
        days_diff = (end - start).days
        if days_diff > max_days:
            raise ValidationError(
                f"Date range exceeds maximum of {max_days} days. "
                f"Range is {days_diff} days ({start} to {end})"
            )

    return start, end


def validate_date_in_range(
    check_date: date | datetime,
    start_date: date | datetime,
    end_date: date | datetime,
    field_name: str = "Date",
) -> date:
    """
    Validate date falls within specified range.

    Args:
        check_date: Date to check
        start_date: Range start (inclusive)
        end_date: Range end (inclusive)
        field_name: Name of field for error messages

    Returns:
        date: Validated date

    Raises:
        ValidationError: If date is outside range
    """
    check = validate_date_not_null(check_date, field_name)
    start = validate_date_not_null(start_date, "Range start")
    end = validate_date_not_null(end_date, "Range end")

    if check < start or check > end:
        raise ValidationError(
            f"{field_name} ({check}) must be between {start} and {end}"
        )

    return check


def validate_academic_year_date(value: date, field_name: str = "Date") -> date:
    """
    Validate a single date is within a reasonable academic year range.

    Academic year runs July 1 to June 30.

    Args:
        value: Date to validate
        field_name: Name of field for error messages

    Returns:
        date: Validated date

    Raises:
        ValidationError: If date is unreasonable
    """
    validated = validate_date_not_null(value, field_name)

    today = date.today()
    five_years_ago = today - timedelta(days=365 * 5)
    five_years_ahead = today + timedelta(days=365 * 5)

    if validated < five_years_ago:
        raise ValidationError(
            f"{field_name} ({validated}) is more than 5 years in the past"
        )

    if validated > five_years_ahead:
        raise ValidationError(
            f"{field_name} ({validated}) is more than 5 years in the future"
        )

    return validated


def validate_academic_year_dates(start_date: date, end_date: date) -> tuple[date, date]:
    """
    Validate academic year date range.

    Academic year must be:
    - Exactly 365 days (or 366 for leap year)
    - Start and end dates make sense for academic calendar

    Args:
        start_date: Academic year start
        end_date: Academic year end

    Returns:
        tuple[date, date]: Validated (start_date, end_date)

    Raises:
        ValidationError: If academic year dates are invalid
    """
    start, end = validate_date_range(
        start_date,
        end_date,
        allow_same_day=False,
        start_field_name="Academic year start",
        end_field_name="Academic year end",
    )

    # Calculate days
    days_diff = (end - start).days + 1  # +1 to include both start and end

    # Should be 365 or 366 days
    if days_diff not in (365, 366):
        raise ValidationError(
            f"Academic year must be 365 or 366 days. Got {days_diff} days "
            f"({start} to {end})"
        )

    return start, end


def validate_block_date(block_date: date) -> date:
    """
    Validate block date is reasonable.

    Blocks should be:
    - Not in the distant past (> 5 years ago)
    - Not in the distant future (> 5 years ahead)

    Args:
        block_date: Block date to validate

    Returns:
        date: Validated block date

    Raises:
        ValidationError: If block date is unreasonable
    """
    validated = validate_date_not_null(block_date, "Block date")

    today = date.today()
    five_years_ago = today - timedelta(days=365 * 5)
    five_years_ahead = today + timedelta(days=365 * 5)

    if validated < five_years_ago:
        raise ValidationError(
            f"Block date ({validated}) is more than 5 years in the past"
        )

    if validated > five_years_ahead:
        raise ValidationError(
            f"Block date ({validated}) is more than 5 years in the future"
        )

    return validated


def validate_acgme_work_period(
    start_date: date | datetime, end_date: date | datetime
) -> tuple[date, date]:
    """
    Validate ACGME work period for duty hour calculations.

    ACGME periods should be:
    - 1-7 days for daily checks
    - 28 days (4 weeks) for rolling average checks

    Args:
        start_date: Period start
        end_date: Period end

    Returns:
        tuple[date, date]: Validated (start_date, end_date)

    Raises:
        ValidationError: If period length is invalid for ACGME calculations
    """
    start, end = validate_date_range(
        start_date,
        end_date,
        allow_same_day=True,
        max_days=28,  # Maximum rolling period
        start_field_name="ACGME period start",
        end_field_name="ACGME period end",
    )

    days = (end - start).days + 1  # +1 to include both days

    # Common valid periods:
    # - 1 day: single day check
    # - 7 days: weekly check (1-in-7 rule)
    # - 28 days: 4-week rolling average (80-hour rule)

    # Allow 1-28 days, but warn if unusual
    if days not in (1, 7, 28):
        # This is just informational - still allow the period
        pass

    return start, end


def validate_future_date(
    check_date: date | datetime, allow_today: bool = True, field_name: str = "Date"
) -> date:
    """
    Validate date is in the future.

    Args:
        check_date: Date to check
        allow_today: Allow today's date (default: True)
        field_name: Name of field for error messages

    Returns:
        date: Validated future date

    Raises:
        ValidationError: If date is in the past
    """
    validated = validate_date_not_null(check_date, field_name)
    today = date.today()

    if allow_today:
        if validated < today:
            raise ValidationError(f"{field_name} ({validated}) cannot be in the past")
    else:
        if validated <= today:
            raise ValidationError(
                f"{field_name} ({validated}) must be in the future (after today)"
            )

    return validated


def validate_past_date(
    check_date: date | datetime, allow_today: bool = True, field_name: str = "Date"
) -> date:
    """
    Validate date is in the past.

    Args:
        check_date: Date to check
        allow_today: Allow today's date (default: True)
        field_name: Name of field for error messages

    Returns:
        date: Validated past date

    Raises:
        ValidationError: If date is in the future
    """
    validated = validate_date_not_null(check_date, field_name)
    today = date.today()

    if allow_today:
        if validated > today:
            raise ValidationError(f"{field_name} ({validated}) cannot be in the future")
    else:
        if validated >= today:
            raise ValidationError(
                f"{field_name} ({validated}) must be in the past (before today)"
            )

    return validated


def validate_time_between_dates(
    start_date: date | datetime,
    end_date: date | datetime,
    min_hours: float | None = None,
    max_hours: float | None = None,
) -> timedelta:
    """
    Validate time duration between dates.

    Args:
        start_date: Start date/datetime
        end_date: End date/datetime
        min_hours: Minimum allowed hours (optional)
        max_hours: Maximum allowed hours (optional)

    Returns:
        timedelta: Time difference

    Raises:
        ValidationError: If duration is outside allowed range
    """
    # Validate range first
    start, end = validate_date_range(start_date, end_date)

    # Calculate difference
    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        delta = end_date - start_date
    else:
        delta = timedelta(days=(end - start).days)

    hours = delta.total_seconds() / 3600

    if min_hours is not None and hours < min_hours:
        raise ValidationError(
            f"Time period ({hours:.1f} hours) is less than minimum {min_hours} hours"
        )

    if max_hours is not None and hours > max_hours:
        raise ValidationError(
            f"Time period ({hours:.1f} hours) exceeds maximum {max_hours} hours"
        )

    return delta


def validate_week_number(week: int, year: int | None = None) -> int:
    """
    Validate week number is valid (1-53).

    Args:
        week: Week number to validate
        year: Optional year for more specific validation

    Returns:
        int: Validated week number

    Raises:
        ValidationError: If week number is invalid
    """
    if not isinstance(week, int):
        raise ValidationError(f"Week must be an integer, got {type(week).__name__}")

    if week < 1 or week > 53:
        raise ValidationError(f"Week number must be between 1 and 53, got {week}")

    # If year provided, check it's valid for that year
    if year is not None:
        # Some years have 52 weeks, some have 53
        # ISO week date system
        last_week = date(year, 12, 28).isocalendar()[1]
        if week > last_week:
            raise ValidationError(
                f"Week {week} does not exist in year {year} (max week: {last_week})"
            )

    return week


def validate_session_time(session: str) -> str:
    """
    Validate session is 'AM' or 'PM'.

    Args:
        session: Session identifier

    Returns:
        str: Validated session (uppercase)

    Raises:
        ValidationError: If session is not AM or PM
    """
    if not session:
        raise ValidationError("Session cannot be empty")

    session_upper = session.upper().strip()

    if session_upper not in ("AM", "PM"):
        raise ValidationError(f"Session must be 'AM' or 'PM', got '{session}'")

    return session_upper
