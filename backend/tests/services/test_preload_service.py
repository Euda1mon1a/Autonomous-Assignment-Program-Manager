"""Tests for PreloadService pure functions and constants.

Tests rotation code normalization, schedule code determination for various
rotation types, date helper methods, and constant validation -- all without
database access.
"""

from datetime import date

import pytest

from app.services.preload_service import (
    _INTERN_CONTINUITY_EXEMPT_ROTATIONS,
    _KAP_ROTATIONS,
    _LEC_EXEMPT_ROTATIONS,
    _NIGHT_FLOAT_ROTATIONS,
    _OFFSITE_ROTATIONS,
    _ROTATION_ALIASES,
    _SATURDAY_OFF_ROTATIONS,
    PreloadService,
)


@pytest.fixture
def service():
    """Create service with None session (only testing pure methods)."""
    svc = PreloadService.__new__(PreloadService)
    svc.session = None
    svc._activity_cache = {}
    svc._template_cache = {}
    return svc


# ============================================================================
# _canonical_rotation_code
# ============================================================================


class TestCanonicalRotationCode:
    """Tests for rotation code normalization."""

    def test_alias_mapping(self, service):
        assert service._canonical_rotation_code("PNF") == "PEDNF"
        assert service._canonical_rotation_code("PEDS NF") == "PEDNF"
        assert service._canonical_rotation_code("L&D NIGHT FLOAT") == "LDNF"

    def test_case_insensitive(self, service):
        assert service._canonical_rotation_code("pnf") == "PEDNF"
        assert service._canonical_rotation_code("kapi") == "KAP"

    def test_strips_whitespace(self, service):
        assert service._canonical_rotation_code("  PNF  ") == "PEDNF"

    def test_none_returns_empty(self, service):
        assert service._canonical_rotation_code(None) == ""

    def test_empty_returns_empty(self, service):
        assert service._canonical_rotation_code("") == ""

    def test_hilo_prefix_normalization(self, service):
        assert service._canonical_rotation_code("HILO") == "HILO"
        assert service._canonical_rotation_code("HILO-R1") == "HILO"
        assert service._canonical_rotation_code("HILO-123") == "HILO"

    def test_oki_prefix_normalization(self, service):
        assert service._canonical_rotation_code("OKI") == "OKI"
        assert service._canonical_rotation_code("OKINAWA") == "OKI"

    def test_kapi_prefix_normalization(self, service):
        assert service._canonical_rotation_code("KAPI") == "KAP"
        assert service._canonical_rotation_code("KAPI-LD") == "KAP"
        assert service._canonical_rotation_code("KAPIOLANI") == "KAP"

    def test_passthrough_unknown(self, service):
        assert service._canonical_rotation_code("CARDIO") == "CARDIO"
        assert service._canonical_rotation_code("IM") == "IM"


# ============================================================================
# _is_last_wednesday
# ============================================================================


class TestIsLastWednesday:
    """Tests for last-Wednesday-of-block detection."""

    def test_last_wednesday(self, service):
        # Block ends April 8 (Tue). Last Wednesday = April 2.
        assert service._is_last_wednesday(date(2025, 4, 2), date(2025, 4, 8)) is True

    def test_not_last_wednesday(self, service):
        # March 26 is a Wednesday but not the last one before April 8
        assert service._is_last_wednesday(date(2025, 3, 26), date(2025, 4, 8)) is False

    def test_not_wednesday(self, service):
        # April 3 is a Thursday
        assert service._is_last_wednesday(date(2025, 4, 3), date(2025, 4, 8)) is False

    def test_wednesday_is_block_end(self, service):
        # Block ends on a Wednesday -- that's the last Wednesday
        assert service._is_last_wednesday(date(2025, 4, 9), date(2025, 4, 9)) is True

    def test_wednesday_one_week_before_end(self, service):
        # Exactly 7 days before end: NOT last (there's another Wednesday)
        assert service._is_last_wednesday(date(2025, 4, 2), date(2025, 4, 9)) is False


# ============================================================================
# _is_lec_exempt / _is_intern_continuity_exempt
# ============================================================================


