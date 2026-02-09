"""Tests for timezone formatting utilities."""

import pytest
from datetime import UTC, date, datetime, time, timedelta

from app.utils.timezone.formatting import TimezoneFormatter


class TestFormatDate:
    def test_default_format(self):
        d = date(2024, 1, 15)
        assert TimezoneFormatter.format_date(d) == "2024-01-15"

    def test_custom_format(self):
        d = date(2024, 1, 15)
        assert TimezoneFormatter.format_date(d, "%B %d, %Y") == "January 15, 2024"

    def test_datetime_input(self):
        dt = datetime(2024, 1, 15, 10, 30)
        assert TimezoneFormatter.format_date(dt) == "2024-01-15"


class TestFormatTime:
    def test_default_short_format(self):
        t = time(14, 30)
        assert TimezoneFormatter.format_time(t) == "14:30"

    def test_with_seconds(self):
        t = time(14, 30, 45)
        assert TimezoneFormatter.format_time(t, include_seconds=True) == "14:30:45"

    def test_datetime_input(self):
        dt = datetime(2024, 1, 15, 14, 30)
        assert TimezoneFormatter.format_time(dt) == "14:30"

    def test_custom_format(self):
        t = time(14, 30)
        assert TimezoneFormatter.format_time(t, "%I:%M %p") == "02:30 PM"


class TestFormatRelative:
    def test_seconds_ago(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 15, 11, 59, 30, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "30 seconds ago"

    def test_minutes_ago(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 15, 11, 45, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "15 minutes ago"

    def test_hours_ago(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "2 hours ago"

    def test_days_ago(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 12, 12, 0, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "3 days ago"

    def test_future_time(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        future = datetime(2024, 1, 15, 14, 0, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(future, reference=now)
        assert result == "2 hours from now"

    def test_singular_forms(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "1 hour ago"

    def test_weeks_ago(self):
        now = datetime(2024, 1, 22, 12, 0, 0, tzinfo=UTC)
        past = datetime(2024, 1, 8, 12, 0, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_relative(past, reference=now)
        assert result == "2 weeks ago"


class TestFormatDateRange:
    def test_same_day(self):
        d = date(2024, 1, 15)
        result = TimezoneFormatter.format_date_range(d, d)
        assert result == "January 15, 2024"

    def test_same_month(self):
        start = date(2024, 1, 15)
        end = date(2024, 1, 19)
        result = TimezoneFormatter.format_date_range(start, end)
        assert result == "January 15 - 19, 2024"

    def test_same_year_different_months(self):
        start = date(2024, 1, 15)
        end = date(2024, 3, 20)
        result = TimezoneFormatter.format_date_range(start, end)
        assert result == "January 15 - March 20, 2024"

    def test_different_years(self):
        start = date(2024, 12, 25)
        end = date(2025, 1, 5)
        result = TimezoneFormatter.format_date_range(start, end)
        assert "December 25, 2024" in result
        assert "January 05, 2025" in result


class TestFormatBlockTime:
    def test_am_block(self):
        d = date(2024, 1, 15)
        result = TimezoneFormatter.format_block_time(d, "AM")
        assert "January 15, 2024" in result
        assert "AM" in result
        assert "8:00 AM - 12:00 PM" in result

    def test_pm_block(self):
        d = date(2024, 1, 15)
        result = TimezoneFormatter.format_block_time(d, "PM")
        assert "PM" in result
        assert "1:00 PM - 5:00 PM" in result

    def test_without_date(self):
        d = date(2024, 1, 15)
        result = TimezoneFormatter.format_block_time(d, "AM", include_date=False)
        assert "January" not in result
        assert result == "AM (8:00 AM - 12:00 PM)"

    def test_unknown_time(self):
        d = date(2024, 1, 15)
        result = TimezoneFormatter.format_block_time(d, "EVENING")
        assert "Unknown" in result


class TestFormatDuration:
    def test_seconds(self):
        assert TimezoneFormatter.format_duration(30, precise=True) == "30 seconds"

    def test_minutes(self):
        assert TimezoneFormatter.format_duration(120, precise=True) == "2 minutes"

    def test_hours_minutes_seconds(self):
        result = TimezoneFormatter.format_duration(3665, precise=True)
        assert "1 hour" in result
        assert "1 minute" in result
        assert "5 seconds" in result

    def test_imprecise_returns_largest_unit(self):
        result = TimezoneFormatter.format_duration(3665, precise=False)
        assert result == "1 hour"

    def test_days(self):
        result = TimezoneFormatter.format_duration(172800, precise=False)
        assert result == "2 days"

    def test_negative_duration(self):
        assert TimezoneFormatter.format_duration(-10) == "0 seconds"

    def test_zero_duration(self):
        assert TimezoneFormatter.format_duration(0, precise=True) == "0 seconds"

    def test_singular_forms(self):
        assert TimezoneFormatter.format_duration(1, precise=True) == "1 second"
        assert TimezoneFormatter.format_duration(60, precise=True) == "1 minute"
        assert TimezoneFormatter.format_duration(3600, precise=True) == "1 hour"
        assert TimezoneFormatter.format_duration(86400, precise=True) == "1 day"


class TestFormatIso8601:
    def test_aware_utc_mode(self):
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_iso8601(dt, utc=True)
        assert "2024-01-15T10:00:00" in result
        assert "+00:00" in result

    def test_naive_utc_mode(self):
        dt = datetime(2024, 1, 15, 10, 0)
        result = TimezoneFormatter.format_iso8601(dt, utc=True)
        # Naive is treated as local (HST, UTC-10), so UTC = 10+10 = 20
        assert "2024-01-15T20:00:00" in result

    def test_local_mode(self):
        dt = datetime(2024, 1, 15, 10, 0)
        result = TimezoneFormatter.format_iso8601(dt, utc=False)
        assert "2024-01-15T10:00:00" in result


class TestFormatForUser:
    def test_full_style(self):
        dt = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_for_user(
            dt, user_tz="Pacific/Honolulu", style="full"
        )
        # 20:00 UTC = 10:00 HST
        assert "10" in result
        assert "HST" in result

    def test_relative_style(self):
        # Just verify it returns a string, don't test exact output
        dt = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_for_user(dt, style="relative")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_iso_style(self):
        dt = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        result = TimezoneFormatter.format_for_user(dt, style="iso")
        assert "2024-01-15" in result
