"""Tests for schedule analytics."""

import pytest
from datetime import date

from app.analytics.schedule.coverage_analyzer import CoverageAnalyzer
from app.analytics.schedule.workload_distribution import WorkloadDistribution
from app.analytics.schedule.rotation_metrics import RotationMetrics
from app.analytics.schedule.efficiency_score import EfficiencyScore


@pytest.mark.asyncio
class TestCoverageAnalyzer:
    """Test coverage analyzer."""

    async def test_analyze_coverage(self, async_db_session):
        """Test coverage analysis."""
        analyzer = CoverageAnalyzer(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        coverage = await analyzer.analyze_coverage(start_date, end_date)

        assert isinstance(coverage, dict)
        assert "coverage_rate" in coverage
        assert "total_blocks" in coverage
        assert "gaps" in coverage

    async def test_find_coverage_gaps(self, async_db_session):
        """Test gap detection."""
        analyzer = CoverageAnalyzer(async_db_session)

        # Would need fixtures for actual gap data
        gaps = await analyzer._find_coverage_gaps(
            date(2024, 1, 1), date(2024, 1, 31), threshold=0.5
        )

        assert isinstance(gaps, list)


@pytest.mark.asyncio
class TestWorkloadDistribution:
    """Test workload distribution."""

    async def test_analyze_distribution(self, async_db_session):
        """Test workload distribution analysis."""
        analyzer = WorkloadDistribution(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        distribution = await analyzer.analyze_distribution(start_date, end_date)

        assert isinstance(distribution, dict)
        assert "distribution" in distribution
        assert "stats" in distribution

    def test_calculate_gini(self):
        """Test Gini coefficient calculation."""
        analyzer = WorkloadDistribution(None)

        # Perfect equality
        gini = analyzer._calculate_gini([10, 10, 10, 10])
        assert gini < 0.1

        # Perfect inequality
        gini = analyzer._calculate_gini([0, 0, 0, 100])
        assert gini > 0.5


@pytest.mark.asyncio
class TestRotationMetrics:
    """Test rotation metrics."""

    async def test_analyze_rotation_metrics(self, async_db_session):
        """Test rotation metrics analysis."""
        analyzer = RotationMetrics(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        metrics = await analyzer.analyze_rotation_metrics(start_date, end_date)

        assert isinstance(metrics, dict)
        assert "rotations" in metrics
        assert "total_assignments" in metrics


@pytest.mark.asyncio
class TestEfficiencyScore:
    """Test efficiency score calculator."""

    async def test_calculate_efficiency(self, async_db_session):
        """Test efficiency calculation."""
        calculator = EfficiencyScore(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        efficiency = await calculator.calculate_efficiency(start_date, end_date)

        assert isinstance(efficiency, dict)
        assert "efficiency_score" in efficiency
        assert 0 <= efficiency["efficiency_score"] <= 100
        assert "coverage_rate" in efficiency
        assert "balance_score" in efficiency
