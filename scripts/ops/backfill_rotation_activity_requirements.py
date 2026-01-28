#!/usr/bin/env python3
"""Backfill rotation activity requirements from weekly patterns.

Creates RotationActivityRequirement rows for outpatient templates that are missing
requirements. Uses WeeklyPattern counts as the source of truth.
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from typing import Iterable


def _load_env() -> None:
    """Load .env/.env.codex and ensure DATABASE_URL is set when possible."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    for path in (".env.codex", ".env"):
        if os.path.exists(path):
            load_dotenv(path, override=True)

    if not os.environ.get("DATABASE_URL"):
        pwd = os.environ.get("DB_PASSWORD")
        if pwd:
            os.environ["DATABASE_URL"] = (
                f"postgresql://scheduler:{pwd}@localhost:5432/residency_scheduler"
            )


def _priority_for_activity(activity) -> int:
    """Return priority weight based on activity category/protection."""
    if activity is None:
        return 80
    if activity.is_protected:
        return 100
    category = (activity.activity_category or "").lower()
    if category in {"educational", "administrative", "time_off"}:
        return 100
    return 80


def _prefer_full_days(activity) -> bool:
    """Prefer full days for clinical activities; otherwise False."""
    if activity is None:
        return False
    return (activity.activity_category or "").lower() == "clinical"


def _build_week_sets(patterns) -> list[tuple[list[int] | None, list]]:
    """Return list of (applicable_weeks, patterns) pairs.

    If any week-specific patterns exist, return per-week entries (applicable_weeks=[week])
    using week-specific patterns when present, else falling back to default patterns.
    If no week-specific patterns exist, return a single entry with applicable_weeks=None.
    """
    default_patterns = [p for p in patterns if p.week_number is None]
    week_specific = {week: [p for p in patterns if p.week_number == week] for week in range(1, 5)}
    has_week_specific = any(week_specific[week] for week in range(1, 5))

    week_sets: list[tuple[list[int] | None, list]] = []
    if has_week_specific:
        for week in range(1, 5):
            week_patterns = week_specific[week] or default_patterns
            if not week_patterns:
                continue
            week_sets.append(([week], week_patterns))
    else:
        if default_patterns:
            week_sets.append((None, default_patterns))
    return week_sets


def _iter_template_ids(value: Iterable[str] | None) -> set[str]:
    if not value:
        return set()
    return {v.strip() for v in value if v.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill RotationActivityRequirement rows from weekly patterns",
    )
    parser.add_argument(
        "--rotation-type",
        default="outpatient",
        help="Rotation type to target (default: outpatient)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing requirements for templates in scope",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing",
    )
    parser.add_argument(
        "--template-id",
        action="append",
        help="Limit to specific rotation_template IDs (repeatable)",
    )
    args = parser.parse_args()

    _load_env()

    from sqlalchemy import delete, select
    from sqlalchemy.orm import selectinload

    from app.db.session import SessionLocal
    from app.models.rotation_activity_requirement import RotationActivityRequirement
    from app.models.rotation_template import RotationTemplate
    from app.models.weekly_pattern import WeeklyPattern

    template_id_filter = _iter_template_ids(args.template_id)
    rotation_type = (args.rotation_type or "").strip().lower()

    session = SessionLocal()
    created_total = 0
    skipped_existing = 0
    skipped_no_patterns = 0
    skipped_out_of_scope = 0
    processed = 0

    try:
        stmt = (
            select(RotationTemplate)
            .options(
                selectinload(RotationTemplate.weekly_patterns).selectinload(
                    WeeklyPattern.activity
                ),
                selectinload(RotationTemplate.activity_requirements),
            )
            .where(RotationTemplate.is_archived == False)  # noqa: E712
        )
        templates = session.execute(stmt).scalars().all()

        for template in templates:
            if rotation_type and (template.rotation_type or "").lower() != rotation_type:
                skipped_out_of_scope += 1
                continue
            if template_id_filter and str(template.id) not in template_id_filter:
                skipped_out_of_scope += 1
                continue

            processed += 1
            existing_reqs = list(template.activity_requirements or [])
            if existing_reqs and not args.replace:
                skipped_existing += 1
                continue

            patterns = [p for p in (template.weekly_patterns or []) if p.activity_id]
            if not patterns:
                skipped_no_patterns += 1
                continue

            if args.replace and existing_reqs:
                session.execute(
                    delete(RotationActivityRequirement).where(
                        RotationActivityRequirement.rotation_template_id == template.id
                    )
                )

            week_sets = _build_week_sets(patterns)
            for applicable_weeks, week_patterns in week_sets:
                counts = Counter(p.activity_id for p in week_patterns)
                for activity_id, count in counts.items():
                    if count <= 0:
                        continue
                    activity = next(
                        (p.activity for p in week_patterns if p.activity_id == activity_id),
                        None,
                    )
                    req = RotationActivityRequirement(
                        rotation_template_id=template.id,
                        activity_id=activity_id,
                        min_halfdays=count,
                        max_halfdays=count,
                        target_halfdays=count,
                        applicable_weeks=applicable_weeks,
                        prefer_full_days=_prefer_full_days(activity),
                        priority=_priority_for_activity(activity),
                    )
                    session.add(req)
                    created_total += 1

        if args.dry_run:
            session.rollback()
        else:
            session.commit()

        action = "Would create" if args.dry_run else "Created"
        print(
            f"{action} {created_total} requirements across {processed} templates "
            f"(skipped existing={skipped_existing}, skipped no patterns={skipped_no_patterns})."
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
