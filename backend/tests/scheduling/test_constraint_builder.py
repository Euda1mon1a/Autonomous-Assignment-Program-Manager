"""
Tests for Constraint Builder

Tests for fluent API, serialization, and constraint cloning.
"""

import json

import pytest

from app.scheduling.constraint_builder import (
    CompositeConstraintBuilder,
    ConstraintBuilder,
    ConstraintCloner,
    ConstraintSerializer,
    build_hard_constraint,
    build_soft_constraint,
)
from app.scheduling.constraints.acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    HardConstraint,
    SoftConstraint,
)


class TestConstraintBuilder:
    """Tests for fluent ConstraintBuilder."""

    def test_builder_initialization(self):
        """Test builder initializes correctly."""
        builder = ConstraintBuilder()
        assert builder._is_hard is True
        assert builder._weight == 1.0
        assert builder._enabled is True

    def test_build_hard_constraint(self):
        """Test building hard constraint."""
        constraint = (
            ConstraintBuilder()
            .hard()
            .name("TestConstraint")
            .type(ConstraintType.AVAILABILITY)
            .priority(ConstraintPriority.HIGH)
            .build()
        )

        assert isinstance(constraint, HardConstraint)
        assert constraint.name == "TestConstraint"
        assert constraint.constraint_type == ConstraintType.AVAILABILITY
        assert constraint.priority == ConstraintPriority.HIGH

    def test_build_soft_constraint(self):
        """Test building soft constraint."""
        constraint = (
            ConstraintBuilder()
            .soft(weight=1.5)
            .name("TestPreference")
            .type(ConstraintType.PREFERENCE)
            .build()
        )

        assert isinstance(constraint, SoftConstraint)
        assert constraint.name == "TestPreference"
        assert constraint.weight == 1.5

    def test_builder_chaining(self):
        """Test builder method chaining."""
        constraint = (
            ConstraintBuilder()
            .hard()
            .name("Chained")
            .type(ConstraintType.CAPACITY)
            .priority(ConstraintPriority.MEDIUM)
            .enabled(False)
            .build()
        )

        assert constraint.name == "Chained"
        assert constraint.enabled is False

    def test_builder_with_parameters(self):
        """Test builder with parameters."""
        constraint = (
            ConstraintBuilder()
            .hard()
            .name("WithParams")
            .type(ConstraintType.CAPACITY)
            .with_parameter("max_capacity", 4)
            .with_parameter("min_utilization", 1)
            .build()
        )

        assert constraint.max_capacity == 4
        assert constraint.min_utilization == 1

    def test_builder_with_multiple_parameters(self):
        """Test builder with multiple parameters at once."""
        params = {"max_capacity": 5, "min_utilization": 2}
        constraint = (
            ConstraintBuilder()
            .hard()
            .name("MultiParams")
            .type(ConstraintType.CAPACITY)
            .with_parameters(params)
            .build()
        )

        assert constraint.max_capacity == 5
        assert constraint.min_utilization == 2

    def test_builder_reset(self):
        """Test builder reset."""
        builder = (
            ConstraintBuilder().hard().name("Test").type(ConstraintType.AVAILABILITY)
        )
        builder.reset()

        assert builder._name is None
        assert builder._constraint_type is None
        assert builder._is_hard is True

    def test_builder_clone(self):
        """Test builder cloning."""
        builder1 = (
            ConstraintBuilder()
            .hard()
            .name("Original")
            .type(ConstraintType.AVAILABILITY)
        )
        builder2 = builder1.clone()

        # Modify cloned builder
        builder2.name("Cloned")

        # Original should be unchanged
        assert builder1._name == "Original"
        assert builder2._name == "Cloned"

    def test_builder_missing_name_error(self):
        """Test builder raises error if name not set."""
        with pytest.raises(ValueError):
            ConstraintBuilder().hard().type(ConstraintType.AVAILABILITY).build()

    def test_builder_missing_type_error(self):
        """Test builder raises error if type not set."""
        with pytest.raises(ValueError):
            ConstraintBuilder().hard().name("Test").build()


class TestCompositeConstraintBuilder:
    """Tests for composite constraint builder."""

    def test_composite_initialization(self):
        """Test composite builder initializes."""
        builder = CompositeConstraintBuilder("TestComposite")
        assert builder.name == "TestComposite"
        assert len(builder.constraints) == 0

    def test_composite_add_constraint(self):
        """Test adding constraint to composite."""
        builder = CompositeConstraintBuilder("TestComposite")
        builder.add_constraint(AvailabilityConstraint())

        assert len(builder.constraints) == 1

    def test_composite_add_multiple_constraints(self):
        """Test adding multiple constraints."""
        builder = CompositeConstraintBuilder("TestComposite")
        constraints = [
            AvailabilityConstraint(),
            EightyHourRuleConstraint(),
        ]
        builder.add_constraints(constraints)

        assert len(builder.constraints) == 2

    def test_composite_build(self):
        """Test building composite."""
        builder = CompositeConstraintBuilder("TestComposite")
        builder.add_constraint(AvailabilityConstraint())
        config = builder.build()

        assert config["name"] == "TestComposite"
        assert config["type"] == "composite"
        assert config["count"] == 1

    def test_composite_chaining(self):
        """Test composite builder chaining."""
        builder = (
            CompositeConstraintBuilder("Chained")
            .add_constraint(AvailabilityConstraint())
            .add_constraint(EightyHourRuleConstraint())
            .enabled(False)
        )

        assert builder.enabled is False
        assert len(builder.constraints) == 2


