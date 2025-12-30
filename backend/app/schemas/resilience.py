"""Resilience API schemas.

Tier 1 (Critical):
- Health check and crisis management
- Fallback schedules
- Load shedding
- Vulnerability analysis

Tier 2 (Strategic):
- Homeostasis and feedback loops
- Blast radius zones
- Equilibrium analysis (Le Chatelier)
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class UtilizationLevel(str, Enum):
    """Utilization severity levels (queuing theory)."""

    GREEN = "GREEN"  # < 70% - healthy buffer
    YELLOW = "YELLOW"  # 70-80% - approaching threshold
    ORANGE = "ORANGE"  # 80-90% - degraded operations
    RED = "RED"  # 90-95% - critical, cascade risk
    BLACK = "BLACK"  # > 95% - imminent failure


class DefenseLevel(str, Enum):
    """Defense in depth levels (nuclear safety paradigm)."""

    PREVENTION = "PREVENTION"
    CONTROL = "CONTROL"
    SAFETY_SYSTEMS = "SAFETY_SYSTEMS"
    CONTAINMENT = "CONTAINMENT"
    EMERGENCY = "EMERGENCY"


class LoadSheddingLevel(str, Enum):
    """Load shedding levels (triage)."""

    NORMAL = "NORMAL"  # All activities
    YELLOW = "YELLOW"  # Suspend optional education
    ORANGE = "ORANGE"  # Also suspend admin & research
    RED = "RED"  # Also suspend core education
    BLACK = "BLACK"  # Essentials only
    CRITICAL = "CRITICAL"  # Patient safety only


class OverallStatus(str, Enum):
    """Overall system health status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class FallbackScenario(str, Enum):
    """Pre-computed fallback scenarios."""

    SINGLE_FACULTY_LOSS = "single_faculty_loss"
    DOUBLE_FACULTY_LOSS = "double_faculty_loss"
    PCS_SEASON_50_PERCENT = "pcs_season_50_percent"
    HOLIDAY_SKELETON = "holiday_skeleton"
    PANDEMIC_ESSENTIAL = "pandemic_essential"
    MASS_CASUALTY = "mass_casualty"
    WEATHER_EMERGENCY = "weather_emergency"


class CrisisSeverity(str, Enum):
    """Crisis severity levels."""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


# Request Schemas


class HealthCheckRequest(BaseModel):
    """Request for system health check."""

    start_date: date | None = None
    end_date: date | None = None
    include_contingency: bool = Field(
        default=False, description="Include N-1/N-2 contingency analysis (slower)"
    )


class CrisisActivationRequest(BaseModel):
    """Request to activate crisis response."""

    severity: CrisisSeverity
    reason: str = Field(..., min_length=10, max_length=500)


class CrisisDeactivationRequest(BaseModel):
    """Request to deactivate crisis response."""

    reason: str = Field(..., min_length=10, max_length=500)


class FallbackActivationRequest(BaseModel):
    """Request to activate a fallback schedule."""

    scenario: FallbackScenario
    reason: str = Field(..., min_length=10, max_length=500)


class FallbackDeactivationRequest(BaseModel):
    """Request to deactivate a fallback."""

    scenario: FallbackScenario
    reason: str = Field(..., min_length=10, max_length=500)


class LoadSheddingRequest(BaseModel):
    """Request to change load shedding level."""

    level: LoadSheddingLevel
    reason: str = Field(..., min_length=10, max_length=500)


# Response Schemas


class UtilizationMetrics(BaseModel):
    """Utilization metrics from queuing theory analysis."""

    utilization_rate: float = Field(..., ge=0.0, le=1.0)
    level: UtilizationLevel
    buffer_remaining: float
    wait_time_multiplier: float
    safe_capacity: int
    current_demand: int
    theoretical_capacity: int


class RedundancyStatus(BaseModel):
    """N+2 redundancy status for a service."""

    service: str
    status: str  # N+2, N+1, N+0, BELOW
    available: int
    minimum_required: int
    buffer: int


class VulnerabilitySummary(BaseModel):
    """Summary of N-1/N-2 vulnerability analysis."""

    n1_pass: bool
    n2_pass: bool
    phase_transition_risk: str  # low, medium, high, critical
    critical_faculty_count: int
    fatal_pair_count: int
    recommended_actions: list[str]


class HealthCheckResponse(BaseModel):
    """Response from system health check."""

    timestamp: datetime
    overall_status: OverallStatus

    # Component statuses
    utilization: UtilizationMetrics
    defense_level: DefenseLevel
    redundancy_status: list[RedundancyStatus]
    load_shedding_level: LoadSheddingLevel
    active_fallbacks: list[str]
    crisis_mode: bool

    # Risk indicators
    n1_pass: bool
    n2_pass: bool
    phase_transition_risk: str

    # Recommendations
    immediate_actions: list[str]
    watch_items: list[str]


class CrisisResponse(BaseModel):
    """Response from crisis activation/deactivation."""

    crisis_mode: bool
    severity: CrisisSeverity | None = None
    actions_taken: list[str]
    load_shedding_level: LoadSheddingLevel
    recovery_plan: list[str] | None = None


