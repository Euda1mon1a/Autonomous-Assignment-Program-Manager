***REMOVED***!/usr/bin/env python3
"""
Compound Stress Simulation - Everything Happens At Once.

OBJECTIVE: SURVIVE
FMIT MUST CONTINUE - NO ADAPTATION POSSIBLE

FMIT Structure (RIGID):
- Friday AM to Sunday 1200: One attending (no breaks)
- Different faculty covers overnight calls
- Cannot be downregulated, cannot be adapted
- Either staffed by FM or turfed to OB (degraded)

Clinic (CAN ADAPT):
- Can downregulate to continuity weeks only
- Continuity = patients your residents have been following
- New patient slots can be dropped temporarily

ACGME FM Requirements:
- Minimum continuity weeks per resident per year
- Cannot go below this floor even in crisis
"""

import sys
import os

sys.path.insert(0, '/home/user/Autonomous-Assignment-Program-Manager/backend')
os.chdir('/home/user/Autonomous-Assignment-Program-Manager/backend')

***REMOVED*** Direct import to avoid broken __init__ chain
import importlib.util
spec = importlib.util.spec_from_file_location(
    "compound_stress_scenario",
    "/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/simulation/compound_stress_scenario.py"
)
compound_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compound_module)

CompoundStressConfig = compound_module.CompoundStressConfig
CompoundStressScenario = compound_module.CompoundStressScenario
run_compound_monte_carlo = compound_module.run_compound_monte_carlo
DefenseLevel = compound_module.DefenseLevel


def print_header():
    print("\n" + "="*70)
    print("  ⚔️  COMPOUND STRESS SIMULATION: EVERYTHING AT ONCE  ⚔️")
    print("="*70)
    print("\n  OBJECTIVE: SURVIVE")
    print("  FMIT MUST CONTINUE - NO ADAPTATION POSSIBLE")
    print("\n  FMIT Structure (RIGID):")
    print("  • Friday AM → Sunday 1200: One attending (no breaks)")
    print("  • Different faculty covers overnight calls")
    print("  • Cannot downregulate - either FM covers or OB turfs")
    print("\n  Clinic (CAN ADAPT):")
    print("  • Downregulate to continuity weeks only when needed")
    print("  • New patient slots dropped, continuity preserved")


def print_single_result(result, config):
    """Print detailed results from single simulation."""
    print("\n" + "─"*70)
    print("  SINGLE SIMULATION RESULT")
    print("─"*70)

    ***REMOVED*** FMIT Status - THE MISSION
    print("\n🎯 FMIT STATUS (THE MISSION):")
    if result.fmit_survived:
        if result.fmit_weeks_turfed == 0:
            print("   ✅ FMIT SURVIVED - All weeks covered by FM faculty")
        else:
            print(f"   🟡 FMIT SURVIVED - {result.fmit_weeks_turfed} weeks turfed to OB")
        print(f"   FM covered:  {result.fmit_weeks_covered} weeks")
        print(f"   OB covered:  {result.fmit_weeks_turfed} weeks")
    else:
        print(f"   ❌ FMIT FAILED - {result.fmit_weeks_failed} weeks UNCOVERED")
        print("   UNACCEPTABLE - Mission failed")

    ***REMOVED*** Staffing
    print(f"\n👥 STAFFING:")
    print(f"   Initial faculty:     {config.initial_faculty}")
    print(f"   Final faculty:       {result.final_faculty}")
    print(f"   Burnout departures:  {result.total_burnout_departures}")
    print(f"   Final screeners:     {result.final_screeners}")
    print(f"   Defense level:       {result.final_defense_level.name}")

    ***REMOVED*** Stress metrics
    print(f"\n📊 STRESS METRICS:")
    print(f"   Peak workload:       {result.peak_workload:.2f}x per physician")
    print(f"   Peak call frequency: q{result.peak_call_frequency:.1f} days")
    print(f"   Days in crisis:      {result.days_in_crisis}/{result.days_survived} ({result.days_in_crisis/max(1,result.days_survived)*100:.0f}%)")

    ***REMOVED*** Screener fallback
    print(f"\n🩺 SCREENER FALLBACK:")
    print(f"   Days below min ratio: {result.days_below_min_screener_ratio}")
    print(f"   RN fallback days:     {result.rn_fallback_days}")
    print(f"   EMT fallback days:    {result.emt_fallback_days}")

    ***REMOVED*** Recommendations
    if result.recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"   {rec}")

    ***REMOVED*** Timeline - key milestones
    print(f"\n📅 TIMELINE:")
    milestones = [0, 7, 30, 60, 90, 180, 364]
    for day in milestones:
        if day < len(result.states):
            s = result.states[day]
            defense_emoji = {
                DefenseLevel.GREEN: "🟢",
                DefenseLevel.YELLOW: "🟡",
                DefenseLevel.ORANGE: "🟠",
                DefenseLevel.RED: "🔴",
                DefenseLevel.BLACK: "⚫",
            }
            emoji = defense_emoji.get(s.defense_level, "❓")
            fmit = "FM" if s.fmit_covered and not s.fmit_turfed_to_ob else "OB" if s.fmit_turfed_to_ob else "❌"
            print(f"   Day {day:3d}: {s.faculty_count}F/{s.screener_dedicated}S | "
                  f"wl={s.workload_per_physician:.1f}x | "
                  f"q{s.call_interval_days:.0f} | "
                  f"FMIT:{fmit} {emoji}")


