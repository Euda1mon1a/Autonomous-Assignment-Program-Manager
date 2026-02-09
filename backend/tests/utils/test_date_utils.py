"""Tests for date utility functions."""

from datetime import date

import pytest

from app.utils.date_utils import (
    days_between,
    get_academic_year,
    get_rolling_window_dates,
    get_week_bounds,
    is_weekend,
)


class TestGetWeekBounds:
    """Tests for get_week_bounds."""

    def test_monday_returns_same_week(self):
        mon = date(2025, 3, 17)  # Monday
        start, end = get_week_bounds(mon)
        assert start == date(2025, 3, 17)
        assert end == date(2025, 3, 23)

    def test_wednesday_returns_correct_bounds(self):
        wed = date(2025, 3, 19)
        start, end = get_week_bounds(wed)
        assert start == date(2025, 3, 17)
        assert end == date(2025, 3, 23)

    def test_sunday_returns_correct_bounds(self):
        sun = date(2025, 3, 23)
        start, end = get_week_bounds(sun)
        assert start == date(2025, 3, 17)
        assert end == date(2025, 3, 23)

    def test_saturday_returns_correct_bounds(self):
        sat = date(2025, 3, 22)
        start, end = get_week_bounds(sat)
        assert start == date(2025, 3, 17)
        assert end == date(2025, 3, 23)

    def test_start_is_monday_end_is_sunday(self):
        start, end = get_week_bounds(date(2025, 1, 1))
        assert start.weekday() == 0  # Monday
        assert end.weekday() == 6  # Sunday

    def test_week_span_is_7_days(self):
        start, end = get_week_bounds(date(2025, 6, 15))
        assert (end - start).days == 6


class TestGetRollingWindowDates:
    """Tests for get_rolling_window_dates."""

    def test_default_4_weeks(self):
        dates = get_rolling_window_dates(date(2025, 3, 28))
        assert len(dates) == 29  # 4 weeks = 28 days + 1 (inclusive)
        assert dates[0] == date(2025, 2, 28)
        assert dates[-1] == date(2025, 3, 28)

    def test_1_week_window(self):
        dates = get_rolling_window_dates(date(2025, 3, 7), weeks=1)
        assert len(dates) == 8  # 7 days + 1 (inclusive)

    def test_dates_are_chronological(self):
        dates = get_rolling_window_dates(date(2025, 3, 15))
        for i in range(len(dates) - 1):
            assert dates[i] < dates[i + 1]

    def test_zero_weeks(self):
        dates = get_rolling_window_dates(date(2025, 3, 15), weeks=0)
        assert len(dates) == 1
        assert dates[0] == date(2025, 3, 15)


class TestIsWeekend:
    """Tests for is_weekend."""

    def test_saturday_is_weekend(self):
        assert is_weekend(date(2025, 3, 22)) is True

    def test_sunday_is_weekend(self):
        assert is_weekend(date(2025, 3, 23)) is True

    def test_monday_is_not_weekend(self):
        assert is_weekend(date(2025, 3, 17)) is False

    def test_friday_is_not_weekend(self):
        assert is_weekend(date(2025, 3, 21)) is False

    def test_wednesday_is_not_weekend(self):
        assert is_weekend(date(2025, 3, 19)) is False


class TestGetAcademicYear:
    """Tests for get_academic_year."""

    def test_july_1_starts_new_year(self):
        assert get_academic_year(date(2025, 7, 1)) == 2025

    def test_june_30_is_previous_year(self):
        assert get_academic_year(date(2025, 6, 30)) == 2024

    def test_december_31_is_current_year(self):
        assert get_academic_year(date(2025, 12, 31)) == 2025

    def test_january_1_is_previous_year(self):
        assert get_academic_year(date(2025, 1, 1)) == 2024

    def test_july_is_boundary_month(self):
        assert get_academic_year(date(2024, 7, 1)) == 2024
        assert get_academic_year(date(2024, 6, 30)) == 2023


class TestDaysBetween:
    """Tests for days_between."""

    def test_same_day_is_1(self):
        d = date(2025, 3, 15)
        assert days_between(d, d) == 1

    def test_adjacent_days_is_2(self):
        assert days_between(date(2025, 3, 15), date(2025, 3, 16)) == 2

    def test_one_week_is_8(self):
        assert days_between(date(2025, 3, 15), date(2025, 3, 22)) == 8

    def test_end_before_start_returns_0(self):
        assert days_between(date(2025, 3, 20), date(2025, 3, 15)) == 0

    def test_month_boundary(self):
        assert days_between(date(2025, 3, 30), date(2025, 4, 2)) == 4
