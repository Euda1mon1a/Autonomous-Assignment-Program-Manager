"""
Activity Assignment Solver using CP-SAT.

This solver assigns activities (C, AT, LEC, ADV, etc.) to half-day slots
that don't already have locked assignments (preload/manual) for both
residents and faculty.

The CP-SAT solver handles rotation-level assignment (which resident
gets which rotation). This solver handles activity-level assignment within
a rotation (which half-day slot gets C vs LEC vs ADV).

Decision Variables:
    a[person_id, date, time_of_day, activity_id] = 1 if person assigned activity at slot

Constraints:
    1. One activity per slot per person
    2. Skip locked slots (source=preload or source=manual)
    3. Resident activity distribution respects rotation_activity_requirements
    4. Resident total activity counts respect min/max from requirements
    5. Faculty AT coverage meets ACGME supervision ratios (uses PCAT baseline)
    6. Faculty clinic caps (min/max) enforced per week (min is soft)
    7. LEC/ADV are expected to be preloaded (locked) and are not assigned here
"""

import json
import os
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_dates
from app.utils.activity_locking import is_activity_preloaded
from app.utils.activity_naming import activity_code_from_name
from app.utils.fmc_capacity import (
    activity_counts_toward_fmc_capacity,
    activity_counts_toward_fmc_capacity_for_template,
    activity_is_proc_or_vas,
    activity_is_sm_capacity,
    activity_capacity_units,
    assignment_counts_toward_fmc_capacity,
    template_is_fmc_clinic,
)
from app.utils.supervision import (
    activity_provides_supervision,
    activity_requires_fmc_supervision,
)

logger = get_logger(__name__)

# Day index cutoff for secondary rotations (day 15+ uses secondary)
BLOCK_HALF_DAY = 14

# Rotation types considered outpatient for activity solving
OUTPATIENT_ACTIVITY_TYPES = {"outpatient"}

# Clinic/supervision codes for activity-level constraints (legacy fallback)
RESIDENT_CLINIC_CODES = {"FM_CLINIC", "C", "C-N", "CV"}
AT_COVERAGE_CODES = {"AT", "PCAT"}
SUPERVISION_REQUIRED_CODES = {"PROC", "PR", "PROCEDURE", "VAS"}
ADMIN_ACTIVITY_CODES = {"GME": "gme", "DFM": "dfm", "SM": "sm_clinic"}
ADMIN_EQUITY_CODES = {"GME", "DFM", "LEC", "ADV"}
SUPERVISION_EQUITY_CODES = {"AT", "PCAT"}
FACULTY_CLINIC_SHORTFALL_PENALTY = 10
FACULTY_CLINIC_OVERAGE_PENALTY = 40
OIC_CLINICAL_AVOID_PENALTY = 18
FACULTY_ADMIN_EQUITY_PENALTY = 12
FACULTY_AT_EQUITY_PENALTY = 12
FACULTY_ADMIN_BONUS = 1
PHYSICAL_CAPACITY_SOFT_PENALTY = 10
ACTIVITY_MIN_SHORTFALL_PENALTY = 10
CLINIC_MIN_SHORTFALL_PENALTY = 25
ACTIVITY_MAX_OVERAGE_PENALTY = 20
CLINIC_MAX_OVERAGE_PENALTY = 40
AT_COVERAGE_SHORTFALL_PENALTY = 50
PROC_VAS_EXTRA_UNITS = 4  # +1 AT for PROC/VAS (scaled by 4)
SM_ALIGNMENT_SHORTFALL_PENALTY = 30
VAS_ALIGNMENT_SHORTFALL_PENALTY = 30
CV_TARGET_NUMERATOR = 3
CV_TARGET_DENOMINATOR = 10
CV_TARGET_SHORTFALL_PENALTY = 25
CV_DAILY_SPREAD_PENALTY = 6
CV_PENALTY_BY_ROLE = {
    "faculty": 0,
    "pgy3": 5,
    "pgy2": 15,
}
OIC_CLINIC_AVOID_DAYS = {0, 4}  # Monday, Friday (Python weekday)
VAS_FACULTY_PRIMARY_NAMES = {"KINKENNON", "LABOUNTY"}
VAS_FACULTY_SECONDARY_NAMES = {"TAGAWA"}
VAS_FACULTY_SECONDARY_PENALTY = 10
VAS_RESIDENT_PENALTY_PROC = 0
VAS_RESIDENT_PENALTY_FMC = 5
VAS_RESIDENT_PENALTY_POCUS = 10
VAS_RESIDENT_PENALTY_OTHER = 20
VAS_ALLOWED_WEEKDAY_TIMES = {(3, "AM"), (3, "PM"), (4, "AM")}


