"""Schedule-related schemas."""
from datetime import date
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SchedulingAlgorithm(str, Enum):
    """Available scheduling algorithms."""
    GREEDY = "greedy"      # Fast heuristic, good for initial solutions
    CP_SAT = "cp_sat"      # OR-Tools constraint programming, optimal solutions
    PULP = "pulp"          # PuLP linear programming, fast for large problems
    HYBRID = "hybrid"      # Combines CP-SAT and PuLP for best results


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
        description="Maximum solver runtime in seconds (5-300)"
    )

    @model_validator(mode='after')
    def validate_date_range(self) -> 'ScheduleRequest':
        """Ensure start_date is before or equal to end_date."""
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be before or equal to "
                f"end_date ({self.end_date})"
            )
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
    total_blocks_assigned: int
    total_blocks: int
    validation: ValidationResult
    run_id: UUID | None = None
    solver_stats: SolverStatistics | None = None
    acgme_override_count: int = 0  # Number of acknowledged ACGME overrides


class EmergencyRequest(BaseModel):
    """Request schema for emergency coverage."""
    person_id: UUID
    start_date: date
    end_date: date
    reason: str
    is_deployment: bool = False


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
    conflict_type: Literal["leave", "conference", "tdy", "training", "deployment", "medical"]
    description: str = ""

    @model_validator(mode='after')
    def validate_dates(self) -> 'ExternalConflictInput':
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self


class SwapFinderRequest(BaseModel):
    """Request schema for finding swap candidates."""
    target_faculty: str = Field(..., description="Faculty member looking to offload a week")
    target_week: date = Field(..., description="Monday of the week to offload")
    faculty_targets: list[FacultyTargetInput] = Field(
        default=[],
        description="Faculty target week allocations (optional - enhances ranking)"
    )
    external_conflicts: list[ExternalConflictInput] = Field(
        default=[],
        description="Known external conflicts (leave, conferences, etc.)"
    )
    include_absence_conflicts: bool = Field(
        default=True,
        description="Cross-reference with database absence records"
    )
    schedule_release_days: int = Field(
        default=90,
        ge=0,
        le=365,
        description="Days ahead that clinic schedules are released"
    )


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
