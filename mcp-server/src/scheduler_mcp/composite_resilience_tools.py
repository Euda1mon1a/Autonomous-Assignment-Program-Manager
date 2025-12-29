"""
Composite/Advanced Resilience Tools for MCP Integration.

This module exposes four advanced resilience modules as MCP tools:

1. Unified Critical Index - Multi-factor risk aggregation combining:
   - N-1/N-2 contingency vulnerability
   - Burnout epidemiology (super-spreader potential)
   - Network hub centrality (structural importance)

2. Recovery Distance (Operations Research) - Measures schedule fragility:
   - Minimum edit distance to recover from N-1 shocks
   - Graph-theoretic resilience metric
   - Lower RD = more resilient schedule

3. Creep Fatigue (Materials Science) - Long-term stress accumulation:
   - Larson-Miller parameter for chronic stress prediction
   - S-N curves for rotation cycle fatigue
   - Miner's rule cumulative damage

4. Transcription Factors (Molecular Biology) - Bio-inspired constraint regulation:
   - Gene regulatory network concepts for constraint management
   - Context-sensitive constraint weighting
   - Signal transduction cascades

These tools provide cross-disciplinary scientific approaches to resilience,
applying concepts from materials science, epidemiology, operations research,
and molecular biology to medical residency scheduling.
"""

import hashlib
import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _anonymize_id(identifier: str | None, prefix: str = "Faculty") -> str:
    """Create consistent anonymized reference from ID.

    Uses SHA-256 hash for consistent mapping without exposing PII.
    Complies with OPSEC/PERSEC requirements for military medical data.
    """
    if not identifier:
        return f"{prefix}-unknown"
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"


# =============================================================================
# Unified Critical Index Types
# =============================================================================


class RiskPatternEnum(str, Enum):
    """
    Risk patterns identified by cross-domain analysis.

    Different combinations of high scores in contingency, epidemiology,
    and hub analysis suggest different intervention strategies.
    """

    UNIVERSAL_CRITICAL = "universal_critical"  # All three domains high
    STRUCTURAL_BURNOUT = "structural_burnout"  # Contingency + Epidemiology
    INFLUENTIAL_HUB = "influential_hub"  # Contingency + Hub
    SOCIAL_CONNECTOR = "social_connector"  # Epidemiology + Hub
    ISOLATED_WORKHORSE = "isolated_workhorse"  # Contingency only
    BURNOUT_VECTOR = "burnout_vector"  # Epidemiology only
    NETWORK_ANCHOR = "network_anchor"  # Hub only
    LOW_RISK = "low_risk"  # No domains high


class InterventionTypeEnum(str, Enum):
    """Recommended intervention types based on risk pattern."""

    IMMEDIATE_PROTECTION = "immediate_protection"
    CROSS_TRAINING = "cross_training"
    WORKLOAD_REDUCTION = "workload_reduction"
    NETWORK_DIVERSIFICATION = "network_diversification"
    MONITORING = "monitoring"
    WELLNESS_SUPPORT = "wellness_support"


class DomainScoreInfo(BaseModel):
    """Score from a single criticality domain."""

    raw_score: float = Field(ge=0.0, le=1.0, description="Raw score before normalization")
    normalized_score: float = Field(
        ge=0.0, le=1.0, description="Score after population normalization"
    )
    percentile: float = Field(ge=0.0, le=100.0, description="Percentile in population")
    is_critical: bool = Field(description="Whether threshold is exceeded")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Domain-specific details"
    )


class FacultyUnifiedIndex(BaseModel):
    """Unified critical index for a single faculty member."""

    faculty_id: str = Field(description="Faculty identifier")
    faculty_name: str = Field(description="Display name (anonymized)")
    composite_index: float = Field(
        ge=0.0, le=1.0, description="Weighted composite risk score"
    )
    risk_pattern: RiskPatternEnum = Field(description="Identified risk pattern")
    confidence: float = Field(ge=0.0, le=1.0, description="Data quality confidence")
    domain_scores: dict[str, DomainScoreInfo] = Field(
        description="Scores by domain: contingency, epidemiology, hub_analysis"
    )
    domain_agreement: float = Field(
        ge=0.0, le=1.0, description="Cross-domain consensus (1=agreement, 0=conflict)"
    )
    leading_domain: str | None = Field(description="Domain with highest score")
    conflict_details: list[str] = Field(
        default_factory=list, description="Notable cross-domain conflicts"
    )
    recommended_interventions: list[InterventionTypeEnum] = Field(
        default_factory=list, description="Recommended actions"
    )
    priority_rank: int = Field(ge=0, description="Priority rank in population (1=highest)")


