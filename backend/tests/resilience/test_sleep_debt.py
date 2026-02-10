"""Tests for sleep debt accumulation model with circadian rhythm (no DB)."""

import math
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.resilience.frms.sleep_debt import (
    CIRCADIAN_MULTIPLIERS,
    CircadianPhase,
    SleepDebtModel,
    SleepDebtState,
    SleepOpportunity,
    _get_phase_description,
    _get_phase_time_range,
    get_circadian_phases_info,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESIDENT_ID = UUID("00000000-0000-0000-0000-000000000001")


def _sleep(
    start_hour: int = 23,
    duration_hours: float = 7.5,
    quality: float = 1.0,
    aligned: bool = True,
    interruptions: int = 0,
    env: float = 1.0,
) -> SleepOpportunity:
    """Create a SleepOpportunity with convenient defaults."""
    start = datetime(2024, 1, 1, start_hour, 0)
    end = start + timedelta(hours=duration_hours)
    return SleepOpportunity(
        start_time=start,
        end_time=end,
        quality_factor=quality,
        circadian_aligned=aligned,
        interruptions=interruptions,
        environment_factor=env,
    )


# ---------------------------------------------------------------------------
# CircadianPhase enum
# ---------------------------------------------------------------------------


class TestCircadianPhase:
    def test_nadir(self):
        assert CircadianPhase.NADIR.value == "nadir"

    def test_morning_peak(self):
        assert CircadianPhase.MORNING_PEAK.value == "morning_peak"

    def test_member_count(self):
        assert len(CircadianPhase) == 7

    def test_all_phases_have_multipliers(self):
        for phase in CircadianPhase:
            assert phase in CIRCADIAN_MULTIPLIERS


# ---------------------------------------------------------------------------
# CIRCADIAN_MULTIPLIERS
# ---------------------------------------------------------------------------


class TestCircadianMultipliers:
    def test_nadir_lowest(self):
        assert CIRCADIAN_MULTIPLIERS[CircadianPhase.NADIR] == 0.6

    def test_morning_peak_highest(self):
        assert CIRCADIAN_MULTIPLIERS[CircadianPhase.MORNING_PEAK] == 1.0

    def test_all_between_zero_and_one(self):
        for phase, mult in CIRCADIAN_MULTIPLIERS.items():
            assert 0.0 < mult <= 1.0, f"{phase} has multiplier {mult}"


# ---------------------------------------------------------------------------
# SleepOpportunity
# ---------------------------------------------------------------------------


class TestSleepOpportunity:
    def test_duration_computed(self):
        so = _sleep(start_hour=23, duration_hours=8.0)
        assert abs(so.duration_hours - 8.0) < 1e-10

    def test_zero_duration(self):
        start = datetime(2024, 1, 1, 23, 0)
        so = SleepOpportunity(start_time=start, end_time=start)
        assert so.duration_hours == 0.0

    def test_negative_duration_clamped(self):
        start = datetime(2024, 1, 2, 7, 0)
        end = datetime(2024, 1, 2, 5, 0)  # End before start
        so = SleepOpportunity(start_time=start, end_time=end)
        assert so.duration_hours == 0.0

    def test_effective_sleep_perfect(self):
        so = _sleep(duration_hours=8.0, quality=1.0, aligned=True, interruptions=0)
        assert abs(so.effective_sleep_hours - 8.0) < 1e-10

    def test_effective_sleep_quality_factor(self):
        so = _sleep(duration_hours=8.0, quality=0.5)
        assert abs(so.effective_sleep_hours - 4.0) < 1e-10

    def test_effective_sleep_misaligned(self):
        so = _sleep(duration_hours=8.0, quality=1.0, aligned=False)
        # 8 * 1.0 * 0.8 = 6.4
        assert abs(so.effective_sleep_hours - 6.4) < 1e-10

    def test_effective_sleep_interruptions(self):
        so = _sleep(duration_hours=8.0, quality=1.0, interruptions=2)
        # 8 * 1.0 * (1 - 2*0.05) = 8 * 0.9 = 7.2
        assert abs(so.effective_sleep_hours - 7.2) < 1e-10

    def test_interruption_penalty_floor(self):
        so = _sleep(duration_hours=8.0, quality=1.0, interruptions=20)
        # Penalty = 1 - 20*0.05 = 0.0, clamped to 0.5
        assert abs(so.effective_sleep_hours - 4.0) < 1e-10

    def test_effective_sleep_environment(self):
        so = _sleep(duration_hours=8.0, quality=1.0, env=0.5)
        assert abs(so.effective_sleep_hours - 4.0) < 1e-10

    def test_effective_sleep_combined_factors(self):
        so = _sleep(
            duration_hours=10.0, quality=0.8, aligned=False, interruptions=1, env=0.9
        )
        # 10 * 0.8 * 0.8 * (1 - 0.05) * 0.9 = 10 * 0.8 * 0.8 * 0.95 * 0.9
        expected = 10.0 * 0.8 * 0.8 * 0.95 * 0.9
        assert abs(so.effective_sleep_hours - expected) < 1e-10

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
        state = SleepDebtState(
            resident_id=RESIDENT_ID,
            current_debt_hours=5.0,
            last_updated=datetime(2024, 1, 1),
        )
        assert state.current_debt_hours == 5.0
        assert state.resident_id == RESIDENT_ID

    def test_defaults(self):
        state = SleepDebtState(
            resident_id=RESIDENT_ID,
            current_debt_hours=0.0,
            last_updated=datetime(2024, 1, 1),
        )
        assert state.consecutive_deficit_days == 0
        assert state.recovery_sleep_needed == 0.0
        assert state.chronic_debt is False
        assert state.debt_severity == "none"
        assert state.impairment_equivalent_bac == 0.0

    def test_to_dict(self):
        state = SleepDebtState(
            resident_id=RESIDENT_ID,
            current_debt_hours=10.0,
            last_updated=datetime(2024, 1, 1),
            chronic_debt=True,
            debt_severity="moderate",
        )
        d = state.to_dict()
        assert d["current_debt_hours"] == 10.0
        assert d["chronic_debt"] is True
        assert d["debt_severity"] == "moderate"
        assert d["resident_id"] == str(RESIDENT_ID)

    def test_to_dict_rounds_values(self):
        state = SleepDebtState(
            resident_id=RESIDENT_ID,
            current_debt_hours=5.123456,
            last_updated=datetime(2024, 1, 1),
            recovery_sleep_needed=7.654321,
            impairment_equivalent_bac=0.025678,
        )
        d = state.to_dict()
        assert d["current_debt_hours"] == 5.1
        assert d["recovery_sleep_needed"] == 7.7
        assert d["impairment_equivalent_bac"] == 0.026


# ---------------------------------------------------------------------------
# SleepDebtModel — init
# ---------------------------------------------------------------------------


class TestSleepDebtModelInit:
    def test_default_baseline(self):
        model = SleepDebtModel()
        assert model.baseline_sleep_need == 7.5

    def test_custom_baseline(self):
        model = SleepDebtModel(baseline_sleep_need=8.0)
        assert model.baseline_sleep_need == 8.0

    def test_individual_variability(self):
        model = SleepDebtModel(baseline_sleep_need=7.5, individual_variability=0.5)
        assert model.baseline_sleep_need == 8.0


# ---------------------------------------------------------------------------
# SleepDebtModel — calculate_daily_debt
# ---------------------------------------------------------------------------


class TestCalculateDailyDebt:
    def test_no_sleep(self):
        model = SleepDebtModel()
        debt = model.calculate_daily_debt([])
        assert abs(debt - 7.5) < 1e-10

    def test_perfect_sleep(self):
        model = SleepDebtModel()
        sleep = _sleep(duration_hours=7.5)
        debt = model.calculate_daily_debt([sleep])
        assert abs(debt) < 1e-10

    def test_extra_sleep_negative_debt(self):
        model = SleepDebtModel()
        sleep = _sleep(duration_hours=9.0)
        debt = model.calculate_daily_debt([sleep])
        assert debt < 0

    def test_short_sleep_positive_debt(self):
        model = SleepDebtModel()
        sleep = _sleep(duration_hours=5.0)
        debt = model.calculate_daily_debt([sleep])
        assert abs(debt - 2.5) < 1e-10

    def test_multiple_sleep_periods(self):
        model = SleepDebtModel()
        main = _sleep(duration_hours=5.0)
        nap = _sleep(start_hour=14, duration_hours=1.0)
        debt = model.calculate_daily_debt([main, nap])
        # 7.5 - (5 + 1) = 1.5
        assert abs(debt - 1.5) < 1e-10

    def test_quality_affects_debt(self):
        model = SleepDebtModel()
        sleep = _sleep(duration_hours=7.5, quality=0.5)
        debt = model.calculate_daily_debt([sleep])
        # effective = 7.5 * 0.5 = 3.75; debt = 7.5 - 3.75 = 3.75
        assert abs(debt - 3.75) < 1e-10


# ---------------------------------------------------------------------------
# SleepDebtModel — get_circadian_phase
# ---------------------------------------------------------------------------


class TestGetCircadianPhase:
    def test_nadir(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 3, 0))
            == CircadianPhase.NADIR
        )

    def test_early_morning(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 7, 0))
            == CircadianPhase.EARLY_MORNING
        )

    def test_morning_peak(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 10, 0))
            == CircadianPhase.MORNING_PEAK
        )

    def test_post_lunch(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 13, 0))
            == CircadianPhase.POST_LUNCH
        )

    def test_afternoon(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 16, 0))
            == CircadianPhase.AFTERNOON
        )

    def test_evening(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 19, 0))
            == CircadianPhase.EVENING
        )

    def test_night_late(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 22, 0))
            == CircadianPhase.NIGHT
        )

    def test_night_early(self):
        model = SleepDebtModel()
        # Hour 0 and 1 should be NIGHT (< 2)
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 0, 0))
            == CircadianPhase.NIGHT
        )
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 1, 0))
            == CircadianPhase.NIGHT
        )

    def test_boundary_2am(self):
        model = SleepDebtModel()
        assert (
            model.get_circadian_phase(datetime(2024, 1, 1, 2, 0))
            == CircadianPhase.NADIR
        )


