"""
Duty Hour Calculation Utilities.

Provides utilities for calculating and tracking duty hours according to ACGME rules.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID
from collections import defaultdict


class CallType(str, Enum):
    """Types of call duty."""
    IN_HOUSE = "in_house"        # Physical presence required
    HOME_CALL = "home_call"      # On-call from home
    NIGHT_FLOAT = "night_float"  # Dedicated night shift
    NONE = "none"                # No call duty


@dataclass
class DutyPeriod:
    """
    Represents a single duty period for a resident.

    A duty period is a continuous segment of duty, including all clinical and
    academic activities. It can include in-house call and may extend beyond
    the scheduled work hours.
    """
    person_id: UUID
    person_name: str
    start_datetime: datetime
    end_datetime: datetime
    hours: float
    call_type: CallType = CallType.NONE
    is_moonlighting: bool = False
    rotation_name: Optional[str] = None
    notes: Optional[str] = None

    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        delta = self.end_datetime - self.start_datetime
        return delta.total_seconds() / 3600

    @property
    def date(self) -> date:
        """Get the start date of this duty period."""
        return self.start_datetime.date()

    def overlaps_date(self, check_date: date) -> bool:
        """Check if this duty period overlaps with a given date."""
        start = self.start_datetime.date()
        end = self.end_datetime.date()
        return start <= check_date <= end

    def get_hours_on_date(self, check_date: date) -> float:
        """
        Get the number of hours worked on a specific date.

        For duty periods that span multiple days, this splits the hours
        proportionally across dates.
        """
        if not self.overlaps_date(check_date):
            return 0.0

        # Start and end of the target date
        date_start = datetime.combine(check_date, datetime.min.time())
        date_end = datetime.combine(check_date, datetime.max.time())

        # Overlap period
        overlap_start = max(self.start_datetime, date_start)
        overlap_end = min(self.end_datetime, date_end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_duration = (overlap_end - overlap_start).total_seconds() / 3600
        return overlap_duration


@dataclass
class WeeklyHours:
    """
    Aggregated duty hours for a week.

    Tracks total hours, call hours, and moonlighting separately.
    """
    person_id: UUID
    person_name: str
    week_start: date
    week_end: date
    total_hours: float = 0.0
    in_house_call_hours: float = 0.0
    home_call_hours: float = 0.0
    night_float_hours: float = 0.0
    moonlighting_hours: float = 0.0
    duty_periods: list[DutyPeriod] = field(default_factory=list)

    @property
    def clinical_hours(self) -> float:
        """Total clinical hours (excluding moonlighting)."""
        return self.total_hours - self.moonlighting_hours

    @property
    def combined_hours(self) -> float:
        """Combined clinical and moonlighting hours."""
        return self.total_hours

    def is_compliant(self, max_hours: float = 80.0) -> bool:
        """Check if weekly hours are compliant."""
        return self.clinical_hours <= max_hours

    def add_duty_period(self, period: DutyPeriod) -> None:
        """Add a duty period to this week's totals."""
        self.duty_periods.append(period)

        # Calculate hours that fall within this week
        for day_offset in range(7):
            current_date = self.week_start + timedelta(days=day_offset)
            if current_date > self.week_end:
                break

            hours_on_date = period.get_hours_on_date(current_date)

            if hours_on_date > 0:
                if period.is_moonlighting:
                    self.moonlighting_hours += hours_on_date
                    self.total_hours += hours_on_date
                else:
                    self.total_hours += hours_on_date

                    if period.call_type == CallType.IN_HOUSE:
                        self.in_house_call_hours += hours_on_date
                    elif period.call_type == CallType.HOME_CALL:
                        self.home_call_hours += hours_on_date
                    elif period.call_type == CallType.NIGHT_FLOAT:
                        self.night_float_hours += hours_on_date


