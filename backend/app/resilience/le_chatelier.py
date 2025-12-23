"""
Le Chatelier's Principle (Physical Chemistry Pattern).

When a system at equilibrium experiences a change in conditions, the system
shifts to partially counteract that change.

"If you stress a system, it responds to reduce the stress."

Key insight: The system will naturally try to compensate, but the compensation
is always PARTIAL. Le Chatelier tells us:
- You cannot fully counteract a stress with internal adjustments alone
- The new equilibrium will be different from the old one
- Accepting the new equilibrium is often better than fighting it

Applied Stress -> System Response -> Scheduling Analog:
- Decrease in reactant -> Equilibrium shifts to produce more -> Cross-training activation, deferred leave
- Increase in temperature -> Favors endothermic direction -> High-pressure: favor rest, buffers
- Increase in pressure -> Shifts to reduce volume -> Crowding: consolidate services

This module implements:
1. Stress quantification for scheduling systems
2. Equilibrium shift calculations
3. Compensation estimation with cost tracking
4. New equilibrium prediction
5. Sustainability analysis
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class StressType(str, Enum):
    """Types of system stress."""

    FACULTY_LOSS = "faculty_loss"  # Decrease in capacity
    DEMAND_SURGE = "demand_surge"  # Increase in requirements
    QUALITY_PRESSURE = "quality_pressure"  # Need for higher standards
    TIME_COMPRESSION = "time_compression"  # Same work in less time
    RESOURCE_SCARCITY = "resource_scarcity"  # Limited supporting resources
    EXTERNAL_PRESSURE = "external_pressure"  # Regulatory, administrative


class CompensationType(str, Enum):
    """Types of compensation responses."""

    OVERTIME = "overtime"  # Extra hours worked
    CROSS_COVERAGE = "cross_coverage"  # Faculty covering unfamiliar areas
    DEFERRED_LEAVE = "deferred_leave"  # Postponed time off
    SERVICE_REDUCTION = "service_reduction"  # Reduced scope
    EFFICIENCY_GAIN = "efficiency_gain"  # Working smarter (limited)
    BACKUP_ACTIVATION = "backup_activation"  # Emergency backup pools
    QUALITY_TRADE = "quality_trade"  # Accepting lower standards (dangerous)


class EquilibriumState(str, Enum):
    """State of system equilibrium."""

    STABLE = "stable"  # At sustainable equilibrium
    COMPENSATING = "compensating"  # Actively shifting to new equilibrium
    STRESSED = "stressed"  # New equilibrium found but strained
    UNSUSTAINABLE = "unsustainable"  # Cannot reach stable equilibrium
    CRITICAL = "critical"  # System failing to equilibrate


@dataclass
class SystemStress:
    """
    A stress applied to the scheduling system.

    Represents a change in conditions that the system must respond to.
    """

    id: UUID
    stress_type: StressType
    description: str
    applied_at: datetime

    # Quantification
    magnitude: float  # 0.0 - 1.0 (fraction of system affected)
    duration_days: int  # Expected duration
    is_acute: bool  # True = sudden, False = gradual
    is_reversible: bool  # Can the stress be removed?

    # Impact on capacity
    capacity_impact: float  # Negative = capacity reduction (e.g., -0.20 = 20% loss)
    demand_impact: float  # Positive = demand increase (e.g., 0.15 = 15% more)

    # Current status
    is_active: bool = True
    resolved_at: datetime | None = None


@dataclass
class CompensationResponse:
    """
    A compensation response to system stress.

    The system's attempt to counteract the stress and restore equilibrium.
    """

    id: UUID
    stress_id: UUID
    compensation_type: CompensationType
    description: str
    initiated_at: datetime

    # Quantification
    compensation_magnitude: float  # How much of the stress is counteracted (0.0 - 1.0)
    effectiveness: float  # 0.0 - 1.0, actual vs expected

    # Costs
    immediate_cost: float  # Direct cost (overtime pay, etc.)
    hidden_cost: float  # Indirect cost (burnout, quality)
    sustainability_days: int  # How long can this be maintained

    # Tracking
    is_active: bool = True
    ended_at: datetime | None = None
    end_reason: str | None = None


@dataclass
class EquilibriumShift:
    """
    Represents a shift from one equilibrium state to another.

    Le Chatelier's principle tells us the new equilibrium will be
    DIFFERENT from the old one, and compensation is always partial.
    """

    id: UUID
    calculated_at: datetime

    # Original state
    original_capacity: float
    original_demand: float
    original_coverage_rate: float

    # Applied stress
    stresses: list[SystemStress]
    total_capacity_impact: float
    total_demand_impact: float

    # Compensation
    compensations: list[CompensationResponse]
    total_compensation: float
    compensation_efficiency: float  # How much of the compensation actually helps

    # New equilibrium
    new_capacity: float
    new_demand: float
    new_coverage_rate: float
    sustainable_capacity: float  # What's sustainable long-term

    # Costs and sustainability
    compensation_debt: float  # Accumulated cost of compensating
    daily_debt_rate: float  # How fast debt accumulates
    burnout_risk: float  # 0.0 - 1.0
    days_until_exhaustion: int  # When compensation fails

    # State
    equilibrium_state: EquilibriumState
    is_sustainable: bool


@dataclass
class StressResponsePrediction:
    """
    Prediction of how the system will respond to a stress.

    Used for planning and decision-making before stress is applied.
    """

    id: UUID
    predicted_at: datetime

    # Input stress
    stress_type: StressType
    stress_magnitude: float
    stress_duration_days: int

    # Predicted response
    predicted_compensation: float  # Expected natural compensation (0-50%)
    predicted_new_capacity: float  # Capacity after equilibrium shift
    predicted_coverage_rate: float  # Coverage after shift

    # Costs
    predicted_daily_cost: float  # Per-day cost of compensation
    predicted_total_cost: float  # Total cost over duration
    predicted_burnout_increase: float  # How much burnout will increase

    # Recommendations
    additional_intervention_needed: float  # How much more help needed
    recommended_actions: list[str]
    sustainability_assessment: str


@dataclass
class EquilibriumReport:
    """Comprehensive equilibrium analysis report."""

    generated_at: datetime

    # Current state
    current_equilibrium_state: EquilibriumState
    current_capacity: float
    current_demand: float
    current_coverage_rate: float

    # Active stresses
    active_stresses: list[SystemStress]
    total_stress_magnitude: float

    # Active compensations
    active_compensations: list[CompensationResponse]
    total_compensation_magnitude: float

    # Equilibrium analysis
    latest_shift: EquilibriumShift | None
    compensation_debt: float
    sustainability_score: float  # 0.0 - 1.0

    # Predictions
    days_until_equilibrium: int  # -1 if stable
    days_until_exhaustion: int  # -1 if sustainable

    # Recommendations
    recommendations: list[str]


class LeChatelierAnalyzer:
    """
    Analyzes system equilibrium and stress response.

    Implements Le Chatelier's principle for scheduling systems:
    - Quantifies stresses and their impacts
    - Calculates compensation responses
    - Predicts new equilibrium states
    - Tracks compensation debt and sustainability
    """

    def __init__(
        self,
        base_compensation_rate: float = 0.5,  # 50% natural compensation
        compensation_cost_multiplier: float = 1.5,  # 50% surcharge for stress
        sustainability_threshold: float = 0.7,
    ):
        self.base_compensation_rate = base_compensation_rate
        self.compensation_cost_multiplier = compensation_cost_multiplier
        self.sustainability_threshold = sustainability_threshold

        self.stresses: dict[UUID, SystemStress] = {}
        self.compensations: dict[UUID, CompensationResponse] = {}
        self.shifts: list[EquilibriumShift] = []

        # Current system state
        self._current_capacity: float = 1.0
        self._current_demand: float = 0.8
        self._compensation_debt: float = 0.0

    def apply_stress(
        self,
        stress_type: StressType,
        description: str,
        magnitude: float,
        duration_days: int,
        capacity_impact: float,
        demand_impact: float = 0.0,
        is_acute: bool = True,
        is_reversible: bool = True,
    ) -> SystemStress:
        """
        Apply a stress to the system.

        Args:
            stress_type: Type of stress
            description: What's happening
            magnitude: 0.0 - 1.0 (fraction of system affected)
            duration_days: Expected duration
            capacity_impact: Negative = capacity reduction
            demand_impact: Positive = demand increase
            is_acute: Sudden vs gradual
            is_reversible: Can it be removed?

        Returns:
            Created SystemStress
        """
        stress = SystemStress(
            id=uuid4(),
            stress_type=stress_type,
            description=description,
            applied_at=datetime.now(),
            magnitude=magnitude,
            duration_days=duration_days,
            is_acute=is_acute,
            is_reversible=is_reversible,
            capacity_impact=capacity_impact,
            demand_impact=demand_impact,
        )

        self.stresses[stress.id] = stress

        # Apply impact to current state
        self._current_capacity = max(0.1, self._current_capacity + capacity_impact)
        self._current_demand = max(0.1, self._current_demand * (1 + demand_impact))

        logger.warning(
            f"Stress applied: {stress_type.value} - "
            f"capacity impact: {capacity_impact:+.0%}, "
            f"demand impact: {demand_impact:+.0%}"
        )

        return stress

    def initiate_compensation(
        self,
        stress_id: UUID,
        compensation_type: CompensationType,
        description: str,
        magnitude: float,
        effectiveness: float = 0.8,
        sustainability_days: int = 30,
        immediate_cost: float = 0.0,
        hidden_cost: float = 0.0,
    ) -> CompensationResponse | None:
        """
        Initiate a compensation response to stress.

        Args:
            stress_id: Stress being compensated
            compensation_type: Type of compensation
            description: What's being done
            magnitude: How much compensation (0.0 - 1.0)
            effectiveness: Expected effectiveness
            sustainability_days: How long can this be maintained
            immediate_cost: Direct costs
            hidden_cost: Indirect costs (burnout, etc.)

        Returns:
            Created CompensationResponse
        """
        stress = self.stresses.get(stress_id)
        if not stress:
            return None

        compensation = CompensationResponse(
            id=uuid4(),
            stress_id=stress_id,
            compensation_type=compensation_type,
            description=description,
            initiated_at=datetime.now(),
            compensation_magnitude=magnitude,
            effectiveness=effectiveness,
            sustainability_days=sustainability_days,
            immediate_cost=immediate_cost,
            hidden_cost=hidden_cost,
        )

        self.compensations[compensation.id] = compensation

        # Apply compensation effect (partial, per Le Chatelier)
        effective_compensation = magnitude * effectiveness * self.base_compensation_rate
        self._current_capacity += abs(stress.capacity_impact) * effective_compensation

        # Add to debt
        self._compensation_debt += hidden_cost

        logger.info(
            f"Compensation initiated: {compensation_type.value} - "
            f"magnitude: {magnitude:.0%}, effective: {effective_compensation:.0%}"
        )

        return compensation

    def calculate_equilibrium_shift(
        self,
        original_capacity: float,
        original_demand: float,
    ) -> EquilibriumShift:
        """
        Calculate the shift from original equilibrium to current state.

        Le Chatelier's principle: the new equilibrium will be different
        from the old one, and compensation is always partial.

        Args:
            original_capacity: Capacity before stress
            original_demand: Demand before stress

        Returns:
            EquilibriumShift analysis
        """
        active_stresses = [s for s in self.stresses.values() if s.is_active]
        active_compensations = [c for c in self.compensations.values() if c.is_active]

        # Calculate total impacts
        total_capacity_impact = sum(s.capacity_impact for s in active_stresses)
        total_demand_impact = sum(s.demand_impact for s in active_stresses)

        # Calculate total compensation
        total_compensation = sum(
            c.compensation_magnitude * c.effectiveness * self.base_compensation_rate
            for c in active_compensations
        )

        # Calculate compensation efficiency (diminishing returns)
        if len(active_compensations) > 1:
            # Multiple compensations interfere with each other
            compensation_efficiency = 1.0 / (
                1.0 + 0.1 * (len(active_compensations) - 1)
            )
        else:
            compensation_efficiency = 1.0

        total_compensation *= compensation_efficiency

        # Calculate new equilibrium values
        raw_new_capacity = original_capacity + total_capacity_impact
        compensation_recovery = abs(total_capacity_impact) * total_compensation
        new_capacity = raw_new_capacity + compensation_recovery

        new_demand = original_demand * (1 + total_demand_impact)

        # Coverage rates
        original_coverage = min(1.0, original_capacity / original_demand)
        new_coverage = min(1.0, new_capacity / new_demand)

        # Sustainable capacity (without compensation)
        sustainable_capacity = raw_new_capacity

        # Calculate costs
        total_hidden_cost = sum(c.hidden_cost for c in active_compensations)
        compensation_debt = self._compensation_debt + total_hidden_cost

        # Daily debt rate
        daily_debt_rate = total_hidden_cost / max(
            1,
            sum(c.sustainability_days for c in active_compensations)
            / len(active_compensations)
            if active_compensations
            else 1,
        )

        # Burnout risk
        if total_compensation > 0:
            burnout_risk = min(1.0, compensation_debt / 100 + total_compensation * 0.3)
        else:
            burnout_risk = 0.0

        # Days until exhaustion
        if active_compensations:
            min_sustainability = min(
                c.sustainability_days for c in active_compensations
            )
            elapsed = max(
                (datetime.now() - c.initiated_at).days for c in active_compensations
            )
            days_until_exhaustion = max(0, min_sustainability - elapsed)
        else:
            days_until_exhaustion = -1  # No limit

        # Determine equilibrium state
        if new_coverage >= 0.9 and burnout_risk < 0.3:
            equilibrium_state = EquilibriumState.STABLE
        elif new_coverage >= 0.8 and burnout_risk < 0.5:
            equilibrium_state = EquilibriumState.COMPENSATING
        elif new_coverage >= 0.7:
            equilibrium_state = EquilibriumState.STRESSED
        elif new_coverage >= 0.5:
            equilibrium_state = EquilibriumState.UNSUSTAINABLE
        else:
            equilibrium_state = EquilibriumState.CRITICAL

        is_sustainable = (
            new_coverage >= self.sustainability_threshold
            and burnout_risk < 0.5
            and days_until_exhaustion < 0
            or days_until_exhaustion > 30
        )

        shift = EquilibriumShift(
            id=uuid4(),
            calculated_at=datetime.now(),
            original_capacity=original_capacity,
            original_demand=original_demand,
            original_coverage_rate=original_coverage,
            stresses=active_stresses,
            total_capacity_impact=total_capacity_impact,
            total_demand_impact=total_demand_impact,
            compensations=active_compensations,
            total_compensation=total_compensation,
            compensation_efficiency=compensation_efficiency,
            new_capacity=new_capacity,
            new_demand=new_demand,
            new_coverage_rate=new_coverage,
            sustainable_capacity=sustainable_capacity,
            compensation_debt=compensation_debt,
            daily_debt_rate=daily_debt_rate,
            burnout_risk=burnout_risk,
            days_until_exhaustion=days_until_exhaustion,
            equilibrium_state=equilibrium_state,
            is_sustainable=is_sustainable,
        )

        self.shifts.append(shift)

        logger.info(
            f"Equilibrium shift calculated: "
            f"coverage {original_coverage:.0%} -> {new_coverage:.0%}, "
            f"state: {equilibrium_state.value}"
        )

        return shift

    def predict_stress_response(
        self,
        stress_type: StressType,
        magnitude: float,
        duration_days: int,
        capacity_impact: float,
        demand_impact: float = 0.0,
    ) -> StressResponsePrediction:
        """
        Predict how the system will respond to a potential stress.

        Use this for planning before actually applying stress.

        Args:
            stress_type: Type of stress
            magnitude: Fraction of system affected
            duration_days: Expected duration
            capacity_impact: Capacity reduction
            demand_impact: Demand increase

        Returns:
            StressResponsePrediction
        """
        # Current state
        current_capacity = self._current_capacity
        current_demand = self._current_demand

        # Calculate natural compensation (Le Chatelier)
        natural_compensation = abs(capacity_impact) * self.base_compensation_rate

        # Predicted new state
        predicted_new_capacity = (
            current_capacity + capacity_impact + natural_compensation
        )
        predicted_new_demand = current_demand * (1 + demand_impact)
        predicted_coverage = min(1.0, predicted_new_capacity / predicted_new_demand)

        # Calculate costs
        daily_cost = (
            abs(capacity_impact) * self.compensation_cost_multiplier * 100
        )  # Arbitrary units
        total_cost = daily_cost * duration_days
        burnout_increase = magnitude * 0.2  # 20% of magnitude converts to burnout

        # Calculate intervention needed
        target_coverage = 0.9
        if predicted_coverage < target_coverage:
            coverage_gap = target_coverage - predicted_coverage
            additional_intervention = coverage_gap / target_coverage
        else:
            additional_intervention = 0.0

        # Build recommendations
        recommendations = []

        if predicted_coverage < 0.7:
            recommendations.append("CRITICAL: Predicted coverage below safe threshold")
            recommendations.append(
                "Activate fallback schedule before stress materializes"
            )
            recommendations.append("Consider load shedding to reduce demand")

        elif predicted_coverage < 0.85:
            recommendations.append("Coverage will be tight - prepare backup coverage")
            recommendations.append(
                "Defer non-essential activities during stress period"
            )

        if burnout_increase > 0.3:
            recommendations.append("High burnout risk - protect high-load faculty")
            recommendations.append("Plan recovery time after stress period")

        if duration_days > 30:
            recommendations.append(
                "Extended stress period - consider permanent adjustments"
            )
            recommendations.append("Compensation debt will accumulate significantly")

        if additional_intervention > 0.1:
            recommendations.append(
                f"Additional {additional_intervention:.0%} intervention needed"
            )
            recommendations.append("Consider external support or service reduction")

        # Sustainability assessment
        if predicted_coverage >= 0.9 and burnout_increase < 0.2:
            sustainability = "System can absorb this stress sustainably"
        elif predicted_coverage >= 0.8 and burnout_increase < 0.4:
            sustainability = "Manageable with active monitoring"
        elif predicted_coverage >= 0.7:
            sustainability = "Risky - intervention recommended"
        else:
            sustainability = "UNSUSTAINABLE - significant intervention required"

        return StressResponsePrediction(
            id=uuid4(),
            predicted_at=datetime.now(),
            stress_type=stress_type,
            stress_magnitude=magnitude,
            stress_duration_days=duration_days,
            predicted_compensation=natural_compensation,
            predicted_new_capacity=predicted_new_capacity,
            predicted_coverage_rate=predicted_coverage,
            predicted_daily_cost=daily_cost,
            predicted_total_cost=total_cost,
            predicted_burnout_increase=burnout_increase,
            additional_intervention_needed=additional_intervention,
            recommended_actions=recommendations,
            sustainability_assessment=sustainability,
        )

    def calculate_new_equilibrium(
        self,
        original_capacity: float,
        stress_reduction: float,
    ) -> dict:
        """
        Calculate new equilibrium using Le Chatelier's formula.

        This is the simplified calculation from the documentation:
        - System partially compensates (50% by default)
        - Compensation has costs (50% surcharge)
        - New equilibrium different from old

        Args:
            original_capacity: Capacity before stress
            stress_reduction: How much capacity is lost

        Returns:
            Dict with capacity, sustainable_capacity, and compensation_debt
        """
        raw_new_capacity = original_capacity - stress_reduction
        compensation = stress_reduction * self.base_compensation_rate
        effective_capacity = raw_new_capacity + compensation

        # But compensation has costs
        compensation_cost = compensation * self.compensation_cost_multiplier

        return {
            "capacity": effective_capacity,
            "sustainable_capacity": raw_new_capacity,  # What's sustainable long-term
            "compensation_debt": compensation_cost,
            "compensation_ratio": compensation / stress_reduction
            if stress_reduction > 0
            else 0,
        }

    def resolve_stress(
        self,
        stress_id: UUID,
        resolution_notes: str = "",
    ):
        """Mark a stress as resolved."""
        stress = self.stresses.get(stress_id)
        if stress:
            stress.is_active = False
            stress.resolved_at = datetime.now()

            # Restore capacity
            self._current_capacity = min(
                1.0, self._current_capacity - stress.capacity_impact
            )

            # End related compensations
            for comp in self.compensations.values():
                if comp.stress_id == stress_id and comp.is_active:
                    comp.is_active = False
                    comp.ended_at = datetime.now()
                    comp.end_reason = "stress_resolved"

            logger.info(f"Stress resolved: {stress.stress_type.value}")

    def end_compensation(
        self,
        compensation_id: UUID,
        reason: str,
    ):
        """End a compensation response."""
        comp = self.compensations.get(compensation_id)
        if comp:
            comp.is_active = False
            comp.ended_at = datetime.now()
            comp.end_reason = reason
            logger.info(
                f"Compensation ended: {comp.compensation_type.value} - {reason}"
            )

    def get_report(self) -> EquilibriumReport:
        """Generate comprehensive equilibrium report."""
        active_stresses = [s for s in self.stresses.values() if s.is_active]
        active_compensations = [c for c in self.compensations.values() if c.is_active]

        # Calculate totals
        total_stress = sum(abs(s.capacity_impact) for s in active_stresses)
        total_compensation = sum(c.compensation_magnitude for c in active_compensations)

        # Current coverage
        current_coverage = min(1.0, self._current_capacity / self._current_demand)

        # Determine current state
        if current_coverage >= 0.9 and self._compensation_debt < 50:
            current_state = EquilibriumState.STABLE
        elif current_coverage >= 0.8:
            current_state = EquilibriumState.COMPENSATING
        elif current_coverage >= 0.7:
            current_state = EquilibriumState.STRESSED
        elif current_coverage >= 0.5:
            current_state = EquilibriumState.UNSUSTAINABLE
        else:
            current_state = EquilibriumState.CRITICAL

        # Get latest shift
        latest_shift = self.shifts[-1] if self.shifts else None

        # Calculate sustainability
        if active_compensations:
            min_sustainability = min(
                c.sustainability_days for c in active_compensations
            )
            max_elapsed = max(
                (datetime.now() - c.initiated_at).days for c in active_compensations
            )
            days_until_exhaustion = max(0, min_sustainability - max_elapsed)
        else:
            days_until_exhaustion = -1

        # Sustainability score
        if current_state == EquilibriumState.STABLE:
            sustainability_score = 1.0
        elif current_state == EquilibriumState.COMPENSATING:
            sustainability_score = 0.8
        elif current_state == EquilibriumState.STRESSED:
            sustainability_score = 0.5
        else:
            sustainability_score = 0.2

        # Build recommendations
        recommendations = []

        if current_state == EquilibriumState.CRITICAL:
            recommendations.append(
                "CRITICAL: System cannot reach equilibrium - immediate intervention required"
            )

        if current_state == EquilibriumState.UNSUSTAINABLE:
            recommendations.append(
                "System equilibrium unsustainable - reduce demand or increase capacity"
            )

        if self._compensation_debt > 75:
            recommendations.append(
                f"High compensation debt ({self._compensation_debt:.0f}) - schedule recovery"
            )

        if days_until_exhaustion >= 0 and days_until_exhaustion < 14:
            recommendations.append(
                f"Compensation exhaustion in {days_until_exhaustion} days - plan transition"
            )

        if total_stress > 0 and total_compensation < total_stress * 0.3:
            recommendations.append(
                "Compensation insufficient - consider additional measures"
            )

        if not recommendations:
            recommendations.append("System at stable equilibrium - continue monitoring")

        return EquilibriumReport(
            generated_at=datetime.now(),
            current_equilibrium_state=current_state,
            current_capacity=self._current_capacity,
            current_demand=self._current_demand,
            current_coverage_rate=current_coverage,
            active_stresses=active_stresses,
            total_stress_magnitude=total_stress,
            active_compensations=active_compensations,
            total_compensation_magnitude=total_compensation,
            latest_shift=latest_shift,
            compensation_debt=self._compensation_debt,
            sustainability_score=sustainability_score,
            days_until_equilibrium=-1
            if current_state == EquilibriumState.STABLE
            else 7,
            days_until_exhaustion=days_until_exhaustion,
            recommendations=recommendations,
        )

    def set_current_state(self, capacity: float, demand: float):
        """Set current system state for calculations."""
        self._current_capacity = capacity
        self._current_demand = demand

    def reset_compensation_debt(self):
        """Reset compensation debt (after recovery period)."""
        self._compensation_debt = 0.0
        logger.info("Compensation debt reset after recovery")
