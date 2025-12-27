"""
Comprehensive tests for the multi-objective optimization framework.

Tests cover:
- Core types (Solution, ParetoFrontier, ObjectiveConfig)
- MOEA/D algorithm and decomposition methods
- Constraint handling (penalty, repair, relaxation)
- Preference articulation (a priori, a posteriori, interactive)
- Quality indicators (hypervolume, IGD, spread)
- Decision support (trade-off analysis, navigation)
- Diversity preservation (crowding, epsilon-dominance)
- Dynamic reweighting
- JSON export
"""

from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
import pytest

from app.multi_objective.core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
    SolutionArchive,
    compare_dominance,
    SCHEDULING_OBJECTIVES,
)
from app.multi_objective.moead import (
    DecompositionType,
    MOEADAlgorithm,
    MOEADConfig,
    PBIDecomposition,
    TchebycheffDecomposition,
    WeightedSumDecomposition,
    WeightVector,
    generate_weight_vectors,
)
from app.multi_objective.constraints import (
    AdaptivePenaltyMethod,
    ConstraintHandler,
    ConstraintHandlingMethod,
    ConstraintRelaxer,
    ConstraintViolation,
    DynamicPenaltyMethod,
    StaticPenaltyMethod,
)
from app.multi_objective.preferences import (
    AchievementScalarizing,
    InteractivePreferenceElicitor,
    LexicographicOrdering,
    PreferenceArticulator,
    ReferencePoint,
    WeightedSum,
)
from app.multi_objective.indicators import (
    EpsilonIndicator,
    GenerationalDistance,
    HypervolumeIndicator,
    InvertedGenerationalDistance,
    MaximumSpread,
    QualityEvaluator,
    Spacing,
    SpreadIndicator,
)
from app.multi_objective.decision_support import (
    DecisionMaker,
    NavigationDirection,
    SolutionExplorer,
    TradeOffAnalyzer,
)
from app.multi_objective.diversity import (
    CrowdingDistance,
    DiversityMechanism,
    DiversityMetric,
    EpsilonDominance,
    NichingOperator,
    ReferencePointAssociation,
)
from app.multi_objective.reweighting import (
    ContextType,
    ContextualReweighter,
    DynamicReweighter,
    FeedbackProcessor,
    FeedbackType,
    ObjectiveAdjuster,
    TemporalReweighter,
)
from app.multi_objective.export import (
    ExportFormat,
    HolographicExporter,
)


# Fixtures
@pytest.fixture
def two_objective_config():
    """Two-objective configuration for testing."""
    return [
        ObjectiveConfig(
            name="coverage",
            display_name="Coverage",
            description="Block coverage",
            direction=ObjectiveDirection.MAXIMIZE,
            objective_type=ObjectiveType.COVERAGE,
            weight=0.6,
            reference_point=1.0,
            nadir_point=0.0,
        ),
        ObjectiveConfig(
            name="equity",
            display_name="Equity",
            description="Assignment equity",
            direction=ObjectiveDirection.MINIMIZE,
            objective_type=ObjectiveType.EQUITY,
            weight=0.4,
            reference_point=0.0,
            nadir_point=1.0,
        ),
    ]


@pytest.fixture
def three_objective_config():
    """Three-objective configuration for testing."""
    return [
        ObjectiveConfig(
            name="coverage",
            display_name="Coverage",
            description="Block coverage",
            direction=ObjectiveDirection.MAXIMIZE,
            objective_type=ObjectiveType.COVERAGE,
            weight=0.5,
            reference_point=1.0,
            nadir_point=0.0,
        ),
        ObjectiveConfig(
            name="equity",
            display_name="Equity",
            description="Assignment equity",
            direction=ObjectiveDirection.MINIMIZE,
            objective_type=ObjectiveType.EQUITY,
            weight=0.3,
            reference_point=0.0,
            nadir_point=1.0,
        ),
        ObjectiveConfig(
            name="preference",
            display_name="Preference Satisfaction",
            description="Staff preferences",
            direction=ObjectiveDirection.MAXIMIZE,
            objective_type=ObjectiveType.PREFERENCE,
            weight=0.2,
            reference_point=1.0,
            nadir_point=0.0,
        ),
    ]


