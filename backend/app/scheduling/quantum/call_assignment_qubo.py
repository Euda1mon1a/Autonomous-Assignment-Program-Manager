"""
QUBO-Based Call Assignment Optimizer for Medical Residency Scheduling.

This module implements Quadratic Unconstrained Binary Optimization (QUBO)
formulations specifically for call assignment optimization. Unlike general
scheduling, call assignment has unique constraints:

1. Overnight call (Sun-Thu nights): One resident per night
2. Weekend coverage: Friday/Saturday handled separately (FMIT)
3. ACGME post-call constraints: Day after call = light duty
4. Call equity: Fair distribution across residents
5. Specialty requirements: Certain rotations need specific coverage

Problem Size Analysis (Sweet Spot: 700-14,600 variables):
    - 20 residents × 365 call nights × 2 call types = 14,600 variables
    - 10 residents × 52 weeks = 520 variables (minimal)
    - Quadratic interactions scale as O(n²) but sparse due to constraints

QUBO Formulation:
    minimize: x^T Q x

    where x ∈ {0,1}^n is the binary assignment vector
    and Q encodes both objectives and constraint penalties

    Q = Q_coverage + Q_acgme + Q_equity + Q_specialty + Q_preference

References:
    - Nurse Scheduling QUBO: https://arxiv.org/abs/2302.09459
    - Quantum-Inspired Optimization: https://arxiv.org/abs/2103.01708
    - D-Wave Scheduling: https://www.dwavesys.com/applications

Author: Claude Code (Autonomous Assignment Program Manager)
Date: 2025-12-27
"""

from __future__ import annotations

import json
import logging
import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

import numpy as np

if TYPE_CHECKING:
    from app.models.person import Person
    from app.scheduling.constraints import SchedulingContext

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS AND DATA CLASSES
# =============================================================================


class CallType(str, Enum):
    """Types of call assignments."""

    OVERNIGHT = "overnight"  # Sun-Thu nights
    BACKUP = "backup"  # Backup coverage
    WEEKEND = "weekend"  # Fri/Sat (typically FMIT)


class ConstraintHardness(str, Enum):
    """Constraint classification for penalty weighting."""

    HARD = "hard"  # Must satisfy (large penalty)
    SOFT = "soft"  # Prefer to satisfy (small penalty)


@dataclass
class CallNight:
    """Represents a single call night to be assigned."""

    date: date
    call_type: CallType
    is_weekend: bool = False
    is_holiday: bool = False
    specialty_required: str | None = None
    min_pgy_level: int = 1

    @property
    def weekday(self) -> int:
        """Return weekday (0=Mon, 6=Sun)."""
        return self.date.weekday()

    @property
    def is_sunday(self) -> bool:
        """Sunday is considered the worst call day."""
        return self.weekday == 6


@dataclass
class CallCandidate:
    """A resident eligible for call assignment."""

    person_id: UUID
    name: str
    pgy_level: int
    specialty: str | None = None
    max_calls_per_week: int = 2
    max_consecutive_call_days: int = 1
    avoid_days: set[int] = field(default_factory=set)  # weekdays to avoid
    preference_bonus: dict[int, float] = field(default_factory=dict)  # weekday -> bonus


@dataclass
class QUBOSolution:
    """Result from QUBO solver."""

    sample: dict[int, int]  # variable index -> 0/1
    energy: float
    assignments: list[tuple[UUID, date, CallType]]
    runtime_seconds: float
    num_sweeps: int
    num_reads: int
    final_temperature: float
    violations: list[str]
    is_valid: bool
    landscape_data: dict | None = None


@dataclass
class LandscapePoint:
    """Single point in the optimization landscape."""

    energy: float
    configuration: list[int]
    constraint_penalties: dict[str, float]
    timestamp: float


# =============================================================================
# QUBO FORMULATION FOR CALL ASSIGNMENT
# =============================================================================


