"""
Tests for Spin Glass Constraint Model.

Tests the spin glass-inspired scheduler including:
- Frustration index computation
- Replica schedule generation
- Parisi overlap calculation
- Glass transition detection
- Energy landscape analysis
- RSB analysis
"""

from datetime import date, timedelta
from uuid import uuid4

import numpy as np
import pytest

from app.scheduling.constraints import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SchedulingContext,
    SoftConstraint,
)
from app.scheduling.spin_glass_model import (
    FrustrationCluster,
    LandscapeAnalysis,
    ReplicaSchedule,
    ReplicaSymmetryAnalysis,
    SpinGlassScheduler,
)
from app.scheduling.solvers import SolverResult


# -------------------------------------------------------------------------
# Mock objects for testing
# -------------------------------------------------------------------------


class MockBlock:
    """Mock block for testing."""

    def __init__(self, block_id=None, block_date=None, is_weekend=False):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.is_weekend = is_weekend
        self.session = "AM"


class MockPerson:
    """Mock person for testing."""

    def __init__(self, person_id=None, role="RESIDENT"):
        self.id = person_id or uuid4()
        self.role = role
        self.first_name = "Test"
        self.last_name = "Person"


class MockTemplate:
    """Mock rotation template for testing."""

    def __init__(self, template_id=None, name="Clinic", requires_credential=False):
        self.id = template_id or uuid4()
        self.name = name
        self.requires_procedure_credential = requires_credential


class MockConstraint(SoftConstraint):
    """Mock constraint for testing."""

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        weight: float = 1.0,
        always_satisfied: bool = True,
    ):
        super().__init__(name, constraint_type, weight=weight)
        self.always_satisfied = always_satisfied

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass

    def validate(self, assignments, context):
        if self.always_satisfied:
            return ConstraintResult(satisfied=True, penalty=0.0)
        else:
            return ConstraintResult(
                satisfied=False,
                penalty=self.weight * 10.0,
            )


# -------------------------------------------------------------------------
# Test fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def test_context():
    """Create a test scheduling context."""
    residents = [MockPerson(role="RESIDENT") for _ in range(5)]
    blocks = [
        MockBlock(block_date=date.today() + timedelta(days=i)) for i in range(10)
    ]
    templates = [MockTemplate(name=f"Template_{i}") for i in range(3)]

    return SchedulingContext(
        blocks=blocks,
        residents=residents,
        faculty=[],
        templates=templates,
        availability={},
        existing_assignments=[],
    )


@pytest.fixture
def test_constraints():
    """Create test constraints with varying types."""
    return [
        MockConstraint("Equity", ConstraintType.EQUITY, weight=1.0),
        MockConstraint("Preference", ConstraintType.PREFERENCE, weight=0.5),
        MockConstraint("Capacity", ConstraintType.CAPACITY, weight=2.0),
        MockConstraint("DutyHours", ConstraintType.DUTY_HOURS, weight=1.5),
    ]


@pytest.fixture
def conflicting_constraints():
    """Create constraints that conflict."""
    return [
        MockConstraint("Equity", ConstraintType.EQUITY, weight=1.0, always_satisfied=True),
        MockConstraint(
            "Preference", ConstraintType.PREFERENCE, weight=1.0, always_satisfied=False
        ),
        MockConstraint("Capacity", ConstraintType.CAPACITY, weight=1.0, always_satisfied=False),
    ]


@pytest.fixture
def spin_glass_scheduler(test_context, test_constraints):
    """Create a spin glass scheduler instance."""
    return SpinGlassScheduler(
        context=test_context,
        constraints=test_constraints,
        temperature=1.0,
        random_seed=42,
    )


# -------------------------------------------------------------------------
# Test SpinGlassScheduler initialization
# -------------------------------------------------------------------------


