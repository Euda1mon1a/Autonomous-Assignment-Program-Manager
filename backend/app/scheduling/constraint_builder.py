"""
Constraint Builder - Fluent API for constraint creation and composition.

This module provides a fluent builder interface for creating and composing
constraints, with support for parameterization, cloning, and serialization.

Features:
    - Fluent constraint builder API for easy creation
    - Constraint composition helpers for combining constraints
    - Parameterization support for configurable constraints
    - Constraint cloning for copying constraint configurations
    - Constraint serialization/deserialization for persistence
    - Builder chaining for readable constraint construction

Classes:
    - ConstraintBuilder: Fluent API for single constraints
    - CompositeConstraintBuilder: Builder for constraint groups
    - ConstraintSerializer: Serialize/deserialize constraints
    - ConstraintCloner: Clone constraint configurations

Example:
    >>> builder = ConstraintBuilder()
    >>> constraint = builder.hard() \\
    ...     .name("CustomRotation") \\
    ...     .type(ConstraintType.ROTATION) \\
    ...     .priority(ConstraintPriority.HIGH) \\
    ...     .with_parameter("max_rotations", 2) \\
    ...     .build()
"""

import copy
import json
import logging
from typing import Any, Optional

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintType,
    HardConstraint,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class ConstraintBuilder:
    """
    Fluent builder for creating constraints.

    Provides a readable, chainable interface for constraint construction.

    Usage:
        >>> constraint = (ConstraintBuilder()
        ...     .hard()
        ...     .name("MyConstraint")
        ...     .type(ConstraintType.CAPACITY)
        ...     .priority(ConstraintPriority.HIGH)
        ...     .build())

        >>> soft_constraint = (ConstraintBuilder()
        ...     .soft(weight=1.5)
        ...     .name("MyPreference")
        ...     .type(ConstraintType.PREFERENCE)
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize builder."""
        self._is_hard = True
        self._name = None
        self._constraint_type = None
        self._priority = ConstraintPriority.MEDIUM
        self._weight = 1.0
        self._enabled = True
        self._parameters = {}
        self._parent_class = None

    def hard(self) -> "ConstraintBuilder":
        """Set as hard constraint."""
        self._is_hard = True
        return self

    def soft(self, weight: float = 1.0) -> "ConstraintBuilder":
        """
        Set as soft constraint with weight.

        Args:
            weight: Constraint weight (default 1.0)

        Returns:
            Self for chaining
        """
        self._is_hard = False
        self._weight = weight
        return self

    def name(self, name: str) -> "ConstraintBuilder":
        """
        Set constraint name.

        Args:
            name: Constraint name (e.g., "CustomRotation")

        Returns:
            Self for chaining
        """
        self._name = name
        return self

    def type(self, constraint_type: ConstraintType) -> "ConstraintBuilder":
        """
        Set constraint type.

        Args:
            constraint_type: Type from ConstraintType enum

        Returns:
            Self for chaining
        """
        self._constraint_type = constraint_type
        return self

    def priority(self, priority: ConstraintPriority) -> "ConstraintBuilder":
        """
        Set constraint priority.

        Args:
            priority: Priority from ConstraintPriority enum

        Returns:
            Self for chaining
        """
        self._priority = priority
        return self

    def weight(self, weight: float) -> "ConstraintBuilder":
        """
        Set soft constraint weight.

        Args:
            weight: Constraint weight (default 1.0)

        Returns:
            Self for chaining
        """
        self._weight = weight
        return self

    def enabled(self, enabled: bool = True) -> "ConstraintBuilder":
        """
        Set constraint enabled state.

        Args:
            enabled: True to enable (default), False to disable

        Returns:
            Self for chaining
        """
        self._enabled = enabled
        return self

    def with_parameter(self, name: str, value: Any) -> "ConstraintBuilder":
        """
        Add parameter to constraint.

        Parameters allow customization of constraint behavior.

        Args:
            name: Parameter name (e.g., "max_capacity")
            value: Parameter value

        Returns:
            Self for chaining

        Example:
            >>> builder.with_parameter("max_capacity", 4) \\
            ...     .with_parameter("min_utilization", 1)
        """
        self._parameters[name] = value
        return self

    def with_parameters(self, params: dict) -> "ConstraintBuilder":
        """
        Add multiple parameters to constraint.

        Args:
            params: Dict of parameter name -> value

        Returns:
            Self for chaining
        """
        self._parameters.update(params)
        return self

    def parent_class(self, parent_class: type) -> "ConstraintBuilder":
        """
        Set parent constraint class.

        Used when building custom constraints that inherit from
        a base class other than HardConstraint or SoftConstraint.

        Args:
            parent_class: Parent class to inherit from

        Returns:
            Self for chaining
        """
        self._parent_class = parent_class
        return self

    def build(self) -> Constraint:
        """
        Build constraint from builder configuration.

        Creates a constraint instance with the specified properties.
        Note: This creates a generic constraint; for custom logic,
        create a proper constraint class.

        Returns:
            Constraint instance (HardConstraint or SoftConstraint)

        Raises:
            ValueError: If required fields are not set
        """
        if not self._name:
            raise ValueError("Constraint name is required")
        if not self._constraint_type:
            raise ValueError("Constraint type is required")

        # Create constraint instance
        if self._is_hard:
            constraint = HardConstraint(
                name=self._name,
                constraint_type=self._constraint_type,
                priority=self._priority,
                enabled=self._enabled,
            )
        else:
            constraint = SoftConstraint(
                name=self._name,
                constraint_type=self._constraint_type,
                weight=self._weight,
                priority=self._priority,
                enabled=self._enabled,
            )

        # Add parameters as attributes
        for param_name, param_value in self._parameters.items():
            setattr(constraint, param_name, param_value)

        logger.debug(f"Built constraint: {self._name}")
        return constraint

    def reset(self) -> "ConstraintBuilder":
        """Reset builder to initial state."""
        self._is_hard = True
        self._name = None
        self._constraint_type = None
        self._priority = ConstraintPriority.MEDIUM
        self._weight = 1.0
        self._enabled = True
        self._parameters = {}
        self._parent_class = None
        return self

    def clone(self) -> "ConstraintBuilder":
        """Create a deep copy of builder configuration."""
        new_builder = ConstraintBuilder()
        new_builder._is_hard = self._is_hard
        new_builder._name = self._name
        new_builder._constraint_type = self._constraint_type
        new_builder._priority = self._priority
        new_builder._weight = self._weight
        new_builder._enabled = self._enabled
        new_builder._parameters = copy.deepcopy(self._parameters)
        new_builder._parent_class = self._parent_class
        return new_builder