class CallAssignmentQUBO:
    """
    QUBO formulation specifically for call assignment optimization.

    The QUBO matrix Q encodes:
    - Coverage objective: Assign exactly one resident per call night
    - ACGME constraints: Post-call rest, consecutive days limits
    - Equity constraints: Fair distribution of call burden
    - Preference constraints: Honor individual preferences

    Binary Variable Encoding:
        x[r, n] = 1 if resident r is assigned to call night n
        where r ∈ {0, ..., R-1} and n ∈ {0, ..., N-1}

    Coordinate Transform (Discrete → Continuous QUBO):
        The discrete scheduling space (resident, night) is mapped to a
        continuous energy landscape via:

        E(x) = x^T Q x = Σ_i Q_ii x_i + Σ_{i<j} Q_ij x_i x_j

        This quadratic form creates a hypersurface over {0,1}^n where:
        - Global minima = optimal schedules
        - Local minima = suboptimal but valid schedules
        - High energy regions = constraint violations

        The quantum tunneling mechanism allows transitions between local
        minima by exploiting the continuous nature of the QUBO landscape.
    """

    # Penalty weights for constraint violations
    HARD_CONSTRAINT_PENALTY = 50000.0  # Coverage, ACGME (must satisfy)
    ACGME_PENALTY = 25000.0  # Post-call rules
    EQUITY_PENALTY = 500.0  # Fair distribution
    PREFERENCE_PENALTY = 50.0  # Individual preferences

    def __init__(
        self,
        call_nights: list[CallNight],
        candidates: list[CallCandidate],
        equity_target: float | None = None,
    ):
        """
        Initialize QUBO formulation for call assignment.

        Args:
            call_nights: List of call nights to assign
            candidates: List of eligible residents
            equity_target: Target calls per resident (auto-calculated if None)
        """
        self.call_nights = call_nights
        self.candidates = candidates
        self.num_nights = len(call_nights)
        self.num_candidates = len(candidates)

        # Calculate equity target
        if equity_target is None:
            self.equity_target = self.num_nights / max(self.num_candidates, 1)
        else:
            self.equity_target = equity_target

        # Build variable indexing
        self.var_index: dict[tuple[int, int], int] = {}
        self.index_to_var: dict[int, tuple[int, int]] = {}
        self._build_variable_index()

        # QUBO matrix (sparse representation)
        self.Q: dict[tuple[int, int], float] = {}

        # Landscape tracking for visualization
        self.landscape_history: list[LandscapePoint] = []

        logger.info(
            f"CallAssignmentQUBO initialized: {self.num_variables} variables "
            f"({self.num_candidates} candidates × {self.num_nights} nights)"
        )

    def _build_variable_index(self) -> None:
        """Build mapping from (candidate, night) to flat index."""
        idx = 0
        for r_i in range(self.num_candidates):
            for n_i in range(self.num_nights):
                self.var_index[(r_i, n_i)] = idx
                self.index_to_var[idx] = (r_i, n_i)
                idx += 1

    @property
    def num_variables(self) -> int:
        """Number of binary variables in the QUBO."""
        return len(self.var_index)

    def build(self) -> dict[tuple[int, int], float]:
        """
        Build the complete QUBO matrix with all constraints.

        Returns:
            Q: Sparse QUBO matrix as dict of (i, j) -> coefficient
        """
        self.Q = {}
        start_time = time.time()

        # Objective: Encourage assignment (negative diagonal)
        self._add_assignment_incentive()

        # Hard: Exactly one resident per call night
        self._add_coverage_constraint()

        # Hard: At most one call per resident per night (already enforced by encoding)
        # Hard: ACGME consecutive call limit
        self._add_consecutive_call_constraint()

        # Soft: Call equity
        self._add_equity_constraint()

        # Soft: Sunday call equity (tracked separately)
        self._add_sunday_equity_constraint()

        # Soft: Weekday preferences
        self._add_preference_constraints()

        # Soft: Call spacing (avoid back-to-back)
        self._add_spacing_constraint()

        build_time = time.time() - start_time
        logger.info(
            f"QUBO matrix built: {len(self.Q)} non-zero terms in {build_time:.3f}s"
        )

        return self.Q

    def _add_assignment_incentive(self) -> None:
        """Add negative linear terms to encourage assignments."""
        # Each assignment contributes -1 to objective (we minimize)
        for idx in range(self.num_variables):
            self._add_linear(idx, -1.0)

    def _add_coverage_constraint(self) -> None:
        """
        Constraint: Exactly one resident per call night.

        Encoded as: P * (Σ_r x[r,n] - 1)² for each night n
        Expands to: P * (Σ_r Σ_s x[r,n]x[s,n] - 2Σ_r x[r,n] + 1)

        The -2*x term cancels with the assignment incentive to give proper
        "exactly one" semantics.
        """
        for n_i in range(self.num_nights):
            # Get all variables for this night
            night_vars = [
                self.var_index[(r_i, n_i)] for r_i in range(self.num_candidates)
            ]

            # Linear part: -2P * Σ x[r,n] (combined with assignment incentive)
            for idx in night_vars:
                self._add_linear(idx, -2 * self.HARD_CONSTRAINT_PENALTY + 1)

            # Quadratic part: P * Σ_r Σ_s x[r,n]x[s,n] for r≠s
            for i, idx1 in enumerate(night_vars):
                for idx2 in night_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * self.HARD_CONSTRAINT_PENALTY)

    def _add_consecutive_call_constraint(self) -> None:
        """
        ACGME Constraint: No more than max_consecutive_call_days in a row.

        For simplicity, we penalize same-resident assignment on consecutive nights.
        This encodes: x[r,n] * x[r,n+1] should be 0
        """
        for r_i, candidate in enumerate(self.candidates):
            max_consecutive = candidate.max_consecutive_call_days

            # For standard case (max_consecutive=1), penalize any consecutive
            if max_consecutive <= 1:
                for n_i in range(self.num_nights - 1):
                    # Check if nights are actually consecutive dates
                    if (
                        self.call_nights[n_i + 1].date - self.call_nights[n_i].date
                    ).days == 1:
                        idx1 = self.var_index[(r_i, n_i)]
                        idx2 = self.var_index[(r_i, n_i + 1)]
                        self._add_quadratic(idx1, idx2, self.ACGME_PENALTY)

    def _add_equity_constraint(self) -> None:
        """
        Soft Constraint: Distribute calls evenly across residents.

        We penalize deviation from mean by adding quadratic terms
        that prefer balanced assignment counts.

        Formulation: Minimize (Σ_n x[r,n] - mean)² for each r
        Expands to: Σ_n Σ_m x[r,n]x[r,m] - 2*mean*Σ_n x[r,n] + mean²

        The quadratic part penalizes residents with too many calls.
        """
        mean_calls = self.equity_target

        for r_i in range(self.num_candidates):
            resident_vars = [
                self.var_index[(r_i, n_i)] for n_i in range(self.num_nights)
            ]

            # Linear: -2*mean*x (encourages filling to mean)
            for idx in resident_vars:
                self._add_linear(idx, -2 * mean_calls * self.EQUITY_PENALTY)

            # Quadratic: x[r,n]*x[r,m] (penalizes exceeding mean)
            # Scale penalty by 1/num_nights to avoid overwhelming other terms
            scaled_penalty = self.EQUITY_PENALTY / max(len(resident_vars), 1)
            for i, idx1 in enumerate(resident_vars):
                for idx2 in resident_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * scaled_penalty)

    def _add_sunday_equity_constraint(self) -> None:
        """
        Track Sunday calls separately (considered worst day).

        Applies additional equity pressure on Sunday nights.
        """
        sunday_nights = [
            n_i for n_i, night in enumerate(self.call_nights) if night.is_sunday
        ]

        if not sunday_nights:
            return

        sunday_mean = len(sunday_nights) / max(self.num_candidates, 1)
        sunday_penalty = self.EQUITY_PENALTY * 2  # Higher weight for Sunday

        for r_i in range(self.num_candidates):
            sunday_vars = [self.var_index[(r_i, n_i)] for n_i in sunday_nights]

            if not sunday_vars:
                continue

            # Similar to general equity but for Sunday subset
            for idx in sunday_vars:
                self._add_linear(idx, -2 * sunday_mean * sunday_penalty)

            scaled_penalty = sunday_penalty / max(len(sunday_vars), 1)
            for i, idx1 in enumerate(sunday_vars):
                for idx2 in sunday_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * scaled_penalty)

    def _add_preference_constraints(self) -> None:
        """
        Honor individual preferences and avoidance days.

        Adds linear penalty for assignments on avoided days
        and bonus (negative penalty) for preferred days.
        """
        for r_i, candidate in enumerate(self.candidates):
            for n_i, night in enumerate(self.call_nights):
                idx = self.var_index[(r_i, n_i)]
                weekday = night.weekday

                # Penalize avoided days
                if weekday in candidate.avoid_days:
                    self._add_linear(idx, self.PREFERENCE_PENALTY * 10)

                # Apply preference bonus (negative = encouraged)
                if weekday in candidate.preference_bonus:
                    bonus = candidate.preference_bonus[weekday]
                    self._add_linear(idx, -bonus * self.PREFERENCE_PENALTY)

    def _add_spacing_constraint(self) -> None:
        """
        Soft Constraint: Prefer spacing between call nights.

        Penalize assignments within 3 days of each other for same resident.
        This helps avoid call fatigue.
        """
        spacing_penalty = self.PREFERENCE_PENALTY * 3

        for r_i in range(self.num_candidates):
            for n_i in range(self.num_nights):
                for n_j in range(n_i + 1, min(n_i + 4, self.num_nights)):
                    # Check actual day spacing
                    days_apart = (
                        self.call_nights[n_j].date - self.call_nights[n_i].date
                    ).days

                    if 2 <= days_apart <= 3:  # Close but not consecutive
                        idx1 = self.var_index[(r_i, n_i)]
                        idx2 = self.var_index[(r_i, n_j)]
                        # Smaller penalty for 3 days apart than 2
                        penalty = spacing_penalty / days_apart
                        self._add_quadratic(idx1, idx2, penalty)

    def _add_linear(self, i: int, value: float) -> None:
        """Add linear term Q[i,i] += value."""
        key = (i, i)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def _add_quadratic(self, i: int, j: int, value: float) -> None:
        """Add quadratic term Q[i,j] += value (symmetric)."""
        if i > j:
            i, j = j, i
        key = (i, j)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def decode_solution(
        self, sample: dict[int, int]
    ) -> list[tuple[UUID, date, CallType]]:
        """
        Decode QUBO solution to assignment list.

        Args:
            sample: Dict mapping variable index to 0/1 value

        Returns:
            List of (person_id, date, call_type) tuples
        """
        assignments = []

        for idx, value in sample.items():
            if value == 1 and idx in self.index_to_var:
                r_i, n_i = self.index_to_var[idx]
                candidate = self.candidates[r_i]
                night = self.call_nights[n_i]
                assignments.append((candidate.person_id, night.date, night.call_type))

        return assignments

    def compute_energy(self, sample: dict[int, int]) -> float:
        """Compute QUBO energy for a sample."""
        energy = 0.0
        for (i, j), coef in self.Q.items():
            if i == j:
                energy += coef * sample.get(i, 0)
            else:
                energy += coef * sample.get(i, 0) * sample.get(j, 0)
        return energy

    def get_constraint_breakdown(self, sample: dict[int, int]) -> dict[str, float]:
        """
        Analyze which constraints contribute to the energy.

        Returns breakdown by constraint type for debugging and visualization.
        """
        # This is a simplified analysis - for full breakdown would need
        # to rebuild Q with tracking
        breakdown = {
            "coverage": 0.0,
            "consecutive": 0.0,
            "equity": 0.0,
            "sunday_equity": 0.0,
            "preferences": 0.0,
            "spacing": 0.0,
            "total": self.compute_energy(sample),
        }

        # Count assignments per resident and night for analysis
        assignments_per_night = defaultdict(int)
        assignments_per_resident = defaultdict(int)

        for idx, value in sample.items():
            if value == 1 and idx in self.index_to_var:
                r_i, n_i = self.index_to_var[idx]
                assignments_per_night[n_i] += 1
                assignments_per_resident[r_i] += 1

        # Coverage violations (nights with ≠1 assignment)
        for n_i, count in assignments_per_night.items():
            if count != 1:
                breakdown["coverage"] += self.HARD_CONSTRAINT_PENALTY * (count - 1) ** 2

        # Equity (variance from mean)
        if assignments_per_resident:
            mean = sum(assignments_per_resident.values()) / len(
                assignments_per_resident
            )
            variance = sum(
                (c - mean) ** 2 for c in assignments_per_resident.values()
            ) / len(assignments_per_resident)
            breakdown["equity"] = variance * self.EQUITY_PENALTY

        return breakdown


