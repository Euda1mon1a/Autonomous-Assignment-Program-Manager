from datetime import timedelta
from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.sync_preload_service import SyncPreloadService
from app.utils.academic_blocks import get_block_dates


def _create_activity(db, code: str, display: str, category: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=display,
        activity_category=category,
        is_protected=category == ActivityCategory.EDUCATIONAL.value,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


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


def _find_last_wednesday(start_date, end_date):
    current = start_date
    last_wed = None
    while current <= end_date:
        if current.weekday() == 2:
            if current + timedelta(days=7) > end_date:
                last_wed = current
                break
        current += timedelta(days=1)
    return last_wed


def _find_first_non_last_wednesday(start_date, end_date):
    current = start_date
    while current <= end_date:
        if current.weekday() == 2 and current + timedelta(days=7) <= end_date:
            return current
        current += timedelta(days=1)
    return None


def test_preload_wednesday_patterns_and_last_wednesday(db):
    _create_activity(db, "C", "C", ActivityCategory.CLINICAL.value)
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)
    _create_activity(db, "ADV", "ADV", ActivityCategory.EDUCATIONAL.value)

    resident = Person(
        id=uuid4(),
        name="Intern One",
        type="resident",
        pgy_level=1,
    )
    template = RotationTemplate(
        id=uuid4(),
        name="Neurology",
        activity_type="outpatient",
        abbreviation="NEURO",
    )
    db.add_all([resident, template])
    db.commit()

    block_number = 10
    academic_year = 2025
    assignment = BlockAssignment(
        id=uuid4(),
        block_number=block_number,
        academic_year=academic_year,
        resident_id=resident.id,
        rotation_template_id=template.id,
    )
    db.add(assignment)
    db.commit()

    service = SyncPreloadService(db)
    service._load_rotation_protected_preloads(block_number, academic_year)

    block_dates = get_block_dates(block_number, academic_year)
    last_wed = _find_last_wednesday(block_dates.start_date, block_dates.end_date)
    first_wed = _find_first_non_last_wednesday(
        block_dates.start_date, block_dates.end_date
    )

    assert last_wed is not None
    assert first_wed is not None

    assert _get_assignment_code(db, resident.id, first_wed, "AM") == "C"
    assert _get_assignment_code(db, resident.id, first_wed, "PM") == "LEC"

    assert _get_assignment_code(db, resident.id, last_wed, "AM") == "LEC"
    assert _get_assignment_code(db, resident.id, last_wed, "PM") == "ADV"


def test_preload_hilo_pattern(db):
    _create_activity(db, "C", "C", ActivityCategory.CLINICAL.value)
    _create_activity(db, "TDY", "TDY", ActivityCategory.TIME_OFF.value)
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)
    _create_activity(db, "ADV", "ADV", ActivityCategory.EDUCATIONAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident Hilo",
        type="resident",
        pgy_level=3,
    )
    template = RotationTemplate(
        id=uuid4(),
        name="Hilo",
        activity_type="off",
        abbreviation="HILO",
    )
    db.add_all([resident, template])
    db.commit()

    block_number = 10
    academic_year = 2025
    assignment = BlockAssignment(
        id=uuid4(),
        block_number=block_number,
        academic_year=academic_year,
        resident_id=resident.id,
        rotation_template_id=template.id,
    )
    db.add(assignment)
    db.commit()

    service = SyncPreloadService(db)
    service._load_rotation_protected_preloads(block_number, academic_year)

    block_dates = get_block_dates(block_number, academic_year)
    day0 = block_dates.start_date
    day1 = block_dates.start_date + timedelta(days=1)
    day2 = block_dates.start_date + timedelta(days=2)
    day19 = block_dates.start_date + timedelta(days=19)

    assert _get_assignment_code(db, resident.id, day0, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day0, "PM") == "C"
    assert _get_assignment_code(db, resident.id, day1, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day1, "PM") == "C"

    assert _get_assignment_code(db, resident.id, day2, "AM") == "TDY"
    assert _get_assignment_code(db, resident.id, day2, "PM") == "TDY"

    assert _get_assignment_code(db, resident.id, day19, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day19, "PM") == "C"


