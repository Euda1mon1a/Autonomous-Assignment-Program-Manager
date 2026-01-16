"""Pydantic schemas for gamified wellness and survey data collection.

This module defines the request/response schemas for the wellness API,
including survey submission, gamification, and Hopfield visualization.
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class SurveyTypeEnum(str, Enum):
    """Types of validated survey instruments."""

    BURNOUT = "burnout"
    STRESS = "stress"
    SLEEP = "sleep"
    EFFICACY = "efficacy"
    PULSE = "pulse"
    HOPFIELD = "hopfield"
    CUSTOM = "custom"


class SurveyFrequencyEnum(str, Enum):
    """How often surveys can be taken."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    BLOCK = "block"
    ANNUAL = "annual"


class TransactionTypeEnum(str, Enum):
    """Types of point transactions."""

    SURVEY = "survey"
    STREAK = "streak"
    ACHIEVEMENT = "achievement"
    BLOCK_BONUS = "block_bonus"
    ADMIN = "admin"
    REDEMPTION = "redemption"


# ============================================================================
# Survey Definition Schemas
# ============================================================================


class QuestionOption(BaseModel):
    """An option for a multiple-choice question."""

    value: int | str
    label: str
    score: int | float | None = None  # For scoring


class SurveyQuestion(BaseModel):
    """A single question in a survey."""

    id: str
    text: str
    question_type: str = "likert"  # likert, multiple_choice, slider, text
    required: bool = True
    options: list[QuestionOption] | None = None
    min_value: int | None = None  # For slider
    max_value: int | None = None  # For slider
    min_label: str | None = None  # For slider endpoints
    max_label: str | None = None


class SurveyBase(BaseModel):
    """Base schema for survey data."""

    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=200)
    survey_type: SurveyTypeEnum
    description: str | None = None
    instructions: str | None = None
    points_value: int = Field(default=50, ge=0)
    estimated_seconds: int = Field(default=60, ge=1)
    frequency: SurveyFrequencyEnum = SurveyFrequencyEnum.WEEKLY


class SurveyCreate(SurveyBase):
    """Schema for creating a new survey."""

    questions: list[SurveyQuestion]
    scoring_algorithm: dict | None = None
    target_roles: list[str] = Field(default_factory=list)


class SurveyUpdate(BaseModel):
    """Schema for updating a survey."""

    display_name: str | None = None
    description: str | None = None
    instructions: str | None = None
    points_value: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    target_roles: list[str] | None = None


class SurveyResponse(SurveyBase):
    """Schema for survey in responses."""

    id: UUID
    questions: list[SurveyQuestion]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SurveyListItem(BaseModel):
    """Abbreviated survey for list views."""

    id: UUID
    name: str
    display_name: str
    survey_type: SurveyTypeEnum
    points_value: int
    estimated_seconds: int
    frequency: SurveyFrequencyEnum
    is_available: bool = True  # Based on cooldown
    next_available_at: datetime | None = None
    completed_this_period: bool = False


# ============================================================================
# Survey Response Schemas
# ============================================================================


class SurveyResponseCreate(BaseModel):
    """Schema for submitting a survey response."""

    responses: dict[str, int | str | float]  # {question_id: answer}
    block_number: int | None = Field(default=None, ge=0, le=13)
    academic_year: int | None = Field(default=None, ge=2000, le=2100)

    @field_validator("responses")
    @classmethod
    def validate_responses(cls, v: dict) -> dict:
        if not v:
            raise ValueError("At least one response is required")
        return v


class SurveySubmissionResult(BaseModel):
    """Result of submitting a survey response."""

    success: bool
    response_id: UUID | None = None
    score: float | None = None
    score_interpretation: str | None = None
    points_earned: int = 0
    new_achievements: list[str] = Field(default_factory=list)
    streak_updated: bool = False
    current_streak: int = 0
    message: str = ""


class SurveyResponseSummary(BaseModel):
    """Summary of a past survey response."""

    id: UUID
    survey_id: UUID
    survey_name: str
    survey_type: SurveyTypeEnum
    score: float | None
    score_interpretation: str | None
    submitted_at: datetime
    block_number: int | None
    academic_year: int | None


class SurveyHistoryResponse(BaseModel):
    """Response for survey history endpoint."""

    responses: list[SurveyResponseSummary]
    total: int
    page: int
    page_size: int