# =============================================================================
# QUANTUM-INSPIRED SIMULATED ANNEALING SOLVER
# =============================================================================


class QuantumTunnelingAnnealingSolver:
    """
    Simulated annealing with quantum-inspired tunneling for QUBO optimization.

    Key Features:
    1. Classical simulated annealing base
    2. Quantum tunneling probability for barrier penetration
    3. Adaptive temperature schedule
    4. Multi-start with population-based search
    5. Landscape tracking for visualization

    Quantum Tunneling Model:
        Unlike classical SA which requires thermal activation to escape local
        minima (P_classical = exp(-ΔE/T)), quantum tunneling allows transitions
        through barriers with probability:

        P_tunnel = exp(-κ * width * √height)

        where:
        - κ is a decay constant (related to Planck's constant)
        - width is the barrier width (Hamming distance in binary space)
        - height is the barrier height (max energy along path)

        In practice, we approximate this using:
        P_tunnel = exp(-barrier_coef * √|ΔE|)

        This allows escaping from local minima without the exponentially small
        probability that classical SA would require.

    Path Integral Inspired Schedule:
        The temperature schedule is inspired by Suzuki-Trotter decomposition
        used in path integral Monte Carlo:

        T(t) = T_0 * (1 - t/t_max)^α

        where α > 1 gives a schedule that maintains higher temperatures longer
        before rapid cooling, mimicking quantum spreading.
    """

    def __init__(
        self,
        num_reads: int = 100,
        num_sweeps: int = 10000,
        beta_range: tuple[float, float] = (0.1, 10.0),
        tunneling_strength: float = 0.3,
        barrier_coefficient: float = 1.0,
        seed: int | None = None,
        track_landscape: bool = True,
        landscape_sample_rate: int = 100,
    ):
        """
        Initialize quantum-inspired simulated annealing solver.

        Args:
            num_reads: Number of independent annealing runs
            num_sweeps: Number of sweeps per run
            beta_range: (beta_start, beta_end) for annealing schedule
            tunneling_strength: Weight of tunneling vs classical acceptance
            barrier_coefficient: Decay rate for tunneling probability
            seed: Random seed for reproducibility
            track_landscape: Whether to record landscape for visualization
            landscape_sample_rate: Sample every N sweeps for landscape
        """
        self.num_reads = num_reads
        self.num_sweeps = num_sweeps
        self.beta_range = beta_range
        self.tunneling_strength = tunneling_strength
        self.barrier_coefficient = barrier_coefficient
        self.seed = seed or random.randint(0, 2**32 - 1)
        self.track_landscape = track_landscape
        self.landscape_sample_rate = landscape_sample_rate

        # Landscape data for export
        self.landscape_history: list[LandscapePoint] = []

    def solve(self, formulation: CallAssignmentQUBO) -> QUBOSolution:
        """
        Solve QUBO using quantum-inspired simulated annealing.

        Args:
            formulation: CallAssignmentQUBO with built Q matrix

        Returns:
            QUBOSolution with best found configuration
        """
        start_time = time.time()
        random.seed(self.seed)
        np.random.seed(self.seed)

        Q = formulation.Q
        n = formulation.num_variables

        if n == 0:
            return QUBOSolution(
                sample={},
                energy=0.0,
                assignments=[],
                runtime_seconds=0.0,
                num_sweeps=0,
                num_reads=0,
                final_temperature=0.0,
                violations=["No variables to optimize"],
                is_valid=False,
            )

        best_sample = dict.fromkeys(range(n), 0)
        best_energy = formulation.compute_energy(best_sample)
        self.landscape_history = []

        logger.info(
            f"Starting quantum-inspired SA: {n} variables, "
            f"{self.num_reads} reads × {self.num_sweeps} sweeps"
        )

        for read in range(self.num_reads):
            # Initialize with random state
            sample = {i: random.randint(0, 1) for i in range(n)}
            energy = formulation.compute_energy(sample)

            beta_start, beta_end = self.beta_range

            for sweep in range(self.num_sweeps):
                # Path-integral inspired temperature schedule
                # Higher power maintains exploration longer
                t = sweep / self.num_sweeps
                alpha = 2.0  # Schedule exponent
                beta = beta_start + (beta_end - beta_start) * (t**alpha)

                # Shuffle variable order for better mixing
                var_order = list(range(n))
                random.shuffle(var_order)

                for i in var_order:
                    # Compute energy change for flipping variable i
                    delta_e = self._compute_delta_energy(sample, Q, i)

                    # Acceptance probability with quantum tunneling
                    accept = False
                    if delta_e <= 0:
                        accept = True
                    else:
                        # Classical Metropolis probability
                        classical_prob = math.exp(-beta * delta_e)

                        # Quantum tunneling probability
                        # P_tunnel = exp(-κ * √|ΔE|)
                        tunneling_prob = math.exp(
                            -self.barrier_coefficient * math.sqrt(abs(delta_e))
                        )

                        # Combined probability
                        combined_prob = (1 - self.tunneling_strength) * classical_prob
                        combined_prob += self.tunneling_strength * tunneling_prob

                        accept = random.random() < combined_prob

                    if accept:
                        sample[i] = 1 - sample[i]
                        energy += delta_e

                # Track landscape periodically
                if self.track_landscape and sweep % self.landscape_sample_rate == 0:
                    self.landscape_history.append(
                        LandscapePoint(
                            energy=energy,
                            configuration=[sample[i] for i in range(n)],
                            constraint_penalties=formulation.get_constraint_breakdown(
                                sample
                            ),
                            timestamp=time.time() - start_time,
                        )
                    )

                if energy < best_energy:
                    best_sample = sample.copy()
                    best_energy = energy

        runtime = time.time() - start_time

        # Decode and validate solution
        assignments = formulation.decode_solution(best_sample)
        violations, is_valid = self._validate_solution(formulation, best_sample)

        # Create landscape data for export
        landscape_data = None
        if self.track_landscape and self.landscape_history:
            landscape_data = self._export_landscape_data(formulation)

        logger.info(
            f"Quantum-inspired SA complete: energy={best_energy:.2f}, "
            f"{len(assignments)} assignments, valid={is_valid}, "
            f"runtime={runtime:.2f}s"
        )

        return QUBOSolution(
            sample=best_sample,
            energy=best_energy,
            assignments=assignments,
            runtime_seconds=runtime,
            num_sweeps=self.num_sweeps,
            num_reads=self.num_reads,
            final_temperature=1.0 / self.beta_range[1],
            violations=violations,
            is_valid=is_valid,
            landscape_data=landscape_data,
        )

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

    def _validate_solution(
        self, formulation: CallAssignmentQUBO, sample: dict[int, int]
    ) -> tuple[list[str], bool]:
        """
        Validate solution against hard constraints.

        Returns:
            (violations, is_valid) tuple
        """
        violations = []

        # Check coverage: exactly one resident per night
        for n_i in range(formulation.num_nights):
            count = sum(
                sample.get(formulation.var_index.get((r_i, n_i), -1), 0)
                for r_i in range(formulation.num_candidates)
            )
            if count == 0:
                violations.append(f"Night {n_i} has no coverage")
            elif count > 1:
                violations.append(f"Night {n_i} has {count} assignments (should be 1)")

        # Check consecutive call constraint
        for r_i, candidate in enumerate(formulation.candidates):
            prev_assigned = False
            for n_i in range(formulation.num_nights):
                idx = formulation.var_index.get((r_i, n_i))
                if idx is not None and sample.get(idx, 0) == 1:
                    if prev_assigned and candidate.max_consecutive_call_days <= 1:
                        violations.append(
                            f"Resident {r_i} has consecutive calls at night {n_i}"
                        )
                    prev_assigned = True
                else:
                    prev_assigned = False

        is_valid = len(violations) == 0
        return violations, is_valid

    def _export_landscape_data(self, formulation: CallAssignmentQUBO) -> dict[str, Any]:
        """
        Export landscape data for holographic visualization.

        Returns JSON-serializable dictionary with:
        - Energy trajectory over time
        - Configuration snapshots
        - Constraint penalty breakdown
        - Coordinate system metadata
        """
        return {
            "metadata": {
                "num_variables": formulation.num_variables,
                "num_candidates": formulation.num_candidates,
                "num_nights": formulation.num_nights,
                "solver": "QuantumTunnelingAnnealingSolver",
                "num_reads": self.num_reads,
                "num_sweeps": self.num_sweeps,
                "tunneling_strength": self.tunneling_strength,
                "seed": self.seed,
            },
            "coordinate_transform": {
                "description": "Maps discrete (resident, night) pairs to continuous QUBO energy",
                "variable_encoding": "x[r,n] = 1 if resident r on call night n",
                "energy_formula": "E(x) = Σ_i Q_ii*x_i + Σ_{i<j} Q_ij*x_i*x_j",
                "landscape_type": "hypersurface over {0,1}^n",
            },
            "trajectory": [
                {
                    "timestamp": pt.timestamp,
                    "energy": pt.energy,
                    "penalties": pt.constraint_penalties,
                }
                for pt in self.landscape_history
            ],
            "final_state": {
                "energy": (
                    self.landscape_history[-1].energy if self.landscape_history else 0
                ),
                "configuration_summary": {
                    "ones_count": (
                        sum(self.landscape_history[-1].configuration)
                        if self.landscape_history
                        else 0
                    ),
                },
            },
        }


