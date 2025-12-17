#!/usr/bin/env python3
"""
CLI tool for analyzing schedule Excel files for conflicts.

Usage:
    python analyze_schedule.py fmit_schedule.xlsx [clinic_schedule.xlsx]

Options:
    --specialty "Provider Name" "Specialty"  Mark a provider as specialty-only
    --json                                    Output as JSON
    --verbose                                 Show detailed slot-level output
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.xlsx_import import (
    analyze_schedule_conflicts,
)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze schedule Excel files for conflicts"
    )
    parser.add_argument(
        "fmit_file",
        help="FMIT rotation schedule Excel file"
    )
    parser.add_argument(
        "clinic_file",
        nargs="?",
        help="Clinic schedule Excel file (optional)"
    )
    parser.add_argument(
        "--specialty",
        nargs=2,
        action="append",
        metavar=("PROVIDER", "SPECIALTY"),
        help="Mark a provider as specialty (can be used multiple times)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    # Build specialty map
    specialty_providers = {}
    if args.specialty:
        for provider, specialty in args.specialty:
            if specialty not in specialty_providers:
                specialty_providers[specialty] = []
            specialty_providers[specialty].append(provider)

    # Run analysis
    result = analyze_schedule_conflicts(
        fmit_file=args.fmit_file,
        clinic_file=args.clinic_file,
        specialty_providers=specialty_providers if specialty_providers else None,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["success"] else 1

    # Human-readable output
    if not result["success"]:
        print(f"ERROR: {result.get('error', 'Unknown error')}")
        return 1

    print("=" * 60)
    print("SCHEDULE CONFLICT ANALYSIS")
    print("=" * 60)

    # FMIT schedule summary
    fmit = result.get("fmit_schedule", {})
    print("\nFMIT Schedule:")
    print(f"  Providers: {len(fmit.get('providers', []))}")
    print(f"  Date range: {fmit.get('date_range', [None, None])}")
    print(f"  FMIT slots: {fmit.get('fmit_slots', 0)}")

    if args.verbose and fmit.get("providers"):
        print(f"  Provider list: {', '.join(fmit['providers'])}")

    # Clinic schedule summary
    clinic = result.get("clinic_schedule")
    if clinic:
        print("\nClinic Schedule:")
        print(f"  Providers: {len(clinic.get('providers', []))}")
        print(f"  Date range: {clinic.get('date_range', [None, None])}")
        print(f"  Clinic slots: {clinic.get('clinic_slots', 0)}")

    # Conflicts
    conflicts = result.get("conflicts", [])
    summary = result.get("summary", {})

    print(f"\n{'=' * 60}")
    print(f"CONFLICTS FOUND: {summary.get('total_conflicts', 0)}")
    print(f"  Errors:   {summary.get('errors', 0)}")
    print(f"  Warnings: {summary.get('warnings', 0)}")
    print("=" * 60)

    if conflicts:
        # Group by type
        by_type = {}
        for c in conflicts:
            ctype = c["type"]
            if ctype not in by_type:
                by_type[ctype] = []
            by_type[ctype].append(c)

        for ctype, items in by_type.items():
            print(f"\n{ctype.upper().replace('_', ' ')} ({len(items)}):")
            for c in items:
                severity_marker = "!!" if c["severity"] == "error" else "!"
                print(f"  {severity_marker} {c['message']}")

    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n{'=' * 60}")
        print("RECOMMENDATIONS:")
        print("=" * 60)
        for r in recommendations:
            print(f"\n  [{r['type']}]")
            print(f"  {r['message']}")
            if r.get("providers"):
                print(f"  Affected: {', '.join(r['providers'])}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
