"""Tests for FRMS performance predictor (no DB)."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.frms.performance_predictor import (
    ClinicalRiskLevel,
    PerformanceDegradation,
    PerformancePredictor,
    ScheduleFeatures,
)


# ---------------------------------------------------------------------------
# ClinicalRiskLevel enum
# ---------------------------------------------------------------------------


class TestClinicalRiskLevel:
    def test_values(self):
        assert ClinicalRiskLevel.MINIMAL == "minimal"
        assert ClinicalRiskLevel.LOW == "low"
        assert ClinicalRiskLevel.MODERATE == "moderate"
        assert ClinicalRiskLevel.HIGH == "high"
        assert ClinicalRiskLevel.SEVERE == "severe"

    def test_count(self):
        assert len(ClinicalRiskLevel) == 5

    def test_is_string_enum(self):
        assert isinstance(ClinicalRiskLevel.MINIMAL, str)


# ---------------------------------------------------------------------------
# PerformanceDegradation dataclass
# ---------------------------------------------------------------------------


class TestPerformanceDegradation:
    def _make(self, **overrides):
        defaults = {
            "person_id": uuid4(),
            "prediction_time": datetime(2026, 1, 15, 8, 0),
            "degradation_probability": 0.35,
            "error_multiplier": 1.5,
            "clinical_risk": ClinicalRiskLevel.MODERATE,
        }
        defaults.update(overrides)
        return PerformanceDegradation(**defaults)

    def test_defaults(self):
        pd = self._make()
        assert pd.contributing_factors == {}
        assert pd.confidence_interval == (0.0, 1.0)
        assert pd.recommended_actions == []
        assert pd.optimal_break_time is None
        assert pd.hours_to_recovery == 0.0

    def test_to_dict_keys(self):
        pd = self._make()
        d = pd.to_dict()
        expected_keys = {
            "person_id",
            "prediction_time",
            "degradation_probability",
            "error_multiplier",
            "clinical_risk",
            "contributing_factors",
            "confidence_interval",
            "recommended_actions",
            "optimal_break_time",
            "hours_to_recovery",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_person_id_string(self):
        pid = uuid4()
        d = self._make(person_id=pid).to_dict()
        assert d["person_id"] == str(pid)

    def test_to_dict_prediction_time_iso(self):
        t = datetime(2026, 1, 15, 8, 30)
        d = self._make(prediction_time=t).to_dict()
        assert d["prediction_time"] == t.isoformat()

    def test_to_dict_rounds_probability(self):
        d = self._make(degradation_probability=0.123456789).to_dict()
        assert d["degradation_probability"] == 0.1235

    def test_to_dict_rounds_error_multiplier(self):
        d = self._make(error_multiplier=1.5678).to_dict()
        assert d["error_multiplier"] == 1.57

    def test_to_dict_clinical_risk_value(self):
        d = self._make(clinical_risk=ClinicalRiskLevel.HIGH).to_dict()
        assert d["clinical_risk"] == "high"

    def test_to_dict_confidence_interval_structure(self):
        d = self._make(confidence_interval=(0.2, 0.5)).to_dict()
        assert d["confidence_interval"]["lower"] == 0.2
        assert d["confidence_interval"]["upper"] == 0.5

    def test_to_dict_optimal_break_none(self):
        d = self._make(optimal_break_time=None).to_dict()
        assert d["optimal_break_time"] is None

    def test_to_dict_optimal_break_iso(self):
        t = datetime(2026, 1, 15, 15, 0)
        d = self._make(optimal_break_time=t).to_dict()
        assert d["optimal_break_time"] == t.isoformat()

    def test_to_dict_rounds_recovery(self):
        d = self._make(hours_to_recovery=12.3456).to_dict()
        assert d["hours_to_recovery"] == 12.3

    def test_to_dict_rounds_contributing_factors(self):
        d = self._make(contributing_factors={"sleep": 0.123456}).to_dict()
        assert d["contributing_factors"]["sleep"] == 0.1235


# ---------------------------------------------------------------------------
# ScheduleFeatures dataclass
# ---------------------------------------------------------------------------


class TestScheduleFeatures:
    def test_defaults(self):
        sf = ScheduleFeatures()
        assert sf.consecutive_duty_days == 0
        assert sf.hours_since_rest == 0.0
        assert sf.average_sleep_hours == 7.0
        assert sf.recovery_quality_score == 1.0
        assert sf.shift_start_hour == 7.0
        assert sf.circadian_alignment_score == 1.0

    def test_to_vector_length(self):
        sf = ScheduleFeatures()
        vec = sf.to_vector()
        assert len(vec) == 20

    def test_to_vector_all_floats(self):
        sf = ScheduleFeatures()
        for v in sf.to_vector():
            assert isinstance(v, float)

    def test_to_vector_bool_converted(self):
        sf = ScheduleFeatures(is_currently_night_shift=True)
        vec = sf.to_vector()
        # is_currently_night_shift is index 7
        assert vec[7] == 1.0

    def test_to_vector_bool_false(self):
        sf = ScheduleFeatures(is_currently_night_shift=False)
        assert sf.to_vector()[7] == 0.0


# ---------------------------------------------------------------------------
# PerformancePredictor — init and class constants
# ---------------------------------------------------------------------------


class TestPredictorInit:
    def test_default_version(self):
        p = PerformancePredictor()
        assert p.model_version == "rule_based_v1"

    def test_custom_version(self):
        p = PerformancePredictor(model_version="v2")
        assert p.model_version == "v2"

    def test_feature_weights_sum_to_one(self):
        total = sum(PerformancePredictor.FEATURE_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_degradation_thresholds_ordered(self):
        t = PerformancePredictor.DEGRADATION_THRESHOLDS
        assert t["severe"] > t["high"] > t["moderate"] > t["low"] > t["minimal"]

    def test_error_multiplier_map_increasing(self):
        m = PerformancePredictor.ERROR_MULTIPLIER_MAP
        assert m[ClinicalRiskLevel.MINIMAL] < m[ClinicalRiskLevel.LOW]
        assert m[ClinicalRiskLevel.LOW] < m[ClinicalRiskLevel.MODERATE]
        assert m[ClinicalRiskLevel.MODERATE] < m[ClinicalRiskLevel.HIGH]
        assert m[ClinicalRiskLevel.HIGH] < m[ClinicalRiskLevel.SEVERE]


# ---------------------------------------------------------------------------
# PerformancePredictor._sigmoid
# ---------------------------------------------------------------------------


class TestSigmoid:
    def test_midpoint_is_half(self):
        p = PerformancePredictor()
        assert abs(p._sigmoid(0.5) - 0.5) < 0.01

    def test_low_input_near_zero(self):
        p = PerformancePredictor()
        assert p._sigmoid(-5.0) < 0.01

    def test_high_input_near_one(self):
        p = PerformancePredictor()
        assert p._sigmoid(5.0) > 0.99

    def test_monotonically_increasing(self):
        p = PerformancePredictor()
        prev = 0.0
        for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = p._sigmoid(x)
            assert val >= prev
            prev = val

    def test_always_between_0_and_1(self):
        p = PerformancePredictor()
        for x in [-10, -1, 0, 0.5, 1, 10]:
            val = p._sigmoid(x)
            assert 0.0 <= val <= 1.0


# ---------------------------------------------------------------------------
# PerformancePredictor._determine_risk_level
# ---------------------------------------------------------------------------


class TestDetermineRiskLevel:
    def test_minimal(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.1) == ClinicalRiskLevel.MINIMAL

    def test_low(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.25) == ClinicalRiskLevel.LOW

    def test_moderate(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.45) == ClinicalRiskLevel.MODERATE

    def test_high(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.65) == ClinicalRiskLevel.HIGH

    def test_severe(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.85) == ClinicalRiskLevel.SEVERE

    def test_boundary_low(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.20) == ClinicalRiskLevel.LOW

    def test_boundary_severe(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.80) == ClinicalRiskLevel.SEVERE

    def test_zero(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(0.0) == ClinicalRiskLevel.MINIMAL

    def test_one(self):
        p = PerformancePredictor()
        assert p._determine_risk_level(1.0) == ClinicalRiskLevel.SEVERE


# ---------------------------------------------------------------------------
# PerformancePredictor._calculate_risk_score
# ---------------------------------------------------------------------------


class TestCalculateRiskScore:
    def test_zero_features_low_score(self):
        p = PerformancePredictor()
        score = p._calculate_risk_score(ScheduleFeatures())
        assert score >= 0.0
        assert score < 0.3

    def test_exhausted_resident_high_score(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(
            consecutive_duty_days=10,
            hours_since_rest=24,
            night_shifts_7d=5,
            hours_in_wocl_7d=20,
            hours_worked_7d=80,
            days_since_full_day_off=10,
            average_sleep_hours=4,
            circadian_alignment_score=0.3,
            call_shifts_7d=3,
            rotation_transitions_14d=4,
            is_currently_night_shift=True,
            weekend_days_worked=4,
        )
        score = p._calculate_risk_score(features)
        assert score > 0.6

    def test_hours_since_rest_exponential_penalty(self):
        p = PerformancePredictor()
        normal = p._calculate_risk_score(ScheduleFeatures(hours_since_rest=12))
        extended = p._calculate_risk_score(ScheduleFeatures(hours_since_rest=24))
        assert extended > normal

    def test_consecutive_days_penalty_after_six(self):
        p = PerformancePredictor()
        six = p._calculate_risk_score(ScheduleFeatures(consecutive_duty_days=6))
        eight = p._calculate_risk_score(ScheduleFeatures(consecutive_duty_days=8))
        assert eight > six

    def test_night_shift_bonus(self):
        p = PerformancePredictor()
        day = p._calculate_risk_score(ScheduleFeatures(is_currently_night_shift=False))
        night = p._calculate_risk_score(ScheduleFeatures(is_currently_night_shift=True))
        assert night > day

    def test_sleep_deficit_increases_score(self):
        p = PerformancePredictor()
        well_rested = p._calculate_risk_score(ScheduleFeatures(average_sleep_hours=8))
        sleep_deprived = p._calculate_risk_score(
            ScheduleFeatures(average_sleep_hours=4)
        )
        assert sleep_deprived > well_rested


# ---------------------------------------------------------------------------
# PerformancePredictor._generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    def test_severe_risk_gets_urgent(self):
        p = PerformancePredictor()
        recs = p._generate_recommendations(
            ScheduleFeatures(), 0.9, ClinicalRiskLevel.SEVERE
        )
        assert any("URGENT" in r for r in recs)

    def test_high_risk_gets_urgent(self):
        p = PerformancePredictor()
        recs = p._generate_recommendations(
            ScheduleFeatures(), 0.7, ClinicalRiskLevel.HIGH
        )
        assert any("URGENT" in r for r in recs)

    def test_consecutive_days_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(consecutive_duty_days=7)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("day off" in r.lower() for r in recs)

    def test_night_shifts_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(night_shifts_7d=4)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("night shift" in r.lower() for r in recs)

    def test_wocl_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(hours_in_wocl_7d=15)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("WOCL" in r for r in recs)

    def test_sleep_deficit_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(average_sleep_hours=5)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("sleep" in r.lower() for r in recs)

    def test_acgme_1_in_7_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(days_since_full_day_off=8)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("ACGME" in r for r in recs)

    def test_circadian_misalignment_recommendation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(circadian_alignment_score=0.5)
        recs = p._generate_recommendations(features, 0.5, ClinicalRiskLevel.MODERATE)
        assert any("circadian" in r.lower() for r in recs)

    def test_no_issues_gets_acceptable_message(self):
        p = PerformancePredictor()
        recs = p._generate_recommendations(
            ScheduleFeatures(), 0.1, ClinicalRiskLevel.MINIMAL
        )
        assert any("acceptable" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# PerformancePredictor._estimate_recovery_time
# ---------------------------------------------------------------------------


class TestEstimateRecoveryTime:
    def test_base_recovery(self):
        p = PerformancePredictor()
        hours = p._estimate_recovery_time(ScheduleFeatures(), 0.0)
        assert hours >= 8.0

    def test_more_fatigue_more_recovery(self):
        p = PerformancePredictor()
        low = p._estimate_recovery_time(ScheduleFeatures(), 0.2)
        high = p._estimate_recovery_time(
            ScheduleFeatures(
                consecutive_duty_days=8,
                night_shifts_7d=4,
                average_sleep_hours=4,
            ),
            0.8,
        )
        assert high > low

    def test_capped_at_48(self):
        p = PerformancePredictor()
        hours = p._estimate_recovery_time(
            ScheduleFeatures(
                consecutive_duty_days=14,
                night_shifts_7d=7,
                average_sleep_hours=2,
            ),
            1.0,
        )
        assert hours <= 48.0


# ---------------------------------------------------------------------------
# PerformancePredictor._calculate_optimal_break
# ---------------------------------------------------------------------------


class TestCalculateOptimalBreak:
    def test_low_probability_returns_none(self):
        p = PerformancePredictor()
        result = p._calculate_optimal_break(
            datetime(2026, 1, 15, 8, 0), ScheduleFeatures(), 0.2
        )
        assert result is None

    def test_morning_suggests_9am(self):
        p = PerformancePredictor()
        result = p._calculate_optimal_break(
            datetime(2026, 1, 15, 7, 0), ScheduleFeatures(), 0.5
        )
        assert result is not None
        assert result.hour == 9

    def test_midday_suggests_3pm(self):
        p = PerformancePredictor()
        result = p._calculate_optimal_break(
            datetime(2026, 1, 15, 12, 0), ScheduleFeatures(), 0.5
        )
        assert result is not None
        assert result.hour == 15

    def test_evening_suggests_next_morning(self):
        p = PerformancePredictor()
        result = p._calculate_optimal_break(
            datetime(2026, 1, 15, 18, 0), ScheduleFeatures(), 0.5
        )
        assert result is not None
        assert result.hour == 9
        assert result.day == 16


# ---------------------------------------------------------------------------
# PerformancePredictor._calculate_factor_contributions
# ---------------------------------------------------------------------------


class TestCalculateFactorContributions:
    def test_returns_dict(self):
        p = PerformancePredictor()
        result = p._calculate_factor_contributions(ScheduleFeatures())
        assert isinstance(result, dict)

    def test_known_factors(self):
        p = PerformancePredictor()
        result = p._calculate_factor_contributions(ScheduleFeatures())
        expected = {
            "sleep_debt",
            "consecutive_days",
            "night_shifts",
            "wocl_exposure",
            "weekly_hours",
            "days_without_rest",
            "circadian_misalignment",
        }
        assert set(result.keys()) == expected

    def test_values_non_negative(self):
        p = PerformancePredictor()
        features = ScheduleFeatures(
            consecutive_duty_days=5,
            night_shifts_7d=2,
            hours_worked_7d=60,
        )
        for v in p._calculate_factor_contributions(features).values():
            assert v >= 0.0


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------


class TestCountConsecutiveDays:
    def test_no_assignments(self):
        p = PerformancePredictor()
        assert p._count_consecutive_days([], date(2026, 1, 15)) == 0

    def test_consecutive(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today},
            {"date": today - timedelta(days=1)},
            {"date": today - timedelta(days=2)},
        ]
        assert p._count_consecutive_days(assignments, today) == 3

    def test_gap_breaks_streak(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today},
            {"date": today - timedelta(days=2)},
        ]
        assert p._count_consecutive_days(assignments, today) == 1

    def test_string_dates(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": "2026-01-15"},
            {"date": "2026-01-14"},
        ]
        assert p._count_consecutive_days(assignments, today) == 2


class TestCountHoursInWindow:
    def test_no_assignments(self):
        p = PerformancePredictor()
        assert p._count_hours_in_window([], date(2026, 1, 15), 7) == 0.0

    def test_within_window(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "hours": 10},
            {"date": today - timedelta(days=3), "hours": 8},
        ]
        assert p._count_hours_in_window(assignments, today, 7) == 18.0

    def test_outside_window_excluded(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today - timedelta(days=10), "hours": 12},
        ]
        assert p._count_hours_in_window(assignments, today, 7) == 0.0

    def test_default_6_hours(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [{"date": today}]
        assert p._count_hours_in_window(assignments, today, 7) == 6.0


class TestCountNightShifts:
    def test_no_assignments(self):
        p = PerformancePredictor()
        assert p._count_night_shifts([], date(2026, 1, 15), 7) == 0

    def test_pm_shifts_counted(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "time_of_day": "PM"},
            {"date": today - timedelta(days=1), "time_of_day": "AM"},
        ]
        assert p._count_night_shifts(assignments, today, 7) == 1

    def test_is_night_shift_flag(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "is_night_shift": True},
        ]
        assert p._count_night_shifts(assignments, today, 7) == 1


class TestEstimateWoclHours:
    def test_proportional_to_night_shifts(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "time_of_day": "PM"},
            {"date": today - timedelta(days=1), "time_of_day": "PM"},
        ]
        assert p._estimate_wocl_hours(assignments, today, 7) == 8.0


class TestCountCallShifts:
    def test_is_call_flag(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "is_call": True},
            {"date": today - timedelta(days=1), "is_call": False},
        ]
        assert p._count_call_shifts(assignments, today, 7) == 1

    def test_call_in_rotation_type(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "rotation_type": "Night Call"},
        ]
        assert p._count_call_shifts(assignments, today, 7) == 1


class TestCountWeekendDays:
    def test_no_weekends(self):
        p = PerformancePredictor()
        # 2026-01-15 is a Thursday
        today = date(2026, 1, 15)
        assignments = [{"date": today}]
        assert p._count_weekend_days(assignments, today, 7) == 0

    def test_saturday_counted(self):
        p = PerformancePredictor()
        today = date(2026, 1, 17)  # Saturday
        assignments = [{"date": today}]
        assert p._count_weekend_days(assignments, today, 7) == 1

    def test_duplicates_not_double_counted(self):
        p = PerformancePredictor()
        today = date(2026, 1, 17)  # Saturday
        assignments = [
            {"date": today},
            {"date": today},
        ]
        assert p._count_weekend_days(assignments, today, 7) == 1


class TestDaysSinceOff:
    def test_today_is_off(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        # No work today
        assert p._days_since_off([], today) == 0

    def test_continuous_work(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today},
            {"date": today - timedelta(days=1)},
            {"date": today - timedelta(days=2)},
        ]
        assert p._days_since_off(assignments, today) == 3

    def test_capped_at_14(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [{"date": today - timedelta(days=i)} for i in range(20)]
        assert p._days_since_off(assignments, today) == 14


class TestCountTransitions:
    def test_no_assignments(self):
        p = PerformancePredictor()
        assert p._count_transitions([], date(2026, 1, 15), 14) == 0

    def test_same_rotation_no_transitions(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "rotation_type": "Wards"},
            {"date": today - timedelta(days=1), "rotation_type": "Wards"},
        ]
        assert p._count_transitions(assignments, today, 14) == 0

    def test_one_transition(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "rotation_type": "ICU"},
            {"date": today - timedelta(days=1), "rotation_type": "Wards"},
        ]
        assert p._count_transitions(assignments, today, 14) == 1

    def test_multiple_transitions(self):
        p = PerformancePredictor()
        today = date(2026, 1, 15)
        assignments = [
            {"date": today, "rotation_type": "ICU"},
            {"date": today - timedelta(days=1), "rotation_type": "Wards"},
            {"date": today - timedelta(days=2), "rotation_type": "Clinic"},
        ]
        assert p._count_transitions(assignments, today, 14) == 2


# ---------------------------------------------------------------------------
# PerformancePredictor.extract_features (integration)
# ---------------------------------------------------------------------------


class TestExtractFeatures:
    def test_empty_assignments(self):
        p = PerformancePredictor()
        features = p.extract_features([], datetime(2026, 1, 15, 8, 0))
        assert features.consecutive_duty_days == 0

    def test_night_shift_detection(self):
        p = PerformancePredictor()
        features = p.extract_features(
            [{"date": date(2026, 1, 15)}],
            datetime(2026, 1, 15, 22, 0),
        )
        assert features.is_currently_night_shift is True

    def test_day_shift_detection(self):
        p = PerformancePredictor()
        features = p.extract_features(
            [{"date": date(2026, 1, 15)}],
            datetime(2026, 1, 15, 10, 0),
        )
        assert features.is_currently_night_shift is False

    def test_fatigue_effectiveness_mapped(self):
        p = PerformancePredictor()
        features = p.extract_features(
            [{"date": date(2026, 1, 15)}],
            datetime(2026, 1, 15, 8, 0),
            fatigue_effectiveness=80.0,
        )
        assert abs(features.circadian_alignment_score - 0.8) < 0.01

    def test_sleep_data_used(self):
        p = PerformancePredictor()
        features = p.extract_features(
            [{"date": date(2026, 1, 15)}],
            datetime(2026, 1, 15, 8, 0),
            sleep_data={"average_hours": 5.5, "quality_score": 0.7},
        )
        assert features.average_sleep_hours == 5.5
        assert features.recovery_quality_score == 0.7


# ---------------------------------------------------------------------------
# PerformancePredictor.predict (integration)
# ---------------------------------------------------------------------------


class TestPredict:
    def test_returns_degradation(self):
        p = PerformancePredictor()
        features = ScheduleFeatures()
        result = p.predict(features, uuid4())
        assert isinstance(result, PerformanceDegradation)

    def test_probability_in_range(self):
        p = PerformancePredictor()
        result = p.predict(ScheduleFeatures(), uuid4())
        assert 0.0 <= result.degradation_probability <= 1.0

    def test_high_fatigue_higher_risk(self):
        p = PerformancePredictor()
        pid = uuid4()
        low = p.predict(ScheduleFeatures(), pid)
        high = p.predict(
            ScheduleFeatures(
                consecutive_duty_days=10,
                hours_since_rest=24,
                night_shifts_7d=5,
                average_sleep_hours=4,
            ),
            pid,
        )
        assert high.degradation_probability > low.degradation_probability

    def test_error_multiplier_matches_risk(self):
        p = PerformancePredictor()
        result = p.predict(ScheduleFeatures(), uuid4())
        expected = PerformancePredictor.ERROR_MULTIPLIER_MAP[result.clinical_risk]
        assert result.error_multiplier == expected

    def test_confidence_interval_contains_probability(self):
        p = PerformancePredictor()
        result = p.predict(ScheduleFeatures(), uuid4())
        lo, hi = result.confidence_interval
        assert lo <= result.degradation_probability <= hi

    def test_recommendations_not_empty(self):
        p = PerformancePredictor()
        result = p.predict(ScheduleFeatures(), uuid4())
        assert len(result.recommended_actions) > 0

    def test_custom_prediction_time(self):
        p = PerformancePredictor()
        t = datetime(2026, 6, 1, 12, 0)
        result = p.predict(ScheduleFeatures(), uuid4(), prediction_time=t)
        assert result.prediction_time == t
