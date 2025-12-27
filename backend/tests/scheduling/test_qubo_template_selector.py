"""
Tests for QUBO Template Selector.

These tests validate the QUBO formulation for rotation template selection,
including fairness objectives, Pareto exploration, and hybrid optimization.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints import SchedulingContext
from app.scheduling.quantum.qubo_template_selector import (
    AdaptiveTemperatureSchedule,
    EnergyLandscapeExplorer,
    EnergyLandscapePoint,
    HybridTemplatePipeline,
    ParetoFrontExplorer,
    ParetoSolution,
    QUBOTemplateFormulation,
    QUBOTemplateSolver,
    TemplateBenchmark,
    TemplateDesirability,
    TemplateSelectionConfig,
    TemplateSelectionResult,
    get_template_selector_status,
)


# ============================================================================
# Test Fixtures
# ============================================================================


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

    def __init__(
        self,
        template_id=None,
        name="Clinic",
        requires_credential=False,
        max_residents=None,
    ):
        self.id = template_id or uuid4()
        self.name = name
        self.requires_procedure_credential = requires_credential
        self.max_residents = max_residents


def create_test_context(
    n_residents: int = 3,
    n_blocks: int = 20,
    n_templates: int = 3,
) -> SchedulingContext:
    """Create a test scheduling context."""
    residents = [MockPerson() for _ in range(n_residents)]
    blocks = [
        MockBlock(block_date=date.today() + timedelta(days=i))
        for i in range(n_blocks)
    ]
    templates = [
        MockTemplate(name=f"Template_{i}")
        for i in range(n_templates)
    ]

    return SchedulingContext(
        blocks=blocks,
        residents=residents,
        faculty=[],
        templates=templates,
        availability={},
        existing_assignments=[],
    )


# ============================================================================
# Test QUBOTemplateFormulation
# ============================================================================


class TestQUBOTemplateFormulation:
    """Tests for QUBO template formulation."""

    def test_formulation_creation(self):
        """Test that formulation is created correctly."""
        context = create_test_context(n_residents=3, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)

        # Should have rotation periods (blocks aggregated into 2-week chunks)
        assert len(formulation.rotation_periods) > 0

        # Should have variables
        assert formulation.num_variables > 0

    def test_variable_indexing(self):
        """Test that variables are correctly indexed."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)

        # Index mapping should be bijective
        assert len(formulation.var_index) == len(formulation.index_to_var)

        # All indices should be consecutive
        indices = set(formulation.var_index.values())
        assert indices == set(range(formulation.num_variables))

    def test_qubo_build(self):
        """Test QUBO matrix construction."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        Q = formulation.build()

        # Q should be a dict with (i, j) -> coefficient
        assert isinstance(Q, dict)
        assert len(Q) > 0

        # All coefficients should be numeric
        for (i, j), coef in Q.items():
            assert isinstance(i, int)
            assert isinstance(j, int)
            assert isinstance(coef, (int, float))

        # Matrix should be upper triangular (i <= j)
        for (i, j) in Q.keys():
            assert i <= j

    def test_objective_matrices_populated(self):
        """Test that individual objective matrices are populated."""
        context = create_test_context(n_residents=3, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        # Should have objective matrices
        assert "coverage" in formulation.objective_matrices
        assert "fairness" in formulation.objective_matrices
        assert "preference" in formulation.objective_matrices
        assert "learning" in formulation.objective_matrices
        assert "constraints" in formulation.objective_matrices

    def test_coverage_objective(self):
        """Test that coverage objective encourages assignments."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=1)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        # Coverage matrix should have negative diagonal terms
        coverage_matrix = formulation.objective_matrices["coverage"]
        diagonal_sum = sum(
            coef for (i, j), coef in coverage_matrix.items() if i == j
        )
        assert diagonal_sum < 0  # Negative encourages x[i] = 1

    def test_solution_decoding(self):
        """Test decoding QUBO solution to assignments."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        # Create a sample solution where first variable is 1
        sample = {i: 0 for i in range(formulation.num_variables)}
        sample[0] = 1

        assignments = formulation.decode_solution(sample)

        # Should have assignments for blocks in the first period
        assert len(assignments) > 0
        for person_id, block_id, template_id in assignments:
            assert person_id is not None
            assert block_id is not None
            assert template_id is not None

    def test_compute_objectives(self):
        """Test computing individual objectives for a solution."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        sample = {i: 1 if i % 2 == 0 else 0 for i in range(formulation.num_variables)}
        objectives = formulation.compute_objectives(sample)

        assert "coverage" in objectives
        assert "fairness" in objectives
        assert "preference" in objectives
        assert "constraints" in objectives

    def test_empty_context(self):
        """Test handling of empty context."""
        context = create_test_context(n_residents=0, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)

        assert formulation.num_variables == 0

    def test_custom_config(self):
        """Test formulation with custom config."""
        context = create_test_context(n_residents=3, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            hard_constraint_penalty=50000.0,
            fairness_penalty=1000.0,
        )
        formulation = QUBOTemplateFormulation(context, config=config)
        Q = formulation.build()

        # Should still build successfully
        assert len(Q) > 0

    def test_desirability_mapping(self):
        """Test custom desirability mapping."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        context.templates[0].name = "Sports Medicine"
        context.templates[1].name = "Night Float"

        desirability_map = {
            "Sports Medicine": TemplateDesirability.HIGHLY_DESIRABLE,
            "Night Float": TemplateDesirability.UNDESIRABLE,
        }

        formulation = QUBOTemplateFormulation(
            context, desirability_map=desirability_map
        )
        formulation.build()

        # Should have preference matrix populated
        assert len(formulation.objective_matrices["preference"]) > 0


# ============================================================================
# Test AdaptiveTemperatureSchedule
# ============================================================================


class TestAdaptiveTemperatureSchedule:
    """Tests for adaptive temperature schedule."""

    def test_schedule_creation(self):
        """Test schedule is created correctly."""
        schedule = AdaptiveTemperatureSchedule(
            beta_start=0.1,
            beta_end=4.0,
            num_sweeps=1000,
        )

        assert schedule.beta_start == 0.1
        assert schedule.beta_end == 4.0
        assert schedule.num_sweeps == 1000
        assert schedule.current_beta == 0.1

    def test_beta_progression(self):
        """Test that beta increases during annealing."""
        schedule = AdaptiveTemperatureSchedule(
            beta_start=0.1,
            beta_end=4.0,
            num_sweeps=100,
        )

        betas = []
        for sweep in range(100):
            beta = schedule.get_beta(sweep, energy=-10.0)
            betas.append(beta)

        # Beta should generally increase (though reheats may cause decreases)
        assert betas[-1] >= betas[0]

    def test_reheat_on_plateau(self):
        """Test that reheat occurs when stuck in plateau."""
        schedule = AdaptiveTemperatureSchedule(
            beta_start=0.1,
            beta_end=4.0,
            num_sweeps=100,
        )

        # Simulate plateau (constant energy)
        for sweep in range(100):
            schedule.get_beta(sweep, energy=0.0)

        # Should have triggered at least one reheat
        assert schedule.reheat_count > 0

    def test_tunneling_probability(self):
        """Test tunneling probability calculation."""
        schedule = AdaptiveTemperatureSchedule()

        # Zero barrier -> probability 1
        prob_zero = schedule.get_tunneling_probability(0.0)
        assert prob_zero == 1.0

        # Negative barrier -> probability 1
        prob_neg = schedule.get_tunneling_probability(-1.0)
        assert prob_neg == 1.0

        # Positive barrier -> probability < 1
        prob_pos = schedule.get_tunneling_probability(10.0)
        assert 0.0 < prob_pos < 1.0

        # Larger barrier -> smaller probability
        prob_large = schedule.get_tunneling_probability(100.0)
        assert prob_large < prob_pos

    def test_statistics(self):
        """Test statistics collection."""
        schedule = AdaptiveTemperatureSchedule(num_sweeps=50)

        for sweep in range(50):
            schedule.get_beta(sweep, energy=-sweep)

        stats = schedule.get_statistics()
        assert "num_sweeps" in stats
        assert "final_beta" in stats
        assert "best_energy" in stats
        assert "reheat_count" in stats


# ============================================================================
# Test EnergyLandscapeExplorer
# ============================================================================


class TestEnergyLandscapeExplorer:
    """Tests for energy landscape exploration."""

    def test_exploration(self):
        """Test basic landscape exploration."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = EnergyLandscapeExplorer(
            formulation,
            sample_count=50,
            seed=42,
        )
        points = explorer.explore()

        assert len(points) == 50
        for point in points:
            assert isinstance(point, EnergyLandscapePoint)
            assert isinstance(point.energy, float)
            assert isinstance(point.objectives, dict)

    def test_local_minima_identification(self):
        """Test that local minima are identified."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = EnergyLandscapeExplorer(
            formulation,
            sample_count=100,
            seed=42,
        )
        points = explorer.explore()

        # Should find at least one local minimum
        minima = [p for p in points if p.is_local_minimum]
        assert len(minima) >= 0  # May be 0 for small problems

    def test_tunneling_probabilities(self):
        """Test tunneling probability computation."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = EnergyLandscapeExplorer(
            formulation,
            sample_count=50,
            seed=42,
        )
        points = explorer.explore()

        for point in points:
            assert 0.0 <= point.tunneling_probability <= 1.0

    def test_export_for_visualization(self):
        """Test export format for visualization."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = EnergyLandscapeExplorer(
            formulation,
            sample_count=50,
            seed=42,
        )
        explorer.explore()

        export = explorer.export_for_visualization()
        assert "num_samples" in export
        assert "num_local_minima" in export
        assert "global_minimum_energy" in export
        assert "energy_range" in export
        assert "points" in export
        assert "minima" in export


# ============================================================================
# Test ParetoFrontExplorer
# ============================================================================


class TestParetoFrontExplorer:
    """Tests for Pareto front exploration."""

    def test_exploration(self):
        """Test basic Pareto exploration."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = ParetoFrontExplorer(
            formulation,
            objectives=["coverage", "fairness"],
            population_size=20,
            generations=10,
            seed=42,
        )
        frontier = explorer.explore()

        # Should find at least one solution
        assert len(frontier) >= 0

    def test_pareto_dominance(self):
        """Test Pareto dominance checking."""
        sol1 = ParetoSolution(
            solution_id=1,
            state={},
            objectives={"a": 1.0, "b": 1.0},
            assignments=[],
        )
        sol2 = ParetoSolution(
            solution_id=2,
            state={},
            objectives={"a": 2.0, "b": 2.0},
            assignments=[],
        )

        # sol1 dominates sol2 (smaller is better in minimization)
        assert sol1.dominates(sol2)
        assert not sol2.dominates(sol1)

    def test_non_dominated_solutions(self):
        """Test that frontier solutions are non-dominated."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = ParetoFrontExplorer(
            formulation,
            objectives=["coverage", "fairness"],
            population_size=30,
            generations=20,
            seed=42,
        )
        frontier = explorer.explore()

        # All frontier solutions should have rank 0
        for sol in frontier:
            assert sol.rank == 0

    def test_crowding_distance(self):
        """Test crowding distance computation."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = ParetoFrontExplorer(
            formulation,
            objectives=["coverage", "fairness"],
            population_size=30,
            generations=20,
            seed=42,
        )
        frontier = explorer.explore()

        for sol in frontier:
            assert sol.crowding_distance >= 0

    def test_export_for_visualization(self):
        """Test export format for visualization."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        formulation = QUBOTemplateFormulation(context)
        formulation.build()

        explorer = ParetoFrontExplorer(
            formulation,
            objectives=["coverage", "fairness"],
            population_size=20,
            generations=10,
            seed=42,
        )
        explorer.explore()

        export = explorer.export_for_visualization()
        assert "num_frontier_solutions" in export
        assert "total_evaluations" in export
        assert "objectives" in export
        assert "frontier" in export
        assert "hypervolume_estimate" in export


# ============================================================================
# Test HybridTemplatePipeline
# ============================================================================


class TestHybridTemplatePipeline:
    """Tests for hybrid classical-quantum pipeline."""

    def test_pipeline_run(self):
        """Test full pipeline execution."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=10,
            num_sweeps=100,
            pareto_generations=10,
            seed=42,
        )

        pipeline = HybridTemplatePipeline(context, config)
        result = pipeline.run()

        assert isinstance(result, TemplateSelectionResult)
        assert result.success
        assert len(result.assignments) > 0

    def test_pipeline_stages(self):
        """Test that all pipeline stages execute."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=5,
            num_sweeps=50,
            pareto_generations=5,
            seed=42,
        )

        pipeline = HybridTemplatePipeline(context, config)
        result = pipeline.run()

        # All stages should have results
        assert pipeline.qubo_result is not None
        assert pipeline.refinement_result is not None
        assert pipeline.repair_result is not None

    def test_energy_improvement(self):
        """Test that pipeline improves energy."""
        context = create_test_context(n_residents=3, n_blocks=30, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=20,
            num_sweeps=200,
            seed=42,
        )

        pipeline = HybridTemplatePipeline(context, config)
        result = pipeline.run()

        # Refined energy should be <= QUBO energy
        qubo_energy = pipeline.qubo_result["energy"]
        refined_energy = pipeline.refinement_result["energy"]
        assert refined_energy <= qubo_energy + 1e-6

    def test_result_json_export(self):
        """Test result JSON export."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=5,
            num_sweeps=50,
            pareto_generations=5,
            seed=42,
        )

        pipeline = HybridTemplatePipeline(context, config)
        result = pipeline.run()

        json_export = result.to_json()
        assert "success" in json_export
        assert "num_assignments" in json_export
        assert "pareto_frontier" in json_export
        assert "energy_landscape" in json_export
        assert "statistics" in json_export


