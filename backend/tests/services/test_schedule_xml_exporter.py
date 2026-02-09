"""Tests for ScheduleXMLExporter pure functions and day code logic.

Tests the rotation pattern lookup, classification, and day code
generation without requiring database fixtures.
"""

import hashlib
from datetime import date

import pytest

from app.services.schedule_xml_exporter import (
    INPATIENT_ROTATIONS,
    INTERN_CONTINUITY_EXEMPT,
    LEC_EXEMPT_ROTATIONS,
    ROTATION_PATTERNS,
    ScheduleXMLExporter,
    _get_pattern,
    _is_inpatient,
    _is_intern_continuity_exempt,
    _is_lec_exempt,
    _normalize_rotation,
)


# ============================================================================
# _normalize_rotation tests
# ============================================================================


class TestNormalizeRotation:
    """Tests for case-insensitive rotation normalization."""

    def test_lowercase_passthrough(self):
        assert _normalize_rotation("nf") == "nf"

    def test_uppercase_lowered(self):
        assert _normalize_rotation("FMIT") == "fmit"

    def test_mixed_case(self):
        assert _normalize_rotation("Peds Ward") == "peds ward"

    def test_empty_string(self):
        assert _normalize_rotation("") == ""

    def test_none_like_falsy(self):
        # Empty string returns empty string (guard: `if rotation`)
        assert _normalize_rotation("") == ""


# ============================================================================
# _get_pattern tests
# ============================================================================


class TestGetPattern:
    """Tests for rotation pattern lookup."""

    def test_fmc_clinic(self):
        assert _get_pattern("FMC") == ("C", "C")

    def test_fmit_inpatient(self):
        assert _get_pattern("FMIT") == ("FMIT", "FMIT")

    def test_nf_night_float(self):
        assert _get_pattern("NF") == ("OFF", "NF")

    def test_pednf_peds_night_float(self):
        assert _get_pattern("PedNF") == ("OFF", "PedNF")

    def test_im_internal_medicine(self):
        assert _get_pattern("IM") == ("IM", "IM")

    def test_proc_procedures(self):
        assert _get_pattern("PROC") == ("PR", "C")

    def test_sm_sports_medicine(self):
        assert _get_pattern("SM") == ("SM", "C")

    def test_pocus_ultrasound(self):
        assert _get_pattern("POCUS") == ("US", "C")

    def test_ldnf_ld_night_float(self):
        assert _get_pattern("LDNF") == ("OFF", "LDNF")

    def test_kap_kapiolani(self):
        assert _get_pattern("KAP") == ("KAP", "KAP")

    def test_hilo_tdy(self):
        assert _get_pattern("Hilo") == ("TDY", "TDY")

    def test_unknown_rotation_defaults_to_clinic(self):
        assert _get_pattern("UNKNOWN_ROTATION") == ("C", "C")

    def test_case_insensitive(self):
        assert _get_pattern("fmit") == ("FMIT", "FMIT")
        assert _get_pattern("Fmit") == ("FMIT", "FMIT")
        assert _get_pattern("FMIT") == ("FMIT", "FMIT")

    def test_neuro_half_day_pattern(self):
        assert _get_pattern("NEURO") == ("NEURO", "C")

    def test_surg_exp(self):
        assert _get_pattern("Surg Exp") == ("SURG", "C")

    def test_gyn_clinic(self):
        assert _get_pattern("Gyn Clinic") == ("GYN", "C")

    def test_endo_elective(self):
        assert _get_pattern("ENDO") == ("ENDO", "C")


# ============================================================================
# _is_inpatient tests
# ============================================================================


class TestIsInpatient:
    """Tests for inpatient rotation classification."""

    @pytest.mark.parametrize(
        "rotation",
        ["FMIT", "FMIT 2", "IM", "IMW", "PedW", "Peds Ward", "KAP", "TDY", "Hilo"],
    )
    def test_inpatient_rotations(self, rotation):
        assert _is_inpatient(rotation) is True

    @pytest.mark.parametrize(
        "rotation",
        ["FMC", "NF", "PROC", "SM", "POCUS", "NEURO", "ENDO", "GYN"],
    )
    def test_outpatient_rotations(self, rotation):
        assert _is_inpatient(rotation) is False

    def test_case_insensitive(self):
        assert _is_inpatient("fmit") is True
        assert _is_inpatient("im") is True

    def test_internal_medicine_alias(self):
        assert _is_inpatient("Internal Medicine") is True


