#!/usr/bin/env python3
"""
PCS Season Simulation - Battle Testing with Real-World Parameters.

Your scenario: Arriving to 4 faculty when normal staffing is 10.
This simulates the burnout cascade risk and provides survival analysis.
"""

import sys
import os

# Direct import to avoid broken resilience __init__ chain
sys.path.insert(0, '/home/user/Autonomous-Assignment-Program-Manager/backend')
os.chdir('/home/user/Autonomous-Assignment-Program-Manager/backend')

from dataclasses import dataclass

# Import directly from module to avoid broken imports in resilience/__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "cascade_scenario",
    "/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/simulation/cascade_scenario.py"
)
cascade_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cascade_module)

CascadeConfig = cascade_module.CascadeConfig
BurnoutCascadeScenario = cascade_module.BurnoutCascadeScenario
CascadeResult = cascade_module.CascadeResult


@dataclass
class PCSSeasonParams:
    """Your program's specific parameters."""
    # Staffing reality
    initial_faculty: int = 4      # Your PCS arrival
    expected_faculty: int = 10    # Normal staffing
    minimum_viable: int = 3       # Can't go below this

    # Screeners (for context - cascade focuses on faculty)
    initial_screeners: int = 2
    available_rns: int = 3
    available_emts: int = 2

    # Workload
    total_workload_units: float = 10.0   # Full 10-person demand
    sustainable_workload: float = 1.2    # Per person sustainable
    burnout_threshold: float = 1.5       # Accelerated departure
    critical_threshold: float = 2.0      # Danger zone

    # Military timing
    hiring_delay_days: int = 45          # GAP between departure/replacement
    base_departure_rate: float = 0.001   # ~3%/year baseline
    burnout_multiplier: float = 5.0      # 5x departure rate when burned out


def run_single_simulation(params: PCSSeasonParams, seed: int = 42) -> CascadeResult:
    """Run a single simulation with given parameters."""
    config = CascadeConfig(
        initial_faculty=params.initial_faculty,
        minimum_viable=params.minimum_viable,
        max_simulation_days=365,
        total_workload_units=params.total_workload_units,
        sustainable_workload=params.sustainable_workload,
        burnout_threshold=params.burnout_threshold,
        critical_threshold=params.critical_threshold,
        base_departure_rate=params.base_departure_rate,
        burnout_multiplier=params.burnout_multiplier,
        hiring_delay_days=params.hiring_delay_days,
        hiring_rate=0.03,  # Slightly higher - military can expedite
        max_hiring_queue=3,
        seed=seed,
    )

    scenario = BurnoutCascadeScenario(config)
    return scenario.run()


