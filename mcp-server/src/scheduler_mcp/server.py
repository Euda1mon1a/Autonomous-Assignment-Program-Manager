"""
Main MCP server for the residency scheduler.

This module creates and configures the FastMCP server, registering all
tools and resources for AI assistant interaction.
"""

import logging
import os
import sys
from datetime import date
from typing import Any

from fastmcp import FastMCP

from .async_tools import (
    ActiveTasksResult,
    BackgroundTaskResult,
    CancelTaskResult,
    TaskStatusResult,
    TaskType,
    cancel_task,
    get_task_status,
    list_active_tasks,
    start_background_task,
)
from .deployment_tools import (
    DeploymentStatusResult,
    Environment,
    ListDeploymentsRequest,
    ListDeploymentsResult,
    PromoteToProductionRequest,
    PromoteToProductionResult,
    RollbackDeploymentRequest,
    RollbackDeploymentResult,
    SecurityScanRequest,
    SecurityScanResult,
    SmokeTestRequest,
    SmokeTestResult,
    TestSuite,
    ValidateDeploymentRequest,
    ValidateDeploymentResult,
    get_deployment_status,
    list_deployments,
    promote_to_production,
    rollback_deployment,
    run_security_scan,
    run_smoke_tests,
    validate_deployment,
)
from .resilience_integration import (
    BlastRadiusAnalysisRequest,
    BlastRadiusAnalysisResponse,
    BehavioralPatternsResponse,
    CognitiveLoadRequest,
    CognitiveLoadResponse,
    ContingencyAnalysisRequest as ResilienceContingencyRequest,
    ContingencyAnalysisResponse as ResilienceContingencyResponse,
    DefenseLevelResponse,
    EquilibriumAnalysisResponse,
    HomeostasisStatusResponse,
    HubAnalysisResponse,
    LeChatelierAnalysisRequest,
    LoadSheddingLevelEnum,
    MTFComplianceRequest,
    MTFComplianceResponse,
    SacrificeHierarchyResponse,
    StaticFallbacksResponse,
    StigmergyAnalysisRequest,
    StigmergyAnalysisResponse,
    UtilizationResponse,
    analyze_homeostasis,
    analyze_hub_centrality,
    analyze_le_chatelier,
    analyze_stigmergy,
    assess_cognitive_load,
    calculate_blast_radius,
    check_mtf_compliance,
    check_utilization_threshold,
    execute_sacrifice_hierarchy,
    get_behavioral_patterns,
    get_defense_level,
    get_static_fallbacks,
    run_contingency_analysis_deep,
)
from .resources import (
    ComplianceSummaryResource,
    ScheduleStatusResource,
    get_compliance_summary,
    get_schedule_status,
)
from .tools import (
    ConflictDetectionRequest,
    ConflictDetectionResult,
    ContingencyRequest,
    ContingencyAnalysisResult,
    ScheduleValidationRequest,
    ScheduleValidationResult,
    SwapAnalysisResult,
    SwapCandidateRequest,
    analyze_swap_candidates,
    detect_conflicts,
    run_contingency_analysis,
    validate_schedule,
)

# Import new validate_schedule tool with ConstraintService integration
from tools.validate_schedule import (
    ScheduleValidationRequest as ConstraintValidationRequest,
    ScheduleValidationResponse as ConstraintValidationResponse,
    ConstraintConfig,
    validate_schedule as validate_schedule_by_id,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "Residency Scheduler",
    version="0.1.0",
    description=(
        "MCP server for medical residency scheduling with ACGME compliance, "
        "conflict detection, and workforce optimization"
    ),
)


# Register Resources