class DutyHourCalculator:
    """
    Calculates duty hours from assignments.

    Converts block-based assignments into duty periods and aggregates
    hours by day, week, and month.
    """

    # Constants
    HOURS_PER_HALF_DAY = 6.0
    STANDARD_SHIFT_HOURS = 12.0
    EXTENDED_SHIFT_HOURS = 24.0
    MAX_CONTINUOUS_HOURS = 28.0  # 24 + 4 rule

    def __init__(self, timezone: str = "UTC"):
        """Initialize calculator with timezone."""
        self.timezone = timezone

    def assignments_to_duty_periods(
        self,
        assignments: list,
        blocks: list,
    ) -> list[DutyPeriod]:
        """
        Convert assignments to duty periods.

        Args:
            assignments: List of Assignment objects
            blocks: List of Block objects

        Returns:
            List of DutyPeriod objects
        """
        duty_periods = []

        # Create lookup for blocks
        block_dict = {b.id: b for b in blocks}

        for assignment in assignments:
            block = block_dict.get(assignment.block_id)
            if not block:
                continue

            # Determine shift hours based on block time
            if hasattr(block, 'time_of_day'):
                if block.time_of_day == 'AM':
                    start_hour = 8
                    duration = self.HOURS_PER_HALF_DAY
                elif block.time_of_day == 'PM':
                    start_hour = 14
                    duration = self.HOURS_PER_HALF_DAY
                else:  # Full day or overnight
                    start_hour = 8
                    duration = self.STANDARD_SHIFT_HOURS
            else:
                # Default to half-day calculation
                start_hour = 8
                duration = self.HOURS_PER_HALF_DAY

            # Create datetime for start of duty
            start_datetime = datetime.combine(
                block.date,
                datetime.min.time().replace(hour=start_hour)
            )
            end_datetime = start_datetime + timedelta(hours=duration)

            # Determine call type (would need additional metadata in real system)
            call_type = CallType.NONE

            # Get person information
            person = assignment.person if hasattr(assignment, 'person') else None
            person_name = person.name if person else "Unknown"
            rotation_name = assignment.activity_name if hasattr(assignment, 'activity_name') else None

            duty_period = DutyPeriod(
                person_id=assignment.person_id,
                person_name=person_name,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                hours=duration,
                call_type=call_type,
                is_moonlighting=False,
                rotation_name=rotation_name,
            )

            duty_periods.append(duty_period)

        return duty_periods

    def calculate_weekly_hours(
        self,
        duty_periods: list[DutyPeriod],
        start_date: date,
        end_date: date,
    ) -> dict[UUID, list[WeeklyHours]]:
        """
        Calculate weekly hours for all persons.

        Args:
            duty_periods: List of DutyPeriod objects
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Dictionary mapping person_id to list of WeeklyHours
        """
        # Group duty periods by person
        by_person = defaultdict(list)
        for period in duty_periods:
            by_person[period.person_id].append(period)

        # Calculate weekly hours for each person
        result = {}

        for person_id, periods in by_person.items():
            if not periods:
                continue

            person_name = periods[0].person_name
            weekly_hours_list = []

            # Iterate through weeks
            current_week_start = start_date
            while current_week_start <= end_date:
                week_end = min(current_week_start + timedelta(days=6), end_date)

                week_hours = WeeklyHours(
                    person_id=person_id,
                    person_name=person_name,
                    week_start=current_week_start,
                    week_end=week_end,
                )

                # Add duty periods that overlap this week
                for period in periods:
                    if period.overlaps_date(current_week_start) or \
                       period.overlaps_date(week_end) or \
                       (period.date < current_week_start and
                        period.end_datetime.date() > week_end):
                        week_hours.add_duty_period(period)

                weekly_hours_list.append(week_hours)
                current_week_start = week_end + timedelta(days=1)

            result[person_id] = weekly_hours_list

        return result

    def calculate_rolling_average(
        self,
        weekly_hours: list[WeeklyHours],
        window_weeks: int = 4,
    ) -> list[tuple[date, float]]:
        """
        Calculate rolling average hours over a window.

        Args:
            weekly_hours: List of WeeklyHours objects (sorted by week_start)
            window_weeks: Number of weeks in rolling window

        Returns:
            List of (date, average_hours) tuples
        """
        if not weekly_hours or len(weekly_hours) < window_weeks:
            return []

        rolling_averages = []

        for i in range(len(weekly_hours) - window_weeks + 1):
            window = weekly_hours[i:i + window_weeks]
            total_hours = sum(w.clinical_hours for w in window)
            avg_hours = total_hours / window_weeks
            window_start = window[0].week_start

            rolling_averages.append((window_start, avg_hours))

        return rolling_averages

    def calculate_monthly_hours(
        self,
        duty_periods: list[DutyPeriod],
    ) -> dict[tuple[UUID, int, int], float]:
        """
        Calculate monthly hours for each person.

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            Dictionary mapping (person_id, year, month) to total hours
        """
        monthly_hours = defaultdict(float)

        for period in duty_periods:
            if period.is_moonlighting:
                continue  # Don't count moonlighting in clinical hours

            # Add hours to each month this period touches
            current_date = period.start_datetime.date()
            end_date = period.end_datetime.date()

            while current_date <= end_date:
                hours_on_date = period.get_hours_on_date(current_date)
                key = (period.person_id, current_date.year, current_date.month)
                monthly_hours[key] += hours_on_date

                # Move to next day
                current_date += timedelta(days=1)

        return dict(monthly_hours)

    def calculate_consecutive_duty_days(
        self,
        duty_periods: list[DutyPeriod],
    ) -> dict[UUID, int]:
        """
        Calculate maximum consecutive duty days for each person.

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            Dictionary mapping person_id to max consecutive days
        """
        by_person = defaultdict(set)
        for period in duty_periods:
            by_person[period.person_id].add(period.date)

        max_consecutive = {}

        for person_id, duty_dates in by_person.items():
            if not duty_dates:
                max_consecutive[person_id] = 0
                continue

            sorted_dates = sorted(duty_dates)
            current_streak = 1
            max_streak = 1

            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1

            max_consecutive[person_id] = max_streak

        return max_consecutive

    def identify_call_frequency_violations(
        self,
        duty_periods: list[DutyPeriod],
        min_nights_between_calls: int = 3,
    ) -> dict[UUID, list[tuple[date, date]]]:
        """
        Identify violations of call frequency limits.

        ACGME requires no more than every 3rd night call.

        Args:
            duty_periods: List of DutyPeriod objects
            min_nights_between_calls: Minimum nights between in-house calls

        Returns:
            Dictionary mapping person_id to list of (call_date1, call_date2) violations
        """
        # Group in-house call periods by person
        by_person = defaultdict(list)
        for period in duty_periods:
            if period.call_type == CallType.IN_HOUSE:
                by_person[period.person_id].append(period.date)

        violations = {}

        for person_id, call_dates in by_person.items():
            sorted_dates = sorted(set(call_dates))
            person_violations = []

            for i in range(1, len(sorted_dates)):
                days_between = (sorted_dates[i] - sorted_dates[i-1]).days
                if days_between < min_nights_between_calls:
                    person_violations.append((sorted_dates[i-1], sorted_dates[i]))

            if person_violations:
                violations[person_id] = person_violations

        return violations

    def check_24_plus_4_rule(
        self,
        duty_periods: list[DutyPeriod],
    ) -> dict[UUID, list[DutyPeriod]]:
        """
        Check for violations of the 24+4 hour maximum shift rule.

        Residents may work up to 24 hours continuous duty, plus up to
        4 additional hours for transitions.

        Args:
            duty_periods: List of DutyPeriod objects

        Returns:
            Dictionary mapping person_id to list of violating DutyPeriod objects
        """
        violations = defaultdict(list)

        for period in duty_periods:
            if period.duration_hours > self.MAX_CONTINUOUS_HOURS:
                violations[period.person_id].append(period)

        return dict(violations)

    def check_minimum_time_off(
        self,
        duty_periods: list[DutyPeriod],
        min_hours_off: float = 14.0,
    ) -> dict[UUID, list[tuple[DutyPeriod, DutyPeriod, float]]]:
        """
        Check for violations of minimum time off between shifts.

        After 24+ hour duty, residents must have at least 14 hours off.
        After shorter duty, at least 8 hours off is recommended.

        Args:
            duty_periods: List of DutyPeriod objects
            min_hours_off: Minimum hours required off

        Returns:
            Dictionary mapping person_id to list of (period1, period2, hours_off)
        """
        # Group and sort by person
        by_person = defaultdict(list)
        for period in duty_periods:
            by_person[period.person_id].append(period)

        for person_id in by_person:
            by_person[person_id].sort(key=lambda p: p.start_datetime)

        violations = defaultdict(list)

        for person_id, periods in by_person.items():
            for i in range(1, len(periods)):
                prev_period = periods[i-1]
                curr_period = periods[i]

                # Calculate time off between shifts
                time_off = (curr_period.start_datetime - prev_period.end_datetime).total_seconds() / 3600

                # Check if violation based on previous shift length
                required_off = min_hours_off if prev_period.hours >= 24 else 8.0

                if time_off < required_off:
                    violations[person_id].append((prev_period, curr_period, time_off))

        return dict(violations)
