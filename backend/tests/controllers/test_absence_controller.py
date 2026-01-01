"""Tests for AbsenceController."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.absence_controller import AbsenceController
from app.models.absence import Absence
from app.schemas.absence import AbsenceCreate, AbsenceUpdate


class TestAbsenceController:
    """Test suite for AbsenceController."""

    # ========================================================================
    # List Absences Tests
    # ========================================================================

    def test_list_absences_no_filters(self, db, sample_resident):
        """Test listing all absences without filters."""
        # Create test absences
        for i in range(5):
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=i),
                end_date=date.today() + timedelta(days=i + 2),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        controller = AbsenceController(db)
        result = controller.list_absences()

        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 100

    def test_list_absences_with_pagination(self, db, sample_resident):
        """Test listing absences with pagination."""
        # Create 10 absences
        for i in range(10):
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=i),
                end_date=date.today() + timedelta(days=i + 1),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        controller = AbsenceController(db)
        result = controller.list_absences(page=1, page_size=5)

        assert result["total"] == 10
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 5

    def test_list_absences_with_person_filter(self, db, sample_residents):
        """Test filtering absences by person_id."""
        person1, person2, person3 = sample_residents

        absence1 = Absence(
            id=uuid4(),
            person_id=person1.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=person2.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            absence_type="sick",
        )
        db.add_all([absence1, absence2])
        db.commit()

        controller = AbsenceController(db)
        result = controller.list_absences(person_id=person1.id)

        assert result["total"] == 1
        assert result["items"][0].person_id == person1.id

    # ========================================================================
    # Get Absence Tests
    # ========================================================================

    def test_get_absence_success(self, db, sample_absence):
        """Test getting a single absence by ID."""
        controller = AbsenceController(db)
        absence = controller.get_absence(sample_absence.id)

        assert absence is not None
        assert absence.id == sample_absence.id
        assert absence.absence_type == sample_absence.absence_type

    def test_get_absence_not_found(self, db):
        """Test getting a non-existent absence raises 404."""
        controller = AbsenceController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_absence(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    # ========================================================================
    # Create Absence Tests
    # ========================================================================

    def test_create_absence_success(self, db, sample_resident):
        """Test creating an absence successfully."""
        controller = AbsenceController(db)

        absence_data = AbsenceCreate(
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
            notes="Annual leave",
        )

        absence = controller.create_absence(absence_data)

        assert absence is not None
        assert absence.person_id == sample_resident.id
        assert absence.absence_type == "vacation"
        assert absence.notes == "Annual leave"

    def test_create_absence_with_all_fields(self, db, sample_resident):
        """Test creating an absence with all optional fields."""
        controller = AbsenceController(db)

        absence_data = AbsenceCreate(
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="deployment",
            replacement_activity="call",
            deployment_orders=True,
            tdy_location="Fort Bragg",
            notes="Military deployment",
        )

        absence = controller.create_absence(absence_data)

        assert absence.replacement_activity == "call"
        assert absence.deployment_orders is True
        assert absence.tdy_location == "Fort Bragg"

    # ========================================================================
    # Update Absence Tests
    # ========================================================================

    def test_update_absence_success(self, db, sample_absence):
        """Test updating an absence successfully."""
        controller = AbsenceController(db)

        update_data = AbsenceUpdate(
            absence_type="conference",
            notes="Medical conference",
        )

        absence = controller.update_absence(sample_absence.id, update_data)

        assert absence.absence_type == "conference"
        assert absence.notes == "Medical conference"

    def test_update_absence_not_found(self, db):
        """Test updating a non-existent absence raises 404."""
        controller = AbsenceController(db)

        update_data = AbsenceUpdate(notes="Updated")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_absence(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    def test_update_absence_partial_fields(self, db, sample_absence):
        """Test updating only some fields preserves others."""
        controller = AbsenceController(db)

        original_type = sample_absence.absence_type
        update_data = AbsenceUpdate(notes="Updated notes only")

        absence = controller.update_absence(sample_absence.id, update_data)

        assert absence.notes == "Updated notes only"
        assert absence.absence_type == original_type

    # ========================================================================
    # Delete Absence Tests
    # ========================================================================

    def test_delete_absence_success(self, db, sample_absence):
        """Test deleting an absence successfully."""
        controller = AbsenceController(db)

        absence_id = sample_absence.id
        controller.delete_absence(absence_id)

        # Verify deletion
        deleted = db.query(Absence).filter(Absence.id == absence_id).first()
        assert deleted is None

    def test_delete_absence_not_found(self, db):
        """Test deleting a non-existent absence raises 404."""
        controller = AbsenceController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_absence(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_list_update_delete_workflow(self, db, sample_resident):
        """Test complete CRUD workflow."""
        controller = AbsenceController(db)

        # Create
        absence_data = AbsenceCreate(
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        created = controller.create_absence(absence_data)
        absence_id = created.id

        # List
        result = controller.list_absences(person_id=sample_resident.id)
        assert result["total"] >= 1

        # Update
        update_data = AbsenceUpdate(absence_type="sick")
        updated = controller.update_absence(absence_id, update_data)
        assert updated.absence_type == "sick"

        # Delete
        controller.delete_absence(absence_id)

        # Verify deletion
        with pytest.raises(HTTPException):
            controller.get_absence(absence_id)
