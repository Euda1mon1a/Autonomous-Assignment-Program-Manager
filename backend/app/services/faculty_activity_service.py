"""Faculty activity service for weekly template and override management.

This service handles:
- Faculty weekly template CRUD (default patterns per person)
- Faculty weekly override CRUD (week-specific exceptions)
- Permitted activities lookup by role
- Effective week computation (template + overrides merged)
- Faculty matrix view for all-faculty scheduling display
"""

from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity
from app.models.faculty_weekly_override import FacultyWeeklyOverride
from app.models.faculty_weekly_template import FacultyWeeklyTemplate
from app.models.person import FacultyRole, Person


class FacultyActivityService:
    """Service for faculty weekly activity operations.

    Supports both sync and async database sessions for flexibility in different
    execution contexts (production async, test sync).

    Key concepts:
    - Template: Default weekly pattern for a faculty member (7x2 grid)
    - Override: Week-specific exception that replaces template slot
    - Effective: Merged view of template + overrides for a specific week
    - Locked: Hard constraint that solver cannot change
    - Priority: Soft preference for solver optimization
    """

    def __init__(self, db: AsyncSession | Session):
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

    async def _flush(self):
        """Flush the session."""
        if self._is_async:
            await self.db.flush()
        else:
            self.db.flush()

    async def _refresh(self, obj):
        """Refresh an object."""
        if self._is_async:
            await self.db.refresh(obj)
        else:
            self.db.refresh(obj)

    async def _delete(self, obj):
        """Delete an object."""
        if self._is_async:
            await self.db.delete(obj)
        else:
            self.db.delete(obj)

    # =========================================================================
    # Faculty Weekly Template CRUD
    # =========================================================================

    async def get_template(
        self,
        person_id: UUID,
        week_number: int | None = None,
    ) -> list[FacultyWeeklyTemplate]:
        """Get weekly template slots for a faculty member.

        Args:
            person_id: Faculty member's ID
            week_number: Filter by week (1-4), or None for all weeks

        Returns:
            List of FacultyWeeklyTemplate objects
        """
        stmt = (
            select(FacultyWeeklyTemplate)
            .options(selectinload(FacultyWeeklyTemplate.activity))
            .where(FacultyWeeklyTemplate.person_id == person_id)
            .order_by(
                FacultyWeeklyTemplate.week_number.nullsfirst(),
                FacultyWeeklyTemplate.day_of_week,
                FacultyWeeklyTemplate.time_of_day,
            )
        )

        if week_number is not None:
            # Get week-specific OR week=NULL (all weeks) patterns
            stmt = stmt.where(
                or_(
                    FacultyWeeklyTemplate.week_number == week_number,
                    FacultyWeeklyTemplate.week_number.is_(None),
                )
            )

        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_template_slot(
        self,
        person_id: UUID,
        day_of_week: int,
        time_of_day: str,
        week_number: int | None = None,
    ) -> FacultyWeeklyTemplate | None:
        """Get a specific template slot.

        Args:
            person_id: Faculty member's ID
            day_of_week: 0-6 (Sunday-Saturday)
            time_of_day: "AM" or "PM"
            week_number: Week 1-4 or None for all-weeks pattern

        Returns:
            Template slot or None
        """
        stmt = (
            select(FacultyWeeklyTemplate)
            .options(selectinload(FacultyWeeklyTemplate.activity))
            .where(
                FacultyWeeklyTemplate.person_id == person_id,
                FacultyWeeklyTemplate.day_of_week == day_of_week,
                FacultyWeeklyTemplate.time_of_day == time_of_day,
            )
        )

        if week_number is None:
            stmt = stmt.where(FacultyWeeklyTemplate.week_number.is_(None))
        else:
            stmt = stmt.where(FacultyWeeklyTemplate.week_number == week_number)

        result = await self._execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_template_slot(
        self,
        person_id: UUID,
        day_of_week: int,
        time_of_day: str,
        week_number: int | None,
        activity_id: UUID | None,
        is_locked: bool = False,
        priority: int = 50,
        notes: str | None = None,
    ) -> FacultyWeeklyTemplate:
        """Create or update a template slot.

        Args:
            person_id: Faculty member's ID
            day_of_week: 0-6 (Sunday-Saturday)
            time_of_day: "AM" or "PM"
            week_number: Week 1-4 or None for all weeks
            activity_id: Activity UUID or None to clear
            is_locked: Hard constraint flag
            priority: Soft preference 0-100
            notes: Optional notes

        Returns:
            Created or updated FacultyWeeklyTemplate
        """
        # Check if slot exists
        existing = await self.get_template_slot(
            person_id, day_of_week, time_of_day, week_number
        )

        if existing:
            # Update existing
            existing.activity_id = activity_id
            existing.is_locked = is_locked
            existing.priority = priority
            existing.notes = notes
            existing.updated_at = datetime.utcnow()
            await self._flush()
            await self._refresh(existing)
            return existing
        else:
            # Create new
            template = FacultyWeeklyTemplate(
                person_id=person_id,
                day_of_week=day_of_week,
                time_of_day=time_of_day,
                week_number=week_number,
                activity_id=activity_id,
                is_locked=is_locked,
                priority=priority,
                notes=notes,
            )
            self.db.add(template)
            await self._flush()
            await self._refresh(template)
            return template

    async def update_template_bulk(
        self,
        person_id: UUID,
        slots: list[dict[str, Any]],
        clear_existing: bool = False,
    ) -> list[FacultyWeeklyTemplate]:
        """Bulk update template slots for a faculty member.

        Args:
            person_id: Faculty member's ID
            slots: List of slot data dicts with keys:
                - day_of_week: int
                - time_of_day: str
                - week_number: int | None
                - activity_id: UUID | None
                - is_locked: bool (optional, default False)
                - priority: int (optional, default 50)
                - notes: str | None (optional)
            clear_existing: If True, delete all existing slots first

        Returns:
            List of created/updated FacultyWeeklyTemplate objects
        """
        if clear_existing:
            # Delete all existing templates for this person
            delete_stmt = delete(FacultyWeeklyTemplate).where(
                FacultyWeeklyTemplate.person_id == person_id
            )
            await self._execute(delete_stmt)

        results = []
        for slot in slots:
            template = await self.upsert_template_slot(
                person_id=person_id,
                day_of_week=slot["day_of_week"],
                time_of_day=slot["time_of_day"],
                week_number=slot.get("week_number"),
                activity_id=slot.get("activity_id"),
                is_locked=slot.get("is_locked", False),
                priority=slot.get("priority", 50),
                notes=slot.get("notes"),
            )
            results.append(template)

        return results

    async def delete_template_slot(
        self,
        person_id: UUID,
        day_of_week: int,
        time_of_day: str,
        week_number: int | None = None,
    ) -> bool:
        """Delete a specific template slot.

        Returns:
            True if deleted, False if not found
        """
        existing = await self.get_template_slot(
            person_id, day_of_week, time_of_day, week_number
        )
        if existing:
            await self._delete(existing)
            await self._flush()
            return True
        return False

    # =========================================================================
    # Faculty Weekly Override CRUD
    # =========================================================================

    async def get_overrides(
        self,
        person_id: UUID,
        week_start: date,
    ) -> list[FacultyWeeklyOverride]:
        """Get overrides for a faculty member for a specific week.

        Args:
            person_id: Faculty member's ID
            week_start: Monday of the week

        Returns:
            List of FacultyWeeklyOverride objects
        """
        stmt = (
            select(FacultyWeeklyOverride)
            .options(selectinload(FacultyWeeklyOverride.activity))
            .where(
                FacultyWeeklyOverride.person_id == person_id,
                FacultyWeeklyOverride.effective_date == week_start,
            )
            .order_by(
                FacultyWeeklyOverride.day_of_week,
                FacultyWeeklyOverride.time_of_day,
            )
        )

        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_override(
        self,
        person_id: UUID,
        week_start: date,
        day_of_week: int,
        time_of_day: str,
    ) -> FacultyWeeklyOverride | None:
        """Get a specific override.

        Args:
            person_id: Faculty member's ID
            week_start: Monday of the week
            day_of_week: 0-6 (Sunday-Saturday)
            time_of_day: "AM" or "PM"

        Returns:
            Override or None
        """
        stmt = (
            select(FacultyWeeklyOverride)
            .options(selectinload(FacultyWeeklyOverride.activity))
            .where(
                FacultyWeeklyOverride.person_id == person_id,
                FacultyWeeklyOverride.effective_date == week_start,
                FacultyWeeklyOverride.day_of_week == day_of_week,
                FacultyWeeklyOverride.time_of_day == time_of_day,
            )
        )

        result = await self._execute(stmt)
        return result.scalar_one_or_none()

    async def create_override(
        self,
        person_id: UUID,
        week_start: date,
        day_of_week: int,
        time_of_day: str,
        activity_id: UUID | None,
        is_locked: bool = False,
        override_reason: str | None = None,
        created_by: UUID | None = None,
    ) -> FacultyWeeklyOverride:
        """Create or replace an override for a specific slot.

        Args:
            person_id: Faculty member's ID
            week_start: Monday of the week
            day_of_week: 0-6 (Sunday-Saturday)
            time_of_day: "AM" or "PM"
            activity_id: Activity UUID or None to clear
            is_locked: Hard constraint flag
            override_reason: Why this override was created
            created_by: Who created this override

        Returns:
            Created FacultyWeeklyOverride
        """
        # Delete existing override if any
        existing = await self.get_override(person_id, week_start, day_of_week, time_of_day)
        if existing:
            await self._delete(existing)

        # Create new override
        override = FacultyWeeklyOverride(
            person_id=person_id,
            effective_date=week_start,
            day_of_week=day_of_week,
            time_of_day=time_of_day,
            activity_id=activity_id,
            is_locked=is_locked,
            override_reason=override_reason,
            created_by=created_by,
        )
        self.db.add(override)
        await self._flush()
        await self._refresh(override)
        return override

    async def delete_override(self, override_id: UUID) -> bool:
        """Delete an override by ID.

        Returns:
            True if deleted, False if not found
        """
        stmt = select(FacultyWeeklyOverride).where(
            FacultyWeeklyOverride.id == override_id
        )
        result = await self._execute(stmt)
        override = result.scalar_one_or_none()

        if override:
            await self._delete(override)
            await self._flush()
            return True
        return False

    # =========================================================================
    # Effective Week Computation
    # =========================================================================

    async def get_effective_week(
        self,
        person_id: UUID,
        week_start: date,
        week_number: int = 1,
    ) -> list[dict[str, Any]]:
        """Get the effective schedule for a faculty member for a specific week.

        Merges template slots with overrides. Overrides take precedence.

        Args:
            person_id: Faculty member's ID
            week_start: Monday of the week
            week_number: Which week in the block (1-4), for week-specific templates

        Returns:
            List of effective slot dicts with keys:
                - day_of_week: int
                - time_of_day: str
                - activity_id: UUID | None
                - activity: Activity | None
                - is_locked: bool
                - priority: int
                - source: "template" | "override"
                - notes: str | None
        """
        # Get template slots (week-specific OR all-weeks)
        templates = await self.get_template(person_id, week_number)

        # Get overrides for this week
        overrides = await self.get_overrides(person_id, week_start)

        # Build slot key -> override mapping
        override_map = {}
        for ovr in overrides:
            key = f"{ovr.day_of_week}_{ovr.time_of_day}"
            override_map[key] = ovr

        # Build effective slots
        effective = []

        # Build template map (week-specific takes precedence over all-weeks)
        template_map = {}
        for tmpl in templates:
            key = f"{tmpl.day_of_week}_{tmpl.time_of_day}"
            # Week-specific (week_number is not None) overrides all-weeks (week_number is None)
            if key not in template_map or tmpl.week_number is not None:
                template_map[key] = tmpl

        # Generate all 14 slots (7 days x 2 time periods)
        for day in range(7):
            for time in ["AM", "PM"]:
                key = f"{day}_{time}"

                slot = {
                    "day_of_week": day,
                    "time_of_day": time,
                    "activity_id": None,
                    "activity": None,
                    "is_locked": False,
                    "priority": 50,
                    "source": None,
                    "notes": None,
                }

                # Check for override first (takes precedence)
                if key in override_map:
                    ovr = override_map[key]
                    slot["activity_id"] = ovr.activity_id
                    slot["activity"] = ovr.activity
                    slot["is_locked"] = ovr.is_locked
                    slot["source"] = "override"
                    slot["notes"] = ovr.override_reason
                # Fall back to template
                elif key in template_map:
                    tmpl = template_map[key]
                    slot["activity_id"] = tmpl.activity_id
                    slot["activity"] = tmpl.activity
                    slot["is_locked"] = tmpl.is_locked
                    slot["priority"] = tmpl.priority
                    slot["source"] = "template"
                    slot["notes"] = tmpl.notes

                effective.append(slot)

        return effective

    # =========================================================================
    # Permission Lookups
    # =========================================================================

    async def get_permitted_activities(
        self,
        faculty_role: str,
    ) -> list[Activity]:
        """Get activities permitted for a faculty role.

        Args:
            faculty_role: FacultyRole enum value (e.g., "pd", "apd", "oic")

        Returns:
            List of Activity objects permitted for this role
        """
        from sqlalchemy import text

        result = await self._execute(
            text("""
                SELECT a.id, a.name, a.code, a.display_abbreviation,
                       a.activity_category, a.font_color, a.background_color,
                       a.requires_supervision, a.is_protected,
                       a.counts_toward_clinical_hours, a.provides_supervision,
                       a.display_order, a.is_archived
                FROM activities a
                JOIN faculty_activity_permissions fap ON fap.activity_id = a.id
                WHERE fap.faculty_role = :role AND a.is_archived = false
                ORDER BY a.display_order, a.name
            """).bindparams(role=faculty_role)
        )

        # Convert rows to Activity objects
        activities = []
        for row in result:
            activity = Activity(
                id=row.id,
                name=row.name,
                code=row.code,
                display_abbreviation=row.display_abbreviation,
                activity_category=row.activity_category,
                font_color=row.font_color,
                background_color=row.background_color,
                requires_supervision=row.requires_supervision,
                is_protected=row.is_protected,
                counts_toward_clinical_hours=row.counts_toward_clinical_hours,
                provides_supervision=row.provides_supervision,
                display_order=row.display_order,
                is_archived=row.is_archived,
            )
            activities.append(activity)

        return activities

    async def get_default_activities(
        self,
        faculty_role: str,
    ) -> list[Activity]:
        """Get default activities for a faculty role (is_default=true).

        Args:
            faculty_role: FacultyRole enum value

        Returns:
            List of Activity objects that are defaults for this role
        """
        from sqlalchemy import text

        result = await self._execute(
            text("""
                SELECT a.id, a.name, a.code, a.display_abbreviation,
                       a.activity_category, a.font_color, a.background_color,
                       a.requires_supervision, a.is_protected,
                       a.counts_toward_clinical_hours, a.provides_supervision,
                       a.display_order, a.is_archived
                FROM activities a
                JOIN faculty_activity_permissions fap ON fap.activity_id = a.id
                WHERE fap.faculty_role = :role
                  AND fap.is_default = true
                  AND a.is_archived = false
                ORDER BY a.display_order, a.name
            """).bindparams(role=faculty_role)
        )

        activities = []
        for row in result:
            activity = Activity(
                id=row.id,
                name=row.name,
                code=row.code,
                display_abbreviation=row.display_abbreviation,
                activity_category=row.activity_category,
                font_color=row.font_color,
                background_color=row.background_color,
                requires_supervision=row.requires_supervision,
                is_protected=row.is_protected,
                counts_toward_clinical_hours=row.counts_toward_clinical_hours,
                provides_supervision=row.provides_supervision,
                display_order=row.display_order,
                is_archived=row.is_archived,
            )
            activities.append(activity)

        return activities

    # =========================================================================
    # Matrix View (All Faculty)
    # =========================================================================

    async def get_faculty_matrix(
        self,
        start_date: date,
        end_date: date,
        include_adjunct: bool = False,
    ) -> list[dict[str, Any]]:
        """Get activity matrix for all faculty within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            include_adjunct: Include adjunct faculty

        Returns:
            List of faculty dicts with their effective schedules:
                - person_id: UUID
                - name: str
                - faculty_role: str
                - weeks: list of week data, each containing:
                    - week_start: date
                    - slots: list of 14 slot dicts
        """
        # Get all faculty members
        stmt = (
            select(Person)
            .where(Person.type == "faculty")
            .order_by(Person.name)
        )

        if not include_adjunct:
            stmt = stmt.where(
                or_(
                    Person.faculty_role != "adjunct",
                    Person.faculty_role.is_(None),
                )
            )

        result = await self._execute(stmt)
        faculty_list = list(result.scalars().all())

        # Calculate weeks in range
        weeks = []
        current = start_date
        # Normalize to Monday
        while current.weekday() != 0:
            current -= timedelta(days=1)

        while current <= end_date:
            weeks.append(current)
            current += timedelta(days=7)

        # Build matrix
        matrix = []
        for faculty in faculty_list:
            faculty_data = {
                "person_id": faculty.id,
                "name": faculty.name,
                "faculty_role": faculty.faculty_role,
                "weeks": [],
            }

            for week_start in weeks:
                # Determine week number within block (simplified: just use week of month)
                week_number = ((week_start.day - 1) // 7) + 1
                if week_number > 4:
                    week_number = 4

                effective = await self.get_effective_week(
                    faculty.id, week_start, week_number
                )

                faculty_data["weeks"].append({
                    "week_start": week_start,
                    "slots": effective,
                })

            matrix.append(faculty_data)

        return matrix
