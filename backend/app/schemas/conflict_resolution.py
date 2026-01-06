"""Schemas for conflict auto-resolution."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Conflict List Response Schemas (for paginated list endpoint)
# ============================================================================


class ConflictSeverity(str, Enum):
    """Severity level of a conflict."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(str, Enum):
    """Type of schedule conflict."""

    SCHEDULING_OVERLAP = "scheduling_overlap"
    ACGME_VIOLATION = "acgme_violation"
    SUPERVISION_MISSING = "supervision_missing"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    ABSENCE_CONFLICT = "absence_conflict"
    QUALIFICATION_MISMATCH = "qualification_mismatch"
    CONSECUTIVE_DUTY = "consecutive_duty"
    REST_PERIOD = "rest_period"
    COVERAGE_GAP = "coverage_gap"
    # Legacy types from ConflictAlert model
    LEAVE_FMIT_OVERLAP = "leave_fmit_overlap"
    BACK_TO_BACK = "back_to_back"
    EXCESSIVE_ALTERNATING = "excessive_alternating"
    CALL_CASCADE = "call_cascade"
    EXTERNAL_COMMITMENT = "external_commitment"


class ConflictStatus(str, Enum):
    """Status of a conflict."""

    UNRESOLVED = "unresolved"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    # Legacy statuses from ConflictAlert model
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"


class ConflictResponse(BaseModel):
    """Response schema for a single conflict in the list."""

    id: UUID
    type: str
    severity: str
    status: str
    title: str
    description: str

    # Affected entities
    affected_person_ids: list[UUID] = Field(default_factory=list)
    affected_assignment_ids: list[UUID] = Field(default_factory=list)
    affected_block_ids: list[UUID] = Field(default_factory=list)

    # Time context
    conflict_date: date
    conflict_session: str | None = None  # AM/PM

    # Detection metadata
    detected_at: datetime
    detected_by: str = "system"
    rule_id: str | None = None

    # Resolution info
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_method: str | None = None
    resolution_notes: str | None = None

    # Additional context
    details: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConflictListResponse(BaseModel):
    """Paginated response for conflicts list."""

    items: list[ConflictResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Resolution Strategy Schemas
# ============================================================================


class ResolutionStrategyEnum(str, Enum):
    """Resolution strategies for conflicts."""

    SWAP_ASSIGNMENTS = "swap_assignments"
    REASSIGN_JUNIOR = "reassign_junior"
    SPLIT_COVERAGE = "split_coverage"
    ESCALATE_TO_BACKUP = "escalate_to_backup"
    DEFER_TO_HUMAN = "defer_to_human"


class ResolutionStatusEnum(str, Enum):
    """Status of a resolution attempt."""

    PROPOSED = "proposed"
    ANALYZING = "analyzing"
    VALIDATED = "validated"
    APPLIED = "applied"
    FAILED = "failed"
    REJECTED = "rejected"


class SafetyCheckType(str, Enum):
    """Types of safety checks performed before auto-resolution."""

    ACGME_COMPLIANCE = "acgme_compliance"
    COVERAGE_GAP = "coverage_gap"
    FACULTY_AVAILABILITY = "faculty_availability"
    SUPERVISION_RATIO = "supervision_ratio"
    WORKLOAD_BALANCE = "workload_balance"


class SafetyCheckResult(BaseModel):
    """Result of a safety check."""

    check_type: SafetyCheckType
    passed: bool
    message: str
    details: dict = Field(default_factory=dict)


class ConflictAnalysis(BaseModel):
    """Analysis of a conflict for resolution planning."""

    conflict_id: UUID
    conflict_type: str
    severity: str

    # Analysis results
    root_cause: str
    affected_faculty: list[UUID]
    affected_dates: list[str]  # ISO format dates
    complexity_score: float = Field(ge=0.0, le=1.0, description="0=simple, 1=complex")

    # Safety considerations
    safety_checks: list[SafetyCheckResult] = Field(default_factory=list)
    all_checks_passed: bool = True
    auto_resolution_safe: bool = True

    # Constraints
    constraints: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    # Recommendations
    recommended_strategies: list[ResolutionStrategyEnum] = Field(default_factory=list)
    estimated_resolution_time: int = Field(
        default=0, description="Estimated minutes to resolve"
    )

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ImpactAssessment(BaseModel):
    """Assessment of resolution impact."""

    affected_faculty_count: int = 0
    affected_weeks_count: int = 0
    affected_blocks_count: int = 0

    # Conflict analysis
    new_conflicts_created: int = 0
    conflicts_resolved: int = 1
    cascading_changes_required: int = 0

    # Quality metrics
    workload_balance_score: float = Field(
        ge=0.0, le=1.0, description="0=poor, 1=excellent"
    )
    fairness_score: float = Field(ge=0.0, le=1.0, description="0=unfair, 1=fair")
    disruption_score: float = Field(ge=0.0, le=1.0, description="0=minimal, 1=severe")

    # Feasibility
    feasibility_score: float = Field(
        ge=0.0, le=1.0, description="0=infeasible, 1=highly feasible"
    )
    confidence_level: float = Field(
        ge=0.0, le=1.0, description="Model confidence in assessment"
    )

    # Summary
    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall resolution quality score"
    )
    recommendation: str


