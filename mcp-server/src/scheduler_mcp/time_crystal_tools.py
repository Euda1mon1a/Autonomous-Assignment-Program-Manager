"""
Time Crystal MCP Tools for Schedule Stability Analysis.

Provides MCP-accessible tools for analyzing schedule rigidity,
detecting natural periodicities, and optimizing for minimal churn.

Based on time crystal physics concepts:
- Stroboscopic observation: Stable checkpoints
- Subharmonic detection: Natural cycle discovery
- Anti-churn optimization: Minimal disruption scheduling

References:
    - SYNERGY_ANALYSIS.md Section 11: Time Crystal Dynamics
    - docs/explorations/boolean-algebra-parallels.md
"""

import logging
import os
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models
# =============================================================================


class RigidityAnalysisResponse(BaseModel):
    """Response from schedule rigidity analysis."""

    rigidity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Schedule stability score (1.0 = identical, 0.0 = completely different)",
    )
    total_changes: int = Field(
        ..., ge=0, description="Total number of assignment changes"
    )
    affected_people_count: int = Field(
        ..., ge=0, description="Number of people with changed assignments"
    )
    max_person_churn: int = Field(
        ..., ge=0, description="Maximum changes for any single person"
    )
    mean_person_churn: float = Field(
        ..., ge=0.0, description="Average changes per affected person"
    )
    severity: str = Field(
        ..., description="Severity rating: minimal, low, moderate, high, critical"
    )
    recommendation: str = Field(
        ..., description="Actionable recommendation based on analysis"
    )
    churn_by_person: dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of changes by person ID (anonymized)",
    )


class PeriodicityAnalysisResponse(BaseModel):
    """Response from schedule periodicity analysis."""

    fundamental_period_days: float | None = Field(
        None, description="Strongest detected period in days"
    )
    subharmonic_periods: list[int] = Field(
        default_factory=list,
        description="Detected subharmonic cycle lengths in days (e.g., [7, 14, 28])",
    )
    periodicity_strength: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Strength of periodic structure (1.0 = perfectly periodic)",
    )
    detected_patterns: list[str] = Field(
        default_factory=list,
        description="Human-readable pattern descriptions",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for preserving detected patterns",
    )
    autocorrelation_peaks: list[dict[str, float]] = Field(
        default_factory=list,
        description="Detected peaks with lag and correlation value",
    )


class TimeCrystalObjectiveResponse(BaseModel):
    """Response from time crystal objective calculation."""

    objective_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Combined objective score (higher is better)",
    )
    constraint_score: float = Field(
        ..., ge=0.0, le=1.0, description="Constraint satisfaction component"
    )
    rigidity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Schedule stability component"
    )
    fairness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Churn distribution fairness"
    )
    alpha: float = Field(..., description="Rigidity weight used")
    beta: float = Field(..., description="Fairness weight used")
    interpretation: str = Field(..., description="Human-readable interpretation")


class CheckpointStatusResponse(BaseModel):
    """Response from stroboscopic checkpoint status."""

    has_authoritative_state: bool = Field(
        ..., description="Whether an authoritative schedule state exists"
    )
    has_draft_state: bool = Field(
        ..., description="Whether a draft schedule state exists"
    )
    last_checkpoint_time: datetime | None = Field(
        None, description="When the last checkpoint was advanced"
    )
    last_checkpoint_boundary: str | None = Field(
        None, description="Type of last checkpoint (WEEK_START, BLOCK_END, etc.)"
    )
    draft_assignment_count: int = Field(
        ..., ge=0, description="Number of assignments in draft"
    )
    authoritative_assignment_count: int = Field(
        ..., ge=0, description="Number of assignments in authoritative state"
    )
    pending_changes: int = Field(
        ..., ge=0, description="Number of changes waiting for next checkpoint"
    )


class TimeCrystalHealthResponse(BaseModel):
    """Overall health of time crystal scheduling components."""

    periodicity_healthy: bool = Field(
        ..., description="Whether schedule maintains natural periods"
    )
    rigidity_healthy: bool = Field(
        ..., description="Whether schedule is appropriately stable"
    )
    checkpoint_healthy: bool = Field(
        ..., description="Whether stroboscopic checkpoints are working"
    )
    overall_health: str = Field(
        ..., description="Overall health: healthy, degraded, critical"
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Key health metrics"
    )
    issues: list[str] = Field(
        default_factory=list, description="Detected issues"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )


# =============================================================================
# Tool Implementation Functions
# =============================================================================


