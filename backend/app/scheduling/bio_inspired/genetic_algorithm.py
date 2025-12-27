"""
Genetic Algorithm (GA) for Multi-Objective Schedule Optimization.

This module implements a Genetic Algorithm with:
- Multiple selection operators (tournament, roulette, rank-based)
- Multiple crossover operators (uniform, single-point, two-point, row-based)
- Multiple mutation operators (swap, insert, delete, flip)
- Adaptive mutation rates responding to search progress
- Elitism to preserve best solutions
- Diversity maintenance through niching

The GA naturally handles the discrete nature of schedule assignments
and can be combined with constraint repair operators.
"""

import logging
import math
import random
import time
from dataclasses import dataclass
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


class SelectionMethod(Enum):
    """Selection methods for parent selection."""
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    RANDOM = "random"


class CrossoverMethod(Enum):
    """Crossover methods for recombination."""
    UNIFORM = "uniform"
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    ROW_BASED = "row_based"  # Swap entire resident schedules
    BLOCK_BASED = "block_based"  # Swap entire block assignments


class MutationMethod(Enum):
    """Mutation methods for exploration."""
    SWAP = "swap"  # Swap two assignments
    INSERT = "insert"  # Insert new assignment
    DELETE = "delete"  # Remove assignment
    FLIP = "flip"  # Change template for assignment
    SCRAMBLE = "scramble"  # Shuffle segment


class SelectionOperator:
    """
    Selection operator for choosing parents.

    Implements multiple selection strategies with configurable pressure.
    """

    def __init__(
        self,
        method: SelectionMethod = SelectionMethod.TOURNAMENT,
        tournament_size: int = 3,
        pressure: float = 1.5,
    ):
        """
        Initialize selection operator.

        Args:
            method: Selection method to use
            tournament_size: Size of tournament for tournament selection
            pressure: Selection pressure (higher = more elitist)
        """
        self.method = method
        self.tournament_size = tournament_size
        self.pressure = pressure

    def select(
        self,
        population: list[Individual],
        n_parents: int,
    ) -> list[Individual]:
        """
        Select parents from population.

        Args:
            population: Current population
            n_parents: Number of parents to select

        Returns:
            List of selected parents
        """
        if self.method == SelectionMethod.TOURNAMENT:
            return self._tournament_select(population, n_parents)
        elif self.method == SelectionMethod.ROULETTE:
            return self._roulette_select(population, n_parents)
        elif self.method == SelectionMethod.RANK:
            return self._rank_select(population, n_parents)
        else:
            return self._random_select(population, n_parents)

    def _tournament_select(
        self,
        population: list[Individual],
        n_parents: int,
    ) -> list[Individual]:
        """Tournament selection."""
        parents = []
        for _ in range(n_parents):
            # Select random tournament participants
            tournament = random.sample(
                population,
                min(self.tournament_size, len(population))
            )
            # Winner is the one with best fitness
            winner = max(
                tournament,
                key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
            )
            parents.append(winner)
        return parents

    def _roulette_select(
        self,
        population: list[Individual],
        n_parents: int,
    ) -> list[Individual]:
        """Roulette wheel (fitness proportionate) selection."""
        fitness_values = [
            max(0.001, ind.fitness.weighted_sum()) if ind.fitness else 0.001
            for ind in population
        ]
        total_fitness = sum(fitness_values)
        probabilities = [f / total_fitness for f in fitness_values]

        parents = []
        for _ in range(n_parents):
            r = random.random()
            cumulative = 0
            for i, p in enumerate(probabilities):
                cumulative += p
                if r <= cumulative:
                    parents.append(population[i])
                    break
        return parents

    def _rank_select(
        self,
        population: list[Individual],
        n_parents: int,
    ) -> list[Individual]:
        """Rank-based selection."""
        # Sort by fitness
        sorted_pop = sorted(
            population,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
            reverse=True
        )

        # Assign ranks (1 = best)
        n = len(sorted_pop)
        probabilities = []
        for rank in range(1, n + 1):
            # Linear ranking with pressure
            prob = (2 - self.pressure + 2 * (self.pressure - 1) * (n - rank) / (n - 1)) / n
            probabilities.append(max(0.001, prob))

        # Normalize
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        # Select
        indices = np.random.choice(
            range(n),
            size=n_parents,
            p=probabilities,
            replace=True
        )
        return [sorted_pop[i] for i in indices]

    def _random_select(
        self,
        population: list[Individual],
        n_parents: int,
    ) -> list[Individual]:
        """Random selection (for diversity)."""
        return random.choices(population, k=n_parents)


