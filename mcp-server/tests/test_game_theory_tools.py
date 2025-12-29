"""
Tests for Game Theory Analysis MCP Tools.

These tests verify the game theory tool implementations for Nash equilibrium
analysis, deviation incentives, and coordination failure detection.

Following the pattern from test_hopfield_tools.py with pytest.mark.asyncio
and structured response validation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from scheduler_mcp.tools.game_theory_tools import (
    # Main async functions
    analyze_nash_stability,
    find_deviation_incentives,
    detect_coordination_failures,
    # Helper functions
    calculate_person_utility,
    _calculate_workload_fairness,
    _calculate_preference_satisfaction,
    _calculate_convenience,
    _calculate_continuity,
    # Request/Response models
    NashStabilityRequest,
    DeviationIncentivesRequest,
    NashStabilityResponse,
    PersonDeviationAnalysis,
    CoordinationFailuresResponse,
    # Enums
    StabilityStatus,
    DeviationType,
    CoordinationFailureType,
    # Data classes
    UtilityComponents,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_assignments():
    """Sample assignment data for testing."""
    return [
        {"id": "assign-1", "person_id": "person-a", "block_id": "block-1"},
        {"id": "assign-2", "person_id": "person-a", "block_id": "block-2"},
        {"id": "assign-3", "person_id": "person-b", "block_id": "block-1"},
        {"id": "assign-4", "person_id": "person-b", "block_id": "block-3"},
        {"id": "assign-5", "person_id": "person-c", "block_id": "block-2"},
    ]


@pytest.fixture
def assignments_by_person(sample_assignments):
    """Group sample assignments by person."""
    grouped = {}
    for assignment in sample_assignments:
        pid = assignment["person_id"]
        grouped.setdefault(pid, []).append(assignment)
    return grouped


@pytest.fixture
def mock_api_assignments_response(sample_assignments):
    """Mock API response for assignments."""
    return {"assignments": sample_assignments}


# =============================================================================
# UtilityComponents Tests
# =============================================================================


class TestUtilityComponents:
    """Test suite for UtilityComponents dataclass."""

    def test_utility_components_creation(self):
        """Test creating UtilityComponents with valid values."""
        utility = UtilityComponents(
            workload_fairness=0.8,
            preference_satisfaction=0.7,
            convenience=0.6,
            continuity=0.9,
        )

        assert utility.workload_fairness == 0.8
        assert utility.preference_satisfaction == 0.7
        assert utility.convenience == 0.6
        assert utility.continuity == 0.9

    def test_total_utility_calculation(self):
        """Test weighted total utility calculation."""
        utility = UtilityComponents(
            workload_fairness=1.0,
            preference_satisfaction=1.0,
            convenience=1.0,
            continuity=1.0,
        )

        # All 1.0 with weights summing to 1.0 should give 1.0 (use approx for float)
        assert abs(utility.total_utility() - 1.0) < 1e-9

    def test_total_utility_with_default_weights(self):
        """Test total utility uses correct default weights."""
        utility = UtilityComponents(
            workload_fairness=0.8,
            preference_satisfaction=0.7,
            convenience=0.6,
            continuity=0.5,
        )

        # Default weights: workload=0.4, preference=0.3, convenience=0.2, continuity=0.1
        expected = 0.8 * 0.4 + 0.7 * 0.3 + 0.6 * 0.2 + 0.5 * 0.1
        assert abs(utility.total_utility() - expected) < 0.0001

    def test_total_utility_with_custom_weights(self):
        """Test total utility with custom weights."""
        utility = UtilityComponents(
            workload_fairness=1.0,
            preference_satisfaction=0.0,
            convenience=0.0,
            continuity=0.0,
        )
        # Override weights
        utility.workload_weight = 1.0
        utility.preference_weight = 0.0
        utility.convenience_weight = 0.0
        utility.continuity_weight = 0.0

        assert utility.total_utility() == 1.0

    def test_utility_bounds(self):
        """Test utility stays in [0.0, 1.0] range."""
        utility = UtilityComponents(
            workload_fairness=0.0,
            preference_satisfaction=0.0,
            convenience=0.0,
            continuity=0.0,
        )
        assert utility.total_utility() == 0.0

        utility = UtilityComponents(
            workload_fairness=1.0,
            preference_satisfaction=1.0,
            convenience=1.0,
            continuity=1.0,
        )
        # Use approximate comparison for floating point
        assert abs(utility.total_utility() - 1.0) < 1e-9


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestWorkloadFairnessCalculation:
    """Test suite for _calculate_workload_fairness helper."""

    def test_empty_assignments(self):
        """Test with empty assignments returns perfect fairness."""
        result = _calculate_workload_fairness([], {})
        assert result == 1.0

    def test_single_person_is_fair(self, assignments_by_person):
        """Test single person's workload is compared against all."""
        person_assignments = assignments_by_person["person-a"]
        result = _calculate_workload_fairness(person_assignments, assignments_by_person)

        assert 0.0 <= result <= 1.0

    def test_equal_distribution_is_fair(self):
        """Test equal distribution returns high fairness."""
        # Each person has exactly 2 assignments
        all_assignments = {
            "person-a": [{"id": "1"}, {"id": "2"}],
            "person-b": [{"id": "3"}, {"id": "4"}],
            "person-c": [{"id": "5"}, {"id": "6"}],
        }
        result = _calculate_workload_fairness(all_assignments["person-a"], all_assignments)

        # Equal distribution should have high fairness (close to 1.0)
        assert result >= 0.9

    def test_unequal_distribution_less_fair(self):
        """Test unequal distribution returns lower fairness."""
        all_assignments = {
            "person-a": [{"id": str(i)} for i in range(10)],  # 10 assignments
            "person-b": [{"id": "only-one"}],  # 1 assignment
        }
        result = _calculate_workload_fairness(all_assignments["person-a"], all_assignments)

        # Unequal distribution should have lower fairness
        assert result < 0.9


