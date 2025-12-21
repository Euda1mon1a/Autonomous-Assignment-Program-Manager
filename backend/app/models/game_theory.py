"""Game theory database models for Axelrod-style tournament simulations.

Models for tracking:
- Tournament configurations and results
- Configuration strategies
- Evolutionary simulation results
- Match history and payoff matrices

Based on Robert Axelrod's Prisoner's Dilemma tournaments for
empirically testing scheduling and resilience configurations.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType, StringArrayType


class StrategyType(str, enum.Enum):
    """Types of configuration strategies."""
    COOPERATIVE = "cooperative"           # Always cooperate (conservative config)
    AGGRESSIVE = "aggressive"             # Always defect (aggressive config)
    TIT_FOR_TAT = "tit_for_tat"          # Mirror opponent behavior
    GRUDGER = "grudger"                   # Cooperate until betrayed, then always defect
    PAVLOV = "pavlov"                     # Win-stay, lose-shift
    RANDOM = "random"                     # Chaos monkey
    SUSPICIOUS_TFT = "suspicious_tft"     # Defect first, then TFT
    FORGIVING_TFT = "forgiving_tft"       # TFT but forgives occasional defection
    CUSTOM = "custom"                     # User-defined strategy


class SimulationType(str, enum.Enum):
    """Types of game theory simulations."""
    TOURNAMENT = "tournament"             # Round-robin tournament
    EVOLUTION = "evolution"               # Moran process evolutionary simulation
    SINGLE_MATCH = "single_match"         # Single head-to-head match
    VALIDATION = "validation"             # TFT validation test


class SimulationStatus(str, enum.Enum):
    """Status of a simulation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConfigStrategy(Base):
    """
    Represents a configuration strategy for game theory simulations.

    Maps resilience configurations to Prisoner's Dilemma strategies.
    """
    __tablename__ = "game_theory_strategies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(30), nullable=False)  # StrategyType enum
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    # Configuration parameters (maps to resilience config)
    utilization_target = Column(Float, default=0.80)
    cross_zone_borrowing = Column(Boolean, default=True)
    sacrifice_willingness = Column(String(20), default="medium")  # low, medium, high
    defense_activation_threshold = Column(Integer, default=3)     # Defense level 1-5
    response_timeout_ms = Column(Integer, default=5000)

    # Strategy behavior parameters
    initial_action = Column(String(10), default="cooperate")  # cooperate or defect
    forgiveness_probability = Column(Float, default=0.0)      # Chance to forgive defection
    retaliation_memory = Column(Integer, default=1)           # Rounds to remember defection
    is_stochastic = Column(Boolean, default=False)

    # Custom strategy logic (for CUSTOM type)
    custom_logic = Column(JSONType)  # Python code or rule definitions

    # Usage tracking
    tournaments_participated = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    average_score = Column(Float)
    cooperation_rate = Column(Float)

    # Active/archive status
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ConfigStrategy(name='{self.name}', type='{self.strategy_type}')>"


class GameTheoryTournament(Base):
    """
    Represents a round-robin tournament between configuration strategies.

    Implements Axelrod's tournament format where each strategy plays
    against every other strategy (including itself) multiple times.
    """
    __tablename__ = "game_theory_tournaments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    # Tournament configuration
    turns_per_match = Column(Integer, nullable=False, default=200)
    repetitions = Column(Integer, nullable=False, default=10)
    noise = Column(Float, default=0.0)  # Probability of random action

    # Payoff matrix (standard PD values)
    payoff_cc = Column(Float, default=3.0)  # Both cooperate
    payoff_cd = Column(Float, default=0.0)  # I cooperate, they defect
    payoff_dc = Column(Float, default=5.0)  # I defect, they cooperate
    payoff_dd = Column(Float, default=1.0)  # Both defect

    # Participants (strategy IDs)
    strategy_ids = Column(StringArrayType())

    # Execution status
    status = Column(String(20), nullable=False, default="pending")  # SimulationStatus
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # Celery task tracking
    celery_task_id = Column(String(100))

    # Results summary
    total_matches = Column(Integer)
    winner_strategy_id = Column(GUID())
    winner_strategy_name = Column(String(100))

    # Full results stored as JSON
    results_json = Column(JSONType)
    rankings = Column(JSONType)  # List of {strategy_id, strategy_name, score, rank}
    payoff_matrix = Column(JSONType)  # 2D matrix of average payoffs

    def __repr__(self):
        return f"<GameTheoryTournament(name='{self.name}', status='{self.status}')>"

    @property
    def is_complete(self) -> bool:
        return self.status == SimulationStatus.COMPLETED.value


