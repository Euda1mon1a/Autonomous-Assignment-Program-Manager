"""Tests for equity and continuity constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.equity import (
    ContinuityConstraint,
    EquityConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, target_clinical_blocks=None):
    """Build a mock person with .id attribute."""
    ns = SimpleNamespace(id=pid or uuid4())
    if target_clinical_blocks is not None:
        ns.target_clinical_blocks = target_clinical_blocks
    return ns


def _block(bid=None, block_date=None):
    """Build a mock block with .id and .date attributes."""
    return SimpleNamespace(id=bid or uuid4(), date=block_date or date(2025, 3, 3))


def _template(tid=None):
    """Build a mock template with .id attribute."""
    return SimpleNamespace(id=tid or uuid4())


def _assignment(person_id, block_id, rotation_template_id=None):
    """Build a mock assignment."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id or uuid4(),
    )


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext with mock objects."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== EquityConstraint Init Tests ====================


class TestEquityConstraintInit:
    """Test EquityConstraint initialization."""

    def test_default_weight(self):
        c = EquityConstraint()
        assert c.weight == 10.0
        assert c.name == "Equity"
        assert c.constraint_type == ConstraintType.EQUITY
        assert c.priority == ConstraintPriority.MEDIUM

    def test_custom_weight(self):
        c = EquityConstraint(weight=25.0)
        assert c.weight == 25.0

    def test_is_soft_constraint(self):
        c = EquityConstraint()
        assert hasattr(c, "weight")
        assert hasattr(c, "get_penalty")


# ==================== EquityConstraint.validate Tests ====================


