"""Tests for NF combined rotation constants and canonical_rotation_code.

Validates that:
- All combined NF codes resolve to themselves (not aliased away)
- NF-PEDS-PGY resolves to NF-PEDS-PG (combined), not PEDNF
- Classification sets include all combined codes
"""

from datetime import date, timedelta

import pytest

from app.services.preload.constants import (
    INTERN_CONTINUITY_EXEMPT_ROTATIONS,
    LEC_EXEMPT_ROTATIONS,
    NF_COMBINED_ACTIVITY_MAP,
    NIGHT_FLOAT_ROTATIONS,
    SATURDAY_OFF_ROTATIONS,
    canonical_rotation_code,
)
from app.services.preload.rotation_codes import get_rotation_preload_codes


class TestCanonicalRotationCode:
    """Combined NF codes must be preserved through canonical_rotation_code."""

    @pytest.mark.parametrize(
        "code",
        list(NF_COMBINED_ACTIVITY_MAP.keys()),
    )
    def test_combined_codes_are_canonical(self, code: str):
        """Every combined NF code should return itself."""
        assert canonical_rotation_code(code) == code

    def test_nf_peds_pgy_alias(self):
        """NF-PEDS-PGY should alias to NF-PEDS-PG (combined)."""
        assert canonical_rotation_code("NF-PEDS-PGY") == "NF-PEDS-PG"

    def test_nf_peds_pg_not_aliased_to_pednf(self):
        """NF-PEDS-PG is a combined rotation, NOT standalone Peds NF."""
        assert canonical_rotation_code("NF-PEDS-PG") == "NF-PEDS-PG"

    def test_plain_nf_peds_resolves_to_pednf(self):
        """Plain NF-PEDS (without -PG suffix) is standalone Peds NF."""
        assert canonical_rotation_code("NF-PEDS") == "PEDNF"

    def test_standalone_rotations_unchanged(self):
        """Non-combined codes should still work correctly."""
        assert canonical_rotation_code("NF") == "NF"
        assert canonical_rotation_code("FMIT") == "FMIT"
        assert canonical_rotation_code("HILO") == "HILO"
        assert canonical_rotation_code("KAP") == "KAP"
        assert canonical_rotation_code("PEDS-EM") == "PEDS-EM"


class TestClassificationSets:
    """All combined NF codes must be in the classification sets."""

    ALL_COMBINED = set(NF_COMBINED_ACTIVITY_MAP)

    def test_all_in_night_float_rotations(self):
        missing = self.ALL_COMBINED - NIGHT_FLOAT_ROTATIONS
        assert not missing, f"Missing from NIGHT_FLOAT_ROTATIONS: {missing}"

    def test_all_in_lec_exempt(self):
        missing = self.ALL_COMBINED - LEC_EXEMPT_ROTATIONS
        assert not missing, f"Missing from LEC_EXEMPT_ROTATIONS: {missing}"

    def test_all_in_saturday_off(self):
        missing = self.ALL_COMBINED - SATURDAY_OFF_ROTATIONS
        assert not missing, f"Missing from SATURDAY_OFF_ROTATIONS: {missing}"

    def test_all_in_intern_continuity_exempt(self):
        missing = self.ALL_COMBINED - INTERN_CONTINUITY_EXEMPT_ROTATIONS
        assert not missing, f"Missing from INTERN_CONTINUITY_EXEMPT: {missing}"


class TestNFCombinedPreloadCodes:
    """Verify get_rotation_preload_codes generates correct 28-day patterns."""

    # Use a Thursday block start (typical) — 2026-06-04 is a Thursday
    BLOCK_START = date(2026, 6, 4)
    BLOCK_END = date(2026, 7, 1)

    @pytest.mark.parametrize("code,specialty", list(NF_COMBINED_ACTIVITY_MAP.items()))
    def test_nf_first_day15_recovery(self, code: str, specialty: str):
        """Day 15 should be recovery for all NF-first combined rotations."""
        day15 = self.BLOCK_START + timedelta(days=14)
        am, pm = get_rotation_preload_codes(
            code,
            day15,
            self.BLOCK_START,
            self.BLOCK_END,
            pgy_level=2,
            is_outpatient=False,
        )
        assert am == "recovery", f"{code} day 15 AM should be recovery, got {am}"
        assert pm == "recovery", f"{code} day 15 PM should be recovery, got {pm}"

    @pytest.mark.parametrize("code,specialty", list(NF_COMBINED_ACTIVITY_MAP.items()))
    def test_nf_first_weekday_first_half(self, code: str, specialty: str):
        """Weekdays in first half (days 1-14) should be OFF/NF for NF-first codes."""
        # Find a Monday in the first half
        d = self.BLOCK_START
        while d.weekday() != 0:  # Monday
            d += timedelta(days=1)
        am, pm = get_rotation_preload_codes(
            code, d, self.BLOCK_START, self.BLOCK_END, pgy_level=2, is_outpatient=False
        )
        assert am == "OFF", f"{code} first-half Monday AM should be OFF, got {am}"
        assert pm == "NF", f"{code} first-half Monday PM should be NF, got {pm}"

    @pytest.mark.parametrize("code,specialty", list(NF_COMBINED_ACTIVITY_MAP.items()))
    def test_nf_first_weekday_second_half(self, code: str, specialty: str):
        """Weekdays in second half (days 16-28) should be specialty for NF-first codes."""
        # Find a Monday in the second half (after day 15)
        d = self.BLOCK_START + timedelta(days=15)
        while d.weekday() != 0:  # Monday
            d += timedelta(days=1)
        am, pm = get_rotation_preload_codes(
            code, d, self.BLOCK_START, self.BLOCK_END, pgy_level=2, is_outpatient=False
        )
        assert am == specialty, (
            f"{code} second-half Monday AM should be {specialty}, got {am}"
        )
        assert pm == specialty, (
            f"{code} second-half Monday PM should be {specialty}, got {pm}"
        )

    def test_sunday_off_for_combined(self):
        """Sundays should be W/W for all combined codes."""
        d = self.BLOCK_START
        while d.weekday() != 6:  # Sunday
            d += timedelta(days=1)
        for code in NF_COMBINED_ACTIVITY_MAP:
            am, pm = get_rotation_preload_codes(
                code,
                d,
                self.BLOCK_START,
                self.BLOCK_END,
                pgy_level=2,
                is_outpatient=False,
            )
            assert (am, pm) == ("W", "W"), f"{code} Sunday should be W/W, got {am}/{pm}"
