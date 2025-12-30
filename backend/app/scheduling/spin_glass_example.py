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


def demonstrate_spin_glass_scheduling():
    """
    Demonstrate complete spin glass scheduling workflow.

    This example shows how to use the spin glass model to:
    - Identify conflicting constraints (frustration analysis)
    - Generate diverse near-optimal solutions (replica ensemble)
    - Analyze solution space structure (energy landscape)
    - Visualize replica symmetry breaking
    """

    ***REMOVED*** Step 1: Create scheduling context with your data
    ***REMOVED*** (In practice, this would come from the database)
    print("=" * 80)
    print("SPIN GLASS SCHEDULING DEMONSTRATION")
    print("=" * 80)
    print()

    ***REMOVED*** Placeholder context - replace with actual data
    ***REMOVED*** context = SchedulingContext(
    ***REMOVED***     residents=residents,
    ***REMOVED***     faculty=faculty,
    ***REMOVED***     blocks=blocks,
    ***REMOVED***     templates=templates,
    ***REMOVED***     availability=availability_matrix,
    ***REMOVED***     existing_assignments=[],
    ***REMOVED*** )

    ***REMOVED*** Step 2: Set up constraint manager
    ***REMOVED*** constraint_manager = ConstraintManager.create_default()
    ***REMOVED*** constraints = constraint_manager.get_enabled_constraints()

    print("Step 1: Initialize Spin Glass Scheduler")
    print("-" * 80)
    print("Temperature: Controls solution diversity")
    print("  - High T (>2.0): More diverse replicas, explore widely")
    print("  - Low T (<0.5):  Less diverse replicas, exploit local minima")
    print()

    ***REMOVED*** For demonstration purposes, we'll use a simplified setup
    ***REMOVED*** scheduler = SpinGlassScheduler(
    ***REMOVED***     context=context,
    ***REMOVED***     constraints=constraints,
    ***REMOVED***     temperature=1.0,  ***REMOVED*** Moderate temperature for balanced exploration
    ***REMOVED***     random_seed=42,   ***REMOVED*** For reproducibility
    ***REMOVED*** )

    print("Step 2: Analyze Constraint Frustration")
    print("-" * 80)
    print("Frustration occurs when constraints conflict (e.g., equity vs preferences)")
    print()

    ***REMOVED*** frustration_index = scheduler.compute_frustration_index()
    ***REMOVED*** print(f"Frustration Index: {frustration_index:.3f}")
    ***REMOVED*** if frustration_index > 0.7:
    ***REMOVED***     print("⚠ WARNING: Highly frustrated system - perfect solution unlikely")
    ***REMOVED***     print("  Consider relaxing some constraints or adjusting weights")
    ***REMOVED*** elif frustration_index > 0.4:
    ***REMOVED***     print("ℹ MODERATE: Some constraint conflicts present")
    ***REMOVED*** else:
    ***REMOVED***     print("✓ LOW: Constraints are mostly compatible")
    ***REMOVED*** print()

    print("Step 3: Generate Replica Schedules")
    print("-" * 80)
    print("Generating ensemble of near-optimal solutions...")
    print()

    ***REMOVED*** replicas = scheduler.generate_replica_schedules(n_replicas=20)
    ***REMOVED*** energies = [r.energy for r in replicas]
    ***REMOVED*** print(f"Generated {len(replicas)} replica schedules")
    ***REMOVED*** print(f"Energy range: {min(energies):.2f} - {max(energies):.2f}")
    ***REMOVED*** print(f"Best schedule: Replica {replicas[0].replica_index} (E={replicas[0].energy:.2f})")
    ***REMOVED*** print()

    print("Step 4: Analyze Energy Landscape")
    print("-" * 80)
    print("Mapping solution space structure...")
    print()

    ***REMOVED*** landscape = scheduler.analyze_energy_landscape(replicas)
    ***REMOVED*** print(f"Global Minimum Energy: {landscape.global_minimum_energy:.2f}")
    ***REMOVED*** print(f"Number of Solution Basins: {len(landscape.basin_sizes)}")
    ***REMOVED*** print(f"Glass Transition Temperature: {landscape.glass_transition_temp:.3f}")
    ***REMOVED*** print()

    ***REMOVED*** if len(landscape.frustration_clusters) > 0:
    ***REMOVED***     print("Identified Frustration Clusters:")
    ***REMOVED***     for i, cluster in enumerate(landscape.frustration_clusters[:3]):
    ***REMOVED***         print(f"  {i+1}. {cluster.conflict_type}")
    ***REMOVED***         print(f"     Frustration: {cluster.frustration_index:.3f}")
    ***REMOVED***         print(f"     Suggestions: {cluster.resolution_suggestions[0]}")
    ***REMOVED*** print()

    print("Step 5: Analyze Replica Symmetry Breaking (RSB)")
    print("-" * 80)
    print("Measuring solution diversity...")
    print()

    ***REMOVED*** rsb_analysis = scheduler.compute_replica_symmetry_analysis(replicas)
    ***REMOVED*** print(f"RSB Order Parameter: {rsb_analysis.rsb_order_parameter:.3f}")
    ***REMOVED*** print(f"Diversity Score: {rsb_analysis.diversity_score:.3f}")
    ***REMOVED*** print(f"Mean Overlap: {rsb_analysis.mean_overlap:.3f}")
    ***REMOVED*** print()

    ***REMOVED*** if rsb_analysis.diversity_score > 0.7:
    ***REMOVED***     print("✓ HIGH DIVERSITY: Many viable solutions available")
    ***REMOVED***     print("  → Robust to perturbations, good for contingency planning")
    ***REMOVED*** elif rsb_analysis.diversity_score > 0.4:
    ***REMOVED***     print("ℹ MODERATE DIVERSITY: Some solution variety")
    ***REMOVED*** else:
    ***REMOVED***     print("⚠ LOW DIVERSITY: Few distinct solutions")
    ***REMOVED***     print("  → Schedule may be brittle, consider relaxing constraints")
    ***REMOVED*** print()

    print("Step 6: Visualization (Optional)")
    print("-" * 80)
    print("Generating visualizations...")
    print()

    ***REMOVED*** ***REMOVED*** Visualize energy landscape
    ***REMOVED*** plot_energy_landscape(replicas, landscape, "spin_glass_energy.png")
    ***REMOVED*** print("✓ Energy landscape plot saved to spin_glass_energy.png")

    ***REMOVED*** ***REMOVED*** Visualize Parisi overlap matrix
    ***REMOVED*** plot_parisi_overlap_matrix(rsb_analysis, "parisi_overlap.png")
    ***REMOVED*** print("✓ Parisi overlap matrix saved to parisi_overlap.png")

    ***REMOVED*** ***REMOVED*** Visualize overlap distribution
    ***REMOVED*** plot_overlap_distribution(rsb_analysis, "overlap_distribution.png")
    ***REMOVED*** print("✓ Overlap distribution saved to overlap_distribution.png")

    ***REMOVED*** ***REMOVED*** Visualize solution basins
    ***REMOVED*** plot_solution_basins(replicas, landscape, "solution_basins.png")
    ***REMOVED*** print("✓ Solution basins plot saved to solution_basins.png")

    ***REMOVED*** ***REMOVED*** Export summary JSON
    ***REMOVED*** export_landscape_summary(
    ***REMOVED***     replicas, landscape, rsb_analysis, "landscape_summary.json"
    ***REMOVED*** )
    ***REMOVED*** print("✓ Landscape summary exported to landscape_summary.json")
    ***REMOVED*** print()

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


