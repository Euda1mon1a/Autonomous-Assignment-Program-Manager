"""
Tests for resident inpatient rotation constraints.

Tests the two inpatient constraints:
1. ResidentInpatientHeadcountConstraint - FMIT and Night Float headcount limits
2. FMITResidentClinicDayConstraint - PGY-specific clinic days for FMIT residents
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.inpatient import (
    FMITResidentClinicDayConstraint,
    ResidentInpatientHeadcountConstraint,
)


# ============================================================================
# Mock Classes for Testing
# ============================================================================


class MockPerson:
    """Mock person object for testing."""

    def __init__(
        self,
        person_id=None,
        name="Test Person",
        person_type="resident",
        pgy_level=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockBlock:
    """Mock block object for testing."""

    def __init__(self, block_id=None, block_date=None, time_of_day="AM"):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day


class MockRotationTemplate:
    """Mock rotation template for testing."""

    def __init__(self, template_id=None, name="Test Template"):
        self.id = template_id or uuid4()
        self.name = name


class MockAssignment:
    """Mock assignment object for testing."""

    def __init__(
        self,
        assignment_id=None,
        person_id=None,
        block_id=None,
        rotation_template_id=None,
    ):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = rotation_template_id


# ============================================================================
# Helper Functions
# ============================================================================


def create_residents_by_pgy(pgy_levels=None):
    """
    Create mock residents for specified PGY levels.

    Args:
        pgy_levels: List of PGY levels (defaults to [1, 2, 3])

    Returns:
        dict: {pgy_level: [residents]}
    """
    if pgy_levels is None:
        pgy_levels = [1, 2, 3]

    residents_by_pgy = {}
    for pgy in pgy_levels:
        # Create 2 residents per PGY level
        residents_by_pgy[pgy] = [
            MockPerson(
                name=f"PGY{pgy} Resident A",
                person_type="resident",
                pgy_level=pgy,
            ),
            MockPerson(
                name=f"PGY{pgy} Resident B",
                person_type="resident",
                pgy_level=pgy,
            ),
        ]

    return residents_by_pgy


def create_fmit_templates():
    """Create FMIT rotation templates."""
    return [
        MockRotationTemplate(name="FMIT Inpatient - PGY1"),
        MockRotationTemplate(name="FMIT Inpatient - PGY2"),
        MockRotationTemplate(name="FMIT Inpatient - PGY3"),
    ]


def create_night_float_templates():
    """Create Night Float rotation templates."""
    return [
        MockRotationTemplate(name="Night Float"),
        MockRotationTemplate(name="NF - General"),
    ]


def create_week_of_blocks(start_date=None):
    """
    Create blocks for a full week (AM and PM).

    Args:
        start_date: Starting date (defaults to today)

    Returns:
        list[MockBlock]: List of blocks covering one week
    """
    if start_date is None:
        start_date = date.today()

    blocks = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(block_date=current_date, time_of_day=time_of_day)
            blocks.append(block)

    return blocks


# ============================================================================
# Tests for ResidentInpatientHeadcountConstraint
# ============================================================================


class TestResidentInpatientHeadcountConstraint:
    """Tests for resident inpatient headcount constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = ResidentInpatientHeadcountConstraint()
        assert constraint.name == "ResidentInpatientHeadcount"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.FMIT_PER_PGY_PER_BLOCK == 1
        assert constraint.NF_CONCURRENT_MAX == 1

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_one_fmit_per_pgy_per_block_passes(self):
        """Test validate passes with exactly 1 FMIT per PGY per block."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        # Create one FMIT assignment per PGY level for first block
        first_block = blocks[0]
        assignments = []
        for pgy in [1, 2, 3]:
            resident = residents_by_pgy[pgy][0]
            assignments.append(
                MockAssignment(
                    person_id=resident.id,
                    block_id=first_block.id,
                    rotation_template_id=fmit_templates[pgy - 1].id,
                )
            )

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_fmit_same_pgy_same_block_fails(self):
        """Test validate fails when multiple residents from same PGY on FMIT in same block."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        first_block = blocks[0]

        # Assign TWO PGY-1 residents to FMIT in same block (violation)
        assignments = [
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[0].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PGY-1" in result.violations[0].message
        assert "FMIT" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"
        assert result.violations[0].details["pgy_level"] == 1
        assert result.violations[0].details["count"] == 2

    def test_validate_different_pgy_levels_same_block_passes(self):
        """Test validate passes when different PGY levels on FMIT in same block."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        first_block = blocks[0]

        # One resident from each PGY level - should be OK (3 total FMIT)
        assignments = [
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[2][0].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[1].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[3][0].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[2].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_one_night_float_per_block_passes(self):
        """Test validate passes with exactly 1 Night Float per block."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        nf_templates = create_night_float_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        # Assign one resident to Night Float for each block
        assignments = []
        for i, block in enumerate(blocks[:3]):  # Test first 3 blocks
            resident = residents_by_pgy[1][0]  # Use same resident for simplicity
            assignments.append(
                MockAssignment(
                    person_id=resident.id,
                    block_id=block.id,
                    rotation_template_id=nf_templates[0].id,
                )
            )

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=nf_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_night_float_same_block_fails(self):
        """Test validate fails when multiple residents on Night Float in same block."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        nf_templates = create_night_float_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        first_block = blocks[0]

        # Assign TWO residents to Night Float in same block (violation)
        assignments = [
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=first_block.id,
                rotation_template_id=nf_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[2][0].id,
                block_id=first_block.id,
                rotation_template_id=nf_templates[0].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=nf_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Night Float" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"
        assert result.violations[0].details["count"] == 2
        assert result.violations[0].details["max"] == 1

    def test_validate_mixed_fmit_and_nf_violations(self):
        """Test validate detects violations in both FMIT and Night Float."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()
        nf_templates = create_night_float_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        all_templates = fmit_templates + nf_templates

        first_block = blocks[0]
        second_block = blocks[1]

        assignments = [
            # Block 1: Two PGY-1 on FMIT (violation)
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=first_block.id,
                rotation_template_id=fmit_templates[0].id,
            ),
            # Block 2: Two residents on Night Float (violation)
            MockAssignment(
                person_id=residents_by_pgy[2][0].id,
                block_id=second_block.id,
                rotation_template_id=nf_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[3][0].id,
                block_id=second_block.id,
                rotation_template_id=nf_templates[0].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=all_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 2

        # Check violation messages
        violation_messages = [v.message for v in result.violations]
        assert any("PGY-1" in msg and "FMIT" in msg for msg in violation_messages)
        assert any("Night Float" in msg for msg in violation_messages)

    def test_get_fmit_template_ids(self):
        """Test _get_fmit_template_ids correctly identifies FMIT templates."""
        constraint = ResidentInpatientHeadcountConstraint()

        templates = [
            MockRotationTemplate(name="FMIT Inpatient"),
            MockRotationTemplate(name="fmit - ward"),
            MockRotationTemplate(name="Night Float"),  # Should be excluded
            MockRotationTemplate(name="Clinic"),  # Should be excluded
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=templates,
        )

        fmit_ids = constraint._get_fmit_template_ids(context)

        # Should only get the two FMIT templates (not Night Float)
        assert len(fmit_ids) == 2
        assert templates[0].id in fmit_ids
        assert templates[1].id in fmit_ids
        assert templates[2].id not in fmit_ids  # Night Float excluded
        assert templates[3].id not in fmit_ids  # Clinic excluded

    def test_get_nf_template_ids(self):
        """Test _get_nf_template_ids correctly identifies Night Float templates."""
        constraint = ResidentInpatientHeadcountConstraint()

        templates = [
            MockRotationTemplate(name="Night Float"),
            MockRotationTemplate(name="NF - General"),
            MockRotationTemplate(name="night shift rotation"),
            MockRotationTemplate(name="FMIT Inpatient"),  # Should be excluded
            MockRotationTemplate(name="Clinic"),  # Should be excluded
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=templates,
        )

        nf_ids = constraint._get_nf_template_ids(context)

        # Should get all three night/NF templates
        assert len(nf_ids) == 3
        assert templates[0].id in nf_ids
        assert templates[1].id in nf_ids
        assert templates[2].id in nf_ids
        assert templates[3].id not in nf_ids  # FMIT excluded
        assert templates[4].id not in nf_ids  # Clinic excluded

    def test_validate_no_templates_passes(self):
        """Test validate passes when no FMIT or NF templates exist."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        # Only clinic templates, no FMIT or NF
        templates = [
            MockRotationTemplate(name="General Clinic"),
            MockRotationTemplate(name="Procedures"),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=templates,
        )

        # Even with assignments, should pass since no FMIT/NF templates
        assignments = [
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=blocks[0].id,
                rotation_template_id=templates[0].id,
            )
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_resident_without_pgy_level(self):
        """Test validate handles residents without pgy_level attribute."""
        constraint = ResidentInpatientHeadcountConstraint()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        # Create resident without pgy_level
        resident_no_pgy = MockPerson(
            name="Resident No PGY",
            person_type="resident",
            pgy_level=None,
        )

        assignments = [
            MockAssignment(
                person_id=resident_no_pgy.id,
                block_id=blocks[0].id,
                rotation_template_id=fmit_templates[0].id,
            )
        ]

        context = SchedulingContext(
            residents=[resident_no_pgy],
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        # Should not cause error, resident is ignored if no PGY level
        result = constraint.validate(assignments, context)

        # Should pass - resident without PGY level is not counted
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_violations_same_pgy_different_blocks(self):
        """Test multiple violations for same PGY level across different blocks."""
        constraint = ResidentInpatientHeadcountConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        # Create violations in multiple blocks for PGY-1
        assignments = [
            # Block 0: Two PGY-1 (violation)
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=blocks[0].id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=blocks[0].id,
                rotation_template_id=fmit_templates[0].id,
            ),
            # Block 1: Two PGY-1 (violation)
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=blocks[1].id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=blocks[1].id,
                rotation_template_id=fmit_templates[0].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=fmit_templates,
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 2  # One per block

        # Both violations should be for PGY-1
        for violation in result.violations:
            assert violation.details["pgy_level"] == 1
            assert violation.details["count"] == 2


# ============================================================================
# Tests for FMITResidentClinicDayConstraint
# ============================================================================


class TestFMITResidentClinicDayConstraint:
    """Tests for FMIT resident clinic day constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = FMITResidentClinicDayConstraint()
        assert constraint.name == "FMITResidentClinicDay"
        assert constraint.constraint_type == ConstraintType.ROTATION
        assert constraint.priority == ConstraintPriority.HIGH

    def test_clinic_day_definitions(self):
        """Test that clinic days are defined correctly for each PGY level."""
        constraint = FMITResidentClinicDayConstraint()

        # PGY-1: Wednesday AM (weekday 2)
        assert constraint.FMIT_CLINIC_DAYS[1]["weekday"] == 2
        assert constraint.FMIT_CLINIC_DAYS[1]["time_of_day"] == "AM"

        # PGY-2: Tuesday PM (weekday 1)
        assert constraint.FMIT_CLINIC_DAYS[2]["weekday"] == 1
        assert constraint.FMIT_CLINIC_DAYS[2]["time_of_day"] == "PM"

        # PGY-3: Monday PM (weekday 0)
        assert constraint.FMIT_CLINIC_DAYS[3]["weekday"] == 0
        assert constraint.FMIT_CLINIC_DAYS[3]["time_of_day"] == "PM"

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = FMITResidentClinicDayConstraint()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        result = constraint.validate([], context)

        # Should pass - validation currently handled by pre-loading
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_with_assignments_passes(self):
        """Test validate passes with assignments (pre-loading handles rules)."""
        constraint = FMITResidentClinicDayConstraint()
        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        templates = create_fmit_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        # Create some assignments
        assignments = [
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=blocks[0].id,
                rotation_template_id=templates[0].id,
            )
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=templates,
        )

        result = constraint.validate(assignments, context)

        # Should pass - constraint is currently a placeholder
        # Pre-loading mechanism handles clinic day assignment
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_add_to_cpsat_no_error(self):
        """Test add_to_cpsat doesn't raise errors (currently a pass-through)."""
        constraint = FMITResidentClinicDayConstraint()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        # Should not raise an error
        try:
            constraint.add_to_cpsat(model=None, variables={}, context=context)
        except Exception as e:
            pytest.fail(f"add_to_cpsat raised unexpected exception: {e}")

    def test_add_to_pulp_no_error(self):
        """Test add_to_pulp doesn't raise errors (currently a pass-through)."""
        constraint = FMITResidentClinicDayConstraint()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        # Should not raise an error
        try:
            constraint.add_to_pulp(model=None, variables={}, context=context)
        except Exception as e:
            pytest.fail(f"add_to_pulp raised unexpected exception: {e}")


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestInpatientConstraintsIntegration:
    """Integration tests for combined inpatient constraints."""

    def test_complete_valid_week_all_constraints(self):
        """Test a complete valid week satisfying all inpatient constraints."""
        headcount_constraint = ResidentInpatientHeadcountConstraint()
        clinic_day_constraint = FMITResidentClinicDayConstraint()

        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()
        nf_templates = create_night_float_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        all_templates = fmit_templates + nf_templates

        # Valid assignments: 1 FMIT per PGY per block, 1 NF per block
        assignments = []

        # Day 1: One of each PGY on FMIT
        assignments.extend(
            [
                MockAssignment(
                    person_id=residents_by_pgy[1][0].id,
                    block_id=blocks[0].id,
                    rotation_template_id=fmit_templates[0].id,
                ),
                MockAssignment(
                    person_id=residents_by_pgy[2][0].id,
                    block_id=blocks[0].id,
                    rotation_template_id=fmit_templates[1].id,
                ),
                MockAssignment(
                    person_id=residents_by_pgy[3][0].id,
                    block_id=blocks[0].id,
                    rotation_template_id=fmit_templates[2].id,
                ),
            ]
        )

        # Day 1 PM: One resident on Night Float
        assignments.append(
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=blocks[1].id,
                rotation_template_id=nf_templates[0].id,
            )
        )

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=all_templates,
        )

        headcount_result = headcount_constraint.validate(assignments, context)
        clinic_day_result = clinic_day_constraint.validate(assignments, context)

        assert headcount_result.satisfied is True
        assert clinic_day_result.satisfied is True
        assert len(headcount_result.violations) == 0
        assert len(clinic_day_result.violations) == 0

    def test_complete_invalid_week_multiple_violations(self):
        """Test a week with multiple inpatient constraint violations."""
        headcount_constraint = ResidentInpatientHeadcountConstraint()

        residents_by_pgy = create_residents_by_pgy()
        blocks = create_week_of_blocks()
        fmit_templates = create_fmit_templates()
        nf_templates = create_night_float_templates()

        all_residents = []
        for residents in residents_by_pgy.values():
            all_residents.extend(residents)

        all_templates = fmit_templates + nf_templates

        assignments = [
            # Block 0: Two PGY-1 on FMIT (violation)
            MockAssignment(
                person_id=residents_by_pgy[1][0].id,
                block_id=blocks[0].id,
                rotation_template_id=fmit_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[1][1].id,
                block_id=blocks[0].id,
                rotation_template_id=fmit_templates[0].id,
            ),
            # Block 1: Two residents on Night Float (violation)
            MockAssignment(
                person_id=residents_by_pgy[2][0].id,
                block_id=blocks[1].id,
                rotation_template_id=nf_templates[0].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[2][1].id,
                block_id=blocks[1].id,
                rotation_template_id=nf_templates[0].id,
            ),
            # Block 2: Three PGY-2 on FMIT (violation)
            MockAssignment(
                person_id=residents_by_pgy[2][0].id,
                block_id=blocks[2].id,
                rotation_template_id=fmit_templates[1].id,
            ),
            MockAssignment(
                person_id=residents_by_pgy[2][1].id,
                block_id=blocks[2].id,
                rotation_template_id=fmit_templates[1].id,
            ),
        ]

        context = SchedulingContext(
            residents=all_residents,
            faculty=[],
            blocks=blocks,
            templates=all_templates,
        )

        result = headcount_constraint.validate(assignments, context)

        assert result.satisfied is False
        # Should have 3 violations: PGY-1 FMIT, Night Float, PGY-2 FMIT
        assert len(result.violations) == 3

        # Verify each violation type
        violation_details = [
            (v.details.get("pgy_level"), v.message) for v in result.violations
        ]

        # Check for PGY-1 FMIT violation
        assert any(pgy == 1 and "FMIT" in msg for pgy, msg in violation_details)

        # Check for Night Float violation
        assert any("Night Float" in msg for _, msg in violation_details)

        # Check for PGY-2 FMIT violation
        assert any(pgy == 2 and "FMIT" in msg for pgy, msg in violation_details)
