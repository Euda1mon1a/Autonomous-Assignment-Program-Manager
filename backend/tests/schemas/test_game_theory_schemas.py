"""Tests for game theory schemas (Field bounds, patterns, enums, defaults)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.game_theory import (
    StrategyType,
    SimulationStatus,
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    TournamentCreate,
    TournamentResponse,
    TournamentListResponse,
    TournamentRanking,
    TournamentResultsResponse,
    MatchResponse,
    EvolutionCreate,
    EvolutionResponse,
    EvolutionListResponse,
    PopulationSnapshot,
    EvolutionResultsResponse,
    ValidationRequest,
    ValidationResponse,
    ConfigAnalysisRequest,
    ConfigAnalysisResponse,
    OptimalConfigRequest,
    OptimalConfigResponse,
    ShapleyValueRequest,
    ShapleyValueResult,
    FacultyShapleyMetrics,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestStrategyType:
    def test_count(self):
        assert len(StrategyType) == 9

    def test_sample(self):
        assert StrategyType.COOPERATIVE == "cooperative"
        assert StrategyType.TIT_FOR_TAT == "tit_for_tat"
        assert StrategyType.CUSTOM == "custom"


class TestSimulationStatus:
    def test_values(self):
        assert SimulationStatus.PENDING == "pending"
        assert SimulationStatus.RUNNING == "running"
        assert SimulationStatus.COMPLETED == "completed"
        assert SimulationStatus.FAILED == "failed"
        assert SimulationStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(SimulationStatus) == 5


# ── StrategyCreate ─────────────────────────────────────────────────────


class TestStrategyCreate:
    def test_defaults(self):
        r = StrategyCreate(name="TFT", strategy_type=StrategyType.TIT_FOR_TAT)
        assert r.description is None
        assert r.utilization_target == 0.80
        assert r.cross_zone_borrowing is True
        assert r.sacrifice_willingness == "medium"
        assert r.defense_activation_threshold == 3
        assert r.response_timeout_ms == 5000
        assert r.initial_action == "cooperate"
        assert r.forgiveness_probability == 0.0
        assert r.retaliation_memory == 1
        assert r.is_stochastic is False
        assert r.custom_logic is None

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            StrategyCreate(name="", strategy_type=StrategyType.COOPERATIVE)

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            StrategyCreate(name="x" * 101, strategy_type=StrategyType.COOPERATIVE)

    # --- description min_length=1, max_length=1000 ---

    def test_description_empty(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="Test",
                strategy_type=StrategyType.COOPERATIVE,
                description="",
            )

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="Test",
                strategy_type=StrategyType.COOPERATIVE,
                description="x" * 1001,
            )

    # --- utilization_target ge=0.0, le=1.0 ---

    def test_utilization_below_min(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                utilization_target=-0.1,
            )

    def test_utilization_above_max(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                utilization_target=1.1,
            )

    # --- sacrifice_willingness pattern ^(low|medium|high)$ ---

    def test_sacrifice_valid(self):
        for val in ("low", "medium", "high"):
            r = StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                sacrifice_willingness=val,
            )
            assert r.sacrifice_willingness == val

    def test_sacrifice_invalid(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                sacrifice_willingness="extreme",
            )

    # --- defense_activation_threshold ge=1, le=5 ---

    def test_defense_threshold_below_min(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                defense_activation_threshold=0,
            )

    def test_defense_threshold_above_max(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                defense_activation_threshold=6,
            )

    # --- response_timeout_ms ge=100, le=60000 ---

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                response_timeout_ms=99,
            )

    def test_timeout_above_max(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                response_timeout_ms=60001,
            )

    # --- initial_action pattern ^(cooperate|defect)$ ---

    def test_initial_action_valid(self):
        for val in ("cooperate", "defect"):
            r = StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                initial_action=val,
            )
            assert r.initial_action == val

    def test_initial_action_invalid(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                initial_action="negotiate",
            )

    # --- forgiveness_probability ge=0.0, le=1.0 ---

    def test_forgiveness_above_max(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                forgiveness_probability=1.1,
            )

    # --- retaliation_memory ge=1, le=100 ---

    def test_retaliation_below_min(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                retaliation_memory=0,
            )

    def test_retaliation_above_max(self):
        with pytest.raises(ValidationError):
            StrategyCreate(
                name="T",
                strategy_type=StrategyType.COOPERATIVE,
                retaliation_memory=101,
            )


# ── TournamentCreate ──────────────────────────────────────────────────


class TestTournamentCreate:
    def test_defaults(self):
        r = TournamentCreate(
            name="Round Robin",
            strategy_ids=[uuid4(), uuid4()],
        )
        assert r.description is None
        assert r.turns_per_match == 200
        assert r.repetitions == 10
        assert r.noise == 0.0
        assert r.payoff_cc == 3.0
        assert r.payoff_cd == 0.0
        assert r.payoff_dc == 5.0
        assert r.payoff_dd == 1.0

    # --- name min_length=1, max_length=200 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            TournamentCreate(name="", strategy_ids=[uuid4(), uuid4()])

    # --- strategy_ids min_length=2 ---

    def test_strategy_ids_too_few(self):
        with pytest.raises(ValidationError):
            TournamentCreate(name="T", strategy_ids=[uuid4()])

    # --- turns_per_match ge=10, le=1000 ---

    def test_turns_below_min(self):
        with pytest.raises(ValidationError):
            TournamentCreate(
                name="T",
                strategy_ids=[uuid4(), uuid4()],
                turns_per_match=9,
            )

    def test_turns_above_max(self):
        with pytest.raises(ValidationError):
            TournamentCreate(
                name="T",
                strategy_ids=[uuid4(), uuid4()],
                turns_per_match=1001,
            )

    # --- repetitions ge=1, le=100 ---

    def test_repetitions_below_min(self):
        with pytest.raises(ValidationError):
            TournamentCreate(
                name="T",
                strategy_ids=[uuid4(), uuid4()],
                repetitions=0,
            )

    # --- noise ge=0.0, le=0.5 ---

    def test_noise_above_max(self):
        with pytest.raises(ValidationError):
            TournamentCreate(
                name="T",
                strategy_ids=[uuid4(), uuid4()],
                noise=0.6,
            )


# ── EvolutionCreate ───────────────────────────────────────────────────


class TestEvolutionCreate:
    def test_defaults(self):
        r = EvolutionCreate(
            name="Evo Sim",
            initial_composition={"s1": 50, "s2": 50},
        )
        assert r.description is None
        assert r.turns_per_interaction == 100
        assert r.max_generations == 1000
        assert r.mutation_rate == 0.01

    # --- name min_length=1, max_length=200 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            EvolutionCreate(name="", initial_composition={"s1": 50, "s2": 50})

    # --- initial_composition min_length=2 ---

    def test_composition_too_few(self):
        with pytest.raises(ValidationError):
            EvolutionCreate(name="T", initial_composition={"s1": 50})

    # --- turns_per_interaction ge=10, le=500 ---

    def test_turns_below_min(self):
        with pytest.raises(ValidationError):
            EvolutionCreate(
                name="T",
                initial_composition={"s1": 50, "s2": 50},
                turns_per_interaction=9,
            )

    # --- max_generations ge=10, le=10000 ---

    def test_generations_above_max(self):
        with pytest.raises(ValidationError):
            EvolutionCreate(
                name="T",
                initial_composition={"s1": 50, "s2": 50},
                max_generations=10001,
            )

    # --- mutation_rate ge=0.0, le=0.5 ---

    def test_mutation_rate_above_max(self):
        with pytest.raises(ValidationError):
            EvolutionCreate(
                name="T",
                initial_composition={"s1": 50, "s2": 50},
                mutation_rate=0.6,
            )


# ── ValidationRequest ──────────────────────────────────────────────────


class TestValidationRequest:
    def test_defaults(self):
        r = ValidationRequest(strategy_id=uuid4())
        assert r.turns == 100
        assert r.repetitions == 10
        assert r.pass_threshold == 2.5

    # --- turns ge=10, le=500 ---

    def test_turns_below_min(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), turns=9)

    def test_turns_above_max(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), turns=501)

    # --- repetitions ge=1, le=50 ---

    def test_repetitions_below_min(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), repetitions=0)

    def test_repetitions_above_max(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), repetitions=51)

    # --- pass_threshold ge=0.0, le=5.0 ---

    def test_threshold_below_min(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), pass_threshold=-0.1)

    def test_threshold_above_max(self):
        with pytest.raises(ValidationError):
            ValidationRequest(strategy_id=uuid4(), pass_threshold=5.1)


# ── ConfigAnalysisRequest ──────────────────────────────────────────────


class TestConfigAnalysisRequest:
    def test_defaults(self):
        r = ConfigAnalysisRequest()
        assert r.utilization_target == 0.80
        assert r.cross_zone_borrowing is True
        assert r.sacrifice_willingness == "medium"
        assert r.defense_activation_threshold == 3

    def test_sacrifice_invalid(self):
        with pytest.raises(ValidationError):
            ConfigAnalysisRequest(sacrifice_willingness="extreme")

    def test_defense_threshold_bounds(self):
        with pytest.raises(ValidationError):
            ConfigAnalysisRequest(defense_activation_threshold=0)
        with pytest.raises(ValidationError):
            ConfigAnalysisRequest(defense_activation_threshold=6)

    def test_utilization_bounds(self):
        with pytest.raises(ValidationError):
            ConfigAnalysisRequest(utilization_target=-0.1)
        with pytest.raises(ValidationError):
            ConfigAnalysisRequest(utilization_target=1.1)


# ── OptimalConfigRequest ──────────────────────────────────────────────


class TestOptimalConfigRequest:
    def test_defaults(self):
        c = ConfigAnalysisRequest()
        r = OptimalConfigRequest(candidates=[c])
        assert r.generations == 100

    # --- generations ge=10, le=1000 ---

    def test_generations_below_min(self):
        with pytest.raises(ValidationError):
            OptimalConfigRequest(candidates=[ConfigAnalysisRequest()], generations=9)

    def test_generations_above_max(self):
        with pytest.raises(ValidationError):
            OptimalConfigRequest(candidates=[ConfigAnalysisRequest()], generations=1001)


# ── ShapleyValueRequest ────────────────────────────────────────────────


class TestShapleyValueRequest:
    def test_defaults(self):
        r = ShapleyValueRequest(
            faculty_ids=[uuid4(), uuid4()],
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 3, 31),
        )
        assert r.num_samples == 1000

    # --- faculty_ids min_length=2 ---

    def test_too_few_faculty(self):
        with pytest.raises(ValidationError):
            ShapleyValueRequest(
                faculty_ids=[uuid4()],
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 3, 31),
            )

    # --- num_samples ge=100, le=10000 ---

    def test_samples_below_min(self):
        with pytest.raises(ValidationError):
            ShapleyValueRequest(
                faculty_ids=[uuid4(), uuid4()],
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 3, 31),
                num_samples=99,
            )

    def test_samples_above_max(self):
        with pytest.raises(ValidationError):
            ShapleyValueRequest(
                faculty_ids=[uuid4(), uuid4()],
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 3, 31),
                num_samples=10001,
            )


# ── ShapleyValueResult ─────────────────────────────────────────────────


class TestShapleyValueResult:
    def test_valid(self):
        r = ShapleyValueResult(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            shapley_value=0.25,
            marginal_contribution=10.0,
            fair_workload_target=40.0,
            current_workload=45.0,
            equity_gap=5.0,
        )
        assert r.shapley_value == 0.25

    # --- shapley_value ge=0.0, le=1.0 ---

    def test_shapley_below_min(self):
        with pytest.raises(ValidationError):
            ShapleyValueResult(
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                shapley_value=-0.1,
                marginal_contribution=10.0,
                fair_workload_target=40.0,
                current_workload=45.0,
                equity_gap=5.0,
            )

    def test_shapley_above_max(self):
        with pytest.raises(ValidationError):
            ShapleyValueResult(
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                shapley_value=1.1,
                marginal_contribution=10.0,
                fair_workload_target=40.0,
                current_workload=45.0,
                equity_gap=5.0,
            )

    # --- marginal_contribution ge=0.0 ---

    def test_marginal_below_min(self):
        with pytest.raises(ValidationError):
            ShapleyValueResult(
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                shapley_value=0.25,
                marginal_contribution=-1.0,
                fair_workload_target=40.0,
                current_workload=45.0,
                equity_gap=5.0,
            )


# ── FacultyShapleyMetrics ──────────────────────────────────────────────


class TestFacultyShapleyMetrics:
    def test_valid(self):
        result = ShapleyValueResult(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            shapley_value=0.5,
            marginal_contribution=20.0,
            fair_workload_target=40.0,
            current_workload=42.0,
            equity_gap=2.0,
        )
        r = FacultyShapleyMetrics(
            faculty_results=[result],
            total_workload=42.0,
            total_fair_target=40.0,
            equity_gap_std_dev=2.0,
            overworked_count=1,
            underworked_count=0,
        )
        assert r.most_overworked_faculty_id is None
        assert r.most_underworked_faculty_id is None

    # --- total_workload ge=0.0 ---

    def test_total_workload_below_min(self):
        with pytest.raises(ValidationError):
            FacultyShapleyMetrics(
                faculty_results=[],
                total_workload=-1.0,
                total_fair_target=40.0,
                equity_gap_std_dev=2.0,
                overworked_count=0,
                underworked_count=0,
            )

    # --- equity_gap_std_dev ge=0.0 ---

    def test_equity_gap_std_dev_below_min(self):
        with pytest.raises(ValidationError):
            FacultyShapleyMetrics(
                faculty_results=[],
                total_workload=40.0,
                total_fair_target=40.0,
                equity_gap_std_dev=-1.0,
                overworked_count=0,
                underworked_count=0,
            )

    # --- overworked_count ge=0 ---

    def test_overworked_below_min(self):
        with pytest.raises(ValidationError):
            FacultyShapleyMetrics(
                faculty_results=[],
                total_workload=40.0,
                total_fair_target=40.0,
                equity_gap_std_dev=0.0,
                overworked_count=-1,
                underworked_count=0,
            )