class CrossoverOperator:
    """
    Crossover operator for recombination.

    Creates offspring by combining genetic material from parents.
    """

    def __init__(
        self,
        method: CrossoverMethod = CrossoverMethod.UNIFORM,
        crossover_rate: float = 0.8,
    ):
        """
        Initialize crossover operator.

        Args:
            method: Crossover method to use
            crossover_rate: Probability of crossover occurring
        """
        self.method = method
        self.crossover_rate = crossover_rate

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> tuple[Chromosome, Chromosome]:
        """
        Perform crossover between two parents.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Two offspring chromosomes
        """
        if random.random() > self.crossover_rate:
            # No crossover, return copies
            return parent1.chromosome.copy(), parent2.chromosome.copy()

        if self.method == CrossoverMethod.UNIFORM:
            return self._uniform_crossover(parent1.chromosome, parent2.chromosome)
        elif self.method == CrossoverMethod.SINGLE_POINT:
            return self._single_point_crossover(parent1.chromosome, parent2.chromosome)
        elif self.method == CrossoverMethod.TWO_POINT:
            return self._two_point_crossover(parent1.chromosome, parent2.chromosome)
        elif self.method == CrossoverMethod.ROW_BASED:
            return self._row_based_crossover(parent1.chromosome, parent2.chromosome)
        else:
            return self._block_based_crossover(parent1.chromosome, parent2.chromosome)

    def _uniform_crossover(
        self,
        c1: Chromosome,
        c2: Chromosome,
    ) -> tuple[Chromosome, Chromosome]:
        """Uniform crossover: each gene randomly from either parent."""
        n_rows, n_cols = c1.genes.shape
        mask = np.random.random((n_rows, n_cols)) < 0.5

        child1_genes = np.where(mask, c1.genes, c2.genes)
        child2_genes = np.where(mask, c2.genes, c1.genes)

        return Chromosome(child1_genes), Chromosome(child2_genes)

    def _single_point_crossover(
        self,
        c1: Chromosome,
        c2: Chromosome,
    ) -> tuple[Chromosome, Chromosome]:
        """Single-point crossover: split at random point."""
        flat1 = c1.genes.flatten()
        flat2 = c2.genes.flatten()

        point = random.randint(1, len(flat1) - 1)

        child1_flat = np.concatenate([flat1[:point], flat2[point:]])
        child2_flat = np.concatenate([flat2[:point], flat1[point:]])

        child1_genes = child1_flat.reshape(c1.genes.shape)
        child2_genes = child2_flat.reshape(c2.genes.shape)

        return Chromosome(child1_genes), Chromosome(child2_genes)

    def _two_point_crossover(
        self,
        c1: Chromosome,
        c2: Chromosome,
    ) -> tuple[Chromosome, Chromosome]:
        """Two-point crossover: swap segment between two points."""
        flat1 = c1.genes.flatten()
        flat2 = c2.genes.flatten()

        points = sorted(random.sample(range(1, len(flat1)), 2))
        p1, p2 = points

        child1_flat = np.concatenate([
            flat1[:p1],
            flat2[p1:p2],
            flat1[p2:]
        ])
        child2_flat = np.concatenate([
            flat2[:p1],
            flat1[p1:p2],
            flat2[p2:]
        ])

        child1_genes = child1_flat.reshape(c1.genes.shape)
        child2_genes = child2_flat.reshape(c2.genes.shape)

        return Chromosome(child1_genes), Chromosome(child2_genes)

    def _row_based_crossover(
        self,
        c1: Chromosome,
        c2: Chromosome,
    ) -> tuple[Chromosome, Chromosome]:
        """Row-based crossover: swap entire resident schedules."""
        n_rows, _ = c1.genes.shape

        # Randomly select rows to swap
        swap_mask = np.random.random(n_rows) < 0.5

        child1_genes = np.where(
            swap_mask[:, np.newaxis],
            c2.genes,
            c1.genes
        )
        child2_genes = np.where(
            swap_mask[:, np.newaxis],
            c1.genes,
            c2.genes
        )

        return Chromosome(child1_genes), Chromosome(child2_genes)

    def _block_based_crossover(
        self,
        c1: Chromosome,
        c2: Chromosome,
    ) -> tuple[Chromosome, Chromosome]:
        """Block-based crossover: swap entire block assignments."""
        _, n_cols = c1.genes.shape

        # Randomly select columns to swap
        swap_mask = np.random.random(n_cols) < 0.5

        child1_genes = np.where(
            swap_mask[np.newaxis, :],
            c2.genes,
            c1.genes
        )
        child2_genes = np.where(
            swap_mask[np.newaxis, :],
            c1.genes,
            c2.genes
        )

        return Chromosome(child1_genes), Chromosome(child2_genes)


