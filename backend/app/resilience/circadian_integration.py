"""
Circadian Model Integration with Schedule Solver.

Integrates circadian phase response curve analysis into the constraint
programming solver to optimize schedules for circadian alignment.

Key Integration Points:
1. **Soft Constraint**: Penalize schedules with poor circadian quality
2. **Objective Function**: Maximize aggregate circadian quality score
3. **Pre-solver Analysis**: Identify residents at risk for circadian disruption
4. **Post-solver Validation**: Verify generated schedule maintains circadian health

Usage in Solver:
    from app.resilience.circadian_integration import CircadianObjective

    # During schedule optimization
    circadian_obj = CircadianObjective(weight=0.2)
    solver.add_objective(circadian_obj.compute_penalty(schedule))

Medical Residency Application:
- Prefer forward rotation (day→evening→night) over backward
- Minimize consecutive night shifts (limit phase drift)
- Allow recovery days after circadian-disrupting shifts
- Balance circadian load across residents equitably
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

# Use try/except to handle both package and standalone imports
try:
    from .circadian_model import (
        CircadianImpact,
        CircadianQualityLevel,
        CircadianScheduleAnalyzer,
        CircadianShiftType,
    )
except ImportError:
    # Standalone import (for testing)
    import circadian_model

    CircadianImpact = circadian_model.CircadianImpact
    CircadianQualityLevel = circadian_model.CircadianQualityLevel
    CircadianScheduleAnalyzer = circadian_model.CircadianScheduleAnalyzer
    CircadianShiftType = circadian_model.CircadianShiftType

logger = logging.getLogger(__name__)


# =============================================================================
# Solver Integration
# =============================================================================


@dataclass
class CircadianConstraintResult:
    """
    Result of circadian constraint evaluation.

    Attributes:
        satisfied: Whether constraint is satisfied
        penalty: Penalty value for soft constraint (0 = satisfied)
        violations: List of specific violations
        quality_score: Overall circadian quality (0-1)
        residents_at_risk: List of resident IDs with poor circadian quality
    """

    satisfied: bool
    penalty: float
    violations: list[str]
    quality_score: float
    residents_at_risk: list[UUID]


class CircadianObjective:
    """
    Circadian alignment optimization objective for schedule solver.

    Adds circadian quality as an objective to maximize during
    schedule generation. Higher quality = better circadian alignment.

    Weight Parameter:
        Controls importance relative to other objectives (e.g., coverage, preferences)
        Typical range: 0.1 - 0.3
        - 0.1: Low priority (basic circadian awareness)
        - 0.2: Moderate priority (balanced optimization)
        - 0.3: High priority (circadian health emphasized)
    """

    def __init__(self, weight: float = 0.2):
        """
        Initialize circadian objective.

        Args:
            weight: Objective weight (0-1), higher = more important
        """
        self.weight = weight
        self.analyzer = CircadianScheduleAnalyzer()
        logger.info(f"Initialized CircadianObjective with weight={weight}")

    def compute_penalty(self, schedule: list[dict]) -> float:
        """
        Compute penalty for circadian misalignment.

        Lower penalty = better circadian alignment.
        Used in solver objective function (minimize penalty).

        Args:
            schedule: List of shift assignments

        Returns:
            Penalty value (0 = perfect alignment)

        Example:
            >>> obj = CircadianObjective(weight=0.2)
            >>> penalty = obj.compute_penalty(schedule)
            >>> # Solver minimizes: total_penalty = coverage_penalty + 0.2 * circadian_penalty
        """
        # Get quality score (0-1, higher = better)
        quality_score = self.analyzer.compute_circadian_quality_score(schedule)

        # Convert to penalty (0-1, lower = better)
        penalty = (1.0 - quality_score) * self.weight

        logger.debug(
            f"Circadian penalty: quality={quality_score:.3f}, "
            f"penalty={penalty:.3f} (weight={self.weight})"
        )

        return penalty

    def evaluate_constraints(
        self,
        schedule: list[dict],
        quality_threshold: float = 0.55,  # FAIR level
    ) -> CircadianConstraintResult:
        """
        Evaluate circadian constraints on a schedule.

        Checks if schedule maintains acceptable circadian quality
        for all residents.

        Args:
            schedule: List of shift assignments
            quality_threshold: Minimum acceptable quality (default: FAIR = 0.55)

        Returns:
            CircadianConstraintResult with violations

        Example:
            >>> obj = CircadianObjective()
            >>> result = obj.evaluate_constraints(schedule)
            >>> if not result.satisfied:
            ...     print(f"Violations: {result.violations}")
        """
        # Group by resident
        shifts_by_resident: dict[UUID, list] = {}
        for shift in schedule:
            resident_id = shift.get("resident_id")
            if resident_id:
                if resident_id not in shifts_by_resident:
                    shifts_by_resident[resident_id] = []
                shifts_by_resident[resident_id].append(shift)

        # Analyze each resident
        violations = []
        at_risk_residents = []
        quality_scores = []

        for resident_id, resident_shifts in shifts_by_resident.items():
            impact = self.analyzer.analyze_schedule_impact(resident_id, resident_shifts)
            quality_scores.append(impact.quality_score)

            if impact.quality_score < quality_threshold:
                violations.append(
                    f"Resident {resident_id}: circadian quality {impact.quality_score:.2f} "
                    f"below threshold {quality_threshold:.2f} ({impact.quality_level.value})"
                )
                at_risk_residents.append(resident_id)

                logger.warning(
                    f"Circadian quality violation: resident={resident_id}, "
                    f"quality={impact.quality_score:.2f}, level={impact.quality_level}"
                )

        # Calculate overall metrics
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 1.0
        )
        satisfied = len(violations) == 0

        # Penalty for violations
        if satisfied:
            penalty = 0.0
        else:
            penalty = len(violations) * 10.0  # 10 penalty points per violation

        result = CircadianConstraintResult(
            satisfied=satisfied,
            penalty=penalty,
            violations=violations,
            quality_score=avg_quality,
            residents_at_risk=at_risk_residents,
        )

        logger.info(
            f"Circadian constraint evaluation: satisfied={satisfied}, "
            f"violations={len(violations)}, avg_quality={avg_quality:.3f}"
        )

        return result


# =============================================================================
# Schedule Analysis Helpers
# =============================================================================


class CircadianScheduleOptimizer:
    """
    Helper for optimizing schedules with circadian awareness.

    Provides pre-solver and post-solver analysis to ensure
    circadian health is maintained.
    """

    def __init__(self):
        """Initialize circadian schedule optimizer."""
        self.analyzer = CircadianScheduleAnalyzer()
        logger.info("Initialized CircadianScheduleOptimizer")

    def pre_solver_analysis(
        self,
        residents: list[UUID],
        historical_schedules: dict[UUID, list[dict]],
    ) -> dict[str, Any]:
        """
        Pre-solver analysis of circadian states.

        Analyzes residents' current circadian states from historical
        schedules to inform solver constraints.

        Args:
            residents: List of resident IDs to schedule
            historical_schedules: Past schedules by resident

        Returns:
            Analysis report with recommendations

        Example:
            >>> optimizer = CircadianScheduleOptimizer()
            >>> report = optimizer.pre_solver_analysis(residents, history)
            >>> # Use report to set solver constraints
        """
        analysis = {
            "analyzed_at": datetime.now().isoformat(),
            "total_residents": len(residents),
            "residents_at_risk": [],
            "recommendations": [],
        }

        for resident_id in residents:
            if resident_id in historical_schedules:
                # Analyze historical schedule
                impact = self.analyzer.analyze_schedule_impact(
                    resident_id, historical_schedules[resident_id]
                )

                # Identify at-risk residents
                if impact.quality_level in [
                    CircadianQualityLevel.POOR,
                    CircadianQualityLevel.CRITICAL,
                ]:
                    analysis["residents_at_risk"].append(
                        {
                            "resident_id": str(resident_id),
                            "quality_score": impact.quality_score,
                            "quality_level": impact.quality_level.value,
                            "phase_drift": impact.phase_drift,
                            "amplitude": self.analyzer.get_or_create_oscillator(
                                resident_id
                            ).amplitude,
                        }
                    )

                    # Add recommendation
                    if impact.quality_level == CircadianQualityLevel.CRITICAL:
                        analysis["recommendations"].append(
                            f"URGENT: Resident {resident_id} requires circadian recovery. "
                            f"Recommend {impact.recovery_days_needed} days of regular schedule."
                        )

        logger.info(
            f"Pre-solver circadian analysis: {len(analysis['residents_at_risk'])} "
            f"residents at risk, {len(analysis['recommendations'])} recommendations"
        )

        return analysis

    def post_solver_validation(
        self,
        schedule: list[dict],
        quality_threshold: float = 0.55,
    ) -> dict[str, Any]:
        """
        Post-solver validation of circadian quality.

        Validates that generated schedule meets circadian health standards.

        Args:
            schedule: Generated schedule to validate
            quality_threshold: Minimum acceptable quality

        Returns:
            Validation report

        Example:
            >>> optimizer = CircadianScheduleOptimizer()
            >>> report = optimizer.post_solver_validation(schedule)
            >>> if not report["passed"]:
            ...     print(f"Circadian validation failed: {report['issues']}")
        """
        objective = CircadianObjective()
        result = objective.evaluate_constraints(schedule, quality_threshold)

        report = {
            "passed": result.satisfied,
            "overall_quality": result.quality_score,
            "violations": result.violations,
            "residents_at_risk": [str(rid) for rid in result.residents_at_risk],
            "penalty": result.penalty,
            "validated_at": datetime.now().isoformat(),
        }

        # Add recommendations for failed validation
        if not result.satisfied:
            report["recommendations"] = self._generate_improvement_recommendations(
                result
            )

        logger.info(
            f"Post-solver validation: passed={report['passed']}, "
            f"quality={result.quality_score:.3f}"
        )

        return report

    def optimize_shift_timing(
        self,
        candidate_shifts: list[dict],
        resident_id: UUID,
    ) -> list[dict]:
        """
        Optimize shift timing for minimal circadian disruption.

        Given multiple candidate shift options, selects shifts that
        minimize circadian disruption for the resident.

        Args:
            candidate_shifts: Possible shift assignments
            resident_id: Resident being scheduled

        Returns:
            Shifts ranked by circadian quality (best first)

        Example:
            >>> optimizer = CircadianScheduleOptimizer()
            >>> candidates = [shift1, shift2, shift3]
            >>> ranked = optimizer.optimize_shift_timing(candidates, resident_id)
            >>> best_shift = ranked[0]  # Minimal circadian impact
        """
        if not candidate_shifts:
            return []

        # Score each candidate
        scored_shifts = []
        for shift in candidate_shifts:
            # Create mini-schedule with just this shift
            mini_schedule = [shift]
            impact = self.analyzer.analyze_schedule_impact(resident_id, mini_schedule)

            scored_shifts.append(
                {
                    "shift": shift,
                    "quality_score": impact.quality_score,
                    "phase_drift": impact.phase_drift,
                    "impact": impact,
                }
            )

        # Sort by quality (descending)
        scored_shifts.sort(key=lambda x: x["quality_score"], reverse=True)

        # Return ranked shifts
        ranked_shifts = [item["shift"] for item in scored_shifts]

        logger.debug(
            f"Ranked {len(ranked_shifts)} shifts by circadian quality for {resident_id}"
        )

        return ranked_shifts

    def _generate_improvement_recommendations(
        self, result: CircadianConstraintResult
    ) -> list[str]:
        """Generate recommendations to improve circadian quality."""
        recommendations = []

        if result.residents_at_risk:
            recommendations.append(
                f"{len(result.residents_at_risk)} residents have poor circadian quality. "
                "Consider:"
            )
            recommendations.append("- Reduce consecutive night shifts")
            recommendations.append(
                "- Add recovery days after circadian-disrupting shifts"
            )
            recommendations.append("- Prefer forward rotation (day→evening→night)")
            recommendations.append("- Avoid rapid shift type changes")

        if result.quality_score < 0.60:
            recommendations.append(
                "Overall schedule circadian quality is low. "
                "Try increasing CircadianObjective weight in solver."
            )

        return recommendations


# =============================================================================
# Utility Functions
# =============================================================================


def classify_shift_type(shift_start: datetime, duration: float) -> CircadianShiftType:
    """
    Classify shift type based on start time and duration.

    Args:
        shift_start: When shift begins
        duration: Shift length in hours

    Returns:
        CircadianShiftType classification

    Example:
        >>> shift_type = classify_shift_type(datetime(2024, 1, 1, 7, 0), 8.0)
        >>> print(shift_type)  # CircadianShiftType.DAY
    """
    hour = shift_start.hour

    if 6 <= hour < 15:
        if duration >= 12:
            return CircadianShiftType.LONG_DAY
        else:
            return CircadianShiftType.DAY
    elif 15 <= hour < 23:
        return CircadianShiftType.EVENING
    elif hour >= 23 or hour < 6:
        return CircadianShiftType.NIGHT
    else:
        return CircadianShiftType.SPLIT


def compute_schedule_regularity(schedule: list[dict]) -> float:
    """
    Compute schedule regularity score.

    Measures how consistent shift types and timing are.
    High regularity = better circadian entrainment.

    Args:
        schedule: List of shifts (chronologically ordered)

    Returns:
        Regularity score (0-1), 1.0 = perfectly regular

    Example:
        >>> regularity = compute_schedule_regularity(schedule)
        >>> print(regularity)  # 0.85
    """
    if len(schedule) <= 1:
        return 1.0

    # Check shift type consistency
    shift_types = [
        classify_shift_type(s["start_time"], s["duration"]) for s in schedule
    ]

    # Count transitions
    transitions = 0
    for i in range(1, len(shift_types)):
        if shift_types[i] != shift_types[i - 1]:
            transitions += 1

    # Regularity decreases with transitions
    max_transitions = len(shift_types) - 1
    regularity = 1.0 - (transitions / max_transitions) if max_transitions > 0 else 1.0

    return regularity


def get_circadian_recommendations(impact: CircadianImpact) -> list[str]:
    """
    Get actionable recommendations based on circadian impact.

    Args:
        impact: CircadianImpact from analysis

    Returns:
        List of recommendations

    Example:
        >>> recommendations = get_circadian_recommendations(impact)
        >>> for rec in recommendations:
        ...     print(rec)
    """
    recommendations = []

    # Phase drift recommendations
    if abs(impact.phase_drift) > 3:
        recommendations.append(
            f"⚠️ Significant phase drift ({impact.phase_drift:+.1f}h). "
            f"Recommend {impact.recovery_days_needed} days regular schedule for recovery."
        )

    # Amplitude recommendations
    if impact.amplitude_change < -0.2:
        recommendations.append(
            "⚠️ Circadian amplitude degradation detected. "
            "Reduce shift type variability and allow recovery periods."
        )

    # Quality level recommendations
    if impact.quality_level == CircadianQualityLevel.CRITICAL:
        recommendations.append(
            "🚨 CRITICAL: Immediate circadian intervention needed. "
            "Assign to regular day shifts for minimum 14 days."
        )
    elif impact.quality_level == CircadianQualityLevel.POOR:
        recommendations.append(
            "⚠️ Poor circadian quality. Avoid night shifts for next 7 days."
        )
    elif impact.quality_level == CircadianQualityLevel.FAIR:
        recommendations.append(
            "Monitor circadian health. Consider reducing shift variability."
        )

    # Misalignment recommendations
    if impact.misalignment_hours > 4:
        recommendations.append(
            f"High circadian misalignment ({impact.misalignment_hours:.1f}h avg). "
            "Prefer shifts aligned with resident's current circadian phase."
        )

    return recommendations
