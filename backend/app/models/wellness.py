"""Models for gamified wellness and survey data collection.

This module implements the research data collection platform for correlating
self-reported wellness data with algorithmic predictions from exotic/resilience modules.

Key Components:
    - Survey: Survey definitions (MBI-2, PSS-4, PSQI-1, GSE-4, etc.)
    - SurveyResponse: Individual survey responses with privacy-preserving linkage
    - WellnessAccount: Gamification points, streaks, and achievements
    - HopfieldPosition: User-positioned state on energy landscape visualization

Research Correlation:
    - Burnout Rt -> MBI-2 scores
    - Fire Danger Index -> PSS-4 + MBI-2
    - FRMS Fatigue -> PSQI-1
    - Hopfield Energy -> User-positioned basin depth
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class SurveyType(str, Enum):
    """Types of validated survey instruments."""

    BURNOUT = "burnout"  # MBI-2
    STRESS = "stress"  # PSS-4
    SLEEP = "sleep"  # PSQI-1
    EFFICACY = "efficacy"  # GSE-4
    PULSE = "pulse"  # Quick mood/energy check
    HOPFIELD = "hopfield"  # Energy landscape positioning


class SurveyFrequency(str, Enum):
    """How often surveys can be taken."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    BLOCK = "block"  # Once per academic block
    ANNUAL = "annual"


class AchievementType(str, Enum):
    """Types of wellness achievements/badges."""

    FIRST_CHECKIN = "first_checkin"
    POINTS_100 = "points_100"
    POINTS_500 = "points_500"
    POINTS_1000 = "points_1000"
    WEEKLY_WARRIOR = "weekly_warrior"  # 4-week streak
    CONSISTENCY_KING = "consistency_king"  # 8-week streak
    DATA_HERO = "data_hero"  # All surveys in a block
    RESEARCH_CHAMPION = "research_champion"  # 52-week participation
    FACULTY_MENTOR = "faculty_mentor"  # Faculty with high engagement
    IRON_RESIDENT = "iron_resident"  # 1000 pts lifetime


