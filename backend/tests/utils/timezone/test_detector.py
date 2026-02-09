"""Tests for timezone detector utilities."""

import pytest

from app.utils.timezone.detector import TimezoneDetector


class TestIsValidTimezone:
    def test_valid_iana(self):
        assert TimezoneDetector.is_valid_timezone("Pacific/Honolulu") is True

    def test_valid_utc(self):
        assert TimezoneDetector.is_valid_timezone("UTC") is True

    def test_valid_new_york(self):
        assert TimezoneDetector.is_valid_timezone("America/New_York") is True

    def test_invalid_timezone(self):
        assert TimezoneDetector.is_valid_timezone("Invalid/Timezone") is False

    def test_empty_string(self):
        assert TimezoneDetector.is_valid_timezone("") is False

    def test_military_abbreviation(self):
        assert TimezoneDetector.is_valid_timezone("HST") is True
        assert TimezoneDetector.is_valid_timezone("EST") is True


class TestNormalizeTimezoneName:
    def test_hst_to_honolulu(self):
        assert TimezoneDetector.normalize_timezone_name("HST") == "Pacific/Honolulu"

    def test_est_to_new_york(self):
        assert TimezoneDetector.normalize_timezone_name("EST") == "America/New_York"

    def test_cst_to_chicago(self):
        assert TimezoneDetector.normalize_timezone_name("CST") == "America/Chicago"

    def test_pst_to_los_angeles(self):
        assert TimezoneDetector.normalize_timezone_name("PST") == "America/Los_Angeles"

    def test_iana_passthrough(self):
        assert (
            TimezoneDetector.normalize_timezone_name("Pacific/Honolulu")
            == "Pacific/Honolulu"
        )

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid timezone"):
            TimezoneDetector.normalize_timezone_name("INVALID")

    def test_case_insensitive_military(self):
        assert TimezoneDetector.normalize_timezone_name("hst") == "Pacific/Honolulu"


class TestFormatOffset:
    def test_negative_offset(self):
        assert TimezoneDetector._format_offset(-10.0) == "UTC-10:00"

    def test_positive_offset(self):
        assert TimezoneDetector._format_offset(9.0) == "UTC+09:00"

    def test_zero_offset(self):
        assert TimezoneDetector._format_offset(0.0) == "UTC+00:00"

    def test_half_hour_offset(self):
        assert TimezoneDetector._format_offset(5.5) == "UTC+05:30"

    def test_negative_half_hour(self):
        assert TimezoneDetector._format_offset(-9.5) == "UTC-09:30"


class TestGetTimezoneInfo:
    def test_hawaii_info(self):
        info = TimezoneDetector.get_timezone_info("Pacific/Honolulu")
        assert info["name"] == "Pacific/Honolulu"
        assert info["utc_offset_hours"] == -10.0
        assert info["has_dst"] is False

    def test_utc_info(self):
        info = TimezoneDetector.get_timezone_info("UTC")
        assert info["name"] == "UTC"
        assert info["utc_offset_hours"] == 0.0

    def test_military_alias(self):
        info = TimezoneDetector.get_timezone_info("HST")
        assert info["name"] == "Pacific/Honolulu"

    def test_has_required_keys(self):
        info = TimezoneDetector.get_timezone_info("Pacific/Honolulu")
        required_keys = [
            "name",
            "abbreviation",
            "utc_offset_hours",
            "utc_offset_string",
            "has_dst",
            "current_dst",
            "current_datetime",
        ]
        for key in required_keys:
            assert key in info


class TestGetTimezoneForLocation:
    def test_honolulu(self):
        assert (
            TimezoneDetector.get_timezone_for_location("Honolulu") == "Pacific/Honolulu"
        )

    def test_hawaii(self):
        assert (
            TimezoneDetector.get_timezone_for_location("Hawaii") == "Pacific/Honolulu"
        )

    def test_tokyo(self):
        assert TimezoneDetector.get_timezone_for_location("Tokyo") == "Asia/Tokyo"

    def test_case_insensitive(self):
        assert (
            TimezoneDetector.get_timezone_for_location("HONOLULU") == "Pacific/Honolulu"
        )

    def test_unknown_location(self):
        assert TimezoneDetector.get_timezone_for_location("Unknown") is None

    def test_whitespace_stripped(self):
        assert (
            TimezoneDetector.get_timezone_for_location("  Honolulu  ")
            == "Pacific/Honolulu"
        )


class TestIsSameTimezone:
    def test_same_name(self):
        assert (
            TimezoneDetector.is_same_timezone("Pacific/Honolulu", "Pacific/Honolulu")
            is True
        )

    def test_alias_match(self):
        assert TimezoneDetector.is_same_timezone("HST", "Pacific/Honolulu") is True

    def test_different_timezones(self):
        assert (
            TimezoneDetector.is_same_timezone("Pacific/Honolulu", "America/New_York")
            is False
        )

    def test_invalid_timezone(self):
        assert TimezoneDetector.is_same_timezone("Invalid", "Pacific/Honolulu") is False


class TestValidateUserTimezonePreference:
    def test_valid_iana(self):
        result = TimezoneDetector.validate_user_timezone_preference("Pacific/Honolulu")
        assert result == "Pacific/Honolulu"

    def test_military_alias(self):
        result = TimezoneDetector.validate_user_timezone_preference("HST")
        assert result == "Pacific/Honolulu"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid timezone"):
            TimezoneDetector.validate_user_timezone_preference("FAKE")


class TestGetCommonTimezones:
    def test_returns_list(self):
        result = TimezoneDetector.get_common_timezones()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_hawaii_included(self):
        result = TimezoneDetector.get_common_timezones()
        values = [tz["value"] for tz in result]
        assert "Pacific/Honolulu" in values

    def test_sorted_by_offset(self):
        result = TimezoneDetector.get_common_timezones()
        offsets = [tz["offset_hours"] for tz in result]
        assert offsets == sorted(offsets)

    def test_has_required_keys(self):
        result = TimezoneDetector.get_common_timezones()
        for tz in result:
            assert "value" in tz
            assert "label" in tz
            assert "offset" in tz
            assert "offset_hours" in tz


class TestGetUserTimezone:
    def test_user_preference(self):
        result = TimezoneDetector.get_user_timezone(user_preference="America/New_York")
        assert result == "America/New_York"

    def test_military_preference(self):
        result = TimezoneDetector.get_user_timezone(user_preference="EST")
        assert result == "America/New_York"

    def test_no_preference_no_request(self):
        result = TimezoneDetector.get_user_timezone()
        assert result == "Pacific/Honolulu"

    def test_invalid_preference_falls_through(self):
        result = TimezoneDetector.get_user_timezone(user_preference="INVALID")
        assert result == "Pacific/Honolulu"
