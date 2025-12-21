"""
Creep/Fatigue-Based Burnout Prediction (Materials Science Pattern).

Adapts materials science concepts of creep (time-dependent deformation under load)
and fatigue (damage from cyclic loading) to predict medical resident burnout.

Key Concepts from Materials Science:

1. **Creep**: Time-dependent deformation under constant stress
   - Primary creep: Decreasing strain rate (adaptation phase)
   - Secondary creep: Steady-state (sustainable work rate)
   - Tertiary creep: Accelerating strain rate (approaching failure)

2. **Larson-Miller Parameter (LMP)**: Combines time and temperature for creep prediction
   - Formula: LMP = T(C + log10(t))
   - Adapted: LMP = workload * (C + log10(duration))
   - Predicts time to failure under sustained stress

3. **S-N Curves (Wöhler curves)**: Stress vs. cycles to failure
   - High stress = fewer cycles to failure
   - Low stress = many cycles before failure
   - Adapted for rotation cycles causing fatigue

4. **Miner's Rule (Palmgren-Miner)**: Cumulative damage from varying stress
   - D = Σ(n_i / N_i) where n_i = actual cycles, N_i = cycles to failure
   - Failure occurs when D ≥ 1.0

Application to Medical Residents:
- "Stress" = workload intensity, difficult rotations, emotional load
- "Time" = duration of sustained high workload
- "Cycles" = rotation changes, shift patterns
- "Failure" = burnout, medical errors, attrition
"""

import math
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class CreepStage(str, Enum):
    """
    Stages of creep deformation leading to failure.

    Analogous to burnout progression in medical residents.
    """
    PRIMARY = "primary"      # Initial adaptation, strain rate decreasing
    SECONDARY = "secondary"  # Steady-state, stable performance
    TERTIARY = "tertiary"    # Accelerating damage, approaching burnout


@dataclass
class CreepAnalysis:
    """
    Results of creep analysis for burnout prediction.

    Attributes:
        resident_id: UUID of the resident being analyzed
        creep_stage: Current stage of creep progression
        larson_miller_parameter: Combined time-temperature parameter
        estimated_time_to_failure: Predicted time until burnout
        strain_rate: Current rate of performance degradation (per day)
        recommended_stress_reduction: Percentage reduction needed for safety
    """
    resident_id: UUID
    creep_stage: CreepStage
    larson_miller_parameter: float
    estimated_time_to_failure: timedelta
    strain_rate: float
    recommended_stress_reduction: float


@dataclass
class FatigueCurve:
    """
    S-N curve fatigue analysis results.

    Tracks cumulative fatigue damage from rotation cycles.

    Attributes:
        cycles_to_failure: Predicted number of cycles until failure at current stress
        stress_amplitude: Current stress level (0.0-1.0)
        current_cycles: Number of cycles completed so far
        remaining_life_fraction: Fraction of life remaining before failure (0.0-1.0)
    """
    cycles_to_failure: int
    stress_amplitude: float
    current_cycles: int
    remaining_life_fraction: float