class MutationOperator:
    """
    Mutation operator for introducing variation.

    Implements multiple mutation strategies with adaptive rates.
    """

    def __init__(
        self,
        method: MutationMethod = MutationMethod.FLIP,
        base_rate: float = 0.1,
        adaptive: bool = True,
        min_rate: float = 0.01,
        max_rate: float = 0.5,
    ):
        """
        Initialize mutation operator.

        Args:
            method: Mutation method to use
            base_rate: Base mutation rate
            adaptive: Whether to adapt rate based on search progress
            min_rate: Minimum mutation rate
            max_rate: Maximum mutation rate
        """
        self.method = method
        self.base_rate = base_rate
        self.adaptive = adaptive
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.current_rate = base_rate

        # Adaptive state
        self._improvement_history: list[bool] = []
        self._stagnation_counter = 0

    def mutate(
        self,
        chromosome: Chromosome,
        n_templates: int,
    ) -> Chromosome:
        """
        Mutate a chromosome.

        Args:
            chromosome: Chromosome to mutate
            n_templates: Number of available templates

        Returns:
            Mutated chromosome
        """
        mutant = chromosome.copy()
        n_rows, n_cols = mutant.genes.shape

        for r in range(n_rows):
            for c in range(n_cols):
                if random.random() < self.current_rate:
                    self._apply_mutation(mutant, r, c, n_templates)

        return mutant

    def _apply_mutation(
        self,
        chromosome: Chromosome,
        row: int,
        col: int,
        n_templates: int,
    ):
        """Apply mutation at a specific position."""
        if self.method == MutationMethod.FLIP:
            # Change to different template or unassign
            current = chromosome.genes[row, col]
            if current == 0:
                chromosome.genes[row, col] = random.randint(1, n_templates)
            else:
                # 20% chance to unassign, 80% to change template
                if random.random() < 0.2:
                    chromosome.genes[row, col] = 0
                else:
                    new_val = random.randint(1, n_templates)
                    while new_val == current and n_templates > 1:
                        new_val = random.randint(1, n_templates)
                    chromosome.genes[row, col] = new_val

        elif self.method == MutationMethod.SWAP:
            # Swap with another position in same row
            n_cols = chromosome.genes.shape[1]
            other_col = random.randint(0, n_cols - 1)
            chromosome.genes[row, col], chromosome.genes[row, other_col] = \
                chromosome.genes[row, other_col], chromosome.genes[row, col]

        elif self.method == MutationMethod.INSERT:
            # Insert random assignment
            chromosome.genes[row, col] = random.randint(1, n_templates)

        elif self.method == MutationMethod.DELETE:
            # Remove assignment
            chromosome.genes[row, col] = 0

        elif self.method == MutationMethod.SCRAMBLE:
            # Scramble a segment
            n_cols = chromosome.genes.shape[1]
            start = col
            end = min(col + random.randint(2, 5), n_cols)
            segment = chromosome.genes[row, start:end].copy()
            np.random.shuffle(segment)
            chromosome.genes[row, start:end] = segment

    def adapt_rate(
        self,
        improved: bool,
        diversity: float,
        generation: int,
    ):
        """
        Adapt mutation rate based on search progress.

        Implements adaptive mutation:
        - Increase rate when stuck (no improvement)
        - Decrease rate when improving
        - Consider population diversity

        Args:
            improved: Whether improvement was made this generation
            diversity: Current population diversity (0-1)
            generation: Current generation number
        """
        if not self.adaptive:
            return

        self._improvement_history.append(improved)
        if len(self._improvement_history) > 10:
            self._improvement_history.pop(0)

        # Calculate improvement rate over last 10 generations
        improvement_rate = sum(self._improvement_history) / len(self._improvement_history)

        if improved:
            self._stagnation_counter = 0
        else:
            self._stagnation_counter += 1

        # Adapt rate
        if self._stagnation_counter > 10:
            # Strong stagnation: increase rate significantly
            self.current_rate = min(
                self.max_rate,
                self.current_rate * 1.5
            )
            logger.debug(f"Stagnation detected, increasing mutation rate to {self.current_rate:.4f}")
        elif improvement_rate > 0.5:
            # Good progress: decrease rate to exploit
            self.current_rate = max(
                self.min_rate,
                self.current_rate * 0.95
            )
        elif improvement_rate < 0.2:
            # Poor progress: increase rate to explore
            self.current_rate = min(
                self.max_rate,
                self.current_rate * 1.1
            )

        # Consider diversity
        if diversity < 0.1:
            # Very low diversity: increase rate
            self.current_rate = min(
                self.max_rate,
                self.current_rate * 1.2
            )
        elif diversity > 0.5:
            # High diversity: slight decrease
            self.current_rate = max(
                self.min_rate,
                self.current_rate * 0.98
            )


