"""
Tests for the procedure credentialing system.

Tests cover:
- Procedure CRUD operations
- Credential CRUD operations
- Faculty qualification checks
- Expiration handling
- API endpoints
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.repositories.procedure import ProcedureRepository
from app.repositories.procedure_credential import ProcedureCredentialRepository
from app.services.procedure_service import ProcedureService
from app.services.credential_service import CredentialService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_procedure(db: Session) -> Procedure:
    """Create a sample procedure."""
    procedure = Procedure(
        id=uuid4(),
        name="IUD Placement",
        description="Intrauterine device placement procedure",
        category="office",
        specialty="OB/GYN",
        supervision_ratio=1,
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
def sample_procedures(db: Session) -> list[Procedure]:
    """Create multiple sample procedures."""
    procedures_data = [
        {
            "name": "Mastectomy",
            "category": "surgical",
            "specialty": "Surgery",
            "supervision_ratio": 1,
            "complexity_level": "complex",
            "min_pgy_level": 3,
        },
        {
            "name": "Botox Injection",
            "category": "office",
            "specialty": "Dermatology",
            "supervision_ratio": 2,
            "complexity_level": "standard",
            "min_pgy_level": 2,
        },
        {
            "name": "Labor and Delivery",
            "category": "obstetric",
            "specialty": "OB/GYN",
            "supervision_ratio": 1,
            "complexity_level": "advanced",
            "min_pgy_level": 2,
        },
        {
            "name": "Sports Medicine Clinic",
            "category": "clinic",
            "specialty": "Sports Medicine",
            "supervision_ratio": 4,
            "complexity_level": "standard",
            "min_pgy_level": 1,
        },
    ]
    procedures = []
    for data in procedures_data:
        procedure = Procedure(id=uuid4(), is_active=True, **data)
        db.add(procedure)
        procedures.append(procedure)
    db.commit()
    for p in procedures:
        db.refresh(p)
    return procedures


@pytest.fixture
def faculty_with_credentials(db: Session, sample_procedures: list[Procedure]) -> Person:
    """Create a faculty member with credentials."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Sarah Johnson",
        type="faculty",
        email="sarah.johnson@hospital.org",
        performs_procedures=True,
        specialties=["OB/GYN", "Surgery"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    # Add credentials for some procedures
    for i, proc in enumerate(sample_procedures[:2]):
        credential = ProcedureCredential(
            id=uuid4(),
            person_id=faculty.id,
            procedure_id=proc.id,
            status="active",
            competency_level="expert" if i == 0 else "qualified",
            issued_date=date.today() - timedelta(days=365),
        )
        db.add(credential)
    db.commit()

    return faculty


# ============================================================================
# Procedure Repository Tests
# ============================================================================


class TestProcedureRepository:
    """Tests for ProcedureRepository."""

    def test_create_procedure(self, db: Session):
        """Test creating a procedure."""
        repo = ProcedureRepository(db)
        procedure = repo.create({
            "name": "Test Procedure",
            "category": "office",
            "specialty": "General",
        })
        repo.commit()

        assert procedure.id is not None
        assert procedure.name == "Test Procedure"
        assert procedure.is_active is True

    def test_get_by_name(self, db: Session, sample_procedure: Procedure):
        """Test getting a procedure by name."""
        repo = ProcedureRepository(db)
        found = repo.get_by_name("IUD Placement")

        assert found is not None
        assert found.id == sample_procedure.id

    def test_list_by_specialty(self, db: Session, sample_procedures: list[Procedure]):
        """Test listing procedures by specialty."""
        repo = ProcedureRepository(db)
        ob_gyn = repo.list_by_specialty("OB/GYN")

        assert len(ob_gyn) == 1
        assert ob_gyn[0].specialty == "OB/GYN"

    def test_list_with_filters(self, db: Session, sample_procedures: list[Procedure]):
        """Test listing procedures with multiple filters."""
        repo = ProcedureRepository(db)

        # Filter by category
        office = repo.list_with_filters(category="office")
        assert len(office) == 1

        # Filter by complexity
        complex_procs = repo.list_with_filters(complexity_level="complex")
        assert len(complex_procs) == 1
        assert complex_procs[0].name == "Mastectomy"

    def test_get_unique_specialties(self, db: Session, sample_procedures: list[Procedure]):
        """Test getting unique specialties."""
        repo = ProcedureRepository(db)
        specialties = repo.get_unique_specialties()

        assert "Surgery" in specialties
        assert "OB/GYN" in specialties
        assert "Sports Medicine" in specialties


# ============================================================================
# Procedure Credential Repository Tests
# ============================================================================


class TestProcedureCredentialRepository:
    """Tests for ProcedureCredentialRepository."""

    def test_create_credential(
        self, db: Session, sample_faculty: Person, sample_procedure: Procedure
    ):
        """Test creating a credential."""
        repo = ProcedureCredentialRepository(db)
        credential = repo.create({
            "person_id": sample_faculty.id,
            "procedure_id": sample_procedure.id,
            "status": "active",
            "competency_level": "qualified",
        })
        repo.commit()

        assert credential.id is not None
        assert credential.status == "active"

    def test_get_by_person_and_procedure(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test getting a credential by person and procedure."""
        repo = ProcedureCredentialRepository(db)
        credential = repo.get_by_person_and_procedure(
            faculty_with_credentials.id,
            sample_procedures[0].id,
        )

        assert credential is not None
        assert credential.person_id == faculty_with_credentials.id

    def test_list_by_person(
        self, db: Session, faculty_with_credentials: Person
    ):
        """Test listing credentials for a person."""
        repo = ProcedureCredentialRepository(db)
        credentials = repo.list_by_person(faculty_with_credentials.id)

        assert len(credentials) == 2

    def test_is_faculty_qualified(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test checking if faculty is qualified."""
        repo = ProcedureCredentialRepository(db)

        # Has credential
        assert repo.is_faculty_qualified_for_procedure(
            faculty_with_credentials.id, sample_procedures[0].id
        ) is True

        # No credential
        assert repo.is_faculty_qualified_for_procedure(
            faculty_with_credentials.id, sample_procedures[2].id
        ) is False

    def test_list_qualified_faculty(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test listing qualified faculty for a procedure."""
        repo = ProcedureCredentialRepository(db)
        faculty = repo.list_qualified_faculty_for_procedure(sample_procedures[0].id)

        assert len(faculty) == 1
        assert faculty[0].id == faculty_with_credentials.id

    def test_expired_credential_not_valid(self, db: Session, sample_faculty: Person, sample_procedure: Procedure):
        """Test that expired credentials are not counted as valid."""
        repo = ProcedureCredentialRepository(db)
        credential = repo.create({
            "person_id": sample_faculty.id,
            "procedure_id": sample_procedure.id,
            "status": "active",
            "expiration_date": date.today() - timedelta(days=1),  # Expired yesterday
        })
        repo.commit()

        assert repo.is_faculty_qualified_for_procedure(
            sample_faculty.id, sample_procedure.id
        ) is False


# ============================================================================
# Procedure Service Tests
# ============================================================================


class TestProcedureService:
    """Tests for ProcedureService."""

    def test_create_procedure(self, db: Session):
        """Test creating a procedure via service."""
        service = ProcedureService(db)
        result = service.create_procedure(
            name="New Procedure",
            specialty="General",
            category="office",
        )

        assert result["error"] is None
        assert result["procedure"].name == "New Procedure"

    def test_create_duplicate_name_fails(self, db: Session, sample_procedure: Procedure):
        """Test that duplicate names are rejected."""
        service = ProcedureService(db)
        result = service.create_procedure(
            name="IUD Placement",  # Already exists
            specialty="OB/GYN",
        )

        assert result["error"] is not None
        assert "already exists" in result["error"]

    def test_update_procedure(self, db: Session, sample_procedure: Procedure):
        """Test updating a procedure."""
        service = ProcedureService(db)
        result = service.update_procedure(
            sample_procedure.id,
            {"description": "Updated description"},
        )

        assert result["error"] is None
        assert result["procedure"].description == "Updated description"

    def test_deactivate_procedure(self, db: Session, sample_procedure: Procedure):
        """Test deactivating a procedure."""
        service = ProcedureService(db)
        result = service.deactivate_procedure(sample_procedure.id)

        assert result["error"] is None
        assert result["procedure"].is_active is False


# ============================================================================
# Credential Service Tests
# ============================================================================


class TestCredentialService:
    """Tests for CredentialService."""

    def test_create_credential(
        self, db: Session, sample_faculty: Person, sample_procedure: Procedure
    ):
        """Test creating a credential via service."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_faculty.id,
            procedure_id=sample_procedure.id,
            status="active",
            competency_level="qualified",
        )

        assert result["error"] is None
        assert result["credential"].status == "active"

    def test_create_credential_resident_fails(
        self, db: Session, sample_resident: Person, sample_procedure: Procedure
    ):
        """Test that residents cannot have credentials."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=sample_resident.id,
            procedure_id=sample_procedure.id,
        )

        assert result["error"] is not None
        assert "faculty" in result["error"].lower()

    def test_duplicate_credential_fails(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test that duplicate credentials are rejected."""
        service = CredentialService(db)
        result = service.create_credential(
            person_id=faculty_with_credentials.id,
            procedure_id=sample_procedures[0].id,  # Already has this credential
        )

        assert result["error"] is not None
        assert "already exists" in result["error"].lower()

    def test_is_faculty_qualified(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test checking faculty qualification."""
        service = CredentialService(db)

        # Has credential
        result = service.is_faculty_qualified(
            faculty_with_credentials.id, sample_procedures[0].id
        )
        assert result["is_qualified"] is True

        # No credential
        result = service.is_faculty_qualified(
            faculty_with_credentials.id, sample_procedures[2].id
        )
        assert result["is_qualified"] is False

    def test_suspend_credential(
        self, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test suspending a credential."""
        service = CredentialService(db)
        cred_repo = ProcedureCredentialRepository(db)

        credential = cred_repo.get_by_person_and_procedure(
            faculty_with_credentials.id, sample_procedures[0].id
        )

        result = service.suspend_credential(credential.id, "Under review")

        assert result["error"] is None
        assert result["credential"].status == "suspended"

    def test_get_faculty_summary(
        self, db: Session, faculty_with_credentials: Person
    ):
        """Test getting faculty credential summary."""
        service = CredentialService(db)
        result = service.get_faculty_credential_summary(faculty_with_credentials.id)

        assert result["error"] is None
        assert result["total_credentials"] == 2
        assert result["active_credentials"] == 2


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestProcedureAPI:
    """Tests for procedure API endpoints."""

    def test_list_procedures(self, client, db: Session, sample_procedures: list[Procedure]):
        """Test listing procedures."""
        response = client.get("/api/procedures")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4

    def test_list_procedures_by_specialty(
        self, client, db: Session, sample_procedures: list[Procedure]
    ):
        """Test listing procedures filtered by specialty."""
        response = client.get("/api/procedures?specialty=Surgery")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["specialty"] == "Surgery"

    def test_get_procedure(self, client, db: Session, sample_procedure: Procedure):
        """Test getting a single procedure."""
        response = client.get(f"/api/procedures/{sample_procedure.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "IUD Placement"

    def test_get_specialties(self, client, db: Session, sample_procedures: list[Procedure]):
        """Test getting unique specialties."""
        response = client.get("/api/procedures/specialties")
        assert response.status_code == 200
        data = response.json()
        assert "Surgery" in data
        assert "OB/GYN" in data


class TestCredentialAPI:
    """Tests for credential API endpoints."""

    def test_get_credentials_for_person(
        self, client, db: Session, faculty_with_credentials: Person
    ):
        """Test getting credentials for a person."""
        response = client.get(f"/api/credentials/by-person/{faculty_with_credentials.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_qualified_faculty(
        self, client, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test getting qualified faculty for a procedure."""
        response = client.get(f"/api/credentials/qualified-faculty/{sample_procedures[0].id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["qualified_faculty"][0]["id"] == str(faculty_with_credentials.id)

    def test_check_qualification(
        self, client, db: Session, faculty_with_credentials: Person, sample_procedures: list[Procedure]
    ):
        """Test checking qualification via API."""
        # Has credential
        response = client.get(
            f"/api/credentials/check/{faculty_with_credentials.id}/{sample_procedures[0].id}"
        )
        assert response.status_code == 200
        assert response.json()["is_qualified"] is True

        # No credential
        response = client.get(
            f"/api/credentials/check/{faculty_with_credentials.id}/{sample_procedures[2].id}"
        )
        assert response.status_code == 200
        assert response.json()["is_qualified"] is False


class TestPeopleCredentialAPI:
    """Tests for credential endpoints on people routes."""

    def test_get_person_credentials(
        self, client, db: Session, faculty_with_credentials: Person
    ):
        """Test getting credentials via people endpoint."""
        response = client.get(f"/api/people/{faculty_with_credentials.id}/credentials")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_person_credential_summary(
        self, client, db: Session, faculty_with_credentials: Person
    ):
        """Test getting credential summary via people endpoint."""
        response = client.get(f"/api/people/{faculty_with_credentials.id}/credentials/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_credentials"] == 2
        assert data["active_credentials"] == 2

    def test_get_person_procedures(
        self, client, db: Session, faculty_with_credentials: Person
    ):
        """Test getting qualified procedures via people endpoint."""
        response = client.get(f"/api/people/{faculty_with_credentials.id}/procedures")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
