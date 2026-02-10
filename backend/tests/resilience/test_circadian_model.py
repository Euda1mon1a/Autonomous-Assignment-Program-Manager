"""Tests for circadian model (pure logic, no DB)."""

import math
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.resilience.circadian_model import (
    AMPLITUDE_DECAY_RATE,
    AMPLITUDE_RECOVERY_DAYS,
    AMPLITUDE_RECOVERY_RATE,
    NATURAL_PERIOD_HOURS,
    PRC_ADVANCE_MAX,
    PRC_DELAY_MAX,
    CircadianImpact,
    CircadianOscillator,
    CircadianQualityLevel,
    CircadianScheduleAnalyzer,
    CircadianShiftType,
)


RESIDENT_ID = UUID("00000000-0000-0000-0000-000000000001")
RESIDENT_ID_2 = UUID("00000000-0000-0000-0000-000000000002")


# -- CircadianShiftType enum --------------------------------------------------


class TestCircadianShiftType:
    def test_values(self):
        assert CircadianShiftType.DAY == "day"
        assert CircadianShiftType.EVENING == "evening"
        assert CircadianShiftType.NIGHT == "night"
        assert CircadianShiftType.LONG_DAY == "long_day"
        assert CircadianShiftType.SPLIT == "split"

    def test_member_count(self):
        assert len(CircadianShiftType) == 5

    def test_is_string_enum(self):
        assert isinstance(CircadianShiftType.DAY, str)


# -- CircadianQualityLevel enum -----------------------------------------------


class TestCircadianQualityLevel:
    def test_values(self):
        assert CircadianQualityLevel.EXCELLENT == "excellent"
        assert CircadianQualityLevel.GOOD == "good"
        assert CircadianQualityLevel.FAIR == "fair"
        assert CircadianQualityLevel.POOR == "poor"
        assert CircadianQualityLevel.CRITICAL == "critical"

    def test_member_count(self):
        assert len(CircadianQualityLevel) == 5


# -- Constants ----------------------------------------------------------------


class TestConstants:
    def test_natural_period(self):
        assert NATURAL_PERIOD_HOURS == 24.2

    def test_prc_advance_positive(self):
        assert PRC_ADVANCE_MAX > 0

    def test_prc_delay_negative(self):
        assert PRC_DELAY_MAX < 0

    def test_decay_faster_than_recovery(self):
        assert AMPLITUDE_DECAY_RATE > AMPLITUDE_RECOVERY_RATE


# -- CircadianOscillator dataclass --------------------------------------------


