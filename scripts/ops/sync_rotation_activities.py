#!/usr/bin/env python
"""Backfill specialty activities and default requirements for rotation templates."""

from __future__ import annotations

import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.activity import Activity, ActivityCategory
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.utils.activity_naming import activity_code_from_name, activity_display_abbrev


DEFAULT_WEEKLY_C_MIN = 2
DEFAULT_WEEKLY_C_MAX = 4
DEFAULT_WEEKLY_SPECIALTY_MIN = 3
DEFAULT_WEEKLY_SPECIALTY_MAX = 4


def ensure_activity(session, template: RotationTemplate) -> tuple[Activity | None, bool]:
    if (template.activity_type or "").lower() not in ("clinic", "outpatient"):
        return None, False

    code = activity_code_from_name(template.name)
    display_abbrev = activity_display_abbrev(
        template.name, template.display_abbreviation, template.abbreviation
    )

    activity = session.execute(
        select(Activity).where(Activity.name == template.name)
    ).scalars().first()
    if activity:
        return activity, False

    activity = session.execute(
        select(Activity).where(Activity.code.ilike(code))
    ).scalars().first()
    if activity:
        return activity, False

    activity = Activity(
        name=template.name,
        code=code,
        display_abbreviation=display_abbrev,
        activity_category=ActivityCategory.CLINICAL.value,
        font_color=template.font_color,
        background_color=template.background_color,
        requires_supervision=True,
        is_protected=False,
        counts_toward_clinical_hours=True,
        provides_supervision=False,
        counts_toward_physical_capacity=True,
        display_order=0,
    )
    session.add(activity)
    session.flush()
    return activity, True


def ensure_default_requirements(
    session,
    template: RotationTemplate,
    clinic_activity: Activity,
    specialty_activity: Activity,
) -> int:
    existing = session.execute(
        select(RotationActivityRequirement).where(
            RotationActivityRequirement.rotation_template_id == template.id
        )
    ).scalars().first()
    if existing:
        return 0

    created = 0
    for week in (1, 2, 3, 4):
        session.add(
            RotationActivityRequirement(
                rotation_template_id=template.id,
                activity_id=clinic_activity.id,
                min_halfdays=DEFAULT_WEEKLY_C_MIN,
                max_halfdays=DEFAULT_WEEKLY_C_MAX,
                applicable_weeks=[week],
                prefer_full_days=True,
                priority=80,
            )
        )
        session.add(
            RotationActivityRequirement(
                rotation_template_id=template.id,
                activity_id=specialty_activity.id,
                min_halfdays=DEFAULT_WEEKLY_SPECIALTY_MIN,
                max_halfdays=DEFAULT_WEEKLY_SPECIALTY_MAX,
                applicable_weeks=[week],
                prefer_full_days=True,
                priority=80,
            )
        )
        created += 2
    session.flush()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync rotation activities")
    parser.add_argument(
        "--with-default-requirements",
        action="store_true",
        help="Create default weekly activity requirements where missing",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        templates = (
            session.execute(
                select(RotationTemplate).where(RotationTemplate.is_archived == False)  # noqa: E712
            )
            .scalars()
            .all()
        )

        clinic_activity = session.execute(
            select(Activity).where(Activity.code == "fm_clinic")
        ).scalars().first()
        if not clinic_activity:
            clinic_activity = Activity(
                name="FM Clinic",
                code="fm_clinic",
                display_abbreviation="C",
                activity_category=ActivityCategory.CLINICAL.value,
                requires_supervision=True,
                is_protected=False,
                counts_toward_clinical_hours=True,
                provides_supervision=False,
                counts_toward_physical_capacity=True,
                display_order=0,
            )
            session.add(clinic_activity)
            session.flush()

        created_activities = 0
        created_requirements = 0
        for template in templates:
            activity, created = ensure_activity(session, template)
            if created:
                created_activities += 1

            if args.with_default_requirements and activity is not None:
                created_requirements += ensure_default_requirements(
                    session, template, clinic_activity, activity
                )

        session.commit()
        print(
            f"Synced activities for {created_activities} templates; "
            f"created {created_requirements} requirements"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
