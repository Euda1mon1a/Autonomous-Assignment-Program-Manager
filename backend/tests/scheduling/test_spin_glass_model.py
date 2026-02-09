"""Tests for SpinGlassScheduler spin glass physics model (pure logic, no DB required)."""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

import numpy as np
import pytest

from app.scheduling.constraints import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
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


# ==================== Mock Objects ====================


@dataclass
class MockPerson:
    id: UUID = field(default_factory=uuid4)


@dataclass
class MockBlock:
    id: UUID = field(default_factory=uuid4)
    date: date = field(default_factory=lambda: date(2025, 1, 1))


@dataclass
class MockTemplate:
    id: UUID = field(default_factory=uuid4)


class ConcreteConstraint(Constraint):
    """Minimal concrete Constraint for testing."""

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        result: ConstraintResult | None = None,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
    ):
        super().__init__(name, constraint_type, priority)
        self._result = result or ConstraintResult(satisfied=True)

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass

    def validate(self, assignments, context):
        return self._result


class ConcreteSoftConstraint(SoftConstraint):
    """Minimal concrete SoftConstraint for testing."""

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        weight: float = 1.0,
        result: ConstraintResult | None = None,
    ):
        super().__init__(name, constraint_type, weight)
        self._result = result or ConstraintResult(satisfied=True)

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass

    def validate(self, assignments, context):
        return self._result


class ConcreteHardConstraint(HardConstraint):
    """Minimal concrete HardConstraint for testing."""

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        result: ConstraintResult | None = None,
    ):
        super().__init__(name, constraint_type)
        self._result = result or ConstraintResult(satisfied=True)

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass

    def validate(self, assignments, context):
        return self._result


def _make_context(
    n_residents: int = 3,
    n_blocks: int = 4,
    n_templates: int = 2,
) -> SchedulingContext:
    """Build a minimal SchedulingContext with mock objects."""
    residents = [MockPerson() for _ in range(n_residents)]
    blocks = [MockBlock() for _ in range(n_blocks)]
    templates = [MockTemplate() for _ in range(n_templates)]
    return SchedulingContext(
        residents=residents,
        faculty=[],
        blocks=blocks,
        templates=templates,
    )


def _make_scheduler(
    n_residents: int = 3,
    n_blocks: int = 4,
    constraints: list[Constraint] | None = None,
    temperature: float = 1.0,
    seed: int = 42,
) -> SpinGlassScheduler:
    """Build a SpinGlassScheduler with mock data."""
    ctx = _make_context(n_residents=n_residents, n_blocks=n_blocks)
    if constraints is None:
        constraints = []
    return SpinGlassScheduler(
        ctx, constraints, temperature=temperature, random_seed=seed
    )


def _make_replica(
    idx: int = 0,
    assignments: list[tuple[UUID, UUID, UUID | None]] | None = None,
    energy: float = 10.0,
    magnetization: float = 0.5,
) -> ReplicaSchedule:
    """Build a ReplicaSchedule with optional assignments."""
    if assignments is None:
        assignments = [(uuid4(), uuid4(), uuid4()) for _ in range(3)]
    return ReplicaSchedule(
        schedule_id=f"replica_{idx:03d}",
        assignments=assignments,
        energy=energy,
        magnetization=magnetization,
        replica_index=idx,
    )


# ==================== Dataclass Tests ====================


class TestFrustrationCluster:
    """Test FrustrationCluster dataclass."""

    def test_default_construction(self):
        fc = FrustrationCluster()
        assert fc.constraints == []
        assert fc.frustration_index == 0.0
        assert fc.affected_persons == set()
        assert fc.affected_blocks == set()
        assert fc.conflict_type == ""
        assert fc.resolution_suggestions == []

    def test_with_values(self):
        pid, bid = uuid4(), uuid4()
        fc = FrustrationCluster(
            constraints=["c1", "c2"],
            frustration_index=0.75,
            affected_persons={pid},
            affected_blocks={bid},
            conflict_type="equity_vs_preference",
            resolution_suggestions=["reduce c1 weight"],
        )
        assert fc.frustration_index == 0.75
        assert pid in fc.affected_persons
        assert len(fc.resolution_suggestions) == 1


