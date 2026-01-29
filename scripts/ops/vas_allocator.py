#!/usr/bin/env python3
"""Post-solver allocator for VAS/VASC clinic pairing.

Targets a small number of VAS/VASC sessions per block by converting
eligible slots into VAS or VASC, while honoring:
- Do not override FMIT, absences (time-off), or PCAT/DO
- Slot pairing: resident + faculty in same slot
- Allowed slots: Thu AM/PM, Fri AM
- AT coverage and physical capacity must remain valid

Usage:
  python scripts/ops/vas_allocator.py --block 10 --academic-year 2026
  python scripts/ops/vas_allocator.py --block 10 --academic-year 2026 --dry-run --verbose
  python scripts/ops/vas_allocator.py --block 10 --academic-year 2026 --vas-total 3 --vasc-target 1 --vasc-max 2
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def _load_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    for path in (".env.codex", ".env"):
        if os.path.exists(path):
            load_dotenv(path, override=True)

    if not os.environ.get("DATABASE_URL"):
        pwd = os.environ.get("DB_PASSWORD")
        if pwd:
            os.environ["DATABASE_URL"] = (
                f"postgresql://scheduler:{pwd}@localhost:5432/residency_scheduler"
            )


_load_env()

from app.db.session import SessionLocal  # noqa: E402
from app.models.activity import Activity  # noqa: E402
from app.models.block_assignment import BlockAssignment  # noqa: E402
from app.models.half_day_assignment import HalfDayAssignment  # noqa: E402
from app.models.procedure_credential import ProcedureCredential  # noqa: E402
from app.utils.academic_blocks import get_block_dates  # noqa: E402
from app.utils.fmc_capacity import (  # noqa: E402
    activity_capacity_units,
    activity_counts_toward_fmc_capacity,
    activity_is_proc_or_vas,
    activity_is_sm_capacity,
    slot_fmc_capacity,
)
from app.utils.supervision import (  # noqa: E402
    activity_requires_fmc_supervision,
    assignment_requires_fmc_supervision,
)


ALLOWED_WEEKDAY_TIMES = {(3, "AM"), (3, "PM"), (4, "AM")}  # Thu AM/PM, Fri AM
FACULTY_COMPETENCY_PENALTY = {
    "master": 0,
    "expert": 0,
    "qualified": 10,
    "trainee": 20,
}
RESIDENT_PENALTY_PROC = 0
RESIDENT_PENALTY_FMC = 5
RESIDENT_PENALTY_POCUS = 10
RESIDENT_PENALTY_OTHER = 20


def _normalize(value: str | None) -> str:
    return (value or "").strip().upper()


def _activity_code(activity: Activity | None) -> str:
    if not activity:
        return ""
    code = _normalize(activity.code)
    if code:
        return code
    return _normalize(activity.display_abbreviation)


def _activity_display(activity: Activity | None) -> str:
    if not activity:
        return ""
    return _normalize(activity.display_abbreviation)


PROTECTED_ACTIVITY_CODES = {"FMIT", "PCAT", "DO"}


def _is_convertible_assignment(assignment: HalfDayAssignment) -> bool:
    activity = assignment.activity
    if not activity:
        return True
    code = _activity_code(activity)
    display = _activity_display(activity)
    if code in PROTECTED_ACTIVITY_CODES or display in PROTECTED_ACTIVITY_CODES:
        return False
    if getattr(activity, "is_time_off", False):
        return False
    return True


def _load_vas_credentials(
    session: SessionLocal,
    procedure_id: str,
) -> dict[str, ProcedureCredential]:
    rows = (
        session.query(ProcedureCredential)
        .filter(ProcedureCredential.procedure_id == procedure_id)
        .filter(ProcedureCredential.status == "active")
        .filter(
            or_(
                ProcedureCredential.expiration_date.is_(None),
                ProcedureCredential.expiration_date >= date.today(),
            )
        )
        .all()
    )
    return {str(row.person_id): row for row in rows}


def _faculty_penalty(credential: ProcedureCredential | None) -> int | None:
    if not credential:
        return None
    level = (credential.competency_level or "").lower()
    return FACULTY_COMPETENCY_PENALTY.get(level, 0)


def _resident_penalty(
    block_assignment: BlockAssignment | None,
    start_date: date,
    assignment_date: date,
) -> int:
    if not block_assignment:
        return RESIDENT_PENALTY_OTHER

    template = block_assignment.rotation_template
    if block_assignment.secondary_rotation_template:
        if (assignment_date - start_date).days >= 14:
            template = block_assignment.secondary_rotation_template

    abbrev = _normalize(getattr(template, "abbreviation", ""))
    name = _normalize(getattr(template, "name", ""))

    if "PROC" in abbrev or "PROC" in name:
        return RESIDENT_PENALTY_PROC
    if abbrev in {"FMC", "FM", "FMC-OP"} or "FM CLINIC" in name:
        return RESIDENT_PENALTY_FMC
    if "POCUS" in abbrev or "POCUS" in name or abbrev == "US" or "ULTRASOUND" in name:
        return RESIDENT_PENALTY_POCUS
    return RESIDENT_PENALTY_OTHER


def _compute_at_demand(
    assignments: Iterable[HalfDayAssignment],
    overrides: dict[str, Activity] | None = None,
) -> float:
    demand = 0.0
    for assignment in assignments:
        person = assignment.person
        if not person or person.type != "resident":
            continue
        override = overrides.get(str(assignment.id)) if overrides else None
        if override is not None:
            requires_supervision = activity_requires_fmc_supervision(override)
            activity = override
        else:
            requires_supervision = assignment_requires_fmc_supervision(assignment)
            activity = assignment.activity
        if not requires_supervision:
            continue
        pgy = person.pgy_level or 1
        if pgy == 1:
            demand += 0.5
        else:
            demand += 0.25
        if activity_is_proc_or_vas(activity):
            demand += 1.0
    return demand


def _compute_at_coverage(
    assignments: Iterable[HalfDayAssignment],
    overrides: dict[str, Activity] | None = None,
) -> float:
    coverage = 0.0
    for assignment in assignments:
        person = assignment.person
        if not person or person.type != "faculty":
            continue
        override = overrides.get(str(assignment.id)) if overrides else None
        activity = override or assignment.activity
        if activity and activity.is_supervision:
            coverage += 1.0
    return coverage


def _slot_capacity(assignments: Iterable[HalfDayAssignment], overrides: dict[str, Activity]) -> int:
    non_sm = 0
    sm_present = False
    for assignment in assignments:
        override = overrides.get(str(assignment.id))
        activity = override or assignment.activity
        if not activity:
            continue
        if activity_is_sm_capacity(activity):
            if activity_counts_toward_fmc_capacity(activity):
                sm_present = True
            continue
        if activity_counts_toward_fmc_capacity(activity):
            non_sm += activity_capacity_units(activity)
    return non_sm + (1 if sm_present else 0)


@dataclass
class CandidatePair:
    slot_key: tuple[date, str]
    resident: HalfDayAssignment
    faculty: HalfDayAssignment
    resident_penalty: int
    faculty_penalty: int
    total_penalty: int
    can_vasc: bool
    can_vas: bool


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-solver VAS/VASC allocator")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--academic-year", type=int, required=True)
    parser.add_argument("--vas-total", type=int, default=3)
    parser.add_argument("--vasc-target", type=int, default=1)
    parser.add_argument("--vasc-max", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.vas_total < 0 or args.vasc_target < 0 or args.vasc_max < 0:
        raise SystemExit("VAS targets must be non-negative")

    session = SessionLocal()
    try:
        block = get_block_dates(args.block, args.academic_year)
        start_date, end_date = block.start_date, block.end_date
        print(
            f"VAS allocator: Block {args.block} AY{args.academic_year} "
            f"{start_date} to {end_date}"
        )

        activities = {
            _activity_code(activity): activity
            for activity in session.query(Activity).filter(
                Activity.code.in_(["VAS", "VASC", "C", "FM_CLINIC"])  # type: ignore[arg-type]
            )
        }
        vas_activity = activities.get("VAS")
        vasc_activity = activities.get("VASC")
        if not vas_activity or not vasc_activity:
            missing = [
                name
                for name, value in {"VAS": vas_activity, "VASC": vasc_activity}.items()
                if value is None
            ]
            raise SystemExit(f"Missing activities: {', '.join(missing)}")
        if not vas_activity.procedure_id:
            raise SystemExit(
                "VAS activity missing procedure_id. Run the credentials migration first."
            )

        vas_credentials = _load_vas_credentials(
            session, str(vas_activity.procedure_id)
        )

        assignments = (
            session.query(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.rotation_template
                ),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.secondary_rotation_template
                ),
            )
            .filter(HalfDayAssignment.date >= start_date)
            .filter(HalfDayAssignment.date <= end_date)
            .all()
        )

        slot_assignments: dict[tuple[date, str], list[HalfDayAssignment]] = {}
        for assignment in assignments:
            key = (assignment.date, assignment.time_of_day)
            slot_assignments.setdefault(key, []).append(assignment)

        existing_vas_slots: set[tuple[date, str]] = set()
        existing_vasc_slots: set[tuple[date, str]] = set()
        for assignment in assignments:
            code = _activity_code(assignment.activity)
            if code == "VAS":
                existing_vas_slots.add((assignment.date, assignment.time_of_day))
            if code == "VASC":
                existing_vasc_slots.add((assignment.date, assignment.time_of_day))

        existing_total = len(existing_vas_slots | existing_vasc_slots)
        existing_vasc = len(existing_vasc_slots)
        if existing_total >= args.vas_total:
            print(
                f"VAS allocator: already have {existing_total} VAS/VASC slots "
                f"(target {args.vas_total}); no changes needed."
            )
            return 0

        remaining_total = max(0, args.vas_total - existing_total)
        remaining_vasc_target = max(0, args.vasc_target - existing_vasc)
        remaining_vasc_max = max(0, args.vasc_max - existing_vasc)

        candidates: list[CandidatePair] = []
        eligible_slots = 0
        rejected_existing = 0
        rejected_capacity = 0
        rejected_coverage = 0
        rejected_no_faculty = 0
        rejected_no_resident = 0
        slots_with_faculty_convertible = 0
        slots_with_allowed_faculty = 0
        slots_with_resident_convertible = 0
        total_candidate_pairs = 0

        for slot_key, slot_list in slot_assignments.items():
            slot_date, time_of_day = slot_key
            if (slot_date.weekday(), time_of_day.upper()) not in ALLOWED_WEEKDAY_TIMES:
                continue
            eligible_slots += 1
            if slot_key in existing_vas_slots or slot_key in existing_vasc_slots:
                rejected_existing += 1
                continue

            capacity_count = slot_fmc_capacity(slot_list)
            if capacity_count > 8:
                rejected_capacity += 1
                continue

            base_demand = _compute_at_demand(slot_list)
            base_coverage = _compute_at_coverage(slot_list)
            if base_coverage < math.ceil(base_demand):
                rejected_coverage += 1
                continue

            faculty_candidates: list[tuple[HalfDayAssignment, int]] = []
            resident_candidates: list[tuple[HalfDayAssignment, int]] = []
            has_faculty_convertible = False
            has_allowed_faculty = False
            has_resident_convertible = False
            for assignment in slot_list:
                if not assignment.person:
                    continue
                if assignment.person.type == "faculty" and _is_convertible_assignment(
                    assignment
                ):
                    has_faculty_convertible = True
                    credential = vas_credentials.get(str(assignment.person_id))
                    penalty = _faculty_penalty(credential)
                    if penalty is None:
                        continue
                    has_allowed_faculty = True
                    faculty_candidates.append((assignment, penalty))
                elif assignment.person.type == "resident" and _is_convertible_assignment(
                    assignment
                ):
                    has_resident_convertible = True
                    penalty = _resident_penalty(
                        assignment.block_assignment,
                        start_date,
                        assignment.date,
                    )
                    resident_candidates.append((assignment, penalty))

            if has_faculty_convertible:
                slots_with_faculty_convertible += 1
            if has_allowed_faculty:
                slots_with_allowed_faculty += 1
            if has_resident_convertible:
                slots_with_resident_convertible += 1

            if not faculty_candidates or not resident_candidates:
                if not faculty_candidates:
                    rejected_no_faculty += 1
                if not resident_candidates:
                    rejected_no_resident += 1
                continue

            for resident_assignment, resident_penalty in resident_candidates:
                for faculty_assignment, faculty_penalty in faculty_candidates:
                    overrides = {
                        str(resident_assignment.id): vasc_activity,
                        str(faculty_assignment.id): vasc_activity,
                    }
                    capacity_after = _slot_capacity(slot_list, overrides)
                    demand_after = _compute_at_demand(slot_list, overrides)
                    coverage_after = _compute_at_coverage(slot_list, overrides)
                    can_vasc = capacity_after <= 8 and coverage_after >= math.ceil(demand_after)

                    overrides[str(resident_assignment.id)] = vas_activity
                    overrides[str(faculty_assignment.id)] = vas_activity
                    capacity_after_vas = _slot_capacity(slot_list, overrides)
                    demand_after_vas = _compute_at_demand(slot_list, overrides)
                    coverage_after_vas = _compute_at_coverage(slot_list, overrides)
                    can_vas = (
                        capacity_after_vas <= 8
                        and coverage_after_vas >= math.ceil(demand_after_vas)
                    )
                    candidates.append(
                        CandidatePair(
                            slot_key=slot_key,
                            resident=resident_assignment,
                            faculty=faculty_assignment,
                            resident_penalty=resident_penalty,
                            faculty_penalty=faculty_penalty,
                            total_penalty=resident_penalty + faculty_penalty,
                            can_vasc=can_vasc,
                            can_vas=can_vas,
                        )
                    )
                    total_candidate_pairs += 1

        candidates.sort(key=lambda c: c.total_penalty)

        used_slots: set[tuple[date, str]] = set()
        selected_vasc: list[CandidatePair] = []
        selected_vas: list[CandidatePair] = []

        def apply_pair(pair: CandidatePair, activity: Activity) -> None:
            pair.resident.activity_id = activity.id
            pair.resident.activity = activity
            pair.faculty.activity_id = activity.id
            pair.faculty.activity = activity

        def pick_candidates(
            pool: list[CandidatePair],
            needed: int,
            allow_vas: bool,
            activity: Activity,
        ) -> list[CandidatePair]:
            selected: list[CandidatePair] = []
            for candidate in pool:
                if len(selected) >= needed:
                    break
                if candidate.slot_key in used_slots:
                    continue
                if allow_vas and not candidate.can_vas:
                    continue
                if not allow_vas and not candidate.can_vasc:
                    continue
                selected.append(candidate)
                used_slots.add(candidate.slot_key)
                apply_pair(candidate, activity)
            return selected

        # 1) Allocate VASC first to hit target
        if remaining_vasc_target > 0 and remaining_total > 0:
            vasc_goal = min(remaining_vasc_target, remaining_total, remaining_vasc_max)
            selected_vasc = pick_candidates(candidates, vasc_goal, False, vasc_activity)

        # 2) Allocate VAS to reach total
        remaining_total -= len(selected_vasc)
        if remaining_total > 0:
            selected_vas = pick_candidates(candidates, remaining_total, True, vas_activity)
            remaining_total -= len(selected_vas)

        # 3) If still short, try to top up with extra VASC (up to max)
        remaining_vasc_capacity = max(0, remaining_vasc_max - len(selected_vasc))
        if remaining_total > 0 and remaining_vasc_capacity > 0:
            extra = min(remaining_total, remaining_vasc_capacity)
            extra_vasc = pick_candidates(candidates, extra, False, vasc_activity)
            selected_vasc.extend(extra_vasc)
            remaining_total -= len(extra_vasc)

        if args.dry_run:
            session.rollback()
        else:
            session.commit()

        total_added = len(selected_vas) + len(selected_vasc)
        print(
            "VAS allocator summary: "
            f"existing={existing_total} (VASC={existing_vasc}), "
            f"added={total_added} (VAS={len(selected_vas)}, VASC={len(selected_vasc)}), "
            f"target={args.vas_total}"
        )
        if remaining_total > 0:
            print(f"Shortfall: {remaining_total} slots (insufficient eligible pairs)")
        if rejected_capacity or rejected_coverage:
            print(
                "Skipped slots: "
                f"over_capacity={rejected_capacity}, coverage_failed={rejected_coverage}"
            )
        if args.verbose:
            print(
                "Eligibility summary: "
                f"eligible_slots={eligible_slots}, "
                f"existing_vas_vasc={rejected_existing}, "
                f"no_faculty={rejected_no_faculty}, "
                f"no_resident={rejected_no_resident}, "
                f"candidate_pairs={total_candidate_pairs}"
            )
            print(
                "Convertible slots: "
                f"slots_with_faculty_convertible={slots_with_faculty_convertible}, "
                f"slots_with_allowed_faculty={slots_with_allowed_faculty}, "
                f"slots_with_resident_convertible={slots_with_resident_convertible}"
            )
        if total_candidate_pairs == 0 and slots_with_allowed_faculty == 0:
            print(
                "Warning: No eligible VAS/VASC faculty slots found in allowed windows "
                "with active vasectomy credentials."
            )

        if args.verbose:
            def _describe(pair: CandidatePair, label: str) -> None:
                resident = pair.resident.person.name if pair.resident.person else "?"
                faculty = pair.faculty.person.name if pair.faculty.person else "?"
                print(
                    f"{label}: {pair.slot_key[0]} {pair.slot_key[1]} "
                    f"resident={resident} faculty={faculty} penalty={pair.total_penalty}"
                )

            for pair in selected_vasc:
                _describe(pair, "VASC")
            for pair in selected_vas:
                _describe(pair, "VAS")

        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
