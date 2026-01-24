"""Pydantic schemas for enhanced swap auto-matching functionality."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class MatchPriority(str, Enum):
    """Priority level for match suggestions."""

    CRITICAL = "critical"  # Blocked week, urgent need
    HIGH = "high"  # Strong preference alignment
    MEDIUM = "medium"  # Good compatibility
    LOW = "low"  # Acceptable match


class MatchType(str, Enum):
    """Type of swap match."""

    MUTUAL = "mutual"  # Both parties want each other's weeks
    ONE_WAY = "one_way"  # One party wants, other is available
    ABSORB = "absorb"  # One party takes on a week


class SwapMatch(BaseModel):
    """A potential swap match between two requests."""

    match_id: UUID = Field(description="Unique identifier for this match")
    request_a_id: UUID = Field(description="First swap request ID")
    request_b_id: UUID = Field(description="Second swap request ID")
    faculty_a_id: UUID = Field(description="First faculty member ID")
    faculty_a_name: str = Field(description="First faculty member name")
    faculty_b_id: UUID = Field(description="Second faculty member ID")
    faculty_b_name: str = Field(description="Second faculty member name")
    week_a: date = Field(description="Week from faculty A")
    week_b: date = Field(description="Week from faculty B")
    match_type: MatchType = Field(description="Type of match")
    is_mutual: bool = Field(description="Whether both parties want each other's weeks")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ScoringBreakdown(BaseModel):
    """Detailed breakdown of compatibility scoring factors."""

    date_proximity_score: float = Field(
        ge=0.0, le=1.0, description="Score based on date closeness"
    )
    preference_alignment_score: float = Field(
        ge=0.0, le=1.0, description="Score based on preference matching"
    )
    workload_balance_score: float = Field(
        ge=0.0, le=1.0, description="Score based on workload fairness"
    )
    history_score: float = Field(
        ge=0.0, le=1.0, description="Score based on past swap patterns"
    )
    availability_score: float = Field(
        ge=0.0, le=1.0, description="Score based on faculty availability"
    )
    blocking_penalty: float = Field(
        ge=0.0, le=1.0, description="Penalty if weeks are blocked (1.0 = no penalty)"
    )
    total_score: float = Field(
        ge=0.0, le=1.0, description="Overall compatibility score"
    )

    class Config:
        from_attributes = True


class RankedMatch(BaseModel):
    """A swap match with ranking and explanation."""

    match: SwapMatch = Field(description="The swap match details")
    compatibility_score: float = Field(
        ge=0.0, le=1.0, description="Overall compatibility score (0-1)"
    )
    priority: MatchPriority = Field(description="Priority level for this match")
    scoring_breakdown: ScoringBreakdown = Field(
        description="Detailed scoring breakdown"
    )
    explanation: str = Field(
        description="Human-readable explanation of why this is a good match"
    )
    estimated_acceptance_probability: float = Field(
        ge=0.0, le=1.0, description="Estimated probability both parties will accept"
    )
    recommended_action: str = Field(description="Suggested action for this match")
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings or concerns"
    )

    class Config:
        from_attributes = True


class AutoMatchResult(BaseModel):
    """Result of auto-matching a single request."""

    request_id: UUID = Field(description="The swap request that was matched")
    faculty_id: UUID = Field(description="Faculty member who made the request")
    source_week: date = Field(description="Week they want to swap away")
    target_week: date | None = Field(
        None, description="Week they want to receive (if specified)"
    )
    matches_found: int = Field(ge=0, description="Number of compatible matches found")
    best_match: RankedMatch | None = Field(
        None, description="The best match if any found"
    )
    all_matches: list[RankedMatch] = Field(
        default_factory=list, description="All compatible matches"
    )
    matched_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(description="Whether matching was successful")
    message: str = Field(description="Status message")

    class Config:
        from_attributes = True


class BatchAutoMatchResult(BaseModel):
    """Result of auto-matching multiple pending requests."""

    total_requests_processed: int = Field(
        ge=0, description="Number of requests processed"
    )
    total_matches_found: int = Field(ge=0, description="Total number of matches found")
    successful_matches: list[AutoMatchResult] = Field(
        default_factory=list, description="Requests with successful matches"
    )
    no_matches: list[UUID] = Field(
        default_factory=list, description="Request IDs that had no matches"
    )
    high_priority_matches: list[AutoMatchResult] = Field(
        default_factory=list, description="High-priority matches requiring attention"
    )
    execution_time_seconds: float = Field(
        ge=0.0, description="Time taken to complete matching"
    )
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class MatchingCriteria(BaseModel):
    """Configurable parameters for the matching algorithm."""

    # Weight factors (must sum close to 1.0)
    date_proximity_weight: float = Field(
        default=0.20, ge=0.0, le=1.0, description="Weight for date proximity factor"
    )
    preference_alignment_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Weight for preference alignment factor",
    )
    workload_balance_weight: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Weight for workload balance factor"
    )
    history_weight: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Weight for past swap history factor"
    )
    availability_weight: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight for faculty availability factor",
    )

    # Thresholds
    minimum_score_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Minimum compatibility score to consider a match",
    )
    high_priority_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Score threshold for high-priority matches",
    )

    # Constraints
    max_matches_per_request: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of matches to return per request",
    )
    max_date_separation_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Maximum days between swap dates to consider compatible",
    )
    require_mutual_availability: bool = Field(
        default=True, description="Whether both parties must be available for the swap"
    )
    exclude_blocked_weeks: bool = Field(
        default=True, description="Whether to exclude matches involving blocked weeks"
    )
    consider_past_rejections: bool = Field(
        default=True,
        description="Whether to avoid suggesting previously rejected pairings",
    )

    # Historical analysis
    history_lookback_days: int = Field(
        default=365,
        ge=1,
        le=1825,
        description="Number of days to look back for swap history analysis",
    )

    @field_validator(
        "preference_alignment_weight",
        "workload_balance_weight",
        "history_weight",
        "availability_weight",
        "date_proximity_weight",
    )
    @classmethod
    def validate_weights(cls, v: float, info: ValidationInfo) -> float:
        """Ensure all weights are valid."""
        if v < 0 or v > 1:
            raise ValueError("Weights must be between 0 and 1")
        return v

    @property
    def total_weight(self) -> float:
        """Calculate total weight (should be close to 1.0)."""
        return (
            self.date_proximity_weight
            + self.preference_alignment_weight
            + self.workload_balance_weight
            + self.history_weight
            + self.availability_weight
        )

    class Config:
        from_attributes = True


class MatchingSuggestion(BaseModel):
    """A proactive suggestion for a faculty member to initiate a swap."""

    faculty_id: UUID = Field(description="Faculty member who would benefit")
    faculty_name: str = Field(description="Faculty member name")
    current_week: date = Field(description="Week they currently have")
    suggested_partner_id: UUID = Field(description="Suggested swap partner")
    suggested_partner_name: str = Field(description="Partner name")
    partner_week: date = Field(description="Week the partner has")
    benefit_score: float = Field(
        ge=0.0, le=1.0, description="How beneficial this swap would be"
    )
    reason: str = Field(description="Why this swap is suggested")
    action_text: str = Field(description="Suggested action text for UI")

    class Config:
        from_attributes = True


class MatchingAnalytics(BaseModel):
    """Analytics about the matching process."""

    date_range_start: date = Field(description="Start of analysis period")
    date_range_end: date = Field(description="End of analysis period")
    total_requests: int = Field(ge=0, description="Total swap requests in period")
    successful_matches: int = Field(ge=0, description="Number of successful matches")
    failed_matches: int = Field(ge=0, description="Number of failed matching attempts")
    average_match_score: float = Field(
        ge=0.0, le=1.0, description="Average compatibility score"
    )
    average_time_to_match_days: float = Field(
        ge=0.0, description="Average days to find a match"
    )
    top_scoring_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Which factors contribute most to successful matches",
    )
    common_blocking_reasons: list[str] = Field(
        default_factory=list, description="Most common reasons matches fail"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
