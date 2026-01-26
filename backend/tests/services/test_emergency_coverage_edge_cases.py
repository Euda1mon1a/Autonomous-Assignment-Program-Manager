"""Edge case and comprehensive tests for emergency coverage service."""

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


class TestEmergencyCoverageEdgeCases:
    """Comprehensive edge case tests for emergency coverage service."""

    @pytest.fixture
    def service(self, db: Session) -> EmergencyCoverageService:
        """Create service instance."""
        return EmergencyCoverageService(db)

    @pytest.fixture
    def faculty(self, db: Session) -> Person:
        """Create faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def backup_faculty(self, db: Session) -> Person:
        """Create backup faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Backup",
            type="faculty",
            email="backup@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create resident."""
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
    def critical_rotation(self, db: Session) -> RotationTemplate:
        """Create critical rotation template (call)."""
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

    @pytest.fixture
    def non_critical_rotation(self, db: Session) -> RotationTemplate:
        """Create non-critical rotation template (clinic)."""
        template = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            rotation_type="outpatient",
            abbreviation="CLINIC",
            max_residents=4,
            supervision_required=False,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def inpatient_rotation(self, db: Session) -> RotationTemplate:
        """Create inpatient rotation template (critical)."""
        template = RotationTemplate(
            id=uuid4(),
            name="Inpatient",
            rotation_type="inpatient",
            abbreviation="IP",
            max_residents=2,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    # ===== TESTS FOR handle_emergency_absence() =====

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_basic(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test basic emergency absence handling."""
        start = date.today()
        end = start + timedelta(days=3)

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=end,
            reason="Medical emergency",
            is_deployment=False,
        )

        assert isinstance(result, dict)
        assert "status" in result
        assert "replacements_found" in result
        assert "coverage_gaps" in result
        assert "requires_manual_review" in result
        assert "details" in result

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_deployment(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test emergency absence for military deployment."""
        start = date.today()
        end = start + timedelta(days=180)  # 6-month deployment

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=end,
            reason="Military deployment",
            is_deployment=True,
        )

        assert result["status"] in ["success", "partial"]
        assert isinstance(result["replacements_found"], int)

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_no_assignments(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test emergency absence when faculty has no assignments."""
        future_start = date.today() + timedelta(days=365)
        future_end = future_start + timedelta(days=7)

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=future_start,
            end_date=future_end,
            reason="Personal leave",
            is_deployment=False,
        )

        # Should succeed with no replacements needed
        assert result["status"] == "success"
        assert result["replacements_found"] == 0
        assert result["coverage_gaps"] == 0

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_critical_service(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test emergency absence affecting critical service."""
        # Create critical assignment (call coverage)
        start = date.today()
        block = Block(
            id=uuid4(),
            date=start,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=block.id,
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=start,
            reason="Family emergency",
            is_deployment=False,
        )

        # Critical service should require manual review if no replacement
        if result["coverage_gaps"] > 0:
            assert result["requires_manual_review"] is True
            assert result["status"] == "partial"

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_non_critical_service(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        non_critical_rotation: RotationTemplate,
    ):
        """Test emergency absence affecting non-critical service."""
        start = date.today()
        block = Block(
            id=uuid4(),
            date=start,
            time_of_day="PM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=block.id,
            rotation_template_id=non_critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=start,
            reason="Sick day",
            is_deployment=False,
        )

        # Non-critical can be cancelled without replacement
        assert isinstance(result["details"], list)

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_multiple_days(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test emergency absence spanning multiple days."""
        start = date.today()
        end = start + timedelta(days=5)

        # Create assignments for multiple days
        for i in range(6):
            day = start + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=day,
                time_of_day="AM",
                block_number=i + 1,
                is_weekend=False,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                person_id=faculty.id,
                block_id=block.id,
                rotation_template_id=critical_rotation.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=end,
            reason="Medical leave",
            is_deployment=False,
        )

        # Should process multiple assignments
        total_processed = result["replacements_found"] + result["coverage_gaps"]
        assert total_processed > 0

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_single_day(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test emergency absence for single day."""
        start = date.today()

        block = Block(
            id=uuid4(),
            date=start,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=block.id,
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=start,
            end_date=start,
            reason="Sick day",
            is_deployment=False,
        )

        assert isinstance(result["details"], list)

    # ===== TESTS FOR _is_critical_service() =====

    def test_is_critical_service_call(
        self,
        service: EmergencyCoverageService,
        db: Session,
        critical_rotation: RotationTemplate,
    ):
        """Test _is_critical_service identifies call as critical."""
        assignment = Assignment(
            id=uuid4(),
            person_id=uuid4(),
            block_id=uuid4(),
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        assignment.rotation_template = critical_rotation

        assert service._is_critical_service(assignment) is True

    def test_is_critical_service_inpatient(
        self,
        service: EmergencyCoverageService,
        db: Session,
        inpatient_rotation: RotationTemplate,
    ):
        """Test _is_critical_service identifies inpatient as critical."""
        assignment = Assignment(
            id=uuid4(),
            person_id=uuid4(),
            block_id=uuid4(),
            rotation_template_id=inpatient_rotation.id,
            role="primary",
        )
        assignment.rotation_template = inpatient_rotation

        assert service._is_critical_service(assignment) is True

    def test_is_critical_service_clinic(
        self,
        service: EmergencyCoverageService,
        db: Session,
        non_critical_rotation: RotationTemplate,
    ):
        """Test _is_critical_service identifies clinic as non-critical."""
        assignment = Assignment(
            id=uuid4(),
            person_id=uuid4(),
            block_id=uuid4(),
            rotation_template_id=non_critical_rotation.id,
            role="primary",
        )
        assignment.rotation_template = non_critical_rotation

        assert service._is_critical_service(assignment) is False

    def test_is_critical_service_no_template(self, service: EmergencyCoverageService):
        """Test _is_critical_service with assignment lacking rotation template."""
        assignment = Assignment(
            id=uuid4(),
            person_id=uuid4(),
            block_id=uuid4(),
            rotation_template_id=None,
            role="primary",
        )
        assignment.rotation_template = None

        # Should default to False
        assert service._is_critical_service(assignment) is False

    # ===== TESTS FOR _find_affected_assignments() =====

    def test_find_affected_assignments_date_range(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test _find_affected_assignments returns correct date range."""
        start = date.today()
        end = start + timedelta(days=3)

        # Create assignments within range
        for i in range(4):
            day = start + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=day,
                time_of_day="AM",
                block_number=i + 1,
                is_weekend=False,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                person_id=faculty.id,
                block_id=block.id,
                rotation_template_id=critical_rotation.id,
                role="primary",
            )
            db.add(assignment)

        # Create assignment outside range
        future_block = Block(
            id=uuid4(),
            date=end + timedelta(days=10),
            time_of_day="AM",
            block_number=99,
            is_weekend=False,
        )
        db.add(future_block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=future_block.id,
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        affected = service._find_affected_assignments(faculty.id, start, end)

        # Should find only 4 assignments within date range
        assert len(affected) == 4

    def test_find_affected_assignments_empty(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test _find_affected_assignments with no assignments."""
        future_start = date.today() + timedelta(days=365)
        future_end = future_start + timedelta(days=7)

        affected = service._find_affected_assignments(
            faculty.id, future_start, future_end
        )

        assert affected == []

    def test_find_affected_assignments_single_day(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test _find_affected_assignments for single day."""
        target_date = date.today()

        block = Block(
            id=uuid4(),
            date=target_date,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=block.id,
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        affected = service._find_affected_assignments(
            faculty.id, target_date, target_date
        )

        assert len(affected) == 1

    # ===== EDGE CASE TESTS =====

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_weekend(
        self,
        service: EmergencyCoverageService,
        db: Session,
        faculty: Person,
        critical_rotation: RotationTemplate,
    ):
        """Test emergency absence affecting weekend coverage."""
        # Find next weekend (Saturday)
        today = date.today()
        days_ahead = (5 - today.weekday()) % 7  # 5 = Saturday
        saturday = today + timedelta(days=days_ahead if days_ahead > 0 else 7)

        block = Block(
            id=uuid4(),
            date=saturday,
            time_of_day="AM",
            block_number=1,
            is_weekend=True,
        )
        db.add(block)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            person_id=faculty.id,
            block_id=block.id,
            rotation_template_id=critical_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=saturday,
            end_date=saturday,
            reason="Weekend emergency",
            is_deployment=False,
        )

        assert isinstance(result["details"], list)

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_past_date(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test emergency absence with past dates."""
        past_start = date.today() - timedelta(days=7)
        past_end = date.today() - timedelta(days=1)

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=past_start,
            end_date=past_end,
            reason="Retroactive entry",
            is_deployment=False,
        )

        # Should complete without error
        assert result["status"] in ["success", "partial"]

    @pytest.mark.asyncio
    async def test_handle_emergency_absence_same_day(
        self, service: EmergencyCoverageService, faculty: Person
    ):
        """Test emergency absence with same start and end date."""
        today = date.today()

        result = await service.handle_emergency_absence(
            person_id=faculty.id,
            start_date=today,
            end_date=today,
            reason="Sick day",
            is_deployment=False,
        )

        assert isinstance(result, dict)

    def test_critical_activities_constant(self, service: EmergencyCoverageService):
        """Test CRITICAL_ACTIVITIES constant is properly defined."""
        assert hasattr(service, "CRITICAL_ACTIVITIES")
        assert isinstance(service.CRITICAL_ACTIVITIES, list)
        assert "call" in service.CRITICAL_ACTIVITIES
        assert "inpatient" in service.CRITICAL_ACTIVITIES
        assert len(service.CRITICAL_ACTIVITIES) > 0
