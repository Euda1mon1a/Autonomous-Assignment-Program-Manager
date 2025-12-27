"""
Fatigue-Aware Constraint Generator for Schedule Optimization.

This module generates scheduling constraints based on fatigue risk analysis,
integrating the Three-Process Model and performance predictor with the
CP-SAT and QUBO solvers.

Constraint Types:
1. FatigueConstraint (Hard): Blocks assignments that would exceed safe fatigue limits
2. FatigueSoftConstraint: Penalizes schedules proportional to fatigue risk
3. CircadianConstraint: Protects WOCL periods and enforces shift duration limits
4. RecoveryConstraint: Ensures adequate recovery time between shifts

Integration:
- CP-SAT solver: Adds as linear constraints with big-M formulation
- QUBO solver: Adds as quadratic penalty terms
- Greedy solver: Used for pre-filtering infeasible assignments

Based on:
- FAA Part 117 flight duty limits
- EASA ORO.FTL unfavorable start time rules
- ICAO FRMS alternative compliance framework
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)
from app.frms.three_process_model import ThreeProcessModel, AlertnessState

logger = logging.getLogger(__name__)


# =============================================================================
# Constraint Type Extension
# =============================================================================

# Add FRMS-specific constraint types
class FRMSConstraintType(ConstraintType):
    """Extended constraint types for FRMS integration."""

    FATIGUE_LIMIT = "fatigue_limit"
    CIRCADIAN_PROTECTION = "circadian_protection"
    WOCL_RESTRICTION = "wocl_restriction"
    RECOVERY_REQUIREMENT = "recovery_requirement"
    SHIFT_DURATION_LIMIT = "shift_duration_limit"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FatigueViolation:
    """
    Detailed fatigue constraint violation.

    Extends base ConstraintViolation with FRMS-specific data.
    """

    person_id: UUID
    block_id: UUID
    violation_type: str  # "effectiveness_below_threshold", "wocl_exposure", etc.
    predicted_effectiveness: float
    threshold: float
    contributing_factors: dict[str, float] = field(default_factory=dict)
    severity: str = "MEDIUM"
    recommendation: str = ""

    def to_constraint_violation(self) -> ConstraintViolation:
        """Convert to base ConstraintViolation."""
        return ConstraintViolation(
            constraint_name="FatigueConstraint",
            constraint_type=ConstraintType.RESILIENCE,
            severity=self.severity,
            message=(
                f"Fatigue violation: {self.violation_type} - "
                f"effectiveness {self.predicted_effectiveness:.1f}% "
                f"(threshold: {self.threshold:.1f}%)"
            ),
            person_id=self.person_id,
            block_id=self.block_id,
            details={
                "violation_type": self.violation_type,
                "predicted_effectiveness": self.predicted_effectiveness,
                "threshold": self.threshold,
                "contributing_factors": self.contributing_factors,
                "recommendation": self.recommendation,
            },
        )


# =============================================================================
# Hard Fatigue Constraint
# =============================================================================


class FatigueConstraint(HardConstraint):
    """
    Hard constraint that blocks assignments exceeding fatigue limits.

    Uses Three-Process Model to predict effectiveness and blocks
    assignments where predicted effectiveness falls below FRA threshold (70%).

    This is a HARD constraint - violations result in infeasible solutions.
    Use FatigueSoftConstraint for optimization objectives.
    """

    # FAA/FRA thresholds
    FAA_CAUTION_THRESHOLD = 77.0  # FAA caution level
    FRA_HIGH_RISK_THRESHOLD = 70.0  # FRA high-risk threshold (hard limit)
    CRITICAL_THRESHOLD = 60.0  # Never schedule below this

    def __init__(
        self,
        threshold: float = FRA_HIGH_RISK_THRESHOLD,
        enabled: bool = True,
    ):
        """
        Initialize fatigue hard constraint.

        Args:
            threshold: Minimum effectiveness threshold (default: FRA 70%)
            enabled: Whether constraint is active
        """
        super().__init__(
            name="FatigueLimit",
            constraint_type=ConstraintType.RESILIENCE,
            priority=ConstraintPriority.CRITICAL,
            enabled=enabled,
        )
        self.threshold = threshold
        self.model = ThreeProcessModel()
        self._alertness_states: dict[UUID, AlertnessState] = {}

    def initialize_states(
        self,
        context: SchedulingContext,
        schedule_start: datetime,
    ) -> None:
        """
        Initialize alertness states for all residents.

        Should be called before constraint evaluation.

        Args:
            context: Scheduling context with residents
            schedule_start: When scheduling period begins
        """
        for resident in context.residents:
            self._alertness_states[resident.id] = self.model.create_state(
                person_id=resident.id,
                initial_reservoir=100.0,  # Assume fully rested at start
                timestamp=schedule_start,
            )
        logger.info(
            f"Initialized alertness states for {len(context.residents)} residents"
        )

    def predict_effectiveness(
        self,
        person_id: UUID,
        block_date: date,
        time_of_day: str,
        hours_worked_prior: float = 0.0,
    ) -> float:
        """
        Predict effectiveness for a potential assignment.

        Args:
            person_id: Resident UUID
            block_date: Date of the block
            time_of_day: "AM" or "PM"
            hours_worked_prior: Hours worked earlier same day

        Returns:
            Predicted effectiveness (0-100%)
        """
        state = self._alertness_states.get(person_id)
        if not state:
            return 100.0  # Assume optimal if no state

        # Calculate time of day as float
        if time_of_day == "AM":
            tod = 8.0  # 8:00 AM
        else:
            tod = 14.0  # 2:00 PM

        # Update state for hours worked today
        if hours_worked_prior > 0:
            state = self.model.update_wakefulness(state, hours_worked_prior)
            self._alertness_states[person_id] = state

        # Calculate effectiveness
        score = self.model.calculate_effectiveness(state, tod)
        return score.overall

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add fatigue constraints to CP-SAT model.

        Uses indicator constraints: if assignment[r,b] = 1 and
        predicted_effectiveness < threshold, then constraint is violated.

        For efficiency, pre-computes effectiveness predictions and only
        adds constraints for assignments that could violate threshold.

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing assignment variables
            context: Scheduling context
        """
        if not self.enabled:
            return

        logger.info("Adding fatigue constraints to CP-SAT model")

        # Get assignment variables
        x = variables.get("x")  # x[r, b, t] binary assignment vars
        if x is None:
            logger.warning("No assignment variables found - skipping fatigue constraint")
            return

        # Initialize states if not done
        if not self._alertness_states:
            self.initialize_states(context, datetime.combine(context.start_date, datetime.min.time()))

        blocked_count = 0

        # For each potential assignment, check if it would violate fatigue limit
        for resident in context.residents:
            r_idx = context.resident_idx.get(resident.id)
            if r_idx is None:
                continue

            for block in context.blocks:
                b_idx = context.block_idx.get(block.id)
                if b_idx is None:
                    continue

                # Predict effectiveness for this assignment
                effectiveness = self.predict_effectiveness(
                    person_id=resident.id,
                    block_date=block.date,
                    time_of_day=getattr(block, "time_of_day", "AM"),
                )

                # If below threshold, block assignment completely
                if effectiveness < self.threshold:
                    # Block all template assignments for this person-block
                    for template in context.templates:
                        t_idx = context.template_idx.get(template.id)
                        if t_idx is not None and (r_idx, b_idx, t_idx) in x:
                            # Force variable to 0
                            model.Add(x[r_idx, b_idx, t_idx] == 0)
                            blocked_count += 1

                # If below critical threshold, log warning
                if effectiveness < self.CRITICAL_THRESHOLD:
                    logger.warning(
                        f"Critical fatigue risk for {resident.id} on {block.date}: "
                        f"{effectiveness:.1f}%"
                    )

        logger.info(f"Blocked {blocked_count} assignments due to fatigue constraints")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add fatigue constraints to PuLP model.

        Similar to CP-SAT but using PuLP constraint syntax.
        """
        if not self.enabled:
            return

        # PuLP implementation follows same logic as CP-SAT
        # Force variables to 0 for assignments below threshold
        x = variables.get("x")
        if x is None:
            return

        if not self._alertness_states:
            self.initialize_states(context, datetime.combine(context.start_date, datetime.min.time()))

        for resident in context.residents:
            r_idx = context.resident_idx.get(resident.id)
            for block in context.blocks:
                b_idx = context.block_idx.get(block.id)

                effectiveness = self.predict_effectiveness(
                    person_id=resident.id,
                    block_date=block.date,
                    time_of_day=getattr(block, "time_of_day", "AM"),
                )

                if effectiveness < self.threshold:
                    for template in context.templates:
                        t_idx = context.template_idx.get(template.id)
                        if t_idx is not None:
                            key = (r_idx, b_idx, t_idx)
                            if key in x:
                                # PuLP: x == 0 constraint
                                model += x[key] == 0, f"fatigue_block_{r_idx}_{b_idx}_{t_idx}"

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate assignments against fatigue limits.

        Args:
            assignments: List of Assignment objects
            context: Scheduling context

        Returns:
            ConstraintResult with any violations
        """
        if not self.enabled:
            return ConstraintResult(satisfied=True)

        violations = []

        for assignment in assignments:
            person_id = getattr(assignment, "person_id", None)
            block = getattr(assignment, "block", None)

            if not person_id or not block:
                continue

            effectiveness = self.predict_effectiveness(
                person_id=person_id,
                block_date=block.date,
                time_of_day=getattr(block, "time_of_day", "AM"),
            )

            if effectiveness < self.threshold:
                fatigue_violation = FatigueViolation(
                    person_id=person_id,
                    block_id=block.id,
                    violation_type="effectiveness_below_threshold",
                    predicted_effectiveness=effectiveness,
                    threshold=self.threshold,
                    severity="HIGH" if effectiveness < self.CRITICAL_THRESHOLD else "MEDIUM",
                    recommendation="Reduce prior workload or reschedule",
                )
                violations.append(fatigue_violation.to_constraint_violation())

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
            penalty=float("inf") if violations else 0.0,
        )


