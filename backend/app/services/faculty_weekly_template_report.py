"""Reporting utilities for faculty weekly template coverage."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.faculty_weekly_override import FacultyWeeklyOverride
from app.models.faculty_weekly_template import FacultyWeeklyTemplate
from app.models.person import Person


class FacultyWeeklyTemplateCoverageService:
    """Service for reporting missing weekly templates/overrides."""

    def __init__(self, db: AsyncSession | Session) -> None:
        self.db = db
        self._is_async = isinstance(db, AsyncSession) or hasattr(db, "_session")

    async def _execute(self, stmt):
        if self._is_async:
            return await self.db.execute(stmt)
        return self.db.execute(stmt)

    async def get_missing_faculty_weekly_templates(self) -> dict[str, Any]:
        """Return faculty missing both weekly templates and overrides."""
        template_counts = (
            select(
                FacultyWeeklyTemplate.person_id.label("person_id"),
                func.count(FacultyWeeklyTemplate.id).label("template_count"),
            )
            .group_by(FacultyWeeklyTemplate.person_id)
            .subquery()
        )

        override_counts = (
            select(
                FacultyWeeklyOverride.person_id.label("person_id"),
                func.count(FacultyWeeklyOverride.id).label("override_count"),
            )
            .group_by(FacultyWeeklyOverride.person_id)
            .subquery()
        )

        faculty_filter = (Person.type == "faculty") & or_(
            Person.faculty_role.is_(None), Person.faculty_role != "adjunct"
        )
        total_faculty_stmt = (
            select(func.count()).select_from(Person).where(faculty_filter)
        )
        total_faculty_result = await self._execute(total_faculty_stmt)
        total_faculty = int(total_faculty_result.scalar_one())

        missing_stmt = (
            select(
                Person.id,
                Person.name,
                Person.faculty_role,
                func.coalesce(template_counts.c.template_count, 0).label(
                    "template_count"
                ),
                func.coalesce(override_counts.c.override_count, 0).label(
                    "override_count"
                ),
            )
            .where(faculty_filter)
            .outerjoin(template_counts, template_counts.c.person_id == Person.id)
            .outerjoin(override_counts, override_counts.c.person_id == Person.id)
            .where(
                func.coalesce(template_counts.c.template_count, 0) == 0,
                func.coalesce(override_counts.c.override_count, 0) == 0,
            )
            .order_by(Person.name)
        )

        missing_result = await self._execute(missing_stmt)
        missing = [
            {
                "person_id": row.id,
                "name": row.name,
                "faculty_role": row.faculty_role,
            }
            for row in missing_result.all()
        ]

        return {
            "total_faculty": total_faculty,
            "total_missing": len(missing),
            "missing": missing,
        }