class TestConstraintCloner:
    """Tests for constraint cloning."""

    def test_clone_hard_constraint(self):
        """Test cloning hard constraint."""
        original = AvailabilityConstraint()
        cloned = ConstraintCloner.clone(original)

        assert cloned.name == original.name
        assert cloned.constraint_type == original.constraint_type
        assert cloned is not original  # Different instances

    def test_clone_to_builder(self):
        """Test converting constraint to builder."""
        original = AvailabilityConstraint()
        builder = ConstraintCloner.clone_to_builder(original)

        assert builder._name == original.name
        assert builder._constraint_type == original.constraint_type

    def test_clone_to_builder_modify(self):
        """Test modifying cloned constraint through builder."""
        original = AvailabilityConstraint()
        modified = (
            ConstraintCloner.clone_to_builder(original)
            .name("ModifiedAvailability")
            .with_parameter("custom", True)
            .build()
        )

        assert modified.name == "ModifiedAvailability"
        assert modified.custom is True


class TestConstraintSerializer:
    """Tests for constraint serialization."""

    def test_serialize_to_dict(self):
        """Test serializing constraint to dict."""
        constraint = AvailabilityConstraint()
        data = ConstraintSerializer.to_dict(constraint)

        assert data["name"] == "Availability"
        assert data["type"] == "hard"
        assert data["constraint_type"] == "availability"
        assert data["priority"] == "CRITICAL"

    def test_serialize_soft_constraint(self):
        """Test serializing soft constraint."""
        from app.scheduling.constraints.equity import EquityConstraint

        constraint = EquityConstraint()
        data = ConstraintSerializer.to_dict(constraint)

        assert data["type"] == "soft"
        assert "weight" in data

    def test_serialize_with_parameters(self):
        """Test serializing constraint with parameters."""
        builder = (
            ConstraintBuilder()
            .hard()
            .name("WithParams")
            .type(ConstraintType.CAPACITY)
            .with_parameter("max_capacity", 4)
        )
        constraint = builder.build()
        data = ConstraintSerializer.to_dict(constraint)

        assert "parameters" in data
        assert data["parameters"]["max_capacity"] == 4

    def test_serialize_to_json(self):
        """Test serializing constraint to JSON."""
        constraint = AvailabilityConstraint()
        json_str = ConstraintSerializer.to_json(constraint)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "Availability"

    def test_deserialize_from_dict(self):
        """Test deserializing constraint from dict."""
        data = {
            "type": "hard",
            "name": "TestConstraint",
            "constraint_type": "availability",
            "priority": "HIGH",
        }
        constraint = ConstraintSerializer.from_dict(data)

        assert constraint is not None
        assert constraint.name == "TestConstraint"
        assert isinstance(constraint, HardConstraint)

    def test_deserialize_from_json(self):
        """Test deserializing constraint from JSON."""
        original = AvailabilityConstraint()
        json_str = ConstraintSerializer.to_json(original)
        constraint = ConstraintSerializer.from_json(json_str)

        assert constraint is not None
        assert constraint.name == original.name

    def test_round_trip_serialization(self):
        """Test serializing and deserializing."""
        original = (
            ConstraintBuilder()
            .hard()
            .name("RoundTrip")
            .type(ConstraintType.CAPACITY)
            .priority(ConstraintPriority.HIGH)
            .with_parameter("test_param", 42)
            .build()
        )

        # Serialize
        data = ConstraintSerializer.to_dict(original)

        # Deserialize
        restored = ConstraintSerializer.from_dict(data)

        assert restored.name == original.name
        assert restored.constraint_type == original.constraint_type
        assert restored.priority == original.priority


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_build_hard_constraint_function(self):
        """Test build_hard_constraint convenience function."""
        constraint = build_hard_constraint(
            "Test",
            ConstraintType.AVAILABILITY,
            ConstraintPriority.HIGH,
        )

        assert isinstance(constraint, HardConstraint)
        assert constraint.name == "Test"

    def test_build_soft_constraint_function(self):
        """Test build_soft_constraint convenience function."""
        constraint = build_soft_constraint(
            "Test",
            ConstraintType.PREFERENCE,
            weight=1.5,
            priority=ConstraintPriority.MEDIUM,
        )

        assert isinstance(constraint, SoftConstraint)
        assert constraint.weight == 1.5
