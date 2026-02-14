"""Tests for ActivityService."""

from uuid import uuid4

import pytest

from app.models.activity import Activity, ActivityCategory
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_create_activity_rejects_duplicate_name(db):
    existing = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add(existing)
    db.commit()

    service = ActivityService(db)

    with pytest.raises(ValueError, match="name"):
        await service.create_activity(
            ActivityCreate(
                name="FM Clinic",
                code="fm_clinic_new",
                display_abbreviation="C2",
                activity_category=ActivityCategory.CLINICAL.value,
            )
        )


@pytest.mark.asyncio
async def test_update_activity_rejects_duplicate_code(db):
    activity_a = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    activity_b = Activity(
        id=uuid4(),
        name="Didactics",
        code="didactics",
        display_abbreviation="LEC",
        activity_category=ActivityCategory.EDUCATIONAL.value,
    )
    db.add_all([activity_a, activity_b])
    db.commit()

    service = ActivityService(db)

    with pytest.raises(ValueError, match="code"):
        await service.update_activity(
            activity_b.id,
            ActivityUpdate(code="fm_clinic"),
        )
