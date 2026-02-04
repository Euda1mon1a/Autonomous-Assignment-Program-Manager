from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.models.faculty_weekly_override import FacultyWeeklyOverride
from app.models.faculty_weekly_template import FacultyWeeklyTemplate
from app.models.person import Person
from app.services.faculty_weekly_template_report import (
    FacultyWeeklyTemplateCoverageService,
)


@pytest.mark.asyncio
async def test_missing_weekly_templates_report(async_db):
    faculty_with_template = Person(
        id=uuid4(),
        name="Dr. Template",
        type="faculty",
        email="template@hospital.org",
        faculty_role="core",
    )
    faculty_with_override = Person(
        id=uuid4(),
        name="Dr. Override",
        type="faculty",
        email="override@hospital.org",
        faculty_role="oic",
    )
    faculty_missing = Person(
        id=uuid4(),
        name="Dr. Missing",
        type="faculty",
        email="missing@hospital.org",
        faculty_role="apd",
    )
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@hospital.org",
        pgy_level=2,
    )

    async_db.add_all(
        [faculty_with_template, faculty_with_override, faculty_missing, resident]
    )
    await async_db.commit()

    template = FacultyWeeklyTemplate(
        id=uuid4(),
        person_id=faculty_with_template.id,
        day_of_week=1,
        time_of_day="AM",
        week_number=None,
        activity_id=None,
        is_locked=False,
        priority=50,
    )
    override = FacultyWeeklyOverride(
        id=uuid4(),
        person_id=faculty_with_override.id,
        effective_date=date(2026, 1, 5),
        day_of_week=1,
        time_of_day="PM",
        activity_id=None,
        is_locked=False,
    )

    async_db.add_all([template, override])
    await async_db.commit()

    service = FacultyWeeklyTemplateCoverageService(async_db)
    report = await service.get_missing_faculty_weekly_templates()

    assert report["total_faculty"] == 3
    assert report["total_missing"] == 1
    assert [item["name"] for item in report["missing"]] == ["Dr. Missing"]