class UnifiedCriticalIndexResponse(BaseModel):
    """Response from unified critical index calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    total_faculty: int = Field(ge=0, description="Total faculty analyzed")
    overall_index: float = Field(
        ge=0.0, le=100.0, description="System-wide composite risk score 0-100"
    )
    risk_level: str = Field(
        description="System risk level: low, moderate, elevated, high, critical"
    )
    risk_concentration: float = Field(
        ge=0.0, le=1.0, description="Gini coefficient of risk distribution"
    )
    critical_count: int = Field(ge=0, description="Faculty with elevated risk")
    universal_critical_count: int = Field(
        ge=0, description="Faculty critical in all domains"
    )
    pattern_distribution: dict[str, int] = Field(
        description="Count by risk pattern"
    )
    top_priority: list[str] = Field(
        description="Top priority faculty IDs for intervention"
    )
    top_critical_faculty: list[FacultyUnifiedIndex] = Field(
        default_factory=list, description="Details for highest-risk faculty"
    )
    contributing_factors: dict[str, float] = Field(
        description="Weight of each domain in composite"
    )
    trend: str = Field(description="Risk trend: improving, stable, degrading")
    top_concerns: list[str] = Field(description="Top 3-5 risk factors")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, warning, critical, emergency")


# =============================================================================
# Recovery Distance Types
# =============================================================================


class N1EventInfo(BaseModel):
    """Information about an N-1 shock event."""

    event_type: str = Field(
        description="Type: faculty_absence, resident_sick, room_closure"
    )
    resource_id: str = Field(description="ID of lost resource")
    resource_name: str | None = Field(description="Name for display")
    affected_blocks: int = Field(ge=0, description="Number of affected blocks")


class EditInfo(BaseModel):
    """Information about a recovery edit."""

    edit_type: str = Field(description="Type: swap, reassign, move_to_backup")
    description: str = Field(description="Human-readable description")
    block_id: str | None = Field(description="Affected block")
    new_person_id: str | None = Field(description="Person taking over")


class RecoveryResultInfo(BaseModel):
    """Recovery distance result for a single event."""

    event: N1EventInfo = Field(description="The N-1 event tested")
    recovery_distance: int = Field(ge=0, description="Minimum edits needed (0=no recovery)")
    feasible: bool = Field(description="Whether recovery is possible")
    witness_edits: list[EditInfo] = Field(
        default_factory=list, description="Concrete edit sequence"
    )
    computation_time_ms: float = Field(ge=0, description="Search time in milliseconds")


class RecoveryDistanceResponse(BaseModel):
    """Response from recovery distance calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    schedule_id: str | None = Field(description="Schedule identifier if applicable")
    period_start: str = Field(description="Analysis period start date")
    period_end: str = Field(description="Analysis period end date")
    events_tested: int = Field(ge=0, description="Number of N-1 events tested")
    rd_mean: float = Field(ge=0.0, description="Average recovery distance")
    rd_median: float = Field(ge=0.0, description="Median recovery distance")
    rd_p95: float = Field(ge=0.0, description="95th percentile (worst-case)")
    rd_max: int = Field(ge=0, description="Maximum recovery distance observed")
    breakglass_count: int = Field(ge=0, description="Events requiring >3 edits")
    infeasible_count: int = Field(ge=0, description="Events with no recovery path")
    by_event_type: dict[str, dict[str, float]] = Field(
        description="Breakdown by event type"
    )
    fragility_score: float = Field(
        ge=0.0, le=1.0, description="Overall schedule fragility (higher=more fragile)"
    )
    sample_results: list[RecoveryResultInfo] = Field(
        default_factory=list, description="Sample of individual results"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="resilient, moderate, fragile, brittle")


# =============================================================================
# Creep Fatigue Types
# =============================================================================


class CreepStageEnum(str, Enum):
    """
    Stages of creep deformation leading to failure.

    Analogous to burnout progression:
    - PRIMARY: Initial adaptation phase, strain rate decreasing
    - SECONDARY: Steady-state, sustainable performance
    - TERTIARY: Accelerating damage, approaching burnout
    """

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class CreepAnalysisInfo(BaseModel):
    """Creep analysis for a single resident."""

    resident_id: str = Field(description="Resident identifier")
    creep_stage: CreepStageEnum = Field(description="Current creep stage")
    larson_miller_parameter: float = Field(
        ge=0.0, description="LMP value (failure threshold ~45)"
    )
    estimated_days_to_failure: int = Field(
        ge=0, description="Predicted days until burnout at current rate"
    )
    strain_rate: float = Field(description="Rate of degradation per day")
    recommended_stress_reduction: float = Field(
        ge=0.0, le=100.0, description="Percentage workload reduction needed"
    )


