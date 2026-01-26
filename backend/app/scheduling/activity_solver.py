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

import time
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.activity import Activity, ActivityCategory
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_dates
from app.utils.activity_locking import is_activity_preloaded
from app.utils.activity_naming import activity_code_from_name, activity_display_abbrev

logger = get_logger(__name__)

# Default weekly activity requirements (per week) when none are configured
DEFAULT_WEEKLY_C_MIN = 2
DEFAULT_WEEKLY_C_MAX = 4
DEFAULT_WEEKLY_SPECIALTY_MIN = 3
DEFAULT_WEEKLY_SPECIALTY_MAX = 4

# Day index cutoff for secondary rotations (day 15+ uses secondary)
BLOCK_HALF_DAY = 14

# Rotation types considered outpatient for activity solving
OUTPATIENT_ACTIVITY_TYPES = {"clinic", "outpatient"}

# Clinic/supervision codes for activity-level constraints (legacy fallback)
RESIDENT_CLINIC_CODES = {"FM_CLINIC", "C", "C-N", "CV"}
AT_COVERAGE_CODES = {"AT", "PCAT"}
ADMIN_ACTIVITY_CODES = {"GME": "gme", "DFM": "dfm", "SM": "sm_clinic"}
FACULTY_CLINIC_SHORTFALL_PENALTY = 10
FACULTY_ADMIN_BONUS = 1
PHYSICAL_CAPACITY_SOFT_PENALTY = 10
CAPACITY_ACTIVITY_CODES = {
    "C",
    "C-N",
    "C-I",
    "CV",
    "V1",
    "V2",
    "V3",
    "FM_CLINIC",
    "PROC",
    "PR",
    "PROCEDURE",
    "VAS",
    "SM",
    "SM_CLINIC",
    "ASM",
}
SM_CAPACITY_CODES = {"SM", "SM_CLINIC", "ASM"}


