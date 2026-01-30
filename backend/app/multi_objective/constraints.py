"""
Advanced Constraint Handling for Multi-Objective Optimization.

This module provides sophisticated constraint handling techniques for
dealing with infeasible solutions during multi-objective optimization.

Constraint Handling Approaches:
    1. Penalty Methods: Add constraint violations to objective function
    2. Repair Operators: Transform infeasible solutions to feasible ones
    3. Feasibility Preservation: Maintain feasibility through evolution
    4. Constraint Relaxation: Gradually relax hard constraints

Multi-Objective Lens - Constraints as Objectives:
    In multi-objective optimization, hard constraints can sometimes be
    treated as additional objectives. This perspective reveals:

    - The "constraint boundary" is itself a Pareto-like surface
    - Trade-offs exist between constraint satisfaction and optimization
    - Infeasible regions may contain valuable information about the problem

    Practical implications for scheduling:
    - ACGME constraints are truly hard (regulatory)
    - Preference constraints can be relaxed with penalties
    - Capacity constraints may have elastic boundaries

Classes:
    - ConstraintHandlingMethod: Enum of handling strategies
    - PenaltyMethod: Various penalty function approaches
    - RepairOperator: Strategies for fixing infeasible solutions
    - FeasibilityPreserver: Maintains feasibility during evolution
    - ConstraintHandler: Orchestrates constraint handling
    - ConstraintRelaxer: Gradual constraint relaxation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import UUID

import numpy as np

from .core import ObjectiveConfig, ObjectiveDirection, Solution


class ConstraintHandlingMethod(Enum):
    """Available methods for handling constraints."""

    PENALTY = "penalty"
    REPAIR = "repair"
    FEASIBILITY_RULES = "feasibility_rules"
    EPSILON_CONSTRAINT = "epsilon_constraint"
    STOCHASTIC_RANKING = "stochastic_ranking"
    HYBRID = "hybrid"


class PenaltyType(Enum):
    """Types of penalty functions."""

    STATIC = "static"
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"
    DEATH = "death"
    CONSTRAINT_DOMINANCE = "constraint_dominance"


@dataclass
class ConstraintViolation:
    """Represents a single constraint violation."""

    constraint_name: str
    constraint_type: str
    magnitude: float
    details: dict[str, Any] = field(default_factory=dict)
    is_hard: bool = True
    relaxable: bool = False
    affected_entities: list[UUID] = field(default_factory=list)


@dataclass
class ConstraintEvaluation:
    """Result of evaluating all constraints for a solution."""

    is_feasible: bool
    total_violation: float
    violations: list[ConstraintViolation] = field(default_factory=list)
    hard_violation_count: int = 0
    soft_violation_count: int = 0
    penalty: float = 0.0
    can_repair: bool = False
    repair_cost: float = 0.0


class PenaltyMethod(ABC):
    """
    Abstract base class for penalty function methods.

    Penalty methods transform constrained optimization into unconstrained
    by adding penalty terms to the objective function.
    """

    @abstractmethod
    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
        generation: int,
        max_generations: int,
    ) -> float:
        """
        Calculate penalty for constraint violations.

        Args:
            violations: List of constraint violations
            generation: Current generation number
            max_generations: Maximum number of generations

        Returns:
            Penalty value to add to objective
        """
        pass


class StaticPenaltyMethod(PenaltyMethod):
    """
    Static penalty with fixed coefficients.

    penalty = sum(k_i * g_i^2)

    where k_i is the penalty coefficient and g_i is the violation magnitude.
    """

    def __init__(
        self,
        hard_coefficient: float = 1000.0,
        soft_coefficient: float = 10.0,
    ) -> None:
        """
        Initialize static penalty.

        Args:
            hard_coefficient: Penalty multiplier for hard constraints
            soft_coefficient: Penalty multiplier for soft constraints
        """
        self.hard_coefficient = hard_coefficient
        self.soft_coefficient = soft_coefficient

    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
        generation: int,
        max_generations: int,
    ) -> float:
        """Calculate static penalty."""
        penalty = 0.0
        for v in violations:
            coeff = self.hard_coefficient if v.is_hard else self.soft_coefficient
            penalty += coeff * (v.magnitude**2)
        return penalty


class DynamicPenaltyMethod(PenaltyMethod):
    """
    Dynamic penalty that increases over generations.

    penalty = sum((C * t)^alpha * g_i^beta)

    where t is generation, C and alpha control growth rate.
    Early generations allow exploration of infeasible space,
    later generations heavily penalize violations.
    """

    def __init__(
        self,
        base_coefficient: float = 100.0,
        growth_rate: float = 2.0,
        violation_power: float = 2.0,
    ) -> None:
        """
        Initialize dynamic penalty.

        Args:
            base_coefficient: Base penalty coefficient
            growth_rate: Exponent for generation-based growth
            violation_power: Exponent for violation magnitude
        """
        self.base_coefficient = base_coefficient
        self.growth_rate = growth_rate
        self.violation_power = violation_power

    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
        generation: int,
        max_generations: int,
    ) -> float:
        """Calculate dynamic penalty that grows over generations."""
        if max_generations == 0:
            progress = 1.0
        else:
            progress = (generation + 1) / max_generations

            # Coefficient grows with generation
        current_coeff = self.base_coefficient * (progress**self.growth_rate)

        penalty = 0.0
        for v in violations:
            multiplier = 10.0 if v.is_hard else 1.0
            penalty += multiplier * current_coeff * (v.magnitude**self.violation_power)

        return penalty


class AdaptivePenaltyMethod(PenaltyMethod):
    """
    Adaptive penalty that adjusts based on population feasibility.

    If too few feasible solutions: decrease penalty
    If too many feasible solutions: increase penalty

    Maintains a balance between exploration and constraint satisfaction.
    """

    def __init__(
        self,
        initial_coefficient: float = 100.0,
        target_feasibility: float = 0.5,
        adaptation_rate: float = 0.1,
    ) -> None:
        """
        Initialize adaptive penalty.

        Args:
            initial_coefficient: Starting penalty coefficient
            target_feasibility: Desired fraction of feasible solutions
            adaptation_rate: Rate of coefficient adaptation
        """
        self.coefficient = initial_coefficient
        self.target_feasibility = target_feasibility
        self.adaptation_rate = adaptation_rate
        self._feasibility_history: list[float] = []

    def update_feasibility(self, feasibility_ratio: float) -> None:
        """Update coefficient based on current feasibility ratio."""
        self._feasibility_history.append(feasibility_ratio)

        if feasibility_ratio < self.target_feasibility:
            # Too few feasible - reduce penalty to allow exploration
            self.coefficient *= 1 - self.adaptation_rate
        else:
            # Too many feasible - increase penalty for convergence
            self.coefficient *= 1 + self.adaptation_rate

            # Keep within reasonable bounds
        self.coefficient = max(1.0, min(10000.0, self.coefficient))

    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
        generation: int,
        max_generations: int,
    ) -> float:
        """Calculate adaptive penalty."""
        penalty = 0.0
        for v in violations:
            multiplier = 10.0 if v.is_hard else 1.0
            penalty += multiplier * self.coefficient * (v.magnitude**2)
        return penalty


class ConstraintDominanceMethod(PenaltyMethod):
    """
    Constraint dominance principle (used in NSGA-II).

    Rules:
    1. Feasible solutions always dominate infeasible
    2. Among infeasible, smaller violation is better
    3. Among feasible, use Pareto dominance

    This method returns a modified penalty suitable for ranking.
    """

    def __init__(self, feasibility_weight: float = float("inf")) -> None:
        """
        Initialize constraint dominance.

        Args:
            feasibility_weight: Weight given to feasibility (inf = strict)
        """
        self.feasibility_weight = feasibility_weight

    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
        generation: int,
        max_generations: int,
    ) -> float:
        """Calculate penalty for constraint dominance ranking."""
        if not violations:
            return 0.0

        total_violation = sum(v.magnitude for v in violations)

        # If any hard constraint is violated, add large penalty
        has_hard_violation = any(v.is_hard for v in violations)
        if has_hard_violation:
            return self.feasibility_weight + total_violation

        return total_violation


class RepairOperator(ABC):
    """
    Abstract base class for repair operators.

    Repair operators attempt to transform infeasible solutions into
    feasible ones while minimizing objective degradation.
    """

    @abstractmethod
    def can_repair(
        self, solution: Solution, violations: list[ConstraintViolation]
    ) -> bool:
        """Check if this operator can repair the given violations."""
        pass

    @abstractmethod
    def repair(
        self,
        solution: Solution,
        violations: list[ConstraintViolation],
        context: Any,
    ) -> tuple[Solution, bool]:
        """
        Attempt to repair the solution.

        Args:
            solution: Solution to repair
            violations: List of violations to fix
            context: Scheduling context with available resources

        Returns:
            Tuple of (repaired_solution, success)
        """
        pass


class GreedyRepairOperator(RepairOperator):
    """
    Greedy repair that fixes violations one at a time.

    Iterates through violations in priority order and applies
    minimal changes to resolve each one.
    """

    def __init__(
        self,
        max_iterations: int = 100,
        repair_functions: dict[str, Callable] | None = None,
    ) -> None:
        """
        Initialize greedy repair.

        Args:
            max_iterations: Maximum repair attempts
            repair_functions: Custom repair functions by constraint type
        """
        self.max_iterations = max_iterations
        self.repair_functions = repair_functions or {}

    def can_repair(
        self, solution: Solution, violations: list[ConstraintViolation]
    ) -> bool:
        """Check if violations are repairable."""
        for v in violations:
            if v.is_hard and not v.relaxable:
                # Check if we have a repair function
                if v.constraint_type not in self.repair_functions:
                    return False
        return True

    def repair(
        self,
        solution: Solution,
        violations: list[ConstraintViolation],
        context: Any,
    ) -> tuple[Solution, bool]:
        """Greedily repair violations."""
        repaired = solution.copy()
        remaining_violations = list(violations)

        for _ in range(self.max_iterations):
            if not remaining_violations:
                return repaired, True

                # Pick violation with smallest magnitude (easier to fix)
            remaining_violations.sort(key=lambda v: v.magnitude)
            violation = remaining_violations[0]

            # Apply repair function
            repair_fn = self.repair_functions.get(violation.constraint_type)
            if repair_fn:
                success = repair_fn(repaired, violation, context)
                if success:
                    remaining_violations.pop(0)
                else:
                    # Could not repair this violation
                    return repaired, False
            else:
                return repaired, False

        return repaired, len(remaining_violations) == 0


class RandomRepairOperator(RepairOperator):
    """
    Random repair that makes stochastic changes.

    Useful for escaping local optima when greedy repair fails.
    """

    def __init__(
        self,
        max_attempts: int = 10,
        perturbation_strength: float = 0.1,
    ) -> None:
        """
        Initialize random repair.

        Args:
            max_attempts: Maximum repair attempts
            perturbation_strength: Magnitude of random changes
        """
        self.max_attempts = max_attempts
        self.perturbation_strength = perturbation_strength

    def can_repair(
        self, solution: Solution, violations: list[ConstraintViolation]
    ) -> bool:
        """Random repair can always attempt repair."""
        return True

    def repair(
        self,
        solution: Solution,
        violations: list[ConstraintViolation],
        context: Any,
    ) -> tuple[Solution, bool]:
        """Attempt random repairs."""
        best_solution = solution
        best_violation = sum(v.magnitude for v in violations)

        for _ in range(self.max_attempts):
            # Create random perturbation
            candidate = solution.copy()

            # Apply random changes based on affected entities
            for v in violations:
                for entity_id in v.affected_entities:
                    # Randomly reassign entity (implementation depends on problem)
                    pass

                    # Evaluate candidate
            new_violations = self._evaluate_constraints(candidate, context)
            new_violation = sum(v.magnitude for v in new_violations)

            if new_violation < best_violation:
                best_solution = candidate
                best_violation = new_violation

                if best_violation == 0:
                    return best_solution, True

        return best_solution, best_violation == 0

    def _evaluate_constraints(
        self, solution: Solution, context: Any
    ) -> list[ConstraintViolation]:
        """Evaluate constraints for a solution (to be overridden)."""
        return []


class FeasibilityPreserver:
    """
    Maintains feasibility during evolutionary operations.

    Instead of repairing infeasible solutions, this approach generates
    only feasible offspring through careful operator design.
    """

    def __init__(
        self,
        feasibility_check: Callable[[Solution, Any], bool],
        max_attempts: int = 100,
    ) -> None:
        """
        Initialize feasibility preserver.

        Args:
            feasibility_check: Function to check if solution is feasible
            max_attempts: Max attempts to generate feasible offspring
        """
        self.feasibility_check = feasibility_check
        self.max_attempts = max_attempts

    def generate_feasible_offspring(
        self,
        parent1: Solution,
        parent2: Solution,
        crossover: Callable[[Solution, Solution], Solution],
        mutate: Callable[[Solution], Solution],
        context: Any,
    ) -> Solution | None:
        """
        Generate a feasible offspring.

        Uses rejection sampling: generate candidates until a feasible
        one is found or max_attempts is reached.

        Args:
            parent1: First parent solution
            parent2: Second parent solution
            crossover: Crossover operator
            mutate: Mutation operator
            context: Problem context

        Returns:
            Feasible offspring or None if none found
        """
        for _ in range(self.max_attempts):
            # Generate offspring
            offspring = crossover(parent1, parent2)
            offspring = mutate(offspring)

            # Check feasibility
            if self.feasibility_check(offspring, context):
                return offspring

                # Fallback: return best parent
        if self.feasibility_check(parent1, context):
            return parent1.copy()
        if self.feasibility_check(parent2, context):
            return parent2.copy()

        return None


@dataclass
class RelaxationLevel:
    """Represents a constraint relaxation level."""

    constraint_name: str
    original_threshold: float
    current_threshold: float
    relaxation_step: float
    max_relaxation: float
    is_relaxed: bool = False


class ConstraintRelaxer:
    """
    Manages gradual constraint relaxation for infeasible problems.

    When no feasible solution exists, constraints can be progressively
    relaxed until the problem becomes feasible. The relaxation is then
    gradually restored as the search progresses.

    Use Cases in Scheduling:
    - Relax capacity limits during emergencies
    - Allow temporary ACGME violations with escalation
    - Adjust equity targets when understaffed
    """

    def __init__(
        self,
        relaxation_rate: float = 0.1,
        recovery_rate: float = 0.05,
    ) -> None:
        """
        Initialize constraint relaxer.

        Args:
            relaxation_rate: Rate at which constraints are relaxed
            recovery_rate: Rate at which constraints are restored
        """
        self.relaxation_rate = relaxation_rate
        self.recovery_rate = recovery_rate
        self.relaxations: dict[str, RelaxationLevel] = {}
        self._infeasible_streak = 0
        self._feasible_streak = 0

    def register_constraint(
        self,
        name: str,
        threshold: float,
        relaxation_step: float | None = None,
        max_relaxation: float | None = None,
    ) -> None:
        """
        Register a constraint for potential relaxation.

        Args:
            name: Constraint name
            threshold: Original constraint threshold
            relaxation_step: Amount to relax per step (default: 10% of threshold)
            max_relaxation: Maximum relaxation allowed (default: 50% of threshold)
        """
        step = relaxation_step or abs(threshold * 0.1)
        max_relax = max_relaxation or abs(threshold * 0.5)

        self.relaxations[name] = RelaxationLevel(
            constraint_name=name,
            original_threshold=threshold,
            current_threshold=threshold,
            relaxation_step=step,
            max_relaxation=max_relax,
        )

    def update(self, is_feasible: bool, feasibility_ratio: float) -> dict[str, float]:
        """
        Update relaxation levels based on feasibility.

        Args:
            is_feasible: Whether best solution is feasible
            feasibility_ratio: Fraction of population that is feasible

        Returns:
            Dictionary of current thresholds
        """
        if is_feasible and feasibility_ratio > 0.1:
            self._feasible_streak += 1
            self._infeasible_streak = 0

            # Restore constraints if feasible for several generations
            if self._feasible_streak > 5:
                self._restore_constraints()

        else:
            self._infeasible_streak += 1
            self._feasible_streak = 0

            # Relax constraints if infeasible for several generations
            if self._infeasible_streak > 3:
                self._relax_constraints()

        return self.get_current_thresholds()

    def _relax_constraints(self) -> None:
        """Relax constraints by one step."""
        for level in self.relaxations.values():
            if not level.is_relaxed:
                new_threshold = level.current_threshold + level.relaxation_step

                # Check max relaxation
                max_threshold = level.original_threshold + level.max_relaxation

                if new_threshold <= max_threshold:
                    level.current_threshold = new_threshold
                    level.is_relaxed = True

    def _restore_constraints(self) -> None:
        """Restore constraints toward original values."""
        for level in self.relaxations.values():
            if level.is_relaxed:
                # Move toward original
                if level.current_threshold > level.original_threshold:
                    level.current_threshold -= (
                        level.relaxation_step * self.recovery_rate
                    )
                    level.current_threshold = max(
                        level.current_threshold, level.original_threshold
                    )
                else:
                    level.current_threshold += (
                        level.relaxation_step * self.recovery_rate
                    )
                    level.current_threshold = min(
                        level.current_threshold, level.original_threshold
                    )

                    # Check if fully restored
                if abs(level.current_threshold - level.original_threshold) < 0.01:
                    level.current_threshold = level.original_threshold
                    level.is_relaxed = False

    def get_current_thresholds(self) -> dict[str, float]:
        """Get current relaxed thresholds."""
        return {
            name: level.current_threshold for name, level in self.relaxations.items()
        }

    def is_any_relaxed(self) -> bool:
        """Check if any constraint is currently relaxed."""
        return any(level.is_relaxed for level in self.relaxations.values())

    def get_relaxation_report(self) -> list[dict[str, Any]]:
        """Get detailed report of all relaxation states."""
        return [
            {
                "constraint": level.constraint_name,
                "original": level.original_threshold,
                "current": level.current_threshold,
                "relaxation_pct": (
                    abs(level.current_threshold - level.original_threshold)
                    / abs(level.max_relaxation)
                    * 100
                    if level.max_relaxation != 0
                    else 0
                ),
                "is_relaxed": level.is_relaxed,
            }
            for level in self.relaxations.values()
        ]


class ConstraintHandler:
    """
    Orchestrates constraint handling during optimization.

    Combines penalty methods, repair operators, and feasibility preservation
    into a unified constraint handling strategy.
    """

    def __init__(
        self,
        method: ConstraintHandlingMethod = ConstraintHandlingMethod.PENALTY,
        penalty_method: PenaltyMethod | None = None,
        repair_operator: RepairOperator | None = None,
        feasibility_preserver: FeasibilityPreserver | None = None,
        constraint_relaxer: ConstraintRelaxer | None = None,
    ) -> None:
        """
        Initialize constraint handler.

        Args:
            method: Primary constraint handling method
            penalty_method: Penalty function (for PENALTY method)
            repair_operator: Repair operator (for REPAIR method)
            feasibility_preserver: Feasibility preserver
            constraint_relaxer: Constraint relaxer for infeasible problems
        """
        self.method = method
        self.penalty_method = penalty_method or AdaptivePenaltyMethod()
        self.repair_operator = repair_operator
        self.feasibility_preserver = feasibility_preserver
        self.constraint_relaxer = constraint_relaxer

        # Statistics
        self.total_evaluations = 0
        self.feasible_count = 0
        self.repaired_count = 0
        self.current_generation = 0
        self.max_generations = 100

    def set_generation_info(self, current: int, max_gen: int) -> None:
        """Set current generation for dynamic methods."""
        self.current_generation = current
        self.max_generations = max_gen

    def process_solution(
        self,
        solution: Solution,
        violations: list[ConstraintViolation],
        context: Any,
    ) -> Solution:
        """
        Process a solution according to the constraint handling strategy.

        Args:
            solution: Solution to process
            violations: Detected constraint violations
            context: Problem context

        Returns:
            Processed solution (possibly repaired with penalty applied)
        """
        self.total_evaluations += 1

        if not violations:
            solution.is_feasible = True
            solution.total_constraint_violation = 0.0
            solution.constraint_violations = []
            self.feasible_count += 1
            return solution

            # Record violations
        solution.constraint_violations = [v.constraint_name for v in violations]
        solution.total_constraint_violation = sum(v.magnitude for v in violations)
        solution.is_feasible = not any(v.is_hard for v in violations)

        # Apply handling method
        if self.method == ConstraintHandlingMethod.PENALTY:
            penalty = self.penalty_method.calculate_penalty(
                violations, self.current_generation, self.max_generations
            )
            solution.metadata["constraint_penalty"] = penalty

        elif self.method == ConstraintHandlingMethod.REPAIR:
            if self.repair_operator and self.repair_operator.can_repair(
                solution, violations
            ):
                repaired, success = self.repair_operator.repair(
                    solution, violations, context
                )
                if success:
                    self.repaired_count += 1
                    repaired.is_feasible = True
                    repaired.total_constraint_violation = 0.0
                    repaired.constraint_violations = []
                    return repaired

                    # Fallback to penalty
            penalty = self.penalty_method.calculate_penalty(
                violations, self.current_generation, self.max_generations
            )
            solution.metadata["constraint_penalty"] = penalty

        elif self.method == ConstraintHandlingMethod.HYBRID:
            # Try repair first, then apply penalty to remaining violations
            if self.repair_operator and self.repair_operator.can_repair(
                solution, violations
            ):
                repaired, success = self.repair_operator.repair(
                    solution, violations, context
                )
                if success:
                    self.repaired_count += 1
                    repaired.is_feasible = True
                    repaired.total_constraint_violation = 0.0
                    return repaired
                    # Partial repair - recalculate violations
                solution = repaired

            penalty = self.penalty_method.calculate_penalty(
                violations, self.current_generation, self.max_generations
            )
            solution.metadata["constraint_penalty"] = penalty

        if solution.is_feasible:
            self.feasible_count += 1

        return solution

    def update_adaptive(self, population: list[Solution]) -> None:
        """
        Update adaptive methods based on population statistics.

        Args:
            population: Current population
        """
        if not population:
            return

        feasible_ratio = sum(1 for s in population if s.is_feasible) / len(population)

        # Update adaptive penalty
        if isinstance(self.penalty_method, AdaptivePenaltyMethod):
            self.penalty_method.update_feasibility(feasible_ratio)

            # Update constraint relaxer
        if self.constraint_relaxer:
            best_feasible = any(s.is_feasible for s in population)
            self.constraint_relaxer.update(best_feasible, feasible_ratio)

    def get_statistics(self) -> dict[str, Any]:
        """Get constraint handling statistics."""
        return {
            "total_evaluations": self.total_evaluations,
            "feasible_count": self.feasible_count,
            "feasibility_rate": (
                self.feasible_count / self.total_evaluations
                if self.total_evaluations > 0
                else 0.0
            ),
            "repaired_count": self.repaired_count,
            "repair_rate": (
                self.repaired_count / self.total_evaluations
                if self.total_evaluations > 0
                else 0.0
            ),
            "method": self.method.value,
            "is_relaxed": (
                self.constraint_relaxer.is_any_relaxed()
                if self.constraint_relaxer
                else False
            ),
        }

        # Pre-configured constraint handlers for common scenarios


def create_acgme_constraint_handler() -> ConstraintHandler:
    """Create constraint handler for ACGME compliance (strict)."""
    return ConstraintHandler(
        method=ConstraintHandlingMethod.PENALTY,
        penalty_method=ConstraintDominanceMethod(),
    )


def create_scheduling_constraint_handler() -> ConstraintHandler:
    """Create constraint handler for general scheduling."""
    relaxer = ConstraintRelaxer()
    relaxer.register_constraint("capacity", 1.0, 0.1, 0.5)
    relaxer.register_constraint("equity", 0.3, 0.05, 0.2)

    return ConstraintHandler(
        method=ConstraintHandlingMethod.HYBRID,
        penalty_method=AdaptivePenaltyMethod(target_feasibility=0.3),
        repair_operator=GreedyRepairOperator(),
        constraint_relaxer=relaxer,
    )


def create_emergency_constraint_handler() -> ConstraintHandler:
    """Create constraint handler for emergency scheduling (relaxed)."""
    relaxer = ConstraintRelaxer(relaxation_rate=0.2, recovery_rate=0.1)
    relaxer.register_constraint("capacity", 1.0, 0.2, 1.0)
    relaxer.register_constraint("equity", 0.3, 0.1, 0.5)
    relaxer.register_constraint("coverage", 0.95, 0.05, 0.2)

    return ConstraintHandler(
        method=ConstraintHandlingMethod.HYBRID,
        penalty_method=DynamicPenaltyMethod(growth_rate=1.5),
        repair_operator=RandomRepairOperator(max_attempts=20),
        constraint_relaxer=relaxer,
    )
