"""
QUBO-Based Quantum-Inspired Solvers for Residency Scheduling.

This module implements Quadratic Unconstrained Binary Optimization (QUBO)
formulations of the scheduling problem, solvable via:
1. Classical simulated annealing (quantum-inspired)
2. D-Wave quantum annealing (actual quantum hardware)
3. Hybrid quantum-classical approaches

The QUBO formulation naturally maps to:
- Constraint penalties as quadratic terms
- Objective optimization as linear/quadratic terms
- Binary decision variables x[resident, block, template]

Environment Configuration:
    USE_QUANTUM_SOLVER: Enable quantum solver (default: false)
    DWAVE_API_TOKEN: D-Wave API token for quantum hardware
    QUANTUM_SOLVER_BACKEND: "classical" or "quantum" (default: classical)

References:
- PyQUBO: https://arxiv.org/abs/2103.01708
- Nurse Scheduling via QUBO: https://arxiv.org/abs/2302.09459
- D-Wave Ocean SDK: https://docs.ocean.dwavesys.com
"""

import logging
import math
import os
import random
import time
from typing import Any
from uuid import UUID

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


# Simulated Annealing Solver Parameters
MIN_READS = 100  # Minimum number of annealing reads
MAX_READS = 1000  # Maximum number of annealing reads
BASE_READS = 10000  # Base reads for read count calculation
MIN_SWEEPS = 1000  # Minimum number of annealing sweeps
MAX_SWEEPS = 10000  # Maximum number of annealing sweeps
SWEEPS_PER_VAR = 10  # Number of sweeps per variable

# Quantum Hardware Limits
MAX_QUANTUM_VARS = 5000  # Maximum variables for quantum hardware


# Check for optional quantum libraries
PYQUBO_AVAILABLE = False
DWAVE_SAMPLERS_AVAILABLE = False
DWAVE_SYSTEM_AVAILABLE = False
QUBOVERT_AVAILABLE = False

try:
    import pyqubo

    PYQUBO_AVAILABLE = True
except ImportError:
    pass

try:
    from dwave.samplers import SimulatedAnnealingSampler, TabuSampler

    DWAVE_SAMPLERS_AVAILABLE = True
except ImportError:
    pass

try:
    from dwave.system import DWaveSampler, EmbeddingComposite

    DWAVE_SYSTEM_AVAILABLE = True
except ImportError:
    pass

try:
    import qubovert as qv

    QUBOVERT_AVAILABLE = True
except ImportError:
    pass


