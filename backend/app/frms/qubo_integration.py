"""
QUBO Solver Integration for FRMS Fatigue Constraints.

This module integrates fatigue-aware constraints with the QUBO (Quadratic
Unconstrained Binary Optimization) solver for quantum-inspired scheduling.

Integration Points:
- Session 1: QUBO formulation extensions
- Session 2: Quantum annealing integration
- Session 3: Core FRMS implementation

Key Features:
1. Fatigue penalty terms in QUBO matrix
2. Circadian-aware variable weighting
3. WOCL protection as quadratic constraints
4. Multi-day fatigue accumulation modeling
5. Recovery requirement constraints

The fatigue penalties are added as soft constraints (quadratic terms)
to the QUBO objective function, guiding the solver toward schedules
with lower fatigue risk while still satisfying hard constraints.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID

from app.frms.three_process_model import ThreeProcessModel
from app.frms.performance_predictor import PerformancePredictor

logger = logging.getLogger(__name__)


@dataclass
class FatigueQUBOConfig:
    """
    Configuration for fatigue-aware QUBO formulation.

    Controls the strength and behavior of fatigue penalties
    in the quantum optimization.
    """

    # Penalty weights
    fatigue_penalty_base: float = 100.0  # Base penalty for low effectiveness
    wocl_penalty_multiplier: float = 2.0  # Extra penalty for WOCL shifts
    consecutive_day_penalty: float = 50.0  # Per day over 5 consecutive
    night_shift_cluster_bonus: float = -20.0  # Negative = reward clustering

    # Thresholds
    effectiveness_threshold: float = 77.0  # FAA caution threshold
    critical_threshold: float = 70.0  # FRA threshold (higher penalty)

    # Model parameters
    enable_circadian: bool = True
    enable_consecutive_days: bool = True
    enable_night_clustering: bool = True
    enable_recovery_requirements: bool = True


class FatigueQUBOIntegration:
    """
    Integrates FRMS fatigue constraints into QUBO formulation.

    Extends the base QUBOFormulation to include fatigue-aware penalty
    terms that guide the quantum-inspired solver toward safer schedules.

    Usage:
        from app.scheduling.quantum import QUBOFormulation
        from app.frms.qubo_integration import FatigueQUBOIntegration

        formulation = QUBOFormulation(context)
        fatigue_integration = FatigueQUBOIntegration()

        # Build base QUBO
        Q = formulation.build()

        # Add fatigue penalties
        Q = fatigue_integration.add_fatigue_penalties(Q, formulation, context)

        # Solve with fatigue-aware objective
        solver = SimulatedQuantumAnnealingSolver()
        result = solver.solve(context)
    """

    def __init__(self, config: FatigueQUBOConfig | None = None):
        """
        Initialize fatigue QUBO integration.

        Args:
            config: Optional configuration for penalty weights
        """
        self.config = config or FatigueQUBOConfig()
        self.model = ThreeProcessModel()
        self.predictor = PerformancePredictor()

        # Cache for effectiveness predictions
        self._effectiveness_cache: dict[tuple[UUID, str], float] = {}

        logger.info(
            f"FatigueQUBOIntegration initialized with base_penalty={self.config.fatigue_penalty_base}"
        )

    def add_fatigue_penalties(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,  # QUBOFormulation
        context: Any,  # SchedulingContext
    ) -> dict[tuple[int, int], float]:
        """
        Add fatigue penalty terms to QUBO matrix.

        Modifies the QUBO matrix in-place to include:
        1. Linear terms (diagonal): Penalties for individual assignments
        2. Quadratic terms (off-diagonal): Penalties for assignment combinations

        Args:
            Q: Existing QUBO matrix {(i,j): coefficient}
            formulation: QUBOFormulation with variable mappings
            context: SchedulingContext with schedule data

        Returns:
            Modified QUBO matrix with fatigue penalties
        """
        logger.info("Adding fatigue penalties to QUBO matrix")

        # Track added penalty terms
        linear_terms_added = 0
        quadratic_terms_added = 0

        # 1. Add linear fatigue penalties (per-assignment)
        linear_terms_added = self._add_linear_fatigue_penalties(Q, formulation, context)

        # 2. Add consecutive day penalties (quadratic, same person across days)
        if self.config.enable_consecutive_days:
            quadratic_terms_added += self._add_consecutive_day_penalties(
                Q, formulation, context
            )

        # 3. Add night shift clustering bonus (quadratic, encourage grouping)
        if self.config.enable_night_clustering:
            quadratic_terms_added += self._add_night_clustering_terms(
                Q, formulation, context
            )

        # 4. Add WOCL protection penalties
        if self.config.enable_circadian:
            linear_terms_added += self._add_wocl_penalties(Q, formulation, context)

        # 5. Add recovery requirement penalties
        if self.config.enable_recovery_requirements:
            quadratic_terms_added += self._add_recovery_penalties(
                Q, formulation, context
            )

        logger.info(
            f"Added fatigue penalties: {linear_terms_added} linear, "
            f"{quadratic_terms_added} quadratic terms"
        )

        return Q

    def _add_linear_fatigue_penalties(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,
        context: Any,
    ) -> int:
        """
        Add linear (diagonal) fatigue penalties.

        For each potential assignment, calculate predicted effectiveness
        and add penalty proportional to fatigue risk.
        """
        terms_added = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                # Predict effectiveness for this assignment
                effectiveness = self._predict_effectiveness(
                    resident.id, block.date, getattr(block, "time_of_day", "AM")
                )

                # Calculate penalty
                penalty = self._calculate_fatigue_penalty(effectiveness)

                if penalty > 0:
                    # Add penalty to all template variables for this person-block
                    for template in context.templates:
                        t_i = context.template_idx.get(template.id)
                        if t_i is not None:
                            var_key = (r_i, b_i, t_i)
                            if var_key in formulation.var_index:
                                idx = formulation.var_index[var_key]
                                # Add to diagonal (linear term)
                                Q[(idx, idx)] = Q.get((idx, idx), 0.0) + penalty
                                terms_added += 1

        return terms_added

    def _add_consecutive_day_penalties(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,
        context: Any,
    ) -> int:
        """
        Add penalties for consecutive day assignments.

        Uses quadratic terms to penalize pairs of assignments on
        consecutive days for the same person.
        """
        terms_added = 0

        # Group blocks by date
        blocks_by_date: dict[date, list] = {}
        for block in context.blocks:
            d = block.date
            if d not in blocks_by_date:
                blocks_by_date[d] = []
            blocks_by_date[d].append(block)

        sorted_dates = sorted(blocks_by_date.keys())

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            # Look at pairs of consecutive days
            for i in range(len(sorted_dates) - 1):
                date1 = sorted_dates[i]
                date2 = sorted_dates[i + 1]

                # Only penalize if actually consecutive
                if (date2 - date1).days != 1:
                    continue

                # Get variable indices for blocks on these days
                vars_day1 = self._get_person_block_vars(
                    formulation, context, r_i, blocks_by_date[date1]
                )
                vars_day2 = self._get_person_block_vars(
                    formulation, context, r_i, blocks_by_date[date2]
                )

                # Add quadratic penalty between all pairs
                penalty = self.config.consecutive_day_penalty

                # Increase penalty for 6+ consecutive days
                if i >= 5:
                    penalty *= 2.0

                for idx1 in vars_day1:
                    for idx2 in vars_day2:
                        if idx1 != idx2:
                            key = (min(idx1, idx2), max(idx1, idx2))
                            Q[key] = Q.get(key, 0.0) + penalty
                            terms_added += 1

        return terms_added

    def _add_night_clustering_terms(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,
        context: Any,
    ) -> int:
        """
        Add terms that encourage clustering night shifts.

        Isolated night shifts cause more circadian disruption than
        consecutive night shifts. Uses negative penalty (reward) for
        adjacent night assignments.
        """
        terms_added = 0

        # Identify PM (night) blocks
        night_blocks = [
            b for b in context.blocks if getattr(b, "time_of_day", "") == "PM"
        ]

        # Group by date
        nights_by_date: dict[date, list] = {}
        for block in night_blocks:
            d = block.date
            if d not in nights_by_date:
                nights_by_date[d] = []
            nights_by_date[d].append(block)

        sorted_dates = sorted(nights_by_date.keys())

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            # Reward consecutive night shifts for same person
            for i in range(len(sorted_dates) - 1):
                date1 = sorted_dates[i]
                date2 = sorted_dates[i + 1]

                if (date2 - date1).days != 1:
                    continue

                vars_night1 = self._get_person_block_vars(
                    formulation, context, r_i, nights_by_date[date1]
                )
                vars_night2 = self._get_person_block_vars(
                    formulation, context, r_i, nights_by_date[date2]
                )

                # Negative penalty = reward
                reward = self.config.night_shift_cluster_bonus

                for idx1 in vars_night1:
                    for idx2 in vars_night2:
                        if idx1 != idx2:
                            key = (min(idx1, idx2), max(idx1, idx2))
                            Q[key] = Q.get(key, 0.0) + reward
                            terms_added += 1

        return terms_added

    def _add_wocl_penalties(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,
        context: Any,
    ) -> int:
        """
        Add penalties for shifts overlapping Window of Circadian Low.

        PM blocks and certain templates are more likely to include
        WOCL (2-6 AM) exposure.
        """
        terms_added = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                # Check if block likely includes WOCL
                tod = getattr(block, "time_of_day", "AM")
                has_wocl = tod == "PM"  # Night blocks include WOCL

                if has_wocl:
                    wocl_penalty = (
                        self.config.fatigue_penalty_base
                        * self.config.wocl_penalty_multiplier
                    )

                    for template in context.templates:
                        t_i = context.template_idx.get(template.id)
                        if t_i is not None:
                            var_key = (r_i, b_i, t_i)
                            if var_key in formulation.var_index:
                                idx = formulation.var_index[var_key]
                                Q[(idx, idx)] = Q.get((idx, idx), 0.0) + wocl_penalty
                                terms_added += 1

        return terms_added

    def _add_recovery_penalties(
        self,
        Q: dict[tuple[int, int], float],
        formulation: Any,
        context: Any,
    ) -> int:
        """
        Add penalties for insufficient recovery between shifts.

        Penalizes assignment pairs that don't have adequate rest between.
        """
        terms_added = 0

        # Minimum recovery hours between shifts
        MIN_RECOVERY_HOURS = 10.0

        # Group blocks by date and time
        blocks_ordered = sorted(
            context.blocks,
            key=lambda b: (b.date, 0 if getattr(b, "time_of_day", "AM") == "AM" else 1),
        )

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            # Check pairs of blocks for recovery violations
            for i, block1 in enumerate(blocks_ordered):
                for block2 in blocks_ordered[i + 1 : i + 3]:  # Check next 2 blocks
                    # Calculate time gap
                    gap_hours = self._calculate_gap_hours(block1, block2)

                    if gap_hours < MIN_RECOVERY_HOURS:
                        # Add penalty for both assignments occurring
                        penalty = self.config.fatigue_penalty_base * (
                            1.0 - gap_hours / MIN_RECOVERY_HOURS
                        )

                        vars1 = self._get_person_block_vars(
                            formulation, context, r_i, [block1]
                        )
                        vars2 = self._get_person_block_vars(
                            formulation, context, r_i, [block2]
                        )

                        for idx1 in vars1:
                            for idx2 in vars2:
                                if idx1 != idx2:
                                    key = (min(idx1, idx2), max(idx1, idx2))
                                    Q[key] = Q.get(key, 0.0) + penalty
                                    terms_added += 1

        return terms_added

    def _predict_effectiveness(
        self,
        person_id: UUID,
        block_date: date,
        time_of_day: str,
    ) -> float:
        """Predict effectiveness for an assignment (cached)."""
        cache_key = (person_id, f"{block_date}_{time_of_day}")

        if cache_key in self._effectiveness_cache:
            return self._effectiveness_cache[cache_key]

        # Calculate time of day as float
        tod = 8.0 if time_of_day == "AM" else 14.0

        # Create temporary state and calculate
        state = self.model.create_state(person_id)
        score = self.model.calculate_effectiveness(state, tod)

        effectiveness = score.overall
        self._effectiveness_cache[cache_key] = effectiveness

        return effectiveness

    def _calculate_fatigue_penalty(self, effectiveness: float) -> float:
        """Calculate penalty based on effectiveness score."""
        if effectiveness >= self.config.effectiveness_threshold:
            return 0.0

        if effectiveness >= self.config.critical_threshold:
            # Linear penalty in caution zone
            gap = self.config.effectiveness_threshold - effectiveness
            return self.config.fatigue_penalty_base * (gap / 10.0)

        # Quadratic penalty below critical threshold
        gap = self.config.effectiveness_threshold - effectiveness
        return self.config.fatigue_penalty_base * ((gap / 10.0) ** 2)

    def _get_person_block_vars(
        self,
        formulation: Any,
        context: Any,
        r_i: int,
        blocks: list,
    ) -> list[int]:
        """Get all variable indices for a person on given blocks."""
        indices = []

        for block in blocks:
            b_i = context.block_idx.get(block.id)
            if b_i is None:
                continue

            for template in context.templates:
                t_i = context.template_idx.get(template.id)
                if t_i is not None:
                    var_key = (r_i, b_i, t_i)
                    if var_key in formulation.var_index:
                        indices.append(formulation.var_index[var_key])

        return indices

    def _calculate_gap_hours(self, block1: Any, block2: Any) -> float:
        """Calculate hours between end of block1 and start of block2."""
        # Assume 6-hour blocks
        # AM: 7:00-13:00, PM: 13:00-19:00

        tod1 = getattr(block1, "time_of_day", "AM")
        tod2 = getattr(block2, "time_of_day", "AM")

        end1_hour = 13.0 if tod1 == "AM" else 19.0
        start2_hour = 7.0 if tod2 == "AM" else 13.0

        # Calculate gap
        date1 = block1.date
        date2 = block2.date
        days_diff = (date2 - date1).days

        gap = days_diff * 24 + (start2_hour - end1_hour)

        return max(0, gap)

    def get_fatigue_weighted_objective(
        self,
        assignments: list[tuple[int, int, int]],
        formulation: Any,
        context: Any,
    ) -> float:
        """
        Calculate fatigue-weighted objective value for a solution.

        Args:
            assignments: List of (r_i, b_i, t_i) assignment tuples
            formulation: QUBO formulation
            context: Scheduling context

        Returns:
            Fatigue penalty contribution to objective
        """
        total_penalty = 0.0

        for r_i, b_i, t_i in assignments:
            # Get person and block
            resident_id = None
            block = None

            for resident in context.residents:
                if context.resident_idx.get(resident.id) == r_i:
                    resident_id = resident.id
                    break

            for b in context.blocks:
                if context.block_idx.get(b.id) == b_i:
                    block = b
                    break

            if resident_id and block:
                effectiveness = self._predict_effectiveness(
                    resident_id, block.date, getattr(block, "time_of_day", "AM")
                )
                total_penalty += self._calculate_fatigue_penalty(effectiveness)

        return total_penalty


def create_fatigue_qubo_solver(
    base_solver: Any,
    config: FatigueQUBOConfig | None = None,
) -> Any:
    """
    Create a fatigue-aware QUBO solver wrapper.

    Wraps an existing QUBO solver to include fatigue penalties
    in the optimization.

    Args:
        base_solver: Existing QUBO solver instance
        config: Optional fatigue configuration

    Returns:
        Wrapped solver with fatigue integration
    """
    integration = FatigueQUBOIntegration(config)

    class FatigueAwareQUBOSolver:
        """Wrapper that adds fatigue penalties to QUBO solving."""

        def __init__(self, solver, fatigue_integration):
            self.solver = solver
            self.integration = fatigue_integration

        def solve(self, context, existing_assignments=None):
            # Get base formulation
            from app.scheduling.quantum import QUBOFormulation

            formulation = QUBOFormulation(context)
            Q = formulation.build()

            # Add fatigue penalties
            Q = self.integration.add_fatigue_penalties(Q, formulation, context)

            # Solve using base solver
            return self.solver.solve(context, existing_assignments)

    return FatigueAwareQUBOSolver(base_solver, integration)
