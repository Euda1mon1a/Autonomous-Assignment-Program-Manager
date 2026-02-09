"""Tests for timezone converter utilities."""

import pytest
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.utils.timezone.converter import TimezoneConverter


class TestGetTimezone:
    def test_valid_timezone(self):
        tz = TimezoneConverter.get_timezone("Pacific/Honolulu")
        assert tz.key == "Pacific/Honolulu"

    def test_utc(self):
        tz = TimezoneConverter.get_timezone("UTC")
        assert tz.key == "UTC"

    def test_invalid_timezone_raises(self):
        with pytest.raises(ValueError, match="Invalid timezone"):
            TimezoneConverter.get_timezone("Invalid/Timezone")


class TestUtcToLocal:
    def test_naive_utc_to_hawaii(self):
        utc_time = datetime(2024, 1, 15, 20, 0)  # 8 PM UTC
        local = TimezoneConverter.utc_to_local(utc_time)
        # HST is UTC-10
        assert local.hour == 10
        assert local.day == 15

    def test_aware_utc_to_hawaii(self):
        utc_time = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        local = TimezoneConverter.utc_to_local(utc_time)
        assert local.hour == 10

    def test_custom_timezone(self):
        utc_time = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        local = TimezoneConverter.utc_to_local(utc_time, "America/New_York")
        # EST is UTC-5
        assert local.hour == 15

    def test_date_rollback(self):
        # 5 AM UTC should be previous day in Hawaii (UTC-10)
        utc_time = datetime(2024, 1, 15, 5, 0, tzinfo=UTC)
        local = TimezoneConverter.utc_to_local(utc_time)
        assert local.day == 14
        assert local.hour == 19


class TestLocalToUtc:
    def test_naive_hawaii_to_utc(self):
        local_time = datetime(2024, 1, 15, 10, 0)  # 10 AM HST
        utc = TimezoneConverter.local_to_utc(local_time)
        # HST+10 = UTC
        assert utc.hour == 20
        assert utc.tzinfo is not None

    def test_custom_timezone(self):
        local_time = datetime(2024, 1, 15, 15, 0)  # 3 PM EST
        utc = TimezoneConverter.local_to_utc(local_time, "America/New_York")
        assert utc.hour == 20

    def test_roundtrip(self):
        original = datetime(2024, 6, 15, 14, 30, tzinfo=UTC)
        local = TimezoneConverter.utc_to_local(original)
        back = TimezoneConverter.local_to_utc(local)
        assert original.hour == back.hour
        assert original.minute == back.minute


class TestConvertBetweenTimezones:
    def test_ny_to_hawaii(self):
        ny_time = datetime(2024, 1, 15, 15, 0)  # 3 PM EST
        hawaii = TimezoneConverter.convert_between_timezones(
            ny_time, "America/New_York", "Pacific/Honolulu"
        )
        # EST is UTC-5, HST is UTC-10, so 5 hours behind
        assert hawaii.hour == 10

    def test_hawaii_to_tokyo(self):
        hi_time = datetime(2024, 1, 15, 10, 0)
        tokyo = TimezoneConverter.convert_between_timezones(
            hi_time, "Pacific/Honolulu", "Asia/Tokyo"
        )
        # HST is UTC-10, JST is UTC+9, so 19 hours ahead
        # 10 AM + 19 = 5 AM next day
        assert tokyo.hour == 5
        assert tokyo.day == 16

    def test_same_timezone(self):
        dt = datetime(2024, 1, 15, 10, 0)
        result = TimezoneConverter.convert_between_timezones(
            dt, "Pacific/Honolulu", "Pacific/Honolulu"
        )
        assert result.hour == 10


class TestNowUtc:
    def test_returns_utc_aware(self):
        now = TimezoneConverter.now_utc()
        assert now.tzinfo is not None
        assert now.tzinfo == UTC

    def test_is_recent(self):
        now = TimezoneConverter.now_utc()
        diff = abs((datetime.now(UTC) - now).total_seconds())
        assert diff < 2


class TestNowLocal:
    def test_returns_aware(self):
        local = TimezoneConverter.now_local()
        assert local.tzinfo is not None

    def test_custom_timezone(self):
        local = TimezoneConverter.now_local("America/New_York")
        assert local.tzinfo is not None


class TestMakeAware:
    def test_makes_naive_aware(self):
        naive = datetime(2024, 1, 15, 10, 0)
        aware = TimezoneConverter.make_aware(naive)
        assert aware.tzinfo is not None

    def test_custom_timezone(self):
        naive = datetime(2024, 1, 15, 10, 0)
        aware = TimezoneConverter.make_aware(naive, "America/New_York")
        assert aware.tzinfo is not None

    def test_already_aware_raises(self):
        aware = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="already timezone-aware"):
            TimezoneConverter.make_aware(aware)


class TestMakeNaive:
    def test_makes_aware_naive(self):
        aware = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)
        naive = TimezoneConverter.make_naive(aware)
        assert naive.tzinfo is None
        # Converted to HST (UTC-10), so hour = 10
        assert naive.hour == 10

    def test_already_naive_raises(self):
        naive = datetime(2024, 1, 15, 10, 0)
        with pytest.raises(ValueError, match="already naive"):
            TimezoneConverter.make_naive(naive)


class TestGetUtcOffset:
    def test_hawaii_offset(self):
        offset = TimezoneConverter.get_utc_offset("Pacific/Honolulu")
        assert offset.total_seconds() / 3600 == -10.0

    def test_utc_offset(self):
        offset = TimezoneConverter.get_utc_offset("UTC")
        assert offset.total_seconds() == 0


class TestIsDst:
    def test_hawaii_no_dst(self):
        summer = datetime(2024, 7, 15, 12, 0)
        assert TimezoneConverter.is_dst(summer, "Pacific/Honolulu") is False

    def test_hawaii_winter_no_dst(self):
        winter = datetime(2024, 1, 15, 12, 0)
        assert TimezoneConverter.is_dst(winter, "Pacific/Honolulu") is False


class TestNormalizeDatetimeRange:
    def test_naive_datetimes(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = datetime(2024, 1, 31, 23, 59)
        utc_start, utc_end = TimezoneConverter.normalize_datetime_range(start, end)
        assert utc_start.tzinfo is not None
        assert utc_end.tzinfo is not None

    def test_aware_datetimes(self):
        start = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 31, 23, 59, tzinfo=UTC)
        utc_start, utc_end = TimezoneConverter.normalize_datetime_range(start, end)
        assert utc_start.hour == 0
        assert utc_end.hour == 23
