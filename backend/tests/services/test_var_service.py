"""Tests for VaR (Value-at-Risk) service.

Test coverage:
- VaR calculation at various confidence levels
- CVaR (Conditional VaR / Expected Shortfall) calculation
- Severity classification based on thresholds
- Gini coefficient for workload distribution
- Recommendation generation
"""

import pytest

from app.schemas.var_analytics import RiskSeverity
from app.services.var_service import VaRService


class TestVaRCalculation:
    """Test _calculate_var static method."""

    def test_empty_list_returns_zero(self):
        """Empty loss list should return 0."""
        assert VaRService._calculate_var([], 0.95) == 0.0

    def test_single_value_returns_that_value(self):
        """Single value list should return that value."""
        assert VaRService._calculate_var([0.5], 0.95) == 0.5

    def test_var_at_95_confidence(self):
        """VaR at 95% should return 95th percentile."""
        # 10 values, 95th percentile = index 9 (0.95 * 10)
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        var = VaRService._calculate_var(losses, 0.95)
        assert var == 1.0  # 95th percentile is the max

    def test_var_at_90_confidence(self):
        """VaR at 90% should return 90th percentile."""
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        var = VaRService._calculate_var(losses, 0.90)
        assert var == 1.0  # index 9

    def test_var_at_50_confidence(self):
        """VaR at 50% should return median."""
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        var = VaRService._calculate_var(losses, 0.50)
        assert var == 0.6  # index 5 (0.5 * 10)

    def test_var_sorts_unsorted_input(self):
        """VaR should work with unsorted input."""
        losses = [0.5, 0.1, 0.9, 0.3, 0.7]
        var = VaRService._calculate_var(losses, 0.80)
        # Sorted: [0.1, 0.3, 0.5, 0.7, 0.9], index 4 = 0.9
        assert var == 0.9


class TestCVaRCalculation:
    """Test _calculate_cvar static method."""

    def test_empty_list_returns_zeros(self):
        """Empty loss list should return (0.0, 0.0)."""
        var, cvar = VaRService._calculate_cvar([], 0.95)
        assert var == 0.0
        assert cvar == 0.0

    def test_cvar_greater_than_or_equal_var(self):
        """CVaR (expected shortfall) should always be >= VaR."""
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        var, cvar = VaRService._calculate_cvar(losses, 0.90)
        assert cvar >= var

    def test_cvar_is_tail_mean(self):
        """CVaR should be the mean of losses >= VaR."""
        # Simple case: 5 values
        losses = [0.1, 0.2, 0.3, 0.4, 0.5]
        var, cvar = VaRService._calculate_cvar(losses, 0.80)
        # VaR at 80% of 5 = index 4 = 0.5
        # Tail losses >= 0.5 = [0.5]
        # Mean = 0.5
        assert var == 0.5
        assert cvar == 0.5

    def test_cvar_with_multiple_tail_values(self):
        """CVaR with multiple values in tail."""
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        var, cvar = VaRService._calculate_cvar(losses, 0.70)
        # VaR at 70% of 10 = index 7 = 0.8
        # Tail losses >= 0.8 = [0.8, 0.9, 1.0]
        # Mean = 0.9
        assert var == 0.8
        assert cvar == 0.9


class TestSeverityClassification:
    """Test _classify_severity static method."""

    def test_low_severity(self):
        """Value below moderate * 0.5 should be LOW."""
        # Moderate = 0.10, so below 0.05 is LOW
        severity = VaRService._classify_severity(0.04, 0.10, 0.20)
        assert severity == RiskSeverity.LOW

    def test_moderate_severity(self):
        """Value at moderate * 0.5 to moderate should be MODERATE."""
        severity = VaRService._classify_severity(0.06, 0.10, 0.20)
        assert severity == RiskSeverity.MODERATE

    def test_high_severity(self):
        """Value at moderate threshold should be HIGH."""
        severity = VaRService._classify_severity(0.15, 0.10, 0.20)
        assert severity == RiskSeverity.HIGH

    def test_critical_severity(self):
        """Value at high threshold should be CRITICAL."""
        severity = VaRService._classify_severity(0.25, 0.10, 0.20)
        assert severity == RiskSeverity.CRITICAL

    def test_extreme_severity(self):
        """Value at high * 1.5 should be EXTREME."""
        severity = VaRService._classify_severity(0.35, 0.10, 0.20)
        assert severity == RiskSeverity.EXTREME