def print_monte_carlo_results(mc, config):
    """Print Monte Carlo results."""
    print("\n" + "─"*70)
    print("  MONTE CARLO ANALYSIS (100 runs)")
    print("─"*70)

    ***REMOVED*** THE METRIC: FMIT survival
    print(f"\n🎯 FMIT SURVIVAL (THE MISSION):")
    fmit_pct = mc['fmit_survival_rate'] * 100
    if fmit_pct >= 95:
        status = "✅ MISSION VIABLE"
    elif fmit_pct >= 80:
        status = "🟡 MISSION AT RISK"
    elif fmit_pct >= 50:
        status = "🟠 MISSION CRITICAL"
    else:
        status = "🔴 MISSION FAILURE LIKELY"
    print(f"   FMIT survival rate: {fmit_pct:.0f}% {status}")
    print(f"   Avg weeks turfed to OB: {mc['avg_fmit_turfed']:.1f}")
    print(f"   Avg weeks FAILED: {mc['avg_fmit_failed']:.1f}")

    ***REMOVED*** System survival
    print(f"\n📊 SYSTEM METRICS:")
    print(f"   System survival:       {mc['survival_rate']*100:.0f}%")
    print(f"   Avg days survived:     {mc['avg_days_survived']:.0f}")
    print(f"   Avg burnout departures: {mc['avg_burnout_departures']:.1f}")
    print(f"   Avg days in crisis:    {mc['avg_days_crisis']:.0f}")


def run_sensitivity_analysis(base_config):
    """Run sensitivity analysis for faculty counts."""
    print("\n" + "─"*70)
    print("  STAFFING SENSITIVITY: FMIT SURVIVAL BY FACULTY COUNT")
    print("─"*70)

    print("\n📊 FMIT SURVIVAL RATE BY STARTING FACULTY:")
    print("   Faculty  FMIT Survives  Status")
    print("   ───────  ─────────────  ──────────")

    results = {}
    for faculty in range(3, 11):
        config = CompoundStressConfig(
            initial_faculty=faculty,
            expected_faculty=10,
            initial_screeners_dedicated=base_config.initial_screeners_dedicated,
            initial_screeners_rn=base_config.initial_screeners_rn,
            initial_screeners_emt=base_config.initial_screeners_emt,
        )
        mc = run_compound_monte_carlo(config, n_runs=50)
        results[faculty] = mc['fmit_survival_rate']

        pct = mc['fmit_survival_rate'] * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))

        if pct >= 95:
            status = "✅ FMIT Safe"
        elif pct >= 80:
            status = "🟡 FMIT At Risk"
        elif pct >= 50:
            status = "🟠 FMIT Critical"
        else:
            status = "🔴 FMIT Failure"

        print(f"      {faculty:2d}       {pct:5.1f}%     {bar} {status}")

    ***REMOVED*** Find thresholds
    safe = min((f for f, r in results.items() if r >= 0.95), default=None)
    viable = min((f for f, r in results.items() if r >= 0.80), default=None)

    print(f"\n💡 FMIT THRESHOLDS:")
    if safe:
        print(f"   Safe (≥95% FMIT survival):   {safe}+ faculty")
    if viable:
        print(f"   Viable (≥80% FMIT survival): {viable}+ faculty")

    return results


