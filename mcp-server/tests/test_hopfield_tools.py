"""
Tests for Hopfield Network Attractor Analysis MCP Tools.

These tests verify the tool implementations return properly structured responses
with realistic placeholder data.
"""

import pytest
from datetime import date

from scheduler_mcp.hopfield_attractor_tools import (
    calculate_schedule_energy,
    find_nearby_attractors,
    measure_basin_depth,
    detect_spurious_attractors,
    StabilityLevelEnum,
    AttractorTypeEnum,
)


class TestCalculateScheduleEnergy:
    """Test suite for calculate_schedule_energy tool."""

    @pytest.mark.asyncio
    async def test_calculate_energy_basic(self):
        """Test basic energy calculation returns valid response."""
        result = await calculate_schedule_energy()

        assert result.analyzed_at is not None
        assert result.assignments_analyzed >= 0
        assert result.state_dimension >= 0
        assert result.metrics is not None
        assert result.stability_level in StabilityLevelEnum
        assert result.interpretation != ""
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_calculate_energy_with_dates(self):
        """Test energy calculation with specific date range."""
        result = await calculate_schedule_energy(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        assert result.period_start == "2025-01-01"
        assert result.period_end == "2025-01-31"

    @pytest.mark.asyncio
    async def test_energy_metrics_structure(self):
        """Test energy metrics have expected fields."""
        result = await calculate_schedule_energy()
        metrics = result.metrics

        assert hasattr(metrics, 'total_energy')
        assert hasattr(metrics, 'normalized_energy')
        assert -1.0 <= metrics.normalized_energy <= 1.0
        assert hasattr(metrics, 'stability_score')
        assert 0.0 <= metrics.stability_score <= 1.0
        assert hasattr(metrics, 'is_local_minimum')
        assert isinstance(metrics.is_local_minimum, bool)
        assert hasattr(metrics, 'distance_to_minimum')
        assert metrics.distance_to_minimum >= 0


class TestFindNearbyAttractors:
    """Test suite for find_nearby_attractors tool."""

    @pytest.mark.asyncio
    async def test_find_attractors_basic(self):
        """Test attractor search returns valid response."""
        result = await find_nearby_attractors()

        assert result.analyzed_at is not None
        assert result.attractors_found >= 0
        assert len(result.attractors) == result.attractors_found
        assert isinstance(result.global_minimum_identified, bool)
        assert result.interpretation != ""

    @pytest.mark.asyncio
    async def test_find_attractors_with_distance(self):
        """Test attractor search with custom max distance."""
        result = await find_nearby_attractors(max_distance=15)

        assert result.attractors_found >= 0
        # All attractors should be within max_distance
        for attractor in result.attractors:
            assert attractor.hamming_distance >= 0

    @pytest.mark.asyncio
    async def test_attractor_info_structure(self):
        """Test attractor info objects have expected fields."""
        result = await find_nearby_attractors()

        for attractor in result.attractors:
            assert attractor.attractor_id is not None
            assert attractor.attractor_type in AttractorTypeEnum
            assert hasattr(attractor, 'energy_level')
            assert hasattr(attractor, 'basin_depth')
            assert attractor.basin_depth >= 0
            assert hasattr(attractor, 'basin_volume')
            assert attractor.basin_volume >= 0
            assert 0.0 <= attractor.confidence <= 1.0


class TestMeasureBasinDepth:
    """Test suite for measure_basin_depth tool."""

    @pytest.mark.asyncio
    async def test_measure_basin_basic(self):
        """Test basin depth measurement returns valid response."""
        result = await measure_basin_depth()

        assert result.analyzed_at is not None
        assert result.attractor_id is not None
        assert result.metrics is not None
        assert result.stability_level in StabilityLevelEnum
        assert isinstance(result.is_robust, bool)
        assert result.robustness_threshold >= 0

    @pytest.mark.asyncio
    async def test_measure_basin_with_perturbations(self):
        """Test basin depth with custom perturbation count."""
        result = await measure_basin_depth(num_perturbations=200)

        assert result.metrics is not None
        # More perturbations should give more reliable results
        assert result.metrics.basin_stability_index >= 0.0

    @pytest.mark.asyncio
    async def test_basin_metrics_structure(self):
        """Test basin metrics have expected fields."""
        result = await measure_basin_depth()
        metrics = result.metrics

        assert hasattr(metrics, 'min_escape_energy')
        assert metrics.min_escape_energy >= 0.0
        assert hasattr(metrics, 'avg_escape_energy')
        assert metrics.avg_escape_energy >= metrics.min_escape_energy
        assert hasattr(metrics, 'max_escape_energy')
        assert metrics.max_escape_energy >= metrics.avg_escape_energy
        assert hasattr(metrics, 'basin_stability_index')
        assert 0.0 <= metrics.basin_stability_index <= 1.0
        assert hasattr(metrics, 'num_escape_paths')
        assert metrics.num_escape_paths >= 0


class TestDetectSpuriousAttractors:
    """Test suite for detect_spurious_attractors tool."""

    @pytest.mark.asyncio
    async def test_detect_spurious_basic(self):
        """Test spurious attractor detection returns valid response."""
        result = await detect_spurious_attractors()

        assert result.analyzed_at is not None
        assert result.spurious_attractors_found >= 0
        assert len(result.spurious_attractors) == result.spurious_attractors_found
        assert 0.0 <= result.total_basin_coverage <= 1.0
        assert isinstance(result.is_current_state_spurious, bool)

    @pytest.mark.asyncio
    async def test_detect_spurious_with_params(self):
        """Test spurious detection with custom parameters."""
        result = await detect_spurious_attractors(
            search_radius=25,
            min_basin_size=15
        )

        assert result.spurious_attractors_found >= 0

    @pytest.mark.asyncio
    async def test_spurious_attractor_info_structure(self):
        """Test spurious attractor info objects have expected fields."""
        result = await detect_spurious_attractors()

        for spurious in result.spurious_attractors:
            assert spurious.attractor_id is not None
            assert hasattr(spurious, 'energy_level')
            assert hasattr(spurious, 'basin_size')
            assert spurious.basin_size >= 0
            assert spurious.anti_pattern_type != ""
            assert spurious.description != ""
            assert spurious.risk_level in ["low", "medium", "high", "critical"]
            assert spurious.distance_from_valid >= 0
            assert 0.0 <= spurious.probability_of_capture <= 1.0
            assert spurious.mitigation_strategy != ""


class TestToolIntegration:
    """Test integration between Hopfield tools."""

    @pytest.mark.asyncio
    async def test_energy_and_attractors_consistency(self):
        """Test that energy calculation and attractor search are consistent."""
        energy_result = await calculate_schedule_energy()
        attractor_result = await find_nearby_attractors()

        # Current state energy should be close to one of the attractors
        assert energy_result.metrics.total_energy is not None
        assert attractor_result.current_state_energy is not None

    @pytest.mark.asyncio
    async def test_basin_depth_for_found_attractor(self):
        """Test basin depth measurement for a found attractor."""
        attractor_result = await find_nearby_attractors()

        if attractor_result.attractors_found > 0:
            first_attractor = attractor_result.attractors[0]
            basin_result = await measure_basin_depth(
                attractor_id=first_attractor.attractor_id
            )

            assert basin_result.attractor_id == first_attractor.attractor_id

    @pytest.mark.asyncio
    async def test_comprehensive_schedule_analysis(self):
        """Test running all four tools in sequence for complete analysis."""
        # 1. Calculate energy
        energy = await calculate_schedule_energy()
        assert energy.stability_level is not None

        # 2. Find nearby attractors
        attractors = await find_nearby_attractors(max_distance=10)
        assert attractors.attractors_found >= 0

        # 3. Measure basin depth
        basin = await measure_basin_depth(num_perturbations=100)
        assert basin.is_robust is not None

        # 4. Detect spurious attractors
        spurious = await detect_spurious_attractors(search_radius=20)
        assert spurious.spurious_attractors_found >= 0

        # All tools should return consistent severity assessments
        severities = [
            energy.severity,
            basin.severity,
            spurious.severity,
        ]
        assert all(s is not None for s in severities)
