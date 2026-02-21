#!/usr/bin/env python3
"""Calibrate rotation_activity_requirements from learned constraints.

Reads learned constraints JSON and applies corrections to the database.
Three modes: --dry-run (report only), --apply-high (high confidence only),
--apply-all (high + medium confidence).

Low-confidence constraints are NEVER auto-applied — they go in needs_review.md.

Usage:
    cd ~/workspace/aapm

    # Dry run first (always!)
    backend/.venv/bin/python scripts/ml/calibrate_constraints.py \
        --learned /tmp/learned_constraints_v2.json \
        --dry-run

    # Apply high-confidence changes only
    backend/.venv/bin/python scripts/ml/calibrate_constraints.py \
        --learned /tmp/learned_constraints_v2.json \
        --apply-high

    # Apply high + medium confidence
    backend/.venv/bin/python scripts/ml/calibrate_constraints.py \
        --learned /tmp/learned_constraints_v2.json \
        --apply-all
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--learned", default="/tmp/learned_constraints_v2.json",
                    help="Path to learned constraints JSON from learn_constraints.py")
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    p.add_argument("--backup-dir", default="/tmp/aapm_backups",
                    help="Directory for pg_dump backups")

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                       help="Report what would change without touching the DB")
    mode.add_argument("--apply-high", action="store_true",
                       help="Apply high-confidence changes only")
    mode.add_argument("--apply-all", action="store_true",
                       help="Apply high + medium confidence changes")

    return p.parse_args()


def backup_table(db_url, backup_dir):
    """Create a pg_dump backup of rotation_activity_requirements."""
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(backup_dir) / f"rar_backup_{timestamp}.sql"

    # Find pg_dump in common locations
    pg_dump = "pg_dump"
    import glob
    pg_dump_candidates = [
        "/opt/homebrew/bin/pg_dump",
        "/opt/homebrew/opt/postgresql@17/bin/pg_dump",
        "/usr/local/bin/pg_dump",
    ] + glob.glob("/opt/homebrew/Cellar/postgresql@*/*/bin/pg_dump")
    for candidate in pg_dump_candidates:
        if Path(candidate).exists():
            pg_dump = candidate
            break

    cmd = [
        pg_dump,
        "--table=rotation_activity_requirements",
        "--data-only",
        "--inserts",
        f"--dbname={db_url}",
        f"--file={backup_path}",
    ]

    print(f"  Backing up rotation_activity_requirements to {backup_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: pg_dump failed: {result.stderr}")
        print("  Continuing anyway (backup is best-effort)...")
        return None

    size = backup_path.stat().st_size
    print(f"  Backup: {backup_path} ({size / 1024:.1f} KB)")
    return str(backup_path)


def fetch_existing_requirements(cur):
    """Fetch all existing rotation_activity_requirements with IDs."""
    cur.execute("""
        SELECT
            rar.id,
            rt.id AS template_id,
            rt.name AS template_name,
            a.id AS activity_id,
            a.code AS activity_code,
            rar.min_halfdays,
            rar.max_halfdays,
            rar.target_halfdays,
            rar.applicable_weeks,
            rar.prefer_full_days,
            rar.priority
        FROM rotation_activity_requirements rar
        JOIN rotation_templates rt ON rar.rotation_template_id = rt.id
        JOIN activities a ON rar.activity_id = a.id
        ORDER BY rt.name, a.code
    """)
    reqs = {}
    for row in cur.fetchall():
        weeks_raw = row[8]  # applicable_weeks (JSON list or None)
        weeks_key = json.dumps(weeks_raw, sort_keys=True) if weeks_raw is not None else None
        key = (row[2], row[4], weeks_key)  # (template_name, activity_code, weeks)
        reqs[key] = {
            "id": str(row[0]),
            "template_id": str(row[1]),
            "template_name": row[2],
            "activity_id": str(row[3]),
            "activity_code": row[4],
            "min_halfdays": row[5],
            "max_halfdays": row[6],
            "target_halfdays": row[7],
            "applicable_weeks": row[8],
            "prefer_full_days": row[9],
            "priority": row[10],
        }
    return reqs


def fetch_template_ids(cur):
    """Fetch template name → id mapping."""
    cur.execute("SELECT id, name FROM rotation_templates WHERE NOT is_archived")
    return {row[1]: str(row[0]) for row in cur.fetchall()}


def fetch_activity_ids(cur):
    """Fetch activity code → id mapping."""
    cur.execute("SELECT id, code FROM activities")
    return {row[1]: str(row[0]) for row in cur.fetchall()}


def compute_applicable_weeks_hash(weeks):
    """Compute the applicable_weeks_hash matching the SQLAlchemy model.

    Uses uuid5(NAMESPACE_DNS, key_string) — same as RotationActivityRequirement.compute_weeks_hash().
    """
    import uuid as _uuid
    if weeks is None:
        return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, "all"))
    weeks_str = ",".join(str(w) for w in sorted(weeks))
    return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, weeks_str))


def plan_changes(learned, existing_reqs, template_ids, activity_ids, apply_tiers):
    """Plan all changes without executing them.

    Returns:
        inserts: list of new requirement dicts to INSERT
        updates: list of (rar_id, changes_dict) to UPDATE
        skips: list of (reason, details) for skipped changes
        review: list of low-confidence items needing coordinator review
    """
    inserts = []
    updates = []
    skips = []
    review = []

    for template_name, tdata in sorted(learned.items()):
        template_id = template_ids.get(template_name)
        if not template_id:
            skips.append(("template_not_found", template_name))
            continue

        template_confidence = tdata.get("confidence", "low")
        applicable_weeks = tdata.get("applicable_weeks")

        for code, lc in sorted(tdata.get("activities", {}).items()):
            activity_id = activity_ids.get(code)
            if not activity_id:
                skips.append(("activity_not_found", f"{template_name}/{code}"))
                continue

            tier = lc.get("confidence", template_confidence)

            # Low confidence → never auto-apply
            if tier == "low":
                review.append({
                    "template_name": template_name,
                    "activity_code": code,
                    "confidence": tier,
                    "learned_min": lc["learned_min"],
                    "learned_max": lc["learned_max"],
                    "learned_target": lc["learned_target"],
                    "reason": "low confidence (n<4), requires coordinator review",
                })
                continue

            # Skip if tier not in apply set
            if tier not in apply_tiers:
                skips.append(("tier_excluded", f"{template_name}/{code} [{tier}]"))
                continue

            raw_weeks = lc.get("applicable_weeks") or applicable_weeks
            weeks_key = json.dumps(raw_weeks, sort_keys=True) if raw_weeks is not None else None
            key = (template_name, code, weeks_key)
            existing = existing_reqs.get(key)

            if existing:
                # UPDATE: only widen or correct
                changes = {}
                e_min = existing["min_halfdays"]
                e_max = existing["max_halfdays"]
                e_tgt = existing["target_halfdays"]

                l_min = lc["learned_min"]
                l_max = lc["learned_max"]
                l_tgt = lc["learned_target"]

                # Only update if learned range is wider or min is lower
                if l_min < e_min:
                    changes["min_halfdays"] = l_min
                if l_max > e_max:
                    changes["max_halfdays"] = l_max
                if e_tgt is None or abs(l_tgt - e_tgt) >= 2:
                    changes["target_halfdays"] = l_tgt

                # Update prefer_full_days if learned differs
                if "prefer_full_days" in lc and lc["prefer_full_days"] != existing["prefer_full_days"]:
                    changes["prefer_full_days"] = lc["prefer_full_days"]

                if changes:
                    updates.append((existing["id"], template_name, code, changes, tier))
                else:
                    skips.append(("no_change_needed", f"{template_name}/{code}"))

            else:
                # INSERT: new constraint pair
                if lc.get("is_background") and lc.get("presence_rate", 1.0) < 0.5:
                    skips.append(("low_presence_bg", f"{template_name}/{code}"))
                    continue

                weeks_hash = compute_applicable_weeks_hash(
                    lc.get("applicable_weeks") or applicable_weeks
                )
                raw_weeks = lc.get("applicable_weeks") or applicable_weeks
                inserts.append({
                    "template_id": template_id,
                    "activity_id": activity_id,
                    "template_name": template_name,
                    "activity_code": code,
                    "min_halfdays": lc["learned_min"],
                    "max_halfdays": lc["learned_max"],
                    "target_halfdays": lc["learned_target"],
                    "prefer_full_days": lc.get("prefer_full_days", True),
                    "applicable_weeks": json.dumps(raw_weeks) if raw_weeks else None,
                    "applicable_weeks_hash": weeks_hash,
                    "priority": 50,  # default priority
                    "confidence": tier,
                })

    # Special: fix orphaned ADV constraints (set min=0)
    for key, req in existing_reqs.items():
        tname, code, _weeks = key
        if code == "ADV" and req["min_halfdays"] > 0:
            # Check if this template has learned data
            if tname in learned:
                activities = learned[tname].get("activities", {})
                if "ADV" not in activities:
                    # ADV exists in DB but not observed → orphan, set min=0
                    updates.append((
                        req["id"], tname, "ADV",
                        {"min_halfdays": 0},
                        "orphan_fix",
                    ))

    return inserts, updates, skips, review


def apply_changes(cur, inserts, updates, dry_run=True):
    """Apply planned changes to the database."""
    if dry_run:
        return

    # INSERTs
    import uuid as _uuid
    for ins in inserts:
        new_id = str(_uuid.uuid4())
        cur.execute("""
            INSERT INTO rotation_activity_requirements
                (id, rotation_template_id, activity_id, min_halfdays, max_halfdays,
                 target_halfdays, prefer_full_days, applicable_weeks,
                 applicable_weeks_hash, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (rotation_template_id, activity_id, applicable_weeks_hash)
            DO UPDATE SET
                min_halfdays = EXCLUDED.min_halfdays,
                max_halfdays = EXCLUDED.max_halfdays,
                target_halfdays = EXCLUDED.target_halfdays
        """, (
            new_id, ins["template_id"], ins["activity_id"],
            ins["min_halfdays"], ins["max_halfdays"], ins["target_halfdays"],
            ins["prefer_full_days"], ins["applicable_weeks"],
            ins["applicable_weeks_hash"], ins["priority"],
        ))

    # UPDATEs
    for rar_id, tname, code, changes, tier in updates:
        set_clauses = []
        values = []
        for col, val in changes.items():
            set_clauses.append(f"{col} = %s")
            values.append(val)
        values.append(rar_id)

        cur.execute(
            f"UPDATE rotation_activity_requirements SET {', '.join(set_clauses)} WHERE id = %s",
            values,
        )


def apply_universal_fixes(cur, dry_run=True):
    """Apply universal fixes independent of learned data.

    These are council-consensus fixes that apply to ALL templates:
    1. lec: set min_halfdays=0 wherever it's >0 (history shows 0-3 actual)
    2. ADV: set min_halfdays=0 wherever it's >0 (orphaned across 20+ templates)
    """
    fixes = []

    # Universal lec fix
    cur.execute("""
        SELECT rar.id, rt.name, rar.min_halfdays
        FROM rotation_activity_requirements rar
        JOIN activities a ON rar.activity_id = a.id
        JOIN rotation_templates rt ON rar.rotation_template_id = rt.id
        WHERE a.code = 'lec' AND rar.min_halfdays > 0
    """)
    lec_rows = cur.fetchall()
    for row in lec_rows:
        fixes.append(("lec_min_zero", row[0], row[1], row[2]))

    # Universal ADV fix
    cur.execute("""
        SELECT rar.id, rt.name, rar.min_halfdays
        FROM rotation_activity_requirements rar
        JOIN activities a ON rar.activity_id = a.id
        JOIN rotation_templates rt ON rar.rotation_template_id = rt.id
        WHERE a.code = 'ADV' AND rar.min_halfdays > 0
    """)
    adv_rows = cur.fetchall()
    for row in adv_rows:
        fixes.append(("adv_min_zero", row[0], row[1], row[2]))

    print(f"\n  Universal fixes:")
    print(f"    lec min→0:  {len(lec_rows)} templates")
    print(f"    ADV min→0:  {len(adv_rows)} templates")

    if not dry_run:
        for fix_type, rar_id, tname, old_min in fixes:
            cur.execute(
                "UPDATE rotation_activity_requirements SET min_halfdays = 0 WHERE id = %s",
                (rar_id,),
            )

    return len(fixes)


def write_review_file(review_items, output_dir="/tmp"):
    """Write needs_review.md for low-confidence constraints."""
    if not review_items:
        return None

    lines = [
        "# Constraints Needing Coordinator Review",
        "",
        "These constraints have low confidence (n < 4 instances) and were NOT auto-applied.",
        "Review each and decide whether to add to the database manually.",
        "",
        "| Template | Activity | Min | Max | Target | Reason |",
        "|----------|----------|-----|-----|--------|--------|",
    ]

    for item in review_items:
        lines.append(
            f"| {item['template_name']} | {item['activity_code']} | "
            f"{item['learned_min']} | {item['learned_max']} | "
            f"{item['learned_target']} | {item['reason']} |"
        )

    path = Path(output_dir) / "needs_review.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def main():
    args = parse_args()

    print("=" * 60)
    print("  CONSTRAINT CALIBRATION")
    print("=" * 60)

    mode = "DRY RUN" if args.dry_run else ("HIGH only" if args.apply_high else "HIGH + MEDIUM")
    print(f"  Mode: {mode}")

    # Determine which tiers to apply
    # Dry-run simulates --apply-all to show the full picture
    if args.dry_run:
        apply_tiers = {"high", "medium"}
    elif args.apply_high:
        apply_tiers = {"high"}
    else:
        apply_tiers = {"high", "medium"}

    # Load learned constraints
    print(f"\nLoading learned constraints from {args.learned}...")
    learned = json.loads(Path(args.learned).read_text())
    print(f"  {len(learned)} templates with learned constraints")

    # Connect to DB
    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()

    print("Fetching existing requirements...")
    existing_reqs = fetch_existing_requirements(cur)
    print(f"  {len(existing_reqs)} existing rotation_activity_requirements")

    template_ids = fetch_template_ids(cur)
    activity_ids = fetch_activity_ids(cur)
    print(f"  {len(template_ids)} active templates, {len(activity_ids)} activities")

    # Plan changes
    print("\nPlanning changes...")
    inserts, updates, skips, review = plan_changes(
        learned, existing_reqs, template_ids, activity_ids, apply_tiers,
    )

    # Report
    print(f"\n{'='*60}")
    print(f"  CHANGE PLAN")
    print(f"{'='*60}")
    print(f"  INSERTs (new constraints):  {len(inserts)}")
    print(f"  UPDATEs (widen/correct):    {len(updates)}")
    print(f"  SKIPs:                      {len(skips)}")
    print(f"  Needs review (low conf):    {len(review)}")

    if inserts:
        print(f"\n  New constraints to INSERT:")
        for ins in inserts[:20]:
            weeks = f" weeks={ins.get('applicable_weeks')}" if ins.get("applicable_weeks") != "null" else ""
            print(f"    {ins['template_name']:35s} + {ins['activity_code']:15s} "
                  f"min={ins['min_halfdays']}, max={ins['max_halfdays']}, "
                  f"target={ins['target_halfdays']} [{ins['confidence']}]{weeks}")
        if len(inserts) > 20:
            print(f"    ... and {len(inserts) - 20} more")

    if updates:
        print(f"\n  Constraints to UPDATE:")
        for rar_id, tname, code, changes, tier in updates[:20]:
            change_str = ", ".join(f"{k}: →{v}" for k, v in changes.items())
            print(f"    {tname:35s} / {code:15s} {change_str} [{tier}]")
        if len(updates) > 20:
            print(f"    ... and {len(updates) - 20} more")

    # Skip reasons summary
    skip_reasons = defaultdict(int)
    for reason, _ in skips:
        skip_reasons[reason] += 1
    if skip_reasons:
        print(f"\n  Skip reasons:")
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason:25s} {count:3d}")

    # Write review file
    if review:
        review_path = write_review_file(review, args.backup_dir)
        if review_path:
            print(f"\n  Review file: {review_path}")

    # Universal fixes report (always shown)
    apply_universal_fixes(cur, dry_run=True)

    # Apply (or not)
    if args.dry_run:
        print(f"\n  DRY RUN — no changes applied.")
        conn.close()
        return

    # Backup before writing
    backup_path = backup_table(args.db_url, args.backup_dir)

    # Apply in transaction
    print(f"\n  Applying learned constraint changes...")
    try:
        apply_changes(cur, inserts, updates, dry_run=False)
        n_universal = apply_universal_fixes(cur, dry_run=False)
        conn.commit()
        print(f"  SUCCESS: {len(inserts)} inserted, {len(updates)} updated, {n_universal} universal fixes")
    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        print(f"  Transaction rolled back. No changes applied.")
        if backup_path:
            print(f"  Backup available at: {backup_path}")
        sys.exit(1)

    # Verify
    cur.execute("SELECT COUNT(*) FROM rotation_activity_requirements")
    new_count = cur.fetchone()[0]
    print(f"  Total requirements after calibration: {new_count}")

    conn.close()
    print(f"\n  Calibration complete.")
    if backup_path:
        print(f"  Backup: {backup_path}")


if __name__ == "__main__":
    main()
