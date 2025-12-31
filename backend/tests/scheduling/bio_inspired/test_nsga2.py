"""Tests for NSGA-II implementation."""

import numpy as np
import pytest

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
)
from app.scheduling.bio_inspired.nsga2 import (
    CrowdingDistance,
    NSGA2Config,
    NSGA2Solver,
    ParetoFront,
)


class TestParetoFront:
    """Tests for ParetoFront class."""

    def _create_individual(
        self,
        coverage: float,
        fairness: float,
        ind_id: int = 0,
    ) -> Individual:
        """Create individual with specified fitness."""
        return Individual(
            chromosome=Chromosome.create_empty(3, 5),
            fitness=FitnessVector(coverage=coverage, fairness=fairness),
            id=ind_id,
        )

    def test_pareto_front_add_non_dominated(self):
        """Test adding non-dominated solutions."""
        pf = ParetoFront()

        # Add first solution
        ind1 = self._create_individual(0.8, 0.6, 1)
        pf.add(ind1)
        assert len(pf.individuals) == 1

        # Add non-dominated solution (different trade-off)
        ind2 = self._create_individual(0.6, 0.8, 2)
        pf.add(ind2)
        assert len(pf.individuals) == 2

    def test_pareto_front_rejects_dominated(self):
        """Test dominated solutions are rejected."""
        pf = ParetoFront()

        # Add dominant solution
        ind1 = self._create_individual(0.9, 0.9, 1)
        pf.add(ind1)

        # Try to add dominated solution
        ind2 = self._create_individual(0.7, 0.7, 2)
        pf.add(ind2)

        # Should still have only 1
        assert len(pf.individuals) == 1
        assert pf.individuals[0].id == 1

    def test_pareto_front_removes_dominated(self):
        """Test adding dominant solution removes dominated ones."""
        pf = ParetoFront()

        # Add weaker solution first
        ind1 = self._create_individual(0.5, 0.5, 1)
        pf.add(ind1)

        # Add dominant solution
        ind2 = self._create_individual(0.9, 0.9, 2)
        pf.add(ind2)

        # Should have replaced
        assert len(pf.individuals) == 1
        assert pf.individuals[0].id == 2

    def test_get_extreme_solutions(self):
        """Test getting extreme solutions."""
        pf = ParetoFront()

        # Add solutions with different extremes
        pf.add(self._create_individual(0.9, 0.3, 1))  # Best coverage
        pf.add(self._create_individual(0.3, 0.9, 2))  # Best fairness
        pf.add(self._create_individual(0.6, 0.6, 3))  # Balanced

        extremes = pf.get_extreme_solutions()

        assert "best_coverage" in extremes
        assert "best_fairness" in extremes
        assert extremes["best_coverage"].id == 1
        assert extremes["best_fairness"].id == 2

    def test_get_knee_point(self):
        """Test finding knee point."""
        pf = ParetoFront()

        # Create a Pareto front with clear knee
        pf.add(self._create_individual(0.9, 0.1, 1))
        pf.add(self._create_individual(0.7, 0.5, 2))  # Likely knee
        pf.add(self._create_individual(0.5, 0.7, 3))
        pf.add(self._create_individual(0.1, 0.9, 4))

        knee = pf.get_knee_point()
        assert knee is not None
        # Knee should be one of the middle solutions
        assert knee.id in [2, 3]

    def test_compute_spread(self):
        """Test spread computation."""
        pf = ParetoFront()

        # Single solution = no spread
        pf.add(self._create_individual(0.5, 0.5, 1))
        spread1 = pf.compute_spread()

        # Add diverse solutions
        pf.add(self._create_individual(0.9, 0.1, 2))
        pf.add(self._create_individual(0.1, 0.9, 3))
        spread2 = pf.compute_spread()

        # Spread should increase
        assert spread2 > spread1

    def test_pareto_to_json(self):
        """Test JSON serialization."""
        pf = ParetoFront(generation=10)
        pf.add(self._create_individual(0.8, 0.6, 1))
        pf.add(self._create_individual(0.6, 0.8, 2))

        data = pf.to_json()

        assert data["generation"] == 10
        assert data["size"] == 2
        assert "individuals" in data
        assert "spread" in data


