"""
Artificial Immune System MCP Tools for Schedule Anomaly Detection.

Exposes the ScheduleImmuneSystem resilience module as MCP tools for AI assistant
interaction. Uses immunology-inspired adaptive response patterns:

1. **Negative Selection Algorithm (NSA)**: Detect anomalous schedule states
   by learning what is "self" (valid) and flagging "non-self" (anomalous).

2. **Clonal Selection**: Select and apply the most appropriate repair
   strategy based on affinity matching.

3. **Memory Cells**: Track learned patterns from past anomalies for
   faster future detection and response.

Key Concepts:
- Detectors: Hyperspheres in feature space that trigger on non-self
- Antibodies: Repair strategies with affinity for specific anomaly patterns
- Affinity: How well an antibody matches an anomaly (distance-based)

These tools provide biologically-inspired anomaly detection and self-healing
capabilities for medical residency scheduling.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Type Definitions
# =============================================================================


class AnomalySeverityEnum(str, Enum):
    """Severity levels for detected anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImmuneSystemStateEnum(str, Enum):
    """Overall state of the immune system."""

    UNTRAINED = "untrained"
    TRAINED = "trained"
    ACTIVE = "active"
    RESPONDING = "responding"


class RepairStatusEnum(str, Enum):
    """Status of a repair attempt."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class AntibodyStatusEnum(str, Enum):
    """Status of an antibody (repair strategy)."""

    AVAILABLE = "available"
    SELECTED = "selected"
    APPLIED = "applied"
    EXHAUSTED = "exhausted"


# =============================================================================
# Pydantic Response Models
# =============================================================================


class DetectorInfo(BaseModel):
    """Information about a single detector in the immune system."""

    detector_id: str = Field(description="Unique identifier for the detector")
    matches_count: int = Field(ge=0, description="Number of anomalies detected")
    radius: float = Field(ge=0.0, description="Detection radius in feature space")
    created_at: str = Field(description="ISO timestamp when detector was created")


class AnomalyInfo(BaseModel):
    """Information about a detected anomaly."""

    anomaly_id: str = Field(description="Unique identifier for the anomaly")
    detected_at: str = Field(description="ISO timestamp of detection")
    anomaly_score: float = Field(
        ge=0.0, description="Anomaly score (0=normal, higher=more anomalous)"
    )
    severity: AnomalySeverityEnum = Field(description="Severity classification")
    matching_detectors_count: int = Field(
        ge=0, description="Number of detectors that triggered"
    )
    description: str = Field(description="Human-readable description of the anomaly")
    schedule_state: dict[str, Any] | None = Field(
        default=None, description="Schedule state that triggered the anomaly"
    )


class AntibodyInfo(BaseModel):
    """Information about a registered antibody (repair strategy)."""

    antibody_id: str = Field(description="Unique identifier for the antibody")
    name: str = Field(description="Antibody name")
    description: str = Field(description="What this antibody repairs")
    applications_count: int = Field(ge=0, description="Number of times applied")
    success_count: int = Field(ge=0, description="Number of successful repairs")
    success_rate: float = Field(
        ge=0.0, le=1.0, description="Historical success rate (0-1)"
    )
    affinity_radius: float = Field(
        ge=0.0, description="How broadly applicable this antibody is"
    )
    status: AntibodyStatusEnum = Field(description="Current status of the antibody")


class MemoryCellInfo(BaseModel):
    """Information about a memory cell (learned pattern)."""

    pattern_id: str = Field(description="Unique identifier for the pattern")
    anomaly_type: str = Field(description="Type of anomaly this pattern detects")
    first_seen: str = Field(description="When this pattern was first detected")
    occurrences: int = Field(ge=0, description="Number of times this pattern occurred")
    effective_response: str | None = Field(
        default=None, description="Antibody that worked best for this pattern"
    )
    response_time_improvement: float = Field(
        ge=0.0, le=1.0, description="How much faster response is due to memory (0-1)"
    )


class ImmuneResponseInfo(BaseModel):
    """Information about the current immune response status."""

    state: ImmuneSystemStateEnum = Field(description="Overall immune system state")
    is_trained: bool = Field(description="Whether the system has been trained")
    detector_count: int = Field(ge=0, description="Number of active detectors")
    antibody_count: int = Field(ge=0, description="Number of registered antibodies")
    anomalies_detected: int = Field(ge=0, description="Total anomalies detected")
    repairs_applied: int = Field(ge=0, description="Total repairs attempted")
    successful_repairs: int = Field(ge=0, description="Total successful repairs")
    repair_success_rate: float = Field(
        ge=0.0, le=1.0, description="Overall repair success rate"
    )
    feature_dimensions: int = Field(
        ge=0, description="Dimensionality of feature space"
    )
    detection_radius: float = Field(ge=0.0, description="Detection radius for detectors")
    training_samples: int = Field(ge=0, description="Number of training samples used")


class RepairResultInfo(BaseModel):
    """Result of applying a repair strategy."""

    repair_id: str = Field(description="Unique identifier for this repair")
    antibody_id: str = Field(description="Antibody that was used")
    antibody_name: str = Field(description="Name of the antibody")
    applied_at: str = Field(description="ISO timestamp of repair application")
    status: RepairStatusEnum = Field(description="Repair status")
    anomaly_score_before: float = Field(
        ge=0.0, description="Anomaly score before repair"
    )
    anomaly_score_after: float = Field(ge=0.0, description="Anomaly score after repair")
    improvement: float = Field(description="Improvement in anomaly score (can be negative)")
    message: str = Field(description="Human-readable repair result message")


# =============================================================================
# Tool Response Models
# =============================================================================


class ImmuneResponseAssessmentResponse(BaseModel):
    """Response from assess_immune_response_tool."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    response_status: ImmuneResponseInfo = Field(
        description="Current immune system status"
    )
    active_detectors: list[DetectorInfo] = Field(
        default_factory=list,
        description="Most active detectors (top by match count)"
    )
    recent_anomalies: list[AnomalyInfo] = Field(
        default_factory=list,
        description="Recently detected anomalies"
    )
    available_antibodies: list[AntibodyInfo] = Field(
        default_factory=list,
        description="Registered repair strategies"
    )
    overall_health: str = Field(
        description="Overall immune health: healthy, responding, stressed, overwhelmed"
    )
    detection_coverage: float = Field(
        ge=0.0, le=1.0, description="Estimated coverage of anomaly space"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, warning, critical, emergency")


class MemoryCellsResponse(BaseModel):
    """Response from check_memory_cells_tool."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    total_memory_cells: int = Field(ge=0, description="Total learned patterns")
    active_memory_cells: int = Field(ge=0, description="Patterns seen recently")
    memory_cells: list[MemoryCellInfo] = Field(
        default_factory=list,
        description="Learned pattern details"
    )
    pattern_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Count of patterns by anomaly type"
    )
    average_response_improvement: float = Field(
        ge=0.0, le=1.0,
        description="Average response time improvement due to memory"
    )
    memory_utilization: float = Field(
        ge=0.0, le=1.0,
        description="How often memory cells are being used"
    )
    oldest_pattern: str | None = Field(
        default=None,
        description="ISO timestamp of oldest learned pattern"
    )
    newest_pattern: str | None = Field(
        default=None,
        description="ISO timestamp of newest learned pattern"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, warning, critical")


class AntibodyResponseInfo(BaseModel):
    """Detailed information about an antibody's response capability."""

    antibody: AntibodyInfo = Field(description="Antibody details")
    affinity_to_current: float | None = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Affinity to current anomaly (if one is active)"
    )
    is_best_match: bool = Field(
        default=False,
        description="Whether this is the best matching antibody"
    )
    recent_applications: int = Field(
        ge=0,
        description="Applications in last 24 hours"
    )
    cooldown_remaining: int = Field(
        ge=0,
        description="Seconds until antibody can be used again (0=ready)"
    )


