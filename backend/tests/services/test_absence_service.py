"""Tests for AbsenceService."""

from datetime import date, timedelta
from uuid import uuid4

from app.models.absence import Absence
from app.services.absence_service import AbsenceService


class TestAbsenceService:
    """Test suite for AbsenceService."""

    # ========================================================================
    # Get Absence Tests
    # ========================================================================

    def test_get_absence_success(self, db, sample_resident):
        """Test getting an absence by ID successfully."""
        # Create absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.get_absence(absence.id)

        assert result is not None
        assert result.id == absence.id
        assert result.person_id == sample_resident.id
        assert result.absence_type == "vacation"

    def test_get_absence_not_found(self, db):
        """Test getting a non-existent absence returns None."""
        service = AbsenceService(db)
        result = service.get_absence(uuid4())

        assert result is None

    # ========================================================================
    # List Absences Tests
    # ========================================================================

    def test_list_absences_no_filters(self, db, sample_resident):
        """Test listing all absences without filters."""
        # Create multiple absences
        absences = []
        for i in range(3):
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=i),
                end_date=date.today() + timedelta(days=i + 3),
                absence_type="vacation",
            )
            db.add(absence)
            absences.append(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.list_absences()

        assert result["total"] == 3
        assert len(result["items"]) == 3

    def test_list_absences_filter_by_person_id(self, db, sample_residents):
        """Test filtering absences by person_id."""
        person1, person2, person3 = sample_residents

        # Create absences for different people
        absence1 = Absence(
            id=uuid4(),
            person_id=person1.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=person2.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            absence_type="conference",
        )
        db.add_all([absence1, absence2])
        db.commit()

        service = AbsenceService(db)
        result = service.list_absences(person_id=person1.id)

        assert result["total"] == 1
        assert result["items"][0].person_id == person1.id

    def test_list_absences_filter_by_date_range(self, db, sample_resident):
        """Test filtering absences by date range."""
        # Create absences with different dates
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 5),
            absence_type="conference",
        )
        absence3 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 5),
            absence_type="sick",
        )
        db.add_all([absence1, absence2, absence3])
        db.commit()

        service = AbsenceService(db)
        result = service.list_absences(
            start_date=date(2025, 1, 15),
            end_date=date(2025, 2, 15),
        )

        # Should only return absence2
        assert result["total"] == 1
        assert result["items"][0].absence_type == "conference"

    def test_list_absences_filter_by_absence_type(self, db, sample_resident):
        """Test filtering absences by absence_type."""
        # Create absences with different types
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="conference",
        )
        absence3 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=17),
            absence_type="vacation",
        )
        db.add_all([absence1, absence2, absence3])
        db.commit()

        service = AbsenceService(db)
        result = service.list_absences(absence_type="vacation")

        assert result["total"] == 2
        assert all(item.absence_type == "vacation" for item in result["items"])

    def test_list_absences_multiple_filters(self, db, sample_residents):
        """Test combining multiple filters."""
        person1, person2, person3 = sample_residents

        # Create multiple absences
        absence1 = Absence(
            id=uuid4(),
            person_id=person1.id,
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 15),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=person1.id,
            start_date=date(2025, 2, 10),
            end_date=date(2025, 2, 15),
            absence_type="conference",
        )
        absence3 = Absence(
            id=uuid4(),
            person_id=person2.id,
            start_date=date(2025, 2, 10),
            end_date=date(2025, 2, 15),
            absence_type="vacation",
        )
        db.add_all([absence1, absence2, absence3])
        db.commit()

        service = AbsenceService(db)
        result = service.list_absences(
            person_id=person1.id,
            absence_type="vacation",
        )

        assert result["total"] == 1
        assert result["items"][0].id == absence1.id

    def test_list_absences_empty_result(self, db):
        """Test listing absences when none exist."""
        service = AbsenceService(db)
        result = service.list_absences()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    # ========================================================================
    # Create Absence Tests
    # ========================================================================

    def test_create_absence_success_minimal_data(self, db, sample_resident):
        """Test creating an absence with minimal required fields."""
        service = AbsenceService(db)
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=10)

        result = service.create_absence(
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
        )

        assert result["error"] is None
        assert result["absence"] is not None
        assert result["absence"].person_id == sample_resident.id
        assert result["absence"].start_date == start
        assert result["absence"].end_date == end
        assert result["absence"].absence_type == "vacation"
        assert result["absence"].id is not None

    def test_create_absence_success_with_all_fields(self, db, sample_resident):
        """Test creating an absence with all optional fields."""
        service = AbsenceService(db)
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=10)

        result = service.create_absence(
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="deployment",
            replacement_activity="call",
            deployment_orders=True,
            tdy_location="Fort Bragg",
            notes="Military deployment",
        )

        assert result["error"] is None
        absence = result["absence"]
        assert absence is not None
        assert absence.replacement_activity == "call"
        assert absence.deployment_orders is True
        assert absence.tdy_location == "Fort Bragg"
        assert absence.notes == "Military deployment"

    def test_create_absence_persists_to_database(self, db, sample_resident):
        """Test that created absence is persisted to database."""
        service = AbsenceService(db)
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=10)

        result = service.create_absence(
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="conference",
        )

        absence_id = result["absence"].id

        # Query directly from database
        db_absence = db.query(Absence).filter(Absence.id == absence_id).first()
        assert db_absence is not None
        assert db_absence.absence_type == "conference"

    # ========================================================================
    # Update Absence Tests
    # ========================================================================

    def test_update_absence_success(self, db, sample_resident):
        """Test updating an absence successfully."""
        # Create absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.update_absence(
            absence.id,
            {"absence_type": "conference", "notes": "Updated notes"},
        )

        assert result["error"] is None
        assert result["absence"].absence_type == "conference"
        assert result["absence"].notes == "Updated notes"

    def test_update_absence_not_found(self, db):
        """Test updating a non-existent absence returns error."""
        service = AbsenceService(db)
        result = service.update_absence(
            uuid4(),
            {"absence_type": "conference"},
        )

        assert result["error"] == "Absence not found"
        assert result["absence"] is None

    def test_update_absence_partial_fields(self, db, sample_resident):
        """Test updating only some fields preserves others."""
        # Create absence with multiple fields
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
            notes="Original notes",
            tdy_location="Location A",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.update_absence(
            absence.id,
            {"notes": "Updated notes"},
        )

        assert result["absence"].notes == "Updated notes"
        assert result["absence"].absence_type == "vacation"
        assert result["absence"].tdy_location == "Location A"

    def test_update_absence_dates(self, db, sample_resident):
        """Test updating absence dates."""
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        new_start = date.today() + timedelta(days=14)
        new_end = date.today() + timedelta(days=21)

        result = service.update_absence(
            absence.id,
            {"start_date": new_start, "end_date": new_end},
        )

        assert result["absence"].start_date == new_start
        assert result["absence"].end_date == new_end

    # ========================================================================
    # Delete Absence Tests
    # ========================================================================

    def test_delete_absence_success(self, db, sample_resident):
        """Test deleting an absence successfully."""
        # Create absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        absence_id = absence.id

        service = AbsenceService(db)
        result = service.delete_absence(absence_id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deletion
        db_absence = db.query(Absence).filter(Absence.id == absence_id).first()
        assert db_absence is None

    def test_delete_absence_not_found(self, db):
        """Test deleting a non-existent absence returns error."""
        service = AbsenceService(db)
        result = service.delete_absence(uuid4())

        assert result["success"] is False
        assert result["error"] == "Absence not found"

    # ========================================================================
    # Is Person Absent Tests
    # ========================================================================

    def test_is_person_absent_true(self, db, sample_resident):
        """Test checking if person is absent on a specific date - returns True."""
        # Create absence spanning multiple days
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=10)
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        check_date = date.today() + timedelta(days=7)  # Middle of absence
        result = service.is_person_absent(sample_resident.id, check_date)

        assert result is True

    def test_is_person_absent_false_no_absence(self, db, sample_resident):
        """Test checking if person is absent when they have no absences."""
        service = AbsenceService(db)
        result = service.is_person_absent(sample_resident.id, date.today())

        assert result is False

    def test_is_person_absent_false_outside_range(self, db, sample_resident):
        """Test checking if person is absent on date outside absence range."""
        # Create absence
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=15)
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        check_date = date.today() + timedelta(days=5)  # Before absence
        result = service.is_person_absent(sample_resident.id, check_date)

        assert result is False

    def test_is_person_absent_on_start_date(self, db, sample_resident):
        """Test checking if person is absent on the start date of absence."""
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=10)
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.is_person_absent(sample_resident.id, start)

        assert result is True

    def test_is_person_absent_on_end_date(self, db, sample_resident):
        """Test checking if person is absent on the end date of absence."""
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=10)
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=start,
            end_date=end,
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        service = AbsenceService(db)
        result = service.is_person_absent(sample_resident.id, end)

        assert result is True

    def test_is_person_absent_multiple_absences(self, db, sample_resident):
        """Test checking absence when person has multiple absences."""
        # Create multiple non-overlapping absences
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 5),
            absence_type="conference",
        )
        db.add_all([absence1, absence2])
        db.commit()

        service = AbsenceService(db)

        # Check date in first absence
        assert service.is_person_absent(sample_resident.id, date(2025, 1, 3)) is True

        # Check date in second absence
        assert service.is_person_absent(sample_resident.id, date(2025, 2, 3)) is True

        # Check date between absences
        assert service.is_person_absent(sample_resident.id, date(2025, 1, 15)) is False
