"""Cascade override planner for deployment-style coverage changes."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import ActivityCategory
from app.models.call_assignment import CallAssignment
from app.models.call_override import CallOverride
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.schedule_override import ScheduleOverride
from app.schemas.cascade_override import (
    CascadeOverridePlanResponse,
    CascadeOverrideRequest,
    CascadeOverrideStep,
)
from app.schemas.call_override import CallOverrideCreate
from app.schemas.schedule_override import ScheduleOverrideCreate
from app.services.call_override_service import CallOverrideService
from app.services.schedule_override_service import ScheduleOverrideService

logger = get_logger(__name__)

PROTECTED_ACTIVITY_CODES = {"FMIT", "AT", "PCAT", "DO"}
ADMIN_CODES = {"GME", "DFM", "LEC", "ADV"}
PROCEDURE_CODES = {"VAS", "VASC", "SM", "BTX", "COLPO"}


class CascadeOverrideService:
    """Build and optionally apply cascade overrides."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.schedule_override_service = ScheduleOverrideService(session)
        self.call_override_service = CallOverrideService(session)

    async def plan_and_apply(
        self,
        request: CascadeOverrideRequest,
        created_by_id: UUID | None,
    ) -> CascadeOverridePlanResponse:
        plan = await self._build_plan(request)

        if not request.apply or plan.errors:
            return plan

        for step in plan.steps:
            if step.target_type == "half_day":
                override = await self.schedule_override_service.create_override(
                    request=ScheduleOverrideCreate(
                        half_day_assignment_id=step.assignment_id,
                        override_type=step.override_type,
                        replacement_person_id=step.replacement_person_id,
                        reason=step.reason,
                        notes=step.notes,
                        supersedes_override_id=None,
                    ),
                    created_by_id=created_by_id,
                )
                step.created_override_id = override.id
            else:
                override = await self.call_override_service.create_override(
                    request=CallOverrideCreate(
                        call_assignment_id=step.assignment_id,
                        override_type=step.override_type,
                        replacement_person_id=step.replacement_person_id,
                        reason=step.reason,
                        notes=step.notes,
                        supersedes_override_id=None,
                    ),
                    created_by_id=created_by_id,
                )
                step.created_override_id = override.id

        plan.applied = True
        return plan

    async def _build_plan(
        self, request: CascadeOverrideRequest
    ) -> CascadeOverridePlanResponse:
        person = await self.session.get(Person, request.person_id)
        if not person or not person.is_faculty:
            return CascadeOverridePlanResponse(
                person_id=request.person_id,
                start_date=request.start_date,
                end_date=request.end_date,
                applied=False,
                steps=[],
                errors=["Cascade planning currently supports faculty only"],
            )

        if person.faculty_role == "adjunct":
            return CascadeOverridePlanResponse(
                person_id=request.person_id,
                start_date=request.start_date,
                end_date=request.end_date,
                applied=False,
                steps=[],
                errors=["Adjunct faculty are not auto-cascaded"],
            )

        half_day_assignments = await self._load_half_day_assignments(
            request.person_id, request.start_date, request.end_date
        )
        call_assignments = await self._load_call_assignments(
            request.person_id, request.start_date, request.end_date
        )

        steps: list[CascadeOverrideStep] = []
        warnings: list[str] = []
        errors: list[str] = []

        reserved_half_day: set[tuple[UUID, date, str]] = set()
        reserved_call: set[tuple[UUID, date]] = set()

        for assignment in sorted(
            half_day_assignments, key=lambda a: (a.date, a.time_of_day)
        ):
            step_result = await self._plan_half_day_override(
                assignment,
                request,
                reserved_half_day,
            )
            if step_result.errors:
                errors.extend(step_result.errors)
            steps.extend(step_result.steps)
            warnings.extend(step_result.warnings)

        for assignment in sorted(call_assignments, key=lambda a: a.date):
            step_result = await self._plan_call_override(
                assignment,
                request,
                reserved_call,
                reserved_half_day,
            )
            if step_result.errors:
                errors.extend(step_result.errors)
            steps.extend(step_result.steps)
            warnings.extend(step_result.warnings)

        return CascadeOverridePlanResponse(
            person_id=request.person_id,
            start_date=request.start_date,
            end_date=request.end_date,
            applied=False,
            steps=steps,
            warnings=warnings,
            errors=errors,
        )

    async def _load_half_day_assignments(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> list[HalfDayAssignment]:
        result = await self.session.execute(
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                HalfDayAssignment.person_id == person_id,
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
        )
        return list(result.scalars().all())

    async def _load_call_assignments(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> list[CallAssignment]:
        result = await self.session.execute(
            select(CallAssignment)
            .options(selectinload(CallAssignment.person))
            .where(
                CallAssignment.person_id == person_id,
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        return list(result.scalars().all())

    async def _plan_half_day_override(
        self,
        target: HalfDayAssignment,
        request: CascadeOverrideRequest,
        reserved_half_day: set[tuple[UUID, date, str]],
    ) -> _PlanResult:
        candidates = await self._get_faculty_candidates(target.date, target.time_of_day)
        best = self._select_best_candidate(target, candidates, reserved_half_day)

        if best is None:
            return _PlanResult(
                steps=[],
                warnings=[],
                errors=[
                    f"No valid replacement found for {target.date} {target.time_of_day}"
                ],
            )

        if best.assigned and request.max_depth < 2:
            return _PlanResult(
                steps=[],
                warnings=[],
                errors=[
                    f"Replacement requires cascade depth > {request.max_depth} for {target.date} {target.time_of_day}"
                ],
            )

        steps: list[CascadeOverrideStep] = []
        warnings: list[str] = list(best.warnings)

        if best.assigned and best.cancel_assignment_id:
            steps.append(
                CascadeOverrideStep(
                    target_type="half_day",
                    assignment_id=best.cancel_assignment_id,
                    override_type="cancellation",
                    replacement_person_id=None,
                    reason=request.reason,
                    notes=request.notes,
                    score=best.score,
                    warnings=best.warnings,
                )
            )

        steps.append(
            CascadeOverrideStep(
                target_type="half_day",
                assignment_id=target.id,
                override_type="coverage",
                replacement_person_id=best.person_id,
                reason=request.reason,
                notes=request.notes,
                score=best.score,
                warnings=best.warnings,
            )
        )

        reserved_half_day.add((best.person_id, target.date, target.time_of_day))

        return _PlanResult(steps=steps, warnings=warnings, errors=[])

    async def _plan_call_override(
        self,
        target: CallAssignment,
        request: CascadeOverrideRequest,
        reserved_call: set[tuple[UUID, date]],
        reserved_half_day: set[tuple[UUID, date, str]],
    ) -> _PlanResult:
        candidates = await self._get_faculty_candidates_for_call(target.date)
        best = await self._select_best_call_candidate(
            target,
            candidates,
            reserved_call,
            reserved_half_day,
            request.start_date,
            request.end_date,
        )

        if best is None:
            return _PlanResult(
                steps=[],
                warnings=[],
                errors=[f"No valid call replacement found for {target.date}"],
            )

        step = CascadeOverrideStep(
            target_type="call",
            assignment_id=target.id,
            override_type="coverage",
            replacement_person_id=best.person_id,
            reason=request.reason,
            notes=request.notes,
            score=best.score,
            warnings=best.warnings,
        )
        reserved_call.add((best.person_id, target.date))

        gap_steps, gap_warnings = await self._plan_post_call_gap_steps(
            target,
            request.reason,
            request.notes,
        )

        return _PlanResult(
            steps=[step, *gap_steps],
            warnings=[*best.warnings, *gap_warnings],
            errors=[],
        )

    async def _get_faculty_candidates(
        self, target_date: date, time_of_day: str
    ) -> list[_Candidate]:
        faculty_result = await self.session.execute(
            select(Person).where(Person.type == "faculty")
        )
        faculty = list(faculty_result.scalars().all())

        assignments_result = await self.session.execute(
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                HalfDayAssignment.date == target_date,
                HalfDayAssignment.time_of_day == time_of_day,
            )
        )
        assignments = list(assignments_result.scalars().all())
        assignment_map = {a.person_id: a for a in assignments}

        candidates: list[_Candidate] = []
        for person in faculty:
            if person.faculty_role == "adjunct":
                continue
            assignment = assignment_map.get(person.id)
            candidate = _Candidate.from_assignment(person, assignment)
            candidates.append(candidate)
        return candidates

    async def _get_faculty_candidates_for_call(
        self, target_date: date
    ) -> list[_Candidate]:
        faculty_result = await self.session.execute(
            select(Person).where(Person.type == "faculty")
        )
        faculty = list(faculty_result.scalars().all())

        assignments_result = await self.session.execute(
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                HalfDayAssignment.date == target_date,
            )
        )
        assignments = list(assignments_result.scalars().all())
        assignment_map = {a.person_id: a for a in assignments}

        candidates: list[_Candidate] = []
        for person in faculty:
            if person.faculty_role == "adjunct":
                continue
            assignment = assignment_map.get(person.id)
            candidate = _Candidate.from_assignment(person, assignment)
            candidates.append(candidate)
        return candidates

    def _select_best_candidate(
        self,
        target: HalfDayAssignment,
        candidates: list[_Candidate],
        reserved_half_day: set[tuple[UUID, date, str]],
    ) -> _Candidate | None:
        best: _Candidate | None = None
        for candidate in candidates:
            if candidate.person_id == target.person_id:
                continue
            if candidate.is_disqualified:
                continue
            if (
                candidate.person_id,
                target.date,
                target.time_of_day,
            ) in reserved_half_day:
                continue
            if (
                candidate.assigned
                and candidate.activity_code in PROTECTED_ACTIVITY_CODES
            ):
                continue

            score = candidate.score
            if best is None or score < best.score:
                best = candidate
        return best

    async def _select_best_call_candidate(
        self,
        target: CallAssignment,
        candidates: list[_Candidate],
        reserved_call: set[tuple[UUID, date]],
        reserved_half_day: set[tuple[UUID, date, str]],
        start_date: date,
        end_date: date,
    ) -> _Candidate | None:
        call_assignments = await self.session.execute(
            select(CallAssignment).where(
                CallAssignment.date == target.date,
            )
        )
        call_on_date = {c.person_id for c in call_assignments.scalars().all()}

        call_override_result = await self.session.execute(
            select(CallOverride).where(
                CallOverride.effective_date == target.date,
                CallOverride.is_active.is_(True),
            )
        )
        call_override_replacements = {
            o.replacement_person_id
            for o in call_override_result.scalars().all()
            if o.replacement_person_id is not None
        }

        call_counts = await self._call_counts(start_date, end_date)

        best: _Candidate | None = None
        for candidate in candidates:
            if candidate.person_id == target.person_id:
                continue
            if (candidate.person_id, target.date) in reserved_call:
                continue
            if candidate.is_disqualified:
                continue
            if candidate.person_id in call_on_date:
                continue
            if candidate.person_id in call_override_replacements:
                continue

            score = candidate.score
            warnings: list[str] = list(candidate.warnings)

            # Same-day clinic allowed with warning
            if candidate.assigned:
                warnings.append(
                    "Replacement has a same-day assignment; patients may need reschedule"
                )
                score += 1.0

            if (candidate.person_id, target.date, "AM") in reserved_half_day or (
                candidate.person_id,
                target.date,
                "PM",
            ) in reserved_half_day:
                warnings.append(
                    "Replacement already covering a half-day override this day"
                )
                score += 1.0

            # Call-before-leave penalty
            if await self._has_absence(
                candidate.person_id, target.date + timedelta(days=1)
            ):
                warnings.append("Replacement has leave the next day")
                score += 1.0

            # Back-to-back call penalty
            if await self._has_call_adjacent(candidate.person_id, target.date):
                warnings.append("Replacement has adjacent call assignment")
                score += 1.0

            next_day_conflicts = await self._next_day_protected_conflicts(
                candidate.person_id, target.date
            )
            if next_day_conflicts:
                warnings.append(
                    "Replacement has next-day protected assignment(s): "
                    + ", ".join(next_day_conflicts)
                )
                warnings.append("Post-call PCAT/DO requires manual follow-up")
                score += 2.0

            score += call_counts.get(candidate.person_id, 0) * 0.25

            if best is None or score < best.score:
                candidate.score = score
                candidate.warnings = warnings
                best = candidate

        return best

    async def _has_absence(self, person_id: UUID, on_date: date) -> bool:
        result = await self.session.execute(
            select(Absence.id).where(
                Absence.person_id == person_id,
                Absence.start_date <= on_date,
                Absence.end_date >= on_date,
            )
        )
        return result.scalar_one_or_none() is not None

    async def _has_call_adjacent(self, person_id: UUID, on_date: date) -> bool:
        result = await self.session.execute(
            select(CallAssignment.id).where(
                CallAssignment.person_id == person_id,
                CallAssignment.date.in_(
                    [on_date - timedelta(days=1), on_date + timedelta(days=1)]
                ),
            )
        )
        return result.scalar_one_or_none() is not None

    async def _call_counts(self, start_date: date, end_date: date) -> dict[UUID, int]:
        result = await self.session.execute(
            select(CallAssignment.person_id).where(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        counts: dict[UUID, int] = defaultdict(int)
        for person_id in result.scalars().all():
            counts[person_id] += 1
        return counts

    async def _plan_post_call_gap_steps(
        self,
        call_assignment: CallAssignment,
        reason: str | None,
        notes: str | None,
    ) -> tuple[list[CascadeOverrideStep], list[str]]:
        """Create GAP overrides for next-day PCAT/DO tied to the original caller."""
        next_day = call_assignment.date + timedelta(days=1)
        result = await self.session.execute(
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                HalfDayAssignment.person_id == call_assignment.person_id,
                HalfDayAssignment.date == next_day,
            )
        )
        assignments = list(result.scalars().all())
        if not assignments:
            return [], []

        override_result = await self.session.execute(
            select(ScheduleOverride).where(
                ScheduleOverride.half_day_assignment_id.in_(
                    [a.id for a in assignments]
                ),
                ScheduleOverride.is_active.is_(True),
            )
        )
        existing_overrides = {
            o.half_day_assignment_id for o in override_result.scalars().all()
        }

        steps: list[CascadeOverrideStep] = []
        warnings: list[str] = []
        for assignment in assignments:
            if assignment.id in existing_overrides:
                continue
            activity = assignment.activity
            code = (
                (activity.display_abbreviation or activity.code or "").upper()
                if activity
                else ""
            )
            if code not in {"PCAT", "DO"}:
                continue

            steps.append(
                CascadeOverrideStep(
                    target_type="half_day",
                    assignment_id=assignment.id,
                    override_type="gap",
                    replacement_person_id=None,
                    reason=reason,
                    notes=notes,
                    warnings=["GAP: post-call PCAT/DO unfilled"],
                )
            )
            warnings.append(f"GAP created for {code} on {next_day.isoformat()}")

        return steps, warnings

    async def _next_day_protected_conflicts(
        self, person_id: UUID, call_date: date
    ) -> list[str]:
        next_day = call_date + timedelta(days=1)
        result = await self.session.execute(
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                HalfDayAssignment.person_id == person_id,
                HalfDayAssignment.date == next_day,
            )
        )
        conflicts: list[str] = []
        for assignment in result.scalars().all():
            activity = assignment.activity
            code = ""
            category = None
            if activity:
                code = (activity.display_abbreviation or activity.code or "").upper()
                category = activity.activity_category

            if category == ActivityCategory.TIME_OFF.value:
                conflicts.append("TIME_OFF")
            elif code in PROTECTED_ACTIVITY_CODES:
                conflicts.append(code)

        return sorted(set(conflicts))


class _Candidate:
    """Internal candidate representation."""

    def __init__(
        self,
        person_id: UUID,
        assigned: bool,
        activity_code: str | None,
        activity_category: str | None,
    ) -> None:
        self.person_id = person_id
        self.assigned = assigned
        self.activity_code = (activity_code or "").upper() if activity_code else None
        self.activity_category = activity_category
        self.is_disqualified = False
        self.score = 0.0
        self.cancel_assignment_id: UUID | None = None
        self.warnings: list[str] = []

    @classmethod
    def from_assignment(
        cls, person: Person, assignment: HalfDayAssignment | None
    ) -> _Candidate:
        if assignment is None:
            return cls(person.id, False, None, None)

        activity = assignment.activity
        activity_code = None
        activity_category = None
        if activity:
            activity_code = (
                activity.display_abbreviation or activity.code or ""
            ).upper()
            activity_category = activity.activity_category

        candidate = cls(person.id, True, activity_code, activity_category)
        candidate.cancel_assignment_id = assignment.id
        candidate._assign_score()
        return candidate

    def _assign_score(self) -> None:
        if not self.assigned:
            return

        if self.activity_category == ActivityCategory.TIME_OFF.value:
            self.is_disqualified = True
            return

        if self.activity_code in PROTECTED_ACTIVITY_CODES:
            self.is_disqualified = True
            return

        if self.activity_code in ADMIN_CODES or self.activity_category in (
            ActivityCategory.ADMINISTRATIVE.value,
            ActivityCategory.EDUCATIONAL.value,
        ):
            self.score = 1.0
            self.warnings.append("Sacrificing admin/education assignment")
            return

        if self.activity_code in PROCEDURE_CODES:
            self.score = 3.0
            self.warnings.append("Sacrificing procedure supervision")
            return

        if self.activity_category == ActivityCategory.CLINICAL.value:
            self.score = 2.0
            self.warnings.append(
                "Sacrificing clinic session (patients may need reschedule)"
            )
            return

        self.score = 2.5
        self.warnings.append("Sacrificing assignment")


class _PlanResult:
    def __init__(
        self,
        steps: list[CascadeOverrideStep],
        warnings: list[str],
        errors: list[str],
    ) -> None:
        self.steps = steps
        self.warnings = warnings
        self.errors = errors
