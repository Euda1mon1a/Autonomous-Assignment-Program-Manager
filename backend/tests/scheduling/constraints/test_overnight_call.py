"""Tests for overnight call generation constraint."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.constraints.overnight_call import (
    OvernightCallGenerationConstraint,
    is_overnight_call_night,
)


class TestIsOvernightCallNight:
    """Test overnight call night detection."""

    def test_sunday_is_call_night(self):
        """Sunday should require overnight call."""
        # Find a Sunday in 2025
        sunday = date(2025, 1, 5)  # January 5, 2025 is a Sunday
        assert sunday.weekday() == 6  # Verify it's Sunday
        assert is_overnight_call_night(sunday) is True

    def test_monday_is_call_night(self):
        """Monday should require overnight call."""
        monday = date(2025, 1, 6)  # January 6, 2025 is a Monday
        assert monday.weekday() == 0  # Verify it's Monday
        assert is_overnight_call_night(monday) is True

    def test_tuesday_is_call_night(self):
        """Tuesday should require overnight call."""
        tuesday = date(2025, 1, 7)  # January 7, 2025 is a Tuesday
        assert tuesday.weekday() == 1  # Verify it's Tuesday
        assert is_overnight_call_night(tuesday) is True

    def test_wednesday_is_call_night(self):
        """Wednesday should require overnight call."""
        wednesday = date(2025, 1, 8)  # January 8, 2025 is a Wednesday
        assert wednesday.weekday() == 2  # Verify it's Wednesday
        assert is_overnight_call_night(wednesday) is True

    def test_thursday_is_call_night(self):
        """Thursday should require overnight call."""
        thursday = date(2025, 1, 9)  # January 9, 2025 is a Thursday
        assert thursday.weekday() == 3  # Verify it's Thursday
        assert is_overnight_call_night(thursday) is True

    def test_friday_is_not_call_night(self):
        """Friday is covered by FMIT - not a regular call night."""
        friday = date(2025, 1, 10)  # January 10, 2025 is a Friday
        assert friday.weekday() == 4  # Verify it's Friday
        assert is_overnight_call_night(friday) is False

    def test_saturday_is_not_call_night(self):
        """Saturday is covered by FMIT - not a regular call night."""
        saturday = date(2025, 1, 11)  # January 11, 2025 is a Saturday
        assert saturday.weekday() == 5  # Verify it's Saturday
        assert is_overnight_call_night(saturday) is False

    def test_full_week_coverage(self):
        """Test a full week to verify pattern."""
        # Start from Sunday January 5, 2025
        start_date = date(2025, 1, 5)
        expected = [
            True,  # Sun - call night
            True,  # Mon - call night
            True,  # Tue - call night
            True,  # Wed - call night
            True,  # Thu - call night
            False,  # Fri - FMIT handles
            False,  # Sat - FMIT handles
        ]

        for i, expected_result in enumerate(expected):
            test_date = start_date + timedelta(days=i)
            assert is_overnight_call_night(test_date) == expected_result, (
                f"Failed for {test_date} (weekday {test_date.weekday()})"
            )


class TestOvernightCallGenerationConstraint:
    """Test overnight call generation constraint initialization."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = OvernightCallGenerationConstraint()

        assert constraint.name == "OvernightCallGeneration"
        assert constraint.enabled is True
        # Should be a hard constraint
        assert hasattr(constraint, "add_to_cpsat")
        assert hasattr(constraint, "add_to_pulp")
        assert hasattr(constraint, "validate")

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = OvernightCallGenerationConstraint()

        # All constraints must implement these
        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))


class TestOvernightCallEligibility:
    """Test faculty eligibility logic."""

    def test_identify_fmit_weeks_empty_context(self):
        """Test FMIT week identification with empty context."""
        constraint = OvernightCallGenerationConstraint()

        # Create a minimal mock context
        class MockContext:
            existing_assignments = []
            templates = []
            blocks = []

        context = MockContext()
        fmit_weeks = constraint._identify_fmit_weeks(context)

        assert fmit_weeks == {}

    def test_is_overnight_call_night_boundary(self):
        """Test boundary between call nights and FMIT nights."""
        # Thursday night (last call night before FMIT)
        thursday = date(2025, 1, 9)
        assert is_overnight_call_night(thursday) is True

        # Friday night (FMIT starts)
        friday = date(2025, 1, 10)
        assert is_overnight_call_night(friday) is False

        # Sunday night (call nights resume)
        sunday = date(2025, 1, 12)
        assert is_overnight_call_night(sunday) is True


class TestOvernightCallValidation:
    """Test overnight call assignment validation."""

    def test_validate_empty_assignments(self):
        """Test validation with no call assignments."""
        constraint = OvernightCallGenerationConstraint()

        class MockContext:
            existing_assignments = []
            templates = []
            blocks = []
            faculty = []

        context = MockContext()
        result = constraint.validate([], context)

        # Should be satisfied when there are no blocks to check
        assert result.satisfied is True

    def test_constraint_priority(self):
        """Test constraint has appropriate priority."""
        from app.scheduling.constraints.base import ConstraintPriority

        constraint = OvernightCallGenerationConstraint()
        assert constraint.priority == ConstraintPriority.HIGH
