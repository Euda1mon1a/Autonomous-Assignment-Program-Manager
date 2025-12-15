"""
Advanced ACGME Compliance Validator.

Provides comprehensive validation against ACGME duty hour requirements:
- 80-hour weekly limit (averaged over 4 weeks)
- 24+4 hour maximum shift duration
- Minimum 14 hours off after 24-hour shifts (8 hours for shorter shifts)
- One day off per 7-day period
- Moonlighting hours tracking
- Call frequency limits (no more than every 3rd night)
- Night float rotation rules
- Home call vs in-house call differentiation
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from collections import defaultdict

from app.validators.duty_hours import (
    DutyHourCalculator,
    DutyPeriod,
    CallType,
    WeeklyHours,
)
from app.schemas.schedule import Violation


@dataclass
class ShiftViolation:
    """
    Represents a detailed shift-level violation.

    More granular than the basic Violation schema, includes shift-specific
    details like exact times, consecutive hours, and recovery periods.
    """
    person_id: UUID
    person_name: str
    violation_type: str
    severity: str
    date: date
    message: str
    duty_hours: Optional[float] = None
    consecutive_days: Optional[int] = None
    time_off_hours: Optional[float] = None
    shift_start: Optional[date] = None
    shift_end: Optional[date] = None
    details: dict = field(default_factory=dict)

    def to_violation(self) -> Violation:
        """Convert to standard Violation schema."""
        return Violation(
            type=self.violation_type,
            severity=self.severity,
            person_id=self.person_id,
            person_name=self.person_name,
            message=self.message,
            details=self.details,
        )


@dataclass
class ACGMEComplianceReport:
    """
    Comprehensive ACGME compliance report.

    Aggregates all validation results and provides summary statistics.
    """
    is_compliant: bool
    total_violations: int
    violations_by_type: dict[str, int] = field(default_factory=dict)
    violations_by_severity: dict[str, int] = field(default_factory=dict)
    shift_violations: list[ShiftViolation] = field(default_factory=list)
    person_summaries: dict[UUID, dict] = field(default_factory=dict)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    @property
    def critical_violations(self) -> list[ShiftViolation]:
        """Get all critical violations."""
        return [v for v in self.shift_violations if v.severity == "CRITICAL"]

    @property
    def high_violations(self) -> list[ShiftViolation]:
        """Get all high severity violations."""
        return [v for v in self.shift_violations if v.severity == "HIGH"]

    def get_violations_for_person(self, person_id: UUID) -> list[ShiftViolation]:
        """Get all violations for a specific person."""
        return [v for v in self.shift_violations if v.person_id == person_id]

    def to_standard_violations(self) -> list[Violation]:
        """Convert all shift violations to standard Violation objects."""
        return [v.to_violation() for v in self.shift_violations]


class AdvancedACGMEValidator:
    """
    Advanced ACGME compliance validator.

    Provides comprehensive validation beyond basic duty hour counting:
    - Detailed shift-level analysis
    - Call frequency tracking
    - Recovery period verification
    - Moonlighting integration
    - Night float special rules
    """

    # ACGME Constants
    MAX_WEEKLY_HOURS = 80.0
    ROLLING_WEEKS = 4
    MAX_SHIFT_HOURS = 24.0
    MAX_SHIFT_WITH_TRANSITION = 28.0  # 24 + 4 hours
    MIN_TIME_OFF_AFTER_24HR = 14.0
    MIN_TIME_OFF_STANDARD = 8.0
    MAX_CONSECUTIVE_DAYS = 6
    MIN_NIGHTS_BETWEEN_CALLS = 3
    MAX_NIGHT_FLOAT_CONSECUTIVE = 6  # Max consecutive night float shifts

    def __init__(self):
        """Initialize validator with duty hour calculator."""
        self.calculator = DutyHourCalculator()

    def validate_all(
        self,
        assignments: list,
        blocks: list,
        start_date: date,
        end_date: date,
    ) -> ACGMEComplianceReport:
        """
        Perform comprehensive ACGME validation.

        Args:
            assignments: List of Assignment objects
            blocks: List of Block objects
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            ACGMEComplianceReport with detailed findings
        """
        # Convert assignments to duty periods
        duty_periods = self.calculator.assignments_to_duty_periods(assignments, blocks)

        # Initialize report
        report = ACGMEComplianceReport(
            is_compliant=True,
            total_violations=0,
            period_start=start_date,
            period_end=end_date,
        )

        # Run all validation checks
        violations = []

        violations.extend(self.validate_80_hour_rule(duty_periods, start_date, end_date))
        violations.extend(self.validate_24_plus_4_rule(duty_periods))
        violations.extend(self.validate_minimum_time_off(duty_periods))
        violations.extend(self.validate_one_in_seven_rule(duty_periods, start_date, end_date))
        violations.extend(self.validate_call_frequency(duty_periods))
        violations.extend(self.validate_night_float_rules(duty_periods))

        # Populate report
        report.shift_violations = violations
        report.total_violations = len(violations)
        report.is_compliant = len(violations) == 0

        # Count by type and severity
        for v in violations:
            report.violations_by_type[v.violation_type] = \
                report.violations_by_type.get(v.violation_type, 0) + 1
            report.violations_by_severity[v.severity] = \
                report.violations_by_severity.get(v.severity, 0) + 1

        # Generate person summaries
        report.person_summaries = self._generate_person_summaries(
            duty_periods, violations, start_date, end_date
        )

        return report

    def validate_80_hour_rule(
        self,
        duty_periods: list[DutyPeriod],
        start_date: date,
        end_date: date,
    ) -> list[ShiftViolation]:
        """
        Validate 80-hour weekly limit (averaged over 4 weeks).

        Args:
            duty_periods: List of DutyPeriod objects
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        # Calculate weekly hours for all persons
        weekly_hours_by_person = self.calculator.calculate_weekly_hours(
            duty_periods, start_date, end_date
        )

        for person_id, weekly_hours_list in weekly_hours_by_person.items():
            if len(weekly_hours_list) < self.ROLLING_WEEKS:
                continue

            person_name = weekly_hours_list[0].person_name

            # Calculate rolling 4-week averages
            rolling_averages = self.calculator.calculate_rolling_average(
                weekly_hours_list, self.ROLLING_WEEKS
            )

            for window_start, avg_hours in rolling_averages:
                if avg_hours > self.MAX_WEEKLY_HOURS:
                    window_end = window_start + timedelta(days=27)

                    violation = ShiftViolation(
                        person_id=person_id,
                        person_name=person_name,
                        violation_type="80_HOUR_VIOLATION",
                        severity="CRITICAL",
                        date=window_start,
                        message=f"{person_name}: {avg_hours:.1f} hours/week average "
                                f"(limit: {self.MAX_WEEKLY_HOURS})",
                        duty_hours=avg_hours,
                        shift_start=window_start,
                        shift_end=window_end,
                        details={
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                            "average_weekly_hours": avg_hours,
                            "limit": self.MAX_WEEKLY_HOURS,
                            "excess_hours": avg_hours - self.MAX_WEEKLY_HOURS,
                        },
                    )
                    violations.append(violation)
                    # Only report first violation per person
                    break

        return violations

    def validate_24_plus_4_rule(
        self,
        duty_periods: list[DutyPeriod],
    ) -> list[ShiftViolation]:
        """
        Validate 24+4 hour maximum shift rule.

        Residents may work maximum 24 hours continuous duty, plus up to
        4 additional hours for transitions (total 28 hours).

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        violating_periods = self.calculator.check_24_plus_4_rule(duty_periods)

        for person_id, periods in violating_periods.items():
            for period in periods:
                violation = ShiftViolation(
                    person_id=person_id,
                    person_name=period.person_name,
                    violation_type="24_PLUS_4_VIOLATION",
                    severity="CRITICAL",
                    date=period.date,
                    message=f"{period.person_name}: {period.duration_hours:.1f} hour shift "
                            f"exceeds 28-hour limit (24+4 rule)",
                    duty_hours=period.duration_hours,
                    shift_start=period.date,
                    shift_end=period.end_datetime.date(),
                    details={
                        "shift_hours": period.duration_hours,
                        "limit": self.MAX_SHIFT_WITH_TRANSITION,
                        "excess_hours": period.duration_hours - self.MAX_SHIFT_WITH_TRANSITION,
                        "start_datetime": period.start_datetime.isoformat(),
                        "end_datetime": period.end_datetime.isoformat(),
                    },
                )
                violations.append(violation)

        return violations

    def validate_minimum_time_off(
        self,
        duty_periods: list[DutyPeriod],
    ) -> list[ShiftViolation]:
        """
        Validate minimum time off between shifts.

        After 24-hour duty: minimum 14 hours off
        After shorter duty: minimum 8 hours off (recommended)

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        # Check both 14-hour and 8-hour requirements
        for min_hours, severity in [(self.MIN_TIME_OFF_AFTER_24HR, "CRITICAL"),
                                     (self.MIN_TIME_OFF_STANDARD, "HIGH")]:
            violating_sequences = self.calculator.check_minimum_time_off(
                duty_periods, min_hours
            )

            for person_id, sequences in violating_sequences.items():
                for prev_period, curr_period, time_off in sequences:
                    # Only report 14-hour violations for 24+ hour shifts
                    if min_hours == self.MIN_TIME_OFF_AFTER_24HR and prev_period.hours < 24:
                        continue

                    # Only report 8-hour violations for <24 hour shifts
                    if min_hours == self.MIN_TIME_OFF_STANDARD and prev_period.hours >= 24:
                        continue

                    violation = ShiftViolation(
                        person_id=person_id,
                        person_name=prev_period.person_name,
                        violation_type="MINIMUM_TIME_OFF_VIOLATION",
                        severity=severity,
                        date=curr_period.date,
                        message=f"{prev_period.person_name}: Only {time_off:.1f} hours off "
                                f"between shifts (required: {min_hours:.1f})",
                        time_off_hours=time_off,
                        details={
                            "time_off_hours": time_off,
                            "required_hours": min_hours,
                            "previous_shift_end": prev_period.end_datetime.isoformat(),
                            "next_shift_start": curr_period.start_datetime.isoformat(),
                            "previous_shift_duration": prev_period.hours,
                        },
                    )
                    violations.append(violation)

        return violations

    def validate_one_in_seven_rule(
        self,
        duty_periods: list[DutyPeriod],
        start_date: date,
        end_date: date,
    ) -> list[ShiftViolation]:
        """
        Validate one-in-seven rule (maximum 6 consecutive duty days).

        Residents must have at least one 24-hour period off every 7 days
        (averaged over 4 weeks).

        Args:
            duty_periods: List of DutyPeriod objects
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        max_consecutive = self.calculator.calculate_consecutive_duty_days(duty_periods)

        for person_id, consecutive_days in max_consecutive.items():
            if consecutive_days > self.MAX_CONSECUTIVE_DAYS:
                # Find the person's name
                person_name = "Unknown"
                for period in duty_periods:
                    if period.person_id == person_id:
                        person_name = period.person_name
                        break

                violation = ShiftViolation(
                    person_id=person_id,
                    person_name=person_name,
                    violation_type="1_IN_7_VIOLATION",
                    severity="HIGH",
                    date=start_date,
                    message=f"{person_name}: {consecutive_days} consecutive duty days "
                            f"(limit: {self.MAX_CONSECUTIVE_DAYS})",
                    consecutive_days=consecutive_days,
                    details={
                        "consecutive_days": consecutive_days,
                        "limit": self.MAX_CONSECUTIVE_DAYS,
                        "excess_days": consecutive_days - self.MAX_CONSECUTIVE_DAYS,
                    },
                )
                violations.append(violation)

        return violations

    def validate_call_frequency(
        self,
        duty_periods: list[DutyPeriod],
    ) -> list[ShiftViolation]:
        """
        Validate call frequency limits.

        In-house call should be no more frequent than every 3rd night
        (averaged over 4 weeks).

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        call_violations = self.calculator.identify_call_frequency_violations(
            duty_periods, self.MIN_NIGHTS_BETWEEN_CALLS
        )

        for person_id, violation_pairs in call_violations.items():
            # Find person name
            person_name = "Unknown"
            for period in duty_periods:
                if period.person_id == person_id:
                    person_name = period.person_name
                    break

            for call_date1, call_date2 in violation_pairs:
                days_between = (call_date2 - call_date1).days

                violation = ShiftViolation(
                    person_id=person_id,
                    person_name=person_name,
                    violation_type="CALL_FREQUENCY_VIOLATION",
                    severity="HIGH",
                    date=call_date2,
                    message=f"{person_name}: In-house call too frequent - "
                            f"only {days_between} days between calls "
                            f"(minimum: {self.MIN_NIGHTS_BETWEEN_CALLS})",
                    details={
                        "first_call_date": call_date1.isoformat(),
                        "second_call_date": call_date2.isoformat(),
                        "days_between": days_between,
                        "minimum_days": self.MIN_NIGHTS_BETWEEN_CALLS,
                    },
                )
                violations.append(violation)

        return violations

    def validate_night_float_rules(
        self,
        duty_periods: list[DutyPeriod],
    ) -> list[ShiftViolation]:
        """
        Validate night float rotation rules.

        Night float rotations should not exceed 6 consecutive shifts
        to prevent circadian disruption.

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        # Group night float periods by person
        by_person = defaultdict(list)
        for period in duty_periods:
            if period.call_type == CallType.NIGHT_FLOAT:
                by_person[period.person_id].append(period)

        for person_id, periods in by_person.items():
            if not periods:
                continue

            # Sort by date
            sorted_periods = sorted(periods, key=lambda p: p.date)
            person_name = sorted_periods[0].person_name

            # Find consecutive night float stretches
            consecutive_count = 1
            max_consecutive = 1

            for i in range(1, len(sorted_periods)):
                if (sorted_periods[i].date - sorted_periods[i-1].date).days == 1:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 1

            if max_consecutive > self.MAX_NIGHT_FLOAT_CONSECUTIVE:
                violation = ShiftViolation(
                    person_id=person_id,
                    person_name=person_name,
                    violation_type="NIGHT_FLOAT_VIOLATION",
                    severity="MEDIUM",
                    date=sorted_periods[0].date,
                    message=f"{person_name}: {max_consecutive} consecutive night float shifts "
                            f"(recommended max: {self.MAX_NIGHT_FLOAT_CONSECUTIVE})",
                    consecutive_days=max_consecutive,
                    details={
                        "consecutive_shifts": max_consecutive,
                        "recommended_max": self.MAX_NIGHT_FLOAT_CONSECUTIVE,
                        "excess_shifts": max_consecutive - self.MAX_NIGHT_FLOAT_CONSECUTIVE,
                    },
                )
                violations.append(violation)

        return violations

    def validate_moonlighting_hours(
        self,
        duty_periods: list[DutyPeriod],
        start_date: date,
        end_date: date,
        max_moonlighting_per_week: float = 16.0,
    ) -> list[ShiftViolation]:
        """
        Validate moonlighting hours.

        Moonlighting hours should be tracked and limited. When combined
        with clinical duty, total hours should not exceed 80/week.

        Args:
            duty_periods: List of DutyPeriod objects
            start_date: Start of validation period
            end_date: End of validation period
            max_moonlighting_per_week: Maximum moonlighting hours per week

        Returns:
            List of ShiftViolation objects
        """
        violations = []

        weekly_hours_by_person = self.calculator.calculate_weekly_hours(
            duty_periods, start_date, end_date
        )

        for person_id, weekly_hours_list in weekly_hours_by_person.items():
            person_name = weekly_hours_list[0].person_name if weekly_hours_list else "Unknown"

            for week_hours in weekly_hours_list:
                # Check moonlighting limits
                if week_hours.moonlighting_hours > max_moonlighting_per_week:
                    violation = ShiftViolation(
                        person_id=person_id,
                        person_name=person_name,
                        violation_type="MOONLIGHTING_VIOLATION",
                        severity="MEDIUM",
                        date=week_hours.week_start,
                        message=f"{person_name}: {week_hours.moonlighting_hours:.1f} "
                                f"moonlighting hours (limit: {max_moonlighting_per_week})",
                        duty_hours=week_hours.moonlighting_hours,
                        details={
                            "moonlighting_hours": week_hours.moonlighting_hours,
                            "limit": max_moonlighting_per_week,
                            "week_start": week_hours.week_start.isoformat(),
                        },
                    )
                    violations.append(violation)

                # Check combined hours
                if week_hours.combined_hours > self.MAX_WEEKLY_HOURS:
                    violation = ShiftViolation(
                        person_id=person_id,
                        person_name=person_name,
                        violation_type="COMBINED_HOURS_VIOLATION",
                        severity="CRITICAL",
                        date=week_hours.week_start,
                        message=f"{person_name}: {week_hours.combined_hours:.1f} "
                                f"combined hours (clinical + moonlighting) exceeds "
                                f"{self.MAX_WEEKLY_HOURS} hour limit",
                        duty_hours=week_hours.combined_hours,
                        details={
                            "clinical_hours": week_hours.clinical_hours,
                            "moonlighting_hours": week_hours.moonlighting_hours,
                            "combined_hours": week_hours.combined_hours,
                            "limit": self.MAX_WEEKLY_HOURS,
                            "week_start": week_hours.week_start.isoformat(),
                        },
                    )
                    violations.append(violation)

        return violations

    def _generate_person_summaries(
        self,
        duty_periods: list[DutyPeriod],
        violations: list[ShiftViolation],
        start_date: date,
        end_date: date,
    ) -> dict[UUID, dict]:
        """
        Generate summary statistics for each person.

        Args:
            duty_periods: List of DutyPeriod objects
            violations: List of ShiftViolation objects
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Dictionary mapping person_id to summary statistics
        """
        summaries = {}

        # Group duty periods by person
        by_person = defaultdict(list)
        for period in duty_periods:
            by_person[period.person_id].append(period)

        # Calculate statistics for each person
        for person_id, periods in by_person.items():
            if not periods:
                continue

            person_name = periods[0].person_name

            # Calculate weekly hours
            weekly_hours_list = self.calculator.calculate_weekly_hours(
                periods, start_date, end_date
            )[person_id]

            total_hours = sum(w.clinical_hours for w in weekly_hours_list)
            avg_weekly_hours = total_hours / len(weekly_hours_list) if weekly_hours_list else 0

            # Get violations for this person
            person_violations = [v for v in violations if v.person_id == person_id]

            # Calculate max consecutive days
            max_consecutive = self.calculator.calculate_consecutive_duty_days(periods)

            summaries[person_id] = {
                "person_name": person_name,
                "total_duty_hours": total_hours,
                "average_weekly_hours": avg_weekly_hours,
                "total_duty_periods": len(periods),
                "max_consecutive_days": max_consecutive.get(person_id, 0),
                "total_violations": len(person_violations),
                "critical_violations": len([v for v in person_violations if v.severity == "CRITICAL"]),
                "high_violations": len([v for v in person_violations if v.severity == "HIGH"]),
                "medium_violations": len([v for v in person_violations if v.severity == "MEDIUM"]),
                "is_compliant": len(person_violations) == 0,
            }

        return summaries
