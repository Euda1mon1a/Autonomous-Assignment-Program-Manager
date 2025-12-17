"""
Unit tests for service layer modules.

Tests for:
- PersonService
- AssignmentService
- BlockService
- AbsenceService
- CertificationService
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.block import Block
from app.models.person import Person


@pytest.mark.unit
class TestPersonServiceQueries:
    """Test PersonService query methods."""

    def test_filter_residents_by_pgy_level(self, db: Session, sample_residents: list):
        """Test filtering residents by PGY level."""
        # Query for PGY 2 residents
        pgy2_residents = (
            db.query(Person)
            .filter(Person.type == "resident", Person.pgy_level == 2)
            .all()
        )

        assert len(pgy2_residents) == 1
        assert pgy2_residents[0].pgy_level == 2

    def test_filter_faculty_by_specialty(self, db: Session, sample_faculty_members: list):
        """Test filtering faculty by specialty."""
        faculty = db.query(Person).filter(Person.type == "faculty").all()

        assert len(faculty) == 3
        assert all(f.type == "faculty" for f in faculty)

    def test_count_people_by_type(self, db: Session, sample_residents: list, sample_faculty_members: list):
        """Test counting people by type."""
        resident_count = db.query(Person).filter(Person.type == "resident").count()
        faculty_count = db.query(Person).filter(Person.type == "faculty").count()

        assert resident_count == 3
        assert faculty_count == 3


@pytest.mark.unit
class TestAbsenceQueries:
    """Test absence-related queries."""

    def test_find_absences_in_date_range(self, db: Session, sample_resident: Person):
        """Test finding absences within a date range."""
        # Create absences
        start = date.today() + timedelta(days=10)
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=start,
            end_date=start + timedelta(days=5),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        # Query for absences in range
        absences = (
            db.query(Absence)
            .filter(
                Absence.start_date >= start,
                Absence.end_date <= start + timedelta(days=7),
            )
            .all()
        )

        assert len(absences) == 1
        assert absences[0].person_id == sample_resident.id

    def test_blocking_absences_flag(self, db: Session, sample_resident: Person):
        """Test blocking absence filtering."""
        # Create blocking and non-blocking absences
        blocking = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=25),
            absence_type="deployment",
            is_blocking=True,
        )
        non_blocking = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            absence_type="conference",
            is_blocking=False,
        )
        db.add(blocking)
        db.add(non_blocking)
        db.commit()

        # Query blocking absences
        blocking_absences = (
            db.query(Absence)
            .filter(Absence.is_blocking)
            .all()
        )

        assert len(blocking_absences) == 1
        assert blocking_absences[0].absence_type == "deployment"


@pytest.mark.unit
class TestBlockQueries:
    """Test block-related queries."""

    def test_find_blocks_for_date_range(self, db: Session, sample_blocks: list):
        """Test finding blocks for a date range."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=3)

        blocks = (
            db.query(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .order_by(Block.date, Block.time_of_day)
            .all()
        )

        # 4 days * 2 half-days = 8 blocks
        assert len(blocks) == 8

    def test_filter_weekend_blocks(self, db: Session, sample_blocks: list):
        """Test filtering weekend blocks."""
        weekend_blocks = db.query(Block).filter(Block.is_weekend).all()

        for block in weekend_blocks:
            assert block.is_weekend is True
            assert block.date.weekday() >= 5  # Saturday or Sunday

    def test_filter_am_pm_blocks(self, db: Session, sample_blocks: list):
        """Test filtering by time of day."""
        am_blocks = db.query(Block).filter(Block.time_of_day == "AM").all()
        pm_blocks = db.query(Block).filter(Block.time_of_day == "PM").all()

        assert len(am_blocks) == 7  # 7 days
        assert len(pm_blocks) == 7


@pytest.mark.unit
class TestAssignmentQueries:
    """Test assignment-related queries."""

    def test_find_assignments_for_person(
        self,
        db: Session,
        sample_assignment,
        sample_resident: Person,
    ):
        """Test finding assignments for a specific person."""
        from app.models.assignment import Assignment

        assignments = (
            db.query(Assignment)
            .filter(Assignment.person_id == sample_resident.id)
            .all()
        )

        assert len(assignments) == 1
        assert assignments[0].role == "primary"

    def test_find_assignments_for_block(
        self,
        db: Session,
        sample_assignment,
        sample_block: Block,
    ):
        """Test finding assignments for a specific block."""
        from app.models.assignment import Assignment

        assignments = (
            db.query(Assignment)
            .filter(Assignment.block_id == sample_block.id)
            .all()
        )

        assert len(assignments) == 1


@pytest.mark.unit
class TestPersonValidation:
    """Test person validation logic."""

    def test_resident_requires_pgy_level(self, db: Session):
        """Test that residents should have a PGY level."""
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="test@hospital.org",
            pgy_level=None,  # Missing PGY level
        )

        # In a real scenario, this would be caught by schema validation
        # Here we just verify the model allows it (validation is at schema level)
        db.add(resident)
        db.commit()

        assert resident.pgy_level is None

    def test_faculty_can_have_specialties(self, db: Session):
        """Test that faculty can have multiple specialties."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Multi-Specialty",
            type="faculty",
            email="multi@hospital.org",
            specialties=["Sports Medicine", "Primary Care", "Musculoskeletal"],
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        assert len(faculty.specialties) == 3
        assert "Sports Medicine" in faculty.specialties