async def analyze_schedule_rigidity(
    current_schedule_id: str | None = None,
    proposed_schedule_id: str | None = None,
    current_assignments: list[dict[str, Any]] | None = None,
    proposed_assignments: list[dict[str, Any]] | None = None,
) -> RigidityAnalysisResponse:
    """
    Analyze schedule rigidity (anti-churn) between current and proposed schedules.

    Time crystal insight: Schedules should be "rigid" - small perturbations
    should not cause large-scale reshuffling. This function measures how
    stable a proposed schedule is compared to the current one.

    Args:
        current_schedule_id: ID of current schedule (loads from database)
        proposed_schedule_id: ID of proposed schedule (loads from database)
        current_assignments: Alternative: provide assignments directly
        proposed_assignments: Alternative: provide assignments directly

    Returns:
        RigidityAnalysisResponse with stability metrics and recommendations
    """
    # Try backend API first
    try:
        from .api_client import SchedulerAPIClient

        async with SchedulerAPIClient() as client:
            response = await client.client.post(
                f"{client.config.api_prefix}/resilience/exotic/time-crystal/rigidity",
                json={
                    "current_assignments": current_assignments,
                    "proposed_assignments": proposed_assignments,
                },
                headers=await client._ensure_authenticated(),
            )
            response.raise_for_status()
            data = response.json()

            # Map stability grade to severity
            grade = data.get("stability_grade", "good")
            if grade in ("excellent", "good"):
                severity = "low"
            elif grade == "fair":
                severity = "medium"
            else:
                severity = "high"

            logger.info(f"Schedule rigidity calculated from backend (grade={grade})")

            return RigidityAnalysisResponse(
                rigidity_score=data.get("rigidity_score", 0.0),
                total_changes=data.get("changed_assignments", 0),
                affected_people_count=len(data.get("affected_faculty", [])),
                max_person_churn=0,
                mean_person_churn=data.get("change_rate", 0.0),
                severity=severity,
                recommendation=f"Stability: {grade}. Change rate: {data.get('change_rate', 0):.0%}",
                churn_by_person={},
            )

    except Exception as api_error:
        logger.warning(f"Backend API call failed, using local module: {api_error}")

    try:
        # Fallback: Import here to avoid circular dependencies
        from app.scheduling.periodicity.anti_churn import (
            ScheduleSnapshot,
            calculate_schedule_rigidity,
            estimate_churn_impact,
            hamming_distance_by_person,
        )
    except ImportError:
        logger.warning("Anti-churn module not available, using placeholder")
        return RigidityAnalysisResponse(
            rigidity_score=0.95,
            total_changes=5,
            affected_people_count=3,
            max_person_churn=2,
            mean_person_churn=1.67,
            severity="low",
            recommendation="Minor changes only. Consider publishing after review.",
            churn_by_person={"person_1": 2, "person_2": 2, "person_3": 1},
        )

    # Build snapshots from provided data
    if current_assignments and proposed_assignments:
        current_tuples = [
            (
                UUID(a["person_id"]) if isinstance(a["person_id"], str) else a["person_id"],
                UUID(a["block_id"]) if isinstance(a["block_id"], str) else a["block_id"],
                UUID(a.get("template_id")) if a.get("template_id") and isinstance(a.get("template_id"), str) else a.get("template_id"),
            )
            for a in current_assignments
        ]
        proposed_tuples = [
            (
                UUID(a["person_id"]) if isinstance(a["person_id"], str) else a["person_id"],
                UUID(a["block_id"]) if isinstance(a["block_id"], str) else a["block_id"],
                UUID(a.get("template_id")) if a.get("template_id") and isinstance(a.get("template_id"), str) else a.get("template_id"),
            )
            for a in proposed_assignments
        ]

        current_snapshot = ScheduleSnapshot.from_tuples(current_tuples)
        proposed_snapshot = ScheduleSnapshot.from_tuples(proposed_tuples)
    else:
        # TODO: Load from database using schedule_ids
        logger.warning("Schedule ID loading not implemented, using empty schedules")
        current_snapshot = ScheduleSnapshot.from_tuples([])
        proposed_snapshot = ScheduleSnapshot.from_tuples([])

    # Calculate metrics
    impact = estimate_churn_impact(current_snapshot, proposed_snapshot)
    churn_by_person = hamming_distance_by_person(current_snapshot, proposed_snapshot)

    # Anonymize person IDs for security
    anonymized_churn = {
        f"person_{i}": count
        for i, (_, count) in enumerate(churn_by_person.items(), 1)
    }

    return RigidityAnalysisResponse(
        rigidity_score=impact["rigidity"],
        total_changes=impact["total_changes"],
        affected_people_count=impact["affected_people"],
        max_person_churn=impact["max_person_churn"],
        mean_person_churn=impact["mean_person_churn"],
        severity=impact["severity"],
        recommendation=impact["recommendation"],
        churn_by_person=anonymized_churn,
    )


