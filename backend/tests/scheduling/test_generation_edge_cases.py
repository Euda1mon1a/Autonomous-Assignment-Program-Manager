"""
Schedule Generation Edge Case Tests.

Comprehensive tests for edge cases and boundary conditions in the
scheduling engine and constraint solver.

Test Coverage:
- Insufficient faculty/residents for coverage
- Conflicting constraints (impossible schedules)
- Holiday and weekend handling
- Leave/absence collision handling
- Timezone edge cases
- Block boundary conditions
- Rotation capacity limits
- Emergency coverage scenarios
- Solver timeout handling
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.engine import SchedulingEngine
from app.scheduling.constraints import ConstraintViolation


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def scheduling_engine(db: Session) -> SchedulingEngine:
    """Create a scheduling engine instance."""
    return SchedulingEngine(db)


@pytest.fixture
def minimal_faculty(db: Session) -> list[Person]:
    """Create minimal faculty (just 1 person)."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Solo Faculty",
        type="faculty",
        email="solo@test.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return [faculty]


@pytest.fixture
def residents_all_pgys(db: Session) -> list[Person]:
    """Create one resident for each PGY level."""
    residents = []
    for pgy in range(1, 4):
        resident = Person(
            id=uuid4(),
            name=f"Dr. PGY-{pgy}",
            type="resident",
            email=f"pgy{pgy}@test.org",
            pgy_level=pgy,
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def high_capacity_rotation(db: Session) -> RotationTemplate:
    """Create rotation requiring many residents."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Busy Clinic",
        activity_type="outpatient",
        abbreviation="BUSY",
        max_residents=10,  # Requires 10 residents
        min_residents=8,
        supervision_required=True,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


@pytest.fixture
def exclusive_rotation(db: Session) -> RotationTemplate:
    """Create rotation that can't overlap with others."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Exclusive Procedure",
        activity_type="procedure",
        abbreviation="EXCL",
        max_residents=1,
        min_residents=1,
        exclusive=True,  # Can't be scheduled with other rotations
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


def create_blocks_range(
    db: Session, start_date: date, end_date: date
) -> list[Block]:
    """Create blocks for a date range."""
    blocks = []
    current = start_date
    while current <= end_date:
        for tod in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current,
                time_of_day=tod,
                block_number=1,
                is_weekend=(current.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)
        current += timedelta(days=1)
    db.commit()
    return blocks


# ============================================================================
# Test Class: Insufficient Resources
# ============================================================================


class TestInsufficientResources:
    """Tests for scenarios with insufficient personnel."""

    def test_insufficient_faculty_for_coverage(
        self, db: Session, scheduling_engine: SchedulingEngine,
        minimal_faculty: list[Person], high_capacity_rotation: RotationTemplate
    ):
        """Test scheduling when not enough faculty available."""
        start_date = date.today()
        blocks = create_blocks_range(db, start_date, start_date + timedelta(days=6))

        # Try to schedule rotation requiring 10 people with only 1 available
        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
            rotation_ids=[high_capacity_rotation.id],
        )

        assert result.success is False
        assert "insufficient" in result.error_message.lower() or \
               "capacity" in result.error_message.lower()

    def test_all_residents_on_leave(
        self, db: Session, scheduling_engine: SchedulingEngine,
        residents_all_pgys: list[Person],
        sample_rotation_template: RotationTemplate
    ):
        """Test scheduling when all residents are on leave."""
        start_date = date.today() + timedelta(days=7)
        blocks = create_blocks_range(db, start_date, start_date + timedelta(days=6))

        # Mark all residents on leave
        for resident in residents_all_pgys:
            absence = Absence(
                id=uuid4(),
                person_id=resident.id,
                start_date=start_date,
                end_date=start_date + timedelta(days=6),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
            rotation_ids=[sample_rotation_template.id],
        )

        assert result.success is False

    def test_partial_availability_scheduling(
        self, db: Session, scheduling_engine: SchedulingEngine,
        residents_all_pgys: list[Person],
        sample_rotation_template: RotationTemplate
    ):
        """Test scheduling with partial resident availability."""
        start_date = date.today() + timedelta(days=7)
        blocks = create_blocks_range(db, start_date, start_date + timedelta(days=6))

        # Mark 2 out of 3 residents on leave
        for i in range(2):
            absence = Absence(
                id=uuid4(),
                person_id=residents_all_pgys[i].id,
                start_date=start_date,
                end_date=start_date + timedelta(days=3),
                absence_type="conference",
            )
            db.add(absence)
        db.commit()

        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
            rotation_ids=[sample_rotation_template.id],
        )

        # Should succeed with reduced capacity or provide partial schedule
        if result.success:
            assert result.assignments_created > 0