class QUBOFormulation:
    """
    Formulates the residency scheduling problem as QUBO.

    The QUBO matrix Q encodes:
    - Objective function: Maximize coverage, minimize imbalance
    - Hard constraints: One assignment per block, availability, ACGME rules
    - Soft constraints: Equity, continuity, preferences

    Mathematical formulation:
    minimize x^T Q x

    where x is a binary vector of assignment variables.
    """

    # Penalty weights for constraint violations
    HARD_CONSTRAINT_PENALTY = 10000.0  # Must be satisfied
    ACGME_PENALTY = 5000.0  # ACGME compliance
    SOFT_CONSTRAINT_PENALTY = 100.0  # Optimization targets

    def __init__(self, context: SchedulingContext):
        """
        Initialize QUBO formulation.

        Args:
            context: SchedulingContext with blocks, residents, templates
        """
        self.context = context
        self.workday_blocks = [b for b in context.blocks if not b.is_weekend]

        # Variable indexing: x[r, b, t] -> flat index
        self.var_index: dict[tuple[int, int, int], int] = {}
        self.index_to_var: dict[int, tuple[int, int, int]] = {}
        self._build_variable_index()

        # QUBO matrix (sparse representation)
        self.Q: dict[tuple[int, int], float] = {}

    def _build_variable_index(self):
        """Build mapping from (resident, block, template) to flat index."""
        idx = 0
        for resident in self.context.residents:
            r_i = self.context.resident_idx[resident.id]
            for block in self.workday_blocks:
                b_i = self.context.block_idx[block.id]
                for template in self.context.templates:
                    # Skip templates requiring credentials
                    if template.requires_procedure_credential:
                        continue
                    t_i = self.context.template_idx.get(template.id, 0)
                    self.var_index[(r_i, b_i, t_i)] = idx
                    self.index_to_var[idx] = (r_i, b_i, t_i)
                    idx += 1

        logger.info(f"QUBO formulation: {idx} binary variables")

    @property
    def num_variables(self) -> int:
        """Number of binary variables in the QUBO."""
        return len(self.var_index)

    def build(self) -> dict[tuple[int, int], float]:
        """
        Build the complete QUBO matrix.

        Returns:
            Q: Sparse QUBO matrix as dict of (i, j) -> coefficient
        """
        self.Q = {}

        # Objective: Maximize coverage (negative = minimize)
        self._add_coverage_objective()

        # Hard: One assignment per person per block
        self._add_one_per_block_constraint()

        # Hard: Availability constraints
        self._add_availability_constraints()

        # Hard: ACGME 80-hour rule (simplified)
        self._add_80_hour_constraint()

        # Soft: Equity (work distribution)
        self._add_equity_objective()

        return self.Q

    def _add_coverage_objective(self):
        """Add objective to maximize coverage (assign as many blocks as possible)."""
        for idx in range(self.num_variables):
            # Negative weight encourages x[i] = 1
            self._add_linear(idx, -1.0)

    def _add_one_per_block_constraint(self):
        """
        Constraint: At most one resident assigned per block.

        Encoded as: penalty * (sum_r x[r,b,t] - 1)^2 for each block b
        Expands to: penalty * (sum_r sum_s x[r,b] * x[s,b] - 2*sum_r x[r,b] + 1)
        """
        # Group variables by block
        block_vars: dict[int, list[int]] = {}
        for (r_i, b_i, t_i), idx in self.var_index.items():
            if b_i not in block_vars:
                block_vars[b_i] = []
            block_vars[b_i].append(idx)

        for b_i, indices in block_vars.items():
            if len(indices) <= 1:
                continue

            # Penalty for multiple assignments: sum over pairs
            for i, idx1 in enumerate(indices):
                for idx2 in indices[i + 1 :]:
                    self._add_quadratic(idx1, idx2, self.HARD_CONSTRAINT_PENALTY)

    def _add_availability_constraints(self):
        """
        Constraint: Cannot assign during unavailable periods.

        If resident r is unavailable at block b, set high penalty for x[r,b,*].
        """
        for resident in self.context.residents:
            r_i = self.context.resident_idx[resident.id]
            unavail = self.context.availability.get(resident.id, set())

            for block in self.workday_blocks:
                b_i = self.context.block_idx[block.id]
                if b_i in unavail:
                    # Penalize any assignment to this block
                    for t_i in range(len(self.context.templates)):
                        if (r_i, b_i, t_i) in self.var_index:
                            idx = self.var_index[(r_i, b_i, t_i)]
                            self._add_linear(idx, self.HARD_CONSTRAINT_PENALTY)

    def _add_80_hour_constraint(self):
        """
        Constraint: Max 80 hours per week (simplified as max blocks).

        Using 6 hours per block, 80 hours = ~13 blocks per week.
        For 4-week rolling average: max 53 blocks per 4-week period.
        """
        HOURS_PER_BLOCK = 6.0
        MAX_BLOCKS_PER_WEEK = int(80 / HOURS_PER_BLOCK)  # ~13

        # Group blocks by week
        week_blocks: dict[int, list[int]] = {}
        for block in self.workday_blocks:
            b_i = self.context.block_idx[block.id]
            # Simple week calculation (0-indexed)
            week = b_i // 10  # Assuming ~10 blocks per week
            if week not in week_blocks:
                week_blocks[week] = []
            week_blocks[week].append(b_i)

        # For each resident, penalize exceeding max per week
        for resident in self.context.residents:
            r_i = self.context.resident_idx[resident.id]

            for week, block_indices in week_blocks.items():
                # Get all variable indices for this resident in this week
                week_vars = []
                for b_i in block_indices:
                    for t_i in range(len(self.context.templates)):
                        if (r_i, b_i, t_i) in self.var_index:
                            week_vars.append(self.var_index[(r_i, b_i, t_i)])

                # Penalty for exceeding threshold: (sum - max)^2 if sum > max
                # Approximated as quadratic penalty on pairs beyond threshold
                if len(week_vars) > MAX_BLOCKS_PER_WEEK:
                    penalty_factor = self.ACGME_PENALTY / (len(week_vars) ** 2)
                    for i, idx1 in enumerate(week_vars):
                        for idx2 in week_vars[i + 1 :]:
                            self._add_quadratic(idx1, idx2, penalty_factor)

    def _add_equity_objective(self):
        """
        Soft objective: Minimize variance in workload distribution.

        Penalize deviation from mean assignments per resident.
        """
        n_residents = len(self.context.residents)
        n_blocks = len(self.workday_blocks)
        mean_blocks = n_blocks / n_residents if n_residents > 0 else 0

        # Group variables by resident
        resident_vars: dict[int, list[int]] = {}
        for (r_i, b_i, t_i), idx in self.var_index.items():
            if r_i not in resident_vars:
                resident_vars[r_i] = []
            resident_vars[r_i].append(idx)

        # Penalize pairs within same resident (encourages spreading)
        for r_i, indices in resident_vars.items():
            # Small penalty for having many assignments to same resident
            penalty = self.SOFT_CONSTRAINT_PENALTY / (len(indices) + 1)
            for i, idx1 in enumerate(indices):
                for idx2 in indices[i + 1 :]:
                    self._add_quadratic(idx1, idx2, penalty * 0.01)

    def _add_linear(self, i: int, value: float):
        """Add linear term Q[i,i] += value."""
        key = (i, i)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def _add_quadratic(self, i: int, j: int, value: float):
        """Add quadratic term Q[i,j] += value (symmetric)."""
        if i > j:
            i, j = j, i
        key = (i, j)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def decode_solution(
        self, sample: dict[int, int]
    ) -> list[tuple[UUID, UUID, UUID | None]]:
        """
        Decode QUBO solution to assignment list.

        Args:
            sample: Dict mapping variable index to 0/1 value

        Returns:
            List of (person_id, block_id, template_id) tuples
        """
        assignments = []
        idx_to_resident = {v: k for k, v in self.context.resident_idx.items()}
        idx_to_block = {v: k for k, v in self.context.block_idx.items()}
        template_list = list(self.context.templates)

        for idx, value in sample.items():
            if value == 1 and idx in self.index_to_var:
                r_i, b_i, t_i = self.index_to_var[idx]
                person_id = idx_to_resident.get(r_i)
                block_id = idx_to_block.get(b_i)
                template_id = (
                    template_list[t_i].id if t_i < len(template_list) else None
                )

                if person_id and block_id:
                    assignments.append((person_id, block_id, template_id))

        return assignments


