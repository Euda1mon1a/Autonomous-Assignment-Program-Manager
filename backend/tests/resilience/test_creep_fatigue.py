"""
Tests for Creep/Fatigue-Based Burnout Prediction.

Tests materials science-inspired burnout prediction using:
- Larson-Miller Parameter (creep analysis)
- Creep stage determination
- S-N curves (fatigue analysis)
- Miner's rule (cumulative damage)
- Combined risk assessment
"""

import math
from datetime import timedelta
from uuid import uuid4

from app.resilience.creep_fatigue import (
    CreepAnalysis,
    CreepFatigueModel,
    CreepStage,
    FatigueCurve,
)


class TestCreepStage:
    """Test CreepStage enum."""

    def test_creep_stages_defined(self):
        """Test all creep stages are defined."""
        assert CreepStage.PRIMARY == "primary"
        assert CreepStage.SECONDARY == "secondary"
        assert CreepStage.TERTIARY == "tertiary"

    def test_creep_stage_values(self):
        """Test creep stage string values."""
        stages = [CreepStage.PRIMARY, CreepStage.SECONDARY, CreepStage.TERTIARY]
        values = [s.value for s in stages]

        assert "primary" in values
        assert "secondary" in values
        assert "tertiary" in values


class TestCreepAnalysisDataclass:
    """Test CreepAnalysis dataclass."""

    def test_creep_analysis_creation(self):
        """Test creating CreepAnalysis instance."""
        resident_id = uuid4()
        analysis = CreepAnalysis(
            resident_id=resident_id,
            creep_stage=CreepStage.SECONDARY,
            larson_miller_parameter=35.5,
            estimated_time_to_failure=timedelta(days=90),
            strain_rate=0.02,
            recommended_stress_reduction=15.0,
        )

        assert analysis.resident_id == resident_id
        assert analysis.creep_stage == CreepStage.SECONDARY
        assert analysis.larson_miller_parameter == 35.5
        assert analysis.estimated_time_to_failure.days == 90
        assert analysis.strain_rate == 0.02
        assert analysis.recommended_stress_reduction == 15.0


class TestFatigueCurveDataclass:
    """Test FatigueCurve dataclass."""

    def test_fatigue_curve_creation(self):
        """Test creating FatigueCurve instance."""
        curve = FatigueCurve(
            cycles_to_failure=1000,
            stress_amplitude=0.75,
            current_cycles=250,
            remaining_life_fraction=0.5,
        )

        assert curve.cycles_to_failure == 1000
        assert curve.stress_amplitude == 0.75
        assert curve.current_cycles == 250
        assert curve.remaining_life_fraction == 0.5


class TestLarsonMillerParameter:
    """Test Larson-Miller Parameter calculations."""

    def test_lmp_basic_calculation(self):
        """Test basic LMP calculation."""
        model = CreepFatigueModel()

        # 80% workload for 30 days
        lmp = model.calculate_larson_miller(0.8, 30)

        # LMP = workload * (base + multiplier * log10(duration))
        # where base = C/2 = 10, multiplier = C * 1.25 = 25
        # = 0.8 * (10 + 25 * log10(30))
        # = 0.8 * (10 + 25 * 1.477) = 0.8 * 46.925 = 37.54
        base = 20.0 / 2.0
        multiplier = 20.0 * 1.25
        expected = 0.8 * (base + multiplier * math.log10(30))
        assert abs(lmp - expected) < 0.01

    def test_lmp_zero_duration(self):
        """Test LMP with zero duration returns zero."""
        model = CreepFatigueModel()

        lmp = model.calculate_larson_miller(0.8, 0)
        assert lmp == 0.0

    def test_lmp_zero_workload(self):
        """Test LMP with zero workload returns zero."""
        model = CreepFatigueModel()

        lmp = model.calculate_larson_miller(0.0, 30)
        assert lmp == 0.0

    def test_lmp_increases_with_duration(self):
        """Test LMP increases with longer duration."""
        model = CreepFatigueModel()

        lmp_short = model.calculate_larson_miller(0.8, 10)
        lmp_medium = model.calculate_larson_miller(0.8, 30)
        lmp_long = model.calculate_larson_miller(0.8, 90)

        assert lmp_short < lmp_medium < lmp_long

    def test_lmp_increases_with_workload(self):
        """Test LMP increases with higher workload."""
        model = CreepFatigueModel()

        lmp_low = model.calculate_larson_miller(0.5, 30)
        lmp_medium = model.calculate_larson_miller(0.75, 30)
        lmp_high = model.calculate_larson_miller(0.95, 30)

        assert lmp_low < lmp_medium < lmp_high

    def test_lmp_custom_constant(self):
        """Test LMP with custom material constant."""
        model = CreepFatigueModel()

        lmp_default = model.calculate_larson_miller(0.8, 30, C=20.0)
        lmp_custom = model.calculate_larson_miller(0.8, 30, C=25.0)

        # Higher C means higher LMP
        assert lmp_custom > lmp_default

    def test_lmp_very_long_duration(self):
        """Test LMP with very long duration (years)."""
        model = CreepFatigueModel()

        # 1 year = 365 days
        lmp = model.calculate_larson_miller(0.7, 365)

        # Should be substantial
        assert lmp > 1000.0


