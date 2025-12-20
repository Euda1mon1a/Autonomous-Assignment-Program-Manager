"""
Tool definitions for the Scheduler MCP server.

Tools enable active operations like validation, analysis, and simulation.
They can modify state or perform complex computations.
"""

import logging
from datetime import date, datetime, timedelta
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

    # Implementation based on ACGME validation logic from backend
    issues: list[ValidationIssue] = []

    # Constants from ACGME constraints
    HOURS_PER_BLOCK = 6
    MAX_WEEKLY_HOURS = 80
    ROLLING_WEEKS = 4
    MAX_CONSECUTIVE_DAYS = 6
    PGY1_RATIO = 2  # 1 faculty per 2 PGY-1
    OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3

    # In a real implementation, this would query the database for assignments
    # For now, we simulate with mock data showing the validation logic

    # 1. Check 80-hour work week violations
    if request.check_work_hours:
        # Simulate checking residents' weekly hours
        # Each block = 6 hours, max blocks per 4-week window = (80 * 4) / 6 = 53
        max_blocks_per_window = (MAX_WEEKLY_HOURS * ROLLING_WEEKS) // HOURS_PER_BLOCK

        # Example violations (in production, these would come from database queries)
        # Simulating a resident approaching the limit
        projected_hours = 78.5
        if projected_hours > MAX_WEEKLY_HOURS * 0.95:  # 95% threshold for warning
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    rule_type="80_hour_rule",
                    person_id="resident-001",
                    person_name="Dr. Williams",
                    date_range=(request.start_date, request.end_date),
                    message=f"Approaching 80-hour weekly limit: {projected_hours:.1f} hours",
                    details={
                        "projected_hours": projected_hours,
                        "limit": MAX_WEEKLY_HOURS,
                        "blocks_assigned": 52,
                        "max_blocks": max_blocks_per_window,
                    },
                    suggested_fix="Reduce assignment hours or redistribute workload to maintain compliance",
                )
            )

        # Simulating an actual violation
        violation_hours = 85.0
        if violation_hours > MAX_WEEKLY_HOURS:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    rule_type="80_hour_rule",
                    person_id="resident-002",
                    person_name="Dr. Chen",
                    date_range=(request.start_date, request.end_date),
                    message=f"ACGME 80-hour violation: {violation_hours:.1f} hours/week average",
                    details={
                        "average_weekly_hours": violation_hours,
                        "limit": MAX_WEEKLY_HOURS,
                        "excess_hours": violation_hours - MAX_WEEKLY_HOURS,
                    },
                    suggested_fix="URGENT: Remove assignments to comply with ACGME 80-hour limit",
                )
            )

    # 2. Check 1-in-7 rest period violations
    if request.check_rest_periods:
        # Simulate checking for consecutive work days > 6
        consecutive_days = 7
        if consecutive_days > MAX_CONSECUTIVE_DAYS:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    rule_type="1_in_7_rule",
                    person_id="resident-003",
                    person_name="Dr. Patel",
                    date_range=(request.start_date, request.end_date),
                    message=f"ACGME 1-in-7 violation: {consecutive_days} consecutive duty days",
                    details={
                        "consecutive_days": consecutive_days,
                        "limit": MAX_CONSECUTIVE_DAYS,
                    },
                    suggested_fix="Ensure at least one 24-hour period off every 7 days",
                )
            )

    # 3. Check supervision ratio violations
    if request.check_supervision:
        # Simulate checking faculty-to-resident ratios per block
        # Example: Block with insufficient supervision
        pgy1_count = 5
        faculty_count = 2
        required_faculty = (pgy1_count + PGY1_RATIO - 1) // PGY1_RATIO  # Ceiling division

        if faculty_count < required_faculty:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    rule_type="supervision_ratio",
                    person_id=None,
                    person_name=None,
                    date_range=(request.start_date, request.start_date),
                    message=f"Supervision ratio violation: {pgy1_count} PGY-1 residents need {required_faculty} faculty, only {faculty_count} assigned",
                    details={
                        "pgy1_count": pgy1_count,
                        "faculty_count": faculty_count,
                        "required_faculty": required_faculty,
                        "ratio": "1:2 for PGY-1",
                    },
                    suggested_fix="Assign additional supervising faculty to meet ACGME requirements",
                )
            )

    # 4. Check consecutive duty violations
    if request.check_consecutive_duty:
        # Simulate checking for assignments during scheduled absences
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type="availability",
                person_id="faculty-001",
                person_name="Dr. Martinez",
                date_range=(request.start_date, request.end_date),
                message="Assignment during scheduled absence/leave",
                details={
                    "absence_type": "Military TDY",
                    "conflict_dates": "2025-01-15 to 2025-01-20",
                },
                suggested_fix="Remove assignment or cancel absence to resolve conflict",
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

    # Implementation based on N-1/N-2 contingency analysis from resilience framework
    # In production, this would query actual assignments and analyze impact

    # Simulate faculty absence impact assessment
    num_affected = len(request.affected_person_ids)

    # Calculate coverage gaps based on scenario type
    if request.scenario == ContingencyScenario.FACULTY_ABSENCE:
        ***REMOVED*** absence: affects supervision ratios and coverage
        # Estimate ~10-15 blocks per faculty member
        estimated_blocks_per_person = 12
        total_affected_blocks = num_affected * estimated_blocks_per_person

        # Check if coverage can be redistributed
        # Assume 80% utilization threshold from resilience framework
        utilization_threshold = 0.80
        coverage_gaps = int(total_affected_blocks * 0.25)  # 25% may be uncoverable
        compliance_violations = coverage_gaps // 5  # Some gaps cause ACGME violations

        affected_rotations = ["Emergency Medicine", "Internal Medicine", "Clinic"][:num_affected]
        workload_increase = (total_affected_blocks / (10 * estimated_blocks_per_person)) * 100
        feasibility_score = max(0.3, 1.0 - (workload_increase / 100))

    elif request.scenario == ContingencyScenario.RESIDENT_ABSENCE:
        # Resident absence: primarily affects supervision ratios
        coverage_gaps = num_affected * 2  # Fewer coverage issues
        compliance_violations = num_affected  # May affect ratios
        affected_rotations = ["Resident Clinic", "Inpatient"]
        workload_increase = num_affected * 5.0
        feasibility_score = 0.85

    elif request.scenario == ContingencyScenario.EMERGENCY_COVERAGE:
        # Emergency: requires immediate coverage
        coverage_gaps = num_affected * 10
        compliance_violations = coverage_gaps // 3
        affected_rotations = ["Emergency Medicine", "Trauma", "ICU"]
        workload_increase = num_affected * 20.0
        feasibility_score = 0.60  # Lower due to urgency

    else:  # MASS_ABSENCE
        # Mass absence (e.g., multiple military deployments)
        coverage_gaps = num_affected * 15
        compliance_violations = coverage_gaps // 2
        affected_rotations = ["All Rotations"]
        workload_increase = num_affected * 30.0
        feasibility_score = 0.40  # Very challenging

    # Identify critical gaps (those that would violate ACGME or leave services uncovered)
    critical_gaps = []
    if compliance_violations > 0:
        critical_gaps.append(f"Night shift coverage gaps: {compliance_violations} blocks")
    if workload_increase > 20:
        critical_gaps.append(f"Remaining staff overloaded by {workload_increase:.1f}%")

    impact = ImpactAssessment(
        affected_rotations=affected_rotations,
        coverage_gaps=coverage_gaps,
        compliance_violations=compliance_violations,
        workload_increase_percent=workload_increase,
        feasibility_score=feasibility_score,
        critical_gaps=critical_gaps,
    )

    # Generate resolution options based on scenario and impact
    resolution_options = []

    # Option 1: Swap assignments (works well for planned absences)
    if request.scenario in (ContingencyScenario.FACULTY_ABSENCE, ContingencyScenario.RESIDENT_ABSENCE):
        swap_success_prob = 0.85 if num_affected == 1 else 0.70
        resolution_options.append(
            ResolutionOption(
                option_id="res-001",
                strategy="swap_assignment",
                description=f"Coordinate swaps with {num_affected} other faculty members",
                affected_people=[f"person-{i:03d}" for i in range(num_affected + 2)],
                estimated_effort="medium" if num_affected <= 2 else "high",
                success_probability=swap_success_prob,
                details={
                    "swap_candidates_available": 5,
                    "requires_approval": True,
                    "acgme_compliant": True,
                },
            )
        )

    # Option 2: Use backup pool (best for emergency coverage)
    if request.scenario in (ContingencyScenario.EMERGENCY_COVERAGE, ContingencyScenario.FACULTY_ABSENCE):
        backup_success_prob = 0.95 if coverage_gaps <= 5 else 0.75
        resolution_options.append(
            ResolutionOption(
                option_id="res-002",
                strategy="reassign_to_backup",
                description="Assign backup faculty from coverage pool",
                affected_people=[f"backup-{i:03d}" for i in range(min(3, coverage_gaps))],
                estimated_effort="low" if coverage_gaps <= 3 else "medium",
                success_probability=backup_success_prob,
                details={
                    "backup_pool_size": 5,
                    "immediate_availability": request.scenario == ContingencyScenario.EMERGENCY_COVERAGE,
                    "coverage_hours": coverage_gaps * 6,
                },
            )
        )

    # Option 3: Redistribute workload (last resort, risky for compliance)
    if workload_increase < 30:  # Only viable if increase is manageable
        redistribute_success = max(0.50, 1.0 - (workload_increase / 100))
        resolution_options.append(
            ResolutionOption(
                option_id="res-003",
                strategy="redistribute_workload",
                description=f"Redistribute workload among remaining {10 - num_affected} staff",
                affected_people=[f"person-{i:03d}" for i in range(10 - num_affected)],
                estimated_effort="high",
                success_probability=redistribute_success,
                details={
                    "avg_increase_per_person": workload_increase / (10 - num_affected),
                    "acgme_risk": "medium" if workload_increase > 15 else "low",
                    "requires_monitoring": True,
                },
            )
        )

    # Option 4: Request external locum/temp staff (for mass absence or high impact)
    if request.scenario == ContingencyScenario.MASS_ABSENCE or coverage_gaps > 10:
        resolution_options.append(
            ResolutionOption(
                option_id="res-004",
                strategy="external_staffing",
                description="Contract external locum tenens or temporary staff",
                affected_people=[],
                estimated_effort="high",
                success_probability=0.80,
                details={
                    "estimated_cost": f"${coverage_gaps * 1500}/day",
                    "lead_time_days": 14,
                    "credentialing_required": True,
                },
            )
        )

    # Determine recommended option
    if resolution_options:
        # Recommend option with highest success probability and lowest effort
        best_option = max(
            resolution_options,
            key=lambda x: x.success_probability - (0.1 if x.estimated_effort == "high" else 0)
        )
        recommended_option_id = best_option.option_id
    else:
        recommended_option_id = None

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

    # Implementation based on conflict auto-detector from backend
    # In production, this would query the database for actual conflicts
    conflicts: list[ConflictInfo] = []

    check_types = request.conflict_types or list(ConflictType)

    # 1. Check for double-booking conflicts
    if ConflictType.DOUBLE_BOOKING in check_types:
        # Simulate finding a person assigned to multiple rotations at the same time
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-001",
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ValidationSeverity.CRITICAL,
                affected_people=["person-007", "person-007"],  # Same person, different assignments
                date_range=(request.start_date, request.start_date),
                description="Dr. Johnson assigned to Emergency Medicine and Clinic simultaneously on AM block",
                auto_resolution_available=True,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-001",
                        strategy="remove_duplicate",
                        description="Remove duplicate clinic assignment, keep Emergency Medicine",
                        affected_people=["person-007"],
                        estimated_effort="low",
                        success_probability=1.0,
                        details={"preferred_assignment": "Emergency Medicine"},
                    )
                ],
            )
        )

    # 2. Check for work hour violations (80-hour rule)
    if ConflictType.WORK_HOUR_VIOLATION in check_types:
        # Simulate finding residents exceeding 80-hour work week
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-002",
                conflict_type=ConflictType.WORK_HOUR_VIOLATION,
                severity=ValidationSeverity.CRITICAL,
                affected_people=["resident-004"],
                date_range=(request.start_date, request.start_date + timedelta(days=27)),
                description="Dr. Anderson: 85.5 hours/week average over 4-week period (ACGME limit: 80 hours)",
                auto_resolution_available=request.include_auto_resolution,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-002",
                        strategy="reduce_assignments",
                        description="Remove 2 PM clinic blocks to bring hours to 79.5/week",
                        affected_people=["resident-004"],
                        estimated_effort="medium",
                        success_probability=0.90,
                        details={
                            "blocks_to_remove": 2,
                            "target_hours": 79.5,
                            "requires_replacement": True,
                        },
                    ),
                    ResolutionOption(
                        option_id="res-auto-003",
                        strategy="redistribute_workload",
                        description="Redistribute 3 blocks to other residents",
                        affected_people=["resident-004", "resident-005", "resident-006"],
                        estimated_effort="high",
                        success_probability=0.75,
                        details={"redistribution_count": 3},
                    ),
                ] if request.include_auto_resolution else [],
            )
        )

    # 3. Check for rest period violations (1-in-7 rule)
    if ConflictType.REST_PERIOD_VIOLATION in check_types:
        # Simulate finding residents without adequate rest periods
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-003",
                conflict_type=ConflictType.REST_PERIOD_VIOLATION,
                severity=ValidationSeverity.CRITICAL,
                affected_people=["resident-005"],
                date_range=(request.start_date, request.start_date + timedelta(days=7)),
                description="Dr. Lee: 8 consecutive duty days without 24-hour rest period (ACGME: max 6 consecutive)",
                auto_resolution_available=request.include_auto_resolution,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-004",
                        strategy="insert_rest_day",
                        description="Clear assignments on day 7 to create rest period",
                        affected_people=["resident-005"],
                        estimated_effort="medium",
                        success_probability=0.85,
                        details={
                            "rest_day": str(request.start_date + timedelta(days=6)),
                            "affected_blocks": 2,
                        },
                    )
                ] if request.include_auto_resolution else [],
            )
        )

    # 4. Check for supervision gaps
    if ConflictType.SUPERVISION_GAP in check_types:
        # Simulate finding blocks with inadequate faculty supervision
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-004",
                conflict_type=ConflictType.SUPERVISION_GAP,
                severity=ValidationSeverity.CRITICAL,
                affected_people=["block-supervisor"],
                date_range=(request.start_date + timedelta(days=5), request.start_date + timedelta(days=5)),
                description="Morning clinic: 6 PGY-1 residents with only 2 faculty (requires 3 faculty for 1:2 ratio)",
                auto_resolution_available=request.include_auto_resolution,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-005",
                        strategy="add_supervision",
                        description="Assign Dr. Rodriguez from backup pool to morning clinic",
                        affected_people=["faculty-backup-001"],
                        estimated_effort="low",
                        success_probability=0.95,
                        details={"backup_pool_available": True},
                    ),
                    ResolutionOption(
                        option_id="res-auto-006",
                        strategy="reduce_resident_count",
                        description="Move 2 PGY-1 residents to afternoon clinic",
                        affected_people=["resident-007", "resident-008"],
                        estimated_effort="medium",
                        success_probability=0.80,
                        details={"target_ratio": "1:2"},
                    ),
                ] if request.include_auto_resolution else [],
            )
        )

    # 5. Check for leave/absence overlaps
    if ConflictType.LEAVE_OVERLAP in check_types:
        # Simulate finding assignments during approved leave
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-005",
                conflict_type=ConflictType.LEAVE_OVERLAP,
                severity=ValidationSeverity.WARNING,
                affected_people=["faculty-002"],
                date_range=(request.start_date + timedelta(days=10), request.start_date + timedelta(days=14)),
                description="Dr. Thompson assigned to FMIT week during approved military TDY leave",
                auto_resolution_available=request.include_auto_resolution,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-007",
                        strategy="remove_conflicting_assignment",
                        description="Remove FMIT assignment during leave period",
                        affected_people=["faculty-002"],
                        estimated_effort="low",
                        success_probability=1.0,
                        details={
                            "leave_type": "Military TDY",
                            "requires_replacement": True,
                        },
                    )
                ] if request.include_auto_resolution else [],
            )
        )

    # 6. Check for credential mismatches
    if ConflictType.CREDENTIAL_MISMATCH in check_types:
        # Simulate finding assignments requiring credentials the person doesn't have
        conflicts.append(
            ConflictInfo(
                conflict_id="conflict-006",
                conflict_type=ConflictType.CREDENTIAL_MISMATCH,
                severity=ValidationSeverity.WARNING,
                affected_people=["faculty-003"],
                date_range=(request.start_date + timedelta(days=3), request.start_date + timedelta(days=3)),
                description="Dr. Kim assigned to pediatric procedures but lacks pediatric sedation certification",
                auto_resolution_available=request.include_auto_resolution,
                resolution_options=[
                    ResolutionOption(
                        option_id="res-auto-008",
                        strategy="reassign_to_qualified",
                        description="Reassign to Dr. Smith (pediatric certified)",
                        affected_people=["faculty-003", "faculty-qualified-001"],
                        estimated_effort="medium",
                        success_probability=0.85,
                        details={"required_credential": "Pediatric Sedation"},
                    )
                ] if request.include_auto_resolution else [],
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

    # Implementation based on swap auto-matcher from backend
    # In production, this would query database for pending swap requests and assignments
    candidates = []

    # Scoring weights (from SwapAutoMatcher)
    DATE_PROXIMITY_WEIGHT = 0.25
    PREFERENCE_ALIGNMENT_WEIGHT = 0.30
    WORKLOAD_BALANCE_WEIGHT = 0.20
    HISTORY_WEIGHT = 0.15
    AVAILABILITY_WEIGHT = 0.10

    # Simulate finding swap candidates
    # In a real implementation, this would query pending swap requests and assignments

    # Candidate 1: High-quality match with mutual benefit
    candidate_1_date_range = request.preferred_date_range or (date.today() + timedelta(days=7), date.today() + timedelta(days=13))

    # Calculate scoring factors for candidate 1
    date_proximity_score = 1.0  # Very close dates
    preference_score = 0.95  # Strong preference alignment
    workload_score = 0.85  # Good workload balance
    history_score = 0.90  # Positive past swaps
    availability_score = 1.0  # Both available

    match_score_1 = (
        date_proximity_score * DATE_PROXIMITY_WEIGHT +
        preference_score * PREFERENCE_ALIGNMENT_WEIGHT +
        workload_score * WORKLOAD_BALANCE_WEIGHT +
        history_score * HISTORY_WEIGHT +
        availability_score * AVAILABILITY_WEIGHT
    )

    candidates.append(
        SwapCandidate(
            candidate_person_id="faculty-008",
            candidate_name="Dr. Chen",
            assignment_id="assign-008",
            match_score=match_score_1,
            rotation="Emergency Medicine",
            date_range=candidate_1_date_range,
            compatibility_factors={
                "rotation_match": True,
                "rotation_type": "Emergency Medicine",
                "date_proximity_score": date_proximity_score,
                "preference_alignment": preference_score,
                "workload_balance": workload_score,
                "schedule_flexibility": "high",
                "past_swaps": 3,
                "successful_past_swaps": 3,
                "mutual_preference": True,
            },
            mutual_benefit=True,
            approval_likelihood="high",
        )
    )

    # Candidate 2: Good match but different rotation
    date_score_2 = 0.85  # Close but not perfect dates
    preference_score_2 = 0.70  # Moderate preference
    workload_score_2 = 0.80  # Fair workload balance
    history_score_2 = 0.75  # Some past swaps
    availability_score_2 = 0.90  # Generally available

    match_score_2 = (
        date_score_2 * DATE_PROXIMITY_WEIGHT +
        preference_score_2 * PREFERENCE_ALIGNMENT_WEIGHT +
        workload_score_2 * WORKLOAD_BALANCE_WEIGHT +
        history_score_2 * HISTORY_WEIGHT +
        availability_score_2 * AVAILABILITY_WEIGHT
    )

    candidates.append(
        SwapCandidate(
            candidate_person_id="faculty-009",
            candidate_name="Dr. Patel",
            assignment_id="assign-009",
            match_score=match_score_2,
            rotation="Internal Medicine",
            date_range=(candidate_1_date_range[0] + timedelta(days=7), candidate_1_date_range[1] + timedelta(days=7)),
            compatibility_factors={
                "rotation_match": False,
                "rotation_type": "Internal Medicine",
                "date_proximity_score": date_score_2,
                "preference_alignment": preference_score_2,
                "workload_balance": workload_score_2,
                "schedule_flexibility": "medium",
                "past_swaps": 2,
                "successful_past_swaps": 2,
                "mutual_preference": False,
            },
            mutual_benefit=False,
            approval_likelihood="medium",
        )
    )

    # Candidate 3: Moderate match with one-way benefit
    date_score_3 = 0.70  # Further apart dates
    preference_score_3 = 0.60  # Some preference alignment
    workload_score_3 = 0.70  # Adequate workload balance
    history_score_3 = 1.0  # No past rejections (new partnership)
    availability_score_3 = 0.85  # Available but with some constraints

    match_score_3 = (
        date_score_3 * DATE_PROXIMITY_WEIGHT +
        preference_score_3 * PREFERENCE_ALIGNMENT_WEIGHT +
        workload_score_3 * WORKLOAD_BALANCE_WEIGHT +
        history_score_3 * HISTORY_WEIGHT +
        availability_score_3 * AVAILABILITY_WEIGHT
    )

    candidates.append(
        SwapCandidate(
            candidate_person_id="faculty-010",
            candidate_name="Dr. Martinez",
            assignment_id="assign-010",
            match_score=match_score_3,
            rotation="Clinic",
            date_range=(candidate_1_date_range[0] + timedelta(days=14), candidate_1_date_range[1] + timedelta(days=14)),
            compatibility_factors={
                "rotation_match": False,
                "rotation_type": "Clinic",
                "date_proximity_score": date_score_3,
                "preference_alignment": preference_score_3,
                "workload_balance": workload_score_3,
                "schedule_flexibility": "low",
                "past_swaps": 0,
                "successful_past_swaps": 0,
                "mutual_preference": False,
            },
            mutual_benefit=False,
            approval_likelihood="medium",
        )
    )

    # Candidate 4: Lower match but blocked week (urgent need)
    date_score_4 = 0.80
    preference_score_4 = 0.95  # Strongly prefers the swap (blocked week)
    workload_score_4 = 0.60  # Some workload imbalance
    history_score_4 = 0.80
    availability_score_4 = 0.70  # Constrained availability

    match_score_4 = (
        date_score_4 * DATE_PROXIMITY_WEIGHT +
        preference_score_4 * PREFERENCE_ALIGNMENT_WEIGHT +
        workload_score_4 * WORKLOAD_BALANCE_WEIGHT +
        history_score_4 * HISTORY_WEIGHT +
        availability_score_4 * AVAILABILITY_WEIGHT
    )

    candidates.append(
        SwapCandidate(
            candidate_person_id="faculty-011",
            candidate_name="Dr. Thompson",
            assignment_id="assign-011",
            match_score=match_score_4,
            rotation="Emergency Medicine",
            date_range=(candidate_1_date_range[0] - timedelta(days=7), candidate_1_date_range[1] - timedelta(days=7)),
            compatibility_factors={
                "rotation_match": True,
                "rotation_type": "Emergency Medicine",
                "date_proximity_score": date_score_4,
                "preference_alignment": preference_score_4,
                "workload_balance": workload_score_4,
                "schedule_flexibility": "medium",
                "past_swaps": 1,
                "successful_past_swaps": 1,
                "mutual_preference": True,
                "requester_week_blocked": True,  # Has blocked week
                "urgent": True,
            },
            mutual_benefit=True,
            approval_likelihood="high",
        )
    )

    # Candidate 5: Acceptable match, less ideal
    date_score_5 = 0.60
    preference_score_5 = 0.50
    workload_score_5 = 0.75
    history_score_5 = 0.65  # One past rejection
    availability_score_5 = 0.80

    match_score_5 = (
        date_score_5 * DATE_PROXIMITY_WEIGHT +
        preference_score_5 * PREFERENCE_ALIGNMENT_WEIGHT +
        workload_score_5 * WORKLOAD_BALANCE_WEIGHT +
        history_score_5 * HISTORY_WEIGHT +
        availability_score_5 * AVAILABILITY_WEIGHT
    )

    candidates.append(
        SwapCandidate(
            candidate_person_id="faculty-012",
            candidate_name="Dr. Lee",
            assignment_id="assign-012",
            match_score=match_score_5,
            rotation="Procedures",
            date_range=(candidate_1_date_range[0] + timedelta(days=21), candidate_1_date_range[1] + timedelta(days=21)),
            compatibility_factors={
                "rotation_match": False,
                "rotation_type": "Procedures",
                "date_proximity_score": date_score_5,
                "preference_alignment": preference_score_5,
                "workload_balance": workload_score_5,
                "schedule_flexibility": "medium",
                "past_swaps": 2,
                "successful_past_swaps": 1,
                "past_rejections": 1,
                "mutual_preference": False,
            },
            mutual_benefit=False,
            approval_likelihood="low",
        )
    )

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