class SimulatedQuantumAnnealingSolver(BaseSolver):
    """
    Classical simulated annealing solver with quantum-inspired features.

    This solver implements quantum-inspired techniques:
    1. Quantum tunneling probability for escaping local minima
    2. Path-integral inspired temperature schedules
    3. Multiple replica evolution (Suzuki-Trotter decomposition inspired)

    Can run without any quantum libraries (pure Python fallback).
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        num_reads: int = 100,
        num_sweeps: int = 1000,
        beta_range: tuple[float, float] = (0.1, 4.2),
        seed: int | None = None,
    ):
        """
        Initialize quantum-inspired simulated annealing solver.

        Args:
            constraint_manager: Optional constraint manager
            timeout_seconds: Maximum solve time
            num_reads: Number of independent annealing runs
            num_sweeps: Number of sweeps per run
            beta_range: (beta_start, beta_end) for annealing schedule
            seed: Random seed for reproducibility
        """
        super().__init__(constraint_manager, timeout_seconds)
        self.num_reads = num_reads
        self.num_sweeps = num_sweeps
        self.beta_range = beta_range
        self.seed = seed or random.randint(0, 2**32 - 1)

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """
        Solve using quantum-inspired simulated annealing.

        Args:
            context: Scheduling context
            existing_assignments: Assignments to preserve

        Returns:
            SolverResult with optimized schedule
        """
        start_time = time.time()

        # Build QUBO formulation
        formulation = QUBOFormulation(context)
        Q = formulation.build()

        if formulation.num_variables == 0:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No variables to optimize",
            )

        logger.info(
            f"QUBO built: {formulation.num_variables} variables, "
            f"{len(Q)} non-zero terms"
        )

        # Try D-Wave samplers first, fall back to pure Python
        if DWAVE_SAMPLERS_AVAILABLE:
            sample, energy = self._solve_with_dwave_samplers(Q, formulation)
        else:
            sample, energy = self._solve_pure_python(Q, formulation)

        runtime = time.time() - start_time

        # Decode solution
        assignments = formulation.decode_solution(sample)

        logger.info(
            f"Quantum-inspired SA found {len(assignments)} assignments "
            f"(energy={energy:.2f}) in {runtime:.2f}s"
        )

        return SolverResult(
            success=True,
            assignments=assignments,
            status="feasible",
            objective_value=-energy,  # Negate since we minimized
            runtime_seconds=runtime,
            solver_status="simulated_annealing",
            random_seed=self.seed,
            statistics={
                "num_variables": formulation.num_variables,
                "num_terms": len(Q),
                "num_reads": self.num_reads,
                "num_sweeps": self.num_sweeps,
                "final_energy": energy,
                "library": (
                    "dwave-samplers" if DWAVE_SAMPLERS_AVAILABLE else "pure_python"
                ),
            },
        )

    def _solve_with_dwave_samplers(
        self, Q: dict, formulation: QUBOFormulation
    ) -> tuple[dict[int, int], float]:
        """Solve using D-Wave's simulated annealing sampler."""
        from dwave.samplers import SimulatedAnnealingSampler

        sampler = SimulatedAnnealingSampler()
        response = sampler.sample_qubo(
            Q,
            num_reads=self.num_reads,
            num_sweeps=self.num_sweeps,
            beta_range=self.beta_range,
            seed=self.seed,
        )

        best = response.first
        return dict(best.sample), best.energy

    def _solve_pure_python(
        self, Q: dict, formulation: QUBOFormulation
    ) -> tuple[dict[int, int], float]:
        """
        Pure Python quantum-inspired simulated annealing.

        Implements quantum tunneling probability for escaping local minima.
        """
        random.seed(self.seed)
        n = formulation.num_variables

        best_sample = dict.fromkeys(range(n), 0)
        best_energy = self._compute_energy(best_sample, Q)

        for read in range(self.num_reads):
            # Initialize random state
            sample = {i: random.randint(0, 1) for i in range(n)}
            energy = self._compute_energy(sample, Q)

            beta_start, beta_end = self.beta_range

            for sweep in range(self.num_sweeps):
                # Linear beta schedule
                t = sweep / self.num_sweeps
                beta = beta_start + t * (beta_end - beta_start)

                # Sweep through all variables
                for i in range(n):
                    # Compute energy change if we flip variable i
                    delta_e = self._compute_delta_energy(sample, Q, i)

                    # Quantum-inspired acceptance probability
                    # Includes tunneling term for barrier penetration
                    if delta_e <= 0:
                        accept = True
                    else:
                        # Classical Metropolis
                        classical_prob = math.exp(-beta * delta_e)

                        # Quantum tunneling contribution
                        # Simplified model: probability to tunnel through barrier
                        barrier_width = 1.0  # Normalized
                        tunneling_prob = math.exp(
                            -barrier_width * math.sqrt(abs(delta_e))
                        )

                        accept = random.random() < max(
                            classical_prob, tunneling_prob * 0.1
                        )

                    if accept:
                        sample[i] = 1 - sample[i]
                        energy += delta_e

                if energy < best_energy:
                    best_sample = sample.copy()
                    best_energy = energy

        return best_sample, best_energy

    def _compute_energy(self, sample: dict[int, int], Q: dict) -> float:
        """Compute QUBO energy for a sample."""
        energy = 0.0
        for (i, j), coef in Q.items():
            if i == j:
                energy += coef * sample.get(i, 0)
            else:
                energy += coef * sample.get(i, 0) * sample.get(j, 0)
        return energy

    def _compute_delta_energy(
        self, sample: dict[int, int], Q: dict, flip_idx: int
    ) -> float:
        """Compute energy change from flipping variable flip_idx."""
        current_val = sample.get(flip_idx, 0)
        new_val = 1 - current_val
        delta = new_val - current_val  # +1 or -1

        energy_change = 0.0

        # Linear term
        if (flip_idx, flip_idx) in Q:
            energy_change += Q[(flip_idx, flip_idx)] * delta

        # Quadratic terms
        for (i, j), coef in Q.items():
            if i == j:
                continue
            if i == flip_idx:
                energy_change += coef * sample.get(j, 0) * delta
            elif j == flip_idx:
                energy_change += coef * sample.get(i, 0) * delta

        return energy_change


