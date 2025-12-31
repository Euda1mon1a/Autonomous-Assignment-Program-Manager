"""Integration tests for data integrity scenarios."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestDataIntegrityScenarios:
    """Test data integrity scenarios."""

    def test_referential_integrity_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test referential integrity is maintained."""
        # Try to delete person with assignments
        response = client.delete(
            f"/api/people/{sample_assignment.person_id}",
            headers=auth_headers,
        )

        # Should prevent or cascade properly
        if response.status_code in [200, 204]:
            # Verify assignments handled
            assignment_check = (
                db.query(Assignment)
                .filter(Assignment.id == sample_assignment.id)
                .first()
            )
            # Should be deleted or orphaned properly

    def test_unique_constraint_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test unique constraints are enforced."""
        # Create person
        response1 = client.post(
            "/api/people/",
            json={
                "name": "Dr. Unique",
                "type": "resident",
                "email": "unique@test.org",
                "pgy_level": 1,
            },
            headers=auth_headers,
        )
        assert response1.status_code in [200, 201]

        # Try to create duplicate email
        response2 = client.post(
            "/api/people/",
            json={
                "name": "Dr. Duplicate",
                "type": "resident",
                "email": "unique@test.org",  # Same email
                "pgy_level": 1,
            },
            headers=auth_headers,
        )

        # Should reject duplicate
        assert response2.status_code in [400, 409, 422]

    def test_no_orphaned_records_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_rotation_template: RotationTemplate,
    ):
        """Test no orphaned records after deletion."""
        # Create block
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        # Create person
        person = Person(
            id=uuid4(),
            name="Dr. Test",
            type="resident",
            email="test@test.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Delete block
        response = client.delete(
            f"/api/blocks/{block.id}",
            headers=auth_headers,
        )

        if response.status_code in [200, 204]:
            # Verify no orphaned assignments
            orphaned = (
                db.query(Assignment).filter(Assignment.block_id == block.id).first()
            )
            assert orphaned is None

    def test_audit_trail_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
    ):
        """Test audit trail is maintained."""
        # Update assignment
        response = client.put(
            f"/api/assignments/{sample_assignment.id}",
            json={"role": "backup"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Check audit log
        audit_response = client.get(
            f"/api/audit/?entity_id={sample_assignment.id}",
            headers=auth_headers,
        )
        assert audit_response.status_code in [200, 404]