class TestPreferenceSatisfactionCalculation:
    """Test suite for _calculate_preference_satisfaction helper."""

    def test_no_assignments(self):
        """Test with no assignments returns perfect satisfaction."""
        result = _calculate_preference_satisfaction([])
        assert result == 1.0

    def test_no_preference_trails(self):
        """Test without preference data returns neutral 0.5."""
        assignments = [{"id": "assign-1"}, {"id": "assign-2"}]
        result = _calculate_preference_satisfaction(assignments)
        assert result == 0.5

    def test_with_preference_trails(self):
        """Test with preference trail data."""
        assignments = [{"id": "assign-1"}, {"id": "assign-2"}]
        preference_trails = {"assign-1": 8.0, "assign-2": 6.0}  # Scale 0-10

        result = _calculate_preference_satisfaction(assignments, preference_trails)

        # Average of 8/10 and 6/10 = 0.7
        assert 0.6 <= result <= 0.8

    def test_high_preference_strength(self):
        """Test with high preference strength (capped at 10)."""
        assignments = [{"id": "assign-1"}]
        preference_trails = {"assign-1": 15.0}  # Above max

        result = _calculate_preference_satisfaction(assignments, preference_trails)

        # Should be capped at 1.0
        assert result == 1.0


class TestConvenienceCalculation:
    """Test suite for _calculate_convenience helper."""

    def test_no_assignments(self):
        """Test with no assignments returns perfect convenience."""
        result = _calculate_convenience([])
        assert result == 1.0

    def test_with_assignments(self):
        """Test with assignments returns placeholder value."""
        assignments = [{"id": "assign-1"}, {"id": "assign-2"}]
        result = _calculate_convenience(assignments)

        # Placeholder returns 0.6
        assert result == 0.6


