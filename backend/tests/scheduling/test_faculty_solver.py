"""
Tests for faculty half-day assignment generation in the global CP-SAT solver.

The global solver handles residents + faculty + call in one solve.
Faculty gets 56 half-day slots per block with activities: C, AT, PCAT, DO, OFF.

Constraints tested:
1. One activity per slot (mutual exclusivity)
2. Clinic limits by role (PD=0, APD=2, Core=4 per week)
3. PCAT/DO linkage to call (call => PCAT next AM, DO next PM)
4. Supervision ratio (ACGME: PGY-1 1:2, PGY-2/3 1:4)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import CPSATSolver


# =============================================================================
# Mock Objects (following existing test patterns)
# =============================================================================


class MockPerson:
    """Mock person for testing without database."""

    def __init__(
        self,
        person_id=None,
        name="Test Person",
        person_type="resident",
        pgy_level=None,
        faculty_role=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level
        self.faculty_role = faculty_role  # PD, APD, core, etc.


class MockBlock:
    """Mock block for testing without database."""

    def __init__(
        self,
        block_id=None,
        block_date=None,
        time_of_day="AM",
        is_weekend=False,
    ):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock rotation template for testing."""

    def __init__(
        self,
        template_id=None,
        name="Test Template",
        max_residents=None,
        requires_procedure_credential=False,
    ):
        self.id = template_id or uuid4()
        self.name = name
        self.max_residents = max_residents
        self.requires_procedure_credential = requires_procedure_credential


# =============================================================================
# Test Fixtures
# =============================================================================


def create_week_of_blocks(start_date=None):
    """Create blocks for a full week (Mon-Sun) with AM/PM slots."""
    start = start_date or date(2026, 3, 2)  # Monday
    blocks = []
    for i in range(7):
        current_date = start + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(
                block_date=current_date,
                time_of_day=time_of_day,
                is_weekend=is_weekend,
            )
            blocks.append(block)
    return blocks


def create_4_week_blocks(start_date=None):
    """Create 56 blocks (28 days x AM/PM) for a 4-week block."""
    start = start_date or date(2026, 3, 2)  # Monday
    blocks = []
    for i in range(28):
        current_date = start + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(
                block_date=current_date,
                time_of_day=time_of_day,
                is_weekend=is_weekend,
            )
            blocks.append(block)
    return blocks


def create_faculty(name="Dr. Faculty", faculty_role=None):
    """Create a faculty member with optional role."""
    return MockPerson(
        name=name,
        person_type="faculty",
        pgy_level=None,
        faculty_role=faculty_role,
    )


def create_resident(name="Dr. Resident", pgy_level=1):
    """Create a resident at specified PGY level."""
    return MockPerson(
        name=name,
        person_type="resident",
        pgy_level=pgy_level,
    )


def create_context_with_availability(residents, faculty, blocks, templates=None):
    """Create a SchedulingContext with full availability.

    Note: Solver requires at least one resident and template to not early-return.
    This helper adds a dummy resident if none provided.
    """
    if templates is None:
        templates = [MockTemplate(name="Clinic")]

    # Solver requires at least one resident to not early-return
    if not residents:
        residents = [create_resident("Dummy Resident", pgy_level=2)]

    start_date = min(b.date for b in blocks)
    end_date = max(b.date for b in blocks)

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        start_date=start_date,
        end_date=end_date,
    )

    # Set up availability for all persons
    for person in residents + faculty:
        context.availability[person.id] = {}
        for block in blocks:
            context.availability[person.id][block.id] = {
                "available": True,
                "replacement": None,
            }

    # Set up call-eligible faculty
    context.call_eligible_faculty = faculty
    context.call_eligible_faculty_idx = {f.id: i for i, f in enumerate(faculty)}

    return context


# =============================================================================
# Test Cases
# =============================================================================


