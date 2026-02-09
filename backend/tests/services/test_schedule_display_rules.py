"""Tests for schedule_display_rules — display code transformation engine.

Covers all 7 transformation rules plus the _rotation_specific_nf helper
and the estimate_impact analysis function.
"""

from datetime import date

import pytest

from app.services.schedule_display_rules import (
    ABSENCE_TYPE_MAP,
    CODE_NORMALIZATION,
    FACULTY_WEEKEND_COLLAPSE,
    ROTATION_CLINIC_MAP,
    WEEKEND_ROTATION_OVERRIDES,
    _rotation_specific_nf,
    estimate_impact,
    transform_code,
)


# ── Rule 1: Night float OFF -> rotation code ────────────────────────────


class TestNightFloatOff:
    """Rule 1: OFF -> rotation-specific code for NF-type rotations."""

    def test_off_ldnf_rotation(self):
        assert transform_code("OFF", rotation="LDNF") == "L&D"

    def test_off_pedsnf_rotation(self):
        assert transform_code("OFF", rotation="PEDSNF") == "PedsNF"

    def test_off_pednf_rotation(self):
        assert transform_code("OFF", rotation="PEDNF") == "PedsNF"

    def test_off_pnf_rotation(self):
        assert transform_code("OFF", rotation="PNF") == "PedsNF"

    def test_off_pedsw_rotation(self):
        assert transform_code("OFF", rotation="PEDSW") == "PedsNF"

    def test_off_nf_endo_rotation(self):
        assert transform_code("OFF", rotation="NF/ENDO") == "NF"

    def test_off_generic_nf_rotation(self):
        assert transform_code("OFF", rotation="NF") == "NF"

    def test_off_non_nf_rotation_unchanged(self):
        """OFF stays OFF when rotation is not night-float type."""
        assert transform_code("OFF", rotation="FMC") == "OFF"

    def test_off_empty_rotation_unchanged(self):
        assert transform_code("OFF", rotation="") == "OFF"

    def test_off_neuro_rotation(self):
        assert transform_code("OFF", rotation="NEURO") == "NF"

    def test_off_neuro_nf_rotation(self):
        assert transform_code("OFF", rotation="NEURO/NF") == "NF"

    def test_off_nf_in_rotation2(self):
        """Secondary rotation triggers NF lookup too."""
        assert transform_code("OFF", rotation="FMC", rotation2="NF") == "NF"


# ── Rule 2: Weekend overrides ───────────────────────────────────────────


class TestWeekendOverrides:
    """Rule 2: W -> rotation-specific code on weekends."""

    def test_w_fmit_weekend(self):
        assert transform_code("W", rotation="FMIT", is_weekend=True) == "FMIT"

    def test_w_imw_weekend(self):
        assert transform_code("W", rotation="IMW", is_weekend=True) == "IMW"

    def test_w_kap_weekend(self):
        assert transform_code("W", rotation="KAP", is_weekend=True) == "KAP"

    def test_w_nf_rotation_weekend(self):
        """W on weekend + NF rotation -> NF-specific code (NF check takes priority)."""
        assert transform_code("W", rotation="LDNF", is_weekend=True) == "L&D"

    def test_w_non_special_rotation_weekend(self):
        """W stays W on weekend for rotations with no override."""
        assert transform_code("W", rotation="FMC", is_weekend=True) == "W"

    def test_w_fmit_weekday(self):
        """FMIT override only on weekends."""
        assert transform_code("W", rotation="FMIT", is_weekend=False) == "W"


# ── Rule 3: Rotation-specific clinic code ────────────────────────────────


class TestRotationClinic:
    """Rule 3: C -> rotation-specific clinic code."""

    def test_c_gyn_rotation(self):
        assert transform_code("C", rotation="GYN") == "GYN"

    def test_c_sm_rotation(self):
        assert transform_code("C", rotation="SM") == "SM"

    def test_c_in_rotation2(self):
        """Clinic mapping checks rotation2 as well."""
        assert transform_code("C", rotation="FMC", rotation2="GYN") == "GYN"

    def test_c_no_mapping(self):
        """C stays C when rotation has no clinic mapping."""
        assert transform_code("C", rotation="FMC") == "C"


