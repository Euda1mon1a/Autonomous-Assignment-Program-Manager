"""
API routes for gamified wellness and survey data collection.

This module provides endpoints for the research data collection platform,
including survey submission, gamification features, and Hopfield visualization.

Key Features:
    - Survey Management: List available surveys, submit responses, view history
    - Gamification: Points, streaks, achievements, leaderboard
    - Hopfield Integration: Submit positions on energy landscape
    - Admin Analytics: Aggregate trends, correlation analysis, data export

Authentication:
    All endpoints require authentication via JWT token. Regular users see
    their own data; admins can view aggregate analytics.

Research Ethics:
    - Research consent required before data used in studies
    - Leaderboard participation is opt-in with anonymous display names
    - Data export is de-identified

Related Models:
    - Survey, SurveyResponse: Survey definitions and responses
    - WellnessAccount: Gamification account (points, streaks, badges)
    - HopfieldPosition: User-positioned energy landscape state

Related Schemas:
    - app.schemas.wellness: Request/response models for all wellness endpoints
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.person import Person
from app.models.user import User
from app.schemas.wellness import (
    AchievementInfo,
    ConsentRequest,
    HopfieldAggregatesResponse,
    HopfieldLandscapeData,
    HopfieldPositionCreate,
    HopfieldPositionResult,
    LeaderboardEntry,
    LeaderboardOptInRequest,
    LeaderboardResponse,
    PointHistoryResponse,
    PointTransactionResponse,
    QuickPulseResult,
    QuickPulseSubmit,
    QuickPulseWidgetData,
    SurveyHistoryResponse,
    SurveyListItem,
    SurveyResponse,
    SurveyResponseCreate,
    SurveyResponseSummary,
    SurveySubmissionResult,
    TransactionTypeEnum,
    WellnessAccountResponse,
    WellnessAccountUpdate,
    WellnessAnalyticsSummary,
)
from app.services.wellness_service import WellnessService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wellness", tags=["wellness"])


# ============================================================================
# Helper Functions
# ============================================================================


async def _get_person_for_user(db: AsyncSession, user: User) -> Person:
    """
    Get the Person record linked to a user.

    Finds the Person record that matches the user's email (resident or faculty).
    """
    from sqlalchemy import select

    result = await db.execute(select(Person).where(Person.email == user.email))
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No person profile linked to this user account",
        )

    return person


# ============================================================================
# Survey Endpoints
# ============================================================================


@router.get("/surveys", response_model=list[SurveyListItem])
async def list_available_surveys(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all surveys available for the current user.

    Returns surveys with availability status based on cooldowns and
    completion history. Surveys are filtered by role targeting.

    Returns:
        list[SurveyListItem]: Available surveys with metadata
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    surveys = await service.get_available_surveys(person.id)

    return [
        SurveyListItem(
            id=s["id"],
            name=s["name"],
            display_name=s["display_name"],
            survey_type=s["survey_type"],
            points_value=s["points_value"],
            estimated_seconds=s["estimated_seconds"],
            frequency=s["frequency"],
            is_available=s["is_available"],
            next_available_at=s["next_available_at"],
            completed_this_period=s["completed_this_period"],
        )
        for s in surveys
    ]


@router.get("/surveys/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific survey by ID.

    Returns the full survey definition including questions.

    Args:
        survey_id: UUID of the survey

    Returns:
        SurveyResponse: Complete survey with questions
    """
    service = WellnessService(db)
    survey = await service.get_survey_by_id(survey_id)

    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found",
        )

    return SurveyResponse(
        id=survey.id,
        name=survey.name,
        display_name=survey.display_name,
        survey_type=survey.survey_type,
        description=survey.description,
        instructions=survey.instructions,
        points_value=survey.points_value,
        estimated_seconds=survey.estimated_seconds,
        frequency=survey.frequency,
        questions=survey.questions_json or [],
        is_active=survey.is_active,
        created_at=survey.created_at,
    )


