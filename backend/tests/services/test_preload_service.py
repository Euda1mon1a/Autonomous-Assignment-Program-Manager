"""Tests for PreloadService pure functions and constants.

Tests rotation code normalization, schedule code determination for various
rotation types, date helper methods, and constant validation -- all without
database access.
"""

from datetime import date

import pytest

from app.services.preload_service import (
    _CLINIC_PATTERN_CODES,
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

    def test_d_plus_n_alias(self, service):
        assert service._canonical_rotation_code("D+N") == "DERM-NF"

    def test_c_plus_n_alias(self, service):
        assert service._canonical_rotation_code("C+N") == "CARDS-NF"


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

    def test_nf_combined_codes_in_all_classification_sets(self):
        """All NF combined codes must be in night float, LEC-exempt,
        intern-continuity-exempt, and Saturday-off sets."""
        nf_combined_codes = {
            "NF-CARDIO",
            "NF-FMIT-PG",
            "NF-DERM-PG",
            "CARDS-NF",
            "DERM-NF",
        }
        for code in nf_combined_codes:
            assert code in _NIGHT_FLOAT_ROTATIONS, f"{code} missing from NF set"
            assert code in _LEC_EXEMPT_ROTATIONS, f"{code} missing from LEC-exempt"
            assert code in _INTERN_CONTINUITY_EXEMPT_ROTATIONS, (
                f"{code} missing from intern-continuity-exempt"
            )
            assert code in _SATURDAY_OFF_ROTATIONS, f"{code} missing from Saturday-off"

    def test_clinic_pattern_codes(self):
        for code in ("C", "C-I", "C-N"):
            assert code in _CLINIC_PATTERN_CODES


# ============================================================================
# _get_rotation_preload_codes (complex branching logic)
# ============================================================================


class TestGetRotationPreloadCodes:
    """Tests for the central preload code determination method.

    This method determines AM/PM activity codes for each slot based on
    rotation type, date, PGY level, and block boundaries.
    """

    def test_empty_rotation_returns_none(self, service):
        assert service._get_rotation_preload_codes(
            "", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == (None, None)

    def test_last_wednesday_returns_lec_adv(self, service):
        # Block ends Apr 8 (Tue). Last Wednesday = Apr 2.
        assert service._get_rotation_preload_codes(
            "IM", date(2025, 4, 2), date(2025, 3, 13), date(2025, 4, 8), 1, True
        ) == ("LEC", "ADV")

    def test_last_wednesday_overrides_everything(self, service):
        # Even night float gets LEC/ADV on last Wednesday
        assert service._get_rotation_preload_codes(
            "NF", date(2025, 4, 2), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("LEC", "ADV")

    def test_saturday_off_for_im(self, service):
        # Saturday (Mar 22), IM is in _SATURDAY_OFF_ROTATIONS
        assert service._get_rotation_preload_codes(
            "IM", date(2025, 3, 22), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("W", "W")

    def test_saturday_off_skipped_with_time_off_patterns(self, service):
        # Saturday but has_time_off_patterns=True skips the W/W default
        result = service._get_rotation_preload_codes(
            "IM",
            date(2025, 3, 22),
            date(2025, 3, 13),
            date(2025, 4, 8),
            1,
            False,
            has_time_off_patterns=True,
        )
        assert result == (None, None)

    def test_offsite_tdy(self, service):
        # TDY rotation on a regular weekday
        assert service._get_rotation_preload_codes(
            "TDY", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("TDY", "TDY")

    def test_offsite_hilo_delegates(self, service):
        # HILO day 0 -> clinic
        assert service._get_rotation_preload_codes(
            "HILO", date(2025, 3, 13), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("C", "C")

    def test_offsite_oki_delegates(self, service):
        # OKI mid-block -> TDY
        assert service._get_rotation_preload_codes(
            "OKI", date(2025, 3, 25), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("TDY", "TDY")

    def test_kap_delegates(self, service):
        # KAP on Monday -> KAP/OFF
        assert service._get_rotation_preload_codes(
            "KAP", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("KAP", "OFF")

    def test_ldnf_delegates(self, service):
        # LDNF on Friday -> C/OFF
        assert service._get_rotation_preload_codes(
            "LDNF", date(2025, 3, 21), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("C", "OFF")

    def test_nf_delegates(self, service):
        # NF on Monday -> OFF/NF
        assert service._get_rotation_preload_codes(
            "NF", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("OFF", "NF")

    def test_pednf_delegates(self, service):
        # PEDNF on Monday -> OFF/PedNF
        assert service._get_rotation_preload_codes(
            "PEDNF", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("OFF", "PedNF")

    def test_wednesday_outpatient_pgy1_gets_continuity_and_lec(self, service):
        # Wed, outpatient, PGY1, non-exempt rotation
        assert service._get_rotation_preload_codes(
            "CARDIO",
            date(2025, 3, 19),
            date(2025, 3, 13),
            date(2025, 4, 8),
            pgy_level=1,
            is_outpatient=True,
        ) == ("C", "LEC")

    def test_wednesday_outpatient_pgy2_no_continuity(self, service):
        # Wed, outpatient, PGY2 -> no continuity clinic, just LEC
        assert service._get_rotation_preload_codes(
            "CARDIO",
            date(2025, 3, 19),
            date(2025, 3, 13),
            date(2025, 4, 8),
            pgy_level=2,
            is_outpatient=True,
        ) == (None, "LEC")

    def test_wednesday_inpatient_pgy1_no_continuity(self, service):
        # Wed, NOT outpatient, PGY1 -> no continuity, just LEC
        assert service._get_rotation_preload_codes(
            "CARDIO",
            date(2025, 3, 19),
            date(2025, 3, 13),
            date(2025, 4, 8),
            pgy_level=1,
            is_outpatient=False,
        ) == (None, "LEC")

    def test_wednesday_lec_exempt_rotation(self, service):
        # Wed, NF rotation -> exempt from LEC
        assert service._get_rotation_preload_codes(
            "NF", date(2025, 3, 19), date(2025, 3, 13), date(2025, 4, 8), 1, False
        ) == ("OFF", "NF")  # NF branch takes priority over Wednesday branch

    def test_regular_weekday_returns_none(self, service):
        # Thursday, regular rotation -> nothing to preload
        assert service._get_rotation_preload_codes(
            "CARDIO", date(2025, 3, 20), date(2025, 3, 13), date(2025, 4, 8), 1, True
        ) == (None, None)

    def test_regular_friday_returns_none(self, service):
        assert service._get_rotation_preload_codes(
            "CARDIO", date(2025, 3, 21), date(2025, 3, 13), date(2025, 4, 8), 1, True
        ) == (None, None)

    def test_wednesday_intern_continuity_exempt_rotation(self, service):
        # Wed, outpatient, PGY1, KAP (exempt from intern continuity)
        # KAP hits the KAP branch first, so it returns KAP Wednesday codes
        assert service._get_rotation_preload_codes(
            "KAP",
            date(2025, 3, 19),
            date(2025, 3, 13),
            date(2025, 4, 8),
            pgy_level=1,
            is_outpatient=True,
        ) == ("C", "LEC")  # KAP Wednesday pattern

    # -- NF Combined (NF-first) half-block tests --
    # Block: Mar 13 (Thu) – Apr 8 (Wed). Mid-block = Mar 27 (day 14).
    # First half (days 0-13): Night Float. Day 14: recovery. Second half (days 15+): specialty.

    def test_nf_combined_first_half_weekday(self, service):
        # Mon Mar 17 (day 4, first half) -> NF pattern
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 17),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == ("OFF", "NF")

    def test_nf_combined_second_half_weekday(self, service):
        # Mon Mar 31 (day 18, second half) -> specialty
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 31),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == ("CARDS", "CARDS")

    def test_nf_combined_mid_block_recovery(self, service):
        # Thu Mar 27 (day 14, mid-block) -> recovery
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 27),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == ("recovery", "recovery")

    def test_nf_combined_wednesday_deferred(self, service):
        # Wed Mar 19 (day 6) -> deferred to weekly_patterns (LEC)
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 19),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == (None, None)

    def test_nf_combined_sunday_off(self, service):
        # Sun Mar 16 (day 3) -> W/W
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 16),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == ("W", "W")

    def test_nf_combined_saturday_off(self, service):
        # Sat Mar 22 (day 9) -> W/W via SATURDAY_OFF_ROTATIONS (fires before handler)
        assert service._get_rotation_preload_codes(
            "NF-CARDIO",
            date(2025, 3, 22),
            date(2025, 3, 13),
            date(2025, 4, 8),
            3,
            False,
        ) == ("W", "W")

    def test_nf_fmit_second_half(self, service):
        # NF-FMIT-PG second half -> FMIT
        assert service._get_rotation_preload_codes(
            "NF-FMIT-PG",
            date(2025, 3, 31),
            date(2025, 3, 13),
            date(2025, 4, 8),
            1,
            False,
        ) == ("FMIT", "FMIT")

    def test_nf_derm_second_half(self, service):
        # NF-DERM-PG second half -> DERM
        assert service._get_rotation_preload_codes(
            "NF-DERM-PG",
            date(2025, 3, 31),
            date(2025, 3, 13),
            date(2025, 4, 8),
            2,
            False,
        ) == ("DERM", "DERM")

    def test_nf_combined_last_wednesday_overrides(self, service):
        # Last Wednesday Apr 2 -> LEC/ADV (fires before NF combined handler)
        assert service._get_rotation_preload_codes(
            "NF-CARDIO", date(2025, 4, 2), date(2025, 3, 13), date(2025, 4, 8), 3, False
        ) == ("LEC", "ADV")

    # -- Mirror/Reverse NF Combined (specialty-first) half-block tests --
    # First half (days 0-13): specialty. Day 14: recovery. Second half (days 15+): NF.

    def test_reverse_derm_nf_first_half(self, service):
        # Mon Mar 17 (first half) -> DERM/DERM (specialty first)
        assert service._get_rotation_preload_codes(
            "DERM-NF", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 2, False
        ) == ("DERM", "DERM")

    def test_reverse_derm_nf_second_half(self, service):
        # Mon Mar 31 (second half) -> OFF/NF (NF second)
        assert service._get_rotation_preload_codes(
            "DERM-NF", date(2025, 3, 31), date(2025, 3, 13), date(2025, 4, 8), 2, False
        ) == ("OFF", "NF")

    def test_reverse_derm_nf_mid_block(self, service):
        # Thu Mar 27 (day 14) -> recovery
        assert service._get_rotation_preload_codes(
            "DERM-NF", date(2025, 3, 27), date(2025, 3, 13), date(2025, 4, 8), 2, False
        ) == ("recovery", "recovery")

    def test_reverse_cards_nf_first_half(self, service):
        # CARDS-NF first half -> CARDS/CARDS
        assert service._get_rotation_preload_codes(
            "CARDS-NF", date(2025, 3, 17), date(2025, 3, 13), date(2025, 4, 8), 3, False
        ) == ("CARDS", "CARDS")

    def test_reverse_cards_nf_second_half(self, service):
        # CARDS-NF second half -> OFF/NF
        assert service._get_rotation_preload_codes(
            "CARDS-NF", date(2025, 3, 31), date(2025, 3, 13), date(2025, 4, 8), 3, False
        ) == ("OFF", "NF")