class TestEquityConstraintValidate:
    """Test EquityConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        """Empty assignments -> satisfied, 0 penalty."""
        c = EquityConstraint()
        r1 = _person()
        ctx = _context(residents=[r1], blocks=[_block()])
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_balanced_assignments_zero_penalty(self):
        """Equal distribution -> spread=0, penalty=0."""
        c = EquityConstraint(weight=10.0)
        r1 = _person()
        r2 = _person()
        b1 = _block()
        b2 = _block()
        ctx = _context(residents=[r1, r2], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id),
            _assignment(r2.id, b2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0
        assert len(result.violations) == 0

    def test_imbalanced_assignments_penalty(self):
        """Unequal distribution -> non-zero penalty."""
        c = EquityConstraint(weight=10.0)
        r1 = _person()
        r2 = _person()
        blocks = [_block() for _ in range(4)]
        ctx = _context(residents=[r1, r2], blocks=blocks)

        # r1 gets 3 blocks, r2 gets 1
        assignments = [
            _assignment(r1.id, blocks[0].id),
            _assignment(r1.id, blocks[1].id),
            _assignment(r1.id, blocks[2].id),
            _assignment(r2.id, blocks[3].id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # Soft constraint always satisfied
        assert result.penalty == 20.0  # spread=2, weight=10

    def test_single_resident_zero_penalty(self):
        """One resident -> spread=0, penalty=0."""
        c = EquityConstraint()
        r1 = _person()
        b1 = _block()
        ctx = _context(residents=[r1], blocks=[b1])

        assignments = [_assignment(r1.id, b1.id)]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_penalty_scales_with_weight(self):
        """Higher weight -> higher penalty."""
        r1 = _person()
        r2 = _person()
        blocks = [_block() for _ in range(3)]
        ctx = _context(residents=[r1, r2], blocks=blocks)

        # r1=2, r2=1, spread=1
        assignments = [
            _assignment(r1.id, blocks[0].id),
            _assignment(r1.id, blocks[1].id),
            _assignment(r2.id, blocks[2].id),
        ]

        c10 = EquityConstraint(weight=10.0)
        c20 = EquityConstraint(weight=20.0)

        result10 = c10.validate(assignments, ctx)
        result20 = c20.validate(assignments, ctx)

        assert result20.penalty == result10.penalty * 2

    def test_non_resident_assignments_ignored(self):
        """Assignments for non-residents (e.g., faculty) are excluded."""
        c = EquityConstraint()
        r1 = _person()
        faculty_id = uuid4()  # Not in context.resident_idx
        b1 = _block()
        b2 = _block()
        ctx = _context(residents=[r1], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id),
            _assignment(faculty_id, b2.id),  # Not a resident
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0  # Only 1 resident, spread=0

    def test_large_spread_creates_violation(self):
        """Spread > blocks/residents -> ConstraintViolation."""
        c = EquityConstraint()
        r1 = _person()
        r2 = _person()
        blocks = [_block() for _ in range(6)]
        ctx = _context(residents=[r1, r2], blocks=blocks)

        # r1=5, r2=1, spread=4, threshold = 6//2 = 3 -> 4 > 3 triggers violation
        assignments = [
            _assignment(r1.id, blocks[0].id),
            _assignment(r1.id, blocks[1].id),
            _assignment(r1.id, blocks[2].id),
            _assignment(r1.id, blocks[3].id),
            _assignment(r1.id, blocks[4].id),
            _assignment(r2.id, blocks[5].id),
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert "imbalance" in result.violations[0].message.lower()

    def test_small_spread_no_violation(self):
        """Spread <= blocks/residents -> no violation."""
        c = EquityConstraint()
        r1 = _person()
        r2 = _person()
        blocks = [_block() for _ in range(4)]
        ctx = _context(residents=[r1, r2], blocks=blocks)

        # r1=3, r2=1, spread=2, threshold = 4//2 = 2 -> not > 2
        assignments = [
            _assignment(r1.id, blocks[0].id),
            _assignment(r1.id, blocks[1].id),
            _assignment(r1.id, blocks[2].id),
            _assignment(r2.id, blocks[3].id),
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 0

    def test_three_residents_spread(self):
        """3 residents, varying assignment counts."""
        c = EquityConstraint(weight=5.0)
        r1 = _person()
        r2 = _person()
        r3 = _person()
        blocks = [_block() for _ in range(6)]
        ctx = _context(residents=[r1, r2, r3], blocks=blocks)

        # r1=3, r2=2, r3=1, spread=2
        assignments = [
            _assignment(r1.id, blocks[0].id),
            _assignment(r1.id, blocks[1].id),
            _assignment(r1.id, blocks[2].id),
            _assignment(r2.id, blocks[3].id),
            _assignment(r2.id, blocks[4].id),
            _assignment(r3.id, blocks[5].id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 10.0  # spread=2, weight=5


# ==================== EquityConstraint.add_to_cpsat Tests ====================


class TestEquityConstraintAddToCpsat:
    """Test EquityConstraint.add_to_cpsat method."""

    def test_empty_assignments_returns_early(self):
        """No assignment variables -> returns without adding constraints."""
        c = EquityConstraint()
        ctx = _context(residents=[_person()], blocks=[_block()])

        # Empty variables dict
        variables = {}
        c.add_to_cpsat(None, variables, ctx)
        assert "equity_penalty" not in variables

    def test_empty_assignments_dict_returns_early(self):
        """Empty assignments dict -> returns without adding constraints."""
        c = EquityConstraint()
        ctx = _context(residents=[_person()], blocks=[_block()])

        variables = {"assignments": {}}
        c.add_to_cpsat(None, variables, ctx)
        assert "equity_penalty" not in variables


# ==================== ContinuityConstraint Init Tests ====================


class TestContinuityConstraintInit:
    """Test ContinuityConstraint initialization."""

    def test_default_weight(self):
        c = ContinuityConstraint()
        assert c.weight == 5.0
        assert c.name == "Continuity"
        assert c.constraint_type == ConstraintType.CONTINUITY
        assert c.priority == ConstraintPriority.LOW

    def test_custom_weight(self):
        c = ContinuityConstraint(weight=15.0)
        assert c.weight == 15.0


# ==================== ContinuityConstraint.validate Tests ====================


class TestContinuityConstraintValidate:
    """Test ContinuityConstraint.validate method."""

    def test_no_assignments_zero_penalty(self):
        c = ContinuityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_single_assignment_zero_penalty(self):
        """One assignment -> no consecutive pair -> 0 penalty."""
        c = ContinuityConstraint()
        b1 = _block(block_date=date(2025, 3, 3))
        r1 = _person()
        ctx = _context(residents=[r1], blocks=[b1])

        assignments = [_assignment(r1.id, b1.id, rotation_template_id=uuid4())]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_same_template_consecutive_zero_penalty(self):
        """Same template on consecutive days -> 0 changes -> 0 penalty."""
        c = ContinuityConstraint(weight=5.0)
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        r1 = _person()
        template_id = uuid4()
        ctx = _context(residents=[r1], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=template_id),
            _assignment(r1.id, b2.id, rotation_template_id=template_id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_different_template_consecutive_penalty(self):
        """Different templates on consecutive days -> 1 change -> weight penalty."""
        c = ContinuityConstraint(weight=5.0)
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        r1 = _person()
        ctx = _context(residents=[r1], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=uuid4()),
            _assignment(r1.id, b2.id, rotation_template_id=uuid4()),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 5.0  # 1 change * weight=5.0

    def test_non_consecutive_days_no_penalty(self):
        """Different templates but > 1 day apart -> not consecutive -> 0 penalty."""
        c = ContinuityConstraint(weight=5.0)
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 5))  # 2 days apart
        r1 = _person()
        ctx = _context(residents=[r1], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=uuid4()),
            _assignment(r1.id, b2.id, rotation_template_id=uuid4()),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_multiple_changes_accumulate(self):
        """Multiple template changes on consecutive days -> penalty scales."""
        c = ContinuityConstraint(weight=5.0)
        d1 = date(2025, 3, 3)
        b1 = _block(block_date=d1)
        b2 = _block(block_date=d1 + timedelta(days=1))
        b3 = _block(block_date=d1 + timedelta(days=2))
        r1 = _person()
        ctx = _context(residents=[r1], blocks=[b1, b2, b3])

        # 3 different templates on 3 consecutive days = 2 changes
        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=uuid4()),
            _assignment(r1.id, b2.id, rotation_template_id=uuid4()),
            _assignment(r1.id, b3.id, rotation_template_id=uuid4()),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 10.0  # 2 changes * weight=5.0

    def test_multiple_residents_independent(self):
        """Each resident's continuity is tracked independently."""
        c = ContinuityConstraint(weight=5.0)
        d1 = date(2025, 3, 3)
        b1 = _block(block_date=d1)
        b2 = _block(block_date=d1 + timedelta(days=1))
        r1 = _person()
        r2 = _person()
        t1 = uuid4()
        t2 = uuid4()
        ctx = _context(residents=[r1, r2], blocks=[b1, b2])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=t1),
            _assignment(r1.id, b2.id, rotation_template_id=t2),  # r1 changes
            _assignment(r2.id, b1.id, rotation_template_id=t1),
            _assignment(r2.id, b2.id, rotation_template_id=t1),  # r2 no change
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 5.0  # Only r1 has 1 change

    def test_always_satisfied(self):
        """Soft constraint -> always returns satisfied=True."""
        c = ContinuityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True


