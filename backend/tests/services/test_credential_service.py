"""Tests for CredentialService."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.services.credential_service import CredentialService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_procedure(db) -> Procedure:
    """Create a sample procedure."""
    procedure = Procedure(
        id=uuid4(),
        name="Botox Injection",
        description="Botulinum toxin injection for cosmetic or therapeutic purposes",
        category="office",
        specialty="Sports Medicine",
        supervision_ratio=2,
        requires_certification=True,
        complexity_level="standard",
        min_pgy_level=2,
        is_active=True,
    )
    db.add(procedure)
    db.commit()
    db.refresh(procedure)
    return procedure


@pytest.fixture
def sample_procedures(db) -> list[Procedure]:
    """Create multiple sample procedures."""
    procedures = [
        Procedure(
            id=uuid4(),
            name="IUD Placement",
            category="office",
            specialty="Women's Health",
            supervision_ratio=1,
        ),
        Procedure(
            id=uuid4(),
            name="Joint Injection",
            category="office",
            specialty="Sports Medicine",
            supervision_ratio=2,
        ),
        Procedure(
            id=uuid4(),
            name="Vasectomy",
            category="surgical",
            specialty="Urology",
            supervision_ratio=1,
        ),
    ]
    db.add_all(procedures)
    db.commit()
    for p in procedures:
        db.refresh(p)
    return procedures


@pytest.fixture
def sample_credential(db, sample_faculty, sample_procedure) -> ProcedureCredential:
    """Create a sample active credential."""
    credential = ProcedureCredential(
        id=uuid4(),
        person_id=sample_faculty.id,
        procedure_id=sample_procedure.id,
        status="active",
        competency_level="qualified",
        issued_date=date.today() - timedelta(days=365),
        expiration_date=date.today() + timedelta(days=365),
        max_concurrent_residents=2,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


@pytest.fixture
def expired_credential(db, sample_faculty, sample_procedure) -> ProcedureCredential:
    """Create an expired credential."""
    # Create a different procedure for expired credential
    expired_proc = Procedure(
        id=uuid4(),
        name="Expired Procedure",
        category="office",
        specialty="General",
    )
    db.add(expired_proc)
    db.commit()

    credential = ProcedureCredential(
        id=uuid4(),
        person_id=sample_faculty.id,
        procedure_id=expired_proc.id,
        status="active",
        competency_level="qualified",
        issued_date=date.today() - timedelta(days=730),
        expiration_date=date.today() - timedelta(days=30),  # Expired 30 days ago
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


# ============================================================================
# Get Credential Tests
# ============================================================================


class TestGetCredential:
    """Test suite for get_credential method."""

    def test_get_credential_success(self, db, sample_credential):
        """Test getting a credential by ID successfully."""
        service = CredentialService(db)
        result = service.get_credential(sample_credential.id)

        assert result is not None
        assert result.id == sample_credential.id
        assert result.status == "active"

    def test_get_credential_not_found(self, db):
        """Test getting a non-existent credential returns None."""
        service = CredentialService(db)
        result = service.get_credential(uuid4())

        assert result is None


class TestGetCredentialForPersonProcedure:
    """Test suite for get_credential_for_person_procedure method."""

    def test_get_credential_for_person_procedure_success(
        self, db, sample_faculty, sample_procedure, sample_credential
    ):
        """Test getting a credential by person and procedure IDs."""
        service = CredentialService(db)
        result = service.get_credential_for_person_procedure(
            sample_faculty.id, sample_procedure.id
        )

        assert result is not None
        assert result.id == sample_credential.id
        assert result.person_id == sample_faculty.id
        assert result.procedure_id == sample_procedure.id

    def test_get_credential_for_person_procedure_not_found(
        self, db, sample_faculty, sample_procedure
    ):
        """Test getting credential when none exists."""
        service = CredentialService(db)
        result = service.get_credential_for_person_procedure(
            sample_faculty.id, sample_procedure.id
        )

        assert result is None


# ============================================================================
# List Credentials Tests
# ============================================================================


class TestListCredentialsForPerson:
    """Test suite for list_credentials_for_person method."""

    def test_list_credentials_for_person_all(
        self, db, sample_faculty, sample_credential
    ):
        """Test listing all credentials for a person."""
        service = CredentialService(db)
        result = service.list_credentials_for_person(sample_faculty.id)

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == sample_credential.id

    def test_list_credentials_for_person_filter_by_status(
        self, db, sample_faculty, sample_credential
    ):
        """Test filtering credentials by status."""
        service = CredentialService(db)
        result = service.list_credentials_for_person(
            sample_faculty.id, status="active"
        )

        assert result["total"] == 1
        assert result["items"][0].status == "active"

    def test_list_credentials_for_person_exclude_expired(
        self, db, sample_faculty, sample_credential, expired_credential
    ):
        """Test that expired credentials are excluded by default."""
        service = CredentialService(db)
        result = service.list_credentials_for_person(
            sample_faculty.id, include_expired=False
        )

        # Should only include the active, non-expired credential
        assert result["total"] == 1
        assert result["items"][0].id == sample_credential.id

    def test_list_credentials_for_person_include_expired(
        self, db, sample_faculty, sample_credential, expired_credential
    ):
        """Test including expired credentials."""
        service = CredentialService(db)
        result = service.list_credentials_for_person(
            sample_faculty.id, include_expired=True
        )

        # Should include both active and expired credentials
        assert result["total"] == 2

    def test_list_credentials_for_person_empty(self, db, sample_faculty):
        """Test listing credentials when person has none."""
        service = CredentialService(db)
        result = service.list_credentials_for_person(sample_faculty.id)

        assert result["total"] == 0
        assert len(result["items"]) == 0


class TestListCredentialsForProcedure:
    """Test suite for list_credentials_for_procedure method."""

    def test_list_credentials_for_procedure_all(
        self, db, sample_procedure, sample_credential
    ):
        """Test listing all credentials for a procedure."""
        service = CredentialService(db)
        result = service.list_credentials_for_procedure(sample_procedure.id)

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == sample_credential.id

    def test_list_credentials_for_procedure_filter_by_status(
        self, db, sample_procedure, sample_credential
    ):
        """Test filtering procedure credentials by status."""
        service = CredentialService(db)
        result = service.list_credentials_for_procedure(
            sample_procedure.id, status="active"
        )

        assert result["total"] == 1
        assert result["items"][0].status == "active"

    def test_list_credentials_for_procedure_empty(self, db, sample_procedure):
        """Test listing credentials when procedure has none."""
        service = CredentialService(db)
        result = service.list_credentials_for_procedure(sample_procedure.id)

        assert result["total"] == 0
        assert len(result["items"]) == 0


# ============================================================================
# List Qualified Faculty Tests
# ============================================================================


class TestListQualifiedFacultyForProcedure:
    """Test suite for list_qualified_faculty_for_procedure method."""

    def test_list_qualified_faculty_success(
        self, db, sample_procedure, sample_credential, sample_faculty
    ):
        """Test listing qualified faculty for a procedure."""
        service = CredentialService(db)
        result = service.list_qualified_faculty_for_procedure(sample_procedure.id)

        assert result["error"] is None
        assert result["procedure_id"] == sample_procedure.id
        assert result["procedure_name"] == sample_procedure.name
        assert result["total"] == 1
        assert len(result["qualified_faculty"]) == 1
        assert result["qualified_faculty"][0].id == sample_faculty.id

    def test_list_qualified_faculty_procedure_not_found(self, db):
        """Test listing qualified faculty when procedure doesn't exist."""
        service = CredentialService(db)
        fake_id = uuid4()
        result = service.list_qualified_faculty_for_procedure(fake_id)

        assert result["error"] == "Procedure not found"
        assert result["procedure_id"] == fake_id
        assert result["procedure_name"] is None
        assert result["total"] == 0
        assert len(result["qualified_faculty"]) == 0

    def test_list_qualified_faculty_none_qualified(self, db, sample_procedure):
        """Test listing qualified faculty when none exist."""
        service = CredentialService(db)
        result = service.list_qualified_faculty_for_procedure(sample_procedure.id)

        assert result["error"] is None
        assert result["total"] == 0
        assert len(result["qualified_faculty"]) == 0


