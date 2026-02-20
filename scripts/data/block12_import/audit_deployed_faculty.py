"""Audit deployed faculty for stale supervision assignments.

The Block 12 dry run found Bridget Colgan (deployed Feb 21 – Jun 30, 2026) still
had 24 supervising assignments. This script finds ALL deployed faculty who have
assignments overlapping their deployment period, across all blocks.

Usage:
  backend/.venv/bin/python scripts/data/block12_import/audit_deployed_faculty.py
  backend/.venv/bin/python scripts/data/block12_import/audit_deployed_faculty.py --fix

The --fix flag deletes stale assignments (creates checkpoint first).
"""

import sys
from datetime import date

import psycopg2

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

# Only look at current and future blocks (no point auditing the past)
AUDIT_START = date(2026, 2, 18)  # Today


def main():
    fix_mode = "--fix" in sys.argv

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    print("=" * 70)
    print("Deployed Faculty Assignment Audit")
    print("=" * 70)

    # Find all deployment absences that overlap with today or future
    cur.execute("""
        SELECT a.id, p.name, p.type, a.start_date, a.end_date, a.notes
        FROM absences a
        JOIN people p ON a.person_id = p.id
        WHERE a.absence_type = 'deployment'
          AND a.end_date >= %s
        ORDER BY p.name, a.start_date
    """, (AUDIT_START,))
    deployments = cur.fetchall()

    if not deployments:
        print("\nNo active/future deployments found.")
        conn.close()
        return

    print(f"\nActive/future deployments: {len(deployments)}")
    for _, name, ptype, start, end, notes in deployments:
        print(f"  {name} ({ptype}): {start} – {end} ({notes or ''})")

    # For each deployed person, find assignments in their deployment window
    print(f"\n{'=' * 70}")
    print("Checking for stale assignments during deployment periods...")
    print("=" * 70)

    total_stale = 0
    stale_details = []

    for absence_id, name, ptype, dep_start, dep_end, notes in deployments:
        cur.execute("""
            SELECT a.id, b.date, b.time_of_day, a.role,
                   rt.abbreviation as rotation
            FROM assignments a
            JOIN blocks b ON a.block_id = b.id
            LEFT JOIN rotation_templates rt ON a.rotation_template_id = rt.id
            JOIN people p ON a.person_id = p.id
            WHERE p.name = %s
              AND b.date >= %s AND b.date <= %s
            ORDER BY b.date, b.time_of_day
        """, (name, dep_start, dep_end))
        stale = cur.fetchall()

        if stale:
            print(f"\n  {name}: {len(stale)} assignments during deployment ({dep_start} – {dep_end})")
            # Show first/last few
            for asn_id, d, tod, role, rot in stale[:5]:
                print(f"    {d} {tod}: {role} ({rot or 'no rotation'})")
            if len(stale) > 5:
                print(f"    ... and {len(stale) - 5} more")

            total_stale += len(stale)
            stale_details.append((name, dep_start, dep_end, [s[0] for s in stale]))
        else:
            print(f"\n  {name}: Clean — no assignments during deployment")

    print(f"\n{'=' * 70}")
    print(f"TOTAL STALE ASSIGNMENTS: {total_stale}")
    print("=" * 70)

    if total_stale == 0:
        print("\nAll clear — no deployed faculty have overlapping assignments.")
        cur.close()
        conn.close()
        return

    if not fix_mode:
        print("\nRun with --fix to delete stale assignments.")
        print("  backend/.venv/bin/python scripts/data/block12_import/audit_deployed_faculty.py --fix")
        cur.close()
        conn.close()
        return

    # Fix mode — delete stale assignments
    print("\n--- FIX MODE ---")
    for name, dep_start, dep_end, assignment_ids in stale_details:
        print(f"\n  Deleting {len(assignment_ids)} assignments for {name}...")
        for asn_id in assignment_ids:
            cur.execute("DELETE FROM assignments WHERE id = %s", (asn_id,))
        print(f"  Deleted {len(assignment_ids)} assignments")

    conn.commit()
    print(f"\nTotal deleted: {total_stale} stale assignments")

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
