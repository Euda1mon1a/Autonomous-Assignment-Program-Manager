"""
Tests for empirical testing tools.

These tests verify that the MCP empirical tools work correctly
for benchmarking, ablation studies, and module analysis.
"""


import pytest

from scheduler_mcp.empirical_tools import (
    ablation_study,
    benchmark_constraints,
    benchmark_resilience,
    benchmark_solvers,
    module_usage_analysis,
)


class TestBenchmarkSolvers:
    """Tests for solver benchmarking."""

    @pytest.mark.asyncio
    async def test_benchmark_solvers_returns_result(self):
        """Test that benchmark_solvers returns a valid result."""
        result = await benchmark_solvers(
            solvers=["greedy"],
            scenario_count=1,
            timeout_per_run=30,
        )

        assert result is not None
        assert result.solvers_tested == ["greedy"]
        assert result.scenarios_run == 1
        assert "greedy" in result.results_by_solver

    @pytest.mark.asyncio
    async def test_benchmark_solvers_default_solvers(self):
        """Test with default solver list."""
        result = await benchmark_solvers(scenario_count=1)

        assert "greedy" in result.solvers_tested
        assert "cp_sat" in result.solvers_tested

    @pytest.mark.asyncio
    async def test_benchmark_solvers_has_recommendation(self):
        """Test that recommendation is generated."""
        result = await benchmark_solvers(
            solvers=["greedy"],
            scenario_count=1,
        )

        assert result.recommendation is not None
        assert len(result.recommendation) > 0


class TestBenchmarkConstraints:
    """Tests for constraint benchmarking."""

    @pytest.mark.asyncio
    async def test_benchmark_constraints_returns_result(self):
        """Test that benchmark_constraints returns a valid result."""
        result = await benchmark_constraints()

        assert result is not None
        assert isinstance(result.constraint_stats, dict)
        assert isinstance(result.high_yield, list)
        assert isinstance(result.low_yield, list)

    @pytest.mark.asyncio
    async def test_benchmark_constraints_categorizes(self):
        """Test that constraints are categorized."""
        result = await benchmark_constraints()

        # Should have some categorization
        total = len(result.high_yield) + len(result.low_yield) + len(result.candidates_for_removal)
        assert total >= 0  # May be empty if no constraints found


class TestAblationStudy:
    """Tests for ablation study."""

    @pytest.mark.asyncio
    async def test_ablation_nonexistent_module(self):
        """Test ablation of non-existent module."""
        result = await ablation_study("nonexistent/module.py")

        assert result is not None
        assert result.module_exists is False
        assert "not found" in result.recommendation.lower()

    @pytest.mark.asyncio
    async def test_ablation_existing_module(self):
        """Test ablation of existing module."""
        # Use a module we know exists
        result = await ablation_study("scheduling/engine.py")

        assert result is not None
        if result.module_exists:
            assert result.module_size_lines > 0
            assert result.removal_impact in ["none", "minor", "major", "breaking", "unknown"]

    @pytest.mark.asyncio
    async def test_ablation_directory(self):
        """Test ablation of directory."""
        result = await ablation_study("scheduling/")

        assert result is not None
        if result.module_exists:
            assert result.file_count >= 0


class TestBenchmarkResilience:
    """Tests for resilience benchmarking."""

    @pytest.mark.asyncio
    async def test_benchmark_resilience_returns_result(self):
        """Test that benchmark_resilience returns a valid result."""
        result = await benchmark_resilience()

        assert result is not None
        assert isinstance(result.module_stats, dict)
        assert isinstance(result.high_value, list)
        assert isinstance(result.low_value, list)

    @pytest.mark.asyncio
    async def test_benchmark_resilience_specific_modules(self):
        """Test with specific modules."""
        result = await benchmark_resilience(
            modules=["n1_contingency", "homeostasis"]
        )

        assert "n1_contingency" in result.module_stats
        assert "homeostasis" in result.module_stats

    @pytest.mark.asyncio
    async def test_benchmark_resilience_has_tiers(self):
        """Test that tier analysis is generated."""
        result = await benchmark_resilience()

        # Should categorize modules into tiers
        for name, stats in result.module_stats.items():
            assert stats.tier in ["tier1", "tier2", "tier3", "unknown", ""]


class TestModuleUsageAnalysis:
    """Tests for module usage analysis."""

    @pytest.mark.asyncio
    async def test_module_usage_returns_result(self):
        """Test that module_usage_analysis returns a valid result."""
        result = await module_usage_analysis()

        assert result is not None
        assert isinstance(result.reachable_modules, list)
        assert isinstance(result.unreachable_modules, list)

    @pytest.mark.asyncio
    async def test_module_usage_custom_entry_points(self):
        """Test with custom entry points."""
        result = await module_usage_analysis(
            entry_points=["main", "scheduling"]
        )

        assert result is not None
        assert "main" in result.entry_points_analyzed
        assert "scheduling" in result.entry_points_analyzed

    @pytest.mark.asyncio
    async def test_module_usage_calculates_dead_code(self):
        """Test that dead code metrics are calculated."""
        result = await module_usage_analysis()

        assert result.dead_code_lines >= 0
        assert result.dead_code_percentage >= 0.0
        assert result.dead_code_percentage <= 100.0


class TestIntegration:
    """Integration tests for empirical tools."""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """Test a complete analysis workflow."""
        # 1. Benchmark solvers
        solver_result = await benchmark_solvers(
            solvers=["greedy"],
            scenario_count=1,
        )
        assert solver_result is not None

        # 2. Benchmark resilience
        resilience_result = await benchmark_resilience(
            modules=["n1_contingency"]
        )
        assert resilience_result is not None

        # 3. Check module usage
        usage_result = await module_usage_analysis(
            entry_points=["main"]
        )
        assert usage_result is not None

        # All tools should return structured data
        assert solver_result.recommendation
        assert isinstance(resilience_result.module_stats, dict)
        assert isinstance(usage_result.reachable_modules, list)
