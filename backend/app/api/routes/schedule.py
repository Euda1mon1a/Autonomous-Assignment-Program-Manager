"""Schedule generation and validation API routes."""

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.file_security import FileValidationError, validate_excel_upload
from app.core.logging import get_logger
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
    SwapCandidateJsonItem,
    SwapCandidateJsonRequest,
    SwapCandidateJsonResponse,
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
from app.schemas.block_import import (
    BlockParseResponse,
    ParsedBlockAssignmentSchema,
    ParsedFMITWeekSchema,
    ResidentRosterItem,
)
from app.services.xlsx_import import (
    ExternalConflict,
    FacultyTarget,
    SwapFinder,
    analyze_schedule_conflicts,
    load_external_conflicts_from_absences,
    parse_block_schedule,
    parse_fmit_attending,
)

# Import observability metrics (optional - graceful degradation)
try:
    from app.core.observability import metrics as obs_metrics
except ImportError:
    obs_metrics = None

router = APIRouter()
logger = get_logger(__name__)


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
        "the cached result will be returned.",
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
        "rotation_template_ids": (
            [str(x) for x in request.rotation_template_ids]
            if request.rotation_template_ids
            else None
        ),
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
                logger.info(
                    f"Returning cached response for idempotency key: {idempotency_key[:8]}..."
                )
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
                logger.info(
                    f"Returning cached error for idempotency key: {idempotency_key[:8]}..."
                )
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
            nf_pc_audit=result.get("nf_pc_audit"),
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
                obs_metrics.record_schedule_success(
                    algorithm, result.get("total_assigned", 0)
                )
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
            obs_metrics.record_schedule_success(
                algorithm, result.get("total_assigned", 0)
            )
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
        logger.error("Error generating schedule: {}", repr(e), exc_info=True)
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
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

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
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

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

        schedule_by_date[date_str][assignment.block.time_of_day].append(
            {
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
            }
        )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "schedule": schedule_by_date,
        "total_assignments": len(assignments),
    }