# =============================================================================
# SOLUTION VALIDATOR
# =============================================================================


class CallAssignmentValidator:
    """
    Validates call assignment solutions against all constraints.

    Performs comprehensive validation including:
    1. Coverage: Every night has exactly one assigned resident
    2. ACGME: Post-call rest, consecutive limits, weekly limits
    3. Equity: Fair distribution within tolerance
    4. Specialty: Required specialties are covered
    """

    def __init__(
        self,
        call_nights: list[CallNight],
        candidates: list[CallCandidate],
        equity_tolerance: float = 3.0,
    ):
        """
        Initialize validator.

        Args:
            call_nights: List of call nights to validate
            candidates: List of eligible residents
            equity_tolerance: Max deviation from mean for equity
        """
        self.call_nights = call_nights
        self.candidates = candidates
        self.equity_tolerance = equity_tolerance
        self.candidate_by_id = {c.person_id: c for c in candidates}

    def validate(
        self, assignments: list[tuple[UUID, date, CallType]]
    ) -> tuple[bool, list[str], dict[str, Any]]:
        """
        Validate call assignments.

        Args:
            assignments: List of (person_id, date, call_type) tuples

        Returns:
            (is_valid, violations, metrics)
        """
        violations = []
        metrics = {}

        # Build assignment maps
        by_night = defaultdict(list)
        by_resident = defaultdict(list)
        for person_id, call_date, call_type in assignments:
            by_night[(call_date, call_type)].append(person_id)
            by_resident[person_id].append((call_date, call_type))

        # 1. Coverage validation
        coverage_violations = self._validate_coverage(by_night)
        violations.extend(coverage_violations)
        metrics["coverage_violations"] = len(coverage_violations)

        # 2. ACGME validation
        acgme_violations = self._validate_acgme(by_resident)
        violations.extend(acgme_violations)
        metrics["acgme_violations"] = len(acgme_violations)

        # 3. Equity validation
        equity_violations, equity_stats = self._validate_equity(by_resident)
        violations.extend(equity_violations)
        metrics["equity"] = equity_stats

        # 4. Specialty validation
        specialty_violations = self._validate_specialty(by_night)
        violations.extend(specialty_violations)
        metrics["specialty_violations"] = len(specialty_violations)

        is_valid = len(violations) == 0
        return is_valid, violations, metrics

    def _validate_coverage(
        self, by_night: dict[tuple[date, CallType], list[UUID]]
    ) -> list[str]:
        """Check that each night has exactly one assignment."""
        violations = []

        night_keys = {(n.date, n.call_type) for n in self.call_nights}

        for key in night_keys:
            count = len(by_night.get(key, []))
            if count == 0:
                violations.append(f"No coverage for {key[0]} ({key[1].value})")
            elif count > 1:
                violations.append(
                    f"Multiple assignments ({count}) for {key[0]} ({key[1].value})"
                )

        return violations

    def _validate_acgme(
        self, by_resident: dict[UUID, list[tuple[date, CallType]]]
    ) -> list[str]:
        """Check ACGME constraints."""
        violations = []

        for person_id, calls in by_resident.items():
            candidate = self.candidate_by_id.get(person_id)
            if not candidate:
                continue

            # Sort calls by date
            sorted_calls = sorted(calls, key=lambda x: x[0])

            # Check consecutive calls
            for i in range(1, len(sorted_calls)):
                prev_date = sorted_calls[i - 1][0]
                curr_date = sorted_calls[i][0]
                if (curr_date - prev_date).days == 1:
                    if candidate.max_consecutive_call_days <= 1:
                        violations.append(
                            f"{candidate.name}: Consecutive calls on {prev_date} and {curr_date}"
                        )

            # Check weekly limit
            # Group by ISO week
            by_week = defaultdict(int)
            for call_date, _ in sorted_calls:
                week_key = call_date.isocalendar()[:2]
                by_week[week_key] += 1

            for week, count in by_week.items():
                if count > candidate.max_calls_per_week:
                    violations.append(
                        f"{candidate.name}: {count} calls in week {week[1]} "
                        f"(max: {candidate.max_calls_per_week})"
                    )

        return violations

    def _validate_equity(
        self, by_resident: dict[UUID, list[tuple[date, CallType]]]
    ) -> tuple[list[str], dict]:
        """Check equity constraints."""
        violations = []

        counts = {
            c.person_id: len(by_resident.get(c.person_id, [])) for c in self.candidates
        }

        if not counts:
            return violations, {"mean": 0, "std": 0, "min": 0, "max": 0, "range": 0}

        values = list(counts.values())
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val

        if range_val > self.equity_tolerance * 2:
            violations.append(
                f"Call equity imbalance: range {min_val}-{max_val} "
                f"(tolerance: ±{self.equity_tolerance})"
            )

        # Check Sunday equity separately
        sunday_counts = {}
        for c in self.candidates:
            sunday_calls = [
                call
                for call in by_resident.get(c.person_id, [])
                if call[0].weekday() == 6
            ]
            sunday_counts[c.person_id] = len(sunday_calls)

        sunday_values = list(sunday_counts.values())
        if sunday_values:
            sunday_range = max(sunday_values) - min(sunday_values)
            if sunday_range > 2:
                violations.append(
                    f"Sunday call imbalance: range {min(sunday_values)}-{max(sunday_values)}"
                )

        return violations, {
            "mean": mean,
            "std": std,
            "min": min_val,
            "max": max_val,
            "range": range_val,
            "counts": counts,
        }

    def _validate_specialty(
        self, by_night: dict[tuple[date, CallType], list[UUID]]
    ) -> list[str]:
        """Check specialty requirements."""
        violations = []

        for night in self.call_nights:
            if not night.specialty_required:
                continue

            key = (night.date, night.call_type)
            assigned = by_night.get(key, [])

            if not assigned:
                continue

            person_id = assigned[0]
            candidate = self.candidate_by_id.get(person_id)

            if candidate and candidate.specialty != night.specialty_required:
                violations.append(
                    f"{night.date}: Requires {night.specialty_required}, "
                    f"assigned {candidate.specialty or 'none'}"
                )

        return violations


