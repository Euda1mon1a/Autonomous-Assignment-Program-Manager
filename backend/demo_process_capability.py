#!/usr/bin/env python3
"""
Demonstration of Six Sigma Process Capability Analysis for Schedule Quality.

This script demonstrates how to use the ScheduleCapabilityAnalyzer to measure
schedule quality using Six Sigma metrics (Cp, Cpk, Pp, Ppk, Cpm).

Example output shows:
1. Basic capability calculation for weekly resident hours
2. Comparison of good vs poor scheduling processes
3. ACGME compliance monitoring over time
4. Interpretation of results and recommendations
"""

import statistics


def calculate_process_capability_manual_demo():
    """
    Manual calculation demo showing the Six Sigma formulas.

    This demonstrates the math behind Cp, Cpk, and sigma levels.
    """
    print("=" * 80)
    print("MANUAL CALCULATION DEMO")
    print("=" * 80)
    print()

    # Sample data: weekly resident hours
    weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, 64, 69, 71, 66]

    # Specification limits (ACGME: 80 hours max, practical min: 40 hours)
    LSL = 40.0  # Lower Specification Limit
    USL = 80.0  # Upper Specification Limit
    TARGET = 60.0  # Ideal target hours

    print(f"Weekly Hours Data: {weekly_hours}")
    print(f"Specification Limits: LSL={LSL}, USL={USL}, Target={TARGET}")
    print()

    # Calculate basic statistics
    mean = statistics.mean(weekly_hours)
    std_dev = statistics.stdev(weekly_hours)

    print("Basic Statistics:")
    print(f"  Mean (μ) = {mean:.2f} hours")
    print(f"  Standard Deviation (σ) = {std_dev:.2f} hours")
    print()

    # Calculate Cp (Process Capability - assumes centered)
    # Cp = (USL - LSL) / (6σ)
    cp = (USL - LSL) / (6 * std_dev)

    print("Cp (Process Capability):")
    print("  Formula: Cp = (USL - LSL) / (6σ)")
    print(f"  Calculation: ({USL} - {LSL}) / (6 × {std_dev:.2f})")
    print(f"  Cp = {cp:.3f}")
    print("  → This tells us the POTENTIAL capability (if process were centered)")
    print()

    # Calculate Cpk (Process Capability accounting for centering)
    # Cpk = min[(USL - μ) / 3σ, (μ - LSL) / 3σ]
    cpu = (USL - mean) / (3 * std_dev)  # Upper capability
    cpl = (mean - LSL) / (3 * std_dev)  # Lower capability
    cpk = min(cpu, cpl)

    print("Cpk (Process Capability with centering):")
    print(
        f"  CPU = (USL - μ) / (3σ) = ({USL} - {mean:.2f}) / (3 × {std_dev:.2f}) = {cpu:.3f}"
    )
    print(
        f"  CPL = (μ - LSL) / (3σ) = ({mean:.2f} - {LSL}) / (3 × {std_dev:.2f}) = {cpl:.3f}"
    )
    print(f"  Cpk = min(CPU, CPL) = {cpk:.3f}")
    print("  → This tells us the ACTUAL capability")
    print()

    # Interpret Cpk
    sigma_level = 3.0 * cpk

    if cpk >= 2.0:
        classification = "EXCELLENT (World Class, 6σ)"
    elif cpk >= 1.67:
        classification = "EXCELLENT (5σ quality)"
    elif cpk >= 1.33:
        classification = "CAPABLE (4σ quality)"
    elif cpk >= 1.0:
        classification = "MARGINAL (3σ quality)"
    else:
        classification = "INCAPABLE (defects expected)"

    print("Interpretation:")
    print(f"  Sigma Level ≈ 3 × Cpk = {sigma_level:.2f}σ")
    print(f"  Classification: {classification}")
    print()

    # Calculate Cpm (Taguchi - penalizes off-target)
    # Cpm = (USL - LSL) / (6 × √[σ² + (μ - T)²])
    deviation_from_target = mean - TARGET
    adjusted_std = (std_dev**2 + deviation_from_target**2) ** 0.5
    cpm = (USL - LSL) / (6 * adjusted_std)

    print("Cpm (Taguchi Index - penalizes off-target):")
    print(
        f"  Deviation from target = μ - T = {mean:.2f} - {TARGET:.2f} = {deviation_from_target:.2f}"
    )
    print(
        f"  Adjusted σ = √(σ² + (μ-T)²) = √({std_dev:.2f}² + {deviation_from_target:.2f}²) = {adjusted_std:.2f}"
    )
    print(f"  Cpm = (USL - LSL) / (6 × adjusted σ) = {cpm:.3f}")
    print("  → Cpm < Cp means process is off-target")
    print()


