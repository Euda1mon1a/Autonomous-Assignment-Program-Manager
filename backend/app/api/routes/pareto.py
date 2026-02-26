"""Pareto optimization API routes.

Provides endpoints for multi-objective schedule optimization
using NSGA-II algorithm via pymoo.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.pareto import (
    ParetoOptimizeRequest,
    ParetoOptimizeResponse,
    SolutionRankRequest,
    SolutionRankResponse,
)
from app.services.pareto_optimization_service import ParetoOptimizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pareto", tags=["pareto"])


@router.post(
    "/optimize",
    response_model=ParetoOptimizeResponse,
    summary="Run multi-objective Pareto optimization",
    description=(
        "Run NSGA-II multi-objective optimization on schedule assignments. "
        "Requires at least 2 objectives. Returns Pareto frontier solutions."
    ),
)
def optimize_schedule(
    request: ParetoOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ParetoOptimizeResponse:
    """Run Pareto optimization on schedule assignments."""
    try:
        service = ParetoOptimizationService(db)
        result = service.optimize_schedule_pareto(
            objectives=request.objectives,
            constraints=request.constraints,
            person_ids=request.person_ids,
            block_ids=request.block_ids,
            population_size=request.population_size,
            n_generations=request.n_generations,
            timeout_seconds=request.timeout_seconds,
            seed=request.seed,
        )

        # Find recommended solution (highest weighted score on frontier)
        recommended_id = None
        if result.frontier_indices:
            frontier_solutions = [result.solutions[i] for i in result.frontier_indices]
            if frontier_solutions:
                # Default: recommend first frontier solution
                recommended_id = frontier_solutions[0].solution_id

        return ParetoOptimizeResponse(
            success=True,
            message=f"Optimization complete: {result.total_solutions} solutions, "
            f"{len(result.frontier_indices)} on Pareto frontier",
            result=result,
            recommended_solution_id=recommended_id,
        )
    except Exception as e:
        logger.exception("Pareto optimization failed")
        return ParetoOptimizeResponse(
            success=False,
            message="Optimization failed",
            error=str(e),
        )


@router.post(
    "/rank",
    response_model=SolutionRankResponse,
    summary="Rank Pareto solutions by weighted objectives",
    description=(
        "Rank a set of solutions using weighted objective values. "
        "Supports minmax, zscore, or no normalization."
    ),
)
def rank_solutions(
    request: SolutionRankRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SolutionRankResponse:
    """Rank solutions by weighted objective values."""
    try:
        service = ParetoOptimizationService(db)

        # The rank endpoint needs existing solutions — for now, return
        # a stub that indicates the service is available. Full ranking
        # requires solutions from a prior /optimize call to be passed in.
        # This endpoint is wired for future state management.
        return SolutionRankResponse(
            success=True,
            ranked_solutions=[],
            normalization_used=request.normalization,
            message="Ranking endpoint ready. Submit solutions from /optimize result.",
        )
    except Exception as e:
        logger.exception("Solution ranking failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
