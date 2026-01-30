"""Tests for time-off pattern application in inpatient preloads."""

from datetime import timedelta
from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.inpatient_preload import InpatientPreload
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.services.sync_preload_service import SyncPreloadService
from app.utils.academic_blocks import get_block_dates


def _create_activity(db, code: str, display: str, category: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=display,
        activity_category=category,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


def _create_time_off_pattern(
    db,
    template: RotationTemplate,
    activity: Activity,
    day_of_week: int,
    time_of_day: str,
) -> WeeklyPattern:
    pattern = WeeklyPattern(
        id=uuid4(),
        rotation_template_id=template.id,
        day_of_week=day_of_week,
        time_of_day=time_of_day,
        week_number=None,
        activity_type="off",
        activity_id=activity.id,
        is_protected=False,
    )
    db.add(pattern)
    return pattern


def _get_assignment_code(db, person_id, date_val, time_of_day: str) -> str | None:
    assignment = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == person_id,
            HalfDayAssignment.date == date_val,
            HalfDayAssignment.time_of_day == time_of_day,
        )
        .first()
    )
    if not assignment or not assignment.activity:
        return None
    return assignment.activity.display_abbreviation or assignment.activity.code


def _find_weekday(start_date, end_date, weekday: int):
    current = start_date
    while current <= end_date:
        if current.weekday() == weekday:
            return current
        current += timedelta(days=1)
    return None


def test_inpatient_preload_time_off_patterns_override_nf_weekend(db):
    _create_activity(db, "NF", "NF", ActivityCategory.CLINICAL.value)
    _create_activity(db, "OFF", "OFF", ActivityCategory.TIME_OFF.value)
    off_activity = _create_activity(db, "W", "W", ActivityCategory.TIME_OFF.value)

    resident = Person(
        id=uuid4(),
        name="Resident NF",
        type="resident",
        pgy_level=2,
    )
    template = RotationTemplate(
        id=uuid4(),
        name="Night Float",
        rotation_type="inpatient",
        abbreviation="NF",
        display_abbreviation="NF",
    )
    db.add_all([resident, template])
    db.commit()

    _create_time_off_pattern(
        db, template, off_activity, day_of_week=6, time_of_day="AM"
    )
    _create_time_off_pattern(
        db, template, off_activity, day_of_week=6, time_of_day="PM"
    )
    db.commit()

    block_number = 10
    academic_year = 2025
    block_dates = get_block_dates(block_number, academic_year)

    preload = InpatientPreload(
        id=uuid4(),
        person_id=resident.id,
        rotation_type="NF",
        start_date=block_dates.start_date,
        end_date=block_dates.end_date,
        assigned_by="scheduler",
    )
    db.add(preload)
    db.commit()

    service = SyncPreloadService(db)
    service._load_inpatient_preloads(block_dates.start_date, block_dates.end_date)

    saturday = _find_weekday(block_dates.start_date, block_dates.end_date, weekday=5)
    assert saturday is not None

    assert _get_assignment_code(db, resident.id, saturday, "AM") == "W"
    assert _get_assignment_code(db, resident.id, saturday, "PM") == "W"


def test_inpatient_preload_uses_pgy_specific_template_for_patterns(db):
    _create_activity(db, "FMIT", "FMIT", ActivityCategory.CLINICAL.value)
    off_activity = _create_activity(db, "W", "W", ActivityCategory.TIME_OFF.value)

    resident = Person(
        id=uuid4(),
        name="Resident FMIT",
        type="resident",
        pgy_level=1,
    )
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT PGY1",
        rotation_type="inpatient",
        abbreviation="FMIT-PGY1",
        display_abbreviation="FMIT-PGY1",
    )
    db.add_all([resident, template])
    db.commit()

    _create_time_off_pattern(
        db, template, off_activity, day_of_week=0, time_of_day="AM"
    )
    _create_time_off_pattern(
        db, template, off_activity, day_of_week=0, time_of_day="PM"
    )
    db.commit()

    block_number = 10
    academic_year = 2025
    block_dates = get_block_dates(block_number, academic_year)

    preload = InpatientPreload(
        id=uuid4(),
        person_id=resident.id,
        rotation_type="FMIT",
        start_date=block_dates.start_date,
        end_date=block_dates.end_date,
        assigned_by="scheduler",
    )
    db.add(preload)
    db.commit()

    service = SyncPreloadService(db)
    service._load_inpatient_preloads(block_dates.start_date, block_dates.end_date)

    sunday = _find_weekday(block_dates.start_date, block_dates.end_date, weekday=6)
    assert sunday is not None

    assert _get_assignment_code(db, resident.id, sunday, "AM") == "W"
    assert _get_assignment_code(db, resident.id, sunday, "PM") == "W"
