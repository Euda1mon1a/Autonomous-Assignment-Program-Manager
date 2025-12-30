"""
Spin Glass Model for Schedule Constraint Optimization.

Models residency scheduling as a spin glass system where:
- Assignments are "spins" with energy based on constraint violations
- Competing constraints create "frustration" preventing single optimum
- Multiple near-optimal "replica" schedules exist (RSB ansatz)

Physics basis: Spin glasses exhibit replica symmetry breaking - multiple
degenerate ground states separated by energy barriers.

References:
- Mézard, M., Parisi, G., & Virasoro, M. A. (1987). Spin glass theory and beyond.
- Sherrington, D., & Kirkpatrick, S. (1975). Solvable model of a spin-glass.
- Parisi, G. (1979). Infinite number of order parameters for spin-glasses.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import numpy as np

from app.scheduling.constraints import (
    Constraint,
    ConstraintResult,
    SchedulingContext,
)
from app.scheduling.solvers import SolverResult

logger = logging.getLogger(__name__)


@dataclass
class FrustrationCluster:
    """
    Identifies a group of conflicting constraints that create frustration.

    In spin glass physics, frustration occurs when competing interactions
    prevent all bonds from being satisfied simultaneously. In scheduling,
    this manifests as conflicting requirements (e.g., "maximize equity" vs
    "respect preferences" vs "minimize coverage gaps").

    Attributes:
        constraints: List of conflicting constraints in this cluster
        frustration_index: Measure of conflict intensity (0.0-1.0)
        affected_persons: Person IDs impacted by this frustration
        affected_blocks: Block IDs impacted by this frustration
        conflict_type: Category of conflict (e.g., "equity_vs_preference")
        resolution_suggestions: Potential ways to reduce frustration
    """

    constraints: list[str] = field(default_factory=list)
    frustration_index: float = 0.0
    affected_persons: set[UUID] = field(default_factory=set)
    affected_blocks: set[UUID] = field(default_factory=set)
    conflict_type: str = ""
    resolution_suggestions: list[str] = field(default_factory=list)


@dataclass
class ReplicaSchedule:
    """
    A single near-optimal schedule replica from the spin glass ensemble.

    Attributes:
        schedule_id: Unique identifier for this replica
        assignments: (person_id, block_id, template_id) tuples
        energy: Total constraint violation energy (lower is better)
        magnetization: Degree of alignment with soft constraints (-1 to 1)
        replica_index: Index in replica ensemble (0 to n_replicas-1)
        constraint_violations: Breakdown of energy by constraint type
    """

    schedule_id: str
    assignments: list[tuple[UUID, UUID, UUID | None]]
    energy: float
    magnetization: float
    replica_index: int
    constraint_violations: dict[str, float] = field(default_factory=dict)


@dataclass
class LandscapeAnalysis:
    """
    Analysis of the energy landscape across multiple replica schedules.

    Maps the "terrain" of possible solutions, identifying local minima,
    energy barriers, and solution basin structure.

    Attributes:
        global_minimum_energy: Lowest energy found across all replicas
        local_minima: List of energies corresponding to distinct local minima
        energy_barrier_heights: Energy gaps between local minima basins
        basin_sizes: Number of replicas in each basin
        frustration_clusters: Identified regions of high constraint conflict
        glass_transition_temp: Estimated temperature where system "freezes"
    """

    global_minimum_energy: float
    local_minima: list[float] = field(default_factory=list)
    energy_barrier_heights: list[float] = field(default_factory=list)
    basin_sizes: dict[int, int] = field(default_factory=dict)
    frustration_clusters: list[FrustrationCluster] = field(default_factory=list)
    glass_transition_temp: float = 0.0


@dataclass
class ReplicaSymmetryAnalysis:
    """
    Analysis of replica symmetry breaking (RSB) in schedule ensemble.

    Measures how different the replica schedules are from each other.
    High RSB indicates many diverse near-optimal solutions (good for robustness).
    Low RSB suggests a single dominant solution (potential brittleness).

    Attributes:
        parisi_overlap_matrix: n×n matrix of schedule similarities
        rsb_order_parameter: Quantifies degree of symmetry breaking (0-1)
        diversity_score: Measure of schedule variety (0-1)
        ultrametric_distance: Hierarchical clustering distance metric
        mean_overlap: Average similarity across all replica pairs
        overlap_distribution: Histogram of overlap values
    """

    parisi_overlap_matrix: np.ndarray = field(default_factory=lambda: np.array([]))
    rsb_order_parameter: float = 0.0
    diversity_score: float = 0.0
    ultrametric_distance: dict[tuple[int, int], float] = field(default_factory=dict)
    mean_overlap: float = 0.0
    overlap_distribution: dict[str, int] = field(default_factory=dict)


class SpinGlassScheduler:
    """
    Spin glass-inspired scheduler using replica theory for robust optimization.

    This scheduler treats the scheduling problem as a frustrated magnetic system
    where constraints act as competing interactions. Rather than seeking a single
    "optimal" solution (which may be brittle), it generates an ensemble of
    near-optimal "replica" schedules that reveal the structure of the solution space.

    Key Methods:
        - compute_frustration_index: Quantify conflicting constraints
        - generate_replica_schedules: Create diverse near-optimal solutions
        - compute_parisi_overlap: Measure similarity between schedules
        - find_glass_transition_threshold: Identify rigidity onset
        - analyze_energy_landscape: Map solution space structure

    Physics Analogy:
        Schedule = Spin configuration (each assignment is a spin)
        Constraints = Magnetic interactions (J_ij couplings)
        Frustration = Conflicting interactions preventing global satisfaction
        Replicas = Multiple degenerate ground states (RSB)
        Energy = Total constraint violation cost
    """

    def __init__(
        self,
        context: SchedulingContext,
        constraints: list[Constraint],
        temperature: float = 1.0,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize spin glass scheduler.

        Args:
            context: Scheduling context with persons, blocks, templates
            constraints: List of scheduling constraints (hard and soft)
            temperature: Thermal energy for replica sampling (higher = more diversity)
            random_seed: Random seed for reproducibility
        """
        self.context = context
        self.constraints = constraints
        self.temperature = temperature
        self.rng = np.random.default_rng(random_seed)

        # Cache constraint interaction matrix for efficiency
        self._interaction_matrix: dict[tuple[str, str], float] | None = None

    def compute_frustration_index(
        self, constraints: list[Constraint] | None = None
    ) -> float:
        """
        Measure the degree of frustration in the constraint system.

        Frustration occurs when satisfying one constraint makes it harder to
        satisfy another. This is computed by analyzing constraint interactions
        and identifying conflicting objectives.

        The frustration index ranges from 0.0 (no conflicts) to 1.0 (maximum
        frustration, where constraints are maximally incompatible).

        Args:
            constraints: Constraints to analyze (defaults to self.constraints)

        Returns:
            Frustration index between 0.0 and 1.0

        Example:
            >>> scheduler = SpinGlassScheduler(context, constraints)
            >>> frustration = scheduler.compute_frustration_index()
            >>> if frustration > 0.7:
            ...     print("Warning: Highly frustrated system - perfect solution unlikely")
        """
        if constraints is None:
            constraints = self.constraints

        if len(constraints) < 2:
            return 0.0

        # Build interaction matrix if not cached
        if self._interaction_matrix is None:
            self._build_interaction_matrix(constraints)

        # Compute frustration as fraction of negative (conflicting) interactions
        total_pairs = 0
        frustrated_pairs = 0

        for (i, j), coupling in self._interaction_matrix.items():
            total_pairs += 1
            # Negative coupling indicates antiferromagnetic (conflicting) interaction
            if coupling < 0:
                frustrated_pairs += 1

        if total_pairs == 0:
            return 0.0

        frustration_ratio = frustrated_pairs / total_pairs

        logger.info(
            f"Frustration analysis: {frustrated_pairs}/{total_pairs} "
            f"conflicting constraint pairs (index={frustration_ratio:.3f})"
        )

        return frustration_ratio

    def generate_replica_schedules(
        self,
        n_replicas: int = 10,
        base_solver_result: SolverResult | None = None,
    ) -> list[ReplicaSchedule]:
        """
        Generate multiple near-optimal replica schedules using thermal sampling.

        Uses simulated annealing at finite temperature to explore different
        regions of the energy landscape, producing diverse solutions that all
        have similar quality but different assignment patterns.

        This is inspired by the replica method in spin glass theory, where
        multiple copies of the system are studied to understand the structure
        of the solution space.

        Args:
            n_replicas: Number of replica schedules to generate
            base_solver_result: Optional initial solution to perturb

        Returns:
            List of ReplicaSchedule objects with diverse near-optimal solutions

        Example:
            >>> replicas = scheduler.generate_replica_schedules(n_replicas=20)
            >>> energies = [r.energy for r in replicas]
            >>> print(f"Energy range: {min(energies):.2f} - {max(energies):.2f}")
        """
        replicas: list[ReplicaSchedule] = []

        logger.info(
            f"Generating {n_replicas} replica schedules at T={self.temperature}"
        )

        for replica_idx in range(n_replicas):
            # Generate a perturbed schedule via simulated annealing
            assignments, energy = self._thermal_sample_schedule(
                base_solution=base_solver_result,
                replica_id=replica_idx,
            )

            # Compute magnetization (alignment with soft constraints)
            magnetization = self._compute_magnetization(assignments)

            # Break down energy by constraint type
            violation_breakdown = self._analyze_violations(assignments)

            replica = ReplicaSchedule(
                schedule_id=f"replica_{replica_idx:03d}",
                assignments=assignments,
                energy=energy,
                magnetization=magnetization,
                replica_index=replica_idx,
                constraint_violations=violation_breakdown,
            )

            replicas.append(replica)

            logger.debug(
                f"Replica {replica_idx}: energy={energy:.2f}, "
                f"magnetization={magnetization:.3f}"
            )

        return replicas

    def compute_parisi_overlap(
        self,
        schedule_a: ReplicaSchedule,
        schedule_b: ReplicaSchedule,
    ) -> float:
        """
        Compute Parisi overlap (similarity) between two schedules.

        The Parisi overlap q_ab measures the fraction of assignments that are
        identical between two schedules. It ranges from 0.0 (completely different)
        to 1.0 (identical).

        This is a key observable in spin glass theory for detecting replica
        symmetry breaking (RSB). High average overlap indicates replica symmetry
        (few solutions), while low overlap indicates RSB (many diverse solutions).

        Args:
            schedule_a: First replica schedule
            schedule_b: Second replica schedule

        Returns:
            Overlap value between 0.0 and 1.0

        Example:
            >>> overlap = scheduler.compute_parisi_overlap(replicas[0], replicas[1])
            >>> if overlap < 0.3:
            ...     print("Schedules are very different - good diversity!")
        """
        if not schedule_a.assignments or not schedule_b.assignments:
            return 0.0

        # Convert assignments to sets for comparison
        assignments_a = set(schedule_a.assignments)
        assignments_b = set(schedule_b.assignments)

        # Compute overlap as fraction of matching assignments
        intersection = assignments_a & assignments_b
        union = assignments_a | assignments_b

        if not union:
            return 1.0  # Both empty

        overlap = len(intersection) / len(union)

        return overlap

    def find_glass_transition_threshold(
        self,
        constraint_density_range: tuple[float, float] = (0.5, 2.0),
        n_samples: int = 10,
    ) -> float:
        """
        Find the glass transition threshold where the system becomes rigid.

        The glass transition is the point where increasing constraint density
        causes the system to "freeze" - flexibility vanishes and the solution
        space becomes dominated by a single frozen configuration.

        This is analogous to the freezing transition in spin glasses as
        temperature is lowered or disorder is increased.

        Args:
            constraint_density_range: (min, max) constraint density to scan
            n_samples: Number of density points to sample

        Returns:
            Critical constraint density at glass transition

        Example:
            >>> critical_density = scheduler.find_glass_transition_threshold()
            >>> print(f"System becomes rigid at constraint density = {critical_density:.2f}")
        """
        min_density, max_density = constraint_density_range
        densities = np.linspace(min_density, max_density, n_samples)

        logger.info(
            f"Scanning constraint density {min_density:.2f}-{max_density:.2f} "
            f"for glass transition"
        )

        overlaps: list[float] = []

        for density in densities:
            # Generate replicas at this constraint density
            # (in practice, we vary temperature instead of adding/removing constraints)
            temp = 1.0 / density  # Higher density = lower temperature
            self.temperature = temp

            replicas = self.generate_replica_schedules(n_replicas=5)

            # Compute mean overlap between replica pairs
            if len(replicas) >= 2:
                mean_overlap = np.mean(
                    [
                        self.compute_parisi_overlap(replicas[i], replicas[j])
                        for i in range(len(replicas))
                        for j in range(i + 1, len(replicas))
                    ]
                )
            else:
                mean_overlap = 1.0

            overlaps.append(mean_overlap)

            logger.debug(
                f"Density={density:.2f}, T={temp:.3f}, overlap={mean_overlap:.3f}"
            )

        # Find transition point as maximum derivative of overlap
        overlaps_array = np.array(overlaps)
        derivatives = np.diff(overlaps_array) / np.diff(densities)

        if len(derivatives) == 0:
            return densities[0]

        transition_idx = np.argmax(np.abs(derivatives))
        critical_density = densities[transition_idx]

        logger.info(f"Glass transition detected at density={critical_density:.2f}")

        return critical_density

    def analyze_energy_landscape(
        self,
        schedules: list[ReplicaSchedule],
    ) -> LandscapeAnalysis:
        """
        Analyze the energy landscape across multiple replica schedules.

        Maps the structure of the solution space by identifying:
        - Local minima (solution basins)
        - Energy barriers between basins
        - Frustration clusters (conflicting constraints)
        - Global properties of the landscape

        Args:
            schedules: List of replica schedules to analyze

        Returns:
            LandscapeAnalysis with detailed landscape characterization

        Example:
            >>> replicas = scheduler.generate_replica_schedules(n_replicas=50)
            >>> landscape = scheduler.analyze_energy_landscape(replicas)
            >>> print(f"Found {len(landscape.local_minima)} distinct solution basins")
        """
        if not schedules:
            return LandscapeAnalysis(global_minimum_energy=float("inf"))

        energies = [s.energy for s in schedules]
        global_min = min(energies)

        logger.info(f"Analyzing landscape from {len(schedules)} replica schedules")

        # Cluster schedules into basins using energy and overlap
        basins = self._identify_solution_basins(schedules)

        # Extract local minima (lowest energy in each basin)
        local_minima = [
            min(schedules[idx].energy for idx in basin_indices)
            for basin_indices in basins.values()
        ]

        # Estimate energy barriers between basins
        barriers = self._estimate_energy_barriers(schedules, basins)

        # Identify frustration clusters
        frustration_clusters = self._identify_frustration_clusters()

        # Estimate glass transition temperature
        glass_temp = self._estimate_glass_temperature(schedules)

        analysis = LandscapeAnalysis(
            global_minimum_energy=global_min,
            local_minima=sorted(local_minima),
            energy_barrier_heights=barriers,
            basin_sizes={
                basin_id: len(indices) for basin_id, indices in basins.items()
            },
            frustration_clusters=frustration_clusters,
            glass_transition_temp=glass_temp,
        )

        logger.info(
            f"Landscape: {len(local_minima)} basins, "
            f"Emin={global_min:.2f}, "
            f"Tg={glass_temp:.3f}"
        )

        return analysis

    def compute_replica_symmetry_analysis(
        self,
        replicas: list[ReplicaSchedule],
    ) -> ReplicaSymmetryAnalysis:
        """
        Analyze replica symmetry breaking (RSB) in the schedule ensemble.

        Computes the Parisi overlap matrix between all replica pairs and
        characterizes the degree of symmetry breaking. This reveals whether
        the system has:
        - Replica symmetry (RS): All replicas similar → single solution
        - One-step RSB: Replicas cluster into discrete groups
        - Full RSB: Continuous hierarchy of solutions (ultrametric structure)

        Args:
            replicas: List of replica schedules to analyze

        Returns:
            ReplicaSymmetryAnalysis with RSB characterization

        Example:
            >>> rsb = scheduler.compute_replica_symmetry_analysis(replicas)
            >>> if rsb.diversity_score > 0.7:
            ...     print("High diversity - many viable solutions available")
        """
        n = len(replicas)

        if n < 2:
            return ReplicaSymmetryAnalysis(
                parisi_overlap_matrix=np.array([]),
                rsb_order_parameter=0.0,
                diversity_score=0.0,
            )

        logger.info(f"Computing RSB analysis for {n} replicas")

        # Build Parisi overlap matrix
        overlap_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                if i == j:
                    overlap_matrix[i, j] = 1.0
                else:
                    overlap = self.compute_parisi_overlap(replicas[i], replicas[j])
                    overlap_matrix[i, j] = overlap
                    overlap_matrix[j, i] = overlap

        # Compute RSB order parameter (variance of overlap distribution)
        off_diagonal = overlap_matrix[np.triu_indices(n, k=1)]
        mean_overlap = np.mean(off_diagonal)
        overlap_variance = np.var(off_diagonal)

        # RSB order parameter: higher variance = more symmetry breaking
        rsb_parameter = min(1.0, overlap_variance * 4.0)  # Normalize to [0, 1]

        # Diversity score: inverse of mean overlap
        diversity_score = 1.0 - mean_overlap

        # Compute overlap distribution histogram
        overlap_hist, bin_edges = np.histogram(
            off_diagonal, bins=[0.0, 0.25, 0.5, 0.75, 1.0]
        )
        overlap_distribution = {
            "0.00-0.25": int(overlap_hist[0]),
            "0.25-0.50": int(overlap_hist[1]),
            "0.50-0.75": int(overlap_hist[2]),
            "0.75-1.00": int(overlap_hist[3]),
        }

        # Compute ultrametric distances (hierarchical clustering metric)
        ultrametric = self._compute_ultrametric_distances(overlap_matrix)

        analysis = ReplicaSymmetryAnalysis(
            parisi_overlap_matrix=overlap_matrix,
            rsb_order_parameter=rsb_parameter,
            diversity_score=diversity_score,
            ultrametric_distance=ultrametric,
            mean_overlap=mean_overlap,
            overlap_distribution=overlap_distribution,
        )

        logger.info(
            f"RSB: parameter={rsb_parameter:.3f}, "
            f"diversity={diversity_score:.3f}, "
            f"mean_overlap={mean_overlap:.3f}"
        )

        return analysis

    # -------------------------------------------------------------------------
    # Private helper methods
    # -------------------------------------------------------------------------

    def _build_interaction_matrix(self, constraints: list[Constraint]) -> None:
        """Build constraint interaction matrix (J_ij couplings)."""
        self._interaction_matrix = {}

        # For each pair of constraints, estimate coupling strength
        for i, c1 in enumerate(constraints):
            for j, c2 in enumerate(constraints):
                if i >= j:
                    continue

                # Estimate interaction by checking if constraints conflict
                # Positive = ferromagnetic (aligned), Negative = antiferromagnetic (conflicting)
                coupling = self._estimate_constraint_coupling(c1, c2)
                self._interaction_matrix[(i, j)] = coupling

    def _estimate_constraint_coupling(
        self,
        constraint1: Constraint,
        constraint2: Constraint,
    ) -> float:
        """
        Estimate coupling strength between two constraints.

        Positive coupling: Constraints are aligned (ferromagnetic)
        Negative coupling: Constraints conflict (antiferromagnetic)
        """
        # Heuristic: Constraints of different types often conflict
        type_map = {
            "equity": 0,
            "preference": 1,
            "capacity": 2,
            "duty_hours": 3,
            "call": 4,
        }

        t1 = type_map.get(constraint1.constraint_type.value, -1)
        t2 = type_map.get(constraint2.constraint_type.value, -1)

        if t1 == -1 or t2 == -1:
            return 0.0

        # Equity vs preference typically conflicts
        if (t1 == 0 and t2 == 1) or (t1 == 1 and t2 == 0):
            return -0.5

        # Same type usually aligns
        if t1 == t2:
            return 0.5

        # Default: weak alignment
        return 0.1

    def _thermal_sample_schedule(
        self,
        base_solution: SolverResult | None,
        replica_id: int,
    ) -> tuple[list[tuple[UUID, UUID, UUID | None]], float]:
        """
        Generate a schedule via thermal sampling (simulated annealing).

        Returns:
            (assignments, energy) tuple
        """
        # Start from base solution if provided, otherwise random
        if base_solution and base_solution.assignments:
            current_assignments = list(base_solution.assignments)
        else:
            current_assignments = self._random_feasible_schedule()

        current_energy = self._compute_energy(current_assignments)

        # Simulated annealing with thermal perturbations
        n_steps = 100
        for step in range(n_steps):
            # Propose a random move (swap, reassign, etc.)
            candidate_assignments = self._propose_move(current_assignments)
            candidate_energy = self._compute_energy(candidate_assignments)

            # Metropolis acceptance criterion
            delta_E = candidate_energy - current_energy
            accept_prob = np.exp(-delta_E / self.temperature)

            if delta_E < 0 or self.rng.random() < accept_prob:
                current_assignments = candidate_assignments
                current_energy = candidate_energy

        return current_assignments, current_energy

    def _random_feasible_schedule(self) -> list[tuple[UUID, UUID, UUID | None]]:
        """Generate a random feasible schedule."""
        assignments = []

        for block in self.context.blocks:
            # Randomly assign a resident to this block
            if self.context.residents:
                person = self.rng.choice(self.context.residents)
                template = (
                    self.rng.choice(self.context.templates)
                    if self.context.templates
                    else None
                )
                template_id = template.id if template else None

                assignments.append((person.id, block.id, template_id))

        return assignments

    def _propose_move(
        self,
        assignments: list[tuple[UUID, UUID, UUID | None]],
    ) -> list[tuple[UUID, UUID, UUID | None]]:
        """Propose a random modification to the schedule."""
        if not assignments:
            return assignments

        new_assignments = list(assignments)

        # Random move type
        move_type = self.rng.choice(["swap", "reassign", "template_change"])

        if move_type == "swap" and len(new_assignments) >= 2:
            # Swap two assignments
            i, j = self.rng.choice(len(new_assignments), size=2, replace=False)
            new_assignments[i], new_assignments[j] = (
                new_assignments[j],
                new_assignments[i],
            )

        elif move_type == "reassign" and self.context.residents:
            # Reassign a random block to a different resident
            idx = self.rng.integers(0, len(new_assignments))
            person_id, block_id, template_id = new_assignments[idx]
            new_person = self.rng.choice(self.context.residents)
            new_assignments[idx] = (new_person.id, block_id, template_id)

        elif move_type == "template_change" and self.context.templates:
            # Change template for a random assignment
            idx = self.rng.integers(0, len(new_assignments))
            person_id, block_id, _ = new_assignments[idx]
            new_template = self.rng.choice(self.context.templates)
            new_assignments[idx] = (person_id, block_id, new_template.id)

        return new_assignments

    def _compute_energy(
        self,
        assignments: list[tuple[UUID, UUID, UUID | None]],
    ) -> float:
        """
        Compute total energy (constraint violations) for a schedule.

        Lower energy = better schedule.
        """
        total_energy = 0.0

        # Validate against all constraints
        for constraint in self.constraints:
            result = constraint.validate(assignments, self.context)

            if not result.satisfied:
                # Hard constraint violation = high energy penalty
                if hasattr(constraint, "get_penalty"):
                    penalty = constraint.get_penalty()
                    if penalty == float("inf"):
                        penalty = 1000.0  # Cap for numerical stability
                    total_energy += penalty
                else:
                    total_energy += 100.0  # Default penalty

            # Add soft constraint penalties
            total_energy += result.penalty

        return total_energy

    def _compute_magnetization(
        self,
        assignments: list[tuple[UUID, UUID, UUID | None]],
    ) -> float:
        """
        Compute magnetization (alignment with soft constraints).

        Returns value in [-1, 1] where:
        - 1.0 = perfect alignment with soft constraints
        - 0.0 = neutral
        - -1.0 = maximum misalignment
        """
        if not assignments:
            return 0.0

        total_alignment = 0.0
        n_soft_constraints = 0

        for constraint in self.constraints:
            # Only consider soft constraints
            if hasattr(constraint, "weight"):
                result = constraint.validate(assignments, self.context)

                # Normalize penalty to [-1, 1] range
                normalized_penalty = min(1.0, result.penalty / 100.0)
                alignment = 1.0 - normalized_penalty

                total_alignment += alignment
                n_soft_constraints += 1

        if n_soft_constraints == 0:
            return 0.0

        return total_alignment / n_soft_constraints

    def _analyze_violations(
        self,
        assignments: list[tuple[UUID, UUID, UUID | None]],
    ) -> dict[str, float]:
        """Break down energy by constraint type."""
        breakdown: dict[str, float] = defaultdict(float)

        for constraint in self.constraints:
            result = constraint.validate(assignments, self.context)

            constraint_type = constraint.constraint_type.value
            breakdown[constraint_type] += result.penalty

        return dict(breakdown)

    def _identify_solution_basins(
        self,
        schedules: list[ReplicaSchedule],
    ) -> dict[int, list[int]]:
        """
        Cluster schedules into solution basins using energy and overlap.

        Returns:
            Dictionary mapping basin_id -> [schedule indices in that basin]
        """
        n = len(schedules)
        basins: dict[int, list[int]] = {}

        # Simple clustering: schedules with high overlap are in same basin
        visited = set()
        basin_id = 0

        for i in range(n):
            if i in visited:
                continue

            # Start new basin
            basin_members = [i]
            visited.add(i)

            # Find all schedules with high overlap to schedule i
            for j in range(n):
                if j in visited:
                    continue

                overlap = self.compute_parisi_overlap(schedules[i], schedules[j])
                if overlap > 0.7:  # Threshold for same basin
                    basin_members.append(j)
                    visited.add(j)

            basins[basin_id] = basin_members
            basin_id += 1

        return basins

    def _estimate_energy_barriers(
        self,
        schedules: list[ReplicaSchedule],
        basins: dict[int, list[int]],
    ) -> list[float]:
        """
        Estimate energy barriers between solution basins.

        Returns:
            List of barrier heights
        """
        barriers = []

        basin_ids = list(basins.keys())

        for i, basin_a_id in enumerate(basin_ids):
            for basin_b_id in basin_ids[i + 1 :]:
                # Find minimum energy in each basin
                min_energy_a = min(schedules[idx].energy for idx in basins[basin_a_id])
                min_energy_b = min(schedules[idx].energy for idx in basins[basin_b_id])

                # Barrier height approximation
                barrier = abs(min_energy_b - min_energy_a)
                barriers.append(barrier)

        return barriers

    def _identify_frustration_clusters(self) -> list[FrustrationCluster]:
        """Identify groups of conflicting constraints."""
        clusters: list[FrustrationCluster] = []

        if self._interaction_matrix is None:
            return clusters

        # Find strongly negative couplings (high frustration)
        conflicting_pairs = [
            (i, j, coupling)
            for (i, j), coupling in self._interaction_matrix.items()
            if coupling < -0.3
        ]

        if not conflicting_pairs:
            return clusters

        # Group into clusters (simplified: one cluster per conflicting pair)
        for i, j, coupling in conflicting_pairs[:5]:  # Limit to top 5
            c1 = self.constraints[i]
            c2 = self.constraints[j]

            cluster = FrustrationCluster(
                constraints=[c1.name, c2.name],
                frustration_index=abs(coupling),
                conflict_type=f"{c1.constraint_type.value}_vs_{c2.constraint_type.value}",
                resolution_suggestions=[
                    f"Reduce weight of {c1.name}",
                    f"Reduce weight of {c2.name}",
                    "Add intermediate constraint to mediate conflict",
                ],
            )

            clusters.append(cluster)

        return clusters

    def _estimate_glass_temperature(self, schedules: list[ReplicaSchedule]) -> float:
        """
        Estimate the glass transition temperature.

        Below this temperature, the system freezes into a rigid configuration.
        """
        if not schedules:
            return 0.0

        # Estimate from energy distribution
        energies = np.array([s.energy for s in schedules])
        energy_std = np.std(energies)

        # Tg ~ width of energy distribution
        glass_temp = energy_std / 2.0

        return glass_temp

    def _compute_ultrametric_distances(
        self,
        overlap_matrix: np.ndarray,
    ) -> dict[tuple[int, int], float]:
        """
        Compute ultrametric distances from overlap matrix.

        Ultrametricity is a signature of hierarchical organization in RSB.
        """
        n = len(overlap_matrix)
        distances: dict[tuple[int, int], float] = {}

        # Convert overlap to distance: d_ij = 1 - q_ij
        for i in range(n):
            for j in range(i + 1, n):
                distance = 1.0 - overlap_matrix[i, j]
                distances[(i, j)] = distance

        return distances
