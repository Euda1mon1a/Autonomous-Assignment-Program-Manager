"""
Example usage of Spin Glass Constraint Model for residency scheduling.

This example demonstrates how to:
1. Set up a spin glass scheduler
2. Analyze constraint frustration
3. Generate replica schedules
4. Analyze the energy landscape
5. Visualize results
"""

from datetime import date, timedelta

from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)
from app.scheduling.spin_glass_model import SpinGlassScheduler
from app.scheduling.spin_glass_visualizer import (
    export_landscape_summary,
    plot_energy_landscape,
    plot_overlap_distribution,
    plot_parisi_overlap_matrix,
    plot_solution_basins,
)


def demonstrate_spin_glass_scheduling() -> None:
    """
    Demonstrate complete spin glass scheduling workflow.

    This example shows how to use the spin glass model to:
    - Identify conflicting constraints (frustration analysis)
    - Generate diverse near-optimal solutions (replica ensemble)
    - Analyze solution space structure (energy landscape)
    - Visualize replica symmetry breaking
    """

    # Step 1: Create scheduling context with your data
    # (In practice, this would come from the database)
    print("=" * 80)
    print("SPIN GLASS SCHEDULING DEMONSTRATION")
    print("=" * 80)
    print()

    # Placeholder context - replace with actual data
    # context = SchedulingContext(
    #     residents=residents,
    #     faculty=faculty,
    #     blocks=blocks,
    #     templates=templates,
    #     availability=availability_matrix,
    #     existing_assignments=[],
    # )

    # Step 2: Set up constraint manager
    # constraint_manager = ConstraintManager.create_default()
    # constraints = constraint_manager.get_enabled_constraints()

    print("Step 1: Initialize Spin Glass Scheduler")
    print("-" * 80)
    print("Temperature: Controls solution diversity")
    print("  - High T (>2.0): More diverse replicas, explore widely")
    print("  - Low T (<0.5):  Less diverse replicas, exploit local minima")
    print()

    # For demonstration purposes, we'll use a simplified setup
    # scheduler = SpinGlassScheduler(
    #     context=context,
    #     constraints=constraints,
    #     temperature=1.0,  # Moderate temperature for balanced exploration
    #     random_seed=42,   # For reproducibility
    # )

    print("Step 2: Analyze Constraint Frustration")
    print("-" * 80)
    print("Frustration occurs when constraints conflict (e.g., equity vs preferences)")
    print()

    # frustration_index = scheduler.compute_frustration_index()
    # print(f"Frustration Index: {frustration_index:.3f}")
    # if frustration_index > 0.7:
    #     print("⚠ WARNING: Highly frustrated system - perfect solution unlikely")
    #     print("  Consider relaxing some constraints or adjusting weights")
    # elif frustration_index > 0.4:
    #     print("ℹ MODERATE: Some constraint conflicts present")
    # else:
    #     print("✓ LOW: Constraints are mostly compatible")
    # print()

    print("Step 3: Generate Replica Schedules")
    print("-" * 80)
    print("Generating ensemble of near-optimal solutions...")
    print()

    # replicas = scheduler.generate_replica_schedules(n_replicas=20)
    # energies = [r.energy for r in replicas]
    # print(f"Generated {len(replicas)} replica schedules")
    # print(f"Energy range: {min(energies):.2f} - {max(energies):.2f}")
    # print(f"Best schedule: Replica {replicas[0].replica_index} (E={replicas[0].energy:.2f})")
    # print()

    print("Step 4: Analyze Energy Landscape")
    print("-" * 80)
    print("Mapping solution space structure...")
    print()

    # landscape = scheduler.analyze_energy_landscape(replicas)
    # print(f"Global Minimum Energy: {landscape.global_minimum_energy:.2f}")
    # print(f"Number of Solution Basins: {len(landscape.basin_sizes)}")
    # print(f"Glass Transition Temperature: {landscape.glass_transition_temp:.3f}")
    # print()

    # if len(landscape.frustration_clusters) > 0:
    #     print("Identified Frustration Clusters:")
    #     for i, cluster in enumerate(landscape.frustration_clusters[:3]):
    #         print(f"  {i+1}. {cluster.conflict_type}")
    #         print(f"     Frustration: {cluster.frustration_index:.3f}")
    #         print(f"     Suggestions: {cluster.resolution_suggestions[0]}")
    # print()

    print("Step 5: Analyze Replica Symmetry Breaking (RSB)")
    print("-" * 80)
    print("Measuring solution diversity...")
    print()

    # rsb_analysis = scheduler.compute_replica_symmetry_analysis(replicas)
    # print(f"RSB Order Parameter: {rsb_analysis.rsb_order_parameter:.3f}")
    # print(f"Diversity Score: {rsb_analysis.diversity_score:.3f}")
    # print(f"Mean Overlap: {rsb_analysis.mean_overlap:.3f}")
    # print()

    # if rsb_analysis.diversity_score > 0.7:
    #     print("✓ HIGH DIVERSITY: Many viable solutions available")
    #     print("  → Robust to perturbations, good for contingency planning")
    # elif rsb_analysis.diversity_score > 0.4:
    #     print("ℹ MODERATE DIVERSITY: Some solution variety")
    # else:
    #     print("⚠ LOW DIVERSITY: Few distinct solutions")
    #     print("  → Schedule may be brittle, consider relaxing constraints")
    # print()

    print("Step 6: Visualization (Optional)")
    print("-" * 80)
    print("Generating visualizations...")
    print()

    # # Visualize energy landscape
    # plot_energy_landscape(replicas, landscape, "spin_glass_energy.png")
    # print("✓ Energy landscape plot saved to spin_glass_energy.png")

    # # Visualize Parisi overlap matrix
    # plot_parisi_overlap_matrix(rsb_analysis, "parisi_overlap.png")
    # print("✓ Parisi overlap matrix saved to parisi_overlap.png")

    # # Visualize overlap distribution
    # plot_overlap_distribution(rsb_analysis, "overlap_distribution.png")
    # print("✓ Overlap distribution saved to overlap_distribution.png")

    # # Visualize solution basins
    # plot_solution_basins(replicas, landscape, "solution_basins.png")
    # print("✓ Solution basins plot saved to solution_basins.png")

    # # Export summary JSON
    # export_landscape_summary(
    #     replicas, landscape, rsb_analysis, "landscape_summary.json"
    # )
    # print("✓ Landscape summary exported to landscape_summary.json")
    # print()

    print("Step 7: Use Results for Decision Making")
    print("-" * 80)
    print("Interpretation Guide:")
    print()
    print("1. LOW FRUSTRATION + HIGH DIVERSITY:")
    print("   → Ideal situation - multiple good solutions available")
    print("   → Safe to choose based on secondary criteria")
    print()
    print("2. LOW FRUSTRATION + LOW DIVERSITY:")
    print("   → Single dominant solution")
    print("   → Schedule may be optimal but brittle")
    print()
    print("3. HIGH FRUSTRATION + HIGH DIVERSITY:")
    print("   → Many solutions but all have some violations")
    print("   → Consider constraint relaxation or manual review")
    print()
    print("4. HIGH FRUSTRATION + LOW DIVERSITY:")
    print("   → Worst case - few solutions and all are problematic")
    print("   → Strongly consider revising constraints")
    print()

    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Integration with existing solvers:")
    print("- Use spin glass analysis to understand constraint conflicts")
    print("- Generate replicas for contingency planning")
    print("- Select best replica based on secondary criteria")
    print("- Monitor diversity to detect rigidity problems early")