class CompositeConstraintBuilder:
    """
    Builder for constraint groups/composites.

    Combines multiple constraints into a single managed unit.

    Usage:
        >>> composite = (CompositeConstraintBuilder("CallManagement")
        ...     .add_constraint(OvernightCallCoverageConstraint())
        ...     .add_constraint(CallSpacingConstraint())
        ...     .build())
    """

    def __init__(self, name: str) -> None:
        """
        Initialize composite builder.

        Args:
            name: Name of composite constraint group
        """
        self.name = name
        self.constraints = []
        self.enabled = True

    def add_constraint(self, constraint: Constraint) -> "CompositeConstraintBuilder":
        """
        Add constraint to composite.

        Args:
            constraint: Constraint to add

        Returns:
            Self for chaining
        """
        self.constraints.append(constraint)
        return self

    def add_constraints(
        self,
        constraints: list[Constraint],
    ) -> "CompositeConstraintBuilder":
        """
        Add multiple constraints to composite.

        Args:
            constraints: List of constraints to add

        Returns:
            Self for chaining
        """
        self.constraints.extend(constraints)
        return self

    def enabled(self, enabled: bool = True) -> "CompositeConstraintBuilder":
        """
        Set composite enabled state.

        Args:
            enabled: True to enable, False to disable

        Returns:
            Self for chaining
        """
        self.enabled = enabled
        return self

    def build(self) -> dict:
        """
        Build composite constraint configuration.

        Returns:
            Dict with composite configuration
        """
        return {
            "name": self.name,
            "type": "composite",
            "enabled": self.enabled,
            "constraints": self.constraints,
            "count": len(self.constraints),
        }


class ConstraintCloner:
    """Clone constraint configurations."""

    @staticmethod
    def clone(constraint: Constraint) -> Constraint:
        """
        Deep clone a constraint.

        Args:
            constraint: Constraint to clone

        Returns:
            New constraint instance with same configuration
        """
        # Create new instance of same class
        constraint_class = type(constraint)
        cloned = copy.deepcopy(constraint)
        logger.debug(f"Cloned constraint: {constraint.name}")
        return cloned

    @staticmethod
    def clone_to_builder(constraint: Constraint) -> ConstraintBuilder:
        """
        Convert constraint to builder for modification.

        Allows cloning a constraint and then modifying it.

        Args:
            constraint: Constraint to convert

        Returns:
            ConstraintBuilder with constraint's configuration

        Example:
            >>> original = EightyHourRuleConstraint()
            >>> builder = ConstraintCloner.clone_to_builder(original)
            >>> modified = builder.with_parameter("threshold", 85).build()
        """
        builder = ConstraintBuilder()
        builder._name = constraint.name
        builder._constraint_type = constraint.constraint_type
        builder._priority = constraint.priority
        builder._enabled = constraint.enabled

        if isinstance(constraint, SoftConstraint):
            builder._is_hard = False
            builder._weight = constraint.weight
        else:
            builder._is_hard = True

        # Copy parameters
        for attr_name in dir(constraint):
            if not attr_name.startswith("_"):
                attr_value = getattr(constraint, attr_name)
                if not callable(attr_value) and attr_name not in [
                    "name",
                    "constraint_type",
                    "priority",
                    "enabled",
                    "weight",
                ]:
                    builder._parameters[attr_name] = attr_value

        return builder