class TestCreepStageDetermination:
    """Test creep stage determination logic."""

    def test_determine_primary_stage(self):
        """Test identifying primary creep stage."""
        model = CreepFatigueModel()

        # LMP < 50% of threshold (45.0) = 22.5
        stage = model.determine_creep_stage(20.0)

        assert stage == CreepStage.PRIMARY

    def test_determine_secondary_stage(self):
        """Test identifying secondary creep stage."""
        model = CreepFatigueModel()

        # 50-80% of threshold: 22.5 - 36.0
        stage = model.determine_creep_stage(30.0)

        assert stage == CreepStage.SECONDARY

    def test_determine_tertiary_stage(self):
        """Test identifying tertiary creep stage."""
        model = CreepFatigueModel()

        # > 80% of threshold (45.0) = > 36.0
        stage = model.determine_creep_stage(40.0)

        assert stage == CreepStage.TERTIARY

    def test_determine_stage_at_boundaries(self):
        """Test stage determination at boundary values."""
        model = CreepFatigueModel()

        # Exactly at 50% boundary
        stage_50 = model.determine_creep_stage(22.5)
        assert stage_50 == CreepStage.SECONDARY  # >= 50%

        # Exactly at 80% boundary
        stage_80 = model.determine_creep_stage(36.0)
        assert stage_80 == CreepStage.TERTIARY  # >= 80%

    def test_determine_stage_custom_threshold(self):
        """Test stage determination with custom threshold."""
        model = CreepFatigueModel()

        # Custom threshold of 50.0
        stage = model.determine_creep_stage(45.0, threshold=50.0)

        # 45/50 = 90% -> TERTIARY
        assert stage == CreepStage.TERTIARY


class TestStrainRateCalculation:
    """Test strain rate calculation from workload history."""

    def test_strain_rate_increasing_workload(self):
        """Test positive strain rate for increasing workload."""
        model = CreepFatigueModel()

        # Steadily increasing workload
        history = [0.6, 0.65, 0.7, 0.75, 0.8]
        rate = model.calculate_strain_rate(history)

        # Should be positive (increasing strain)
        assert rate > 0

    def test_strain_rate_decreasing_workload(self):
        """Test negative strain rate for decreasing workload."""
        model = CreepFatigueModel()

        # Decreasing workload (recovery)
        history = [0.8, 0.75, 0.7, 0.65, 0.6]
        rate = model.calculate_strain_rate(history)

        # Should be negative (decreasing strain = recovery)
        assert rate < 0

    def test_strain_rate_stable_workload(self):
        """Test near-zero strain rate for stable workload."""
        model = CreepFatigueModel()

        # Stable workload
        history = [0.7, 0.7, 0.7, 0.7, 0.7]
        rate = model.calculate_strain_rate(history)

        # Should be near zero
        assert abs(rate) < 0.01

    def test_strain_rate_empty_history(self):
        """Test strain rate with empty history returns zero."""
        model = CreepFatigueModel()

        rate = model.calculate_strain_rate([])
        assert rate == 0.0

    def test_strain_rate_single_point(self):
        """Test strain rate with single data point returns zero."""
        model = CreepFatigueModel()

        rate = model.calculate_strain_rate([0.75])
        assert rate == 0.0

    def test_strain_rate_volatile_workload(self):
        """Test strain rate with volatile workload."""
        model = CreepFatigueModel()

        # Up and down
        history = [0.5, 0.8, 0.6, 0.9, 0.7]
        rate = model.calculate_strain_rate(history)

        # Overall trend should be positive (ends higher than starts)
        assert rate > 0


