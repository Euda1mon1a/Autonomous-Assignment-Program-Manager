"""Schedule generation and validation API routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.schedule import (
    ScheduleRequest,
    ScheduleResponse,
    ValidationResult,
    EmergencyRequest,
    EmergencyResponse,
    SolverStatistics,
)
from app.scheduling.engine import SchedulingEngine
from app.scheduling.validator import ACGMEValidator
from app.services.emergency_coverage import EmergencyCoverageService
from app.core.security import get_current_active_user

router = APIRouter()


@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate schedule for a date range. Requires authentication.

    Uses the scheduling engine with constraint-based optimization:
    1. Load absences and build availability matrix
    2. Assign residents using selected algorithm
    3. Assign supervising faculty based on ACGME ratios
    4. Validate ACGME compliance

    Available algorithms:
    - greedy: Fast heuristic, good for initial solutions
    - cp_sat: OR-Tools constraint programming, optimal solutions
    - pulp: PuLP linear programming, fast for large problems
    - hybrid: Combines CP-SAT and PuLP for best results
    """
    try:
        engine = SchedulingEngine(db, request.start_date, request.end_date)

        # Generate schedule with selected algorithm
        result = engine.generate(
            pgy_levels=request.pgy_levels,
            rotation_template_ids=request.rotation_template_ids,
            algorithm=request.algorithm.value,
            timeout_seconds=request.timeout_seconds,
        )

        # Build solver statistics if available
        solver_stats = None
        if result.get("solver_stats"):
            stats = result["solver_stats"]
            solver_stats = SolverStatistics(
                total_blocks=stats.get("total_blocks"),
                total_residents=stats.get("total_residents"),
                coverage_rate=stats.get("coverage_rate"),
                branches=stats.get("branches"),
                conflicts=stats.get("conflicts"),
            )

        return ScheduleResponse(
            status=result["status"],
            message=result["message"],
            total_blocks_assigned=result["total_assigned"],
            total_blocks=result["total_blocks"],
            validation=result["validation"],
            run_id=result.get("run_id"),
            solver_stats=solver_stats,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate", response_model=ValidationResult)
async def validate_schedule(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
):
    """
    Validate current schedule for ACGME compliance.

    Checks:
    - 80-hour rule (rolling 4-week average)
    - 1-in-7 days off
    - Supervision ratios (1:2 for PGY-1, 1:4 for PGY-2/3)
    """
    from datetime import datetime

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    validator = ACGMEValidator(db)
    result = validator.validate_all(start, end)

    return result


@router.post("/emergency-coverage", response_model=EmergencyResponse)
async def handle_emergency_coverage(
    request: EmergencyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Handle emergency absence and find replacement coverage. Requires authentication.

    Used for:
    - Military deployments
    - TDY assignments
    - Medical emergencies
    - Family emergencies

    Finds replacement coverage for affected assignments,
    prioritizing critical services (inpatient, call).
    """
    service = EmergencyCoverageService(db)

    result = await service.handle_emergency_absence(
        person_id=request.person_id,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        is_deployment=request.is_deployment,
    )

    return EmergencyResponse(
        status=result["status"],
        replacements_found=result["replacements_found"],
        coverage_gaps=result["coverage_gaps"],
        requires_manual_review=result["requires_manual_review"],
        details=result["details"],
    )


@router.get("/{start_date}/{end_date}")
async def get_schedule(start_date: str, end_date: str, db: Session = Depends(get_db)):
    """
    Get the schedule for a date range.

    Returns all assignments with person and rotation template details.
    """
    from datetime import datetime
    from sqlalchemy.orm import joinedload
    from app.models.assignment import Assignment
    from app.models.block import Block

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    assignments = (
        db.query(Assignment)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .join(Block)
        .filter(Block.date >= start, Block.date <= end)
        .order_by(Block.date, Block.time_of_day)
        .all()
    )

    # Group by date for calendar view
    schedule_by_date = {}
    for assignment in assignments:
        date_str = assignment.block.date.isoformat()
        if date_str not in schedule_by_date:
            schedule_by_date[date_str] = {"AM": [], "PM": []}

        schedule_by_date[date_str][assignment.block.time_of_day].append({
            "id": str(assignment.id),
            "person": {
                "id": str(assignment.person.id),
                "name": assignment.person.name,
                "type": assignment.person.type,
                "pgy_level": assignment.person.pgy_level,
            },
            "role": assignment.role,
            "activity": assignment.activity_name,
            "abbreviation": assignment.abbreviation,
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "schedule": schedule_by_date,
        "total_assignments": len(assignments),
    }