# ---------------------------------------------------------------------------
# SleepDebtModel — get_circadian_multiplier
# ---------------------------------------------------------------------------


class TestGetCircadianMultiplier:
    def test_nadir_multiplier(self):
        model = SleepDebtModel()
        mult = model.get_circadian_multiplier(datetime(2024, 1, 1, 4, 0))
        assert mult == 0.6

    def test_peak_multiplier(self):
        model = SleepDebtModel()
        mult = model.get_circadian_multiplier(datetime(2024, 1, 1, 10, 0))
        assert mult == 1.0


# ---------------------------------------------------------------------------
# SleepDebtModel — calculate_circadian_curve
# ---------------------------------------------------------------------------


class TestCalculateCircadianCurve:
    def test_24h_curve_length(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 0, 0), 24)
        assert len(curve) == 24

    def test_default_24h(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 0, 0))
        assert len(curve) == 24

    def test_curve_data_fields(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 0, 0), 1)
        entry = curve[0]
        assert "time" in entry
        assert "hour" in entry
        assert "phase" in entry
        assert "phase_name" in entry
        assert "alertness_multiplier" in entry
        assert "alertness_percent" in entry

    def test_short_curve(self):
        model = SleepDebtModel()
        curve = model.calculate_circadian_curve(datetime(2024, 1, 1, 9, 0), 3)
        assert len(curve) == 3
        assert curve[0]["hour"] == 9
        assert curve[1]["hour"] == 10
        assert curve[2]["hour"] == 11


