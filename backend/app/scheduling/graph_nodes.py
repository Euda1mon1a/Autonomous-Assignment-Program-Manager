"""
Graph node functions for the scheduling pipeline.

Each function corresponds to one phase of SchedulingEngine.generate().
Functions read from state/config and return a partial state dict.
Side effects (DB writes) happen through the engine instance.
"""

from __future__ import annotations

import os
import time
from datetime import date
from typing import Any, cast
from uuid import UUID

from langchain_core.runnables import RunnableConfig

from app.core.logging import get_logger
from app.schemas.schedule import (
    NFPCAudit,
    NFPCAuditViolation,
    ValidationResult,
    Violation,
)
from app.scheduling.graph_state import ScheduleGraphState

logger = get_logger(__name__)


def _get_engine(config: RunnableConfig) -> Any:
    """Extract the SchedulingEngine from LangGraph config."""
    return config["configurable"]["engine"]


def _get_param(config: RunnableConfig, key: str, default: Any = None) -> Any:
    """Extract a generation parameter from LangGraph config."""
    return config["configurable"].get(key, default)


# ─── Node 1: init ────────────────────────────────────────────────────


def init_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Validate algorithm, create ScheduleRun, run pre-resilience check.

    Corresponds to engine.py lines 169-198.
    """
    engine = _get_engine(config)
    start_time = time.time()

    # Force canonical CP-SAT solver
    algorithm = _get_param(config, "algorithm", "cp_sat")
    if algorithm not in engine.ALGORITHMS:
        algorithm = "cp_sat"
    if algorithm != "cp_sat":
        logger.info(
            f"Overriding algorithm '{algorithm}' -> 'cp_sat' (canonical pathway)"
        )
        algorithm = "cp_sat"

    run = engine._create_initial_run(algorithm)

    # Pre-generation resilience check
    engine._pre_health_report = None
    if _get_param(config, "check_resilience", True):
        engine._pre_health_report = engine._check_pre_generation_resilience()

    return {
        "start_time": start_time,
        "run": run,
        "run_id": cast(UUID, run.id),
        "failed": False,
        "error": None,
    }


# ─── Node 2: load_data ───────────────────────────────────────────────


def load_data_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Ensure blocks, load preserved assignments, build availability.

    Corresponds to engine.py lines 200-324.
    """
    engine = _get_engine(config)

    # Step 1: Ensure blocks exist
    blocks = engine._ensure_blocks_exist(commit=False)

    # Steps 1.5a-f: Load preserved assignments
    preserve_ids: set[UUID] = set()

    fmit_assignments: list[Any] = []
    if _get_param(config, "preserve_fmit", True):
        fmit_assignments = engine._load_fmit_assignments()
        preserve_ids.update({cast(UUID, a.id) for a in fmit_assignments})
        if fmit_assignments:
            logger.info(f"Preserving {len(fmit_assignments)} FMIT faculty assignments")

    resident_inpatient_assignments: list[Any] = []
    if _get_param(config, "preserve_resident_inpatient", True):
        resident_inpatient_assignments = engine._load_resident_inpatient_assignments()
        preserve_ids.update({cast(UUID, a.id) for a in resident_inpatient_assignments})
        if resident_inpatient_assignments:
            logger.info(
                f"Preserving {len(resident_inpatient_assignments)} "
                "resident inpatient assignments (FMIT/NF/NICU)"
            )

    absence_assignments: list[Any] = []
    if _get_param(config, "preserve_absence", True):
        absence_assignments = engine._load_absence_assignments()
        preserve_ids.update({cast(UUID, a.id) for a in absence_assignments})
        if absence_assignments:
            logger.info(
                f"Preserving {len(absence_assignments)} "
                "absence assignments (Leave/Weekend)"
            )

    offsite_assignments = engine._load_offsite_assignments()
    preserve_ids.update({cast(UUID, a.id) for a in offsite_assignments})
    if offsite_assignments:
        logger.info(
            f"Preserving {len(offsite_assignments)} "
            "off-site assignments (Hilo/Kapiolani/Okinawa)"
        )

    recovery_assignments = engine._load_recovery_assignments()
    preserve_ids.update({cast(UUID, a.id) for a in recovery_assignments})
    if recovery_assignments:
        logger.info(
            f"Preserving {len(recovery_assignments)} recovery assignments (Post-Call)"
        )

    education_assignments = engine._load_education_assignments()
    preserve_ids.update({cast(UUID, a.id) for a in education_assignments})
    if education_assignments:
        logger.info(
            f"Preserving {len(education_assignments)} "
            "education assignments (FMO/GME/Lectures)"
        )

    logger.info(
        f"Preservation summary: "
        f"fmit={len(fmit_assignments)}, "
        f"inpatient={len(resident_inpatient_assignments)}, "
        f"absence={len(absence_assignments)}, "
        f"offsite={len(offsite_assignments)}, "
        f"recovery={len(recovery_assignments)}, "
        f"education={len(education_assignments)}, "
        f"total_preserve_ids={len(preserve_ids)}"
    )

    # Step 1.5g: Infer block/year if not provided
    block_number = _get_param(config, "block_number")
    academic_year = _get_param(config, "academic_year")
    if block_number is None or academic_year is None:
        from app.utils.academic_blocks import get_block_number_for_date

        block_number, _ = get_block_number_for_date(engine.start_date)
        if engine.start_date.month >= 7:
            academic_year = engine.start_date.year
        else:
            academic_year = engine.start_date.year - 1
        logger.info(f"Inferred block {block_number} AY {academic_year} from dates")

    # Step 2: Build availability matrix
    engine._build_availability_matrix()

    # Step 3: Get residents, faculty, templates
    create_draft = _get_param(config, "create_draft", False)
    residents = engine._get_residents(
        _get_param(config, "pgy_levels"),
        block_number,
        academic_year,
        create_draft=create_draft,
    )
    templates = engine._get_rotation_templates(
        _get_param(config, "rotation_template_ids")
    )
    faculty = engine._get_faculty()

    logger.info(
        f"Data load summary: "
        f"residents={len(residents)}, templates={len(templates)}, "
        f"faculty={len(faculty)}"
    )

    # Step 3.5: Load non-call preloads
    preload_count = 0
    if block_number is not None and academic_year is not None and not create_draft:
        from app.services.sync_preload_service import SyncPreloadService

        preload_service = SyncPreloadService(engine.db)
        preload_count = preload_service.load_all_preloads(
            block_number, academic_year, skip_faculty_call=True
        )
        logger.info(f"Loaded {preload_count} non-call preload assignments")
    elif create_draft:
        logger.info("Skipping preload sync in draft mode (would modify live data)")

    return {
        "blocks": blocks,
        "fmit_assignments": fmit_assignments,
        "resident_inpatient_assignments": resident_inpatient_assignments,
        "absence_assignments": absence_assignments,
        "offsite_assignments": offsite_assignments,
        "recovery_assignments": recovery_assignments,
        "education_assignments": education_assignments,
        "preserve_ids": preserve_ids,
        "block_number": block_number,
        "academic_year": academic_year,
        "residents": residents,
        "faculty": faculty,
        "templates": templates,
        "preload_count": preload_count,
    }


