"""
Fairness Audit Service.

Provides unified visibility into faculty workload distribution across
call, FMIT, clinic, admin, and academic time.

Used by the fairness dashboard to display min/max/mean statistics
per category and identify workload imbalances.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints.integrated_workload import (
    ADMIN_WEIGHT,
    ACADEMIC_WEIGHT,
    CALL_WEIGHT,
    CLINIC_WEIGHT,
    FMIT_WEIGHT,
    FacultyWorkload,
)

logger = logging.getLogger(__name__)


@dataclass
class CategoryStats:
    """Statistics for a single workload category."""

    min: int
    max: int
    mean: float
    spread: int

    def to_dict(self) -> dict:
        return {
            "min": self.min,
            "max": self.max,
            "mean": round(self.mean, 2),
            "spread": self.spread,
        }


@dataclass
class FairnessAuditReport:
    """Complete fairness audit report."""

    period_start: date
    period_end: date
    faculty_count: int

    # Per-category statistics
    call_stats: CategoryStats
    fmit_stats: CategoryStats
    clinic_stats: CategoryStats
    admin_stats: CategoryStats
    academic_stats: CategoryStats

    # Total workload
    workload_stats: CategoryStats

    # Individual faculty workloads
    workloads: list[FacultyWorkload]

    # Jain's fairness index (0-1, 1=perfect)
    fairness_index: float

    # Outliers (faculty > 1.25x or < 0.75x mean)
    high_workload_faculty: list[str]
    low_workload_faculty: list[str]

    def to_dict(self) -> dict:
        return {
            "period": {
                "start": str(self.period_start),
                "end": str(self.period_end),
            },
            "faculty_count": self.faculty_count,
            "category_stats": {
                "call": self.call_stats.to_dict(),
                "fmit": self.fmit_stats.to_dict(),
                "clinic": self.clinic_stats.to_dict(),
                "admin": self.admin_stats.to_dict(),
                "academic": self.academic_stats.to_dict(),
            },
            "workload_stats": self.workload_stats.to_dict(),
            "fairness_index": round(self.fairness_index, 3),
            "outliers": {
                "high": self.high_workload_faculty,
                "low": self.low_workload_faculty,
            },
            "workloads": [w.to_dict() for w in self.workloads],
            "weights": {
                "call": CALL_WEIGHT,
                "fmit": FMIT_WEIGHT,
                "clinic": CLINIC_WEIGHT,
                "admin": ADMIN_WEIGHT,
                "academic": ACADEMIC_WEIGHT,
            },
        }


class FairnessAuditService:
    """Service for auditing faculty workload fairness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_audit_report(
        self,
        start_date: date,
        end_date: date,
        include_titled_faculty: bool = False,
    ) -> FairnessAuditReport:
        """
        Generate a comprehensive fairness audit report.

        Args:
            start_date: Start of audit period
            end_date: End of audit period
            include_titled_faculty: Include PD/APD/OIC/Dept Chief (default False)

        Returns:
            FairnessAuditReport with workload breakdown and statistics
        """
        # Get all faculty
        faculty_query = select(Person).where(Person.type == "faculty")
        faculty_result = await self.db.execute(faculty_query)
        all_faculty = faculty_result.scalars().all()

        # Filter to eligible faculty (Core by default)
        titled_roles = {"pd", "apd", "oic", "dept_chief", "department_chief"}
        if include_titled_faculty:
            eligible_faculty = list(all_faculty)
        else:
            eligible_faculty = [
                f for f in all_faculty if not self._has_titled_role(f, titled_roles)
            ]

        if not eligible_faculty:
            return self._empty_report(start_date, end_date)

        # Get blocks in date range
        block_query = select(Block).where(
            Block.date >= start_date,
            Block.date <= end_date,
        )
        block_result = await self.db.execute(block_query)
        blocks = block_result.scalars().all()
        block_ids = [b.id for b in blocks]

        if not block_ids:
            return self._empty_report(start_date, end_date)

        # Get rotation templates for classification
        template_query = select(RotationTemplate)
        template_result = await self.db.execute(template_query)
        templates = {t.id: t for t in template_result.scalars().all()}

        # Get assignments for eligible faculty in date range
        faculty_ids = [f.id for f in eligible_faculty]
        assignment_query = select(Assignment).where(
            Assignment.person_id.in_(faculty_ids),
            Assignment.block_id.in_(block_ids),
        )
        assignment_result = await self.db.execute(assignment_query)
        assignments = assignment_result.scalars().all()

        # Calculate workload per faculty
        workloads = self._calculate_workloads(
            eligible_faculty, assignments, templates, blocks
        )

        # Calculate statistics
        report = self._build_report(start_date, end_date, workloads)

        return report

    def _has_titled_role(self, faculty: Person, titled_roles: set) -> bool:
        """Check if faculty has a titled role."""
        if hasattr(faculty, "faculty_role") and faculty.faculty_role:
            role = faculty.faculty_role.lower().replace(" ", "_")
            if role in titled_roles:
                return True
        if hasattr(faculty, "title") and faculty.title:
            title = faculty.title.lower().replace(" ", "_")
            if title in titled_roles:
                return True
        return False

    def _calculate_workloads(
        self,
        faculty: list[Person],
        assignments: list[Assignment],
        templates: dict[UUID, RotationTemplate],
        blocks: list[Block],
    ) -> list[FacultyWorkload]:
        """Calculate workload for each faculty member."""
        block_by_id = {b.id: b for b in blocks}
        workloads: dict[UUID, FacultyWorkload] = {}
        fmit_weeks_seen: dict[UUID, set] = {}

        # Initialize workloads
        for f in faculty:
            workloads[f.id] = FacultyWorkload(
                person_id=str(f.id),
                person_name=f.name or "Unknown",
            )
            fmit_weeks_seen[f.id] = set()

        # Process assignments
        for a in assignments:
            if a.person_id not in workloads:
                continue

            workload = workloads[a.person_id]
            template = (
                templates.get(a.rotation_template_id)
                if a.rotation_template_id
                else None
            )
            block = block_by_id.get(a.block_id)

            # Count call
            if hasattr(a, "call_type") and a.call_type == "overnight":
                workload.call_count += 1

            if template:
                template_name = (template.name or "").upper()
                activity_type = (template.activity_type or "").lower()

                # Count FMIT (by week)
                if "FMIT" in template_name:
                    if block:
                        iso_week = block.date.isocalendar()[:2]
                        if iso_week not in fmit_weeks_seen[a.person_id]:
                            fmit_weeks_seen[a.person_id].add(iso_week)
                            workload.fmit_weeks += 1

                # Count clinic
                if activity_type in ("outpatient", "clinic", "fm_clinic"):
                    workload.clinic_halfdays += 1

                # Count admin
                if (
                    "GME" in template_name
                    or "DFM" in template_name
                    or activity_type in ("admin", "gme", "dfm")
                ):
                    workload.admin_halfdays += 1

                # Count academic
                if (
                    "LEC" in template_name
                    or "ADV" in template_name
                    or activity_type in ("academic", "lecture", "advising")
                ):
                    workload.academic_halfdays += 1

        return list(workloads.values())

    def _build_report(
        self,
        start_date: date,
        end_date: date,
        workloads: list[FacultyWorkload],
    ) -> FairnessAuditReport:
        """Build the audit report from workload data."""

        def calc_stats(values: list[int]) -> CategoryStats:
            if not values:
                return CategoryStats(min=0, max=0, mean=0.0, spread=0)
            return CategoryStats(
                min=min(values),
                max=max(values),
                mean=sum(values) / len(values),
                spread=max(values) - min(values),
            )

        call_stats = calc_stats([w.call_count for w in workloads])
        fmit_stats = calc_stats([w.fmit_weeks for w in workloads])
        clinic_stats = calc_stats([w.clinic_halfdays for w in workloads])
        admin_stats = calc_stats([w.admin_halfdays for w in workloads])
        academic_stats = calc_stats([w.academic_halfdays for w in workloads])

        # Total workload scores
        scores = [w.total_score for w in workloads]
        workload_stats = CategoryStats(
            min=int(min(scores)) if scores else 0,
            max=int(max(scores)) if scores else 0,
            mean=sum(scores) / len(scores) if scores else 0.0,
            spread=int(max(scores) - min(scores)) if scores else 0,
        )

        # Jain's fairness index
        fairness_index = self._jains_fairness_index(scores)

        # Identify outliers
        mean_score = workload_stats.mean
        high_workload = (
            [w.person_name for w in workloads if w.total_score > mean_score * 1.25]
            if mean_score > 0
            else []
        )
        low_workload = (
            [w.person_name for w in workloads if w.total_score < mean_score * 0.75]
            if mean_score > 0
            else []
        )

        return FairnessAuditReport(
            period_start=start_date,
            period_end=end_date,
            faculty_count=len(workloads),
            call_stats=call_stats,
            fmit_stats=fmit_stats,
            clinic_stats=clinic_stats,
            admin_stats=admin_stats,
            academic_stats=academic_stats,
            workload_stats=workload_stats,
            workloads=workloads,
            fairness_index=fairness_index,
            high_workload_faculty=high_workload,
            low_workload_faculty=low_workload,
        )

    def _jains_fairness_index(self, values: list[float]) -> float:
        """
        Calculate Jain's fairness index.

        Returns a value between 0 and 1, where 1 is perfectly fair.
        """
        if not values or len(values) == 0:
            return 1.0
        n = len(values)
        sum_values = sum(values)
        sum_squares = sum(x * x for x in values)
        if sum_squares == 0:
            return 1.0
        return (sum_values * sum_values) / (n * sum_squares)

    def _empty_report(self, start_date: date, end_date: date) -> FairnessAuditReport:
        """Return an empty report when no data available."""
        empty_stats = CategoryStats(min=0, max=0, mean=0.0, spread=0)
        return FairnessAuditReport(
            period_start=start_date,
            period_end=end_date,
            faculty_count=0,
            call_stats=empty_stats,
            fmit_stats=empty_stats,
            clinic_stats=empty_stats,
            admin_stats=empty_stats,
            academic_stats=empty_stats,
            workload_stats=empty_stats,
            workloads=[],
            fairness_index=1.0,
            high_workload_faculty=[],
            low_workload_faculty=[],
        )
