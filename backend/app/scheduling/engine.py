"""
Scheduling Engine for Residency Program.

Implements the core scheduling algorithms:
- Phase 0: Absence loading -> Availability matrix
- Phase 1: Smart pairing -> Greedy initialization
- Phase 2: Resident association -> Constraint-based assignment
- Phase 3: Faculty assignment -> Supervision ratio enforcement
- Phase 7: Validation -> ACGME compliance checking

Algorithms:
- greedy: Fast heuristic, assigns hardest blocks first to least-loaded residents
- cp_sat: Constraint programming solver using Google OR-Tools, guarantees ACGME compliance
- pulp: Linear programming solver using PuLP for large-scale optimization
- hybrid: Combines CP-SAT and PuLP for best results

The engine uses a modular constraint system (constraints.py) and pluggable solvers (solvers.py)
for flexible, maintainable scheduling.
"""

import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ActivityNotFoundError
from app.core.logging import get_logger
from app.schemas.schedule import (
    NFPCAudit,
    NFPCAuditViolation,
    ValidationResult,
    Violation,
)

logger = get_logger(__name__)

from app.models.absence import Absence
from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.person import FacultyRole, Person
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.models.schedule_run import ScheduleRun
from app.resilience.service import ResilienceConfig, ResilienceService
from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)
from app.scheduling.pre_solver_validator import PreSolverValidator
from app.scheduling.solvers import (
    SolverFactory,
    SolverResult,
)
from app.scheduling.validator import ACGMEValidator
from app.services.sync_preload_service import SyncPreloadService
from app.scheduling.activity_solver import CPSATActivitySolver
from app.services.schedule_draft_service import ScheduleDraftService
from app.models.schedule_draft import DraftSourceType
from app.utils.academic_blocks import get_block_number_for_date


class SchedulingEngine:
    """
    Clean, maintainable scheduling engine for residency programs.

    Features:
    - Multiple solver backends (greedy, CP-SAT, PuLP, hybrid)
    - Modular constraint system
    - ACGME compliance validation
    - Faculty supervision assignment

    Algorithm Flow:
    1. Ensure blocks exist for date range
    2. Build availability matrix from absences
    3. Create scheduling context with all data
    4. Run selected solver with constraints
    5. Assign faculty supervision
    6. Validate and save results
    """

    # Available algorithms
    ALGORITHMS = ["greedy", "cp_sat", "pulp", "hybrid"]

    def __init__(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        constraint_manager: ConstraintManager | None = None,
        resilience_config: ResilienceConfig | None = None,
    ) -> None:
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.availability_matrix: dict = {}
        self.assignments: list[Assignment] = []
        self.validator = ACGMEValidator(db)
        self.constraint_manager = (
            constraint_manager or ConstraintManager.create_default()
        )

        # Initialize resilience service for health monitoring
        self.resilience = ResilienceService(
            db=db,
            config=resilience_config or ResilienceConfig(),
        )

    def generate(
        self,
        pgy_levels: list[int] | None = None,
        rotation_template_ids: list[UUID] | None = None,
        algorithm: str = "greedy",
        timeout_seconds: float = 60.0,
        check_resilience: bool = True,
        preserve_fmit: bool = True,
        preserve_resident_inpatient: bool = True,
        preserve_absence: bool = True,
        expand_block_assignments: bool = True,
        block_number: int | None = None,
        academic_year: int | None = None,
        create_draft: bool = False,
        created_by_id: UUID | None = None,
        validate_pcat_do: bool = True,
    ) -> dict:
        """
        Generate a complete schedule.

        Args:
            pgy_levels: Filter residents by PGY level (None = all)
            rotation_template_ids: Filter templates by ID (None = all)
            algorithm: Solver algorithm ('greedy', 'cp_sat', 'pulp', 'hybrid')
            timeout_seconds: Maximum solver runtime
            check_resilience: Run resilience health check before/after generation
            preserve_fmit: Preserve existing FMIT faculty assignments (default True)
            preserve_resident_inpatient: Preserve existing resident inpatient assignments
                                        (FMIT, NF, NICU) - prevents over-assignment bug
            preserve_absence: Preserve existing absence assignments (Leave, Weekend)
                             so solver skips people with scheduled time off
            expand_block_assignments: Deprecated (expansion pipeline removed).
                                     Kept for API compatibility; ignored.
            block_number: Academic block number (0-13), used for preloads and
                         activity solver defaults.
            academic_year: Academic year (e.g., 2025 for AY 2025-2026), used for
                          preloads and activity solver defaults.
            create_draft: If True, stage assignments in a draft instead of committing
                         directly to live assignments. Draft must be published separately.
            created_by_id: UUID of user creating the schedule (for audit trail).
            validate_pcat_do: Run PCAT/DO integrity check after sync (default True).
                             Set to False once pipeline is proven stable.

        Returns:
            Dictionary with status, assignments, validation results, and resilience info.
            If create_draft=True, includes 'draft_id' for the created draft.
        """
        start_time = time.time()

        # Validate algorithm
        if algorithm not in self.ALGORITHMS:
            logger.warning(f"Unknown algorithm '{algorithm}', using canonical CP-SAT")
            algorithm = "cp_sat"

        # Canonical solver path: CP-SAT only
        if algorithm != "cp_sat":
            logger.info(
                f"Overriding algorithm '{algorithm}' -> 'cp_sat' (canonical pathway)"
            )
            algorithm = "cp_sat"

        # Issue #3: Transaction boundaries - wrap everything in a single transaction
        # Create an "in_progress" run record first
        run = self._create_initial_run(algorithm)

        # Expansion pipeline removed; expand_block_assignments is deprecated.
        if expand_block_assignments is False:
            logger.warning(
                "expand_block_assignments is deprecated and ignored "
                "(CP-SAT is canonical)."
            )

        # Pre-generation resilience check
        # Store as instance attribute for _populate_resilience_data to access
        self._pre_health_report = None
        if check_resilience:
            self._pre_health_report = self._check_pre_generation_resilience()

        try:
            # Step 1: Ensure blocks exist (but don't commit yet)
            blocks = self._ensure_blocks_exist(commit=False)

            # Step 1.5a: Load FMIT faculty assignments if preserving them
            fmit_assignments = []
            preserve_ids: set[UUID] = set()
            if preserve_fmit:
                fmit_assignments = self._load_fmit_assignments()
                preserve_ids = {cast(UUID, a.id) for a in fmit_assignments}
                if fmit_assignments:
                    logger.info(
                        f"Preserving {len(fmit_assignments)} FMIT faculty assignments"
                    )

            # Step 1.5b: Load resident inpatient assignments if preserving them
            resident_inpatient_assignments = []
            if preserve_resident_inpatient:
                resident_inpatient_assignments = (
                    self._load_resident_inpatient_assignments()
                )
                preserve_ids.update(
                    {cast(UUID, a.id) for a in resident_inpatient_assignments}
                )
                if resident_inpatient_assignments:
                    logger.info(
                        f"Preserving {len(resident_inpatient_assignments)} "
                        "resident inpatient assignments (FMIT/NF/NICU)"
                    )

            # Step 1.5c: Load absence assignments if preserving them
            absence_assignments = []
            if preserve_absence:
                absence_assignments = self._load_absence_assignments()
                preserve_ids.update({cast(UUID, a.id) for a in absence_assignments})
                if absence_assignments:
                    logger.info(
                        f"Preserving {len(absence_assignments)} "
                        "absence assignments (Leave/Weekend)"
                    )

            # Step 1.5d: Load off-site assignments (Hilo, Kapiolani, Okinawa)
            offsite_assignments = self._load_offsite_assignments()
            preserve_ids.update({cast(UUID, a.id) for a in offsite_assignments})
            if offsite_assignments:
                logger.info(
                    f"Preserving {len(offsite_assignments)} "
                    "off-site assignments (Hilo/Kapiolani/Okinawa)"
                )

            # Step 1.5e: Load recovery assignments (Post-Call)
            # Note: PC is also enforced by NightFloatPostCallConstraint
            recovery_assignments = self._load_recovery_assignments()
            preserve_ids.update({cast(UUID, a.id) for a in recovery_assignments})
            if recovery_assignments:
                logger.info(
                    f"Preserving {len(recovery_assignments)} "
                    "recovery assignments (Post-Call)"
                )

            # Step 1.5f: Load education assignments (FMO, GME, Lectures)
            education_assignments = self._load_education_assignments()
            preserve_ids.update({cast(UUID, a.id) for a in education_assignments})
            if education_assignments:
                logger.info(
                    f"Preserving {len(education_assignments)} "
                    "education assignments (FMO/GME/Lectures)"
                )

            # =================================================================
            # CORRECTED ORDER OF OPERATIONS (per TAMC skill)
            # =================================================================
            # The dependency chain is:
            #   Call → PCAT (DO paired for rest) → AT Coverage → Resident Clinic Load → Faculty Admin
            #
            # PCAT (Post-Call Attending Time) counts toward AT coverage.
            # Residents must know PCAT availability BEFORE scheduling clinic.
            # Faculty admin fills AFTER knowing resident clinic demand.
            # =================================================================

            # Step 1.5g: Infer block/year if not provided
            if block_number is None or academic_year is None:
                # Try to infer from date range
                block_number, _ = get_block_number_for_date(self.start_date)
                # Academic year is the year of July 1 that starts the AY
                if self.start_date.month >= 7:
                    academic_year = self.start_date.year
                else:
                    academic_year = self.start_date.year - 1
                logger.info(
                    f"Inferred block {block_number} AY {academic_year} from dates"
                )

            # Step 2: Load absences and build availability matrix (moved earlier)
            self._build_availability_matrix()

            # Step 3: Get residents, faculty, and templates (moved earlier)
            residents = self._get_residents(pgy_levels, block_number, academic_year)
            templates = self._get_rotation_templates(rotation_template_ids)
            faculty = self._get_faculty()

            # NOTE: Context is built in Step 4 (unchanged location)
            # CP-SAT solving happens in Step 5
            # Preloads now skip stale faculty call PCAT/DO

            # Step 3.5: Load NON-CALL preloads (FMIT, absences, C-I, NF, aSM)
            # SKIP faculty call PCAT/DO - those will come from NEW call in Step 6.5
            # This prevents loading stale PCAT/DO from old CallAssignment records
            # SKIP in draft mode - preloads write to live half_day_assignments
            if (
                block_number is not None
                and academic_year is not None
                and not create_draft
            ):
                preload_service = SyncPreloadService(self.db)
                preload_count = preload_service.load_all_preloads(
                    block_number, academic_year, skip_faculty_call=True
                )
                logger.info(f"Loaded {preload_count} non-call preload assignments")
            elif create_draft:
                logger.info(
                    "Skipping preload sync in draft mode (would modify live data)"
                )

            # NOTE: Activity solver runs AFTER call assignments are created.
            # This ensures:
            # 1. PCAT/DO from NEW call is locked before activity solver runs (PCAT drives AT coverage)
            # 2. Activity solver knows PCAT coverage for AT ratio calculations

            # NOTE: Deletion deferred until after successful solve (see Step 5.5)
            # This prevents data loss if the solver fails

            if not residents:
                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()
                return {
                    "status": "failed",
                    "message": "No residents found matching criteria",
                    "total_assigned": 0,
                    "total_blocks": len(blocks),
                    "validation": self._empty_validation(),
                    "run_id": run.id,
                }

            # Step 4: Create scheduling context (with resilience data if available)
            # Combine all preserved assignments to pass to context as immutable
            preserved_assignments = (
                fmit_assignments
                + resident_inpatient_assignments
                + absence_assignments
                + offsite_assignments
                + recovery_assignments
                + education_assignments
            )
            context = self._build_context(
                residents,
                faculty,
                blocks,
                templates,
                include_resilience=check_resilience,
                existing_assignments=preserved_assignments,
            )

            # Half-day scheduling uses many residents per block; disable one-person cap.
            if any(getattr(block, "time_of_day", None) for block in blocks):
                self.constraint_manager.disable("OnePersonPerBlock")
                logger.info("Disabled OnePersonPerBlock constraint for half-day blocks")
                has_time_off_templates = any(
                    (getattr(t, "rotation_type", "") or "").lower()
                    in {"off", "absence", "recovery"}
                    for t in templates
                )
                if not has_time_off_templates:
                    self.constraint_manager.disable("1in7Rule")
                    self.constraint_manager.disable("80HourRule")
                    logger.info(
                        "Disabled 1in7Rule and 80HourRule (no time-off templates in solver context)"
                    )

                # Half-day outpatient solver cannot satisfy clinic-wide caps
                # or Wednesday-only rules when all residents are scheduled.
                self.constraint_manager.disable("MaxPhysiciansInClinic")
                self.constraint_manager.disable("WednesdayAMInternOnly")
                self.constraint_manager.disable("WednesdayPMSingleFaculty")
                self.constraint_manager.disable("InvertedWednesday")
                self.constraint_manager.disable("ProtectedSlot")
                logger.info(
                    "Disabled MaxPhysiciansInClinic, Wednesday temporal, and ProtectedSlot constraints for half-day blocks"
                )

            # Step 4.5: Pre-solver validation
            # Check constraint saturation before invoking expensive solver
            pre_validator = PreSolverValidator()
            validation_result = pre_validator.validate_saturation(context)

            if not validation_result.feasible:
                # Problem is obviously infeasible - fail fast
                logger.error(
                    f"Pre-solver validation failed: {len(validation_result.issues)} issues detected"
                )
                for issue in validation_result.issues:
                    logger.error(f"  - {issue}")
                for recommendation in validation_result.recommendations:
                    logger.info(f"  Recommendation: {recommendation}")
                self._log_constraint_summary()
                self._log_context_summary(context)
                self._dump_failure_snapshot(
                    context,
                    run_id=run.id,
                    stage="pre_solver_validation",
                    solver_status="pre_solver_validation_failed",
                    pre_solver_validation={
                        "feasible": validation_result.feasible,
                        "issues": validation_result.issues,
                        "recommendations": validation_result.recommendations,
                        "statistics": validation_result.statistics,
                    },
                )

                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()

                return {
                    "status": "failed",
                    "message": f"Pre-solver validation failed: {len(validation_result.issues)} issues",
                    "total_assigned": 0,
                    "total_blocks": len(blocks),
                    "validation": self._empty_validation(),
                    "run_id": run.id,
                    "pre_solver_validation": {
                        "feasible": False,
                        "issues": validation_result.issues,
                        "recommendations": validation_result.recommendations,
                        "statistics": validation_result.statistics,
                    },
                }

            # Log pre-solver validation results
            logger.info(
                f"Pre-solver validation passed: "
                f"complexity={validation_result.statistics.get('complexity_level', 'UNKNOWN')}, "
                f"{validation_result.statistics.get('num_variables', 0):,} variables, "
                f"estimated runtime: {validation_result.statistics.get('estimated_runtime', 'unknown')}"
            )
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Pre-solver warning: {warning}")

            # Step 5: Run solver (CP-SAT full outpatient assignments)
            logger.info("Running CP-SAT solver for outpatient assignments + call")
            solver_result = self._run_solver("cp_sat", context, timeout_seconds)
            if not solver_result.success:
                logger.error(f"CP-SAT solver failed: {solver_result.solver_status}")
                if solver_result.solver_status.upper() == "INFEASIBLE":
                    logger.error(
                        "CP-SAT reported INFEASIBLE; schedule may be impossible with current hard constraints."
                    )
                self._log_constraint_summary()
                self._log_context_summary(context)
                self._dump_failure_snapshot(
                    context,
                    run_id=run.id,
                    stage="solver",
                    solver_status=solver_result.solver_status,
                    solver_stats=solver_result.statistics,
                )
                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()
                return {
                    "status": "failed",
                    "message": f"CP-SAT solver failed: {solver_result.solver_status}",
                    "total_assigned": 0,
                    "total_blocks": len(blocks),
                    "validation": self._empty_validation(),
                    "run_id": run.id,
                }
            logger.info(
                f"CP-SAT solver generated {len(solver_result.assignments)} "
                f"rotation assignments and {len(solver_result.call_assignments)} call assignments"
            )

            # Step 5.5: Delete existing assignments (except preserved ones)
            # This happens AFTER successful solve to prevent data loss on solver failure
            # SKIP in draft mode - draft staging should not modify live schedule
            if not create_draft:
                self._delete_existing_assignments(preserve_ids)
                self._delete_existing_half_day_assignments()

            # Step 6: Convert solver results to assignments
            locked_slots = self._get_blocking_half_day_slots()
            blocks_by_id = {b.id: b for b in blocks}
            self._create_assignments_from_result(
                solver_result,
                residents,
                templates,
                cast(UUID, run.id),
                existing_assignments=preserved_assignments,
                locked_half_day_slots=locked_slots,
                blocks_by_id=blocks_by_id,
            )
            if not create_draft:
                for assignment in self.assignments:
                    self.db.add(assignment)
                self.db.flush()
                self._persist_solver_assignments_to_half_day(self.assignments, blocks)
                self._ensure_faculty_half_day_slots(faculty, blocks)

            # Step 6.5: Create call assignments from solver results
            # Creates CallAssignment records for overnight call (Sun-Thurs)
            # SKIP in draft mode - draft staging should not modify live CallAssignment table
            call_assignments = []
            if not create_draft:
                call_assignments = self._create_call_assignments_from_result(
                    solver_result, context
                )

                # Step 6.6: Sync PCAT/DO to half_day_assignments based on NEW call
                # Creates PCAT (AM) and DO (PM) for day after call, locked as preload.
                # NOW we have baseline AT coverage for ratio calculations.
                if call_assignments:
                    self._sync_call_pcat_do_to_half_day(call_assignments)

                    # Step 6.6.1: Validate PCAT/DO integrity (catches sync bugs)
                    # This runs automatically after PCAT/DO sync to ensure correctness.
                    # Can be disabled via validate_pcat_do=False once pipeline is stable.
                    if validate_pcat_do:
                        pcat_do_issues = self._validate_pcat_do_integrity(
                            call_assignments
                        )
                        if pcat_do_issues:
                            logger.error(
                                f"PCAT/DO integrity check FAILED: "
                                f"{len(pcat_do_issues)} issues detected"
                            )
                            for issue in pcat_do_issues:
                                logger.error(f"  - {issue}")

                            # Fail generation - PCAT is critical for AT coverage (DO is post-call rest)
                            # ROLLBACK all schedule changes to avoid partial state
                            # (CallAssignments, HalfDayAssignments written so far)
                            # Note: run record was committed in _create_initial_run,
                            # so it survives rollback - we just need to update it.
                            run_id = run.id  # Save before rollback
                            elapsed = time.time() - start_time
                            self.db.rollback()

                            # Re-fetch run record (detached after rollback) and update status
                            # The run was committed separately in _create_initial_run
                            existing_run = self.db.get(ScheduleRun, run_id)
                            if existing_run:
                                self._update_run_status(
                                    existing_run, "failed", 0, 0, elapsed
                                )
                                self.db.commit()

                            return {
                                "status": "failed",
                                "message": f"PCAT/DO integrity check failed: {len(pcat_do_issues)} issues (rolled back)",
                                "total_assigned": 0,
                                "total_blocks": len(blocks),
                                "validation": self._empty_validation(),
                                "run_id": run_id,
                                "pcat_do_issues": pcat_do_issues,
                            }
                        else:
                            logger.info(
                                f"PCAT/DO integrity check passed "
                                f"({len(call_assignments)} calls verified)"
                            )
            elif solver_result.call_assignments:
                logger.info(
                    f"Skipping {len(solver_result.call_assignments)} call assignments "
                    f"in draft mode (would modify live CallAssignment table)"
                )

            # =================================================================
            # CORRECTED: Activity solver runs AFTER call
            # =================================================================
            # NOW that PCAT is locked, the activity solver knows AT coverage.
            # Residents can be scheduled knowing which slots have supervision.

            # Step 6.7: Run activity solver to assign activities to half-day slots
            # This assigns activities to resident + faculty slots that aren't locked by preload.
            # NOW runs AFTER PCAT is created, so AT coverage is known.
            # SKIP in draft mode - activity solver writes to live half_day_assignments
            if (
                block_number is not None
                and academic_year is not None
                and not create_draft
            ):
                activity_solver = CPSATActivitySolver(
                    self.db,
                    timeout_seconds=min(timeout_seconds, 30.0),  # Cap at 30s
                )
                activity_result = activity_solver.solve(block_number, academic_year)
                if activity_result.get("success"):
                    logger.info(
                        f"Activity solver assigned {activity_result.get('assignments_updated', 0)} "
                        f"activities ({activity_result.get('status', 'unknown')})"
                    )
                else:
                    logger.warning(
                        f"Activity solver failed: {activity_result.get('message', 'unknown error')}"
                    )
            elif create_draft and (
                block_number is not None and academic_year is not None
            ):
                logger.info(
                    "Skipping activity solver in draft mode (would modify live data)"
                )

            # Step 7: Assign faculty supervision (legacy mode only)
            logger.info("Skipping legacy faculty supervision (CP-SAT output only)")

            # Step 8: Handle draft vs live assignment persistence
            draft_id = None
            if create_draft:
                # Create draft instead of committing to live assignments
                # Use sync methods to avoid event loop issues in async contexts
                draft_service = ScheduleDraftService(self.db)

                # Create the draft (sync version)
                draft_result = draft_service.create_draft_sync(
                    source_type=DraftSourceType.SOLVER,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    block_number=block_number,
                    created_by_id=created_by_id,
                    schedule_run_id=cast(UUID, run.id),
                    notes=f"Generated by {algorithm} solver",
                )

                if draft_result.success and draft_result.draft_id:
                    draft_id = draft_result.draft_id
                    logger.info(f"Created draft {draft_id} for staging")

                    # Add solver assignments to draft (sync version)
                    draft_service.add_solver_assignments_to_draft_sync(
                        draft_id=draft_id,
                        assignments=self.assignments,
                        existing_ids=preserve_ids,
                    )
                else:
                    logger.warning(
                        f"Failed to create draft: {draft_result.message}. "
                        "Falling back to live commit."
                    )
                    # Fall back to live commit
                    for assignment in self.assignments:
                        self.db.add(assignment)
                    self.db.flush()
            else:
                # Assignments already added/flushed in Step 6 for live mode.
                # Step 8.5: Flush to make assignments visible to validator
                self.db.flush()

            # Step 9: Validate
            validation = self.validator.validate_all(self.start_date, self.end_date)

            # Step 9.1: Add validation flags to draft if in draft mode
            if create_draft and draft_id and validation.violations:
                draft_service = ScheduleDraftService(self.db)
                draft_service.add_validation_flags_to_draft_sync(
                    draft_id=draft_id,
                    validation_result=validation,
                )

            # Step 9.5: Run NF -> PC audit and surface violations
            nf_pc_audit = self._audit_nf_pc_allocations()
            if not nf_pc_audit.get("compliant", True):
                violations = list(validation.violations)
                for nf_violation in nf_pc_audit.get("violations", []):
                    violations.append(
                        Violation(
                            type="NF_PC_COVERAGE",
                            severity="HIGH",
                            person_id=(
                                UUID(nf_violation["person_id"])
                                if nf_violation.get("person_id")
                                else None
                            ),
                            person_name=nf_violation.get("person_name"),
                            message=(
                                "Missing Post-Call coverage after Night Float day"
                            ),
                            details={
                                "nf_date": nf_violation.get("nf_date"),
                                "pc_required_date": nf_violation.get(
                                    "pc_required_date"
                                ),
                                "missing_am_pc": nf_violation.get("missing_am_pc"),
                                "missing_pm_pc": nf_violation.get("missing_pm_pc"),
                            },
                        )
                    )
                validation = ValidationResult(
                    valid=False,
                    total_violations=len(violations),
                    violations=violations,
                    coverage_rate=validation.coverage_rate,
                    statistics=validation.statistics,
                )

            nf_pc_audit_model = None
            if nf_pc_audit:
                audit_violations = []
                for v in nf_pc_audit.get("violations", []):
                    person_value = v.get("person_id")
                    person_uuid = None
                    if isinstance(person_value, UUID):
                        person_uuid = person_value
                    elif person_value:
                        try:
                            person_uuid = UUID(person_value)
                        except (TypeError, ValueError):
                            person_uuid = None

                    audit_violations.append(
                        NFPCAuditViolation(
                            person_id=person_uuid,
                            person_name=v.get("person_name"),
                            nf_date=(
                                date.fromisoformat(v["nf_date"])
                                if isinstance(v.get("nf_date"), str)
                                else v.get("nf_date")
                            ),
                            pc_required_date=(
                                date.fromisoformat(v["pc_required_date"])
                                if isinstance(v.get("pc_required_date"), str)
                                else v.get("pc_required_date")
                            ),
                            missing_am_pc=v.get("missing_am_pc", False),
                            missing_pm_pc=v.get("missing_pm_pc", False),
                        )
                    )

                nf_pc_audit_model = NFPCAudit(
                    compliant=nf_pc_audit.get("compliant", True),
                    total_nf_transitions=nf_pc_audit.get("total_nf_transitions", 0),
                    violations=audit_violations,
                    message=nf_pc_audit.get("message"),
                )

            # Step 10: Update run record with results
            runtime = time.time() - start_time
            self._update_run_with_results(
                run, algorithm, validation, runtime, solver_result
            )

            # Issue #3: Single atomic commit - all or nothing
            # In draft mode, assignments are already committed to draft tables
            # Only commit run record and preserved assignments
            if create_draft and draft_id:
                # Commit just the run record update (no live assignments)
                logger.info(
                    f"Draft mode: Assignments staged in draft {draft_id}. "
                    "Publish draft to commit to live assignments."
                )
            self.db.commit()
            self.db.refresh(run)

            # Post-generation resilience check
            post_health_report = None
            resilience_warnings = []
            if check_resilience:
                post_health_report = self._check_post_generation_resilience(
                    faculty, blocks, self.assignments
                )
                resilience_warnings = self._get_resilience_warnings(post_health_report)

            # Build result message
            if create_draft and draft_id:
                result_message = (
                    f"Generated {len(self.assignments)} assignments using {algorithm}. "
                    f"Staged in draft {draft_id}."
                )
                result_status = "draft"
            else:
                result_message = (
                    f"Generated {len(self.assignments)} assignments using {algorithm}"
                )
                result_status = "success" if validation.valid else "partial"

            return {
                "status": result_status,
                "message": result_message,
                "total_assigned": len(self.assignments),
                "total_blocks": len(blocks),
                "validation": validation,
                "run_id": run.id,
                "draft_id": draft_id,  # None if not in draft mode
                "solver_stats": solver_result.statistics,
                "nf_pc_audit": nf_pc_audit_model,
                "resilience": {
                    "pre_generation_status": (
                        self._pre_health_report.overall_status
                        if self._pre_health_report
                        else None
                    ),
                    "post_generation_status": (
                        post_health_report.overall_status
                        if post_health_report
                        else None
                    ),
                    "utilization_rate": (
                        post_health_report.utilization.utilization_rate
                        if post_health_report
                        else None
                    ),
                    "n1_compliant": (
                        post_health_report.n1_pass if post_health_report else None
                    ),
                    "n2_compliant": (
                        post_health_report.n2_pass if post_health_report else None
                    ),
                    "warnings": resilience_warnings,
                    "immediate_actions": (
                        post_health_report.immediate_actions
                        if post_health_report
                        else []
                    ),
                    # New: Include resilience constraint activity
                    "resilience_constraints_active": (
                        context.has_resilience_data() if context else False
                    ),
                    "hub_faculty_count": len(context.hub_scores) if context else 0,
                },
            }

        except Exception as e:
            # Issue #3: Rollback on any failure to prevent partial persistence
            logger.error(f"Schedule generation failed: {e}")
            self.db.rollback()

            # Try to update run status to failed (in a new transaction)
            try:
                self.db.refresh(run)
                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()
            except Exception:
                self.db.rollback()

            raise

    def _build_context(
        self,
        residents: list[Person],
        faculty: list[Person],
        blocks: list[Block],
        templates: list[RotationTemplate],
        include_resilience: bool = True,
        existing_assignments: list[Assignment] | None = None,
    ) -> SchedulingContext:
        """
        Build scheduling context from database objects.

        Args:
            residents: List of resident Person objects
            faculty: List of faculty Person objects
            blocks: List of Block objects for the schedule period
            templates: List of RotationTemplate objects
            include_resilience: Whether to populate resilience data
            existing_assignments: Immutable assignments (inpatient, FMIT, absences)
                                 that solver must not overwrite

        Returns:
            SchedulingContext with all data needed for constraint evaluation
        """
        # Get call-eligible faculty (excludes adjuncts)
        call_eligible = self._get_call_eligible_faculty(faculty)

        # Load activities and activity requirements for templates
        activities = self._load_activities()
        template_ids = [cast(UUID, t.id) for t in templates]
        activity_requirements = self._load_activity_requirements(template_ids)
        protected_patterns = self._load_protected_patterns(template_ids)

        # Build base context
        locked_blocks = self._get_locked_block_pairs(blocks)
        context = SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=templates,
            availability=self.availability_matrix,
            start_date=self.start_date,
            end_date=self.end_date,
            existing_assignments=existing_assignments or [],
            locked_blocks=locked_blocks,
            call_eligible_faculty=call_eligible,
            activities=activities,
            activity_requirements=activity_requirements,
            protected_patterns=protected_patterns,
        )

        # Enable activity requirement constraint if we have data
        if activity_requirements and self.constraint_manager:
            self.constraint_manager.enable("ActivityRequirement")
            logger.debug(
                f"Loaded {len(activity_requirements)} activity requirements for "
                f"{len(template_ids)} templates"
            )

        # Enable protected slot constraint if we have protected patterns
        if protected_patterns and self.constraint_manager:
            self.constraint_manager.enable("ProtectedSlot")
            total_patterns = sum(len(p) for p in protected_patterns.values())
            logger.debug(
                f"Loaded {total_patterns} protected patterns for "
                f"{len(protected_patterns)} templates"
            )

        # Populate resilience data if available and requested
        if include_resilience and self.resilience:
            self._populate_resilience_data(context, faculty, blocks)

        return context

    def _populate_resilience_data(
        self,
        context: SchedulingContext,
        faculty: list[Person],
        blocks: list[Block],
    ) -> None:
        """
        Populate resilience data in the scheduling context.

        Tier 1 (Critical):
        - Hub scores from hub analysis
        - Current utilization from resilience service

        Tier 2 (Strategic):
        - N-1 vulnerable faculty from contingency analysis
        - Preference trails from stigmergy
        - Zone assignments from blast radius isolation

        The data enables resilience-aware constraints to function.
        Constraints are auto-enabled when their data is available.
        """
        try:
            # =================================================================
            # TIER 1: Critical resilience data
            # =================================================================

            # Get hub scores
            hub_scores = self._get_hub_scores(faculty)
            if hub_scores:
                context.hub_scores = hub_scores
                logger.debug(f"Loaded hub scores for {len(hub_scores)} faculty")

                # Enable hub protection constraint if we have data
                if self.constraint_manager:
                    self.constraint_manager.enable("HubProtection")

            # Get current utilization from pre-generation check
            if hasattr(self, "_pre_health_report") and self._pre_health_report:
                context.current_utilization = (
                    self._pre_health_report.utilization.utilization_rate
                )
                context.target_utilization = self.resilience.config.max_utilization

                # Enable utilization buffer constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("UtilizationBuffer")

            # =================================================================
            # TIER 2: Strategic resilience data
            # =================================================================

            # Get N-1 vulnerable faculty from contingency analysis
            n1_vulnerable = self._get_n1_vulnerable_faculty(faculty, blocks)
            if n1_vulnerable:
                context.n1_vulnerable_faculty = n1_vulnerable
                logger.debug(f"Identified {len(n1_vulnerable)} N-1 vulnerable faculty")

            # Always enable N1 constraint - it can work without pre-identified faculty
            # by analyzing the solution for single points of failure
            if self.constraint_manager:
                self.constraint_manager.enable("N1Vulnerability")

            # Get preference trails from stigmergy
            preference_trails = self._get_preference_trails(faculty)
            if preference_trails:
                context.preference_trails = preference_trails
                logger.debug(
                    f"Loaded preference trails for {len(preference_trails)} faculty"
                )

                # Enable preference trail constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("PreferenceTrail")

            # Get zone assignments from blast radius isolation
            zone_data = self._get_zone_assignments(faculty, blocks)
            if zone_data:
                context.zone_assignments = zone_data.get("faculty_zones", {})
                context.block_zones = zone_data.get("block_zones", {})
                logger.debug(
                    f"Loaded zone data: {len(context.zone_assignments)} faculty, "
                    f"{len(context.block_zones)} blocks"
                )

                # Enable zone boundary constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("ZoneBoundary")

        except Exception as e:
            logger.warning(f"Failed to populate resilience data: {e}")
            # Continue without resilience data - constraints will be no-ops

    def _get_hub_scores(self, faculty: list[Person]) -> dict[UUID, float]:
        """
        Get hub vulnerability scores for faculty from network analysis.

        Hub scores are computed by the ResilienceService using network centrality
        metrics (degree, betweenness, closeness) to identify critical "hub"
        faculty whose loss would significantly impact the system.

        Network Theory Context:
            Scale-free networks (common in organizations) are:
            - Robust to random failures
            - Extremely vulnerable to targeted hub removal
            - Hub faculty cover unique services or specialties
            - Over-assigning hubs increases systemic risk

        Args:
            faculty: List of faculty Person objects

        Returns:
            dict[UUID, float]: Mapping of faculty_id to hub score (0.0-1.0)
                - 0.0-0.4: Low hub score, not critical
                - 0.4-0.6: Moderate hub, should be somewhat protected
                - 0.6-1.0: Critical hub, strongly protect from over-assignment
                Returns empty dict if hub analysis data unavailable

        Example:
            >>> hub_scores = self._get_hub_scores(faculty)
            >>> critical_hubs = {fid: score for fid, score in hub_scores.items() if score > 0.6}
            >>> print(f"Found {len(critical_hubs)} critical hub faculty")

        Note:
            Called during context building if resilience integration is enabled.
            Scores are cached in the scheduling context for constraint evaluation.
        """
        hub_scores = {}

        try:
            # Check if we have cached hub analysis results
            if hasattr(self.resilience, "hub_analyzer"):
                # Get latest centrality data
                for fac in faculty:
                    centrality = self.resilience.hub_analyzer.calculate_centrality(
                        cast(UUID, fac.id)
                    )
                    if centrality:
                        hub_scores[cast(UUID, fac.id)] = centrality.composite_score
        except Exception as e:
            logger.debug(f"Could not get hub scores: {e}")

        return hub_scores

    def _get_n1_vulnerable_faculty(
        self,
        faculty: list[Person],
        blocks: list[Block],
    ) -> set[UUID]:
        """
        Identify faculty whose loss would cause N-1 failure.

        These are single points of failure - the schedule cannot
        survive if they become unavailable.
        """
        n1_vulnerable = set()

        try:
            # Use contingency analyzer if available
            if hasattr(self.resilience, "contingency"):
                # This would need existing assignments to analyze
                # For now, return empty - will be populated after solving
                pass
        except Exception as e:
            logger.debug(f"Could not get N-1 vulnerable faculty: {e}")

        return n1_vulnerable

    def _get_preference_trails(
        self, faculty: list[Person]
    ) -> dict[UUID, dict[str, float]]:
        """
        Get preference trail data from stigmergy system.

        Returns dict of faculty_id -> {slot_type -> strength}.
        Used for soft preference optimization.
        """
        preference_trails = {}

        try:
            if hasattr(self.resilience, "stigmergy"):
                for fac in faculty:
                    prefs = self.resilience.get_faculty_preferences(
                        cast(UUID, fac.id), min_strength=0.3
                    )
                    if prefs:
                        faculty_prefs = {}
                        for trail in prefs:
                            if trail.slot_type:
                                faculty_prefs[trail.slot_type] = trail.strength
                        if faculty_prefs:
                            preference_trails[cast(UUID, fac.id)] = faculty_prefs
        except Exception as e:
            logger.debug(f"Could not get preference trails: {e}")

        return preference_trails

    def _get_zone_assignments(
        self,
        faculty: list[Person],
        blocks: list[Block],
    ) -> dict | None:
        """
        Get zone assignment data from blast radius isolation system.

        Returns dict with:
        - faculty_zones: {faculty_id -> zone_id}
        - block_zones: {block_id -> zone_id}

        Used to enforce zone boundaries and contain failures.
        """
        zone_data = {
            "faculty_zones": {},
            "block_zones": {},
        }

        try:
            if hasattr(self.resilience, "blast_radius"):
                blast_radius = self.resilience.blast_radius

                # Get faculty zone assignments
                for fac in faculty:
                    zone = blast_radius.get_faculty_zone(cast(UUID, fac.id))  # type: ignore[attr-defined]
                    if zone:
                        zone_data["faculty_zones"][cast(UUID, fac.id)] = zone.id

                # Get block zone assignments (from rotation template or service type)
                for block in blocks:
                    # Blocks may be associated with zones through their rotation template
                    # or through explicit zone assignment
                    zone = blast_radius.get_block_zone(cast(UUID, block.id))  # type: ignore[attr-defined]
                    if zone:
                        zone_data["block_zones"][cast(UUID, block.id)] = zone.id

        except Exception as e:
            logger.debug(f"Could not get zone assignments: {e}")

        # Only return if we have meaningful data
        if zone_data["faculty_zones"] or zone_data["block_zones"]:
            return zone_data
        return None

    def _run_solver(
        self,
        algorithm: str,
        context: SchedulingContext,
        timeout_seconds: float,
        constraint_manager: ConstraintManager | None = None,
    ) -> SolverResult:
        """Run the selected solver algorithm."""
        try:
            if algorithm not in self.ALGORITHMS:
                logger.warning(
                    f"Unknown solver '{algorithm}', forcing canonical CP-SAT"
                )
                algorithm = "cp_sat"
            if algorithm != "cp_sat":
                logger.info(
                    f"Overriding solver '{algorithm}' -> 'cp_sat' (canonical pathway)"
                )
                algorithm = "cp_sat"

            solver = SolverFactory.create(
                algorithm,
                constraint_manager=constraint_manager or self.constraint_manager,
                timeout_seconds=timeout_seconds,
            )
            # Pass existing_assignments from context as immutable constraints
            existing_assign = (
                context.existing_assignments if context.existing_assignments else []
            )
            return solver.solve(context, existing_assign)
        except Exception as e:
            logger.error(f"Solver error: {e}")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status=str(e),
            )

    def _create_assignments_from_result(
        self,
        result: SolverResult,
        residents: list[Person],
        templates: list[RotationTemplate],
        run_id: UUID,
        existing_assignments: list[Assignment] | None = None,
        locked_half_day_slots: set[tuple[UUID, date, str]] | None = None,
        blocks_by_id: dict[UUID, Block] | None = None,
    ) -> None:
        """Convert solver results to Assignment objects.

        Filters out any solver-generated assignments that conflict with
        immutable existing assignments (inpatient, FMIT, absences).
        """
        # Build set of (person_id, block_id) pairs that are already assigned
        occupied_slots: set[tuple[UUID, UUID]] = set()
        if existing_assignments:
            for a in existing_assignments:
                occupied_slots.add((cast(UUID, a.person_id), cast(UUID, a.block_id)))

        skipped = 0
        locked_skipped = 0
        for person_id, block_id, template_id in result.assignments:
            # Skip if this person+block is already occupied by an immutable assignment
            if (person_id, block_id) in occupied_slots:
                skipped += 1
                continue
            if locked_half_day_slots and blocks_by_id:
                block = blocks_by_id.get(cast(UUID, block_id))
                if block:
                    key = (cast(UUID, person_id), block.date, block.time_of_day)
                    if key in locked_half_day_slots:
                        locked_skipped += 1
                        continue

            assignment = Assignment(
                block_id=block_id,
                person_id=person_id,
                rotation_template_id=template_id,
                role="primary",
                schedule_run_id=run_id,
            )
            self.assignments.append(assignment)

        if skipped > 0:
            logger.info(
                f"Skipped {skipped} solver assignments that conflicted with "
                "immutable existing assignments"
            )
        if locked_skipped > 0:
            logger.info(
                f"Skipped {locked_skipped} solver assignments due to "
                "locked half-day slots (preload/manual)"
            )

    def _create_call_assignments_from_result(
        self,
        result: SolverResult,
        context: SchedulingContext,
    ) -> list[CallAssignment]:
        """
        Convert solver call results to CallAssignment objects.

        Creates CallAssignment records from the solver's call_assignments output.
        Each assignment maps a faculty member to a specific date for overnight call.

        Clears existing call assignments for the date range before inserting new ones
        to avoid unique constraint violations on regeneration.

        Args:
            result: SolverResult containing call_assignments list
            context: SchedulingContext with block lookup data

        Returns:
            List of CallAssignment objects created
        """
        call_assignments: list[CallAssignment] = []

        if not result.call_assignments:
            return call_assignments

        # Clear existing call assignments for this date range to avoid conflicts
        # This allows regeneration without unique constraint violations
        deleted_count = (
            self.db.query(CallAssignment)
            .filter(
                CallAssignment.date >= self.start_date,
                CallAssignment.date <= self.end_date,
            )
            .delete(synchronize_session=False)
        )
        if deleted_count:
            logger.info(
                f"Cleared {deleted_count} existing call assignments for "
                f"{self.start_date} to {self.end_date}"
            )

        # Build block lookup for date extraction
        block_by_id = {b.id: b for b in context.blocks}

        for person_id, block_id, call_type in result.call_assignments:
            block = block_by_id.get(block_id)
            if not block:
                logger.warning(f"Block {block_id} not found for call assignment")
                continue

            # Map solver call types to database-allowed values
            # Constraint allows: 'overnight', 'weekend', 'backup'
            # Solver uses: 'overnight' (generic)
            is_sunday = block.date.weekday() == 6
            if call_type == "overnight":
                # Weekend (Sunday) vs overnight (Mon-Thu)
                mapped_call_type = "weekend" if is_sunday else "overnight"
            else:
                mapped_call_type = call_type

            call_assignment = CallAssignment(
                date=block.date,
                person_id=person_id,
                call_type=mapped_call_type,
                is_weekend=is_sunday,
                is_holiday=False,  # Could be enhanced to check holiday calendar
            )
            self.db.add(call_assignment)
            call_assignments.append(call_assignment)

        if call_assignments:
            logger.info(f"Created {len(call_assignments)} overnight call assignments")

        return call_assignments

    def _sync_call_pcat_do_to_half_day(
        self,
        call_assignments: list[CallAssignment],
    ) -> int:
        """
        Sync PCAT/DO slots in half_day_assignments to match new CallAssignment records.

        The preload service runs BEFORE the solver generates new call assignments.
        This creates a divergence: half_day_assignments has PCAT/DO from OLD call records,
        but CallAssignment now has NEW call records from the solver.

        This method runs AFTER call assignments are created to sync PCAT/DO:
        - For each new CallAssignment, create PCAT (AM) and DO (PM) for the next day
        - Updates or inserts with source='preload' to lock these slots
        - Skips if person is on FMIT the next day

        Args:
            call_assignments: List of newly created CallAssignment records

        Returns:
            Number of PCAT/DO slots created/updated
        """
        from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
        from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
        from app.models.activity import Activity
        from sqlalchemy import select

        if not call_assignments:
            return 0

        # Get PCAT and DO activity IDs
        # Note: Activity codes are lowercase in database (pcat, do)
        pcat_activity = (
            self.db.execute(select(Activity).where(Activity.code == "pcat"))
            .scalars()
            .first()
        )
        do_activity = (
            self.db.execute(select(Activity).where(Activity.code == "do"))
            .scalars()
            .first()
        )

        if not pcat_activity or not do_activity:
            logger.warning("Missing PCAT or DO activity, skipping PCAT/DO sync")
            return 0

        count = 0
        for call in call_assignments:
            next_day = call.date + timedelta(days=1)

            # Note: Don't skip cross-block PCAT/DO - we use actual dates and preload
            # source is locked, so next block generation won't overwrite it

            # Check if person is on FMIT next day (no PCAT/DO for FMIT)
            fmit_check = (
                self.db.execute(
                    select(InpatientPreload).where(
                        InpatientPreload.person_id == call.person_id,
                        InpatientPreload.rotation_type == InpatientRotationType.FMIT,
                        InpatientPreload.start_date <= next_day,
                        InpatientPreload.end_date >= next_day,
                    )
                )
                .scalars()
                .first()
            )

            if fmit_check:
                continue  # FMIT faculty don't get PCAT/DO

            # Create/update PCAT (AM) and DO (PM) for next day
            for time_of_day, activity in [("AM", pcat_activity), ("PM", do_activity)]:
                existing = (
                    self.db.execute(
                        select(HalfDayAssignment).where(
                            HalfDayAssignment.person_id == call.person_id,
                            HalfDayAssignment.date == next_day,
                            HalfDayAssignment.time_of_day == time_of_day,
                        )
                    )
                    .scalars()
                    .first()
                )

                if existing:
                    # Update if lower priority source
                    if existing.source in (
                        AssignmentSource.TEMPLATE.value,
                        AssignmentSource.SOLVER.value,
                    ):
                        existing.activity_id = cast(UUID, activity.id)
                        existing.source = AssignmentSource.PRELOAD.value
                        count += 1
                else:
                    # Insert new
                    self.db.add(
                        HalfDayAssignment(
                            person_id=call.person_id,
                            date=next_day,
                            time_of_day=time_of_day,
                            activity_id=activity.id,
                            source=AssignmentSource.PRELOAD.value,
                        )
                    )
                    count += 1

        if count:
            self.db.flush()
            logger.info(f"Synced {count} PCAT/DO slots to match new call assignments")

        return count

    def _validate_pcat_do_integrity(
        self,
        call_assignments: list,
    ) -> list[str]:
        """
        Validate PCAT/DO were created for each call assignment.

        This is a post-generation integrity check that runs after PCAT/DO sync.
        It catches bugs where PCAT/DO creation silently fails.

        Args:
            call_assignments: List of CallAssignment objects to validate

        Returns:
            List of issues (empty = valid). Each issue is a string describing
            the missing PCAT or DO.

        Note:
            This validation can be disabled via validate_pcat_do=False in generate()
            once the pipeline is proven stable.
        """
        from app.models.half_day_assignment import HalfDayAssignment
        from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
        from app.models.activity import Activity
        from sqlalchemy import select

        if not call_assignments:
            return []

        issues: list[str] = []

        # Get PCAT and DO activity IDs
        pcat_activity = (
            self.db.execute(select(Activity).where(Activity.code == "pcat"))
            .scalars()
            .first()
        )
        do_activity = (
            self.db.execute(select(Activity).where(Activity.code == "do"))
            .scalars()
            .first()
        )

        if not pcat_activity or not do_activity:
            issues.append("PCAT or DO activity not found in database")
            return issues

        for call in call_assignments:
            next_day = call.date + timedelta(days=1)

            # Note: Don't skip cross-block validation - PCAT/DO should exist even if
            # next_day is in the next block (created during this block's generation)

            # Check if person is on FMIT next day (no PCAT/DO for FMIT)
            fmit_check = (
                self.db.execute(
                    select(InpatientPreload).where(
                        InpatientPreload.person_id == call.person_id,
                        InpatientPreload.rotation_type == InpatientRotationType.FMIT,
                        InpatientPreload.start_date <= next_day,
                        InpatientPreload.end_date >= next_day,
                    )
                )
                .scalars()
                .first()
            )

            if fmit_check:
                continue  # FMIT faculty don't get PCAT/DO - this is correct

            # Check PCAT (AM) - may be overwritten by another preload (holiday, leave, etc.)
            pcat = (
                self.db.execute(
                    select(HalfDayAssignment).where(
                        HalfDayAssignment.person_id == call.person_id,
                        HalfDayAssignment.date == next_day,
                        HalfDayAssignment.time_of_day == "AM",
                        HalfDayAssignment.activity_id == pcat_activity.id,
                    )
                )
                .scalars()
                .first()
            )

            if not pcat:
                # Check if there's another preload that took precedence (e.g., holiday, leave)
                other_preload_am = (
                    self.db.execute(
                        select(HalfDayAssignment).where(
                            HalfDayAssignment.person_id == call.person_id,
                            HalfDayAssignment.date == next_day,
                            HalfDayAssignment.time_of_day == "AM",
                            HalfDayAssignment.source == "preload",
                        )
                    )
                    .scalars()
                    .first()
                )
                if not other_preload_am:
                    issues.append(
                        f"Missing PCAT: call {call.date} -> expected PCAT on {next_day} AM"
                    )

            # Check DO (PM) - may be overwritten by another preload
            do = (
                self.db.execute(
                    select(HalfDayAssignment).where(
                        HalfDayAssignment.person_id == call.person_id,
                        HalfDayAssignment.date == next_day,
                        HalfDayAssignment.time_of_day == "PM",
                        HalfDayAssignment.activity_id == do_activity.id,
                    )
                )
                .scalars()
                .first()
            )

            if not do:
                # Check if there's another preload that took precedence (e.g., call)
                other_preload = (
                    self.db.execute(
                        select(HalfDayAssignment).where(
                            HalfDayAssignment.person_id == call.person_id,
                            HalfDayAssignment.date == next_day,
                            HalfDayAssignment.time_of_day == "PM",
                            HalfDayAssignment.source == "preload",
                        )
                    )
                    .scalars()
                    .first()
                )
                if not other_preload:
                    issues.append(
                        f"Missing DO: call {call.date} -> expected DO on {next_day} PM"
                    )

        return issues

    def _ensure_blocks_exist(self, commit: bool = True) -> list[Block]:
        """Ensure half-day blocks exist for the date range.

        Block numbers use Thursday-Wednesday alignment:
        - Block 0: July 1 through day before first Thursday (orientation)
        - Blocks 1-12: 28 days each, Thursday start, Wednesday end
        - Block 13: Thursday start, June 30 end (variable length)
        """
        blocks = []
        current_date = self.start_date

        while current_date <= self.end_date:
            # Use Thursday-Wednesday aligned block number calculation
            block_number, _ = get_block_number_for_date(current_date)

            for time_of_day in ["AM", "PM"]:
                existing = (
                    self.db.query(Block)
                    .filter(
                        Block.date == current_date,
                        Block.time_of_day == time_of_day,
                    )
                    .first()
                )

                if existing:
                    blocks.append(existing)
                else:
                    block = Block(
                        date=current_date,
                        time_of_day=time_of_day,
                        block_number=block_number,
                        is_weekend=(current_date.weekday() >= 5),
                    )
                    self.db.add(block)
                    blocks.append(block)

            current_date += timedelta(days=1)

        if commit:
            self.db.commit()
        else:
            self.db.flush()  # Make blocks available in the session without committing

        return blocks

    def _build_availability_matrix(self) -> None:
        """
        Build availability matrix from absences in the database.

        This method queries all absences that overlap with the scheduling period
        and constructs a matrix indicating whether each person is available for
        each block. This is a critical preprocessing step that enables fast
        constraint evaluation during solving.

        Matrix structure:
            {
                person_id (UUID): {
                    block_id (UUID): {
                        'available' (bool): True if person can be assigned,
                        'replacement' (str): Activity displayed in calendar (e.g., "TDY"),
                        'partial_absence' (bool): True if person has non-blocking absence
                    }
                }
            }

        Absence Classification Logic:
            - **Blocking absences** (deployment, TDY, extended medical):
              - available = False
              - Person CANNOT be assigned to this block
              - Enforced by AvailabilityConstraint (hard constraint)

            - **Partial absences** (vacation day, conference, appointment):
              - available = True
              - Person CAN be assigned (they can work partial day)
              - partial_absence = True (tracked for informational purposes)
              - Calendar shows replacement activity but assignment is allowed

        Performance:
            - Pre-computes all availability checks: O(people × blocks × absences)
            - Enables O(1) lookup during constraint evaluation
            - Reduces solver time by avoiding database queries during solving

        Example:
            >>> # After building availability matrix:
            >>> is_available = self.availability_matrix[resident_id][block_id]["available"]
            >>> if is_available:
            ...     # Can assign resident to this block
        """
        # Get all people (no eager loading needed - only accessing person.id)
        people = self.db.query(Person).all()

        # Get all blocks in range
        blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            )
            .all()
        )

        # Get absences in range
        absences = (
            self.db.query(Absence)
            .filter(
                Absence.start_date <= self.end_date,
                Absence.end_date >= self.start_date,
            )
            .all()
        )

        # Build matrix
        for person in people:
            self.availability_matrix[person.id] = {}

            for block in blocks:
                # Default: available
                is_available = True
                replacement_activity = None
                has_partial_absence = False

                # Check absences
                for absence in absences:
                    if (
                        absence.person_id == person.id
                        and absence.start_date <= block.date <= absence.end_date
                    ):
                        # Use the should_block_assignment property to determine
                        if absence.should_block_assignment:
                            # Blocking absence - person cannot be assigned
                            is_available = False
                            replacement_activity = absence.replacement_activity
                            break
                        else:
                            # Partial absence - person can be assigned but we track it
                            has_partial_absence = True
                            replacement_activity = absence.replacement_activity
                            # Don't break - keep checking for blocking absences

                self.availability_matrix[person.id][block.id] = {
                    "available": is_available,
                    "replacement": replacement_activity,
                    "partial_absence": has_partial_absence,
                }

    def _get_residents(
        self,
        pgy_levels: list[int] | None = None,
        block_number: int | None = None,
        academic_year: int | None = None,
    ) -> list[Person]:
        """Get residents, optionally filtered by PGY level."""
        query = self.db.query(Person).filter(Person.type == "resident")

        if pgy_levels:
            query = query.filter(Person.pgy_level.in_(pgy_levels))

        if block_number is not None and academic_year is not None:
            resident_ids = (
                self.db.query(BlockAssignment.resident_id)
                .filter(
                    BlockAssignment.block_number == block_number,
                    BlockAssignment.academic_year == academic_year,
                )
                .distinct()
                .all()
            )
            resident_ids = [row[0] for row in resident_ids]
            if not resident_ids:
                logger.error(
                    "No BlockAssignments found for block "
                    f"{block_number} AY {academic_year}; refusing to schedule all residents"
                )
                return []
            query = query.filter(Person.id.in_(resident_ids))

        return query.order_by(Person.pgy_level, Person.name).all()

    def _get_faculty(self) -> list[Person]:
        """Get all faculty members."""
        return self.db.query(Person).filter(Person.type == "faculty").all()

    def _get_call_eligible_faculty(self, faculty: list[Person]) -> list[Person]:
        """
        Get faculty eligible for solver-generated overnight call.

        Adjunct faculty are excluded because they are manually added to call
        rather than auto-scheduled by the solver.

        Args:
            faculty: List of all faculty members

        Returns:
            List of faculty eligible for overnight call (excludes adjuncts)
        """
        return [f for f in faculty if f.faculty_role != FacultyRole.ADJUNCT.value]

    def _load_fmit_assignments(self) -> list[Assignment]:
        """
        Load FMIT assignments (faculty on inpatient) for the date range.

        FMIT (Faculty Managing Inpatient Teaching) assignments are pre-selected
        by faculty at the beginning of the academic year. These assignments
        should be preserved during schedule generation rather than deleted
        and regenerated.

        Detection logic:
            - person.type == 'faculty'
            - template.rotation_type == 'inpatient'

        Returns:
            List of Assignment objects for faculty on FMIT rotations
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(Person, Assignment.person_id == Person.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                Person.type == "faculty",
                RotationTemplate.rotation_type == "inpatient",
            )
            .all()
        )

    def _load_resident_inpatient_assignments(self) -> list[Assignment]:
        """
        Load resident inpatient assignments (FMIT, NF, NICU) for the date range.

        These assignments are sourced from the block schedule and should be
        loaded BEFORE solver runs as fixed constraints. This prevents the
        NF over-assignment bug where solver assigns Night Float to everyone.

        Detection logic:
            - person.type == 'resident'
            - template.rotation_type == 'inpatient'
            - Includes: FMIT AM/PM, Night Float AM/PM, NICU

        Business Rules:
            - FMIT: 1 per PGY level per block (PGY1=Wed AM, PGY2=Tue PM, PGY3=Mon PM)
            - NF: Only 1 resident at a time
            - NICU: Clinic Friday PM (always)
            - PC: Thursday after NF ends (auto-generated, not loaded here)

        Returns:
            List of Assignment objects for residents on inpatient rotations
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(Person, Assignment.person_id == Person.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                Person.type == "resident",
                RotationTemplate.rotation_type == "inpatient",
            )
            .all()
        )

    def _load_absence_assignments(self) -> list[Assignment]:
        """
        Load absence assignments (Leave, Weekend, TDY blocks) for the date range.

        These assignments represent scheduled time off and should be preserved
        so the solver skips assigning new work to people with absences.

        Detection logic:
            - template.rotation_type == 'absence'
            - Includes: Leave AM/PM, Weekend AM/PM

        Business Rules:
            - People with absence assignments should not receive new assignments
            - Absences are visible on schedule (not hidden)
            - Similar to inpatient pre-loading pattern

        Returns:
            List of Assignment objects for absence-type rotations
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                RotationTemplate.rotation_type == "absence",
            )
            .all()
        )

    def _load_offsite_assignments(self) -> list[Assignment]:
        """
        Load off-site assignments (Hilo, Kapiolani, Okinawa) for the date range.

        These assignments represent rotations at different hospitals/locations
        and should be preserved so the solver doesn't double-book people.

        Detection logic:
            - template.rotation_type == 'off'
            - Includes: Hilo, Kapiolani, Okinawa, OFF AM/PM

        Business Rules:
            - People on off-site rotations are physically elsewhere
            - Cannot be assigned to main site during off-site rotation
            - Similar to inpatient pre-loading pattern

        Returns:
            List of Assignment objects for off-site rotations
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                RotationTemplate.rotation_type == "off",
            )
            .all()
        )

    def _load_recovery_assignments(self) -> list[Assignment]:
        """
        Load recovery/post-call assignments for the date range.

        Post-call recovery days follow Night Float or FMIT for both
        residents and faculty. These are mandatory rest periods.

        Detection logic:
            - template.rotation_type == 'recovery'
            - Includes: Post-Call Recovery (PCR)

        Business Rules:
            - Post-call is mandatory after night duty (ACGME)
            - Applies to both residents and faculty after FMIT
            - Cannot be scheduled for clinical duties during recovery

        Returns:
            List of Assignment objects for recovery periods
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                RotationTemplate.rotation_type == "recovery",
            )
            .all()
        )

    def _load_education_assignments(self) -> list[Assignment]:
        """
        Load education/orientation assignments for the date range.

        Education blocks include orientation (FMO), GME days, and lectures.
        These are protected academic time that cannot be preempted.

        Detection logic:
            - template.rotation_type == 'education'
            - Includes: FMO, GME AM/PM, Lecture AM/PM

        Business Rules:
            - Block 0/1 orientation (FMO) is mandatory for interns
            - GME days are protected academic time
            - Weekly didactics/lectures are required

        Returns:
            List of Assignment objects for education periods
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                RotationTemplate.rotation_type == "education",
            )
            .all()
        )

    def _load_activities(self) -> list[Activity]:
        """
        Load all non-archived activities from the database.

        Activities are slot-level events (FM Clinic, LEC, Specialty) that can
        be assigned to half-day slots. They are used by the
        ActivityRequirementConstraint to enforce per-activity distribution
        targets within rotation blocks.

        Returns:
            List of Activity objects ordered by display_order.
        """
        return (
            self.db.query(Activity)
            .filter(Activity.is_archived == False)  # noqa: E712
            .order_by(Activity.display_order)
            .all()
        )

    def _load_activity_requirements(
        self, template_ids: list[UUID]
    ) -> list[RotationActivityRequirement]:
        """
        Load activity requirements for the given rotation templates.

        Activity requirements define per-activity halfday targets (min/max/target)
        for rotation templates. They are used by the ActivityRequirementConstraint
        to guide the solver toward proper activity distribution.

        This is the dynamic replacement for the fixed-field approach in
        RotationHalfDayRequirement.

        Args:
            template_ids: List of RotationTemplate IDs to load requirements for.

        Returns:
            List of RotationActivityRequirement objects with activity relationship
            eagerly loaded.

        Example:
            >>> template_ids = [neurology_id, sports_med_id]
            >>> requirements = self._load_activity_requirements(template_ids)
            >>> for req in requirements:
            ...     print(f"{req.activity.name}: {req.target_halfdays} half-days")
        """
        if not template_ids:
            return []

        return (
            self.db.query(RotationActivityRequirement)
            .filter(RotationActivityRequirement.rotation_template_id.in_(template_ids))
            .options(selectinload(RotationActivityRequirement.activity))
            .all()
        )

    def _load_protected_patterns(
        self, template_ids: list[UUID]
    ) -> dict[UUID, list[dict]]:
        """
        Load protected weekly patterns for the given rotation templates.

        Protected patterns define locked slots (is_protected=True) that the solver
        cannot modify. These typically include:
        - Wednesday PM lecture (weeks 1-3)
        - Wednesday AM lecture (week 4)
        - Wednesday PM advising (week 4)
        - Fixed clinic times for FMIT/intern rotations

        Args:
            template_ids: List of RotationTemplate IDs to load patterns for.

        Returns:
            Dict mapping template_id to list of pattern dicts with keys:
            day_of_week, time_of_day, activity_type, week_number
        """
        if not template_ids:
            return {}

        patterns = (
            self.db.query(WeeklyPattern)
            .filter(WeeklyPattern.rotation_template_id.in_(template_ids))
            .filter(WeeklyPattern.is_protected == True)  # noqa: E712
            .all()
        )

        # Group by template_id
        result: dict[UUID, list[dict]] = {}
        for pattern in patterns:
            template_id = cast(UUID, pattern.rotation_template_id)
            if template_id not in result:
                result[template_id] = []
            result[template_id].append(
                {
                    "day_of_week": pattern.day_of_week,
                    "time_of_day": pattern.time_of_day,
                    "activity_type": pattern.activity_type,
                    "week_number": pattern.week_number,
                }
            )

        logger.debug(
            f"Loaded {len(patterns)} protected patterns for {len(result)} templates"
        )
        return result

    def _get_rotation_templates(
        self,
        template_ids: list[UUID] | None = None,
        rotation_type: str | None = "outpatient",
    ) -> list[RotationTemplate]:
        """
        Get rotation templates for solver optimization.

        Args:
            template_ids: Optional list of specific template IDs to include
            rotation_type: Filter by rotation type (default: "outpatient").
                          Use None to get all templates.

        Returns:
            List of RotationTemplate objects matching the criteria.

        Note:
            By default, only outpatient templates are returned because the solvers
            are designed for OUTPATIENT HALF-DAY OPTIMIZATION only.
            Block-assigned rotations (FMIT, NF, Inpatient, NICU) should NOT
            be passed to the solver - they are pre-assigned separately.

            The "outpatient" rotation_type includes elective/selective rotations
            (Neurology, ID, Palliative, etc.) that use half-day scheduling.
            FMC continuity clinic is modeled as Activities (fm_clinic, C, C-N),
            not as a separate rotation_type.

            See backend/app/scheduling/solvers.py header for architecture details.
        """
        query = self.db.query(RotationTemplate)

        if template_ids:
            query = query.filter(RotationTemplate.id.in_(template_ids))

        if rotation_type:
            query = query.filter(RotationTemplate.rotation_type == rotation_type)

        return query.all()

    def _assign_faculty(
        self,
        faculty: list[Person],
        blocks: list[Block],
        run_id: UUID,
        preserved_assignments: list[Assignment] | None = None,
    ) -> None:
        """
        Assign faculty supervision based on ACGME supervision ratios.

        This method implements the second phase of scheduling: after residents
        are assigned to blocks, faculty are assigned to provide supervision
        according to ACGME requirements.

        ACGME Supervision Ratios:
            - PGY-1 residents: 1 faculty : 2 residents (0.5 AT load each)
            - PGY-2/3 residents: 1 faculty : 4 residents (0.25 AT load each)
            - Formula: ceil(0.5*PGY1_count + 0.25*Other_count)

        Additional Rules:
            - AM weekday floor: Minimum 1 AT for all AM weekday blocks (safeguard)
            - Procedure clinic +1: PROC, VAS, BTX, COLPO require +1 faculty
            - PCAT counts as AT: Post-Call Attending Time satisfies supervision

        Algorithm:
            1. Group existing resident assignments by block
            2. For each block with residents:
               a. Count PGY-1 vs. PGY-2/3 residents
               b. Calculate ACGME required: ceil(0.5*PGY1 + 0.25*Others)
               c. Check for procedure clinic bonus (+1)
               d. Apply AM weekday floor (min 1)
               e. Final required = max(floor, ACGME) + procedure_bonus
               f. Find available faculty and assign least-loaded
            3. Second pass: Ensure empty AM weekday blocks get floor of 1

        Load Balancing:
            Faculty are sorted by current assignment count and selected in order
            to distribute supervision burden equitably across all faculty.

        Args:
            faculty: List of Person objects with type="faculty"
            blocks: List of Block objects in the scheduling period
            run_id: Schedule run ID for provenance
            preserved_assignments: Assignments that are immutable (FMIT, absences)

        Side Effects:
            Appends faculty Assignment objects to self.assignments with role="supervising"

        Example:
            Block with 2 PGY-1 and 4 PGY-2/3 residents:
            - ACGME required: ceil(0.5*2 + 0.25*4) = ceil(2.0) = 2 faculty
            - If AM weekday: floor = 1, so final = max(1, 2) = 2
            - If PROC clinic: +1 bonus, so final = 3 faculty

        Note:
            This method is separate from the main constraint solver because
            faculty assignment is a post-processing step that depends on
            resident assignments being finalized first.
        """
        # Build set of (faculty_id, block_id) pairs that are already assigned
        # Faculty with FMIT/absences OR solver-assigned cannot supervise clinic
        faculty_occupied_slots: set[tuple[UUID, UUID]] = set()
        faculty_ids = {cast(UUID, f.id) for f in faculty}

        # Check preserved assignments (FMIT, absences, etc.)
        if preserved_assignments:
            for a in preserved_assignments:
                if cast(UUID, a.person_id) in faculty_ids:
                    faculty_occupied_slots.add(
                        (cast(UUID, a.person_id), cast(UUID, a.block_id))
                    )

        # Also check assignments created by solver in this session
        for a in self.assignments:
            if cast(UUID, a.person_id) in faculty_ids:
                faculty_occupied_slots.add(
                    (cast(UUID, a.person_id), cast(UUID, a.block_id))
                )

        # Group assignments by block - include BOTH new (self.assignments) AND preserved
        # Preserved assignments in DB need faculty supervision too
        assignments_by_block: dict[UUID, list[Assignment]] = {}

        # First add new assignments from this run
        for assignment in self.assignments:
            if assignment.block_id not in assignments_by_block:
                assignments_by_block[assignment.block_id] = []
            assignments_by_block[assignment.block_id].append(assignment)

        # Then add preserved assignments (already in DB, not deleted)
        if preserved_assignments:
            for assignment in preserved_assignments:
                if assignment.block_id not in assignments_by_block:
                    assignments_by_block[assignment.block_id] = []
                # Avoid duplicates if same assignment is in both lists
                if assignment not in assignments_by_block[assignment.block_id]:
                    assignments_by_block[assignment.block_id].append(assignment)

        # Pre-fetch all residents who have assignments (N+1 fix)
        # This replaces the per-block query inside the loop
        # Include both new and preserved assignments
        all_resident_ids = {a.person_id for a in self.assignments}
        if preserved_assignments:
            all_resident_ids.update(a.person_id for a in preserved_assignments)
        all_residents = (
            self.db.query(Person).filter(Person.id.in_(all_resident_ids)).all()
        )
        residents_by_id = {r.id: r for r in all_residents}

        # Pre-fetch all rotation templates used in assignments (N+1 fix)
        # This is used by _get_primary_template_for_block to break ties
        # Include both new and preserved assignments
        all_template_ids = {
            a.rotation_template_id for a in self.assignments if a.rotation_template_id
        }
        if preserved_assignments:
            all_template_ids.update(
                a.rotation_template_id
                for a in preserved_assignments
                if a.rotation_template_id
            )
        all_templates = (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.id.in_(all_template_ids))
            .all()
            if all_template_ids
            else []
        )
        templates_by_id = {t.id: t for t in all_templates}

        # Build blocks lookup for time_of_day and is_weekend checks
        blocks_by_id = {b.id: b for b in blocks}

        # Procedure clinic abbreviations that require +1 faculty for immediate supervision
        PROCEDURE_CLINIC_ABBREVS = {"PROC", "VAS", "BTX", "COLPO"}

        # Assign faculty to each block
        faculty_assignments = {f.id: 0 for f in faculty}

        for block_id, block_assignments in assignments_by_block.items():
            # Get block details for floor calculation
            block = blocks_by_id.get(block_id)
            is_am_weekday = (
                block is not None and block.time_of_day == "AM" and not block.is_weekend
            )

            # Get resident details for this block from pre-fetched data
            resident_ids = [a.person_id for a in block_assignments]
            residents_in_block = [
                residents_by_id[rid] for rid in resident_ids if rid in residents_by_id
            ]

            # Calculate required faculty using ACGME ratios
            pgy1_count = sum(1 for r in residents_in_block if r.pgy_level == 1)
            other_count = len(residents_in_block) - pgy1_count

            # Calculate supervision using fractional load approach
            # PGY-1: 2 units (0.5 load = 1:2 ratio), PGY-2/3: 1 unit (0.25 load = 1:4 ratio)
            # Sum loads THEN ceiling (4 units = 1 faculty)
            supervision_units = (pgy1_count * 2) + other_count
            acgme_required = (
                (supervision_units + 3) // 4 if supervision_units > 0 else 0
            )

            # Check for procedure clinic requiring +1 faculty (immediate supervision)
            # ONLY specific procedure clinics (PROC, VAS, BTX, COLPO) need +1
            # Not all "procedures" rotation_type - POCUS, PR-AM don't require +1
            procedure_bonus = 0
            for assignment in block_assignments:
                # Check activity_override first (slot-level activity)
                if assignment.activity_override:
                    override_upper = assignment.activity_override.upper()
                    if any(proc in override_upper for proc in PROCEDURE_CLINIC_ABBREVS):
                        procedure_bonus = 1
                        break

                # Check rotation template abbreviation (ONLY specific clinics)
                if assignment.rotation_template_id:
                    template = templates_by_id.get(assignment.rotation_template_id)
                    if template and template.abbreviation in PROCEDURE_CLINIC_ABBREVS:
                        procedure_bonus = 1
                        break

            # Apply AM weekday floor: always at least 1 AT for AM weekdays (safeguard)
            # PCAT (post-call AT) counts toward this requirement
            if is_am_weekday:
                floor = 1
            else:
                floor = 0

            # Final required = max(floor, ACGME calc) + procedure bonus
            # Cap at 6 (physical limit of faculty in clinic at any time)
            MAX_FACULTY_IN_CLINIC = 6
            required = min(
                MAX_FACULTY_IN_CLINIC, max(floor, acgme_required) + procedure_bonus
            )

            # Find available faculty (not on leave AND not already assigned to this block)
            available = [
                f
                for f in faculty
                if self._is_available(cast(UUID, f.id), cast(UUID, block_id))
                and (cast(UUID, f.id), cast(UUID, block_id))
                not in faculty_occupied_slots
            ]

            # Assign faculty (balance load)
            selected = sorted(
                available, key=lambda f: faculty_assignments[cast(UUID, f.id)]
            )[:required]

            # Determine primary rotation template from resident assignments in this block
            # Faculty should be assigned the same rotation as the residents they supervise
            primary_template_id = self._get_primary_template_for_block(
                block_assignments,
                {cast(UUID, k): v for k, v in templates_by_id.items()},
            )

            for fac in selected:
                assignment = Assignment(
                    block_id=block_id,
                    person_id=fac.id,
                    rotation_template_id=primary_template_id,
                    role="supervising",
                    schedule_run_id=run_id,
                )
                self.assignments.append(assignment)
                faculty_assignments[fac.id] += 1

        # Second pass: Ensure AM weekday blocks without resident assignments still get 1 AT
        # This handles cases where no residents are in clinic but we still need supervision available
        blocks_with_assignments = set(assignments_by_block.keys())
        for block in blocks:
            if block.id in blocks_with_assignments:
                continue  # Already processed above

            # Only apply floor to AM weekday blocks
            if block.time_of_day != "AM" or block.is_weekend:
                continue

            # Check if faculty already assigned to this block (from preserved/expanded)
            if any((f.id, block.id) in faculty_occupied_slots for f in faculty):
                continue

            # Assign 1 faculty for AM weekday floor
            available = [
                f
                for f in faculty
                if self._is_available(cast(UUID, f.id), cast(UUID, block.id))
                and (cast(UUID, f.id), cast(UUID, block.id))
                not in faculty_occupied_slots
            ]

            if available:
                selected = sorted(
                    available, key=lambda f: faculty_assignments[cast(UUID, f.id)]
                )[:1]
                for fac in selected:
                    assignment = Assignment(
                        block_id=block.id,
                        person_id=fac.id,
                        rotation_template_id=None,  # No specific rotation, just AT coverage
                        role="supervising",
                        schedule_run_id=run_id,
                    )
                    self.assignments.append(assignment)
                    faculty_assignments[fac.id] += 1

    def _get_primary_template_for_block(
        self,
        block_assignments: list[Assignment],
        templates_cache: dict[UUID, RotationTemplate] | None = None,
    ) -> UUID | None:
        """
        Determine the primary rotation template for a block based on resident assignments.

        Faculty supervisors should be assigned the same rotation template as the
        residents they're supervising. This ensures:
        1. Faculty show up correctly in activity-type views (e.g., inpatient view)
        2. Reporting and analytics count faculty correctly per rotation type
        3. ACGME compliance reports accurately reflect supervision coverage

        Priority logic (most common template wins):
            - Count occurrences of each template in block's resident assignments
            - Return the most frequently occurring template
            - If tie, prefer inpatient > clinic > other (clinical priority)

        Args:
            block_assignments: List of resident Assignment objects for this block
            templates_cache: Pre-fetched templates dict (N+1 optimization).
                           If None, will query database (for backward compatibility).

        Returns:
            UUID of the primary rotation template, or None if no assignments
        """
        if not block_assignments:
            return None

        # Count template occurrences
        template_counts: dict[UUID, int] = {}
        for assignment in block_assignments:
            if assignment.rotation_template_id:
                tid = cast(UUID, assignment.rotation_template_id)
                template_counts[tid] = template_counts.get(tid, 0) + 1

        if not template_counts:
            return None

        # Find most common template
        # If there's a tie, we'll prefer clinical templates (inpatient, etc.)
        max_count = max(template_counts.values())
        candidates = [
            tid for tid, count in template_counts.items() if count == max_count
        ]

        if len(candidates) == 1:
            return candidates[0]

        # Break ties by preferring inpatient templates
        # Use cache if available to avoid N+1 queries
        for tid in candidates:
            if templates_cache is not None:
                template = templates_cache.get(tid)
            else:
                # Fallback to database query (backward compatibility)
                template = (
                    self.db.query(RotationTemplate)
                    .filter(RotationTemplate.id == tid)
                    .first()
                )
            if template and template.rotation_type == "inpatient":
                return tid

        # Default to first candidate
        return candidates[0]

    def _is_available(self, person_id: UUID, block_id: UUID) -> bool:
        """Check if person is available for block."""
        if person_id not in self.availability_matrix:
            return True
        if block_id not in self.availability_matrix[person_id]:
            return True
        return cast(bool, self.availability_matrix[person_id][block_id]["available"])

    def _create_initial_run(self, algorithm: str) -> ScheduleRun:
        """Create initial run record with 'in_progress' status."""
        run = ScheduleRun(
            start_date=self.start_date,
            end_date=self.end_date,
            algorithm=algorithm,
            status="in_progress",
            total_blocks_assigned=0,
            acgme_violations=0,
            runtime_seconds=0.0,
            config_json={},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _delete_existing_assignments(
        self, preserve_ids: set[UUID] | None = None
    ) -> None:
        """
        Delete existing assignments for the date range to avoid duplicates.

        Uses row-level locking (SELECT FOR UPDATE) to prevent concurrent
        schedule generations from racing. This ensures that only one
        generation can modify assignments for a given date range at a time.

        Args:
            preserve_ids: Set of assignment IDs to preserve (e.g., FMIT assignments)
        """
        preserve_ids = preserve_ids or set()

        # Get all block IDs in the date range with row-level lock
        # The FOR UPDATE lock ensures exclusive access to these blocks
        # during the transaction, preventing concurrent generations from
        # creating conflicting assignments
        blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            )
            .with_for_update(nowait=False)  # Wait for lock rather than fail immediately
            .all()
        )
        block_ids = [block.id for block in blocks]

        if block_ids:
            # Lock and delete existing assignments for these blocks
            # We select first to acquire locks, then delete
            existing_assignments = (
                self.db.query(Assignment)
                .filter(Assignment.block_id.in_(block_ids))
                .with_for_update(nowait=False)
                .all()
            )

            deleted_count = 0
            preserved_count = 0
            for assignment in existing_assignments:
                if assignment.id in preserve_ids:
                    preserved_count += 1
                    continue  # Skip preserved assignments (e.g., FMIT)
                self.db.delete(assignment)
                deleted_count += 1

            logger.info(
                f"Deleted {deleted_count} existing assignments for date range "
                f"({self.start_date} to {self.end_date}), preserved {preserved_count}"
            )

            # CRITICAL: Flush deletes before any inserts to avoid constraint violations
            # SQLAlchemy may execute INSERTs before DELETEs without explicit flush
            self.db.flush()

    def _delete_existing_half_day_assignments(self) -> None:
        """
        Delete existing half-day assignments for the date range that are
        solver/template generated. Preload/manual are preserved.
        """
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource

        deleted_count = (
            self.db.query(HalfDayAssignment)
            .filter(
                HalfDayAssignment.date >= self.start_date,
                HalfDayAssignment.date <= self.end_date,
                HalfDayAssignment.source.in_(
                    [
                        AssignmentSource.SOLVER.value,
                        AssignmentSource.TEMPLATE.value,
                    ]
                ),
            )
            .delete(synchronize_session=False)
        )
        if deleted_count:
            logger.info(
                f"Deleted {deleted_count} solver/template half-day assignments "
                f"for date range {self.start_date} to {self.end_date}"
            )
            self.db.flush()

    def _get_off_activity_id(self) -> UUID:
        """Resolve the OFF activity once for placeholder slots."""
        if getattr(self, "_off_activity_id", None):
            return self._off_activity_id

        result = self.db.execute(
            select(Activity).where(func.lower(Activity.code) == "off")
        )
        activity = result.scalars().first()
        if not activity:
            raise ActivityNotFoundError("off", context="SchedulingEngine")
        self._off_activity_id = activity.id
        return self._off_activity_id

    def _get_blocking_half_day_slots(self) -> set[tuple[UUID, date, str]]:
        """
        Get blocking half-day slots (preload/manual) for the date range.
        Blocking slots should not receive solver rotation assignments.
        """
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
        from app.models.activity import Activity
        from app.utils.activity_locking import is_activity_blocking_for_solver

        locked_rows = (
            self.db.query(
                HalfDayAssignment.person_id,
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                Activity,
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .filter(
                HalfDayAssignment.date >= self.start_date,
                HalfDayAssignment.date <= self.end_date,
                HalfDayAssignment.source.in_(
                    [
                        AssignmentSource.PRELOAD.value,
                        AssignmentSource.MANUAL.value,
                    ]
                ),
            )
            .all()
        )
        blocking = set()
        for person_id, slot_date, time_of_day, activity in locked_rows:
            if is_activity_blocking_for_solver(activity):
                blocking.add((person_id, slot_date, time_of_day))
        return blocking

    def _get_locked_block_pairs(self, blocks: list[Block]) -> set[tuple[UUID, UUID]]:
        """
        Convert locked half-day assignments (preload/manual) into (person_id, block_id) pairs.
        """
        locked_slots = self._get_blocking_half_day_slots()
        if not locked_slots:
            return set()

        block_by_key = {(b.date, b.time_of_day): b.id for b in blocks}
        locked_blocks: set[tuple[UUID, UUID]] = set()
        for person_id, slot_date, time_of_day in locked_slots:
            block_id = block_by_key.get((slot_date, time_of_day))
            if block_id:
                locked_blocks.add((person_id, block_id))
        return locked_blocks

    def _persist_solver_assignments_to_half_day(
        self,
        assignments: list[Assignment],
        blocks: list[Block],
    ) -> int:
        """
        Persist solver assignments into HalfDayAssignment with source='solver'.

        Uses source priority:
        - preload/manual: never overwritten
        - solver/template: overwritten by solver
        """
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource

        off_activity_id = self._get_off_activity_id()
        block_by_id = {b.id: b for b in blocks}
        updated = 0

        for assignment in assignments:
            block = block_by_id.get(cast(UUID, assignment.block_id))
            if not block:
                continue

            existing = (
                self.db.query(HalfDayAssignment)
                .filter(
                    HalfDayAssignment.person_id == assignment.person_id,
                    HalfDayAssignment.date == block.date,
                    HalfDayAssignment.time_of_day == block.time_of_day,
                )
                .first()
            )

            if existing:
                if existing.is_locked:
                    continue
                existing.activity_id = off_activity_id
                existing.source = AssignmentSource.SOLVER.value
                updated += 1
                continue

            self.db.add(
                HalfDayAssignment(
                    person_id=assignment.person_id,
                    date=block.date,
                    time_of_day=block.time_of_day,
                    activity_id=off_activity_id,
                    source=AssignmentSource.SOLVER.value,
                )
            )
            updated += 1

        if updated:
            self.db.flush()
            logger.info(
                f"Persisted {updated} solver half-day assignments (source=solver)"
            )

        return updated

    def _ensure_faculty_half_day_slots(
        self,
        faculty: list[Person],
        blocks: list[Block],
    ) -> int:
        """
        Ensure faculty have half-day slots for the block date range.

        Creates source='solver' HalfDayAssignment rows for any missing
        faculty slots on workdays, preserving any existing preload/manual rows.
        """
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource

        if not faculty:
            return 0

        off_activity_id = self._get_off_activity_id()
        eligible_faculty = [
            f for f in faculty if getattr(f, "faculty_role", None) != "adjunct"
        ]
        faculty_ids = [cast(UUID, f.id) for f in eligible_faculty]
        existing = (
            self.db.query(
                HalfDayAssignment.person_id,
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
            )
            .filter(
                HalfDayAssignment.person_id.in_(faculty_ids),
                HalfDayAssignment.date >= self.start_date,
                HalfDayAssignment.date <= self.end_date,
            )
            .all()
        )
        existing_keys = {(p, d, t) for p, d, t in existing}

        created = 0
        for block in blocks:
            if block.is_weekend:
                continue
            for fac in eligible_faculty:
                key = (cast(UUID, fac.id), block.date, block.time_of_day)
                if key in existing_keys:
                    continue
                self.db.add(
                    HalfDayAssignment(
                        person_id=fac.id,
                        date=block.date,
                        time_of_day=block.time_of_day,
                        activity_id=off_activity_id,
                        source=AssignmentSource.SOLVER.value,
                    )
                )
                created += 1

        if created:
            self.db.flush()
            logger.info(f"Created {created} faculty half-day slots for solver")

        return created

    def _log_constraint_summary(self) -> None:
        """Log enabled/disabled constraint summary for solver diagnostics."""
        if not self.constraint_manager:
            logger.error(
                "Constraint summary unavailable: no ConstraintManager configured"
            )
            return

        enabled = self.constraint_manager.get_enabled()
        disabled = [c for c in self.constraint_manager.constraints if not c.enabled]
        hard = self.constraint_manager.get_hard_constraints()
        soft = self.constraint_manager.get_soft_constraints()

        logger.error(
            f"Constraint summary: enabled={len(enabled)} (hard={len(hard)}, "
            f"soft={len(soft)}), disabled={len(disabled)}"
        )

        enabled_names = sorted({c.name for c in enabled})
        disabled_names = sorted({c.name for c in disabled})

        if enabled_names:
            logger.error(f"Enabled constraints: {self._format_list(enabled_names)}")
        if disabled_names:
            logger.warning(f"Disabled constraints: {self._format_list(disabled_names)}")

    def _log_context_summary(self, context: SchedulingContext) -> None:
        """Log context counts and template coverage for solver diagnostics."""
        if not context:
            logger.error("Context summary unavailable: context is None")
            return

        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        locked_count = len(getattr(context, "locked_blocks", set()))
        call_eligible = len(getattr(context, "call_eligible_faculty", []))

        logger.error(
            "Context summary: residents=%s, faculty=%s, templates=%s, blocks=%s (workday=%s), locked=%s, call_eligible=%s, existing_assignments=%s"
            % (
                len(context.residents),
                len(context.faculty),
                len(context.templates),
                len(context.blocks),
                len(workday_blocks),
                locked_count,
                call_eligible,
                len(getattr(context, "existing_assignments", [])),
            )
        )

        template_codes = sorted(
            {
                (t.abbreviation or t.name or "").strip()
                for t in context.templates
                if (t.abbreviation or t.name)
            }
        )
        if template_codes:
            logger.error(f"Template abbreviations: {self._format_list(template_codes)}")

        required_templates = {"PCAT", "DO", "SM", "NF", "PC"}
        present = {code.upper() for code in template_codes}
        missing = sorted(code for code in required_templates if code not in present)
        if missing:
            logger.warning(
                f"Missing templates (may disable constraints): {', '.join(missing)}"
            )

    def _dump_failure_snapshot(
        self,
        context: SchedulingContext,
        run_id: UUID | None,
        stage: str,
        solver_status: str,
        pre_solver_validation: dict[str, Any] | None = None,
        solver_stats: dict[Any, Any] | None = None,
    ) -> None:
        """Write a PII-free failure snapshot to disk for debugging."""
        if not context:
            logger.error("Failure snapshot unavailable: context is None")
            return

        enabled = (
            self.constraint_manager.get_enabled() if self.constraint_manager else []
        )
        disabled = (
            [c for c in self.constraint_manager.constraints if not c.enabled]
            if self.constraint_manager
            else []
        )
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        locked_count = len(getattr(context, "locked_blocks", set()))
        call_eligible = len(getattr(context, "call_eligible_faculty", []))

        template_summaries = [
            {
                "id": str(getattr(t, "id", "")),
                "name": getattr(t, "name", None),
                "abbreviation": getattr(t, "abbreviation", None),
                "rotation_type": getattr(t, "rotation_type", None),
            }
            for t in context.templates
        ]
        template_codes = {
            (t.abbreviation or t.name or "").strip().upper()
            for t in context.templates
            if (t.abbreviation or t.name)
        }
        required_templates = {"PCAT", "DO", "SM", "NF", "PC"}
        missing_templates = sorted(
            code for code in required_templates if code not in template_codes
        )

        snapshot = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "stage": stage,
            "solver_status": solver_status,
            "run_id": str(run_id) if run_id else None,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "counts": {
                "residents": len(context.residents),
                "faculty": len(context.faculty),
                "templates": len(context.templates),
                "blocks": len(context.blocks),
                "workday_blocks": len(workday_blocks),
                "locked_blocks": locked_count,
                "call_eligible_faculty": call_eligible,
                "existing_assignments": len(
                    getattr(context, "existing_assignments", [])
                ),
            },
            "constraints": {
                "enabled": sorted({c.name for c in enabled}),
                "disabled": sorted({c.name for c in disabled}),
                "hard_enabled": sorted(
                    {c.name for c in self.constraint_manager.get_hard_constraints()}
                )
                if self.constraint_manager
                else [],
                "soft_enabled": sorted(
                    {c.name for c in self.constraint_manager.get_soft_constraints()}
                )
                if self.constraint_manager
                else [],
            },
            "templates": template_summaries,
            "missing_templates": missing_templates,
            "pre_solver_validation": pre_solver_validation,
            "solver_stats": solver_stats,
        }

        output_dir = Path(
            os.environ.get("SCHEDULE_FAILURE_SNAPSHOT_DIR", "/tmp")
        ).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            safe_run_id = str(run_id) if run_id else "unknown"
            path = output_dir / f"schedule_failure_{safe_run_id}_{stamp}.json"
            path.write_text(json.dumps(snapshot, indent=2, default=str))
            logger.error(f"Wrote failure snapshot to {path}")
        except Exception as exc:
            logger.error(f"Failed to write failure snapshot: {exc}")

    @staticmethod
    def _format_list(items: list[str], max_items: int = 20) -> str:
        """Format long lists for logs without overwhelming output."""
        if len(items) <= max_items:
            return ", ".join(items)
        return ", ".join(items[:max_items]) + f", ... (+{len(items) - max_items} more)"

    def _audit_nf_pc_allocations(self) -> dict:
        """
        Audit Night Float to Post-Call allocations after generation.

        Blindspot #6: Post-generation audit for NF->PC allocations.

        This verifies that for each NF (Night Float) assignment ending at a
        block-half boundary, the next day has proper PC (Post-Call) assignments
        for both AM and PM blocks.

        Returns:
            dict with:
                - compliant: bool - True if all NF->PC requirements are met
                - total_nf_transitions: int - Total NF block-half transitions found
                - violations: list[dict] - Details of missing PC assignments
        """
        violations = []
        total_transitions = 0

        # Get all assignments grouped by person and block
        assignments_by_person: dict[UUID, list] = {}
        for assignment in self.assignments:
            if assignment.person_id not in assignments_by_person:
                assignments_by_person[assignment.person_id] = []
            assignments_by_person[assignment.person_id].append(assignment)

        # Get NF and PC template IDs
        nf_template = (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.abbreviation == "NF")
            .first()
        )
        pc_template = (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.abbreviation == "PC")
            .first()
        )

        if not nf_template:
            logger.debug("No NF rotation template found - skipping NF->PC audit")
            return {
                "compliant": True,
                "total_nf_transitions": 0,
                "violations": [],
                "message": "No Night Float rotation template configured",
            }

        if not pc_template:
            logger.warning("No PC rotation template found - cannot validate NF->PC")
            return {
                "compliant": False,
                "total_nf_transitions": 0,
                "violations": [{"error": "PC rotation template not configured"}],
                "message": "Post-Call rotation template not configured",
            }

        # Pre-fetch all blocks in the date range (N+1 fix)
        # Build lookups by ID and by date for efficient access
        all_blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            )
            .all()
        )
        blocks_by_id = {b.id: b for b in all_blocks}
        blocks_by_date: dict[date, list[Block]] = {}
        for block in all_blocks:
            if block.date not in blocks_by_date:
                blocks_by_date[block.date] = []
            blocks_by_date[block.date].append(block)

        # Pre-fetch all persons who have assignments (N+1 fix)
        all_person_ids = list(assignments_by_person.keys())
        all_persons = (
            self.db.query(Person).filter(Person.id.in_(all_person_ids)).all()
            if all_person_ids
            else []
        )
        persons_by_id = {p.id: p for p in all_persons}

        # Check each person's NF assignments
        for person_id, person_assignments in assignments_by_person.items():
            # Find NF assignments
            nf_assignments = [
                a
                for a in person_assignments
                if a.rotation_template_id == nf_template.id
            ]

            if not nf_assignments:
                continue

            # Group NF assignments by date to find transition days
            # Use pre-fetched blocks instead of querying per assignment
            nf_by_date: dict[date, list] = {}
            for a in nf_assignments:
                block = blocks_by_id.get(a.block_id)
                if block:
                    if block.date not in nf_by_date:
                        nf_by_date[block.date] = []
                    nf_by_date[block.date].append(a)

            # For each NF date, check if next day has PC
            for nf_date in sorted(nf_by_date.keys()):
                pc_required_date = nf_date + timedelta(days=1)

                # Skip if outside schedule range
                if pc_required_date > self.end_date:
                    continue

                total_transitions += 1

                # Check for PC assignments on the required date
                # Use pre-fetched blocks instead of querying per date
                pc_blocks = blocks_by_date.get(pc_required_date, [])

                has_am_pc = False
                has_pm_pc = False

                for block in pc_blocks:
                    # Check if person has PC assignment for this block
                    pc_assignment = next(
                        (
                            a
                            for a in person_assignments
                            if a.block_id == block.id
                            and a.rotation_template_id == pc_template.id
                        ),
                        None,
                    )
                    if pc_assignment:
                        if block.time_of_day == "AM":
                            has_am_pc = True
                        elif block.time_of_day == "PM":
                            has_pm_pc = True

                # Record violations
                if not has_am_pc or not has_pm_pc:
                    # Use pre-fetched person instead of querying per violation
                    person = persons_by_id.get(person_id)
                    violations.append(
                        {
                            "person_id": str(person_id),
                            "person_name": person.name if person else "Unknown",
                            "nf_date": str(nf_date),
                            "pc_required_date": str(pc_required_date),
                            "missing_am_pc": not has_am_pc,
                            "missing_pm_pc": not has_pm_pc,
                        }
                    )

        return {
            "compliant": len(violations) == 0,
            "total_nf_transitions": total_transitions,
            "violations": violations,
            "message": f"Audited {total_transitions} NF transitions, "
            f"found {len(violations)} violations",
        }

    def _update_run_status(
        self,
        run: ScheduleRun,
        status: str,
        total_assigned: int,
        violations: int,
        runtime: float,
    ) -> None:
        """Update run record with final status."""
        run.status = status
        run.total_blocks_assigned = total_assigned
        run.acgme_violations = violations
        run.runtime_seconds = runtime
        self.db.add(run)

    def _update_run_with_results(
        self,
        run: ScheduleRun,
        algorithm: str,
        validation: ValidationResult,
        runtime: float,
        solver_result: SolverResult | None = None,
    ) -> None:
        """Update run record with generation results."""
        config = {}
        if solver_result:
            config = {
                "solver_status": solver_result.solver_status,
                "objective_value": solver_result.objective_value,
                "solver_runtime": solver_result.runtime_seconds,
                "statistics": solver_result.statistics,
            }

        run.algorithm = algorithm
        run.status = "success" if validation.valid else "partial"
        run.total_blocks_assigned = len(self.assignments)
        run.acgme_violations = validation.total_violations
        run.runtime_seconds = runtime
        run.config_json = config
        self.db.add(run)

    def _empty_validation(self) -> ValidationResult:
        """Return empty validation result."""
        return ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=0.0,
        )

    def _check_pre_generation_resilience(self) -> Any:
        """
        Run resilience health check before schedule generation.

        This provides early warning if system is already stressed.
        """
        try:
            faculty = self._get_faculty()
            blocks = (
                self.db.query(Block)
                .filter(
                    Block.date >= self.start_date,
                    Block.date <= self.end_date,
                )
                .all()
            )
            existing_assignments = (
                self.db.query(Assignment)
                .join(Block)
                .filter(
                    Block.date >= self.start_date,
                    Block.date <= self.end_date,
                )
                .all()
            )

            report = self.resilience.check_health(
                faculty=faculty,
                blocks=blocks,
                assignments=existing_assignments,
            )

            # Log warning if system is stressed
            if report.overall_status in ("critical", "emergency"):
                logger.warning(
                    f"Pre-generation resilience check: {report.overall_status.upper()}. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}. "
                    f"Actions: {report.immediate_actions}"
                )
            elif report.overall_status == "degraded":
                logger.info(
                    f"Pre-generation resilience check: degraded. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}"
                )

            return report

        except Exception as e:
            logger.warning(f"Pre-generation resilience check failed: {e}")
            return None

    def _check_post_generation_resilience(
        self,
        faculty: list[Person],
        blocks: list[Block],
        assignments: list[Assignment],
    ) -> Any:
        """
        Run resilience health check after schedule generation.

        This validates the generated schedule doesn't create stress conditions.
        """
        try:
            report = self.resilience.check_health(
                faculty=faculty,
                blocks=blocks,
                assignments=assignments,
            )

            # Log if schedule creates concerning conditions
            if report.overall_status in ("critical", "emergency"):
                logger.warning(
                    f"Post-generation resilience check: {report.overall_status.upper()}. "
                    f"Generated schedule may create stress conditions. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}"
                )
            elif not report.n1_pass:
                logger.warning(
                    "Post-generation resilience check: N-1 FAIL. "
                    "Schedule is vulnerable to single faculty loss."
                )

            return report

        except Exception as e:
            logger.warning(f"Post-generation resilience check failed: {e}")
            return None

    def _get_resilience_warnings(self, health_report: Any) -> list[str]:
        """Extract actionable warnings from health report."""
        warnings: list[str] = []

        if health_report is None:
            return warnings

        # Utilization warnings
        if health_report.utilization.level.value in ("ORANGE", "RED", "BLACK"):
            warnings.append(
                f"High utilization ({health_report.utilization.utilization_rate:.0%}) - "
                f"approaching cascade failure risk"
            )

        # Contingency warnings
        if not health_report.n1_pass:
            warnings.append(
                "N-1 vulnerability: Schedule cannot survive loss of one key faculty member"
            )
        if not health_report.n2_pass:
            warnings.append(
                "N-2 vulnerability: Schedule cannot survive loss of two faculty members"
            )

        # Phase transition warning
        if health_report.phase_transition_risk in ("high", "critical"):
            warnings.append(
                f"Phase transition risk is {health_report.phase_transition_risk} - "
                f"system may experience sudden degradation"
            )

        # Buffer warning
        if health_report.utilization.buffer_remaining < 0.10:
            warnings.append(
                f"Buffer critically low ({health_report.utilization.buffer_remaining:.0%}) - "
                f"no capacity for unexpected absences"
            )

        return warnings
