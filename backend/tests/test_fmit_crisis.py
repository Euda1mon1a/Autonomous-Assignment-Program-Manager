"""
Tests for FMIT Crisis Mode Constraints.

Tests the two new constraints for production fork:
1. FMITContinuityTurfConstraint - OB turf rules based on load shedding level
2. FMITStaffingFloorConstraint - Minimum faculty requirements for FMIT
"""

from datetime import date, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    SchedulingContext,
)
from app.scheduling.constraints.fmit import (
    FMITContinuityTurfConstraint,
    FMITStaffingFloorConstraint,
)


class TestFMITContinuityTurfConstraint:
    """Tests for FMIT continuity turf rules based on system load."""

    @pytest.fixture
    def constraint(self):
        """Create FMITContinuityTurfConstraint instance."""
        return FMITContinuityTurfConstraint()

    @pytest.fixture
    def base_context(self):
        """Create a basic scheduling context."""
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        return context

    def test_constraint_initialization(self, constraint):
        """Test constraint is initialized correctly."""
        assert constraint.name == "FMITContinuityTurf"
        assert constraint.priority.value == 75  # HIGH priority
        assert constraint.enabled is True

    def test_normal_level_no_violations(self, constraint, base_context):
        """Test NORMAL level (0) produces no violations."""
        base_context.load_shedding_level = 0
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_yellow_level_no_violations(self, constraint, base_context):
        """Test YELLOW level (1) produces no violations."""
        base_context.load_shedding_level = 1
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_orange_level_warning(self, constraint, base_context):
        """Test ORANGE level (2) produces warning about OB availability."""
        base_context.load_shedding_level = 2
        result = constraint.validate([], base_context)

        assert result.satisfied is True  # Informational, not a failure
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.severity == "warning"
        assert "ORANGE" in violation.message or "2" in violation.message
        assert "OB" in violation.message

    def test_red_level_info(self, constraint, base_context):
        """Test RED level (3) produces info about OB coverage."""
        base_context.load_shedding_level = 3
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.severity == "info"
        assert "3" in violation.message

    def test_black_level_all_to_ob(self, constraint, base_context):
        """Test BLACK level (4) indicates all continuity to OB."""
        base_context.load_shedding_level = 4
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.severity == "info"
        assert "All continuity to OB" in violation.message

    def test_missing_load_shedding_defaults_to_normal(self, constraint, base_context):
        """Test missing load_shedding_level defaults to NORMAL (no violations)."""
        # Don't set load_shedding_level
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_turf_policy_levels(self, constraint):
        """Test turf policy descriptions for each level."""
        policies = {
            0: "FM attends all continuity deliveries",
            1: "FM attends all continuity deliveries (yellow alert)",
            2: "FM preferred, OB acceptable for continuity",
            3: "OB covers most continuity, FM if available",
            4: "All continuity to OB - FM essential services only",
        }

        for level, expected_policy in policies.items():
            policy = constraint._get_turf_policy(level)
            assert policy == expected_policy

    def test_violation_details_include_level(self, constraint, base_context):
        """Test violation details include load shedding level."""
        base_context.load_shedding_level = 2

        result = constraint.validate([], base_context)
        violation = result.violations[0]

        assert "load_shedding_level" in violation.details
        assert violation.details["load_shedding_level"] == 2
        assert "turf_policy" in violation.details