class CPSATActivitySolver:
    """
    CP-SAT solver for assigning activities to half-day slots.

    This solver operates on HalfDayAssignment records created by the
    CP-SAT pipeline (source='solver') and fills activity_id.

    The solver respects:
    - Locked slots (source=preload or manual) - never touched
    - rotation_activity_requirements - determines which activities to assign
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

        # Ensure default requirements + rotation activities for outpatient templates
        requirements_by_template = self._ensure_default_requirements(
            templates_by_id, requirements_by_template
        )

        # Load activities after any default creation
        all_activities = self._load_activities()
        if not all_activities:
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
        if not assignable_ids:
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
        at_activity = self._get_activity_by_code("at") or self._get_activity_by_code(
            "AT"
        )

        # Activity ID sets for supervision and clinic demand (data-driven)
        supervision_required_ids = {
            activity.id
            for activity in all_activities
            if activity.requires_supervision
            and activity.activity_category == "clinical"
        }
        supervision_provider_ids = {
            activity.id for activity in all_activities if activity.provides_supervision
        }

        # Legacy fallback for older data (no flags configured)
        used_required_fallback = False
        used_provider_fallback = False
        if not supervision_required_ids:
            supervision_required_ids = self._activity_ids_for_codes(
                all_activities, RESIDENT_CLINIC_CODES
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
                "message": "Missing supervision-providing activities (AT/PCAT/DO)",
            }
        capacity_activity_ids = self._activity_ids_for_codes(
            all_activities, CAPACITY_ACTIVITY_CODES
        )
        sm_capacity_ids = self._activity_ids_for_codes(
            all_activities, SM_CAPACITY_CODES
        )

        # Create the CP model
        model = cp_model.CpModel()

        # Build allowed activity sets per template
        allowed_by_template: dict[UUID, list[UUID]] = {}
        for template_id, reqs in requirements_by_template.items():
            allowed_ids = []
            for req in reqs:
                if req.activity_id in assignable_ids and not is_activity_preloaded(
                    req.activity
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
                if not allowed:
                    allowed = list(faculty_allowed_ids)
            else:
                allowed = allowed_by_template.get(template_id) if template_id else None
                if not allowed:
                    if template_id:
                        logger.warning(
                            f"No activity requirements for template {template_id}, "
                            "falling back to all assignable activities"
                        )
                    allowed = fallback_allowed
            slot_allowed[s_i] = allowed

            for act_id in allowed:
                act_code = (
                    activity_by_id.get(act_id).code
                    if act_id in activity_by_id
                    else "act"
                )
                safe_code = act_code.replace("-", "_")
                a[s_i, act_id] = model.NewBoolVar(f"a_{s_i}_{safe_code}")

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
        baseline_sm_resident_presence: dict[tuple[date, str], int] = defaultdict(int)
        baseline_sm_faculty_coverage: dict[tuple[date, str], int] = defaultdict(int)
        person_ids = {meta["person_id"] for meta in slot_meta.values()}
        locked_slots = self._load_locked_slots(start_date, end_date, person_ids)
        sm_clinic_activity = self._get_activity_by_code(
            "sm_clinic"
        ) or self._get_activity_by_code("SM")
        for locked in locked_slots:
            if not locked.activity_id:
                continue
            week_number = self._get_week_number(locked.date, start_date)
            person_type = locked.person.type if locked.person else None
            slot_key = (locked.date, locked.time_of_day)

            if person_type == "faculty":
                if locked.activity_id in supervision_provider_ids:
                    baseline_faculty_coverage[slot_key] += 1
                if clinic_activity and locked.activity_id == clinic_activity.id:
                    locked_faculty_clinic_counts[(locked.person_id, week_number)] += 1
                if (
                    sm_clinic_activity
                    and locked.activity_id == sm_clinic_activity.id
                    and locked.person
                    and self._is_sports_medicine_faculty(locked.person)
                ):
                    baseline_sm_faculty_coverage[slot_key] += 1
            else:
                if locked.activity_id in supervision_required_ids:
                    pgy_level = (
                        locked.person.pgy_level
                        if locked.person and locked.person.pgy_level
                        else 2
                    )
                    demand_units = 2 if pgy_level == 1 else 1
                    baseline_resident_demand[slot_key] += demand_units

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
                model.Add(sum(entry["vars"]) >= entry["min"])
                model.Add(sum(entry["vars"]) <= entry["max"])
                constraint_count += 1

        if constraint_count:
            logger.info(f"Added {constraint_count} activity requirement constraints")

        # ==================================================
        # FACULTY CLINIC CAPS (min/max per week)
        # ==================================================
        faculty_clinic_shortfalls: list[Any] = []
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

                if max_allowed <= 0:
                    model.Add(sum(clinic_vars) == 0)
                else:
                    if max_allowed < len(clinic_vars):
                        model.Add(sum(clinic_vars) <= max_allowed)

                if min_needed > 0:
                    shortfall = model.NewIntVar(
                        0,
                        min_needed,
                        f"fac_clinic_shortfall_{str(faculty_id)[:8]}_{week}",
                    )
                    model.Add(sum(clinic_vars) + shortfall >= min_needed)
                    faculty_clinic_shortfalls.append(shortfall)

        # ==================================================
        # ACGME AT COVERAGE (faculty supervision)
        # ==================================================
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
                model.Add(total_coverage * 4 >= total_demand)

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

        if sm_template_ids and sm_clinic_activity:
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
                    model.Add(sum(faculty_vars) + baseline_faculty >= 1)
                    continue

                resident_vars = sm_resident_vars_by_slot.get(slot_key, [])
                if not resident_vars:
                    continue

                any_resident = model.NewBoolVar(
                    f"any_sm_res_{slot_date.strftime('%Y%m%d')}_{time_of_day}"
                )
                model.AddMaxEquality(any_resident, resident_vars)
                model.Add(sum(faculty_vars) + baseline_faculty >= any_resident)

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

        def _capacity_ids_for_person(person_type: str | None) -> set[UUID]:
            if person_type == "faculty":
                return capacity_activity_ids
            return capacity_activity_ids - sm_capacity_ids

        def _counts_toward_capacity(
            activity_id: UUID | None, person_type: str | None
        ) -> bool:
            if not activity_id:
                return False
            if activity_id not in capacity_activity_ids:
                return False
            if activity_id in sm_capacity_ids and person_type != "faculty":
                return False
            return True

        # Baseline occupancy from locked/preloaded slots not in solver
        slot_ids = {slot.id for slot in slots}
        baseline_capacity: dict[tuple[date, str], int] = defaultdict(int)
        baseline_stmt = (
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.person))
            .where(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
        )
        for assignment in self.session.execute(baseline_stmt).scalars():
            if assignment.id in slot_ids:
                continue  # handled by solver
            person_type = assignment.person.type if assignment.person else None
            if _counts_toward_capacity(assignment.activity_id, person_type):
                baseline_capacity[(assignment.date, assignment.time_of_day)] += 1

        # For each time slot, sum(clinical activities) + baseline <= HARD
        clinical_activity_ids = capacity_activity_ids.intersection(assignable_ids)
        overage_vars: list[Any] = []
        if clinical_activity_ids:
            enforced_groups = 0
            overhard_groups = 0
            overhard_examples: list[str] = []
            for (slot_date, time_of_day), slot_indices in slot_groups.items():
                # Skip weekends
                if slot_date.weekday() >= 5:
                    continue

                # Sum of clinical assignments for this slot
                slot_clinic_sum = sum(
                    a[s_i, act_id]
                    for s_i in slot_indices
                    for act_id in slot_allowed[s_i]
                    if _counts_toward_capacity(
                        act_id, slot_meta[s_i].get("person_type")
                    )
                )

                baseline = baseline_capacity.get((slot_date, time_of_day), 0)
                forced_capacity = sum(
                    1
                    for s_i in slot_indices
                    if set(slot_allowed[s_i]).issubset(
                        _capacity_ids_for_person(slot_meta[s_i].get("person_type"))
                    )
                )
                min_required = forced_capacity + baseline
                if min_required > HARD_PHYSICAL_CAPACITY:
                    overhard_groups += 1
                    if len(overhard_examples) < 5:
                        overhard_examples.append(
                            f"{slot_date} {time_of_day} min={min_required}"
                        )
                    continue

                total_clinic = slot_clinic_sum + baseline

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
                return {
                    "success": False,
                    "assignments_updated": 0,
                    "status": "error",
                    "message": (
                        "Physical capacity infeasible (min clinic demand exceeds hard "
                        f"{HARD_PHYSICAL_CAPACITY})"
                    ),
                }

            if enforced_groups:
                logger.info(
                    f"Added physical capacity constraints (soft {SOFT_PHYSICAL_CAPACITY}, "
                    f"hard {HARD_PHYSICAL_CAPACITY}) for {enforced_groups} of "
                    f"{len(slot_groups)} time slots"
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

        if overage_vars:
            overage_penalty = sum(overage_vars) * PHYSICAL_CAPACITY_SOFT_PENALTY
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
                    slot.activity_id = act_id
                    slot.source = AssignmentSource.SOLVER.value
                    updated += 1
                    break

        self.session.flush()
        logger.info(f"Activity solver updated {updated} slots")

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

    def _get_faculty_clinic_caps(self, faculty: Person) -> tuple[int, int]:
        """Return (min, max) weekly clinic half-days for a faculty member."""
        min_c = getattr(faculty, "min_clinic_halfdays_per_week", 0) or 0
        max_c = getattr(faculty, "max_clinic_halfdays_per_week", 4) or 0
        if max_c < min_c:
            max_c = min_c
        return min_c, max_c

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

    def _ensure_activity(
        self,
        name: str,
        code: str,
        display_abbreviation: str,
        activity_category: str,
        counts_toward_physical_capacity: bool,
        font_color: str | None = None,
        background_color: str | None = None,
    ) -> Activity:
        """Find or create an activity by name/code."""
        stmt = select(Activity).where(Activity.name == name)
        activity = self.session.execute(stmt).scalars().first()
        if activity:
            return activity

        stmt = select(Activity).where(Activity.code.ilike(code))
        activity = self.session.execute(stmt).scalars().first()
        if activity:
            return activity

        activity = Activity(
            name=name,
            code=code,
            display_abbreviation=display_abbreviation,
            activity_category=activity_category,
            font_color=font_color,
            background_color=background_color,
            requires_supervision=True,
            is_protected=False,
            counts_toward_clinical_hours=True,
            provides_supervision=False,
            counts_toward_physical_capacity=counts_toward_physical_capacity,
            display_order=0,
        )
        self.session.add(activity)
        self.session.flush()

        # Update cache for lookups
        self._activity_cache[activity.code] = activity
        if activity.display_abbreviation:
            self._activity_cache[activity.display_abbreviation] = activity

        logger.info(f"Created activity '{activity.name}' (code={activity.code})")
        return activity

    def _ensure_rotation_activity(self, template: RotationTemplate) -> Activity:
        """Ensure a specialty activity exists for this rotation template."""
        code = activity_code_from_name(template.name)
        display_abbrev = activity_display_abbrev(
            template.name,
            template.display_abbreviation,
            template.abbreviation,
        )
        return self._ensure_activity(
            name=template.name,
            code=code,
            display_abbreviation=display_abbrev,
            activity_category=ActivityCategory.CLINICAL.value,
            counts_toward_physical_capacity=True,
            font_color=template.font_color,
            background_color=template.background_color,
        )

    def _ensure_default_requirements(
        self,
        templates_by_id: dict[UUID, RotationTemplate],
        requirements_by_template: dict[UUID, list[RotationActivityRequirement]],
    ) -> dict[UUID, list[RotationActivityRequirement]]:
        """Create default weekly activity requirements for outpatient templates."""
        created = 0

        for template_id, template in templates_by_id.items():
            existing = requirements_by_template.get(template_id, [])
            if existing:
                continue
            if (template.rotation_type or "").lower() not in OUTPATIENT_ACTIVITY_TYPES:
                continue

            clinic_activity = self._ensure_activity(
                name="FM Clinic",
                code="fm_clinic",
                display_abbreviation="C",
                activity_category=ActivityCategory.CLINICAL.value,
                counts_toward_physical_capacity=True,
            )
            specialty_activity = self._ensure_rotation_activity(template)

            reqs: list[RotationActivityRequirement] = []
            for week in (1, 2, 3, 4):
                reqs.append(
                    RotationActivityRequirement(
                        rotation_template_id=template.id,
                        activity_id=clinic_activity.id,
                        min_halfdays=DEFAULT_WEEKLY_C_MIN,
                        max_halfdays=DEFAULT_WEEKLY_C_MAX,
                        applicable_weeks=[week],
                        prefer_full_days=True,
                        priority=80,
                    )
                )
                reqs.append(
                    RotationActivityRequirement(
                        rotation_template_id=template.id,
                        activity_id=specialty_activity.id,
                        min_halfdays=DEFAULT_WEEKLY_SPECIALTY_MIN,
                        max_halfdays=DEFAULT_WEEKLY_SPECIALTY_MAX,
                        applicable_weeks=[week],
                        prefer_full_days=True,
                        priority=80,
                    )
                )

            self.session.add_all(reqs)
            self.session.flush()
            requirements_by_template[template_id] = reqs
            created += len(reqs)

            logger.info(
                f"Created default activity requirements for template {template.name}"
            )

        if created:
            logger.info(f"Created {created} default activity requirements")

        return requirements_by_template

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