@router.post("/import/analyze", response_model=ImportAnalysisResponse)
def analyze_imported_schedules(
    fmit_file: UploadFile = File(..., description="FMIT rotation schedule Excel file"),
    clinic_file: UploadFile | None = File(
        None, description="Clinic schedule Excel file (optional)"
    ),
    specialty_providers: str | None = Form(
        None,
        description='JSON mapping of specialty to providers, e.g., {"Sports Medicine": ["FAC-SPORTS"]}',
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
                status_code=400, detail="Invalid specialty_providers JSON format"
            )

    # Read file contents
    try:
        fmit_bytes = fmit_file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    # Validate FMIT file
    try:
        validate_excel_upload(fmit_bytes, fmit_file.filename, fmit_file.content_type)
    except FileValidationError:
        raise HTTPException(status_code=400, detail="File validation failed")

    clinic_bytes = None
    if clinic_file:
        try:
            clinic_bytes = clinic_file.file.read()
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to read uploaded file")

        # Validate clinic file
        try:
            validate_excel_upload(
                clinic_bytes, clinic_file.filename, clinic_file.content_type
            )
        except FileValidationError:
            raise HTTPException(status_code=400, detail="File validation failed")

    # Run analysis
    result = analyze_schedule_conflicts(
        fmit_bytes=fmit_bytes,
        clinic_bytes=clinic_bytes,
        specialty_providers=specialty_map,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=422, detail=result.get("error", "Analysis failed")
        )

    # Build response
    return ImportAnalysisResponse(
        success=True,
        fmit_schedule=(
            ScheduleSummary(**result["fmit_schedule"])
            if result.get("fmit_schedule")
            else None
        ),
        clinic_schedule=(
            ScheduleSummary(**result["clinic_schedule"])
            if result.get("clinic_schedule")
            else None
        ),
        conflicts=[ConflictItem(**c) for c in result.get("conflicts", [])],
        recommendations=[
            Recommendation(**r) for r in result.get("recommendations", [])
        ],
        summary=ConflictSummary(**result["summary"]) if result.get("summary") else None,
    )


@router.post("/import/analyze-file")
def analyze_single_file(
    file: UploadFile = File(..., description="Schedule Excel file to analyze"),
    file_type: str = Form(
        "auto", description="File type: 'fmit', 'clinic', or 'auto' to detect"
    ),
    specialty_providers: str | None = Form(
        None, description="JSON mapping of specialty to providers"
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
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    # Validate uploaded file
    try:
        validate_excel_upload(file_bytes, file.filename, file.content_type)
    except FileValidationError:
        raise HTTPException(status_code=400, detail="File validation failed")

    # Parse specialty providers
    specialty_map = None
    if specialty_providers:
        try:
            specialty_map = json.loads(specialty_providers)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid specialty_providers JSON format"
            )

    # Import the file
    importer = ClinicScheduleImporter(db)
    result = importer.import_file(file_bytes=file_bytes)

    if not result.success:
        raise HTTPException(
            status_code=422, detail=f"Failed to parse file: {result.errors}"
        )

    # Check for alternating patterns
    alternating_providers = []
    for provider_name, schedule in result.providers.items():
        if schedule.has_alternating_pattern():
            weeks = schedule.get_fmit_weeks()
            alternating_providers.append(
                {
                    "name": provider_name,
                    "fmit_weeks": [
                        {"start": w[0].isoformat(), "end": w[1].isoformat()}
                        for w in weeks
                    ],
                    "pattern": "alternating",
                    "recommendation": "Consider consolidating FMIT weeks",
                }
            )

    # Build provider summary
    provider_summary = []
    for provider_name, schedule in result.providers.items():
        fmit_slots = sum(
            1 for s in schedule.slots.values() if s.slot_type.value == "fmit"
        )
        clinic_slots = sum(
            1 for s in schedule.slots.values() if s.slot_type.value == "clinic"
        )

        # Check if specialty provider
        specialties = []
        if specialty_map:
            for specialty, providers in specialty_map.items():
                if provider_name in providers:
                    specialties.append(specialty)

        provider_summary.append(
            {
                "name": provider_name,
                "total_slots": len(schedule.slots),
                "fmit_slots": fmit_slots,
                "clinic_slots": clinic_slots,
                "specialties": specialties,
                "fmit_weeks": [
                    {"start": w[0].isoformat(), "end": w[1].isoformat()}
                    for w in schedule.get_fmit_weeks()
                ],
            }
        )

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


@router.post("/import/block", response_model=BlockParseResponse)
def parse_block_schedule_endpoint(
    file: UploadFile = File(..., description="Excel schedule file"),
    block_number: int = Form(
        ..., description="Block number to parse (1-13)", ge=1, le=13
    ),
    known_people: str | None = Form(
        None, description="JSON array of known person names for fuzzy matching"
    ),
    include_fmit: bool = Form(True, description="Include FMIT attending schedule"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Parse a specific block schedule from an Excel file.

    Uses anchor-based fuzzy-tolerant parsing to extract:
    - Resident roster grouped by template (R1, R2, R3)
    - FMIT attending schedule (weekly faculty assignments)
    - Daily assignments with AM/PM slots

    Handles human-edited spreadsheet chaos:
    - Column shifts from copy/paste
    - Merged cells
    - Name typos (fuzzy matching with known_people list)

    Args:
        file: Excel file with block schedule
        block_number: Block to parse (1-13)
        known_people: Optional JSON array of known names for better fuzzy matching
        include_fmit: Whether to include FMIT schedule (default: True)

    Returns:
        BlockParseResponse with roster, FMIT schedule, and parsing warnings
    """
    import json as json_module
    import os
    import tempfile

    # Read and validate file
    try:
        file_bytes = file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    try:
        validate_excel_upload(file_bytes, file.filename, file.content_type)
    except FileValidationError:
        raise HTTPException(status_code=400, detail="File validation failed")

    # Parse known people if provided
    people_list = None
    if known_people:
        try:
            people_list = json_module.loads(known_people)
            if not isinstance(people_list, list):
                raise ValueError("known_people must be a JSON array")
        except (json_module.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid known_people format: {e}"
            )

    # Save to temp file (openpyxl needs file path)
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        result = parse_block_schedule(
            filepath=tmp_path,
            block_number=block_number,
            known_people=people_list,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)

    # Parse FMIT if requested
    fmit_schedule = []
    if include_fmit:
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                all_fmit = parse_fmit_attending(filepath=tmp_path)
                fmit_schedule = [
                    ParsedFMITWeekSchema(
                        block_number=f.block_number,
                        week_number=f.week_number,
                        start_date=f.start_date.isoformat() if f.start_date else None,
                        end_date=f.end_date.isoformat() if f.end_date else None,
                        faculty_name=f.faculty_name,
                        is_holiday_call=f.is_holiday_call,
                    )
                    for f in all_fmit
                    if f.block_number == block_number
                ]
            finally:
                os.unlink(tmp_path)
        except Exception:
            pass  # FMIT sheet not found, that's OK

    # Convert to response schema
    return BlockParseResponse(
        success=len(result.errors) == 0,
        block_number=result.block_number,
        start_date=result.start_date.isoformat() if result.start_date else None,
        end_date=result.end_date.isoformat() if result.end_date else None,
        residents=[ResidentRosterItem(**r) for r in result.residents],
        residents_by_template={
            template: [ResidentRosterItem(**r) for r in residents]
            for template, residents in result.get_residents_by_template().items()
        },
        fmit_schedule=fmit_schedule,
        assignments=[
            ParsedBlockAssignmentSchema(
                person_name=a.person_name,
                date=a.date.isoformat(),
                template=a.template,
                role=a.role,
                slot_am=a.slot_am,
                slot_pm=a.slot_pm,
                row_idx=a.row_idx,
                confidence=a.confidence,
            )
            for a in result.assignments
        ],
        warnings=result.warnings,
        errors=result.errors,
        total_residents=len(result.residents),
        total_assignments=len(result.assignments),
    )


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
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid request JSON format")

    # Read FMIT file
    try:
        fmit_bytes = fmit_file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    # Validate FMIT file
    try:
        validate_excel_upload(fmit_bytes, fmit_file.filename, fmit_file.content_type)
    except FileValidationError:
        raise HTTPException(status_code=400, detail="File validation failed")

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
            logger.warning(f"Failed to load absence conflicts: {e}")

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
        raise HTTPException(status_code=422, detail="Invalid request parameters")

    # Validate target faculty exists in schedule
    if request.target_faculty not in swap_finder.faculty_weeks:
        available = list(swap_finder.faculty_weeks.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Faculty '{request.target_faculty}' not found in schedule. "
            f"Available: {', '.join(available[:10])}{'...' if len(available) > 10 else ''}",
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
                gives_week=(
                    candidate.gives_week.isoformat() if candidate.gives_week else None
                ),
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

    viable_count = sum(
        1 for c in candidates if c.back_to_back_ok and not c.external_conflict
    )

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


@router.post("/swaps/candidates", response_model=SwapCandidateJsonResponse)
def find_swap_candidates_json(
    request: SwapCandidateJsonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Find swap candidates using JSON input (no file upload required).

    This endpoint queries the database directly to find potential swap partners
    for a given person and optionally a specific assignment or block.

    Unlike /swaps/find which requires an Excel file, this endpoint works with
    database assignments and is suitable for MCP tool integration.

    Args:
        request: JSON request with person_id and optional assignment/block

    Returns:
        SwapCandidateJsonResponse with ranked candidates
    """
    from datetime import datetime
    from uuid import UUID

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate

    # Validate person exists
    try:
        person_uuid = UUID(request.person_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person_id format")

    requester = db.query(Person).filter(Person.id == person_uuid).first()
    if not requester:
        raise HTTPException(
            status_code=404, detail=f"Person {request.person_id} not found"
        )

    # Get the target assignment if specified
    target_assignment = None
    target_block = None

    if request.assignment_id:
        try:
            assignment_uuid = UUID(request.assignment_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid assignment_id format")

        target_assignment = (
            db.query(Assignment).filter(Assignment.id == assignment_uuid).first()
        )
        if not target_assignment:
            raise HTTPException(
                status_code=404, detail=f"Assignment {request.assignment_id} not found"
            )
        target_block = (
            db.query(Block).filter(Block.id == target_assignment.block_id).first()
        )

    elif request.block_id:
        try:
            block_uuid = UUID(request.block_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid block_id format")

        target_block = db.query(Block).filter(Block.id == block_uuid).first()
        if not target_block:
            raise HTTPException(
                status_code=404, detail=f"Block {request.block_id} not found"
            )

        # Find the requester's assignment for this block
        target_assignment = (
            db.query(Assignment)
            .filter(
                Assignment.person_id == person_uuid,
                Assignment.block_id == block_uuid,
            )
            .first()
        )

    # Get future assignments for the requester if no specific target
    if not target_block:
        future_assignments = (
            db.query(Assignment, Block)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == person_uuid,
                Block.start_date >= datetime.utcnow().date(),
            )
            .order_by(Block.start_date)
            .limit(5)
            .all()
        )

        if not future_assignments:
            return SwapCandidateJsonResponse(
                success=True,
                requester_person_id=request.person_id,
                requester_name=requester.name,
                original_assignment_id=None,
                candidates=[],
                total_candidates=0,
                top_candidate_id=None,
                message="No future assignments found for this person",
            )

        # Use the first future assignment as target
        target_assignment, target_block = future_assignments[0]

    # Find potential swap candidates
    # Look for other people with assignments on nearby blocks
    candidates = []

    # Get other people's assignments on the same block or nearby
    other_assignments = (
        db.query(Assignment, Block, Person, RotationTemplate)
        .join(Block, Assignment.block_id == Block.id)
        .join(Person, Assignment.person_id == Person.id)
        .outerjoin(
            RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
        )
        .filter(
            Assignment.person_id != person_uuid,
            Person.type == requester.type,  # Same type (faculty/resident)
            Block.start_date >= datetime.utcnow().date(),
        )
        .order_by(Block.start_date)
        .limit(100)  # Get a pool of candidates
        .all()
    )

    for assignment, block, person, rotation in other_assignments:
        # Calculate a simple match score based on various factors
        score = 0.5  # Base score

        # Boost if same block (direct swap possible)
        if target_block and block.id == target_block.id:
            score += 0.3

        # Boost if same rotation type
        if (
            target_assignment
            and target_assignment.rotation_template_id
            and rotation
            and rotation.id == target_assignment.rotation_template_id
        ):
            score += 0.1

        # Penalize if dates are far apart
        if target_block:
            days_apart = abs((block.start_date - target_block.start_date).days)
            if days_apart <= 7:
                score += 0.1
            elif days_apart <= 28:
                pass  # neutral
            else:
                score -= 0.2

        score = max(0.0, min(1.0, score))

        # Determine approval likelihood based on score
        if score >= 0.8:
            likelihood = "high"
        elif score >= 0.5:
            likelihood = "medium"
        else:
            likelihood = "low"

        candidates.append(
            SwapCandidateJsonItem(
                candidate_person_id=str(person.id),
                candidate_name=person.name,
                candidate_role=person.type.capitalize() if person.type else "Unknown",
                assignment_id=str(assignment.id),
                block_date=block.start_date.isoformat(),
                block_session=block.session or "AM",
                match_score=score,
                rotation_name=rotation.name if rotation else None,
                compatibility_factors={
                    "same_type": person.type == requester.type,
                    "same_block": target_block and block.id == target_block.id,
                },
                mutual_benefit=target_block and block.id == target_block.id,
                approval_likelihood=likelihood,
            )
        )

    # Sort by match score
    candidates.sort(key=lambda c: c.match_score, reverse=True)

    # Limit to max_candidates
    candidates = candidates[: request.max_candidates]

    top_candidate_id = candidates[0].candidate_person_id if candidates else None

    return SwapCandidateJsonResponse(
        success=True,
        requester_person_id=request.person_id,
        requester_name=requester.name,
        original_assignment_id=str(target_assignment.id) if target_assignment else None,
        candidates=candidates,
        total_candidates=len(candidates),
        top_candidate_id=top_candidate_id,
        message=f"Found {len(candidates)} swap candidates",
    )


# ============================================================================
# Faculty Outpatient Assignment Generation
# ============================================================================


@router.post("/faculty-outpatient/generate")
def generate_faculty_outpatient(
    block_number: int,
    regenerate: bool = True,
    include_clinic: bool = True,
    include_supervision: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate faculty PRIMARY clinic and SUPERVISION assignments for a block.

    This generates:
    1. Faculty clinic sessions - Based on role limits (PD=0, APD=2, Core=4/week)
    2. Faculty supervision - ACGME-compliant supervision of resident assignments

    Args:
        block_number: Block number (1-13 for academic year)
        regenerate: If True, clear existing faculty outpatient assignments first
        include_clinic: Generate faculty primary clinic assignments
        include_supervision: Generate faculty supervision assignments

    Returns:
        Generation result with assignment counts and faculty summaries

    Note:
        This endpoint modifies the database. Ensure backup before use.
        Use the safe-schedule-generation skill pre-flight checklist.
    """
    from app.services.faculty_outpatient_service import FacultyOutpatientAssignmentService

    logger.info(
        f"Generating faculty outpatient assignments for block {block_number}",
        extra={
            "user": current_user.username,
            "block_number": block_number,
            "regenerate": regenerate,
        },
    )

    try:
        service = FacultyOutpatientAssignmentService(db)
        result = service.generate_faculty_outpatient_assignments(
            block_number=block_number,
            regenerate=regenerate,
            include_clinic=include_clinic,
            include_supervision=include_supervision,
        )

        if not result.success:
            logger.warning(f"Faculty outpatient generation failed: {result.message}")
            raise HTTPException(status_code=400, detail=result.message)

        logger.info(
            f"Faculty outpatient generation complete: "
            f"{result.total_clinic_assignments} clinic + "
            f"{result.total_supervision_assignments} supervision assignments"
        )

        return {
            "success": result.success,
            "message": result.message,
            "block_number": result.block_number,
            "block_start": str(result.block_start),
            "block_end": str(result.block_end),
            "total_clinic_assignments": result.total_clinic_assignments,
            "total_supervision_assignments": result.total_supervision_assignments,
            "cleared_count": result.cleared_count,
            "faculty_summaries": [
                {
                    "faculty_id": str(s.faculty_id),
                    "faculty_name": s.faculty_name,
                    "faculty_role": s.faculty_role,
                    "clinic_sessions": s.clinic_sessions,
                    "supervision_sessions": s.supervision_sessions,
                    "total_sessions": s.total_sessions,
                }
                for s in result.faculty_summaries
            ],
            "warnings": result.warnings,
            "errors": result.errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Use repr to avoid format string issues with loguru
        logger.error("Faculty outpatient generation error: {}", repr(e), exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Faculty outpatient generation failed: {repr(e)}",
        )