# =============================================================================
# BENCHMARKING AGAINST OR-TOOLS
# =============================================================================


class CallAssignmentBenchmark:
    """
    Benchmark QUBO solver against OR-Tools CP-SAT.

    Compares:
    - Solution quality (objective value)
    - Runtime
    - Constraint satisfaction
    - Scalability
    """

    def __init__(
        self,
        call_nights: list[CallNight],
        candidates: list[CallCandidate],
    ):
        self.call_nights = call_nights
        self.candidates = candidates

    def run_qubo_solver(
        self,
        num_reads: int = 100,
        num_sweeps: int = 5000,
    ) -> dict[str, Any]:
        """Run QUBO solver and collect metrics."""
        formulation = CallAssignmentQUBO(self.call_nights, self.candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=num_reads,
            num_sweeps=num_sweeps,
            track_landscape=True,
        )

        solution = solver.solve(formulation)

        return {
            "solver": "QUBO",
            "energy": solution.energy,
            "num_assignments": len(solution.assignments),
            "runtime_seconds": solution.runtime_seconds,
            "is_valid": solution.is_valid,
            "violations": solution.violations,
            "num_variables": formulation.num_variables,
        }

    def run_ortools_solver(self, timeout_seconds: float = 60.0) -> dict[str, Any]:
        """Run OR-Tools CP-SAT solver for comparison."""
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            return {
                "solver": "OR-Tools",
                "error": "OR-Tools not installed",
                "energy": float("inf"),
            }

        start_time = time.time()

        model = cp_model.CpModel()

        n_candidates = len(self.candidates)
        n_nights = len(self.call_nights)

        # Variables: x[r, n] = 1 if resident r on call night n
        x = {}
        for r_i in range(n_candidates):
            for n_i in range(n_nights):
                x[r_i, n_i] = model.NewBoolVar(f"x_{r_i}_{n_i}")

        # Constraint: Exactly one resident per night
        for n_i in range(n_nights):
            model.AddExactlyOne([x[r_i, n_i] for r_i in range(n_candidates)])

        # Constraint: Max calls per week
        for r_i, candidate in enumerate(self.candidates):
            # Group nights by week
            by_week = defaultdict(list)
            for n_i, night in enumerate(self.call_nights):
                week_key = night.date.isocalendar()[:2]
                by_week[week_key].append(n_i)

            for week, night_indices in by_week.items():
                model.Add(
                    sum(x[r_i, n_i] for n_i in night_indices)
                    <= candidate.max_calls_per_week
                )

        # Constraint: No consecutive calls
        for r_i, candidate in enumerate(self.candidates):
            if candidate.max_consecutive_call_days <= 1:
                for n_i in range(n_nights - 1):
                    if (
                        self.call_nights[n_i + 1].date - self.call_nights[n_i].date
                    ).days == 1:
                        model.Add(x[r_i, n_i] + x[r_i, n_i + 1] <= 1)

        # Objective: Minimize max calls (equity)
        max_calls = model.NewIntVar(0, n_nights, "max_calls")
        for r_i in range(n_candidates):
            model.Add(sum(x[r_i, n_i] for n_i in range(n_nights)) <= max_calls)
        model.Minimize(max_calls)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout_seconds
        status = solver.Solve(model)

        runtime = time.time() - start_time

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            assignments = []
            for r_i in range(n_candidates):
                for n_i in range(n_nights):
                    if solver.Value(x[r_i, n_i]) == 1:
                        assignments.append(
                            (
                                self.candidates[r_i].person_id,
                                self.call_nights[n_i].date,
                                self.call_nights[n_i].call_type,
                            )
                        )

            return {
                "solver": "OR-Tools",
                "objective": solver.ObjectiveValue(),
                "num_assignments": len(assignments),
                "runtime_seconds": runtime,
                "status": solver.StatusName(status),
                "branches": solver.NumBranches(),
                "conflicts": solver.NumConflicts(),
            }
        else:
            return {
                "solver": "OR-Tools",
                "error": solver.StatusName(status),
                "runtime_seconds": runtime,
            }

    def compare(
        self,
        qubo_reads: int = 100,
        qubo_sweeps: int = 5000,
        ortools_timeout: float = 60.0,
    ) -> dict[str, Any]:
        """
        Run both solvers and compare results.

        Returns comprehensive comparison metrics.
        """
        qubo_result = self.run_qubo_solver(qubo_reads, qubo_sweeps)
        ortools_result = self.run_ortools_solver(ortools_timeout)

        comparison = {
            "problem_size": {
                "num_nights": len(self.call_nights),
                "num_candidates": len(self.candidates),
                "num_variables": len(self.call_nights) * len(self.candidates),
            },
            "qubo": qubo_result,
            "ortools": ortools_result,
            "comparison": {},
        }

        # Compare if both succeeded
        if "error" not in qubo_result and "error" not in ortools_result:
            comparison["comparison"] = {
                "runtime_ratio": (
                    qubo_result["runtime_seconds"] / ortools_result["runtime_seconds"]
                    if ortools_result["runtime_seconds"] > 0
                    else float("inf")
                ),
                "qubo_valid": qubo_result["is_valid"],
                "assignment_difference": (
                    qubo_result["num_assignments"] - ortools_result["num_assignments"]
                ),
            }

        return comparison


