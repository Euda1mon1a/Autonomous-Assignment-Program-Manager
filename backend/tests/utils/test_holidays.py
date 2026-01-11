"""Tests for federal holiday calendar utility."""

from datetime import date

import pytest

from app.utils.holidays import (
    Holiday,
    get_academic_year_holidays,
    get_federal_holidays,
    is_federal_holiday,
)


class TestGetFederalHolidays:
    """Test get_federal_holidays function."""

    def test_returns_11_holidays(self):
        """Should return exactly 11 federal holidays (includes Juneteenth)."""
        holidays = get_federal_holidays(2025)
        assert len(holidays) == 11

    def test_holidays_are_sorted_by_date(self):
        """Holidays should be returned in chronological order."""
        holidays = get_federal_holidays(2025)
        dates = [h.date for h in holidays]
        assert dates == sorted(dates)

    def test_fixed_holidays_correct_2025(self):
        """Fixed holidays should be on correct dates for 2025."""
        holidays = get_federal_holidays(2025)
        holiday_dict = {h.name: h.date for h in holidays}

        assert holiday_dict["New Year's Day"] == date(2025, 1, 1)
        assert holiday_dict["Independence Day"] == date(2025, 7, 4)
        assert holiday_dict["Veterans Day"] == date(2025, 11, 11)
        assert holiday_dict["Christmas Day"] == date(2025, 12, 25)

    def test_floating_holidays_correct_2025(self):
        """Floating holidays should be calculated correctly for 2025."""
        holidays = get_federal_holidays(2025)
        holiday_dict = {h.name: h.date for h in holidays}

        # 2025 floating holidays (verified against OPM calendar)
        assert holiday_dict["Martin Luther King Jr. Day"] == date(
            2025, 1, 20
        )  # 3rd Mon Jan
        assert holiday_dict["Presidents Day"] == date(2025, 2, 17)  # 3rd Mon Feb
        assert holiday_dict["Memorial Day"] == date(2025, 5, 26)  # Last Mon May
        assert holiday_dict["Labor Day"] == date(2025, 9, 1)  # 1st Mon Sep
        assert holiday_dict["Columbus Day"] == date(2025, 10, 13)  # 2nd Mon Oct
        assert holiday_dict["Thanksgiving Day"] == date(2025, 11, 27)  # 4th Thu Nov

    def test_floating_holidays_correct_2026(self):
        """Floating holidays should be calculated correctly for 2026."""
        holidays = get_federal_holidays(2026)
        holiday_dict = {h.name: h.date for h in holidays}

        # 2026 floating holidays
        assert holiday_dict["Martin Luther King Jr. Day"] == date(
            2026, 1, 19
        )  # 3rd Mon Jan
        assert holiday_dict["Presidents Day"] == date(2026, 2, 16)  # 3rd Mon Feb
        assert holiday_dict["Memorial Day"] == date(2026, 5, 25)  # Last Mon May
        assert holiday_dict["Labor Day"] == date(2026, 9, 7)  # 1st Mon Sep
        assert holiday_dict["Columbus Day"] == date(2026, 10, 12)  # 2nd Mon Oct
        assert holiday_dict["Thanksgiving Day"] == date(2026, 11, 26)  # 4th Thu Nov

    def test_juneteenth_exists(self):
        """Juneteenth (June 19) should be included."""
        holidays = get_federal_holidays(2025)
        holiday_names = [h.name for h in holidays]
        assert "Juneteenth National Independence Day" in holiday_names

        # Check date
        holiday_dict = {h.name: h.date for h in holidays}
        assert holiday_dict["Juneteenth National Independence Day"] == date(2025, 6, 19)

    def test_observed_date_saturday_to_friday(self):
        """July 4, 2026 falls on Saturday, should be observed Friday July 3."""
        holidays = get_federal_holidays(2026)
        independence_day = next(h for h in holidays if h.name == "Independence Day")

        # Observed date should be Friday July 3
        assert independence_day.date == date(2026, 7, 3)
        # Actual date should be Saturday July 4
        assert independence_day.actual_date == date(2026, 7, 4)

    def test_observed_date_sunday_to_monday(self):
        """July 4, 2021 fell on Sunday, should be observed Monday July 5."""
        holidays = get_federal_holidays(2021)
        independence_day = next(h for h in holidays if h.name == "Independence Day")

        # Observed date should be Monday July 5
        assert independence_day.date == date(2021, 7, 5)
        # Actual date should be Sunday July 4
        assert independence_day.actual_date == date(2021, 7, 4)

    def test_observed_date_weekday_unchanged(self):
        """July 4, 2025 falls on Friday, should be observed same day."""
        holidays = get_federal_holidays(2025)
        independence_day = next(h for h in holidays if h.name == "Independence Day")

        # Observed date should be same as actual (Friday)
        assert independence_day.date == date(2025, 7, 4)
        # actual_date should be None when same as observed
        assert independence_day.actual_date is None


class TestIsFederalHoliday:
    """Test is_federal_holiday function."""

    def test_returns_true_for_holiday(self):
        """Should return True and name for holiday dates."""
        is_hol, name = is_federal_holiday(date(2025, 12, 25))
        assert is_hol is True
        assert name == "Christmas Day"

    def test_returns_false_for_non_holiday(self):
        """Should return False and None for non-holiday dates."""
        is_hol, name = is_federal_holiday(date(2025, 12, 26))
        assert is_hol is False
        assert name is None

    def test_floating_holiday_detection(self):
        """Should correctly detect floating holidays."""
        # Thanksgiving 2025 is Nov 27
        is_hol, name = is_federal_holiday(date(2025, 11, 27))
        assert is_hol is True
        assert name == "Thanksgiving Day"

        # Nov 26 is not Thanksgiving
        is_hol, name = is_federal_holiday(date(2025, 11, 26))
        assert is_hol is False


class TestGetAcademicYearHolidays:
    """Test get_academic_year_holidays function."""

    def test_academic_year_2025_holidays(self):
        """AY 2025-2026 should include holidays from Jul 2025 - Jun 2026."""
        holidays = get_academic_year_holidays(2025)

        # Should have ~10 holidays (some years have 9-11 depending on date ranges)
        assert 9 <= len(holidays) <= 11

        # First holiday should be in July or later of start year
        assert holidays[0].date >= date(2025, 7, 1)

        # Last holiday should be in June or earlier of end year
        assert holidays[-1].date <= date(2026, 6, 30)

    def test_includes_independence_day(self):
        """Academic year should include Independence Day (July 4)."""
        holidays = get_academic_year_holidays(2025)
        holiday_names = [h.name for h in holidays]
        assert "Independence Day" in holiday_names

    def test_includes_new_years_day(self):
        """Academic year should include New Year's Day of the second year."""
        holidays = get_academic_year_holidays(2025)
        holiday_dict = {h.name: h.date for h in holidays}
        assert "New Year's Day" in holiday_dict
        assert holiday_dict["New Year's Day"] == date(2026, 1, 1)

    def test_excludes_christmas_of_end_year(self):
        """Academic year should NOT include Christmas of the end year (Dec 2026)."""
        holidays = get_academic_year_holidays(2025)
        holiday_dict = {h.name: h.date for h in holidays}
        # Christmas should be Dec 2025, not Dec 2026
        assert holiday_dict.get("Christmas Day") == date(2025, 12, 25)
