"""Tests for half-day import staging draft creation."""

from datetime import date
from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.import_staging import (
    ImportBatch,
    ImportBatchStatus,
    ImportStagedAssignment,
)
from app.models.person import Person
from app.models.schedule_draft import DraftAssignmentChangeType, ScheduleDraftAssignment
from app.schemas.half_day_import import HalfDayDiffType
from app.services.half_day_import_service import HalfDayImportService


def _create_activity(db, code: str, category: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=code,
        activity_category=category,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


def test_create_draft_from_batch_modified_slot(db):
    _create_activity(db, "C", ActivityCategory.CLINICAL.value)
    _create_activity(db, "ADV", ActivityCategory.EDUCATIONAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident Import",
        type="resident",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()

    slot_date = date(2026, 3, 12)
    existing = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=db.query(Activity).filter(Activity.code == "C").first().id,
        source="solver",
    )
    db.add(existing)

    batch = ImportBatch(
        id=uuid4(),
        status=ImportBatchStatus.STAGED,
        target_block=10,
        target_start_date=slot_date,
        target_end_date=slot_date,
        row_count=1,
    )
    db.add(batch)
    db.commit()

    staged = ImportStagedAssignment(
        id=uuid4(),
        batch_id=batch.id,
        person_name=resident.name,
        assignment_date=slot_date,
        slot="AM",
        rotation_name="ADV",
        matched_person_id=resident.id,
        conflict_type=HalfDayDiffType.MODIFIED.value,
        existing_assignment_id=existing.id,
    )
    db.add(staged)
    db.commit()

    service = HalfDayImportService(db)
    result = service.create_draft_from_batch(batch.id)

    assert result.success is True
    assert result.modified == 1
    assert result.draft_id is not None

    draft_assignment = (
        db.query(ScheduleDraftAssignment)
        .filter(ScheduleDraftAssignment.draft_id == result.draft_id)
        .first()
    )
    assert draft_assignment is not None
    assert draft_assignment.change_type == DraftAssignmentChangeType.MODIFY
    assert draft_assignment.activity_code == "ADV"


def test_create_draft_from_batch_invalid_status(db):
    batch = ImportBatch(
        id=uuid4(),
        status=ImportBatchStatus.REJECTED,
        target_block=10,
        target_start_date=date(2026, 3, 12),
        target_end_date=date(2026, 3, 12),
        row_count=0,
    )
    db.add(batch)
    db.commit()

    service = HalfDayImportService(db)
    result = service.create_draft_from_batch(batch.id)

    assert result.success is False
    assert result.error_code == "INVALID_BATCH_STATUS"
    assert result.failed_ids == []


def test_create_draft_from_batch_missing_existing_assignment(db):
    _create_activity(db, "ADV", ActivityCategory.EDUCATIONAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident Import Missing",
        type="resident",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()

    slot_date = date(2026, 3, 12)
    batch = ImportBatch(
        id=uuid4(),
        status=ImportBatchStatus.STAGED,
        target_block=10,
        target_start_date=slot_date,
        target_end_date=slot_date,
        row_count=1,
    )
    db.add(batch)
    db.commit()

    staged = ImportStagedAssignment(
        id=uuid4(),
        batch_id=batch.id,
        person_name=resident.name,
        assignment_date=slot_date,
        slot="AM",
        rotation_name="ADV",
        matched_person_id=resident.id,
        conflict_type=HalfDayDiffType.MODIFIED.value,
        existing_assignment_id=None,
    )
    db.add(staged)
    db.commit()

    service = HalfDayImportService(db)
    result = service.create_draft_from_batch(batch.id)

    assert result.success is False
    assert result.failed == 1
    assert result.draft_id is None
    assert result.failed_ids == [staged.id]


def test_create_draft_from_batch_validation_errors(db):
    _create_activity(db, "C", ActivityCategory.CLINICAL.value)

    resident = Person(
        id=uuid4(),
        name="Resident Import Error",
        type="resident",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()

    slot_date = date(2026, 3, 12)
    batch = ImportBatch(
        id=uuid4(),
        status=ImportBatchStatus.STAGED,
        target_block=10,
        target_start_date=slot_date,
        target_end_date=slot_date,
        row_count=1,
    )
    db.add(batch)
    db.commit()

    staged = ImportStagedAssignment(
        id=uuid4(),
        batch_id=batch.id,
        person_name=resident.name,
        assignment_date=slot_date,
        slot="AM",
        rotation_name="C",
        matched_person_id=resident.id,
        conflict_type=HalfDayDiffType.ADDED.value,
        validation_errors=["Unknown activity code 'ZZZ'"],
    )
    db.add(staged)
    db.commit()

    service = HalfDayImportService(db)
    result = service.create_draft_from_batch(batch.id)

    assert result.success is False
    assert result.error_code == "ROW_FAILURE"
    assert result.failed_ids == [staged.id]