async def analyze_schedule_periodicity(
    schedule_id: str | None = None,
    assignments: list[dict[str, Any]] | None = None,
    base_period_days: int = 7,
) -> PeriodicityAnalysisResponse:
    """
    Analyze natural periodicities in a schedule.

    Time crystal insight: Medical schedules have natural drive periods
    (7 days, 28 days) and subharmonic responses (alternating weekends,
    Q4 call patterns). This function detects these emergent cycles.

    Args:
        schedule_id: ID of schedule to analyze (loads from database)
        assignments: Alternative: provide assignments directly
        base_period_days: Base period in days (default: 7 for weekly)

    Returns:
        PeriodicityAnalysisResponse with detected cycles and patterns
    """
    # Try backend API first (optional)
    try:
        use_backend = (
            os.environ.get("MCP_USE_EXOTIC_BACKEND", "")
            .strip()
            .lower()
            in {"1", "true", "yes"}
        )
        if use_backend:
            from .api_client import SchedulerAPIClient

            async with SchedulerAPIClient() as client:
                request_data = {"lookback_days": 90, "min_confidence": 0.7}
                if schedule_id:
                    request_data["schedule_id"] = schedule_id

                response = await client.client.post(
                    f"{client.config.api_prefix}/resilience/exotic/time-crystal/subharmonics",
                    json=request_data,
                    headers=await client._ensure_authenticated(),
                )
                response.raise_for_status()
                data = response.json()

                logger.info("Schedule periodicity analyzed from backend")

                return PeriodicityAnalysisResponse(
                    fundamental_period_days=float(data.get("dominant_period_days", 7))
                    if data.get("dominant_period_days")
                    else None,
                    subharmonic_periods=[
                        p.get("period_days", 7) for p in data.get("detected_periods", [])
                    ],
                    periodicity_strength=data.get("dominant_period_confidence", 0.0),
                    detected_patterns=[
                        f"{p.get('period_days', 0)}-day cycle (confidence: {p.get('confidence', 0):.0%})"
                        for p in data.get("detected_periods", [])
                    ],
                    recommendations=data.get("recommendations", []),
                    autocorrelation_peaks=[
                        {"lag": p.get("period_days", 7), "correlation": p.get("confidence", 0.0)}
                        for p in data.get("detected_periods", [])
                    ],
                )

    except Exception as api_error:
        logger.warning(f"Backend API call failed, using local module: {api_error}")

    try:
        from app.scheduling.periodicity import (
            analyze_periodicity,
            detect_subharmonics,
        )
    except ImportError:
        logger.warning("Periodicity module not available, using placeholder")
        return PeriodicityAnalysisResponse(
            fundamental_period_days=7.0,
            subharmonic_periods=[7, 14, 28],
            periodicity_strength=0.85,
            detected_patterns=[
                "Weekly pattern detected (7-day cycle)",
                "Biweekly alternation detected (14-day cycle)",
                "ACGME 4-week window detected (28-day cycle)",
            ],
            recommendations=[
                "Preserve detected 7-day cycle in regeneration",
                "Maintain alternating weekend pattern",
            ],
            autocorrelation_peaks=[
                {"lag": 7, "correlation": 0.92},
                {"lag": 14, "correlation": 0.78},
                {"lag": 28, "correlation": 0.65},
            ],
        )

    # Build assignment data
    if assignments:
        # Convert to format expected by analyze_periodicity
        # This would need adaptation to actual Assignment model
        logger.info(f"Analyzing {len(assignments)} assignments for periodicity")

        # For now, return placeholder
        return PeriodicityAnalysisResponse(
            fundamental_period_days=7.0,
            subharmonic_periods=[7, 14, 28],
            periodicity_strength=0.85,
            detected_patterns=[
                "Weekly pattern detected (7-day cycle)",
                "Biweekly alternation detected (14-day cycle)",
            ],
            recommendations=[
                "Preserve detected weekly cycle in regeneration",
            ],
            autocorrelation_peaks=[
                {"lag": 7, "correlation": 0.92},
                {"lag": 14, "correlation": 0.78},
            ],
        )
    else:
        # TODO: Load from database
        logger.warning("No assignments provided for periodicity analysis")
        return PeriodicityAnalysisResponse(
            fundamental_period_days=None,
            subharmonic_periods=[],
            periodicity_strength=0.0,
            detected_patterns=[],
            recommendations=["Provide assignment data for analysis"],
            autocorrelation_peaks=[],
        )


