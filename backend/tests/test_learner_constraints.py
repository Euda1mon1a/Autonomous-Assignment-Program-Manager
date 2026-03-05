"""Tests for learner scheduling constraints."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import ConstraintResult, SchedulingContext
from app.scheduling.constraints.learner import (
    LearnerASMWednesdayConstraint,
    LearnerDoubleBookingConstraint,
    LearnerFMITBlockingConstraint,
    LearnerSupervisionConstraint,
    LearnerTrackBalanceConstraint,
)


def _make_context() -> SchedulingContext:
    """Minimal scheduling context for testing."""
    return SchedulingContext(
        residents=[],
        faculty=[],
        blocks=[],
        templates=[],
    )


def _make_assignment(
    learner_id=None,
    block_id=None,
    day_of_week=0,
    time_of_day="AM",
    activity_type="clinic",
    parent_assignment_id=None,
    track_id=None,
):
    """Create a mock learner assignment."""
    a = MagicMock()
    a.learner_id = learner_id or uuid4()
    a.block_id = block_id or uuid4()
    a.day_of_week = day_of_week
    a.time_of_day = time_of_day
    a.activity_type = activity_type
    a.parent_assignment_id = parent_assignment_id
    a.track_id = track_id
    return a


class TestLearnerSupervisionConstraint:
    def test_no_violations_under_limit(self):
        constraint = LearnerSupervisionConstraint()
        ctx = _make_context()
        parent_id = uuid4()
        assignments = [
            _make_assignment(parent_assignment_id=parent_id),
            _make_assignment(parent_assignment_id=parent_id),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied

    def test_violation_over_limit(self):
        constraint = LearnerSupervisionConstraint()
        ctx = _make_context()
        parent_id = uuid4()
        assignments = [
            _make_assignment(parent_assignment_id=parent_id),
            _make_assignment(parent_assignment_id=parent_id),
            _make_assignment(parent_assignment_id=parent_id),
        ]
        result = constraint.validate(assignments, ctx)
        assert not result.satisfied
        assert len(result.violations) == 1
        assert "max 2" in result.violations[0].message

    def test_no_parent_ok(self):
        constraint = LearnerSupervisionConstraint()
        ctx = _make_context()
        assignments = [
            _make_assignment(parent_assignment_id=None),
            _make_assignment(parent_assignment_id=None),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied


class TestLearnerASMWednesdayConstraint:
    def test_asm_on_wednesday_am_ok(self):
        constraint = LearnerASMWednesdayConstraint()
        ctx = _make_context()
        assignments = [
            _make_assignment(day_of_week=2, time_of_day="AM", activity_type="ASM"),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied

    def test_asm_on_wrong_day_violated(self):
        constraint = LearnerASMWednesdayConstraint()
        ctx = _make_context()
        assignments = [
            _make_assignment(day_of_week=1, time_of_day="AM", activity_type="ASM"),
        ]
        result = constraint.validate(assignments, ctx)
        assert not result.satisfied
        assert "Wednesday AM" in result.violations[0].message

    def test_asm_on_wednesday_pm_violated(self):
        constraint = LearnerASMWednesdayConstraint()
        ctx = _make_context()
        assignments = [
            _make_assignment(day_of_week=2, time_of_day="PM", activity_type="ASM"),
        ]
        result = constraint.validate(assignments, ctx)
        assert not result.satisfied

    def test_non_asm_on_any_day_ok(self):
        constraint = LearnerASMWednesdayConstraint()
        ctx = _make_context()
        assignments = [
            _make_assignment(day_of_week=0, time_of_day="AM", activity_type="clinic"),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied


class TestLearnerDoubleBookingConstraint:
    def test_no_double_booking(self):
        constraint = LearnerDoubleBookingConstraint()
        ctx = _make_context()
        lid = uuid4()
        bid = uuid4()
        assignments = [
            _make_assignment(
                learner_id=lid, block_id=bid, day_of_week=0, time_of_day="AM"
            ),
            _make_assignment(
                learner_id=lid, block_id=bid, day_of_week=0, time_of_day="PM"
            ),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied

    def test_double_booking_detected(self):
        constraint = LearnerDoubleBookingConstraint()
        ctx = _make_context()
        lid = uuid4()
        bid = uuid4()
        assignments = [
            _make_assignment(
                learner_id=lid, block_id=bid, day_of_week=0, time_of_day="AM"
            ),
            _make_assignment(
                learner_id=lid, block_id=bid, day_of_week=0, time_of_day="AM"
            ),
        ]
        result = constraint.validate(assignments, ctx)
        assert not result.satisfied
        assert len(result.violations) == 1


class TestLearnerTrackBalanceConstraint:
    def test_balanced_tracks(self):
        constraint = LearnerTrackBalanceConstraint()
        ctx = _make_context()
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        assignments = [
            _make_assignment(track_id=t1),
            _make_assignment(track_id=t2),
            _make_assignment(track_id=t3),
        ]
        result = constraint.validate(assignments, ctx)
        assert result.satisfied
        assert result.penalty == 0.0

    def test_imbalanced_tracks_penalty(self):
        constraint = LearnerTrackBalanceConstraint()
        ctx = _make_context()
        t1, t2 = uuid4(), uuid4()
        assignments = [
            _make_assignment(track_id=t1),
            _make_assignment(track_id=t1),
            _make_assignment(track_id=t1),
            _make_assignment(track_id=t1),
            _make_assignment(track_id=t2),
        ]
        result = constraint.validate(assignments, ctx)
        # Imbalance is 3, should have penalty and violation
        assert len(result.violations) == 1
        assert result.penalty > 0


class TestLearnerFMITBlockingConstraint:
    def test_validate_passes_without_context(self):
        constraint = LearnerFMITBlockingConstraint()
        ctx = _make_context()
        result = constraint.validate([], ctx)
        assert result.satisfied
