"""
Base Classes for Bio-Inspired Optimization.

This module provides foundational abstractions for evolutionary and swarm-based
optimization algorithms. All bio-inspired solvers inherit from BioInspiredSolver.

Key Concepts:
- Chromosome: Encoding of a complete schedule as a genetic representation
- Individual: Chromosome + fitness values
- Population: Collection of individuals evolving over generations
- FitnessVector: Multi-objective fitness (fairness, preferences, learning goals)
"""

import logging
import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
from uuid import UUID

import numpy as np

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


class ObjectiveType(Enum):
    """Types of objectives for multi-objective optimization."""

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@dataclass
class FitnessVector:
    """
    Multi-objective fitness representation.

    Each bio-inspired solver optimizes multiple objectives simultaneously:
    - coverage: Maximize block assignment coverage
    - fairness: Minimize variance in workload distribution
    - preferences: Maximize preference satisfaction
    - learning_goals: Maximize educational objective alignment
    - acgme_compliance: Maximize compliance with ACGME rules
    - continuity: Maximize rotation continuity

    All values are normalized to [0, 1] for Pareto comparison.
    """

    coverage: float = 0.0
    fairness: float = 0.0
    preferences: float = 0.0
    learning_goals: float = 0.0
    acgme_compliance: float = 1.0
    continuity: float = 0.0

    # Objective directions (all maximized after normalization)
    _objectives: dict = field(
        default_factory=lambda: {
            "coverage": ObjectiveType.MAXIMIZE,
            "fairness": ObjectiveType.MAXIMIZE,  # Higher = more fair
            "preferences": ObjectiveType.MAXIMIZE,
            "learning_goals": ObjectiveType.MAXIMIZE,
            "acgme_compliance": ObjectiveType.MAXIMIZE,
            "continuity": ObjectiveType.MAXIMIZE,
        }
    )

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for vectorized operations."""
        return np.array(
            [
                self.coverage,
                self.fairness,
                self.preferences,
                self.learning_goals,
                self.acgme_compliance,
                self.continuity,
            ]
        )

    @classmethod
    def from_array(cls, arr: np.ndarray) -> "FitnessVector":
        """Create FitnessVector from numpy array."""
        return cls(
            coverage=float(arr[0]),
            fairness=float(arr[1]),
            preferences=float(arr[2]),
            learning_goals=float(arr[3]),
            acgme_compliance=float(arr[4]),
            continuity=float(arr[5]),
        )

    def dominates(self, other: "FitnessVector") -> bool:
        """
        Check if this solution Pareto-dominates another.

        A solution dominates another if it is:
        - At least as good in all objectives
        - Strictly better in at least one objective
        """
        self_arr = self.to_array()
        other_arr = other.to_array()

        at_least_as_good = np.all(self_arr >= other_arr)
        strictly_better = np.any(self_arr > other_arr)

        return at_least_as_good and strictly_better

    def weighted_sum(self, weights: dict[str, float] | None = None) -> float:
        """
        Compute weighted sum of objectives for single-objective optimization.

        Default weights emphasize ACGME compliance and coverage.
        """
        if weights is None:
            weights = {
                "coverage": 0.25,
                "fairness": 0.15,
                "preferences": 0.10,
                "learning_goals": 0.10,
                "acgme_compliance": 0.30,
                "continuity": 0.10,
            }

        return (
            weights.get("coverage", 0) * self.coverage
            + weights.get("fairness", 0) * self.fairness
            + weights.get("preferences", 0) * self.preferences
            + weights.get("learning_goals", 0) * self.learning_goals
            + weights.get("acgme_compliance", 0) * self.acgme_compliance
            + weights.get("continuity", 0) * self.continuity
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "coverage": self.coverage,
            "fairness": self.fairness,
            "preferences": self.preferences,
            "learning_goals": self.learning_goals,
            "acgme_compliance": self.acgme_compliance,
            "continuity": self.continuity,
            "weighted_sum": self.weighted_sum(),
        }


@dataclass
class Chromosome:
    """
    Genetic encoding of a complete schedule.

    The chromosome is a 2D matrix where:
    - Rows represent residents (indexed by resident_idx)
    - Columns represent blocks (indexed by block_idx)
    - Values are template indices (0 = unassigned, 1+ = template index)

    This encoding supports:
    - Efficient crossover operations (row-based, column-based, uniform)
    - Local mutations (swap, insert, delete assignments)
    - Constraint-aware repair operators
    """

    genes: np.ndarray  # Shape: (n_residents, n_blocks)

    def __post_init__(self):
        """Ensure genes array is proper type."""
        if not isinstance(self.genes, np.ndarray):
            self.genes = np.array(self.genes, dtype=np.int32)

    @classmethod
    def create_random(
        cls,
        n_residents: int,
        n_blocks: int,
        n_templates: int,
        density: float = 0.6,
        seed: int | None = None,
    ) -> "Chromosome":
        """
        Create a random chromosome with specified assignment density.

        Args:
            n_residents: Number of residents
            n_blocks: Number of blocks
            n_templates: Number of available templates
            density: Probability of assignment at each position
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)

        # Generate random assignments
        genes = np.zeros((n_residents, n_blocks), dtype=np.int32)

        for r in range(n_residents):
            for b in range(n_blocks):
                if np.random.random() < density:
                    # Assign a random template (1-indexed, 0 = unassigned)
                    genes[r, b] = np.random.randint(1, n_templates + 1)

        return cls(genes=genes)

    @classmethod
    def create_empty(cls, n_residents: int, n_blocks: int) -> "Chromosome":
        """Create an empty chromosome with no assignments."""
        return cls(genes=np.zeros((n_residents, n_blocks), dtype=np.int32))

    def copy(self) -> "Chromosome":
        """Create a deep copy of this chromosome."""
        return Chromosome(genes=self.genes.copy())

    def get_assignment(self, resident_idx: int, block_idx: int) -> int:
        """Get template index for a resident-block pair (0 = unassigned)."""
        return int(self.genes[resident_idx, block_idx])

    def set_assignment(self, resident_idx: int, block_idx: int, template_idx: int) -> None:
        """Set template index for a resident-block pair."""
        self.genes[resident_idx, block_idx] = template_idx

    def get_resident_assignments(self, resident_idx: int) -> np.ndarray:
        """Get all assignments for a resident."""
        return self.genes[resident_idx, :]

    def get_block_assignments(self, block_idx: int) -> np.ndarray:
        """Get all assignments for a block."""
        return self.genes[:, block_idx]

    def count_assignments(self) -> int:
        """Count total number of assignments."""
        return int(np.sum(self.genes > 0))

    def count_resident_assignments(self, resident_idx: int) -> int:
        """Count assignments for a specific resident."""
        return int(np.sum(self.genes[resident_idx, :] > 0))

    def count_block_assignments(self, block_idx: int) -> int:
        """Count assignments for a specific block."""
        return int(np.sum(self.genes[:, block_idx] > 0))

    def to_assignment_list(
        self,
        context: SchedulingContext,
    ) -> list[tuple[UUID, UUID, UUID | None]]:
        """
        Convert chromosome to assignment list.

        Returns:
            List of (person_id, block_id, template_id) tuples
        """
        assignments = []

        idx_to_resident = {v: k for k, v in context.resident_idx.items()}
        idx_to_block = {v: k for k, v in context.block_idx.items()}
        template_list = list(context.templates)

        n_residents, n_blocks = self.genes.shape

        for r_idx in range(n_residents):
            for b_idx in range(n_blocks):
                t_idx = int(self.genes[r_idx, b_idx])
                if t_idx > 0:  # 0 = unassigned
                    person_id = idx_to_resident.get(r_idx)
                    block_id = idx_to_block.get(b_idx)
                    # Template index is 1-based in chromosome
                    template_id = (
                        template_list[t_idx - 1].id
                        if 0 < t_idx <= len(template_list)
                        else None
                    )

                    if person_id and block_id:
                        assignments.append((person_id, block_id, template_id))

        return assignments

    @classmethod
    def from_assignment_list(
        cls,
        assignments: list[tuple[UUID, UUID, UUID | None]],
        context: SchedulingContext,
    ) -> "Chromosome":
        """
        Create chromosome from assignment list.

        Args:
            assignments: List of (person_id, block_id, template_id) tuples
            context: Scheduling context for index mapping
        """
        n_residents = len(context.residents)
        n_blocks = len(context.blocks)
        genes = np.zeros((n_residents, n_blocks), dtype=np.int32)

        template_to_idx = {t.id: i + 1 for i, t in enumerate(context.templates)}

        for person_id, block_id, template_id in assignments:
            r_idx = context.resident_idx.get(person_id)
            b_idx = context.block_idx.get(block_id)
            t_idx = template_to_idx.get(template_id, 0) if template_id else 0

            if r_idx is not None and b_idx is not None:
                genes[r_idx, b_idx] = t_idx

        return cls(genes=genes)

    def hamming_distance(self, other: "Chromosome") -> int:
        """Compute Hamming distance (number of differing positions)."""
        return int(np.sum(self.genes != other.genes))

    def similarity(self, other: "Chromosome") -> float:
        """Compute similarity (1 - normalized Hamming distance)."""
        total = self.genes.size
        if total == 0:
            return 1.0
        return 1.0 - (self.hamming_distance(other) / total)