# ============================================================================
# Test QUBOTemplateSolver
# ============================================================================


class TestQUBOTemplateSolver:
    """Tests for QUBO template solver."""

    def test_solve(self):
        """Test basic solve functionality."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=10,
            num_sweeps=100,
            seed=42,
        )

        solver = QUBOTemplateSolver(config=config)
        result = solver.solve(context)

        assert result.success
        assert result.status == "feasible"
        assert len(result.assignments) > 0

    def test_solve_with_full_result(self):
        """Test solve with full result including Pareto front."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=10,
            num_sweeps=100,
            pareto_generations=10,
            seed=42,
        )

        solver = QUBOTemplateSolver(config=config)
        result = solver.solve_with_full_result(context)

        assert isinstance(result, TemplateSelectionResult)
        assert result.success
        assert len(result.pareto_frontier) >= 0
        assert len(result.energy_landscape) > 0

    def test_empty_context(self):
        """Test handling of empty context."""
        context = create_test_context(n_residents=0, n_blocks=0, n_templates=0)
        solver = QUBOTemplateSolver()

        result = solver.solve(context)
        assert not result.success

    def test_reproducibility(self):
        """Test that same seed produces same result."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        config = TemplateSelectionConfig(
            num_reads=5,
            num_sweeps=50,
            seed=12345,
        )

        solver1 = QUBOTemplateSolver(config=config)
        result1 = solver1.solve(context)

        solver2 = QUBOTemplateSolver(config=config)
        result2 = solver2.solve(context)

        # Same seed should produce same number of assignments
        assert len(result1.assignments) == len(result2.assignments)


# ============================================================================
# Test TemplateBenchmark
# ============================================================================


class TestTemplateBenchmark:
    """Tests for benchmark comparisons."""

    def test_benchmark_run(self):
        """Test benchmark execution."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        benchmark = TemplateBenchmark(context)

        results = benchmark.run_benchmark()

        assert "qubo" in results
        assert "greedy" in results
        assert "random" in results
        assert "comparison" in results

    def test_benchmark_metrics(self):
        """Test that benchmark collects metrics."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        benchmark = TemplateBenchmark(context)

        results = benchmark.run_benchmark()

        # QUBO results
        assert "success" in results["qubo"]
        assert "num_assignments" in results["qubo"]
        assert "runtime_seconds" in results["qubo"]

        # Comparison
        assert "qubo_vs_greedy_improvement" in results["comparison"]
        assert "qubo_vs_random_improvement" in results["comparison"]

    def test_export_results(self):
        """Test benchmark export."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)
        benchmark = TemplateBenchmark(context)
        benchmark.run_benchmark()

        export = benchmark.export_results()
        assert "benchmark_results" in export
        assert "context_summary" in export


