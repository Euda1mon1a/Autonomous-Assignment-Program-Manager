"""Tests for FMIT and faculty role constraints."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.constraints.fmit import (
    get_fmit_week_dates,
    is_sun_thurs,
    FMITWeekBlockingConstraint,
    FMITMandatoryCallConstraint,
    PostFMITRecoveryConstraint,
)
from app.scheduling.constraints.faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintResult,
    ConstraintViolation,
    SchedulingContext,
)


class TestFMITWeekDates:
    """Tests for FMIT week date calculation utility."""

    def test_friday_returns_same_week(self):
        """Test that Friday returns its own week."""
        friday = date(2025, 1, 3)  # Friday
        start, end = get_fmit_week_dates(friday)
        assert start == friday
        assert end == date(2025, 1, 9)  # Thursday

    def test_saturday_returns_current_week(self):
        """Test Saturday returns week starting previous Friday."""
        saturday = date(2025, 1, 4)  # Saturday
        start, end = get_fmit_week_dates(saturday)
        assert start == date(2025, 1, 3)  # Friday
        assert end == date(2025, 1, 9)  # Thursday

    def test_sunday_returns_current_week(self):
        """Test Sunday returns week starting previous Friday."""
        sunday = date(2025, 1, 5)  # Sunday
        start, end = get_fmit_week_dates(sunday)
        assert start == date(2025, 1, 3)  # Friday
        assert end == date(2025, 1, 9)  # Thursday

    def test_monday_returns_current_week(self):
        """Test Monday returns week starting previous Friday."""
        monday = date(2025, 1, 6)  # Monday
        start, end = get_fmit_week_dates(monday)
        assert start == date(2025, 1, 3)  # Friday
        assert end == date(2025, 1, 9)  # Thursday

    def test_thursday_returns_current_week(self):
        """Test Thursday (end of FMIT week) returns correct week."""
        thursday = date(2025, 1, 9)  # Thursday
        start, end = get_fmit_week_dates(thursday)
        assert start == date(2025, 1, 3)  # Friday
        assert end == thursday

    def test_week_span_is_7_days(self):
        """Test that FMIT week is exactly 7 days (Fri-Thurs)."""
        friday = date(2025, 1, 3)
        start, end = get_fmit_week_dates(friday)
        assert (end - start).days == 6  # Inclusive of both days = 7 days


class TestIsSunThurs:
    """Tests for Sun-Thurs check utility."""

    def test_sunday_is_sun_thurs(self):
        """Test Sunday is in Sun-Thurs range."""
        sunday = date(2025, 1, 5)  # Sunday
        assert is_sun_thurs(sunday) is True

    def test_monday_is_sun_thurs(self):
        """Test Monday is in Sun-Thurs range."""
        monday = date(2025, 1, 6)  # Monday
        assert is_sun_thurs(monday) is True

    def test_tuesday_is_sun_thurs(self):
        """Test Tuesday is in Sun-Thurs range."""
        tuesday = date(2025, 1, 7)  # Tuesday
        assert is_sun_thurs(tuesday) is True

    def test_wednesday_is_sun_thurs(self):
        """Test Wednesday is in Sun-Thurs range."""
        wednesday = date(2025, 1, 8)  # Wednesday
        assert is_sun_thurs(wednesday) is True

    def test_thursday_is_sun_thurs(self):
        """Test Thursday is in Sun-Thurs range."""
        thursday = date(2025, 1, 9)  # Thursday
        assert is_sun_thurs(thursday) is True

    def test_friday_is_not_sun_thurs(self):
        """Test Friday is NOT in Sun-Thurs range."""
        friday = date(2025, 1, 3)  # Friday
        assert is_sun_thurs(friday) is False

    def test_saturday_is_not_sun_thurs(self):
        """Test Saturday is NOT in Sun-Thurs range."""
        saturday = date(2025, 1, 4)  # Saturday
        assert is_sun_thurs(saturday) is False


class TestFMITWeekBlockingConstraint:
    """Tests for FMITWeekBlockingConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = FMITWeekBlockingConstraint()
        assert constraint.name == "FMITWeekBlocking"
        assert constraint.priority.value == 100  # CRITICAL

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = FMITWeekBlockingConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0


