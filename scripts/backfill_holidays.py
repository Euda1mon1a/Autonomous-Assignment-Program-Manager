#!/usr/bin/env python3
"""
Backfill holiday flags on existing Block records.

Updates blocks that were created before holiday detection was added.
Sets day_type, operational_intent, and actual_date for observed holidays.
Idempotent: safe to run multiple times.

Usage:
    # Dry run to see what would change
    python scripts/backfill_holidays.py --dry-run

    # Apply changes
    python scripts/backfill_holidays.py

    # Verbose output
    python scripts/backfill_holidays.py --verbose
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import or_

from app.db.session import SessionLocal
from app.models.block import Block
from app.models.day_type import DayType, get_default_operational_intent
from app.utils.holidays import get_federal_holidays, is_federal_holiday


def backfill_holidays(dry_run: bool = False, verbose: bool = False) -> tuple[int, int]:
    """
    Update existing blocks with holiday flags and day_type fields.

    Sets:
    - is_holiday = True
    - holiday_name = <holiday name>
    - day_type = FEDERAL_HOLIDAY
    - operational_intent = REDUCED_CAPACITY
    - actual_date = <actual calendar date if observed != actual>

    Args:
        dry_run: If True, don't commit changes
        verbose: If True, print each update

    Returns:
        Tuple of (updated_count, total_checked)
    """
    db = SessionLocal()
    updated = 0
    total = 0

    try:
        # Find blocks that need holiday backfill:
        # 1. is_holiday=False or NULL (never marked as holiday)
        # 2. is_holiday=True but day_type=NORMAL (marked but missing new fields)
        blocks = (
            db.query(Block)
            .filter(
                or_(
                    Block.is_holiday == False,  # noqa: E712
                    Block.is_holiday.is_(None),
                    # Also catch existing holidays missing new day_type fields
                    (Block.is_holiday == True) & (Block.day_type == DayType.NORMAL),  # noqa: E712
                )
            )
            .order_by(Block.date, Block.time_of_day)
            .all()
        )

        total = len(blocks)
        print(f"Checking {total} blocks for holiday status...")

        # Build holiday lookup dict with actual_date info
        # Key: observed date, Value: (name, actual_date or None)
        holiday_lookup: dict[date, tuple[str, date | None]] = {}
        if blocks:
            years = {b.date.year for b in blocks}
            for year in years:
                for holiday in get_federal_holidays(year):
                    holiday_lookup[holiday.date] = (holiday.name, holiday.actual_date)

        for block in blocks:
            is_hol, name = is_federal_holiday(block.date)

            if is_hol:
                # Get actual_date for observed holidays
                actual_date = None
                if block.date in holiday_lookup:
                    _, actual_date = holiday_lookup[block.date]

                if verbose:
                    observed_tag = (
                        f" [observed, actual={actual_date}]" if actual_date else ""
                    )
                    print(f"  UPDATE: {block.date} {block.time_of_day} → {name}{observed_tag}")

                if not dry_run:
                    block.is_holiday = True
                    block.holiday_name = name
                    block.day_type = DayType.FEDERAL_HOLIDAY
                    # Use default mapping to prevent drift if defaults change
                    block.operational_intent = get_default_operational_intent(
                        DayType.FEDERAL_HOLIDAY
                    )
                    block.actual_date = actual_date

                updated += 1

        if not dry_run:
            db.commit()
            print(f"\nCommitted {updated} updates")
        else:
            print(f"\n[DRY RUN] Would update {updated} blocks")

    finally:
        db.close()

    return updated, total


def main():
    parser = argparse.ArgumentParser(
        description="Backfill holiday flags on existing Block records.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes
  python scripts/backfill_holidays.py --dry-run --verbose

  # Apply changes
  python scripts/backfill_holidays.py
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each block as it's updated",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN MODE ===\n")

    updated, total = backfill_holidays(dry_run=args.dry_run, verbose=args.verbose)

    print(f"\nSummary: {updated} of {total} blocks marked as holidays")


if __name__ == "__main__":
    main()
