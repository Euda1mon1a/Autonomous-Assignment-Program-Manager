#!/usr/bin/env python3
"""
Demo script showing StabilityMetrics usage.

This script demonstrates how to use the StabilityMetrics module
to analyze schedule stability and identify potential issues.

Run with:
    python examples/stability_metrics_demo.py
"""

from datetime import datetime
from uuid import uuid4


# Mock database session for demonstration
class MockDBSession:
    """Mock database session for demo purposes."""

    pass


def demo_basic_usage():
    """Demonstrate basic StabilityMetrics usage."""
    print("=" * 70)
    print("DEMO 1: Basic Stability Metrics")
    print("=" * 70)

    from app.analytics.stability_metrics import StabilityMetrics

    # Create example metrics
    metrics = StabilityMetrics(
        assignments_changed=15,
        churn_rate=0.12,
        ripple_factor=1.8,
        n1_vulnerability_score=0.35,
        new_violations=0,
        days_since_major_change=45,
        total_assignments=125,
        computed_at=datetime.now(),
    )

    print("\nSchedule Stability Analysis:")
    print(f"  Total Assignments: {metrics.total_assignments}")
    print(f"  Changes from Previous: {metrics.assignments_changed}")
    print(f"  Churn Rate: {metrics.churn_rate:.1%}")
    print(f"  Ripple Factor: {metrics.ripple_factor:.2f} hops")
    print(f"  N-1 Vulnerability: {metrics.n1_vulnerability_score:.2f}")
    print(f"  New Violations: {metrics.new_violations}")
    print(f"  Days Since Major Change: {metrics.days_since_major_change}")

    print("\n✓ Overall Assessment:")
    print(f"  Stability Grade: {metrics.stability_grade}")
    print(f"  Is Stable: {'Yes ✓' if metrics.is_stable else 'No ✗'}")

    print("\n" + "=" * 70)


def demo_stability_scenarios():
    """Demonstrate different stability scenarios."""
    print("\n" + "=" * 70)
    print("DEMO 2: Different Stability Scenarios")
    print("=" * 70)

    from app.analytics.stability_metrics import StabilityMetrics

    scenarios = [
        {
            "name": "Excellent Stability (Grade A)",
            "metrics": StabilityMetrics(
                assignments_changed=5,
                churn_rate=0.05,
                ripple_factor=0.8,
                n1_vulnerability_score=0.15,
                new_violations=0,
                days_since_major_change=60,
            ),
        },
        {
            "name": "Moderate Churn (Grade C)",
            "metrics": StabilityMetrics(
                assignments_changed=30,
                churn_rate=0.25,
                ripple_factor=2.5,
                n1_vulnerability_score=0.45,
                new_violations=0,
                days_since_major_change=15,
            ),
        },
        {
            "name": "High Vulnerability (Grade D)",
            "metrics": StabilityMetrics(
                assignments_changed=20,
                churn_rate=0.18,
                ripple_factor=3.2,
                n1_vulnerability_score=0.75,
                new_violations=0,
                days_since_major_change=10,
            ),
        },
        {
            "name": "Has Violations (Grade F)",
            "metrics": StabilityMetrics(
                assignments_changed=12,
                churn_rate=0.10,
                ripple_factor=1.5,
                n1_vulnerability_score=0.30,
                new_violations=3,
                days_since_major_change=25,
            ),
        },
    ]

    for scenario in scenarios:
        m = scenario["metrics"]
        print(f"\n{scenario['name']}:")
        print(
            f"  Churn: {m.churn_rate:.1%} | Ripple: {m.ripple_factor:.2f} | "
            f"Vuln: {m.n1_vulnerability_score:.2f} | Violations: {m.new_violations}"
        )
        print(
            f"  → Grade: {m.stability_grade} | Stable: {'Yes ✓' if m.is_stable else 'No ✗'}"
        )

    print("\n" + "=" * 70)


