import asyncio
import uuid
from datetime import datetime, timedelta, UTC
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models.notification import (
    Notification,
    ScheduledNotificationRecord,
    NotificationPreferenceRecord,
)
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.models.email_log import EmailLog, EmailStatus
from app.models.person import Person
from app.models.user import User


async def seed_notifications():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        now_naive = datetime.utcnow()

        print("Seeding Email Templates...")
        templates_data = [
            {
                "name": "Schedule Published",
                "template_type": EmailTemplateType.SCHEDULE_CHANGE,
                "subject_template": "New Schedule Published for Block {{ block_number }}",
                "body_html_template": "<p>Hello {{ name }},</p><p>A new schedule has been published for Block {{ block_number }}.</p>",
                "body_text_template": "Hello {{ name }},\n\nA new schedule has been published for Block {{ block_number }}.",
            },
            {
                "name": "Swap Request",
                "template_type": EmailTemplateType.SWAP_NOTIFICATION,
                "subject_template": "New Swap Request from {{ requester_name }}",
                "body_html_template": "<p>{{ requester_name }} wants to swap {{ your_shift }} with their {{ requester_shift }}.</p>",
                "body_text_template": "{{ requester_name }} wants to swap {{ your_shift }} with their {{ requester_shift }}.",
            },
        ]

        for data in templates_data:
            result = await db.execute(
                select(EmailTemplate).where(EmailTemplate.name == data["name"])
            )
            if not result.scalar_one_or_none():
                t = EmailTemplate(**data)
                t.created_at = now_naive
                t.updated_at = now_naive
                db.add(t)
                print(f" - Added template: {t.name}")

        await db.flush()

        print("\nCreating Notification Preferences for all people...")
        result = await db.execute(select(Person))
        people = result.scalars().all()

        for person in people:
            result = await db.execute(
                select(NotificationPreferenceRecord).where(
                    NotificationPreferenceRecord.user_id == person.id
                )
            )
            if not result.scalar_one_or_none():
                pref = NotificationPreferenceRecord(
                    user_id=person.id,
                    enabled_channels="in_app,email",
                    notification_types={
                        "schedule_change": True,
                        "swap_request": True,
                        "wellness_reminder": True,
                    },
                )
                pref.created_at = now_naive
                pref.updated_at = now_naive
                db.add(pref)
                print(f" - Created preferences for: {person.name}")

        await db.flush()

        print("\nAdding sample notifications...")
        for person in people[:3]:
            notif = Notification(
                recipient_id=person.id,
                notification_type="welcome",
                subject="Welcome to the Residency Scheduler",
                body="Welcome! Your wellness account has been set up and you have 100 points.",
                priority="normal",
                channels_delivered="in_app",
            )
            notif.created_at = now_naive
            db.add(notif)
            print(f" - Added welcome notification for: {person.name}")

        await db.commit()
        print("\nNotification seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_notifications())