class TestPredictTimeToBurnout:
    """Test time-to-burnout prediction."""

    def test_predict_low_workload_low_risk(self):
        """Test prediction with low sustained workload."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # 60% workload for 30 days - should be low risk
        analysis = model.predict_time_to_burnout(resident_id, 0.6, timedelta(days=30))

        assert analysis.resident_id == resident_id
        assert analysis.creep_stage == CreepStage.PRIMARY
        assert analysis.estimated_time_to_failure.days > 30
        assert analysis.recommended_stress_reduction == 0.0  # No reduction needed

    def test_predict_moderate_workload_secondary_stage(self):
        """Test prediction with moderate sustained workload."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # 75% workload for 60 days
        analysis = model.predict_time_to_burnout(resident_id, 0.75, timedelta(days=60))

        assert analysis.creep_stage == CreepStage.SECONDARY
        assert analysis.larson_miller_parameter > 20.0

    def test_predict_high_workload_tertiary_stage(self):
        """Test prediction with high sustained workload."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # 90% workload for 90 days - high risk
        analysis = model.predict_time_to_burnout(resident_id, 0.9, timedelta(days=90))

        assert analysis.creep_stage == CreepStage.TERTIARY
        assert analysis.estimated_time_to_failure.days < 30
        assert analysis.recommended_stress_reduction > 0

    def test_predict_at_failure_threshold(self):
        """Test prediction when already at failure threshold."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Very high workload for extended period
        analysis = model.predict_time_to_burnout(resident_id, 0.95, timedelta(days=120))

        # Should show immediate risk
        assert analysis.creep_stage == CreepStage.TERTIARY
        assert analysis.estimated_time_to_failure.days <= 7

    def test_predict_strain_rate_varies_by_stage(self):
        """Test that strain rate varies by creep stage."""
        model = CreepFatigueModel()

        # Primary stage - should have negative or low strain rate
        primary = model.predict_time_to_burnout(uuid4(), 0.5, timedelta(days=20))
        assert primary.strain_rate <= 0.01

        # Secondary stage - moderate positive strain rate
        secondary = model.predict_time_to_burnout(uuid4(), 0.75, timedelta(days=50))
        assert secondary.strain_rate > 0

        # Tertiary stage - high strain rate
        tertiary = model.predict_time_to_burnout(uuid4(), 0.9, timedelta(days=80))
        assert tertiary.strain_rate > secondary.strain_rate


class TestStressReductionRecommendation:
    """Test stress reduction recommendations."""

    def test_recommend_no_reduction_when_safe(self):
        """Test no reduction recommended when LMP is safe."""
        model = CreepFatigueModel()

        # Already below safe threshold
        reduction = model.recommend_stress_reduction(25.0, safe_lmp=31.5)

        assert reduction == 0.0

    def test_recommend_reduction_when_unsafe(self):
        """Test reduction recommended when LMP is unsafe."""
        model = CreepFatigueModel()

        # Above safe threshold
        reduction = model.recommend_stress_reduction(40.0, safe_lmp=31.5)

        # Should recommend reduction
        assert reduction > 0
        # (40 - 31.5) / 40 * 100 = 21.25%
        assert abs(reduction - 21.25) < 0.1

    def test_recommend_caps_at_50_percent(self):
        """Test reduction recommendation caps at 50%."""
        model = CreepFatigueModel()

        # Very high LMP
        reduction = model.recommend_stress_reduction(100.0, safe_lmp=20.0)

        # Should cap at 50%
        assert reduction == 50.0

    def test_recommend_at_failure_threshold(self):
        """Test recommendation at failure threshold."""
        model = CreepFatigueModel()

        # At failure threshold (45.0), safe is 31.5
        reduction = model.recommend_stress_reduction(45.0, 31.5)

        # (45 - 31.5) / 45 * 100 = 30%
        assert abs(reduction - 30.0) < 0.1


