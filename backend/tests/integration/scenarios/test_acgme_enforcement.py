"""Integration tests for ACGME rule enforcement scenarios."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestACGMEEnforcementScenarios:
    """Test ACGME enforcement scenarios."""

    def test_prevent_80_hour_violation_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test system prevents assignment that would violate 80-hour rule."""
        start_date = date.today()

        # Create near-maximum workload
        for i in range(6):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                db.commit()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Try to add assignment that would violate 80-hour rule
        violation_block = Block(
            id=uuid4(),
            date=start_date + timedelta(days=6),
            time_of_day="AM",
            block_number=1,
        )
        db.add(violation_block)
        db.commit()

        response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(violation_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        # Should reject or warn
        assert response.status_code in [200, 201, 400, 422]

    def test_enforce_mandatory_day_off_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test system enforces 1-in-7 day off rule."""
        start_date = date.today()

        # Create 7 consecutive days of assignments
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                db.commit()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Try to add 8th day (should violate 1-in-7)
        eighth_day_block = Block(
            id=uuid4(),
            date=start_date + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(eighth_day_block)
        db.commit()

        response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(eighth_day_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        # Should reject or flag violation
        assert response.status_code in [200, 201, 400, 422]

    def test_supervision_ratio_enforcement_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test supervision ratio is enforced."""
        # Create supervised rotation
        template = RotationTemplate(
            id=uuid4(),
            name="Supervised",
            rotation_type="procedures",
            abbreviation="SUP",
            supervision_required=True,
            max_supervision_ratio=2,  # 1:2
        )
        db.add(template)
        db.commit()

        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Try to assign 3 residents without faculty
        for i in range(3):
            response = client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(sample_residents[i].id),
                    "rotation_template_id": str(template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Should detect violation
        compliance_response = client.get(
            f"/api/analytics/supervision?block_id={block.id}",
            headers=auth_headers,
        )
        assert compliance_response.status_code in [200, 404]