class TestFMITStaffingFloorConstraint:
    """Tests for FMIT staffing floor requirements."""

    @pytest.fixture
    def constraint(self):
        """Create FMITStaffingFloorConstraint instance."""
        return FMITStaffingFloorConstraint()

    @pytest.fixture
    def mock_faculty(self):
        """Create mock faculty objects."""

        def create_faculty(count):
            return [
                Mock(id=uuid4(), name=f"Faculty {i}", role="core") for i in range(count)
            ]

        return create_faculty

    @pytest.fixture
    def mock_fmit_template(self):
        """Create mock FMIT template."""
        template = Mock()
        template.id = uuid4()
        template.rotation_type = "inpatient"
        template.name = "FMIT Rotation"
        return template

    @pytest.fixture
    def mock_non_fmit_template(self):
        """Create mock non-FMIT template."""
        template = Mock()
        template.id = uuid4()
        template.rotation_type = "clinic"
        template.name = "Family Medicine Clinic"
        return template

    @pytest.fixture
    def base_context(self, mock_faculty):
        """Create basic scheduling context."""
        faculty = mock_faculty(10)  # Default to 10 faculty
        context = SchedulingContext(
            residents=[],
            faculty=faculty,
            blocks=[],
            templates=[],
        )
        return context

    def test_constraint_initialization(self, constraint):
        """Test constraint is initialized correctly."""
        assert constraint.name == "FMITStaffingFloor"
        assert constraint.priority.value == 100  # CRITICAL priority
        assert constraint.MINIMUM_FACULTY_FOR_FMIT == 5
        assert constraint.FMIT_UTILIZATION_CAP == 0.20

    def test_no_fmit_assignments_passes(self, constraint, base_context):
        """Test validation passes when there are no FMIT assignments."""
        result = constraint.validate([], base_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_below_minimum_faculty_blocks_fmit(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test FMIT is blocked when faculty count < 5."""
        # Create context with only 4 faculty
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(4),
            blocks=[self._create_block(date(2025, 1, 3))],
            templates=[mock_fmit_template],
        )

        # Create FMIT assignment
        assignment = self._create_assignment(
            context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.severity == "CRITICAL"
        assert "only 4 faculty available" in violation.message
        assert "minimum 5 required" in violation.message

    def test_exactly_minimum_faculty_allows_fmit(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test FMIT is allowed with exactly 5 faculty."""
        # Create context with exactly 5 faculty
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(5),
            blocks=[self._create_block(date(2025, 1, 3))],
            templates=[mock_fmit_template],
        )

        # Create 1 FMIT assignment (5 * 0.20 = 1 allowed)
        assignment = self._create_assignment(
            context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_utilization_cap_with_10_faculty(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test utilization cap with 10 faculty allows max 2 concurrent FMIT."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(10),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template],
        )

        # Create 2 concurrent FMIT assignments (10 * 0.20 = 2 allowed)
        assignments = [
            self._create_assignment(
                context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[1].id, context.blocks[0].id, mock_fmit_template.id
            ),
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_exceeding_utilization_cap_fails(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test exceeding utilization cap creates violation."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(10),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template],
        )

        # Create 3 concurrent FMIT assignments (10 * 0.20 = 2 allowed, so 3 exceeds)
        assignments = [
            self._create_assignment(
                context.faculty[i].id, context.blocks[0].id, mock_fmit_template.id
            )
            for i in range(3)
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation.severity == "CRITICAL"
        assert "3 concurrent FMIT exceeds cap" in violation.message
        assert "2 max for 10 faculty" in violation.message

    def test_utilization_cap_edge_case_5_faculty(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test edge case: 5 faculty * 0.20 = 1.0, should allow exactly 1 FMIT."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(5),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template],
        )

        # 5 * 0.20 = 1, should allow 1
        assignment = self._create_assignment(
            context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True

        # Try 2 concurrent (should fail)
        assignments = [
            self._create_assignment(
                context.faculty[i].id, context.blocks[0].id, mock_fmit_template.id
            )
            for i in range(2)
        ]

        result = constraint.validate(assignments, context)
        assert result.satisfied is False

    def test_utilization_cap_rounds_up(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test that at least 1 FMIT is always allowed if above minimum."""
        # 6 faculty * 0.20 = 1.2 -> should allow max(1, int(1.2)) = 1
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(6),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template],
        )

        assignment = self._create_assignment(
            context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True

    def test_multiple_weeks_tracked_separately(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test that different FMIT weeks are tracked separately."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(10),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3))
            + self._create_fmit_week_blocks(date(2025, 1, 10)),
            templates=[mock_fmit_template],
        )

        # 2 FMIT in week 1, 2 FMIT in week 2 (both weeks at cap but valid)
        assignments = [
            # Week 1
            self._create_assignment(
                context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[1].id, context.blocks[0].id, mock_fmit_template.id
            ),
            # Week 2
            self._create_assignment(
                context.faculty[2].id, context.blocks[7].id, mock_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[3].id, context.blocks[7].id, mock_fmit_template.id
            ),
        ]

        result = constraint.validate(assignments, context)
        assert result.satisfied is True

    def test_non_fmit_assignments_ignored(
        self, constraint, mock_faculty, mock_fmit_template, mock_non_fmit_template
    ):
        """Test non-FMIT assignments don't count toward cap."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(10),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template, mock_non_fmit_template],
        )

        # 2 FMIT (at cap) + 5 clinic (ignored)
        assignments = [
            self._create_assignment(
                context.faculty[0].id, context.blocks[0].id, mock_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[1].id, context.blocks[0].id, mock_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[2].id, context.blocks[0].id, mock_non_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[3].id, context.blocks[0].id, mock_non_fmit_template.id
            ),
            self._create_assignment(
                context.faculty[4].id, context.blocks[0].id, mock_non_fmit_template.id
            ),
        ]

        result = constraint.validate(assignments, context)
        assert result.satisfied is True

    def test_violation_details_comprehensive(
        self, constraint, mock_faculty, mock_fmit_template
    ):
        """Test violation details contain all relevant information."""
        context = SchedulingContext(
            residents=[],
            faculty=mock_faculty(5),
            blocks=self._create_fmit_week_blocks(date(2025, 1, 3)),
            templates=[mock_fmit_template],
        )

        # 2 concurrent FMIT with only 5 faculty (exceeds cap)
        assignments = [
            self._create_assignment(
                context.faculty[i].id, context.blocks[0].id, mock_fmit_template.id
            )
            for i in range(2)
        ]

        result = constraint.validate(assignments, context)
        violation = result.violations[0]

        assert "week_start" in violation.details
        assert "concurrent_fmit" in violation.details
        assert "max_allowed" in violation.details
        assert "total_faculty" in violation.details
        assert "utilization_cap" in violation.details
        assert violation.details["concurrent_fmit"] == 2
        assert violation.details["max_allowed"] == 1
        assert violation.details["total_faculty"] == 5

    # Helper methods

    def _create_block(self, block_date):
        """Create a mock block."""
        block = Mock()
        block.id = uuid4()
        block.date = block_date
        block.session_type = "AM"
        return block

    def _create_fmit_week_blocks(self, friday_start):
        """Create blocks for a full FMIT week (Fri-Thurs)."""
        blocks = []
        for i in range(7):
            blocks.append(self._create_block(friday_start + timedelta(days=i)))
        return blocks

    def _create_assignment(self, person_id, block_id, template_id):
        """Create a mock assignment."""
        assignment = Mock()
        assignment.id = uuid4()
        assignment.person_id = person_id
        assignment.block_id = block_id
        assignment.rotation_template_id = template_id
        return assignment


class TestFMITCrisisIntegration:
    """Integration tests for both crisis mode constraints together."""

    def test_both_constraints_can_coexist(self):
        """Test that both constraints can be instantiated together."""
        turf = FMITContinuityTurfConstraint()
        floor = FMITStaffingFloorConstraint()

        assert turf.name != floor.name
        assert turf.constraint_type != floor.constraint_type

    def test_staffing_floor_triggers_before_turf_needed(self):
        """Test that staffing floor prevents FMIT before turf becomes necessary."""
        # With 4 faculty, staffing floor blocks FMIT entirely
        # This prevents the need for OB turf in the first place
        floor = FMITStaffingFloorConstraint()

        context = SchedulingContext(
            residents=[],
            faculty=[Mock(id=uuid4()) for _ in range(4)],
            blocks=[],
            templates=[],
        )
        context.load_shedding_level = 0  # NORMAL - would require FM attendance

        # No FMIT assignments to validate, but if there were, floor would block them
        result = floor.validate([], context)
        assert result.satisfied is True  # No violations because no assignments

    def test_pcs_scenario_4_faculty(self):
        """Test PCS season scenario: arrived to only 4 faculty."""
        floor = FMITStaffingFloorConstraint()
        turf = FMITContinuityTurfConstraint()

        # Create minimal context
        context = SchedulingContext(
            residents=[],
            faculty=[Mock(id=uuid4(), name=f"Faculty {i}") for i in range(4)],
            blocks=[Mock(id=uuid4(), date=date(2025, 1, 3))],
            templates=[Mock(id=uuid4(), rotation_type="inpatient", name="FMIT")],
        )
        context.load_shedding_level = 3  # RED - system stressed

        # Attempt FMIT assignment
        assignment = Mock(
            id=uuid4(),
            person_id=context.faculty[0].id,
            block_id=context.blocks[0].id,
            rotation_template_id=context.templates[0].id,
        )

        # Staffing floor should block it
        floor_result = floor.validate([assignment], context)
        assert floor_result.satisfied is False
        assert "only 4 faculty" in floor_result.violations[0].message

        # Turf should indicate OB is covering
        turf_result = turf.validate([], context)
        assert turf_result.satisfied is True  # Informational
        assert len(turf_result.violations) == 1  # Info message about OB coverage
