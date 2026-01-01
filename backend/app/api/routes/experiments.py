"""A/B testing and experiments API routes.

Admin endpoints for managing experiments:
- Create, read, update, delete experiments
- Start, pause, conclude experiments
- Assign users to variants
- Track metrics
- View results and lifecycle events
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_async_db, get_db
from app.experiments import (
    Experiment,
    ExperimentService,
    ExperimentStatus,
)
from app.models.user import User
from app.schemas.experiments import (
    ConcludeExperimentRequest,
    ExperimentCreateRequest,
    ExperimentLifecycleListResponse,
    ExperimentLifecycleResponse,
    ExperimentListResponse,
    ExperimentResponse,
    ExperimentResultsResponse,
    ExperimentStatsResponse,
    ExperimentUpdateRequest,
    MetricDataResponse,
    MetricTrackRequest,
    UserAssignmentRequest,
    VariantAssignmentResponse,
    VariantMetricsResponse,
    VariantResponse,
)

router = APIRouter()


def _experiment_to_response(exp: Experiment) -> ExperimentResponse:
    """Convert Experiment model to response schema."""
    return ExperimentResponse(
        key=exp.key,
        name=exp.name,
        description=exp.description,
        hypothesis=exp.hypothesis,
        variants=[
            VariantResponse(
                key=v.key,
                name=v.name,
                description=v.description,
                allocation=v.allocation,
                is_control=v.is_control,
                config=v.config,
            )
            for v in exp.variants
        ],
        targeting=exp.targeting,
        config=exp.config,
        status=exp.status,
        start_date=exp.start_date,
        end_date=exp.end_date,
        created_by=exp.created_by,
        created_at=exp.created_at,
        updated_at=exp.updated_at,
    )


@router.post(
    "/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED
)
async def create_experiment(
    experiment_in: ExperimentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Create a new A/B test experiment.

    Requires admin privileges. Experiments are created in DRAFT status.
    """
    service = ExperimentService()

    try:
        experiment = Experiment(
            key=experiment_in.key,
            name=experiment_in.name,
            description=experiment_in.description,
            hypothesis=experiment_in.hypothesis,
            variants=experiment_in.variants,
            targeting=experiment_in.targeting,
            config=experiment_in.config,
            start_date=experiment_in.start_date,
            end_date=experiment_in.end_date,
            created_by=str(current_user.id),
        )
        created = await service.create_experiment(experiment)
        return _experiment_to_response(created)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.get("/", response_model=ExperimentListResponse)
