#!/usr/bin/env python3
"""
Quick test of Lotka-Volterra ecological dynamics tools.

This script demonstrates the four MCP tools for predator-prey modeling
of schedule supply/demand dynamics.
"""

import asyncio
from datetime import date, timedelta

# Import the tool functions directly
from src.scheduler_mcp.tools.ecological_dynamics_tools import (
    CapacityCrunchRequest,
    EquilibriumRequest,
    HistoricalDataPoint,
    InterventionRequest,
    InterventionTypeEnum,
    SupplyDemandCyclesRequest,
    analyze_supply_demand_cycles,
    find_equilibrium_point,
    predict_capacity_crunch,
    simulate_intervention,
)


async def test_analyze_cycles():
    """Test supply/demand cycle analysis."""
    print("\n" + "="*70)
    print("TEST 1: Analyze Supply/Demand Cycles")
    print("="*70)

    # Create synthetic historical data with oscillating pattern
    start_date = date(2025, 1, 1)
    data_points = []

    for i in range(20):
        # Simulate oscillations: capacity and demand cycle
        week = i
        capacity = 45 + 10 * ((-1) ** (i // 3))  # Oscillates between 35-55
        demand = 42 + 8 * ((-1) ** ((i + 2) // 3))  # Oscillates between 34-50, phase shifted

        data_points.append(
            HistoricalDataPoint(
                date=start_date + timedelta(weeks=week),
                capacity=float(capacity),
                demand=float(demand),
            )
        )

    request = SupplyDemandCyclesRequest(
        historical_data=data_points,
        prediction_days=90,
    )

    result = await analyze_supply_demand_cycles(request)

    print(f"Data points analyzed: {result.data_points}")
    print("Fitted parameters:")
    print(f"  α (capacity growth): {result.fitted_parameters['alpha']:.4f}")
    print(f"  β (consumption rate): {result.fitted_parameters['beta']:.4f}")
    print(f"  δ (demand amplification): {result.fitted_parameters['delta']:.4f}")
    print(f"  γ (demand decay): {result.fitted_parameters['gamma']:.4f}")
    print(f"R² goodness of fit: {result.r_squared:.4f}")
    print(f"Equilibrium capacity: {result.equilibrium_capacity:.2f}")
    print(f"Equilibrium demand: {result.equilibrium_demand:.2f}")
    print(f"Oscillation period: {result.oscillation_period_days:.1f} days")
    print(f"System stability: {result.system_stability}")
    print(f"\nInterpretation: {result.ecological_interpretation}")

    return result.fitted_parameters


async def test_predict_crunch(params):
    """Test capacity crunch prediction."""
    print("\n" + "="*70)
    print("TEST 2: Predict Capacity Crunch")
    print("="*70)

    request = CapacityCrunchRequest(
        current_capacity=40.0,
        current_demand=48.0,
        alpha=params['alpha'],
        beta=params['beta'],
        delta=params['delta'],
        gamma=params['gamma'],
        crunch_threshold=20.0,
        prediction_days=180,
    )

    result = await predict_capacity_crunch(request)

    print(f"Current capacity: {result.current_capacity:.1f}")
    print(f"Current demand: {result.current_demand:.1f}")
    print(f"Equilibrium capacity: {result.equilibrium_capacity:.1f}")
    print(f"Capacity deficit: {result.capacity_deficit:.1f}")
    print(f"Risk level: {result.risk_level}")

    if result.days_until_crunch:
        print(f"⚠️  Days until crunch: {result.days_until_crunch}")
        print(f"Crunch date: {result.crunch_date}")
    else:
        print("✓ No crunch predicted in forecast window")

    print(f"Minimum capacity: {result.minimum_capacity:.1f} on {result.minimum_capacity_date}")
    print(f"Will recover: {result.will_recover}")
    print(f"\nMitigation urgency: {result.mitigation_urgency}")


async def test_equilibrium(params):
    """Test equilibrium point calculation."""
    print("\n" + "="*70)
    print("TEST 3: Find Equilibrium Point")
    print("="*70)

    request = EquilibriumRequest(
        alpha=params['alpha'],
        beta=params['beta'],
        delta=params['delta'],
        gamma=params['gamma'],
    )

    result = await find_equilibrium_point(request)

    print(f"Equilibrium capacity (x*): {result.equilibrium_capacity:.2f}")
    print(f"Equilibrium demand (y*): {result.equilibrium_demand:.2f}")
    print(f"Oscillation period: {result.oscillation_period_days:.1f} days")
    print(f"Is stable: {result.is_stable}")
    print(f"\nInterpretation: {result.ecological_interpretation}")
    print("\nParameter sensitivity:")
    for param, effect in result.parameter_sensitivity.items():
        print(f"  {param}: {effect}")


async def test_intervention(params):
    """Test intervention simulation."""
    print("\n" + "="*70)
    print("TEST 4: Simulate Intervention")
    print("="*70)

    request = InterventionRequest(
        current_capacity=40.0,
        current_demand=48.0,
        alpha=params['alpha'],
        beta=params['beta'],
        delta=params['delta'],
        gamma=params['gamma'],
        intervention_type=InterventionTypeEnum.ADD_CAPACITY,
        intervention_magnitude=0.25,  # 25% capacity increase
        intervention_start_day=0,
        intervention_duration_days=90,
        simulation_days=180,
    )

    result = await simulate_intervention(request)

    print(f"Intervention: {result.intervention_type} @ {result.intervention_magnitude:.0%}")
    print("\nBaseline (no intervention):")
    print(f"  Min capacity: {result.baseline_min_capacity:.1f}")
    print(f"  Oscillation amplitude: {result.baseline_oscillation_amplitude:.1f}")
    print("\nWith intervention:")
    print(f"  Min capacity: {result.intervention_min_capacity:.1f}")
    print(f"  Oscillation amplitude: {result.intervention_oscillation_amplitude:.1f}")
    print("\nImpact:")
    print(f"  Capacity improvement: +{result.capacity_improvement:.1f}")
    print(f"  Amplitude reduction: -{result.amplitude_reduction:.1f}")
    print(f"  Effectiveness score: {result.intervention_effectiveness:.2%}")
    print(f"\n{result.recommendation}")


async def main():
    """Run all tests."""
    print("\n╔══════════════════════════════════════════════════════════════════════╗")
    print("║      Lotka-Volterra Ecological Dynamics Tools - Test Suite          ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    try:
        # Test 1: Analyze historical cycles
        params = await test_analyze_cycles()

        # Test 2: Predict capacity crunch
        await test_predict_crunch(params)

        # Test 3: Find equilibrium
        await test_equilibrium(params)

        # Test 4: Simulate intervention
        await test_intervention(params)

        print("\n" + "="*70)
        print("✓ All tests completed successfully!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
