"""
Constraint Manager for Scheduling.

This module provides the ConstraintManager class which orchestrates
collections of constraints for scheduling optimization.

Features:
    - Composable constraint sets
    - Priority-based ordering
    - Easy enable/disable of constraints
    - Validation aggregation
    - Factory methods for common configurations

Classes:
    - ConstraintManager: Main manager class for organizing constraints
"""

import logging
from typing import Any

# Import all constraint classes
from .acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)
from .base import (
    Constraint,
    ConstraintResult,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)
from .capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)
from .equity import ContinuityConstraint, EquityConstraint
from .night_float_post_call import NightFloatPostCallConstraint
from .primary_duty import (
    FacultyClinicEquitySoftConstraint,
    FacultyDayAvailabilityConstraint,
    FacultyPrimaryDutyClinicConstraint,
)
from .resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)
from .temporal import (
    InvertedWednesdayConstraint,
    WednesdayAMInternOnlyConstraint,
    WednesdayPMSingleFacultyConstraint,
)

# Block 10 constraints - call equity and inpatient headcount
from .call_equity import (
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)
from .fmit import (
    FMITContinuityTurfConstraint,
    FMITMandatoryCallConstraint,
    FMITStaffingFloorConstraint,
    FMITWeekBlockingConstraint,
    PostFMITRecoveryConstraint,
    PostFMITSundayBlockingConstraint,
)
from .inpatient import (
    FMITResidentClinicDayConstraint,
    ResidentInpatientHeadcountConstraint,
)

# Overnight call constraints
from .call_coverage import (
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
)
from .overnight_call import OvernightCallGenerationConstraint

# Post-call and faculty constraints
from .post_call import PostCallAutoAssignmentConstraint
from .faculty import PreferenceConstraint
from .faculty_role import FacultyRoleClinicConstraint, SMFacultyClinicConstraint

# Sports Medicine constraints
from .sports_medicine import SMResidentFacultyAlignmentConstraint

logger = logging.getLogger(__name__)


