"""Tests for cascading delete impact endpoint."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_number_for_date


def test_delete_impact_person_dependencies(client: TestClient, auth_headers: dict, db):
    today = date.today()

    person = Person(
        id=uuid4(),
        name="Delete Impact Resident",
        type="resident",
        email="delete.impact@example.org",
        pgy_level=1,
    )
    db.add(person)

    rotation = RotationTemplate(
        id=uuid4(),
        name="Delete Impact Rotation",
        rotation_type="inpatient",
        abbreviation="IM",
    )
    db.add(rotation)

    block_number, _ = get_block_number_for_date(today)
    block = Block(
        id=uuid4(),
        date=today,
        time_of_day="AM",
        block_number=block_number,
        is_weekend=False,
        is_holiday=False,
    )
    db.add(block)

    db.add(
        Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
    )

    db.add(
        Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=today,
            end_date=today + timedelta(days=2),
            absence_type="vacation",
        )
    )

    db.commit()

    response = client.get(
        f"/api/v1/admin/delete-impact?resource_type=person&resource_id={person.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["resource_type"] == "person"
    assert payload["resource_id"] == str(person.id)

    dependencies = {item["table"]: item for item in payload["dependencies"]}
    assert dependencies["assignments"]["count"] == 1
    assert dependencies["absences"]["count"] == 1
    assert payload["total_dependents"] == sum(
        item["count"] for item in payload["dependencies"]
    )