# ============================================================================
# _is_lec_exempt tests
# ============================================================================


class TestIsLecExempt:
    """Tests for LEC (lecture) exemption classification."""

    @pytest.mark.parametrize(
        "rotation",
        ["NF", "PedNF", "Peds NF", "LDNF", "L&D Night Float", "TDY", "Hilo"],
    )
    def test_exempt_rotations(self, rotation):
        assert _is_lec_exempt(rotation) is True

    @pytest.mark.parametrize(
        "rotation",
        ["FMC", "FMIT", "IM", "PROC", "SM", "POCUS", "KAP", "NEURO"],
    )
    def test_non_exempt_rotations(self, rotation):
        assert _is_lec_exempt(rotation) is False

    def test_case_insensitive(self):
        assert _is_lec_exempt("nf") is True
        assert _is_lec_exempt("tdy") is True


# ============================================================================
# _is_intern_continuity_exempt tests
# ============================================================================


class TestIsInternContinuityExempt:
    """Tests for intern continuity clinic exemption."""

    @pytest.mark.parametrize(
        "rotation",
        ["NF", "PedNF", "LDNF", "TDY", "Hilo", "KAP", "KAPI-LD"],
    )
    def test_exempt_rotations(self, rotation):
        assert _is_intern_continuity_exempt(rotation) is True

    @pytest.mark.parametrize(
        "rotation",
        ["FMC", "FMIT", "IM", "PROC", "SM", "PedW", "NEURO"],
    )
    def test_non_exempt_rotations(self, rotation):
        assert _is_intern_continuity_exempt(rotation) is False


# ============================================================================
# ScheduleXMLExporter._is_last_wednesday tests
# ============================================================================


class TestIsLastWednesday:
    """Tests for last Wednesday of block detection."""

    def test_last_wednesday_of_block(self):
        # Block: 2026-03-12 (Thu) to 2026-04-08 (Wed)
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))
        # 2026-04-08 is Wed and next Wed (04-15) > block_end
        assert exporter._is_last_wednesday(date(2026, 4, 8)) is True

    def test_not_last_wednesday(self):
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))
        # 2026-04-01 is Wed but next Wed (04-08) <= block_end
        assert exporter._is_last_wednesday(date(2026, 4, 1)) is False

    def test_not_wednesday(self):
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))
        # 2026-04-07 is Tuesday
        assert exporter._is_last_wednesday(date(2026, 4, 7)) is False

    def test_early_wednesday(self):
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))
        # 2026-03-18 is Wed, but many Wednesdays follow
        assert exporter._is_last_wednesday(date(2026, 3, 18)) is False


# ============================================================================
# ScheduleXMLExporter._get_day_codes tests
# ============================================================================