def demo_churn_analysis():
    """Demonstrate churn rate calculation."""
    print("\n" + "=" * 70)
    print("DEMO 3: Churn Rate Analysis")
    print("=" * 70)

    from app.analytics.stability_metrics import StabilityMetricsComputer

    # Mock assignments for demonstration
    class MockAssignment:
        def __init__(self, person_id, block_id, rotation_id):
            self.id = uuid4()
            self.person_id = person_id
            self.block_id = block_id
            self.rotation_template_id = rotation_id
            self.role = "primary"
            self.activity_override = None

    # Create old schedule
    old_assignments = [MockAssignment(uuid4(), uuid4(), uuid4()) for _ in range(10)]

    # Create new schedule (7 same, 3 removed, 5 added)
    new_assignments = old_assignments[:7].copy()
    new_assignments.extend(
        [MockAssignment(uuid4(), uuid4(), uuid4()) for _ in range(5)]
    )

    computer = StabilityMetricsComputer(None)
    churn_data = computer._calculate_churn_rate(old_assignments, new_assignments)

    print("\nChurn Analysis:")
    print(f"  Previous Schedule: {len(old_assignments)} assignments")
    print(f"  Current Schedule: {len(new_assignments)} assignments")
    print(f"  Added: {len(churn_data['added'])}")
    print(f"  Removed: {len(churn_data['removed'])}")
    print(f"  Modified: {len(churn_data['modified'])}")
    print(f"  Total Changed: {churn_data['changed_count']}")
    print(f"  Churn Rate: {churn_data['churn_rate']:.1%}")

    print("\n" + "=" * 70)


def demo_n1_vulnerability():
    """Demonstrate N-1 vulnerability calculation."""
    print("\n" + "=" * 70)
    print("DEMO 4: N-1 Vulnerability Assessment")
    print("=" * 70)

    from app.analytics.stability_metrics import StabilityMetricsComputer

    class MockAssignment:
        def __init__(self, person_id, block_id, rotation_id):
            self.person_id = person_id
            self.block_id = block_id
            self.rotation_template_id = rotation_id
            self.activity_override = None

    # Scenario: One person covers unique rotation (single point of failure)
    critical_person = uuid4()
    shared_rotation = uuid4()
    unique_rotation = uuid4()
    other_person = uuid4()

    assignments = [
        # Critical person with unique coverage
        MockAssignment(critical_person, uuid4(), unique_rotation),
        MockAssignment(critical_person, uuid4(), unique_rotation),
        MockAssignment(critical_person, uuid4(), unique_rotation),
        MockAssignment(critical_person, uuid4(), shared_rotation),
        # Other person with shared coverage only
        MockAssignment(other_person, uuid4(), shared_rotation),
        MockAssignment(other_person, uuid4(), shared_rotation),
    ]

    computer = StabilityMetricsComputer(None)
    vulnerability = computer._calculate_n1_vulnerability(assignments)

    print("\nN-1 Vulnerability Analysis:")
    print(f"  Total Assignments: {len(assignments)}")
    print("  People: 2 (one with unique coverage)")
    print("  Rotations: 2 (one unique, one shared)")
    print(f"  Vulnerability Score: {vulnerability:.2f}")

    if vulnerability > 0.5:
        print("  ⚠️  HIGH RISK: Schedule is vulnerable to single-point-of-failure")
    elif vulnerability > 0.3:
        print("  ⚠️  MODERATE RISK: Some single-point dependencies exist")
    else:
        print("  ✓ LOW RISK: Good redundancy")

    print("\n" + "=" * 70)


def demo_api_response():
    """Demonstrate converting metrics to API response format."""
    print("\n" + "=" * 70)
    print("DEMO 5: API Response Format")
    print("=" * 70)

    import json

    from app.analytics.stability_metrics import StabilityMetrics

    metrics = StabilityMetrics(
        assignments_changed=18,
        churn_rate=0.14,
        ripple_factor=2.1,
        n1_vulnerability_score=0.38,
        new_violations=0,
        days_since_major_change=35,
        total_assignments=130,
        computed_at=datetime.now(),
        version_id="schedule-v1.2.3",
    )

    # Convert to dictionary for JSON API response
    response = metrics.to_dict()
    response["is_stable"] = metrics.is_stable
    response["stability_grade"] = metrics.stability_grade

    print("\nJSON API Response:")
    print(json.dumps(response, indent=2, default=str))

    print("\n" + "=" * 70)


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "STABILITY METRICS DEMONSTRATION" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")

    demo_basic_usage()
    demo_stability_scenarios()
    demo_churn_analysis()
    demo_n1_vulnerability()
    demo_api_response()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
The StabilityMetrics module provides comprehensive schedule stability analysis:

Key Features:
  ✓ Churn Rate - Track schedule changes over time
  ✓ Ripple Factor - Measure cascade effects through dependency graphs
  ✓ N-1 Vulnerability - Assess single-point-of-failure risk
  ✓ Stability Grading - A-F letter grades for quick assessment
  ✓ Violation Tracking - Monitor constraint compliance

Use Cases:
  • Monitor schedule stability after swaps
  • Identify high-risk dependencies
  • Track improvement over time
  • Alert on instability thresholds
  • Generate reports for stakeholders

For more information, see:
  - backend/app/analytics/STABILITY_METRICS_USAGE.md
  - backend/tests/test_stability_metrics.py
  - PROJECT_STATUS_ASSESSMENT.md (line 980+)
""")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
