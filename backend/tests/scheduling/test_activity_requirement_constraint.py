"""
Tests for ActivityRequirementConstraint.

Tests the soft constraint that enforces min/max/target halfdays per activity
based on RotationActivityRequirement configuration.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.activity_requirement import (
    ActivityRequirementConstraint,
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
    """Mock rotation template object for testing."""

    def __init__(
        self,
        template_id=None,
        name="Test Template",
        rotation_type="outpatient",
    ):
        self.id = template_id or uuid4()
        self.name = name
        self.rotation_type = rotation_type


class MockActivity:
    """Mock activity object for testing."""

    def __init__(
        self,
        activity_id=None,
        name="FM Clinic",
        code="fm_clinic",
        activity_category="clinical",
        is_protected=False,
    ):
        self.id = activity_id or uuid4()
        self.name = name
        self.code = code
        self.activity_category = activity_category
        self.is_protected = is_protected


class MockActivityRequirement:
    """Mock activity requirement object for testing."""

    def __init__(
        self,
        requirement_id=None,
        rotation_template_id=None,
        activity_id=None,
        activity=None,
        min_halfdays=0,
        max_halfdays=14,
        target_halfdays=None,
        applicable_weeks=None,
        prefer_full_days=True,
        preferred_days=None,
        avoid_days=None,
        priority=50,
    ):
        self.id = requirement_id or uuid4()
        self.rotation_template_id = rotation_template_id
        self.activity_id = activity_id
        self.activity = activity
        self.min_halfdays = min_halfdays
        self.max_halfdays = max_halfdays
        self.target_halfdays = target_halfdays
        self.applicable_weeks = applicable_weeks
        self.prefer_full_days = prefer_full_days
        self.preferred_days = preferred_days
        self.avoid_days = avoid_days
        self.priority = priority


class MockAssignment:
    """Mock assignment object for testing with activity support."""

    def __init__(
        self,
        assignment_id=None,
        person_id=None,
        block_id=None,
        rotation_template_id=None,
        activity_id=None,
        role="primary",
    ):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = rotation_template_id
        self.activity_id = activity_id
        self.role = role


# ============================================================================
# Helper Functions
# ============================================================================


def create_week_of_blocks(start_date=None):
    """Create blocks for a full week (Mon-Sun) with AM/PM slots."""
    if start_date is None:
        today = date.today()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)

    blocks = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(
                block_date=current_date,
                time_of_day=time_of_day,
                is_weekend=is_weekend,
            )
            blocks.append(block)

    return blocks


def create_residents(count=3):
    """Create multiple resident persons."""
    return [
        MockPerson(
            name=f"Dr. Resident {i + 1}",
            person_type="resident",
            pgy_level=(i % 3) + 1,
        )
        for i in range(count)
    ]


def create_activities():
    """Create standard activity set."""
    return [
        MockActivity(name="FM Clinic", code="fm_clinic"),
        MockActivity(name="Specialty", code="specialty"),
        MockActivity(
            name="LEC", code="lec", activity_category="educational", is_protected=True
        ),
        MockActivity(name="Day Off", code="off", activity_category="time_off"),
    ]


# ============================================================================
# Tests for ActivityRequirementConstraint
# ============================================================================


class TestActivityRequirementConstraintInit:
    """Tests for constraint initialization."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = ActivityRequirementConstraint()
        assert constraint.name == "ActivityRequirement"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.MEDIUM
        assert constraint.weight == 50.0

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initialization with custom weight."""
        constraint = ActivityRequirementConstraint(weight=100.0)
        assert constraint.weight == 100.0

    def test_constraint_is_soft(self):
        """Test that this is a soft constraint."""
        constraint = ActivityRequirementConstraint()
        # Soft constraints should have a weight attribute
        assert hasattr(constraint, "weight")
        assert constraint.weight > 0


class TestActivityRequirementValidation:
    """Tests for constraint validation."""

    def test_validate_no_requirements(self):
        """Test validate passes when no requirements configured."""
        constraint = ActivityRequirementConstraint()
        blocks = create_week_of_blocks()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
            activity_requirements=[],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0
        assert result.penalty == 0.0

    def test_validate_meets_target(self):
        """Test validate passes when actual matches target."""
        constraint = ActivityRequirementConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        # Requirement: FM Clinic target 4 halfdays
        fm_clinic = activities[0]
        requirement = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=fm_clinic.id,
            activity=fm_clinic,
            min_halfdays=2,
            max_halfdays=6,
            target_halfdays=4,
            priority=50,
        )

        # Assignments: 4 FM Clinic halfdays
        assignments = []
        for i in range(4):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[i].id,
                    rotation_template_id=template.id,
                    activity_id=fm_clinic.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[requirement],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        # No significant violations when hitting target
        assert result.penalty == 0.0

    def test_validate_below_target(self):
        """Test validate calculates penalty when below target."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        fm_clinic = activities[0]
        requirement = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=fm_clinic.id,
            activity=fm_clinic,
            min_halfdays=2,
            max_halfdays=6,
            target_halfdays=4,
            priority=50,
        )

        # Only 2 FM Clinic halfdays (below target of 4)
        assignments = []
        for i in range(2):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[i].id,
                    rotation_template_id=template.id,
                    activity_id=fm_clinic.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[requirement],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True  # Soft constraint always satisfied
        # Penalty: weight * (priority/100) * deviation = 50 * 0.5 * 2 = 50
        assert result.penalty > 0

    def test_validate_below_min(self):
        """Test validate has high penalty when below minimum."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        fm_clinic = activities[0]
        requirement = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=fm_clinic.id,
            activity=fm_clinic,
            min_halfdays=4,
            max_halfdays=6,
            target_halfdays=5,
            priority=50,
        )

        # Only 2 FM Clinic halfdays (below min of 4)
        assignments = []
        for i in range(2):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[i].id,
                    rotation_template_id=template.id,
                    activity_id=fm_clinic.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[requirement],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True  # Still soft satisfied
        assert len(result.violations) >= 1
        assert "minimum" in result.violations[0].message.lower()
        # High penalty for min violation (10x multiplier)
        # 50 * 10 * (4-2) = 1000
        assert result.penalty >= 1000.0

    def test_validate_above_max(self):
        """Test validate has high penalty when above maximum."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        fm_clinic = activities[0]
        requirement = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=fm_clinic.id,
            activity=fm_clinic,
            min_halfdays=2,
            max_halfdays=4,
            target_halfdays=3,
            priority=50,
        )

        # 6 FM Clinic halfdays (above max of 4)
        assignments = []
        for i in range(6):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[i].id,
                    rotation_template_id=template.id,
                    activity_id=fm_clinic.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[requirement],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True  # Soft constraint
        assert len(result.violations) >= 1
        assert "maximum" in result.violations[0].message.lower()
        # High penalty for max violation (10x multiplier)
        # 50 * 10 * (6-4) = 1000
        assert result.penalty >= 1000.0

    def test_validate_priority_affects_penalty(self):
        """Test that higher priority requirements have larger penalty."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        # High priority requirement
        fm_clinic = activities[0]
        high_priority_req = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=fm_clinic.id,
            activity=fm_clinic,
            min_halfdays=0,
            max_halfdays=10,
            target_halfdays=4,
            priority=100,  # High priority
        )

        # Low priority requirement
        lec = activities[2]
        low_priority_req = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=lec.id,
            activity=lec,
            min_halfdays=0,
            max_halfdays=10,
            target_halfdays=4,
            priority=25,  # Low priority
        )

        # Both have 2 assignments (2 below target)
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[2].id,
                rotation_template_id=template.id,
                activity_id=lec.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[3].id,
                rotation_template_id=template.id,
                activity_id=lec.id,
            ),
        ]

        # Test high priority first
        context_high = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[high_priority_req],
        )

        result_high = constraint.validate(assignments[:2], context_high)

        # Test low priority
        context_low = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[low_priority_req],
        )

        result_low = constraint.validate(assignments[2:], context_low)

        # High priority should have higher penalty
        assert result_high.penalty > result_low.penalty

    def test_validate_multiple_requirements(self):
        """Test validate with multiple activity requirements."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        fm_clinic = activities[0]
        specialty = activities[1]

        requirements = [
            MockActivityRequirement(
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
                activity=fm_clinic,
                min_halfdays=2,
                max_halfdays=6,
                target_halfdays=4,
                priority=80,
            ),
            MockActivityRequirement(
                rotation_template_id=template.id,
                activity_id=specialty.id,
                activity=specialty,
                min_halfdays=3,
                max_halfdays=7,
                target_halfdays=5,
                priority=60,
            ),
        ]

        # Mix of FM Clinic and Specialty assignments
        assignments = [
            # 4 FM Clinic (hits target)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[2].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[3].id,
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
            ),
            # 3 Specialty (below target of 5)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[4].id,
                rotation_template_id=template.id,
                activity_id=specialty.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[5].id,
                rotation_template_id=template.id,
                activity_id=specialty.id,
            ),
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[6].id,
                rotation_template_id=template.id,
                activity_id=specialty.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=requirements,
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        # Should have penalty for specialty being below target
        assert result.penalty > 0