class TestFMITMandatoryCallConstraint:
    """Tests for FMITMandatoryCallConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = FMITMandatoryCallConstraint()
        assert constraint.name == "FMITMandatoryCall"
        assert constraint.priority.value == 100  # CRITICAL


class TestPostFMITRecoveryConstraint:
    """Tests for PostFMITRecoveryConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = PostFMITRecoveryConstraint()
        assert constraint.name == "PostFMITRecovery"
        assert constraint.priority.value == 75  # HIGH

    def test_recovery_friday_calculation(self):
        """Test that recovery Friday is day after FMIT Thursday."""
        # FMIT week: Fri Jan 3 - Thu Jan 9
        # Recovery Friday: Jan 10
        friday_start = date(2025, 1, 3)
        thursday_end = date(2025, 1, 9)
        recovery_friday = thursday_end + timedelta(days=1)
        assert recovery_friday == date(2025, 1, 10)
        assert recovery_friday.weekday() == 4  # Friday


class TestFacultyRoleClinicConstraint:
    """Tests for FacultyRoleClinicConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = FacultyRoleClinicConstraint()
        assert constraint.name == "FacultyRoleClinic"
        assert constraint.priority.value == 75  # HIGH

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = FacultyRoleClinicConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_get_week_start_monday(self):
        """Test _get_week_start returns Monday."""
        constraint = FacultyRoleClinicConstraint()
        # Wednesday Jan 8, 2025
        wednesday = date(2025, 1, 8)
        week_start = constraint._get_week_start(wednesday)
        assert week_start == date(2025, 1, 6)  # Monday
        assert week_start.weekday() == 0  # Monday

    def test_get_week_start_already_monday(self):
        """Test _get_week_start returns same day for Monday."""
        constraint = FacultyRoleClinicConstraint()
        monday = date(2025, 1, 6)
        week_start = constraint._get_week_start(monday)
        assert week_start == monday


class TestSMFacultyClinicConstraint:
    """Tests for SMFacultyClinicConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = SMFacultyClinicConstraint()
        assert constraint.name == "SMFacultyNoRegularClinic"
        assert constraint.priority.value == 75  # HIGH

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = SMFacultyClinicConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0


class TestFMITWeekEdgeCases:
    """Test edge cases for FMIT week calculations."""

    def test_year_boundary(self):
        """Test FMIT week spanning year boundary."""
        # If Dec 31 is in middle of FMIT week
        dec_31_2024 = date(2024, 12, 31)  # Tuesday
        start, end = get_fmit_week_dates(dec_31_2024)
        # Friday Dec 27, 2024 to Thursday Jan 2, 2025
        assert start == date(2024, 12, 27)
        assert end == date(2025, 1, 2)

    def test_leap_year(self):
        """Test FMIT week in leap year."""
        # Feb 29, 2024 was a Thursday
        leap_day = date(2024, 2, 29)
        start, end = get_fmit_week_dates(leap_day)
        assert start == date(2024, 2, 23)  # Friday
        assert end == leap_day  # Thursday (leap day)

    def test_consecutive_weeks(self):
        """Test consecutive FMIT weeks don't overlap."""
        # Week 1: Fri Jan 3 - Thu Jan 9
        week1_start, week1_end = get_fmit_week_dates(date(2025, 1, 5))

        # Week 2: Fri Jan 10 - Thu Jan 16
        week2_start, week2_end = get_fmit_week_dates(date(2025, 1, 12))

        # Week 1 end should be day before week 2 start
        assert week1_end + timedelta(days=1) == week2_start