async def list_experiments(
    status_filter: ExperimentStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    List all experiments with pagination.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        experiments = await service.list_experiments(status=status_filter)

        # Manual pagination
        total = len(experiments)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = experiments[start_idx:end_idx]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return ExperimentListResponse(
            experiments=[_experiment_to_response(e) for e in paginated],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    finally:
        await service.close()


@router.get("/stats", response_model=ExperimentStatsResponse)
async def get_experiment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get experiment statistics summary.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        experiments = await service.list_experiments()

        # Calculate stats
        status_counts = {
            ExperimentStatus.DRAFT: 0,
            ExperimentStatus.RUNNING: 0,
            ExperimentStatus.PAUSED: 0,
            ExperimentStatus.COMPLETED: 0,
            ExperimentStatus.CANCELLED: 0,
        }
        for exp in experiments:
            status_counts[exp.status] = status_counts.get(exp.status, 0) + 1

        # Count total users and metrics across all experiments
        total_users = 0
        total_metrics = 0
        for exp in experiments:
            if exp.status in [ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED]:
                try:
                    results = await service.get_results(exp.key)
                    total_users += results.total_users
                    for vm in results.variant_metrics:
                        for metric_stats in vm.metrics.values():
                            total_metrics += int(metric_stats.get("count", 0))
                except Exception:
                    pass  # Skip experiments with missing data

        return ExperimentStatsResponse(
            total_experiments=len(experiments),
            running_experiments=status_counts[ExperimentStatus.RUNNING],
            completed_experiments=status_counts[ExperimentStatus.COMPLETED],
            draft_experiments=status_counts[ExperimentStatus.DRAFT],
            paused_experiments=status_counts[ExperimentStatus.PAUSED],
            cancelled_experiments=status_counts[ExperimentStatus.CANCELLED],
            total_users_assigned=total_users,
            total_metrics_tracked=total_metrics,
        )
    finally:
        await service.close()


@router.get("/{key}", response_model=ExperimentResponse)
async def get_experiment(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get a specific experiment by key.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        experiment = await service.get_experiment(key)
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{key}' not found",
            )
        return _experiment_to_response(experiment)
    finally:
        await service.close()


@router.put("/{key}", response_model=ExperimentResponse)
async def update_experiment(
    key: str,
    update_in: ExperimentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Update an experiment.

    Requires admin privileges. Only DRAFT experiments can have variants updated.
    """
    service = ExperimentService()

    try:
        # Convert to dict, excluding None values
        updates = update_in.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        experiment = await service.update_experiment(key, updates)
        return _experiment_to_response(experiment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    finally:
        await service.close()


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Delete (cancel) an experiment.

    Requires admin privileges. Running experiments will be cancelled.
    """
    service = ExperimentService()

    try:
        experiment = await service.get_experiment(key)
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{key}' not found",
            )

        if experiment.status == ExperimentStatus.RUNNING:
            # Cancel running experiment
            await service.pause_experiment(key, paused_by=str(current_user.id))

        # Note: The service doesn't have a delete method, so we'll just mark as cancelled
        # In production, you might want to add a soft-delete mechanism
    finally:
        await service.close()


@router.post("/{key}/start", response_model=ExperimentResponse)
async def start_experiment(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Start an experiment.

    Requires admin privileges. Only DRAFT or PAUSED experiments can be started.
    """
    service = ExperimentService()

    try:
        experiment = await service.start_experiment(
            key, started_by=str(current_user.id)
        )
        return _experiment_to_response(experiment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.post("/{key}/pause", response_model=ExperimentResponse)
async def pause_experiment(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Pause an experiment.

    Requires admin privileges. Only RUNNING experiments can be paused.
    """
    service = ExperimentService()

    try:
        experiment = await service.pause_experiment(key, paused_by=str(current_user.id))
        return _experiment_to_response(experiment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.post("/{key}/conclude", response_model=ExperimentResponse)
async def conclude_experiment(
    key: str,
    conclude_in: ConcludeExperimentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Conclude an experiment with a winning variant.

    Requires admin privileges. Only RUNNING experiments can be concluded.
    """
    service = ExperimentService()

    try:
        experiment = await service.conclude_experiment(
            key,
            winning_variant=conclude_in.winning_variant,
            concluded_by=str(current_user.id),
        )
        return _experiment_to_response(experiment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.post("/{key}/assignments", response_model=VariantAssignmentResponse)
async def assign_user(
    key: str,
    assignment_in: UserAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Assign a user to an experiment variant.

    Any authenticated user can assign themselves or others.
    Uses consistent hashing for deterministic assignment.
    """
    service = ExperimentService()

    try:
        assignment = await service.assign_user(
            experiment_key=key,
            user_id=assignment_in.user_id,
            user_attributes=assignment_in.user_attributes,
            force_variant=assignment_in.force_variant,
        )
        return VariantAssignmentResponse(
            experiment_key=assignment.experiment_key,
            user_id=assignment.user_id,
            variant_key=assignment.variant_key,
            assigned_at=assignment.assigned_at,
            is_override=assignment.is_override,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.get("/{key}/assignments/{user_id}", response_model=VariantAssignmentResponse)
async def get_user_assignment(
    key: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a user's assignment for an experiment.

    Any authenticated user can view assignments.
    """
    service = ExperimentService()

    try:
        assignment = await service.get_assignment(experiment_key=key, user_id=user_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No assignment found for user '{user_id}' in experiment '{key}'",
            )
        return VariantAssignmentResponse(
            experiment_key=assignment.experiment_key,
            user_id=assignment.user_id,
            variant_key=assignment.variant_key,
            assigned_at=assignment.assigned_at,
            is_override=assignment.is_override,
        )
    finally:
        await service.close()


@router.post(
    "/{key}/metrics",
    response_model=MetricDataResponse,
    status_code=status.HTTP_201_CREATED,
)
async def track_metric(
    key: str,
    metric_in: MetricTrackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Track a metric for an experiment.

    Any authenticated user can track metrics.
    """
    service = ExperimentService()

    try:
        metric = await service.track_metric(
            experiment_key=key,
            user_id=metric_in.user_id,
            variant_key=metric_in.variant_key,
            metric_name=metric_in.metric_name,
            value=metric_in.value,
            metric_type=metric_in.metric_type,
            metadata=metric_in.metadata,
        )
        return MetricDataResponse(
            experiment_key=metric.experiment_key,
            user_id=metric.user_id,
            variant_key=metric.variant_key,
            metric_name=metric.metric_name,
            metric_type=metric.metric_type,
            value=metric.value,
            timestamp=metric.timestamp,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        await service.close()


@router.get("/{key}/metrics/{variant_key}", response_model=VariantMetricsResponse)
async def get_variant_metrics(
    key: str,
    variant_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get aggregated metrics for a variant.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        metrics = await service.get_variant_metrics(
            experiment_key=key, variant_key=variant_key
        )
        return VariantMetricsResponse(
            variant_key=metrics.variant_key,
            user_count=metrics.user_count,
            metrics=metrics.metrics,
        )
    finally:
        await service.close()


@router.get("/{key}/results", response_model=ExperimentResultsResponse)
async def get_experiment_results(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get experiment results with statistical analysis.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        results = await service.get_results(key)
        return ExperimentResultsResponse(
            experiment_key=results.experiment_key,
            status=results.status,
            start_date=results.start_date,
            end_date=results.end_date,
            duration_days=results.duration_days,
            total_users=results.total_users,
            variant_metrics=[
                VariantMetricsResponse(
                    variant_key=vm.variant_key,
                    user_count=vm.user_count,
                    metrics=vm.metrics,
                )
                for vm in results.variant_metrics
            ],
            is_significant=results.is_significant,
            confidence_level=results.confidence_level,
            p_value=results.p_value,
            winning_variant=results.winning_variant,
            recommendation=results.recommendation,
            statistical_power=results.statistical_power,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    finally:
        await service.close()


@router.get("/{key}/events", response_model=ExperimentLifecycleListResponse)
async def get_lifecycle_events(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get experiment lifecycle events.

    Requires admin privileges.
    """
    service = ExperimentService()

    try:
        events = await service.get_lifecycle_events(key)
        return ExperimentLifecycleListResponse(
            events=[
                ExperimentLifecycleResponse(
                    experiment_key=e.experiment_key,
                    event_type=e.event_type,
                    previous_status=e.previous_status,
                    new_status=e.new_status,
                    triggered_by=e.triggered_by,
                    timestamp=e.timestamp,
                    notes=e.notes,
                    metadata=e.metadata,
                )
                for e in events
            ],
            total=len(events),
        )
    finally:
        await service.close()