class TestActivityRequirementContextIntegration:
    """Tests for context integration."""

    def test_context_has_activity_requirements(self):
        """Test SchedulingContext properly tracks activity requirements."""
        blocks = create_week_of_blocks()
        activities = create_activities()
        template = MockTemplate(name="Neurology")

        requirement = MockActivityRequirement(
            rotation_template_id=template.id,
            activity_id=activities[0].id,
            activity=activities[0],
            target_halfdays=4,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=[requirement],
        )

        assert context.has_activity_requirements() is True
        reqs = context.get_requirements_for_template(template.id)
        assert len(reqs) == 1
        assert reqs[0].target_halfdays == 4

    def test_context_no_requirements(self):
        """Test SchedulingContext returns False when no requirements."""
        blocks = create_week_of_blocks()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
            activities=[],
            activity_requirements=[],
        )

        assert context.has_activity_requirements() is False

    def test_activity_idx_built_correctly(self):
        """Test activity index is built in context post_init."""
        blocks = create_week_of_blocks()
        activities = create_activities()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
            activities=activities,
            activity_requirements=[],
        )

        # Check activity_idx is populated
        assert len(context.activity_idx) == len(activities)
        for i, activity in enumerate(activities):
            assert context.activity_idx[activity.id] == i


@pytest.mark.integration
class TestActivityRequirementIntegration:
    """Integration tests for activity requirement constraint."""

    def test_realistic_rotation_scenario(self):
        """Test a realistic rotation with multiple activities."""
        constraint = ActivityRequirementConstraint(weight=50.0)
        blocks = create_week_of_blocks()
        residents = create_residents(count=1)
        activities = create_activities()
        template = MockTemplate(name="Sports Medicine Elective")

        # Realistic requirements for a 2-week (14 halfday) block:
        # - FM Clinic: 4 halfdays (20%)
        # - Specialty: 8 halfdays (57%)
        # - LEC: 2 halfdays (14%) - protected
        # Total: 14 halfdays

        fm_clinic = activities[0]
        specialty = activities[1]
        lec = activities[2]

        requirements = [
            MockActivityRequirement(
                rotation_template_id=template.id,
                activity_id=fm_clinic.id,
                activity=fm_clinic,
                min_halfdays=3,
                max_halfdays=5,
                target_halfdays=4,
                priority=80,
            ),
            MockActivityRequirement(
                rotation_template_id=template.id,
                activity_id=specialty.id,
                activity=specialty,
                min_halfdays=6,
                max_halfdays=10,
                target_halfdays=8,
                priority=70,
            ),
            MockActivityRequirement(
                rotation_template_id=template.id,
                activity_id=lec.id,
                activity=lec,
                min_halfdays=2,
                max_halfdays=2,  # Exact - protected
                target_halfdays=2,
                priority=100,  # Highest - protected time
            ),
        ]

        # Assignments that match targets exactly
        assignments = []
        slot_idx = 0

        # 4 FM Clinic
        for _ in range(4):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[slot_idx].id,
                    rotation_template_id=template.id,
                    activity_id=fm_clinic.id,
                )
            )
            slot_idx += 1

        # 8 Specialty
        for _ in range(8):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[slot_idx].id,
                    rotation_template_id=template.id,
                    activity_id=specialty.id,
                )
            )
            slot_idx += 1

        # 2 LEC
        for _ in range(2):
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=blocks[slot_idx % len(blocks)].id,
                    rotation_template_id=template.id,
                    activity_id=lec.id,
                )
            )
            slot_idx += 1

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
            activities=activities,
            activity_requirements=requirements,
        )

        result = constraint.validate(assignments, context)

        # Should be satisfied with zero penalty (all targets hit)
        assert result.satisfied is True
        assert result.penalty == 0.0
        assert len(result.violations) == 0