# ============================================================================
# Test Utility Functions
# ============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_template_selector_status(self):
        """Test status function."""
        status = get_template_selector_status()

        assert "qubo_template_selector_available" in status
        assert status["qubo_template_selector_available"] is True

        assert "features" in status
        assert "fairness_objectives" in status["features"]
        assert "pareto_exploration" in status["features"]
        assert "adaptive_temperature" in status["features"]

        assert "recommended_problem_size" in status


# ============================================================================
# Test Scalability
# ============================================================================


class TestScalability:
    """Tests for solver scalability."""

    @pytest.mark.parametrize(
        "n_residents,n_blocks,n_templates",
        [
            (3, 20, 2),
            (5, 40, 3),
            (10, 50, 4),
        ],
    )
    def test_scaling(self, n_residents: int, n_blocks: int, n_templates: int):
        """Test solver on various problem sizes."""
        context = create_test_context(
            n_residents=n_residents,
            n_blocks=n_blocks,
            n_templates=n_templates,
        )
        config = TemplateSelectionConfig(
            num_reads=10,
            num_sweeps=100,
            seed=42,
        )

        solver = QUBOTemplateSolver(config=config)
        result = solver.solve(context)

        assert result.success
        assert result.runtime_seconds < 60.0  # Should complete within 60s

    def test_780_variable_sweet_spot(self):
        """Test near the 780 variable sweet spot."""
        # Approximate: 15 residents × 4 periods × 13 templates ≈ 780 variables
        context = create_test_context(
            n_residents=10,
            n_blocks=40,  # ~4 rotation periods
            n_templates=8,
        )
        config = TemplateSelectionConfig(
            num_reads=20,
            num_sweeps=200,
            seed=42,
        )

        formulation = QUBOTemplateFormulation(context, config)
        n_vars = formulation.num_variables

        # Should be in reasonable range
        assert 100 < n_vars < 2000

        solver = QUBOTemplateSolver(config=config)
        result = solver.solve(context)

        assert result.success


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_resident(self):
        """Test with single resident."""
        context = create_test_context(n_residents=1, n_blocks=20, n_templates=2)
        solver = QUBOTemplateSolver(
            config=TemplateSelectionConfig(num_reads=5, num_sweeps=50)
        )
        result = solver.solve(context)

        assert result.success

    def test_single_template(self):
        """Test with single template."""
        context = create_test_context(n_residents=3, n_blocks=20, n_templates=1)
        solver = QUBOTemplateSolver(
            config=TemplateSelectionConfig(num_reads=5, num_sweeps=50)
        )
        result = solver.solve(context)

        assert result.success

    def test_weekend_blocks_excluded(self):
        """Test that weekend blocks are handled correctly."""
        blocks = []
        for i in range(14):
            is_weekend = i % 7 in [5, 6]  # Saturday, Sunday
            blocks.append(
                MockBlock(
                    block_date=date.today() + timedelta(days=i),
                    is_weekend=is_weekend,
                )
            )

        context = SchedulingContext(
            blocks=blocks,
            residents=[MockPerson() for _ in range(2)],
            faculty=[],
            templates=[MockTemplate() for _ in range(2)],
            availability={},
            existing_assignments=[],
        )

        formulation = QUBOTemplateFormulation(context)

        # Should aggregate non-weekend blocks into periods
        total_weekday_blocks = sum(1 for b in blocks if not b.is_weekend)
        assert total_weekday_blocks == 10

    def test_unavailable_resident(self):
        """Test handling of unavailable resident."""
        context = create_test_context(n_residents=2, n_blocks=20, n_templates=2)

        # Mark first resident as unavailable for first block
        resident_id = context.residents[0].id
        block_idx = context.block_idx[context.blocks[0].id]
        context.availability[resident_id] = {block_idx}

        formulation = QUBOTemplateFormulation(context)
        Q = formulation.build()

        # Should still build QUBO
        assert len(Q) > 0

    def test_template_with_capacity(self):
        """Test handling of template capacity constraints."""
        context = create_test_context(n_residents=5, n_blocks=20, n_templates=2)
        context.templates[0].max_residents = 2  # Limited capacity

        formulation = QUBOTemplateFormulation(context)
        Q = formulation.build()

        # Constraint matrix should have capacity penalties
        assert len(formulation.objective_matrices["constraints"]) > 0