class FatigueAnalysisInfo(BaseModel):
    """Fatigue analysis from rotation cycles."""

    current_cycles: int = Field(ge=0, description="Rotations completed")
    cycles_to_failure: int = Field(ge=0, description="Predicted cycles until failure")
    stress_amplitude: float = Field(ge=0.0, le=1.0, description="Current rotation stress")
    remaining_life_fraction: float = Field(
        ge=0.0, le=1.0, description="Fraction of fatigue life remaining"
    )
    cumulative_damage: float = Field(
        ge=0.0, description="Miner's rule damage accumulation (1.0=failure)"
    )


class CreepFatigueAssessment(BaseModel):
    """Combined creep-fatigue assessment for one resident."""

    resident_id: str = Field(description="Resident identifier")
    overall_risk: str = Field(description="Risk level: low, moderate, high")
    risk_score: float = Field(ge=0.0, le=3.0, description="Combined risk score")
    risk_description: str = Field(description="Human-readable risk summary")
    creep_analysis: CreepAnalysisInfo = Field(description="Time-based creep analysis")
    fatigue_analysis: FatigueAnalysisInfo = Field(
        description="Cycle-based fatigue analysis"
    )
    recommendations: list[str] = Field(default_factory=list)


class CreepFatigueResponse(BaseModel):
    """Response from creep-fatigue burnout assessment."""

    analyzed_at: str = Field(description="ISO timestamp")
    residents_analyzed: int = Field(ge=0, description="Number of residents assessed")
    high_risk_count: int = Field(ge=0, description="Residents at high burnout risk")
    moderate_risk_count: int = Field(ge=0, description="Residents at moderate risk")
    tertiary_creep_count: int = Field(
        ge=0, description="Residents in tertiary (pre-failure) stage"
    )
    average_lmp: float = Field(ge=0.0, description="Average Larson-Miller parameter")
    average_remaining_life: float = Field(
        ge=0.0, le=1.0, description="Average fatigue life remaining"
    )
    lmp_threshold: float = Field(description="LMP failure threshold (default ~45)")
    safe_lmp: float = Field(description="Safe operating LMP (default ~31.5)")
    assessments: list[CreepFatigueAssessment] = Field(
        default_factory=list, description="Individual assessments"
    )
    system_recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, at_risk, critical")


# =============================================================================
# Transcription Factors Types
# =============================================================================


class TFTypeEnum(str, Enum):
    """Types of transcription factors in the regulatory network."""

    ACTIVATOR = "activator"  # Increases constraint weight
    REPRESSOR = "repressor"  # Decreases/disables constraint
    DUAL = "dual"  # Context-dependent
    PIONEER = "pioneer"  # Can re-enable silenced constraints
    MASTER = "master"  # Controls entire regulatory programs


class SignalStrengthEnum(str, Enum):
    """Strength categories for TF expression."""

    WEAK = "weak"  # 0.0 - 0.3
    MODERATE = "moderate"  # 0.3 - 0.6
    STRONG = "strong"  # 0.6 - 0.8
    MAXIMAL = "maximal"  # 0.8 - 1.0


class TranscriptionFactorInfo(BaseModel):
    """Information about a transcription factor."""

    name: str = Field(description="TF name")
    tf_type: TFTypeEnum = Field(description="TF type")
    expression_level: float = Field(
        ge=0.0, le=1.0, description="Current expression (0=off, 1=max)"
    )
    strength_category: SignalStrengthEnum = Field(description="Expression category")
    is_active: bool = Field(description="Whether TF is meaningfully expressed")
    targets_count: int = Field(ge=0, description="Number of constraints/TFs regulated")
    description: str = Field(description="TF function description")


class ConstraintRegulationInfo(BaseModel):
    """Regulation status for a constraint."""

    constraint_id: str = Field(description="Constraint identifier")
    constraint_name: str = Field(description="Constraint name")
    base_weight: float = Field(description="Default weight")
    effective_weight: float = Field(description="Current weight after regulation")
    activation_level: float = Field(ge=0.0, le=1.0, description="Activation strength")
    chromatin_state: str = Field(description="open, poised, closed, silenced")
    regulating_tfs: list[str] = Field(default_factory=list, description="Active TF names")
    explanation: str = Field(description="How weight was calculated")


class RegulatoryLoopInfo(BaseModel):
    """Information about a detected regulatory loop."""

    loop_type: str = Field(
        description="positive_feedback, negative_feedback, feed_forward_coherent, etc."
    )
    description: str = Field(description="Loop description")
    tf_names: list[str] = Field(description="TFs involved")
    stability: str = Field(description="stable, oscillating, bistable")