@mcp.resource("schedule://status")
async def schedule_status_resource(
    start_date: str | None = None,
    end_date: str | None = None,
) -> ScheduleStatusResource:
    """
    Get current schedule status.

    Provides comprehensive view of assignments, coverage metrics, and active issues.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: today)
        end_date: End date in YYYY-MM-DD format (default: 30 days from start)

    Returns:
        Current schedule status with assignments and metrics
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    return await get_schedule_status(start_date=start, end_date=end)


@mcp.resource("schedule://compliance")
async def compliance_summary_resource(
    start_date: str | None = None,
    end_date: str | None = None,
) -> ComplianceSummaryResource:
    """
    Get ACGME compliance summary.

    Analyzes schedule for work hour violations, supervision requirements,
    and duty hour restrictions.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: today)
        end_date: End date in YYYY-MM-DD format (default: 30 days from start)

    Returns:
        Compliance summary with violations and recommendations
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    return await get_compliance_summary(start_date=start, end_date=end)


# Register Tools


@mcp.tool()
async def validate_schedule_tool(
    start_date: str,
    end_date: str,
    check_work_hours: bool = True,
    check_supervision: bool = True,
    check_rest_periods: bool = True,
    check_consecutive_duty: bool = True,
) -> ScheduleValidationResult:
    """
    Validate schedule against ACGME regulations.

    Performs comprehensive validation including work hours, supervision,
    rest periods, and consecutive duty restrictions.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        check_work_hours: Validate 80-hour weekly work limit
        check_supervision: Validate supervision requirements
        check_rest_periods: Validate rest period requirements
        check_consecutive_duty: Validate consecutive duty limits

    Returns:
        Validation result with issues and compliance metrics
    """
    request = ScheduleValidationRequest(
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        check_work_hours=check_work_hours,
        check_supervision=check_supervision,
        check_rest_periods=check_rest_periods,
        check_consecutive_duty=check_consecutive_duty,
    )

    return await validate_schedule(request)


@mcp.tool()
async def validate_schedule_by_id_tool(
    schedule_id: str,
    constraint_config: str = "default",
    include_suggestions: bool = True,
) -> ConstraintValidationResponse:
    """
    Validate a schedule by ID against ACGME constraints.

    This tool validates a specific schedule identified by schedule_id against
    the full constraint system including ACGME compliance rules. It connects
    to the ConstraintService for comprehensive validation.

    Security Features:
    - Input schedule_id is validated and sanitized against injection attacks
    - Output is sanitized to prevent PII leakage
    - All person references are anonymized

    Args:
        schedule_id: Unique identifier for the schedule (UUID or alphanumeric).
                    Must be 1-64 characters, no special characters allowed.
        constraint_config: Constraint configuration to use:
                          - "default": Standard ACGME compliance checks
                          - "minimal": Fast basic validation
                          - "strict": Comprehensive strict validation
                          - "resilience": Include resilience framework constraints
        include_suggestions: Whether to include suggested actions for issues

    Returns:
        Validation result with sanitized issues and compliance metrics.
        All person names and identifiers are anonymized.

    Raises:
        ValueError: If schedule_id contains invalid characters or is too long

    Example:
        # Validate a schedule with default constraints
        result = await validate_schedule_by_id_tool(
            schedule_id="abc123-def456",
            constraint_config="default",
            include_suggestions=True
        )

        if result.is_valid:
            print("Schedule passes all critical constraints!")
        else:
            print(f"Found {result.critical_count} critical issues")
    """
    try:
        config = ConstraintConfig(constraint_config)
    except ValueError as e:
        raise ValueError(
            f"Invalid constraint_config: {constraint_config}. "
            f"Must be one of: {[c.value for c in ConstraintConfig]}"
        ) from e

    request = ConstraintValidationRequest(
        schedule_id=schedule_id,
        constraint_config=config,
        include_suggestions=include_suggestions,
    )

    return await validate_schedule_by_id(request)


@mcp.tool()
async def run_contingency_analysis_tool(
    scenario: str,
    affected_person_ids: list[str],
    start_date: str,
    end_date: str,
    auto_resolve: bool = False,
) -> ContingencyAnalysisResult:
    """
    Run contingency analysis for workforce planning.

    Simulates absence or emergency scenarios and identifies impact on
    coverage, compliance, and workload. Suggests resolution strategies.

    Args:
        scenario: Scenario type (faculty_absence, resident_absence,
                  emergency_coverage, mass_absence)
        affected_person_ids: List of person IDs affected by scenario
        start_date: Scenario start date in YYYY-MM-DD format
        end_date: Scenario end date in YYYY-MM-DD format
        auto_resolve: Whether to automatically apply recommended resolution

    Returns:
        Contingency analysis with impact assessment and resolution options
    """
    request = ContingencyRequest(
        scenario=scenario,  # type: ignore
        affected_person_ids=affected_person_ids,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        auto_resolve=auto_resolve,
    )

    return await run_contingency_analysis(request)


