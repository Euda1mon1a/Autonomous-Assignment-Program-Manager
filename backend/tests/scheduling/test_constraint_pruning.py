"""
Tests for constraint pruning optimization.

Comprehensive test suite for ConstraintPruner class,
covering early feasibility checking and search space reduction.
"""

import pytest
from datetime import date
from uuid import uuid4

from app.scheduling.optimizer.constraint_pruning import (
    ConstraintPruner,
    prune_infeasible_assignments,
)


@pytest.fixture
def sample_persons():
    """Create sample person data for testing."""
    return [
        {
            "id": str(uuid4()),
            "name": "PGY1-01",
            "type": "resident",
            "pgy_level": 1,
            "specialties": ["family_medicine"],
            "unavailable_dates": [],
        },
        {
            "id": str(uuid4()),
            "name": "PGY2-01",
            "type": "resident",
            "pgy_level": 2,
            "specialties": ["family_medicine"],
            "unavailable_dates": [],
        },
        {
            "id": str(uuid4()),
            "name": "FAC-01",
            "type": "faculty",
            "pgy_level": None,
            "specialties": ["family_medicine", "cardiology"],
            "unavailable_dates": [],
        },
    ]


@pytest.fixture
def sample_rotations():
    """Create sample rotation data for testing."""
    return [
        {
            "id": str(uuid4()),
            "name": "Inpatient",
            "allowed_person_types": ["resident", "faculty"],
            "min_pgy_level": 1,
            "max_pgy_level": 3,
        },
        {
            "id": str(uuid4()),
            "name": "PGY2+ Only",
            "allowed_person_types": ["resident"],
            "min_pgy_level": 2,
        },
        {
            "id": str(uuid4()),
            "name": "Cardiology Clinic",
            "allowed_person_types": ["faculty"],
            "required_specialties": ["cardiology"],
        },
        {
            "id": str(uuid4()),
            "name": "AM Only",
            "allowed_person_types": ["resident", "faculty"],
            "time_of_day": "AM",
        },
    ]


@pytest.fixture
def sample_blocks():
    """Create sample block data for testing."""
    return [
        {
            "id": str(uuid4()),
            "date": date(2025, 1, 1),
            "is_am": True,
        },
        {
            "id": str(uuid4()),
            "date": date(2025, 1, 1),
            "is_am": False,
        },
        {
            "id": str(uuid4()),
            "date": date(2025, 1, 2),
            "is_am": True,
        },
    ]


