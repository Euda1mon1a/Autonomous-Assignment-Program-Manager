#!/usr/bin/env python3
"""
Backfill Saturday-off weekly patterns for ICU/NICU/L&D rotation templates.

Idempotent: safe to run multiple times.

Usage:
    python backend/scripts/backfill_weekly_patterns_saturday_off.py --dry-run
    python backend/scripts/backfill_weekly_patterns_saturday_off.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import and_, func, or_

# Add backend directory to path for app imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern

SATURDAY_DOW = 6  # 0=Sunday, 6=Saturday
TIME_OF_DAY = ("AM", "PM")

TARGET_ABBREVS = {"ICU", "NICU", "LAD", "LND", "LD", "L&D"}
EXCLUDED_ABBREVS = {"LDNF"}


def _normalize(text: str | None) -> str:
    return (text or "").strip().upper()


def resolve_time_off_activities(db) -> dict[str, Activity]:
    """Resolve AM/PM time-off activities for Saturday patterns."""
    activities = (
        db.query(Activity)
        .filter(func.lower(Activity.activity_category) == "time_off")
        .all()
    )
    if not activities:
        raise ValueError("No time_off activities found in activities table")

    by_code: dict[str, Activity] = {}
    by_display: dict[str, Activity] = {}

    for activity in activities:
        code = _normalize(activity.code)
        display = _normalize(activity.display_abbreviation)
        if code:
            by_code.setdefault(code, activity)
        if display:
            by_display.setdefault(display, activity)

    # Prefer explicit AM/PM weekend or OFF activities
    if "W-AM" in by_code and "W-PM" in by_code:
        return {"AM": by_code["W-AM"], "PM": by_code["W-PM"]}
    if "OFF-AM" in by_code and "OFF-PM" in by_code:
        return {"AM": by_code["OFF-AM"], "PM": by_code["OFF-PM"]}

    # Fallback to shared weekend/off activity
    shared = (
        by_code.get("W")
        or by_code.get("OFF")
        or by_display.get("W")
        or by_display.get("OFF")
    )
    if shared:
        return {"AM": shared, "PM": shared}

    available = ", ".join(sorted(by_code.keys()))
    raise ValueError(
        "No suitable time_off activity found. "
        f"Expected code W/OFF or W-AM/W-PM. Available codes: {available}"
    )


def load_target_templates(db) -> list[RotationTemplate]:
    """Load rotation templates for ICU/NICU/L&D (excluding night float)."""
    name_match = and_(
        func.lower(RotationTemplate.name).like("%labor%"),
        func.lower(RotationTemplate.name).like("%delivery%"),
    )
    templates = (
        db.query(RotationTemplate)
        .filter(
            RotationTemplate.is_archived.is_(False),
            or_(
                RotationTemplate.rotation_type.is_(None),
                func.lower(RotationTemplate.rotation_type) != "off",
            ),
            or_(
                RotationTemplate.abbreviation.in_(TARGET_ABBREVS),
                RotationTemplate.display_abbreviation.in_(TARGET_ABBREVS),
                name_match,
            ),
        )
        .all()
    )

    filtered: list[RotationTemplate] = []
    for template in templates:
        abbrev = _normalize(template.abbreviation)
        display = _normalize(template.display_abbreviation)
        name = (template.name or "").lower()
        if abbrev in EXCLUDED_ABBREVS or display in EXCLUDED_ABBREVS:
            continue
        if "night float" in name:
            continue
        filtered.append(template)

    return filtered


def backfill_patterns(db, dry_run: bool = False) -> dict[str, int]:
    activities = resolve_time_off_activities(db)
    templates = load_target_templates(db)

    if not templates:
        raise ValueError("No ICU/NICU/L&D rotation templates found")

    created = 0
    updated = 0
    skipped = 0

    for template in templates:
        for tod in TIME_OF_DAY:
            desired = activities[tod]
            existing = (
                db.query(WeeklyPattern)
                .filter(
                    WeeklyPattern.rotation_template_id == template.id,
                    WeeklyPattern.day_of_week == SATURDAY_DOW,
                    WeeklyPattern.time_of_day == tod,
                    WeeklyPattern.week_number.is_(None),
                )
                .one_or_none()
            )

            if existing:
                if existing.activity_id == desired.id:
                    skipped += 1
                    continue

                updated += 1
                if not dry_run:
                    existing.activity_id = desired.id
                    existing.activity_type = desired.code
                continue

            created += 1
            if not dry_run:
                db.add(
                    WeeklyPattern(
                        rotation_template_id=template.id,
                        day_of_week=SATURDAY_DOW,
                        time_of_day=tod,
                        week_number=None,
                        activity_type=desired.code,
                        activity_id=desired.id,
                        is_protected=False,
                        notes="P6-2 Saturday off pattern backfill",
                    )
                )

    if not dry_run:
        db.commit()

    return {"created": created, "updated": updated, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill Saturday-off weekly patterns for ICU/NICU/L&D."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing to the database.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = backfill_patterns(db, dry_run=args.dry_run)
        mode = "DRY RUN" if args.dry_run else "APPLIED"
        print(
            f"[{mode}] created={result['created']} updated={result['updated']} skipped={result['skipped']}"
        )
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