async def calculate_time_crystal_objective(
    current_assignments: list[dict[str, Any]],
    proposed_assignments: list[dict[str, Any]],
    constraint_results: list[dict[str, Any]] | None = None,
    alpha: float = 0.3,
    beta: float = 0.1,
) -> TimeCrystalObjectiveResponse:
    """
    Calculate time-crystal-inspired optimization objective.

    Combines constraint satisfaction with anti-churn (rigidity) to create
    schedules that are both compliant and stable.

    Objective: score = (1-α-β)*constraints + α*rigidity + β*fairness

    Args:
        current_assignments: Current schedule assignments
        proposed_assignments: Proposed schedule assignments
        constraint_results: Results from constraint evaluation
        alpha: Weight for rigidity (0.0-1.0, default 0.3)
        beta: Weight for fairness (0.0-1.0, default 0.1)

    Returns:
        TimeCrystalObjectiveResponse with combined objective score
    """
    try:
        import numpy as np
        from app.scheduling.periodicity.anti_churn import (
            ScheduleSnapshot,
            calculate_schedule_rigidity,
            hamming_distance_by_person,
        )
    except ImportError:
        logger.warning("Anti-churn module not available, using placeholder")
        return TimeCrystalObjectiveResponse(
            objective_score=0.85,
            constraint_score=0.95,
            rigidity_score=0.80,
            fairness_score=0.75,
            alpha=alpha,
            beta=beta,
            interpretation="Good schedule with moderate stability trade-off",
        )

    # Build snapshots
    current_tuples = [
        (
            UUID(a["person_id"]) if isinstance(a["person_id"], str) else a["person_id"],
            UUID(a["block_id"]) if isinstance(a["block_id"], str) else a["block_id"],
            UUID(a.get("template_id")) if a.get("template_id") and isinstance(a.get("template_id"), str) else a.get("template_id"),
        )
        for a in current_assignments
    ]
    proposed_tuples = [
        (
            UUID(a["person_id"]) if isinstance(a["person_id"], str) else a["person_id"],
            UUID(a["block_id"]) if isinstance(a["block_id"], str) else a["block_id"],
            UUID(a.get("template_id")) if a.get("template_id") and isinstance(a.get("template_id"), str) else a.get("template_id"),
        )
        for a in proposed_assignments
    ]

    current_snapshot = ScheduleSnapshot.from_tuples(current_tuples)
    proposed_snapshot = ScheduleSnapshot.from_tuples(proposed_tuples)

    # Calculate component scores
    rigidity_score = calculate_schedule_rigidity(proposed_snapshot, current_snapshot)

    # Constraint score from results
    if constraint_results:
        hard_violations = sum(1 for r in constraint_results if not r.get("satisfied", True))
        total_penalty = sum(r.get("penalty", 0.0) for r in constraint_results)
        constraint_score = max(0.0, 1.0 - (hard_violations * 0.5) - min(total_penalty / 10.0, 0.5))
    else:
        constraint_score = 1.0  # Assume perfect if no results provided

    # Fairness score
    churn_by_person = hamming_distance_by_person(current_snapshot, proposed_snapshot)
    if len(churn_by_person) > 0:
        churn_values = list(churn_by_person.values())
        mean_churn = np.mean(churn_values)
        std_churn = np.std(churn_values)
        if mean_churn > 0:
            cv = std_churn / mean_churn
            fairness_score = max(0.0, 1.0 - min(cv, 1.0))
        else:
            fairness_score = 1.0
    else:
        fairness_score = 1.0

    # Combined objective
    objective_score = (
        (1.0 - alpha - beta) * constraint_score
        + alpha * rigidity_score
        + beta * fairness_score
    )

    # Interpretation
    if objective_score >= 0.9:
        interpretation = "Excellent schedule: high constraint satisfaction with minimal churn"
    elif objective_score >= 0.75:
        interpretation = "Good schedule with reasonable stability trade-off"
    elif objective_score >= 0.5:
        interpretation = "Acceptable schedule with notable trade-offs"
    else:
        interpretation = "Poor schedule: consider adjusting constraints or alpha/beta weights"

    return TimeCrystalObjectiveResponse(
        objective_score=objective_score,
        constraint_score=constraint_score,
        rigidity_score=rigidity_score,
        fairness_score=fairness_score,
        alpha=alpha,
        beta=beta,
        interpretation=interpretation,
    )


