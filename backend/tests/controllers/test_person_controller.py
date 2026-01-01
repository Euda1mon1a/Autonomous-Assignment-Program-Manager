"""Tests for PersonController."""

import pytest
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.person_controller import PersonController
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate


class TestPersonController:
    """Test suite for PersonController."""

    # ========================================================================
    # List People Tests
    # ========================================================================

    def test_list_people_no_filters(self, db):
        """Test listing all people without filters."""
        # Create test people
        for i in range(3):
            person = Person(
                id=uuid4(),
                name=f"Dr. Test {i}",
                type="resident" if i % 2 == 0 else "faculty",
                email=f"test{i}@hospital.org",
                pgy_level=1 if i % 2 == 0 else None,
            )
            db.add(person)
        db.commit()

        controller = PersonController(db)
        result = controller.list_people()

        assert result.total >= 3
        assert len(result.items) >= 3

    def test_list_people_filter_by_type(self, db):
        """Test listing people filtered by type."""
        # Create residents and faculty
        for i in range(5):
            person = Person(
                id=uuid4(),
                name=f"Dr. Person {i}",
                type="resident" if i < 3 else "faculty",
                email=f"person{i}@hospital.org",
                pgy_level=1 if i < 3 else None,
            )
            db.add(person)
        db.commit()

        controller = PersonController(db)

        # Filter by resident
        residents = controller.list_people(type="resident")
        assert residents.total >= 3
        assert all(p.type == "resident" for p in residents.items)

        # Filter by faculty
        faculty = controller.list_people(type="faculty")
        assert faculty.total >= 2
        assert all(p.type == "faculty" for p in faculty.items)

    def test_list_people_filter_by_pgy_level(self, db):
        """Test listing people filtered by PGY level."""
        # Create residents with different PGY levels
        for pgy in [1, 1, 2, 2, 3]:
            person = Person(
                id=uuid4(),
                name=f"Dr. PGY{pgy}",
                type="resident",
                email=f"pgy{pgy}_{uuid4().hex[:6]}@hospital.org",
                pgy_level=pgy,
            )
            db.add(person)
        db.commit()

        controller = PersonController(db)
        result = controller.list_people(pgy_level=2)

        assert result.total >= 2
        assert all(p.pgy_level == 2 for p in result.items)

    # ========================================================================
    # List Residents Tests
    # ========================================================================

    def test_list_residents_returns_only_residents(self, db):
        """Test that list_residents only returns residents."""
        # Create mixed types
        resident = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=2,
        )
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
        )
        db.add_all([resident, faculty])
        db.commit()

        controller = PersonController(db)
        result = controller.list_residents()

        assert result.total >= 1
        assert all(p.type == "resident" for p in result.items)

    def test_list_residents_filter_by_pgy(self, db):
        """Test filtering residents by PGY level."""
        for pgy in [1, 2, 3]:
            person = Person(
                id=uuid4(),
                name=f"Resident PGY{pgy}",
                type="resident",
                email=f"res_pgy{pgy}@hospital.org",
                pgy_level=pgy,
            )
            db.add(person)
        db.commit()

        controller = PersonController(db)
        result = controller.list_residents(pgy_level=1)

        assert result.total >= 1
        assert all(p.pgy_level == 1 for p in result.items)

    # ========================================================================
    # List Faculty Tests
    # ========================================================================

    def test_list_faculty_returns_only_faculty(self, db):
        """Test that list_faculty only returns faculty."""
        resident = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident2@hospital.org",
            pgy_level=1,
        )
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty2@hospital.org",
        )
        db.add_all([resident, faculty])
        db.commit()

        controller = PersonController(db)
        result = controller.list_faculty()

        assert result.total >= 1
        assert all(p.type == "faculty" for p in result.items)

    # ========================================================================
    # Get Person Tests
    # ========================================================================

    def test_get_person_success(self, db):
        """Test getting a person by ID."""
        person = Person(
            id=uuid4(),
            name="Dr. Test",
            type="resident",
            email="test@hospital.org",
            pgy_level=2,
        )
        db.add(person)
        db.commit()

        controller = PersonController(db)
        result = controller.get_person(person.id)

        assert result is not None
        assert result.id == person.id
        assert result.name == "Dr. Test"
        assert result.type == "resident"

    def test_get_person_not_found(self, db):
        """Test getting a non-existent person raises 404."""
        controller = PersonController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    # ========================================================================
    # Create Person Tests
    # ========================================================================

    def test_create_person_resident(self, db):
        """Test creating a resident."""
        controller = PersonController(db)

        person_data = PersonCreate(
            name="Dr. New Resident",
            type="resident",
            email="newresident@hospital.org",
            pgy_level=1,
        )

        result = controller.create_person(person_data)

        assert result is not None
        assert result.name == "Dr. New Resident"
        assert result.type == "resident"
        assert result.pgy_level == 1

    def test_create_person_faculty(self, db):
        """Test creating a faculty member."""
        controller = PersonController(db)

        person_data = PersonCreate(
            name="Dr. New Faculty",
            type="faculty",
            email="newfaculty@hospital.org",
            performs_procedures=True,
        )

        result = controller.create_person(person_data)

        assert result is not None
        assert result.name == "Dr. New Faculty"
        assert result.type == "faculty"

    def test_create_person_duplicate_email(self, db):
        """Test creating person with duplicate email fails."""
        # Create existing person
        existing = Person(
            id=uuid4(),
            name="Dr. Existing",
            type="resident",
            email="duplicate@hospital.org",
            pgy_level=1,
        )
        db.add(existing)
        db.commit()

        controller = PersonController(db)

        person_data = PersonCreate(
            name="Dr. New Person",
            type="resident",
            email="duplicate@hospital.org",  # Same email
            pgy_level=2,
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_person(person_data)

        assert exc_info.value.status_code == 400

    # ========================================================================
    # Update Person Tests
    # ========================================================================

    def test_update_person_success(self, db):
        """Test updating a person."""
        person = Person(
            id=uuid4(),
            name="Dr. Original",
            type="resident",
            email="original@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()

        controller = PersonController(db)

        update_data = PersonUpdate(name="Dr. Updated")
        result = controller.update_person(person.id, update_data)

        assert result.name == "Dr. Updated"
        assert result.type == "resident"  # Unchanged

    def test_update_person_pgy_level(self, db):
        """Test updating PGY level."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident3@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()

        controller = PersonController(db)

        update_data = PersonUpdate(pgy_level=2)
        result = controller.update_person(person.id, update_data)

        assert result.pgy_level == 2

    def test_update_person_not_found(self, db):
        """Test updating non-existent person raises 404."""
        controller = PersonController(db)

        update_data = PersonUpdate(name="New Name")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_person(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Delete Person Tests
    # ========================================================================

    def test_delete_person_success(self, db):
        """Test deleting a person."""
        person = Person(
            id=uuid4(),
            name="Dr. ToDelete",
            type="resident",
            email="todelete@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        person_id = person.id

        controller = PersonController(db)
        controller.delete_person(person_id)

        # Verify deletion
        deleted = db.query(Person).filter(Person.id == person_id).first()
        assert deleted is None

    def test_delete_person_not_found(self, db):
        """Test deleting non-existent person raises 404."""
        controller = PersonController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_person(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_get_update_delete_workflow(self, db):
        """Test complete CRUD workflow for a person."""
        controller = PersonController(db)

        # Create
        person_data = PersonCreate(
            name="Dr. Workflow",
            type="resident",
            email="workflow@hospital.org",
            pgy_level=1,
        )
        created = controller.create_person(person_data)
        person_id = created.id

        # Get
        retrieved = controller.get_person(person_id)
        assert retrieved.name == "Dr. Workflow"

        # Update
        update_data = PersonUpdate(name="Dr. Updated Workflow", pgy_level=2)
        updated = controller.update_person(person_id, update_data)
        assert updated.name == "Dr. Updated Workflow"
        assert updated.pgy_level == 2

        # Delete
        controller.delete_person(person_id)

        # Verify deletion
        with pytest.raises(HTTPException):
            controller.get_person(person_id)

    def test_list_after_create(self, db):
        """Test that newly created person appears in list."""
        controller = PersonController(db)

        # Get initial count
        initial = controller.list_people()
        initial_count = initial.total

        # Create a new person
        person_data = PersonCreate(
            name="Dr. New",
            type="resident",
            email="new@hospital.org",
            pgy_level=1,
        )
        controller.create_person(person_data)

        # Get new count
        after = controller.list_people()
        assert after.total == initial_count + 1
