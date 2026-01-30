"""
Usage examples for the Burnout Fire Index system.

This module demonstrates how to use the multi-temporal burnout danger
rating system adapted from the Canadian Forest Fire Weather Index.
"""

from uuid import uuid4

from app.resilience.burnout_fire_index import (
    BurnoutDangerRating,
)


def example_single_resident():
    """Calculate danger for a single resident."""
    rating = BurnoutDangerRating()

    # Example: Resident with moderate concern
    report = rating.calculate_burnout_danger(
        resident_id=uuid4(),
        recent_hours=71.0,  # Hours worked last 2 weeks
        monthly_load=264.0,  # Average monthly hours (last 3 months)
        yearly_satisfaction=0.56,  # Job satisfaction (0.0-1.0)
        workload_velocity=4.5,  # Hours/week increase rate
    )

    print(f"Danger Class: {report.danger_class.value.upper()}")
    print(f"FWI Score: {report.fwi_score:.1f}")
    print(f"Safe: {report.is_safe}")
    print(f"Requires Intervention: {report.requires_intervention}")
    print("\nComponent Breakdown:")
    print(f"  FFMC (2-week): {report.component_scores['ffmc']:.1f}")
    print(f"  DMC (3-month): {report.component_scores['dmc']:.1f}")
    print(f"  DC (1-year): {report.component_scores['dc']:.1f}")
    print("\nRecommended Restrictions:")
    for restriction in report.recommended_restrictions:
        print(f"  - {restriction}")

    return report


def example_program_screening():
    """Screen an entire residency program for burnout risk."""
    rating = BurnoutDangerRating()

    # Simulated resident data
    residents = [
        {
            "resident_id": uuid4(),
            "recent_hours": 52.0,
            "monthly_load": 225.0,
            "yearly_satisfaction": 0.87,
            "workload_velocity": 0.0,
        },
        {
            "resident_id": uuid4(),
            "recent_hours": 71.0,
            "monthly_load": 264.0,
            "yearly_satisfaction": 0.56,
            "workload_velocity": 4.5,
        },
        {
            "resident_id": uuid4(),
            "recent_hours": 82.0,
            "monthly_load": 292.0,
            "yearly_satisfaction": 0.28,
            "workload_velocity": 9.0,
        },
        {
            "resident_id": uuid4(),
            "recent_hours": 88.0,
            "monthly_load": 305.0,
            "yearly_satisfaction": 0.18,
            "workload_velocity": 13.0,
        },
    ]

    # Calculate danger for all residents (returns sorted by FWI, highest first)
    reports = rating.calculate_batch_danger(residents)

    print(f"Program Burnout Screening ({len(reports)} residents):\n")
    print(f"{'Rank':<6} {'Danger':<12} {'FWI':<8} {'Intervention'}")
    print("-" * 50)

    for i, report in enumerate(reports, 1):
        intervention = "YES" if report.requires_intervention else "No"
        print(
            f"{i:<6} {report.danger_class.value.upper():<12} "
            f"{report.fwi_score:<8.1f} {intervention}"
        )

        # Identify critical cases
    critical_cases = [r for r in reports if r.requires_intervention]
    print(f"\n⚠️  {len(critical_cases)} residents require immediate intervention")

    return reports


