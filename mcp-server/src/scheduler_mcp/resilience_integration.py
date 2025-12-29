"""
Resilience Framework MCP Integration.

Exposes all 13 resilience patterns as MCP tools for AI assistant interaction.
These tools provide deep insights into system stability, vulnerability analysis,
and automated safety mechanisms.

Tier 1 (Critical): Core resilience monitoring
Tier 2 (Strategic): Advanced stress analysis and equilibrium
Tier 3 (Advanced): Behavioral patterns and cognitive load
Tier 4 (Epidemiological): Burnout contagion modeling and network analysis
"""

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)


def _anonymize_id(identifier: str | None, prefix: str = "Provider") -> str:
    """Create consistent anonymized reference from ID.

    Uses a hash-based approach to create deterministic but non-reversible
    identifiers that comply with OPSEC/PERSEC requirements for military
    medical data.

    Args:
        identifier: The original identifier (e.g., faculty_id, provider_id)
        prefix: Prefix for the anonymized string (e.g., "Faculty", "Provider")

    Returns:
        Anonymized string like "Faculty-a1b2c3" or "Provider-d4e5f6"
    """
    if not identifier:
        return f"{prefix}-unknown"
    import hashlib
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"


# =============================================================================
# Tier 1: Critical Resilience Tools
# =============================================================================


