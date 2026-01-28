"""Rotation template service with business logic for patterns and preferences.

This service handles:
- Weekly pattern CRUD operations
- Rotation preference CRUD operations
- Atomic batch updates for patterns/preferences
- Business validation rules
"""

import asyncio
from datetime import datetime
from typing import Any, Union
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ActivityNotFoundError
from app.models.activity import Activity, ActivityCategory
from app.models.rotation_halfday_requirement import RotationHalfDayRequirement
from app.models.rotation_preference import RotationPreference
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.utils.activity_naming import activity_code_from_name, activity_display_abbrev
from app.schemas.rotation_template_gui import (
    HalfDayRequirementCreate,
    HalfDayRequirementResponse,
    RotationPreferenceCreate,
    RotationPreferenceResponse,
    RotationPreferenceUpdate,
    WeeklyGridUpdate,
    WeeklyPatternCreate,
    WeeklyPatternResponse,
)


class RotationTemplateService:
    """Service for rotation template operations including patterns and preferences.

    Supports both sync and async database sessions for flexibility in different
    execution contexts (production async, test sync).
    """

    def __init__(self, db: AsyncSession | Session):
        """Initialize service with database session.

        Args:
            db: Database session (async or sync)
        """
        self.db = db
        # Check if session is async by checking for AsyncSession type
        # OR by checking for async method signatures (for test wrappers)
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

    async def _delete(self, obj):
        """Delete an object, handling both sync and async sessions."""
        if self._is_async:
            await self.db.delete(obj)
        else:
            self.db.delete(obj)

    async def _flush(self):
        """Flush the session, handling both sync and async sessions."""
        if self._is_async:
            await self.db.flush()
        else:
            self.db.flush()

    async def _refresh(self, obj):
        """Refresh an object, handling both sync and async sessions."""
        if self._is_async:
            await self.db.refresh(obj)
        else:
            self.db.refresh(obj)

    async def _ensure_activity_for_template(self, template: RotationTemplate) -> None:
        """Create a specialty activity for outpatient templates if missing."""
        if (
            template.template_category != "rotation"
            or (template.rotation_type or "").lower() != "outpatient"
        ):
            return

        code = activity_code_from_name(template.name)
        display_abbrev = activity_display_abbrev(
            template.name,
            template.display_abbreviation,
            template.abbreviation,
        )

        existing = await self._execute(
            select(Activity).where(Activity.name == template.name)
        )
        if existing.scalar_one_or_none():
            return

        existing = await self._execute(
            select(Activity).where(Activity.code.ilike(code))
        )
        if existing.scalar_one_or_none():
            return

        activity = Activity(
            name=template.name,
            code=code,
            display_abbreviation=display_abbrev,
            activity_category=ActivityCategory.CLINICAL.value,
            font_color=template.font_color,
            background_color=template.background_color,
            requires_supervision=True,
            is_protected=False,
            counts_toward_clinical_hours=True,
            provides_supervision=False,
            counts_toward_physical_capacity=False,
            display_order=0,
        )
        self.db.add(activity)
        await self._flush()

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
        result = await self._execute(
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
        result = await self._execute(
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
        result = await self._execute(
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
        await self._execute(
            delete(WeeklyPattern).where(
                WeeklyPattern.rotation_template_id == template_id
            )
        )

        # Create new patterns
        now = datetime.utcnow()
        new_patterns = []
        for pattern_data in patterns:
            activity = await self._resolve_pattern_activity(
                pattern_data.activity_type,
                getattr(pattern_data, "activity_id", None),
            )
            pattern = WeeklyPattern(
                rotation_template_id=template_id,
                day_of_week=pattern_data.day_of_week,
                time_of_day=pattern_data.time_of_day,
                activity_type=pattern_data.activity_type,
                activity_id=activity.id,
                linked_template_id=pattern_data.linked_template_id,
                is_protected=pattern_data.is_protected,
                notes=pattern_data.notes,
                created_at=now,
                updated_at=now,
            )
            self.db.add(pattern)
            new_patterns.append(pattern)

        await self._flush()

        # Refresh to get IDs
        for pattern in new_patterns:
            await self._refresh(pattern)

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

            if not pattern.activity_type or not pattern.activity_type.strip():
                raise ValueError("activity_type is required for weekly pattern slots")

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

    async def _resolve_pattern_activity(
        self,
        activity_type: str | None,
        activity_id: UUID | None,
    ) -> Activity:
        """Resolve a weekly pattern activity to a real Activity record."""
        if activity_id:
            result = await self._execute(
                select(Activity).where(Activity.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            if activity:
                return activity
            raise ActivityNotFoundError(
                str(activity_id), context="weekly_patterns.activity_id"
            )

        if not activity_type or not activity_type.strip():
            raise ValueError("weekly pattern requires activity_type or activity_id")

        normalized = activity_type.strip()
        result = await self._execute(
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
        return activity

    # =========================================================================
    # Half-Day Requirement Operations
    # =========================================================================

    async def get_halfday_requirements(
        self, template_id: UUID
    ) -> RotationHalfDayRequirement | None:
        """Get half-day requirements for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            RotationHalfDayRequirement instance or None if not configured
        """
        result = await self._execute(
            select(RotationHalfDayRequirement).where(
                RotationHalfDayRequirement.rotation_template_id == template_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_halfday_requirements(
        self, template_id: UUID, data: HalfDayRequirementCreate
    ) -> RotationHalfDayRequirement:
        """Create or update half-day requirements for a template.

        If requirements already exist for this template, update them.
        Otherwise, create new requirements.

        Args:
            template_id: UUID of the rotation template
            data: HalfDayRequirementCreate schema with requirement values

        Returns:
            Created or updated RotationHalfDayRequirement instance

        Raises:
            ValueError: If template not found
        """
        # Verify template exists
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Check if requirements already exist
        existing = await self.get_halfday_requirements(template_id)

        now = datetime.utcnow()

        if existing:
            # Update existing requirements
            existing.fm_clinic_halfdays = data.fm_clinic_halfdays
            existing.specialty_halfdays = data.specialty_halfdays
            existing.specialty_name = data.specialty_name
            existing.academics_halfdays = data.academics_halfdays
            existing.elective_halfdays = data.elective_halfdays
            existing.min_consecutive_specialty = data.min_consecutive_specialty
            existing.prefer_combined_clinic_days = data.prefer_combined_clinic_days
            existing.updated_at = now
            await self._flush()
            await self._refresh(existing)
            return existing
        else:
            # Create new requirements
            requirements = RotationHalfDayRequirement(
                rotation_template_id=template_id,
                fm_clinic_halfdays=data.fm_clinic_halfdays,
                specialty_halfdays=data.specialty_halfdays,
                specialty_name=data.specialty_name,
                academics_halfdays=data.academics_halfdays,
                elective_halfdays=data.elective_halfdays,
                min_consecutive_specialty=data.min_consecutive_specialty,
                prefer_combined_clinic_days=data.prefer_combined_clinic_days,
                created_at=now,
                updated_at=now,
            )
            self.db.add(requirements)
            await self._flush()
            await self._refresh(requirements)
            return requirements

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
        result = await self._execute(
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
        await self._execute(
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

        await self._flush()

        # Refresh to get IDs
        for preference in new_preferences:
            await self._refresh(preference)

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
        """Commit the current transaction.

        Supports both sync and async sessions for test compatibility.
        """
        if hasattr(self.db, "commit"):
            result = self.db.commit()
            if result is not None:
                await result

    async def rollback(self) -> None:
        """Rollback the current transaction.

        Supports both sync and async sessions for test compatibility.
        """
        if hasattr(self.db, "rollback"):
            result = self.db.rollback()
            if result is not None:
                await result

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
                        "template_id": str(template_id),
                        "success": False,
                        "error": f"Template with ID {template_id} not found",
                    }
                )
            else:
                templates_to_delete.append((idx, template_id, template))
                results.append(
                    {
                        "index": idx,
                        "template_id": str(template_id),
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
                await self._delete(template)
            await self._flush()

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
                        "template_id": str(template_id),
                        "success": False,
                        "error": f"Template with ID {template_id} not found",
                    }
                )
            else:
                templates_to_update.append((idx, template_id, template, update_data))
                results.append(
                    {
                        "index": idx,
                        "template_id": str(template_id),
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
            await self._flush()

        return {
            "operation_type": "update",
            "total": len(updates),
            "succeeded": len(templates_to_update),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_create(
        self,
        templates_data: list[dict[str, Any]],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Atomically create multiple rotation templates.

        This operation is all-or-nothing: if any validation fails,
        the entire batch is rolled back.

        Args:
            templates_data: List of template data dicts
            dry_run: If True, validate only without creating

        Returns:
            Dict with operation results including created_ids

        Raises:
            ValueError: If validation fails
        """
        from app.schemas.rotation_template import RotationTemplateCreate

        results = []
        templates_to_create = []
        created_ids = []

        # Check for duplicate names within the batch
        names_in_batch = [t.get("name", "").strip().lower() for t in templates_data]
        seen_names = set()
        for idx, name in enumerate(names_in_batch):
            if name in seen_names:
                results.append(
                    {
                        "index": idx,
                        "template_id": None,
                        "success": False,
                        "error": f"Duplicate name in batch: '{templates_data[idx].get('name')}'",
                    }
                )
            else:
                seen_names.add(name)

        # If duplicates found, fail early
        if results:
            return {
                "operation_type": "create",
                "total": len(templates_data),
                "succeeded": 0,
                "failed": len(results),
                "results": results,
                "dry_run": dry_run,
                "created_ids": None,
            }

        # Check for name collisions with existing templates
        for idx, template_data in enumerate(templates_data):
            name = template_data.get("name", "").strip()
            existing = await self._execute(
                select(RotationTemplate).where(RotationTemplate.name == name)
            )
            if existing.scalar_one_or_none():
                results.append(
                    {
                        "index": idx,
                        "template_id": None,
                        "success": False,
                        "error": f"Template with name '{name}' already exists",
                    }
                )
            else:
                templates_to_create.append((idx, template_data))
                results.append(
                    {
                        "index": idx,
                        "template_id": None,
                        "success": True,
                        "error": None,
                    }
                )

        # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "create",
                "total": len(templates_data),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
                "created_ids": None,
            }

        # Phase 2: Create templates (if not dry run)
        if not dry_run:
            now = datetime.utcnow()
            for idx, template_data in templates_to_create:
                template = RotationTemplate(
                    **template_data,
                    created_at=now,
                )
                self.db.add(template)
                await self._flush()
                await self._refresh(template)
                await self._ensure_activity_for_template(template)
                created_ids.append(template.id)
                # Update result with created ID
                for r in results:
                    if r["index"] == idx:
                        r["template_id"] = template.id

        return {
            "operation_type": "create",
            "total": len(templates_data),
            "succeeded": len(templates_to_create),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
            "created_ids": created_ids if created_ids else None,
        }

    async def check_conflicts(
        self,
        template_ids: list[UUID],
        operation: str,
    ) -> dict[str, Any]:
        """Check for conflicts before performing operations.

        Args:
            template_ids: List of template IDs to check
            operation: Operation type ('delete', 'archive', 'update')

        Returns:
            Dict with conflicts and whether operation can proceed
        """
        from app.models.assignment import Assignment

        conflicts = []

        for template_id in template_ids:
            template = await self.get_template_by_id(template_id)
            if not template:
                continue

            # Check for existing assignments
            if operation in ("delete", "archive"):
                assignment_count = await self._execute(
                    select(Assignment).where(
                        Assignment.rotation_template_id == template_id
                    )
                )
                assignments = list(assignment_count.scalars().all())
                if assignments:
                    conflicts.append(
                        {
                            "template_id": str(template_id),
                            "template_name": template.name,
                            "conflict_type": "has_assignments",
                            "description": f"Template has {len(assignments)} existing assignments",
                            "severity": "warning"
                            if operation == "archive"
                            else "error",
                            "blocking": operation == "delete",
                        }
                    )

        has_conflicts = len(conflicts) > 0
        can_proceed = not any(c["blocking"] for c in conflicts)

        return {
            "has_conflicts": has_conflicts,
            "conflicts": conflicts,
            "can_proceed": can_proceed,
        }

    async def export_templates(
        self,
        template_ids: list[UUID],
        include_patterns: bool = True,
        include_preferences: bool = True,
    ) -> dict[str, Any]:
        """Export templates with their patterns and preferences.

        Args:
            template_ids: List of template IDs to export
            include_patterns: Include weekly patterns
            include_preferences: Include preferences

        Returns:
            Dict with exported template data
        """
        templates_data = []

        for template_id in template_ids:
            template = await self.get_template_with_relations(template_id)
            if not template:
                continue

            export_item = {
                "template": {
                    "id": str(template.id),
                    "name": template.name,
                    "rotation_type": template.rotation_type,
                    "abbreviation": template.abbreviation,
                    "display_abbreviation": template.display_abbreviation,
                    "font_color": template.font_color,
                    "background_color": template.background_color,
                    "clinic_location": template.clinic_location,
                    "max_residents": template.max_residents,
                    "requires_specialty": template.requires_specialty,
                    "requires_procedure_credential": template.requires_procedure_credential,
                    "supervision_required": template.supervision_required,
                    "max_supervision_ratio": template.max_supervision_ratio,
                    "created_at": template.created_at.isoformat()
                    if template.created_at
                    else None,
                },
                "patterns": None,
                "preferences": None,
            }

            if include_patterns and template.weekly_patterns:
                export_item["patterns"] = [
                    {
                        "day_of_week": p.day_of_week,
                        "time_of_day": p.time_of_day,
                        "activity_type": p.activity_type,
                        "is_protected": p.is_protected,
                        "notes": p.notes,
                    }
                    for p in template.weekly_patterns
                ]

            if include_preferences and template.preferences:
                export_item["preferences"] = [
                    {
                        "preference_type": p.preference_type,
                        "weight": p.weight,
                        "config_json": p.config_json,
                        "is_active": p.is_active,
                        "description": p.description,
                    }
                    for p in template.preferences
                ]

            templates_data.append(export_item)

        return {
            "templates": templates_data,
            "exported_at": datetime.utcnow().isoformat(),
            "total": len(templates_data),
        }

    # =========================================================================
    # Archive/Restore Operations
    # =========================================================================

    async def archive_template(
        self, template_id: UUID, user_id: str
    ) -> RotationTemplate:
        """Archive a single rotation template (soft delete).

        Args:
            template_id: UUID of template to archive
            user_id: ID of user performing the archive

        Returns:
            Archived RotationTemplate

        Raises:
            ValueError: If template not found or already archived
        """
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        if template.is_archived:
            raise ValueError(f"Template with ID {template_id} is already archived")

        template.is_archived = True
        template.archived_at = datetime.utcnow()
        template.archived_by = user_id

        await self._flush()
        await self._refresh(template)

        return template

    async def restore_template(self, template_id: UUID) -> RotationTemplate:
        """Restore an archived rotation template.

        Args:
            template_id: UUID of template to restore

        Returns:
            Restored RotationTemplate

        Raises:
            ValueError: If template not found or not archived
        """
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        if not template.is_archived:
            raise ValueError(f"Template with ID {template_id} is not archived")

        template.is_archived = False
        template.archived_at = None
        template.archived_by = None

        await self._flush()
        await self._refresh(template)

        return template

    async def batch_archive(
        self, template_ids: list[UUID], user_id: str, dry_run: bool = False
    ) -> dict[str, Any]:
        """Atomically archive multiple rotation templates.

        This operation is all-or-nothing: if any template doesn't exist,
        is already archived, or has blocking issues, the entire batch is rolled back.

        Args:
            template_ids: List of template UUIDs to archive
            user_id: ID of user performing the archive
            dry_run: If True, validate only without archiving

        Returns:
            Dict with operation results:
            - operation_type: "archive"
            - total: Number of requested archives
            - succeeded: Number of successful archives
            - failed: Number of failed archives
            - results: Per-template results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any template not found or already archived (atomic rollback)
        """
        results = []
        templates_to_archive = []

        # Phase 1: Validate all templates exist and are not archived
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
            elif template.is_archived:
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": False,
                        "error": f"Template with ID {template_id} is already archived",
                    }
                )
            else:
                templates_to_archive.append((idx, template_id, template))
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
                "operation_type": "archive",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Archive templates (if not dry run)
        if not dry_run:
            now = datetime.utcnow()
            for idx, template_id, template in templates_to_archive:
                template.is_archived = True
                template.archived_at = now
                template.archived_by = user_id
            await self._flush()

        return {
            "operation_type": "archive",
            "total": len(template_ids),
            "succeeded": len(templates_to_archive),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_restore(
        self, template_ids: list[UUID], dry_run: bool = False
    ) -> dict[str, Any]:
        """Atomically restore multiple archived rotation templates.

        This operation is all-or-nothing: if any template doesn't exist
        or is not archived, the entire batch is rolled back.

        Args:
            template_ids: List of template UUIDs to restore
            dry_run: If True, validate only without restoring

        Returns:
            Dict with operation results:
            - operation_type: "restore"
            - total: Number of requested restores
            - succeeded: Number of successful restores
            - failed: Number of failed restores
            - results: Per-template results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any template not found or not archived (atomic rollback)
        """
        results = []
        templates_to_restore = []

        # Phase 1: Validate all templates exist and are archived
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
            elif not template.is_archived:
                results.append(
                    {
                        "index": idx,
                        "template_id": template_id,
                        "success": False,
                        "error": f"Template with ID {template_id} is not archived",
                    }
                )
            else:
                templates_to_restore.append((idx, template_id, template))
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
                "operation_type": "restore",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Restore templates (if not dry run)
        if not dry_run:
            for idx, template_id, template in templates_to_restore:
                template.is_archived = False
                template.archived_at = None
                template.archived_by = None
            await self._flush()

        return {
            "operation_type": "restore",
            "total": len(template_ids),
            "succeeded": len(templates_to_restore),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_apply_patterns(
        self,
        template_ids: list[UUID],
        patterns: list[WeeklyPatternCreate],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Apply the same weekly pattern to multiple templates atomically.

        This is useful for bulk operations like applying a standard clinic
        pattern to all clinic templates.

        Args:
            template_ids: List of template UUIDs to update
            patterns: List of patterns to apply to each template
            dry_run: If True, validate only without updating

        Returns:
            Dict with operation results

        Raises:
            ValueError: If any template not found or validation fails
        """
        results = []
        templates_to_update = []

        # Validate patterns first
        try:
            self._validate_patterns(patterns)
        except ValueError as e:
            return {
                "operation_type": "batch_apply_patterns",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(template_ids),
                "results": [
                    {
                        "index": idx,
                        "template_id": tid,
                        "success": False,
                        "error": f"Pattern validation failed: {str(e)}",
                    }
                    for idx, tid in enumerate(template_ids)
                ],
                "dry_run": dry_run,
            }

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
                templates_to_update.append((idx, template_id))
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
                "operation_type": "batch_apply_patterns",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Apply patterns (if not dry run)
        if not dry_run:
            for idx, template_id in templates_to_update:
                await self.replace_patterns(template_id, patterns)

        return {
            "operation_type": "batch_apply_patterns",
            "total": len(template_ids),
            "succeeded": len(templates_to_update),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_apply_preferences(
        self,
        template_ids: list[UUID],
        preferences: list[RotationPreferenceCreate],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Apply the same preferences to multiple templates atomically.

        This is useful for bulk operations like applying standard
        preference configurations to all templates of a certain type.

        Args:
            template_ids: List of template UUIDs to update
            preferences: List of preferences to apply to each template
            dry_run: If True, validate only without updating

        Returns:
            Dict with operation results

        Raises:
            ValueError: If any template not found or validation fails
        """
        results = []
        templates_to_update = []

        # Validate preferences first
        try:
            self._validate_preferences(preferences)
        except ValueError as e:
            return {
                "operation_type": "batch_apply_preferences",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(template_ids),
                "results": [
                    {
                        "index": idx,
                        "template_id": tid,
                        "success": False,
                        "error": f"Preference validation failed: {str(e)}",
                    }
                    for idx, tid in enumerate(template_ids)
                ],
                "dry_run": dry_run,
            }

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
                templates_to_update.append((idx, template_id))
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
                "operation_type": "batch_apply_preferences",
                "total": len(template_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

        # Phase 2: Apply preferences (if not dry run)
        if not dry_run:
            for idx, template_id in templates_to_update:
                await self.replace_preferences(template_id, preferences)

        return {
            "operation_type": "batch_apply_preferences",
            "total": len(template_ids),
            "succeeded": len(templates_to_update),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    async def batch_update_weekly_patterns(
        self,
        template_ids: list[UUID],
        mode: str,
        slots: list[dict],
        week_numbers: list[int] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Bulk update weekly patterns across multiple templates.

        Supports two modes:
        - overlay: Only modifies specified slots, leaves others unchanged
        - replace: Replaces entire pattern with the provided slots

        Args:
            template_ids: List of template UUIDs to update
            mode: "overlay" or "replace"
            slots: List of slot dictionaries with day_of_week, time_of_day, etc.
            week_numbers: List of weeks to target (1-4). None = all weeks
            dry_run: If True, validate without applying changes

        Returns:
            Dict with operation results including success/failure per template
        """
        results = []
        templates_found = []

        # Phase 1: Validate all templates exist
        for template_id in template_ids:
            template = await self.get_template_by_id(template_id)
            if not template:
                results.append(
                    {
                        "template_id": template_id,
                        "template_name": "Unknown",
                        "success": False,
                        "slots_modified": 0,
                        "error": f"Template with ID {template_id} not found",
                    }
                )
            else:
                templates_found.append(template)
                results.append(
                    {
                        "template_id": template_id,
                        "template_name": template.name,
                        "success": True,
                        "slots_modified": 0,
                        "error": None,
                    }
                )

        # Check for failures in validation
        failed_count = sum(1 for r in results if not r["success"])
        if failed_count > 0:
            return {
                "total_templates": len(template_ids),
                "successful": 0,
                "failed": failed_count,
                "results": results,
            }

        # Phase 2: Apply pattern updates (if not dry run)
        if not dry_run:
            for idx, template in enumerate(templates_found):
                try:
                    slots_modified = await self._apply_pattern_update(
                        template_id=template.id,
                        mode=mode,
                        slots=slots,
                        week_numbers=week_numbers,
                    )
                    results[idx]["slots_modified"] = slots_modified
                except Exception as e:
                    results[idx]["success"] = False
                    results[idx]["error"] = str(e)

        # Recalculate success/failure counts
        successful = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])

        return {
            "total_templates": len(template_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
        }

    async def _apply_pattern_update(
        self,
        template_id: UUID,
        mode: str,
        slots: list[dict],
        week_numbers: list[int] | None = None,
    ) -> int:
        """Apply pattern update to a single template.

        Args:
            template_id: Template UUID
            mode: "overlay" or "replace"
            slots: Slot updates to apply
            week_numbers: Target weeks (None = all weeks)

        Returns:
            Number of slots modified
        """
        slots_modified = 0

        if mode == "replace":
            # Delete existing patterns (for target weeks or all)
            if week_numbers:
                for week in week_numbers:
                    stmt = delete(WeeklyPattern).where(
                        WeeklyPattern.rotation_template_id == template_id,
                        WeeklyPattern.week_number == week,
                    )
                    await self._execute(stmt)
            else:
                stmt = delete(WeeklyPattern).where(
                    WeeklyPattern.rotation_template_id == template_id
                )
                await self._execute(stmt)

        # Apply each slot
        for slot_data in slots:
            day_of_week = slot_data["day_of_week"]
            time_of_day = slot_data["time_of_day"]
            linked_template_id = slot_data.get("linked_template_id")
            activity_type = slot_data.get("activity_type")
            activity_id = slot_data.get("activity_id")
            is_protected = slot_data.get("is_protected")
            notes = slot_data.get("notes")

            resolved_activity = None
            activity_type_value = activity_type
            if activity_type is not None or activity_id is not None:
                resolved_activity = await self._resolve_pattern_activity(
                    activity_type, activity_id
                )
                if activity_type_value is None:
                    activity_type_value = resolved_activity.code

            # Determine which weeks to apply to
            target_weeks = week_numbers if week_numbers else [None]

            for week_num in target_weeks:
                if mode == "overlay":
                    # Find existing pattern for this slot/week
                    stmt = select(WeeklyPattern).where(
                        WeeklyPattern.rotation_template_id == template_id,
                        WeeklyPattern.day_of_week == day_of_week,
                        WeeklyPattern.time_of_day == time_of_day,
                        WeeklyPattern.week_number == week_num,
                    )
                    result = await self._execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update existing pattern
                        if linked_template_id is not None:
                            existing.linked_template_id = linked_template_id
                        if activity_type_value is not None:
                            existing.activity_type = activity_type_value
                        if resolved_activity is not None:
                            existing.activity_id = resolved_activity.id
                        if is_protected is not None:
                            existing.is_protected = is_protected
                        if notes is not None:
                            existing.notes = notes
                        slots_modified += 1
                    else:
                        # Create new pattern
                        if resolved_activity is None:
                            raise ValueError(
                                "activity_type or activity_id required for new weekly pattern"
                            )
                        new_pattern = WeeklyPattern(
                            rotation_template_id=template_id,
                            day_of_week=day_of_week,
                            time_of_day=time_of_day,
                            week_number=week_num,
                            linked_template_id=linked_template_id,
                            activity_type=activity_type_value or resolved_activity.code,
                            activity_id=resolved_activity.id,
                            is_protected=is_protected or False,
                            notes=notes,
                        )
                        self.db.add(new_pattern)
                        slots_modified += 1
                else:
                    # Replace mode - create new patterns
                    if resolved_activity is None:
                        raise ValueError(
                            "activity_type or activity_id required for weekly pattern"
                        )
                    new_pattern = WeeklyPattern(
                        rotation_template_id=template_id,
                        day_of_week=day_of_week,
                        time_of_day=time_of_day,
                        week_number=week_num,
                        linked_template_id=linked_template_id,
                        activity_type=activity_type_value or resolved_activity.code,
                        activity_id=resolved_activity.id,
                        is_protected=is_protected or False,
                        notes=notes,
                    )
                    self.db.add(new_pattern)
                    slots_modified += 1

        await self._flush()
        return slots_modified
