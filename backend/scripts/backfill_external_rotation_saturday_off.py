#!/usr/bin/env python3
"""Backfill Saturday-off weekly patterns for external inpatient rotations.

Ensures ICU/NICU/L&D rotation templates have Saturday AM/PM time-off
patterns in weekly_patterns. Safe to run multiple times.
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import func, or_

# Add backend/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models.activity import Activity  # noqa: E402
from app.models.rotation_template import RotationTemplate  # noqa: E402
from app.models.weekly_pattern import WeeklyPattern  # noqa: E402

SATURDAY_DOW = 6  # 0=Sunday, 6=Saturday
TARGET_ABBREVIATIONS = {"ICU", "NICU", "LAD", "LND", "LD", "L&D"}
TARGET_DISPLAY_ABBREVIATIONS = {"ICU", "NICU", "LND", "LD", "L&D"}
TARGET_NAMES = {
    "intensive care unit intern",
    "nicu",
    "labor and delivery",
    "labor & delivery",
    "labor and delivery intern",
    "labor & delivery intern",
}


def _resolve_time_off_activity(db) -> Activity:
    """Find a time-off activity to use for Saturday off patterns."""
    candidates = ["W", "OFF"]
    for code in candidates:
        activity = (
            db.query(Activity)
            .filter(
                func.lower(Activity.activity_category) == "time_off",
                or_(
                    func.lower(Activity.code) == code.lower(),
                    func.lower(Activity.display_abbreviation) == code.lower(),
                    func.lower(Activity.name) == code.lower(),
                ),
            )
            .first()
        )
        if activity:
            return activity
    raise ValueError("No time_off activity found for codes W or OFF")


def _load_target_templates(db) -> list[RotationTemplate]:
    name_matches = [name.lower() for name in TARGET_NAMES]
    return (
        db.query(RotationTemplate)
        .filter(
            or_(
                func.upper(RotationTemplate.abbreviation).in_(TARGET_ABBREVIATIONS),
                func.upper(RotationTemplate.display_abbreviation).in_(
                    TARGET_DISPLAY_ABBREVIATIONS
                ),
                func.lower(RotationTemplate.name).in_(name_matches),
            )
        )
        .all()
    )


def _is_time_off_activity(activity: Activity | None) -> bool:
    if not activity:
        return False
    if (activity.activity_category or "").lower() == "time_off":
        return True
    return (activity.code or "").strip().upper() in {"W", "OFF"}


def backfill(dry_run: bool = False) -> int:
    db = SessionLocal()
    created = 0
    try:
        time_off_activity = _resolve_time_off_activity(db)
        templates = _load_target_templates(db)

        if not templates:
            print("No matching rotation templates found.")
            return 0

        for template in templates:
            for time_of_day in ("AM", "PM"):
                existing = (
                    db.query(WeeklyPattern)
                    .filter(
                        WeeklyPattern.rotation_template_id == template.id,
                        WeeklyPattern.day_of_week == SATURDAY_DOW,
                        WeeklyPattern.time_of_day == time_of_day,
                    )
                    .all()
                )

                if any(_is_time_off_activity(p.activity) for p in existing):
                    continue

                if existing:
                    print(
                        f"Skip: existing Saturday {time_of_day} pattern for {template.name} ({template.abbreviation or template.display_abbreviation})"
                    )
                    continue

                pattern = WeeklyPattern(
                    rotation_template_id=template.id,
                    day_of_week=SATURDAY_DOW,
                    time_of_day=time_of_day,
                    week_number=None,
                    activity_type=time_off_activity.code,
                    activity_id=time_off_activity.id,
                    is_protected=False,
                    notes="P6-2 Saturday-off backfill",
                )
                db.add(pattern)
                created += 1

        if dry_run:
            db.rollback()
        else:
            db.commit()

        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Backfill Saturday-off weekly patterns for ICU/NICU/L&D rotations")
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without committing",
    )
    args = parser.parse_args()

    created = backfill(dry_run=args.dry_run)
    if args.dry_run:
        print(f"Dry-run complete. Patterns to create: {created}")
    else:
        print(f"Backfill complete. Patterns created: {created}")


if __name__ == "__main__":
    main()
