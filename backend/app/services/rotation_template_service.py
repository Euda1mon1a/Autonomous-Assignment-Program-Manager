"""Rotation template service with business logic for patterns and preferences.

This service handles:
- Weekly pattern CRUD operations
- Rotation preference CRUD operations
- Atomic batch updates for patterns/preferences
- Business validation rules
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rotation_preference import RotationPreference
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.schemas.rotation_template_gui import (
    RotationPreferenceCreate,
    RotationPreferenceResponse,
    RotationPreferenceUpdate,
    WeeklyGridUpdate,
    WeeklyPatternCreate,
    WeeklyPatternResponse,
)


class RotationTemplateService:
    """Service for rotation template operations including patterns and preferences."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    # =========================================================================
    # Template Operations
    # =========================================================================

    async def get_template_by_id(self, template_id: UUID) -> RotationTemplate | None:
        """Get rotation template by ID.

        Args:
            template_id: UUID of the template

        Returns:
            RotationTemplate or None if not found
        """
        result = await self.db.execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_template_with_relations(
        self, template_id: UUID
    ) -> RotationTemplate | None:
        """Get rotation template with weekly patterns and preferences loaded.

        Args:
            template_id: UUID of the template

        Returns:
            RotationTemplate with loaded relations or None
        """
        result = await self.db.execute(
            select(RotationTemplate)
            .where(RotationTemplate.id == template_id)
            .options(
                selectinload(RotationTemplate.weekly_patterns),
                selectinload(RotationTemplate.preferences),
            )
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Weekly Pattern Operations
    # =========================================================================

    async def get_patterns_by_template_id(
        self, template_id: UUID
    ) -> list[WeeklyPattern]:
        """Get all weekly patterns for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of WeeklyPattern instances
        """
        result = await self.db.execute(
            select(WeeklyPattern)
            .where(WeeklyPattern.rotation_template_id == template_id)
            .order_by(WeeklyPattern.day_of_week, WeeklyPattern.time_of_day)
        )
        return list(result.scalars().all())

    async def replace_patterns(
        self, template_id: UUID, patterns: list[WeeklyPatternCreate]
    ) -> list[WeeklyPattern]:
        """Atomically replace all patterns for a template.

        This operation:
        1. Deletes all existing patterns for the template
        2. Creates new patterns from the input
        3. Returns the newly created patterns

        Args:
            template_id: UUID of the rotation template
            patterns: List of pattern create schemas (max 14)

        Returns:
            List of created WeeklyPattern instances

        Raises:
            ValueError: If template not found or validation fails
        """
        # Verify template exists
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Validate patterns
        self._validate_patterns(patterns)

        # Delete existing patterns
        await self.db.execute(
            delete(WeeklyPattern).where(
                WeeklyPattern.rotation_template_id == template_id
            )
        )

        # Create new patterns
        now = datetime.utcnow()
        new_patterns = []
        for pattern_data in patterns:
            pattern = WeeklyPattern(
                rotation_template_id=template_id,
                day_of_week=pattern_data.day_of_week,
                time_of_day=pattern_data.time_of_day,
                activity_type=pattern_data.activity_type,
                linked_template_id=pattern_data.linked_template_id,
                is_protected=pattern_data.is_protected,
                notes=pattern_data.notes,
                created_at=now,
                updated_at=now,
            )
            self.db.add(pattern)
            new_patterns.append(pattern)

        await self.db.flush()

        # Refresh to get IDs
        for pattern in new_patterns:
            await self.db.refresh(pattern)

        return new_patterns

    def _validate_patterns(self, patterns: list[WeeklyPatternCreate]) -> None:
        """Validate pattern list for consistency.

        Args:
            patterns: List of patterns to validate

        Raises:
            ValueError: If validation fails
        """
        if len(patterns) > 14:
            raise ValueError("Maximum 14 patterns allowed (7 days x 2 time periods)")

        # Check for duplicate day/time combinations
        seen = set()
        for pattern in patterns:
            key = (pattern.day_of_week, pattern.time_of_day)
            if key in seen:
                raise ValueError(
                    f"Duplicate pattern for day {pattern.day_of_week} {pattern.time_of_day}"
                )
            seen.add(key)

            # Validate day of week
            if pattern.day_of_week < 0 or pattern.day_of_week > 6:
                raise ValueError(
                    f"Invalid day_of_week: {pattern.day_of_week}. Must be 0-6."
                )

            # Validate time of day
            if pattern.time_of_day not in ("AM", "PM"):
                raise ValueError(
                    f"Invalid time_of_day: {pattern.time_of_day}. Must be 'AM' or 'PM'."
                )

    # =========================================================================
    # Rotation Preference Operations
    # =========================================================================

    async def get_preferences_by_template_id(
        self, template_id: UUID
    ) -> list[RotationPreference]:
        """Get all preferences for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of RotationPreference instances
        """
        result = await self.db.execute(
            select(RotationPreference)
            .where(RotationPreference.rotation_template_id == template_id)
            .order_by(RotationPreference.preference_type)
        )
        return list(result.scalars().all())

    async def replace_preferences(
        self, template_id: UUID, preferences: list[RotationPreferenceCreate]
    ) -> list[RotationPreference]:
        """Atomically replace all preferences for a template.

        This operation:
        1. Deletes all existing preferences for the template
        2. Creates new preferences from the input
        3. Returns the newly created preferences

        Args:
            template_id: UUID of the rotation template
            preferences: List of preference create schemas

        Returns:
            List of created RotationPreference instances

        Raises:
            ValueError: If template not found or validation fails
        """
        # Verify template exists
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Validate preferences
        self._validate_preferences(preferences)

        # Delete existing preferences
        await self.db.execute(
            delete(RotationPreference).where(
                RotationPreference.rotation_template_id == template_id
            )
        )

        # Create new preferences
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

        # Refresh to get IDs
        for preference in new_preferences:
            await self.db.refresh(preference)

        return new_preferences

    def _validate_preferences(
        self, preferences: list[RotationPreferenceCreate]
    ) -> None:
        """Validate preference list for consistency.

        Args:
            preferences: List of preferences to validate

        Raises:
            ValueError: If validation fails
        """
        valid_types = {
            "full_day_grouping",
            "consecutive_specialty",
            "avoid_isolated",
            "preferred_days",
            "avoid_friday_pm",
            "balance_weekly",
        }

        valid_weights = {"low", "medium", "high", "required"}

        # Check for duplicate preference types
        seen_types = set()
        for pref in preferences:
            if pref.preference_type in seen_types:
                raise ValueError(f"Duplicate preference type: {pref.preference_type}")
            seen_types.add(pref.preference_type)

            # Validate preference type
            if pref.preference_type not in valid_types:
                raise ValueError(
                    f"Invalid preference_type: {pref.preference_type}. "
                    f"Must be one of {valid_types}"
                )

            # Validate weight
            if pref.weight not in valid_weights:
                raise ValueError(
                    f"Invalid weight: {pref.weight}. Must be one of {valid_weights}"
                )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.db.rollback()

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_delete(
        self, template_ids: list[UUID], dry_run: bool = False
    ) -> dict[str, Any]:
        """Atomically delete multiple rotation templates.

        This operation is all-or-nothing: if any template doesn't exist or
        cannot be deleted, the entire batch is rolled back.

        Args:
            template_ids: List of template UUIDs to delete
            dry_run: If True, validate only without deleting

        Returns:
            Dict with operation results:
            - operation_type: "delete"
            - total: Number of requested deletions
            - succeeded: Number of successful deletions
            - failed: Number of failed deletions
            - results: Per-template results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any template not found (atomic rollback)
        """
        results = []
        templates_to_delete = []

        # Phase 1: Validate all templates exist
        for idx, template_id in enumerate(template_ids):
            template = await self.get_template_by_id(template_id)
            if not template:
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": False,
                        "error": f"Template with ID {template_id} not found",
                    }
                )
            else:
                templates_to_delete.append((idx, template_id, template))
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": True,
                        "error": None,
                    }
                )

        # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "delete",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Execute deletions (if not dry run)
        if not dry_run:
            for idx, template_id, template in templates_to_delete:
                await self.db.delete(template)
            await self.db.flush()

        return {
            "operation_type": "delete",
            "total": len(template_ids),
            "succeeded": len(templates_to_delete),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_update(
        self, updates: list[dict[str, Any]], dry_run: bool = False
    ) -> dict[str, Any]:
        """Atomically update multiple rotation templates.

        This operation is all-or-nothing: if any template doesn't exist or
        validation fails, the entire batch is rolled back.

        Args:
            updates: List of dicts, each with:
                - template_id: UUID of template to update
                - updates: Dict of field updates
            dry_run: If True, validate only without updating

        Returns:
            Dict with operation results:
            - operation_type: "update"
            - total: Number of requested updates
            - succeeded: Number of successful updates
            - failed: Number of failed updates
            - results: Per-template results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any template not found or validation fails
        """
        results = []
        templates_to_update = []

        # Phase 1: Validate all templates exist and collect updates
        for idx, update_item in enumerate(updates):
            template_id = update_item["template_id"]
            update_data = update_item["updates"]

            template = await self.get_template_by_id(template_id)
            if not template:
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": False,
                        "error": f"Template with ID {template_id} not found",
                    }
                )
            else:
                templates_to_update.append((idx, template_id, template, update_data))
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": True,
                        "error": None,
                    }
                )

        # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "update",
                "total": len(updates),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Apply updates (if not dry run)
        if not dry_run:
            for idx, template_id, template, update_data in templates_to_update:
                for field, value in update_data.items():
                    setattr(template, field, value)
            await self.db.flush()

        return {
            "operation_type": "update",
            "total": len(updates),
            "succeeded": len(templates_to_update),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }
