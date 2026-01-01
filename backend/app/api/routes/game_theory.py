"""Game Theory API routes.

Endpoints for:
- Configuration strategy management
- Tournament execution and results
- Evolutionary simulation
- TFT validation
- Configuration analysis
"""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.game_theory import (
    ConfigAnalysisRequest,
    ConfigAnalysisResponse,
    EvolutionCreate,
    EvolutionListResponse,
    EvolutionResponse,
    EvolutionResultsResponse,
    PopulationSnapshot,
    SimulationStatus,
    StrategyCreate,
    StrategyListResponse,
    StrategyResponse,
    StrategyType,
    StrategyUpdate,
    TournamentCreate,
    TournamentListResponse,
    TournamentRanking,
    TournamentResponse,
    TournamentResultsResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.game_theory import get_game_theory_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Strategy Endpoints
# =============================================================================


@router.get("/strategies", response_model=StrategyListResponse)
async def list_strategies(
    active_only: bool = Query(True, description="Only show active strategies"),
    db: AsyncSession = Depends(get_async_db),
) -> StrategyListResponse:
    """
    List all configuration strategies.

    Strategies represent different resilience configurations mapped
    to Prisoner's Dilemma behaviors.
    """
    service = get_game_theory_service(db)
    strategies = service.list_strategies(active_only=active_only)

    return StrategyListResponse(
        strategies=[
            StrategyResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                strategy_type=StrategyType(s.strategy_type),
                created_at=s.created_at,
                utilization_target=s.utilization_target,
                cross_zone_borrowing=s.cross_zone_borrowing,
                sacrifice_willingness=s.sacrifice_willingness,
                defense_activation_threshold=s.defense_activation_threshold,
                response_timeout_ms=s.response_timeout_ms,
                initial_action=s.initial_action,
                forgiveness_probability=s.forgiveness_probability,
                retaliation_memory=s.retaliation_memory,
                is_stochastic=s.is_stochastic,
                tournaments_participated=s.tournaments_participated,
                total_matches=s.total_matches,
                total_wins=s.total_wins,
                average_score=s.average_score,
                cooperation_rate=s.cooperation_rate,
                is_active=s.is_active,
            )
            for s in strategies
        ],
        total=len(strategies),
    )


@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    request: StrategyCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StrategyResponse:
    """
    Create a new configuration strategy.

    Maps resilience configuration parameters to game theory behavior.
    """
    service = get_game_theory_service(db)

    strategy = service.create_strategy(
        name=request.name,
        description=request.description,
        strategy_type=request.strategy_type.value,
        created_by=str(current_user.id),
        utilization_target=request.utilization_target,
        cross_zone_borrowing=request.cross_zone_borrowing,
        sacrifice_willingness=request.sacrifice_willingness,
        defense_activation_threshold=request.defense_activation_threshold,
        response_timeout_ms=request.response_timeout_ms,
        initial_action=request.initial_action,
        forgiveness_probability=request.forgiveness_probability,
        retaliation_memory=request.retaliation_memory,
        is_stochastic=request.is_stochastic,
        custom_logic=request.custom_logic,
    )

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        strategy_type=StrategyType(strategy.strategy_type),
        created_at=strategy.created_at,
        utilization_target=strategy.utilization_target,
        cross_zone_borrowing=strategy.cross_zone_borrowing,
        sacrifice_willingness=strategy.sacrifice_willingness,
        defense_activation_threshold=strategy.defense_activation_threshold,
        response_timeout_ms=strategy.response_timeout_ms,
        initial_action=strategy.initial_action,
        forgiveness_probability=strategy.forgiveness_probability,
        retaliation_memory=strategy.retaliation_memory,
        is_stochastic=strategy.is_stochastic,
        tournaments_participated=strategy.tournaments_participated,
        total_matches=strategy.total_matches,
        total_wins=strategy.total_wins,
        average_score=strategy.average_score,
        cooperation_rate=strategy.cooperation_rate,
        is_active=strategy.is_active,
    )


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> StrategyResponse:
    """Get a strategy by ID."""
    service = get_game_theory_service(db)
    strategy = service.get_strategy(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        strategy_type=StrategyType(strategy.strategy_type),
        created_at=strategy.created_at,
        utilization_target=strategy.utilization_target,
        cross_zone_borrowing=strategy.cross_zone_borrowing,
        sacrifice_willingness=strategy.sacrifice_willingness,
        defense_activation_threshold=strategy.defense_activation_threshold,
        response_timeout_ms=strategy.response_timeout_ms,
        initial_action=strategy.initial_action,
        forgiveness_probability=strategy.forgiveness_probability,
        retaliation_memory=strategy.retaliation_memory,
        is_stochastic=strategy.is_stochastic,
        tournaments_participated=strategy.tournaments_participated,
        total_matches=strategy.total_matches,
        total_wins=strategy.total_wins,
        average_score=strategy.average_score,
        cooperation_rate=strategy.cooperation_rate,
        is_active=strategy.is_active,
    )