def find_glass_transition_example():
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

    ***REMOVED*** scheduler = SpinGlassScheduler(context, constraints, temperature=1.0)
    ***REMOVED*** critical_density = scheduler.find_glass_transition_threshold(
    ***REMOVED***     constraint_density_range=(0.5, 2.0),
    ***REMOVED***     n_samples=10,
    ***REMOVED*** )

    ***REMOVED*** print(f"Critical constraint density: {critical_density:.2f}")
    ***REMOVED*** print()
    ***REMOVED*** print("Interpretation:")
    ***REMOVED*** if critical_density < 1.0:
    ***REMOVED***     print("  System is highly constrained - close to glass transition")
    ***REMOVED***     print("  Adding more constraints may cause rigidity")
    ***REMOVED*** else:
    ***REMOVED***     print("  System has flexibility - can accommodate more constraints")

    print("This analysis helps predict when adding new constraints")
    print("will cause scheduling flexibility to vanish.")


def compare_replicas_example():
    """
    Example: Compare multiple replica schedules to find trade-offs.
    """
    print()
    print("=" * 80)
    print("REPLICA COMPARISON FOR TRADE-OFF ANALYSIS")
    print("=" * 80)
    print()

    ***REMOVED*** scheduler = SpinGlassScheduler(context, constraints, temperature=1.0)
    ***REMOVED*** replicas = scheduler.generate_replica_schedules(n_replicas=10)

    ***REMOVED*** ***REMOVED*** Sort by different criteria
    ***REMOVED*** by_energy = sorted(replicas, key=lambda r: r.energy)
    ***REMOVED*** by_magnetization = sorted(replicas, key=lambda r: -r.magnetization)

    ***REMOVED*** print("Top 3 by Energy (Constraint Violations):")
    ***REMOVED*** for i, replica in enumerate(by_energy[:3]):
    ***REMOVED***     print(f"  {i+1}. {replica.schedule_id}: E={replica.energy:.2f}")

    ***REMOVED*** print()
    ***REMOVED*** print("Top 3 by Magnetization (Soft Constraint Alignment):")
    ***REMOVED*** for i, replica in enumerate(by_magnetization[:3]):
    ***REMOVED***     print(f"  {i+1}. {replica.schedule_id}: M={replica.magnetization:.3f}")

    ***REMOVED*** ***REMOVED*** Compare pairwise
    ***REMOVED*** best_energy = by_energy[0]
    ***REMOVED*** best_magnetization = by_magnetization[0]

    ***REMOVED*** if best_energy.schedule_id != best_magnetization.schedule_id:
    ***REMOVED***     overlap = scheduler.compute_parisi_overlap(best_energy, best_magnetization)
    ***REMOVED***     print()
    ***REMOVED***     print(f"Best-energy vs best-magnetization overlap: {overlap:.3f}")
    ***REMOVED***     if overlap < 0.5:
    ***REMOVED***         print("  → These schedules are very different!")
    ***REMOVED***         print("  → Trade-off: minimize violations vs maximize preferences")

    print("Use replica comparison to:")
    print("- Identify trade-offs between competing objectives")
    print("- Present multiple options to stakeholders")
    print("- Maintain backup schedules for contingencies")


if __name__ == "__main__":
    ***REMOVED*** Run demonstration
    demonstrate_spin_glass_scheduling()

    ***REMOVED*** Additional examples
    ***REMOVED*** find_glass_transition_example()
    ***REMOVED*** compare_replicas_example()

    print()
    print("For production use, uncomment the actual code blocks")
    print("and provide real scheduling context and constraints.")