# ============================================================================
# List Procedures for Faculty Tests
# ============================================================================


class TestListProceduresForFaculty:
    """Test suite for list_procedures_for_faculty method."""

    def test_list_procedures_for_faculty_success(
        self, db, sample_faculty, sample_credential, sample_procedure
    ):
        """Test listing procedures for a faculty member."""
        service = CredentialService(db)
        result = service.list_procedures_for_faculty(sample_faculty.id)

        assert result["error"] is None
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == sample_procedure.id

    def test_list_procedures_for_faculty_person_not_found(self, db):
        """Test listing procedures when person doesn't exist."""
        service = CredentialService(db)
        result = service.list_procedures_for_faculty(uuid4())

        assert result["error"] == "Person not found"
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_procedures_for_faculty_not_faculty(self, db, sample_resident):
        """Test listing procedures when person is not faculty."""
        service = CredentialService(db)
        result = service.list_procedures_for_faculty(sample_resident.id)

        assert result["error"] == "Person is not faculty"
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_procedures_for_faculty_none_qualified(self, db, sample_faculty):
        """Test listing procedures when faculty has no credentials."""
        service = CredentialService(db)
        result = service.list_procedures_for_faculty(sample_faculty.id)

        assert result["error"] is None
        assert result["total"] == 0
        assert len(result["items"]) == 0


