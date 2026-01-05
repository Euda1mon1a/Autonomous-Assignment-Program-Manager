"""Tests for FMIT assignment CRUD API routes.

Comprehensive test suite covering:
- Create assignment (POST /fmit/assignments)
- Update assignment (PUT /fmit/assignments/{week_date})
- Delete assignment (DELETE /fmit/assignments/{faculty_id}/{week_date})
- Bulk create (POST /fmit/assignments/bulk)
- Year grid view (GET /fmit/assignments/year-grid/{year})
- Conflict checking (GET /fmit/assignments/check-conflicts)
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


@pytest.fixture
def fmit_template(db: Session) -> RotationTemplate:
    """Create the FMIT rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT",
        description="Faculty Maintenance in Training",
        requirements={},
    )
    db.add(template)
    db.commit()
    return template


@pytest.fixture
def sample_faculty(db: Session) -> Person:
    """Create a sample faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="faculty@hospital.org",
    )
    db.add(faculty)
    db.commit()
    return faculty


@pytest.fixture
def second_faculty(db: Session) -> Person:
    """Create a second faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Second Faculty",
        type="faculty",
        email="second@hospital.org",
    )
    db.add(faculty)
    db.commit()
    return faculty


@pytest.fixture
def week_blocks(db: Session) -> list[Block]:
    """Create blocks for a week (7 days x 2 AM/PM)."""
    # Use next Friday as week start
    today = date.today()
    days_until_friday = (4 - today.weekday()) % 7
    week_start = today + timedelta(days=days_until_friday + 7)  # Next Friday

    blocks = []
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=current_date.weekday() >= 5,
                is_holiday=False,
            )
            blocks.append(block)
            db.add(block)
    db.commit()
    return blocks


class TestCreateFMITAssignment:
    """Tests for POST /api/v1/fmit/assignments endpoint."""

    def test_create_assignment_success(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test creating an FMIT assignment successfully."""
        week_date = date.today() + timedelta(days=14)

        response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
                "created_by": "test_user",
                "notes": "Test assignment",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["faculty_id"] == str(sample_faculty.id)
        assert data["faculty_name"] == sample_faculty.name
        assert data["is_complete"] is True  # Should have all 14 blocks
        assert data["block_count"] == 14
        assert len(data["assignment_ids"]) == 14

    def test_create_assignment_faculty_not_found(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
    ):
        """Test creating assignment with non-existent faculty."""
        week_date = date.today() + timedelta(days=14)

        response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(uuid4()),  # Non-existent
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "FACULTY_NOT_FOUND"

    def test_create_assignment_no_fmit_template(
        self,
        client: TestClient,
        db: Session,
        sample_faculty: Person,
    ):
        """Test creating assignment when FMIT template doesn't exist."""
        week_date = date.today() + timedelta(days=14)

        response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"

    def test_create_assignment_with_blocking_absence(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test creating assignment when faculty has blocking absence."""
        week_date = date.today() + timedelta(days=14)

        # Create blocking absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=week_date,
            end_date=week_date + timedelta(days=7),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error_code"] == "CONFLICT_DETECTED"
        assert len(data["detail"]["conflicts"]) > 0

    def test_create_assignment_date_too_far_in_past(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test creating assignment with date too far in the past."""
        old_date = date.today() - timedelta(days=60)

        response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": old_date.isoformat(),
            },
        )

        assert response.status_code == 422  # Validation error


