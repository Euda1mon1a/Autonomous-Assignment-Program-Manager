"""
Temporal rule validators.

Validates time-based constraints and rules:
- Date sequences
- Time window constraints
- Scheduling horizons
- Temporal dependencies
"""

from datetime import date, datetime, timedelta
from typing import Optional

from app.validators.common import ValidationError
from app.validators.date_validators import validate_date_range, validate_date_not_null


def validate_scheduling_horizon(
    schedule_date: date,
    min_advance_days: int = 1,
    max_advance_days: int = 365,
) -> dict:
    """
    Validate that date is within acceptable scheduling horizon.

    Args:
        schedule_date: Date to schedule
        min_advance_days: Minimum days in advance (default: 1)
        max_advance_days: Maximum days in advance (default: 365)

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If date is outside horizon
    """
    today = date.today()
    min_date = today + timedelta(days=min_advance_days)
    max_date = today + timedelta(days=max_advance_days)

    if schedule_date < min_date:
        return {
            "is_valid": False,
            "schedule_date": schedule_date.isoformat(),
            "min_date": min_date.isoformat(),
            "message": f"Schedule date ({schedule_date}) is too soon. "
            f"Minimum {min_advance_days} days advance required.",
        }

    if schedule_date > max_date:
        return {
            "is_valid": False,
            "schedule_date": schedule_date.isoformat(),
            "max_date": max_date.isoformat(),
            "message": f"Schedule date ({schedule_date}) is too far ahead. "
            f"Maximum {max_advance_days} days advance allowed.",
        }

    days_until = (schedule_date - today).days

    return {
        "is_valid": True,
        "schedule_date": schedule_date.isoformat(),
        "days_until": days_until,
    }


def validate_time_window(
    start_date: date,
    end_date: date,
    min_duration_days: int = 1,
    max_duration_days: int = 365,
) -> dict:
    """
    Validate time window is acceptable.

    Args:
        start_date: Window start date
        end_date: Window end date
        min_duration_days: Minimum window duration
        max_duration_days: Maximum window duration

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If window is invalid
    """
    # Validate date range
    validated_start, validated_end = validate_date_range(
        start_date, end_date, allow_same_day=(min_duration_days == 0)
    )

    # Calculate duration
    duration_days = (validated_end - validated_start).days + 1  # Inclusive

    if duration_days < min_duration_days:
        return {
            "is_valid": False,
            "start_date": validated_start.isoformat(),
            "end_date": validated_end.isoformat(),
            "duration_days": duration_days,
            "min_duration_days": min_duration_days,
            "message": f"Time window too short: {duration_days} days. "
            f"Minimum {min_duration_days} days required.",
        }

    if duration_days > max_duration_days:
        return {
            "is_valid": False,
            "start_date": validated_start.isoformat(),
            "end_date": validated_end.isoformat(),
            "duration_days": duration_days,
            "max_duration_days": max_duration_days,
            "message": f"Time window too long: {duration_days} days. "
            f"Maximum {max_duration_days} days allowed.",
        }

    return {
        "is_valid": True,
        "start_date": validated_start.isoformat(),
        "end_date": validated_end.isoformat(),
        "duration_days": duration_days,
    }


def validate_sequence_order(
    dates: list[date],
    allow_duplicates: bool = False,
    allow_gaps: bool = True,
) -> dict:
    """
    Validate sequence of dates is properly ordered.

    Args:
        dates: List of dates to validate
        allow_duplicates: Allow duplicate dates in sequence
        allow_gaps: Allow non-consecutive dates

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If dates list is empty
    """
    if not dates:
        raise ValidationError("Date sequence cannot be empty")

    if len(dates) == 1:
        return {
            "is_valid": True,
            "sequence_length": 1,
            "is_consecutive": True,
        }

    issues = []

    # Check ordering
    for i in range(len(dates) - 1):
        current = dates[i]
        next_date = dates[i + 1]

        if current > next_date:
            issues.append(f"Dates out of order at index {i}: {current} > {next_date}")

        if not allow_duplicates and current == next_date:
            issues.append(f"Duplicate date at index {i}: {current}")

    # Check for gaps if not allowed
    if not allow_gaps:
        for i in range(len(dates) - 1):
            current = dates[i]
            next_date = dates[i + 1]
            expected_next = current + timedelta(days=1)

            if next_date != expected_next:
                gap_days = (next_date - current).days - 1
                issues.append(
                    f"Gap in sequence at index {i}: {gap_days} days between "
                    f"{current} and {next_date}"
                )

    # Calculate statistics
    is_consecutive = all(
        dates[i + 1] - dates[i] == timedelta(days=1) for i in range(len(dates) - 1)
    )

    return {
        "is_valid": len(issues) == 0,
        "sequence_length": len(dates),
        "is_consecutive": is_consecutive,
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
        "issues": issues,
    }


