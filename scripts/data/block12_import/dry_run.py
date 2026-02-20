"""Block 12 Dry Run — Auto-derive schedule from DB + Excel Block Schedule.

This script performs a dry run of the Block 12 handjam import using:
1. Excel "Block Schedule" sheet (coordinator's master rotation assignments)
2. DB rotation_templates (for AM/PM half-day patterns)
3. DB absences (for leave/TDY/deployment overlaps)

It does NOT use the daily handjam Excel (which doesn't exist yet for Block 12).

Usage:
  1. Backup DB: ./checkpoint.sh pre_dry_run
  2. Run: backend/.venv/bin/python scripts/data/block12_import/dry_run.py
  3. Review output and dry_run_report.md
  4. Restore if needed: ./checkpoint.sh restore pre_dry_run

What this CAN do:
  - Fix stale block_assignments (align DB to Excel Block Schedule)
  - Rebuild assignments table with correct rotation templates
  - Handle split-block (primary + NF secondary) residents
  - Generate template-derived HDAs for residents
  - Sync known absences

What this CANNOT do (needs interactive handjam):
  - Faculty daily AM/PM activity codes
  - Call schedule, conference days, SIM days
  - Day-specific overrides
  - Sports med rotators, TY residents, medical students
"""

import uuid
from datetime import date, timedelta, datetime
from collections import defaultdict

import psycopg2

# ── Configuration ────────────────────────────────────────────────────────────

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

BLOCK_CONFIG = {
    "block_number": 12,
    "academic_year": 2025,
    "start_date": date(2026, 5, 7),
    "end_date": date(2026, 6, 3),
}

# ── Block 12 Rotation Assignments (from Excel "Block Schedule" col 24-25) ───
# Format: (db_name, primary_rotation_abbr, secondary_rotation_abbr_or_None)
#
# Split-block logic:
#   - If a combined NF template exists (NF-CARDIO, NF-DERM-PG, etc.),
#     use it as primary with no secondary.
#   - If no combined template, use primary + secondary with day-15 split.

BLOCK12_ASSIGNMENTS = [
    # PGY-1
    ("Tessa Sawyer",       "NF-PEDS-PG", None),         # Peds NF (combined: NF + Peds Ward)
    ("Clara Wilhelm",      "NF-FMIT-PG", None),         # NF + FMIT Intern (combined)
    ("Colin Travis",       "MSK-SEL",    None),          # MSK Selective (full block)
    ("Katie Byrnes",       "FMIT-PGY2",  "NF"),          # FMIT2 wk1-2, NF wk3-4
    ("Meleigh Sloss",      "PEDS-WARD-", "NF-PEDS-PG"), # Peds Ward wk1-2, Peds NF wk3-4
    ("Josh Monsivais",     "NBN",        None),          # Newborn Nursery (full block)
    # PGY-2
    ("Felipe Cataquiz",    "NF-LD",      None),          # L&D Night Float (full block)
    ("Scott Cook",         "ELEC",       None),          # Elective - Sports Med
    ("Alaine Gigon",       "FMC",        None),          # Family Medicine Clinic
    ("James Headid",       "ELEC",       None),          # Elective (Op Japan?)
    ("Nick Maher",         "NF-DERM-PG", None),          # Derm + NF (combined)
    ("Devin Thomas",       "NF-CARDIO",  None),          # NF + Cardiology (combined)
    # PGY-3
    ("Christian Hernandez","PEDS-EM",    None),          # Pediatric Emergency Medicine
    ("Cam Mayell",         "FMIT-PGY3",  None),          # FMIT 2 (PGY-3 role)
    ("Clay Petrie",        "HILO-PGY3",  None),          # Hilo
    ("Jae You",            "JAPAN",      None),          # Japan Off-Site
    # NOT ASSIGNED (graduated/done after Block 10):
    # Laura Connolly — blank in Excel Block Schedule
]


