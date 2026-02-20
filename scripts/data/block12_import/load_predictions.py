"""Pre-fill Block 12 NULL HDAs using ML predictions.

Reads predictions from schedule-vision/data/block12_db_ready.json
and updates half_day_assignments where activity_id IS NULL.

Only fills high/medium confidence predictions. Low confidence flagged
for manual review.

Usage:
  1. Copy block12_db_ready.json to Mini (or access via shared path)
  2. Backup DB: ./checkpoint.sh pre_predictions
  3. Run: backend/.venv/bin/python scripts/data/block12_import/load_predictions.py
  4. Verify with: SELECT count(*) FROM half_day_assignments
         WHERE date >= '2026-05-07' AND activity_id IS NOT NULL;

Options:
  --dry-run    Show what would be updated without writing to DB
  --min-conf   Minimum confidence threshold (default: 0.5)
  --all        Include low-confidence predictions too
"""

import argparse
import json
import sys
from pathlib import Path

import psycopg2

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

# Default prediction file location
PREDICTIONS_PATH = Path(__file__).parent.parent.parent.parent / "schedule-vision" / "data" / "block12_db_ready.json"
ALT_PREDICTIONS_PATH = Path.home() / "schedule-vision" / "data" / "block12_db_ready.json"


def load_predictions(predictions_path: Path, min_confidence: float, dry_run: bool):
    """Load ML predictions into NULL HDAs."""
    # Load predictions
    data = json.loads(predictions_path.read_text())
    preds = data["predictions"]
    meta = data["metadata"]

    print(f"Block 12 Prediction Loader")
    print(f"  Source: {predictions_path}")
    print(f"  Training: {meta['training_data']}")
    print(f"  Total predictions: {meta['total_predictions']}")
    print(f"  Min confidence: {min_confidence:.0%}")
    if dry_run:
        print(f"  ** DRY RUN — no DB writes **")

    # Filter by confidence
    filtered = [p for p in preds if p["confidence"] >= min_confidence]
    print(f"  Predictions above threshold: {len(filtered)}")

    if not filtered:
        print("  No predictions above threshold. Done.")
        return

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    # Build lookups
    cur.execute("SELECT id, name FROM people")
    people = {name: pid for pid, name in cur.fetchall()}

    cur.execute("SELECT id, code FROM activities")
    activities = {code: aid for aid, code in cur.fetchall()}

    # Track results
    updated = 0
    skipped_no_person = 0
    skipped_no_activity = 0
    skipped_not_null = 0
    skipped_no_hda = 0
    missing_people = set()
    missing_activities = set()

    for p in filtered:
        db_name = p["db_name"]
        d = p["date"]
        tod = p["time_of_day"]
        db_code = p["db_activity_code"]
        confidence = p["confidence"]

        person_id = people.get(db_name)
        if not person_id:
            missing_people.add(db_name)
            skipped_no_person += 1
            continue

        activity_id = activities.get(db_code)
        if not activity_id:
            missing_activities.add(db_code)
            skipped_no_activity += 1
            continue

        if dry_run:
            # Check if HDA exists and is NULL
            cur.execute(
                """SELECT activity_id FROM half_day_assignments
                WHERE person_id = %s AND date = %s AND time_of_day = %s""",
                (person_id, d, tod),
            )
            row = cur.fetchone()
            if not row:
                skipped_no_hda += 1
            elif row[0] is not None:
                skipped_not_null += 1
            else:
                updated += 1
        else:
            # Only update NULL activity_ids (don't overwrite manual data)
            # Note: source='solver' because ck_half_day_assignments_check_half_day_source
            # only allows: preload|manual|solver|template. See gotcha #9.
            cur.execute(
                """UPDATE half_day_assignments
                SET activity_id = %s, source = 'solver', updated_at = NOW()
                WHERE person_id = %s AND date = %s AND time_of_day = %s
                  AND activity_id IS NULL""",
                (activity_id, person_id, d, tod),
            )
            updated += cur.rowcount
            if cur.rowcount == 0:
                # Check why: no HDA or already filled?
                cur.execute(
                    """SELECT activity_id FROM half_day_assignments
                    WHERE person_id = %s AND date = %s AND time_of_day = %s""",
                    (person_id, d, tod),
                )
                row = cur.fetchone()
                if not row:
                    skipped_no_hda += 1
                elif row[0] is not None:
                    skipped_not_null += 1

    if not dry_run:
        conn.commit()

    cur.close()
    conn.close()

    # Report
    print(f"\n  Results:")
    print(f"    {'Would update' if dry_run else 'Updated'}: {updated} NULL HDAs")
    print(f"    Skipped (already filled): {skipped_not_null}")
    print(f"    Skipped (no HDA row): {skipped_no_hda}")
    print(f"    Skipped (person not in DB): {skipped_no_person}")
    print(f"    Skipped (activity not in DB): {skipped_no_activity}")

    if missing_people:
        print(f"\n  Missing people ({len(missing_people)}):")
        for name in sorted(missing_people):
            print(f"    - {name}")

    if missing_activities:
        print(f"\n  Missing activities ({len(missing_activities)}):")
        for code in sorted(missing_activities):
            print(f"    - {code}")

    # Confidence distribution of what was loaded
    conf_tiers = {"high (>=80%)": 0, "medium (50-79%)": 0, "low (<50%)": 0}
    for p in filtered:
        if p["confidence"] >= 0.8:
            conf_tiers["high (>=80%)"] += 1
        elif p["confidence"] >= 0.5:
            conf_tiers["medium (50-79%)"] += 1
        else:
            conf_tiers["low (<50%)"] += 1
    print(f"\n  Confidence distribution of loaded predictions:")
    for tier, count in conf_tiers.items():
        print(f"    {tier}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Load Block 12 ML predictions")
    parser.add_argument("--predictions", default=None,
                        help="Path to block12_db_ready.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be updated")
    parser.add_argument("--min-conf", type=float, default=0.5,
                        help="Minimum confidence threshold (0.0-1.0)")
    parser.add_argument("--all", action="store_true",
                        help="Include all predictions (no confidence filter)")
    args = parser.parse_args()

    # Find predictions file
    if args.predictions:
        pred_path = Path(args.predictions)
    elif PREDICTIONS_PATH.exists():
        pred_path = PREDICTIONS_PATH
    elif ALT_PREDICTIONS_PATH.exists():
        pred_path = ALT_PREDICTIONS_PATH
    else:
        print(f"Error: Cannot find predictions file.")
        print(f"  Checked: {PREDICTIONS_PATH}")
        print(f"  Checked: {ALT_PREDICTIONS_PATH}")
        print(f"  Use --predictions to specify path")
        sys.exit(1)

    min_conf = 0.0 if args.all else args.min_conf
    load_predictions(pred_path, min_conf, args.dry_run)


if __name__ == "__main__":
    main()
