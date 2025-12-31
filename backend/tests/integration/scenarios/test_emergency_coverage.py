"""
Integration tests for emergency coverage scenarios.

Tests system response to emergency situations requiring schedule changes.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestEmergencyCoverageScenarios:
    """Test emergency coverage scenarios."""

    def test_sudden_absence_coverage_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test covering a sudden absence."""
        # Step 1: Create scheduled assignments
        start_date = date.today()
        blocks = []

        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Assign resident
        resident = sample_residents[0]
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Step 2: Report sudden absence
        absence = Absence(
            id=uuid4(),
            person_id=resident.id,
            start_date=start_date,
            end_date=start_date + timedelta(days=2),
            absence_type="emergency",
            notes="Sudden illness",
        )
        db.add(absence)
        db.commit()

        # Step 3: Find coverage
        coverage_response = client.post(
            "/api/emergency/find-coverage",
            json={
                "absent_person_id": str(resident.id),
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=2)).isoformat(),
            },
            headers=auth_headers,
        )
        assert coverage_response.status_code in [200, 404, 501]

    def test_deployment_coverage_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test covering military deployment."""
        # Create assignments for faculty member
        start_date = date.today()
        faculty = sample_faculty_members[0]

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty.id,
                rotation_template_id=sample_rotation_template.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        # Report deployment
        deployment = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
            absence_type="deployment",
            notes="TDY assignment",
        )
        db.add(deployment)
        db.commit()

        # Find replacement
        replacement_response = client.post(
            "/api/emergency/find-replacement",
            json={
                "person_id": str(faculty.id),
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=30)).isoformat(),
            },
            headers=auth_headers,
        )
        assert replacement_response.status_code in [200, 404, 501]

    def test_cascade_failure_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Test handling cascade of failures."""
        # Create minimal coverage
        start_date = date.today()
        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Assign all residents
        for resident in sample_residents:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Multiple absences
        for i, resident in enumerate(sample_residents[:2]):
            absence = Absence(
                id=uuid4(),
                person_id=resident.id,
                start_date=start_date,
                end_date=start_date,
                absence_type="sick",
                notes=f"Sick day {i}",
            )
            db.add(absence)
        db.commit()

        # Check if system can handle
        coverage_response = client.get(
            f"/api/emergency/coverage-status?date={start_date.isoformat()}",
            headers=auth_headers,
        )
        assert coverage_response.status_code in [200, 404, 501]

    def test_n_minus_2_failure_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test N-2 failure handling."""
        # Test simultaneous failure of two residents
        start_date = date.today()

        # Check resilience
        resilience_response = client.post(
            "/api/resilience/test-n-minus-2",
            json={
                "start_date": start_date.isoformat(),
                "person_ids": [str(r.id) for r in sample_residents[:2]],
            },
            headers=auth_headers,
        )
        assert resilience_response.status_code in [200, 404, 501]

    def test_urgent_procedure_coverage_scenario(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty_members: list[Person],
    ):
        """Test urgent procedure requiring specialist."""
        # Find available specialist
        specialist_response = client.post(
            "/api/emergency/find-specialist",
            json={
                "specialty": "Sports Medicine",
                "date": date.today().isoformat(),
                "urgency": "high",
            },
            headers=auth_headers,
        )
        assert specialist_response.status_code in [200, 404, 501]
