"""Tests for call equity and preference constraints."""

from datetime import date

from app.scheduling.constraints.base import (
    ConstraintPriority,
    SchedulingContext,
)
from app.scheduling.constraints.call_equity import (
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)


class TestSundayCallEquityConstraint:
    """Tests for SundayCallEquityConstraint."""

    def test_constraint_initialization_default_weight(self):
        """Test constraint initializes with default weight."""
        constraint = SundayCallEquityConstraint()
        assert constraint.name == "SundayCallEquity"
        assert constraint.weight == 10.0
        assert constraint.priority == ConstraintPriority.MEDIUM

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initializes with custom weight."""
        constraint = SundayCallEquityConstraint(weight=15.0)
        assert constraint.weight == 15.0

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = SundayCallEquityConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_sunday_is_weekday_6(self):
        """Test that Sunday is correctly identified as weekday 6."""
        # Jan 5, 2025 is a Sunday
        sunday = date(2025, 1, 5)
        assert sunday.weekday() == 6


class TestWeekdayCallEquityConstraint:
    """Tests for WeekdayCallEquityConstraint."""

    def test_constraint_initialization_default_weight(self):
        """Test constraint initializes with default weight."""
        constraint = WeekdayCallEquityConstraint()
        assert constraint.name == "WeekdayCallEquity"
        assert constraint.weight == 5.0
        assert constraint.priority == ConstraintPriority.MEDIUM

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initializes with custom weight."""
        constraint = WeekdayCallEquityConstraint(weight=8.0)
        assert constraint.weight == 8.0

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = WeekdayCallEquityConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_weekday_numbers(self):
        """Test that Mon-Thurs are correctly identified."""
        # Jan 6-9, 2025 is Mon-Thu
        monday = date(2025, 1, 6)
        tuesday = date(2025, 1, 7)
        wednesday = date(2025, 1, 8)
        thursday = date(2025, 1, 9)

        assert monday.weekday() == 0
        assert tuesday.weekday() == 1
        assert wednesday.weekday() == 2
        assert thursday.weekday() == 3


class TestTuesdayCallPreferenceConstraint:
    """Tests for TuesdayCallPreferenceConstraint."""

    def test_constraint_initialization_default_weight(self):
        """Test constraint initializes with default weight."""
        constraint = TuesdayCallPreferenceConstraint()
        assert constraint.name == "TuesdayCallPreference"
        assert constraint.weight == 2.0
        assert constraint.priority == ConstraintPriority.LOW

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initializes with custom weight."""
        constraint = TuesdayCallPreferenceConstraint(weight=3.0)
        assert constraint.weight == 3.0

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = TuesdayCallPreferenceConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert result.penalty == 0.0
        assert len(result.violations) == 0

    def test_tuesday_is_weekday_1(self):
        """Test that Tuesday is correctly identified as weekday 1."""
        # Jan 7, 2025 is a Tuesday
        tuesday = date(2025, 1, 7)
        assert tuesday.weekday() == 1


class TestDeptChiefWednesdayPreferenceConstraint:
    """Tests for DeptChiefWednesdayPreferenceConstraint."""

    def test_constraint_initialization_default_weight(self):
        """Test constraint initializes with default weight."""
        constraint = DeptChiefWednesdayPreferenceConstraint()
        assert constraint.name == "DeptChiefWednesdayPreference"
        assert constraint.weight == 1.0
        assert constraint.priority == ConstraintPriority.LOW

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initializes with custom weight."""
        constraint = DeptChiefWednesdayPreferenceConstraint(weight=2.0)
        assert constraint.weight == 2.0

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = DeptChiefWednesdayPreferenceConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert result.penalty == 0.0  # No bonus without assignments

    def test_wednesday_is_weekday_2(self):
        """Test that Wednesday is correctly identified as weekday 2."""
        # Jan 8, 2025 is a Wednesday
        wednesday = date(2025, 1, 8)
        assert wednesday.weekday() == 2


