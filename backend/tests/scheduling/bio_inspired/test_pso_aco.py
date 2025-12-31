"""Tests for Particle Swarm and Ant Colony Optimization."""

import numpy as np
import pytest

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
)
from app.scheduling.bio_inspired.particle_swarm import (
    Particle,
    ParticleSwarmSolver,
    PSOConfig,
    SwarmTopology,
)
from app.scheduling.bio_inspired.ant_colony import (
    ACOConfig,
    AntColonySolver,
    AntPath,
    PheromoneMatrix,
)


class TestParticle:
    """Tests for Particle class."""

    def test_particle_creation(self):
        """Test creating a particle."""
        position = np.array([0.5, 0.5, 0.5])
        velocity = np.array([0.1, -0.1, 0.0])

        particle = Particle(
            position=position,
            velocity=velocity,
            personal_best=position.copy(),
            id=1,
        )

        assert particle.id == 1
        assert np.array_equal(particle.position, position)
        assert particle.personal_best_fitness == float("-inf")

    def test_particle_update_personal_best(self):
        """Test updating personal best."""
        particle = Particle(
            position=np.array([0.5, 0.5]),
            velocity=np.array([0.1, 0.1]),
            personal_best=np.array([0.3, 0.3]),
            personal_best_fitness=0.5,
            fitness=0.8,  # Better than personal best
        )

        particle.update_personal_best()

        assert particle.personal_best_fitness == 0.8
        assert np.array_equal(particle.personal_best, particle.position)

    def test_particle_to_dict(self):
        """Test particle to dictionary conversion."""
        particle = Particle(
            position=np.array([0.5, 0.5]),
            velocity=np.array([0.1, 0.1]),
            personal_best=np.array([0.4, 0.4]),
            personal_best_fitness=0.6,
            fitness=0.7,
            id=42,
        )

        d = particle.to_dict()

        assert d["id"] == 42
        assert d["fitness"] == 0.7
        assert "position" in d


