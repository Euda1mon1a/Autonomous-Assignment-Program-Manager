"""
Example: Catastrophe Theory in Medical Residency Scheduling.

This example demonstrates how to use the catastrophe detector to:
1. Identify critical thresholds in scheduling parameters
2. Predict catastrophic failures before they occur
3. Generate early warning alerts
4. Recommend appropriate defense levels

Use case: Military medical residency during deployment season.
"""

from datetime import datetime, timedelta

from app.resilience.catastrophe_detector import (
    CatastropheAlert,
    CatastropheDetector,
    ParameterState,
)
from app.resilience.defense_in_depth import DefenseInDepth, DefenseLevel


def example_deployment_season_monitoring():
    """
    Example: Monitor scheduling system during deployment season.

    Deployment season increases coverage demand and constraint strictness,
    potentially pushing the system toward catastrophe.
    """
    print("=" * 70)
    print("CATASTROPHE THEORY EXAMPLE: DEPLOYMENT SEASON MONITORING")
    print("=" * 70)
    print()

    # Initialize catastrophe detector
    detector = CatastropheDetector(
        demand_range=(0.5, 1.2), strictness_range=(0.0, 1.0)
    )

    # Initialize defense in depth
    defense = DefenseInDepth()

    print("Step 1: Mapping constraint space...")
    print("-" * 70)

    # Map the feasibility surface
    surface = detector.map_constraint_space(resolution=(30, 30))

    print(f"✓ Surface mapped: {surface.grid_resolution[0]}x{surface.grid_resolution[1]} grid")
    print(f"  Computation time: {surface.computation_time_seconds:.2f}s")
    print()

    print("Step 2: Detecting catastrophe boundaries...")
    print("-" * 70)

    # Detect cusp catastrophe
    analysis = detector.detect_catastrophe_cusp(surface)

    if analysis.cusp_exists:
        print(f"✓ Cusp catastrophe detected!")
        print(f"  Cusp center: {analysis.cusp_center}")
        print(f"  Cusp score: {analysis.cusp_score:.3f}")
        print(f"  Hysteresis gap: {analysis.hysteresis_gap:.3f}")
    else:
        print("✓ No clear cusp detected (system may be stable)")

    print()

    # Find critical thresholds
    thresholds = detector.find_critical_thresholds(surface)
    print("  Critical thresholds:")
    for key, value in thresholds.items():
        print(f"    {key}: {value:.3f}")
    print()

    print("Step 3: Simulating deployment season trajectory...")
    print("-" * 70)

    # Simulate progression through deployment season
    trajectory = []
    base_date = datetime.now()

    scenarios = [
        (0.70, 0.40, "Normal operations"),
        (0.75, 0.50, "Deployment notice received"),
        (0.82, 0.60, "First faculty deployed"),
        (0.88, 0.70, "Multiple deployments"),
        (0.93, 0.80, "Peak deployment season"),
    ]

    print("  Month | Demand | Strict | Scenario")
    print("  ------|--------|--------|-----------------------------------")

    for i, (demand, strictness, description) in enumerate(scenarios):
        timestamp = base_date + timedelta(days=30 * i)
        params = ParameterState(
            demand=demand,
            strictness=strictness,
            timestamp=timestamp,
            metadata={"scenario": description},
        )
        trajectory.append(params)

        print(f"  {i+1:5d} | {demand:6.2f} | {strictness:6.2f} | {description}")

    print()

    print("Step 4: Analyzing each time point...")
    print("-" * 70)
    print()

    for i, params in enumerate(trajectory):
        print(f"Month {i+1}: {params.metadata['scenario']}")
        print(f"  Parameters: demand={params.demand:.2f}, strictness={params.strictness:.2f}")

        # Compute distance to catastrophe
        distance = detector.compute_distance_to_catastrophe(params, analysis)
        print(f"  Distance to catastrophe: {distance:.3f}")

        # Generate alert if needed
        alert = detector.create_alert(params, analysis, distance)

        if alert:
            print(f"  ⚠️  ALERT: {alert.severity.upper()}")
            print(f"      Region: {alert.region.value}")
            print(f"      Message: {alert.message}")
            print(f"      Recommended defense level: {alert.recommended_defense_level.name}")

            # Activate appropriate defense level
            defense_level = alert.recommended_defense_level
            print(f"      → Activating defense level: {defense_level.name}")
        else:
            print(f"  ✓ System safe (no alert)")

        print()

    print("Step 5: Predicting future failures...")
    print("-" * 70)

    # Predict failure from trajectory
    prediction = detector.predict_system_failure(
        trajectory=trajectory, cusp_analysis=analysis, horizon=2
    )

    print(f"Prediction results:")
    print(f"  Will fail: {prediction.will_fail}")
    print(f"  Confidence: {prediction.confidence:.2%}")
    print(f"  Current state: {prediction.current_state.value}")
    print(f"  Predicted state: {prediction.predicted_state.value}")
    print(f"  Trajectory direction: {prediction.trajectory_direction}")
    print(f"  Distance to catastrophe: {prediction.distance_to_catastrophe:.3f}")

    if prediction.time_to_failure is not None:
        print(f"  Time to failure: {prediction.time_to_failure:.1f} time steps")

    print()
    print(f"  Defense level needed: {prediction.defense_level_needed.name}")
    print()

    if prediction.recommended_actions:
        print(f"  Recommended actions:")
        for action in prediction.recommended_actions:
            print(f"    • {action}")
    print()

    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