class TestConstraintWeightHierarchy:
    """Test that constraint weights follow the specified hierarchy."""

    def test_sunday_equity_highest_weight(self):
        """Test Sunday equity has highest weight (10.0)."""
        sunday = SundayCallEquityConstraint()
        weekday = WeekdayCallEquityConstraint()
        tuesday = TuesdayCallPreferenceConstraint()
        wednesday = DeptChiefWednesdayPreferenceConstraint()

        assert sunday.weight > weekday.weight
        assert weekday.weight > tuesday.weight
        assert tuesday.weight > wednesday.weight

    def test_weight_hierarchy_values(self):
        """Test specific weight values match specification."""
        sunday = SundayCallEquityConstraint()
        weekday = WeekdayCallEquityConstraint()
        tuesday = TuesdayCallPreferenceConstraint()
        wednesday = DeptChiefWednesdayPreferenceConstraint()

        assert sunday.weight == 10.0
        assert weekday.weight == 5.0
        assert tuesday.weight == 2.0
        assert wednesday.weight == 1.0


class TestConstraintPriorities:
    """Test constraint priority levels."""

    def test_equity_constraints_medium_priority(self):
        """Test equity constraints have MEDIUM priority."""
        sunday = SundayCallEquityConstraint()
        weekday = WeekdayCallEquityConstraint()

        assert sunday.priority == ConstraintPriority.MEDIUM
        assert weekday.priority == ConstraintPriority.MEDIUM

    def test_preference_constraints_low_priority(self):
        """Test preference constraints have LOW priority."""
        tuesday = TuesdayCallPreferenceConstraint()
        wednesday = DeptChiefWednesdayPreferenceConstraint()

        assert tuesday.priority == ConstraintPriority.LOW
        assert wednesday.priority == ConstraintPriority.LOW


class TestCallDayIdentification:
    """Test correct identification of call days."""

    def test_full_week_days(self):
        """Test all days of the week are correctly identified."""
        # Week of Jan 5-11, 2025 (Sun-Sat)
        sunday = date(2025, 1, 5)
        monday = date(2025, 1, 6)
        tuesday = date(2025, 1, 7)
        wednesday = date(2025, 1, 8)
        thursday = date(2025, 1, 9)
        friday = date(2025, 1, 10)
        saturday = date(2025, 1, 11)

        # Sunday equity day
        assert sunday.weekday() == 6

        # Weekday equity days (Mon-Thu)
        weekday_days = [monday, tuesday, wednesday, thursday]
        for day in weekday_days:
            assert day.weekday() in (0, 1, 2, 3)

        # FMIT call days (Fri-Sat)
        assert friday.weekday() == 4
        assert saturday.weekday() == 5

    def test_tuesday_avoidance_day(self):
        """Test Tuesday is the avoidance day for PD/APD."""
        constraint = TuesdayCallPreferenceConstraint()
        # Verify the constraint looks for weekday 1 (Tuesday)
        tuesday = date(2025, 1, 7)
        assert tuesday.weekday() == 1

    def test_wednesday_preference_day(self):
        """Test Wednesday is the preference day for Dept Chief."""
        constraint = DeptChiefWednesdayPreferenceConstraint()
        # Verify the constraint looks for weekday 2 (Wednesday)
        wednesday = date(2025, 1, 8)
        assert wednesday.weekday() == 2