@pytest.fixture
def sample_solutions(two_objective_config):
    """Create sample solutions for testing."""
    return [
        Solution(
            id=uuid4(),
            objective_values={"coverage": 0.9, "equity": 0.2},
            is_feasible=True,
        ),
        Solution(
            id=uuid4(),
            objective_values={"coverage": 0.8, "equity": 0.1},
            is_feasible=True,
        ),
        Solution(
            id=uuid4(),
            objective_values={"coverage": 0.7, "equity": 0.3},
            is_feasible=True,
        ),
        Solution(
            id=uuid4(),
            objective_values={"coverage": 0.95, "equity": 0.35},
            is_feasible=True,
        ),
        Solution(
            id=uuid4(),
            objective_values={"coverage": 0.6, "equity": 0.05},
            is_feasible=True,
        ),
    ]


@pytest.fixture
def pareto_frontier(two_objective_config, sample_solutions):
    """Create a Pareto frontier from sample solutions."""
    frontier = ParetoFrontier(objectives=two_objective_config)
    for sol in sample_solutions:
        frontier.add(sol)
    return frontier


# ============================================================================
# Core Types Tests
# ============================================================================
class TestObjectiveConfig:
    """Tests for ObjectiveConfig."""

    def test_normalize_minimize(self):
        """Test normalization for minimization objective."""
        obj = ObjectiveConfig(
            name="test",
            display_name="Test",
            description="Test",
            direction=ObjectiveDirection.MINIMIZE,
            objective_type=ObjectiveType.CUSTOM,
            reference_point=0.0,
            nadir_point=1.0,
        )

        assert obj.normalize(0.0) == 0.0  # Ideal
        assert obj.normalize(1.0) == 1.0  # Worst
        assert obj.normalize(0.5) == 0.5  # Middle

    def test_normalize_maximize(self):
        """Test normalization for maximization objective."""
        obj = ObjectiveConfig(
            name="test",
            display_name="Test",
            description="Test",
            direction=ObjectiveDirection.MAXIMIZE,
            objective_type=ObjectiveType.CUSTOM,
            reference_point=1.0,
            nadir_point=0.0,
        )

        assert obj.normalize(1.0) == 0.0  # Ideal (best)
        assert obj.normalize(0.0) == 1.0  # Worst
        assert obj.normalize(0.5) == 0.5  # Middle


class TestDominance:
    """Tests for dominance comparison."""

    def test_dominates(self, two_objective_config):
        """Test that better solution dominates."""
        # Coverage: maximize, Equity: minimize
        better = Solution(objective_values={"coverage": 0.9, "equity": 0.1})
        worse = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        result = compare_dominance(better, worse, two_objective_config)
        assert result == DominanceRelation.DOMINATES

    def test_dominated(self, two_objective_config):
        """Test that worse solution is dominated."""
        worse = Solution(objective_values={"coverage": 0.7, "equity": 0.3})
        better = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        result = compare_dominance(worse, better, two_objective_config)
        assert result == DominanceRelation.DOMINATED

    def test_incomparable(self, two_objective_config):
        """Test incomparable (trade-off) solutions."""
        sol_a = Solution(objective_values={"coverage": 0.9, "equity": 0.3})
        sol_b = Solution(objective_values={"coverage": 0.7, "equity": 0.1})

        result = compare_dominance(sol_a, sol_b, two_objective_config)
        assert result == DominanceRelation.INCOMPARABLE

    def test_equal(self, two_objective_config):
        """Test equal solutions."""
        sol_a = Solution(objective_values={"coverage": 0.8, "equity": 0.2})
        sol_b = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        result = compare_dominance(sol_a, sol_b, two_objective_config)
        assert result == DominanceRelation.EQUAL

    def test_feasibility_dominance(self, two_objective_config):
        """Test that feasible dominates infeasible."""
        feasible = Solution(
            objective_values={"coverage": 0.5, "equity": 0.5}, is_feasible=True
        )
        infeasible = Solution(
            objective_values={"coverage": 0.9, "equity": 0.1}, is_feasible=False
        )

        result = compare_dominance(feasible, infeasible, two_objective_config)
        assert result == DominanceRelation.DOMINATES