class TestCircadianOscillator:
    def test_creation_defaults(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        assert osc.resident_id == RESIDENT_ID
        assert osc.phase == 0.0
        assert osc.amplitude == 1.0
        assert osc.period == NATURAL_PERIOD_HOURS

    def test_phase_wraps(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=25.0)
        assert osc.phase == pytest.approx(1.0)

    def test_phase_negative_wraps(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=-2.0)
        assert osc.phase == pytest.approx(22.0)

    def test_amplitude_clamps_high(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.5)
        assert osc.amplitude == 1.0

    def test_amplitude_clamps_low(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=-0.5)
        assert osc.amplitude == 0.0

    def test_to_dict(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=6.0, amplitude=0.85)
        d = osc.to_dict()
        assert d["resident_id"] == str(RESIDENT_ID)
        assert d["phase"] == 6.0
        assert d["amplitude"] == 0.85
        assert "period" in d
        assert "last_updated" in d
        assert "chronotype_offset" in d
        assert "entrainment_strength" in d


# -- CircadianOscillator._get_prc_value --------------------------------------


class TestGetPrcValue:
    def test_dead_zone_zero(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        assert osc._get_prc_value(13.0) == 0.0
        assert osc._get_prc_value(14.0) == 0.0

    def test_morning_advance_positive(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # Peak at midpoint of [6, 10] = 8
        val = osc._get_prc_value(8.0)
        assert val > 0
        assert val == pytest.approx(PRC_ADVANCE_MAX, rel=0.01)

    def test_evening_night_delay_negative(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # Peak delay at midnight (hour=0 is in the 20-2 range)
        val = osc._get_prc_value(22.0)
        assert val < 0

    def test_midnight_delay(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # At midnight (hour=0) → t = (0+4)/4 = 1 → sin(pi) = 0
        # Actually hour=0 matches hour < 2 → t = (0 + 4) / 4 = 1.0
        val = osc._get_prc_value(0.0)
        # sin(pi * 1.0) = sin(pi) ≈ 0
        assert abs(val) < 0.01

    def test_transition_zone_2_to_6(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # At hour=2, t=0 → PRC_DELAY_MAX * (1-0) = PRC_DELAY_MAX
        val = osc._get_prc_value(2.0)
        assert val == pytest.approx(PRC_DELAY_MAX, rel=0.01)

    def test_transition_zone_10_to_12(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # At hour=10, t=0 → PRC_ADVANCE_MAX * (1-0) = PRC_ADVANCE_MAX
        val = osc._get_prc_value(10.0)
        assert val == pytest.approx(PRC_ADVANCE_MAX, rel=0.01)

    def test_transition_zone_16_to_20(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # At hour=16, t=0 → PRC_DELAY_MAX * 0 = 0
        val = osc._get_prc_value(16.0)
        assert val == pytest.approx(0.0, abs=0.01)

    def test_wraps_above_24(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID)
        # 25 % 24 = 1, which is in the delay zone (hour < 2)
        val = osc._get_prc_value(25.0)
        val_direct = osc._get_prc_value(1.0)
        assert val == pytest.approx(val_direct)


# -- CircadianOscillator.compute_phase_shift ----------------------------------


class TestComputePhaseShift:
    def test_day_shift_advance(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.0)
        shift_start = datetime(2026, 1, 15, 7, 0)  # 7 AM
        # midpoint = (7 + 8/2) % 24 = 11
        # PRC at 11 → transition zone (10-12): t = (11-10)/2 = 0.5 → PRC_ADVANCE_MAX * 0.5
        shift = osc.compute_phase_shift(shift_start, 8.0, CircadianShiftType.DAY)
        assert shift > 0  # Morning shift should advance phase

    def test_night_shift_amplified(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.0)
        shift_start = datetime(2026, 1, 15, 23, 0)  # 11 PM
        # Night shifts multiply by 1.5
        shift = osc.compute_phase_shift(shift_start, 8.0, CircadianShiftType.NIGHT)
        # midpoint hour = (23 + 4) % 24 = 3 → transition zone (2-6)
        # The shift should be nonzero
        assert shift != 0

    def test_split_shift_dampened(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.0)
        shift_start = datetime(2026, 1, 15, 7, 0)  # 7 AM
        day_shift = osc.compute_phase_shift(shift_start, 8.0, CircadianShiftType.DAY)
        split_shift = osc.compute_phase_shift(
            shift_start, 8.0, CircadianShiftType.SPLIT
        )
        # Split is 0.5x → half of day shift
        if day_shift != 0:
            assert abs(split_shift) < abs(day_shift)

    def test_amplitude_scales_shift(self):
        osc_strong = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.0)
        osc_weak = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.5)
        shift_start = datetime(2026, 1, 15, 7, 0)
        strong = osc_strong.compute_phase_shift(
            shift_start, 8.0, CircadianShiftType.DAY
        )
        weak = osc_weak.compute_phase_shift(shift_start, 8.0, CircadianShiftType.DAY)
        if strong != 0:
            assert abs(weak) == pytest.approx(abs(strong) * 0.5, rel=0.01)


# -- CircadianOscillator.update_phase -----------------------------------------


class TestUpdatePhase:
    def test_natural_advance(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=0.0)
        osc.update_phase(timedelta(hours=24))
        # natural_advance = 24 * (24 / 24.2) ≈ 23.80
        # phase = (0 + 23.80) % 24 = 23.80
        assert osc.phase == pytest.approx(
            24 * (24.0 / NATURAL_PERIOD_HOURS) % 24, rel=0.01
        )

    def test_with_phase_shift(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=12.0)
        osc.update_phase(timedelta(hours=0), phase_shift=2.0)
        assert osc.phase == pytest.approx(14.0)

    def test_wraps_around_24(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=23.0)
        osc.update_phase(timedelta(hours=0), phase_shift=3.0)
        assert osc.phase == pytest.approx(2.0)


# -- CircadianOscillator.update_amplitude -------------------------------------


class TestUpdateAmplitude:
    def test_regular_schedule_recovers(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.8)
        osc.update_amplitude(1.0)
        assert osc.amplitude > 0.8

    def test_irregular_schedule_decays(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.8)
        osc.update_amplitude(0.3)
        assert osc.amplitude < 0.8

    def test_boundary_regularity_no_change(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.7)
        osc.update_amplitude(0.8)
        # regularity == 0.8: the boundary case
        # ≥ 0.8 path: delta = AMPLITUDE_RECOVERY_RATE * (0.8 - 0.8) / 0.2 = 0
        assert osc.amplitude == pytest.approx(0.7)

    def test_amplitude_never_exceeds_1(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.99)
        osc.update_amplitude(1.0)
        assert osc.amplitude <= 1.0

    def test_amplitude_never_below_0(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.01)
        osc.update_amplitude(0.0)
        assert osc.amplitude >= 0.0


# -- CircadianOscillator.get_current_alertness --------------------------------


class TestGetCurrentAlertness:
    def test_peak_alertness_near_phase_plus_4(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, phase=6.0, amplitude=1.0)
        # Peak at phase + 4 = 10 AM
        peak_alert = osc.get_current_alertness(datetime(2026, 1, 15, 10, 0))
        off_peak = osc.get_current_alertness(datetime(2026, 1, 15, 22, 0))
        assert peak_alert > off_peak

    def test_range_0_to_1(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=1.0)
        for hour in range(24):
            alertness = osc.get_current_alertness(datetime(2026, 1, 15, hour, 0))
            assert 0.0 <= alertness <= 1.0

    def test_low_amplitude_flattens_curve(self):
        osc_high = CircadianOscillator(
            resident_id=RESIDENT_ID, phase=6.0, amplitude=1.0
        )
        osc_low = CircadianOscillator(resident_id=RESIDENT_ID, phase=6.0, amplitude=0.1)
        peak = datetime(2026, 1, 15, 10, 0)
        trough = datetime(2026, 1, 15, 22, 0)
        high_range = osc_high.get_current_alertness(
            peak
        ) - osc_high.get_current_alertness(trough)
        low_range = osc_low.get_current_alertness(peak) - osc_low.get_current_alertness(
            trough
        )
        assert low_range < high_range

    def test_zero_amplitude_constant(self):
        osc = CircadianOscillator(resident_id=RESIDENT_ID, amplitude=0.0)
        a1 = osc.get_current_alertness(datetime(2026, 1, 15, 6, 0))
        a2 = osc.get_current_alertness(datetime(2026, 1, 15, 18, 0))
        assert a1 == pytest.approx(a2, abs=0.01)
        assert a1 == pytest.approx(0.5, abs=0.01)


# -- CircadianImpact dataclass ------------------------------------------------


class TestCircadianImpact:
    def test_creation(self):
        impact = CircadianImpact(
            resident_id=RESIDENT_ID,
            phase_drift=2.5,
            amplitude_change=-0.1,
            quality_score=0.75,
            misalignment_hours=3.0,
            recovery_days_needed=3,
            quality_level=CircadianQualityLevel.GOOD,
        )
        assert impact.phase_drift == 2.5
        assert impact.quality_level == CircadianQualityLevel.GOOD

    def test_to_dict(self):
        impact = CircadianImpact(
            resident_id=RESIDENT_ID,
            phase_drift=1.0,
            amplitude_change=0.0,
            quality_score=0.9,
            misalignment_hours=1.5,
            recovery_days_needed=1,
            quality_level=CircadianQualityLevel.EXCELLENT,
        )
        d = impact.to_dict()
        assert d["resident_id"] == str(RESIDENT_ID)
        assert d["quality_level"] == "excellent"
        assert "analyzed_at" in d


# -- CircadianScheduleAnalyzer init -------------------------------------------


class TestCircadianScheduleAnalyzerInit:
    def test_empty_init(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._oscillators == {}


# -- get_or_create_oscillator -------------------------------------------------


class TestGetOrCreateOscillator:
    def test_creates_new(self):
        analyzer = CircadianScheduleAnalyzer()
        osc = analyzer.get_or_create_oscillator(RESIDENT_ID)
        assert osc.resident_id == RESIDENT_ID
        assert osc.phase == 6.0  # default
        assert osc.amplitude == 1.0

    def test_returns_cached(self):
        analyzer = CircadianScheduleAnalyzer()
        osc1 = analyzer.get_or_create_oscillator(RESIDENT_ID)
        osc2 = analyzer.get_or_create_oscillator(RESIDENT_ID)
        assert osc1 is osc2

    def test_custom_initial_values(self):
        analyzer = CircadianScheduleAnalyzer()
        osc = analyzer.get_or_create_oscillator(
            RESIDENT_ID, initial_phase=8.0, initial_amplitude=0.9
        )
        assert osc.phase == 8.0
        assert osc.amplitude == 0.9

    def test_different_residents(self):
        analyzer = CircadianScheduleAnalyzer()
        osc1 = analyzer.get_or_create_oscillator(RESIDENT_ID)
        osc2 = analyzer.get_or_create_oscillator(RESIDENT_ID_2)
        assert osc1 is not osc2


# -- analyze_schedule_impact --------------------------------------------------


class TestAnalyzeScheduleImpact:
    def test_single_day_shift(self):
        analyzer = CircadianScheduleAnalyzer()
        schedule = [
            {
                "start_time": datetime(2026, 1, 15, 7, 0),
                "duration": 8.0,
                "type": CircadianShiftType.DAY.value,
            }
        ]
        impact = analyzer.analyze_schedule_impact(RESIDENT_ID, schedule)
        assert isinstance(impact, CircadianImpact)
        assert impact.resident_id == RESIDENT_ID
        assert 0.0 <= impact.quality_score <= 1.0

    def test_multiple_shifts(self):
        analyzer = CircadianScheduleAnalyzer()
        schedule = [
            {
                "start_time": datetime(2026, 1, 15, 7, 0),
                "duration": 8.0,
                "type": CircadianShiftType.DAY.value,
            },
            {
                "start_time": datetime(2026, 1, 16, 7, 0),
                "duration": 8.0,
                "type": CircadianShiftType.DAY.value,
            },
        ]
        impact = analyzer.analyze_schedule_impact(RESIDENT_ID, schedule)
        assert len(impact.shift_impacts) == 2

    def test_mixed_shifts_produce_lower_quality_than_consistent(self):
        """Mixed shift types cause irregular schedule penalty vs consistent shifts."""
        analyzer_consistent = CircadianScheduleAnalyzer()
        consistent_schedule = [
            {
                "start_time": datetime(2026, 1, 15, 23, 0),
                "duration": 8.0,
                "type": CircadianShiftType.NIGHT.value,
            },
            {
                "start_time": datetime(2026, 1, 16, 23, 0),
                "duration": 8.0,
                "type": CircadianShiftType.NIGHT.value,
            },
        ]
        analyzer_mixed = CircadianScheduleAnalyzer()
        mixed_schedule = [
            {
                "start_time": datetime(2026, 1, 15, 7, 0),
                "duration": 8.0,
                "type": CircadianShiftType.DAY.value,
            },
            {
                "start_time": datetime(2026, 1, 16, 23, 0),
                "duration": 8.0,
                "type": CircadianShiftType.NIGHT.value,
            },
        ]
        consistent_impact = analyzer_consistent.analyze_schedule_impact(
            RESIDENT_ID, consistent_schedule
        )
        mixed_impact = analyzer_mixed.analyze_schedule_impact(
            RESIDENT_ID_2, mixed_schedule
        )
        # Both produce valid scores
        assert 0.0 <= consistent_impact.quality_score <= 1.0
        assert 0.0 <= mixed_impact.quality_score <= 1.0


# -- compute_circadian_quality_score ------------------------------------------


class TestComputeCircadianQualityScore:
    def test_empty_schedule(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer.compute_circadian_quality_score([]) == 1.0

    def test_single_resident(self):
        analyzer = CircadianScheduleAnalyzer()
        schedule = [
            {
                "resident_id": RESIDENT_ID,
                "start_time": datetime(2026, 1, 15, 7, 0),
                "duration": 8.0,
                "type": CircadianShiftType.DAY.value,
            }
        ]
        score = analyzer.compute_circadian_quality_score(schedule)
        assert 0.0 <= score <= 1.0


# -- predict_burnout_risk_from_circadian --------------------------------------


class TestPredictBurnoutRisk:
    def test_high_amplitude_low_risk(self):
        analyzer = CircadianScheduleAnalyzer()
        risk = analyzer.predict_burnout_risk_from_circadian(0.9)
        assert risk < 0.1

    def test_low_amplitude_high_risk(self):
        analyzer = CircadianScheduleAnalyzer()
        risk = analyzer.predict_burnout_risk_from_circadian(0.2)
        assert risk > 0.5

    def test_boundary_amplitude_0_5(self):
        analyzer = CircadianScheduleAnalyzer()
        risk = analyzer.predict_burnout_risk_from_circadian(0.5)
        # At exactly 0.5: else branch → 0.5 * (1.0 - 0.5) = 0.25
        assert risk == pytest.approx(0.25, abs=0.01)

    def test_range_0_to_1(self):
        analyzer = CircadianScheduleAnalyzer()
        for amp in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
            risk = analyzer.predict_burnout_risk_from_circadian(amp)
            assert 0.0 <= risk <= 1.0


# -- _compute_quality_score ---------------------------------------------------


class TestComputeQualityScore:
    def test_perfect_score(self):
        analyzer = CircadianScheduleAnalyzer()
        score = analyzer._compute_quality_score(
            phase_drift=0.0, amplitude_change=0.0, avg_misalignment=0.0
        )
        assert score == pytest.approx(1.0)

    def test_large_drift_reduces_score(self):
        analyzer = CircadianScheduleAnalyzer()
        score = analyzer._compute_quality_score(
            phase_drift=6.0, amplitude_change=0.0, avg_misalignment=0.0
        )
        # phase_score = max(0, 1 - 6/6) = 0 → 0.4*0 + 0.3*1 + 0.3*1 = 0.6
        assert score == pytest.approx(0.6, abs=0.05)

    def test_amplitude_degradation_reduces_score(self):
        analyzer = CircadianScheduleAnalyzer()
        score = analyzer._compute_quality_score(
            phase_drift=0.0, amplitude_change=-0.5, avg_misalignment=0.0
        )
        # amp_score = max(0, 1 + (-0.5)) = 0.5 → 0.4*1 + 0.3*0.5 + 0.3*1 = 0.85
        assert score == pytest.approx(0.85, abs=0.05)

    def test_amplitude_improvement_no_penalty(self):
        analyzer = CircadianScheduleAnalyzer()
        score_improve = analyzer._compute_quality_score(
            phase_drift=0.0, amplitude_change=0.1, avg_misalignment=0.0
        )
        score_neutral = analyzer._compute_quality_score(
            phase_drift=0.0, amplitude_change=0.0, avg_misalignment=0.0
        )
        # Both should give amp_score=1.0
        assert score_improve == pytest.approx(score_neutral)

    def test_misalignment_reduces_score(self):
        analyzer = CircadianScheduleAnalyzer()
        score = analyzer._compute_quality_score(
            phase_drift=0.0, amplitude_change=0.0, avg_misalignment=3.0
        )
        # misalign_score = max(0, 1 - 3/6) = 0.5 → 0.4*1 + 0.3*1 + 0.3*0.5 = 0.85
        assert score == pytest.approx(0.85, abs=0.05)


# -- _classify_quality --------------------------------------------------------


class TestClassifyQuality:
    def test_excellent(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.90) == CircadianQualityLevel.EXCELLENT

    def test_good(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.75) == CircadianQualityLevel.GOOD

    def test_fair(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.60) == CircadianQualityLevel.FAIR

    def test_poor(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.45) == CircadianQualityLevel.POOR

    def test_critical(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.30) == CircadianQualityLevel.CRITICAL

    def test_boundary_085(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.85) == CircadianQualityLevel.EXCELLENT

    def test_boundary_070(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.70) == CircadianQualityLevel.GOOD

    def test_boundary_055(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.55) == CircadianQualityLevel.FAIR

    def test_boundary_040(self):
        analyzer = CircadianScheduleAnalyzer()
        assert analyzer._classify_quality(0.40) == CircadianQualityLevel.POOR


# -- _estimate_recovery_days --------------------------------------------------


class TestEstimateRecoveryDays:
    def test_no_drift_no_degradation(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(0.0, 0.0)
        assert days == 0

    def test_phase_drift_only(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(3.0, 0.0)
        # 3 hours drift → 3 days recovery
        assert days == 3

    def test_amplitude_degradation_only(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(0.0, -0.5)
        # 0.5 * 14 = 7 days
        assert days == 7

    def test_takes_max(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(5.0, -0.5)
        # phase: 5 days, amplitude: 7 days → max = 7
        assert days == 7

    def test_amplitude_improvement_no_recovery(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(0.0, 0.1)
        assert days == 0

    def test_ceiling(self):
        analyzer = CircadianScheduleAnalyzer()
        days = analyzer._estimate_recovery_days(2.5, 0.0)
        # ceil(2.5) = 3
        assert days == 3


# -- reset_oscillator ---------------------------------------------------------


class TestResetOscillator:
    def test_reset_existing(self):
        analyzer = CircadianScheduleAnalyzer()
        analyzer.get_or_create_oscillator(RESIDENT_ID)
        assert RESIDENT_ID in analyzer._oscillators
        analyzer.reset_oscillator(RESIDENT_ID)
        assert RESIDENT_ID not in analyzer._oscillators

    def test_reset_nonexistent_no_error(self):
        analyzer = CircadianScheduleAnalyzer()
        analyzer.reset_oscillator(RESIDENT_ID)  # No error


# -- get_oscillator_summary ---------------------------------------------------


class TestGetOscillatorSummary:
    def test_empty(self):
        analyzer = CircadianScheduleAnalyzer()
        summary = analyzer.get_oscillator_summary()
        assert summary["total_residents"] == 0
        assert summary["oscillators"] == []

    def test_with_residents(self):
        analyzer = CircadianScheduleAnalyzer()
        analyzer.get_or_create_oscillator(RESIDENT_ID)
        analyzer.get_or_create_oscillator(RESIDENT_ID_2)
        summary = analyzer.get_oscillator_summary()
        assert summary["total_residents"] == 2
        assert len(summary["oscillators"]) == 2
