"""
Tool definitions for the Scheduler MCP server.

Tools enable active operations like validation, analysis, and simulation.
They can modify state or perform complex computations.
"""

import logging
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Request/Response Models


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """A single validation issue."""

    severity: ValidationSeverity
    rule_type: str
    person_id: str | None = None
    person_name: str | None = None
    date_range: tuple[date, date] | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    suggested_fix: str | None = None


class ScheduleValidationRequest(BaseModel):
    """Request to validate a schedule."""

    start_date: date
    end_date: date
    check_work_hours: bool = True
    check_supervision: bool = True
    check_rest_periods: bool = True
    check_consecutive_duty: bool = True


class ScheduleValidationResult(BaseModel):
    """Result of schedule validation."""

    is_valid: bool
    overall_compliance_rate: float = Field(ge=0.0, le=1.0)
    total_issues: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    issues: list[ValidationIssue]
    validated_at: datetime
    date_range: tuple[date, date]


class ContingencyScenario(str, Enum):
    """Types of contingency scenarios."""

    FACULTY_ABSENCE = "faculty_absence"
    RESIDENT_ABSENCE = "resident_absence"
    EMERGENCY_COVERAGE = "emergency_coverage"
    MASS_ABSENCE = "mass_absence"


class ContingencyRequest(BaseModel):
    """Request to run contingency analysis."""

    scenario: ContingencyScenario
    affected_person_ids: list[str]
    start_date: date
    end_date: date
    auto_resolve: bool = False


class ImpactAssessment(BaseModel):
    """Assessment of contingency impact."""

    affected_rotations: list[str]
    coverage_gaps: int
    compliance_violations: int
    workload_increase_percent: float
    feasibility_score: float = Field(ge=0.0, le=1.0)
    critical_gaps: list[str]


class ResolutionOption(BaseModel):
    """A possible resolution for a contingency."""

    option_id: str
    strategy: str
    description: str
    affected_people: list[str]
    estimated_effort: str  # "low", "medium", "high"
    success_probability: float = Field(ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)


class ContingencyAnalysisResult(BaseModel):
    """Result of contingency analysis."""

    scenario: ContingencyScenario
    impact: ImpactAssessment
    resolution_options: list[ResolutionOption]
    recommended_option_id: str | None = None
    analyzed_at: datetime


class ConflictType(str, Enum):
    """Types of scheduling conflicts."""

    DOUBLE_BOOKING = "double_booking"
    WORK_HOUR_VIOLATION = "work_hour_violation"
    REST_PERIOD_VIOLATION = "rest_period_violation"
    SUPERVISION_GAP = "supervision_gap"
    LEAVE_OVERLAP = "leave_overlap"
    CREDENTIAL_MISMATCH = "credential_mismatch"


class ConflictDetectionRequest(BaseModel):
    """Request to detect conflicts."""

    start_date: date
    end_date: date
    conflict_types: list[ConflictType] | None = None
    include_auto_resolution: bool = True


class ConflictInfo(BaseModel):
    """Information about a detected conflict."""

    conflict_id: str
    conflict_type: ConflictType
    severity: ValidationSeverity
    affected_people: list[str]
    date_range: tuple[date, date]
    description: str
    auto_resolution_available: bool
    resolution_options: list[ResolutionOption] = Field(default_factory=list)


class ConflictDetectionResult(BaseModel):
    """Result of conflict detection."""

    total_conflicts: int
    conflicts_by_type: dict[ConflictType, int]
    conflicts: list[ConflictInfo]
    auto_resolvable_count: int
    detected_at: datetime


class SwapCandidateRequest(BaseModel):
    """Request to analyze swap candidates."""

    requester_person_id: str
    assignment_id: str
    preferred_date_range: tuple[date, date] | None = None
    max_candidates: int = Field(default=10, ge=1, le=50)


