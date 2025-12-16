"""Resilience system database models.

Models for tracking:

Tier 1 (Critical):
- System health checks
- Crisis events and responses
- Load shedding (sacrifice) decisions
- Fallback schedule activations

Tier 2 (Strategic):
- Homeostasis feedback loop states
- Allostatic load tracking
- Scheduling zones for blast radius isolation
- Zone incidents and borrowing
- Equilibrium shifts and stress compensation

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

    ***REMOVED*** Overall status
    overall_status = Column(String(20), nullable=False)

    ***REMOVED*** Utilization metrics
    utilization_rate = Column(Float, nullable=False)
    utilization_level = Column(String(20), nullable=False)  ***REMOVED*** GREEN, YELLOW, ORANGE, RED, BLACK
    buffer_remaining = Column(Float)

    ***REMOVED*** Defense status
    defense_level = Column(String(30))  ***REMOVED*** PREVENTION, CONTROL, SAFETY_SYSTEMS, CONTAINMENT, EMERGENCY
    load_shedding_level = Column(String(20))  ***REMOVED*** NORMAL, YELLOW, ORANGE, RED, BLACK, CRITICAL

    ***REMOVED*** Contingency compliance
    n1_pass = Column(Boolean, default=True)
    n2_pass = Column(Boolean, default=True)
    phase_transition_risk = Column(String(20))  ***REMOVED*** low, medium, high, critical

    ***REMOVED*** Active responses
    active_fallbacks = Column(StringArrayType())
    crisis_mode = Column(Boolean, default=False)

    ***REMOVED*** Recommendations captured
    immediate_actions = Column(JSONType())
    watch_items = Column(JSONType())

    ***REMOVED*** Full metrics snapshot for deep analysis
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

    ***REMOVED*** Event context
    severity = Column(String(20))  ***REMOVED*** minor, moderate, severe, critical
    reason = Column(String(500))
    triggered_by = Column(String(100))  ***REMOVED*** 'system', 'user:<id>', 'scheduled_task'

    ***REMOVED*** State before/after
    previous_state = Column(JSONType())
    new_state = Column(JSONType())

    ***REMOVED*** Related entities
    related_health_check_id = Column(GUID(), ForeignKey("resilience_health_checks.id"))

    ***REMOVED*** Additional context
    metadata = Column(JSONType())

    ***REMOVED*** Relationships
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

    ***REMOVED*** Decision details
    from_level = Column(String(20), nullable=False)  ***REMOVED*** Previous load shedding level
    to_level = Column(String(20), nullable=False)  ***REMOVED*** New load shedding level
    reason = Column(String(500), nullable=False)

    ***REMOVED*** What was affected
    activities_suspended = Column(StringArrayType())
    activities_protected = Column(StringArrayType())

    ***REMOVED*** Authorization
    approved_by = Column(String(100))  ***REMOVED*** User ID or 'auto' for automatic
    approval_method = Column(String(50))  ***REMOVED*** 'automatic', 'manual', 'emergency_override'

    ***REMOVED*** Context
    utilization_at_decision = Column(Float)
    coverage_at_decision = Column(Float)
    related_event_id = Column(GUID(), ForeignKey("resilience_events.id"))

    ***REMOVED*** Recovery tracking
    recovered_at = Column(DateTime)
    recovery_reason = Column(String(500))

    ***REMOVED*** Relationships
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

    ***REMOVED*** Fallback details
    scenario = Column(String(50), nullable=False)  ***REMOVED*** e.g., 'single_faculty_loss', 'pcs_season'
    scenario_description = Column(String(500))

    ***REMOVED*** Authorization
    activated_by = Column(String(100))  ***REMOVED*** User ID or 'auto'
    activation_reason = Column(String(500))

    ***REMOVED*** Schedule details
    assignments_count = Column(Integer)
    coverage_rate = Column(Float)
    services_reduced = Column(StringArrayType())
    assumptions = Column(StringArrayType())

    ***REMOVED*** Deactivation
    deactivated_at = Column(DateTime)
    deactivated_by = Column(String(100))
    deactivation_reason = Column(String(500))

    ***REMOVED*** Related event
    related_event_id = Column(GUID(), ForeignKey("resilience_events.id"))

    ***REMOVED*** Relationships
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

    ***REMOVED*** Analysis scope
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    faculty_count = Column(Integer)
    block_count = Column(Integer)

    ***REMOVED*** Results
    n1_pass = Column(Boolean, nullable=False)
    n2_pass = Column(Boolean, nullable=False)
    phase_transition_risk = Column(String(20))

    ***REMOVED*** Vulnerability details
    n1_vulnerabilities = Column(JSONType())  ***REMOVED*** List of single-loss vulnerabilities
    n2_fatal_pairs = Column(JSONType())  ***REMOVED*** List of fatal faculty pairs
    most_critical_faculty = Column(JSONType())  ***REMOVED*** IDs with highest centrality

    ***REMOVED*** Recommendations generated
    recommended_actions = Column(StringArrayType())

    ***REMOVED*** Related health check
    related_health_check_id = Column(GUID(), ForeignKey("resilience_health_checks.id"))

    ***REMOVED*** Relationships
    health_check = relationship("ResilienceHealthCheck", backref="vulnerability_records")

    def __repr__(self):
        return f"<VulnerabilityRecord(n1={self.n1_pass}, n2={self.n2_pass})>"


***REMOVED*** =============================================================================
***REMOVED*** Tier 2: Strategic Implementation Models
***REMOVED*** =============================================================================


class AllostasisState(str, enum.Enum):
    """Allostatic state of a faculty member or system."""
    HOMEOSTASIS = "homeostasis"  ***REMOVED*** Stable, within normal operating range
    ALLOSTASIS = "allostasis"    ***REMOVED*** Actively compensating for stress
    ALLOSTATIC_LOAD = "allostatic_load"  ***REMOVED*** Chronic compensation, accumulating wear
    ALLOSTATIC_OVERLOAD = "allostatic_overload"  ***REMOVED*** System failing to compensate


class ZoneStatus(str, enum.Enum):
    """Health status of a scheduling zone."""
    GREEN = "green"         ***REMOVED*** Fully operational
    YELLOW = "yellow"       ***REMOVED*** Operational at minimum
    ORANGE = "orange"       ***REMOVED*** Degraded, using backup
    RED = "red"             ***REMOVED*** Critical, needs support
    BLACK = "black"         ***REMOVED*** Failed, services suspended


class ContainmentLevel(str, enum.Enum):
    """Level of failure containment."""
    NONE = "none"           ***REMOVED*** No containment active
    SOFT = "soft"           ***REMOVED*** Advisory logging
    MODERATE = "moderate"   ***REMOVED*** Require approval
    STRICT = "strict"       ***REMOVED*** No cross-zone borrowing
    LOCKDOWN = "lockdown"   ***REMOVED*** Zone completely isolated


class EquilibriumState(str, enum.Enum):
    """State of system equilibrium."""
    STABLE = "stable"           ***REMOVED*** At sustainable equilibrium
    COMPENSATING = "compensating"  ***REMOVED*** Shifting to new equilibrium
    STRESSED = "stressed"       ***REMOVED*** Strained but holding
    UNSUSTAINABLE = "unsustainable"  ***REMOVED*** Cannot reach stable
    CRITICAL = "critical"       ***REMOVED*** Failing to equilibrate


class FeedbackLoopState(Base):
    """
    Tracks state of homeostasis feedback loops.

    Feedback loops monitor metrics and trigger corrections
    when deviation from setpoint exceeds tolerance.
    """
    __tablename__ = "feedback_loop_states"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    loop_name = Column(String(100), nullable=False)
    setpoint_name = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Setpoint configuration
    target_value = Column(Float, nullable=False)
    tolerance = Column(Float, nullable=False)
    is_critical = Column(Boolean, default=False)

    ***REMOVED*** Current state
    current_value = Column(Float)
    deviation = Column(Float)
    deviation_severity = Column(String(20))  ***REMOVED*** none, minor, moderate, major, critical
    consecutive_deviations = Column(Integer, default=0)

    ***REMOVED*** Trend analysis
    trend_direction = Column(String(20))  ***REMOVED*** stable, increasing, decreasing
    is_improving = Column(Boolean)

    ***REMOVED*** Action tracking
    correction_triggered = Column(Boolean, default=False)
    correction_type = Column(String(50))
    correction_effective = Column(Boolean)

    def __repr__(self):
        return f"<FeedbackLoopState(loop='{self.loop_name}', deviation={self.deviation_severity})>"


class AllostasisRecord(Base):
    """
    Tracks allostatic load for faculty members and the system.

    Allostatic load is the cumulative cost of chronic stress adaptation.
    High load indicates burnout risk.
    """
    __tablename__ = "allostasis_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    entity_id = Column(GUID(), nullable=False)  ***REMOVED*** ID or system UUID
    entity_type = Column(String(20), nullable=False)  ***REMOVED*** "faculty" or "system"
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Stress factors
    consecutive_weekend_calls = Column(Integer, default=0)
    nights_past_month = Column(Integer, default=0)
    schedule_changes_absorbed = Column(Integer, default=0)
    holidays_worked_this_year = Column(Integer, default=0)
    overtime_hours_month = Column(Float, default=0.0)
    coverage_gap_responses = Column(Integer, default=0)
    cross_coverage_events = Column(Integer, default=0)

    ***REMOVED*** Calculated scores
    acute_stress_score = Column(Float, default=0.0)
    chronic_stress_score = Column(Float, default=0.0)
    total_allostatic_load = Column(Float, default=0.0)

    ***REMOVED*** State
    allostasis_state = Column(String(30))  ***REMOVED*** AllostasisState enum value
    risk_level = Column(String(20))  ***REMOVED*** low, moderate, high, critical

    def __repr__(self):
        return f"<AllostasisRecord(entity={self.entity_id}, load={self.total_allostatic_load:.1f})>"


class PositiveFeedbackAlert(Base):
    """
    Alerts for detected positive feedback loops.

    Positive feedback loops amplify problems and destabilize systems.
    These records track detection and intervention.
    """
    __tablename__ = "positive_feedback_alerts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Loop pattern
    trigger = Column(String(200))
    amplification = Column(String(200))
    consequence = Column(String(200))

    ***REMOVED*** Detection
    evidence = Column(JSONType())
    confidence = Column(Float)
    severity = Column(String(20))

    ***REMOVED*** Intervention
    intervention_recommended = Column(String(500))
    urgency = Column(String(20))  ***REMOVED*** immediate, soon, monitor

    ***REMOVED*** Resolution
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(500))
    intervention_effective = Column(Boolean)

    def __repr__(self):
        return f"<PositiveFeedbackAlert(name='{self.name}', urgency='{self.urgency}')>"


class SchedulingZoneRecord(Base):
    """
    Configuration and state for scheduling zones.

    Zones provide blast radius isolation - failures in one zone
    cannot propagate to affect others.
    """
    __tablename__ = "scheduling_zones"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50), nullable=False)  ***REMOVED*** inpatient, outpatient, education, etc.
    description = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Services
    services = Column(StringArrayType())

    ***REMOVED*** Capacity requirements
    minimum_coverage = Column(Integer, default=1)
    optimal_coverage = Column(Integer, default=2)
    maximum_coverage = Column(Integer, default=5)

    ***REMOVED*** Current status
    status = Column(String(20), default="green")  ***REMOVED*** ZoneStatus enum
    containment_level = Column(String(20), default="none")  ***REMOVED*** ContainmentLevel enum
    last_status_change = Column(DateTime)

    ***REMOVED*** Borrowing configuration
    borrowing_limit = Column(Integer, default=2)
    lending_limit = Column(Integer, default=1)
    priority = Column(Integer, default=5)

    ***REMOVED*** Relationships can_borrow_from and can_lend_to stored as arrays
    can_borrow_from_zones = Column(StringArrayType())
    can_lend_to_zones = Column(StringArrayType())

    ***REMOVED*** Metrics
    total_borrowing_requests = Column(Integer, default=0)
    total_lending_events = Column(Integer, default=0)

    ***REMOVED*** Active status
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<SchedulingZoneRecord(name='{self.name}', status='{self.status}')>"


class ZoneFacultyAssignmentRecord(Base):
    """
    Records faculty assignments to zones.
    """
    __tablename__ = "zone_faculty_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    zone_id = Column(GUID(), ForeignKey("scheduling_zones.id"), nullable=False)
    faculty_id = Column(GUID(), nullable=False)
    faculty_name = Column(String(200))
    role = Column(String(20), nullable=False)  ***REMOVED*** primary, secondary, backup
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_available = Column(Boolean, default=True)
    removed_at = Column(DateTime)

    ***REMOVED*** Relationship
    zone = relationship("SchedulingZoneRecord", backref="faculty_assignments")

    def __repr__(self):
        return f"<ZoneFacultyAssignment(zone_id={self.zone_id}, role='{self.role}')>"


class ZoneBorrowingRecord(Base):
    """
    Records cross-zone faculty borrowing requests.
    """
    __tablename__ = "zone_borrowing_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    requesting_zone_id = Column(GUID(), ForeignKey("scheduling_zones.id"), nullable=False)
    lending_zone_id = Column(GUID(), ForeignKey("scheduling_zones.id"), nullable=False)
    faculty_id = Column(GUID(), nullable=False)

    ***REMOVED*** Request details
    priority = Column(String(20), nullable=False)  ***REMOVED*** critical, high, medium, low
    reason = Column(String(500))
    duration_hours = Column(Integer)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Approval
    status = Column(String(20), default="pending")  ***REMOVED*** pending, approved, denied, completed
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    denial_reason = Column(String(500))

    ***REMOVED*** Execution
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    was_effective = Column(Boolean)

    ***REMOVED*** Relationships
    requesting_zone = relationship("SchedulingZoneRecord", foreign_keys=[requesting_zone_id])
    lending_zone = relationship("SchedulingZoneRecord", foreign_keys=[lending_zone_id])

    def __repr__(self):
        return f"<ZoneBorrowingRecord(status='{self.status}', priority='{self.priority}')>"


class ZoneIncidentRecord(Base):
    """
    Records incidents affecting scheduling zones.
    """
    __tablename__ = "zone_incidents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    zone_id = Column(GUID(), ForeignKey("scheduling_zones.id"), nullable=False)
    incident_type = Column(String(50), nullable=False)  ***REMOVED*** faculty_loss, demand_surge, etc.
    description = Column(String(500))
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    severity = Column(String(20), nullable=False)  ***REMOVED*** minor, moderate, severe, critical

    ***REMOVED*** Impact
    faculty_affected = Column(StringArrayType())
    capacity_lost = Column(Float, default=0.0)
    services_affected = Column(StringArrayType())

    ***REMOVED*** Resolution
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(500))
    containment_successful = Column(Boolean, default=True)

    ***REMOVED*** Relationship
    zone = relationship("SchedulingZoneRecord", backref="incidents")

    def __repr__(self):
        return f"<ZoneIncidentRecord(type='{self.incident_type}', severity='{self.severity}')>"


class EquilibriumShiftRecord(Base):
    """
    Records equilibrium shifts per Le Chatelier's principle.

    Tracks how the system responds to stress and compensates.
    """
    __tablename__ = "equilibrium_shifts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Original state
    original_capacity = Column(Float, nullable=False)
    original_demand = Column(Float, nullable=False)
    original_coverage_rate = Column(Float, nullable=False)

    ***REMOVED*** Stress applied
    stress_types = Column(StringArrayType())
    total_capacity_impact = Column(Float)
    total_demand_impact = Column(Float)

    ***REMOVED*** Compensation
    compensation_types = Column(StringArrayType())
    total_compensation = Column(Float)
    compensation_efficiency = Column(Float)

    ***REMOVED*** New equilibrium
    new_capacity = Column(Float, nullable=False)
    new_demand = Column(Float, nullable=False)
    new_coverage_rate = Column(Float, nullable=False)
    sustainable_capacity = Column(Float)

    ***REMOVED*** Costs
    compensation_debt = Column(Float, default=0.0)
    daily_debt_rate = Column(Float, default=0.0)
    burnout_risk = Column(Float, default=0.0)
    days_until_exhaustion = Column(Integer)

    ***REMOVED*** State
    equilibrium_state = Column(String(30))  ***REMOVED*** EquilibriumState enum
    is_sustainable = Column(Boolean)

    def __repr__(self):
        return f"<EquilibriumShiftRecord(state='{self.equilibrium_state}', sustainable={self.is_sustainable})>"


class SystemStressRecord(Base):
    """
    Records stresses applied to the system.
    """
    __tablename__ = "system_stress_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    stress_type = Column(String(50), nullable=False)
    description = Column(String(500))
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Quantification
    magnitude = Column(Float, nullable=False)
    duration_days = Column(Integer)
    is_acute = Column(Boolean, default=True)
    is_reversible = Column(Boolean, default=True)

    ***REMOVED*** Impact
    capacity_impact = Column(Float)
    demand_impact = Column(Float)

    ***REMOVED*** Status
    is_active = Column(Boolean, default=True)
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(500))

    def __repr__(self):
        return f"<SystemStressRecord(type='{self.stress_type}', active={self.is_active})>"


class CompensationRecord(Base):
    """
    Records compensation responses to system stress.
    """
    __tablename__ = "compensation_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    stress_id = Column(GUID(), ForeignKey("system_stress_records.id"), nullable=False)
    compensation_type = Column(String(50), nullable=False)
    description = Column(String(500))
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ***REMOVED*** Quantification
    compensation_magnitude = Column(Float, nullable=False)
    effectiveness = Column(Float, default=0.8)

    ***REMOVED*** Costs
    immediate_cost = Column(Float, default=0.0)
    hidden_cost = Column(Float, default=0.0)
    sustainability_days = Column(Integer)

    ***REMOVED*** Status
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime)
    end_reason = Column(String(200))

    ***REMOVED*** Relationship
    stress = relationship("SystemStressRecord", backref="compensations")

    def __repr__(self):
        return f"<CompensationRecord(type='{self.compensation_type}', active={self.is_active})>"