@dataclass
class Individual:
    """
    An individual in the population with chromosome and fitness.

    Tracks:
    - Genetic representation (chromosome)
    - Multi-objective fitness (FitnessVector)
    - Pareto ranking and crowding distance for NSGA-II
    - Lineage information for genealogy tracking
    """

    chromosome: Chromosome
    fitness: FitnessVector | None = None
    rank: int = 0  # Pareto rank (0 = non-dominated)
    crowding_distance: float = 0.0
    generation: int = 0
    parent_ids: list[int] = field(default_factory=list)
    id: int = 0

    def __lt__(self, other: "Individual") -> bool:
        """Compare for sorting: lower rank better, higher crowding better."""
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.crowding_distance > other.crowding_distance

    def copy(self) -> "Individual":
        """Create a deep copy."""
        return Individual(
            chromosome=self.chromosome.copy(),
            fitness=FitnessVector(**self.fitness.to_dict()) if self.fitness else None,
            rank=self.rank,
            crowding_distance=self.crowding_distance,
            generation=self.generation,
            parent_ids=self.parent_ids.copy(),
            id=self.id,
        )


@dataclass
class PopulationStats:
    """Statistics for a population at a given generation."""

    generation: int
    population_size: int
    best_fitness: float
    worst_fitness: float
    mean_fitness: float
    std_fitness: float
    diversity: float  # Average pairwise distance
    pareto_front_size: int
    hypervolume: float  # Volume of dominated objective space
    convergence: float  # Distance to reference Pareto front

    # Objective-specific statistics
    best_coverage: float = 0.0
    best_fairness: float = 0.0
    best_acgme: float = 0.0

    # Evolution dynamics
    selection_pressure: float = 0.0  # Ratio of best to mean fitness
    mutation_rate: float = 0.0
    crossover_rate: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "generation": self.generation,
            "population_size": self.population_size,
            "best_fitness": self.best_fitness,
            "worst_fitness": self.worst_fitness,
            "mean_fitness": self.mean_fitness,
            "std_fitness": self.std_fitness,
            "diversity": self.diversity,
            "pareto_front_size": self.pareto_front_size,
            "hypervolume": self.hypervolume,
            "convergence": self.convergence,
            "best_coverage": self.best_coverage,
            "best_fairness": self.best_fairness,
            "best_acgme": self.best_acgme,
            "selection_pressure": self.selection_pressure,
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
        }