def validate_temporal_dependency(
    predecessor_date: date,
    successor_date: date,
    min_gap_days: int = 0,
    max_gap_days: int | None = None,
) -> dict:
    """
    Validate temporal dependency between two dates.

    Args:
        predecessor_date: Earlier date
        successor_date: Later date
        min_gap_days: Minimum days between dates
        max_gap_days: Maximum days between dates (optional)

    Returns:
        dict: Validation result
    """
    # Validate dates
    pred = validate_date_not_null(predecessor_date, "Predecessor date")
    succ = validate_date_not_null(successor_date, "Successor date")

    # Check order
    if succ < pred:
        return {
            "is_valid": False,
            "predecessor_date": pred.isoformat(),
            "successor_date": succ.isoformat(),
            "message": "Successor date must be after predecessor date",
        }

    # Calculate gap
    gap_days = (succ - pred).days

    # Check minimum gap
    if gap_days < min_gap_days:
        return {
            "is_valid": False,
            "predecessor_date": pred.isoformat(),
            "successor_date": succ.isoformat(),
            "gap_days": gap_days,
            "min_gap_days": min_gap_days,
            "message": f"Gap too small: {gap_days} days. Minimum {min_gap_days} days required.",
        }

    # Check maximum gap if specified
    if max_gap_days is not None and gap_days > max_gap_days:
        return {
            "is_valid": False,
            "predecessor_date": pred.isoformat(),
            "successor_date": succ.isoformat(),
            "gap_days": gap_days,
            "max_gap_days": max_gap_days,
            "message": f"Gap too large: {gap_days} days. Maximum {max_gap_days} days allowed.",
        }

    return {
        "is_valid": True,
        "predecessor_date": pred.isoformat(),
        "successor_date": succ.isoformat(),
        "gap_days": gap_days,
    }


def validate_rolling_window(
    check_date: date,
    window_size_days: int,
    reference_date: date | None = None,
) -> dict:
    """
    Validate date falls within rolling time window.

    Args:
        check_date: Date to validate
        window_size_days: Size of rolling window in days
        reference_date: Reference date (default: today)

    Returns:
        dict: Validation result
    """
    if reference_date is None:
        reference_date = date.today()

    window_start = reference_date - timedelta(days=window_size_days // 2)
    window_end = reference_date + timedelta(days=window_size_days // 2)

    is_in_window = window_start <= check_date <= window_end

    return {
        "is_in_window": is_in_window,
        "check_date": check_date.isoformat(),
        "reference_date": reference_date.isoformat(),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "window_size_days": window_size_days,
    }


def validate_temporal_rule(
    rule_name: str,
    context: dict,
) -> dict:
    """
    Validate a named temporal rule.

    Args:
        rule_name: Name of temporal rule
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If rule name is unknown
    """
    valid_rules = [
        "scheduling_horizon",
        "time_window",
        "sequence_order",
        "temporal_dependency",
        "rolling_window",
    ]

    if rule_name not in valid_rules:
        raise ValidationError(
            f"Unknown temporal rule: '{rule_name}'. Valid rules: {valid_rules}"
        )

    return {
        "rule_name": rule_name,
        "is_valid": True,
        "message": f"Temporal rule '{rule_name}' validated",
    }


def check_date_constraints(
    check_date: date,
    min_date: date | None = None,
    max_date: date | None = None,
) -> bool:
    """
    Quick boolean check for date constraints.

    Args:
        check_date: Date to check
        min_date: Minimum allowed date
        max_date: Maximum allowed date

    Returns:
        bool: True if within constraints, False otherwise
    """
    if min_date is not None and check_date < min_date:
        return False

    if max_date is not None and check_date > max_date:
        return False

    return True
