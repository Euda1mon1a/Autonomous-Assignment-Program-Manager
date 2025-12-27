"""Database models for Fatigue Risk Management System (FRMS).

Stores fatigue assessments, predictions, hazard alerts, and interventions
for audit trail and historical analysis.

Models:
- FatigueAssessment: Point-in-time fatigue measurements
- FatigueHazardAlert: Detected hazards and required mitigations
- FatigueIntervention: Actions taken in response to hazards
- SleepDebtHistory: Daily sleep debt tracking
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType, StringArrayType


class SamnPerelliLevel(enum.IntEnum):
    """Samn-Perelli 7-level fatigue scale."""

    FULLY_ALERT = 1
    VERY_LIVELY = 2
    OKAY = 3
    A_LITTLE_TIRED = 4
    MODERATELY_TIRED = 5
    EXTREMELY_TIRED = 6
    EXHAUSTED = 7


class HazardLevelEnum(str, enum.Enum):
    """Fatigue hazard severity levels."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"


class CircadianPhaseEnum(str, enum.Enum):
    """Circadian rhythm phases."""

    NADIR = "nadir"
    EARLY_MORNING = "early_morning"
    MORNING_PEAK = "morning_peak"
    POST_LUNCH = "post_lunch"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class InterventionTypeEnum(str, enum.Enum):
    """Types of fatigue interventions."""

    MONITORING = "monitoring"
    BUDDY_SYSTEM = "buddy_system"
    DUTY_RESTRICTION = "duty_restriction"
    SHIFT_SWAP = "shift_swap"
    EARLY_RELEASE = "early_release"
    SCHEDULE_MODIFICATION = "schedule_modification"
    MANDATORY_REST = "mandatory_rest"
    IMMEDIATE_RELIEF = "immediate_relief"


class InterventionOutcome(str, enum.Enum):
    """Outcome of fatigue intervention."""

    PENDING = "pending"
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    NOT_APPLICABLE = "not_applicable"


class FatigueAssessment(Base):
    """
    Point-in-time fatigue assessment for a resident.

    Captures both objective metrics and subjective ratings
    for comprehensive fatigue tracking.
    """

    __tablename__ = "fatigue_assessments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)
    assessed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Samn-Perelli assessment
    samn_perelli_level = Column(Integer, nullable=False)
    is_self_reported = Column(Boolean, default=False)

    # Calculated metrics
    alertness_score = Column(Float)  # 0.0-1.0
    sleep_debt_hours = Column(Float)
    hours_awake = Column(Float)
    hours_worked_24h = Column(Float)

    # Circadian context
    circadian_phase = Column(String(30))

    # Work context
    consecutive_duty_days = Column(Integer, default=0)
    consecutive_night_shifts = Column(Integer, default=0)
    prior_sleep_hours = Column(Float)
    prior_sleep_quality = Column(Float)  # 0.0-1.0

    # Duty context
    current_shift_type = Column(String(50))
    current_duty_type = Column(String(50))

    # Derived safety status
    safe_for_duty = Column(Boolean, default=True)
    duty_restrictions = Column(StringArrayType())
    recommended_rest_hours = Column(Float)

    # Notes
    notes = Column(String(1000))
    created_by = Column(String(100))

    # Relationships
    person = relationship("Person", backref="fatigue_assessments")

    # Indexes
    __table_args__ = (
        Index("ix_fatigue_assessments_person_date", "person_id", "assessed_at"),
        Index("ix_fatigue_assessments_level", "samn_perelli_level"),
    )

    def __repr__(self):
        return (
            f"<FatigueAssessment(person={self.person_id}, "
            f"SP-{self.samn_perelli_level}, alert={self.alertness_score:.2f})>"
        )


class FatigueHazardAlert(Base):
    """
    Detected fatigue hazard requiring attention.

    Captures hazard level, triggers, and required mitigations
    for audit trail and intervention tracking.
    """

    __tablename__ = "fatigue_hazard_alerts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Hazard classification
    hazard_level = Column(String(20), nullable=False)
    triggers = Column(StringArrayType())

    # Metrics at detection
    alertness_score = Column(Float)
    sleep_debt_hours = Column(Float)
    hours_awake = Column(Float)
    samn_perelli_level = Column(Integer)

    # ACGME context
    hours_worked_week = Column(Float)
    acgme_risk = Column(Boolean, default=False)

    # Required actions
    required_mitigations = Column(StringArrayType())
    recommended_mitigations = Column(StringArrayType())

    # Escalation tracking
    escalation_time = Column(DateTime)
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime)
    escalated_to_level = Column(String(20))

    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    resolution_notes = Column(String(1000))

    # Related assessment
    assessment_id = Column(GUID(), ForeignKey("fatigue_assessments.id"))

    # Relationships
    person = relationship("Person", backref="fatigue_alerts")
    assessment = relationship("FatigueAssessment", backref="alerts")

    # Indexes
    __table_args__ = (
        Index("ix_fatigue_hazards_person_date", "person_id", "detected_at"),
        Index("ix_fatigue_hazards_level", "hazard_level"),
        Index("ix_fatigue_hazards_unresolved", "resolved", "hazard_level"),
    )

    def __repr__(self):
        return (
            f"<FatigueHazardAlert(person={self.person_id}, "
            f"level={self.hazard_level}, resolved={self.resolved})>"
        )

    @property
    def is_critical(self) -> bool:
        """Check if hazard is critical level."""
        return self.hazard_level in ["red", "black"]