def find_glass_transition_example() -> None:
    """
    Example: Find the glass transition point for a constraint system.

    The glass transition marks the point where adding more constraints
    causes the system to "freeze" into a rigid configuration with little
    flexibility.
    """
    print()
    print("=" * 80)
    print("GLASS TRANSITION ANALYSIS")
    print("=" * 80)
    print()

    # scheduler = SpinGlassScheduler(context, constraints, temperature=1.0)
    # critical_density = scheduler.find_glass_transition_threshold(
    #     constraint_density_range=(0.5, 2.0),
    #     n_samples=10,
    # )

    # print(f"Critical constraint density: {critical_density:.2f}")
    # print()
    # print("Interpretation:")
    # if critical_density < 1.0:
    #     print("  System is highly constrained - close to glass transition")
    #     print("  Adding more constraints may cause rigidity")
    # else:
    #     print("  System has flexibility - can accommodate more constraints")

    print("This analysis helps predict when adding new constraints")
    print("will cause scheduling flexibility to vanish.")


def compare_replicas_example() -> None:
    """
    Example: Compare multiple replica schedules to find trade-offs.
    """
    print()
    print("=" * 80)
    print("REPLICA COMPARISON FOR TRADE-OFF ANALYSIS")
    print("=" * 80)
    print()

    # scheduler = SpinGlassScheduler(context, constraints, temperature=1.0)
    # replicas = scheduler.generate_replica_schedules(n_replicas=10)

    # # Sort by different criteria
    # by_energy = sorted(replicas, key=lambda r: r.energy)
    # by_magnetization = sorted(replicas, key=lambda r: -r.magnetization)

    # print("Top 3 by Energy (Constraint Violations):")
    # for i, replica in enumerate(by_energy[:3]):
    #     print(f"  {i+1}. {replica.schedule_id}: E={replica.energy:.2f}")

    # print()
    # print("Top 3 by Magnetization (Soft Constraint Alignment):")
    # for i, replica in enumerate(by_magnetization[:3]):
    #     print(f"  {i+1}. {replica.schedule_id}: M={replica.magnetization:.3f}")

    # # Compare pairwise
    # best_energy = by_energy[0]
    # best_magnetization = by_magnetization[0]

    # if best_energy.schedule_id != best_magnetization.schedule_id:
    #     overlap = scheduler.compute_parisi_overlap(best_energy, best_magnetization)
    #     print()
    #     print(f"Best-energy vs best-magnetization overlap: {overlap:.3f}")
    #     if overlap < 0.5:
    #         print("  → These schedules are very different!")
    #         print("  → Trade-off: minimize violations vs maximize preferences")

    print("Use replica comparison to:")
    print("- Identify trade-offs between competing objectives")
    print("- Present multiple options to stakeholders")
    print("- Maintain backup schedules for contingencies")


if __name__ == "__main__":
    # Run demonstration
    demonstrate_spin_glass_scheduling()

    # Additional examples
    # find_glass_transition_example()
    # compare_replicas_example()

    print()
    print("For production use, uncomment the actual code blocks")
    print("and provide real scheduling context and constraints.")
