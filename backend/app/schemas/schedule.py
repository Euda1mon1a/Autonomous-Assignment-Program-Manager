"""Schedule-related schemas."""
from datetime import date
from enum import Enum
from typing import Optional, Literal
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
    pgy_levels: Optional[list[int]] = None  # Filter residents by PGY level
    rotation_template_ids: Optional[list[UUID]] = None  # Specific templates to use
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
    person_id: Optional[UUID] = None
    person_name: Optional[str] = None
    block_id: Optional[UUID] = None
    message: str
    details: Optional[dict] = None


class ValidationResult(BaseModel):
    """Schema for ACGME validation results."""
    valid: bool
    total_violations: int
    violations: list[Violation]
    coverage_rate: float  # Percentage of blocks covered
    statistics: Optional[dict] = None


class SolverStatistics(BaseModel):
    """Statistics from the solver run."""
    total_blocks: Optional[int] = None
    total_residents: Optional[int] = None
    coverage_rate: Optional[float] = None
    branches: Optional[int] = None  # CP-SAT specific
    conflicts: Optional[int] = None  # CP-SAT specific


class ScheduleResponse(BaseModel):
    """Response schema for schedule generation."""
    status: str  # 'success', 'partial', 'failed'
    message: str
    total_blocks_assigned: int
    total_blocks: int
    validation: ValidationResult
    run_id: Optional[UUID] = None
    solver_stats: Optional[SolverStatistics] = None
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
    fmit_assignment: Optional[str] = None
    clinic_assignment: Optional[str] = None


class ScheduleSummary(BaseModel):
    """Summary of an imported schedule."""
    providers: list[str]
    date_range: list[Optional[str]]  # [start, end] as ISO strings
    total_slots: int
    fmit_slots: int = 0
    clinic_slots: int = 0


class Recommendation(BaseModel):
    """Recommendation for resolving conflicts."""
    type: str  # 'consolidate_fmit', 'specialty_coverage', 'resolve_double_booking'
    providers: Optional[list[str]] = None
    count: Optional[int] = None
    message: str


class ConflictSummary(BaseModel):
    """Summary of conflicts found."""
    total_conflicts: int
    errors: int
    warnings: int


class ImportAnalysisResponse(BaseModel):
    """Response schema for schedule import and analysis."""
    success: bool
    error: Optional[str] = None
    fmit_schedule: Optional[ScheduleSummary] = None
    clinic_schedule: Optional[ScheduleSummary] = None
    conflicts: list[ConflictItem] = []
    recommendations: list[Recommendation] = []
    summary: Optional[ConflictSummary] = None
