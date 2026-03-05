"""
Learner Schedule Generator.

Generates weekly schedules for med students and rotating interns using
the overlay model: learners shadow attendings/residents in existing
clinic assignments rather than owning their own slots.

Algorithm:
    1. Load active learner-to-track assignments for the target block
    2. For each learner, build a weekly template based on track + learner type
    3. Stagger FMIT weeks across tracks (tracks 1-7 get different weeks)
    4. Match learners to available supervisor assignments
    5. Validate against constraints (supervision, ASM, FMIT blocking, double-booking)
    6. Persist LearnerAssignment records

Weekly Template (per learner type):
    MS (Med Student):
        - Mon-Fri AM/PM: clinic (shadowing supervisor)
        - Wed AM: ASM (all learners, mandatory)
        - FMIT week: all slots → FMIT activity (per track's default_fmit_week)
    TY (Transitional Year):
        - Same as MS but requires_fmit=False by default
    PSYCH (Psychiatry):
        - Same as MS but requires_fmit=False by default
"""

import logging
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.learner import LearnerAssignment, LearnerToTrack, LearnerTrack
from app.models.person import Person

logger = logging.getLogger(__name__)

# Default weekly template: (day_of_week, time_of_day, activity_type)
# day_of_week: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
# time_of_day: AM, PM
WEEKLY_TEMPLATE = [
    (0, "AM", "clinic"),
    (0, "PM", "clinic"),
    (1, "AM", "clinic"),
    (1, "PM", "clinic"),
    (2, "AM", "ASM"),  # Wednesday AM = ASM for all learners
    (2, "PM", "clinic"),
    (3, "AM", "clinic"),
    (3, "PM", "clinic"),
    (4, "AM", "clinic"),
    (4, "PM", "didactics"),  # Friday PM = didactics
]

# FMIT week template: all slots become FMIT
FMIT_WEEK_TEMPLATE = [(day, time, "FMIT") for day in range(5) for time in ("AM", "PM")]


def get_active_learner_tracks(
    db: Session,
    block: Block,
) -> list[LearnerToTrack]:
    """Get learner-to-track assignments active during the given block."""
    return (
        db.query(LearnerToTrack)
        .filter(
            LearnerToTrack.start_date <= block.end_date,
            LearnerToTrack.end_date >= block.start_date,
        )
        .all()
    )


def get_block_week_number(block: Block) -> int:
    """
    Determine which week (1-4) within a 4-week block we're generating for.

    Blocks run 4 weeks. Returns 1-4 based on the block's position.
    For a single-block generation, defaults to week 1.
    """
    if not block.start_date:
        return 1
    # Block number within the academic period determines FMIT rotation
    if hasattr(block, "block_number") and block.block_number:
        return ((block.block_number - 1) % 4) + 1
    return 1


def find_available_supervisors(
    db: Session,
    block_id: UUID,
    day_of_week: int,
    time_of_day: str,
    exclude_person_ids: set[UUID] | None = None,
) -> list[Assignment]:
    """
    Find existing clinic assignments that can host a learner.

    Returns assignments where the assigned person can supervise learners
    (faculty or PGY-2+) and hasn't hit the 2-learner cap.
    """
    exclude = exclude_person_ids or set()

    # Get existing clinic assignments for this block/day/time
    assignments = (
        db.query(Assignment)
        .join(Person, Assignment.person_id == Person.id)
        .filter(
            Assignment.block_id == block_id,
        )
        .all()
    )

    eligible = []
    for a in assignments:
        if a.person_id in exclude:
            continue
        person = db.query(Person).filter(Person.id == a.person_id).first()
        if not person or not person.can_supervise_learners:
            continue

        # Check current learner count for this assignment
        learner_count = (
            db.query(LearnerAssignment)
            .filter(
                LearnerAssignment.parent_assignment_id == a.id,
                LearnerAssignment.day_of_week == day_of_week,
                LearnerAssignment.time_of_day == time_of_day,
            )
            .count()
        )
        if learner_count < 2:
            eligible.append(a)

    return eligible


def generate_learner_schedule(
    db: Session,
    block_id: UUID,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Generate learner schedule for a block.

    Args:
        db: Database session
        block_id: Target block UUID
        dry_run: If True, return plan without persisting

    Returns:
        Dict with generated assignments, warnings, and statistics
    """
    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        return {"error": "Block not found", "assignments": []}

    # Get active learner-track assignments
    active_tracks = get_active_learner_tracks(db, block)
    if not active_tracks:
        return {
            "assignments": [],
            "message": "No active learner-track assignments for this block",
        }

    # Load track info for FMIT week mapping
    tracks_by_id = {t.id: t for t in db.query(LearnerTrack).all()}

    block_week = get_block_week_number(block)
    assignments_created = []
    warnings = []
    stats = defaultdict(int)

    for ltt in active_tracks:
        learner = db.query(Person).filter(Person.id == ltt.learner_id).first()
        if not learner or not learner.is_learner:
            warnings.append(f"Skipping invalid learner {ltt.learner_id}")
            continue

        track = tracks_by_id.get(ltt.track_id)
        if not track:
            warnings.append(
                f"Track {ltt.track_id} not found for learner {learner.name}"
            )
            continue

        # Determine if this is a FMIT week for this learner's track
        is_fmit_week = ltt.requires_fmit and track.default_fmit_week == block_week

        template = FMIT_WEEK_TEMPLATE if is_fmit_week else WEEKLY_TEMPLATE

        for day, time, activity_type in template:
            # For clinic slots, try to find a supervisor
            parent_assignment_id = None
            if activity_type == "clinic":
                supervisors = find_available_supervisors(db, block_id, day, time)
                if supervisors:
                    parent_assignment_id = supervisors[0].id
                else:
                    warnings.append(
                        f"No supervisor available for {learner.name} "
                        f"day={day} time={time}"
                    )
                    stats["unmatched_slots"] += 1

            # Check for existing assignment in this slot
            existing = (
                db.query(LearnerAssignment)
                .filter(
                    LearnerAssignment.learner_id == learner.id,
                    LearnerAssignment.block_id == block_id,
                    LearnerAssignment.day_of_week == day,
                    LearnerAssignment.time_of_day == time,
                )
                .first()
            )
            if existing:
                stats["skipped_existing"] += 1
                continue

            assignment = LearnerAssignment(
                learner_id=learner.id,
                block_id=block_id,
                parent_assignment_id=parent_assignment_id,
                activity_type=activity_type,
                day_of_week=day,
                time_of_day=time,
                source="generator",
            )

            if not dry_run:
                db.add(assignment)

            assignments_created.append(
                {
                    "learner_id": str(learner.id),
                    "learner_name": learner.name,
                    "block_id": str(block_id),
                    "day_of_week": day,
                    "time_of_day": time,
                    "activity_type": activity_type,
                    "parent_assignment_id": str(parent_assignment_id)
                    if parent_assignment_id
                    else None,
                    "is_fmit_week": is_fmit_week,
                }
            )
            stats["created"] += 1

        stats["learners_processed"] += 1

    if not dry_run and assignments_created:
        db.commit()
        logger.info(
            f"Generated {stats['created']} learner assignments for block {block_id} "
            f"({stats['learners_processed']} learners)"
        )

    return {
        "assignments": assignments_created,
        "warnings": warnings,
        "stats": dict(stats),
        "dry_run": dry_run,
    }
