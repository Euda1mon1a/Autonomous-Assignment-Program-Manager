"""Tests for absence service."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.person import Person
from app.services.absence_service import AbsenceService


@pytest.fixture
def absence_service(db: Session) -> AbsenceService:
    """Create absence service fixture."""
    return AbsenceService(db)


@pytest.fixture
def test_person(db: Session) -> Person:
    """Create a test person."""
    person = Person(
        id=uuid4(),
        name="John Doe",
        email="john.doe@example.com",
        type="resident",
        pgy_level=1,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


class TestAbsenceService:
    """Test cases for AbsenceService."""

    def test_create_absence_success(
        self, absence_service: AbsenceService, test_person: Person
    ) -> None:
        """Test successful absence creation."""
        start = date.today()
        end = start + timedelta(days=7)

        result = absence_service.create_absence(
            person_id=test_person.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
            notes="Vacation time",
        )

        assert result["error"] is None
        assert "absence" in result
        assert result["absence"].person_id == test_person.id
        assert result["absence"].start_date == start
        assert result["absence"].end_date == end
        assert result["absence"].absence_type == "vacation"

    def test_create_absence_invalid_dates(
        self, absence_service: AbsenceService, test_person: Person
    ) -> None:
        """Test absence creation with end date before start date."""
        from sqlalchemy.exc import IntegrityError

        start = date.today()
        end = start - timedelta(days=1)  # End before start

        # Database constraint should catch this
        with pytest.raises(IntegrityError) as exc_info:
            absence_service.create_absence(
                person_id=test_person.id,
                start_date=start,
                end_date=end,
                absence_type="vacation",
            )

        assert "check_absence_dates" in str(exc_info.value)

    def test_get_absence_found(
        self, absence_service: AbsenceService, test_person: Person, db: Session
    ) -> None:
        """Test retrieving an existing absence."""
        # Create absence directly in DB
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            absence_type="tdy",
        )
        db.add(absence)
        db.commit()

        # Retrieve it
        retrieved = absence_service.get_absence(absence.id)

        assert retrieved is not None
        assert retrieved.id == absence.id
        assert retrieved.person_id == test_person.id
        assert retrieved.absence_type == "tdy"

    def test_get_absence_not_found(self, absence_service: AbsenceService) -> None:
        """Test retrieving a non-existent absence."""
        fake_id = uuid4()
        retrieved = absence_service.get_absence(fake_id)

        assert retrieved is None

    def test_list_absences_empty(self, absence_service: AbsenceService) -> None:
        """Test listing absences when none exist."""
        result = absence_service.list_absences()

        assert result["items"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 100

    def test_list_absences_with_filters(
        self, absence_service: AbsenceService, test_person: Person, db: Session
    ) -> None:
        """Test listing absences with person_id filter."""
        # Create two absences for the test person
        absence1 = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="tdy",
        )
        db.add_all([absence1, absence2])
        db.commit()

        # List with person filter
        result = absence_service.list_absences(person_id=test_person.id)

        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_delete_absence_success(
        self, absence_service: AbsenceService, test_person: Person, db: Session
    ) -> None:
        """Test successful absence deletion."""
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        # Delete it
        result = absence_service.delete_absence(absence.id)

        assert result["success"] is True
        # Verify it's gone
        assert absence_service.get_absence(absence.id) is None

    def test_delete_absence_not_found(self, absence_service: AbsenceService) -> None:
        """Test deletion of non-existent absence."""
        fake_id = uuid4()
        result = absence_service.delete_absence(fake_id)

        assert result["success"] is False
        assert "error" in result or "not found" in result.get("message", "").lower()
