#!/usr/bin/env python3
"""
CLI tool for analyzing FMIT schedule swaps.

Usage:
    python -m app.cli.swap_analyzer --file schedule.xlsx --faculty "Dr. Smith" --week 2025-03-03
    python -m app.cli.swap_analyzer --file schedule.xlsx --analyze-all
    python -m app.cli.swap_analyzer --file schedule.xlsx --alternating

Examples:
    # Find swap candidates for a specific faculty and week
    python -m app.cli.swap_analyzer -f fmit_schedule.xlsx -F "Johnson" -w 2025-03-10

    # Analyze all faculty with alternating patterns
    python -m app.cli.swap_analyzer -f fmit_schedule.xlsx --alternating

    # Full analysis with recommendations
    python -m app.cli.swap_analyzer -f fmit_schedule.xlsx --analyze-all --verbose
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Add parent to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.xlsx_import import (
    ExternalConflict,
    SwapFinder,
)


def parse_date(date_str: str) -> date:
    """Parse a date string in various formats."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d-%b-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}. Use YYYY-MM-DD format.")


def print_header(text: str, char: str = "=") -> None:
    """Print a header with underline."""
    print(f"\n{text}")
    print(char * len(text))


def print_swap_candidates(
    swap_finder: SwapFinder,
    target_faculty: str,
    target_week: date,
    verbose: bool = False,
) -> None:
    """Print swap candidates for a faculty/week."""
    candidates = swap_finder.find_swap_candidates(target_faculty, target_week)

    print_header(
        f"Swap Candidates for {target_faculty} - Week of {target_week.strftime('%b %d, %Y')}"
    )

    if not candidates:
        print("No swap candidates found.")
        return

    viable = [c for c in candidates if c.back_to_back_ok and not c.external_conflict]
    print(f"Total candidates: {len(candidates)} | Viable: {len(viable)}\n")

    for i, candidate in enumerate(candidates, 1):
        status = (
            "✓"
            if candidate.back_to_back_ok and not candidate.external_conflict
            else "✗"
        )
        swap_type = "1:1 swap" if candidate.gives_week else "absorb"

        print(f"{i}. [{status}] {candidate.faculty}")
        print(f"   Type: {swap_type}")

        if candidate.gives_week:
            print(f"   Gives back: {candidate.gives_week.strftime('%b %d, %Y')}")

        if not candidate.back_to_back_ok:
            print(f"   ⚠ Back-to-back conflict: {candidate.reason}")

        if candidate.external_conflict:
            print(f"   ⚠ External conflict: {candidate.external_conflict}")

        if verbose:
            print(f"   Flexibility: {candidate.flexibility}")

        print()


def print_alternating_patterns(swap_finder: SwapFinder, threshold: int = 3) -> None:
    """Print faculty with excessive alternating patterns."""
    print_header("Faculty with Alternating FMIT Patterns")

    alternating = swap_finder.find_excessive_alternating(threshold=threshold)

    if not alternating:
        print(f"No faculty found with {threshold}+ alternating cycles.")
        return

    print(f"Found {len(alternating)} faculty with {threshold}+ alternating cycles:\n")

    for faculty, cycle_count in alternating:
        weeks = swap_finder.faculty_weeks.get(faculty, [])
        sorted_weeks = sorted(weeks)

        print(f"• {faculty} ({cycle_count} alternating cycles)")
        print(f"  FMIT weeks: {', '.join(w.strftime('%b %d') for w in sorted_weeks)}")

        # Show suggested swaps
        suggestions = swap_finder.suggest_swaps_for_alternating(faculty)
        if suggestions:
            print("  Suggested weeks to swap out:")
            for week, candidates in suggestions[:3]:  # Show top 3
                viable_count = sum(1 for c in candidates if c.back_to_back_ok)
                print(
                    f"    - {week.strftime('%b %d')} ({viable_count} viable candidates)"
                )
        print()


