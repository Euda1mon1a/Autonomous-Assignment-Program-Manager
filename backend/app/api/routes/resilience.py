"""Resilience API routes.

Provides REST API endpoints for:
- System health monitoring
- Crisis response activation/deactivation
- Fallback schedule management
- Load shedding control
- Vulnerability analysis
- Historical data retrieval
"""
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.user import User
from app.models.resilience import (
    ResilienceHealthCheck,
    ResilienceEvent,
    ResilienceEventType,
    SacrificeDecision,
    FallbackActivation,
    VulnerabilityRecord,
)
from app.schemas.resilience import (
    HealthCheckRequest,
    HealthCheckResponse,
    CrisisActivationRequest,
    CrisisDeactivationRequest,
    CrisisResponse,
    FallbackActivationRequest,
    FallbackDeactivationRequest,
    FallbackListResponse,
    FallbackActivationResponse,
    FallbackInfo,
    LoadSheddingRequest,
    LoadSheddingStatus,
    VulnerabilityReportResponse,
    ComprehensiveReportResponse,
    CentralityScore,
    HealthCheckHistoryResponse,
    HealthCheckHistoryItem,
    EventHistoryResponse,
    EventHistoryItem,
    UtilizationMetrics,
    RedundancyStatus,
    OverallStatus,
    UtilizationLevel,
    DefenseLevel,
    LoadSheddingLevel,
    FallbackScenario,
    CrisisSeverity,
)
from app.core.security import get_current_active_user

router = APIRouter()


def get_resilience_service(db: Session):
    """Get or create ResilienceService instance."""
    from app.resilience.service import ResilienceService
    from app.core.config import get_resilience_config

    config = get_resilience_config()
    return ResilienceService(db=db, config=config)


def persist_health_check(db: Session, report, metrics_snapshot: dict = None):
    """Persist health check results to database."""
    health_check = ResilienceHealthCheck(
        timestamp=report.timestamp,
        overall_status=report.overall_status,
        utilization_rate=report.utilization.utilization_rate,
        utilization_level=report.utilization.level.value,
        buffer_remaining=report.utilization.buffer_remaining,
        defense_level=report.defense_level.name if report.defense_level else None,
        load_shedding_level=report.load_shedding_level.name if report.load_shedding_level else None,
        n1_pass=report.n1_pass,
        n2_pass=report.n2_pass,
        phase_transition_risk=report.phase_transition_risk,
        active_fallbacks=report.active_fallbacks,
        crisis_mode=getattr(report, 'crisis_mode', False),
        immediate_actions=report.immediate_actions,
        watch_items=report.watch_items,
        metrics_snapshot=metrics_snapshot,
    )
    db.add(health_check)
    db.commit()
    db.refresh(health_check)
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
        metadata=metadata,
        related_health_check_id=health_check_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/health", response_model=HealthCheckResponse)
