"""Tests for bio-inspired optimization base classes."""

import numpy as np
import pytest

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
    ObjectiveType,
    PopulationStats,
)


class TestFitnessVector:
    """Tests for FitnessVector class."""

    def test_fitness_vector_creation(self):
        """Test creating a fitness vector."""
        fitness = FitnessVector(
            coverage=0.8,
            fairness=0.7,
            preferences=0.6,
            learning_goals=0.5,
            acgme_compliance=0.9,
            continuity=0.4,
        )

        assert fitness.coverage == 0.8
        assert fitness.fairness == 0.7
        assert fitness.acgme_compliance == 0.9

    def test_fitness_to_array(self):
        """Test converting fitness to numpy array."""
        fitness = FitnessVector(
            coverage=0.8,
            fairness=0.7,
            preferences=0.6,
            learning_goals=0.5,
            acgme_compliance=0.9,
            continuity=0.4,
        )

        arr = fitness.to_array()
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 6
        assert arr[0] == 0.8  # coverage
        assert arr[4] == 0.9  # acgme_compliance

    def test_fitness_from_array(self):
        """Test creating fitness from numpy array."""
        arr = np.array([0.8, 0.7, 0.6, 0.5, 0.9, 0.4])
        fitness = FitnessVector.from_array(arr)

        assert fitness.coverage == 0.8
        assert fitness.fairness == 0.7
        assert fitness.acgme_compliance == 0.9

    def test_fitness_dominates(self):
        """Test Pareto dominance relation."""
        # f1 dominates f2 (better in all objectives)
        f1 = FitnessVector(
            coverage=0.9,
            fairness=0.8,
            preferences=0.7,
            learning_goals=0.6,
            acgme_compliance=0.9,
            continuity=0.5,
        )
        f2 = FitnessVector(
            coverage=0.8,
            fairness=0.7,
            preferences=0.6,
            learning_goals=0.5,
            acgme_compliance=0.8,
            continuity=0.4,
        )

        assert f1.dominates(f2)
        assert not f2.dominates(f1)

    def test_fitness_not_dominates_incomparable(self):
        """Test that incomparable solutions don't dominate each other."""
        # f1 is better in coverage, f2 is better in fairness
        f1 = FitnessVector(coverage=0.9, fairness=0.5)
        f2 = FitnessVector(coverage=0.5, fairness=0.9)

        assert not f1.dominates(f2)
        assert not f2.dominates(f1)

    def test_weighted_sum_default(self):
        """Test weighted sum with default weights."""
        fitness = FitnessVector(
            coverage=1.0,
            fairness=1.0,
            preferences=1.0,
            learning_goals=1.0,
            acgme_compliance=1.0,
            continuity=1.0,
        )

        weighted = fitness.weighted_sum()
        assert weighted == pytest.approx(1.0, abs=0.01)

    def test_weighted_sum_custom_weights(self):
        """Test weighted sum with custom weights."""
        fitness = FitnessVector(coverage=1.0, fairness=0.0)
        weights = {
            "coverage": 1.0,
            "fairness": 0.0,
            "preferences": 0.0,
            "learning_goals": 0.0,
            "acgme_compliance": 0.0,
            "continuity": 0.0,
        }

        weighted = fitness.weighted_sum(weights)
        assert weighted == 1.0

    def test_fitness_to_dict(self):
        """Test fitness to dictionary conversion."""
        fitness = FitnessVector(coverage=0.8, fairness=0.7)
        d = fitness.to_dict()

        assert "coverage" in d
        assert "fairness" in d
        assert "weighted_sum" in d
        assert d["coverage"] == 0.8


