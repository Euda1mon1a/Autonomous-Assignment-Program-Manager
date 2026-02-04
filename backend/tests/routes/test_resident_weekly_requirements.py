"""Tests for resident weekly requirements endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.resident_weekly_requirement import ResidentWeeklyRequirement
from app.models.rotation_template import RotationTemplate


def test_apply_outpatient_defaults_creates_requirement(
    client: TestClient, auth_headers, db
):
    template = RotationTemplate(
        id=uuid4(),
        name="Outpatient Clinic",
        rotation_type="outpatient",
        template_category="rotation",
        leave_eligible=True,
    )
    db.add(template)
    db.commit()

    response = client.post(
        "/api/v1/resident-weekly-requirements/bulk/outpatient-defaults",
        params={"dry_run": "false"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1
    assert str(template.id) in data["created_ids"]

    requirement = (
        db.query(ResidentWeeklyRequirement)
        .filter(ResidentWeeklyRequirement.rotation_template_id == template.id)
        .one()
    )
    assert requirement.fm_clinic_min_per_week == 2
    assert requirement.academics_required is True
    assert requirement.protected_slots.get("wed_am") == "conference"
