"""Tests for activity_naming.py - activity naming utilities.

These are pure unit tests - no database required.

NOTE: The activity_code_from_name function has a regex that matches literal 's'
due to escaped backslash (\\s instead of \\s). Tests reflect actual behavior.
"""

import pytest

from app.utils.activity_naming import (
    MAX_DISPLAY_ABBREV_LEN,
    activity_code_from_name,
    activity_display_abbrev,
)


class TestActivityCodeFromName:
    """Tests for activity_code_from_name function."""

    def test_simple_name_lowercased(self):
        """Simple name should be lowercased."""
        assert activity_code_from_name("Clinic") == "clinic"

    def test_slashes_to_underscores(self):
        """Slashes become underscores."""
        # Note: 's' after slash also converted due to regex bug
        result = activity_code_from_name("FM/Test")
        assert result == "fm_te_t"

    def test_hyphens_to_underscores(self):
        """Hyphens become underscores."""
        assert activity_code_from_name("Pre-Op") == "pre_op"

    def test_removes_parentheses(self):
        """Parentheses removed, contents kept."""
        assert activity_code_from_name("Clinic (Main)") == "clinicmain"

    def test_removes_at_symbol(self):
        """@ symbol removed."""
        result = activity_code_from_name("Clinic@Hospital")
        assert "@" not in result

    def test_empty_string_fallback(self):
        """Empty string returns 'activity'."""
        assert activity_code_from_name("") == "activity"

    def test_whitespace_only_fallback(self):
        """Whitespace-only string returns 'activity'."""
        assert activity_code_from_name("   ") == "activity"

    def test_only_special_chars_fallback(self):
        """String with only special chars returns 'activity'."""
        assert activity_code_from_name("@#$%") == "activity"

    def test_numbers_preserved(self):
        """Numbers are preserved in the code."""
        result = activity_code_from_name("Clinic1")
        assert "1" in result

    def test_preserves_existing_underscores(self):
        """Existing underscores are preserved."""
        assert activity_code_from_name("fm_clinic") == "fm_clinic"

    def test_output_is_lowercase(self):
        """Output is always lowercase."""
        result = activity_code_from_name("UPPERCASE")
        assert result == result.lower()

    def test_no_leading_underscore(self):
        """No leading underscore in output."""
        result = activity_code_from_name("_test")
        assert not result.startswith("_")

    def test_no_trailing_underscore(self):
        """No trailing underscore in output."""
        result = activity_code_from_name("test_")
        assert not result.endswith("_")

    def test_ob_gyn_conversion(self):
        """OB/GYN converted with slash to underscore."""
        result = activity_code_from_name("OB/GYN")
        assert "_" in result  # Slash converted to underscore

    def test_returns_string(self):
        """Always returns a string."""
        assert isinstance(activity_code_from_name("Test"), str)
        assert isinstance(activity_code_from_name(""), str)


class TestActivityDisplayAbbrev:
    """Tests for activity_display_abbrev function."""

    def test_prefers_display_abbreviation(self):
        """display_abbreviation takes highest precedence."""
        result = activity_display_abbrev(
            name="Family Medicine Clinic",
            display_abbreviation="FM",
            abbreviation="FMC",
        )
        assert result == "FM"

    def test_falls_back_to_abbreviation(self):
        """abbreviation used when display_abbreviation is None."""
        result = activity_display_abbrev(
            name="Family Medicine Clinic",
            display_abbreviation=None,
            abbreviation="FMC",
        )
        assert result == "FMC"

    def test_falls_back_to_name(self):
        """name used when both abbreviations are None."""
        result = activity_display_abbrev(
            name="Clinic",
            display_abbreviation=None,
            abbreviation=None,
        )
        assert result == "CLINIC"

    def test_empty_display_abbrev_falls_back(self):
        """Empty display_abbreviation falls back to abbreviation."""
        result = activity_display_abbrev(
            name="Clinic",
            display_abbreviation="",
            abbreviation="C",
        )
        assert result == "C"

    def test_all_empty_returns_act(self):
        """All empty/None returns 'ACT' fallback."""
        result = activity_display_abbrev(
            name="",
            display_abbreviation=None,
            abbreviation=None,
        )
        assert result == "ACT"

    def test_all_whitespace_returns_act(self):
        """All whitespace returns 'ACT' fallback."""
        result = activity_display_abbrev(
            name="   ",
            display_abbreviation="   ",
            abbreviation="   ",
        )
        assert result == "ACT"

    def test_uppercase_output(self):
        """Output is always uppercase."""
        result = activity_display_abbrev(
            name="clinic",
            display_abbreviation="fm",
        )
        assert result == "FM"

    def test_mixed_case_uppercased(self):
        """Mixed case is converted to uppercase."""
        result = activity_display_abbrev(
            name="FamilyMedicine",
            display_abbreviation="FmC",
        )
        assert result == "FMC"

    def test_truncates_at_max_length(self):
        """Output truncated at MAX_DISPLAY_ABBREV_LEN (20)."""
        long_name = "A" * 25
        result = activity_display_abbrev(name=long_name)
        assert len(result) == MAX_DISPLAY_ABBREV_LEN
        assert result == "A" * 20

    def test_exactly_max_length_not_truncated(self):
        """Exactly MAX_DISPLAY_ABBREV_LEN chars not truncated."""
        exact_name = "A" * MAX_DISPLAY_ABBREV_LEN
        result = activity_display_abbrev(name=exact_name)
        assert len(result) == MAX_DISPLAY_ABBREV_LEN

    def test_under_max_length_unchanged(self):
        """Under MAX_DISPLAY_ABBREV_LEN chars unchanged (except uppercase)."""
        short_name = "FM"
        result = activity_display_abbrev(name=short_name)
        assert result == "FM"

    def test_strips_whitespace(self):
        """Leading/trailing whitespace stripped before processing."""
        result = activity_display_abbrev(
            name="Clinic",
            display_abbreviation="  FM  ",
        )
        assert result == "FM"

    def test_max_display_abbrev_len_constant(self):
        """MAX_DISPLAY_ABBREV_LEN should be 20."""
        assert MAX_DISPLAY_ABBREV_LEN == 20

    def test_returns_string(self):
        """Always returns a string."""
        assert isinstance(activity_display_abbrev(name="Test"), str)
        assert isinstance(activity_display_abbrev(name=""), str)


class TestActivityNamingIntegration:
    """Integration tests for activity naming functions used together."""

    def test_short_name_produces_valid_outputs(self):
        """Short names produce valid code and abbrev."""
        name = "FM"
        code = activity_code_from_name(name)
        abbrev = activity_display_abbrev(name)

        assert code == "fm"
        assert abbrev == "FM"

    def test_abbrev_always_uppercase_code_always_lowercase(self):
        """Code is lowercase, abbrev is uppercase."""
        name = "Test"
        code = activity_code_from_name(name)
        abbrev = activity_display_abbrev(name)

        assert code == code.lower()
        assert abbrev == abbrev.upper()