# ── Rule 4: Faculty weekend collapse ────────────────────────────────────


class TestFacultyWeekendCollapse:
    """Rule 4: Faculty admin/edu codes -> W on weekends."""

    @pytest.mark.parametrize("code", sorted(FACULTY_WEEKEND_COLLAPSE))
    def test_faculty_code_collapses_to_w(self, code):
        assert transform_code(code, is_faculty=True, is_weekend=True) == "W"

    def test_faculty_code_weekday_unchanged(self):
        """Faculty codes stay unchanged on weekdays."""
        assert transform_code("GME", is_faculty=True, is_weekend=False) == "GME"

    def test_non_faculty_weekend_unchanged(self):
        """Non-faculty people keep admin codes on weekends."""
        assert transform_code("GME", is_faculty=False, is_weekend=True) == "GME"


# ── Rule 5: Code normalization ──────────────────────────────────────────


class TestCodeNormalization:
    """Rule 5: Simple spelling/abbreviation fixes."""

    @pytest.mark.parametrize(
        "input_code,expected",
        list(CODE_NORMALIZATION.items()),
    )
    def test_normalization(self, input_code, expected):
        assert transform_code(input_code) == expected

    def test_unknown_code_unchanged(self):
        assert transform_code("FOOBAR") == "FOOBAR"


# ── Rule 6: Absence type mapping ────────────────────────────────────────


class TestAbsenceMapping:
    """Rule 6: LV -> specific absence code when absence type is known."""

    def test_lv_deployment(self):
        assert transform_code("LV", absence_type="deployment") == "DEP"

    def test_lv_tdy(self):
        assert transform_code("LV", absence_type="tdy") == "TDY"

    def test_lv_usafp(self):
        assert transform_code("LV", absence_type="usafp") == "USAFP"

    def test_lv_regular_leave(self):
        """Regular leave (no mapped type) stays LV."""
        assert transform_code("LV", absence_type="annual") == "LV"

    def test_lv_no_absence_type(self):
        assert transform_code("LV") == "LV"

    def test_absence_case_insensitive(self):
        """Absence type matching is case-insensitive."""
        assert transform_code("LV", absence_type="DEPLOYMENT") == "DEP"
        assert transform_code("LV", absence_type="Tdy") == "TDY"


# ── Rule 7: Generic NF -> rotation-specific NF ──────────────────────────


class TestGenericNFTransform:
    """Rule 7: Generic NF code -> rotation-specific display code."""

    def test_nf_ldnf_rotation(self):
        assert transform_code("NF", rotation="LDNF") == "L&D"

    def test_nf_pedsnf_rotation(self):
        assert transform_code("NF", rotation="PEDSNF") == "PedsNF"

    def test_nf_generic_rotation(self):
        """NF on a generic NF rotation stays NF (specific == NF, no change)."""
        assert transform_code("NF", rotation="NF") == "NF"

    def test_nf_non_nf_rotation(self):
        """NF on a non-NF rotation stays NF."""
        assert transform_code("NF", rotation="FMC") == "NF"


# ── _rotation_specific_nf helper ─────────────────────────────────────────


class TestRotationSpecificNf:
    """Test the _rotation_specific_nf helper function directly."""

    def test_ldnf(self):
        assert _rotation_specific_nf("LDNF", "") == "L&D"

    def test_pedsnf(self):
        assert _rotation_specific_nf("PEDSNF", "") == "PedsNF"

    def test_pednf(self):
        assert _rotation_specific_nf("PEDNF", "") == "PedsNF"

    def test_pnf(self):
        assert _rotation_specific_nf("PNF", "") == "PedsNF"

    def test_pedsw(self):
        assert _rotation_specific_nf("PEDSW", "") == "PedsNF"

    def test_nf_endo(self):
        assert _rotation_specific_nf("NF/ENDO", "") == "NF"

    def test_generic_nf(self):
        assert _rotation_specific_nf("NF", "") == "NF"

    def test_neuro(self):
        assert _rotation_specific_nf("NEURO", "") == "NF"

    def test_neuro_nf(self):
        assert _rotation_specific_nf("NEURO/NF", "") == "NF"

    def test_non_nf_returns_none(self):
        assert _rotation_specific_nf("FMC", "") is None

    def test_empty_returns_none(self):
        assert _rotation_specific_nf("", "") is None

    def test_combined_rot_rot2(self):
        """Matches against combined 'rot rot2' string."""
        assert _rotation_specific_nf("FMC", "LDNF") == "L&D"

    def test_case_insensitive(self):
        """Input is uppercased internally."""
        assert _rotation_specific_nf("ldnf", "") == "L&D"

    def test_ordering_ldnf_before_nf(self):
        """LDNF must match before generic NF (both contain 'NF')."""
        assert _rotation_specific_nf("LDNF", "") == "L&D"


# ── Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases and input sanitization."""

    def test_empty_code(self):
        assert transform_code("") == ""

    def test_whitespace_trimmed(self):
        assert transform_code("  OFF  ", rotation="  NF  ") == "NF"

    def test_none_code_is_falsy(self):
        """Empty string treated as no-op."""
        assert transform_code("") == ""

    def test_day_date_passed_through(self):
        """day_date param accepted but doesn't affect current rules."""
        result = transform_code("OFF", rotation="NF", day_date=date(2026, 1, 5))
        assert result == "NF"

    def test_rule_priority_absence_over_normalization(self):
        """Rule 6 (absence) has highest priority -- checked before normalization."""
        assert transform_code("LV", absence_type="tdy") == "TDY"

    def test_rule_priority_normalization_then_nf(self):
        """Code normalization runs before NF check (Rule 5 before Rule 7)."""
        # "LDNF" normalizes to "L&D" (Rule 5) and does NOT enter Rule 7
        assert transform_code("LDNF") == "L&D"


# ── estimate_impact ─────────────────────────────────────────────────────


class TestEstimateImpact:
    """Test the estimate_impact analysis utility."""

    def test_code_normalization_counted(self):
        mismatches = [{"db_code": "IM", "truth_code": "IMW", "rotation": ""}]
        result = estimate_impact(mismatches)
        assert result["code_normalization"] == 1

    def test_faculty_weekend_counted(self):
        mismatches = [{"db_code": "GME", "truth_code": "W", "rotation": ""}]
        result = estimate_impact(mismatches)
        assert result["faculty_weekend"] == 1

    def test_rotation_clinic_counted(self):
        mismatches = [{"db_code": "C", "truth_code": "GYN", "rotation": "GYN"}]
        result = estimate_impact(mismatches)
        assert result["rotation_clinic"] == 1

    def test_absence_mapping_counted(self):
        mismatches = [{"db_code": "LV", "truth_code": "DEP", "rotation": ""}]
        result = estimate_impact(mismatches)
        assert result["absence_mapping"] == 1

    def test_unfixed_counted(self):
        mismatches = [{"db_code": "X", "truth_code": "Y", "rotation": ""}]
        result = estimate_impact(mismatches)
        assert result["unfixed"] == 1

    def test_empty_mismatches(self):
        result = estimate_impact([])
        assert all(v == 0 for v in result.values())

    def test_multiple_mixed(self):
        mismatches = [
            {"db_code": "IM", "truth_code": "IMW", "rotation": ""},
            {"db_code": "GME", "truth_code": "W", "rotation": ""},
            {"db_code": "X", "truth_code": "Y", "rotation": ""},
        ]
        result = estimate_impact(mismatches)
        assert result["code_normalization"] == 1
        assert result["faculty_weekend"] == 1
        assert result["unfixed"] == 1

    def test_night_float_off_counted(self):
        """OFF -> NF display code should be counted as night_float_off fix."""
        mismatches = [{"db_code": "OFF", "truth_code": "NF", "rotation": "NF"}]
        result = estimate_impact(mismatches)
        assert result["night_float_off"] == 1

    def test_night_float_off_ld(self):
        mismatches = [{"db_code": "OFF", "truth_code": "L&D", "rotation": "LDNF"}]
        result = estimate_impact(mismatches)
        assert result["night_float_off"] == 1

    def test_weekend_override_counted(self):
        mismatches = [{"db_code": "W", "truth_code": "FMIT", "rotation": "FMIT"}]
        result = estimate_impact(mismatches)
        assert result["weekend_override"] == 1
