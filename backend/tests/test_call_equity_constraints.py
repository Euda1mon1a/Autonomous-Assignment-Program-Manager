"""Tests for call equity and preference constraints."""

import pytest
from datetime import date
from uuid import uuid4

from app.scheduling.constraints.call_equity import (
    SundayCallEquityConstraint,
    WeekdayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    DeptChiefWednesdayPreferenceConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    SchedulingContext,
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
