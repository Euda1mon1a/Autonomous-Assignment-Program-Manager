"""Minimal CP-SAT pipeline integration test."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.activity_solver import CPSATActivitySolver
from app.scheduling.engine import SchedulingEngine
from app.scheduling.constraints import (
    ConstraintManager,
    OvernightCallCoverageConstraint,
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
)
from app.utils.academic_blocks import get_block_number_for_date


def _seed_activity(db: Session, *, code: str, name: str, category: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=name,
        code=code,
        display_abbreviation=code.upper(),
        activity_category=category,
    )
    db.add(activity)
    return activity


@pytest.mark.integration
def test_cpsat_pipeline_minimal_dataset(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run CP-SAT generation on a tiny dataset and verify half-day + PCAT/DO."""
    # SQLite test DB doesn't include JSONB-backed tables (rotation_activity_requirements).
    monkeypatch.setattr(
        SchedulingEngine,
        "_load_activity_requirements",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        CPSATActivitySolver,
        "_load_activity_requirements",
        lambda *_args, **_kwargs: {},
    )

    def _create_call_assignments_from_result(self, solver_result, context):
        call_assignments: list[CallAssignment] = []
        block_by_id = {
            b.id: b
            for b in self.db.query(Block)
            .filter(Block.date >= self.start_date, Block.date <= self.end_date)
            .all()
        }
        for person_id, block_id, _call_type in solver_result.call_assignments:
            block = block_by_id.get(block_id)
            if not block:
                continue
            is_sunday = block.date.weekday() == 6
            # CHECK constraint: call_type IN ('overnight', 'weekend', 'backup')
            mapped_call_type = "weekend" if is_sunday else "overnight"
            call_assignment = CallAssignment(
                date=block.date,
                person_id=person_id,
                call_type=mapped_call_type,
                is_weekend=is_sunday,
                is_holiday=bool(getattr(block, "is_holiday", False)),
            )
            self.db.add(call_assignment)
            call_assignments.append(call_assignment)
        return call_assignments

    monkeypatch.setattr(
        SchedulingEngine,
        "_create_call_assignments_from_result",
        _create_call_assignments_from_result,
    )

    start_date = date(2026, 2, 2)  # Monday
    end_date = start_date + timedelta(days=1)
    block_number, academic_year = get_block_number_for_date(start_date)

    # Seed minimal activities required by preload + pipeline.
    _seed_activity(db, code="OFF", name="OFF", category="time_off")
    # NOTE: Activity codes for PCAT/DO are stored lowercase in the database.
    _seed_activity(db, code="pcat", name="PCAT", category="administrative")
    _seed_activity(db, code="do", name="DO", category="time_off")
    _seed_activity(db, code="AT", name="AT", category="administrative")
    _seed_activity(db, code="C", name="Clinic", category="clinical")
    _seed_activity(db, code="CALL", name="Call", category="clinical")
    _seed_activity(db, code="LV-AM", name="Leave AM", category="time_off")
    _seed_activity(db, code="LV-PM", name="Leave PM", category="time_off")
    _seed_activity(db, code="W", name="Weekend Off", category="time_off")
    _seed_activity(db, code="LEC", name="Lecture", category="educational")
    _seed_activity(db, code="ADV", name="Advising", category="educational")
    _seed_activity(db, code="CV", name="CV Review", category="administrative")
    _seed_activity(db, code="fm_clinic", name="FM Clinic", category="clinical")

    # Core scheduling data.
    resident_1 = Person(
        id=uuid4(),
        name="Resident One",
        type="resident",
        email="resident1@test.org",
        pgy_level=1,
    )
    resident_2 = Person(
        id=uuid4(),
        name="Resident Two",
        type="resident",
        email="resident2@test.org",
        pgy_level=2,
    )
    faculty = Person(
        id=uuid4(),
        name="Faculty One",
        type="faculty",
        email="faculty1@test.org",
        faculty_role="core",
    )
    faculty_2 = Person(
        id=uuid4(),
        name="Faculty Two",
        type="faculty",
        email="faculty2@test.org",
        faculty_role="core",
    )
    rotation = RotationTemplate(
        id=uuid4(),
        name="Outpatient Clinic",
        rotation_type="outpatient",
        abbreviation="OUT",
        supervision_required=True,
    )

    db.add_all([resident_1, resident_2, faculty, faculty_2, rotation])
    db.commit()

    # Block assignments for resident filtering (template optional).
    # Full-block rotation: two rows per resident (block_half=1 and block_half=2).
    for resident in (resident_1, resident_2):
        for bh in (1, 2):
            db.add(
                BlockAssignment(
                    id=uuid4(),
                    block_number=block_number,
                    academic_year=academic_year,
                    resident_id=resident.id,
                    block_half=bh,
                )
            )
    db.commit()

    constraint_manager = ConstraintManager.create_minimal()
    constraint_manager.add(OvernightCallCoverageConstraint())
    constraint_manager.add(AdjunctCallExclusionConstraint())
    constraint_manager.add(CallAvailabilityConstraint())

    engine = SchedulingEngine(
        db,
        start_date=start_date,
        end_date=end_date,
        constraint_manager=constraint_manager,
    )
    result = engine.generate(
        algorithm="cp_sat",
        block_number=block_number,
        academic_year=academic_year,
        rotation_template_ids=[rotation.id],
        timeout_seconds=5.0,
        check_resilience=False,
        validate_pcat_do=True,
    )

    assert result["status"] in {"success", "partial"}

    # Solver-created half-day assignments for residents + faculty.
    resident_solver_count = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id.in_([resident_1.id, resident_2.id]),
            HalfDayAssignment.source == AssignmentSource.SOLVER.value,
        )
        .count()
    )
    faculty_solver_count = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == faculty.id,
            HalfDayAssignment.source == AssignmentSource.SOLVER.value,
        )
        .count()
    )
    assert resident_solver_count > 0, "Expected resident solver half-day assignments"
    assert faculty_solver_count > 0, "Expected faculty solver half-day assignments"

    # Call → PCAT/DO sync should create next-day preloads.
    call_assignment = (
        db.query(CallAssignment)
        .filter(CallAssignment.date < end_date)
        .order_by(CallAssignment.date.asc())
        .first()
    )
    assert call_assignment is not None, "Expected overnight call assignments"

    next_day = call_assignment.date + timedelta(days=1)
    pcat_activity = db.query(Activity).filter(Activity.code == "pcat").first()
    do_activity = db.query(Activity).filter(Activity.code == "do").first()
    assert pcat_activity is not None
    assert do_activity is not None

    pcat_slot = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == call_assignment.person_id,
            HalfDayAssignment.date == next_day,
            HalfDayAssignment.time_of_day == "AM",
            HalfDayAssignment.activity_id == pcat_activity.id,
        )
        .first()
    )
    do_slot = (
        db.query(HalfDayAssignment)
        .filter(
            HalfDayAssignment.person_id == call_assignment.person_id,
            HalfDayAssignment.date == next_day,
            HalfDayAssignment.time_of_day == "PM",
            HalfDayAssignment.activity_id == do_activity.id,
        )
        .first()
    )

    assert pcat_slot is not None, "Expected PCAT preload after call"
    assert do_slot is not None, "Expected DO preload after call"
    assert pcat_slot.source == AssignmentSource.PRELOAD.value
    assert do_slot.source == AssignmentSource.PRELOAD.value