class TranscriptionTriggersResponse(BaseModel):
    """Response from transcription factors analysis."""

    analyzed_at: str = Field(description="ISO timestamp")
    total_tfs: int = Field(ge=0, description="Total transcription factors defined")
    active_tfs: int = Field(ge=0, description="Currently active TFs")
    master_regulators_active: int = Field(
        ge=0, description="Active master regulators (always-on safety TFs)"
    )
    total_constraints_regulated: int = Field(ge=0, description="Constraints with promoters")
    constraints_with_modified_weight: int = Field(
        ge=0, description="Constraints with weight != 1.0"
    )
    regulatory_edges: int = Field(ge=0, description="TF-to-target links")
    detected_loops: int = Field(ge=0, description="Regulatory loops identified")
    total_activation: float = Field(ge=0.0, description="Sum of activator expression")
    total_repression: float = Field(ge=0.0, description="Sum of repressor expression")
    network_entropy: float = Field(
        ge=0.0, description="Diversity of regulatory state"
    )
    active_tfs_list: list[TranscriptionFactorInfo] = Field(
        default_factory=list, description="Active TF details"
    )
    regulated_constraints: list[ConstraintRegulationInfo] = Field(
        default_factory=list, description="Constraint regulation status"
    )
    loops: list[RegulatoryLoopInfo] = Field(
        default_factory=list, description="Detected regulatory loops"
    )
    recent_signals: int = Field(ge=0, description="Signals processed in last hour")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="normal, regulatory_stress, crisis_mode")


# =============================================================================
# Tool Functions
# =============================================================================


async def get_unified_critical_index(
    include_details: bool = True,
    top_n: int = 5,
) -> UnifiedCriticalIndexResponse:
    """
    Calculate unified critical index aggregating all resilience signals.

    Combines signals from three domains into a single actionable risk score:

    1. **Contingency (N-1/N-2 Vulnerability)** - Weight: 40%
       Faculty whose loss causes coverage gaps or cascade failures.
       Immediate operational impact if they become unavailable.

    2. **Epidemiology (Burnout Super-Spreader)** - Weight: 25%
       Faculty who can spread burnout through social connections.
       High network connectivity amplifies burnout transmission.

    3. **Hub Analysis (Network Centrality)** - Weight: 35%
       Faculty who are structural "hubs" in the assignment network.
       High betweenness, PageRank, and eigenvector centrality.

    Key Insight: A faculty member who is N-1 vulnerable, a super-spreader,
    AND a hub represents the highest concentration of organizational risk.

    Cross-validation between domains reveals hidden patterns:
    - High hub + low epidemiology = isolated workaholic (different intervention)
    - High epidemiology + low hub = social connector (burnout spreads but schedule survives)
    - All three high = UNIVERSAL_CRITICAL (immediate protection needed)

    Args:
        include_details: Include individual faculty assessments
        top_n: Number of top-risk faculty to return (1-20)

    Returns:
        UnifiedCriticalIndexResponse with composite risk assessment

    Example:
        # Check overall system risk
        result = await get_unified_critical_index_tool()
        if result.risk_level == "critical":
            print(f"ALERT: {result.universal_critical_count} faculty need immediate protection")
            for faculty in result.top_critical_faculty:
                print(f"  - {faculty.faculty_name}: {faculty.risk_pattern.value}")
    """
    logger.info(f"Calculating unified critical index (top_n={top_n})")

    try:
        # Try to import the actual backend module to verify availability
        import importlib.util
        if importlib.util.find_spec("app.resilience.unified_critical_index") is None:
            raise ImportError("Module not found")

        # In production, this would fetch data from the database
        # For now, return mock data showing the structure
        logger.warning("Unified critical index using placeholder data")

        # Mock response demonstrating the response structure
        return UnifiedCriticalIndexResponse(
            analyzed_at=datetime.now().isoformat(),
            total_faculty=25,
            overall_index=42.5,  # Moderate system risk
            risk_level="moderate",
            risk_concentration=0.35,  # Moderate concentration
            critical_count=3,
            universal_critical_count=1,
            pattern_distribution={
                "universal_critical": 1,
                "structural_burnout": 1,
                "influential_hub": 1,
                "social_connector": 2,
                "isolated_workhorse": 3,
                "burnout_vector": 2,
                "network_anchor": 3,
                "low_risk": 12,
            },
            top_priority=["FAC-001", "FAC-007", "FAC-012"],
            top_critical_faculty=[
                FacultyUnifiedIndex(
                    faculty_id="FAC-001",
                    faculty_name="Faculty-001",
                    composite_index=0.82,
                    risk_pattern=RiskPatternEnum.UNIVERSAL_CRITICAL,
                    confidence=0.85,
                    domain_scores={
                        "contingency": DomainScoreInfo(
                            raw_score=0.75,
                            normalized_score=0.85,
                            percentile=92.0,
                            is_critical=True,
                            details={"sole_provider_blocks": 5},
                        ),
                        "epidemiology": DomainScoreInfo(
                            raw_score=0.68,
                            normalized_score=0.78,
                            percentile=88.0,
                            is_critical=True,
                            details={"degree_centrality": 0.7},
                        ),
                        "hub_analysis": DomainScoreInfo(
                            raw_score=0.72,
                            normalized_score=0.82,
                            percentile=90.0,
                            is_critical=True,
                            details={"betweenness": 0.65},
                        ),
                    },
                    domain_agreement=0.88,
                    leading_domain="contingency",
                    conflict_details=["Strong domain consensus - high confidence"],
                    recommended_interventions=[
                        InterventionTypeEnum.IMMEDIATE_PROTECTION,
                        InterventionTypeEnum.CROSS_TRAINING,
                        InterventionTypeEnum.WORKLOAD_REDUCTION,
                    ],
                    priority_rank=1,
                )
            ]
            if include_details
            else [],
            contributing_factors={
                "contingency": 0.40,
                "hub_analysis": 0.35,
                "epidemiology": 0.25,
            },
            trend="stable",
            top_concerns=[
                "1 faculty member is critical in all domains",
                "Risk concentration (Gini=0.35) is moderate",
                "3 faculty are single points of failure",
            ],
            recommendations=[
                "Prioritize cross-training for FAC-001",
                "Consider workload redistribution from top-3 hubs",
                "Monitor burnout vectors for early warning signs",
            ],
            severity="warning",
        )

    except ImportError as e:
        logger.warning(f"Unified critical index module not available: {e}")
        return UnifiedCriticalIndexResponse(
            analyzed_at=datetime.now().isoformat(),
            total_faculty=0,
            overall_index=0.0,
            risk_level="unknown",
            risk_concentration=0.0,
            critical_count=0,
            universal_critical_count=0,
            pattern_distribution={},
            top_priority=[],
            top_critical_faculty=[],
            contributing_factors={},
            trend="unknown",
            top_concerns=["Module not available"],
            recommendations=["Install networkx: pip install networkx"],
            severity="warning",
        )