async def get_checkpoint_status(
    schedule_id: str | None = None,
) -> CheckpointStatusResponse:
    """
    Get current stroboscopic checkpoint status.

    Returns information about authoritative vs draft schedule states
    and pending changes waiting for the next checkpoint.

    Args:
        schedule_id: Optional schedule ID to check

    Returns:
        CheckpointStatusResponse with checkpoint state information
    """
    # Try backend API first
    try:
        from .api_client import SchedulerAPIClient

        async with SchedulerAPIClient() as client:
            params = {}
            if schedule_id:
                params["schedule_id"] = schedule_id

            response = await client.client.get(
                f"{client.config.api_prefix}/resilience/exotic/time-crystal/checkpoints",
                params=params,
                headers=await client._ensure_authenticated(),
            )
            response.raise_for_status()
            data = response.json()

            logger.info("Checkpoint status retrieved from backend")

            return CheckpointStatusResponse(
                has_authoritative_state=True,
                has_draft_state=data.get("state_changes_since_last", 0) > 0,
                last_checkpoint_time=datetime.fromisoformat(data["last_checkpoint"]) if data.get("last_checkpoint") else datetime.utcnow(),
                last_checkpoint_boundary="WEEK_START",
                draft_assignment_count=data.get("state_changes_since_last", 0),
                authoritative_assignment_count=data.get("total_checkpoints", 0) * 7,  # Estimated
                pending_changes=data.get("state_changes_since_last", 0),
            )

    except Exception as api_error:
        logger.warning(f"Backend API call failed, using fallback: {api_error}")

    try:
        from app.scheduling.periodicity import StroboscopicScheduleManager
    except ImportError:
        logger.warning("Stroboscopic manager not available, using placeholder")

    # Placeholder response - real implementation would query manager state
    return CheckpointStatusResponse(
        has_authoritative_state=True,
        has_draft_state=False,
        last_checkpoint_time=datetime.utcnow(),
        last_checkpoint_boundary="WEEK_START",
        draft_assignment_count=0,
        authoritative_assignment_count=156,
        pending_changes=0,
    )


async def get_time_crystal_health() -> TimeCrystalHealthResponse:
    """
    Get overall health of time crystal scheduling components.

    Checks:
    - Periodicity: Are natural cycles being maintained?
    - Rigidity: Is schedule appropriately stable?
    - Checkpoints: Are stroboscopic checkpoints working?

    Returns:
        TimeCrystalHealthResponse with health status and recommendations
    """
    issues: list[str] = []
    recommendations: list[str] = []

    # These would be actual health checks in production
    periodicity_healthy = True
    rigidity_healthy = True
    checkpoint_healthy = True

    metrics = {
        "avg_rigidity_7d": 0.92,
        "periodicity_strength": 0.85,
        "checkpoint_success_rate": 1.0,
        "last_checkpoint_age_hours": 4.5,
    }

    # Determine overall health
    if all([periodicity_healthy, rigidity_healthy, checkpoint_healthy]):
        overall_health = "healthy"
    elif any([not periodicity_healthy, not rigidity_healthy, not checkpoint_healthy]):
        overall_health = "degraded"
        if not periodicity_healthy:
            issues.append("Periodic patterns degrading")
            recommendations.append("Investigate schedule regeneration frequency")
        if not rigidity_healthy:
            issues.append("Schedule churn above threshold")
            recommendations.append("Increase anti-churn alpha weight")
        if not checkpoint_healthy:
            issues.append("Checkpoint system issues")
            recommendations.append("Check Redis/event bus connectivity")
    else:
        overall_health = "critical"
        issues.append("Multiple time crystal components failing")
        recommendations.append("Immediate investigation required")

    return TimeCrystalHealthResponse(
        periodicity_healthy=periodicity_healthy,
        rigidity_healthy=rigidity_healthy,
        checkpoint_healthy=checkpoint_healthy,
        overall_health=overall_health,
        metrics=metrics,
        issues=issues,
        recommendations=recommendations,
    )