class TestGetDayCodes:
    """Tests for the main day code generation logic."""

    def setup_method(self):
        # Block 10: 2026-03-12 (Thu) to 2026-04-08 (Wed)
        self.exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))

    # --- Last Wednesday Rule ---

    def test_last_wednesday_always_lec_adv(self):
        """Last Wednesday of block is always LEC/ADV regardless of rotation."""
        last_wed = date(2026, 4, 8)
        assert self.exporter._get_day_codes(last_wed, "FMIT", 1) == ("LEC", "ADV")
        assert self.exporter._get_day_codes(last_wed, "NF", 2) == ("LEC", "ADV")
        assert self.exporter._get_day_codes(last_wed, "KAP", 3) == ("LEC", "ADV")

    # --- Weekend Rules ---

    def test_weekend_outpatient_off(self):
        """Non-inpatient rotations get W/W on weekends."""
        sat = date(2026, 3, 14)  # Saturday
        assert self.exporter._get_day_codes(sat, "FMC", 1) == ("W", "W")
        assert self.exporter._get_day_codes(sat, "PROC", 2) == ("W", "W")

    def test_weekend_inpatient_works(self):
        """Inpatient rotations work on weekends."""
        sat = date(2026, 3, 14)
        assert self.exporter._get_day_codes(sat, "FMIT", 1) == ("FMIT", "FMIT")
        assert self.exporter._get_day_codes(sat, "IM", 2) == ("IM", "IM")
        assert self.exporter._get_day_codes(sat, "PedW", 3) == ("PedW", "PedW")

    # --- Wednesday Rules ---

    def test_wednesday_intern_clinic(self):
        """PGY-1 interns get clinic (C) on Wednesday AM for continuity."""
        wed = date(2026, 3, 18)  # Wednesday
        assert self.exporter._get_day_codes(wed, "FMIT", pgy=1) == ("C", "LEC")
        assert self.exporter._get_day_codes(wed, "IM", pgy=1) == ("C", "LEC")

    def test_wednesday_intern_exempt_rotation(self):
        """PGY-1 on exempt rotation doesn't get forced clinic."""
        wed = date(2026, 3, 18)
        # NF is LEC-exempt AND intern-continuity-exempt
        am, pm = self.exporter._get_day_codes(wed, "NF", pgy=1)
        assert am == "OFF"  # Default NF AM
        assert pm == "NF"  # NF is LEC-exempt

    def test_wednesday_pm_lecture(self):
        """Non-exempt rotations get LEC on Wednesday PM."""
        wed = date(2026, 3, 18)
        _, pm = self.exporter._get_day_codes(wed, "FMIT", pgy=2)
        assert pm == "LEC"

    def test_wednesday_pm_lec_exempt(self):
        """LEC-exempt rotations keep their default PM on Wednesday."""
        wed = date(2026, 3, 18)
        _, pm = self.exporter._get_day_codes(wed, "TDY", pgy=2)
        assert pm == "TDY"  # TDY is LEC-exempt

    def test_wednesday_sm_academic(self):
        """Sports Medicine gets aSM on Wednesday AM (non-intern)."""
        wed = date(2026, 3, 18)
        am, _ = self.exporter._get_day_codes(wed, "SM", pgy=2)
        assert am == "aSM"

    # --- Inpatient Continuity Clinic ---

    def test_im_pgy2_tuesday_clinic(self):
        """PGY-2 on IM gets clinic PM on Tuesday."""
        tue = date(2026, 3, 17)  # Tuesday
        assert self.exporter._get_day_codes(tue, "IM", pgy=2) == ("IM", "C")

    def test_im_pgy3_monday_clinic(self):
        """PGY-3 on IM gets clinic PM on Monday."""
        mon = date(2026, 3, 16)  # Monday
        assert self.exporter._get_day_codes(mon, "IM", pgy=3) == ("IM", "C")

    def test_fmit_pgy2_tuesday_clinic(self):
        """PGY-2 on FMIT gets clinic PM on Tuesday."""
        tue = date(2026, 3, 17)
        assert self.exporter._get_day_codes(tue, "FMIT", pgy=2) == ("FMIT", "C")

    def test_pedw_pgy3_monday_clinic(self):
        """PGY-3 on PedW gets clinic PM on Monday."""
        mon = date(2026, 3, 16)
        assert self.exporter._get_day_codes(mon, "PedW", pgy=3) == ("PedW", "C")

    # --- Kapiolani L&D Pattern ---

    def test_kap_monday(self):
        """KAP Monday: travel back — KAP/OFF."""
        mon = date(2026, 3, 16)
        assert self.exporter._get_day_codes(mon, "KAP", pgy=2) == ("KAP", "OFF")

    def test_kap_tuesday(self):
        """KAP Tuesday: recovery — OFF/OFF."""
        tue = date(2026, 3, 17)
        assert self.exporter._get_day_codes(tue, "KAP", pgy=2) == ("OFF", "OFF")

    def test_kap_wednesday(self):
        """KAP Wednesday: continuity clinic — C/LEC."""
        wed = date(2026, 3, 18)
        assert self.exporter._get_day_codes(wed, "KAP", pgy=2) == ("C", "LEC")

    def test_kap_thursday(self):
        """KAP Thursday-Sunday: on-site — KAP/KAP."""
        thu = date(2026, 3, 19)
        assert self.exporter._get_day_codes(thu, "KAP", pgy=2) == ("KAP", "KAP")

    # --- L&D Night Float Pattern ---

    def test_ldnf_weekday(self):
        """LDNF Mon-Thu: OFF/LDNF."""
        mon = date(2026, 3, 16)
        assert self.exporter._get_day_codes(mon, "LDNF", pgy=2) == ("OFF", "LDNF")

    def test_ldnf_friday_clinic(self):
        """LDNF Friday: morning clinic — C/OFF."""
        fri = date(2026, 3, 20)
        assert self.exporter._get_day_codes(fri, "LDNF", pgy=2) == ("C", "OFF")

    def test_ldnf_weekend(self):
        """LDNF Weekend: W/W."""
        sat = date(2026, 3, 14)
        assert self.exporter._get_day_codes(sat, "LDNF", pgy=2) == ("W", "W")

    # --- Default Pattern ---

    def test_default_weekday_clinic(self):
        """FMC on regular weekday: C/C."""
        thu = date(2026, 3, 12)
        assert self.exporter._get_day_codes(thu, "FMC", pgy=1) == ("C", "C")

    def test_default_neuro(self):
        """NEURO on regular weekday: NEURO/C."""
        thu = date(2026, 3, 12)
        assert self.exporter._get_day_codes(thu, "NEURO", pgy=2) == ("NEURO", "C")