class TestCrowdingDistance:
    """Tests for crowding distance calculation."""

    def _create_individuals(
        self,
        fitness_values: list[tuple[float, float]],
    ) -> list[Individual]:
        """Create individuals with specified fitness values."""
        individuals = []
        for i, (cov, fair) in enumerate(fitness_values):
            ind = Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=cov, fairness=fair),
                id=i,
            )
            individuals.append(ind)
        return individuals

    def test_boundary_points_infinite_distance(self):
        """Test boundary points get infinite crowding distance."""
        individuals = self._create_individuals(
            [
                (0.1, 0.9),  # Boundary
                (0.5, 0.5),  # Middle
                (0.9, 0.1),  # Boundary
            ]
        )

        CrowdingDistance.compute(individuals, ["coverage", "fairness"])

        # First and last (by coverage) should have infinite distance
        sorted_by_cov = sorted(individuals, key=lambda ind: ind.fitness.coverage)
        assert sorted_by_cov[0].crowding_distance == float("inf")
        assert sorted_by_cov[-1].crowding_distance == float("inf")

    def test_crowding_distance_middle_points(self):
        """Test middle points get finite crowding distance."""
        individuals = self._create_individuals(
            [
                (0.1, 0.9),
                (0.3, 0.7),  # Middle
                (0.5, 0.5),  # Middle
                (0.7, 0.3),  # Middle
                (0.9, 0.1),
            ]
        )

        CrowdingDistance.compute(individuals, ["coverage", "fairness"])

        # Middle points should have finite distance > 0
        for ind in individuals[1:-1]:
            assert 0 < ind.crowding_distance < float("inf")

    def test_single_individual(self):
        """Test single individual gets infinite distance."""
        individuals = self._create_individuals([(0.5, 0.5)])
        CrowdingDistance.compute(individuals, ["coverage"])

        assert individuals[0].crowding_distance == float("inf")

    def test_two_individuals(self):
        """Test two individuals both get infinite distance."""
        individuals = self._create_individuals(
            [
                (0.3, 0.7),
                (0.7, 0.3),
            ]
        )
        CrowdingDistance.compute(individuals, ["coverage", "fairness"])

        assert individuals[0].crowding_distance == float("inf")
        assert individuals[1].crowding_distance == float("inf")


class TestNSGA2Config:
    """Tests for NSGA-II configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = NSGA2Config()

        assert config.population_size == 100
        assert config.max_generations == 200
        assert config.tournament_size == 2  # Binary for NSGA-II

    def test_custom_config(self):
        """Test custom configuration."""
        config = NSGA2Config(
            population_size=50,
            crossover_rate=0.95,
        )

        assert config.population_size == 50
        assert config.crossover_rate == 0.95


class TestNSGA2Solver:
    """Tests for NSGA-II solver (unit tests without full scheduling context)."""

    def test_nsga2_initialization(self):
        """Test NSGA-II solver initializes correctly."""
        config = NSGA2Config(population_size=20, max_generations=10)
        solver = NSGA2Solver(config=config, seed=42)

        assert solver.config.population_size == 20
        assert solver.seed == 42

    def test_nsga2_objectives_configurable(self):
        """Test objectives can be configured."""
        solver = NSGA2Solver(objectives=["coverage", "fairness"])

        assert "coverage" in solver.objectives
        assert "fairness" in solver.objectives
        assert len(solver.objectives) == 2

    def test_fast_non_dominated_sort_single_front(self):
        """Test sorting when all solutions are non-dominated."""
        solver = NSGA2Solver(config=NSGA2Config(population_size=5))

        # Create population where no solution dominates another
        population = []
        for i in range(5):
            ind = Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(
                    coverage=0.1 * i,
                    fairness=0.8 - 0.1 * i,
                ),
                id=i,
            )
            population.append(ind)

        fronts = solver._fast_non_dominated_sort(population)

        # All should be in front 0 (non-dominated)
        assert len(fronts) >= 1
        assert len(fronts[0]) == 5

    def test_fast_non_dominated_sort_multiple_fronts(self):
        """Test sorting creates multiple fronts."""
        solver = NSGA2Solver(config=NSGA2Config(population_size=4))

        population = [
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.9, fairness=0.9),  # Front 0
                id=1,
            ),
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.8, fairness=0.8),  # Front 1
                id=2,
            ),
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.5, fairness=0.5),  # Front 2
                id=3,
            ),
        ]

        fronts = solver._fast_non_dominated_sort(population)

        # Should have 3 fronts
        assert len(fronts) == 3
        assert fronts[0][0].id == 1
        assert fronts[1][0].id == 2
        assert fronts[2][0].id == 3

    def test_get_pareto_solutions(self):
        """Test getting Pareto solutions."""
        solver = NSGA2Solver(config=NSGA2Config(population_size=3))

        # Set up mock fronts
        solver.fronts = [
            [
                Individual(
                    chromosome=Chromosome.create_empty(3, 5),
                    fitness=FitnessVector(coverage=0.8, fairness=0.6),
                    id=1,
                ),
                Individual(
                    chromosome=Chromosome.create_empty(3, 5),
                    fitness=FitnessVector(coverage=0.6, fairness=0.8),
                    id=2,
                ),
            ]
        ]

        solutions = solver.get_pareto_solutions()

        assert len(solutions) == 2
        assert solutions[0]["id"] == 1
        assert "fitness" in solutions[0]

    def test_get_evolution_data(self):
        """Test evolution data export."""
        solver = NSGA2Solver(config=NSGA2Config(population_size=10))

        data = solver.get_evolution_data()

        assert "algorithm" in data
        assert data["algorithm"] == "NSGA2Solver"
        assert "nsga2_config" in data
        assert "objectives" in data["nsga2_config"]
