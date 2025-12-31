"""Tests for additional high-priority constraints identified in Session 029 audit.

These constraints are critical ACGME compliance and call scheduling constraints
that needed expanded test coverage beyond basic smoke tests.

Constraints Tested:
    - EightyHourRuleConstraint: ACGME 80-hour work week limit (hard)
    - SupervisionRatioConstraint: ACGME faculty supervision ratios (hard)
    - OvernightCallCoverageConstraint: Call coverage enforcement (hard)
    - OneInSevenRuleConstraint: ACGME 1-in-7 day off rule (hard)
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import Mock
from collections import defaultdict

from app.scheduling.constraints.acgme import (
    EightyHourRuleConstraint,
    SupervisionRatioConstraint,
    OneInSevenRuleConstraint,
)
from app.scheduling.constraints.call_coverage import OvernightCallCoverageConstraint
from app.scheduling.constraints.base import (
    SchedulingContext,
    ConstraintPriority,
    ConstraintType,
)


# ============================================================================
# EightyHourRuleConstraint Tests
# ============================================================================


class TestEightyHourRuleConstraint:
    """Tests for ACGME 80-hour work week constraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = EightyHourRuleConstraint()

        assert constraint.name == "80HourRule"
        assert constraint.constraint_type == ConstraintType.DUTY_HOURS
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.enabled is True

        # Verify constants
        assert constraint.HOURS_PER_BLOCK == 6
        assert constraint.MAX_WEEKLY_HOURS == 80
        assert constraint.ROLLING_WEEKS == 4
        assert constraint.ROLLING_DAYS == 28

        # Max blocks calculation: (80 * 4) / 6 = 53.33 -> 53
        assert constraint.max_blocks_per_window == 53

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = EightyHourRuleConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))

    def test_validate_well_under_limit(self):
        """Test validation with hours well under 80/week."""
        constraint = EightyHourRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        # Create 4 weeks of blocks (28 days)
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(28):
            for time_of_day in ["AM", "PM"]:
                block = Mock()
                block.id = uuid4()
                block.date = start_date + timedelta(days=day_offset)
                block.time_of_day = time_of_day
                blocks.append(block)

        # Assign resident to 40 blocks (40 * 6 = 240 hours / 4 weeks = 60 hours/week)
        assignments = []
        for i in range(40):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_exactly_at_limit(self):
        """Test validation when exactly at 80 hours/week average."""
        constraint = EightyHourRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Jones"

        # Create 4 weeks of blocks
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(28):
            for time_of_day in ["AM", "PM"]:
                block = Mock()
                block.id = uuid4()
                block.date = start_date + timedelta(days=day_offset)
                block.time_of_day = time_of_day
                blocks.append(block)

        # Assign exactly 53 blocks (53 * 6 = 318 hours / 4 weeks = 79.5 hours/week)
        # This is the maximum allowed
        assignments = []
        for i in range(53):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should pass - at or just under the limit
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_over_limit(self):
        """Test validation when exceeding 80 hours/week."""
        constraint = EightyHourRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Overworked"

        # Create 4 weeks of blocks
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(28):
            for time_of_day in ["AM", "PM"]:
                block = Mock()
                block.id = uuid4()
                block.date = start_date + timedelta(days=day_offset)
                block.time_of_day = time_of_day
                blocks.append(block)

        # Assign 56 blocks (56 * 6 = 336 hours / 4 weeks = 84 hours/week) - VIOLATION
        assignments = []
        for i in range(56):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "80HourRule"
        assert violation.severity == "CRITICAL"
        assert "84.0 hours/week" in violation.message
        assert violation.person_id == resident.id
        assert violation.details["average_weekly_hours"] == 84.0
        assert violation.details["max_weekly_hours"] == 80

    def test_validate_rolling_window_violation(self):
        """Test that rolling 4-week window catches violations."""
        constraint = EightyHourRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Burnout"

        # Create 8 weeks of blocks
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(56):  # 8 weeks
            for time_of_day in ["AM", "PM"]:
                block = Mock()
                block.id = uuid4()
                block.date = start_date + timedelta(days=day_offset)
                block.time_of_day = time_of_day
                blocks.append(block)

        # Create assignments that violate in the middle 4-week window
        # First 2 weeks: light (20 blocks)
        # Middle 4 weeks: heavy (60 blocks = 90 hours/week average)
        # Last 2 weeks: light (20 blocks)
        assignments = []

        # First 2 weeks: 20 blocks
        for i in range(20):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        # Middle 4 weeks (days 14-41): 60 blocks
        for i in range(28, 88):  # Block indices for middle period
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        # Last 2 weeks: 20 blocks
        for i in range(92, 112):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should detect violation in the middle rolling window
        assert result.satisfied is False
        assert len(result.violations) >= 1

        violation = result.violations[0]
        assert violation.constraint_name == "80HourRule"
        assert violation.severity == "CRITICAL"
        assert violation.details["average_weekly_hours"] > 80
        assert violation.details["window_days"] == 28

    def test_validate_empty_assignments(self):
        """Test validation with no assignments."""
        constraint = EightyHourRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. OnVacation"

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(28):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_residents(self):
        """Test that constraint validates each resident independently."""
        constraint = EightyHourRuleConstraint()

        resident1 = Mock()
        resident1.id = uuid4()
        resident1.name = "Dr. Normal"

        resident2 = Mock()
        resident2.id = uuid4()
        resident2.name = "Dr. Overworked"

        # Create 4 weeks of blocks
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(28):
            for time_of_day in ["AM", "PM"]:
                block = Mock()
                block.id = uuid4()
                block.date = start_date + timedelta(days=day_offset)
                block.time_of_day = time_of_day
                blocks.append(block)

        assignments = []

        # Resident 1: 40 blocks (60 hours/week - OK)
        for i in range(40):
            assignment = Mock()
            assignment.person_id = resident1.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        # Resident 2: 56 blocks (84 hours/week - VIOLATION)
        for i in range(56):
            assignment = Mock()
            assignment.person_id = resident2.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident1, resident2],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should have violation for resident2 only
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].person_id == resident2.id