class SwapCandidate(BaseModel):
    """A potential swap candidate."""

    candidate_person_id: str
    candidate_name: str
    assignment_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    rotation: str
    date_range: tuple[date, date]
    compatibility_factors: dict[str, Any]
    mutual_benefit: bool
    approval_likelihood: str  # "low", "medium", "high"


class SwapAnalysisResult(BaseModel):
    """Result of swap candidate analysis."""

    requester_person_id: str
    original_assignment_id: str
    candidates: list[SwapCandidate]
    top_candidate_id: str | None = None
    analyzed_at: datetime


# Tool Functions


async def validate_schedule(
    request: ScheduleValidationRequest,
) -> ScheduleValidationResult:
    """
    Validate a schedule against ACGME regulations and institutional policies.

    This tool performs comprehensive validation of work hours, supervision
    requirements, rest periods, and consecutive duty restrictions.

    Args:
        request: Validation request with date range and check options

    Returns:
        ScheduleValidationResult with all identified issues and compliance metrics

    Raises:
        ValueError: If date range is invalid
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(
        f"Validating schedule from {request.start_date} to {request.end_date}"
    )

    # TODO: Replace with actual validation logic from backend
    # This is a placeholder implementation
    issues: list[ValidationIssue] = []

    if request.check_work_hours:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type="work_hour_limit",
                person_id="person-003",
                person_name="Dr. Williams",
                date_range=(request.start_date, request.end_date),
                message="Approaching 80-hour weekly limit",
                details={"projected_hours": 78, "limit": 80},
                suggested_fix="Reduce assignment hours or redistribute workload",
            )
        )

    critical_count = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
    warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
    info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)

    return ScheduleValidationResult(
        is_valid=(critical_count == 0),
        overall_compliance_rate=0.95,
        total_issues=len(issues),
        critical_issues=critical_count,
        warning_issues=warning_count,
        info_issues=info_count,
        issues=issues,
        validated_at=datetime.now(),
        date_range=(request.start_date, request.end_date),
    )


async def run_contingency_analysis(
    request: ContingencyRequest,
) -> ContingencyAnalysisResult:
    """
    Run contingency analysis for workforce planning scenarios.

    This tool simulates various absence or emergency scenarios and identifies
    their impact on schedule coverage, compliance, and workload distribution.
    It can also suggest resolution strategies.

    Args:
        request: Contingency request with scenario type and affected personnel

    Returns:
        ContingencyAnalysisResult with impact assessment and resolution options

    Raises:
        ValueError: If request parameters are invalid
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    if not request.affected_person_ids:
        raise ValueError("Must specify at least one affected person")

    logger.info(
        f"Running {request.scenario} contingency analysis for "
        f"{len(request.affected_person_ids)} people"
    )

    # TODO: Replace with actual contingency analysis logic
    # This is a placeholder implementation
    impact = ImpactAssessment(
        affected_rotations=["Emergency Medicine", "Internal Medicine"],
        coverage_gaps=3,
        compliance_violations=1,
        workload_increase_percent=15.5,
        feasibility_score=0.75,
        critical_gaps=["Night shift EM on 2025-01-15"],
    )

    resolution_options = [
        ResolutionOption(
            option_id="res-001",
            strategy="swap_assignment",
            description="Swap with Dr. Martinez from cardiology rotation",
            affected_people=["person-004", "person-005"],
            estimated_effort="medium",
            success_probability=0.85,
            details={
                "swap_date": "2025-01-15",
                "requires_approval": True,
            },
        ),
        ResolutionOption(
            option_id="res-002",
            strategy="reassign_to_backup",
            description="Assign backup faculty from coverage pool",
            affected_people=["person-006"],
            estimated_effort="low",
            success_probability=0.95,
            details={
                "backup_pool_size": 3,
                "immediate_availability": True,
            },
        ),
    ]

    return ContingencyAnalysisResult(
        scenario=request.scenario,
        impact=impact,
        resolution_options=resolution_options,
        recommended_option_id="res-002",
        analyzed_at=datetime.now(),
    )


