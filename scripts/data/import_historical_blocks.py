"""Import historical block schedules (2-11) from ground truth JSON into DB.

Reads the structured JSON produced by extract_ground_truth.py and upserts
half-day assignments (HDAs) for each block. This is the multi-block equivalent
of import_block12.py but operates on pre-extracted JSON rather than raw Excel.

Upsert logic:
  - If HDA exists with source='manual': SKIP (already imported, don't clobber)
  - If HDA exists with source='solver'|'template': OVERWRITE, set source='manual'
  - If no HDA exists: INSERT with source='manual'
  - With --force: re-import even if manual exists

Usage:
    # Dry run (report only):
    backend/.venv/bin/python scripts/data/import_historical_blocks.py \
        --truth /tmp/ground_truth.json --blocks 2 3 4 5 6 7 8 9 10 11 --dry-run

    # Import:
    backend/.venv/bin/python scripts/data/import_historical_blocks.py \
        --truth /tmp/ground_truth.json --blocks 2 3 4 5 6 7 8 9 10 11
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import psycopg2

sys.path.insert(0, "scripts/data")
from code_maps import CODE_MAP, display_to_db  # noqa: E402

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

# ── Name Matching ────────────────────────────────────────────────────────────
# Maps "Last, First" from Excel to DB name. Reuses the same manual mapping
# from import_block12.py. This must stay local (OPSEC: no real names in git).

NAME_MAP = {
    # PGY-3 (R3) — includes graduated R3s from earlier blocks
    "Connolly, Laura": "Laura Connolly",
    "Hernandez, Christian*": "Christian Hernandez",
    "Mayell, Cameron*": "Cam Mayell",
    "Petrie, William*": "Clay Petrie",
    "You, Jae*": "Jae You",
    "Doria, Russell*": "Russell Doria",
    "Doyle, Jacob*": "Jacob Doyle",
    "Doyle, Jake": "Jacob Doyle",           # Alternate in later blocks
    "Evans, Amber": "Amber Evans",
    "Giblin, Bailey*": "Bailey Giblin",
    "Idelkope, Daniel": "Daniel Idelkope",
    "Kerby, Mary*": "Mary Kerby",
    "Machado, Jared*": "Jared Machado",
    # PGY-2 (R2)
    "Cataquiz, Felipe": "Felipe Cataquiz",
    "Cook, Scott": "Scott Cook",
    "Gigon, Alaine": "Alaine Gigon",
    "Headid, Ronald": "James Headid",
    "Maher, Nicholas": "Nick Maher",
    "Thomas, Devin": "Devin Thomas",
    "Booth, CJ": "CJ Booth",
    # PGY-1 (R1)
    "Sawyer, Tessa": "Tessa Sawyer",
    "Wilhelm, Clara": "Clara Wilhelm",
    "Travis, Colin": "Colin Travis",
    "Byrnes, Katherine": "Katie Byrnes",
    "Burns, Catherine": "Katie Byrnes",      # Alternate spelling
    "Sloss, Meleighe": "Meleigh Sloss",
    "Monsivais, Joshua": "Josh Monsivais",
    # Faculty (C19)
    "Bevis, Zach": "Zach Bevis",
    "Kinkennon, Sarah": "Sarah Kinkennon",
    "LaBounty, Alex*": "Alex LaBounty",
    "McGuire, Chris": "Chris McGuire",
    "Dahl, Brian*": "Brian Dahl",
    "McRae, Zachery": "Zach McRae",
    "Tagawa, Chelsea": "Chelsea Tagawa",
    "Montgomery, Aaron": "Aaron Montgomery",
    "Colgan, Bridget": "Bridget Colgan",
    "Chu, Jimmy*": "Jimmy Chu",
    "Chu, Jimmy": "Jimmy Chu",
    "Napierala, Joseph": "Joseph Napierala",
    "Thiel, Derrick": "Derrick Thiel",
    "Van Brunt, T. Blake": "Blake Van Brunt",
    "Samblanet, Kyle (IMA)*": "Kyle Samblanet",
    "Lamoureux, Anne": "Anne Lamoureux",
    "Bohringer, Kate": "Kate Bohringer",
    "Gomes, Lisa": "Lisa Gomes",
    # Visiting / IMA / TY residents
    "Bennett, Nick (IMA)*": "Nick Bennett",
    "Bennett, Nick (IMA)": "Nick Bennett",
    "Ching, Collette": "Collette Ching",
    "Davidson, Nathan": "Nathan Davidson",
    "Gouthro, Kathryn": "Kathryn Gouthro",
    "McGarity, Daniel": "Daniel McGarity",
    "Oh, Jaeyoung": "Jaeyoung Oh",
    "Wong-Lopez, Jaime": "Jaime Wong-Lopez",
    "Raymond, Tyler (IMA)*": "Tyler Raymond",
    "Richter, Jordan (25 Aug - 19 Sep)": "Jordan Richter",
    "Edward, Simon (TY)": "Simon Edward",
    "Icaza, Veronica (IM)": "Veronica Icaza",
    "Icaza, Veronica (IM) Mar 9-27?": "Veronica Icaza",
    "Nandakumar, Tharun (2 Sep - 26 Sep)": "Tharun Nandakumar",
    "Pusztai, Benjamin (2 Sep - 26 Sep)": "Benjamin Pusztai",
    "Smith, Alexa (2 Sep - 26 Sep)": "Alexa Smith",
}


def _last_name(name: str) -> str:
    """Extract lowercase last name from 'Last, First' or 'First Last'."""
    name = name.strip().rstrip("*").strip()
    if "," in name:
        return name.split(",")[0].strip().lower()
    parts = name.split()
    return parts[-1].lower() if parts else name.lower()


def load_ground_truth(path: Path) -> dict:
    """Load ground truth JSON from extract_ground_truth.py output."""
    return json.loads(path.read_text())


def build_person_index(cur) -> dict[str, str]:
    """Build {db_name: person_id} from people table."""
    cur.execute("SELECT id, name FROM people")
    return {name: str(pid) for pid, name in cur.fetchall()}


def build_activity_index(cur) -> dict[str, str]:
    """Build {activity_code: activity_id} from activities table, cached."""
    cur.execute("SELECT id, code FROM activities")
    return {code: str(aid) for aid, code in cur.fetchall()}


def resolve_block_dates(cur, block_number: int, academic_year: int = 2025) -> tuple[date, date] | None:
    """Get block start/end dates from academic_blocks table."""
    cur.execute(
        "SELECT start_date, end_date FROM academic_blocks "
        "WHERE block_number = %s AND academic_year = %s",
        (block_number, academic_year),
    )
    row = cur.fetchone()
    if row:
        return row[0], row[1]
    return None


def resolve_name(excel_name: str, person_index: dict[str, str]) -> str | None:
    """Resolve Excel name to person_id via NAME_MAP then DB lookup."""
    db_name = NAME_MAP.get(excel_name)
    if db_name:
        pid = person_index.get(db_name)
        if pid:
            return pid
    # Fallback: try last-name match
    ln = _last_name(excel_name)
    for name, pid in person_index.items():
        if _last_name(name) == ln:
            return pid
    return None


def import_block(
    cur,
    block_data: dict,
    person_index: dict[str, str],
    activity_index: dict[str, str],
    block_start: date,
    block_end: date,
    dry_run: bool = True,
    force: bool = False,
) -> dict:
    """Import one block's ground truth into half_day_assignments.

    Returns stats dict.
    """
    stats = {
        "block": block_data["tab_name"],
        "inserted": 0,
        "updated": 0,
        "skipped_manual": 0,
        "skipped_no_person": 0,
        "skipped_no_activity": 0,
        "skipped_no_date": 0,
        "unmapped_names": set(),
        "unmapped_codes": Counter(),
        "total_cells": 0,
    }

    # Build date list from block date range (28 days)
    num_days = (block_end - block_start).days + 1
    block_dates = [block_start + timedelta(days=i) for i in range(num_days)]

    for person in block_data["people"]:
        excel_name = person["name"]
        person_id = resolve_name(excel_name, person_index)

        if not person_id:
            stats["unmapped_names"].add(excel_name)
            continue

        for day in person["days"]:
            day_index = day["day_index"]

            # Map day_index to actual date from block calendar
            if day_index < 0 or day_index >= len(block_dates):
                continue

            actual_date = block_dates[day_index]

            for half, tod in [("am", "AM"), ("pm", "PM")]:
                display_code = day.get(half)
                if not display_code:
                    continue

                stats["total_cells"] += 1

                # Map display code to DB code
                db_code = display_to_db(display_code)
                activity_id = activity_index.get(db_code)

                if not activity_id:
                    stats["unmapped_codes"][display_code] += 1
                    stats["skipped_no_activity"] += 1
                    continue

                if dry_run:
                    # Check what would happen
                    cur.execute(
                        "SELECT source FROM half_day_assignments "
                        "WHERE person_id = %s AND date = %s AND time_of_day = %s",
                        (person_id, actual_date, tod),
                    )
                    row = cur.fetchone()
                    if row:
                        if row[0] == "manual" and not force:
                            stats["skipped_manual"] += 1
                        else:
                            stats["updated"] += 1
                    else:
                        stats["inserted"] += 1
                else:
                    # Real upsert
                    cur.execute(
                        "SELECT id, source FROM half_day_assignments "
                        "WHERE person_id = %s AND date = %s AND time_of_day = %s",
                        (person_id, actual_date, tod),
                    )
                    row = cur.fetchone()
                    if row:
                        existing_id, existing_source = row
                        if existing_source == "manual" and not force:
                            stats["skipped_manual"] += 1
                            continue
                        # Overwrite
                        cur.execute(
                            "UPDATE half_day_assignments "
                            "SET activity_id = %s, source = 'manual', updated_at = NOW() "
                            "WHERE id = %s",
                            (activity_id, existing_id),
                        )
                        stats["updated"] += 1
                    else:
                        # Insert
                        cur.execute(
                            "INSERT INTO half_day_assignments "
                            "(id, person_id, date, time_of_day, activity_id, source, "
                            "is_override, created_at, updated_at) "
                            "VALUES (%s, %s, %s, %s, %s, 'manual', false, NOW(), NOW())",
                            (str(uuid.uuid4()), person_id, actual_date, tod, activity_id),
                        )
                        stats["inserted"] += 1

    # Convert set to sorted list for JSON
    stats["unmapped_names"] = sorted(stats["unmapped_names"])
    stats["unmapped_codes"] = dict(stats["unmapped_codes"].most_common())
    return stats


def print_block_report(stats: dict):
    """Print per-block import report."""
    print(f"\n  {'─'*50}")
    print(f"  {stats['block']}")
    print(f"  {'─'*50}")
    print(f"    Total cells:      {stats['total_cells']:5d}")
    print(f"    Inserted:         {stats['inserted']:5d}")
    print(f"    Updated:          {stats['updated']:5d}")
    print(f"    Skipped (manual): {stats['skipped_manual']:5d}")
    print(f"    Skipped (person): {stats['skipped_no_person']:5d}")
    print(f"    Skipped (code):   {stats['skipped_no_activity']:5d}")

    if stats["unmapped_names"]:
        print(f"    Unmapped names ({len(stats['unmapped_names'])}):")
        for name in stats["unmapped_names"][:10]:
            print(f"      - {name}")

    if stats["unmapped_codes"]:
        print(f"    Unmapped codes ({len(stats['unmapped_codes'])}):")
        for code, cnt in list(stats["unmapped_codes"].items())[:10]:
            print(f"      - '{code}' ({cnt}x)")


def main():
    parser = argparse.ArgumentParser(
        description="Import historical blocks from ground truth JSON"
    )
    parser.add_argument("--truth", required=True, help="Path to ground_truth.json")
    parser.add_argument(
        "--blocks",
        nargs="+",
        type=int,
        default=list(range(2, 12)),
        help="Block numbers to import (default: 2-11)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report only, no DB changes")
    parser.add_argument("--force", action="store_true", help="Re-import even if manual exists")
    parser.add_argument("--academic-year", type=int, default=2025, help="Academic year (default: 2025)")
    args = parser.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.exists():
        print(f"ERROR: {truth_path} not found")
        sys.exit(1)

    print("=" * 60)
    mode = "DRY RUN" if args.dry_run else "LIVE IMPORT"
    print(f"  Historical Block Import — {mode}")
    print(f"  Blocks: {args.blocks}")
    print(f"  Academic Year: {args.academic_year}")
    if args.force:
        print("  Force mode: will overwrite existing manual entries")
    print("=" * 60)

    if not args.dry_run:
        print("\n  WARNING: This will modify the database.")
        print("  Ensure you have a backup (checkpoint.sh pre_historical_import)")

    # Load ground truth
    truth_data = load_ground_truth(truth_path)
    truth_blocks = {b["tab_name"]: b for b in truth_data["blocks"]}

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    person_index = build_person_index(cur)
    activity_index = build_activity_index(cur)

    print(f"\n  DB has {len(person_index)} people, {len(activity_index)} activities")

    all_stats = []
    totals = {
        "inserted": 0, "updated": 0, "skipped_manual": 0,
        "skipped_no_activity": 0, "total_cells": 0,
    }

    for block_num in args.blocks:
        tab_name = f"Block {block_num}"
        block_data = truth_blocks.get(tab_name)
        if not block_data:
            print(f"\n  SKIP: {tab_name} not found in ground truth")
            continue

        # Get block dates from DB
        block_dates = resolve_block_dates(cur, block_num, args.academic_year)
        if not block_dates:
            print(f"\n  SKIP: {tab_name} not found in academic_blocks table")
            continue

        block_start, block_end = block_dates

        stats = import_block(
            cur, block_data, person_index, activity_index,
            block_start, block_end,
            dry_run=args.dry_run, force=args.force,
        )
        all_stats.append(stats)
        print_block_report(stats)

        for key in totals:
            totals[key] += stats.get(key, 0)

    if not args.dry_run:
        conn.commit()
        print("\n  Committed to database.")
    else:
        conn.rollback()

    cur.close()
    conn.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"  TOTALS ({len(all_stats)} blocks)")
    print(f"{'='*60}")
    print(f"    Total cells:      {totals['total_cells']:5d}")
    print(f"    Would insert:     {totals['inserted']:5d}" if args.dry_run else f"    Inserted:         {totals['inserted']:5d}")
    print(f"    Would update:     {totals['updated']:5d}" if args.dry_run else f"    Updated:          {totals['updated']:5d}")
    print(f"    Skipped (manual): {totals['skipped_manual']:5d}")
    print(f"    Skipped (code):   {totals['skipped_no_activity']:5d}")

    # Aggregate unmapped codes across all blocks
    all_unmapped = Counter()
    all_unmapped_names = set()
    for s in all_stats:
        for code, cnt in s["unmapped_codes"].items():
            all_unmapped[code] += cnt
        all_unmapped_names.update(s["unmapped_names"])

    if all_unmapped:
        print(f"\n  ALL UNMAPPED CODES ({len(all_unmapped)}):")
        for code, cnt in all_unmapped.most_common(20):
            print(f"    '{code}' → '{display_to_db(code)}' ({cnt}x)")

    if all_unmapped_names:
        print(f"\n  ALL UNMAPPED NAMES ({len(all_unmapped_names)}):")
        for name in sorted(all_unmapped_names):
            print(f"    - {name}")


if __name__ == "__main__":
    main()
