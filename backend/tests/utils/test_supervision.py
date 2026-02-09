"""Tests for FMC supervision ratio helpers."""

from types import SimpleNamespace

import pytest

from app.utils.supervision import (
    activity_is_virtual_clinic,
    activity_provides_supervision,
    activity_requires_fmc_supervision,
)


def _make_activity(
    code="C", display_abbreviation=None, is_supervision=False, capacity_units=None
):
    """Create a mock activity object."""
    return SimpleNamespace(
        code=code,
        display_abbreviation=display_abbreviation or code,
        is_supervision=is_supervision,
        capacity_units=capacity_units,
    )


# ============================================================================
# activity_is_virtual_clinic
# ============================================================================


class TestActivityIsVirtualClinic:
    """Tests for activity_is_virtual_clinic."""

    def test_cv_code(self):
        assert activity_is_virtual_clinic(_make_activity(code="CV")) is True

    def test_cv_display_abbreviation(self):
        assert (
            activity_is_virtual_clinic(
                _make_activity(code="X", display_abbreviation="CV")
            )
            is True
        )

    def test_non_cv_code(self):
        assert activity_is_virtual_clinic(_make_activity(code="C")) is False

    def test_none_activity(self):
        assert activity_is_virtual_clinic(None) is False

    def test_case_insensitive(self):
        assert activity_is_virtual_clinic(_make_activity(code="cv")) is True

    def test_whitespace_handled(self):
        assert activity_is_virtual_clinic(_make_activity(code=" CV ")) is True


# ============================================================================
# activity_provides_supervision
# ============================================================================


class TestActivityProvidesSupervision:
    """Tests for activity_provides_supervision."""

    def test_supervision_activity(self):
        assert (
            activity_provides_supervision(_make_activity(is_supervision=True)) is True
        )

    def test_non_supervision_activity(self):
        assert (
            activity_provides_supervision(_make_activity(is_supervision=False)) is False
        )

    def test_none_activity(self):
        assert activity_provides_supervision(None) is False


# ============================================================================
# activity_requires_fmc_supervision
# ============================================================================


class TestActivityRequiresFmcSupervision:
    """Tests for activity_requires_fmc_supervision."""

    def test_clinic_requires_supervision(self):
        assert activity_requires_fmc_supervision(_make_activity(code="C")) is True

    def test_virtual_clinic_requires_supervision(self):
        assert activity_requires_fmc_supervision(_make_activity(code="CV")) is True

    def test_supervision_activity_does_not_require_supervision(self):
        """Supervisors don't need supervision themselves."""
        assert (
            activity_requires_fmc_supervision(
                _make_activity(code="AT", is_supervision=True)
            )
            is False
        )

    def test_non_capacity_code(self):
        assert activity_requires_fmc_supervision(_make_activity(code="OFF")) is False

    def test_none_activity(self):
        assert activity_requires_fmc_supervision(None) is False

    def test_sm_requires_supervision(self):
        assert activity_requires_fmc_supervision(_make_activity(code="SM")) is True

    def test_zero_capacity_excluded(self):
        assert (
            activity_requires_fmc_supervision(
                _make_activity(code="C", capacity_units=0)
            )
            is False
        )
