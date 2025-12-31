"""
Call Schedule Compliance Validator.

Implements ACGME call scheduling rules:
- 1-in-7 rule: No more than 1 call every 3 nights averaged over 4 weeks
- Consecutive night limits: Maximum consecutive night shifts
- Call frequency fairness: Equitable distribution among faculty
- Post-call recovery: Mandatory rest after overnight call
- Night Float transitions: Post-call day (PC) mandatory after Night Float

This validator ensures fair call distribution while maintaining
resident wellness and ACGME compliance.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# ACGME Call Constants
MAX_CALL_FREQUENCY_DAYS = 3  # Every third night rule
ROLLING_WINDOW_WEEKS = 4  # 4-week averaging period
ROLLING_WINDOW_DAYS = 28
MAX_CONSECUTIVE_NIGHTS = 2  # Clinical guideline (stricter than 1-in-7)
MIN_CALL_SPACING_DAYS = 2  # Minimum days between calls
POST_CALL_MANDATORY_HOURS = 10  # Minimum rest after overnight call


@dataclass
class CallViolation:
    """Represents a call scheduling compliance violation."""

    person_id: UUID
    violation_type: str  # "frequency", "spacing", "consecutive", "equity"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM"
    message: str
    call_dates: list[date]
    violation_count: int  # How many calls violate


@dataclass
class CallWarning:
    """Represents a call scheduling warning."""

    person_id: UUID
    warning_type: str  # "approaching_limit", "imbalance"
    message: str
    call_count: int
    equity_metric: float  # Standard deviation from mean


class CallValidator:
    """
    Validates ACGME call scheduling compliance for faculty.

    Rules:
    1. Every-3rd-night: No more than ~10 calls in 28-day period
    2. Consecutive limits: No more than 2 consecutive overnight calls
    3. Minimum spacing: At least 2 days between calls
    4. Equity: Fair distribution among faculty pool
    5. Post-call: Mandatory rest periods after call
    """

    def __init__(self):
        """Initialize call validator."""
        self.max_call_frequency_days = MAX_CALL_FREQUENCY_DAYS
        self.rolling_window_days = ROLLING_WINDOW_DAYS
        self.rolling_window_weeks = ROLLING_WINDOW_WEEKS
        self.max_calls_per_window = (
            self.rolling_window_days // self.max_call_frequency_days
        )  # ~9-10

    def validate_call_frequency(
        self,
        person_id: UUID,
        call_dates: list[date],
    ) -> tuple[list[CallViolation], list[CallWarning]]:
        """
        Validate every-3rd-night rule compliance.

        In any 28-day rolling window, maximum ~9-10 in-house call nights.

        Args:
            person_id: Faculty member ID
            call_dates: List of call dates

        Returns:
            (violations, warnings) tuple
        """
        violations = []
        warnings = []

        if not call_dates or len(call_dates) < 2:
            return violations, warnings

        sorted_dates = sorted(call_dates)

        # Check every possible 28-day rolling window
        for i, start_date in enumerate(sorted_dates):
            window_end = start_date + timedelta(days=self.rolling_window_days - 1)

            # Count calls in this window
            calls_in_window = [
                d for d in sorted_dates
                if start_date <= d <= window_end
            ]
            call_count = len(calls_in_window)

            # Check for violation (>10 calls in 28 days)
            if call_count > self.max_calls_per_window:
                violation_count = call_count - self.max_calls_per_window
                violations.append(
                    CallViolation(
                        person_id=person_id,
                        violation_type="frequency",
                        severity="HIGH",
                        message=(
                            f"Excessive call frequency: {call_count} calls in "
                            f"28-day window {start_date} to {window_end} "
                            f"(limit: {self.max_calls_per_window})"
                        ),
                        call_dates=calls_in_window,
                        violation_count=violation_count,
                    )
                )
            elif call_count > self.max_calls_per_window * 0.9:  # Approaching limit
                warnings.append(
                    CallWarning(
                        person_id=person_id,
                        warning_type="approaching_limit",
                        message=(
                            f"Approaching call frequency limit: "
                            f"{call_count} calls in {self.max_calls_per_window} "
                            f"call window"
                        ),
                        call_count=call_count,
                        equity_metric=0.9,
                    )
                )

        return violations, warnings

    def validate_consecutive_nights(
        self,
        person_id: UUID,
        call_dates: list[date],
    ) -> tuple[list[CallViolation], list[CallWarning]]:
        """
        Validate consecutive night call limits.

        Maximum 2 consecutive overnight call nights recommended.

        Args:
            person_id: Faculty member ID
            call_dates: List of consecutive call dates

        Returns:
            (violations, warnings) tuple
        """
        violations = []
        warnings = []

        if not call_dates or len(call_dates) < 2:
            return violations, warnings

        sorted_dates = sorted(call_dates)

        # Find consecutive sequences
        consecutive_sequence = [sorted_dates[0]]
        sequence_start = sorted_dates[0]

        for i in range(1, len(sorted_dates)):
            current_date = sorted_dates[i]
            previous_date = sorted_dates[i - 1]

            # Check if consecutive
            if (current_date - previous_date).days == 1:
                consecutive_sequence.append(current_date)
            else:
                # End of sequence, check length
                if len(consecutive_sequence) > MAX_CONSECUTIVE_NIGHTS:
                    violations.append(
                        CallViolation(
                            person_id=person_id,
                            violation_type="consecutive",
                            severity="MEDIUM",
                            message=(
                                f"Excessive consecutive call: "
                                f"{len(consecutive_sequence)} consecutive nights "
                                f"{sequence_start} to {consecutive_sequence[-1]} "
                                f"(limit: {MAX_CONSECUTIVE_NIGHTS})"
                            ),
                            call_dates=consecutive_sequence.copy(),
                            violation_count=len(consecutive_sequence) -
                            MAX_CONSECUTIVE_NIGHTS,
                        )
                    )
                elif len(consecutive_sequence) == MAX_CONSECUTIVE_NIGHTS:
                    warnings.append(
                        CallWarning(
                            person_id=person_id,
                            warning_type="approaching_limit",
                            message=(
                                f"At maximum consecutive nights: "
                                f"{sequence_start} to {consecutive_sequence[-1]}"
                            ),
                            call_count=len(consecutive_sequence),
                            equity_metric=1.0,
                        )
                    )

                # Reset sequence
                consecutive_sequence = [current_date]
                sequence_start = current_date

        # Check final sequence
        if len(consecutive_sequence) > MAX_CONSECUTIVE_NIGHTS:
            violations.append(
                CallViolation(
                    person_id=person_id,
                    violation_type="consecutive",
                    severity="MEDIUM",
                    message=(
                        f"Excessive consecutive call: "
                        f"{len(consecutive_sequence)} consecutive nights "
                        f"(limit: {MAX_CONSECUTIVE_NIGHTS})"
                    ),
                    call_dates=consecutive_sequence,
                    violation_count=len(consecutive_sequence) -
                    MAX_CONSECUTIVE_NIGHTS,
                )
            )

        return violations, warnings

    def validate_call_spacing(
        self,
        person_id: UUID,
        call_dates: list[date],
    ) -> tuple[list[CallViolation], list[CallWarning]]:
        """
        Validate minimum spacing between call assignments.

        Minimum 2 days between call assignments (at least 1 day off).

        Args:
            person_id: Faculty member ID
            call_dates: List of call dates

        Returns:
            (violations, warnings) tuple
        """
        violations = []
        warnings = []

        if not call_dates or len(call_dates) < 2:
            return violations, warnings

        sorted_dates = sorted(call_dates)

        for i in range(len(sorted_dates) - 1):
            current_date = sorted_dates[i]
            next_date = sorted_dates[i + 1]
            spacing = (next_date - current_date).days

            if spacing < MIN_CALL_SPACING_DAYS:
                violations.append(
                    CallViolation(
                        person_id=person_id,
                        violation_type="spacing",
                        severity="MEDIUM",
                        message=(
                            f"Insufficient call spacing: {spacing} days between "
                            f"{current_date} and {next_date} "
                            f"(minimum {MIN_CALL_SPACING_DAYS} required)"
                        ),
                        call_dates=[current_date, next_date],
                        violation_count=1,
                    )
                )

        return violations, warnings

    def validate_call_equity(
        self,
        period_start: date,
        period_end: date,
        faculty_call_assignments: dict[UUID, list[date]],
    ) -> tuple[list[CallWarning], dict]:
        """
        Validate fair call distribution among faculty.

        Args:
            period_start: Start of period
            period_end: End of period
            faculty_call_assignments: Dict mapping faculty_id to call_dates

        Returns:
            (warnings, metrics) tuple where metrics contains:
            - mean_calls: Average calls per faculty
            - std_dev: Standard deviation
            - imbalance_ratio: max / min ratio
            - over_assigned: Faculty with >mean calls
            - under_assigned: Faculty with <mean calls
        """
        warnings = []
        call_counts = {
            fid: len(dates) for fid, dates in faculty_call_assignments.items()
        }

        if not call_counts or len(call_counts) < 2:
            return warnings, {}

        counts = list(call_counts.values())
        mean_calls = sum(counts) / len(counts)
        variance = sum((c - mean_calls) ** 2 for c in counts) / len(counts)
        std_dev = variance ** 0.5

        imbalance_ratio = max(counts) / (min(counts) + 0.1)  # Avoid division by zero

        # Identify over/under-assigned
        over_assigned = [
            fid for fid, count in call_counts.items()
            if count > mean_calls + std_dev
        ]
        under_assigned = [
            fid for fid, count in call_counts.items()
            if count < mean_calls - std_dev and count > 0
        ]

        # Create warnings for imbalance
        if imbalance_ratio > 1.5:  # More than 50% difference
            warnings.append(
                CallWarning(
                    person_id=UUID('00000000-0000-0000-0000-000000000000'),
                    warning_type="imbalance",
                    message=(
                        f"Call distribution imbalance detected: "
                        f"ratio of {imbalance_ratio:.2f} "
                        f"(some faculty have significantly more/fewer calls)"
                    ),
                    call_count=int(mean_calls),
                    equity_metric=std_dev,
                )
            )

        metrics = {
            'mean_calls': mean_calls,
            'std_dev': std_dev,
            'imbalance_ratio': imbalance_ratio,
            'over_assigned': over_assigned,
            'under_assigned': under_assigned,
            'total_calls': sum(counts),
            'faculty_count': len(call_counts),
        }

        return warnings, metrics

    def validate_night_float_post_call(
        self,
        person_id: UUID,
        night_float_end_date: date,
        post_call_assignment_date: Optional[date] = None,
    ) -> Optional[str]:
        """
        Validate Night Float post-call (PC) day assignment.

        After completing Night Float assignment, resident must have
        post-call recovery day (both AM and PM blocked).

        Args:
            person_id: Resident ID
            night_float_end_date: Last date of Night Float assignment
            post_call_assignment_date: Expected PC assignment date

        Returns:
            Error message if missing PC day, None if compliant
        """
        expected_pc_date = night_float_end_date + timedelta(days=1)

        if post_call_assignment_date is None:
            return (
                f"Missing mandatory post-call recovery day after Night Float "
                f"(should be {expected_pc_date})"
            )

        if post_call_assignment_date != expected_pc_date:
            return (
                f"Post-call recovery day on wrong date: "
                f"{post_call_assignment_date} (expected {expected_pc_date})"
            )

        return None

    def get_call_schedule_summary(
        self,
        faculty_call_assignments: dict[UUID, list[date]],
        period_start: date,
        period_end: date,
    ) -> dict:
        """
        Generate summary of call schedule for period.

        Args:
            faculty_call_assignments: Dict mapping faculty_id to call_dates
            period_start: Period start date
            period_end: Period end date

        Returns:
            Summary dict with call statistics
        """
        total_calls = sum(len(dates) for dates in faculty_call_assignments.values())
        faculty_count = len(faculty_call_assignments)

        call_counts = {
            fid: len(dates) for fid, dates in faculty_call_assignments.items()
        }

        if not call_counts:
            return {
                'period': {'start': period_start, 'end': period_end},
                'total_calls': 0,
                'faculty_count': 0,
                'mean_calls_per_faculty': 0,
                'call_distribution': {},
            }

        counts = list(call_counts.values())
        mean = sum(counts) / len(counts) if counts else 0

        return {
            'period': {'start': period_start, 'end': period_end},
            'total_calls': total_calls,
            'faculty_count': faculty_count,
            'mean_calls_per_faculty': mean,
            'min_calls': min(counts),
            'max_calls': max(counts),
            'call_distribution': call_counts,
        }
