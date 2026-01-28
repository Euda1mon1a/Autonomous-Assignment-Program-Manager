"""Test suite for emergency coverage service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.models.absence import Absence
from app.services.emergency_coverage import EmergencyCoverageService


class TestEmergencyCoverageService:
    """Test suite for emergency coverage service."""

    @pytest.fixture
    def coverage_service(self, db: Session) -> EmergencyCoverageService:
        """Create an emergency coverage service instance."""
        return EmergencyCoverageService(db)

    @pytest.fixture
    def faculty_1(self, db: Session) -> Person:
        """Create first faculty."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty 1",
            type="faculty",
            email="fac1@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def faculty_2(self, db: Session) -> Person:
        """Create second faculty."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty 2",
            type="faculty",
            email="fac2@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=2,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def rotation_template(self, db: Session) -> RotationTemplate:
        """Create rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="Call Coverage",
            rotation_type="call",
            abbreviation="CALL",
            max_residents=1,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_coverage_service_initialization(self, db: Session):
        """Test EmergencyCoverageService initialization."""
        service = EmergencyCoverageService(db)

        assert service.db is db

    def test_handle_faculty_absence(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
    ):
        """Test handling faculty absence."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        result = coverage_service.handle_absence(
            faculty_id=faculty_1.id,
            absence_type="medical",
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(result, (bool, dict))

    def test_find_coverage_replacement(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
        faculty_2: Person,
    ):
        """Test finding replacement coverage."""
        coverage_date = date.today() + timedelta(days=5)

        replacement = coverage_service.find_replacement(
            original_faculty_id=faculty_1.id,
            coverage_date=coverage_date,
            role="call",
        )

        assert isinstance(replacement, (Person, type(None), dict))

    def test_find_available_coverage(
        self,
        coverage_service: EmergencyCoverageService,
        coverage_date: date = None,
    ):
        """Test finding available coverage."""
        if coverage_date is None:
            coverage_date = date.today() + timedelta(days=5)

        available = coverage_service.find_available(
            coverage_date=coverage_date,
            role="call",
        )

        assert isinstance(available, list)

    def test_get_on_call_schedule(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test retrieving on-call schedule."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        schedule = coverage_service.get_on_call_schedule(start_date, end_date)

        assert isinstance(schedule, list)

    def test_assign_emergency_coverage(
        self,
        coverage_service: EmergencyCoverageService,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test assigning emergency coverage."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=5),
            time_of_day="NIGHT",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        result = coverage_service.assign_coverage(
            person_id=resident.id,
            block_id=block.id,
            rotation_template_id=rotation_template.id,
            emergency=True,
        )

        assert isinstance(result, (bool, dict))

    def test_cancel_assignment_and_find_replacement(
        self,
        coverage_service: EmergencyCoverageService,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test canceling assignment and finding replacement."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=5),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = coverage_service.cancel_and_replace(assignment.id)

        assert isinstance(result, bool)

    def test_get_coverage_gaps(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test identifying coverage gaps."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        gaps = coverage_service.find_gaps(start_date, end_date)

        assert isinstance(gaps, list)

    def test_emergency_escalation_path(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test emergency escalation path."""
        escalation_contacts = coverage_service.get_escalation_path()

        assert isinstance(escalation_contacts, list)

    def test_tdy_deployment_coverage(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
    ):
        """Test handling TDY/deployment."""
        start_date = date.today() + timedelta(days=10)
        end_date = start_date + timedelta(days=30)

        result = coverage_service.handle_tdy(
            faculty_id=faculty_1.id,
            start_date=start_date,
            end_date=end_date,
            reason="deployment",
        )

        assert isinstance(result, (bool, dict))

    def test_medical_emergency_coverage(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
    ):
        """Test handling medical emergency."""
        result = coverage_service.handle_medical_emergency(
            faculty_id=faculty_1.id,
            effective_immediately=True,
        )

        assert isinstance(result, (bool, dict))

    def test_get_backup_coverage_list(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
    ):
        """Test retrieving backup coverage list."""
        backups = coverage_service.get_backups_for(faculty_1.id)

        assert isinstance(backups, list)

    def test_escalate_to_administration(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test escalating coverage issue to administration."""
        result = coverage_service.escalate(
            reason="Cannot find replacement coverage",
            priority="high",
        )

        assert isinstance(result, bool)

    def test_coverage_for_holiday(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test handling coverage during holidays."""
        holiday_date = date.today() + timedelta(days=60)

        coverage = coverage_service.get_holiday_coverage(holiday_date)

        assert isinstance(coverage, list)

    def test_coverage_statistics(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test getting coverage statistics."""
        stats = coverage_service.get_statistics()

        assert isinstance(stats, dict)

    def test_find_faculty_with_skills(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
        db: Session,
    ):
        """Test finding faculty with specific skills."""
        # Add procedure skills
        faculty_1.performs_procedures = True
        db.commit()

        faculty = coverage_service.find_by_skills(
            required_skills=["procedure"],
        )

        assert isinstance(faculty, list)

    def test_conflict_check_before_assignment(
        self,
        coverage_service: EmergencyCoverageService,
        resident: Person,
    ):
        """Test checking conflicts before emergency assignment."""
        coverage_date = date.today() + timedelta(days=5)

        is_available = coverage_service.check_availability(
            person_id=resident.id,
            date=coverage_date,
        )

        assert isinstance(is_available, bool)

    def test_notify_coverage_assigned(
        self,
        coverage_service: EmergencyCoverageService,
        faculty_1: Person,
    ):
        """Test notification when coverage is assigned."""
        result = coverage_service.notify_coverage_assigned(
            faculty_id=faculty_1.id,
            start_date=date.today() + timedelta(days=5),
        )

        assert isinstance(result, bool)

    def test_audit_coverage_changes(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test audit trail for coverage changes."""
        changes = coverage_service.get_audit_trail()

        assert isinstance(changes, list)

    def test_validate_coverage_compliance(
        self,
        coverage_service: EmergencyCoverageService,
    ):
        """Test validating coverage compliance."""
        is_compliant = coverage_service.validate_compliance()

        assert isinstance(is_compliant, bool)