class TestChromosome:
    """Tests for Chromosome class."""

    def test_chromosome_creation(self):
        """Test creating a chromosome."""
        genes = np.array([[1, 2, 0], [0, 1, 2]], dtype=np.int32)
        chrom = Chromosome(genes=genes)

        assert chrom.genes.shape == (2, 3)
        assert chrom.genes[0, 0] == 1

    def test_chromosome_create_random(self):
        """Test random chromosome creation."""
        chrom = Chromosome.create_random(
            n_residents=5,
            n_blocks=10,
            n_templates=3,
            density=0.5,
            seed=42,
        )

        assert chrom.genes.shape == (5, 10)
        # Some assignments should be non-zero
        assert chrom.count_assignments() > 0

    def test_chromosome_create_empty(self):
        """Test empty chromosome creation."""
        chrom = Chromosome.create_empty(n_residents=5, n_blocks=10)

        assert chrom.genes.shape == (5, 10)
        assert chrom.count_assignments() == 0

    def test_chromosome_copy(self):
        """Test chromosome copy is deep."""
        original = Chromosome.create_random(3, 5, 2, seed=42)
        copy = original.copy()

        # Modify copy
        copy.genes[0, 0] = 99

        # Original should be unchanged
        assert original.genes[0, 0] != 99

    def test_get_set_assignment(self):
        """Test getting and setting assignments."""
        chrom = Chromosome.create_empty(3, 5)

        chrom.set_assignment(1, 2, 3)
        assert chrom.get_assignment(1, 2) == 3

    def test_count_assignments(self):
        """Test counting assignments."""
        chrom = Chromosome.create_empty(3, 5)
        chrom.set_assignment(0, 0, 1)
        chrom.set_assignment(0, 1, 2)
        chrom.set_assignment(1, 0, 1)

        assert chrom.count_assignments() == 3

    def test_count_resident_assignments(self):
        """Test counting assignments per resident."""
        chrom = Chromosome.create_empty(3, 5)
        chrom.set_assignment(0, 0, 1)
        chrom.set_assignment(0, 1, 2)
        chrom.set_assignment(1, 0, 1)

        assert chrom.count_resident_assignments(0) == 2
        assert chrom.count_resident_assignments(1) == 1
        assert chrom.count_resident_assignments(2) == 0

    def test_hamming_distance(self):
        """Test Hamming distance calculation."""
        genes1 = np.array([[1, 2, 3], [0, 1, 2]])
        genes2 = np.array([[1, 3, 3], [0, 0, 2]])
        c1 = Chromosome(genes1)
        c2 = Chromosome(genes2)

        # Different positions: (0,1), (1,1)
        assert c1.hamming_distance(c2) == 2

    def test_similarity(self):
        """Test similarity calculation."""
        c1 = Chromosome.create_empty(3, 5)
        c2 = c1.copy()

        assert c1.similarity(c2) == 1.0

        # Modify one position
        c2.genes[0, 0] = 99
        expected_similarity = 1.0 - (1 / 15)  # 1 difference out of 15 positions
        assert c1.similarity(c2) == pytest.approx(expected_similarity)


class TestIndividual:
    """Tests for Individual class."""

    def test_individual_creation(self):
        """Test creating an individual."""
        chrom = Chromosome.create_random(3, 5, 2, seed=42)
        fitness = FitnessVector(coverage=0.8)

        ind = Individual(
            chromosome=chrom,
            fitness=fitness,
            generation=5,
            id=42,
        )

        assert ind.id == 42
        assert ind.generation == 5
        assert ind.fitness.coverage == 0.8

    def test_individual_comparison(self):
        """Test individual comparison for sorting."""
        ind1 = Individual(
            chromosome=Chromosome.create_empty(3, 5),
            rank=1,
            crowding_distance=0.5,
        )
        ind2 = Individual(
            chromosome=Chromosome.create_empty(3, 5),
            rank=0,
            crowding_distance=0.3,
        )
        ind3 = Individual(
            chromosome=Chromosome.create_empty(3, 5),
            rank=0,
            crowding_distance=0.7,
        )

        # Lower rank is better
        assert ind2 < ind1

        # Same rank, higher crowding distance is better
        assert ind3 < ind2

    def test_individual_copy(self):
        """Test individual copy is deep."""
        original = Individual(
            chromosome=Chromosome.create_random(3, 5, 2),
            fitness=FitnessVector(coverage=0.8),
            id=42,
        )
        copy = original.copy()

        # Modify copy
        copy.chromosome.genes[0, 0] = 99
        copy.id = 100

        # Original unchanged
        assert original.chromosome.genes[0, 0] != 99
        assert original.id == 42


class TestPopulationStats:
    """Tests for PopulationStats class."""

    def test_population_stats_creation(self):
        """Test creating population stats."""
        stats = PopulationStats(
            generation=10,
            population_size=100,
            best_fitness=0.95,
            worst_fitness=0.30,
            mean_fitness=0.65,
            std_fitness=0.15,
            diversity=0.45,
            pareto_front_size=15,
            hypervolume=0.82,
            convergence=0.55,
        )

        assert stats.generation == 10
        assert stats.best_fitness == 0.95
        assert stats.pareto_front_size == 15

    def test_population_stats_to_dict(self):
        """Test stats to dictionary conversion."""
        stats = PopulationStats(
            generation=10,
            population_size=100,
            best_fitness=0.95,
            worst_fitness=0.30,
            mean_fitness=0.65,
            std_fitness=0.15,
            diversity=0.45,
            pareto_front_size=15,
            hypervolume=0.82,
            convergence=0.55,
        )

        d = stats.to_dict()

        assert d["generation"] == 10
        assert d["best_fitness"] == 0.95
        assert d["pareto_front_size"] == 15