# ─── Node 3: check_residents ─────────────────────────────────────────


def check_residents_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Fail fast if no residents found.

    Corresponds to engine.py lines 334-344.
    """
    if not state.get("residents"):
        engine = _get_engine(config)
        run = state["run"]
        engine._update_run_status(
            run, "failed", 0, 0, time.time() - state["start_time"]
        )
        engine.db.commit()
        return {
            "failed": True,
            "error": "No residents found matching criteria",
            "result": {
                "status": "failed",
                "message": "No residents found matching criteria",
                "total_assigned": 0,
                "total_blocks": len(state.get("blocks", [])),
                "validation": engine._empty_validation(),
                "run_id": state["run_id"],
            },
        }
    return {"failed": False}


# ─── Node 4: build_context ───────────────────────────────────────────


def build_context_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Build SchedulingContext, adjust constraints for half-day blocks.

    Corresponds to engine.py lines 346-399.
    """
    engine = _get_engine(config)

    # Combine all preserved assignments
    preserved_assignments = (
        state.get("fmit_assignments", [])
        + state.get("resident_inpatient_assignments", [])
        + state.get("absence_assignments", [])
        + state.get("offsite_assignments", [])
        + state.get("recovery_assignments", [])
        + state.get("education_assignments", [])
    )

    context = engine._build_context(
        state["residents"],
        state["faculty"],
        state["blocks"],
        state["templates"],
        include_resilience=_get_param(config, "check_resilience", True),
        existing_assignments=preserved_assignments,
        block_number=state.get("block_number"),
        academic_year=state.get("academic_year"),
    )

    # Half-day constraint adjustments (engine.py lines 367-399)
    blocks = state["blocks"]
    if any(getattr(block, "time_of_day", None) for block in blocks):
        engine.constraint_manager.disable("OnePersonPerBlock")
        logger.info("Disabled OnePersonPerBlock constraint for half-day blocks")

        # Check for time-off context in availability data
        has_time_off_context = any(
            bool(days) for days in getattr(context, "preassigned_off_days", {}).values()
        )
        if not has_time_off_context:
            for resident in context.residents:
                for info in context.availability.get(resident.id, {}).values():
                    if not info.get("available", True):
                        has_time_off_context = True
                        break
                if has_time_off_context:
                    break

        if not has_time_off_context:
            logger.info(
                "No time-off data detected in solver context; "
                "1in7Rule and 80HourRule remain enabled"
            )

        # Disable clinic-wide constraints for half-day solver
        engine.constraint_manager.disable("MaxPhysiciansInClinic")
        engine.constraint_manager.disable("WednesdayAMInternOnly")
        engine.constraint_manager.disable("WednesdayPMSingleFaculty")
        engine.constraint_manager.disable("InvertedWednesday")
        engine.constraint_manager.disable("ProtectedSlot")
        logger.info(
            "Disabled MaxPhysiciansInClinic, Wednesday temporal, "
            "and ProtectedSlot constraints for half-day blocks"
        )

    return {
        "context": context,
        "preserved_assignments": preserved_assignments,
    }


