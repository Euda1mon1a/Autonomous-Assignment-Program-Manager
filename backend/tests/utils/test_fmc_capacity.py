"""Tests for FMC physical capacity calculation helpers."""

from types import SimpleNamespace

import pytest

from app.utils.fmc_capacity import (
    CV_CODES,
    FMC_CAPACITY_CODES,
    FMC_CLINIC_CODES,
    FMC_TEMPLATE_ABBREVS,
    PROC_VAS_CODES,
    SM_CAPACITY_CODES,
    _normalize_code,
    activity_capacity_units,
    activity_counts_toward_fmc_capacity,
    activity_counts_toward_fmc_capacity_for_template,
    activity_is_proc_or_vas,
    activity_is_sm_capacity,
    template_is_fmc_clinic,
)


def _make_activity(
    code="C", display_abbreviation=None, capacity_units=None, is_supervision=False
):
    """Create a mock activity object."""
    return SimpleNamespace(
        code=code,
        display_abbreviation=display_abbreviation or code,
        capacity_units=capacity_units,
        is_supervision=is_supervision,
    )


def _make_template(abbreviation="FMC", display_abbreviation=None):
    """Create a mock rotation template."""
    return SimpleNamespace(
        abbreviation=abbreviation,
        display_abbreviation=display_abbreviation,
    )


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    """Verify constant sets are well-formed."""

    def test_fmc_template_abbrevs(self):
        assert "C" in FMC_TEMPLATE_ABBREVS
        assert "CONT" in FMC_TEMPLATE_ABBREVS
        assert "CONTINUITY" in FMC_TEMPLATE_ABBREVS

    def test_fmc_clinic_codes(self):
        assert "C" in FMC_CLINIC_CODES
        assert "FM_CLINIC" in FMC_CLINIC_CODES

    def test_fmc_capacity_codes_excludes_cv(self):
        assert "CV" not in FMC_CAPACITY_CODES

    def test_cv_codes(self):
        assert "CV" in CV_CODES

    def test_sm_capacity_codes(self):
        assert "SM" in SM_CAPACITY_CODES
        assert "ASM" in SM_CAPACITY_CODES

    def test_proc_vas_codes(self):
        assert "PR" in PROC_VAS_CODES
        assert "PROC" in PROC_VAS_CODES


# ============================================================================
# _normalize_code
# ============================================================================


class TestNormalizeCode:
    """Tests for _normalize_code helper."""

    def test_normal_code(self):
        assert _normalize_code("C") == "C"

    def test_lowercase_uppercased(self):
        assert _normalize_code("c") == "C"

    def test_whitespace_stripped(self):
        assert _normalize_code("  C  ") == "C"

    def test_none_returns_empty(self):
        assert _normalize_code(None) == ""

    def test_empty_returns_empty(self):
        assert _normalize_code("") == ""


# ============================================================================
# activity_is_sm_capacity
# ============================================================================


class TestActivityIsSmCapacity:
    """Tests for activity_is_sm_capacity."""

    def test_sm_code(self):
        assert activity_is_sm_capacity(_make_activity(code="SM")) is True

    def test_asm_code(self):
        assert activity_is_sm_capacity(_make_activity(code="ASM")) is True

    def test_sm_clinic_code(self):
        assert activity_is_sm_capacity(_make_activity(code="SM_CLINIC")) is True

    def test_non_sm_code(self):
        assert activity_is_sm_capacity(_make_activity(code="C")) is False

    def test_none_activity(self):
        assert activity_is_sm_capacity(None) is False

    def test_sm_via_display_abbrev(self):
        assert (
            activity_is_sm_capacity(_make_activity(code="X", display_abbreviation="SM"))
            is True
        )


# ============================================================================
# activity_is_proc_or_vas
# ============================================================================


class TestActivityIsProcOrVas:
    """Tests for activity_is_proc_or_vas."""

    def test_proc_code(self):
        assert activity_is_proc_or_vas(_make_activity(code="PROC")) is True

    def test_pr_code(self):
        assert activity_is_proc_or_vas(_make_activity(code="PR")) is True

    def test_procedure_code(self):
        assert activity_is_proc_or_vas(_make_activity(code="PROCEDURE")) is True

    def test_non_proc_code(self):
        assert activity_is_proc_or_vas(_make_activity(code="C")) is False

    def test_none_activity(self):
        assert activity_is_proc_or_vas(None) is False

    def test_vas_not_in_proc_codes(self):
        """VAS is handled like clinic/SM, NOT as extra AT demand."""
        assert activity_is_proc_or_vas(_make_activity(code="VAS")) is False


