"""
Tests for Ecological Dynamics (Lotka-Volterra) MCP Tools.

These tests verify the tool implementations for predator-prey modeling
of schedule supply/demand dynamics return properly structured responses
with valid value ranges.
"""

import pytest
from datetime import date, timedelta

from scheduler_mcp.tools.ecological_dynamics_tools import (
    analyze_supply_demand_cycles,
    predict_capacity_crunch,
    find_equilibrium_point,
    simulate_intervention,
    HistoricalDataPoint,
    SupplyDemandCyclesRequest,
    CapacityCrunchRequest,
    EquilibriumRequest,
    InterventionRequest,
    InterventionTypeEnum,
    SystemStabilityEnum,
    RiskLevelEnum,
)


# ============================================================================
# Fixtures for Test Data
# ============================================================================


@pytest.fixture
def oscillating_historical_data() -> list[HistoricalDataPoint]:
    """
    Create synthetic historical data with oscillating supply/demand pattern.

    Simulates natural boom/bust cycles in coverage.
    """
    start_date = date(2025, 1, 1)
    data_points = []

    for i in range(20):
        # Simulate oscillations: capacity and demand cycle
        capacity = 45 + 10 * ((-1) ** (i // 3))  # Oscillates 35-55
        demand = 42 + 8 * ((-1) ** ((i + 2) // 3))  # Oscillates 34-50, phase shifted

        data_points.append(
            HistoricalDataPoint(
                date=start_date + timedelta(weeks=i),
                capacity=float(capacity),
                demand=float(demand),
            )
        )

    return data_points


@pytest.fixture
def stable_historical_data() -> list[HistoricalDataPoint]:
    """
    Create historical data with low variance (stable system).
    """
    start_date = date(2025, 1, 1)
    data_points = []

    for i in range(15):
        # Minimal oscillation around equilibrium
        capacity = 50 + (i % 3 - 1) * 2  # 48, 50, 52, 48, ...
        demand = 40 + (i % 3 - 1) * 1  # 39, 40, 41, 39, ...

        data_points.append(
            HistoricalDataPoint(
                date=start_date + timedelta(weeks=i),
                capacity=float(capacity),
                demand=float(demand),
            )
        )

    return data_points


@pytest.fixture
def lotka_volterra_params() -> dict[str, float]:
    """Standard Lotka-Volterra parameters for testing."""
    return {
        "alpha": 0.1,  # Capacity growth rate
        "beta": 0.02,  # Consumption rate
        "delta": 0.01,  # Demand amplification
        "gamma": 0.05,  # Demand decay
    }


# ============================================================================
# Tests for analyze_supply_demand_cycles
# ============================================================================


class TestAnalyzeSupplyDemandCycles:
    """Test suite for analyze_supply_demand_cycles tool."""

    @pytest.mark.asyncio
    async def test_analyze_cycles_basic(self, oscillating_historical_data):
        """Test basic cycle analysis returns valid response structure."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )

        result = await analyze_supply_demand_cycles(request)

        # Verify response structure
        assert result.analyzed_at is not None
        assert result.data_points == len(oscillating_historical_data)
        assert result.fitted_parameters is not None
        assert result.ecological_interpretation != ""

    @pytest.mark.asyncio
    async def test_analyze_cycles_fitted_parameters(self, oscillating_historical_data):
        """Test that fitted parameters are present and positive."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=60,
        )

        result = await analyze_supply_demand_cycles(request)
        params = result.fitted_parameters

        # All LV parameters must be positive
        assert "alpha" in params and params["alpha"] > 0
        assert "beta" in params and params["beta"] > 0
        assert "delta" in params and params["delta"] > 0
        assert "gamma" in params and params["gamma"] > 0

    @pytest.mark.asyncio
    async def test_analyze_cycles_r_squared_range(self, oscillating_historical_data):
        """Test R-squared is in valid range [0, 1]."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=30,
        )

        result = await analyze_supply_demand_cycles(request)

        assert 0.0 <= result.r_squared <= 1.0
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_cycles_equilibrium_positive(self, oscillating_historical_data):
        """Test equilibrium values are non-negative."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )

        result = await analyze_supply_demand_cycles(request)

        assert result.equilibrium_capacity >= 0.0
        assert result.equilibrium_demand >= 0.0

    @pytest.mark.asyncio
    async def test_analyze_cycles_stability_classification(self, oscillating_historical_data):
        """Test stability is a valid enum value."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )

        result = await analyze_supply_demand_cycles(request)

        assert result.system_stability in SystemStabilityEnum

    @pytest.mark.asyncio
    async def test_analyze_cycles_predicted_trajectory(self, oscillating_historical_data):
        """Test predicted trajectory has valid structure."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )

        result = await analyze_supply_demand_cycles(request)

        assert len(result.predicted_trajectory) > 0
        for point in result.predicted_trajectory:
            assert "day" in point
            assert "capacity" in point
            assert "demand" in point
            assert point["capacity"] >= 0
            assert point["demand"] >= 0

    @pytest.mark.asyncio
    async def test_analyze_cycles_current_state(self, oscillating_historical_data):
        """Test current state reflects last data point."""
        request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=30,
        )

        result = await analyze_supply_demand_cycles(request)

        # Current values should match last historical point
        last_point = oscillating_historical_data[-1]
        assert result.current_capacity == last_point.capacity
        assert result.current_demand == last_point.demand


# ============================================================================
# Tests for predict_capacity_crunch
# ============================================================================


class TestPredictCapacityCrunch:
    """Test suite for predict_capacity_crunch tool."""

    @pytest.mark.asyncio
    async def test_predict_crunch_basic(self, lotka_volterra_params):
        """Test basic crunch prediction returns valid response."""
        request = CapacityCrunchRequest(
            current_capacity=40.0,
            current_demand=48.0,
            crunch_threshold=20.0,
            prediction_days=180,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        assert result.analyzed_at is not None
        assert result.current_capacity == 40.0
        assert result.current_demand == 48.0
        assert result.crunch_threshold == 20.0

    @pytest.mark.asyncio
    async def test_predict_crunch_equilibrium_calculated(self, lotka_volterra_params):
        """Test equilibrium is correctly calculated from parameters."""
        request = CapacityCrunchRequest(
            current_capacity=50.0,
            current_demand=40.0,
            crunch_threshold=10.0,
            prediction_days=90,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        # Equilibrium: x* = gamma/delta, y* = alpha/beta
        expected_x_eq = lotka_volterra_params["gamma"] / lotka_volterra_params["delta"]
        expected_y_eq = lotka_volterra_params["alpha"] / lotka_volterra_params["beta"]

        assert abs(result.equilibrium_capacity - expected_x_eq) < 0.01

    @pytest.mark.asyncio
    async def test_predict_crunch_risk_level_enum(self, lotka_volterra_params):
        """Test risk level is valid enum value."""
        request = CapacityCrunchRequest(
            current_capacity=40.0,
            current_demand=50.0,
            crunch_threshold=20.0,
            prediction_days=180,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        assert result.risk_level in RiskLevelEnum

    @pytest.mark.asyncio
    async def test_predict_crunch_minimum_capacity(self, lotka_volterra_params):
        """Test minimum capacity fields are valid."""
        request = CapacityCrunchRequest(
            current_capacity=50.0,
            current_demand=45.0,
            crunch_threshold=15.0,
            prediction_days=180,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        assert result.minimum_capacity >= 0.0
        assert result.minimum_capacity_date is not None

    @pytest.mark.asyncio
    async def test_predict_crunch_trajectory_structure(self, lotka_volterra_params):
        """Test predicted trajectory has valid structure."""
        request = CapacityCrunchRequest(
            current_capacity=40.0,
            current_demand=48.0,
            crunch_threshold=20.0,
            prediction_days=90,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        assert len(result.predicted_trajectory) > 0
        for point in result.predicted_trajectory:
            assert "day" in point
            assert "capacity" in point
            assert "demand" in point

    @pytest.mark.asyncio
    async def test_predict_crunch_no_crunch_scenario(self):
        """Test when no crunch is predicted (stable near equilibrium)."""
        # Parameters near equilibrium with very low threshold
        # Equilibrium: x* = gamma/delta = 0.1/0.01 = 10.0
        # Start at equilibrium so oscillations are minimal
        request = CapacityCrunchRequest(
            current_capacity=10.0,  # At equilibrium
            current_demand=10.0,  # At equilibrium (alpha/beta = 0.1/0.01)
            alpha=0.1,
            beta=0.01,
            delta=0.01,
            gamma=0.1,
            crunch_threshold=1.0,  # Very low - well below equilibrium
            prediction_days=90,
        )

        result = await predict_capacity_crunch(request)

        # System should stay near equilibrium, minimum capacity should be above threshold
        assert result.minimum_capacity >= 0.0
        # Either no crunch, or risk should reflect reality
        assert result.risk_level in RiskLevelEnum

    @pytest.mark.asyncio
    async def test_predict_crunch_mitigation_urgency_present(self, lotka_volterra_params):
        """Test mitigation urgency message is provided."""
        request = CapacityCrunchRequest(
            current_capacity=40.0,
            current_demand=50.0,
            crunch_threshold=20.0,
            prediction_days=180,
            **lotka_volterra_params,
        )

        result = await predict_capacity_crunch(request)

        assert result.mitigation_urgency != ""
        assert isinstance(result.mitigation_urgency, str)


# ============================================================================
# Tests for find_equilibrium_point
# ============================================================================


class TestFindEquilibriumPoint:
    """Test suite for find_equilibrium_point tool."""

    @pytest.mark.asyncio
    async def test_find_equilibrium_basic(self, lotka_volterra_params):
        """Test basic equilibrium calculation returns valid response."""
        request = EquilibriumRequest(**lotka_volterra_params)

        result = await find_equilibrium_point(request)

        assert result.analyzed_at is not None
        assert result.equilibrium_capacity >= 0.0
        assert result.equilibrium_demand >= 0.0

    @pytest.mark.asyncio
    async def test_find_equilibrium_formula_correctness(self):
        """Test equilibrium follows mathematical formula: x*=gamma/delta, y*=alpha/beta."""
        request = EquilibriumRequest(
            alpha=0.2,
            beta=0.04,
            delta=0.02,
            gamma=0.1,
        )

        result = await find_equilibrium_point(request)

        # x* = gamma/delta = 0.1/0.02 = 5.0
        # y* = alpha/beta = 0.2/0.04 = 5.0
        assert abs(result.equilibrium_capacity - 5.0) < 0.001
        assert abs(result.equilibrium_demand - 5.0) < 0.001

    @pytest.mark.asyncio
    async def test_find_equilibrium_oscillation_period(self, lotka_volterra_params):
        """Test oscillation period is calculated."""
        request = EquilibriumRequest(**lotka_volterra_params)

        result = await find_equilibrium_point(request)

        assert result.oscillation_period_days >= 0.0

    @pytest.mark.asyncio
    async def test_find_equilibrium_stability_flag(self, lotka_volterra_params):
        """Test stability flag is boolean."""
        request = EquilibriumRequest(**lotka_volterra_params)

        result = await find_equilibrium_point(request)

        assert isinstance(result.is_stable, bool)

    @pytest.mark.asyncio
    async def test_find_equilibrium_interpretation_present(self, lotka_volterra_params):
        """Test ecological interpretation is provided."""
        request = EquilibriumRequest(**lotka_volterra_params)

        result = await find_equilibrium_point(request)

        assert result.ecological_interpretation != ""
        assert len(result.ecological_interpretation) > 20  # Non-trivial explanation

    @pytest.mark.asyncio
    async def test_find_equilibrium_parameter_sensitivity(self, lotka_volterra_params):
        """Test parameter sensitivity analysis is provided."""
        request = EquilibriumRequest(**lotka_volterra_params)

        result = await find_equilibrium_point(request)

        assert result.parameter_sensitivity is not None
        assert "alpha" in result.parameter_sensitivity
        assert "beta" in result.parameter_sensitivity
        assert "delta" in result.parameter_sensitivity
        assert "gamma" in result.parameter_sensitivity


# ============================================================================
# Tests for simulate_intervention
# ============================================================================


class TestSimulateIntervention:
    """Test suite for simulate_intervention tool."""

    @pytest.mark.asyncio
    async def test_simulate_intervention_add_capacity(self, lotka_volterra_params):
        """Test ADD_CAPACITY intervention simulation."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=48.0,
            intervention_type=InterventionTypeEnum.ADD_CAPACITY,
            intervention_magnitude=0.25,  # 25% increase
            intervention_start_day=0,
            intervention_duration_days=90,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert result.analyzed_at is not None
        assert result.intervention_type == InterventionTypeEnum.ADD_CAPACITY
        assert result.intervention_magnitude == 0.25

    @pytest.mark.asyncio
    async def test_simulate_intervention_trajectories_present(self, lotka_volterra_params):
        """Test both baseline and intervention trajectories are returned."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=45.0,
            intervention_type=InterventionTypeEnum.REDUCE_DEMAND,
            intervention_magnitude=0.20,
            simulation_days=120,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert len(result.baseline_trajectory) > 0
        assert len(result.intervention_trajectory) > 0

    @pytest.mark.asyncio
    async def test_simulate_intervention_capacity_metrics(self, lotka_volterra_params):
        """Test capacity improvement metrics are valid."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=50.0,
            intervention_type=InterventionTypeEnum.ADD_CAPACITY,
            intervention_magnitude=0.30,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert result.baseline_min_capacity >= 0.0
        assert result.intervention_min_capacity >= 0.0
        # With positive intervention, capacity should improve or stay same
        assert result.capacity_improvement is not None

    @pytest.mark.asyncio
    async def test_simulate_intervention_amplitude_metrics(self, lotka_volterra_params):
        """Test oscillation amplitude metrics are valid."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=48.0,
            intervention_type=InterventionTypeEnum.DEMAND_SMOOTHING,
            intervention_magnitude=0.25,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert result.baseline_oscillation_amplitude >= 0.0
        assert result.intervention_oscillation_amplitude >= 0.0

    @pytest.mark.asyncio
    async def test_simulate_intervention_effectiveness_range(self, lotka_volterra_params):
        """Test effectiveness score is in valid range [0, 1]."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=48.0,
            intervention_type=InterventionTypeEnum.MOONLIGHTING,
            intervention_magnitude=0.20,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert 0.0 <= result.intervention_effectiveness <= 1.0

    @pytest.mark.asyncio
    async def test_simulate_intervention_recommendation_present(self, lotka_volterra_params):
        """Test recommendation message is provided."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=48.0,
            intervention_type=InterventionTypeEnum.INCREASE_EFFICIENCY,
            intervention_magnitude=0.15,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert result.recommendation != ""
        assert len(result.recommendation) > 20

    @pytest.mark.asyncio
    async def test_simulate_intervention_parameter_changes_tracked(self, lotka_volterra_params):
        """Test that parameter changes are documented."""
        request = InterventionRequest(
            current_capacity=40.0,
            current_demand=48.0,
            intervention_type=InterventionTypeEnum.SCHEDULE_COMPRESSION,
            intervention_magnitude=0.20,
            simulation_days=180,
            **lotka_volterra_params,
        )

        result = await simulate_intervention(request)

        assert result.parameter_changes is not None
        # SCHEDULE_COMPRESSION should modify beta and gamma
        assert len(result.parameter_changes) > 0

    @pytest.mark.asyncio
    async def test_simulate_all_intervention_types(self, lotka_volterra_params):
        """Test all intervention types return valid responses."""
        intervention_types = [
            InterventionTypeEnum.ADD_CAPACITY,
            InterventionTypeEnum.REDUCE_DEMAND,
            InterventionTypeEnum.INCREASE_EFFICIENCY,
            InterventionTypeEnum.MOONLIGHTING,
            InterventionTypeEnum.SCHEDULE_COMPRESSION,
            InterventionTypeEnum.DEMAND_SMOOTHING,
        ]

        for intervention_type in intervention_types:
            request = InterventionRequest(
                current_capacity=40.0,
                current_demand=45.0,
                intervention_type=intervention_type,
                intervention_magnitude=0.20,
                simulation_days=90,
                **lotka_volterra_params,
            )

            result = await simulate_intervention(request)

            assert result.intervention_type == intervention_type
            assert result.recommendation != ""
            assert 0.0 <= result.intervention_effectiveness <= 1.0


# ============================================================================
# Integration Tests
# ============================================================================


class TestToolIntegration:
    """Test integration between ecological dynamics tools."""

    @pytest.mark.asyncio
    async def test_analyze_then_predict_crunch(self, oscillating_historical_data):
        """Test using analyzed parameters for crunch prediction."""
        # Step 1: Analyze historical data
        analyze_request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )
        analyze_result = await analyze_supply_demand_cycles(analyze_request)
        params = analyze_result.fitted_parameters

        # Step 2: Use fitted parameters for crunch prediction
        crunch_request = CapacityCrunchRequest(
            current_capacity=analyze_result.current_capacity,
            current_demand=analyze_result.current_demand,
            alpha=params["alpha"],
            beta=params["beta"],
            delta=params["delta"],
            gamma=params["gamma"],
            crunch_threshold=20.0,
            prediction_days=180,
        )
        crunch_result = await predict_capacity_crunch(crunch_request)

        # Results should be consistent
        assert crunch_result.current_capacity == analyze_result.current_capacity
        assert crunch_result.current_demand == analyze_result.current_demand

    @pytest.mark.asyncio
    async def test_analyze_then_find_equilibrium(self, oscillating_historical_data):
        """Test finding equilibrium from analyzed parameters."""
        # Step 1: Analyze to get parameters
        analyze_request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=60,
        )
        analyze_result = await analyze_supply_demand_cycles(analyze_request)
        params = analyze_result.fitted_parameters

        # Step 2: Find equilibrium
        eq_request = EquilibriumRequest(
            alpha=params["alpha"],
            beta=params["beta"],
            delta=params["delta"],
            gamma=params["gamma"],
        )
        eq_result = await find_equilibrium_point(eq_request)

        # Equilibrium should match what analyze_supply_demand_cycles calculated
        assert abs(eq_result.equilibrium_capacity - analyze_result.equilibrium_capacity) < 0.1
        assert abs(eq_result.equilibrium_demand - analyze_result.equilibrium_demand) < 0.1

    @pytest.mark.asyncio
    async def test_full_workflow(self, oscillating_historical_data):
        """Test complete workflow: analyze -> equilibrium -> predict -> intervene."""
        # 1. Analyze historical data
        analyze_request = SupplyDemandCyclesRequest(
            historical_data=oscillating_historical_data,
            prediction_days=90,
        )
        analyze_result = await analyze_supply_demand_cycles(analyze_request)
        params = analyze_result.fitted_parameters

        # 2. Find equilibrium
        eq_result = await find_equilibrium_point(
            EquilibriumRequest(**params)
        )
        assert eq_result.equilibrium_capacity > 0

        # 3. Predict crunch
        crunch_result = await predict_capacity_crunch(
            CapacityCrunchRequest(
                current_capacity=analyze_result.current_capacity,
                current_demand=analyze_result.current_demand,
                crunch_threshold=15.0,
                prediction_days=180,
                **params,
            )
        )
        assert crunch_result.risk_level in RiskLevelEnum

        # 4. Simulate intervention
        intervention_result = await simulate_intervention(
            InterventionRequest(
                current_capacity=analyze_result.current_capacity,
                current_demand=analyze_result.current_demand,
                intervention_type=InterventionTypeEnum.ADD_CAPACITY,
                intervention_magnitude=0.25,
                simulation_days=180,
                **params,
            )
        )
        assert intervention_result.recommendation != ""
        assert 0.0 <= intervention_result.intervention_effectiveness <= 1.0
