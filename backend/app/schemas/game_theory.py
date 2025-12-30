"""Pydantic schemas for game theory API.

Request/response models for:
- Configuration strategies
- Tournament management
- Evolutionary simulations
- Validation results
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    """Types of configuration strategies."""

    COOPERATIVE = "cooperative"
    AGGRESSIVE = "aggressive"
    TIT_FOR_TAT = "tit_for_tat"
    GRUDGER = "grudger"
    PAVLOV = "pavlov"
    RANDOM = "random"
    SUSPICIOUS_TFT = "suspicious_tft"
    FORGIVING_TFT = "forgiving_tft"
    CUSTOM = "custom"


class SimulationStatus(str, Enum):
    """Status of a simulation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Strategy Schemas
# =============================================================================


class StrategyCreate(BaseModel):
    """Request to create a new configuration strategy."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    strategy_type: StrategyType

    # Configuration parameters
    utilization_target: float = Field(0.80, ge=0.0, le=1.0)
    cross_zone_borrowing: bool = True
    sacrifice_willingness: str = Field("medium", pattern="^(low|medium|high)$")
    defense_activation_threshold: int = Field(3, ge=1, le=5)
    response_timeout_ms: int = Field(5000, ge=100, le=60000)

    # Strategy behavior
    initial_action: str = Field("cooperate", pattern="^(cooperate|defect)$")
    forgiveness_probability: float = Field(0.0, ge=0.0, le=1.0)
    retaliation_memory: int = Field(1, ge=1, le=100)
    is_stochastic: bool = False

    # Custom logic (for CUSTOM type)
    custom_logic: dict | None = None


class StrategyUpdate(BaseModel):
    """Request to update a strategy."""

    name: str | None = None
    description: str | None = None
    utilization_target: float | None = None
    cross_zone_borrowing: bool | None = None
    sacrifice_willingness: str | None = None
    defense_activation_threshold: int | None = None
    response_timeout_ms: int | None = None
    forgiveness_probability: float | None = None
    is_active: bool | None = None


class StrategyResponse(BaseModel):
    """Response containing strategy details."""

    id: UUID
    name: str
    description: str | None
    strategy_type: StrategyType
    created_at: datetime

    utilization_target: float
    cross_zone_borrowing: bool
    sacrifice_willingness: str
    defense_activation_threshold: int
    response_timeout_ms: int

    initial_action: str
    forgiveness_probability: float
    retaliation_memory: int
    is_stochastic: bool

    tournaments_participated: int
    total_matches: int
    total_wins: int
    average_score: float | None
    cooperation_rate: float | None
    is_active: bool

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """Response containing list of strategies."""

    strategies: list[StrategyResponse]
    total: int


# =============================================================================
# Tournament Schemas
# =============================================================================


class TournamentCreate(BaseModel):
    """Request to create a new tournament."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    strategy_ids: list[UUID] = Field(..., min_length=2)

    # Configuration
    turns_per_match: int = Field(200, ge=10, le=1000)
    repetitions: int = Field(10, ge=1, le=100)
    noise: float = Field(0.0, ge=0.0, le=0.5)

    # Payoff matrix (optional, uses standard PD values by default)
    payoff_cc: float = Field(3.0, description="Both cooperate")
    payoff_cd: float = Field(0.0, description="I cooperate, they defect")
    payoff_dc: float = Field(5.0, description="I defect, they cooperate")
    payoff_dd: float = Field(1.0, description="Both defect")


class TournamentResponse(BaseModel):
    """Response containing tournament details."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    created_by: str | None

    turns_per_match: int
    repetitions: int
    noise: float

    strategy_ids: list[str] | None
    status: SimulationStatus

    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    celery_task_id: str | None
    total_matches: int | None
    winner_strategy_id: UUID | None
    winner_strategy_name: str | None

    class Config:
        from_attributes = True


class TournamentListResponse(BaseModel):
    """Response containing list of tournaments."""

    tournaments: list[TournamentResponse]
    total: int


class TournamentRanking(BaseModel):
    """Ranking entry for a strategy in a tournament."""

    rank: int
    strategy_id: UUID
    strategy_name: str
    total_score: float
    average_score: float
    wins: int
    losses: int
    ties: int
    cooperation_rate: float


class TournamentResultsResponse(BaseModel):
    """Detailed tournament results."""

    id: UUID
    name: str
    status: SimulationStatus
    completed_at: datetime | None

    # Rankings
    rankings: list[TournamentRanking]

    # Payoff matrix (strategy names as keys)
    payoff_matrix: dict[str, dict[str, float]]

    # Summary statistics
    total_matches: int
    total_turns: int
    average_cooperation_rate: float


class MatchResponse(BaseModel):
    """Response containing match details."""

    id: UUID
    tournament_id: UUID

    strategy1_id: UUID
    strategy1_name: str
    strategy2_id: UUID
    strategy2_name: str

    score1: float
    score2: float
    cooperation_rate1: float | None
    cooperation_rate2: float | None

    winner: str | None

    class Config:
        from_attributes = True


# =============================================================================
# Evolution Schemas
# =============================================================================


class EvolutionCreate(BaseModel):
    """Request to create an evolutionary simulation."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None

    # Initial population: {strategy_id: count}
    initial_composition: dict[str, int] = Field(..., min_length=2)

    # Configuration
    turns_per_interaction: int = Field(100, ge=10, le=500)
    max_generations: int = Field(1000, ge=10, le=10000)
    mutation_rate: float = Field(0.01, ge=0.0, le=0.5)