class TestConstraintPruner:
    """Test suite for ConstraintPruner class."""

    def test_initialization(self):
        """Test pruner initializes with zero counters."""
        # Act
        pruner = ConstraintPruner()

        # Assert
        assert pruner.pruned_count == 0
        assert pruner.total_evaluated == 0

    def test_prune_assignments_basic(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test basic pruning of infeasible assignments."""
        # Arrange
        pruner = ConstraintPruner()

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Assert
        assert "feasible_assignments" in result
        assert "total_evaluated" in result
        assert "pruned_count" in result
        assert "pruning_reasons" in result
        assert "reduction_ratio" in result
        assert isinstance(result["feasible_assignments"], list)
        assert result["total_evaluated"] > 0

    def test_prune_by_person_type(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test pruning based on person type restrictions."""
        # Arrange
        pruner = ConstraintPruner()

        # Cardiology clinic only allows faculty
        cardiology_rotation = next(
            r for r in sample_rotations if r["name"] == "Cardiology Clinic"
        )

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=[cardiology_rotation],
            blocks=sample_blocks,
        )

        # Assert
        # Only faculty should be assigned to cardiology clinic
        for assignment in result["feasible_assignments"]:
            person = next(
                p for p in sample_persons if p["id"] == assignment["person_id"]
            )
            assert person["type"] == "faculty"

    def test_prune_by_pgy_level(self, sample_persons, sample_rotations, sample_blocks):
        """Test pruning based on PGY level restrictions."""
        # Arrange
        pruner = ConstraintPruner()

        # PGY2+ rotation
        pgy2_rotation = next(r for r in sample_rotations if r["name"] == "PGY2+ Only")

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=[pgy2_rotation],
            blocks=sample_blocks,
        )

        # Assert
        # Only PGY2+ residents should be assigned
        for assignment in result["feasible_assignments"]:
            person = next(
                p for p in sample_persons if p["id"] == assignment["person_id"]
            )
            assert person.get("pgy_level", 999) >= 2

    def test_prune_by_specialty(self, sample_persons, sample_rotations, sample_blocks):
        """Test pruning based on specialty requirements."""
        # Arrange
        pruner = ConstraintPruner()

        # Cardiology clinic requires cardiology specialty
        cardiology_rotation = next(
            r for r in sample_rotations if r["name"] == "Cardiology Clinic"
        )

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=[cardiology_rotation],
            blocks=sample_blocks,
        )

        # Assert
        # Only people with cardiology specialty should be assigned
        for assignment in result["feasible_assignments"]:
            person = next(
                p for p in sample_persons if p["id"] == assignment["person_id"]
            )
            assert "cardiology" in person.get("specialties", [])

    def test_prune_by_time_of_day(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test pruning based on time of day restrictions."""
        # Arrange
        pruner = ConstraintPruner()

        # AM only rotation
        am_rotation = next(r for r in sample_rotations if r["name"] == "AM Only")

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=[am_rotation],
            blocks=sample_blocks,
        )

        # Assert
        # Only AM blocks should have assignments
        for assignment in result["feasible_assignments"]:
            block = next(b for b in sample_blocks if b["id"] == assignment["block_id"])
            assert block["is_am"] is True

    def test_prune_by_unavailability(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test pruning based on person unavailability."""
        # Arrange
        pruner = ConstraintPruner()

        # Mark one person as unavailable on Jan 1
        sample_persons[0]["unavailable_dates"] = [date(2025, 1, 1)]

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Assert
        # First person should not be assigned on Jan 1
        person_id = sample_persons[0]["id"]
        jan_1_blocks = [b["id"] for b in sample_blocks if b["date"] == date(2025, 1, 1)]

        for assignment in result["feasible_assignments"]:
            if assignment["person_id"] == person_id:
                assert assignment["block_id"] not in jan_1_blocks

    def test_prune_with_existing_assignments(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test pruning skips existing assignments."""
        # Arrange
        pruner = ConstraintPruner()

        existing = [
            {
                "person_id": sample_persons[0]["id"],
                "block_id": sample_blocks[0]["id"],
                "rotation_id": sample_rotations[0]["id"],
            }
        ]

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
            existing_assignments=existing,
        )

        # Assert
        # Existing assignment should not be in feasible assignments
        key = (sample_persons[0]["id"], sample_blocks[0]["id"])
        assert not any(
            (a["person_id"], a["block_id"]) == key
            for a in result["feasible_assignments"]
        )

    def test_pruning_reasons_tracked(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test pruning reasons are tracked correctly."""
        # Arrange
        pruner = ConstraintPruner()

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Assert
        assert "pruning_reasons" in result
        assert isinstance(result["pruning_reasons"], dict)
        # Should have some pruning reasons (e.g., person_type_mismatch, pgy_level_too_low)
        if result["pruned_count"] > 0:
            assert len(result["pruning_reasons"]) > 0

    def test_reduction_ratio_calculated(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test reduction ratio is calculated correctly."""
        # Arrange
        pruner = ConstraintPruner()

        # Act
        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Assert
        expected_ratio = (
            result["pruned_count"] / result["total_evaluated"]
            if result["total_evaluated"] > 0
            else 0
        )
        assert result["reduction_ratio"] == pytest.approx(expected_ratio)
        assert 0 <= result["reduction_ratio"] <= 1

    def test_estimate_search_space_reduction(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test estimating search space reduction from pruning."""
        # Arrange
        pruner = ConstraintPruner()

        result = pruner.prune_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Act
        estimation = pruner.estimate_search_space_reduction(result)

        # Assert
        assert "total_combinations" in estimation
        assert "pruned_combinations" in estimation
        assert "remaining_combinations" in estimation
        assert "reduction_ratio" in estimation
        assert "estimated_search_space_reduction_factor" in estimation
        assert "estimated_solver_speedup" in estimation

        assert estimation["total_combinations"] == result["total_evaluated"]
        assert estimation["pruned_combinations"] == result["pruned_count"]
        assert (
            estimation["remaining_combinations"]
            == result["total_evaluated"] - result["pruned_count"]
        )


class TestPruneInfeasibleAssignmentsUtility:
    """Test suite for utility function."""

    def test_utility_function_works(
        self, sample_persons, sample_rotations, sample_blocks
    ):
        """Test utility function creates pruner and returns result."""
        # Act
        result = prune_infeasible_assignments(
            persons=sample_persons,
            rotations=sample_rotations,
            blocks=sample_blocks,
        )

        # Assert
        assert "feasible_assignments" in result
        assert "total_evaluated" in result
        assert "pruned_count" in result
        assert isinstance(result, dict)