# ---------------------------------------------------------------------------
# SleepDebtModel — update_cumulative_debt
# ---------------------------------------------------------------------------


class TestUpdateCumulativeDebt:
    def test_positive_debt_accumulates(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, 2.0)
        assert abs(state.current_debt_hours - 2.0) < 1e-10

    def test_consecutive_positive_debt(self):
        model = SleepDebtModel()
        model.update_cumulative_debt(RESIDENT_ID, 2.0)
        state = model.update_cumulative_debt(RESIDENT_ID, 3.0)
        assert abs(state.current_debt_hours - 5.0) < 1e-10

    def test_deficit_days_increment(self):
        model = SleepDebtModel()
        model.update_cumulative_debt(RESIDENT_ID, 1.0)
        state = model.update_cumulative_debt(RESIDENT_ID, 1.0)
        assert state.consecutive_deficit_days == 2

    def test_deficit_days_reset_on_recovery(self):
        model = SleepDebtModel()
        model.update_cumulative_debt(RESIDENT_ID, 2.0)
        model.update_cumulative_debt(RESIDENT_ID, 2.0)
        state = model.update_cumulative_debt(RESIDENT_ID, -1.0)
        assert state.consecutive_deficit_days == 0

    def test_chronic_debt_after_threshold(self):
        model = SleepDebtModel()
        for _ in range(5):
            state = model.update_cumulative_debt(RESIDENT_ID, 1.0)
        assert state.chronic_debt is True
        assert state.consecutive_deficit_days == 5

    def test_not_chronic_before_threshold(self):
        model = SleepDebtModel()
        for _ in range(4):
            state = model.update_cumulative_debt(RESIDENT_ID, 1.0)
        assert state.chronic_debt is False

    def test_max_debt_capped(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, 50.0)
        assert state.current_debt_hours <= SleepDebtModel.MAX_DEBT_HOURS

    def test_recovery_with_natural_recovery(self):
        model = SleepDebtModel()
        model.update_cumulative_debt(RESIDENT_ID, 10.0)
        state = model.update_cumulative_debt(RESIDENT_ID, -1.0)
        # Recovery: abs(-1.0) / 1.5 = 0.667 removed from 10.0
        expected = 10.0 - (1.0 / 1.5)
        assert abs(state.current_debt_hours - expected) < 1e-10

    def test_recovery_no_natural(self):
        model = SleepDebtModel()
        model.update_cumulative_debt(RESIDENT_ID, 10.0)
        state = model.update_cumulative_debt(RESIDENT_ID, -1.0, natural_recovery=False)
        # Without natural recovery, debt + change = 10 + (-1) = 9
        assert abs(state.current_debt_hours - 9.0) < 1e-10

    def test_debt_never_negative(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, -5.0)
        assert state.current_debt_hours >= 0.0

    def test_severity_classified(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, 7.0)
        assert state.debt_severity == "moderate"

    def test_impairment_bac_set(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, 10.0)
        assert abs(state.impairment_equivalent_bac - 0.05) < 1e-10

    def test_recovery_sleep_needed(self):
        model = SleepDebtModel()
        state = model.update_cumulative_debt(RESIDENT_ID, 10.0)
        # recovery = 10 * 1.5 = 15.0
        assert abs(state.recovery_sleep_needed - 15.0) < 1e-10