# ============================================================================
# SupervisionRatioConstraint Tests
# ============================================================================


class TestSupervisionRatioConstraint:
    """Tests for ACGME supervision ratio constraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = SupervisionRatioConstraint()

        assert constraint.name == "SupervisionRatio"
        assert constraint.constraint_type == ConstraintType.SUPERVISION
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.enabled is True

        # Verify ratios
        assert constraint.PGY1_RATIO == 2  # 1 faculty per 2 PGY-1
        assert constraint.OTHER_RATIO == 4  # 1 faculty per 4 PGY-2/3

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = SupervisionRatioConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))
        assert callable(getattr(constraint, "calculate_required_faculty", None))

    def test_calculate_required_faculty_no_residents(self):
        """Test faculty calculation with no residents."""
        constraint = SupervisionRatioConstraint()

        result = constraint.calculate_required_faculty(0, 0)
        assert result == 0

    def test_calculate_required_faculty_pgy1_only(self):
        """Test faculty calculation for PGY-1 residents only."""
        constraint = SupervisionRatioConstraint()

        # 1 PGY-1 = 1 faculty (0.5 load)
        assert constraint.calculate_required_faculty(1, 0) == 1

        # 2 PGY-1 = 1 faculty (1.0 load)
        assert constraint.calculate_required_faculty(2, 0) == 1

        # 3 PGY-1 = 2 faculty (1.5 load)
        assert constraint.calculate_required_faculty(3, 0) == 2

        # 4 PGY-1 = 2 faculty (2.0 load)
        assert constraint.calculate_required_faculty(4, 0) == 2

        # 5 PGY-1 = 3 faculty (2.5 load)
        assert constraint.calculate_required_faculty(5, 0) == 3

    def test_calculate_required_faculty_pgy23_only(self):
        """Test faculty calculation for PGY-2/3 residents only."""
        constraint = SupervisionRatioConstraint()

        # 1-4 PGY-2/3 = 1 faculty
        assert constraint.calculate_required_faculty(0, 1) == 1
        assert constraint.calculate_required_faculty(0, 2) == 1
        assert constraint.calculate_required_faculty(0, 3) == 1
        assert constraint.calculate_required_faculty(0, 4) == 1

        # 5 PGY-2/3 = 2 faculty (1.25 load)
        assert constraint.calculate_required_faculty(0, 5) == 2

        # 8 PGY-2/3 = 2 faculty (2.0 load)
        assert constraint.calculate_required_faculty(0, 8) == 2

    def test_calculate_required_faculty_mixed(self):
        """Test faculty calculation for mixed PGY levels."""
        constraint = SupervisionRatioConstraint()

        # 1 PGY-1 + 1 PGY-2: 0.5 + 0.25 = 0.75 → 1 faculty
        assert constraint.calculate_required_faculty(1, 1) == 1

        # 1 PGY-1 + 2 PGY-2: 0.5 + 0.5 = 1.0 → 1 faculty
        assert constraint.calculate_required_faculty(1, 2) == 1

        # 1 PGY-1 + 3 PGY-2: 0.5 + 0.75 = 1.25 → 2 faculty
        assert constraint.calculate_required_faculty(1, 3) == 2

        # 2 PGY-1 + 4 PGY-2: 1.0 + 1.0 = 2.0 → 2 faculty
        assert constraint.calculate_required_faculty(2, 4) == 2

        # 3 PGY-1 + 4 PGY-2: 1.5 + 1.0 = 2.5 → 3 faculty
        assert constraint.calculate_required_faculty(3, 4) == 3

    def test_validate_adequate_supervision_pgy1(self):
        """Test validation with adequate supervision for PGY-1."""
        constraint = SupervisionRatioConstraint()

        pgy1_resident1 = Mock()
        pgy1_resident1.id = uuid4()
        pgy1_resident1.name = "PGY1-01"
        pgy1_resident1.pgy_level = 1

        pgy1_resident2 = Mock()
        pgy1_resident2.id = uuid4()
        pgy1_resident2.name = "PGY1-02"
        pgy1_resident2.pgy_level = 1

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. Supervisor"

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # 2 PGY-1 residents + 1 faculty (meets 1:2 ratio)
        assignments = []
        for resident in [pgy1_resident1, pgy1_resident2]:
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = block.id
            assignments.append(assignment)

        faculty_assignment = Mock()
        faculty_assignment.person_id = faculty.id
        faculty_assignment.block_id = block.id
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=[pgy1_resident1, pgy1_resident2],
            faculty=[faculty],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_inadequate_supervision_pgy1(self):
        """Test validation with inadequate supervision for PGY-1."""
        constraint = SupervisionRatioConstraint()

        pgy1_resident1 = Mock()
        pgy1_resident1.id = uuid4()
        pgy1_resident1.name = "PGY1-01"
        pgy1_resident1.pgy_level = 1

        pgy1_resident2 = Mock()
        pgy1_resident2.id = uuid4()
        pgy1_resident2.name = "PGY1-02"
        pgy1_resident2.pgy_level = 1

        pgy1_resident3 = Mock()
        pgy1_resident3.id = uuid4()
        pgy1_resident3.name = "PGY1-03"
        pgy1_resident3.pgy_level = 1

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. Supervisor"

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # 3 PGY-1 residents + 1 faculty (violates 1:2 ratio - need 2 faculty)
        assignments = []
        for resident in [pgy1_resident1, pgy1_resident2, pgy1_resident3]:
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = block.id
            assignments.append(assignment)

        faculty_assignment = Mock()
        faculty_assignment.person_id = faculty.id
        faculty_assignment.block_id = block.id
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=[pgy1_resident1, pgy1_resident2, pgy1_resident3],
            faculty=[faculty],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "SupervisionRatio"
        assert violation.severity == "CRITICAL"
        assert "needs 2 faculty but has 1" in violation.message
        assert violation.block_id == block.id
        assert violation.details["residents"] == 3
        assert violation.details["pgy1_count"] == 3
        assert violation.details["faculty"] == 1
        assert violation.details["required"] == 2

    def test_validate_adequate_supervision_mixed(self):
        """Test validation with mixed PGY levels and adequate supervision."""
        constraint = SupervisionRatioConstraint()

        pgy1 = Mock()
        pgy1.id = uuid4()
        pgy1.name = "PGY1-01"
        pgy1.pgy_level = 1

        pgy2 = Mock()
        pgy2.id = uuid4()
        pgy2.name = "PGY2-01"
        pgy2.pgy_level = 2

        pgy3 = Mock()
        pgy3.id = uuid4()
        pgy3.name = "PGY3-01"
        pgy3.pgy_level = 3

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. Supervisor"

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # 1 PGY-1 + 2 PGY-2/3 + 1 faculty
        # Load: 0.5 + 0.25 + 0.25 = 1.0 → 1 faculty required ✓
        assignments = []
        for resident in [pgy1, pgy2, pgy3]:
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = block.id
            assignments.append(assignment)

        faculty_assignment = Mock()
        faculty_assignment.person_id = faculty.id
        faculty_assignment.block_id = block.id
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=[pgy1, pgy2, pgy3],
            faculty=[faculty],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_faculty_assigned(self):
        """Test validation when no faculty are assigned."""
        constraint = SupervisionRatioConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "PGY1-01"
        resident.pgy_level = 1

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # 1 resident, 0 faculty (violation)
        assignment = Mock()
        assignment.person_id = resident.id
        assignment.block_id = block.id

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "SupervisionRatio"
        assert violation.severity == "CRITICAL"
        assert "needs 1 faculty but has 0" in violation.message

    def test_validate_multiple_blocks_independently(self):
        """Test that supervision is validated per block."""
        constraint = SupervisionRatioConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "PGY1-01"
        resident.pgy_level = 1

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. Supervisor"

        block1 = Mock()
        block1.id = uuid4()
        block1.date = date.today()

        block2 = Mock()
        block2.id = uuid4()
        block2.date = date.today() + timedelta(days=1)

        # Block 1: Resident + Faculty (OK)
        r1_assignment = Mock()
        r1_assignment.person_id = resident.id
        r1_assignment.block_id = block1.id

        f1_assignment = Mock()
        f1_assignment.person_id = faculty.id
        f1_assignment.block_id = block1.id

        # Block 2: Resident only (VIOLATION)
        r2_assignment = Mock()
        r2_assignment.person_id = resident.id
        r2_assignment.block_id = block2.id

        assignments = [r1_assignment, f1_assignment, r2_assignment]

        context = SchedulingContext(
            residents=[resident],
            faculty=[faculty],
            blocks=[block1, block2],
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should have violation for block2
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].block_id == block2.id

    def test_validate_empty_assignments(self):
        """Test validation with no assignments."""
        constraint = SupervisionRatioConstraint()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# OvernightCallCoverageConstraint Tests
# ============================================================================


class TestOvernightCallCoverageConstraint:
    """Tests for overnight call coverage constraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = OvernightCallCoverageConstraint()

        assert constraint.name == "OvernightCallCoverage"
        assert constraint.constraint_type == ConstraintType.CALL
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.enabled is True

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = OvernightCallCoverageConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))

    def test_validate_proper_coverage_all_nights(self):
        """Test validation when all required nights have exactly one call."""
        constraint = OvernightCallCoverageConstraint()

        faculty1 = Mock()
        faculty1.id = uuid4()
        faculty1.name = "Dr. OnCall1"

        faculty2 = Mock()
        faculty2.id = uuid4()
        faculty2.name = "Dr. OnCall2"

        # Sunday through Thursday (5 call nights)
        sunday = date(2025, 1, 5)  # Sunday
        blocks = []
        for day_offset in range(5):  # Sun-Thu
            block = Mock()
            block.id = uuid4()
            block.date = sunday + timedelta(days=day_offset)
            block.time_of_day = "AM"
            blocks.append(block)

        # Create call assignments (one per night)
        assignments = []
        for i, block in enumerate(blocks):
            assignment = Mock()
            assignment.person_id = faculty1.id if i % 2 == 0 else faculty2.id
            assignment.block_id = block.id
            assignment.call_type = "overnight"
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[faculty1, faculty2],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_missing_call_coverage(self):
        """Test validation when a night has no call coverage."""
        constraint = OvernightCallCoverageConstraint()

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. OnCall"

        # Sunday through Thursday
        sunday = date(2025, 1, 5)
        blocks = []
        for day_offset in range(5):
            block = Mock()
            block.id = uuid4()
            block.date = sunday + timedelta(days=day_offset)
            block.time_of_day = "AM"
            blocks.append(block)

        # Only assign 4 nights (skip Wednesday)
        assignments = []
        for i, block in enumerate(blocks):
            if i == 3:  # Skip Wednesday
                continue
            assignment = Mock()
            assignment.person_id = faculty.id
            assignment.block_id = block.id
            assignment.call_type = "overnight"
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "OvernightCallCoverage"
        assert violation.severity == "CRITICAL"
        assert "No overnight call coverage" in violation.message
        assert violation.details["actual"] == 0
        assert violation.details["expected"] == 1

    def test_validate_double_coverage(self):
        """Test validation when a night has multiple call assignments."""
        constraint = OvernightCallCoverageConstraint()

        faculty1 = Mock()
        faculty1.id = uuid4()
        faculty1.name = "Dr. OnCall1"

        faculty2 = Mock()
        faculty2.id = uuid4()
        faculty2.name = "Dr. OnCall2"

        # Monday night
        monday = date(2025, 1, 6)  # Monday
        block = Mock()
        block.id = uuid4()
        block.date = monday
        block.time_of_day = "AM"

        # Two faculty assigned to same night (violation)
        assignment1 = Mock()
        assignment1.person_id = faculty1.id
        assignment1.block_id = block.id
        assignment1.call_type = "overnight"

        assignment2 = Mock()
        assignment2.person_id = faculty2.id
        assignment2.block_id = block.id
        assignment2.call_type = "overnight"

        context = SchedulingContext(
            residents=[],
            faculty=[faculty1, faculty2],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate([assignment1, assignment2], context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "OvernightCallCoverage"
        assert violation.severity == "CRITICAL"
        assert "Multiple overnight call" in violation.message
        assert violation.details["actual"] == 2

    def test_validate_friday_saturday_excluded(self):
        """Test that Friday and Saturday are not checked (FMIT handles)."""
        constraint = OvernightCallCoverageConstraint()

        # Friday and Saturday (should be ignored)
        friday = date(2025, 1, 10)  # Friday
        saturday = date(2025, 1, 11)  # Saturday

        blocks = []
        for day_offset in range(2):
            block = Mock()
            block.id = uuid4()
            block.date = friday + timedelta(days=day_offset)
            block.time_of_day = "AM"
            blocks.append(block)

        # No call assignments for Fri/Sat
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)

        # Should be satisfied (Fri/Sat not checked)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_ignores_non_overnight_assignments(self):
        """Test that non-overnight assignments are ignored."""
        constraint = OvernightCallCoverageConstraint()

        faculty = Mock()
        faculty.id = uuid4()
        faculty.name = "Dr. Clinic"

        monday = date(2025, 1, 6)  # Monday
        block = Mock()
        block.id = uuid4()
        block.date = monday
        block.time_of_day = "AM"

        # Regular assignment (not overnight call)
        assignment = Mock()
        assignment.person_id = faculty.id
        assignment.block_id = block.id
        assignment.call_type = None  # Not an overnight call

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate([assignment], context)

        # Should have violation (no overnight call found)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "No overnight call coverage" in result.violations[0].message

    def test_validate_empty_assignments(self):
        """Test validation with no assignments."""
        constraint = OvernightCallCoverageConstraint()

        monday = date(2025, 1, 6)
        block = Mock()
        block.id = uuid4()
        block.date = monday
        block.time_of_day = "AM"

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[],
        )

        result = constraint.validate([], context)

        # Should have violation (Monday requires call)
        assert result.satisfied is False
        assert len(result.violations) == 1