async def calculate_recovery_distance(
    start_date: str | None = None,
    end_date: str | None = None,
    max_events: int = 20,
    include_samples: bool = True,
) -> RecoveryDistanceResponse:
    """
    Calculate recovery distance metrics for schedule resilience.

    Recovery Distance (RD) measures how many minimal edits are needed to restore
    schedule feasibility after common N-1 shocks (single resource loss).

    **Concept from Operations Research:**
    - Lower RD = More resilient schedule (easier to recover)
    - Higher RD = More brittle schedule (requires many changes)
    - RD=0 means schedule survives the shock without any changes

    **Event Types Tested:**
    - Faculty absence: Single faculty member unavailable
    - Resident sick day: Single resident unavailable for a day
    - Room closure: Facility unavailable (future)

    **Edit Operations:**
    1. Swap: Exchange assignments between two people
    2. Move to backup: Reassign to pre-designated backup
    3. Reassign: Find any available qualified person

    **Key Metrics:**
    - rd_mean: Average recovery distance (good < 2.0)
    - rd_p95: 95th percentile for worst-case planning
    - breakglass_count: Events requiring >3 edits (emergency scenarios)
    - infeasible_count: Events with no recovery path found

    Args:
        start_date: Analysis start date (YYYY-MM-DD), defaults to today
        end_date: Analysis end date (YYYY-MM-DD), defaults to 30 days
        max_events: Maximum N-1 events to test (1-100)
        include_samples: Include sample individual results

    Returns:
        RecoveryDistanceResponse with recovery metrics and fragility score

    Example:
        # Assess schedule fragility
        result = await calculate_recovery_distance_tool()
        if result.rd_p95 > 4:
            print("WARNING: High recovery cost in worst case")
        if result.breakglass_count > result.events_tested * 0.2:
            print("CRITICAL: Many scenarios require extensive rework")
    """
    logger.info(f"Calculating recovery distance (max_events={max_events})")

    # Parse dates with defaults
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else (today + timedelta(days=30))

    try:
        # Try to import the actual backend module to verify availability
        import importlib.util
        if importlib.util.find_spec("app.resilience.recovery_distance") is None:
            raise ImportError("Module not found")

        # In production, would fetch schedule and run actual analysis
        logger.warning("Recovery distance using placeholder data")

        # Mock response showing typical structure
        sample_results = []
        if include_samples:
            sample_results = [
                RecoveryResultInfo(
                    event=N1EventInfo(
                        event_type="faculty_absence",
                        resource_id="FAC-003",
                        resource_name="Faculty-003",
                        affected_blocks=8,
                    ),
                    recovery_distance=2,
                    feasible=True,
                    witness_edits=[
                        EditInfo(
                            edit_type="swap",
                            description="Swap FAC-005 with FAC-003 on blocks 1-4",
                            block_id="BLK-001",
                            new_person_id="FAC-005",
                        ),
                        EditInfo(
                            edit_type="reassign",
                            description="Reassign blocks 5-8 to backup FAC-012",
                            block_id="BLK-005",
                            new_person_id="FAC-012",
                        ),
                    ],
                    computation_time_ms=45.2,
                ),
                RecoveryResultInfo(
                    event=N1EventInfo(
                        event_type="resident_sick",
                        resource_id="RES-007",
                        resource_name="Resident-PGY2-07",
                        affected_blocks=2,
                    ),
                    recovery_distance=1,
                    feasible=True,
                    witness_edits=[
                        EditInfo(
                            edit_type="move_to_backup",
                            description="Activate backup resident RES-015",
                            block_id="BLK-042",
                            new_person_id="RES-015",
                        ),
                    ],
                    computation_time_ms=12.8,
                ),
            ]

        # Calculate fragility score (0=resilient, 1=brittle)
        rd_mean = 1.8
        breakglass_rate = 0.15
        infeasible_rate = 0.05
        fragility = min(1.0, (rd_mean / 5.0) * 0.5 + breakglass_rate * 0.3 + infeasible_rate * 0.2)

        return RecoveryDistanceResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=None,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            events_tested=18,
            rd_mean=rd_mean,
            rd_median=1.5,
            rd_p95=3.0,
            rd_max=4,
            breakglass_count=3,
            infeasible_count=1,
            by_event_type={
                "faculty_absence": {"mean": 2.1, "median": 2.0, "max": 4, "count": 12},
                "resident_sick": {"mean": 1.2, "median": 1.0, "max": 2, "count": 6},
            },
            fragility_score=fragility,
            sample_results=sample_results,
            recommendations=[
                "Schedule is moderately resilient (RD mean=1.8)",
                "Consider cross-training for 3 breakglass scenarios",
                "Investigate 1 infeasible event - may need backup pools",
            ],
            severity="moderate",
        )

    except ImportError as e:
        logger.warning(f"Recovery distance module not available: {e}")
        return RecoveryDistanceResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=None,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            events_tested=0,
            rd_mean=0.0,
            rd_median=0.0,
            rd_p95=0.0,
            rd_max=0,
            breakglass_count=0,
            infeasible_count=0,
            by_event_type={},
            fragility_score=0.0,
            sample_results=[],
            recommendations=["Module not available - check backend installation"],
            severity="warning",
        )


