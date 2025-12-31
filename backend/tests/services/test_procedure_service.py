"""Test suite for procedure service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.procedure_service import ProcedureService


class TestProcedureService:
    """Test suite for procedure service."""

    @pytest.fixture
    def proc_service(self, db: Session) -> ProcedureService:
        """Create a procedure service instance."""
        return ProcedureService(db)

    @pytest.fixture
    def faculty(self, db: Session) -> Person:
        """Create a faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Surgeon",
            type="faculty",
            email="surgeon@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    def test_service_initialization(self, db: Session):
        """Test ProcedureService initialization."""
        service = ProcedureService(db)

        assert service.db is db

    def test_get_procedures(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting list of procedures."""
        procedures = proc_service.get_procedures()

        assert isinstance(procedures, list)

    def test_get_faculty_procedures(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting procedures for a faculty member."""
        procedures = proc_service.get_faculty_procedures(faculty.id)

        assert isinstance(procedures, list)

    def test_assign_procedure_to_faculty(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test assigning a procedure to faculty."""
        result = proc_service.assign_procedure(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(result, bool)

    def test_remove_procedure_from_faculty(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test removing a procedure from faculty."""
        result = proc_service.remove_procedure(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(result, bool)

    def test_get_faculty_with_procedure(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting faculty with specific procedure."""
        faculty = proc_service.get_faculty_with_procedure("Arthroscopy")

        assert isinstance(faculty, list)

    def test_get_procedure_credentials(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting procedure credentials."""
        credentials = proc_service.get_credentials(faculty.id)

        assert isinstance(credentials, list)

    def test_record_procedure_competency(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test recording procedure competency."""
        result = proc_service.record_competency(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
            competency_level="expert",
        )

        assert isinstance(result, bool)

    def test_get_procedure_competency(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting procedure competency level."""
        competency = proc_service.get_competency(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(competency, (str, dict, type(None)))

    def test_get_high_risk_procedures(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting high-risk procedures."""
        procedures = proc_service.get_high_risk_procedures()

        assert isinstance(procedures, list)

    def test_get_procedure_supervision_requirements(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting supervision requirements for procedures."""
        requirements = proc_service.get_supervision_requirements()

        assert isinstance(requirements, dict)

    def test_check_procedure_authorization(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test checking if faculty is authorized for procedure."""
        is_authorized = proc_service.is_authorized(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(is_authorized, bool)

    def test_get_credentialing_status(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting credentialing status."""
        status = proc_service.get_credentialing_status(faculty.id)

        assert isinstance(status, dict)

    def test_schedule_credentialing_review(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test scheduling credentialing review."""
        result = proc_service.schedule_review(
            faculty_id=faculty.id,
            review_date=date.today() + timedelta(days=30),
        )

        assert isinstance(result, bool)

    def test_get_expiring_credentials(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting expiring credentials."""
        credentials = proc_service.get_expiring_credentials(days=30)

        assert isinstance(credentials, list)

    def test_batch_assign_procedures(
        self,
        proc_service: ProcedureService,
        faculty: Person,
        db: Session,
    ):
        """Test batch assigning procedures."""
        # Create multiple faculty
        faculty_list = [faculty]
        for i in range(2):
            fac = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i}",
                type="faculty",
                email=f"fac{i}@hospital.org",
                performs_procedures=True,
            )
            db.add(fac)
            faculty_list.append(fac)
        db.commit()

        result = proc_service.batch_assign(
            faculty_ids=[f.id for f in faculty_list],
            procedure_names=["Arthroscopy", "MRI"],
        )

        assert isinstance(result, bool)

    def test_get_procedure_statistics(
        self,
        proc_service: ProcedureService,
    ):
        """Test getting procedure statistics."""
        stats = proc_service.get_statistics()

        assert isinstance(stats, dict)

    def test_validate_procedure_assignment(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test validating procedure assignment."""
        is_valid = proc_service.validate_assignment(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(is_valid, bool)

    def test_get_procedure_training_status(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting training status for procedures."""
        status = proc_service.get_training_status(faculty.id)

        assert isinstance(status, dict)

    def test_enroll_in_procedure_training(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test enrolling in procedure training."""
        result = proc_service.enroll_training(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(result, bool)

    def test_get_procedure_audit_trail(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test getting audit trail for procedures."""
        trail = proc_service.get_audit_trail(faculty.id)

        assert isinstance(trail, list)

    def test_renew_procedure_credential(
        self,
        proc_service: ProcedureService,
        faculty: Person,
    ):
        """Test renewing procedure credential."""
        result = proc_service.renew_credential(
            faculty_id=faculty.id,
            procedure_name="Arthroscopy",
        )

        assert isinstance(result, bool)
