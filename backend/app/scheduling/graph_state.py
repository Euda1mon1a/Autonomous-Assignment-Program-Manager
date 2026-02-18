"""
LangGraph state definitions for the scheduling pipeline.

These TypedDicts carry intermediate data between graph nodes.
Each node reads what it needs and returns a partial dict of outputs.
"""

from __future__ import annotations

from datetime import date
from typing import Any, TypedDict
from uuid import UUID


class ScheduleGraphConfig(TypedDict, total=False):
    """Configuration passed via LangGraph's configurable mechanism.

    Contains the engine instance and generation parameters that don't
    change between nodes. The engine carries the DB session, constraint
    manager, and resilience service.
    """

    engine: Any  # SchedulingEngine — Any to avoid circular import
    pgy_levels: list[int] | None
    rotation_template_ids: list[UUID] | None
    algorithm: str
    timeout_seconds: float
    check_resilience: bool
    preserve_fmit: bool
    preserve_resident_inpatient: bool
    preserve_absence: bool
    block_number: int | None
    academic_year: int | None
    create_draft: bool
    created_by_id: UUID | None
    validate_pcat_do: bool


class ScheduleGraphState(TypedDict, total=False):
    """Mutable state flowing through the scheduling graph.

    Each node reads from this and returns a partial dict of fields
    it produces. LangGraph merges partial dicts into accumulated state.

    Fields use total=False so nodes only return the fields they set.
    """

    # ── Phase: init ──────────────────────────────────────────────
    start_time: float
    run_id: UUID
    run: Any  # ScheduleRun ORM object

    # ── Phase: load_data ─────────────────────────────────────────
    blocks: list[Any]  # list[Block]
    fmit_assignments: list[Any]  # list[Assignment]
    resident_inpatient_assignments: list[Any]
    absence_assignments: list[Any]
    offsite_assignments: list[Any]
    recovery_assignments: list[Any]
    education_assignments: list[Any]
    preserve_ids: set[UUID]
    block_number: int | None
    academic_year: int | None
    residents: list[Any]  # list[Person]
    faculty: list[Any]  # list[Person]
    templates: list[Any]  # list[RotationTemplate]
    preload_count: int

    # ── Phase: build_context ─────────────────────────────────────
    context: Any  # SchedulingContext
    preserved_assignments: list[Any]  # list[Assignment]

    # ── Phase: pre_validate ──────────────────────────────────────
    pre_validation_passed: bool
    pre_validation_result: Any  # PreSolverValidationResult

    # ── Phase: solve ─────────────────────────────────────────────
    solver_result: Any  # SolverResult

    # ── Phase: persist_and_call ──────────────────────────────────
    assignments: list[Any]  # list[Assignment]
    call_assignments: list[Any]  # list[CallAssignment]
    pcat_do_valid: bool

    # ── Phase: activity_solver ───────────────────────────────────
    activity_result: dict[str, Any]

    # ── Phase: persist_draft_or_live ─────────────────────────────
    draft_id: UUID | None

    # ── Phase: validate ──────────────────────────────────────────
    validation: Any  # ValidationResult
    nf_pc_audit: Any  # NFPCAudit pydantic model
    nf_pc_audit_raw: dict[str, Any]

    # ── Phase: finalize ──────────────────────────────────────────
    post_health_report: Any  # SystemHealthReport
    resilience_warnings: list[str]

    # ── Terminal ─────────────────────────────────────────────────
    result: dict[str, Any]  # Final return dict matching generate()'s output

    # ── Control ──────────────────────────────────────────────────
    failed: bool
    error: str | None
