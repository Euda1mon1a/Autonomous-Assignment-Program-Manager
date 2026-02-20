import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models.wellness import (
    Survey,
    SurveyType,
    SurveyFrequency,
    WellnessAccount,
    SurveyResponse,
    HopfieldPosition,
    AchievementType,
    WellnessPointTransaction,
)
from app.models.person import Person

# MBI-2 Questions
MBI_QUESTIONS = [
    {
        "id": "mbi_exhaustion",
        "text": "I feel burned out from my work.",
        "type": "likert_7",
        "options": [
            {"label": "Never", "value": 0, "score": 0},
            {"label": "A few times a year", "value": 1, "score": 1},
            {"label": "Once a month", "value": 2, "score": 2},
            {"label": "A few times a month", "value": 3, "score": 3},
            {"label": "Once a week", "value": 4, "score": 4},
            {"label": "A few times a week", "value": 5, "score": 5},
            {"label": "Every day", "value": 6, "score": 6},
        ],
    },
    {
        "id": "mbi_depersonalization",
        "text": "I've become more callous toward people since I took this job.",
        "type": "likert_7",
        "options": [
            {"label": "Never", "value": 0, "score": 0},
            {"label": "A few times a year", "value": 1, "score": 1},
            {"label": "Once a month", "value": 2, "score": 2},
            {"label": "A few times a month", "value": 3, "score": 3},
            {"label": "Once a week", "value": 4, "score": 4},
            {"label": "A few times a week", "value": 5, "score": 5},
            {"label": "Every day", "value": 6, "score": 6},
        ],
    },
]

# PSS-4 Questions
PSS_QUESTIONS = [
    {
        "id": "pss_control",
        "text": "In the last month, how often have you felt that you were unable to control the important things in your life?",
        "type": "likert_5",
        "options": [
            {"label": "Never", "value": 0, "score": 0},
            {"label": "Almost Never", "value": 1, "score": 1},
            {"label": "Sometimes", "value": 2, "score": 2},
            {"label": "Fairly Often", "value": 3, "score": 3},
            {"label": "Very Often", "value": 4, "score": 4},
        ],
    },
    {
        "id": "pss_confident",
        "text": "In the last month, how often have you felt confident about your ability to handle your personal problems?",
        "type": "likert_5",
        "options": [
            {"label": "Never", "value": 4, "score": 4},
            {"label": "Almost Never", "value": 3, "score": 3},
            {"label": "Sometimes", "value": 2, "score": 2},
            {"label": "Fairly Often", "value": 1, "score": 1},
            {"label": "Very Often", "value": 0, "score": 0},
        ],
    },
    {
        "id": "pss_going_way",
        "text": "In the last month, how often have you felt that things were going your way?",
        "type": "likert_5",
        "options": [
            {"label": "Never", "value": 4, "score": 4},
            {"label": "Almost Never", "value": 3, "score": 3},
            {"label": "Sometimes", "value": 2, "score": 2},
            {"label": "Fairly Often", "value": 1, "score": 1},
            {"label": "Very Often", "value": 0, "score": 0},
        ],
    },
    {
        "id": "pss_piling_up",
        "text": "In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
        "type": "likert_5",
        "options": [
            {"label": "Never", "value": 0, "score": 0},
            {"label": "Almost Never", "value": 1, "score": 1},
            {"label": "Sometimes", "value": 2, "score": 2},
            {"label": "Fairly Often", "value": 3, "score": 3},
            {"label": "Very Often", "value": 4, "score": 4},
        ],
    },
]

# Pulse Questions
PULSE_QUESTIONS = [
    {
        "id": "pulse_mood",
        "text": "How is your mood today?",
        "type": "rating_5",
        "options": [
            {"label": "Very Low", "value": 1, "score": 1},
            {"label": "Low", "value": 2, "score": 2},
            {"label": "Neutral", "value": 3, "score": 3},
            {"label": "High", "value": 4, "score": 4},
            {"label": "Very High", "value": 5, "score": 5},
        ],
    },
    {
        "id": "pulse_energy",
        "text": "How is your energy level?",
        "type": "rating_5",
        "options": [
            {"label": "Depleted", "value": 1, "score": 1},
            {"label": "Low", "value": 2, "score": 2},
            {"label": "Moderate", "value": 3, "score": 3},
            {"label": "High", "value": 4, "score": 4},
            {"label": "Full", "value": 5, "score": 5},
        ],
    },
]