def run_monte_carlo(params: PCSSeasonParams, n_runs: int = 100) -> dict:
    """Run Monte Carlo simulation for survival analysis."""
    results = []
    collapse_days = []
    peak_workloads = []

    for seed in range(n_runs):
        result = run_single_simulation(params, seed=seed)
        results.append(result)

        if result.collapsed:
            collapse_days.append(result.days_to_collapse)
        peak_workloads.append(result.peak_workload)

    survival_count = sum(1 for r in results if not r.collapsed)
    survival_rate = survival_count / n_runs

    # Calculate percentiles for collapse timing
    collapse_days_sorted = sorted(collapse_days) if collapse_days else []

    return {
        "n_runs": n_runs,
        "survival_rate": survival_rate,
        "survival_count": survival_count,
        "collapse_count": n_runs - survival_count,
        "avg_collapse_day": sum(collapse_days) / len(collapse_days) if collapse_days else None,
        "median_collapse_day": collapse_days_sorted[len(collapse_days_sorted)//2] if collapse_days_sorted else None,
        "earliest_collapse": min(collapse_days) if collapse_days else None,
        "latest_collapse": max(collapse_days) if collapse_days else None,
        "avg_peak_workload": sum(peak_workloads) / len(peak_workloads),
        "max_peak_workload": max(peak_workloads),
        "vortex_entries": sum(1 for r in results if r.entered_vortex),
    }


def print_single_result(result: CascadeResult, params: PCSSeasonParams):
    """Print detailed results from a single simulation."""
    print("\n" + "="*70)
    print("  PCS SEASON SIMULATION RESULTS - SINGLE RUN")
    print("="*70)

    # Initial conditions
    print(f"\n📊 INITIAL CONDITIONS:")
    print(f"   Faculty:         {params.initial_faculty} (normal: {params.expected_faculty})")
    print(f"   Workload/person: {params.total_workload_units / params.initial_faculty:.2f}x")
    print(f"   Status:          {'🔴 CRITICAL' if params.total_workload_units / params.initial_faculty > params.critical_threshold else '🟠 BURNOUT ZONE' if params.total_workload_units / params.initial_faculty > params.burnout_threshold else '🟢 SUSTAINABLE'}")

    # Outcome
    print(f"\n📈 OUTCOME:")
    if result.collapsed:
        print(f"   ❌ COLLAPSED after {result.days_to_collapse} days")
        print(f"   Final faculty: {result.final_faculty_count}")
    else:
        print(f"   ✅ SURVIVED 365 days")
        print(f"   Final faculty: {result.final_faculty_count}")

    # Key metrics
    print(f"\n📉 KEY METRICS:")
    print(f"   Peak workload:        {result.peak_workload:.2f}x per person")
    print(f"   Days in burnout zone: {result.time_in_burnout_zone} ({result.time_in_burnout_zone/365*100:.1f}%)")
    print(f"   Days in critical:     {result.time_in_critical_zone} ({result.time_in_critical_zone/365*100:.1f}%)")
    print(f"   Total departures:     {result.total_departures}")
    print(f"   Burnout departures:   {result.departures_from_burnout}")
    print(f"   Total hires:          {result.total_hires}")

    # Vortex status
    if result.entered_vortex:
        print(f"\n🌀 EXTINCTION VORTEX:")
        print(f"   Entered on day {result.vortex_entry_day} with {result.vortex_faculty_count} faculty")
        print(f"   (Departure rate exceeded replacement rate)")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"   {i}. {rec}")

    # Timeline highlights
    print(f"\n📅 TIMELINE HIGHLIGHTS:")
    milestones = [0, 30, 60, 90, 180, 364]
    for day in milestones:
        if day < len(result.snapshots):
            s = result.snapshots[day]
            status = "🔴" if s.in_critical_zone else "🟠" if s.in_burnout_zone else "🟢"
            print(f"   Day {day:3d}: {s.faculty_count} faculty, {s.workload_per_person:.2f}x workload {status}")


def print_monte_carlo_results(mc_results: dict, params: PCSSeasonParams):
    """Print Monte Carlo analysis results."""
    print("\n" + "="*70)
    print("  MONTE CARLO SURVIVAL ANALYSIS")
    print("="*70)

    print(f"\n📊 SIMULATION PARAMETERS:")
    print(f"   Starting faculty:   {params.initial_faculty}")
    print(f"   Number of runs:     {mc_results['n_runs']}")
    print(f"   Initial workload:   {params.total_workload_units / params.initial_faculty:.2f}x per person")

    print(f"\n🎯 SURVIVAL ANALYSIS:")
    survival_pct = mc_results['survival_rate'] * 100

    if survival_pct >= 95:
        status = "✅ SAFE"
    elif survival_pct >= 80:
        status = "🟡 LIKELY"
    elif survival_pct >= 50:
        status = "🟠 COIN FLIP"
    else:
        status = "🔴 UNLIKELY"

    print(f"   Survival rate:      {survival_pct:.1f}% {status}")
    print(f"   Survivors:          {mc_results['survival_count']}/{mc_results['n_runs']}")
    print(f"   Collapses:          {mc_results['collapse_count']}/{mc_results['n_runs']}")

    if mc_results['avg_collapse_day']:
        print(f"\n⏱️  COLLAPSE TIMING (when it happens):")
        print(f"   Average:            Day {mc_results['avg_collapse_day']:.0f}")
        print(f"   Median:             Day {mc_results['median_collapse_day']}")
        print(f"   Earliest:           Day {mc_results['earliest_collapse']}")
        print(f"   Latest:             Day {mc_results['latest_collapse']}")

    print(f"\n📈 WORKLOAD ANALYSIS:")
    print(f"   Avg peak workload:  {mc_results['avg_peak_workload']:.2f}x")
    print(f"   Max peak workload:  {mc_results['max_peak_workload']:.2f}x")
    print(f"   Vortex entries:     {mc_results['vortex_entries']}/{mc_results['n_runs']} ({mc_results['vortex_entries']/mc_results['n_runs']*100:.1f}%)")


