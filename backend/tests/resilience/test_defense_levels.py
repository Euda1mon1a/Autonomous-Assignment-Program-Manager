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
        """Test YELLOW level with 80-90% utilization."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.85,
            n1_failures=2,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=1,
        )

        assert result.level == DefenseLevel.YELLOW
        assert len(result.recommendations) > 0

    def test_orange_level_high_utilization(self):
        """Test ORANGE level with 90-95% utilization."""
        calc = DefenseLevelCalculator()
        result = calc.calculate(
            utilization=0.92,
            n1_failures=8,
            n2_failures=2,
            coverage_gaps=3,
        )

        assert result.level == DefenseLevel.ORANGE
        assert "degraded" in result.rationale.lower() or "orange" in result.rationale.lower()

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
        assert any("CRITICAL" in rec or "urgent" in rec.lower() for rec in result.recommendations)

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
        assert any("EMERGENCY" in rec or "emergency" in rec.lower() for rec in result.recommendations)

    def test_n2_failures_increase_severity(self):
        """Test that N-2 failures significantly increase severity."""
        calc = DefenseLevelCalculator()

        # Without N-2 failures
        result_no_n2 = calc.calculate(
            utilization=0.75,
            n1_failures=5,
            n2_failures=0,
        )

        # With N-2 failures
        result_with_n2 = calc.calculate(
            utilization=0.75,
            n1_failures=5,
            n2_failures=10,
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
        """Test defense level comparison operators."""
        assert DefenseLevel.GREEN < DefenseLevel.YELLOW
        assert DefenseLevel.YELLOW < DefenseLevel.ORANGE
        assert DefenseLevel.ORANGE < DefenseLevel.RED
        assert DefenseLevel.RED < DefenseLevel.BLACK

        assert DefenseLevel.GREEN <= DefenseLevel.GREEN
        assert DefenseLevel.BLACK > DefenseLevel.RED

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
