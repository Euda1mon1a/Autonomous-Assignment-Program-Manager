"""Tests for Fatigue Risk Management System (FRMS).

Tests cover:
- Samn-Perelli fatigue scale
- Sleep debt accumulation
- Alertness prediction
- Hazard threshold detection
- FRMS service integration
- ACGME compliance validation
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.resilience.frms.samn_perelli import (
    SamnPerelliLevel,
    SamnPerelliAssessment,
    assess_fatigue_level,
    is_safe_for_duty,
    estimate_level_from_factors,
    get_all_levels,
    DUTY_THRESHOLDS,
)
from app.resilience.frms.sleep_debt import (
    SleepDebtModel,
    SleepDebtState,
    SleepOpportunity,
    CircadianPhase,
    get_circadian_phases_info,
)
from app.resilience.frms.alertness_engine import (
    AlertnessPredictor,
    AlertnessPrediction,
    ShiftPattern,
    ShiftType,
)
from app.resilience.frms.hazard_thresholds import (
    HazardLevel,
    HazardThresholdEngine,
    FatigueHazard,
    TriggerType,
    MitigationType,
    get_hazard_level_info,
    get_mitigation_info,
)
from app.resilience.frms.frms_service import (
    FRMSService,
    FatigueProfile,
)


class TestSamnPerelliScale:
    """Tests for Samn-Perelli fatigue scale."""

    def test_all_levels_defined(self):
        """Test that all 7 levels are defined."""
        levels = get_all_levels()
        assert len(levels) == 7
        for i, level in enumerate(levels, start=1):
            assert level["level"] == i

    def test_assess_fatigue_level_valid(self):
        """Test valid fatigue level assessment."""
        resident_id = uuid4()
        assessment = assess_fatigue_level(
            level=4,
            resident_id=resident_id,
            is_self_reported=True,
            notes="Feeling a bit tired",
        )

        assert assessment.resident_id == resident_id
        assert assessment.level == SamnPerelliLevel.A_LITTLE_TIRED
        assert assessment.is_self_reported is True
        assert assessment.safe_for_duty is True
        assert "critical_care" not in (assessment.duty_restrictions or [])

    def test_assess_fatigue_level_invalid(self):
        """Test invalid fatigue level raises error."""
        with pytest.raises(ValueError, match="must be 1-7"):
            assess_fatigue_level(level=8, resident_id=uuid4())

        with pytest.raises(ValueError, match="must be 1-7"):
            assess_fatigue_level(level=0, resident_id=uuid4())

    def test_duty_restrictions_by_level(self):
        """Test that higher levels restrict more duties."""
        resident_id = uuid4()

        # Level 3 (Okay) - should be safe for all duties
        assessment_3 = assess_fatigue_level(level=3, resident_id=resident_id)
        assert assessment_3.duty_restrictions is None or len(assessment_3.duty_restrictions) == 0

        # Level 5 (Moderately tired) - should restrict some duties
        assessment_5 = assess_fatigue_level(level=5, resident_id=resident_id)
        assert "procedures" in (assessment_5.duty_restrictions or [])
        assert "critical_care" in (assessment_5.duty_restrictions or [])

        # Level 7 (Exhausted) - should restrict most duties
        assessment_7 = assess_fatigue_level(level=7, resident_id=resident_id)
        assert assessment_7.safe_for_duty is False
        assert len(assessment_7.duty_restrictions or []) >= 4

    def test_is_safe_for_duty(self):
        """Test duty safety checking."""
        # Level 3 should be safe for procedures
        safe, reason = is_safe_for_duty(SamnPerelliLevel.OKAY, "procedures")
        assert safe is True

        # Level 5 should not be safe for procedures
        safe, reason = is_safe_for_duty(SamnPerelliLevel.MODERATELY_TIRED, "procedures")
        assert safe is False
        assert "exceeds" in reason

    def test_estimate_level_from_factors(self):
        """Test level estimation from objective factors."""
        # Well-rested scenario
        level = estimate_level_from_factors(
            hours_awake=8.0,
            hours_worked_24h=6.0,
            consecutive_night_shifts=0,
            time_of_day_hour=10,
            prior_sleep_hours=8.0,
        )
        assert level.value <= 3  # Should be alert

        # Fatigued scenario
        level = estimate_level_from_factors(
            hours_awake=20.0,
            hours_worked_24h=14.0,
            consecutive_night_shifts=3,
            time_of_day_hour=4,  # Circadian nadir
            prior_sleep_hours=4.0,
        )
        assert level.value >= 5  # Should be tired

    def test_assessment_to_dict(self):
        """Test assessment serialization."""
        assessment = assess_fatigue_level(level=4, resident_id=uuid4())
        data = assessment.to_dict()

        assert "resident_id" in data
        assert "level" in data
        assert "description" in data
        assert "safe_for_duty" in data


class TestSleepDebtModel:
    """Tests for sleep debt accumulation model."""

    def test_baseline_sleep_need(self):
        """Test baseline sleep configuration."""
        model = SleepDebtModel()
        assert model.baseline_sleep_need == 7.5

        model_custom = SleepDebtModel(baseline_sleep_need=8.0)
        assert model_custom.baseline_sleep_need == 8.0

    def test_calculate_daily_debt_adequate_sleep(self):
        """Test no debt accumulation with adequate sleep."""
        model = SleepDebtModel()
        now = datetime.now()

        sleep = SleepOpportunity(
            start_time=now - timedelta(hours=8),
            end_time=now,
            quality_factor=1.0,
        )

        debt = model.calculate_daily_debt([sleep])
        assert debt < 0  # Net recovery (slept more than baseline)

    def test_calculate_daily_debt_inadequate_sleep(self):
        """Test debt accumulation with inadequate sleep."""
        model = SleepDebtModel()
        now = datetime.now()

        sleep = SleepOpportunity(
            start_time=now - timedelta(hours=5),
            end_time=now,
            quality_factor=1.0,
        )

        debt = model.calculate_daily_debt([sleep])
        assert debt > 0  # Net debt (slept less than baseline)
        assert debt == pytest.approx(2.5, rel=0.1)  # 7.5 - 5 = 2.5

    def test_effective_sleep_hours(self):
        """Test effective sleep calculation with quality factors."""
        now = datetime.now()

        # Perfect sleep
        sleep_perfect = SleepOpportunity(
            start_time=now - timedelta(hours=8),
            end_time=now,
            quality_factor=1.0,
            circadian_aligned=True,
            interruptions=0,
        )
        assert sleep_perfect.effective_sleep_hours == 8.0

        # Poor quality sleep
        sleep_poor = SleepOpportunity(
            start_time=now - timedelta(hours=8),
            end_time=now,
            quality_factor=0.7,
            circadian_aligned=False,
            interruptions=2,
        )
        # 8.0 * 0.7 * 0.8 * 0.9 = 4.032
        assert sleep_poor.effective_sleep_hours < 5.0

    def test_circadian_phase_detection(self):
        """Test circadian phase identification."""
        model = SleepDebtModel()

        # 4 AM should be nadir
        nadir_time = datetime.now().replace(hour=4, minute=0)
        assert model.get_circadian_phase(nadir_time) == CircadianPhase.NADIR

        # 10 AM should be morning peak
        peak_time = datetime.now().replace(hour=10, minute=0)
        assert model.get_circadian_phase(peak_time) == CircadianPhase.MORNING_PEAK

    def test_circadian_multiplier(self):
        """Test circadian alertness multipliers."""
        model = SleepDebtModel()

        # Nadir should have lowest multiplier
        nadir_time = datetime.now().replace(hour=4, minute=0)
        nadir_mult = model.get_circadian_multiplier(nadir_time)
        assert nadir_mult == 0.6

        # Peak should have highest multiplier
        peak_time = datetime.now().replace(hour=10, minute=0)
        peak_mult = model.get_circadian_multiplier(peak_time)
        assert peak_mult == 1.0

    def test_sleep_debt_trajectory(self):
        """Test sleep debt trajectory prediction."""
        model = SleepDebtModel()
        resident_id = uuid4()

        # Simulate poor sleep week
        trajectory = model.predict_debt_trajectory(
            resident_id=resident_id,
            planned_sleep_hours=[5.0, 5.5, 6.0, 5.0, 5.5, 9.0, 9.0],
            start_debt=0.0,
        )

        assert len(trajectory) == 7
        # Debt should increase then decrease
        max_debt_day = max(trajectory, key=lambda t: t["cumulative_debt"])
        assert max_debt_day["day"] <= 5  # Peak before recovery days

    def test_impairment_equivalent_bac(self):
        """Test cognitive impairment BAC equivalence."""
        model = SleepDebtModel()

        # 10 hours debt should be ~0.05 BAC
        state = model.update_cumulative_debt(uuid4(), 10.0, natural_recovery=False)
        assert state.impairment_equivalent_bac == pytest.approx(0.05, rel=0.1)


class TestAlertnessPrediction:
    """Tests for alertness prediction engine."""

    def test_predict_alertness_rested(self):
        """Test alertness prediction for well-rested resident."""
        predictor = AlertnessPredictor()
        resident_id = uuid4()
        now = datetime.now().replace(hour=10)  # Morning peak

        # Recent good sleep
        sleep = SleepOpportunity(
            start_time=now - timedelta(hours=10),
            end_time=now - timedelta(hours=2),
            quality_factor=1.0,
        )

        prediction = predictor.predict_alertness(
            resident_id=resident_id,
            target_time=now,
            recent_shifts=[],
            sleep_history=[sleep],
            current_sleep_debt=0.0,
        )

        assert prediction.alertness_score >= 0.7
        assert prediction.risk_level in ["minimal", "low"]

    def test_predict_alertness_fatigued(self):
        """Test alertness prediction for fatigued resident."""
        predictor = AlertnessPredictor()
        resident_id = uuid4()
        now = datetime.now().replace(hour=4)  # Circadian nadir

        # Long awake period
        sleep = SleepOpportunity(
            start_time=now - timedelta(hours=24),
            end_time=now - timedelta(hours=20),
            quality_factor=0.6,
        )

        prediction = predictor.predict_alertness(
            resident_id=resident_id,
            target_time=now,
            recent_shifts=[],
            sleep_history=[sleep],
            current_sleep_debt=15.0,
        )

        assert prediction.alertness_score < 0.5
        assert prediction.risk_level in ["moderate", "high"]
        assert len(prediction.recommendations) > 0

    def test_shift_trajectory_prediction(self):
        """Test trajectory prediction across multiple shifts."""
        predictor = AlertnessPredictor()
        resident_id = uuid4()
        now = datetime.now()

        shifts = [
            ShiftPattern(
                shift_type=ShiftType.DAY,
                start_time=now,
                end_time=now + timedelta(hours=10),
                prior_sleep_hours=7.5,
            ),
            ShiftPattern(
                shift_type=ShiftType.NIGHT,
                start_time=now + timedelta(days=1, hours=19),
                end_time=now + timedelta(days=2, hours=7),
                prior_sleep_hours=6.0,
            ),
            ShiftPattern(
                shift_type=ShiftType.NIGHT,
                start_time=now + timedelta(days=2, hours=19),
                end_time=now + timedelta(days=3, hours=7),
                prior_sleep_hours=5.0,
            ),
        ]

        trajectory = predictor.predict_shift_trajectory(
            resident_id=resident_id,
            upcoming_shifts=shifts,
            current_sleep_debt=0.0,
        )

        assert len(trajectory) == 3
        # Alertness should decrease across night shifts
        assert trajectory[0].alertness_score > trajectory[2].alertness_score

    def test_identify_high_risk_windows(self):
        """Test identification of high-risk periods."""
        predictor = AlertnessPredictor()

        # Create trajectory with varying alertness
        predictions = [
            AlertnessPrediction(
                resident_id=uuid4(),
                prediction_time=datetime.now(),
                alertness_score=0.8,
                samn_perelli_estimate=SamnPerelliLevel.VERY_LIVELY,
                circadian_phase=CircadianPhase.MORNING_PEAK,
                hours_awake=8,
                sleep_debt=0,
                performance_capacity=80,
                risk_level="low",
            ),
            AlertnessPrediction(
                resident_id=uuid4(),
                prediction_time=datetime.now() + timedelta(hours=12),
                alertness_score=0.4,
                samn_perelli_estimate=SamnPerelliLevel.EXTREMELY_TIRED,
                circadian_phase=CircadianPhase.NADIR,
                hours_awake=20,
                sleep_debt=5,
                performance_capacity=40,
                risk_level="high",
            ),
        ]

        high_risk = predictor.identify_high_risk_windows(predictions, threshold=0.5)
        assert len(high_risk) == 1
        assert high_risk[0]["alertness"] == 0.4


class TestHazardThresholds:
    """Tests for hazard threshold detection."""

    def test_hazard_level_info(self):
        """Test hazard level reference data."""
        levels = get_hazard_level_info()
        assert len(levels) == 5  # GREEN through BLACK

    def test_mitigation_info(self):
        """Test mitigation type reference data."""
        mitigations = get_mitigation_info()
        assert len(mitigations) >= 5

    def test_evaluate_green_hazard(self):
        """Test GREEN hazard (normal operations)."""
        engine = HazardThresholdEngine()
        resident_id = uuid4()

        hazard = engine.evaluate_hazard(
            resident_id=resident_id,
            alertness=0.85,
            sleep_debt=2.0,
            hours_awake=10.0,
            samn_perelli=SamnPerelliLevel.OKAY,
        )

        assert hazard.hazard_level == HazardLevel.GREEN
        assert len(hazard.triggers) == 0
        assert len(hazard.required_mitigations) == 0

    def test_evaluate_yellow_hazard(self):
        """Test YELLOW hazard (advisory)."""
        engine = HazardThresholdEngine()
        resident_id = uuid4()

        hazard = engine.evaluate_hazard(
            resident_id=resident_id,
            alertness=0.6,
            sleep_debt=8.0,
            hours_awake=16.0,
            samn_perelli=SamnPerelliLevel.MODERATELY_TIRED,
        )

        assert hazard.hazard_level == HazardLevel.YELLOW
        assert len(hazard.triggers) > 0
        assert MitigationType.MONITORING.value in [m.value for m in hazard.required_mitigations]

    def test_evaluate_red_hazard(self):
        """Test RED hazard (warning)."""
        engine = HazardThresholdEngine()
        resident_id = uuid4()

        hazard = engine.evaluate_hazard(
            resident_id=resident_id,
            alertness=0.35,
            sleep_debt=18.0,
            hours_awake=24.0,
            samn_perelli=SamnPerelliLevel.EXHAUSTED,
        )

        assert hazard.hazard_level == HazardLevel.RED
        assert hazard.is_critical is True
        assert hazard.requires_schedule_change is True

    def test_acgme_risk_detection(self):
        """Test ACGME violation risk detection."""
        engine = HazardThresholdEngine()
        resident_id = uuid4()

        # Approaching weekly limit
        hazard = engine.evaluate_hazard(
            resident_id=resident_id,
            alertness=0.7,
            hours_worked_week=75.0,  # 90%+ of 80-hour limit
        )

        assert hazard.acgme_risk is True
        assert TriggerType.ACGME_APPROACHING in hazard.triggers

    def test_batch_evaluate(self):
        """Test batch hazard evaluation."""
        engine = HazardThresholdEngine()

        residents = [
            {"resident_id": uuid4(), "alertness": 0.8, "sleep_debt": 2.0},
            {"resident_id": uuid4(), "alertness": 0.5, "sleep_debt": 12.0},
            {"resident_id": uuid4(), "alertness": 0.3, "sleep_debt": 20.0},
        ]

        hazards = engine.batch_evaluate(residents)
        assert len(hazards) == 3

        summary = engine.get_level_summary(hazards)
        assert summary["total_residents"] == 3
        assert summary["critical_count"] >= 1


class TestFRMSService:
    """Tests for FRMS service integration."""

    def test_calculate_fatigue_score(self):
        """Test synchronous fatigue score calculation."""
        service = FRMSService()

        result = service.calculate_fatigue_score(
            hours_awake=12.0,
            hours_worked_24h=8.0,
            consecutive_night_shifts=0,
            time_of_day_hour=14,
            prior_sleep_hours=7.5,
        )

        assert "samn_perelli_level" in result
        assert "alertness_score" in result
        assert "circadian_phase" in result
        assert result["samn_perelli_level"] <= 4  # Should be reasonably alert

    def test_export_temporal_constraints(self):
        """Test temporal constraint export for holographic hub."""
        service = FRMSService()
        export = service.export_temporal_constraints()

        assert export["version"] == "1.0"
        assert "circadian_rhythm" in export
        assert "sleep_homeostasis" in export
        assert "samn_perelli_scale" in export
        assert "hazard_thresholds" in export
        assert "acgme_integration" in export
        assert "scheduling_constraints" in export

        # Verify ACGME integration
        assert export["acgme_integration"]["weekly_limit"] == 80.0

        # Verify scheduling constraints structure
        assert "hard_constraints" in export["scheduling_constraints"]
        assert "soft_constraints" in export["scheduling_constraints"]


class TestACGMEFRMSIntegration:
    """Tests proving FRMS prevents ACGME violations."""

    def test_fatigue_predicts_acgme_risk(self):
        """Test that high fatigue correlates with ACGME risk."""
        engine = HazardThresholdEngine()

        # High fatigue scenario
        hazard = engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=0.4,
            sleep_debt=15.0,
            hours_worked_week=70.0,  # Not yet at 80, but high fatigue
        )

        # Even before ACGME limit, fatigue indicates risk
        assert hazard.hazard_level in [HazardLevel.ORANGE, HazardLevel.RED]

    def test_frms_catches_violations_early(self):
        """Test that FRMS detects problems before ACGME thresholds."""
        service = FRMSService()

        # Simulate resident approaching problems
        score = service.calculate_fatigue_score(
            hours_awake=18.0,
            hours_worked_24h=12.0,
            consecutive_night_shifts=4,
            time_of_day_hour=4,  # Nadir
            prior_sleep_hours=5.0,
        )

        # FRMS should flag this as concerning
        assert score["samn_perelli_level"] >= 5
        assert score["alertness_score"] < 0.5

    def test_circadian_constraint_validates_acgme(self):
        """Test that circadian constraints complement ACGME rules."""
        service = FRMSService()
        export = service.export_temporal_constraints()

        # Verify circadian constraints exist
        hard_constraints = export["scheduling_constraints"]["hard_constraints"]
        nadir_constraint = next(
            (c for c in hard_constraints if "nadir" in c["name"]),
            None
        )
        assert nadir_constraint is not None
        assert "2-6 AM" in nadir_constraint["description"]


class TestTemporalDynamics:
    """Tests for temporal dynamics documentation support."""

    def test_circadian_curve_generation(self):
        """Test circadian alertness curve generation."""
        model = SleepDebtModel()
        now = datetime.now().replace(hour=0)

        curve = model.calculate_circadian_curve(now, 24)

        assert len(curve) == 24
        # Find nadir and peak
        nadir = min(curve, key=lambda p: p["alertness_multiplier"])
        peak = max(curve, key=lambda p: p["alertness_multiplier"])

        assert nadir["phase"] == "nadir"
        assert peak["phase"] == "morning_peak"
        assert nadir["alertness_multiplier"] < peak["alertness_multiplier"]

    def test_debt_severity_classification(self):
        """Test sleep debt severity classification."""
        model = SleepDebtModel()

        # Test classification at different debt levels
        assert model._classify_debt_severity(1.0) == "none"
        assert model._classify_debt_severity(3.0) == "mild"
        assert model._classify_debt_severity(7.0) == "moderate"
        assert model._classify_debt_severity(12.0) == "severe"
        assert model._classify_debt_severity(25.0) == "critical"

    def test_recovery_time_estimation(self):
        """Test recovery time estimation."""
        model = SleepDebtModel()

        # 10 hours debt with 9 hours sleep (1.5 hour extra)
        nights = model.estimate_recovery_time(10.0, recovery_sleep_per_night=9.0)

        # Should take ~10 nights (10 / (1.5 / 1.5))
        assert nights >= 8
        assert nights <= 15

    def test_circadian_phases_complete(self):
        """Test all circadian phases are documented."""
        phases = get_circadian_phases_info()

        assert len(phases) == 7
        phase_names = [p["phase"] for p in phases]
        assert "nadir" in phase_names
        assert "morning_peak" in phase_names
        assert "post_lunch" in phase_names
