"""Schemas for conflict auto-resolution."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


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

    ***REMOVED*** Analysis results
    root_cause: str
    affected_faculty: list[UUID]
    affected_dates: list[str]  ***REMOVED*** ISO format dates
    complexity_score: float = Field(ge=0.0, le=1.0, description="0=simple, 1=complex")

    ***REMOVED*** Safety considerations
    safety_checks: list[SafetyCheckResult] = Field(default_factory=list)
    all_checks_passed: bool = True
    auto_resolution_safe: bool = True

    ***REMOVED*** Constraints
    constraints: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    ***REMOVED*** Recommendations
    recommended_strategies: list[ResolutionStrategyEnum] = Field(default_factory=list)
    estimated_resolution_time: int = Field(
        default=0, description="Estimated minutes to resolve"
    )

    ***REMOVED*** Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ImpactAssessment(BaseModel):
    """Assessment of resolution impact."""

    affected_faculty_count: int = 0
    affected_weeks_count: int = 0
    affected_blocks_count: int = 0

    ***REMOVED*** Conflict analysis
    new_conflicts_created: int = 0
    conflicts_resolved: int = 1
    cascading_changes_required: int = 0

    ***REMOVED*** Quality metrics
    workload_balance_score: float = Field(
        ge=0.0, le=1.0, description="0=poor, 1=excellent"
    )
    fairness_score: float = Field(ge=0.0, le=1.0, description="0=unfair, 1=fair")
    disruption_score: float = Field(ge=0.0, le=1.0, description="0=minimal, 1=severe")

    ***REMOVED*** Feasibility
    feasibility_score: float = Field(
        ge=0.0, le=1.0, description="0=infeasible, 1=highly feasible"
    )
    confidence_level: float = Field(
        ge=0.0, le=1.0, description="Model confidence in assessment"
    )

    ***REMOVED*** Summary
    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall resolution quality score"
    )
    recommendation: str


class ResolutionOption(BaseModel):
    """A possible resolution for a conflict."""

    id: str
    conflict_id: UUID
    strategy: ResolutionStrategyEnum

    ***REMOVED*** Description
    title: str
    description: str
    detailed_steps: list[str] = Field(default_factory=list)

    ***REMOVED*** Resolution details
    changes: dict = Field(default_factory=dict, description="Specific changes to make")
    prerequisites: list[str] = Field(default_factory=list)

    ***REMOVED*** Impact and safety
    impact: ImpactAssessment | None = None
    safety_validated: bool = False
    safety_issues: list[str] = Field(default_factory=list)

    ***REMOVED*** Status
    status: ResolutionStatusEnum = ResolutionStatusEnum.PROPOSED
    can_auto_apply: bool = False
    requires_approval: bool = True

    ***REMOVED*** Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration: int = Field(default=0, description="Estimated minutes to apply")
    risk_level: str = Field(default="medium", description="low, medium, high")


class ResolutionResult(BaseModel):
    """Result of applying a resolution."""

    resolution_option_id: str
    conflict_id: UUID
    strategy: ResolutionStrategyEnum

    ***REMOVED*** Outcome
    success: bool
    status: ResolutionStatusEnum
    message: str

    ***REMOVED*** Changes made
    changes_applied: list[str] = Field(default_factory=list)
    entities_modified: dict = Field(
        default_factory=dict, description="Map of entity type to list of IDs modified"
    )

    ***REMOVED*** Post-resolution state
    conflict_resolved: bool = False
    new_conflicts_created: list[UUID] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    ***REMOVED*** Timing
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    applied_by_id: UUID | None = None
    duration_seconds: float | None = None

    ***REMOVED*** Rollback capability
    can_rollback: bool = False
    rollback_instructions: str | None = None

    ***REMOVED*** Error information (if failed)
    error_code: str | None = None
    error_details: dict = Field(default_factory=dict)

    ***REMOVED*** Follow-up actions
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

    ***REMOVED*** Request info
    total_conflicts: int
    conflicts_analyzed: int

    ***REMOVED*** Resolution outcomes
    resolutions_proposed: int = 0
    resolutions_applied: int = 0
    resolutions_failed: int = 0
    resolutions_deferred: int = 0

    ***REMOVED*** Details
    results: list[ResolutionResult] = Field(default_factory=list)
    pending_approvals: list[ResolutionOption] = Field(default_factory=list)
    failed_conflicts: list[UUID] = Field(default_factory=list)

    ***REMOVED*** Aggregate impact
    total_faculty_affected: int = 0
    total_changes_made: int = 0
    new_conflicts_created: int = 0

    ***REMOVED*** Safety summary
    safety_checks_performed: int = 0
    safety_checks_passed: int = 0
    safety_checks_failed: int = 0

    ***REMOVED*** Performance
    processing_time_seconds: float
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    ***REMOVED*** Summary
    success_rate: float = Field(ge=0.0, le=1.0)
    overall_status: str  ***REMOVED*** "completed", "partial", "failed"
    summary_message: str
    recommendations: list[str] = Field(default_factory=list)


class AutoResolutionConfig(BaseModel):
    """Configuration for auto-resolution behavior."""

    enabled: bool = True

    ***REMOVED*** Strategy preferences
    preferred_strategies: list[ResolutionStrategyEnum] = Field(
        default_factory=lambda: [
            ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
            ResolutionStrategyEnum.REASSIGN_JUNIOR,
            ResolutionStrategyEnum.ESCALATE_TO_BACKUP,
        ]
    )

    ***REMOVED*** Safety thresholds
    min_feasibility_score: float = Field(default=0.7, ge=0.0, le=1.0)
    max_disruption_score: float = Field(default=0.3, ge=0.0, le=1.0)
    min_confidence_level: float = Field(default=0.8, ge=0.0, le=1.0)

    ***REMOVED*** Limits
    max_affected_faculty: int = Field(default=5, gt=0)
    max_cascading_changes: int = Field(default=3, gt=0)
    max_batch_size: int = Field(default=20, gt=0)

    ***REMOVED*** Auto-apply rules
    auto_apply_low_risk: bool = True
    auto_apply_medium_risk: bool = False
    auto_apply_high_risk: bool = False
    require_approval_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
