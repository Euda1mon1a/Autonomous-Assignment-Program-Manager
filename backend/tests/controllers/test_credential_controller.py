"""Tests for CredentialController."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.credential_controller import CredentialController
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.schemas.procedure_credential import CredentialCreate, CredentialUpdate


class TestCredentialController:
    """Test suite for CredentialController."""

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data."""
        # Create faculty member
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)

        # Create another faculty for comparison tests
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Other Faculty",
            type="faculty",
            email="faculty2@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty2)

        # Create procedure
        procedure = Procedure(
            id=uuid4(),
            name="Test Procedure",
            description="A test procedure",
            category="office",
            specialty="General",
            supervision_ratio=2,
            requires_certification=True,
            complexity_level="standard",
            min_pgy_level=1,
            is_active=True,
        )
        db.add(procedure)

        # Create another procedure
        procedure2 = Procedure(
            id=uuid4(),
            name="Other Procedure",
            description="Another procedure",
            category="surgical",
            specialty="Surgery",
            supervision_ratio=1,
            requires_certification=True,
            complexity_level="advanced",
            min_pgy_level=2,
            is_active=True,
        )
        db.add(procedure2)

        db.commit()

        return {
            "faculty": faculty,
            "faculty2": faculty2,
            "procedure": procedure,
            "procedure2": procedure2,
        }

    # ========================================================================
    # Get Credential Tests
    # ========================================================================

    def test_get_credential_success(self, db, setup_data):
        """Test getting a credential by ID."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="qualified",
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.get_credential(credential.id)

        assert result is not None
        assert result.id == credential.id
        assert result.status == "active"

    def test_get_credential_not_found(self, db):
        """Test getting a non-existent credential raises 404."""
        controller = CredentialController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_credential(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    # ========================================================================
    # List Credentials Tests
    # ========================================================================

    def test_list_credentials_for_person(self, db, setup_data):
        """Test listing credentials for a person."""
        # Create multiple credentials
        for proc in [setup_data["procedure"], setup_data["procedure2"]]:
            credential = ProcedureCredential(
                id=uuid4(),
                person_id=setup_data["faculty"].id,
                procedure_id=proc.id,
                status="active",
                competency_level="qualified",
                issued_date=date.today(),
            )
            db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.list_credentials_for_person(setup_data["faculty"].id)

        assert result.total >= 2
        assert len(result.items) >= 2

    def test_list_credentials_for_person_with_status_filter(self, db, setup_data):
        """Test filtering credentials by status."""
        # Create active and suspended credentials
        active = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
        )
        suspended = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure2"].id,
            status="suspended",
        )
        db.add_all([active, suspended])
        db.commit()

        controller = CredentialController(db)
        result = controller.list_credentials_for_person(
            setup_data["faculty"].id, status_filter="active"
        )

        assert all(c.status == "active" for c in result.items)

    def test_list_credentials_for_procedure(self, db, setup_data):
        """Test listing credentials for a procedure."""
        # Create credentials for different faculty
        for fac in [setup_data["faculty"], setup_data["faculty2"]]:
            credential = ProcedureCredential(
                id=uuid4(),
                person_id=fac.id,
                procedure_id=setup_data["procedure"].id,
                status="active",
            )
            db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.list_credentials_for_procedure(setup_data["procedure"].id)

        assert result.total >= 2

    # ========================================================================
    # Create Credential Tests
    # ========================================================================

    def test_create_credential_success(self, db, setup_data):
        """Test creating a credential."""
        controller = CredentialController(db)

        credential_data = CredentialCreate(
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="qualified",
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )

        result = controller.create_credential(credential_data)

        assert result is not None
        assert result.status == "active"
        assert result.competency_level == "qualified"

    def test_create_credential_with_limits(self, db, setup_data):
        """Test creating a credential with supervision limits."""
        controller = CredentialController(db)

        credential_data = CredentialCreate(
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="expert",
            issued_date=date.today(),
            max_concurrent_residents=3,
            max_per_week=10,
            max_per_academic_year=100,
        )

        result = controller.create_credential(credential_data)

        assert result is not None
        assert result.max_concurrent_residents == 3
        assert result.max_per_week == 10

    def test_create_credential_duplicate_fails(self, db, setup_data):
        """Test creating duplicate credential fails."""
        # Create initial credential
        existing = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
        )
        db.add(existing)
        db.commit()

        controller = CredentialController(db)

        credential_data = CredentialCreate(
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,  # Same person and procedure
            status="active",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_credential(credential_data)

        assert exc_info.value.status_code == 400

    # ========================================================================
    # Update Credential Tests
    # ========================================================================

    def test_update_credential_success(self, db, setup_data):
        """Test updating a credential."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="qualified",
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)

        update_data = CredentialUpdate(competency_level="expert")
        result = controller.update_credential(credential.id, update_data)

        assert result.competency_level == "expert"

    def test_update_credential_expiration(self, db, setup_data):
        """Test updating credential expiration date."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            expiration_date=date.today() + timedelta(days=30),
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)

        new_expiration = date.today() + timedelta(days=365)
        update_data = CredentialUpdate(expiration_date=new_expiration)
        result = controller.update_credential(credential.id, update_data)

        assert result.expiration_date == new_expiration

    def test_update_credential_not_found(self, db):
        """Test updating non-existent credential raises 404."""
        controller = CredentialController(db)

        update_data = CredentialUpdate(status="suspended")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_credential(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Delete Credential Tests
    # ========================================================================

    def test_delete_credential_success(self, db, setup_data):
        """Test deleting a credential."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
        )
        db.add(credential)
        db.commit()
        credential_id = credential.id

        controller = CredentialController(db)
        controller.delete_credential(credential_id)

        # Verify deletion
        deleted = (
            db.query(ProcedureCredential)
            .filter(ProcedureCredential.id == credential_id)
            .first()
        )
        assert deleted is None

    def test_delete_credential_not_found(self, db):
        """Test deleting non-existent credential raises 404."""
        controller = CredentialController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_credential(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Suspend/Activate Credential Tests
    # ========================================================================

    def test_suspend_credential_success(self, db, setup_data):
        """Test suspending a credential."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.suspend_credential(
            credential.id, notes="Suspended for review"
        )

        assert result.status == "suspended"

    def test_activate_credential_success(self, db, setup_data):
        """Test activating a suspended credential."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="suspended",
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.activate_credential(credential.id)

        assert result.status == "active"

    def test_verify_credential(self, db, setup_data):
        """Test marking credential as verified."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.verify_credential(credential.id)

        assert result.last_verified_date is not None

    # ========================================================================
    # Expiring Credentials Tests
    # ========================================================================

    def test_list_expiring_credentials(self, db, setup_data):
        """Test listing credentials expiring soon."""
        # Create credential expiring in 15 days
        expiring_soon = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            expiration_date=date.today() + timedelta(days=15),
        )
        # Create credential expiring in 60 days
        expiring_later = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty2"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            expiration_date=date.today() + timedelta(days=60),
        )
        db.add_all([expiring_soon, expiring_later])
        db.commit()

        controller = CredentialController(db)
        result = controller.list_expiring_credentials(days=30)

        # Should include the one expiring in 15 days
        assert result.total >= 1
        assert any(
            c.expiration_date <= date.today() + timedelta(days=30) for c in result.items
        )

    # ========================================================================
    # Qualified Faculty Tests
    # ========================================================================

    def test_get_qualified_faculty(self, db, setup_data):
        """Test getting qualified faculty for a procedure."""
        # Create active credentials for both faculty
        for fac in [setup_data["faculty"], setup_data["faculty2"]]:
            credential = ProcedureCredential(
                id=uuid4(),
                person_id=fac.id,
                procedure_id=setup_data["procedure"].id,
                status="active",
                competency_level="qualified",
            )
            db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.get_qualified_faculty(setup_data["procedure"].id)

        assert result.total >= 2
        assert len(result.qualified_faculty) >= 2

    def test_check_qualification_success(self, db, setup_data):
        """Test checking if faculty is qualified."""
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="qualified",
        )
        db.add(credential)
        db.commit()

        controller = CredentialController(db)
        result = controller.check_qualification(
            setup_data["faculty"].id, setup_data["procedure"].id
        )

        assert result["is_qualified"] is True

    def test_check_qualification_not_qualified(self, db, setup_data):
        """Test checking qualification when not qualified."""
        controller = CredentialController(db)
        result = controller.check_qualification(
            setup_data["faculty"].id, setup_data["procedure"].id
        )

        assert result["is_qualified"] is False

    # ========================================================================
    # Faculty Summary Tests
    # ========================================================================

    def test_get_faculty_summary(self, db, setup_data):
        """Test getting faculty credential summary."""
        # Create multiple credentials
        active = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            expiration_date=date.today() + timedelta(days=15),  # Expiring soon
        )
        expired = ProcedureCredential(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure2"].id,
            status="active",
            expiration_date=date.today() - timedelta(days=1),  # Expired
        )
        db.add_all([active, expired])
        db.commit()

        controller = CredentialController(db)
        result = controller.get_faculty_summary(setup_data["faculty"].id)

        assert result.person_id == setup_data["faculty"].id
        assert result.total_credentials >= 2

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_suspend_activate_workflow(self, db, setup_data):
        """Test complete credential lifecycle."""
        controller = CredentialController(db)

        # Create
        credential_data = CredentialCreate(
            person_id=setup_data["faculty"].id,
            procedure_id=setup_data["procedure"].id,
            status="active",
            competency_level="qualified",
        )
        created = controller.create_credential(credential_data)
        credential_id = created.id

        # Verify qualification
        qual = controller.check_qualification(
            setup_data["faculty"].id, setup_data["procedure"].id
        )
        assert qual["is_qualified"] is True

        # Suspend
        suspended = controller.suspend_credential(credential_id)
        assert suspended.status == "suspended"

        # Check qualification after suspension
        qual = controller.check_qualification(
            setup_data["faculty"].id, setup_data["procedure"].id
        )
        assert qual["is_qualified"] is False

        # Reactivate
        reactivated = controller.activate_credential(credential_id)
        assert reactivated.status == "active"

        # Final qualification check
        qual = controller.check_qualification(
            setup_data["faculty"].id, setup_data["procedure"].id
        )
        assert qual["is_qualified"] is True
