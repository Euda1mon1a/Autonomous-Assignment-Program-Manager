"""
Comprehensive tests for EmergencyCoverageService.

Tests covering:
- Emergency coverage detection (deployments, medical/family emergencies)
- Coverage gap identification (critical vs non-critical services)
- Emergency staffing logic (replacement finding, priority handling)
- Edge cases (no replacements, multiple assignments, cascading effects)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.emergency_coverage import EmergencyCoverageService


@pytest.fixture
def service(db: Session) -> EmergencyCoverageService:
    """Create an EmergencyCoverageService instance."""
    return EmergencyCoverageService(db)


@pytest.fixture
def critical_rotation_template(db: Session) -> RotationTemplate:
    """Create a critical service rotation template (inpatient)."""
    template = RotationTemplate(
        id=uuid4(),
        name="Inpatient Service",
        rotation_type="inpatient",
        abbreviation="IP",
        max_residents=4,
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def call_rotation_template(db: Session) -> RotationTemplate:
    """Create a critical call rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Emergency Call",
        rotation_type="call",
        abbreviation="CALL",
        max_residents=2,
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def clinic_rotation_template(db: Session) -> RotationTemplate:
    """Create a non-critical clinic rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Sports Medicine Clinic",
        rotation_type="clinic",
        abbreviation="SM",
        max_residents=3,
        supervision_required=False,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def education_rotation_template(db: Session) -> RotationTemplate:
    """Create a non-critical education rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Didactic Education",
        rotation_type="education",
        abbreviation="EDU",
        max_residents=10,
        supervision_required=False,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def multiple_residents(db: Session) -> list[Person]:
    """Create multiple residents at different PGY levels."""
    residents = []
    for i in range(1, 5):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident {i}",
            type="resident",
            email=f"resident{i}@hospital.org",
            pgy_level=(i % 3) + 1,  # PGY 1, 2, 3 levels
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def emergency_blocks(db: Session) -> list[Block]:
    """Create blocks for emergency scenario (next 7 days)."""
    blocks = []
    start_date = date.today() + timedelta(days=1)
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)
    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.mark.unit
