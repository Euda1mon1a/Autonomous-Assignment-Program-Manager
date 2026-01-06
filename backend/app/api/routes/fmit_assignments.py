"""FMIT Assignment CRUD API routes for 52-week planner.

Provides write endpoints for FMIT scheduling:
- POST /fmit/assignments - Create week assignment
- PUT /fmit/assignments/{week_date} - Update assignment (reassign)
- DELETE /fmit/assignments/{faculty_id}/{week_date} - Remove assignment
- POST /fmit/assignments/bulk - Bulk create assignments
- GET /fmit/assignments/year-grid/{year} - Full year view with all faculty
- GET /fmit/assignments/check-conflicts - Pre-assignment conflict check

All endpoints require authentication and use async SQLAlchemy patterns.
"""

import statistics
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.fmit_assignments import (
    AssignmentStatus,
    ConflictCheckResponse,
    ConflictDetail,
    ConflictType,
    FacultyYearSummary,
    FMITAssignmentCreate,
    FMITAssignmentDeleteResponse,
    FMITAssignmentResponse,
    FMITAssignmentUpdate,
    FMITBulkAssignmentRequest,
    FMITBulkAssignmentResponse,
    FMITBulkAssignmentResult,
    WeekSlot,
    YearGridResponse,
)
from app.scheduling.constraints.fmit import get_fmit_week_dates

router = APIRouter()
logger = get_logger(__name__)

# Constants
FMIT_ROTATION_NAME = "FMIT"
BLOCKS_PER_WEEK = 14  # 7 days x 2 blocks (AM/PM)


# =============================================================================
# Helper Functions
# =============================================================================


async def get_fmit_template(db: Session) -> RotationTemplate | None:
    """Get the FMIT rotation template."""
    result = db.execute(
        select(RotationTemplate).where(RotationTemplate.name == FMIT_ROTATION_NAME)
    )
    return result.scalar_one_or_none()


def get_week_start(any_date: date) -> date:
    """Get the Friday of the FMIT week containing the given date."""
    friday, _ = get_fmit_week_dates(any_date)
    return friday


async def get_or_create_blocks(
    db: Session, start_date: date, end_date: date
) -> list[Block]:
    """Get or create all blocks for a date range."""
    blocks = []
    current_date = start_date

    while current_date <= end_date:
        for time_of_day in ["AM", "PM"]:
            # Try to get existing block
            result = db.execute(
                select(Block).where(
                    and_(Block.date == current_date, Block.time_of_day == time_of_day)
                )
            )
            block = result.scalar_one_or_none()

            # Create if doesn't exist
            if not block:
                block = Block(
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=current_date.weekday() >= 5,
                    is_holiday=False,
                )
                db.add(block)
                db.flush()

            blocks.append(block)

        current_date += timedelta(days=1)

    return blocks