class ConstraintSerializer:
    """Serialize and deserialize constraints."""

    @staticmethod
    def to_dict(constraint: Constraint) -> dict:
        """
        Serialize constraint to dictionary.

        Args:
            constraint: Constraint to serialize

        Returns:
            Dict representation of constraint

        Example:
            >>> constraint = EightyHourRuleConstraint()
            >>> data = ConstraintSerializer.to_dict(constraint)
            >>> json.dumps(data)
        """
        constraint_type = "hard" if isinstance(constraint, HardConstraint) else "soft"

        data = {
            "type": constraint_type,
            "class": type(constraint).__name__,
            "module": type(constraint).__module__,
            "name": constraint.name,
            "constraint_type": constraint.constraint_type.value,
            "priority": constraint.priority.name,
            "enabled": constraint.enabled,
        }

        if isinstance(constraint, SoftConstraint):
            data["weight"] = constraint.weight

        # Serialize parameters
        parameters = {}
        for attr_name in dir(constraint):
            if not attr_name.startswith("_"):
                attr_value = getattr(constraint, attr_name)
                if not callable(attr_value) and attr_name not in [
                    "name",
                    "constraint_type",
                    "priority",
                    "enabled",
                    "weight",
                ]:
                    try:
                        # Try to serialize (skip non-serializable)
                        json.dumps(attr_value)
                        parameters[attr_name] = attr_value
                    except TypeError:
                        pass

        if parameters:
            data["parameters"] = parameters

        return data

    @staticmethod
    def to_json(constraint: Constraint) -> str:
        """
        Serialize constraint to JSON string.

        Args:
            constraint: Constraint to serialize

        Returns:
            JSON string representation
        """
        return json.dumps(ConstraintSerializer.to_dict(constraint), indent=2)

    @staticmethod
    def from_dict(data: dict) -> Constraint | None:
        """
        Deserialize constraint from dictionary.

        Note: This creates a generic HardConstraint or SoftConstraint.
        For custom constraint classes, import the actual class and
        instantiate directly.

        Args:
            data: Dict representation of constraint

        Returns:
            Constraint instance or None if deserialization fails

        Example:
            >>> data = {
            ...     "type": "hard",
            ...     "name": "Availability",
            ...     "constraint_type": "availability",
            ...     "priority": "CRITICAL",
            ... }
            >>> constraint = ConstraintSerializer.from_dict(data)
        """
        try:
            # Reconstruct constraint using builder
            builder = ConstraintBuilder()

            if data.get("type") == "soft":
                builder.soft(weight=data.get("weight", 1.0))
            else:
                builder.hard()

            builder.name(data.get("name"))

            # Reconstruct constraint type
            constraint_type_str = data.get("constraint_type")
            constraint_type = ConstraintType(constraint_type_str)
            builder.type(constraint_type)

            # Reconstruct priority
            priority_str = data.get("priority", "MEDIUM")
            priority = ConstraintPriority[priority_str]
            builder.priority(priority)

            builder.enabled(data.get("enabled", True))

            # Add parameters
            if "parameters" in data:
                builder.with_parameters(data["parameters"])

            return builder.build()
        except Exception as e:
            logger.error(f"Error deserializing constraint: {e}")
            return None

    @staticmethod
    def from_json(json_str: str) -> Constraint | None:
        """
        Deserialize constraint from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            Constraint instance or None if deserialization fails
        """
        try:
            data = json.loads(json_str)
            return ConstraintSerializer.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            return None


# Convenience functions


def build_hard_constraint(
    name: str,
    constraint_type: ConstraintType,
    priority: ConstraintPriority = ConstraintPriority.HIGH,
) -> HardConstraint:
    """
    Convenience function to build hard constraint.

    Args:
        name: Constraint name
        constraint_type: ConstraintType
        priority: Priority level

    Returns:
        HardConstraint instance
    """
    return (
        ConstraintBuilder()
        .hard()
        .name(name)
        .type(constraint_type)
        .priority(priority)
        .build()
    )


def build_soft_constraint(
    name: str,
    constraint_type: ConstraintType,
    weight: float = 1.0,
    priority: ConstraintPriority = ConstraintPriority.MEDIUM,
) -> SoftConstraint:
    """
    Convenience function to build soft constraint.

    Args:
        name: Constraint name
        constraint_type: ConstraintType
        weight: Constraint weight
        priority: Priority level

    Returns:
        SoftConstraint instance
    """
    return (
        ConstraintBuilder()
        .soft(weight=weight)
        .name(name)
        .type(constraint_type)
        .priority(priority)
        .build()
    )