class TestContinuityCalculation:
    """Test suite for _calculate_continuity helper."""

    def test_no_previous_assignments(self):
        """Test with no previous assignments returns perfect continuity."""
        current = [{"id": "assign-1"}]
        result = _calculate_continuity(current, [])
        assert result == 1.0

    def test_no_current_assignments(self):
        """Test with no current assignments returns zero continuity."""
        previous = [{"id": "assign-1"}]
        result = _calculate_continuity([], previous)
        assert result == 0.0

    def test_full_overlap(self):
        """Test full overlap returns perfect continuity."""
        assignments = [{"id": "assign-1"}, {"id": "assign-2"}]
        result = _calculate_continuity(assignments, assignments)
        assert result == 1.0

    def test_partial_overlap(self):
        """Test partial overlap returns fractional continuity."""
        current = [{"id": "assign-1"}, {"id": "assign-3"}]
        previous = [{"id": "assign-1"}, {"id": "assign-2"}]

        result = _calculate_continuity(current, previous)

        # 1 of 2 previous assignments retained = 0.5
        assert result == 0.5

    def test_no_overlap(self):
        """Test no overlap returns zero continuity."""
        current = [{"id": "assign-3"}, {"id": "assign-4"}]
        previous = [{"id": "assign-1"}, {"id": "assign-2"}]

        result = _calculate_continuity(current, previous)
        assert result == 0.0


