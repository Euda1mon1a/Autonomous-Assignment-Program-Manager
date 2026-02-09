"""Tests for QUBO template optimization schemas (Pydantic validation and Field coverage)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.qubo_templates import (
    TemplateDesirabilityLevel,
    QUBOObjectiveWeight,
    QUBOAnnealingConfig,
    QUBOParetoConfig,
    TemplateDesirabilityMapping,
    QUBOTemplateOptimizeRequest,
    ParetoSolutionSchema,
    EnergyLandscapePointSchema,
    EnergyLandscapeSchema,
    BenchmarkResultSchema,
    BenchmarkComparisonSchema,
    AssignmentSchema,
    QUBOStatisticsSchema,
    QUBOTemplateOptimizeResponse,
    QUBOStatusResponse,
    QuantumAdvantageScenario,
    QuantumAdvantageDocResponse,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestTemplateDesirabilityLevel:
    def test_values(self):
        assert TemplateDesirabilityLevel.HIGHLY_DESIRABLE.value == "highly_desirable"
        assert TemplateDesirabilityLevel.NEUTRAL.value == "neutral"
        assert TemplateDesirabilityLevel.UNDESIRABLE.value == "undesirable"

    def test_count(self):
        assert len(TemplateDesirabilityLevel) == 3

    def test_is_str(self):
        assert isinstance(TemplateDesirabilityLevel.NEUTRAL, str)


# ===========================================================================
# QUBOObjectiveWeight Tests
# ===========================================================================


class TestQUBOObjectiveWeight:
    def test_defaults(self):
        r = QUBOObjectiveWeight()
        assert r.coverage == 1.0
        assert r.fairness == 1.0
        assert r.preference == 0.5
        assert r.learning == 0.3

    def test_boundaries(self):
        r = QUBOObjectiveWeight(
            coverage=0.0, fairness=0.0, preference=0.0, learning=0.0
        )
        assert r.coverage == 0.0

        r = QUBOObjectiveWeight(
            coverage=2.0, fairness=2.0, preference=2.0, learning=2.0
        )
        assert r.coverage == 2.0

    def test_above_max(self):
        with pytest.raises(ValidationError):
            QUBOObjectiveWeight(coverage=2.1)

    def test_negative(self):
        with pytest.raises(ValidationError):
            QUBOObjectiveWeight(fairness=-0.1)


# ===========================================================================
# QUBOAnnealingConfig Tests
# ===========================================================================


class TestQUBOAnnealingConfig:
    def test_defaults(self):
        r = QUBOAnnealingConfig()
        assert r.num_reads == 100
        assert r.num_sweeps == 1000
        assert r.beta_start == 0.1
        assert r.beta_end == 4.2
        assert r.use_adaptive_temperature is True

    # --- num_reads ge=1, le=1000 ---

    def test_num_reads_boundaries(self):
        r = QUBOAnnealingConfig(num_reads=1)
        assert r.num_reads == 1
        r = QUBOAnnealingConfig(num_reads=1000)
        assert r.num_reads == 1000

    def test_num_reads_zero(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(num_reads=0)

    def test_num_reads_above_max(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(num_reads=1001)

    # --- num_sweeps ge=100, le=10000 ---

    def test_num_sweeps_boundaries(self):
        r = QUBOAnnealingConfig(num_sweeps=100)
        assert r.num_sweeps == 100
        r = QUBOAnnealingConfig(num_sweeps=10000)
        assert r.num_sweeps == 10000

    def test_num_sweeps_below_min(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(num_sweeps=99)

    def test_num_sweeps_above_max(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(num_sweeps=10001)

    # --- beta_start ge=0.01, le=1.0 ---

    def test_beta_start_boundaries(self):
        r = QUBOAnnealingConfig(beta_start=0.01)
        assert r.beta_start == 0.01
        r = QUBOAnnealingConfig(beta_start=1.0)
        assert r.beta_start == 1.0

    def test_beta_start_below_min(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(beta_start=0.009)

    def test_beta_start_above_max(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(beta_start=1.1)

    # --- beta_end ge=1.0, le=10.0 ---

    def test_beta_end_boundaries(self):
        r = QUBOAnnealingConfig(beta_end=1.0)
        assert r.beta_end == 1.0
        r = QUBOAnnealingConfig(beta_end=10.0)
        assert r.beta_end == 10.0

    def test_beta_end_below_min(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(beta_end=0.9)

    def test_beta_end_above_max(self):
        with pytest.raises(ValidationError):
            QUBOAnnealingConfig(beta_end=10.1)


# ===========================================================================
# QUBOParetoConfig Tests
# ===========================================================================


class TestQUBOParetoConfig:
    def test_defaults(self):
        r = QUBOParetoConfig()
        assert r.enabled is True
        assert r.population_size == 50
        assert r.generations == 100
        assert r.objectives == ["coverage", "fairness", "preference"]

    # --- population_size ge=10, le=200 ---

    def test_population_size_boundaries(self):
        r = QUBOParetoConfig(population_size=10)
        assert r.population_size == 10
        r = QUBOParetoConfig(population_size=200)
        assert r.population_size == 200

    def test_population_size_below_min(self):
        with pytest.raises(ValidationError):
            QUBOParetoConfig(population_size=9)

    def test_population_size_above_max(self):
        with pytest.raises(ValidationError):
            QUBOParetoConfig(population_size=201)

    # --- generations ge=10, le=500 ---

    def test_generations_boundaries(self):
        r = QUBOParetoConfig(generations=10)
        assert r.generations == 10
        r = QUBOParetoConfig(generations=500)
        assert r.generations == 500

    def test_generations_below_min(self):
        with pytest.raises(ValidationError):
            QUBOParetoConfig(generations=9)

    def test_generations_above_max(self):
        with pytest.raises(ValidationError):
            QUBOParetoConfig(generations=501)


# ===========================================================================
# TemplateDesirabilityMapping Tests
# ===========================================================================


class TestTemplateDesirabilityMapping:
    def test_valid(self):
        r = TemplateDesirabilityMapping(
            template_name="ICU",
            desirability=TemplateDesirabilityLevel.HIGHLY_DESIRABLE,
        )
        assert r.desirability == TemplateDesirabilityLevel.HIGHLY_DESIRABLE


# ===========================================================================
# QUBOTemplateOptimizeRequest Tests
# ===========================================================================


class TestQUBOTemplateOptimizeRequest:
    def _valid_kwargs(self):
        return {
            "start_date": date(2026, 3, 1),
            "end_date": date(2026, 3, 31),
        }

    def test_valid_minimal(self):
        r = QUBOTemplateOptimizeRequest(**self._valid_kwargs())
        assert r.person_ids is None
        assert r.template_ids is None
        assert r.desirability_mappings is None
        assert r.seed is None
        assert r.timeout_seconds == 120.0
        assert r.include_energy_landscape is True
        assert r.include_benchmarks is False

    def test_defaults_create_sub_objects(self):
        r = QUBOTemplateOptimizeRequest(**self._valid_kwargs())
        assert r.objective_weights.coverage == 1.0
        assert r.annealing_config.num_reads == 100
        assert r.pareto_config.enabled is True

    # --- model_validator: end_date must be after start_date ---

    def test_end_date_equals_start_date(self):
        with pytest.raises(ValidationError):
            QUBOTemplateOptimizeRequest(
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 1),
            )

    def test_end_date_before_start_date(self):
        with pytest.raises(ValidationError):
            QUBOTemplateOptimizeRequest(
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
            )

    # --- timeout_seconds ge=10.0, le=600.0 ---

    def test_timeout_boundaries(self):
        kw = self._valid_kwargs()
        kw["timeout_seconds"] = 10.0
        r = QUBOTemplateOptimizeRequest(**kw)
        assert r.timeout_seconds == 10.0

        kw["timeout_seconds"] = 600.0
        r = QUBOTemplateOptimizeRequest(**kw)
        assert r.timeout_seconds == 600.0

    def test_timeout_below_min(self):
        kw = self._valid_kwargs()
        kw["timeout_seconds"] = 9.9
        with pytest.raises(ValidationError):
            QUBOTemplateOptimizeRequest(**kw)

    def test_timeout_above_max(self):
        kw = self._valid_kwargs()
        kw["timeout_seconds"] = 600.1
        with pytest.raises(ValidationError):
            QUBOTemplateOptimizeRequest(**kw)

    def test_with_person_ids(self):
        kw = self._valid_kwargs()
        kw["person_ids"] = [uuid4(), uuid4()]
        r = QUBOTemplateOptimizeRequest(**kw)
        assert len(r.person_ids) == 2


# ===========================================================================
# ParetoSolutionSchema Tests
# ===========================================================================


class TestParetoSolutionSchema:
    def test_valid(self):
        r = ParetoSolutionSchema(
            solution_id=1,
            objectives={"coverage": 0.9, "fairness": 0.85},
            num_assignments=50,
        )
        assert r.rank == 0
        assert r.crowding_distance == 0.0


# ===========================================================================
# EnergyLandscapePointSchema Tests
# ===========================================================================


class TestEnergyLandscapePointSchema:
    def test_valid(self):
        r = EnergyLandscapePointSchema(energy=-5.0)
        assert r.is_local_minimum is False
        assert r.tunneling_probability == 0.0
        assert r.basin_size == 1
        assert r.objectives == {}


# ===========================================================================
# EnergyLandscapeSchema Tests
# ===========================================================================


class TestEnergyLandscapeSchema:
    def test_valid(self):
        r = EnergyLandscapeSchema(
            num_samples=100,
            num_local_minima=5,
            global_minimum_energy=-10.0,
            energy_range={"min": -10.0, "max": 5.0},
        )
        assert r.points == []
        assert r.minima == []


# ===========================================================================
# BenchmarkResultSchema Tests
# ===========================================================================


class TestBenchmarkResultSchema:
    def test_valid(self):
        r = BenchmarkResultSchema(
            approach="qubo",
            success=True,
            num_assignments=50,
            runtime_seconds=30.0,
        )
        assert r.objective_value is None

    def test_with_objective(self):
        r = BenchmarkResultSchema(
            approach="greedy",
            success=True,
            num_assignments=45,
            runtime_seconds=0.5,
            objective_value=-8.5,
        )
        assert r.objective_value == -8.5


# ===========================================================================
# BenchmarkComparisonSchema Tests
# ===========================================================================


class TestBenchmarkComparisonSchema:
    def _make_result(self, approach="qubo"):
        return BenchmarkResultSchema(
            approach=approach, success=True, num_assignments=50, runtime_seconds=1.0
        )

    def test_valid(self):
        r = BenchmarkComparisonSchema(
            qubo=self._make_result("qubo"),
            greedy=self._make_result("greedy"),
            random=self._make_result("random"),
            qubo_vs_greedy_improvement=15.0,
            qubo_vs_random_improvement=30.0,
        )
        assert r.qubo_vs_greedy_improvement == 15.0


# ===========================================================================
# AssignmentSchema Tests
# ===========================================================================


class TestAssignmentSchema:
    def test_valid(self):
        r = AssignmentSchema(person_id=uuid4(), block_id=uuid4())
        assert r.template_id is None

    def test_with_template(self):
        r = AssignmentSchema(person_id=uuid4(), block_id=uuid4(), template_id=uuid4())
        assert r.template_id is not None


# ===========================================================================
# QUBOStatisticsSchema Tests
# ===========================================================================


class TestQUBOStatisticsSchema:
    def test_valid(self):
        r = QUBOStatisticsSchema(
            num_variables=500,
            num_qubo_terms=10000,
            qubo_energy=-5.0,
            refined_energy=-7.0,
            final_energy=-8.0,
            improvement=3.0,
            num_assignments=50,
        )
        assert r.objectives == {}
        assert r.pareto_frontier_size == 0
        assert r.num_local_minima == 0


# ===========================================================================
# QUBOTemplateOptimizeResponse Tests
# ===========================================================================


class TestQUBOTemplateOptimizeResponse:
    def test_valid_minimal(self):
        r = QUBOTemplateOptimizeResponse(
            success=True,
            message="Optimization complete",
            runtime_seconds=30.0,
        )
        assert r.assignments == []
        assert r.statistics is None
        assert r.pareto_frontier == []
        assert r.recommended_solution_id is None
        assert r.energy_landscape is None
        assert r.benchmarks is None
        assert r.quantum_advantage_estimate is None


# ===========================================================================
# QUBOStatusResponse Tests
# ===========================================================================


class TestQUBOStatusResponse:
    def test_valid(self):
        r = QUBOStatusResponse(
            available=True,
            features={"pareto": True, "annealing": True},
            recommended_problem_size={"min": 10, "max": 500},
            quantum_libraries={"dwave": False, "qiskit": False},
        )
        assert r.available is True


# ===========================================================================
# QuantumAdvantageScenario Tests
# ===========================================================================


class TestQuantumAdvantageScenario:
    def test_valid(self):
        r = QuantumAdvantageScenario(
            scenario_name="Large-Scale Scheduling",
            description="When problem size exceeds classical solver capacity",
            problem_characteristics=["high_connectivity", "many_constraints"],
            expected_speedup="2-10x",
            conditions=["Problem size > 1000 variables"],
        )
        assert r.expected_speedup == "2-10x"


# ===========================================================================
# QuantumAdvantageDocResponse Tests
# ===========================================================================


class TestQuantumAdvantageDocResponse:
    def test_valid(self):
        r = QuantumAdvantageDocResponse(
            overview="Quantum approaches may help scheduling",
            scenarios=[],
            current_limitations=["NISQ era hardware constraints"],
            recommendations=["Use for exploratory analysis"],
        )
        assert len(r.scenarios) == 0
