"""
Date validation utilities for business logic checks.

Provides reasonable range checks to prevent nonsensical dates in medical
residency scheduling context (2020-2050 range for academic years).
"""
from datetime import date
from typing import Optional


# Reasonable date range for medical residency scheduling application
# Academic years typically span current decade plus planning horizon
MIN_REASONABLE_DATE = date(2020, 1, 1)
MAX_REASONABLE_DATE = date(2050, 12, 31)


def validate_date_range(
    value: date,
    field_name: str = "date",
    min_date: Optional[date] = None,
    max_date: Optional[date] = None
) -> date:
    """
    Validate that a date falls within reasonable bounds.

    Args:
        value: Date to validate
        field_name: Name of the field being validated (for error messages)
        min_date: Minimum allowed date (defaults to MIN_REASONABLE_DATE)
        max_date: Maximum allowed date (defaults to MAX_REASONABLE_DATE)

    Returns:
        date: The validated date value

    Raises:
        ValueError: If date is outside reasonable range
    """
    min_allowed = min_date or MIN_REASONABLE_DATE
    max_allowed = max_date or MAX_REASONABLE_DATE

    if value < min_allowed:
        raise ValueError(
            f"{field_name} must be on or after {min_allowed.isoformat()}. "
            f"Got: {value.isoformat()}"
        )

    if value > max_allowed:
        raise ValueError(
            f"{field_name} must be on or before {max_allowed.isoformat()}. "
            f"Got: {value.isoformat()}"
        )

    return value


def validate_date_order(
    start_date: date,
    end_date: date,
    start_field: str = "start_date",
    end_field: str = "end_date",
    allow_same: bool = True
) -> tuple[date, date]:
    """
    Validate that start_date comes before (or equals) end_date.

    Args:
        start_date: Starting date
        end_date: Ending date
        start_field: Name of start field (for error messages)
        end_field: Name of end field (for error messages)
        allow_same: Allow start and end to be the same date

    Returns:
        tuple[date, date]: The validated (start_date, end_date) pair

    Raises:
        ValueError: If dates are in wrong order
    """
    if allow_same:
        if start_date > end_date:
            raise ValueError(
                f"{start_field} ({start_date.isoformat()}) must be before or equal to "
                f"{end_field} ({end_date.isoformat()})"
            )
    else:
        if start_date >= end_date:
            raise ValueError(
                f"{start_field} ({start_date.isoformat()}) must be before "
                f"{end_field} ({end_date.isoformat()})"
            )

    return start_date, end_date


def validate_expiration_after_issue(
    issued_date: date,
    expiration_date: date,
    issue_field: str = "issued_date",
    expiration_field: str = "expiration_date"
) -> tuple[date, date]:
    """
    Validate that expiration_date comes after issued_date.

    Args:
        issued_date: Date of issuance
        expiration_date: Date of expiration
        issue_field: Name of issue field (for error messages)
        expiration_field: Name of expiration field (for error messages)

    Returns:
        tuple[date, date]: The validated (issued_date, expiration_date) pair

    Raises:
        ValueError: If expiration is before or same as issue date
    """
    if expiration_date <= issued_date:
        raise ValueError(
            f"{expiration_field} ({expiration_date.isoformat()}) must be after "
            f"{issue_field} ({issued_date.isoformat()})"
        )

    return issued_date, expiration_date


def validate_academic_year_date(
    value: date,
    field_name: str = "date"
) -> date:
    """
    Validate date is within academic year bounds (July 1, 2020 - June 30, 2050).

    Academic years typically run July 1 - June 30, so we enforce slightly
    tighter bounds than general date range.

    Args:
        value: Date to validate
        field_name: Name of field being validated

    Returns:
        date: The validated date value

    Raises:
        ValueError: If date is outside academic year planning range
    """
    academic_min = date(2020, 7, 1)
    academic_max = date(2050, 6, 30)

    return validate_date_range(
        value,
        field_name=field_name,
        min_date=academic_min,
        max_date=academic_max
    )