class EvolutionSimulation(Base):
    """
    Represents a Moran process evolutionary simulation.

    Tests which configuration strategy is evolutionarily stable -
    meaning it cannot be invaded by mutant strategies.
    """
    __tablename__ = "game_theory_evolution"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    # Evolution configuration
    initial_population_size = Column(Integer, nullable=False, default=100)
    turns_per_interaction = Column(Integer, nullable=False, default=100)
    max_generations = Column(Integer, default=1000)
    mutation_rate = Column(Float, default=0.01)  # Noise/mutation probability

    # Initial population composition
    # JSON: {strategy_id: count, ...}
    initial_composition = Column(JSONType, nullable=False)

    # Execution status
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # Celery task tracking
    celery_task_id = Column(String(100))

    # Results
    generations_completed = Column(Integer, default=0)
    winner_strategy_id = Column(GUID())
    winner_strategy_name = Column(String(100))
    is_evolutionarily_stable = Column(Boolean)

    # Population history (sampled at intervals)
    # List of {generation: int, populations: {strategy_name: count}}
    population_history = Column(JSONType)

    # Final population state
    final_population = Column(JSONType)

    def __repr__(self):
        return f"<EvolutionSimulation(name='{self.name}', winner='{self.winner_strategy_name}')>"


class TournamentMatch(Base):
    """
    Stores individual match results within a tournament.

    Provides detailed record of each strategy pairing.
    """
    __tablename__ = "game_theory_matches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(GUID(), ForeignKey("game_theory_tournaments.id"), nullable=False)

    # Participants
    strategy1_id = Column(GUID(), ForeignKey("game_theory_strategies.id"), nullable=False)
    strategy1_name = Column(String(100))
    strategy2_id = Column(GUID(), ForeignKey("game_theory_strategies.id"), nullable=False)
    strategy2_name = Column(String(100))

    # Results
    score1 = Column(Float, nullable=False)
    score2 = Column(Float, nullable=False)
    cooperation_rate1 = Column(Float)  # Fraction of cooperations by strategy 1
    cooperation_rate2 = Column(Float)

    # Action history (for detailed analysis)
    # Stored as string of C/D, e.g., "CCDCDC..."
    actions1 = Column(Text)
    actions2 = Column(Text)

    # Relationships
    tournament = relationship("GameTheoryTournament", backref="matches")
    strategy1 = relationship("ConfigStrategy", foreign_keys=[strategy1_id])
    strategy2 = relationship("ConfigStrategy", foreign_keys=[strategy2_id])

    def __repr__(self):
        return f"<TournamentMatch({self.strategy1_name} vs {self.strategy2_name})>"

    @property
    def winner(self) -> str | None:
        """Get the winner of this match, or None if tie."""
        if self.score1 > self.score2:
            return self.strategy1_name
        elif self.score2 > self.score1:
            return self.strategy2_name
        return None


class ValidationResult(Base):
    """
    Stores results of TFT validation tests.

    Tests whether a configuration can coexist with a Tit for Tat
    validator - a benchmark for production-ready behavior.
    """
    __tablename__ = "game_theory_validations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(GUID(), ForeignKey("game_theory_strategies.id"), nullable=False)
    strategy_name = Column(String(100))
    validated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Validation configuration
    turns = Column(Integer, default=100)
    repetitions = Column(Integer, default=10)

    # Results
    passed = Column(Boolean, nullable=False)
    average_score = Column(Float, nullable=False)
    cooperation_rate = Column(Float, nullable=False)

    # Thresholds used
    pass_threshold = Column(Float, default=2.5)  # Mutual cooperation score

    # Assessment
    assessment = Column(String(50))  # cooperative, too_aggressive, exploitable
    recommendation = Column(Text)

    # Relationship
    strategy = relationship("ConfigStrategy", backref="validations")

    def __repr__(self):
        return f"<ValidationResult(strategy='{self.strategy_name}', passed={self.passed})>"