class TestReplicaSchedule:
    """Test ReplicaSchedule dataclass."""

    def test_basic_construction(self):
        r = _make_replica(idx=5, energy=25.3, magnetization=-0.1)
        assert r.schedule_id == "replica_005"
        assert r.energy == 25.3
        assert r.magnetization == -0.1
        assert r.replica_index == 5
        assert len(r.assignments) == 3

    def test_constraint_violations_default(self):
        r = _make_replica()
        assert r.constraint_violations == {}

    def test_with_violations(self):
        r = ReplicaSchedule(
            schedule_id="r",
            assignments=[],
            energy=50.0,
            magnetization=0.0,
            replica_index=0,
            constraint_violations={"equity": 30.0, "capacity": 20.0},
        )
        assert r.constraint_violations["equity"] == 30.0


class TestLandscapeAnalysis:
    """Test LandscapeAnalysis dataclass."""

    def test_default_construction(self):
        la = LandscapeAnalysis(global_minimum_energy=5.0)
        assert la.global_minimum_energy == 5.0
        assert la.local_minima == []
        assert la.energy_barrier_heights == []
        assert la.basin_sizes == {}
        assert la.frustration_clusters == []
        assert la.glass_transition_temp == 0.0

    def test_with_basins(self):
        la = LandscapeAnalysis(
            global_minimum_energy=2.0,
            local_minima=[2.0, 5.0, 8.0],
            basin_sizes={0: 5, 1: 3, 2: 2},
        )
        assert len(la.local_minima) == 3
        assert la.basin_sizes[0] == 5


class TestReplicaSymmetryAnalysis:
    """Test ReplicaSymmetryAnalysis dataclass."""

    def test_default_construction(self):
        rsa = ReplicaSymmetryAnalysis()
        assert rsa.rsb_order_parameter == 0.0
        assert rsa.diversity_score == 0.0
        assert rsa.mean_overlap == 0.0
        assert rsa.ultrametric_distance == {}
        assert rsa.overlap_distribution == {}

    def test_with_matrix(self):
        matrix = np.eye(3)
        rsa = ReplicaSymmetryAnalysis(
            parisi_overlap_matrix=matrix,
            rsb_order_parameter=0.4,
            diversity_score=0.6,
            mean_overlap=0.3,
        )
        assert rsa.parisi_overlap_matrix.shape == (3, 3)
        assert rsa.rsb_order_parameter == 0.4


# ==================== SpinGlassScheduler Init Tests ====================


class TestSchedulerInit:
    """Test SpinGlassScheduler initialization."""

    def test_basic_construction(self):
        s = _make_scheduler()
        assert s.temperature == 1.0
        assert s._interaction_matrix is None

    def test_custom_temperature(self):
        s = _make_scheduler(temperature=2.5)
        assert s.temperature == 2.5

    def test_rng_deterministic(self):
        s1 = _make_scheduler(seed=123)
        s2 = _make_scheduler(seed=123)
        vals1 = [s1.rng.random() for _ in range(5)]
        vals2 = [s2.rng.random() for _ in range(5)]
        assert vals1 == vals2

    def test_context_stored(self):
        s = _make_scheduler(n_residents=5)
        assert len(s.context.residents) == 5


# ==================== Parisi Overlap Tests ====================


