"""Resilience system database models.

Models for tracking:
- System health checks
- Crisis events and responses
- Load shedding (sacrifice) decisions
- Fallback schedule activations

These provide the audit trail and historical data needed for
accountability and post-incident review.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base
from app.db.types import GUID, JSONType, StringArrayType


class ResilienceEventType(str, enum.Enum):
    """Types of resilience events."""
    HEALTH_CHECK = "health_check"
    CRISIS_ACTIVATED = "crisis_activated"
    CRISIS_DEACTIVATED = "crisis_deactivated"
    FALLBACK_ACTIVATED = "fallback_activated"
    FALLBACK_DEACTIVATED = "fallback_deactivated"
    LOAD_SHEDDING_ACTIVATED = "load_shedding_activated"
    LOAD_SHEDDING_DEACTIVATED = "load_shedding_deactivated"
    DEFENSE_LEVEL_CHANGED = "defense_level_changed"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    N1_VIOLATION = "n1_violation"
    N2_VIOLATION = "n2_violation"


class OverallStatus(str, enum.Enum):
    """Overall system status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ResilienceHealthCheck(Base):
    """
    Stores periodic system health check results.

    Used for:
    - Historical trend analysis
    - Alerting on degradation
    - Post-incident review
    """
    __tablename__ = "resilience_health_checks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Overall status
    overall_status = Column(String(20), nullable=False)

    # Utilization metrics
    utilization_rate = Column(Float, nullable=False)
    utilization_level = Column(String(20), nullable=False)  # GREEN, YELLOW, ORANGE, RED, BLACK
    buffer_remaining = Column(Float)

    # Defense status
    defense_level = Column(String(30))  # PREVENTION, CONTROL, SAFETY_SYSTEMS, CONTAINMENT, EMERGENCY
    load_shedding_level = Column(String(20))  # NORMAL, YELLOW, ORANGE, RED, BLACK, CRITICAL

    # Contingency compliance
    n1_pass = Column(Boolean, default=True)
    n2_pass = Column(Boolean, default=True)
    phase_transition_risk = Column(String(20))  # low, medium, high, critical

    # Active responses
    active_fallbacks = Column(StringArrayType())
    crisis_mode = Column(Boolean, default=False)

    # Recommendations captured
    immediate_actions = Column(JSONType())
    watch_items = Column(JSONType())

    # Full metrics snapshot for deep analysis
    metrics_snapshot = Column(JSONType())

    def __repr__(self):
        return f"<ResilienceHealthCheck(status='{self.overall_status}', util={self.utilization_rate:.0%})>"


class ResilienceEvent(Base):
    """
    Audit log for resilience system events.

    Captures all significant state changes for accountability
    and post-incident review.
    """
    __tablename__ = "resilience_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(50), nullable=False)

    # Event context
    severity = Column(String(20))  # minor, moderate, severe, critical
    reason = Column(String(500))
    triggered_by = Column(String(100))  # 'system', 'user:<id>', 'scheduled_task'

    # State before/after
    previous_state = Column(JSONType())
    new_state = Column(JSONType())

    # Related entities
    related_health_check_id = Column(GUID(), ForeignKey("resilience_health_checks.id"))

    # Additional context
    metadata = Column(JSONType())

    # Relationships
    health_check = relationship("ResilienceHealthCheck", backref="events")

    def __repr__(self):
        return f"<ResilienceEvent(type='{self.event_type}', severity='{self.severity}')>"


