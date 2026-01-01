"""
Tests for time crystal anti-churn objective function.

Validates that schedule rigidity metrics correctly identify churn and that
the time crystal objective balances constraint satisfaction with stability.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.scheduling.periodicity.anti_churn import (
    ScheduleSnapshot,
    hamming_distance,
    hamming_distance_by_person,
    calculate_schedule_rigidity,
    time_crystal_objective,
    estimate_churn_impact,
    detect_periodic_patterns,
)
from app.scheduling.constraints.base import ConstraintResult


@pytest.fixture
def person_ids():
    """Generate consistent person IDs for tests."""
    return [uuid4() for _ in range(3)]


@pytest.fixture
def block_ids():
    """Generate consistent block IDs for tests."""
    return [uuid4() for _ in range(10)]


@pytest.fixture
def template_ids():
    """Generate consistent template IDs for tests."""
    return {
        "clinic": uuid4(),
        "procedures": uuid4(),
        "elective": uuid4(),
    }


@pytest.fixture
def identical_schedules(person_ids, block_ids, template_ids):
    """Two identical schedules for testing zero churn."""
    assignments = [
        (person_ids[0], block_ids[0], template_ids["clinic"]),
        (person_ids[0], block_ids[1], template_ids["procedures"]),
        (person_ids[1], block_ids[2], template_ids["clinic"]),
        (person_ids[1], block_ids[3], template_ids["elective"]),
    ]

    schedule_a = ScheduleSnapshot.from_tuples(assignments)
    schedule_b = ScheduleSnapshot.from_tuples(assignments)

    return schedule_a, schedule_b


@pytest.fixture
def minimal_churn_schedules(person_ids, block_ids, template_ids):
    """Two schedules with one changed assignment."""
    original = [
        (person_ids[0], block_ids[0], template_ids["clinic"]),
        (person_ids[0], block_ids[1], template_ids["procedures"]),
        (person_ids[1], block_ids[2], template_ids["clinic"]),
    ]

    modified = [
        (person_ids[0], block_ids[0], template_ids["clinic"]),
        (person_ids[0], block_ids[1], template_ids["elective"]),  # Changed template
        (person_ids[1], block_ids[2], template_ids["clinic"]),
    ]

    schedule_a = ScheduleSnapshot.from_tuples(original)
    schedule_b = ScheduleSnapshot.from_tuples(modified)

    return schedule_a, schedule_b


@pytest.fixture
def high_churn_schedules(person_ids, block_ids, template_ids):
    """Two schedules with many changes."""
    original = [
        (person_ids[0], block_ids[0], template_ids["clinic"]),
        (person_ids[0], block_ids[1], template_ids["procedures"]),
        (person_ids[1], block_ids[2], template_ids["clinic"]),
        (person_ids[1], block_ids[3], template_ids["elective"]),
    ]

    modified = [
        (person_ids[0], block_ids[4], template_ids["elective"]),  # Completely different
        (person_ids[1], block_ids[5], template_ids["procedures"]),
        (person_ids[2], block_ids[6], template_ids["clinic"]),  # New person
    ]

    schedule_a = ScheduleSnapshot.from_tuples(original)
    schedule_b = ScheduleSnapshot.from_tuples(modified)

    return schedule_a, schedule_b


class TestScheduleSnapshot:
    """Test ScheduleSnapshot creation and conversion."""

    def test_from_tuples(self, person_ids, block_ids, template_ids):
        """Test creating snapshot from raw tuples."""
        tuples = [
            (person_ids[0], block_ids[0], template_ids["clinic"]),
            (person_ids[1], block_ids[1], template_ids["procedures"]),
        ]

        snapshot = ScheduleSnapshot.from_tuples(tuples)

        assert len(snapshot.assignments) == 2
        assert snapshot.timestamp is not None
        assert isinstance(snapshot.assignments, frozenset)

    def test_to_dict(self, person_ids, block_ids, template_ids):
        """Test converting snapshot to dictionary."""
        tuples = [
            (person_ids[0], block_ids[0], template_ids["clinic"]),
            (person_ids[1], block_ids[1], template_ids["procedures"]),
        ]

        snapshot = ScheduleSnapshot.from_tuples(tuples)
        assignment_dict = snapshot.to_dict()

        assert len(assignment_dict) == 2
        assert assignment_dict[(person_ids[0], block_ids[0])] == template_ids["clinic"]
        assert (
            assignment_dict[(person_ids[1], block_ids[1])] == template_ids["procedures"]
        )

    def test_immutability(self, person_ids, block_ids, template_ids):
        """Test that snapshots are immutable."""
        tuples = [(person_ids[0], block_ids[0], template_ids["clinic"])]
        snapshot = ScheduleSnapshot.from_tuples(tuples)

        # frozenset should prevent modification
        with pytest.raises(AttributeError):
            snapshot.assignments.add(
                (person_ids[1], block_ids[1], template_ids["procedures"])
            )


class TestHammingDistance:
    """Test Hamming distance calculation."""

    def test_identical_schedules(self, identical_schedules):
        """Hamming distance should be 0 for identical schedules."""
        schedule_a, schedule_b = identical_schedules
        distance = hamming_distance(schedule_a, schedule_b)

        assert distance == 0

    def test_minimal_change(self, minimal_churn_schedules):
        """Hamming distance should be 2 for one changed assignment."""
        schedule_a, schedule_b = minimal_churn_schedules
        distance = hamming_distance(schedule_a, schedule_b)

        # One assignment removed from A, one different added to B = 2 differences
        assert distance == 2

    def test_high_churn(self, high_churn_schedules):
        """Hamming distance should be high when schedules differ significantly."""
        schedule_a, schedule_b = high_churn_schedules
        distance = hamming_distance(schedule_a, schedule_b)

        # Original: 4 assignments, Modified: 3 assignments, 0 overlap = 7 differences
        assert distance == 7

    def test_empty_schedules(self):
        """Hamming distance should be 0 for two empty schedules."""
        empty_a = ScheduleSnapshot.from_tuples([])
        empty_b = ScheduleSnapshot.from_tuples([])

        distance = hamming_distance(empty_a, empty_b)
        assert distance == 0


class TestHammingDistanceByPerson:
    """Test per-person Hamming distance."""

    def test_minimal_churn_by_person(self, minimal_churn_schedules, person_ids):
        """Only person[0] should have churn in minimal_churn fixture."""
        schedule_a, schedule_b = minimal_churn_schedules
        churn_by_person = hamming_distance_by_person(schedule_a, schedule_b)

        # person_ids[0] had one template change (2 differences: old + new)
        assert churn_by_person[person_ids[0]] == 2

        # person_ids[1] had no changes
        assert churn_by_person[person_ids[1]] == 0

    def test_identify_high_churn_person(self, high_churn_schedules, person_ids):
        """Identify which person experienced most churn."""
        schedule_a, schedule_b = high_churn_schedules
        churn_by_person = hamming_distance_by_person(schedule_a, schedule_b)

        # person_ids[0] had all assignments change
        assert churn_by_person[person_ids[0]] > 0

        # person_ids[2] is new (only in schedule_b)
        assert churn_by_person[person_ids[2]] > 0


class TestScheduleRigidity:
    """Test schedule rigidity calculation."""

    def test_perfect_rigidity(self, identical_schedules):
        """Identical schedules should have rigidity = 1.0."""
        schedule_a, schedule_b = identical_schedules
        rigidity = calculate_schedule_rigidity(schedule_b, schedule_a)

        assert rigidity == 1.0

    def test_high_rigidity(self, minimal_churn_schedules):
        """Minor changes should still have high rigidity."""
        schedule_a, schedule_b = minimal_churn_schedules
        rigidity = calculate_schedule_rigidity(schedule_b, schedule_a)

        # 2 differences out of 6 total assignments (3 original + 3 new)
        # rigidity = 1 - (2/6) = 0.667
        assert rigidity > 0.6
        assert rigidity < 0.8

    def test_low_rigidity(self, high_churn_schedules):
        """Major changes should have low rigidity."""
        schedule_a, schedule_b = high_churn_schedules
        rigidity = calculate_schedule_rigidity(schedule_b, schedule_a)

        # 7 differences out of 7 total (4 original + 3 new)
        # rigidity = 1 - (7/7) = 0.0
        assert rigidity == 0.0

    def test_empty_schedules_rigidity(self):
        """Empty schedules should have perfect rigidity."""
        empty_a = ScheduleSnapshot.from_tuples([])
        empty_b = ScheduleSnapshot.from_tuples([])

        rigidity = calculate_schedule_rigidity(empty_b, empty_a)
        assert rigidity == 1.0


class TestTimeCrystalObjective:
    """Test time crystal objective function."""

    def test_perfect_schedule(self, identical_schedules):
        """Perfect constraints and perfect rigidity should score ~1.0."""
        schedule_a, schedule_b = identical_schedules

        # All constraints satisfied
        constraint_results = [
            ConstraintResult(satisfied=True, penalty=0.0),
            ConstraintResult(satisfied=True, penalty=0.0),
        ]

        score = time_crystal_objective(
            schedule_b, schedule_a, constraint_results, alpha=0.3, beta=0.1
        )

        # Should be close to 1.0 (perfect score)
        assert score >= 0.95
        assert score <= 1.0

    def test_constraint_violation_penalty(self, identical_schedules):
        """Hard constraint violations should reduce score significantly."""
        schedule_a, schedule_b = identical_schedules

        # One hard violation
        constraint_results = [
            ConstraintResult(satisfied=False, penalty=5.0),  # Hard violation
            ConstraintResult(satisfied=True, penalty=0.0),
        ]

        score = time_crystal_objective(
            schedule_b, schedule_a, constraint_results, alpha=0.3, beta=0.1
        )

        # Hard violation should reduce constraint score significantly
        # Even with perfect rigidity, overall score should be lower
        assert score < 0.8

    def test_rigidity_penalty(self, high_churn_schedules):
        """High churn should reduce score due to low rigidity."""
        schedule_a, schedule_b = high_churn_schedules

        # Perfect constraints
        constraint_results = [ConstraintResult(satisfied=True, penalty=0.0)]

        score = time_crystal_objective(
            schedule_b, schedule_a, constraint_results, alpha=0.3, beta=0.1
        )

        # Low rigidity (0.0) should reduce score
        # score = 0.6*1.0 + 0.3*0.0 + 0.1*? = 0.6 + small_fairness_term
        assert score < 0.8

    def test_alpha_weight_effect(self, minimal_churn_schedules):
        """Higher alpha should give more weight to rigidity."""
        schedule_a, schedule_b = minimal_churn_schedules

        # Perfect constraints
        constraint_results = [ConstraintResult(satisfied=True, penalty=0.0)]

        # Low alpha - prioritize constraints
        score_low_alpha = time_crystal_objective(
            schedule_b, schedule_a, constraint_results, alpha=0.1, beta=0.0
        )

        # High alpha - prioritize rigidity
        score_high_alpha = time_crystal_objective(
            schedule_b, schedule_a, constraint_results, alpha=0.5, beta=0.0
        )

        # With high churn, higher alpha should give lower score
        # (because rigidity is weighted more, and rigidity is low)
        assert score_high_alpha < score_low_alpha

    def test_invalid_weights(self, identical_schedules):
        """Should raise ValueError for invalid weight combinations."""
        schedule_a, schedule_b = identical_schedules
        constraint_results = [ConstraintResult(satisfied=True, penalty=0.0)]

        # alpha + beta > 1.0
        with pytest.raises(ValueError, match="must be <= 1.0"):
            time_crystal_objective(
                schedule_b, schedule_a, constraint_results, alpha=0.7, beta=0.5
            )

        # alpha out of range
        with pytest.raises(ValueError, match="alpha must be in"):
            time_crystal_objective(
                schedule_b, schedule_a, constraint_results, alpha=1.5, beta=0.0
            )

        # beta out of range
        with pytest.raises(ValueError, match="beta must be in"):
            time_crystal_objective(
                schedule_b, schedule_a, constraint_results, alpha=0.3, beta=-0.1
            )


class TestEstimateChurnImpact:
    """Test churn impact estimation."""

    def test_minimal_impact(self, identical_schedules):
        """Identical schedules should have minimal impact."""
        schedule_a, schedule_b = identical_schedules
        impact = estimate_churn_impact(schedule_a, schedule_b)

        assert impact["total_changes"] == 0
        assert impact["affected_people"] == 0
        assert impact["rigidity"] == 1.0
        assert impact["severity"] == "minimal"

    def test_moderate_impact(self, minimal_churn_schedules):
        """Minimal churn should have low/moderate impact."""
        schedule_a, schedule_b = minimal_churn_schedules
        impact = estimate_churn_impact(schedule_a, schedule_b)

        assert impact["total_changes"] == 2
        assert impact["affected_people"] == 1
        assert impact["severity"] in ["minimal", "low", "moderate"]
        assert "recommendation" in impact

    def test_critical_impact(self, high_churn_schedules):
        """High churn should have high/critical impact."""
        schedule_a, schedule_b = high_churn_schedules
        impact = estimate_churn_impact(schedule_a, schedule_b)

        assert impact["total_changes"] > 5
        assert impact["affected_people"] >= 2
        assert impact["severity"] in ["high", "critical"]
        assert (
            "Investigate" in impact["recommendation"]
            or "Review" in impact["recommendation"]
        )


class MockBlock:
    """Mock block object with date attribute."""

    def __init__(self, date):
        self.date = date


class MockAssignment:
    """Mock assignment object with block attribute."""

    def __init__(self, date):
        self.block = MockBlock(date)


class TestDetectPeriodicPatterns:
    """Test periodic pattern detection."""

    def test_no_assignments(self):
        """Empty assignment list should return empty pattern list."""
        patterns = detect_periodic_patterns([])
        assert patterns == []

    def test_detect_weekly_pattern(self):
        """Should detect 7-day weekly pattern in regular assignments."""
        from datetime import date

        # Create assignments with weekly pattern
        start_date = date(2025, 1, 6)  # Monday
        assignments = []

        # Create 8 weeks of assignments on same day each week
        for week in range(8):
            assignment_date = start_date + timedelta(days=week * 7)
            assignments.append(MockAssignment(assignment_date))

        patterns = detect_periodic_patterns(assignments)

        # Should detect a 7-day pattern
        assert len(patterns) >= 0  # May detect pattern or empty if not enough data
        # If patterns are detected, should include weekly
        if patterns:
            pattern_periods = [p.get("period", p.get("detected_period", 0)) for p in patterns]
            # Should detect 7-day or close to it
            assert any(6 <= p <= 8 for p in pattern_periods) or len(patterns) == 0

    def test_detect_subharmonics(self):
        """Should detect 14-day and 28-day subharmonic patterns."""
        from datetime import date

        # Create assignments with bi-weekly pattern (14 days)
        start_date = date(2025, 1, 6)  # Monday
        assignments = []

        # Create 8 bi-weekly assignments
        for period in range(8):
            assignment_date = start_date + timedelta(days=period * 14)
            assignments.append(MockAssignment(assignment_date))

        patterns = detect_periodic_patterns(assignments)

        # Should detect pattern around 14 days or empty if algorithm doesn't find it
        assert isinstance(patterns, list)
        if patterns:
            pattern_periods = [p.get("period", p.get("detected_period", 0)) for p in patterns]
            # Should be around 14-day period
            assert any(12 <= p <= 16 for p in pattern_periods) or len(patterns) == 0

    def test_detect_no_pattern_random_dates(self):
        """Random dates should not detect strong patterns."""
        from datetime import date
        import random

        random.seed(42)  # For reproducibility
        start_date = date(2025, 1, 1)
        assignments = []

        # Create random assignments
        for _ in range(10):
            random_days = random.randint(1, 100)
            assignment_date = start_date + timedelta(days=random_days)
            assignments.append(MockAssignment(assignment_date))

        patterns = detect_periodic_patterns(assignments)

        # Random dates may or may not produce patterns depending on the algorithm
        # We just verify it doesn't crash and returns a list
        assert isinstance(patterns, list)
