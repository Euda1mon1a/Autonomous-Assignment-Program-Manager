"""Repository for RotationPreference model operations.

Provides async CRUD operations for rotation preferences with specialized
queries for preference management in rotation templates.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rotation_preference import RotationPreference
from app.repositories.async_base import AsyncBaseRepository
from app.schemas.rotation_template_gui import RotationPreferenceCreate


class RotationPreferenceRepository(AsyncBaseRepository[RotationPreference]):
    """Repository for RotationPreference database operations.

    Extends AsyncBaseRepository with specialized methods for
    managing scheduling preferences in rotation templates.
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.

        Args:
            db: Async database session
        """
        super().__init__(RotationPreference, db)

    async def get_by_template_id(self, template_id: UUID) -> list[RotationPreference]:
        """Get all preferences for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of RotationPreference instances ordered by type
        """
        result = await self.db.execute(
            select(RotationPreference)
            .where(RotationPreference.rotation_template_id == template_id)
            .order_by(RotationPreference.preference_type)
        )
        return list(result.scalars().all())

    async def get_active_by_template_id(
        self, template_id: UUID
    ) -> list[RotationPreference]:
        """Get all active preferences for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of active RotationPreference instances
        """
        result = await self.db.execute(
            select(RotationPreference)
            .where(
                and_(
                    RotationPreference.rotation_template_id == template_id,
                    RotationPreference.is_active == True,
                )
            )
            .order_by(RotationPreference.preference_type)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self, template_id: UUID, preference_type: str
    ) -> RotationPreference | None:
        """Get a specific preference type for a template.

        Args:
            template_id: UUID of the rotation template
            preference_type: Type of preference

        Returns:
            RotationPreference or None if not found
        """
        result = await self.db.execute(
            select(RotationPreference).where(
                and_(
                    RotationPreference.rotation_template_id == template_id,
                    RotationPreference.preference_type == preference_type,
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_template_id(self, template_id: UUID) -> int:
        """Delete all preferences for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            Number of deleted preferences
        """
        result = await self.db.execute(
            delete(RotationPreference).where(
                RotationPreference.rotation_template_id == template_id
            )
        )
        return result.rowcount

    async def bulk_create_for_template(
        self, template_id: UUID, preferences: list[RotationPreferenceCreate]
    ) -> list[RotationPreference]:
        """Create multiple preferences for a template.

        Args:
            template_id: UUID of the rotation template
            preferences: List of preference create schemas

        Returns:
            List of created RotationPreference instances
        """
        now = datetime.utcnow()
        new_preferences = []

        for pref_data in preferences:
            preference = RotationPreference(
                rotation_template_id=template_id,
                preference_type=pref_data.preference_type,
                weight=pref_data.weight,
                config_json=pref_data.config_json,
                is_active=pref_data.is_active,
                description=pref_data.description,
                created_at=now,
                updated_at=now,
            )
            self.db.add(preference)
            new_preferences.append(preference)

        await self.db.flush()
        return new_preferences

    async def get_by_weight(
        self,
        template_id: UUID,
        weight: Literal["low", "medium", "high", "required"],
    ) -> list[RotationPreference]:
        """Get all preferences with a specific weight.

        Args:
            template_id: UUID of the rotation template
            weight: Weight level to filter by

        Returns:
            List of RotationPreference instances with the specified weight
        """
        result = await self.db.execute(
            select(RotationPreference)
            .where(
                and_(
                    RotationPreference.rotation_template_id == template_id,
                    RotationPreference.weight == weight,
                )
            )
            .order_by(RotationPreference.preference_type)
        )
        return list(result.scalars().all())

    async def get_high_priority(self, template_id: UUID) -> list[RotationPreference]:
        """Get high priority preferences (high weight or required).

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of high priority RotationPreference instances
        """
        result = await self.db.execute(
            select(RotationPreference)
            .where(
                and_(
                    RotationPreference.rotation_template_id == template_id,
                    RotationPreference.is_active == True,
                    RotationPreference.weight.in_(["high", "required"]),
                )
            )
            .order_by(RotationPreference.preference_type)
        )
        return list(result.scalars().all())

    async def toggle_active(
        self, template_id: UUID, preference_type: str
    ) -> RotationPreference | None:
        """Toggle the is_active status of a preference.

        Args:
            template_id: UUID of the rotation template
            preference_type: Type of preference to toggle

        Returns:
            Updated RotationPreference or None if not found
        """
        preference = await self.get_by_type(template_id, preference_type)
        if preference:
            preference.is_active = not preference.is_active
            preference.updated_at = datetime.utcnow()
            await self.db.flush()
        return preference

    async def update_weight(
        self,
        template_id: UUID,
        preference_type: str,
        weight: Literal["low", "medium", "high", "required"],
    ) -> RotationPreference | None:
        """Update the weight of a preference.

        Args:
            template_id: UUID of the rotation template
            preference_type: Type of preference to update
            weight: New weight value

        Returns:
            Updated RotationPreference or None if not found
        """
        preference = await self.get_by_type(template_id, preference_type)
        if preference:
            preference.weight = weight
            preference.updated_at = datetime.utcnow()
            await self.db.flush()
        return preference

    async def count_active(self, template_id: UUID) -> int:
        """Count active preferences for a template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            Number of active preferences
        """
        preferences = await self.get_active_by_template_id(template_id)
        return len(preferences)