@mcp.tool()
async def detect_conflicts_tool(
    start_date: str,
    end_date: str,
    conflict_types: list[str] | None = None,
    include_auto_resolution: bool = True,
) -> ConflictDetectionResult:
    """
    Detect scheduling conflicts.

    Scans for double-bookings, work hour violations, supervision gaps,
    and other conflicts. Suggests automatic resolution strategies.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        conflict_types: Specific conflict types to check (default: all)
        include_auto_resolution: Include automatic resolution suggestions

    Returns:
        Conflict detection results with resolution options
    """
    request = ConflictDetectionRequest(
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        conflict_types=[ct for ct in conflict_types] if conflict_types else None,  # type: ignore
        include_auto_resolution=include_auto_resolution,
    )

    return await detect_conflicts(request)


@mcp.tool()
async def analyze_swap_candidates_tool(
    requester_person_id: str,
    assignment_id: str,
    preferred_start_date: str | None = None,
    preferred_end_date: str | None = None,
    max_candidates: int = 10,
) -> SwapAnalysisResult:
    """
    Analyze potential swap candidates.

    Uses intelligent matching to find optimal swap partners based on
    rotation compatibility, flexibility, and mutual benefit.

    Args:
        requester_person_id: ID of person requesting swap
        assignment_id: ID of assignment to swap
        preferred_start_date: Preferred swap start date in YYYY-MM-DD (optional)
        preferred_end_date: Preferred swap end date in YYYY-MM-DD (optional)
        max_candidates: Maximum number of candidates to return (1-50)

    Returns:
        Swap analysis with ranked candidates and compatibility scores
    """
    preferred_range = None
    if preferred_start_date and preferred_end_date:
        preferred_range = (
            date.fromisoformat(preferred_start_date),
            date.fromisoformat(preferred_end_date),
        )

    request = SwapCandidateRequest(
        requester_person_id=requester_person_id,
        assignment_id=assignment_id,
        preferred_date_range=preferred_range,
        max_candidates=max_candidates,
    )

    return await analyze_swap_candidates(request)


# Async Task Management Tools


@mcp.tool()
async def start_background_task_tool(
    task_type: str,
    params: dict[str, Any] | None = None,
) -> BackgroundTaskResult:
    """
    Start a background task using Celery.

    Triggers long-running tasks such as resilience analysis, schedule metrics
    computation, or contingency planning. Returns a task_id for status polling.

    Available task types:
    - resilience_health_check: Run health check
    - resilience_contingency: Run N-1/N-2 contingency analysis
    - resilience_fallback_precompute: Precompute fallback schedules
    - resilience_utilization_forecast: Forecast utilization
    - resilience_crisis_activation: Activate crisis response
    - metrics_computation: Compute schedule metrics
    - metrics_snapshot: Take metrics snapshot
    - metrics_cleanup: Clean up old snapshots
    - metrics_fairness_report: Generate fairness trend report
    - metrics_version_diff: Compare two schedule versions

    Args:
        task_type: Type of task to start
        params: Optional task-specific parameters

    Returns:
        Task information with task_id for polling

    Example params:
        resilience_contingency: {"days_ahead": 90}
        metrics_computation: {"start_date": "2025-01-01", "end_date": "2025-03-31"}
        metrics_version_diff: {"run_id_1": "uuid1", "run_id_2": "uuid2"}
    """
    try:
        task_type_enum = TaskType(task_type)
    except ValueError as e:
        raise ValueError(
            f"Invalid task_type: {task_type}. Must be one of: {[t.value for t in TaskType]}"
        ) from e

    return await start_background_task(task_type_enum, params)