@router.post("/surveys/{survey_id}/respond", response_model=SurveySubmissionResult)
async def submit_survey_response(
    survey_id: UUID,
    request: SurveyResponseCreate,
    http_request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a response to a survey.

    Validates responses, calculates score, awards points, updates streak,
    and checks for new achievements. Also captures algorithm snapshot
    for research correlation.

    Args:
        survey_id: UUID of the survey
        request: Response data including answers

    Returns:
        SurveySubmissionResult: Submission result with points, achievements
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    # Extract client info
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    # TODO: Capture algorithm snapshot from MCP tools
    # This would call the exotic/resilience modules to get current state
    algorithm_snapshot = None

    result = await service.submit_survey_response(
        person_id=person.id,
        survey_id=survey_id,
        responses=request.responses,
        block_number=request.block_number,
        academic_year=request.academic_year,
        ip_address=ip_address,
        user_agent=user_agent,
        algorithm_snapshot=algorithm_snapshot,
    )

    return SurveySubmissionResult(
        success=result.success,
        response_id=result.response_id,
        score=result.score,
        score_interpretation=result.score_interpretation,
        points_earned=result.points_result.points_awarded,
        new_achievements=result.achievement_result.newly_earned,
        streak_updated=result.streak_result.streak_updated,
        current_streak=result.streak_result.current_streak,
        message=result.message,
    )


@router.get("/surveys/history", response_model=SurveyHistoryResponse)
async def get_survey_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's survey response history.

    Returns paginated list of past survey responses with scores.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)

    Returns:
        SurveyHistoryResponse: Paginated response history
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    responses, total = await service.get_survey_response_history(
        person_id=person.id,
        page=page,
        page_size=page_size,
    )

    return SurveyHistoryResponse(
        responses=[
            SurveyResponseSummary(
                id=r["id"],
                survey_id=r["survey_id"],
                survey_name=r["survey_name"],
                survey_type=r["survey_type"],
                score=r["score"],
                score_interpretation=r["score_interpretation"],
                submitted_at=r["submitted_at"],
                block_number=r["block_number"],
                academic_year=r["academic_year"],
            )
            for r in responses
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# Wellness Account Endpoints
# ============================================================================


@router.get("/account", response_model=WellnessAccountResponse)
async def get_wellness_account(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's wellness account.

    Returns points balance, streak info, achievements, and settings.

    Returns:
        WellnessAccountResponse: Account details with achievements
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    account = await service.get_or_create_account(person.id)
    achievements = service.get_achievement_info(account)
    available_surveys = await service.get_available_surveys(person.id)

    return WellnessAccountResponse(
        person_id=person.id,
        points_balance=account.points_balance,
        points_lifetime=account.points_lifetime,
        current_streak_weeks=account.current_streak_weeks,
        longest_streak_weeks=account.longest_streak_weeks,
        last_activity_date=account.last_activity_date,
        streak_start_date=account.streak_start_date,
        leaderboard_opt_in=account.leaderboard_opt_in,
        display_name=account.display_name,
        research_consent=account.research_consent,
        achievements=[
            AchievementInfo(
                code=a["code"],
                name=a["name"],
                description=a["description"],
                icon=a["icon"],
                earned=a["earned"],
                earned_at=a["earned_at"],
                criteria=a["criteria"],
            )
            for a in achievements
        ],
        surveys_completed_this_week=sum(
            1 for s in available_surveys if s["completed_this_period"]
        ),
        surveys_available=sum(1 for s in available_surveys if s["is_available"]),
    )


@router.patch("/account", response_model=WellnessAccountResponse)
async def update_wellness_account(
    request: WellnessAccountUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update wellness account settings.

    Allows updating leaderboard opt-in, display name, and research consent.

    Args:
        request: Update data

    Returns:
        WellnessAccountResponse: Updated account details
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    account = await service.update_account_settings(
        person_id=person.id,
        leaderboard_opt_in=request.leaderboard_opt_in,
        display_name=request.display_name,
        research_consent=request.research_consent,
    )

    achievements = service.get_achievement_info(account)
    available_surveys = await service.get_available_surveys(person.id)

    await db.commit()

    return WellnessAccountResponse(
        person_id=person.id,
        points_balance=account.points_balance,
        points_lifetime=account.points_lifetime,
        current_streak_weeks=account.current_streak_weeks,
        longest_streak_weeks=account.longest_streak_weeks,
        last_activity_date=account.last_activity_date,
        streak_start_date=account.streak_start_date,
        leaderboard_opt_in=account.leaderboard_opt_in,
        display_name=account.display_name,
        research_consent=account.research_consent,
        achievements=[
            AchievementInfo(
                code=a["code"],
                name=a["name"],
                description=a["description"],
                icon=a["icon"],
                earned=a["earned"],
                earned_at=a["earned_at"],
                criteria=a["criteria"],
            )
            for a in achievements
        ],
        surveys_completed_this_week=sum(
            1 for s in available_surveys if s["completed_this_period"]
        ),
        surveys_available=sum(1 for s in available_surveys if s["is_available"]),
    )


@router.post("/account/consent")
async def provide_research_consent(
    request: ConsentRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Provide or withdraw research consent.

    Research consent is required for survey responses to be used in
    correlation studies. Can be withdrawn at any time.

    Args:
        request: Consent decision and version

    Returns:
        dict: Confirmation message
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    await service.update_account_settings(
        person_id=person.id,
        research_consent=request.consent,
    )

    await db.commit()

    action = "provided" if request.consent else "withdrawn"
    return {"message": f"Research consent {action} successfully"}


@router.post("/account/leaderboard")
async def opt_in_leaderboard(
    request: LeaderboardOptInRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Opt in or out of the anonymous leaderboard.

    When opting in, can provide an anonymous display name.

    Args:
        request: Opt-in decision and display name

    Returns:
        dict: Confirmation message
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    await service.update_account_settings(
        person_id=person.id,
        leaderboard_opt_in=request.opt_in,
        display_name=request.display_name,
    )

    await db.commit()

    action = "joined" if request.opt_in else "left"
    return {"message": f"You have {action} the leaderboard"}


# ============================================================================
# Points History Endpoint
# ============================================================================


@router.get("/points/history", response_model=PointHistoryResponse)
async def get_points_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's points transaction history.

    Returns paginated ledger of all point credits and debits.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)

    Returns:
        PointHistoryResponse: Paginated transaction history
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    account = await service.get_account(person.id)
    if not account:
        return PointHistoryResponse(
            transactions=[],
            total=0,
            page=page,
            page_size=page_size,
            current_balance=0,
        )

    transactions, total = await service.get_point_history(
        person_id=person.id,
        page=page,
        page_size=page_size,
    )

    return PointHistoryResponse(
        transactions=[
            PointTransactionResponse(
                id=t.id,
                points=t.points,
                balance_after=t.balance_after,
                transaction_type=TransactionTypeEnum(t.transaction_type),
                source=t.source,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=total,
        page=page,
        page_size=page_size,
        current_balance=account.points_balance,
    )


# ============================================================================
# Leaderboard Endpoints
# ============================================================================


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the anonymous wellness leaderboard.

    Shows opt-in participants ranked by lifetime points.
    Current user's position is highlighted if they have opted in.

    Returns:
        LeaderboardResponse: Ranked participants and stats
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    leaderboard = await service.get_leaderboard(
        requesting_person_id=person.id,
        limit=20,
    )

    return LeaderboardResponse(
        entries=[
            LeaderboardEntry(
                rank=e["rank"],
                display_name=e["display_name"],
                points=e["points"],
                streak=e["streak"],
                is_you=e["is_you"],
            )
            for e in leaderboard["entries"]
        ],
        total_participants=leaderboard["total_participants"],
        your_rank=leaderboard["your_rank"],
        your_points=leaderboard["your_points"],
    )


# ============================================================================
# Hopfield Endpoints
# ============================================================================


@router.post("/hopfield/position", response_model=HopfieldPositionResult)
async def submit_hopfield_position(
    request: HopfieldPositionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a position on the Hopfield energy landscape.

    Users drag a ball to indicate where they perceive the program
    currently sits on the energy landscape. Position is recorded
    with computed metrics for research correlation.

    Args:
        request: Position coordinates and optional metadata

    Returns:
        HopfieldPositionResult: Computed metrics at position
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    # TODO: Call Hopfield MCP tools to compute metrics at position
    # computed_metrics = await call_hopfield_tools(request.x_position, request.y_position)
    computed_metrics = None

    result = await service.submit_hopfield_position(
        person_id=person.id,
        x_position=request.x_position,
        y_position=request.y_position,
        z_position=request.z_position,
        confidence=request.confidence,
        notes=request.notes,
        block_number=request.block_number,
        academic_year=request.academic_year,
        computed_metrics=computed_metrics,
    )

    return HopfieldPositionResult(
        success=result["success"],
        position_id=result["position_id"],
        basin_depth=result["basin_depth"],
        energy_value=result["energy_value"],
        stability_score=result["stability_score"],
        nearest_attractor_type=result["nearest_attractor_type"],
        points_earned=result["points_earned"],
        message=result["message"],
    )


@router.get("/hopfield/aggregates", response_model=HopfieldAggregatesResponse)
async def get_hopfield_aggregates(
    block_number: int | None = None,
    academic_year: int | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get aggregated Hopfield positions for program-wide view.

    Returns anonymized aggregate of all positions, useful for
    comparing individual perception to group perception.

    Args:
        block_number: Optional filter by academic block
        academic_year: Optional filter by academic year

    Returns:
        HopfieldAggregatesResponse: Aggregate position data
    """
    service = WellnessService(db)

    aggregates = await service.get_hopfield_aggregates(
        block_number=block_number,
        academic_year=academic_year,
    )

    return HopfieldAggregatesResponse(
        total_positions=aggregates["total_positions"],
        average_x=aggregates["average_x"],
        average_y=aggregates["average_y"],
        average_basin_depth=aggregates["average_basin_depth"],
        average_energy=aggregates["average_energy"],
        block_number=aggregates["block_number"],
        academic_year=aggregates["academic_year"],
    )


# ============================================================================
# Quick Pulse Widget Endpoints
# ============================================================================


@router.get("/widget/data", response_model=QuickPulseWidgetData)
async def get_widget_data(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get data for the quick pulse dashboard widget.

    Returns current account status, available surveys, and
    recent achievements for the embedded dashboard widget.

    Returns:
        QuickPulseWidgetData: Widget display data
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    account = await service.get_or_create_account(person.id)
    achievements = service.get_achievement_info(account)
    surveys = await service.get_available_surveys(person.id)

    # Get recently earned achievements (last 30 days)
    from datetime import datetime, timedelta

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_achievements = [
        AchievementInfo(
            code=a["code"],
            name=a["name"],
            description=a["description"],
            icon=a["icon"],
            earned=True,
            earned_at=a["earned_at"],
            criteria=a["criteria"],
        )
        for a in achievements
        if a["earned"]
        and a["earned_at"]
        and datetime.fromisoformat(a["earned_at"]) > thirty_days_ago
    ]

    return QuickPulseWidgetData(
        can_submit=True,  # TODO: Check pulse cooldown
        last_submitted_at=None,  # TODO: Get last pulse submission
        current_streak=account.current_streak_weeks,
        points_balance=account.points_balance,
        available_surveys=[
            SurveyListItem(
                id=s["id"],
                name=s["name"],
                display_name=s["display_name"],
                survey_type=s["survey_type"],
                points_value=s["points_value"],
                estimated_seconds=s["estimated_seconds"],
                frequency=s["frequency"],
                is_available=s["is_available"],
                next_available_at=s["next_available_at"],
                completed_this_period=s["completed_this_period"],
            )
            for s in surveys
            if s["is_available"]
        ][:3],  # Limit to 3 for widget
        recent_achievements=recent_achievements[:3],  # Limit to 3 for widget
    )


@router.post("/pulse", response_model=QuickPulseResult)
async def submit_quick_pulse(
    request: QuickPulseSubmit,
    http_request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a quick pulse check-in.

    Simple mood/energy check-in that awards points but requires
    less time commitment than full surveys.

    Args:
        request: Mood (1-5) and optional energy (1-5)

    Returns:
        QuickPulseResult: Points awarded and streak info
    """
    person = await _get_person_for_user(db, current_user)
    service = WellnessService(db)

    # Get or create the pulse survey
    pulse_survey = await service.get_survey_by_name("Program-Pulse")

    if not pulse_survey:
        # Create default pulse survey if it doesn't exist
        # TODO: Should be seeded in migration
        return QuickPulseResult(
            success=False,
            points_earned=0,
            current_streak=0,
            message="Pulse survey not configured",
        )

    # Submit as regular survey response
    ip_address = http_request.client.host if http_request.client else None
    responses = {"pulse_mood": request.mood}
    if request.energy is not None:
        responses["pulse_energy"] = request.energy

    result = await service.submit_survey_response(
        person_id=person.id,
        survey_id=pulse_survey.id,
        responses=responses,
        ip_address=ip_address,
    )

    return QuickPulseResult(
        success=result.success,
        points_earned=result.points_result.points_awarded,
        current_streak=result.streak_result.current_streak,
        message=result.message,
    )


# ============================================================================
# Admin Analytics Endpoints
# ============================================================================


@router.get("/admin/analytics", response_model=WellnessAnalyticsSummary)
async def get_wellness_analytics(
    block_number: int | None = None,
    academic_year: int | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get wellness analytics summary (admin only).

    Provides aggregate statistics on participation, scores, and engagement.
    All data is de-identified.

    Args:
        block_number: Optional filter by academic block
        academic_year: Optional filter by academic year

    Returns:
        WellnessAnalyticsSummary: Aggregate analytics
    """
    # TODO: Add admin role check
    if current_user.role not in ["admin", "coordinator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or coordinator access required",
        )

    service = WellnessService(db)

    analytics = await service.get_analytics_summary(
        block_number=block_number,
        academic_year=academic_year,
    )

    return WellnessAnalyticsSummary(
        total_participants=analytics["total_participants"],
        active_this_week=analytics["active_this_week"],
        active_this_block=analytics["active_this_block"],
        participation_rate=analytics["participation_rate"],
        total_responses_this_week=analytics["total_responses_this_week"],
        total_responses_this_block=analytics["total_responses_this_block"],
        average_responses_per_person=analytics["average_responses_per_person"],
        average_streak=analytics["average_streak"],
        longest_streak=analytics["longest_streak"],
        total_points_earned_this_week=analytics["total_points_earned_this_week"],
    )