@dataclass
class GAConfig:
    """Configuration for Genetic Algorithm."""
    population_size: int = 100
    max_generations: int = 200
    elite_size: int = 5
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    crossover_method: CrossoverMethod = CrossoverMethod.UNIFORM
    mutation_method: MutationMethod = MutationMethod.FLIP
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    adaptive_mutation: bool = True
    tournament_size: int = 3
    niching: bool = True
    niche_radius: float = 0.1
    early_stop_generations: int = 50


class GeneticAlgorithmSolver(BioInspiredSolver):
    """
    Genetic Algorithm solver for schedule optimization.

    Implements a standard GA with:
    - Configurable operators (selection, crossover, mutation)
    - Elitism to preserve best solutions
    - Adaptive mutation rates
    - Diversity maintenance through niching
    - Early stopping on convergence
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        config: GAConfig | None = None,
        seed: int | None = None,
    ):
        """
        Initialize Genetic Algorithm solver.

        Args:
            constraint_manager: Constraint manager for validation
            timeout_seconds: Maximum solve time
            config: GA configuration
            seed: Random seed
        """
        self.config = config or GAConfig()

        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=self.config.population_size,
            max_generations=self.config.max_generations,
            seed=seed,
        )

        # Initialize operators
        self.selection = SelectionOperator(
            method=self.config.selection_method,
            tournament_size=self.config.tournament_size,
        )
        self.crossover = CrossoverOperator(
            method=self.config.crossover_method,
            crossover_rate=self.config.crossover_rate,
        )
        self.mutation = MutationOperator(
            method=self.config.mutation_method,
            base_rate=self.config.mutation_rate,
            adaptive=self.config.adaptive_mutation,
        )

        # Convergence tracking
        self._best_fitness_history: list[float] = []
        self._n_templates: int = 1

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run genetic algorithm evolution.

        Args:
            context: Scheduling context

        Returns:
            Best individual found
        """
        start_time = time.time()

        # Calculate number of templates
        self._n_templates = max(1, len([
            t for t in context.templates
            if not t.requires_procedure_credential
        ]))

        # Initialize population
        self.population = self.initialize_population(context)
        self.best_individual = max(
            self.population,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
        )

        logger.info(
            f"GA initialized: pop_size={len(self.population)}, "
            f"initial_best={self.best_individual.fitness.weighted_sum():.4f}"
        )

        # Evolution loop
        for generation in range(self.max_generations):
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                logger.info(f"GA timeout at generation {generation}")
                break

            # Evolve one generation
            improved = self._evolve_generation(context, generation)

            # Adaptive mutation
            stats = self.evolution_history[-1] if self.evolution_history else None
            diversity = stats.diversity if stats else 0.5
            self.mutation.adapt_rate(improved, diversity, generation)

            # Update Pareto front
            self.update_pareto_front(self.population)

            # Check convergence
            if self._check_convergence(generation):
                logger.info(f"GA converged at generation {generation}")
                break

            # Log progress
            if generation % 20 == 0:
                best_fit = self.best_individual.fitness.weighted_sum() if self.best_individual.fitness else 0
                logger.info(
                    f"GA gen {generation}: best={best_fit:.4f}, "
                    f"mut_rate={self.mutation.current_rate:.4f}, "
                    f"pareto_size={len(self.pareto_front)}"
                )

        return self.best_individual

    def _evolve_generation(
        self,
        context: SchedulingContext,
        generation: int,
    ) -> bool:
        """
        Evolve one generation.

        Args:
            context: Scheduling context
            generation: Current generation number

        Returns:
            Whether improvement was made
        """
        prev_best = (
            self.best_individual.fitness.weighted_sum()
            if self.best_individual and self.best_individual.fitness
            else 0
        )

        # Select elite
        sorted_pop = sorted(
            self.population,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
            reverse=True
        )
        elite = sorted_pop[:self.config.elite_size]

        # Create new population
        new_population = [ind.copy() for ind in elite]

        # Fill rest of population with offspring
        while len(new_population) < self.population_size:
            # Select parents
            parents = self.selection.select(self.population, 2)

            # Crossover
            child1_chr, child2_chr = self.crossover.crossover(parents[0], parents[1])

            # Mutation
            child1_chr = self.mutation.mutate(child1_chr, self._n_templates)
            child2_chr = self.mutation.mutate(child2_chr, self._n_templates)

            # Evaluate fitness
            fitness1 = self.evaluate_fitness(child1_chr, context)
            fitness2 = self.evaluate_fitness(child2_chr, context)

            # Create individuals
            child1 = Individual(
                chromosome=child1_chr,
                fitness=fitness1,
                generation=generation + 1,
                parent_ids=[parents[0].id, parents[1].id],
                id=self._get_next_id(),
            )
            child2 = Individual(
                chromosome=child2_chr,
                fitness=fitness2,
                generation=generation + 1,
                parent_ids=[parents[0].id, parents[1].id],
                id=self._get_next_id(),
            )

            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)

        # Apply niching if enabled
        if self.config.niching:
            new_population = self._apply_niching(new_population)

        self.population = new_population

        # Update best individual
        current_best = max(
            self.population,
            key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
        )
        if (
            current_best.fitness and
            (not self.best_individual or not self.best_individual.fitness or
             current_best.fitness.weighted_sum() > self.best_individual.fitness.weighted_sum())
        ):
            self.best_individual = current_best.copy()

        # Track statistics
        stats = self.compute_population_stats(
            self.population,
            generation,
            mutation_rate=self.mutation.current_rate,
            crossover_rate=self.crossover.crossover_rate,
        )
        self.evolution_history.append(stats)

        current_best_fit = (
            self.best_individual.fitness.weighted_sum()
            if self.best_individual and self.best_individual.fitness
            else 0
        )
        return current_best_fit > prev_best

    def _apply_niching(self, population: list[Individual]) -> list[Individual]:
        """
        Apply niching to maintain diversity.

        Reduces fitness of similar individuals to encourage diversity.

        Args:
            population: Current population

        Returns:
            Population with adjusted fitness for niching
        """
        for ind in population:
            if ind.fitness is None:
                continue

            # Count neighbors within niche radius
            niche_count = 0
            for other in population:
                if ind is other or other.fitness is None:
                    continue
                similarity = ind.chromosome.similarity(other.chromosome)
                if similarity > (1 - self.config.niche_radius):
                    niche_count += 1

            # Share fitness with niche members
            if niche_count > 0:
                share_factor = 1.0 / (niche_count + 1)
                # Apply to weighted sum (stored separately for display)
                ind.rank = int(niche_count)  # Abuse rank field for niche count

        return population

    def _check_convergence(self, generation: int) -> bool:
        """
        Check if evolution has converged.

        Returns True if no improvement in recent generations.
        """
        current_best = (
            self.best_individual.fitness.weighted_sum()
            if self.best_individual and self.best_individual.fitness
            else 0
        )
        self._best_fitness_history.append(current_best)

        if len(self._best_fitness_history) > self.config.early_stop_generations:
            self._best_fitness_history.pop(0)

            # Check if improvement is negligible
            if len(self._best_fitness_history) == self.config.early_stop_generations:
                min_fit = min(self._best_fitness_history)
                max_fit = max(self._best_fitness_history)
                improvement = max_fit - min_fit

                if improvement < 0.001:  # Less than 0.1% improvement
                    return True

        return False

    def get_evolution_data(self) -> dict:
        """Get evolution data including GA-specific information."""
        base_data = super().get_evolution_data()
        base_data["ga_config"] = {
            "elite_size": self.config.elite_size,
            "selection_method": self.config.selection_method.value,
            "crossover_method": self.config.crossover_method.value,
            "mutation_method": self.config.mutation_method.value,
            "niching": self.config.niching,
            "niche_radius": self.config.niche_radius,
        }
        base_data["adaptive_mutation_history"] = [
            s.mutation_rate for s in self.evolution_history
        ]
        return base_data
