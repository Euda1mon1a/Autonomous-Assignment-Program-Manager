#!/usr/bin/env python3
"""
CSV Transform: Backend/Cowork Export → VBA Import Format

Pivots the long-format schedule CSV into the wide format
expected by the VBA ImportScheduleFromCSV() macro.

Usage:
    python csv_to_vba_format.py input.csv output.csv --block 10

Supported input formats:

1. Backend API format:
    Date,Time,Person,Type,PGY Level,Role,Activity
    2026-03-12,AM,"Smith, John",resident,3,primary,FMC

2. Cowork format:
    name,type,pgy_level,date,time_of_day,activity_code,display_code,source
    Cam Mayell,resident,3,2026-03-12,AM,fm_clinic,C,solver

VBA format (output):
    type,name,pgy,rotation,rotation2,2026-03-12_AM,2026-03-12_PM,...
    RES,"Mayell, Cam",3,,,C,C,...
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


# Block date ranges for AY 2025-2026
BLOCK_DATES = {
    10: (date(2026, 3, 12), date(2026, 4, 8)),
    11: (date(2026, 4, 9), date(2026, 5, 6)),
    12: (date(2026, 5, 7), date(2026, 6, 3)),
    13: (date(2026, 6, 4), date(2026, 7, 1)),
}


def get_block_dates(block_number: int) -> tuple[date, date]:
    """Get start and end dates for a block."""
    if block_number in BLOCK_DATES:
        return BLOCK_DATES[block_number]
    raise ValueError(f"Unknown block number: {block_number}. Valid: {list(BLOCK_DATES.keys())}")


def generate_date_columns(start_date: date, end_date: date) -> list[str]:
    """Generate column headers for all date/time slots."""
    columns = []
    current = start_date
    while current <= end_date:
        columns.append(f"{current.isoformat()}_AM")
        columns.append(f"{current.isoformat()}_PM")
        current += timedelta(days=1)
    return columns


def to_last_first(name: str) -> str:
    """Convert 'First Last' to 'Last, First' format."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name


def detect_format(fieldnames: list[str]) -> str:
    """Detect which CSV format we're working with."""
    if "display_code" in fieldnames:
        return "cowork"
    elif "Person" in fieldnames:
        return "backend"
    else:
        raise ValueError(f"Unknown CSV format. Headers: {fieldnames}")


def transform_csv(input_path: str, output_path: str, block_number: int, name_format: str = "last_first") -> dict:
    """
    Transform backend/Cowork CSV to VBA format.

    Args:
        input_path: Source CSV file
        output_path: Destination CSV file
        block_number: Block number (10-13)
        name_format: 'last_first' (default) or 'first_last'

    Returns stats dict with counts.
    """
    start_date, end_date = get_block_dates(block_number)
    date_columns = generate_date_columns(start_date, end_date)

    # Read input and build person data
    # Structure: {name: {pgy: int, type: str, schedule: {date_time: activity}}}
    people: dict[str, dict] = defaultdict(lambda: {
        "pgy": "",
        "type": "",
        "rotation": "",
        "rotation2": "",
        "schedule": {},
    })

    row_count = 0
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        csv_format = detect_format(fieldnames)
        print(f"Detected format: {csv_format}")

        for row in reader:
            row_count += 1

            if csv_format == "cowork":
                # Cowork format: name,type,pgy_level,date,time_of_day,activity_code,display_code,source
                name = row["name"]
                date_str = row["date"]
                time_slot = row["time_of_day"].upper()
                activity = row["display_code"] or ""  # Use display_code for VBA
                person_type = row["type"].lower()
                pgy = row["pgy_level"]
            else:
                # Backend API format: Date,Time,Person,Type,PGY Level,Role,Activity
                name = row["Person"]
                date_str = row["Date"]
                time_slot = row["Time"].upper()
                activity = row["Activity"] or ""
                person_type = row["Type"].lower()
                pgy = row["PGY Level"]

            # Convert name format if needed
            if name_format == "last_first":
                # Check if already "Last, First"
                if ", " not in name:
                    name = to_last_first(name)

            # Build the date_time key
            date_time_key = f"{date_str}_{time_slot}"

            # Update person record
            people[name]["schedule"][date_time_key] = activity
            people[name]["pgy"] = pgy or ""
            people[name]["type"] = "RES" if "resident" in person_type else "FAC"

    # Write output
    headers = ["type", "name", "pgy", "rotation", "rotation2"] + date_columns

    resident_count = 0
    faculty_count = 0

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        # Sort people: residents first (by PGY desc), then faculty
        def sort_key(item):
            name, data = item
            is_resident = data["type"] == "RES"
            pgy = int(data["pgy"]) if data["pgy"].isdigit() else 0
            return (not is_resident, -pgy, name)  # Residents first, higher PGY first

        for name, data in sorted(people.items(), key=sort_key):
            row = [
                data["type"],
                name,
                data["pgy"],
                data["rotation"],
                data["rotation2"],
            ]

            # Add schedule data for each date column
            for col in date_columns:
                row.append(data["schedule"].get(col, ""))

            writer.writerow(row)

            if data["type"] == "RES":
                resident_count += 1
            else:
                faculty_count += 1

    return {
        "input_rows": row_count,
        "residents": resident_count,
        "faculty": faculty_count,
        "date_columns": len(date_columns),
        "output_file": output_path,
        "format": csv_format,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Transform backend/Cowork schedule CSV to VBA import format"
    )
    parser.add_argument("input", help="Input CSV file (backend or Cowork format)")
    parser.add_argument("output", help="Output CSV file (VBA format)")
    parser.add_argument(
        "--block", "-b",
        type=int,
        required=True,
        help="Block number (10-13)"
    )
    parser.add_argument(
        "--name-format",
        choices=["last_first", "first_last"],
        default="last_first",
        help="Output name format (default: last_first for VBA)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        stats = transform_csv(args.input, args.output, args.block, args.name_format)

        print(f"✅ Transform complete!")
        print(f"   Format detected: {stats['format']}")
        print(f"   Input rows: {stats['input_rows']}")
        print(f"   Residents: {stats['residents']}")
        print(f"   Faculty: {stats['faculty']}")
        print(f"   Date columns: {stats['date_columns']}")
        print(f"   Output: {stats['output_file']}")
        print()
        print("Next steps:")
        print(f"  1. Copy {stats['output_file']} to same folder as Excel workbook")
        print(f"  2. Rename to SCHEDULE_OUTPUT.csv")
        print("  3. Run ImportScheduleFromCSV() macro in Excel")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
