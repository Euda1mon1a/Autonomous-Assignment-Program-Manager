"""Tests for Genetic Algorithm implementation."""

import numpy as np
import pytest

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
)
from app.scheduling.bio_inspired.genetic_algorithm import (
    CrossoverMethod,
    CrossoverOperator,
    GAConfig,
    GeneticAlgorithmSolver,
    MutationMethod,
    MutationOperator,
    SelectionMethod,
    SelectionOperator,
)


class TestSelectionOperator:
    """Tests for selection operators."""

    def _create_population(self, n: int = 10) -> list[Individual]:
        """Create test population with varying fitness."""
        population = []
        for i in range(n):
            fitness = FitnessVector(coverage=0.1 * i, fairness=0.9 - 0.1 * i)
            ind = Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=fitness,
                id=i,
            )
            population.append(ind)
        return population

    def test_tournament_selection(self):
        """Test tournament selection returns individuals."""
        population = self._create_population()
        selector = SelectionOperator(
            method=SelectionMethod.TOURNAMENT,
            tournament_size=3,
        )

        parents = selector.select(population, 4)

        assert len(parents) == 4
        for parent in parents:
            assert parent in population

    def test_roulette_selection(self):
        """Test roulette wheel selection returns individuals."""
        population = self._create_population()
        selector = SelectionOperator(method=SelectionMethod.ROULETTE)

        parents = selector.select(population, 4)

        assert len(parents) == 4
        for parent in parents:
            assert isinstance(parent, Individual)

    def test_rank_selection(self):
        """Test rank-based selection returns individuals."""
        population = self._create_population()
        selector = SelectionOperator(
            method=SelectionMethod.RANK,
            pressure=1.5,
        )

        parents = selector.select(population, 4)

        assert len(parents) == 4
        for parent in parents:
            assert isinstance(parent, Individual)

    def test_random_selection(self):
        """Test random selection returns individuals."""
        population = self._create_population()
        selector = SelectionOperator(method=SelectionMethod.RANDOM)

        parents = selector.select(population, 4)

        assert len(parents) == 4


class TestCrossoverOperator:
    """Tests for crossover operators."""

    def _create_parents(self) -> tuple[Individual, Individual]:
        """Create two parent individuals."""
        genes1 = np.ones((5, 10), dtype=np.int32)
        genes2 = np.ones((5, 10), dtype=np.int32) * 2

        return (
            Individual(chromosome=Chromosome(genes1), id=1),
            Individual(chromosome=Chromosome(genes2), id=2),
        )

    def test_uniform_crossover(self):
        """Test uniform crossover mixes genes."""
        parent1, parent2 = self._create_parents()
        crossover = CrossoverOperator(
            method=CrossoverMethod.UNIFORM,
            crossover_rate=1.0,  # Always crossover
        )

        np.random.seed(42)
        child1, child2 = crossover.crossover(parent1, parent2)

        # Children should have mix of 1s and 2s
        assert 1 in child1.genes
        assert 2 in child1.genes

    def test_single_point_crossover(self):
        """Test single-point crossover creates valid offspring."""
        parent1, parent2 = self._create_parents()
        crossover = CrossoverOperator(
            method=CrossoverMethod.SINGLE_POINT,
            crossover_rate=1.0,
        )

        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.genes.shape == (5, 10)
        assert child2.genes.shape == (5, 10)

    def test_two_point_crossover(self):
        """Test two-point crossover creates valid offspring."""
        parent1, parent2 = self._create_parents()
        crossover = CrossoverOperator(
            method=CrossoverMethod.TWO_POINT,
            crossover_rate=1.0,
        )

        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.genes.shape == (5, 10)
        assert child2.genes.shape == (5, 10)

    def test_row_based_crossover(self):
        """Test row-based crossover swaps entire rows."""
        parent1, parent2 = self._create_parents()
        crossover = CrossoverOperator(
            method=CrossoverMethod.ROW_BASED,
            crossover_rate=1.0,
        )

        child1, child2 = crossover.crossover(parent1, parent2)

        # Each row should be all 1s or all 2s
        for row in child1.genes:
            assert np.all(row == 1) or np.all(row == 2)

    def test_no_crossover_when_rate_zero(self):
        """Test no crossover when rate is 0."""
        parent1, parent2 = self._create_parents()
        crossover = CrossoverOperator(crossover_rate=0.0)

        child1, child2 = crossover.crossover(parent1, parent2)

        # Children should be copies of parents
        assert np.array_equal(child1.genes, parent1.chromosome.genes)
        assert np.array_equal(child2.genes, parent2.chromosome.genes)


