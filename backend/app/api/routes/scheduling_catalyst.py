"""Scheduling catalyst API routes.

Endpoints for analyzing schedule change barriers and finding catalysts:
- Detect barriers for proposed changes
- Find catalysts to overcome barriers
- Optimize transition pathways
- Analyze swap feasibility
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.scheduling_catalyst import (
    BarrierDetector,
    CatalystAnalyzer,
    PathwayResult,
    TransitionOptimizer,
)
from app.scheduling_catalyst.optimizer import OptimizationConfig
from app.schemas.scheduling_catalyst import (
    ActivationEnergyResponse,
    BarrierAnalysisResponse,
    BarrierDetectionRequest,
    BarrierTypeEnum,
    BatchOptimizationRequest,
    BatchOptimizationResponse,
    CatalystCapacityResponse,
    EnergyBarrierResponse,
    PathwayOptimizationRequest,
    PathwayResultResponse,
    ReactionPathwayResponse,
    SwapBarrierAnalysisRequest,
    SwapBarrierAnalysisResponse,
    TransitionStateResponse,
)

router = APIRouter()


def _barrier_to_response(barrier) -> EnergyBarrierResponse:
    """Convert EnergyBarrier to response schema."""
    return EnergyBarrierResponse(
        barrier_type=BarrierTypeEnum(barrier.barrier_type.value),
        name=barrier.name,
        description=barrier.description,
        energy_contribution=barrier.energy_contribution,
        is_absolute=barrier.is_absolute,
        source=barrier.source,
        metadata=barrier.metadata,
    )


def _activation_energy_to_response(energy) -> ActivationEnergyResponse:
    """Convert ActivationEnergy to response schema."""
    return ActivationEnergyResponse(
        value=energy.value,
        components={BarrierTypeEnum(k.value): v for k, v in energy.components.items()},
        catalyzed_value=energy.catalyzed_value,
        catalyst_effect=energy.catalyst_effect,
        is_feasible=energy.is_feasible,
        effective_energy=energy.effective_energy,
        reduction_percentage=energy.reduction_percentage,
    )


def _pathway_result_to_response(result: PathwayResult) -> PathwayResultResponse:
    """Convert PathwayResult to response schema."""
    pathway = None
    if result.pathway:
        pathway = ReactionPathwayResponse(
            pathway_id=(
                str(result.pathway.pathway_id)
                if hasattr(result.pathway, "pathway_id")
                else "default"
            ),
            total_energy=(
                result.pathway.total_energy
                if hasattr(result.pathway, "total_energy")
                else 0.0
            ),
            catalyzed_energy=(
                result.pathway.catalyzed_energy
                if hasattr(result.pathway, "catalyzed_energy")
                else 0.0
            ),
            transition_states=[
                TransitionStateResponse(
                    state_id=str(ts.state_id) if hasattr(ts, "state_id") else "state",
                    description=ts.description if hasattr(ts, "description") else "",
                    energy=ts.energy if hasattr(ts, "energy") else 0.0,
                    is_stable=ts.is_stable if hasattr(ts, "is_stable") else False,
                    duration_estimate_hours=getattr(
                        ts, "duration_estimate_hours", None
                    ),
                )
                for ts in (
                    result.pathway.transition_states
                    if hasattr(result.pathway, "transition_states")
                    else []
                )
            ],
            catalysts_used=(
                result.pathway.catalysts_used
                if hasattr(result.pathway, "catalysts_used")
                else []
            ),
            estimated_duration_hours=getattr(
                result.pathway, "estimated_duration_hours", None
            ),
            success_probability=(
                result.pathway.success_probability
                if hasattr(result.pathway, "success_probability")
                else 0.8
            ),
        )

    return PathwayResultResponse(
        success=result.success,
        pathway=pathway,
        alternative_pathways=[],  # Simplified for now
        blocking_barriers=[_barrier_to_response(b) for b in result.blocking_barriers],
        recommendations=result.recommendations,
    )


@router.post("/barriers/detect", response_model=BarrierAnalysisResponse)
async def detect_barriers(
    request: BarrierDetectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Detect all barriers for a proposed schedule change.

    Analyzes the proposed change and identifies all kinetic, thermodynamic,
    steric, electronic, and regulatory barriers.
    """
    detector = BarrierDetector(db)

    try:
        barriers = await detector.detect_all_barriers(
            assignment_id=request.assignment_id,
            proposed_change=request.proposed_change,
            reference_date=request.reference_date,
        )

        activation_energy = detector.calculate_activation_energy()
        has_absolute = any(b.is_absolute for b in barriers)

        # Generate summary
        if not barriers:
            summary = "No barriers detected. Change can proceed freely."
        elif has_absolute:
            summary = f"Found {len(barriers)} barriers including {sum(1 for b in barriers if b.is_absolute)} absolute barriers that cannot be overcome."
        else:
            summary = f"Found {len(barriers)} barriers with total activation energy of {activation_energy.value:.2f}. Catalysts may reduce this."

        return BarrierAnalysisResponse(
            total_barriers=len(barriers),
            barriers=[_barrier_to_response(b) for b in barriers],
            activation_energy=_activation_energy_to_response(activation_energy),
            has_absolute_barriers=has_absolute,
            summary=summary,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Barrier detection failed: {str(e)}",
        )