class BioInspiredSolver(BaseSolver, ABC):
    """
    Base class for bio-inspired optimization solvers.

    Provides common functionality for:
    - Population initialization
    - Fitness evaluation
    - Evolution tracking
    - Pareto front maintenance
    - Adaptive parameter control
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        population_size: int = 100,
        max_generations: int = 200,
        seed: int | None = None,
        objective_weights: dict[str, float] | None = None,
        track_evolution: bool = True,
    ):
        """
        Initialize bio-inspired solver.

        Args:
            constraint_manager: Constraint manager for validation
            timeout_seconds: Maximum solve time
            population_size: Number of individuals in population
            max_generations: Maximum number of generations
            seed: Random seed for reproducibility
            objective_weights: Weights for multi-objective scalarization
            track_evolution: Whether to track evolution history
        """
        super().__init__(constraint_manager, timeout_seconds)
        self.population_size = population_size
        self.max_generations = max_generations
        self.seed = seed or random.randint(0, 2**32 - 1)
        self.objective_weights = objective_weights
        self.track_evolution = track_evolution

        # State
        self.population: list[Individual] = []
        self.pareto_front: list[Individual] = []
        self.evolution_history: list[PopulationStats] = []
        self.best_individual: Individual | None = None
        self._next_id: int = 0
        self._context: SchedulingContext | None = None

        # Set random seeds
        random.seed(self.seed)
        np.random.seed(self.seed)

    def _get_next_id(self) -> int:
        """Get next unique individual ID."""
        id = self._next_id
        self._next_id += 1
        return id

    @abstractmethod
    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run the evolution process.

        Implemented by subclasses for specific algorithms.

        Returns:
            Best individual found
        """
        pass

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """
        Solve using bio-inspired optimization.

        Args:
            context: Scheduling context
            existing_assignments: Assignments to preserve

        Returns:
            SolverResult with optimized schedule
        """
        start_time = time.time()
        self._context = context

        # Filter to workday blocks
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        if not workday_blocks or not context.residents:
            return SolverResult(
                success=False,
                assignments=[],
                status="empty",
                solver_status="No blocks or residents to schedule",
            )

        logger.info(
            f"{self.__class__.__name__}: {len(context.residents)} residents, "
            f"{len(workday_blocks)} blocks, pop_size={self.population_size}"
        )

        # Run evolution
        try:
            best = self._evolve(context)
        except Exception as e:
            logger.error(f"Evolution error: {e}", exc_info=True)
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status=str(e),
            )

        runtime = time.time() - start_time

        if best is None:
            return SolverResult(
                success=False,
                assignments=[],
                status="infeasible",
                solver_status="No valid solution found",
                runtime_seconds=runtime,
            )

        # Convert to assignments
        assignments = best.chromosome.to_assignment_list(context)

        logger.info(
            f"{self.__class__.__name__}: Found {len(assignments)} assignments "
            f"(fitness={best.fitness.weighted_sum():.4f}) in {runtime:.2f}s"
        )

        return SolverResult(
            success=True,
            assignments=assignments,
            status="feasible",
            objective_value=best.fitness.weighted_sum() if best.fitness else 0.0,
            runtime_seconds=runtime,
            solver_status=f"{self.__class__.__name__}",
            random_seed=self.seed,
            statistics={
                "population_size": self.population_size,
                "generations": len(self.evolution_history),
                "pareto_front_size": len(self.pareto_front),
                "final_fitness": best.fitness.to_dict() if best.fitness else {},
                "evolution_history": [
                    s.to_dict() for s in self.evolution_history[-10:]
                ],
            },
        )

    def evaluate_fitness(
        self,
        chromosome: Chromosome,
        context: SchedulingContext,
    ) -> FitnessVector:
        """
        Evaluate multi-objective fitness of a chromosome.

        Args:
            chromosome: Schedule encoding to evaluate
            context: Scheduling context

        Returns:
            FitnessVector with all objective values
        """
        n_residents = len(context.residents)
        n_blocks = len([b for b in context.blocks if not b.is_weekend])
        n_templates = len(context.templates)

        if n_residents == 0 or n_blocks == 0:
            return FitnessVector()

        # Coverage: Proportion of possible assignments made
        total_possible = n_residents * n_blocks
        total_assigned = chromosome.count_assignments()
        coverage = total_assigned / total_possible if total_possible > 0 else 0.0

        # Fairness: 1 - normalized variance in resident workload
        resident_counts = np.array(
            [chromosome.count_resident_assignments(r) for r in range(n_residents)]
        )
        if len(resident_counts) > 1 and np.mean(resident_counts) > 0:
            cv = np.std(resident_counts) / np.mean(
                resident_counts
            )  # Coefficient of variation
            fairness = 1.0 / (1.0 + cv)  # Higher = more fair
        else:
            fairness = 1.0

        # ACGME Compliance: Check 80-hour rule approximation
        # Simplified: penalize if any resident exceeds threshold
        max_blocks_per_week = 13  # ~80 hours at 6 hours/block
        blocks_per_week = 10  # Approximate
        acgme_violations = 0

        for r in range(n_residents):
            assignments = chromosome.get_resident_assignments(r)
            # Check weekly chunks
            for week_start in range(0, n_blocks, blocks_per_week):
                week_end = min(week_start + blocks_per_week, n_blocks)
                week_count = np.sum(assignments[week_start:week_end] > 0)
                if week_count > max_blocks_per_week:
                    acgme_violations += 1

        max_violations = n_residents * (n_blocks // blocks_per_week + 1)
        acgme_compliance = 1.0 - (
            acgme_violations / max_violations if max_violations > 0 else 0
        )

        # Continuity: Reward consecutive assignments to same template
        continuity_score = 0
        total_transitions = 0

        for r in range(n_residents):
            assignments = chromosome.get_resident_assignments(r)
            for b in range(n_blocks - 1):
                if assignments[b] > 0 and assignments[b + 1] > 0:
                    total_transitions += 1
                    if assignments[b] == assignments[b + 1]:
                        continuity_score += 1

        continuity = (
            continuity_score / total_transitions if total_transitions > 0 else 1.0
        )

        # Preferences: Placeholder (would need preference data)
        preferences = 0.5  # Neutral

        # Learning Goals: Placeholder (would need curriculum data)
        learning_goals = 0.5  # Neutral

        return FitnessVector(
            coverage=coverage,
            fairness=fairness,
            preferences=preferences,
            learning_goals=learning_goals,
            acgme_compliance=acgme_compliance,
            continuity=continuity,
        )

    def initialize_population(
        self,
        context: SchedulingContext,
        density: float = 0.5,
    ) -> list[Individual]:
        """
        Initialize population with random chromosomes.

        Args:
            context: Scheduling context
            density: Assignment density for random chromosomes

        Returns:
            List of initialized individuals
        """
        n_residents = len(context.residents)
        n_blocks = len([b for b in context.blocks if not b.is_weekend])
        n_templates = len(
            [t for t in context.templates if not t.requires_procedure_credential]
        )

        population = []
        for i in range(self.population_size):
            # Vary density for diversity
            ind_density = density * (0.8 + 0.4 * random.random())

            chromosome = Chromosome.create_random(
                n_residents=n_residents,
                n_blocks=n_blocks,
                n_templates=max(1, n_templates),
                density=ind_density,
            )

            fitness = self.evaluate_fitness(chromosome, context)

            individual = Individual(
                chromosome=chromosome,
                fitness=fitness,
                generation=0,
                id=self._get_next_id(),
            )
            population.append(individual)

        return population

    def update_pareto_front(self, population: list[Individual]) -> None:
        """
        Update the Pareto front with non-dominated solutions.

        Args:
            population: Current population
        """
        candidates = population + self.pareto_front

        # Find non-dominated solutions
        non_dominated = []
        for ind in candidates:
            if ind.fitness is None:
                continue

            dominated = False
            for other in candidates:
                if other.fitness is None or ind is other:
                    continue
                if other.fitness.dominates(ind.fitness):
                    dominated = True
                    break

            if not dominated:
                # Check if already in non_dominated (by fitness)
                is_duplicate = any(
                    np.allclose(ind.fitness.to_array(), nd.fitness.to_array())
                    for nd in non_dominated
                    if nd.fitness is not None
                )
                if not is_duplicate:
                    non_dominated.append(ind.copy())

        self.pareto_front = non_dominated

    def compute_population_stats(
        self,
        population: list[Individual],
        generation: int,
        mutation_rate: float = 0.0,
        crossover_rate: float = 0.0,
    ) -> PopulationStats:
        """
        Compute statistics for the current population.

        Args:
            population: Current population
            generation: Current generation number
            mutation_rate: Current mutation rate
            crossover_rate: Current crossover rate

        Returns:
            PopulationStats for this generation
        """
        fitness_values = [
            ind.fitness.weighted_sum() for ind in population if ind.fitness is not None
        ]

        if not fitness_values:
            return PopulationStats(
                generation=generation,
                population_size=len(population),
                best_fitness=0.0,
                worst_fitness=0.0,
                mean_fitness=0.0,
                std_fitness=0.0,
                diversity=0.0,
                pareto_front_size=0,
                hypervolume=0.0,
                convergence=0.0,
            )

        best_fitness = max(fitness_values)
        worst_fitness = min(fitness_values)
        mean_fitness = np.mean(fitness_values)
        std_fitness = np.std(fitness_values)

        # Diversity: average pairwise similarity
        if len(population) > 1:
            sample_size = min(20, len(population))
            sample = random.sample(population, sample_size)
            similarities = []
            for i, ind1 in enumerate(sample):
                for ind2 in sample[i + 1 :]:
                    similarities.append(ind1.chromosome.similarity(ind2.chromosome))
            diversity = 1.0 - np.mean(similarities) if similarities else 0.0
        else:
            diversity = 0.0

        # Selection pressure
        selection_pressure = best_fitness / mean_fitness if mean_fitness > 0 else 1.0

        # Best objectives
        best_coverage = max(
            (ind.fitness.coverage for ind in population if ind.fitness), default=0.0
        )
        best_fairness = max(
            (ind.fitness.fairness for ind in population if ind.fitness), default=0.0
        )
        best_acgme = max(
            (ind.fitness.acgme_compliance for ind in population if ind.fitness),
            default=0.0,
        )

        # Hypervolume (simplified 2D projection)
        # Use coverage and fairness for visualization
        if self.pareto_front:
            # Reference point: worst possible
            ref_point = np.array([0.0, 0.0])
            hypervolume = self._compute_hypervolume_2d(
                [
                    (ind.fitness.coverage, ind.fitness.fairness)
                    for ind in self.pareto_front
                    if ind.fitness
                ],
                ref_point,
            )
        else:
            hypervolume = 0.0

        return PopulationStats(
            generation=generation,
            population_size=len(population),
            best_fitness=best_fitness,
            worst_fitness=worst_fitness,
            mean_fitness=mean_fitness,
            std_fitness=std_fitness,
            diversity=diversity,
            pareto_front_size=len(self.pareto_front),
            hypervolume=hypervolume,
            convergence=1.0 - diversity,  # Inverse of diversity
            best_coverage=best_coverage,
            best_fairness=best_fairness,
            best_acgme=best_acgme,
            selection_pressure=selection_pressure,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
        )

    def _compute_hypervolume_2d(
        self,
        points: list[tuple[float, float]],
        ref_point: np.ndarray,
    ) -> float:
        """
        Compute 2D hypervolume indicator.

        Args:
            points: List of (x, y) objective values
            ref_point: Reference point (worst possible)

        Returns:
            Hypervolume value
        """
        if not points:
            return 0.0

        # Sort by first objective
        sorted_points = sorted(points, key=lambda p: p[0], reverse=True)

        hypervolume = 0.0
        prev_y = ref_point[1]

        for x, y in sorted_points:
            if y > prev_y:
                hypervolume += (x - ref_point[0]) * (y - prev_y)
                prev_y = y

        return hypervolume

    def get_evolution_data(self) -> dict:
        """
        Get evolution data for export.

        Returns:
            Dictionary with evolution history and Pareto front
        """
        return {
            "algorithm": self.__class__.__name__,
            "parameters": {
                "population_size": self.population_size,
                "max_generations": self.max_generations,
                "seed": self.seed,
                "objective_weights": self.objective_weights,
            },
            "evolution_history": [s.to_dict() for s in self.evolution_history],
            "pareto_front": [
                {
                    "id": ind.id,
                    "fitness": ind.fitness.to_dict() if ind.fitness else {},
                    "rank": ind.rank,
                    "crowding_distance": ind.crowding_distance,
                }
                for ind in self.pareto_front
            ],
            "best_individual": {
                "id": self.best_individual.id if self.best_individual else None,
                "fitness": self.best_individual.fitness.to_dict()
                if self.best_individual and self.best_individual.fitness
                else {},
            }
            if self.best_individual
            else None,
        }