class TestPSOConfig:
    """Tests for PSO configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = PSOConfig()

        assert config.swarm_size == 50
        assert config.max_iterations == 200
        assert config.inertia_weight == 0.7
        assert config.cognitive_coeff == 1.5
        assert config.social_coeff == 1.5

    def test_custom_config(self):
        """Test custom configuration."""
        config = PSOConfig(
            swarm_size=30,
            topology=SwarmTopology.RING,
        )

        assert config.swarm_size == 30
        assert config.topology == SwarmTopology.RING


class TestParticleSwarmSolver:
    """Tests for PSO solver."""

    def test_pso_initialization(self):
        """Test PSO solver initializes correctly."""
        config = PSOConfig(swarm_size=20, max_iterations=10)
        solver = ParticleSwarmSolver(config=config, seed=42)

        assert solver.config.swarm_size == 20
        assert solver.seed == 42

    def test_pso_initialize_swarm(self):
        """Test swarm initialization."""
        config = PSOConfig(swarm_size=10, dimension=4)
        solver = ParticleSwarmSolver(config=config, seed=42)

        solver._initialize_swarm()

        assert len(solver.swarm) == 10
        for particle in solver.swarm:
            assert particle.position.shape == (4,)
            assert particle.velocity.shape == (4,)

    def test_pso_setup_global_topology(self):
        """Test global topology setup."""
        config = PSOConfig(swarm_size=5, topology=SwarmTopology.GLOBAL)
        solver = ParticleSwarmSolver(config=config)

        solver._initialize_swarm()
        solver._setup_topology()

        # Each particle should see all others
        for particle in solver.swarm:
            assert len(particle.neighbors) == 5

    def test_pso_setup_ring_topology(self):
        """Test ring topology setup."""
        config = PSOConfig(swarm_size=5, topology=SwarmTopology.RING)
        solver = ParticleSwarmSolver(config=config)

        solver._initialize_swarm()
        solver._setup_topology()

        # Each particle should have 3 neighbors (self + 2)
        for particle in solver.swarm:
            assert len(particle.neighbors) == 3

    def test_pso_normalize_weights(self):
        """Test weight normalization."""
        solver = ParticleSwarmSolver()

        position = np.array([0.5, 0.3, 0.2, 0.0, 0.1, 0.1])
        weights = solver._normalize_weights(position)

        # Should sum to 1
        assert np.isclose(np.sum(weights), 1.0)
        # All positive
        assert np.all(weights > 0)

    def test_pso_get_optimized_weights(self):
        """Test getting optimized weights."""
        solver = ParticleSwarmSolver()
        solver.global_best = np.array([0.4, 0.3, 0.1, 0.1, 0.05, 0.05])

        weights = solver.get_optimized_weights()

        assert len(weights) == 6
        assert all(isinstance(v, float) for v in weights.values())

    def test_pso_adapt_inertia(self):
        """Test adaptive inertia."""
        config = PSOConfig(
            inertia_max=0.9,
            inertia_min=0.4,
            adaptive_inertia=True,
        )
        solver = ParticleSwarmSolver(config=config)

        # At start
        solver._adapt_inertia(0)
        assert solver.current_inertia == pytest.approx(0.9)

        # At end
        solver._adapt_inertia(config.max_iterations)
        assert solver.current_inertia == pytest.approx(0.4)


class TestAntPath:
    """Tests for AntPath class."""

    def test_ant_path_creation(self):
        """Test creating an ant path."""
        path = AntPath(
            resident_idx=0,
            path=[1, 2, 0, 1, 3],
            fitness=0.75,
        )

        assert path.resident_idx == 0
        assert len(path.path) == 5
        assert path.fitness == 0.75

    def test_ant_path_to_chromosome_row(self):
        """Test converting path to chromosome row."""
        path = AntPath(
            resident_idx=0,
            path=[1, 2, 0, 1, 3],
        )

        row = path.to_chromosome_row()

        assert isinstance(row, np.ndarray)
        assert len(row) == 5
        assert row[0] == 1
        assert row[2] == 0


class TestPheromoneMatrix:
    """Tests for PheromoneMatrix class."""

    def test_pheromone_matrix_creation(self):
        """Test creating pheromone matrix."""
        pm = PheromoneMatrix(
            n_residents=5,
            n_blocks=10,
            n_templates=3,
            initial_value=1.0,
        )

        assert pm.assignment.shape == (5, 10, 4)  # +1 for unassigned
        assert pm.transition.shape == (4, 4)
        assert np.all(pm.assignment == 1.0)

    def test_pheromone_evaporation(self):
        """Test pheromone evaporation."""
        pm = PheromoneMatrix(
            n_residents=3,
            n_blocks=5,
            n_templates=2,
            initial_value=1.0,
            evaporation_rate=0.1,
            min_pheromone=0.01,
        )

        pm.evaporate()

        # Should be 90% of original
        assert np.allclose(pm.assignment, 0.9)
        assert np.allclose(pm.transition, 0.9)

    def test_pheromone_deposit(self):
        """Test pheromone deposition."""
        pm = PheromoneMatrix(
            n_residents=3,
            n_blocks=5,
            n_templates=2,
            initial_value=1.0,
        )

        paths = [
            AntPath(resident_idx=0, path=[1, 1, 0, 2, 1], pheromone_contribution=0.5),
        ]

        pm.deposit(paths)

        # Check that pheromone increased on path
        assert pm.assignment[0, 0, 1] > 1.0
        assert pm.transition[0, 1] > 1.0  # Transition from 0 to 1

    def test_pheromone_min_max_bounds(self):
        """Test pheromone stays within bounds."""
        pm = PheromoneMatrix(
            n_residents=2,
            n_blocks=3,
            n_templates=2,
            initial_value=1.0,
            min_pheromone=0.1,
            max_pheromone=5.0,
        )

        # Deposit a lot of pheromone
        paths = [
            AntPath(
                resident_idx=0,
                path=[1, 1, 1],
                pheromone_contribution=10.0,
            ),
        ]
        pm.deposit(paths, elite_factor=3.0)

        # Should be capped at max
        assert np.all(pm.assignment <= 5.0)

        # Evaporate many times
        for _ in range(100):
            pm.evaporate()

        # Should be at least min
        assert np.all(pm.assignment >= 0.1)

    def test_get_assignment_probability(self):
        """Test probability distribution for assignment."""
        pm = PheromoneMatrix(
            n_residents=2,
            n_blocks=3,
            n_templates=2,
        )

        prob = pm.get_assignment_probability(
            resident_idx=0,
            block_idx=0,
        )

        # Should be valid probability distribution
        assert np.isclose(np.sum(prob), 1.0)
        assert np.all(prob >= 0)


class TestACOConfig:
    """Tests for ACO configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = ACOConfig()

        assert config.colony_size == 50
        assert config.alpha == 1.0
        assert config.beta == 2.0
        assert config.evaporation_rate == 0.1

    def test_custom_config(self):
        """Test custom configuration."""
        config = ACOConfig(
            colony_size=30,
            alpha=1.5,
            use_elite=False,
        )

        assert config.colony_size == 30
        assert config.alpha == 1.5
        assert config.use_elite is False


class TestAntColonySolver:
    """Tests for ACO solver."""

    def test_aco_initialization(self):
        """Test ACO solver initializes correctly."""
        config = ACOConfig(colony_size=20, max_iterations=10)
        solver = AntColonySolver(config=config, seed=42)

        assert solver.config.colony_size == 20
        assert solver.seed == 42

    def test_aco_get_pheromone_analysis(self):
        """Test pheromone analysis export."""
        solver = AntColonySolver()

        # Without pheromone matrix
        analysis = solver.get_pheromone_analysis()
        assert analysis == {}

        # With pheromone matrix
        solver.pheromone = PheromoneMatrix(
            n_residents=3,
            n_blocks=5,
            n_templates=2,
        )

        analysis = solver.get_pheromone_analysis()
        assert "pheromone_matrix" in analysis
        assert "n_hotspots" in analysis

    def test_aco_get_evolution_data(self):
        """Test evolution data export."""
        solver = AntColonySolver(config=ACOConfig(alpha=1.5, beta=2.5))

        data = solver.get_evolution_data()

        assert "algorithm" in data
        assert data["algorithm"] == "AntColonySolver"
        assert "aco_config" in data
        assert data["aco_config"]["alpha"] == 1.5
        assert data["aco_config"]["beta"] == 2.5
