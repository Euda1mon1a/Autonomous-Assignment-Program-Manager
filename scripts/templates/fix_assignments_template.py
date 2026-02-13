"""Fix assignments table and backfill HDA linkage template.

After loading HDAs from Excel, the assignments table may contain stale records
from a previous solver run. This script:
1. Deletes stale assignments for a block
2. Rebuilds from block_assignments (correct resident → rotation mappings)
3. Backfills block_assignment_id on HDAs for provenance

Usage:
  1. Copy to /tmp/fix_blockNN_assignments.py
  2. Fill in BLOCK_CONFIG
  3. Run: backend/.venv/bin/python /tmp/fix_blockNN_assignments.py

Prerequisite:
  - Database backup
  - block_assignments table populated (from solver or manual entry)

Reference implementation: scripts/data/block11_import/ (local only, gitignored)
"""

import uuid
from datetime import date, datetime

import psycopg2

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

BLOCK_CONFIG = {
    "block_number": 0,
    "academic_year": 2025,
    "start_date": date(2026, 1, 1),
    "end_date": date(2026, 1, 28),
}


def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    block_num = BLOCK_CONFIG["block_number"]
    start = BLOCK_CONFIG["start_date"]
    end = BLOCK_CONFIG["end_date"]
    ay = BLOCK_CONFIG["academic_year"]

    # Step 1: Get correct resident → rotation mappings from block_assignments
    # Include secondary_rotation_template_id for split-block residents
    cur.execute(
        """SELECT id, resident_id, rotation_template_id,
                  secondary_rotation_template_id
        FROM block_assignments
        WHERE block_number = %s AND academic_year = %s""",
        (block_num, ay),
    )
    block_assignments = cur.fetchall()
    print(f"Found {len(block_assignments)} block_assignments for Block {block_num}")

    if not block_assignments:
        print("ERROR: No block_assignments found. Populate those first.")
        return

    # Step 2: Get block slot IDs for the date range
    cur.execute(
        "SELECT id, date FROM blocks WHERE date >= %s AND date <= %s ORDER BY date",
        (start, end),
    )
    block_slots = cur.fetchall()
    print(f"Found {len(block_slots)} block slots")

    # Step 3: Delete stale assignments
    slot_ids = [s[0] for s in block_slots]
    cur.execute(
        "DELETE FROM assignments WHERE block_id = ANY(%s::uuid[])",
        ([str(s) for s in slot_ids],),
    )
    print(f"Deleted {cur.rowcount} stale assignments")

    # Step 4: Create correct assignments
    # For split-block residents, use secondary rotation after BLOCK_HALF_DAY (day 14)
    block_half_day = 14
    created = 0
    for ba_id, resident_id, rotation_id, secondary_rotation_id in block_assignments:
        for slot_id, slot_date in block_slots:
            day_in_block = (slot_date - start).days + 1
            effective_rotation = rotation_id
            if secondary_rotation_id and day_in_block > block_half_day:
                effective_rotation = secondary_rotation_id
            cur.execute(
                """INSERT INTO assignments
                (id, block_id, person_id, rotation_template_id, role, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
                (str(uuid.uuid4()), slot_id, resident_id, effective_rotation, "primary"),
            )
            created += 1
    print(f"Created {created} assignments")

    # Step 5: Backfill block_assignment_id on HDAs
    ba_lookup = {str(resident_id): str(ba_id) for ba_id, resident_id, _ in block_assignments}
    updated = 0
    for resident_id_str, ba_id_str in ba_lookup.items():
        cur.execute(
            """UPDATE half_day_assignments
            SET block_assignment_id = %s
            WHERE person_id = %s AND date >= %s AND date <= %s""",
            (ba_id_str, resident_id_str, start, end),
        )
        updated += cur.rowcount
    print(f"Backfilled block_assignment_id on {updated} HDAs")

    conn.commit()
    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