class SacrificeDecision(Base):
    """
    Audit trail for load shedding (sacrifice) decisions.

    Records when activities are suspended and why, for:
    - Accountability
    - Pattern analysis
    - Stakeholder communication
    """
    __tablename__ = "sacrifice_decisions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Decision details
    from_level = Column(String(20), nullable=False)  # Previous load shedding level
    to_level = Column(String(20), nullable=False)  # New load shedding level
    reason = Column(String(500), nullable=False)

    # What was affected
    activities_suspended = Column(StringArrayType())
    activities_protected = Column(StringArrayType())

    # Authorization
    approved_by = Column(String(100))  # User ID or 'auto' for automatic
    approval_method = Column(String(50))  # 'automatic', 'manual', 'emergency_override'

    # Context
    utilization_at_decision = Column(Float)
    coverage_at_decision = Column(Float)
    related_event_id = Column(GUID(), ForeignKey("resilience_events.id"))

    # Recovery tracking
    recovered_at = Column(DateTime)
    recovery_reason = Column(String(500))

    # Relationships
    event = relationship("ResilienceEvent", backref="sacrifice_decisions")

    def __repr__(self):
        return f"<SacrificeDecision(from='{self.from_level}', to='{self.to_level}')>"

    @property
    def is_active(self) -> bool:
        """Check if this decision is still active (not recovered)."""
        return self.recovered_at is None

    @property
    def duration_minutes(self) -> int | None:
        """Get duration of the sacrifice period in minutes."""
        if self.recovered_at is None:
            return None
        delta = self.recovered_at - self.timestamp
        return int(delta.total_seconds() / 60)


class FallbackActivation(Base):
    """
    Tracks fallback schedule activations.

    Records when pre-computed fallback schedules are activated,
    providing audit trail and effectiveness tracking.
    """
    __tablename__ = "fallback_activations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    activated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Fallback details
    scenario = Column(String(50), nullable=False)  # e.g., 'single_faculty_loss', 'pcs_season'
    scenario_description = Column(String(500))

    # Authorization
    activated_by = Column(String(100))  # User ID or 'auto'
    activation_reason = Column(String(500))

    # Schedule details
    assignments_count = Column(Integer)
    coverage_rate = Column(Float)
    services_reduced = Column(StringArrayType())
    assumptions = Column(StringArrayType())

    # Deactivation
    deactivated_at = Column(DateTime)
    deactivated_by = Column(String(100))
    deactivation_reason = Column(String(500))

    # Related event
    related_event_id = Column(GUID(), ForeignKey("resilience_events.id"))

    # Relationships
    event = relationship("ResilienceEvent", backref="fallback_activations")

    def __repr__(self):
        return f"<FallbackActivation(scenario='{self.scenario}', active={self.is_active})>"

    @property
    def is_active(self) -> bool:
        """Check if this fallback is currently active."""
        return self.deactivated_at is None

    @property
    def duration_minutes(self) -> int | None:
        """Get duration of the fallback activation in minutes."""
        if self.deactivated_at is None:
            return None
        delta = self.deactivated_at - self.activated_at
        return int(delta.total_seconds() / 60)


class VulnerabilityRecord(Base):
    """
    Stores N-1/N-2 vulnerability analysis results.

    Captures point-in-time vulnerability assessments for
    trend tracking and risk monitoring.
    """
    __tablename__ = "vulnerability_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Analysis scope
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    faculty_count = Column(Integer)
    block_count = Column(Integer)

    # Results
    n1_pass = Column(Boolean, nullable=False)
    n2_pass = Column(Boolean, nullable=False)
    phase_transition_risk = Column(String(20))

    # Vulnerability details
    n1_vulnerabilities = Column(JSONType())  # List of single-loss vulnerabilities
    n2_fatal_pairs = Column(JSONType())  # List of fatal faculty pairs
    most_critical_faculty = Column(JSONType())  ***REMOVED*** IDs with highest centrality

    # Recommendations generated
    recommended_actions = Column(StringArrayType())

    # Related health check
    related_health_check_id = Column(GUID(), ForeignKey("resilience_health_checks.id"))

    # Relationships
    health_check = relationship("ResilienceHealthCheck", backref="vulnerability_records")

    def __repr__(self):
        return f"<VulnerabilityRecord(n1={self.n1_pass}, n2={self.n2_pass})>"