class TestCalculatePersonUtility:
    """Test suite for calculate_person_utility function."""

    def test_basic_utility_calculation(self, assignments_by_person):
        """Test basic utility calculation returns UtilityComponents."""
        person_assignments = assignments_by_person["person-a"]

        result = calculate_person_utility(
            person_id="person-a",
            assignments=person_assignments,
            all_assignments=assignments_by_person,
        )

        assert isinstance(result, UtilityComponents)
        assert 0.0 <= result.total_utility() <= 1.0

    def test_utility_with_custom_weights(self, assignments_by_person):
        """Test utility calculation with custom weights."""
        person_assignments = assignments_by_person["person-a"]
        custom_weights = {
            "workload": 0.6,
            "preference": 0.2,
            "convenience": 0.1,
            "continuity": 0.1,
        }

        result = calculate_person_utility(
            person_id="person-a",
            assignments=person_assignments,
            all_assignments=assignments_by_person,
            weights=custom_weights,
        )

        assert result.workload_weight == 0.6
        assert result.preference_weight == 0.2

    def test_utility_with_preference_trails(self, assignments_by_person):
        """Test utility calculation with preference trail data."""
        person_assignments = assignments_by_person["person-a"]
        preference_trails = {"assign-1": 9.0, "assign-2": 7.0}

        result = calculate_person_utility(
            person_id="person-a",
            assignments=person_assignments,
            all_assignments=assignments_by_person,
            preference_trails=preference_trails,
        )

        # With preference data, should have higher preference satisfaction
        assert result.preference_satisfaction > 0.5


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Test suite for game theory enums."""

    def test_stability_status_values(self):
        """Test StabilityStatus enum values."""
        assert StabilityStatus.STABLE.value == "stable"
        assert StabilityStatus.UNSTABLE.value == "unstable"
        assert StabilityStatus.WEAKLY_STABLE.value == "weakly_stable"
        assert StabilityStatus.UNKNOWN.value == "unknown"

    def test_deviation_type_values(self):
        """Test DeviationType enum values."""
        assert DeviationType.SWAP.value == "swap"
        assert DeviationType.ABSORB.value == "absorb"
        assert DeviationType.DROP.value == "drop"
        assert DeviationType.REJECT.value == "reject"

    def test_coordination_failure_type_values(self):
        """Test CoordinationFailureType enum values."""
        assert CoordinationFailureType.INFORMATION_ASYMMETRY.value == "information_asymmetry"
        assert CoordinationFailureType.TRUST_DEFICIT.value == "trust_deficit"
        assert CoordinationFailureType.TRANSACTION_COST.value == "transaction_cost"
        assert CoordinationFailureType.PROTOCOL_BARRIER.value == "protocol_barrier"
        assert CoordinationFailureType.PREFERENCE_MISMATCH.value == "preference_mismatch"


# =============================================================================
# Request Model Tests
# =============================================================================


class TestRequestModels:
    """Test suite for request model validation."""

    def test_nash_stability_request_valid(self):
        """Test valid NashStabilityRequest creation."""
        request = NashStabilityRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
        )
        assert request.start_date == "2025-01-01"
        assert request.end_date == "2025-01-31"
        assert request.include_person_details is True  # default
        assert request.deviation_threshold == 0.01  # default

    def test_nash_stability_request_custom_params(self):
        """Test NashStabilityRequest with custom parameters."""
        request = NashStabilityRequest(
            start_date="2025-01-01",
            end_date="2025-01-31",
            include_person_details=False,
            deviation_threshold=0.05,
            utility_weights={"workload": 0.5, "preference": 0.5},
        )
        assert request.include_person_details is False
        assert request.deviation_threshold == 0.05
        assert request.utility_weights["workload"] == 0.5

    def test_deviation_incentives_request_valid(self):
        """Test valid DeviationIncentivesRequest creation."""
        request = DeviationIncentivesRequest(
            person_id="person-123",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )
        assert request.person_id == "person-123"
        assert request.max_alternatives == 5  # default

    def test_deviation_incentives_request_custom_params(self):
        """Test DeviationIncentivesRequest with custom parameters."""
        request = DeviationIncentivesRequest(
            person_id="person-123",
            start_date="2025-01-01",
            end_date="2025-01-31",
            include_all_alternatives=True,
            max_alternatives=10,
        )
        assert request.include_all_alternatives is True
        assert request.max_alternatives == 10


# =============================================================================
# analyze_nash_stability Tests
# =============================================================================


class TestAnalyzeNashStability:
    """Test suite for analyze_nash_stability function."""

    @pytest.mark.asyncio
    async def test_returns_valid_response_structure(self):
        """Test function returns properly structured response."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value={"assignments": []})
            mock_get_client.return_value = mock_client

            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await analyze_nash_stability(request)

            assert isinstance(result, NashStabilityResponse)
            assert result.analyzed_at is not None
            assert isinstance(result.stability_status, StabilityStatus)
            assert isinstance(result.is_nash_equilibrium, bool)
            assert result.total_players >= 0
            assert 0.0 <= result.deviation_rate <= 1.0

    @pytest.mark.asyncio
    async def test_empty_schedule_is_nash_stable(self):
        """Test empty schedule is trivially Nash stable."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value={"assignments": []})
            mock_get_client.return_value = mock_client

            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await analyze_nash_stability(request)

            assert result.stability_status == StabilityStatus.STABLE
            assert result.is_nash_equilibrium is True
            assert result.total_players == 0
            assert result.players_with_deviations == 0

    @pytest.mark.asyncio
    async def test_with_assignments_analyzes_players(self, mock_api_assignments_response):
        """Test with assignments analyzes all players."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_get_client.return_value = mock_client

            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await analyze_nash_stability(request)

            # Should have 3 unique persons
            assert result.total_players == 3
            assert result.game_theoretic_interpretation != ""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self):
        """Test returns placeholder response on API error."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_get_client.side_effect = Exception("API unavailable")

            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await analyze_nash_stability(request)

            assert result.stability_status == StabilityStatus.UNKNOWN
            assert result.is_nash_equilibrium is False
            assert "failed" in result.game_theoretic_interpretation.lower()

    @pytest.mark.asyncio
    async def test_respects_deviation_threshold(self, mock_api_assignments_response):
        """Test deviation threshold filters small utility gains."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_get_client.return_value = mock_client

            # High threshold should filter out small deviations
            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
                deviation_threshold=0.5,  # Very high threshold
            )

            result = await analyze_nash_stability(request)

            # With high threshold, fewer deviations should pass
            assert result.metadata["deviation_threshold"] == 0.5

    @pytest.mark.asyncio
    async def test_includes_recommendations_when_unstable(self, mock_api_assignments_response):
        """Test recommendations are provided when schedule is unstable."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_get_client.return_value = mock_client

            request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
                deviation_threshold=0.001,  # Very low threshold to catch deviations
            )

            result = await analyze_nash_stability(request)

            # Response should have interpretation regardless of stability
            assert isinstance(result.game_theoretic_interpretation, str)
            assert len(result.game_theoretic_interpretation) > 0


# =============================================================================
# find_deviation_incentives Tests
# =============================================================================


class TestFindDeviationIncentives:
    """Test suite for find_deviation_incentives function."""

    @pytest.mark.asyncio
    async def test_returns_valid_response_structure(self, mock_api_assignments_response):
        """Test function returns properly structured response."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_client.get_swap_candidates = AsyncMock(return_value={"candidates": []})
            mock_get_client.return_value = mock_client

            request = DeviationIncentivesRequest(
                person_id="person-a",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await find_deviation_incentives(request)

            assert isinstance(result, PersonDeviationAnalysis)
            assert result.person_id is not None
            assert 0.0 <= result.current_utility <= 1.0
            assert isinstance(result.utility_breakdown, dict)
            assert isinstance(result.has_profitable_deviation, bool)

    @pytest.mark.asyncio
    async def test_analyzes_strategic_position(self, mock_api_assignments_response):
        """Test determines strategic position correctly."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_client.get_swap_candidates = AsyncMock(return_value={"candidates": []})
            mock_get_client.return_value = mock_client

            request = DeviationIncentivesRequest(
                person_id="person-a",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await find_deviation_incentives(request)

            # Strategic position should be a non-empty string
            assert result.strategic_position != ""
            assert isinstance(result.strategic_position, str)

    @pytest.mark.asyncio
    async def test_identifies_barriers(self, mock_api_assignments_response):
        """Test identifies barriers to deviation."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_client.get_swap_candidates = AsyncMock(return_value={"candidates": []})
            mock_get_client.return_value = mock_client

            request = DeviationIncentivesRequest(
                person_id="person-a",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await find_deviation_incentives(request)

            # No candidates should result in barriers being identified
            assert len(result.barriers_to_deviation) > 0
            assert "No compatible swap partners found" in result.barriers_to_deviation

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self):
        """Test returns placeholder response on API error."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_get_client.side_effect = Exception("API unavailable")

            request = DeviationIncentivesRequest(
                person_id="person-a",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            result = await find_deviation_incentives(request)

            assert result.current_utility == 0.5  # Placeholder value
            assert "backend unavailable" in result.strategic_position.lower()


# =============================================================================
# detect_coordination_failures Tests
# =============================================================================


class TestDetectCoordinationFailures:
    """Test suite for detect_coordination_failures function."""

    @pytest.mark.asyncio
    async def test_returns_valid_response_structure(self, mock_api_assignments_response):
        """Test function returns properly structured response."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_get_client.return_value = mock_client

            result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            assert isinstance(result, CoordinationFailuresResponse)
            assert result.analyzed_at is not None
            assert result.total_failures_detected >= 0
            assert result.total_pareto_gain_available >= 0.0
            assert isinstance(result.failures, list)

    @pytest.mark.asyncio
    async def test_detects_protocol_barrier(self, mock_api_assignments_response):
        """Test detects protocol barrier coordination failure."""
        # Create larger assignment set to trigger failure detection
        large_assignments = {
            "assignments": [
                {"id": f"assign-{i}", "person_id": f"person-{i % 5}", "block_id": f"block-{i}"}
                for i in range(15)
            ]
        }

        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=large_assignments)
            mock_get_client.return_value = mock_client

            result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            # With >10 assignments, should detect at least one failure
            assert result.total_failures_detected >= 1

            if result.failures:
                failure = result.failures[0]
                assert failure.failure_type == CoordinationFailureType.PROTOCOL_BARRIER
                assert failure.potential_pareto_gain > 0
                assert len(failure.involved_person_ids) > 0

    @pytest.mark.asyncio
    async def test_provides_recommendations(self, mock_api_assignments_response):
        """Test provides system recommendations when failures detected."""
        large_assignments = {
            "assignments": [
                {"id": f"assign-{i}", "person_id": f"person-{i % 5}", "block_id": f"block-{i}"}
                for i in range(15)
            ]
        }

        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=large_assignments)
            mock_get_client.return_value = mock_client

            result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            if result.total_failures_detected > 0:
                assert len(result.system_recommendations) > 0
                assert result.game_theoretic_insights != ""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self):
        """Test returns placeholder response on API error."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_get_client.side_effect = Exception("API unavailable")

            result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )

            assert result.total_failures_detected == 0
            assert result.total_pareto_gain_available == 0.0
            assert "failed" in result.game_theoretic_insights.lower()

    @pytest.mark.asyncio
    async def test_respects_min_pareto_gain(self, mock_api_assignments_response):
        """Test min_pareto_gain parameter filters small improvements."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_get_client.return_value = mock_client

            result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
                min_pareto_gain=0.05,
            )

            # All returned failures should have gain >= threshold
            for failure in result.failures:
                assert failure.potential_pareto_gain >= 0.05