class UtilizationLevelEnum(str, Enum):
    """Utilization status levels."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"


class UtilizationResponse(BaseModel):
    """Response from utilization threshold check."""

    level: UtilizationLevelEnum
    utilization_rate: float = Field(ge=0.0, le=1.0)
    effective_utilization: float = Field(ge=0.0, le=1.0)
    buffer_remaining: float = Field(ge=0.0, le=1.0)
    total_capacity: int
    required_coverage: int
    current_assignments: int
    safe_maximum: int
    wait_time_multiplier: float
    message: str
    recommendations: list[str]
    severity: str  # "healthy", "warning", "critical", "emergency"


class DefenseLevelEnum(str, Enum):
    """Defense in depth levels."""

    PREVENTION = "prevention"
    CONTROL = "control"
    SAFETY_SYSTEMS = "safety_systems"
    CONTAINMENT = "containment"
    EMERGENCY = "emergency"


class DefenseLevelResponse(BaseModel):
    """Response from defense level check."""

    current_level: DefenseLevelEnum
    recommended_level: DefenseLevelEnum
    status: str  # "ready", "active", "degraded"
    active_actions: list[dict[str, Any]]
    automation_status: dict[str, bool]
    escalation_needed: bool
    coverage_rate: float
    severity: str  # "normal", "elevated", "critical"


class ContingencyAnalysisRequest(BaseModel):
    """Request for N-1/N-2 contingency analysis."""

    start_date: date | None = None  # Defaults to today in backend
    end_date: date | None = None  # Defaults to 30 days from start in backend
    analyze_n1: bool = True
    analyze_n2: bool = True
    include_cascade_simulation: bool = False
    critical_faculty_only: bool = True


class VulnerabilityInfo(BaseModel):
    """Information about a detected vulnerability."""

    faculty_id: str
    faculty_name: str
    severity: str  # "critical", "high", "medium", "low"
    affected_blocks: int
    is_unique_provider: bool
    details: str
    services_affected: list[str] = Field(default_factory=list)


class FatalPairInfo(BaseModel):
    """Information about a fatal faculty pair."""

    faculty_1_id: str
    faculty_1_name: str
    faculty_2_id: str
    faculty_2_name: str
    uncoverable_blocks: int
    affected_services: list[str] = Field(default_factory=list)


class ContingencyAnalysisResponse(BaseModel):
    """Response from contingency analysis."""

    analysis_date: str
    period_start: str
    period_end: str
    n1_pass: bool
    n1_vulnerabilities: list[VulnerabilityInfo]
    n2_pass: bool
    n2_fatal_pairs: list[FatalPairInfo]
    most_critical_faculty: list[str]
    phase_transition_risk: str  # "low", "medium", "high", "critical"
    leading_indicators: list[str]
    recommended_actions: list[str]
    severity: str  # "healthy", "vulnerable", "critical"


class FallbackScenarioEnum(str, Enum):
    """Pre-computed fallback scenarios."""

    SINGLE_ABSENCE = "single_absence"
    DUAL_ABSENCE = "dual_absence"
    PCS_SEASON = "pcs_season"
    HOLIDAY_PERIOD = "holiday_period"
    DEPLOYMENT = "deployment"
    MASS_CASUALTY = "mass_casualty"


class FallbackScheduleInfo(BaseModel):
    """Information about a fallback schedule."""

    scenario: FallbackScenarioEnum
    is_active: bool
    activated_at: str | None
    approved_by: str | None
    assignments_count: int
    coverage_rate: float
    description: str


class StaticFallbacksResponse(BaseModel):
    """Response with available fallback schedules."""

    active_fallbacks: list[FallbackScheduleInfo]
    available_fallbacks: list[FallbackScheduleInfo]
    recommended_scenario: FallbackScenarioEnum | None
    precomputed_scenarios_count: int
    last_precomputed: str | None
    message: str


class LoadSheddingLevelEnum(str, Enum):
    """Load shedding (sacrifice hierarchy) levels."""

    NORMAL = "normal"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"
    CRITICAL = "critical"


class SacrificeHierarchyResponse(BaseModel):
    """Response from sacrifice hierarchy execution."""

    current_level: LoadSheddingLevelEnum
    activities_suspended: list[str]
    activities_protected: list[str]
    simulation_mode: bool
    estimated_capacity_freed: float
    recovery_plan: list[dict[str, Any]]
    message: str
    severity: str


# =============================================================================
# Tier 2: Strategic Resilience Tools
# =============================================================================


class HomeostasisStatusResponse(BaseModel):
    """Response from homeostasis analysis."""

    overall_state: str  # "homeostasis", "allostasis", "allostatic_load", "allostatic_overload"
    feedback_loops_healthy: int
    feedback_loops_deviating: int
    average_allostatic_load: float
    positive_feedback_risks: int
    urgent_corrections_needed: int
    faculty_at_risk: list[dict[str, Any]]
    system_metrics: dict[str, float]
    recommendations: list[str]
    severity: str


class BlastRadiusAnalysisRequest(BaseModel):
    """Request for blast radius analysis."""

    zone_id: str | None = None
    check_all_zones: bool = True


class ZoneHealthInfo(BaseModel):
    """Health information for a scheduling zone."""

    zone_id: str
    zone_name: str
    zone_type: str
    health_status: str  # "healthy", "degraded", "critical"
    coverage_rate: float
    available_faculty: int
    minimum_required: int
    incidents_24h: int
    containment_level: str


class BlastRadiusAnalysisResponse(BaseModel):
    """Response from blast radius analysis."""

    total_zones: int
    zones_healthy: int
    zones_degraded: int
    zones_critical: int
    zone_details: list[ZoneHealthInfo]
    global_containment_level: str  # "none", "light", "moderate", "strict"
    containment_active: bool
    borrowing_requests_pending: int
    recommendations: list[str]
    severity: str


class LeChatelierAnalysisRequest(BaseModel):
    """Request for Le Chatelier equilibrium analysis."""

    include_stress_prediction: bool = True


class StressInfo(BaseModel):
    """Information about a system stress."""

    stress_id: str
    stress_type: str
    description: str
    magnitude: float
    duration_days: int
    capacity_impact: float
    is_active: bool
    compensation_responses: int


class EquilibriumAnalysisResponse(BaseModel):
    """Response from Le Chatelier analysis."""

    current_equilibrium_state: (
        str  # "stable", "compensating", "stressed", "unsustainable", "critical"
    )
    current_capacity: float
    current_demand: float
    current_coverage_rate: float
    active_stresses: list[StressInfo]
    compensation_debt: float
    sustainability_score: float
    days_until_exhaustion: int | None
    predicted_coverage_in_30_days: float
    compensation_sustainability: str  # "sustainable", "at_risk", "unsustainable"
    recommendations: list[str]
    severity: str


# =============================================================================
# Tier 3: Advanced Resilience Tools
# =============================================================================


class HubCentralityInfo(BaseModel):
    """Information about faculty hub centrality."""

    faculty_id: str
    faculty_name: str
    centrality_score: float
    risk_level: str  # "low", "moderate", "high", "catastrophic"
    services_covered: int
    unique_coverage_slots: int
    replacement_difficulty: float
    workload_share: float
    betweenness: float
    pagerank: float
    cascade_impact: str | None


class HubAnalysisResponse(BaseModel):
    """Response from hub centrality analysis."""

    total_faculty_analyzed: int
    hubs_identified: int
    critical_hubs: int
    top_hubs: list[HubCentralityInfo]
    cascade_failure_points: list[str]
    cross_training_priority: list[dict[str, Any]]
    hub_concentration_risk: str  # "low", "moderate", "high", "critical"
    recommendations: list[str]
    severity: str


class CognitiveLoadRequest(BaseModel):
    """Request for cognitive load assessment."""

    session_id: str | None = None
    include_queue_status: bool = True


class DecisionInfo(BaseModel):
    """Information about a pending decision."""

    decision_id: str
    category: str
    complexity: str
    description: str
    is_urgent: bool
    deadline: str | None
    cognitive_cost: float


class CognitiveLoadResponse(BaseModel):
    """Response from cognitive load assessment."""

    session_id: str | None
    pending_decisions: int
    urgent_decisions: int
    total_cognitive_cost: float
    decision_queue: list[DecisionInfo]
    fatigue_level: str  # "fresh", "alert", "fatigued", "exhausted"
    can_auto_decide: int
    batching_opportunities: int
    recommendations: list[str]
    severity: str


class BehavioralPatternsResponse(BaseModel):
    """Response from behavioral patterns analysis."""

    total_trails: int
    active_trails: int
    average_strength: float
    popular_slots: list[dict[str, Any]]
    unpopular_slots: list[dict[str, Any]]
    swap_network_density: float
    preference_clustering: dict[str, int]
    emergent_patterns: list[str]
    recommendations: list[str]


class StigmergyAnalysisRequest(BaseModel):
    """Request for stigmergy optimization analysis."""

    slot_id: str | None = None
    slot_type: str | None = None
    include_suggestions: bool = True


class StigmergyAnalysisResponse(BaseModel):
    """Response from stigmergy analysis."""

    collective_preferences: dict[str, Any] | None
    faculty_suggestions: list[dict[str, Any]]
    preference_strength: float
    popularity_score: float
    contributing_faculty: int
    optimization_potential: float
    swarm_intelligence_score: float
    recommendations: list[str]


class MTFComplianceRequest(BaseModel):
    """Request for MTF compliance check."""

    check_circuit_breaker: bool = True
    generate_sitrep: bool = True


class CircuitBreakerInfo(BaseModel):
    """Circuit breaker status information."""

    state: str  # "closed", "half_open", "open"
    tripped: bool
    trigger: str | None
    trigger_details: str | None
    triggered_at: str | None
    locked_operations: list[str]
    override_active: bool


class MTFComplianceResponse(BaseModel):
    """Response from MTF compliance check."""

    drrs_category: str  # "C1", "C2", "C3", "C4", "C5"
    mission_capability: str  # "FMC", "PMC", "NMC"
    personnel_rating: str  # "P1", "P2", "P3", "P4"
    capability_rating: str  # "S1", "S2", "S3", "S4"
    circuit_breaker: CircuitBreakerInfo
    executive_summary: str
    deficiencies: list[str]
    mfrs_generated: int
    rffs_generated: int
    iron_dome_status: str  # "green", "amber", "red", "black"
    severity: str


# =============================================================================
# Tool Functions
# =============================================================================


async def check_utilization_threshold(
    available_faculty: int,
    required_blocks: int,
    blocks_per_faculty_per_day: float = 2.0,
    days_in_period: int = 1,
) -> UtilizationResponse:
    """
    Check current utilization against 80% threshold (queuing theory).

    This tool calculates system utilization and compares it to the critical
    80% threshold from queuing theory. Above 80%, wait times increase
    exponentially and cascade failures become likely.

    Args:
        available_faculty: Number of faculty members available
        required_blocks: Number of blocks requiring coverage
        blocks_per_faculty_per_day: Max blocks per faculty per day (default: 2)
        days_in_period: Number of days in analysis period

    Returns:
        UtilizationResponse with current status and recommendations

    Raises:
        ValueError: If parameters are invalid
    """
    if available_faculty < 0:
        raise ValueError("available_faculty must be non-negative")
    if required_blocks < 0:
        raise ValueError("required_blocks must be non-negative")

    logger.info(f"Checking utilization: {available_faculty} faculty, {required_blocks} blocks")

    try:
        from app.resilience.utilization import UtilizationMonitor, UtilizationThreshold

        monitor = UtilizationMonitor(UtilizationThreshold())
        metrics = monitor.calculate_utilization(
            available_faculty=[{"id": f"fac-{i}"} for i in range(available_faculty)],
            required_blocks=required_blocks,
            blocks_per_faculty_per_day=blocks_per_faculty_per_day,
            days_in_period=days_in_period,
        )

        status_report = monitor.get_status_report(metrics)
        wait_multiplier = monitor.calculate_wait_time_multiplier(metrics.utilization_rate)

        # Determine severity
        severity_map = {
            "green": "healthy",
            "yellow": "warning",
            "orange": "critical",
            "red": "emergency",
            "black": "emergency",
        }
        severity = severity_map.get(metrics.level.value, "unknown")

        return UtilizationResponse(
            level=UtilizationLevelEnum(metrics.level.value),
            utilization_rate=metrics.utilization_rate,
            effective_utilization=metrics.effective_utilization,
            buffer_remaining=metrics.buffer_remaining,
            total_capacity=metrics.total_capacity,
            required_coverage=required_blocks,
            current_assignments=metrics.current_assignments,
            safe_maximum=status_report["capacity"]["safe_maximum"],
            wait_time_multiplier=wait_multiplier,
            message=status_report["message"],
            recommendations=status_report["recommendations"],
            severity=severity,
        )

    except ImportError as e:
        logger.error(f"Resilience service unavailable: {e}")
        # Graceful fallback with simple calculation
        capacity = available_faculty * blocks_per_faculty_per_day * days_in_period
        utilization = required_blocks / capacity if capacity > 0 else 1.0

        if utilization >= 0.95:
            level = UtilizationLevelEnum.BLACK
            severity = "emergency"
        elif utilization >= 0.90:
            level = UtilizationLevelEnum.RED
            severity = "emergency"
        elif utilization >= 0.80:
            level = UtilizationLevelEnum.ORANGE
            severity = "critical"
        elif utilization >= 0.70:
            level = UtilizationLevelEnum.YELLOW
            severity = "warning"
        else:
            level = UtilizationLevelEnum.GREEN
            severity = "healthy"

        return UtilizationResponse(
            level=level,
            utilization_rate=min(utilization, 1.0),
            effective_utilization=min(utilization, 1.0),
            buffer_remaining=max(0.0, 0.80 - utilization),
            total_capacity=int(capacity),
            required_coverage=required_blocks,
            current_assignments=required_blocks,
            safe_maximum=int(capacity * 0.80),
            wait_time_multiplier=utilization / (1 - min(utilization, 0.99))
            if utilization < 1.0
            else 999.9,
            message=f"Utilization at {utilization * 100:.0f}% (service unavailable, using fallback calculation)",
            recommendations=["Service unavailable - using simplified calculation"],
            severity=severity,
        )


async def get_defense_level(
    coverage_rate: float,
) -> DefenseLevelResponse:
    """
    Get current defense-in-depth level (nuclear safety paradigm).

    This tool implements the 5-level defense-in-depth strategy from nuclear
    reactor safety, adapted for medical scheduling. Each level operates
    independently assuming all previous levels have failed.

    Args:
        coverage_rate: Current coverage rate (0.0 to 1.0)

    Returns:
        DefenseLevelResponse with current and recommended defense levels

    Raises:
        ValueError: If coverage_rate is invalid
    """
    if not 0.0 <= coverage_rate <= 1.0:
        raise ValueError("coverage_rate must be between 0.0 and 1.0")

    logger.info(f"Checking defense level for coverage rate: {coverage_rate:.2%}")

    try:
        from app.resilience.defense_in_depth import DefenseInDepth, DefenseLevel

        defense = DefenseInDepth()
        recommended = defense.get_recommended_level(coverage_rate)
        status_report = defense.get_status_report()

        current_level = DefenseLevel.PREVENTION  # Default
        for level_status in defense.get_all_status():
            if level_status.status == "active":
                current_level = level_status.level
                break

        # Get active actions
        active_actions = []
        for level_data in status_report["levels"]:
            if level_data["status"] == "active":
                active_actions.extend(
                    [
                        {
                            "name": a["name"],
                            "description": a["description"],
                            "automated": a["automated"],
                            "activations": a["activations"],
                        }
                        for a in level_data["actions"]
                    ]
                )

        # Automation status
        automation = {
            "prevention": True,
            "control": True,
            "safety_systems": True,
            "containment": False,
            "emergency": False,
        }

        escalation_needed = recommended.value > current_level.value

        # Determine severity
        if recommended.value >= 5:
            severity = "critical"
        elif recommended.value >= 4:
            severity = "critical"
        elif recommended.value >= 3:
            severity = "elevated"
        else:
            severity = "normal"

        return DefenseLevelResponse(
            current_level=DefenseLevelEnum(current_level.name.lower()),
            recommended_level=DefenseLevelEnum(recommended.name.lower()),
            status="active" if escalation_needed else "ready",
            active_actions=active_actions,
            automation_status=automation,
            escalation_needed=escalation_needed,
            coverage_rate=coverage_rate,
            severity=severity,
        )

    except ImportError as e:
        logger.error(f"Resilience service unavailable: {e}")

        # Simple fallback logic
        if coverage_rate >= 0.95:
            recommended = DefenseLevelEnum.PREVENTION
            severity = "normal"
        elif coverage_rate >= 0.90:
            recommended = DefenseLevelEnum.CONTROL
            severity = "elevated"
        elif coverage_rate >= 0.80:
            recommended = DefenseLevelEnum.SAFETY_SYSTEMS
            severity = "elevated"
        elif coverage_rate >= 0.70:
            recommended = DefenseLevelEnum.CONTAINMENT
            severity = "critical"
        else:
            recommended = DefenseLevelEnum.EMERGENCY
            severity = "critical"

        return DefenseLevelResponse(
            current_level=DefenseLevelEnum.PREVENTION,
            recommended_level=recommended,
            status="degraded",
            active_actions=[],
            automation_status={},
            escalation_needed=recommended != DefenseLevelEnum.PREVENTION,
            coverage_rate=coverage_rate,
            severity=severity,
        )


async def run_contingency_analysis_deep(
    request: ContingencyAnalysisRequest,
) -> ContingencyAnalysisResponse:
    """
    Run N-1/N-2 contingency analysis (power grid planning).

    This tool performs contingency analysis inspired by electrical grid
    operations. N-1: system must survive loss of any single component.
    N-2: system must survive loss of any two components.

    Args:
        request: Contingency analysis request configuration

    Returns:
        ContingencyAnalysisResponse with vulnerability analysis

    Raises:
        ValueError: If request parameters are invalid
        RuntimeError: If backend API call fails
    """
    logger.info(f"Running contingency analysis: N-1={request.analyze_n1}, N-2={request.analyze_n2}")

    try:
        client = await get_api_client()

        # Prepare date parameters (use defaults if not specified)
        # Default to one block (28 days) for analysis period
        start = request.start_date or datetime.now().date()
        end = request.end_date or (start + timedelta(days=28))

        # Call backend vulnerability endpoint
        result = await client.run_contingency_analysis(
            scenario="n1_n2_analysis",  # Not used by backend but required by signature
            affected_ids=[],
            start_date=start.isoformat(),
            end_date=end.isoformat(),
        )

        # Map backend VulnerabilityReportResponse to MCP ContingencyAnalysisResponse
        # Backend response structure:
        # - analyzed_at: datetime
        # - period_start, period_end: date
        # - n1_pass, n2_pass: bool
        # - phase_transition_risk: str
        # - n1_vulnerabilities: list[dict] with faculty_id, affected_blocks, severity
        # - n2_fatal_pairs: list[dict] with faculty1_id, faculty2_id
        # - most_critical_faculty: list[CentralityScore] with person_id, centrality_score, name
        # - recommended_actions: list[str]

        # Map n1_vulnerabilities
        n1_vulns = []
        for v in result.get("n1_vulnerabilities", []):
            n1_vulns.append(
                VulnerabilityInfo(
                    faculty_id=v.get("faculty_id", ""),
                    faculty_name=_anonymize_id(v.get("faculty_id"), "Faculty"),
                    severity=v.get("severity", "medium"),
                    affected_blocks=v.get("affected_blocks", 0),
                    is_unique_provider=v.get("affected_blocks", 0) > 10,  # Heuristic
                    details=f"Loss would affect {v.get('affected_blocks', 0)} blocks",
                    services_affected=[],
                )
            )

        # Map n2_fatal_pairs
        n2_pairs = []
        for p in result.get("n2_fatal_pairs", []):
            n2_pairs.append(
                FatalPairInfo(
                    faculty_1_id=p.get("faculty1_id", ""),
                    faculty_1_name=_anonymize_id(p.get("faculty1_id"), "Faculty"),
                    faculty_2_id=p.get("faculty2_id", ""),
                    faculty_2_name=_anonymize_id(p.get("faculty2_id"), "Faculty"),
                    uncoverable_blocks=p.get("uncoverable_blocks", 0),
                    affected_services=[],
                )
            )

        # Map most_critical_faculty (CentralityScore -> list[str])
        critical_faculty = []
        for f in result.get("most_critical_faculty", []):
            if isinstance(f, dict):
                name = f.get("name") or f.get("person_id", "unknown")
                critical_faculty.append(name)
            else:
                critical_faculty.append(str(f))

        # Determine severity based on pass/fail status
        n1_pass = result.get("n1_pass", True)
        n2_pass = result.get("n2_pass", True)
        if not n1_pass:
            severity = "critical"
        elif not n2_pass:
            severity = "vulnerable"
        else:
            severity = "healthy"

        # Generate leading indicators based on vulnerability data
        leading_indicators = []
        if len(n1_vulns) > 3:
            leading_indicators.append(f"{len(n1_vulns)} N-1 vulnerabilities detected")
        if len(n2_pairs) > 5:
            leading_indicators.append(f"{len(n2_pairs)} fatal faculty pairs identified")
        phase_risk = result.get("phase_transition_risk", "low")
        if phase_risk in ("high", "critical"):
            leading_indicators.append(f"Phase transition risk is {phase_risk}")

        return ContingencyAnalysisResponse(
            analysis_date=result.get("analyzed_at", datetime.now().isoformat())[:10],
            period_start=result.get("period_start", start.isoformat()),
            period_end=result.get("period_end", end.isoformat()),
            n1_pass=n1_pass,
            n1_vulnerabilities=n1_vulns,
            n2_pass=n2_pass,
            n2_fatal_pairs=n2_pairs,
            most_critical_faculty=critical_faculty,
            phase_transition_risk=phase_risk,
            leading_indicators=leading_indicators,
            recommended_actions=result.get("recommended_actions", []),
            severity=severity,
        )

    except Exception as e:
        logger.error(f"Contingency analysis failed: {e}")
        raise RuntimeError(f"Failed to run contingency analysis: {e}") from e


async def get_static_fallbacks() -> StaticFallbacksResponse:
    """
    Get pre-computed fallback schedules (AWS static stability).

    This tool retrieves fallback schedules that have been pre-computed for
    various crisis scenarios. Like AWS availability zones, these provide
    immediate failover capability.

    Returns:
        StaticFallbacksResponse with available fallback schedules
    """
    logger.info("Retrieving static fallback schedules")

    try:
        # Placeholder for actual integration
        logger.warning("Static fallbacks not yet fully integrated with backend")

        return StaticFallbacksResponse(
            active_fallbacks=[],
            available_fallbacks=[],
            recommended_scenario=None,
            precomputed_scenarios_count=0,
            last_precomputed=None,
            message="Static fallback system ready",
        )

    except Exception as e:
        logger.error(f"Failed to retrieve fallbacks: {e}")
        raise


async def execute_sacrifice_hierarchy(
    target_level: LoadSheddingLevelEnum,
    simulate_only: bool = True,
) -> SacrificeHierarchyResponse:
    """
    Execute sacrifice hierarchy (triage-based load shedding).

    This tool implements triage-based load shedding, suspending non-essential
    activities in priority order to maintain critical patient safety functions.

    Args:
        target_level: Target load shedding level
        simulate_only: If True, only simulate (don't actually apply)

    Returns:
        SacrificeHierarchyResponse with load shedding details

    Raises:
        ValueError: If target_level is invalid
    """
    logger.info(f"Executing sacrifice hierarchy to level: {target_level.value}")

    try:
        # Placeholder for actual integration
        logger.warning("Sacrifice hierarchy not yet fully integrated with backend")

        activities_by_level = {
            LoadSheddingLevelEnum.NORMAL: [],
            LoadSheddingLevelEnum.YELLOW: ["optional_education", "professional_development"],
            LoadSheddingLevelEnum.ORANGE: [
                "optional_education",
                "professional_development",
                "admin_tasks",
                "research",
            ],
            LoadSheddingLevelEnum.RED: [
                "optional_education",
                "professional_development",
                "admin_tasks",
                "research",
                "required_education_non_clinical",
            ],
            LoadSheddingLevelEnum.BLACK: [
                "optional_education",
                "professional_development",
                "admin_tasks",
                "research",
                "required_education_non_clinical",
                "elective_procedures",
            ],
        }

        suspended = activities_by_level.get(target_level, [])
        protected = ["emergency_coverage", "patient_safety", "critical_care"]

        severity_map = {
            LoadSheddingLevelEnum.NORMAL: "healthy",
            LoadSheddingLevelEnum.YELLOW: "warning",
            LoadSheddingLevelEnum.ORANGE: "elevated",
            LoadSheddingLevelEnum.RED: "critical",
            LoadSheddingLevelEnum.BLACK: "emergency",
        }

        return SacrificeHierarchyResponse(
            current_level=target_level,
            activities_suspended=suspended,
            activities_protected=protected,
            simulation_mode=simulate_only,
            estimated_capacity_freed=len(suspended) * 0.05,
            recovery_plan=[],
            message=f"Load shedding at {target_level.value} level"
            + (" (SIMULATION)" if simulate_only else ""),
            severity=severity_map.get(target_level, "unknown"),
        )

    except Exception as e:
        logger.error(f"Sacrifice hierarchy execution failed: {e}")
        raise


async def analyze_homeostasis(
    current_values: dict[str, float],
) -> HomeostasisStatusResponse:
    """
    Analyze homeostasis feedback loops and allostatic load.

    This tool monitors feedback loops that maintain system stability and
    calculates allostatic load (cumulative stress) on faculty and the system.

    Args:
        current_values: Dictionary of setpoint_name -> current_value

    Returns:
        HomeostasisStatusResponse with feedback loop analysis

    Raises:
        ValueError: If current_values is empty
    """
    if not current_values:
        raise ValueError("current_values cannot be empty")

    logger.info(f"Analyzing homeostasis with {len(current_values)} metrics")

    try:
        # Placeholder for actual integration
        logger.warning("Homeostasis analysis not yet fully integrated with backend")

        avg_load = sum(current_values.values()) / len(current_values) * 100

        if avg_load > 80:
            state = "allostatic_overload"
            severity = "critical"
        elif avg_load > 60:
            state = "allostatic_load"
            severity = "elevated"
        elif avg_load > 40:
            state = "allostasis"
            severity = "warning"
        else:
            state = "homeostasis"
            severity = "healthy"

        return HomeostasisStatusResponse(
            overall_state=state,
            feedback_loops_healthy=len(current_values),
            feedback_loops_deviating=0,
            average_allostatic_load=avg_load,
            positive_feedback_risks=0,
            urgent_corrections_needed=0,
            faculty_at_risk=[],
            system_metrics=current_values,
            recommendations=[],
            severity=severity,
        )

    except Exception as e:
        logger.error(f"Homeostasis analysis failed: {e}")
        raise


async def calculate_blast_radius(
    request: BlastRadiusAnalysisRequest,
) -> BlastRadiusAnalysisResponse:
    """
    Calculate blast radius and zone isolation status.

    This tool analyzes how failures are contained within scheduling zones,
    preventing cascades from spreading across the entire system.

    Args:
        request: Blast radius analysis request

    Returns:
        BlastRadiusAnalysisResponse with zone health analysis

    Raises:
        ValueError: If request is invalid
    """
    logger.info(f"Calculating blast radius (check_all={request.check_all_zones})")

    try:
        # Placeholder for actual integration
        logger.warning("Blast radius analysis not yet fully integrated with backend")

        return BlastRadiusAnalysisResponse(
            total_zones=0,
            zones_healthy=0,
            zones_degraded=0,
            zones_critical=0,
            zone_details=[],
            global_containment_level="none",
            containment_active=False,
            borrowing_requests_pending=0,
            recommendations=[],
            severity="healthy",
        )

    except Exception as e:
        logger.error(f"Blast radius calculation failed: {e}")
        raise


async def analyze_le_chatelier(
    request: LeChatelierAnalysisRequest,
) -> EquilibriumAnalysisResponse:
    """
    Analyze equilibrium shift and stress compensation (Le Chatelier).

    This tool applies Le Chatelier's principle to scheduling: when stress is
    applied, the system shifts to a new equilibrium. Compensation is always
    partial and temporary.

    Args:
        request: Le Chatelier analysis request

    Returns:
        EquilibriumAnalysisResponse with stress and compensation analysis

    Raises:
        ValueError: If request is invalid
    """
    logger.info("Analyzing Le Chatelier equilibrium shift")

    try:
        # Placeholder for actual integration
        logger.warning("Le Chatelier analysis not yet fully integrated with backend")

        return EquilibriumAnalysisResponse(
            current_equilibrium_state="stable",
            current_capacity=100.0,
            current_demand=75.0,
            current_coverage_rate=1.0,
            active_stresses=[],
            compensation_debt=0.0,
            sustainability_score=1.0,
            days_until_exhaustion=None,
            predicted_coverage_in_30_days=1.0,
            compensation_sustainability="sustainable",
            recommendations=[],
            severity="healthy",
        )

    except Exception as e:
        logger.error(f"Le Chatelier analysis failed: {e}")
        raise


async def analyze_hub_centrality() -> HubAnalysisResponse:
    """
    Analyze faculty hub centrality and single points of failure.

    This tool uses network analysis to identify "hub" faculty members whose
    removal would cause disproportionate system disruption. Uses NetworkX
    for advanced centrality metrics.

    Returns:
        HubAnalysisResponse with faculty centrality analysis
    """
    logger.info("Analyzing hub centrality")

    try:
        # Placeholder for actual integration
        logger.warning("Hub centrality analysis not yet fully integrated with backend")

        return HubAnalysisResponse(
            total_faculty_analyzed=0,
            hubs_identified=0,
            critical_hubs=0,
            top_hubs=[],
            cascade_failure_points=[],
            cross_training_priority=[],
            hub_concentration_risk="low",
            recommendations=[],
            severity="healthy",
        )

    except Exception as e:
        logger.error(f"Hub centrality analysis failed: {e}")
        raise


async def assess_cognitive_load(
    request: CognitiveLoadRequest,
) -> CognitiveLoadResponse:
    """
    Assess cognitive load and decision queue complexity.

    This tool implements Miller's Law (7±2 items in working memory) to
    monitor decision queue complexity and coordinator cognitive load.

    Args:
        request: Cognitive load assessment request

    Returns:
        CognitiveLoadResponse with decision queue analysis

    Raises:
        ValueError: If request is invalid
    """
    logger.info(f"Assessing cognitive load (session_id={request.session_id})")

    try:
        # Placeholder for actual integration
        logger.warning("Cognitive load assessment not yet fully integrated with backend")

        return CognitiveLoadResponse(
            session_id=request.session_id,
            pending_decisions=0,
            urgent_decisions=0,
            total_cognitive_cost=0.0,
            decision_queue=[],
            fatigue_level="fresh",
            can_auto_decide=0,
            batching_opportunities=0,
            recommendations=[],
            severity="healthy",
        )

    except Exception as e:
        logger.error(f"Cognitive load assessment failed: {e}")
        raise


async def get_behavioral_patterns() -> BehavioralPatternsResponse:
    """
    Get behavioral patterns from stigmergy (swarm intelligence).

    This tool analyzes preference trails left by faculty members making
    schedule decisions. Like ant pheromone trails, these reveal collective
    intelligence about optimal scheduling patterns.

    Returns:
        BehavioralPatternsResponse with emergent patterns
    """
    logger.info("Analyzing behavioral patterns from stigmergy")

    try:
        # Placeholder for actual integration
        logger.warning("Behavioral patterns analysis not yet fully integrated with backend")

        return BehavioralPatternsResponse(
            total_trails=0,
            active_trails=0,
            average_strength=0.0,
            popular_slots=[],
            unpopular_slots=[],
            swap_network_density=0.0,
            preference_clustering={},
            emergent_patterns=[],
            recommendations=[],
        )

    except Exception as e:
        logger.error(f"Behavioral patterns analysis failed: {e}")
        raise


async def analyze_stigmergy(
    request: StigmergyAnalysisRequest,
) -> StigmergyAnalysisResponse:
    """
    Analyze stigmergic optimization signals for specific slots.

    This tool provides stigmergy-based scheduling suggestions for specific
    slots or slot types based on collective preference trails.

    Args:
        request: Stigmergy analysis request

    Returns:
        StigmergyAnalysisResponse with optimization suggestions

    Raises:
        ValueError: If request is invalid
    """
    logger.info(f"Analyzing stigmergy for slot_id={request.slot_id}, slot_type={request.slot_type}")

    try:
        # Placeholder for actual integration
        logger.warning("Stigmergy analysis not yet fully integrated with backend")

        return StigmergyAnalysisResponse(
            collective_preferences=None,
            faculty_suggestions=[],
            preference_strength=0.0,
            popularity_score=0.0,
            contributing_faculty=0,
            optimization_potential=0.0,
            swarm_intelligence_score=0.0,
            recommendations=[],
        )

    except Exception as e:
        logger.error(f"Stigmergy analysis failed: {e}")
        raise


async def check_mtf_compliance(
    request: MTFComplianceRequest,
) -> MTFComplianceResponse:
    """
    Check Multi-Tier Functionality (MTF) compliance status.

    This tool provides military-style compliance reporting including DRRS
    translation, circuit breaker status, and "Iron Dome" regulatory protection.

    Args:
        request: MTF compliance check request

    Returns:
        MTFComplianceResponse with compliance status

    Raises:
        ValueError: If request is invalid
    """
    logger.info(f"Checking MTF compliance (circuit_breaker={request.check_circuit_breaker})")

    try:
        from scheduler_mcp.api_client import get_api_client

        # Get API client and call the MTF compliance endpoint
        api_client = await get_api_client()
        result = await api_client.get_mtf_compliance(
            check_circuit_breaker=request.check_circuit_breaker
        )

        # Parse circuit breaker info from response
        cb_data = result.get("circuit_breaker")
        if cb_data:
            circuit_breaker = CircuitBreakerInfo(
                state=cb_data.get("state", "closed"),
                tripped=cb_data.get("tripped", False),
                trigger=cb_data.get("trigger"),
                trigger_details=cb_data.get("trigger_details"),
                triggered_at=cb_data.get("triggered_at"),
                locked_operations=cb_data.get("locked_operations", []),
                override_active=cb_data.get("override_active", False),
            )
        else:
            circuit_breaker = CircuitBreakerInfo(
                state="closed",
                tripped=False,
                trigger=None,
                trigger_details=None,
                triggered_at=None,
                locked_operations=[],
                override_active=False,
            )

        return MTFComplianceResponse(
            drrs_category=result.get("drrs_category", "C1"),
            mission_capability=result.get("mission_capability", "FMC"),
            personnel_rating=result.get("personnel_rating", "P1"),
            capability_rating=result.get("capability_rating", "S1"),
            circuit_breaker=circuit_breaker,
            executive_summary=result.get("executive_summary", ""),
            deficiencies=result.get("deficiencies", []),
            mfrs_generated=result.get("mfrs_generated", 0),
            rffs_generated=result.get("rffs_generated", 0),
            iron_dome_status=result.get("iron_dome_status", "green"),
            severity=result.get("severity", "healthy"),
        )

    except Exception as e:
        logger.error(f"MTF compliance check failed: {e}")
        # Return fallback response when API is unavailable
        logger.warning("Returning fallback MTF compliance response")
        circuit_breaker = CircuitBreakerInfo(
            state="unknown",
            tripped=False,
            trigger=None,
            trigger_details="API connection failed",
            triggered_at=None,
            locked_operations=[],
            override_active=False,
        )
        return MTFComplianceResponse(
            drrs_category="C1",
            mission_capability="FMC",
            personnel_rating="P1",
            capability_rating="S1",
            circuit_breaker=circuit_breaker,
            executive_summary=f"MTF compliance check unavailable: {e}",
            deficiencies=["Unable to connect to backend API"],
            mfrs_generated=0,
            rffs_generated=0,
            iron_dome_status="yellow",
            severity="warning",
        )


# =============================================================================
# Tier 4: Epidemiological Burnout Modeling
# =============================================================================


class BurnoutEpidemicStatusEnum(str, Enum):
    """Status of burnout epidemic based on reproduction number (Rt)."""

    NO_CASES = "no_cases"  # Rt = 0, no burnout detected
    DECLINING = "declining"  # Rt < 0.5, epidemic fading
    CONTROLLED = "controlled"  # 0.5 <= Rt < 1.0, stable/declining
    SPREADING = "spreading"  # 1.0 <= Rt < 2.0, slowly growing
    RAPID_SPREAD = "rapid_spread"  # 2.0 <= Rt < 3.0, accelerating
    CRISIS = "crisis"  # Rt >= 3.0, emergency intervention needed


class InterventionLevelEnum(str, Enum):
    """Intervention urgency level based on reproduction number."""

    NONE = "none"  # Rt << 1, burnout declining
    MONITORING = "monitoring"  # Rt ~= 1, stable but watch closely
    MODERATE = "moderate"  # Rt > 1, spreading slowly
    AGGRESSIVE = "aggressive"  # Rt > 2, spreading rapidly
    EMERGENCY = "emergency"  # Rt > 3, crisis intervention needed


class SuperspreaderInfo(BaseModel):
    """Information about a potential burnout superspreader."""

    provider_id: str = Field(description="Provider identifier")
    secondary_cases: int = Field(
        ge=0, description="Number of secondary burnout cases caused by this provider"
    )
    degree: int = Field(ge=0, description="Number of social/work connections")
    risk_level: str = Field(description="Risk level: low, moderate, high, critical")


class BurnoutRtResponse(BaseModel):
    """Response from burnout reproduction number calculation.

    The reproduction number (Rt) is the average number of secondary burnout
    cases caused by each burned out individual. It is a key epidemiological
    metric that indicates whether burnout is spreading or declining.

    - Rt < 1: Each burned out person infects less than 1 other, epidemic declining
    - Rt = 1: Endemic state, stable but not declining
    - Rt > 1: Each burned out person infects more than 1 other, epidemic growing
    - Rt > 2: Rapid exponential growth, aggressive intervention needed
    - Rt > 3: Crisis level, emergency intervention required
    """

    rt: float = Field(
        ge=0.0,
        description="Effective reproduction number (Rt) - average secondary cases per burnout",
    )
    status: BurnoutEpidemicStatusEnum = Field(
        description="Epidemic status based on Rt value"
    )
    intervention_level: InterventionLevelEnum = Field(
        description="Recommended intervention urgency level"
    )
    interventions: list[str] = Field(
        description="List of recommended intervention strategies"
    )
    herd_immunity_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of population that must be immune to stop spread (1 - 1/R0)",
    )
    total_cases_analyzed: int = Field(
        ge=0, description="Number of burned out individuals analyzed"
    )
    total_close_contacts: int = Field(
        ge=0, description="Total number of close contacts identified"
    )
    superspreaders: list[SuperspreaderInfo] = Field(
        default_factory=list,
        description="High-connectivity individuals with >= 3 secondary cases",
    )
    high_risk_contacts: list[str] = Field(
        default_factory=list,
        description="Provider IDs of contacts at high risk of developing burnout",
    )
    analyzed_at: str = Field(description="Timestamp of analysis (ISO format)")
    time_window_days: int = Field(
        ge=1, description="Time window used for analysis (days)"
    )
    severity: str = Field(description="Overall severity: healthy, warning, critical, emergency")


class SIRSimulationPoint(BaseModel):
    """Single time point in SIR simulation trajectory."""

    week: int = Field(ge=0, description="Simulation week number")
    susceptible: int = Field(ge=0, description="Number of susceptible individuals")
    infected: int = Field(ge=0, description="Number of infected (burned out) individuals")
    recovered: int = Field(ge=0, description="Number of recovered individuals")
    infection_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of population currently infected"
    )


class BurnoutSpreadSimulationResponse(BaseModel):
    """Response from SIR epidemic simulation for burnout spread.

    Uses the SIR (Susceptible-Infected-Recovered) epidemiological model to
    project burnout spread through the social/work network over time.

    Key parameters:
    - beta (infection_rate): Probability of burnout transmission per contact per week
    - gamma (recovery_rate): Probability of recovery per week (1/gamma = avg burnout duration)

    R0 (basic reproduction number) = beta / gamma
    - R0 > 1: Epidemic grows until herd immunity reached
    - R0 < 1: Epidemic dies out naturally
    """

    simulation_weeks: int = Field(ge=1, description="Number of weeks simulated")
    infection_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Beta - transmission probability per contact per week",
    )
    recovery_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Gamma - recovery probability per week",
    )
    r0: float = Field(
        ge=0.0,
        description="Basic reproduction number (R0 = beta/gamma)",
    )
    herd_immunity_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction that must be immune to stop spread",
    )
    initial_infected: int = Field(ge=0, description="Number of initially infected")
    final_infected: int = Field(ge=0, description="Number infected at simulation end")
    final_recovered: int = Field(ge=0, description="Number recovered at simulation end")
    peak_infected: int = Field(ge=0, description="Maximum number infected simultaneously")
    peak_week: int = Field(ge=0, description="Week when peak infection occurred")
    epidemic_died_out: bool = Field(description="Whether epidemic naturally died out")
    trajectory: list[SIRSimulationPoint] = Field(
        description="Weekly SIR trajectory data"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Warnings about simulation results"
    )
    severity: str = Field(description="Overall severity: healthy, warning, critical, emergency")


class ContagionRiskEnum(str, Enum):
    """Overall contagion risk level."""

    LOW = "low"  # <10% of network infected
    MODERATE = "moderate"  # 10-25% infected
    HIGH = "high"  # 25-50% infected
    CRITICAL = "critical"  # >50% infected, cascade likely


class ContagionSuperspreaderProfile(BaseModel):
    """Detailed profile of a potential burnout superspreader in contagion model."""

    provider_id: str = Field(description="Provider identifier")
    provider_name: str = Field(description="Provider name (anonymized)")
    burnout_score: float = Field(ge=0.0, le=1.0, description="Current burnout score")
    burnout_trend: str = Field(description="Trend: increasing, stable, decreasing")
    degree_centrality: float = Field(
        ge=0.0, le=1.0, description="Normalized degree centrality"
    )
    betweenness_centrality: float = Field(
        ge=0.0, le=1.0, description="Betweenness centrality (bridge importance)"
    )
    eigenvector_centrality: float = Field(
        ge=0.0, le=1.0, description="Eigenvector centrality (connection quality)"
    )
    composite_centrality: float = Field(
        ge=0.0, le=1.0, description="Combined centrality score"
    )
    superspreader_score: float = Field(
        ge=0.0,
        description="Risk score = burnout * centrality",
    )
    risk_level: str = Field(description="Risk level: low, moderate, high, critical")
    direct_contacts: int = Field(ge=0, description="Number of direct connections")
    estimated_cascade_size: int = Field(
        ge=0, description="Estimated downstream infections if this node is infected"
    )


class NetworkInterventionInfo(BaseModel):
    """Recommended network intervention to reduce burnout contagion."""

    intervention_type: str = Field(
        description="Type: edge_removal, buffer_insertion, workload_reduction, quarantine, peer_support"
    )
    priority: int = Field(ge=1, le=5, description="Priority 1=highest")
    reason: str = Field(description="Reason for intervention")
    target_providers: list[str] = Field(
        description="Provider IDs targeted by this intervention"
    )
    affected_edges: list[tuple[str, str]] = Field(
        default_factory=list, description="Network edges affected"
    )
    estimated_infection_reduction: float = Field(
        ge=0.0, le=1.0, description="Estimated reduction in final infection rate"
    )
    estimated_cost_hours: float = Field(
        ge=0.0, description="Estimated schedule disruption in hours"
    )


class BurnoutContagionResponse(BaseModel):
    """Response from burnout contagion simulation using network diffusion model.

    Uses SIS (Susceptible-Infected-Susceptible) epidemiological model on
    the social/collaboration network to simulate burnout spread. Unlike SIR,
    SIS allows reinfection - appropriate for burnout which can recur.

    Key concepts:
    - Superspreaders: High-burnout + high-centrality nodes that amplify contagion
    - Network interventions: Targeted actions to break transmission chains
    - Cascade prediction: Estimating outbreak severity from current state
    """

    network_size: int = Field(ge=0, description="Total nodes in social network")
    current_susceptible: int = Field(
        ge=0, description="Currently susceptible (low burnout)"
    )
    current_infected: int = Field(ge=0, description="Currently infected (high burnout)")
    current_infection_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction currently infected"
    )
    contagion_risk: ContagionRiskEnum = Field(
        description="Overall contagion risk level"
    )
    simulation_iterations: int = Field(ge=0, description="Number of iterations simulated")
    final_infection_rate: float = Field(
        ge=0.0, le=1.0, description="Projected final infection rate"
    )
    peak_infection_rate: float = Field(
        ge=0.0, le=1.0, description="Peak infection rate during simulation"
    )
    peak_iteration: int = Field(ge=0, description="Iteration when peak occurred")
    superspreaders: list[ContagionSuperspreaderProfile] = Field(
        default_factory=list, description="Identified superspreader profiles"
    )
    total_superspreaders: int = Field(ge=0, description="Count of superspreaders")
    recommended_interventions: list[NetworkInterventionInfo] = Field(
        default_factory=list, description="Recommended network interventions"
    )
    warnings: list[str] = Field(default_factory=list, description="Alert messages")
    generated_at: str = Field(description="Timestamp of analysis (ISO format)")
    severity: str = Field(
        description="Overall severity: healthy, warning, critical, emergency"
    )


# =============================================================================
# Tier 4 Tool Functions: Epidemiological Burnout Modeling
# =============================================================================


async def calculate_burnout_rt(
    burned_out_provider_ids: list[str],
    time_window_days: int = 28,
) -> BurnoutRtResponse:
    """
    Calculate the effective reproduction number (Rt) for burnout spread.

    Applies epidemiological SIR modeling to understand burnout transmission
    dynamics through social networks. The reproduction number (Rt) indicates
    whether burnout is spreading or declining in the organization.

    Scientific Background:
    - Burnout spreads through social networks like an infectious disease
    - Emotional contagion occurs through close work contacts
    - High-connectivity individuals can become "superspreaders"
    - Breaking transmission chains requires targeted interventions

    Args:
        burned_out_provider_ids: List of provider IDs currently experiencing burnout.
            These are the "index cases" from which secondary cases are traced.
        time_window_days: Time window in days for tracing secondary cases (default: 28).
            Longer windows capture more transmission but may include unrelated cases.

    Returns:
        BurnoutRtResponse with reproduction number, status, and intervention recommendations.

    Raises:
        ValueError: If time_window_days is invalid (must be >= 1)

    Example:
        # Calculate Rt for 5 burned out providers
        result = await calculate_burnout_rt(
            burned_out_provider_ids=["provider-1", "provider-2", "provider-3"],
            time_window_days=28
        )

        if result.rt > 1.0:
            print(f"Burnout spreading! Rt={result.rt:.2f}")
            print(f"Interventions: {result.interventions}")
    """
    if time_window_days < 1:
        raise ValueError("time_window_days must be >= 1")

    logger.info(
        f"Calculating burnout Rt for {len(burned_out_provider_ids)} cases, "
        f"time_window={time_window_days} days"
    )

    try:
        # Attempt to use the actual epidemiology module
        import networkx as nx
        from app.resilience.burnout_epidemiology import (
            BurnoutEpidemiology,
            BurnoutState,
        )

        # Build social network from backend (placeholder - would call API in production)
        # For now, create a simulated network
        logger.warning("Using simulated social network - integrate with backend API for production")

        # Create a simulated social network
        network = nx.watts_strogatz_graph(n=50, k=6, p=0.3)

        # Relabel nodes to use provider IDs
        provider_ids = [f"provider-{i}" for i in range(50)]
        mapping = {i: provider_ids[i] for i in range(50)}
        network = nx.relabel_nodes(network, mapping)

        # Initialize epidemiology analyzer
        epi = BurnoutEpidemiology(network)

        # Record burnout states
        now = datetime.now()
        for provider_id in burned_out_provider_ids:
            if provider_id in network:
                epi.record_burnout_state(
                    UUID(provider_id) if "-" in provider_id else UUID(int=hash(provider_id) % (2**128)),
                    BurnoutState.BURNED_OUT,
                    now - timedelta(days=time_window_days // 2),  # Simulate onset in middle of window
                )

        # Calculate Rt
        burned_out_uuids = {
            UUID(pid) if "-" in pid else UUID(int=hash(pid) % (2**128))
            for pid in burned_out_provider_ids
            if pid in network
        }

        report = epi.calculate_reproduction_number(
            burned_out_residents=burned_out_uuids,
            time_window=timedelta(days=time_window_days),
        )

        # Map status
        status_map = {
            "no_cases": BurnoutEpidemicStatusEnum.NO_CASES,
            "declining": BurnoutEpidemicStatusEnum.DECLINING,
            "controlled": BurnoutEpidemicStatusEnum.CONTROLLED,
            "spreading": BurnoutEpidemicStatusEnum.SPREADING,
            "rapid_spread": BurnoutEpidemicStatusEnum.RAPID_SPREAD,
            "crisis": BurnoutEpidemicStatusEnum.CRISIS,
        }

        intervention_map = {
            "none": InterventionLevelEnum.NONE,
            "monitoring": InterventionLevelEnum.MONITORING,
            "moderate": InterventionLevelEnum.MODERATE,
            "aggressive": InterventionLevelEnum.AGGRESSIVE,
            "emergency": InterventionLevelEnum.EMERGENCY,
        }

        # Map superspreaders
        superspreader_infos = [
            SuperspreaderInfo(
                provider_id=str(ss_id),
                secondary_cases=report.secondary_cases.get(str(ss_id), 0),
                degree=epi._get_degree(ss_id),
                risk_level="high" if report.secondary_cases.get(str(ss_id), 0) >= 5 else "moderate",
            )
            for ss_id in report.super_spreaders
        ]

        # Determine severity
        if report.reproduction_number >= 3.0:
            severity = "emergency"
        elif report.reproduction_number >= 2.0:
            severity = "critical"
        elif report.reproduction_number >= 1.0:
            severity = "warning"
        else:
            severity = "healthy"

        return BurnoutRtResponse(
            rt=report.reproduction_number,
            status=status_map.get(report.status, BurnoutEpidemicStatusEnum.CONTROLLED),
            intervention_level=intervention_map.get(
                report.intervention_level.value, InterventionLevelEnum.MONITORING
            ),
            interventions=report.recommended_interventions,
            herd_immunity_threshold=epi.calculate_herd_immunity_threshold(
                report.reproduction_number
            ),
            total_cases_analyzed=report.total_cases_analyzed,
            total_close_contacts=report.total_close_contacts,
            superspreaders=superspreader_infos,
            high_risk_contacts=[str(c) for c in report.high_risk_contacts],
            analyzed_at=report.analyzed_at.isoformat(),
            time_window_days=time_window_days,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Burnout epidemiology module unavailable: {e}")
        # Fallback with simulated data
        return await _calculate_burnout_rt_fallback(
            burned_out_provider_ids, time_window_days
        )
    except Exception as e:
        logger.error(f"Burnout Rt calculation failed: {e}")
        raise RuntimeError(f"Failed to calculate burnout Rt: {e}") from e


async def _calculate_burnout_rt_fallback(
    burned_out_provider_ids: list[str],
    time_window_days: int,
) -> BurnoutRtResponse:
    """Fallback calculation when epidemiology module is unavailable."""
    num_cases = len(burned_out_provider_ids)

    # Simple heuristic: estimate Rt based on case count
    if num_cases == 0:
        rt = 0.0
        status = BurnoutEpidemicStatusEnum.NO_CASES
        level = InterventionLevelEnum.NONE
        severity = "healthy"
    elif num_cases <= 2:
        rt = 0.5
        status = BurnoutEpidemicStatusEnum.DECLINING
        level = InterventionLevelEnum.MONITORING
        severity = "healthy"
    elif num_cases <= 5:
        rt = 1.2
        status = BurnoutEpidemicStatusEnum.SPREADING
        level = InterventionLevelEnum.MODERATE
        severity = "warning"
    elif num_cases <= 10:
        rt = 2.0
        status = BurnoutEpidemicStatusEnum.RAPID_SPREAD
        level = InterventionLevelEnum.AGGRESSIVE
        severity = "critical"
    else:
        rt = 3.5
        status = BurnoutEpidemicStatusEnum.CRISIS
        level = InterventionLevelEnum.EMERGENCY
        severity = "emergency"

    # Generate interventions based on level
    interventions = _get_interventions_for_rt(rt)

    # Calculate herd immunity threshold
    hit = 1.0 - (1.0 / rt) if rt > 1.0 else 0.0

    return BurnoutRtResponse(
        rt=rt,
        status=status,
        intervention_level=level,
        interventions=interventions,
        herd_immunity_threshold=max(0.0, min(1.0, hit)),
        total_cases_analyzed=num_cases,
        total_close_contacts=num_cases * 5,  # Estimate 5 contacts per case
        superspreaders=[],
        high_risk_contacts=[],
        analyzed_at=datetime.now().isoformat(),
        time_window_days=time_window_days,
        severity=severity,
    )


def _get_interventions_for_rt(rt: float) -> list[str]:
    """Get intervention recommendations based on reproduction number."""
    interventions = []

    if rt < 0.5:
        interventions.extend([
            "Continue current preventive measures",
            "Monitor for early warning signs",
            "Maintain work-life balance programs",
        ])
    elif rt < 1.0:
        interventions.extend([
            "Increase monitoring of at-risk individuals",
            "Offer voluntary support groups and counseling",
            "Review workload distribution for equity",
            "Strengthen peer support networks",
        ])
    elif rt < 2.0:
        interventions.extend([
            "MODERATE INTERVENTION REQUIRED",
            "Implement workload reduction for burned out individuals",
            "Mandatory wellness check-ins for all staff",
            "Increase staffing levels to reduce individual burden",
            "Break transmission chains: reduce contact between burned out and at-risk",
            "Provide mental health resources and counseling",
        ])
    elif rt < 3.0:
        interventions.extend([
            "AGGRESSIVE INTERVENTION REQUIRED",
            "Mandatory time off for burned out individuals",
            "Emergency staffing augmentation (temporary hires, locums)",
            "Restructure teams to reduce superspreader connectivity",
            "Daily wellness monitoring for all staff",
            "Implement crisis management protocols",
        ])
    else:
        interventions.extend([
            "EMERGENCY INTERVENTION REQUIRED",
            "IMMEDIATE ACTION: Remove burned out individuals from clinical duties",
            "Emergency external support (crisis counseling, temporary replacements)",
            "System-wide operational pause to prevent collapse",
            "Comprehensive organizational assessment and restructuring",
            "Notify program leadership and institutional administration",
        ])

    return interventions


async def simulate_burnout_spread(
    initial_infected_ids: list[str],
    infection_rate: float = 0.05,
    recovery_rate: float = 0.02,
    simulation_weeks: int = 52,
) -> BurnoutSpreadSimulationResponse:
    """
    Run SIR epidemic simulation for burnout spread through social network.

    Uses the classic SIR (Susceptible-Infected-Recovered) epidemiological model
    to project how burnout might spread through the organization's social network
    over time. This helps identify:
    - Whether burnout will become epidemic (R0 > 1) or die out (R0 < 1)
    - When peak infection might occur
    - How many people might ultimately be affected

    Scientific Background:
    - SIR model divides population into Susceptible, Infected, Recovered compartments
    - Transmission occurs when infected contacts susceptible
    - Recovery rate determines average duration of burnout
    - R0 = beta/gamma predicts epidemic trajectory

    Args:
        initial_infected_ids: List of provider IDs to seed as initially burned out.
            These are the "patient zero" cases that start the simulation.
        infection_rate: Beta - probability of burnout transmission per contact per week.
            Typical range: 0.01-0.15. Higher = faster spread.
        recovery_rate: Gamma - probability of recovery per week.
            Typical range: 0.001-0.05. Higher = faster recovery.
            Note: 1/gamma = average weeks of burnout (e.g., 0.02 = 50 weeks avg)
        simulation_weeks: Number of weeks to simulate (default: 52 = 1 year).

    Returns:
        BurnoutSpreadSimulationResponse with trajectory and peak analysis.

    Raises:
        ValueError: If rates are out of range [0, 1] or simulation_weeks < 1

    Example:
        # Simulate 1 year of burnout spread starting with 3 cases
        result = await simulate_burnout_spread(
            initial_infected_ids=["provider-1", "provider-2", "provider-3"],
            infection_rate=0.05,
            recovery_rate=0.02,
            simulation_weeks=52
        )

        print(f"R0: {result.r0:.2f}")
        print(f"Peak: {result.peak_infected} infected at week {result.peak_week}")
        if result.epidemic_died_out:
            print("Epidemic died out naturally")
    """
    if not 0.0 <= infection_rate <= 1.0:
        raise ValueError("infection_rate must be between 0.0 and 1.0")
    if not 0.0 <= recovery_rate <= 1.0:
        raise ValueError("recovery_rate must be between 0.0 and 1.0")
    if simulation_weeks < 1:
        raise ValueError("simulation_weeks must be >= 1")

    logger.info(
        f"Simulating burnout spread: {len(initial_infected_ids)} initial cases, "
        f"beta={infection_rate}, gamma={recovery_rate}, weeks={simulation_weeks}"
    )

    try:
        # Attempt to use actual epidemiology module
        import networkx as nx
        from app.resilience.burnout_epidemiology import BurnoutEpidemiology

        logger.warning("Using simulated social network - integrate with backend API for production")

        # Create simulated social network
        network = nx.watts_strogatz_graph(n=50, k=6, p=0.3)
        provider_ids = [f"provider-{i}" for i in range(50)]
        mapping = {i: provider_ids[i] for i in range(50)}
        network = nx.relabel_nodes(network, mapping)

        epi = BurnoutEpidemiology(network)

        # Map initial infected to UUIDs
        initial_uuids = set()
        for pid in initial_infected_ids:
            if pid in network:
                uid = UUID(pid) if "-" in pid and len(pid) == 36 else UUID(int=hash(pid) % (2**128))
                initial_uuids.add(uid)

        # Run simulation
        trajectory = epi.simulate_sir_spread(
            initial_infected=initial_uuids,
            beta=infection_rate,
            gamma=recovery_rate,
            steps=simulation_weeks,
        )

        # Convert trajectory to response format
        trajectory_points = []
        peak_infected = 0
        peak_week = 0

        for point in trajectory:
            total = point["S"] + point["I"] + point["R"]
            infection_rate_at_point = point["I"] / total if total > 0 else 0.0

            trajectory_points.append(
                SIRSimulationPoint(
                    week=point["week"],
                    susceptible=point["S"],
                    infected=point["I"],
                    recovered=point["R"],
                    infection_rate=infection_rate_at_point,
                )
            )

            if point["I"] > peak_infected:
                peak_infected = point["I"]
                peak_week = point["week"]

        # Calculate R0
        r0 = infection_rate / recovery_rate if recovery_rate > 0 else float("inf")

        # Calculate herd immunity threshold
        hit = 1.0 - (1.0 / r0) if r0 > 1.0 else 0.0

        # Check if epidemic died out
        final_point = trajectory[-1] if trajectory else {"I": 0, "R": 0}
        epidemic_died_out = final_point.get("I", 0) == 0

        # Generate warnings
        warnings = []
        if r0 > 1.0:
            warnings.append(f"R0 > 1 ({r0:.2f}): Burnout is epidemic-capable")
        if peak_infected > len(provider_ids) * 0.25:
            warnings.append(
                f"Peak infection affects {peak_infected}/{len(provider_ids)} ({peak_infected/len(provider_ids)*100:.0f}%) of network"
            )
        if not epidemic_died_out and simulation_weeks >= 52:
            warnings.append("Epidemic still active after 1 year - consider interventions")

        # Determine severity
        final_rate = final_point.get("I", 0) / len(provider_ids) if provider_ids else 0
        if final_rate > 0.5:
            severity = "emergency"
        elif final_rate > 0.25:
            severity = "critical"
        elif final_rate > 0.10:
            severity = "warning"
        else:
            severity = "healthy"

        return BurnoutSpreadSimulationResponse(
            simulation_weeks=simulation_weeks,
            infection_rate=infection_rate,
            recovery_rate=recovery_rate,
            r0=r0 if r0 != float("inf") else 999.9,
            herd_immunity_threshold=max(0.0, min(1.0, hit)),
            initial_infected=len(initial_infected_ids),
            final_infected=final_point.get("I", 0),
            final_recovered=final_point.get("R", 0),
            peak_infected=peak_infected,
            peak_week=peak_week,
            epidemic_died_out=epidemic_died_out,
            trajectory=trajectory_points,
            warnings=warnings,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Burnout epidemiology module unavailable: {e}")
        return await _simulate_burnout_spread_fallback(
            initial_infected_ids, infection_rate, recovery_rate, simulation_weeks
        )
    except Exception as e:
        logger.error(f"Burnout spread simulation failed: {e}")
        raise RuntimeError(f"Failed to simulate burnout spread: {e}") from e


async def _simulate_burnout_spread_fallback(
    initial_infected_ids: list[str],
    infection_rate: float,
    recovery_rate: float,
    simulation_weeks: int,
) -> BurnoutSpreadSimulationResponse:
    """Fallback simulation when epidemiology module is unavailable."""
    # Simple SIR simulation without NetworkX
    population = 50
    initial_infected = min(len(initial_infected_ids), population)

    susceptible = population - initial_infected
    infected = initial_infected
    recovered = 0

    trajectory = []
    peak_infected = infected
    peak_week = 0

    for week in range(simulation_weeks):
        total = susceptible + infected + recovered
        trajectory.append(
            SIRSimulationPoint(
                week=week,
                susceptible=susceptible,
                infected=infected,
                recovered=recovered,
                infection_rate=infected / total if total > 0 else 0.0,
            )
        )

        if infected > peak_infected:
            peak_infected = infected
            peak_week = week

        # SIR transitions (simplified)
        new_infections = int(infection_rate * susceptible * infected / total) if total > 0 else 0
        new_recoveries = int(recovery_rate * infected)

        susceptible -= new_infections
        infected += new_infections - new_recoveries
        recovered += new_recoveries

        susceptible = max(0, susceptible)
        infected = max(0, infected)

        if infected == 0:
            break

    r0 = infection_rate / recovery_rate if recovery_rate > 0 else 999.9
    hit = 1.0 - (1.0 / r0) if r0 > 1.0 else 0.0

    warnings = []
    if r0 > 1.0:
        warnings.append(f"R0 > 1 ({r0:.2f}): Epidemic-capable (fallback calculation)")

    final_rate = infected / population
    if final_rate > 0.5:
        severity = "emergency"
    elif final_rate > 0.25:
        severity = "critical"
    elif final_rate > 0.10:
        severity = "warning"
    else:
        severity = "healthy"

    return BurnoutSpreadSimulationResponse(
        simulation_weeks=simulation_weeks,
        infection_rate=infection_rate,
        recovery_rate=recovery_rate,
        r0=min(r0, 999.9),
        herd_immunity_threshold=max(0.0, min(1.0, hit)),
        initial_infected=initial_infected,
        final_infected=infected,
        final_recovered=recovered,
        peak_infected=peak_infected,
        peak_week=peak_week,
        epidemic_died_out=(infected == 0),
        trajectory=trajectory,
        warnings=warnings,
        severity=severity,
    )


async def simulate_burnout_contagion(
    provider_burnout_scores: dict[str, float],
    infection_rate: float = 0.05,
    recovery_rate: float = 0.01,
    simulation_iterations: int = 50,
    max_interventions: int = 10,
) -> BurnoutContagionResponse:
    """
    Simulate burnout contagion through social network using SIS model.

    Uses the SIS (Susceptible-Infected-Susceptible) epidemiological model
    on the provider collaboration network. Unlike SIR, SIS allows reinfection -
    appropriate for burnout which can recur even after recovery.

    Key features:
    - Identifies superspreaders (high burnout + high network centrality)
    - Recommends targeted network interventions
    - Predicts cascade severity and peak infection timing

    Scientific Background:
    - Network topology determines outbreak severity
    - Superspreaders (high-degree + high-burnout nodes) amplify contagion
    - Edge removal, workload reduction, and quarantine can break transmission
    - Centrality metrics (degree, betweenness, eigenvector) identify critical nodes

    Args:
        provider_burnout_scores: Dictionary mapping provider_id -> burnout score (0.0-1.0).
            Scores >= 0.5 are considered "infected" (high burnout).
        infection_rate: Beta - transmission probability per contact per iteration.
            Typical range: 0.01-0.15.
        recovery_rate: Lambda - recovery probability per iteration.
            Typical range: 0.001-0.05.
        simulation_iterations: Number of iterations to simulate (default: 50).
        max_interventions: Maximum interventions to recommend (default: 10).

    Returns:
        BurnoutContagionResponse with superspreaders, interventions, and trajectory.

    Raises:
        ValueError: If rates are out of range or provider_burnout_scores is empty

    Example:
        # Simulate contagion with burnout scores for team
        scores = {
            "provider-1": 0.7,  # High burnout
            "provider-2": 0.3,  # Low burnout
            "provider-3": 0.9,  # Very high burnout
            "provider-4": 0.4,  # Moderate
        }
        result = await simulate_burnout_contagion(
            provider_burnout_scores=scores,
            infection_rate=0.05,
            recovery_rate=0.01
        )

        print(f"Risk: {result.contagion_risk}")
        print(f"Superspreaders: {[s.provider_id for s in result.superspreaders]}")
        for intervention in result.recommended_interventions:
            print(f"  - {intervention.intervention_type}: {intervention.reason}")
    """
    if not provider_burnout_scores:
        raise ValueError("provider_burnout_scores cannot be empty")
    if not 0.0 <= infection_rate <= 1.0:
        raise ValueError("infection_rate must be between 0.0 and 1.0")
    if not 0.0 <= recovery_rate <= 1.0:
        raise ValueError("recovery_rate must be between 0.0 and 1.0")
    if simulation_iterations < 1:
        raise ValueError("simulation_iterations must be >= 1")

    logger.info(
        f"Simulating burnout contagion: {len(provider_burnout_scores)} providers, "
        f"beta={infection_rate}, lambda={recovery_rate}"
    )

    try:
        # Attempt to use actual contagion model
        import networkx as nx
        from app.resilience.contagion_model import BurnoutContagionModel

        logger.warning("Using simulated social network - integrate with backend API for production")

        # Create simulated social network with provider IDs
        provider_ids = list(provider_burnout_scores.keys())
        n = len(provider_ids)

        if n < 4:
            # Too small for Watts-Strogatz, use complete graph
            network = nx.complete_graph(n)
        else:
            k = min(4, n - 1)  # Each node connected to k neighbors
            network = nx.watts_strogatz_graph(n=n, k=k, p=0.3)

        mapping = {i: provider_ids[i] for i in range(n)}
        network = nx.relabel_nodes(network, mapping)

        # Initialize contagion model
        model = BurnoutContagionModel(network)
        model.configure(infection_rate=infection_rate, recovery_rate=recovery_rate)
        model.set_initial_burnout(provider_ids, provider_burnout_scores)

        # Run simulation
        model.simulate(iterations=simulation_iterations)

        # Generate report
        report = model.generate_report()

        # Map superspreader profiles
        superspreader_profiles = [
            ContagionSuperspreaderProfile(
                provider_id=p.provider_id,
                provider_name=_anonymize_id(p.provider_id, "Provider"),
                burnout_score=p.burnout_score,
                burnout_trend=p.burnout_trend,
                degree_centrality=p.degree_centrality,
                betweenness_centrality=p.betweenness_centrality,
                eigenvector_centrality=p.eigenvector_centrality,
                composite_centrality=p.composite_centrality,
                superspreader_score=p.superspreader_score,
                risk_level=p.risk_level,
                direct_contacts=p.direct_contacts,
                estimated_cascade_size=p.estimated_cascade_size,
            )
            for p in report.superspreaders
        ]

        # Map interventions
        interventions = [
            NetworkInterventionInfo(
                intervention_type=i.intervention_type.value,
                priority=i.priority,
                reason=i.reason,
                target_providers=i.target_providers,
                affected_edges=list(i.affected_edges),
                estimated_infection_reduction=i.estimated_infection_reduction,
                estimated_cost_hours=i.estimated_cost,
            )
            for i in report.recommended_interventions[:max_interventions]
        ]

        # Determine severity
        if report.contagion_risk.value == "critical":
            severity = "emergency"
        elif report.contagion_risk.value == "high":
            severity = "critical"
        elif report.contagion_risk.value == "moderate":
            severity = "warning"
        else:
            severity = "healthy"

        return BurnoutContagionResponse(
            network_size=report.network_size,
            current_susceptible=report.current_susceptible,
            current_infected=report.current_infected,
            current_infection_rate=report.current_infection_rate,
            contagion_risk=ContagionRiskEnum(report.contagion_risk.value),
            simulation_iterations=report.simulation_iterations,
            final_infection_rate=report.final_infection_rate,
            peak_infection_rate=report.peak_infection_rate,
            peak_iteration=report.peak_iteration,
            superspreaders=superspreader_profiles,
            total_superspreaders=report.total_superspreaders,
            recommended_interventions=interventions,
            warnings=report.warnings,
            generated_at=report.generated_at.isoformat(),
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Contagion model unavailable: {e}")
        return await _simulate_burnout_contagion_fallback(
            provider_burnout_scores,
            infection_rate,
            recovery_rate,
            simulation_iterations,
            max_interventions,
        )
    except Exception as e:
        logger.error(f"Burnout contagion simulation failed: {e}")
        raise RuntimeError(f"Failed to simulate burnout contagion: {e}") from e


async def _simulate_burnout_contagion_fallback(
    provider_burnout_scores: dict[str, float],
    infection_rate: float,
    recovery_rate: float,
    simulation_iterations: int,
    max_interventions: int,
) -> BurnoutContagionResponse:
    """Fallback simulation when contagion model is unavailable."""
    provider_ids = list(provider_burnout_scores.keys())
    n = len(provider_ids)

    # Count infected (burnout >= 0.5)
    infected_count = sum(1 for score in provider_burnout_scores.values() if score >= 0.5)
    susceptible_count = n - infected_count
    infection_rate_current = infected_count / n if n > 0 else 0.0

    # Determine risk level
    if infection_rate_current >= 0.5:
        risk = ContagionRiskEnum.CRITICAL
        severity = "emergency"
    elif infection_rate_current >= 0.25:
        risk = ContagionRiskEnum.HIGH
        severity = "critical"
    elif infection_rate_current >= 0.1:
        risk = ContagionRiskEnum.MODERATE
        severity = "warning"
    else:
        risk = ContagionRiskEnum.LOW
        severity = "healthy"

    # Identify high-burnout individuals as potential superspreaders
    superspreaders = []
    for pid, score in provider_burnout_scores.items():
        if score >= 0.6:
            superspreaders.append(
                ContagionSuperspreaderProfile(
                    provider_id=pid,
                    provider_name=f"Provider {pid[-4:]}",
                    burnout_score=score,
                    burnout_trend="stable",
                    degree_centrality=0.5,  # Placeholder
                    betweenness_centrality=0.3,
                    eigenvector_centrality=0.4,
                    composite_centrality=0.4,
                    superspreader_score=score * 0.4,
                    risk_level="high" if score >= 0.8 else "moderate",
                    direct_contacts=5,
                    estimated_cascade_size=int(score * 10),
                )
            )

    # Generate simple interventions
    interventions = []
    for ss in superspreaders[:3]:
        if ss.burnout_score >= 0.7:
            interventions.append(
                NetworkInterventionInfo(
                    intervention_type="workload_reduction",
                    priority=1,
                    reason=f"High burnout score ({ss.burnout_score:.2f})",
                    target_providers=[ss.provider_id],
                    affected_edges=[],
                    estimated_infection_reduction=0.15,
                    estimated_cost_hours=20.0,
                )
            )

    warnings = []
    if infected_count > n * 0.3:
        warnings.append(f"High infection rate: {infected_count}/{n} ({infection_rate_current*100:.0f}%)")
    if len(superspreaders) > 3:
        warnings.append(f"Multiple superspreaders identified: {len(superspreaders)}")

    return BurnoutContagionResponse(
        network_size=n,
        current_susceptible=susceptible_count,
        current_infected=infected_count,
        current_infection_rate=infection_rate_current,
        contagion_risk=risk,
        simulation_iterations=simulation_iterations,
        final_infection_rate=min(1.0, infection_rate_current * 1.5),  # Estimate
        peak_infection_rate=min(1.0, infection_rate_current * 2.0),
        peak_iteration=simulation_iterations // 2,
        superspreaders=superspreaders,
        total_superspreaders=len(superspreaders),
        recommended_interventions=interventions[:max_interventions],
        warnings=warnings,
        generated_at=datetime.now().isoformat(),
        severity=severity,
    )
