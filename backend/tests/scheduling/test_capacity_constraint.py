"""Tests for capacity and coverage constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)


# ==================== Helpers ====================


def _person(pid=None):
    """Build a mock person with .id attribute."""
    return SimpleNamespace(id=pid or uuid4())


def _block(bid=None, block_date=None, is_weekend=False, time_of_day="AM"):
    """Build a mock block with .id, .date, .is_weekend, .time_of_day."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        is_weekend=is_weekend,
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", max_residents=None, rotation_type=None):
    """Build a mock template."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name, max_residents=max_residents)
    if rotation_type is not None:
        ns.rotation_type = rotation_type
    return ns


def _assignment(person_id, block_id, role="primary", rotation_template_id=None):
    """Build a mock assignment."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        role=role,
        rotation_template_id=rotation_template_id,
    )


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== OnePersonPerBlockConstraint Tests ====================


class TestOnePersonPerBlockConstraintInit:
    """Test OnePersonPerBlockConstraint initialization."""

    def test_defaults(self):
        c = OnePersonPerBlockConstraint()
        assert c.max_per_block == 1
        assert c.name == "OnePersonPerBlock"
        assert c.constraint_type == ConstraintType.CAPACITY
        assert c.priority == ConstraintPriority.CRITICAL

    def test_custom_max(self):
        c = OnePersonPerBlockConstraint(max_per_block=2)
        assert c.max_per_block == 2