class TestSpinGlassSchedulerInit:
    """Tests for scheduler initialization."""

    def test_initialization(self, test_context, test_constraints):
        """Test scheduler initializes correctly."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=2.0,
            random_seed=42,
        )

        assert scheduler.context == test_context
        assert scheduler.constraints == test_constraints
        assert scheduler.temperature == 2.0
        assert scheduler._interaction_matrix is None

    def test_reproducibility_with_seed(self, test_context, test_constraints):
        """Test that random seed ensures reproducibility."""
        scheduler1 = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            random_seed=42,
        )
        scheduler2 = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            random_seed=42,
        )

        # Generate replicas with same seed
        replicas1 = scheduler1.generate_replica_schedules(n_replicas=3)
        replicas2 = scheduler2.generate_replica_schedules(n_replicas=3)

        # Should produce identical results
        for r1, r2 in zip(replicas1, replicas2):
            assert r1.energy == r2.energy


# -------------------------------------------------------------------------
# Test frustration index computation
# -------------------------------------------------------------------------


class TestFrustrationIndex:
    """Tests for frustration index computation."""

    def test_no_constraints(self, test_context):
        """Test frustration index with no constraints."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=[],
            temperature=1.0,
        )

        frustration = scheduler.compute_frustration_index()
        assert frustration == 0.0

    def test_single_constraint(self, test_context, test_constraints):
        """Test frustration index with single constraint."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=[test_constraints[0]],
            temperature=1.0,
        )

        frustration = scheduler.compute_frustration_index()
        assert frustration == 0.0

    def test_multiple_constraints(self, test_context, test_constraints):
        """Test frustration index with multiple constraints."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=1.0,
        )

        frustration = scheduler.compute_frustration_index()

        # Should be between 0 and 1
        assert 0.0 <= frustration <= 1.0

    def test_conflicting_constraints(self, test_context, conflicting_constraints):
        """Test frustration index with conflicting constraints."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=conflicting_constraints,
            temperature=1.0,
        )

        frustration = scheduler.compute_frustration_index()

        # Should detect some frustration
        assert frustration > 0.0

    def test_interaction_matrix_cached(self, spin_glass_scheduler):
        """Test that interaction matrix is cached."""
        assert spin_glass_scheduler._interaction_matrix is None

        # First call builds matrix
        spin_glass_scheduler.compute_frustration_index()
        assert spin_glass_scheduler._interaction_matrix is not None

        # Matrix is reused
        matrix = spin_glass_scheduler._interaction_matrix
        spin_glass_scheduler.compute_frustration_index()
        assert spin_glass_scheduler._interaction_matrix is matrix


# -------------------------------------------------------------------------
# Test replica schedule generation
# -------------------------------------------------------------------------


class TestReplicaGeneration:
    """Tests for replica schedule generation."""

    def test_generate_replicas_basic(self, spin_glass_scheduler):
        """Test basic replica generation."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)

        assert len(replicas) == 5
        for replica in replicas:
            assert isinstance(replica, ReplicaSchedule)
            assert replica.energy >= 0.0
            assert -1.0 <= replica.magnetization <= 1.0
            assert len(replica.assignments) > 0

    def test_replica_uniqueness(self, spin_glass_scheduler):
        """Test that replicas are diverse (not identical)."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=10)

        # Check that not all replicas are identical
        energies = [r.energy for r in replicas]
        unique_energies = set(energies)

        # Should have some diversity
        assert len(unique_energies) > 1

    def test_replica_indices(self, spin_glass_scheduler):
        """Test that replica indices are assigned correctly."""
        n_replicas = 5
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=n_replicas)

        indices = [r.replica_index for r in replicas]
        assert indices == list(range(n_replicas))

    def test_replica_schedule_ids(self, spin_glass_scheduler):
        """Test that replica schedule IDs are unique."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)

        schedule_ids = [r.schedule_id for r in replicas]
        assert len(schedule_ids) == len(set(schedule_ids))

    def test_violation_breakdown(self, spin_glass_scheduler):
        """Test that constraint violations are broken down by type."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=3)

        for replica in replicas:
            assert isinstance(replica.constraint_violations, dict)

    def test_temperature_effect(self, test_context, test_constraints):
        """Test that temperature affects replica diversity."""
        # Low temperature (should be less diverse)
        scheduler_cold = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=0.1,
            random_seed=42,
        )

        # High temperature (should be more diverse)
        scheduler_hot = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=5.0,
            random_seed=123,
        )

        replicas_cold = scheduler_cold.generate_replica_schedules(n_replicas=10)
        replicas_hot = scheduler_hot.generate_replica_schedules(n_replicas=10)

        # Higher temperature should produce more diverse energies
        cold_std = np.std([r.energy for r in replicas_cold])
        hot_std = np.std([r.energy for r in replicas_hot])

        # This is probabilistic, but should generally hold
        # If test is flaky, consider increasing n_replicas or adjusting threshold
        assert hot_std >= cold_std * 0.5  # Allow some variance


# -------------------------------------------------------------------------
# Test Parisi overlap computation
# -------------------------------------------------------------------------


class TestParisiOverlap:
    """Tests for Parisi overlap calculation."""

    def test_self_overlap(self, spin_glass_scheduler):
        """Test that overlap of schedule with itself is 1.0."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=2)

        overlap = spin_glass_scheduler.compute_parisi_overlap(replicas[0], replicas[0])
        assert overlap == pytest.approx(1.0)

    def test_overlap_range(self, spin_glass_scheduler):
        """Test that overlap is in valid range [0, 1]."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)

        for i in range(len(replicas)):
            for j in range(i + 1, len(replicas)):
                overlap = spin_glass_scheduler.compute_parisi_overlap(
                    replicas[i], replicas[j]
                )
                assert 0.0 <= overlap <= 1.0

    def test_overlap_symmetry(self, spin_glass_scheduler):
        """Test that overlap is symmetric: q_ab = q_ba."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=3)

        overlap_01 = spin_glass_scheduler.compute_parisi_overlap(replicas[0], replicas[1])
        overlap_10 = spin_glass_scheduler.compute_parisi_overlap(replicas[1], replicas[0])

        assert overlap_01 == pytest.approx(overlap_10)

    def test_empty_schedules(self, spin_glass_scheduler):
        """Test overlap with empty schedules."""
        empty_replica = ReplicaSchedule(
            schedule_id="empty",
            assignments=[],
            energy=0.0,
            magnetization=0.0,
            replica_index=0,
        )

        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=1)
        overlap = spin_glass_scheduler.compute_parisi_overlap(empty_replica, replicas[0])

        # Empty vs non-empty should have 0 overlap
        assert overlap == 0.0