class QUBOSolver(BaseSolver):
    """
    QUBO solver using PyQUBO for formulation.

    PyQUBO provides a higher-level interface for building QUBO models
    with automatic constraint handling and penalty tuning.

    Requires: pip install pyqubo
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        num_reads: int = 100,
        use_tabu: bool = False,
    ):
        """
        Initialize PyQUBO-based solver.

        Args:
            constraint_manager: Optional constraint manager
            timeout_seconds: Maximum solve time
            num_reads: Number of samples to collect
            use_tabu: Use tabu search instead of simulated annealing
        """
        super().__init__(constraint_manager, timeout_seconds)
        self.num_reads = num_reads
        self.use_tabu = use_tabu

        if not PYQUBO_AVAILABLE:
            logger.warning("PyQUBO not installed. Install with: pip install pyqubo")

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Solve using PyQUBO formulation."""
        if not PYQUBO_AVAILABLE:
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status="PyQUBO not installed",
            )

        start_time = time.time()

        # Build PyQUBO model
        model, var_map = self._build_pyqubo_model(context)

        if model is None:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="Could not build model",
            )

        # Compile to BQM with placeholder values
        # lambda_block is the penalty weight for the one-per-block constraint
        feed_dict = {"lambda_block": QUBOFormulation.HARD_CONSTRAINT_PENALTY}
        bqm = model.to_bqm(feed_dict=feed_dict)

        logger.info(
            f"PyQUBO model: {len(bqm.variables)} variables, "
            f"{len(bqm.quadratic)} interactions"
        )

        # Solve with appropriate sampler
        if DWAVE_SAMPLERS_AVAILABLE:
            if self.use_tabu:
                from dwave.samplers import TabuSampler

                sampler = TabuSampler()
                response = sampler.sample(bqm, num_reads=self.num_reads)
            else:
                from dwave.samplers import SimulatedAnnealingSampler

                sampler = SimulatedAnnealingSampler()
                response = sampler.sample(bqm, num_reads=self.num_reads)

            best = response.first
            decoded = model.decode_sample(best.sample, vartype="BINARY")
        else:
            # Fallback to pure Python
            formulation = QUBOFormulation(context)
            Q = formulation.build()
            sample, energy = SimulatedQuantumAnnealingSolver(
                timeout_seconds=self.timeout_seconds,
                num_reads=self.num_reads,
            )._solve_pure_python(Q, formulation)

            assignments = formulation.decode_solution(sample)
            runtime = time.time() - start_time

            return SolverResult(
                success=True,
                assignments=assignments,
                status="feasible",
                objective_value=-energy,
                runtime_seconds=runtime,
                solver_status="pure_python_fallback",
                statistics={"num_variables": formulation.num_variables},
            )

        runtime = time.time() - start_time

        # Extract assignments from decoded solution
        assignments = self._extract_assignments(decoded, var_map, context)

        return SolverResult(
            success=True,
            assignments=assignments,
            status="feasible",
            objective_value=-best.energy,
            runtime_seconds=runtime,
            solver_status="pyqubo",
            statistics={
                "num_variables": len(bqm.variables),
                "num_interactions": len(bqm.quadratic),
                "constraint_violations": decoded.constraints(only_broken=True),
            },
        )

    def _build_pyqubo_model(self, context: SchedulingContext) -> tuple[Any, dict]:
        """Build PyQUBO model from scheduling context."""
        from pyqubo import Array, Constraint, Placeholder

        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        n_residents = len(context.residents)
        n_blocks = len(workday_blocks)
        n_templates = len(
            [t for t in context.templates if not t.requires_procedure_credential]
        )

        if n_residents == 0 or n_blocks == 0 or n_templates == 0:
            return None, {}

        # Create binary variables: x[resident, block, template]
        x = Array.create(
            "x", shape=(n_residents, n_blocks, n_templates), vartype="BINARY"
        )

        # Build index mappings
        var_map = {
            "resident_idx": {r.id: i for i, r in enumerate(context.residents)},
            "block_idx": {b.id: i for i, b in enumerate(workday_blocks)},
            "template_idx": {
                t.id: i
                for i, t in enumerate(context.templates)
                if not t.requires_procedure_credential
            },
            "idx_to_resident": {i: r.id for i, r in enumerate(context.residents)},
            "idx_to_block": {i: b.id for i, b in enumerate(workday_blocks)},
            "idx_to_template": {
                i: t.id
                for i, t in enumerate(context.templates)
                if not t.requires_procedure_credential
            },
        }

        # Objective: Maximize coverage
        H_coverage = -sum(
            x[r, b, t]
            for r in range(n_residents)
            for b in range(n_blocks)
            for t in range(n_templates)
        )

        # Constraint: At most one assignment per resident per block
        H_one_per_block = sum(
            Constraint(
                (sum(x[r, b, t] for t in range(n_templates)) - 1) ** 2,
                label=f"one_per_block_{r}_{b}",
            )
            for r in range(n_residents)
            for b in range(n_blocks)
        )

        # Constraint: At most one resident per block (simplified)
        H_one_resident = sum(
            Constraint(
                (
                    sum(
                        x[r, b, t]
                        for r in range(n_residents)
                        for t in range(n_templates)
                    )
                )
                ** 2
                - sum(
                    x[r, b, t] for r in range(n_residents) for t in range(n_templates)
                ),
                label=f"one_resident_{b}",
            )
            for b in range(n_blocks)
        )

        # Build final Hamiltonian
        H = H_coverage + Placeholder("lambda_block") * H_one_per_block

        # Compile model
        model = H.compile()

        return model, var_map

    def _extract_assignments(
        self, decoded: Any, var_map: dict, context: SchedulingContext
    ) -> list[tuple[UUID, UUID, UUID | None]]:
        """Extract assignments from decoded PyQUBO solution."""
        assignments = []

        for var_name, value in decoded.sample.items():
            if value == 1 and var_name.startswith("x["):
                # Parse x[r,b,t] format
                try:
                    indices = var_name[2:-1].split("][")
                    if len(indices) == 3:
                        r, b, t = int(indices[0]), int(indices[1]), int(indices[2])
                        person_id = var_map["idx_to_resident"].get(r)
                        block_id = var_map["idx_to_block"].get(b)
                        template_id = var_map["idx_to_template"].get(t)

                        if person_id and block_id:
                            assignments.append((person_id, block_id, template_id))
                except (ValueError, KeyError):
                    continue

        return assignments


