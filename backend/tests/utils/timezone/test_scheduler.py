"""Tests for timezone-aware scheduling utilities."""

import pytest
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.utils.timezone.scheduler import TimezoneAwareScheduler


class TestIsBusinessHours:
    def test_weekday_within_hours(self):
        # Monday 10 AM
        dt = datetime(2024, 1, 15, 10, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is True

    def test_weekday_before_hours(self):
        # Monday 6 AM
        dt = datetime(2024, 1, 15, 6, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is False

    def test_weekday_after_hours(self):
        # Monday 6 PM
        dt = datetime(2024, 1, 15, 18, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is False

    def test_at_start_boundary(self):
        # Monday exactly 8 AM
        dt = datetime(2024, 1, 15, 8, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is True

    def test_at_end_boundary(self):
        # Monday exactly 5 PM
        dt = datetime(2024, 1, 15, 17, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is True

    def test_weekend_excluded(self):
        # Saturday 10 AM
        dt = datetime(2024, 1, 13, 10, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is False

    def test_weekend_included(self):
        # Saturday 10 AM with weekends included
        dt = datetime(2024, 1, 13, 10, 0)
        assert (
            TimezoneAwareScheduler.is_business_hours(dt, include_weekends=True) is True
        )

    def test_sunday_excluded(self):
        # Sunday 10 AM
        dt = datetime(2024, 1, 14, 10, 0)
        assert TimezoneAwareScheduler.is_business_hours(dt) is False

    def test_custom_hours(self):
        # Monday 7 AM with custom start 7 AM
        dt = datetime(2024, 1, 15, 7, 0)
        assert (
            TimezoneAwareScheduler.is_business_hours(dt, start_time=time(7, 0)) is True
        )

    def test_aware_datetime_utc(self):
        # 6 PM UTC = 8 AM HST (UTC-10), should be business hours in Hawaii
        dt = datetime(2024, 1, 15, 18, 0, tzinfo=UTC)
        assert (
            TimezoneAwareScheduler.is_business_hours(dt, tz_name="Pacific/Honolulu")
            is True
        )


class TestGetNextBusinessDay:
    def test_weekday_to_weekday(self):
        # Monday -> Tuesday
        monday = date(2024, 1, 15)
        assert TimezoneAwareScheduler.get_next_business_day(monday) == date(2024, 1, 16)

    def test_friday_to_monday(self):
        friday = date(2024, 1, 19)
        assert TimezoneAwareScheduler.get_next_business_day(friday) == date(2024, 1, 22)

    def test_saturday_to_monday(self):
        saturday = date(2024, 1, 20)
        assert TimezoneAwareScheduler.get_next_business_day(saturday) == date(
            2024, 1, 22
        )

    def test_sunday_to_monday(self):
        sunday = date(2024, 1, 21)
        assert TimezoneAwareScheduler.get_next_business_day(sunday) == date(2024, 1, 22)

    def test_weekends_included(self):
        # Friday -> Saturday when weekends included
        friday = date(2024, 1, 19)
        assert TimezoneAwareScheduler.get_next_business_day(
            friday, include_weekends=True
        ) == date(2024, 1, 20)


class TestGetBusinessDaysBetween:
    def test_full_week(self):
        # Monday to Friday = 5 business days
        start = date(2024, 1, 15)
        end = date(2024, 1, 19)
        assert TimezoneAwareScheduler.get_business_days_between(start, end) == 5

    def test_includes_weekend(self):
        # Monday to next Monday = 6 business days (Mon-Fri + Mon)
        start = date(2024, 1, 15)
        end = date(2024, 1, 22)
        assert TimezoneAwareScheduler.get_business_days_between(start, end) == 6

    def test_same_day(self):
        d = date(2024, 1, 15)  # Monday
        assert TimezoneAwareScheduler.get_business_days_between(d, d) == 1

    def test_weekend_only(self):
        # Saturday to Sunday = 0 business days
        start = date(2024, 1, 20)
        end = date(2024, 1, 21)
        assert TimezoneAwareScheduler.get_business_days_between(start, end) == 0

    def test_reversed_dates(self):
        start = date(2024, 1, 19)
        end = date(2024, 1, 15)
        assert TimezoneAwareScheduler.get_business_days_between(start, end) == 0

    def test_include_weekends(self):
        # Monday to Sunday = 7 days when weekends included
        start = date(2024, 1, 15)
        end = date(2024, 1, 21)
        assert (
            TimezoneAwareScheduler.get_business_days_between(
                start, end, include_weekends=True
            )
            == 7
        )

    def test_two_full_weeks(self):
        # Two full weeks Mon-Fri = 10 business days
        start = date(2024, 1, 15)
        end = date(2024, 1, 26)
        assert TimezoneAwareScheduler.get_business_days_between(start, end) == 10


class TestGenerateDateRange:
    def test_simple_range(self):
        start = date(2024, 1, 15)
        end = date(2024, 1, 17)
        result = TimezoneAwareScheduler.generate_date_range(start, end)
        assert len(result) == 3
        assert result[0] == start
        assert result[-1] == end

    def test_excludes_weekends(self):
        # Mon Jan 15 to Sun Jan 21 without weekends = 5 days
        start = date(2024, 1, 15)
        end = date(2024, 1, 21)
        result = TimezoneAwareScheduler.generate_date_range(
            start, end, include_weekends=False
        )
        assert len(result) == 5
        for d in result:
            assert d.weekday() < 5

    def test_includes_weekends(self):
        start = date(2024, 1, 15)
        end = date(2024, 1, 21)
        result = TimezoneAwareScheduler.generate_date_range(start, end)
        assert len(result) == 7

    def test_single_day(self):
        d = date(2024, 1, 15)
        result = TimezoneAwareScheduler.generate_date_range(d, d)
        assert result == [d]

    def test_empty_if_reversed(self):
        start = date(2024, 1, 19)
        end = date(2024, 1, 15)
        result = TimezoneAwareScheduler.generate_date_range(start, end)
        assert result == []


class TestIsClinicAmBlock:
    def test_within_am_block(self):
        # 10 AM
        dt = datetime(2024, 1, 15, 10, 0)
        assert TimezoneAwareScheduler.is_clinic_am_block(dt) is True

    def test_at_am_start(self):
        # 8 AM exactly
        dt = datetime(2024, 1, 15, 8, 0)
        assert TimezoneAwareScheduler.is_clinic_am_block(dt) is True

    def test_at_noon_excluded(self):
        # 12 PM (end is exclusive)
        dt = datetime(2024, 1, 15, 12, 0)
        assert TimezoneAwareScheduler.is_clinic_am_block(dt) is False

    def test_pm_time(self):
        # 2 PM
        dt = datetime(2024, 1, 15, 14, 0)
        assert TimezoneAwareScheduler.is_clinic_am_block(dt) is False

    def test_before_am(self):
        # 7 AM
        dt = datetime(2024, 1, 15, 7, 0)
        assert TimezoneAwareScheduler.is_clinic_am_block(dt) is False


class TestIsClinicPmBlock:
    def test_within_pm_block(self):
        # 2 PM
        dt = datetime(2024, 1, 15, 14, 0)
        assert TimezoneAwareScheduler.is_clinic_pm_block(dt) is True

    def test_at_pm_start(self):
        # 1 PM exactly
        dt = datetime(2024, 1, 15, 13, 0)
        assert TimezoneAwareScheduler.is_clinic_pm_block(dt) is True

    def test_at_pm_end_excluded(self):
        # 5 PM (end is exclusive)
        dt = datetime(2024, 1, 15, 17, 0)
        assert TimezoneAwareScheduler.is_clinic_pm_block(dt) is False

    def test_am_time(self):
        # 10 AM
        dt = datetime(2024, 1, 15, 10, 0)
        assert TimezoneAwareScheduler.is_clinic_pm_block(dt) is False

    def test_lunch_gap(self):
        # 12:30 PM (between AM end and PM start)
        dt = datetime(2024, 1, 15, 12, 30)
        assert TimezoneAwareScheduler.is_clinic_pm_block(dt) is False


class TestGetBlockStartEnd:
    def test_am_block(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(d, "AM")
        assert start.hour == 8
        assert start.minute == 0
        assert end.hour == 12
        assert end.minute == 0
        assert start.tzinfo is not None

    def test_pm_block(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(d, "PM")
        assert start.hour == 13
        assert start.minute == 0
        assert end.hour == 17
        assert end.minute == 0

    def test_am_block_duration(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(d, "AM")
        duration = (end - start).total_seconds() / 3600
        assert duration == 4.0

    def test_pm_block_duration(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(d, "PM")
        duration = (end - start).total_seconds() / 3600
        assert duration == 4.0

    def test_case_insensitive(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(d, "am")
        assert start.hour == 8

    def test_custom_timezone(self):
        d = date(2024, 1, 15)
        start, end = TimezoneAwareScheduler.get_block_start_end(
            d, "AM", tz_name="America/New_York"
        )
        assert start.tzinfo == ZoneInfo("America/New_York")


class TestNormalizeToBusinessHours:
    def test_within_hours_unchanged(self):
        # Monday 10 AM should stay the same
        dt = datetime(2024, 1, 15, 10, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(dt)
        assert result.hour == 10
        assert result.minute == 0

    def test_before_hours_snaps_to_start(self):
        # Monday 6 AM -> 8 AM
        dt = datetime(2024, 1, 15, 6, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(dt)
        assert result.hour == 8
        assert result.minute == 0

    def test_after_hours_next_direction(self):
        # Monday 6 PM -> Tuesday 8 AM
        dt = datetime(2024, 1, 15, 18, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="next"
        )
        assert result.date() == date(2024, 1, 16)
        assert result.hour == 8

    def test_after_hours_previous_direction(self):
        # Monday 6 PM -> Monday 5 PM
        dt = datetime(2024, 1, 15, 18, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="previous"
        )
        assert result.date() == date(2024, 1, 15)
        assert result.hour == 17

    def test_saturday_next(self):
        # Saturday -> Monday 8 AM
        dt = datetime(2024, 1, 20, 10, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="next"
        )
        assert result.weekday() == 0  # Monday
        assert result.date() == date(2024, 1, 22)
        assert result.hour == 8

    def test_sunday_next(self):
        # Sunday -> Monday 8 AM
        dt = datetime(2024, 1, 21, 10, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="next"
        )
        assert result.weekday() == 0
        assert result.date() == date(2024, 1, 22)

    def test_saturday_previous(self):
        # Saturday -> Friday 5 PM
        dt = datetime(2024, 1, 20, 10, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="previous"
        )
        assert result.weekday() == 4  # Friday
        assert result.date() == date(2024, 1, 19)
        assert result.hour == 17

    def test_friday_after_hours_next(self):
        # Friday 6 PM -> Monday 8 AM (skips weekend)
        dt = datetime(2024, 1, 19, 18, 0)
        result = TimezoneAwareScheduler.normalize_to_business_hours(
            dt, direction="next"
        )
        assert result.date() == date(2024, 1, 22)
        assert result.hour == 8


class TestFindOverlappingHours:
    def test_hawaii_new_york_overlap(self):
        # Hawaii (HST) 8-17 is UTC 18-03 (next day)
        # New York (EST) 8-17 is UTC 13-22
        # Overlap in UTC: 18-22 = 4 hours
        # In Hawaii time: 8 AM - 12 PM
        overlap = TimezoneAwareScheduler.find_overlapping_hours(
            "Pacific/Honolulu", "America/New_York"
        )
        assert overlap is not None
        start, end = overlap
        # Hawaii business hours are 8-17, NY 8-17
        # NY 8 AM EST = 3 AM HST, NY 5 PM EST = 12 PM HST
        # Overlap: max(8 AM HST, 3 AM HST) to min(5 PM HST, 12 PM HST)
        # = 8 AM HST to 12 PM HST
        assert start.hour == 8
        assert end.hour == 12

    def test_same_timezone_full_overlap(self):
        overlap = TimezoneAwareScheduler.find_overlapping_hours(
            "Pacific/Honolulu", "Pacific/Honolulu"
        )
        assert overlap is not None
        start, end = overlap
        assert start == time(8, 0)
        assert end == time(17, 0)

    def test_no_overlap(self):
        # Hawaii 8-12 vs Tokyo 8-12 (19 hour difference = no overlap in those windows)
        overlap = TimezoneAwareScheduler.find_overlapping_hours(
            "Pacific/Honolulu",
            "Asia/Tokyo",
            end_time1=time(12, 0),
            end_time2=time(12, 0),
        )
        # HST 8-12 = UTC 18-22; JST 8-12 = UTC 23-03 — no overlap
        assert overlap is None


class TestCalculateHoursInPeriod:
    def test_simple_total(self):
        start = datetime(2024, 1, 15, 8, 0)
        end = datetime(2024, 1, 15, 17, 0)
        assert TimezoneAwareScheduler.calculate_hours_in_period(start, end) == 9.0

    def test_overnight(self):
        start = datetime(2024, 1, 15, 22, 0)
        end = datetime(2024, 1, 16, 6, 0)
        assert TimezoneAwareScheduler.calculate_hours_in_period(start, end) == 8.0

    def test_multi_day(self):
        start = datetime(2024, 1, 15, 0, 0)
        end = datetime(2024, 1, 17, 0, 0)
        assert TimezoneAwareScheduler.calculate_hours_in_period(start, end) == 48.0

    def test_zero_duration(self):
        dt = datetime(2024, 1, 15, 10, 0)
        assert TimezoneAwareScheduler.calculate_hours_in_period(dt, dt) == 0.0

    def test_fractional_hours(self):
        start = datetime(2024, 1, 15, 10, 0)
        end = datetime(2024, 1, 15, 10, 30)
        assert TimezoneAwareScheduler.calculate_hours_in_period(start, end) == 0.5