@mcp.tool()
async def get_task_status_tool(task_id: str) -> TaskStatusResult:
    """
    Get the status of a background task.

    Polls Celery to check task progress and retrieve results or errors.

    Args:
        task_id: Task ID from start_background_task

    Returns:
        Task status with progress, result, or error

    Possible statuses:
    - pending: Waiting to execute
    - started: Currently running
    - success: Completed successfully (result available)
    - failure: Failed (error available)
    - revoked: Canceled
    - retry: Being retried
    """
    return await get_task_status(task_id)


@mcp.tool()
async def cancel_task_tool(task_id: str) -> CancelTaskResult:
    """
    Cancel a running or queued background task.

    Revokes a Celery task to prevent execution or terminate it if running.

    Args:
        task_id: Task ID to cancel

    Returns:
        Cancellation confirmation

    Note:
        Completed tasks cannot be canceled. Running tasks may not stop immediately.
    """
    return await cancel_task(task_id)


@mcp.tool()
async def list_active_tasks_tool(
    task_type: str | None = None,
) -> ActiveTasksResult:
    """
    List all currently active (queued or running) tasks.

    Queries Celery workers to find tasks currently executing or in queue.

    Args:
        task_type: Optional filter by task type

    Returns:
        List of active tasks with their status

    Note:
        Requires Celery workers to be running and connected.
    """
    task_type_enum = None
    if task_type:
        try:
            task_type_enum = TaskType(task_type)
        except ValueError as e:
            raise ValueError(
                f"Invalid task_type: {task_type}. Must be one of: {[t.value for t in TaskType]}"
            ) from e

    return await list_active_tasks(task_type_enum)


# Resilience Framework Tools


@mcp.tool()
async def check_utilization_threshold_tool(
    available_faculty: int,
    required_blocks: int,
    blocks_per_faculty_per_day: float = 2.0,
    days_in_period: int = 1,
) -> UtilizationResponse:
    """
    Check current utilization against 80% threshold (queuing theory).

    Calculates system utilization and compares it to the critical 80% threshold
    from queuing theory. Above 80%, wait times increase exponentially and cascade
    failures become likely.

    Args:
        available_faculty: Number of faculty members available
        required_blocks: Number of blocks requiring coverage
        blocks_per_faculty_per_day: Max blocks per faculty per day (default: 2)
        days_in_period: Number of days in analysis period

    Returns:
        Utilization status with recommendations
    """
    return await check_utilization_threshold(
        available_faculty, required_blocks, blocks_per_faculty_per_day, days_in_period
    )


@mcp.tool()
async def get_defense_level_tool(coverage_rate: float) -> DefenseLevelResponse:
    """
    Get current defense-in-depth level (nuclear safety paradigm).

    Implements the 5-level defense-in-depth strategy from nuclear reactor safety,
    adapted for medical scheduling. Each level operates independently assuming
    all previous levels have failed.

    Args:
        coverage_rate: Current coverage rate (0.0 to 1.0)

    Returns:
        Defense level status with recommended actions
    """
    return await get_defense_level(coverage_rate)


@mcp.tool()
async def run_contingency_analysis_resilience_tool(
    analyze_n1: bool = True,
    analyze_n2: bool = True,
    include_cascade_simulation: bool = False,
    critical_faculty_only: bool = True,
) -> ResilienceContingencyResponse:
    """
    Run N-1/N-2 contingency analysis (power grid planning).

    Performs contingency analysis inspired by electrical grid operations.
    N-1: system must survive loss of any single component.
    N-2: system must survive loss of any two components.

    Args:
        analyze_n1: Perform N-1 analysis (single faculty loss)
        analyze_n2: Perform N-2 analysis (dual faculty loss)
        include_cascade_simulation: Include cascade failure simulation
        critical_faculty_only: Only analyze critical faculty for N-2

    Returns:
        Vulnerability analysis with N-1/N-2 results
    """
    request = ResilienceContingencyRequest(
        analyze_n1=analyze_n1,
        analyze_n2=analyze_n2,
        include_cascade_simulation=include_cascade_simulation,
        critical_faculty_only=critical_faculty_only,
    )
    return await run_contingency_analysis_deep(request)


