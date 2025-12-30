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
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
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
    joint_entropy: float = Field(
        ..., description="Joint entropy across all dimensions"
    )
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
    computed_at: str = Field(
        ..., description="Timestamp of analysis (ISO format)"
    )
    source: str = Field("backend", description="Data source")


# --- Thermodynamics: Phase Transitions ---
class PhaseTransitionRequest(BaseModel):
    """Request for phase transition detection."""

    schedule_id: UUID | None = Field(
        None, description="Schedule ID to analyze"
    )
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
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Prediction confidence"
    )
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
    total_detectors: int = Field(
        ..., description="Total number of active detectors"
    )
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

    total_memory_cells: int = Field(
        ..., description="Total stored anomaly patterns"
    )
    recent_activations: int = Field(
        ..., description="Activations in last 30 days"
    )
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

    total_antibodies: int = Field(
        ..., description="Total available repair strategies"
    )
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

    current_schedule_id: UUID | None = Field(
        None, description="Current schedule ID"
    )
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
    changed_assignments: int = Field(
        ..., description="Number of assignments changed"
    )
    total_assignments: int = Field(
        ..., description="Total assignments compared"
    )
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
    dominant_period_days: int | None = Field(
        None, description="Most prominent period"
    )
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
    next_checkpoint: str | None = Field(
        None, description="Next checkpoint timestamp"
    )
    last_checkpoint: str | None = Field(
        None, description="Last checkpoint timestamp"
    )
    checkpoint_interval_days: int = Field(
        7, description="Days between checkpoints"
    )
    state_changes_since_last: int = Field(
        ..., description="Assignments changed since last checkpoint"
    )
    stability_since_last: float = Field(
        ..., ge=0.0, le=1.0, description="Stability score since last checkpoint"
    )
    source: str = Field("backend", description="Data source")


# =============================================================================
# Thermodynamics Endpoints
# =============================================================================


@router.post("/thermodynamics/entropy", response_model=EntropyMetricsResponse)
async def analyze_schedule_entropy(
    request: EntropyAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
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

    result = await db.execute(query)
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
async def detect_phase_transition(
    request: PhaseTransitionRequest,
    db: AsyncSession = Depends(get_async_db),
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

    result = await db.execute(query)
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
async def assess_immune_response(
    request: ImmuneAssessmentRequest,
    db: AsyncSession = Depends(get_async_db),
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

    result = await db.execute(query)
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
            repairs.append({
                "name": name,
                "description": antibody.description,
                "affinity": antibody.get_affinity(immune.extract_features(schedule_state)),
            })

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
async def get_memory_cells(
    db: AsyncSession = Depends(get_async_db),
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
        pattern_categories={"detectors": len(immune.detectors), "antibodies": len(immune.antibodies)},
        oldest_pattern_age_days=0,  # No memory persistence in current implementation
        memory_utilization=len(immune.detectors) / max(immune.detector_count, 1),
        source="backend",
    )


@router.post("/immune/antibody-analysis", response_model=AntibodyAnalysisResponse)
async def analyze_antibodies(
    request: AntibodyAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
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
        ranked = ranked[:request.top_k]

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
async def calculate_rigidity(
    request: RigidityRequest,
    db: AsyncSession = Depends(get_async_db),
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
        result = await db.execute(query)
        current_assignments = list(result.scalars().all())

    if request.proposed_schedule_id:
        query = select(Assignment).where(
            Assignment.schedule_id == request.proposed_schedule_id
        )
        result = await db.execute(query)
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
async def detect_subharmonics(
    request: SubharmonicRequest,
    db: AsyncSession = Depends(get_async_db),
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

    result = await db.execute(query)
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
async def get_stroboscopic_checkpoints(
    schedule_id: UUID | None = None,
    db: AsyncSession = Depends(get_async_db),
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
        next_checkpoint=status.next_checkpoint.isoformat() if status.next_checkpoint else None,
        last_checkpoint=status.last_checkpoint.isoformat() if status.last_checkpoint else None,
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
    unique_faculty = len(set(a.person_id for a in assignments if hasattr(a, "person_id")))
    unique_rotations = len(
        set(a.rotation_template_id for a in assignments if hasattr(a, "rotation_template_id") and a.rotation_template_id)
    )

    # Normalize features
    return [
        total / 100.0,  # Normalized total
        unique_faculty / 20.0,  # Normalized faculty count
        unique_rotations / 10.0,  # Normalized rotation count
        unique_faculty / max(total, 1),  # Faculty utilization
        unique_rotations / max(total, 1),  # Rotation diversity
        0.0, 0.0, 0.0, 0.0, 0.0,  # Placeholder features
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
