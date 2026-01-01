"""Resilience API routes.

Tier 1 (Critical) endpoints:
- System health monitoring
- Crisis response activation/deactivation
- Fallback schedule management
- Load shedding control
- Vulnerability analysis
- Historical data retrieval

Tier 2 (Strategic) endpoints:
- Homeostasis and feedback loop monitoring
- Allostatic load calculation
- Scheduling zone management (blast radius)
- Zone borrowing and incidents
- Equilibrium analysis (Le Chatelier)
- Stress and compensation tracking
"""

import logging
import time
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.resilience import (
    FallbackActivation,
    ResilienceEvent,
    ResilienceEventType,
    ResilienceHealthCheck,
    SacrificeDecision,
    VulnerabilityRecord,
)
from app.models.user import User
from app.schemas.resilience import (
    AllostasisMetricsResponse,
    AssignmentSuggestionsResponse,
    BehavioralSignalResponse,
    BlastRadiusReportResponse,
    CentralityScore,
    CognitiveLoadAnalysis,
    CognitiveSessionEndResponse,
    CognitiveSessionStartResponse,
    CognitiveSessionStatusResponse,
    CollectivePreferenceResponse,
    CompensationResponse,
    ComprehensiveReportResponse,
    ContainmentSetResponse,
    CrisisActivationRequest,
    CrisisDeactivationRequest,
    CrisisResponse,
    CrisisSeverity,
    CrossTrainingRecommendationsResponse,
    DecisionCreateResponse,
    DecisionQueueResponse,
    DecisionResolveResponse,
    DefenseLevel,
    EquilibriumReportResponse,
    EquilibriumShiftResponse,
    EventHistoryItem,
    EventHistoryResponse,
    FacultyPreferencesResponse,
    FallbackActivationRequest,
    FallbackActivationResponse,
    FallbackDeactivationRequest,
    FallbackDeactivationResponse,
    FallbackInfo,
    FallbackListResponse,
    FallbackScenario,
    HealthCheckHistoryItem,
    HealthCheckHistoryResponse,
    HealthCheckResponse,
    HomeostasisCheckRequest,
    HomeostasisReport,
    HomeostasisStatusResponse,
    HubAnalysisResponse,
    HubDistributionReportResponse,
    HubProfileDetailResponse,
    HubProtectionPlanCreateResponse,
    HubStatusResponse,
    LoadSheddingLevel,
    LoadSheddingRequest,
    LoadSheddingStatus,
    MTFComplianceResponse,
    OverallStatus,
    PreferenceRecordResponse,
    PrioritizedDecisionsResponse,
    RedundancyStatus,
    StigmergyPatternsResponse,
    StigmergyStatusResponse,
    StressPredictionResponse,
    StressResolveResponse,
    StressResponse,
    SwapNetworkResponse,
    Tier2StatusResponse,
    Tier3StatusResponse,
    TopHubsResponse,
    TrailEvaporationResponse,
    UtilizationLevel,
    UtilizationMetrics,
    VulnerabilityReportResponse,
    ZoneAssignmentResponse,
    ZoneIncidentResponse,
    ZoneListResponse,
    ZoneResponse,
)
from app.services.resilience.homeostasis import (
    get_homeostasis_service,
)

router = APIRouter()


def get_resilience_service(db: Session):
    """Get or create ResilienceService instance."""
    from app.core.config import get_resilience_config
    from app.resilience.service import ResilienceService

    config = get_resilience_config()
    return ResilienceService(db=db, config=config)


def persist_health_check(db: Session, report, metrics_snapshot: dict = None):
    """Persist health check results to database."""
    health_check = ResilienceHealthCheck(
        timestamp=report.timestamp,
        overall_status=report.overall_status,
        utilization_rate=report.utilization.utilization_rate,
        utilization_level=report.utilization.level.value.upper(),
        buffer_remaining=report.utilization.buffer_remaining,
        defense_level=report.defense_level.name if report.defense_level else None,
        load_shedding_level=(
            report.load_shedding_level.name if report.load_shedding_level else None
        ),
        n1_pass=report.n1_pass,
        n2_pass=report.n2_pass,
        phase_transition_risk=report.phase_transition_risk,
        active_fallbacks=report.active_fallbacks,
        crisis_mode=getattr(report, "crisis_mode", False),
        immediate_actions=report.immediate_actions,
        watch_items=report.watch_items,
        metrics_snapshot=metrics_snapshot,
    )
    db.add(health_check)
    await db.commit()
    await db.refresh(health_check)
    return health_check