@router.patch("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    request: StrategyUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> StrategyResponse:
    """Update a strategy."""
    service = get_game_theory_service(db)
    strategy = service.update_strategy(
        strategy_id, **request.model_dump(exclude_unset=True)
    )

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        strategy_type=StrategyType(strategy.strategy_type),
        created_at=strategy.created_at,
        utilization_target=strategy.utilization_target,
        cross_zone_borrowing=strategy.cross_zone_borrowing,
        sacrifice_willingness=strategy.sacrifice_willingness,
        defense_activation_threshold=strategy.defense_activation_threshold,
        response_timeout_ms=strategy.response_timeout_ms,
        initial_action=strategy.initial_action,
        forgiveness_probability=strategy.forgiveness_probability,
        retaliation_memory=strategy.retaliation_memory,
        is_stochastic=strategy.is_stochastic,
        tournaments_participated=strategy.tournaments_participated,
        total_matches=strategy.total_matches,
        total_wins=strategy.total_wins,
        average_score=strategy.average_score,
        cooperation_rate=strategy.cooperation_rate,
        is_active=strategy.is_active,
    )


@router.post("/strategies/defaults")
async def create_default_strategies(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> dict[str, int | list[str]]:
    """
    Create default set of strategies for testing.

    Includes: Conservative TFT, Aggressive, Ultra-Conservative,
    Grudger, Forgiving TFT, and Chaos Monkey.
    """
    service = get_game_theory_service(db)
    created = service.create_default_strategies()

    return {
        "created": len(created),
        "strategies": [s.name for s in created],
    }


# =============================================================================
# Tournament Endpoints
# =============================================================================


@router.get("/tournaments", response_model=TournamentListResponse)
async def list_tournaments(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
) -> TournamentListResponse:
    """List recent tournaments."""
    service = get_game_theory_service(db)
    tournaments = service.list_tournaments(limit=limit)

    return TournamentListResponse(
        tournaments=[
            TournamentResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                created_at=t.created_at,
                created_by=t.created_by,
                turns_per_match=t.turns_per_match,
                repetitions=t.repetitions,
                noise=t.noise,
                strategy_ids=t.strategy_ids,
                status=SimulationStatus(t.status),
                started_at=t.started_at,
                completed_at=t.completed_at,
                error_message=t.error_message,
                celery_task_id=t.celery_task_id,
                total_matches=t.total_matches,
                winner_strategy_id=t.winner_strategy_id,
                winner_strategy_name=t.winner_strategy_name,
            )
            for t in tournaments
        ],
        total=len(tournaments),
    )