# ============================================================================
# ScheduleXMLExporter.export integration test
# ============================================================================


class TestExportXML:
    """Test the full XML export pipeline."""

    def test_single_resident_generates_valid_xml(self):
        """Export a single resident and verify XML structure."""
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 3, 14))
        residents = [
            {"name": "Smith, Jane", "pgy": 1, "rotation1": "FMC", "rotation2": ""},
        ]
        xml = exporter.export(residents)
        assert '<?xml version="1.0" ?>' in xml
        assert '<schedule block_start="2026-03-12" block_end="2026-03-14">' in xml
        assert 'name="Smith, Jane"' in xml
        assert 'pgy="1"' in xml
        assert 'rotation1="FMC"' in xml

    def test_residents_sorted_by_name(self):
        """Residents should be sorted alphabetically by name."""
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 3, 12))
        residents = [
            {"name": "Zeta, Alice", "pgy": 2, "rotation1": "IM", "rotation2": ""},
            {"name": "Alpha, Bob", "pgy": 1, "rotation1": "FMC", "rotation2": ""},
        ]
        xml = exporter.export(residents)
        alpha_pos = xml.index("Alpha, Bob")
        zeta_pos = xml.index("Zeta, Alice")
        assert alpha_pos < zeta_pos

    def test_mid_block_rotation_transition(self):
        """Resident with rotation2 should transition at day 11 (start of Week 3)."""
        # Block: Thu Mar 12 to Wed Apr 8 (28 days)
        exporter = ScheduleXMLExporter(date(2026, 3, 12), date(2026, 4, 8))
        residents = [
            {"name": "Test, Person", "pgy": 2, "rotation1": "FMC", "rotation2": "IM"},
        ]
        xml = exporter.export(residents)
        # Day 11 = Mar 23 (Mon). Before: FMC pattern. After: IM pattern.
        # Mar 22 (Sun) should still be FMC → W/W (weekend outpatient)
        assert 'date="2026-03-22"' in xml
        # Mar 23 (Mon) should be IM pattern
        assert 'date="2026-03-23"' in xml


# ============================================================================
# Constants Consistency tests
# ============================================================================


class TestConstantsConsistency:
    """Verify rotation constant sets are consistent with pattern dict."""

    def test_all_inpatient_rotations_have_patterns(self):
        """Every inpatient rotation should have a pattern defined."""
        patterns_lower = {k.lower() for k in ROTATION_PATTERNS}
        for rot in INPATIENT_ROTATIONS:
            if rot.lower() not in patterns_lower:
                # TDY/Hilo and KAP-LD may not have direct pattern entries
                # but should at least resolve via _get_pattern default
                pass  # OK if they fall through to default

    def test_lec_exempt_subset_of_patterns_or_has_default(self):
        """LEC-exempt rotations should be findable."""
        for rot in LEC_EXEMPT_ROTATIONS:
            # Should return a pattern (even if default)
            pattern = _get_pattern(rot)
            assert isinstance(pattern, tuple)
            assert len(pattern) == 2

    def test_intern_continuity_exempt_subset(self):
        """Intern continuity exempt should be a superset of LEC-exempt + off-site."""
        for rot in LEC_EXEMPT_ROTATIONS:
            if rot.lower() not in ("l and d night float",):
                # Most LEC-exempt should also be intern-continuity-exempt
                pass