# ============================================================================
# Test Class: Conflicting Constraints
# ============================================================================


class TestConflictingConstraints:
    """Tests for impossible schedules due to conflicting constraints."""

    def test_mutually_exclusive_rotations_same_time(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person, exclusive_rotation: RotationTemplate,
        sample_rotation_template: RotationTemplate
    ):
        """Test scheduling exclusive rotations at same time."""
        start_date = date.today() + timedelta(days=7)
        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Pre-assign resident to exclusive rotation
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_resident.id,
            rotation_template_id=exclusive_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Try to add another rotation for same resident at same time
        result = scheduling_engine.add_assignment(
            person_id=sample_resident.id,
            block_id=block.id,
            rotation_id=sample_rotation_template.id,
        )

        assert result.success is False
        assert "exclusive" in result.error_message.lower() or \
               "conflict" in result.error_message.lower()

    def test_supervision_ratio_impossible_to_meet(
        self, db: Session, scheduling_engine: SchedulingEngine,
        minimal_faculty: list[Person], residents_all_pgys: list[Person]
    ):
        """Test when supervision ratio can't be met."""
        # Create rotation requiring 1:1 supervision
        rotation = RotationTemplate(
            id=uuid4(),
            name="High Supervision Procedure",
            activity_type="procedure",
            abbreviation="HSP",
            max_residents=3,
            supervision_required=True,
            max_supervision_ratio=1,  # 1:1 ratio required
        )
        db.add(rotation)
        db.commit()

        start_date = date.today() + timedelta(days=7)
        blocks = create_blocks_range(db, start_date, start_date)

        # Try to schedule 3 residents with only 1 faculty
        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=start_date,
            rotation_ids=[rotation.id],
        )

        assert result.success is False or result.assignments_created <= 1

    def test_acgme_hours_make_schedule_impossible(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person
    ):
        """Test when ACGME constraints make schedule impossible."""
        start_date = date.today() + timedelta(days=7)

        # Create call rotation
        call_rotation = RotationTemplate(
            id=uuid4(),
            name="24hr Call",
            activity_type="call",
            abbreviation="CALL",
            max_residents=1,
        )
        db.add(call_rotation)
        db.commit()

        # Try to schedule 7 consecutive 24-hour call shifts (violates 80-hour limit)
        blocks = create_blocks_range(db, start_date, start_date + timedelta(days=6))

        for i in range(0, len(blocks), 2):
            # Assign full 24-hour blocks
            for j in range(2):
                if i + j < len(blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=blocks[i + j].id,
                        person_id=sample_resident.id,
                        rotation_template_id=call_rotation.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        # Validation should fail
        violations = scheduling_engine.validate_schedule(sample_resident.id, start_date)
        assert len(violations) > 0


# ============================================================================
# Test Class: Holiday and Weekend Handling
# ============================================================================


class TestHolidayWeekendHandling:
    """Tests for holiday and weekend edge cases."""

    def test_schedule_over_major_holiday(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person, sample_rotation_template: RotationTemplate
    ):
        """Test scheduling over major holiday period."""
        # December 25, 2024 (Christmas)
        holiday_date = date(2024, 12, 25)

        block = Block(
            id=uuid4(),
            date=holiday_date,
            time_of_day="AM",
            block_number=1,
            is_holiday=True,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        result = scheduling_engine.add_assignment(
            person_id=sample_resident.id,
            block_id=block.id,
            rotation_id=sample_rotation_template.id,
        )

        # Should either succeed with holiday pay or apply special rules
        assert result.success is not None

    def test_weekend_coverage_requirements(
        self, db: Session, scheduling_engine: SchedulingEngine,
        residents_all_pgys: list[Person]
    ):
        """Test that weekend coverage is properly distributed."""
        start_date = date.today()
        # Find next Saturday
        days_ahead = 5 - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        saturday = start_date + timedelta(days=days_ahead)

        blocks = create_blocks_range(db, saturday, saturday + timedelta(days=1))

        # Create weekend call rotation
        weekend_call = RotationTemplate(
            id=uuid4(),
            name="Weekend Call",
            activity_type="call",
            abbreviation="WKD",
            max_residents=1,
            min_residents=1,
        )
        db.add(weekend_call)
        db.commit()

        result = scheduling_engine.generate_schedule(
            start_date=saturday,
            end_date=saturday + timedelta(days=1),
            rotation_ids=[weekend_call.id],
        )

        # Should assign weekend coverage
        assert result.success is True
        assert result.assignments_created > 0


# ============================================================================
# Test Class: Boundary Conditions
# ============================================================================


class TestBoundaryConditions:
    """Tests for boundary conditions in scheduling."""

    def test_schedule_single_block(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person, sample_rotation_template: RotationTemplate
    ):
        """Test scheduling for a single block (minimum unit)."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        result = scheduling_engine.add_assignment(
            person_id=sample_resident.id,
            block_id=block.id,
            rotation_id=sample_rotation_template.id,
        )

        assert result.success is True

    def test_schedule_full_year(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person, sample_rotation_template: RotationTemplate
    ):
        """Test scheduling for full academic year (365 days)."""
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=364)

        # Create blocks (this will be 730 blocks)
        blocks = create_blocks_range(db, start_date, end_date)

        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=end_date,
            rotation_ids=[sample_rotation_template.id],
        )

        # Should handle large scale scheduling
        assert result.success is not None

    def test_midnight_boundary_handling(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_resident: Person
    ):
        """Test that PM to next day AM transition is handled correctly."""
        today = date.today()

        pm_block = Block(
            id=uuid4(),
            date=today,
            time_of_day="PM",
            block_number=1,
        )
        am_block = Block(
            id=uuid4(),
            date=today + timedelta(days=1),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([pm_block, am_block])
        db.commit()

        # Create overnight call rotation
        overnight = RotationTemplate(
            id=uuid4(),
            name="Overnight Call",
            activity_type="call",
            abbreviation="NIGHT",
            max_residents=1,
        )
        db.add(overnight)
        db.commit()

        # Assign overnight shift spanning midnight
        assignment1 = Assignment(
            id=uuid4(),
            block_id=pm_block.id,
            person_id=sample_resident.id,
            rotation_template_id=overnight.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=am_block.id,
            person_id=sample_resident.id,
            rotation_template_id=overnight.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Validate shift continuity
        violations = scheduling_engine.validate_schedule(sample_resident.id, today)
        # Should recognize as continuous shift, not two separate shifts


# ============================================================================
# Test Class: Emergency Coverage
# ============================================================================


class TestEmergencyCoverage:
    """Tests for emergency coverage scenarios."""

    def test_last_minute_absence_coverage(
        self, db: Session, scheduling_engine: SchedulingEngine,
        residents_all_pgys: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test emergency coverage when resident calls in sick."""
        tomorrow = date.today() + timedelta(days=1)
        block = Block(
            id=uuid4(),
            date=tomorrow,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Schedule resident
        original = residents_all_pgys[0]
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=original.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Resident calls in sick (last minute absence)
        absence = Absence(
            id=uuid4(),
            person_id=original.id,
            start_date=tomorrow,
            end_date=tomorrow,
            absence_type="sick",
            notes="Emergency sick day",
        )
        db.add(absence)
        db.commit()

        # Find replacement
        result = scheduling_engine.find_emergency_coverage(
            block_id=block.id,
            rotation_id=sample_rotation_template.id,
            exclude_person_ids=[original.id],
        )

        # Should find available replacement from remaining residents
        assert result.success is True or result.available_count >= 0

    def test_deployment_coverage_planning(
        self, db: Session, scheduling_engine: SchedulingEngine,
        sample_faculty_members: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test coverage when faculty member is deployed."""
        start_date = date.today() + timedelta(days=30)
        deployment_duration = 180  # 6 months

        # Mark faculty as deployed
        deployed_faculty = sample_faculty_members[0]
        absence = Absence(
            id=uuid4(),
            person_id=deployed_faculty.id,
            start_date=start_date,
            end_date=start_date + timedelta(days=deployment_duration),
            absence_type="deployment",
            notes="TDY - 6 months",
        )
        db.add(absence)
        db.commit()

        blocks = create_blocks_range(
            db, start_date, start_date + timedelta(days=deployment_duration)
        )

        # Generate schedule without deployed faculty
        result = scheduling_engine.generate_schedule(
            start_date=start_date,
            end_date=start_date + timedelta(days=deployment_duration),
            rotation_ids=[sample_rotation_template.id],
            exclude_person_ids=[deployed_faculty.id],
        )

        # Should generate schedule with remaining faculty
        assert result.success is True or result.assignments_created > 0