def run_screener_sensitivity(base_config):
    """Test screener configurations for FMIT survival."""
    print("\n" + "─"*70)
    print("  SCREENER SENSITIVITY: FMIT SURVIVAL BY SCREENER CONFIG")
    print("─"*70)

    print("\n  Testing: 4 faculty with varying screener support")
    print("  Dedicated/RN/EMT  FMIT Survives")
    print("  ───────────────── ─────────────")

    configs = [
        (2, 3, 2, "Current: 2 dedicated, 3 RN, 2 EMT"),
        (1, 3, 2, "Reduced: 1 dedicated, 3 RN, 2 EMT"),
        (0, 3, 2, "No dedicated: 0 dedicated, 3 RN, 2 EMT"),
        (3, 3, 2, "Added: 3 dedicated, 3 RN, 2 EMT"),
        (4, 3, 2, "Full: 4 dedicated, 3 RN, 2 EMT"),
    ]

    for ded, rn, emt, label in configs:
        config = CompoundStressConfig(
            initial_faculty=4,  ***REMOVED*** YOUR SCENARIO
            initial_screeners_dedicated=ded,
            initial_screeners_rn=rn,
            initial_screeners_emt=emt,
        )
        mc = run_compound_monte_carlo(config, n_runs=50)
        pct = mc['fmit_survival_rate'] * 100
        print(f"  {ded}/{rn}/{emt}               {pct:5.1f}%    {label}")


if __name__ == "__main__":
    print_header()

    ***REMOVED*** Your scenario
    config = CompoundStressConfig(
        initial_faculty=4,
        expected_faculty=10,
        minimum_faculty_for_fmit=5,  ***REMOVED*** Reality: need 5 for safe FMIT
        initial_screeners_dedicated=2,
        initial_screeners_rn=3,
        initial_screeners_emt=2,
        initial_interns=4,
        initial_seniors=4,
        ***REMOVED*** FMIT is RIGID
        fmit_weeks_per_year=52,
        fmit_faculty_required=1,
        fmit_can_turf_to_ob=True,
        ***REMOVED*** ACGME minimum continuity
        ***REMOVED*** (clinic can downregulate but must maintain minimum)
    )

    ***REMOVED*** Single run
    print("\n\n" + "─"*70)
    print("  PHASE 1: SINGLE SIMULATION")
    print("─"*70)
    scenario = CompoundStressScenario(config)
    result = scenario.run()
    print_single_result(result, config)

    ***REMOVED*** Monte Carlo
    print("\n\n" + "─"*70)
    print("  PHASE 2: MONTE CARLO (100 runs)")
    print("─"*70)
    mc = run_compound_monte_carlo(config, n_runs=100)
    print_monte_carlo_results(mc, config)

    ***REMOVED*** Faculty sensitivity
    print("\n\n" + "─"*70)
    print("  PHASE 3: FACULTY SENSITIVITY")
    print("─"*70)
    run_sensitivity_analysis(config)

    ***REMOVED*** Screener sensitivity
    print("\n\n" + "─"*70)
    print("  PHASE 4: SCREENER SENSITIVITY")
    print("─"*70)
    run_screener_sensitivity(config)

    print("\n" + "="*70)
    print("  SIMULATION COMPLETE")
    print("="*70)
    print("\n  Remember: FMIT has NO adaptation.")
    print("  Friday AM → Sunday 1200: One attending, no breaks.")
    print("  Either FM covers, or OB turfs. That's the only choice.\n")
