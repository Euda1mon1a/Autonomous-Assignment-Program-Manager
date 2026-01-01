"""Shapley Value Service for Fair Workload Distribution.

Implements cooperative game theory's Shapley value calculation
to determine fair workload allocation based on marginal contributions.

Key features:
- Monte Carlo approximation for computational efficiency
- Marginal contribution analysis (coverage gained per faculty)
- Fair workload targets based on Shapley proportions
- Equity gap detection (actual vs. fair workload)
- Integration with existing assignment and resilience frameworks

Mathematical Foundation:
φᵢ(v) = Σ [|S|!(n-|S|-1)!/n!] × [v(S∪{i}) - v(S)]

Where:
- φᵢ(v) = Shapley value for faculty i
- S = coalition of faculty (subset not containing i)
- v(S) = value function (total coverage provided by coalition S)
- n = total number of faculty

The Shapley value is the unique fair division satisfying:
1. Efficiency: Sum of all Shapley values = total value
2. Symmetry: Identical players get identical payoffs
3. Linearity: Linear in the value function
4. Null player: Zero contribution players get zero payoff
"""

import logging
import random
from collections import defaultdict
from datetime import date
from typing import Callable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.schemas.game_theory import (
    FacultyShapleyMetrics,
    ShapleyValueRequest,
    ShapleyValueResult,
)

logger = logging.getLogger(__name__)