class ConstraintManager:
    """
    Manages a collection of constraints for scheduling.

    Features:
    - Composable constraint sets
    - Priority-based ordering
    - Easy enable/disable
    - Validation aggregation
    """

    def __init__(self) -> None:
        self.constraints: list[Constraint] = []
        self._hard_constraints: list[HardConstraint] = []
        self._soft_constraints: list[SoftConstraint] = []

    def add(self, constraint: Constraint) -> "ConstraintManager":
        """
        Add a constraint to the manager.

        Constraints are automatically categorized as hard or soft based on
        their class type. Returns self to allow method chaining.

        Args:
            constraint: Constraint instance to add (HardConstraint or SoftConstraint)

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> manager = ConstraintManager()
            >>> manager.add(AvailabilityConstraint())\\
            ...        .add(EightyHourRuleConstraint())\\
            ...        .add(EquityConstraint(weight=10.0))
        """
        self.constraints.append(constraint)
        if isinstance(constraint, HardConstraint):
            self._hard_constraints.append(constraint)
        elif isinstance(constraint, SoftConstraint):
            self._soft_constraints.append(constraint)
        return self

    def remove(self, name: str) -> "ConstraintManager":
        """
        Remove a constraint by name.

        Returns self to allow method chaining. If constraint name is not found,
        no error is raised (idempotent operation).

        Args:
            name: Name of the constraint to remove (e.g., "80HourRule")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> manager.remove("Continuity").remove("Preferences")
        """
        self.constraints = [c for c in self.constraints if c.name != name]
        self._hard_constraints = [c for c in self._hard_constraints if c.name != name]
        self._soft_constraints = [c for c in self._soft_constraints if c.name != name]
        return self

    def enable(self, name: str) -> "ConstraintManager":
        """
        Enable a constraint by name.

        Enabled constraints are applied during solving and validation.
        Returns self to allow method chaining.

        Args:
            name: Name of the constraint to enable (e.g., "HubProtection")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> # Enable resilience constraints when data is available
            >>> if context.has_resilience_data():
            ...     manager.enable("HubProtection")\\
            ...            .enable("UtilizationBuffer")
        """
        for c in self.constraints:
            if c.name == name:
                c.enabled = True
        return self

    def disable(self, name: str) -> "ConstraintManager":
        """
        Disable a constraint by name.

        Disabled constraints are skipped during solving and validation.
        Returns self to allow method chaining.

        Args:
            name: Name of the constraint to disable (e.g., "Continuity")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> # Disable soft constraints for faster solving
            >>> manager.disable("Continuity")\\
            ...        .disable("Preferences")
        """
        for c in self.constraints:
            if c.name == name:
                c.enabled = False
        return self

    def get_enabled(self) -> list[Constraint]:
        """
        Get all enabled constraints.

        Returns:
            list[Constraint]: List of enabled constraints (both hard and soft)

        Example:
            >>> enabled = manager.get_enabled()
            >>> print(f"Active constraints: {[c.name for c in enabled]}")
        """
        return [c for c in self.constraints if c.enabled]

    def get_hard_constraints(self) -> list[HardConstraint]:
        """
        Get enabled hard constraints.

        Hard constraints must be satisfied for a valid schedule. These typically
        enforce ACGME requirements, availability, and capacity limits.

        Returns:
            list[HardConstraint]: List of enabled hard constraints

        Example:
            >>> hard = manager.get_hard_constraints()
            >>> print(f"Must satisfy: {[c.name for c in hard]}")
        """
        return [c for c in self._hard_constraints if c.enabled]

    def get_soft_constraints(self) -> list[SoftConstraint]:
        """
        Get enabled soft constraints.

        Soft constraints are optimization objectives (equity, coverage, continuity).
        They have weights and contribute to the objective function.

        Returns:
            list[SoftConstraint]: List of enabled soft constraints

        Example:
            >>> soft = manager.get_soft_constraints()
            >>> total_weight = sum(c.weight for c in soft)
            >>> print(f"Optimization weights: {total_weight}")
        """
        return [c for c in self._soft_constraints if c.enabled]

    def apply_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Apply all enabled constraints to CP-SAT model."""
        for constraint in sorted(self.get_enabled(), key=lambda c: -c.priority.value):
            try:
                constraint.add_to_cpsat(model, variables, context)
                logger.debug(f"Applied constraint to CP-SAT: {constraint.name}")
            except Exception as e:
                logger.error(f"Error applying {constraint.name} to CP-SAT: {e}")

    def apply_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Apply all enabled constraints to PuLP model."""
        for constraint in sorted(self.get_enabled(), key=lambda c: -c.priority.value):
            try:
                constraint.add_to_pulp(model, variables, context)
                logger.debug(f"Applied constraint to PuLP: {constraint.name}")
            except Exception as e:
                logger.error(f"Error applying {constraint.name} to PuLP: {e}")

    def validate_all(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate all constraints and aggregate results."""
        all_violations: list[Any] = []
        total_penalty = 0.0
        all_satisfied = True

        for constraint in self.get_enabled():
            try:
                result = constraint.validate(assignments, context)
                all_violations.extend(result.violations)
                total_penalty += result.penalty
                if not result.satisfied:
                    all_satisfied = False
            except Exception as e:
                logger.error(f"Error validating {constraint.name}: {e}")

        return ConstraintResult(
            satisfied=all_satisfied,
            violations=all_violations,
            penalty=total_penalty,
        )

    @classmethod
    def create_default(cls) -> "ConstraintManager":
        """Create manager with default ACGME constraints."""
        manager = cls()

        # Hard constraints (ACGME compliance)
        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(EightyHourRuleConstraint())
        manager.add(OneInSevenRuleConstraint())
        manager.add(SupervisionRatioConstraint())
        manager.add(ClinicCapacityConstraint())
        manager.add(MaxPhysiciansInClinicConstraint())
        manager.add(WednesdayAMInternOnlyConstraint())
        manager.add(WednesdayPMSingleFacultyConstraint())
        manager.add(InvertedWednesdayConstraint())
        manager.add(NightFloatPostCallConstraint())

        # Block 10 hard constraints - inpatient headcount and post-FMIT blocking
        manager.add(ResidentInpatientHeadcountConstraint())
        manager.add(PostFMITRecoveryConstraint())  # Faculty Friday PC after FMIT
        manager.add(PostFMITSundayBlockingConstraint())

        # Faculty primary duty constraints (Airtable-driven)
        # Uses primary_duties.json for per-faculty clinic min/max and availability
        manager.add(FacultyPrimaryDutyClinicConstraint())
        manager.add(FacultyDayAvailabilityConstraint())

        # Faculty role-based constraints
        manager.add(FacultyRoleClinicConstraint())

        # Overnight call generation (disabled by default - opt-in via factory method)
        manager.add(OvernightCallGenerationConstraint())
        manager.disable("OvernightCallGeneration")

        # Post-call auto-assignment (disabled by default - opt-in via factory method)
        manager.add(PostCallAutoAssignmentConstraint())
        manager.disable("PostCallAutoAssignment")

        # Sports Medicine coordination (disabled by default - enable if SM program exists)
        manager.add(SMResidentFacultyAlignmentConstraint())
        manager.add(SMFacultyClinicConstraint())
        manager.disable("SMResidentFacultyAlignment")
        manager.disable("SMFacultyNoRegularClinic")

        # Additional FMIT constraints (disabled by default - opt-in via factory method)
        manager.add(FMITWeekBlockingConstraint())
        manager.add(FMITMandatoryCallConstraint())
        manager.add(FMITResidentClinicDayConstraint())
        manager.disable("FMITWeekBlocking")
        manager.disable("FMITMandatoryCall")
        manager.disable("FMITResidentClinicDay")

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))
        manager.add(FacultyClinicEquitySoftConstraint(weight=15.0))

        # Block 10 soft constraints - call equity (weight hierarchy documented)
        # Weight order: Sunday (10) > CallSpacing (8) > Weekday (5) > Tuesday (2)
        manager.add(SundayCallEquityConstraint(weight=10.0))
        manager.add(CallSpacingConstraint(weight=8.0))
        manager.add(WeekdayCallEquityConstraint(weight=5.0))
        manager.add(TuesdayCallPreferenceConstraint(weight=2.0))

        # Tier 1: Resilience-aware soft constraints (ENABLED by default)
        # These provide critical protection against cascade failures
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(UtilizationBufferConstraint(weight=20.0))
        # Tier 2: Strategic resilience constraints (disabled by default - more aggressive)
        manager.add(ZoneBoundaryConstraint(weight=12.0))
        manager.add(PreferenceTrailConstraint(weight=8.0))
        manager.add(N1VulnerabilityConstraint(weight=25.0))
        # Tier 2 disabled by default - enable with create_resilience_aware(tier=2)
        manager.disable("ZoneBoundary")
        manager.disable("PreferenceTrail")
        manager.disable("N1Vulnerability")

        return manager

    @classmethod
    def create_resilience_aware(
        cls,
        target_utilization: float = 0.80,
        tier: int = 2,
    ) -> "ConstraintManager":
        """
        Create manager with resilience-aware constraints enabled.

        This configuration:
        - Includes all ACGME compliance constraints
        - Tier 1: Hub protection, utilization buffer
        - Tier 2: Zone boundaries, preference trails, N-1 vulnerability
        - Suitable for systems with ResilienceService integration

        Args:
            target_utilization: Maximum utilization before penalties (default 80%)
            tier: Maximum tier to enable (1 or 2, default 2)

        Returns:
            ConstraintManager with resilience constraints enabled
        """
        manager = cls()

        # Hard constraints (ACGME compliance)
        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(EightyHourRuleConstraint())
        manager.add(OneInSevenRuleConstraint())
        manager.add(SupervisionRatioConstraint())
        manager.add(ClinicCapacityConstraint())
        manager.add(MaxPhysiciansInClinicConstraint())
        manager.add(WednesdayAMInternOnlyConstraint())
        manager.add(WednesdayPMSingleFacultyConstraint())
        manager.add(InvertedWednesdayConstraint())
        manager.add(NightFloatPostCallConstraint())

        # Block 10 hard constraints - inpatient headcount and post-FMIT blocking
        manager.add(ResidentInpatientHeadcountConstraint())
        manager.add(PostFMITRecoveryConstraint())  # Faculty Friday PC after FMIT
        manager.add(PostFMITSundayBlockingConstraint())

        # Faculty primary duty constraints (Airtable-driven)
        manager.add(FacultyPrimaryDutyClinicConstraint())
        manager.add(FacultyDayAvailabilityConstraint())

        # Faculty role-based constraints
        manager.add(FacultyRoleClinicConstraint())

        # Overnight call generation (disabled by default)
        manager.add(OvernightCallGenerationConstraint())
        manager.disable("OvernightCallGeneration")

        # Post-call auto-assignment (disabled by default)
        manager.add(PostCallAutoAssignmentConstraint())
        manager.disable("PostCallAutoAssignment")

        # Sports Medicine coordination (disabled by default)
        manager.add(SMResidentFacultyAlignmentConstraint())
        manager.add(SMFacultyClinicConstraint())
        manager.disable("SMResidentFacultyAlignment")
        manager.disable("SMFacultyNoRegularClinic")

        # Additional FMIT constraints (disabled by default)
        manager.add(FMITWeekBlockingConstraint())
        manager.add(FMITMandatoryCallConstraint())
        manager.add(FMITResidentClinicDayConstraint())
        manager.disable("FMITWeekBlocking")
        manager.disable("FMITMandatoryCall")
        manager.disable("FMITResidentClinicDay")

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))
        manager.add(FacultyClinicEquitySoftConstraint(weight=15.0))

        # Block 10 soft constraints - call equity
        manager.add(SundayCallEquityConstraint(weight=10.0))
        manager.add(CallSpacingConstraint(weight=8.0))
        manager.add(WeekdayCallEquityConstraint(weight=5.0))
        manager.add(TuesdayCallPreferenceConstraint(weight=2.0))

        # Tier 1: Core resilience constraints (ENABLED)
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(
            UtilizationBufferConstraint(
                weight=20.0, target_utilization=target_utilization
            )
        )

        # Tier 2: Strategic resilience constraints
        manager.add(ZoneBoundaryConstraint(weight=12.0))
        manager.add(PreferenceTrailConstraint(weight=8.0))
        manager.add(N1VulnerabilityConstraint(weight=25.0))

        # Only enable Tier 2 if requested
        if tier < 2:
            manager.disable("ZoneBoundary")
            manager.disable("PreferenceTrail")
            manager.disable("N1Vulnerability")

        return manager

    @classmethod
    def create_minimal(cls) -> "ConstraintManager":
        """Create manager with minimal constraints (fast solving)."""
        manager = cls()

        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(CoverageConstraint(weight=1000.0))

        return manager

    @classmethod
    def create_strict(cls) -> "ConstraintManager":
        """Create manager with all constraints enabled at high weight."""
        manager = cls.create_default()

        # Increase soft constraint weights
        for c in manager._soft_constraints:
            c.weight *= 2

        return manager
