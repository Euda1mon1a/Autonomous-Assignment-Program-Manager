"""Resilience API schemas."""
from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UtilizationLevel(str, Enum):
    """Utilization severity levels (queuing theory)."""
    GREEN = "GREEN"      # < 70% - healthy buffer
    YELLOW = "YELLOW"    # 70-80% - approaching threshold
    ORANGE = "ORANGE"    # 80-90% - degraded operations
    RED = "RED"          # 90-95% - critical, cascade risk
    BLACK = "BLACK"      # > 95% - imminent failure


class DefenseLevel(str, Enum):
    """Defense in depth levels (nuclear safety paradigm)."""
    PREVENTION = "PREVENTION"
    CONTROL = "CONTROL"
    SAFETY_SYSTEMS = "SAFETY_SYSTEMS"
    CONTAINMENT = "CONTAINMENT"
    EMERGENCY = "EMERGENCY"


class LoadSheddingLevel(str, Enum):
    """Load shedding levels (triage)."""
    NORMAL = "NORMAL"      # All activities
    YELLOW = "YELLOW"      # Suspend optional education
    ORANGE = "ORANGE"      # Also suspend admin & research
    RED = "RED"            # Also suspend core education
    BLACK = "BLACK"        # Essentials only
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
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_contingency: bool = Field(
        default=False,
        description="Include N-1/N-2 contingency analysis (slower)"
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
    severity: Optional[CrisisSeverity] = None
    actions_taken: list[str]
    load_shedding_level: LoadSheddingLevel
    recovery_plan: Optional[list[str]] = None


class FallbackInfo(BaseModel):
    """Information about a fallback schedule."""
    scenario: FallbackScenario
    description: str
    is_active: bool
    is_precomputed: bool
    assignments_count: Optional[int] = None
    coverage_rate: Optional[float] = None
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
    defense_level: Optional[DefenseLevel]
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
    severity: Optional[str]
    reason: Optional[str]
    triggered_by: Optional[str]


class EventHistoryResponse(BaseModel):
    """Historical resilience events."""
    items: list[EventHistoryItem]
    total: int
    page: int
    page_size: int