# ─── Node 5: pre_validate ────────────────────────────────────────────


def pre_validate_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Run PreSolverValidator. Sets failed=True if infeasible.

    Corresponds to engine.py lines 401-457.
    """
    from app.scheduling.pre_solver_validator import PreSolverValidator

    engine = _get_engine(config)
    pre_validator = PreSolverValidator()
    validation_result = pre_validator.validate_saturation(state["context"])

    if not validation_result.feasible:
        logger.error(
            f"Pre-solver validation failed: "
            f"{len(validation_result.issues)} issues detected"
        )
        for issue in validation_result.issues:
            logger.error(f"  - {issue}")
        for recommendation in validation_result.recommendations:
            logger.info(f"  Recommendation: {recommendation}")

        engine._log_constraint_summary()
        engine._log_context_summary(state["context"])
        engine._dump_failure_snapshot(
            state["context"],
            run_id=state["run_id"],
            stage="pre_solver_validation",
            solver_status="pre_solver_validation_failed",
            pre_solver_validation={
                "feasible": False,
                "issues": validation_result.issues,
                "recommendations": validation_result.recommendations,
                "statistics": validation_result.statistics,
            },
        )

        run = state["run"]
        engine._update_run_status(
            run, "failed", 0, 0, time.time() - state["start_time"]
        )
        engine.db.commit()

        return {
            "pre_validation_passed": False,
            "pre_validation_result": validation_result,
            "failed": True,
            "error": f"Pre-solver validation failed: {len(validation_result.issues)} issues",
            "result": {
                "status": "failed",
                "message": f"Pre-solver validation failed: {len(validation_result.issues)} issues",
                "total_assigned": 0,
                "total_blocks": len(state.get("blocks", [])),
                "validation": engine._empty_validation(),
                "run_id": state["run_id"],
                "pre_solver_validation": {
                    "feasible": False,
                    "issues": validation_result.issues,
                    "recommendations": validation_result.recommendations,
                    "statistics": validation_result.statistics,
                },
            },
        }

    # Log success
    logger.info(
        f"Pre-solver validation passed: "
        f"complexity={validation_result.statistics.get('complexity_level', 'UNKNOWN')}, "
        f"{validation_result.statistics.get('num_variables', 0):,} variables, "
        f"estimated runtime: {validation_result.statistics.get('estimated_runtime', 'unknown')}"
    )
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning(f"Pre-solver warning: {warning}")

    return {
        "pre_validation_passed": True,
        "pre_validation_result": validation_result,
        "failed": False,
    }


# ─── Node 6: solve ───────────────────────────────────────────────────


def solve_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Run CP-SAT solver. Sets failed=True if solver fails.

    Corresponds to engine.py lines 459-490.
    """
    engine = _get_engine(config)
    timeout = _get_param(config, "timeout_seconds", 60.0)

    logger.info("Running CP-SAT solver for outpatient assignments + call")
    solver_result = engine._run_solver("cp_sat", state["context"], timeout)

    if not solver_result.success:
        logger.error(f"CP-SAT solver failed: {solver_result.solver_status}")
        if solver_result.solver_status.upper() == "INFEASIBLE":
            logger.error(
                "CP-SAT reported INFEASIBLE; schedule may be impossible "
                "with current hard constraints."
            )
        engine._log_constraint_summary()
        engine._log_context_summary(state["context"])
        engine._dump_failure_snapshot(
            state["context"],
            run_id=state["run_id"],
            stage="solver",
            solver_status=solver_result.solver_status,
            solver_stats=solver_result.statistics,
        )

        run = state["run"]
        engine._update_run_status(
            run, "failed", 0, 0, time.time() - state["start_time"]
        )
        engine.db.commit()

        return {
            "solver_result": solver_result,
            "failed": True,
            "error": f"CP-SAT solver failed: {solver_result.solver_status}",
            "result": {
                "status": "failed",
                "message": f"CP-SAT solver failed: {solver_result.solver_status}",
                "total_assigned": 0,
                "total_blocks": len(state.get("blocks", [])),
                "validation": engine._empty_validation(),
                "run_id": state["run_id"],
            },
        }

    logger.info(
        f"CP-SAT solver generated {len(solver_result.assignments)} "
        f"rotation assignments and {len(solver_result.call_assignments)} "
        "call assignments"
    )

    return {"solver_result": solver_result, "failed": False}