class ShapleyValueService:
    """Service for calculating Shapley values for fair workload distribution."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the Shapley value service.

        Args:
            db: Async database session
        """
        self.db = db

    async def calculate_shapley_values(
        self,
        faculty_ids: list[UUID],
        start_date: date,
        end_date: date,
        num_samples: int = 1000,
    ) -> dict[UUID, ShapleyValueResult]:
        """
        Calculate Shapley values for faculty workload contribution.

        Uses Monte Carlo sampling to approximate the Shapley value formula:
        φᵢ(v) = Σ [|S|!(n-|S|-1)!/n!] × [v(S∪{i}) - v(S)]

        Args:
            faculty_ids: List of faculty member UUIDs to analyze
            start_date: Start date for workload analysis
            end_date: End date for workload analysis (inclusive)
            num_samples: Number of random permutations for Monte Carlo (more = better accuracy)

        Returns:
            Dictionary mapping faculty_id to ShapleyValueResult

        Example:
            >>> service = ShapleyValueService(db)
            >>> results = await service.calculate_shapley_values(
            ...     faculty_ids=[fac1_id, fac2_id, fac3_id],
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 3, 31),
            ...     num_samples=2000
            ... )
            >>> results[fac1_id].shapley_value  # 0.35 (35% contribution)
            >>> results[fac1_id].fair_workload_target  # 280 hours (35% of total)
        """
        # Load faculty data
        faculty_map = await self._load_faculty(faculty_ids)
        if len(faculty_map) < 2:
            raise ValueError("Need at least 2 faculty members for Shapley calculation")

        # Load assignments for the period
        assignments_by_faculty = await self._load_assignments(
            faculty_ids, start_date, end_date
        )

        # Get total coverage needed (all blocks in period)
        total_coverage = await self._calculate_total_coverage(start_date, end_date)

        # Define value function: coalition -> total coverage provided
        def value_function(coalition: set[UUID]) -> float:
            """Calculate total coverage (blocks covered) by a coalition of faculty."""
            if not coalition:
                return 0.0

            # Count unique blocks covered by coalition
            covered_blocks = set()
            for fac_id in coalition:
                for assignment in assignments_by_faculty.get(fac_id, []):
                    covered_blocks.add(assignment.block_id)

            return float(len(covered_blocks))

        # Run Monte Carlo approximation
        shapley_values = await self._monte_carlo_shapley(
            list(faculty_ids), value_function, num_samples
        )

        # Calculate current workloads
        current_workloads = await self._calculate_workloads(
            faculty_ids, assignments_by_faculty
        )

        # Calculate total actual hours
        total_hours = sum(current_workloads.values())

        # Build results
        results = {}
        total_value = sum(shapley_values.values())

        for fac_id in faculty_ids:
            shapley_value = shapley_values[fac_id]
            current_workload = current_workloads[fac_id]

            # Normalize Shapley value to proportion (0-1)
            shapley_proportion = shapley_value / total_value if total_value > 0 else 0.0

            # Fair workload target based on Shapley proportion
            fair_workload_target = shapley_proportion * total_hours

            # Equity gap (positive = overworked, negative = underworked)
            equity_gap = current_workload - fair_workload_target

            # Marginal contribution (value added by this faculty)
            marginal_contribution = shapley_value

            results[fac_id] = ShapleyValueResult(
                faculty_id=fac_id,
                faculty_name=faculty_map[fac_id].name,
                shapley_value=shapley_proportion,
                marginal_contribution=marginal_contribution,
                fair_workload_target=fair_workload_target,
                current_workload=current_workload,
                equity_gap=equity_gap,
            )

        return results

    async def get_equity_report(
        self,
        faculty_ids: list[UUID],
        start_date: date,
        end_date: date,
        num_samples: int = 1000,
    ) -> FacultyShapleyMetrics:
        """
        Generate a comprehensive equity report using Shapley values.

        Args:
            faculty_ids: List of faculty member UUIDs
            start_date: Start date for analysis
            end_date: End date for analysis
            num_samples: Monte Carlo samples

        Returns:
            FacultyShapleyMetrics with summary statistics and per-faculty results

        Example:
            >>> metrics = await service.get_equity_report(
            ...     faculty_ids=all_faculty,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31)
            ... )
            >>> metrics.equity_gap_std_dev  # 12.5 hours (low = fair distribution)
            >>> metrics.overworked_count  # 2 faculty over their fair share
        """
        results = await self.calculate_shapley_values(
            faculty_ids, start_date, end_date, num_samples
        )

        # Calculate summary statistics
        equity_gaps = [r.equity_gap for r in results.values()]
        total_workload = sum(r.current_workload for r in results.values())
        total_fair_target = sum(r.fair_workload_target for r in results.values())

        # Count faculty over/under fair share
        overworked_count = sum(1 for gap in equity_gaps if gap > 0)
        underworked_count = sum(1 for gap in equity_gaps if gap < 0)

        # Calculate standard deviation of equity gaps (lower = more equitable)
        import statistics

        equity_gap_std_dev = (
            statistics.stdev(equity_gaps) if len(equity_gaps) > 1 else 0.0
        )

        # Identify most/least loaded faculty
        sorted_by_gap = sorted(results.values(), key=lambda x: x.equity_gap)
        most_overworked = sorted_by_gap[-1] if sorted_by_gap else None
        most_underworked = sorted_by_gap[0] if sorted_by_gap else None

        return FacultyShapleyMetrics(
            faculty_results=list(results.values()),
            total_workload=total_workload,
            total_fair_target=total_fair_target,
            equity_gap_std_dev=equity_gap_std_dev,
            overworked_count=overworked_count,
            underworked_count=underworked_count,
            most_overworked_faculty_id=(
                most_overworked.faculty_id if most_overworked else None
            ),
            most_underworked_faculty_id=(
                most_underworked.faculty_id if most_underworked else None
            ),
        )

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _load_faculty(self, faculty_ids: list[UUID]) -> dict[UUID, Person]:
        """Load faculty members by ID."""
        stmt = select(Person).where(
            Person.id.in_(faculty_ids), Person.type == "faculty"
        )
        result = await self.db.execute(stmt)
        faculty = result.scalars().all()

        return {f.id: f for f in faculty}

    async def _load_assignments(
        self, faculty_ids: list[UUID], start_date: date, end_date: date
    ) -> dict[UUID, list[Assignment]]:
        """
        Load assignments for faculty within date range.

        Returns:
            Dictionary mapping faculty_id to list of their assignments
        """
        stmt = (
            select(Assignment)
            .join(Block)
            .options(selectinload(Assignment.block))
            .where(
                Assignment.person_id.in_(faculty_ids),
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        result = await self.db.execute(stmt)
        assignments = result.scalars().all()

        # Group by faculty
        by_faculty = defaultdict(list)
        for assignment in assignments:
            by_faculty[assignment.person_id].append(assignment)

        return dict(by_faculty)

    async def _calculate_total_coverage(
        self, start_date: date, end_date: date
    ) -> float:
        """Calculate total coverage blocks needed in period."""
        stmt = select(func.count(Block.id)).where(
            Block.date >= start_date,
            Block.date <= end_date,
            Block.is_weekend == False,  # noqa: E712
            Block.is_holiday == False,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return float(result.scalar_one())

    async def _calculate_workloads(
        self,
        faculty_ids: list[UUID],
        assignments_by_faculty: dict[UUID, list[Assignment]],
    ) -> dict[UUID, float]:
        """
        Calculate current workload (hours) for each faculty member.

        Each block = 4 hours (half-day)
        """
        workloads = {}
        for fac_id in faculty_ids:
            assignments = assignments_by_faculty.get(fac_id, [])
            # Each assignment is a half-day block = 4 hours
            workloads[fac_id] = len(assignments) * 4.0

        return workloads

    async def _monte_carlo_shapley(
        self,
        faculty_ids: list[UUID],
        value_function: Callable[[set[UUID]], float],
        num_samples: int,
    ) -> dict[UUID, float]:
        """
        Approximate Shapley values using Monte Carlo sampling.

        Algorithm:
        1. Generate random permutations of faculty
        2. For each permutation, compute marginal contribution of each faculty
           (value added when they join the coalition in that order)
        3. Average marginal contributions across all permutations

        This approximates the exact formula:
        φᵢ(v) = Σ [|S|!(n-|S|-1)!/n!] × [v(S∪{i}) - v(S)]

        Args:
            faculty_ids: List of faculty UUIDs
            value_function: Maps coalition (set of UUIDs) -> total value
            num_samples: Number of random permutations to sample

        Returns:
            Dictionary mapping faculty_id to Shapley value
        """
        shapley = dict.fromkeys(faculty_ids, 0.0)

        for _ in range(num_samples):
            # Random permutation (order of joining coalition)
            order = random.sample(faculty_ids, len(faculty_ids))

            coalition = set()
            for fac_id in order:
                # Marginal contribution: v(S ∪ {i}) - v(S)
                before = value_function(coalition)
                coalition.add(fac_id)
                after = value_function(coalition)

                marginal_contribution = after - before
                shapley[fac_id] += marginal_contribution

        # Average over samples
        for fac_id in shapley:
            shapley[fac_id] /= num_samples

        return shapley

    # =========================================================================
    # Recommendation Engine
    # =========================================================================

    async def suggest_workload_adjustments(
        self,
        faculty_ids: list[UUID],
        start_date: date,
        end_date: date,
        threshold: float = 10.0,
    ) -> list[dict]:
        """
        Suggest workload adjustments to achieve Shapley fairness.

        Args:
            faculty_ids: Faculty to analyze
            start_date: Period start
            end_date: Period end
            threshold: Equity gap threshold (hours) to trigger recommendation

        Returns:
            List of adjustment recommendations

        Example:
            >>> suggestions = await service.suggest_workload_adjustments(
            ...     faculty_ids=all_faculty,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 3, 31),
            ...     threshold=8.0
            ... )
            >>> suggestions[0]
            {
                'faculty_id': UUID('...'),
                'faculty_name': 'Dr. Smith',
                'action': 'reduce',
                'hours': 12.5,
                'reason': 'Working 12.5 hours above Shapley-fair target'
            }
        """
        results = await self.calculate_shapley_values(faculty_ids, start_date, end_date)

        suggestions = []
        for result in results.values():
            if abs(result.equity_gap) > threshold:
                action = "reduce" if result.equity_gap > 0 else "increase"
                reason = (
                    f"Working {abs(result.equity_gap):.1f} hours "
                    f"{'above' if result.equity_gap > 0 else 'below'} "
                    f"Shapley-fair target based on marginal contribution"
                )

                suggestions.append(
                    {
                        "faculty_id": result.faculty_id,
                        "faculty_name": result.faculty_name,
                        "action": action,
                        "hours": abs(result.equity_gap),
                        "reason": reason,
                        "current_workload": result.current_workload,
                        "fair_target": result.fair_workload_target,
                    }
                )

        # Sort by magnitude of gap (most urgent first)
        suggestions.sort(key=lambda x: x["hours"], reverse=True)

        return suggestions


def get_shapley_value_service(db: AsyncSession) -> ShapleyValueService:
    """Dependency injection for ShapleyValueService."""
    return ShapleyValueService(db)