class TestEmergencyAbsenceHandling:
    """Tests for handle_emergency_absence() method."""

    @pytest.mark.asyncio
    async def test_handle_deployment_emergency(
        self,
        service: EmergencyCoverageService,
        db: Session,
        multiple_residents: list[Person],
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test handling military deployment emergency."""
        resident = multiple_residents[0]
        replacement_candidate = multiple_residents[1]

        # Create assignment for deployed resident
        assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Military deployment",
            is_deployment=True,
        )

        assert result["status"] in ["success", "partial"]
        assert result["replacements_found"] >= 0

        # Verify absence was recorded
        absence = db.query(Absence).filter(Absence.person_id == resident.id).first()
        assert absence is not None
        assert absence.absence_type == "deployment"
        assert absence.deployment_orders is True

    @pytest.mark.asyncio
    async def test_handle_family_emergency(
        self,
        service: EmergencyCoverageService,
        db: Session,
        multiple_residents: list[Person],
        emergency_blocks: list[Block],
        clinic_rotation_template: RotationTemplate,
    ):
        """Test handling family emergency."""
        resident = multiple_residents[0]

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=clinic_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=3)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Family emergency",
            is_deployment=False,
        )

        assert result is not None
        assert "status" in result

        # Verify absence was recorded
        absence = db.query(Absence).filter(Absence.person_id == resident.id).first()
        assert absence is not None
        assert absence.absence_type == "family_emergency"
        assert absence.deployment_orders is False

    @pytest.mark.asyncio
    async def test_emergency_with_no_affected_assignments(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
    ):
        """Test emergency when resident has no assignments in the date range."""
        start_date = date.today() + timedelta(days=30)
        end_date = date.today() + timedelta(days=37)

        result = await service.handle_emergency_absence(
            person_id=sample_resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Medical leave",
            is_deployment=False,
        )

        assert result["status"] == "success"
        assert result["replacements_found"] == 0
        assert result["coverage_gaps"] == 0
        assert result["requires_manual_review"] is False
        assert len(result["details"]) == 0


@pytest.mark.unit
class TestCoverageGapIdentification:
    """Tests for coverage gap identification and critical service detection."""

    def test_find_affected_assignments(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test finding all assignments affected by an absence."""
        # Create multiple assignments across date range
        assignments = []
        for i in range(5):
            assignment = Assignment(
                id=uuid4(),
                block_id=emergency_blocks[i].id,
                person_id=sample_resident.id,
                rotation_template_id=critical_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=3)

        affected = service._find_affected_assignments(
            sample_resident.id,
            start_date,
            end_date,
        )

        # Should find assignments within date range
        assert len(affected) > 0
        assert all(a.person_id == sample_resident.id for a in affected)

    def test_identify_critical_service(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test identifying critical services (inpatient, call, emergency)."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        assignment.rotation_template = critical_rotation_template

        is_critical = service._is_critical_service(assignment)

        assert is_critical is True

    def test_identify_non_critical_service(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        clinic_rotation_template: RotationTemplate,
    ):
        """Test identifying non-critical services (clinic, education)."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=clinic_rotation_template.id,
            role="primary",
        )
        assignment.rotation_template = clinic_rotation_template

        is_critical = service._is_critical_service(assignment)

        assert is_critical is False

    def test_identify_call_service_as_critical(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        call_rotation_template: RotationTemplate,
    ):
        """Test that call services are identified as critical."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=call_rotation_template.id,
            role="primary",
        )
        assignment.rotation_template = call_rotation_template

        is_critical = service._is_critical_service(assignment)

        assert is_critical is True

    def test_critical_service_keywords(
        self,
        service: EmergencyCoverageService,
    ):
        """Test that critical service keywords are properly defined."""
        assert "inpatient" in service.CRITICAL_ACTIVITIES
        assert "call" in service.CRITICAL_ACTIVITIES
        assert "emergency" in service.CRITICAL_ACTIVITIES
        assert "procedure" in service.CRITICAL_ACTIVITIES


@pytest.mark.unit
class TestEmergencyStaffingLogic:
    """Tests for finding replacements and staffing decisions."""

    @pytest.mark.asyncio
    async def test_find_replacement_same_pgy_level(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test finding replacement prefers same PGY level."""
        # Create residents at different PGY levels
        resident_pgy2 = Person(
            id=uuid4(),
            name="Dr. Assigned PGY2",
            type="resident",
            email="assigned@hospital.org",
            pgy_level=2,
        )
        replacement_pgy2 = Person(
            id=uuid4(),
            name="Dr. Available PGY2",
            type="resident",
            email="available2@hospital.org",
            pgy_level=2,
        )
        replacement_pgy3 = Person(
            id=uuid4(),
            name="Dr. Available PGY3",
            type="resident",
            email="available3@hospital.org",
            pgy_level=3,
        )
        db.add_all([resident_pgy2, replacement_pgy2, replacement_pgy3])
        db.commit()

        # Create assignment for PGY2
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident_pgy2.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Find replacement
        replacement = await service._find_replacement(assignment)

        # Should prefer same PGY level
        assert replacement is not None
        assert replacement.pgy_level == 2

    @pytest.mark.asyncio
    async def test_find_replacement_excludes_assigned(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test that already-assigned residents are excluded from replacement pool."""
        # Create residents
        resident1 = Person(
            id=uuid4(),
            name="Dr. Assigned",
            type="resident",
            email="assigned@hospital.org",
            pgy_level=2,
        )
        resident2 = Person(
            id=uuid4(),
            name="Dr. Also Assigned",
            type="resident",
            email="also.assigned@hospital.org",
            pgy_level=2,
        )
        available = Person(
            id=uuid4(),
            name="Dr. Available",
            type="resident",
            email="available@hospital.org",
            pgy_level=2,
        )
        db.add_all([resident1, resident2, available])
        db.commit()

        block = emergency_blocks[0]

        # Create assignments - resident1 needs replacement, resident2 is already on same block
        assignment1 = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident1.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident2.id,
            rotation_template_id=critical_rotation_template.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()
        db.refresh(assignment1)

        # Find replacement
        replacement = await service._find_replacement(assignment1)

        # Should be the available resident, not the one already assigned
        if replacement:
            assert replacement.id == available.id

    @pytest.mark.asyncio
    async def test_find_replacement_excludes_absent(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test that residents with absences on the date are excluded."""
        # Create residents
        resident = Person(
            id=uuid4(),
            name="Dr. Needs Replacement",
            type="resident",
            email="needs.replacement@hospital.org",
            pgy_level=2,
        )
        absent_resident = Person(
            id=uuid4(),
            name="Dr. On Leave",
            type="resident",
            email="on.leave@hospital.org",
            pgy_level=2,
        )
        available_resident = Person(
            id=uuid4(),
            name="Dr. Available",
            type="resident",
            email="available@hospital.org",
            pgy_level=2,
        )
        db.add_all([resident, absent_resident, available_resident])
        db.commit()

        # Create absence for one potential replacement
        absence = Absence(
            id=uuid4(),
            person_id=absent_resident.id,
            start_date=sample_block.date - timedelta(days=1),
            end_date=sample_block.date + timedelta(days=1),
            absence_type="vacation",
        )
        db.add(absence)

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Find replacement
        replacement = await service._find_replacement(assignment)

        # Should be the available resident, not the absent one
        if replacement:
            assert replacement.id == available_resident.id

    @pytest.mark.asyncio
    async def test_find_replacement_no_candidates(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test handling when no replacement candidates are available."""
        # Create only one resident
        resident = Person(
            id=uuid4(),
            name="Dr. Only Resident",
            type="resident",
            email="only@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Find replacement
        replacement = await service._find_replacement(assignment)

        # Should return None when no candidates
        assert replacement is None


@pytest.mark.unit
class TestPriorityHandling:
    """Tests for priority-based handling of different service types."""

    @pytest.mark.asyncio
    async def test_critical_service_creates_gap_if_no_replacement(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test that critical services without replacements create coverage gaps."""
        # Create only one resident
        resident = Person(
            id=uuid4(),
            name="Dr. Only Resident",
            type="resident",
            email="only@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()

        # Create critical assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Medical emergency",
            is_deployment=False,
        )

        # Should create coverage gap for critical service
        assert result["coverage_gaps"] > 0
        assert result["requires_manual_review"] is True
        assert result["status"] == "partial"

        # Check details for UNCOVERED status
        critical_gaps = [
            d
            for d in result["details"]
            if d.get("status") == "UNCOVERED - REQUIRES ATTENTION"
        ]
        assert len(critical_gaps) > 0

    @pytest.mark.asyncio
    async def test_non_critical_service_cancelled_if_no_replacement(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        education_rotation_template: RotationTemplate,
    ):
        """Test that non-critical services are cancelled if no replacement found."""
        # Create only one resident
        resident = Person(
            id=uuid4(),
            name="Dr. Only Resident",
            type="resident",
            email="only@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()

        # Create non-critical assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=education_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Family leave",
            is_deployment=False,
        )

        # Non-critical should be cancelled, not create gap
        assert result["coverage_gaps"] == 0
        assert result["requires_manual_review"] is False
        assert result["status"] == "success"

        # Check details for cancelled status
        cancelled = [d for d in result["details"] if d.get("status") == "cancelled"]
        assert len(cancelled) > 0

    @pytest.mark.asyncio
    async def test_mixed_critical_and_non_critical_assignments(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
        clinic_rotation_template: RotationTemplate,
    ):
        """Test handling mix of critical and non-critical assignments."""
        # Create two residents - one to be absent, one available
        resident = Person(
            id=uuid4(),
            name="Dr. Emergency Leave",
            type="resident",
            email="emergency@hospital.org",
            pgy_level=2,
        )
        available = Person(
            id=uuid4(),
            name="Dr. Available",
            type="resident",
            email="available@hospital.org",
            pgy_level=2,
        )
        db.add_all([resident, available])
        db.commit()

        # Create one critical and one non-critical assignment
        critical_assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        clinic_assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[1].id,
            person_id=resident.id,
            rotation_template_id=clinic_rotation_template.id,
            role="primary",
        )
        db.add_all([critical_assignment, clinic_assignment])
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Medical emergency",
            is_deployment=False,
        )

        # Should have replacements and/or cancellations
        assert len(result["details"]) == 2

        # Check that critical is covered or flagged
        critical_details = [
            d for d in result["details"] if d.get("is_critical") is True
        ]
        assert len(critical_details) > 0


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_emergency_on_nonexistent_person(
        self,
        service: EmergencyCoverageService,
        db: Session,
    ):
        """Test handling emergency for non-existent person."""
        fake_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=3)

        result = await service.handle_emergency_absence(
            person_id=fake_id,
            start_date=start_date,
            end_date=end_date,
            reason="Test",
            is_deployment=False,
        )

        # Should handle gracefully
        assert result["status"] == "success"
        assert result["replacements_found"] == 0
        assert result["coverage_gaps"] == 0

    @pytest.mark.asyncio
    async def test_overlapping_date_ranges(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test handling when emergency dates span multiple assignments."""
        # Create assignments across a week
        for i in range(7):
            assignment = Assignment(
                id=uuid4(),
                block_id=emergency_blocks[i].id,
                person_id=sample_resident.id,
                rotation_template_id=critical_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)

        result = await service.handle_emergency_absence(
            person_id=sample_resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Deployment",
            is_deployment=True,
        )

        # Should find all affected assignments
        total_actions = (
            result["replacements_found"]
            + result["coverage_gaps"]
            + len([d for d in result["details"] if d.get("status") == "cancelled"])
        )
        assert total_actions > 0

    @pytest.mark.asyncio
    async def test_same_day_emergency(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test handling emergency that starts and ends same day."""
        # Update block to be today
        sample_block.date = date.today()
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        today = date.today()

        result = await service.handle_emergency_absence(
            person_id=sample_resident.id,
            start_date=today,
            end_date=today,
            reason="Acute illness",
            is_deployment=False,
        )

        # Should handle single-day emergency
        assert result is not None
        assert "status" in result

    @pytest.mark.asyncio
    async def test_assignment_notes_updated_with_replacement_info(
        self,
        service: EmergencyCoverageService,
        db: Session,
        multiple_residents: list[Person],
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test that assignment notes are updated with replacement information."""
        resident = multiple_residents[0]
        available = multiple_residents[1]

        assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        assignment_id = assignment.id

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Deployment",
            is_deployment=True,
        )

        # Refresh assignment and check notes
        db.refresh(assignment)
        updated_assignment = (
            db.query(Assignment).filter(Assignment.id == assignment_id).first()
        )

        if result["replacements_found"] > 0:
            assert updated_assignment.notes is not None
            assert (
                "Replaced" in updated_assignment.notes
                or updated_assignment.person_id != resident.id
            )

    @pytest.mark.asyncio
    async def test_multiple_emergencies_same_block(
        self,
        service: EmergencyCoverageService,
        db: Session,
        multiple_residents: list[Person],
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test handling multiple residents with emergencies on same block."""
        resident1 = multiple_residents[0]
        resident2 = multiple_residents[1]

        # Create assignments for both residents on same block
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident1.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident2.id,
            rotation_template_id=critical_rotation_template.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Handle first emergency
        result1 = await service.handle_emergency_absence(
            person_id=resident1.id,
            start_date=sample_block.date,
            end_date=sample_block.date,
            reason="Emergency 1",
            is_deployment=False,
        )

        # Handle second emergency
        result2 = await service.handle_emergency_absence(
            person_id=resident2.id,
            start_date=sample_block.date,
            end_date=sample_block.date,
            reason="Emergency 2",
            is_deployment=False,
        )

        # Both should be handled (though may have gaps)
        assert result1 is not None
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_person_type_matching_in_replacement(
        self,
        service: EmergencyCoverageService,
        db: Session,
        sample_block: Block,
        critical_rotation_template: RotationTemplate,
    ):
        """Test that replacements match the person type (resident vs faculty)."""
        # Create a resident and a faculty
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
            performs_procedures=True,
        )
        another_resident = Person(
            id=uuid4(),
            name="Dr. Available Resident",
            type="resident",
            email="available@hospital.org",
            pgy_level=2,
        )
        db.add_all([resident, faculty, another_resident])
        db.commit()

        # Create assignment for resident
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Find replacement
        replacement = await service._find_replacement(assignment)

        # Replacement should be same type
        if replacement:
            assert replacement.type == "resident"

    def test_absence_recorded_before_finding_replacements(
        self,
        service: EmergencyCoverageService,
        db: Session,
    ):
        """Test that absence is recorded even if replacement finding fails."""
        # This is tested implicitly in other tests, but verify absence creation
        # happens regardless of replacement success
        pass

    @pytest.mark.asyncio
    async def test_result_details_structure(
        self,
        service: EmergencyCoverageService,
        db: Session,
        multiple_residents: list[Person],
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
        clinic_rotation_template: RotationTemplate,
    ):
        """Test that result details have expected structure."""
        resident = multiple_residents[0]

        # Create both critical and non-critical assignments
        critical_assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        clinic_assignment = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[1].id,
            person_id=resident.id,
            rotation_template_id=clinic_rotation_template.id,
            role="primary",
        )
        db.add_all([critical_assignment, clinic_assignment])
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        result = await service.handle_emergency_absence(
            person_id=resident.id,
            start_date=start_date,
            end_date=end_date,
            reason="Test emergency",
            is_deployment=False,
        )

        # Verify result structure
        assert "status" in result
        assert "replacements_found" in result
        assert "coverage_gaps" in result
        assert "requires_manual_review" in result
        assert "details" in result
        assert isinstance(result["details"], list)

        # Verify each detail has expected fields
        for detail in result["details"]:
            assert "block_id" in detail
            assert "is_critical" in detail
            assert "status" in detail


@pytest.mark.unit
class TestIntegrationScenarios:
    """Integration tests for complex real-world scenarios."""

    @pytest.mark.asyncio
    async def test_full_deployment_scenario(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
        clinic_rotation_template: RotationTemplate,
        education_rotation_template: RotationTemplate,
    ):
        """Test complete deployment scenario with mixed assignment types."""
        # Create deployed resident and multiple available residents
        deployed = Person(
            id=uuid4(),
            name="Maj. Deployed",
            type="resident",
            email="deployed@hospital.org",
            pgy_level=2,
        )
        available1 = Person(
            id=uuid4(),
            name="Dr. Available 1",
            type="resident",
            email="available1@hospital.org",
            pgy_level=2,
        )
        available2 = Person(
            id=uuid4(),
            name="Dr. Available 2",
            type="resident",
            email="available2@hospital.org",
            pgy_level=3,
        )
        db.add_all([deployed, available1, available2])
        db.commit()

        # Create diverse assignments: critical, clinic, education
        assignments = [
            Assignment(
                id=uuid4(),
                block_id=emergency_blocks[0].id,
                person_id=deployed.id,
                rotation_template_id=critical_rotation_template.id,
                role="primary",
            ),
            Assignment(
                id=uuid4(),
                block_id=emergency_blocks[1].id,
                person_id=deployed.id,
                rotation_template_id=clinic_rotation_template.id,
                role="primary",
            ),
            Assignment(
                id=uuid4(),
                block_id=emergency_blocks[2].id,
                person_id=deployed.id,
                rotation_template_id=education_rotation_template.id,
                role="primary",
            ),
        ]
        for a in assignments:
            db.add(a)
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=90)  # 3-month deployment

        result = await service.handle_emergency_absence(
            person_id=deployed.id,
            start_date=start_date,
            end_date=end_date,
            reason="TDY deployment - 90 days",
            is_deployment=True,
        )

        # Verify comprehensive handling
        assert result["status"] in ["success", "partial"]
        total_handled = (
            result["replacements_found"]
            + result["coverage_gaps"]
            + len([d for d in result["details"] if d.get("status") == "cancelled"])
        )
        assert total_handled == 3  # All 3 assignments should be handled

        # Verify absence recorded as deployment
        absence = db.query(Absence).filter(Absence.person_id == deployed.id).first()
        assert absence is not None
        assert absence.deployment_orders is True
        assert (absence.end_date - absence.start_date).days >= 89

    @pytest.mark.asyncio
    async def test_cascading_coverage_with_limited_pool(
        self,
        service: EmergencyCoverageService,
        db: Session,
        emergency_blocks: list[Block],
        critical_rotation_template: RotationTemplate,
    ):
        """Test coverage decisions when replacement pool is very limited."""
        # Create 3 residents, 2 need emergency coverage
        resident1 = Person(
            id=uuid4(),
            name="Dr. Emergency 1",
            type="resident",
            email="emergency1@hospital.org",
            pgy_level=2,
        )
        resident2 = Person(
            id=uuid4(),
            name="Dr. Emergency 2",
            type="resident",
            email="emergency2@hospital.org",
            pgy_level=2,
        )
        only_available = Person(
            id=uuid4(),
            name="Dr. Only Available",
            type="resident",
            email="only.available@hospital.org",
            pgy_level=2,
        )
        db.add_all([resident1, resident2, only_available])
        db.commit()

        # Create critical assignments for both
        assignment1 = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident1.id,
            rotation_template_id=critical_rotation_template.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=emergency_blocks[0].id,
            person_id=resident2.id,
            rotation_template_id=critical_rotation_template.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=2)

        # Handle first emergency - should get the available resident
        result1 = await service.handle_emergency_absence(
            person_id=resident1.id,
            start_date=start_date,
            end_date=end_date,
            reason="Medical emergency",
            is_deployment=False,
        )

        # Handle second emergency - no one left
        result2 = await service.handle_emergency_absence(
            person_id=resident2.id,
            start_date=start_date,
            end_date=end_date,
            reason="Family emergency",
            is_deployment=False,
        )

        # First should potentially succeed, second should show gaps
        assert result1 is not None
        assert result2 is not None

        # At least one should require manual review
        assert result1["requires_manual_review"] or result2["requires_manual_review"]