# ============================================================================
# Wellness Account Schemas
# ============================================================================


class AchievementInfo(BaseModel):
    """Information about an achievement."""

    code: str
    name: str
    description: str
    icon: str  # Emoji or icon class
    earned: bool = False
    earned_at: datetime | None = None
    progress: float | None = None  # 0-1 progress toward earning
    criteria: str | None = None


class WellnessAccountResponse(BaseModel):
    """Response for wellness account details."""

    person_id: UUID
    points_balance: int
    points_lifetime: int
    current_streak_weeks: int
    longest_streak_weeks: int
    last_activity_date: date | None
    streak_start_date: date | None
    leaderboard_opt_in: bool
    display_name: str | None
    research_consent: bool
    achievements: list[AchievementInfo]
    surveys_completed_this_week: int = 0
    surveys_available: int = 0


class WellnessAccountUpdate(BaseModel):
    """Schema for updating wellness account settings."""

    leaderboard_opt_in: bool | None = None
    display_name: str | None = Field(default=None, min_length=3, max_length=50)
    research_consent: bool | None = None


class LeaderboardOptInRequest(BaseModel):
    """Request to opt into leaderboard with display name."""

    opt_in: bool
    display_name: str | None = Field(default=None, min_length=3, max_length=50)


class ConsentRequest(BaseModel):
    """Request to provide research consent."""

    consent: bool
    consent_version: str = "1.0"


# ============================================================================
# Leaderboard Schemas
# ============================================================================


class LeaderboardEntry(BaseModel):
    """A single entry on the leaderboard."""

    rank: int
    display_name: str
    points: int
    streak: int
    is_you: bool = False  # True if this is the requesting user


class LeaderboardResponse(BaseModel):
    """Response for leaderboard endpoint."""

    entries: list[LeaderboardEntry]
    total_participants: int
    your_rank: int | None = None
    your_points: int | None = None
    snapshot_date: date | None = None


# ============================================================================
# Point Transaction Schemas
# ============================================================================


class PointTransactionResponse(BaseModel):
    """A single point transaction."""

    id: UUID
    points: int
    balance_after: int
    transaction_type: TransactionTypeEnum
    source: str
    created_at: datetime


class PointHistoryResponse(BaseModel):
    """Response for point history endpoint."""

    transactions: list[PointTransactionResponse]
    total: int
    page: int
    page_size: int
    current_balance: int


# ============================================================================
# Hopfield Position Schemas
# ============================================================================


class HopfieldPositionCreate(BaseModel):
    """Schema for submitting a Hopfield landscape position."""

    x_position: float = Field(..., ge=0, le=1)
    y_position: float = Field(..., ge=0, le=1)
    z_position: float | None = Field(default=None, ge=0, le=1)
    confidence: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=500)
    block_number: int | None = Field(default=None, ge=0, le=13)
    academic_year: int | None = Field(default=None, ge=2000, le=2100)


class HopfieldPositionResult(BaseModel):
    """Result after submitting a Hopfield position."""

    success: bool
    position_id: UUID | None = None
    basin_depth: float | None = None
    energy_value: float | None = None
    stability_score: float | None = None
    nearest_attractor_type: str | None = None
    points_earned: int = 0
    message: str = ""


class HopfieldLandscapeData(BaseModel):
    """Data for rendering the Hopfield energy landscape."""

    # Grid data for energy surface
    x_grid: list[float]  # X coordinates
    y_grid: list[float]  # Y coordinates
    energy_grid: list[list[float]]  # Energy values at each point

    # Attractor positions
    attractors: list[dict]  # {id, x, y, type, energy, label}

    # Current computed state
    current_position: dict | None = None  # {x, y, energy, basin_depth}

    # Aggregate user positions (anonymized)
    aggregate_positions: list[dict] | None = None  # {x, y, count}

    # Metadata
    computed_at: datetime
    block_number: int | None = None
    academic_year: int | None = None


class HopfieldAggregatesResponse(BaseModel):
    """Aggregated Hopfield positions for program-wide view."""

    total_positions: int
    average_x: float | None = None
    average_y: float | None = None
    average_basin_depth: float | None = None
    average_energy: float | None = None
    computed_basin_depth: float | None = None  # From algorithm
    agreement_score: float | None = None  # How much users agree with algorithm
    block_number: int | None = None
    academic_year: int | None = None


