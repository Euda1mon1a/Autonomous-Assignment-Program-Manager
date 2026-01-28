"""Schedule-related schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.date_validators import validate_academic_year_date


class SchedulingAlgorithm(str, Enum):
    """Available scheduling algorithms."""

    GREEDY = "greedy"  # Fast heuristic, good for initial solutions
    CP_SAT = "cp_sat"  # OR-Tools constraint programming, optimal solutions
    PULP = "pulp"  # PuLP linear programming, fast for large problems
    HYBRID = "hybrid"  # Combines CP-SAT and PuLP for best results


class ScheduleRequest(BaseModel):
    """Request schema for schedule generation."""

    start_date: date
    end_date: date
    pgy_levels: list[int] | None = None  # Filter residents by PGY level
    rotation_template_ids: list[UUID] | None = None  # Specific templates to use
    algorithm: SchedulingAlgorithm = SchedulingAlgorithm.GREEDY
    timeout_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Maximum solver runtime in seconds (5-300)",
    )
    # Block assignment expansion params (Session 095)
    expand_block_assignments: bool = Field(
        default=False,
        description="Deprecated; expansion pipeline removed (ignored).",
    )
    block_number: int | None = Field(
        default=None,
        ge=0,
        le=13,
        description="Academic block number (0-13) for block_assignment expansion",
    )
    academic_year: int | None = Field(
        default=None,
        ge=2020,
        le=2100,
        description="Academic year for block_assignment expansion (e.g., 2025 for AY 2025-2026)",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @model_validator(mode="after")
    def validate_date_range(self) -> "ScheduleRequest":
        """Ensure start_date is before or equal to end_date."""
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be before or equal to "
                f"end_date ({self.end_date})"
            )
        return self

    @model_validator(mode="after")
    def validate_block_expansion_params(self) -> "ScheduleRequest":
        """Deprecated expansion params kept for compatibility."""
        return self


class Violation(BaseModel):
    """Schema for a single ACGME violation."""

    type: str  # 'SUPERVISION_RATIO', '80_HOUR', '1_IN_7', etc.
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    person_id: UUID | None = None
    person_name: str | None = None
    block_id: UUID | None = None
    message: str
    details: dict | None = None


class NFPCAuditViolation(BaseModel):
    """Details for NF -> PC audit violations."""

    person_id: UUID | None = None
    person_name: str | None = None
    nf_date: date | None = None
    pc_required_date: date | None = None
    missing_am_pc: bool = False
    missing_pm_pc: bool = False


class NFPCAudit(BaseModel):
    """Post-generation audit results for Night Float to Post-Call coverage."""

    compliant: bool
    total_nf_transitions: int
    violations: list[NFPCAuditViolation]
    message: str | None = None


class ValidationResult(BaseModel):
    """Schema for ACGME validation results."""

    valid: bool
    total_violations: int
    violations: list[Violation]
    coverage_rate: float  # Percentage of blocks covered
    statistics: dict | None = None


class SolverStatistics(BaseModel):
    """Statistics from the solver run."""

    total_blocks: int | None = None
    total_residents: int | None = None
    coverage_rate: float | None = None
    branches: int | None = None  # CP-SAT specific
    conflicts: int | None = None  # CP-SAT specific


class ScheduleResponse(BaseModel):
    """Response schema for schedule generation."""

    status: str  # 'success', 'partial', 'failed'
    message: str
    # Note: Field stores assignment count, not block count. Exposed as total_assignments
    # in API responses for clarity. DB column remains total_blocks_assigned for backwards
    # compatibility. After axios camelCase conversion, frontend receives totalAssignments.
    total_assignments: int = Field(serialization_alias="total_assignments")
    total_blocks: int
    validation: ValidationResult
    run_id: UUID | None = None
    solver_stats: SolverStatistics | None = None
    nf_pc_audit: NFPCAudit | None = None
    acgme_override_count: int = 0  # Number of acknowledged ACGME overrides

    class Config:
        populate_by_name = True


class EmergencyRequest(BaseModel):
    """Request schema for emergency coverage."""

    person_id: UUID
    start_date: date
    end_date: date
    reason: str
    is_deployment: bool = False

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @model_validator(mode="after")
    def validate_date_order(self) -> "EmergencyRequest":
        """Ensure start_date is before or equal to end_date."""
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be before or equal to "
                f"end_date ({self.end_date})"
            )
        return self


class EmergencyResponse(BaseModel):
    """Response schema for emergency coverage."""

    status: str  # 'success', 'partial', 'failed'
    replacements_found: int
    coverage_gaps: int
    requires_manual_review: bool
    details: list[dict]


# Import/Conflict Analysis Schemas


class ConflictItem(BaseModel):
    """Schema for a single scheduling conflict."""

    provider: str
    date: str
    time: str
    type: str  # 'double_book', 'specialty_unavailable', 'consecutive_weeks'
    severity: str  # 'error', 'warning', 'info'
    message: str
    fmit_assignment: str | None = None
    clinic_assignment: str | None = None


class ScheduleSummary(BaseModel):
    """Summary of an imported schedule."""

    providers: list[str]
    date_range: list[str | None]  # [start, end] as ISO strings
    total_slots: int
    fmit_slots: int = 0
    clinic_slots: int = 0


class Recommendation(BaseModel):
    """Recommendation for resolving conflicts."""

    type: str  # 'consolidate_fmit', 'specialty_coverage', 'resolve_double_booking'
    providers: list[str] | None = None
    count: int | None = None
    message: str


class ConflictSummary(BaseModel):
    """Summary of conflicts found."""

    total_conflicts: int
    errors: int
    warnings: int


class ImportAnalysisResponse(BaseModel):
    """Response schema for schedule import and analysis."""

    success: bool
    error: str | None = None
    fmit_schedule: ScheduleSummary | None = None
    clinic_schedule: ScheduleSummary | None = None
    conflicts: list[ConflictItem] = []
    recommendations: list[Recommendation] = []
    summary: ConflictSummary | None = None


# SwapFinder API Schemas


class FacultyTargetInput(BaseModel):
    """Input schema for faculty target configuration."""

    name: str
    target_weeks: int = Field(default=6, ge=0, le=52)
    role: Literal["faculty", "chief", "pd", "adjunct"] = "faculty"
    current_weeks: int = Field(default=0, ge=0)


class ExternalConflictInput(BaseModel):
    """Input schema for external conflicts (leave, conferences, etc.)."""

    faculty: str
    start_date: date
    end_date: date
    conflict_type: Literal[
        "leave", "conference", "tdy", "training", "deployment", "medical"
    ]
    description: str = ""

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @model_validator(mode="after")
    def validate_dates(self) -> "ExternalConflictInput":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self


class SwapFinderRequest(BaseModel):
    """Request schema for finding swap candidates."""

    target_faculty: str = Field(
        ..., description="Faculty member looking to offload a week"
    )
    target_week: date = Field(..., description="Monday of the week to offload")
    faculty_targets: list[FacultyTargetInput] = Field(
        default=[],
        description="Faculty target week allocations (optional - enhances ranking)",
    )
    external_conflicts: list[ExternalConflictInput] = Field(
        default=[], description="Known external conflicts (leave, conferences, etc.)"
    )
    include_absence_conflicts: bool = Field(
        default=True, description="Cross-reference with database absence records"
    )
    schedule_release_days: int = Field(
        default=90,
        ge=0,
        le=365,
        description="Days ahead that clinic schedules are released",
    )

    @field_validator("target_week")
    @classmethod
    def validate_target_week_in_range(cls, v: date) -> date:
        """Validate target_week is within academic year bounds."""
        return validate_academic_year_date(v, field_name="target_week")


class SwapCandidateResponse(BaseModel):
    """Response schema for a single swap candidate."""

    faculty: str
    can_take_week: str  # ISO date
    gives_week: str | None = None  # ISO date for 1:1 swap
    back_to_back_ok: bool
    external_conflict: str | None = None
    flexibility: str  # "easy", "hard", "very_hard", "impossible"
    reason: str = ""
    rank: int = 0  # 1 = best candidate


class AlternatingPatternInfo(BaseModel):
    """Info about faculty with excessive alternating patterns."""

    faculty: str
    cycle_count: int
    fmit_weeks: list[str]  # ISO dates
    recommendation: str


class SwapFinderResponse(BaseModel):
    """Response schema for swap finder results."""

    success: bool
    target_faculty: str
    target_week: str
    candidates: list[SwapCandidateResponse]
    total_candidates: int
    viable_candidates: int  # Candidates with no back-to-back issues
    alternating_patterns: list[AlternatingPatternInfo] = []
    message: str = ""


# JSON-based swap candidate schemas for MCP integration
class SwapCandidateJsonRequest(BaseModel):
    """Request schema for JSON-based swap candidate lookup (no file upload)."""

    person_id: str
    assignment_id: str | None = None  # Optional: specific assignment
    block_id: str | None = None  # Optional: specific block
    max_candidates: int = Field(default=10, ge=1, le=50)


class SwapCandidateJsonItem(BaseModel):
    """A single swap candidate from JSON-based lookup."""

    candidate_person_id: str
    candidate_name: str
    candidate_role: str  # Role-based identifier (e.g., "Faculty") - no PII
    assignment_id: str | None = None
    block_date: str  # ISO date
    block_session: str  # AM/PM
    match_score: float = Field(ge=0.0, le=1.0)
    rotation_name: str | None = None
    compatibility_factors: dict = Field(default_factory=dict)
    mutual_benefit: bool = False
    approval_likelihood: str = "medium"  # "low", "medium", "high"


class SwapCandidateJsonResponse(BaseModel):
    """Response schema for JSON-based swap candidate lookup."""

    success: bool
    requester_person_id: str
    requester_name: str | None = None
    original_assignment_id: str | None = None
    candidates: list[SwapCandidateJsonItem]
    total_candidates: int
    top_candidate_id: str | None = None
    message: str = ""


# Admin Scheduling Management Schemas


class ScheduleMetrics(BaseModel):
    """Schema for schedule metrics (RunResult in frontend)."""

    run_id: str = Field(alias="runId")
    status: str
    coverage_percent: float = Field(default=0.0, alias="coveragePercent")
    acgme_violations: int = Field(default=0, alias="acgmeViolations")
    fairness_score: float = Field(default=0.0, alias="fairnessScore")
    swap_churn: float = Field(default=0.0, alias="swapChurn")
    runtime_seconds: float = Field(default=0.0, alias="runtimeSeconds")
    stability: float = Field(default=0.0, alias="stability")
    blocks_assigned: int = Field(default=0, alias="blocksAssigned")
    total_blocks: int = Field(default=0, alias="totalBlocks")
    timestamp: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ScheduleRunRead(BaseModel):
    """Schema for reading schedule run history (RunLogEntry in frontend)."""

    id: UUID
    run_id: str | None = Field(default=None, alias="runId")
    algorithm: SchedulingAlgorithm
    timestamp: datetime
    status: str
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    configuration: dict = Field(default_factory=dict)
    result: ScheduleMetrics | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def from_orm(cls, obj: Any) -> "ScheduleRunRead":
        """Custom from_orm to handle field mapping from model."""
        # Use getattr safely as different model versions might exist
        metrics = ScheduleMetrics(
            run_id=str(getattr(obj, "run_id", obj.id)),
            status=getattr(obj, "status", "unknown"),
            coverage_percent=getattr(obj, "coverage_percent", 0.0),
            acgme_violations=getattr(obj, "acgme_violations", 0),
            blocks_assigned=getattr(obj, "total_blocks_assigned", 0),
            total_blocks=getattr(obj, "total_blocks", 0),
            runtime_seconds=getattr(obj, "runtime_seconds", 0.0),
            timestamp=getattr(obj, "created_at", datetime.now()),
        )

        return cls(
            id=getattr(obj, "id", obj.id),
            runId=str(getattr(obj, "run_id", obj.id)),
            algorithm=getattr(obj, "algorithm", "hybrid"),
            timestamp=getattr(obj, "created_at", datetime.now()),
            status=getattr(obj, "status", "unknown"),
            startDate=getattr(obj, "start_date", None),
            endDate=getattr(obj, "end_date", None),
            configuration=getattr(obj, "config_json", {}),
            result=metrics,
            notes=getattr(obj, "notes", None),
            tags=getattr(obj, "tags", []),
        )

    class Config:
        from_attributes = True
        populate_by_name = True


class ScheduleRunsResponse(BaseModel):
    """Response schema for schedule run history list."""

    runs: list[ScheduleRunRead]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    class Config:
        from_attributes = True
        populate_by_name = True


class RollbackPoint(BaseModel):
    """Schema for schedule rollback points."""

    id: UUID
    created_at: datetime
    created_by: str | None = None
    description: str
    run_id: UUID | None = None
    assignment_count: int
    can_revert: bool = True


class SyncMetadata(BaseModel):
    """Schema for external system sync metadata."""

    last_sync_time: datetime | None = None
    sync_status: str  # 'synced', 'pending', 'error'
    source_system: str
    records_affected: int = 0


# ============================================================================
# Experiment Queue Schemas (for Admin Scheduling Lab)
# ============================================================================


class ExperimentRunStatus(str, Enum):
    """Status of an experiment run in the queue."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentRunResult(BaseModel):
    """Result of a completed experiment run."""

    run_id: str = Field(alias="runId")
    status: str  # 'success', 'partial', 'failed'
    coverage_percent: float = Field(alias="coveragePercent")
    acgme_violations: int = Field(alias="acgmeViolations")
    fairness_score: float = Field(default=0.0, alias="fairnessScore")
    swap_churn: float = Field(default=0.0, alias="swapChurn")
    runtime_seconds: float = Field(alias="runtimeSeconds")
    stability: float = Field(default=1.0)
    blocks_assigned: int = Field(alias="blocksAssigned")
    total_blocks: int = Field(alias="totalBlocks")
    timestamp: datetime

    class Config:
        populate_by_name = True


