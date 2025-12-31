#!/usr/bin/env python3
"""
CLI schedule generation script.

Generates schedules from command line without running the full application.

Usage:
    python scripts/scheduling/generate_schedule.py --start 2025-07-01 --end 2025-09-30
    python scripts/scheduling/generate_schedule.py --block 10
    python scripts/scheduling/generate_schedule.py --start 2025-07-01 --algorithm cp_sat --timeout 300
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.db.session import SessionLocal
from app.models.block import Block
from app.scheduling.engine import ScheduleGenerator
from sqlalchemy import select


def parse_date(date_str: str) -> date:
    """Parse date string."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_block_dates(db, block_number: int) -> tuple[date, date]:
    """Get start and end dates for a block number."""
    first_block = db.execute(
        select(Block)
        .where(Block.block_number == block_number)
        .order_by(Block.date.asc())
        .limit(1)
    ).scalar_one_or_none()

    if not first_block:
        raise ValueError(f"Block {block_number} not found in database")

    last_block = db.execute(
        select(Block)
        .where(Block.block_number == block_number)
        .order_by(Block.date.desc())
        .limit(1)
    ).scalar_one()

    return first_block.date, last_block.date


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CLI schedule generation script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for date range
  python scripts/scheduling/generate_schedule.py \\
      --start 2025-07-01 --end 2025-09-30

  # Generate for specific block
  python scripts/scheduling/generate_schedule.py --block 10

  # Use specific algorithm with timeout
  python scripts/scheduling/generate_schedule.py \\
      --start 2025-07-01 --end 2025-09-30 \\
      --algorithm cp_sat --timeout 300

  # Save to file
  python scripts/scheduling/generate_schedule.py \\
      --block 10 --output schedule.json
        """,
    )

    # Date range options
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    date_group.add_argument(
        "--block",
        type=int,
        help="Block number (1-13)",
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD), required if --start is used",
    )

    # Algorithm options
    parser.add_argument(
        "--algorithm",
        choices=["greedy", "cp_sat", "pulp", "hybrid"],
        default="greedy",
        help="Scheduling algorithm (default: greedy)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Solver timeout in seconds (default: 60)",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        help="Save schedule to JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate schedule without saving to database",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    try:
        # Validate arguments
        if args.start and not args.end:
            parser.error("--end is required when using --start")

        # Initialize database
        db = SessionLocal()

        try:
            # Determine date range
            if args.block:
                start_date, end_date = get_block_dates(db, args.block)
                print(f"Block {args.block}: {start_date} to {end_date}")
            else:
                start_date = parse_date(args.start)
                end_date = parse_date(args.end)

            print("=" * 70)
            print("Schedule Generation")
            print("=" * 70)
            print(f"\nDate Range: {start_date} to {end_date}")
            print(f"Algorithm: {args.algorithm}")
            print(f"Timeout: {args.timeout}s")

            if args.dry_run:
                print("\n⚠ DRY RUN MODE - No changes will be saved")

            # Initialize generator
            generator = ScheduleGenerator(db)

            # Generate schedule
            print("\nGenerating schedule...")

            result = generator.generate(
                start_date=start_date,
                end_date=end_date,
                algorithm=args.algorithm,
                timeout=args.timeout,
            )

            # Display results
            print("\n" + "=" * 70)
            print("Generation Complete")
            print("=" * 70)
            print(f"\nAssignments Created: {len(result.assignments)}")
            print(f"Violations: {result.violation_count}")
            print(f"Score: {result.score:.4f}")
            print(f"Generation Time: {result.generation_time:.2f}s")

            if result.violations and args.verbose:
                print("\nViolations:")
                for violation in result.violations[:10]:
                    print(f"  - {violation}")
                if len(result.violations) > 10:
                    print(f"  ... and {len(result.violations) - 10} more")

            # Save to database
            if not args.dry_run:
                print("\nSaving to database...")
                for assignment in result.assignments:
                    db.add(assignment)
                db.commit()
                print("✓ Saved successfully")

            # Export to file
            if args.output:
                print(f"\nExporting to {args.output}...")

                data = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "algorithm": args.algorithm,
                    "score": result.score,
                    "violation_count": result.violation_count,
                    "generation_time": result.generation_time,
                    "assignments": [
                        {
                            "person_id": str(a.person_id),
                            "block_id": str(a.block_id),
                            "rotation_id": str(a.rotation_id) if a.rotation_id else None,
                            "date": a.block.date.isoformat() if a.block else None,
                            "session": a.block.session if a.block else None,
                        }
                        for a in result.assignments
                    ],
                    "violations": [str(v) for v in result.violations],
                }

                args.output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(data, f, indent=2)

                print(f"✓ Exported to {args.output}")

            print("\n" + "=" * 70)

            # Return exit code based on violations
            if result.violation_count > 0:
                print("⚠ Schedule generated with violations")
                return 1
            else:
                print("✓ Schedule generated successfully")
                return 0

        finally:
            db.close()

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