# ============================================================================
# template_is_fmc_clinic
# ============================================================================


class TestTemplateIsFmcClinic:
    """Tests for template_is_fmc_clinic."""

    def test_c_template(self):
        assert template_is_fmc_clinic(_make_template(abbreviation="C")) is True

    def test_cont_template(self):
        assert template_is_fmc_clinic(_make_template(abbreviation="CONT")) is True

    def test_display_abbreviation_used(self):
        assert (
            template_is_fmc_clinic(
                _make_template(abbreviation="X", display_abbreviation="C")
            )
            is True
        )

    def test_non_fmc_template(self):
        assert template_is_fmc_clinic(_make_template(abbreviation="NF")) is False

    def test_none_template(self):
        assert template_is_fmc_clinic(None) is False

    def test_case_insensitive(self):
        assert template_is_fmc_clinic(_make_template(abbreviation="cont")) is True


# ============================================================================
# activity_counts_toward_fmc_capacity
# ============================================================================


class TestActivityCountsTowardFmcCapacity:
    """Tests for activity_counts_toward_fmc_capacity (without template)."""

    def test_clinic_code_counts(self):
        assert activity_counts_toward_fmc_capacity(_make_activity(code="C")) is True

    def test_sm_counts(self):
        assert activity_counts_toward_fmc_capacity(_make_activity(code="SM")) is True

    def test_cv_excluded(self):
        assert activity_counts_toward_fmc_capacity(_make_activity(code="CV")) is False

    def test_none_activity(self):
        assert activity_counts_toward_fmc_capacity(None) is False

    def test_zero_capacity_units_excluded(self):
        assert (
            activity_counts_toward_fmc_capacity(
                _make_activity(code="C", capacity_units=0)
            )
            is False
        )

    def test_negative_capacity_units_excluded(self):
        assert (
            activity_counts_toward_fmc_capacity(
                _make_activity(code="C", capacity_units=-1)
            )
            is False
        )


# ============================================================================
# activity_counts_toward_fmc_capacity_for_template
# ============================================================================


class TestActivityCountsForTemplate:
    """Tests for activity_counts_toward_fmc_capacity_for_template."""

    def test_sm_counts_regardless_of_template(self):
        template = _make_template(abbreviation="NF")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="SM"), template
            )
            is True
        )

    def test_proc_counts_regardless_of_template(self):
        template = _make_template(abbreviation="NF")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="PROC"), template
            )
            is True
        )

    def test_cv_excluded(self):
        template = _make_template(abbreviation="C")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="CV"), template
            )
            is False
        )

    def test_clinic_code_with_fmc_template(self):
        template = _make_template(abbreviation="C")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="C"), template
            )
            is True
        )

    def test_clinic_code_with_non_fmc_template(self):
        template = _make_template(abbreviation="NF")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="C"), template
            )
            is False
        )

    def test_v1_counts(self):
        template = _make_template(abbreviation="NF")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="V1"), template
            )
            is True
        )

    def test_none_activity(self):
        assert (
            activity_counts_toward_fmc_capacity_for_template(None, _make_template())
            is False
        )

    def test_zero_capacity_units_excluded(self):
        template = _make_template(abbreviation="C")
        assert (
            activity_counts_toward_fmc_capacity_for_template(
                _make_activity(code="C", capacity_units=0), template
            )
            is False
        )


# ============================================================================
# activity_capacity_units
# ============================================================================


class TestActivityCapacityUnits:
    """Tests for activity_capacity_units."""

    def test_none_activity_returns_0(self):
        assert activity_capacity_units(None) == 0

    def test_no_capacity_units_defaults_to_1(self):
        assert activity_capacity_units(_make_activity(code="C")) == 1

    def test_explicit_capacity_units(self):
        assert activity_capacity_units(_make_activity(code="C", capacity_units=3)) == 3

    def test_zero_units(self):
        assert activity_capacity_units(_make_activity(code="C", capacity_units=0)) == 0

    def test_negative_units_clamped_to_0(self):
        assert activity_capacity_units(_make_activity(code="C", capacity_units=-5)) == 0

    def test_invalid_units_defaults_to_1(self):
        assert (
            activity_capacity_units(_make_activity(code="C", capacity_units="invalid"))
            == 1
        )