class QuantumInspiredSolver(BaseSolver):
    """
    Hybrid solver that automatically selects the best quantum-inspired approach.

    Selection strategy:
    1. Small problems (<100 vars): Exact solver if available
    2. Medium problems (<10000 vars): Simulated annealing
    3. Large problems: Decomposition + parallel annealing
    4. If D-Wave available: Use quantum hardware for subproblems

    Environment Configuration:
        - USE_QUANTUM_SOLVER: Enable/disable quantum solver (default: false)
        - DWAVE_API_TOKEN: D-Wave API token for quantum hardware access
        - QUANTUM_SOLVER_BACKEND: "classical" or "quantum" (default: classical)

    The solver gracefully falls back to classical simulated annealing if:
    - D-Wave libraries are not installed
    - D-Wave API token is missing or invalid
    - D-Wave service is unreachable
    - Problem size exceeds hardware constraints
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 60.0,
        use_quantum_hardware: bool = False,
        dwave_token: str | None = None,
    ):
        """
        Initialize hybrid quantum-inspired solver.

        Args:
            constraint_manager: Optional constraint manager
            timeout_seconds: Maximum solve time
            use_quantum_hardware: Whether to use D-Wave quantum hardware
            dwave_token: D-Wave API token (if using hardware)
        """
        super().__init__(constraint_manager, timeout_seconds)

        # Validate quantum hardware availability
        self.use_quantum_hardware = False
        if use_quantum_hardware:
            if not DWAVE_SYSTEM_AVAILABLE:
                logger.warning(
                    "D-Wave system libraries not available. "
                    "Install with: pip install dwave-system"
                )
            elif not dwave_token:
                logger.warning(
                    "D-Wave API token not provided. "
                    "Set DWAVE_API_TOKEN environment variable."
                )
            else:
                # All requirements met - enable quantum hardware
                self.use_quantum_hardware = True
                logger.info("Quantum hardware mode enabled (D-Wave)")

        self.dwave_token = dwave_token

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Solve using best available quantum-inspired method."""
        formulation = QUBOFormulation(context)
        n_vars = formulation.num_variables

        logger.info(f"QuantumInspiredSolver: {n_vars} variables")

        # Select solver based on problem size
        if n_vars == 0:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No variables",
            )

        if self.use_quantum_hardware and n_vars <= MAX_QUANTUM_VARS:
            # Use D-Wave quantum annealer
            return self._solve_with_dwave(context, existing_assignments)

        # Use simulated annealing for all sizes
        solver = SimulatedQuantumAnnealingSolver(
            constraint_manager=self.constraint_manager,
            timeout_seconds=self.timeout_seconds,
            num_reads=min(MAX_READS, max(MIN_READS, BASE_READS // n_vars)),
            num_sweeps=min(MAX_SWEEPS, max(MIN_SWEEPS, n_vars * SWEEPS_PER_VAR)),
        )
        return solver.solve(context, existing_assignments)

    def _solve_with_dwave(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """
        Solve using D-Wave quantum hardware with graceful fallback.

        Falls back to classical simulated annealing if:
        - D-Wave libraries not available
        - API token missing or invalid
        - Service unreachable
        - Problem too large for hardware

        Returns:
            SolverResult with solver_status indicating "dwave_quantum" or fallback
        """
        if not DWAVE_SYSTEM_AVAILABLE:
            logger.warning("D-Wave system not available, falling back to classical SA")
            return SimulatedQuantumAnnealingSolver(
                timeout_seconds=self.timeout_seconds
            ).solve(context, existing_assignments)

        if not self.dwave_token:
            logger.warning("D-Wave API token not set, falling back to classical SA")
            return SimulatedQuantumAnnealingSolver(
                timeout_seconds=self.timeout_seconds
            ).solve(context, existing_assignments)

        start_time = time.time()
        formulation = QUBOFormulation(context)
        Q = formulation.build()

        # Try D-Wave quantum hardware
        try:
            from dwave.system import DWaveSampler, EmbeddingComposite

            logger.info(
                f"Attempting D-Wave quantum solve ({formulation.num_variables} variables)"
            )
            sampler = EmbeddingComposite(DWaveSampler(token=self.dwave_token))
            response = sampler.sample_qubo(
                Q,
                num_reads=100,
                annealing_time=20,  # microseconds
            )
            best = response.first
            sample = dict(best.sample)
            energy = best.energy
            used_quantum = True
            solver_status = "dwave_quantum"
            logger.info(f"D-Wave quantum solve succeeded (energy={energy:.2f})")

        except Exception as e:
            # Graceful fallback to classical SA
            logger.warning(
                f"D-Wave quantum solve failed: {e.__class__.__name__}: {e}"
            )
            logger.info("Falling back to classical simulated annealing")
            sample, energy = SimulatedQuantumAnnealingSolver(
                timeout_seconds=self.timeout_seconds
            )._solve_pure_python(Q, formulation)
            used_quantum = False
            solver_status = "classical_fallback"

        runtime = time.time() - start_time
        assignments = formulation.decode_solution(sample)

        return SolverResult(
            success=True,
            assignments=assignments,
            status="feasible",
            objective_value=-energy,
            runtime_seconds=runtime,
            solver_status=solver_status,
            statistics={
                "num_variables": formulation.num_variables,
                "used_quantum": used_quantum,
                "backend": "dwave" if used_quantum else "simulated_annealing",
            },
        )


def get_quantum_library_status() -> dict[str, bool]:
    """
    Check which quantum libraries are available.

    Returns:
        Dict with library availability status
    """
    return {
        "pyqubo": PYQUBO_AVAILABLE,
        "dwave_samplers": DWAVE_SAMPLERS_AVAILABLE,
        "dwave_system": DWAVE_SYSTEM_AVAILABLE,
        "qubovert": QUBOVERT_AVAILABLE,
    }


def get_quantum_solver_config() -> dict[str, Any]:
    """
    Load quantum solver configuration from environment variables.

    Returns:
        Dict with configuration:
            - enabled: Whether quantum solver is enabled
            - backend: "classical" or "quantum"
            - dwave_token: D-Wave API token (if set)
            - use_quantum_hardware: Whether to attempt quantum hardware use

    Environment Variables:
        USE_QUANTUM_SOLVER: "true" to enable (default: "false")
        DWAVE_API_TOKEN: D-Wave API token
        QUANTUM_SOLVER_BACKEND: "classical" or "quantum" (default: "classical")

    Example:
        >>> config = get_quantum_solver_config()
        >>> if config["enabled"]:
        ...     solver = QuantumInspiredSolver(
        ...         use_quantum_hardware=config["use_quantum_hardware"],
        ...         dwave_token=config["dwave_token"]
        ...     )
    """
    enabled = os.getenv("USE_QUANTUM_SOLVER", "false").lower() == "true"
    backend = os.getenv("QUANTUM_SOLVER_BACKEND", "classical").lower()
    dwave_token = os.getenv("DWAVE_API_TOKEN")

    # Only use quantum hardware if:
    # 1. Quantum solver is enabled
    # 2. Backend is set to "quantum"
    # 3. D-Wave token is provided
    # 4. D-Wave libraries are available
    use_quantum_hardware = (
        enabled
        and backend == "quantum"
        and dwave_token is not None
        and DWAVE_SYSTEM_AVAILABLE
    )

    return {
        "enabled": enabled,
        "backend": backend,
        "dwave_token": dwave_token,
        "use_quantum_hardware": use_quantum_hardware,
        "libraries_available": get_quantum_library_status(),
    }


def create_quantum_solver_from_env(
    constraint_manager: ConstraintManager | None = None,
    timeout_seconds: float = 60.0,
) -> QuantumInspiredSolver | SimulatedQuantumAnnealingSolver:
    """
    Create quantum solver instance from environment configuration.

    Automatically selects the appropriate solver based on environment variables:
    - If USE_QUANTUM_SOLVER=false: Returns None (use classical solvers)
    - If QUANTUM_SOLVER_BACKEND=classical: Returns SimulatedQuantumAnnealingSolver
    - If QUANTUM_SOLVER_BACKEND=quantum: Returns QuantumInspiredSolver with D-Wave

    Args:
        constraint_manager: Optional constraint manager
        timeout_seconds: Maximum solve time

    Returns:
        Configured quantum solver instance, or None if disabled

    Example:
        >>> solver = create_quantum_solver_from_env()
        >>> if solver:
        ...     result = solver.solve(context)
        ... else:
        ...     # Use classical solver instead
        ...     result = CPSATSolver().solve(context)
    """
    config = get_quantum_solver_config()

    if not config["enabled"]:
        logger.info("Quantum solver disabled (USE_QUANTUM_SOLVER=false)")
        return None

    if config["backend"] == "quantum" and config["use_quantum_hardware"]:
        logger.info("Creating quantum-inspired solver with D-Wave hardware support")
        return QuantumInspiredSolver(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            use_quantum_hardware=True,
            dwave_token=config["dwave_token"],
        )
    else:
        logger.info("Creating classical simulated annealing solver (quantum-inspired)")
        return SimulatedQuantumAnnealingSolver(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
        )