def run_staffing_sensitivity(params: PCSSeasonParams, n_runs: int = 100) -> dict:
    """Run sensitivity analysis across different starting faculty counts."""
    results = {}

    for faculty_count in range(3, 11):
        test_params = PCSSeasonParams(
            initial_faculty=faculty_count,
            expected_faculty=params.expected_faculty,
            minimum_viable=params.minimum_viable,
            total_workload_units=params.total_workload_units,
            sustainable_workload=params.sustainable_workload,
            burnout_threshold=params.burnout_threshold,
            critical_threshold=params.critical_threshold,
            hiring_delay_days=params.hiring_delay_days,
        )

        mc = run_monte_carlo(test_params, n_runs=n_runs)
        results[faculty_count] = mc['survival_rate']

    return results


def print_sensitivity_analysis(sensitivity: dict):
    """Print staffing sensitivity analysis."""
    print("\n" + "="*70)
    print("  STAFFING SENSITIVITY ANALYSIS")
    print("="*70)

    print(f"\n📊 SURVIVAL RATE BY STARTING FACULTY COUNT:")
    print("   Faculty  Survival  Risk Level")
    print("   ───────  ────────  ──────────")

    for faculty, survival in sorted(sensitivity.items()):
        pct = survival * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))

        if pct >= 95:
            risk = "✅ Safe"
        elif pct >= 80:
            risk = "🟡 Manageable"
        elif pct >= 50:
            risk = "🟠 Risky"
        else:
            risk = "🔴 Critical"

        print(f"      {faculty:2d}     {pct:5.1f}%  {bar} {risk}")

    # Find thresholds
    safe_threshold = min((f for f, s in sensitivity.items() if s >= 0.95), default=None)
    manageable_threshold = min((f for f, s in sensitivity.items() if s >= 0.80), default=None)

    print(f"\n💡 THRESHOLDS:")
    if safe_threshold:
        print(f"   Safe (≥95% survival):       {safe_threshold}+ faculty")
    if manageable_threshold:
        print(f"   Manageable (≥80% survival): {manageable_threshold}+ faculty")


if __name__ == "__main__":
    print("\n" + "🏥 "*20)
    print("\n  PCS SEASON BATTLE TEST SIMULATION")
    print("  Your scenario: Arriving to 4 faculty (normal: 10)")
    print("\n" + "🏥 "*20)

    # Your program's parameters
    params = PCSSeasonParams()

    # Run single detailed simulation
    print("\n\n" + "─"*70)
    print("  PHASE 1: SINGLE SIMULATION (seed=42)")
    print("─"*70)
    result = run_single_simulation(params, seed=42)
    print_single_result(result, params)

    # Run Monte Carlo
    print("\n\n" + "─"*70)
    print("  PHASE 2: MONTE CARLO (100 runs)")
    print("─"*70)
    mc_results = run_monte_carlo(params, n_runs=100)
    print_monte_carlo_results(mc_results, params)

    # Run sensitivity analysis
    print("\n\n" + "─"*70)
    print("  PHASE 3: STAFFING SENSITIVITY (3-10 faculty)")
    print("─"*70)
    sensitivity = run_staffing_sensitivity(params, n_runs=100)
    print_sensitivity_analysis(sensitivity)

    print("\n" + "="*70)
    print("  SIMULATION COMPLETE")
    print("="*70 + "\n")
