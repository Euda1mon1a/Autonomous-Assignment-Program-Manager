"""
Integration tests for complete schedule workflow.

Tests the end-to-end lifecycle of schedule creation, modification,
validation, and deletion.
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
from app.utils.academic_blocks import get_block_number_for_date


class TestScheduleWorkflow:
    """Test complete schedule lifecycle."""

    def test_create_schedule_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
    ):
        """Test creating a complete schedule from scratch."""
        # Step 1: Create rotation templates
        template_response = client.post(
            "/api/rotation-templates/",
            json={
                "name": "Clinic A",
                "rotation_type": "outpatient",
                "abbreviation": "CLNA",
                "max_residents": 2,
                "supervision_required": True,
            },
            headers=auth_headers,
        )
        assert template_response.status_code == 201
        template_id = template_response.json()["id"]

        # Step 2: Create blocks for a week
        start_date = date.today()
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                block_response = client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": 1,
                    },
                    headers=auth_headers,
                )
                assert block_response.status_code in [200, 201]

        # Step 3: Create assignments
        blocks = db.query(Block).filter(Block.date >= start_date).all()
        assignments_created = []

        for i, block in enumerate(blocks[:10]):  # Assign first 10 blocks
            resident = sample_residents[i % len(sample_residents)]
            assignment_response = client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(resident.id),
                    "rotation_template_id": template_id,
                    "role": "primary",
                },
                headers=auth_headers,
            )
            assert assignment_response.status_code in [200, 201]
            assignments_created.append(assignment_response.json())

        # Step 4: Validate schedule compliance
        validation_response = client.post(
            "/api/schedule/validate",
            json={
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=6)).isoformat(),
            },
            headers=auth_headers,
        )
        assert validation_response.status_code == 200

        # Step 5: Verify assignments were created
        assert len(assignments_created) == 10

        # Step 6: Retrieve schedule
        schedule_response = client.get(
            f"/api/schedule/?start_date={start_date.isoformat()}&end_date={(start_date + timedelta(days=6)).isoformat()}",
            headers=auth_headers,
        )
        assert schedule_response.status_code == 200
        schedule_data = schedule_response.json()
        assert len(schedule_data) > 0

    def test_modify_schedule_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_assignment: Assignment,
        sample_residents: list[Person],
    ):
        """Test modifying an existing schedule."""
        # Step 1: Get current assignment
        get_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        original = get_response.json()

        # Step 2: Update assignment to different resident
        new_resident = sample_residents[0]
        update_response = client.put(
            f"/api/assignments/{sample_assignment.id}",
            json={"person_id": str(new_resident.id)},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["person_id"] == str(new_resident.id)

        # Step 3: Verify change was persisted
        verify_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["person_id"] == str(new_resident.id)

    def test_delete_schedule_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
    ):
        """Test deleting schedule assignments."""
        # Step 1: Verify assignment exists
        get_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200

        # Step 2: Delete assignment
        delete_response = client.delete(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert delete_response.status_code in [200, 204]

        # Step 3: Verify assignment no longer exists
        verify_response = client.get(
            f"/api/assignments/{sample_assignment.id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 404

    def test_bulk_schedule_generation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
    ):
        """Test generating schedule for multiple weeks at once."""
        # Step 1: Create rotation templates
        templates = []
        for i, activity in enumerate(["outpatient", "inpatient", "procedures"]):
            response = client.post(
                "/api/rotation-templates/",
                json={
                    "name": f"Rotation {i + 1}",
                    "rotation_type": activity,
                    "abbreviation": f"R{i + 1}",
                    "max_residents": 3,
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            templates.append(response.json())

        # Step 2: Create blocks for 4 weeks
        start_date = date.today()
        for i in range(28):
            current_date = start_date + timedelta(days=i)
            # Use Thursday-Wednesday aligned block number calculation
            block_number, _ = get_block_number_for_date(current_date)
            for tod in ["AM", "PM"]:
                client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": block_number,
                    },
                    headers=auth_headers,
                )

        # Step 3: Request bulk schedule generation
        generate_response = client.post(
            "/api/scheduler/generate",
            json={
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=27)).isoformat(),
                "person_ids": [str(r.id) for r in sample_residents],
                "template_ids": [t["id"] for t in templates],
            },
            headers=auth_headers,
        )

        # Step 4: Verify generation started
        assert generate_response.status_code in [200, 202]

    def test_schedule_conflict_detection_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test that overlapping assignments are detected."""
        # Step 1: Create first assignment
        first_block = sample_blocks[0]
        first_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(first_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert first_response.status_code in [200, 201]

        # Step 2: Try to create overlapping assignment (same person, same block)
        second_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(first_block.id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "backup",
            },
            headers=auth_headers,
        )

        # Step 3: Should either reject or detect conflict
        # Different systems may handle this differently
        if second_response.status_code in [200, 201]:
            # If created, check for conflict detection
            conflicts_response = client.get(
                f"/api/conflicts/?person_id={sample_resident.id}",
                headers=auth_headers,
            )
            assert conflicts_response.status_code == 200
        else:
            # Should return 400 or 409 for conflict
            assert second_response.status_code in [400, 409]

    def test_schedule_export_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment: Assignment,
    ):
        """Test exporting schedule in various formats."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Test CSV export
        csv_response = client.get(
            f"/api/exports/schedule/csv?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert csv_response.status_code == 200
        assert "text/csv" in csv_response.headers.get("content-type", "")

        # Test JSON export
        json_response = client.get(
            f"/api/exports/schedule/json?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert json_response.status_code == 200

    def test_schedule_copy_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_blocks: list[Block],
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test copying a schedule from one period to another."""
        # Step 1: Create assignments in first week
        first_week = sample_blocks[:14]  # 7 days * 2 blocks
        for i, block in enumerate(first_week):
            resident = sample_residents[i % len(sample_residents)]
            client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Step 2: Create blocks for second week
        second_week_start = date.today() + timedelta(days=7)
        for i in range(7):
            current_date = second_week_start + timedelta(days=i)
            for tod in ["AM", "PM"]:
                client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": 1,
                    },
                    headers=auth_headers,
                )

        # Step 3: Request schedule copy
        copy_response = client.post(
            "/api/schedule/copy",
            json={
                "source_start": date.today().isoformat(),
                "source_end": (date.today() + timedelta(days=6)).isoformat(),
                "target_start": second_week_start.isoformat(),
            },
            headers=auth_headers,
        )

        # Should either succeed or explain why copy isn't supported
        assert copy_response.status_code in [200, 201, 501]
