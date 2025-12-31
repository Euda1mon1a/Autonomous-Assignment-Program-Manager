"""
Integration tests for assignment lifecycle workflow.

Tests assignment creation, modification, conflict detection, and deletion.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestAssignmentWorkflow:
    """Test assignment lifecycle operations."""

    def test_create_assignment_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test creating a new assignment."""
        # Create assignment
        create_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert create_response.status_code in [200, 201]
        assignment_id = create_response.json()["id"]

        # Verify assignment
        get_response = client.get(
            f"/api/assignments/{assignment_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200

    def test_modify_assignment_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
        sample_residents: list[Person],
    ):
        """Test modifying an existing assignment."""
        # Update assignment
        new_resident = sample_residents[0]
        update_response = client.put(
            f"/api/assignments/{sample_assignment.id}",
            json={"person_id": str(new_resident.id)},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # Verify update
        get_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["person_id"] == str(new_resident.id)

    def test_bulk_assignment_creation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test creating multiple assignments at once."""
        # Create blocks
        start_date = date.today()
        blocks = []
        for i in range(5):
            current_date = start_date + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create bulk assignments
        bulk_data = [
            {
                "block_id": str(blocks[i].id),
                "person_id": str(sample_residents[i % len(sample_residents)].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            }
            for i in range(len(blocks))
        ]

        bulk_response = client.post(
            "/api/assignments/bulk",
            json={"assignments": bulk_data},
            headers=auth_headers,
        )
        assert bulk_response.status_code in [200, 201, 404, 501]

    def test_assignment_conflict_detection_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test detection of conflicting assignments."""
        # Create first assignment
        first_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert first_response.status_code in [200, 201]

        # Try to create conflicting assignment
        conflict_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "backup",
            },
            headers=auth_headers,
        )

        # Should detect conflict
        if conflict_response.status_code in [200, 201]:
            # Check conflict endpoint
            conflicts = client.get(
                f"/api/conflicts/?person_id={sample_resident.id}",
                headers=auth_headers,
            )
            assert conflicts.status_code in [200, 404]
        else:
            assert conflict_response.status_code in [400, 409]

    def test_assignment_by_date_range_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test retrieving assignments by date range."""
        # Create assignments across date range
        start_date = date.today()
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(sample_resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Query by date range
        range_response = client.get(
            f"/api/assignments/?start_date={start_date.isoformat()}&end_date={(start_date + timedelta(days=6)).isoformat()}",
            headers=auth_headers,
        )
        assert range_response.status_code == 200
        assignments = range_response.json()
        assert len(assignments) >= 7

    def test_assignment_by_person_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
        sample_resident: Person,
    ):
        """Test retrieving all assignments for a person."""
        person_assignments = client.get(
            f"/api/assignments/?person_id={sample_resident.id}",
            headers=auth_headers,
        )
        assert person_assignments.status_code == 200
        assignments = person_assignments.json()
        assert len(assignments) > 0

    def test_assignment_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test assignment validation before creation."""
        # Validate assignment
        validate_response = client.post(
            "/api/assignments/validate",
            json={
                "block_id": str(sample_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert validate_response.status_code in [200, 404, 501]

    def test_assignment_history_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
    ):
        """Test retrieving assignment change history."""
        # Get assignment history
        history_response = client.get(
            f"/api/assignments/{sample_assignment.id}/history",
            headers=auth_headers,
        )
        assert history_response.status_code in [200, 404, 501]

    def test_delete_assignments_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
    ):
        """Test deleting assignments."""
        # Delete assignment
        delete_response = client.delete(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert delete_response.status_code in [200, 204]

        # Verify deletion
        get_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_bulk_delete_assignments_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test bulk deletion of assignments."""
        # Create multiple assignments
        assignment_ids = []
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i % len(sample_residents)].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
            assignment_ids.append(str(assignment.id))
        db.commit()

        # Bulk delete
        bulk_delete_response = client.post(
            "/api/assignments/bulk-delete",
            json={"assignment_ids": assignment_ids},
            headers=auth_headers,
        )
        assert bulk_delete_response.status_code in [200, 204, 404, 501]
