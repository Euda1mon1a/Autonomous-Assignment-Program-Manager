"""Tests for PersonService."""

import pytest
from uuid import uuid4

from app.services.person_service import PersonService
from app.models.person import Person


class TestPersonService:
    """Test suite for PersonService."""

    # ========================================================================
    # Get Person Tests
    # ========================================================================

    def test_get_person_success(self, db, sample_resident):
        """Test getting a person by ID successfully."""
        service = PersonService(db)
        result = service.get_person(sample_resident.id)

        assert result is not None
        assert result.id == sample_resident.id
        assert result.name == sample_resident.name
        assert result.type == "resident"

    def test_get_person_not_found(self, db):
        """Test getting a non-existent person returns None."""
        service = PersonService(db)
        result = service.get_person(uuid4())

        assert result is None

    # ========================================================================
    # List People Tests
    # ========================================================================

    def test_list_people_no_filters(self, db, sample_residents, sample_faculty_members):
        """Test listing all people without filters."""
        service = PersonService(db)
        result = service.list_people()

        # Should return all residents and faculty
        assert result["total"] == 6  # 3 residents + 3 faculty
        assert len(result["items"]) == 6

    def test_list_people_filter_by_type_resident(self, db, sample_residents, sample_faculty_members):
        """Test filtering people by type (resident)."""
        service = PersonService(db)
        result = service.list_people(type="resident")

        assert result["total"] == 3
        assert all(person.type == "resident" for person in result["items"])

    def test_list_people_filter_by_type_faculty(self, db, sample_residents, sample_faculty_members):
        """Test filtering people by type (faculty)."""
        service = PersonService(db)
        result = service.list_people(type="faculty")

        assert result["total"] == 3
        assert all(person.type == "faculty" for person in result["items"])

    def test_list_people_filter_by_pgy_level(self, db, sample_residents):
        """Test filtering people by PGY level."""
        service = PersonService(db)
        result = service.list_people(pgy_level=2)

        assert result["total"] == 1
        assert result["items"][0].pgy_level == 2

    def test_list_people_filter_by_type_and_pgy(self, db):
        """Test filtering people by both type and PGY level."""
        # Create residents with specific PGY levels
        resident1 = Person(
            id=uuid4(),
            name="PGY1 Resident",
            type="resident",
            pgy_level=1,
        )
        resident2 = Person(
            id=uuid4(),
            name="PGY2 Resident",
            type="resident",
            pgy_level=2,
        )
        faculty = Person(
            id=uuid4(),
            name="Faculty Member",
            type="faculty",
        )
        db.add_all([resident1, resident2, faculty])
        db.commit()

        service = PersonService(db)
        result = service.list_people(type="resident", pgy_level=1)

        assert result["total"] == 1
        assert result["items"][0].name == "PGY1 Resident"

    def test_list_people_empty_result(self, db):
        """Test listing people when none exist."""
        service = PersonService(db)
        result = service.list_people()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    # ========================================================================
    # List Residents Tests
    # ========================================================================

    def test_list_residents_all(self, db, sample_residents, sample_faculty_members):
        """Test listing all residents without PGY filter."""
        service = PersonService(db)
        result = service.list_residents()

        assert result["total"] == 3
        assert all(person.type == "resident" for person in result["items"])

    def test_list_residents_filter_by_pgy_level(self, db, sample_residents):
        """Test listing residents filtered by PGY level."""
        service = PersonService(db)
        result = service.list_residents(pgy_level=3)

        assert result["total"] == 1
        assert result["items"][0].pgy_level == 3

    def test_list_residents_empty_when_no_residents(self, db, sample_faculty_members):
        """Test listing residents when only faculty exist."""
        service = PersonService(db)
        result = service.list_residents()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_residents_excludes_faculty(self, db, sample_residents, sample_faculty_members):
        """Test that list_residents only returns residents, not faculty."""
        service = PersonService(db)
        result = service.list_residents()

        assert result["total"] == 3
        person_ids = {person.id for person in result["items"]}
        for faculty in sample_faculty_members:
            assert faculty.id not in person_ids

    # ========================================================================
    # List Faculty Tests
    # ========================================================================

    def test_list_faculty_all(self, db, sample_residents, sample_faculty_members):
        """Test listing all faculty without specialty filter."""
        service = PersonService(db)
        result = service.list_faculty()

        assert result["total"] == 3
        assert all(person.type == "faculty" for person in result["items"])

    def test_list_faculty_filter_by_specialty(self, db):
        """Test listing faculty filtered by specialty."""
        # Create faculty with specific specialties
        faculty1 = Person(
            id=uuid4(),
            name="Sports Med Faculty",
            type="faculty",
            specialties=["Sports Medicine"],
        )
        faculty2 = Person(
            id=uuid4(),
            name="Primary Care Faculty",
            type="faculty",
            specialties=["Primary Care"],
        )
        faculty3 = Person(
            id=uuid4(),
            name="Multi-specialty Faculty",
            type="faculty",
            specialties=["Sports Medicine", "Primary Care"],
        )
        db.add_all([faculty1, faculty2, faculty3])
        db.commit()

        service = PersonService(db)
        result = service.list_faculty(specialty="Sports Medicine")

        assert result["total"] == 2
        # Should return faculty1 and faculty3
        names = {person.name for person in result["items"]}
        assert "Sports Med Faculty" in names
        assert "Multi-specialty Faculty" in names

    def test_list_faculty_empty_when_no_faculty(self, db, sample_residents):
        """Test listing faculty when only residents exist."""
        service = PersonService(db)
        result = service.list_faculty()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_faculty_excludes_residents(self, db, sample_residents, sample_faculty_members):
        """Test that list_faculty only returns faculty, not residents."""
        service = PersonService(db)
        result = service.list_faculty()

        assert result["total"] == 3
        person_ids = {person.id for person in result["items"]}
        for resident in sample_residents:
            assert resident.id not in person_ids

    # ========================================================================
    # Create Person Tests (Resident)
    # ========================================================================

    def test_create_resident_success_minimal_data(self, db):
        """Test creating a resident with minimal required fields."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. New Resident",
            type="resident",
            pgy_level=1,
        )

        assert result["error"] is None
        person = result["person"]
        assert person is not None
        assert person.name == "Dr. New Resident"
        assert person.type == "resident"
        assert person.pgy_level == 1
        assert person.id is not None

    def test_create_resident_with_all_fields(self, db):
        """Test creating a resident with all optional fields."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Full Data Resident",
            type="resident",
            email="full.resident@hospital.org",
            pgy_level=2,
            target_clinical_blocks=48,
        )

        person = result["person"]
        assert person.name == "Dr. Full Data Resident"
        assert person.email == "full.resident@hospital.org"
        assert person.pgy_level == 2
        assert person.target_clinical_blocks == 48

    def test_create_resident_missing_pgy_level_error(self, db):
        """Test creating a resident without PGY level returns error."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Missing PGY",
            type="resident",
        )

        assert result["error"] == "PGY level required for residents"
        assert result["person"] is None

    def test_create_resident_persists_to_database(self, db):
        """Test that created resident is persisted to database."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Persistent",
            type="resident",
            pgy_level=3,
        )

        person_id = result["person"].id

        # Query directly from database
        db_person = db.query(Person).filter(Person.id == person_id).first()
        assert db_person is not None
        assert db_person.name == "Dr. Persistent"

    # ========================================================================
    # Create Person Tests (Faculty)
    # ========================================================================

    def test_create_faculty_success_minimal_data(self, db):
        """Test creating faculty with minimal required fields."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. New Faculty",
            type="faculty",
        )

        assert result["error"] is None
        person = result["person"]
        assert person is not None
        assert person.name == "Dr. New Faculty"
        assert person.type == "faculty"
        assert person.pgy_level is None

    def test_create_faculty_with_specialties(self, db):
        """Test creating faculty with specialties."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Specialist",
            type="faculty",
            specialties=["Sports Medicine", "Primary Care"],
            performs_procedures=True,
        )

        person = result["person"]
        assert person.specialties == ["Sports Medicine", "Primary Care"]
        assert person.performs_procedures is True

    def test_create_faculty_with_all_fields(self, db):
        """Test creating faculty with all optional fields."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Complete Faculty",
            type="faculty",
            email="complete.faculty@hospital.org",
            specialties=["Sports Medicine"],
            performs_procedures=True,
        )

        person = result["person"]
        assert person.name == "Dr. Complete Faculty"
        assert person.email == "complete.faculty@hospital.org"
        assert person.specialties == ["Sports Medicine"]
        assert person.performs_procedures is True

    # ========================================================================
    # Update Person Tests
    # ========================================================================

    def test_update_person_success(self, db, sample_resident):
        """Test updating a person successfully."""
        service = PersonService(db)
        result = service.update_person(
            sample_resident.id,
            {"name": "Dr. Updated Name", "email": "updated@hospital.org"},
        )

        assert result["error"] is None
        person = result["person"]
        assert person.name == "Dr. Updated Name"
        assert person.email == "updated@hospital.org"

    def test_update_person_not_found(self, db):
        """Test updating a non-existent person returns error."""
        service = PersonService(db)
        result = service.update_person(
            uuid4(),
            {"name": "Does Not Exist"},
        )

        assert result["error"] == "Person not found"
        assert result["person"] is None

    def test_update_person_partial_fields(self, db, sample_resident):
        """Test updating only some fields preserves others."""
        original_name = sample_resident.name
        original_pgy = sample_resident.pgy_level

        service = PersonService(db)
        result = service.update_person(
            sample_resident.id,
            {"email": "new.email@hospital.org"},
        )

        person = result["person"]
        assert person.email == "new.email@hospital.org"
        assert person.name == original_name
        assert person.pgy_level == original_pgy

    def test_update_resident_pgy_level(self, db, sample_resident):
        """Test updating a resident's PGY level."""
        service = PersonService(db)
        result = service.update_person(
            sample_resident.id,
            {"pgy_level": 3},
        )

        assert result["person"].pgy_level == 3

    def test_update_faculty_specialties(self, db, sample_faculty):
        """Test updating faculty specialties."""
        service = PersonService(db)
        new_specialties = ["Primary Care", "Urgent Care"]
        result = service.update_person(
            sample_faculty.id,
            {"specialties": new_specialties},
        )

        assert result["person"].specialties == new_specialties

    def test_update_person_multiple_fields(self, db, sample_resident):
        """Test updating multiple fields at once."""
        service = PersonService(db)
        result = service.update_person(
            sample_resident.id,
            {
                "name": "Dr. Multi Update",
                "email": "multi@hospital.org",
                "pgy_level": 3,
                "target_clinical_blocks": 52,
            },
        )

        person = result["person"]
        assert person.name == "Dr. Multi Update"
        assert person.email == "multi@hospital.org"
        assert person.pgy_level == 3
        assert person.target_clinical_blocks == 52

    # ========================================================================
    # Delete Person Tests
    # ========================================================================

    def test_delete_person_success(self, db, sample_resident):
        """Test deleting a person successfully."""
        person_id = sample_resident.id

        service = PersonService(db)
        result = service.delete_person(person_id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deletion
        db_person = db.query(Person).filter(Person.id == person_id).first()
        assert db_person is None

    def test_delete_person_not_found(self, db):
        """Test deleting a non-existent person returns error."""
        service = PersonService(db)
        result = service.delete_person(uuid4())

        assert result["success"] is False
        assert result["error"] == "Person not found"

    def test_delete_resident(self, db, sample_resident):
        """Test deleting a resident."""
        person_id = sample_resident.id

        service = PersonService(db)
        result = service.delete_person(person_id)

        assert result["success"] is True

        # Verify it's gone
        db_person = db.query(Person).filter(Person.id == person_id).first()
        assert db_person is None

    def test_delete_faculty(self, db, sample_faculty):
        """Test deleting a faculty member."""
        person_id = sample_faculty.id

        service = PersonService(db)
        result = service.delete_person(person_id)

        assert result["success"] is True

        # Verify it's gone
        db_person = db.query(Person).filter(Person.id == person_id).first()
        assert db_person is None

    # ========================================================================
    # Edge Cases and Business Logic Tests
    # ========================================================================

    def test_create_person_with_empty_specialties_list(self, db):
        """Test creating faculty with empty specialties list."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. No Specialties",
            type="faculty",
            specialties=[],
        )

        person = result["person"]
        assert person.specialties == []

    def test_list_people_mixed_pgy_levels(self, db):
        """Test listing people with mixed PGY levels."""
        # Create residents with different PGY levels
        for pgy in [1, 1, 2, 2, 3]:
            person = Person(
                id=uuid4(),
                name=f"Dr. PGY{pgy} Resident",
                type="resident",
                pgy_level=pgy,
            )
            db.add(person)
        db.commit()

        service = PersonService(db)

        # Test PGY 1
        result = service.list_people(pgy_level=1)
        assert result["total"] == 2

        # Test PGY 2
        result = service.list_people(pgy_level=2)
        assert result["total"] == 2

        # Test PGY 3
        result = service.list_people(pgy_level=3)
        assert result["total"] == 1

    def test_faculty_can_have_pgy_level_none(self, db):
        """Test that faculty can be created without PGY level (should be None)."""
        service = PersonService(db)
        result = service.create_person(
            name="Dr. Faculty No PGY",
            type="faculty",
        )

        assert result["person"].pgy_level is None

    def test_update_changes_persist_across_queries(self, db, sample_resident):
        """Test that updates persist when querying the database again."""
        service = PersonService(db)

        # Update the person
        service.update_person(
            sample_resident.id,
            {"name": "Dr. Persistent Update"},
        )

        # Query again with fresh service
        fresh_service = PersonService(db)
        result = fresh_service.get_person(sample_resident.id)

        assert result.name == "Dr. Persistent Update"