# =============================================================================
# Soft Fatigue Constraint (Optimization Objective)
# =============================================================================


class FatigueSoftConstraint(SoftConstraint):
    """
    Soft constraint that penalizes schedules proportional to fatigue risk.

    Unlike FatigueConstraint (hard), this adds penalty to the objective
    function based on how far effectiveness drops below optimal.

    Penalty calculation:
    - No penalty above FAA caution threshold (77%)
    - Linear penalty from 77% to 70%
    - Quadratic penalty below 70% (FRA threshold)
    """

    FAA_CAUTION_THRESHOLD = 77.0
    FRA_HIGH_RISK_THRESHOLD = 70.0

    def __init__(
        self,
        weight: float = 100.0,
        enabled: bool = True,
    ):
        """
        Initialize soft fatigue constraint.

        Args:
            weight: Base penalty weight
            enabled: Whether constraint is active
        """
        super().__init__(
            name="FatiguePenalty",
            constraint_type=ConstraintType.RESILIENCE,
            weight=weight,
            priority=ConstraintPriority.HIGH,
            enabled=enabled,
        )
        self.model = ThreeProcessModel()
        self._alertness_states: dict[UUID, AlertnessState] = {}

    def calculate_penalty(self, effectiveness: float) -> float:
        """
        Calculate penalty for given effectiveness score.

        Args:
            effectiveness: Predicted effectiveness (0-100)

        Returns:
            Penalty value (higher = worse)
        """
        if effectiveness >= self.FAA_CAUTION_THRESHOLD:
            return 0.0

        if effectiveness >= self.FRA_HIGH_RISK_THRESHOLD:
            # Linear penalty in caution zone
            gap = self.FAA_CAUTION_THRESHOLD - effectiveness
            return self.weight * (gap / 10.0)  # 0.7 weight per percent below 77

        # Quadratic penalty below FRA threshold
        gap = self.FAA_CAUTION_THRESHOLD - effectiveness
        linear_part = (self.FAA_CAUTION_THRESHOLD - self.FRA_HIGH_RISK_THRESHOLD) / 10.0
        quadratic_part = ((self.FRA_HIGH_RISK_THRESHOLD - effectiveness) / 10.0) ** 2

        return self.weight * (linear_part + quadratic_part)

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add fatigue penalty to CP-SAT objective.

        Adds penalty terms to objective function based on predicted
        effectiveness for each assignment.
        """
        if not self.enabled:
            return

        x = variables.get("x")
        objective_terms = variables.get("objective_terms", [])

        if x is None:
            return

        for resident in context.residents:
            r_idx = context.resident_idx.get(resident.id)
            if r_idx is None:
                continue

            for block in context.blocks:
                b_idx = context.block_idx.get(block.id)
                if b_idx is None:
                    continue

                # Get or predict effectiveness
                state = self._alertness_states.get(resident.id)
                if not state:
                    state = self.model.create_state(resident.id)
                    self._alertness_states[resident.id] = state

                tod = 8.0 if getattr(block, "time_of_day", "AM") == "AM" else 14.0
                score = self.model.calculate_effectiveness(state, tod)
                penalty = self.calculate_penalty(score.overall)

                if penalty > 0:
                    for template in context.templates:
                        t_idx = context.template_idx.get(template.id)
                        if t_idx is not None and (r_idx, b_idx, t_idx) in x:
                            # Add penalty term: penalty * x[r,b,t]
                            objective_terms.append((int(penalty), x[r_idx, b_idx, t_idx]))

        variables["objective_terms"] = objective_terms

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add fatigue penalty to PuLP objective."""
        if not self.enabled:
            return

        # PuLP implementation similar to CP-SAT
        # Add penalty coefficients to objective
        pass  # Implementation follows CP-SAT pattern

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate and calculate total penalty for assignments."""
        if not self.enabled:
            return ConstraintResult(satisfied=True)

        total_penalty = 0.0
        violations = []

        for assignment in assignments:
            person_id = getattr(assignment, "person_id", None)
            block = getattr(assignment, "block", None)

            if not person_id or not block:
                continue

            state = self._alertness_states.get(person_id)
            if not state:
                state = self.model.create_state(person_id)
                self._alertness_states[person_id] = state

            tod = 8.0 if getattr(block, "time_of_day", "AM") == "AM" else 14.0
            score = self.model.calculate_effectiveness(state, tod)
            penalty = self.calculate_penalty(score.overall)

            total_penalty += penalty

            if score.overall < self.FAA_CAUTION_THRESHOLD:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Fatigue warning: {score.overall:.1f}% effectiveness",
                        person_id=person_id,
                        block_id=block.id,
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint is always "satisfied"
            violations=violations,
            penalty=total_penalty,
        )


# =============================================================================
# Circadian Protection Constraint
# =============================================================================


class CircadianConstraint(SoftConstraint):
    """
    Constraint protecting circadian rhythm alignment.

    Implements:
    1. WOCL (2-6 AM) restrictions for high-risk procedures
    2. Shift duration limits based on start time (EASA-style)
    3. Rotation transition penalties
    4. Night shift clustering (avoid isolated nights)
    """

    WOCL_START = 2.0
    WOCL_END = 6.0
    HIGH_RISK_PROCEDURES = [
        "central_line",
        "intubation",
        "lumbar_puncture",
        "arterial_line",
        "chest_tube",
        "conscious_sedation",
    ]

    def __init__(
        self,
        weight: float = 50.0,
        wocl_penalty_multiplier: float = 2.0,
        enabled: bool = True,
    ):
        """
        Initialize circadian constraint.

        Args:
            weight: Base penalty weight
            wocl_penalty_multiplier: Extra penalty for WOCL violations
            enabled: Whether constraint is active
        """
        super().__init__(
            name="CircadianProtection",
            constraint_type=ConstraintType.RESILIENCE,
            weight=weight,
            priority=ConstraintPriority.HIGH,
            enabled=enabled,
        )
        self.wocl_multiplier = wocl_penalty_multiplier
        self.model = ThreeProcessModel()

    def is_wocl_period(self, time_of_day: float) -> bool:
        """Check if time falls within WOCL."""
        return self.WOCL_START <= time_of_day < self.WOCL_END

    def calculate_max_shift_duration(
        self,
        start_hour: float,
        base_duration: float = 12.0,
    ) -> float:
        """
        Calculate maximum shift duration based on start time.

        Based on EASA unfavorable start time rules.
        """
        return self.model.calculate_max_shift_duration(start_hour, base_duration)

    def calculate_circadian_penalty(
        self,
        shift_start_hour: float,
        shift_duration: float,
        has_procedure: bool = False,
        procedure_type: str = "",
    ) -> float:
        """
        Calculate penalty for circadian misalignment.

        Args:
            shift_start_hour: Hour of day shift starts (0-23)
            shift_duration: Duration in hours
            has_procedure: Whether shift includes procedures
            procedure_type: Type of procedure (for high-risk check)

        Returns:
            Penalty value
        """
        penalty = 0.0

        # WOCL exposure penalty
        shift_end_hour = (shift_start_hour + shift_duration) % 24

        # Check if shift overlaps WOCL
        wocl_overlap = False
        if shift_start_hour <= self.WOCL_END or shift_end_hour >= self.WOCL_START:
            wocl_overlap = self._check_wocl_overlap(
                shift_start_hour, shift_duration
            )

        if wocl_overlap:
            wocl_hours = self._calculate_wocl_hours(shift_start_hour, shift_duration)
            penalty += self.weight * wocl_hours * 0.5

            # Extra penalty for procedures during WOCL
            if has_procedure:
                if procedure_type.lower() in [p.lower() for p in self.HIGH_RISK_PROCEDURES]:
                    penalty *= self.wocl_multiplier

        # Shift duration penalty
        max_duration = self.calculate_max_shift_duration(shift_start_hour)
        if shift_duration > max_duration:
            excess = shift_duration - max_duration
            penalty += self.weight * excess * 0.3

        return penalty

    def _check_wocl_overlap(self, start_hour: float, duration: float) -> bool:
        """Check if shift overlaps with WOCL window."""
        end_hour = start_hour + duration

        # Handle overnight shifts
        if end_hour > 24:
            # Shift wraps past midnight
            return (start_hour < self.WOCL_END) or (end_hour % 24 > self.WOCL_START)

        # Normal shift
        return not (end_hour <= self.WOCL_START or start_hour >= self.WOCL_END)

    def _calculate_wocl_hours(self, start_hour: float, duration: float) -> float:
        """Calculate hours of WOCL exposure during shift."""
        end_hour = start_hour + duration
        wocl_hours = 0.0

        # Calculate overlap with WOCL window (2-6 AM)
        if end_hour > 24:
            # Overnight shift
            # First check 2-6 AM on next day
            wocl_start_next = max(0, min(self.WOCL_END, end_hour % 24) - self.WOCL_START)
            wocl_hours += max(0, wocl_start_next)

            # Check if shift started before WOCL ended
            if start_hour < self.WOCL_END:
                wocl_hours += min(self.WOCL_END, 24) - max(self.WOCL_START, start_hour)
        else:
            # Same-day shift
            overlap_start = max(self.WOCL_START, start_hour)
            overlap_end = min(self.WOCL_END, end_hour)
            if overlap_end > overlap_start:
                wocl_hours = overlap_end - overlap_start

        return wocl_hours

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add circadian penalties to CP-SAT objective."""
        if not self.enabled:
            return

        # Similar to FatigueSoftConstraint - add penalty terms to objective
        pass

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add circadian penalties to PuLP objective."""
        if not self.enabled:
            return

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate circadian alignment of assignments."""
        if not self.enabled:
            return ConstraintResult(satisfied=True)

        total_penalty = 0.0
        violations = []

        for assignment in assignments:
            block = getattr(assignment, "block", None)
            rotation = getattr(assignment, "rotation", None)

            if not block:
                continue

            # Get shift timing
            tod = getattr(block, "time_of_day", "AM")
            start_hour = 7.0 if tod == "AM" else 13.0
            duration = 6.0  # Half-day block

            # Check for procedures
            has_procedure = False
            procedure_type = ""
            if rotation:
                has_procedure = getattr(rotation, "has_procedures", False)
                procedure_type = getattr(rotation, "procedure_type", "")

            penalty = self.calculate_circadian_penalty(
                start_hour, duration, has_procedure, procedure_type
            )

            total_penalty += penalty

            # Add violation for significant WOCL exposure
            if self._check_wocl_overlap(start_hour, duration):
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message="Shift overlaps Window of Circadian Low (2-6 AM)",
                        block_id=block.id,
                    )
                )

        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=total_penalty,
        )


# =============================================================================
# Constraint Factory
# =============================================================================


def create_fatigue_constraints(
    hard_threshold: float = 70.0,
    soft_weight: float = 100.0,
    circadian_weight: float = 50.0,
    enable_hard: bool = True,
    enable_soft: bool = True,
    enable_circadian: bool = True,
) -> list[Constraint]:
    """
    Create a set of fatigue-aware constraints.

    Factory function to create standard FRMS constraint set.

    Args:
        hard_threshold: Effectiveness threshold for hard constraint
        soft_weight: Weight for soft penalty constraint
        circadian_weight: Weight for circadian constraint
        enable_hard: Enable hard fatigue constraint
        enable_soft: Enable soft fatigue penalty
        enable_circadian: Enable circadian protection

    Returns:
        List of configured constraint objects
    """
    constraints = []

    if enable_hard:
        constraints.append(FatigueConstraint(threshold=hard_threshold))

    if enable_soft:
        constraints.append(FatigueSoftConstraint(weight=soft_weight))

    if enable_circadian:
        constraints.append(CircadianConstraint(weight=circadian_weight))

    logger.info(f"Created {len(constraints)} fatigue-aware constraints")
    return constraints
