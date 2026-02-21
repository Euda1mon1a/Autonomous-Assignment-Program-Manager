#!/usr/bin/env python3
"""Export block HDA data as JSON for schedule-vision extraction.

Produces blockN_data.json files compatible with extract.py --db-dir.

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/export_blocks_json.py --output-dir /tmp/db_exports
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="/tmp/db_exports")
    parser.add_argument("--db-url", default="postgresql://scheduler@localhost:5432/residency_scheduler")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()

    # Get academic blocks
    cur.execute("""
        SELECT block_number, start_date, end_date
        FROM academic_blocks
        WHERE academic_year = 2025
        ORDER BY block_number
    """)
    blocks = cur.fetchall()
    print(f"Found {len(blocks)} academic blocks")

    for block_num, start_date, end_date in blocks:
        # Get all HDAs for this block
        cur.execute("""
            SELECT h.person_id, p.name, p.type,
                   p.pgy_level, h.date, h.time_of_day, a.code as activity_code,
                   h.source
            FROM half_day_assignments h
            JOIN people p ON h.person_id = p.id
            JOIN activities a ON h.activity_id = a.id
            WHERE h.date >= %s AND h.date <= %s
              AND h.source IN ('preload', 'manual')
            ORDER BY p.name, h.date, h.time_of_day
        """, (start_date, end_date))

        rows = cur.fetchall()
        if not rows:
            continue

        # Group by person_id (stable UUID) to avoid merging distinct people
        # who happen to share the same normalized name.
        people = defaultdict(lambda: {"days": []})
        for person_id, name, ptype, pgy, date, tod, code, source in rows:
            # Convert "First Last" to "Last, First" for extract.py compatibility
            parts = name.strip().split()
            if len(parts) >= 2:
                display_name = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                display_name = name
            key = str(person_id)
            p = people[key]
            p["name"] = display_name
            p["person_type"] = ptype
            p["pgy_level"] = pgy
            p["days"].append({
                "date": date.isoformat(),
                "am": code if tod == "AM" else None,
                "pm": code if tod == "PM" else None,
            })

        # Merge AM/PM for same date
        for pname, pdata in people.items():
            merged = {}
            for d in pdata["days"]:
                date_key = d["date"]
                if date_key not in merged:
                    merged[date_key] = {"date": date_key, "am": None, "pm": None}
                if d["am"]:
                    merged[date_key]["am"] = d["am"]
                if d["pm"]:
                    merged[date_key]["pm"] = d["pm"]
            pdata["days"] = sorted(merged.values(), key=lambda x: x["date"])

        # Split into residents and faculty
        residents = []
        faculty = []
        for pname, pdata in sorted(people.items()):
            entry = {
                "name": pdata["name"],
                "pgy": pdata.get("pgy_level"),
                "days": pdata["days"],
            }
            if pdata.get("person_type") == "faculty":
                faculty.append(entry)
            else:
                residents.append(entry)

        block_data = {
            "block_number": block_num,
            "block_start": start_date.isoformat(),
            "block_end": end_date.isoformat(),
            "residents": residents,
            "faculty": faculty,
        }

        out_path = out_dir / f"block{block_num}_data.json"
        out_path.write_text(json.dumps(block_data, indent=2))
        total_cells = sum(
            sum(1 for d in p["days"] for h in ["am", "pm"] if d.get(h))
            for p in residents + faculty
        )
        print(f"  Block {block_num}: {len(residents)} residents, {len(faculty)} faculty, {total_cells} cells → {out_path.name}")

    conn.close()
    print(f"\nDone. Exports in {out_dir}/")


if __name__ == "__main__":
    main()
