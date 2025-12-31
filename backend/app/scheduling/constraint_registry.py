"""
Constraint Registry - Central registration and discovery system for constraints.

This module provides a registry for managing constraint lifecycles including
registration, discovery, versioning, deprecation, and activation.

Features:
    - Constraint registration with metadata
    - Constraint discovery and lookup
    - Version management for constraints
    - Deprecation handling
    - Constraint activation/deactivation
    - Constraint categorization

Classes:
    - ConstraintMetadata: Metadata for registered constraints
    - ConstraintRegistry: Central registry singleton
    - ConstraintRegistration: Decorator for constraint registration

Example:
    >>> # Register a constraint
    >>> @ConstraintRegistry.register(
    ...     name="MyConstraint",
    ...     version="1.0",
    ...     category="CUSTOM",
    ... )
    ... class MyConstraint(HardConstraint):
    ...     ...

    >>> # Discover constraints
    >>> all_constraints = ConstraintRegistry.get_all()
    >>> custom_constraints = ConstraintRegistry.find(category="CUSTOM")
    >>> constraint = ConstraintRegistry.get("MyConstraint", "1.0")
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.scheduling.constraints.base import Constraint, ConstraintType

logger = logging.getLogger(__name__)


@dataclass
class ConstraintMetadata:
    """Metadata for a registered constraint."""

    name: str
    version: str
    constraint_class: type
    category: str  # 'ACGME', 'CAPACITY', 'EQUITY', 'CUSTOM', etc.
    description: str = ""
    is_deprecated: bool = False
    deprecation_message: str = ""
    replacement_constraint: str | None = None  # Name of replacement if deprecated
    tags: list[str] = field(default_factory=list)
    constraints_types: list[ConstraintType] = field(default_factory=list)
    is_enabled: bool = True
    author: str = ""
    since_version: str = ""  # Scheduler version when constraint was added

    def __str__(self) -> str:
        """String representation."""
        status = "(DEPRECATED)" if self.is_deprecated else ""
        enabled = "[DISABLED]" if not self.is_enabled else ""
        return (
            f"{self.name} v{self.version} [{self.category}] {status} {enabled}".strip()
        )

    def is_active(self) -> bool:
        """Check if constraint is active (not deprecated and enabled)."""
        return not self.is_deprecated and self.is_enabled

    def get_deprecation_info(self) -> dict | None:
        """Get deprecation information if applicable."""
        if not self.is_deprecated:
            return None
        return {
            "message": self.deprecation_message,
            "replacement": self.replacement_constraint,
        }


class ConstraintRegistry:
    """
    Central registry for constraints.

    Manages constraint registration, discovery, versioning, and lifecycle.
    Implemented as a singleton for global access.

    Usage:
        >>> # Register constraint
        >>> ConstraintRegistry.register("MyConstraint", "1.0", "CUSTOM")(MyConstraintClass)

        >>> # Discover constraints
        >>> all_constraints = ConstraintRegistry.get_all()
        >>> custom = ConstraintRegistry.find(category="CUSTOM")
        >>> constraint = ConstraintRegistry.get("MyConstraint", "1.0")

        >>> # Deprecation
        >>> ConstraintRegistry.deprecate("OldConstraint", "Use NewConstraint instead",
        ...     replacement="NewConstraint")
    """

    _instance = None
    _constraints: dict[tuple[str, str], ConstraintMetadata] = {}
    _latest_versions: dict[str, str] = {}

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(
        cls,
        name: str,
        version: str,
        category: str,
        description: str = "",
        tags: list[str] | None = None,
        constraint_types: list[ConstraintType] | None = None,
        author: str = "",
        since_version: str = "",
    ) -> Callable:
        """
        Decorator for registering constraints.

        Args:
            name: Constraint name
            version: Semantic version (e.g., "1.0.0")
            category: Category (ACGME, CAPACITY, EQUITY, CUSTOM, etc.)
            description: Constraint description
            tags: Tags for organization
            constraint_types: List of ConstraintType values
            author: Author/team name
            since_version: Scheduler version when added

        Returns:
            Decorator function

        Example:
            >>> @ConstraintRegistry.register(
            ...     name="MyConstraint",
            ...     version="1.0.0",
            ...     category="CUSTOM",
            ...     description="My custom constraint",
            ...     tags=["optimization", "experimental"],
            ... )
            ... class MyConstraint(HardConstraint):
            ...     ...
        """

        def decorator(constraint_class: type) -> type:
            # Create metadata
            metadata = ConstraintMetadata(
                name=name,
                version=version,
                constraint_class=constraint_class,
                category=category,
                description=description,
                is_deprecated=False,
                tags=tags or [],
                constraints_types=constraint_types or [],
                author=author,
                since_version=since_version,
            )

            # Register
            key = (name, version)
            cls._constraints[key] = metadata
            cls._latest_versions[name] = version

            logger.info(f"Registered constraint: {metadata}")
            return constraint_class

        return decorator

    @classmethod
    def get(
        cls,
        name: str,
        version: str | None = None,
    ) -> type | None:
        """
        Get constraint class by name and optional version.

        Args:
            name: Constraint name
            version: Specific version (optional, defaults to latest)

        Returns:
            Constraint class or None if not found

        Example:
            >>> ConstraintClass = ConstraintRegistry.get("Availability")
            >>> constraint = ConstraintClass()
        """
        # Use latest version if not specified
        if version is None:
            version = cls._latest_versions.get(name)
            if version is None:
                logger.warning(f"Constraint '{name}' not found")
                return None

        key = (name, version)
        metadata = cls._constraints.get(key)

        if metadata is None:
            logger.warning(f"Constraint '{name}' version '{version}' not found")
            return None

        if not metadata.is_active():
            logger.warning(
                f"Constraint '{name}' is {
                    'deprecated' if metadata.is_deprecated else 'disabled'
                }"
            )

        return metadata.constraint_class

    @classmethod
    def get_metadata(
        cls,
        name: str,
        version: str | None = None,
    ) -> ConstraintMetadata | None:
        """
        Get constraint metadata.

        Args:
            name: Constraint name
            version: Specific version (optional, defaults to latest)

        Returns:
            ConstraintMetadata or None if not found
        """
        if version is None:
            version = cls._latest_versions.get(name)
            if version is None:
                return None

        key = (name, version)
        return cls._constraints.get(key)

    @classmethod
    def get_all(
        cls,
        active_only: bool = False,
    ) -> dict[tuple[str, str], ConstraintMetadata]:
        """
        Get all registered constraints.

        Args:
            active_only: Only return active (non-deprecated, enabled) constraints

        Returns:
            Dict of registered constraints
        """
        if active_only:
            return {
                key: metadata
                for key, metadata in cls._constraints.items()
                if metadata.is_active()
            }
        return cls._constraints

    @classmethod
    def find(
        cls,
        category: str | None = None,
        tag: str | None = None,
        constraint_type: ConstraintType | None = None,
        active_only: bool = False,
    ) -> list[ConstraintMetadata]:
        """
        Find constraints by criteria.

        Args:
            category: Filter by category
            tag: Filter by tag
            constraint_type: Filter by constraint type
            active_only: Only return active constraints

        Returns:
            List of matching constraints

        Example:
            >>> custom = ConstraintRegistry.find(category="CUSTOM")
            >>> tags_experimental = ConstraintRegistry.find(tag="experimental")
        """
        results = []

        for metadata in cls._constraints.values():
            if active_only and not metadata.is_active():
                continue

            if category and metadata.category != category:
                continue

            if tag and tag not in metadata.tags:
                continue

            if constraint_type and constraint_type not in metadata.constraints_types:
                continue

            results.append(metadata)

        return results

    @classmethod
    def deprecate(
        cls,
        name: str,
        message: str,
        replacement: str | None = None,
        version: str | None = None,
    ) -> bool:
        """
        Mark constraint as deprecated.

        Args:
            name: Constraint name
            message: Deprecation message
            replacement: Name of replacement constraint (if any)
            version: Specific version (optional, defaults to all versions)

        Returns:
            True if deprecation succeeded, False otherwise

        Example:
            >>> ConstraintRegistry.deprecate(
            ...     "OldConstraint",
            ...     "Use NewConstraint instead",
            ...     replacement="NewConstraint",
            ... )
        """
        if version is None:
            # Deprecate all versions
            for metadata in cls._constraints.values():
                if metadata.name == name:
                    metadata.is_deprecated = True
                    metadata.deprecation_message = message
                    metadata.replacement_constraint = replacement
                    logger.info(f"Deprecated constraint: {name}")
            return True
        else:
            # Deprecate specific version
            key = (name, version)
            if key not in cls._constraints:
                logger.warning(f"Constraint '{name}' version '{version}' not found")
                return False

            metadata = cls._constraints[key]
            metadata.is_deprecated = True
            metadata.deprecation_message = message
            metadata.replacement_constraint = replacement
            logger.info(f"Deprecated constraint: {name} v{version}")
            return True

    @classmethod
    def enable(
        cls,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Enable a constraint.

        Args:
            name: Constraint name
            version: Specific version (optional, defaults to latest)

        Returns:
            True if enable succeeded
        """
        if version is None:
            version = cls._latest_versions.get(name)
            if version is None:
                return False

        key = (name, version)
        if key not in cls._constraints:
            return False

        cls._constraints[key].is_enabled = True
        logger.info(f"Enabled constraint: {name} v{version}")
        return True

    @classmethod
    def disable(
        cls,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Disable a constraint.

        Args:
            name: Constraint name
            version: Specific version (optional, defaults to latest)

        Returns:
            True if disable succeeded
        """
        if version is None:
            version = cls._latest_versions.get(name)
            if version is None:
                return False

        key = (name, version)
        if key not in cls._constraints:
            return False

        cls._constraints[key].is_enabled = False
        logger.info(f"Disabled constraint: {name} v{version}")
        return True

    @classmethod
    def list_by_category(cls) -> dict[str, list[ConstraintMetadata]]:
        """
        Group constraints by category.

        Returns:
            Dict of category -> list of constraints
        """
        categories = {}

        for metadata in cls._constraints.values():
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(metadata)

        return categories

    @classmethod
    def get_category_stats(cls) -> dict[str, int]:
        """
        Get count of constraints per category.

        Returns:
            Dict of category -> count
        """
        stats = {}
        for metadata in cls._constraints.values():
            category = metadata.category
            stats[category] = stats.get(category, 0) + 1
        return stats

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._constraints.clear()
        cls._latest_versions.clear()
        logger.warning("Cleared constraint registry")

    @classmethod
    def get_status_report(cls) -> str:
        """
        Generate registry status report.

        Returns:
            Formatted status report
        """
        lines = ["Constraint Registry Status Report"]
        lines.append("=" * 50)

        # Statistics
        stats = cls.get_category_stats()
        lines.append(f"\nTotal Constraints: {len(cls._constraints)}")
        lines.append("\nBy Category:")
        for category in sorted(stats.keys()):
            lines.append(f"  {category}: {stats[category]}")

        # Active/Inactive
        active = sum(1 for m in cls._constraints.values() if m.is_active())
        deprecated = sum(1 for m in cls._constraints.values() if m.is_deprecated)
        disabled = sum(1 for m in cls._constraints.values() if not m.is_enabled)

        lines.append("\nStatus:")
        lines.append(f"  Active: {active}")
        lines.append(f"  Deprecated: {deprecated}")
        lines.append(f"  Disabled: {disabled}")

        # Recent constraints
        if cls._constraints:
            lines.append("\nRecent Constraints:")
            for key in list(cls._constraints.keys())[-5:]:
                metadata = cls._constraints[key]
                lines.append(f"  - {metadata}")

        return "\n".join(lines)


# Initialize with built-in constraints
def _register_builtin_constraints():
    """Register all built-in constraints."""
    from app.scheduling.constraints.acgme import (
        AvailabilityConstraint,
        EightyHourRuleConstraint,
        OneInSevenRuleConstraint,
        SupervisionRatioConstraint,
    )
    from app.scheduling.constraints.capacity import (
        ClinicCapacityConstraint,
        CoverageConstraint,
        MaxPhysiciansInClinicConstraint,
        OnePersonPerBlockConstraint,
    )
    from app.scheduling.constraints.equity import (
        ContinuityConstraint,
        EquityConstraint,
    )

    # Register ACGME constraints
    ConstraintRegistry.register(
        name="Availability",
        version="1.0",
        category="ACGME",
        description="Enforces resident/faculty availability",
    )(AvailabilityConstraint)

    ConstraintRegistry.register(
        name="EightyHourRule",
        version="1.0",
        category="ACGME",
        description="80-hour per week duty limit",
    )(EightyHourRuleConstraint)

    ConstraintRegistry.register(
        name="OneInSevenRule",
        version="1.0",
        category="ACGME",
        description="1-in-7 day off requirement",
    )(OneInSevenRuleConstraint)

    ConstraintRegistry.register(
        name="SupervisionRatio",
        version="1.0",
        category="ACGME",
        description="Faculty supervision ratios by PGY level",
    )(SupervisionRatioConstraint)

    # Register capacity constraints
    ConstraintRegistry.register(
        name="OnePersonPerBlock",
        version="1.0",
        category="CAPACITY",
        description="Exactly one person per block-rotation",
    )(OnePersonPerBlockConstraint)

    ConstraintRegistry.register(
        name="ClinicCapacity",
        version="1.0",
        category="CAPACITY",
        description="Clinic maximum occupancy limits",
    )(ClinicCapacityConstraint)

    ConstraintRegistry.register(
        name="MaxPhysiciansInClinic",
        version="1.0",
        category="CAPACITY",
        description="Maximum faculty supervising same clinic",
    )(MaxPhysiciansInClinicConstraint)

    ConstraintRegistry.register(
        name="Coverage",
        version="1.0",
        category="CAPACITY",
        description="All required rotations must be covered",
    )(CoverageConstraint)

    # Register equity constraints
    ConstraintRegistry.register(
        name="Equity",
        version="1.0",
        category="EQUITY",
        description="Balanced assignment distribution",
    )(EquityConstraint)

    ConstraintRegistry.register(
        name="Continuity",
        version="1.0",
        category="EQUITY",
        description="Continuity of care for repeated assignments",
    )(ContinuityConstraint)


# Register built-in constraints on import
try:
    _register_builtin_constraints()
except Exception as e:
    logger.warning(f"Failed to register built-in constraints: {e}")