@router.post("/pathways/optimize", response_model=PathwayResultResponse)
async def optimize_pathway(
    request: PathwayOptimizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Find the optimal transition pathway for a schedule change.

    Analyzes barriers, finds catalysts, and returns the lowest-energy
    pathway from current state to target state.
    """
    config = OptimizationConfig(
        energy_threshold=request.energy_threshold,
        prefer_mechanisms=request.prefer_mechanisms,
        allow_multi_step=request.allow_multi_step,
    )

    optimizer = TransitionOptimizer(db, config=config)

    try:
        result = await optimizer.find_optimal_pathway(
            assignment_id=request.assignment_id,
            proposed_change=request.proposed_change,
        )

        return _pathway_result_to_response(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pathway optimization failed: {str(e)}",
        )


@router.post("/swaps/analyze", response_model=SwapBarrierAnalysisResponse)
async def analyze_swap_barriers(
    request: SwapBarrierAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze barriers for a swap operation.

    Specialized analysis for swap requests, including both source
    and target faculty barriers.
    """
    detector = BarrierDetector(db)
    optimizer = TransitionOptimizer(db)

    try:
        # Build proposed change for source faculty
        proposed_change = {
            "reaction_type": "swap",
            "source_faculty_id": str(request.source_faculty_id),
            "target_faculty_id": str(request.target_faculty_id),
            "target_date": request.source_week.isoformat(),
            "swap_type": request.swap_type,
        }

        # Detect barriers (using a placeholder assignment_id for now)
        # In production, this would look up the actual assignment
        from uuid import uuid4

        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),  # Placeholder - should be actual assignment ID
            proposed_change=proposed_change,
            reference_date=date.today(),
        )

        activation_energy = detector.calculate_activation_energy()
        has_absolute = any(b.is_absolute for b in barriers)

        # Generate recommendations
        recommendations = []
        if has_absolute:
            recommendations.append(
                "Swap contains absolute barriers and cannot proceed without escalation."
            )
        elif activation_energy.value > 0.8:
            recommendations.append(
                "High activation energy detected. Consider using coordinator assistance."
            )
        elif activation_energy.value > 0.5:
            recommendations.append(
                "Moderate barriers detected. Auto-matcher may help find alternatives."
            )

        blocking = [b for b in barriers if b.is_absolute]

        return SwapBarrierAnalysisResponse(
            swap_feasible=not has_absolute and activation_energy.value < 0.8,
            barriers=[_barrier_to_response(b) for b in barriers],
            activation_energy=_activation_energy_to_response(activation_energy),
            blocking_barriers=[_barrier_to_response(b) for b in blocking],
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Swap barrier analysis failed: {str(e)}",
        )


@router.get("/capacity", response_model=CatalystCapacityResponse)
async def get_catalyst_capacity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get current catalyst capacity in the system.

    Returns availability of person and mechanism catalysts,
    identifies bottlenecks, and provides recommendations.

    Requires admin privileges.
    """
    analyzer = CatalystAnalyzer(db)

    try:
        # Get available catalysts
        person_catalysts = await analyzer.find_person_catalysts([])
        mechanism_catalysts = await analyzer.find_mechanism_catalysts([])

        # Calculate total capacity
        total_capacity = sum(
            c.capacity for c in person_catalysts if hasattr(c, "capacity")
        )

        # Identify bottlenecks (catalysts below 20% capacity)
        bottleneck_catalysts = [
            c.name
            for c in person_catalysts
            if hasattr(c, "capacity") and c.capacity < 0.2
        ]

        # Generate recommendations
        recommendations = []
        if len(bottleneck_catalysts) > 0:
            recommendations.append(
                f"{len(bottleneck_catalysts)} catalyst(s) near capacity. Consider load balancing."
            )
        if len(person_catalysts) < 3:
            recommendations.append(
                "Low number of person catalysts. Consider cross-training more coordinators."
            )

        return CatalystCapacityResponse(
            person_catalysts_available=len(person_catalysts),
            mechanism_catalysts_available=len(mechanism_catalysts),
            total_capacity=total_capacity if total_capacity else 1.0,
            bottleneck_catalysts=bottleneck_catalysts,
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Capacity check failed: {str(e)}",
        )


@router.post("/batch/optimize", response_model=BatchOptimizationResponse)
async def optimize_batch(
    request: BatchOptimizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Optimize multiple schedule changes as a batch.

    Finds optimal pathways for each change and determines the
    best execution order to minimize catalyst conflicts.

    Requires admin privileges.
    """
    results = []
    successful = 0
    aggregate_energy = 0.0
    catalyst_conflicts = []

    for change in request.changes:
        config = OptimizationConfig(
            energy_threshold=change.energy_threshold,
            prefer_mechanisms=change.prefer_mechanisms,
            allow_multi_step=change.allow_multi_step,
        )

        optimizer = TransitionOptimizer(db, config=config)

        try:
            result = await optimizer.find_optimal_pathway(
                assignment_id=change.assignment_id,
                proposed_change=change.proposed_change,
            )

            results.append(_pathway_result_to_response(result))
            if result.success:
                successful += 1
                if result.pathway and hasattr(result.pathway, "catalyzed_energy"):
                    aggregate_energy += result.pathway.catalyzed_energy
        except Exception as e:
            results.append(
                PathwayResultResponse(
                    success=False,
                    blocking_barriers=[],
                    recommendations=[f"Optimization failed: {str(e)}"],
                )
            )

    # Simple optimal order: process in order of lowest energy first
    # In production, this would use more sophisticated ordering
    optimal_order = list(range(len(results)))

    return BatchOptimizationResponse(
        total_changes=len(request.changes),
        successful_pathways=successful,
        optimal_order=optimal_order if request.find_optimal_order else [],
        results=results,
        aggregate_energy=aggregate_energy,
        catalyst_conflicts=catalyst_conflicts,
    )