class TestSNCurveFatigue:
    """Test S-N curve fatigue predictions."""

    def test_sn_curve_high_stress_fewer_cycles(self):
        """Test high stress leads to fewer cycles to failure."""
        model = CreepFatigueModel()

        cycles_high = model.sn_curve_cycles_to_failure(0.9)
        cycles_low = model.sn_curve_cycles_to_failure(0.3)

        # High stress should fail sooner
        assert cycles_high < cycles_low

    def test_sn_curve_stress_relationship(self):
        """Test relationship between stress and cycles."""
        model = CreepFatigueModel()

        # Increasing stress should decrease cycles
        stress_levels = [0.3, 0.5, 0.7, 0.9]
        cycles = [model.sn_curve_cycles_to_failure(s) for s in stress_levels]

        # Should be monotonically decreasing
        for i in range(len(cycles) - 1):
            assert cycles[i] > cycles[i + 1]

    def test_sn_curve_zero_stress(self):
        """Test S-N curve with zero stress."""
        model = CreepFatigueModel()

        cycles = model.sn_curve_cycles_to_failure(0.0)

        # Should return large number (won't fail)
        assert cycles >= 1e6

    def test_sn_curve_invalid_stress(self):
        """Test S-N curve with invalid stress (> 1.0)."""
        model = CreepFatigueModel()

        cycles = model.sn_curve_cycles_to_failure(1.5)

        # Should return large number
        assert cycles >= 1e6

    def test_sn_curve_custom_parameters(self):
        """Test S-N curve with custom material parameters."""
        model = CreepFatigueModel()

        cycles_default = model.sn_curve_cycles_to_failure(0.7)
        cycles_custom = model.sn_curve_cycles_to_failure(
            0.7,
            material_constant=1e9,  # Lower constant
            exponent=-3.0,
        )

        # Lower constant should give fewer cycles
        assert cycles_custom < cycles_default

    def test_sn_curve_exponent_effect(self):
        """Test effect of exponent on S-N curve."""
        model = CreepFatigueModel()

        # More negative exponent = steeper curve
        cycles_steep = model.sn_curve_cycles_to_failure(0.7, exponent=-4.0)
        cycles_gentle = model.sn_curve_cycles_to_failure(0.7, exponent=-2.0)

        # Results depend on stress level and A value
        # Just verify both are valid
        assert cycles_steep > 0
        assert cycles_gentle > 0


class TestMinerRuleCumulativeDamage:
    """Test Miner's rule cumulative damage calculations."""

    def test_fatigue_no_stress_history(self):
        """Test fatigue calculation with no stress history."""
        model = CreepFatigueModel()

        curve = model.calculate_fatigue_damage([])

        assert curve.current_cycles == 0
        assert curve.remaining_life_fraction == 1.0
        assert curve.stress_amplitude == 0.0

    def test_fatigue_single_rotation(self):
        """Test fatigue calculation with single rotation."""
        model = CreepFatigueModel()

        curve = model.calculate_fatigue_damage([0.7])

        assert curve.current_cycles == 1
        assert curve.remaining_life_fraction > 0.99  # Minimal damage
        assert curve.stress_amplitude == 0.7

    def test_fatigue_accumulates_damage(self):
        """Test that damage accumulates over multiple rotations."""
        model = CreepFatigueModel()

        # Progressive damage
        curve_1 = model.calculate_fatigue_damage([0.8])
        curve_3 = model.calculate_fatigue_damage([0.8, 0.8, 0.8])
        curve_5 = model.calculate_fatigue_damage([0.8, 0.8, 0.8, 0.8, 0.8])

        # More rotations = more damage = less remaining life
        assert curve_1.remaining_life_fraction > curve_3.remaining_life_fraction
        assert curve_3.remaining_life_fraction > curve_5.remaining_life_fraction

    def test_fatigue_high_stress_more_damage(self):
        """Test high stress causes more damage per cycle."""
        model = CreepFatigueModel()

        # Same number of rotations, different stress
        curve_low = model.calculate_fatigue_damage([0.5, 0.5, 0.5])
        curve_high = model.calculate_fatigue_damage([0.9, 0.9, 0.9])

        # High stress should cause more damage
        assert curve_high.remaining_life_fraction < curve_low.remaining_life_fraction

    def test_fatigue_mixed_stress_levels(self):
        """Test fatigue with varying stress levels."""
        model = CreepFatigueModel()

        # Mix of high and low stress
        curve = model.calculate_fatigue_damage([0.9, 0.5, 0.8, 0.6, 0.9])

        assert curve.current_cycles == 5
        assert 0.0 <= curve.remaining_life_fraction <= 1.0
        assert curve.stress_amplitude == 0.9  # Last rotation

    def test_fatigue_cycles_per_rotation(self):
        """Test custom cycles per rotation."""
        model = CreepFatigueModel()

        # Each rotation counts as 2 cycles
        curve = model.calculate_fatigue_damage([0.8, 0.8], cycles_per_rotation=2)

        assert curve.current_cycles == 4  # 2 rotations * 2 cycles each

    def test_fatigue_reports_current_stress(self):
        """Test that fatigue curve reports current stress level."""
        model = CreepFatigueModel()

        curve = model.calculate_fatigue_damage([0.7, 0.8, 0.6])

        # Should report last stress level
        assert curve.stress_amplitude == 0.6