# =============================================================================
# Integration Tests
# =============================================================================


class TestGameTheoryToolIntegration:
    """Test integration between game theory tools."""

    @pytest.mark.asyncio
    async def test_nash_and_deviation_consistency(self, mock_api_assignments_response):
        """Test Nash stability and deviation analysis are consistent."""
        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=mock_api_assignments_response)
            mock_client.get_swap_candidates = AsyncMock(return_value={"candidates": []})
            mock_get_client.return_value = mock_client

            # Run Nash stability analysis
            nash_request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            nash_result = await analyze_nash_stability(nash_request)

            # Run deviation analysis for a person
            deviation_request = DeviationIncentivesRequest(
                person_id="person-a",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            deviation_result = await find_deviation_incentives(deviation_request)

            # Both should return valid results
            assert nash_result.total_players >= 0
            assert deviation_result.current_utility >= 0.0

    @pytest.mark.asyncio
    async def test_comprehensive_game_theory_analysis(self, mock_api_assignments_response):
        """Test running all three game theory tools in sequence."""
        large_assignments = {
            "assignments": [
                {"id": f"assign-{i}", "person_id": f"person-{i % 3}", "block_id": f"block-{i}"}
                for i in range(15)
            ]
        }

        with patch("scheduler_mcp.api_client.get_api_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_assignments = AsyncMock(return_value=large_assignments)
            mock_client.get_swap_candidates = AsyncMock(
                return_value={"candidates": [{"person_id": "person-2", "compatibility_score": 0.8}]}
            )
            mock_get_client.return_value = mock_client

            # 1. Analyze Nash stability
            nash_request = NashStabilityRequest(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            nash_result = await analyze_nash_stability(nash_request)
            assert nash_result.stability_status in StabilityStatus

            # 2. Find deviation incentives for first player
            deviation_request = DeviationIncentivesRequest(
                person_id="person-0",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            deviation_result = await find_deviation_incentives(deviation_request)
            assert deviation_result.strategic_position != ""

            # 3. Detect coordination failures
            coordination_result = await detect_coordination_failures(
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            assert coordination_result.total_failures_detected >= 0

            # All tools should complete without error
            assert nash_result.analyzed_at is not None
            assert coordination_result.analyzed_at is not None
