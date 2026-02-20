"""Fix Block 12 assignments table and backfill HDA linkage.

After loading HDAs from Excel, the assignments table may contain stale records
from a previous solver run. This script:
1. Deletes stale resident assignments for Block 12
2. Rebuilds from block_assignments (correct resident -> rotation mappings)
3. Handles split-block residents (secondary_rotation_template_id)
4. Backfills block_assignment_id on HDAs for provenance

Usage:
  1. Backup DB: ./checkpoint.sh pre_assignments_fix
  2. Run: backend/.venv/bin/python scripts/data/block12_import/fix_block12_assignments.py

Block 11 gotchas addressed:
  #2: Split-block residents — uses secondary_rotation_template_id
  #8: 4-column unpack — explicit column naming in SELECT
"""

import uuid
from datetime import date, datetime

import psycopg2

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

BLOCK_CONFIG = {
    "block_number": 12,
    "academic_year": 2025,
    "start_date": date(2026, 5, 7),
    "end_date": date(2026, 6, 3),
}


def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    block_num = BLOCK_CONFIG["block_number"]
    start = BLOCK_CONFIG["start_date"]
    end = BLOCK_CONFIG["end_date"]
    ay = BLOCK_CONFIG["academic_year"]

    print(f"Block {block_num} AY{ay}: {start} to {end}")
    print("=" * 60)

    # Step 1: Get correct resident -> rotation mappings
    # Explicit 4-column SELECT (Block 11 gotcha #8: always name columns)
    cur.execute(
        """SELECT id, resident_id, rotation_template_id,
                  secondary_rotation_template_id
        FROM block_assignments
        WHERE block_number = %s AND academic_year = %s""",
        (block_num, ay),
    )
    block_assignments = cur.fetchall()
    print(f"\nStep 1: Found {len(block_assignments)} block_assignments")

    if not block_assignments:
        print("ERROR: No block_assignments found. Populate those first.")
        conn.close()
        return

    # Show mappings
    for ba_id, resident_id, rotation_id, secondary_id in block_assignments:
        cur.execute("SELECT name FROM people WHERE id = %s", (resident_id,))
        name = cur.fetchone()[0] if cur.rowcount else "(unknown)"
        cur.execute(
            "SELECT name FROM rotation_templates WHERE id = %s", (rotation_id,)
        )
        rot_name = cur.fetchone()[0] if cur.rowcount else "(none)"
        split = ""
        if secondary_id:
            cur.execute(
                "SELECT name FROM rotation_templates WHERE id = %s",
                (secondary_id,),
            )
            sec_name = cur.fetchone()[0] if cur.rowcount else "(none)"
            split = f" → {sec_name} (day 15+)"
        print(f"  {name:25s} → {rot_name}{split}")

    # Step 2: Get block slot IDs
    cur.execute(
        "SELECT id, date FROM blocks WHERE date >= %s AND date <= %s ORDER BY date",
        (start, end),
    )
    block_slots = cur.fetchall()
    print(f"\nStep 2: Found {len(block_slots)} block slots")

    # Step 3: Delete stale resident assignments
    slot_ids = [str(s[0]) for s in block_slots]
    resident_ids = [str(r) for _, r, _, _ in block_assignments]
    cur.execute(
        """DELETE FROM assignments
        WHERE block_id = ANY(%s::uuid[])
          AND person_id = ANY(%s::uuid[])""",
        (slot_ids, resident_ids),
    )
    print(f"\nStep 3: Deleted {cur.rowcount} stale resident assignments")

    # Step 4: Create correct assignments
    # Split-block: use secondary rotation after day 14 (Block 11 gotcha #2)
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
                (id, block_id, person_id, rotation_template_id, role,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
                (
                    str(uuid.uuid4()),
                    slot_id,
                    resident_id,
                    effective_rotation,
                    "primary",
                ),
            )
            created += 1
    print(f"\nStep 4: Created {created} assignments")

    # Step 5: Backfill block_assignment_id on HDAs
    ba_lookup = {
        str(resident_id): str(ba_id)
        for ba_id, resident_id, _, _ in block_assignments
    }
    updated = 0
    for resident_id_str, ba_id_str in ba_lookup.items():
        cur.execute(
            """UPDATE half_day_assignments
            SET block_assignment_id = %s
            WHERE person_id = %s AND date >= %s AND date <= %s""",
            (ba_id_str, resident_id_str, start, end),
        )
        updated += cur.rowcount
    print(f"\nStep 5: Backfilled block_assignment_id on {updated} HDAs")

    conn.commit()
    cur.close()
    conn.close()
    print("\n" + "=" * 60)
    print("Done. Update BLOCK12_SCHEDULE_LOAD.md with results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