class TestFaculty56Slots:
    """Test that each faculty gets exactly 56 half-day assignments."""

    def test_faculty_56_slots_per_block(self):
        """Each faculty should get 56 slots (28 days x 2 AM/PM)."""
        faculty = [create_faculty("Dr. Core")]
        blocks = create_4_week_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success, f"Solver failed: {result.status}"
        assert result.faculty_half_day_assignments is not None

        # Count assignments for this faculty
        faculty_assignments = [
            a for a in result.faculty_half_day_assignments if a[0] == faculty[0].id
        ]
        assert len(faculty_assignments) == 56, (
            f"Expected 56 slots, got {len(faculty_assignments)}"
        )

    def test_multiple_faculty_each_get_56_slots(self):
        """Multiple faculty should each get 56 slots."""
        faculty = [
            create_faculty("Dr. One"),
            create_faculty("Dr. Two"),
            create_faculty("Dr. Three"),
        ]
        blocks = create_4_week_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=15,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        for fac in faculty:
            fac_assignments = [
                a for a in result.faculty_half_day_assignments if a[0] == fac.id
            ]
            assert len(fac_assignments) == 56, (
                f"Faculty {fac.name} got {len(fac_assignments)} slots, expected 56"
            )


class TestOneActivityPerSlot:
    """Test that faculty can only have one activity per slot."""

    def test_no_duplicate_slots(self):
        """No duplicate (faculty_id, block_id) pairs in output."""
        faculty = [create_faculty("Dr. Core")]
        blocks = create_4_week_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        # Check for duplicates
        seen = set()
        for fac_id, block_id, activity in result.faculty_half_day_assignments:
            key = (fac_id, block_id)
            assert key not in seen, f"Duplicate assignment found: {key}"
            seen.add(key)

    def test_activity_is_valid_type(self):
        """Activity must be one of: C, AT, PCAT, DO, OFF."""
        valid_activities = {"C", "AT", "PCAT", "DO", "OFF"}
        faculty = [create_faculty("Dr. Core")]
        blocks = create_4_week_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        for fac_id, block_id, activity in result.faculty_half_day_assignments:
            assert activity in valid_activities, (
                f"Invalid activity '{activity}' for faculty {fac_id}"
            )


class TestClinicLimits:
    """Test clinic session limits by faculty role."""

    def test_core_faculty_max_4_clinic_per_week(self):
        """Core faculty (default role) should have max 4 clinic sessions per week."""
        faculty = [create_faculty("Dr. Core", faculty_role=None)]  # Core is default
        blocks = create_week_of_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        # Count clinic assignments
        clinic_count = sum(
            1
            for fac_id, _, activity in result.faculty_half_day_assignments
            if fac_id == faculty[0].id and activity == "C"
        )
        assert clinic_count <= 4, (
            f"Core faculty has {clinic_count} clinic sessions, max is 4"
        )

    def test_pd_zero_clinic(self):
        """Program Director should have 0 clinic sessions."""
        faculty = [create_faculty("Dr. PD", faculty_role="program_director")]
        blocks = create_week_of_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        clinic_count = sum(
            1
            for fac_id, _, activity in result.faculty_half_day_assignments
            if fac_id == faculty[0].id and activity == "C"
        )
        assert clinic_count == 0, (
            f"PD has {clinic_count} clinic sessions, should be 0"
        )

    def test_apd_max_2_clinic_per_week(self):
        """APD should have max 2 clinic sessions per week."""
        faculty = [create_faculty("Dr. APD", faculty_role="assistant_program_director")]
        blocks = create_week_of_blocks()
        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        assert result.faculty_half_day_assignments is not None

        clinic_count = sum(
            1
            for fac_id, _, activity in result.faculty_half_day_assignments
            if fac_id == faculty[0].id and activity == "C"
        )
        assert clinic_count <= 2, (
            f"APD has {clinic_count} clinic sessions, max is 2"
        )