# ============================================================================
# Quick Pulse Schemas
# ============================================================================


class QuickPulseSubmit(BaseModel):
    """Schema for quick pulse check-in."""

    mood: int = Field(..., ge=1, le=5)  # 1=very low, 5=great
    energy: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=200)


class QuickPulseResult(BaseModel):
    """Result of quick pulse submission."""

    success: bool
    points_earned: int = 0
    current_streak: int = 0
    message: str = ""


# ============================================================================
# Analytics Schemas (Admin)
# ============================================================================


class WellnessAnalyticsSummary(BaseModel):
    """Summary analytics for wellness dashboard."""

    # Participation
    total_participants: int
    active_this_week: int
    active_this_block: int
    participation_rate: float  # 0-1

    # Surveys
    total_responses_this_week: int
    total_responses_this_block: int
    average_responses_per_person: float

    # Scores (aggregated, anonymized)
    average_burnout_score: float | None = None
    average_stress_score: float | None = None
    average_sleep_score: float | None = None

    # Engagement
    average_streak: float
    longest_streak: int
    total_points_earned_this_week: int

    # Hopfield
    hopfield_positions_this_week: int
    average_basin_depth: float | None = None


class CorrelationDataPoint(BaseModel):
    """A data point for algorithm-survey correlation."""

    algorithm_value: float
    survey_score: float
    block_number: int | None = None
    academic_year: int | None = None


class CorrelationAnalysis(BaseModel):
    """Correlation between algorithm predictions and survey responses."""

    algorithm_name: str  # e.g., "burnout_rt", "fire_danger_index"
    survey_name: str  # e.g., "MBI-2", "PSS-4"
    correlation_coefficient: float  # -1 to 1
    p_value: float
    sample_size: int
    data_points: list[CorrelationDataPoint] | None = None  # Optional raw data
    analysis_date: datetime


class WellnessExportRequest(BaseModel):
    """Request for de-identified data export."""

    start_date: date | None = None
    end_date: date | None = None
    survey_types: list[SurveyTypeEnum] | None = None
    include_hopfield: bool = True
    include_algorithm_snapshots: bool = True
    format: str = "csv"  # csv, json


class WellnessExportResponse(BaseModel):
    """Response for data export request."""

    export_id: UUID
    status: str  # pending, processing, ready, failed
    download_url: str | None = None
    record_count: int | None = None
    created_at: datetime


# ============================================================================
# Dashboard Widget Schemas
# ============================================================================


class QuickPulseWidgetData(BaseModel):
    """Data for the quick pulse dashboard widget."""

    can_submit: bool = True
    last_submitted_at: datetime | None = None
    current_streak: int = 0
    points_balance: int = 0
    available_surveys: list[SurveyListItem] = Field(default_factory=list)
    recent_achievements: list[AchievementInfo] = Field(default_factory=list)


# ============================================================================
# Predefined Survey Instruments
# ============================================================================

# MBI-2 (2-item Maslach Burnout Inventory)
MBI_2_QUESTIONS = [
    SurveyQuestion(
        id="mbi_ee",
        text="I feel emotionally drained from my work.",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=0),
            QuestionOption(value=1, label="A few times a year", score=1),
            QuestionOption(value=2, label="Once a month", score=2),
            QuestionOption(value=3, label="A few times a month", score=3),
            QuestionOption(value=4, label="Once a week", score=4),
            QuestionOption(value=5, label="A few times a week", score=5),
            QuestionOption(value=6, label="Every day", score=6),
        ],
    ),
    SurveyQuestion(
        id="mbi_dp",
        text="I have become more callous toward people since I took this job.",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=0),
            QuestionOption(value=1, label="A few times a year", score=1),
            QuestionOption(value=2, label="Once a month", score=2),
            QuestionOption(value=3, label="A few times a month", score=3),
            QuestionOption(value=4, label="Once a week", score=4),
            QuestionOption(value=5, label="A few times a week", score=5),
            QuestionOption(value=6, label="Every day", score=6),
        ],
    ),
]