class TestParetoFrontier:
    """Tests for ParetoFrontier."""

    def test_add_non_dominated(self, two_objective_config):
        """Test adding non-dominated solutions."""
        frontier = ParetoFrontier(objectives=two_objective_config)

        sol1 = Solution(objective_values={"coverage": 0.9, "equity": 0.3})
        sol2 = Solution(objective_values={"coverage": 0.7, "equity": 0.1})

        assert frontier.add(sol1)
        assert frontier.add(sol2)
        assert len(frontier) == 2

    def test_reject_dominated(self, two_objective_config):
        """Test that dominated solutions are rejected."""
        frontier = ParetoFrontier(objectives=two_objective_config)

        better = Solution(objective_values={"coverage": 0.9, "equity": 0.1})
        worse = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        frontier.add(better)
        assert not frontier.add(worse)  # Should be rejected
        assert len(frontier) == 1

    def test_remove_dominated_on_add(self, two_objective_config):
        """Test that dominated solutions are removed when better arrives."""
        frontier = ParetoFrontier(objectives=two_objective_config)

        worse = Solution(objective_values={"coverage": 0.8, "equity": 0.2})
        better = Solution(objective_values={"coverage": 0.9, "equity": 0.1})

        frontier.add(worse)
        frontier.add(better)

        assert len(frontier) == 1
        assert frontier.solutions[0].id == better.id

    def test_get_extreme_solutions(self, pareto_frontier):
        """Test getting extreme solutions."""
        extremes = pareto_frontier.get_extreme_solutions()
        assert len(extremes) >= 2  # At least one for each objective

    def test_get_knee_solution(self, pareto_frontier):
        """Test getting knee solution."""
        knee = pareto_frontier.get_knee_solution()
        assert knee is not None
        assert knee in pareto_frontier.solutions


class TestSolutionArchive:
    """Tests for SolutionArchive."""

    def test_max_size_pruning(self, two_objective_config):
        """Test archive prunes when exceeding max size."""
        archive = SolutionArchive(max_size=3, objectives=two_objective_config)

        for i in range(5):
            sol = Solution(
                objective_values={"coverage": 0.5 + i * 0.1, "equity": 0.5 - i * 0.1}
            )
            archive.add(sol)

        assert len(archive) <= 3

    def test_rejects_dominated(self, two_objective_config):
        """Test archive rejects dominated solutions."""
        archive = SolutionArchive(max_size=10, objectives=two_objective_config)

        better = Solution(objective_values={"coverage": 0.9, "equity": 0.1})
        worse = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        archive.add(better)
        assert not archive.add(worse)


# ============================================================================
# MOEA/D Tests
# ============================================================================
class TestWeightVectors:
    """Tests for weight vector generation."""

    def test_generate_uniform_2d(self):
        """Test generating 2D weight vectors."""
        weights = generate_weight_vectors(2, 10, method="uniform")
        assert len(weights) >= 10
        for w in weights:
            assert abs(sum(w) - 1.0) < 1e-10  # Sum to 1

    def test_generate_uniform_3d(self):
        """Test generating 3D weight vectors."""
        weights = generate_weight_vectors(3, 20, method="uniform")
        assert len(weights) >= 10
        for w in weights:
            assert abs(sum(w) - 1.0) < 1e-10

    def test_generate_random(self):
        """Test random weight generation."""
        weights = generate_weight_vectors(3, 50, method="random")
        assert len(weights) == 50
        for w in weights:
            assert abs(sum(w) - 1.0) < 1e-10


