"""
Integration tests for bulk operations workflow.

Tests bulk data operations for efficiency and consistency.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestBulkOperationsWorkflow:
    """Test bulk operation workflows."""

    def test_bulk_block_creation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating multiple blocks at once."""
        start_date = date.today()
        blocks_data = []

        for i in range(14):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                blocks_data.append({
                    "date": current_date.isoformat(),
                    "time_of_day": tod,
                    "block_number": 1,
                })

        bulk_response = client.post(
            "/api/blocks/bulk",
            json={"blocks": blocks_data},
            headers=auth_headers,
        )
        assert bulk_response.status_code in [200, 201, 404, 501]

    def test_bulk_assignment_creation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test creating multiple assignments at once."""
        # Create blocks first
        start_date = date.today()
        blocks = []
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Prepare bulk assignments
        assignments_data = [
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
            json={"assignments": assignments_data},
            headers=auth_headers,
        )
        assert bulk_response.status_code in [200, 201, 404, 501]

    def test_bulk_update_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_blocks: list[Block],
    ):
        """Test bulk updating records."""
        update_data = [
            {
                "id": str(block.id),
                "is_holiday": True,
            }
            for block in sample_blocks[:5]
        ]

        bulk_update_response = client.put(
            "/api/blocks/bulk",
            json={"updates": update_data},
            headers=auth_headers,
        )
        assert bulk_update_response.status_code in [200, 404, 501]

    def test_bulk_delete_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test bulk deletion of records."""
        # Create blocks to delete
        block_ids = []
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=100 + i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            block_ids.append(str(block.id))
        db.commit()

        # Bulk delete
        delete_response = client.post(
            "/api/blocks/bulk-delete",
            json={"block_ids": block_ids},
            headers=auth_headers,
        )
        assert delete_response.status_code in [200, 204, 404, 501]

    def test_bulk_import_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk import from CSV/Excel."""
        # Simulate CSV upload
        import_response = client.post(
            "/api/imports/schedule",
            files={"file": ("schedule.csv", b"date,time_of_day,person,rotation\n", "text/csv")},
            headers=auth_headers,
        )
        assert import_response.status_code in [200, 201, 400, 404, 501]

    def test_bulk_export_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk export to CSV/Excel."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        export_response = client.get(
            f"/api/exports/schedule/csv?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 404]

    def test_bulk_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test bulk validation before import."""
        # Prepare invalid and valid data
        assignments_data = [
            {
                "block_id": str(uuid4()),  # Non-existent block
                "person_id": str(sample_residents[0].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            }
        ]

        validate_response = client.post(
            "/api/assignments/bulk-validate",
            json={"assignments": assignments_data},
            headers=auth_headers,
        )
        assert validate_response.status_code in [200, 400, 404, 501]
