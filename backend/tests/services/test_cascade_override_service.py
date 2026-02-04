"""Tests for CascadeOverrideService planning safeguards."""

from datetime import date
from uuid import uuid4

import pytest

from app.models.person import Person
from app.schemas.cascade_override import CascadeOverrideRequest
from app.services.cascade_override_service import CascadeOverrideService


@pytest.mark.asyncio
async def test_cascade_override_requires_faculty(async_db_session, db):
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@example.org",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()

    service = CascadeOverrideService(async_db_session)
    request = CascadeOverrideRequest(
        person_id=resident.id,
        start_date=date.today(),
        end_date=date.today(),
        reason="deployment",
        notes=None,
        apply=False,
        max_depth=2,
    )

    plan = await service.plan_and_apply(request, created_by_id=None)

    assert plan.applied is False
    assert plan.steps == []
    assert "faculty" in plan.errors[0].lower()