# PSS-4 (4-item Perceived Stress Scale)
PSS_4_QUESTIONS = [
    SurveyQuestion(
        id="pss_1",
        text="In the last week, how often have you felt that you were unable to control the important things in your life?",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=0),
            QuestionOption(value=1, label="Almost never", score=1),
            QuestionOption(value=2, label="Sometimes", score=2),
            QuestionOption(value=3, label="Fairly often", score=3),
            QuestionOption(value=4, label="Very often", score=4),
        ],
    ),
    SurveyQuestion(
        id="pss_2",
        text="In the last week, how often have you felt confident about your ability to handle your personal problems?",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=4),  # Reverse scored
            QuestionOption(value=1, label="Almost never", score=3),
            QuestionOption(value=2, label="Sometimes", score=2),
            QuestionOption(value=3, label="Fairly often", score=1),
            QuestionOption(value=4, label="Very often", score=0),
        ],
    ),
    SurveyQuestion(
        id="pss_3",
        text="In the last week, how often have you felt that things were going your way?",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=4),  # Reverse scored
            QuestionOption(value=1, label="Almost never", score=3),
            QuestionOption(value=2, label="Sometimes", score=2),
            QuestionOption(value=3, label="Fairly often", score=1),
            QuestionOption(value=4, label="Very often", score=0),
        ],
    ),
    SurveyQuestion(
        id="pss_4",
        text="In the last week, how often have you felt difficulties were piling up so high that you could not overcome them?",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Never", score=0),
            QuestionOption(value=1, label="Almost never", score=1),
            QuestionOption(value=2, label="Sometimes", score=2),
            QuestionOption(value=3, label="Fairly often", score=3),
            QuestionOption(value=4, label="Very often", score=4),
        ],
    ),
]

# PSQI-1 (Single-item sleep quality)
PSQI_1_QUESTIONS = [
    SurveyQuestion(
        id="psqi_quality",
        text="During the past week, how would you rate your sleep quality overall?",
        question_type="likert",
        options=[
            QuestionOption(value=0, label="Very good", score=0),
            QuestionOption(value=1, label="Fairly good", score=1),
            QuestionOption(value=2, label="Fairly bad", score=2),
            QuestionOption(value=3, label="Very bad", score=3),
        ],
    ),
]

# GSE-4 (4-item General Self-Efficacy Scale subset)
GSE_4_QUESTIONS = [
    SurveyQuestion(
        id="gse_1",
        text="I can always manage to solve difficult problems if I try hard enough.",
        question_type="likert",
        options=[
            QuestionOption(value=1, label="Not at all true", score=1),
            QuestionOption(value=2, label="Hardly true", score=2),
            QuestionOption(value=3, label="Moderately true", score=3),
            QuestionOption(value=4, label="Exactly true", score=4),
        ],
    ),
    SurveyQuestion(
        id="gse_2",
        text="I am confident that I could deal efficiently with unexpected events.",
        question_type="likert",
        options=[
            QuestionOption(value=1, label="Not at all true", score=1),
            QuestionOption(value=2, label="Hardly true", score=2),
            QuestionOption(value=3, label="Moderately true", score=3),
            QuestionOption(value=4, label="Exactly true", score=4),
        ],
    ),
    SurveyQuestion(
        id="gse_3",
        text="I can remain calm when facing difficulties because I can rely on my coping abilities.",
        question_type="likert",
        options=[
            QuestionOption(value=1, label="Not at all true", score=1),
            QuestionOption(value=2, label="Hardly true", score=2),
            QuestionOption(value=3, label="Moderately true", score=3),
            QuestionOption(value=4, label="Exactly true", score=4),
        ],
    ),
    SurveyQuestion(
        id="gse_4",
        text="When I am confronted with a problem, I can usually find several solutions.",
        question_type="likert",
        options=[
            QuestionOption(value=1, label="Not at all true", score=1),
            QuestionOption(value=2, label="Hardly true", score=2),
            QuestionOption(value=3, label="Moderately true", score=3),
            QuestionOption(value=4, label="Exactly true", score=4),
        ],
    ),
]

# Program Pulse (Quick daily check)
PROGRAM_PULSE_QUESTIONS = [
    SurveyQuestion(
        id="pulse_mood",
        text="How are you feeling right now?",
        question_type="emoji_scale",
        options=[
            QuestionOption(value=1, label="Very low", score=1),
            QuestionOption(value=2, label="Low", score=2),
            QuestionOption(value=3, label="Okay", score=3),
            QuestionOption(value=4, label="Good", score=4),
            QuestionOption(value=5, label="Great", score=5),
        ],
    ),
]