async def check_faculty_conflicts(
    db: Session,
    faculty_id: UUID,
    week_start: date,
    week_end: date,
    fmit_template_id: UUID,
) -> list[ConflictDetail]:
    """Check for conflicts with faculty assignment."""
    conflicts = []

    # Check for blocking absences
    result = db.execute(
        select(Absence).where(
            and_(
                Absence.person_id == faculty_id,
                Absence.is_blocking == True,  # noqa: E712
                Absence.start_date <= week_end,
                Absence.end_date >= week_start,
            )
        )
    )
    absences = result.scalars().all()

    for absence in absences:
        conflicts.append(
            ConflictDetail(
                conflict_type=ConflictType.LEAVE_OVERLAP,
                severity="critical",
                description=f"Faculty has blocking {absence.absence_type} from {absence.start_date} to {absence.end_date}",
                faculty_id=faculty_id,
                week_date=week_start,
                blocking_absence_id=absence.id,
                blocking_absence_type=absence.absence_type,
            )
        )

    # Check for existing FMIT assignment
    result = db.execute(
        select(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .where(
            and_(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template_id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
        )
    )
    existing = result.scalars().first()

    if existing:
        conflicts.append(
            ConflictDetail(
                conflict_type=ConflictType.ALREADY_ASSIGNED,
                severity="critical",
                description="Faculty already has FMIT assignment for this week",
                faculty_id=faculty_id,
                week_date=week_start,
            )
        )

    # Check for back-to-back assignments (within 2 weeks)
    buffer_start = week_start - timedelta(days=14)
    buffer_end = week_end + timedelta(days=14)

    result = db.execute(
        select(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .where(
            and_(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template_id,
                Block.date >= buffer_start,
                Block.date <= buffer_end,
                Block.date < week_start,  # Only check past weeks
            )
        )
        .distinct()
    )
    nearby_assignments = result.scalars().all()

    if nearby_assignments:
        conflicts.append(
            ConflictDetail(
                conflict_type=ConflictType.BACK_TO_BACK,
                severity="warning",
                description="Faculty has FMIT assignment within 2 weeks - back-to-back scheduling",
                faculty_id=faculty_id,
                week_date=week_start,
            )
        )

    return conflicts


def calculate_jains_fairness_index(values: list[float]) -> float:
    """Calculate Jain's fairness index (0-1, 1=perfectly fair)."""
    if not values or len(values) == 0:
        return 1.0
    n = len(values)
    sum_values = sum(values)
    sum_squares = sum(x * x for x in values)
    if sum_squares == 0:
        return 1.0
    return round((sum_values * sum_values) / (n * sum_squares), 3)


# =============================================================================
# API Routes
# =============================================================================


@router.post(
    "/assignments",
    response_model=FMITAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create FMIT week assignment",
    description="Assign a faculty member to FMIT duty for an entire week (14 blocks).",
)
async def create_fmit_assignment(
    request: FMITAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create an FMIT assignment for a faculty member.

    Creates assignments for all 14 blocks (AM/PM x 7 days) in the FMIT week.
    Week dates are normalized to Friday-Thursday boundaries.

    Requires coordinator or admin role.
    """
    # Validate faculty exists
    result = db.execute(
        select(Person).where(
            and_(Person.id == request.faculty_id, Person.type == "faculty")
        )
    )
    faculty = result.scalar_one_or_none()

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Faculty not found", "error_code": "FACULTY_NOT_FOUND"},
        )

    # Get FMIT template
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "FMIT rotation template not found",
                "error_code": "TEMPLATE_NOT_FOUND",
            },
        )

    # Get week boundaries
    week_start = get_week_start(request.week_date)
    week_end = week_start + timedelta(days=6)

    # Check for conflicts
    conflicts = await check_faculty_conflicts(
        db, request.faculty_id, week_start, week_end, fmit_template.id
    )

    critical_conflicts = [c for c in conflicts if c.severity == "critical"]
    if critical_conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Cannot create assignment due to conflicts",
                "error_code": "CONFLICT_DETECTED",
                "conflicts": [c.model_dump() for c in critical_conflicts],
            },
        )

    # Get or create blocks for the week
    blocks = await get_or_create_blocks(db, week_start, week_end)

    # Create assignments for all blocks
    assignment_ids = []
    created_by = request.created_by or current_user.email or "system"

    for block in blocks:
        # Check if already assigned to this block
        result = db.execute(
            select(Assignment).where(
                and_(
                    Assignment.block_id == block.id,
                    Assignment.person_id == request.faculty_id,
                )
            )
        )
        if result.scalar_one_or_none():
            continue  # Skip, already assigned

        assignment = Assignment(
            block_id=block.id,
            person_id=request.faculty_id,
            rotation_template_id=fmit_template.id,
            role="primary",
            created_by=created_by,
        )
        db.add(assignment)
        db.flush()
        assignment_ids.append(assignment.id)

    db.commit()

    logger.info(
        f"Created FMIT assignment for faculty {faculty.name} week {week_start}",
        extra={
            "faculty_id": str(request.faculty_id),
            "week_start": str(week_start),
            "blocks_created": len(assignment_ids),
            "created_by": created_by,
        },
    )

    return FMITAssignmentResponse(
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        week_start=week_start,
        week_end=week_end,
        assignment_ids=assignment_ids,
        rotation_template_id=fmit_template.id,
        is_complete=len(assignment_ids) >= BLOCKS_PER_WEEK,
        block_count=len(assignment_ids),
        status=AssignmentStatus.CONFIRMED,
        notes=request.notes,
        created_at=datetime.utcnow(),
        created_by=created_by,
    )


@router.put(
    "/assignments/{week_date}",
    response_model=FMITAssignmentResponse,
    summary="Update FMIT week assignment",
    description="Reassign an FMIT week to a different faculty member.",
)
async def update_fmit_assignment(
    week_date: date,
    request: FMITAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an FMIT assignment for a specific week.

    Primarily used to reassign a week to a different faculty member.
    """
    # Get FMIT template
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FMIT rotation template not found"},
        )

    week_start = get_week_start(week_date)
    week_end = week_start + timedelta(days=6)

    # Find existing assignments for this week
    result = db.execute(
        select(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .options(joinedload(Assignment.person))
        .where(
            and_(
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
        )
    )
    existing_assignments = result.scalars().unique().all()

    if not existing_assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"No FMIT assignment found for week {week_start}"},
        )

    # If reassigning to new faculty
    if request.faculty_id:
        # Validate new faculty
        result = db.execute(
            select(Person).where(
                and_(Person.id == request.faculty_id, Person.type == "faculty")
            )
        )
        new_faculty = result.scalar_one_or_none()

        if not new_faculty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "New faculty not found"},
            )

        # Check conflicts for new faculty
        conflicts = await check_faculty_conflicts(
            db, request.faculty_id, week_start, week_end, fmit_template.id
        )
        critical_conflicts = [c for c in conflicts if c.severity == "critical"]

        if critical_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Cannot reassign due to conflicts",
                    "conflicts": [c.model_dump() for c in critical_conflicts],
                },
            )

        # Update all assignments to new faculty
        old_faculty_name = (
            existing_assignments[0].person.name if existing_assignments else "Unknown"
        )
        for assignment in existing_assignments:
            assignment.person_id = request.faculty_id

        db.commit()

        logger.info(
            f"Reassigned FMIT week {week_start} from {old_faculty_name} to {new_faculty.name}",
            extra={
                "week_start": str(week_start),
                "old_faculty": old_faculty_name,
                "new_faculty": new_faculty.name,
                "updated_by": current_user.email,
            },
        )

        return FMITAssignmentResponse(
            faculty_id=new_faculty.id,
            faculty_name=new_faculty.name,
            week_start=week_start,
            week_end=week_end,
            assignment_ids=[a.id for a in existing_assignments],
            rotation_template_id=fmit_template.id,
            is_complete=len(existing_assignments) >= BLOCKS_PER_WEEK,
            block_count=len(existing_assignments),
            status=request.status or AssignmentStatus.CONFIRMED,
            notes=request.notes,
        )

    # No faculty_id provided, just return current assignment
    current_faculty = existing_assignments[0].person
    return FMITAssignmentResponse(
        faculty_id=current_faculty.id,
        faculty_name=current_faculty.name,
        week_start=week_start,
        week_end=week_end,
        assignment_ids=[a.id for a in existing_assignments],
        rotation_template_id=fmit_template.id,
        is_complete=len(existing_assignments) >= BLOCKS_PER_WEEK,
        block_count=len(existing_assignments),
        status=request.status or AssignmentStatus.CONFIRMED,
        notes=request.notes,
    )