class TestUpdateFMITAssignment:
    """Tests for PUT /api/v1/fmit/assignments/{week_date} endpoint."""

    def test_update_assignment_reassign_faculty(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
        second_faculty: Person,
    ):
        """Test reassigning a week to different faculty."""
        week_date = date.today() + timedelta(days=14)

        # First create an assignment
        create_response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )
        assert create_response.status_code == 201

        # Now reassign to second faculty
        update_response = client.put(
            f"/api/v1/fmit/assignments/{week_date.isoformat()}",
            json={"faculty_id": str(second_faculty.id)},
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["faculty_id"] == str(second_faculty.id)
        assert data["faculty_name"] == second_faculty.name

    def test_update_assignment_not_found(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
    ):
        """Test updating non-existent assignment."""
        week_date = date.today() + timedelta(days=30)

        response = client.put(
            f"/api/v1/fmit/assignments/{week_date.isoformat()}",
            json={"faculty_id": str(uuid4())},
        )

        assert response.status_code == 404


class TestDeleteFMITAssignment:
    """Tests for DELETE /api/v1/fmit/assignments/{faculty_id}/{week_date} endpoint."""

    def test_delete_assignment_success(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test deleting an FMIT assignment successfully."""
        week_date = date.today() + timedelta(days=14)

        # First create
        create_response = client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )
        assert create_response.status_code == 201

        # Then delete
        delete_response = client.delete(
            f"/api/v1/fmit/assignments/{sample_faculty.id}/{week_date.isoformat()}"
        )

        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 14

    def test_delete_assignment_not_found(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test deleting non-existent assignment."""
        week_date = date.today() + timedelta(days=30)

        response = client.delete(
            f"/api/v1/fmit/assignments/{sample_faculty.id}/{week_date.isoformat()}"
        )

        assert response.status_code == 404


class TestBulkCreateFMITAssignments:
    """Tests for POST /api/v1/fmit/assignments/bulk endpoint."""

    def test_bulk_create_success(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
        second_faculty: Person,
    ):
        """Test bulk creating multiple assignments."""
        week1 = date.today() + timedelta(days=14)
        week2 = date.today() + timedelta(days=21)

        response = client.post(
            "/api/v1/fmit/assignments/bulk",
            json={
                "assignments": [
                    {"faculty_id": str(sample_faculty.id), "week_date": week1.isoformat()},
                    {"faculty_id": str(second_faculty.id), "week_date": week2.isoformat()},
                ],
                "created_by": "bulk_test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["successful_count"] == 2
        assert data["failed_count"] == 0

    def test_bulk_create_dry_run(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test bulk create with dry run mode."""
        week_date = date.today() + timedelta(days=14)

        response = client.post(
            "/api/v1/fmit/assignments/bulk",
            json={
                "assignments": [
                    {"faculty_id": str(sample_faculty.id), "week_date": week_date.isoformat()},
                ],
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["successful_count"] == 1

        # Verify nothing was actually created
        assignments = db.query(Assignment).all()
        assert len(assignments) == 0

    def test_bulk_create_skip_conflicts(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
        second_faculty: Person,
    ):
        """Test bulk create with skip_conflicts mode."""
        week_date = date.today() + timedelta(days=14)

        # Create blocking absence for first faculty
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=week_date,
            end_date=week_date + timedelta(days=7),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        response = client.post(
            "/api/v1/fmit/assignments/bulk",
            json={
                "assignments": [
                    {"faculty_id": str(sample_faculty.id), "week_date": week_date.isoformat()},
                    {"faculty_id": str(second_faculty.id), "week_date": week_date.isoformat()},
                ],
                "skip_conflicts": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["successful_count"] == 1
        assert data["skipped_count"] == 1  # First one skipped due to conflict


class TestYearGridView:
    """Tests for GET /api/v1/fmit/assignments/year-grid/{year} endpoint."""

    def test_year_grid_empty(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
    ):
        """Test year grid with no assignments."""
        current_year = date.today().year

        response = client.get(f"/api/v1/fmit/assignments/year-grid/{current_year}")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == current_year
        assert len(data["weeks"]) >= 52
        assert data["coverage_percentage"] == 0.0
        assert data["unassigned_weeks"] == data["total_weeks"]

    def test_year_grid_with_assignments(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test year grid with some assignments."""
        # Create an assignment
        week_date = date.today() + timedelta(days=14)
        client.post(
            "/api/v1/fmit/assignments",
            json={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )

        current_year = date.today().year
        response = client.get(f"/api/v1/fmit/assignments/year-grid/{current_year}")

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_weeks"] >= 1
        assert data["coverage_percentage"] > 0

        # Check faculty summaries
        assert len(data["faculty_summaries"]) >= 1
        faculty_summary = next(
            (f for f in data["faculty_summaries"] if f["faculty_id"] == str(sample_faculty.id)),
            None,
        )
        assert faculty_summary is not None
        assert faculty_summary["total_weeks"] >= 1

    def test_year_grid_academic_year(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
    ):
        """Test year grid with academic year boundaries."""
        current_year = date.today().year

        response = client.get(
            f"/api/v1/fmit/assignments/year-grid/{current_year}",
            params={"academic_year": True},
        )

        assert response.status_code == 200
        data = response.json()
        # Academic year starts July 1
        assert data["academic_year_start"] == f"{current_year}-07-01"
        assert data["academic_year_end"] == f"{current_year + 1}-06-30"


class TestConflictCheck:
    """Tests for GET /api/v1/fmit/assignments/check-conflicts endpoint."""

    def test_check_conflicts_no_conflicts(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test conflict check with no conflicts."""
        week_date = date.today() + timedelta(days=14)

        response = client.get(
            "/api/v1/fmit/assignments/check-conflicts",
            params={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["can_assign"] is True
        assert len(data["conflicts"]) == 0

    def test_check_conflicts_with_absence(
        self,
        client: TestClient,
        db: Session,
        fmit_template: RotationTemplate,
        sample_faculty: Person,
    ):
        """Test conflict check with blocking absence."""
        week_date = date.today() + timedelta(days=14)

        # Create blocking absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=week_date,
            end_date=week_date + timedelta(days=7),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        response = client.get(
            "/api/v1/fmit/assignments/check-conflicts",
            params={
                "faculty_id": str(sample_faculty.id),
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["can_assign"] is False
        assert len(data["conflicts"]) > 0
        assert data["conflicts"][0]["conflict_type"] == "leave_overlap"

    def test_check_conflicts_faculty_not_found(
        self,
        client: TestClient,
        fmit_template: RotationTemplate,
    ):
        """Test conflict check with non-existent faculty."""
        week_date = date.today() + timedelta(days=14)

        response = client.get(
            "/api/v1/fmit/assignments/check-conflicts",
            params={
                "faculty_id": str(uuid4()),
                "week_date": week_date.isoformat(),
            },
        )

        assert response.status_code == 404