class TestExemptionChecks:
    """Tests for LEC and intern continuity exemption checks."""

    def test_lec_exempt_nf(self, service):
        assert service._is_lec_exempt("NF") is True

    def test_lec_exempt_pednf(self, service):
        assert service._is_lec_exempt("PEDNF") is True

    def test_lec_exempt_tdy(self, service):
        assert service._is_lec_exempt("TDY") is True

    def test_lec_not_exempt_im(self, service):
        assert service._is_lec_exempt("IM") is False

    def test_lec_not_exempt_cardio(self, service):
        assert service._is_lec_exempt("CARDIO") is False

    def test_intern_continuity_exempt_nf(self, service):
        assert service._is_intern_continuity_exempt("NF") is True

    def test_intern_continuity_exempt_kap(self, service):
        assert service._is_intern_continuity_exempt("KAP") is True

    def test_intern_continuity_not_exempt_im(self, service):
        assert service._is_intern_continuity_exempt("IM") is False

    def test_intern_continuity_not_exempt_cardio(self, service):
        assert service._is_intern_continuity_exempt("CARDIO") is False


# ============================================================================
# _get_kap_codes
# ============================================================================


class TestGetKapCodes:
    """Tests for Kapiolani L&D schedule codes."""

    def test_monday(self, service):
        assert service._get_kap_codes(date(2025, 3, 17)) == ("KAP", "OFF")

    def test_tuesday(self, service):
        assert service._get_kap_codes(date(2025, 3, 18)) == ("OFF", "OFF")

    def test_wednesday(self, service):
        assert service._get_kap_codes(date(2025, 3, 19)) == ("C", "LEC")

    def test_thursday(self, service):
        assert service._get_kap_codes(date(2025, 3, 20)) == ("KAP", "KAP")

    def test_friday(self, service):
        assert service._get_kap_codes(date(2025, 3, 21)) == ("KAP", "KAP")

    def test_saturday(self, service):
        assert service._get_kap_codes(date(2025, 3, 22)) == ("KAP", "KAP")


# ============================================================================
# _get_ldnf_codes
# ============================================================================


class TestGetLdnfCodes:
    """Tests for L&D Night Float schedule codes."""

    def test_weekday(self, service):
        # Mon-Thu: OFF/LDNF
        assert service._get_ldnf_codes(date(2025, 3, 17)) == ("OFF", "LDNF")  # Monday
        assert service._get_ldnf_codes(date(2025, 3, 20)) == ("OFF", "LDNF")  # Thursday

    def test_friday(self, service):
        assert service._get_ldnf_codes(date(2025, 3, 21)) == ("C", "OFF")

    def test_saturday(self, service):
        assert service._get_ldnf_codes(date(2025, 3, 22)) == ("W", "W")

    def test_sunday(self, service):
        assert service._get_ldnf_codes(date(2025, 3, 23)) == ("W", "W")


# ============================================================================
# _get_nf_codes
# ============================================================================


class TestGetNfCodes:
    """Tests for Night Float schedule codes."""

    def test_nf_weekday(self, service):
        assert service._get_nf_codes("NF", date(2025, 3, 17)) == ("OFF", "NF")  # Monday
        assert service._get_nf_codes("NF", date(2025, 3, 21)) == ("OFF", "NF")  # Friday

    def test_nf_weekend(self, service):
        assert service._get_nf_codes("NF", date(2025, 3, 22)) == ("W", "W")  # Saturday
        assert service._get_nf_codes("NF", date(2025, 3, 23)) == ("W", "W")  # Sunday

    def test_pednf_weekday(self, service):
        assert service._get_nf_codes("PEDNF", date(2025, 3, 17)) == ("OFF", "PedNF")

    def test_pednf_saturday_off(self, service):
        assert service._get_nf_codes("PEDNF", date(2025, 3, 22)) == ("W", "W")

    def test_pednf_sunday_on(self, service):
        # Sunday is weekday-like for PedNF (only Saturday off)
        assert service._get_nf_codes("PEDNF", date(2025, 3, 23)) == ("OFF", "PedNF")


# ============================================================================
# _get_hilo_codes
# ============================================================================


