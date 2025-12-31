"""Tests for priority constraints identified in Session 029 audit.

These are HARD constraints registered in the default configuration
that were missing test coverage.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import Mock

from app.scheduling.constraints.capacity import ClinicCapacityConstraint
from app.scheduling.constraints.night_float_post_call import (
    NightFloatPostCallConstraint,
)
from app.scheduling.constraints.base import (
    SchedulingContext,
    ConstraintPriority,
    ConstraintType,
)


# ============================================================================
# ClinicCapacityConstraint Tests
# ============================================================================


class TestClinicCapacityConstraint:
    """Tests for ClinicCapacityConstraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = ClinicCapacityConstraint()

        assert constraint.name == "ClinicCapacity"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.HIGH
        assert constraint.enabled is True

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = ClinicCapacityConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))

    def test_validate_within_capacity(self):
        """Test that assignments within template capacity are allowed."""
        constraint = ClinicCapacityConstraint()

        # Create mock template with max 4 residents
        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 4

        # Create mock block
        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # Create 3 assignments (within capacity of 4)
        assignments = []
        for i in range(3):
            assignment = Mock()
            assignment.block_id = block.id
            assignment.rotation_template_id = template.id
            assignment.person_id = uuid4()
            assignments.append(assignment)

        # Create context
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        # Validate
        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_at_capacity(self):
        """Test that assignments at exact capacity are allowed."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 4

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # Create exactly 4 assignments (at capacity)
        assignments = []
        for i in range(4):
            assignment = Mock()
            assignment.block_id = block.id
            assignment.rotation_template_id = template.id
            assignment.person_id = uuid4()
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_over_capacity(self):
        """Test that assignments exceeding template capacity are blocked."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 4

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # Create 5 assignments (over capacity of 4)
        assignments = []
        for i in range(5):
            assignment = Mock()
            assignment.block_id = block.id
            assignment.rotation_template_id = template.id
            assignment.person_id = uuid4()
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.constraint_name == "ClinicCapacity"
        assert violation.severity == "HIGH"
        assert "5 assigned" in violation.message
        assert "max: 4" in violation.message
        assert violation.details["count"] == 5
        assert violation.details["limit"] == 4

    def test_validate_no_capacity_limit(self):
        """Test behavior when template has no capacity limit."""
        constraint = ClinicCapacityConstraint()

        # Template with no max_residents set
        template = Mock()
        template.id = uuid4()
        template.name = "General Clinic"
        template.max_residents = None

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # Create many assignments
        assignments = []
        for i in range(10):
            assignment = Mock()
            assignment.block_id = block.id
            assignment.rotation_template_id = template.id
            assignment.person_id = uuid4()
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate(assignments, context)

        # Should be satisfied (no limit enforced)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_zero_capacity(self):
        """Test behavior when template has zero capacity."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Closed Clinic"
        template.max_residents = 0

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # Create 1 assignment
        assignment = Mock()
        assignment.block_id = block.id
        assignment.rotation_template_id = template.id
        assignment.person_id = uuid4()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate([assignment], context)

        # max_residents=0 means no limit enforced (per implementation)
        assert result.satisfied is True

    def test_validate_multiple_blocks_same_template(self):
        """Test capacity enforcement is per-block, not global."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 2

        block1 = Mock()
        block1.id = uuid4()
        block1.date = date.today()

        block2 = Mock()
        block2.id = uuid4()
        block2.date = date.today() + timedelta(days=1)

        # 2 assignments per block (each at capacity)
        assignments = []
        for block in [block1, block2]:
            for i in range(2):
                assignment = Mock()
                assignment.block_id = block.id
                assignment.rotation_template_id = template.id
                assignment.person_id = uuid4()
                assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block1, block2],
            templates=[template],
        )

        result = constraint.validate(assignments, context)

        # Should be satisfied (capacity enforced per block)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_templates_same_block(self):
        """Test capacity enforcement is per-template."""
        constraint = ClinicCapacityConstraint()

        template1 = Mock()
        template1.id = uuid4()
        template1.name = "Sports Medicine Clinic"
        template1.max_residents = 2

        template2 = Mock()
        template2.id = uuid4()
        template2.name = "Primary Care Clinic"
        template2.max_residents = 3

        block = Mock()
        block.id = uuid4()
        block.date = date.today()

        # 2 assignments for template1, 3 for template2 (both at capacity)
        assignments = []
        for template, count in [(template1, 2), (template2, 3)]:
            for i in range(count):
                assignment = Mock()
                assignment.block_id = block.id
                assignment.rotation_template_id = template.id
                assignment.person_id = uuid4()
                assignments.append(assignment)

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template1, template2],
        )

        result = constraint.validate(assignments, context)

        # Should be satisfied (capacity enforced per template)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_empty_assignments(self):
        """Test behavior with no assignments."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 4

        block = Mock()
        block.id = uuid4()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_assignment_without_template(self):
        """Test assignments without rotation_template_id are ignored."""
        constraint = ClinicCapacityConstraint()

        template = Mock()
        template.id = uuid4()
        template.name = "Sports Medicine Clinic"
        template.max_residents = 2

        block = Mock()
        block.id = uuid4()

        # Assignment without rotation_template_id
        assignment = Mock()
        assignment.block_id = block.id
        assignment.rotation_template_id = None
        assignment.person_id = uuid4()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[block],
            templates=[template],
        )

        result = constraint.validate([assignment], context)

        # Should be satisfied (assignment ignored)
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# NightFloatPostCallConstraint Tests
# ============================================================================


class TestNightFloatPostCallConstraint:
    """Tests for NightFloatPostCallConstraint."""

    def test_constraint_initialization(self):
        """Test that constraint initializes with correct properties."""
        constraint = NightFloatPostCallConstraint()

        assert constraint.name == "NightFloatPostCall"
        assert constraint.constraint_type == ConstraintType.ROTATION
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.enabled is True

    def test_constraint_has_required_methods(self):
        """Test constraint has all required interface methods."""
        constraint = NightFloatPostCallConstraint()

        assert callable(getattr(constraint, "add_to_cpsat", None))
        assert callable(getattr(constraint, "add_to_pulp", None))
        assert callable(getattr(constraint, "validate", None))

    def test_validate_with_proper_post_call(self):
        """Test that proper post-call assignment after NF is allowed."""
        constraint = NightFloatPostCallConstraint()

        # Create NF and PC templates
        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.name = "Night Float"
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.name = "Post-Call"
        pc_template.abbreviation = "PC"

        # Create resident
        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        # Create blocks for block-half transition
        # Block 1, half 1, last day (day 14)
        last_day = date(2025, 1, 14)
        nf_am_block = Mock()
        nf_am_block.id = uuid4()
        nf_am_block.date = last_day
        nf_am_block.time_of_day = "AM"
        nf_am_block.block_number = 1
        nf_am_block.block_half = 1

        nf_pm_block = Mock()
        nf_pm_block.id = uuid4()
        nf_pm_block.date = last_day
        nf_pm_block.time_of_day = "PM"
        nf_pm_block.block_number = 1
        nf_pm_block.block_half = 1

        # Block 1, half 2, first day (day 15) - PC day
        pc_day = date(2025, 1, 15)
        pc_am_block = Mock()
        pc_am_block.id = uuid4()
        pc_am_block.date = pc_day
        pc_am_block.time_of_day = "AM"
        pc_am_block.block_number = 1
        pc_am_block.block_half = 2

        pc_pm_block = Mock()
        pc_pm_block.id = uuid4()
        pc_pm_block.date = pc_day
        pc_pm_block.time_of_day = "PM"
        pc_pm_block.block_number = 1
        pc_pm_block.block_half = 2

        # Create assignments: NF on last day of half 1
        nf_assignment_am = Mock()
        nf_assignment_am.block_id = nf_am_block.id
        nf_assignment_am.person_id = resident.id
        nf_assignment_am.rotation_template_id = nf_template.id

        nf_assignment_pm = Mock()
        nf_assignment_pm.block_id = nf_pm_block.id
        nf_assignment_pm.person_id = resident.id
        nf_assignment_pm.rotation_template_id = nf_template.id

        # PC assignments on day 15 (both AM and PM)
        pc_assignment_am = Mock()
        pc_assignment_am.block_id = pc_am_block.id
        pc_assignment_am.person_id = resident.id
        pc_assignment_am.rotation_template_id = pc_template.id

        pc_assignment_pm = Mock()
        pc_assignment_pm.block_id = pc_pm_block.id
        pc_assignment_pm.person_id = resident.id
        pc_assignment_pm.rotation_template_id = pc_template.id

        assignments = [
            nf_assignment_am,
            nf_assignment_pm,
            pc_assignment_am,
            pc_assignment_pm,
        ]

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[nf_am_block, nf_pm_block, pc_am_block, pc_pm_block],
            templates=[nf_template, pc_template],
        )

        result = constraint.validate(assignments, context)

        # Should be satisfied (PC properly assigned)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_missing_post_call_am(self):
        """Test that missing Post-Call AM is detected as violation."""
        constraint = NightFloatPostCallConstraint()

        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.name = "Night Float"
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.name = "Post-Call"
        pc_template.abbreviation = "PC"

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        # Last day of block-half
        last_day = date(2025, 1, 14)
        nf_block = Mock()
        nf_block.id = uuid4()
        nf_block.date = last_day
        nf_block.time_of_day = "AM"
        nf_block.block_number = 1
        nf_block.block_half = 1

        # PC day (missing AM PC)
        pc_day = date(2025, 1, 15)
        pc_pm_block = Mock()
        pc_pm_block.id = uuid4()
        pc_pm_block.date = pc_day
        pc_pm_block.time_of_day = "PM"
        pc_pm_block.block_number = 1
        pc_pm_block.block_half = 2

        # NF assignment on last day
        nf_assignment = Mock()
        nf_assignment.block_id = nf_block.id
        nf_assignment.person_id = resident.id
        nf_assignment.rotation_template_id = nf_template.id

        # Only PM PC (AM missing)
        pc_assignment_pm = Mock()
        pc_assignment_pm.block_id = pc_pm_block.id
        pc_assignment_pm.person_id = resident.id
        pc_assignment_pm.rotation_template_id = pc_template.id

        assignments = [nf_assignment, pc_assignment_pm]

        # Need to add AM block for pc_day (even though no assignment)
        pc_am_block = Mock()
        pc_am_block.id = uuid4()
        pc_am_block.date = pc_day
        pc_am_block.time_of_day = "AM"
        pc_am_block.block_number = 1
        pc_am_block.block_half = 2

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[nf_block, pc_am_block, pc_pm_block],
            templates=[nf_template, pc_template],
        )

        result = constraint.validate(assignments, context)

        # Should have violation for missing AM PC
        assert result.satisfied is False
        assert len(result.violations) >= 1
        violation = result.violations[0]
        assert violation.constraint_name == "NightFloatPostCall"
        assert violation.severity == "CRITICAL"
        assert "missing Post-Call" in violation.message
        assert "AM" in violation.message

    def test_validate_missing_post_call_pm(self):
        """Test that missing Post-Call PM is detected as violation."""
        constraint = NightFloatPostCallConstraint()

        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.name = "Night Float"
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.name = "Post-Call"
        pc_template.abbreviation = "PC"

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        last_day = date(2025, 1, 14)
        nf_block = Mock()
        nf_block.id = uuid4()
        nf_block.date = last_day
        nf_block.time_of_day = "AM"
        nf_block.block_number = 1
        nf_block.block_half = 1

        pc_day = date(2025, 1, 15)
        pc_am_block = Mock()
        pc_am_block.id = uuid4()
        pc_am_block.date = pc_day
        pc_am_block.time_of_day = "AM"
        pc_am_block.block_number = 1
        pc_am_block.block_half = 2

        pc_pm_block = Mock()
        pc_pm_block.id = uuid4()
        pc_pm_block.date = pc_day
        pc_pm_block.time_of_day = "PM"
        pc_pm_block.block_number = 1
        pc_pm_block.block_half = 2

        # NF assignment
        nf_assignment = Mock()
        nf_assignment.block_id = nf_block.id
        nf_assignment.person_id = resident.id
        nf_assignment.rotation_template_id = nf_template.id

        # Only AM PC (PM missing)
        pc_assignment_am = Mock()
        pc_assignment_am.block_id = pc_am_block.id
        pc_assignment_am.person_id = resident.id
        pc_assignment_am.rotation_template_id = pc_template.id

        assignments = [nf_assignment, pc_assignment_am]

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[nf_block, pc_am_block, pc_pm_block],
            templates=[nf_template, pc_template],
        )

        result = constraint.validate(assignments, context)

        # Should have violation for missing PM PC
        assert result.satisfied is False
        assert len(result.violations) >= 1
        # Find the PM violation
        pm_violations = [v for v in result.violations if "PM" in v.message]
        assert len(pm_violations) >= 1
        violation = pm_violations[0]
        assert violation.constraint_name == "NightFloatPostCall"
        assert violation.severity == "CRITICAL"

    def test_validate_no_night_float_assignments(self):
        """Test behavior when no Night Float assignments exist."""
        constraint = NightFloatPostCallConstraint()

        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.name = "Night Float"
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.name = "Post-Call"
        pc_template.abbreviation = "PC"

        regular_template = Mock()
        regular_template.id = uuid4()
        regular_template.name = "Clinic"
        regular_template.abbreviation = "CLINIC"

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        block = Mock()
        block.id = uuid4()
        block.date = date.today()
        block.time_of_day = "AM"
        block.block_number = 1
        block.block_half = 1

        # Regular assignment (not NF)
        assignment = Mock()
        assignment.block_id = block.id
        assignment.person_id = resident.id
        assignment.rotation_template_id = regular_template.id

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[block],
            templates=[nf_template, pc_template, regular_template],
        )

        result = constraint.validate([assignment], context)

        # Should be satisfied (no NF to enforce PC for)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_templates(self):
        """Test behavior when NF or PC templates don't exist."""
        constraint = NightFloatPostCallConstraint()

        resident = Mock()
        resident.id = uuid4()
        resident.name = "Dr. Smith"

        block = Mock()
        block.id = uuid4()
        block.date = date.today()
        block.time_of_day = "AM"

        assignment = Mock()
        assignment.block_id = block.id
        assignment.person_id = resident.id
        assignment.rotation_template_id = uuid4()

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[block],
            templates=[],  # No templates
        )

        result = constraint.validate([assignment], context)

        # Should be satisfied (can't enforce without templates)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_empty_assignments(self):
        """Test behavior with no assignments."""
        constraint = NightFloatPostCallConstraint()

        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.abbreviation = "PC"

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[nf_template, pc_template],
        )

        result = constraint.validate([], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_residents(self):
        """Test constraint handles multiple residents independently."""
        constraint = NightFloatPostCallConstraint()

        nf_template = Mock()
        nf_template.id = uuid4()
        nf_template.abbreviation = "NF"

        pc_template = Mock()
        pc_template.id = uuid4()
        pc_template.abbreviation = "PC"

        resident1 = Mock()
        resident1.id = uuid4()
        resident1.name = "Dr. Smith"

        resident2 = Mock()
        resident2.id = uuid4()
        resident2.name = "Dr. Jones"

        # Block half transition
        last_day = date(2025, 1, 14)
        nf_block = Mock()
        nf_block.id = uuid4()
        nf_block.date = last_day
        nf_block.time_of_day = "AM"
        nf_block.block_number = 1
        nf_block.block_half = 1

        pc_day = date(2025, 1, 15)
        pc_am_block = Mock()
        pc_am_block.id = uuid4()
        pc_am_block.date = pc_day
        pc_am_block.time_of_day = "AM"
        pc_am_block.block_number = 1
        pc_am_block.block_half = 2

        pc_pm_block = Mock()
        pc_pm_block.id = uuid4()
        pc_pm_block.date = pc_day
        pc_pm_block.time_of_day = "PM"
        pc_pm_block.block_number = 1
        pc_pm_block.block_half = 2

        # Resident 1: NF + proper PC
        r1_nf = Mock()
        r1_nf.block_id = nf_block.id
        r1_nf.person_id = resident1.id
        r1_nf.rotation_template_id = nf_template.id

        r1_pc_am = Mock()
        r1_pc_am.block_id = pc_am_block.id
        r1_pc_am.person_id = resident1.id
        r1_pc_am.rotation_template_id = pc_template.id

        r1_pc_pm = Mock()
        r1_pc_pm.block_id = pc_pm_block.id
        r1_pc_pm.person_id = resident1.id
        r1_pc_pm.rotation_template_id = pc_template.id

        # Resident 2: NF + proper PC
        r2_nf = Mock()
        r2_nf.block_id = nf_block.id
        r2_nf.person_id = resident2.id
        r2_nf.rotation_template_id = nf_template.id

        r2_pc_am = Mock()
        r2_pc_am.block_id = pc_am_block.id
        r2_pc_am.person_id = resident2.id
        r2_pc_am.rotation_template_id = pc_template.id

        r2_pc_pm = Mock()
        r2_pc_pm.block_id = pc_pm_block.id
        r2_pc_pm.person_id = resident2.id
        r2_pc_pm.rotation_template_id = pc_template.id

        assignments = [r1_nf, r1_pc_am, r1_pc_pm, r2_nf, r2_pc_am, r2_pc_pm]

        context = SchedulingContext(
            residents=[resident1, resident2],
            faculty=[],
            blocks=[nf_block, pc_am_block, pc_pm_block],
            templates=[nf_template, pc_template],
        )

        result = constraint.validate(assignments, context)

        # Both residents have proper PC
        assert result.satisfied is True
        assert len(result.violations) == 0