def example_hysteresis_demonstration():
    """
    Example: Demonstrate hysteresis in schedule recovery.

    Shows that it's easier to prevent failure than to recover from it.
    """
    print()
    print("=" * 70)
    print("HYSTERESIS DEMONSTRATION")
    print("=" * 70)
    print()

    detector = CatastropheDetector()
    surface = detector.map_constraint_space(resolution=(25, 25))
    analysis = detector.detect_catastrophe_cusp(surface)

    if not analysis.cusp_exists or analysis.hysteresis_gap < 0.05:
        print("Insufficient hysteresis detected for demonstration")
        return

    print(f"Hysteresis gap: {analysis.hysteresis_gap:.3f}")
    print()
    print("This means:")
    print(f"  • When demand INCREASES, system fails at higher threshold")
    print(f"  • When demand DECREASES, system recovers at lower threshold")
    print(f"  • Gap represents the 'cost' of letting system fail")
    print()
    print("Implications for scheduling:")
    print(f"  ✓ Prevention is easier than cure")
    print(f"  ✓ Build buffers BEFORE deployment season")
    print(f"  ✓ Recovery requires larger capacity reduction")
    print()


def example_multi_scenario_comparison():
    """
    Example: Compare different scheduling scenarios.

    Tests how different policies affect catastrophe risk.
    """
    print("=" * 70)
    print("SCENARIO COMPARISON")
    print("=" * 70)
    print()

    detector = CatastropheDetector()
    surface = detector.map_constraint_space(resolution=(20, 20))
    analysis = detector.detect_catastrophe_cusp(surface)

    scenarios = {
        "Aggressive (high demand, strict)": ParameterState(0.95, 0.85),
        "Balanced (moderate demand/strict)": ParameterState(0.80, 0.60),
        "Conservative (low demand, relaxed)": ParameterState(0.65, 0.40),
    }

    print(f"{'Scenario':<40} | Distance | Risk Level")
    print(f"{'-'*40}-|----------|------------")

    for name, params in scenarios.items():
        distance = detector.compute_distance_to_catastrophe(params, analysis)

        if distance > 0.5:
            risk = "LOW"
        elif distance > 0.3:
            risk = "MEDIUM"
        elif distance > 0.15:
            risk = "HIGH"
        else:
            risk = "CRITICAL"

        print(f"{name:<40} | {distance:8.3f} | {risk}")

    print()


if __name__ == "__main__":
    # Run all examples
    example_deployment_season_monitoring()
    example_hysteresis_demonstration()
    example_multi_scenario_comparison()