# ─── Node 7: persist_and_call ─────────────────────────────────────────


def persist_and_call_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Delete old, create assignments, create call assignments, PCAT/DO sync.

    Merged node preserving the no_autoflush context manager boundary.
    Corresponds to engine.py lines 492-592.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)
    validate_pcat_do = _get_param(config, "validate_pcat_do", True)

    from app.models.schedule_run import ScheduleRun

    with engine.db.no_autoflush:
        # Step 5.5: Delete existing assignments (except preserved)
        if not create_draft:
            engine._delete_existing_assignments(state["preserve_ids"])
            engine._delete_existing_half_day_assignments()

        # Step 6: Convert solver results to assignments
        locked_slots = engine._get_blocking_half_day_slots()
        blocks_by_id = {b.id: b for b in state["blocks"]}
        engine._create_assignments_from_result(
            state["solver_result"],
            state["residents"],
            state["templates"],
            state["run_id"],
            existing_assignments=state.get("preserved_assignments"),
            locked_half_day_slots=locked_slots,
            blocks_by_id=blocks_by_id,
        )
        if not create_draft:
            for assignment in engine.assignments:
                engine.db.add(assignment)
            engine.db.flush()
            engine._persist_solver_assignments_to_half_day(
                engine.assignments, state["blocks"]
            )
            # Step 6.1: Persist faculty half-day from solver
            engine._persist_faculty_half_day_from_solver(
                state["solver_result"], state["blocks"]
            )

        # Step 6.5: Create call assignments
        call_assignments: list[Any] = []
        if not create_draft:
            call_assignments = engine._create_call_assignments_from_result(
                state["solver_result"], state["context"]
            )

            # Step 6.6: Sync PCAT/DO
            if call_assignments:
                engine._sync_call_pcat_do_to_half_day(call_assignments)

                # Step 6.6.1: Validate PCAT/DO integrity
                if validate_pcat_do:
                    pcat_do_issues = engine._validate_pcat_do_integrity(
                        call_assignments
                    )
                    if pcat_do_issues:
                        logger.error(
                            f"PCAT/DO integrity check FAILED: "
                            f"{len(pcat_do_issues)} issues detected"
                        )
                        for issue in pcat_do_issues:
                            logger.error(f"  - {issue}")

                        # Rollback and fail
                        run_id = state["run_id"]
                        elapsed = time.time() - state["start_time"]
                        engine.db.rollback()

                        existing_run = engine.db.get(ScheduleRun, run_id)
                        if existing_run:
                            engine._update_run_status(
                                existing_run, "failed", 0, 0, elapsed
                            )
                            engine.db.commit()

                        return {
                            "assignments": [],
                            "call_assignments": [],
                            "pcat_do_valid": False,
                            "failed": True,
                            "error": f"PCAT/DO integrity check failed: {len(pcat_do_issues)} issues",
                            "result": {
                                "status": "failed",
                                "message": f"PCAT/DO integrity check failed: {len(pcat_do_issues)} issues (rolled back)",
                                "total_assigned": 0,
                                "total_blocks": len(state.get("blocks", [])),
                                "validation": engine._empty_validation(),
                                "run_id": run_id,
                                "pcat_do_issues": pcat_do_issues,
                            },
                        }
                    else:
                        logger.info(
                            f"PCAT/DO integrity check passed "
                            f"({len(call_assignments)} calls verified)"
                        )
        elif state["solver_result"].call_assignments:
            logger.info(
                f"Skipping {len(state['solver_result'].call_assignments)} "
                f"call assignments in draft mode "
                "(would modify live CallAssignment table)"
            )

    return {
        "assignments": list(engine.assignments),
        "call_assignments": call_assignments,
        "pcat_do_valid": True,
        "failed": False,
    }


