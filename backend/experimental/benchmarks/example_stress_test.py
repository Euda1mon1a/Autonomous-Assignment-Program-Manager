"""
Example usage of the Stress Testing framework.

This script demonstrates how to use the StressTester class to validate
scheduler behavior under various stress conditions.
"""

from stress_testing import StressLevel, StressTester


def example_stress_test():
    """
    Example: Run a stress test on the scheduler.

    NOTE: This example shows the API, but requires a real database
    and scheduler instance to run. For actual testing, integrate
    with your test suite.
    """
    # Create stress tester
    tester = StressTester()

    # Create a mock scenario for demonstration
    # In real usage, you would use a real SchedulingEngine instance
    scenario = StressTester.create_scenario(
        algorithm="greedy",
        pgy_levels=None,  # All residents
        check_resilience=True,
    )

    print("=" * 80)
    print("STRESS TESTING FRAMEWORK - EXAMPLE USAGE")
    print("=" * 80)
    print()
    print("This example demonstrates the stress testing API.")
    print("To run actual tests, you need:")
    print("  1. A database session (db)")
    print("  2. A SchedulingEngine instance")
    print("  3. Test data (residents, faculty, blocks, templates)")
    print()
    print("=" * 80)
    print("EXAMPLE CODE:")
    print("=" * 80)
    print()

    example_code = """
    from datetime import date, timedelta
    from app.scheduling.engine import SchedulingEngine
    from experimental.benchmarks.stress_testing import StressTester, StressLevel

    # Create scheduler
    engine = SchedulingEngine(
        db=db,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=28)
    )

    # Create scenario
    scenario = StressTester.create_scenario(
        algorithm="greedy",
        check_resilience=True
    )

    # Create tester
    tester = StressTester()

    # Run single stress test
    result = tester.run_stress_test(engine, StressLevel.CRITICAL, scenario)
    print(f"ACGME Compliance: {result.acgme_compliance:.1%}")
    print(f"Patient Safety: {result.patient_safety_maintained}")
    print(f"Graceful Degradation: {result.degradation_graceful}")

    # Run full degradation ladder (all stress levels)
    all_results = tester.run_degradation_ladder(engine, scenario)

    # Generate report
    report = tester.generate_report(all_results)
    print(report)

    # Verify master regulators (patient safety maintained at all levels)
    if tester.verify_master_regulators(all_results):
        print("✓ Patient safety maintained at all stress levels")
    else:
        print("✗ Patient safety violations detected")

    # Verify graceful degradation
    if tester.verify_graceful_degradation(all_results):
        print("✓ System degraded gracefully under all stress conditions")
    else:
        print("✗ System experienced catastrophic failures")
    """

    print(example_code)
    print()
    print("=" * 80)
    print("STRESS LEVELS:")
    print("=" * 80)
    print()

    for level in StressLevel:
        print(f"{level.value.upper():12s} - ", end="")
        if level == StressLevel.NORMAL:
            print("100% capacity, 60s timeout, 0% absence rate")
        elif level == StressLevel.ELEVATED:
            print("110% load, 45s timeout, 10% absence rate")
        elif level == StressLevel.HIGH:
            print("120% load, 30s timeout, 20% absence rate")
        elif level == StressLevel.CRITICAL:
            print("130% load, 20s timeout, 30% absence rate")
        elif level == StressLevel.CRISIS:
            print("150% load, 10s timeout, 40% absence rate")

    print()
    print("=" * 80)
    print("EXPECTED OUTCOMES:")
    print("=" * 80)
    print()
    print("1. Constraint Satisfaction:")
    print("   - NORMAL:    All constraints satisfied")
    print("   - ELEVATED:  Soft constraints may relax")
    print("   - HIGH:      Non-critical constraints silenced")
    print("   - CRITICAL:  Only safety-critical constraints")
    print("   - CRISIS:    Emergency mode, minimal constraints")
    print()
    print("2. Coverage Expectations:")
    print("   - NORMAL:    ≥90% schedule coverage")
    print("   - ELEVATED:  ≥75% schedule coverage")
    print("   - HIGH:      ≥60% schedule coverage")
    print("   - CRITICAL:  ≥40% schedule coverage")
    print("   - CRISIS:    ≥25% schedule coverage")
    print()
    print("3. Patient Safety (Master Regulator):")
    print("   - Must be maintained at ALL stress levels")
    print("   - Supervision ratios NEVER violated")
    print("   - This is the critical safety constraint")
    print()
    print("=" * 80)


if __name__ == "__main__":
    example_stress_test()