class FallbackInfo(BaseModel):
    """Information about a fallback schedule."""

    scenario: FallbackScenario
    description: str
    is_active: bool
    is_precomputed: bool
    assignments_count: int | None = None
    coverage_rate: float | None = None
    services_reduced: list[str]
    assumptions: list[str]
    activation_count: int


class FallbackListResponse(BaseModel):
    """List of available fallback schedules."""

    fallbacks: list[FallbackInfo]
    active_count: int


class FallbackActivationResponse(BaseModel):
    """Response from fallback activation."""

    success: bool
    scenario: FallbackScenario
    assignments_count: int
    coverage_rate: float
    services_reduced: list[str]
    message: str


class LoadSheddingStatus(BaseModel):
    """Current load shedding status."""

    level: LoadSheddingLevel
    activities_suspended: list[str]
    activities_protected: list[str]
    capacity_available: float
    capacity_demand: float


class CentralityScore(BaseModel):
    """Faculty centrality score (hub vulnerability)."""

    faculty_id: UUID
    faculty_name: str
    centrality_score: float
    services_covered: int
    unique_coverage_slots: int
    replacement_difficulty: float
    risk_level: str  # low, medium, high, critical


class VulnerabilityReportResponse(BaseModel):
    """Full N-1/N-2 vulnerability report."""

    analyzed_at: datetime
    period_start: date
    period_end: date

    # Summary
    n1_pass: bool
    n2_pass: bool
    phase_transition_risk: str

    # Details
    n1_vulnerabilities: list[dict]
    n2_fatal_pairs: list[dict]
    most_critical_faculty: list[CentralityScore]

    # Recommendations
    recommended_actions: list[str]


class ComprehensiveReportResponse(BaseModel):
    """Comprehensive resilience report."""

    generated_at: datetime
    overall_status: OverallStatus

    summary: dict
    immediate_actions: list[str]
    watch_items: list[str]

    components: dict


class HealthCheckHistoryItem(BaseModel):
    """Historical health check record."""

    id: UUID
    timestamp: datetime
    overall_status: OverallStatus
    utilization_rate: float
    utilization_level: UtilizationLevel
    defense_level: DefenseLevel | None
    n1_pass: bool
    n2_pass: bool
    crisis_mode: bool


class HealthCheckHistoryResponse(BaseModel):
    """Historical health check records."""

    items: list[HealthCheckHistoryItem]
    total: int
    page: int
    page_size: int


class EventHistoryItem(BaseModel):
    """Historical resilience event."""

    id: UUID
    timestamp: datetime
    event_type: str
    severity: str | None
    reason: str | None
    triggered_by: str | None


