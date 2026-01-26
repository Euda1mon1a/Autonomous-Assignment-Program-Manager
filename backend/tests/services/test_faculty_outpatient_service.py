"""Test suite for faculty outpatient service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.services.faculty_outpatient_service import (
    FacultyOutpatientAssignmentService as FacultyOutpatientService,
)


class TestFacultyOutpatientService:
    """Test suite for faculty outpatient service."""

    @pytest.fixture
    def outpatient_service(self, db: Session) -> FacultyOutpatientService:
        """Create a faculty outpatient service instance."""
        return FacultyOutpatientService(db)

    @pytest.fixture
    def faculty(self, db: Session) -> Person:
        """Create a faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Attending",
            type="faculty",
            email="attending@hospital.org",
            performs_procedures=False,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def clinic_rotation(self, db: Session) -> RotationTemplate:
        """Create a clinic rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="Outpatient Clinic",
            rotation_type="outpatient",
            abbreviation="OPC",
            max_residents=4,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_service_initialization(self, db: Session):
        """Test FacultyOutpatientService initialization."""
        service = FacultyOutpatientService(db)

        assert service.db is db

    def test_get_outpatient_schedule_for_faculty(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test getting outpatient schedule for faculty."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        schedule = outpatient_service.get_schedule(
            faculty_id=faculty.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(schedule, (list, dict))

    def test_assign_faculty_to_clinic(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
        clinic_rotation: RotationTemplate,
        db: Session,
    ):
        """Test assigning faculty to clinic."""
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        result = outpatient_service.assign_to_clinic(
            faculty_id=faculty.id,
            block_id=block.id,
            rotation_id=clinic_rotation.id,
        )

        assert isinstance(result, bool)

    def test_get_clinic_capacity(
        self,
        outpatient_service: FacultyOutpatientService,
        clinic_rotation: RotationTemplate,
    ):
        """Test getting clinic capacity."""
        capacity = outpatient_service.get_capacity(clinic_rotation.id)

        assert isinstance(capacity, (int, dict))

    def test_get_available_clinic_slots(
        self,
        outpatient_service: FacultyOutpatientService,
        clinic_rotation: RotationTemplate,
    ):
        """Test getting available clinic slots."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        slots = outpatient_service.get_available_slots(
            clinic_id=clinic_rotation.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(slots, list)

    def test_schedule_faculty_supervision(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
        resident: Person,
    ):
        """Test scheduling faculty supervision of resident."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        result = outpatient_service.schedule_supervision(
            faculty_id=faculty.id,
            resident_id=resident.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(result, bool)

    def test_get_supervision_ratios(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test getting supervision ratios."""
        ratios = outpatient_service.get_ratios(faculty.id)

        assert isinstance(ratios, dict)

    def test_check_supervision_compliance(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test checking supervision compliance."""
        is_compliant = outpatient_service.check_compliance()

        assert isinstance(is_compliant, bool)

    def test_get_faculty_clinic_preferences(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test getting faculty clinic preferences."""
        preferences = outpatient_service.get_preferences(faculty.id)

        assert isinstance(preferences, (dict, list))

    def test_set_faculty_clinic_preferences(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test setting faculty clinic preferences."""
        preferences = {
            "preferred_clinics": ["Monday AM", "Wednesday PM"],
            "max_clinics_per_week": 2,
        }

        result = outpatient_service.set_preferences(faculty.id, preferences)

        assert isinstance(result, bool)

    def test_get_clinic_session_details(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test getting clinic session details."""
        details = outpatient_service.get_session_details()

        assert isinstance(details, list)

    def test_balance_faculty_clinic_load(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test balancing faculty clinic load."""
        result = outpatient_service.balance_load()

        assert isinstance(result, bool)

    def test_get_clinic_workload_statistics(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test getting clinic workload statistics."""
        stats = outpatient_service.get_workload_stats()

        assert isinstance(stats, dict)

    def test_report_clinic_no_show(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test reporting clinic no-show."""
        result = outpatient_service.report_no_show(
            faculty_id=faculty.id,
            date=date.today(),
        )

        assert isinstance(result, bool)

    def test_get_clinic_coverage_gaps(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test getting clinic coverage gaps."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        gaps = outpatient_service.find_gaps(start_date, end_date)

        assert isinstance(gaps, list)

    def test_find_clinic_coverage_replacement(
        self,
        outpatient_service: FacultyOutpatientService,
        faculty: Person,
    ):
        """Test finding replacement for clinic coverage."""
        clinic_date = date.today() + timedelta(days=5)

        replacement = outpatient_service.find_replacement(
            faculty_id=faculty.id,
            clinic_date=clinic_date,
        )

        assert isinstance(replacement, (Person, type(None), list))

    def test_get_clinic_audit_trail(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test getting clinic audit trail."""
        trail = outpatient_service.get_audit_trail()

        assert isinstance(trail, list)

    def test_export_clinic_schedule(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test exporting clinic schedule."""
        result = outpatient_service.export_schedule(filename="clinic_schedule.csv")

        assert isinstance(result, bool)

    def test_validate_clinic_coverage(
        self,
        outpatient_service: FacultyOutpatientService,
    ):
        """Test validating clinic coverage."""
        is_valid = outpatient_service.validate_coverage()

        assert isinstance(is_valid, bool)