class TestMutationOperator:
    """Tests for mutation operators."""

    def test_flip_mutation(self):
        """Test flip mutation changes genes."""
        chrom = Chromosome(np.zeros((5, 10), dtype=np.int32))
        mutator = MutationOperator(
            method=MutationMethod.FLIP,
            base_rate=1.0,  # Mutate all
        )

        np.random.seed(42)
        mutated = mutator.mutate(chrom, n_templates=3)

        # Some genes should have changed
        assert not np.array_equal(mutated.genes, chrom.genes)

    def test_swap_mutation(self):
        """Test swap mutation swaps positions."""
        genes = np.arange(10).reshape(2, 5).astype(np.int32)
        chrom = Chromosome(genes)
        mutator = MutationOperator(
            method=MutationMethod.SWAP,
            base_rate=1.0,
        )

        mutated = mutator.mutate(chrom, n_templates=10)

        # Shape should be preserved
        assert mutated.genes.shape == chrom.genes.shape

    def test_insert_mutation(self):
        """Test insert mutation adds assignments."""
        chrom = Chromosome.create_empty(5, 10)
        mutator = MutationOperator(
            method=MutationMethod.INSERT,
            base_rate=1.0,
        )

        mutated = mutator.mutate(chrom, n_templates=3)

        # Should have some assignments now
        assert mutated.count_assignments() > 0

    def test_delete_mutation(self):
        """Test delete mutation removes assignments."""
        genes = np.ones((5, 10), dtype=np.int32) * 2
        chrom = Chromosome(genes)
        mutator = MutationOperator(
            method=MutationMethod.DELETE,
            base_rate=1.0,
        )

        mutated = mutator.mutate(chrom, n_templates=3)

        # Should have fewer assignments
        assert mutated.count_assignments() < 50

    def test_adaptive_mutation_increases_on_stagnation(self):
        """Test adaptive mutation increases rate when stagnating."""
        mutator = MutationOperator(
            base_rate=0.1,
            adaptive=True,
            min_rate=0.01,
            max_rate=0.5,
        )

        # Simulate stagnation (no improvement)
        for _ in range(15):
            mutator.adapt_rate(improved=False, diversity=0.5, generation=_)

        # Rate should have increased
        assert mutator.current_rate > 0.1

    def test_adaptive_mutation_decreases_on_progress(self):
        """Test adaptive mutation decreases rate when improving."""
        mutator = MutationOperator(
            base_rate=0.3,
            adaptive=True,
            min_rate=0.01,
            max_rate=0.5,
        )

        # Simulate good progress
        for i in range(15):
            mutator.adapt_rate(improved=True, diversity=0.5, generation=i)

        # Rate should have decreased
        assert mutator.current_rate < 0.3


class TestGAConfig:
    """Tests for GA configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GAConfig()

        assert config.population_size == 100
        assert config.max_generations == 200
        assert config.crossover_rate == 0.8
        assert config.mutation_rate == 0.1

    def test_custom_config(self):
        """Test custom configuration values."""
        config = GAConfig(
            population_size=50,
            elite_size=10,
            crossover_method=CrossoverMethod.ROW_BASED,
        )

        assert config.population_size == 50
        assert config.elite_size == 10
        assert config.crossover_method == CrossoverMethod.ROW_BASED


class TestGeneticAlgorithmSolver:
    """Tests for GA solver (unit tests without full scheduling context)."""

    def test_ga_solver_initialization(self):
        """Test GA solver initializes correctly."""
        config = GAConfig(population_size=20, max_generations=10)
        solver = GeneticAlgorithmSolver(config=config, seed=42)

        assert solver.config.population_size == 20
        assert solver.config.max_generations == 10
        assert solver.seed == 42

    def test_ga_operators_initialized(self):
        """Test GA operators are initialized."""
        config = GAConfig(
            selection_method=SelectionMethod.TOURNAMENT,
            crossover_method=CrossoverMethod.UNIFORM,
            mutation_method=MutationMethod.FLIP,
        )
        solver = GeneticAlgorithmSolver(config=config)

        assert solver.selection.method == SelectionMethod.TOURNAMENT
        assert solver.crossover.method == CrossoverMethod.UNIFORM
        assert solver.mutation.method == MutationMethod.FLIP

    def test_get_evolution_data(self):
        """Test evolution data export."""
        solver = GeneticAlgorithmSolver(config=GAConfig(population_size=10))

        # Add some mock history
        from app.scheduling.bio_inspired.base import PopulationStats

        solver.evolution_history = [
            PopulationStats(
                generation=i,
                population_size=10,
                best_fitness=0.5 + 0.01 * i,
                worst_fitness=0.3,
                mean_fitness=0.4,
                std_fitness=0.1,
                diversity=0.3,
                pareto_front_size=5,
                hypervolume=0.5,
                convergence=0.7,
                mutation_rate=0.1,
            )
            for i in range(5)
        ]

        data = solver.get_evolution_data()

        assert "algorithm" in data
        assert data["algorithm"] == "GeneticAlgorithmSolver"
        assert "ga_config" in data
        assert "evolution_history" in data
