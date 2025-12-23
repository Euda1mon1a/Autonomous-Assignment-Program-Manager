"""FMIT Timeline API routes for Gantt-style view of faculty assignments.

Provides endpoints for visualizing faculty assignment timelines:
- Academic year overview
- Individual faculty timelines
- Weekly views
- Gantt chart data for visualization libraries

All endpoints include workload balance metrics and fairness indicators.
"""

import statistics
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.user import User
from app.schemas.fmit_timeline import (
    AggregateMetrics,
    FacultyTimeline,
    GanttDataResponse,
    GanttGroup,
    GanttTask,
    LoadDistribution,
    TimelineResponse,
    WeekAssignment,
    WeeklyView,
    WeeklyViewResponse,
    WorkloadSummary,
)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================


def get_academic_year_dates() -> tuple[date, date]:
    """
    Get start and end dates for current academic year.
    Assumes academic year starts July 1st.
    """
    today = date.today()
    if today.month >= 7:
        # July-December: current year is start year
        start_date = date(today.year, 7, 1)
        end_date = date(today.year + 1, 6, 30)
    else:
        # January-June: previous year is start year
        start_date = date(today.year - 1, 7, 1)
        end_date = date(today.year, 6, 30)
    return start_date, end_date


def get_week_bounds(target_date: date) -> tuple[date, date]:
    """Get Monday and Sunday for the week containing target_date."""
    # Python weekday: Monday=0, Sunday=6
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def calculate_jains_fairness_index(values: list[float]) -> float:
    """
    Calculate Jain's fairness index.
    Returns value between 0 and 1, where 1 = perfectly fair.
    Formula: (sum(x_i))^2 / (n * sum(x_i^2))
    """
    if not values or len(values) == 0:
        return 1.0

    n = len(values)
    sum_values = sum(values)
    sum_squares = sum(x * x for x in values)

    if sum_squares == 0:
        return 1.0

    fairness = (sum_values * sum_values) / (n * sum_squares)
    return round(fairness, 3)


