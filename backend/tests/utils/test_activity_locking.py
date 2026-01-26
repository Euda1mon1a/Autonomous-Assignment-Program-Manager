"""Tests for activity_locking.py - activity locking utilities for CP-SAT solver.

These are pure unit tests using mock Activity objects - no database required.
"""

from unittest.mock import MagicMock

import pytest

from app.utils.activity_locking import (
    is_activity_blocking_for_solver,
    is_activity_preloaded,
    is_code_preloaded,
    preload_codes,
)


def create_mock_activity(
    code: str | None = "C",
    display_abbreviation: str | None = None,
    activity_category: str = "clinical",
    is_protected: bool = False,
) -> MagicMock:
    """Create a mock Activity object for testing."""
    activity = MagicMock()
    activity.code = code
    activity.display_abbreviation = display_abbreviation or code
    activity.activity_category = activity_category
    activity.is_protected = is_protected
    return activity


class TestIsActivityPreloaded:
    """Tests for is_activity_preloaded function."""

    def test_none_activity_returns_false(self):
        """None activity should not be preloaded."""
        assert is_activity_preloaded(None) is False

    def test_time_off_category_returns_true(self):
        """time_off activities are always preloaded."""
        activity = create_mock_activity(code="CUSTOM", activity_category="time_off")
        assert is_activity_preloaded(activity) is True

    def test_protected_flag_returns_true(self):
        """Protected activities are always preloaded."""
        activity = create_mock_activity(code="CUSTOM", is_protected=True)
        assert is_activity_preloaded(activity) is True

    def test_protected_overrides_non_locked_code(self):
        """Protected flag takes precedence over code not being in locked list."""
        activity = create_mock_activity(code="REGULAR_CLINIC", is_protected=True)
        assert is_activity_preloaded(activity) is True

    def test_unlocked_code_returns_false(self):
        """Regular codes not in locked list return False."""
        activity = create_mock_activity(code="C")
        assert is_activity_preloaded(activity) is False

    def test_unlocked_clinical_category_not_preloaded(self):
        """Clinical activities without locked codes are not preloaded."""
        activity = create_mock_activity(code="FM_CLINIC", activity_category="clinical")
        assert is_activity_preloaded(activity) is False

    @pytest.mark.parametrize(
        "code",
        [
            "FMIT",
            "LV",
            "LV-AM",
            "LV-PM",
            "W",
            "W-AM",
            "W-PM",
            "PC",
            "PCAT",
            "DO",
            "LEC",
            "LEC-PM",
            "ADV",
            "SIM",
            "HAFP",
            "USAFP",
            "BLS",
            "DEP",
            "PI",
            "MM",
            "HOL",
            "TDY",
            "CCC",
            "ORIENT",
            "OFF",
            "OFF-AM",
            "OFF-PM",
        ],
    )
    def test_all_locked_codes_are_preloaded(self, code: str):
        """All codes in _LOCKED_CODES should return True."""
        activity = create_mock_activity(code=code)
        assert is_activity_preloaded(activity) is True

    def test_locked_code_lowercase(self):
        """Locked code check should be case-insensitive."""
        activity = create_mock_activity(code="fmit")
        assert is_activity_preloaded(activity) is True

    def test_locked_code_mixed_case(self):
        """Mixed case codes should still match."""
        activity = create_mock_activity(code="FmIt")
        assert is_activity_preloaded(activity) is True

    def test_locked_code_with_whitespace(self):
        """Codes with whitespace should be normalized."""
        activity = create_mock_activity(code="  FMIT  ")
        assert is_activity_preloaded(activity) is True

    def test_display_abbreviation_checked(self):
        """Display abbreviation should also be checked for locked codes."""
        activity = create_mock_activity(code="CUSTOM", display_abbreviation="FMIT")
        assert is_activity_preloaded(activity) is True

    def test_either_code_or_abbrev_matches(self):
        """Either code or display_abbreviation matching is sufficient."""
        activity = create_mock_activity(code="XYZ", display_abbreviation="LV")
        assert is_activity_preloaded(activity) is True