class TestDecomposition:
    """Tests for decomposition methods."""

    def test_weighted_sum(self):
        """Test weighted sum decomposition."""
        decomp = WeightedSumDecomposition()
        weight = np.array([0.5, 0.5])
        obj_values = np.array([0.3, 0.7])
        ref_point = np.array([0.0, 0.0])

        result = decomp.scalarize(obj_values, weight, ref_point)
        assert result == pytest.approx(0.5)

    def test_tchebycheff(self):
        """Test Tchebycheff decomposition."""
        decomp = TchebycheffDecomposition()
        weight = np.array([0.5, 0.5])
        obj_values = np.array([0.3, 0.7])
        ref_point = np.array([0.0, 0.0])

        result = decomp.scalarize(obj_values, weight, ref_point)
        assert result == pytest.approx(0.35)

    def test_pbi(self):
        """Test PBI decomposition."""
        decomp = PBIDecomposition(theta=5.0)
        weight = np.array([0.5, 0.5])
        obj_values = np.array([0.3, 0.3])
        ref_point = np.array([0.0, 0.0])

        result = decomp.scalarize(obj_values, weight, ref_point)
        assert result > 0


class TestMOEAD:
    """Tests for MOEA/D algorithm."""

    def test_initialization(self, two_objective_config):
        """Test MOEA/D initialization."""
        moead = MOEADAlgorithm(two_objective_config)

        assert len(moead.weight_vectors) > 0
        assert moead.n_objectives == 2

    def test_neighborhoods(self, two_objective_config):
        """Test neighborhood computation."""
        config = MOEADConfig(n_weight_vectors=20, n_neighbors=5)
        moead = MOEADAlgorithm(two_objective_config, config)

        for wv in moead.weight_vectors:
            assert len(wv.neighbors) == 5


# ============================================================================
# Constraint Handling Tests
# ============================================================================
class TestPenaltyMethods:
    """Tests for penalty methods."""

    def test_static_penalty(self):
        """Test static penalty calculation."""
        penalty = StaticPenaltyMethod(hard_coefficient=1000.0, soft_coefficient=10.0)

        violations = [
            ConstraintViolation("test", "capacity", 0.5, is_hard=True),
            ConstraintViolation("test2", "preference", 0.3, is_hard=False),
        ]

        result = penalty.calculate_penalty(violations, 0, 100)
        expected = 1000.0 * 0.25 + 10.0 * 0.09  # magnitude^2
        assert result == pytest.approx(expected, rel=0.01)

    def test_dynamic_penalty_grows(self):
        """Test that dynamic penalty grows with generation."""
        penalty = DynamicPenaltyMethod()
        violations = [ConstraintViolation("test", "capacity", 0.5, is_hard=True)]

        early = penalty.calculate_penalty(violations, 10, 100)
        late = penalty.calculate_penalty(violations, 90, 100)

        assert late > early

    def test_adaptive_penalty_updates(self):
        """Test adaptive penalty coefficient updates."""
        penalty = AdaptivePenaltyMethod(initial_coefficient=100.0, target_feasibility=0.5)

        initial = penalty.coefficient
        penalty.update_feasibility(0.2)  # Too few feasible
        assert penalty.coefficient < initial  # Should decrease

        penalty.update_feasibility(0.8)  # Too many feasible
        # Should increase


