"""Tests for faculty preference constraint (pure logic, no DB required)."""

from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.faculty import PreferenceConstraint


# ==================== Helpers ====================


def _person(pid=None, name="Faculty"):
    return SimpleNamespace(id=pid or uuid4(), name=name)


def _context():
    return SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])


def _assignment(person_id, block_id, rotation_template_id=None):
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )


# ==================== PreferenceConstraint Tests ====================


class TestPreferenceConstraintInit:
    def test_name(self):
        c = PreferenceConstraint()
        assert c.name == "Preferences"

    def test_type(self):
        c = PreferenceConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE

    def test_priority(self):
        c = PreferenceConstraint()
        assert c.priority == ConstraintPriority.LOW

    def test_default_weight(self):
        c = PreferenceConstraint()
        assert c.weight == 2.0

    def test_custom_weight(self):
        c = PreferenceConstraint(weight=5.0)
        assert c.weight == 5.0

    def test_default_preferences_empty(self):
        c = PreferenceConstraint()
        assert c.preferences == {}

    def test_custom_preferences(self):
        pid = uuid4()
        tid = uuid4()
        prefs = {pid: {tid: 0.9}}
        c = PreferenceConstraint(preferences=prefs)
        assert c.preferences[pid][tid] == 0.9


class TestPreferenceConstraintValidate:
    def test_no_assignments_satisfied(self):
        c = PreferenceConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_no_rotation_template_id_zero_penalty(self):
        """Assignments without rotation_template_id -> no preference scored."""
        c = PreferenceConstraint()
        ctx = _context()
        a = _assignment(uuid4(), uuid4(), rotation_template_id=None)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_perfect_preference_zero_penalty(self):
        """Score 1.0 for each assignment -> satisfaction=1.0 -> penalty=0."""
        pid = uuid4()
        tid = uuid4()
        c = PreferenceConstraint(preferences={pid: {tid: 1.0}})
        ctx = _context()
        a = _assignment(pid, uuid4(), rotation_template_id=tid)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_zero_preference_max_penalty(self):
        """Score 0.0 -> satisfaction=0.0 -> penalty = (1-0)*weight*count."""
        pid = uuid4()
        tid = uuid4()
        c = PreferenceConstraint(preferences={pid: {tid: 0.0}}, weight=2.0)
        ctx = _context()
        a = _assignment(pid, uuid4(), rotation_template_id=tid)
        result = c.validate([a], ctx)
        # penalty = (1 - 0.0) * 2.0 * 1 = 2.0
        assert result.penalty == 2.0

    def test_neutral_preference_half_penalty(self):
        """No preference data -> default 0.5 -> satisfaction=0.5."""
        pid = uuid4()
        tid = uuid4()
        c = PreferenceConstraint(preferences={}, weight=2.0)
        ctx = _context()
        a = _assignment(pid, uuid4(), rotation_template_id=tid)
        result = c.validate([a], ctx)
        # default score 0.5, satisfaction = 0.5/1.0 = 0.5
        # penalty = (1 - 0.5) * 2.0 * 1 = 1.0
        assert result.penalty == 1.0

    def test_multiple_assignments_penalty(self):
        """Multiple assignments scale the penalty."""
        pid = uuid4()
        tid = uuid4()
        c = PreferenceConstraint(preferences={pid: {tid: 0.0}}, weight=2.0)
        ctx = _context()
        assignments = [
            _assignment(pid, uuid4(), rotation_template_id=tid) for _ in range(3)
        ]
        result = c.validate(assignments, ctx)
        # satisfaction = 0/3 = 0, penalty = (1-0)*2.0*3 = 6.0
        assert result.penalty == 6.0

    def test_always_satisfied(self):
        """PreferenceConstraint is soft -> always satisfied."""
        pid = uuid4()
        tid = uuid4()
        c = PreferenceConstraint(preferences={pid: {tid: 0.0}})
        ctx = _context()
        a = _assignment(pid, uuid4(), rotation_template_id=tid)
        result = c.validate([a], ctx)
        assert result.satisfied is True
