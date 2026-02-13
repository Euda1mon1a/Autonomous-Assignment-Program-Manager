"""Extract a block schedule from the database to CSV files.

Produces two CSVs:
  1. Call schedule: faculty call assignments by date
  2. Schedule grid: full HDA grid (person × date × time_of_day)

Usage:
  1. Copy to /tmp/extract_blockNN.py
  2. Fill in BLOCK_CONFIG
  3. Run: backend/.venv/bin/python /tmp/extract_blockNN.py

Output files are written to OUTPUT_DIR (default: /tmp/).

Reference implementation: scripts/data/block11_import/ (local only, gitignored)
"""

import csv
import os
import sys
from collections import defaultdict

# ── Bootstrap ────────────────────────────────────────────────────────────────
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
os.chdir(BACKEND_DIR)
sys.path.insert(0, ".")

from dotenv import dotenv_values

for env_file in ["../.env", ".env"]:
    if os.path.exists(env_file):
        for key, value in dotenv_values(env_file).items():
            if value is not None:
                os.environ[key] = value

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person

# ── Configuration ────────────────────────────────────────────────────────────

BLOCK_CONFIG = {
    "block_number": 0,  # e.g., 12
    "academic_year": 2025,
    "start_date": date(2026, 1, 1),
    "end_date": date(2026, 1, 28),
}

OUTPUT_DIR = "/tmp"

# Activity codes that count as "call" assignments
CALL_CODES = {"C", "SC", "BC", "CALL", "SUNDAY_CALL", "WEEKDAY_CALL"}


# ── Extraction ───────────────────────────────────────────────────────────────


def main():
    block_num = BLOCK_CONFIG["block_number"]
    start = BLOCK_CONFIG["start_date"]
    end = BLOCK_CONFIG["end_date"]

    if block_num == 0:
        print("ERROR: Set block_number in BLOCK_CONFIG before running.")
        return

    db = SessionLocal()

    try:
        # Load all HDAs for the date range with person and activity
        stmt = (
            select(HalfDayAssignment)
            .options(
                joinedload(HalfDayAssignment.person),
                joinedload(HalfDayAssignment.activity),
            )
            .where(
                HalfDayAssignment.date >= start,
                HalfDayAssignment.date <= end,
            )
            .order_by(HalfDayAssignment.date, HalfDayAssignment.time_of_day)
        )
        hdas = list(db.execute(stmt).scalars().unique().all())
        print(f"Loaded {len(hdas)} HDAs for Block {block_num}")

        # Build date list
        dates = []
        d = start
        while d <= end:
            dates.append(d)
            d += timedelta(days=1)

        # ── Schedule Grid CSV ────────────────────────────────────────────
        grid_path = os.path.join(OUTPUT_DIR, f"block{block_num}_schedule_grid.csv")

        # Group by person
        person_hdas: dict[str, dict[str, str]] = defaultdict(dict)
        person_info: dict[str, tuple[str, str, int | None]] = {}

        for hda in hdas:
            if not hda.person:
                continue
            pid = str(hda.person_id)
            key = f"{hda.date.isoformat()}_{hda.time_of_day}"
            code = hda.activity.code if hda.activity else "?"
            person_hdas[pid][key] = code
            if pid not in person_info:
                person_info[pid] = (
                    hda.person.name or f"ID:{pid[:8]}",
                    hda.person.type,
                    hda.person.pgy_level,
                )

        # Write grid
        slot_headers = []
        for d in dates:
            slot_headers.append(f"{d.isoformat()}_AM")
            slot_headers.append(f"{d.isoformat()}_PM")

        with open(grid_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Type", "PGY"] + slot_headers)
            for pid, info in sorted(person_info.items(), key=lambda x: x[1][0]):
                name, ptype, pgy = info
                row = [name, ptype, pgy or ""]
                for header in slot_headers:
                    row.append(person_hdas[pid].get(header, ""))
                writer.writerow(row)

        print(f"Wrote schedule grid: {grid_path} ({len(person_info)} people)")

        # ── Call Schedule CSV ────────────────────────────────────────────
        call_path = os.path.join(OUTPUT_DIR, f"block{block_num}_call_schedule.csv")

        call_hdas = [
            hda
            for hda in hdas
            if hda.activity and hda.activity.code in CALL_CODES
        ]

        with open(call_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Person", "Type", "Activity"])
            for hda in sorted(call_hdas, key=lambda h: (h.date, h.time_of_day)):
                writer.writerow([
                    hda.date.isoformat(),
                    hda.time_of_day,
                    hda.person.name if hda.person else "?",
                    hda.person.type if hda.person else "?",
                    hda.activity.code,
                ])

        print(f"Wrote call schedule: {call_path} ({len(call_hdas)} entries)")

    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    main()