class ExperimentRunConfiguration(BaseModel):
    """Configuration for an experiment run."""

    algorithm: str
    constraints: list[dict] = Field(default_factory=list)
    preserve_fmit: bool = Field(default=True, alias="preserveFMIT")
    nf_post_call_enabled: bool = Field(default=True, alias="nfPostCallEnabled")
    academic_year: str = Field(alias="academicYear")
    block_range: dict = Field(alias="blockRange")
    timeout_seconds: int = Field(alias="timeoutSeconds")
    dry_run: bool = Field(default=False, alias="dryRun")

    class Config:
        populate_by_name = True


class ExperimentRunResponse(BaseModel):
    """Schema for an experiment run (ExperimentRun in frontend)."""

    id: str
    name: str
    status: ExperimentRunStatus
    configuration: ExperimentRunConfiguration
    queued_at: datetime = Field(alias="queuedAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    progress: float | None = None  # 0.0 to 1.0
    result: ExperimentRunResult | None = None

    class Config:
        populate_by_name = True

    @classmethod
    def from_schedule_run(cls, obj: Any) -> "ExperimentRunResponse":
        """Convert a ScheduleRun model to ExperimentRunResponse."""
        config_json = getattr(obj, "config_json", {}) or {}

        # Build configuration from config_json
        configuration = ExperimentRunConfiguration(
            algorithm=getattr(obj, "algorithm", "hybrid"),
            constraints=config_json.get("constraints", []),
            # Handle both camelCase (frontend) and snake_case (legacy) keys
            preserve_fmit=config_json.get(
                "preserveFMIT", config_json.get("preserve_fmit", True)
            ),
            nf_post_call_enabled=config_json.get(
                "nfPostCallEnabled", config_json.get("nf_post_call", True)
            ),
            academic_year=config_json.get(
                "academicYear", config_json.get("academic_year", "2025-2026")
            ),
            block_range=config_json.get("block_range", {"start": 1, "end": 26}),
            timeout_seconds=config_json.get("timeout_seconds", 60),
            dry_run=config_json.get("dry_run", False),
        )

        # Build result if completed
        result = None
        status_str = getattr(obj, "status", "queued")
        if status_str in ("success", "partial", "failed", "completed"):
            result = ExperimentRunResult(
                run_id=str(obj.id),
                status=status_str if status_str != "completed" else "success",
                coverage_percent=getattr(obj, "coverage_percent", 0.0) or 0.0,
                acgme_violations=getattr(obj, "acgme_violations", 0) or 0,
                fairness_score=getattr(obj, "fairness_score", 0.0) or 0.0,
                swap_churn=getattr(obj, "swap_churn", 0.0) or 0.0,
                runtime_seconds=float(getattr(obj, "runtime_seconds", 0.0) or 0.0),
                stability=getattr(obj, "stability", 1.0) or 1.0,
                blocks_assigned=getattr(obj, "total_blocks_assigned", 0) or 0,
                total_blocks=getattr(obj, "total_blocks", 0) or 0,
                timestamp=getattr(obj, "created_at", datetime.now()),
            )

        # Map status (in_progress is the DB status when solver is actively running)
        status_map = {
            "queued": ExperimentRunStatus.QUEUED,
            "pending": ExperimentRunStatus.QUEUED,
            "in_progress": ExperimentRunStatus.RUNNING,
            "running": ExperimentRunStatus.RUNNING,
            "success": ExperimentRunStatus.COMPLETED,
            "partial": ExperimentRunStatus.COMPLETED,
            "completed": ExperimentRunStatus.COMPLETED,
            "failed": ExperimentRunStatus.FAILED,
            "cancelled": ExperimentRunStatus.CANCELLED,
        }
        status = status_map.get(status_str, ExperimentRunStatus.QUEUED)

        return cls(
            id=str(obj.id),
            name=config_json.get("name", f"Run {str(obj.id)[:8]}"),
            status=status,
            configuration=configuration,
            queued_at=getattr(obj, "created_at", datetime.now()),
            started_at=getattr(obj, "started_at", None),
            completed_at=getattr(obj, "completed_at", None),
            progress=getattr(obj, "progress", None),
            result=result,
        )


class RunQueueResponse(BaseModel):
    """Schema for experiment run queue (RunQueue in frontend)."""

    runs: list[ExperimentRunResponse]
    max_concurrent: int = Field(default=2, alias="maxConcurrent")
    currently_running: int = Field(default=0, alias="currentlyRunning")

    class Config:
        populate_by_name = True


class QueueBatchRequest(BaseModel):
    """Request to queue multiple experiment configurations."""

    configurations: list[dict]