# ============================================================================
# OneInSevenRuleConstraint Tests
# ============================================================================


class TestOneInSevenRuleConstraint:
    """Tests for ACGME 1-in-7 day off rule constraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = OneInSevenRuleConstraint()

        assert constraint.name == "1in7Rule"
        assert constraint.constraint_type == ConstraintType.CONSECUTIVE_DAYS
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.enabled is True
        assert constraint.MAX_CONSECUTIVE_DAYS == 6

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = OneInSevenRuleConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))

    def test_validate_within_limit(self):
        """Test validation when resident works 5 consecutive days."""
        constraint = OneInSevenRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Rested"

        # Create 7 days of blocks
        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(7):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        # Work 5 consecutive days, then 2 days off
        assignments = []
        for i in range(5):  # Days 0-4
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_exactly_at_limit(self):
        """Test validation when resident works exactly 6 consecutive days."""
        constraint = OneInSevenRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. AtLimit"

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(7):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        # Work exactly 6 consecutive days
        assignments = []
        for i in range(6):  # Days 0-5
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should pass - 6 consecutive is the maximum allowed
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_over_limit(self):
        """Test validation when resident works 7+ consecutive days."""
        constraint = OneInSevenRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Overworked"

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(8):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        # Work 7 consecutive days (violation)
        assignments = []
        for i in range(7):
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1

        violation = result.violations[0]
        assert violation.constraint_name == "1in7Rule"
        assert violation.severity == "HIGH"
        assert "7 consecutive duty days" in violation.message
        assert violation.person_id == resident.id
        assert violation.details["consecutive_days"] == 7

    def test_validate_pattern_with_breaks(self):
        """Test that days off reset the consecutive counter."""
        constraint = OneInSevenRuleConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Balanced"

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(14):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        # Pattern: 5 days on, 1 day off, 5 days on, 1 day off
        work_days = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13]
        assignments = []
        for day_idx in work_days:
            assignment = Mock()
            assignment.person_id = resident.id
            assignment.block_id = blocks[day_idx].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should pass - max consecutive is 5 days
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_empty_assignments(self):
        """Test validation with no assignments."""
        constraint = OneInSevenRuleConstraint()

        resident = Mock()
        resident.id = uuid4()

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(7):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_residents_independent(self):
        """Test that each resident is validated independently."""
        constraint = OneInSevenRuleConstraint()

        resident1 = Mock()
        resident1.id = uuid4()
        resident1.name = "Dr. GoodSchedule"

        resident2 = Mock()
        resident2.id = uuid4()
        resident2.name = "Dr. BadSchedule"

        start_date = date(2025, 1, 1)
        blocks = []
        for day_offset in range(8):
            block = Mock()
            block.id = uuid4()
            block.date = start_date + timedelta(days=day_offset)
            blocks.append(block)

        assignments = []

        # Resident 1: 5 consecutive days (OK)
        for i in range(5):
            assignment = Mock()
            assignment.person_id = resident1.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        # Resident 2: 7 consecutive days (VIOLATION)
        for i in range(7):
            assignment = Mock()
            assignment.person_id = resident2.id
            assignment.block_id = blocks[i].id
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[resident1, resident2],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should have violation for resident2 only
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].person_id == resident2.id
        assert result.violations[0].details["consecutive_days"] == 7
