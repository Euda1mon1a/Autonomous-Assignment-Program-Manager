"""Tests for the block scheduler service.

Tests cover:
- Leave-eligible rotation matching algorithm
- Coverage prioritization for non-leave-eligible rotations
- Dashboard data generation
- CRUD operations for block assignments
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.block_scheduler_service import BlockSchedulerService


class TestBlockSchedulerService:
    """Test suite for BlockSchedulerService."""

    @pytest.fixture
    def service(self, db: Session) -> BlockSchedulerService:
        """Create a BlockSchedulerService instance."""
        return BlockSchedulerService(db)

    @pytest.fixture
    def leave_eligible_rotation(self, db: Session) -> RotationTemplate:
        """Create a leave-eligible rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Elective",
            activity_type="elective",
            abbreviation="SME",
            leave_eligible=True,
            max_residents=3,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def non_leave_eligible_rotation(self, db: Session) -> RotationTemplate:
        """Create a non-leave-eligible rotation (e.g., FMIT)."""
        template = RotationTemplate(
            id=uuid4(),
            name="FMIT Inpatient",
            activity_type="inpatient",
            abbreviation="FMIT",
            leave_eligible=False,
            max_residents=2,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def residents_with_leave(self, db: Session) -> list[tuple[Person, Absence]]:
        """Create residents with leave during block 5 of 2025."""
        # Block 5 of 2025 starts July 1 + (5-1)*28 = July 1 + 112 days = Oct 21
        block_start = date(2025, 10, 21)
        block_end = block_start + timedelta(days=27)

        results = []

        # Resident 1: Full block vacation
        r1 = Person(
            id=uuid4(),
            name="Dr. Vacation Full",
            type="resident",
            email="vacation.full@test.org",
            pgy_level=2,
        )
        db.add(r1)
        a1 = Absence(
            id=uuid4(),
            person_id=r1.id,
            start_date=block_start,
            end_date=block_end,
            absence_type="vacation",
        )
        db.add(a1)
        results.append((r1, a1))

        # Resident 2: Partial leave (conference)
        r2 = Person(
            id=uuid4(),
            name="Dr. Conference",
            type="resident",
            email="conference@test.org",
            pgy_level=1,
        )
        db.add(r2)
        a2 = Absence(
            id=uuid4(),
            person_id=r2.id,
            start_date=block_start + timedelta(days=5),
            end_date=block_start + timedelta(days=8),
            absence_type="conference",
        )
        db.add(a2)
        results.append((r2, a2))

        db.commit()
        for r, a in results:
            db.refresh(r)
            db.refresh(a)

        return results

    @pytest.fixture
    def residents_without_leave(self, db: Session) -> list[Person]:
        """Create residents without leave."""
        residents = []
        for i in range(3):
            r = Person(
                id=uuid4(),
                name=f"Dr. Available {i + 1}",
                type="resident",
                email=f"available{i + 1}@test.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(r)
            residents.append(r)

        db.commit()
        for r in residents:
            db.refresh(r)
        return residents

    # =========================================================================
    # Block Date Calculation Tests
    # =========================================================================

    def test_get_block_dates_block_1(self, service: BlockSchedulerService):
        """Test date calculation for block 1."""
        start, end = service.get_block_dates(1, 2025)

        # Block 1 starts July 1, 2025
        assert start == date(2025, 7, 1)
        assert end == date(2025, 7, 28)
        assert (end - start).days == 27  # 28 days inclusive

    def test_get_block_dates_block_5(self, service: BlockSchedulerService):
        """Test date calculation for block 5."""
        start, end = service.get_block_dates(5, 2025)

        # Block 5 starts July 1 + 4*28 days = July 1 + 112 days
        expected_start = date(2025, 7, 1) + timedelta(days=112)
        assert start == expected_start
        assert (end - start).days == 27

    def test_get_block_dates_block_0_orientation(self, service: BlockSchedulerService):
        """Test date calculation for block 0 (orientation)."""
        start, end = service.get_block_dates(0, 2025)

        # Block 0 is orientation, last week before July 1
        assert end == date(2025, 6, 30)
        assert start == date(2025, 6, 24)

    # =========================================================================
    # Leave Detection Tests
    # =========================================================================

    def test_get_residents_with_leave_in_block(
        self,
        service: BlockSchedulerService,
        residents_with_leave: list[tuple[Person, Absence]],
        residents_without_leave: list[Person],
    ):
        """Test detection of residents with leave in a block."""
        # Block 5 of 2025 contains our test leave
        result = service.get_residents_with_leave_in_block(5, 2025)

        assert len(result) == 2

        # Check full vacation resident
        full_leave = next(r for r in result if r.resident.name == "Dr. Vacation Full")
        assert full_leave.leave_days == 28
        assert "vacation" in full_leave.leave_types

        # Check partial leave resident
        partial_leave = next(r for r in result if r.resident.name == "Dr. Conference")
        assert partial_leave.leave_days == 4
        assert "conference" in partial_leave.leave_types

    def test_no_residents_with_leave(
        self,
        service: BlockSchedulerService,
        residents_without_leave: list[Person],
    ):
        """Test when no residents have leave in a block."""
        result = service.get_residents_with_leave_in_block(1, 2025)
        assert len(result) == 0

    # =========================================================================
    # Rotation Capacity Tests
    # =========================================================================

    def test_get_rotation_capacities(
        self,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        non_leave_eligible_rotation: RotationTemplate,
    ):
        """Test getting rotation capacity status."""
        capacities = service.get_rotation_capacities(1, 2025)

        assert len(capacities) == 2

        # Check leave-eligible rotation
        le_slot = capacities[leave_eligible_rotation.id]
        assert le_slot.template.leave_eligible is True
        assert le_slot.max_capacity == 3
        assert le_slot.current_count == 0
        assert le_slot.available == 3
        assert le_slot.is_full is False

        # Check non-leave-eligible rotation
        nle_slot = capacities[non_leave_eligible_rotation.id]
        assert nle_slot.template.leave_eligible is False
        assert nle_slot.max_capacity == 2

    # =========================================================================
    # Scheduling Algorithm Tests
    # =========================================================================

    def test_schedule_block_assigns_leave_residents_to_leave_eligible(
        self,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        non_leave_eligible_rotation: RotationTemplate,
        residents_with_leave: list[tuple[Person, Absence]],
    ):
        """Test that residents with leave get assigned to leave-eligible rotations."""
        result = service.schedule_block(
            block_number=5,
            academic_year=2025,
            dry_run=True,
            include_all_residents=False,
        )

        assert result.success is True
        assert result.dry_run is True
        assert result.residents_with_leave == 2
        assert len(result.assignments) == 2

        # All assignments should be to leave-eligible rotation
        for assignment in result.assignments:
            assert assignment.has_leave is True
            assert assignment.is_leave_eligible_rotation is True
            assert assignment.assignment_reason == "leave_eligible_match"

    def test_schedule_block_coverage_priority(
        self,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        non_leave_eligible_rotation: RotationTemplate,
        residents_without_leave: list[Person],
    ):
        """Test that residents without leave fill coverage needs first."""
        result = service.schedule_block(
            block_number=1,
            academic_year=2025,
            dry_run=True,
            include_all_residents=True,
        )

        assert result.success is True
        assert len(result.assignments) == 3

        # Check that non-leave-eligible rotation gets priority
        coverage_assignments = [
            a for a in result.assignments if not a.is_leave_eligible_rotation
        ]

        # Should have assignments to non-leave-eligible (FMIT)
        # up to its capacity (2)
        assert len(coverage_assignments) <= 2

    def test_schedule_block_dry_run_does_not_save(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        residents_with_leave: list[tuple[Person, Absence]],
    ):
        """Test that dry run doesn't save to database."""
        result = service.schedule_block(
            block_number=5,
            academic_year=2025,
            dry_run=True,
        )

        assert result.dry_run is True

        # Check database has no assignments
        assignments = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.block_number == 5,
                BlockAssignment.academic_year == 2025,
            )
            .all()
        )

        assert len(assignments) == 0

    def test_schedule_block_saves_when_not_dry_run(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        residents_with_leave: list[tuple[Person, Absence]],
    ):
        """Test that assignments are saved when dry_run=False."""
        result = service.schedule_block(
            block_number=5,
            academic_year=2025,
            dry_run=False,
            include_all_residents=False,
        )

        assert result.dry_run is False

        # Check database has assignments
        assignments = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.block_number == 5,
                BlockAssignment.academic_year == 2025,
            )
            .all()
        )

        assert len(assignments) == len(result.assignments)

    def test_schedule_block_identifies_coverage_gaps(
        self,
        service: BlockSchedulerService,
        non_leave_eligible_rotation: RotationTemplate,
    ):
        """Test that coverage gaps are identified."""
        # No residents to assign, so FMIT will have gaps
        result = service.schedule_block(
            block_number=1,
            academic_year=2025,
            dry_run=True,
        )

        # Find gap for non-leave-eligible rotation
        fmit_gaps = [
            g for g in result.coverage_gaps if g.rotation_name == "FMIT Inpatient"
        ]

        assert len(fmit_gaps) == 1
        assert fmit_gaps[0].gap == 2  # max_residents = 2, assigned = 0
        assert fmit_gaps[0].severity == "critical"

    # =========================================================================
    # Dashboard Tests
    # =========================================================================

    def test_get_dashboard(
        self,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        non_leave_eligible_rotation: RotationTemplate,
        residents_with_leave: list[tuple[Person, Absence]],
        residents_without_leave: list[Person],
    ):
        """Test dashboard data generation."""
        dashboard = service.get_dashboard(5, 2025)

        assert dashboard.block_number == 5
        assert dashboard.academic_year == 2025
        assert dashboard.block_start_date is not None
        assert dashboard.block_end_date is not None

        # Check resident counts
        assert dashboard.total_residents == 5  # 2 with leave + 3 without
        assert len(dashboard.residents_with_leave) == 2

        # Check rotation counts
        assert dashboard.leave_eligible_rotations == 1
        assert dashboard.non_leave_eligible_rotations == 1
        assert len(dashboard.rotation_capacities) == 2

        # No assignments yet
        assert len(dashboard.current_assignments) == 0
        assert dashboard.unassigned_residents == 5

    # =========================================================================
    # Manual Assignment Tests
    # =========================================================================

    def test_create_manual_assignment(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        residents_without_leave: list[Person],
    ):
        """Test manual assignment creation."""
        resident = residents_without_leave[0]

        assignment = service.create_manual_assignment(
            block_number=1,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=leave_eligible_rotation.id,
            created_by="test@test.org",
            notes="Manual override",
        )

        assert assignment is not None
        assert assignment.resident_id == resident.id
        assert assignment.rotation_template_id == leave_eligible_rotation.id
        assert assignment.assignment_reason == "manual"
        assert assignment.has_leave is False
        assert assignment.notes == "Manual override"

    def test_create_manual_assignment_with_leave(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        residents_with_leave: list[tuple[Person, Absence]],
    ):
        """Test manual assignment detects leave status."""
        resident, absence = residents_with_leave[0]

        assignment = service.create_manual_assignment(
            block_number=5,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=leave_eligible_rotation.id,
        )

        assert assignment.has_leave is True
        assert assignment.leave_days == 28

    def test_update_assignment(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        non_leave_eligible_rotation: RotationTemplate,
        residents_without_leave: list[Person],
    ):
        """Test updating an assignment."""
        resident = residents_without_leave[0]

        # Create initial assignment
        assignment = service.create_manual_assignment(
            block_number=1,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=leave_eligible_rotation.id,
        )

        # Update to different rotation
        updated = service.update_assignment(
            assignment.id,
            {"rotation_template_id": non_leave_eligible_rotation.id},
        )

        assert updated is not None
        assert updated.rotation_template_id == non_leave_eligible_rotation.id
        assert updated.assignment_reason == "manual"  # Changed due to rotation update

    def test_delete_assignment(
        self,
        db: Session,
        service: BlockSchedulerService,
        leave_eligible_rotation: RotationTemplate,
        residents_without_leave: list[Person],
    ):
        """Test deleting an assignment."""
        resident = residents_without_leave[0]

        assignment = service.create_manual_assignment(
            block_number=1,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=leave_eligible_rotation.id,
        )

        success = service.delete_assignment(assignment.id)
        assert success is True

        # Verify deleted
        retrieved = service.get_assignment(assignment.id)
        assert retrieved is None

    def test_delete_nonexistent_assignment(
        self,
        service: BlockSchedulerService,
    ):
        """Test deleting a nonexistent assignment."""
        success = service.delete_assignment(uuid4())
        assert success is False


class TestLeaveConflictDetection:
    """Test suite for leave conflict detection."""

    @pytest.fixture
    def service(self, db: Session) -> BlockSchedulerService:
        return BlockSchedulerService(db)

    def test_leave_conflict_when_no_leave_eligible_capacity(
        self,
        db: Session,
        service: BlockSchedulerService,
    ):
        """Test conflict detection when no leave-eligible rotation has capacity."""
        # Create only non-leave-eligible rotation
        fmit = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            leave_eligible=False,
            max_residents=2,
        )
        db.add(fmit)

        # Create resident with leave
        resident = Person(
            id=uuid4(),
            name="Dr. Stuck",
            type="resident",
            email="stuck@test.org",
            pgy_level=2,
        )
        db.add(resident)

        absence = Absence(
            id=uuid4(),
            person_id=resident.id,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 28),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        result = service.schedule_block(
            block_number=1,
            academic_year=2025,
            dry_run=True,
            include_all_residents=False,
        )

        assert result.success is False
        assert len(result.leave_conflicts) == 1
        assert result.leave_conflicts[0].resident_name == "Dr. Stuck"
        assert "No leave-eligible rotation" in result.leave_conflicts[0].conflict_reason
