"""Extract ground truth from handjam workbook → structured JSON.

Reads every schedule cell from block tabs that have full data (named residents),
producing labeled examples: (person, date, am/pm, display_code, rotation, block).

Usage:
    python scripts/ops/extract_ground_truth.py \
        --workbook ~/Downloads/"Current AY 25-26 pulled 29 JAN 2026.xlsx" \
        --output /tmp/ground_truth.json
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import load_workbook

# Layout constants (same across all block tabs)
ROW_DATES = 3
ROW_STAFF_CALL = 4
ROW_RES_CALL = 5
ROW_RESIDENTS_START = 9
ROW_RESIDENTS_END = 25
ROW_FACULTY_START = 31
ROW_FACULTY_END = 47
COL_ROTATION1 = 1   # A
COL_ROTATION2 = 2   # B
COL_TEMPLATE = 3     # C (R1/R2/R3/C19/ADJ/SPEC)
COL_ROLE = 4         # D (PGY 1/2/3, FAC, PSY)
COL_NAME = 5         # E
COL_SCHEDULE_START = 6
COL_SCHEDULE_END = 61  # inclusive
COLS_PER_DAY = 2

NBSP = "\xa0"


def extract_workbook(wb_path: Path) -> dict:
    """Extract ground truth from all viable block tabs."""
    wb = load_workbook(wb_path, read_only=True, data_only=True)

    result = {
        "source": str(wb_path.name),
        "blocks": [],
    }

    block_tabs = [s for s in wb.sheetnames if s.startswith("Block ") and s != "Block Schedule"]

    for tab_name in block_tabs:
        ws = wb[tab_name]

        # Check if this tab has named residents (Last, First format)
        has_names = False
        for row in range(ROW_RESIDENTS_START, ROW_RESIDENTS_END + 1):
            v = ws.cell(row=row, column=COL_NAME).value
            if v and v.strip() and v != NBSP and "," in v:
                has_names = True
                break

        if not has_names:
            continue

        # Extract dates from row 3 (even columns: 6, 8, 10, ...)
        dates = []
        for col in range(COL_SCHEDULE_START, COL_SCHEDULE_END + 1, COLS_PER_DAY):
            v = ws.cell(row=ROW_DATES, column=col).value
            if isinstance(v, datetime):
                dates.append(v.date())
            elif isinstance(v, date):
                dates.append(v)
            else:
                dates.append(None)

        # Fix year if needed (workbook may show 2025 for AY 25-26 blocks after Jan)
        # Block 10 = Mar 12, which should be 2026 in AY 25-26
        if dates and dates[0]:
            block_num_str = tab_name.replace("Block ", "").replace("Deprecated ", "")
            try:
                block_num = int(block_num_str)
            except ValueError:
                block_num = 0

            # AY 25-26: blocks 1-6 are in 2025, blocks 7-13 are in 2025-2026
            # The dates from Excel formulas may have wrong year
            # We'll keep them as-is but note the month/day is correct

        block_data = {
            "tab_name": tab_name,
            "dates": [d.isoformat() if d else None for d in dates],
            "num_days": len([d for d in dates if d]),
            "staff_call": [],
            "resident_call": [],
            "people": [],
        }

        # Staff call row
        for i, d in enumerate(dates):
            col = COL_SCHEDULE_START + i * COLS_PER_DAY
            v = ws.cell(row=ROW_STAFF_CALL, column=col).value
            if v and v != NBSP:
                block_data["staff_call"].append({
                    "date": d.isoformat() if d else None,
                    "day_index": i,
                    "staff": str(v).strip(),
                })

        # Resident call row
        for i, d in enumerate(dates):
            col = COL_SCHEDULE_START + i * COLS_PER_DAY
            v = ws.cell(row=ROW_RES_CALL, column=col).value
            if v and v != NBSP:
                block_data["resident_call"].append({
                    "date": d.isoformat() if d else None,
                    "day_index": i,
                    "note": str(v).strip(),
                })

        # Extract people (residents + faculty)
        for row_start, row_end, person_type in [
            (ROW_RESIDENTS_START, ROW_RESIDENTS_END, "resident"),
            (ROW_FACULTY_START, ROW_FACULTY_END, "faculty"),
        ]:
            for row in range(row_start, row_end + 1):
                name_raw = ws.cell(row=row, column=COL_NAME).value
                if not name_raw or name_raw == NBSP or not str(name_raw).strip():
                    continue

                name = str(name_raw).strip()
                # Skip if it looks like a schedule code leaked into name col
                if len(name) <= 4 and "," not in name and name.upper() == name:
                    continue

                rot1_raw = ws.cell(row=row, column=COL_ROTATION1).value
                rot2_raw = ws.cell(row=row, column=COL_ROTATION2).value
                template_raw = ws.cell(row=row, column=COL_TEMPLATE).value
                role_raw = ws.cell(row=row, column=COL_ROLE).value

                rot1 = str(rot1_raw).strip() if rot1_raw and rot1_raw != NBSP else None
                rot2 = str(rot2_raw).strip() if rot2_raw and rot2_raw != NBSP else None
                template = str(template_raw).strip() if template_raw and template_raw != NBSP else None
                role = str(role_raw).strip() if role_raw and role_raw != NBSP else None

                person = {
                    "name": name,
                    "row": row,
                    "type": person_type,
                    "rotation1": rot1,
                    "rotation2": rot2,
                    "template": template,
                    "role": role,
                    "days": [],
                }

                for i, d in enumerate(dates):
                    am_col = COL_SCHEDULE_START + i * COLS_PER_DAY
                    pm_col = am_col + 1

                    am_raw = ws.cell(row=row, column=am_col).value
                    pm_raw = ws.cell(row=row, column=pm_col).value

                    am = str(am_raw).strip() if am_raw and am_raw != NBSP else None
                    pm = str(pm_raw).strip() if pm_raw and pm_raw != NBSP else None

                    person["days"].append({
                        "date": d.isoformat() if d else None,
                        "day_index": i,
                        "am": am,
                        "pm": pm,
                    })

                person["filled_cells"] = sum(
                    1 for day in person["days"]
                    if day["am"] or day["pm"]
                )
                block_data["people"].append(person)

        result["blocks"].append(block_data)

    wb.close()

    # Summary
    total_people = sum(len(b["people"]) for b in result["blocks"])
    total_cells = sum(
        p["filled_cells"]
        for b in result["blocks"]
        for p in b["people"]
    )
    result["summary"] = {
        "blocks_extracted": len(result["blocks"]),
        "block_names": [b["tab_name"] for b in result["blocks"]],
        "total_people": total_people,
        "total_filled_cells": total_cells,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract ground truth from handjam workbook")
    parser.add_argument("--workbook", required=True, help="Path to handjam .xlsx")
    parser.add_argument("--output", default="/tmp/ground_truth.json", help="Output JSON path")
    args = parser.parse_args()

    wb_path = Path(args.workbook).expanduser()
    if not wb_path.exists():
        print(f"ERROR: {wb_path} not found")
        return

    print(f"Reading {wb_path.name}...")
    data = extract_workbook(wb_path)

    out = Path(args.output)
    out.write_text(json.dumps(data, indent=2))
    print(f"\nWrote {out} ({out.stat().st_size:,} bytes)")
    print(f"\nSummary:")
    for k, v in data["summary"].items():
        print(f"  {k}: {v}")

    # Quick code frequency table
    code_counts: dict[str, int] = {}
    for block in data["blocks"]:
        for person in block["people"]:
            for day in person["days"]:
                for half in ("am", "pm"):
                    code = day.get(half)
                    if code:
                        code_counts[code] = code_counts.get(code, 0) + 1

    print(f"\n  Unique display codes: {len(code_counts)}")
    print(f"  Top 20:")
    for code, cnt in sorted(code_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {code:12s} {cnt:5d}")


if __name__ == "__main__":
    main()
