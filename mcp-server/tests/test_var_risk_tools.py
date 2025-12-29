"""
Tests for VaR (Value-at-Risk) tools.

Tests the core VaR calculation functions and MCP tool endpoints.
"""

import pytest

# Import the core calculation functions
# Note: We test the calculation functions directly, not the async tool wrappers
from scheduler_mcp.var_risk_tools import (
    calculate_cvar,
    calculate_var,
    classify_risk_severity,
    RiskSeverity,
)


class TestVaRCalculations:
    """Test core VaR calculation functions."""

    def test_calculate_var_simple(self):
        """Test VaR calculation with simple data."""
        losses = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        # 90% confidence (10% tail) -> 10th percentile
        var_90 = calculate_var(losses, 0.90)
        assert var_90 == 9.0

        # 95% confidence (5% tail) -> 5th percentile
        var_95 = calculate_var(losses, 0.95)
        assert var_95 == 9.0  # With 10 samples, 5% = 0.5 samples, rounds to index 0

        # 50% confidence (50% tail) -> median
        var_50 = calculate_var(losses, 0.50)
        assert var_50 == 5.0

    def test_calculate_var_empty(self):
        """Test VaR with empty data."""
        losses = []
        var = calculate_var(losses, 0.95)
        assert var == 0.0

    def test_calculate_var_single_value(self):
        """Test VaR with single data point."""
        losses = [5.0]
        var = calculate_var(losses, 0.95)
        assert var == 5.0

    def test_calculate_cvar_simple(self):
        """Test CVaR calculation."""
        losses = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        var, cvar = calculate_cvar(losses, 0.90)

        # VaR should be at 90% confidence level
        assert var == 9.0

        # CVaR should be average of tail (values >= var)
        # Tail = [9.0, 10.0], average = 9.5
        assert cvar == 9.5

    def test_calculate_cvar_no_tail(self):
        """Test CVaR when no values exceed VaR."""
        losses = [1.0, 1.0, 1.0]

        var, cvar = calculate_cvar(losses, 0.95)

        # All values are the same
        assert var == 1.0
        assert cvar == 1.0

    def test_calculate_cvar_empty(self):
        """Test CVaR with empty data."""
        losses = []
        var, cvar = calculate_cvar(losses, 0.95)
        assert var == 0.0
        assert cvar == 0.0

    def test_classify_risk_severity(self):
        """Test risk severity classification."""
        # Low risk
        assert classify_risk_severity(0.05, 0.10, 0.20) == RiskSeverity.LOW

        # Moderate risk
        assert classify_risk_severity(0.08, 0.10, 0.20) == RiskSeverity.MODERATE

        # High risk
        assert classify_risk_severity(0.15, 0.10, 0.20) == RiskSeverity.HIGH

        # Critical risk
        assert classify_risk_severity(0.22, 0.10, 0.20) == RiskSeverity.CRITICAL

        # Extreme risk
        assert classify_risk_severity(0.35, 0.10, 0.20) == RiskSeverity.EXTREME


class TestVaRScenarios:
    """Test VaR with realistic scheduling scenarios."""

    def test_coverage_drop_distribution(self):
        """Test VaR with realistic coverage drop distribution."""
        # Simulate coverage drops: mostly small, some large (heavy-tailed)
        # 95 small drops (0-5%), 4 moderate (5-15%), 1 large (15-25%)
        small_drops = [0.01, 0.02, 0.03, 0.04, 0.05] * 19  # 95 values
        moderate_drops = [0.08, 0.10, 0.12, 0.15]  # 4 values
        large_drops = [0.22]  # 1 value

        losses = small_drops + moderate_drops + large_drops

        # 95% VaR should capture the moderate drops
        var_95 = calculate_var(losses, 0.95)
        assert 0.08 <= var_95 <= 0.22

        # CVaR should be higher than VaR (tail risk)
        var, cvar = calculate_cvar(losses, 0.95)
        assert cvar >= var

    def test_workload_inequality_var(self):
        """Test VaR for workload inequality (Gini coefficient)."""
        # Gini coefficients: mostly low (0.1-0.2), some high (0.3-0.4)
        gini_values = [0.12, 0.15, 0.18, 0.20] * 23  # 92 low values
        gini_values += [0.32, 0.35, 0.38, 0.40] * 2  # 8 high values

        var_95 = calculate_var(gini_values, 0.95)

        # 95% VaR should be in the high range
        assert 0.30 <= var_95 <= 0.40

        # Risk should be classified appropriately
        severity = classify_risk_severity(var_95, 0.25, 0.35)
        assert severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]


@pytest.mark.asyncio
class TestVaRToolsAsync:
    """Test async VaR tool functions."""

    async def test_calculate_coverage_var_placeholder(self):
        """Test coverage VaR tool with placeholder data."""
        from scheduler_mcp.var_risk_tools import (
            CoverageVaRRequest,
            _calculate_coverage_var_placeholder,
        )

        request = CoverageVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            confidence_levels=[0.90, 0.95, 0.99],
            historical_days=90,
        )

        response = _calculate_coverage_var_placeholder(request)

        # Verify response structure
        assert response.period_start == "2025-01-01"
        assert response.period_end == "2025-01-31"
        assert response.historical_days == 90
        assert len(response.var_metrics) == 3

        # Verify VaR ordering (higher confidence = higher VaR)
        vars = [m.var_value for m in response.var_metrics]
        assert vars[0] <= vars[1] <= vars[2]  # 90% <= 95% <= 99%

        # Verify severity is classified
        assert response.severity in [e.value for e in RiskSeverity]

    async def test_calculate_workload_var_placeholder(self):
        """Test workload VaR tool with placeholder data."""
        from scheduler_mcp.var_risk_tools import (
            WorkloadVaRRequest,
            _calculate_workload_var_placeholder,
        )

        request = WorkloadVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            confidence_levels=[0.95],
            metric="gini_coefficient",
        )

        response = _calculate_workload_var_placeholder(request)

        # Verify response
        assert response.metric == "gini_coefficient"
        assert len(response.var_metrics) == 1
        assert response.baseline_value > 0.0
        assert response.worst_case_value >= response.baseline_value

    async def test_simulate_disruption_scenarios(self):
        """Test disruption simulation."""
        from scheduler_mcp.var_risk_tools import (
            DisruptionSimulationRequest,
            DisruptionType,
            simulate_disruption_scenarios,
        )

        request = DisruptionSimulationRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            num_simulations=100,
            disruption_types=[DisruptionType.RANDOM_ABSENCE],
            disruption_probability=0.05,
            seed=42,  # For reproducibility
        )

        response = await simulate_disruption_scenarios(request)

        # Verify simulation ran
        assert response.num_simulations == 100
        assert len(response.sample_scenarios) <= 10
        assert response.worst_case_scenario is not None

        # Verify VaR ordering
        assert response.var_95_coverage_drop <= response.var_99_coverage_drop

    async def test_calculate_conditional_var_placeholder(self):
        """Test CVaR calculation."""
        from scheduler_mcp.var_risk_tools import (
            ConditionalVaRRequest,
            _calculate_conditional_var_placeholder,
        )

        request = ConditionalVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            confidence_level=0.95,
            loss_metric="coverage_drop",
        )

        response = _calculate_conditional_var_placeholder(request)

        # CVaR should be >= VaR (tail is worse than threshold)
        assert response.cvar_value >= response.var_value

        # Verify tail statistics
        assert response.tail_scenarios_count > 0
        assert response.tail_mean > 0.0
        assert response.tail_std >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
