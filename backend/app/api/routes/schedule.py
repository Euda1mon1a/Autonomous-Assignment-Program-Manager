"""Schedule generation and validation API routes."""
import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.file_security import FileValidationError, validate_excel_upload
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.scheduling.engine import SchedulingEngine
from app.scheduling.validator import ACGMEValidator
from app.schemas.schedule import (
    AlternatingPatternInfo,
    ConflictItem,
    ConflictSummary,
    EmergencyRequest,
    EmergencyResponse,
    ImportAnalysisResponse,
    Recommendation,
    ScheduleRequest,
    ScheduleResponse,
    ScheduleSummary,
    SolverStatistics,
    SwapCandidateResponse,
    SwapFinderRequest,
    SwapFinderResponse,
    ValidationResult,
)
from app.services.emergency_coverage import EmergencyCoverageService
from app.services.idempotency_service import (
    IdempotencyService,
    extract_idempotency_params,
)
from app.services.xlsx_import import (
    ExternalConflict,
    FacultyTarget,
    SwapFinder,
    analyze_schedule_conflicts,
    load_external_conflicts_from_absences,
)

# Import observability metrics (optional - graceful degradation)
try:
    from app.core.observability import metrics as obs_metrics
except ImportError:
    obs_metrics = None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    idempotency_key: str | None = Header(
        None,
        alias="Idempotency-Key",
        description="Unique key to prevent duplicate schedule generations. "
                    "If the same key is sent with identical parameters, "
                    "the cached result will be returned."
    ),
):
    """
    Generate schedule for a date range. Requires authentication.

    Supports idempotency via the Idempotency-Key header. If the same key
    is sent with identical request parameters, the cached result will be
    returned instead of generating a new schedule.

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
    from datetime import datetime, timedelta

    from app.models.schedule_run import ScheduleRun

    # Initialize idempotency service
    idempotency_service = IdempotencyService(db)
    idempotency_request = None

    # Extract request parameters for hashing
    request_params = {
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "algorithm": request.algorithm.value,
        "pgy_levels": request.pgy_levels,
        "rotation_template_ids": [str(x) for x in request.rotation_template_ids] if request.rotation_template_ids else None,
        "timeout_seconds": request.timeout_seconds,
    }

    # If idempotency key provided, check for existing request
    if idempotency_key:
        body_hash = idempotency_service.compute_body_hash(
            extract_idempotency_params(request_params)
        )

        # Check for key conflict (same key, different body)
        conflict = idempotency_service.check_key_conflict(idempotency_key, body_hash)
        if conflict:
            if obs_metrics:
                obs_metrics.record_idempotency_conflict()
            raise HTTPException(
                status_code=422,
                detail="Idempotency key was already used with different request parameters. "
                       "Use a new key for different requests.",
            )

        # Check for existing request with same key and body
        existing = idempotency_service.get_existing_request(idempotency_key, body_hash)
        if existing:
            if existing.is_pending:
                # Request is still being processed
                if obs_metrics:
                    obs_metrics.record_idempotency_pending()
                raise HTTPException(
                    status_code=409,
                    detail="A request with this idempotency key is currently being processed. "
                           "Please wait for it to complete.",
                )
            elif existing.is_completed and existing.response_body:
                # Return cached response
                if obs_metrics:
                    obs_metrics.record_idempotency_hit()
                logger.info(f"Returning cached response for idempotency key: {idempotency_key[:8]}...")
                status_code = int(existing.response_status_code or 200)
                return JSONResponse(
                    status_code=status_code,
                    content=existing.response_body,
                    headers={"X-Idempotency-Replayed": "true"},
                )
            elif existing.is_failed:
                # Return cached error response
                if obs_metrics:
                    obs_metrics.record_idempotency_hit()
                logger.info(f"Returning cached error for idempotency key: {idempotency_key[:8]}...")
                status_code = int(existing.response_status_code or 500)
                raise HTTPException(
                    status_code=status_code,
                    detail=existing.error_message or "Previous request failed",
                )

        # Create new idempotency request record (cache miss)
        if obs_metrics:
            obs_metrics.record_idempotency_miss()
        try:
            idempotency_request = idempotency_service.create_request(
                idempotency_key=idempotency_key,
                body_hash=body_hash,
                request_params=request_params,
            )
        except Exception as e:
            logger.warning(f"Failed to create idempotency record: {e}")
            # Continue without idempotency tracking

    # Issue #1: Double-submit / Re-entrancy protection
    # Check for in-progress generations for overlapping date ranges
    recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
    in_progress_run = (
        db.query(ScheduleRun)
        .filter(
            ScheduleRun.status == "in_progress",
            ScheduleRun.created_at >= recent_cutoff,
            # Check for overlapping date ranges
            ScheduleRun.start_date <= request.end_date,
            ScheduleRun.end_date >= request.start_date,
        )
        .first()
    )

    if in_progress_run:
        error_msg = (
            "Schedule generation already in progress for overlapping date range. "
            "Please wait for the current run to complete."
        )
        if idempotency_request:
            idempotency_service.mark_failed(
                idempotency_request,
                error_message=error_msg,
                response_body={"detail": error_msg},
                response_status_code=409,
            )
            db.commit()
        raise HTTPException(status_code=409, detail=error_msg)

    algorithm = request.algorithm.value
    try:
        engine = SchedulingEngine(db, request.start_date, request.end_date)

        # Generate schedule with selected algorithm (timed for metrics)
        if obs_metrics:
            with obs_metrics.time_schedule_generation(algorithm):
                result = engine.generate(
                    pgy_levels=request.pgy_levels,
                    rotation_template_ids=request.rotation_template_ids,
                    algorithm=algorithm,
                    timeout_seconds=request.timeout_seconds,
                )
        else:
            result = engine.generate(
                pgy_levels=request.pgy_levels,
                rotation_template_ids=request.rotation_template_ids,
                algorithm=algorithm,
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

        response = ScheduleResponse(
            status=result["status"],
            message=result["message"],
            total_blocks_assigned=result["total_assigned"],
            total_blocks=result["total_blocks"],
            validation=result["validation"],
            run_id=result.get("run_id"),
            solver_stats=solver_stats,
        )

        # Issue #5: Partial success semantics - use proper HTTP status codes
        # Return 207 Multi-Status for partial success (some assignments created but with violations)
        # Return 422 for validation errors or complete failure
        if result["status"] == "failed":
            if obs_metrics:
                obs_metrics.record_schedule_failure(algorithm)
            error_msg = result["message"]
            if idempotency_request:
                idempotency_service.mark_failed(
                    idempotency_request,
                    error_message=error_msg,
                    response_body={"detail": error_msg},
                    response_status_code=422,
                )
                db.commit()
            raise HTTPException(status_code=422, detail=error_msg)
        elif result["status"] == "partial":
            # Use 207 Multi-Status for partial success
            if obs_metrics:
                obs_metrics.record_schedule_success(algorithm, result.get("total_assigned", 0))
            response_body = response.model_dump(mode="json")
            if idempotency_request:
                idempotency_service.mark_completed(
                    idempotency_request,
                    result_ref=result.get("run_id"),
                    response_body=response_body,
                    response_status_code=207,
                )
                db.commit()
            return JSONResponse(
                status_code=207,
                content=response_body,
            )

        # Success - record metrics and cache the response
        if obs_metrics:
            obs_metrics.record_schedule_success(algorithm, result.get("total_assigned", 0))
        response_body = response.model_dump(mode="json")
        if idempotency_request:
            idempotency_service.mark_completed(
                idempotency_request,
                result_ref=result.get("run_id"),
                response_body=response_body,
                response_status_code=200,
            )
            db.commit()

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        if obs_metrics:
            obs_metrics.record_schedule_failure(algorithm)
        logger.error(f"Error generating schedule: {e}", exc_info=True)
        error_msg = "An error occurred generating the schedule"
        if idempotency_request:
            idempotency_service.mark_failed(
                idempotency_request,
                error_message=str(e),
                response_body={"detail": error_msg},
                response_status_code=500,
            )
            try:
                db.commit()
            except Exception:
                db.rollback()
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/validate", response_model=ValidationResult)
def validate_schedule(
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
def get_schedule(start_date: str, end_date: str, db: Session = Depends(get_db)):
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


@router.post("/import/analyze", response_model=ImportAnalysisResponse)
def analyze_imported_schedules(
    fmit_file: UploadFile = File(..., description="FMIT rotation schedule Excel file"),
    clinic_file: UploadFile | None = File(None, description="Clinic schedule Excel file (optional)"),
    specialty_providers: str | None = Form(
        None,
        description="JSON mapping of specialty to providers, e.g., {\"Sports Medicine\": [\"Tagawa\"]}"
    ),
    db: Session = Depends(get_db),
):
    """
    Import and analyze schedules for conflicts.

    Upload Excel files containing FMIT rotation and clinic schedules.
    The system will detect:
    - Double-bookings (same provider scheduled for FMIT and clinic)
    - Specialty unavailability (specialty provider on FMIT creates clinic gap)
    - Alternating patterns (week-on/week-off that's hard on families)

    This is an analysis-only endpoint - no data is written to the database.
    Use this to identify conflicts before finalizing schedules.

    Args:
        fmit_file: Excel file with FMIT rotation schedule
        clinic_file: Excel file with clinic schedule (optional)
        specialty_providers: JSON string mapping specialty to provider names

    Returns:
        Analysis results with conflicts and recommendations
    """
    import json

    # Parse specialty providers if provided
    specialty_map = None
    if specialty_providers:
        try:
            specialty_map = json.loads(specialty_providers)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid specialty_providers JSON format"
            )

    # Read file contents
    try:
        fmit_bytes = fmit_file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file"
        )

    # Validate FMIT file
    try:
        validate_excel_upload(fmit_bytes, fmit_file.filename)
    except FileValidationError as e:
        raise HTTPException(
            status_code=400,
            detail="File validation failed"
        )

    clinic_bytes = None
    if clinic_file:
        try:
            clinic_bytes = clinic_file.file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail="Failed to read uploaded file"
            )

        # Validate clinic file
        try:
            validate_excel_upload(clinic_bytes, clinic_file.filename)
        except FileValidationError as e:
            raise HTTPException(
                status_code=400,
                detail="File validation failed"
            )

    # Run analysis
    result = analyze_schedule_conflicts(
        fmit_bytes=fmit_bytes,
        clinic_bytes=clinic_bytes,
        specialty_providers=specialty_map,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Analysis failed")
        )

    # Build response
    return ImportAnalysisResponse(
        success=True,
        fmit_schedule=ScheduleSummary(**result["fmit_schedule"]) if result.get("fmit_schedule") else None,
        clinic_schedule=ScheduleSummary(**result["clinic_schedule"]) if result.get("clinic_schedule") else None,
        conflicts=[ConflictItem(**c) for c in result.get("conflicts", [])],
        recommendations=[Recommendation(**r) for r in result.get("recommendations", [])],
        summary=ConflictSummary(**result["summary"]) if result.get("summary") else None,
    )


@router.post("/import/analyze-file")
def analyze_single_file(
    file: UploadFile = File(..., description="Schedule Excel file to analyze"),
    file_type: str = Form("auto", description="File type: 'fmit', 'clinic', or 'auto' to detect"),
    specialty_providers: str | None = Form(
        None,
        description="JSON mapping of specialty to providers"
    ),
    db: Session = Depends(get_db),
):
    """
    Quick analysis of a single schedule file.

    Upload an Excel file to detect:
    - Schedule structure (providers, date range, slot types)
    - Alternating week patterns
    - Specialty provider assignments

    Returns parsed schedule data without requiring a second file.
    """
    import json

    from app.services.xlsx_import import ClinicScheduleImporter

    # Read file
    try:
        file_bytes = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file"
        )

    # Validate uploaded file
    try:
        validate_excel_upload(file_bytes, file.filename)
    except FileValidationError as e:
        raise HTTPException(
            status_code=400,
            detail="File validation failed"
        )

    # Parse specialty providers
    specialty_map = None
    if specialty_providers:
        try:
            specialty_map = json.loads(specialty_providers)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid specialty_providers JSON format"
            )

    # Import the file
    importer = ClinicScheduleImporter(db)
    result = importer.import_file(file_bytes=file_bytes)

    if not result.success:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse file: {result.errors}"
        )

    # Check for alternating patterns
    alternating_providers = []
    for provider_name, schedule in result.providers.items():
        if schedule.has_alternating_pattern():
            weeks = schedule.get_fmit_weeks()
            alternating_providers.append({
                "name": provider_name,
                "fmit_weeks": [
                    {"start": w[0].isoformat(), "end": w[1].isoformat()}
                    for w in weeks
                ],
                "pattern": "alternating",
                "recommendation": "Consider consolidating FMIT weeks"
            })

    # Build provider summary
    provider_summary = []
    for provider_name, schedule in result.providers.items():
        fmit_slots = sum(1 for s in schedule.slots.values() if s.slot_type.value == "fmit")
        clinic_slots = sum(1 for s in schedule.slots.values() if s.slot_type.value == "clinic")

        # Check if specialty provider
        specialties = []
        if specialty_map:
            for specialty, providers in specialty_map.items():
                if provider_name in providers:
                    specialties.append(specialty)

        provider_summary.append({
            "name": provider_name,
            "total_slots": len(schedule.slots),
            "fmit_slots": fmit_slots,
            "clinic_slots": clinic_slots,
            "specialties": specialties,
            "fmit_weeks": [
                {"start": w[0].isoformat(), "end": w[1].isoformat()}
                for w in schedule.get_fmit_weeks()
            ],
        })

    return {
        "success": True,
        "file_name": file.filename,
        "date_range": {
            "start": result.date_range[0].isoformat() if result.date_range[0] else None,
            "end": result.date_range[1].isoformat() if result.date_range[1] else None,
        },
        "statistics": {
            "total_providers": len(result.providers),
            "total_slots": result.total_slots,
            "fmit_slots": result.fmit_slots,
            "clinic_slots": result.clinic_slots,
        },
        "providers": provider_summary,
        "alternating_patterns": alternating_providers,
        "warnings": result.warnings,
    }


@router.post("/swaps/find", response_model=SwapFinderResponse)
def find_swap_candidates(
    fmit_file: UploadFile = File(..., description="FMIT rotation schedule Excel file"),
    request_json: str = Form(..., description="SwapFinderRequest as JSON string"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Find swap candidates for an FMIT week.

    Given a faculty member and week they want to offload, this endpoint:
    1. Parses the FMIT schedule from the uploaded Excel file
    2. Cross-references with database absence records (if enabled)
    3. Finds all faculty who could take the target week
    4. Ranks candidates by viability (back-to-back conflicts, external conflicts, flexibility)

    The response includes:
    - Ranked list of swap candidates with details
    - Whether they can do a 1:1 swap or must absorb
    - Any external conflicts (leave, TDY, etc.)
    - Faculty with excessive alternating patterns

    Args:
        fmit_file: Excel file with FMIT rotation schedule
        request_json: SwapFinderRequest serialized as JSON

    Returns:
        SwapFinderResponse with ranked candidates and analysis
    """
    import json

    # Parse request JSON
    try:
        request_data = json.loads(request_json)
        request = SwapFinderRequest(**request_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid request JSON format"
        )

    # Read FMIT file
    try:
        fmit_bytes = fmit_file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file"
        )

    # Validate FMIT file
    try:
        validate_excel_upload(fmit_bytes, fmit_file.filename)
    except FileValidationError as e:
        raise HTTPException(
            status_code=400,
            detail="File validation failed"
        )

    # Build faculty targets dict
    faculty_targets = {
        ft.name: FacultyTarget(
            name=ft.name,
            target_weeks=ft.target_weeks,
            role=ft.role,
            current_weeks=ft.current_weeks,
        )
        for ft in request.faculty_targets
    }

    # Build external conflicts list
    external_conflicts = [
        ExternalConflict(
            faculty=ec.faculty,
            start_date=ec.start_date,
            end_date=ec.end_date,
            conflict_type=ec.conflict_type,
            description=ec.description,
        )
        for ec in request.external_conflicts
    ]

    # Add absence-based conflicts if requested
    if request.include_absence_conflicts:
        try:
            absence_conflicts = load_external_conflicts_from_absences(db)
            external_conflicts.extend(absence_conflicts)
        except Exception as e:
            # Log but don't fail - absence integration is optional
            import logging
            logging.warning(f"Failed to load absence conflicts: {e}")

    try:
        # Create SwapFinder from file
        swap_finder = SwapFinder.from_fmit_file(
            file_bytes=fmit_bytes,
            faculty_targets=faculty_targets if faculty_targets else None,
            external_conflicts=external_conflicts if external_conflicts else None,
            db=db if request.include_absence_conflicts else None,
            include_absence_conflicts=False,  # Already loaded above
            schedule_release_days=request.schedule_release_days,
        )
    except ValueError as e:
        logger.error(f"Invalid swap finder request: {e}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid request parameters"
        )

    # Validate target faculty exists in schedule
    if request.target_faculty not in swap_finder.faculty_weeks:
        available = list(swap_finder.faculty_weeks.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Faculty '{request.target_faculty}' not found in schedule. "
                   f"Available: {', '.join(available[:10])}{'...' if len(available) > 10 else ''}"
        )

    # Find swap candidates
    candidates = swap_finder.find_swap_candidates(
        target_faculty=request.target_faculty,
        target_week=request.target_week,
    )

    # Find alternating patterns
    alternating = swap_finder.find_excessive_alternating(threshold=3)

    # Build response
    candidate_responses = []
    for rank, candidate in enumerate(candidates, 1):
        candidate_responses.append(
            SwapCandidateResponse(
                faculty=candidate.faculty,
                can_take_week=candidate.can_take_week.isoformat(),
                gives_week=candidate.gives_week.isoformat() if candidate.gives_week else None,
                back_to_back_ok=candidate.back_to_back_ok,
                external_conflict=candidate.external_conflict,
                flexibility=candidate.flexibility,
                reason=candidate.reason,
                rank=rank,
            )
        )

    alternating_info = []
    for faculty, cycle_count in alternating:
        weeks = swap_finder.faculty_weeks.get(faculty, [])
        alternating_info.append(
            AlternatingPatternInfo(
                faculty=faculty,
                cycle_count=cycle_count,
                fmit_weeks=[w.isoformat() for w in sorted(weeks)],
                recommendation="Consider consolidating FMIT weeks to reduce family burden",
            )
        )

    viable_count = sum(1 for c in candidates if c.back_to_back_ok and not c.external_conflict)

    return SwapFinderResponse(
        success=True,
        target_faculty=request.target_faculty,
        target_week=request.target_week.isoformat(),
        candidates=candidate_responses,
        total_candidates=len(candidates),
        viable_candidates=viable_count,
        alternating_patterns=alternating_info,
        message=f"Found {viable_count} viable swap candidates out of {len(candidates)} total",
    )