# ==================== ContinuityConstraint.add_to_cpsat Tests ====================


class TestContinuityConstraintAddToCpsat:
    """Test ContinuityConstraint.add_to_cpsat is a no-op."""

    def test_does_nothing(self):
        """add_to_cpsat is a pass-through (complexity handled in post-processing)."""
        c = ContinuityConstraint()
        variables = {"assignments": {}}
        c.add_to_cpsat(None, variables, _context())
        # Should not raise, should not modify variables
        assert "continuity_penalty" not in variables


class TestContinuityConstraintAddToPulp:
    """Test ContinuityConstraint.add_to_pulp is a no-op."""

    def test_does_nothing(self):
        c = ContinuityConstraint()
        variables = {"assignments": {}}
        c.add_to_pulp(None, variables, _context())
        assert "continuity_penalty" not in variables


# ==================== SchedulingContext Helper Tests ====================


class TestSchedulingContextHelpers:
    """Test SchedulingContext helper methods used by constraints."""

    def test_resident_idx_built(self):
        r1 = _person()
        r2 = _person()
        ctx = _context(residents=[r1, r2])
        assert ctx.resident_idx[r1.id] == 0
        assert ctx.resident_idx[r2.id] == 1

    def test_block_idx_built(self):
        b1 = _block()
        b2 = _block()
        ctx = _context(blocks=[b1, b2])
        assert ctx.block_idx[b1.id] == 0
        assert ctx.block_idx[b2.id] == 1

    def test_has_resilience_data_false(self):
        ctx = _context()
        assert ctx.has_resilience_data() is False

    def test_has_resilience_data_with_hub_scores(self):
        ctx = _context()
        ctx.hub_scores = {uuid4(): 0.5}
        assert ctx.has_resilience_data() is True

    def test_get_hub_score_default(self):
        ctx = _context()
        assert ctx.get_hub_score(uuid4()) == 0.0

    def test_is_n1_vulnerable(self):
        fac_id = uuid4()
        ctx = _context()
        ctx.n1_vulnerable_faculty = {fac_id}
        assert ctx.is_n1_vulnerable(fac_id) is True
        assert ctx.is_n1_vulnerable(uuid4()) is False

    def test_get_preference_strength_default(self):
        ctx = _context()
        assert ctx.get_preference_strength(uuid4(), "monday_am") == 0.5
