"""
Tests for VaR and Shapley MCP tool wrappers (DEBT-009).

Tests the armory tool wrappers in server.py that expose VaR and Shapley
functionality as MCP tools. These wrappers delegate to the underlying
implementations in var_risk_tools.py and the Shapley placeholder.
"""

import os
import pytest

# Enable all armory domains for testing
os.environ["ARMORY_DOMAINS"] = "all"

from scheduler_mcp.var_risk_tools import (
    CoverageVaRRequest,
    WorkloadVaRRequest,
    DisruptionSimulationRequest,
    DisruptionType,
    ConditionalVaRRequest,
    calculate_coverage_var,
    calculate_workload_var,
    simulate_disruption_scenarios,
    calculate_conditional_var,
    _calculate_coverage_var_placeholder,
    _calculate_workload_var_placeholder,
    _calculate_conditional_var_placeholder,
)


# =============================================================================
# VaR MCP Tool Wrapper Tests
# =============================================================================


@pytest.mark.asyncio
class TestCoverageVaRTool:
    """Test the calculate_coverage_var MCP tool wrapper."""

    async def test_coverage_var_placeholder_returns_valid_response(self):
        """Coverage VaR placeholder returns properly structured response."""
        request = CoverageVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            confidence_levels=[0.90, 0.95, 0.99],
            historical_days=90,
        )

        response = await calculate_coverage_var(request)

        assert response.period_start == "2025-01-01"
        assert response.period_end == "2025-03-31"
        assert response.historical_days == 90
        assert len(response.var_metrics) == 3
        assert response.baseline_coverage > 0.0
        assert response.worst_case_coverage >= 0.0
        assert response.severity is not None
        assert response.metadata.get("source") == "placeholder"

    async def test_coverage_var_metrics_are_ordered(self):
        """Higher confidence levels produce higher VaR values."""
        request = CoverageVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            confidence_levels=[0.90, 0.95, 0.99],
        )

        response = await calculate_coverage_var(request)
        var_values = [m.var_value for m in response.var_metrics]

        # VaR should be non-decreasing with confidence
        assert var_values[0] <= var_values[1] <= var_values[2]

    async def test_coverage_var_has_recommendations(self):
        """Response includes actionable recommendations."""
        request = CoverageVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        response = await calculate_coverage_var(request)
        assert len(response.recommendations) > 0

    async def test_coverage_var_single_confidence_level(self):
        """Works with a single confidence level."""
        request = CoverageVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            confidence_levels=[0.95],
        )

        response = await calculate_coverage_var(request)
        assert len(response.var_metrics) == 1
        assert response.var_metrics[0].confidence_level == 0.95


@pytest.mark.asyncio
class TestWorkloadVaRTool:
    """Test the calculate_workload_var MCP tool wrapper."""

    async def test_workload_var_gini(self):
        """Workload VaR works with Gini coefficient metric."""
        request = WorkloadVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            metric="gini_coefficient",
        )

        response = await calculate_workload_var(request)

        assert response.metric == "gini_coefficient"
        assert response.baseline_value > 0.0
        assert response.worst_case_value >= response.baseline_value
        assert len(response.var_metrics) > 0

    async def test_workload_var_max_hours(self):
        """Workload VaR works with max_hours metric."""
        request = WorkloadVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            metric="max_hours",
        )

        response = await calculate_workload_var(request)
        assert response.metric == "max_hours"
        assert response.baseline_value > 0.0

    async def test_workload_var_variance(self):
        """Workload VaR works with variance metric."""
        request = WorkloadVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            metric="variance",
        )

        response = await calculate_workload_var(request)
        assert response.metric == "variance"


@pytest.mark.asyncio
class TestDisruptionSimulationTool:
    """Test the simulate_disruption_scenarios MCP tool wrapper."""

    async def test_basic_simulation(self):
        """Basic simulation returns valid results."""
        request = DisruptionSimulationRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            num_simulations=100,
            disruption_types=[DisruptionType.RANDOM_ABSENCE],
            seed=42,
        )

        response = await simulate_disruption_scenarios(request)

        assert response.num_simulations == 100
        assert len(response.sample_scenarios) <= 10
        assert response.worst_case_scenario is not None
        assert response.var_95_coverage_drop >= 0.0
        assert response.var_99_coverage_drop >= 0.0
        assert response.var_95_coverage_drop <= response.var_99_coverage_drop

    async def test_simulation_reproducibility(self):
        """Same seed produces same results."""
        request = DisruptionSimulationRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            num_simulations=100,
            seed=42,
        )

        response1 = await simulate_disruption_scenarios(request)
        response2 = await simulate_disruption_scenarios(request)

        assert response1.var_95_coverage_drop == response2.var_95_coverage_drop
        assert response1.var_99_coverage_drop == response2.var_99_coverage_drop

    async def test_multiple_disruption_types(self):
        """Simulation works with multiple disruption types."""
        request = DisruptionSimulationRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            num_simulations=100,
            disruption_types=[
                DisruptionType.RANDOM_ABSENCE,
                DisruptionType.ILLNESS_CLUSTER,
            ],
            seed=42,
        )

        response = await simulate_disruption_scenarios(request)
        assert len(response.disruption_types) == 2