# ---------------------------------------------------------------------------
# SleepDebtModel — predict_debt_trajectory
# ---------------------------------------------------------------------------


class TestPredictDebtTrajectory:
    def test_returns_correct_days(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [6.0, 7.0, 8.0])
        assert len(traj) == 3
        assert traj[0]["day"] == 1
        assert traj[2]["day"] == 3

    def test_debt_increases_with_short_sleep(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [5.0, 5.0], start_debt=0.0)
        assert traj[0]["cumulative_debt"] > 0
        assert traj[1]["cumulative_debt"] > traj[0]["cumulative_debt"]

    def test_debt_decreases_with_long_sleep(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [9.0, 9.0], start_debt=10.0)
        assert traj[0]["cumulative_debt"] < 10.0
        assert traj[1]["cumulative_debt"] < traj[0]["cumulative_debt"]

    def test_start_debt_used(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [5.0], start_debt=5.0)
        # debt_change = 7.5 - 5 = 2.5, cumulative = 5 + 2.5 = 7.5
        assert abs(traj[0]["cumulative_debt"] - 7.5) < 1e-10

    def test_trajectory_fields(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [6.0], start_debt=0.0)
        entry = traj[0]
        assert "day" in entry
        assert "planned_sleep_hours" in entry
        assert "debt_change" in entry
        assert "cumulative_debt" in entry
        assert "severity" in entry
        assert "impairment_bac" in entry
        assert "deficit_days" in entry

    def test_capped_at_max(self):
        model = SleepDebtModel()
        traj = model.predict_debt_trajectory(RESIDENT_ID, [0.0] * 10, start_debt=35.0)
        for entry in traj:
            assert entry["cumulative_debt"] <= SleepDebtModel.MAX_DEBT_HOURS