@mcp.tool()
async def get_static_fallbacks_tool() -> StaticFallbacksResponse:
    """
    Get pre-computed fallback schedules (AWS static stability).

    Retrieves fallback schedules pre-computed for various crisis scenarios.
    Like AWS availability zones, these provide immediate failover capability.

    Returns:
        Available fallback schedules and recommendations
    """
    return await get_static_fallbacks()


@mcp.tool()
async def execute_sacrifice_hierarchy_tool(
    target_level: str, simulate_only: bool = True
) -> SacrificeHierarchyResponse:
    """
    Execute sacrifice hierarchy (triage-based load shedding).

    Implements triage-based load shedding, suspending non-essential activities
    in priority order to maintain critical patient safety functions.

    Args:
        target_level: Target load shedding level (normal, yellow, orange, red, black)
        simulate_only: If True, only simulate (don't actually apply)

    Returns:
        Load shedding details with activities suspended/protected
    """
    try:
        level_enum = LoadSheddingLevelEnum(target_level)
    except ValueError as e:
        raise ValueError(
            f"Invalid target_level: {target_level}. Must be one of: "
            f"{[l.value for l in LoadSheddingLevelEnum]}"
        ) from e

    return await execute_sacrifice_hierarchy(level_enum, simulate_only)


@mcp.tool()
async def analyze_homeostasis_tool(
    current_values: dict[str, float],
) -> HomeostasisStatusResponse:
    """
    Analyze homeostasis feedback loops and allostatic load.

    Monitors feedback loops that maintain system stability and calculates
    allostatic load (cumulative stress) on faculty and the system.

    Args:
        current_values: Dictionary of metric_name -> current_value

    Returns:
        Homeostasis status with feedback loop analysis
    """
    return await analyze_homeostasis(current_values)


@mcp.tool()
async def calculate_blast_radius_tool(
    zone_id: str | None = None, check_all_zones: bool = True
) -> BlastRadiusAnalysisResponse:
    """
    Calculate blast radius and zone isolation status.

    Analyzes how failures are contained within scheduling zones, preventing
    cascades from spreading across the entire system.

    Args:
        zone_id: Specific zone to analyze (optional)
        check_all_zones: Check all zones if True

    Returns:
        Zone health analysis with containment status
    """
    request = BlastRadiusAnalysisRequest(
        zone_id=zone_id, check_all_zones=check_all_zones
    )
    return await calculate_blast_radius(request)


@mcp.tool()
async def analyze_le_chatelier_tool(
    include_stress_prediction: bool = True,
) -> EquilibriumAnalysisResponse:
    """
    Analyze equilibrium shift and stress compensation (Le Chatelier).

    Applies Le Chatelier's principle to scheduling: when stress is applied,
    the system shifts to a new equilibrium. Compensation is always partial
    and temporary.

    Args:
        include_stress_prediction: Include stress response predictions

    Returns:
        Equilibrium analysis with stress and compensation details
    """
    request = LeChatelierAnalysisRequest(
        include_stress_prediction=include_stress_prediction
    )
    return await analyze_le_chatelier(request)


@mcp.tool()
async def analyze_hub_centrality_tool() -> HubAnalysisResponse:
    """
    Analyze faculty hub centrality and single points of failure.

    Uses network analysis to identify "hub" faculty members whose removal
    would cause disproportionate system disruption. Uses NetworkX for
    advanced centrality metrics (betweenness, PageRank).

    Returns:
        Faculty centrality analysis with hub identification
    """
    return await analyze_hub_centrality()


@mcp.tool()
async def assess_cognitive_load_tool(
    session_id: str | None = None, include_queue_status: bool = True
) -> CognitiveLoadResponse:
    """
    Assess cognitive load and decision queue complexity.

    Implements Miller's Law (7±2 items in working memory) to monitor decision
    queue complexity and coordinator cognitive load.

    Args:
        session_id: Specific session to analyze (optional)
        include_queue_status: Include decision queue status

    Returns:
        Cognitive load analysis with decision queue details
    """
    request = CognitiveLoadRequest(
        session_id=session_id, include_queue_status=include_queue_status
    )
    return await assess_cognitive_load(request)


