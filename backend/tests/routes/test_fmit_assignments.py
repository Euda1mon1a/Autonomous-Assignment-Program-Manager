"""Tests for FMIT assignment conflict checks."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.fmit_assignments import get_week_start
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


def _create_fmit_template(db: Session) -> RotationTemplate:
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT",
        rotation_type="inpatient",
        abbreviation="FMIT",
        display_abbreviation="FMIT",
        leave_eligible=False,
        includes_weekend_work=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def test_conflict_check_requires_fmit_template(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    response = client.get(
        "/api/v1/fmit/assignments/check-conflicts",
        params={
            "faculty_id": str(sample_faculty.id),
            "week_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "FMIT rotation template not found"


def test_conflict_check_detects_blocking_absence_and_suggestions(
    client: TestClient,
    auth_headers: dict,
    db: Session,
    sample_faculty: Person,
):
    _create_fmit_template(db)

    other_faculty = Person(
        id=uuid4(),
        name="Dr. Backup",
        type="faculty",
        email="backup@hospital.org",
    )
    db.add(other_faculty)
    db.commit()

    week_start = get_week_start(date.today())
    week_end = week_start + timedelta(days=6)

    absence = Absence(
        id=uuid4(),
        person_id=sample_faculty.id,
        start_date=week_start,
        end_date=week_end,
        absence_type="deployment",
        is_blocking=True,
        is_away_from_program=False,
        status="approved",
    )
    db.add(absence)
    db.commit()

    response = client.get(
        "/api/v1/fmit/assignments/check-conflicts",
        params={
            "faculty_id": str(sample_faculty.id),
            "week_date": week_start.isoformat(),
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["can_assign"] is False
    assert any(c["conflict_type"] == "leave_overlap" for c in data["conflicts"])
    assert any("Consider" in suggestion for suggestion in data["suggestions"])


def test_conflict_check_flags_back_to_back_warning(
    client: TestClient,
    auth_headers: dict,
    db: Session,
    sample_faculty: Person,
):
    template = _create_fmit_template(db)

    week_start = get_week_start(date.today())
    prior_date = week_start - timedelta(days=7)

    block = Block(
        id=uuid4(),
        date=prior_date,
        time_of_day="AM",
        block_number=1,
        is_weekend=prior_date.weekday() >= 5,
        is_holiday=False,
    )
    db.add(block)

    assignment = Assignment(
        id=uuid4(),
        block_id=block.id,
        person_id=sample_faculty.id,
        rotation_template_id=template.id,
        role="primary",
    )
    db.add(assignment)
    db.commit()

    response = client.get(
        "/api/v1/fmit/assignments/check-conflicts",
        params={
            "faculty_id": str(sample_faculty.id),
            "week_date": week_start.isoformat(),
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["can_assign"] is True
    assert any(c["conflict_type"] == "back_to_back" for c in data["conflicts"])
    assert any("back-to-back" in warning for warning in data["warnings"])