def example_component_analysis() -> None:
    """Analyze individual FWI components."""
    rating = BurnoutDangerRating()

    print("Component Analysis Examples:\n")

    # FFMC - Fine Fuel Moisture Code (2-week acute stress)
    print("1. FFMC (Recent Hours vs 60h target):")
    for hours in [50, 60, 70, 80, 90]:
        ffmc = rating.calculate_fine_fuel_moisture_code(hours, target=60.0)
        print(f"   {hours}h → FFMC={ffmc:5.1f}")

        # DMC - Duff Moisture Code (3-month sustained load)
    print("\n2. DMC (Monthly Hours vs 240h target):")
    for monthly in [220, 240, 260, 280, 300]:
        dmc = rating.calculate_duff_moisture_code(monthly, target=240.0)
        print(f"   {monthly}h → DMC={dmc:5.1f}")

        # DC - Drought Code (yearly satisfaction)
    print("\n3. DC (Job Satisfaction):")
    for satisfaction in [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]:
        dc = rating.calculate_drought_code(satisfaction)
        print(f"   {satisfaction:.1f} → DC={dc:5.1f}")

        # ISI - Initial Spread Index (FFMC + velocity)
    print("\n4. ISI (Spread Rate):")
    ffmc = 70.0
    for velocity in [-5, 0, 5, 10, 15]:
        isi = rating.calculate_initial_spread_index(ffmc, velocity)
        print(f"   FFMC={ffmc}, velocity={velocity:+3.0f}h/wk → ISI={isi:5.1f}")


def example_custom_targets() -> None:
    """Use custom targets for different specialties or programs."""
    # Some specialties may have different sustainable workload targets

    # Example: Surgery residency with higher expected hours
    surgery_rating = BurnoutDangerRating(
        ffmc_target=70.0,  # 70h per 2 weeks (vs 60h default)
        dmc_target=280.0,  # 280h per month (vs 240h default)
    )

    report = surgery_rating.calculate_burnout_danger(
        resident_id=uuid4(),
        recent_hours=72.0,  # Would be high for IM, moderate for surgery
        monthly_load=275.0,  # Ditto
        yearly_satisfaction=0.7,
        workload_velocity=2.0,
    )

    print("Surgery Residency (adjusted targets):")
    print(
        f"  72h/2wk, 275h/mo → {report.danger_class.value.upper()} (FWI={report.fwi_score:.1f})"
    )


def example_danger_thresholds() -> None:
    """Show all danger classification thresholds."""
    rating = BurnoutDangerRating()

    print("Danger Classification Thresholds:\n")

    test_fwi_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    for fwi in test_fwi_values:
        danger_class = rating.classify_danger(fwi)
        print(f"FWI={fwi:3.0f} → {danger_class.value.upper()}")


def example_temporal_integration() -> None:
    """Demonstrate multi-temporal integration concept."""
    rating = BurnoutDangerRating()

    print("Multi-Temporal Integration:\n")

    scenarios = [
        ("Only recent high", 80.0, 220.0, 0.9, 0.0),
        ("Only monthly high", 50.0, 290.0, 0.9, 0.0),
        ("Only satisfaction low", 50.0, 220.0, 0.2, 0.0),
        ("All scales aligned", 85.0, 300.0, 0.2, 12.0),
    ]

    for name, hours, monthly, satisfaction, velocity in scenarios:
        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=hours,
            monthly_load=monthly,
            yearly_satisfaction=satisfaction,
            workload_velocity=velocity,
        )
        print(
            f"{name:25s} → {report.danger_class.value.upper():<12} (FWI={report.fwi_score:.1f})"
        )

    print("\n→ Burnout requires alignment across multiple temporal scales")
    print("→ Single scale high = LOW/MODERATE")
    print("→ All scales high = EXTREME")


if __name__ == "__main__":
    print("=" * 70)
    print("BURNOUT FIRE INDEX - Usage Examples")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("Example 1: Single Resident Assessment")
    print("=" * 70)
    example_single_resident()

    print("\n" + "=" * 70)
    print("Example 2: Program-Wide Screening")
    print("=" * 70)
    example_program_screening()

    print("\n" + "=" * 70)
    print("Example 3: Component Analysis")
    print("=" * 70)
    example_component_analysis()

    print("\n" + "=" * 70)
    print("Example 4: Custom Targets (Surgery Residency)")
    print("=" * 70)
    example_custom_targets()

    print("\n" + "=" * 70)
    print("Example 5: Danger Thresholds")
    print("=" * 70)
    example_danger_thresholds()

    print("\n" + "=" * 70)
    print("Example 6: Temporal Integration Concept")
    print("=" * 70)
    example_temporal_integration()
