"""
Tests for DOW convention in FacultyWeeklyTemplateConstraint.

Verifies that faculty_weekly_templates use Python weekday convention (0=Monday, 6=Sunday),
NOT PG EXTRACT(DOW) convention (0=Sunday, 6=Saturday).

See docs/architecture/DOW_CONVENTION_BUG.md for full reference.
"""

from datetime import date
from uuid import uuid4

import pytest

from app.scheduling.constraints.faculty_weekly_template import (
    FacultyWeeklyTemplateConstraint,
)


@pytest.fixture
def constraint():
    """Create a constraint instance with test templates."""
    return FacultyWeeklyTemplateConstraint()


class TestDOWConvention:
    """Verify Python weekday convention in template lookups."""

    def test_monday_is_zero(self):
        """date(2026, 5, 11) is a Monday → weekday() == 0."""
        d = date(2026, 5, 11)
        assert d.weekday() == 0, "Monday should be Python weekday 0"

    def test_friday_is_four(self):
        """date(2026, 5, 15) is a Friday → weekday() == 4."""
        d = date(2026, 5, 15)
        assert d.weekday() == 4, "Friday should be Python weekday 4"

    def test_saturday_is_five(self):
        """date(2026, 5, 16) is a Saturday → weekday() == 5."""
        d = date(2026, 5, 16)
        assert d.weekday() == 5, "Saturday should be Python weekday 5"

    def test_sunday_is_six(self):
        """date(2026, 5, 17) is a Sunday → weekday() == 6."""
        d = date(2026, 5, 17)
        assert d.weekday() == 6, "Sunday should be Python weekday 6"


class TestEffectiveSlotLookup:
    """Verify _get_effective_slot matches on Python weekday, not PG DOW."""

    def test_friday_template_matches_friday_date(self):
        """Template with day_of_week=4 (Python Friday) matches a Friday date."""
        constraint = FacultyWeeklyTemplateConstraint()
        person_id = uuid4()
        activity_id = uuid4()

        # Manually inject a template for Friday (Python weekday 4)
        constraint._templates = {
            person_id: [
                {
                    "day_of_week": 4,  # Python weekday: Friday
                    "time_of_day": "AM",
                    "week_number": None,
                    "activity_id": activity_id,
                    "is_locked": True,
                    "priority": 80,
                }
            ]
        }
        constraint._overrides = {}
        constraint._effective_cache = {}

        # Friday 2026-05-15
        friday = date(2026, 5, 15)
        assert friday.weekday() == 4

        result = constraint._get_effective_slot(
            person_id, friday, friday.weekday(), "AM", 1
        )
        assert result is not None
        assert result["activity_id"] == activity_id

    def test_friday_template_does_not_match_thursday(self):
        """Template with day_of_week=4 (Friday) does NOT match Thursday."""
        constraint = FacultyWeeklyTemplateConstraint()
        person_id = uuid4()

        constraint._templates = {
            person_id: [
                {
                    "day_of_week": 4,
                    "time_of_day": "AM",
                    "week_number": None,
                    "activity_id": uuid4(),
                    "is_locked": True,
                    "priority": 80,
                }
            ]
        }
        constraint._overrides = {}
        constraint._effective_cache = {}

        # Thursday 2026-05-14
        thursday = date(2026, 5, 14)
        assert thursday.weekday() == 3

        result = constraint._get_effective_slot(
            person_id, thursday, thursday.weekday(), "AM", 1
        )
        assert result is None

    def test_monday_template_does_not_match_sunday(self):
        """Template with day_of_week=0 (Python Monday) does NOT match Sunday.

        This is the core regression test: under the old PG DOW convention,
        day_of_week=0 would mean Sunday. Under Python weekday, it means Monday.
        """
        constraint = FacultyWeeklyTemplateConstraint()
        person_id = uuid4()

        constraint._templates = {
            person_id: [
                {
                    "day_of_week": 0,  # Python weekday: Monday
                    "time_of_day": "AM",
                    "week_number": None,
                    "activity_id": uuid4(),
                    "is_locked": True,
                    "priority": 80,
                }
            ]
        }
        constraint._overrides = {}
        constraint._effective_cache = {}

        # Sunday 2026-05-17
        sunday = date(2026, 5, 17)
        assert sunday.weekday() == 6

        result = constraint._get_effective_slot(
            person_id, sunday, sunday.weekday(), "AM", 1
        )
        assert result is None, "Monday template (DOW=0) should NOT match Sunday"

    def test_monday_template_matches_monday(self):
        """Template with day_of_week=0 matches Monday."""
        constraint = FacultyWeeklyTemplateConstraint()
        person_id = uuid4()
        activity_id = uuid4()

        constraint._templates = {
            person_id: [
                {
                    "day_of_week": 0,
                    "time_of_day": "AM",
                    "week_number": None,
                    "activity_id": activity_id,
                    "is_locked": True,
                    "priority": 80,
                }
            ]
        }
        constraint._overrides = {}
        constraint._effective_cache = {}

        # Monday 2026-05-11
        monday = date(2026, 5, 11)
        assert monday.weekday() == 0

        result = constraint._get_effective_slot(
            person_id, monday, monday.weekday(), "AM", 1
        )
        assert result is not None
        assert result["activity_id"] == activity_id


class TestNoPythonWeekdayToPatternMethod:
    """Verify the buggy conversion method has been removed."""

    def test_no_conversion_method(self):
        """_python_weekday_to_pattern should no longer exist."""
        constraint = FacultyWeeklyTemplateConstraint()
        assert not hasattr(constraint, "_python_weekday_to_pattern"), (
            "_python_weekday_to_pattern should be removed — "
            "templates use Python weekday directly, no conversion needed"
        )