class EventHistoryResponse(BaseModel):
    """Historical resilience events."""

    items: list[EventHistoryItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# Tier 2: Strategic Implementation Schemas
# =============================================================================


# Homeostasis Enums


class AllostasisState(str, Enum):
    """Allostatic state of a faculty member or system."""

    HOMEOSTASIS = "homeostasis"
    ALLOSTASIS = "allostasis"
    ALLOSTATIC_LOAD = "allostatic_load"
    ALLOSTATIC_OVERLOAD = "allostatic_overload"


class DeviationSeverity(str, Enum):
    """Severity of deviation from setpoint."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class CorrectiveActionType(str, Enum):
    """Types of corrective actions."""

    REDISTRIBUTE = "redistribute"
    RECRUIT_BACKUP = "recruit_backup"
    DEFER_ACTIVITY = "defer_activity"
    PROTECT_RESOURCE = "protect_resource"
    REDUCE_SCOPE = "reduce_scope"
    ALERT_ONLY = "alert_only"


# Zone Enums


class ZoneStatus(str, Enum):
    """Health status of a scheduling zone."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"


class ZoneType(str, Enum):
    """Types of scheduling zones."""

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EDUCATION = "education"
    RESEARCH = "research"
    ADMINISTRATIVE = "admin"
    ON_CALL = "on_call"


class ContainmentLevel(str, Enum):
    """Level of failure containment."""

    NONE = "none"
    SOFT = "soft"
    MODERATE = "moderate"
    STRICT = "strict"
    LOCKDOWN = "lockdown"


class BorrowingPriority(str, Enum):
    """Priority levels for cross-zone borrowing."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Equilibrium Enums


class EquilibriumState(str, Enum):
    """State of system equilibrium."""

    STABLE = "stable"
    COMPENSATING = "compensating"
    STRESSED = "stressed"
    UNSUSTAINABLE = "unsustainable"
    CRITICAL = "critical"


class StressType(str, Enum):
    """Types of system stress."""

    FACULTY_LOSS = "faculty_loss"
    DEMAND_SURGE = "demand_surge"
    QUALITY_PRESSURE = "quality_pressure"
    TIME_COMPRESSION = "time_compression"
    RESOURCE_SCARCITY = "resource_scarcity"
    EXTERNAL_PRESSURE = "external_pressure"


class CompensationType(str, Enum):
    """Types of compensation responses."""

    OVERTIME = "overtime"
    CROSS_COVERAGE = "cross_coverage"
    DEFERRED_LEAVE = "deferred_leave"
    SERVICE_REDUCTION = "service_reduction"
    EFFICIENCY_GAIN = "efficiency_gain"
    BACKUP_ACTIVATION = "backup_activation"
    QUALITY_TRADE = "quality_trade"


# Homeostasis Schemas


class SetpointInfo(BaseModel):
    """Information about a setpoint."""

    name: str
    description: str
    target_value: float
    tolerance: float
    unit: str
    is_critical: bool


class FeedbackLoopStatus(BaseModel):
    """Status of a feedback loop."""

    loop_name: str
    setpoint: SetpointInfo
    current_value: float | None
    deviation: float | None
    deviation_severity: DeviationSeverity
    consecutive_deviations: int
    trend_direction: str
    is_improving: bool
    last_checked: datetime | None
    total_corrections: int


class CorrectiveActionInfo(BaseModel):
    """Information about a corrective action."""

    id: UUID
    feedback_loop_name: str
    action_type: CorrectiveActionType
    description: str
    triggered_at: datetime
    deviation_severity: DeviationSeverity
    target_value: float
    actual_value: float
    executed: bool
    effective: bool | None


class AllostasisMetricsResponse(BaseModel):
    """Allostatic load metrics for an entity."""

    entity_id: UUID
    entity_type: str
    calculated_at: datetime
    consecutive_weekend_calls: int
    nights_past_month: int
    schedule_changes_absorbed: int
    holidays_worked_this_year: int
    overtime_hours_month: float
    coverage_gap_responses: int
    cross_coverage_events: int
    acute_stress_score: float
    chronic_stress_score: float
    total_allostatic_load: float
    state: AllostasisState
    risk_level: str


class PositiveFeedbackRiskInfo(BaseModel):
    """Information about a detected positive feedback risk."""

    id: UUID
    name: str
    description: str
    detected_at: datetime
    trigger: str
    amplification: str
    consequence: str
    evidence: list[str]
    confidence: float
    severity: DeviationSeverity
    intervention: str
    urgency: str


class HomeostasisStatusResponse(BaseModel):
    """Overall homeostasis status."""

    timestamp: datetime
    overall_state: AllostasisState
    feedback_loops_healthy: int
    feedback_loops_deviating: int
    active_corrections: int
    positive_feedback_risks: int
    average_allostatic_load: float
    recommendations: list[str]
    feedback_loops: list[FeedbackLoopStatus]
    positive_risks: list[PositiveFeedbackRiskInfo]


class HomeostasisCheckRequest(BaseModel):
    """Request to check homeostasis with provided metrics."""

    metrics: dict[str, float] = Field(
        ...,
        description="Setpoint names and current values, e.g., {'coverage_rate': 0.92}",
        examples=[{"coverage_rate": 0.92, "faculty_utilization": 0.78}],
    )


class HomeostasisReport(BaseModel):
    """
    Report from homeostasis check.

    This is the primary response type from the homeostasis service's
    check_homeostasis method. It provides a summary of feedback loop
    states and system health.
    """

    timestamp: datetime = Field(
        ...,
        description="When the homeostasis check was performed",
    )
    overall_state: AllostasisState = Field(
        ...,
        description="Overall allostatic state of the system",
    )
    feedback_loops_healthy: int = Field(
        ...,
        ge=0,
        description="Number of feedback loops within tolerance",
    )
    feedback_loops_deviating: int = Field(
        ...,
        ge=0,
        description="Number of feedback loops with deviations",
    )
    active_corrections: int = Field(
        ...,
        ge=0,
        description="Number of corrective actions currently in progress",
    )
    positive_feedback_risks: int = Field(
        ...,
        ge=0,
        description="Number of detected positive feedback loop risks",
    )
    average_allostatic_load: float = Field(
        ...,
        ge=0.0,
        description="Average allostatic load across monitored entities",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="List of recommended actions based on current state",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00",
                "overall_state": "homeostasis",
                "feedback_loops_healthy": 4,
                "feedback_loops_deviating": 1,
                "active_corrections": 0,
                "positive_feedback_risks": 0,
                "average_allostatic_load": 25.5,
                "recommendations": ["Monitor coverage rate - approaching threshold"],
            }
        }


class AllostasisCalculateRequest(BaseModel):
    """Request to calculate allostatic load."""

    entity_id: UUID
    entity_type: str = Field(default="faculty", pattern="^(faculty|system)$")
    consecutive_weekend_calls: int = 0
    nights_past_month: int = 0
    schedule_changes_absorbed: int = 0
    holidays_worked_this_year: int = 0
    overtime_hours_month: float = 0.0
    coverage_gap_responses: int = 0
    cross_coverage_events: int = 0


# Zone Schemas


class ZoneFacultyAssignment(BaseModel):
    """Faculty assignment to a zone."""

    faculty_id: UUID
    faculty_name: str
    role: str
    is_available: bool
    assigned_at: datetime


class ZoneHealthReport(BaseModel):
    """Health report for a scheduling zone."""

    zone_id: UUID
    zone_name: str
    zone_type: ZoneType
    checked_at: datetime
    status: ZoneStatus
    containment_level: ContainmentLevel
    is_self_sufficient: bool
    has_surplus: bool
    available_faculty: int
    minimum_required: int
    optimal_required: int
    capacity_ratio: float
    faculty_borrowed: int
    faculty_lent: int
    net_borrowing: int
    active_incidents: int
    services_affected: list[str]
    recommendations: list[str]


class ZoneCreateRequest(BaseModel):
    """Request to create a scheduling zone."""

    name: str = Field(..., min_length=1, max_length=100)
    zone_type: ZoneType
    description: str = Field(default="", max_length=500)
    services: list[str] = Field(default_factory=list)
    minimum_coverage: int = Field(default=1, ge=0)
    optimal_coverage: int = Field(default=2, ge=0)
    priority: int = Field(default=5, ge=1, le=10)


class ZoneResponse(BaseModel):
    """Response for zone operations."""

    id: UUID
    name: str
    zone_type: ZoneType
    description: str
    services: list[str]
    minimum_coverage: int
    optimal_coverage: int
    priority: int
    status: ZoneStatus
    containment_level: ContainmentLevel
    borrowing_limit: int
    lending_limit: int
    is_active: bool


class BorrowingRequest(BaseModel):
    """Request to borrow faculty from another zone."""

    requesting_zone_id: UUID
    lending_zone_id: UUID
    faculty_id: UUID
    priority: BorrowingPriority
    reason: str = Field(..., min_length=10, max_length=500)
    duration_hours: int = Field(default=8, ge=1, le=72)


class BorrowingResponse(BaseModel):
    """Response for borrowing operations."""

    id: UUID
    requesting_zone_id: UUID
    lending_zone_id: UUID
    faculty_id: UUID
    priority: BorrowingPriority
    reason: str
    status: str
    requested_at: datetime
    approved_at: datetime | None
    approved_by: str | None


class ZoneIncidentRequest(BaseModel):
    """Request to record a zone incident."""

    zone_id: UUID
    incident_type: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=10, max_length=500)
    severity: str = Field(..., pattern="^(minor|moderate|severe|critical)$")
    faculty_affected: list[UUID] = Field(default_factory=list)
    services_affected: list[str] = Field(default_factory=list)


class ZoneIncidentResponse(BaseModel):
    """Response for zone incident."""

    id: UUID
    zone_id: UUID
    incident_type: str
    description: str
    severity: str
    started_at: datetime
    faculty_affected: list[str]
    services_affected: list[str]
    capacity_lost: float
    resolved_at: datetime | None
    containment_successful: bool


class BlastRadiusReportResponse(BaseModel):
    """Overall blast radius containment report."""

    generated_at: datetime
    total_zones: int
    zones_healthy: int
    zones_degraded: int
    zones_critical: int
    containment_active: bool
    containment_level: ContainmentLevel
    zones_isolated: int
    active_borrowing_requests: int
    pending_borrowing_requests: int
    zone_reports: list[ZoneHealthReport]
    recommendations: list[str]


class ContainmentSetRequest(BaseModel):
    """Request to set containment level."""

    level: ContainmentLevel
    reason: str = Field(..., min_length=10, max_length=500)


# Equilibrium Schemas


class StressApplyRequest(BaseModel):
    """Request to apply a stress to the system."""

    stress_type: StressType
    description: str = Field(..., min_length=10, max_length=500)
    magnitude: float = Field(..., ge=0.0, le=1.0)
    duration_days: int = Field(..., ge=1, le=365)
    capacity_impact: float = Field(..., ge=-1.0, le=0.0)
    demand_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    is_acute: bool = True
    is_reversible: bool = True


class StressResponse(BaseModel):
    """Response for stress operations."""

    id: UUID
    stress_type: StressType
    description: str
    magnitude: float
    duration_days: int
    capacity_impact: float
    demand_impact: float
    applied_at: datetime
    is_active: bool


class CompensationInitiateRequest(BaseModel):
    """Request to initiate a compensation response."""

    stress_id: UUID
    compensation_type: CompensationType
    description: str = Field(..., min_length=10, max_length=500)
    magnitude: float = Field(..., ge=0.0, le=1.0)
    effectiveness: float = Field(default=0.8, ge=0.0, le=1.0)
    sustainability_days: int = Field(default=30, ge=1, le=365)
    immediate_cost: float = Field(default=0.0, ge=0.0)
    hidden_cost: float = Field(default=0.0, ge=0.0)


class CompensationResponse(BaseModel):
    """Response for compensation operations."""

    id: UUID
    stress_id: UUID
    compensation_type: CompensationType
    description: str
    compensation_magnitude: float
    effectiveness: float
    initiated_at: datetime
    is_active: bool


class EquilibriumShiftResponse(BaseModel):
    """Response for equilibrium shift calculation."""

    id: UUID
    calculated_at: datetime
    original_capacity: float
    original_demand: float
    original_coverage_rate: float
    total_capacity_impact: float
    total_demand_impact: float
    total_compensation: float
    compensation_efficiency: float
    new_capacity: float
    new_demand: float
    new_coverage_rate: float
    sustainable_capacity: float
    compensation_debt: float
    daily_debt_rate: float
    burnout_risk: float
    days_until_exhaustion: int
    equilibrium_state: EquilibriumState
    is_sustainable: bool


class StressPredictionRequest(BaseModel):
    """Request to predict stress response."""

    stress_type: StressType
    magnitude: float = Field(..., ge=0.0, le=1.0)
    duration_days: int = Field(..., ge=1, le=365)
    capacity_impact: float = Field(..., ge=-1.0, le=0.0)
    demand_impact: float = Field(default=0.0, ge=0.0, le=1.0)


class StressPredictionResponse(BaseModel):
    """Prediction of stress response."""

    id: UUID
    predicted_at: datetime
    stress_type: StressType
    stress_magnitude: float
    stress_duration_days: int
    predicted_compensation: float
    predicted_new_capacity: float
    predicted_coverage_rate: float
    predicted_daily_cost: float
    predicted_total_cost: float
    predicted_burnout_increase: float
    additional_intervention_needed: float
    recommended_actions: list[str]
    sustainability_assessment: str


class EquilibriumReportResponse(BaseModel):
    """Comprehensive equilibrium analysis report."""

    generated_at: datetime
    current_equilibrium_state: EquilibriumState
    current_capacity: float
    current_demand: float
    current_coverage_rate: float
    active_stresses: list[StressResponse]
    total_stress_magnitude: float
    active_compensations: list[CompensationResponse]
    total_compensation_magnitude: float
    compensation_debt: float
    sustainability_score: float
    days_until_equilibrium: int
    days_until_exhaustion: int
    recommendations: list[str]


# Combined Tier 2 Status


class Tier2StatusResponse(BaseModel):
    """Combined status of all Tier 2 resilience components."""

    generated_at: datetime

    # Homeostasis summary
    homeostasis_state: AllostasisState
    feedback_loops_healthy: int
    feedback_loops_deviating: int
    average_allostatic_load: float
    positive_feedback_risks: int

    # Blast radius summary
    total_zones: int
    zones_healthy: int
    zones_critical: int
    containment_active: bool
    containment_level: ContainmentLevel

    # Equilibrium summary
    equilibrium_state: EquilibriumState
    current_coverage_rate: float
    compensation_debt: float
    sustainability_score: float

    # Overall
    tier2_status: str  # healthy, degraded, critical
    recommendations: list[str]


# =============================================================================
# Tier 3 Schemas: Cognitive Load, Stigmergy, Hub Analysis
# =============================================================================


class DecisionComplexity(str, Enum):
    """Complexity level of a decision."""

    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    STRATEGIC = "strategic"


class DecisionCategory(str, Enum):
    """Category of scheduling decision."""

    ASSIGNMENT = "assignment"
    SWAP = "swap"
    COVERAGE = "coverage"
    LEAVE = "leave"
    CONFLICT = "conflict"
    OVERRIDE = "override"
    POLICY = "policy"
    EMERGENCY = "emergency"


class CognitiveState(str, Enum):
    """Current cognitive load state."""

    FRESH = "fresh"
    ENGAGED = "engaged"
    LOADED = "loaded"
    FATIGUED = "fatigued"
    DEPLETED = "depleted"


class DecisionOutcome(str, Enum):
    """Outcome of a decision request."""

    DECIDED = "decided"
    DEFERRED = "deferred"
    AUTO_DEFAULT = "auto_default"
    DELEGATED = "delegated"
    CANCELLED = "cancelled"


class TrailType(str, Enum):
    """Types of preference trails."""

    PREFERENCE = "preference"
    AVOIDANCE = "avoidance"
    SWAP_AFFINITY = "swap_affinity"
    WORKLOAD = "workload"
    SEQUENCE = "sequence"


class TrailStrength(str, Enum):
    """Categorical strength of a trail."""

    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class SignalType(str, Enum):
    """Types of behavioral signals."""

    EXPLICIT_PREFERENCE = "explicit_preference"
    ACCEPTED_ASSIGNMENT = "accepted_assignment"
    REQUESTED_SWAP = "requested_swap"
    COMPLETED_SWAP = "completed_swap"
    DECLINED_OFFER = "declined_offer"
    HIGH_SATISFACTION = "high_satisfaction"
    LOW_SATISFACTION = "low_satisfaction"
    PATTERN_DETECTED = "pattern_detected"


class HubRiskLevel(str, Enum):
    """Risk level if this hub is lost."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class HubProtectionStatus(str, Enum):
    """Current protection status of a hub."""

    UNPROTECTED = "unprotected"
    MONITORED = "monitored"
    PROTECTED = "protected"
    REDUNDANT = "redundant"


class CrossTrainingPriority(str, Enum):
    """Priority for cross-training a skill."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Cognitive Load Schemas


class CognitiveSessionResponse(BaseModel):
    """Response for cognitive session."""

    session_id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: datetime | None
    max_decisions_before_break: int
    current_state: CognitiveState
    decisions_count: int
    total_cognitive_cost: float
    should_take_break: bool


class DecisionRequest(BaseModel):
    """Request to create a decision."""

    category: DecisionCategory
    complexity: DecisionComplexity
    description: str = Field(..., min_length=5, max_length=500)
    options: list[str] = Field(..., min_items=2)
    recommended_option: str | None = None
    safe_default: str | None = None
    is_urgent: bool = False


class DecisionResponse(BaseModel):
    """Response for decision operations."""

    decision_id: UUID
    category: DecisionCategory
    complexity: DecisionComplexity
    description: str
    options: list[str]
    recommended_option: str | None
    has_safe_default: bool
    is_urgent: bool
    estimated_cognitive_cost: float


class DecisionQueueResponse(BaseModel):
    """Status of pending decision queue."""

    total_pending: int
    by_complexity: dict
    by_category: dict
    urgent_count: int
    can_auto_decide: int
    oldest_pending: datetime | None
    estimated_cognitive_cost: float
    recommendations: list[str]


class CognitiveLoadAnalysis(BaseModel):
    """Analysis of cognitive load for a schedule."""

    total_score: float
    grade: str
    grade_description: str
    factors: dict
    recommendations: list[str]


# Stigmergy Schemas


class PreferenceTrailRequest(BaseModel):
    """Request to record a preference trail."""

    faculty_id: UUID
    trail_type: TrailType
    slot_type: str | None = None
    slot_id: UUID | None = None
    target_faculty_id: UUID | None = None
    strength: float = Field(default=0.5, ge=0.0, le=1.0)


class PreferenceTrailResponse(BaseModel):
    """Response for preference trail operations."""

    trail_id: UUID
    faculty_id: UUID
    trail_type: TrailType
    strength: float
    strength_category: TrailStrength
    slot_type: str | None
    reinforcement_count: int
    age_days: float


class CollectivePreferenceResponse(BaseModel):
    """Aggregated preference for a slot or slot type."""

    found: bool
    slot_type: str | None
    total_preference_strength: float | None
    total_avoidance_strength: float | None
    net_preference: float | None
    faculty_count: int | None
    confidence: float | None
    is_popular: bool | None
    is_unpopular: bool | None


class StigmergyStatusResponse(BaseModel):
    """Status of the stigmergy system."""

    timestamp: datetime
    total_trails: int
    active_trails: int
    trails_by_type: dict
    average_strength: float
    average_age_days: float
    evaporation_debt_hours: float
    popular_slots: list[str]
    unpopular_slots: list[str]
    strong_swap_pairs: int
    recommendations: list[str]


# Hub Analysis Schemas


class FacultyCentralityResponse(BaseModel):
    """Faculty centrality metrics."""

    faculty_id: UUID
    faculty_name: str
    composite_score: float
    risk_level: HubRiskLevel
    is_hub: bool
    degree_centrality: float
    betweenness_centrality: float
    services_covered: int
    unique_services: int
    replacement_difficulty: float


class HubProfileResponse(BaseModel):
    """Detailed profile for a hub faculty member."""

    faculty_id: UUID
    faculty_name: str
    risk_level: HubRiskLevel
    unique_skills: list[str]
    high_demand_skills: list[str]
    protection_status: HubProtectionStatus
    protection_measures: list[str]
    backup_faculty: list[UUID]
    risk_factors: list[str]
    mitigation_actions: list[str]


class HubProtectionPlanRequest(BaseModel):
    """Request to create hub protection plan."""

    hub_faculty_id: UUID
    period_start: date
    period_end: date
    reason: str = Field(..., min_length=10, max_length=500)
    workload_reduction: float = Field(default=0.3, ge=0.0, le=1.0)
    assign_backup: bool = True


class HubProtectionPlanResponse(BaseModel):
    """Response for hub protection plan."""

    plan_id: UUID
    hub_faculty_id: UUID
    hub_faculty_name: str
    period_start: date
    period_end: date
    reason: str
    workload_reduction: float
    backup_assigned: bool
    backup_faculty_ids: list[UUID]
    status: str


class CrossTrainingRecommendationResponse(BaseModel):
    """Cross-training recommendation."""

    id: UUID
    skill: str
    priority: CrossTrainingPriority
    reason: str
    current_holders: list[UUID]
    recommended_trainees: list[UUID]
    estimated_training_hours: int
    risk_reduction: float
    status: str


class HubDistributionResponse(BaseModel):
    """Hub distribution report."""

    generated_at: datetime
    total_faculty: int
    total_hubs: int
    catastrophic_hubs: int
    critical_hubs: int
    high_risk_hubs: int
    hub_concentration: float
    single_points_of_failure: int
    average_hub_score: float
    services_with_single_provider: list[str]
    services_with_dual_coverage: list[str]
    well_covered_services: list[str]
    recommendations: list[str]


# Combined Tier 3 Status


class Tier3StatusResponse(BaseModel):
    """Combined status of all Tier 3 resilience components."""

    generated_at: datetime

    # Cognitive load summary
    pending_decisions: int
    urgent_decisions: int
    estimated_cognitive_cost: float
    can_auto_decide: int

    # Stigmergy summary
    total_trails: int
    active_trails: int
    average_strength: float
    popular_slots: list[str]
    unpopular_slots: list[str]

    # Hub analysis summary
    total_hubs: int
    catastrophic_hubs: int
    critical_hubs: int
    active_protection_plans: int
    pending_cross_training: int

    # Overall
    tier3_status: str  # healthy, warning, degraded
    issues: list[str]
    recommendations: list[str]


# =============================================================================
# Complex Systems: Self-Organized Criticality (SOC) Early Warning
# =============================================================================


class SOCWarningLevel(str, Enum):
    """Warning level for critical slowing down."""

    GREEN = "green"  # Healthy - no warning signals
    YELLOW = "yellow"  # Single warning signal detected
    ORANGE = "orange"  # Two warning signals detected
    RED = "red"  # All three signals detected - critical
    UNKNOWN = "unknown"  # Insufficient data


# SOC Request Schemas


class CriticalSlowingDownRequest(BaseModel):
    """Request to analyze critical slowing down signals."""

    utilization_history: list[float] = Field(
        ...,
        description="Daily utilization values (0.0 to 1.0) for analysis",
        min_items=30,
    )
    coverage_history: list[float] | None = Field(
        default=None,
        description="Optional daily coverage rates for enhanced analysis",
    )
    days_lookback: int = Field(
        default=60,
        ge=30,
        le=180,
        description="Number of historical days to analyze",
    )


# SOC Response Schemas


class CriticalSlowingDownResponse(BaseModel):
    """Response from critical slowing down analysis."""

    # Analysis metadata
    id: UUID
    calculated_at: datetime
    days_analyzed: int
    data_quality: str  # "excellent", "good", "fair", "poor"

    # Warning status
    is_critical: bool = Field(..., description="Approaching critical point?")
    warning_level: SOCWarningLevel
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Early warning signals - Relaxation Time
    relaxation_time_hours: float | None = Field(
        None,
        description="Current relaxation time in hours (target: < 48)",
    )
    relaxation_time_baseline: float | None = Field(
        None,
        description="Historical baseline relaxation time",
    )
    relaxation_time_increasing: bool = Field(
        False,
        description="Is relaxation time increasing?",
    )

    # Early warning signals - Variance
    variance_current: float | None = Field(
        None,
        description="Current variance in utilization",
    )
    variance_baseline: float | None = Field(
        None,
        description="Historical baseline variance",
    )
    variance_slope: float | None = Field(
        None,
        description="Variance trend slope (target: < 0.1)",
    )
    variance_increasing: bool = Field(
        False,
        description="Is variance increasing?",
    )

    # Early warning signals - Autocorrelation
    autocorrelation_ac1: float | None = Field(
        None,
        description="Lag-1 autocorrelation (target: < 0.7)",
    )
    autocorrelation_baseline: float | None = Field(
        None,
        description="Historical baseline AC1",
    )
    autocorrelation_increasing: bool = Field(
        False,
        description="Is autocorrelation increasing?",
    )

    # Risk assessment
    signals_triggered: int = Field(
        ...,
        ge=0,
        le=3,
        description="Count of warning signals triggered (0-3)",
    )
    estimated_days_to_critical: int | None = Field(
        None,
        description="Projected days until critical point",
    )
    avalanche_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite avalanche risk score",
    )

    # Actionable insights
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations",
    )
    immediate_actions: list[str] = Field(
        default_factory=list,
        description="Actions requiring immediate attention",
    )
    watch_items: list[str] = Field(
        default_factory=list,
        description="Items to monitor closely",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "calculated_at": "2024-01-15T10:30:00",
                "days_analyzed": 60,
                "data_quality": "excellent",
                "is_critical": True,
                "warning_level": "orange",
                "confidence": 0.85,
                "relaxation_time_hours": 52.3,
                "relaxation_time_baseline": 24.1,
                "relaxation_time_increasing": True,
                "variance_current": 0.045,
                "variance_baseline": 0.022,
                "variance_slope": 0.15,
                "variance_increasing": True,
                "autocorrelation_ac1": 0.68,
                "autocorrelation_baseline": 0.45,
                "autocorrelation_increasing": True,
                "signals_triggered": 2,
                "estimated_days_to_critical": 18,
                "avalanche_risk_score": 0.72,
                "recommendations": [
                    "⚠️ TWO warning signals - avalanche risk elevated",
                    "Activate preventive measures",
                ],
                "immediate_actions": ["Review N-1/N-2 contingency plans"],
                "watch_items": ["Monitor swap resolution times"],
            }
        }


class SOCMetricsHistoryResponse(BaseModel):
    """Historical SOC metrics for trend analysis."""

    metrics: list[CriticalSlowingDownResponse]
    total_count: int
    date_range_start: date
    date_range_end: date
    trend_summary: dict = Field(
        default_factory=dict,
        description="Summary of trends over the period",
    )


# =============================================================================
# Additional Response Schemas for API Endpoints
# =============================================================================


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str


class FallbackDeactivationResponse(BaseModel):
    """Response from fallback deactivation."""

    success: bool
    message: str


class MTFComplianceResponse(BaseModel):
    """Response from MTF compliance check (Iron Dome)."""

    drrs_category: str = Field(..., description="DRRS C-rating (C1-C5)")
    mission_capability: str = Field(..., description="Mission capability assessment")
    personnel_rating: str = Field(..., description="Personnel P-rating (P1-P4)")
    capability_rating: str = Field(..., description="Capability S-rating (S1-S4)")
    circuit_breaker: dict | None = Field(
        None, description="Circuit breaker status if checked"
    )
    executive_summary: str = Field(..., description="Executive summary")
    deficiencies: list[str] = Field(default_factory=list)
    mfrs_generated: int = Field(default=0)
    rffs_generated: int = Field(default=0)
    iron_dome_status: str = Field(..., description="green/yellow/red status")
    severity: str = Field(..., description="healthy/warning/critical/emergency")


class ZoneListResponse(BaseModel):
    """Response listing all zones."""

    zones: list["ZoneResponse"]
    total: int


class ZoneAssignmentResponse(BaseModel):
    """Response from zone faculty assignment."""

    success: bool
    message: str


class ContainmentSetResponse(BaseModel):
    """Response from setting containment level."""

    success: bool
    containment_level: str
    reason: str


class StressResolveResponse(BaseModel):
    """Response from resolving a stress."""

    success: bool
    stress_id: str
    message: str


class CognitiveSessionStartResponse(BaseModel):
    """Response from starting a cognitive session."""

    session_id: UUID
    user_id: str
    started_at: str
    max_decisions_before_break: int
    current_state: str


class CognitiveSessionEndResponse(BaseModel):
    """Response from ending a cognitive session."""

    success: bool
    session_id: str
    message: str


class CognitiveSessionStatusResponse(BaseModel):
    """Response for cognitive session status."""

    session_id: str
    user_id: str
    current_state: str
    decisions_this_session: int
    cognitive_cost_this_session: float
    remaining_capacity: float
    decisions_until_break: int
    should_take_break: bool
    average_decision_time: float
    recommendations: list[str]


class DecisionCreateResponse(BaseModel):
    """Response from creating a decision."""

    decision_id: UUID
    category: str
    complexity: str
    description: str
    options: list[str]
    recommended_option: str | None
    has_safe_default: bool
    is_urgent: bool
    estimated_cognitive_cost: float


class DecisionResolveResponse(BaseModel):
    """Response from resolving a decision."""

    success: bool
    decision_id: str
    chosen_option: str


class PrioritizedDecisionsResponse(BaseModel):
    """Response for prioritized decisions."""

    decisions: list[dict]
    total: int


class ScheduleCognitiveAnalysisResponse(BaseModel):
    """Response from analyzing schedule cognitive load."""

    total_score: float
    grade: str
    grade_description: str
    factors: dict
    recommendations: list[str]


class PreferenceRecordResponse(BaseModel):
    """Response from recording a preference."""

    trail_id: UUID
    faculty_id: str
    trail_type: str
    strength: float
    strength_category: str


class BehavioralSignalResponse(BaseModel):
    """Response from recording a behavioral signal."""

    success: bool
    signal_type: str
    faculty_id: str


class FacultyPreferencesResponse(BaseModel):
    """Response for faculty preferences."""

    faculty_id: str
    trails: list[dict]
    total: int


class SwapNetworkResponse(BaseModel):
    """Response for swap network."""

    edges: list[dict]
    total_pairs: int


class AssignmentSuggestionsResponse(BaseModel):
    """Response for assignment suggestions."""

    suggestions: list[dict]
    total: int


class StigmergyPatternsResponse(BaseModel):
    """Response for stigmergy patterns."""

    patterns: list[dict] = Field(default_factory=list)
    total: int = 0


class TrailEvaporationResponse(BaseModel):
    """Response from trail evaporation."""

    success: bool
    message: str


class HubAnalysisResponse(BaseModel):
    """Response from hub analysis."""

    analyzed_at: str
    total_faculty: int
    total_hubs: int
    hubs: list[dict]


class TopHubsResponse(BaseModel):
    """Response for top hubs."""

    hubs: list[dict]
    count: int


class HubProfileDetailResponse(BaseModel):
    """Response for hub profile details."""

    faculty_id: str
    faculty_name: str
    risk_level: str
    unique_skills: list[str]
    high_demand_skills: list[str]
    protection_status: str
    protection_measures: list[str]
    backup_faculty: list[str]
    risk_factors: list[str]
    mitigation_actions: list[str]


class CrossTrainingRecommendationsResponse(BaseModel):
    """Response for cross-training recommendations."""

    recommendations: list[dict]
    total: int


class HubProtectionPlanCreateResponse(BaseModel):
    """Response from creating a hub protection plan."""

    plan_id: str
    hub_faculty_id: str
    hub_faculty_name: str
    period_start: str
    period_end: str
    reason: str
    workload_reduction: float
    backup_assigned: bool
    backup_faculty_ids: list[str]
    status: str


class HubDistributionReportResponse(BaseModel):
    """Response for hub distribution report."""

    generated_at: str
    total_faculty: int
    total_hubs: int
    catastrophic_hubs: int
    critical_hubs: int
    high_risk_hubs: int
    hub_concentration: float
    single_points_of_failure: int
    average_hub_score: float
    services_with_single_provider: list[str]
    services_with_dual_coverage: list[str]
    well_covered_services: list[str]
    recommendations: list[str]


class HubStatusResponse(BaseModel):
    """Response for hub status."""

    total_hubs: int
    catastrophic_count: int
    critical_count: int
    high_risk_count: int
    active_protection_plans: int
    pending_cross_training: int
    recommendations: list[str] = Field(default_factory=list)