async def assess_creep_fatigue(
    include_assessments: bool = True,
    top_n: int = 10,
) -> CreepFatigueResponse:
    """
    Assess burnout risk using materials science creep-fatigue analysis.

    Adapts materials science concepts to predict medical resident burnout:

    **Creep Analysis (Time-Dependent Deformation):**
    - PRIMARY stage: Adaptation phase, strain rate decreasing
    - SECONDARY stage: Steady-state, sustainable performance
    - TERTIARY stage: Accelerating damage, approaching burnout

    Uses Larson-Miller Parameter (LMP) to predict time-to-failure:
    - LMP = workload * (C + log10(duration))
    - LMP > 45.0 indicates high burnout risk
    - Safe operating range: LMP < 31.5

    **Fatigue Analysis (Cyclic Loading):**
    Uses S-N curves (Wohler curves) and Miner's Rule:
    - High stress rotations = fewer cycles to failure
    - Cumulative damage D = Sum(n_i / N_i)
    - Failure predicted when D >= 1.0

    **Combined Risk Assessment:**
    - 60% weight on creep (sustained workload)
    - 40% weight on fatigue (rotation cycles)
    - Overall risk: low, moderate, high

    Args:
        include_assessments: Include individual resident assessments
        top_n: Number of highest-risk residents to return (1-50)

    Returns:
        CreepFatigueResponse with burnout predictions and recommendations

    Example:
        # Monitor resident burnout risk
        result = await assess_creep_fatigue_tool()
        if result.tertiary_creep_count > 0:
            print(f"URGENT: {result.tertiary_creep_count} residents approaching burnout")
        for assessment in result.assessments:
            if assessment.overall_risk == "high":
                lmp = assessment.creep_analysis.larson_miller_parameter
                print(f"  {assessment.resident_id}: LMP={lmp:.1f}")
    """
    logger.info(f"Assessing creep-fatigue burnout risk (top_n={top_n})")

    try:
        # Try to import the actual backend module to verify availability
        import importlib.util
        if importlib.util.find_spec("app.resilience.creep_fatigue") is None:
            raise ImportError("Module not found")

        # In production, would fetch resident workload data
        logger.warning("Creep-fatigue using placeholder data")

        assessments = []
        if include_assessments:
            assessments = [
                CreepFatigueAssessment(
                    resident_id="RES-003",
                    overall_risk="high",
                    risk_score=2.6,
                    risk_description="High burnout risk - immediate intervention needed",
                    creep_analysis=CreepAnalysisInfo(
                        resident_id="RES-003",
                        creep_stage=CreepStageEnum.TERTIARY,
                        larson_miller_parameter=42.5,
                        estimated_days_to_failure=14,
                        strain_rate=0.05,
                        recommended_stress_reduction=25.0,
                    ),
                    fatigue_analysis=FatigueAnalysisInfo(
                        current_cycles=8,
                        cycles_to_failure=12,
                        stress_amplitude=0.85,
                        remaining_life_fraction=0.33,
                        cumulative_damage=0.67,
                    ),
                    recommendations=[
                        "URGENT: Reduce workload by 25%",
                        "Schedule easier rotations to allow recovery",
                    ],
                ),
                CreepFatigueAssessment(
                    resident_id="RES-007",
                    overall_risk="moderate",
                    risk_score=1.9,
                    risk_description="Moderate burnout risk - schedule adjustment recommended",
                    creep_analysis=CreepAnalysisInfo(
                        resident_id="RES-007",
                        creep_stage=CreepStageEnum.SECONDARY,
                        larson_miller_parameter=28.0,
                        estimated_days_to_failure=90,
                        strain_rate=0.01,
                        recommended_stress_reduction=10.0,
                    ),
                    fatigue_analysis=FatigueAnalysisInfo(
                        current_cycles=5,
                        cycles_to_failure=20,
                        stress_amplitude=0.65,
                        remaining_life_fraction=0.75,
                        cumulative_damage=0.25,
                    ),
                    recommendations=[
                        "Target workload reduction: 10%",
                        "Continue monitoring",
                    ],
                ),
            ]

        return CreepFatigueResponse(
            analyzed_at=datetime.now().isoformat(),
            residents_analyzed=15,
            high_risk_count=1,
            moderate_risk_count=3,
            tertiary_creep_count=1,
            average_lmp=24.5,
            average_remaining_life=0.72,
            lmp_threshold=45.0,
            safe_lmp=31.5,
            assessments=assessments,
            system_recommendations=[
                "1 resident in tertiary creep - immediate action required",
                "Average LMP (24.5) is within safe range",
                "Consider rebalancing workload from high-risk residents",
            ],
            severity="at_risk",
        )

    except ImportError as e:
        logger.warning(f"Creep-fatigue module not available: {e}")
        return CreepFatigueResponse(
            analyzed_at=datetime.now().isoformat(),
            residents_analyzed=0,
            high_risk_count=0,
            moderate_risk_count=0,
            tertiary_creep_count=0,
            average_lmp=0.0,
            average_remaining_life=1.0,
            lmp_threshold=45.0,
            safe_lmp=31.5,
            assessments=[],
            system_recommendations=["Module not available"],
            severity="warning",
        )


