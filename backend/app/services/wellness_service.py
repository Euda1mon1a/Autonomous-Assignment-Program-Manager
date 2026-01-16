"""
Wellness Service.

Implements gamification logic for the research data collection platform,
including points, streaks, achievements, and survey management.

Key Features:
    - Survey availability tracking with cooldowns
    - Points economy (earn, spend, track)
    - Streak management (weekly participation)
    - Achievement unlocking
    - Leaderboard management (opt-in, anonymous)
    - Algorithm correlation snapshot capture

Research Correlation:
    - Captures algorithm state at survey submission time
    - Enables validation of predictive models against self-reports
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.person import Person
from app.models.wellness import (
    AchievementType,
    HopfieldPosition,
    Survey,
    SurveyAvailability,
    SurveyFrequency,
    SurveyResponse,
    WellnessAccount,
    WellnessLeaderboardSnapshot,
    WellnessPointTransaction,
)
from app.utils.academic_blocks import get_block_number_for_date

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Points values
POINTS_MBI_2 = 50
POINTS_PSS_4 = 50
POINTS_SLEEP = 25
POINTS_GSE_4 = 50
POINTS_PULSE = 10
POINTS_HOPFIELD = 25
POINTS_STREAK_BONUS = 50  # After 2+ weeks
POINTS_BLOCK_COMPLETION = 200  # All surveys in a block

# Achievement definitions
ACHIEVEMENT_DEFINITIONS = {
    AchievementType.FIRST_CHECKIN: {
        "name": "First Check-In",
        "description": "Completed your first wellness survey",
        "icon": "badge-check",
        "criteria": "Complete any survey",
    },
    AchievementType.POINTS_100: {
        "name": "Century Club",
        "description": "Earned 100 lifetime points",
        "icon": "star",
        "criteria": "Accumulate 100 points",
    },
    AchievementType.POINTS_500: {
        "name": "Rising Star",
        "description": "Earned 500 lifetime points",
        "icon": "star-fill",
        "criteria": "Accumulate 500 points",
    },
    AchievementType.POINTS_1000: {
        "name": "Iron Resident",
        "description": "Earned 1000 lifetime points",
        "icon": "trophy",
        "criteria": "Accumulate 1000 points",
    },
    AchievementType.WEEKLY_WARRIOR: {
        "name": "Weekly Warrior",
        "description": "Maintained a 4-week participation streak",
        "icon": "fire",
        "criteria": "Complete surveys 4 weeks in a row",
    },
    AchievementType.CONSISTENCY_KING: {
        "name": "Consistency King",
        "description": "Maintained an 8-week participation streak",
        "icon": "crown",
        "criteria": "Complete surveys 8 weeks in a row",
    },
    AchievementType.DATA_HERO: {
        "name": "Data Hero",
        "description": "Completed all available surveys in an academic block",
        "icon": "chart-bar",
        "criteria": "Complete MBI-2, PSS-4, Sleep, and GSE-4 in one block",
    },
    AchievementType.RESEARCH_CHAMPION: {
        "name": "Research Champion",
        "description": "Participated for 52 weeks (full academic year)",
        "icon": "academic-cap",
        "criteria": "Complete surveys for 52 weeks",
    },
    AchievementType.FACULTY_MENTOR: {
        "name": "Faculty Mentor",
        "description": "Faculty member with exceptional engagement",
        "icon": "user-group",
        "criteria": "Faculty with 500+ points and research consent",
    },
}

# Frequency to cooldown mapping
FREQUENCY_COOLDOWNS = {
    SurveyFrequency.DAILY: timedelta(days=1),
    SurveyFrequency.WEEKLY: timedelta(days=7),
    SurveyFrequency.BIWEEKLY: timedelta(days=14),
    SurveyFrequency.BLOCK: timedelta(days=28),  # Approximation
    SurveyFrequency.ANNUAL: timedelta(days=365),
}


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PointsResult:
    """Result of a points operation."""

    points_awarded: int
    new_balance: int
    new_lifetime: int
    transaction_id: UUID | None = None


@dataclass
class AchievementResult:
    """Result of checking/awarding achievements."""

    newly_earned: list[str]
    all_achievements: list[str]


@dataclass
class StreakResult:
    """Result of streak update."""

    current_streak: int
    longest_streak: int
    streak_updated: bool
    streak_bonus_awarded: int


@dataclass
class SurveySubmissionResult:
    """Complete result of survey submission."""

    success: bool
    response_id: UUID | None
    score: float | None
    score_interpretation: str | None
    points_result: PointsResult
    streak_result: StreakResult
    achievement_result: AchievementResult
    message: str


# ============================================================================
# Wellness Service
# ============================================================================


class WellnessService:
    """
    Service for managing wellness surveys and gamification.

    Handles:
        - Survey availability and cooldowns
        - Response submission and scoring
        - Points economy
        - Streak tracking
        - Achievement unlocking
        - Leaderboard management
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------------
    # Account Management
    # ------------------------------------------------------------------------

    async def get_or_create_account(self, person_id: UUID) -> WellnessAccount:
        """Get or create a wellness account for a person."""
        result = await self.db.execute(
            select(WellnessAccount).where(WellnessAccount.person_id == person_id)
        )
        account = result.scalar_one_or_none()

        if account is None:
            account = WellnessAccount(
                person_id=person_id,
                points_balance=0,
                points_lifetime=0,
                current_streak_weeks=0,
                longest_streak_weeks=0,
                achievements_json=[],
                achievements_earned_at_json={},
            )
            self.db.add(account)
            await self.db.flush()
            logger.info(f"Created wellness account for person {person_id}")

        return account

    async def get_account(self, person_id: UUID) -> WellnessAccount | None:
        """Get a wellness account by person ID."""
        result = await self.db.execute(
            select(WellnessAccount).where(WellnessAccount.person_id == person_id)
        )
        return result.scalar_one_or_none()

    async def update_account_settings(
        self,
        person_id: UUID,
        leaderboard_opt_in: bool | None = None,
        display_name: str | None = None,
        research_consent: bool | None = None,
    ) -> WellnessAccount:
        """Update wellness account settings."""
        account = await self.get_or_create_account(person_id)

        if leaderboard_opt_in is not None:
            account.leaderboard_opt_in = leaderboard_opt_in
        if display_name is not None:
            account.display_name = display_name
        if research_consent is not None:
            account.research_consent = research_consent
            if research_consent:
                account.consent_date = datetime.utcnow()
                account.consent_version = "1.0"

        await self.db.flush()
        return account

    # ------------------------------------------------------------------------
    # Survey Management
    # ------------------------------------------------------------------------

    async def get_available_surveys(self, person_id: UUID) -> list[dict]:
        """Get surveys available for a person to take."""
        # Get active surveys
        result = await self.db.execute(select(Survey).where(Survey.is_active == True))
        surveys = result.scalars().all()

        # Get person's role for targeting
        person_result = await self.db.execute(
            select(Person).where(Person.id == person_id)
        )
        person = person_result.scalar_one_or_none()
        person_type = person.type if person else None

        available = []
        for survey in surveys:
            # Check role targeting
            target_roles = survey.target_roles_json or []
            if target_roles and person_type not in target_roles:
                continue

            # Check availability/cooldown
            availability = await self._get_survey_availability(person_id, survey.id)
            is_available = availability is None or (
                availability.next_available_at is None
                or availability.next_available_at <= datetime.utcnow()
            )

            available.append(
                {
                    "id": survey.id,
                    "name": survey.name,
                    "display_name": survey.display_name,
                    "survey_type": survey.survey_type,
                    "points_value": survey.points_value,
                    "estimated_seconds": survey.estimated_seconds,
                    "frequency": survey.frequency,
                    "is_available": is_available,
                    "next_available_at": (
                        availability.next_available_at
                        if availability and not is_available
                        else None
                    ),
                    "completed_this_period": not is_available,
                }
            )

        return available

    async def get_survey_by_id(self, survey_id: UUID) -> Survey | None:
        """Get a survey by ID."""
        result = await self.db.execute(select(Survey).where(Survey.id == survey_id))
        return result.scalar_one_or_none()

    async def get_survey_by_name(self, name: str) -> Survey | None:
        """Get a survey by name."""
        result = await self.db.execute(select(Survey).where(Survey.name == name))
        return result.scalar_one_or_none()

    async def _get_survey_availability(
        self, person_id: UUID, survey_id: UUID
    ) -> SurveyAvailability | None:
        """Get survey availability record."""
        result = await self.db.execute(
            select(SurveyAvailability).where(
                SurveyAvailability.person_id == person_id,
                SurveyAvailability.survey_id == survey_id,
            )
        )
        return result.scalar_one_or_none()

    async def _update_survey_availability(
        self, person_id: UUID, survey: Survey
    ) -> None:
        """Update survey availability after completion."""
        availability = await self._get_survey_availability(person_id, survey.id)

        if availability is None:
            availability = SurveyAvailability(
                person_id=person_id,
                survey_id=survey.id,
            )
            self.db.add(availability)

        now = datetime.utcnow()
        availability.last_completed_at = now

        # Calculate next available time based on frequency
        frequency = SurveyFrequency(survey.frequency)
        cooldown = FREQUENCY_COOLDOWNS.get(frequency, timedelta(days=7))
        availability.next_available_at = now + cooldown

        # Update block tracking
        block_info = get_block_number_for_date(now.date())
        if block_info:
            block_num, academic_year = block_info
            if (
                availability.current_block_number != block_num
                or availability.current_academic_year != academic_year
            ):
                # New block, reset counter
                availability.current_block_number = block_num
                availability.current_academic_year = academic_year
                availability.completions_this_block = 0
            availability.completions_this_block += 1

        availability.completions_this_year = (
            availability.completions_this_year or 0
        ) + 1

        await self.db.flush()

    # ------------------------------------------------------------------------
    # Survey Submission
    # ------------------------------------------------------------------------

    async def submit_survey_response(
        self,
        person_id: UUID,
        survey_id: UUID,
        responses: dict[str, Any],
        block_number: int | None = None,
        academic_year: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        algorithm_snapshot: dict | None = None,
    ) -> SurveySubmissionResult:
        """
        Submit a survey response.

        Handles:
            1. Validation
            2. Scoring
            3. Points award
            4. Streak update
            5. Achievement check
            6. Algorithm snapshot storage
        """
        # Get survey
        survey = await self.get_survey_by_id(survey_id)
        if survey is None:
            return SurveySubmissionResult(
                success=False,
                response_id=None,
                score=None,
                score_interpretation=None,
                points_result=PointsResult(0, 0, 0),
                streak_result=StreakResult(0, 0, False, 0),
                achievement_result=AchievementResult([], []),
                message="Survey not found",
            )

        # Check availability
        availability = await self._get_survey_availability(person_id, survey_id)
        if availability and availability.next_available_at:
            if availability.next_available_at > datetime.utcnow():
                return SurveySubmissionResult(
                    success=False,
                    response_id=None,
                    score=None,
                    score_interpretation=None,
                    points_result=PointsResult(0, 0, 0),
                    streak_result=StreakResult(0, 0, False, 0),
                    achievement_result=AchievementResult([], []),
                    message=f"Survey not available until {availability.next_available_at}",
                )

        # Get or create account
        account = await self.get_or_create_account(person_id)

        # Calculate temporal scoping
        if block_number is None or academic_year is None:
            block_info = get_block_number_for_date(date.today())
            if block_info:
                block_number, academic_year = block_info

        # Calculate score
        score, interpretation = self._calculate_score(survey, responses)

        # Create response
        response = SurveyResponse(
            survey_id=survey_id,
            person_id=person_id,
            block_number=block_number,
            academic_year=academic_year,
            response_data=responses,
            score=score,
            score_interpretation=interpretation,
            ip_address=ip_address,
            user_agent=user_agent,
            algorithm_snapshot_json=algorithm_snapshot,
        )
        self.db.add(response)
        await self.db.flush()

        # Update availability
        await self._update_survey_availability(person_id, survey)

        # Award points
        points_result = await self._award_points(
            account=account,
            points=survey.points_value,
            transaction_type="survey",
            source=f"{survey.display_name} completion",
            survey_response_id=response.id,
        )

        # Update streak
        streak_result = await self._update_streak(account)

        # Award streak bonus if applicable
        if streak_result.streak_bonus_awarded > 0:
            await self._award_points(
                account=account,
                points=streak_result.streak_bonus_awarded,
                transaction_type="streak",
                source=f"Week {streak_result.current_streak} streak bonus",
            )
            points_result.points_awarded += streak_result.streak_bonus_awarded
            points_result.new_balance = account.points_balance
            points_result.new_lifetime = account.points_lifetime

        # Check achievements
        achievement_result = await self._check_and_award_achievements(
            account, person_id
        )

        await self.db.commit()

        return SurveySubmissionResult(
            success=True,
            response_id=response.id,
            score=score,
            score_interpretation=interpretation,
            points_result=points_result,
            streak_result=streak_result,
            achievement_result=achievement_result,
            message="Survey submitted successfully",
        )

    def _calculate_score(
        self, survey: Survey, responses: dict[str, Any]
    ) -> tuple[float | None, str | None]:
        """Calculate survey score based on responses."""
        if not survey.scoring_json:
            # Simple sum scoring
            questions = survey.questions_json or []
            total_score = 0
            for q in questions:
                q_id = q.get("id")
                if q_id in responses:
                    options = q.get("options", [])
                    for opt in options:
                        if opt.get("value") == responses[q_id]:
                            total_score += opt.get("score", 0)
                            break

            # Interpret based on survey type
            interpretation = self._interpret_score(survey.survey_type, total_score)
            return total_score, interpretation

        # Custom scoring algorithm
        scoring = survey.scoring_json
        method = scoring.get("method", "sum")

        if method == "sum":
            total = sum(responses.values())
            return total, self._interpret_score(survey.survey_type, total)
        elif method == "average":
            avg = sum(responses.values()) / len(responses) if responses else 0
            return avg, self._interpret_score(survey.survey_type, avg)

        return None, None

    def _interpret_score(self, survey_type: str, score: float) -> str | None:
        """Interpret a score based on survey type."""
        interpretations = {
            "burnout": [
                (6, "low"),
                (9, "moderate"),
                (float("inf"), "high"),
            ],
            "stress": [
                (4, "low"),
                (8, "moderate"),
                (12, "high"),
                (float("inf"), "very_high"),
            ],
            "sleep": [
                (1, "good"),
                (2, "fair"),
                (float("inf"), "poor"),
            ],
            "efficacy": [
                (8, "low"),
                (12, "moderate"),
                (float("inf"), "high"),
            ],
        }

        thresholds = interpretations.get(survey_type)
        if not thresholds:
            return None

        for threshold, label in thresholds:
            if score <= threshold:
                return label
        return None

    # ------------------------------------------------------------------------
    # Points Management
    # ------------------------------------------------------------------------

    async def _award_points(
        self,
        account: WellnessAccount,
        points: int,
        transaction_type: str,
        source: str,
        survey_response_id: UUID | None = None,
    ) -> PointsResult:
        """Award points to an account."""
        if points <= 0:
            return PointsResult(0, account.points_balance, account.points_lifetime)

        account.points_balance += points
        account.points_lifetime += points
        account.last_activity_date = date.today()

        # Create transaction record
        transaction = WellnessPointTransaction(
            account_id=account.id,
            points=points,
            balance_after=account.points_balance,
            transaction_type=transaction_type,
            source=source,
            survey_response_id=survey_response_id,
        )
        self.db.add(transaction)
        await self.db.flush()

        return PointsResult(
            points_awarded=points,
            new_balance=account.points_balance,
            new_lifetime=account.points_lifetime,
            transaction_id=transaction.id,
        )

    async def get_point_history(
        self,
        person_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WellnessPointTransaction], int]:
        """Get point transaction history for an account."""
        account = await self.get_account(person_id)
        if not account:
            return [], 0

        # Count total
        count_result = await self.db.execute(
            select(func.count(WellnessPointTransaction.id)).where(
                WellnessPointTransaction.account_id == account.id
            )
        )
        total = count_result.scalar_one()

        # Get page
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(WellnessPointTransaction)
            .where(WellnessPointTransaction.account_id == account.id)
            .order_by(desc(WellnessPointTransaction.created_at))
            .offset(offset)
            .limit(page_size)
        )
        transactions = result.scalars().all()

        return list(transactions), total

    # ------------------------------------------------------------------------
    # Streak Management
    # ------------------------------------------------------------------------

    async def _update_streak(self, account: WellnessAccount) -> StreakResult:
        """Update streak based on activity."""
        today = date.today()
        streak_bonus = 0

        if account.last_activity_date is None:
            # First activity
            account.current_streak_weeks = 1
            account.streak_start_date = today
        else:
            days_since_last = (today - account.last_activity_date).days

            if days_since_last <= 7:
                # Check if we're in a new week
                last_week = account.last_activity_date.isocalendar()[1]
                this_week = today.isocalendar()[1]

                if this_week != last_week:
                    # New week, increment streak
                    account.current_streak_weeks += 1

                    # Award streak bonus after 2+ weeks
                    if account.current_streak_weeks >= 2:
                        streak_bonus = POINTS_STREAK_BONUS
            elif days_since_last > 14:
                # Streak broken (more than 2 weeks)
                account.current_streak_weeks = 1
                account.streak_start_date = today

        # Update longest streak
        if account.current_streak_weeks > account.longest_streak_weeks:
            account.longest_streak_weeks = account.current_streak_weeks

        account.last_activity_date = today
        await self.db.flush()

        return StreakResult(
            current_streak=account.current_streak_weeks,
            longest_streak=account.longest_streak_weeks,
            streak_updated=True,
            streak_bonus_awarded=streak_bonus,
        )

    # ------------------------------------------------------------------------
    # Achievement Management
    # ------------------------------------------------------------------------

    async def _check_and_award_achievements(
        self, account: WellnessAccount, person_id: UUID
    ) -> AchievementResult:
        """Check and award any newly earned achievements."""
        newly_earned = []

        # First check-in
        if not account.has_achievement(AchievementType.FIRST_CHECKIN.value):
            account.add_achievement(AchievementType.FIRST_CHECKIN.value)
            newly_earned.append(AchievementType.FIRST_CHECKIN.value)
            await self._award_points(
                account, 10, "achievement", "First Check-In achievement"
            )

        # Points milestones
        if account.points_lifetime >= 100 and not account.has_achievement(
            AchievementType.POINTS_100.value
        ):
            account.add_achievement(AchievementType.POINTS_100.value)
            newly_earned.append(AchievementType.POINTS_100.value)

        if account.points_lifetime >= 500 and not account.has_achievement(
            AchievementType.POINTS_500.value
        ):
            account.add_achievement(AchievementType.POINTS_500.value)
            newly_earned.append(AchievementType.POINTS_500.value)

        if account.points_lifetime >= 1000 and not account.has_achievement(
            AchievementType.POINTS_1000.value
        ):
            account.add_achievement(AchievementType.POINTS_1000.value)
            newly_earned.append(AchievementType.POINTS_1000.value)

        # Streak milestones
        if account.current_streak_weeks >= 4 and not account.has_achievement(
            AchievementType.WEEKLY_WARRIOR.value
        ):
            account.add_achievement(AchievementType.WEEKLY_WARRIOR.value)
            newly_earned.append(AchievementType.WEEKLY_WARRIOR.value)

        if account.current_streak_weeks >= 8 and not account.has_achievement(
            AchievementType.CONSISTENCY_KING.value
        ):
            account.add_achievement(AchievementType.CONSISTENCY_KING.value)
            newly_earned.append(AchievementType.CONSISTENCY_KING.value)

        if account.longest_streak_weeks >= 52 and not account.has_achievement(
            AchievementType.RESEARCH_CHAMPION.value
        ):
            account.add_achievement(AchievementType.RESEARCH_CHAMPION.value)
            newly_earned.append(AchievementType.RESEARCH_CHAMPION.value)

        # Check Data Hero (all surveys in a block)
        await self._check_data_hero_achievement(account, person_id)
        if account.has_achievement(
            AchievementType.DATA_HERO.value
        ) and AchievementType.DATA_HERO.value not in (account.achievements_json or []):
            newly_earned.append(AchievementType.DATA_HERO.value)

        await self.db.flush()

        return AchievementResult(
            newly_earned=newly_earned,
            all_achievements=account.achievements_json or [],
        )

    async def _check_data_hero_achievement(
        self, account: WellnessAccount, person_id: UUID
    ) -> None:
        """Check if person has completed all surveys in current block."""
        if account.has_achievement(AchievementType.DATA_HERO.value):
            return

        # Get current block
        block_info = get_block_number_for_date(date.today())
        if not block_info:
            return
        block_num, academic_year = block_info

        # Get required surveys (MBI-2, PSS-4, Sleep, GSE-4)
        required_surveys = ["MBI-2", "PSS-4", "PSQI-1", "GSE-4"]

        # Check completions this block
        result = await self.db.execute(
            select(SurveyResponse)
            .join(Survey)
            .where(
                SurveyResponse.person_id == person_id,
                SurveyResponse.block_number == block_num,
                SurveyResponse.academic_year == academic_year,
                Survey.name.in_(required_surveys),
            )
        )
        responses = result.scalars().all()
        completed_surveys = {r.survey.name for r in responses if hasattr(r, "survey")}

        if all(s in completed_surveys for s in required_surveys):
            account.add_achievement(AchievementType.DATA_HERO.value)
            await self._award_points(
                account, POINTS_BLOCK_COMPLETION, "achievement", "Data Hero achievement"
            )

    def get_achievement_info(self, account: WellnessAccount | None) -> list[dict]:
        """Get all achievements with earned status."""
        achievements = []
        earned_list = account.achievements_json if account else []
        earned_at = account.achievements_earned_at_json if account else {}

        for achievement_type in AchievementType:
            definition = ACHIEVEMENT_DEFINITIONS.get(achievement_type, {})
            is_earned = achievement_type.value in (earned_list or [])

            achievements.append(
                {
                    "code": achievement_type.value,
                    "name": definition.get("name", achievement_type.value),
                    "description": definition.get("description", ""),
                    "icon": definition.get("icon", "star"),
                    "earned": is_earned,
                    "earned_at": earned_at.get(achievement_type.value)
                    if is_earned
                    else None,
                    "criteria": definition.get("criteria", ""),
                }
            )

        return achievements

    # ------------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------------

    async def get_leaderboard(
        self,
        requesting_person_id: UUID | None = None,
        limit: int = 20,
    ) -> dict:
        """Get the anonymous leaderboard."""
        # Get opt-in accounts ordered by points
        result = await self.db.execute(
            select(WellnessAccount)
            .where(WellnessAccount.leaderboard_opt_in == True)
            .order_by(desc(WellnessAccount.points_lifetime))
            .limit(limit)
        )
        accounts = result.scalars().all()

        entries = []
        your_rank = None
        your_points = None

        for rank, account in enumerate(accounts, 1):
            is_you = (
                requesting_person_id is not None
                and account.person_id == requesting_person_id
            )
            if is_you:
                your_rank = rank
                your_points = account.points_lifetime

            entries.append(
                {
                    "rank": rank,
                    "display_name": account.display_name or f"Anonymous{rank}",
                    "points": account.points_lifetime,
                    "streak": account.current_streak_weeks,
                    "is_you": is_you,
                }
            )

        # Get total participants
        count_result = await self.db.execute(
            select(func.count(WellnessAccount.id)).where(
                WellnessAccount.leaderboard_opt_in == True
            )
        )
        total = count_result.scalar_one()

        return {
            "entries": entries,
            "total_participants": total,
            "your_rank": your_rank,
            "your_points": your_points,
        }

    async def create_leaderboard_snapshot(self) -> WellnessLeaderboardSnapshot:
        """Create a snapshot of the current leaderboard."""
        leaderboard = await self.get_leaderboard(limit=100)

        # Calculate aggregate stats
        result = await self.db.execute(
            select(
                func.avg(WellnessAccount.points_lifetime),
                func.count(WellnessAccount.id),
            ).where(WellnessAccount.leaderboard_opt_in == True)
        )
        row = result.one()
        avg_points = row[0] or 0
        total = row[1]

        snapshot = WellnessLeaderboardSnapshot(
            snapshot_date=date.today(),
            snapshot_type="weekly",
            rankings_json=leaderboard["entries"],
            total_participants=total,
            average_points=avg_points,
            top_10_cutoff=(
                leaderboard["entries"][9]["points"]
                if len(leaderboard["entries"]) >= 10
                else None
            ),
        )
        self.db.add(snapshot)
        await self.db.flush()

        return snapshot

    # ------------------------------------------------------------------------
    # Hopfield Position
    # ------------------------------------------------------------------------

    async def submit_hopfield_position(
        self,
        person_id: UUID,
        x_position: float,
        y_position: float,
        z_position: float | None = None,
        confidence: int | None = None,
        notes: str | None = None,
        block_number: int | None = None,
        academic_year: int | None = None,
        computed_metrics: dict | None = None,
    ) -> dict:
        """Submit a Hopfield landscape position."""
        account = await self.get_or_create_account(person_id)

        # Calculate temporal scoping if not provided
        if block_number is None or academic_year is None:
            block_info = get_block_number_for_date(date.today())
            if block_info:
                block_number, academic_year = block_info

        # Create position record
        position = HopfieldPosition(
            person_id=person_id,
            x_position=x_position,
            y_position=y_position,
            z_position=z_position,
            confidence=confidence,
            notes=notes,
            block_number=block_number,
            academic_year=academic_year,
        )

        # Add computed metrics if provided
        if computed_metrics:
            position.basin_depth = computed_metrics.get("basin_depth")
            position.energy_value = computed_metrics.get("energy_value")
            position.stability_score = computed_metrics.get("stability_score")
            position.nearest_attractor_id = computed_metrics.get("nearest_attractor_id")
            position.nearest_attractor_type = computed_metrics.get(
                "nearest_attractor_type"
            )
            position.hamming_distance = computed_metrics.get("hamming_distance")

        self.db.add(position)

        # Award points
        points_result = await self._award_points(
            account=account,
            points=POINTS_HOPFIELD,
            transaction_type="survey",
            source="Hopfield landscape positioning",
        )

        await self.db.commit()

        return {
            "success": True,
            "position_id": position.id,
            "basin_depth": position.basin_depth,
            "energy_value": position.energy_value,
            "stability_score": position.stability_score,
            "nearest_attractor_type": position.nearest_attractor_type,
            "points_earned": points_result.points_awarded,
            "message": "Position recorded successfully",
        }

    async def get_hopfield_aggregates(
        self,
        block_number: int | None = None,
        academic_year: int | None = None,
    ) -> dict:
        """Get aggregated Hopfield positions for program-wide view."""
        # Build query
        query = select(
            func.count(HopfieldPosition.id),
            func.avg(HopfieldPosition.x_position),
            func.avg(HopfieldPosition.y_position),
            func.avg(HopfieldPosition.basin_depth),
            func.avg(HopfieldPosition.energy_value),
        )

        if block_number is not None:
            query = query.where(HopfieldPosition.block_number == block_number)
        if academic_year is not None:
            query = query.where(HopfieldPosition.academic_year == academic_year)

        result = await self.db.execute(query)
        row = result.one()

        return {
            "total_positions": row[0],
            "average_x": row[1],
            "average_y": row[2],
            "average_basin_depth": row[3],
            "average_energy": row[4],
            "block_number": block_number,
            "academic_year": academic_year,
        }

    # ------------------------------------------------------------------------
    # Analytics (Admin)
    # ------------------------------------------------------------------------

    async def get_analytics_summary(
        self,
        block_number: int | None = None,
        academic_year: int | None = None,
    ) -> dict:
        """Get analytics summary for admin dashboard."""
        # Get current block if not specified
        if block_number is None or academic_year is None:
            block_info = get_block_number_for_date(date.today())
            if block_info:
                block_number, academic_year = block_info

        # Total participants
        total_result = await self.db.execute(select(func.count(WellnessAccount.id)))
        total_participants = total_result.scalar_one()

        # Active this week
        week_ago = date.today() - timedelta(days=7)
        active_week_result = await self.db.execute(
            select(func.count(WellnessAccount.id)).where(
                WellnessAccount.last_activity_date >= week_ago
            )
        )
        active_this_week = active_week_result.scalar_one()

        # Responses this week
        week_ago_dt = datetime.utcnow() - timedelta(days=7)
        responses_week_result = await self.db.execute(
            select(func.count(SurveyResponse.id)).where(
                SurveyResponse.submitted_at >= week_ago_dt
            )
        )
        responses_this_week = responses_week_result.scalar_one()

        # Average streak
        streak_result = await self.db.execute(
            select(func.avg(WellnessAccount.current_streak_weeks))
        )
        avg_streak = streak_result.scalar_one() or 0

        # Longest streak
        longest_result = await self.db.execute(
            select(func.max(WellnessAccount.longest_streak_weeks))
        )
        longest_streak = longest_result.scalar_one() or 0

        return {
            "total_participants": total_participants,
            "active_this_week": active_this_week,
            "active_this_block": active_this_week,  # Simplified
            "participation_rate": (
                active_this_week / total_participants if total_participants > 0 else 0
            ),
            "total_responses_this_week": responses_this_week,
            "total_responses_this_block": responses_this_week,
            "average_responses_per_person": (
                responses_this_week / active_this_week if active_this_week > 0 else 0
            ),
            "average_streak": avg_streak,
            "longest_streak": longest_streak,
            "total_points_earned_this_week": 0,  # Would need more complex query
        }

    async def get_survey_response_history(
        self,
        person_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Get survey response history for a person."""
        # Count total
        count_result = await self.db.execute(
            select(func.count(SurveyResponse.id)).where(
                SurveyResponse.person_id == person_id
            )
        )
        total = count_result.scalar_one()

        # Get page with survey details
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(SurveyResponse)
            .options(selectinload(SurveyResponse.survey))
            .where(SurveyResponse.person_id == person_id)
            .order_by(desc(SurveyResponse.submitted_at))
            .offset(offset)
            .limit(page_size)
        )
        responses = result.scalars().all()

        response_dicts = [
            {
                "id": r.id,
                "survey_id": r.survey_id,
                "survey_name": r.survey.name if r.survey else None,
                "survey_type": r.survey.survey_type if r.survey else None,
                "score": r.score,
                "score_interpretation": r.score_interpretation,
                "submitted_at": r.submitted_at,
                "block_number": r.block_number,
                "academic_year": r.academic_year,
            }
            for r in responses
        ]

        return response_dicts, total
