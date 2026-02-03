"""Tests for CallOverrideService."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.call_assignment import CallAssignment
from app.models.call_override import CallOverride
from app.models.person import Person
from app.schemas.call_override import CallOverrideCreate
from app.services.call_override_service import CallOverrideService


@pytest.mark.asyncio
async def test_list_overrides_requires_filters(async_db_session):
    service = CallOverrideService(async_db_session)

    with pytest.raises(HTTPException) as excinfo:
        await service.list_overrides()

    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_create_override_rejects_same_person(db, async_db_session):
    person = Person(
        id=uuid4(),
        name="Dr. Call",
        type="faculty",
        email="call.faculty@example.org",
    )
    db.add(person)
    db.commit()

    assignment = CallAssignment(
        id=uuid4(),
        date=date.today(),
        person_id=person.id,
        call_type="weekday",
        is_weekend=False,
        is_holiday=False,
    )
    db.add(assignment)
    db.commit()

    service = CallOverrideService(async_db_session)

    with pytest.raises(HTTPException) as excinfo:
        await service.create_override(
            CallOverrideCreate(
                call_assignment_id=assignment.id,
                replacement_person_id=person.id,
                override_type="coverage",
                reason="sick",
                notes=None,
                supersedes_override_id=None,
            ),
            created_by_id=None,
        )

    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_apply_overrides_replaces_person(db, async_db_session):
    original = Person(
        id=uuid4(),
        name="Dr. Original",
        type="faculty",
        email="original@example.org",
    )
    replacement = Person(
        id=uuid4(),
        name="Dr. Replacement",
        type="faculty",
        email="replacement@example.org",
    )
    db.add_all([original, replacement])
    db.commit()

    assignment = CallAssignment(
        id=uuid4(),
        date=date.today(),
        person_id=original.id,
        call_type="weekday",
        is_weekend=False,
        is_holiday=False,
    )
    db.add(assignment)
    db.commit()

    override = CallOverride(
        id=uuid4(),
        call_assignment_id=assignment.id,
        original_person_id=original.id,
        replacement_person_id=replacement.id,
        override_type="coverage",
        reason="sick",
        notes=None,
        effective_date=assignment.date,
        call_type=assignment.call_type,
        is_active=True,
    )
    db.add(override)
    db.commit()

    service = CallOverrideService(async_db_session)
    result = await service.apply_overrides([assignment])

    assert len(result) == 1
    assert result[0].person_id == replacement.id
    assert result[0].person.id == replacement.id