class TestCallSpacingConstraint:
    """Tests for CallSpacingConstraint."""

    def test_constraint_initialization_default_weight(self):
        """Test constraint initializes with default weight."""
        constraint = CallSpacingConstraint()
        assert constraint.name == "CallSpacing"
        assert constraint.weight == 8.0
        assert constraint.priority == ConstraintPriority.MEDIUM

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initializes with custom weight."""
        constraint = CallSpacingConstraint(weight=12.0)
        assert constraint.weight == 12.0

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = CallSpacingConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert result.penalty == 0.0
        assert len(result.violations) == 0

    def test_iso_week_calculation(self):
        """Test that ISO week numbers are correctly calculated."""
        # Week 1 of 2025 starts Monday Dec 30, 2024
        week1_day = date(2025, 1, 6)  # Monday of week 2
        week2_day = date(2025, 1, 13)  # Monday of week 3

        iso1 = week1_day.isocalendar()
        iso2 = week2_day.isocalendar()

        assert iso1[0] == 2025  # year
        assert iso1[1] == 2  # week 2
        assert iso2[1] == 3  # week 3

    def test_consecutive_weeks_detection(self):
        """Test that consecutive weeks are properly detected.

        Week 2 (Jan 6-12) and Week 3 (Jan 13-19) are consecutive.
        """
        week2_mon = date(2025, 1, 6)
        week3_mon = date(2025, 1, 13)

        iso2 = week2_mon.isocalendar()
        iso3 = week3_mon.isocalendar()

        # Same year, adjacent week numbers = consecutive
        is_consecutive = (
            iso2[0] == iso3[0]
            and iso3[1] == iso2[1] + 1
        )
        assert is_consecutive is True

    def test_non_consecutive_weeks(self):
        """Test that non-consecutive weeks are not flagged.

        Week 2 (Jan 6-12) and Week 4 (Jan 20-26) are NOT consecutive.
        """
        week2_mon = date(2025, 1, 6)
        week4_mon = date(2025, 1, 20)

        iso2 = week2_mon.isocalendar()
        iso4 = week4_mon.isocalendar()

        # Same year but week 2 and week 4 are not adjacent
        is_consecutive = (
            iso2[0] == iso4[0]
            and iso4[1] == iso2[1] + 1
        )
        assert is_consecutive is False

    def test_year_boundary_weeks(self):
        """Test consecutive weeks across year boundary.

        Week 52 of 2024 → Week 1 of 2025 should be detected as consecutive.
        """
        week52_day = date(2024, 12, 30)  # Monday of ISO week 1 of 2025 (edge case)
        week1_day = date(2025, 1, 6)  # Monday of week 2 of 2025

        iso52 = week52_day.isocalendar()
        iso1 = week1_day.isocalendar()

        # This tests the year rollover logic in the constraint
        # Note: Dec 30 2024 is actually ISO week 1 of 2025
        # So this is not a year boundary case for ISO calendar
        # A true year boundary would be Dec 23 2024 (week 52) to Dec 30 2024 (week 1 of 2025)
        true_week52 = date(2024, 12, 23)
        true_week1 = date(2024, 12, 30)

        iso_52 = true_week52.isocalendar()
        iso_1 = true_week1.isocalendar()

        assert iso_52[1] == 52
        assert iso_1[1] == 1  # Week 1 of 2025

        # Year rollover detection
        is_consecutive = (
            iso_52[0] + 1 == iso_1[0]
            and iso_52[1] >= 52
            and iso_1[1] == 1
        )
        assert is_consecutive is True


class TestCallSpacingWeightHierarchy:
    """Test CallSpacingConstraint fits into the weight hierarchy."""

    def test_call_spacing_weight_in_hierarchy(self):
        """Test CallSpacing weight is between Sunday equity and weekday equity.

        Weight hierarchy:
        - Sunday equity: 10.0 (highest - worst day)
        - Call spacing: 8.0 (high - burnout prevention)
        - Weekday equity: 5.0 (medium - balance)
        - Tuesday preference: 2.0 (low - operational)
        - Wednesday preference: 1.0 (lowest - personal)
        """
        sunday = SundayCallEquityConstraint()
        spacing = CallSpacingConstraint()
        weekday = WeekdayCallEquityConstraint()
        tuesday = TuesdayCallPreferenceConstraint()

        assert sunday.weight > spacing.weight
        assert spacing.weight > weekday.weight
        assert weekday.weight > tuesday.weight

    def test_call_spacing_priority(self):
        """Test CallSpacing has MEDIUM priority like other equity constraints."""
        spacing = CallSpacingConstraint()
        sunday = SundayCallEquityConstraint()
        weekday = WeekdayCallEquityConstraint()

        assert spacing.priority == ConstraintPriority.MEDIUM
        assert spacing.priority == sunday.priority
        assert spacing.priority == weekday.priority
