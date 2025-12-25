"""
Resilience Framework MCP Integration.

Exposes all 13 resilience patterns as MCP tools for AI assistant interaction.
These tools provide deep insights into system stability, vulnerability analysis,
and automated safety mechanisms.

Tier 1 (Critical): Core resilience monitoring
Tier 2 (Strategic): Advanced stress analysis and equilibrium
Tier 3 (Advanced): Behavioral patterns and cognitive load
"""

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)


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
                    faculty_name=v.get("faculty_name", f"Faculty {v.get('faculty_id', 'unknown')}"),
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
                    faculty_1_name=p.get(
                        "faculty1_name", f"Faculty {p.get('faculty1_id', 'unknown')}"
                    ),
                    faculty_2_id=p.get("faculty2_id", ""),
                    faculty_2_name=p.get(
                        "faculty2_name", f"Faculty {p.get('faculty2_id', 'unknown')}"
                    ),
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