class Survey(Base):
    """
    Survey instrument definition.

    Stores validated survey instruments like MBI-2, PSS-4, PSQI-1, GSE-4.
    Questions are stored as JSON to allow flexible survey configuration.

    Attributes:
        name: Short name (e.g., "MBI-2", "PSS-4")
        display_name: User-facing name (e.g., "Burnout Assessment")
        survey_type: Category of survey (burnout, stress, sleep, etc.)
        description: Brief description shown to users
        questions_json: JSON array of question definitions
        scoring_json: JSON object with scoring algorithm
        points_value: Points awarded for completion
        frequency: How often survey can be taken
        is_active: Whether survey is currently available
    """

    __tablename__ = "surveys"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Survey identification
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    survey_type = Column(String(50), nullable=False, index=True)

    # Content
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)  # Instructions shown before survey
    questions_json = Column(JSONType, nullable=False)  # Question definitions
    scoring_json = Column(JSONType, nullable=True)  # Scoring algorithm

    # Gamification
    points_value = Column(Integer, default=50, nullable=False)
    estimated_seconds = Column(Integer, default=60)  # Estimated completion time

    # Availability
    frequency = Column(String(20), default="weekly", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Targeting (optional)
    target_roles_json = Column(
        JSONType, default=list
    )  # ["resident", "faculty"] or empty=all

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    responses = relationship("SurveyResponse", back_populates="survey")

    __table_args__ = (
        CheckConstraint(
            "survey_type IN ('burnout', 'stress', 'sleep', 'efficacy', 'pulse', 'hopfield', 'custom')",
            name="check_survey_type",
        ),
        CheckConstraint(
            "frequency IN ('daily', 'weekly', 'biweekly', 'block', 'annual')",
            name="check_survey_frequency",
        ),
        CheckConstraint("points_value >= 0", name="check_points_non_negative"),
    )

    def __repr__(self):
        return f"<Survey(name='{self.name}', type='{self.survey_type}', active={self.is_active})>"


class SurveyResponse(Base):
    """
    Individual survey response with optional person linking.

    Supports privacy-preserving data collection with optional person linkage.
    Uses SET NULL on delete to preserve response history even if person is deleted.

    Temporal scoping allows correlation with:
        - Academic blocks (block_number + academic_year)
        - Rotation assignments
        - Algorithmic predictions at that time

    Versioned with SQLAlchemy-Continuum for audit trail.

    Attributes:
        survey_id: Reference to survey definition
        person_id: Optional link to respondent (SET NULL on delete)
        block_number: Academic block (0-13) for temporal scoping
        academic_year: Academic year (e.g., 2025 for AY 2025-2026)
        response_data: JSON object with {question_id: answer}
        score: Computed score if applicable
        submitted_at: When response was submitted
    """

    __tablename__ = "survey_responses"
    __versioned__ = {}  # Enable audit trail

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Survey reference
    survey_id = Column(
        GUID(),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional person reference (privacy-preserving)
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Temporal scoping for research correlation
    block_number = Column(Integer, nullable=True)  # 0-13
    academic_year = Column(Integer, nullable=True)  # e.g., 2025

    # Response data
    response_data = Column(JSONType, nullable=False)  # {question_id: answer}
    score = Column(Float, nullable=True)  # Computed score if applicable
    score_interpretation = Column(
        String(100), nullable=True
    )  # e.g., "low", "moderate", "high"

    # Metadata
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)

    # Algorithmic correlation (snapshot at submission time)
    algorithm_snapshot_json = Column(JSONType, nullable=True)
    # Example: {"burnout_rt": 1.2, "fire_danger_index": 0.65, "defense_level": 3}

    # Relationships
    survey = relationship("Survey", back_populates="responses")
    person = relationship("Person", backref="survey_responses")

    __table_args__ = (
        CheckConstraint(
            "block_number IS NULL OR (block_number >= 0 AND block_number <= 13)",
            name="check_block_number_range",
        ),
        CheckConstraint(
            "academic_year IS NULL OR (academic_year >= 2000 AND academic_year <= 2100)",
            name="check_academic_year_range",
        ),
        Index(
            "ix_survey_responses_temporal", "survey_id", "block_number", "academic_year"
        ),
    )

    def __repr__(self):
        return f"<SurveyResponse(survey_id={self.survey_id}, person_id={self.person_id}, score={self.score})>"


class WellnessAccount(Base):
    """
    Gamification account for wellness engagement.

    Tracks points, streaks, and achievements for each participant.
    Implements a closed-economy points system similar to KarmaMechanism.

    Points Economy:
        - MBI-2 completion: 50 pts
        - PSS-4 completion: 50 pts
        - Sleep survey: 25 pts
        - Quick pulse: 10 pts
        - Weekly streak bonus: 50 pts
        - Block completion: 200 pts

    Achievements unlock based on engagement milestones.

    Attributes:
        person_id: Unique link to person (one account per person)
        points_balance: Current available points
        points_lifetime: Total points earned ever
        current_streak_weeks: Consecutive weeks with activity
        longest_streak_weeks: Personal record for streak
        achievements_json: List of unlocked achievement codes
        leaderboard_opt_in: Whether to show on anonymous leaderboard
        display_name: Anonymous display name for leaderboard
    """

    __tablename__ = "wellness_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Person link (one-to-one)
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Points
    points_balance = Column(Integer, default=0, nullable=False)
    points_lifetime = Column(Integer, default=0, nullable=False)
    points_spent = Column(
        Integer, default=0, nullable=False
    )  # Future: redeem for perks

    # Streaks
    current_streak_weeks = Column(Integer, default=0, nullable=False)
    longest_streak_weeks = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(Date, nullable=True)
    streak_start_date = Column(Date, nullable=True)

    # Achievements
    achievements_json = Column(
        JSONType, default=list
    )  # ["first_checkin", "weekly_warrior"]
    achievements_earned_at_json = Column(
        JSONType, default=dict
    )  # {"first_checkin": "2026-01-15"}

    # Leaderboard
    leaderboard_opt_in = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(50), nullable=True)  # Anonymous display name

    # Consent tracking
    research_consent = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime, nullable=True)
    consent_version = Column(String(20), nullable=True)  # e.g., "1.0"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    person = relationship("Person", backref="wellness_account", uselist=False)
    point_transactions = relationship(
        "WellnessPointTransaction", back_populates="account"
    )

    __table_args__ = (
        CheckConstraint(
            "points_balance >= 0", name="check_wellness_points_non_negative"
        ),
        CheckConstraint(
            "points_lifetime >= 0", name="check_wellness_lifetime_non_negative"
        ),
        CheckConstraint("current_streak_weeks >= 0", name="check_streak_non_negative"),
    )

    def __repr__(self):
        return f"<WellnessAccount(person_id={self.person_id}, points={self.points_balance}, streak={self.current_streak_weeks})>"

    def add_points(self, points: int, source: str) -> None:
        """Add points to the account.

        Args:
            points: Number of points to add (must be positive)
            source: Description of point source (e.g., "MBI-2 completion")
        """
        if points < 0:
            raise ValueError("Points must be non-negative")
        self.points_balance += points
        self.points_lifetime += points
        self.last_activity_date = date.today()

    def has_achievement(self, achievement: str) -> bool:
        """Check if account has a specific achievement."""
        return achievement in (self.achievements_json or [])

    def add_achievement(self, achievement: str) -> bool:
        """Add an achievement if not already earned.

        Returns:
            bool: True if newly earned, False if already had it
        """
        if self.has_achievement(achievement):
            return False

        if self.achievements_json is None:
            self.achievements_json = []
        self.achievements_json = self.achievements_json + [achievement]

        if self.achievements_earned_at_json is None:
            self.achievements_earned_at_json = {}
        self.achievements_earned_at_json = {
            **self.achievements_earned_at_json,
            achievement: datetime.utcnow().isoformat(),
        }
        return True