class ResolutionOption(BaseModel):
    """A possible resolution for a conflict."""

    id: str
    conflict_id: UUID
    strategy: ResolutionStrategyEnum

    # Description
    title: str
    description: str
    detailed_steps: list[str] = Field(default_factory=list)

    # Resolution details
    changes: dict = Field(default_factory=dict, description="Specific changes to make")
    prerequisites: list[str] = Field(default_factory=list)

    # Impact and safety
    impact: ImpactAssessment | None = None
    safety_validated: bool = False
    safety_issues: list[str] = Field(default_factory=list)

    # Status
    status: ResolutionStatusEnum = ResolutionStatusEnum.PROPOSED
    can_auto_apply: bool = False
    requires_approval: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration: int = Field(default=0, description="Estimated minutes to apply")
    risk_level: str = Field(default="medium", description="low, medium, high")


class ResolutionResult(BaseModel):
    """Result of applying a resolution."""

    resolution_option_id: str
    conflict_id: UUID
    strategy: ResolutionStrategyEnum

    # Outcome
    success: bool
    status: ResolutionStatusEnum
    message: str

    # Changes made
    changes_applied: list[str] = Field(default_factory=list)
    entities_modified: dict = Field(
        default_factory=dict, description="Map of entity type to list of IDs modified"
    )

    # Post-resolution state
    conflict_resolved: bool = False
    new_conflicts_created: list[UUID] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Timing
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    applied_by_id: UUID | None = None
    duration_seconds: float | None = None

    # Rollback capability
    can_rollback: bool = False
    rollback_instructions: str | None = None

    # Error information (if failed)
    error_code: str | None = None
    error_details: dict = Field(default_factory=dict)

    # Follow-up actions
    follow_up_required: bool = False
    follow_up_actions: list[str] = Field(default_factory=list)


class BatchResolutionRequest(BaseModel):
    """Request to auto-resolve multiple conflicts."""

    conflict_ids: list[UUID] = Field(min_length=1)
    strategy_preference: ResolutionStrategyEnum | None = None
    auto_apply_safe: bool = Field(
        default=False,
        description="Automatically apply resolutions that pass all safety checks",
    )
    max_risk_level: str = Field(
        default="medium", description="Maximum acceptable risk: low, medium, high"
    )
    require_approval: bool = Field(
        default=True, description="Require human approval before applying"
    )


class BatchResolutionReport(BaseModel):
    """Report of batch auto-resolution results."""

    # Request info
    total_conflicts: int
    conflicts_analyzed: int

    # Resolution outcomes
    resolutions_proposed: int = 0
    resolutions_applied: int = 0
    resolutions_failed: int = 0
    resolutions_deferred: int = 0

    # Details
    results: list[ResolutionResult] = Field(default_factory=list)
    pending_approvals: list[ResolutionOption] = Field(default_factory=list)
    failed_conflicts: list[UUID] = Field(default_factory=list)

    # Aggregate impact
    total_faculty_affected: int = 0
    total_changes_made: int = 0
    new_conflicts_created: int = 0

    # Safety summary
    safety_checks_performed: int = 0
    safety_checks_passed: int = 0
    safety_checks_failed: int = 0

    # Performance
    processing_time_seconds: float
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Summary
    success_rate: float = Field(ge=0.0, le=1.0)
    overall_status: str  # "completed", "partial", "failed"
    summary_message: str
    recommendations: list[str] = Field(default_factory=list)


class AutoResolutionConfig(BaseModel):
    """Configuration for auto-resolution behavior."""

    enabled: bool = True

    # Strategy preferences
    preferred_strategies: list[ResolutionStrategyEnum] = Field(
        default_factory=lambda: [
            ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
            ResolutionStrategyEnum.REASSIGN_JUNIOR,
            ResolutionStrategyEnum.ESCALATE_TO_BACKUP,
        ]
    )

    # Safety thresholds
    min_feasibility_score: float = Field(default=0.7, ge=0.0, le=1.0)
    max_disruption_score: float = Field(default=0.3, ge=0.0, le=1.0)
    min_confidence_level: float = Field(default=0.8, ge=0.0, le=1.0)

    # Limits
    max_affected_faculty: int = Field(default=5, gt=0)
    max_cascading_changes: int = Field(default=3, gt=0)
    max_batch_size: int = Field(default=20, gt=0)

    # Auto-apply rules
    auto_apply_low_risk: bool = True
    auto_apply_medium_risk: bool = False
    auto_apply_high_risk: bool = False
    require_approval_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
