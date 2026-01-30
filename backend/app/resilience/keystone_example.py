"""
Example usage of Keystone Species Analysis.

This demonstrates how to identify keystone resources in a scheduling system
and create succession plans to mitigate dependency risks.
"""

from datetime import datetime
from uuid import uuid4

from app.resilience.keystone_analysis import KeystoneAnalyzer


def example_keystone_analysis() -> None:
    """
    Example: Identify keystone faculty and create succession plans.

    Scenario:
    - Dr. Smith: Neonatology specialist (only one who can handle high-risk deliveries)
    - Dr. Jones: General family medicine (one of several)
    - Dr. Lee: Sports medicine (one of two)
    """

    # Initialize analyzer
    analyzer = KeystoneAnalyzer(keystone_threshold=0.6, use_networkx=True)

    # Mock data structures (in real use, fetch from database)
    class MockFaculty:
        def __init__(self, fid, name) -> None:
            self.id = fid
            self.name = name

    dr_smith = MockFaculty(uuid4(), "Dr. Smith (Neonatologist)")
    dr_jones = MockFaculty(uuid4(), "Dr. Jones (Family Med)")
    dr_lee = MockFaculty(uuid4(), "Dr. Lee (Sports Med)")

    faculty = [dr_smith, dr_jones, dr_lee]
    residents = []

    # Services
    neonate_service = uuid4()
    family_med_service = uuid4()
    sports_med_service = uuid4()

    services = {
        neonate_service: [dr_smith.id],  # Only Dr. Smith can do this
        family_med_service: [
            dr_smith.id,
            dr_jones.id,
            dr_lee.id,
        ],  # All can do family med
        sports_med_service: [dr_jones.id, dr_lee.id],  # Two can do sports med
    }

    # Rotations
    rotations = {
        uuid4(): {"name": "NICU", "required_services": [neonate_service]},
        uuid4(): {"name": "Family Clinic", "required_services": [family_med_service]},
        uuid4(): {"name": "Sports Clinic", "required_services": [sports_med_service]},
    }

    # Assignments (simplified)
    assignments = []

    # Step 1: Identify keystone resources
    print("=" * 80)
    print("STEP 1: Identifying Keystone Resources")
    print("=" * 80)

    keystones = analyzer.identify_keystone_resources(
        faculty=faculty,
        residents=residents,
        assignments=assignments,
        services=services,
        rotations=rotations,
        threshold=0.5,
    )

    print(f"\nFound {len(keystones)} keystone resource(s):\n")

    for keystone in keystones:
        print(f"  • {keystone.entity_name}")
        print(f"    - Type: {keystone.entity_type.value}")
        print(f"    - Keystoneness Score: {keystone.keystoneness_score:.2f}")
        print(f"    - Functional Redundancy: {keystone.functional_redundancy:.2f}")
        print(f"    - Risk Level: {keystone.risk_level.value}")
        print(f"    - Unique Capabilities: {len(keystone.unique_capabilities)}")
        print(f"    - Is Keystone: {keystone.is_keystone}")
        print(f"    - Single Point of Failure: {keystone.is_single_point_of_failure}")
        print()

        # Step 2: Simulate cascade for most critical keystone
    if keystones:
        print("=" * 80)
        print("STEP 2: Simulating Removal Cascade")
        print("=" * 80)

        top_keystone = keystones[0]
        print(f"\nSimulating removal of: {top_keystone.entity_name}\n")

        cascade = analyzer.simulate_removal_cascade(
            entity_id=top_keystone.entity_id,
            faculty=faculty,
            residents=residents,
            assignments=assignments,
            services=services,
            rotations=rotations,
        )

        print(f"  • Cascade Depth: {cascade.cascade_depth} levels")
        print(f"  • Total Affected: {cascade.total_affected} entities")
        print(f"  • Coverage Loss: {cascade.coverage_loss:.1%}")
        print(f"  • Recovery Time: {cascade.recovery_time_days} days")
        print(f"  • Catastrophic: {cascade.is_catastrophic}")
        print()

        if cascade.cascade_steps:
            print("  Cascade Steps:")
            for step in cascade.cascade_steps:
                print(
                    f"    Level {step['level']}: {step['affected_count']} entities affected"
                )
                print(f"      Reason: {step['reason']}")
            print()

            # Step 3: Create succession plans
    if keystones:
        print("=" * 80)
        print("STEP 3: Creating Succession Plans")
        print("=" * 80)

        all_entities = faculty + residents

        for keystone in keystones[:3]:  # Top 3 keystones
            print(f"\nSuccession Plan for: {keystone.entity_name}\n")

            plan = analyzer.recommend_succession_plan(
                keystone=keystone,
                all_entities=all_entities,
                services=services,
            )

            print(f"  • Training Priority: {plan.training_priority}")
            print(f"  • Estimated Training Hours: {plan.estimated_training_hours}h")
            print(f"  • Expected Risk Reduction: {plan.risk_reduction:.1%}")
            print()

            if plan.backup_candidates:
                print("  Backup Candidates:")
                for candidate_id, candidate_name, suitability in plan.backup_candidates[
                    :3
                ]:
                    print(f"    - {candidate_name}: {suitability:.0%} suitability")
                print()

            if plan.cross_training_needed:
                print("  Training Needed:")
                for skill in plan.cross_training_needed:
                    print(f"    - {skill}")
                print()

            if plan.interim_measures:
                print("  Interim Measures:")
                for measure in plan.interim_measures:
                    print(f"    - {measure}")
                print()

                # Step 4: Summary statistics
    print("=" * 80)
    print("STEP 4: Summary Statistics")
    print("=" * 80)

    summary = analyzer.get_keystone_summary()

    print(f"\nTotal Keystones: {summary['total_keystones']}")
    print("\nBy Risk Level:")
    for level, count in summary["by_risk_level"].items():
        if count > 0:
            print(f"  • {level.upper()}: {count}")

    print(f"\nSingle Points of Failure: {summary['single_points_of_failure']}")
    print(f"Average Keystoneness: {summary['average_keystoneness']:.2f}")

    print("\nSuccession Plans:")
    print(f"  • Total: {summary['succession_plans']['total']}")
    for status, count in summary["succession_plans"]["by_status"].items():
        if count > 0:
            print(f"  • {status.upper()}: {count}")

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    example_keystone_analysis()