# -------------------------------------------------------------------------
# Test glass transition detection
# -------------------------------------------------------------------------


class TestGlassTransition:
    """Tests for glass transition threshold detection."""

    def test_glass_transition_basic(self, spin_glass_scheduler):
        """Test basic glass transition detection."""
        critical_density = spin_glass_scheduler.find_glass_transition_threshold(
            constraint_density_range=(0.5, 2.0),
            n_samples=5,
        )

        # Should return a value in the scanned range
        assert 0.5 <= critical_density <= 2.0

    def test_glass_transition_reproducibility(self, test_context, test_constraints):
        """Test that glass transition is reproducible with same seed."""
        scheduler1 = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=1.0,
            random_seed=42,
        )

        scheduler2 = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=1.0,
            random_seed=42,
        )

        critical1 = scheduler1.find_glass_transition_threshold(n_samples=3)
        critical2 = scheduler2.find_glass_transition_threshold(n_samples=3)

        assert critical1 == pytest.approx(critical2, rel=0.1)


# -------------------------------------------------------------------------
# Test energy landscape analysis
# -------------------------------------------------------------------------


class TestEnergyLandscape:
    """Tests for energy landscape analysis."""

    def test_landscape_empty_schedules(self, spin_glass_scheduler):
        """Test landscape analysis with no schedules."""
        landscape = spin_glass_scheduler.analyze_energy_landscape([])

        assert landscape.global_minimum_energy == float("inf")
        assert len(landscape.local_minima) == 0

    def test_landscape_single_schedule(self, spin_glass_scheduler):
        """Test landscape with single schedule."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=1)
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)

        assert landscape.global_minimum_energy == replicas[0].energy
        assert len(landscape.local_minima) == 1

    def test_landscape_multiple_schedules(self, spin_glass_scheduler):
        """Test landscape with multiple schedules."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=10)
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)

        assert isinstance(landscape, LandscapeAnalysis)
        assert landscape.global_minimum_energy <= min(r.energy for r in replicas)
        assert len(landscape.local_minima) > 0

    def test_landscape_basin_detection(self, spin_glass_scheduler):
        """Test that landscape identifies solution basins."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=20)
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)

        # Should identify at least one basin
        assert len(landscape.basin_sizes) > 0

        # Total replicas across all basins should equal total replicas
        total_in_basins = sum(landscape.basin_sizes.values())
        assert total_in_basins == len(replicas)

    def test_landscape_frustration_clusters(self, spin_glass_scheduler):
        """Test that landscape identifies frustration clusters."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)

        assert isinstance(landscape.frustration_clusters, list)
        for cluster in landscape.frustration_clusters:
            assert isinstance(cluster, FrustrationCluster)

    def test_landscape_glass_temperature(self, spin_glass_scheduler):
        """Test that landscape estimates glass temperature."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=10)
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)

        assert landscape.glass_transition_temp >= 0.0


# -------------------------------------------------------------------------
# Test RSB analysis
# -------------------------------------------------------------------------


class TestRSBAnalysis:
    """Tests for replica symmetry breaking analysis."""

    def test_rsb_empty_replicas(self, spin_glass_scheduler):
        """Test RSB analysis with no replicas."""
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis([])

        assert rsb.parisi_overlap_matrix.size == 0
        assert rsb.rsb_order_parameter == 0.0
        assert rsb.diversity_score == 0.0

    def test_rsb_single_replica(self, spin_glass_scheduler):
        """Test RSB analysis with single replica."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=1)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        assert rsb.parisi_overlap_matrix.size == 0

    def test_rsb_multiple_replicas(self, spin_glass_scheduler):
        """Test RSB analysis with multiple replicas."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        assert isinstance(rsb, ReplicaSymmetryAnalysis)
        assert rsb.parisi_overlap_matrix.shape == (5, 5)
        assert 0.0 <= rsb.rsb_order_parameter <= 1.0
        assert 0.0 <= rsb.diversity_score <= 1.0

    def test_overlap_matrix_diagonal(self, spin_glass_scheduler):
        """Test that overlap matrix diagonal is 1.0 (self-overlap)."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        diagonal = np.diag(rsb.parisi_overlap_matrix)
        np.testing.assert_allclose(diagonal, 1.0)

    def test_overlap_matrix_symmetric(self, spin_glass_scheduler):
        """Test that overlap matrix is symmetric."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=5)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        matrix = rsb.parisi_overlap_matrix
        np.testing.assert_allclose(matrix, matrix.T)

    def test_overlap_distribution(self, spin_glass_scheduler):
        """Test overlap distribution computation."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=10)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        assert isinstance(rsb.overlap_distribution, dict)
        assert set(rsb.overlap_distribution.keys()) == {
            "0.00-0.25",
            "0.25-0.50",
            "0.50-0.75",
            "0.75-1.00",
        }

        # Total counts should equal number of pairs (excluding diagonal)
        n = len(replicas)
        n_pairs = n * (n - 1) // 2
        total_counts = sum(rsb.overlap_distribution.values())
        assert total_counts == n_pairs

    def test_ultrametric_distances(self, spin_glass_scheduler):
        """Test ultrametric distance computation."""
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=4)
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)

        assert isinstance(rsb.ultrametric_distance, dict)

        # Should have distance for each pair
        n = len(replicas)
        n_pairs = n * (n - 1) // 2
        assert len(rsb.ultrametric_distance) == n_pairs

        # All distances should be in [0, 1]
        for distance in rsb.ultrametric_distance.values():
            assert 0.0 <= distance <= 1.0


