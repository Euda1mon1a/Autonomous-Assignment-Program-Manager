"""
Example usage patterns for time crystal anti-churn module.

These examples demonstrate how to integrate anti-churn objectives
into the scheduling workflow.
"""

from datetime import datetime
from uuid import UUID, uuid4

from app.models.assignment import Assignment
from app.scheduling.constraints.base import ConstraintResult
from app.scheduling.periodicity import (
    ScheduleSnapshot,
    calculate_schedule_rigidity,
    estimate_churn_impact,
    hamming_distance,
    time_crystal_objective,
)


# Example 1: Basic Rigidity Check
# ================================


def example_basic_rigidity_check() -> float:
    """
    Check if proposed schedule changes too much from current.

    Use case: Before publishing a regenerated schedule, verify it
    doesn't disrupt too many residents.
    """
    # Current schedule (from database)
    current_assignments = [
        Assignment(
            person_id=uuid4(),
            block_id=uuid4(),
            rotation_template_id=uuid4(),
        ),
        # ... more assignments
    ]

    # Proposed schedule (from solver)
    proposed_tuples = [
        (uuid4(), uuid4(), uuid4()),  # (person_id, block_id, template_id)
        # ... more assignments
    ]

    # Create snapshots
    current = ScheduleSnapshot.from_assignments(current_assignments)
    proposed = ScheduleSnapshot.from_tuples(proposed_tuples)

    # Check rigidity
    rigidity = calculate_schedule_rigidity(proposed, current)

    if rigidity < 0.7:
        print(f"⚠️  Schedule changed significantly (rigidity={rigidity:.2%})")
        print("Consider reviewing changes before publishing")
    else:
        print(f"✅ Schedule is stable (rigidity={rigidity:.2%})")
        print("Safe to publish")

    return rigidity


# Example 2: Detailed Impact Analysis
# ===================================


def example_detailed_impact_analysis() -> dict:
    """
    Get detailed breakdown of schedule changes.

    Use case: Show administrators what will change before committing
    to a new schedule.
    """
    # Create example schedules
    current = ScheduleSnapshot.from_tuples(
        [(uuid4(), uuid4(), uuid4()) for _ in range(100)]
    )

    proposed = ScheduleSnapshot.from_tuples(
        [(uuid4(), uuid4(), uuid4()) for _ in range(100)]
    )

    # Analyze impact
    impact = estimate_churn_impact(current, proposed)

    # Display results
    print("=== Schedule Change Impact ===")
    print(f"Severity: {impact['severity'].upper()}")
    print(f"Total changes: {impact['total_changes']}")
    print(f"Affected residents: {impact['affected_people']}")
    print(f"Worst-case (max changes per person): {impact['max_person_churn']}")
    print(f"Average changes per affected person: {impact['mean_person_churn']:.1f}")
    print(f"Overall rigidity: {impact['rigidity']:.2%}")
    print(f"\nRecommendation: {impact['recommendation']}")

    return impact


# Example 3: Time Crystal Objective Function
# ==========================================


def example_time_crystal_objective() -> tuple[float, float]:
    """
    Use time crystal objective to score proposed schedules.

    Use case: When evaluating multiple solver results, choose the one
    with best balance of constraint satisfaction and stability.
    """
    current = ScheduleSnapshot.from_tuples(
        [(uuid4(), uuid4(), uuid4()) for _ in range(50)]
    )

    # Option A: High churn but perfect constraints
    option_a = ScheduleSnapshot.from_tuples(
        [
            (uuid4(), uuid4(), uuid4())
            for _ in range(50)  # Completely different
        ]
    )
    constraints_a = [ConstraintResult(satisfied=True, penalty=0.0)]

    # Option B: Low churn but one soft constraint violation
    option_b_tuples = list(current.assignments)[:45]  # Keep 90% the same
    option_b_tuples.extend(
        [
            (uuid4(), uuid4(), uuid4())
            for _ in range(5)  # Change 10%
        ]
    )
    option_b = ScheduleSnapshot.from_tuples(option_b_tuples)
    constraints_b = [ConstraintResult(satisfied=True, penalty=2.0)]  # Soft penalty

    # Score both options
    score_a = time_crystal_objective(option_a, current, constraints_a, alpha=0.3)
    score_b = time_crystal_objective(option_b, current, constraints_b, alpha=0.3)

    print("=== Comparing Schedule Options ===")
    print(f"Option A (high churn, perfect constraints): {score_a:.3f}")
    print(f"Option B (low churn, soft penalty): {score_b:.3f}")

    if score_b > score_a:
        print("\n✅ Option B is better - accepts small penalty for stability")
    else:
        print("\n✅ Option A is better - constraints outweigh stability")

    return score_a, score_b