# ============================================================================
# Is Faculty Qualified Tests
# ============================================================================


class TestIsFacultyQualified:
    """Test suite for is_faculty_qualified method."""

    def test_is_faculty_qualified_true(
        self, db, sample_faculty, sample_procedure, sample_credential
    ):
        """Test checking if faculty is qualified returns True."""
        service = CredentialService(db)
        result = service.is_faculty_qualified(
            sample_faculty.id, sample_procedure.id
        )

        assert result["is_qualified"] is True

    def test_is_faculty_qualified_false_no_credential(
        self, db, sample_faculty, sample_procedure
    ):
        """Test checking if faculty is qualified returns False when no credential."""
        service = CredentialService(db)
        result = service.is_faculty_qualified(
            sample_faculty.id, sample_procedure.id
        )

        assert result["is_qualified"] is False

    def test_is_faculty_qualified_false_expired(
        self, db, sample_faculty, expired_credential
    ):
        """Test checking if faculty is qualified returns False when credential expired."""
        service = CredentialService(db)
        result = service.is_faculty_qualified(
            sample_faculty.id, expired_credential.procedure_id
        )

        assert result["is_qualified"] is False


# ============================================================================
# Create Credential Tests
# ============================================================================


class TestCreateCredential:
    """Test suite for create_credential method."""

    def test_create_credential_success_minimal_data(
        self, db, sample_faculty, sample_procedure
    ):
        """Test creating a credential with minimal data."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=sample_procedure.id,
        )

        assert result["error"] is None
        credential = result["credential"]
        assert credential is not None
        assert credential.person_id == sample_faculty.id
        assert credential.procedure_id == sample_procedure.id
        assert credential.status == "active"
        assert credential.competency_level == "qualified"
        assert credential.issued_date == date.today()

    def test_create_credential_with_all_fields(
        self, db, sample_faculty, sample_procedure
    ):
        """Test creating a credential with all optional fields."""
        expiration = date.today() + timedelta(days=365)
        issued = date.today() - timedelta(days=30)
        verified = date.today()

        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=sample_procedure.id,
            status="active",
            competency_level="expert",
            issued_date=issued,
            expiration_date=expiration,
            last_verified_date=verified,
            max_concurrent_residents=3,
            max_per_week=10,
            max_per_academic_year=100,
            notes="Excellent performer",
        )

        credential = result["credential"]
        assert credential.status == "active"
        assert credential.competency_level == "expert"
        assert credential.issued_date == issued
        assert credential.expiration_date == expiration
        assert credential.last_verified_date == verified
        assert credential.max_concurrent_residents == 3
        assert credential.max_per_week == 10
        assert credential.max_per_academic_year == 100
        assert credential.notes == "Excellent performer"

    def test_create_credential_person_not_found(self, db, sample_procedure):
        """Test creating credential when person doesn't exist."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=uuid4(),
            procedure_id=sample_procedure.id,
        )

        assert result["error"] == "Person not found"
        assert result["credential"] is None

    def test_create_credential_not_faculty(self, db, sample_resident, sample_procedure):
        """Test creating credential when person is not faculty."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_resident.id,
            procedure_id=sample_procedure.id,
        )

        assert result["error"] == "Only faculty can have procedure credentials"
        assert result["credential"] is None

    def test_create_credential_procedure_not_found(self, db, sample_faculty):
        """Test creating credential when procedure doesn't exist."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=uuid4(),
        )

        assert result["error"] == "Procedure not found"
        assert result["credential"] is None

    def test_create_credential_already_exists(
        self, db, sample_faculty, sample_procedure, sample_credential
    ):
        """Test creating credential when one already exists."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=sample_procedure.id,
        )

        assert result["credential"] is None
        assert "already exists" in result["error"]

    def test_create_credential_persists_to_database(
        self, db, sample_faculty, sample_procedure
    ):
        """Test that created credential is persisted to database."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=sample_procedure.id,
        )

        credential_id = result["credential"].id

        # Query directly from database
        db_credential = (
            db.query(ProcedureCredential)
            .filter(ProcedureCredential.id == credential_id)
            .first()
        )
        assert db_credential is not None
        assert db_credential.person_id == sample_faculty.id


