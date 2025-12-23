#!/usr/bin/env python3
"""
Example usage of SPC (Statistical Process Control) workload monitoring.

This script demonstrates how to use the SPC monitoring module to detect
workload anomalies and ACGME compliance issues in resident scheduling.
"""

from uuid import uuid4

# Note: In production, import from app.resilience
# from app.resilience.spc_monitoring import (
#     WorkloadControlChart,
#     calculate_control_limits,
#     calculate_process_capability,
# )

# For this example, we'll simulate the imports
print("=" * 70)
print("SPC Monitoring Example - Resident Workload Analysis")
print("=" * 70)
print()


def example_1_basic_monitoring():
    """Example 1: Basic workload monitoring with Western Electric Rules."""
    print("Example 1: Basic Workload Monitoring")
    print("-" * 70)

    from app.resilience.spc_monitoring import WorkloadControlChart

    # Create control chart: target=60h/week, sigma=5h
    chart = WorkloadControlChart(target_hours=60, sigma=5)

    # Simulate 10 weeks of resident workload
    resident_id = uuid4()
    weekly_hours = [58, 62, 59, 67, 71, 75, 78, 80, 77, 74]

    print(f"Resident ID: {resident_id}")
    print(f"Weekly hours: {weekly_hours}")
    print(
        f"Target: {chart.target_hours}h, 3σ limits: [{chart.lcl_3sigma:.1f}h, {chart.ucl_3sigma:.1f}h]"
    )
    print()

    # Detect violations
    alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

    if alerts:
        print(f"⚠️  {len(alerts)} violation(s) detected:")
        for i, alert in enumerate(alerts, 1):
            print(f"\n{i}. {alert.rule} ({alert.severity})")
            print(f"   {alert.message}")
    else:
        print("✅ No violations detected - workload within normal limits")

    print("\n")


def example_2_historical_control_limits():
    """Example 2: Calculate control limits from historical data."""
    print("Example 2: Calculate Control Limits from Historical Data")
    print("-" * 70)

    from app.resilience.spc_monitoring import (
        WorkloadControlChart,
        calculate_control_limits,
    )

    # Historical weekly hours for last academic year
    historical_data = [
        58,
        62,
        59,
        61,
        63,
        60,
        58,
        62,
        64,
        57,  # Weeks 1-10
        59,
        61,
        60,
        58,
        62,
        61,
        59,
        60,
        63,
        58,  # Weeks 11-20
        60,
        62,
        59,
        61,
        60,
        58,
        62,
        61,
        59,
        60,  # Weeks 21-30
    ]

    print(f"Historical data: {len(historical_data)} weeks")
    print()

    # Calculate empirical control limits
    limits = calculate_control_limits(historical_data)

    print("Calculated control limits:")
    print(f"  Centerline (mean): {limits['centerline']:.1f}h")
    print(f"  Standard deviation: {limits['sigma']:.2f}h")
    print(f"  UCL (3σ): {limits['ucl']:.1f}h")
    print(f"  LCL (3σ): {limits['lcl']:.1f}h")
    print(f"  Sample size: {limits['n']} weeks")
    print()

    # Use empirical limits for future monitoring
    chart = WorkloadControlChart(
        target_hours=limits["centerline"], sigma=limits["sigma"]
    )

    print("Using empirical control limits for ongoing monitoring...")
    print("\n")


