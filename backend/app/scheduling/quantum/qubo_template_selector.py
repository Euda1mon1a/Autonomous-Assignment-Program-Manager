"""
QUBO-Based Template Selection for Rotation Optimization.

This module implements Quadratic Unconstrained Binary Optimization (QUBO)
for rotation template selection - the 780 variable sweet spot for quantum
advantage exploration.

Key Features:
1. Template selection formulation (templates × blocks × constraints)
2. Fairness objectives for equal rotation distribution
3. Pareto front exploration for multi-objective optimization
4. Hybrid classical-quantum pipeline
5. Energy landscape visualization
6. Adaptive temperature scheduling

References:
- QUBO Formulation: https://arxiv.org/abs/2103.01708
- Multi-objective QUBO: https://arxiv.org/abs/2111.08062
- Pareto Optimization: https://en.wikipedia.org/wiki/Pareto_efficiency
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

class TemplateDesirability(str, Enum):
    """Classification of rotation template desirability."""
    HIGHLY_DESIRABLE = "highly_desirable"  # e.g., Sports Medicine, Electives
    NEUTRAL = "neutral"                     # e.g., Standard Clinic
    UNDESIRABLE = "undesirable"             # e.g., Night Float, Weekend Call


# Default desirability mappings (can be overridden)
DEFAULT_DESIRABILITY_MAP = {
    "Sports Medicine": TemplateDesirability.HIGHLY_DESIRABLE,
    "Elective": TemplateDesirability.HIGHLY_DESIRABLE,
    "Research": TemplateDesirability.HIGHLY_DESIRABLE,
    "Clinic": TemplateDesirability.NEUTRAL,
    "FMIT": TemplateDesirability.UNDESIRABLE,
    "Night Float": TemplateDesirability.UNDESIRABLE,
    "Call": TemplateDesirability.UNDESIRABLE,
}


@dataclass
class TemplateSelectionConfig:
    """Configuration for QUBO template selection."""

    # Penalty weights
    hard_constraint_penalty: float = 10000.0
    acgme_penalty: float = 5000.0
    soft_constraint_penalty: float = 100.0
    fairness_penalty: float = 500.0

    # Objective weights (for weighted-sum scalarization)
    coverage_weight: float = 1.0
    fairness_weight: float = 1.0
    preference_weight: float = 0.5
    learning_goal_weight: float = 0.3

    # Annealing parameters
    num_reads: int = 100
    num_sweeps: int = 1000
    beta_start: float = 0.1
    beta_end: float = 4.2

    # Adaptive temperature parameters
    use_adaptive_temperature: bool = True
    reheat_threshold: float = 0.001  # Reheat if improvement < threshold
    reheat_factor: float = 0.5       # Multiply beta by this on reheat

    # Pareto parameters
    pareto_population: int = 50
    pareto_generations: int = 100

    # Seed for reproducibility
    seed: int | None = None


@dataclass
class EnergyLandscapePoint:
    """A point in the QUBO energy landscape."""

    state: dict[int, int]
    energy: float
    objectives: dict[str, float]
    is_local_minimum: bool = False
    tunneling_probability: float = 0.0
    basin_size: int = 1


@dataclass
class ParetoSolution:
    """A solution on the Pareto frontier."""

    solution_id: int
    state: dict[int, int]
    objectives: dict[str, float]
    assignments: list[tuple[UUID, UUID, UUID]]
    rank: int = 0
    crowding_distance: float = 0.0

    def dominates(self, other: "ParetoSolution") -> bool:
        """Check if this solution dominates another."""
        dominated = False
        for obj in self.objectives:
            if self.objectives[obj] > other.objectives.get(obj, float('inf')):
                return False
            if self.objectives[obj] < other.objectives.get(obj, float('inf')):
                dominated = True
        return dominated


@dataclass
class TemplateSelectionResult:
    """Result of QUBO template selection optimization."""

    success: bool
    assignments: list[tuple[UUID, UUID, UUID | None]]
    pareto_frontier: list[ParetoSolution]
    energy_landscape: list[EnergyLandscapePoint]
    statistics: dict[str, Any]
    runtime_seconds: float
    recommended_solution_id: int | None = None

    def to_json(self) -> dict:
        """Export result to JSON-compatible format."""
        return {
            "success": self.success,
            "num_assignments": len(self.assignments),
            "pareto_frontier": [
                {
                    "solution_id": sol.solution_id,
                    "objectives": sol.objectives,
                    "rank": sol.rank,
                    "crowding_distance": sol.crowding_distance,
                    "num_assignments": len(sol.assignments),
                }
                for sol in self.pareto_frontier
            ],
            "energy_landscape": [
                {
                    "energy": point.energy,
                    "objectives": point.objectives,
                    "is_local_minimum": point.is_local_minimum,
                    "tunneling_probability": point.tunneling_probability,
                    "basin_size": point.basin_size,
                }
                for point in self.energy_landscape[:100]  # Limit for export
            ],
            "statistics": self.statistics,
            "runtime_seconds": self.runtime_seconds,
            "recommended_solution_id": self.recommended_solution_id,
        }


# ============================================================================
# QUBO TEMPLATE FORMULATION
# ============================================================================

class QUBOTemplateFormulation:
    """
    QUBO formulation for rotation template selection.

    This formulation targets the 780-variable sweet spot by:
    1. Focusing on template selection (not individual block assignments)
    2. Encoding fairness as quadratic penalty terms
    3. Supporting multi-objective optimization via scalarization

    Binary variables: x[resident, rotation_period, template]
    Where rotation_period aggregates blocks into 2-week periods.
    """

    def __init__(
        self,
        context: SchedulingContext,
        config: TemplateSelectionConfig | None = None,
        desirability_map: dict[str, TemplateDesirability] | None = None,
    ):
        """
        Initialize QUBO template formulation.

        Args:
            context: SchedulingContext with blocks, residents, templates
            config: Configuration parameters
            desirability_map: Template name -> desirability classification
        """
        self.context = context
        self.config = config or TemplateSelectionConfig()
        self.desirability_map = desirability_map or DEFAULT_DESIRABILITY_MAP

        # Aggregate blocks into rotation periods (2-week chunks)
        self.rotation_periods = self._build_rotation_periods()

        # Variable indexing: x[r, p, t] -> flat index
        self.var_index: dict[tuple[int, int, int], int] = {}
        self.index_to_var: dict[int, tuple[int, int, int]] = {}
        self._build_variable_index()

        # QUBO matrix (sparse representation)
        self.Q: dict[tuple[int, int], float] = {}

        # Objective components for Pareto analysis
        self.objective_matrices: dict[str, dict[tuple[int, int], float]] = {}

        logger.info(
            f"QUBO Template Formulation: {self.num_variables} variables "
            f"({len(self.context.residents)} residents × "
            f"{len(self.rotation_periods)} periods × "
            f"{len(self.context.templates)} templates)"
        )

    def _build_rotation_periods(self) -> list[list[Any]]:
        """Aggregate blocks into rotation periods (2-week chunks)."""
        workday_blocks = sorted(
            [b for b in self.context.blocks if not b.is_weekend],
            key=lambda b: b.date
        )

        if not workday_blocks:
            return []

        # Group into 2-week (10 workday) periods
        periods = []
        current_period = []

        for block in workday_blocks:
            current_period.append(block)
            if len(current_period) >= 10:  # ~2 weeks of workdays
                periods.append(current_period)
                current_period = []

        if current_period:
            periods.append(current_period)

        return periods

    def _build_variable_index(self):
        """Build mapping from (resident, period, template) to flat index."""
        idx = 0
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        for r_i, resident in enumerate(self.context.residents):
            for p_i in range(len(self.rotation_periods)):
                for t_i, template in enumerate(valid_templates):
                    self.var_index[(r_i, p_i, t_i)] = idx
                    self.index_to_var[idx] = (r_i, p_i, t_i)
                    idx += 1

        logger.debug(f"Built variable index with {idx} variables")

    @property
    def num_variables(self) -> int:
        """Number of binary variables in the QUBO."""
        return len(self.var_index)

    def build(
        self,
        objective_weights: dict[str, float] | None = None
    ) -> dict[tuple[int, int], float]:
        """
        Build the complete QUBO matrix.

        Args:
            objective_weights: Optional weights to override config defaults

        Returns:
            Q: Sparse QUBO matrix as dict of (i, j) -> coefficient
        """
        weights = objective_weights or {
            "coverage": self.config.coverage_weight,
            "fairness": self.config.fairness_weight,
            "preference": self.config.preference_weight,
            "learning": self.config.learning_goal_weight,
        }

        self.Q = {}
        self.objective_matrices = {
            "coverage": {},
            "fairness": {},
            "preference": {},
            "learning": {},
            "constraints": {},
        }

        # Build individual objective matrices
        self._add_coverage_objective()
        self._add_fairness_objective()
        self._add_preference_objective()
        self._add_learning_goal_objective()

        # Add constraints
        self._add_one_template_per_period_constraint()
        self._add_template_capacity_constraints()
        self._add_availability_constraints()

        # Combine into final Q using weights
        for obj_name, matrix in self.objective_matrices.items():
            weight = weights.get(obj_name, 1.0)
            for (i, j), coef in matrix.items():
                self._add_to_Q(i, j, weight * coef)

        logger.info(
            f"QUBO built: {self.num_variables} variables, "
            f"{len(self.Q)} non-zero terms"
        )

        return self.Q

    def _add_coverage_objective(self):
        """
        Objective: Maximize assignment coverage.

        Each resident should be assigned a template for each period.
        Encoded as: minimize -sum(x[r,p,t]) for all variables
        """
        matrix = self.objective_matrices["coverage"]

        for idx in range(self.num_variables):
            key = (idx, idx)
            matrix[key] = matrix.get(key, 0.0) - 1.0

    def _add_fairness_objective(self):
        """
        Objective: Fair distribution of desirable/undesirable rotations.

        Encode as quadratic penalty for deviation from equal distribution.
        For each desirability category, penalize variance across residents.
        """
        matrix = self.objective_matrices["fairness"]
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        n_residents = len(self.context.residents)
        if n_residents <= 1:
            return

        # Group templates by desirability
        desirability_templates: dict[TemplateDesirability, list[int]] = {
            TemplateDesirability.HIGHLY_DESIRABLE: [],
            TemplateDesirability.NEUTRAL: [],
            TemplateDesirability.UNDESIRABLE: [],
        }

        for t_i, template in enumerate(valid_templates):
            desirability = self.desirability_map.get(
                template.name, TemplateDesirability.NEUTRAL
            )
            desirability_templates[desirability].append(t_i)

        # For each desirability category, add equity constraints
        for desirability, template_indices in desirability_templates.items():
            if not template_indices:
                continue

            # Expected count per resident for this category
            n_periods = len(self.rotation_periods)
            expected_per_resident = (
                len(template_indices) * n_periods / n_residents
            )

            # Penalty weight inversely proportional to expected count
            penalty = self.config.fairness_penalty / max(expected_per_resident, 1)

            # Penalize pairs of same-category assignments to same resident
            # This encourages spreading desirable templates across residents
            for r_i in range(n_residents):
                vars_for_resident = []
                for p_i in range(n_periods):
                    for t_i in template_indices:
                        if (r_i, p_i, t_i) in self.var_index:
                            vars_for_resident.append(
                                self.var_index[(r_i, p_i, t_i)]
                            )

                # Small penalty for each pair (discourages hoarding)
                for i, idx1 in enumerate(vars_for_resident):
                    for idx2 in vars_for_resident[i + 1:]:
                        key = (min(idx1, idx2), max(idx1, idx2))
                        matrix[key] = matrix.get(key, 0.0) + penalty * 0.1

    def _add_preference_objective(self):
        """
        Objective: Satisfy resident preferences.

        Add linear bonus for assignments matching stated preferences.
        """
        matrix = self.objective_matrices["preference"]
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        # TODO: Integrate with actual preference data from context
        # For now, use desirability as proxy
        for (r_i, p_i, t_i), idx in self.var_index.items():
            template = valid_templates[t_i] if t_i < len(valid_templates) else None
            if template:
                desirability = self.desirability_map.get(
                    template.name, TemplateDesirability.NEUTRAL
                )

                # Bonus for desirable templates
                if desirability == TemplateDesirability.HIGHLY_DESIRABLE:
                    key = (idx, idx)
                    matrix[key] = matrix.get(key, 0.0) - 0.5
                elif desirability == TemplateDesirability.UNDESIRABLE:
                    key = (idx, idx)
                    matrix[key] = matrix.get(key, 0.0) + 0.2

    def _add_learning_goal_objective(self):
        """
        Objective: Support learning goals through rotation variety.

        Encourage each resident to experience different template types.
        """
        matrix = self.objective_matrices["learning"]
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        n_periods = len(self.rotation_periods)

        for r_i in range(len(self.context.residents)):
            # For each template, if assigned to multiple periods, add small penalty
            # This encourages variety
            for t_i in range(len(valid_templates)):
                period_vars = []
                for p_i in range(n_periods):
                    if (r_i, p_i, t_i) in self.var_index:
                        period_vars.append(self.var_index[(r_i, p_i, t_i)])

                # Small penalty for consecutive same-template assignments
                for i in range(len(period_vars) - 1):
                    key = (period_vars[i], period_vars[i + 1])
                    matrix[key] = matrix.get(key, 0.0) + 0.05

    def _add_one_template_per_period_constraint(self):
        """
        Constraint: Exactly one template per resident per period.

        Encoded as: penalty * (sum_t x[r,p,t] - 1)^2
        """
        matrix = self.objective_matrices["constraints"]
        n_periods = len(self.rotation_periods)
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        for r_i in range(len(self.context.residents)):
            for p_i in range(n_periods):
                # Get all variables for this (resident, period)
                period_vars = []
                for t_i in range(len(valid_templates)):
                    if (r_i, p_i, t_i) in self.var_index:
                        period_vars.append(self.var_index[(r_i, p_i, t_i)])

                if len(period_vars) <= 1:
                    continue

                # (sum - 1)^2 = sum^2 - 2*sum + 1
                # = sum_i sum_j x_i * x_j - 2*sum_i x_i + 1
                # = sum_i x_i^2 + 2*sum_{i<j} x_i*x_j - 2*sum_i x_i + 1
                # = sum_i (x_i - 2*x_i) + 2*sum_{i<j} x_i*x_j + 1
                # = -sum_i x_i + 2*sum_{i<j} x_i*x_j + 1

                penalty = self.config.hard_constraint_penalty

                # Linear terms (encourage at least one selection)
                for idx in period_vars:
                    key = (idx, idx)
                    matrix[key] = matrix.get(key, 0.0) - penalty

                # Quadratic terms (penalize multiple selections)
                for i, idx1 in enumerate(period_vars):
                    for idx2 in period_vars[i + 1:]:
                        key = (min(idx1, idx2), max(idx1, idx2))
                        matrix[key] = matrix.get(key, 0.0) + 2 * penalty

    def _add_template_capacity_constraints(self):
        """
        Constraint: Respect template capacity limits.

        For templates with max_residents, penalize over-assignment.
        """
        matrix = self.objective_matrices["constraints"]
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]
        n_residents = len(self.context.residents)
        n_periods = len(self.rotation_periods)

        for t_i, template in enumerate(valid_templates):
            max_capacity = getattr(template, 'max_residents', None)
            if max_capacity is None or max_capacity >= n_residents:
                continue

            # For each period, penalize if more than max_capacity assigned
            for p_i in range(n_periods):
                period_vars = []
                for r_i in range(n_residents):
                    if (r_i, p_i, t_i) in self.var_index:
                        period_vars.append(self.var_index[(r_i, p_i, t_i)])

                if len(period_vars) <= max_capacity:
                    continue

                # Soft penalty for exceeding capacity
                # Use quadratic penalty scaled by over-capacity
                penalty = self.config.soft_constraint_penalty * 10

                for i, idx1 in enumerate(period_vars):
                    for idx2 in period_vars[i + 1:]:
                        key = (min(idx1, idx2), max(idx1, idx2))
                        matrix[key] = matrix.get(key, 0.0) + penalty / max_capacity

    def _add_availability_constraints(self):
        """
        Constraint: Cannot assign during unavailable periods.

        High penalty for assignments violating availability.
        """
        matrix = self.objective_matrices["constraints"]
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        for r_i, resident in enumerate(self.context.residents):
            unavail_blocks = self.context.availability.get(resident.id, set())

            for p_i, period_blocks in enumerate(self.rotation_periods):
                # Check if any block in period is unavailable
                period_block_ids = {b.id for b in period_blocks}
                unavailable_in_period = any(
                    self.context.block_idx.get(bid) in unavail_blocks
                    for bid in period_block_ids
                    if bid in self.context.block_idx
                )

                if unavailable_in_period:
                    # Penalize all template assignments for this period
                    for t_i in range(len(valid_templates)):
                        if (r_i, p_i, t_i) in self.var_index:
                            idx = self.var_index[(r_i, p_i, t_i)]
                            key = (idx, idx)
                            matrix[key] = matrix.get(key, 0.0) + \
                                self.config.hard_constraint_penalty

    def _add_to_Q(self, i: int, j: int, value: float):
        """Add value to Q matrix (symmetric)."""
        if i > j:
            i, j = j, i
        key = (i, j)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def decode_solution(
        self,
        sample: dict[int, int]
    ) -> list[tuple[UUID, UUID, UUID | None]]:
        """
        Decode QUBO solution to assignment list.

        Args:
            sample: Dict mapping variable index to 0/1 value

        Returns:
            List of (person_id, block_id, template_id) tuples
        """
        assignments = []
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        for idx, value in sample.items():
            if value == 1 and idx in self.index_to_var:
                r_i, p_i, t_i = self.index_to_var[idx]

                resident = self.context.residents[r_i] if r_i < len(self.context.residents) else None
                template = valid_templates[t_i] if t_i < len(valid_templates) else None
                period_blocks = self.rotation_periods[p_i] if p_i < len(self.rotation_periods) else []

                if resident and template and period_blocks:
                    # Create assignment for each block in the period
                    for block in period_blocks:
                        assignments.append((
                            resident.id,
                            block.id,
                            template.id
                        ))

        return assignments

    def compute_objectives(
        self,
        sample: dict[int, int]
    ) -> dict[str, float]:
        """
        Compute individual objective values for a solution.

        Args:
            sample: Dict mapping variable index to 0/1 value

        Returns:
            Dict of objective name -> value
        """
        objectives = {}

        for obj_name, matrix in self.objective_matrices.items():
            value = 0.0
            for (i, j), coef in matrix.items():
                if i == j:
                    value += coef * sample.get(i, 0)
                else:
                    value += coef * sample.get(i, 0) * sample.get(j, 0)
            objectives[obj_name] = value

        return objectives


# ============================================================================
# ADAPTIVE TEMPERATURE SIMULATED ANNEALING
# ============================================================================

class AdaptiveTemperatureSchedule:
    """
    Adaptive temperature schedule for simulated annealing.

    Features:
    1. Geometric cooling with automatic reheat
    2. Plateau detection with temperature boost
    3. Quantum tunneling probability for barrier crossing
    """

    def __init__(
        self,
        beta_start: float = 0.1,
        beta_end: float = 4.2,
        num_sweeps: int = 1000,
        reheat_threshold: float = 0.001,
        reheat_factor: float = 0.5,
    ):
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.num_sweeps = num_sweeps
        self.reheat_threshold = reheat_threshold
        self.reheat_factor = reheat_factor

        # Tracking
        self.current_sweep = 0
        self.current_beta = beta_start
        self.best_energy = float('inf')
        self.last_improvement_sweep = 0
        self.energy_history: list[float] = []
        self.reheat_count = 0

    def get_beta(self, sweep: int, current_energy: float) -> float:
        """
        Get inverse temperature for current sweep.

        Args:
            sweep: Current sweep number
            current_energy: Current solution energy

        Returns:
            Beta (inverse temperature) value
        """
        self.current_sweep = sweep
        self.energy_history.append(current_energy)

        # Track best energy
        if current_energy < self.best_energy:
            self.best_energy = current_energy
            self.last_improvement_sweep = sweep

        # Check for plateau (no improvement for 10% of sweeps)
        plateau_threshold = int(self.num_sweeps * 0.1)
        if (sweep - self.last_improvement_sweep) > plateau_threshold:
            # Reheat: reduce beta to increase temperature
            self.current_beta *= self.reheat_factor
            self.current_beta = max(self.current_beta, self.beta_start)
            self.last_improvement_sweep = sweep
            self.reheat_count += 1
            logger.debug(f"Reheat at sweep {sweep}, beta={self.current_beta:.4f}")
        else:
            # Normal geometric cooling
            t = sweep / self.num_sweeps
            self.current_beta = self.beta_start + t * (self.beta_end - self.beta_start)

        return self.current_beta

    def get_tunneling_probability(
        self,
        energy_barrier: float,
        barrier_width: float = 1.0
    ) -> float:
        """
        Compute quantum tunneling probability through energy barrier.

        Based on WKB approximation: P ∝ exp(-2 * barrier_width * sqrt(barrier))

        Args:
            energy_barrier: Height of the energy barrier
            barrier_width: Effective width of the barrier

        Returns:
            Tunneling probability (0 to 1)
        """
        if energy_barrier <= 0:
            return 1.0

        # Quantum tunneling term
        exponent = -barrier_width * math.sqrt(abs(energy_barrier))
        return min(1.0, math.exp(exponent))

    def get_statistics(self) -> dict:
        """Get schedule statistics."""
        return {
            "num_sweeps": self.num_sweeps,
            "final_beta": self.current_beta,
            "best_energy": self.best_energy,
            "reheat_count": self.reheat_count,
            "last_improvement_sweep": self.last_improvement_sweep,
        }


# ============================================================================
# ENERGY LANDSCAPE EXPLORER
# ============================================================================

class EnergyLandscapeExplorer:
    """
    Explores and visualizes the QUBO energy landscape.

    Identifies local minima, barrier heights, and tunneling paths
    for visualization in the holographic hub.
    """

    def __init__(
        self,
        formulation: QUBOTemplateFormulation,
        sample_count: int = 200,
        seed: int | None = None,
    ):
        self.formulation = formulation
        self.sample_count = sample_count
        self.rng = random.Random(seed)
        self.points: list[EnergyLandscapePoint] = []

    def explore(self) -> list[EnergyLandscapePoint]:
        """
        Sample the energy landscape to find local structure.

        Returns:
            List of sampled points with energy and objective values
        """
        Q = self.formulation.Q
        n = self.formulation.num_variables

        if n == 0:
            return []

        # Sample random states
        for i in range(self.sample_count):
            state = {j: self.rng.randint(0, 1) for j in range(n)}
            energy = self._compute_energy(state, Q)
            objectives = self.formulation.compute_objectives(state)

            point = EnergyLandscapePoint(
                state=state.copy(),
                energy=energy,
                objectives=objectives,
            )
            self.points.append(point)

        # Identify local minima by local search
        self._identify_local_minima(Q)

        # Compute tunneling probabilities between minima
        self._compute_tunneling_probabilities()

        # Estimate basin sizes
        self._estimate_basin_sizes(Q)

        return self.points

    def _compute_energy(
        self,
        state: dict[int, int],
        Q: dict[tuple[int, int], float]
    ) -> float:
        """Compute QUBO energy for a state."""
        energy = 0.0
        for (i, j), coef in Q.items():
            if i == j:
                energy += coef * state.get(i, 0)
            else:
                energy += coef * state.get(i, 0) * state.get(j, 0)
        return energy

    def _identify_local_minima(self, Q: dict):
        """Mark points that are local minima."""
        n = self.formulation.num_variables

        for point in self.points:
            is_minimum = True

            # Check all single-bit flips
            for flip_idx in range(min(n, 50)):  # Limit for efficiency
                # Compute energy after flip
                delta = self._compute_delta_energy(point.state, Q, flip_idx)
                if delta < -1e-6:  # Found improvement
                    is_minimum = False
                    break

            point.is_local_minimum = is_minimum

    def _compute_delta_energy(
        self,
        state: dict[int, int],
        Q: dict,
        flip_idx: int
    ) -> float:
        """Compute energy change from flipping one variable."""
        current_val = state.get(flip_idx, 0)
        new_val = 1 - current_val
        delta = new_val - current_val

        energy_change = 0.0

        if (flip_idx, flip_idx) in Q:
            energy_change += Q[(flip_idx, flip_idx)] * delta

        for (i, j), coef in Q.items():
            if i == j:
                continue
            if i == flip_idx:
                energy_change += coef * state.get(j, 0) * delta
            elif j == flip_idx:
                energy_change += coef * state.get(i, 0) * delta

        return energy_change

    def _compute_tunneling_probabilities(self):
        """Compute tunneling probability from each point to best known."""
        minima = [p for p in self.points if p.is_local_minimum]
        if not minima:
            return

        best_minimum = min(minima, key=lambda p: p.energy)

        for point in self.points:
            if point == best_minimum:
                point.tunneling_probability = 1.0
            else:
                barrier = point.energy - best_minimum.energy
                point.tunneling_probability = math.exp(
                    -math.sqrt(max(0, barrier))
                )

    def _estimate_basin_sizes(self, Q: dict):
        """Estimate basin of attraction size for each local minimum."""
        minima = [p for p in self.points if p.is_local_minimum]

        for point in self.points:
            # Count how many non-minima points would descend to this one
            if point.is_local_minimum:
                basin = sum(
                    1 for p in self.points
                    if not p.is_local_minimum and
                    abs(p.energy - point.energy) < 100  # Rough proximity
                )
                point.basin_size = max(1, basin)

    def export_for_visualization(self) -> dict:
        """Export landscape data for holographic hub visualization."""
        minima = [p for p in self.points if p.is_local_minimum]

        return {
            "num_samples": len(self.points),
            "num_local_minima": len(minima),
            "global_minimum_energy": min(p.energy for p in self.points) if self.points else 0,
            "energy_range": {
                "min": min(p.energy for p in self.points) if self.points else 0,
                "max": max(p.energy for p in self.points) if self.points else 0,
            },
            "points": [
                {
                    "energy": p.energy,
                    "is_local_minimum": p.is_local_minimum,
                    "tunneling_probability": p.tunneling_probability,
                    "basin_size": p.basin_size,
                    "objectives": p.objectives,
                }
                for p in sorted(self.points, key=lambda x: x.energy)[:100]
            ],
            "minima": [
                {
                    "energy": m.energy,
                    "basin_size": m.basin_size,
                    "objectives": m.objectives,
                }
                for m in sorted(minima, key=lambda x: x.energy)[:20]
            ],
        }


# ============================================================================
# PARETO FRONT EXPLORER
# ============================================================================

class ParetoFrontExplorer:
    """
    Multi-objective optimization via Pareto front exploration.

    Uses weighted-sum scalarization with adaptive weights to
    discover the Pareto frontier of non-dominated solutions.
    """

    def __init__(
        self,
        formulation: QUBOTemplateFormulation,
        objectives: list[str] | None = None,
        population_size: int = 50,
        generations: int = 100,
        seed: int | None = None,
    ):
        self.formulation = formulation
        self.objectives = objectives or ["coverage", "fairness", "preference"]
        self.population_size = population_size
        self.generations = generations
        self.rng = random.Random(seed)
        self.solutions: list[ParetoSolution] = []
        self.frontier: list[ParetoSolution] = []

    def explore(self) -> list[ParetoSolution]:
        """
        Explore Pareto front using multi-objective optimization.

        Returns:
            List of non-dominated Pareto solutions
        """
        n_objectives = len(self.objectives)

        # Generate diverse weight vectors
        weight_vectors = self._generate_weight_vectors(self.population_size)

        solution_id = 0

        for gen in range(self.generations):
            for weights in weight_vectors:
                # Create weighted objective
                weight_dict = {
                    obj: w for obj, w in zip(self.objectives, weights)
                }

                # Solve with these weights
                Q = self.formulation.build(weight_dict)

                # Quick simulated annealing
                sample, energy = self._quick_anneal(Q, num_sweeps=100)

                # Compute individual objectives
                objectives = self.formulation.compute_objectives(sample)
                assignments = self.formulation.decode_solution(sample)

                solution = ParetoSolution(
                    solution_id=solution_id,
                    state=sample,
                    objectives={
                        obj: objectives.get(obj, 0.0) for obj in self.objectives
                    },
                    assignments=assignments,
                )
                self.solutions.append(solution)
                solution_id += 1

            # Prune dominated solutions periodically
            if gen % 10 == 0:
                self._compute_pareto_ranks()
                # Keep only non-dominated and slightly dominated
                self.solutions = [s for s in self.solutions if s.rank <= 2]

        # Final ranking
        self._compute_pareto_ranks()
        self._compute_crowding_distances()

        # Extract frontier
        self.frontier = [s for s in self.solutions if s.rank == 0]

        logger.info(
            f"Pareto exploration: {len(self.frontier)} frontier solutions "
            f"from {solution_id} total evaluations"
        )

        return self.frontier

    def _generate_weight_vectors(self, n: int) -> list[list[float]]:
        """Generate diverse weight vectors for objectives."""
        n_objectives = len(self.objectives)
        vectors = []

        # Uniform grid on simplex
        for i in range(n):
            weights = [self.rng.random() for _ in range(n_objectives)]
            total = sum(weights)
            weights = [w / total for w in weights]
            vectors.append(weights)

        # Add extreme weights (single objective)
        for i in range(n_objectives):
            weights = [0.1] * n_objectives
            weights[i] = 0.9
            vectors.append(weights)

        return vectors

    def _quick_anneal(
        self,
        Q: dict,
        num_sweeps: int = 100
    ) -> tuple[dict[int, int], float]:
        """Quick simulated annealing for single solution."""
        n = self.formulation.num_variables
        if n == 0:
            return {}, 0.0

        sample = {i: self.rng.randint(0, 1) for i in range(n)}
        energy = self._compute_energy(sample, Q)

        best_sample = sample.copy()
        best_energy = energy

        for sweep in range(num_sweeps):
            beta = 0.1 + (4.0 * sweep / num_sweeps)

            for _ in range(min(n, 100)):
                i = self.rng.randint(0, n - 1)
                delta = self._compute_delta_energy(sample, Q, i)

                if delta <= 0 or self.rng.random() < math.exp(-beta * delta):
                    sample[i] = 1 - sample[i]
                    energy += delta

                    if energy < best_energy:
                        best_sample = sample.copy()
                        best_energy = energy

        return best_sample, best_energy

    def _compute_energy(self, sample: dict, Q: dict) -> float:
        """Compute QUBO energy."""
        energy = 0.0
        for (i, j), coef in Q.items():
            if i == j:
                energy += coef * sample.get(i, 0)
            else:
                energy += coef * sample.get(i, 0) * sample.get(j, 0)
        return energy

    def _compute_delta_energy(self, sample: dict, Q: dict, flip_idx: int) -> float:
        """Compute energy change from flipping variable."""
        delta = (1 - sample.get(flip_idx, 0)) - sample.get(flip_idx, 0)
        change = 0.0

        if (flip_idx, flip_idx) in Q:
            change += Q[(flip_idx, flip_idx)] * delta

        for (i, j), coef in Q.items():
            if i != j:
                if i == flip_idx:
                    change += coef * sample.get(j, 0) * delta
                elif j == flip_idx:
                    change += coef * sample.get(i, 0) * delta

        return change

    def _compute_pareto_ranks(self):
        """Compute Pareto rank for each solution."""
        for sol in self.solutions:
            sol.rank = 0

        remaining = list(self.solutions)
        rank = 0

        while remaining:
            non_dominated = []

            for sol in remaining:
                is_dominated = False
                for other in remaining:
                    if other != sol and other.dominates(sol):
                        is_dominated = True
                        break

                if not is_dominated:
                    non_dominated.append(sol)

            for sol in non_dominated:
                sol.rank = rank
                remaining.remove(sol)

            rank += 1

            if rank > 100:  # Safety limit
                break

    def _compute_crowding_distances(self):
        """Compute crowding distance for diversity."""
        frontier = [s for s in self.solutions if s.rank == 0]

        if len(frontier) <= 2:
            for sol in frontier:
                sol.crowding_distance = float('inf')
            return

        for obj in self.objectives:
            # Sort by objective
            frontier.sort(key=lambda s: s.objectives.get(obj, 0))

            # Boundary solutions get infinite distance
            frontier[0].crowding_distance = float('inf')
            frontier[-1].crowding_distance = float('inf')

            # Interior solutions
            obj_range = (
                frontier[-1].objectives.get(obj, 0) -
                frontier[0].objectives.get(obj, 0)
            )

            if obj_range > 0:
                for i in range(1, len(frontier) - 1):
                    diff = (
                        frontier[i + 1].objectives.get(obj, 0) -
                        frontier[i - 1].objectives.get(obj, 0)
                    )
                    frontier[i].crowding_distance += diff / obj_range

    def export_for_visualization(self) -> dict:
        """Export Pareto front for holographic hub visualization."""
        return {
            "num_frontier_solutions": len(self.frontier),
            "total_evaluations": len(self.solutions),
            "objectives": self.objectives,
            "frontier": [
                {
                    "solution_id": s.solution_id,
                    "objectives": s.objectives,
                    "crowding_distance": s.crowding_distance,
                    "num_assignments": len(s.assignments),
                }
                for s in sorted(self.frontier, key=lambda x: x.crowding_distance, reverse=True)
            ],
            "hypervolume_estimate": self._estimate_hypervolume(),
        }

    def _estimate_hypervolume(self) -> float:
        """Estimate hypervolume indicator of Pareto front."""
        if not self.frontier or not self.objectives:
            return 0.0

        # Simple 2D hypervolume for first two objectives
        if len(self.objectives) < 2:
            return 0.0

        obj1, obj2 = self.objectives[:2]
        points = [
            (s.objectives.get(obj1, 0), s.objectives.get(obj2, 0))
            for s in self.frontier
        ]

        # Sort by first objective
        points.sort()

        # Reference point (nadir)
        ref = (
            max(p[0] for p in points) + 1,
            max(p[1] for p in points) + 1,
        )

        # Compute hypervolume
        hv = 0.0
        prev_y = ref[1]

        for x, y in points:
            hv += (ref[0] - x) * (prev_y - y)
            prev_y = min(prev_y, y)

        return abs(hv)


# ============================================================================
# HYBRID CLASSICAL-QUANTUM PIPELINE
# ============================================================================

class HybridTemplatePipeline:
    """
    Hybrid classical-quantum pipeline for template optimization.

    Pipeline:
    1. QUBO for coarse template assignment (quantum-amenable)
    2. Gradient descent for fine-tuning (classical optimization)
    3. Local search for constraint repair (classical)
    """

    def __init__(
        self,
        context: SchedulingContext,
        config: TemplateSelectionConfig | None = None,
    ):
        self.context = context
        self.config = config or TemplateSelectionConfig()
        self.formulation: QUBOTemplateFormulation | None = None

        # Pipeline stage results
        self.qubo_result: dict | None = None
        self.refinement_result: dict | None = None
        self.repair_result: dict | None = None

    def run(self) -> TemplateSelectionResult:
        """
        Run the full hybrid pipeline.

        Returns:
            TemplateSelectionResult with optimized schedule
        """
        start_time = time.time()

        # Stage 1: QUBO coarse optimization
        logger.info("Pipeline Stage 1: QUBO template selection")
        self.formulation = QUBOTemplateFormulation(self.context, self.config)
        Q = self.formulation.build()

        if self.formulation.num_variables == 0:
            return TemplateSelectionResult(
                success=False,
                assignments=[],
                pareto_frontier=[],
                energy_landscape=[],
                statistics={"error": "No variables to optimize"},
                runtime_seconds=time.time() - start_time,
            )

        # Run quantum-inspired annealing with adaptive temperature
        sample, energy = self._run_adaptive_annealing(Q)

        self.qubo_result = {
            "sample": sample,
            "energy": energy,
            "assignments": self.formulation.decode_solution(sample),
        }

        # Stage 2: Classical refinement (gradient-like descent)
        logger.info("Pipeline Stage 2: Classical refinement")
        refined_sample, refined_energy = self._classical_refinement(
            sample, energy, Q
        )

        self.refinement_result = {
            "sample": refined_sample,
            "energy": refined_energy,
            "improvement": energy - refined_energy,
        }

        # Stage 3: Constraint repair
        logger.info("Pipeline Stage 3: Constraint repair")
        repaired_sample = self._constraint_repair(refined_sample, Q)
        repaired_energy = self._compute_energy(repaired_sample, Q)

        self.repair_result = {
            "sample": repaired_sample,
            "energy": repaired_energy,
        }

        # Decode final solution
        final_assignments = self.formulation.decode_solution(repaired_sample)
        final_objectives = self.formulation.compute_objectives(repaired_sample)

        # Explore Pareto front
        logger.info("Pipeline: Pareto front exploration")
        pareto_explorer = ParetoFrontExplorer(
            self.formulation,
            population_size=self.config.pareto_population,
            generations=min(self.config.pareto_generations, 20),
            seed=self.config.seed,
        )
        pareto_frontier = pareto_explorer.explore()

        # Explore energy landscape
        logger.info("Pipeline: Energy landscape exploration")
        landscape_explorer = EnergyLandscapeExplorer(
            self.formulation,
            sample_count=100,
            seed=self.config.seed,
        )
        energy_landscape = landscape_explorer.explore()

        runtime = time.time() - start_time

        # Find recommended solution from Pareto front
        recommended_id = None
        if pareto_frontier:
            # Recommend solution with best coverage
            best = min(
                pareto_frontier,
                key=lambda s: s.objectives.get("coverage", 0)
            )
            recommended_id = best.solution_id

        return TemplateSelectionResult(
            success=True,
            assignments=final_assignments,
            pareto_frontier=pareto_frontier,
            energy_landscape=energy_landscape,
            statistics={
                "num_variables": self.formulation.num_variables,
                "num_qubo_terms": len(Q),
                "qubo_energy": energy,
                "refined_energy": refined_energy,
                "final_energy": repaired_energy,
                "improvement": energy - repaired_energy,
                "num_assignments": len(final_assignments),
                "objectives": final_objectives,
                "pareto_frontier_size": len(pareto_frontier),
                "num_local_minima": sum(1 for p in energy_landscape if p.is_local_minimum),
            },
            runtime_seconds=runtime,
            recommended_solution_id=recommended_id,
        )

    def _run_adaptive_annealing(
        self,
        Q: dict,
    ) -> tuple[dict[int, int], float]:
        """Run simulated annealing with adaptive temperature."""
        n = self.formulation.num_variables
        rng = random.Random(self.config.seed)

        schedule = AdaptiveTemperatureSchedule(
            beta_start=self.config.beta_start,
            beta_end=self.config.beta_end,
            num_sweeps=self.config.num_sweeps,
            reheat_threshold=self.config.reheat_threshold,
            reheat_factor=self.config.reheat_factor,
        )

        best_sample = dict.fromkeys(range(n), 0)
        best_energy = self._compute_energy(best_sample, Q)

        for read in range(self.config.num_reads):
            sample = {i: rng.randint(0, 1) for i in range(n)}
            energy = self._compute_energy(sample, Q)

            for sweep in range(self.config.num_sweeps):
                beta = schedule.get_beta(sweep, energy)

                for i in range(n):
                    delta = self._compute_delta_energy(sample, Q, i)

                    if delta <= 0:
                        accept = True
                    else:
                        classical_prob = math.exp(-beta * delta)
                        tunnel_prob = schedule.get_tunneling_probability(delta)
                        accept = rng.random() < max(classical_prob, tunnel_prob * 0.1)

                    if accept:
                        sample[i] = 1 - sample[i]
                        energy += delta

                if energy < best_energy:
                    best_sample = sample.copy()
                    best_energy = energy

        return best_sample, best_energy

    def _classical_refinement(
        self,
        sample: dict[int, int],
        energy: float,
        Q: dict,
    ) -> tuple[dict[int, int], float]:
        """Classical gradient-like descent for refinement."""
        n = self.formulation.num_variables
        current = sample.copy()
        current_energy = energy

        improved = True
        max_iterations = 1000
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            # Try each variable flip
            for i in range(n):
                delta = self._compute_delta_energy(current, Q, i)

                if delta < -1e-6:  # Improvement found
                    current[i] = 1 - current[i]
                    current_energy += delta
                    improved = True

        return current, current_energy

    def _constraint_repair(
        self,
        sample: dict[int, int],
        Q: dict,
    ) -> dict[int, int]:
        """Repair constraint violations."""
        repaired = sample.copy()
        n_periods = len(self.formulation.rotation_periods)
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        # Ensure exactly one template per resident per period
        for r_i in range(len(self.context.residents)):
            for p_i in range(n_periods):
                period_vars = []
                for t_i in range(len(valid_templates)):
                    if (r_i, p_i, t_i) in self.formulation.var_index:
                        idx = self.formulation.var_index[(r_i, p_i, t_i)]
                        period_vars.append((idx, t_i))

                # Count assigned
                assigned = [idx for idx, t_i in period_vars if repaired.get(idx, 0) == 1]

                if len(assigned) == 0:
                    # Assign first available template
                    if period_vars:
                        repaired[period_vars[0][0]] = 1
                elif len(assigned) > 1:
                    # Keep first, unassign rest
                    for idx in assigned[1:]:
                        repaired[idx] = 0

        return repaired

    def _compute_energy(self, sample: dict, Q: dict) -> float:
        """Compute QUBO energy."""
        energy = 0.0
        for (i, j), coef in Q.items():
            if i == j:
                energy += coef * sample.get(i, 0)
            else:
                energy += coef * sample.get(i, 0) * sample.get(j, 0)
        return energy

    def _compute_delta_energy(self, sample: dict, Q: dict, flip_idx: int) -> float:
        """Compute energy change from flip."""
        delta = (1 - sample.get(flip_idx, 0)) - sample.get(flip_idx, 0)
        change = 0.0

        if (flip_idx, flip_idx) in Q:
            change += Q[(flip_idx, flip_idx)] * delta

        for (i, j), coef in Q.items():
            if i != j:
                if i == flip_idx:
                    change += coef * sample.get(j, 0) * delta
                elif j == flip_idx:
                    change += coef * sample.get(i, 0) * delta

        return change


# ============================================================================
# MAIN SOLVER CLASS
# ============================================================================

class QUBOTemplateSolver(BaseSolver):
    """
    QUBO-based solver for rotation template selection.

    Provides the full pipeline:
    1. QUBO formulation with fairness objectives
    2. Pareto front exploration
    3. Hybrid classical-quantum optimization
    4. Energy landscape visualization
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 120.0,
        config: TemplateSelectionConfig | None = None,
    ):
        super().__init__(constraint_manager, timeout_seconds)
        self.config = config or TemplateSelectionConfig()

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """
        Solve template selection using QUBO.

        Args:
            context: Scheduling context
            existing_assignments: Existing assignments to preserve

        Returns:
            SolverResult with optimized schedule
        """
        start_time = time.time()

        # Run hybrid pipeline
        pipeline = HybridTemplatePipeline(context, self.config)
        result = pipeline.run()

        runtime = time.time() - start_time

        if not result.success:
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status="QUBO template selection failed",
                runtime_seconds=runtime,
            )

        return SolverResult(
            success=True,
            assignments=result.assignments,
            status="feasible",
            objective_value=-result.statistics.get("final_energy", 0),
            runtime_seconds=runtime,
            solver_status="qubo_template_selector",
            random_seed=self.config.seed,
            statistics={
                **result.statistics,
                "pareto_frontier_size": len(result.pareto_frontier),
                "recommended_solution_id": result.recommended_solution_id,
            },
        )

    def solve_with_full_result(
        self,
        context: SchedulingContext,
    ) -> TemplateSelectionResult:
        """
        Solve and return full result with Pareto front and energy landscape.

        Args:
            context: Scheduling context

        Returns:
            TemplateSelectionResult with full optimization data
        """
        pipeline = HybridTemplatePipeline(context, self.config)
        return pipeline.run()


