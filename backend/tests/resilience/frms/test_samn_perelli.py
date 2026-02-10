"""Tests for Samn-Perelli fatigue scale pure logic (no DB, no Redis).

Covers: SamnPerelliLevel, LEVEL_DESCRIPTIONS, DUTY_THRESHOLDS,
SamnPerelliAssessment, assess_fatigue_level, is_safe_for_duty,
estimate_level_from_factors, get_all_levels.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.resilience.frms.samn_perelli import (
    DUTY_THRESHOLDS,
    LEVEL_DESCRIPTIONS,
    SamnPerelliAssessment,
    SamnPerelliLevel,
    assess_fatigue_level,
    estimate_level_from_factors,
    get_all_levels,
    is_safe_for_duty,
)


# ---------------------------------------------------------------------------
# SamnPerelliLevel enum
# ---------------------------------------------------------------------------


class TestSamnPerelliLevel:
    def test_values(self):
        assert SamnPerelliLevel.FULLY_ALERT == 1
        assert SamnPerelliLevel.VERY_LIVELY == 2
        assert SamnPerelliLevel.OKAY == 3
        assert SamnPerelliLevel.A_LITTLE_TIRED == 4
        assert SamnPerelliLevel.MODERATELY_TIRED == 5
        assert SamnPerelliLevel.EXTREMELY_TIRED == 6
        assert SamnPerelliLevel.EXHAUSTED == 7

    def test_count(self):
        assert len(SamnPerelliLevel) == 7

    def test_ordering(self):
        assert SamnPerelliLevel.FULLY_ALERT < SamnPerelliLevel.EXHAUSTED
        assert SamnPerelliLevel.MODERATELY_TIRED > SamnPerelliLevel.OKAY


class TestConstants:
    def test_level_descriptions_complete(self):
        for level in SamnPerelliLevel:
            assert level in LEVEL_DESCRIPTIONS
            assert isinstance(LEVEL_DESCRIPTIONS[level], str)

    def test_duty_thresholds_keys(self):
        expected = {
            "critical_care",
            "procedures",
            "inpatient",
            "outpatient",
            "education",
            "administrative",
        }
        assert set(DUTY_THRESHOLDS.keys()) == expected

    def test_procedures_strictest(self):
        # Procedures should have the strictest threshold
        assert DUTY_THRESHOLDS["procedures"] <= DUTY_THRESHOLDS["inpatient"]
        assert DUTY_THRESHOLDS["procedures"] <= DUTY_THRESHOLDS["education"]


# ---------------------------------------------------------------------------
# SamnPerelliAssessment
# ---------------------------------------------------------------------------


class TestSamnPerelliAssessmentToDict:
    def test_to_dict_keys(self):
        rid = uuid4()
        a = assess_fatigue_level(1, rid)
        d = a.to_dict()
        assert d["resident_id"] == str(rid)
        assert d["level"] == 1
        assert d["level_name"] == "FULLY_ALERT"
        assert "assessed_at" in d
        assert d["safe_for_duty"] is True

    def test_to_dict_with_restrictions(self):
        a = assess_fatigue_level(6, uuid4())
        d = a.to_dict()
        assert d["duty_restrictions"] is not None
        assert len(d["duty_restrictions"]) > 0


# ---------------------------------------------------------------------------
# assess_fatigue_level
# ---------------------------------------------------------------------------


class TestAssessFatigueLevel:
    def test_valid_level_1(self):
        a = assess_fatigue_level(1, uuid4())
        assert a.level == SamnPerelliLevel.FULLY_ALERT
        assert a.safe_for_duty is True
        assert a.duty_restrictions is None

    def test_valid_level_4_partial_restrictions(self):
        a = assess_fatigue_level(4, uuid4())
        assert a.level == SamnPerelliLevel.A_LITTLE_TIRED
        assert a.safe_for_duty is True
        # Level 4 exceeds procedures threshold (3)
        assert a.duty_restrictions is not None
        assert "procedures" in a.duty_restrictions

    def test_valid_level_5_more_restrictions(self):
        a = assess_fatigue_level(5, uuid4())
        assert a.safe_for_duty is True
        assert "procedures" in a.duty_restrictions
        assert "critical_care" in a.duty_restrictions

    def test_valid_level_6_extensive_restrictions(self):
        a = assess_fatigue_level(6, uuid4())
        assert a.safe_for_duty is True  # <=6 still technically safe
        assert len(a.duty_restrictions) >= 4

    def test_level_7_not_safe(self):
        a = assess_fatigue_level(7, uuid4())
        assert a.level == SamnPerelliLevel.EXHAUSTED
        assert a.safe_for_duty is False
        # All duties restricted
        assert len(a.duty_restrictions) == len(DUTY_THRESHOLDS)

    def test_invalid_level_0(self):
        with pytest.raises(ValueError, match="must be 1-7"):
            assess_fatigue_level(0, uuid4())

    def test_invalid_level_8(self):
        with pytest.raises(ValueError, match="must be 1-7"):
            assess_fatigue_level(8, uuid4())

    def test_self_reported(self):
        a = assess_fatigue_level(3, uuid4(), is_self_reported=True)
        assert a.is_self_reported is True

    def test_context_passed(self):
        ctx = {"shift_type": "night", "hours_worked": 12}
        a = assess_fatigue_level(3, uuid4(), context=ctx)
        assert a.context == ctx

    def test_notes_passed(self):
        a = assess_fatigue_level(3, uuid4(), notes="Feeling okay")
        assert a.notes == "Feeling okay"

    def test_recommended_rest_increases_with_level(self):
        rest_1 = assess_fatigue_level(1, uuid4()).recommended_rest_hours
        rest_5 = assess_fatigue_level(5, uuid4()).recommended_rest_hours
        rest_7 = assess_fatigue_level(7, uuid4()).recommended_rest_hours
        assert rest_1 <= rest_5 <= rest_7

    def test_description_matches_level(self):
        a = assess_fatigue_level(3, uuid4())
        assert a.description == LEVEL_DESCRIPTIONS[SamnPerelliLevel.OKAY]


# ---------------------------------------------------------------------------
# is_safe_for_duty
# ---------------------------------------------------------------------------


class TestIsSafeForDuty:
    def test_level_1_safe_for_all(self):
        for duty in DUTY_THRESHOLDS:
            safe, reason = is_safe_for_duty(SamnPerelliLevel.FULLY_ALERT, duty)
            assert safe is True

    def test_level_5_not_safe_for_procedures(self):
        safe, reason = is_safe_for_duty(SamnPerelliLevel.MODERATELY_TIRED, "procedures")
        assert safe is False
        assert "exceeds" in reason

    def test_level_5_safe_for_inpatient(self):
        safe, reason = is_safe_for_duty(SamnPerelliLevel.MODERATELY_TIRED, "inpatient")
        assert safe is True

    def test_level_7_not_safe_for_education(self):
        safe, reason = is_safe_for_duty(SamnPerelliLevel.EXHAUSTED, "education")
        assert safe is False

    def test_unknown_duty_uses_default(self):
        safe, reason = is_safe_for_duty(
            SamnPerelliLevel.MODERATELY_TIRED, "unknown_duty"
        )
        # Default threshold is MODERATELY_TIRED (5), so level 5 is safe
        assert safe is True

    def test_reason_includes_levels(self):
        _, reason = is_safe_for_duty(SamnPerelliLevel.OKAY, "procedures")
        assert "3" in reason  # Level 3 and threshold 3


# ---------------------------------------------------------------------------
# estimate_level_from_factors
# ---------------------------------------------------------------------------


class TestEstimateLevelFromFactors:
    def test_fresh_person_level_1(self):
        level = estimate_level_from_factors(
            hours_awake=8,
            hours_worked_24h=4,
            consecutive_night_shifts=0,
            time_of_day_hour=10,
            prior_sleep_hours=8.0,
        )
        assert level == SamnPerelliLevel.FULLY_ALERT

    def test_long_awake_increases_level(self):
        level = estimate_level_from_factors(
            hours_awake=25,
            hours_worked_24h=0,
            consecutive_night_shifts=0,
            time_of_day_hour=12,
            prior_sleep_hours=7.0,
        )
        assert level >= SamnPerelliLevel.A_LITTLE_TIRED

    def test_heavy_work_increases_level(self):
        level = estimate_level_from_factors(
            hours_awake=8,
            hours_worked_24h=18,
            consecutive_night_shifts=0,
            time_of_day_hour=12,
            prior_sleep_hours=7.0,
        )
        assert level >= SamnPerelliLevel.OKAY

    def test_night_shifts_increase_level(self):
        level_0 = estimate_level_from_factors(
            hours_awake=10,
            hours_worked_24h=8,
            consecutive_night_shifts=0,
            time_of_day_hour=12,
            prior_sleep_hours=7.0,
        )
        level_3 = estimate_level_from_factors(
            hours_awake=10,
            hours_worked_24h=8,
            consecutive_night_shifts=3,
            time_of_day_hour=12,
            prior_sleep_hours=7.0,
        )
        assert level_3 >= level_0

    def test_circadian_nadir_impact(self):
        level_noon = estimate_level_from_factors(
            hours_awake=12,
            hours_worked_24h=8,
            time_of_day_hour=12,
            prior_sleep_hours=7.0,
        )
        level_4am = estimate_level_from_factors(
            hours_awake=12,
            hours_worked_24h=8,
            time_of_day_hour=4,
            prior_sleep_hours=7.0,
        )
        assert level_4am >= level_noon

    def test_sleep_deficit_increases_level(self):
        level_rested = estimate_level_from_factors(
            hours_awake=8,
            hours_worked_24h=6,
            time_of_day_hour=12,
            prior_sleep_hours=8.0,
        )
        level_deprived = estimate_level_from_factors(
            hours_awake=8,
            hours_worked_24h=6,
            time_of_day_hour=12,
            prior_sleep_hours=3.0,
        )
        assert level_deprived >= level_rested

    def test_extreme_factors_max_at_7(self):
        level = estimate_level_from_factors(
            hours_awake=30,
            hours_worked_24h=20,
            consecutive_night_shifts=5,
            time_of_day_hour=4,
            prior_sleep_hours=2.0,
        )
        assert level == SamnPerelliLevel.EXHAUSTED

    def test_returns_samn_perelli_level(self):
        level = estimate_level_from_factors(
            hours_awake=10,
            hours_worked_24h=8,
        )
        assert isinstance(level, SamnPerelliLevel)


# ---------------------------------------------------------------------------
# get_all_levels
# ---------------------------------------------------------------------------


class TestGetAllLevels:
    def test_returns_7_levels(self):
        levels = get_all_levels()
        assert len(levels) == 7

    def test_level_dict_keys(self):
        levels = get_all_levels()
        for item in levels:
            assert "level" in item
            assert "name" in item
            assert "description" in item

    def test_levels_ordered(self):
        levels = get_all_levels()
        values = [item["level"] for item in levels]
        assert values == list(range(1, 8))