class TestConstraintRelaxer:
    """Tests for constraint relaxation."""

    def test_register_constraint(self):
        """Test constraint registration."""
        relaxer = ConstraintRelaxer()
        relaxer.register_constraint("capacity", 1.0, 0.1, 0.5)

        thresholds = relaxer.get_current_thresholds()
        assert "capacity" in thresholds
        assert thresholds["capacity"] == 1.0

    def test_relaxation_on_infeasibility(self):
        """Test constraints relax after infeasibility streak."""
        relaxer = ConstraintRelaxer()
        relaxer.register_constraint("capacity", 1.0, 0.1, 0.5)

        # Simulate infeasibility streak
        for _ in range(5):
            relaxer.update(is_feasible=False, feasibility_ratio=0.0)

        thresholds = relaxer.get_current_thresholds()
        assert thresholds["capacity"] > 1.0  # Should have relaxed

    def test_restoration_on_feasibility(self):
        """Test constraints restore after feasibility."""
        relaxer = ConstraintRelaxer()
        relaxer.register_constraint("capacity", 1.0, 0.1, 0.5)

        # First relax
        for _ in range(5):
            relaxer.update(is_feasible=False, feasibility_ratio=0.0)

        relaxed = relaxer.get_current_thresholds()["capacity"]

        # Then restore
        for _ in range(10):
            relaxer.update(is_feasible=True, feasibility_ratio=0.5)

        restored = relaxer.get_current_thresholds()["capacity"]
        assert restored < relaxed  # Should have moved toward original


# ============================================================================
# Preference Articulation Tests
# ============================================================================
class TestWeightedSumPreference:
    """Tests for weighted sum preference."""

    def test_score_calculation(self, two_objective_config):
        """Test weighted sum score."""
        pref = WeightedSum({"coverage": 0.7, "equity": 0.3})
        sol = Solution(objective_values={"coverage": 0.8, "equity": 0.2})

        score = pref.score(sol, two_objective_config)
        # Coverage is maximize (negated), equity is minimize
        expected = 0.7 * (-0.8) + 0.3 * 0.2
        assert score == pytest.approx(expected, rel=0.01)

    def test_ranking(self, two_objective_config, sample_solutions):
        """Test solution ranking."""
        pref = WeightedSum({"coverage": 1.0, "equity": 0.0})
        ranked = pref.rank_solutions(sample_solutions, two_objective_config)

        # Should be sorted by coverage (highest first, but scores are negated)
        for i in range(len(ranked) - 1):
            assert ranked[i][1] <= ranked[i + 1][1]


class TestAchievementScalarizing:
    """Tests for achievement scalarizing function."""

    def test_asf_score(self, two_objective_config):
        """Test ASF score calculation."""
        ref = ReferencePoint(
            values={"coverage": 0.9, "equity": 0.1},
            objective_names=["coverage", "equity"],
        )
        asf = AchievementScalarizing(ref)

        sol = Solution(objective_values={"coverage": 0.8, "equity": 0.2})
        score = asf.score(sol, two_objective_config)

        # Solution is worse in both, so score should be positive
        assert score > 0


class TestInteractiveElicitor:
    """Tests for interactive preference elicitation."""

    def test_start_elicitation(self, two_objective_config, pareto_frontier):
        """Test starting interactive elicitation."""
        elicitor = InteractivePreferenceElicitor(two_objective_config)
        representatives = elicitor.start_elicitation(pareto_frontier)

        assert len(representatives) > 0
        assert len(representatives) <= 5

    def test_process_rating_feedback(self, two_objective_config, pareto_frontier):
        """Test processing rating feedback."""
        elicitor = InteractivePreferenceElicitor(two_objective_config)
        reps = elicitor.start_elicitation(pareto_frontier)

        feedback = {
            "ratings": {str(reps[0].id): 5, str(reps[1].id): 2},
        }
        new_reps = elicitor.process_feedback("rating", feedback, pareto_frontier)

        assert len(new_reps) > 0


# ============================================================================
# Quality Indicator Tests
# ============================================================================
class TestHypervolume:
    """Tests for hypervolume indicator."""

    def test_2d_hypervolume(self, two_objective_config):
        """Test 2D hypervolume calculation."""
        frontier = ParetoFrontier(objectives=two_objective_config)

        # Add two non-dominated solutions
        frontier.add(Solution(objective_values={"coverage": 0.8, "equity": 0.2}))
        frontier.add(Solution(objective_values={"coverage": 0.6, "equity": 0.1}))

        hv = HypervolumeIndicator()
        result = hv.calculate(frontier)

        assert result > 0

    def test_empty_frontier_hypervolume(self, two_objective_config):
        """Test hypervolume of empty frontier."""
        frontier = ParetoFrontier(objectives=two_objective_config)
        hv = HypervolumeIndicator()

        assert hv.calculate(frontier) == 0.0