def persist_event(
    db: Session,
    event_type: str,
    severity: str = None,
    reason: str = None,
    triggered_by: str = None,
    previous_state: dict = None,
    new_state: dict = None,
    metadata: dict = None,
    health_check_id: UUID = None,
):
    """Persist resilience event to database."""
    event = ResilienceEvent(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        severity=severity,
        reason=reason,
        triggered_by=triggered_by,
        previous_state=previous_state,
        new_state=new_state,
        event_metadata=metadata,
        related_health_check_id=health_check_id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/health", response_model=HealthCheckResponse)
async def get_system_health(
    start_date: date | None = None,
    end_date: date | None = None,
    include_contingency: bool = False,
    persist: bool = True,
    max_faculty: int | None = Query(
        None, ge=1, description="Optional limit for faculty records"
    ),
    max_blocks: int | None = Query(
        None, ge=1, description="Optional limit for block records"
    ),
    max_assignments: int | None = Query(
        None, ge=1, description="Optional limit for assignment records"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get current system health status.

    Returns comprehensive health report including:
    - Utilization metrics (queuing theory)
    - Defense level (nuclear safety paradigm)
    - Redundancy status (N+2 rule)
    - Load shedding level (triage)
    - Active fallbacks
    - N-1/N-2 compliance
    - Recommendations

    Set `include_contingency=true` for full N-1/N-2 analysis (slower).
    Set `persist=false` to skip saving to database.

    Optional limits (max_faculty, max_blocks, max_assignments) can be set for
    performance tuning. By default, no limits are applied to ensure accurate
    resilience calculations.
    """
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person

    service = get_resilience_service(db)

    # Default date range: next 30 days
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data for analysis - apply optional limits if specified
    query_start = time.time()
    faculty_query = (
        db.query(Person).filter(Person.type == "faculty").order_by(Person.id)
    )
    if max_faculty:
        faculty_query = faculty_query.limit(max_faculty)
    faculty = faculty_query.all()

    blocks_query = (
        db.query(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Block.id)
    )
    if max_blocks:
        blocks_query = blocks_query.limit(max_blocks)
    blocks = blocks_query.all()

    assignments_query = (
        db.query(Assignment)
        .join(Block)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Assignment.id)
    )
    if max_assignments:
        assignments_query = assignments_query.limit(max_assignments)
    assignments = assignments_query.all()
    query_time = time.time() - query_start

    logger.info(
        "Health check data loaded: faculty=%d, blocks=%d, assignments=%d, "
        "date_range=%s to %s, query_time=%.3fs",
        len(faculty),
        len(blocks),
        len(assignments),
        start_date,
        end_date,
        query_time,
    )

    # Run health check
    report = service.check_health(
        faculty=faculty,
        blocks=blocks,
        assignments=assignments,
    )

    # Persist if requested
    if persist:
        persist_health_check(db, report)

    # Convert to response schema
    # Use getattr with defaults for fields that may not be present in all implementations
    util = report.utilization
    return HealthCheckResponse(
        timestamp=report.timestamp,
        overall_status=OverallStatus(report.overall_status),
        utilization=UtilizationMetrics(
            utilization_rate=util.utilization_rate,
            level=UtilizationLevel(util.level.value.upper()),
            buffer_remaining=util.buffer_remaining,
            wait_time_multiplier=getattr(util, "wait_time_multiplier", 1.0),
            safe_capacity=getattr(util, "safe_capacity", util.total_capacity),
            current_demand=getattr(util, "current_demand", util.current_assignments),
            theoretical_capacity=getattr(
                util, "theoretical_capacity", util.total_capacity
            ),
        ),
        defense_level=DefenseLevel(report.defense_level.name),
        redundancy_status=[
            RedundancyStatus(
                service=getattr(r, "service", r.function_name),
                status=r.status,
                available=getattr(r, "available", r.current_available),
                minimum_required=getattr(r, "minimum_required", r.required_minimum),
                buffer=getattr(r, "buffer", r.redundancy_level),
            )
            for r in report.redundancy_status
        ],
        load_shedding_level=LoadSheddingLevel(report.load_shedding_level.name),
        active_fallbacks=report.active_fallbacks,
        crisis_mode=service._crisis_mode,
        n1_pass=report.n1_pass,
        n2_pass=report.n2_pass,
        phase_transition_risk=report.phase_transition_risk,
        immediate_actions=report.immediate_actions,
        watch_items=report.watch_items,
    )


@router.post("/crisis/activate", response_model=CrisisResponse)
async def activate_crisis_response(
    request: CrisisActivationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Activate crisis response mode. Requires admin role.

    Severity levels:
    - minor: Yellow level - suspend optional activities
    - moderate: Orange level - automated reassignment, suspend admin/research
    - severe: Red level - service reduction, suspend education
    - critical: Black level - emergency response, essential services only
    """
    service = get_resilience_service(db)

    # Activate crisis
    result = service.activate_crisis_response(
        severity=request.severity.value,
        reason=request.reason,
    )

    # Persist event
    persist_event(
        db,
        event_type=ResilienceEventType.CRISIS_ACTIVATED.value,
        severity=request.severity.value,
        reason=request.reason,
        triggered_by=f"user:{current_user.id}",
        new_state=result,
    )

    return CrisisResponse(
        crisis_mode=result["crisis_mode"],
        severity=CrisisSeverity(request.severity.value),
        actions_taken=result["actions_taken"],
        load_shedding_level=LoadSheddingLevel(result["load_shedding_level"]),
    )


@router.post("/crisis/deactivate", response_model=CrisisResponse)
async def deactivate_crisis_response(
    request: CrisisDeactivationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Deactivate crisis response and begin recovery. Requires admin role.

    Recovery is gradual - services are restored in reverse sacrifice order.
    """
    service = get_resilience_service(db)

    # Deactivate crisis
    result = service.deactivate_crisis_response(reason=request.reason)

    # Persist event
    persist_event(
        db,
        event_type=ResilienceEventType.CRISIS_DEACTIVATED.value,
        reason=request.reason,
        triggered_by=f"user:{current_user.id}",
        new_state=result,
    )

    return CrisisResponse(
        crisis_mode=result["crisis_mode"],
        actions_taken=[],
        load_shedding_level=LoadSheddingLevel.NORMAL,
        recovery_plan=result.get("recovery_plan", []),
    )


@router.get("/fallbacks", response_model=FallbackListResponse)
async def list_fallbacks(
    db: AsyncSession = Depends(get_async_db),
):
    """
    List all available fallback schedules.

    Shows which fallbacks are precomputed and ready for activation.
    """
    service = get_resilience_service(db)

    fallbacks = []
    active_count = 0

    for scenario in FallbackScenario:
        # Get info from service
        fallback_schedule = service.fallback.get_fallback(scenario.value)
        is_active = fallback_schedule is not None and fallback_schedule.is_active

        if is_active:
            active_count += 1

        fallbacks.append(
            FallbackInfo(
                scenario=scenario,
                description=_get_scenario_description(scenario),
                is_active=is_active,
                is_precomputed=fallback_schedule is not None,
                assignments_count=(
                    len(fallback_schedule.assignments) if fallback_schedule else None
                ),
                coverage_rate=(
                    fallback_schedule.coverage_rate if fallback_schedule else None
                ),
                services_reduced=(
                    fallback_schedule.services_reduced if fallback_schedule else []
                ),
                assumptions=fallback_schedule.assumptions if fallback_schedule else [],
                activation_count=(
                    fallback_schedule.activation_count if fallback_schedule else 0
                ),
            )
        )

    return FallbackListResponse(
        fallbacks=fallbacks,
        active_count=active_count,
    )


@router.post("/fallbacks/activate", response_model=FallbackActivationResponse)
async def activate_fallback(
    request: FallbackActivationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Activate a pre-computed fallback schedule. Requires admin role.

    This instantly switches to the fallback schedule without recomputation.
    """
    service = get_resilience_service(db)

    # Map schema enum to service enum
    from app.resilience.static_stability import FallbackScenario as ServiceScenario

    scenario_map = {
        FallbackScenario.SINGLE_FACULTY_LOSS: ServiceScenario.SINGLE_FACULTY_LOSS,
        FallbackScenario.DOUBLE_FACULTY_LOSS: ServiceScenario.DOUBLE_FACULTY_LOSS,
        FallbackScenario.PCS_SEASON_50_PERCENT: ServiceScenario.PCS_SEASON_50_PERCENT,
        FallbackScenario.HOLIDAY_SKELETON: ServiceScenario.HOLIDAY_SKELETON,
        FallbackScenario.PANDEMIC_ESSENTIAL: ServiceScenario.PANDEMIC_ESSENTIAL,
        FallbackScenario.MASS_CASUALTY: ServiceScenario.MASS_CASUALTY,
        FallbackScenario.WEATHER_EMERGENCY: ServiceScenario.WEATHER_EMERGENCY,
    }

    service_scenario = scenario_map.get(request.scenario)
    if not service_scenario:
        raise HTTPException(
            status_code=400, detail=f"Unknown scenario: {request.scenario}"
        )

    fallback = service.activate_fallback(
        scenario=service_scenario,
        approved_by=str(current_user.id),
    )

    if not fallback:
        raise HTTPException(
            status_code=404,
            detail=f"Fallback schedule for '{request.scenario.value}' not found or not precomputed",
        )

    # Persist activation
    activation = FallbackActivation(
        scenario=request.scenario.value,
        scenario_description=_get_scenario_description(request.scenario),
        activated_by=str(current_user.id),
        activation_reason=request.reason,
        assignments_count=len(fallback.assignments),
        coverage_rate=fallback.coverage_rate,
        services_reduced=fallback.services_reduced,
        assumptions=fallback.assumptions,
    )
    db.add(activation)

    # Persist event
    persist_event(
        db,
        event_type=ResilienceEventType.FALLBACK_ACTIVATED.value,
        reason=request.reason,
        triggered_by=f"user:{current_user.id}",
        new_state={"scenario": request.scenario.value},
    )

    await db.commit()

    return FallbackActivationResponse(
        success=True,
        scenario=request.scenario,
        assignments_count=len(fallback.assignments),
        coverage_rate=fallback.coverage_rate,
        services_reduced=fallback.services_reduced,
        message=f"Fallback '{request.scenario.value}' activated successfully",
    )


@router.post("/fallbacks/deactivate", response_model=FallbackDeactivationResponse)
async def deactivate_fallback(
    request: FallbackDeactivationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Deactivate a fallback schedule and return to normal operations.
    Requires admin role.
    """
    service = get_resilience_service(db)

    # Map and deactivate
    from app.resilience.static_stability import FallbackScenario as ServiceScenario

    scenario_map = {
        FallbackScenario.SINGLE_FACULTY_LOSS: ServiceScenario.SINGLE_FACULTY_LOSS,
        FallbackScenario.DOUBLE_FACULTY_LOSS: ServiceScenario.DOUBLE_FACULTY_LOSS,
        FallbackScenario.PCS_SEASON_50_PERCENT: ServiceScenario.PCS_SEASON_50_PERCENT,
        FallbackScenario.HOLIDAY_SKELETON: ServiceScenario.HOLIDAY_SKELETON,
        FallbackScenario.PANDEMIC_ESSENTIAL: ServiceScenario.PANDEMIC_ESSENTIAL,
        FallbackScenario.MASS_CASUALTY: ServiceScenario.MASS_CASUALTY,
        FallbackScenario.WEATHER_EMERGENCY: ServiceScenario.WEATHER_EMERGENCY,
    }

    service_scenario = scenario_map.get(request.scenario)
    service.fallback.deactivate_fallback(service_scenario)

    # Update activation record
    activation = (
        db.query(FallbackActivation)
        .filter(
            FallbackActivation.scenario == request.scenario.value,
            FallbackActivation.deactivated_at.is_(None),
        )
        .first()
    )

    if activation:
        activation.deactivated_at = datetime.utcnow()
        activation.deactivated_by = str(current_user.id)
        activation.deactivation_reason = request.reason

    # Persist event
    persist_event(
        db,
        event_type=ResilienceEventType.FALLBACK_DEACTIVATED.value,
        reason=request.reason,
        triggered_by=f"user:{current_user.id}",
        new_state={"scenario": request.scenario.value},
    )

    await db.commit()

    return {
        "success": True,
        "message": f"Fallback '{request.scenario.value}' deactivated",
    }


@router.get("/load-shedding", response_model=LoadSheddingStatus)
async def get_load_shedding_status(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get current load shedding status.

    Shows which activities are suspended and which are protected.
    """
    service = get_resilience_service(db)
    status = service.sacrifice.get_status()

    return LoadSheddingStatus(
        level=LoadSheddingLevel(status.level.name),
        activities_suspended=status.activities_suspended,
        activities_protected=status.activities_protected,
        capacity_available=status.capacity_available,
        capacity_demand=status.capacity_demand,
    )


@router.post("/load-shedding", response_model=LoadSheddingStatus)
async def set_load_shedding_level(
    request: LoadSheddingRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Manually set load shedding level. Requires admin role.

    This overrides automatic load shedding decisions.
    """
    service = get_resilience_service(db)

    # Map schema enum to service enum
    from app.resilience.sacrifice_hierarchy import LoadSheddingLevel as ServiceLevel

    level_map = {
        LoadSheddingLevel.NORMAL: ServiceLevel.NORMAL,
        LoadSheddingLevel.YELLOW: ServiceLevel.YELLOW,
        LoadSheddingLevel.ORANGE: ServiceLevel.ORANGE,
        LoadSheddingLevel.RED: ServiceLevel.RED,
        LoadSheddingLevel.BLACK: ServiceLevel.BLACK,
        LoadSheddingLevel.CRITICAL: ServiceLevel.CRITICAL,
    }

    previous_level = service.sacrifice.current_level

    # Activate new level
    service.sacrifice.activate_level(
        level_map[request.level],
        reason=request.reason,
    )

    status = service.sacrifice.get_status()

    # Persist sacrifice decision
    decision = SacrificeDecision(
        from_level=previous_level.name,
        to_level=request.level.value,
        reason=request.reason,
        activities_suspended=status.activities_suspended,
        activities_protected=status.activities_protected,
        approved_by=str(current_user.id),
        approval_method="manual",
    )
    db.add(decision)

    # Persist event
    persist_event(
        db,
        event_type=ResilienceEventType.LOAD_SHEDDING_ACTIVATED.value,
        reason=request.reason,
        triggered_by=f"user:{current_user.id}",
        previous_state={"level": previous_level.name},
        new_state={"level": request.level.value},
    )

    await db.commit()

    return LoadSheddingStatus(
        level=request.level,
        activities_suspended=status.activities_suspended,
        activities_protected=status.activities_protected,
        capacity_available=status.capacity_available,
        capacity_demand=status.capacity_demand,
    )


def get_contingency_service(db: Session):
    """Get or create ContingencyService instance with dependency injection."""
    from app.services.resilience.contingency import ContingencyService

    return ContingencyService(db=db)


@router.get("/vulnerability", response_model=VulnerabilityReportResponse)
async def get_vulnerability_report(
    start_date: date | None = None,
    end_date: date | None = None,
    include_n2: bool = Query(True, description="Include N-2 analysis (more expensive)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Run full N-1/N-2 vulnerability analysis.

    This endpoint uses the ContingencyService to perform efficient N-1/N-2
    contingency analysis with optimized simulation loops.

    The analysis implements power grid reliability principles:
    - N-1: System must survive loss of any single faculty member
    - N-2: System must survive loss of any two faculty members (optional)

    Args:
        start_date: Start of analysis period (defaults to today)
        end_date: End of analysis period (defaults to 30 days from start)
        include_n2: Whether to include N-2 pair analysis (default True)
    """
    contingency_service = get_contingency_service(db)

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Run contingency analysis using the service
    analysis_start = time.time()
    result = contingency_service.analyze_contingency(
        start_date=start_date,
        end_date=end_date,
        include_n2=include_n2,
    )
    analysis_time = time.time() - analysis_start

    logger.info(
        "Vulnerability analysis completed: n1_pass=%s, n2_pass=%s, "
        "vulnerabilities=%d, fatal_pairs=%d, duration=%.3fs",
        result.n1_pass,
        result.n2_pass,
        len(result.n1_vulnerabilities),
        len(result.n2_fatal_pairs),
        analysis_time,
    )

    # Persist vulnerability record
    vuln_record = VulnerabilityRecord(
        period_start=datetime.combine(start_date, datetime.min.time()),
        period_end=datetime.combine(end_date, datetime.min.time()),
        faculty_count=len(result.n1_simulations),
        block_count=(
            len(set(b for s in result.n1_simulations for b in s.uncovered_blocks))
            if result.n1_simulations
            else 0
        ),
        n1_pass=result.n1_pass,
        n2_pass=result.n2_pass,
        phase_transition_risk=result.phase_transition_risk,
        n1_vulnerabilities=[v.to_dict() for v in result.n1_vulnerabilities[:10]],
        n2_fatal_pairs=[p.to_dict() for p in result.n2_fatal_pairs[:10]],
        most_critical_faculty=[str(fid) for fid in result.most_critical_faculty[:5]],
        recommended_actions=result.recommended_actions,
    )
    db.add(vuln_record)
    await db.commit()

    return VulnerabilityReportResponse(
        analyzed_at=result.analyzed_at,
        period_start=start_date,
        period_end=end_date,
        n1_pass=result.n1_pass,
        n2_pass=result.n2_pass,
        phase_transition_risk=result.phase_transition_risk,
        n1_vulnerabilities=[
            {
                "faculty_id": str(v.faculty_id),
                "affected_blocks": v.affected_blocks,
                "severity": v.severity,
            }
            for v in result.n1_vulnerabilities[:10]
        ],
        n2_fatal_pairs=[
            {
                "faculty1_id": str(p.faculty1_id),
                "faculty2_id": str(p.faculty2_id),
            }
            for p in result.n2_fatal_pairs[:10]
        ],
        most_critical_faculty=[
            CentralityScore(
                faculty_id=c.faculty_id,
                faculty_name=c.faculty_name,
                centrality_score=c.centrality_score,
                services_covered=c.services_covered,
                unique_coverage_slots=c.unique_coverage_slots,
                replacement_difficulty=c.replacement_difficulty,
                risk_level=_centrality_to_risk(c.centrality_score),
            )
            for c in result.centrality_scores[:10]
        ],
        recommended_actions=result.recommended_actions,
    )


@router.get("/report", response_model=ComprehensiveReportResponse)
async def get_comprehensive_report(
    start_date: date | None = None,
    end_date: date | None = None,
    max_faculty: int | None = Query(
        None, ge=1, description="Optional limit for faculty records"
    ),
    max_blocks: int | None = Query(
        None, ge=1, description="Optional limit for block records"
    ),
    max_assignments: int | None = Query(
        None, ge=1, description="Optional limit for assignment records"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Generate comprehensive resilience report.

    Combines all component reports into a single document
    suitable for leadership review or audit.

    Optional limits (max_faculty, max_blocks, max_assignments) can be set for
    performance tuning. By default, no limits are applied to ensure accurate
    reporting.
    """
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person

    service = get_resilience_service(db)

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data - apply optional limits if specified
    query_start = time.time()
    faculty_query = (
        db.query(Person).filter(Person.type == "faculty").order_by(Person.id)
    )
    if max_faculty:
        faculty_query = faculty_query.limit(max_faculty)
    faculty = faculty_query.all()

    blocks_query = (
        db.query(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Block.id)
    )
    if max_blocks:
        blocks_query = blocks_query.limit(max_blocks)
    blocks = blocks_query.all()

    assignments_query = (
        db.query(Assignment)
        .join(Block)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Assignment.id)
    )
    if max_assignments:
        assignments_query = assignments_query.limit(max_assignments)
    assignments = assignments_query.all()
    query_time = time.time() - query_start

    logger.info(
        "Comprehensive report data loaded: faculty=%d, blocks=%d, assignments=%d, "
        "date_range=%s to %s, query_time=%.3fs",
        len(faculty),
        len(blocks),
        len(assignments),
        start_date,
        end_date,
        query_time,
    )

    report = service.get_comprehensive_report(faculty, blocks, assignments)

    return ComprehensiveReportResponse(
        generated_at=datetime.fromisoformat(report["generated_at"]),
        overall_status=OverallStatus(report["overall_status"]),
        summary=report["summary"],
        immediate_actions=report["immediate_actions"],
        watch_items=report["watch_items"],
        components=report["components"],
    )


@router.get("/history/health", response_model=HealthCheckHistoryResponse)
async def get_health_check_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: OverallStatus | None = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get historical health check records.

    Use for trend analysis and pattern detection.
    """
    query = db.query(ResilienceHealthCheck)

    if status:
        query = query.filter(ResilienceHealthCheck.overall_status == status.value)

    total = query.count()

    items = (
        query.order_by(desc(ResilienceHealthCheck.timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return HealthCheckHistoryResponse(
        items=[
            HealthCheckHistoryItem(
                id=item.id,
                timestamp=item.timestamp,
                overall_status=OverallStatus(item.overall_status),
                utilization_rate=item.utilization_rate,
                utilization_level=UtilizationLevel(item.utilization_level),
                defense_level=(
                    DefenseLevel(item.defense_level) if item.defense_level else None
                ),
                n1_pass=item.n1_pass,
                n2_pass=item.n2_pass,
                crisis_mode=item.crisis_mode,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/history/events", response_model=EventHistoryResponse)
async def get_event_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: str | None = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get historical resilience events.

    Use for audit trail and incident review.
    """
    query = db.query(ResilienceEvent)

    if event_type:
        query = query.filter(ResilienceEvent.event_type == event_type)

    total = query.count()

    items = (
        query.order_by(desc(ResilienceEvent.timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return EventHistoryResponse(
        items=[
            EventHistoryItem(
                id=item.id,
                timestamp=item.timestamp,
                event_type=item.event_type,
                severity=item.severity,
                reason=item.reason,
                triggered_by=item.triggered_by,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# Helper functions


def _get_scenario_description(scenario: FallbackScenario) -> str:
    """Get human-readable description for a fallback scenario."""
    descriptions = {
        FallbackScenario.SINGLE_FACULTY_LOSS: "Coverage for loss of any single faculty member",
        FallbackScenario.DOUBLE_FACULTY_LOSS: "Coverage for simultaneous loss of two faculty members",
        FallbackScenario.PCS_SEASON_50_PERCENT: "Reduced operations during PCS season (~50% capacity)",
        FallbackScenario.HOLIDAY_SKELETON: "Minimal coverage for holiday periods",
        FallbackScenario.PANDEMIC_ESSENTIAL: "Essential services only during pandemic conditions",
        FallbackScenario.MASS_CASUALTY: "All-hands emergency response configuration",
        FallbackScenario.WEATHER_EMERGENCY: "Weather emergency response configuration",
    }
    return descriptions.get(scenario, "Unknown scenario")


def _centrality_to_risk(score: float) -> str:
    """Convert centrality score to risk level."""
    if score >= 0.8:
        return "critical"
    elif score >= 0.6:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


# =============================================================================
# MTF Compliance / Iron Dome Endpoint
# =============================================================================


@router.get("/mtf-compliance", response_model=MTFComplianceResponse)
async def get_mtf_compliance(
    check_circuit_breaker: bool = Query(
        True, description="Check circuit breaker status"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get MTF (Military Treatment Facility) compliance status using the Iron Dome service.

    Returns DRRS readiness ratings, circuit breaker status, and compliance documentation.

    This endpoint translates scheduling system metrics into military reporting format:
    - DRRS C-ratings (C1-C5)
    - Personnel P-ratings (P1-P4)
    - Capability S-ratings (S1-S4)
    - Circuit breaker status (tripped/locked operations)
    """
    from datetime import timedelta

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.resilience.mtf_compliance import IronDomeService

    # Default date range: next 30 days
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    # Load data for analysis
    faculty = (await db.execute(select(Person).where(Person.type == "faculty"))).scalars().all()
    blocks = (
        (await db.execute(select(Block).where(Block.date >= start_date, Block.date <= end_date))).scalars().all()
    )
    assignments = (
        db.query(Assignment)
        .join(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .all()
    )

    # Get resilience service for current system state
    resilience_service = get_resilience_service(db)

    # Run health check to get current metrics
    health = resilience_service.check_health(
        faculty=faculty,
        blocks=blocks,
        assignments=assignments,
    )

    # Initialize Iron Dome service
    iron_dome = IronDomeService()

    # Map load shedding level
    from app.resilience.sacrifice_hierarchy import LoadSheddingLevel as ServiceLevel

    level_map = {
        ServiceLevel.NORMAL: "NORMAL",
        ServiceLevel.YELLOW: "YELLOW",
        ServiceLevel.ORANGE: "ORANGE",
        ServiceLevel.RED: "RED",
        ServiceLevel.BLACK: "BLACK",
        ServiceLevel.CRITICAL: "CRITICAL",
    }
    load_level_str = level_map.get(health.load_shedding_level, "NORMAL")

    # Map equilibrium state - use a default if not available
    equilibrium_state = "STABLE"
    try:
        tier2_status = resilience_service.get_tier2_status()
        equilibrium_state = tier2_status.get("equilibrium", {}).get("state", "STABLE")
    except Exception:
        pass

    # Calculate required faculty (based on blocks)
    required_faculty = max(len(blocks) // 2, len(faculty))

    # Count overloaded faculty (faculty with high assignment counts)
    assignment_counts = {}
    for a in assignments:
        if a.person_id:
            assignment_counts[a.person_id] = assignment_counts.get(a.person_id, 0) + 1
    avg_assignments = sum(assignment_counts.values()) / max(len(assignment_counts), 1)
    overloaded = sum(1 for c in assignment_counts.values() if c > avg_assignments * 1.5)

    # Perform readiness assessment
    from app.schemas.resilience import EquilibriumState
    from app.schemas.resilience import LoadSheddingLevel as SchemaLoadLevel

    schema_level = SchemaLoadLevel[load_level_str]
    schema_equilibrium = EquilibriumState[equilibrium_state.upper().replace("-", "_")]

    assessment = iron_dome.assess_readiness(
        load_shedding_level=schema_level,
        equilibrium_state=schema_equilibrium,
        n1_pass=health.n1_pass,
        n2_pass=health.n2_pass,
        coverage_rate=health.utilization.utilization_rate,
        available_faculty=len(faculty),
        required_faculty=required_faculty,
        overloaded_faculty_count=overloaded,
    )

    # Check circuit breaker if requested
    circuit_breaker_info = None
    if check_circuit_breaker:
        # Get additional metrics for circuit breaker
        avg_allostatic_load = 50.0  # Default
        volatility_level = "low"
        compensation_debt = 0.0
        try:
            tier2 = resilience_service.get_tier2_status()
            avg_allostatic_load = tier2.get("homeostasis", {}).get(
                "average_allostatic_load", 50.0
            )
            compensation_debt = tier2.get("equilibrium", {}).get(
                "compensation_debt", 0.0
            )
        except Exception:
            pass

        cb_check = iron_dome.check_circuit_breaker(
            n1_pass=health.n1_pass,
            n2_pass=health.n2_pass,
            coverage_rate=health.utilization.utilization_rate,
            average_allostatic_load=avg_allostatic_load,
            volatility_level=volatility_level,
            compensation_debt=compensation_debt,
        )

        circuit_breaker_info = {
            "state": cb_check.state,
            "tripped": cb_check.tripped,
            "trigger": cb_check.trigger,
            "trigger_details": cb_check.trigger_details,
            "locked_operations": cb_check.locked_operations,
            "override_active": cb_check.override_active,
        }

    # Map severity based on DRRS rating
    severity_map = {
        "C1": "healthy",
        "C2": "healthy",
        "C3": "warning",
        "C4": "critical",
        "C5": "emergency",
    }

    # Map iron dome status based on circuit breaker
    iron_dome_status = "green"
    if (
        circuit_breaker_info and circuit_breaker_info["tripped"]
    ) or assessment.overall_rating in ["C4", "C5"]:
        iron_dome_status = "red"
    elif assessment.overall_rating in ["C3"]:
        iron_dome_status = "yellow"

    return {
        "drrs_category": assessment.overall_rating,
        "mission_capability": assessment.overall_capability,
        "personnel_rating": assessment.personnel_rating,
        "capability_rating": assessment.capability_rating,
        "circuit_breaker": circuit_breaker_info,
        "executive_summary": assessment.executive_summary,
        "deficiencies": assessment.deficiencies,
        "mfrs_generated": len(iron_dome.mfr_history),
        "rffs_generated": len(iron_dome.rff_history),
        "iron_dome_status": iron_dome_status,
        "severity": severity_map.get(assessment.overall_rating, "warning"),
    }


# =============================================================================
# Tier 2: Homeostasis Endpoints
# =============================================================================


@router.get("/tier2/homeostasis", response_model=HomeostasisStatusResponse)
async def get_homeostasis_status(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get current homeostasis status including feedback loops and allostatic load.

    Returns status of all feedback loops and detected positive feedback risks.
    """
    from app.schemas.resilience import AllostasisState as SchemaAllostasisState
    from app.schemas.resilience import DeviationSeverity as SchemaDeviationSeverity
    from app.schemas.resilience import (
        FeedbackLoopStatus,
        HomeostasisStatusResponse,
        PositiveFeedbackRiskInfo,
        SetpointInfo,
    )

    service = get_resilience_service(db)

    # Check homeostasis with default metrics
    status = service.homeostasis.get_status()

    # Build feedback loop statuses
    loop_statuses = []
    for loop in service.homeostasis.feedback_loops.values():
        current_value = None
        deviation = None
        if loop.value_history:
            current_value = loop.value_history[-1][1]
            deviation, _ = loop.setpoint.check_deviation(current_value)

        loop_statuses.append(
            FeedbackLoopStatus(
                loop_name=loop.name,
                setpoint=SetpointInfo(
                    name=loop.setpoint.name,
                    description=loop.setpoint.description,
                    target_value=loop.setpoint.target_value,
                    tolerance=loop.setpoint.tolerance,
                    unit=loop.setpoint.unit,
                    is_critical=loop.setpoint.is_critical,
                ),
                current_value=current_value,
                deviation=deviation,
                deviation_severity=SchemaDeviationSeverity.NONE,
                consecutive_deviations=loop.consecutive_deviations,
                trend_direction=loop.get_trend(),
                is_improving=loop.is_improving(),
                last_checked=loop.last_checked,
                total_corrections=loop.total_corrections,
            )
        )

    # Build positive feedback risks
    risk_infos = [
        PositiveFeedbackRiskInfo(
            id=risk.id,
            name=risk.name,
            description=risk.description,
            detected_at=risk.detected_at,
            trigger=risk.trigger,
            amplification=risk.amplification,
            consequence=risk.consequence,
            evidence=risk.evidence,
            confidence=risk.confidence,
            severity=SchemaDeviationSeverity(risk.severity.value),
            intervention=risk.intervention,
            urgency=risk.urgency,
        )
        for risk in service.homeostasis.positive_feedback_risks
    ]

    return HomeostasisStatusResponse(
        timestamp=status.timestamp,
        overall_state=SchemaAllostasisState(status.overall_state.value),
        feedback_loops_healthy=status.feedback_loops_healthy,
        feedback_loops_deviating=status.feedback_loops_deviating,
        active_corrections=status.active_corrections,
        positive_feedback_risks=status.positive_feedback_risks,
        average_allostatic_load=status.average_allostatic_load,
        recommendations=status.recommendations,
        feedback_loops=loop_statuses,
        positive_risks=risk_infos,
    )


@router.post("/tier2/homeostasis/check", response_model=HomeostasisReport)
async def check_homeostasis(
    request: HomeostasisCheckRequest,
    db: AsyncSession = Depends(get_async_db),
) -> HomeostasisReport:
    """
    Check homeostasis with provided metrics.

    Metrics dict should contain setpoint names and current values:
    {"coverage_rate": 0.92, "faculty_utilization": 0.78}

    Available setpoints:
    - coverage_rate: Target 0.95, tolerance 0.05
    - faculty_utilization: Target 0.75, tolerance 0.10
    - workload_balance: Target 0.15 (std_dev), tolerance 0.05
    - schedule_stability: Target 0.95, tolerance 0.05
    - acgme_compliance: Target 1.0, tolerance 0.02

    Returns a HomeostasisReport with feedback loop states and recommendations.
    """
    homeostasis_service = get_homeostasis_service(db)
    return homeostasis_service.check_homeostasis(request.metrics)


@router.post("/tier2/allostasis/calculate", response_model=AllostasisMetricsResponse)
async def calculate_allostatic_load(
    entity_id: UUID,
    entity_type: str,
    stress_factors: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Calculate allostatic load for a faculty member or system.

    stress_factors should contain:
    - consecutive_weekend_calls: int
    - nights_past_month: int
    - schedule_changes_absorbed: int
    - holidays_worked_this_year: int
    - overtime_hours_month: float
    - coverage_gap_responses: int
    - cross_coverage_events: int
    """
    from app.schemas.resilience import AllostasisMetricsResponse
    from app.schemas.resilience import AllostasisState as SchemaState

    service = get_resilience_service(db)
    metrics = service.calculate_allostatic_load(entity_id, entity_type, stress_factors)

    return AllostasisMetricsResponse(
        entity_id=metrics.entity_id,
        entity_type=metrics.entity_type,
        calculated_at=metrics.calculated_at,
        consecutive_weekend_calls=metrics.consecutive_weekend_calls,
        nights_past_month=metrics.nights_past_month,
        schedule_changes_absorbed=metrics.schedule_changes_absorbed,
        holidays_worked_this_year=metrics.holidays_worked_this_year,
        overtime_hours_month=metrics.overtime_hours_month,
        coverage_gap_responses=metrics.coverage_gap_responses,
        cross_coverage_events=metrics.cross_coverage_events,
        acute_stress_score=metrics.acute_stress_score,
        chronic_stress_score=metrics.chronic_stress_score,
        total_allostatic_load=metrics.total_allostatic_load,
        state=SchemaState(metrics.state.value),
        risk_level=metrics.risk_level,
    )


# =============================================================================
# Tier 2: Blast Radius / Zone Endpoints
# =============================================================================


@router.get("/tier2/zones", response_model=ZoneListResponse)
async def list_zones(
    db: AsyncSession = Depends(get_async_db),
):
    """
    List all scheduling zones and their current status.
    """
    from app.schemas.resilience import ContainmentLevel as SchemaContainment
    from app.schemas.resilience import (
        ZoneResponse,
    )
    from app.schemas.resilience import ZoneStatus as SchemaZoneStatus
    from app.schemas.resilience import ZoneType as SchemaZoneType

    service = get_resilience_service(db)
    zones = []

    for zone in service.blast_radius.zones.values():
        zones.append(
            ZoneResponse(
                id=zone.id,
                name=zone.name,
                zone_type=SchemaZoneType(zone.zone_type.value),
                description=zone.description,
                services=zone.services,
                minimum_coverage=zone.minimum_coverage,
                optimal_coverage=zone.optimal_coverage,
                priority=zone.priority,
                status=SchemaZoneStatus(zone.status.value),
                containment_level=SchemaContainment(zone.containment_level.value),
                borrowing_limit=zone.borrowing_limit,
                lending_limit=zone.lending_limit,
                is_active=True,
            )
        )

    return {"zones": zones, "total": len(zones)}


@router.get("/tier2/zones/report", response_model=BlastRadiusReportResponse)
async def get_blast_radius_report(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get comprehensive blast radius containment report.

    Returns health status of all zones and overall containment status.
    """
    from app.schemas.resilience import (
        BlastRadiusReportResponse,
    )
    from app.schemas.resilience import ContainmentLevel as SchemaContainment
    from app.schemas.resilience import ZoneHealthReport as SchemaZoneHealth
    from app.schemas.resilience import ZoneStatus as SchemaZoneStatus
    from app.schemas.resilience import ZoneType as SchemaZoneType

    service = get_resilience_service(db)
    report = service.check_all_zones()

    zone_reports = [
        SchemaZoneHealth(
            zone_id=zr.zone_id,
            zone_name=zr.zone_name,
            zone_type=SchemaZoneType(zr.zone_type.value),
            checked_at=zr.checked_at,
            status=SchemaZoneStatus(zr.status.value),
            containment_level=SchemaContainment(zr.containment_level.value),
            is_self_sufficient=zr.is_self_sufficient,
            has_surplus=zr.has_surplus,
            available_faculty=zr.available_faculty,
            minimum_required=zr.minimum_required,
            optimal_required=zr.optimal_required,
            capacity_ratio=zr.capacity_ratio,
            faculty_borrowed=zr.faculty_borrowed,
            faculty_lent=zr.faculty_lent,
            net_borrowing=zr.net_borrowing,
            active_incidents=zr.active_incidents,
            services_affected=zr.services_affected,
            recommendations=zr.recommendations,
        )
        for zr in report.zone_reports
    ]

    return BlastRadiusReportResponse(
        generated_at=report.generated_at,
        total_zones=report.total_zones,
        zones_healthy=report.zones_healthy,
        zones_degraded=report.zones_degraded,
        zones_critical=report.zones_critical,
        containment_active=report.containment_active,
        containment_level=SchemaContainment(report.containment_level.value),
        zones_isolated=report.zones_isolated,
        active_borrowing_requests=report.active_borrowing_requests,
        pending_borrowing_requests=report.pending_borrowing_requests,
        zone_reports=zone_reports,
        recommendations=report.recommendations,
    )


@router.post("/tier2/zones", response_model=ZoneResponse)
async def create_zone(
    name: str,
    zone_type: str,
    description: str = "",
    services: list[str] = None,
    minimum_coverage: int = 1,
    optimal_coverage: int = 2,
    priority: int = 5,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new scheduling zone. Requires authentication.
    """
    from app.resilience.blast_radius import ZoneType
    from app.schemas.resilience import ContainmentLevel, ZoneResponse, ZoneStatus
    from app.schemas.resilience import ZoneType as SchemaZoneType

    type_map = {
        "inpatient": ZoneType.INPATIENT,
        "outpatient": ZoneType.OUTPATIENT,
        "education": ZoneType.EDUCATION,
        "research": ZoneType.RESEARCH,
        "admin": ZoneType.ADMINISTRATIVE,
        "on_call": ZoneType.ON_CALL,
    }

    service = get_resilience_service(db)
    zone = service.create_zone(
        name=name,
        zone_type=type_map.get(zone_type, ZoneType.INPATIENT),
        description=description,
        services=services or [],
        minimum_coverage=minimum_coverage,
        optimal_coverage=optimal_coverage,
        priority=priority,
    )

    return ZoneResponse(
        id=zone.id,
        name=zone.name,
        zone_type=SchemaZoneType(zone.zone_type.value),
        description=zone.description,
        services=zone.services,
        minimum_coverage=zone.minimum_coverage,
        optimal_coverage=zone.optimal_coverage,
        priority=zone.priority,
        status=ZoneStatus.GREEN,
        containment_level=ContainmentLevel.NONE,
        borrowing_limit=zone.borrowing_limit,
        lending_limit=zone.lending_limit,
        is_active=True,
    )


@router.post("/tier2/zones/{zone_id}/assign", response_model=ZoneAssignmentResponse)
async def assign_faculty_to_zone(
    zone_id: UUID,
    faculty_id: UUID,
    faculty_name: str,
    role: str = "primary",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Assign a faculty member to a zone. Requires authentication.

    role must be: "primary", "secondary", or "backup"
    """
    service = get_resilience_service(db)
    success = service.assign_faculty_to_zone(zone_id, faculty_id, faculty_name, role)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign faculty to zone")

    return {"success": True, "message": f"Assigned {faculty_name} to zone as {role}"}


@router.post("/tier2/zones/incident", response_model=ZoneIncidentResponse)
async def record_zone_incident(
    zone_id: UUID,
    incident_type: str,
    description: str,
    severity: str,
    faculty_affected: list[UUID] = None,
    services_affected: list[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record an incident affecting a zone. Requires authentication.

    severity must be: "minor", "moderate", "severe", or "critical"
    """
    from app.schemas.resilience import ZoneIncidentResponse

    service = get_resilience_service(db)
    incident = service.record_zone_incident(
        zone_id=zone_id,
        incident_type=incident_type,
        description=description,
        severity=severity,
        faculty_affected=faculty_affected,
        services_affected=services_affected,
    )

    if not incident:
        raise HTTPException(status_code=404, detail="Zone not found")

    return ZoneIncidentResponse(
        id=incident.id,
        zone_id=incident.zone_id,
        incident_type=incident.incident_type,
        description=incident.description,
        severity=incident.severity,
        started_at=incident.started_at,
        faculty_affected=[str(f) for f in incident.faculty_affected],
        services_affected=incident.services_affected,
        capacity_lost=incident.capacity_lost,
        resolved_at=incident.resolved_at,
        containment_successful=incident.containment_successful,
    )


@router.post("/tier2/zones/containment", response_model=ContainmentSetResponse)
async def set_containment_level(
    level: str,
    reason: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Set system-wide containment level. Requires authentication.

    level must be: "none", "soft", "moderate", "strict", or "lockdown"
    """
    from app.resilience.blast_radius import ContainmentLevel

    level_map = {
        "none": ContainmentLevel.NONE,
        "soft": ContainmentLevel.SOFT,
        "moderate": ContainmentLevel.MODERATE,
        "strict": ContainmentLevel.STRICT,
        "lockdown": ContainmentLevel.LOCKDOWN,
    }

    if level not in level_map:
        raise HTTPException(
            status_code=400, detail=f"Invalid containment level: {level}"
        )

    service = get_resilience_service(db)
    service.set_containment_level(level_map[level], reason)

    return {
        "success": True,
        "containment_level": level,
        "reason": reason,
    }


# =============================================================================
# Tier 2: Le Chatelier / Equilibrium Endpoints
# =============================================================================


@router.get("/tier2/equilibrium", response_model=EquilibriumReportResponse)
async def get_equilibrium_report(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get comprehensive equilibrium analysis report.

    Shows current stresses, compensations, and sustainability analysis.
    """
    from app.schemas.resilience import CompensationResponse as SchemaCompResponse
    from app.schemas.resilience import CompensationType as SchemaCompType
    from app.schemas.resilience import (
        EquilibriumReportResponse,
    )
    from app.schemas.resilience import EquilibriumState as SchemaEquilState
    from app.schemas.resilience import (
        StressResponse,
    )
    from app.schemas.resilience import StressType as SchemaStressType

    service = get_resilience_service(db)
    report = service.get_equilibrium_report()

    stress_responses = [
        StressResponse(
            id=s.id,
            stress_type=SchemaStressType(s.stress_type.value),
            description=s.description,
            magnitude=s.magnitude,
            duration_days=s.duration_days,
            capacity_impact=s.capacity_impact,
            demand_impact=s.demand_impact,
            applied_at=s.applied_at,
            is_active=s.is_active,
        )
        for s in report.active_stresses
    ]

    comp_responses = [
        SchemaCompResponse(
            id=c.id,
            stress_id=c.stress_id,
            compensation_type=SchemaCompType(c.compensation_type.value),
            description=c.description,
            compensation_magnitude=c.compensation_magnitude,
            effectiveness=c.effectiveness,
            initiated_at=c.initiated_at,
            is_active=c.is_active,
        )
        for c in report.active_compensations
    ]

    return EquilibriumReportResponse(
        generated_at=report.generated_at,
        current_equilibrium_state=SchemaEquilState(
            report.current_equilibrium_state.value
        ),
        current_capacity=report.current_capacity,
        current_demand=report.current_demand,
        current_coverage_rate=report.current_coverage_rate,
        active_stresses=stress_responses,
        total_stress_magnitude=report.total_stress_magnitude,
        active_compensations=comp_responses,
        total_compensation_magnitude=report.total_compensation_magnitude,
        compensation_debt=report.compensation_debt,
        sustainability_score=report.sustainability_score,
        days_until_equilibrium=report.days_until_equilibrium,
        days_until_exhaustion=report.days_until_exhaustion,
        recommendations=report.recommendations,
    )


@router.post("/tier2/stress", response_model=StressResponse)
async def apply_stress(
    stress_type: str,
    description: str,
    magnitude: float,
    duration_days: int,
    capacity_impact: float,
    demand_impact: float = 0.0,
    is_acute: bool = True,
    is_reversible: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Apply a stress to the system. Requires authentication.

    stress_type must be: "faculty_loss", "demand_surge", "quality_pressure",
    "time_compression", "resource_scarcity", or "external_pressure"
    """
    from app.resilience.le_chatelier import StressType
    from app.schemas.resilience import StressResponse
    from app.schemas.resilience import StressType as SchemaStressType

    type_map = {
        "faculty_loss": StressType.FACULTY_LOSS,
        "demand_surge": StressType.DEMAND_SURGE,
        "quality_pressure": StressType.QUALITY_PRESSURE,
        "time_compression": StressType.TIME_COMPRESSION,
        "resource_scarcity": StressType.RESOURCE_SCARCITY,
        "external_pressure": StressType.EXTERNAL_PRESSURE,
    }

    if stress_type not in type_map:
        raise HTTPException(
            status_code=400, detail=f"Invalid stress type: {stress_type}"
        )

    service = get_resilience_service(db)
    stress = service.apply_system_stress(
        stress_type=type_map[stress_type],
        description=description,
        magnitude=magnitude,
        duration_days=duration_days,
        capacity_impact=capacity_impact,
        demand_impact=demand_impact,
        is_acute=is_acute,
        is_reversible=is_reversible,
    )

    return StressResponse(
        id=stress.id,
        stress_type=SchemaStressType(stress.stress_type.value),
        description=stress.description,
        magnitude=stress.magnitude,
        duration_days=stress.duration_days,
        capacity_impact=stress.capacity_impact,
        demand_impact=stress.demand_impact,
        applied_at=stress.applied_at,
        is_active=stress.is_active,
    )


@router.post("/tier2/stress/{stress_id}/resolve", response_model=StressResolveResponse)
async def resolve_stress(
    stress_id: UUID,
    resolution_notes: str = "",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark a stress as resolved. Requires authentication.
    """
    service = get_resilience_service(db)
    service.resolve_stress(stress_id, resolution_notes)

    return {"success": True, "stress_id": str(stress_id), "message": "Stress resolved"}


@router.post("/tier2/compensation", response_model=CompensationResponse)
async def initiate_compensation(
    stress_id: UUID,
    compensation_type: str,
    description: str,
    magnitude: float,
    effectiveness: float = 0.8,
    sustainability_days: int = 30,
    immediate_cost: float = 0.0,
    hidden_cost: float = 0.0,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Initiate a compensation response to a stress. Requires authentication.

    compensation_type must be: "overtime", "cross_coverage", "deferred_leave",
    "service_reduction", "efficiency_gain", "backup_activation", or "quality_trade"
    """
    from app.resilience.le_chatelier import CompensationType
    from app.schemas.resilience import CompensationResponse as SchemaCompResponse
    from app.schemas.resilience import CompensationType as SchemaCompType

    type_map = {
        "overtime": CompensationType.OVERTIME,
        "cross_coverage": CompensationType.CROSS_COVERAGE,
        "deferred_leave": CompensationType.DEFERRED_LEAVE,
        "service_reduction": CompensationType.SERVICE_REDUCTION,
        "efficiency_gain": CompensationType.EFFICIENCY_GAIN,
        "backup_activation": CompensationType.BACKUP_ACTIVATION,
        "quality_trade": CompensationType.QUALITY_TRADE,
    }

    if compensation_type not in type_map:
        raise HTTPException(
            status_code=400, detail=f"Invalid compensation type: {compensation_type}"
        )

    service = get_resilience_service(db)
    compensation = service.initiate_compensation(
        stress_id=stress_id,
        compensation_type=type_map[compensation_type],
        description=description,
        magnitude=magnitude,
        effectiveness=effectiveness,
        sustainability_days=sustainability_days,
        immediate_cost=immediate_cost,
        hidden_cost=hidden_cost,
    )

    if not compensation:
        raise HTTPException(status_code=404, detail="Stress not found")

    return SchemaCompResponse(
        id=compensation.id,
        stress_id=compensation.stress_id,
        compensation_type=SchemaCompType(compensation.compensation_type.value),
        description=compensation.description,
        compensation_magnitude=compensation.compensation_magnitude,
        effectiveness=compensation.effectiveness,
        initiated_at=compensation.initiated_at,
        is_active=compensation.is_active,
    )


@router.post("/tier2/stress/predict", response_model=StressPredictionResponse)
async def predict_stress_response(
    stress_type: str,
    magnitude: float,
    duration_days: int,
    capacity_impact: float,
    demand_impact: float = 0.0,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Predict how the system will respond to a potential stress.

    Use this for planning before actually applying stress.
    """
    from app.resilience.le_chatelier import StressType
    from app.schemas.resilience import StressPredictionResponse
    from app.schemas.resilience import StressType as SchemaStressType

    type_map = {
        "faculty_loss": StressType.FACULTY_LOSS,
        "demand_surge": StressType.DEMAND_SURGE,
        "quality_pressure": StressType.QUALITY_PRESSURE,
        "time_compression": StressType.TIME_COMPRESSION,
        "resource_scarcity": StressType.RESOURCE_SCARCITY,
        "external_pressure": StressType.EXTERNAL_PRESSURE,
    }

    if stress_type not in type_map:
        raise HTTPException(
            status_code=400, detail=f"Invalid stress type: {stress_type}"
        )

    service = get_resilience_service(db)
    prediction = service.predict_stress_response(
        stress_type=type_map[stress_type],
        magnitude=magnitude,
        duration_days=duration_days,
        capacity_impact=capacity_impact,
        demand_impact=demand_impact,
    )

    return StressPredictionResponse(
        id=prediction.id,
        predicted_at=prediction.predicted_at,
        stress_type=SchemaStressType(prediction.stress_type.value),
        stress_magnitude=prediction.stress_magnitude,
        stress_duration_days=prediction.stress_duration_days,
        predicted_compensation=prediction.predicted_compensation,
        predicted_new_capacity=prediction.predicted_new_capacity,
        predicted_coverage_rate=prediction.predicted_coverage_rate,
        predicted_daily_cost=prediction.predicted_daily_cost,
        predicted_total_cost=prediction.predicted_total_cost,
        predicted_burnout_increase=prediction.predicted_burnout_increase,
        additional_intervention_needed=prediction.additional_intervention_needed,
        recommended_actions=prediction.recommended_actions,
        sustainability_assessment=prediction.sustainability_assessment,
    )


@router.post("/tier2/equilibrium/shift", response_model=EquilibriumShiftResponse)
async def calculate_equilibrium_shift(
    original_capacity: float,
    original_demand: float,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Calculate the equilibrium shift from original state to current.

    Per Le Chatelier's principle, compensation is always partial
    and the new equilibrium will be different from the old one.
    """
    from app.schemas.resilience import EquilibriumShiftResponse
    from app.schemas.resilience import EquilibriumState as SchemaEquilState

    service = get_resilience_service(db)
    shift = service.calculate_equilibrium_shift(original_capacity, original_demand)

    return EquilibriumShiftResponse(
        id=shift.id,
        calculated_at=shift.calculated_at,
        original_capacity=shift.original_capacity,
        original_demand=shift.original_demand,
        original_coverage_rate=shift.original_coverage_rate,
        total_capacity_impact=shift.total_capacity_impact,
        total_demand_impact=shift.total_demand_impact,
        total_compensation=shift.total_compensation,
        compensation_efficiency=shift.compensation_efficiency,
        new_capacity=shift.new_capacity,
        new_demand=shift.new_demand,
        new_coverage_rate=shift.new_coverage_rate,
        sustainable_capacity=shift.sustainable_capacity,
        compensation_debt=shift.compensation_debt,
        daily_debt_rate=shift.daily_debt_rate,
        burnout_risk=shift.burnout_risk,
        days_until_exhaustion=shift.days_until_exhaustion,
        equilibrium_state=SchemaEquilState(shift.equilibrium_state.value),
        is_sustainable=shift.is_sustainable,
    )


# =============================================================================
# Tier 2: Combined Status Endpoint
# =============================================================================


@router.get("/tier2/status", response_model=Tier2StatusResponse)
async def get_tier2_status(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get combined status of all Tier 2 resilience components.

    Returns summary of homeostasis, blast radius, and equilibrium status.
    """
    from app.schemas.resilience import AllostasisState as SchemaAllostasisState
    from app.schemas.resilience import ContainmentLevel as SchemaContainment
    from app.schemas.resilience import EquilibriumState as SchemaEquilState
    from app.schemas.resilience import (
        Tier2StatusResponse,
    )

    service = get_resilience_service(db)
    status = service.get_tier2_status()

    return Tier2StatusResponse(
        generated_at=datetime.fromisoformat(status["generated_at"]),
        homeostasis_state=SchemaAllostasisState(status["homeostasis"]["state"]),
        feedback_loops_healthy=status["homeostasis"]["feedback_loops_healthy"],
        feedback_loops_deviating=status["homeostasis"]["feedback_loops_deviating"],
        average_allostatic_load=status["homeostasis"]["average_allostatic_load"],
        positive_feedback_risks=status["homeostasis"]["positive_feedback_risks"],
        total_zones=status["blast_radius"]["total_zones"],
        zones_healthy=status["blast_radius"]["zones_healthy"],
        zones_critical=status["blast_radius"]["zones_critical"],
        containment_active=status["blast_radius"]["containment_active"],
        containment_level=SchemaContainment(
            status["blast_radius"]["containment_level"]
        ),
        equilibrium_state=SchemaEquilState(status["equilibrium"]["state"]),
        current_coverage_rate=status["equilibrium"]["current_coverage_rate"],
        compensation_debt=status["equilibrium"]["compensation_debt"],
        sustainability_score=status["equilibrium"]["sustainability_score"],
        tier2_status=status["tier2_status"],
        recommendations=status["recommendations"],
    )


# =============================================================================
# Tier 3: Cognitive Load Endpoints
# =============================================================================


@router.post(
    "/tier3/cognitive/session/start", response_model=CognitiveSessionStartResponse
)
async def start_cognitive_session(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a new cognitive session for decision-making.

    Tracks cognitive load and prevents decision fatigue.
    """
    service = get_resilience_service(db)
    session = service.start_cognitive_session(user_id)

    return {
        "session_id": session.id,
        "user_id": str(user_id),
        "started_at": session.started_at.isoformat(),
        "max_decisions_before_break": session.max_decisions_before_break,
        "current_state": session.current_state.value,
    }


@router.post(
    "/tier3/cognitive/session/{session_id}/end",
    response_model=CognitiveSessionEndResponse,
)
async def end_cognitive_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """End a cognitive session."""
    service = get_resilience_service(db)
    service.end_cognitive_session(session_id)

    return {"success": True, "session_id": str(session_id), "message": "Session ended"}


@router.get(
    "/tier3/cognitive/session/{session_id}/status",
    response_model=CognitiveSessionStatusResponse,
)
async def get_cognitive_session_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get cognitive load status for a session.

    Returns current state, remaining capacity, and recommendations.
    """
    service = get_resilience_service(db)
    status = service.get_cognitive_status(session_id)

    if not status:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": str(status.session_id),
        "user_id": str(status.user_id),
        "current_state": status.current_state.value,
        "decisions_this_session": status.decisions_this_session,
        "cognitive_cost_this_session": status.cognitive_cost_this_session,
        "remaining_capacity": status.remaining_capacity,
        "decisions_until_break": status.decisions_until_break,
        "should_take_break": status.should_take_break,
        "average_decision_time": status.average_decision_time,
        "recommendations": status.recommendations,
    }


@router.post("/tier3/cognitive/decision", response_model=DecisionCreateResponse)
async def create_decision(
    category: str,
    complexity: str,
    description: str,
    options: list[str],
    recommended_option: str | None = None,
    safe_default: str | None = None,
    is_urgent: bool = False,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new decision request.

    category: assignment, swap, coverage, leave, conflict, override, policy, emergency
    complexity: trivial, simple, moderate, complex, strategic
    """
    from app.resilience.cognitive_load import DecisionCategory, DecisionComplexity

    category_map = {
        "assignment": DecisionCategory.ASSIGNMENT,
        "swap": DecisionCategory.SWAP,
        "coverage": DecisionCategory.COVERAGE,
        "leave": DecisionCategory.LEAVE,
        "conflict": DecisionCategory.CONFLICT,
        "override": DecisionCategory.OVERRIDE,
        "policy": DecisionCategory.POLICY,
        "emergency": DecisionCategory.EMERGENCY,
    }

    complexity_map = {
        "trivial": DecisionComplexity.TRIVIAL,
        "simple": DecisionComplexity.SIMPLE,
        "moderate": DecisionComplexity.MODERATE,
        "complex": DecisionComplexity.COMPLEX,
        "strategic": DecisionComplexity.STRATEGIC,
    }

    if category not in category_map:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    if complexity not in complexity_map:
        raise HTTPException(status_code=400, detail=f"Invalid complexity: {complexity}")

    service = get_resilience_service(db)
    decision = service.create_decision(
        category=category_map[category],
        complexity=complexity_map[complexity],
        description=description,
        options=options,
        recommended_option=recommended_option,
        safe_default=safe_default,
        is_urgent=is_urgent,
    )

    return {
        "decision_id": decision.id,
        "category": decision.category.value,
        "complexity": decision.complexity.value,
        "description": decision.description,
        "options": decision.options,
        "recommended_option": decision.recommended_option,
        "has_safe_default": decision.has_safe_default,
        "is_urgent": decision.is_urgent,
        "estimated_cognitive_cost": decision.get_cognitive_cost(),
    }


@router.post(
    "/tier3/cognitive/decision/{decision_id}/resolve",
    response_model=DecisionResolveResponse,
)
async def resolve_decision(
    decision_id: UUID,
    session_id: UUID,
    chosen_option: str,
    actual_time_seconds: float | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a decision that was made."""
    service = get_resilience_service(db)
    service.record_decision(
        session_id=session_id,
        decision_id=decision_id,
        chosen_option=chosen_option,
        decided_by=str(current_user.id),
        actual_time_seconds=actual_time_seconds,
    )

    return {
        "success": True,
        "decision_id": str(decision_id),
        "chosen_option": chosen_option,
    }


@router.get("/tier3/cognitive/queue", response_model=DecisionQueueResponse)
async def get_decision_queue(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get status of pending decision queue.

    Shows pending decisions grouped by complexity and category.
    """
    service = get_resilience_service(db)
    status = service.get_decision_queue_status()

    return {
        "total_pending": status.total_pending,
        "by_complexity": status.by_complexity,
        "by_category": status.by_category,
        "urgent_count": status.urgent_count,
        "can_auto_decide": status.can_auto_decide,
        "oldest_pending": (
            status.oldest_pending.isoformat() if status.oldest_pending else None
        ),
        "estimated_cognitive_cost": status.estimated_cognitive_cost,
        "recommendations": status.recommendations,
    }


@router.get(
    "/tier3/cognitive/decisions/prioritized",
    response_model=PrioritizedDecisionsResponse,
)
async def get_prioritized_decisions(
    db: AsyncSession = Depends(get_async_db),
):
    """Get pending decisions in recommended processing order."""
    service = get_resilience_service(db)
    decisions = service.get_prioritized_decisions()

    return {
        "decisions": [
            {
                "decision_id": d.id,
                "category": d.category.value,
                "complexity": d.complexity.value,
                "description": d.description,
                "is_urgent": d.is_urgent,
                "recommended_option": d.recommended_option,
                "cognitive_cost": d.get_cognitive_cost(),
            }
            for d in decisions[:20]
        ],
        "total": len(decisions),
    }


@router.post("/tier3/cognitive/schedule/analyze", response_model=CognitiveLoadAnalysis)
async def analyze_schedule_cognitive_load(
    schedule_changes: list[dict],
    db: AsyncSession = Depends(get_async_db),
):
    """
    Calculate cognitive load imposed by a schedule on coordinators.

    schedule_changes: List of dicts with 'type' field describing the change.
    """
    service = get_resilience_service(db)
    result = service.calculate_schedule_cognitive_load(schedule_changes)

    return result


# =============================================================================
# Tier 3: Stigmergy Endpoints
# =============================================================================


@router.post("/tier3/stigmergy/preference", response_model=PreferenceRecordResponse)
async def record_preference(
    faculty_id: UUID,
    trail_type: str,
    slot_type: str | None = None,
    slot_id: UUID | None = None,
    target_faculty_id: UUID | None = None,
    strength: float = 0.5,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record a preference trail for a faculty member.

    trail_type: preference, avoidance, swap_affinity, workload, sequence
    """
    from app.resilience.stigmergy import TrailType

    type_map = {
        "preference": TrailType.PREFERENCE,
        "avoidance": TrailType.AVOIDANCE,
        "swap_affinity": TrailType.SWAP_AFFINITY,
        "workload": TrailType.WORKLOAD,
        "sequence": TrailType.SEQUENCE,
    }

    if trail_type not in type_map:
        raise HTTPException(status_code=400, detail=f"Invalid trail type: {trail_type}")

    service = get_resilience_service(db)
    trail = service.record_preference(
        faculty_id=faculty_id,
        trail_type=type_map[trail_type],
        slot_type=slot_type,
        slot_id=slot_id,
        target_faculty_id=target_faculty_id,
        strength=strength,
    )

    return {
        "trail_id": trail.id,
        "faculty_id": str(faculty_id),
        "trail_type": trail.trail_type.value,
        "strength": trail.strength,
        "strength_category": trail.strength_category.value,
    }


@router.post("/tier3/stigmergy/signal", response_model=BehavioralSignalResponse)
async def record_behavioral_signal(
    faculty_id: UUID,
    signal_type: str,
    slot_type: str | None = None,
    slot_id: UUID | None = None,
    target_faculty_id: UUID | None = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Record a behavioral signal that updates preference trails.

    signal_type: explicit_preference, accepted_assignment, requested_swap,
                 completed_swap, declined_offer, high_satisfaction, low_satisfaction
    """
    from app.resilience.stigmergy import SignalType

    type_map = {
        "explicit_preference": SignalType.EXPLICIT_PREFERENCE,
        "accepted_assignment": SignalType.ACCEPTED_ASSIGNMENT,
        "requested_swap": SignalType.REQUESTED_SWAP,
        "completed_swap": SignalType.COMPLETED_SWAP,
        "declined_offer": SignalType.DECLINED_OFFER,
        "high_satisfaction": SignalType.HIGH_SATISFACTION,
        "low_satisfaction": SignalType.LOW_SATISFACTION,
    }

    if signal_type not in type_map:
        raise HTTPException(
            status_code=400, detail=f"Invalid signal type: {signal_type}"
        )

    service = get_resilience_service(db)
    service.record_behavioral_signal(
        faculty_id=faculty_id,
        signal_type=type_map[signal_type],
        slot_type=slot_type,
        slot_id=slot_id,
        target_faculty_id=target_faculty_id,
    )

    return {"success": True, "signal_type": signal_type, "faculty_id": str(faculty_id)}


@router.get("/tier3/stigmergy/collective", response_model=CollectivePreferenceResponse)
async def get_collective_preference(
    slot_type: str | None = None,
    slot_id: UUID | None = None,
    db: AsyncSession = Depends(get_async_db),
):
    """Get aggregated preference for a slot or slot type."""
    service = get_resilience_service(db)
    pref = service.get_collective_preference(slot_type, slot_id)

    if not pref:
        return {
            "found": False,
            "slot_type": slot_type,
            "slot_id": str(slot_id) if slot_id else None,
        }

    return {
        "found": True,
        "slot_type": pref.slot_type,
        "total_preference_strength": pref.total_preference_strength,
        "total_avoidance_strength": pref.total_avoidance_strength,
        "net_preference": pref.net_preference,
        "faculty_count": pref.faculty_count,
        "confidence": pref.confidence,
        "is_popular": pref.is_popular,
        "is_unpopular": pref.is_unpopular,
    }


@router.get(
    "/tier3/stigmergy/faculty/{faculty_id}/preferences",
    response_model=FacultyPreferencesResponse,
)
async def get_faculty_preferences(
    faculty_id: UUID,
    trail_type: str | None = None,
    min_strength: float = 0.1,
    db: AsyncSession = Depends(get_async_db),
):
    """Get all preference trails for a faculty member."""
    from app.resilience.stigmergy import TrailType

    type_map = {
        "preference": TrailType.PREFERENCE,
        "avoidance": TrailType.AVOIDANCE,
        "swap_affinity": TrailType.SWAP_AFFINITY,
        "workload": TrailType.WORKLOAD,
        "sequence": TrailType.SEQUENCE,
    }

    parsed_type = type_map.get(trail_type) if trail_type else None

    service = get_resilience_service(db)
    trails = service.get_faculty_preferences(faculty_id, parsed_type, min_strength)

    return {
        "faculty_id": str(faculty_id),
        "trails": [
            {
                "trail_id": t.id,
                "trail_type": t.trail_type.value,
                "slot_type": t.slot_type,
                "strength": t.strength,
                "strength_category": t.strength_category.value,
                "reinforcement_count": t.reinforcement_count,
                "age_days": t.age_days,
            }
            for t in trails
        ],
        "total": len(trails),
    }


@router.get("/tier3/stigmergy/swap-network", response_model=SwapNetworkResponse)
async def get_swap_network(
    db: AsyncSession = Depends(get_async_db),
):
    """Get swap affinity network showing faculty pairings."""
    service = get_resilience_service(db)
    network = service.get_swap_network()

    edges = [
        {
            "faculty1_id": str(f1),
            "faculty2_id": str(f2),
            "affinity": affinity,
            "successful_swaps": network.successful_swaps.get((f1, f2), 0),
        }
        for (f1, f2), affinity in network.edges.items()
    ]

    return {
        "edges": edges,
        "total_pairs": len(edges),
    }


@router.post("/tier3/stigmergy/suggest", response_model=AssignmentSuggestionsResponse)
async def suggest_assignments(
    slot_id: UUID,
    slot_type: str,
    available_faculty: list[UUID],
    db: AsyncSession = Depends(get_async_db),
):
    """Suggest faculty for a slot based on preference trails."""
    service = get_resilience_service(db)
    suggestions = service.suggest_assignments(slot_id, slot_type, available_faculty)

    return {
        "suggestions": [
            {
                "faculty_id": str(fid),
                "score": score,
                "reason": reason,
            }
            for fid, score, reason in suggestions
        ],
        "total": len(suggestions),
    }


@router.get("/tier3/stigmergy/status", response_model=StigmergyStatusResponse)
async def get_stigmergy_status(
    db: AsyncSession = Depends(get_async_db),
):
    """Get overall status of the stigmergy system."""
    service = get_resilience_service(db)
    status = service.get_stigmergy_status()

    return {
        "timestamp": status.timestamp.isoformat(),
        "total_trails": status.total_trails,
        "active_trails": status.active_trails,
        "trails_by_type": status.trails_by_type,
        "average_strength": status.average_strength,
        "average_age_days": status.average_age_days,
        "evaporation_debt_hours": status.evaporation_debt_hours,
        "popular_slots": status.popular_slots,
        "unpopular_slots": status.unpopular_slots,
        "strong_swap_pairs": status.strong_swap_pairs,
        "recommendations": status.recommendations,
    }


@router.get("/tier3/stigmergy/patterns", response_model=StigmergyPatternsResponse)
async def detect_preference_patterns(
    db: AsyncSession = Depends(get_async_db),
):
    """Detect emergent patterns from collective trails."""
    service = get_resilience_service(db)
    patterns = service.detect_preference_patterns()

    return patterns


@router.post("/tier3/stigmergy/evaporate", response_model=TrailEvaporationResponse)
async def evaporate_trails(
    force: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply evaporation to all preference trails."""
    service = get_resilience_service(db)
    service.evaporate_trails(force)

    return {"success": True, "message": "Trail evaporation applied"}


# =============================================================================
# Tier 3: Hub Analysis Endpoints
# =============================================================================


@router.post("/tier3/hubs/analyze", response_model=HubAnalysisResponse)
async def analyze_hubs(
    start_date: date | None = None,
    end_date: date | None = None,
    max_faculty: int | None = Query(
        None, ge=1, description="Optional limit for faculty records"
    ),
    max_assignments: int | None = Query(
        None, ge=1, description="Optional limit for assignment records"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Run hub vulnerability analysis on faculty.

    Identifies critical "hub" faculty whose loss would cause disproportionate disruption.

    Optional limits (max_faculty, max_assignments) can be set for performance tuning.
    By default, no limits are applied to ensure accurate hub analysis.
    """
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person

    service = get_resilience_service(db)

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data - apply optional limits if specified
    query_start = time.time()
    faculty_query = (
        db.query(Person).filter(Person.type == "faculty").order_by(Person.id)
    )
    if max_faculty:
        faculty_query = faculty_query.limit(max_faculty)
    faculty = faculty_query.all()

    assignments_query = (
        db.query(Assignment)
        .join(Block)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Assignment.id)
    )
    if max_assignments:
        assignments_query = assignments_query.limit(max_assignments)
    assignments = assignments_query.all()
    query_time = time.time() - query_start

    logger.info(
        "Hub analysis data loaded: faculty=%d, assignments=%d, "
        "date_range=%s to %s, query_time=%.3fs",
        len(faculty),
        len(assignments),
        start_date,
        end_date,
        query_time,
    )

    # Build services mapping (simplified - would need proper implementation)
    services = {}  # service_id -> [faculty_ids]

    # Run analysis
    results = service.analyze_hubs(faculty, assignments, services)

    return {
        "analyzed_at": datetime.utcnow().isoformat(),
        "total_faculty": len(faculty),
        "total_hubs": len([r for r in results if r.is_hub]),
        "hubs": [
            {
                "faculty_id": str(r.faculty_id),
                "faculty_name": r.faculty_name,
                "composite_score": r.composite_score,
                "risk_level": r.risk_level.value,
                "is_hub": r.is_hub,
                "degree_centrality": r.degree_centrality,
                "betweenness_centrality": r.betweenness_centrality,
                "services_covered": r.services_covered,
                "unique_services": r.unique_services,
                "replacement_difficulty": r.replacement_difficulty,
            }
            for r in results[:20]
        ],
    }


@router.get("/tier3/hubs/top", response_model=TopHubsResponse)
async def get_top_hubs(
    n: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_async_db),
):
    """Get top N most critical hubs."""
    service = get_resilience_service(db)
    hubs = service.get_top_hubs(n)

    return {
        "hubs": [
            {
                "faculty_id": str(h.faculty_id),
                "faculty_name": h.faculty_name,
                "composite_score": h.composite_score,
                "risk_level": h.risk_level.value,
                "unique_services": h.unique_services,
            }
            for h in hubs
        ],
        "count": len(hubs),
    }


@router.get("/tier3/hubs/{faculty_id}/profile", response_model=HubProfileDetailResponse)
async def get_hub_profile(
    faculty_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get detailed profile for a hub faculty member."""
    service = get_resilience_service(db)

    # Would need proper services mapping
    services = {}
    profile = service.create_hub_profile(faculty_id, services)

    if not profile:
        raise HTTPException(status_code=404, detail="Hub profile not found")

    return {
        "faculty_id": str(profile.faculty_id),
        "faculty_name": profile.faculty_name,
        "risk_level": profile.risk_level.value,
        "unique_skills": profile.unique_skills,
        "high_demand_skills": profile.high_demand_skills,
        "protection_status": profile.protection_status.value,
        "protection_measures": profile.protection_measures,
        "backup_faculty": [str(b) for b in profile.backup_faculty],
        "risk_factors": profile.risk_factors,
        "mitigation_actions": profile.mitigation_actions,
    }


@router.get(
    "/tier3/hubs/cross-training", response_model=CrossTrainingRecommendationsResponse
)
async def get_cross_training_recommendations(
    db: AsyncSession = Depends(get_async_db),
):
    """Get cross-training recommendations to reduce hub concentration."""
    service = get_resilience_service(db)

    # Would need proper services mapping
    services = {}
    recommendations = service.generate_cross_training_recommendations(services)

    return {
        "recommendations": [
            {
                "id": str(r.id),
                "skill": r.skill,
                "priority": r.priority.value,
                "reason": r.reason,
                "current_holders": [str(h) for h in r.current_holders],
                "recommended_trainees": [str(t) for t in r.recommended_trainees],
                "estimated_training_hours": r.estimated_training_hours,
                "risk_reduction": r.risk_reduction,
                "status": r.status,
            }
            for r in recommendations
        ],
        "total": len(recommendations),
    }


@router.post(
    "/tier3/hubs/{faculty_id}/protect", response_model=HubProtectionPlanCreateResponse
)
async def create_hub_protection_plan(
    faculty_id: UUID,
    period_start: date,
    period_end: date,
    reason: str,
    workload_reduction: float = 0.3,
    assign_backup: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a protection plan for a hub during a high-risk period."""
    service = get_resilience_service(db)

    plan = service.create_hub_protection_plan(
        hub_faculty_id=faculty_id,
        period_start=period_start,
        period_end=period_end,
        reason=reason,
        workload_reduction=workload_reduction,
        assign_backup=assign_backup,
        created_by=str(current_user.id),
    )

    if not plan:
        raise HTTPException(
            status_code=404, detail="Faculty is not a hub or not analyzed"
        )

    return {
        "plan_id": str(plan.id),
        "hub_faculty_id": str(plan.hub_faculty_id),
        "hub_faculty_name": plan.hub_faculty_name,
        "period_start": plan.period_start.isoformat(),
        "period_end": plan.period_end.isoformat(),
        "reason": plan.reason,
        "workload_reduction": plan.workload_reduction,
        "backup_assigned": plan.backup_assigned,
        "backup_faculty_ids": [str(b) for b in plan.backup_faculty_ids],
        "status": plan.status,
    }


@router.get("/tier3/hubs/distribution", response_model=HubDistributionReportResponse)
async def get_hub_distribution_report(
    db: AsyncSession = Depends(get_async_db),
):
    """Get report on hub distribution across the system."""
    service = get_resilience_service(db)

    # Would need proper services mapping
    services = {}
    report = service.get_hub_distribution_report(services)

    return {
        "generated_at": report.generated_at.isoformat(),
        "total_faculty": report.total_faculty,
        "total_hubs": report.total_hubs,
        "catastrophic_hubs": report.catastrophic_hubs,
        "critical_hubs": report.critical_hubs,
        "high_risk_hubs": report.high_risk_hubs,
        "hub_concentration": report.hub_concentration,
        "single_points_of_failure": report.single_points_of_failure,
        "average_hub_score": report.average_hub_score,
        "services_with_single_provider": report.services_with_single_provider,
        "services_with_dual_coverage": report.services_with_dual_coverage,
        "well_covered_services": report.well_covered_services,
        "recommendations": report.recommendations,
    }


@router.get("/tier3/hubs/status", response_model=HubStatusResponse)
async def get_hub_status(
    db: AsyncSession = Depends(get_async_db),
):
    """Get summary status of hub analysis."""
    service = get_resilience_service(db)
    status = service.get_hub_status()

    return status


# =============================================================================
# Tier 3: Combined Status Endpoint
# =============================================================================


@router.get("/tier3/status", response_model=Tier3StatusResponse)
async def get_tier3_status(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get combined status of all Tier 3 resilience components.

    Returns summary of cognitive load, stigmergy, and hub analysis.
    """
    service = get_resilience_service(db)
    status = service.get_tier3_status()

    return status
