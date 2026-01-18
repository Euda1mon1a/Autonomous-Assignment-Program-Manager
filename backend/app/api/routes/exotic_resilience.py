"""
Exotic Resilience API Routes.

Exposes advanced resilience features for MCP tool integration:
- Thermodynamics (entropy, phase transitions, free energy)
- Immune System (AIS anomaly detection)
- Time Crystal (anti-churn, periodicity, stroboscopic checkpoints)
- Hopfield Networks (attractor basins, energy landscapes)

These endpoints provide real backend calculations to replace MCP placeholder data.

Created: 2025-12-30 (Session 024 - Marathon Execution)
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.decorators import require_feature_flag
from app.models.assignment import Assignment

# Import thermodynamics modules
from app.resilience.thermodynamics import (
    PhaseTransitionDetector,
    ScheduleEntropyMonitor,
    calculate_schedule_entropy,
    detect_critical_slowing,
    estimate_time_to_transition,
)

# Import immune system module
from app.resilience.immune_system import (
    Antibody,
    Detector,
    ScheduleImmuneSystem,
)

# Import time crystal / periodicity modules
from app.scheduling.periodicity import (
    ScheduleSnapshot,
    StroboscopicScheduleManager,
    SubharmonicDetector,
    calculate_schedule_rigidity,
)

# Import exotic frontier modules (Tier 5)
from app.resilience.exotic import (
    MetastabilityDetector,
    SpinGlassModel,
    CatastropheTheory,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


# --- Thermodynamics: Entropy ---
class EntropyAnalysisRequest(BaseModel):
    """Request for schedule entropy analysis."""

    schedule_id: UUID | None = Field(
        None, description="Schedule ID to analyze (uses active if not provided)"
    )
    start_date: str | None = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: str | None = Field(None, description="End date (YYYY-MM-DD)")


class EntropyMetricsResponse(BaseModel):
    """Schedule entropy analysis results."""

    person_entropy: float = Field(
        ..., description="Entropy of assignment distribution across faculty"
    )
    rotation_entropy: float = Field(
        ..., description="Entropy of rotation assignment distribution"
    )
    time_entropy: float = Field(..., description="Entropy of temporal distribution")
    joint_entropy: float = Field(..., description="Joint entropy across all dimensions")
    mutual_information: float = Field(
        ..., description="Information shared between dimensions"
    )
    normalized_entropy: float = Field(
        ..., description="Entropy relative to maximum possible (0-1)"
    )
    entropy_production_rate: float = Field(
        0.0, description="Rate of entropy generation over time"
    )
    interpretation: str = Field(
        ...,
        description="Human-readable interpretation",
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    computed_at: str = Field(..., description="Timestamp of analysis (ISO format)")
    source: str = Field("backend", description="Data source")


# --- Thermodynamics: Phase Transitions ---
class PhaseTransitionRequest(BaseModel):
    """Request for phase transition detection."""

    schedule_id: UUID | None = Field(None, description="Schedule ID to analyze")
    lookback_days: int = Field(
        30, ge=7, le=365, description="Days of history to analyze"
    )
    sensitivity: float = Field(
        1.0, ge=0.5, le=2.0, description="Detection sensitivity multiplier"
    )


class CriticalSignalResponse(BaseModel):
    """A detected early warning signal."""

    signal_type: str
    metric_name: str
    severity: str
    value: float
    threshold: float
    description: str
    detected_at: str


class PhaseTransitionResponse(BaseModel):
    """Phase transition risk assessment results."""

    overall_severity: str = Field(
        ...,
        description="Overall risk level: normal, elevated, high, critical, imminent",
    )
    signals: list[CriticalSignalResponse] = Field(
        default_factory=list, description="Detected early warning signals"
    )
    time_to_transition: float | None = Field(
        None, description="Estimated time until transition (hours)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    recommendations: list[str] = Field(
        default_factory=list, description="Suggested interventions"
    )
    source: str = Field("backend", description="Data source")


# --- Immune System: Assessment ---
class ImmuneAssessmentRequest(BaseModel):
    """Request for immune system assessment."""

    schedule_id: UUID | None = Field(None, description="Schedule ID to assess")
    feature_vector: list[float] | None = Field(
        None, description="Schedule feature vector (if precomputed)"
    )


class ImmuneAssessmentResponse(BaseModel):
    """Immune system assessment results."""

    is_anomaly: bool = Field(..., description="Whether schedule is anomalous")
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0, description="Anomaly severity (0=normal, 1=severe)"
    )
    matching_detectors: int = Field(
        ..., description="Number of detectors that triggered"
    )
    total_detectors: int = Field(..., description="Total number of active detectors")
    closest_detector_distance: float = Field(
        ..., description="Distance to nearest detector"
    )
    suggested_repairs: list[dict[str, Any]] = Field(
        default_factory=list, description="Suggested repair strategies"
    )
    immune_health: str = Field(
        ...,
        description="Overall immune system status: healthy, degraded, compromised",
    )
    source: str = Field("backend", description="Data source")


# --- Immune System: Memory Cells ---
class MemoryCellsResponse(BaseModel):
    """Memory cells status (past anomaly patterns)."""

    total_memory_cells: int = Field(..., description="Total stored anomaly patterns")
    recent_activations: int = Field(..., description="Activations in last 30 days")
    pattern_categories: dict[str, int] = Field(
        default_factory=dict, description="Count by pattern category"
    )
    oldest_pattern_age_days: int = Field(
        ..., description="Age of oldest stored pattern"
    )
    memory_utilization: float = Field(
        ..., ge=0.0, le=1.0, description="Memory capacity used"
    )
    source: str = Field("backend", description="Data source")


# --- Immune System: Antibody Analysis ---
class AntibodyAnalysisRequest(BaseModel):
    """Request for antibody analysis."""

    anomaly_signature: list[float] | None = Field(
        None, description="Feature vector of detected anomaly"
    )
    top_k: int = Field(5, ge=1, le=20, description="Number of top antibodies to return")


class AntibodyResponse(BaseModel):
    """A single antibody (repair strategy)."""

    antibody_id: str
    repair_type: str
    affinity: float
    success_rate: float
    avg_repair_time_minutes: float
    description: str


class AntibodyAnalysisResponse(BaseModel):
    """Antibody analysis results."""

    total_antibodies: int = Field(..., description="Total available repair strategies")
    matching_antibodies: list[AntibodyResponse] = Field(
        default_factory=list, description="Best matching antibodies"
    )
    recommended_repair: AntibodyResponse | None = Field(
        None, description="Best overall repair strategy"
    )
    coverage_score: float = Field(
        ..., ge=0.0, le=1.0, description="How well antibodies cover anomaly types"
    )
    source: str = Field("backend", description="Data source")


# --- Time Crystal: Rigidity ---
class RigidityRequest(BaseModel):
    """Request for schedule rigidity calculation."""

    current_schedule_id: UUID | None = Field(None, description="Current schedule ID")
    proposed_schedule_id: UUID | None = Field(
        None, description="Proposed schedule ID to compare"
    )
    # Alternative: provide assignment lists directly
    current_assignments: list[dict[str, str]] | None = Field(
        None, description="Current assignments as list of dicts"
    )
    proposed_assignments: list[dict[str, str]] | None = Field(
        None, description="Proposed assignments as list of dicts"
    )


class RigidityResponse(BaseModel):
    """Schedule rigidity analysis results."""

    rigidity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Schedule rigidity (1.0 = no changes, 0.0 = complete overhaul)",
    )
    changed_assignments: int = Field(..., description="Number of assignments changed")
    total_assignments: int = Field(..., description="Total assignments compared")
    change_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of assignments changed"
    )
    affected_faculty: list[str] = Field(
        default_factory=list, description="Faculty with changed assignments"
    )
    churn_analysis: dict[str, Any] = Field(
        default_factory=dict, description="Detailed churn breakdown"
    )
    stability_grade: str = Field(
        ...,
        description="Stability rating: excellent, good, fair, poor, unstable",
    )
    source: str = Field("backend", description="Data source")


# --- Time Crystal: Subharmonics ---
class SubharmonicRequest(BaseModel):
    """Request for subharmonic detection."""

    schedule_id: UUID | None = Field(None, description="Schedule ID to analyze")
    lookback_days: int = Field(
        90, ge=14, le=365, description="Days of history to analyze"
    )
    min_confidence: float = Field(
        0.7, ge=0.5, le=0.99, description="Minimum confidence threshold"
    )


class SubharmonicResponse(BaseModel):
    """Detected natural cycles in schedule."""

    detected_periods: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected periodic patterns"
    )
    dominant_period_days: int | None = Field(None, description="Most prominent period")
    dominant_period_confidence: float = Field(
        0.0, description="Confidence in dominant period"
    )
    acgme_alignment: dict[str, float] = Field(
        default_factory=dict, description="Alignment with ACGME windows"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    source: str = Field("backend", description="Data source")


# --- Time Crystal: Stroboscopic Checkpoints ---
class CheckpointResponse(BaseModel):
    """Stroboscopic checkpoint status."""

    total_checkpoints: int = Field(
        ..., description="Total checkpoints in schedule period"
    )
    next_checkpoint: str | None = Field(None, description="Next checkpoint timestamp")
    last_checkpoint: str | None = Field(None, description="Last checkpoint timestamp")
    checkpoint_interval_days: int = Field(7, description="Days between checkpoints")
    state_changes_since_last: int = Field(
        ..., description="Assignments changed since last checkpoint"
    )
    stability_since_last: float = Field(
        ..., ge=0.0, le=1.0, description="Stability score since last checkpoint"
    )
    source: str = Field("backend", description="Data source")


# --- Exotic: Metastability Detection ---
class MetastabilityRequest(BaseModel):
    """Request for metastability detection."""

    current_energy: float = Field(..., description="Current state energy level")
    energy_landscape: list[float] = Field(
        default_factory=list, description="Energies of nearby states"
    )
    barrier_samples: list[float] = Field(
        default_factory=list, description="Energy barriers to nearby states"
    )
    temperature: float = Field(1.0, ge=0.1, le=10.0, description="System temperature")


class MetastabilityResponse(BaseModel):
    """Metastability analysis results."""

    energy: float = Field(..., description="Current energy level")
    barrier_height: float = Field(
        ..., description="Energy barrier to nearest stable state"
    )
    escape_rate: float = Field(
        ..., description="Probability of spontaneous escape per time unit"
    )
    lifetime: float = Field(..., description="Expected lifetime in current state")
    is_metastable: bool = Field(..., description="True if trapped in local minimum")
    stability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Stability score (0-1)"
    )
    nearest_stable_state: float | None = Field(
        None, description="Energy of nearest true minimum"
    )
    risk_level: str = Field(
        ..., description="Risk level: low, moderate, high, critical"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations"
    )
    source: str = Field("backend", description="Data source")


class ReorganizationRiskRequest(BaseModel):
    """Request for reorganization risk prediction."""

    current_stability: float = Field(
        ..., ge=0.0, le=1.0, description="Current stability score"
    )
    external_perturbation: float = Field(
        ..., ge=0.0, description="Magnitude of external stress"
    )
    system_temperature: float = Field(
        1.0, ge=0.1, le=10.0, description="System agitation level"
    )


class ReorganizationRiskResponse(BaseModel):
    """Reorganization risk assessment."""

    risk_level: str = Field(
        ..., description="Risk level: low, moderate, high, critical"
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    interpretation: str = Field(..., description="Human-readable interpretation")
    effective_barrier: float = Field(..., description="Effective energy barrier")
    estimated_time_to_reorganization: float = Field(
        ..., description="Estimated time units until reorganization"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations"
    )
    source: str = Field("backend", description="Data source")


# --- Exotic: Spin Glass Model ---
class SpinGlassRequest(BaseModel):
    """Request for spin glass replica generation."""

    num_spins: int = Field(
        100, ge=10, le=1000, description="Number of binary variables"
    )
    num_replicas: int = Field(
        5, ge=1, le=20, description="Number of diverse replicas to generate"
    )
    temperature: float = Field(
        1.0, ge=0.1, le=10.0, description="System temperature for sampling"
    )
    frustration_level: float = Field(
        0.3, ge=0.0, le=1.0, description="Degree of conflicting constraints"
    )
    num_iterations: int = Field(
        1000, ge=100, le=10000, description="Monte Carlo iterations per replica"
    )


class SpinConfigurationResponse(BaseModel):
    """A single spin glass configuration."""

    energy: float = Field(..., description="Schedule quality (lower = better)")
    frustration: float = Field(
        ..., ge=0.0, le=1.0, description="Degree of constraint conflict"
    )
    magnetization: float = Field(
        ..., description="Overall bias (should be ~0 for balanced)"
    )
    overlap: float = Field(
        ..., ge=-1.0, le=1.0, description="Overlap with reference configuration"
    )


class SpinGlassResponse(BaseModel):
    """Spin glass ensemble results."""

    configurations: list[SpinConfigurationResponse] = Field(
        default_factory=list, description="Generated schedule replicas"
    )
    mean_energy: float = Field(..., description="Average energy across replicas")
    energy_std: float = Field(..., description="Energy standard deviation")
    mean_overlap: float = Field(..., description="Average pairwise overlap")
    diversity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Diversity score (1 - mean_overlap)"
    )
    landscape_ruggedness: float = Field(
        ..., ge=0.0, le=1.0, description="Energy landscape ruggedness"
    )
    difficulty: str = Field(
        ..., description="Optimization difficulty: easy, moderate, hard, very_hard"
    )
    source: str = Field("backend", description="Data source")


# --- Exotic: Catastrophe Theory ---
class CatastropheRequest(BaseModel):
    """Request for catastrophe prediction."""

    current_a: float = Field(..., description="Current asymmetry parameter")
    current_b: float = Field(..., description="Current bias parameter")
    da: float = Field(..., description="Change in asymmetry")
    db: float = Field(..., description="Change in bias")
    num_steps: int = Field(
        100, ge=10, le=1000, description="Number of simulation steps"
    )


class CatastrophePointResponse(BaseModel):
    """Detected catastrophe point."""

    a_critical: float = Field(..., description="Critical asymmetry value")
    b_critical: float = Field(..., description="Critical bias value")
    x_before: float = Field(..., description="State before jump")
    x_after: float = Field(..., description="State after jump")
    jump_magnitude: float = Field(..., description="Size of discontinuous jump")
    hysteresis_width: float = Field(..., description="Width of hysteresis region")


class CatastropheResponse(BaseModel):
    """Catastrophe theory analysis results."""

    catastrophe_detected: bool = Field(
        ..., description="Whether catastrophe is predicted"
    )
    catastrophe_point: CatastrophePointResponse | None = Field(
        None, description="Detected catastrophe point"
    )
    resilience_score: float = Field(..., ge=0.0, le=1.0, description="Resilience score")
    status: str = Field(..., description="Status: robust, stable, vulnerable, critical")
    is_safe: bool = Field(..., description="Whether system is safe from catastrophe")
    distance_to_catastrophe: float = Field(
        ..., description="Distance to catastrophe boundary"
    )
    current_distance_to_bifurcation: float = Field(
        ..., description="Current distance to bifurcation set"
    )
    warning: str = Field(..., description="Warning message")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations"
    )
    source: str = Field("backend", description="Data source")


# =============================================================================
# Thermodynamics Endpoints
# =============================================================================


@router.post("/thermodynamics/entropy", response_model=EntropyMetricsResponse)
@require_feature_flag("exotic_resilience_enabled")
async def analyze_schedule_entropy(
    request: EntropyAnalysisRequest,
    db: Session = Depends(get_db),
) -> EntropyMetricsResponse:
    """
    Analyze schedule entropy using information theory.

    Calculates Shannon entropy across multiple dimensions:
    - Person entropy: Workload distribution balance
    - Rotation entropy: Service coverage diversity
    - Time entropy: Temporal assignment balance
    - Joint entropy: Correlations between dimensions
    - Mutual information: Coupling between faculty and rotations

    High entropy = diverse but potentially chaotic
    Low entropy = concentrated but potentially vulnerable
    Optimal = moderate entropy with balanced distribution
    """
    logger.info(f"Analyzing schedule entropy: {request}")

    # Fetch assignments from database
    query = select(Assignment)
    if request.schedule_id:
        query = query.where(Assignment.schedule_id == request.schedule_id)

    result = db.execute(query)
    assignments = list(result.scalars().all())

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assignments found for analysis",
        )

    # Calculate entropy metrics
    metrics = calculate_schedule_entropy(assignments)

    # Interpret results
    interpretation = _interpret_entropy(metrics)
    recommendations = _get_entropy_recommendations(metrics)

    return EntropyMetricsResponse(
        person_entropy=metrics.person_entropy,
        rotation_entropy=metrics.rotation_entropy,
        time_entropy=metrics.time_entropy,
        joint_entropy=metrics.joint_entropy,
        mutual_information=metrics.mutual_information,
        normalized_entropy=metrics.normalized_entropy,
        entropy_production_rate=metrics.entropy_production_rate,
        interpretation=interpretation,
        recommendations=recommendations,
        computed_at=datetime.utcnow().isoformat(),
        source="backend",
    )


@router.post("/thermodynamics/phase-transition", response_model=PhaseTransitionResponse)
@require_feature_flag("exotic_resilience_enabled")
async def detect_phase_transition(
    request: PhaseTransitionRequest,
    db: Session = Depends(get_db),
) -> PhaseTransitionResponse:
    """
    Detect approaching phase transitions using critical phenomena theory.

    Monitors universal early warning signals:
    - Variance increase
    - Autocorrelation increase
    - Skewness changes
    - Flickering/intermittency
    - Critical slowing down

    These signals appear BEFORE system transitions regardless of mechanism.
    """
    logger.info(f"Detecting phase transitions: {request}")

    # Fetch recent assignments for time series analysis
    query = select(Assignment)
    if request.schedule_id:
        query = query.where(Assignment.schedule_id == request.schedule_id)

    result = db.execute(query)
    assignments = list(result.scalars().all())

    if len(assignments) < 10:
        # Not enough data for meaningful analysis
        return PhaseTransitionResponse(
            overall_severity="normal",
            signals=[],
            time_to_transition=None,
            confidence=0.0,
            recommendations=[
                "Insufficient data for phase transition analysis. "
                "Need at least 10 assignments."
            ],
            source="backend",
        )

    # Create detector and analyze
    detector = PhaseTransitionDetector(
        window_size=min(20, len(assignments) // 2),
        significance_threshold=0.05 / request.sensitivity,
    )

    # Build time series from assignments
    time_series = _build_utilization_time_series(assignments)

    # Detect critical signals
    risk_assessment = detector.assess_transition_risk(time_series)

    # Convert signals to response format
    signal_responses = [
        CriticalSignalResponse(
            signal_type=s.signal_type,
            metric_name=s.metric_name,
            severity=s.severity.value,
            value=s.value,
            threshold=s.threshold,
            description=s.description,
            detected_at=s.detected_at.isoformat(),
        )
        for s in risk_assessment.signals
    ]

    return PhaseTransitionResponse(
        overall_severity=risk_assessment.overall_severity.value,
        signals=signal_responses,
        time_to_transition=risk_assessment.time_to_transition,
        confidence=risk_assessment.confidence,
        recommendations=risk_assessment.recommendations,
        source="backend",
    )


# =============================================================================
# Immune System Endpoints
# =============================================================================


@router.post("/immune/assess", response_model=ImmuneAssessmentResponse)
@require_feature_flag("exotic_resilience_enabled")
async def assess_immune_response(
    request: ImmuneAssessmentRequest,
    db: Session = Depends(get_db),
) -> ImmuneAssessmentResponse:
    """
    Assess schedule anomalies using Artificial Immune System (AIS).

    Uses negative selection algorithm to detect "non-self" (anomalous)
    schedule states without explicit definition of all possible threats.

    Returns anomaly detection results and suggested repair strategies.
    """
    logger.info(f"Assessing immune response: {request}")

    # Initialize immune system
    immune = ScheduleImmuneSystem(feature_dims=10, detector_count=100)

    # Build schedule state from assignments
    query = select(Assignment)
    if request.schedule_id:
        query = query.where(Assignment.schedule_id == request.schedule_id)

    result = db.execute(query)
    assignments = list(result.scalars().all())

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assignments found for immune assessment",
        )

    # Build schedule state dict for immune system
    schedule_state = _build_schedule_state(assignments)

    # Check for anomalies using the actual API
    is_anomaly = immune.is_anomaly(schedule_state)
    anomaly_score = immune.get_anomaly_score(schedule_state)

    # Detect anomaly for details
    anomaly_report = immune.detect_anomaly(schedule_state)

    matching_detectors = len(anomaly_report.matching_detectors) if anomaly_report else 0
    closest_distance = anomaly_report.anomaly_score if anomaly_report else 0.0

    # Get repair suggestions if anomaly detected
    repairs = []
    if is_anomaly:
        antibody_result = immune.select_antibody(schedule_state)
        if antibody_result:
            name, antibody = antibody_result
            repairs.append(
                {
                    "name": name,
                    "description": antibody.description,
                    "affinity": antibody.get_affinity(
                        immune.extract_features(schedule_state)
                    ),
                }
            )

    # Determine immune health based on detector coverage
    total_detectors = immune.detector_count
    immune_health = _assess_immune_health(total_detectors, matching_detectors)

    return ImmuneAssessmentResponse(
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        matching_detectors=matching_detectors,
        total_detectors=total_detectors,
        closest_detector_distance=closest_distance,
        suggested_repairs=repairs,
        immune_health=immune_health,
        source="backend",
    )


@router.get("/immune/memory-cells", response_model=MemoryCellsResponse)
@require_feature_flag("exotic_resilience_enabled")
async def get_memory_cells(
    db: Session = Depends(get_db),
) -> MemoryCellsResponse:
    """
    Get status of immune system memory cells.

    Memory cells store past anomaly patterns for faster future detection.
    """
    logger.info("Getting immune memory cells status")

    # Initialize immune system
    immune = ScheduleImmuneSystem(feature_dims=10, detector_count=100)

    # Get statistics from immune system
    stats = immune.get_statistics()

    return MemoryCellsResponse(
        total_memory_cells=len(immune.detectors),
        recent_activations=stats.get("anomalies_detected", 0),
        pattern_categories={
            "detectors": len(immune.detectors),
            "antibodies": len(immune.antibodies),
        },
        oldest_pattern_age_days=0,  # No memory persistence in current implementation
        memory_utilization=len(immune.detectors) / max(immune.detector_count, 1),
        source="backend",
    )


@router.post("/immune/antibody-analysis", response_model=AntibodyAnalysisResponse)
@require_feature_flag("exotic_resilience_enabled")
async def analyze_antibodies(
    request: AntibodyAnalysisRequest,
    db: Session = Depends(get_db),
) -> AntibodyAnalysisResponse:
    """
    Analyze antibody (repair strategy) coverage for anomaly patterns.

    Uses clonal selection to find the best repair strategies for
    detected anomalies.
    """
    logger.info(f"Analyzing antibodies: {request}")

    # Initialize immune system
    immune = ScheduleImmuneSystem(feature_dims=10, detector_count=100)

    # Get all antibodies from the immune system
    total = len(immune.antibodies)

    # If anomaly signature provided, find matching antibodies
    matching = []
    recommended = None

    if request.anomaly_signature:
        import numpy as np

        feature_array = np.array(request.anomaly_signature)

        # Rank antibodies by affinity
        ranked = []
        for name, antibody in immune.antibodies.items():
            affinity = antibody.get_affinity(feature_array)
            if affinity > 0:
                ranked.append((name, antibody, affinity))

        ranked.sort(key=lambda x: x[2], reverse=True)
        ranked = ranked[: request.top_k]

        matching = [
            AntibodyResponse(
                antibody_id=str(ab.id),
                repair_type=name,
                affinity=aff,
                success_rate=ab.success_rate,
                avg_repair_time_minutes=5.0,  # Default estimate
                description=ab.description,
            )
            for name, ab, aff in ranked
        ]
        if matching:
            recommended = matching[0]

    # Calculate coverage score based on antibody count
    coverage = min(1.0, len(immune.antibodies) / 10.0)

    return AntibodyAnalysisResponse(
        total_antibodies=total,
        matching_antibodies=matching,
        recommended_repair=recommended,
        coverage_score=coverage,
        source="backend",
    )


# =============================================================================
# Time Crystal / Periodicity Endpoints
# =============================================================================


@router.post("/time-crystal/rigidity", response_model=RigidityResponse)
@require_feature_flag("exotic_resilience_enabled")
async def calculate_rigidity(
    request: RigidityRequest,
    db: Session = Depends(get_db),
) -> RigidityResponse:
    """
    Calculate schedule rigidity (stability under perturbation).

    Rigidity measures how much a schedule changes between versions:
    - 1.0 = perfectly rigid (no changes)
    - 0.0 = completely fluid (all assignments changed)

    High rigidity is desirable - small perturbations should not cause
    large-scale reshuffling.
    """
    logger.info(f"Calculating schedule rigidity: {request}")

    # Get current and proposed assignments
    current_assignments = []
    proposed_assignments = []

    if request.current_schedule_id:
        query = select(Assignment).where(
            Assignment.schedule_id == request.current_schedule_id
        )
        result = db.execute(query)
        current_assignments = list(result.scalars().all())

    if request.proposed_schedule_id:
        query = select(Assignment).where(
            Assignment.schedule_id == request.proposed_schedule_id
        )
        result = db.execute(query)
        proposed_assignments = list(result.scalars().all())

    # Or use provided assignment lists
    if request.current_assignments and not current_assignments:
        current_assignments = request.current_assignments
    if request.proposed_assignments and not proposed_assignments:
        proposed_assignments = request.proposed_assignments

    if not current_assignments or not proposed_assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide current and proposed assignments for comparison",
        )

    # Create snapshots
    current_snapshot = ScheduleSnapshot.from_assignments(current_assignments)
    proposed_snapshot = ScheduleSnapshot.from_assignments(proposed_assignments)

    # Calculate rigidity
    rigidity_result = calculate_schedule_rigidity(current_snapshot, proposed_snapshot)

    # Determine stability grade
    stability_grade = _grade_stability(rigidity_result.rigidity_score)

    return RigidityResponse(
        rigidity_score=rigidity_result.rigidity_score,
        changed_assignments=rigidity_result.changed_count,
        total_assignments=rigidity_result.total_count,
        change_rate=rigidity_result.change_rate,
        affected_faculty=rigidity_result.affected_faculty,
        churn_analysis=rigidity_result.churn_details,
        stability_grade=stability_grade,
        source="backend",
    )


@router.post("/time-crystal/subharmonics", response_model=SubharmonicResponse)
@require_feature_flag("exotic_resilience_enabled")
async def detect_subharmonics(
    request: SubharmonicRequest,
    db: Session = Depends(get_db),
) -> SubharmonicResponse:
    """
    Detect natural periodic cycles (subharmonics) in schedule patterns.

    Looks for:
    - 7-day weekly cycles
    - 14-day alternating weekend cycles
    - 28-day ACGME compliance windows
    - Q4 (4-day) call cycles
    """
    logger.info(f"Detecting subharmonics: {request}")

    # Fetch assignments
    query = select(Assignment)
    if request.schedule_id:
        query = query.where(Assignment.schedule_id == request.schedule_id)

    result = db.execute(query)
    assignments = list(result.scalars().all())

    if len(assignments) < 14:
        return SubharmonicResponse(
            detected_periods=[],
            dominant_period_days=None,
            dominant_period_confidence=0.0,
            acgme_alignment={},
            recommendations=[
                "Need at least 14 days of data to detect periodic patterns"
            ],
            source="backend",
        )

    # Create detector and analyze
    detector = SubharmonicDetector(min_confidence=request.min_confidence)
    detection_result = detector.detect(assignments, lookback_days=request.lookback_days)

    # Check alignment with ACGME windows
    acgme_alignment = detector.check_acgme_alignment(detection_result)

    return SubharmonicResponse(
        detected_periods=detection_result.periods,
        dominant_period_days=detection_result.dominant_period,
        dominant_period_confidence=detection_result.confidence,
        acgme_alignment=acgme_alignment,
        recommendations=detection_result.recommendations,
        source="backend",
    )


@router.get("/time-crystal/checkpoints", response_model=CheckpointResponse)
@require_feature_flag("exotic_resilience_enabled")
async def get_stroboscopic_checkpoints(
    schedule_id: UUID | None = None,
    db: Session = Depends(get_db),
) -> CheckpointResponse:
    """
    Get stroboscopic checkpoint status.

    Stroboscopic checkpoints are discrete boundaries where schedule state
    is captured. Changes between checkpoints are measured for anti-churn
    optimization.
    """
    logger.info(f"Getting stroboscopic checkpoints: schedule_id={schedule_id}")

    # Initialize manager
    manager = StroboscopicScheduleManager(checkpoint_interval_days=7)

    # Get checkpoint status
    status = manager.get_status(schedule_id)

    return CheckpointResponse(
        total_checkpoints=status.total_checkpoints,
        next_checkpoint=status.next_checkpoint.isoformat()
        if status.next_checkpoint
        else None,
        last_checkpoint=status.last_checkpoint.isoformat()
        if status.last_checkpoint
        else None,
        checkpoint_interval_days=status.interval_days,
        state_changes_since_last=status.changes_since_last,
        stability_since_last=status.stability_score,
        source="backend",
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _interpret_entropy(metrics) -> str:
    """Generate human-readable interpretation of entropy metrics."""
    if metrics.normalized_entropy < 0.3:
        return (
            "Low entropy: Schedule is highly concentrated. This may indicate "
            "workload imbalance or over-reliance on specific faculty."
        )
    elif metrics.normalized_entropy < 0.7:
        return (
            "Moderate entropy: Schedule has balanced diversity. Good mix of "
            "predictability and flexibility."
        )
    else:
        return (
            "High entropy: Schedule is highly diverse/chaotic. May need more "
            "structure to ensure consistent coverage."
        )


def _get_entropy_recommendations(metrics) -> list[str]:
    """Generate optimization recommendations based on entropy analysis."""
    recs = []

    if metrics.normalized_entropy < 0.3:
        recs.append("Consider distributing workload more evenly across faculty")
        recs.append("Review if any faculty are carrying disproportionate load")

    if metrics.mutual_information > 1.5:
        recs.append(
            "High coupling between faculty and rotations detected. "
            "Cross-training may improve flexibility."
        )

    if metrics.entropy_production_rate > 0.1:
        recs.append(
            "Schedule disorder is increasing over time. Consider stabilization."
        )

    return recs


def _build_utilization_time_series(assignments: list) -> list[float]:
    """Build utilization time series from assignments for phase transition analysis."""
    from collections import defaultdict

    # Group by date
    daily_counts = defaultdict(int)
    for a in assignments:
        if hasattr(a, "block") and hasattr(a.block, "date"):
            daily_counts[a.block.date] += 1

    # Convert to sorted list
    sorted_dates = sorted(daily_counts.keys())
    return [daily_counts[d] for d in sorted_dates]


def _extract_schedule_features(assignments: list) -> list[float]:
    """Extract feature vector from assignments for immune system analysis."""
    if not assignments:
        return [0.0] * 10

    # Simple feature extraction
    total = len(assignments)
    unique_faculty = len(
        set(a.person_id for a in assignments if hasattr(a, "person_id"))
    )
    unique_rotations = len(
        set(
            a.rotation_template_id
            for a in assignments
            if hasattr(a, "rotation_template_id") and a.rotation_template_id
        )
    )

    # Normalize features
    return [
        total / 100.0,  # Normalized total
        unique_faculty / 20.0,  # Normalized faculty count
        unique_rotations / 10.0,  # Normalized rotation count
        unique_faculty / max(total, 1),  # Faculty utilization
        unique_rotations / max(total, 1),  # Rotation diversity
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,  # Placeholder features
    ]


def _build_schedule_state(assignments: list) -> dict:
    """Build schedule state dict from assignments for immune system."""
    if not assignments:
        return {
            "total_blocks": 0,
            "covered_blocks": 0,
            "faculty_count": 0,
            "resident_count": 0,
            "acgme_violations": [],
            "avg_hours_per_week": 0.0,
            "supervision_ratio": 0.0,
            "workload_std_dev": 0.0,
            "schedule_changes": 0,
            "coverage_by_type": {},
        }

    # Extract unique people and estimate counts
    unique_people = set(a.person_id for a in assignments if hasattr(a, "person_id"))
    unique_blocks = set(a.block_id for a in assignments if hasattr(a, "block_id"))

    # Estimate coverage by rotation type
    coverage_by_type = {}
    for a in assignments:
        if hasattr(a, "rotation_template_id") and a.rotation_template_id:
            rot_id = str(a.rotation_template_id)
            coverage_by_type[rot_id] = coverage_by_type.get(rot_id, 0) + 1

    return {
        "total_blocks": len(unique_blocks) if unique_blocks else len(assignments),
        "covered_blocks": len(assignments),
        "faculty_count": len(unique_people),
        "resident_count": 0,  # Would need role info
        "acgme_violations": [],  # Would need ACGME validation
        "avg_hours_per_week": 40.0,  # Estimated
        "supervision_ratio": 1.0,  # Estimated
        "workload_std_dev": 0.1,  # Estimated
        "schedule_changes": 0,
        "coverage_by_type": coverage_by_type,
    }


def _assess_immune_health(total_detectors: int, matching: int) -> str:
    """Assess overall immune system health."""
    if total_detectors < 50:
        return "compromised"
    elif matching > total_detectors * 0.3:
        return "degraded"
    else:
        return "healthy"


def _grade_stability(rigidity: float) -> str:
    """Grade schedule stability based on rigidity score."""
    if rigidity >= 0.95:
        return "excellent"
    elif rigidity >= 0.85:
        return "good"
    elif rigidity >= 0.70:
        return "fair"
    elif rigidity >= 0.50:
        return "poor"
    else:
        return "unstable"


# =============================================================================
# Exotic Frontier Endpoints (Tier 5)
# =============================================================================


@router.post("/exotic/metastability", response_model=MetastabilityResponse)
@require_feature_flag("exotic_resilience_enabled")
async def analyze_metastability(
    request: MetastabilityRequest,
    db: Session = Depends(get_db),
) -> MetastabilityResponse:
    """
    Detect metastable states using statistical mechanics.

    Metastability occurs when a system is trapped in a local energy minimum
    (locally optimal but globally suboptimal). Uses Kramers escape rate theory
    to predict spontaneous transitions to more stable states.

    Applications:
    - Solver trapped in suboptimal schedule
    - Organization stuck in inefficient pattern
    - Risk of sudden reorganization (morale collapse, mass resignations)
    """
    logger.info(f"Analyzing metastability: {request}")

    # Initialize detector
    detector = MetastabilityDetector(temperature=request.temperature)

    # Analyze current state
    state = detector.analyze_state(
        current_energy=request.current_energy,
        energy_landscape=request.energy_landscape,
        barrier_samples=request.barrier_samples,
    )

    # Determine risk level
    if state.is_metastable:
        if state.barrier_height < 0.5:
            risk_level = "critical"
        elif state.barrier_height < 1.0:
            risk_level = "high"
        elif state.barrier_height < 2.0:
            risk_level = "moderate"
        else:
            risk_level = "low"
    else:
        risk_level = "low"

    # Generate recommendations
    recommendations = []
    if state.is_metastable:
        recommendations.append(
            f"System trapped in local minimum (barrier height: {state.barrier_height:.2f})"
        )
        if state.nearest_stable_state:
            recommendations.append(
                f"More stable state exists at energy {state.nearest_stable_state:.2f}"
            )
        if state.escape_rate > 0.1:
            recommendations.append(
                f"High escape probability: {state.escape_rate:.3f} per time unit"
            )
            recommendations.append(
                "Consider proactive reorganization before spontaneous transition"
            )
        else:
            recommendations.append(
                "Barrier is high - system relatively stable in current state"
            )
    else:
        recommendations.append(
            "No metastability detected - system in stable configuration"
        )

    return MetastabilityResponse(
        energy=state.energy,
        barrier_height=state.barrier_height,
        escape_rate=state.escape_rate,
        lifetime=state.lifetime,
        is_metastable=state.is_metastable,
        stability_score=state.stability_score,
        nearest_stable_state=state.nearest_stable_state,
        risk_level=risk_level,
        recommendations=recommendations,
        source="backend",
    )


@router.post("/exotic/reorganization-risk", response_model=ReorganizationRiskResponse)
@require_feature_flag("exotic_resilience_enabled")
async def predict_reorganization_risk(
    request: ReorganizationRiskRequest,
    db: Session = Depends(get_db),
) -> ReorganizationRiskResponse:
    """
    Predict risk of sudden system reorganization.

    Uses metastability theory to assess whether external perturbations
    could trigger sudden transitions (e.g., mass resignations, strikes,
    morale collapse).
    """
    logger.info(f"Predicting reorganization risk: {request}")

    # Initialize detector
    detector = MetastabilityDetector(temperature=request.system_temperature)

    # Assess risk
    result = detector.predict_reorganization_risk(
        current_stability=request.current_stability,
        external_perturbation=request.external_perturbation,
        system_temperature=request.system_temperature,
    )

    return ReorganizationRiskResponse(
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        interpretation=result["interpretation"],
        effective_barrier=result["effective_barrier"],
        estimated_time_to_reorganization=result["estimated_time_to_reorganization"],
        recommendations=result["recommendations"],
        source="backend",
    )


@router.post("/exotic/spin-glass", response_model=SpinGlassResponse)
@require_feature_flag("exotic_resilience_enabled")
async def generate_spin_glass_replicas(
    request: SpinGlassRequest,
    db: Session = Depends(get_db),
) -> SpinGlassResponse:
    """
    Generate diverse schedule replicas using spin glass model.

    Spin glass physics models frustrated systems where constraints conflict.
    Generates multiple equally-good but different schedules for:
    - Ensemble averaging (robustness)
    - Exploring solution space diversity
    - Understanding constraint frustration

    Uses Edwards-Anderson spin glass model with simulated annealing.
    """
    logger.info(f"Generating spin glass replicas: {request}")

    # Initialize spin glass model
    model = SpinGlassModel(
        num_spins=request.num_spins,
        temperature=request.temperature,
        frustration_level=request.frustration_level,
    )

    # Generate replica ensemble
    ensemble = model.generate_replica_ensemble(
        num_replicas=request.num_replicas,
        num_iterations=request.num_iterations,
    )

    # Assess landscape ruggedness
    ruggedness_info = model.assess_landscape_ruggedness(num_samples=100)

    # Convert configurations to response format
    config_responses = [
        SpinConfigurationResponse(
            energy=config.energy,
            frustration=config.frustration,
            magnetization=config.magnetization,
            overlap=config.overlap,
        )
        for config in ensemble.configurations
    ]

    return SpinGlassResponse(
        configurations=config_responses,
        mean_energy=ensemble.mean_energy,
        energy_std=ensemble.energy_std,
        mean_overlap=ensemble.mean_overlap,
        diversity_score=ensemble.diversity_score,
        landscape_ruggedness=ruggedness_info["ruggedness_score"],
        difficulty=ruggedness_info["difficulty"],
        source="backend",
    )


@router.post("/exotic/catastrophe", response_model=CatastropheResponse)
@require_feature_flag("exotic_resilience_enabled")
async def predict_catastrophe(
    request: CatastropheRequest,
    db: Session = Depends(get_db),
) -> CatastropheResponse:
    """
    Predict sudden system failures using catastrophe theory.

    Catastrophe theory (René Thom, 1972) studies how smooth parameter changes
    can cause sudden discontinuous transitions. Uses cusp catastrophe model
    to identify tipping points.

    Applications:
    - Predict sudden morale collapses from gradual stress accumulation
    - Identify bifurcation points where behavior changes qualitatively
    - Model hysteresis (forward/backward paths differ)

    Parameters:
    - a: Asymmetry factor (splitting parameter)
    - b: Bias factor (normal parameter)
    """
    logger.info(f"Predicting catastrophe: {request}")

    # Initialize catastrophe theory model
    model = CatastropheTheory()

    # Predict catastrophe jump
    catastrophe_point = model.predict_catastrophe_jump(
        current_a=request.current_a,
        current_b=request.current_b,
        da=request.da,
        db=request.db,
        num_steps=request.num_steps,
    )

    # Calculate resilience from catastrophe
    resilience = model.calculate_resilience_from_catastrophe(
        current_state=(request.current_a, request.current_b, 0.0),
        stress_direction=(request.da, request.db),
    )

    # Convert catastrophe point to response format
    catastrophe_point_response = None
    if catastrophe_point:
        catastrophe_point_response = CatastrophePointResponse(
            a_critical=catastrophe_point.a_critical,
            b_critical=catastrophe_point.b_critical,
            x_before=catastrophe_point.x_before,
            x_after=catastrophe_point.x_after,
            jump_magnitude=catastrophe_point.jump_magnitude,
            hysteresis_width=catastrophe_point.hysteresis_width,
        )

    # Generate recommendations based on status
    recommendations = []
    if resilience["status"] == "critical":
        recommendations.extend(
            [
                "URGENT: System approaching catastrophe boundary",
                "Reduce stress parameters immediately",
                "Prepare for potential sudden transition",
            ]
        )
    elif resilience["status"] == "vulnerable":
        recommendations.extend(
            [
                "System vulnerable to catastrophic transition",
                "Monitor stress parameters closely",
                "Plan contingency responses",
            ]
        )
    elif resilience["status"] == "stable":
        recommendations.append("System stable, continue monitoring")
    else:
        recommendations.append("System robust, low catastrophe risk")

    return CatastropheResponse(
        catastrophe_detected=catastrophe_point is not None,
        catastrophe_point=catastrophe_point_response,
        resilience_score=resilience["resilience_score"],
        status=resilience["status"],
        is_safe=resilience["is_safe"],
        distance_to_catastrophe=resilience["distance_to_catastrophe"],
        current_distance_to_bifurcation=resilience["current_distance_to_bifurcation"],
        warning=resilience["warning"],
        recommendations=recommendations,
        source="backend",
    )