class TestQualityEvaluator:
    """Tests for quality evaluator."""

    def test_evaluate_frontier(self, pareto_frontier):
        """Test comprehensive quality evaluation."""
        evaluator = QualityEvaluator()
        report = evaluator.evaluate(pareto_frontier)

        assert report.front_size == len(pareto_frontier)
        assert report.hypervolume is not None or report.hypervolume == 0
        assert report.objective_names


# ============================================================================
# Decision Support Tests
# ============================================================================
class TestTradeOffAnalyzer:
    """Tests for trade-off analysis."""

    def test_analyze_trade_off(self, two_objective_config):
        """Test trade-off analysis between solutions."""
        analyzer = TradeOffAnalyzer(two_objective_config)

        sol_from = Solution(objective_values={"coverage": 0.7, "equity": 0.1})
        sol_to = Solution(objective_values={"coverage": 0.9, "equity": 0.3})

        trade_offs = analyzer.analyze_trade_off(sol_from, sol_to)

        assert len(trade_offs) > 0
        # Coverage improves, equity degrades
        improved = [t.objective_improved for t in trade_offs]
        degraded = [t.objective_degraded for t in trade_offs]
        assert "coverage" in improved
        assert "equity" in degraded


class TestSolutionExplorer:
    """Tests for solution exploration."""

    def test_start_at_knee(self, two_objective_config, pareto_frontier):
        """Test starting exploration at knee."""
        explorer = SolutionExplorer(pareto_frontier, two_objective_config)
        knee = explorer.start_at_knee()

        assert knee is not None
        assert explorer.current_solution == knee

    def test_navigate_toward_objective(self, two_objective_config, pareto_frontier):
        """Test navigation toward an objective."""
        explorer = SolutionExplorer(pareto_frontier, two_objective_config)
        explorer.start_at_knee()

        steps = explorer.navigate(NavigationDirection.TOWARD_OBJECTIVE, "coverage")

        if steps:  # May be empty if already at extreme
            assert steps[0].to_solution != explorer.exploration_history[0]

    def test_bookmark_solutions(self, two_objective_config, pareto_frontier):
        """Test bookmarking."""
        explorer = SolutionExplorer(pareto_frontier, two_objective_config)
        explorer.start_at_knee()

        explorer.bookmark()
        assert len(explorer.bookmarks) == 1


class TestDecisionMaker:
    """Tests for decision maker interface."""

    def test_get_overview(self, two_objective_config, pareto_frontier):
        """Test getting decision space overview."""
        dm = DecisionMaker(pareto_frontier, two_objective_config)
        overview = dm.get_overview()

        assert "frontier_size" in overview
        assert "objectives" in overview
        assert "knee_solution" in overview

    def test_record_preference(self, two_objective_config, pareto_frontier):
        """Test recording preferences."""
        dm = DecisionMaker(pareto_frontier, two_objective_config)

        sol_a = pareto_frontier.solutions[0]
        sol_b = pareto_frontier.solutions[1]

        dm.record_preference(sol_a, sol_b, preferred=0)

        summary = dm.get_decision_summary()
        assert summary["comparisons_made"] == 1


# ============================================================================
# Diversity Tests
# ============================================================================
class TestCrowdingDistance:
    """Tests for crowding distance."""

    def test_calculate_crowding(self, two_objective_config, sample_solutions):
        """Test crowding distance calculation."""
        crowding = CrowdingDistance(two_objective_config)
        crowding.calculate(sample_solutions)

        # Boundary solutions should have infinite distance
        distances = [s.crowding_distance for s in sample_solutions]
        assert any(d == float("inf") for d in distances)

    def test_select_by_crowding(self, two_objective_config, sample_solutions):
        """Test selection by crowding distance."""
        crowding = CrowdingDistance(two_objective_config)
        selected = crowding.select_by_crowding(sample_solutions, 3)

        assert len(selected) == 3


