"""Tests for Sleep Debt Accumulation Model pure logic (no DB, no Redis).

Covers: CircadianPhase, CIRCADIAN_MULTIPLIERS, SleepOpportunity,
SleepDebtState, SleepDebtModel, get_circadian_phases_info.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.frms.sleep_debt import (
    CIRCADIAN_MULTIPLIERS,
    CircadianPhase,
    SleepDebtModel,
    SleepDebtState,
    SleepOpportunity,
    get_circadian_phases_info,
)


# ---------------------------------------------------------------------------
# CircadianPhase enum
# ---------------------------------------------------------------------------


class TestCircadianPhase:
    def test_values(self):
        assert CircadianPhase.NADIR == "nadir"
        assert CircadianPhase.EARLY_MORNING == "early_morning"
        assert CircadianPhase.MORNING_PEAK == "morning_peak"
        assert CircadianPhase.POST_LUNCH == "post_lunch"
        assert CircadianPhase.AFTERNOON == "afternoon"
        assert CircadianPhase.EVENING == "evening"
        assert CircadianPhase.NIGHT == "night"

    def test_count(self):
        assert len(CircadianPhase) == 7

    def test_is_string_enum(self):
        assert isinstance(CircadianPhase.NADIR, str)
        assert CircadianPhase.NADIR == "nadir"


class TestCircadianMultipliers:
    def test_all_phases_have_multiplier(self):
        for phase in CircadianPhase:
            assert phase in CIRCADIAN_MULTIPLIERS
            assert isinstance(CIRCADIAN_MULTIPLIERS[phase], float)

    def test_multiplier_range(self):
        for phase, mult in CIRCADIAN_MULTIPLIERS.items():
            assert 0.0 < mult <= 1.0, f"{phase}: {mult} out of range"

    def test_morning_peak_is_highest(self):
        assert CIRCADIAN_MULTIPLIERS[CircadianPhase.MORNING_PEAK] == 1.0

    def test_nadir_is_lowest(self):
        nadir = CIRCADIAN_MULTIPLIERS[CircadianPhase.NADIR]
        for phase, mult in CIRCADIAN_MULTIPLIERS.items():
            assert nadir <= mult, f"Nadir ({nadir}) should be <= {phase} ({mult})"


# ---------------------------------------------------------------------------
# SleepOpportunity
# ---------------------------------------------------------------------------


class TestSleepOpportunity:
    def test_duration_calculated(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end)
        assert so.duration_hours == 8.0

    def test_duration_negative_clamped_to_zero(self):
        start = datetime(2024, 1, 2, 7, 0)
        end = datetime(2024, 1, 1, 23, 0)
        so = SleepOpportunity(start_time=start, end_time=end)
        assert so.duration_hours == 0

    def test_effective_sleep_perfect_quality(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end, quality_factor=1.0)
        assert so.effective_sleep_hours == 8.0

    def test_effective_sleep_reduced_quality(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end, quality_factor=0.5)
        assert so.effective_sleep_hours == 4.0

    def test_effective_sleep_circadian_misalignment(self):
        start = datetime(2024, 1, 1, 8, 0)  # daytime sleep
        end = datetime(2024, 1, 1, 16, 0)
        so = SleepOpportunity(start_time=start, end_time=end, circadian_aligned=False)
        # 8 hours * 1.0 quality * 0.8 misalignment = 6.4
        assert abs(so.effective_sleep_hours - 6.4) < 0.01

    def test_effective_sleep_interruptions(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end, interruptions=4)
        # 8 hours * 1.0 * (1 - 4*0.05) = 8 * 0.8 = 6.4
        assert abs(so.effective_sleep_hours - 6.4) < 0.01

    def test_interruption_penalty_clamped_at_50pct(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end, interruptions=20)
        # penalty = 1 - 20*0.05 = 0.0, clamped to 0.5
        # 8 * 0.5 = 4.0
        assert abs(so.effective_sleep_hours - 4.0) < 0.01

    def test_effective_sleep_environment_factor(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end, environment_factor=0.5)
        assert abs(so.effective_sleep_hours - 4.0) < 0.01

    def test_combined_factors(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(
            start_time=start,
            end_time=end,
            quality_factor=0.9,
            circadian_aligned=False,
            interruptions=2,
            environment_factor=0.8,
        )
        # 8 * 0.9 * 0.8 * (1 - 0.1) * 0.8 = 8 * 0.9 * 0.8 * 0.9 * 0.8
        expected = 8.0 * 0.9 * 0.8 * 0.9 * 0.8
        assert abs(so.effective_sleep_hours - expected) < 0.01

    def test_defaults(self):
        start = datetime(2024, 1, 1, 23, 0)
        end = datetime(2024, 1, 2, 7, 0)
        so = SleepOpportunity(start_time=start, end_time=end)
        assert so.quality_factor == 1.0
        assert so.is_primary_sleep is True
        assert so.circadian_aligned is True
        assert so.interruptions == 0
        assert so.environment_factor == 1.0


# ---------------------------------------------------------------------------
# SleepDebtState
# ---------------------------------------------------------------------------


class TestSleepDebtState:
    def test_construction(self):
        rid = uuid4()
        now = datetime.utcnow()
        state = SleepDebtState(
            resident_id=rid,
            current_debt_hours=5.0,
            last_updated=now,
        )
        assert state.resident_id == rid
        assert state.current_debt_hours == 5.0
        assert state.consecutive_deficit_days == 0
        assert state.chronic_debt is False
        assert state.debt_severity == "none"
        assert state.impairment_equivalent_bac == 0.0

    def test_to_dict_keys(self):
        state = SleepDebtState(
            resident_id=uuid4(),
            current_debt_hours=10.5,
            last_updated=datetime(2024, 1, 1, 12, 0),
            consecutive_deficit_days=3,
            recovery_sleep_needed=15.75,
            chronic_debt=False,
            debt_severity="moderate",
            impairment_equivalent_bac=0.053,
        )
        d = state.to_dict()
        assert d["current_debt_hours"] == 10.5
        assert d["consecutive_deficit_days"] == 3
        assert d["recovery_sleep_needed"] == 15.8  # rounded
        assert d["chronic_debt"] is False
        assert d["debt_severity"] == "moderate"
        assert d["impairment_equivalent_bac"] == 0.053

    def test_to_dict_resident_id_is_string(self):
        rid = uuid4()
        state = SleepDebtState(
            resident_id=rid,
            current_debt_hours=0,
            last_updated=datetime.utcnow(),
        )
        d = state.to_dict()
        assert d["resident_id"] == str(rid)

    def test_to_dict_last_updated_iso(self):
        dt = datetime(2024, 6, 15, 14, 30, 0)
        state = SleepDebtState(
            resident_id=uuid4(),
            current_debt_hours=0,
            last_updated=dt,
        )
        d = state.to_dict()
        assert d["last_updated"] == "2024-06-15T14:30:00"


# ---------------------------------------------------------------------------
# SleepDebtModel init and constants
# ---------------------------------------------------------------------------


class TestSleepDebtModelInit:
    def test_defaults(self):
        model = SleepDebtModel()
        assert model.baseline_sleep_need == 7.5

    def test_custom_baseline(self):
        model = SleepDebtModel(baseline_sleep_need=8.0)
        assert model.baseline_sleep_need == 8.0

    def test_individual_variability(self):
        model = SleepDebtModel(baseline_sleep_need=7.5, individual_variability=0.5)
        assert model.baseline_sleep_need == 8.0

    def test_negative_variability(self):
        model = SleepDebtModel(baseline_sleep_need=7.5, individual_variability=-0.5)
        assert model.baseline_sleep_need == 7.0

    def test_class_constants(self):
        assert SleepDebtModel.BASELINE_SLEEP_NEED == 7.5
        assert SleepDebtModel.MAX_DEBT_HOURS == 40.0
        assert SleepDebtModel.DEBT_RECOVERY_RATIO == 1.5
        assert SleepDebtModel.CHRONIC_THRESHOLD_DAYS == 5


# ---------------------------------------------------------------------------
# SleepDebtModel.calculate_daily_debt
# ---------------------------------------------------------------------------


class TestCalculateDailyDebt:
    def test_perfect_sleep_no_debt(self):
        model = SleepDebtModel()
        sleep = SleepOpportunity(
            start_time=datetime(2024, 1, 1, 23, 0),
            end_time=datetime(2024, 1, 2, 6, 30),  # 7.5 hours
        )
        debt = model.calculate_daily_debt([sleep])
        assert abs(debt) < 0.01

    def test_short_sleep_creates_debt(self):
        model = SleepDebtModel()
        sleep = SleepOpportunity(
            start_time=datetime(2024, 1, 1, 23, 0),
            end_time=datetime(2024, 1, 2, 4, 30),  # 5.5 hours
        )
        debt = model.calculate_daily_debt([sleep])
        assert abs(debt - 2.0) < 0.01  # 7.5 - 5.5 = 2.0

    def test_oversleep_negative_debt(self):
        model = SleepDebtModel()
        sleep = SleepOpportunity(
            start_time=datetime(2024, 1, 1, 22, 0),
            end_time=datetime(2024, 1, 2, 8, 0),  # 10 hours
        )
        debt = model.calculate_daily_debt([sleep])
        assert debt < 0  # 7.5 - 10 = -2.5

    def test_multiple_sleep_periods(self):
        model = SleepDebtModel()
        primary = SleepOpportunity(
            start_time=datetime(2024, 1, 1, 23, 0),
            end_time=datetime(2024, 1, 2, 5, 0),  # 6 hours
        )
        nap = SleepOpportunity(
            start_time=datetime(2024, 1, 2, 13, 0),
            end_time=datetime(2024, 1, 2, 14, 0),  # 1 hour nap
        )
        debt = model.calculate_daily_debt([primary, nap])
        assert abs(debt - 0.5) < 0.01  # 7.5 - (6 + 1) = 0.5

    def test_quality_factor_increases_debt(self):
        model = SleepDebtModel()
        sleep = SleepOpportunity(
            start_time=datetime(2024, 1, 1, 23, 0),
            end_time=datetime(2024, 1, 2, 6, 30),  # 7.5 hours
            quality_factor=0.8,
        )
        debt = model.calculate_daily_debt([sleep])
        # effective = 7.5 * 0.8 = 6.0, debt = 7.5 - 6.0 = 1.5
        assert abs(debt - 1.5) < 0.01

    def test_no_sleep_maximum_debt(self):
        model = SleepDebtModel()
        debt = model.calculate_daily_debt([])
        assert abs(debt - 7.5) < 0.01


# ---------------------------------------------------------------------------
# SleepDebtModel.update_cumulative_debt
# ---------------------------------------------------------------------------


class TestUpdateCumulativeDebt:
    def test_first_day_deficit(self):
        model = SleepDebtModel()
        rid = uuid4()
        state = model.update_cumulative_debt(rid, 2.0)
        assert state.current_debt_hours == 2.0
        assert state.consecutive_deficit_days == 1
        assert state.resident_id == rid

    def test_accumulating_debt(self):
        model = SleepDebtModel()
        rid = uuid4()
        model.update_cumulative_debt(rid, 2.0)
        state = model.update_cumulative_debt(rid, 3.0)
        assert state.current_debt_hours == 5.0
        assert state.consecutive_deficit_days == 2

    def test_recovery_with_extra_sleep(self):
        model = SleepDebtModel()
        rid = uuid4()
        model.update_cumulative_debt(rid, 5.0)  # 5 hours debt
        # Sleep -1.0 means 1 hour over baseline, triggers recovery
        state = model.update_cumulative_debt(rid, -1.0)
        # Recovery: abs(-1.0) / 1.5 = 0.667 hours recovered
        # new_debt = 5.0 - 0.667 = ~4.33
        assert state.current_debt_hours < 5.0
        assert state.consecutive_deficit_days == 0

    def test_debt_capped_at_max(self):
        model = SleepDebtModel()
        rid = uuid4()
        model.update_cumulative_debt(rid, 35.0)
        state = model.update_cumulative_debt(rid, 10.0)
        assert state.current_debt_hours == 40.0  # MAX_DEBT_HOURS

    def test_debt_cannot_go_negative(self):
        model = SleepDebtModel()
        rid = uuid4()
        state = model.update_cumulative_debt(rid, -5.0)
        assert state.current_debt_hours >= 0

    def test_chronic_debt_threshold(self):
        model = SleepDebtModel()
        rid = uuid4()
        for _ in range(5):
            state = model.update_cumulative_debt(rid, 1.0)
        assert state.consecutive_deficit_days == 5
        assert state.chronic_debt is True

    def test_severity_classification(self):
        model = SleepDebtModel()
        rid = uuid4()
        state = model.update_cumulative_debt(rid, 1.0)
        assert state.debt_severity == "none"  # < 2 hours

    def test_recovery_sleep_needed(self):
        model = SleepDebtModel()
        rid = uuid4()
        state = model.update_cumulative_debt(rid, 10.0)
        assert state.recovery_sleep_needed == 15.0  # 10 * 1.5

    def test_impairment_bac(self):
        model = SleepDebtModel()
        rid = uuid4()
        state = model.update_cumulative_debt(rid, 10.0)
        assert abs(state.impairment_equivalent_bac - 0.050) < 0.001

    def test_no_natural_recovery(self):
        model = SleepDebtModel()
        rid = uuid4()
        model.update_cumulative_debt(rid, 5.0)
        state = model.update_cumulative_debt(rid, -1.0, natural_recovery=False)
        # Without natural recovery, surplus sleep just reduces debt directly
        # daily_change = -1.0, new_debt = 5.0 + (-1.0) = 4.0
        assert state.current_debt_hours == 4.0


# ---------------------------------------------------------------------------
# SleepDebtModel.get_circadian_phase
# ---------------------------------------------------------------------------


class TestGetCircadianPhase:
    def test_nadir(self):
        model = SleepDebtModel()
        for hour in [2, 3, 4, 5]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.NADIR

    def test_early_morning(self):
        model = SleepDebtModel()
        for hour in [6, 7, 8]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.EARLY_MORNING

    def test_morning_peak(self):
        model = SleepDebtModel()
        for hour in [9, 10, 11]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.MORNING_PEAK

    def test_post_lunch(self):
        model = SleepDebtModel()
        for hour in [12, 13, 14]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.POST_LUNCH

    def test_afternoon(self):
        model = SleepDebtModel()
        for hour in [15, 16, 17]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.AFTERNOON

    def test_evening(self):
        model = SleepDebtModel()
        for hour in [18, 19, 20]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.EVENING

    def test_night(self):
        model = SleepDebtModel()
        for hour in [21, 22, 23, 0, 1]:
            dt = datetime(2024, 1, 1, hour, 0)
            assert model.get_circadian_phase(dt) == CircadianPhase.NIGHT


# ---------------------------------------------------------------------------
# SleepDebtModel.get_circadian_multiplier
# ---------------------------------------------------------------------------


class TestGetCircadianMultiplier:
    def test_nadir_multiplier(self):
        model = SleepDebtModel()
        mult = model.get_circadian_multiplier(datetime(2024, 1, 1, 4, 0))
        assert mult == 0.6

    def test_morning_peak_multiplier(self):
        model = SleepDebtModel()
        mult = model.get_circadian_multiplier(datetime(2024, 1, 1, 10, 0))
        assert mult == 1.0

    def test_night_multiplier(self):
        model = SleepDebtModel()
        mult = model.get_circadian_multiplier(datetime(2024, 1, 1, 22, 0))
        assert mult == 0.75


# ---------------------------------------------------------------------------
# SleepDebtModel.calculate_circadian_curve
# ---------------------------------------------------------------------------


class TestCalculateCircadianCurve:
    def test_24_hour_curve(self):
        model = SleepDebtModel()
        start = datetime(2024, 1, 1, 0, 0)
        curve = model.calculate_circadian_curve(start, duration_hours=24)
        assert len(curve) == 24

    def test_curve_data_point_keys(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 0, 0), 1)
        point = curve[0]
        assert "time" in point
        assert "hour" in point
        assert "phase" in point
        assert "phase_name" in point
        assert "alertness_multiplier" in point
        assert "alertness_percent" in point

    def test_alertness_percent_is_int(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 0, 0), 24)
        for point in curve:
            assert isinstance(point["alertness_percent"], int)

    def test_hours_increment(self):
        model = SleepDebtModel()
        start = datetime(2024, 1, 1, 6, 0)
        curve = model.calculate_circadian_curve(start, 5)
        hours = [p["hour"] for p in curve]
        assert hours == [6, 7, 8, 9, 10]


# ---------------------------------------------------------------------------
# SleepDebtModel.predict_debt_trajectory
# ---------------------------------------------------------------------------


class TestPredictDebtTrajectory:
    def test_trajectory_length(self):
        model = SleepDebtModel()
        planned = [6.0, 5.5, 7.0, 9.0, 9.0]
        traj = model.predict_debt_trajectory(uuid4(), planned, start_debt=0)
        assert len(traj) == 5

    def test_trajectory_keys(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(uuid4(), [6.0], start_debt=0)
        point = traj[0]
        assert "day" in point
        assert "planned_sleep_hours" in point
        assert "debt_change" in point
        assert "cumulative_debt" in point
        assert "severity" in point
        assert "impairment_bac" in point
        assert "deficit_days" in point

    def test_increasing_debt(self):
        model = SleepDebtModel()
        # 3 days of short sleep: debt increases each day
        traj = model.predict_debt_trajectory(uuid4(), [5.0, 5.0, 5.0], start_debt=0)
        debts = [p["cumulative_debt"] for p in traj]
        assert debts[0] < debts[1] < debts[2]

    def test_recovery_in_trajectory(self):
        model = SleepDebtModel()
        # 2 days short sleep, then 2 days of recovery sleep
        traj = model.predict_debt_trajectory(
            uuid4(), [5.0, 5.0, 10.0, 10.0], start_debt=0
        )
        # Debt should peak then decrease
        debts = [p["cumulative_debt"] for p in traj]
        peak = max(debts)
        assert debts[-1] < peak

    def test_start_debt_used(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(uuid4(), [5.0], start_debt=10.0)
        # Starting from 10, add 2.5 more (7.5-5.0)
        assert traj[0]["cumulative_debt"] == 12.5

    def test_debt_capped_at_max(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(uuid4(), [0.0], start_debt=38.0)
        # 38 + 7.5 = 45.5, but capped at 40
        assert traj[0]["cumulative_debt"] == 40.0

    def test_day_numbering_starts_at_1(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(uuid4(), [7.5, 7.5], start_debt=0)
        assert traj[0]["day"] == 1
        assert traj[1]["day"] == 2


# ---------------------------------------------------------------------------
# SleepDebtModel.estimate_recovery_time
# ---------------------------------------------------------------------------


class TestEstimateRecoveryTime:
    def test_no_debt_zero_nights(self):
        model = SleepDebtModel()
        assert model.estimate_recovery_time(0) == 0

    def test_negative_debt_zero_nights(self):
        model = SleepDebtModel()
        assert model.estimate_recovery_time(-5.0) == 0

    def test_basic_recovery(self):
        model = SleepDebtModel()
        # debt=15, recovery_sleep=9, extra=1.5, recovery_per_night=1.0
        nights = model.estimate_recovery_time(15.0, 9.0)
        assert nights == 15

    def test_cannot_recover_without_extra(self):
        model = SleepDebtModel()
        # recovery_sleep == baseline: no extra sleep
        nights = model.estimate_recovery_time(10.0, 7.5)
        assert nights == -1

    def test_cannot_recover_below_baseline(self):
        model = SleepDebtModel()
        nights = model.estimate_recovery_time(10.0, 6.0)
        assert nights == -1

    def test_more_sleep_faster_recovery(self):
        model = SleepDebtModel()
        nights_9 = model.estimate_recovery_time(15.0, 9.0)
        nights_10 = model.estimate_recovery_time(15.0, 10.0)
        assert nights_10 < nights_9


# ---------------------------------------------------------------------------
# SleepDebtModel._classify_debt_severity
# ---------------------------------------------------------------------------


class TestClassifyDebtSeverity:
    def test_none(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(0.0) == "none"
        assert model._classify_debt_severity(1.9) == "none"

    def test_mild(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(2.0) == "mild"
        assert model._classify_debt_severity(4.9) == "mild"

    def test_moderate(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(5.0) == "moderate"
        assert model._classify_debt_severity(9.9) == "moderate"

    def test_severe(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(10.0) == "severe"
        assert model._classify_debt_severity(19.9) == "severe"

    def test_critical(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(20.0) == "critical"
        assert model._classify_debt_severity(40.0) == "critical"


# ---------------------------------------------------------------------------
# SleepDebtModel._calculate_impairment_equivalent
# ---------------------------------------------------------------------------


class TestCalculateImpairmentEquivalent:
    def test_zero_debt_zero_impairment(self):
        model = SleepDebtModel()
        assert model._calculate_impairment_equivalent(0.0) == 0.0

    def test_10_hours_debt(self):
        model = SleepDebtModel()
        bac = model._calculate_impairment_equivalent(10.0)
        assert abs(bac - 0.05) < 0.001

    def test_20_hours_debt(self):
        model = SleepDebtModel()
        bac = model._calculate_impairment_equivalent(20.0)
        assert abs(bac - 0.10) < 0.001

    def test_capped_at_015(self):
        model = SleepDebtModel()
        bac = model._calculate_impairment_equivalent(50.0)
        assert bac == 0.15

    def test_linear_scaling(self):
        model = SleepDebtModel()
        bac5 = model._calculate_impairment_equivalent(5.0)
        bac10 = model._calculate_impairment_equivalent(10.0)
        assert abs(bac10 - 2 * bac5) < 0.001


# ---------------------------------------------------------------------------
# get_circadian_phases_info
# ---------------------------------------------------------------------------


class TestGetCircadianPhasesInfo:
    def test_returns_7_phases(self):
        info = get_circadian_phases_info()
        assert len(info) == 7

    def test_phase_dict_keys(self):
        info = get_circadian_phases_info()
        for item in info:
            assert "phase" in item
            assert "name" in item
            assert "time_range" in item
            assert "alertness_multiplier" in item
            assert "description" in item

    def test_phase_values_match_enum(self):
        info = get_circadian_phases_info()
        phase_values = {item["phase"] for item in info}
        enum_values = {p.value for p in CircadianPhase}
        assert phase_values == enum_values

    def test_descriptions_not_empty(self):
        info = get_circadian_phases_info()
        for item in info:
            assert len(item["description"]) > 0

    def test_time_ranges_not_unknown(self):
        info = get_circadian_phases_info()
        for item in info:
            assert item["time_range"] != "Unknown"