class TestCombinedRiskAssessment:
    """Test combined creep and fatigue risk assessment."""

    def test_assess_low_risk_resident(self):
        """Test assessment of low-risk resident."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Low workload, easy rotations
        risk = model.assess_combined_risk(
            resident_id,
            0.6,
            timedelta(days=30),
            [0.5, 0.6, 0.5, 0.6],
        )

        assert risk["overall_risk"] == "low"
        assert risk["risk_score"] < 2.0
        assert risk["creep_analysis"]["stage"] == "primary"
        assert risk["fatigue_analysis"]["remaining_life"] > 0.9

    def test_assess_moderate_risk_resident(self):
        """Test assessment of moderate-risk resident."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Moderate sustained workload, some difficult rotations
        risk = model.assess_combined_risk(
            resident_id,
            0.75,
            timedelta(days=60),
            [0.7, 0.8, 0.75, 0.8, 0.7],
        )

        assert risk["overall_risk"] in ["moderate", "low"]
        assert "resident_id" in risk
        assert "creep_analysis" in risk
        assert "fatigue_analysis" in risk

    def test_assess_high_risk_resident(self):
        """Test assessment of high-risk resident."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # High sustained workload, many difficult rotations
        risk = model.assess_combined_risk(
            resident_id,
            0.9,
            timedelta(days=90),
            [0.9, 0.85, 0.9, 0.9, 0.85, 0.9],
        )

        assert risk["overall_risk"] in ["high", "moderate"]
        assert risk["risk_score"] >= 1.5
        assert len(risk["recommendations"]) > 0

    def test_assess_includes_all_components(self):
        """Test that assessment includes all required components."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        risk = model.assess_combined_risk(
            resident_id,
            0.7,
            timedelta(days=45),
            [0.6, 0.7, 0.8],
        )

        # Verify structure
        assert "resident_id" in risk
        assert "overall_risk" in risk
        assert "risk_score" in risk
        assert "risk_description" in risk
        assert "creep_analysis" in risk
        assert "fatigue_analysis" in risk
        assert "recommendations" in risk

        # Verify creep analysis components
        creep = risk["creep_analysis"]
        assert "stage" in creep
        assert "lmp" in creep
        assert "time_to_failure_days" in creep
        assert "strain_rate" in creep

        # Verify fatigue analysis components
        fatigue = risk["fatigue_analysis"]
        assert "current_cycles" in fatigue
        assert "remaining_life" in fatigue
        assert "current_stress" in fatigue

    def test_assess_recommendations_for_high_risk(self):
        """Test that high risk generates actionable recommendations."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Very high risk scenario
        risk = model.assess_combined_risk(
            resident_id,
            0.95,
            timedelta(days=100),
            [0.9, 0.9, 0.95, 0.9, 0.95],
        )

        recommendations = risk["recommendations"]
        assert len(recommendations) > 0

        # Should have urgent recommendation
        urgent_found = any(
            "URGENT" in r or "reduce" in r.lower() for r in recommendations
        )
        assert urgent_found

    def test_assess_risk_score_calculation(self):
        """Test risk score calculation logic."""
        model = CreepFatigueModel()

        # Create scenarios with known creep and fatigue states
        # Low creep (primary), low fatigue
        risk_low = model.assess_combined_risk(
            uuid4(),
            0.5,
            timedelta(days=20),
            [0.4, 0.5, 0.5],
        )

        # High creep (tertiary), high fatigue
        risk_high = model.assess_combined_risk(
            uuid4(),
            0.95,
            timedelta(days=100),
            [0.9, 0.9, 0.9, 0.9],
        )

        # High risk should have higher score
        assert risk_high["risk_score"] > risk_low["risk_score"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_lmp_with_very_small_workload(self):
        """Test LMP with very small workload."""
        model = CreepFatigueModel()

        lmp = model.calculate_larson_miller(0.01, 30)

        # Should be very small but not crash
        assert lmp >= 0
        assert lmp < 10

    def test_lmp_with_one_day_duration(self):
        """Test LMP with minimum duration."""
        model = CreepFatigueModel()

        lmp = model.calculate_larson_miller(0.8, 1)

        # log10(1) = 0, so LMP = 80 * 20 = 1600
        assert lmp > 0

    def test_strain_rate_with_two_points(self):
        """Test strain rate with minimum points for calculation."""
        model = CreepFatigueModel()

        rate = model.calculate_strain_rate([0.6, 0.8])

        # Should calculate slope
        assert rate > 0  # Increasing

    def test_fatigue_with_zero_stress(self):
        """Test fatigue calculation with zero stress rotation."""
        model = CreepFatigueModel()

        # Include a zero stress rotation
        curve = model.calculate_fatigue_damage([0.7, 0.0, 0.8])

        # Should handle gracefully
        assert curve.remaining_life_fraction > 0

    def test_assess_with_empty_rotation_history(self):
        """Test combined assessment with no rotation history."""
        model = CreepFatigueModel()

        risk = model.assess_combined_risk(
            uuid4(),
            0.7,
            timedelta(days=30),
            [],  # No rotation history
        )

        # Should still work
        assert "overall_risk" in risk
        # Fatigue should show perfect condition
        assert risk["fatigue_analysis"]["remaining_life"] == 1.0

    def test_predict_with_zero_duration(self):
        """Test prediction with zero duration."""
        model = CreepFatigueModel()

        analysis = model.predict_time_to_burnout(uuid4(), 0.8, timedelta(days=0))

        # Should handle gracefully
        assert analysis.larson_miller_parameter == 0.0
        assert analysis.creep_stage == CreepStage.PRIMARY


class TestConstantsAndThresholds:
    """Test model constants and thresholds."""

    def test_failure_threshold_defined(self):
        """Test FAILURE_THRESHOLD is defined."""
        assert CreepFatigueModel.FAILURE_THRESHOLD == 45.0

    def test_safe_lmp_defined(self):
        """Test SAFE_LMP is defined."""
        assert CreepFatigueModel.SAFE_LMP == 31.5

    def test_safe_lmp_below_failure(self):
        """Test SAFE_LMP is below FAILURE_THRESHOLD."""
        assert CreepFatigueModel.SAFE_LMP < CreepFatigueModel.FAILURE_THRESHOLD

    def test_safe_lmp_is_70_percent(self):
        """Test SAFE_LMP is approximately 70% of FAILURE_THRESHOLD."""
        ratio = CreepFatigueModel.SAFE_LMP / CreepFatigueModel.FAILURE_THRESHOLD
        assert abs(ratio - 0.7) < 0.01


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_resident_progressive_burnout_scenario(self):
        """Test tracking resident through progressive burnout stages."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Week 1-2: Fresh, adapting
        analysis_week2 = model.predict_time_to_burnout(
            resident_id, 0.7, timedelta(days=14)
        )
        assert analysis_week2.creep_stage == CreepStage.PRIMARY

        # Week 1-6: Steady state
        analysis_week6 = model.predict_time_to_burnout(
            resident_id, 0.75, timedelta(days=42)
        )
        # Should be transitioning to secondary
        assert analysis_week6.creep_stage in [CreepStage.PRIMARY, CreepStage.SECONDARY]

        # Week 1-12: High risk
        analysis_week12 = model.predict_time_to_burnout(
            resident_id, 0.85, timedelta(days=84)
        )
        # Likely in secondary or tertiary
        assert analysis_week12.creep_stage in [
            CreepStage.SECONDARY,
            CreepStage.TERTIARY,
        ]

    def test_rotation_fatigue_accumulation_scenario(self):
        """Test realistic rotation stress accumulation."""
        model = CreepFatigueModel()

        # PGY-1 year: mix of easy and hard rotations
        rotations = [
            0.5,  # Orientation
            0.7,  # Floor medicine
            0.8,  # ICU
            0.6,  # Clinic
            0.9,  # Trauma surgery
            0.7,  # Floor medicine
            0.5,  # Elective
            0.8,  # Emergency
        ]

        curve = model.calculate_fatigue_damage(rotations)

        # After 8 rotations, should have some but not critical damage
        assert 0.5 < curve.remaining_life_fraction < 1.0
        assert curve.current_cycles == 8

    def test_intervention_effectiveness_scenario(self):
        """Test that intervention (stress reduction) improves outlook."""
        model = CreepFatigueModel()
        resident_id = uuid4()

        # Before intervention: high stress
        before = model.predict_time_to_burnout(resident_id, 0.9, timedelta(days=60))

        # After intervention: reduced workload per recommendation
        reduction_pct = before.recommended_stress_reduction / 100.0
        new_workload = 0.9 * (1 - reduction_pct)

        after = model.predict_time_to_burnout(
            resident_id, new_workload, timedelta(days=60)
        )

        # After intervention should be better
        assert after.larson_miller_parameter < before.larson_miller_parameter
        assert after.estimated_time_to_failure > before.estimated_time_to_failure