class TestGetHiloCodes:
    """Tests for Hilo/Okinawa TDY schedule codes."""

    def test_day_0_clinic(self, service):
        # First day of block: clinic before leaving
        block_start = date(2025, 3, 13)
        assert service._get_hilo_codes(date(2025, 3, 13), block_start) == ("C", "C")

    def test_day_1_clinic(self, service):
        block_start = date(2025, 3, 13)
        assert service._get_hilo_codes(date(2025, 3, 14), block_start) == ("C", "C")

    def test_day_2_tdy(self, service):
        block_start = date(2025, 3, 13)
        assert service._get_hilo_codes(date(2025, 3, 15), block_start) == ("TDY", "TDY")

    def test_day_19_return_clinic(self, service):
        block_start = date(2025, 3, 13)
        assert service._get_hilo_codes(date(2025, 4, 1), block_start) == ("C", "C")

    def test_mid_tdy(self, service):
        block_start = date(2025, 3, 13)
        assert service._get_hilo_codes(date(2025, 3, 25), block_start) == ("TDY", "TDY")


# ============================================================================
# _pattern_week_number / _pattern_day_of_week
# ============================================================================


class TestPatternHelpers:
    """Tests for pattern week/day calculation."""

    def test_week_number_first_week(self, service):
        assert service._pattern_week_number(date(2025, 3, 13), date(2025, 3, 13)) == 1
        assert service._pattern_week_number(date(2025, 3, 19), date(2025, 3, 13)) == 1

    def test_week_number_second_week(self, service):
        assert service._pattern_week_number(date(2025, 3, 20), date(2025, 3, 13)) == 2
        assert service._pattern_week_number(date(2025, 3, 26), date(2025, 3, 13)) == 2

    def test_week_number_fourth_week(self, service):
        assert service._pattern_week_number(date(2025, 4, 3), date(2025, 3, 13)) == 4

    def test_day_of_week_sunday_is_zero(self, service):
        # Python: Sunday = 6, pattern: Sunday = 0
        assert service._pattern_day_of_week(date(2025, 3, 16)) == 0  # Sunday

    def test_day_of_week_monday_is_one(self, service):
        assert service._pattern_day_of_week(date(2025, 3, 17)) == 1  # Monday

    def test_day_of_week_saturday_is_six(self, service):
        assert service._pattern_day_of_week(date(2025, 3, 22)) == 6  # Saturday

    def test_day_of_week_wednesday(self, service):
        assert service._pattern_day_of_week(date(2025, 3, 19)) == 3  # Wednesday


# ============================================================================
# Constants validation
# ============================================================================


class TestConstants:
    """Tests for module-level rotation constants."""

    def test_night_float_rotations(self):
        assert "NF" in _NIGHT_FLOAT_ROTATIONS
        assert "PEDNF" in _NIGHT_FLOAT_ROTATIONS
        assert "LDNF" in _NIGHT_FLOAT_ROTATIONS

    def test_lec_exempt_includes_night_float(self):
        # All night float rotations should be LEC-exempt
        for rot in _NIGHT_FLOAT_ROTATIONS:
            assert rot in _LEC_EXEMPT_ROTATIONS, f"{rot} should be LEC-exempt"

    def test_lec_exempt_includes_offsite(self):
        assert "TDY" in _LEC_EXEMPT_ROTATIONS
        assert "HILO" in _LEC_EXEMPT_ROTATIONS
        assert "OKI" in _LEC_EXEMPT_ROTATIONS

    def test_offsite_rotations(self):
        assert "TDY" in _OFFSITE_ROTATIONS
        assert "HILO" in _OFFSITE_ROTATIONS
        assert "OKI" in _OFFSITE_ROTATIONS

    def test_kap_rotations(self):
        assert "KAP" in _KAP_ROTATIONS

    def test_intern_continuity_exempt_superset_of_night_float(self):
        for rot in _NIGHT_FLOAT_ROTATIONS:
            assert rot in _INTERN_CONTINUITY_EXEMPT_ROTATIONS, (
                f"{rot} should be intern continuity exempt"
            )

    def test_saturday_off_rotations_includes_inpatient(self):
        for rot in ("IM", "IMW", "PEDW", "ICU", "CCU", "NICU"):
            assert rot in _SATURDAY_OFF_ROTATIONS, f"{rot} should have Saturday off"

    def test_rotation_aliases_values_are_canonical(self):
        """Alias values should be short canonical codes."""
        for alias, canonical in _ROTATION_ALIASES.items():
            assert canonical == canonical.upper(), (
                f"Canonical code {canonical} should be uppercase"
            )
            assert len(canonical) <= 10, f"Canonical code {canonical} too long"