async def get_system_health(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_contingency: bool = False,
    persist: bool = True,
    db: Session = Depends(get_db),
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
    """
    from app.models.person import Person
    from app.models.block import Block
    from app.models.assignment import Assignment

    service = get_resilience_service(db)

    # Default date range: next 30 days
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data for analysis
    faculty = db.query(Person).filter(Person.type == "faculty").all()
    blocks = db.query(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()
    assignments = db.query(Assignment).join(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()

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
    return HealthCheckResponse(
        timestamp=report.timestamp,
        overall_status=OverallStatus(report.overall_status),
        utilization=UtilizationMetrics(
            utilization_rate=report.utilization.utilization_rate,
            level=UtilizationLevel(report.utilization.level.value),
            buffer_remaining=report.utilization.buffer_remaining,
            wait_time_multiplier=report.utilization.wait_time_multiplier,
            safe_capacity=report.utilization.safe_capacity,
            current_demand=report.utilization.current_demand,
            theoretical_capacity=report.utilization.theoretical_capacity,
        ),
        defense_level=DefenseLevel(report.defense_level.name),
        redundancy_status=[
            RedundancyStatus(
                service=r.service,
                status=r.status,
                available=r.available,
                minimum_required=r.minimum_required,
                buffer=r.buffer,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Activate crisis response mode. Requires authentication.

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deactivate crisis response and begin recovery. Requires authentication.

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
    db: Session = Depends(get_db),
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

        fallbacks.append(FallbackInfo(
            scenario=scenario,
            description=_get_scenario_description(scenario),
            is_active=is_active,
            is_precomputed=fallback_schedule is not None,
            assignments_count=len(fallback_schedule.assignments) if fallback_schedule else None,
            coverage_rate=fallback_schedule.coverage_rate if fallback_schedule else None,
            services_reduced=fallback_schedule.services_reduced if fallback_schedule else [],
            assumptions=fallback_schedule.assumptions if fallback_schedule else [],
            activation_count=fallback_schedule.activation_count if fallback_schedule else 0,
        ))

    return FallbackListResponse(
        fallbacks=fallbacks,
        active_count=active_count,
    )


@router.post("/fallbacks/activate", response_model=FallbackActivationResponse)
async def activate_fallback(
    request: FallbackActivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Activate a pre-computed fallback schedule. Requires authentication.

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
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {request.scenario}")

    fallback = service.activate_fallback(
        scenario=service_scenario,
        approved_by=str(current_user.id),
    )

    if not fallback:
        raise HTTPException(
            status_code=404,
            detail=f"Fallback schedule for '{request.scenario.value}' not found or not precomputed"
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

    db.commit()

    return FallbackActivationResponse(
        success=True,
        scenario=request.scenario,
        assignments_count=len(fallback.assignments),
        coverage_rate=fallback.coverage_rate,
        services_reduced=fallback.services_reduced,
        message=f"Fallback '{request.scenario.value}' activated successfully",
    )


@router.post("/fallbacks/deactivate")
async def deactivate_fallback(
    request: FallbackDeactivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deactivate a fallback schedule and return to normal operations.
    Requires authentication.
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
    activation = db.query(FallbackActivation).filter(
        FallbackActivation.scenario == request.scenario.value,
        FallbackActivation.deactivated_at.is_(None),
    ).first()

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

    db.commit()

    return {"success": True, "message": f"Fallback '{request.scenario.value}' deactivated"}


@router.get("/load-shedding", response_model=LoadSheddingStatus)
async def get_load_shedding_status(
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually set load shedding level. Requires authentication.

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

    db.commit()

    return LoadSheddingStatus(
        level=request.level,
        activities_suspended=status.activities_suspended,
        activities_protected=status.activities_protected,
        capacity_available=status.capacity_available,
        capacity_demand=status.capacity_demand,
    )


@router.get("/vulnerability", response_model=VulnerabilityReportResponse)
async def get_vulnerability_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Run full N-1/N-2 vulnerability analysis.

    This is computationally intensive for large datasets.
    Use for periodic assessment, not real-time monitoring.
    """
    from app.models.person import Person
    from app.models.block import Block
    from app.models.assignment import Assignment

    service = get_resilience_service(db)

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data
    faculty = db.query(Person).filter(Person.type == "faculty").all()
    blocks = db.query(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()
    assignments = db.query(Assignment).join(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()

    # Build coverage requirements
    coverage_requirements = {b.id: 1 for b in blocks}

    # Run analysis
    report = service.contingency.generate_report(
        faculty=faculty,
        blocks=blocks,
        assignments=assignments,
        coverage_requirements=coverage_requirements,
        current_utilization=0.0,  # Will be calculated
    )

    # Get centrality scores
    services = {}  # Would need proper service mapping
    centrality_scores = service.contingency.calculate_centrality(
        faculty, assignments, services
    )

    # Persist vulnerability record
    vuln_record = VulnerabilityRecord(
        period_start=datetime.combine(start_date, datetime.min.time()),
        period_end=datetime.combine(end_date, datetime.min.time()),
        faculty_count=len(faculty),
        block_count=len(blocks),
        n1_pass=report.n1_pass,
        n2_pass=report.n2_pass,
        phase_transition_risk=report.phase_transition_risk,
        n1_vulnerabilities=[v.__dict__ for v in report.n1_vulnerabilities[:10]],
        n2_fatal_pairs=[{"pair": [str(p.faculty1_id), str(p.faculty2_id)]} for p in report.n2_fatal_pairs[:10]],
        most_critical_faculty=[str(fid) for fid in report.most_critical_faculty[:5]],
        recommended_actions=report.recommended_actions,
    )
    db.add(vuln_record)
    db.commit()

    return VulnerabilityReportResponse(
        analyzed_at=datetime.utcnow(),
        period_start=start_date,
        period_end=end_date,
        n1_pass=report.n1_pass,
        n2_pass=report.n2_pass,
        phase_transition_risk=report.phase_transition_risk,
        n1_vulnerabilities=[
            {
                "faculty_id": str(v.faculty_id),
                "affected_blocks": v.affected_blocks,
                "severity": v.severity,
            }
            for v in report.n1_vulnerabilities[:10]
        ],
        n2_fatal_pairs=[
            {
                "faculty1_id": str(p.faculty1_id),
                "faculty2_id": str(p.faculty2_id),
            }
            for p in report.n2_fatal_pairs[:10]
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
            for c in centrality_scores[:10]
        ],
        recommended_actions=report.recommended_actions,
    )


@router.get("/report", response_model=ComprehensiveReportResponse)
async def get_comprehensive_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Generate comprehensive resilience report.

    Combines all component reports into a single document
    suitable for leadership review or audit.
    """
    from app.models.person import Person
    from app.models.block import Block
    from app.models.assignment import Assignment

    service = get_resilience_service(db)

    # Default date range
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Load data
    faculty = db.query(Person).filter(Person.type == "faculty").all()
    blocks = db.query(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()
    assignments = db.query(Assignment).join(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()

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
    status: Optional[OverallStatus] = None,
    db: Session = Depends(get_db),
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
        query
        .order_by(desc(ResilienceHealthCheck.timestamp))
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
                defense_level=DefenseLevel(item.defense_level) if item.defense_level else None,
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
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
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
        query
        .order_by(desc(ResilienceEvent.timestamp))
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
