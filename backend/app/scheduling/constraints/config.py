"""
Constraint Configuration System

Centralized configuration for constraint enablement, priorities, and weights.
This module provides a declarative way to configure which constraints are
enabled and how they should be weighted in the optimization.

Features:
    - Constraint enable/disable toggles
    - Priority configuration
    - Weight configuration for soft constraints
    - Dependency tracking
    - Environment-based configuration
    - Use case presets

Classes:
    - ConstraintConfig: Configuration for a single constraint
    - ConstraintConfigManager: Manages all constraint configurations
    - ConstraintPreset: Pre-configured constraint sets for common use cases

Example:
    >>> from app.scheduling.constraints.config import get_constraint_config
    >>> config = get_constraint_config()
    >>> if config.is_enabled("OvernightCallGeneration"):
    ...     # Enable overnight call scheduling
    ...     pass
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ConstraintCategory(str, Enum):
    """Constraint categories for organization."""

    ACGME = "ACGME"  # Regulatory compliance
    CAPACITY = "CAPACITY"  # Resource capacity limits
    COVERAGE = "COVERAGE"  # Coverage requirements
    EQUITY = "EQUITY"  # Fairness and workload distribution
    CALL = "CALL"  # Overnight call scheduling
    FMIT = "FMIT"  # FMIT (Friday inpatient) scheduling
    SPECIALTY = "SPECIALTY"  # Specialty-specific (SM, etc.)
    RESILIENCE = "RESILIENCE"  # Resilience framework
    TEMPORAL = "TEMPORAL"  # Time-based constraints
    FACULTY = "FACULTY"  # Faculty-specific constraints


class ConstraintPriorityLevel(int, Enum):
    """Priority levels for constraint application."""

    CRITICAL = 1  # Must be satisfied (ACGME, safety)
    HIGH = 2  # Important for quality
    MEDIUM = 3  # Optimization objectives
    LOW = 4  # Nice-to-have preferences


@dataclass
class ConstraintConfig:
    """Configuration for a single constraint."""

    name: str
    enabled: bool = True
    priority: ConstraintPriorityLevel = ConstraintPriorityLevel.MEDIUM
    weight: float = 1.0  # For soft constraints
    category: ConstraintCategory = ConstraintCategory.COVERAGE
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    enable_condition: str | None = None  # When to enable (documentation)
    disable_reason: str | None = None  # Why disabled by default

    def is_active(self) -> bool:
        """Check if constraint is active."""
        return self.enabled

    def should_enable(self, context: dict[str, any]) -> bool:
        """
        Check if constraint should be enabled based on context.

        Args:
            context: Dictionary of contextual information (e.g., has_sm_program)

        Returns:
            True if constraint should be enabled
        """
        if not self.enabled:
            return False

            # Check dependencies
        for dep in self.dependencies:
            if not context.get(f"{dep}_enabled", False):
                logger.debug(
                    f"Constraint {self.name} disabled: dependency {dep} not enabled"
                )
                return False

        return True


class ConstraintConfigManager:
    """
    Manages constraint configurations.

    Provides centralized configuration for all constraints in the system,
    including enable/disable state, priorities, and weights.
    """

    def __init__(self) -> None:
        """Initialize constraint configuration manager."""
        self._configs: dict[str, ConstraintConfig] = {}
        self._initialize_default_configs()

    def _initialize_default_configs(self) -> None:
        """Initialize default constraint configurations."""

        # ========================================
        # ACGME CONSTRAINTS (Always Enabled)
        # ========================================
        self._configs["Availability"] = ConstraintConfig(
            name="Availability",
            enabled=True,
            priority=ConstraintPriorityLevel.CRITICAL,
            category=ConstraintCategory.ACGME,
            description="Enforces resident/faculty availability",
        )

        self._configs["EightyHourRule"] = ConstraintConfig(
            name="EightyHourRule",
            enabled=True,
            priority=ConstraintPriorityLevel.CRITICAL,
            weight=1000.0,
            category=ConstraintCategory.ACGME,
            description="80-hour per week duty limit (rolling 4-week average)",
        )

        self._configs["OneInSevenRule"] = ConstraintConfig(
            name="OneInSevenRule",
            enabled=True,
            priority=ConstraintPriorityLevel.CRITICAL,
            weight=1000.0,
            category=ConstraintCategory.ACGME,
            description="1-in-7 day off requirement",
        )

        self._configs["SupervisionRatio"] = ConstraintConfig(
            name="SupervisionRatio",
            enabled=True,
            priority=ConstraintPriorityLevel.CRITICAL,
            weight=1000.0,
            category=ConstraintCategory.ACGME,
            description="Faculty supervision ratios by PGY level",
        )

        # ========================================
        # CAPACITY CONSTRAINTS (Always Enabled)
        # ========================================
        self._configs["OnePersonPerBlock"] = ConstraintConfig(
            name="OnePersonPerBlock",
            enabled=True,
            priority=ConstraintPriorityLevel.CRITICAL,
            category=ConstraintCategory.CAPACITY,
            description="Exactly one person per block-rotation assignment",
        )

        self._configs["ClinicCapacity"] = ConstraintConfig(
            name="ClinicCapacity",
            enabled=True,
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.CAPACITY,
            description="Clinic maximum occupancy limits",
        )

        self._configs["MaxPhysiciansInClinic"] = ConstraintConfig(
            name="MaxPhysiciansInClinic",
            enabled=True,
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.CAPACITY,
            description="Maximum faculty supervising same clinic",
        )

        self._configs["Coverage"] = ConstraintConfig(
            name="Coverage",
            enabled=True,
            priority=ConstraintPriorityLevel.HIGH,
            weight=1000.0,
            category=ConstraintCategory.COVERAGE,
            description="All required rotations must be covered",
        )

        # ========================================
        # EQUITY CONSTRAINTS (Always Enabled)
        # ========================================
        self._configs["Equity"] = ConstraintConfig(
            name="Equity",
            enabled=True,
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=10.0,
            category=ConstraintCategory.EQUITY,
            description="Balanced assignment distribution",
        )

        self._configs["Continuity"] = ConstraintConfig(
            name="Continuity",
            enabled=True,
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=5.0,
            category=ConstraintCategory.EQUITY,
            description="Continuity of care for repeated assignments",
        )

        # ========================================
        # CALL CONSTRAINTS (Opt-in)
        # ========================================
        self._configs["OvernightCallGeneration"] = ConstraintConfig(
            name="OvernightCallGeneration",
            enabled=False,  # Opt-in
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.CALL,
            description="Generates overnight call assignments (Sun-Thu)",
            enable_condition="Enable when automatic call scheduling is desired",
            disable_reason="Disabled by default - call may be manually scheduled",
        )

        self._configs["PostCallAutoAssignment"] = ConstraintConfig(
            name="PostCallAutoAssignment",
            enabled=True,  # ENABLED: auto-generate PCAT/DO after overnight call
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.CALL,
            description="Auto-assigns PCAT/DO after overnight call",
            dependencies=["OvernightCallGeneration"],
            enable_condition="Enable when post-call activities should be auto-assigned",
            disable_reason="Disabled by default - depends on OvernightCallGeneration",
        )

        # ========================================
        # FMIT CONSTRAINTS (Opt-in)
        # ========================================
        self._configs["FMITWeekBlocking"] = ConstraintConfig(
            name="FMITWeekBlocking",
            enabled=False,  # Opt-in
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.FMIT,
            description="Blocks other assignments during FMIT weeks",
            enable_condition="Enable for strict FMIT week blocking",
            disable_reason="Disabled by default - FMIT handled by other constraints",
        )

        self._configs["FMITMandatoryCall"] = ConstraintConfig(
            name="FMITMandatoryCall",
            enabled=False,  # Opt-in
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.FMIT,
            description="FMIT faculty takes Friday/Saturday call",
            enable_condition="Enable when FMIT includes mandatory weekend call",
            disable_reason="Disabled by default - may use separate call scheduling",
        )

        self._configs["FMITResidentClinicDay"] = ConstraintConfig(
            name="FMITResidentClinicDay",
            enabled=False,  # Opt-in
            priority=ConstraintPriorityLevel.MEDIUM,
            category=ConstraintCategory.FMIT,
            description="Resident clinic day constraints during FMIT",
            enable_condition="Enable when resident clinic must be scheduled during FMIT",
            disable_reason="Disabled by default - clinic scheduling may be flexible",
        )

        # ========================================
        # SPORTS MEDICINE CONSTRAINTS (Conditional)
        # ========================================
        self._configs["SMResidentFacultyAlignment"] = ConstraintConfig(
            name="SMResidentFacultyAlignment",
            enabled=False,  # Conditional
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.SPECIALTY,
            description="SM residents scheduled with SM faculty",
            enable_condition="Enable when Sports Medicine program exists",
            disable_reason="Disabled by default - only needed if SM program exists",
        )

        self._configs["SMFacultyNoRegularClinic"] = ConstraintConfig(
            name="SMFacultyNoRegularClinic",
            enabled=False,  # Conditional
            priority=ConstraintPriorityLevel.HIGH,
            category=ConstraintCategory.SPECIALTY,
            description="SM faculty excluded from regular clinic",
            dependencies=["SMResidentFacultyAlignment"],
            enable_condition="Enable when SM faculty only does SM clinic",
            disable_reason="Disabled by default - only needed if SM program exists",
        )

        # ========================================
        # RESILIENCE CONSTRAINTS (Tiered)
        # ========================================
        # Tier 1: Core resilience (Enabled in resilience-aware mode)
        self._configs["HubProtection"] = ConstraintConfig(
            name="HubProtection",
            enabled=True,  # Tier 1
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=15.0,
            category=ConstraintCategory.RESILIENCE,
            description="Protects hub resources from overload",
        )

        self._configs["UtilizationBuffer"] = ConstraintConfig(
            name="UtilizationBuffer",
            enabled=True,  # Tier 1
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=20.0,
            category=ConstraintCategory.RESILIENCE,
            description="Maintains utilization below 80% threshold",
        )

        # Tier 2: Strategic resilience (Opt-in for aggressive protection)
        self._configs["ZoneBoundary"] = ConstraintConfig(
            name="ZoneBoundary",
            enabled=False,  # Tier 2
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=12.0,
            category=ConstraintCategory.RESILIENCE,
            description="Isolates zones to prevent cascade failures",
            enable_condition="Enable for aggressive resilience (Tier 2)",
            disable_reason="Tier 2 resilience - may be too restrictive for some use cases",
        )

        self._configs["PreferenceTrail"] = ConstraintConfig(
            name="PreferenceTrail",
            enabled=False,  # Tier 2
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=8.0,
            category=ConstraintCategory.RESILIENCE,
            description="Tracks preference violations for resilience",
            enable_condition="Enable for aggressive resilience (Tier 2)",
            disable_reason="Tier 2 resilience - may be too restrictive for some use cases",
        )

        self._configs["N1Vulnerability"] = ConstraintConfig(
            name="N1Vulnerability",
            enabled=False,  # Tier 2
            priority=ConstraintPriorityLevel.MEDIUM,
            weight=25.0,
            category=ConstraintCategory.RESILIENCE,
            description="Prevents N-1 vulnerability (single point of failure)",
            enable_condition="Enable for aggressive resilience (Tier 2)",
            disable_reason="Tier 2 resilience - may be too restrictive for some use cases",
        )

    def get(self, name: str) -> ConstraintConfig | None:
        """
        Get configuration for a constraint.

        Args:
            name: Constraint name

        Returns:
            ConstraintConfig or None if not found
        """
        return self._configs.get(name)

    def is_enabled(self, name: str) -> bool:
        """
        Check if a constraint is enabled.

        Args:
            name: Constraint name

        Returns:
            True if enabled, False otherwise
        """
        config = self.get(name)
        return config.enabled if config else False

    def enable(self, name: str) -> bool:
        """
        Enable a constraint.

        Args:
            name: Constraint name

        Returns:
            True if successful
        """
        config = self.get(name)
        if config:
            config.enabled = True
            logger.info(f"Enabled constraint: {name}")
            return True
        logger.warning(f"Constraint not found: {name}")
        return False

    def disable(self, name: str) -> bool:
        """
        Disable a constraint.

        Args:
            name: Constraint name

        Returns:
            True if successful
        """
        config = self.get(name)
        if config:
            config.enabled = False
            logger.info(f"Disabled constraint: {name}")
            return True
        logger.warning(f"Constraint not found: {name}")
        return False

    def get_enabled_by_category(
        self, category: ConstraintCategory
    ) -> list[ConstraintConfig]:
        """
        Get all enabled constraints in a category.

        Args:
            category: Constraint category

        Returns:
            List of enabled constraint configs
        """
        return [
            config
            for config in self._configs.values()
            if config.category == category and config.enabled
        ]

    def get_all_enabled(self) -> list[ConstraintConfig]:
        """
        Get all enabled constraints.

        Returns:
            List of enabled constraint configs
        """
        return [config for config in self._configs.values() if config.enabled]

    def get_all_disabled(self) -> list[ConstraintConfig]:
        """
        Get all disabled constraints.

        Returns:
            List of disabled constraint configs
        """
        return [config for config in self._configs.values() if not config.enabled]

    def apply_preset(self, preset: str) -> None:
        """
        Apply a constraint preset.

        Args:
            preset: Preset name (default, minimal, strict, resilience_tier1, resilience_tier2)
        """
        if preset == "minimal":
            self._apply_minimal_preset()
        elif preset == "strict":
            self._apply_strict_preset()
        elif preset == "resilience_tier1":
            self._apply_resilience_tier1_preset()
        elif preset == "resilience_tier2":
            self._apply_resilience_tier2_preset()
        elif preset == "call_scheduling":
            self._apply_call_scheduling_preset()
        elif preset == "sports_medicine":
            self._apply_sports_medicine_preset()
        else:
            logger.warning(f"Unknown preset: {preset}")

    def _apply_minimal_preset(self) -> None:
        """Apply minimal constraint preset (fast solving)."""
        # Disable all optional constraints
        for name in [
            "Continuity",
            "OvernightCallGeneration",
            "PostCallAutoAssignment",
            "FMITWeekBlocking",
            "FMITMandatoryCall",
            "FMITResidentClinicDay",
            "SMResidentFacultyAlignment",
            "SMFacultyNoRegularClinic",
            "ZoneBoundary",
            "PreferenceTrail",
            "N1Vulnerability",
        ]:
            self.disable(name)

    def _apply_strict_preset(self) -> None:
        """Apply strict constraint preset (all constraints enabled)."""
        # Enable all constraints
        for config in self._configs.values():
            config.enabled = True
            if config.weight > 0:
                config.weight *= 2  # Double weights for strict mode

    def _apply_resilience_tier1_preset(self) -> None:
        """Apply resilience tier 1 preset (core resilience)."""
        self.enable("HubProtection")
        self.enable("UtilizationBuffer")
        # Tier 2 remains disabled
        self.disable("ZoneBoundary")
        self.disable("PreferenceTrail")
        self.disable("N1Vulnerability")

    def _apply_resilience_tier2_preset(self) -> None:
        """Apply resilience tier 2 preset (aggressive resilience)."""
        # Enable all resilience constraints
        self.enable("HubProtection")
        self.enable("UtilizationBuffer")
        self.enable("ZoneBoundary")
        self.enable("PreferenceTrail")
        self.enable("N1Vulnerability")

    def _apply_call_scheduling_preset(self) -> None:
        """Apply call scheduling preset (overnight call enabled)."""
        self.enable("OvernightCallGeneration")
        self.enable("PostCallAutoAssignment")

    def _apply_sports_medicine_preset(self) -> None:
        """Apply sports medicine preset (SM constraints enabled)."""
        self.enable("SMResidentFacultyAlignment")
        self.enable("SMFacultyNoRegularClinic")

    def get_status_report(self) -> str:
        """
        Generate a status report of all constraints.

        Returns:
            Formatted status report
        """
        lines = ["Constraint Configuration Status Report"]
        lines.append("=" * 70)

        # Summary
        enabled_count = len(self.get_all_enabled())
        disabled_count = len(self.get_all_disabled())
        lines.append(f"\nTotal Constraints: {len(self._configs)}")
        lines.append(f"  Enabled: {enabled_count}")
        lines.append(f"  Disabled: {disabled_count}")

        # By category
        lines.append("\nConstraints by Category:")
        for category in ConstraintCategory:
            constraints = [c for c in self._configs.values() if c.category == category]
            if constraints:
                enabled = len([c for c in constraints if c.enabled])
                total = len(constraints)
                lines.append(f"\n  {category.value}: {enabled}/{total} enabled")
                for config in sorted(constraints, key=lambda c: c.name):
                    status = "✓" if config.enabled else "✗"
                    lines.append(f"    [{status}] {config.name}")
                    if not config.enabled and config.disable_reason:
                        lines.append(f"        Reason: {config.disable_reason}")
                    if config.enable_condition:
                        lines.append(f"        Enable when: {config.enable_condition}")

        return "\n".join(lines)

        # Global singleton instance


_constraint_config_manager = None


def get_constraint_config() -> ConstraintConfigManager:
    """
    Get global constraint configuration manager.

    Returns:
        ConstraintConfigManager singleton instance
    """
    global _constraint_config_manager
    if _constraint_config_manager is None:
        _constraint_config_manager = ConstraintConfigManager()

        # Apply preset from environment if specified
        preset = os.getenv("CONSTRAINT_PRESET", None)
        if preset:
            logger.info(f"Applying constraint preset from environment: {preset}")
            _constraint_config_manager.apply_preset(preset)

    return _constraint_config_manager


def reset_constraint_config() -> None:
    """Reset global constraint configuration (for testing)."""
    global _constraint_config_manager
    _constraint_config_manager = None