def test_preload_okinawa_pattern(db):
    _create_activity(db, "C", "C", ActivityCategory.CLINICAL.value)
    _create_activity(db, "TDY", "TDY", ActivityCategory.TIME_OFF.value)
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)
    _create_activity(db, "ADV", "ADV", ActivityCategory.EDUCATIONAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident Okinawa",
        type="resident",
        pgy_level=3,
    )
    template = RotationTemplate(
        id=uuid4(),
        name="Okinawa",
        activity_type="off",
        abbreviation="OKI",
    )
    db.add_all([resident, template])
    db.commit()

    block_number = 10
    academic_year = 2025
    assignment = BlockAssignment(
        id=uuid4(),
        block_number=block_number,
        academic_year=academic_year,
        resident_id=resident.id,
        rotation_template_id=template.id,
    )
    db.add(assignment)
    db.commit()

    service = SyncPreloadService(db)
    service._load_rotation_protected_preloads(block_number, academic_year)

    block_dates = get_block_dates(block_number, academic_year)
    day0 = block_dates.start_date
    day1 = block_dates.start_date + timedelta(days=1)
    day2 = block_dates.start_date + timedelta(days=2)
    day19 = block_dates.start_date + timedelta(days=19)

    assert _get_assignment_code(db, resident.id, day0, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day0, "PM") == "C"
    assert _get_assignment_code(db, resident.id, day1, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day1, "PM") == "C"

    assert _get_assignment_code(db, resident.id, day2, "AM") == "TDY"
    assert _get_assignment_code(db, resident.id, day2, "PM") == "TDY"

    assert _get_assignment_code(db, resident.id, day19, "AM") == "C"
    assert _get_assignment_code(db, resident.id, day19, "PM") == "C"


def test_preload_nf_split_secondary_rotation(db):
    _create_activity(db, "OFF", "OFF", ActivityCategory.TIME_OFF.value)
    _create_activity(db, "NF", "NF", ActivityCategory.CLINICAL.value)
    _create_activity(db, "W", "W", ActivityCategory.TIME_OFF.value)
    _create_activity(db, "LEC", "LEC", ActivityCategory.EDUCATIONAL.value)
    _create_activity(db, "ADV", "ADV", ActivityCategory.EDUCATIONAL.value)
    _create_activity(db, "C", "C", ActivityCategory.CLINICAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident NF",
        type="resident",
        pgy_level=3,
    )
    primary = RotationTemplate(
        id=uuid4(),
        name="Neurology",
        activity_type="outpatient",
        abbreviation="NEURO",
    )
    secondary = RotationTemplate(
        id=uuid4(),
        name="Night Float",
        activity_type="inpatient",
        abbreviation="NF",
    )
    db.add_all([resident, primary, secondary])
    db.commit()

    block_number = 10
    academic_year = 2025
    assignment = BlockAssignment(
        id=uuid4(),
        block_number=block_number,
        academic_year=academic_year,
        resident_id=resident.id,
        rotation_template_id=primary.id,
        secondary_rotation_template_id=secondary.id,
    )
    db.add(assignment)
    db.commit()

    service = SyncPreloadService(db)
    service._load_rotation_protected_preloads(block_number, academic_year)

    block_dates = get_block_dates(block_number, academic_year)
    mid_block_date = block_dates.start_date + timedelta(days=11)
    day0 = block_dates.start_date

    assert _get_assignment_code(db, resident.id, mid_block_date, "AM") == "OFF"
    assert _get_assignment_code(db, resident.id, mid_block_date, "PM") == "NF"

    # No protected preload expected on first day for NEURO (non-Wednesday)
    assert _get_assignment_code(db, resident.id, day0, "AM") is None
    assert _get_assignment_code(db, resident.id, day0, "PM") is None