def demonstrate_good_vs_poor_scheduling():
    """Compare good (capable) vs poor (incapable) scheduling processes."""
    print("=" * 80)
    print("GOOD vs POOR SCHEDULING COMPARISON")
    print("=" * 80)
    print()

    # Good scheduling: tight control, well-centered
    good_schedule = [
        60,
        62,
        58,
        61,
        59,
        63,
        60,
        61,
        59,
        62,
        60,
        61,
        59,
        62,
        60,
        61,
        58,
        63,
        60,
        61,
    ]

    # Poor scheduling: high variation, off-center
    poor_schedule = [
        45,
        75,
        50,
        78,
        48,
        72,
        55,
        70,
        50,
        75,
        48,
        73,
        52,
        71,
        49,
        74,
        51,
        72,
        50,
        76,
    ]

    LSL, USL = 40.0, 80.0

    # Analyze good schedule
    print("GOOD SCHEDULING (Tight Control):")
    print(f"  Hours: {good_schedule[:10]}... (showing first 10)")
    good_mean = statistics.mean(good_schedule)
    good_std = statistics.stdev(good_schedule)
    good_cpk = min(
        (USL - good_mean) / (3 * good_std), (good_mean - LSL) / (3 * good_std)
    )
    good_sigma = 3.0 * good_cpk

    print(f"  Mean: {good_mean:.1f}, Std Dev: {good_std:.1f}")
    print(f"  Cpk: {good_cpk:.3f}")
    print(f"  Sigma: {good_sigma:.1f}σ")
    print("  Status: EXCELLENT - Consistently balanced workload")
    print()

    # Analyze poor schedule
    print("POOR SCHEDULING (High Variation):")
    print(f"  Hours: {poor_schedule[:10]}... (showing first 10)")
    poor_mean = statistics.mean(poor_schedule)
    poor_std = statistics.stdev(poor_schedule)
    poor_cpk = min(
        (USL - poor_mean) / (3 * poor_std), (poor_mean - LSL) / (3 * poor_std)
    )
    poor_sigma = 3.0 * poor_cpk

    print(f"  Mean: {poor_mean:.1f}, Std Dev: {poor_std:.1f}")
    print(f"  Cpk: {poor_cpk:.3f}")
    print(f"  Sigma: {poor_sigma:.1f}σ")
    print("  Status: INCAPABLE - Erratic workload, burnout risk")
    print()

    print("IMPACT:")
    print(
        f"  Good scheduling has {good_std / poor_std:.0%} the variation of poor scheduling"
    )
    print(f"  Good scheduling is {good_cpk / poor_cpk:.1f}x more capable")
    print(f"  Poor scheduling has {(poor_std / good_std) ** 2:.1f}x more variance")
    print()


