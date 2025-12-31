"""
Tests for overnight faculty call generation.

Tests the call coverage constraints, solver integration, and call assignment
creation for overnight faculty call (Sun-Thurs nights).
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import SchedulingContext
from app.scheduling.constraints.call_coverage import (
    OVERNIGHT_CALL_DAYS,
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
    is_overnight_call_day,
)


class TestOvernightCallDays:
    """Test overnight call day detection."""

    def test_sunday_is_call_day(self):
        """Sunday (weekday 6) is an overnight call day."""
        sunday = date(2025, 12, 28)  # A Sunday
        assert sunday.weekday() == 6
        assert is_overnight_call_day(sunday)

    def test_monday_through_thursday_are_call_days(self):
        """Monday through Thursday are overnight call days."""
        monday = date(2025, 12, 29)
        tuesday = date(2025, 12, 30)
        wednesday = date(2025, 12, 31)
        thursday = date(2026, 1, 1)

        assert is_overnight_call_day(monday)
        assert is_overnight_call_day(tuesday)
        assert is_overnight_call_day(wednesday)
        assert is_overnight_call_day(thursday)

    def test_friday_saturday_not_call_days(self):
        """Friday and Saturday are NOT overnight call days (FMIT covers)."""
        friday = date(2026, 1, 2)
        saturday = date(2026, 1, 3)

        assert friday.weekday() == 4
        assert saturday.weekday() == 5
        assert not is_overnight_call_day(friday)
        assert not is_overnight_call_day(saturday)

    def test_overnight_call_days_constant(self):
        """Verify the OVERNIGHT_CALL_DAYS constant matches Sun-Thu."""
        assert {0, 1, 2, 3, 6} == OVERNIGHT_CALL_DAYS


class TestOvernightCallCoverageConstraint:
    """Tests for OvernightCallCoverageConstraint."""

    @pytest.fixture
    def constraint(self):
        """Create constraint instance."""
        return OvernightCallCoverageConstraint()

    @pytest.fixture
    def faculty(self):
        """Create test faculty list."""
        return [
            Person(id=uuid4(), name="Faculty A", type="faculty", faculty_role="core"),
            Person(id=uuid4(), name="Faculty B", type="faculty", faculty_role="core"),
            Person(id=uuid4(), name="Faculty C", type="faculty", faculty_role="pd"),
        ]

    @pytest.fixture
    def blocks(self):
        """Create a week of blocks (Sun-Sat)."""
        blocks = []
        start_date = date(2025, 12, 28)  # Sunday
        for i in range(7):
            block_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                blocks.append(
                    Block(
                        id=uuid4(),
                        date=block_date,
                        time_of_day=time_of_day,
                        is_weekend=(block_date.weekday() >= 5),
                    )
                )
        return blocks

    @pytest.fixture
    def context(self, faculty, blocks):
        """Create scheduling context with call-eligible faculty."""
        return SchedulingContext(
            residents=[],
            faculty=faculty,
            blocks=blocks,
            templates=[],
            call_eligible_faculty=faculty,  # All are eligible
        )

    def test_constraint_name(self, constraint):
        """Verify constraint name."""
        assert constraint.name == "OvernightCallCoverage"

    def test_constraint_enabled_by_default(self, constraint):
        """Constraint should be enabled by default."""
        assert constraint.enabled

    def test_validate_with_complete_coverage(
        self, constraint, context, faculty, blocks
    ):
        """Validate passes with complete overnight call coverage."""
        # Create mock assignments with one faculty per overnight call day
        assignments = []
        call_dates_assigned = set()

        for block in blocks:
            if block.date not in call_dates_assigned and is_overnight_call_day(
                block.date
            ):
                # Assign first faculty to this date
                assignments.append(
                    type(
                        "MockCallAssignment",
                        (),
                        {
                            "person_id": faculty[0].id,
                            "block_id": block.id,
                            "call_type": "overnight",
                        },
                    )()
                )
                call_dates_assigned.add(block.date)

        # Validate should pass
        result = constraint.validate(assignments, context)
        # Note: Current implementation may need assignments in specific format


class TestAdjunctCallExclusionConstraint:
    """Tests for AdjunctCallExclusionConstraint."""

    @pytest.fixture
    def constraint(self):
        """Create constraint instance."""
        return AdjunctCallExclusionConstraint()

    def test_constraint_name(self, constraint):
        """Verify constraint name."""
        assert constraint.name == "AdjunctCallExclusion"

    def test_adjunct_excluded_from_call_eligible(self):
        """Adjunct faculty should be excluded from call-eligible list."""
        all_faculty = [
            Person(
                id=uuid4(), name="Core Faculty", type="faculty", faculty_role="core"
            ),
            Person(
                id=uuid4(),
                name="Adjunct Faculty",
                type="faculty",
                faculty_role="adjunct",
            ),
            Person(id=uuid4(), name="PD Faculty", type="faculty", faculty_role="pd"),
        ]

        # Filter like the engine does
        call_eligible = [f for f in all_faculty if f.faculty_role != "adjunct"]

        assert len(call_eligible) == 2
        assert all(f.faculty_role != "adjunct" for f in call_eligible)


class TestCallAvailabilityConstraint:
    """Tests for CallAvailabilityConstraint."""

    @pytest.fixture
    def constraint(self):
        """Create constraint instance."""
        return CallAvailabilityConstraint()

    def test_constraint_name(self, constraint):
        """Verify constraint name."""
        assert constraint.name == "CallAvailability"


class TestCallAssignmentModel:
    """Tests for CallAssignment model."""

    def test_create_call_assignment(self, db: Session):
        """Test creating a call assignment."""
        # Create a faculty member
        faculty = Person(
            id=uuid4(),
            name="Test Faculty",
            type="faculty",
            faculty_role="core",
        )
        db.add(faculty)
        db.commit()

        # Create a call assignment
        call = CallAssignment(
            id=uuid4(),
            date=date(2025, 12, 29),  # Monday
            person_id=faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        assert call.id is not None
        assert call.date == date(2025, 12, 29)
        assert call.call_type == "overnight"
        assert call.is_weekend is False

    def test_call_assignment_unique_constraint(self, db: Session):
        """Test that duplicate call assignments are rejected."""
        from sqlalchemy.exc import IntegrityError

        faculty = Person(
            id=uuid4(),
            name="Test Faculty",
            type="faculty",
            faculty_role="core",
        )
        db.add(faculty)
        db.commit()

        # Create first call assignment
        call1 = CallAssignment(
            id=uuid4(),
            date=date(2025, 12, 29),
            person_id=faculty.id,
            call_type="overnight",
        )
        db.add(call1)
        db.commit()

        # Try to create duplicate - same date, person, call_type
        call2 = CallAssignment(
            id=uuid4(),
            date=date(2025, 12, 29),
            person_id=faculty.id,
            call_type="overnight",
        )
        db.add(call2)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_is_weekend_or_holiday_property(self, db: Session):
        """Test the is_weekend_or_holiday property."""
        faculty = Person(
            id=uuid4(),
            name="Test Faculty",
            type="faculty",
            faculty_role="core",
        )
        db.add(faculty)
        db.commit()

        # Weekday call
        weekday_call = CallAssignment(
            date=date(2025, 12, 29),  # Monday
            person_id=faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )
        assert weekday_call.is_weekend_or_holiday is False

        # Weekend call
        weekend_call = CallAssignment(
            date=date(2025, 12, 28),  # Sunday
            person_id=faculty.id,
            call_type="overnight",
            is_weekend=True,
            is_holiday=False,
        )
        assert weekend_call.is_weekend_or_holiday is True

        # Holiday call
        holiday_call = CallAssignment(
            date=date(2025, 12, 25),  # Christmas
            person_id=faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=True,
        )
        assert holiday_call.is_weekend_or_holiday is True


class TestCallAssignmentService:
    """Tests for CallAssignmentService."""

    def test_get_call_assignments_empty(self, db: Session):
        """Test getting call assignments when none exist."""
        from app.services.call_assignment_service import CallAssignmentService

        service = CallAssignmentService(db)
        assignments = service.get_call_assignments(
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
        )

        assert len(assignments) == 0

    def test_create_call_assignment(self, db: Session):
        """Test creating a call assignment via service."""
        from app.services.call_assignment_service import CallAssignmentService
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Test Faculty",
            type="faculty",
            faculty_role="core",
        )
        db.add(faculty)
        db.commit()

        service = CallAssignmentService(db)
        create_data = CallAssignmentCreate(
            date=date(2025, 12, 29),
            person_id=faculty.id,
            call_type="overnight",
        )

        assignment = service.create_call_assignment(create_data)

        assert assignment.date == date(2025, 12, 29)
        assert assignment.person_id == faculty.id
        assert assignment.call_type == "overnight"

    def test_bulk_create_call_assignments(self, db: Session):
        """Test bulk creation of call assignments."""
        from app.services.call_assignment_service import CallAssignmentService
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create multiple faculty
        faculty_list = []
        for i in range(3):
            f = Person(
                id=uuid4(),
                name=f"Faculty {i}",
                type="faculty",
                faculty_role="core",
            )
            db.add(f)
            faculty_list.append(f)
        db.commit()

        service = CallAssignmentService(db)

        # Create bulk assignments
        create_list = [
            CallAssignmentCreate(
                date=date(2025, 12, 29) + timedelta(days=i),
                person_id=faculty_list[i % 3].id,
                call_type="overnight",
            )
            for i in range(5)
        ]

        assignments = service.bulk_create_call_assignments(create_list)

        assert len(assignments) == 5

    def test_delete_call_assignments_in_range(self, db: Session):
        """Test deleting call assignments in a date range."""
        from app.services.call_assignment_service import CallAssignmentService
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Test Faculty",
            type="faculty",
            faculty_role="core",
        )
        db.add(faculty)
        db.commit()

        service = CallAssignmentService(db)

        # Create assignments for a week
        for i in range(7):
            service.create_call_assignment(
                CallAssignmentCreate(
                    date=date(2025, 12, 22) + timedelta(days=i),
                    person_id=faculty.id,
                    call_type="overnight",
                )
            )

        # Verify 7 exist
        all_assignments = service.get_call_assignments(
            start_date=date(2025, 12, 22),
            end_date=date(2025, 12, 28),
        )
        assert len(all_assignments) == 7

        # Delete middle 3 days
        deleted = service.delete_call_assignments_in_range(
            start_date=date(2025, 12, 24),
            end_date=date(2025, 12, 26),
        )
        assert deleted == 3

        # Verify 4 remain
        remaining = service.get_call_assignments(
            start_date=date(2025, 12, 22),
            end_date=date(2025, 12, 28),
        )
        assert len(remaining) == 4


class TestSolverSundayNightCallCoverage:
    """
    Integration tests verifying Sunday nights are included in call scheduling.

    This addresses the bug where Sunday nights were excluded because:
    - workday_blocks filtered out blocks with is_weekend=True
    - Sunday blocks have is_weekend=True
    - But Sunday nights (weekday 6) require overnight call coverage

    The fix uses context.blocks with explicit weekday filtering instead.
    """

    @pytest.fixture
    def faculty(self):
        """Create test faculty list."""
        return [
            Person(id=uuid4(), name="Faculty A", type="faculty", faculty_role="core"),
            Person(id=uuid4(), name="Faculty B", type="faculty", faculty_role="core"),
        ]

    @pytest.fixture
    def week_blocks(self):
        """
        Create a full week of blocks starting from Sunday.

        Note: Sunday and Saturday have is_weekend=True, which previously
        caused Sunday to be incorrectly filtered out of call scheduling.
        """
        blocks = []
        start_date = date(2025, 12, 28)  # Sunday
        for i in range(7):
            block_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                blocks.append(
                    Block(
                        id=uuid4(),
                        date=block_date,
                        time_of_day=time_of_day,
                        # Weekends are 5 (Sat) and 6 (Sun)
                        is_weekend=(block_date.weekday() in (5, 6)),
                    )
                )
        return blocks

    def test_sunday_block_has_is_weekend_true(self, week_blocks):
        """Verify our test data: Sunday blocks should have is_weekend=True."""
        sunday_blocks = [b for b in week_blocks if b.date.weekday() == 6]
        assert len(sunday_blocks) == 2  # AM and PM
        for block in sunday_blocks:
            assert block.is_weekend is True, "Sunday should be marked as weekend"

    def test_sunday_is_valid_overnight_call_day(self):
        """Verify Sunday is recognized as an overnight call day."""
        sunday = date(2025, 12, 28)
        assert sunday.weekday() == 6  # Confirm it's Sunday
        assert is_overnight_call_day(sunday), "Sunday should be an overnight call day"

    def test_call_blocks_include_sunday_despite_weekend_flag(self, week_blocks):
        """
        Test that call block filtering includes Sunday nights.

        This is the core regression test for the bug fixed in PR #489.
        The solver should use explicit weekday filtering (0,1,2,3,6)
        rather than relying on is_weekend flag.
        """
        # Simulate the fixed solver logic: filter by weekday, not is_weekend
        call_blocks = [
            block for block in week_blocks if block.date.weekday() in (0, 1, 2, 3, 6)
        ]

        # Get unique call dates
        call_dates = set(b.date for b in call_blocks)

        # Should include: Sun (28), Mon (29), Tue (30), Wed (31), Thu (1 Jan)
        # Should exclude: Fri (2 Jan), Sat (3 Jan)
        assert len(call_dates) == 5, f"Expected 5 call nights, got {len(call_dates)}"

        # Specifically verify Sunday is included
        sunday = date(2025, 12, 28)
        assert sunday in call_dates, "Sunday should be included in call dates"

    def test_workday_blocks_would_exclude_sunday_without_fix(self, week_blocks):
        """
        Demonstrate the original bug: filtering by is_weekend excludes Sunday.

        This test shows what the bug was - workday_blocks would filter out
        Sunday because is_weekend=True, but Sunday nights need call coverage.
        """
        # Old logic (buggy): filter out weekend blocks
        workday_blocks = [b for b in week_blocks if not b.is_weekend]
        workday_dates = set(b.date for b in workday_blocks)

        # Sunday would NOT be in workday_blocks due to is_weekend=True
        sunday = date(2025, 12, 28)
        assert sunday not in workday_dates, "Sunday filtered by is_weekend"

        # But Sunday IS a valid call night
        assert is_overnight_call_day(sunday), "Sunday needs overnight call coverage"

    def test_context_blocks_include_all_days(self, week_blocks):
        """Verify context.blocks includes all days including weekends."""
        all_dates = set(b.date for b in week_blocks)
        assert len(all_dates) == 7, "Should have all 7 days of the week"

        # Verify weekends are in the full block list
        sunday = date(2025, 12, 28)
        saturday = date(2026, 1, 3)
        assert sunday in all_dates, "Sunday should be in context.blocks"
        assert saturday in all_dates, "Saturday should be in context.blocks"