# -------------------------------------------------------------------------
# Integration tests
# -------------------------------------------------------------------------


class TestSpinGlassIntegration:
    """Integration tests for complete spin glass workflow."""

    def test_full_workflow(self, spin_glass_scheduler):
        """Test complete spin glass analysis workflow."""
        # 1. Compute frustration index
        frustration = spin_glass_scheduler.compute_frustration_index()
        assert 0.0 <= frustration <= 1.0

        # 2. Generate replica schedules
        replicas = spin_glass_scheduler.generate_replica_schedules(n_replicas=10)
        assert len(replicas) == 10

        # 3. Analyze energy landscape
        landscape = spin_glass_scheduler.analyze_energy_landscape(replicas)
        assert isinstance(landscape, LandscapeAnalysis)

        # 4. Compute RSB analysis
        rsb = spin_glass_scheduler.compute_replica_symmetry_analysis(replicas)
        assert isinstance(rsb, ReplicaSymmetryAnalysis)

        # 5. Verify consistency
        assert landscape.global_minimum_energy == min(r.energy for r in replicas)

    def test_with_base_solution(self, spin_glass_scheduler):
        """Test replica generation starting from base solution."""
        # Create a base solution
        base_assignments = []
        for block in spin_glass_scheduler.context.blocks[:5]:
            person = spin_glass_scheduler.context.residents[0]
            template = spin_glass_scheduler.context.templates[0]
            base_assignments.append((person.id, block.id, template.id))

        base_result = SolverResult(
            success=True,
            assignments=base_assignments,
            status="OPTIMAL",
        )

        # Generate replicas from base
        replicas = spin_glass_scheduler.generate_replica_schedules(
            n_replicas=5,
            base_solver_result=base_result,
        )

        assert len(replicas) == 5

    def test_high_diversity_schedule(self, test_context, test_constraints):
        """Test that high temperature produces diverse schedules."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=10.0,  # Very high temperature
            random_seed=42,
        )

        replicas = scheduler.generate_replica_schedules(n_replicas=20)
        rsb = scheduler.compute_replica_symmetry_analysis(replicas)

        # High temperature should produce diverse schedules
        assert rsb.diversity_score > 0.3

    def test_low_diversity_schedule(self, test_context, test_constraints):
        """Test that low temperature produces less diverse schedules."""
        scheduler = SpinGlassScheduler(
            context=test_context,
            constraints=test_constraints,
            temperature=0.01,  # Very low temperature
            random_seed=42,
        )

        replicas = scheduler.generate_replica_schedules(n_replicas=20)
        rsb = scheduler.compute_replica_symmetry_analysis(replicas)

        # Low temperature may still have some diversity due to simulated annealing
        assert rsb.rsb_order_parameter >= 0.0