def demonstrate_acgme_monitoring():
    """Demonstrate using capability analysis for ACGME compliance monitoring."""
    print("=" * 80)
    print("ACGME COMPLIANCE MONITORING")
    print("=" * 80)
    print()

    print("Scenario: Monitoring resident weekly hours over a 12-week rotation")
    print()

    # Simulate 12 weeks of data
    weeks = [
        ("Week 1", 65),
        ("Week 2", 72),
        ("Week 3", 58),
        ("Week 4", 75),
        ("Week 5", 68),
        ("Week 6", 70),
        ("Week 7", 62),
        ("Week 8", 77),
        ("Week 9", 64),
        ("Week 10", 69),
        ("Week 11", 71),
        ("Week 12", 66),
    ]

    print("Weekly Hours:")
    for week, hours in weeks:
        status = "✓" if hours < 80 else "✗ VIOLATION"
        print(f"  {week}: {hours:2d} hours  {status}")
    print()

    hours_data = [h for _, h in weeks]
    mean = statistics.mean(hours_data)
    std_dev = statistics.stdev(hours_data)

    LSL, USL = 40.0, 80.0
    cpk = min((USL - mean) / (3 * std_dev), (mean - LSL) / (3 * std_dev))

    print("Process Capability Analysis:")
    print(f"  Mean: {mean:.1f} hours/week")
    print(f"  Std Dev: {std_dev:.1f} hours")
    print(f"  Cpk: {cpk:.3f}")
    print()

    # Predict probability of violation
    # Approximate: For Cpk=1.33, ~66 PPM (0.0066%) outside specs
    # For Cpk=1.0, ~2700 PPM (0.27%) outside specs
    if cpk >= 1.67:
        risk = "VERY LOW (<0.001%)"
        recommendation = "Excellent compliance. Maintain current practices."
    elif cpk >= 1.33:
        risk = "LOW (<0.01%)"
        recommendation = "Good compliance. Monitor for regression."
    elif cpk >= 1.0:
        risk = "MODERATE (~0.27%)"
        recommendation = "Marginal. Tighten schedule controls to reduce variation."
    else:
        risk = "HIGH (>0.27%)"
        recommendation = (
            "URGENT: High risk of ACGME violations. Review scheduling process."
        )

    print("Risk Assessment:")
    print(f"  Risk of exceeding 80 hours: {risk}")
    print(f"  Recommendation: {recommendation}")
    print()


def demonstrate_practical_use_case():
    """Show a practical use case: evaluating schedule generator quality."""
    print("=" * 80)
    print("PRACTICAL USE CASE: Evaluating Schedule Generator Quality")
    print("=" * 80)
    print()

    print("Scenario: Compare two schedule generation algorithms")
    print()

    # Algorithm A: Simple round-robin (poor balancing)
    algo_a_hours = [55, 70, 48, 75, 52, 68, 58, 72, 50, 74, 56, 69]

    # Algorithm B: Optimized with load balancing (good)
    algo_b_hours = [62, 64, 61, 63, 62, 61, 63, 62, 61, 64, 62, 63]

    LSL, USL = 40.0, 80.0

    for name, hours in [
        ("Algorithm A (Round-Robin)", algo_a_hours),
        ("Algorithm B (Load-Balanced)", algo_b_hours),
    ]:
        print(f"{name}:")
        mean = statistics.mean(hours)
        std = statistics.stdev(hours)
        cpk = min((USL - mean) / (3 * std), (mean - LSL) / (3 * std))
        sigma = 3.0 * cpk

        if cpk >= 1.67:
            verdict = "EXCELLENT - Deploy to production"
        elif cpk >= 1.33:
            verdict = "CAPABLE - Acceptable for use"
        elif cpk >= 1.0:
            verdict = "MARGINAL - Needs improvement"
        else:
            verdict = "INCAPABLE - Do not deploy"

        print(f"  Mean: {mean:.1f}, Std: {std:.1f}")
        print(f"  Cpk: {cpk:.3f} ({sigma:.1f}σ)")
        print(f"  Verdict: {verdict}")
        print()

    print("Decision: Choose Algorithm B for production deployment")
    print()


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print(" " * 20 + "SIX SIGMA PROCESS CAPABILITY ANALYSIS")
    print(" " * 25 + "Schedule Quality Metrics Demo")
    print("=" * 80)
    print()

    calculate_process_capability_manual_demo()
    print("\n")

    demonstrate_good_vs_poor_scheduling()
    print("\n")

    demonstrate_acgme_monitoring()
    print("\n")

    demonstrate_practical_use_case()

    print("=" * 80)
    print("END OF DEMONSTRATION")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("  • Cpk measures how well a process meets specifications")
    print("  • Higher Cpk = more consistent, predictable scheduling")
    print("  • Cpk >= 1.33 is industry standard for 'capable' processes")
    print("  • Cpk >= 1.67 is 'excellent' (5σ quality)")
    print("  • Use these metrics to compare and improve schedule generators")
    print("  • Monitor Cpk over time to detect process degradation")
    print()


if __name__ == "__main__":
    main()
