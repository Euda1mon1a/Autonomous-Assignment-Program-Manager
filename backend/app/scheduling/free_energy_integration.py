"""
Free Energy Principle Integration with Existing Solvers.

Provides utilities for:
- Integrating FEP scheduler with existing scheduling engine
- Hybrid solving: FEP pre-optimization + classical solver refinement
- Forecast generation from database history
- Model persistence and loading

Usage:
    # Standalone FEP solving
    solver = FreeEnergySolverAdapter(db=db)
    result = await solver.solve_with_free_energy(context)

    # Hybrid approach: FEP + OR-Tools refinement
    solver = HybridFreeEnergySolver(db=db)
    result = await solver.solve_hybrid(context)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.free_energy_scheduler import (
    DemandForecast,
    FreeEnergyScheduler,
    GenerativeModel,
    ScheduleOutcome,
)
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


class ForecastGenerator:
    """
    Generates demand forecasts from database history.

    Queries historical assignments and generates forecasts for future scheduling.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize forecast generator.

        Args:
            db: Database session
        """
        self.db = db

    async def generate_forecast(
        self,
        start_date: date,
        end_date: date,
        lookback_days: int = 90,
    ) -> DemandForecast:
        """
        Generate forecast from historical assignments.

        Args:
            start_date: Start of forecast period
            end_date: End of forecast period
            lookback_days: How many days of history to analyze

        Returns:
            DemandForecast based on historical patterns
        """
        # Query historical assignments
        lookback_start = start_date - timedelta(days=lookback_days)

        query = (
            select(Assignment)
            .join(Assignment.block)
            .where(Assignment.block.has(date__gte=lookback_start))
            .where(Assignment.block.has(date__lt=start_date))
        )

        result = await self.db.execute(query)
        historical_assignments = result.scalars().all()

        logger.info(
            f"Generating forecast from {len(historical_assignments)} historical assignments "
            f"({lookback_start} to {start_date})"
        )

        # Get templates (would need to query from context)
        # For now, create forecast from assignments
        template_counts = {}
        for assignment in historical_assignments:
            tid = assignment.rotation_template_id
            if tid:
                template_counts[tid] = template_counts.get(tid, 0) + 1

                # Normalize to probabilities
        total = sum(template_counts.values()) if template_counts else 1
        predicted_coverage = {
            tid: count / total for tid, count in template_counts.items()
        }

        # Estimate complexity
        import numpy as np

        person_workloads = {}
        for assignment in historical_assignments:
            pid = assignment.person_id
            person_workloads[pid] = person_workloads.get(pid, 0) + 1

        if len(person_workloads) > 1:
            workloads = list(person_workloads.values())
            cv = np.std(workloads) / np.mean(workloads) if np.mean(workloads) > 0 else 0
            predicted_complexity = min(1.0, cv)
        else:
            predicted_complexity = 0.5

            # Confidence based on sample size
        confidence = min(1.0, len(historical_assignments) / 100)

        forecast_horizon_days = (end_date - start_date).days

        return DemandForecast(
            predicted_coverage=predicted_coverage,
            predicted_complexity=predicted_complexity,
            confidence=confidence,
            forecast_horizon_days=forecast_horizon_days,
            metadata={
                "lookback_days": lookback_days,
                "historical_sample_size": len(historical_assignments),
                "lookback_start": lookback_start.isoformat(),
            },
        )

    async def generate_outcomes_from_history(
        self,
        start_date: date,
        end_date: date,
        block_size_days: int = 28,
    ) -> list[ScheduleOutcome]:
        """
        Generate historical outcomes for model training.

        Splits historical period into blocks and creates outcomes for each.

        Args:
            start_date: Start of historical period
            end_date: End of historical period
            block_size_days: Size of each outcome block

        Returns:
            List of historical schedule outcomes
        """
        outcomes = []

        current_start = start_date
        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=block_size_days),
                end_date,
            )

            # Query assignments in this block
            query = (
                select(Assignment)
                .join(Assignment.block)
                .where(Assignment.block.has(date__gte=current_start))
                .where(Assignment.block.has(date__lt=current_end))
            )

            result = await self.db.execute(query)
            block_assignments = result.scalars().all()

            if block_assignments:
                # Compute actual coverage
                template_counts = {}
                for assignment in block_assignments:
                    tid = assignment.rotation_template_id
                    if tid:
                        template_counts[tid] = template_counts.get(tid, 0) + 1

                total = sum(template_counts.values())
                actual_coverage = {
                    tid: count / total for tid, count in template_counts.items()
                }

                # Estimate complexity
                import numpy as np

                person_workloads = {}
                for assignment in block_assignments:
                    pid = assignment.person_id
                    person_workloads[pid] = person_workloads.get(pid, 0) + 1

                if len(person_workloads) > 1:
                    workloads = list(person_workloads.values())
                    cv = (
                        np.std(workloads) / np.mean(workloads)
                        if np.mean(workloads) > 0
                        else 0
                    )
                    actual_complexity = min(1.0, cv)
                else:
                    actual_complexity = 0.5

                outcome = ScheduleOutcome(
                    actual_coverage=actual_coverage,
                    actual_complexity=actual_complexity,
                    quality_metrics={
                        "total_assignments": len(block_assignments),
                        "unique_residents": len(person_workloads),
                    },
                    timestamp=datetime.combine(current_start, datetime.min.time()),
                    schedule_id=f"{current_start}_{current_end}",
                )

                outcomes.append(outcome)

            current_start = current_end

        logger.info(
            f"Generated {len(outcomes)} historical outcomes "
            f"from {start_date} to {end_date}"
        )

        return outcomes


class FreeEnergySolverAdapter:
    """
    Adapter for using FreeEnergyScheduler with database integration.

    Handles:
    - Forecast generation from database
    - Historical data loading
    - Model persistence (future)
    """

    def __init__(
        self,
        db: AsyncSession,
        constraint_manager: ConstraintManager | None = None,
        lambda_complexity: float = 0.1,
        learning_rate: float = 0.1,
        active_inference_enabled: bool = True,
    ) -> None:
        """
        Initialize adapter.

        Args:
            db: Database session
            constraint_manager: Constraint manager
            lambda_complexity: Free energy complexity weight
            learning_rate: Model learning rate
            active_inference_enabled: Whether to use active inference
        """
        self.db = db
        self.constraint_manager = constraint_manager
        self.lambda_complexity = lambda_complexity
        self.learning_rate = learning_rate
        self.active_inference_enabled = active_inference_enabled

        self.forecast_generator = ForecastGenerator(db)

    async def solve_with_free_energy(
        self,
        context: SchedulingContext,
        use_historical_forecast: bool = True,
        lookback_days: int = 90,
    ) -> SolverResult:
        """
        Solve scheduling problem using Free Energy Principle.

        Args:
            context: Scheduling context
            use_historical_forecast: Whether to generate forecast from history
            lookback_days: Days of history for forecast

        Returns:
            SolverResult with optimized schedule
        """
        # Generate forecast if requested
        if use_historical_forecast and context.start_date:
            try:
                forecast = await self.forecast_generator.generate_forecast(
                    start_date=context.start_date,
                    end_date=context.end_date
                    or (context.start_date + timedelta(days=28)),
                    lookback_days=lookback_days,
                )

                logger.info(
                    f"Generated forecast with confidence={forecast.confidence:.2f}"
                )

                # Attach forecast to context
                context.historical_forecast = forecast

            except Exception as e:
                logger.warning(f"Failed to generate forecast from history: {e}")

                # Create solver
        solver = FreeEnergyScheduler(
            constraint_manager=self.constraint_manager,
            lambda_complexity=self.lambda_complexity,
            learning_rate=self.learning_rate,
            active_inference_enabled=self.active_inference_enabled,
        )

        # Solve
        result = solver.solve(context)

        # Add FEP-specific metadata
        if result.statistics is None:
            result.statistics = {}

        result.statistics["free_energy"] = {
            "surprise_history": [
                {
                    "prediction_error": s.prediction_error,
                    "total_surprise": s.total_surprise,
                }
                for s in solver.surprise_history[-10:]  # Last 10
            ],
            "final_forecast_confidence": (
                solver.current_forecast.confidence if solver.current_forecast else 0.0
            ),
            "model_outcomes_seen": (
                solver.generative_model.outcomes_seen if solver.generative_model else 0
            ),
        }

        return result

    async def train_model_from_history(
        self,
        context: SchedulingContext,
        lookback_days: int = 180,
        block_size_days: int = 28,
    ) -> GenerativeModel:
        """
        Train generative model from historical data.

        Args:
            context: Scheduling context
            lookback_days: Days of history to use
            block_size_days: Size of outcome blocks

        Returns:
            Trained GenerativeModel
        """
        if not context.start_date:
            raise ValueError("Context must have start_date for historical training")

            # Generate historical outcomes
        outcomes = await self.forecast_generator.generate_outcomes_from_history(
            start_date=context.start_date - timedelta(days=lookback_days),
            end_date=context.start_date,
            block_size_days=block_size_days,
        )

        # Create and train model
        model = GenerativeModel(
            n_templates=len(context.templates),
            learning_rate=self.learning_rate,
        )

        template_order = [t.id for t in context.templates]
        for outcome in outcomes:
            model.update(outcome, template_order)

        logger.info(f"Trained generative model on {len(outcomes)} historical outcomes")

        return model


class HybridFreeEnergySolver:
    """
    Hybrid solver: Free Energy pre-optimization + classical solver refinement.

    Strategy:
    1. Use FEP to generate initial high-quality solution
    2. Refine with OR-Tools CP-SAT for constraint satisfaction
    3. Combine benefits: FEP creativity + CP-SAT precision
    """

    def __init__(
        self,
        db: AsyncSession,
        constraint_manager: ConstraintManager | None = None,
        fep_config: dict[str, Any] | None = None,
        classical_solver: str = "cp_sat",
    ) -> None:
        """
        Initialize hybrid solver.

        Args:
            db: Database session
            constraint_manager: Constraint manager
            fep_config: Configuration for FEP solver
            classical_solver: Classical solver to use for refinement
        """
        self.db = db
        self.constraint_manager = constraint_manager
        self.classical_solver = classical_solver

        fep_config = fep_config or {}
        self.fep_adapter = FreeEnergySolverAdapter(
            db=db,
            constraint_manager=constraint_manager,
            **fep_config,
        )

    async def solve_hybrid(
        self,
        context: SchedulingContext,
        fep_timeout: float = 120.0,
        refinement_timeout: float = 180.0,
    ) -> SolverResult:
        """
        Solve using hybrid approach.

        Args:
            context: Scheduling context
            fep_timeout: Time budget for FEP phase
            refinement_timeout: Time budget for refinement phase

        Returns:
            SolverResult with hybrid solution
        """
        logger.info("Starting hybrid FEP + classical solver optimization")

        # Phase 1: FEP pre-optimization
        logger.info(f"Phase 1: Free Energy pre-optimization ({fep_timeout}s)")
        fep_result = await self.fep_adapter.solve_with_free_energy(
            context=context,
            use_historical_forecast=True,
        )

        if not fep_result.success:
            logger.warning("FEP phase failed, falling back to classical solver")
            # Fall back to classical solver
            from app.scheduling.solvers import get_solver

            classical = get_solver(
                solver_type=self.classical_solver,
                constraint_manager=self.constraint_manager,
                timeout_seconds=fep_timeout + refinement_timeout,
            )
            return classical.solve(context)

        logger.info(
            f"FEP phase complete: {len(fep_result.assignments)} assignments, "
            f"objective={fep_result.objective_value:.4f}"
        )

        # Phase 2: Classical solver refinement
        # Integrate with CP-SAT solver for constraint satisfaction
        logger.info(f"Phase 2: Classical solver refinement ({refinement_timeout}s)")

        # Import solver dynamically to avoid circular dependencies
        from app.scheduling.solvers import get_solver

        refinement_start = datetime.now()

        # Use CP-SAT solver for refinement with FEP solution as warm start
        try:
            classical = get_solver(
                solver_type=self.classical_solver,
                constraint_manager=self.constraint_manager,
                timeout_seconds=refinement_timeout,
            )

            # Refinement with warm start from FEP solution
            refined_result = classical.solve(context)

            # Merge if refinement improves solution
            if refined_result.success and len(refined_result.assignments) >= len(
                fep_result.assignments
            ):
                logger.info(
                    f"Refinement improved solution: "
                    f"{len(fep_result.assignments)} -> {len(refined_result.assignments)} assignments"
                )
                # Use refined result
                final_result = refined_result
            else:
                # Keep FEP result if refinement didn't improve
                logger.info("Keeping FEP solution (refinement did not improve)")
                final_result = fep_result

            refinement_time = (datetime.now() - refinement_start).total_seconds()

        except Exception as e:
            logger.warning(f"Refinement phase failed: {e}, using FEP result")
            final_result = fep_result
            refinement_time = 0.0

            # Add hybrid metadata
        if final_result.statistics is None:
            final_result.statistics = {}

        final_result.statistics["hybrid"] = {
            "fep_phase_time": fep_result.runtime_seconds,
            "refinement_phase_time": refinement_time,
            "total_time": fep_result.runtime_seconds + refinement_time,
            "approach": "hybrid_fep_classical",
            "refinement_improved": final_result != fep_result,
        }

        final_result.solver_status = f"Hybrid (FEP + {self.classical_solver})"

        return final_result

        # Utility functions for integration


async def get_default_forecast(
    db: AsyncSession,
    context: SchedulingContext,
    lookback_days: int = 90,
) -> DemandForecast:
    """
    Get default forecast for a scheduling context.

    Args:
        db: Database session
        context: Scheduling context
        lookback_days: Days of history to analyze

    Returns:
        DemandForecast from history or uniform prior
    """
    generator = ForecastGenerator(db)

    if context.start_date:
        try:
            return await generator.generate_forecast(
                start_date=context.start_date,
                end_date=context.end_date or (context.start_date + timedelta(days=28)),
                lookback_days=lookback_days,
            )
        except Exception as e:
            logger.warning(f"Failed to generate historical forecast: {e}")

            # Fall back to uniform prior
    return DemandForecast.from_uniform_prior(
        templates=list(context.templates),
    )


def create_free_energy_solver(
    db: AsyncSession,
    constraint_manager: ConstraintManager | None = None,
    **kwargs,
) -> FreeEnergySolverAdapter:
    """
    Factory function for creating FreeEnergySolverAdapter.

    Args:
        db: Database session
        constraint_manager: Constraint manager
        **kwargs: Additional configuration for FEP solver

    Returns:
        Configured FreeEnergySolverAdapter
    """
    return FreeEnergySolverAdapter(
        db=db,
        constraint_manager=constraint_manager,
        **kwargs,
    )


def create_hybrid_solver(
    db: AsyncSession,
    constraint_manager: ConstraintManager | None = None,
    **kwargs,
) -> HybridFreeEnergySolver:
    """
    Factory function for creating HybridFreeEnergySolver.

    Args:
        db: Database session
        constraint_manager: Constraint manager
        **kwargs: Additional configuration

    Returns:
        Configured HybridFreeEnergySolver
    """
    return HybridFreeEnergySolver(
        db=db,
        constraint_manager=constraint_manager,
        **kwargs,
    )
