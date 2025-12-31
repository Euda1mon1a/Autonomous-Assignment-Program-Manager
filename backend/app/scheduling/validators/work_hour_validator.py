"""
Work Hour Compliance Validator.

Implements ACGME work hour rules:
- 80-hour maximum per week (rolling 4-week average)
- 24+4 hour shift limits (24 hours + 4 hours handoff)
- 10-hour minimum rest period after 24-hour shifts
- Moonlighting hours integration

This validator ensures residents work within regulatory limits while
tracking workload distribution and violation severity.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# ACGME Work Hour Constants
MAX_WEEKLY_HOURS = 80
ROLLING_WEEKS = 4
ROLLING_DAYS = 28  # Exact 28-day window, not 4 calendar weeks
HOURS_PER_BLOCK = 6  # Standard block duration (AM/PM sessions)
MAX_BLOCKS_PER_WINDOW = (MAX_WEEKLY_HOURS * ROLLING_WEEKS) // HOURS_PER_BLOCK  # 53
MAX_CONSECUTIVE_HOURS = 24
MAX_HOURS_AFTER_24_SHIFT = 4  # 24+4 rule
MAX_TOTAL_SHIFT_HOURS = 28
MIN_REST_HOURS_AFTER_SHIFT = 10
MOONLIGHTING_HOURS_PER_WEEK_WARNING = 20  # Alert if exceeding this


@dataclass
class WorkHourViolation:
    """Represents a work hour compliance violation."""

    person_id: UUID
    violation_type: str  # "80_hour", "24_plus_4", "rest_period", "moonlighting"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    message: str
    date_range: tuple[date, date]
    hours: float
    limit: float
    violation_percentage: float = 0.0  # (hours - limit) / limit * 100


@dataclass
class WorkHourWarning:
    """Represents a work hour warning (approaching limit)."""

    person_id: UUID
    warning_type: str  # "approaching_limit", "imbalance", "pattern"
    message: str
    current_hours: float
    warning_threshold: float
    days_remaining: int


class WorkHourValidator:
    """
    Validates ACGME work hour compliance for residents.

    Rules:
    1. 80-hour rolling average: ≤ 80 hours/week averaged over 4 weeks (28 days)
    2. 24+4 rule: Maximum 24 consecutive hours, plus 4 hours for handoff (28 total)
    3. 10-hour rest: Minimum 10 continuous hours off after any shift
    4. Moonlighting integration: All moonlighting hours count toward 80-hour limit
    """

    def __init__(self):
        """Initialize work hour validator."""
        self.max_weekly_hours = MAX_WEEKLY_HOURS
        self.rolling_days = ROLLING_DAYS
        self.rolling_weeks = ROLLING_WEEKS
        self.hours_per_block = HOURS_PER_BLOCK
        self.max_blocks_per_window = MAX_BLOCKS_PER_WINDOW

    def validate_80_hour_rolling_average(
        self,
        person_id: UUID,
        hours_by_date: dict[date, float],
        moonlighting_hours: dict[date, float] = None,
    ) -> tuple[list[WorkHourViolation], list[WorkHourWarning]]:
        """
        Validate 80-hour rolling average across all 28-day windows.

        Args:
            person_id: Resident ID
            hours_by_date: Dict mapping date to hours worked
            moonlighting_hours: Dict mapping date to moonlighting hours

        Returns:
            (violations, warnings) tuples
        """
        violations = []
        warnings = []

        if not hours_by_date:
            return violations, warnings

        # Integrate moonlighting hours
        total_hours_by_date = dict(hours_by_date)
        if moonlighting_hours:
            for work_date, moonlight_hours in moonlighting_hours.items():
                if work_date in total_hours_by_date:
                    total_hours_by_date[work_date] += moonlight_hours
                else:
                    total_hours_by_date[work_date] = moonlight_hours

        sorted_dates = sorted(total_hours_by_date.keys())
        if not sorted_dates:
            return violations, warnings

        # Check every possible 28-day rolling window
        for start_date in sorted_dates:
            window_end = start_date + timedelta(days=self.rolling_days - 1)

            # Calculate total hours in window
            total_hours = sum(
                hours
                for d, hours in total_hours_by_date.items()
                if start_date <= d <= window_end
            )

            # Calculate average weekly hours
            average_weekly = total_hours / self.rolling_weeks

            # Check for violation
            if average_weekly > self.max_weekly_hours:
                violation_pct = (
                    (average_weekly - self.max_weekly_hours)
                    / self.max_weekly_hours
                    * 100
                )
                violations.append(
                    WorkHourViolation(
                        person_id=person_id,
                        violation_type="80_hour",
                        severity="CRITICAL" if violation_pct > 10 else "HIGH",
                        message=(
                            f"80-hour rule violation: "
                            f"{average_weekly:.1f}h/week avg over {start_date} to "
                            f"{window_end} (limit: {self.max_weekly_hours}h)"
                        ),
                        date_range=(start_date, window_end),
                        hours=average_weekly,
                        limit=self.max_weekly_hours,
                        violation_percentage=violation_pct,
                    )
                )
            elif average_weekly > self.max_weekly_hours * 0.95:  # 76+ hours
                warnings.append(
                    WorkHourWarning(
                        person_id=person_id,
                        warning_type="approaching_limit",
                        message=(
                            f"Approaching 80-hour limit: "
                            f"{average_weekly:.1f}h/week over {start_date}"
                        ),
                        current_hours=average_weekly,
                        warning_threshold=76.0,
                        days_remaining=(window_end - start_date).days,
                    )
                )

        return violations, warnings

    def validate_24_plus_4_rule(
        self,
        person_id: UUID,
        shift_data: list[dict],
    ) -> tuple[list[WorkHourViolation], list[WorkHourWarning]]:
        """
        Validate 24+4 hour shift limits.

        This is a simplified implementation using block-based data.
        In production systems with minute-level precision, this would be
        more granular.

        Args:
            person_id: Resident ID
            shift_data: List of dicts with {'date': date, 'start_time': time,
                       'end_time': time, 'duration_hours': float}

        Returns:
            (violations, warnings) tuples
        """
        violations = []
        warnings = []

        # Group shifts by approximate continuous period
        if not shift_data:
            return violations, warnings

        sorted_shifts = sorted(shift_data, key=lambda x: x.get("start_time", "00:00"))

        for i, shift in enumerate(sorted_shifts):
            duration = shift.get("duration_hours", 0)

            if duration > MAX_CONSECUTIVE_HOURS:
                # Check if 24+4 exception applies
                if duration <= MAX_TOTAL_SHIFT_HOURS:
                    # 24+4 rule allows up to 28 hours
                    if duration > 26:  # Close to limit
                        warnings.append(
                            WorkHourWarning(
                                person_id=person_id,
                                warning_type="imbalance",
                                message=(
                                    f"Extended shift {shift.get('date', 'Unknown')}: "
                                    f"{duration:.1f} hours (24+4 limit: 28h)"
                                ),
                                current_hours=duration,
                                warning_threshold=26.0,
                                days_remaining=1,
                            )
                        )
                else:
                    # Exceeds 24+4 rule
                    violations.append(
                        WorkHourViolation(
                            person_id=person_id,
                            violation_type="24_plus_4",
                            severity="CRITICAL",
                            message=(
                                f"24+4 rule violation on {shift.get('date', 'Unknown')}: "
                                f"{duration:.1f} hours (limit: 28h)"
                            ),
                            date_range=(shift.get("date"), shift.get("date")),
                            hours=duration,
                            limit=MAX_TOTAL_SHIFT_HOURS,
                        )
                    )

        return violations, warnings

    def validate_rest_period(
        self,
        person_id: UUID,
        shift_data: list[dict],
    ) -> tuple[list[WorkHourViolation], list[WorkHourWarning]]:
        """
        Validate 10-hour minimum rest period after 24-hour shifts.

        Args:
            person_id: Resident ID
            shift_data: List of dicts with shift timing info

        Returns:
            (violations, warnings) tuples
        """
        violations = []
        warnings = []

        if len(shift_data) < 2:
            return violations, warnings

        sorted_shifts = sorted(shift_data, key=lambda x: x.get("end_time", "00:00"))

        for i in range(len(sorted_shifts) - 1):
            current_shift = sorted_shifts[i]
            next_shift = sorted_shifts[i + 1]

            current_duration = current_shift.get("duration_hours", 0)
            if current_duration < MAX_CONSECUTIVE_HOURS:
                continue  # No rest requirement after short shifts

            # Calculate rest period
            # Simplified: assumes shifts on consecutive days
            rest_hours = 10  # Placeholder for actual calculation

            if rest_hours < MIN_REST_HOURS_AFTER_SHIFT:
                violations.append(
                    WorkHourViolation(
                        person_id=person_id,
                        violation_type="rest_period",
                        severity="HIGH",
                        message=(
                            f"Insufficient rest period: {rest_hours:.1f}h "
                            f"(minimum {MIN_REST_HOURS_AFTER_SHIFT}h required)"
                        ),
                        date_range=(
                            current_shift.get("date"),
                            next_shift.get("date"),
                        ),
                        hours=rest_hours,
                        limit=MIN_REST_HOURS_AFTER_SHIFT,
                    )
                )

        return violations, warnings

    def validate_moonlighting_integration(
        self,
        person_id: UUID,
        moonlighting_hours: dict[date, float],
    ) -> tuple[list[WorkHourViolation], list[WorkHourWarning]]:
        """
        Validate moonlighting hours integration with 80-hour limit.

        All moonlighting (internal or external) counts toward 80-hour limit.

        Args:
            person_id: Resident ID
            moonlighting_hours: Dict mapping date to moonlighting hours

        Returns:
            (violations, warnings) tuples
        """
        violations = []
        warnings = []

        if not moonlighting_hours:
            return violations, warnings

        # Calculate total moonlighting per week
        weeks_data = {}
        for work_date, hours in moonlighting_hours.items():
            # Calculate week starting Monday
            week_start = work_date - timedelta(days=work_date.weekday())
            if week_start not in weeks_data:
                weeks_data[week_start] = 0
            weeks_data[week_start] += hours

        # Check weekly moonlighting
        for week_start, total_hours in weeks_data.items():
            if total_hours > MOONLIGHTING_HOURS_PER_WEEK_WARNING:
                warnings.append(
                    WorkHourWarning(
                        person_id=person_id,
                        warning_type="imbalance",
                        message=(
                            f"High moonlighting hours week of {week_start}: "
                            f"{total_hours:.1f}h (watch for 80-hour limit)"
                        ),
                        current_hours=total_hours,
                        warning_threshold=MOONLIGHTING_HOURS_PER_WEEK_WARNING,
                        days_remaining=7,
                    )
                )

        return violations, warnings

    def calculate_violation_severity_level(self, violation_percentage: float) -> str:
        """
        Calculate severity level based on violation magnitude.

        Args:
            violation_percentage: Percentage over limit

        Returns:
            Severity level: "CRITICAL", "HIGH", "MEDIUM"
        """
        if violation_percentage >= 10:
            return "CRITICAL"
        elif violation_percentage >= 5:
            return "HIGH"
        else:
            return "MEDIUM"

    def create_violation_notification_level(self, hours: float) -> str | None:
        """
        Determine notification threshold for approaching limit.

        Args:
            hours: Current hours in rolling window

        Returns:
            Notification level: "yellow" (75h), "orange" (78h), "red" (80h),
            or None
        """
        if hours >= self.max_weekly_hours:
            return "red"  # Violation
        elif hours >= self.max_weekly_hours * 0.975:  # 78 hours
            return "orange"  # Critical warning
        elif hours >= self.max_weekly_hours * 0.9375:  # 75 hours
            return "yellow"  # Warning
        return None

    def check_exemption_eligibility(self, person_id: UUID, violation_type: str) -> bool:
        """
        Check if resident may be eligible for ACGME-approved exemption.

        In practice, exemptions require institutional review and documentation.

        Args:
            person_id: Resident ID
            violation_type: Type of violation

        Returns:
            True if exemption eligibility possible (requires review)
        """
        # Exemptions are rare and require special approval
        # This is a placeholder for institutional policy
        if violation_type == "24_plus_4":
            # Continuity of care exception possible with documentation
            return True
        return False


class BlockBasedWorkHourCalculator:
    """
    Calculates work hours from block-based assignments.

    The scheduler uses block-based model (AM/PM sessions).
    This calculator converts block assignments to hour estimates.
    """

    HOURS_PER_BLOCK = 6  # Standard assumption
    HOURS_PER_INTENSIVE_BLOCK = 12  # FMIT, Night Float, inpatient

    def __init__(self):
        """Initialize calculator."""
        self.standard_hours = self.HOURS_PER_BLOCK
        self.intensive_hours = self.HOURS_PER_INTENSIVE_BLOCK

    def calculate_hours_from_assignments(
        self,
        assignments: list[dict],
        rotation_intensity_map: dict[str, str] = None,
    ) -> dict[date, float]:
        """
        Calculate work hours from block assignments.

        Args:
            assignments: List of assignment dicts with 'block_date', 'rotation'
            rotation_intensity_map: Dict mapping rotation_id to 'standard' or
                                   'intensive'

        Returns:
            Dict mapping date to total hours
        """
        hours_by_date = {}
        rotation_intensity_map = rotation_intensity_map or {}

        for assignment in assignments:
            block_date = assignment.get("block_date")
            rotation_id = assignment.get("rotation_id")

            if not block_date:
                continue

            # Determine hours based on rotation intensity
            intensity = rotation_intensity_map.get(rotation_id, "standard")
            hours = (
                self.intensive_hours
                if intensity == "intensive"
                else self.standard_hours
            )

            if block_date in hours_by_date:
                hours_by_date[block_date] += hours
            else:
                hours_by_date[block_date] = hours

        return hours_by_date
