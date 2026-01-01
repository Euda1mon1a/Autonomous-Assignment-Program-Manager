"""
NSGA-II: Non-dominated Sorting Genetic Algorithm II for Pareto Front Discovery.

This module implements the NSGA-II algorithm, the gold standard for
multi-objective evolutionary optimization. It discovers Pareto-optimal
trade-offs between competing objectives:

1. Fairness vs Coverage: More coverage may mean less fair distribution
2. Preferences vs ACGME Compliance: Resident preferences vs regulatory rules
3. Learning Goals vs Continuity: Educational variety vs rotation stability

Key Features:
- Fast non-dominated sorting (O(MN²) where M=objectives, N=population)
- Crowding distance for diversity preservation
- Elitist selection combining parents and offspring
- No scalarization required - finds full Pareto front
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from app.scheduling.bio_inspired.base import (
    BioInspiredSolver,
    Chromosome,
    FitnessVector,
    Individual,
    PopulationStats,
)
from app.scheduling.bio_inspired.constants import (
    NSGA2_DEFAULT_POPULATION_SIZE,
    NSGA2_DEFAULT_MAX_GENERATIONS,
    NSGA2_DEFAULT_CROSSOVER_RATE,
    NSGA2_DEFAULT_MUTATION_RATE,
    NSGA2_DEFAULT_TOURNAMENT_SIZE,
    NSGA2_EARLY_STOP_GENERATIONS,
    NSGA2_CONVERGENCE_THRESHOLD,
    NSGA2_LOG_INTERVAL,
    NSGA2_TOP_RISK_RESIDENTS,
)
from app.scheduling.bio_inspired.genetic_algorithm import (
    CrossoverMethod,
    CrossoverOperator,
    MutationMethod,
    MutationOperator,
    SelectionMethod,
)
from app.scheduling.constraints import ConstraintManager, SchedulingContext

logger = logging.getLogger(__name__)


@dataclass
class ParetoFront:
    """
    Pareto front representation and analysis.

    The Pareto front contains all non-dominated solutions where no solution
    is strictly better than another in all objectives.
    """

    individuals: list[Individual] = field(default_factory=list)
    generation: int = 0

    def add(self, individual: Individual) -> None:
        """Add individual if it's non-dominated."""
        # Check if dominated by any existing member
        for existing in self.individuals:
            if existing.fitness and individual.fitness:
                if existing.fitness.dominates(individual.fitness):
                    return  # Dominated, don't add

        # Remove any existing members dominated by new individual
        self.individuals = [
            ind
            for ind in self.individuals
            if not (
                individual.fitness
                and ind.fitness
                and individual.fitness.dominates(ind.fitness)
            )
        ]

        # Check for duplicates (same fitness values)
        if individual.fitness:
            for existing in self.individuals:
                if existing.fitness:
                    if np.allclose(
                        individual.fitness.to_array(), existing.fitness.to_array()
                    ):
                        return  # Already have this point

        self.individuals.append(individual)

    def get_extreme_solutions(self) -> dict[str, Individual | None]:
        """Get solutions that are extreme in each objective."""
        if not self.individuals:
            return {}

        objectives = [
            "coverage",
            "fairness",
            "preferences",
            "learning_goals",
            "acgme_compliance",
            "continuity",
        ]
        extremes = {}

        for obj in objectives:
            best = max(
                self.individuals,
                key=lambda ind: getattr(ind.fitness, obj) if ind.fitness else 0,
            )
            extremes[f"best_{obj}"] = best

        return extremes

    def get_knee_point(self) -> Individual | None:
        """
        Find the knee point of the Pareto front.

        The knee point is the solution with maximum "curvature" -
        representing the best trade-off between objectives.
        """
        if len(self.individuals) < 3:
            return self.individuals[0] if self.individuals else None

        # Use coverage and fairness for 2D knee detection
        points = [
            (ind.fitness.coverage, ind.fitness.fairness)
            for ind in self.individuals
            if ind.fitness
        ]

        if len(points) < 3:
            return self.individuals[0]

        # Sort by first objective
        sorted_indices = sorted(range(len(points)), key=lambda i: points[i][0])

        # Find point with maximum perpendicular distance from line
        # connecting first and last points
        first = np.array(points[sorted_indices[0]])
        last = np.array(points[sorted_indices[-1]])
        line_vec = last - first
        line_len = np.linalg.norm(line_vec)

        if line_len < 1e-10:
            return self.individuals[sorted_indices[len(sorted_indices) // 2]]

        line_unit = line_vec / line_len

        max_dist = 0
        knee_idx = sorted_indices[len(sorted_indices) // 2]

        for i in sorted_indices[1:-1]:
            point = np.array(points[i])
            proj = np.dot(point - first, line_unit) * line_unit + first
            dist = np.linalg.norm(point - proj)

            if dist > max_dist:
                max_dist = dist
                knee_idx = i

        return self.individuals[knee_idx]

    def compute_spread(self) -> float:
        """
        Compute spread metric of the Pareto front.

        Spread measures the extent of the front across the objective space.
        """
        if len(self.individuals) < 2:
            return 0.0

        # Get objective arrays
        objectives = np.array(
            [ind.fitness.to_array() for ind in self.individuals if ind.fitness]
        )

        if len(objectives) < 2:
            return 0.0

        # Compute range in each objective
        ranges = np.max(objectives, axis=0) - np.min(objectives, axis=0)
        return float(np.mean(ranges))

    def to_json(self) -> dict:
        """Convert Pareto front to JSON-serializable dict."""
        return {
            "generation": self.generation,
            "size": len(self.individuals),
            "individuals": [
                {
                    "id": ind.id,
                    "fitness": ind.fitness.to_dict() if ind.fitness else {},
                    "rank": ind.rank,
                    "crowding_distance": ind.crowding_distance,
                }
                for ind in self.individuals
            ],
            "spread": self.compute_spread(),
            "knee_point": (
                self.get_knee_point().fitness.to_dict()
                if self.get_knee_point() and self.get_knee_point().fitness
                else None
            ),
        }


class CrowdingDistance:
    """
    Crowding distance calculator for NSGA-II.

    Crowding distance measures how close an individual is to its neighbors
    in objective space. Higher distance = more isolated = more valuable
    for diversity.
    """

    @staticmethod
    def compute(
        individuals: list[Individual],
        objectives: list[str] | None = None,
    ) -> list[Individual]:
        """
        Compute crowding distance for a set of individuals.

        Args:
            individuals: List of individuals (modified in place)
            objectives: Which objectives to consider (default: all)

        Returns:
            Same individuals with crowding_distance updated
        """
        if len(individuals) <= 2:
            for ind in individuals:
                ind.crowding_distance = float("inf")
            return individuals

        if objectives is None:
            objectives = [
                "coverage",
                "fairness",
                "preferences",
                "learning_goals",
                "acgme_compliance",
                "continuity",
            ]

        # Initialize distances
        for ind in individuals:
            ind.crowding_distance = 0.0

        # Compute for each objective
        for obj in objectives:
            # Sort by this objective
            sorted_inds = sorted(
                individuals,
                key=lambda ind: getattr(ind.fitness, obj) if ind.fitness else 0,
            )

            # Boundary points get infinite distance
            sorted_inds[0].crowding_distance = float("inf")
            sorted_inds[-1].crowding_distance = float("inf")

            # Get objective range
            if sorted_inds[0].fitness and sorted_inds[-1].fitness:
                obj_min = getattr(sorted_inds[0].fitness, obj)
                obj_max = getattr(sorted_inds[-1].fitness, obj)
                obj_range = obj_max - obj_min
            else:
                obj_range = 0

            if obj_range < 1e-10:
                continue

            # Compute distances for middle points
            for i in range(1, len(sorted_inds) - 1):
                if not math.isinf(sorted_inds[i].crowding_distance):
                    if sorted_inds[i - 1].fitness and sorted_inds[i + 1].fitness:
                        obj_prev = getattr(sorted_inds[i - 1].fitness, obj)
                        obj_next = getattr(sorted_inds[i + 1].fitness, obj)
                        sorted_inds[i].crowding_distance += (
                            obj_next - obj_prev
                        ) / obj_range

        return individuals


@dataclass
class NSGA2Config:
    """Configuration for NSGA-II algorithm."""

    population_size: int = NSGA2_DEFAULT_POPULATION_SIZE
    max_generations: int = NSGA2_DEFAULT_MAX_GENERATIONS
    crossover_method: CrossoverMethod = CrossoverMethod.UNIFORM
    mutation_method: MutationMethod = MutationMethod.FLIP
    crossover_rate: float = NSGA2_DEFAULT_CROSSOVER_RATE
    mutation_rate: float = NSGA2_DEFAULT_MUTATION_RATE
    adaptive_mutation: bool = True
    tournament_size: int = (
        NSGA2_DEFAULT_TOURNAMENT_SIZE  # Binary tournament for NSGA-II
    )
    early_stop_generations: int = NSGA2_EARLY_STOP_GENERATIONS


class NSGA2Solver(BioInspiredSolver):
    """
    NSGA-II solver for multi-objective schedule optimization.

    Implements the complete NSGA-II algorithm:
    1. Fast non-dominated sorting
    2. Crowding distance calculation
    3. Binary tournament selection with crowded comparison
    4. Elitist replacement

    Returns the entire Pareto front, allowing decision makers to
    choose their preferred trade-off point.
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        config: NSGA2Config | None = None,
        seed: int | None = None,
        objectives: list[str] | None = None,
    ):
        """
        Initialize NSGA-II solver.

        Args:
            constraint_manager: Constraint manager for validation
            timeout_seconds: Maximum solve time
            config: NSGA-II configuration
            seed: Random seed
            objectives: Which objectives to optimize (default: all)
        """
        self.config = config or NSGA2Config()
        self.objectives = objectives or [
            "coverage",
            "fairness",
            "preferences",
            "learning_goals",
            "acgme_compliance",
            "continuity",
        ]

        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=self.config.population_size,
            max_generations=self.config.max_generations,
            seed=seed,
        )

        # Initialize operators
        self.crossover = CrossoverOperator(
            method=self.config.crossover_method,
            crossover_rate=self.config.crossover_rate,
        )
        self.mutation = MutationOperator(
            method=self.config.mutation_method,
            base_rate=self.config.mutation_rate,
            adaptive=self.config.adaptive_mutation,
        )

        # NSGA-II specific state
        self.fronts: list[list[Individual]] = []
        self.pareto_history: list[ParetoFront] = []
        self._n_templates: int = 1
        self._hypervolume_history: list[float] = []

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run NSGA-II evolution.

        Args:
            context: Scheduling context

        Returns:
            Best individual (knee point of final Pareto front)
        """
        start_time = time.time()

        # Calculate number of templates
        self._n_templates = max(
            1,
            len([t for t in context.templates if not t.requires_procedure_credential]),
        )

        # Initialize population
        self.population = self.initialize_population(context)

        # Initial sorting
        self.fronts = self._fast_non_dominated_sort(self.population)
        self._assign_crowding_distance()

        logger.info(
            f"NSGA-II initialized: pop_size={len(self.population)}, "
            f"fronts={len(self.fronts)}, front_0_size={len(self.fronts[0]) if self.fronts else 0}"
        )

        # Evolution loop
        for generation in range(self.max_generations):
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                logger.info(f"NSGA-II timeout at generation {generation}")
                break

            # Create offspring population
            offspring = self._create_offspring(context, generation)

            # Combine parent and offspring
            combined = self.population + offspring

            # Fast non-dominated sort
            self.fronts = self._fast_non_dominated_sort(combined)

            # Select next generation
            self.population = self._select_next_generation()

            # Update Pareto front
            pareto = ParetoFront(
                individuals=[ind.copy() for ind in self.fronts[0]],
                generation=generation,
            )
            self.pareto_history.append(pareto)
            self.pareto_front = pareto.individuals

            # Adaptive mutation
            improved = self._check_improvement()
            stats = self.evolution_history[-1] if self.evolution_history else None
            diversity = stats.diversity if stats else 0.5
            self.mutation.adapt_rate(improved, diversity, generation)

            # Track statistics
            stats = self.compute_population_stats(
                self.population,
                generation,
                mutation_rate=self.mutation.current_rate,
                crossover_rate=self.crossover.crossover_rate,
            )
            self.evolution_history.append(stats)

            # Check convergence
            if self._check_convergence(generation):
                logger.info(f"NSGA-II converged at generation {generation}")
                break

            # Log progress
            if generation % NSGA2_LOG_INTERVAL == 0:
                logger.info(
                    f"NSGA-II gen {generation}: fronts={len(self.fronts)}, "
                    f"front_0={len(self.fronts[0]) if self.fronts else 0}, "
                    f"hypervolume={stats.hypervolume:.4f}"
                )

        # Return knee point of final Pareto front
        final_pareto = ParetoFront(
            individuals=self.fronts[0] if self.fronts else [],
            generation=len(self.evolution_history),
        )
        knee = final_pareto.get_knee_point()
        self.best_individual = knee

        return knee if knee else (self.population[0] if self.population else None)

    def _fast_non_dominated_sort(
        self,
        population: list[Individual],
    ) -> list[list[Individual]]:
        """
        Perform fast non-dominated sorting.

        Assigns rank to each individual based on Pareto dominance.
        Time complexity: O(MN²) where M=objectives, N=population size.

        Args:
            population: Population to sort

        Returns:
            List of fronts (front 0 = non-dominated)
        """
        n = len(population)
        dominated_by: dict[int, list[int]] = {i: [] for i in range(n)}
        domination_count: dict[int, int] = dict.fromkeys(range(n), 0)
        fronts: list[list[Individual]] = [[]]

        # Compare all pairs
        for i, ind_i in enumerate(population):
            for j, ind_j in enumerate(population):
                if i == j:
                    continue
                if ind_i.fitness and ind_j.fitness:
                    if ind_i.fitness.dominates(ind_j.fitness):
                        dominated_by[i].append(j)
                    elif ind_j.fitness.dominates(ind_i.fitness):
                        domination_count[i] += 1

            # If not dominated by anyone, it's in front 0
            if domination_count[i] == 0:
                population[i].rank = 0
                fronts[0].append(population[i])

        # Build subsequent fronts
        current_front = 0
        while fronts[current_front]:
            next_front = []
            for ind in fronts[current_front]:
                ind_idx = population.index(ind)
                for dominated_idx in dominated_by[ind_idx]:
                    domination_count[dominated_idx] -= 1
                    if domination_count[dominated_idx] == 0:
                        population[dominated_idx].rank = current_front + 1
                        next_front.append(population[dominated_idx])
            current_front += 1
            fronts.append(next_front)

        # Remove empty last front
        if not fronts[-1]:
            fronts.pop()

        return fronts

    def _assign_crowding_distance(self) -> None:
        """Assign crowding distance to all individuals in each front."""
        for front in self.fronts:
            CrowdingDistance.compute(front, self.objectives)

    def _create_offspring(
        self,
        context: SchedulingContext,
        generation: int,
    ) -> list[Individual]:
        """
        Create offspring population using tournament selection and genetic operators.

        Args:
            context: Scheduling context
            generation: Current generation

        Returns:
            List of offspring individuals
        """
        offspring = []

        while len(offspring) < self.population_size:
            # Binary tournament selection (crowded comparison)
            parent1 = self._crowded_tournament_select()
            parent2 = self._crowded_tournament_select()

            # Crossover
            child1_chr, child2_chr = self.crossover.crossover(parent1, parent2)

            # Mutation
            child1_chr = self.mutation.mutate(child1_chr, self._n_templates)
            child2_chr = self.mutation.mutate(child2_chr, self._n_templates)

            # Evaluate
            fitness1 = self.evaluate_fitness(child1_chr, context)
            fitness2 = self.evaluate_fitness(child2_chr, context)

            # Create individuals
            offspring.append(
                Individual(
                    chromosome=child1_chr,
                    fitness=fitness1,
                    generation=generation + 1,
                    parent_ids=[parent1.id, parent2.id],
                    id=self._get_next_id(),
                )
            )

            if len(offspring) < self.population_size:
                offspring.append(
                    Individual(
                        chromosome=child2_chr,
                        fitness=fitness2,
                        generation=generation + 1,
                        parent_ids=[parent1.id, parent2.id],
                        id=self._get_next_id(),
                    )
                )

        return offspring

    def _crowded_tournament_select(self) -> Individual:
        """
        Binary tournament selection using crowded comparison operator.

        Selects winner based on:
        1. Lower rank wins (better Pareto front)
        2. If same rank, higher crowding distance wins (more diverse)
        """
        candidates = random.sample(
            self.population, min(self.config.tournament_size, len(self.population))
        )

        winner = candidates[0]
        for candidate in candidates[1:]:
            if candidate.rank < winner.rank:
                winner = candidate
            elif candidate.rank == winner.rank:
                if candidate.crowding_distance > winner.crowding_distance:
                    winner = candidate

        return winner

    def _select_next_generation(self) -> list[Individual]:
        """
        Select next generation from combined parent/offspring population.

        Fills population by adding fronts in order until full.
        For the last front, uses crowding distance to break ties.

        Returns:
            New population
        """
        new_population = []

        for front in self.fronts:
            # Compute crowding distance for this front
            CrowdingDistance.compute(front, self.objectives)

            if len(new_population) + len(front) <= self.population_size:
                # Add entire front
                new_population.extend(front)
            else:
                # Add best from this front based on crowding distance
                remaining = self.population_size - len(new_population)
                sorted_front = sorted(
                    front,
                    key=lambda ind: ind.crowding_distance,
                    reverse=True,  # Higher crowding = more diverse
                )
                new_population.extend(sorted_front[:remaining])
                break

        return new_population

    def _check_improvement(self) -> bool:
        """Check if Pareto front improved this generation."""
        if len(self.pareto_history) < 2:
            return True

        prev = self.pareto_history[-2]
        curr = self.pareto_history[-1]

        # Check if spread increased or size increased
        return (
            len(curr.individuals) > len(prev.individuals)
            or curr.compute_spread() > prev.compute_spread() * 1.01
        )

    def _check_convergence(self, generation: int) -> bool:
        """
        Check if NSGA-II has converged.

        Uses hypervolume stability as convergence criterion.
        """
        if len(self.evolution_history) < self.config.early_stop_generations:
            return False

        # Check hypervolume stability
        recent_hv = [
            s.hypervolume
            for s in self.evolution_history[-self.config.early_stop_generations :]
        ]
        hv_range = max(recent_hv) - min(recent_hv)

        return hv_range < NSGA2_CONVERGENCE_THRESHOLD

    def get_pareto_solutions(self) -> list[dict]:
        """
        Get all solutions on the final Pareto front.

        Returns:
            List of solution dictionaries with fitness and assignments
        """
        if not self.fronts or not self.fronts[0]:
            return []

        return [
            {
                "id": ind.id,
                "fitness": ind.fitness.to_dict() if ind.fitness else {},
                "rank": ind.rank,
                "crowding_distance": ind.crowding_distance,
                "n_assignments": ind.chromosome.count_assignments(),
            }
            for ind in self.fronts[0]
        ]

    def get_evolution_data(self) -> dict:
        """Get evolution data including NSGA-II specific information."""
        base_data = super().get_evolution_data()

        base_data["nsga2_config"] = {
            "objectives": self.objectives,
            "tournament_size": self.config.tournament_size,
        }

        base_data["pareto_history"] = [pf.to_json() for pf in self.pareto_history[-10:]]

        base_data["final_pareto_front"] = (
            self.pareto_history[-1].to_json() if self.pareto_history else None
        )

        return base_data
