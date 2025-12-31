"""
Ant Colony Optimization (ACO) for Rotation Path Finding.

This module implements ACO for finding optimal rotation sequences.
ACO is particularly suited for path-finding problems, viewing scheduling as:

- Resident's rotation sequence as a path through time
- Blocks as nodes in a graph
- Templates as edge types
- Pheromones indicate historically good choices

ACO mimics foraging behavior:
1. Ants construct solutions by walking through the graph
2. Pheromones are deposited on good paths
3. Future ants prefer paths with more pheromone
4. Evaporation prevents premature convergence

Applications in Scheduling:
- Finding educational rotation sequences (variety in learning)
- Balancing rotation distribution across residents
- Optimizing transition costs between rotation types
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
from app.scheduling.constraints import ConstraintManager, SchedulingContext

logger = logging.getLogger(__name__)


@dataclass
class AntPath:
    """
    Path constructed by an ant.

    Represents a complete rotation sequence for a resident.
    """

    resident_idx: int
    path: list[int]  # Sequence of template indices for each block
    fitness: float = 0.0
    pheromone_contribution: float = 0.0

    def to_chromosome_row(self) -> np.ndarray:
        """
        Convert path to chromosome row.

        Returns:
            np.ndarray: Integer array representing the sequence of template
                assignments for each block in the path.
        """
        return np.array(self.path, dtype=np.int32)

    @classmethod
    def from_chromosome_row(
        cls,
        resident_idx: int,
        row: np.ndarray,
    ) -> "AntPath":
        """
        Create path from chromosome row.

        Args:
            resident_idx: Index of the resident this path belongs to
            row: Chromosome row containing template assignments

        Returns:
            AntPath: New AntPath instance created from the chromosome row
        """
        return cls(
            resident_idx=resident_idx,
            path=row.tolist(),
        )


class PheromoneMatrix:
    """
    Pheromone matrix for ACO.

    The matrix represents learned preferences:
    - pheromone[r, b, t]: desirability of assigning template t to resident r at block b
    - pheromone[t1, t2]: desirability of transitioning from template t1 to t2
    """

    def __init__(
        self,
        n_residents: int,
        n_blocks: int,
        n_templates: int,
        initial_value: float = 1.0,
        evaporation_rate: float = 0.1,
        min_pheromone: float = 0.01,
        max_pheromone: float = 10.0,
    ):
        """
        Initialize pheromone matrix.

        Args:
            n_residents: Number of residents
            n_blocks: Number of blocks
            n_templates: Number of templates (0 = unassigned)
            initial_value: Initial pheromone level
            evaporation_rate: Pheromone evaporation rate (rho)
            min_pheromone: Minimum pheromone level (prevents stagnation)
            max_pheromone: Maximum pheromone level (prevents dominance)
        """
        self.n_residents = n_residents
        self.n_blocks = n_blocks
        self.n_templates = n_templates + 1  # Include 0 for unassigned
        self.evaporation_rate = evaporation_rate
        self.min_pheromone = min_pheromone
        self.max_pheromone = max_pheromone

        # Assignment pheromone: [resident, block, template]
        self.assignment = np.full(
            (n_residents, n_blocks, self.n_templates), initial_value, dtype=np.float64
        )

        # Transition pheromone: [from_template, to_template]
        self.transition = np.full(
            (self.n_templates, self.n_templates), initial_value, dtype=np.float64
        )

    def evaporate(self) -> None:
        """Apply pheromone evaporation."""
        self.assignment *= 1 - self.evaporation_rate
        self.transition *= 1 - self.evaporation_rate

        # Apply minimum
        self.assignment = np.maximum(self.assignment, self.min_pheromone)
        self.transition = np.maximum(self.transition, self.min_pheromone)

    def deposit(
        self,
        paths: list[AntPath],
        elite_factor: float = 1.0,
    ) -> None:
        """
        Deposit pheromone on paths.

        Args:
            paths: Paths constructed by ants
            elite_factor: Multiplier for elite paths
        """
        for path in paths:
            deposit_amount = path.pheromone_contribution * elite_factor

            prev_template = 0  # Start from "unassigned"
            for b_idx, template in enumerate(path.path):
                # Assignment pheromone
                self.assignment[path.resident_idx, b_idx, template] += deposit_amount

                # Transition pheromone
                self.transition[prev_template, template] += deposit_amount
                prev_template = template

        # Apply maximum
        self.assignment = np.minimum(self.assignment, self.max_pheromone)
        self.transition = np.minimum(self.transition, self.max_pheromone)

    def get_assignment_probability(
        self,
        resident_idx: int,
        block_idx: int,
        heuristic: np.ndarray | None = None,
        alpha: float = 1.0,
        beta: float = 2.0,
    ) -> np.ndarray:
        """
        Get probability distribution for template selection.

        Args:
            resident_idx: Resident index
            block_idx: Block index
            heuristic: Heuristic desirability for each template
            alpha: Pheromone importance
            beta: Heuristic importance

        Returns:
            Probability distribution over templates
        """
        pheromone = self.assignment[resident_idx, block_idx]

        if heuristic is None:
            heuristic = np.ones(self.n_templates)

        # Combine pheromone and heuristic
        combined = (pheromone**alpha) * (heuristic**beta)

        # Normalize to probability
        total = np.sum(combined)
        if total > 0:
            return combined / total
        else:
            return np.ones(self.n_templates) / self.n_templates

    def get_transition_probability(
        self,
        from_template: int,
        alpha: float = 1.0,
        beta: float = 2.0,
    ) -> np.ndarray:
        """
        Get probability distribution for template transition.

        Args:
            from_template: Current template
            alpha: Pheromone importance
            beta: Not used (for consistency)

        Returns:
            Probability distribution over next templates
        """
        pheromone = self.transition[from_template]

        # Normalize
        total = np.sum(pheromone)
        if total > 0:
            return pheromone / total
        else:
            return np.ones(self.n_templates) / self.n_templates

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Creates a summary of the pheromone matrix state for logging and
        analysis purposes.

        Returns:
            dict: Dictionary containing:
                - n_residents: Number of residents
                - n_blocks: Number of blocks
                - n_templates: Number of templates
                - evaporation_rate: Pheromone evaporation rate
                - assignment_mean: Mean assignment pheromone level
                - assignment_std: Std dev of assignment pheromones
                - transition_mean: Mean transition pheromone level
        """
        return {
            "n_residents": self.n_residents,
            "n_blocks": self.n_blocks,
            "n_templates": self.n_templates,
            "evaporation_rate": self.evaporation_rate,
            "assignment_mean": float(np.mean(self.assignment)),
            "assignment_std": float(np.std(self.assignment)),
            "transition_mean": float(np.mean(self.transition)),
        }