class FatigueIntervention(Base):
    """
    Intervention taken in response to fatigue hazard.

    Tracks what actions were taken and their effectiveness
    for continuous improvement.
    """

    __tablename__ = "fatigue_interventions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)
    alert_id = Column(GUID(), ForeignKey("fatigue_hazard_alerts.id"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Intervention details
    intervention_type = Column(String(50), nullable=False)
    description = Column(String(1000))

    # Authorization
    authorized_by = Column(String(100))
    authorization_method = Column(String(50))  # automatic, manual, emergency

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)

    # Effectiveness
    outcome = Column(String(30))
    outcome_notes = Column(String(1000))

    # Pre/post metrics
    pre_alertness = Column(Float)
    post_alertness = Column(Float)
    alertness_improvement = Column(Float)

    # Related entities
    swap_id = Column(GUID())  # If intervention involved a swap
    schedule_run_id = Column(GUID())  # If schedule was modified

    # Relationships
    person = relationship("Person", backref="fatigue_interventions")
    alert = relationship("FatigueHazardAlert", backref="interventions")

    # Indexes
    __table_args__ = (
        Index("ix_fatigue_interventions_person", "person_id"),
        Index("ix_fatigue_interventions_type", "intervention_type"),
    )

    def __repr__(self):
        return (
            f"<FatigueIntervention(person={self.person_id}, "
            f"type={self.intervention_type}, outcome={self.outcome})>"
        )


class SleepDebtHistory(Base):
    """
    Daily sleep debt tracking for trend analysis.

    Stores end-of-day sleep debt calculations for each resident
    to identify chronic debt accumulation patterns.
    """

    __tablename__ = "sleep_debt_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Sleep data
    reported_sleep_hours = Column(Float)
    effective_sleep_hours = Column(Float)
    sleep_quality_factor = Column(Float)

    # Debt calculation
    daily_debt_change = Column(Float)
    cumulative_debt = Column(Float)
    debt_severity = Column(String(20))

    # Recovery metrics
    recovery_applied = Column(Float, default=0.0)
    consecutive_deficit_days = Column(Integer, default=0)

    # Impairment estimate
    impairment_bac_equivalent = Column(Float)

    # Flags
    chronic_debt = Column(Boolean, default=False)

    # Relationships
    person = relationship("Person", backref="sleep_debt_history")

    # Indexes and constraints
    __table_args__ = (
        Index("ix_sleep_debt_person_date", "person_id", "date"),
        Index("ix_sleep_debt_chronic", "chronic_debt"),
    )

    def __repr__(self):
        return (
            f"<SleepDebtHistory(person={self.person_id}, "
            f"date={self.date.date()}, debt={self.cumulative_debt:.1f}h)>"
        )


class CircadianProfile(Base):
    """
    Individual circadian profile for personalized fatigue modeling.

    Stores individual variations in circadian rhythm to improve
    prediction accuracy for each resident.
    """

    __tablename__ = "circadian_profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Chronotype (morningness-eveningness)
    chronotype = Column(String(20))  # morning, intermediate, evening
    chronotype_score = Column(Float)  # MEQ score if available

    # Natural sleep timing
    natural_sleep_onset = Column(String(10))  # HH:MM
    natural_wake_time = Column(String(10))  # HH:MM
    natural_sleep_duration = Column(Float)

    # Phase shift from night work
    is_night_adapted = Column(Boolean, default=False)
    adaptation_days = Column(Integer, default=0)
    phase_shift_hours = Column(Float, default=0.0)

    # Personal thresholds
    individual_sleep_need = Column(Float, default=7.5)
    fatigue_sensitivity = Column(Float, default=1.0)  # Multiplier

    # Calibration data
    last_calibration = Column(DateTime)
    calibration_data = Column(JSONType())

    # Relationships
    person = relationship("Person", backref="circadian_profile")

    def __repr__(self):
        return (
            f"<CircadianProfile(person={self.person_id}, "
            f"chronotype={self.chronotype})>"
        )