class EvolutionResponse(BaseModel):
    """Response containing evolution simulation details."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    created_by: str | None

    initial_population_size: int
    turns_per_interaction: int
    max_generations: int
    mutation_rate: float

    status: SimulationStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    celery_task_id: str | None
    generations_completed: int
    winner_strategy_id: UUID | None
    winner_strategy_name: str | None
    is_evolutionarily_stable: bool | None

    class Config:
        from_attributes = True


class EvolutionListResponse(BaseModel):
    """Response containing list of evolution simulations."""

    simulations: list[EvolutionResponse]
    total: int


class PopulationSnapshot(BaseModel):
    """Population state at a point in time."""

    generation: int
    populations: dict[str, int]  # strategy_name -> count


class EvolutionResultsResponse(BaseModel):
    """Detailed evolution results."""

    id: UUID
    name: str
    status: SimulationStatus
    completed_at: datetime | None

    generations_completed: int
    winner_strategy_name: str | None
    is_evolutionarily_stable: bool | None

    # Population history (sampled)
    population_history: list[PopulationSnapshot]

    # Final state
    final_population: dict[str, int]


# =============================================================================
# Validation Schemas
# =============================================================================


class ValidationRequest(BaseModel):
    """Request to validate a strategy against TFT."""

    strategy_id: UUID
    turns: int = Field(100, ge=10, le=500)
    repetitions: int = Field(10, ge=1, le=50)
    pass_threshold: float = Field(2.5, ge=0.0, le=5.0)


class ValidationResponse(BaseModel):
    """Response containing validation results."""

    id: UUID
    strategy_id: UUID
    strategy_name: str
    validated_at: datetime

    turns: int
    repetitions: int

    passed: bool
    average_score: float
    cooperation_rate: float
    pass_threshold: float

    assessment: str
    recommendation: str | None

    class Config:
        from_attributes = True


# =============================================================================
# Analysis Schemas
# =============================================================================


class ConfigAnalysisRequest(BaseModel):
    """Request to analyze current resilience config using game theory."""

    utilization_target: float = Field(0.80, ge=0.0, le=1.0)
    cross_zone_borrowing: bool = True
    sacrifice_willingness: str = Field("medium", pattern="^(low|medium|high)$")
    defense_activation_threshold: int = Field(3, ge=1, le=5)


class ConfigAnalysisResponse(BaseModel):
    """Response from configuration analysis."""

    config_name: str
    matchup_results: dict[str, dict]
    average_score: float
    cooperation_rate: float
    recommendation: str
    strategy_classification: StrategyType


class OptimalConfigRequest(BaseModel):
    """Request to find optimal configuration through evolution."""

    candidates: list[ConfigAnalysisRequest]
    generations: int = Field(100, ge=10, le=1000)


class OptimalConfigResponse(BaseModel):
    """Response from optimal configuration search."""

    optimal_config: ConfigAnalysisRequest
    generations_to_win: int
    is_evolutionarily_stable: bool
    competing_configs: list[str]


# =============================================================================
# Shapley Value Schemas (Fair Workload Distribution)
# =============================================================================


class ShapleyValueRequest(BaseModel):
    """Request to calculate Shapley values for faculty workload."""

    faculty_ids: list[UUID] = Field(
        ..., min_length=2, description="Faculty members to analyze (minimum 2)"
    )
    start_date: datetime = Field(..., description="Start date for workload analysis")
    end_date: datetime = Field(
        ..., description="End date for workload analysis (inclusive)"
    )
    num_samples: int = Field(
        1000,
        ge=100,
        le=10000,
        description="Monte Carlo samples (more = better accuracy, default 1000)",
    )


class ShapleyValueResult(BaseModel):
    """Shapley value analysis result for a single faculty member."""

    faculty_id: UUID
    faculty_name: str

    # Core Shapley metrics
    shapley_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized Shapley value (0-1, proportion of total contribution)",
    )
    marginal_contribution: float = Field(
        ..., ge=0.0, description="Marginal contribution to coverage (blocks)"
    )

    # Workload fairness
    fair_workload_target: float = Field(
        ..., ge=0.0, description="Fair workload in hours based on Shapley proportion"
    )
    current_workload: float = Field(..., ge=0.0, description="Actual workload in hours")
    equity_gap: float = Field(
        ..., description="Hours above (+) or below (-) fair target"
    )

    class Config:
        from_attributes = True


class FacultyShapleyMetrics(BaseModel):
    """Comprehensive Shapley-based equity metrics for a faculty group."""

    # Per-faculty results
    faculty_results: list[ShapleyValueResult]

    # Summary statistics
    total_workload: float = Field(
        ..., ge=0.0, description="Total hours worked by all faculty"
    )
    total_fair_target: float = Field(
        ..., ge=0.0, description="Sum of all fair workload targets"
    )
    equity_gap_std_dev: float = Field(
        ...,
        ge=0.0,
        description="Standard deviation of equity gaps (lower = more equitable)",
    )

    # Equity indicators
    overworked_count: int = Field(
        ..., ge=0, description="Number of faculty working above fair share"
    )
    underworked_count: int = Field(
        ..., ge=0, description="Number of faculty working below fair share"
    )

    # Outliers
    most_overworked_faculty_id: UUID | None = Field(
        None, description="Faculty ID with largest positive equity gap"
    )
    most_underworked_faculty_id: UUID | None = Field(
        None, description="Faculty ID with largest negative equity gap"
    )
