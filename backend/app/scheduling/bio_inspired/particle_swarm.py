"""
Particle Swarm Optimization (PSO) for Fairness-Preference Trade-offs.

This module implements PSO for continuous optimization of schedule parameters.
While schedules are discrete, PSO optimizes:
- Objective weights (how to balance fairness vs preferences)
- Constraint penalties (soft constraint trade-offs)
- Template probabilities (likelihood of assigning each rotation type)

PSO is inspired by social behavior:
- Each particle has a position (solution) and velocity
- Particles are attracted to their personal best and swarm's global best
- Inertia keeps particles moving to explore the search space

Key Features:
- Multiple topology options (global, ring, random)
- Adaptive inertia weight
- Constraint handling via penalty functions
- Multi-swarm for multi-objective optimization
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
from app.scheduling.bio_inspired.constants import (
    PSO_DEFAULT_SWARM_SIZE,
    PSO_DEFAULT_MAX_ITERATIONS,
    PSO_DEFAULT_INERTIA_WEIGHT,
    PSO_DEFAULT_COGNITIVE_COEFF,
    PSO_DEFAULT_SOCIAL_COEFF,
    PSO_DEFAULT_VELOCITY_CLAMP,
    PSO_INERTIA_MIN,
    PSO_INERTIA_MAX,
    PSO_DEFAULT_DIMENSION,
    PSO_POSITION_MIN,
    PSO_POSITION_MAX,
    PSO_EARLY_STOP_ITERATIONS,
    PSO_CONVERGENCE_THRESHOLD,
    PSO_LOG_INTERVAL,
    PSO_VELOCITY_RANGE_MULTIPLIER,
    PSO_RANDOM_TOPOLOGY_MIN_NEIGHBORS,
    PSO_MIN_WEIGHT_VALUE,
    PSO_DENSITY_BASE,
    PSO_DENSITY_RANGE,
    PSO_ASSIGNMENT_MULTIPLIER,
    PSO_WEEKLY_LOOKBACK_BLOCKS,
    ACGME_WEEKLY_LIMIT_BLOCKS,
)
from app.scheduling.constraints import ConstraintManager, SchedulingContext

logger = logging.getLogger(__name__)


class SwarmTopology(Enum):
    """Topology for particle communication."""

    GLOBAL = "global"  # All particles share global best
    RING = "ring"  # Each particle has 2 neighbors
    RANDOM = "random"  # Random subset of neighbors
    VON_NEUMANN = "von_neumann"  # 2D grid topology


@dataclass
class Particle:
    """
    A particle in the swarm.

    Represents a point in the search space with:
    - Position: Current solution (weight vector or probability vector)
    - Velocity: Direction and speed of movement
    - Personal best: Best position this particle has visited
    - Fitness: Evaluation at current position
    """

    position: np.ndarray
    velocity: np.ndarray
    personal_best: np.ndarray
    personal_best_fitness: float = float("-inf")
    fitness: float = float("-inf")
    id: int = 0
    neighbors: list[int] = field(default_factory=list)

    # For multi-objective PSO
    personal_pareto: list[np.ndarray] = field(default_factory=list)
    crowding_distance: float = 0.0

    def update_personal_best(self) -> None:
        """
        Update personal best if current position is better.

        Compares the current fitness to the personal best fitness and updates
        the personal best position if the current position is superior.

        Note:
            This method modifies the particle's personal_best and
            personal_best_fitness attributes in-place.
        """
        if self.fitness > self.personal_best_fitness:
            self.personal_best = self.position.copy()
            self.personal_best_fitness = self.fitness

    def to_dict(self) -> dict:
        """
        Convert particle to dictionary for serialization.

        Creates a JSON-serializable dictionary representation of the particle,
        including its position, velocity magnitude, and fitness metrics.

        Returns:
            dict: Dictionary containing:
                - id (int): Particle identifier
                - position (list[float]): Current position vector
                - velocity (float): Velocity magnitude (L2 norm)
                - fitness (float): Current fitness value
                - personal_best_fitness (float): Best fitness achieved
        """
        return {
            "id": self.id,
            "position": self.position.tolist(),
            "velocity": np.linalg.norm(self.velocity),
            "fitness": self.fitness,
            "personal_best_fitness": self.personal_best_fitness,
        }


@dataclass
class PSOConfig:
    """Configuration for Particle Swarm Optimization."""

    swarm_size: int = PSO_DEFAULT_SWARM_SIZE
    max_iterations: int = PSO_DEFAULT_MAX_ITERATIONS
    topology: SwarmTopology = SwarmTopology.GLOBAL

    # PSO parameters
    inertia_weight: float = PSO_DEFAULT_INERTIA_WEIGHT  # w: momentum
    cognitive_coeff: float = (
        PSO_DEFAULT_COGNITIVE_COEFF  # c1: attraction to personal best
    )
    social_coeff: float = (
        PSO_DEFAULT_SOCIAL_COEFF  # c2: attraction to global/local best
    )
    velocity_clamp: float = PSO_DEFAULT_VELOCITY_CLAMP  # Max velocity magnitude

    # Adaptive parameters
    inertia_min: float = PSO_INERTIA_MIN
    inertia_max: float = PSO_INERTIA_MAX
    adaptive_inertia: bool = True

    # Search space bounds
    dimension: int = PSO_DEFAULT_DIMENSION  # Number of objective weights to optimize
    position_min: float = PSO_POSITION_MIN
    position_max: float = PSO_POSITION_MAX

    # Convergence
    early_stop_iterations: int = PSO_EARLY_STOP_ITERATIONS


class ParticleSwarmSolver(BioInspiredSolver):
    """
    PSO solver for schedule optimization.

    Uses PSO to optimize:
    1. Objective weights for scalarization
    2. Template selection probabilities
    3. Constraint penalty coefficients

    The optimized parameters are then used to guide schedule construction.
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        config: PSOConfig | None = None,
        seed: int | None = None,
        parameter_names: list[str] | None = None,
    ) -> None:
        """
        Initialize PSO solver.

        Args:
            constraint_manager: Constraint manager
            timeout_seconds: Maximum solve time
            config: PSO configuration
            seed: Random seed
            parameter_names: Names of parameters being optimized
        """
        self.config = config or PSOConfig()
        self.parameter_names = parameter_names or [
            "coverage_weight",
            "fairness_weight",
            "preferences_weight",
            "learning_weight",
            "acgme_weight",
            "continuity_weight",
        ]

        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=self.config.swarm_size,
            max_generations=self.config.max_iterations,
            seed=seed,
        )

        # PSO state
        self.swarm: list[Particle] = []
        self.global_best: np.ndarray | None = None
        self.global_best_fitness: float = float("-inf")
        self.current_inertia: float = self.config.inertia_weight
        self._n_templates: int = 1
        self._fitness_history: list[float] = []

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run PSO optimization.

        Args:
            context: Scheduling context

        Returns:
            Best individual found
        """
        start_time = time.time()

        # Calculate number of templates
        self._n_templates = max(
            1,
            len([t for t in context.templates if not t.requires_procedure_credential]),
        )

        # Initialize swarm
        self._initialize_swarm()
        self._setup_topology()

        # Evaluate initial swarm
        for particle in self.swarm:
            particle.fitness = self._evaluate_position(particle.position, context)
            particle.update_personal_best()
            self._update_global_best(particle)

        logger.info(
            f"PSO initialized: swarm_size={len(self.swarm)}, "
            f"dimension={self.config.dimension}, "
            f"initial_best={self.global_best_fitness:.4f}"
        )

        # Main PSO loop
        for iteration in range(self.config.max_iterations):
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                logger.info(f"PSO timeout at iteration {iteration}")
                break

                # Update inertia weight
            if self.config.adaptive_inertia:
                self._adapt_inertia(iteration)

                # Update each particle
            for particle in self.swarm:
                self._update_particle(particle, context)

                # Track statistics
            self._track_iteration(iteration)

            # Check convergence
            if self._check_convergence():
                logger.info(f"PSO converged at iteration {iteration}")
                break

                # Log progress
            if iteration % PSO_LOG_INTERVAL == 0:
                logger.info(
                    f"PSO iter {iteration}: best={self.global_best_fitness:.4f}, "
                    f"inertia={self.current_inertia:.4f}"
                )

                # Convert best position to schedule
        best_weights = self._normalize_weights(self.global_best)
        best_chromosome = self._generate_schedule(context, best_weights)
        best_fitness = self.evaluate_fitness(best_chromosome, context)

        self.best_individual = Individual(
            chromosome=best_chromosome,
            fitness=best_fitness,
            id=self._get_next_id(),
        )

        return self.best_individual

    def _initialize_swarm(self) -> None:
        """
        Initialize swarm with random particles.

        Creates a population of particles with randomized positions and velocities
        within the defined search space bounds. Initial velocity is set to 10% of
        the position range to promote exploration.

        Note:
            Each particle's personal best is initialized to its starting position.
            The swarm attribute is populated with config.swarm_size particles.
        """
        self.swarm = []

        for i in range(self.config.swarm_size):
            # Random position in search space
            position = np.random.uniform(
                self.config.position_min,
                self.config.position_max,
                self.config.dimension,
            )

            # Random initial velocity
            velocity_range = (
                self.config.position_max - self.config.position_min
            ) * PSO_VELOCITY_RANGE_MULTIPLIER
            velocity = np.random.uniform(
                -velocity_range, velocity_range, self.config.dimension
            )

            particle = Particle(
                position=position,
                velocity=velocity,
                personal_best=position.copy(),
                id=i,
            )
            self.swarm.append(particle)

    def _setup_topology(self) -> None:
        """
        Set up communication topology between particles.

        Establishes the neighborhood structure that determines which particles
        can exchange information. Supports four topology types:
        - GLOBAL: All particles connected (fully connected graph)
        - RING: Each particle has 2 neighbors (ring lattice)
        - RANDOM: Random k-nearest neighbors (k = sqrt(n))
        - VON_NEUMANN: 2D grid with 4-connectivity

        Note:
            Modifies each particle's neighbors list in-place based on the
            configured topology type.
        """
        n = len(self.swarm)

        if self.config.topology == SwarmTopology.GLOBAL:
            # All particles see all others
            for particle in self.swarm:
                particle.neighbors = list(range(n))

        elif self.config.topology == SwarmTopology.RING:
            # Each particle has 2 neighbors
            for i, particle in enumerate(self.swarm):
                particle.neighbors = [(i - 1) % n, i, (i + 1) % n]

        elif self.config.topology == SwarmTopology.RANDOM:
            # Random subset of neighbors (sqrt(n) neighbors)
            k = max(PSO_RANDOM_TOPOLOGY_MIN_NEIGHBORS, int(math.sqrt(n)))
            for i, particle in enumerate(self.swarm):
                others = [j for j in range(n) if j != i]
                particle.neighbors = [i] + random.sample(others, min(k, len(others)))

        elif self.config.topology == SwarmTopology.VON_NEUMANN:
            # 2D grid (4 neighbors + self)
            side = int(math.sqrt(n))
            for i, particle in enumerate(self.swarm):
                row, col = i // side, i % side
                neighbors = [i]  # Include self
                # Up, down, left, right
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_row = (row + dr) % side
                    new_col = (col + dc) % side
                    neighbor_idx = new_row * side + new_col
                    if neighbor_idx < n:
                        neighbors.append(neighbor_idx)
                particle.neighbors = neighbors

    def _update_particle(self, particle: Particle, context: SchedulingContext) -> None:
        """
        Update particle position and velocity.

        Uses standard PSO update equations:
        v(t+1) = w*v(t) + c1*r1*(pbest - x) + c2*r2*(lbest - x)
        x(t+1) = x(t) + v(t+1)
        """
        # Get local best from neighbors
        local_best = self._get_local_best(particle)

        # Random coefficients
        r1 = np.random.random(self.config.dimension)
        r2 = np.random.random(self.config.dimension)

        # Velocity update
        cognitive = (
            self.config.cognitive_coeff
            * r1
            * (particle.personal_best - particle.position)
        )
        social = self.config.social_coeff * r2 * (local_best - particle.position)

        new_velocity = self.current_inertia * particle.velocity + cognitive + social

        # Clamp velocity
        velocity_magnitude = np.linalg.norm(new_velocity)
        if velocity_magnitude > self.config.velocity_clamp:
            new_velocity = new_velocity * (
                self.config.velocity_clamp / velocity_magnitude
            )

        particle.velocity = new_velocity

        # Position update
        new_position = particle.position + new_velocity

        # Clamp position to bounds
        new_position = np.clip(
            new_position, self.config.position_min, self.config.position_max
        )

        particle.position = new_position

        # Evaluate new position
        particle.fitness = self._evaluate_position(particle.position, context)

        # Update personal best
        particle.update_personal_best()

        # Update global best
        self._update_global_best(particle)

    def _get_local_best(self, particle: Particle) -> np.ndarray:
        """
        Get best position among particle's neighbors.

        Searches through the particle's neighborhood (defined by topology) to
        find the neighbor with the best personal best fitness.

        Args:
            particle: Particle whose neighborhood to search

        Returns:
            np.ndarray: Position of the best neighbor, or global best if no
                neighbors have been evaluated, or particle's own position
                as fallback.
        """
        best_fitness = float("-inf")
        best_position = (
            self.global_best if self.global_best is not None else particle.position
        )

        for neighbor_idx in particle.neighbors:
            neighbor = self.swarm[neighbor_idx]
            if neighbor.personal_best_fitness > best_fitness:
                best_fitness = neighbor.personal_best_fitness
                best_position = neighbor.personal_best

        return best_position

    def _update_global_best(self, particle: Particle) -> None:
        """
        Update global best if particle has better fitness.

        Compares the particle's personal best fitness to the global best and
        updates the global best if the particle is superior.

        Args:
            particle: Particle to compare against global best

        Note:
            Modifies self.global_best and self.global_best_fitness in-place.
        """
        if particle.personal_best_fitness > self.global_best_fitness:
            self.global_best = particle.personal_best.copy()
            self.global_best_fitness = particle.personal_best_fitness

    def _evaluate_position(
        self,
        position: np.ndarray,
        context: SchedulingContext,
    ) -> float:
        """
        Evaluate fitness at a position.

        Position represents objective weights. We:
        1. Normalize weights to sum to 1
        2. Generate a schedule using these weights
        3. Evaluate multi-objective fitness
        4. Return weighted sum using the position weights
        """
        weights = self._normalize_weights(position)

        # Generate schedule with these weights
        chromosome = self._generate_schedule(context, weights)

        # Evaluate fitness
        fitness_vec = self.evaluate_fitness(chromosome, context)

        # Compute weighted sum using the weights we're optimizing
        weight_dict = {
            "coverage": weights[0],
            "fairness": weights[1],
            "preferences": weights[2],
            "learning_goals": weights[3],
            "acgme_compliance": weights[4],
            "continuity": weights[5],
        }

        return fitness_vec.weighted_sum(weight_dict)

    def _normalize_weights(self, position: np.ndarray) -> np.ndarray:
        """
        Normalize position to valid weight vector (sum to 1).

        Converts a position vector into a valid weight vector by ensuring
        all values are positive and normalizing to sum to 1.0.

        Args:
            position: Raw position vector from PSO

        Returns:
            np.ndarray: Normalized weight vector where all elements are
                positive and sum to 1.0. Minimum value per element is 0.001
                to prevent zero weights.
        """
        # Ensure all positive
        weights = np.maximum(position, PSO_MIN_WEIGHT_VALUE)
        # Normalize
        return weights / np.sum(weights)

    def _generate_schedule(
        self,
        context: SchedulingContext,
        weights: np.ndarray,
    ) -> Chromosome:
        """
        Generate a schedule using weighted objectives.

        Uses a greedy construction heuristic that considers
        the weighted objectives at each decision point.
        """
        n_residents = len(context.residents)
        n_blocks = len([b for b in context.blocks if not b.is_weekend])
        n_templates = self._n_templates

        chromosome = Chromosome.create_empty(n_residents, n_blocks)

        # Greedy assignment based on weighted priorities
        # Higher weight on coverage = more assignments
        # Higher weight on fairness = balance workload
        # Higher weight on ACGME = respect limits

        target_density = (
            PSO_DENSITY_BASE + PSO_DENSITY_RANGE * weights[0]
        )  # Coverage weight affects density
        target_per_resident = int(n_blocks * target_density / n_residents)

        # Track assignments per resident for fairness
        resident_counts = np.zeros(n_residents)

        for b_idx in range(n_blocks):
            # Decide how many residents to assign this block
            n_to_assign = max(
                1, int(n_residents * PSO_ASSIGNMENT_MULTIPLIER * weights[0])
            )

            # Score each resident for this block
            scores = []
            for r_idx in range(n_residents):
                score = 0.0

                # Fairness: prefer residents with fewer assignments
                if weights[1] > 0.1:
                    fairness_score = 1.0 / (1.0 + resident_counts[r_idx])
                    score += weights[1] * fairness_score

                    # ACGME: respect weekly limits
                weekly_count = sum(
                    chromosome.genes[
                        r_idx, max(0, b_idx - PSO_WEEKLY_LOOKBACK_BLOCKS) : b_idx
                    ]
                    > 0
                )
                if weekly_count >= ACGME_WEEKLY_LIMIT_BLOCKS:  # ~80 hours
                    score -= weights[4] * 2.0  # Heavy penalty

                scores.append((r_idx, score))

                # Select top residents
            scores.sort(key=lambda x: x[1], reverse=True)
            for r_idx, _ in scores[:n_to_assign]:
                template = random.randint(1, n_templates)
                chromosome.genes[r_idx, b_idx] = template
                resident_counts[r_idx] += 1

        return chromosome

    def _adapt_inertia(self, iteration: int) -> None:
        """
        Adapt inertia weight based on progress.

        Linearly decreases inertia from max to min over the course of
        optimization. Higher inertia early promotes exploration, while
        lower inertia later promotes exploitation.

        Args:
            iteration: Current iteration number

        Note:
            Modifies self.current_inertia in-place based on iteration progress.
            Uses linear interpolation between config.inertia_max and
            config.inertia_min.
        """
        progress = iteration / self.config.max_iterations
        self.current_inertia = self.config.inertia_max - progress * (
            self.config.inertia_max - self.config.inertia_min
        )

    def _track_iteration(self, iteration: int) -> None:
        """
        Track statistics for this iteration.

        Records fitness statistics and diversity metrics for the current
        iteration. Updates evolution history with population statistics.

        Args:
            iteration: Current iteration number

        Note:
            Appends PopulationStats to self.evolution_history and updates
            self._fitness_history with the global best fitness.
        """
        fitness_values = [p.fitness for p in self.swarm]
        self._fitness_history.append(self.global_best_fitness)

        # Compute swarm diversity (average pairwise distance)
        positions = np.array([p.position for p in self.swarm])
        if len(positions) > 1:
            # Simplified: standard deviation of positions
            diversity = float(np.mean(np.std(positions, axis=0)))
        else:
            diversity = 0.0

            # Store in evolution history as PopulationStats
        stats = PopulationStats(
            generation=iteration,
            population_size=len(self.swarm),
            best_fitness=self.global_best_fitness,
            worst_fitness=min(fitness_values),
            mean_fitness=np.mean(fitness_values),
            std_fitness=np.std(fitness_values),
            diversity=diversity,
            pareto_front_size=1,  # PSO maintains single global best
            hypervolume=self.global_best_fitness,
            convergence=1.0 - diversity,
            mutation_rate=0.0,
            crossover_rate=0.0,
        )
        self.evolution_history.append(stats)

    def _check_convergence(self) -> bool:
        """
        Check if PSO has converged.

        Examines recent fitness history to determine if the swarm has
        converged (no significant improvement).

        Returns:
            bool: True if fitness improvement over the last
                early_stop_iterations iterations is less than 0.001,
                False otherwise or if insufficient history.

        Note:
            Requires at least config.early_stop_iterations of history
            to assess convergence.
        """
        if len(self._fitness_history) < self.config.early_stop_iterations:
            return False

        recent = self._fitness_history[-self.config.early_stop_iterations :]
        improvement = max(recent) - min(recent)

        return improvement < PSO_CONVERGENCE_THRESHOLD

    def get_optimized_weights(self) -> dict[str, float]:
        """
        Get the optimized objective weights.

        Converts the global best position into a dictionary of named
        objective weights.

        Returns:
            dict[str, float]: Dictionary mapping parameter names to their
                optimized weight values. Returns empty dict if no global
                best has been established.

        Example:
            {
                "coverage_weight": 0.25,
                "fairness_weight": 0.30,
                "preferences_weight": 0.20,
                ...
            }
        """
        if self.global_best is None:
            return {}

        weights = self._normalize_weights(self.global_best)
        return dict(zip(self.parameter_names, weights.tolist()))

    def get_evolution_data(self) -> dict:
        """
        Get evolution data including PSO-specific information.

        Returns:
            dict: Evolution data containing:
                - Base evolution data from parent class
                - pso_config: PSO-specific configuration
                - swarm_state: State of first 10 particles
                - optimized_weights: Final optimized weight values
                - global_best_position: Global best position vector

        Note:
            Extends the base class get_evolution_data with PSO-specific
            metrics and configuration.
        """
        base_data = super().get_evolution_data()

        base_data["pso_config"] = {
            "topology": self.config.topology.value,
            "inertia_weight": self.config.inertia_weight,
            "cognitive_coeff": self.config.cognitive_coeff,
            "social_coeff": self.config.social_coeff,
        }

        base_data["swarm_state"] = [p.to_dict() for p in self.swarm[:10]]
        base_data["optimized_weights"] = self.get_optimized_weights()
        base_data["global_best_position"] = (
            self.global_best.tolist() if self.global_best is not None else None
        )

        return base_data