@mcp.tool()
async def get_behavioral_patterns_tool() -> BehavioralPatternsResponse:
    """
    Get behavioral patterns from stigmergy (swarm intelligence).

    Analyzes preference trails left by faculty members making schedule decisions.
    Like ant pheromone trails, these reveal collective intelligence about
    optimal scheduling patterns.

    Returns:
        Behavioral patterns with emergent preferences
    """
    return await get_behavioral_patterns()


@mcp.tool()
async def analyze_stigmergy_tool(
    slot_id: str | None = None,
    slot_type: str | None = None,
    include_suggestions: bool = True,
) -> StigmergyAnalysisResponse:
    """
    Analyze stigmergic optimization signals for specific slots.

    Provides stigmergy-based scheduling suggestions for specific slots or
    slot types based on collective preference trails.

    Args:
        slot_id: Specific slot to analyze (optional)
        slot_type: Slot type to analyze (optional)
        include_suggestions: Include faculty assignment suggestions

    Returns:
        Stigmergy analysis with optimization suggestions
    """
    request = StigmergyAnalysisRequest(
        slot_id=slot_id, slot_type=slot_type, include_suggestions=include_suggestions
    )
    return await analyze_stigmergy(request)


@mcp.tool()
async def check_mtf_compliance_tool(
    check_circuit_breaker: bool = True, generate_sitrep: bool = True
) -> MTFComplianceResponse:
    """
    Check Multi-Tier Functionality (MTF) compliance status.

    Provides military-style compliance reporting including DRRS translation,
    circuit breaker status, and "Iron Dome" regulatory protection.

    Args:
        check_circuit_breaker: Include circuit breaker status
        generate_sitrep: Generate SITREP executive summary

    Returns:
        MTF compliance status with DRRS ratings
    """
    request = MTFComplianceRequest(
        check_circuit_breaker=check_circuit_breaker, generate_sitrep=generate_sitrep
    )
    return await check_mtf_compliance(request)


# Deployment Workflow Tools


@mcp.tool()
async def validate_deployment_tool(
    environment: str,
    git_ref: str,
    dry_run: bool = False,
    skip_tests: bool = False,
    skip_security_scan: bool = False,
) -> ValidateDeploymentResult:
    """
    Validate a deployment before executing.

    Performs comprehensive checks including tests, security scan,
    migrations safety, configuration validity, and environment readiness.

    Args:
        environment: Target environment (staging or production)
        git_ref: Git reference to deploy (branch, tag, or SHA)
        dry_run: Simulate validation without side effects
        skip_tests: Skip test verification (not recommended)
        skip_security_scan: Skip security scan (not recommended)

    Returns:
        Validation result with all checks and any blockers

    Example:
        # Validate staging deployment
        result = await validate_deployment_tool(
            environment="staging",
            git_ref="main",
            dry_run=False
        )

        # Check if valid
        if result.valid:
            print("Deployment is ready!")
        else:
            print(f"Blockers: {result.blockers}")
    """
    try:
        env = Environment(environment)
    except ValueError as e:
        raise ValueError(
            f"Invalid environment: {environment}. Must be 'staging' or 'production'"
        ) from e

    request = ValidateDeploymentRequest(
        environment=env,
        git_ref=git_ref,
        dry_run=dry_run,
        skip_tests=skip_tests,
        skip_security_scan=skip_security_scan,
    )

    return await validate_deployment(request)