def get_faculty_weekly_assignments(
    db: Session, faculty_id: UUID, start_date: date, end_date: date
) -> list[WeekAssignment]:
    """
    Get week-by-week assignment data for a faculty member.
    Groups assignments by week and calculates status.
    """
    # Get all assignments for this faculty in date range
    assignments = (
        db.query(Assignment)
        .join(Block)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(
            and_(
                Assignment.person_id == faculty_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        .limit(100)
        .all()
    )

    # Group by week
    weeks_map = {}
    for assignment in assignments:
        block = assignment.block
        week_start, week_end = get_week_bounds(block.date)
        week_key = week_start.isoformat()

        if week_key not in weeks_map:
            weeks_map[week_key] = {
                "week_start": week_start,
                "week_end": week_end,
                "assignment_count": 0,
                "total_blocks": 0,
                "dates": set(),
            }

        weeks_map[week_key]["assignment_count"] += 1
        weeks_map[week_key]["total_blocks"] += 1
        weeks_map[week_key]["dates"].add(block.date)

    # Convert to list of WeekAssignment objects
    today = date.today()
    week_assignments = []

    for week_data in weeks_map.values():
        # Determine status based on date
        if week_data["week_end"] < today:
            status = "completed"
        elif week_data["week_start"] <= today <= week_data["week_end"]:
            status = "in_progress"
        else:
            status = "scheduled"

        week_assignments.append(
            WeekAssignment(
                week_start=week_data["week_start"],
                week_end=week_data["week_end"],
                status=status,
                assignment_count=week_data["assignment_count"],
                total_blocks=week_data["total_blocks"],
            )
        )

    # Sort by week start date
    week_assignments.sort(key=lambda w: w.week_start)
    return week_assignments


def calculate_workload_summary(
    weekly_assignments: list[WeekAssignment], target_weeks: float = 4.5
) -> WorkloadSummary:
    """Calculate workload summary metrics for a faculty member."""
    total_weeks = len(weekly_assignments)

    if target_weeks == 0:
        utilization_percent = 0.0
        variance = 0.0
        is_balanced = True
    else:
        utilization_percent = round((total_weeks / target_weeks) * 100.0, 1)
        variance = round(total_weeks - target_weeks, 2)
        # Consider balanced if within 15% of target
        is_balanced = abs(variance) <= (target_weeks * 0.15)

    return WorkloadSummary(
        total_weeks=total_weeks,
        target_weeks=target_weeks,
        utilization_percent=utilization_percent,
        is_balanced=is_balanced,
        variance_from_target=variance,
    )


def get_all_faculty_timelines(
    db: Session, start_date: date, end_date: date, faculty_filter: UUID | None = None
) -> list[FacultyTimeline]:
    """Get timeline data for all faculty members (or specific faculty)."""
    # Get all faculty with FMIT assignments in the date range
    query = (
        db.query(Person)
        .join(Assignment)
        .join(Block)
        .filter(
            and_(
                Person.type == "faculty",
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
    )

    if faculty_filter:
        query = query.filter(Person.id == faculty_filter)

    faculty_list = query.distinct().limit(100).all()

    timelines = []
    for faculty in faculty_list:
        weekly_assignments = get_faculty_weekly_assignments(
            db, faculty.id, start_date, end_date
        )

        workload = calculate_workload_summary(weekly_assignments)

        # Get department/specialty from person model
        department = getattr(faculty, "primary_duty", None)
        specialty = None
        if hasattr(faculty, "specialties") and faculty.specialties:
            specialty = faculty.specialties[0] if len(faculty.specialties) > 0 else None

        timelines.append(
            FacultyTimeline(
                faculty_id=faculty.id,
                faculty_name=faculty.name,
                weeks_assigned=weekly_assignments,
                workload=workload,
                department=department,
                specialty=specialty,
            )
        )

    return timelines


def calculate_aggregate_metrics(
    timelines: list[FacultyTimeline], start_date: date, end_date: date, db: Session
) -> AggregateMetrics:
    """Calculate system-wide fairness and balance metrics."""
    if not timelines:
        return AggregateMetrics(
            fairness_index=1.0,
            load_distribution=LoadDistribution(),
            total_faculty=0,
            total_weeks_scheduled=0,
            coverage_percentage=0.0,
        )

    # Collect workload values
    weeks_per_faculty = [t.workload.total_weeks for t in timelines]

    # Calculate fairness index
    fairness_index = calculate_jains_fairness_index(
        [float(w) for w in weeks_per_faculty]
    )

    # Calculate distribution statistics
    load_dist = LoadDistribution(
        mean=round(statistics.mean(weeks_per_faculty), 2) if weeks_per_faculty else 0.0,
        median=(
            round(statistics.median(weeks_per_faculty), 2) if weeks_per_faculty else 0.0
        ),
        stdev=(
            round(statistics.stdev(weeks_per_faculty), 2)
            if len(weeks_per_faculty) > 1
            else 0.0
        ),
        min=float(min(weeks_per_faculty)) if weeks_per_faculty else 0.0,
        max=float(max(weeks_per_faculty)) if weeks_per_faculty else 0.0,
    )

    # Calculate coverage percentage
    # Count total FMIT blocks that need coverage
    total_blocks = (
        db.query(Block)
        .filter(and_(Block.date >= start_date, Block.date <= end_date))
        .count()
    )

    # Count blocks with assignments
    covered_blocks = (
        db.query(Block)
        .join(Assignment)
        .filter(and_(Block.date >= start_date, Block.date <= end_date))
        .distinct()
        .count()
    )

    coverage_percentage = round(
        (covered_blocks / total_blocks * 100.0) if total_blocks > 0 else 0.0, 1
    )

    return AggregateMetrics(
        fairness_index=fairness_index,
        load_distribution=load_dist,
        total_faculty=len(timelines),
        total_weeks_scheduled=sum(weeks_per_faculty),
        coverage_percentage=coverage_percentage,
    )


# ============================================================================
# API Routes
# ============================================================================


@router.get("/academic-year", response_model=TimelineResponse)
async def get_academic_year_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get full academic year timeline for all FMIT faculty.

    Returns comprehensive timeline data showing:
    - Week-by-week assignments for each faculty member
    - Workload balance metrics
    - System-wide fairness indicators
    - Coverage statistics

    Requires authentication.
    """
    start_date, end_date = get_academic_year_dates()

    # Get all faculty timelines
    timelines = get_all_faculty_timelines(db, start_date, end_date)

    # Calculate aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(timelines, start_date, end_date, db)

    return TimelineResponse(
        timeline_data=timelines,
        aggregate_metrics=aggregate_metrics,
        start_date=start_date,
        end_date=end_date,
        generated_at=datetime.utcnow(),
    )


@router.get("/faculty/{faculty_id}", response_model=TimelineResponse)
async def get_faculty_timeline(
    faculty_id: UUID,
    start_date: date | None = Query(
        None, description="Start date (default: academic year start)"
    ),
    end_date: date | None = Query(
        None, description="End date (default: academic year end)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get timeline for a single faculty member.

    Returns detailed assignment timeline for one faculty member including:
    - Weekly assignment breakdown
    - Workload metrics compared to target
    - Balance indicators

    Args:
        faculty_id: UUID of the faculty member
        start_date: Optional start date (defaults to academic year start)
        end_date: Optional end date (defaults to academic year end)

    Requires authentication.
    """
    # Verify faculty exists
    faculty = db.query(Person).filter(Person.id == faculty_id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faculty member with ID {faculty_id} not found",
        )

    # Default to academic year if dates not provided
    if start_date is None or end_date is None:
        ay_start, ay_end = get_academic_year_dates()
        start_date = start_date or ay_start
        end_date = end_date or ay_end

    # Get timeline for this faculty member
    timelines = get_all_faculty_timelines(
        db, start_date, end_date, faculty_filter=faculty_id
    )

    # If no assignments found, create empty timeline
    if not timelines:
        timelines = [
            FacultyTimeline(
                faculty_id=faculty.id,
                faculty_name=faculty.name,
                weeks_assigned=[],
                workload=WorkloadSummary(),
                department=getattr(faculty, "primary_duty", None),
                specialty=(
                    faculty.specialties[0]
                    if hasattr(faculty, "specialties") and faculty.specialties
                    else None
                ),
            )
        ]

    # Calculate metrics (even for single faculty)
    aggregate_metrics = calculate_aggregate_metrics(timelines, start_date, end_date, db)

    return TimelineResponse(
        timeline_data=timelines,
        aggregate_metrics=aggregate_metrics,
        start_date=start_date,
        end_date=end_date,
        generated_at=datetime.utcnow(),
    )


@router.get("/week/{week_start}", response_model=WeeklyViewResponse)
async def get_weekly_view(
    week_start: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get weekly view of FMIT assignments.

    Returns detailed view of a specific week showing:
    - All faculty assignments for the week
    - Coverage statistics
    - Adjacent week summaries for navigation

    Args:
        week_start: Start date of the week (will normalize to Monday)

    Requires authentication.
    """
    # Normalize to Monday
    week_start, week_end = get_week_bounds(week_start)

    # Get all assignments for this week
    assignments = (
        db.query(Assignment)
        .join(Block)
        .join(Person)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(
            and_(
                Block.date >= week_start,
                Block.date <= week_end,
                Person.type == "faculty",
            )
        )
        .limit(100)
        .all()
    )

    # Group assignments by faculty
    faculty_assignments = {}
    for assignment in assignments:
        faculty = assignment.person
        faculty_key = str(faculty.id)

        if faculty_key not in faculty_assignments:
            faculty_assignments[faculty_key] = {
                "faculty_id": str(faculty.id),
                "faculty_name": faculty.name,
                "assignments": [],
            }

        faculty_assignments[faculty_key]["assignments"].append(
            {
                "date": assignment.block.date.isoformat(),
                "time_of_day": assignment.block.time_of_day,
                "block_id": str(assignment.block.id),
                "assignment_id": str(assignment.id),
                "role": assignment.role,
            }
        )

    # Calculate coverage
    total_blocks = (
        db.query(Block)
        .filter(and_(Block.date >= week_start, Block.date <= week_end))
        .count()
    )

    filled_slots = len(assignments)
    coverage_percentage = round(
        (filled_slots / total_blocks * 100.0) if total_blocks > 0 else 0.0, 1
    )

    # Get adjacent week summaries
    prev_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)

    prev_week_count = (
        db.query(Assignment)
        .join(Block)
        .filter(and_(Block.date >= prev_week_start, Block.date < week_start))
        .count()
    )

    next_week_count = (
        db.query(Assignment)
        .join(Block)
        .filter(
            and_(
                Block.date >= next_week_start,
                Block.date < next_week_start + timedelta(days=7),
            )
        )
        .count()
    )

    adjacent_weeks = {
        "previous_week": {
            "week_start": prev_week_start.isoformat(),
            "assignment_count": prev_week_count,
        },
        "next_week": {
            "week_start": next_week_start.isoformat(),
            "assignment_count": next_week_count,
        },
    }

    week_data = WeeklyView(
        week_start=week_start,
        week_end=week_end,
        faculty_assignments=list(faculty_assignments.values()),
        total_slots=total_blocks,
        filled_slots=filled_slots,
        coverage_percentage=coverage_percentage,
    )

    return WeeklyViewResponse(
        week_data=week_data,
        adjacent_weeks=adjacent_weeks,
        generated_at=datetime.utcnow(),
    )


@router.get("/gantt-data", response_model=GanttDataResponse)
async def get_gantt_data(
    start_date: date | None = Query(
        None, description="Start date (default: academic year start)"
    ),
    end_date: date | None = Query(
        None, description="End date (default: academic year end)"
    ),
    faculty_ids: list[UUID] | None = Query(
        None, description="Filter by specific faculty IDs"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get Gantt chart JSON data for visualization libraries.

    Returns data formatted for Gantt chart rendering with:
    - Tasks grouped by faculty member
    - Assignment periods as task bars
    - Progress indicators based on completion status
    - Custom styling hints for overloaded faculty

    Args:
        start_date: Optional start date (defaults to academic year start)
        end_date: Optional end date (defaults to academic year end)
        faculty_ids: Optional list of faculty IDs to filter

    Requires authentication.
    """
    # Default to academic year if dates not provided
    if start_date is None or end_date is None:
        ay_start, ay_end = get_academic_year_dates()
        start_date = start_date or ay_start
        end_date = end_date or ay_end

    # Get faculty timelines
    query = (
        db.query(Person)
        .join(Assignment)
        .join(Block)
        .filter(
            and_(
                Person.type == "faculty",
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
    )

    if faculty_ids:
        query = query.filter(Person.id.in_(faculty_ids))

    faculty_list = query.distinct().limit(100).all()

    groups = []
    all_tasks = []
    task_counter = 0

    for faculty in faculty_list:
        weekly_assignments = get_faculty_weekly_assignments(
            db, faculty.id, start_date, end_date
        )

        if not weekly_assignments:
            continue

        # Create tasks for each continuous period
        tasks = []
        for week in weekly_assignments:
            task_counter += 1
            task_id = f"task_{faculty.id}_{task_counter}"

            # Determine progress based on status
            progress = (
                100.0
                if week.status == "completed"
                else 50.0 if week.status == "in_progress" else 0.0
            )

            # Custom styling based on workload
            styles = {}
            if week.total_blocks > 8:  # Heavy week
                styles = {"backgroundColor": "#ff6b6b", "color": "#ffffff"}
            elif week.total_blocks > 4:
                styles = {"backgroundColor": "#ffd93d", "color": "#000000"}
            else:
                styles = {"backgroundColor": "#6bcf7f", "color": "#ffffff"}

            task = GanttTask(
                id=task_id,
                name=faculty.name,
                start=week.week_start,
                end=week.week_end,
                progress=progress,
                dependencies=[],
                resource=faculty.name,
                type="task",
                styles=styles,
            )

            tasks.append(task)
            all_tasks.append(task)

        # Create group for this faculty
        group = GanttGroup(id=str(faculty.id), name=faculty.name, tasks=tasks)
        groups.append(group)

    # Metadata
    metadata = {
        "total_faculty": len(groups),
        "total_tasks": len(all_tasks),
        "date_range_days": (end_date - start_date).days,
        "view_mode": "Week",
    }

    return GanttDataResponse(
        groups=groups,
        all_tasks=all_tasks,
        date_range={"start": start_date.isoformat(), "end": end_date.isoformat()},
        metadata=metadata,
        generated_at=datetime.utcnow(),
    )