# ─── Node 8: activity_solver ─────────────────────────────────────────


def activity_solver_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Run CPSATActivitySolver for half-day activity assignment.

    Corresponds to engine.py lines 594-638.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)
    block_number = state.get("block_number")
    academic_year = state.get("academic_year")
    timeout = _get_param(config, "timeout_seconds", 60.0)

    activity_result: dict[str, Any] = {}

    if block_number is not None and academic_year is not None and not create_draft:
        from app.scheduling.activity_solver import CPSATActivitySolver

        include_faculty = os.getenv(
            "ACTIVITY_SOLVER_INCLUDE_FACULTY", "true"
        ).strip().lower() in {"1", "true", "yes", "on"}

        activity_solver = CPSATActivitySolver(
            engine.db,
            timeout_seconds=min(timeout, 30.0),
        )
        activity_result = activity_solver.solve(
            block_number,
            academic_year,
            include_faculty_slots=include_faculty,
            force_faculty_override=include_faculty,
        )
        if activity_result.get("success"):
            logger.info(
                f"Activity solver assigned "
                f"{activity_result.get('assignments_updated', 0)} "
                f"activities ({activity_result.get('status', 'unknown')}); "
                f"faculty_slots={'on' if include_faculty else 'off'}"
            )
        else:
            logger.warning(
                f"Activity solver failed: "
                f"{activity_result.get('message', 'unknown error')}"
            )
    elif create_draft and (block_number is not None and academic_year is not None):
        logger.info("Skipping activity solver in draft mode (would modify live data)")

    return {"activity_result": activity_result}


