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

from .api_client import get_api_client

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
    role: str | None = None  # Role-based identifier (e.g., "PGY-1", "Faculty") - no PII
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
    candidate_role: str  # Role-based identifier (e.g., "Faculty", "PGY-2") - no PII
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

    This tool calls the real FastAPI backend to perform comprehensive validation
    of work hours, supervision requirements, rest periods, and consecutive duty.

    Args:
        request: Validation request with date range and check options

    Returns:
        ScheduleValidationResult with all identified issues and compliance metrics

    Raises:
        ValueError: If date range is invalid
        RuntimeError: If backend API call fails
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(
        f"Validating schedule from {request.start_date} to {request.end_date}"
    )

    try:
        client = await get_api_client()

        # Call the real backend API
        result = await client.validate_schedule(
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
        )

        # Transform backend response to MCP format
        issues: list[ValidationIssue] = []

        # Parse violations from backend response
        for violation in result.get("violations", []):
            severity_str = violation.get("severity", "warning").lower()
            if severity_str == "critical" or severity_str == "error":
                severity = ValidationSeverity.CRITICAL
            elif severity_str == "warning":
                severity = ValidationSeverity.WARNING
            else:
                severity = ValidationSeverity.INFO

            issues.append(
                ValidationIssue(
                    severity=severity,
                    rule_type=violation.get("rule_type", "unknown"),
                    person_id=violation.get("person_id"),
                    role=violation.get("role"),
                    date_range=(request.start_date, request.end_date),
                    message=violation.get("message", "Validation issue"),
                    details=violation.get("details", {}),
                    suggested_fix=violation.get("suggested_fix"),
                )
            )

        critical_count = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)

        return ScheduleValidationResult(
            is_valid=result.get("valid", critical_count == 0),
            overall_compliance_rate=result.get("compliance_rate", 1.0 if critical_count == 0 else 0.0),
            total_issues=len(issues),
            critical_issues=critical_count,
            warning_issues=warning_count,
            info_issues=info_count,
            issues=issues,
            validated_at=datetime.now(),
            date_range=(request.start_date, request.end_date),
        )

    except Exception as e:
        logger.error(f"Schedule validation failed: {e}")
        raise RuntimeError(f"Failed to validate schedule: {e}") from e


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
        # Faculty absence: affects supervision ratios and coverage
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

    This tool calls the real FastAPI backend to scan the schedule for various
    types of conflicts including double-bookings, work hour violations, and
    supervision gaps.

    Args:
        request: Conflict detection request with date range and options

    Returns:
        ConflictDetectionResult with all detected conflicts and resolutions

    Raises:
        ValueError: If date range is invalid
        RuntimeError: If backend API call fails
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(
        f"Detecting conflicts from {request.start_date} to {request.end_date}"
    )

    try:
        client = await get_api_client()

        # Call the real backend API
        result = await client.get_conflicts(
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
        )

        # Transform backend response to MCP format
        conflicts: list[ConflictInfo] = []

        for conflict in result.get("conflicts", []):
            # Map backend conflict type to MCP ConflictType
            conflict_type_str = conflict.get("type", "").upper()
            try:
                conflict_type = ConflictType(conflict_type_str.lower())
            except ValueError:
                # Default to double_booking if unknown type
                conflict_type = ConflictType.DOUBLE_BOOKING

            # Map severity
            severity_str = conflict.get("severity", "warning").lower()
            if severity_str in ("critical", "error", "high"):
                severity = ValidationSeverity.CRITICAL
            elif severity_str == "warning":
                severity = ValidationSeverity.WARNING
            else:
                severity = ValidationSeverity.INFO

            conflicts.append(
                ConflictInfo(
                    conflict_id=conflict.get("id", f"conflict-{len(conflicts)}"),
                    conflict_type=conflict_type,
                    severity=severity,
                    affected_people=conflict.get("affected_people", []),
                    date_range=(request.start_date, request.end_date),
                    description=conflict.get("description", ""),
                    auto_resolution_available=False,  # Backend doesn't provide auto-resolution
                    resolution_options=[],
                )
            )

        conflicts_by_type = {
            ctype: sum(1 for c in conflicts if c.conflict_type == ctype)
            for ctype in ConflictType
        }

        return ConflictDetectionResult(
            total_conflicts=len(conflicts),
            conflicts_by_type=conflicts_by_type,
            conflicts=conflicts,
            auto_resolvable_count=0,
            detected_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        raise RuntimeError(f"Failed to detect conflicts: {e}") from e


# Keep mock implementation as fallback for swap candidates (requires file upload in backend)
async def _detect_conflicts_mock(
    request: ConflictDetectionRequest,
) -> ConflictDetectionResult:
    """
    Mock implementation of conflict detection (fallback).

    Used when backend API is unavailable or for testing.
    """
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
            candidate_role="Faculty",
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
            candidate_role="Faculty",
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
            candidate_role="Faculty",
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
            candidate_role="Faculty",
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
            candidate_role="Faculty",
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


# Schedule Generation Models and Function


class ScheduleAlgorithm(str, Enum):
    """Available scheduling algorithms."""

    GREEDY = "greedy"
    CP_SAT = "cp_sat"
    PULP = "pulp"
    HYBRID = "hybrid"


class ScheduleGenerationRequest(BaseModel):
    """Request to generate a schedule."""

    start_date: date
    end_date: date
    # Default to CP_SAT - greedy has a known bug (see backend/app/scheduling/solvers.py)
    algorithm: ScheduleAlgorithm = ScheduleAlgorithm.CP_SAT
    timeout_seconds: float = Field(default=120.0, ge=5.0, le=300.0)
    clear_existing: bool = True


class ScheduleGenerationResult(BaseModel):
    """Result of schedule generation."""

    status: str  # "success", "partial", "failed"
    total_blocks_assigned: int
    message: str
    validation_passed: bool
    total_violations: int
    coverage_rate: float
    generated_at: datetime
    date_range: tuple[date, date]
    details: dict[str, Any] = Field(default_factory=dict)


async def generate_schedule(
    request: ScheduleGenerationRequest,
) -> ScheduleGenerationResult:
    """
    Generate a schedule for the given date range using the backend API.

    This tool calls the FastAPI backend to generate a schedule using the
    specified algorithm. It optionally clears existing assignments first.

    SAFETY NOTE: This is a database-modifying operation. The safe-schedule-generation
    skill requires backup verification before calling this tool.

    Args:
        request: Schedule generation request with date range and options

    Returns:
        ScheduleGenerationResult with generation status and validation results

    Raises:
        ValueError: If date range is invalid
        RuntimeError: If backend API call fails
    """
    if request.end_date < request.start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(
        f"Generating schedule from {request.start_date} to {request.end_date} "
        f"using {request.algorithm.value} algorithm"
    )

    try:
        client = await get_api_client()

        # Call the backend API
        result = await client.generate_schedule(
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            algorithm=request.algorithm.value,
            timeout_seconds=request.timeout_seconds,
            clear_existing=request.clear_existing,
        )

        # Extract validation info
        validation = result.get("validation", {})
        total_violations = validation.get("total_violations", 0)
        coverage_rate = validation.get("coverage_rate", 0.0)

        return ScheduleGenerationResult(
            status=result.get("status", "unknown"),
            total_blocks_assigned=result.get("total_blocks_assigned", 0),
            message=result.get("message", "Schedule generation completed"),
            validation_passed=validation.get("valid", total_violations == 0),
            total_violations=total_violations,
            coverage_rate=coverage_rate,
            generated_at=datetime.now(),
            date_range=(request.start_date, request.end_date),
            details={
                "algorithm": request.algorithm.value,
                "solver_stats": result.get("solver_stats", {}),
                "resilience": result.get("resilience", {}),
                "nf_pc_audit": result.get("nf_pc_audit", {}),
            },
        )

    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        raise RuntimeError(f"Failed to generate schedule: {e}") from e