# ============================================================================
# Update Credential Tests
# ============================================================================


class TestUpdateCredential:
    """Test suite for update_credential method."""

    def test_update_credential_success(self, db, sample_credential):
        """Test updating a credential successfully."""
        service = CredentialService(db)
        result = service.update_credential(
            sample_credential.id,
            {"competency_level": "expert", "notes": "Updated notes"},
        )

        assert result["error"] is None
        credential = result["credential"]
        assert credential.competency_level == "expert"
        assert credential.notes == "Updated notes"

    def test_update_credential_not_found(self, db):
        """Test updating a non-existent credential."""
        service = CredentialService(db)
        result = service.update_credential(
            uuid4(),
            {"competency_level": "expert"},
        )

        assert result["error"] == "Credential not found"
        assert result["credential"] is None

    def test_update_credential_status(self, db, sample_credential):
        """Test updating credential status."""
        service = CredentialService(db)
        result = service.update_credential(
            sample_credential.id,
            {"status": "suspended"},
        )

        assert result["credential"].status == "suspended"

    def test_update_credential_expiration_date(self, db, sample_credential):
        """Test updating credential expiration date."""
        new_expiration = date.today() + timedelta(days=730)

        service = CredentialService(db)
        result = service.update_credential(
            sample_credential.id,
            {"expiration_date": new_expiration},
        )

        assert result["credential"].expiration_date == new_expiration

    def test_update_credential_multiple_fields(self, db, sample_credential):
        """Test updating multiple fields at once."""
        service = CredentialService(db)
        result = service.update_credential(
            sample_credential.id,
            {
                "competency_level": "master",
                "max_concurrent_residents": 5,
                "max_per_week": 15,
                "notes": "Top performer",
            },
        )

        credential = result["credential"]
        assert credential.competency_level == "master"
        assert credential.max_concurrent_residents == 5
        assert credential.max_per_week == 15
        assert credential.notes == "Top performer"


# ============================================================================
# Delete Credential Tests
# ============================================================================