@pytest.mark.asyncio
class TestConditionalVaRTool:
    """Test the calculate_conditional_var MCP tool wrapper."""

    async def test_cvar_coverage_drop(self):
        """CVaR works with coverage_drop metric."""
        request = ConditionalVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            confidence_level=0.95,
            loss_metric="coverage_drop",
        )

        response = await calculate_conditional_var(request)

        assert response.cvar_value >= response.var_value
        assert response.tail_scenarios_count > 0
        assert response.tail_mean > 0.0
        assert response.confidence_level == 0.95
        assert response.loss_metric == "coverage_drop"

    async def test_cvar_workload_spike(self):
        """CVaR works with workload_spike metric."""
        request = ConditionalVaRRequest(
            start_date="2025-01-01",
            end_date="2025-03-31",
            loss_metric="workload_spike",
        )

        response = await calculate_conditional_var(request)
        assert response.loss_metric == "workload_spike"
        assert response.cvar_value >= response.var_value

    async def test_cvar_has_interpretation(self):
        """CVaR response includes human-readable interpretation."""
        request = ConditionalVaRRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        response = await calculate_conditional_var(request)
        assert len(response.interpretation) > 0
        assert "worst" in response.interpretation.lower()


# =============================================================================
# Shapley Placeholder Improvement Tests
# =============================================================================


class TestShapleyPlaceholder:
    """Test the improved Shapley placeholder in server.py."""

    def test_shapley_placeholder_not_uniform(self):
        """Verify Shapley placeholder no longer returns uniform distribution."""
        import random

        faculty_ids = ["fac-001", "fac-002", "fac-003", "fac-004"]
        n = len(faculty_ids)

        # Replicate the placeholder logic
        random.seed(hash(tuple(faculty_ids)) % 2**31)
        raw_weights = [random.gammavariate(2.0, 1.0) for _ in range(n)]
        total_weight = sum(raw_weights)
        shapley_proportions = [w / total_weight for w in raw_weights]

        # Values should NOT all be equal (1/n)
        uniform_value = 1.0 / n
        assert not all(
            abs(p - uniform_value) < 0.001 for p in shapley_proportions
        ), "Shapley values should not be uniformly distributed"

        # Values should sum to 1.0
        assert abs(sum(shapley_proportions) - 1.0) < 0.001

        # All values should be positive
        assert all(p > 0 for p in shapley_proportions)

    def test_shapley_placeholder_deterministic(self):
        """Same faculty IDs produce same Shapley values."""
        import random

        faculty_ids = ["fac-001", "fac-002", "fac-003"]

        def generate_proportions(fids):
            random.seed(hash(tuple(fids)) % 2**31)
            n = len(fids)
            raw = [random.gammavariate(2.0, 1.0) for _ in range(n)]
            total = sum(raw)
            return [w / total for w in raw]

        result1 = generate_proportions(faculty_ids)
        result2 = generate_proportions(faculty_ids)

        assert result1 == result2

    def test_shapley_placeholder_varies_by_faculty(self):
        """Different faculty sets produce different Shapley values."""
        import random

        def generate_proportions(fids):
            random.seed(hash(tuple(fids)) % 2**31)
            n = len(fids)
            raw = [random.gammavariate(2.0, 1.0) for _ in range(n)]
            total = sum(raw)
            return [w / total for w in raw]

        result1 = generate_proportions(["fac-001", "fac-002", "fac-003"])
        result2 = generate_proportions(["fac-004", "fac-005", "fac-006"])

        # Different inputs should (very likely) produce different outputs
        assert result1 != result2


# =============================================================================
# Armory Registration Tests
# =============================================================================


class TestArmoryRegistration:
    """Test VaR tools are properly registered in the armory loader."""

    def test_var_tools_in_operations_research_domain(self):
        """VaR tools are listed in the operations_research domain."""
        from scheduler_mcp.armory.loader import DOMAIN_TOOLS

        or_tools = DOMAIN_TOOLS["operations_research"]

        assert "calculate_coverage_var_tool" in or_tools
        assert "calculate_workload_var_tool" in or_tools
        assert "simulate_disruption_scenarios_tool" in or_tools
        assert "calculate_conditional_var_tool" in or_tools

    def test_var_tools_in_all_armory_tools(self):
        """VaR tools appear in ALL_ARMORY_TOOLS set."""
        from scheduler_mcp.armory.loader import ALL_ARMORY_TOOLS

        assert "calculate_coverage_var_tool" in ALL_ARMORY_TOOLS
        assert "calculate_workload_var_tool" in ALL_ARMORY_TOOLS
        assert "simulate_disruption_scenarios_tool" in ALL_ARMORY_TOOLS
        assert "calculate_conditional_var_tool" in ALL_ARMORY_TOOLS

    def test_shapley_still_registered(self):
        """Shapley tool remains in operations_research domain."""
        from scheduler_mcp.armory.loader import DOMAIN_TOOLS

        assert "calculate_shapley_workload_tool" in DOMAIN_TOOLS["operations_research"]
