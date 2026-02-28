"""
Tests for DOW convention disambiguation between faculty_weekly_templates and weekly_patterns.

Two different DOW conventions coexist in the codebase:
- faculty_weekly_templates: Python weekday (0=Monday, 6=Sunday)
- weekly_patterns: PG EXTRACT(DOW) (0=Sunday, 6=Saturday)

These tests ensure the constants are correct and the conventions remain distinct.
See docs/architecture/DOW_CONVENTION_BUG.md for full reference.
"""

from app.models.faculty_weekly_template import (
    PYTHON_WEEKDAY_SATURDAY,
    PYTHON_WEEKDAY_SUNDAY,
)
from app.models.weekly_pattern import WeeklyPattern


class TestFacultyWeeklyTemplateConvention:
    """Faculty templates use Python weekday (0=Monday, 6=Sunday)."""

    def test_saturday_is_5(self):
        assert PYTHON_WEEKDAY_SATURDAY == 5

    def test_sunday_is_6(self):
        assert PYTHON_WEEKDAY_SUNDAY == 6

    def test_conventions_differ(self):
        """The two conventions MUST use different values for Saturday."""
        assert PYTHON_WEEKDAY_SATURDAY != WeeklyPattern.PG_DOW_SATURDAY, (
            "Python weekday Saturday (5) must differ from PG DOW Saturday (6)"
        )


class TestWeeklyPatternConvention:
    """Weekly patterns use PG EXTRACT(DOW) (0=Sunday, 6=Saturday)."""

    def test_sunday_is_0(self):
        assert WeeklyPattern.PG_DOW_SUNDAY == 0

    def test_saturday_is_6(self):
        assert WeeklyPattern.PG_DOW_SATURDAY == 6

    def test_sunday_conventions_differ(self):
        """PG DOW Sunday (0) must differ from Python weekday Sunday (6)."""
        assert WeeklyPattern.PG_DOW_SUNDAY != PYTHON_WEEKDAY_SUNDAY