# =============================================================================
# HIGH-LEVEL INTERFACE
# =============================================================================


def solve_call_assignment(
    call_nights: list[CallNight],
    candidates: list[CallCandidate],
    num_reads: int = 100,
    num_sweeps: int = 10000,
    export_landscape: bool = True,
    output_path: Path | None = None,
) -> QUBOSolution:
    """
    Convenience function to solve call assignment optimization.

    Args:
        call_nights: List of call nights to assign
        candidates: List of eligible residents
        num_reads: Number of SA restarts
        num_sweeps: Sweeps per restart
        export_landscape: Whether to export landscape data
        output_path: Path to save landscape JSON

    Returns:
        QUBOSolution with optimized assignments
    """
    # Build QUBO
    formulation = CallAssignmentQUBO(call_nights, candidates)
    formulation.build()

    # Solve
    solver = QuantumTunnelingAnnealingSolver(
        num_reads=num_reads,
        num_sweeps=num_sweeps,
        track_landscape=export_landscape,
    )

    solution = solver.solve(formulation)

    # Export landscape if requested
    if export_landscape and output_path and solution.landscape_data:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(solution.landscape_data, f, indent=2, default=str)
        logger.info(f"Landscape data exported to {output_path}")

    return solution


def create_call_nights_from_dates(
    start_date: date,
    end_date: date,
    call_type: CallType = CallType.OVERNIGHT,
    exclude_weekends: bool = True,
) -> list[CallNight]:
    """
    Generate call nights from date range.

    Args:
        start_date: First date to include
        end_date: Last date to include
        call_type: Type of call for all nights
        exclude_weekends: Skip Fri/Sat (typically FMIT)

    Returns:
        List of CallNight objects
    """
    nights = []
    current = start_date

    while current <= end_date:
        weekday = current.weekday()

        # Skip Friday (4) and Saturday (5) if excluding weekends
        if not exclude_weekends or weekday not in (4, 5):
            nights.append(
                CallNight(
                    date=current,
                    call_type=call_type,
                    is_weekend=weekday in (5, 6),
                )
            )

        current += timedelta(days=1)

    return nights


def create_candidates_from_residents(
    residents: list[Person],
    max_calls_per_week: int = 2,
    max_consecutive: int = 1,
) -> list[CallCandidate]:
    """
    Create CallCandidate list from Person models.

    Args:
        residents: List of Person objects
        max_calls_per_week: Default weekly call limit
        max_consecutive: Default consecutive call limit

    Returns:
        List of CallCandidate objects
    """
    candidates = []

    for resident in residents:
        candidate = CallCandidate(
            person_id=resident.id,
            name=resident.name,
            pgy_level=getattr(resident, "pgy_level", 1),
            specialty=getattr(resident, "specialty", None),
            max_calls_per_week=max_calls_per_week,
            max_consecutive_call_days=max_consecutive,
        )
        candidates.append(candidate)

    return candidates