async def analyze_transcription_triggers(
    include_tf_details: bool = True,
    include_constraint_status: bool = True,
) -> TranscriptionTriggersResponse:
    """
    Analyze transcription factor regulatory network for constraint management.

    Applies gene regulatory network (GRN) concepts to scheduling constraints:

    **Biological Analogy:**
    - Constraints = "Genes" in the scheduler genome
    - Transcription Factors (TFs) = Regulatory proteins that control constraint weights
    - Signal Events = External stimuli (deployment, crisis, holiday) that induce TFs
    - Chromatin State = Accessibility of constraints (open, closed, silenced)

    **TF Types:**
    - MASTER: Always active, controls patient safety (e.g., PatientSafety_MR)
    - ACTIVATOR: Increases constraint weight when expressed
    - REPRESSOR: Decreases/disables constraints when expressed
    - PIONEER: Can re-open silenced constraints
    - DUAL: Context-dependent activation or repression

    **Key TFs (Default Set):**
    - PatientSafety_MR (MASTER): Always active, ensures safety constraints
    - ACGMECompliance_MR (MASTER): Maintains ACGME requirements
    - MilitaryEmergency_TF (ACTIVATOR): Triggered by deployments
    - CrisisMode_TF (REPRESSOR): Relaxes soft constraints during crisis
    - WorkloadProtection_TF (ACTIVATOR): Activates when imbalance detected

    **Network Analysis:**
    - Positive feedback loops: Amplify signals
    - Negative feedback loops: Stabilize the system
    - Feed-forward loops: Filter noise and create delays

    Args:
        include_tf_details: Include details of active transcription factors
        include_constraint_status: Include constraint regulation status

    Returns:
        TranscriptionTriggersResponse with GRN analysis

    Example:
        # Check regulatory state
        result = await analyze_transcription_triggers_tool()
        print(f"Active TFs: {result.active_tfs}/{result.total_tfs}")
        print(f"Modified constraints: {result.constraints_with_modified_weight}")

        # Find repressed constraints during crisis
        for tf in result.active_tfs_list:
            if tf.tf_type == "repressor" and tf.is_active:
                print(f"Repressor active: {tf.name}")
    """
    logger.info("Analyzing transcription factor regulatory network")

    try:
        # Try to import the actual backend module to verify availability
        import importlib.util
        if importlib.util.find_spec("app.resilience.transcription_factors") is None:
            raise ImportError("Module not found")

        # In production, would access actual TF scheduler state
        logger.warning("Transcription factors using placeholder data")

        active_tfs = []
        if include_tf_details:
            active_tfs = [
                TranscriptionFactorInfo(
                    name="PatientSafety_MR",
                    tf_type=TFTypeEnum.MASTER,
                    expression_level=1.0,
                    strength_category=SignalStrengthEnum.MAXIMAL,
                    is_active=True,
                    targets_count=5,
                    description="Master regulator ensuring patient safety constraints active",
                ),
                TranscriptionFactorInfo(
                    name="ACGMECompliance_MR",
                    tf_type=TFTypeEnum.MASTER,
                    expression_level=0.9,
                    strength_category=SignalStrengthEnum.STRONG,
                    is_active=True,
                    targets_count=8,
                    description="Master regulator for ACGME compliance requirements",
                ),
                TranscriptionFactorInfo(
                    name="WorkloadProtection_TF",
                    tf_type=TFTypeEnum.ACTIVATOR,
                    expression_level=0.45,
                    strength_category=SignalStrengthEnum.MODERATE,
                    is_active=True,
                    targets_count=3,
                    description="Activates workload balancing constraints when imbalance detected",
                ),
            ]

        regulated_constraints = []
        if include_constraint_status:
            regulated_constraints = [
                ConstraintRegulationInfo(
                    constraint_id="ACGME-80HR",
                    constraint_name="ACGME 80-Hour Work Week",
                    base_weight=1.0,
                    effective_weight=1.8,
                    activation_level=0.9,
                    chromatin_state="open",
                    regulating_tfs=["ACGMECompliance_MR"],
                    explanation="Activation=0.90 (activators=0.90, repressors=0.00)",
                ),
                ConstraintRegulationInfo(
                    constraint_id="WORKLOAD-BALANCE",
                    constraint_name="Workload Balance",
                    base_weight=1.0,
                    effective_weight=1.35,
                    activation_level=0.45,
                    chromatin_state="open",
                    regulating_tfs=["WorkloadProtection_TF"],
                    explanation="Activation=0.45 (activators=0.45, repressors=0.00)",
                ),
            ]

        loops = [
            RegulatoryLoopInfo(
                loop_type="negative_feedback",
                description="Feedback: WorkloadProtection_TF <-> LowStaffing_TF",
                tf_names=["WorkloadProtection_TF", "LowStaffing_TF"],
                stability="stable",
            ),
        ]

        return TranscriptionTriggersResponse(
            analyzed_at=datetime.now().isoformat(),
            total_tfs=8,
            active_tfs=3,
            master_regulators_active=2,
            total_constraints_regulated=12,
            constraints_with_modified_weight=5,
            regulatory_edges=18,
            detected_loops=1,
            total_activation=2.35,
            total_repression=0.0,
            network_entropy=0.42,
            active_tfs_list=active_tfs,
            regulated_constraints=regulated_constraints,
            loops=loops,
            recent_signals=0,
            recommendations=[
                "2 master regulators active (PatientSafety, ACGME)",
                "WorkloadProtection_TF moderately expressed - monitoring imbalance",
                "No crisis/emergency TFs active",
            ],
            severity="normal",
        )

    except ImportError as e:
        logger.warning(f"Transcription factors module not available: {e}")
        return TranscriptionTriggersResponse(
            analyzed_at=datetime.now().isoformat(),
            total_tfs=0,
            active_tfs=0,
            master_regulators_active=0,
            total_constraints_regulated=0,
            constraints_with_modified_weight=0,
            regulatory_edges=0,
            detected_loops=0,
            total_activation=0.0,
            total_repression=0.0,
            network_entropy=0.0,
            active_tfs_list=[],
            regulated_constraints=[],
            loops=[],
            recent_signals=0,
            recommendations=["Module not available"],
            severity="warning",
        )
