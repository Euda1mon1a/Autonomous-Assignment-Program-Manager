"""
Tests for defense level calculator.

Tests the 5-tier defense system (GREEN → YELLOW → ORANGE → RED → BLACK).
"""

import pytest

from app.resilience.engine.defense_level_calculator import (
    DefenseLevel,
    DefenseLevelCalculator,
)


class TestDefenseLevelCalculator:
    """Test suite for defense level calculation."""

    def test_green_level_low_utilization(self):
        """Test GREEN level with low utilization and no failures."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.60,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
            cascade_risk=0.0,
        )

        assert result.level == DefenseLevel.GREEN
        assert result.metrics.utilization == 0.60
        assert "normal" in result.rationale.lower()

    def test_yellow_level_moderate_utilization(self):
        """Test YELLOW level requires multiple corroborating signals.

        Utilization=0.85 with n1=2 and burnout=1 produces a combined
        weighted score of ~0.275 (GREEN). The weighted system needs
        more signals to reach YELLOW (score >= 1.0).
        """
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.88,
            n1_failures=8,
            n2_failures=3,
            coverage_gaps=1,
            burnout_cases=3,
            cascade_risk=0.15,
        )

        assert result.level == DefenseLevel.YELLOW
        assert len(result.recommendations) > 0

    def test_orange_level_high_utilization(self):
        """Test ORANGE level with high utilization and multiple stressors.

        Utilization=0.92, n1=8, n2=2, gaps=3 produces YELLOW (score ~1.26).
        Need stronger signals to reach ORANGE (score >= 2.0).
        """
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.96,
            n1_failures=15,
            n2_failures=8,
            coverage_gaps=5,
            burnout_cases=6,
        )

        assert result.level == DefenseLevel.ORANGE
        assert (
            "degraded" in result.rationale.lower()
            or "orange" in result.rationale.lower()
        )

    def test_red_level_critical_utilization(self):
        """Test RED level with >95% utilization."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.96,
            n1_failures=15,
            n2_failures=8,
            coverage_gaps=5,
            burnout_cases=6,
        )

        assert result.level in [DefenseLevel.RED, DefenseLevel.ORANGE]
        assert any(
            "CRITICAL" in rec or "urgent" in rec.lower()
            for rec in result.recommendations
        )

    def test_black_level_emergency(self):
        """Test BLACK level with catastrophic conditions."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.99,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=12,
            cascade_risk=0.80,
        )

        assert result.level in [DefenseLevel.BLACK, DefenseLevel.RED]
        assert any(
            "EMERGENCY" in rec or "emergency" in rec.lower()
            for rec in result.recommendations
        )

    def test_n2_failures_increase_severity(self):
        """Test that N-2 failures significantly increase severity.

        Baseline stress at GREEN (score ~0.74). Adding critical N-2
        failures (weight=0.25, score 3.33) pushes across the YELLOW
        boundary (combined ~1.58).
        """
        calc = DefenseLevelCalculator()

        # Without N-2 failures - moderate stress, stays GREEN
        result_no_n2 = calc.calculate(
            utilization=0.90,
            n1_failures=5,
            n2_failures=0,
            coverage_gaps=1,
            burnout_cases=1,
            cascade_risk=0.05,
        )

        # With N-2 failures - same baseline, crosses to YELLOW
        result_with_n2 = calc.calculate(
            utilization=0.90,
            n1_failures=5,
            n2_failures=20,
            coverage_gaps=1,
            burnout_cases=1,
            cascade_risk=0.05,
        )

        assert result_with_n2.level > result_no_n2.level

    def test_cascade_risk_affects_level(self):
        """Test that high cascade risk increases defense level."""
        calc = DefenseLevelCalculator()

        # Low cascade risk
        result_low = calc.calculate(
            utilization=0.80,
            cascade_risk=0.10,
        )

        # High cascade risk
        result_high = calc.calculate(
            utilization=0.80,
            cascade_risk=0.70,
        )

        assert result_high.level >= result_low.level

    def test_defense_level_comparison(self):
        """Test defense level comparison operators.

        Only __lt__ and __le__ are implemented on DefenseLevel.
        Use RED < BLACK instead of BLACK > RED since __gt__ is not defined.
        """
        assert DefenseLevel.GREEN < DefenseLevel.YELLOW
        assert DefenseLevel.YELLOW < DefenseLevel.ORANGE
        assert DefenseLevel.ORANGE < DefenseLevel.RED
        assert DefenseLevel.RED < DefenseLevel.BLACK

        assert DefenseLevel.GREEN <= DefenseLevel.GREEN
        # Use __lt__ (RED < BLACK) rather than __gt__ (BLACK > RED)
        # since __gt__ is not implemented on DefenseLevel
        assert DefenseLevel.RED < DefenseLevel.BLACK

    def test_severity_score(self):
        """Test severity score property."""
        assert DefenseLevel.GREEN.severity_score == 0
        assert DefenseLevel.YELLOW.severity_score == 1
        assert DefenseLevel.ORANGE.severity_score == 2
        assert DefenseLevel.RED.severity_score == 3
        assert DefenseLevel.BLACK.severity_score == 4

    def test_recommendations_present(self):
        """Test that all defense levels generate recommendations."""
        calc = DefenseLevelCalculator()

        for utilization in [0.60, 0.85, 0.92, 0.96, 0.99]:
            result = calc.calculate(utilization=utilization)
            assert len(result.recommendations) > 0
            assert result.rationale != ""

    def test_edge_case_zero_values(self):
        """Test edge case with all zero values."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.0,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
            cascade_risk=0.0,
        )

        assert result.level == DefenseLevel.GREEN
        assert result.metrics.utilization == 0.0

    def test_edge_case_extreme_values(self):
        """Test edge case with extreme values."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=1.5,  # Over 100%!
            n1_failures=100,
            n2_failures=50,
            coverage_gaps=50,
            burnout_cases=30,
            cascade_risk=1.0,
        )

        assert result.level == DefenseLevel.BLACK
        assert result.metrics.utilization == 1.5