class TestOnePersonPerBlockValidate:
    """Test OnePersonPerBlockConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = OnePersonPerBlockConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_one_primary_per_block_satisfied(self):
        c = OnePersonPerBlockConstraint()
        b1 = _block()
        b2 = _block()
        ctx = _context(blocks=[b1, b2])

        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b2.id, role="primary"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_two_primary_same_block_violation(self):
        c = OnePersonPerBlockConstraint()
        b1 = _block()
        ctx = _context(blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="primary"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "2 primary" in result.violations[0].message

    def test_supervisor_role_not_counted(self):
        """Non-primary roles don't count."""
        c = OnePersonPerBlockConstraint()
        b1 = _block()
        ctx = _context(blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="supervisor"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_custom_max_2_allows_two(self):
        c = OnePersonPerBlockConstraint(max_per_block=2)
        b1 = _block()
        ctx = _context(blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="primary"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_custom_max_2_three_violates(self):
        c = OnePersonPerBlockConstraint(max_per_block=2)
        b1 = _block()
        ctx = _context(blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="primary"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False

    def test_multiple_blocks_independent(self):
        """Different blocks checked independently."""
        c = OnePersonPerBlockConstraint()
        b1 = _block()
        b2 = _block()
        ctx = _context(blocks=[b1, b2])

        # 2 in b1 (violates), 1 in b2 (ok)
        assignments = [
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b1.id, role="primary"),
            _assignment(uuid4(), b2.id, role="primary"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1  # Only b1


# ==================== ClinicCapacityConstraint Tests ====================


class TestClinicCapacityConstraintInit:
    """Test ClinicCapacityConstraint initialization."""

    def test_defaults(self):
        c = ClinicCapacityConstraint()
        assert c.name == "ClinicCapacity"
        assert c.constraint_type == ConstraintType.CAPACITY
        assert c.priority == ConstraintPriority.HIGH


class TestClinicCapacityValidate:
    """Test ClinicCapacityConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = ClinicCapacityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_within_capacity_satisfied(self):
        c = ClinicCapacityConstraint()
        t1 = _template(name="FM Clinic", max_residents=3)
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        # 2 assigned to template with max 3
        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_over_capacity_violation(self):
        c = ClinicCapacityConstraint()
        t1 = _template(name="FM Clinic", max_residents=2)
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        # 3 assigned to template with max 2
        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "FM Clinic" in result.violations[0].message

    def test_no_limit_no_violation(self):
        """Template with no max_residents -> no violation."""
        c = ClinicCapacityConstraint()
        t1 = _template(name="Open", max_residents=None)
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id) for _ in range(10)
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_different_templates_independent(self):
        """Capacity checked per (block, template) pair."""
        c = ClinicCapacityConstraint()
        t1 = _template(name="A", max_residents=1)
        t2 = _template(name="B", max_residents=1)
        b1 = _block()
        ctx = _context(templates=[t1, t2], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # 1 each, both within limit

    def test_exactly_at_capacity(self):
        c = ClinicCapacityConstraint()
        t1 = _template(name="FM Clinic", max_residents=2)
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_null_template_id_ignored(self):
        """Assignments without rotation_template_id skipped."""
        c = ClinicCapacityConstraint()
        t1 = _template(name="A", max_residents=1)
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=None),
            _assignment(uuid4(), b1.id, rotation_template_id=None),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True


# ==================== MaxPhysiciansInClinicConstraint Tests ====================


class TestMaxPhysiciansInClinicInit:
    """Test MaxPhysiciansInClinicConstraint initialization."""

    def test_defaults(self):
        c = MaxPhysiciansInClinicConstraint()
        assert c.max_physicians == 6
        assert c.name == "MaxPhysiciansInClinic"
        assert c.priority == ConstraintPriority.HIGH

    def test_custom_max(self):
        c = MaxPhysiciansInClinicConstraint(max_physicians=4)
        assert c.max_physicians == 4


class TestMaxPhysiciansInClinicValidate:
    """Test MaxPhysiciansInClinicConstraint.validate method."""

    def test_no_clinic_templates_satisfied(self):
        """No outpatient templates -> always satisfied."""
        c = MaxPhysiciansInClinicConstraint()
        t1 = _template(rotation_type="inpatient")
        ctx = _context(templates=[t1])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_within_limit_satisfied(self):
        c = MaxPhysiciansInClinicConstraint(max_physicians=4)
        t1 = _template(rotation_type="outpatient")
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id) for _ in range(3)
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_over_limit_violation(self):
        c = MaxPhysiciansInClinicConstraint(max_physicians=4)
        t1 = _template(rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id) for _ in range(5)
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "5 physicians" in result.violations[0].message
        assert "max: 4" in result.violations[0].message

    def test_non_clinic_assignments_not_counted(self):
        """Assignments to non-outpatient templates not counted."""
        c = MaxPhysiciansInClinicConstraint(max_physicians=2)
        t_clinic = _template(rotation_type="outpatient")
        t_inpatient = _template(rotation_type="inpatient")
        b1 = _block()
        ctx = _context(templates=[t_clinic, t_inpatient], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t_clinic.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t_clinic.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t_inpatient.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t_inpatient.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # Only 2 clinic assignments

    def test_multiple_blocks_independent(self):
        c = MaxPhysiciansInClinicConstraint(max_physicians=2)
        t1 = _template(rotation_type="outpatient")
        b1 = _block()
        b2 = _block()
        ctx = _context(templates=[t1], blocks=[b1, b2])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id),
            _assignment(uuid4(), b2.id, rotation_template_id=t1.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # 2 per block, within limit

    def test_template_without_rotation_type_excluded(self):
        """Templates without rotation_type attribute not considered clinic."""
        c = MaxPhysiciansInClinicConstraint(max_physicians=2)
        t1 = _template()  # No rotation_type attribute
        b1 = _block()
        ctx = _context(templates=[t1], blocks=[b1])

        assignments = [
            _assignment(uuid4(), b1.id, rotation_template_id=t1.id) for _ in range(5)
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # No clinic templates detected


# ==================== CoverageConstraint Tests ====================


class TestCoverageConstraintInit:
    """Test CoverageConstraint initialization."""

    def test_defaults(self):
        c = CoverageConstraint()
        assert c.weight == 1000.0
        assert c.name == "Coverage"
        assert c.constraint_type == ConstraintType.CAPACITY
        assert c.priority == ConstraintPriority.HIGH

    def test_custom_weight(self):
        c = CoverageConstraint(weight=500.0)
        assert c.weight == 500.0


class TestCoverageValidate:
    """Test CoverageConstraint.validate method."""

    def test_no_blocks_no_penalty(self):
        c = CoverageConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == pytest.approx(1000.0)  # (1-0) * 1000

    def test_full_coverage_zero_penalty(self):
        c = CoverageConstraint(weight=1000.0)
        b1 = _block(is_weekend=False)
        b2 = _block(is_weekend=False)
        ctx = _context(blocks=[b1, b2])

        assignments = [
            _assignment(uuid4(), b1.id),
            _assignment(uuid4(), b2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0
        assert len(result.violations) == 0

    def test_partial_coverage_penalty(self):
        c = CoverageConstraint(weight=1000.0)
        b1 = _block(is_weekend=False)
        b2 = _block(is_weekend=False)
        ctx = _context(blocks=[b1, b2])

        # Only b1 assigned
        assignments = [_assignment(uuid4(), b1.id)]
        result = c.validate(assignments, ctx)
        assert result.penalty == pytest.approx(500.0)  # (1 - 0.5) * 1000

    def test_below_90_percent_violation(self):
        """Coverage < 90% -> MEDIUM violation."""
        c = CoverageConstraint()
        blocks = [_block(is_weekend=False) for _ in range(10)]
        ctx = _context(blocks=blocks)

        # Only 8 of 10 assigned (80%)
        assignments = [_assignment(uuid4(), b.id) for b in blocks[:8]]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert "80.0%" in result.violations[0].message

    def test_at_90_percent_no_violation(self):
        """Coverage >= 90% -> no violation."""
        c = CoverageConstraint()
        blocks = [_block(is_weekend=False) for _ in range(10)]
        ctx = _context(blocks=blocks)

        # 9 of 10 assigned (90%)
        assignments = [_assignment(uuid4(), b.id) for b in blocks[:9]]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 0

    def test_weekend_blocks_excluded(self):
        """Weekend blocks don't count toward coverage denominator."""
        c = CoverageConstraint()
        b_weekday = _block(is_weekend=False)
        b_weekend = _block(is_weekend=True)
        ctx = _context(blocks=[b_weekday, b_weekend])

        # Only weekday assigned
        assignments = [_assignment(uuid4(), b_weekday.id)]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0  # 1/1 workday blocks = 100%

    def test_all_weekend_no_workdays(self):
        """No workday blocks -> coverage_rate=0, penalty=weight."""
        c = CoverageConstraint(weight=100.0)
        b1 = _block(is_weekend=True)
        ctx = _context(blocks=[b1])

        result = c.validate([], ctx)
        # workday_blocks = [], coverage_rate = 0
        assert result.penalty == pytest.approx(100.0)

    def test_always_satisfied(self):
        """Soft constraint -> always satisfied."""
        c = CoverageConstraint()
        ctx = _context(blocks=[_block(is_weekend=False)])
        result = c.validate([], ctx)
        assert result.satisfied is True
