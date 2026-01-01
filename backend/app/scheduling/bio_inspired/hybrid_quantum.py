"""
Hybrid GA-QUBO Pipeline for Quantum-Evolutionary Optimization.

This module combines genetic algorithms with QUBO quantum optimization:

1. GA evolves problem decompositions (which sub-problems to solve with QUBO)
2. QUBO solves sub-problems with quantum-inspired annealing
3. Solutions are recombined into complete schedules
4. Fitness guides evolution of decomposition strategies

This hybrid approach leverages:
- GA's global search and exploration capabilities
- QUBO's ability to find optimal solutions for well-structured sub-problems
- Decomposition strategies that learn which problems are quantum-suitable

Use Cases:
- Large problems that exceed QUBO capacity
- Problems with mixed constraint types (some better for GA, some for QUBO)
- Exploring different problem partitions
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import numpy as np

from app.scheduling.bio_inspired.base import (
    BioInspiredSolver,
    Chromosome,
    FitnessVector,
    Individual,
    PopulationStats,
)
from app.scheduling.bio_inspired.genetic_algorithm import (
    CrossoverMethod,
    CrossoverOperator,
    MutationMethod,
    MutationOperator,
    SelectionMethod,
    SelectionOperator,
)
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.quantum.qubo_solver import (
    QUBOFormulation,
    SimulatedQuantumAnnealingSolver,
)

logger = logging.getLogger(__name__)


class DecompositionStrategy(Enum):
    """Strategies for decomposing the problem."""

    BY_RESIDENT = "by_resident"  # Each resident as separate QUBO
    BY_BLOCK_WEEK = "by_block_week"  # Weekly blocks as QUBO
    BY_TEMPLATE = "by_template"  # Templates as separate problems
    ADAPTIVE = "adaptive"  # Evolved decomposition boundaries


@dataclass
class ProblemDecomposition:
    """
    A decomposition of the scheduling problem into sub-problems.

    The decomposition is encoded as a chromosome where:
    - Genes represent which sub-problem each (resident, block) pair belongs to
    - Each sub-problem is solved independently with QUBO
    - Solutions are merged to form complete schedule
    """

    # Decomposition matrix: [n_residents, n_blocks] -> sub-problem index
    partition: np.ndarray
    n_subproblems: int
    strategy: DecompositionStrategy

    # Sub-problem solutions
    subproblem_solutions: dict[int, np.ndarray] = field(default_factory=dict)
    subproblem_energies: dict[int, float] = field(default_factory=dict)

    # Performance metrics
    qubo_time: float = 0.0
    merge_time: float = 0.0
    total_energy: float = 0.0

    @classmethod
    def create_by_resident(
        cls,
        n_residents: int,
        n_blocks: int,
    ) -> "ProblemDecomposition":
        """Create decomposition where each resident is a sub-problem."""
        partition = np.zeros((n_residents, n_blocks), dtype=np.int32)
        for r_idx in range(n_residents):
            partition[r_idx, :] = r_idx
        return cls(
            partition=partition,
            n_subproblems=n_residents,
            strategy=DecompositionStrategy.BY_RESIDENT,
        )

    @classmethod
    def create_by_week(
        cls,
        n_residents: int,
        n_blocks: int,
        blocks_per_week: int = 10,
    ) -> "ProblemDecomposition":
        """Create decomposition where each week is a sub-problem."""
        partition = np.zeros((n_residents, n_blocks), dtype=np.int32)
        n_weeks = (n_blocks + blocks_per_week - 1) // blocks_per_week

        for b_idx in range(n_blocks):
            week = b_idx // blocks_per_week
            partition[:, b_idx] = week

        return cls(
            partition=partition,
            n_subproblems=n_weeks,
            strategy=DecompositionStrategy.BY_BLOCK_WEEK,
        )

    @classmethod
    def create_adaptive(
        cls,
        n_residents: int,
        n_blocks: int,
        n_subproblems: int = 10,
    ) -> "ProblemDecomposition":
        """Create random adaptive decomposition."""
        partition = np.random.randint(
            0, n_subproblems, size=(n_residents, n_blocks), dtype=np.int32
        )
        return cls(
            partition=partition,
            n_subproblems=n_subproblems,
            strategy=DecompositionStrategy.ADAPTIVE,
        )

    def get_subproblem_mask(self, subproblem_idx: int) -> np.ndarray:
        """Get boolean mask for positions in a sub-problem."""
        return self.partition == subproblem_idx

    def merge_solutions(self) -> np.ndarray:
        """Merge sub-problem solutions into complete solution."""
        if not self.subproblem_solutions:
            return np.zeros_like(self.partition)

        result = np.zeros_like(self.partition)
        for idx, solution in self.subproblem_solutions.items():
            mask = self.get_subproblem_mask(idx)
            result[mask] = solution[mask]

        return result

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "strategy": self.strategy.value,
            "n_subproblems": self.n_subproblems,
            "partition_shape": list(self.partition.shape),
            "qubo_time": self.qubo_time,
            "merge_time": self.merge_time,
            "total_energy": self.total_energy,
            "subproblem_energies": self.subproblem_energies,
        }


@dataclass
class HybridConfig:
    """Configuration for Hybrid GA-QUBO solver."""

    population_size: int = 50
    max_generations: int = 100

    # Decomposition
    decomposition_strategy: DecompositionStrategy = DecompositionStrategy.ADAPTIVE
    n_subproblems: int = 10
    min_subproblem_size: int = 5  # Minimum variables per QUBO

    # GA parameters
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elite_size: int = 3

    # QUBO parameters
    qubo_num_reads: int = 50
    qubo_num_sweeps: int = 500
    qubo_timeout: float = 5.0  # Per sub-problem

    # Migration (for island model)
    enable_migration: bool = True
    migration_interval: int = 10
    migration_size: int = 3
    n_islands: int = 4


class HybridGAQUBOSolver(BioInspiredSolver):
    """
    Hybrid solver combining GA and QUBO.

    The GA evolves problem decompositions while QUBO solves sub-problems.
    This leverages both evolutionary exploration and quantum-inspired
    optimization for a powerful hybrid approach.
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 600.0,
        config: HybridConfig | None = None,
        seed: int | None = None,
    ) -> None:
        """
        Initialize hybrid GA-QUBO solver.

        Args:
            constraint_manager: Constraint manager
            timeout_seconds: Maximum solve time
            config: Hybrid configuration
            seed: Random seed
        """
        self.config = config or HybridConfig()

        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=self.config.population_size,
            max_generations=self.config.max_generations,
            seed=seed,
        )

        # Initialize operators
        self.selection = SelectionOperator(
            method=SelectionMethod.TOURNAMENT,
            tournament_size=3,
        )
        self.crossover = CrossoverOperator(
            method=CrossoverMethod.UNIFORM,
            crossover_rate=self.config.crossover_rate,
        )
        self.mutation = MutationOperator(
            method=MutationMethod.FLIP,
            base_rate=self.config.mutation_rate,
        )

        # Islands for parallel populations
        self.islands: list[list[Individual]] = []
        self._n_templates: int = 1

        # Statistics
        self.qubo_stats: list[dict] = []

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run hybrid GA-QUBO evolution.

        Args:
            context: Scheduling context

        Returns:
            Best individual found
        """
        start_time = time.time()

        n_residents = len(context.residents)
        n_blocks = len([b for b in context.blocks if not b.is_weekend])
        self._n_templates = max(
            1,
            len([t for t in context.templates if not t.requires_procedure_credential]),
        )

        # Initialize islands
        self._initialize_islands(context, n_residents, n_blocks)

        logger.info(
            f"Hybrid GA-QUBO initialized: {self.config.n_islands} islands, "
            f"pop_per_island={self.config.population_size // self.config.n_islands}"
        )

        # Evolution loop
        for generation in range(self.config.max_generations):
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                logger.info(f"Hybrid timeout at generation {generation}")
                break

            # Evolve each island
            for island_idx, island in enumerate(self.islands):
                self._evolve_island(island, context, generation, n_residents, n_blocks)

            # Migration between islands
            if (
                self.config.enable_migration
                and generation > 0
                and generation % self.config.migration_interval == 0
            ):
                self._migrate_between_islands()

            # Update best individual
            self._update_best()

            # Track statistics
            self._track_generation(generation)

            # Log progress
            if generation % 10 == 0:
                best_fit = (
                    self.best_individual.fitness.weighted_sum()
                    if self.best_individual and self.best_individual.fitness
                    else 0
                )
                logger.info(
                    f"Hybrid gen {generation}: best={best_fit:.4f}, "
                    f"qubo_calls={len(self.qubo_stats)}"
                )

        return self.best_individual

    def _initialize_islands(
        self,
        context: SchedulingContext,
        n_residents: int,
        n_blocks: int,
    ) -> None:
        """Initialize island populations with different decomposition strategies."""
        self.islands = []
        pop_per_island = self.config.population_size // self.config.n_islands

        strategies = [
            DecompositionStrategy.BY_RESIDENT,
            DecompositionStrategy.BY_BLOCK_WEEK,
            DecompositionStrategy.ADAPTIVE,
            DecompositionStrategy.ADAPTIVE,  # Duplicate adaptive for diversity
        ]

        for island_idx in range(self.config.n_islands):
            island = []
            strategy = strategies[island_idx % len(strategies)]

            for _ in range(pop_per_island):
                # Create decomposition
                if strategy == DecompositionStrategy.BY_RESIDENT:
                    decomp = ProblemDecomposition.create_by_resident(
                        n_residents, n_blocks
                    )
                elif strategy == DecompositionStrategy.BY_BLOCK_WEEK:
                    decomp = ProblemDecomposition.create_by_week(n_residents, n_blocks)
                else:
                    decomp = ProblemDecomposition.create_adaptive(
                        n_residents, n_blocks, self.config.n_subproblems
                    )

                # Solve with QUBO
                chromosome = self._solve_decomposition(decomp, context)
                fitness = self.evaluate_fitness(chromosome, context)

                individual = Individual(
                    chromosome=chromosome,
                    fitness=fitness,
                    generation=0,
                    id=self._get_next_id(),
                )
                island.append(individual)

            self.islands.append(island)

        # Set initial best
        all_individuals = [ind for island in self.islands for ind in island]
        self.best_individual = max(
            all_individuals,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
        )

    def _evolve_island(
        self,
        island: list[Individual],
        context: SchedulingContext,
        generation: int,
        n_residents: int,
        n_blocks: int,
    ) -> None:
        """Evolve a single island population."""
        # Sort by fitness
        sorted_island = sorted(
            island,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
            reverse=True,
        )

        # Keep elite
        new_island = sorted_island[: self.config.elite_size]

        # Create offspring
        while len(new_island) < len(island):
            # Select parents
            parents = self.selection.select(island, 2)

            # Crossover decomposition partitions
            # Treat partition as chromosome for crossover
            parent1_decomp = self._chromosome_to_decomposition(
                parents[0].chromosome, n_residents, n_blocks
            )
            parent2_decomp = self._chromosome_to_decomposition(
                parents[1].chromosome, n_residents, n_blocks
            )

            # Crossover on partition genes
            child1_partition = self._crossover_partitions(
                parent1_decomp.partition,
                parent2_decomp.partition,
            )
            child2_partition = self._crossover_partitions(
                parent2_decomp.partition,
                parent1_decomp.partition,
            )

            # Mutation
            child1_partition = self._mutate_partition(
                child1_partition,
                self.config.n_subproblems,
            )
            child2_partition = self._mutate_partition(
                child2_partition,
                self.config.n_subproblems,
            )

            # Create decompositions and solve
            child1_decomp = ProblemDecomposition(
                partition=child1_partition,
                n_subproblems=self.config.n_subproblems,
                strategy=DecompositionStrategy.ADAPTIVE,
            )
            child2_decomp = ProblemDecomposition(
                partition=child2_partition,
                n_subproblems=self.config.n_subproblems,
                strategy=DecompositionStrategy.ADAPTIVE,
            )

            # Solve with QUBO
            child1_chr = self._solve_decomposition(child1_decomp, context)
            child2_chr = self._solve_decomposition(child2_decomp, context)

            # Evaluate
            fitness1 = self.evaluate_fitness(child1_chr, context)
            fitness2 = self.evaluate_fitness(child2_chr, context)

            # Create individuals
            new_island.append(
                Individual(
                    chromosome=child1_chr,
                    fitness=fitness1,
                    generation=generation + 1,
                    parent_ids=[parents[0].id, parents[1].id],
                    id=self._get_next_id(),
                )
            )

            if len(new_island) < len(island):
                new_island.append(
                    Individual(
                        chromosome=child2_chr,
                        fitness=fitness2,
                        generation=generation + 1,
                        parent_ids=[parents[0].id, parents[1].id],
                        id=self._get_next_id(),
                    )
                )

        # Replace island population
        island.clear()
        island.extend(new_island)

    def _solve_decomposition(
        self,
        decomp: ProblemDecomposition,
        context: SchedulingContext,
    ) -> Chromosome:
        """
        Solve a problem decomposition using QUBO for each sub-problem.

        Args:
            decomp: Problem decomposition
            context: Scheduling context

        Returns:
            Complete chromosome from merged sub-solutions
        """
        start_time = time.time()
        n_residents, n_blocks = decomp.partition.shape

        for subproblem_idx in range(decomp.n_subproblems):
            mask = decomp.get_subproblem_mask(subproblem_idx)
            n_vars = np.sum(mask)

            if n_vars < self.config.min_subproblem_size:
                # Too small for QUBO, use random assignment
                solution = np.random.randint(
                    0,
                    self._n_templates + 1,
                    size=(n_residents, n_blocks),
                    dtype=np.int32,
                )
                decomp.subproblem_solutions[subproblem_idx] = solution
                decomp.subproblem_energies[subproblem_idx] = 0.0
                continue

            # Solve sub-problem with QUBO
            try:
                solution, energy = self._solve_subproblem_qubo(
                    mask, context, n_residents, n_blocks
                )
                decomp.subproblem_solutions[subproblem_idx] = solution
                decomp.subproblem_energies[subproblem_idx] = energy
            except Exception as e:
                logger.warning(f"QUBO sub-problem {subproblem_idx} failed: {e}")
                # Fallback to random
                solution = np.random.randint(
                    0,
                    self._n_templates + 1,
                    size=(n_residents, n_blocks),
                    dtype=np.int32,
                )
                decomp.subproblem_solutions[subproblem_idx] = solution
                decomp.subproblem_energies[subproblem_idx] = 0.0

        decomp.qubo_time = time.time() - start_time

        # Merge solutions
        merge_start = time.time()
        merged = decomp.merge_solutions()
        decomp.merge_time = time.time() - merge_start

        decomp.total_energy = sum(decomp.subproblem_energies.values())

        # Track QUBO stats
        self.qubo_stats.append(decomp.to_dict())

        return Chromosome(genes=merged)

    def _solve_subproblem_qubo(
        self,
        mask: np.ndarray,
        context: SchedulingContext,
        n_residents: int,
        n_blocks: int,
    ) -> tuple[np.ndarray, float]:
        """
        Solve a sub-problem using QUBO.

        Args:
            mask: Boolean mask for sub-problem positions
            context: Scheduling context
            n_residents: Total residents
            n_blocks: Total blocks

        Returns:
            (solution_matrix, energy)
        """
        # Build mini-QUBO for this sub-problem
        # Map positions to flat indices
        positions = np.argwhere(mask)
        n_vars = len(positions)

        if n_vars == 0:
            return np.zeros((n_residents, n_blocks), dtype=np.int32), 0.0

        # Create QUBO matrix for sub-problem
        # Each position can be assigned one of n_templates
        total_vars = n_vars * self._n_templates
        Q = {}

        # Coverage objective (negative = want x=1)
        for i in range(total_vars):
            Q[(i, i)] = -1.0

        # One template per position constraint
        for pos_idx in range(n_vars):
            start = pos_idx * self._n_templates
            for t1 in range(self._n_templates):
                for t2 in range(t1 + 1, self._n_templates):
                    i1 = start + t1
                    i2 = start + t2
                    Q[(i1, i2)] = 100.0  # Penalty for multiple templates

        # Solve with simulated annealing
        sample = self._simulated_annealing(Q, total_vars)

        # Decode solution
        solution = np.zeros((n_residents, n_blocks), dtype=np.int32)
        energy = 0.0

        for pos_idx, (r_idx, b_idx) in enumerate(positions):
            start = pos_idx * self._n_templates
            for t_idx in range(self._n_templates):
                if sample.get(start + t_idx, 0) == 1:
                    solution[r_idx, b_idx] = t_idx + 1  # 1-indexed
                    energy += Q.get((start + t_idx, start + t_idx), 0)
                    break

        return solution, energy

    def _simulated_annealing(
        self,
        Q: dict,
        n_vars: int,
    ) -> dict[int, int]:
        """Run simulated annealing on QUBO."""
        # Simple SA implementation
        sample = {i: random.randint(0, 1) for i in range(n_vars)}

        def compute_energy(s: dict[int, int]) -> float:
            e = 0.0
            for (i, j), coef in Q.items():
                if i == j:
                    e += coef * s.get(i, 0)
                else:
                    e += coef * s.get(i, 0) * s.get(j, 0)
            return e

        energy = compute_energy(sample)
        best_sample = sample.copy()
        best_energy = energy

        for sweep in range(self.config.qubo_num_sweeps):
            temp = 1.0 - sweep / self.config.qubo_num_sweeps
            temp = max(0.01, temp)

            for i in range(n_vars):
                # Try flip
                old_val = sample[i]
                sample[i] = 1 - old_val

                new_energy = compute_energy(sample)
                delta = new_energy - energy

                if delta < 0 or random.random() < math.exp(-delta / temp):
                    energy = new_energy
                    if energy < best_energy:
                        best_sample = sample.copy()
                        best_energy = energy
                else:
                    sample[i] = old_val

        return best_sample

    def _chromosome_to_decomposition(
        self,
        chromosome: Chromosome,
        n_residents: int,
        n_blocks: int,
    ) -> ProblemDecomposition:
        """Convert chromosome back to decomposition (extract partition pattern)."""
        # Use template values modulo n_subproblems as partition
        partition = chromosome.genes % self.config.n_subproblems
        return ProblemDecomposition(
            partition=partition.astype(np.int32),
            n_subproblems=self.config.n_subproblems,
            strategy=DecompositionStrategy.ADAPTIVE,
        )

    def _crossover_partitions(
        self,
        partition1: np.ndarray,
        partition2: np.ndarray,
    ) -> np.ndarray:
        """Crossover two partition matrices."""
        if random.random() > self.config.crossover_rate:
            return partition1.copy()

        # Uniform crossover
        mask = np.random.random(partition1.shape) < 0.5
        return np.where(mask, partition1, partition2)

    def _mutate_partition(
        self,
        partition: np.ndarray,
        n_subproblems: int,
    ) -> np.ndarray:
        """Mutate partition matrix."""
        mutated = partition.copy()
        mutation_mask = np.random.random(partition.shape) < self.config.mutation_rate

        # Random reassignment for mutated positions
        mutated[mutation_mask] = np.random.randint(
            0, n_subproblems, size=np.sum(mutation_mask)
        )

        return mutated

    def _migrate_between_islands(self) -> None:
        """Migrate best individuals between islands."""
        # Ring topology: island i sends to island (i+1) % n
        migrants = []

        for island in self.islands:
            sorted_island = sorted(
                island,
                key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
                reverse=True,
            )
            migrants.append(
                [ind.copy() for ind in sorted_island[: self.config.migration_size]]
            )

        # Receive migrants from previous island
        for i, island in enumerate(self.islands):
            from_island = (i - 1) % len(self.islands)
            # Replace worst individuals with migrants
            island.sort(
                key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
            )
            for j, migrant in enumerate(migrants[from_island]):
                if j < len(island):
                    island[j] = migrant

        logger.debug(f"Migration complete: {self.config.migration_size} per island")

    def _update_best(self) -> None:
        """Update best individual across all islands."""
        all_individuals = [ind for island in self.islands for ind in island]
        current_best = max(
            all_individuals,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
        )

        if (
            not self.best_individual
            or not self.best_individual.fitness
            or (
                current_best.fitness
                and current_best.fitness.weighted_sum()
                > self.best_individual.fitness.weighted_sum()
            )
        ):
            self.best_individual = current_best.copy()

    def _track_generation(self, generation: int) -> None:
        """Track statistics for this generation."""
        all_individuals = [ind for island in self.islands for ind in island]
        fitness_values = [
            ind.fitness.weighted_sum() for ind in all_individuals if ind.fitness
        ]

        stats = PopulationStats(
            generation=generation,
            population_size=len(all_individuals),
            best_fitness=max(fitness_values) if fitness_values else 0,
            worst_fitness=min(fitness_values) if fitness_values else 0,
            mean_fitness=np.mean(fitness_values) if fitness_values else 0,
            std_fitness=np.std(fitness_values) if fitness_values else 0,
            diversity=0.0,  # Would need chromosome comparison
            pareto_front_size=1,
            hypervolume=max(fitness_values) if fitness_values else 0,
            convergence=0.0,
        )
        self.evolution_history.append(stats)

    def get_evolution_data(self) -> dict:
        """Get evolution data including hybrid-specific information."""
        base_data = super().get_evolution_data()

        base_data["hybrid_config"] = {
            "decomposition_strategy": self.config.decomposition_strategy.value,
            "n_subproblems": self.config.n_subproblems,
            "n_islands": self.config.n_islands,
            "enable_migration": self.config.enable_migration,
        }

        base_data["qubo_statistics"] = {
            "total_calls": len(self.qubo_stats),
            "avg_qubo_time": (
                np.mean([s["qubo_time"] for s in self.qubo_stats])
                if self.qubo_stats
                else 0
            ),
            "avg_energy": (
                np.mean([s["total_energy"] for s in self.qubo_stats])
                if self.qubo_stats
                else 0
            ),
        }

        base_data["island_stats"] = [
            {
                "island_idx": i,
                "size": len(island),
                "best_fitness": max(
                    (ind.fitness.weighted_sum() for ind in island if ind.fitness),
                    default=0,
                ),
            }
            for i, island in enumerate(self.islands)
        ]

        return base_data