async def detect_conflicts(
    request: ConflictDetectionRequest,
) -> ConflictDetectionResult:
    """
    Detect scheduling conflicts and identify auto-resolution options.

    This tool scans the schedule for various types of conflicts including
    double-bookings, work hour violations, and supervision gaps. It can
    optionally suggest automatic resolution strategies.

    Args:
        request: Conflict detection request with date range and options

    Returns:
        ConflictDetectionResult with all detected conflicts and resolutions

    Raises:
        ValueError: If date range is invalid
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(
        f"Detecting conflicts from {request.start_date} to {request.end_date}"
    )

    # TODO: Replace with actual conflict detection logic
    # This is a placeholder implementation
    conflicts: list[ConflictInfo] = []

    check_types = request.conflict_types or list(ConflictType)

    if ConflictType.DOUBLE_BOOKING in check_types:
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-001",
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ValidationSeverity.CRITICAL,
                affected_people=["person-007"],
                date_range=(request.start_date, request.start_date),
                description="Person assigned to two rotations simultaneously",
                auto_resolution_available=True,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-003",
                        strategy="remove_duplicate",
                        description="Remove duplicate assignment",
                        affected_people=["person-007"],
                        estimated_effort="low",
                        success_probability=1.0,
                    )
                ],
            )
        )

    conflicts_by_type = {
        ctype: sum(1 for c in conflicts if c.conflict_type == ctype)
        for ctype in ConflictType
    }

    auto_resolvable = sum(1 for c in conflicts if c.auto_resolution_available)

    return ConflictDetectionResult(
        total_conflicts=len(conflicts),
        conflicts_by_type=conflicts_by_type,
        conflicts=conflicts,
        auto_resolvable_count=auto_resolvable,
        detected_at=datetime.now(),
    )


async def analyze_swap_candidates(
    request: SwapCandidateRequest,
) -> SwapAnalysisResult:
    """
    Analyze potential swap candidates for schedule change requests.

    This tool uses intelligent matching to find optimal swap partners based on
    rotation compatibility, schedule flexibility, mutual benefit, and
    historical swap patterns.

    Args:
        request: Swap candidate request with requester and assignment details

    Returns:
        SwapAnalysisResult with ranked candidates and compatibility scores

    Raises:
        ValueError: If request parameters are invalid
    """
    logger.info(
        f"Analyzing swap candidates for person {request.requester_person_id}"
    )

    # TODO: Replace with actual swap matching logic
    # This is a placeholder implementation
    candidates = [
        SwapCandidate(
            candidate_person_id="person-008",
            candidate_name="Dr. Chen",
            assignment_id="assign-008",
            match_score=0.92,
            rotation="Emergency Medicine",
            date_range=(date(2025, 1, 15), date(2025, 1, 21)),
            compatibility_factors={
                "rotation_match": True,
                "pgy_level_compatible": True,
                "schedule_flexibility": "high",
                "past_swaps": 2,
            },
            mutual_benefit=True,
            approval_likelihood="high",
        ),
        SwapCandidate(
            candidate_person_id="person-009",
            candidate_name="Dr. Patel",
            assignment_id="assign-009",
            match_score=0.78,
            rotation="Internal Medicine",
            date_range=(date(2025, 1, 15), date(2025, 1, 21)),
            compatibility_factors={
                "rotation_match": False,
                "pgy_level_compatible": True,
                "schedule_flexibility": "medium",
                "past_swaps": 0,
            },
            mutual_benefit=False,
            approval_likelihood="medium",
        ),
    ]

    # Sort by match score
    candidates.sort(key=lambda c: c.match_score, reverse=True)

    top_candidate_id = candidates[0].candidate_person_id if candidates else None

    return SwapAnalysisResult(
        requester_person_id=request.requester_person_id,
        original_assignment_id=request.assignment_id,
        candidates=candidates[: request.max_candidates],
        top_candidate_id=top_candidate_id,
        analyzed_at=datetime.now(),
    )