# Example 4: Per-Person Churn Tracking
# ====================================


def example_per_person_churn() -> dict[UUID, int]:
    """
    Identify which residents are most affected by schedule changes.

    Use case: Proactively communicate with residents who will see
    significant changes to their schedule.
    """
    from app.scheduling.periodicity.anti_churn import hamming_distance_by_person

    # Example person IDs
    person_ids = {
        "Dr. Smith": uuid4(),
        "Dr. Jones": uuid4(),
        "Dr. Lee": uuid4(),
    }

    # Current schedule
    current = ScheduleSnapshot.from_tuples(
        [
            (person_ids["Dr. Smith"], uuid4(), uuid4()),
            (person_ids["Dr. Smith"], uuid4(), uuid4()),
            (person_ids["Dr. Jones"], uuid4(), uuid4()),
            (person_ids["Dr. Lee"], uuid4(), uuid4()),
            (person_ids["Dr. Lee"], uuid4(), uuid4()),
            (person_ids["Dr. Lee"], uuid4(), uuid4()),
        ]
    )

    # Proposed schedule - Dr. Lee has all assignments changed
    proposed = ScheduleSnapshot.from_tuples(
        [
            (person_ids["Dr. Smith"], uuid4(), uuid4()),  # Same
            (person_ids["Dr. Smith"], uuid4(), uuid4()),  # Same
            (person_ids["Dr. Jones"], uuid4(), uuid4()),  # Same
            (person_ids["Dr. Lee"], uuid4(), uuid4()),  # Different
            (person_ids["Dr. Lee"], uuid4(), uuid4()),  # Different
            (person_ids["Dr. Lee"], uuid4(), uuid4()),  # Different
        ]
    )

    # Calculate per-person churn
    churn_by_person = hamming_distance_by_person(current, proposed)

    # Identify high-churn residents
    print("=== Residents Affected by Schedule Changes ===")
    for name, person_id in person_ids.items():
        churn = churn_by_person.get(person_id, 0)
        if churn > 2:
            print(f"⚠️  {name}: {churn} changes (high - notify)")
        elif churn > 0:
            print(f"ℹ️  {name}: {churn} changes")
        else:
            print(f"✅ {name}: No changes")

    return churn_by_person


# Example 5: Tuning Alpha Parameter
# =================================


def example_tuning_alpha() -> None:
    """
    Demonstrate how alpha parameter affects objective function.

    Use case: Help administrators understand the trade-off between
    constraint optimization and schedule stability.
    """
    current = ScheduleSnapshot.from_tuples(
        [(uuid4(), uuid4(), uuid4()) for _ in range(50)]
    )

    # Proposed schedule with moderate churn
    proposed_tuples = list(current.assignments)[:35]  # Keep 70%
    proposed_tuples.extend(
        [
            (uuid4(), uuid4(), uuid4())
            for _ in range(15)  # Change 30%
        ]
    )
    proposed = ScheduleSnapshot.from_tuples(proposed_tuples)

    # Constraints: one soft violation
    constraints = [
        ConstraintResult(satisfied=True, penalty=0.0),
        ConstraintResult(satisfied=True, penalty=1.5),  # Soft penalty
    ]

    print("=== Effect of Alpha Parameter ===")
    print("Alpha | Constraint Weight | Rigidity Weight | Score")
    print("------|-------------------|-----------------|-------")

    for alpha in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        score = time_crystal_objective(proposed, current, constraints, alpha=alpha)
        constraint_weight = (1.0 - alpha) * 100
        rigidity_weight = alpha * 100
        print(
            f"{alpha:.1f}   | {constraint_weight:5.0f}%           | {rigidity_weight:5.0f}%          | {score:.3f}"
        )

    print("\nInterpretation:")
    print("- α=0.0: Pure optimization (ignores stability)")
    print("- α=0.3: Balanced (recommended)")
    print("- α=0.5: Conservative (prefers stability)")
    print("- α=1.0: Pure stability (never changes)")


