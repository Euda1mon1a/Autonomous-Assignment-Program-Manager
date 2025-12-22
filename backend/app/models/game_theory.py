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
    COOPERATIVE = "cooperative"           ***REMOVED*** Always cooperate (conservative config)
    AGGRESSIVE = "aggressive"             ***REMOVED*** Always defect (aggressive config)
    TIT_FOR_TAT = "tit_for_tat"          ***REMOVED*** Mirror opponent behavior
    GRUDGER = "grudger"                   ***REMOVED*** Cooperate until betrayed, then always defect
    PAVLOV = "pavlov"                     ***REMOVED*** Win-stay, lose-shift
    RANDOM = "random"                     ***REMOVED*** Chaos monkey
    SUSPICIOUS_TFT = "suspicious_tft"     ***REMOVED*** Defect first, then TFT
    FORGIVING_TFT = "forgiving_tft"       ***REMOVED*** TFT but forgives occasional defection
    CUSTOM = "custom"                     ***REMOVED*** User-defined strategy


class SimulationType(str, enum.Enum):
    """Types of game theory simulations."""
    TOURNAMENT = "tournament"             ***REMOVED*** Round-robin tournament
    EVOLUTION = "evolution"               ***REMOVED*** Moran process evolutionary simulation
    SINGLE_MATCH = "single_match"         ***REMOVED*** Single head-to-head match
    VALIDATION = "validation"             ***REMOVED*** TFT validation test


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
    strategy_type = Column(String(30), nullable=False)  ***REMOVED*** StrategyType enum
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    ***REMOVED*** Configuration parameters (maps to resilience config)
    utilization_target = Column(Float, default=0.80)
    cross_zone_borrowing = Column(Boolean, default=True)
    sacrifice_willingness = Column(String(20), default="medium")  ***REMOVED*** low, medium, high
    defense_activation_threshold = Column(Integer, default=3)     ***REMOVED*** Defense level 1-5
    response_timeout_ms = Column(Integer, default=5000)

    ***REMOVED*** Strategy behavior parameters
    initial_action = Column(String(10), default="cooperate")  ***REMOVED*** cooperate or defect
    forgiveness_probability = Column(Float, default=0.0)      ***REMOVED*** Chance to forgive defection
    retaliation_memory = Column(Integer, default=1)           ***REMOVED*** Rounds to remember defection
    is_stochastic = Column(Boolean, default=False)

    ***REMOVED*** Custom strategy logic (for CUSTOM type)
    custom_logic = Column(JSONType)  ***REMOVED*** Python code or rule definitions

    ***REMOVED*** Usage tracking
    tournaments_participated = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    average_score = Column(Float)
    cooperation_rate = Column(Float)

    ***REMOVED*** Active/archive status
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

    ***REMOVED*** Tournament configuration
    turns_per_match = Column(Integer, nullable=False, default=200)
    repetitions = Column(Integer, nullable=False, default=10)
    noise = Column(Float, default=0.0)  ***REMOVED*** Probability of random action

    ***REMOVED*** Payoff matrix (standard PD values)
    payoff_cc = Column(Float, default=3.0)  ***REMOVED*** Both cooperate
    payoff_cd = Column(Float, default=0.0)  ***REMOVED*** I cooperate, they defect
    payoff_dc = Column(Float, default=5.0)  ***REMOVED*** I defect, they cooperate
    payoff_dd = Column(Float, default=1.0)  ***REMOVED*** Both defect

    ***REMOVED*** Participants (strategy IDs)
    strategy_ids = Column(StringArrayType())

    ***REMOVED*** Execution status
    status = Column(String(20), nullable=False, default="pending")  ***REMOVED*** SimulationStatus
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    ***REMOVED*** Celery task tracking
    celery_task_id = Column(String(100))

    ***REMOVED*** Results summary
    total_matches = Column(Integer)
    winner_strategy_id = Column(GUID())
    winner_strategy_name = Column(String(100))

    ***REMOVED*** Full results stored as JSON
    results_json = Column(JSONType)
    rankings = Column(JSONType)  ***REMOVED*** List of {strategy_id, strategy_name, score, rank}
    payoff_matrix = Column(JSONType)  ***REMOVED*** 2D matrix of average payoffs

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

    ***REMOVED*** Evolution configuration
    initial_population_size = Column(Integer, nullable=False, default=100)
    turns_per_interaction = Column(Integer, nullable=False, default=100)
    max_generations = Column(Integer, default=1000)
    mutation_rate = Column(Float, default=0.01)  ***REMOVED*** Noise/mutation probability

    ***REMOVED*** Initial population composition
    ***REMOVED*** JSON: {strategy_id: count, ...}
    initial_composition = Column(JSONType, nullable=False)

    ***REMOVED*** Execution status
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    ***REMOVED*** Celery task tracking
    celery_task_id = Column(String(100))

    ***REMOVED*** Results
    generations_completed = Column(Integer, default=0)
    winner_strategy_id = Column(GUID())
    winner_strategy_name = Column(String(100))
    is_evolutionarily_stable = Column(Boolean)

    ***REMOVED*** Population history (sampled at intervals)
    ***REMOVED*** List of {generation: int, populations: {strategy_name: count}}
    population_history = Column(JSONType)

    ***REMOVED*** Final population state
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

    ***REMOVED*** Participants
    strategy1_id = Column(GUID(), ForeignKey("game_theory_strategies.id"), nullable=False)
    strategy1_name = Column(String(100))
    strategy2_id = Column(GUID(), ForeignKey("game_theory_strategies.id"), nullable=False)
    strategy2_name = Column(String(100))

    ***REMOVED*** Results
    score1 = Column(Float, nullable=False)
    score2 = Column(Float, nullable=False)
    cooperation_rate1 = Column(Float)  ***REMOVED*** Fraction of cooperations by strategy 1
    cooperation_rate2 = Column(Float)

    ***REMOVED*** Action history (for detailed analysis)
    ***REMOVED*** Stored as string of C/D, e.g., "CCDCDC..."
    actions1 = Column(Text)
    actions2 = Column(Text)

    ***REMOVED*** Relationships
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

    ***REMOVED*** Validation configuration
    turns = Column(Integer, default=100)
    repetitions = Column(Integer, default=10)

    ***REMOVED*** Results
    passed = Column(Boolean, nullable=False)
    average_score = Column(Float, nullable=False)
    cooperation_rate = Column(Float, nullable=False)

    ***REMOVED*** Thresholds used
    pass_threshold = Column(Float, default=2.5)  ***REMOVED*** Mutual cooperation score

    ***REMOVED*** Assessment
    assessment = Column(String(50))  ***REMOVED*** cooperative, too_aggressive, exploitable
    recommendation = Column(Text)

    ***REMOVED*** Relationship
    strategy = relationship("ConfigStrategy", backref="validations")

    def __repr__(self):
        return f"<ValidationResult(strategy='{self.strategy_name}', passed={self.passed})>"