# ============================================================================
# BENCHMARKING
# ============================================================================

class TemplateBenchmark:
    """Benchmark QUBO template selection vs classical approaches."""

    def __init__(self, context: SchedulingContext):
        self.context = context
        self.results: dict[str, dict] = {}

    def run_benchmark(self) -> dict:
        """
        Run comparative benchmark.

        Returns:
            Dict with benchmark results for each approach
        """
        # QUBO approach
        qubo_start = time.time()
        qubo_solver = QUBOTemplateSolver(
            config=TemplateSelectionConfig(
                num_reads=50,
                num_sweeps=500,
            )
        )
        qubo_result = qubo_solver.solve(self.context)
        qubo_time = time.time() - qubo_start

        self.results["qubo"] = {
            "success": qubo_result.success,
            "num_assignments": len(qubo_result.assignments),
            "objective_value": qubo_result.objective_value,
            "runtime_seconds": qubo_time,
            "statistics": qubo_result.statistics,
        }

        # Classical greedy approach
        greedy_start = time.time()
        greedy_assignments = self._greedy_assignment()
        greedy_time = time.time() - greedy_start

        self.results["greedy"] = {
            "success": len(greedy_assignments) > 0,
            "num_assignments": len(greedy_assignments),
            "runtime_seconds": greedy_time,
        }

        # Random baseline
        random_start = time.time()
        random_assignments = self._random_assignment()
        random_time = time.time() - random_start

        self.results["random"] = {
            "success": len(random_assignments) > 0,
            "num_assignments": len(random_assignments),
            "runtime_seconds": random_time,
        }

        # Compute improvement metrics
        qubo_coverage = len(qubo_result.assignments)
        greedy_coverage = len(greedy_assignments)
        random_coverage = len(random_assignments)

        self.results["comparison"] = {
            "qubo_vs_greedy_improvement": (
                (qubo_coverage - greedy_coverage) / max(greedy_coverage, 1) * 100
            ),
            "qubo_vs_random_improvement": (
                (qubo_coverage - random_coverage) / max(random_coverage, 1) * 100
            ),
            "qubo_speedup_vs_exhaustive": "N/A (exhaustive infeasible)",
        }

        return self.results

    def _greedy_assignment(self) -> list[tuple]:
        """Simple greedy template assignment."""
        assignments = []
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        if not valid_templates:
            return assignments

        for resident in self.context.residents:
            for block in self.context.blocks:
                if not block.is_weekend:
                    # Assign first available template
                    template = valid_templates[0]
                    assignments.append((resident.id, block.id, template.id))

        return assignments

    def _random_assignment(self) -> list[tuple]:
        """Random template assignment baseline."""
        assignments = []
        valid_templates = [
            t for t in self.context.templates
            if not t.requires_procedure_credential
        ]

        if not valid_templates:
            return assignments

        rng = random.Random(42)

        for resident in self.context.residents:
            for block in self.context.blocks:
                if not block.is_weekend:
                    template = rng.choice(valid_templates)
                    assignments.append((resident.id, block.id, template.id))

        return assignments

    def export_results(self) -> dict:
        """Export benchmark results for analysis."""
        return {
            "benchmark_results": self.results,
            "context_summary": {
                "num_residents": len(self.context.residents),
                "num_blocks": len(self.context.blocks),
                "num_templates": len(self.context.templates),
            },
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_template_selector_status() -> dict[str, Any]:
    """Get status of QUBO template selector capabilities."""
    return {
        "qubo_template_selector_available": True,
        "features": {
            "fairness_objectives": True,
            "pareto_exploration": True,
            "adaptive_temperature": True,
            "energy_landscape_visualization": True,
            "hybrid_pipeline": True,
        },
        "recommended_problem_size": {
            "min_variables": 50,
            "optimal_variables": 780,
            "max_variables": 5000,
        },
    }