@router.post("/tournaments", response_model=TournamentResponse)
async def create_tournament(
    request: TournamentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> TournamentResponse:
    """
    Create a new tournament.

    The tournament will be queued for background execution.
    """
    service = get_game_theory_service(db)

    # Validate strategies exist
    for sid in request.strategy_ids:
        if not service.get_strategy(sid):
            raise HTTPException(status_code=400, detail=f"Strategy {sid} not found")

    tournament = service.create_tournament(
        name=request.name,
        description=request.description,
        strategy_ids=request.strategy_ids,
        created_by=str(current_user.id),
        turns_per_match=request.turns_per_match,
        repetitions=request.repetitions,
        noise=request.noise,
        payoff_cc=request.payoff_cc,
        payoff_cd=request.payoff_cd,
        payoff_dc=request.payoff_dc,
        payoff_dd=request.payoff_dd,
    )

    # Queue background task (or use Celery for production)
    background_tasks.add_task(run_tournament_background, tournament.id, db)

    return TournamentResponse(
        id=tournament.id,
        name=tournament.name,
        description=tournament.description,
        created_at=tournament.created_at,
        created_by=tournament.created_by,
        turns_per_match=tournament.turns_per_match,
        repetitions=tournament.repetitions,
        noise=tournament.noise,
        strategy_ids=tournament.strategy_ids,
        status=SimulationStatus(tournament.status),
        started_at=tournament.started_at,
        completed_at=tournament.completed_at,
        error_message=tournament.error_message,
        celery_task_id=tournament.celery_task_id,
        total_matches=tournament.total_matches,
        winner_strategy_id=tournament.winner_strategy_id,
        winner_strategy_name=tournament.winner_strategy_name,
    )


def run_tournament_background(tournament_id: UUID, db: Session) -> None:
    """Background task to run tournament."""
    try:
        service = get_game_theory_service(db)
        service.run_tournament(tournament_id)
    except Exception as e:
        logger.exception(f"Background tournament {tournament_id} failed: {e}")


@router.get("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> TournamentResponse:
    """Get tournament details."""
    service = get_game_theory_service(db)
    tournament = service.get_tournament(tournament_id)

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return TournamentResponse(
        id=tournament.id,
        name=tournament.name,
        description=tournament.description,
        created_at=tournament.created_at,
        created_by=tournament.created_by,
        turns_per_match=tournament.turns_per_match,
        repetitions=tournament.repetitions,
        noise=tournament.noise,
        strategy_ids=tournament.strategy_ids,
        status=SimulationStatus(tournament.status),
        started_at=tournament.started_at,
        completed_at=tournament.completed_at,
        error_message=tournament.error_message,
        celery_task_id=tournament.celery_task_id,
        total_matches=tournament.total_matches,
        winner_strategy_id=tournament.winner_strategy_id,
        winner_strategy_name=tournament.winner_strategy_name,
    )


@router.get(
    "/tournaments/{tournament_id}/results", response_model=TournamentResultsResponse
)
async def get_tournament_results(
    tournament_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> TournamentResultsResponse:
    """Get detailed tournament results including rankings and payoff matrix."""
    service = get_game_theory_service(db)
    tournament = service.get_tournament(tournament_id)

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.status != "completed":
        raise HTTPException(
            status_code=400, detail=f"Tournament is {tournament.status}, not completed"
        )

    # Parse rankings
    rankings = []
    if tournament.rankings:
        for r in tournament.rankings:
            rankings.append(
                TournamentRanking(
                    rank=r.get("rank", 0),
                    strategy_id=(
                        UUID(r["strategy_id"]) if r.get("strategy_id") else None
                    ),
                    strategy_name=r.get("strategy_name", "Unknown"),
                    total_score=r.get("total_score", 0),
                    average_score=r.get("average_score", 0),
                    wins=r.get("wins", 0),
                    losses=r.get("losses", 0),
                    ties=r.get("ties", 0),
                    cooperation_rate=r.get("cooperation_rate", 0),
                )
            )

    return TournamentResultsResponse(
        id=tournament.id,
        name=tournament.name,
        status=SimulationStatus(tournament.status),
        completed_at=tournament.completed_at,
        rankings=rankings,
        payoff_matrix=tournament.payoff_matrix or {},
        total_matches=tournament.total_matches or 0,
        total_turns=(tournament.total_matches or 0) * tournament.turns_per_match,
        average_cooperation_rate=(
            sum(r.cooperation_rate for r in rankings) / len(rankings) if rankings else 0
        ),
    )


@router.post("/tournaments/{tournament_id}/run")
async def run_tournament_sync(
    tournament_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> dict:
    """
    Run a tournament synchronously (for testing).

    Use POST /tournaments for async execution in production.
    """
    service = get_game_theory_service(db)
    result = service.run_tournament(tournament_id)
    return result


# =============================================================================
# Evolution Endpoints
# =============================================================================


@router.get("/evolution", response_model=EvolutionListResponse)
async def list_evolutions(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
) -> EvolutionListResponse:
    """List recent evolutionary simulations."""
    service = get_game_theory_service(db)
    evolutions = service.list_evolutions(limit=limit)

    return EvolutionListResponse(
        simulations=[
            EvolutionResponse(
                id=e.id,
                name=e.name,
                description=e.description,
                created_at=e.created_at,
                created_by=e.created_by,
                initial_population_size=e.initial_population_size,
                turns_per_interaction=e.turns_per_interaction,
                max_generations=e.max_generations,
                mutation_rate=e.mutation_rate,
                status=SimulationStatus(e.status),
                started_at=e.started_at,
                completed_at=e.completed_at,
                error_message=e.error_message,
                celery_task_id=e.celery_task_id,
                generations_completed=e.generations_completed,
                winner_strategy_id=e.winner_strategy_id,
                winner_strategy_name=e.winner_strategy_name,
                is_evolutionarily_stable=e.is_evolutionarily_stable,
            )
            for e in evolutions
        ],
        total=len(evolutions),
    )


@router.post("/evolution", response_model=EvolutionResponse)
async def create_evolution(
    request: EvolutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> EvolutionResponse:
    """
    Create a new evolutionary simulation.

    Tests which configuration strategy is evolutionarily stable.
    """
    service = get_game_theory_service(db)

    # Validate strategies exist
    for sid_str in request.initial_composition:
        if not service.get_strategy(UUID(sid_str)):
            raise HTTPException(status_code=400, detail=f"Strategy {sid_str} not found")

    evolution = service.create_evolution(
        name=request.name,
        description=request.description,
        initial_composition=request.initial_composition,
        created_by=str(current_user.id),
        turns_per_interaction=request.turns_per_interaction,
        max_generations=request.max_generations,
        mutation_rate=request.mutation_rate,
    )

    # Queue background task
    background_tasks.add_task(run_evolution_background, evolution.id, db)

    return EvolutionResponse(
        id=evolution.id,
        name=evolution.name,
        description=evolution.description,
        created_at=evolution.created_at,
        created_by=evolution.created_by,
        initial_population_size=evolution.initial_population_size,
        turns_per_interaction=evolution.turns_per_interaction,
        max_generations=evolution.max_generations,
        mutation_rate=evolution.mutation_rate,
        status=SimulationStatus(evolution.status),
        started_at=evolution.started_at,
        completed_at=evolution.completed_at,
        error_message=evolution.error_message,
        celery_task_id=evolution.celery_task_id,
        generations_completed=evolution.generations_completed,
        winner_strategy_id=evolution.winner_strategy_id,
        winner_strategy_name=evolution.winner_strategy_name,
        is_evolutionarily_stable=evolution.is_evolutionarily_stable,
    )


def run_evolution_background(evolution_id: UUID, db: Session) -> None:
    """Background task to run evolution."""
    try:
        service = get_game_theory_service(db)
        service.run_evolution(evolution_id)
    except Exception as e:
        logger.exception(f"Background evolution {evolution_id} failed: {e}")


@router.get("/evolution/{evolution_id}", response_model=EvolutionResponse)
async def get_evolution(
    evolution_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> EvolutionResponse:
    """Get evolution simulation details."""
    service = get_game_theory_service(db)
    evolution = service.get_evolution(evolution_id)

    if not evolution:
        raise HTTPException(status_code=404, detail="Evolution not found")

    return EvolutionResponse(
        id=evolution.id,
        name=evolution.name,
        description=evolution.description,
        created_at=evolution.created_at,
        created_by=evolution.created_by,
        initial_population_size=evolution.initial_population_size,
        turns_per_interaction=evolution.turns_per_interaction,
        max_generations=evolution.max_generations,
        mutation_rate=evolution.mutation_rate,
        status=SimulationStatus(evolution.status),
        started_at=evolution.started_at,
        completed_at=evolution.completed_at,
        error_message=evolution.error_message,
        celery_task_id=evolution.celery_task_id,
        generations_completed=evolution.generations_completed,
        winner_strategy_id=evolution.winner_strategy_id,
        winner_strategy_name=evolution.winner_strategy_name,
        is_evolutionarily_stable=evolution.is_evolutionarily_stable,
    )


@router.get(
    "/evolution/{evolution_id}/results", response_model=EvolutionResultsResponse
)
async def get_evolution_results(
    evolution_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> EvolutionResultsResponse:
    """Get detailed evolution results including population history."""
    service = get_game_theory_service(db)
    evolution = service.get_evolution(evolution_id)

    if not evolution:
        raise HTTPException(status_code=404, detail="Evolution not found")

    if evolution.status != "completed":
        raise HTTPException(
            status_code=400, detail=f"Evolution is {evolution.status}, not completed"
        )

    # Parse population history
    history = []
    if evolution.population_history:
        for snapshot in evolution.population_history:
            history.append(
                PopulationSnapshot(
                    generation=snapshot.get("generation", 0),
                    populations=snapshot.get("populations", {}),
                )
            )

    return EvolutionResultsResponse(
        id=evolution.id,
        name=evolution.name,
        status=SimulationStatus(evolution.status),
        completed_at=evolution.completed_at,
        generations_completed=evolution.generations_completed,
        winner_strategy_name=evolution.winner_strategy_name,
        is_evolutionarily_stable=evolution.is_evolutionarily_stable,
        population_history=history,
        final_population=evolution.final_population or {},
    )


# =============================================================================
# Validation Endpoints
# =============================================================================


@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy(
    request: ValidationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> ValidationResponse:
    """
    Validate a strategy against Tit for Tat.

    Tests whether the strategy can coexist with TFT - a benchmark
    for production-ready configuration behavior.
    """
    service = get_game_theory_service(db)

    try:
        validation = service.validate_strategy(
            strategy_id=request.strategy_id,
            turns=request.turns,
            repetitions=request.repetitions,
            pass_threshold=request.pass_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ValidationResponse(
        id=validation.id,
        strategy_id=validation.strategy_id,
        strategy_name=validation.strategy_name,
        validated_at=validation.validated_at,
        turns=validation.turns,
        repetitions=validation.repetitions,
        passed=validation.passed,
        average_score=validation.average_score,
        cooperation_rate=validation.cooperation_rate,
        pass_threshold=validation.pass_threshold,
        assessment=validation.assessment,
        recommendation=validation.recommendation,
    )


# =============================================================================
# Analysis Endpoints
# =============================================================================


@router.post("/analyze", response_model=ConfigAnalysisResponse)
async def analyze_config(
    request: ConfigAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
) -> ConfigAnalysisResponse:
    """
    Analyze a resilience configuration using game theory.

    Tests the configuration against standard opponent strategies
    to determine its game-theoretic properties.
    """
    service = get_game_theory_service(db)

    result = service.analyze_current_config(
        utilization_target=request.utilization_target,
        cross_zone_borrowing=request.cross_zone_borrowing,
        sacrifice_willingness=request.sacrifice_willingness,
        defense_activation_threshold=request.defense_activation_threshold,
    )

    return ConfigAnalysisResponse(
        config_name=result["config_name"],
        matchup_results=result["matchup_results"],
        average_score=result["average_score"],
        cooperation_rate=result["cooperation_rate"],
        recommendation=result["recommendation"],
        strategy_classification=StrategyType(result["strategy_classification"]),
    )


@router.get("/summary")
async def get_game_theory_summary(
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """
    Get summary of game theory analysis status.

    Overview for the admin dashboard.
    """
    service = get_game_theory_service(db)

    strategies = service.list_strategies()
    tournaments = service.list_tournaments(limit=10)
    evolutions = service.list_evolutions(limit=10)

    # Calculate stats
    completed_tournaments = [t for t in tournaments if t.status == "completed"]
    completed_evolutions = [e for e in evolutions if e.status == "completed"]

    # Find most successful strategy
    best_strategy = None
    best_score = 0
    for s in strategies:
        if s.average_score and s.average_score > best_score:
            best_score = s.average_score
            best_strategy = s.name

    return {
        "total_strategies": len(strategies),
        "total_tournaments": len(tournaments),
        "completed_tournaments": len(completed_tournaments),
        "total_evolutions": len(evolutions),
        "completed_evolutions": len(completed_evolutions),
        "best_performing_strategy": best_strategy,
        "best_strategy_score": best_score,
        "recent_tournaments": [
            {
                "id": str(t.id),
                "name": t.name,
                "status": t.status,
                "winner": t.winner_strategy_name,
            }
            for t in tournaments[:5]
        ],
        "recent_evolutions": [
            {
                "id": str(e.id),
                "name": e.name,
                "status": e.status,
                "winner": e.winner_strategy_name,
            }
            for e in evolutions[:5]
        ],
    }
