"""
Scheduler Explainability Schemas.

Provides transparency into scheduling decisions:
- Why a particular assignment was made
- What constraints were considered
- What alternatives were rejected
- Confidence in the decision
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for a scheduling decision."""

    HIGH = "high"  ***REMOVED*** Clear winner, large margin
    MEDIUM = "medium"  ***REMOVED*** Good choice, some alternatives close
    LOW = "low"  ***REMOVED*** Many viable alternatives, marginal decision


class ConstraintType(str, Enum):
    """Type of constraint."""

    HARD = "hard"  ***REMOVED*** Must not violate
    SOFT = "soft"  ***REMOVED*** Prefer to satisfy


class ConstraintStatus(str, Enum):
    """Whether a constraint was satisfied."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    NOT_APPLICABLE = "not_applicable"


class ConstraintEvaluation(BaseModel):
    """Evaluation of a single constraint for an assignment."""

    constraint_name: str
    constraint_type: ConstraintType
    status: ConstraintStatus
    weight: float = 1.0
    penalty: float = 0.0  ***REMOVED*** Penalty incurred (0 if satisfied)
    details: str | None = None  ***REMOVED*** Human-readable explanation


class AlternativeCandidate(BaseModel):
    """An alternative that was considered but not selected."""

    person_id: UUID
    person_name: str
    score: float
    rejection_reasons: list[str] = []
    constraint_violations: list[str] = []


class DecisionInputs(BaseModel):
    """Inputs that went into a scheduling decision."""

    block_id: UUID
    block_date: datetime
    block_time_of_day: str  ***REMOVED*** "AM" or "PM"
    rotation_template_id: UUID | None = None
    rotation_name: str | None = None
    eligible_residents: int  ***REMOVED*** How many residents were eligible
    active_constraints: list[str] = []  ***REMOVED*** Names of active constraints
    overrides_in_effect: list[str] = []  ***REMOVED*** Any overrides that applied


class DecisionExplanation(BaseModel):
    """
    Complete explanation of a scheduling decision.

    This provides full transparency into why an assignment was made,
    supporting ACGME accountability and fairness audits.
    """

    ***REMOVED*** Assignment identification
    assignment_id: UUID | None = None
    person_id: UUID
    person_name: str

    ***REMOVED*** Decision inputs
    inputs: DecisionInputs

    ***REMOVED*** Scoring breakdown
    score: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    ***REMOVED*** e.g., {"coverage": 1000, "equity_penalty": -50, "continuity_bonus": 10}

    ***REMOVED*** Constraint evaluation
    constraints_evaluated: list[ConstraintEvaluation] = []
    hard_constraints_satisfied: bool = True
    soft_constraint_penalties: float = 0.0

    ***REMOVED*** Alternatives considered
    alternatives: list[AlternativeCandidate] = []
    margin_vs_next_best: float = 0.0  ***REMOVED*** Score difference from 2nd best

    ***REMOVED*** Confidence assessment
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.5  ***REMOVED*** 0-1 numeric confidence
    confidence_factors: list[str] = []  ***REMOVED*** What influenced confidence

    ***REMOVED*** Trade-off summary (plain English)
    trade_off_summary: str = ""
    ***REMOVED*** e.g., "Chose Dr. Smith because they have 2 fewer assignments than average.
    ***REMOVED***        This slightly increases Friday coverage variance (+1 shift)."

    ***REMOVED*** Audit trail
    algorithm: str = ""
    solver_version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    random_seed: int | None = None

    class Config:
        from_attributes = True


class AssignmentWithExplanation(BaseModel):
    """Assignment response that includes the decision explanation."""

    id: UUID
    block_id: UUID
    person_id: UUID
    rotation_template_id: UUID | None
    role: str
    notes: str | None
    override_reason: str | None
    created_at: datetime
    updated_at: datetime

    ***REMOVED*** Explanation data
    explanation: DecisionExplanation | None = None
    confidence: ConfidenceLevel | None = None
    confidence_score: float | None = None

    class Config:
        from_attributes = True


class ExplainabilityReport(BaseModel):
    """
    Summary report of scheduling explainability for a date range.

    Useful for APE/PEC review and fairness audits.
    """

    start_date: datetime
    end_date: datetime
    total_assignments: int

    ***REMOVED*** Confidence distribution
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    average_confidence_score: float = 0.0

    ***REMOVED*** Constraint summary
    hard_constraint_violations: int = 0
    soft_constraint_penalties_total: float = 0.0
    most_common_violations: list[str] = []

    ***REMOVED*** Override summary
    overrides_used: int = 0
    override_reasons: list[str] = []

    ***REMOVED*** Fairness indicators
    fairness_score: float = 0.0  ***REMOVED*** Gini-based
    workload_variance: float = 0.0
    max_assignment_delta: int = 0  ***REMOVED*** Max diff from mean

    ***REMOVED*** Algorithm info
    algorithm_used: str = ""
    solver_runtime_seconds: float = 0.0
    random_seed: int | None = None
