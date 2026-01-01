"""
Example usage of Game Theory MCP tools for Nash equilibrium analysis.

This script demonstrates how to use the game theory tools to analyze
schedule stability and detect coordination failures.
"""

import asyncio


async def example_nash_stability_analysis():
    """Analyze whether a schedule is Nash stable."""
    from scheduler_mcp.tools.game_theory_tools import (
        NashStabilityRequest,
        analyze_nash_stability,
    )

    # Define date range (e.g., Q1 2025)
    start_date = "2025-01-01"
    end_date = "2025-03-31"

    # Create request
    request = NashStabilityRequest(
        start_date=start_date,
        end_date=end_date,
        include_person_details=True,
        deviation_threshold=0.01,  # 1% utility gain threshold
    )

    # Analyze stability
    result = await analyze_nash_stability(request)

    # Display results
    print("=" * 80)
    print("NASH EQUILIBRIUM STABILITY ANALYSIS")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Status: {result.stability_status.value.upper()}")
    print(f"Is Nash Equilibrium: {result.is_nash_equilibrium}")
    print()

    print(f"Total Players: {result.total_players}")
    print(f"Players with Deviations: {result.players_with_deviations}")
    print(f"Deviation Rate: {result.deviation_rate:.1%}")
    print()

    if result.max_deviation_incentive > 0:
        print(f"Max Deviation Incentive: {result.max_deviation_incentive:.3f}")
        print(f"Avg Utility Gain Available: {result.avg_utility_gain_available:.3f}")
        print()

    print("Game Theory Interpretation:")
    print(f"  {result.game_theoretic_interpretation}")
    print()

    if result.recommendations:
        print("Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        print()

    if result.deviations:
        print(f"Top {min(5, len(result.deviations))} Deviations:")
        for i, dev in enumerate(result.deviations[:5], 1):
            print(f"  {i}. {dev.person_id}:")
            print(f"     Current utility: {dev.current_utility:.3f}")
            print(f"     Alternative utility: {dev.alternative_utility:.3f}")
            print(f"     Gain: +{dev.utility_gain:.3f}")
            print(f"     Type: {dev.deviation_type.value}")
            print(f"     Description: {dev.description}")
        print()

    return result


async def example_person_deviation_analysis():
    """Analyze deviation incentives for a specific person."""
    from scheduler_mcp.tools.game_theory_tools import (
        DeviationIncentivesRequest,
        find_deviation_incentives,
    )

    # Example person ID (replace with actual ID)
    person_id = "example-faculty-id"
    start_date = "2025-01-01"
    end_date = "2025-03-31"

    # Create request
    request = DeviationIncentivesRequest(
        person_id=person_id,
        start_date=start_date,
        end_date=end_date,
        include_all_alternatives=False,
        max_alternatives=5,
    )

    # Analyze deviations
    result = await find_deviation_incentives(request)

    # Display results
    print("=" * 80)
    print("PERSON DEVIATION INCENTIVE ANALYSIS")
    print("=" * 80)
    print(f"Person: {result.person_id}")
    print(f"Date Range: {start_date} to {end_date}")
    print()

    print(f"Current Utility: {result.current_utility:.3f}")
    print()

    print("Utility Breakdown:")
    for component, value in result.utility_breakdown.items():
        status = "✓" if value >= 0.7 else "⚠" if value >= 0.5 else "✗"
        print(f"  {status} {component}: {value:.3f}")
    print()

    print(f"Best Alternative Utility: {result.best_alternative_utility:.3f}")
    print(f"Max Utility Gain: {result.max_utility_gain:.3f}")
    print(f"Has Profitable Deviation: {result.has_profitable_deviation}")
    print()

    print(f"Strategic Position: {result.strategic_position}")
    print()

    if result.deviation_incentives:
        print(f"Deviation Incentives ({len(result.deviation_incentives)}):")
        for i, dev in enumerate(result.deviation_incentives, 1):
            print(f"  {i}. {dev.deviation_type.value.upper()}:")
            print(f"     Target: {dev.target_person_id or 'N/A'}")
            print(f"     Utility Gain: +{dev.utility_gain:.3f}")
            print(f"     Description: {dev.description}")
            print(f"     Confidence: {dev.confidence:.2f}")
        print()

    if result.barriers_to_deviation:
        print("Barriers to Deviation:")
        for barrier in result.barriers_to_deviation:
            print(f"  - {barrier}")
        print()

    return result


async def example_coordination_failures():
    """Detect coordination failures preventing Pareto improvements."""
    from scheduler_mcp.tools.game_theory_tools import detect_coordination_failures

    start_date = "2025-01-01"
    end_date = "2025-03-31"
    min_pareto_gain = 0.05

    # Detect failures
    result = await detect_coordination_failures(
        start_date=start_date,
        end_date=end_date,
        min_pareto_gain=min_pareto_gain,
    )

    # Display results
    print("=" * 80)
    print("COORDINATION FAILURE DETECTION")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Minimum Pareto Gain Threshold: {min_pareto_gain:.3f}")
    print()

    print(f"Total Failures Detected: {result.total_failures_detected}")
    print(f"Total Pareto Gain Available: {result.total_pareto_gain_available:.3f}")
    print()

    print("Game Theory Insights:")
    print(f"  {result.game_theoretic_insights}")
    print()

    if result.failures:
        print("Coordination Failures:")
        for i, failure in enumerate(result.failures, 1):
            print(f"\n  {i}. {failure.failure_type.value.upper()}:")
            print(f"     Involved Players: {', '.join(failure.involved_person_ids)}")
            print(f"     Potential Gain: {failure.potential_pareto_gain:.3f}")
            print("     Per-Person Gains:")
            for pid, gain in failure.per_person_gains.items():
                print(f"       - {pid}: +{gain:.3f}")
            print(f"     Barrier: {failure.coordination_barrier}")
            if failure.solution_path:
                print(f"     Solution: {failure.solution_path}")
            print(f"     Confidence: {failure.confidence:.2f}")
        print()

    if result.system_recommendations:
        print("System Recommendations:")
        for i, rec in enumerate(result.system_recommendations, 1):
            print(f"  {i}. {rec}")
        print()

    return result


async def example_utility_calculation():
    """Demonstrate utility calculation with custom weights."""
    from scheduler_mcp.tools.game_theory_tools import (
        calculate_person_utility,
    )

    # Example data (replace with actual data)
    person_id = "example-person"
    assignments = []  # Would contain actual assignments
    all_assignments = {person_id: assignments}

    # Calculate utility with default weights
    utility_default = calculate_person_utility(
        person_id=person_id,
        assignments=assignments,
        all_assignments=all_assignments,
    )

    print("=" * 80)
    print("UTILITY CALCULATION EXAMPLE")
    print("=" * 80)
    print("Default Weights (0.4, 0.3, 0.2, 0.1):")
    print(f"  Workload Fairness: {utility_default.workload_fairness:.3f}")
    print(f"  Preference Satisfaction: {utility_default.preference_satisfaction:.3f}")
    print(f"  Convenience: {utility_default.convenience:.3f}")
    print(f"  Continuity: {utility_default.continuity:.3f}")
    print(f"  Total Utility: {utility_default.total_utility():.3f}")
    print()

    # Calculate utility with custom weights (emphasize workload fairness)
    custom_weights = {
        "workload": 0.5,
        "preference": 0.3,
        "convenience": 0.1,
        "continuity": 0.1,
    }

    utility_custom = calculate_person_utility(
        person_id=person_id,
        assignments=assignments,
        all_assignments=all_assignments,
        weights=custom_weights,
    )

    print("Custom Weights (0.5, 0.3, 0.1, 0.1) - Emphasize Fairness:")
    print(f"  Workload Fairness: {utility_custom.workload_fairness:.3f}")
    print(f"  Preference Satisfaction: {utility_custom.preference_satisfaction:.3f}")
    print(f"  Convenience: {utility_custom.convenience:.3f}")
    print(f"  Continuity: {utility_custom.continuity:.3f}")
    print(f"  Total Utility: {utility_custom.total_utility():.3f}")
    print()

    return utility_default, utility_custom


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("GAME THEORY MCP TOOLS - USAGE EXAMPLES")
    print("=" * 80 + "\n")

    # Example 1: Nash Stability Analysis
    print("\nExample 1: Nash Stability Analysis")
    print("-" * 80)
    await example_nash_stability_analysis()

    # Example 2: Person Deviation Analysis
    print("\nExample 2: Person Deviation Analysis")
    print("-" * 80)
    await example_person_deviation_analysis()

    # Example 3: Coordination Failures
    print("\nExample 3: Coordination Failure Detection")
    print("-" * 80)
    await example_coordination_failures()

    # Example 4: Utility Calculation
    print("\nExample 4: Utility Calculation")
    print("-" * 80)
    await example_utility_calculation()

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