class TestGiniCoefficient:
    """Test _calculate_gini static method."""

    def test_empty_list_returns_zero(self):
        """Empty list should return 0."""
        assert VaRService._calculate_gini([]) == 0.0

    def test_single_value_returns_zero(self):
        """Single value (n < 2) should return 0."""
        assert VaRService._calculate_gini([100.0]) == 0.0

    def test_perfect_equality_returns_zero(self):
        """All equal values should have Gini = 0."""
        gini = VaRService._calculate_gini([10.0, 10.0, 10.0, 10.0])
        assert gini == pytest.approx(0.0, abs=0.001)

    def test_moderate_inequality(self):
        """Moderate inequality should have Gini between 0 and 1."""
        # [10, 20, 30, 40] has some inequality
        gini = VaRService._calculate_gini([10.0, 20.0, 30.0, 40.0])
        assert 0.0 < gini < 1.0

    def test_high_inequality(self):
        """Highly unequal distribution should have higher Gini."""
        low_inequality = VaRService._calculate_gini([9.0, 10.0, 10.0, 11.0])
        high_inequality = VaRService._calculate_gini([1.0, 1.0, 1.0, 97.0])
        assert high_inequality > low_inequality


class TestCoverageRecommendations:
    """Test _generate_coverage_recommendations."""

    def test_low_risk_returns_default_message(self):
        """Low risk should return positive message."""
        service = VaRService()
        recs = service._generate_coverage_recommendations(0.05, RiskSeverity.LOW)
        assert len(recs) == 1
        assert "acceptable" in recs[0].lower()

    def test_high_risk_includes_float_pool(self):
        """High risk should recommend float pool."""
        service = VaRService()
        recs = service._generate_coverage_recommendations(0.20, RiskSeverity.HIGH)
        assert any("float pool" in r.lower() for r in recs)

    def test_critical_risk_includes_scheduling_gaps(self):
        """Critical risk should mention scheduling gaps."""
        service = VaRService()
        recs = service._generate_coverage_recommendations(0.25, RiskSeverity.CRITICAL)
        assert any("gaps" in r.lower() for r in recs)

    def test_extreme_risk_includes_urgent(self):
        """Extreme risk should include URGENT warning."""
        service = VaRService()
        recs = service._generate_coverage_recommendations(0.35, RiskSeverity.EXTREME)
        assert any("URGENT" in r for r in recs)


class TestWorkloadRecommendations:
    """Test _generate_workload_recommendations."""

    def test_low_risk_returns_default_message(self):
        """Low risk should return positive message."""
        service = VaRService()
        recs = service._generate_workload_recommendations(
            "gini_coefficient", 0.15, RiskSeverity.LOW
        )
        assert len(recs) == 1
        assert "acceptable" in recs[0].lower()

    def test_high_gini_includes_fairness_warning(self):
        """High Gini coefficient should warn about fairness."""
        service = VaRService()
        recs = service._generate_workload_recommendations(
            "gini_coefficient", 0.35, RiskSeverity.HIGH
        )
        assert any("fairness" in r.lower() or "inequality" in r.lower() for r in recs)

    def test_high_max_hours_includes_acgme_warning(self):
        """High max hours should mention ACGME."""
        service = VaRService()
        recs = service._generate_workload_recommendations(
            "max_hours", 75.0, RiskSeverity.HIGH
        )
        assert any("ACGME" in r for r in recs)


class TestCVaRRecommendations:
    """Test _generate_cvar_recommendations."""

    def test_low_risk_returns_default_message(self):
        """Low risk should return positive message."""
        service = VaRService()
        recs = service._generate_cvar_recommendations(
            "coverage_drop", 0.10, RiskSeverity.LOW
        )
        assert len(recs) == 1
        assert "acceptable" in recs[0].lower()

    def test_high_risk_mentions_contingency(self):
        """High risk should recommend contingency planning."""
        service = VaRService()
        recs = service._generate_cvar_recommendations(
            "coverage_drop", 0.30, RiskSeverity.HIGH
        )
        assert any("contingency" in r.lower() for r in recs)

    def test_critical_recommends_backup_resources(self):
        """Critical CVaR should recommend backup resources."""
        service = VaRService()
        recs = service._generate_cvar_recommendations(
            "workload_spike", 0.30, RiskSeverity.CRITICAL
        )
        assert any("backup" in r.lower() for r in recs)