@mcp.tool()
async def run_security_scan_tool(
    git_ref: str,
    scan_dependencies: bool = True,
    scan_code: bool = True,
    scan_secrets: bool = True,
    dry_run: bool = False,
) -> SecurityScanResult:
    """
    Run comprehensive security scan on codebase.

    Performs dependency vulnerability scanning, SAST (static application
    security testing), and secret detection.

    Args:
        git_ref: Git reference to scan
        scan_dependencies: Run dependency vulnerability scan
        scan_code: Run SAST analysis
        scan_secrets: Run secret detection
        dry_run: Simulate scan without actual execution

    Returns:
        Security scan results with vulnerabilities and severity summary

    Example:
        # Run full security scan
        result = await run_security_scan_tool(
            git_ref="main",
            dry_run=False
        )

        # Check critical vulnerabilities
        if result.severity_summary.get("critical", 0) > 0:
            print("Critical vulnerabilities found!")
    """
    request = SecurityScanRequest(
        git_ref=git_ref,
        scan_dependencies=scan_dependencies,
        scan_code=scan_code,
        scan_secrets=scan_secrets,
        dry_run=dry_run,
    )

    return await run_security_scan(request)


@mcp.tool()
async def run_smoke_tests_tool(
    environment: str,
    test_suite: str = "basic",
    timeout_seconds: int = 300,
    dry_run: bool = False,
) -> SmokeTestResult:
    """
    Run smoke tests against deployed environment.

    Tests basic functionality including API health, database connectivity,
    Redis connectivity, authentication, and critical user journeys.

    Args:
        environment: Target environment (staging or production)
        test_suite: Test suite to run (basic or full)
        timeout_seconds: Test timeout in seconds (30-1800)
        dry_run: Simulate tests without actual execution

    Returns:
        Smoke test results with individual test outcomes

    Example:
        # Run basic smoke tests on staging
        result = await run_smoke_tests_tool(
            environment="staging",
            test_suite="basic",
            dry_run=False
        )

        if result.passed:
            print("All smoke tests passed!")
    """
    try:
        env = Environment(environment)
    except ValueError as e:
        raise ValueError(
            f"Invalid environment: {environment}. Must be 'staging' or 'production'"
        ) from e

    try:
        suite = TestSuite(test_suite)
    except ValueError as e:
        raise ValueError(
            f"Invalid test_suite: {test_suite}. Must be 'basic' or 'full'"
        ) from e

    request = SmokeTestRequest(
        environment=env,
        test_suite=suite,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )

    return await run_smoke_tests(request)


@mcp.tool()
async def promote_to_production_tool(
    staging_version: str,
    approval_token: str,
    skip_smoke_tests: bool = False,
    dry_run: bool = False,
) -> PromoteToProductionResult:
    """
    Promote staging deployment to production.

    Requires staging smoke tests to pass and valid human approval token.
    Triggers production deployment pipeline.

    Args:
        staging_version: Staging version to promote (git ref)
        approval_token: Human approval token for production deployment
        skip_smoke_tests: Skip smoke test verification (not recommended)
        dry_run: Simulate promotion without actual deployment

    Returns:
        Promotion result with deployment ID and status

    Example:
        # Promote to production
        result = await promote_to_production_tool(
            staging_version="v1.2.3",
            approval_token="prod-token-abc123",
            dry_run=False
        )

        print(f"Deployment ID: {result.deployment_id}")
        print(f"Status: {result.status}")

    Security:
        Production deployments require valid approval token.
        Set DEPLOYMENT_ADMIN_TOKENS environment variable.
    """
    request = PromoteToProductionRequest(
        staging_version=staging_version,
        approval_token=approval_token,
        skip_smoke_tests=skip_smoke_tests,
        dry_run=dry_run,
    )

    return await promote_to_production(request)


@mcp.tool()
async def rollback_deployment_tool(
    environment: str,
    reason: str,
    target_version: str | None = None,
    dry_run: bool = False,
) -> RollbackDeploymentResult:
    """
    Rollback a deployment to previous version.

    Identifies previous stable version and triggers redeployment.
    Verifies rollback success.

    Args:
        environment: Target environment (staging or production)
        reason: Reason for rollback (for audit trail)
        target_version: Optional specific version to rollback to
        dry_run: Simulate rollback without actual execution

    Returns:
        Rollback result with status and version information

    Example:
        # Rollback production to previous version
        result = await rollback_deployment_tool(
            environment="production",
            reason="Critical bug in authentication",
            dry_run=False
        )

        print(f"Rolling back from {result.from_version} to {result.to_version}")

    Note:
        If target_version is not specified, rolls back to most recent
        successful deployment.
    """
    try:
        env = Environment(environment)
    except ValueError as e:
        raise ValueError(
            f"Invalid environment: {environment}. Must be 'staging' or 'production'"
        ) from e

    request = RollbackDeploymentRequest(
        environment=env,
        target_version=target_version,
        reason=reason,
        dry_run=dry_run,
    )

    return await rollback_deployment(request)