class TestComputeParisiOverlap:
    """Test compute_parisi_overlap Jaccard similarity."""

    def test_identical_schedules_full_overlap(self):
        s = _make_scheduler()
        shared = [(uuid4(), uuid4(), uuid4()) for _ in range(5)]
        r1 = _make_replica(assignments=list(shared))
        r2 = _make_replica(assignments=list(shared))
        assert s.compute_parisi_overlap(r1, r2) == 1.0

    def test_disjoint_schedules_zero_overlap(self):
        s = _make_scheduler()
        r1 = _make_replica(assignments=[(uuid4(), uuid4(), uuid4()) for _ in range(3)])
        r2 = _make_replica(assignments=[(uuid4(), uuid4(), uuid4()) for _ in range(3)])
        assert s.compute_parisi_overlap(r1, r2) == 0.0

    def test_partial_overlap(self):
        s = _make_scheduler()
        shared = (uuid4(), uuid4(), uuid4())
        r1 = _make_replica(assignments=[shared, (uuid4(), uuid4(), uuid4())])
        r2 = _make_replica(assignments=[shared, (uuid4(), uuid4(), uuid4())])
        overlap = s.compute_parisi_overlap(r1, r2)
        # 1 in intersection, 3 in union => 1/3
        assert overlap == pytest.approx(1 / 3)

    def test_empty_a_returns_zero(self):
        s = _make_scheduler()
        r1 = _make_replica(assignments=[])
        r2 = _make_replica()
        assert s.compute_parisi_overlap(r1, r2) == 0.0

    def test_both_empty_returns_zero(self):
        s = _make_scheduler()
        r1 = _make_replica(assignments=[])
        r2 = _make_replica(assignments=[])
        assert s.compute_parisi_overlap(r1, r2) == 0.0

    def test_symmetric(self):
        s = _make_scheduler()
        r1 = _make_replica()
        r2 = _make_replica()
        assert s.compute_parisi_overlap(r1, r2) == s.compute_parisi_overlap(r2, r1)


# ==================== Constraint Coupling Tests ====================