class TestPCATDOLinkage:
    """Test PCAT/DO linkage to call assignments."""

    def test_call_implies_pcat_next_am(self):
        """Faculty on call should have PCAT the next morning."""
        faculty = [create_faculty("Dr. Call")]
        # Create blocks spanning call night and next day
        start = date(2026, 3, 2)  # Monday
        blocks = []
        for i in range(3):  # Mon, Tue, Wed
            d = start + timedelta(days=i)
            for tod in ["AM", "PM"]:
                blocks.append(MockBlock(block_date=d, time_of_day=tod, is_weekend=False))

        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success

        # If there's a call assignment, check PCAT linkage
        if result.call_assignments:
            for person_id, block_id, call_type in result.call_assignments:
                if person_id == faculty[0].id:
                    # Find the call block date
                    call_block = next(b for b in blocks if b.id == block_id)
                    next_date = call_block.date + timedelta(days=1)

                    # Find next AM block
                    next_am_block = next(
                        (b for b in blocks if b.date == next_date and b.time_of_day == "AM"),
                        None,
                    )
                    if next_am_block:
                        # Check for PCAT
                        pcat_found = any(
                            fac_id == faculty[0].id
                            and blk_id == next_am_block.id
                            and activity == "PCAT"
                            for fac_id, blk_id, activity in result.faculty_half_day_assignments
                        )
                        assert pcat_found, (
                            f"Call on {call_block.date} should have PCAT on {next_date} AM"
                        )

    def test_call_implies_do_next_pm(self):
        """Faculty on call should have DO the next afternoon."""
        faculty = [create_faculty("Dr. Call")]
        start = date(2026, 3, 2)  # Monday
        blocks = []
        for i in range(3):
            d = start + timedelta(days=i)
            for tod in ["AM", "PM"]:
                blocks.append(MockBlock(block_date=d, time_of_day=tod, is_weekend=False))

        context = create_context_with_availability([], faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=10,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success

        if result.call_assignments:
            for person_id, block_id, call_type in result.call_assignments:
                if person_id == faculty[0].id:
                    call_block = next(b for b in blocks if b.id == block_id)
                    next_date = call_block.date + timedelta(days=1)

                    next_pm_block = next(
                        (b for b in blocks if b.date == next_date and b.time_of_day == "PM"),
                        None,
                    )
                    if next_pm_block:
                        do_found = any(
                            fac_id == faculty[0].id
                            and blk_id == next_pm_block.id
                            and activity == "DO"
                            for fac_id, blk_id, activity in result.faculty_half_day_assignments
                        )
                        assert do_found, (
                            f"Call on {call_block.date} should have DO on {next_date} PM"
                        )


class TestSupervisionRatio:
    """Test ACGME supervision ratios."""

    def test_supervision_with_pgy1_residents(self):
        """
        With PGY-1 residents in clinic, supervision ratio should be met.
        ACGME: 1 faculty per 2 PGY-1 residents.
        """
        # 4 PGY-1 residents need at least 2 supervising faculty
        residents = [create_resident(f"Intern {i}", pgy_level=1) for i in range(4)]
        faculty = [create_faculty(f"Dr. {i}") for i in range(3)]
        blocks = create_week_of_blocks()
        template = MockTemplate(name="Clinic")

        context = create_context_with_availability(residents, faculty, blocks, [template])

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=15,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        # The solver should produce a solution that meets supervision requirements
        # Detailed verification would require checking per-slot ratios

    def test_supervision_with_pgy23_residents(self):
        """
        With PGY-2/3 residents in clinic, supervision ratio should be met.
        ACGME: 1 faculty per 4 PGY-2/3 residents.
        """
        # 4 PGY-2/3 residents need at least 1 supervising faculty
        residents = [create_resident(f"Senior {i}", pgy_level=2) for i in range(4)]
        faculty = [create_faculty(f"Dr. {i}") for i in range(2)]
        blocks = create_week_of_blocks()
        template = MockTemplate(name="Clinic")

        context = create_context_with_availability(residents, faculty, blocks, [template])

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=15,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success
        # The solver should produce a solution that meets supervision requirements


# =============================================================================
# Integration Tests
# =============================================================================


class TestFacultySolverIntegration:
    """Integration tests for the full faculty solver pipeline."""

    def test_solver_produces_complete_faculty_schedule(self):
        """Full solve should produce assignments for all faculty and all blocks."""
        faculty = [
            create_faculty("Dr. Core"),
            create_faculty("Dr. PD", faculty_role="program_director"),
            create_faculty("Dr. APD", faculty_role="assistant_program_director"),
        ]
        residents = [create_resident(f"Resident {i}", pgy_level=(i % 3) + 1) for i in range(6)]
        blocks = create_4_week_blocks()

        context = create_context_with_availability(residents, faculty, blocks)

        solver = CPSATSolver(
            constraint_manager=ConstraintManager(),
            timeout_seconds=30,
            num_workers=1,
        )
        result = solver.solve(context)

        assert result.success, f"Solver failed: {result.status}"
        assert result.faculty_half_day_assignments is not None

        # Verify total assignment count
        expected_total = len(faculty) * len(blocks)
        actual_total = len(result.faculty_half_day_assignments)
        assert actual_total == expected_total, (
            f"Expected {expected_total} faculty assignments, got {actual_total}"
        )

        # Verify statistics include faculty metrics
        assert "faculty_half_day_assignments" in result.statistics
        assert "faculty_activity_breakdown" in result.statistics
