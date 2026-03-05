"""
Learner Management API Routes — med students and rotating interns.

Endpoints:
    GET  /api/v1/learners                  - List all learners
    POST /api/v1/learners                  - Create a learner
    GET  /api/v1/learners/{id}             - Get learner details
    DELETE /api/v1/learners/{id}           - Remove a learner

    GET  /api/v1/learners/tracks           - List all tracks (1-7)
    POST /api/v1/learners/tracks/seed      - Seed default 7 tracks

    POST /api/v1/learners/track-assignments - Assign learner to track
    GET  /api/v1/learners/track-assignments - List track assignments

    GET  /api/v1/learners/assignments      - List learner schedule assignments
    POST /api/v1/learners/assignments      - Create learner assignment
    POST /api/v1/learners/generate/{block_id} - Generate learner schedule for block
"""

import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.learner import LearnerAssignment, LearnerToTrack, LearnerTrack
from app.models.person import Person
from app.models.user import User
from app.schemas.learner import (
    LearnerAssignmentCreate,
    LearnerAssignmentResponse,
    LearnerCreate,
    LearnerResponse,
    LearnerToTrackCreate,
    LearnerToTrackResponse,
    LearnerTrackResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["learners"])


# ============================================================================
# Learner CRUD
# ============================================================================


@router.get("", response_model=list[LearnerResponse])
async def list_learners(db: Session = Depends(get_db)):
    """List all learners (med students and rotating interns)."""
    learners = (
        db.query(Person)
        .filter(Person.type.in_(["med_student", "rotating_intern"]))
        .all()
    )
    return learners


@router.post("", response_model=LearnerResponse, status_code=status.HTTP_201_CREATED)
async def create_learner(
    body: LearnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """Create a new learner (med student or rotating intern)."""
    person = Person(
        id=uuid.uuid4(),
        name=body.name,
        email=body.email,
        type=body.type,
        learner_type=body.learner_type,
        med_school=body.med_school,
        ms_year=body.ms_year,
        requires_fmit=body.requires_fmit,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    logger.info(f"Created learner: {person.name} ({person.learner_type})")
    return person


@router.get("/{learner_id}", response_model=LearnerResponse)
async def get_learner(learner_id: UUID, db: Session = Depends(get_db)):
    """Get a learner by ID."""
    person = db.query(Person).filter(Person.id == learner_id).first()
    if not person or not person.is_learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    return person


@router.delete("/{learner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learner(
    learner_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """Remove a learner."""
    person = db.query(Person).filter(Person.id == learner_id).first()
    if not person or not person.is_learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    db.delete(person)
    db.commit()
    logger.info(f"Deleted learner: {person.name}")


# ============================================================================
# Learner Tracks
# ============================================================================


@router.get("/tracks", response_model=list[LearnerTrackResponse])
async def list_tracks(db: Session = Depends(get_db)):
    """List all learner tracks."""
    return db.query(LearnerTrack).order_by(LearnerTrack.track_number).all()


@router.post(
    "/tracks/seed",
    response_model=list[LearnerTrackResponse],
    status_code=status.HTTP_201_CREATED,
)
async def seed_tracks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """Seed the default 7 learner tracks with staggered FMIT weeks."""
    existing = db.query(LearnerTrack).count()
    if existing > 0:
        raise HTTPException(status_code=400, detail=f"{existing} tracks already exist")

    tracks = []
    fmit_weeks = [1, 2, 3, 4, 1, 2, 3]
    for i in range(7):
        track = LearnerTrack(
            track_number=i + 1,
            default_fmit_week=fmit_weeks[i],
            description=f"Track {i + 1} (FMIT week {fmit_weeks[i]})",
        )
        db.add(track)
        tracks.append(track)

    db.commit()
    for t in tracks:
        db.refresh(t)
    logger.info("Seeded 7 default learner tracks")
    return tracks


# ============================================================================
# Learner-to-Track Assignments
# ============================================================================


@router.get("/track-assignments", response_model=list[LearnerToTrackResponse])
async def list_track_assignments(db: Session = Depends(get_db)):
    """List all learner-to-track assignments."""
    return db.query(LearnerToTrack).all()


@router.post(
    "/track-assignments",
    response_model=LearnerToTrackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_track_assignment(
    body: LearnerToTrackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """Assign a learner to a track for a date range."""
    learner = db.query(Person).filter(Person.id == body.learner_id).first()
    if not learner or not learner.is_learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    track = db.query(LearnerTrack).filter(LearnerTrack.id == body.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    assignment = LearnerToTrack(
        learner_id=body.learner_id,
        track_id=body.track_id,
        start_date=body.start_date,
        end_date=body.end_date,
        requires_fmit=body.requires_fmit,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    logger.info(f"Assigned learner {learner.name} to track {track.track_number}")
    return assignment


# ============================================================================
# Learner Schedule Assignments
# ============================================================================


@router.get("/assignments", response_model=list[LearnerAssignmentResponse])
async def list_learner_assignments(
    block_id: UUID | None = Query(default=None),
    learner_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """List learner schedule assignments, optionally filtered."""
    q = db.query(LearnerAssignment)
    if block_id:
        q = q.filter(LearnerAssignment.block_id == block_id)
    if learner_id:
        q = q.filter(LearnerAssignment.learner_id == learner_id)
    return q.all()


@router.post(
    "/assignments",
    response_model=LearnerAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_learner_assignment(
    body: LearnerAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """Create a learner schedule assignment."""
    learner = db.query(Person).filter(Person.id == body.learner_id).first()
    if not learner or not learner.is_learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Validate supervision capacity if assigning to a parent assignment
    if body.parent_assignment_id:
        from app.models.assignment import Assignment

        parent = (
            db.query(Assignment)
            .filter(Assignment.id == body.parent_assignment_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent assignment not found")

        supervisor = db.query(Person).filter(Person.id == parent.person_id).first()
        if supervisor and not supervisor.can_supervise_learners:
            raise HTTPException(
                status_code=400,
                detail=f"{supervisor.name} cannot supervise learners (PGY-1)",
            )

        # Check max 2 learners per supervisor per block
        existing_count = (
            db.query(LearnerAssignment)
            .filter(
                LearnerAssignment.parent_assignment_id == body.parent_assignment_id,
            )
            .count()
        )
        if existing_count >= 2:
            raise HTTPException(
                status_code=400,
                detail="Supervisor already has 2 learners for this assignment (max)",
            )

    assignment = LearnerAssignment(
        learner_id=body.learner_id,
        block_id=body.block_id,
        parent_assignment_id=body.parent_assignment_id,
        activity_type=body.activity_type,
        day_of_week=body.day_of_week,
        time_of_day=body.time_of_day,
        source=body.source,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ============================================================================
# Schedule Generation
# ============================================================================


@router.post("/generate/{block_id}")
async def generate_learner_schedule_endpoint(
    block_id: UUID,
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Generate learner schedule for a block.

    Uses the overlay model to match learners with supervisor assignments.
    Set dry_run=false to persist the generated schedule.
    """
    from app.scheduling.learner_generator import generate_learner_schedule

    result = generate_learner_schedule(db, block_id, dry_run=dry_run)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