class TestEpsilonDominance:
    """Tests for epsilon-dominance."""

    def test_grid_location(self, two_objective_config):
        """Test grid location calculation."""
        eps_dom = EpsilonDominance(two_objective_config, epsilon=0.1)

        sol = Solution(objective_values={"coverage": 0.55, "equity": 0.23})
        location = eps_dom.get_grid_location(sol)

        assert len(location) == 2

    def test_update_archive(self, two_objective_config):
        """Test archive update with epsilon-dominance."""
        eps_dom = EpsilonDominance(two_objective_config, epsilon=0.1)
        archive: list[Solution] = []

        sol1 = Solution(objective_values={"coverage": 0.8, "equity": 0.2})
        sol2 = Solution(objective_values={"coverage": 0.81, "equity": 0.21})  # Same cell

        archive = eps_dom.update_archive(archive, sol1)
        archive = eps_dom.update_archive(archive, sol2)

        # Should only keep one (same cell)
        assert len(archive) == 1


class TestDiversityMechanism:
    """Tests for combined diversity mechanism."""

    def test_get_diversity_stats(self, two_objective_config, sample_solutions):
        """Test diversity statistics."""
        mechanism = DiversityMechanism(
            two_objective_config, primary_metric=DiversityMetric.CROWDING_DISTANCE
        )

        stats = mechanism.get_diversity_stats(sample_solutions)

        assert stats.metric_type == DiversityMetric.CROWDING_DISTANCE
        assert stats.mean_distance >= 0


# ============================================================================
# Reweighting Tests
# ============================================================================
class TestFeedbackProcessor:
    """Tests for feedback processing."""

    def test_process_rating(self, two_objective_config):
        """Test processing rating feedback."""
        processor = FeedbackProcessor(two_objective_config)

        from app.multi_objective.reweighting import FeedbackEvent

        event = FeedbackEvent(
            feedback_type=FeedbackType.RATING,
            timestamp=datetime.now(),
            data={"rating": 5, "objectives": {"coverage": 0.9, "equity": 0.1}},
        )

        deltas = processor.process_feedback(event)
        assert isinstance(deltas, dict)