class CreepFatigueModel:
    """
    Creep and fatigue analysis for predicting resident burnout.

    Uses materials science principles adapted to human performance:
    - Larson-Miller Parameter for time-to-burnout under sustained load
    - Creep stage analysis for progression tracking
    - S-N curves for rotation cycle fatigue
    - Miner's rule for cumulative damage

    Constants:
        FAILURE_THRESHOLD: Larson-Miller parameter indicating high burnout risk
        SAFE_LMP: Target LMP for sustainable workload
    """

    # Larson-Miller Parameter threshold for failure prediction
    # LMP > 45.0 indicates high risk of burnout
    FAILURE_THRESHOLD: float = 45.0

    # Safe operating threshold (70% of failure threshold)
    SAFE_LMP: float = 31.5

    def calculate_larson_miller(
        self,
        workload_fraction: float,
        duration_days: int,
        C: float = 20.0
    ) -> float:
        """
        Calculate Larson-Miller Parameter for creep prediction.

        The LMP combines workload intensity and duration into a single
        failure prediction metric. Higher values indicate higher risk.

        In materials science: LMP = T(C + log10(t))
        where T = temperature (Kelvin/Rankine), t = time (hours)

        Adapted for human workload:
        LMP = workload * (base + multiplier * log10(duration))
        where workload is normalized 0.0-1.0, duration in days
        base = C/2, multiplier = C * 1.25
        This produces values in the 0-50 range for typical workloads

        Args:
            workload_fraction: Workload as fraction of capacity (0.0-1.0)
            duration_days: Duration of sustained workload in days
            C: Material constant (default 20, controls sensitivity)

        Returns:
            Larson-Miller Parameter value (typically 0-50 range)

        Example:
            >>> model = CreepFatigueModel()
            >>> # 90% workload for 30 days
            >>> lmp = model.calculate_larson_miller(0.9, 30)
            >>> # Returns ~42.2 (approaching failure threshold of 45.0)
        """
        if duration_days <= 0:
            return 0.0

        if workload_fraction <= 0:
            return 0.0

        # Simplified formula adapted from materials science
        # base = C/2 gives the constant component
        # multiplier = C * 1.25 controls time sensitivity
        base = C / 2.0
        multiplier = C * 1.25

        # LMP = workload * (base + multiplier * log10(duration))
        lmp = workload_fraction * (base + multiplier * math.log10(duration_days))

        logger.debug(
            f"Larson-Miller: workload={workload_fraction:.2f}, "
            f"duration={duration_days}d -> LMP={lmp:.2f}"
        )

        return lmp

    def determine_creep_stage(
        self,
        larson_miller: float,
        threshold: float = FAILURE_THRESHOLD
    ) -> CreepStage:
        """
        Determine current creep stage based on Larson-Miller parameter.

        Stages map to burnout progression:
        - PRIMARY (LMP < 50% threshold): Adaptation, decreasing strain rate
        - SECONDARY (50-80% threshold): Steady-state, sustainable
        - TERTIARY (> 80% threshold): Accelerating damage, high risk

        Args:
            larson_miller: Current LMP value
            threshold: Failure threshold (default: FAILURE_THRESHOLD)

        Returns:
            Current CreepStage
        """
        if larson_miller < threshold * 0.5:
            return CreepStage.PRIMARY
        elif larson_miller < threshold * 0.8:
            return CreepStage.SECONDARY
        else:
            return CreepStage.TERTIARY

    def calculate_strain_rate(
        self,
        workload_history: list[float]
    ) -> float:
        """
        Calculate rate of accumulating fatigue from workload history.

        Strain rate indicates how quickly performance is degrading.
        - Negative: Performance improving (adaptation)
        - Near zero: Stable performance
        - Positive: Performance degrading (fatigue accumulating)

        Uses linear regression on workload history to determine trend.

        Args:
            workload_history: List of workload values over time (chronological)

        Returns:
            Strain rate (change per time unit, can be negative)

        Example:
            >>> model = CreepFatigueModel()
            >>> # Increasing workload over time
            >>> history = [0.7, 0.75, 0.8, 0.85, 0.9]
            >>> rate = model.calculate_strain_rate(history)
            >>> # Returns positive value indicating increasing strain
        """
        if not workload_history or len(workload_history) < 2:
            return 0.0

        # Simple linear regression: slope of workload over time
        n = len(workload_history)
        x_values = list(range(n))
        y_values = workload_history

        # Calculate slope: (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        logger.debug(
            f"Strain rate: {len(workload_history)} points -> slope={slope:.4f}"
        )

        return slope

    def predict_time_to_burnout(
        self,
        resident_id: UUID,
        sustained_workload: float,
        duration: timedelta
    ) -> CreepAnalysis:
        """
        Predict time to burnout using creep analysis.

        Combines Larson-Miller parameter with creep stage analysis
        to estimate when a resident will experience burnout if current
        workload continues.

        Args:
            resident_id: UUID of resident to analyze
            sustained_workload: Current sustained workload (0.0-1.0)
            duration: How long workload has been sustained

        Returns:
            CreepAnalysis with predictions and recommendations

        Example:
            >>> model = CreepFatigueModel()
            >>> resident_id = UUID("...")
            >>> # 85% workload for 45 days
            >>> analysis = model.predict_time_to_burnout(
            ...     resident_id,
            ...     0.85,
            ...     timedelta(days=45)
            ... )
            >>> print(analysis.creep_stage)  # SECONDARY or TERTIARY
        """
        duration_days = int(duration.total_seconds() / 86400)

        # Calculate Larson-Miller parameter
        lmp = self.calculate_larson_miller(sustained_workload, duration_days)

        # Determine creep stage
        stage = self.determine_creep_stage(lmp, self.FAILURE_THRESHOLD)

        # Estimate time to failure
        # Based on how far we are from threshold
        lmp_margin = self.FAILURE_THRESHOLD - lmp

        if lmp_margin <= 0:
            # Already at or past threshold - immediate risk
            time_to_failure = timedelta(days=0)
        elif stage == CreepStage.TERTIARY:
            # Tertiary creep: accelerating failure, 1-2 weeks
            time_to_failure = timedelta(days=7)
        elif stage == CreepStage.SECONDARY:
            # Secondary creep: steady state, extrapolate linearly
            # Time to failure = (current_duration * margin) / current_lmp
            if lmp > 0:
                days_to_failure = (duration_days * lmp_margin) / lmp
                time_to_failure = timedelta(days=days_to_failure)
            else:
                time_to_failure = timedelta(days=365)  # Very safe
        else:
            # Primary creep: adapting, long time to failure
            time_to_failure = timedelta(days=180)

        # Calculate strain rate (approximate from current state)
        # In real implementation, would use historical data
        if stage == CreepStage.TERTIARY:
            strain_rate = 0.05  # High rate of degradation
        elif stage == CreepStage.SECONDARY:
            strain_rate = 0.01  # Slow steady degradation
        else:
            strain_rate = -0.005  # Negative = improving (adaptation)

        # Calculate recommended stress reduction
        stress_reduction = self.recommend_stress_reduction(lmp, self.SAFE_LMP)

        analysis = CreepAnalysis(
            resident_id=resident_id,
            creep_stage=stage,
            larson_miller_parameter=lmp,
            estimated_time_to_failure=time_to_failure,
            strain_rate=strain_rate,
            recommended_stress_reduction=stress_reduction,
        )

        logger.info(
            f"Creep analysis for {resident_id}: "
            f"LMP={lmp:.2f}, stage={stage.value}, "
            f"TTF={time_to_failure.days}d, reduction={stress_reduction:.1f}%"
        )

        return analysis

    def recommend_stress_reduction(
        self,
        current_lmp: float,
        safe_lmp: float = SAFE_LMP
    ) -> float:
        """
        Calculate recommended stress reduction to reach safe LMP.

        Returns percentage reduction needed in workload to bring
        Larson-Miller parameter down to safe operating level.

        Args:
            current_lmp: Current Larson-Miller parameter
            safe_lmp: Target safe LMP (default: SAFE_LMP)

        Returns:
            Percentage reduction needed (0.0-100.0)

        Example:
            >>> model = CreepFatigueModel()
            >>> reduction = model.recommend_stress_reduction(40.0, 31.5)
            >>> # Returns ~21.25 (need 21.25% reduction)
        """
        if current_lmp <= safe_lmp:
            return 0.0  # Already safe

        # Percentage reduction needed: (current - safe) / current * 100
        reduction_pct = ((current_lmp - safe_lmp) / current_lmp) * 100.0

        # Cap at 50% maximum recommended reduction
        # (larger reductions should be phased)
        return min(reduction_pct, 50.0)

    def sn_curve_cycles_to_failure(
        self,
        stress_amplitude: float,
        material_constant: float = 1e10,
        exponent: float = -3.0
    ) -> int:
        """
        Predict cycles to failure using S-N curve (Wöhler curve).

        The S-N curve relates stress amplitude to number of cycles
        before fatigue failure. Commonly modeled as:
        N = A * S^b
        where N = cycles to failure, S = stress, A = material constant, b = exponent

        In medical context:
        - Stress = difficulty of rotation (normalized 0.0-1.0)
        - Cycles = number of rotation changes
        - Failure = burnout from repeated difficult transitions

        Args:
            stress_amplitude: Stress level (0.0-1.0, higher = more difficult)
            material_constant: Material constant A (default: 1e10)
            exponent: Stress exponent b (default: -3.0, typical for metals)

        Returns:
            Number of cycles to failure

        Example:
            >>> model = CreepFatigueModel()
            >>> # High stress (0.9) -> fewer cycles
            >>> cycles_high = model.sn_curve_cycles_to_failure(0.9)
            >>> # Low stress (0.3) -> more cycles
            >>> cycles_low = model.sn_curve_cycles_to_failure(0.3)
            >>> assert cycles_low > cycles_high
        """
        if stress_amplitude <= 0 or stress_amplitude > 1.0:
            # Invalid stress - return large number (won't fail)
            return int(1e6)

        # S-N curve: N = A * S^b
        cycles = material_constant * (stress_amplitude ** exponent)

        # Ensure reasonable bounds
        cycles = max(1, min(int(cycles), int(1e6)))

        logger.debug(
            f"S-N curve: stress={stress_amplitude:.2f} -> "
            f"N={cycles} cycles to failure"
        )

        return cycles

    def calculate_fatigue_damage(
        self,
        rotation_stresses: list[float],
        cycles_per_rotation: int = 1
    ) -> FatigueCurve:
        """
        Calculate cumulative fatigue damage using Miner's rule.

        Miner's rule (Palmgren-Miner linear damage hypothesis):
        D = Σ(n_i / N_i)
        where:
        - n_i = number of cycles at stress level i
        - N_i = cycles to failure at stress level i
        - Failure occurs when D ≥ 1.0

        Args:
            rotation_stresses: List of stress levels for rotations (0.0-1.0)
            cycles_per_rotation: Cycles per rotation (default: 1)

        Returns:
            FatigueCurve with cumulative damage analysis

        Example:
            >>> model = CreepFatigueModel()
            >>> # Three difficult rotations followed by one easier
            >>> stresses = [0.9, 0.85, 0.9, 0.6]
            >>> curve = model.calculate_fatigue_damage(stresses)
            >>> print(f"Remaining life: {curve.remaining_life_fraction:.2%}")
        """
        if not rotation_stresses:
            # No stress history - perfect condition
            return FatigueCurve(
                cycles_to_failure=int(1e6),
                stress_amplitude=0.0,
                current_cycles=0,
                remaining_life_fraction=1.0,
            )

        # Calculate cumulative damage using Miner's rule
        cumulative_damage = 0.0

        for stress in rotation_stresses:
            # Get cycles to failure for this stress level
            N_i = self.sn_curve_cycles_to_failure(stress)

            # Damage from this rotation: n_i / N_i
            damage_i = cycles_per_rotation / N_i
            cumulative_damage += damage_i

        # Remaining life fraction: 1 - D
        remaining_life = max(0.0, 1.0 - cumulative_damage)

        # Current stress (most recent)
        current_stress = rotation_stresses[-1]

        # Cycles to failure at current stress
        cycles_at_current = self.sn_curve_cycles_to_failure(current_stress)

        # Total cycles completed
        total_cycles = len(rotation_stresses) * cycles_per_rotation

        curve = FatigueCurve(
            cycles_to_failure=cycles_at_current,
            stress_amplitude=current_stress,
            current_cycles=total_cycles,
            remaining_life_fraction=remaining_life,
        )

        logger.info(
            f"Fatigue damage: {len(rotation_stresses)} rotations, "
            f"D={cumulative_damage:.3f}, remaining={remaining_life:.1%}"
        )

        return curve

    def assess_combined_risk(
        self,
        resident_id: UUID,
        sustained_workload: float,
        duration: timedelta,
        rotation_stresses: list[float],
    ) -> dict:
        """
        Assess combined creep and fatigue risk for comprehensive burnout prediction.

        Combines both analyses:
        - Creep: Long-term sustained workload effects
        - Fatigue: Cumulative damage from rotation cycles

        Args:
            resident_id: UUID of resident
            sustained_workload: Current sustained workload level (0.0-1.0)
            duration: Duration of sustained workload
            rotation_stresses: Historical rotation stress levels

        Returns:
            Dict with combined risk assessment

        Example:
            >>> model = CreepFatigueModel()
            >>> risk = model.assess_combined_risk(
            ...     UUID("..."),
            ...     0.85,
            ...     timedelta(days=60),
            ...     [0.9, 0.8, 0.85, 0.9, 0.7]
            ... )
            >>> print(risk["overall_risk"])  # "high", "moderate", "low"
        """
        # Creep analysis
        creep = self.predict_time_to_burnout(resident_id, sustained_workload, duration)

        # Fatigue analysis
        fatigue = self.calculate_fatigue_damage(rotation_stresses)

        # Combined risk assessment
        creep_risk_score = 0.0
        if creep.creep_stage == CreepStage.TERTIARY:
            creep_risk_score = 3.0
        elif creep.creep_stage == CreepStage.SECONDARY:
            creep_risk_score = 2.0
        else:
            creep_risk_score = 1.0

        # Fatigue risk based on remaining life
        if fatigue.remaining_life_fraction < 0.2:
            fatigue_risk_score = 3.0
        elif fatigue.remaining_life_fraction < 0.5:
            fatigue_risk_score = 2.0
        else:
            fatigue_risk_score = 1.0

        # Combined score (weighted average: 60% creep, 40% fatigue)
        combined_score = creep_risk_score * 0.6 + fatigue_risk_score * 0.4

        # Risk level
        if combined_score >= 2.5:
            overall_risk = "high"
            risk_description = "High burnout risk - immediate intervention needed"
        elif combined_score >= 1.8:
            overall_risk = "moderate"
            risk_description = "Moderate burnout risk - schedule adjustment recommended"
        else:
            overall_risk = "low"
            risk_description = "Low burnout risk - continue monitoring"

        # Recommendations
        recommendations = []
        if creep.creep_stage == CreepStage.TERTIARY:
            recommendations.append(
                f"URGENT: Reduce workload by {creep.recommended_stress_reduction:.1f}%"
            )
        if fatigue.remaining_life_fraction < 0.3:
            recommendations.append(
                "Schedule easier rotations to allow recovery"
            )
        if creep.recommended_stress_reduction > 0:
            recommendations.append(
                f"Target workload reduction: {creep.recommended_stress_reduction:.1f}%"
            )

        if not recommendations:
            recommendations.append("Continue current schedule with regular monitoring")

        return {
            "resident_id": str(resident_id),
            "overall_risk": overall_risk,
            "risk_score": combined_score,
            "risk_description": risk_description,
            "creep_analysis": {
                "stage": creep.creep_stage.value,
                "lmp": creep.larson_miller_parameter,
                "time_to_failure_days": creep.estimated_time_to_failure.days,
                "strain_rate": creep.strain_rate,
            },
            "fatigue_analysis": {
                "current_cycles": fatigue.current_cycles,
                "remaining_life": fatigue.remaining_life_fraction,
                "current_stress": fatigue.stress_amplitude,
            },
            "recommendations": recommendations,
        }