@mcp.tool()
async def get_deployment_status_tool(
    deployment_id: str,
) -> DeploymentStatusResult:
    """
    Get current status of a deployment.

    Returns detailed information including deployment status, timeline,
    individual check results, recent logs, and health check results.

    Args:
        deployment_id: Deployment identifier from promote_to_production or rollback

    Returns:
        Deployment status with logs and health checks

    Example:
        # Check deployment status
        result = await get_deployment_status_tool(
            deployment_id="deploy-1234567890.123"
        )

        print(f"Status: {result.deployment.status}")
        print(f"Health: {result.health_checks}")

        # View logs
        for log in result.logs:
            print(log)
    """
    return await get_deployment_status(deployment_id)


@mcp.tool()
async def list_deployments_tool(
    environment: str | None = None,
    limit: int = 10,
    include_failed: bool = True,
) -> ListDeploymentsResult:
    """
    List recent deployments.

    Returns recent deployment history with filtering options.

    Args:
        environment: Filter by environment (staging or production)
        limit: Maximum number of deployments to return (1-100)
        include_failed: Include failed deployments in results

    Returns:
        List of recent deployments

    Example:
        # List last 5 production deployments
        result = await list_deployments_tool(
            environment="production",
            limit=5,
            include_failed=False
        )

        for deployment in result.deployments:
            print(f"{deployment.version}: {deployment.status}")
    """
    env = None
    if environment:
        try:
            env = Environment(environment)
        except ValueError as e:
            raise ValueError(
                f"Invalid environment: {environment}. Must be 'staging' or 'production'"
            ) from e

    request = ListDeploymentsRequest(
        environment=env,
        limit=limit,
        include_failed=include_failed,
    )

    return await list_deployments(request)


# Server lifecycle hooks


@mcp.on_initialize()
async def on_initialize() -> None:
    """
    Initialize the MCP server.

    Called when the server starts. Used for setup tasks like
    database connections and configuration validation.
    """
    logger.info("Initializing Residency Scheduler MCP Server")

    # Validate environment variables
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning(
            "DATABASE_URL not set. Server will use placeholder data. "
            "Set DATABASE_URL for production use."
        )

    api_url = os.getenv("API_BASE_URL")
    if api_url:
        logger.info(f"API integration enabled: {api_url}")
    else:
        logger.info("API integration disabled. Using direct database access.")

    logger.info("Server initialization complete")


@mcp.on_shutdown()
async def on_shutdown() -> None:
    """
    Clean up server resources.

    Called when the server shuts down. Used for cleanup tasks like
    closing database connections.
    """
    logger.info("Shutting down Residency Scheduler MCP Server")
    # TODO: Add cleanup logic (close DB connections, etc.)
    logger.info("Server shutdown complete")


# Main entry point


def main() -> None:
    """
    Run the MCP server.

    This is the main entry point when running as a script or via
    the scheduler-mcp command.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Residency Scheduler MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DATABASE_URL     PostgreSQL connection string
  API_BASE_URL     Optional: Main application API URL
  LOG_LEVEL        Logging level (DEBUG, INFO, WARNING, ERROR)

Examples:
  # Run with database connection
  DATABASE_URL=postgresql://user:pass@localhost/scheduler scheduler-mcp

  # Run with debug logging
  LOG_LEVEL=DEBUG scheduler-mcp

  # Run with API integration
  API_BASE_URL=http://localhost:8000 scheduler-mcp
        """,
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )

    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    logger.info(f"Log level: {args.log_level}")

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