@router.delete(
    "/assignments/{faculty_id}/{week_date}",
    response_model=FMITAssignmentDeleteResponse,
    summary="Delete FMIT week assignment",
    description="Remove a faculty member's FMIT assignment for a specific week.",
)
async def delete_fmit_assignment(
    faculty_id: UUID,
    week_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete all FMIT assignments for a faculty member in a specific week.
    """
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FMIT rotation template not found"},
        )

    week_start = get_week_start(week_date)
    week_end = week_start + timedelta(days=6)

    # Find assignments to delete
    result = db.execute(
        select(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .where(
            and_(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
        )
    )
    assignments = result.scalars().all()

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"No FMIT assignments found for faculty {faculty_id} in week {week_start}"
            },
        )

    assignment_ids = [a.id for a in assignments]
    deleted_count = len(assignments)

    for assignment in assignments:
        db.delete(assignment)

    db.commit()

    logger.info(
        f"Deleted {deleted_count} FMIT assignments for week {week_start}",
        extra={
            "faculty_id": str(faculty_id),
            "week_start": str(week_start),
            "deleted_count": deleted_count,
            "deleted_by": current_user.email,
        },
    )

    return FMITAssignmentDeleteResponse(
        success=True,
        message=f"Deleted {deleted_count} FMIT assignments for week {week_start}",
        deleted_assignment_ids=assignment_ids,
        deleted_count=deleted_count,
    )


@router.post(
    "/assignments/bulk",
    response_model=FMITBulkAssignmentResponse,
    summary="Bulk create FMIT assignments",
    description="Create multiple FMIT week assignments in a single request.",
)
async def bulk_create_fmit_assignments(
    request: FMITBulkAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Bulk create FMIT assignments.

    Supports dry_run mode for validation and skip_conflicts mode
    to continue on errors.
    """
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FMIT rotation template not found"},
        )

    results = []
    successful_count = 0
    failed_count = 0
    skipped_count = 0
    warnings = []
    created_by = request.created_by or current_user.email or "system"

    for item in request.assignments:
        week_start = get_week_start(item.week_date)
        week_end = week_start + timedelta(days=6)

        # Validate faculty
        result = db.execute(
            select(Person).where(
                and_(Person.id == item.faculty_id, Person.type == "faculty")
            )
        )
        faculty = result.scalar_one_or_none()

        if not faculty:
            if request.skip_conflicts:
                skipped_count += 1
                results.append(
                    FMITBulkAssignmentResult(
                        faculty_id=item.faculty_id,
                        week_date=item.week_date,
                        success=False,
                        message="Faculty not found",
                        error_code="FACULTY_NOT_FOUND",
                    )
                )
                continue
            else:
                failed_count += 1
                results.append(
                    FMITBulkAssignmentResult(
                        faculty_id=item.faculty_id,
                        week_date=item.week_date,
                        success=False,
                        message="Faculty not found",
                        error_code="FACULTY_NOT_FOUND",
                    )
                )
                continue

        # Check conflicts
        conflicts = await check_faculty_conflicts(
            db, item.faculty_id, week_start, week_end, fmit_template.id
        )
        critical_conflicts = [c for c in conflicts if c.severity == "critical"]

        if critical_conflicts:
            if request.skip_conflicts:
                skipped_count += 1
                results.append(
                    FMITBulkAssignmentResult(
                        faculty_id=item.faculty_id,
                        week_date=item.week_date,
                        success=False,
                        message=f"Conflict: {critical_conflicts[0].description}",
                        error_code="CONFLICT_DETECTED",
                    )
                )
                continue
            else:
                failed_count += 1
                results.append(
                    FMITBulkAssignmentResult(
                        faculty_id=item.faculty_id,
                        week_date=item.week_date,
                        success=False,
                        message=f"Conflict: {critical_conflicts[0].description}",
                        error_code="CONFLICT_DETECTED",
                    )
                )
                continue

        # Add warnings
        warning_conflicts = [c for c in conflicts if c.severity == "warning"]
        for wc in warning_conflicts:
            warnings.append(f"{faculty.name} week {week_start}: {wc.description}")

        if request.dry_run:
            # Dry run - just validate
            successful_count += 1
            results.append(
                FMITBulkAssignmentResult(
                    faculty_id=item.faculty_id,
                    week_date=item.week_date,
                    success=True,
                    message="Validation passed (dry run)",
                )
            )
            continue

        # Create assignments
        blocks = await get_or_create_blocks(db, week_start, week_end)
        assignment_ids = []

        for block in blocks:
            # Check if already exists
            result = db.execute(
                select(Assignment).where(
                    and_(
                        Assignment.block_id == block.id,
                        Assignment.person_id == item.faculty_id,
                    )
                )
            )
            if result.scalar_one_or_none():
                continue

            assignment = Assignment(
                block_id=block.id,
                person_id=item.faculty_id,
                rotation_template_id=fmit_template.id,
                role="primary",
                created_by=created_by,
            )
            db.add(assignment)
            db.flush()
            assignment_ids.append(assignment.id)

        successful_count += 1
        results.append(
            FMITBulkAssignmentResult(
                faculty_id=item.faculty_id,
                week_date=item.week_date,
                success=True,
                message=f"Created {len(assignment_ids)} block assignments",
                assignment_ids=assignment_ids,
            )
        )

    if not request.dry_run:
        db.commit()

    logger.info(
        f"Bulk FMIT assignment: {successful_count} successful, {failed_count} failed, {skipped_count} skipped",
        extra={
            "total_requested": len(request.assignments),
            "successful": successful_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "dry_run": request.dry_run,
            "created_by": created_by,
        },
    )

    return FMITBulkAssignmentResponse(
        total_requested=len(request.assignments),
        successful_count=successful_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        results=results,
        dry_run=request.dry_run,
        warnings=warnings,
    )