# ---------------------------------------------------------------------------
# SleepDebtModel — estimate_recovery_time
# ---------------------------------------------------------------------------


class TestEstimateRecoveryTime:
    def test_zero_debt(self):
        model = SleepDebtModel()
        assert model.estimate_recovery_time(0.0) == 0

    def test_negative_debt(self):
        model = SleepDebtModel()
        assert model.estimate_recovery_time(-5.0) == 0

    def test_cannot_recover_without_extra(self):
        model = SleepDebtModel()
        # If recovery sleep equals baseline, no recovery possible
        assert model.estimate_recovery_time(10.0, recovery_sleep_per_night=7.5) == -1

    def test_known_recovery(self):
        model = SleepDebtModel()
        # Extra per night: 9.0 - 7.5 = 1.5
        # Recovery per night: 1.5 / 1.5 = 1.0
        # Nights: ceil(10 / 1) = 10
        assert model.estimate_recovery_time(10.0, 9.0) == 10

    def test_more_debt_more_nights(self):
        model = SleepDebtModel()
        n1 = model.estimate_recovery_time(5.0, 9.0)
        n2 = model.estimate_recovery_time(15.0, 9.0)
        assert n2 > n1


# ---------------------------------------------------------------------------
# SleepDebtModel — severity and impairment
# ---------------------------------------------------------------------------


class TestSeverityAndImpairment:
    def test_severity_none(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(1.5) == "none"

    def test_severity_mild(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(3.0) == "mild"

    def test_severity_moderate(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(7.0) == "moderate"

    def test_severity_severe(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(15.0) == "severe"

    def test_severity_critical(self):
        model = SleepDebtModel()
        assert model._classify_debt_severity(25.0) == "critical"

    def test_impairment_zero(self):
        model = SleepDebtModel()
        assert model._calculate_impairment_equivalent(0.0) == 0.0

    def test_impairment_10h(self):
        model = SleepDebtModel()
        assert abs(model._calculate_impairment_equivalent(10.0) - 0.05) < 1e-10

    def test_impairment_capped(self):
        model = SleepDebtModel()
        assert model._calculate_impairment_equivalent(100.0) == 0.15


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class TestModuleHelpers:
    def test_get_circadian_phases_info_length(self):
        info = get_circadian_phases_info()
        assert len(info) == 7

    def test_get_circadian_phases_info_fields(self):
        info = get_circadian_phases_info()
        for entry in info:
            assert "phase" in entry
            assert "name" in entry
            assert "time_range" in entry
            assert "alertness_multiplier" in entry
            assert "description" in entry

    def test_phase_time_range_nadir(self):
        assert _get_phase_time_range(CircadianPhase.NADIR) == "2:00 AM - 6:00 AM"

    def test_phase_time_range_morning_peak(self):
        assert (
            _get_phase_time_range(CircadianPhase.MORNING_PEAK) == "9:00 AM - 12:00 PM"
        )

    def test_phase_description_not_empty(self):
        for phase in CircadianPhase:
            desc = _get_phase_description(phase)
            assert len(desc) > 0
            assert desc != "Unknown phase"