class TestEstimateConstraintCoupling:
    """Test _estimate_constraint_coupling heuristic."""

    def test_equity_vs_preference_negative(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        coupling = s._estimate_constraint_coupling(c1, c2)
        assert coupling == -0.5

    def test_preference_vs_equity_negative(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        c2 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        coupling = s._estimate_constraint_coupling(c1, c2)
        assert coupling == -0.5

    def test_same_type_positive(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq1", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("eq2", ConstraintType.EQUITY)
        coupling = s._estimate_constraint_coupling(c1, c2)
        assert coupling == 0.5

    def test_different_types_weak_positive(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("cap", ConstraintType.CAPACITY)
        c2 = ConcreteConstraint("duty", ConstraintType.DUTY_HOURS)
        coupling = s._estimate_constraint_coupling(c1, c2)
        assert coupling == 0.1

    def test_unknown_type_returns_zero(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("c1", ConstraintType.SUPERVISION)
        c2 = ConcreteConstraint("c2", ConstraintType.EQUITY)
        coupling = s._estimate_constraint_coupling(c1, c2)
        assert coupling == 0.0


# ==================== Interaction Matrix Tests ====================


class TestBuildInteractionMatrix:
    """Test _build_interaction_matrix."""

    def test_empty_constraints(self):
        s = _make_scheduler()
        s._build_interaction_matrix([])
        assert s._interaction_matrix == {}

    def test_single_constraint_no_pairs(self):
        s = _make_scheduler()
        c = ConcreteConstraint("c1", ConstraintType.EQUITY)
        s._build_interaction_matrix([c])
        assert s._interaction_matrix == {}

    def test_two_constraints_one_pair(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        s._build_interaction_matrix([c1, c2])
        assert len(s._interaction_matrix) == 1
        assert (0, 1) in s._interaction_matrix
        assert s._interaction_matrix[(0, 1)] == -0.5

    def test_three_constraints_three_pairs(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        c3 = ConcreteConstraint("cap", ConstraintType.CAPACITY)
        s._build_interaction_matrix([c1, c2, c3])
        assert len(s._interaction_matrix) == 3


# ==================== Frustration Index Tests ====================


class TestComputeFrustrationIndex:
    """Test compute_frustration_index."""

    def test_no_constraints_returns_zero(self):
        s = _make_scheduler()
        assert s.compute_frustration_index([]) == 0.0

    def test_single_constraint_returns_zero(self):
        s = _make_scheduler()
        c = ConcreteConstraint("c1", ConstraintType.EQUITY)
        assert s.compute_frustration_index([c]) == 0.0

    def test_conflicting_pair_fully_frustrated(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        index = s.compute_frustration_index([c1, c2])
        # Only 1 pair, and equity-vs-preference is negative -> 1/1 = 1.0
        assert index == 1.0

    def test_aligned_pair_no_frustration(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq1", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("eq2", ConstraintType.EQUITY)
        index = s.compute_frustration_index([c1, c2])
        assert index == 0.0

    def test_mixed_frustration(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        c3 = ConcreteConstraint("cap", ConstraintType.CAPACITY)
        index = s.compute_frustration_index([c1, c2, c3])
        # 3 pairs: eq-pref(-0.5), eq-cap(0.1), pref-cap(0.1)
        # 1 negative out of 3 => 1/3
        assert index == pytest.approx(1 / 3)

    def test_uses_cached_matrix(self):
        s = _make_scheduler()
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        # First call builds matrix
        s.compute_frustration_index([c1, c2])
        # Second call uses cached matrix (self._interaction_matrix already set)
        s.compute_frustration_index()
        assert s._interaction_matrix is not None


# ==================== Energy and Magnetization Tests ====================


class TestComputeEnergy:
    """Test _compute_energy."""

    def test_no_constraints_zero_energy(self):
        s = _make_scheduler()
        assignments = [(uuid4(), uuid4(), uuid4())]
        assert s._compute_energy(assignments) == 0.0

    def test_satisfied_constraint_adds_penalty(self):
        result = ConstraintResult(satisfied=True, penalty=5.0)
        c = ConcreteConstraint("c1", ConstraintType.EQUITY, result=result)
        s = _make_scheduler(constraints=[c])
        energy = s._compute_energy([(uuid4(), uuid4(), uuid4())])
        # Satisfied but has soft penalty => energy = 5.0
        assert energy == 5.0

    def test_violated_constraint_high_energy(self):
        result = ConstraintResult(satisfied=False, penalty=0.0)
        c = ConcreteConstraint("c1", ConstraintType.EQUITY, result=result)
        s = _make_scheduler(constraints=[c])
        energy = s._compute_energy([(uuid4(), uuid4(), uuid4())])
        # Violated, no get_penalty => default 100.0 + penalty(0.0)
        assert energy == 100.0

    def test_hard_constraint_violation_capped(self):
        result = ConstraintResult(satisfied=False, penalty=0.0)
        c = ConcreteHardConstraint("hard", ConstraintType.DUTY_HOURS, result=result)
        s = _make_scheduler(constraints=[c])
        energy = s._compute_energy([(uuid4(), uuid4(), uuid4())])
        # Hard constraint penalty = inf, capped to 1000.0
        assert energy == 1000.0


class TestComputeMagnetization:
    """Test _compute_magnetization."""

    def test_empty_assignments_zero(self):
        s = _make_scheduler()
        assert s._compute_magnetization([]) == 0.0

    def test_no_soft_constraints_zero(self):
        c = ConcreteConstraint("c", ConstraintType.EQUITY)
        s = _make_scheduler(constraints=[c])
        mag = s._compute_magnetization([(uuid4(), uuid4(), uuid4())])
        assert mag == 0.0

    def test_soft_constraint_perfect_alignment(self):
        result = ConstraintResult(satisfied=True, penalty=0.0)
        c = ConcreteSoftConstraint("soft", ConstraintType.PREFERENCE, result=result)
        s = _make_scheduler(constraints=[c])
        mag = s._compute_magnetization([(uuid4(), uuid4(), uuid4())])
        # penalty=0 => normalized=0 => alignment=1.0
        assert mag == 1.0

    def test_soft_constraint_high_penalty_low_alignment(self):
        result = ConstraintResult(satisfied=True, penalty=100.0)
        c = ConcreteSoftConstraint("soft", ConstraintType.PREFERENCE, result=result)
        s = _make_scheduler(constraints=[c])
        mag = s._compute_magnetization([(uuid4(), uuid4(), uuid4())])
        # penalty=100 => normalized=min(1.0, 100/100)=1.0 => alignment=0.0
        assert mag == 0.0


# ==================== Violation Analysis Tests ====================


class TestAnalyzeViolations:
    """Test _analyze_violations breakdown."""

    def test_no_constraints_empty(self):
        s = _make_scheduler()
        result = s._analyze_violations([(uuid4(), uuid4(), uuid4())])
        assert result == {}

    def test_single_constraint_breakdown(self):
        result = ConstraintResult(satisfied=True, penalty=15.0)
        c = ConcreteConstraint("eq1", ConstraintType.EQUITY, result=result)
        s = _make_scheduler(constraints=[c])
        breakdown = s._analyze_violations([(uuid4(), uuid4(), uuid4())])
        assert breakdown["equity"] == 15.0

    def test_multiple_same_type_summed(self):
        r1 = ConstraintResult(satisfied=True, penalty=10.0)
        r2 = ConstraintResult(satisfied=True, penalty=5.0)
        c1 = ConcreteConstraint("eq1", ConstraintType.EQUITY, result=r1)
        c2 = ConcreteConstraint("eq2", ConstraintType.EQUITY, result=r2)
        s = _make_scheduler(constraints=[c1, c2])
        breakdown = s._analyze_violations([(uuid4(), uuid4(), uuid4())])
        assert breakdown["equity"] == 15.0


# ==================== Solution Basins Tests ====================


class TestIdentifySolutionBasins:
    """Test _identify_solution_basins clustering."""

    def test_empty_schedules(self):
        s = _make_scheduler()
        basins = s._identify_solution_basins([])
        assert basins == {}

    def test_single_schedule_one_basin(self):
        s = _make_scheduler()
        r = _make_replica()
        basins = s._identify_solution_basins([r])
        assert len(basins) == 1
        assert basins[0] == [0]

    def test_identical_schedules_same_basin(self):
        s = _make_scheduler()
        shared = [(uuid4(), uuid4(), uuid4()) for _ in range(5)]
        r1 = _make_replica(idx=0, assignments=list(shared))
        r2 = _make_replica(idx=1, assignments=list(shared))
        basins = s._identify_solution_basins([r1, r2])
        assert len(basins) == 1
        assert set(basins[0]) == {0, 1}

    def test_disjoint_schedules_separate_basins(self):
        s = _make_scheduler()
        r1 = _make_replica(idx=0, assignments=[(uuid4(), uuid4(), uuid4())])
        r2 = _make_replica(idx=1, assignments=[(uuid4(), uuid4(), uuid4())])
        basins = s._identify_solution_basins([r1, r2])
        assert len(basins) == 2


# ==================== Energy Barriers Tests ====================


class TestEstimateEnergyBarriers:
    """Test _estimate_energy_barriers."""

    def test_single_basin_no_barriers(self):
        s = _make_scheduler()
        basins = {0: [0, 1]}
        r1 = _make_replica(idx=0, energy=10.0)
        r2 = _make_replica(idx=1, energy=12.0)
        barriers = s._estimate_energy_barriers([r1, r2], basins)
        assert barriers == []

    def test_two_basins_one_barrier(self):
        s = _make_scheduler()
        r1 = _make_replica(idx=0, energy=5.0)
        r2 = _make_replica(idx=1, energy=15.0)
        basins = {0: [0], 1: [1]}
        barriers = s._estimate_energy_barriers([r1, r2], basins)
        assert len(barriers) == 1
        assert barriers[0] == 10.0

    def test_three_basins_three_barriers(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i, energy=float(i * 10)) for i in range(3)]
        basins = {0: [0], 1: [1], 2: [2]}
        barriers = s._estimate_energy_barriers(replicas, basins)
        assert len(barriers) == 3


# ==================== Glass Temperature Tests ====================


class TestEstimateGlassTemperature:
    """Test _estimate_glass_temperature."""

    def test_empty_returns_zero(self):
        s = _make_scheduler()
        assert s._estimate_glass_temperature([]) == 0.0

    def test_identical_energies_zero(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i, energy=10.0) for i in range(5)]
        tg = s._estimate_glass_temperature(replicas)
        assert tg == 0.0

    def test_varied_energies_positive(self):
        s = _make_scheduler()
        energies = [5.0, 10.0, 15.0, 20.0, 25.0]
        replicas = [_make_replica(idx=i, energy=e) for i, e in enumerate(energies)]
        tg = s._estimate_glass_temperature(replicas)
        expected_std = np.std(energies)
        assert tg == pytest.approx(expected_std / 2.0)
        assert tg > 0


# ==================== Ultrametric Distance Tests ====================


class TestComputeUltrametricDistances:
    """Test _compute_ultrametric_distances."""

    def test_identity_matrix_zero_distances(self):
        s = _make_scheduler()
        matrix = np.eye(3)
        distances = s._compute_ultrametric_distances(matrix)
        for (i, j), d in distances.items():
            assert d == 1.0  # d = 1 - 0 = 1.0 for off-diagonal

    def test_full_overlap_zero_distance(self):
        s = _make_scheduler()
        matrix = np.ones((2, 2))
        distances = s._compute_ultrametric_distances(matrix)
        assert distances[(0, 1)] == 0.0

    def test_pair_count(self):
        s = _make_scheduler()
        matrix = np.eye(4)
        distances = s._compute_ultrametric_distances(matrix)
        # C(4,2) = 6 pairs
        assert len(distances) == 6


# ==================== Replica Symmetry Analysis Tests ====================


class TestReplicaSymmetryAnalysis:
    """Test compute_replica_symmetry_analysis."""

    def test_single_replica_empty(self):
        s = _make_scheduler()
        r = _make_replica()
        rsa = s.compute_replica_symmetry_analysis([r])
        assert rsa.rsb_order_parameter == 0.0
        assert rsa.diversity_score == 0.0

    def test_identical_replicas_low_diversity(self):
        s = _make_scheduler()
        shared = [(uuid4(), uuid4(), uuid4()) for _ in range(5)]
        replicas = [_make_replica(idx=i, assignments=list(shared)) for i in range(3)]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        assert rsa.mean_overlap == 1.0
        assert rsa.diversity_score == 0.0

    def test_disjoint_replicas_high_diversity(self):
        s = _make_scheduler()
        replicas = [
            _make_replica(idx=i, assignments=[(uuid4(), uuid4(), uuid4())])
            for i in range(4)
        ]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        assert rsa.mean_overlap == 0.0
        assert rsa.diversity_score == 1.0

    def test_overlap_matrix_shape(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i) for i in range(5)]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        assert rsa.parisi_overlap_matrix.shape == (5, 5)

    def test_overlap_matrix_diagonal_ones(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i) for i in range(3)]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        for i in range(3):
            assert rsa.parisi_overlap_matrix[i, i] == 1.0

    def test_overlap_distribution_bins(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i) for i in range(3)]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        assert set(rsa.overlap_distribution.keys()) == {
            "0.00-0.25",
            "0.25-0.50",
            "0.50-0.75",
            "0.75-1.00",
        }

    def test_rsb_parameter_bounded(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i) for i in range(5)]
        rsa = s.compute_replica_symmetry_analysis(replicas)
        assert 0.0 <= rsa.rsb_order_parameter <= 1.0


# ==================== Energy Landscape Tests ====================


class TestAnalyzeEnergyLandscape:
    """Test analyze_energy_landscape."""

    def test_empty_schedules_inf_energy(self):
        s = _make_scheduler()
        la = s.analyze_energy_landscape([])
        assert la.global_minimum_energy == float("inf")

    def test_single_schedule(self):
        s = _make_scheduler()
        r = _make_replica(energy=7.5)
        la = s.analyze_energy_landscape([r])
        assert la.global_minimum_energy == 7.5
        assert len(la.basin_sizes) == 1

    def test_multiple_disjoint_schedules(self):
        s = _make_scheduler()
        replicas = [
            _make_replica(
                idx=i,
                energy=float(i * 5),
                assignments=[(uuid4(), uuid4(), uuid4())],
            )
            for i in range(4)
        ]
        la = s.analyze_energy_landscape(replicas)
        assert la.global_minimum_energy == 0.0
        assert len(la.local_minima) >= 1
        assert la.local_minima == sorted(la.local_minima)

    def test_glass_temperature_computed(self):
        s = _make_scheduler()
        replicas = [_make_replica(idx=i, energy=float(i * 10)) for i in range(5)]
        la = s.analyze_energy_landscape(replicas)
        assert la.glass_transition_temp > 0


# ==================== Propose Move Tests ====================


class TestProposeMove:
    """Test _propose_move schedule modification."""

    def test_empty_assignments_returns_empty(self):
        s = _make_scheduler()
        result = s._propose_move([])
        assert result == []

    def test_move_returns_same_length(self):
        s = _make_scheduler(n_residents=3, n_blocks=5)
        assignments = [(uuid4(), uuid4(), uuid4()) for _ in range(5)]
        result = s._propose_move(assignments)
        assert len(result) == 5

    def test_deterministic_with_shared_context(self):
        ctx = _make_context(n_residents=3, n_blocks=5)
        s1 = SpinGlassScheduler(ctx, [], temperature=1.0, random_seed=99)
        s2 = SpinGlassScheduler(ctx, [], temperature=1.0, random_seed=99)
        assignments = [(uuid4(), uuid4(), uuid4()) for _ in range(3)]
        r1 = s1._propose_move(list(assignments))
        r2 = s2._propose_move(list(assignments))
        # Same seed + same context => same random choice => same result
        assert r1 == r2


# ==================== Frustration Clusters Tests ====================


class TestIdentifyFrustrationClusters:
    """Test _identify_frustration_clusters."""

    def test_no_matrix_returns_empty(self):
        s = _make_scheduler()
        assert s._identify_frustration_clusters() == []

    def test_no_negative_couplings_empty(self):
        s = _make_scheduler()
        s._interaction_matrix = {(0, 1): 0.5, (0, 2): 0.1}
        assert s._identify_frustration_clusters() == []

    def test_strong_negative_produces_cluster(self):
        c1 = ConcreteConstraint("eq", ConstraintType.EQUITY)
        c2 = ConcreteConstraint("pref", ConstraintType.PREFERENCE)
        s = _make_scheduler(constraints=[c1, c2])
        s._interaction_matrix = {(0, 1): -0.5}
        clusters = s._identify_frustration_clusters()
        assert len(clusters) == 1
        assert clusters[0].frustration_index == 0.5
        assert "eq" in clusters[0].constraints
        assert "pref" in clusters[0].constraints

    def test_weak_negative_ignored(self):
        s = _make_scheduler()
        s._interaction_matrix = {(0, 1): -0.2}  # Above -0.3 threshold
        assert s._identify_frustration_clusters() == []

    def test_max_five_clusters(self):
        constraints = [
            ConcreteConstraint(f"c{i}", ConstraintType.EQUITY) for i in range(12)
        ]
        s = _make_scheduler(constraints=constraints)
        # Create 10 strongly negative pairs
        s._interaction_matrix = {(i, i + 1): -0.5 for i in range(10)}
        clusters = s._identify_frustration_clusters()
        assert len(clusters) <= 5