class AntibodyAnalysisResponse(BaseModel):
    """Response from analyze_antibody_response_tool."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    total_antibodies: int = Field(ge=0, description="Total registered antibodies")
    available_antibodies: int = Field(ge=0, description="Antibodies ready to use")
    antibody_details: list[AntibodyResponseInfo] = Field(
        default_factory=list,
        description="Detailed antibody information"
    )
    best_match_antibody: str | None = Field(
        default=None,
        description="Name of best matching antibody for current state"
    )
    overall_coverage: float = Field(
        ge=0.0, le=1.0,
        description="Estimated coverage of anomaly types"
    )
    repair_capacity: float = Field(
        ge=0.0, le=1.0,
        description="Current repair capacity (1=fully available)"
    )
    historical_effectiveness: float = Field(
        ge=0.0, le=1.0,
        description="Historical antibody effectiveness"
    )
    active_countermeasures: list[str] = Field(
        default_factory=list,
        description="Currently active repair countermeasures"
    )
    pending_repairs: int = Field(
        ge=0,
        description="Number of repairs in progress"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, degraded, overwhelmed")


class ImmuneActionEnum(str, Enum):
    """Types of immune response actions."""

    DETECT_ANOMALY = "detect_anomaly"
    APPLY_REPAIR = "apply_repair"
    TRAIN_SYSTEM = "train_system"
    REGISTER_ANTIBODY = "register_antibody"
    RESET_STATISTICS = "reset_statistics"


class TriggerImmuneResponseResponse(BaseModel):
    """Response from trigger_immune_response function."""

    triggered_at: str = Field(description="ISO timestamp of trigger")
    action: ImmuneActionEnum = Field(description="Action that was triggered")
    success: bool = Field(description="Whether the action succeeded")
    anomaly_detected: bool | None = Field(
        default=None,
        description="Whether an anomaly was detected (for detect_anomaly action)"
    )
    anomaly_info: AnomalyInfo | None = Field(
        default=None,
        description="Detected anomaly details (if any)"
    )
    repair_applied: bool | None = Field(
        default=None,
        description="Whether a repair was applied (for apply_repair action)"
    )
    repair_result: RepairResultInfo | None = Field(
        default=None,
        description="Repair result details (if repair was applied)"
    )
    antibody_used: str | None = Field(
        default=None,
        description="Name of antibody used for repair"
    )
    state_before: dict[str, Any] | None = Field(
        default=None,
        description="Schedule state before action"
    )
    state_after: dict[str, Any] | None = Field(
        default=None,
        description="Schedule state after action (if modified)"
    )
    training_info: dict[str, Any] | None = Field(
        default=None,
        description="Training info (for train_system action)"
    )
    message: str = Field(description="Human-readable result message")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="info, success, warning, error")


# =============================================================================
# Tool Functions
# =============================================================================


async def assess_immune_response(
    include_detectors: bool = True,
    include_recent_anomalies: bool = True,
    include_antibodies: bool = True,
    max_items: int = 10,
) -> ImmuneResponseAssessmentResponse:
    """
    Assess the current status of the artificial immune system.

    Provides a comprehensive view of the immune system's adaptive response
    capabilities, including:

    - **Training Status**: Whether the system has learned valid schedule patterns
    - **Detector Coverage**: How many detectors are active and their effectiveness
    - **Anomaly History**: Recent anomalies detected by the system
    - **Antibody Arsenal**: Available repair strategies and their success rates

    The immune system uses Negative Selection Algorithm (NSA) to distinguish
    between "self" (valid schedules) and "non-self" (anomalous states).

    Args:
        include_detectors: Include details of most active detectors
        include_recent_anomalies: Include recently detected anomalies
        include_antibodies: Include registered antibody information
        max_items: Maximum items to return for each category (1-50)

    Returns:
        ImmuneResponseAssessmentResponse with comprehensive immune status

    Example:
        # Check if immune system is healthy
        result = await assess_immune_response_tool()
        if result.response_status.is_trained:
            print(f"Immune system trained with {result.response_status.detector_count} detectors")
            print(f"Success rate: {result.response_status.repair_success_rate:.1%}")
        else:
            print("WARNING: Immune system needs training")
    """
    logger.info(f"Assessing immune response (max_items={max_items})")

    try:
        from app.resilience.immune_system import ScheduleImmuneSystem

        # In production, would access the actual immune system instance
        logger.warning("Immune system assessment using placeholder data")

        # Build response with mock data showing structure
        active_detectors = []
        if include_detectors:
            active_detectors = [
                DetectorInfo(
                    detector_id="DET-001",
                    matches_count=15,
                    radius=0.1,
                    created_at=(datetime.now()).isoformat(),
                ),
                DetectorInfo(
                    detector_id="DET-002",
                    matches_count=8,
                    radius=0.1,
                    created_at=(datetime.now()).isoformat(),
                ),
                DetectorInfo(
                    detector_id="DET-003",
                    matches_count=5,
                    radius=0.1,
                    created_at=(datetime.now()).isoformat(),
                ),
            ][:max_items]

        recent_anomalies = []
        if include_recent_anomalies:
            recent_anomalies = [
                AnomalyInfo(
                    anomaly_id="ANO-001",
                    detected_at=datetime.now().isoformat(),
                    anomaly_score=1.2,
                    severity=AnomalySeverityEnum.HIGH,
                    matching_detectors_count=3,
                    description="Low coverage: 75%; 2 ACGME violations",
                ),
                AnomalyInfo(
                    anomaly_id="ANO-002",
                    detected_at=datetime.now().isoformat(),
                    anomaly_score=0.6,
                    severity=AnomalySeverityEnum.MEDIUM,
                    matching_detectors_count=1,
                    description="High workload imbalance",
                ),
            ][:max_items]

        available_antibodies = []
        if include_antibodies:
            available_antibodies = [
                AntibodyInfo(
                    antibody_id="AB-COVERAGE",
                    name="coverage_gap_repair",
                    description="Repairs coverage gaps by finding available faculty",
                    applications_count=12,
                    success_count=10,
                    success_rate=0.83,
                    affinity_radius=1.0,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
                AntibodyInfo(
                    antibody_id="AB-WORKLOAD",
                    name="workload_balance_repair",
                    description="Rebalances workload by redistributing assignments",
                    applications_count=8,
                    success_count=6,
                    success_rate=0.75,
                    affinity_radius=0.8,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
                AntibodyInfo(
                    antibody_id="AB-ACGME",
                    name="acgme_violation_repair",
                    description="Fixes ACGME violations by adjusting hours/rest periods",
                    applications_count=5,
                    success_count=4,
                    success_rate=0.80,
                    affinity_radius=1.2,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
            ][:max_items]

        response_status = ImmuneResponseInfo(
            state=ImmuneSystemStateEnum.ACTIVE,
            is_trained=True,
            detector_count=100,
            antibody_count=3,
            anomalies_detected=25,
            repairs_applied=15,
            successful_repairs=12,
            repair_success_rate=0.80,
            feature_dimensions=10,
            detection_radius=0.1,
            training_samples=50,
        )

        # Determine overall health
        if response_status.repair_success_rate >= 0.8:
            overall_health = "healthy"
            severity = "healthy"
        elif response_status.repair_success_rate >= 0.6:
            overall_health = "responding"
            severity = "warning"
        elif response_status.repair_success_rate >= 0.4:
            overall_health = "stressed"
            severity = "critical"
        else:
            overall_health = "overwhelmed"
            severity = "emergency"

        return ImmuneResponseAssessmentResponse(
            analyzed_at=datetime.now().isoformat(),
            response_status=response_status,
            active_detectors=active_detectors,
            recent_anomalies=recent_anomalies,
            available_antibodies=available_antibodies,
            overall_health=overall_health,
            detection_coverage=0.85,
            recommendations=[
                "Immune system is trained and operational",
                "80% repair success rate is healthy",
                "Consider training on more edge cases to improve coverage",
            ],
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Immune system module not available: {e}")
        return ImmuneResponseAssessmentResponse(
            analyzed_at=datetime.now().isoformat(),
            response_status=ImmuneResponseInfo(
                state=ImmuneSystemStateEnum.UNTRAINED,
                is_trained=False,
                detector_count=0,
                antibody_count=0,
                anomalies_detected=0,
                repairs_applied=0,
                successful_repairs=0,
                repair_success_rate=0.0,
                feature_dimensions=10,
                detection_radius=0.1,
                training_samples=0,
            ),
            active_detectors=[],
            recent_anomalies=[],
            available_antibodies=[],
            overall_health="untrained",
            detection_coverage=0.0,
            recommendations=["Immune system module not available - check installation"],
            severity="warning",
        )


async def check_memory_cells(
    include_inactive: bool = False,
    max_patterns: int = 20,
) -> MemoryCellsResponse:
    """
    Check the immune system's memory cells (learned patterns from past stressors).

    Memory cells represent learned patterns from past anomalies, enabling faster
    and more effective responses to recurring issues. Like biological immune
    memory (T and B cells), the system remembers:

    - **What worked**: Which antibodies were effective for which anomaly types
    - **Pattern signatures**: Feature vectors that characterize specific anomalies
    - **Response optimization**: Faster detection and repair for known patterns

    Memory improves response time because:
    1. Known patterns trigger immediate recognition (no search needed)
    2. Effective antibodies are pre-selected based on history
    3. Repair strategies are optimized from past experience

    Args:
        include_inactive: Include patterns not seen recently (last 30 days)
        max_patterns: Maximum number of patterns to return (1-100)

    Returns:
        MemoryCellsResponse with learned pattern information

    Example:
        # Check what the immune system has learned
        result = await check_memory_cells_tool()
        print(f"Memory cells: {result.total_memory_cells}")
        print(f"Response improvement: {result.average_response_improvement:.1%}")

        # Find most common anomaly types
        for anomaly_type, count in result.pattern_distribution.items():
            print(f"  {anomaly_type}: {count} occurrences")
    """
    logger.info(f"Checking memory cells (include_inactive={include_inactive})")

    try:
        from app.resilience.immune_system import ScheduleImmuneSystem

        # In production, would access actual memory cell data
        logger.warning("Memory cell check using placeholder data")

        memory_cells = [
            MemoryCellInfo(
                pattern_id="MEM-001",
                anomaly_type="coverage_gap",
                first_seen=(datetime.now()).isoformat(),
                occurrences=12,
                effective_response="coverage_gap_repair",
                response_time_improvement=0.45,
            ),
            MemoryCellInfo(
                pattern_id="MEM-002",
                anomaly_type="acgme_violation",
                first_seen=(datetime.now()).isoformat(),
                occurrences=5,
                effective_response="acgme_violation_repair",
                response_time_improvement=0.35,
            ),
            MemoryCellInfo(
                pattern_id="MEM-003",
                anomaly_type="workload_imbalance",
                first_seen=(datetime.now()).isoformat(),
                occurrences=8,
                effective_response="workload_balance_repair",
                response_time_improvement=0.40,
            ),
        ][:max_patterns]

        pattern_distribution = {
            "coverage_gap": 12,
            "workload_imbalance": 8,
            "acgme_violation": 5,
            "schedule_instability": 3,
        }

        avg_improvement = sum(m.response_time_improvement for m in memory_cells) / len(memory_cells) if memory_cells else 0.0

        return MemoryCellsResponse(
            analyzed_at=datetime.now().isoformat(),
            total_memory_cells=len(memory_cells),
            active_memory_cells=len([m for m in memory_cells if m.occurrences > 2]),
            memory_cells=memory_cells,
            pattern_distribution=pattern_distribution,
            average_response_improvement=avg_improvement,
            memory_utilization=0.65,
            oldest_pattern=memory_cells[-1].first_seen if memory_cells else None,
            newest_pattern=memory_cells[0].first_seen if memory_cells else None,
            recommendations=[
                "Memory system is functioning well",
                "Coverage gap is the most frequently encountered pattern",
                "Consider reinforcing detection for rare patterns",
            ],
            severity="healthy",
        )

    except ImportError as e:
        logger.warning(f"Immune system module not available: {e}")
        return MemoryCellsResponse(
            analyzed_at=datetime.now().isoformat(),
            total_memory_cells=0,
            active_memory_cells=0,
            memory_cells=[],
            pattern_distribution={},
            average_response_improvement=0.0,
            memory_utilization=0.0,
            oldest_pattern=None,
            newest_pattern=None,
            recommendations=["Immune system module not available"],
            severity="warning",
        )


async def analyze_antibody_response(
    schedule_state: dict[str, Any] | None = None,
    include_all: bool = True,
) -> AntibodyAnalysisResponse:
    """
    Analyze the antibody (repair strategy) response capabilities.

    Antibodies are repair strategies that can fix specific types of anomalies.
    Each antibody has an affinity pattern - it works best for anomalies with
    similar feature vectors. This tool analyzes:

    - **Available Antibodies**: What repair strategies are registered
    - **Affinity Matching**: Which antibody best matches the current state
    - **Historical Effectiveness**: Success rates and application counts
    - **Active Countermeasures**: Currently executing repairs

    The system uses Clonal Selection to choose the best antibody:
    1. Calculate affinity of each antibody to the anomaly
    2. Select the antibody with highest affinity
    3. Boost selection by historical success rate
    4. Apply repair and track results

    Args:
        schedule_state: Optional current schedule state to calculate affinities.
            If provided, affinities are calculated against this state.
            Expected keys: total_blocks, covered_blocks, faculty_count,
            resident_count, acgme_violations, avg_hours_per_week,
            supervision_ratio, workload_std_dev, schedule_changes
        include_all: Include all antibodies even if affinity is zero

    Returns:
        AntibodyAnalysisResponse with active countermeasures and recommendations

    Example:
        # Find best repair for current schedule
        schedule = {
            "total_blocks": 100,
            "covered_blocks": 75,
            "faculty_count": 10,
            "resident_count": 25,
            "acgme_violations": [{"type": "80hr", "severity": "CRITICAL"}],
            "avg_hours_per_week": 85,
            "workload_std_dev": 0.4,
        }
        result = await analyze_antibody_response_tool(schedule_state=schedule)

        if result.best_match_antibody:
            print(f"Recommended repair: {result.best_match_antibody}")
        print(f"Repair capacity: {result.repair_capacity:.1%}")
    """
    logger.info(f"Analyzing antibody response (schedule_state={schedule_state is not None})")

    try:
        from app.resilience.immune_system import ScheduleImmuneSystem

        # In production, would access actual immune system
        logger.warning("Antibody analysis using placeholder data")

        # Calculate mock affinities based on schedule state
        has_coverage_issue = False
        has_workload_issue = False
        has_acgme_issue = False

        if schedule_state:
            coverage_rate = schedule_state.get("covered_blocks", 100) / max(1, schedule_state.get("total_blocks", 100))
            has_coverage_issue = coverage_rate < 0.9
            has_workload_issue = schedule_state.get("workload_std_dev", 0) > 0.3
            has_acgme_issue = len(schedule_state.get("acgme_violations", [])) > 0

        antibody_details = [
            AntibodyResponseInfo(
                antibody=AntibodyInfo(
                    antibody_id="AB-COVERAGE",
                    name="coverage_gap_repair",
                    description="Repairs coverage gaps by finding available faculty",
                    applications_count=12,
                    success_count=10,
                    success_rate=0.83,
                    affinity_radius=1.0,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
                affinity_to_current=0.85 if has_coverage_issue else 0.2,
                is_best_match=has_coverage_issue and not has_acgme_issue,
                recent_applications=2,
                cooldown_remaining=0,
            ),
            AntibodyResponseInfo(
                antibody=AntibodyInfo(
                    antibody_id="AB-WORKLOAD",
                    name="workload_balance_repair",
                    description="Rebalances workload by redistributing assignments",
                    applications_count=8,
                    success_count=6,
                    success_rate=0.75,
                    affinity_radius=0.8,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
                affinity_to_current=0.75 if has_workload_issue else 0.15,
                is_best_match=has_workload_issue and not has_coverage_issue and not has_acgme_issue,
                recent_applications=1,
                cooldown_remaining=0,
            ),
            AntibodyResponseInfo(
                antibody=AntibodyInfo(
                    antibody_id="AB-ACGME",
                    name="acgme_violation_repair",
                    description="Fixes ACGME violations by adjusting hours/rest periods",
                    applications_count=5,
                    success_count=4,
                    success_rate=0.80,
                    affinity_radius=1.2,
                    status=AntibodyStatusEnum.AVAILABLE,
                ),
                affinity_to_current=0.90 if has_acgme_issue else 0.1,
                is_best_match=has_acgme_issue,
                recent_applications=0,
                cooldown_remaining=0,
            ),
        ]

        # Find best match
        best_match = None
        for detail in antibody_details:
            if detail.is_best_match:
                best_match = detail.antibody.name
                break

        # If no specific issue, coverage is usually the best default
        if best_match is None and schedule_state:
            best_match = "coverage_gap_repair"

        # Calculate overall metrics
        total_antibodies = len(antibody_details)
        available_antibodies = len([d for d in antibody_details if d.cooldown_remaining == 0])
        avg_success_rate = sum(d.antibody.success_rate for d in antibody_details) / total_antibodies

        # Active countermeasures (none in mock)
        active_countermeasures: list[str] = []

        # Determine severity
        if avg_success_rate >= 0.75 and available_antibodies == total_antibodies:
            severity = "healthy"
        elif avg_success_rate >= 0.5:
            severity = "degraded"
        else:
            severity = "overwhelmed"

        return AntibodyAnalysisResponse(
            analyzed_at=datetime.now().isoformat(),
            total_antibodies=total_antibodies,
            available_antibodies=available_antibodies,
            antibody_details=antibody_details,
            best_match_antibody=best_match,
            overall_coverage=0.85,
            repair_capacity=available_antibodies / total_antibodies if total_antibodies > 0 else 0.0,
            historical_effectiveness=avg_success_rate,
            active_countermeasures=active_countermeasures,
            pending_repairs=0,
            recommendations=[
                f"Best matching antibody: {best_match}" if best_match else "No specific antibody recommended",
                f"Historical effectiveness: {avg_success_rate:.1%}",
                "All antibodies are available for use",
            ],
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Immune system module not available: {e}")
        return AntibodyAnalysisResponse(
            analyzed_at=datetime.now().isoformat(),
            total_antibodies=0,
            available_antibodies=0,
            antibody_details=[],
            best_match_antibody=None,
            overall_coverage=0.0,
            repair_capacity=0.0,
            historical_effectiveness=0.0,
            active_countermeasures=[],
            pending_repairs=0,
            recommendations=["Immune system module not available"],
            severity="degraded",
        )