@router.get(
    "/assignments/year-grid/{year}",
    response_model=YearGridResponse,
    summary="Get 52-week year grid",
    description="Get full year view with all FMIT weeks and faculty assignments.",
)
async def get_year_grid(
    year: int,
    academic_year: bool = Query(
        True, description="Use academic year (July-June) instead of calendar year"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a 52-week grid view of FMIT assignments.

    Returns all weeks in the year with assigned faculty, coverage stats,
    and fairness metrics.
    """
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FMIT rotation template not found"},
        )

    # Determine year boundaries
    if academic_year:
        start_date = date(year, 7, 1)
        end_date = date(year + 1, 6, 30)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    # Get all FMIT assignments in range
    result = db.execute(
        select(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .options(joinedload(Assignment.person))
        .where(
            and_(
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
    )
    assignments = result.scalars().unique().all()

    # Group assignments by week
    week_assignments = {}
    for assignment in assignments:
        week_start = get_week_start(assignment.block.date)
        if week_start not in week_assignments:
            week_assignments[week_start] = {
                "faculty_id": assignment.person_id,
                "faculty_name": assignment.person.name,
                "count": 0,
            }
        week_assignments[week_start]["count"] += 1

    # Build week slots
    weeks = []
    today = date.today()
    current_week_start = get_week_start(today)
    week_number = 1
    current_date = get_week_start(start_date)

    while current_date <= end_date:
        week_end = current_date + timedelta(days=6)
        week_data = week_assignments.get(current_date)

        # Check for conflicts (unassigned weeks are "conflicts")
        has_conflict = week_data is None and current_date >= today

        weeks.append(
            WeekSlot(
                week_number=week_number,
                week_start=current_date,
                week_end=week_end,
                is_current_week=current_date == current_week_start,
                is_past=current_date < current_week_start,
                faculty_id=week_data["faculty_id"] if week_data else None,
                faculty_name=week_data["faculty_name"] if week_data else None,
                is_complete=(week_data["count"] >= BLOCKS_PER_WEEK)
                if week_data
                else False,
                has_conflict=has_conflict,
                conflict_reason="No faculty assigned" if has_conflict else None,
            )
        )

        current_date += timedelta(days=7)
        week_number += 1

    # Get all faculty and calculate summaries
    result = db.execute(select(Person).where(Person.type == "faculty"))
    all_faculty = result.scalars().all()

    faculty_summaries = []
    faculty_week_counts = []

    for faculty in all_faculty:
        faculty_weeks = [ws.week_start for ws in weeks if ws.faculty_id == faculty.id]
        total_weeks = len(faculty_weeks)
        faculty_week_counts.append(float(total_weeks))

        completed = len([w for w in faculty_weeks if get_week_start(today) > w])
        upcoming = total_weeks - completed

        target = 52.0 / max(len(all_faculty), 1)
        variance = total_weeks - target

        faculty_summaries.append(
            FacultyYearSummary(
                faculty_id=faculty.id,
                faculty_name=faculty.name,
                total_weeks=total_weeks,
                completed_weeks=completed,
                upcoming_weeks=upcoming,
                target_weeks=round(target, 2),
                variance=round(variance, 2),
                is_balanced=abs(variance) <= 1.0,
                week_dates=faculty_weeks,
            )
        )

    # Sort by name
    faculty_summaries.sort(key=lambda x: x.faculty_name)

    # Calculate metrics
    assigned_weeks = len([w for w in weeks if w.faculty_id is not None])
    total_weeks = len(weeks)
    coverage_pct = round((assigned_weeks / total_weeks * 100) if total_weeks else 0, 1)
    fairness = calculate_jains_fairness_index(faculty_week_counts)

    return YearGridResponse(
        year=year,
        academic_year_start=start_date,
        academic_year_end=end_date,
        weeks=weeks,
        faculty_summaries=faculty_summaries,
        total_weeks=total_weeks,
        assigned_weeks=assigned_weeks,
        unassigned_weeks=total_weeks - assigned_weeks,
        coverage_percentage=coverage_pct,
        fairness_index=fairness,
        generated_at=datetime.utcnow(),
    )


@router.get(
    "/assignments/check-conflicts",
    response_model=ConflictCheckResponse,
    summary="Check assignment conflicts",
    description="Pre-check for conflicts before creating an assignment.",
)
async def check_conflicts(
    faculty_id: UUID = Query(..., description="Faculty member UUID"),
    week_date: date = Query(..., description="Target week date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Check for conflicts before creating an FMIT assignment.

    Returns detailed conflict information and suggestions.
    """
    fmit_template = await get_fmit_template(db)
    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FMIT rotation template not found"},
        )

    # Validate faculty
    result = db.execute(
        select(Person).where(and_(Person.id == faculty_id, Person.type == "faculty"))
    )
    faculty = result.scalar_one_or_none()

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Faculty not found"},
        )

    week_start = get_week_start(week_date)
    week_end = week_start + timedelta(days=6)

    # Check conflicts
    conflicts = await check_faculty_conflicts(
        db, faculty_id, week_start, week_end, fmit_template.id
    )

    # Add faculty name to conflicts
    for conflict in conflicts:
        conflict.faculty_name = faculty.name

    critical_conflicts = [c for c in conflicts if c.severity == "critical"]
    warnings = [c.description for c in conflicts if c.severity == "warning"]

    # Generate suggestions if there are conflicts
    suggestions = []
    if critical_conflicts:
        # Suggest alternative faculty
        result = db.execute(
            select(Person).where(
                and_(Person.type == "faculty", Person.id != faculty_id)
            )
        )
        other_faculty = result.scalars().all()

        for other in other_faculty[:3]:  # Suggest up to 3 alternatives
            other_conflicts = await check_faculty_conflicts(
                db, other.id, week_start, week_end, fmit_template.id
            )
            if not [c for c in other_conflicts if c.severity == "critical"]:
                suggestions.append(f"Consider {other.name} who has no conflicts")

    return ConflictCheckResponse(
        can_assign=len(critical_conflicts) == 0,
        conflicts=conflicts,
        warnings=warnings,
        suggestions=suggestions,
    )