def example_3_process_capability():
    """Example 3: Assess process capability for ACGME compliance."""
    print("Example 3: Process Capability Analysis (ACGME Compliance)")
    print("-" * 70)

    from app.resilience.spc_monitoring import calculate_process_capability

    # Weekly hours for a resident
    weekly_hours = [58, 62, 59, 61, 63, 60, 58, 62, 64, 57]

    # ACGME specification: 0-80 hours/week
    lsl = 0  # Lower spec limit
    usl = 80  # Upper spec limit (ACGME maximum)

    print(f"Weekly hours: {weekly_hours}")
    print(f"Specification limits: [{lsl}h, {usl}h]")
    print()

    # Calculate capability
    capability = calculate_process_capability(weekly_hours, lsl, usl)

    print("Process Capability Results:")
    print(f"  Mean: {capability['mean']:.1f}h")
    print(f"  Std Dev: {capability['sigma']:.2f}h")
    print(f"  Cp (potential): {capability['cp']:.3f}")
    print(f"  Cpk (actual): {capability['cpk']:.3f}")
    print(f"  Pp (performance): {capability['pp']:.3f}")
    print(f"  Ppk (performance actual): {capability['ppk']:.3f}")
    print()
    print(f"Interpretation: {capability['interpretation']}")
    print()

    # Capability guidelines:
    print("Capability Guidelines:")
    print("  Cpk < 1.0:  ❌ Process not capable (violations likely)")
    print("  Cpk ≥ 1.0:  ⚠️  Marginal (minimum acceptable)")
    print("  Cpk ≥ 1.33: ✅ Capable (4σ quality)")
    print("  Cpk ≥ 1.67: ⭐ Excellent (5σ quality)")
    print("  Cpk ≥ 2.0:  🏆 World-class (6σ quality)")
    print()

    if capability["cpk"] >= 1.33:
        print("✅ Process is capable of maintaining ACGME compliance")
    elif capability["cpk"] >= 1.0:
        print("⚠️  Process marginally capable - improvement recommended")
    else:
        print("❌ Process not capable - ACGME violations likely")

    print("\n")


def example_4_combined_analysis():
    """Example 4: Combined SPC + Capability analysis."""
    print("Example 4: Combined SPC Monitoring + Capability Analysis")
    print("-" * 70)

    from app.resilience.spc_monitoring import (
        WorkloadControlChart,
        calculate_process_capability,
    )

    resident_id = uuid4()

    # Simulated workload showing gradual increase (burnout pattern)
    weekly_hours = [60, 62, 64, 66, 68, 70, 72, 74, 76, 78]

    print(f"Resident ID: {resident_id}")
    print(f"Weekly hours (10 weeks): {weekly_hours}")
    print()

    # 1. Real-time SPC monitoring
    print("1. Western Electric Rules Analysis:")
    print("   " + "-" * 40)
    chart = WorkloadControlChart(target_hours=60, sigma=5)
    alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

    if alerts:
        for alert in alerts:
            severity_icon = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🔵"}
            icon = severity_icon.get(alert.severity, "⚪")
            print(f"   {icon} {alert.rule}: {alert.message[:60]}...")
    else:
        print("   ✅ No violations")
    print()

    # 2. Overall process capability
    print("2. Process Capability Analysis:")
    print("   " + "-" * 40)
    capability = calculate_process_capability(weekly_hours, lsl=0, usl=80)
    print(f"   Cpk: {capability['cpk']:.3f} - {capability['interpretation']}")
    print(f"   Mean workload: {capability['mean']:.1f}h/week")
    print()

    # 3. Recommendations
    print("3. Recommendations:")
    print("   " + "-" * 40)

    if alerts:
        critical = [a for a in alerts if a.severity == "CRITICAL"]
        warning = [a for a in alerts if a.severity == "WARNING"]

        if critical:
            print(f"   🔴 URGENT: {len(critical)} critical violation(s)")
            print("      → Immediate intervention required")
            print("      → Review rotation assignments")
            print("      → Ensure ACGME compliance")
        if warning:
            print(f"   🟠 WARNING: {len(warning)} pattern(s) detected")
            print("      → Monitor closely")
            print("      → Investigate root causes")

    if capability["cpk"] < 1.0:
        print("   ❌ Process incapable - systemic changes needed")
        print("      → Redistribute workload more evenly")
        print("      → Review scheduling algorithm parameters")

    print("\n")


def main():
    """Run all examples."""
    example_1_basic_monitoring()
    example_2_historical_control_limits()
    example_3_process_capability()
    example_4_combined_analysis()

    print("=" * 70)
    print("For more information, see:")
    print("  - backend/app/resilience/SPC_MONITORING_README.md")
    print("  - backend/tests/resilience/test_spc_monitoring.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