async def seed_wellness():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        print("Seeding Surveys...")

        now_naive = datetime.now(UTC)

        surveys_data = [
            {
                "name": "MBI-2",
                "display_name": "Burnout Assessment (MBI-2)",
                "survey_type": SurveyType.BURNOUT,
                "description": "Maslach Burnout Inventory 2-item short form.",
                "questions_json": MBI_QUESTIONS,
                "points_value": 50,
                "frequency": SurveyFrequency.WEEKLY,
                "target_roles_json": ["resident"],
            },
            {
                "name": "PSS-4",
                "display_name": "Perceived Stress Scale (PSS-4)",
                "survey_type": SurveyType.STRESS,
                "description": "4-item version of the Perceived Stress Scale.",
                "questions_json": PSS_QUESTIONS,
                "points_value": 50,
                "frequency": SurveyFrequency.WEEKLY,
            },
            {
                "name": "Program-Pulse",
                "display_name": "Quick Pulse Check-in",
                "survey_type": SurveyType.PULSE,
                "description": "Quick daily mood and energy check.",
                "questions_json": PULSE_QUESTIONS,
                "points_value": 10,
                "frequency": SurveyFrequency.DAILY,
            },
        ]

        for data in surveys_data:
            result = await db.execute(select(Survey).where(Survey.name == data["name"]))
            if not result.scalar_one_or_none():
                s = Survey(**data)
                s.created_at = now_naive
                s.updated_at = now_naive
                db.add(s)
                print(f" - Added survey: {s.name}")

        await db.flush()

        print("\nCreating Wellness Accounts for all people...")
        result = await db.execute(select(Person))
        people = result.scalars().all()

        for person in people:
            result = await db.execute(
                select(WellnessAccount).where(WellnessAccount.person_id == person.id)
            )
            if not result.scalar_one_or_none():
                account = WellnessAccount(
                    person_id=person.id,
                    points_balance=100,
                    points_lifetime=100,
                    current_streak_weeks=2,
                    longest_streak_weeks=2,
                    achievements_json=[AchievementType.FIRST_CHECKIN.value],
                    achievements_earned_at_json={
                        AchievementType.FIRST_CHECKIN.value: now_naive.isoformat()
                    },
                    leaderboard_opt_in=True,
                    display_name=f"User-{str(person.id)[:4]}",
                    research_consent=True,
                )
                account.created_at = now_naive
                account.updated_at = now_naive
                db.add(account)
                print(f" - Created account for: {person.name}")

                # Add initial transaction
                await db.flush()
                tx = WellnessPointTransaction(
                    account_id=account.id,
                    points=100,
                    balance_after=100,
                    transaction_type="achievement",
                    source="Initial Welcome Points",
                )
                tx.created_at = now_naive
                db.add(tx)

        await db.flush()

        print("\nAdding sample Hopfield positions...")
        for person in people[:5]:  # Just first 5 people
            existing = await db.execute(
                select(HopfieldPosition).where(
                    HopfieldPosition.person_id == person.id,
                    HopfieldPosition.block_number == 1,
                    HopfieldPosition.academic_year == 2025,
                )
            )
            if existing.scalar_one_or_none():
                print(f" - Hopfield position already exists for: {person.name}")
                continue
            pos = HopfieldPosition(
                person_id=person.id,
                x_position=0.4,
                y_position=0.6,
                basin_depth=0.75,
                energy_value=-1.2,
                stability_score=0.8,
                confidence=4,
                block_number=1,
                academic_year=2025,
            )
            pos.created_at = now_naive
            db.add(pos)
            print(f" - Added position for: {person.name}")

        await db.commit()
        print("\nWellness seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_wellness())