class TestIsActivityBlockingForSolver:
    """Tests for is_activity_blocking_for_solver function."""

    def test_none_activity_returns_false(self):
        """None activity should not be blocking."""
        assert is_activity_blocking_for_solver(None) is False

    def test_time_off_category_is_blocking(self):
        """time_off activities always block solver."""
        activity = create_mock_activity(code="CUSTOM", activity_category="time_off")
        assert is_activity_blocking_for_solver(activity) is True

    def test_regular_clinic_not_blocking(self):
        """Regular clinic codes don't block solver."""
        activity = create_mock_activity(code="C")
        assert is_activity_blocking_for_solver(activity) is False

    @pytest.mark.parametrize(
        "code",
        [
            "FMIT",
            "NF",
            "PEDNF",
            "LDNF",
            "KAP",
            "KAPI-LD",
            "KAPI_LD",
            "IM",
            "PEDW",
            "PNF",
            "TDY",
            "DEP",
            "LV",
            "OFF",
            "W",
            "HOL",
            "PC",
            "PCAT",
            "DO",
        ],
    )
    def test_all_blocking_codes(self, code: str):
        """All codes in _BLOCKING_CODES should return True."""
        activity = create_mock_activity(code=code)
        assert is_activity_blocking_for_solver(activity) is True

    def test_blocking_code_with_am_suffix(self):
        """Codes with -AM suffix should still match base code."""
        activity = create_mock_activity(code="LV-AM")
        assert is_activity_blocking_for_solver(activity) is True

    def test_blocking_code_with_pm_suffix(self):
        """Codes with -PM suffix should still match base code."""
        activity = create_mock_activity(code="OFF-PM")
        assert is_activity_blocking_for_solver(activity) is True

    def test_blocking_code_lowercase(self):
        """Blocking code check should be case-insensitive."""
        activity = create_mock_activity(code="fmit")
        assert is_activity_blocking_for_solver(activity) is True

    def test_display_abbreviation_checked_for_blocking(self):
        """Display abbreviation should also be checked."""
        activity = create_mock_activity(code="CUSTOM", display_abbreviation="NF")
        assert is_activity_blocking_for_solver(activity) is True


class TestIsCodePreloaded:
    """Tests for is_code_preloaded function."""

    def test_locked_code_returns_true(self):
        """Locked codes return True."""
        assert is_code_preloaded("FMIT") is True

    def test_unlocked_code_returns_false(self):
        """Unlocked codes return False."""
        assert is_code_preloaded("C") is False

    def test_none_returns_false(self):
        """None input returns False."""
        assert is_code_preloaded(None) is False

    def test_empty_string_returns_false(self):
        """Empty string returns False."""
        assert is_code_preloaded("") is False

    def test_case_insensitive(self):
        """Check is case-insensitive."""
        assert is_code_preloaded("fmit") is True
        assert is_code_preloaded("Fmit") is True

    def test_whitespace_stripped(self):
        """Whitespace is stripped before comparison."""
        assert is_code_preloaded("  FMIT  ") is True


class TestPreloadCodes:
    """Tests for preload_codes function."""

    def test_returns_iterable(self):
        """Should return an iterable."""
        codes = preload_codes()
        assert hasattr(codes, "__iter__")

    def test_returns_sorted_list(self):
        """Should return sorted codes."""
        codes = list(preload_codes())
        assert codes == sorted(codes)

    def test_contains_key_codes(self):
        """Should contain known locked codes."""
        codes = set(preload_codes())
        assert "FMIT" in codes
        assert "LV" in codes
        assert "PCAT" in codes
        assert "DO" in codes
        assert "HOL" in codes

    def test_count_matches_expected(self):
        """Should return expected number of codes (27)."""
        codes = list(preload_codes())
        assert len(codes) == 27


class TestLockingVsBlocking:
    """Tests for the distinction between locking and blocking."""

    def test_nf_is_blocking_but_not_locked(self):
        """NF (Night Float) is blocking but not in locked preload list."""
        activity = create_mock_activity(code="NF")
        assert is_activity_blocking_for_solver(activity) is True
        assert is_activity_preloaded(activity) is False

    def test_lec_is_locked_but_not_blocking(self):
        """LEC (Lecture) is locked/preloaded but doesn't block rotation assignment."""
        activity = create_mock_activity(code="LEC")
        assert is_activity_preloaded(activity) is True
        assert is_activity_blocking_for_solver(activity) is False

    def test_fmit_is_both_locked_and_blocking(self):
        """FMIT is both locked and blocking."""
        activity = create_mock_activity(code="FMIT")
        assert is_activity_preloaded(activity) is True
        assert is_activity_blocking_for_solver(activity) is True

    def test_clinic_is_neither_locked_nor_blocking(self):
        """Regular clinic (C) is neither locked nor blocking."""
        activity = create_mock_activity(code="C")
        assert is_activity_preloaded(activity) is False
        assert is_activity_blocking_for_solver(activity) is False
