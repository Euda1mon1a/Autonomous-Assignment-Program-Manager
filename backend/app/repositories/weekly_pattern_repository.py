"""Repository for WeeklyPattern model operations.

Provides async CRUD operations for weekly patterns with specialized
queries for pattern management in rotation templates.
"""

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ActivityNotFoundError
from app.models.activity import Activity
from app.models.weekly_pattern import WeeklyPattern
from app.repositories.async_base import AsyncBaseRepository
from app.schemas.rotation_template_gui import WeeklyPatternCreate


class WeeklyPatternRepository(AsyncBaseRepository[WeeklyPattern]):
    """Repository for WeeklyPattern database operations.

    Extends AsyncBaseRepository with specialized methods for
    managing weekly pattern grids in rotation templates.
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.

        Args:
            db: Async database session
        """
        super().__init__(WeeklyPattern, db)

    async def get_by_template_id(self, template_id: UUID) -> list[WeeklyPattern]:
        """Get all patterns for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of WeeklyPattern instances ordered by day and time
        """
        result = await self.db.execute(
            select(WeeklyPattern)
            .where(WeeklyPattern.rotation_template_id == template_id)
            .order_by(WeeklyPattern.day_of_week, WeeklyPattern.time_of_day)
        )
        return list(result.scalars().all())

    async def get_by_slot(
        self, template_id: UUID, day_of_week: int, time_of_day: str
    ) -> WeeklyPattern | None:
        """Get a specific slot pattern.

        Args:
            template_id: UUID of the rotation template
            day_of_week: Day of week (0=Sunday, 6=Saturday)
            time_of_day: "AM" or "PM"

        Returns:
            WeeklyPattern or None if not found
        """
        result = await self.db.execute(
            select(WeeklyPattern).where(
                and_(
                    WeeklyPattern.rotation_template_id == template_id,
                    WeeklyPattern.day_of_week == day_of_week,
                    WeeklyPattern.time_of_day == time_of_day,
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_template_id(self, template_id: UUID) -> int:
        """Delete all patterns for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            Number of deleted patterns
        """
        result = await self.db.execute(
            delete(WeeklyPattern).where(
                WeeklyPattern.rotation_template_id == template_id
            )
        )
        return result.rowcount

    async def bulk_create_for_template(
        self, template_id: UUID, patterns: list[WeeklyPatternCreate]
    ) -> list[WeeklyPattern]:
        """Create multiple patterns for a template.

        Args:
            template_id: UUID of the rotation template
            patterns: List of pattern create schemas

        Returns:
            List of created WeeklyPattern instances
        """
        now = datetime.utcnow()
        new_patterns = []

        async def resolve_activity_id(
            activity_type: str | None,
            activity_id: UUID | None,
        ) -> UUID:
            if activity_id:
                result = await self.db.execute(
                    select(Activity).where(Activity.id == activity_id)
                )
                activity = result.scalar_one_or_none()
                if activity:
                    return activity.id
                raise ActivityNotFoundError(
                    str(activity_id), context="weekly_patterns.activity_id"
                )

            if not activity_type or not activity_type.strip():
                raise ValueError("weekly pattern requires activity_type or activity_id")

            normalized = activity_type.strip()
            result = await self.db.execute(
                select(Activity).where(
                    or_(
                        func.lower(Activity.code) == normalized.lower(),
                        func.lower(Activity.display_abbreviation) == normalized.lower(),
                        func.lower(Activity.name) == normalized.lower(),
                    )
                )
            )
            activity = result.scalar_one_or_none()
            if not activity:
                raise ActivityNotFoundError(
                    normalized, context="weekly_patterns.activity_type"
                )
            return activity.id

        for pattern_data in patterns:
            activity_id = await resolve_activity_id(
                pattern_data.activity_type,
                getattr(pattern_data, "activity_id", None),
            )
            pattern = WeeklyPattern(
                rotation_template_id=template_id,
                day_of_week=pattern_data.day_of_week,
                time_of_day=pattern_data.time_of_day,
                activity_type=pattern_data.activity_type,
                activity_id=activity_id,
                linked_template_id=pattern_data.linked_template_id,
                is_protected=pattern_data.is_protected,
                notes=pattern_data.notes,
                created_at=now,
                updated_at=now,
            )
            self.db.add(pattern)
            new_patterns.append(pattern)

        await self.db.flush()
        return new_patterns

    async def get_protected_slots(self, template_id: UUID) -> list[WeeklyPattern]:
        """Get all protected (non-editable) slots for a template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of protected WeeklyPattern instances
        """
        result = await self.db.execute(
            select(WeeklyPattern).where(
                and_(
                    WeeklyPattern.rotation_template_id == template_id,
                    WeeklyPattern.is_protected == True,
                )
            )
        )
        return list(result.scalars().all())

    async def count_by_activity_type(self, template_id: UUID) -> dict[str, int]:
        """Count patterns by activity type for a template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            Dictionary mapping activity_type to count
        """
        patterns = await self.get_by_template_id(template_id)
        counts: dict[str, int] = {}
        for pattern in patterns:
            activity = pattern.activity_type
            counts[activity] = counts.get(activity, 0) + 1
        return counts

    async def get_weekday_patterns(self, template_id: UUID) -> list[WeeklyPattern]:
        """Get patterns for weekdays only (Monday-Friday).

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of WeeklyPattern instances for weekdays
        """
        result = await self.db.execute(
            select(WeeklyPattern)
            .where(
                and_(
                    WeeklyPattern.rotation_template_id == template_id,
                    WeeklyPattern.day_of_week.in_([1, 2, 3, 4, 5]),  # Mon-Fri
                )
            )
            .order_by(WeeklyPattern.day_of_week, WeeklyPattern.time_of_day)
        )
        return list(result.scalars().all())

    async def get_weekend_patterns(self, template_id: UUID) -> list[WeeklyPattern]:
        """Get patterns for weekends only (Saturday-Sunday).

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of WeeklyPattern instances for weekends
        """
        result = await self.db.execute(
            select(WeeklyPattern)
            .where(
                and_(
                    WeeklyPattern.rotation_template_id == template_id,
                    WeeklyPattern.day_of_week.in_([0, 6]),  # Sun, Sat
                )
            )
            .order_by(WeeklyPattern.day_of_week, WeeklyPattern.time_of_day)
        )
        return list(result.scalars().all())
