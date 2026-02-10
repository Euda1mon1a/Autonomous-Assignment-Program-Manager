"""Tests for alertness prediction engine (no DB)."""

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.resilience.frms.alertness_engine import (
    SHIFT_CHARACTERISTICS,
    AlertnessPrediction,
    AlertnessPredictor,
    ShiftPattern,
    ShiftType,
)
from app.resilience.frms.sleep_debt import (
    CircadianPhase,
    SleepDebtModel,
    SleepOpportunity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESIDENT_ID = UUID("00000000-0000-0000-0000-000000000001")
BASE_DATE = datetime(2024, 1, 15, 7, 0)  # Monday 7 AM


def _shift(
    shift_type: ShiftType = ShiftType.DAY,
    start: datetime | None = None,
    hours: float | None = None,
    prior_sleep: float = 7.0,
    prior_quality: float = 0.9,
) -> ShiftPattern:
    """Create a ShiftPattern with convenient defaults."""
    if start is None:
        start = BASE_DATE
    if hours is None:
        hours = SHIFT_CHARACTERISTICS[shift_type]["duration_hours"]
    end = start + timedelta(hours=hours)
    return ShiftPattern(
        shift_type=shift_type,
        start_time=start,
        end_time=end,
        prior_sleep_hours=prior_sleep,
        prior_sleep_quality=prior_quality,
    )


def _sleep_opp(
    end_hour: int = 7,
    duration: float = 7.5,
    quality: float = 1.0,
) -> SleepOpportunity:
    """Create a SleepOpportunity ending at the given hour."""
    end = datetime(2024, 1, 15, end_hour, 0)
    start = end - timedelta(hours=duration)
    return SleepOpportunity(start_time=start, end_time=end, quality_factor=quality)


# ---------------------------------------------------------------------------
# ShiftType enum
# ---------------------------------------------------------------------------


class TestShiftType:
    def test_day(self):
        assert ShiftType.DAY.value == "day"

    def test_night(self):
        assert ShiftType.NIGHT.value == "night"

    def test_call_24(self):
        assert ShiftType.CALL_24.value == "call_24"

    def test_off(self):
        assert ShiftType.OFF.value == "off"

    def test_member_count(self):
        assert len(ShiftType) == 8


# ---------------------------------------------------------------------------
# SHIFT_CHARACTERISTICS
# ---------------------------------------------------------------------------


class TestShiftCharacteristics:
    def test_all_shift_types_covered(self):
        for st in ShiftType:
            assert st in SHIFT_CHARACTERISTICS

    def test_day_characteristics(self):
        c = SHIFT_CHARACTERISTICS[ShiftType.DAY]
        assert c["typical_start_hour"] == 7
        assert c["typical_end_hour"] == 17
        assert c["duration_hours"] == 10
        assert c["circadian_aligned"] is True
        assert c["fatigue_factor"] == 1.0

    def test_night_high_fatigue(self):
        assert SHIFT_CHARACTERISTICS[ShiftType.NIGHT]["fatigue_factor"] == 1.8

    def test_call_24_highest_fatigue(self):
        assert SHIFT_CHARACTERISTICS[ShiftType.CALL_24]["fatigue_factor"] == 2.5

    def test_off_zero_fatigue(self):
        assert SHIFT_CHARACTERISTICS[ShiftType.OFF]["fatigue_factor"] == 0.0


# ---------------------------------------------------------------------------
# ShiftPattern dataclass
# ---------------------------------------------------------------------------


class TestShiftPattern:
    def test_duration_computed(self):
        sp = _shift(ShiftType.DAY, hours=10)
        assert abs(sp.duration_hours - 10.0) < 1e-10

    def test_overnight_detection(self):
        start = datetime(2024, 1, 15, 19, 0)
        end = datetime(2024, 1, 16, 7, 0)
        sp = ShiftPattern(shift_type=ShiftType.NIGHT, start_time=start, end_time=end)
        assert sp.is_overnight is True

    def test_same_day_not_overnight(self):
        sp = _shift(ShiftType.DAY, hours=10)
        assert sp.is_overnight is False

    def test_fatigue_factor_property(self):
        sp = _shift(ShiftType.NIGHT)
        assert sp.fatigue_factor == 1.8

    def test_circadian_aligned_property(self):
        assert _shift(ShiftType.DAY).is_circadian_aligned is True
        assert _shift(ShiftType.NIGHT).is_circadian_aligned is False

    def test_defaults(self):
        sp = _shift()
        assert sp.prior_sleep_hours == 7.0
        assert sp.prior_sleep_quality == 0.9


# ---------------------------------------------------------------------------
# AlertnessPrediction dataclass
# ---------------------------------------------------------------------------


class TestAlertnessPrediction:
    def _make_prediction(self, **kw) -> AlertnessPrediction:
        from app.resilience.frms.samn_perelli import SamnPerelliLevel

        defaults = {
            "resident_id": RESIDENT_ID,
            "prediction_time": BASE_DATE,
            "alertness_score": 0.8,
            "samn_perelli_estimate": SamnPerelliLevel.FULLY_ALERT,
            "circadian_phase": CircadianPhase.MORNING_PEAK,
            "hours_awake": 8.0,
            "sleep_debt": 2.0,
            "performance_capacity": 80.0,
            "risk_level": "low",
        }
        defaults.update(kw)
        return AlertnessPrediction(**defaults)

    def test_construction(self):
        pred = self._make_prediction()
        assert pred.alertness_score == 0.8
        assert pred.risk_level == "low"

    def test_default_lists(self):
        pred = self._make_prediction()
        assert pred.contributing_factors == []
        assert pred.recommendations == []

    def test_to_dict_keys(self):
        pred = self._make_prediction()
        d = pred.to_dict()
        assert "resident_id" in d
        assert "alertness_score" in d
        assert "alertness_percent" in d
        assert "samn_perelli" in d
        assert "circadian_phase" in d
        assert "hours_awake" in d
        assert "sleep_debt" in d
        assert "risk_level" in d

    def test_to_dict_rounds(self):
        pred = self._make_prediction(alertness_score=0.8567)
        d = pred.to_dict()
        assert d["alertness_score"] == 0.857
        assert d["alertness_percent"] == 85

    def test_to_dict_samn_perelli_nested(self):
        pred = self._make_prediction()
        d = pred.to_dict()
        assert "level" in d["samn_perelli"]
        assert "name" in d["samn_perelli"]


# ---------------------------------------------------------------------------
# AlertnessPredictor — init
# ---------------------------------------------------------------------------


class TestAlertnessPredictorInit:
    def test_default_sleep_model(self):
        ap = AlertnessPredictor()
        assert isinstance(ap.sleep_model, SleepDebtModel)

    def test_custom_sleep_model(self):
        model = SleepDebtModel(baseline_sleep_need=8.0)
        ap = AlertnessPredictor(sleep_model=model)
        assert ap.sleep_model.baseline_sleep_need == 8.0


# ---------------------------------------------------------------------------
# AlertnessPredictor — internal methods
# ---------------------------------------------------------------------------


class TestEstimateHoursAwake:
    def test_no_history_default(self):
        ap = AlertnessPredictor()
        result = ap._estimate_hours_awake(BASE_DATE, [])
        assert result == 8.0

    def test_recent_sleep(self):
        ap = AlertnessPredictor()
        # Woke up at 7 AM, target is 3 PM → 8 hours awake
        sleep = _sleep_opp(end_hour=7, duration=8.0)
        target = datetime(2024, 1, 15, 15, 0)
        result = ap._estimate_hours_awake(target, [sleep])
        assert abs(result - 8.0) < 1e-10

    def test_future_sleep_end(self):
        ap = AlertnessPredictor()
        # Sleep ends after target → just woke up
        sleep = _sleep_opp(end_hour=15, duration=8.0)
        target = datetime(2024, 1, 15, 10, 0)
        result = ap._estimate_hours_awake(target, [sleep])
        assert result == 0.0


class TestCalculateCircadianScore:
    def test_morning_peak(self):
        ap = AlertnessPredictor()
        result = ap._calculate_circadian_score(datetime(2024, 1, 15, 10, 0))
        assert result == 1.0

    def test_nadir(self):
        ap = AlertnessPredictor()
        result = ap._calculate_circadian_score(datetime(2024, 1, 15, 4, 0))
        assert result == 0.6


class TestCalculateSleepInertia:
    def test_no_history(self):
        ap = AlertnessPredictor()
        result = ap._calculate_sleep_inertia(BASE_DATE, [])
        assert result == 0.0

    def test_just_woke_up(self):
        ap = AlertnessPredictor()
        sleep = _sleep_opp(end_hour=7, duration=8.0)
        # 5 minutes after wake
        target = datetime(2024, 1, 15, 7, 5)
        result = ap._calculate_sleep_inertia(target, [sleep])
        assert result > 0.0

    def test_well_past_wake(self):
        ap = AlertnessPredictor()
        sleep = _sleep_opp(end_hour=7, duration=8.0)
        # 2 hours after wake → no inertia
        target = datetime(2024, 1, 15, 9, 0)
        result = ap._calculate_sleep_inertia(target, [sleep])
        assert result == 0.0


class TestCalculateWorkloadImpact:
    def test_no_shifts(self):
        ap = AlertnessPredictor()
        result = ap._calculate_workload_impact([], BASE_DATE)
        assert result == 0.0

    def test_single_day_shift(self):
        ap = AlertnessPredictor()
        shift = _shift(ShiftType.DAY)
        result = ap._calculate_workload_impact([shift], BASE_DATE + timedelta(hours=5))
        assert result >= 0.0

    def test_capped_at_04(self):
        ap = AlertnessPredictor()
        # Many high-fatigue shifts
        shifts = [
            _shift(ShiftType.CALL_24, start=BASE_DATE - timedelta(days=i))
            for i in range(7)
        ]
        result = ap._calculate_workload_impact(shifts, BASE_DATE)
        assert result <= 0.4

    def test_old_shifts_excluded(self):
        ap = AlertnessPredictor()
        old_shift = _shift(ShiftType.CALL_24, start=BASE_DATE - timedelta(days=10))
        result = ap._calculate_workload_impact([old_shift], BASE_DATE)
        assert result == 0.0


class TestEstimateSleepDebt:
    def test_no_history(self):
        ap = AlertnessPredictor()
        assert ap._estimate_sleep_debt([]) == 0.0

    def test_adequate_sleep_no_debt(self):
        ap = AlertnessPredictor()
        sleeps = [_sleep_opp(duration=8.0) for _ in range(3)]
        result = ap._estimate_sleep_debt(sleeps)
        assert result == 0.0

    def test_short_sleep_creates_debt(self):
        ap = AlertnessPredictor()
        sleeps = [_sleep_opp(duration=5.0) for _ in range(3)]
        result = ap._estimate_sleep_debt(sleeps)
        assert result > 0.0


class TestCalculateDebtImpact:
    def test_zero_debt(self):
        ap = AlertnessPredictor()
        assert ap._calculate_debt_impact(0.0) == 0.0

    def test_10h_debt(self):
        ap = AlertnessPredictor()
        # 10 * 0.02 = 0.2
        assert abs(ap._calculate_debt_impact(10.0) - 0.2) < 1e-10

    def test_capped_at_05(self):
        ap = AlertnessPredictor()
        assert ap._calculate_debt_impact(100.0) == 0.5


class TestHoursAwakePenalty:
    def test_under_12_no_penalty(self):
        ap = AlertnessPredictor()
        assert ap._hours_awake_penalty(10.0) == 0.0
        assert ap._hours_awake_penalty(12.0) == 0.0

    def test_14_hours(self):
        ap = AlertnessPredictor()
        # (14-12)*0.025 = 0.05
        assert abs(ap._hours_awake_penalty(14.0) - 0.05) < 1e-10

    def test_18_hours(self):
        ap = AlertnessPredictor()
        # 0.1 + (18-16)*0.05 = 0.2
        assert abs(ap._hours_awake_penalty(18.0) - 0.2) < 1e-10

    def test_22_hours(self):
        ap = AlertnessPredictor()
        # 0.3 + (22-20)*0.075 = 0.45
        assert abs(ap._hours_awake_penalty(22.0) - 0.45) < 1e-10

    def test_26_hours(self):
        ap = AlertnessPredictor()
        # 0.6 + (26-24)*0.05 = 0.7
        assert abs(ap._hours_awake_penalty(26.0) - 0.7) < 1e-10

    def test_capped_at_07(self):
        ap = AlertnessPredictor()
        assert ap._hours_awake_penalty(50.0) == 0.7


# ---------------------------------------------------------------------------
# AlertnessPredictor — risk and recommendations
# ---------------------------------------------------------------------------


class TestClassifyRisk:
    def test_high_low_alertness(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.3, 10, 0) == "high"

    def test_high_long_awake(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.8, 22, 0) == "high"

    def test_high_large_debt(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.8, 10, 20) == "high"

    def test_moderate_mid_alertness(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.5, 10, 0) == "moderate"

    def test_moderate_awake_17(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.8, 17, 0) == "moderate"

    def test_moderate_debt_10(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.8, 10, 10) == "moderate"

    def test_low(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.7, 10, 0) == "low"

    def test_minimal(self):
        ap = AlertnessPredictor()
        assert ap._classify_risk(0.9, 8, 0) == "minimal"


class TestIdentifyContributingFactors:
    def test_no_factors(self):
        ap = AlertnessPredictor()
        factors = ap._identify_contributing_factors(10, 1.0, 0, 0)
        assert factors == ["No significant fatigue factors"]

    def test_extended_wakefulness(self):
        ap = AlertnessPredictor()
        factors = ap._identify_contributing_factors(20, 1.0, 0, 0)
        assert any("wakefulness" in f.lower() for f in factors)

    def test_circadian_low(self):
        ap = AlertnessPredictor()
        factors = ap._identify_contributing_factors(10, 0.6, 0, 0)
        assert any("circadian" in f.lower() for f in factors)

    def test_sleep_debt(self):
        ap = AlertnessPredictor()
        factors = ap._identify_contributing_factors(10, 1.0, 10, 0)
        assert any("debt" in f.lower() for f in factors)

    def test_high_workload(self):
        ap = AlertnessPredictor()
        factors = ap._identify_contributing_factors(10, 1.0, 0, 0.3)
        assert any("workload" in f.lower() for f in factors)


class TestGenerateRecommendations:
    def test_high_risk_defers(self):
        ap = AlertnessPredictor()
        recs = ap._generate_recommendations("high", 22, 10, BASE_DATE)
        assert any("defer" in r.lower() for r in recs)

    def test_high_risk_extended_awake(self):
        ap = AlertnessPredictor()
        recs = ap._generate_recommendations("high", 22, 0, BASE_DATE)
        assert any("sleep" in r.lower() for r in recs)

    def test_moderate_caffeine(self):
        ap = AlertnessPredictor()
        recs = ap._generate_recommendations("moderate", 10, 0, BASE_DATE)
        assert any("caffeine" in r.lower() for r in recs)

    def test_nadir_warning(self):
        ap = AlertnessPredictor()
        nadir_time = datetime(2024, 1, 15, 4, 0)
        recs = ap._generate_recommendations("minimal", 8, 0, nadir_time)
        assert any("circadian" in r.lower() or "2-6" in r for r in recs)

    def test_minimal_ok(self):
        ap = AlertnessPredictor()
        noon = datetime(2024, 1, 15, 12, 0)
        recs = ap._generate_recommendations("minimal", 8, 0, noon)
        assert any("adequate" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# AlertnessPredictor — predict_alertness (integration)
# ---------------------------------------------------------------------------


class TestPredictAlertness:
    def test_returns_prediction(self):
        ap = AlertnessPredictor()
        shift = _shift(ShiftType.DAY)
        target = BASE_DATE + timedelta(hours=5)
        pred = ap.predict_alertness(RESIDENT_ID, target, [shift], [])
        assert isinstance(pred, AlertnessPrediction)
        assert 0.0 < pred.alertness_score <= 1.0

    def test_alertness_bounded(self):
        ap = AlertnessPredictor()
        pred = ap.predict_alertness(RESIDENT_ID, BASE_DATE, [], [])
        assert 0.1 <= pred.alertness_score <= 1.0

    def test_high_debt_reduces_alertness(self):
        ap = AlertnessPredictor()
        target = datetime(2024, 1, 15, 10, 0)  # Morning peak
        low_debt = ap.predict_alertness(
            RESIDENT_ID, target, [], [], current_sleep_debt=0.0
        )
        high_debt = ap.predict_alertness(
            RESIDENT_ID, target, [], [], current_sleep_debt=20.0
        )
        assert high_debt.alertness_score < low_debt.alertness_score

    def test_prediction_has_risk(self):
        ap = AlertnessPredictor()
        pred = ap.predict_alertness(RESIDENT_ID, BASE_DATE, [], [])
        assert pred.risk_level in ["minimal", "low", "moderate", "high"]


# ---------------------------------------------------------------------------
# AlertnessPredictor — identify_high_risk_windows
# ---------------------------------------------------------------------------


class TestIdentifyHighRiskWindows:
    def test_empty_trajectory(self):
        ap = AlertnessPredictor()
        assert ap.identify_high_risk_windows([]) == []

    def test_all_above_threshold(self):
        ap = AlertnessPredictor()
        pred = ap.predict_alertness(
            RESIDENT_ID, datetime(2024, 1, 15, 10, 0), [], [], current_sleep_debt=0.0
        )
        # If alertness > threshold, no high risk
        if pred.alertness_score >= 0.5:
            windows = ap.identify_high_risk_windows([pred], threshold=0.5)
            assert len(windows) == 0

    def test_below_threshold_detected(self):
        ap = AlertnessPredictor()
        pred = ap.predict_alertness(
            RESIDENT_ID,
            datetime(2024, 1, 15, 4, 0),  # Nadir
            [],
            [],
            current_sleep_debt=20.0,
        )
        windows = ap.identify_high_risk_windows([pred], threshold=0.99)
        assert len(windows) >= 1
        assert "time" in windows[0]
        assert "alertness" in windows[0]
        assert "risk_level" in windows[0]


# ---------------------------------------------------------------------------
# AlertnessPredictor — predict_shift_trajectory
# ---------------------------------------------------------------------------


class TestPredictShiftTrajectory:
    def test_returns_predictions(self):
        ap = AlertnessPredictor()
        shifts = [
            _shift(ShiftType.DAY, start=BASE_DATE),
            _shift(ShiftType.DAY, start=BASE_DATE + timedelta(days=1)),
        ]
        traj = ap.predict_shift_trajectory(RESIDENT_ID, shifts)
        assert len(traj) == 2

    def test_off_day_excluded(self):
        ap = AlertnessPredictor()
        shifts = [
            _shift(ShiftType.DAY, start=BASE_DATE),
            _shift(ShiftType.OFF, start=BASE_DATE + timedelta(days=1), hours=0),
        ]
        traj = ap.predict_shift_trajectory(RESIDENT_ID, shifts)
        # OFF shift shouldn't produce a prediction
        assert len(traj) == 1

    def test_off_day_reduces_debt(self):
        ap = AlertnessPredictor()
        shifts = [
            _shift(ShiftType.DAY, start=BASE_DATE, prior_sleep=7.5),
            _shift(ShiftType.OFF, start=BASE_DATE + timedelta(days=1), hours=0),
            _shift(ShiftType.DAY, start=BASE_DATE + timedelta(days=2), prior_sleep=7.5),
        ]
        traj = ap.predict_shift_trajectory(RESIDENT_ID, shifts, current_sleep_debt=10.0)
        # OFF day recovers (8.5-7.5)/1.5 = 0.667h, and DAY shift with
        # prior_sleep=7.5 adds 0 debt. So second shift debt < first.
        assert traj[1].sleep_debt < traj[0].sleep_debt
