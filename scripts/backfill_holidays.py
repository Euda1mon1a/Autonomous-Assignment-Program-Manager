#!/usr/bin/env python3
"""
Backfill holiday flags on existing Block records.

Updates blocks that were created before holiday detection was added.
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
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import or_

from app.db.session import SessionLocal
from app.models.block import Block
from app.utils.holidays import is_federal_holiday


def backfill_holidays(dry_run: bool = False, verbose: bool = False) -> tuple[int, int]:
    """
    Update existing blocks with holiday flags.

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
        # Find all blocks (we check both False and None for is_holiday)
        blocks = (
            db.query(Block)
            .filter(or_(Block.is_holiday == False, Block.is_holiday.is_(None)))  # noqa: E712
            .order_by(Block.date, Block.time_of_day)
            .all()
        )

        total = len(blocks)
        print(f"Checking {total} blocks for holiday status...")

        for block in blocks:
            is_hol, name = is_federal_holiday(block.date)

            if is_hol:
                if verbose:
                    print(f"  UPDATE: {block.date} {block.time_of_day} → {name}")

                if not dry_run:
                    block.is_holiday = True
                    block.holiday_name = name

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
