#!/usr/bin/env python3
"""
Generate scheduling blocks (AM/PM half-days) for academic year.

Each day has 2 blocks: AM and PM.
Academic year: July 1 - June 30 (final block extends to cover the last day)

Usage:
    # Generate blocks for Block 10 (March 12 - April 8, 2026)
    python scripts/generate_blocks.py --start 2026-03-12 --end 2026-04-08 --block-number 10

    # Generate full academic year 2025-2026 (starts July 1, 2025)
    python scripts/generate_blocks.py --academic-year 2025

    # Dry run to see what would be created
    python scripts/generate_blocks.py --academic-year 2025 --dry-run
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.models.block import Block
from app.utils.holidays import is_federal_holiday


def get_first_thursday(reference_date: date) -> date:
    """
    Find the first Thursday on or after the reference date.

    Blocks always start on Thursday and end on Wednesday (28 days).

    Args:
        reference_date: Date to start searching from (e.g., July 1)

    Returns:
        The first Thursday on or after reference_date
    """
    days_until_thursday = (3 - reference_date.weekday()) % 7
    return reference_date + timedelta(days=days_until_thursday)


def calculate_block_dates(
    block_number: int, academic_year_start: date
) -> tuple[date, date]:
    """
    Calculate start and end dates for a given block number.

    Each block is 4 weeks (28 days), starting Thursday and ending Wednesday.
    Academic year starts July 1, but Block 1 begins on the first Thursday.

    Args:
        block_number: Block number (1-13)
        academic_year_start: Start date of academic year (e.g., July 1)

    Returns:
        Tuple of (block_start, block_end) dates
    """
    # Blocks start on first Thursday of the academic year
    block_1_start = get_first_thursday(academic_year_start)
    block_start = block_1_start + timedelta(days=(block_number - 1) * 28)
    block_end = block_start + timedelta(days=27)

    academic_year_end = date(academic_year_start.year + 1, 6, 30)
    if (
        block_number == 13
        and academic_year_start.month == 7
        and academic_year_start.day == 1
        and block_end < academic_year_end
    ):
        # Extend the final block to include the last day of the academic year.
        block_end = academic_year_end

    return block_start, block_end


def generate_blocks(
    start_date: date,
    end_date: date,
    block_number: int,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """
    Generate AM/PM blocks for each day in range.

    Args:
        start_date: First date to generate blocks for
        end_date: Last date to generate blocks for
        block_number: Academic year block number (1-13)
        dry_run: If True, don't actually create blocks
        verbose: If True, print each block as it's created

    Returns:
        Tuple of (created_count, skipped_count)
    """
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        current = start_date
        while current <= end_date:
            is_weekend = current.weekday() >= 5  # Saturday = 5, Sunday = 6
            is_holiday, holiday_name = is_federal_holiday(current)

            for tod in ["AM", "PM"]:
                # Check if block already exists
                existing = (
                    db.query(Block)
                    .filter(Block.date == current, Block.time_of_day == tod)
                    .first()
                )

                if existing:
                    skipped += 1
                    if verbose:
                        print(f"  SKIP: {current} {tod} (already exists)")
                    continue

                if not dry_run:
                    block = Block(
                        date=current,
                        time_of_day=tod,
                        block_number=block_number,
                        is_weekend=is_weekend,
                        is_holiday=is_holiday,
                        holiday_name=holiday_name,
                    )
                    db.add(block)

                created += 1
                if verbose:
                    weekend_tag = " (weekend)" if is_weekend else ""
                    holiday_tag = f" ({holiday_name})" if is_holiday else ""
                    print(f"  CREATE: {current} {tod}{weekend_tag}{holiday_tag}")

            current += timedelta(days=1)

        if not dry_run:
            db.commit()

    finally:
        db.close()

    return created, skipped


def generate_academic_year(
    year: int, dry_run: bool = False, verbose: bool = False
) -> tuple[int, int]:
    """
    Generate all 13 blocks for an academic year.

    Academic year 2025 = July 1, 2025 to June 30, 2026

    Args:
        year: The calendar year when the academic year starts (e.g., 2025)
        dry_run: If True, don't actually create blocks
        verbose: If True, print each block as it's created

    Returns:
        Tuple of (total_created, total_skipped)
    """
    academic_year_start = date(year, 7, 1)
    academic_year_end = date(year + 1, 6, 30)
    total_created = 0
    total_skipped = 0

    print(f"Generating 13 blocks for Academic Year {year}-{year + 1}")
    print(f"Starting: {academic_year_start.strftime('%B %d, %Y')}\n")

    for block_num in range(1, 14):  # Blocks 1-13
        block_start, block_end = calculate_block_dates(block_num, academic_year_start)
        if block_num == 13:
            block_end = academic_year_end
        print(
            f"Block {block_num:2d}: {block_start.strftime('%b %d')} - {block_end.strftime('%b %d, %Y')}"
        )

        created, skipped = generate_blocks(
            start_date=block_start,
            end_date=block_end,
            block_number=block_num,
            dry_run=dry_run,
            verbose=verbose,
        )

        total_created += created
        total_skipped += skipped
        print(f"         Created: {created}, Skipped: {skipped}")

    return total_created, total_skipped


def main():
    parser = argparse.ArgumentParser(
        description="Generate scheduling blocks (AM/PM half-days) for academic year.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a single block period
  python scripts/generate_blocks.py --start 2026-03-12 --end 2026-04-08 --block-number 10

  # Generate full academic year 2025-2026
  python scripts/generate_blocks.py --academic-year 2025

  # Dry run to preview changes
  python scripts/generate_blocks.py --academic-year 2025 --dry-run --verbose
        """,
    )

    # Date range options
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD format)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD format)")
    parser.add_argument(
        "--block-number", type=int, help="Block number (1-13) for the date range"
    )

    # Academic year option
    parser.add_argument(
        "--academic-year",
        type=int,
        metavar="YEAR",
        help="Generate all 13 blocks for academic year starting in YEAR (e.g., 2025 for AY 2025-2026)",
    )

    # Behavior options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each block as it's created/skipped",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.academic_year:
        if args.start or args.end or args.block_number:
            parser.error(
                "--academic-year cannot be used with --start, --end, or --block-number"
            )

        if args.dry_run:
            print("=== DRY RUN MODE ===\n")

        total_created, total_skipped = generate_academic_year(
            year=args.academic_year, dry_run=args.dry_run, verbose=args.verbose
        )

        print(
            f"\n{'Would create' if args.dry_run else 'Created'} {total_created} blocks"
        )
        print(f"Skipped {total_skipped} existing blocks")

    elif args.start and args.end and args.block_number:
        try:
            start_date = date.fromisoformat(args.start)
            end_date = date.fromisoformat(args.end)
        except ValueError as e:
            parser.error(f"Invalid date format: {e}. Use YYYY-MM-DD format.")

        if start_date > end_date:
            parser.error("Start date must be before or equal to end date")

        if not 1 <= args.block_number <= 13:
            parser.error("Block number must be between 1 and 13")

        if args.dry_run:
            print("=== DRY RUN MODE ===\n")

        print(f"Generating blocks for Block {args.block_number}")
        print(f"Date range: {start_date} to {end_date}\n")

        created, skipped = generate_blocks(
            start_date=start_date,
            end_date=end_date,
            block_number=args.block_number,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

        print(f"\n{'Would create' if args.dry_run else 'Created'} {created} blocks")
        print(f"Skipped {skipped} existing blocks")

    else:
        parser.error(
            "Either --academic-year OR (--start, --end, and --block-number) required.\n"
            "Run with --help for usage examples."
        )


if __name__ == "__main__":
    main()