class TestObjectiveAdjuster:
    """Tests for objective weight adjustment."""

    def test_apply_deltas(self, two_objective_config):
        """Test applying weight deltas."""
        adjuster = ObjectiveAdjuster(two_objective_config)
        initial = adjuster.get_weights()

        deltas = {"coverage": 0.1}
        new_weights = adjuster.apply_deltas(deltas)

        assert sum(new_weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_weight_bounds(self, two_objective_config):
        """Test weight bounds enforcement."""
        adjuster = ObjectiveAdjuster(two_objective_config, min_weight=0.1, max_weight=0.9)

        # Try to set extreme weight
        deltas = {"coverage": 10.0}
        new_weights = adjuster.apply_deltas(deltas)

        assert all(0.1 <= w <= 0.9 for w in new_weights.values())


class TestContextualReweighter:
    """Tests for contextual reweighting."""

    def test_switch_context(self, two_objective_config):
        """Test context switching."""
        reweighter = ContextualReweighter(two_objective_config)

        multipliers = reweighter.switch_context(ContextType.EMERGENCY)
        assert reweighter.current_context == ContextType.EMERGENCY

    def test_apply_context(self, two_objective_config):
        """Test applying context to weights."""
        reweighter = ContextualReweighter(two_objective_config)
        base_weights = {"coverage": 0.5, "equity": 0.5}

        adjusted = reweighter.apply_context(base_weights, ContextType.EMERGENCY)

        assert sum(adjusted.values()) == pytest.approx(1.0, rel=0.01)


class TestDynamicReweighter:
    """Tests for complete dynamic reweighting."""

    def test_process_feedback(self, two_objective_config):
        """Test processing feedback through dynamic reweighter."""
        reweighter = DynamicReweighter(two_objective_config)

        weights = reweighter.process_feedback(
            FeedbackType.PRIORITY,
            {"priority_order": ["coverage", "equity"]},
        )

        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_boost_objective(self, two_objective_config):
        """Test boosting an objective."""
        reweighter = DynamicReweighter(two_objective_config)
        initial = reweighter.get_weights()

        new_weights = reweighter.boost_objective("coverage", factor=1.5)

        # Coverage should have increased relative to others
        assert new_weights["coverage"] > initial["coverage"]


# ============================================================================
# Export Tests
# ============================================================================
class TestHolographicExporter:
    """Tests for holographic export."""

    def test_export_landscape(self, two_objective_config, pareto_frontier):
        """Test landscape export."""
        exporter = HolographicExporter(two_objective_config)
        json_str = exporter.export_landscape(pareto_frontier, ExportFormat.COMPACT)

        import json

        data = json.loads(json_str)

        assert "solutions" in data
        assert "objectives" in data
        assert "n_solutions" in data

    def test_export_visualization(self, two_objective_config, pareto_frontier):
        """Test 3D visualization export."""
        exporter = HolographicExporter(two_objective_config)
        json_str = exporter.export_visualization(pareto_frontier)

        import json

        data = json.loads(json_str)

        assert "points" in data
        assert "colors" in data
        assert "x_axis" in data

    def test_export_solution(self, two_objective_config, sample_solutions):
        """Test single solution export."""
        exporter = HolographicExporter(two_objective_config)
        json_str = exporter.export_solution(sample_solutions[0])

        import json

        data = json.loads(json_str)

        assert "id" in data
        assert "objectives" in data


# ============================================================================
# Integration Tests
# ============================================================================
class TestMultiObjectiveIntegration:
    """Integration tests for the complete framework."""

    def test_full_optimization_workflow(self, three_objective_config):
        """Test complete optimization workflow."""
        # Create MOEA/D
        config = MOEADConfig(n_weight_vectors=20, max_generations=5)
        moead = MOEADAlgorithm(three_objective_config, config)

        # Create initial solutions
        initial = []
        for _ in range(10):
            sol = Solution(
                objective_values={
                    "coverage": np.random.random(),
                    "equity": np.random.random(),
                    "preference": np.random.random(),
                }
            )
            initial.append(sol)

        # Simple evaluation/mutation functions
        def evaluate(sol):
            return sol

        def mutate(sol):
            new_sol = sol.copy()
            for key in new_sol.objective_values:
                new_sol.objective_values[key] += np.random.normal(0, 0.05)
                new_sol.objective_values[key] = max(
                    0, min(1, new_sol.objective_values[key])
                )
            return new_sol

        def crossover(sol1, sol2):
            new_sol = sol1.copy()
            for key in new_sol.objective_values:
                if np.random.random() < 0.5:
                    new_sol.objective_values[key] = sol2.objective_values[key]
            return new_sol

        # Run optimization
        archive = moead.optimize(initial, evaluate, mutate, crossover)

        assert len(archive) > 0

    def test_decision_support_workflow(self, two_objective_config, pareto_frontier):
        """Test complete decision support workflow."""
        # Create decision maker
        dm = DecisionMaker(pareto_frontier, two_objective_config)

        # Get overview
        overview = dm.get_overview()
        assert overview["frontier_size"] > 0

        # Start at recommended point
        start = dm.recommend_starting_point()
        assert start is not None

        # Compare solutions
        if len(pareto_frontier.solutions) >= 2:
            sol_a = pareto_frontier.solutions[0]
            sol_b = pareto_frontier.solutions[1]

            comparison = dm.compare_solutions(sol_a, sol_b)
            assert comparison.dominance in DominanceRelation

            # Record preference
            dm.record_preference(sol_a, sol_b, preferred=0)

        # Get recommendation
        recommended, explanation = dm.get_recommendation()
        assert explanation