class CPSATActivitySolver:
    """
    CP-SAT solver for assigning activities to half-day slots.

    This solver operates on HalfDayAssignment records created by the
    CP-SAT pipeline (source='solver') and fills activity_id.

    The solver respects:
    - Locked slots (source=preload or manual) - never touched
    - rotation_activity_requirements - determines which activities to assign
      (outpatient templates must have explicit requirements; no auto-create)
    - LEC/ADV are preloaded and therefore excluded from solver assignments
    """

    def __init__(
        self,
        session: Session,
        timeout_seconds: float = 60.0,
        num_workers: int = 4,
    ):
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.num_workers = num_workers
        self._activity_cache: dict[str, Activity] = {}
        self._assignment_rotation_map: dict[
            tuple[UUID, date, str], RotationTemplate
        ] = {}

    def _is_fmc_clinic_activity(self, activity: Activity | None) -> bool:
        if not activity:
            return False
        code = (activity.code or "").strip().upper()
        display = (activity.display_abbreviation or "").strip().upper()
        return code in {"C", "C-N", "C-I", "FM_CLINIC"} or display in {
            "C",
            "C-N",
            "C-I",
            "FM_CLINIC",
        }

    def _is_cv_activity(self, activity: Activity | None) -> bool:
        if not activity:
            return False
        code = (activity.code or "").strip().upper()
        display = (activity.display_abbreviation or "").strip().upper()
        return code == "CV" or display == "CV"

    def _is_vas_allowed_slot(self, slot_date: date, time_of_day: str) -> bool:
        return (slot_date.weekday(), time_of_day.upper()) in VAS_ALLOWED_WEEKDAY_TIMES

    def _normalize_person_name(self, person: Person | None) -> str:
        if not person or not person.name:
            return ""
        return "".join(ch for ch in person.name.upper() if ch.isalpha())

    def _vas_faculty_tier(self, faculty: Person | None) -> str:
        normalized = self._normalize_person_name(faculty)
        if any(name in normalized for name in VAS_FACULTY_PRIMARY_NAMES):
            return "primary"
        if any(name in normalized for name in VAS_FACULTY_SECONDARY_NAMES):
            return "secondary"
        return "other"

    def _is_vas_faculty(self, faculty: Person | None) -> bool:
        return self._vas_faculty_tier(faculty) != "other"

    def _vas_faculty_penalty(self, faculty: Person | None) -> int:
        tier = self._vas_faculty_tier(faculty)
        if tier == "secondary":
            return VAS_FACULTY_SECONDARY_PENALTY
        return 0

    def _vas_resident_category(self, template: RotationTemplate | None) -> str:
        if not template:
            return "other"
        abbrev = (template.abbreviation or template.display_abbreviation or "").upper()
        name = (template.name or "").upper()
        if "PROC" in abbrev or "PROC" in name:
            return "proc"
        if "POCUS" in abbrev or "POCUS" in name or abbrev == "US":
            return "pocus"
        if template_is_fmc_clinic(template) or "FMC" in abbrev or "FMC" in name:
            return "fmc"
        return "other"

    def _is_vas_resident_template(self, template: RotationTemplate | None) -> bool:
        return self._vas_resident_category(template) in {"proc", "fmc", "pocus"}

    def _vas_resident_penalty(self, template: RotationTemplate | None) -> int:
        category = self._vas_resident_category(template)
        if category == "proc":
            return VAS_RESIDENT_PENALTY_PROC
        if category == "fmc":
            return VAS_RESIDENT_PENALTY_FMC
        if category == "pocus":
            return VAS_RESIDENT_PENALTY_POCUS
        return VAS_RESIDENT_PENALTY_OTHER

    def solve(
        self,
        block_number: int,
        academic_year: int,
    ) -> dict[str, Any]:
        """
        Assign activities to half-day slots for a block.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)

        Returns:
            Dictionary with:
                - success: True if solution found
                - assignments_updated: Number of slots with activity assigned
                - status: "optimal", "feasible", or "infeasible"
                - runtime_seconds: Solver runtime
        """
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.error("OR-Tools not installed. Run: pip install ortools>=9.8")
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "OR-Tools not installed",
            }

        start_time = time.time()

        # Get block date range
        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        logger.info(
            f"Activity solver starting for Block {block_number}: "
            f"{start_date} to {end_date}"
        )

        # Load candidate slots WITHOUT template filtering first
        # (template filtering requires _assignment_rotation_map which we build next)
        candidate_slots = self._load_candidate_slots(start_date, end_date)
        if not candidate_slots:
            logger.info("No candidate slots to assign")
            return {
                "success": True,
                "assignments_updated": 0,
                "status": "no_work",
                "message": "All slots are locked or no slots exist",
            }

        # Build assignment rotation map BEFORE filtering
        # (needed for _get_active_rotation_template fallback path)
        person_ids = {slot.person_id for slot in candidate_slots}
        self._assignment_rotation_map = self._load_assignment_rotation_map(
            start_date, end_date, person_ids
        )

        # NOW filter for outpatient rotations (map is populated)
        slots = self._filter_outpatient_slots(candidate_slots, start_date)
        if not slots:
            logger.info("No outpatient slots to assign after filtering")
            return {
                "success": True,
                "assignments_updated": 0,
                "status": "no_work",
                "message": "No outpatient rotation slots found",
            }

        logger.info(f"Found {len(slots)} outpatient slots to assign")
        slot_meta: dict[int, dict[str, Any]] = {}
        templates_by_id: dict[UUID, RotationTemplate] = {}
        resident_slots: set[int] = set()
        faculty_slots: set[int] = set()
        for s_i, slot in enumerate(slots):
            person_type = slot.person.type if slot.person else None
            template = None
            if person_type != "faculty":
                template = self._get_active_rotation_template(slot, start_date)
                if template:
                    templates_by_id[template.id] = template
            week_number = self._get_week_number(slot.date, start_date)
            slot_meta[s_i] = {
                "person_id": slot.person_id,
                "person_type": person_type,
                "template_id": template.id if template else None,
                "week": week_number,
                "date": slot.date,
                "time_of_day": slot.time_of_day,
                "pgy_level": (
                    slot.person.pgy_level
                    if slot.person and person_type != "faculty"
                    else None
                ),
            }
            if person_type == "faculty":
                faculty_slots.add(s_i)
            else:
                resident_slots.add(s_i)

        # Load activity requirements for templates in scope
        requirements_by_template = self._load_activity_requirements(
            set(templates_by_id.keys())
        )

        # Validate outpatient templates have explicit requirements (no auto-create)
        missing_templates = self._missing_outpatient_requirements(
            templates_by_id, requirements_by_template
        )
        if missing_templates:
            missing_names = ", ".join(
                sorted({template.name for template in missing_templates})
            )
            missing_ids = ", ".join(str(template.id) for template in missing_templates)
            logger.error(
                "Missing rotation activity requirements for outpatient templates: "
                f"{missing_names} (ids: {missing_ids})"
            )
            self._write_failure_snapshot(
                {
                    "stage": "requirements",
                    "status": "error",
                    "message": (
                        "Missing rotation activity requirements for outpatient "
                        "templates. Add RotationActivityRequirement rows."
                    ),
                    "block_number": block_number,
                    "academic_year": academic_year,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "counts": {
                        "slots_total": len(slots),
                        "slots_resident": len(resident_slots),
                        "slots_faculty": len(faculty_slots),
                        "templates_total": len(templates_by_id),
                        "templates_outpatient": len(
                            [
                                t
                                for t in templates_by_id.values()
                                if (t.rotation_type or "").lower()
                                in OUTPATIENT_ACTIVITY_TYPES
                            ]
                        ),
                        "requirements_total": sum(
                            len(reqs) for reqs in requirements_by_template.values()
                        ),
                    },
                    "missing_outpatient_templates": [
                        {
                            "id": str(template.id),
                            "name": template.name,
                            "abbreviation": template.abbreviation,
                            "rotation_type": template.rotation_type,
                        }
                        for template in missing_templates
                    ],
                }
            )
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": (
                    "Missing rotation activity requirements for outpatient templates. "
                    "Add RotationActivityRequirement rows before running activity solver."
                ),
            }

        # Load activities after any default creation
        all_activities = self._load_activities()
        if not all_activities:
            self._write_failure_snapshot(
                {
                    "stage": "activities",
                    "status": "error",
                    "message": "No activities found",
                    "block_number": block_number,
                    "academic_year": academic_year,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "counts": {
                        "slots_total": len(slots),
                        "slots_resident": len(resident_slots),
                        "slots_faculty": len(faculty_slots),
                        "templates_total": len(templates_by_id),
                        "requirements_total": sum(
                            len(reqs) for reqs in requirements_by_template.values()
                        ),
                    },
                }
            )
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "No activities found",
            }

        activity_by_id = {a.id: a for a in all_activities}

        # Candidate activities for solver: exclude preloaded/protected/time_off
        assignable_activities = [
            a for a in all_activities if not is_activity_preloaded(a)
        ]
        assignable_ids = {a.id for a in assignable_activities}
        template_locked_ids = {a.id for a in all_activities if is_activity_preloaded(a)}
        if not assignable_ids:
            self._write_failure_snapshot(
                {
                    "stage": "activities",
                    "status": "error",
                    "message": "No assignable activities (all locked/preloaded)",
                    "block_number": block_number,
                    "academic_year": academic_year,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "counts": {
                        "slots_total": len(slots),
                        "slots_resident": len(resident_slots),
                        "slots_faculty": len(faculty_slots),
                        "templates_total": len(templates_by_id),
                        "activities_total": len(all_activities),
                        "assignable_total": 0,
                    },
                }
            )
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "No assignable activities (all locked/preloaded)",
            }

        # Get key activities
        clinic_activity = self._get_activity_by_code(
            "fm_clinic"
        ) or self._get_activity_by_code("C")
        cv_activity = self._get_activity_by_code("CV")
        at_activity = self._get_activity_by_code("at") or self._get_activity_by_code(
            "AT"
        )

        # Activity ID sets for supervision and clinic demand (AT/PCAT only)
        supervision_required_ids = {
            activity.id
            for activity in all_activities
            if activity_requires_fmc_supervision(activity)
        }
        supervision_provider_ids = {
            activity.id
            for activity in all_activities
            if activity_provides_supervision(activity)
        }

        # Legacy fallback for older data (no flags configured)
        used_required_fallback = False
        used_provider_fallback = False
        if not supervision_required_ids:
            supervision_required_ids = self._activity_ids_for_codes(
                all_activities,
                RESIDENT_CLINIC_CODES | SUPERVISION_REQUIRED_CODES | {"CV"},
            )
            used_required_fallback = True
        if not supervision_provider_ids:
            supervision_provider_ids = self._activity_ids_for_codes(
                all_activities, AT_COVERAGE_CODES
            )
            used_provider_fallback = True
        logger.info(
            "Supervision activity sets: required="
            f"{len(supervision_required_ids)}, providers="
            f"{len(supervision_provider_ids)} (fallback_required="
            f"{used_required_fallback}, fallback_providers={used_provider_fallback})"
        )

        if resident_slots and not supervision_provider_ids:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "Missing supervision-providing activities (AT/PCAT)",
            }
        capacity_activity_ids = {
            activity.id
            for activity in all_activities
            if activity_counts_toward_fmc_capacity(activity)
        }
        proc_vas_activity_ids = {
            activity.id
            for activity in all_activities
            if activity_is_proc_or_vas(activity)
        }
        vas_activity_ids = self._activity_ids_for_codes(all_activities, {"VAS"})
        sm_capacity_ids = {
            activity.id
            for activity in all_activities
            if activity_is_sm_capacity(activity)
        }
        admin_equity_ids = self._activity_ids_for_codes(
            all_activities, ADMIN_EQUITY_CODES
        )
        supervision_equity_ids = self._activity_ids_for_codes(
            all_activities, SUPERVISION_EQUITY_CODES
        )

        # Create the CP model
        model = cp_model.CpModel()

        # Build allowed activity sets per template
        allowed_by_template: dict[UUID, list[UUID]] = {}
        for template_id, reqs in requirements_by_template.items():
            template = templates_by_id.get(template_id)
            allowed_ids = []
            for req in reqs:
                if req.activity_id in assignable_ids:
                    allowed_ids.append(req.activity_id)
                    continue
                if (
                    req.activity_id in template_locked_ids
                    and template
                    and self._activity_matches_template(req.activity, template)
                ):
                    allowed_ids.append(req.activity_id)
            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for act_id in allowed_ids:
                if act_id not in seen:
                    seen.add(act_id)
                    deduped.append(act_id)
            if deduped:
                allowed_by_template[template_id] = deduped

        # Fallback: if a template has no requirements, allow all assignables
        fallback_allowed = sorted(
            assignable_ids,
            key=lambda act_id: activity_by_id.get(act_id).code
            if act_id in activity_by_id
            else "",
        )

        # Faculty allowed activities (AT + clinic + admin types)
        faculty_allowed_ids: list[UUID] = []
        if at_activity and at_activity.id in assignable_ids:
            faculty_allowed_ids.append(at_activity.id)
        if clinic_activity and clinic_activity.id in assignable_ids:
            faculty_allowed_ids.append(clinic_activity.id)
        for admin_code in ADMIN_ACTIVITY_CODES.values():
            admin_activity = self._get_activity_by_code(admin_code)
            if admin_activity and admin_activity.id in assignable_ids:
                faculty_allowed_ids.append(admin_activity.id)

        if faculty_slots and not faculty_allowed_ids:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "Missing assignable activities for faculty (AT/C)",
            }

        # ==================================================
        # DECISION VARIABLES
        # a[slot_idx, activity_id] = 1 if slot gets activity
        # ==================================================
        a: dict[tuple[int, UUID], Any] = {}
        slot_allowed: dict[int, list[UUID]] = {}
        faculty_admin_activity_by_slot: dict[int, UUID] = {}
        cv_penalty_terms: list[tuple[Any, int]] = []
        vas_penalty_terms: list[tuple[Any, int]] = []
        oic_clinical_avoid_terms: list[tuple[Any, int]] = []

        for s_i, slot in enumerate(slots):
            person_type = slot_meta[s_i].get("person_type")
            template_id = slot_meta[s_i]["template_id"]
            if person_type == "faculty":
                allowed: list[UUID] = []
                faculty = slot.person
                if faculty:
                    if at_activity and at_activity.id in assignable_ids:
                        allowed.append(at_activity.id)

                    admin_activity = self._get_admin_activity_for_faculty(
                        faculty, self._activity_cache
                    )
                    if (
                        admin_activity
                        and admin_activity.id in assignable_ids
                        and admin_activity.id not in allowed
                    ):
                        allowed.append(admin_activity.id)
                        faculty_admin_activity_by_slot[s_i] = admin_activity.id

                    if self._is_sports_medicine_faculty(faculty):
                        sm_activity = self._get_activity_by_code(
                            "sm_clinic"
                        ) or self._get_activity_by_code("SM")
                        if (
                            sm_activity
                            and sm_activity.id in assignable_ids
                            and sm_activity.id not in allowed
                        ):
                            allowed.append(sm_activity.id)
                            faculty_admin_activity_by_slot[s_i] = sm_activity.id

                    min_c, max_c = self._get_faculty_clinic_caps(faculty)
                    if clinic_activity and (max_c > 0 or min_c > 0):
                        if clinic_activity.id in assignable_ids:
                            allowed.append(clinic_activity.id)
                            if (
                                cv_activity
                                and cv_activity.id in assignable_ids
                                and cv_activity.id not in allowed
                            ):
                                allowed.append(cv_activity.id)
                    if vas_activity_ids and faculty and self._is_vas_faculty(faculty):
                        for vas_id in vas_activity_ids:
                            if vas_id in assignable_ids and vas_id not in allowed:
                                allowed.append(vas_id)
                if not allowed:
                    allowed = list(faculty_allowed_ids)
            else:
                allowed = list(allowed_by_template.get(template_id) or [])
                if not allowed:
                    if template_id:
                        logger.warning(
                            f"No activity requirements for template {template_id}, "
                            "falling back to all assignable activities"
                        )
                    allowed = list(fallback_allowed)
                template = templates_by_id.get(template_id)
                pgy_level = slot_meta[s_i].get("pgy_level") or 0
                allow_cv = False
                if (
                    cv_activity
                    and cv_activity.id in assignable_ids
                    and template
                    and template_is_fmc_clinic(template)
                    and pgy_level >= 2
                ):
                    allow_cv = True
                if cv_activity and cv_activity.id in allowed and not allow_cv:
                    allowed = [act_id for act_id in allowed if act_id != cv_activity.id]
                if allow_cv and cv_activity and cv_activity.id not in allowed:
                    allowed.append(cv_activity.id)
                if not allowed:
                    allowed = list(fallback_allowed)
                    if cv_activity and cv_activity.id in allowed and not allow_cv:
                        allowed = [
                            act_id for act_id in allowed if act_id != cv_activity.id
                        ]
            vas_penalty_weight: int | None = None
            if vas_activity_ids and any(act_id in vas_activity_ids for act_id in allowed):
                if not self._is_vas_allowed_slot(slot.date, slot.time_of_day):
                    allowed = [act_id for act_id in allowed if act_id not in vas_activity_ids]
                elif person_type == "faculty":
                    if not self._is_vas_faculty(slot.person):
                        allowed = [
                            act_id for act_id in allowed if act_id not in vas_activity_ids
                        ]
                    else:
                        vas_penalty_weight = self._vas_faculty_penalty(slot.person)
                else:
                    template = templates_by_id.get(template_id)
                    if not self._is_vas_resident_template(template):
                        allowed = [
                            act_id for act_id in allowed if act_id not in vas_activity_ids
                        ]
                    else:
                        vas_penalty_weight = self._vas_resident_penalty(template)
            if not allowed:
                allowed = list(fallback_allowed)
                if cv_activity and cv_activity.id in allowed:
                    if person_type != "faculty":
                        template = templates_by_id.get(template_id)
                        pgy_level = slot_meta[s_i].get("pgy_level") or 0
                        allow_cv = (
                            cv_activity
                            and cv_activity.id in assignable_ids
                            and template
                            and template_is_fmc_clinic(template)
                            and pgy_level >= 2
                        )
                        if not allow_cv:
                            allowed = [
                                act_id for act_id in allowed if act_id != cv_activity.id
                            ]
                if vas_activity_ids and any(
                    act_id in vas_activity_ids for act_id in allowed
                ):
                    allowed = [
                        act_id for act_id in allowed if act_id not in vas_activity_ids
                    ]
            slot_allowed[s_i] = allowed

            for act_id in allowed:
                act_code = (
                    activity_by_id.get(act_id).code
                    if act_id in activity_by_id
                    else "act"
                )
                safe_code = act_code.replace("-", "_")
                a[s_i, act_id] = model.NewBoolVar(f"a_{s_i}_{safe_code}")

            if vas_penalty_weight and vas_penalty_weight > 0:
                for act_id in allowed:
                    if act_id in vas_activity_ids and (s_i, act_id) in a:
                        vas_penalty_terms.append((a[s_i, act_id], vas_penalty_weight))

            if cv_activity and cv_activity.id in allowed:
                if (s_i, cv_activity.id) in a:
                    penalty_weight = 0
                    if person_type == "faculty":
                        penalty_weight = CV_PENALTY_BY_ROLE["faculty"]
                    else:
                        pgy_level = slot_meta[s_i].get("pgy_level") or 0
                        if pgy_level >= 3:
                            penalty_weight = CV_PENALTY_BY_ROLE["pgy3"]
                        elif pgy_level == 2:
                            penalty_weight = CV_PENALTY_BY_ROLE["pgy2"]
                        if penalty_weight > 0:
                            cv_penalty_terms.append(
                                (a[s_i, cv_activity.id], penalty_weight)
                            )

            if person_type == "faculty" and slot.person:
                role = (getattr(slot.person, "faculty_role", "") or "").lower()
                if role == "oic" and slot_meta[s_i]["date"].weekday() in OIC_CLINIC_AVOID_DAYS:
                    for act_id in allowed:
                        activity = activity_by_id.get(act_id)
                        if not activity or activity.activity_category != "clinical":
                            continue
                        if activity.provides_supervision:
                            continue
                        if (s_i, act_id) in a:
                            oic_clinical_avoid_terms.append(
                                (a[s_i, act_id], OIC_CLINICAL_AVOID_PENALTY)
                            )

        slot_capacity_ids: dict[int, list[UUID]] = {}
        slot_sm_capacity_ids: dict[int, list[UUID]] = {}
        for s_i, allowed in slot_allowed.items():
            template = templates_by_id.get(slot_meta[s_i]["template_id"])
            capacity_ids: list[UUID] = []
            sm_ids: list[UUID] = []
            for act_id in allowed:
                activity = activity_by_id.get(act_id)
                if not activity:
                    continue
                if activity_counts_toward_fmc_capacity_for_template(activity, template):
                    capacity_ids.append(act_id)
                    if activity_is_sm_capacity(activity):
                        sm_ids.append(act_id)
            slot_capacity_ids[s_i] = capacity_ids
            slot_sm_capacity_ids[s_i] = sm_ids

        # ==================================================
        # CONSTRAINTS
        # ==================================================

        # Constraint 1: Exactly one activity per slot
        for s_i, allowed in slot_allowed.items():
            model.Add(sum(a[s_i, act_id] for act_id in allowed) == 1)

        # Constraint 2: Activity requirements (per week, per person, per rotation)
        slots_by_key: dict[tuple[UUID, UUID, int], list[int]] = defaultdict(list)
        for s_i, meta in slot_meta.items():
            template_id = meta["template_id"]
            if not template_id:
                continue
            key = (meta["person_id"], template_id, meta["week"])
            slots_by_key[key].append(s_i)

        locked_counts: dict[tuple[UUID, UUID, int, UUID], int] = defaultdict(int)
        baseline_resident_demand: dict[tuple[date, str], int] = defaultdict(int)
        baseline_faculty_coverage: dict[tuple[date, str], int] = defaultdict(int)
        locked_faculty_clinic_counts: dict[tuple[UUID, int], int] = defaultdict(int)
        locked_faculty_admin_counts: dict[tuple[UUID, int], int] = defaultdict(int)
        locked_faculty_supervision_counts: dict[tuple[UUID, int], int] = defaultdict(int)
        baseline_sm_resident_presence: dict[tuple[date, str], int] = defaultdict(int)
        baseline_sm_faculty_coverage: dict[tuple[date, str], int] = defaultdict(int)
        baseline_vas_resident_presence: dict[tuple[date, str], int] = defaultdict(int)
        baseline_vas_faculty_coverage: dict[tuple[date, str], int] = defaultdict(int)
        locked_slots = self._load_locked_slots(start_date, end_date, None)
        sm_clinic_activity = self._get_activity_by_code(
            "sm_clinic"
        ) or self._get_activity_by_code("SM")
        disable_sm_alignment = os.environ.get("DISABLE_SM_ALIGNMENT", "").lower() in {
            "1",
            "true",
            "yes",
        }
        disable_clinic_floor = os.environ.get("DISABLE_CLINIC_FLOOR", "").lower() in {
            "1",
            "true",
            "yes",
        }
        disable_physical_capacity = os.environ.get(
            "DISABLE_PHYSICAL_CAPACITY", ""
        ).lower() in {"1", "true", "yes"}
        locked_cv_target_counts: dict[int, dict[str, int]] = defaultdict(
            lambda: {"clinic": 0, "cv": 0}
        )
        locked_cv_target_counts_by_day: dict[tuple[int, int], dict[str, int]] = (
            defaultdict(lambda: {"clinic": 0, "cv": 0})
        )

        for locked in locked_slots:
            if not locked.activity_id:
                continue
            week_number = self._get_week_number(locked.date, start_date)
            day_of_week = locked.date.weekday()
            person_type = locked.person.type if locked.person else None
            slot_key = (locked.date, locked.time_of_day)
            activity = activity_by_id.get(locked.activity_id)
            is_cv = self._is_cv_activity(activity)
            is_clinic = self._is_fmc_clinic_activity(activity)
            pgy_level = (
                locked.person.pgy_level
                if locked.person and locked.person.pgy_level
                else 2
            )

            if person_type == "faculty":
                if locked.activity_id in supervision_provider_ids:
                    baseline_faculty_coverage[slot_key] += 1
                if clinic_activity and locked.activity_id == clinic_activity.id:
                    locked_faculty_clinic_counts[(locked.person_id, week_number)] += 1
                if locked.activity_id in admin_equity_ids:
                    locked_faculty_admin_counts[(locked.person_id, week_number)] += 1
                if locked.activity_id in supervision_equity_ids:
                    locked_faculty_supervision_counts[
                        (locked.person_id, week_number)
                    ] += 1
                if locked.activity_id in vas_activity_ids:
                    baseline_vas_faculty_coverage[slot_key] += 1
                if is_cv:
                    locked_cv_target_counts[week_number]["cv"] += 1
                    locked_cv_target_counts_by_day[(week_number, day_of_week)][
                        "cv"
                    ] += 1
                elif is_clinic:
                    locked_cv_target_counts[week_number]["clinic"] += 1
                    locked_cv_target_counts_by_day[(week_number, day_of_week)][
                        "clinic"
                    ] += 1
                if (
                    sm_clinic_activity
                    and locked.activity_id == sm_clinic_activity.id
                    and locked.person
                    and self._is_sports_medicine_faculty(locked.person)
                ):
                    baseline_sm_faculty_coverage[slot_key] += 1
            else:
                if locked.activity_id in supervision_required_ids:
                    demand_units = 2 if pgy_level == 1 else 1
                    baseline_resident_demand[slot_key] += demand_units
                    if locked.activity_id in proc_vas_activity_ids:
                        baseline_resident_demand[slot_key] += PROC_VAS_EXTRA_UNITS
                if locked.activity_id in vas_activity_ids:
                    baseline_vas_resident_presence[slot_key] += 1
                if pgy_level == 3:
                    if is_cv:
                        locked_cv_target_counts[week_number]["cv"] += 1
                        locked_cv_target_counts_by_day[(week_number, day_of_week)][
                            "cv"
                        ] += 1
                    elif is_clinic and assignment_counts_toward_fmc_capacity(locked):
                        locked_cv_target_counts[week_number]["clinic"] += 1
                        locked_cv_target_counts_by_day[(week_number, day_of_week)][
                            "clinic"
                        ] += 1

            template = self._get_active_rotation_template(locked, start_date)
            if not template:
                continue
            if person_type != "faculty" and self._should_count_sm_resident_presence(
                template, locked.activity_id, sm_clinic_activity
            ):
                baseline_sm_resident_presence[slot_key] += 1
            locked_counts[
                (locked.person_id, template.id, week_number, locked.activity_id)
            ] += 1

        constraint_count = 0
        activity_min_shortfalls: list[tuple[Any, UUID]] = []
        activity_max_overages: list[tuple[Any, UUID]] = []
        clamped_stats: dict[str, Any] = {
            "total": 0,
            "max_shortage": 0,
            "by_template": defaultdict(lambda: {"count": 0, "max_shortage": 0}),
            "by_activity": defaultdict(lambda: {"count": 0, "max_shortage": 0}),
        }
        for (person_id, template_id, week), slot_indices in slots_by_key.items():
            reqs = requirements_by_template.get(template_id, [])
            if not reqs:
                continue

            req_entries = []
            for req in reqs:
                if req.activity_id not in assignable_ids:
                    continue
                if req.applicable_weeks and week not in req.applicable_weeks:
                    continue

                vars_for_req = [
                    a[s_i, req.activity_id]
                    for s_i in slot_indices
                    if req.activity_id in slot_allowed[s_i]
                ]
                if not vars_for_req:
                    continue

                locked_count = locked_counts.get(
                    (person_id, template_id, week, req.activity_id), 0
                )
                min_needed = max(0, req.min_halfdays - locked_count)
                max_allowed = max(0, req.max_halfdays - locked_count)

                if min_needed > len(vars_for_req):
                    shortage = min_needed - len(vars_for_req)
                    clamped_stats["total"] += 1
                    clamped_stats["max_shortage"] = max(
                        clamped_stats["max_shortage"], shortage
                    )
                    template_entry = clamped_stats["by_template"][template_id]
                    template_entry["count"] += 1
                    template_entry["max_shortage"] = max(
                        template_entry["max_shortage"], shortage
                    )
                    activity_entry = clamped_stats["by_activity"][req.activity_id]
                    activity_entry["count"] += 1
                    activity_entry["max_shortage"] = max(
                        activity_entry["max_shortage"], shortage
                    )
                    logger.warning(
                        f"Clamping min requirement for person={person_id} "
                        f"template={template_id} week={week} "
                        f"activity={req.activity_id}: min={min_needed} "
                        f"available={len(vars_for_req)}"
                    )
                    min_needed = len(vars_for_req)

                if max_allowed < 0:
                    max_allowed = 0
                if max_allowed > len(vars_for_req):
                    max_allowed = len(vars_for_req)

                req_entries.append(
                    {
                        "activity_id": req.activity_id,
                        "vars": vars_for_req,
                        "min": min_needed,
                        "max": max_allowed,
                    }
                )

            if not req_entries:
                continue

            # If per-activity max totals don't cover all slots, relax max to fill
            total_max = sum(entry["max"] for entry in req_entries)
            slack = len(slot_indices) - total_max
            if slack > 0:
                # Prefer giving slack to clinic activity
                clinic_id = clinic_activity.id if clinic_activity else None
                for entry in req_entries:
                    if clinic_id and entry["activity_id"] == clinic_id:
                        room = len(entry["vars"]) - entry["max"]
                        bump = min(slack, room)
                        if bump:
                            entry["max"] += bump
                            slack -= bump
                        break
                # If still slack, distribute to any activity with room
                if slack > 0:
                    for entry in req_entries:
                        room = len(entry["vars"]) - entry["max"]
                        bump = min(slack, room)
                        if bump:
                            entry["max"] += bump
                            slack -= bump
                        if slack <= 0:
                            break
                if slack > 0:
                    logger.warning(
                        "Unable to relax max enough for person=%s template=%s "
                        "week=%s (slack remaining=%s)",
                        person_id,
                        template_id,
                        week,
                        slack,
                    )

            for entry in req_entries:
                min_target = entry["min"]
                max_target = entry["max"]
                vars_for_req = entry["vars"]
                hard_min = 0

                # Clinic hard floor: ensure at least 1 clinic slot when required
                if (
                    not disable_clinic_floor
                    and clinic_activity
                    and entry["activity_id"] == clinic_activity.id
                ):
                    pgy_level = slot_meta[slot_indices[0]].get("pgy_level") or 0
                    cv_allowed = bool(
                        cv_activity
                        and any(
                            cv_activity.id in slot_allowed[s_i] for s_i in slot_indices
                        )
                    )
                    enforce_floor = pgy_level == 1 or not cv_allowed
                    if enforce_floor and min_target > 0 and vars_for_req:
                        hard_min = min(1, len(vars_for_req))
                        model.Add(sum(vars_for_req) >= hard_min)

                # Soft mins for all activities (including clinic above hard floor)
                if min_target > hard_min:
                    shortfall_max = min_target - hard_min
                    shortfall = model.NewIntVar(
                        0,
                        shortfall_max,
                        f"req_shortfall_{constraint_count}",
                    )
                    model.Add(sum(vars_for_req) + shortfall >= min_target)
                    activity_min_shortfalls.append((shortfall, entry["activity_id"]))

                if max_target < len(vars_for_req):
                    overage_max = len(vars_for_req) - max_target
                    overage = model.NewIntVar(
                        0,
                        overage_max,
                        f"req_over_{constraint_count}",
                    )
                    model.Add(sum(vars_for_req) <= max_target + overage)
                    activity_max_overages.append((overage, entry["activity_id"]))
                else:
                    model.Add(sum(vars_for_req) <= max_target)
                constraint_count += 1

        if constraint_count:
            logger.info(f"Added {constraint_count} activity requirement constraints")

        # ==================================================
        # FACULTY CLINIC CAPS (min/max per week)
        # ==================================================
        faculty_clinic_shortfalls: list[Any] = []
        faculty_clinic_overages: list[Any] = []
        if faculty_slots and clinic_activity:
            faculty_by_id: dict[UUID, Person] = {}
            for s_i in faculty_slots:
                slot_person = slots[s_i].person
                if slot_person:
                    faculty_by_id[slot_person.id] = slot_person

            faculty_week_slots: dict[tuple[UUID, int], list[int]] = defaultdict(list)
            for s_i in faculty_slots:
                meta = slot_meta[s_i]
                faculty_week_slots[(meta["person_id"], meta["week"])].append(s_i)

            for (faculty_id, week), slot_indices in faculty_week_slots.items():
                faculty = faculty_by_id.get(faculty_id)
                if not faculty:
                    continue
                min_c, max_c = self._get_faculty_clinic_caps(faculty)
                locked_c = locked_faculty_clinic_counts.get((faculty_id, week), 0)
                min_needed = max(0, min_c - locked_c)
                max_allowed = max(0, max_c - locked_c)

                clinic_vars = [
                    a[s_i, clinic_activity.id]
                    for s_i in slot_indices
                    if clinic_activity.id in slot_allowed[s_i]
                ]
                if not clinic_vars:
                    continue

                over_max = model.NewIntVar(
                    0,
                    len(clinic_vars),
                    f"fac_clinic_over_{str(faculty_id)[:8]}_{week}",
                )
                model.Add(sum(clinic_vars) <= max_allowed + over_max)
                faculty_clinic_overages.append(over_max)

        # ==================================================
        # FACULTY EQUITY (admin + supervision) by role, per week
        # ==================================================
        faculty_admin_equity_ranges: list[Any] = []
        faculty_supervision_equity_ranges: list[Any] = []
        if faculty_slots:
            faculty_by_id: dict[UUID, Person] = {}
            for s_i in faculty_slots:
                slot_person = slots[s_i].person
                if slot_person:
                    faculty_by_id[slot_person.id] = slot_person

            faculty_week_slots: dict[tuple[UUID, int], list[int]] = defaultdict(list)
            for s_i in faculty_slots:
                meta = slot_meta[s_i]
                faculty_week_slots[(meta["person_id"], meta["week"])].append(s_i)

            role_groups: dict[str, list[UUID]] = defaultdict(list)
            for faculty_id, faculty in faculty_by_id.items():
                role = (getattr(faculty, "faculty_role", None) or "core").lower()
                role_groups[role].append(faculty_id)

            week_numbers = sorted(
                {
                    meta["week"]
                    for meta in slot_meta.values()
                    if meta.get("week") is not None
                }
            )

            def add_equity_ranges(
                *,
                activity_ids: set[UUID],
                locked_counts: dict[tuple[UUID, int], int],
                ranges_out: list[Any],
                label: str,
            ) -> None:
                if not activity_ids:
                    return
                for week in week_numbers:
                    for role, faculty_ids in role_groups.items():
                        counts = []
                        max_possible = 0
                        for faculty_id in faculty_ids:
                            slot_indices = faculty_week_slots.get((faculty_id, week))
                            if not slot_indices:
                                continue
                            vars_for_activity = [
                                a[s_i, act_id]
                                for s_i in slot_indices
                                for act_id in activity_ids
                                if act_id in slot_allowed[s_i]
                            ]
                            locked_count = locked_counts.get((faculty_id, week), 0)
                            if not vars_for_activity and locked_count == 0:
                                continue
                            max_slots = len(slot_indices)
                            max_possible = max(
                                max_possible, locked_count + max_slots
                            )
                            count_var = model.NewIntVar(
                                locked_count,
                                locked_count + max_slots,
                                f"{label}_count_{str(faculty_id)[:6]}_{week}",
                            )
                            model.Add(
                                count_var == locked_count + sum(vars_for_activity)
                            )
                            counts.append(count_var)
                        if len(counts) <= 1:
                            continue
                        max_var = model.NewIntVar(0, max_possible, f"{label}_max_{role}_{week}")
                        min_var = model.NewIntVar(0, max_possible, f"{label}_min_{role}_{week}")
                        for count_var in counts:
                            model.Add(count_var <= max_var)
                            model.Add(count_var >= min_var)
                        range_var = model.NewIntVar(0, max_possible, f"{label}_range_{role}_{week}")
                        model.Add(range_var == max_var - min_var)
                        ranges_out.append(range_var)

            add_equity_ranges(
                activity_ids=admin_equity_ids,
                locked_counts=locked_faculty_admin_counts,
                ranges_out=faculty_admin_equity_ranges,
                label="admin_eq",
            )
            add_equity_ranges(
                activity_ids=supervision_equity_ids,
                locked_counts=locked_faculty_supervision_counts,
                ranges_out=faculty_supervision_equity_ranges,
                label="at_eq",
            )

        # ==================================================
        # CV TARGET (faculty + PGY-3) per week
        # Applies to FMC clinic assignments only
        # ==================================================
        cv_target_shortfalls: list[Any] = []
        cv_day_shortfalls: list[Any] = []
        if cv_activity and clinic_activity:
            clinic_id = clinic_activity.id
            cv_id = cv_activity.id
            cv_terms_by_week: dict[int, dict[str, list[Any]]] = defaultdict(
                lambda: {"clinic": [], "cv": []}
            )
            cv_terms_by_week_day: dict[tuple[int, int], dict[str, list[Any]]] = (
                defaultdict(lambda: {"clinic": [], "cv": []})
            )
            for s_i, meta in slot_meta.items():
                week = meta.get("week")
                if week is None:
                    continue
                day_of_week = meta["date"].weekday()
                person_type = meta.get("person_type")
                if person_type == "faculty":
                    if clinic_id not in slot_allowed.get(s_i, []):
                        continue
                else:
                    pgy_level = meta.get("pgy_level") or 0
                    if pgy_level != 3:
                        continue
                    template = templates_by_id.get(meta.get("template_id"))
                    if not template or not template_is_fmc_clinic(template):
                        continue

                allowed = slot_allowed.get(s_i, [])
                if clinic_id in allowed and (s_i, clinic_id) in a:
                    cv_terms_by_week[week]["clinic"].append(a[s_i, clinic_id])
                    cv_terms_by_week_day[(week, day_of_week)]["clinic"].append(
                        a[s_i, clinic_id]
                    )
                if cv_id in allowed and (s_i, cv_id) in a:
                    cv_terms_by_week[week]["cv"].append(a[s_i, cv_id])
                    cv_terms_by_week_day[(week, day_of_week)]["cv"].append(
                        a[s_i, cv_id]
                    )

            for week, terms in cv_terms_by_week.items():
                locked_counts = locked_cv_target_counts.get(
                    week, {"clinic": 0, "cv": 0}
                )
                if (
                    not terms["clinic"]
                    and not terms["cv"]
                    and not locked_counts["clinic"]
                    and not locked_counts["cv"]
                ):
                    continue
                locked_clinic = locked_counts["clinic"]
                locked_cv = locked_counts["cv"]
                total_clinic = (
                    sum(terms["clinic"]) + sum(terms["cv"]) + locked_clinic + locked_cv
                )
                cv_count = sum(terms["cv"]) + locked_cv
                max_terms = (
                    len(terms["clinic"]) + len(terms["cv"]) + locked_clinic + locked_cv
                )
                shortfall = model.NewIntVar(
                    0,
                    CV_TARGET_NUMERATOR * max_terms,
                    f"cv_shortfall_week_{week}",
                )
                model.Add(
                    CV_TARGET_DENOMINATOR * cv_count + shortfall
                    >= CV_TARGET_NUMERATOR * total_clinic
                )
                cv_target_shortfalls.append(shortfall)

            for (week, day_of_week), terms in cv_terms_by_week_day.items():
                locked_counts = locked_cv_target_counts_by_day.get(
                    (week, day_of_week), {"clinic": 0, "cv": 0}
                )
                if (
                    not terms["clinic"]
                    and not terms["cv"]
                    and not locked_counts["clinic"]
                    and not locked_counts["cv"]
                ):
                    continue
                locked_clinic = locked_counts["clinic"]
                locked_cv = locked_counts["cv"]
                total_clinic = (
                    sum(terms["clinic"]) + sum(terms["cv"]) + locked_clinic + locked_cv
                )
                cv_count = sum(terms["cv"]) + locked_cv
                max_terms = (
                    len(terms["clinic"]) + len(terms["cv"]) + locked_clinic + locked_cv
                )
                shortfall = model.NewIntVar(
                    0,
                    CV_TARGET_NUMERATOR * max_terms,
                    f"cv_day_shortfall_w{week}_d{day_of_week}",
                )
                model.Add(
                    CV_TARGET_DENOMINATOR * cv_count + shortfall
                    >= CV_TARGET_NUMERATOR * total_clinic
                )
                cv_day_shortfalls.append(shortfall)

        # ==================================================
        # ACGME AT COVERAGE (faculty supervision)
        # ==================================================
        at_shortfalls: list[Any] = []
        if resident_slots and faculty_slots and at_activity:
            resident_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)
            faculty_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)
            for s_i, meta in slot_meta.items():
                key = (meta["date"], meta["time_of_day"])
                if meta.get("person_type") == "faculty":
                    faculty_slots_by_key[key].append(s_i)
                else:
                    resident_slots_by_key[key].append(s_i)

            all_keys = set(resident_slots_by_key.keys()) | set(
                baseline_resident_demand.keys()
            )
            for slot_key in all_keys:
                slot_date, time_of_day = slot_key
                if slot_date.weekday() >= 5:
                    continue

                demand_terms = []
                for s_i in resident_slots_by_key.get(slot_key, []):
                    pgy_level = slot_meta[s_i].get("pgy_level") or 2
                    demand_units = 2 if pgy_level == 1 else 1
                    for act_id in slot_allowed[s_i]:
                        if act_id in supervision_required_ids:
                            demand_terms.append(a[s_i, act_id] * demand_units)
                            if act_id in proc_vas_activity_ids:
                                demand_terms.append(
                                    a[s_i, act_id] * PROC_VAS_EXTRA_UNITS
                                )

                baseline_demand = baseline_resident_demand.get(slot_key, 0)
                if not demand_terms and baseline_demand == 0:
                    continue

                coverage_terms = []
                for s_i in faculty_slots_by_key.get(slot_key, []):
                    for act_id in slot_allowed[s_i]:
                        if act_id in supervision_provider_ids:
                            coverage_terms.append(a[s_i, act_id])

                baseline_coverage = baseline_faculty_coverage.get(slot_key, 0)
                total_demand = sum(demand_terms) + baseline_demand
                total_coverage = sum(coverage_terms) + baseline_coverage

                # Scale by 4 to avoid fractional demand (PGY1=2, PGY2/3=1)
                # Soft constraint: allow shortfall with penalty
                max_demand = baseline_demand
                for s_i in resident_slots_by_key.get(slot_key, []):
                    allowed = set(slot_allowed[s_i])
                    if not allowed.intersection(supervision_required_ids):
                        continue
                    pgy_level = slot_meta[s_i].get("pgy_level") or 2
                    max_demand += 2 if pgy_level == 1 else 1
                    if allowed.intersection(proc_vas_activity_ids):
                        max_demand += PROC_VAS_EXTRA_UNITS
                shortfall = model.NewIntVar(
                    0,
                    max_demand,
                    f"at_shortfall_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                )
                model.Add(total_coverage * 4 + shortfall >= total_demand)
                at_shortfalls.append(shortfall)

        # ==================================================
        # SPORTS MEDICINE ALIGNMENT
        # SM residents must align with SM faculty SM clinic
        # ==================================================
        if sm_clinic_activity:
            sm_template_ids = {
                t.id for t in templates_by_id.values() if self._is_sm_template(t)
            }
        else:
            sm_template_ids = set()

        sm_shortfalls: list[Any] = []
        if sm_template_ids and sm_clinic_activity and not disable_sm_alignment:
            sm_resident_vars_by_slot: dict[tuple[date, str], list[Any]] = defaultdict(
                list
            )
            sm_faculty_vars_by_slot: dict[tuple[date, str], list[Any]] = defaultdict(
                list
            )

            for s_i, meta in slot_meta.items():
                key = (meta["date"], meta["time_of_day"])
                if meta.get("person_type") == "faculty":
                    slot_person = slots[s_i].person
                    if (
                        slot_person
                        and self._is_sports_medicine_faculty(slot_person)
                        and sm_clinic_activity.id in slot_allowed[s_i]
                    ):
                        sm_faculty_vars_by_slot[key].append(
                            a[s_i, sm_clinic_activity.id]
                        )
                else:
                    if (
                        meta.get("template_id") in sm_template_ids
                        and sm_clinic_activity.id in slot_allowed[s_i]
                    ):
                        # Only SM clinic activity counts toward SM alignment.
                        sm_resident_vars_by_slot[key].append(
                            a[s_i, sm_clinic_activity.id]
                        )

            all_sm_keys = set(sm_resident_vars_by_slot.keys()) | set(
                baseline_sm_resident_presence.keys()
            )
            for slot_key in all_sm_keys:
                slot_date, time_of_day = slot_key
                if slot_date.weekday() >= 5:
                    continue

                faculty_vars = sm_faculty_vars_by_slot.get(slot_key, [])
                baseline_faculty = baseline_sm_faculty_coverage.get(slot_key, 0)

                if baseline_sm_resident_presence.get(slot_key, 0) > 0:
                    shortfall = model.NewIntVar(
                        0,
                        1,
                        f"sm_shortfall_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                    )
                    model.Add(sum(faculty_vars) + baseline_faculty + shortfall >= 1)
                    sm_shortfalls.append(shortfall)
                    continue

                resident_vars = sm_resident_vars_by_slot.get(slot_key, [])
                if not resident_vars:
                    continue

                any_resident = model.NewBoolVar(
                    f"any_sm_res_{slot_date.strftime('%Y%m%d')}_{time_of_day}"
                )
                model.AddMaxEquality(any_resident, resident_vars)
                shortfall = model.NewIntVar(
                    0,
                    1,
                    f"sm_shortfall_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                )
                model.Add(
                    sum(faculty_vars) + baseline_faculty + shortfall >= any_resident
                )
                sm_shortfalls.append(shortfall)
        elif sm_template_ids and sm_clinic_activity and disable_sm_alignment:
            logger.warning("Skipping SM alignment constraints (DISABLE_SM_ALIGNMENT)")

        # ==================================================
        # VASECTOMY ALIGNMENT
        # VAS residents must align with VAS faculty, and faculty VAS requires resident
        # ==================================================
        vas_shortfalls: list[Any] = []
        if vas_activity_ids:
            vas_resident_vars_by_slot: dict[tuple[date, str], list[Any]] = defaultdict(
                list
            )
            vas_faculty_vars_by_slot: dict[tuple[date, str], list[Any]] = defaultdict(
                list
            )

            for s_i, meta in slot_meta.items():
                key = (meta["date"], meta["time_of_day"])
                if meta.get("person_type") == "faculty":
                    for act_id in slot_allowed[s_i]:
                        if act_id in vas_activity_ids:
                            vas_faculty_vars_by_slot[key].append(a[s_i, act_id])
                else:
                    for act_id in slot_allowed[s_i]:
                        if act_id in vas_activity_ids:
                            vas_resident_vars_by_slot[key].append(a[s_i, act_id])

            all_vas_keys = set(vas_resident_vars_by_slot.keys()) | set(
                vas_faculty_vars_by_slot.keys()
            )
            all_vas_keys |= set(baseline_vas_resident_presence.keys())
            all_vas_keys |= set(baseline_vas_faculty_coverage.keys())

            for slot_key in all_vas_keys:
                slot_date, time_of_day = slot_key
                resident_vars = vas_resident_vars_by_slot.get(slot_key, [])
                faculty_vars = vas_faculty_vars_by_slot.get(slot_key, [])
                baseline_resident = baseline_vas_resident_presence.get(slot_key, 0)
                baseline_faculty = baseline_vas_faculty_coverage.get(slot_key, 0)

                if not resident_vars and not faculty_vars and not baseline_resident and not baseline_faculty:
                    continue

                shortfall = model.NewIntVar(
                    0,
                    1,
                    f"vas_shortfall_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                )

                # Resident VAS requires faculty VAS coverage.
                if baseline_resident > 0:
                    model.Add(sum(faculty_vars) + baseline_faculty + shortfall >= 1)
                elif resident_vars:
                    any_resident = model.NewBoolVar(
                        f"any_vas_res_{slot_date.strftime('%Y%m%d')}_{time_of_day}"
                    )
                    model.AddMaxEquality(any_resident, resident_vars)
                    model.Add(
                        sum(faculty_vars) + baseline_faculty + shortfall >= any_resident
                    )

                # Faculty VAS requires resident presence.
                if baseline_faculty > 0:
                    model.Add(sum(resident_vars) + baseline_resident + shortfall >= 1)
                elif faculty_vars:
                    any_faculty = model.NewBoolVar(
                        f"any_vas_fac_{slot_date.strftime('%Y%m%d')}_{time_of_day}"
                    )
                    model.AddMaxEquality(any_faculty, faculty_vars)
                    model.Add(
                        sum(resident_vars) + baseline_resident + shortfall >= any_faculty
                    )

                vas_shortfalls.append(shortfall)

        # ==================================================
        # CONSTRAINT: Physical Capacity (Soft 6, Hard 8 per slot)
        # Session 136: Clinic has limited exam rooms
        # Includes baseline occupancy from locked/preloaded slots.
        # ==================================================
        SOFT_PHYSICAL_CAPACITY = 6
        HARD_PHYSICAL_CAPACITY = 8

        # Group slots by (date, time_of_day)
        slot_groups: dict[tuple[date, str], list[int]] = defaultdict(list)
        for s_i, slot in enumerate(slots):
            key = (slot.date, slot.time_of_day)
            slot_groups[key].append(s_i)

        # Baseline occupancy from locked/preloaded slots not in solver
        slot_ids = {slot.id for slot in slots}
        baseline_non_sm: dict[tuple[date, str], int] = defaultdict(int)
        baseline_sm_present: dict[tuple[date, str], int] = defaultdict(int)
        baseline_stmt = (
            select(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
            .where(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
        )
        for assignment in self.session.execute(baseline_stmt).scalars():
            if assignment.id in slot_ids:
                continue  # handled by solver
            if not assignment_counts_toward_fmc_capacity(assignment):
                continue
            if activity_is_sm_capacity(assignment.activity):
                baseline_sm_present[(assignment.date, assignment.time_of_day)] = 1
                continue
            baseline_non_sm[(assignment.date, assignment.time_of_day)] += (
                activity_capacity_units(assignment.activity)
            )

        # For each time slot, sum(clinical activities) + baseline <= HARD
        has_capacity = (
            any(slot_capacity_ids.values())
            or any(baseline_non_sm.values())
            or any(baseline_sm_present.values())
        )
        overage_vars: list[Any] = []
        if has_capacity and not disable_physical_capacity:
            enforced_groups = 0
            overhard_groups = 0
            overhard_examples: list[str] = []
            overhard_details: list[dict[str, Any]] = []
            for (slot_date, time_of_day), slot_indices in slot_groups.items():
                # Skip weekends
                if slot_date.weekday() >= 5:
                    continue

                # Sum of non-SM clinical assignments for this slot
                slot_non_sm_sum = sum(
                    a[s_i, act_id] * activity_capacity_units(activity_by_id.get(act_id))
                    for s_i in slot_indices
                    for act_id in slot_capacity_ids[s_i]
                    if act_id not in set(slot_sm_capacity_ids[s_i])
                )

                sm_vars = [
                    a[s_i, act_id]
                    for s_i in slot_indices
                    for act_id in slot_sm_capacity_ids[s_i]
                ]
                sm_present = 0
                if sm_vars:
                    sm_present = model.NewBoolVar(
                        f"sm_present_{slot_date.strftime('%Y%m%d')}_{time_of_day}"
                    )
                    model.AddMaxEquality(sm_present, sm_vars)

                baseline = baseline_non_sm.get((slot_date, time_of_day), 0)
                baseline_sm = baseline_sm_present.get((slot_date, time_of_day), 0)
                forced_non_sm = 0
                forced_sm = False
                for s_i in slot_indices:
                    allowed = set(slot_allowed[s_i])
                    if not allowed:
                        continue
                    capacity_allowed = set(slot_capacity_ids[s_i])
                    if not capacity_allowed or not allowed.issubset(capacity_allowed):
                        continue
                    sm_allowed = set(slot_sm_capacity_ids[s_i])
                    if capacity_allowed and capacity_allowed.issubset(sm_allowed):
                        forced_sm = True
                    else:
                        forced_non_sm += 1
                min_required = (
                    forced_non_sm + (1 if forced_sm else 0) + baseline + baseline_sm
                )
                if min_required > HARD_PHYSICAL_CAPACITY:
                    overhard_groups += 1
                    if len(overhard_examples) < 5:
                        overhard_examples.append(
                            f"{slot_date} {time_of_day} min={min_required}"
                        )
                    overhard_details.append(
                        self._build_physical_capacity_detail(
                            slot_date=slot_date,
                            time_of_day=time_of_day,
                            slot_indices=slot_indices,
                            slot_meta=slot_meta,
                            slot_allowed=slot_allowed,
                            slot_capacity_ids=slot_capacity_ids,
                            slot_sm_capacity_ids=slot_sm_capacity_ids,
                            activity_by_id=activity_by_id,
                            templates_by_id=templates_by_id,
                            baseline_non_sm=baseline,
                            baseline_sm=baseline_sm,
                            min_required=min_required,
                        )
                    )
                    continue

                total_clinic = slot_non_sm_sum + baseline + baseline_sm
                if sm_vars:
                    total_clinic += sm_present

                # Hard constraint: at most 8 in clinic per slot
                model.Add(total_clinic <= HARD_PHYSICAL_CAPACITY)

                # Soft constraint: penalize clinic counts above 6
                over_expr = model.NewIntVar(
                    -HARD_PHYSICAL_CAPACITY,
                    HARD_PHYSICAL_CAPACITY,
                    f"cap_over_expr_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                )
                model.Add(over_expr == total_clinic - SOFT_PHYSICAL_CAPACITY)
                overage = model.NewIntVar(
                    0,
                    max(HARD_PHYSICAL_CAPACITY - SOFT_PHYSICAL_CAPACITY, 0),
                    f"cap_over_{slot_date.strftime('%Y%m%d')}_{time_of_day}",
                )
                model.AddMaxEquality(overage, [over_expr, 0])
                overage_vars.append(overage)
                enforced_groups += 1

            if overhard_groups:
                examples = ", ".join(overhard_examples)
                logger.error(
                    f"Physical capacity infeasible: {overhard_groups} of "
                    f"{len(slot_groups)} slots have minimum clinic demand above "
                    f"hard {HARD_PHYSICAL_CAPACITY}. Examples: {examples}"
                )
                self._write_failure_snapshot(
                    {
                        "stage": "capacity",
                        "status": "error",
                        "block_number": block_number,
                        "academic_year": academic_year,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "capacity": {
                            "hard_limit": HARD_PHYSICAL_CAPACITY,
                            "soft_limit": SOFT_PHYSICAL_CAPACITY,
                            "slot_groups": len(slot_groups),
                            "overhard_groups": overhard_groups,
                            "examples": overhard_examples,
                            "details": overhard_details[:10],
                        },
                    }
                )
                return {
                    "success": False,
                    "assignments_updated": 0,
                    "status": "error",
                    "message": (
                        "Physical capacity infeasible (min clinic demand exceeds hard "
                        f"{HARD_PHYSICAL_CAPACITY})"
                    ),
                    "details": overhard_details,
                }

            if enforced_groups:
                logger.info(
                    f"Added physical capacity constraints (soft {SOFT_PHYSICAL_CAPACITY}, "
                    f"hard {HARD_PHYSICAL_CAPACITY}) for {enforced_groups} of "
                    f"{len(slot_groups)} time slots"
                )
        elif disable_physical_capacity:
            logger.warning(
                "Skipping physical capacity constraints (DISABLE_PHYSICAL_CAPACITY)"
            )

        # ==================================================
        # OBJECTIVE: Maximize clinic (C) assignments
        # (Most slots should be clinic for outpatient rotations)
        # Constraint above limits this to respect physical capacity
        # ==================================================
        objective_expr = None
        if clinic_activity and clinic_activity.id in assignable_ids:
            clinic_id = clinic_activity.id
            clinic_count = sum(
                a[s_i, clinic_id]
                for s_i in resident_slots
                if clinic_id in slot_allowed[s_i]
            )
            objective_expr = clinic_count

        admin_bonus_vars = [
            a[s_i, act_id]
            for s_i, act_id in faculty_admin_activity_by_slot.items()
            if (s_i, act_id) in a
        ]
        if admin_bonus_vars:
            admin_bonus = sum(admin_bonus_vars) * FACULTY_ADMIN_BONUS
            objective_expr = (
                objective_expr + admin_bonus
                if objective_expr is not None
                else admin_bonus
            )

        if faculty_clinic_shortfalls:
            shortfall_sum = sum(faculty_clinic_shortfalls)
            penalty = shortfall_sum * FACULTY_CLINIC_SHORTFALL_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if activity_min_shortfalls:
            penalties = []
            for shortfall, activity_id in activity_min_shortfalls:
                weight = (
                    CLINIC_MIN_SHORTFALL_PENALTY
                    if clinic_activity and activity_id == clinic_activity.id
                    else ACTIVITY_MIN_SHORTFALL_PENALTY
                )
                penalties.append(shortfall * weight)
            if penalties:
                penalty = sum(penalties)
                objective_expr = (
                    objective_expr - penalty if objective_expr is not None else -penalty
                )

        if activity_max_overages:
            penalties = []
            for overage, activity_id in activity_max_overages:
                weight = (
                    CLINIC_MAX_OVERAGE_PENALTY
                    if clinic_activity and activity_id == clinic_activity.id
                    else ACTIVITY_MAX_OVERAGE_PENALTY
                )
                penalties.append(overage * weight)
            if penalties:
                penalty = sum(penalties)
                objective_expr = (
                    objective_expr - penalty if objective_expr is not None else -penalty
                )

        if at_shortfalls:
            penalty = sum(at_shortfalls) * AT_COVERAGE_SHORTFALL_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if sm_shortfalls:
            penalty = sum(sm_shortfalls) * SM_ALIGNMENT_SHORTFALL_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if vas_shortfalls:
            penalty = sum(vas_shortfalls) * VAS_ALIGNMENT_SHORTFALL_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if cv_penalty_terms:
            penalties = [var * weight for var, weight in cv_penalty_terms]
            if penalties:
                penalty = sum(penalties)
                objective_expr = (
                    objective_expr - penalty if objective_expr is not None else -penalty
                )

        if vas_penalty_terms:
            penalties = [var * weight for var, weight in vas_penalty_terms]
            if penalties:
                penalty = sum(penalties)
                objective_expr = (
                    objective_expr - penalty if objective_expr is not None else -penalty
                )

        if oic_clinical_avoid_terms:
            penalties = [var * weight for var, weight in oic_clinical_avoid_terms]
            if penalties:
                penalty = sum(penalties)
                objective_expr = (
                    objective_expr - penalty if objective_expr is not None else -penalty
                )

        if cv_target_shortfalls:
            penalty = sum(cv_target_shortfalls) * CV_TARGET_SHORTFALL_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if cv_day_shortfalls:
            penalty = sum(cv_day_shortfalls) * CV_DAILY_SPREAD_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if faculty_admin_equity_ranges:
            penalty = sum(faculty_admin_equity_ranges) * FACULTY_ADMIN_EQUITY_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if faculty_supervision_equity_ranges:
            penalty = sum(faculty_supervision_equity_ranges) * FACULTY_AT_EQUITY_PENALTY
            objective_expr = (
                objective_expr - penalty if objective_expr is not None else -penalty
            )

        if overage_vars:
            overage_penalty = sum(overage_vars) * PHYSICAL_CAPACITY_SOFT_PENALTY
            objective_expr = (
                objective_expr - overage_penalty
                if objective_expr is not None
                else -overage_penalty
            )
        if faculty_clinic_overages:
            overage_penalty = sum(faculty_clinic_overages) * FACULTY_CLINIC_OVERAGE_PENALTY
            objective_expr = (
                objective_expr - overage_penalty
                if objective_expr is not None
                else -overage_penalty
            )

        if objective_expr is not None:
            model.Maximize(objective_expr)

        # ==================================================
        # SOLVE
        # ==================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout_seconds
        solver.parameters.num_search_workers = self.num_workers

        status = solver.Solve(model)
        runtime = time.time() - start_time

        status_name = solver.StatusName(status)
        logger.info(f"Activity solver status: {status_name} ({runtime:.2f}s)")

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            coverage_diagnostics = self._build_at_coverage_diagnostics(
                slot_meta=slot_meta,
                slot_allowed=slot_allowed,
                baseline_resident_demand=baseline_resident_demand,
                baseline_faculty_coverage=baseline_faculty_coverage,
                supervision_required_ids=supervision_required_ids,
                supervision_provider_ids=supervision_provider_ids,
                proc_vas_activity_ids=proc_vas_activity_ids,
            )
            sm_alignment_diagnostics = self._build_sm_alignment_diagnostics(
                slot_meta=slot_meta,
                slot_allowed=slot_allowed,
                baseline_sm_resident_presence=baseline_sm_resident_presence,
                baseline_sm_faculty_coverage=baseline_sm_faculty_coverage,
                sm_clinic_activity=sm_clinic_activity,
            )
            slot_allowed_empty = sum(
                1 for allowed in slot_allowed.values() if not allowed
            )
            template_requirement_counts = {
                template_id: len(reqs)
                for template_id, reqs in requirements_by_template.items()
            }
            outpatient_templates = [
                t
                for t in templates_by_id.values()
                if (t.rotation_type or "").lower() in OUTPATIENT_ACTIVITY_TYPES
            ]
            missing_outpatient = [
                t
                for t in outpatient_templates
                if not requirements_by_template.get(t.id)
            ]
            clamped_by_template = []
            for template_id, data in clamped_stats["by_template"].items():
                template = templates_by_id.get(template_id)
                clamped_by_template.append(
                    {
                        "template_id": str(template_id),
                        "template_name": getattr(template, "name", None),
                        "rotation_type": getattr(template, "rotation_type", None),
                        "count": data["count"],
                        "max_shortage": data["max_shortage"],
                    }
                )
            clamped_by_template.sort(key=lambda entry: entry["count"], reverse=True)
            clamped_by_activity = []
            for activity_id, data in clamped_stats["by_activity"].items():
                activity = activity_by_id.get(activity_id)
                clamped_by_activity.append(
                    {
                        "activity_id": str(activity_id),
                        "activity_code": getattr(activity, "code", None),
                        "activity_display": getattr(
                            activity, "display_abbreviation", None
                        ),
                        "count": data["count"],
                        "max_shortage": data["max_shortage"],
                    }
                )
            clamped_by_activity.sort(key=lambda entry: entry["count"], reverse=True)
            self._write_failure_snapshot(
                {
                    "stage": "solve",
                    "status": "infeasible",
                    "solver_status": status_name,
                    "runtime_seconds": runtime,
                    "block_number": block_number,
                    "academic_year": academic_year,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "counts": {
                        "slots_total": len(slots),
                        "slots_resident": len(resident_slots),
                        "slots_faculty": len(faculty_slots),
                        "slots_allowed_empty": slot_allowed_empty,
                        "templates_total": len(templates_by_id),
                        "templates_outpatient": len(outpatient_templates),
                        "requirements_total": sum(
                            len(reqs) for reqs in requirements_by_template.values()
                        ),
                        "activities_total": len(all_activities),
                        "activities_assignable": len(assignable_ids),
                    },
                    "activities": {
                        "clinic_activity": getattr(clinic_activity, "code", None),
                        "clinic_activity_display": getattr(
                            clinic_activity, "display_abbreviation", None
                        ),
                        "at_activity": getattr(at_activity, "code", None),
                        "supervision_required_count": len(supervision_required_ids),
                        "supervision_provider_count": len(supervision_provider_ids),
                        "capacity_activity_count": len(capacity_activity_ids),
                        "sm_capacity_count": len(sm_capacity_ids),
                    },
                    "requirements": {
                        "template_requirement_counts": {
                            str(k): v for k, v in template_requirement_counts.items()
                        },
                        "missing_outpatient_templates": [
                            {
                                "id": str(template.id),
                                "name": template.name,
                                "abbreviation": template.abbreviation,
                                "rotation_type": template.rotation_type,
                            }
                            for template in missing_outpatient
                        ],
                        "clamped_min_requirements": {
                            "total": clamped_stats["total"],
                            "max_shortage": clamped_stats["max_shortage"],
                            "by_template": clamped_by_template[:20],
                            "by_activity": clamped_by_activity[:20],
                        },
                    },
                    "coverage": coverage_diagnostics,
                    "sm_alignment": sm_alignment_diagnostics,
                    "settings": {
                        "disable_sm_alignment": disable_sm_alignment,
                        "disable_clinic_floor": disable_clinic_floor,
                        "disable_physical_capacity": disable_physical_capacity,
                    },
                }
            )
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "infeasible",
                "solver_status": status_name,
                "runtime_seconds": runtime,
            }

        # ==================================================
        # EXTRACT SOLUTION & UPDATE DATABASE
        # ==================================================
        updated = 0
        for s_i, slot in enumerate(slots):
            for act_id in slot_allowed[s_i]:
                if solver.Value(a[s_i, act_id]) == 1:
                    activity = activity_by_id.get(act_id)
                    template = templates_by_id.get(slot_meta[s_i].get("template_id"))
                    slot.activity_id = act_id
                    slot.counts_toward_fmc_capacity = (
                        activity_counts_toward_fmc_capacity_for_template(
                            activity, template
                        )
                    )
                    slot.source = AssignmentSource.SOLVER.value
                    updated += 1
                    break

        self.session.flush()
        logger.info(f"Activity solver updated {updated} slots")

        if activity_min_shortfalls:
            min_total = sum(
                solver.Value(var) for var, _activity_id in activity_min_shortfalls
            )
            if min_total:
                logger.warning(f"Activity min shortfall total: {min_total}")
            else:
                logger.info("Activity min shortfall total: 0")

        if activity_max_overages:
            max_total = sum(
                solver.Value(var) for var, _activity_id in activity_max_overages
            )
            if max_total:
                logger.warning(f"Activity max overage total: {max_total}")
            else:
                logger.info("Activity max overage total: 0")

        if at_shortfalls:
            at_total = sum(solver.Value(var) for var in at_shortfalls)
            if at_total:
                logger.warning(f"AT coverage shortfall total: {at_total}")
            else:
                logger.info("AT coverage shortfall total: 0")

        if sm_shortfalls:
            sm_total = sum(solver.Value(var) for var in sm_shortfalls)
            if sm_total:
                logger.warning(f"SM alignment shortfall total: {sm_total}")
            else:
                logger.info("SM alignment shortfall total: 0")

        if vas_shortfalls:
            vas_total = sum(solver.Value(var) for var in vas_shortfalls)
            if vas_total:
                logger.warning(f"VAS alignment shortfall total: {vas_total}")
            else:
                logger.info("VAS alignment shortfall total: 0")

        if faculty_admin_equity_ranges:
            admin_eq_total = sum(
                solver.Value(var) for var in faculty_admin_equity_ranges
            )
            logger.info(f"Faculty admin equity range total: {admin_eq_total}")

        if faculty_supervision_equity_ranges:
            at_eq_total = sum(
                solver.Value(var) for var in faculty_supervision_equity_ranges
            )
            logger.info(f"Faculty AT equity range total: {at_eq_total}")

        return {
            "success": True,
            "assignments_updated": updated,
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "solver_status": status_name,
            "runtime_seconds": runtime,
        }

    def _load_activities(self) -> list[Activity]:
        """Load all active (non-archived) activities."""
        stmt = select(Activity).where(~Activity.is_archived)
        result = self.session.execute(stmt)
        activities = list(result.scalars().all())

        # Cache for lookup
        for activity in activities:
            self._activity_cache[activity.code] = activity
            if activity.display_abbreviation:
                self._activity_cache[activity.display_abbreviation] = activity

        return activities

    def _write_failure_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Write a PII-free failure snapshot to disk for debugging."""
        output_dir = Path(
            os.environ.get("SCHEDULE_FAILURE_SNAPSHOT_DIR", "/tmp")
        ).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            snapshot = dict(snapshot)
            snapshot["timestamp"] = datetime.utcnow().isoformat() + "Z"
            stage = snapshot.get("stage", "unknown")
            block_number = snapshot.get("block_number", "unknown")
            academic_year = snapshot.get("academic_year", "unknown")
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            path = (
                output_dir
                / f"activity_failure_{stage}_block{block_number}_ay{academic_year}_{stamp}.json"
            )
            path.write_text(json.dumps(snapshot, indent=2, default=str))
            logger.error(f"Wrote activity failure snapshot to {path}")
        except Exception as exc:
            logger.error(f"Failed to write activity failure snapshot: {exc}")

    @staticmethod
    def _build_physical_capacity_detail(
        *,
        slot_date: date,
        time_of_day: str,
        slot_indices: list[int],
        slot_meta: dict[int, dict[str, Any]],
        slot_allowed: dict[int, list[UUID]],
        slot_capacity_ids: dict[int, list[UUID]],
        slot_sm_capacity_ids: dict[int, list[UUID]],
        activity_by_id: dict[UUID, Activity],
        templates_by_id: dict[UUID, RotationTemplate],
        baseline_non_sm: int,
        baseline_sm: int,
        min_required: int,
    ) -> dict[str, Any]:
        """Return diagnostics for a single slot group that exceeds hard capacity."""
        forced_non_sm = 0
        forced_sm_slots = 0
        forced_slots: list[dict[str, Any]] = []

        for s_i in slot_indices:
            allowed = set(slot_allowed.get(s_i, []))
            if not allowed:
                continue

            capacity_allowed = set(slot_capacity_ids.get(s_i, []))
            if not capacity_allowed or not allowed.issubset(capacity_allowed):
                continue

            sm_allowed = set(slot_sm_capacity_ids.get(s_i, []))
            is_sm_only = bool(capacity_allowed) and capacity_allowed.issubset(
                sm_allowed
            )
            if is_sm_only:
                forced_sm_slots += 1
            else:
                forced_non_sm += 1

            meta = slot_meta.get(s_i, {})
            template_id = meta.get("template_id")
            template = templates_by_id.get(template_id) if template_id else None

            def _activity_label(act_id: UUID) -> str:
                activity = activity_by_id.get(act_id)
                if not activity:
                    return str(act_id)
                return activity.display_abbreviation or activity.code or str(act_id)

            forced_slots.append(
                {
                    "slot_index": s_i,
                    "person_id": str(meta.get("person_id")),
                    "person_type": meta.get("person_type"),
                    "template_id": str(template_id) if template_id else None,
                    "template_name": getattr(template, "name", None),
                    "allowed": [_activity_label(act_id) for act_id in allowed],
                    "capacity_allowed": [
                        _activity_label(act_id) for act_id in capacity_allowed
                    ],
                    "forced_sm_only": is_sm_only,
                }
            )

        forced_sm_capacity = 1 if forced_sm_slots > 0 else 0

        return {
            "date": str(slot_date),
            "time_of_day": time_of_day,
            "baseline_non_sm": baseline_non_sm,
            "baseline_sm": baseline_sm,
            "forced_non_sm": forced_non_sm,
            "forced_sm_slots": forced_sm_slots,
            "forced_sm_capacity": forced_sm_capacity,
            "min_required": min_required,
            "forced_slots": forced_slots,
        }

    @staticmethod
    def _build_at_coverage_diagnostics(
        *,
        slot_meta: dict[int, dict[str, Any]],
        slot_allowed: dict[int, list[UUID]],
        baseline_resident_demand: dict[tuple[date, str], int],
        baseline_faculty_coverage: dict[tuple[date, str], int],
        supervision_required_ids: set[UUID],
        supervision_provider_ids: set[UUID],
        proc_vas_activity_ids: set[UUID],
    ) -> dict[str, Any]:
        """Summarize per-slot AT coverage bounds to explain infeasibility."""
        resident_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)
        faculty_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)

        for s_i, meta in slot_meta.items():
            key = (meta["date"], meta["time_of_day"])
            if meta.get("person_type") == "faculty":
                faculty_slots_by_key[key].append(s_i)
            else:
                resident_slots_by_key[key].append(s_i)

        all_keys = set(resident_slots_by_key.keys()) | set(faculty_slots_by_key.keys())
        all_keys |= set(baseline_resident_demand.keys())
        all_keys |= set(baseline_faculty_coverage.keys())

        slot_summaries: list[dict[str, Any]] = []
        hard_violations = 0

        for slot_key in sorted(all_keys):
            slot_date, time_of_day = slot_key
            if slot_date.weekday() >= 5:
                continue

            min_demand = baseline_resident_demand.get(slot_key, 0)
            max_demand = baseline_resident_demand.get(slot_key, 0)
            forced_residents = 0
            flexible_residents = 0

            for s_i in resident_slots_by_key.get(slot_key, []):
                allowed = set(slot_allowed.get(s_i, []))
                if not allowed:
                    continue
                pgy_level = slot_meta[s_i].get("pgy_level") or 2
                demand_units = 2 if pgy_level == 1 else 1
                if allowed.issubset(supervision_required_ids):
                    min_demand += demand_units
                    forced_residents += 1
                    if allowed.issubset(proc_vas_activity_ids):
                        min_demand += PROC_VAS_EXTRA_UNITS
                if allowed.intersection(supervision_required_ids):
                    max_demand += demand_units
                    flexible_residents += 1
                    if allowed.intersection(proc_vas_activity_ids):
                        max_demand += PROC_VAS_EXTRA_UNITS

            min_coverage = baseline_faculty_coverage.get(slot_key, 0)
            max_coverage = baseline_faculty_coverage.get(slot_key, 0)
            forced_faculty = 0
            flexible_faculty = 0

            for s_i in faculty_slots_by_key.get(slot_key, []):
                allowed = set(slot_allowed.get(s_i, []))
                if not allowed:
                    continue
                if allowed.issubset(supervision_provider_ids):
                    min_coverage += 1
                    max_coverage += 1
                    forced_faculty += 1
                elif allowed.intersection(supervision_provider_ids):
                    max_coverage += 1
                    flexible_faculty += 1

            gap_min = min_demand - (max_coverage * 4)
            gap_max = max_demand - (max_coverage * 4)
            if gap_min > 0:
                hard_violations += 1

            slot_summaries.append(
                {
                    "date": str(slot_date),
                    "time_of_day": time_of_day,
                    "min_demand": min_demand,
                    "max_demand": max_demand,
                    "min_coverage": min_coverage,
                    "max_coverage": max_coverage,
                    "gap_min": gap_min,
                    "gap_max": gap_max,
                    "forced_residents": forced_residents,
                    "flexible_residents": flexible_residents,
                    "forced_faculty": forced_faculty,
                    "flexible_faculty": flexible_faculty,
                }
            )

        slot_summaries.sort(key=lambda s: (s["gap_min"], s["gap_max"]), reverse=True)
        return {
            "slots_analyzed": len(slot_summaries),
            "hard_violations": hard_violations,
            "top_gaps": slot_summaries[:20],
        }

    @staticmethod
    def _build_sm_alignment_diagnostics(
        *,
        slot_meta: dict[int, dict[str, Any]],
        slot_allowed: dict[int, list[UUID]],
        baseline_sm_resident_presence: dict[tuple[date, str], int],
        baseline_sm_faculty_coverage: dict[tuple[date, str], int],
        sm_clinic_activity: Activity | None,
    ) -> dict[str, Any]:
        """Summarize SM alignment feasibility by slot."""
        if not sm_clinic_activity:
            return {"enabled": False}

        resident_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)
        faculty_slots_by_key: dict[tuple[date, str], list[int]] = defaultdict(list)
        for s_i, meta in slot_meta.items():
            key = (meta["date"], meta["time_of_day"])
            if meta.get("person_type") == "faculty":
                faculty_slots_by_key[key].append(s_i)
            else:
                resident_slots_by_key[key].append(s_i)

        all_keys = set(resident_slots_by_key.keys()) | set(faculty_slots_by_key.keys())
        all_keys |= set(baseline_sm_resident_presence.keys())
        all_keys |= set(baseline_sm_faculty_coverage.keys())

        slot_summaries: list[dict[str, Any]] = []
        hard_violations = 0

        for slot_key in sorted(all_keys):
            slot_date, time_of_day = slot_key
            if slot_date.weekday() >= 5:
                continue

            baseline_resident = baseline_sm_resident_presence.get(slot_key, 0)
            baseline_faculty = baseline_sm_faculty_coverage.get(slot_key, 0)

            forced_resident = 0
            optional_resident = 0
            for s_i in resident_slots_by_key.get(slot_key, []):
                allowed = set(slot_allowed.get(s_i, []))
                if not allowed or sm_clinic_activity.id not in allowed:
                    continue
                if allowed == {sm_clinic_activity.id}:
                    forced_resident += 1
                else:
                    optional_resident += 1

            forced_faculty = 0
            optional_faculty = 0
            for s_i in faculty_slots_by_key.get(slot_key, []):
                allowed = set(slot_allowed.get(s_i, []))
                if not allowed or sm_clinic_activity.id not in allowed:
                    continue
                if allowed == {sm_clinic_activity.id}:
                    forced_faculty += 1
                else:
                    optional_faculty += 1

            min_residents = baseline_resident + forced_resident
            max_faculty = baseline_faculty + forced_faculty + optional_faculty
            gap = min_residents - max_faculty
            if gap > 0:
                hard_violations += 1

            slot_summaries.append(
                {
                    "date": str(slot_date),
                    "time_of_day": time_of_day,
                    "baseline_resident": baseline_resident,
                    "baseline_faculty": baseline_faculty,
                    "forced_resident": forced_resident,
                    "optional_resident": optional_resident,
                    "forced_faculty": forced_faculty,
                    "optional_faculty": optional_faculty,
                    "min_residents": min_residents,
                    "max_faculty": max_faculty,
                    "gap": gap,
                }
            )

        slot_summaries.sort(key=lambda s: s["gap"], reverse=True)
        return {
            "enabled": True,
            "slots_analyzed": len(slot_summaries),
            "hard_violations": hard_violations,
            "top_gaps": slot_summaries[:20],
        }

    def _get_activity_by_code(self, code: str) -> Activity | None:
        """Get activity by code from cache."""
        return self._activity_cache.get(code)

    def _activity_ids_for_codes(
        self, activities: list[Activity], codes: set[str]
    ) -> set[UUID]:
        """Return activity IDs whose code or display abbreviation matches codes."""
        normalized = {c.strip().upper() for c in codes}
        matched: set[UUID] = set()
        for activity in activities:
            code = (activity.code or "").strip().upper()
            abbrev = (activity.display_abbreviation or "").strip().upper()
            if code in normalized or abbrev in normalized:
                matched.add(activity.id)
        return matched

    def _activity_matches_template(
        self, activity: Activity | None, template: RotationTemplate
    ) -> bool:
        """Return True if activity corresponds to the rotation template itself."""
        if not activity:
            return False
        template_abbrev = (template.abbreviation or "").strip().upper()
        base_abbrev = template_abbrev.replace("-AM", "").replace("-PM", "")
        template_name = (template.name or "").strip().upper()
        base_name = template_name.replace(" AM", "").replace(" PM", "")

        activity_abbrev = (activity.display_abbreviation or "").strip().upper()
        activity_code = (activity.code or "").strip().upper()
        template_code = activity_code_from_name(template.name).upper()
        base_template_code = activity_code_from_name(base_name).upper()

        return activity_abbrev in {base_abbrev, base_name} or activity_code in {
            template_code,
            base_template_code,
        }

    def _get_faculty_clinic_caps(self, faculty: Person) -> tuple[int, int]:
        """Return (min, max) weekly clinic half-days for a faculty member."""
        max_c = getattr(faculty, "max_clinic_halfdays_per_week", 4) or 0
        if max_c < 0:
            max_c = 0
        # Policy: no minimum clinic requirement to preserve AT capacity.
        return 0, max_c

    def _get_admin_activity_for_faculty(
        self, faculty: Person, activities: dict[str, Activity]
    ) -> Activity | None:
        """Return admin activity based on faculty.admin_type (GME/DFM/SM)."""
        admin_type = (getattr(faculty, "admin_type", "GME") or "GME").upper()
        code = ADMIN_ACTIVITY_CODES.get(admin_type, "gme")
        return activities.get(code) or activities.get(code.upper())

    def _is_sports_medicine_faculty(self, faculty: Person) -> bool:
        """Return True if faculty is Sports Medicine."""
        if hasattr(faculty, "is_sports_medicine"):
            return bool(faculty.is_sports_medicine)
        role = getattr(faculty, "faculty_role", None)
        return role == "sports_med"

    def _is_sm_template(self, template: RotationTemplate) -> bool:
        """Return True if rotation template represents Sports Medicine."""
        if hasattr(template, "requires_specialty") and template.requires_specialty:
            if template.requires_specialty == "Sports Medicine":
                return True
        name = getattr(template, "name", "") or ""
        abbrev = getattr(template, "abbreviation", "") or ""
        name_upper = name.upper()
        abbrev_upper = abbrev.upper()
        return (
            "SPORTS MEDICINE" in name_upper
            or name_upper == "SM"
            or abbrev_upper == "SM"
        )

    def _should_count_sm_resident_presence(
        self,
        template: RotationTemplate | None,
        activity_id: UUID | None,
        sm_clinic_activity: Activity | None,
    ) -> bool:
        """Return True if a locked resident slot should count for SM alignment."""
        if not template or not sm_clinic_activity or not activity_id:
            return False
        if activity_id != sm_clinic_activity.id:
            return False
        return self._is_sm_template(template)

    def _get_week_number(self, slot_date: date, block_start: date) -> int:
        """Get week number (1-4) for a slot within a block."""
        days_into_block = (slot_date - block_start).days
        return (days_into_block // 7) + 1

    def _get_active_rotation_template(
        self,
        slot: HalfDayAssignment,
        block_start: date,
    ) -> RotationTemplate | None:
        """Resolve rotation template for a given slot (block_assignment or solver)."""
        if slot.block_assignment:
            if slot.block_assignment.secondary_rotation_template_id:
                day_in_block = (slot.date - block_start).days + 1
                if day_in_block > BLOCK_HALF_DAY:
                    return slot.block_assignment.secondary_rotation_template
            return slot.block_assignment.rotation_template

        return self._assignment_rotation_map.get(
            (slot.person_id, slot.date, slot.time_of_day)
        )

    def _missing_outpatient_requirements(
        self,
        templates_by_id: dict[UUID, RotationTemplate],
        requirements_by_template: dict[UUID, list[RotationActivityRequirement]],
    ) -> list[RotationTemplate]:
        """Return outpatient templates that lack explicit activity requirements."""
        missing: list[RotationTemplate] = []
        for template in templates_by_id.values():
            rotation_type = (template.rotation_type or "").lower()
            if rotation_type not in OUTPATIENT_ACTIVITY_TYPES:
                continue
            if requirements_by_template.get(template.id):
                continue
            missing.append(template)
        return missing

    def _load_slots(
        self,
        start_date: date,
        end_date: date,
        sources: list[str],
        person_ids: set[UUID] | None = None,
    ) -> list[HalfDayAssignment]:
        """Load half-day slots with relationships and source filter."""
        stmt = (
            select(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.activity),
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.rotation_template
                ),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.secondary_rotation_template
                ),
            )
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .where(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                HalfDayAssignment.source.in_(sources),
            )
        )
        if person_ids:
            stmt = stmt.where(HalfDayAssignment.person_id.in_(person_ids))
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def _load_unlocked_slots(
        self, start_date: date, end_date: date
    ) -> list[HalfDayAssignment]:
        """Load half-day slots that can be assigned activities.

        Includes resident outpatient slots and faculty slots that are not locked.
        Faculty slots are assigned AT/C/admin by this solver; resident slots are
        assigned based on rotation activity requirements.
        """
        slots = self._load_slots(
            start_date,
            end_date,
            [AssignmentSource.SOLVER.value, AssignmentSource.TEMPLATE.value],
        )
        # Only outpatient rotations are eligible for activity solving
        eligible: list[HalfDayAssignment] = []
        for slot in slots:
            if slot.person and slot.person.type == "faculty":
                if getattr(slot.person, "faculty_role", None) == "adjunct":
                    continue
                eligible.append(slot)
                continue
            template = self._get_active_rotation_template(slot, start_date)
            if not template:
                continue
            if (template.rotation_type or "").lower() not in OUTPATIENT_ACTIVITY_TYPES:
                continue
            eligible.append(slot)
        return eligible

    def _load_candidate_slots(
        self, start_date: date, end_date: date
    ) -> list[HalfDayAssignment]:
        """Load all solver/template slots without rotation filtering.

        This method loads slots without checking rotation templates, allowing
        the assignment rotation map to be built before filtering. Only adjunct
        faculty are filtered out (they don't need template checks).
        """
        slots = self._load_slots(
            start_date,
            end_date,
            [AssignmentSource.SOLVER.value, AssignmentSource.TEMPLATE.value],
        )
        # Only filter adjunct faculty (no template check needed for this)
        return [
            slot
            for slot in slots
            if not (
                slot.person
                and slot.person.type == "faculty"
                and getattr(slot.person, "faculty_role", None) == "adjunct"
            )
        ]

    def _filter_outpatient_slots(
        self, slots: list[HalfDayAssignment], start_date: date
    ) -> list[HalfDayAssignment]:
        """Filter slots to only outpatient rotations.

        IMPORTANT: Requires _assignment_rotation_map to be populated first,
        as _get_active_rotation_template uses it as a fallback when
        block_assignment is not set.
        """
        eligible: list[HalfDayAssignment] = []
        for slot in slots:
            if slot.person and slot.person.type == "faculty":
                eligible.append(slot)
                continue
            template = self._get_active_rotation_template(slot, start_date)
            if not template:
                continue
            if (template.rotation_type or "").lower() not in OUTPATIENT_ACTIVITY_TYPES:
                continue
            eligible.append(slot)
        return eligible

    def _load_locked_slots(
        self,
        start_date: date,
        end_date: date,
        person_ids: set[UUID],
    ) -> list[HalfDayAssignment]:
        """Load locked (preload/manual) slots for baseline counts."""
        return self._load_slots(
            start_date,
            end_date,
            [AssignmentSource.PRELOAD.value, AssignmentSource.MANUAL.value],
            person_ids=person_ids,
        )

    def _load_assignment_rotation_map(
        self,
        start_date: date,
        end_date: date,
        person_ids: set[UUID],
    ) -> dict[tuple[UUID, date, str], RotationTemplate]:
        """Map (person_id, date, time_of_day) -> RotationTemplate from Assignment table."""
        if not person_ids:
            return {}

        stmt = (
            select(Assignment, Block, RotationTemplate)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .where(
                Assignment.person_id.in_(person_ids),
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        result = self.session.execute(stmt).all()
        mapping: dict[tuple[UUID, date, str], RotationTemplate] = {}
        for assignment, block, template in result:
            mapping[(assignment.person_id, block.date, block.time_of_day)] = template
        return mapping

    def _load_activity_requirements(
        self, template_ids: set[UUID]
    ) -> dict[UUID, list[RotationActivityRequirement]]:
        """Load rotation activity requirements for specific templates."""
        if not template_ids:
            return {}

        stmt = (
            select(RotationActivityRequirement)
            .where(RotationActivityRequirement.rotation_template_id.in_(template_ids))
            .options(
                selectinload(RotationActivityRequirement.activity),
                selectinload(RotationActivityRequirement.rotation_template),
            )
        )
        result = self.session.execute(stmt)
        requirements = list(result.scalars().all())

        by_template: dict[UUID, list[RotationActivityRequirement]] = defaultdict(list)
        for req in requirements:
            by_template[req.rotation_template_id].append(req)
        return by_template


def solve_activities(
    session: Session,
    block_number: int,
    academic_year: int,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    """
    Convenience function to run activity solver.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year
        timeout_seconds: Solver timeout

    Returns:
        Solver result dictionary
    """
    solver = CPSATActivitySolver(session, timeout_seconds=timeout_seconds)
    return solver.solve(block_number, academic_year)