# Example 6: Integration with Solver
# ==================================


def example_solver_integration(solver_result, current_assignments) -> dict:
    """
    Example of integrating anti-churn into solver workflow.

    Use case: Real integration pattern for SchedulingEngine.
    """
    # Convert current assignments to snapshot
    current_snapshot = ScheduleSnapshot.from_assignments(
        current_assignments,
        metadata={"source": "database", "timestamp": datetime.utcnow()},
    )

    # Convert solver result to snapshot
    proposed_snapshot = ScheduleSnapshot.from_tuples(
        solver_result.assignments,
        metadata={
            "source": "solver",
            "algorithm": solver_result.solver_status,
            "runtime": solver_result.runtime_seconds,
        },
    )

    # Evaluate with time crystal objective
    # (constraint results would come from validator)
    constraint_results = [
        ConstraintResult(satisfied=True, penalty=0.0),
        # ... from ACGME validator, etc.
    ]

    score = time_crystal_objective(
        proposed_snapshot,
        current_snapshot,
        constraint_results,
        alpha=0.3,  # Configurable via environment
    )

    # Check impact
    impact = estimate_churn_impact(current_snapshot, proposed_snapshot)

    # Decision logic
    if impact["severity"] == "critical":
        return {
            "accept": False,
            "reason": "Churn too high",
            "impact": impact,
            "score": score,
        }
    elif score < 0.5:
        return {
            "accept": False,
            "reason": "Score too low (constraints or rigidity failed)",
            "impact": impact,
            "score": score,
        }
    else:
        return {
            "accept": True,
            "impact": impact,
            "score": score,
        }


# Example 7: Monitoring and Alerting
# ==================================


def example_monitoring_setup() -> None:
    """
    Set up monitoring for schedule rigidity over time.

    Use case: Track how often schedules are being regenerated and
    how much they change each time.
    """
    # Pseudo-code for monitoring setup
    print("=== Monitoring Setup ===")
    print("""
    # Prometheus metrics to add:

    schedule_rigidity = Histogram(
        "schedule_rigidity_score",
        "Schedule rigidity after regeneration (0-1)",
        buckets=[0.0, 0.5, 0.7, 0.85, 0.95, 1.0]
    )

    schedule_churn_severity = Counter(
        "schedule_churn_severity_total",
        "Count of schedule generations by churn severity",
        ["severity"]  # minimal, low, moderate, high, critical
    )

    schedule_affected_people = Gauge(
        "schedule_churn_affected_people",
        "Number of people affected by last schedule regeneration"
    )

    # Grafana alerts:

    - Alert: "High Schedule Churn"
      Condition: schedule_rigidity_score < 0.7 for 2 consecutive regenerations
      Action: Notify scheduling coordinator

    - Alert: "Critical Schedule Churn"
      Condition: schedule_churn_severity{severity="critical"} > 0
      Action: Page on-call administrator

    # Usage in code:

    def track_regeneration(current, proposed):
        rigidity = calculate_schedule_rigidity(proposed, current)
        impact = estimate_churn_impact(current, proposed)

        schedule_rigidity.observe(rigidity)
        schedule_churn_severity.labels(severity=impact["severity"]).inc()
        schedule_affected_people.set(impact["affected_people"])
    """)


if __name__ == "__main__":
    print("Running Time Crystal Anti-Churn Examples\n")

    print("Example 1: Basic Rigidity Check")
    print("-" * 50)
    example_basic_rigidity_check()

    print("\n\nExample 2: Detailed Impact Analysis")
    print("-" * 50)
    example_detailed_impact_analysis()

    print("\n\nExample 3: Time Crystal Objective")
    print("-" * 50)
    example_time_crystal_objective()

    print("\n\nExample 4: Per-Person Churn Tracking")
    print("-" * 50)
    example_per_person_churn()

    print("\n\nExample 5: Tuning Alpha Parameter")
    print("-" * 50)
    example_tuning_alpha()

    print("\n\nExample 7: Monitoring Setup")
    print("-" * 50)
    example_monitoring_setup()