class TestDeleteCredential:
    """Test suite for delete_credential method."""

    def test_delete_credential_success(self, db, sample_credential):
        """Test deleting a credential successfully."""
        credential_id = sample_credential.id

        service = CredentialService(db)
        result = service.delete_credential(credential_id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deletion
        db_credential = (
            db.query(ProcedureCredential)
            .filter(ProcedureCredential.id == credential_id)
            .first()
        )
        assert db_credential is None

    def test_delete_credential_not_found(self, db):
        """Test deleting a non-existent credential."""
        service = CredentialService(db)
        result = service.delete_credential(uuid4())

        assert result["success"] is False
        assert result["error"] == "Credential not found"


# ============================================================================
# Suspend/Activate Credential Tests
# ============================================================================


class TestSuspendActivateCredential:
    """Test suite for suspend_credential and activate_credential methods."""

    def test_suspend_credential_success(self, db, sample_credential):
        """Test suspending a credential."""
        service = CredentialService(db)
        result = service.suspend_credential(
            sample_credential.id,
            notes="Suspended for review",
        )

        assert result["error"] is None
        credential = result["credential"]
        assert credential.status == "suspended"
        assert credential.notes == "Suspended for review"

    def test_suspend_credential_without_notes(self, db, sample_credential):
        """Test suspending a credential without notes."""
        service = CredentialService(db)
        result = service.suspend_credential(sample_credential.id)

        assert result["error"] is None
        assert result["credential"].status == "suspended"

    def test_activate_credential_success(self, db, sample_credential):
        """Test activating a credential."""
        # First suspend it
        service = CredentialService(db)
        service.suspend_credential(sample_credential.id)

        # Then activate it
        result = service.activate_credential(sample_credential.id)

        assert result["error"] is None
        assert result["credential"].status == "active"

    def test_suspend_credential_not_found(self, db):
        """Test suspending a non-existent credential."""
        service = CredentialService(db)
        result = service.suspend_credential(uuid4())

        assert result["error"] == "Credential not found"

    def test_activate_credential_not_found(self, db):
        """Test activating a non-existent credential."""
        service = CredentialService(db)
        result = service.activate_credential(uuid4())

        assert result["error"] == "Credential not found"


# ============================================================================
# Verify Credential Tests
# ============================================================================


class TestVerifyCredential:
    """Test suite for verify_credential method."""

    def test_verify_credential_success(self, db, sample_credential):
        """Test verifying a credential."""
        service = CredentialService(db)
        result = service.verify_credential(sample_credential.id)

        assert result["error"] is None
        credential = result["credential"]
        assert credential.last_verified_date == date.today()

    def test_verify_credential_not_found(self, db):
        """Test verifying a non-existent credential."""
        service = CredentialService(db)
        result = service.verify_credential(uuid4())

        assert result["error"] == "Credential not found"


# ============================================================================
# List Expiring Credentials Tests
# ============================================================================


class TestListExpiringCredentials:
    """Test suite for list_expiring_credentials method."""

    def test_list_expiring_credentials_default_30_days(self, db, sample_faculty):
        """Test listing credentials expiring in default 30 days."""
        # Create credential expiring in 15 days
        procedure = Procedure(id=uuid4(), name="Expiring Soon Procedure")
        db.add(procedure)
        db.commit()

        credential = ProcedureCredential(
            id=uuid4(),
            person_id=sample_faculty.id,
            procedure_id=procedure.id,
            status="active",
            expiration_date=date.today() + timedelta(days=15),
        )
        db.add(credential)
        db.commit()

        service = CredentialService(db)
        result = service.list_expiring_credentials()

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == credential.id

    def test_list_expiring_credentials_custom_days(self, db, sample_faculty):
        """Test listing credentials expiring in custom number of days."""
        # Create credential expiring in 60 days
        procedure = Procedure(id=uuid4(), name="Expiring Later Procedure")
        db.add(procedure)
        db.commit()

        credential = ProcedureCredential(
            id=uuid4(),
            person_id=sample_faculty.id,
            procedure_id=procedure.id,
            status="active",
            expiration_date=date.today() + timedelta(days=60),
        )
        db.add(credential)
        db.commit()

        service = CredentialService(db)
        result = service.list_expiring_credentials(days=90)

        assert result["total"] == 1
        assert result["items"][0].id == credential.id

    def test_list_expiring_credentials_excludes_far_future(
        self, db, sample_faculty, sample_credential
    ):
        """Test that credentials expiring far in the future are excluded."""
        service = CredentialService(db)
        result = service.list_expiring_credentials(days=30)

        # sample_credential expires in 365 days, should not be included
        assert result["total"] == 0

    def test_list_expiring_credentials_excludes_already_expired(
        self, db, expired_credential
    ):
        """Test that already expired credentials are excluded."""
        service = CredentialService(db)
        result = service.list_expiring_credentials(days=30)

        assert result["total"] == 0

    def test_list_expiring_credentials_empty(self, db):
        """Test listing expiring credentials when none exist."""
        service = CredentialService(db)
        result = service.list_expiring_credentials()

        assert result["total"] == 0
        assert len(result["items"]) == 0


# ============================================================================
# Get Faculty Credential Summary Tests
# ============================================================================


class TestGetFacultyCredentialSummary:
    """Test suite for get_faculty_credential_summary method."""

    def test_get_faculty_credential_summary_success(
        self, db, sample_faculty, sample_credential
    ):
        """Test getting credential summary for faculty."""
        service = CredentialService(db)
        result = service.get_faculty_credential_summary(sample_faculty.id)

        assert result["error"] is None
        assert result["person_id"] == sample_faculty.id
        assert result["person_name"] == sample_faculty.name
        assert result["total_credentials"] == 1
        assert result["active_credentials"] == 1
        assert result["expiring_soon"] == 0  # Expires in 365 days
        assert len(result["procedures"]) == 1

    def test_get_faculty_credential_summary_with_expiring(self, db, sample_faculty):
        """Test credential summary includes expiring soon count."""
        # Create credential expiring in 15 days
        procedure = Procedure(id=uuid4(), name="Expiring Procedure")
        db.add(procedure)
        db.commit()

        credential = ProcedureCredential(
            id=uuid4(),
            person_id=sample_faculty.id,
            procedure_id=procedure.id,
            status="active",
            expiration_date=date.today() + timedelta(days=15),
        )
        db.add(credential)
        db.commit()

        service = CredentialService(db)
        result = service.get_faculty_credential_summary(sample_faculty.id)

        assert result["total_credentials"] == 1
        assert result["active_credentials"] == 1
        assert result["expiring_soon"] == 1

    def test_get_faculty_credential_summary_person_not_found(self, db):
        """Test getting summary when person doesn't exist."""
        service = CredentialService(db)
        result = service.get_faculty_credential_summary(uuid4())

        assert result["error"] == "Person not found"

    def test_get_faculty_credential_summary_not_faculty(self, db, sample_resident):
        """Test getting summary when person is not faculty."""
        service = CredentialService(db)
        result = service.get_faculty_credential_summary(sample_resident.id)

        assert result["error"] == "Person is not faculty"

    def test_get_faculty_credential_summary_no_credentials(self, db, sample_faculty):
        """Test getting summary when faculty has no credentials."""
        service = CredentialService(db)
        result = service.get_faculty_credential_summary(sample_faculty.id)

        assert result["error"] is None
        assert result["total_credentials"] == 0
        assert result["active_credentials"] == 0
        assert result["expiring_soon"] == 0
        assert len(result["procedures"]) == 0


# ============================================================================
# Bulk Create Credentials Tests
# ============================================================================


class TestBulkCreateCredentials:
    """Test suite for bulk_create_credentials method."""

    def test_bulk_create_credentials_success(
        self, db, sample_faculty, sample_procedures
    ):
        """Test creating multiple credentials at once."""
        procedure_ids = [p.id for p in sample_procedures]

        service = CredentialService(db)
        result = service.bulk_create_credentials(
            person_id=sample_faculty.id,
            procedure_ids=procedure_ids,
            competency_level="qualified",
            status="active",
        )

        assert result["total_created"] == 3
        assert result["total_errors"] == 0
        assert len(result["created"]) == 3
        assert len(result["errors"]) == 0

    def test_bulk_create_credentials_partial_success(
        self, db, sample_faculty, sample_procedures, sample_credential
    ):
        """Test bulk create with some failures."""
        # sample_credential already exists for one procedure
        procedure_ids = [sample_credential.procedure_id] + [
            p.id for p in sample_procedures[:2]
        ]

        service = CredentialService(db)
        result = service.bulk_create_credentials(
            person_id=sample_faculty.id,
            procedure_ids=procedure_ids,
        )

        assert result["total_created"] == 2
        assert result["total_errors"] == 1
        assert len(result["errors"]) == 1
        assert "already exists" in result["errors"][0]["error"]

    def test_bulk_create_credentials_with_defaults(
        self, db, sample_faculty, sample_procedures
    ):
        """Test bulk create with default parameters."""
        procedure_ids = [p.id for p in sample_procedures]
        expiration = date.today() + timedelta(days=365)

        service = CredentialService(db)
        result = service.bulk_create_credentials(
            person_id=sample_faculty.id,
            procedure_ids=procedure_ids,
            competency_level="expert",
            expiration_date=expiration,
            max_concurrent_residents=4,
        )

        assert result["total_created"] == 3
        # Verify defaults were applied
        for credential in result["created"]:
            assert credential.competency_level == "expert"
            assert credential.expiration_date == expiration
            assert credential.max_concurrent_residents == 4

    def test_bulk_create_credentials_all_failures(self, db, sample_resident):
        """Test bulk create when all creations fail."""
        # Using a resident should fail all creations
        procedure_ids = [uuid4(), uuid4()]

        service = CredentialService(db)
        result = service.bulk_create_credentials(
            person_id=sample_resident.id,
            procedure_ids=procedure_ids,
        )

        assert result["total_created"] == 0
        assert result["total_errors"] == 2
        assert len(result["errors"]) == 2

    def test_bulk_create_credentials_empty_list(self, db, sample_faculty):
        """Test bulk create with empty procedure list."""
        service = CredentialService(db)
        result = service.bulk_create_credentials(
            person_id=sample_faculty.id,
            procedure_ids=[],
        )

        assert result["total_created"] == 0
        assert result["total_errors"] == 0
        assert len(result["created"]) == 0
        assert len(result["errors"]) == 0


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestEdgeCases:
    """Test suite for edge cases and complex scenarios."""

    def test_credential_is_valid_property(self, db, sample_credential):
        """Test the is_valid property on credential model."""
        # Active credential with future expiration should be valid
        assert sample_credential.is_valid is True

    def test_credential_is_valid_when_expired(self, db, expired_credential):
        """Test is_valid property returns False when expired."""
        assert expired_credential.is_valid is False

    def test_credential_is_valid_when_suspended(self, db, sample_credential):
        """Test is_valid property returns False when suspended."""
        service = CredentialService(db)
        service.suspend_credential(sample_credential.id)
        db.refresh(sample_credential)

        assert sample_credential.is_valid is False

    def test_multiple_faculty_same_procedure(self, db, sample_procedure):
        """Test multiple faculty can have credentials for same procedure."""
        # Create two faculty members
        faculty1 = Person(
            id=uuid4(),
            name="Dr. Faculty One",
            type="faculty",
            email="faculty1@test.org",
        )
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Faculty Two",
            type="faculty",
            email="faculty2@test.org",
        )
        db.add_all([faculty1, faculty2])
        db.commit()

        service = CredentialService(db)

        # Create credentials for both faculty
        result1 = service.create_credential(faculty1.id, sample_procedure.id)
        result2 = service.create_credential(faculty2.id, sample_procedure.id)

        assert result1["error"] is None
        assert result2["error"] is None

        # Verify both are qualified
        qualified = service.list_qualified_faculty_for_procedure(sample_procedure.id)
        assert qualified["total"] == 2

    def test_credential_without_expiration_never_expires(self, db, sample_faculty):
        """Test that credentials without expiration date never expire."""
        procedure = Procedure(id=uuid4(), name="No Expiration Procedure")
        db.add(procedure)
        db.commit()

        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=procedure.id,
            expiration_date=None,  # No expiration
        )

        credential = result["credential"]
        assert credential.expiration_date is None
        assert credential.is_valid is True

    def test_updates_persist_across_service_instances(
        self, db, sample_credential
    ):
        """Test that updates persist when creating new service instance."""
        service1 = CredentialService(db)
        service1.update_credential(
            sample_credential.id,
            {"competency_level": "master"},
        )

        # Create new service instance and verify change persisted
        service2 = CredentialService(db)
        credential = service2.get_credential(sample_credential.id)

        assert credential.competency_level == "master"