def print_full_analysis(swap_finder: SwapFinder, verbose: bool = False) -> None:
    """Print comprehensive schedule analysis."""
    print_header("FMIT Schedule Analysis", "=")

    # Summary stats
    total_faculty = len(swap_finder.faculty_weeks)
    total_weeks = sum(len(weeks) for weeks in swap_finder.faculty_weeks.values())

    print("\nSummary:")
    print(f"  Faculty members: {total_faculty}")
    print(f"  Total FMIT weeks assigned: {total_weeks}")
    print(
        f"  Average weeks per faculty: {total_weeks / total_faculty:.1f}"
        if total_faculty
        else ""
    )

    # Week distribution
    print_header("Week Distribution", "-")
    for faculty in sorted(swap_finder.faculty_weeks.keys()):
        weeks = swap_finder.faculty_weeks[faculty]
        meta = swap_finder.faculty_targets.get(faculty)
        target = meta.target_weeks if meta else 6

        indicator = ""
        if len(weeks) < target - 1:
            indicator = " (under target)"
        elif len(weeks) > target + 1:
            indicator = " (over target)"

        print(f"  {faculty}: {len(weeks)} weeks{indicator}")

    # Alternating patterns
    print_alternating_patterns(swap_finder)

    # External conflicts summary
    if swap_finder.external_conflicts:
        print_header("Known External Conflicts", "-")
        for conflict in swap_finder.external_conflicts:
            print(
                f"  {conflict.faculty}: {conflict.conflict_type} "
                f"({conflict.start_date.strftime('%b %d')} - {conflict.end_date.strftime('%b %d')})"
            )
            if conflict.description:
                print(f"    {conflict.description}")


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze FMIT schedule swaps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="Path to FMIT schedule Excel file",
    )
    parser.add_argument(
        "-F",
        "--faculty",
        type=str,
        help="Target faculty member name (for swap candidate search)",
    )
    parser.add_argument(
        "-w",
        "--week",
        type=str,
        help="Target week (Monday) in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--alternating",
        action="store_true",
        help="Show faculty with excessive alternating patterns",
    )
    parser.add_argument(
        "--analyze-all",
        action="store_true",
        help="Run full schedule analysis",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Threshold for alternating pattern detection (default: 3)",
    )
    parser.add_argument(
        "--conflicts-file",
        type=str,
        help="Path to JSON file with external conflicts",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )

    args = parser.parse_args()

    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    # Load external conflicts if provided
    external_conflicts = []
    if args.conflicts_file:
        import json

        try:
            with open(args.conflicts_file) as f:
                conflicts_data = json.load(f)
            for c in conflicts_data:
                external_conflicts.append(
                    ExternalConflict(
                        faculty=c["faculty"],
                        start_date=parse_date(c["start_date"]),
                        end_date=parse_date(c["end_date"]),
                        conflict_type=c.get("conflict_type", "leave"),
                        description=c.get("description", ""),
                    )
                )
        except Exception as e:
            print(f"Warning: Failed to load conflicts file: {e}", file=sys.stderr)

    # Create SwapFinder
    try:
        swap_finder = SwapFinder.from_fmit_file(
            file_path=str(file_path),
            external_conflicts=external_conflicts if external_conflicts else None,
            include_absence_conflicts=False,  # No DB in CLI mode
        )
    except Exception as e:
        print(f"Error: Failed to parse schedule file: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Loaded schedule with {len(swap_finder.faculty_weeks)} faculty members")

    # Dispatch to appropriate action
    if args.analyze_all:
        print_full_analysis(swap_finder, verbose=args.verbose)
    elif args.alternating:
        print_alternating_patterns(swap_finder, threshold=args.threshold)
    elif args.faculty and args.week:
        try:
            target_week = parse_date(args.week)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        if args.faculty not in swap_finder.faculty_weeks:
            print(
                f"Error: Faculty '{args.faculty}' not found in schedule.",
                file=sys.stderr,
            )
            print(
                f"Available faculty: {', '.join(sorted(swap_finder.faculty_weeks.keys()))}",
                file=sys.stderr,
            )
            return 1

        print_swap_candidates(
            swap_finder, args.faculty, target_week, verbose=args.verbose
        )
    else:
        parser.print_help()
        print(
            "\nError: Specify --faculty and --week for swap search, or --analyze-all / --alternating for analysis"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