@dataclass
class ACOConfig:
    """Configuration for Ant Colony Optimization."""

    colony_size: int = 50  # Number of ants
    max_iterations: int = 200

    # ACO parameters
    alpha: float = 1.0  # Pheromone importance
    beta: float = 2.0  # Heuristic importance
    evaporation_rate: float = 0.1
    initial_pheromone: float = 1.0

    # Elite ant strategies
    use_elite: bool = True
    elite_count: int = 5
    elite_factor: float = 2.0

    # Pheromone bounds
    min_pheromone: float = 0.01
    max_pheromone: float = 10.0

    # Local search
    local_search: bool = True
    local_search_iterations: int = 5

    # Convergence
    early_stop_iterations: int = 30


class AntColonySolver(BioInspiredSolver):
    """
    ACO solver for rotation path optimization.

    Uses ant colony behavior to find optimal rotation sequences:
    1. Each ant constructs a complete schedule
    2. Ants follow pheromone trails and heuristic information
    3. Better solutions deposit more pheromone
    4. Colony converges to good solutions while maintaining exploration
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        config: ACOConfig | None = None,
        seed: int | None = None,
    ):
        """
        Initialize ACO solver.

        Args:
            constraint_manager: Constraint manager
            timeout_seconds: Maximum solve time
            config: ACO configuration
            seed: Random seed
        """
        self.config = config or ACOConfig()

        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=self.config.colony_size,
            max_generations=self.config.max_iterations,
            seed=seed,
        )

        # ACO state
        self.pheromone: PheromoneMatrix | None = None
        self.heuristic_matrix: np.ndarray | None = None
        self._n_templates: int = 1
        self._best_fitness_history: list[float] = []

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run ACO optimization.

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

        # Initialize pheromone matrix
        self.pheromone = PheromoneMatrix(
            n_residents=n_residents,
            n_blocks=n_blocks,
            n_templates=self._n_templates,
            initial_value=self.config.initial_pheromone,
            evaporation_rate=self.config.evaporation_rate,
            min_pheromone=self.config.min_pheromone,
            max_pheromone=self.config.max_pheromone,
        )

        # Build heuristic matrix
        self._build_heuristic(context, n_residents, n_blocks)

        # Initialize best solution
        best_chromosome = None
        best_fitness = float("-inf")

        logger.info(
            f"ACO initialized: colony_size={self.config.colony_size}, "
            f"n_residents={n_residents}, n_blocks={n_blocks}, "
            f"n_templates={self._n_templates}"
        )

        # Main ACO loop
        for iteration in range(self.config.max_iterations):
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                logger.info(f"ACO timeout at iteration {iteration}")
                break

            # Construct solutions with all ants
            ant_solutions = []
            for ant_id in range(self.config.colony_size):
                chromosome = self._construct_solution(context, n_residents, n_blocks)

                # Evaluate fitness
                fitness = self.evaluate_fitness(chromosome, context)
                weighted = fitness.weighted_sum()

                ant_solutions.append((chromosome, fitness, weighted))

                # Update best
                if weighted > best_fitness:
                    best_fitness = weighted
                    best_chromosome = chromosome.copy()

            # Apply local search to best solutions
            if self.config.local_search:
                top_k = sorted(ant_solutions, key=lambda x: x[2], reverse=True)[:5]
                for chrom, fit, weighted in top_k:
                    improved = self._local_search(chrom, context)
                    new_fit = self.evaluate_fitness(improved, context)
                    new_weighted = new_fit.weighted_sum()
                    if new_weighted > best_fitness:
                        best_fitness = new_weighted
                        best_chromosome = improved.copy()

            # Evaporate pheromone
            self.pheromone.evaporate()

            # Deposit pheromone
            self._deposit_pheromone(ant_solutions)

            # Elite ant deposition
            if self.config.use_elite and best_chromosome is not None:
                elite_path = self._chromosome_to_paths(best_chromosome)
                for path in elite_path:
                    path.pheromone_contribution = best_fitness
                self.pheromone.deposit(elite_path, self.config.elite_factor)

            # Track statistics
            self._track_iteration(iteration, ant_solutions, best_fitness)

            # Check convergence
            self._best_fitness_history.append(best_fitness)
            if self._check_convergence():
                logger.info(f"ACO converged at iteration {iteration}")
                break

            # Log progress
            if iteration % 20 == 0:
                logger.info(
                    f"ACO iter {iteration}: best={best_fitness:.4f}, "
                    f"pheromone_mean={np.mean(self.pheromone.assignment):.4f}"
                )

        # Create best individual
        if best_chromosome is not None:
            best_fit = self.evaluate_fitness(best_chromosome, context)
            self.best_individual = Individual(
                chromosome=best_chromosome,
                fitness=best_fit,
                id=self._get_next_id(),
            )
        else:
            # Fallback to random
            self.best_individual = Individual(
                chromosome=Chromosome.create_random(
                    n_residents, n_blocks, self._n_templates
                ),
                fitness=FitnessVector(),
                id=self._get_next_id(),
            )

        return self.best_individual

    def _build_heuristic(
        self,
        context: SchedulingContext,
        n_residents: int,
        n_blocks: int,
    ) -> None:
        """
        Build heuristic matrix for ant decisions.

        Heuristic encodes prior knowledge:
        - Availability constraints
        - Template capacity
        - Educational goals
        """
        self.heuristic_matrix = np.ones(
            (n_residents, n_blocks, self._n_templates + 1), dtype=np.float64
        )

        # Penalize unavailable slots
        for resident in context.residents:
            r_idx = context.resident_idx.get(resident.id)
            if r_idx is None:
                continue

            unavail = context.availability.get(resident.id, set())
            for b_idx in unavail:
                if 0 <= b_idx < n_blocks:
                    # Set all templates to low probability
                    self.heuristic_matrix[r_idx, b_idx, :] = 0.1

        # Boost unassigned to prevent over-scheduling
        self.heuristic_matrix[:, :, 0] *= 1.5

    def _construct_solution(
        self,
        context: SchedulingContext,
        n_residents: int,
        n_blocks: int,
    ) -> Chromosome:
        """
        Construct a solution using ant's probabilistic walk.

        Args:
            context: Scheduling context
            n_residents: Number of residents
            n_blocks: Number of blocks

        Returns:
            Constructed chromosome
        """
        genes = np.zeros((n_residents, n_blocks), dtype=np.int32)

        for r_idx in range(n_residents):
            prev_template = 0  # Start unassigned

            for b_idx in range(n_blocks):
                # Get probability distribution
                prob = self.pheromone.get_assignment_probability(
                    r_idx,
                    b_idx,
                    heuristic=self.heuristic_matrix[r_idx, b_idx],
                    alpha=self.config.alpha,
                    beta=self.config.beta,
                )

                # Consider transition preference
                trans_prob = self.pheromone.get_transition_probability(
                    prev_template,
                    alpha=self.config.alpha,
                )

                # Combine probabilities
                combined_prob = prob * trans_prob
                total = np.sum(combined_prob)
                if total > 0:
                    combined_prob /= total

                # Select template
                template = np.random.choice(len(combined_prob), p=combined_prob)

                genes[r_idx, b_idx] = template
                prev_template = template

        return Chromosome(genes=genes)

    def _local_search(
        self,
        chromosome: Chromosome,
        context: SchedulingContext,
    ) -> Chromosome:
        """
        Apply local search to improve a solution.

        Uses simple 2-opt style moves.
        """
        best = chromosome.copy()
        best_fitness = self.evaluate_fitness(best, context).weighted_sum()

        for _ in range(self.config.local_search_iterations):
            # Random swap within a resident's schedule
            n_residents, n_blocks = best.genes.shape

            r_idx = random.randint(0, n_residents - 1)
            b1 = random.randint(0, n_blocks - 1)
            b2 = random.randint(0, n_blocks - 1)

            if b1 != b2:
                # Try swap
                candidate = best.copy()
                candidate.genes[r_idx, b1], candidate.genes[r_idx, b2] = (
                    candidate.genes[r_idx, b2],
                    candidate.genes[r_idx, b1],
                )

                new_fitness = self.evaluate_fitness(candidate, context).weighted_sum()
                if new_fitness > best_fitness:
                    best = candidate
                    best_fitness = new_fitness

            # Try random flip
            r_idx = random.randint(0, n_residents - 1)
            b_idx = random.randint(0, n_blocks - 1)
            old_val = best.genes[r_idx, b_idx]
            new_val = random.randint(0, self._n_templates)

            if new_val != old_val:
                candidate = best.copy()
                candidate.genes[r_idx, b_idx] = new_val

                new_fitness = self.evaluate_fitness(candidate, context).weighted_sum()
                if new_fitness > best_fitness:
                    best = candidate
                    best_fitness = new_fitness

        return best

    def _chromosome_to_paths(self, chromosome: Chromosome) -> list[AntPath]:
        """
        Convert chromosome to list of ant paths.

        Extracts each resident's rotation sequence from the chromosome and
        creates an AntPath object for pheromone deposition.

        Args:
            chromosome: Schedule chromosome to convert

        Returns:
            list[AntPath]: One AntPath per resident, containing their
                complete rotation sequence.
        """
        paths = []
        for r_idx in range(chromosome.genes.shape[0]):
            path = AntPath(
                resident_idx=r_idx,
                path=chromosome.genes[r_idx].tolist(),
            )
            paths.append(path)
        return paths

    def _deposit_pheromone(
        self,
        solutions: list[tuple[Chromosome, FitnessVector, float]],
    ) -> None:
        """
        Deposit pheromone based on solution quality.

        Args:
            solutions: List of (chromosome, fitness, weighted_sum) tuples
        """
        # Sort by fitness
        sorted_solutions = sorted(solutions, key=lambda x: x[2], reverse=True)

        # Deposit for top solutions
        for rank, (chromosome, fitness, weighted) in enumerate(
            sorted_solutions[: self.config.elite_count]
        ):
            paths = self._chromosome_to_paths(chromosome)

            # Pheromone amount based on fitness and rank
            pheromone_amount = weighted / (rank + 1)

            for path in paths:
                path.pheromone_contribution = pheromone_amount

            self.pheromone.deposit(paths, elite_factor=1.0)

    def _track_iteration(
        self,
        iteration: int,
        solutions: list[tuple[Chromosome, FitnessVector, float]],
        best_fitness: float,
    ) -> None:
        """Track statistics for this iteration."""
        fitness_values = [s[2] for s in solutions]

        stats = PopulationStats(
            generation=iteration,
            population_size=len(solutions),
            best_fitness=best_fitness,
            worst_fitness=min(fitness_values),
            mean_fitness=np.mean(fitness_values),
            std_fitness=np.std(fitness_values),
            diversity=float(np.std(self.pheromone.assignment)),
            pareto_front_size=1,
            hypervolume=best_fitness,
            convergence=1.0 - float(np.std(fitness_values)),
        )
        self.evolution_history.append(stats)

    def _check_convergence(self) -> bool:
        """
        Check if ACO has converged.

        Examines recent best fitness history to determine if the algorithm
        has stagnated (no significant improvement).

        Returns:
            bool: True if improvement over last early_stop_iterations is less
                than 0.001, False otherwise or if insufficient history.

        Note:
            Requires at least config.early_stop_iterations of history to
            assess convergence.
        """
        if len(self._best_fitness_history) < self.config.early_stop_iterations:
            return False

        recent = self._best_fitness_history[-self.config.early_stop_iterations :]
        improvement = max(recent) - min(recent)

        return improvement < 0.001

    def get_pheromone_analysis(self) -> dict:
        """
        Analyze pheromone distribution for insights.

        Identifies high-pheromone regions (hotspots) and common transition
        patterns that emerged during optimization.

        Returns:
            dict: Analysis containing:
                - pheromone_matrix: Summary statistics
                - n_hotspots: Count of high-pheromone assignments
                - hotspot_examples: Sample hotspot coordinates
                - top_transitions: Most common template transitions

        Note:
            Returns empty dict if pheromone matrix hasn't been initialized.
        """
        if self.pheromone is None:
            return {}

        # Find hotspots (high pheromone)
        threshold = np.percentile(self.pheromone.assignment, 90)
        hotspots = np.argwhere(self.pheromone.assignment > threshold)

        # Find preferred transitions
        top_transitions = []
        for from_t in range(self.pheromone.n_templates):
            for to_t in range(self.pheromone.n_templates):
                if self.pheromone.transition[from_t, to_t] > 2.0:
                    top_transitions.append(
                        {
                            "from": from_t,
                            "to": to_t,
                            "pheromone": float(self.pheromone.transition[from_t, to_t]),
                        }
                    )

        return {
            "pheromone_matrix": self.pheromone.to_dict(),
            "n_hotspots": len(hotspots),
            "hotspot_examples": hotspots[:10].tolist() if len(hotspots) > 0 else [],
            "top_transitions": sorted(
                top_transitions, key=lambda x: x["pheromone"], reverse=True
            )[:10],
        }

    def get_evolution_data(self) -> dict:
        """
        Get evolution data including ACO-specific information.

        Returns:
            dict: Evolution data containing:
                - Base evolution data from parent class
                - aco_config: ACO-specific parameters
                - pheromone_analysis: Pheromone distribution insights

        Note:
            Extends the base class get_evolution_data with ACO-specific
            metrics and pheromone analysis.
        """
        base_data = super().get_evolution_data()

        base_data["aco_config"] = {
            "alpha": self.config.alpha,
            "beta": self.config.beta,
            "evaporation_rate": self.config.evaporation_rate,
            "use_elite": self.config.use_elite,
            "local_search": self.config.local_search,
        }

        base_data["pheromone_analysis"] = self.get_pheromone_analysis()

        return base_data
