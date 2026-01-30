"""Activity service for slot-level schedule events.

This service handles:
- Activity CRUD operations
- Activity requirement CRUD for rotation templates
- Business validation rules
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.schemas.activity import (
    ActivityCreate,
    ActivityRequirementCreate,
    ActivityRequirementResponse,
    ActivityResponse,
    ActivityUpdate,
)


class ActivityService:
    """Service for activity operations.

    Supports both sync and async database sessions for flexibility in different
    execution contexts (production async, test sync).
    """

    def __init__(self, db: AsyncSession | Session) -> None:
        """Initialize service with database session.

        Args:
            db: Database session (async or sync)
        """
        self.db = db
        self._is_async = (
            isinstance(db, AsyncSession)
            or hasattr(db, "_session")  # Test wrapper detection
        )

    async def _execute(self, stmt):
        """Execute a statement, handling both sync and async sessions."""
        if self._is_async:
            return await self.db.execute(stmt)
        else:
            return self.db.execute(stmt)

    async def _flush(self) -> None:
        """Flush the session."""
        if self._is_async:
            await self.db.flush()
        else:
            self.db.flush()

    async def _refresh(self, obj) -> None:
        """Refresh an object."""
        if self._is_async:
            await self.db.refresh(obj)
        else:
            self.db.refresh(obj)

    async def _delete(self, obj) -> None:
        """Delete an object."""
        if self._is_async:
            await self.db.delete(obj)
        else:
            self.db.delete(obj)

            # =========================================================================
            # Activity CRUD
            # =========================================================================

    async def list_activities(
        self,
        category: str | None = None,
        include_archived: bool = False,
    ) -> list[Activity]:
        """List all activities with optional filtering.

        Args:
            category: Filter by activity_category
            include_archived: Include archived activities

        Returns:
            List of Activity models
        """
        stmt = select(Activity).order_by(Activity.display_order, Activity.name)

        if not include_archived:
            stmt = stmt.where(Activity.is_archived == False)  # noqa: E712

        if category:
            stmt = stmt.where(Activity.activity_category == category)

        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_activity_by_id(self, activity_id: UUID) -> Activity | None:
        """Get activity by ID.

        Args:
            activity_id: UUID of the activity

        Returns:
            Activity or None if not found
        """
        result = await self._execute(select(Activity).where(Activity.id == activity_id))
        return result.scalar_one_or_none()

    async def get_activity_by_code(self, code: str) -> Activity | None:
        """Get activity by code.

        Args:
            code: Activity code (e.g., 'fm_clinic')

        Returns:
            Activity or None if not found
        """
        result = await self._execute(
            select(Activity).where(Activity.code == code.lower())
        )
        return result.scalar_one_or_none()

    async def create_activity(self, data: ActivityCreate) -> Activity:
        """Create a new activity.

        Args:
            data: Activity creation data

        Returns:
            Created Activity model

        Raises:
            ValueError: If activity with same name or code exists
        """
        # Check for existing name
        existing_name = await self._execute(
            select(Activity).where(Activity.name == data.name)
        )
        if existing_name.scalar_one_or_none():
            raise ValueError(f"Activity with name '{data.name}' already exists")

            # Check for existing code
        existing_code = await self._execute(
            select(Activity).where(Activity.code == data.code)
        )
        if existing_code.scalar_one_or_none():
            raise ValueError(f"Activity with code '{data.code}' already exists")

        activity_kwargs = {
            "name": data.name,
            "code": data.code,
            "display_abbreviation": data.display_abbreviation,
            "activity_category": data.activity_category,
            "procedure_id": data.procedure_id,
            "font_color": data.font_color,
            "background_color": data.background_color,
            "requires_supervision": data.requires_supervision,
            "is_protected": data.is_protected,
            "counts_toward_clinical_hours": data.counts_toward_clinical_hours,
            "display_order": data.display_order,
        }
        if data.capacity_units is not None:
            activity_kwargs["capacity_units"] = data.capacity_units

        activity = Activity(**activity_kwargs)
        self.db.add(activity)
        await self._flush()
        await self._refresh(activity)
        return activity

    async def update_activity(
        self,
        activity_id: UUID,
        data: ActivityUpdate,
    ) -> Activity | None:
        """Update an activity.

        Args:
            activity_id: UUID of the activity
            data: Update data (only non-None fields are updated)

        Returns:
            Updated Activity or None if not found

        Raises:
            ValueError: If name or code conflicts with existing activity
        """
        activity = await self.get_activity_by_id(activity_id)
        if not activity:
            return None

            # Check for name conflict if updating name
        if data.name is not None and data.name != activity.name:
            existing = await self._execute(
                select(Activity).where(
                    Activity.name == data.name,
                    Activity.id != activity_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Activity with name '{data.name}' already exists")
            activity.name = data.name

            # Check for code conflict if updating code
        if data.code is not None and data.code != activity.code:
            existing = await self._execute(
                select(Activity).where(
                    Activity.code == data.code,
                    Activity.id != activity_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Activity with code '{data.code}' already exists")
            activity.code = data.code

            # Update other fields if provided
        if data.display_abbreviation is not None:
            activity.display_abbreviation = data.display_abbreviation
        if data.activity_category is not None:
            activity.activity_category = data.activity_category
        if data.procedure_id is not None:
            activity.procedure_id = data.procedure_id
        if data.font_color is not None:
            activity.font_color = data.font_color
        if data.background_color is not None:
            activity.background_color = data.background_color
        if data.requires_supervision is not None:
            activity.requires_supervision = data.requires_supervision
        if data.is_protected is not None:
            activity.is_protected = data.is_protected
        if data.counts_toward_clinical_hours is not None:
            activity.counts_toward_clinical_hours = data.counts_toward_clinical_hours
        if data.display_order is not None:
            activity.display_order = data.display_order
        if data.capacity_units is not None:
            activity.capacity_units = data.capacity_units

        await self._flush()
        await self._refresh(activity)
        return activity

    async def archive_activity(self, activity_id: UUID) -> Activity | None:
        """Soft delete an activity.

        Args:
            activity_id: UUID of the activity

        Returns:
            Archived Activity or None if not found
        """
        activity = await self.get_activity_by_id(activity_id)
        if not activity:
            return None

        activity.is_archived = True
        activity.archived_at = datetime.utcnow()
        await self._flush()
        await self._refresh(activity)
        return activity

    async def delete_activity(self, activity_id: UUID) -> bool:
        """Hard delete an activity (fails if in use).

        Args:
            activity_id: UUID of the activity

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If activity is in use by weekly patterns or requirements
        """
        activity = await self.get_activity_by_id(activity_id)
        if not activity:
            return False

            # Check if in use by activity requirements
        result = await self._execute(
            select(RotationActivityRequirement)
            .where(RotationActivityRequirement.activity_id == activity_id)
            .limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError(
                f"Activity '{activity.name}' is in use by rotation requirements"
            )

            # Note: WeeklyPattern.activity_id FK has ondelete=RESTRICT
            # so if any patterns use this activity, the delete will fail at DB level

        await self._delete(activity)
        await self._flush()
        return True

        # =========================================================================
        # Activity Requirements for Rotation Templates
        # =========================================================================

    async def list_requirements_for_template(
        self,
        template_id: UUID,
    ) -> list[RotationActivityRequirement]:
        """Get all activity requirements for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            List of RotationActivityRequirement models with activity loaded
        """
        result = await self._execute(
            select(RotationActivityRequirement)
            .options(selectinload(RotationActivityRequirement.activity))
            .where(RotationActivityRequirement.rotation_template_id == template_id)
            .order_by(RotationActivityRequirement.priority.desc())
        )
        return list(result.scalars().all())

    async def get_requirement_by_id(
        self,
        requirement_id: UUID,
    ) -> RotationActivityRequirement | None:
        """Get a single activity requirement by ID.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            RotationActivityRequirement or None
        """
        result = await self._execute(
            select(RotationActivityRequirement)
            .options(selectinload(RotationActivityRequirement.activity))
            .where(RotationActivityRequirement.id == requirement_id)
        )
        return result.scalar_one_or_none()

    async def create_requirement(
        self,
        template_id: UUID,
        data: ActivityRequirementCreate,
    ) -> RotationActivityRequirement:
        """Create an activity requirement for a rotation template.

        Args:
            template_id: UUID of the rotation template
            data: Requirement creation data

        Returns:
            Created RotationActivityRequirement model

        Raises:
            ValueError: If template or activity not found, or duplicate requirement
        """
        # Verify template exists
        result = await self._execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError(f"Rotation template {template_id} not found")

            # Verify activity exists
        activity = await self.get_activity_by_id(data.activity_id)
        if not activity:
            raise ValueError(f"Activity {data.activity_id} not found")

        requirement = RotationActivityRequirement(
            rotation_template_id=template_id,
            activity_id=data.activity_id,
            min_halfdays=data.min_halfdays,
            max_halfdays=data.max_halfdays,
            target_halfdays=data.target_halfdays,
            applicable_weeks=data.applicable_weeks,
            prefer_full_days=data.prefer_full_days,
            preferred_days=data.preferred_days,
            avoid_days=data.avoid_days,
            priority=data.priority,
        )
        self.db.add(requirement)
        await self._flush()
        await self._refresh(requirement)
        return requirement

    async def update_requirements_bulk(
        self,
        template_id: UUID,
        requirements: list[ActivityRequirementCreate],
    ) -> list[RotationActivityRequirement]:
        """Replace all activity requirements for a rotation template.

        This is an atomic operation - all old requirements are deleted
        and new ones are created.

        Args:
            template_id: UUID of the rotation template
            requirements: List of new requirements

        Returns:
            List of created RotationActivityRequirement models

        Raises:
            ValueError: If template or any activity not found
        """
        # Verify template exists
        result = await self._execute(
            select(RotationTemplate).where(RotationTemplate.id == template_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError(f"Rotation template {template_id} not found")

            # Verify all activities exist
        for req in requirements:
            activity = await self.get_activity_by_id(req.activity_id)
            if not activity:
                raise ValueError(f"Activity {req.activity_id} not found")

                # Delete existing requirements
        await self._execute(
            delete(RotationActivityRequirement).where(
                RotationActivityRequirement.rotation_template_id == template_id
            )
        )

        # Create new requirements
        created = []
        for req in requirements:
            requirement = RotationActivityRequirement(
                rotation_template_id=template_id,
                activity_id=req.activity_id,
                min_halfdays=req.min_halfdays,
                max_halfdays=req.max_halfdays,
                target_halfdays=req.target_halfdays,
                applicable_weeks=req.applicable_weeks,
                prefer_full_days=req.prefer_full_days,
                preferred_days=req.preferred_days,
                avoid_days=req.avoid_days,
                priority=req.priority,
            )
            self.db.add(requirement)
            created.append(requirement)

        await self._flush()

        # Refresh and return with activity loaded
        return await self.list_requirements_for_template(template_id)

    async def delete_requirement(self, requirement_id: UUID) -> bool:
        """Delete a single activity requirement.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            True if deleted, False if not found
        """
        requirement = await self.get_requirement_by_id(requirement_id)
        if not requirement:
            return False

        await self._delete(requirement)
        await self._flush()
        return True