# ─── Node 9: backfill ────────────────────────────────────────────────


def backfill_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Backfill weekend slots and virtual clinic conversion.

    Corresponds to engine.py lines 640-650.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)

    if not create_draft:
        engine._backfill_weekend_slots(state["residents"], state["blocks"])
        engine._backfill_virtual_clinic(state["residents"])

    return {}


# ─── Node 10: persist_draft_or_live ───────────────────────────────────


def persist_draft_or_live_node(
    state: ScheduleGraphState, config: RunnableConfig
) -> dict:
    """Create draft or flush live assignments.

    Corresponds to engine.py lines 652-692.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)

    draft_id = None
    if create_draft:
        from app.models.schedule_draft import DraftSourceType
        from app.services.schedule_draft_service import ScheduleDraftService

        draft_service = ScheduleDraftService(engine.db)
        draft_result = draft_service.create_draft_sync(
            source_type=DraftSourceType.SOLVER,
            start_date=engine.start_date,
            end_date=engine.end_date,
            block_number=state.get("block_number"),
            created_by_id=_get_param(config, "created_by_id"),
            schedule_run_id=state["run_id"],
            notes="Generated by cp_sat solver",
        )

        if draft_result.success and draft_result.draft_id:
            draft_id = draft_result.draft_id
            logger.info(f"Created draft {draft_id} for staging")
            draft_service.add_solver_assignments_to_draft_sync(
                draft_id=draft_id,
                assignments=engine.assignments,
                existing_ids=state.get("preserve_ids", set()),
            )
        else:
            logger.warning(
                f"Failed to create draft: {draft_result.message}. "
                "Falling back to live commit."
            )
            for assignment in engine.assignments:
                engine.db.add(assignment)
            engine.db.flush()
    else:
        # Assignments already added/flushed in persist_and_call
        engine.db.flush()

    return {"draft_id": draft_id}


# ─── Node 11: validate ───────────────────────────────────────────────


def validate_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Run ACGME validation and NF/PC audit.

    Corresponds to engine.py lines 694-779.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)
    draft_id = state.get("draft_id")

    # Step 9: Validate
    validation = engine.validator.validate_all(engine.start_date, engine.end_date)

    # Step 9.1: Add validation flags to draft
    if create_draft and draft_id and validation.violations:
        from app.services.schedule_draft_service import ScheduleDraftService

        draft_service = ScheduleDraftService(engine.db)
        draft_service.add_validation_flags_to_draft_sync(
            draft_id=draft_id,
            validation_result=validation,
        )

    # Step 9.5: NF -> PC audit
    nf_pc_audit_raw = engine._audit_nf_pc_allocations()
    if not nf_pc_audit_raw.get("compliant", True):
        violations = list(validation.violations)
        for nf_violation in nf_pc_audit_raw.get("violations", []):
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
                    message=("Missing Post-Call coverage after Night Float day"),
                    details={
                        "nf_date": nf_violation.get("nf_date"),
                        "pc_required_date": nf_violation.get("pc_required_date"),
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

    # Build NFPCAudit model
    nf_pc_audit_model = None
    if nf_pc_audit_raw:
        audit_violations = []
        for v in nf_pc_audit_raw.get("violations", []):
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
            compliant=nf_pc_audit_raw.get("compliant", True),
            total_nf_transitions=nf_pc_audit_raw.get("total_nf_transitions", 0),
            violations=audit_violations,
            message=nf_pc_audit_raw.get("message"),
        )

    return {
        "validation": validation,
        "nf_pc_audit": nf_pc_audit_model,
        "nf_pc_audit_raw": nf_pc_audit_raw,
    }


# ─── Node 12: ml_score ───────────────────────────────────────────────


def ml_score_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Score the generated schedule using ML models (if enabled).

    Runs post-validation, pre-finalize. Provides quality metrics
    (preference satisfaction, workload balance, conflict risk) that
    are included in the final result for human review.

    Gracefully degrades: if ML is disabled or models aren't trained,
    returns empty scores and continues the pipeline.
    """
    engine = _get_engine(config)
    settings = getattr(engine, "settings", None)

    # Check if ML scoring is enabled
    ml_enabled = False
    if settings:
        ml_enabled = getattr(settings, "ML_ENABLED", False)
    if not ml_enabled:
        ml_enabled = os.getenv("ML_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    if not ml_enabled:
        logger.debug("ML scoring disabled (ML_ENABLED=false); skipping")
        return {"ml_scores": {}}

    try:
        from pathlib import Path

        from app.ml.inference.schedule_scorer import ScheduleScorer

        # Resolve model paths from settings or env
        models_dir = Path(
            getattr(settings, "ML_MODELS_DIR", None)
            or os.getenv("ML_MODELS_DIR", "models")
        )
        pref_path = getattr(settings, "ML_PREFERENCE_MODEL_PATH", None) or None
        conflict_path = getattr(settings, "ML_CONFLICT_MODEL_PATH", None) or None
        workload_path = getattr(settings, "ML_WORKLOAD_MODEL_PATH", None) or None

        # Convert non-empty strings to Path; fall back to models_dir defaults
        # Directory names match training pipeline (ml_tasks.py)
        pref_path = (
            Path(pref_path) if pref_path else models_dir / "preference_predictor"
        )
        conflict_path = (
            Path(conflict_path) if conflict_path else models_dir / "conflict_predictor"
        )
        workload_path = (
            Path(workload_path) if workload_path else models_dir / "workload_optimizer"
        )

        scorer = ScheduleScorer(
            preference_model_path=pref_path,
            workload_model_path=workload_path,
            conflict_model_path=conflict_path,
            db=None,  # Sync context; scorer uses pre-loaded models only
        )

        # Build schedule dict from state for the scorer
        assignments = state.get("assignments", [])
        residents = state.get("residents", [])
        faculty = state.get("faculty", [])
        templates = state.get("templates", [])

        # Build lookups for enriching ML payloads
        person_type_map = {}
        for p in residents:
            person_type_map[getattr(p, "id", None)] = "resident"
        for p in faculty:
            person_type_map[getattr(p, "id", None)] = "faculty"

        template_name_map = {
            getattr(t, "id", None): getattr(t, "name", "") for t in templates
        }

        def _is_weekend(a: Any) -> bool:
            """Check if assignment falls on a weekend."""
            block = getattr(a, "block", None)
            if block:
                start = getattr(block, "start_date", None)
                if start and hasattr(start, "weekday"):
                    return start.weekday() >= 5
            return False

        schedule_dict: dict[str, Any] = {
            "assignments": [
                {
                    "person": {
                        "id": str(getattr(a, "person_id", "")),
                        "type": person_type_map.get(
                            getattr(a, "person_id", None), "resident"
                        ),
                    },
                    "rotation": {
                        "id": str(getattr(a, "rotation_template_id", "")),
                        "name": template_name_map.get(
                            getattr(a, "rotation_template_id", None), ""
                        ),
                    },
                    "block": {
                        "id": str(getattr(a, "block_id", "")),
                    },
                }
                for a in assignments
            ],
            "people": [
                {
                    "person": {
                        "id": str(getattr(p, "id", "")),
                        "type": person_type_map.get(getattr(p, "id", None), "resident"),
                        "pgy_level": getattr(p, "pgy_level", None),
                        "faculty_role": getattr(p, "faculty_role", None),
                        "target_clinical_blocks": getattr(
                            p, "target_clinical_blocks", None
                        ),
                    },
                    "assignments": [
                        {
                            "rotation_template_id": str(
                                getattr(a, "rotation_template_id", "")
                            ),
                            "rotation_name": template_name_map.get(
                                getattr(a, "rotation_template_id", None), ""
                            ),
                            "block_id": str(getattr(a, "block_id", "")),
                            "is_weekend": _is_weekend(a),
                        }
                        for a in assignments
                        if getattr(a, "person_id", None) == getattr(p, "id", None)
                    ],
                }
                for p in list(residents) + list(faculty)
            ],
            "metadata": {
                "block_number": state.get("block_number"),
                "academic_year": state.get("academic_year"),
                "total_assignments": len(assignments),
            },
        }

        ml_scores = scorer.score_schedule(schedule_dict)
        logger.info(
            f"ML scoring complete: {ml_scores.get('grade', '?')} "
            f"(score={ml_scores.get('overall_score', 0):.3f})"
        )
        return {"ml_scores": ml_scores}

    except Exception as e:
        # ML scoring is advisory — never fail the pipeline
        logger.warning(f"ML scoring failed (non-fatal): {e}")
        return {"ml_scores": {"error": "ml_scoring_unavailable"}}


# ─── Node 13: finalize ───────────────────────────────────────────────


def finalize_node(state: ScheduleGraphState, config: RunnableConfig) -> dict:
    """Update run record, commit, post-resilience check, build result.

    Corresponds to engine.py lines 781-865.
    """
    engine = _get_engine(config)
    create_draft = _get_param(config, "create_draft", False)
    draft_id = state.get("draft_id")

    run = state["run"]
    runtime = time.time() - state["start_time"]
    validation = state["validation"]
    solver_result = state["solver_result"]

    # Step 10: Update run record
    engine._update_run_with_results(run, "cp_sat", validation, runtime, solver_result)

    # Atomic commit
    if create_draft and draft_id:
        logger.info(
            f"Draft mode: Assignments staged in draft {draft_id}. "
            "Publish draft to commit to live assignments."
        )
    engine.db.commit()
    engine.db.refresh(run)

    # Post-generation resilience check
    post_health_report = None
    resilience_warnings: list[str] = []
    if _get_param(config, "check_resilience", True):
        post_health_report = engine._check_post_generation_resilience(
            state["faculty"], state["blocks"], engine.assignments
        )
        resilience_warnings = engine._get_resilience_warnings(post_health_report)

    # Build result message
    if create_draft and draft_id:
        result_message = (
            f"Generated {len(engine.assignments)} assignments using cp_sat. "
            f"Staged in draft {draft_id}."
        )
        result_status = "draft"
    else:
        result_message = f"Generated {len(engine.assignments)} assignments using cp_sat"
        result_status = "success" if validation.valid else "partial"

    context = state.get("context")

    return {
        "post_health_report": post_health_report,
        "resilience_warnings": resilience_warnings,
        "result": {
            "status": result_status,
            "message": result_message,
            "total_assigned": len(engine.assignments),
            "total_blocks": len(state.get("blocks", [])),
            "validation": validation,
            "run_id": state["run_id"],
            "draft_id": draft_id,
            "solver_stats": solver_result.statistics,
            "nf_pc_audit": state.get("nf_pc_audit"),
            "resilience": {
                "pre_generation_status": (
                    engine._pre_health_report.overall_status
                    if engine._pre_health_report
                    else None
                ),
                "post_generation_status": (
                    post_health_report.overall_status if post_health_report else None
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
                    post_health_report.immediate_actions if post_health_report else []
                ),
                "resilience_constraints_active": (
                    context.has_resilience_data() if context else False
                ),
                "hub_faculty_count": (len(context.hub_scores) if context else 0),
            },
            "ml_scores": state.get("ml_scores", {}),
        },
    }