class WellnessPointTransaction(Base):
    """
    Ledger of point transactions for wellness accounts.

    Provides audit trail and transparency for all point changes.
    Similar to karma mechanism's transaction tracking.

    Attributes:
        account_id: Reference to wellness account
        points: Point change (positive for credit, negative for debit)
        transaction_type: Type of transaction (survey, streak, achievement, etc.)
        source: Human-readable description
        survey_response_id: Optional link to survey response that triggered this
    """

    __tablename__ = "wellness_point_transactions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Account reference
    account_id = Column(
        GUID(),
        ForeignKey("wellness_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction details
    points = Column(Integer, nullable=False)  # Positive = credit, negative = debit
    balance_after = Column(Integer, nullable=False)  # Balance after this transaction
    transaction_type = Column(String(50), nullable=False)
    source = Column(String(200), nullable=False)  # Human-readable description

    # Optional references
    survey_response_id = Column(
        GUID(),
        ForeignKey("survey_responses.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    account = relationship("WellnessAccount", back_populates="point_transactions")

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('survey', 'streak', 'achievement', 'block_bonus', 'admin', 'redemption')",
            name="check_transaction_type",
        ),
    )

    def __repr__(self):
        return f"<WellnessPointTransaction(account_id={self.account_id}, points={self.points}, type='{self.transaction_type}')>"


class HopfieldPosition(Base):
    """
    User-positioned state on Hopfield energy landscape.

    Captures user perception of program stability via interactive
    3D visualization where users drag a ball to show where they
    perceive the program currently is on the energy landscape.

    Research Correlation:
        - Compare user-positioned basin depth to computed Hopfield energy
        - Track position changes over time
        - Aggregate positions for program-wide perception

    Attributes:
        person_id: Respondent
        x_position: X coordinate (0-1 normalized)
        y_position: Y coordinate (0-1 normalized)
        z_position: Optional Z coordinate for 3D
        basin_depth: Computed basin depth at position
        energy_value: Computed energy at position
        block_number: Academic block for temporal scoping
        academic_year: Academic year for temporal scoping
    """

    __tablename__ = "hopfield_positions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Person reference
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Position in energy landscape (normalized 0-1)
    x_position = Column(Float, nullable=False)
    y_position = Column(Float, nullable=False)
    z_position = Column(Float, nullable=True)  # Optional 3rd dimension

    # Computed metrics at position (from Hopfield MCP tools)
    basin_depth = Column(Float, nullable=True)
    energy_value = Column(Float, nullable=True)
    stability_score = Column(Float, nullable=True)  # 0-1

    # Attractor information
    nearest_attractor_id = Column(String(100), nullable=True)
    nearest_attractor_type = Column(
        String(50), nullable=True
    )  # global_minimum, local_minimum, etc.
    hamming_distance = Column(Integer, nullable=True)  # Distance to nearest attractor

    # User's qualitative assessment
    confidence = Column(
        Integer, nullable=True
    )  # 1-5 how confident they are in positioning
    notes = Column(Text, nullable=True)  # Optional user notes

    # Temporal scoping
    block_number = Column(Integer, nullable=True)  # 0-13
    academic_year = Column(Integer, nullable=True)  # e.g., 2025

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    person = relationship("Person", backref="hopfield_positions")

    __table_args__ = (
        CheckConstraint(
            "x_position >= 0 AND x_position <= 1",
            name="check_x_position_range",
        ),
        CheckConstraint(
            "y_position >= 0 AND y_position <= 1",
            name="check_y_position_range",
        ),
        CheckConstraint(
            "z_position IS NULL OR (z_position >= 0 AND z_position <= 1)",
            name="check_z_position_range",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 1 AND confidence <= 5)",
            name="check_confidence_range",
        ),
        CheckConstraint(
            "block_number IS NULL OR (block_number >= 0 AND block_number <= 13)",
            name="check_hopfield_block_range",
        ),
        Index(
            "ix_hopfield_positions_temporal",
            "person_id",
            "block_number",
            "academic_year",
        ),
    )

    def __repr__(self):
        return f"<HopfieldPosition(person_id={self.person_id}, x={self.x_position}, y={self.y_position}, energy={self.energy_value})>"


class WellnessLeaderboardSnapshot(Base):
    """
    Periodic snapshot of leaderboard rankings.

    Captures leaderboard state for historical analysis and
    to avoid real-time computation costs.

    Attributes:
        snapshot_date: Date of snapshot
        rankings_json: List of {display_name, points, rank, streak}
        total_participants: Number of opt-in participants
        average_points: Average points across participants
    """

    __tablename__ = "wellness_leaderboard_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Snapshot timing
    snapshot_date = Column(Date, nullable=False, index=True)
    snapshot_type = Column(String(20), default="weekly")  # daily, weekly, block

    # Ranking data (anonymized)
    rankings_json = Column(JSONType, nullable=False)
    # [{"rank": 1, "display_name": "ResidentAlpha", "points": 1250, "streak": 8}, ...]

    # Aggregate stats
    total_participants = Column(Integer, nullable=False)
    average_points = Column(Float, nullable=True)
    median_points = Column(Float, nullable=True)
    top_10_cutoff = Column(Integer, nullable=True)  # Minimum points to be in top 10

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "snapshot_type IN ('daily', 'weekly', 'block')",
            name="check_snapshot_type",
        ),
        UniqueConstraint(
            "snapshot_date", "snapshot_type", name="uq_leaderboard_snapshot"
        ),
    )

    def __repr__(self):
        return f"<WellnessLeaderboardSnapshot(date={self.snapshot_date}, participants={self.total_participants})>"


class SurveyAvailability(Base):
    """
    Tracks when surveys become available for each person.

    Manages survey cooldowns based on frequency settings.
    Prevents over-surveying while encouraging consistent participation.

    Attributes:
        person_id: The person
        survey_id: The survey
        last_completed_at: When they last completed this survey
        next_available_at: When they can take it again
        completions_this_block: Count for block-level tracking
    """

    __tablename__ = "survey_availability"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    survey_id = Column(
        GUID(),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Completion tracking
    last_completed_at = Column(DateTime, nullable=True)
    next_available_at = Column(DateTime, nullable=True)
    completions_this_block = Column(Integer, default=0)
    completions_this_year = Column(Integer, default=0)

    # Current block tracking
    current_block_number = Column(Integer, nullable=True)
    current_academic_year = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "person_id", "survey_id", name="uq_survey_availability_person_survey"
        ),
        Index("ix_survey_availability_next", "next_available_at"),
    )

    def __repr__(self):
        return f"<SurveyAvailability(person_id={self.person_id}, survey_id={self.survey_id}, next={self.next_available_at})>"