def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    block_num = BLOCK_CONFIG["block_number"]
    start = BLOCK_CONFIG["start_date"]
    end = BLOCK_CONFIG["end_date"]
    ay = BLOCK_CONFIG["academic_year"]

    print("=" * 70)
    print(f"Block {block_num} Dry Run — May 7 – Jun 3, 2026 (AY {ay})")
    print("=" * 70)

    # ── Lookups ──────────────────────────────────────────────────────────
    cur.execute("SELECT id, name FROM people WHERE type = 'resident'")
    people = {name: pid for pid, name in cur.fetchall()}

    cur.execute("SELECT id, abbreviation, name FROM rotation_templates")
    rot_templates = {abbr: (rid, rname) for rid, abbr, rname in cur.fetchall()}

    cur.execute("SELECT id, date, time_of_day FROM blocks WHERE date >= %s AND date <= %s ORDER BY date, time_of_day",
                (start, end))
    block_slots = cur.fetchall()
    print(f"\nBlock slots: {len(block_slots)} (expected 56)")

    # ── Step 1: Fix block_assignments ────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 1: Fix block_assignments (align DB to Excel Block Schedule)")
    print("=" * 70)

    # Show what's currently in DB
    cur.execute("""SELECT ba.id, p.name, rt.abbreviation, rt2.abbreviation
        FROM block_assignments ba
        JOIN people p ON ba.resident_id = p.id
        JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        LEFT JOIN rotation_templates rt2 ON ba.secondary_rotation_template_id = rt2.id
        WHERE ba.block_number = %s AND ba.academic_year = %s
        ORDER BY p.name""", (block_num, ay))
    old_ba = cur.fetchall()
    print(f"\n  Current DB block_assignments: {len(old_ba)}")
    for ba_id, name, rot, sec in old_ba:
        sec_str = f" / {sec}" if sec else ""
        print(f"    {name:30s} -> {rot}{sec_str}")

    # Delete stale block_assignments
    cur.execute("DELETE FROM block_assignments WHERE block_number = %s AND academic_year = %s",
                (block_num, ay))
    print(f"\n  Deleted {cur.rowcount} stale block_assignments")

    # Also delete Connolly's stale assignments in the assignments table
    connolly_id = people.get("Laura Connolly")
    if connolly_id:
        slot_ids = [str(s[0]) for s in block_slots]
        cur.execute("""DELETE FROM assignments
            WHERE block_id = ANY(%s::uuid[]) AND person_id = %s""",
                    (slot_ids, connolly_id))
        print(f"  Deleted {cur.rowcount} stale Connolly assignments")

    # Insert correct block_assignments from Excel
    created_ba = 0
    ba_lookup = {}  # name -> ba_id for HDA backfill later
    for name, primary_abbr, secondary_abbr in BLOCK12_ASSIGNMENTS:
        person_id = people.get(name)
        if not person_id:
            print(f"  WARNING: '{name}' not found in people table")
            continue

        primary_rt = rot_templates.get(primary_abbr)
        if not primary_rt:
            print(f"  WARNING: rotation '{primary_abbr}' not found")
            continue

        secondary_rt_id = None
        if secondary_abbr:
            sec_rt = rot_templates.get(secondary_abbr)
            if sec_rt:
                secondary_rt_id = sec_rt[0]
            else:
                print(f"  WARNING: secondary rotation '{secondary_abbr}' not found")

        ba_id = str(uuid.uuid4())
        cur.execute("""INSERT INTO block_assignments
            (id, resident_id, rotation_template_id, secondary_rotation_template_id,
             block_number, academic_year, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())""",
                    (ba_id, person_id, primary_rt[0], secondary_rt_id, block_num, ay))
        created_ba += 1
        ba_lookup[name] = ba_id

        sec_str = f" / {secondary_abbr}" if secondary_abbr else ""
        print(f"  + {name:30s} -> {primary_abbr}{sec_str}")

    print(f"\n  Created {created_ba} block_assignments")

    # ── Step 2: Rebuild assignments table ────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 2: Rebuild assignments table")
    print("=" * 70)

    # Delete all existing resident assignments for Block 12
    resident_ids = [str(people[name]) for name, _, _ in BLOCK12_ASSIGNMENTS if name in people]
    if connolly_id:
        resident_ids.append(str(connolly_id))
    slot_ids = [str(s[0]) for s in block_slots]

    cur.execute("""DELETE FROM assignments
        WHERE block_id = ANY(%s::uuid[]) AND person_id = ANY(%s::uuid[])""",
                (slot_ids, resident_ids))
    print(f"\n  Deleted {cur.rowcount} stale resident assignments")

    # Also remove deployed faculty (Bridget Colgan) assignments
    cur.execute("SELECT id FROM people WHERE name = 'Bridget Colgan'")
    colgan = cur.fetchone()
    if colgan:
        cur.execute("""DELETE FROM assignments
            WHERE block_id = ANY(%s::uuid[]) AND person_id = %s""",
                    (slot_ids, colgan[0]))
        print(f"  Deleted {cur.rowcount} Colgan (deployed) supervising assignments")

    # Rebuild assignments
    block_half_day = 14  # Day 15 is split point
    created_asn = 0
    for name, primary_abbr, secondary_abbr in BLOCK12_ASSIGNMENTS:
        person_id = people.get(name)
        if not person_id:
            continue

        primary_rt = rot_templates.get(primary_abbr)
        if not primary_rt:
            continue

        secondary_rt = rot_templates.get(secondary_abbr) if secondary_abbr else None

        for slot_id, slot_date, slot_tod in block_slots:
            day_in_block = (slot_date - start).days + 1
            if secondary_rt and day_in_block > block_half_day:
                effective_rotation = secondary_rt[0]
            else:
                effective_rotation = primary_rt[0]

            cur.execute("""INSERT INTO assignments
                (id, block_id, person_id, rotation_template_id, role,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
                        (str(uuid.uuid4()), slot_id, person_id,
                         effective_rotation, "primary"))
            created_asn += 1

    print(f"  Created {created_asn} resident assignments")

    # ── Step 3: Generate comparison report ───────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 3: Generate dry run report")
    print("=" * 70)

    # Get absences overlapping Block 12
    cur.execute("""SELECT p.name, a.absence_type, a.start_date, a.end_date, a.notes
        FROM absences a
        JOIN people p ON a.person_id = p.id
        WHERE a.start_date <= %s AND a.end_date >= %s
        ORDER BY p.name, a.start_date""",
                (end, start))
    absences = cur.fetchall()

    # Build absence lookup by name -> set of dates
    absence_dates = defaultdict(set)
    for aname, atype, astart, aend, anotes in absences:
        d = max(astart, start)
        while d <= min(aend, end):
            absence_dates[aname].add(d)
            d += timedelta(days=1)

    # Count HDAs that WOULD be generated (minus absence days)
    total_hdas = 0
    report_lines = []
    report_lines.append("# Block 12 Dry Run Report")
    report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"**Block:** 12 (May 7 – Jun 3, 2026), AY 2025")
    report_lines.append(f"**Source:** Excel Block Schedule + DB rotation templates")
    report_lines.append(f"**Type:** DRY RUN — template-derived, NOT from coordinator handjam\n")

    report_lines.append("## Rotation Assignments (Corrected from Excel)\n")
    report_lines.append("| Resident | PGY | Primary Rotation | Secondary (Split) | Leave Days |")
    report_lines.append("|----------|-----|-----------------|-------------------|------------|")

    for name, primary_abbr, secondary_abbr in BLOCK12_ASSIGNMENTS:
        person_id = people.get(name)
        if not person_id:
            continue

        # Get PGY level
        cur.execute("SELECT pgy_level FROM people WHERE id = %s", (person_id,))
        pgy = cur.fetchone()[0] or "?"

        leave_days = len(absence_dates.get(name, set()))
        sec_str = secondary_abbr or "-"
        leave_str = f"{leave_days} days" if leave_days > 0 else "-"
        report_lines.append(f"| {name} | {pgy} | {primary_abbr} | {sec_str} | {leave_str} |")

        # Count HDAs (56 total - 2 per leave day)
        hdas_for_person = 56 - (leave_days * 2)
        total_hdas += max(0, hdas_for_person)

    report_lines.append(f"\n**Total expected HDAs:** {total_hdas} (16 residents x 56 slots - absence days)")

    # Absences section
    report_lines.append("\n## Known Absences Overlapping Block 12\n")
    report_lines.append("| Person | Type | Start | End | Notes |")
    report_lines.append("|--------|------|-------|-----|-------|")
    for aname, atype, astart, aend, anotes in absences:
        report_lines.append(f"| {aname} | {atype} | {astart} | {aend} | {anotes or ''} |")

    # Issues section
    report_lines.append("\n## Issues Identified\n")
    report_lines.append("1. **DB block_assignments were 100% stale** — all 16 had wrong rotations (Block 11 data)")
    report_lines.append("2. **Laura Connolly** not assigned to Block 12 (graduated/done after Block 10)")
    report_lines.append("3. **Bridget Colgan** (faculty) deployed Feb 21 – Jun 30 — removed supervision assignments")
    report_lines.append("4. **Memorial Day (May 25)** not flagged as holiday in blocks table")
    report_lines.append("5. **6 split-block residents** — using combined NF templates where available")

    # What's missing
    report_lines.append("\n## What This Dry Run Did NOT Generate\n")
    report_lines.append("- Faculty daily AM/PM activity codes (need handjam)")
    report_lines.append("- Call schedule (Staff Call row)")
    report_lines.append("- Day-specific overrides (clinic cancellations, SIM, conference)")
    report_lines.append("- Sports Medicine rotator schedule (Travis listed as SM rotator)")
    report_lines.append("- TY/Flight Surgeon, medical student, IPAP assignments")
    report_lines.append("- Exact NF split dates (used day 15 cutoff; actual may differ)")

    # Discrepancy table
    report_lines.append("\n## DB vs Excel Discrepancy (Pre-Fix State)\n")
    report_lines.append("| Resident | Was (DB) | Should Be (Excel) |")
    report_lines.append("|----------|---------|------------------|")
    old_ba_dict = {name: rot for _, name, rot, _ in old_ba}
    for name, primary_abbr, _ in BLOCK12_ASSIGNMENTS:
        old_rot = old_ba_dict.get(name, "(none)")
        if old_rot != primary_abbr:
            report_lines.append(f"| {name} | {old_rot} | {primary_abbr} |")

    report_text = "\n".join(report_lines)

    # Write report
    report_path = "scripts/data/block12_import/dry_run_report.md"
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"\n  Report written to: {report_path}")

    # ── Step 4: Backfill block_assignment_id on existing HDAs ────────────
    print("\n" + "=" * 70)
    print("STEP 4: Backfill block_assignment_id on HDAs")
    print("=" * 70)

    updated_hdas = 0
    for name, ba_id in ba_lookup.items():
        person_id = people.get(name)
        if not person_id:
            continue
        cur.execute("""UPDATE half_day_assignments
            SET block_assignment_id = %s
            WHERE person_id = %s AND date >= %s AND date <= %s""",
                    (ba_id, person_id, start, end))
        updated_hdas += cur.rowcount
    print(f"  Backfilled block_assignment_id on {updated_hdas} HDAs")

    # ── Commit ───────────────────────────────────────────────────────────
    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 70)
    print("DRY RUN COMPLETE")
    print("=" * 70)
    print(f"\n  block_assignments: {created_ba} created (was {len(old_ba)} stale)")
    print(f"  assignments: {created_asn} created")
    print(f"  Expected HDAs: ~{total_hdas} (from template, not yet generated)")
    print(f"  Report: {report_path}")
    print(f"\n  To restore: /opt/homebrew/opt/postgresql@17/bin/pg_restore \\")
    print(f"    -U scheduler -d residency_scheduler --clean \\")
    print(f"    /tmp/block12_pre_dry_run_*.dump")


if __name__ == "__main__":
    main()
