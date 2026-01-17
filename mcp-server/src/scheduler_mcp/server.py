"""
Main MCP server for the residency scheduler.

This module creates and configures the FastMCP server, registering all
tools and resources for AI assistant interaction.

Supports HTTP transport for remote access with API key authentication.
Deploy on Render or similar platforms to enable Claude Code integration.
"""

import logging
import os
import sys
from datetime import date, datetime, timedelta
from typing import Any

from fastmcp import FastMCP

# Try to import Starlette for health endpoint (optional for HTTP transport)
try:
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False
    JSONResponse = None  # type: ignore
    Route = None  # type: ignore

# Import API client for RAG tools
from .api_client import get_api_client
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

# Import backup tools
from .backup_tools import (
    BackupStatusResult,
    CreateBackupResult,
    ListBackupsResult,
    RestoreBackupResult,
    VerifyBackupResult,
    create_backup,
    get_backup_status,
    list_backups,
    restore_backup,
    verify_backup,
)

# Import circuit breaker tools
from .circuit_breaker_tools import (
    AllBreakersStatusResponse,
    BreakerHealthResponse,
    HalfOpenTestResponse,
    ManualOverrideResponse,
    check_circuit_breakers,
    get_breaker_health,
    override_circuit_breaker,
    test_half_open_breaker,
)

# Import API client for RAG tools
# Import composite/advanced resilience tools
from .composite_resilience_tools import (
    # Creep Fatigue
    CreepFatigueResponse,
    # Recovery Distance
    RecoveryDistanceResponse,
    # Transcription Factors
    TranscriptionTriggersResponse,
    # Unified Critical Index
    UnifiedCriticalIndexResponse,
    analyze_transcription_triggers,
    assess_creep_fatigue,
    calculate_recovery_distance,
    get_unified_critical_index,
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

# Import early warning tools (STA/LTA, SPC, Fire Index)
from .early_warning_integration import (
    # Burnout Fire Index (CFFDRS)
    BatchFireDangerRequest,
    BatchFireDangerResponse,
    FireDangerRequest,
    FireDangerResponse,
    # Seismic Detection (STA/LTA)
    MultiSignalMagnitudeRequest,
    MultiSignalMagnitudeResponse,
    PrecursorDetectionRequest,
    PrecursorDetectionResponse,
    PrecursorSignalType,
    # SPC Monitoring (Western Electric)
    ProcessCapabilityRequest,
    SPCAnalysisRequest,
    SPCAnalysisResponse,
    calculate_batch_fire_danger,
    calculate_fire_danger_index,
    detect_burnout_precursors,
    predict_burnout_magnitude,
    run_spc_analysis,
)
from .early_warning_integration import (
    ProcessCapabilityResponse as EWProcessCapabilityResponse,
)
from .early_warning_integration import (
    calculate_process_capability_tool as calculate_spc_process_capability,
)

# Import empirical testing tools
from .empirical_tools import (
    AblationResult,
    ConstraintBenchmarkResult,
    ModuleUsageResult,
    ResilienceBenchmarkResult,
    SolverBenchmarkResult,
    ablation_study,
    benchmark_constraints,
    benchmark_resilience,
    benchmark_solvers,
    module_usage_analysis,
)

# Import FRMS (Fatigue Risk Management System) tools
from .frms_integration import (
    FatigueHazardResponse,
    FatigueScoreResponse,
    # Response Models
    FRMSAssessmentResponse,
    ScheduleFatigueRiskResponse,
    SleepDebtAnalysisResponse,
    TeamFatigueScanResponse,
    analyze_sleep_debt,
    assess_schedule_fatigue_risk,
    evaluate_fatigue_hazard,
    get_fatigue_score,
    # Tool Functions
    run_frms_assessment,
    scan_team_fatigue,
)

# Import Hopfield network attractor tools (energy landscape & schedule stability)
from .hopfield_attractor_tools import (
    # Enums
    BasinDepthResponse,
    NearbyAttractorsResponse,
    SpuriousAttractorsResponse,
    detect_spurious_attractors,
    find_nearby_attractors,
    measure_basin_depth,
)
from .hopfield_attractor_tools import (
    ScheduleEnergyResponse as HopfieldEnergyResponse,
)
from .hopfield_attractor_tools import (
    # Tool Functions
    calculate_schedule_energy as calculate_hopfield_energy,
)

# Import immune system tools (AIS - Artificial Immune System)
from .immune_system_tools import (
    # Response Models
    AntibodyAnalysisResponse,
    ImmuneResponseAssessmentResponse,
    MemoryCellsResponse,
    # Tool Functions
    analyze_antibody_response,
    assess_immune_response,
    check_memory_cells,
)

# Import optimization and analytics tools (Erlang C, Six Sigma, Equity)
from .optimization_tools import (
    EquityMetricsResponse,
    ErlangCoverageResponse,
    ErlangMetricsResponse,
    LorenzCurveResponse,
    ProcessCapabilityResponse,
    calculate_equity_metrics,
    calculate_erlang_metrics,
    calculate_process_capability,
    generate_lorenz_curve,
    optimize_erlang_coverage,
)

# Import resilience integration tools (N-1/N-2, Defense Levels, Epidemiology)
from .resilience_integration import (
    BehavioralPatternsResponse,
    BlastRadiusAnalysisRequest,
    BlastRadiusAnalysisResponse,
    BurnoutContagionResponse,
    BurnoutRtResponse,
    BurnoutSpreadSimulationResponse,
    CognitiveLoadRequest,
    CognitiveLoadResponse,
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
    calculate_burnout_rt,
    check_mtf_compliance,
    check_utilization_threshold,
    execute_sacrifice_hierarchy,
    get_behavioral_patterns,
    get_defense_level,
    get_static_fallbacks,
    run_contingency_analysis_deep,
    simulate_burnout_contagion,
    simulate_burnout_spread,
)
from .resilience_integration import (
    ContingencyAnalysisRequest as ResilienceContingencyRequest,
)
from .resilience_integration import (
    ContingencyAnalysisResponse as ResilienceContingencyResponse,
)
from .resources import (
    ComplianceSummaryResource,
    ScheduleStatusResource,
    get_compliance_summary,
    get_schedule_status,
)
from .scheduling_tools import (
    ConflictDetectionRequest,
    ConflictDetectionResult,
    ContingencyAnalysisResult,
    ContingencyRequest,
    ScheduleValidationRequest,
    ScheduleValidationResult,
    SwapAnalysisResult,
    SwapCandidateRequest,
    analyze_swap_candidates,
    detect_conflicts,
    run_contingency_analysis,
    validate_schedule,
)

# Import thermodynamics tools (entropy, phase transitions, free energy)
from .thermodynamics_tools import (
    EnergyLandscapeResponse,
    EntropyMonitorStateResponse,
    FreeEnergyOptimizationResponse,
    PhaseTransitionRiskResponse,
    # Response Models
    ScheduleEntropyResponse,
    analyze_energy_landscape,
    analyze_phase_transitions,
    # Tool Functions
    calculate_schedule_entropy,
    get_entropy_monitor_state,
    optimize_free_energy,
)

# Import time crystal tools
from .time_crystal_tools import (
    CheckpointStatusResponse,
    PeriodicityAnalysisResponse,
    RigidityAnalysisResponse,
    TimeCrystalHealthResponse,
    TimeCrystalObjectiveResponse,
    analyze_schedule_periodicity,
    analyze_schedule_rigidity,
    calculate_time_crystal_objective,
    get_checkpoint_status,
    get_time_crystal_health,
)

# Import VaR (Value-at-Risk) tools for schedule vulnerability analysis
# Import Game Theory tools for Nash equilibrium analysis
# Import Ecological dynamics tools (Lotka-Volterra supply/demand modeling)
# Import Kalman filter tools for workload trend analysis
# Import Fourier/FFT analysis tools for periodicity detection
# Import validate_schedule tool with ConstraintService integration
from .tools.validate_schedule import (
    ConstraintConfig,
)
from .tools.validate_schedule import (
    ScheduleValidationRequest as ConstraintValidationRequest,
)
from .tools.validate_schedule import (
    ScheduleValidationResponse as ConstraintValidationResponse,
)
from .tools.validate_schedule import (
    validate_schedule as validate_schedule_by_id,
)

# Configure logging - MUST use stderr for STDIO transport compatibility
# MCP uses stdout for JSON-RPC messages; logging to stdout corrupts the protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "Residency Scheduler",
    version="0.1.0",
    instructions=(
        "MCP server for medical residency scheduling with ACGME compliance, "
        "conflict detection, and workforce optimization"
    ),
)


# =============================================================================
# MCP Prompts - Tool Usage Requirements
# =============================================================================
# These prompts are injected into any LLM that connects to this MCP server,
# ensuring consistent tool usage regardless of the client (Claude, GPT, etc.)


@mcp.prompt()
async def tool_usage_requirements() -> str:
    """
    Required tool usage patterns for medical residency scheduling.

    This prompt injects tool usage requirements into the LLM context,
    ensuring all AI assistants follow proper workflows when working
    with the scheduling system.
    """
    return """
REQUIRED MCP TOOL USAGE FOR RESIDENCY SCHEDULING:

1. SCHEDULE VALIDATION (Before any schedule modification):
   - MUST run: validate_schedule_tool
   - Catches ACGME violations, coverage gaps, and supervision issues before implementation
   - Never edit schedule code without validating first

2. DOMAIN KNOWLEDGE (Before answering domain questions):
   - MUST query: rag_search
   - Contains ACGME rules, scheduling policies, swap procedures, and institutional knowledge
   - 67+ documents indexed with semantic search

3. RESILIENCE CHECK (Before capacity or staffing changes):
   - MUST check: get_defense_level_tool
   - Shows current utilization (80% threshold), N-1/N-2 vulnerability status
   - Prevents decisions that degrade system resilience

4. COMPLIANCE REPORTING (After schedule generation):
   - SHOULD run: check_mtf_compliance_tool
   - Generates military-style readiness report (DRRS ratings)
   - Includes circuit breaker status and SITREP summary

5. SWAP ANALYSIS (Before processing swap requests):
   - MUST run: analyze_swap_candidates_tool
   - Finds compatible swap partners with safety checks
   - Validates ACGME compliance for proposed swaps

TOOL QUICK REFERENCE:
| Scenario                  | Tool                        |
|---------------------------|-----------------------------|
| ACGME compliance question | rag_search                  |
| Schedule validation       | validate_schedule_tool      |
| Resilience status         | get_defense_level_tool      |
| System health             | check_circuit_breakers_tool |
| Swap compatibility        | analyze_swap_candidates_tool|
| Fatigue assessment        | run_frms_assessment_tool    |
| Conflict detection        | detect_conflicts_tool       |

ARMORY (Advanced Analysis):
For deep scientific analysis, activate specialized tool domains:
- biology: Burnout Rt, epidemiology, creep fatigue
- resilience_advanced: Hub centrality, blast radius, cognitive load
- physics: Phase transitions, entropy, time crystals
- operations_research: Shapley values, equity metrics, Erlang coverage

Set ARMORY_DOMAINS environment variable or use /armory skill.

These tools exist to prevent errors and ensure ACGME compliance. Use them.
"""


# =============================================================================
# Armory Conditional Loading
# =============================================================================
# Import armory loader for conditional tool registration
from .armory.loader import ALL_ARMORY_TOOLS, get_armory_status, should_load_tool


def armory_tool(tool_name: str):
    """
    Decorator for armory tools - only registers if domain is enabled.

    Usage:
        @armory_tool("calculate_schedule_entropy_tool")
        async def calculate_schedule_entropy_tool(...):
            ...

    Core tools should continue to use @mcp.tool() directly.
    """
    def decorator(func):
        if should_load_tool(tool_name):
            return mcp.tool()(func)
        else:
            # Return a no-op function that won't be registered
            logger.debug(f"Armory tool not loaded (domain disabled): {tool_name}")
            return func
    return decorator

# Log armory status
_armory_status = get_armory_status()
if _armory_status["effective_domains"]:
    logger.info(f"Armory domains active: {_armory_status['effective_domains']}")
else:
    logger.info(f"Armory disabled ({len(ALL_ARMORY_TOOLS)} tools available via ARMORY_DOMAINS env var)")


def parse_date_range(date_range: str) -> tuple[date, date]:
    """
    Parse a date_range preset into start and end dates.

    Args:
        date_range: Date range preset string:
            - "current" or "today": Today only
            - "week" or "this-week": Next 7 days
            - "month" or "this-month": Next 30 days
            - "YYYY-MM-DD:YYYY-MM-DD": Explicit date range
            - Any other value: Default to 30 days

    Returns:
        Tuple of (start_date, end_date) as date objects.
    """
    today = date.today()

    # Normalize the input
    range_lower = date_range.lower().strip()

    if range_lower in ("current", "today"):
        return today, today
    elif range_lower in ("week", "this-week"):
        return today, today + timedelta(days=7)
    elif range_lower in ("month", "this-month"):
        return today, today + timedelta(days=30)
    elif ":" in date_range:
        # Try to parse as explicit range "YYYY-MM-DD:YYYY-MM-DD"
        try:
            parts = date_range.split(":")
            if len(parts) == 2:
                start = date.fromisoformat(parts[0].strip())
                end = date.fromisoformat(parts[1].strip())
                return start, end
        except ValueError:
            # Invalid format, fall through to default
            pass

    # Default: next 30 days
    return today, today + timedelta(days=30)


# Register Resources


@mcp.resource("schedule://status/{date_range}")
async def schedule_status_resource(
    date_range: str = "current",
) -> ScheduleStatusResource:
    """
    Get current schedule status.

    Provides comprehensive view of assignments, coverage metrics, and active issues.

    Args:
        date_range: Date range preset:
            - "current" or "today": Today only
            - "week" or "this-week": Next 7 days
            - "month" or "this-month": Next 30 days
            - "YYYY-MM-DD:YYYY-MM-DD": Explicit date range
            - Any other value: Default to 30 days

    Returns:
        Current schedule status with assignments and metrics
    """
    start, end = parse_date_range(date_range)
    return await get_schedule_status(start_date=start, end_date=end)


@mcp.resource("schedule://compliance/{date_range}")
async def compliance_summary_resource(
    date_range: str = "current",
) -> ComplianceSummaryResource:
    """
    Get ACGME compliance summary.

    Analyzes schedule for work hour violations, supervision requirements,
    and duty hour restrictions.

    Args:
        date_range: Date range preset:
            - "current" or "today": Today only
            - "week" or "this-week": Next 7 days
            - "month" or "this-month": Next 30 days
            - "YYYY-MM-DD:YYYY-MM-DD": Explicit date range
            - Any other value: Default to 30 days

    Returns:
        Compliance summary with violations and recommendations
    """
    start, end = parse_date_range(date_range)
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
        conflict_types=list(conflict_types) if conflict_types else None,  # type: ignore
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


# Database Backup Tools


@mcp.tool()
async def create_backup_tool(
    strategy: str = "full",
    description: str = "",
) -> CreateBackupResult:
    """
    Create a database backup.

    Triggers backup creation via the backend API, which runs the backup
    script and creates a compressed PostgreSQL dump.

    Args:
        strategy: Backup strategy - "full", "incremental", or "differential"
        description: Optional description for audit trail

    Returns:
        CreateBackupResult with backup details or error

    Example:
        # Create a full backup before deployment
        result = await create_backup_tool(
            strategy="full",
            description="Pre-deployment backup"
        )

        if result.success:
            print(f"Backup created: {result.backup.backup_id}")
    """
    return await create_backup(strategy=strategy, description=description)


@mcp.tool()
async def list_backups_tool(
    limit: int = 50,
    strategy: str | None = None,
) -> ListBackupsResult:
    """
    List available database backups.

    Retrieves list of backups from the backend API with metadata
    and storage statistics.

    Args:
        limit: Maximum backups to return (default 50, max 100)
        strategy: Filter by strategy type (optional)

    Returns:
        ListBackupsResult with backups and storage stats

    Example:
        # List recent backups
        result = await list_backups_tool(limit=10)
        for backup in result.backups:
            print(f"{backup.backup_id}: {backup.size_mb}MB ({backup.created_at})")
    """
    return await list_backups(limit=limit, strategy=strategy)


@mcp.tool()
async def restore_backup_tool(
    backup_id: str,
    dry_run: bool = True,
) -> RestoreBackupResult:
    """
    Restore database from a backup.

    WARNING: Non-dry-run will replace ALL data in the database.
    Always run with dry_run=True first to preview the restore.

    Args:
        backup_id: ID of backup to restore
        dry_run: If True, preview restore without applying (default True)

    Returns:
        RestoreBackupResult with status and message

    Example:
        # Preview restore first
        preview = await restore_backup_tool(
            backup_id="residency_scheduler_20260116_165316",
            dry_run=True
        )

        # If preview looks good, actually restore (DANGEROUS!)
        # result = await restore_backup_tool(
        #     backup_id="residency_scheduler_20260116_165316",
        #     dry_run=False
        # )
    """
    return await restore_backup(backup_id=backup_id, dry_run=dry_run)


@mcp.tool()
async def verify_backup_tool(
    backup_id: str,
) -> VerifyBackupResult:
    """
    Verify backup integrity.

    Checks that the backup file exists and calculates its checksum
    for integrity verification.

    Args:
        backup_id: ID of backup to verify

    Returns:
        VerifyBackupResult with checksum and validity status

    Example:
        result = await verify_backup_tool(
            backup_id="residency_scheduler_20260116_165316"
        )

        if result.valid:
            print(f"Backup valid. Checksum: {result.checksum}")
        else:
            print(f"Backup invalid: {result.error}")
    """
    return await verify_backup(backup_id=backup_id)


@mcp.tool()
async def get_backup_status_tool() -> BackupStatusResult:
    """
    Get backup system health status.

    Returns the age of the latest backup, total backup count,
    storage usage, and any warnings about backup health.

    Returns:
        BackupStatusResult with health indicators and warnings

    Example:
        result = await get_backup_status_tool()

        if result.healthy:
            print(f"Backup system healthy. Latest: {result.latest_backup_id}")
        else:
            print(f"Warnings: {result.warnings}")
    """
    return await get_backup_status()


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
            f"{[level.value for level in LoadSheddingLevelEnum]}"
        ) from e

    return await execute_sacrifice_hierarchy(level_enum, simulate_only)


@armory_tool("analyze_homeostasis_tool")
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


@armory_tool("calculate_blast_radius_tool")
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
    request = BlastRadiusAnalysisRequest(zone_id=zone_id, check_all_zones=check_all_zones)
    return await calculate_blast_radius(request)


@armory_tool("analyze_le_chatelier_tool")
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
    request = LeChatelierAnalysisRequest(include_stress_prediction=include_stress_prediction)
    return await analyze_le_chatelier(request)


@armory_tool("analyze_hub_centrality_tool")
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


@armory_tool("assess_cognitive_load_tool")
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
    request = CognitiveLoadRequest(session_id=session_id, include_queue_status=include_queue_status)
    return await assess_cognitive_load(request)


@armory_tool("get_behavioral_patterns_tool")
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


@armory_tool("analyze_stigmergy_tool")
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
        raise ValueError(f"Invalid test_suite: {test_suite}. Must be 'basic' or 'full'") from e

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


# =============================================================================
# Empirical Testing Tools
# =============================================================================


@mcp.tool()
async def benchmark_solvers_tool(
    solvers: list[str] | None = None,
    scenario_count: int = 10,
    timeout_per_run: int = 60,
) -> SolverBenchmarkResult:
    """
    Benchmark scheduling solvers head-to-head.

    Runs each solver on identical scenarios and compares runtime,
    violation count, coverage, and fairness. Use this to determine
    which solver should be the default.

    Args:
        solvers: Solvers to test (default: all available)
        scenario_count: Number of test scenarios
        timeout_per_run: Timeout per solver run in seconds

    Returns:
        Comparison results with winner by metric and recommendations

    Example:
        # Compare all solvers
        result = await benchmark_solvers_tool()

        # Compare specific solvers
        result = await benchmark_solvers_tool(
            solvers=["greedy", "cp_sat"],
            scenario_count=20
        )
    """
    return await benchmark_solvers(
        solvers=solvers,
        scenario_count=scenario_count,
        timeout_per_run=timeout_per_run,
    )


@mcp.tool()
async def benchmark_constraints_tool(
    test_schedules: str = "historical",
) -> ConstraintBenchmarkResult:
    """
    Measure constraint effectiveness and yield.

    Analyzes which constraints catch real issues (high yield) vs
    generate false positives (low yield). Identifies candidates
    for removal.

    Args:
        test_schedules: Type of schedules to test against
            - "historical": Use past schedules
            - "synthetic": Generate test schedules
            - "edge_cases": Focus on boundary conditions

    Returns:
        Constraint statistics with high/low yield lists

    Example:
        result = await benchmark_constraints_tool()
        print(f"High yield: {result.high_yield}")
        print(f"Remove candidates: {result.candidates_for_removal}")
    """
    return await benchmark_constraints(test_schedules=test_schedules)


@mcp.tool()
async def ablation_study_tool(
    module_path: str,
) -> AblationResult:
    """
    Test impact of removing a module.

    Analyzes what would happen if a module were removed:
    - How many lines of code
    - What imports this module
    - What tests would break
    - Whether it's safe to remove

    Args:
        module_path: Path relative to backend/app/
            Examples: "scheduling/tensegrity/", "resilience/stigmergy.py"

    Returns:
        Ablation analysis with safety recommendation

    Example:
        # Check if tensegrity solver can be removed
        result = await ablation_study_tool("scheduling/tensegrity/")
        if result.safe_to_remove:
            print(f"Safe to remove: {result.module_size_lines} lines")
    """
    return await ablation_study(module_path=module_path)


@mcp.tool()
async def benchmark_resilience_tool(
    modules: list[str] | None = None,
) -> ResilienceBenchmarkResult:
    """
    Compare resilience framework components.

    Evaluates each resilience module for:
    - Detection rate (true positives)
    - False alarm rate
    - Complexity (lines of code)
    - Value score (detection - false alarms)

    Args:
        modules: Specific modules to test (default: all)

    Returns:
        Module statistics with high-value and cut-candidate lists

    Example:
        result = await benchmark_resilience_tool()
        print(f"High value: {result.high_value}")
        print(f"Cut candidates: {result.cut_candidates}")
    """
    return await benchmark_resilience(modules=modules)


@mcp.tool()
async def module_usage_analysis_tool(
    entry_points: list[str] | None = None,
) -> ModuleUsageResult:
    """
    Analyze which modules are actually used.

    Traces imports from entry points to find:
    - Reachable modules (used)
    - Unreachable modules (dead code candidates)
    - Hot paths (frequently imported)
    - Cold paths (rarely imported)

    Args:
        entry_points: Starting points for analysis
            Default: ["main", "api", "scheduling"]

    Returns:
        Usage analysis with dead code statistics

    Example:
        result = await module_usage_analysis_tool()
        print(f"Dead code: {result.dead_code_lines} lines")
        print(f"Unreachable: {result.unreachable_modules}")
    """
    return await module_usage_analysis(entry_points=entry_points)


# =============================================================================
# Research-to-Tool Conversions (Game Theory, Complex Systems, Signal Processing)
# Time Crystal Scheduling Tools
# =============================================================================


@armory_tool("calculate_shapley_workload_tool")
async def calculate_shapley_workload_tool(
    faculty_ids: list[str],
    start_date: str,
    end_date: str,
    num_samples: int = 1000,
) -> dict:
    """
    Calculate Shapley values for fair workload distribution.

    Uses cooperative game theory to determine each faculty member's fair share
    of workload based on their marginal contribution to schedule coverage.

    The Shapley value is the unique fair division satisfying:
    - Efficiency: Sum of all values = total value
    - Symmetry: Identical players get identical payoffs
    - Null player: Zero contribution = zero payoff

    Args:
        faculty_ids: List of faculty member IDs to analyze (minimum 2)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        num_samples: Monte Carlo samples (100-10000, default 1000)

    Returns:
        Dictionary with per-faculty Shapley values and equity metrics:
        - shapley_value: Normalized contribution (0-1)
        - marginal_contribution: Blocks covered uniquely
        - fair_workload_target: Hours based on Shapley proportion
        - current_workload: Actual hours assigned
        - equity_gap: +/- hours from fair target

    Example:
        result = await calculate_shapley_workload_tool(
            faculty_ids=["fac-001", "fac-002", "fac-003"],
            start_date="2025-01-01",
            end_date="2025-03-31"
        )
        # Dr. Smith: Shapley=35.2%, Gap=+39.5 hours (overworked)
    """
    # Import here to avoid circular imports
    from uuid import UUID

    try:
        parsed_faculty_ids = [UUID(fid) for fid in faculty_ids]
        parsed_start = date.fromisoformat(start_date)
        parsed_end = date.fromisoformat(end_date)
    except ValueError as e:
        return {
            "error": f"Invalid input format: {e}",
            "status": "failed",
        }

    # For now, return placeholder with structure
    # TODO: Connect to actual ShapleyValueService when DB is available
    logger.info(
        f"Calculating Shapley values for {len(faculty_ids)} faculty "
        f"from {start_date} to {end_date} ({num_samples} samples)"
    )

    return {
        "status": "success",
        "message": "Shapley value calculation completed",
        "faculty_count": len(faculty_ids),
        "date_range": {"start": start_date, "end": end_date},
        "num_samples": num_samples,
        "results": {
            fid: {
                "shapley_value": round(1.0 / len(faculty_ids), 3),
                "marginal_contribution": 0.0,
                "fair_workload_target": 0.0,
                "current_workload": 0.0,
                "equity_gap": 0.0,
            }
            for fid in faculty_ids
        },
        "summary": {
            "total_workload": 0.0,
            "equity_gap_std_dev": 0.0,
            "overworked_count": 0,
            "underworked_count": 0,
        },
        "note": "Connect to ShapleyValueService for real calculations",
    }


@armory_tool("detect_critical_slowing_down_tool")
async def detect_critical_slowing_down_tool(
    utilization_history: list[float],
    coverage_history: list[float] | None = None,
    days_lookback: int = 60,
) -> dict:
    """
    Detect critical slowing down for early warning of cascade failures.

    Monitors three early warning signals from Self-Organized Criticality (SOC):
    1. Relaxation time (τ) - recovery time from perturbations (threshold: > 48 hours)
    2. Variance trend - increasing instability (threshold: slope > 0.1)
    3. Autocorrelation (AC1) - loss of resilience (threshold: > 0.7)

    When 2+ signals trigger, the system is approaching a phase transition
    with 2-4 week warning window before cascade failure.

    Args:
        utilization_history: Daily utilization values (0.0 to 1.0)
        coverage_history: Optional daily coverage rates for enhanced analysis
        days_lookback: Days of history to analyze (default: 60)

    Returns:
        Dictionary with early warning assessment:
        - is_critical: Whether approaching critical point
        - warning_level: GREEN/YELLOW/ORANGE/RED
        - signals_triggered: Count of warning signals (0-3)
        - estimated_days_to_critical: Projected time to failure
        - recommendations: Actionable insights
        - immediate_actions: Urgent steps if critical

    Example:
        result = await detect_critical_slowing_down_tool(
            utilization_history=[0.75, 0.78, 0.82, 0.85, 0.88, ...],
            days_lookback=60
        )
        if result["is_critical"]:
            print(f"WARNING: {result['estimated_days_to_critical']} days to failure")
    """
    import numpy as np

    if len(utilization_history) < 10:
        return {
            "error": "Insufficient data: need at least 10 data points",
            "status": "failed",
        }

    # Trim to lookback period
    data = utilization_history[-days_lookback:]
    n = len(data)

    # Calculate early warning signals
    # 1. Variance trend (rolling window)
    window_size = min(7, n // 3)
    if window_size >= 2:
        variances = []
        for i in range(n - window_size + 1):
            variances.append(np.var(data[i : i + window_size]))
        variance_slope = (variances[-1] - variances[0]) / len(variances) if variances else 0
    else:
        variance_slope = 0.0

    # 2. Autocorrelation at lag-1
    if n >= 2:
        ac1 = float(np.corrcoef(data[:-1], data[1:])[0, 1])
    else:
        ac1 = 0.0

    # 3. Relaxation time approximation (simplified)
    # In a real implementation, this would track perturbation recovery
    mean_util = np.mean(data)
    deviations = np.abs(np.array(data) - mean_util)
    relaxation_proxy = float(np.mean(deviations) * 24)  # hours

    # Count triggered signals
    signals = 0
    triggered = []

    if relaxation_proxy > 48.0:
        signals += 1
        triggered.append(f"Relaxation time high: {relaxation_proxy:.1f}h > 48h threshold")

    if variance_slope > 0.1:
        signals += 1
        triggered.append(f"Variance increasing: slope {variance_slope:.3f} > 0.1 threshold")

    if ac1 > 0.7:
        signals += 1
        triggered.append(f"Autocorrelation high: AC1 {ac1:.3f} > 0.7 threshold")

    # Determine warning level
    warning_levels = {0: "GREEN", 1: "YELLOW", 2: "ORANGE", 3: "RED"}
    warning_level = warning_levels.get(signals, "RED")

    # Estimate days to critical (simplified)
    if signals >= 2 and variance_slope > 0:
        # Rough estimate based on trend
        days_to_critical = max(7, int(30 * (1 - mean_util) / (variance_slope + 0.01)))
    else:
        days_to_critical = None

    # Generate recommendations
    recommendations = []
    immediate_actions = []

    if warning_level == "GREEN":
        recommendations.append("System healthy - continue standard monitoring")
    elif warning_level == "YELLOW":
        recommendations.append("Single warning signal detected - increase monitoring frequency")
        recommendations.append("Review recent schedule changes for destabilizing patterns")
    elif warning_level == "ORANGE":
        recommendations.append("Multiple warning signals - activate preventive measures")
        immediate_actions.append("Reduce utilization below 75%")
        immediate_actions.append("Prepare backup coverage plans")
    else:  # RED
        recommendations.append("Critical state - emergency protocols required")
        immediate_actions.append("Activate fallback schedules immediately")
        immediate_actions.append("Halt non-essential schedule changes")
        immediate_actions.append("Brief leadership on cascade risk")

    logger.info(
        f"SOC analysis: {warning_level} ({signals}/3 signals), "
        f"utilization mean={mean_util:.2f}, AC1={ac1:.3f}"
    )

    return {
        "status": "success",
        "is_critical": signals >= 2,
        "warning_level": warning_level,
        "confidence": min(1.0, n / 60),
        "data_quality": "excellent" if n >= 60 else "good" if n >= 30 else "fair",
        "signals_triggered": signals,
        "triggered_signals": triggered,
        "estimated_days_to_critical": days_to_critical,
        "metrics": {
            "relaxation_time_hours": round(relaxation_proxy, 2),
            "variance_slope": round(variance_slope, 4),
            "autocorrelation_ac1": round(ac1, 4),
            "mean_utilization": round(mean_util, 4),
        },
        "thresholds": {
            "relaxation_time_hours": 48.0,
            "variance_slope": 0.1,
            "autocorrelation_ac1": 0.7,
        },
        "recommendations": recommendations,
        "immediate_actions": immediate_actions,
        "days_analyzed": n,
    }


@armory_tool("detect_schedule_changepoints_tool")
async def detect_schedule_changepoints_tool(
    daily_values: list[float],
    dates: list[str],
    methods: list[str] | None = None,
) -> dict:
    """
    Detect regime shifts and structural breaks in schedule patterns.

    Uses signal processing algorithms to identify when schedule patterns
    fundamentally changed (policy updates, staffing transitions, etc.):
    - CUSUM: Detects mean shifts (upward/downward workload changes)
    - PELT: Optimal segmentation for multiple change points

    Args:
        daily_values: Daily workload/utilization values
        dates: Corresponding dates in YYYY-MM-DD format
        methods: Detection methods (default: ["cusum", "pelt"])

    Returns:
        Dictionary with detected change points per method:
        - change_points: List of detected regime shifts
        - Each point includes: index, timestamp, change_type, magnitude, confidence
        - segmentation_quality: How well the segments explain the data

    Example:
        result = await detect_schedule_changepoints_tool(
            daily_values=[8, 8, 8, 10, 12, 12, 12, 12],
            dates=["2025-01-01", "2025-01-02", ...],
            methods=["cusum", "pelt"]
        )
        # Detects mean shift at index 3 (2025-01-04): 8.0 → 12.0 hours
    """
    import numpy as np

    if len(daily_values) != len(dates):
        return {
            "error": "daily_values and dates must have same length",
            "status": "failed",
        }

    if len(daily_values) < 10:
        return {
            "error": "Need at least 10 data points for change point detection",
            "status": "failed",
        }

    methods = methods or ["cusum", "pelt"]
    series = np.array(daily_values, dtype=np.float64)
    n = len(series)

    results = {}

    # CUSUM detection
    if "cusum" in methods:
        mean = np.mean(series)
        std = np.std(series) + 1e-10
        standardized = (series - mean) / std

        threshold = 5.0
        s_high = 0.0
        s_low = 0.0
        change_points = []

        for t in range(1, n):
            s_high = max(0, s_high + standardized[t])
            s_low = min(0, s_low + standardized[t])

            if s_high > threshold:
                segment_start = max(0, t - 10)
                pre_mean = float(np.mean(series[segment_start:t]))
                post_mean = float(np.mean(series[t : min(t + 5, n)]))

                change_points.append({
                    "index": int(t),
                    "timestamp": dates[t] if t < len(dates) else "",
                    "change_type": "mean_shift_upward",
                    "magnitude": round(post_mean - pre_mean, 2),
                    "confidence": min(1.0, s_high / (threshold * 2)),
                    "description": f"Upward shift: {pre_mean:.1f} → {post_mean:.1f}",
                })
                s_high = 0

            if s_low < -threshold:
                segment_start = max(0, t - 10)
                pre_mean = float(np.mean(series[segment_start:t]))
                post_mean = float(np.mean(series[t : min(t + 5, n)]))

                change_points.append({
                    "index": int(t),
                    "timestamp": dates[t] if t < len(dates) else "",
                    "change_type": "mean_shift_downward",
                    "magnitude": round(post_mean - pre_mean, 2),
                    "confidence": min(1.0, abs(s_low) / (threshold * 2)),
                    "description": f"Downward shift: {pre_mean:.1f} → {post_mean:.1f}",
                })
                s_low = 0

        results["cusum"] = {
            "method": "cusum",
            "change_points": change_points,
            "num_changepoints": len(change_points),
            "algorithm_parameters": {"threshold": threshold, "drift": 0.0},
        }

    # Simplified PELT detection
    if "pelt" in methods:
        min_segment = 5
        change_points = []

        # Simple variance-based segmentation
        def segment_cost(start: int, end: int) -> float:
            if end - start < 2:
                return 0.0
            return float(np.var(series[start:end]) * (end - start))

        # Greedy search for change points
        current_pos = 0
        penalty = 1.0

        while current_pos < n - min_segment:
            best_cost = float("inf")
            best_split = None

            for split in range(current_pos + min_segment, n - min_segment):
                cost_one = segment_cost(current_pos, n)
                cost_two = segment_cost(current_pos, split) + segment_cost(split, n) + penalty

                if cost_two < cost_one and cost_two < best_cost:
                    best_cost = cost_two
                    best_split = split

            if best_split is not None and best_cost < segment_cost(current_pos, n):
                pre_mean = float(np.mean(series[max(0, best_split - min_segment) : best_split]))
                post_mean = float(np.mean(series[best_split : min(best_split + min_segment, n)]))

                change_points.append({
                    "index": int(best_split),
                    "timestamp": dates[best_split] if best_split < len(dates) else "",
                    "change_type": "segment_boundary",
                    "magnitude": round(abs(post_mean - pre_mean), 2),
                    "confidence": 0.7,
                    "description": f"Segment break: {pre_mean:.1f} → {post_mean:.1f}",
                })
                current_pos = best_split
            else:
                break

        results["pelt"] = {
            "method": "pelt",
            "change_points": change_points,
            "num_changepoints": len(change_points),
            "algorithm_parameters": {"penalty": penalty, "min_segment_length": min_segment},
        }

    # Combine and summarize
    all_changepoints = []
    for method_name, method_result in results.items():
        all_changepoints.extend(method_result.get("change_points", []))

    logger.info(
        f"Change point detection: CUSUM={len(results.get('cusum', {}).get('change_points', []))}, "
        f"PELT={len(results.get('pelt', {}).get('change_points', []))}"
    )

    return {
        "status": "success",
        "methods_used": methods,
        "data_points": n,
        "date_range": {"start": dates[0], "end": dates[-1]},
        "results": results,
        "total_changepoints": len(all_changepoints),
        "summary": {
            "mean_value": round(float(np.mean(series)), 2),
            "std_value": round(float(np.std(series)), 2),
            "min_value": round(float(np.min(series)), 2),
            "max_value": round(float(np.max(series)), 2),
        },
    }
async def analyze_schedule_rigidity_tool(
    current_assignments: list[dict] | None = None,
    proposed_assignments: list[dict] | None = None,
    current_schedule_id: str | None = None,
    proposed_schedule_id: str | None = None,
) -> RigidityAnalysisResponse:
    """
    Analyze schedule rigidity (anti-churn) between current and proposed schedules.

    Time crystal insight: Schedules should be "rigid" - small perturbations
    (like adding one absence) should NOT cause large-scale reshuffling.
    This measures schedule stability.

    Args:
        current_assignments: Current schedule as list of dicts with
            {person_id, block_id, template_id}
        proposed_assignments: Proposed schedule as list of dicts
        current_schedule_id: Alternative: ID of current schedule in database
        proposed_schedule_id: Alternative: ID of proposed schedule in database

    Returns:
        Rigidity analysis with stability metrics:
        - rigidity_score: 1.0 = identical, 0.0 = completely different
        - total_changes: Number of assignment differences
        - affected_people_count: How many people's schedules changed
        - severity: minimal/low/moderate/high/critical
        - recommendation: Actionable advice

    Example:
        # Compare two schedule versions
        result = await analyze_schedule_rigidity_tool(
            current_assignments=[
                {"person_id": "uuid1", "block_id": "block1", "template_id": "clinic"}
            ],
            proposed_assignments=[
                {"person_id": "uuid1", "block_id": "block1", "template_id": "OR"}
            ]
        )

        print(f"Rigidity: {result.rigidity_score}")  # 0.0 - complete change
        print(f"Severity: {result.severity}")
    """
    return await analyze_schedule_rigidity(
        current_schedule_id=current_schedule_id,
        proposed_schedule_id=proposed_schedule_id,
        current_assignments=current_assignments,
        proposed_assignments=proposed_assignments,
    )


# =============================================================================
# Composite/Advanced Resilience Tools
# =============================================================================


@mcp.tool()
async def get_unified_critical_index_tool(
    include_details: bool = True,
    top_n: int = 5,
) -> UnifiedCriticalIndexResponse:
    """
    Calculate unified critical index aggregating all resilience signals.

    Combines signals from three domains into a single actionable risk score:

    1. **Contingency (N-1/N-2 Vulnerability)** - Weight: 40%
       Faculty whose loss causes coverage gaps or cascade failures.

    2. **Epidemiology (Burnout Super-Spreader)** - Weight: 25%
       Faculty who can spread burnout through social connections.

    3. **Hub Analysis (Network Centrality)** - Weight: 35%
       Faculty who are structural "hubs" in the assignment network.

    Key Insight: A faculty member who is N-1 vulnerable, a super-spreader,
    AND a hub represents the highest concentration of organizational risk.

    Risk Patterns:
    - UNIVERSAL_CRITICAL: All three domains high - maximum risk
    - STRUCTURAL_BURNOUT: Contingency + Epidemiology high
    - INFLUENTIAL_HUB: Contingency + Hub high
    - SOCIAL_CONNECTOR: Epidemiology + Hub high
    - LOW_RISK: No domains elevated

    Args:
        include_details: Include individual faculty assessments
        top_n: Number of top-risk faculty to return (1-20)

    Returns:
        Unified critical index with composite risk score, risk pattern
        distribution, and prioritized intervention recommendations

    Example:
        result = await get_unified_critical_index_tool()
        if result.risk_level == "critical":
            print(f"ALERT: {result.universal_critical_count} faculty critical")
    """
    return await get_unified_critical_index(
        include_details=include_details,
        top_n=top_n,
    )


@armory_tool("analyze_schedule_periodicity_tool")
async def analyze_schedule_periodicity_tool(
    assignments: list[dict] | None = None,
    schedule_id: str | None = None,
    base_period_days: int = 7,
) -> PeriodicityAnalysisResponse:
    """
    Analyze natural periodicities in a schedule.

    Time crystal insight: Medical schedules have natural "drive periods"
    (7 days, 28 days) and emergent "subharmonic responses" (alternating
    weekends, Q4 call patterns). Detecting these helps preserve schedule
    structure during regeneration.

    Args:
        assignments: Schedule as list of dicts with {person_id, block_id, date}
        schedule_id: Alternative: ID of schedule in database
        base_period_days: Base period to look for (default: 7 for weekly)

    Returns:
        Periodicity analysis with:
        - fundamental_period_days: Strongest detected period
        - subharmonic_periods: Detected longer cycles [7, 14, 28]
        - periodicity_strength: 0-1 measure of periodic structure
        - detected_patterns: Human-readable pattern descriptions
        - recommendations: How to preserve detected patterns

    Example:
        result = await analyze_schedule_periodicity_tool(base_period_days=7)

        print(f"Detected periods: {result.subharmonic_periods}")
        # [7, 14, 28] - weekly, biweekly, ACGME 4-week
    """
    return await analyze_schedule_periodicity(
        schedule_id=schedule_id,
        assignments=assignments,
        base_period_days=base_period_days,
    )


@armory_tool("calculate_recovery_distance_tool")
async def calculate_recovery_distance_tool(
    start_date: str | None = None,
    end_date: str | None = None,
    max_events: int = 20,
    include_samples: bool = True,
) -> RecoveryDistanceResponse:
    """
    Calculate recovery distance metrics for schedule resilience.

    Recovery Distance (RD) measures minimum edits to restore feasibility
    after N-1 shocks. Inspired by graph-theoretic operations research.

    Lower RD = More resilient schedule (easier to recover)
    Higher RD = More brittle schedule (requires many changes)

    Event Types Tested:
    - Faculty absence: Single faculty unavailable
    - Resident sick day: Single resident unavailable

    Edit Operations:
    1. Swap: Exchange assignments between two people
    2. Move to backup: Reassign to pre-designated backup
    3. Reassign: Find any available qualified person

    Key Metrics:
    - rd_mean: Average recovery distance (good < 2.0)
    - rd_p95: 95th percentile for worst-case planning
    - breakglass_count: Events requiring >3 edits (emergency)
    - fragility_score: Overall schedule fragility (0-1)

    Args:
        start_date: Analysis start (YYYY-MM-DD), defaults to today
        end_date: Analysis end (YYYY-MM-DD), defaults to 30 days
        max_events: Maximum N-1 events to test (1-100)
        include_samples: Include sample individual results

    Returns:
        Recovery distance metrics with fragility score and recommendations

    Example:
        result = await calculate_recovery_distance_tool()
        if result.rd_p95 > 4:
            print("WARNING: High recovery cost in worst case")
    """
    return await calculate_recovery_distance(
        start_date=start_date,
        end_date=end_date,
        max_events=max_events,
        include_samples=include_samples,
    )


@armory_tool("assess_creep_fatigue_tool")
async def assess_creep_fatigue_tool(
    include_assessments: bool = True,
    top_n: int = 10,
) -> CreepFatigueResponse:
    """
    Assess burnout risk using materials science creep-fatigue analysis.

    Adapts materials science concepts to predict resident burnout:

    Creep Analysis (Time-Dependent Deformation):
    - PRIMARY: Adaptation phase, strain rate decreasing
    - SECONDARY: Steady-state, sustainable performance
    - TERTIARY: Accelerating damage, approaching burnout

    Uses Larson-Miller Parameter (LMP) to predict time-to-failure:
    - LMP = workload * (C + log10(duration))
    - LMP > 45.0 = high burnout risk
    - Safe operating: LMP < 31.5

    Fatigue Analysis (Cyclic Loading from Rotations):
    Uses S-N curves and Miner's Rule:
    - High stress rotations = fewer cycles to failure
    - Cumulative damage D = Sum(n_i / N_i)
    - Failure predicted when D >= 1.0

    Combined Risk: 60% creep + 40% fatigue

    Args:
        include_assessments: Include individual resident assessments
        top_n: Number of highest-risk residents to return (1-50)

    Returns:
        Creep-fatigue burnout predictions with LMP values and recommendations

    Example:
        result = await assess_creep_fatigue_tool()
        if result.tertiary_creep_count > 0:
            print(f"URGENT: {result.tertiary_creep_count} residents near burnout")
    """
    return await assess_creep_fatigue(
        include_assessments=include_assessments,
        top_n=top_n,
    )


@armory_tool("analyze_transcription_triggers_tool")
async def analyze_transcription_triggers_tool(
    include_tf_details: bool = True,
    include_constraint_status: bool = True,
) -> TranscriptionTriggersResponse:
    """
    Analyze transcription factor regulatory network for constraints.

    Applies gene regulatory network (GRN) concepts to constraint management:

    Biological Analogy:
    - Constraints = "Genes" in the scheduler genome
    - Transcription Factors (TFs) = Proteins controlling constraint weights
    - Signals = External events (deployment, crisis) inducing TFs
    - Chromatin State = Constraint accessibility (open/silenced)

    TF Types:
    - MASTER: Always active (PatientSafety_MR, ACGMECompliance_MR)
    - ACTIVATOR: Increases constraint weight when expressed
    - REPRESSOR: Decreases/disables constraints (e.g., CrisisMode_TF)
    - PIONEER: Can re-open silenced constraints
    - DUAL: Context-dependent action

    Network Analysis:
    - Positive feedback: Amplifies signals
    - Negative feedback: Stabilizes system
    - Feed-forward: Filters noise

    Args:
        include_tf_details: Include active TF details
        include_constraint_status: Include constraint regulation status

    Returns:
        GRN analysis with TF expression, constraint weights, regulatory loops

    Example:
        result = await analyze_transcription_triggers_tool()
        print(f"Active TFs: {result.active_tfs}/{result.total_tfs}")
        for tf in result.active_tfs_list:
            if tf.tf_type == "repressor" and tf.is_active:
                print(f"Repressor active: {tf.name}")
    """
    return await analyze_transcription_triggers(
        include_tf_details=include_tf_details,
        include_constraint_status=include_constraint_status,
    )


# =============================================================================
# Epidemiological Burnout Modeling Tools (Tier 4)
# =============================================================================


@armory_tool("calculate_burnout_rt_tool")
async def calculate_burnout_rt_tool(
    burned_out_provider_ids: list[str],
    time_window_days: int = 28,
) -> BurnoutRtResponse:
    """
    Calculate the effective reproduction number (Rt) for burnout spread.

    Applies epidemiological SIR modeling to understand burnout transmission
    dynamics through social networks. The reproduction number (Rt) indicates
    whether burnout is spreading or declining in the organization.

    Scientific Background:
    - Burnout spreads through social networks like an infectious disease
    - Emotional contagion occurs through close work contacts (Bakker et al., 2009)
    - High-connectivity individuals can become "superspreaders"
    - Breaking transmission chains requires targeted interventions

    Key Metrics:
    - Rt < 1: Epidemic declining (each case causes <1 secondary case)
    - Rt = 1: Endemic state (stable but not declining)
    - Rt > 1: Epidemic growing (each case causes >1 secondary cases)
    - Rt > 2: Rapid spread (aggressive intervention needed)
    - Rt > 3: Crisis level (emergency intervention required)

    Args:
        burned_out_provider_ids: List of provider IDs currently experiencing burnout.
            These are the "index cases" from which secondary cases are traced.
        time_window_days: Time window in days for tracing secondary cases (default: 28).
            Longer windows capture more transmission but may include unrelated cases.

    Returns:
        BurnoutRtResponse with reproduction number, status, and intervention recommendations.

    Example:
        # Calculate Rt for providers with high burnout
        result = await calculate_burnout_rt_tool(
            burned_out_provider_ids=["provider-1", "provider-2", "provider-3"],
            time_window_days=28
        )

        if result.rt > 1.0:
            print(f"ALERT: Burnout spreading! Rt={result.rt:.2f}")
            for intervention in result.interventions:
                print(f"  - {intervention}")
        else:
            print(f"Burnout declining. Rt={result.rt:.2f}")
    """
    return await calculate_burnout_rt(
        burned_out_provider_ids=burned_out_provider_ids,
        time_window_days=time_window_days,
    )


@armory_tool("simulate_burnout_spread_tool")
async def simulate_burnout_spread_tool(
    initial_infected_ids: list[str],
    infection_rate: float = 0.05,
    recovery_rate: float = 0.02,
    simulation_weeks: int = 52,
) -> BurnoutSpreadSimulationResponse:
    """
    Run SIR epidemic simulation for burnout spread through social network.

    Uses the classic SIR (Susceptible-Infected-Recovered) epidemiological model
    to project how burnout might spread through the organization's social network
    over time. This helps identify:
    - Whether burnout will become epidemic (R0 > 1) or die out (R0 < 1)
    - When peak infection might occur
    - How many people might ultimately be affected

    Scientific Background:
    - SIR model divides population into Susceptible, Infected, Recovered compartments
    - Transmission occurs when infected contacts susceptible
    - Recovery rate determines average duration of burnout
    - R0 = beta/gamma predicts epidemic trajectory
    - Herd immunity threshold = 1 - 1/R0

    Args:
        initial_infected_ids: List of provider IDs to seed as initially burned out.
            These are the "patient zero" cases that start the simulation.
        infection_rate: Beta - probability of burnout transmission per contact per week.
            Typical range: 0.01-0.15. Higher = faster spread.
        recovery_rate: Gamma - probability of recovery per week.
            Typical range: 0.001-0.05. Higher = faster recovery.
            Note: 1/gamma = average weeks of burnout (e.g., 0.02 = 50 weeks avg)
        simulation_weeks: Number of weeks to simulate (default: 52 = 1 year).

    Returns:
        BurnoutSpreadSimulationResponse with trajectory and peak analysis.

    Example:
        # Simulate 1 year of burnout spread starting with 3 cases
        result = await simulate_burnout_spread_tool(
            initial_infected_ids=["provider-1", "provider-2", "provider-3"],
            infection_rate=0.05,
            recovery_rate=0.02,
            simulation_weeks=52
        )

        print(f"R0: {result.r0:.2f}")
        print(f"Herd immunity threshold: {result.herd_immunity_threshold:.1%}")
        print(f"Peak: {result.peak_infected} infected at week {result.peak_week}")

        if result.epidemic_died_out:
            print("Good news: Epidemic died out naturally")
        else:
            print("WARNING: Epidemic still active - intervention needed")
    """
    return await simulate_burnout_spread(
        initial_infected_ids=initial_infected_ids,
        infection_rate=infection_rate,
        recovery_rate=recovery_rate,
        simulation_weeks=simulation_weeks,
    )


@armory_tool("simulate_burnout_contagion_tool")
async def simulate_burnout_contagion_tool(
    provider_burnout_scores: dict[str, float],
    infection_rate: float = 0.05,
    recovery_rate: float = 0.01,
    simulation_iterations: int = 50,
    max_interventions: int = 10,
) -> BurnoutContagionResponse:
    """
    Simulate burnout contagion through social network using SIS model.

    Uses the SIS (Susceptible-Infected-Susceptible) epidemiological model
    on the provider collaboration network. Unlike SIR, SIS allows reinfection -
    appropriate for burnout which can recur even after recovery.

    Key Features:
    - Identifies superspreaders (high burnout + high network centrality)
    - Recommends targeted network interventions to break transmission
    - Predicts cascade severity and peak infection timing
    - Uses network analysis (degree, betweenness, eigenvector centrality)

    Scientific Background:
    - Network topology determines outbreak severity
    - Superspreaders (high-degree + high-burnout nodes) amplify contagion
    - Edge removal, workload reduction, and quarantine can break transmission
    - Centrality metrics identify critical nodes for intervention

    Args:
        provider_burnout_scores: Dictionary mapping provider_id -> burnout score (0.0-1.0).
            Scores >= 0.5 are considered "infected" (high burnout).
        infection_rate: Beta - transmission probability per contact per iteration.
            Typical range: 0.01-0.15.
        recovery_rate: Lambda - recovery probability per iteration.
            Typical range: 0.001-0.05.
        simulation_iterations: Number of iterations to simulate (default: 50).
        max_interventions: Maximum interventions to recommend (default: 10).

    Returns:
        BurnoutContagionResponse with superspreaders, interventions, and trajectory.

    Example:
        # Simulate contagion with burnout scores for team
        scores = {
            "provider-1": 0.7,   # High burnout
            "provider-2": 0.3,   # Low burnout
            "provider-3": 0.9,   # Very high burnout - potential superspreader
            "provider-4": 0.4,   # Moderate
            "provider-5": 0.6,   # Elevated
        }
        result = await simulate_burnout_contagion_tool(
            provider_burnout_scores=scores,
            infection_rate=0.05,
            recovery_rate=0.01
        )

        print(f"Contagion Risk: {result.contagion_risk}")
        print(f"Final infection rate: {result.final_infection_rate:.1%}")

        # Identify superspreaders
        print(f"Superspreaders ({result.total_superspreaders}):")
        for ss in result.superspreaders:
            print(f"  - {ss.provider_id}: score={ss.superspreader_score:.2f}, "
                  f"contacts={ss.direct_contacts}, risk={ss.risk_level}")

        # Get intervention recommendations
        print(f"Recommended Interventions:")
        for intervention in result.recommended_interventions:
            print(f"  - [{intervention.priority}] {intervention.intervention_type}: "
                  f"{intervention.reason}")
    """
    return await simulate_burnout_contagion(
        provider_burnout_scores=provider_burnout_scores,
        infection_rate=infection_rate,
        recovery_rate=recovery_rate,
        simulation_iterations=simulation_iterations,
        max_interventions=max_interventions,
    )


# =============================================================================
# Circuit Breaker Tools (Distributed Systems Failure Isolation)
# =============================================================================


@mcp.tool()
async def check_circuit_breakers_tool() -> AllBreakersStatusResponse:
    """
    Get status of all registered circuit breakers.

    This tool retrieves comprehensive status information for all circuit
    breakers in the system, including their current state, failure rates,
    and recent state transitions. Based on the Netflix Hystrix pattern.

    Circuit Breaker States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Circuit tripped due to failures, requests fail fast (protects downstream)
    - HALF_OPEN: Testing recovery, limited requests allowed to verify service health

    Use Cases:
    - System health monitoring dashboards
    - Incident response (identify failing services)
    - Capacity planning (identify overloaded services)
    - Post-mortem analysis (review state transitions)

    Returns:
        AllBreakersStatusResponse with:
        - Total count of breakers in each state
        - Names of OPEN and HALF_OPEN breakers
        - Detailed status for each breaker (failure rates, request counts)
        - Overall system health assessment
        - Recommended actions

    Example:
        result = await check_circuit_breakers_tool()

        if result.open_breakers > 0:
            print(f"WARNING: {result.open_breakers} breakers are OPEN")
            for name in result.open_breaker_names:
                print(f"  - {name}")
            print(f"Recommendations:")
            for rec in result.recommendations:
                print(f"  * {rec}")
    """
    return await check_circuit_breakers()


@mcp.tool()
async def get_breaker_health_tool() -> BreakerHealthResponse:
    """
    Get aggregated health metrics for all circuit breakers.

    This tool provides a high-level health assessment across all circuit
    breakers, useful for dashboards, alerting, and trend analysis.

    Metrics include:
    - Total requests, failures, and rejections across all breakers
    - Overall and average failure rates
    - Identification of unhealthiest breakers
    - Trend analysis (improving, stable, degrading)

    Severity Levels:
    - HEALTHY: All breakers operating normally
    - WARNING: Some breakers have elevated failure rates
    - CRITICAL: Breakers are OPEN, service degradation occurring
    - EMERGENCY: System-wide circuit breaker failures

    Returns:
        BreakerHealthResponse with:
        - Aggregated metrics across all breakers
        - List of breakers needing immediate attention
        - Trend analysis
        - Severity assessment
        - Prioritized recommendations

    Example:
        health = await get_breaker_health_tool()

        # Use for alerting
        if health.severity.value in ("critical", "emergency"):
            send_alert(f"Circuit breaker alert: {health.severity.value}")

        # Dashboard metrics
        print(f"Overall failure rate: {health.metrics.overall_failure_rate*100:.1f}%")
        print(f"Breakers needing attention: {health.breakers_needing_attention}")
    """
    return await get_breaker_health()


@mcp.tool()
async def test_half_open_tool(
    breaker_name: str,
) -> HalfOpenTestResponse:
    """
    Test a circuit breaker in HALF_OPEN state to verify recovery progress.

    When a circuit breaker is in HALF_OPEN state, it allows limited test
    requests to determine if the downstream service has recovered. This
    tool provides information about the half-open state and recovery progress.

    Half-Open Recovery Process:
    1. Circuit opens after failure_threshold failures
    2. After timeout_seconds, circuit transitions to HALF_OPEN
    3. Limited requests are allowed through (half_open_max_calls)
    4. If success_threshold successes occur, circuit closes (recovery complete)
    5. If any failure occurs, circuit reopens (back to step 2)

    Use Cases:
    - Monitor service recovery progress
    - Verify downstream service health before allowing full traffic
    - Determine if manual intervention is needed

    Args:
        breaker_name: Name of the circuit breaker to test

    Returns:
        HalfOpenTestResponse with:
        - Whether breaker is in HALF_OPEN state
        - Recovery progress (successes / threshold)
        - Whether breaker is ready to close
        - Recommended next steps

    Example:
        # Check if database breaker is recovering
        result = await test_half_open_tool("database_connection")

        if result.is_half_open:
            progress = result.test_result
            print(f"Recovery progress: {progress.consecutive_successes}/"
                  f"{progress.success_threshold}")

            if progress.ready_to_close:
                print("Service has recovered! Next request will close circuit.")
        else:
            print(f"Breaker not in HALF_OPEN: {result.error_message}")
    """
    return await test_half_open_breaker(breaker_name)


@mcp.tool()
async def override_circuit_breaker_tool(
    breaker_name: str,
    action: str,
    reason: str,
) -> ManualOverrideResponse:
    """
    Manually override a circuit breaker state for emergency or maintenance.

    This tool allows manual control over circuit breaker state. Use with
    caution - overriding circuit breakers bypasses automatic failure protection.

    Available Actions:
    - open: Force circuit to OPEN state (reject all requests to protect system)
    - close: Force circuit to CLOSED state (allow all requests - verify service first!)
    - reset: Reset circuit to initial state (clear all metrics and history)

    When to Use:
    - open: Known service issues, planned maintenance, protecting from cascade
    - close: Verified service recovery, override after investigation
    - reset: After fixing underlying issue, start fresh

    Security Note:
    This action is logged for audit purposes. Overriding circuit breakers
    should only be done during planned maintenance or emergency situations.

    Args:
        breaker_name: Name of the circuit breaker to override
        action: Action to take: "open", "close", or "reset"
        reason: Reason for the override (stored in audit trail)

    Returns:
        ManualOverrideResponse with:
        - Success/failure status
        - Previous and current state
        - Timestamp for audit

    Raises:
        ValueError: If breaker_name not found or action is invalid

    Example:
        # Force close after verified recovery
        result = await override_circuit_breaker_tool(
            breaker_name="external_api",
            action="close",
            reason="Verified service recovery after deployment v2.3.1"
        )

        # Force open during known issues
        result = await override_circuit_breaker_tool(
            breaker_name="database",
            action="open",
            reason="Database failover in progress - preventing cascade failures"
        )

        # Reset after root cause fix
        result = await override_circuit_breaker_tool(
            breaker_name="payment_gateway",
            action="reset",
            reason="Completed remediation of payment gateway timeout issue"
        )
    """
    return await override_circuit_breaker(breaker_name, action, reason)


# =============================================================================
# Optimization and Analytics Tools
# =============================================================================


@armory_tool("optimize_erlang_coverage_tool")
async def optimize_erlang_coverage_tool(
    specialty: str,
    arrival_rate: float,
    service_time_minutes: float,
    target_wait_minutes: float = 15.0,
    target_wait_probability: float = 0.05,
    max_servers: int = 20,
) -> ErlangCoverageResponse:
    """
    Optimize specialist staffing using telecommunications Erlang-C formulas.

    Applies M/M/c queuing theory (Markovian arrival, Markovian service, c servers)
    to determine optimal specialist coverage, balancing utilization against wait
    times. This is the same mathematical model used by call centers worldwide.

    Key Concepts:
    - Offered Load (A): arrival_rate * service_time = average work per time unit
    - Erlang C: Probability a request must wait (with infinite queue)
    - Service Level: Percentage of requests served within target wait time
    - 80% Utilization Threshold: Above this, wait times grow exponentially

    Typical Medical Applications:
    - ER specialist coverage (orthopedic surgeon within 15 min)
    - Call schedule optimization (consultant callback times)
    - Procedure coverage (specialist availability for emergent cases)

    Args:
        specialty: Name of specialty (e.g., "Orthopedic Surgery", "Cardiology")
        arrival_rate: Average requests per hour (e.g., 2.5 cases/hour)
        service_time_minutes: Average time per case in minutes (e.g., 30 min)
        target_wait_minutes: Target wait time for service level (default: 15 min)
        target_wait_probability: Maximum acceptable wait probability (default: 5%)
        max_servers: Maximum servers to consider (default: 20)

    Returns:
        Optimal staffing recommendation with staffing table and metrics

    Example:
        # Optimize ER orthopedic coverage
        result = await optimize_erlang_coverage_tool(
            specialty="Orthopedic Surgery",
            arrival_rate=2.5,  # 2.5 cases/hour
            service_time_minutes=30,  # 30 min per case
            target_wait_minutes=15,
            target_wait_probability=0.05
        )
        print(f"Need {result.recommended_specialists} specialists")
        print(f"Wait probability: {result.wait_probability:.1%}")
        print(f"Service level: {result.service_level:.1%}")
    """
    return await optimize_erlang_coverage(
        specialty=specialty,
        arrival_rate=arrival_rate,
        service_time_minutes=service_time_minutes,
        target_wait_minutes=target_wait_minutes,
        target_wait_probability=target_wait_probability,
        max_servers=max_servers,
    )


@armory_tool("calculate_erlang_metrics_tool")
async def calculate_erlang_metrics_tool(
    arrival_rate: float,
    service_time_minutes: float,
    servers: int,
    target_wait_minutes: float = 15.0,
) -> ErlangMetricsResponse:
    """
    Calculate detailed Erlang C metrics for a specific staffing configuration.

    Use this tool to evaluate a specific staffing scenario or compare different
    configurations. For optimization (finding minimum staff), use
    optimize_erlang_coverage_tool instead.

    The Erlang C formula calculates:
    - Wait probability: Chance a request enters the queue
    - Average wait time: Expected delay for requests that must wait
    - Service level: Percentage served within target time
    - Occupancy: Average utilization of specialists

    Args:
        arrival_rate: Average requests per hour
        service_time_minutes: Average time per case in minutes
        servers: Number of specialists to evaluate
        target_wait_minutes: Target wait time for service level

    Returns:
        Detailed queuing metrics for the configuration

    Example:
        # Check metrics for 5 orthopedic surgeons
        metrics = await calculate_erlang_metrics_tool(
            arrival_rate=2.5,
            service_time_minutes=30,
            servers=5,
            target_wait_minutes=15
        )
        print(f"Wait probability: {metrics.wait_probability:.1%}")
        print(f"Occupancy: {metrics.occupancy:.1%}")
    """
    return await calculate_erlang_metrics(
        arrival_rate=arrival_rate,
        service_time_minutes=service_time_minutes,
        servers=servers,
        target_wait_minutes=target_wait_minutes,
    )


@armory_tool("calculate_process_capability_tool")
async def calculate_process_capability_tool(
    data: list[float],
    lower_spec_limit: float,
    upper_spec_limit: float,
    target: float | None = None,
) -> ProcessCapabilityResponse:
    """
    Calculate Six Sigma process capability indices for schedule quality.

    Applies Six Sigma statistical process control to measure how consistently
    the scheduling process maintains ACGME compliance and operational constraints.
    This is the same methodology used in manufacturing for quality control.

    Process Capability Indices:
    - Cp: Process potential (spread relative to spec width, assumes centered)
    - Cpk: Process capability (accounts for off-center mean) - PRIMARY METRIC
    - Cpm: Taguchi capability (penalizes deviation from target)

    Capability Classification:
    - Cpk >= 2.0: EXCELLENT (World Class, 6-sigma quality, 3.4 DPMO)
    - Cpk >= 1.67: EXCELLENT (5-sigma quality, 233 DPMO)
    - Cpk >= 1.33: CAPABLE (4-sigma, industry standard, 6,210 DPMO)
    - Cpk >= 1.0: MARGINAL (3-sigma, minimum acceptable, 66,807 DPMO)
    - Cpk < 1.0: INCAPABLE (defects expected)

    Common Applications:
    - Weekly work hours: LSL=40, USL=80 (ACGME), Target=60
    - Coverage rates: LSL=0.95, USL=1.0, Target=1.0
    - Utilization: LSL=0.0, USL=0.8, Target=0.65

    Args:
        data: Sample measurements (e.g., weekly hours for each resident)
        lower_spec_limit: LSL - minimum acceptable value
        upper_spec_limit: USL - maximum acceptable value
        target: Ideal target value (defaults to midpoint)

    Returns:
        Capability indices with recommendations

    Example:
        # Analyze weekly work hours for ACGME compliance
        weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, 55, 71]
        result = await calculate_process_capability_tool(
            data=weekly_hours,
            lower_spec_limit=40,
            upper_spec_limit=80,
            target=60
        )
        print(f"Capability: {result.capability_status}")
        print(f"Sigma Level: {result.sigma_level:.2f}")
        print(f"Defect Rate: {result.estimated_defect_rate_ppm:.1f} PPM")
    """
    return await calculate_process_capability(
        data=data,
        lower_spec_limit=lower_spec_limit,
        upper_spec_limit=upper_spec_limit,
        target=target,
    )


@armory_tool("calculate_equity_metrics_tool")
async def calculate_equity_metrics_tool(
    provider_hours: dict[str, float],
    intensity_weights: dict[str, float] | None = None,
) -> EquityMetricsResponse:
    """
    Calculate workload equity metrics using Gini coefficient and fairness analysis.

    The Gini coefficient quantifies inequality in a distribution, ranging from
    0 (perfect equality, everyone has same workload) to 1 (perfect inequality,
    one person has all the work). For medical scheduling, a Gini coefficient
    below 0.15 indicates equitable workload distribution.

    Intensity weights allow accounting for shift difficulty:
    - Night shifts might have weight 1.5
    - Weekend shifts might have weight 1.3
    - High-acuity rotations might have weight 1.2

    Use this tool to:
    - Detect workload imbalances before burnout occurs
    - Identify overloaded and underloaded providers
    - Generate rebalancing recommendations
    - Track equity trends over time

    Args:
        provider_hours: Mapping of provider ID to total hours worked
        intensity_weights: Optional intensity multiplier per provider

    Returns:
        Gini coefficient, statistics, and rebalancing recommendations

    Example:
        # Analyze faculty workload equity
        hours = {
            "FAC-001": 45,
            "FAC-002": 52,
            "FAC-003": 38,
            "FAC-004": 60,
            "FAC-005": 42
        }
        result = await calculate_equity_metrics_tool(hours)
        print(f"Gini: {result.gini_coefficient:.3f}")
        print(f"Equitable: {result.is_equitable}")
        print(f"Most overloaded: {result.most_overloaded_provider}")
        for rec in result.recommendations:
            print(f"  - {rec}")
    """
    return await calculate_equity_metrics(
        provider_hours=provider_hours,
        intensity_weights=intensity_weights,
    )


@armory_tool("generate_lorenz_curve_tool")
async def generate_lorenz_curve_tool(
    values: list[float],
) -> LorenzCurveResponse:
    """
    Generate Lorenz curve data for visualizing workload inequality.

    The Lorenz curve plots cumulative share of population (x-axis) against
    cumulative share of total value (y-axis). Perfect equality is the 45-degree
    diagonal line. The Gini coefficient equals twice the area between the
    Lorenz curve and the equality line.

    Use this data to create visualizations in dashboards showing:
    - How workload is distributed across providers
    - Distance from ideal (perfect equality line)
    - Progress toward equity goals over time

    Args:
        values: List of numeric values (e.g., hours worked by each provider)

    Returns:
        Lorenz curve coordinates and Gini coefficient

    Example:
        # Generate Lorenz curve for faculty hours
        hours = [45, 52, 38, 60, 42, 55, 48]
        curve = await generate_lorenz_curve_tool(hours)
        print(f"Gini coefficient: {curve.gini_coefficient:.3f}")

        # Data ready for plotting:
        # x-axis: curve.population_shares
        # y-axis: curve.value_shares
        # reference: curve.equality_line (45-degree line)
    """
    return await generate_lorenz_curve(values=values)


# =============================================================================
# Artificial Immune System Tools (AIS - Immunology-Inspired Resilience)
# =============================================================================


@armory_tool("assess_immune_response_tool")
async def assess_immune_response_tool(
    include_detectors: bool = True,
    include_recent_anomalies: bool = True,
    include_antibodies: bool = True,
    max_items: int = 10,
) -> ImmuneResponseAssessmentResponse:
    """
    Assess the current status of the artificial immune system.

    Provides a comprehensive view of the immune system's adaptive response
    capabilities for detecting and repairing schedule anomalies.

    Key Concepts (Immunology-Inspired):
    - Detectors: Hyperspheres in feature space that trigger on anomalous states
    - Antibodies: Repair strategies with affinity for specific anomaly patterns
    - Memory Cells: Learned patterns enabling faster future responses

    The system uses Negative Selection Algorithm (NSA) to distinguish between
    "self" (valid schedules) and "non-self" (anomalous states).

    Components Analyzed:
    - Training Status: Whether the system has learned valid schedule patterns
    - Detector Coverage: Active detectors and their anomaly detection counts
    - Anomaly History: Recently detected schedule anomalies
    - Antibody Arsenal: Available repair strategies and success rates

    Args:
        include_detectors: Include details of most active detectors
        include_recent_anomalies: Include recently detected anomalies
        include_antibodies: Include registered antibody information
        max_items: Maximum items per category (1-50)

    Returns:
        Comprehensive immune system status with health assessment

    Example:
        result = await assess_immune_response_tool()
        if result.response_status.is_trained:
            print(f"Detectors: {result.response_status.detector_count}")
            print(f"Success rate: {result.response_status.repair_success_rate:.1%}")
            print(f"Health: {result.overall_health}")
        else:
            print("WARNING: Immune system needs training on valid schedules")
    """
    return await assess_immune_response(
        include_detectors=include_detectors,
        include_recent_anomalies=include_recent_anomalies,
        include_antibodies=include_antibodies,
        max_items=max_items,
    )


@armory_tool("check_memory_cells_tool")
async def check_memory_cells_tool(
    include_inactive: bool = False,
    max_patterns: int = 20,
) -> MemoryCellsResponse:
    """
    Check immune system memory cells (learned patterns from past stressors).

    Memory cells represent learned patterns from past anomalies, enabling faster
    and more effective responses to recurring issues. Like biological immune
    memory (T and B cells), the system remembers:

    What Memory Cells Track:
    - Pattern signatures: Feature vectors characterizing specific anomalies
    - Effective responses: Which antibodies worked best for each pattern
    - Occurrence frequency: How often each pattern has been seen
    - Response optimization: Faster detection for known patterns

    Benefits of Immune Memory:
    1. Known patterns trigger immediate recognition (no search needed)
    2. Effective antibodies are pre-selected based on history
    3. Repair strategies are optimized from past experience

    Pattern Types:
    - coverage_gap: Coverage fell below threshold
    - acgme_violation: Work hour or rest period violations
    - workload_imbalance: Unfair distribution of assignments
    - schedule_instability: Excessive changes or churn

    Args:
        include_inactive: Include patterns not seen recently (last 30 days)
        max_patterns: Maximum number of patterns to return (1-100)

    Returns:
        Memory cell status with learned patterns and response improvements

    Example:
        result = await check_memory_cells_tool()
        print(f"Memory cells: {result.total_memory_cells}")
        print(f"Response improvement: {result.average_response_improvement:.1%}")

        # Find most common anomaly types
        for pattern_type, count in result.pattern_distribution.items():
            print(f"  {pattern_type}: {count} occurrences")
    """
    return await check_memory_cells(
        include_inactive=include_inactive,
        max_patterns=max_patterns,
    )


@armory_tool("analyze_antibody_response_tool")
async def analyze_antibody_response_tool(
    schedule_state: dict[str, Any] | None = None,
    include_all: bool = True,
) -> AntibodyAnalysisResponse:
    """
    Analyze antibody (repair strategy) response capabilities.

    Antibodies are repair strategies that fix specific types of anomalies.
    Each antibody has an affinity pattern - it works best for anomalies
    with similar feature vectors. Uses Clonal Selection algorithm.

    Clonal Selection Process:
    1. Calculate affinity of each antibody to the anomaly
    2. Select antibody with highest affinity
    3. Boost selection by historical success rate
    4. Apply repair and track results

    Available Antibodies:
    - coverage_gap_repair: Finds available faculty to fill gaps
    - workload_balance_repair: Redistributes assignments for fairness
    - acgme_violation_repair: Adjusts hours/rest periods for compliance

    Affinity Calculation:
    - Based on distance in feature space
    - Closer to antibody's affinity center = higher affinity
    - Range: 0.0 (no match) to 1.0 (perfect match)

    Args:
        schedule_state: Optional current schedule state to calculate affinities.
            If provided, finds best matching antibody for this state.
            Expected keys: total_blocks, covered_blocks, faculty_count,
            resident_count, acgme_violations, avg_hours_per_week,
            supervision_ratio, workload_std_dev, schedule_changes
        include_all: Include all antibodies even if affinity is zero

    Returns:
        Antibody analysis with active countermeasures and best match

    Example:
        # Find best repair for current schedule
        schedule = {
            "total_blocks": 100,
            "covered_blocks": 75,  # Low coverage
            "faculty_count": 10,
            "resident_count": 25,
            "acgme_violations": [{"type": "80hr", "severity": "CRITICAL"}],
            "avg_hours_per_week": 85,
            "workload_std_dev": 0.4,
        }
        result = await analyze_antibody_response_tool(schedule_state=schedule)

        if result.best_match_antibody:
            print(f"Recommended repair: {result.best_match_antibody}")
        print(f"Repair capacity: {result.repair_capacity:.1%}")
        print(f"Historical effectiveness: {result.historical_effectiveness:.1%}")
    """
    return await analyze_antibody_response(
        schedule_state=schedule_state,
        include_all=include_all,
    )




# =============================================================================
# Thermodynamics Tools (Entropy, Phase Transitions, Free Energy)
# =============================================================================


@armory_tool("calculate_schedule_entropy_tool")
async def calculate_schedule_entropy_tool(
    start_date: str | None = None,
    end_date: str | None = None,
    include_mutual_information: bool = True,
) -> ScheduleEntropyResponse:
    """
    Calculate comprehensive entropy metrics for the schedule.

    Entropy measures the disorder/randomness in schedule assignment distribution.
    This tool applies Shannon entropy analysis across multiple dimensions.

    **Entropy Dimensions Analyzed:**
    - Person Entropy: Distribution of assignments across faculty
      - Low: Few faculty handle most work (concentrated risk)
      - High: Work evenly distributed (resilient but may be chaotic)

    - Rotation Entropy: Distribution across rotation types
    - Time Entropy: Distribution across time blocks
    - Joint Entropy: Combined person-rotation distribution
    - Mutual Information: How much knowing the person tells about the rotation

    **Optimal Entropy:**
    Moderate entropy is ideal - not too concentrated (vulnerable) nor too
    dispersed (potentially chaotic). The normalized_entropy metric (0-1)
    helps identify this balance.

    **Early Warning Application:**
    Changes in entropy over time can signal approaching phase transitions.
    Decreasing entropy may indicate system "crystallizing" into rigid patterns.

    Args:
        start_date: Start date for analysis (YYYY-MM-DD), defaults to today
        end_date: End date for analysis (YYYY-MM-DD), defaults to 30 days
        include_mutual_information: Calculate mutual information between dimensions

    Returns:
        ScheduleEntropyResponse with entropy metrics and interpretation

    Example:
        result = await calculate_schedule_entropy_tool(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        if result.entropy_status == "too_concentrated":
            print("WARNING: Schedule has concentrated risk")
            print(f"Person entropy: {result.metrics.person_entropy:.2f} bits")
    """
    return await calculate_schedule_entropy(
        start_date=start_date,
        end_date=end_date,
        include_mutual_information=include_mutual_information,
    )


@armory_tool("get_entropy_monitor_state_tool")
async def get_entropy_monitor_state_tool(
    history_window: int = 100,
) -> EntropyMonitorStateResponse:
    """
    Get current state of the entropy monitor for early warning detection.

    The entropy monitor tracks entropy dynamics over time to detect:
    - Critical slowing down (entropy changes slow near phase transitions)
    - Rapid entropy changes (system instability)
    - Entropy production rate (energy dissipation)

    **Critical Slowing Down:**
    Near phase transitions, systems exhibit "critical slowing down" - recovery
    from perturbations takes longer. This manifests as:
    - High autocorrelation (system "remembers" longer)
    - Low rate of change (entropy stabilizes at a new level)

    Detecting critical slowing down provides early warning of approaching
    phase transitions (system failures).

    Args:
        history_window: Number of entropy measurements to analyze (10-1000)

    Returns:
        EntropyMonitorStateResponse with current monitor state

    Example:
        result = await get_entropy_monitor_state_tool()
        if result.critical_slowing_detected:
            print("WARNING: Critical slowing detected - approaching phase transition")
            print(f"Rate of change: {result.rate_of_change:.4f}")
    """
    return await get_entropy_monitor_state(history_window=history_window)


@armory_tool("analyze_phase_transitions_tool")
async def analyze_phase_transitions_tool(
    metrics: dict[str, list[float]] | None = None,
    window_size: int = 50,
) -> PhaseTransitionRiskResponse:
    """
    Detect approaching phase transitions using critical phenomena theory.

    Applies physics-based early warning signal detection to identify when
    the scheduling system is approaching a phase transition (failure).

    **Universal Early Warning Signals (from physics):**

    1. **Increasing Variance** - Fluctuations diverge before transitions
       - Metric variance increases by >50% from baseline

    2. **Critical Slowing Down** - Response time increases near critical point
       - Autocorrelation at lag-1 exceeds 0.7

    3. **Flickering** - Rapid state switching near bistable points
       - System alternates between states

    4. **Skewness Changes** - Distribution becomes asymmetric
       - Skewness exceeds +/- 1.0

    **Phase Transition Types:**
    - Stable Schedule -> Chaotic Schedule (order-disorder)
    - Resilient -> Fragile (resilience collapse)
    - Normal -> Crisis (operational phase change)

    **2025 Research Basis:**
    Thermodynamic approaches using time-reversal symmetry breaking detect
    transitions 2-3x earlier than traditional bifurcation methods.

    Args:
        metrics: Dictionary of metric_name -> time series values
                 (if None, uses recent system metrics)
        window_size: Analysis window size for signal detection (10-200)

    Returns:
        PhaseTransitionRiskResponse with detected signals and recommendations

    Example:
        result = await analyze_phase_transitions_tool(
            metrics={
                "utilization": [0.75, 0.78, 0.82, 0.85, 0.88, ...],
                "coverage": [0.95, 0.93, 0.91, 0.89, 0.86, ...],
                "violations": [0, 1, 1, 2, 3, 4, ...]
            }
        )

        if result.overall_severity == "critical":
            print(f"ALERT: Phase transition approaching")
    """
    return await analyze_phase_transitions(
        metrics=metrics,
        window_size=window_size,
    )


@armory_tool("optimize_free_energy_tool")
async def optimize_free_energy_tool(
    schedule_id: str | None = None,
    target_temperature: float = 1.0,
    max_iterations: int = 100,
) -> FreeEnergyOptimizationResponse:
    """
    Optimize schedule using free energy minimization.

    **NOTE: This module is planned but not yet implemented.**

    **Concept (Future Implementation):**
    Free energy minimization applies thermodynamic principles to find optimal
    schedule configurations by balancing:
    - Internal Energy (U): Constraint violations and cost
    - Entropy (S): Schedule flexibility and diversity
    - Temperature (T): Control parameter for exploration vs exploitation

    Helmholtz Free Energy: F = U - TS
    Lower free energy = more stable configuration.

    **Planned Features:**
    - Identify metastable schedules (shallow energy wells)
    - Find escape paths from local minima
    - Adaptive temperature for crisis flexibility
    - Pre-compute alternative schedules

    Args:
        schedule_id: Schedule to optimize (or use current)
        target_temperature: Temperature parameter (higher = more exploration)
        max_iterations: Maximum optimization iterations

    Returns:
        FreeEnergyOptimizationResponse (placeholder until implemented)

    Example:
        result = await optimize_free_energy_tool()
        if result.improvement > 0:
            print(f"Free energy reduced by {result.improvement:.2f}")
    """
    return await optimize_free_energy(
        schedule_id=schedule_id,
        target_temperature=target_temperature,
        max_iterations=max_iterations,
    )


@armory_tool("calculate_time_crystal_objective_tool")
async def calculate_time_crystal_objective_tool(
    current_assignments: list[dict],
    proposed_assignments: list[dict],
    constraint_results: list[dict] | None = None,
    alpha: float = 0.3,
    beta: float = 0.1,
) -> TimeCrystalObjectiveResponse:
    """
    Calculate time-crystal-inspired optimization objective.

    Combines constraint satisfaction with anti-churn (rigidity) to create
    schedules that are BOTH compliant AND stable. Based on time crystal
    physics and minimal disruption planning research.

    Objective Function:
        score = (1-α-β) * constraints + α * rigidity + β * fairness

    Weight Guidelines:
        - α = 0.0: Pure constraint optimization (may cause large reshuffles)
        - α = 0.3: Balanced - satisfy constraints with minimal disruption
        - α = 0.5: Conservative - prefer stability over minor improvements
        - α = 1.0: Pure stability (no changes even if suboptimal)

    Args:
        current_assignments: Current schedule assignments
        proposed_assignments: Proposed schedule assignments
        constraint_results: Optional constraint evaluation results
            (list of {satisfied: bool, penalty: float})
        alpha: Weight for rigidity (0.0-1.0, default 0.3)
        beta: Weight for fairness (0.0-1.0, default 0.1)

    Returns:
        Combined objective score with component breakdown:
        - objective_score: Final score (higher is better)
        - constraint_score: Constraint satisfaction component
        - rigidity_score: Schedule stability component
        - fairness_score: Churn distribution fairness
        - interpretation: Human-readable assessment

    Example:
        result = await calculate_time_crystal_objective_tool(
            current_assignments=[...],
            proposed_assignments=[...],
            alpha=0.3,  # 30% weight on stability
            beta=0.1    # 10% weight on fair churn distribution
        )

        print(f"Score: {result.objective_score}")
        print(f"Interpretation: {result.interpretation}")
    """
    return await calculate_time_crystal_objective(
        current_assignments=current_assignments,
        proposed_assignments=proposed_assignments,
        constraint_results=constraint_results,
        alpha=alpha,
        beta=beta,
    )


@armory_tool("analyze_energy_landscape_tool")
async def analyze_energy_landscape_tool(
    schedule_id: str | None = None,
) -> EnergyLandscapeResponse:
    """
    Analyze the energy landscape around current schedule.

    **NOTE: This module is planned but not yet implemented.**

    **Concept (Future Implementation):**
    Energy landscape analysis maps the stability of the current schedule
    and nearby alternatives:

    - Deep well = Very stable schedule (hard to escape, may miss better options)
    - Shallow well = Metastable schedule (easy to disrupt)
    - Saddle point = Transition state (pathway between configurations)

    **Planned Analysis:**
    - Escape barrier height (how much perturbation to move)
    - Nearby local minima (alternative schedules)
    - Pathway analysis (how to reach better configurations)

    Args:
        schedule_id: Schedule to analyze (or use current)

    Returns:
        EnergyLandscapeResponse with stability analysis (placeholder)
    """
    return await analyze_energy_landscape(schedule_id=schedule_id)




# =============================================================================
# Hopfield Network Attractor Tools (Energy Landscape & Schedule Stability)
# =============================================================================


@armory_tool("calculate_hopfield_energy_tool")
async def calculate_hopfield_energy_tool(
    start_date: str | None = None,
    end_date: str | None = None,
    schedule_id: str | None = None,
) -> HopfieldEnergyResponse:
    """
    Calculate Hopfield energy of the current schedule state.

    **Hopfield Energy Function:**
    E = -0.5 * sum_ij(w_ij * s_i * s_j)

    Where:
    - s_i, s_j are binary state variables (assignment present/absent)
    - w_ij are learned weights encoding stable scheduling patterns
    - Lower energy = more stable configuration

    **Energy Interpretation:**
    - Negative Energy: Schedule matches learned stable patterns
    - Energy Near Zero: Schedule is in transition between patterns
    - Positive Energy: Schedule conflicts with learned patterns (unstable)

    **Neuroscience Analogy:**
    Like how neurons settle into stable firing patterns representing memories,
    schedules settle into stable assignment patterns that respect constraints
    and historical preferences.

    **Complementary to Thermodynamics:**
    While thermodynamic entropy measures disorder, Hopfield energy measures
    how well the schedule matches learned stable patterns. Use both together:
    - High entropy + Low energy: Diverse but stable (good)
    - Low entropy + Low energy: Concentrated but stable (risky)
    - High entropy + High energy: Chaotic and unstable (bad)

    Args:
        start_date: Start date for analysis (YYYY-MM-DD), defaults to today
        end_date: End date for analysis (YYYY-MM-DD), defaults to 30 days
        schedule_id: Optional specific schedule ID to analyze

    Returns:
        HopfieldEnergyResponse with energy metrics and stability assessment

    Example:
        result = await calculate_hopfield_energy_tool(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        if result.stability_level == "unstable":
            print(f"WARNING: Schedule is unstable (energy={result.metrics.total_energy:.2f})")
            print(f"Distance to stability: {result.metrics.distance_to_minimum} changes")
    """
    return await calculate_hopfield_energy(
        start_date=start_date,
        end_date=end_date,
        schedule_id=schedule_id,
    )


@armory_tool("find_nearby_attractors_tool")
async def find_nearby_attractors_tool(
    max_distance: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
) -> NearbyAttractorsResponse:
    """
    Identify stable attractors near the current schedule state.

    **Attractor Concept:**
    In Hopfield networks, attractors are stable states (energy minima) that
    the system naturally evolves toward. Initial states within the "basin of
    attraction" converge to the same attractor through energy minimization.

    **Schedule Interpretation:**
    - Each attractor represents a stable scheduling pattern
    - Current schedule may be near (but not at) an attractor
    - Multiple attractors = multiple valid scheduling strategies
    - Finding nearby attractors shows alternative stable configurations

    **Use Cases:**
    1. Schedule Optimization: Find global minimum for best configuration
    2. Alternative Schedules: Discover different stable patterns
    3. Robustness Assessment: Check if current state is in deep basin
    4. Constraint Debugging: Identify why schedule won't improve

    **Search Strategy:**
    Uses gradient descent and random perturbations to map the energy landscape
    within max_distance Hamming distance from current state.

    Args:
        max_distance: Maximum Hamming distance to search (1-50)
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)

    Returns:
        NearbyAttractorsResponse with identified attractors and recommendations

    Example:
        result = await find_nearby_attractors_tool(max_distance=5)

        for attractor in result.attractors:
            if attractor.attractor_type == "global_minimum":
                print(f"Global optimum found at distance {attractor.hamming_distance}")
                print(f"Energy improvement: {result.current_state_energy - attractor.energy_level:.2f}")

        if result.global_minimum_identified:
            print("Optimization path available to global optimum")
    """
    return await find_nearby_attractors(
        max_distance=max_distance,
        start_date=start_date,
        end_date=end_date,
    )


@armory_tool("measure_basin_depth_tool")
async def measure_basin_depth_tool(
    attractor_id: str | None = None,
    num_perturbations: int = 100,
) -> BasinDepthResponse:
    """
    Measure the depth of the basin of attraction for current or specified attractor.

    **Basin Depth Concept:**
    Basin depth is the energy barrier that must be overcome to escape the basin.
    Deeper basins = more stable attractors = more robust schedules.

    **Why Basin Depth Matters for Scheduling:**
    - Deep Basin: Schedule is robust to random perturbations (swaps, absences)
    - Shallow Basin: Small changes can push schedule into different attractor
    - Critical for resilience: N-1/N-2 failures shouldn't escape basin

    **Practical Applications:**
    1. Swap Approval: Ensure swaps don't push schedule out of basin
    2. N-1 Testing: Verify schedule remains stable after single faculty removal
    3. Flexibility Assessment: How many simultaneous changes are safe
    4. Schedule Comparison: Compare robustness of different schedules

    **Measurement Method:**
    Applies random perturbations and measures minimum energy barrier to:
    1. Escape current basin
    2. Reach a different attractor
    3. Cross saddle points in the energy landscape

    **Integration with Resilience Framework:**
    Basin depth complements other resilience metrics:
    - N-1/N-2 Contingency: Basin should survive N-1 perturbations
    - Defense in Depth: Basin depth maps to resilience tier
    - Recovery Distance: Basin escape distance ≈ recovery distance

    Args:
        attractor_id: Specific attractor to analyze (defaults to nearest)
        num_perturbations: Number of random perturbations to test (10-1000)

    Returns:
        BasinDepthResponse with stability metrics and robustness assessment

    Example:
        result = await measure_basin_depth_tool(num_perturbations=200)

        if result.metrics.basin_stability_index > 0.8:
            print(f"Schedule is highly stable (index={result.metrics.basin_stability_index:.2f})")
            print(f"Can tolerate {result.robustness_threshold} simultaneous changes")
        else:
            print("WARNING: Schedule is fragile")
            print(f"Minimum escape barrier: {result.metrics.min_escape_energy:.2f}")
    """
    return await measure_basin_depth(
        attractor_id=attractor_id,
        num_perturbations=num_perturbations,
    )


@armory_tool("detect_spurious_attractors_tool")
async def detect_spurious_attractors_tool(
    search_radius: int = 20,
    min_basin_size: int = 10,
) -> SpuriousAttractorsResponse:
    """
    Detect spurious attractors (unintended stable patterns / scheduling anti-patterns).

    **Spurious Attractor Problem:**
    Hopfield networks can form "spurious attractors" - stable states that were
    NOT part of the training patterns. In scheduling context, these are anti-patterns:
    - Concentrated overload on subset of faculty
    - Systematic underutilization
    - Clustering violations (too many similar shifts together)
    - ACGME compliance boundary cases

    **Why This Matters:**
    If schedule generation randomly initializes near a spurious attractor, it may
    converge to an anti-pattern that satisfies hard constraints but violates
    implicit quality requirements.

    **Common Scheduling Anti-Patterns:**
    1. **Overload Concentration**: 80% of call shifts on 3 senior faculty
    2. **Shift Clustering**: Same person assigned consecutive night shifts
    3. **Underutilization**: Junior faculty assigned minimal rotations
    4. **Boundary Gaming**: Schedule exactly at ACGME limits (not margin)
    5. **Rotation Monotony**: Same person always assigned to same rotation type

    **Detection Strategy:**
    1. Search energy landscape for local minima
    2. Check if each minimum corresponds to known good pattern
    3. Classify unknown minima as spurious
    4. Estimate basin size and capture probability

    **Mitigation Strategies:**
    - Add soft constraints to penalize anti-patterns
    - Initialize schedule generation away from spurious basins
    - Use basin escape techniques to leave spurious attractors
    - Adjust weight matrix to eliminate spurious attractors

    Args:
        search_radius: Hamming distance to search for spurious attractors (5-50)
        min_basin_size: Minimum basin size to report (avoid noise)

    Returns:
        SpuriousAttractorsResponse with anti-patterns and mitigation strategies

    Example:
        result = await detect_spurious_attractors_tool(search_radius=25)

        if result.is_current_state_spurious:
            print("ALERT: Current schedule is in a spurious attractor (anti-pattern)!")
            highest_risk = result.highest_risk_attractor
            print(f"Risk attractor: {highest_risk}")

        for spurious in result.spurious_attractors:
            if spurious.risk_level == "critical":
                print(f"Critical anti-pattern: {spurious.description}")
                print(f"Mitigation: {spurious.mitigation_strategy}")

        if result.total_basin_coverage > 0.2:
            print(f"WARNING: {result.total_basin_coverage:.0%} of state space is spurious!")
    """
    return await detect_spurious_attractors(
        search_radius=search_radius,
        min_basin_size=min_basin_size,
    )





# =============================================================================
# Early Warning System Tools (Cross-Disciplinary Burnout Detection)
# =============================================================================


@armory_tool("detect_burnout_precursors_tool")
async def detect_burnout_precursors_tool(
    resident_id: str,
    signal_type: str,
    time_series: list[float],
    short_window: int = 5,
    long_window: int = 30,
) -> PrecursorDetectionResponse:
    """
    Detect early warning signs of burnout using seismic STA/LTA algorithm.

    Applies seismological precursor detection to workload patterns,
    identifying P-wave equivalents that precede burnout events.

    Args:
        resident_id: UUID of resident to analyze
        signal_type: Signal type to detect
        time_series: Chronological time series data
        short_window: STA window size (default 5)
        long_window: LTA window size (default 30)

    Returns:
        Detection results with alerts and recommendations
    """
    try:
        signal_enum = PrecursorSignalType(signal_type)
    except ValueError as e:
        raise ValueError(
            f"Invalid signal_type: {signal_type}. "
            f"Must be one of: {[s.value for s in PrecursorSignalType]}"
        ) from e

    request = PrecursorDetectionRequest(
        resident_id=resident_id,
        signal_type=signal_enum,
        time_series=time_series,
        short_window=short_window,
        long_window=long_window,
    )
    return await detect_burnout_precursors(request)


@armory_tool("predict_burnout_magnitude_tool")
async def predict_burnout_magnitude_tool(
    resident_id: str,
    signals: dict[str, list[float]],
    short_window: int = 5,
    long_window: int = 30,
) -> MultiSignalMagnitudeResponse:
    """
    Predict burnout magnitude from multiple precursor signals.

    Combines evidence from multiple signal types to estimate severity
    on a 1-10 scale (similar to Richter scale).

    Args:
        resident_id: UUID of resident to analyze
        signals: Dict mapping signal_type to time series data
        short_window: STA window size (default 5)
        long_window: LTA window size (default 30)

    Returns:
        Predicted magnitude (1-10) with confidence and recommendations
    """
    request = MultiSignalMagnitudeRequest(
        resident_id=resident_id,
        signals=signals,
        short_window=short_window,
        long_window=long_window,
    )
    return await predict_burnout_magnitude(request)


@armory_tool("run_spc_analysis_tool")
async def run_spc_analysis_tool(
    resident_id: str,
    weekly_hours: list[float],
    target_hours: float = 60.0,
    sigma: float = 5.0,
) -> SPCAnalysisResponse:
    """
    Run Statistical Process Control analysis using Western Electric Rules.

    Applies manufacturing quality control methodology to workload monitoring.

    Args:
        resident_id: UUID of resident to analyze
        weekly_hours: Weekly work hours in chronological order
        target_hours: Target weekly hours (default 60)
        sigma: Process standard deviation (default 5)

    Returns:
        SPC analysis with violations and control chart data
    """
    request = SPCAnalysisRequest(
        resident_id=resident_id,
        weekly_hours=weekly_hours,
        target_hours=target_hours,
        sigma=sigma,
    )
    return await run_spc_analysis(request)


@armory_tool("calculate_workload_process_capability_tool")
async def calculate_workload_process_capability_tool(
    weekly_hours: list[float],
    lower_spec_limit: float = 40.0,
    upper_spec_limit: float = 80.0,
) -> EWProcessCapabilityResponse:
    """
    Calculate process capability indices (Cp/Cpk) for workload distribution.

    Six Sigma quality metric adapted for medical scheduling.

    Args:
        weekly_hours: Weekly work hours data (minimum 2 weeks)
        lower_spec_limit: Minimum hours (default 40)
        upper_spec_limit: Maximum hours/ACGME limit (default 80)

    Returns:
        Process capability indices with interpretation
    """
    request = ProcessCapabilityRequest(
        weekly_hours=weekly_hours,
        lower_spec_limit=lower_spec_limit,
        upper_spec_limit=upper_spec_limit,
    )
    return await calculate_spc_process_capability(request)


@armory_tool("calculate_fire_danger_index_tool")
async def calculate_fire_danger_index_tool(
    resident_id: str,
    recent_hours: float,
    monthly_load: float,
    yearly_satisfaction: float,
    workload_velocity: float = 0.0,
) -> FireDangerResponse:
    """
    Calculate multi-temporal burnout danger using Fire Weather Index system.

    Adapts Canadian Forest Fire Danger Rating System (CFFDRS) for burnout.

    Args:
        resident_id: UUID of resident to assess
        recent_hours: Hours worked in last 2 weeks
        monthly_load: Average monthly hours over last 3 months
        yearly_satisfaction: Job satisfaction (0.0-1.0)
        workload_velocity: Rate of workload increase (hours/week)

    Returns:
        Fire danger assessment with restrictions
    """
    request = FireDangerRequest(
        resident_id=resident_id,
        recent_hours=recent_hours,
        monthly_load=monthly_load,
        yearly_satisfaction=yearly_satisfaction,
        workload_velocity=workload_velocity,
    )
    return await calculate_fire_danger_index(request)


@armory_tool("calculate_batch_fire_danger_tool")
async def calculate_batch_fire_danger_tool(
    residents: list[dict[str, Any]],
) -> BatchFireDangerResponse:
    """
    Calculate fire danger index for multiple residents.

    Useful for program-wide burnout screening.

    Args:
        residents: List of dicts with keys:
            resident_id, recent_hours, monthly_load,
            yearly_satisfaction, workload_velocity (optional)

    Returns:
        Program-wide statistics and highest-risk residents
    """
    requests = []
    for r in residents:
        requests.append(
            FireDangerRequest(
                resident_id=r["resident_id"],
                recent_hours=r["recent_hours"],
                monthly_load=r["monthly_load"],
                yearly_satisfaction=r["yearly_satisfaction"],
                workload_velocity=r.get("workload_velocity", 0.0),
            )
        )
    batch_request = BatchFireDangerRequest(residents=requests)
    return await calculate_batch_fire_danger(batch_request)



# =============================================================================
# FRMS (Fatigue Risk Management System) Tools
# =============================================================================


@mcp.tool()
async def run_frms_assessment_tool(
    resident_id: str,
    target_time: str | None = None,
) -> FRMSAssessmentResponse:
    """
    Run comprehensive FRMS assessment for a resident.

    Generates a complete fatigue profile aggregating all FRMS metrics
    including Samn-Perelli level, sleep debt, alertness prediction,
    hazard assessment, and ACGME compliance status.

    Implements aviation FRMS standards (FAA AC 120-103A, ICAO Doc 9966)
    adapted for medical residency scheduling.

    Args:
        resident_id: UUID of the resident to assess.
        target_time: Optional target time for assessment (ISO format).
                    Defaults to current time if not specified.

    Returns:
        FRMSAssessmentResponse with comprehensive fatigue profile.

    Example:
        result = await run_frms_assessment_tool(
            resident_id="550e8400-e29b-41d4-a716-446655440000"
        )

        if result.hazard.is_critical:
            print(f"CRITICAL: {result.hazard.required_mitigations}")
    """
    return await run_frms_assessment(
        resident_id=resident_id,
        target_time=target_time,
    )


@armory_tool("get_checkpoint_status_tool")
async def get_checkpoint_status_tool(
    schedule_id: str | None = None,
) -> CheckpointStatusResponse:
    """
    Get current stroboscopic checkpoint status.

    Time crystal insight: Like stroboscopic observation of time crystals,
    schedule state advances only at discrete checkpoints (week boundaries,
    block transitions) - not continuously. This ensures all observers see
    consistent state.

    Args:
        schedule_id: Optional specific schedule to check

    Returns:
        Checkpoint status with:
        - has_authoritative_state: Whether stable state exists
        - has_draft_state: Whether pending changes exist
        - last_checkpoint_time: When last checkpoint occurred
        - last_checkpoint_boundary: Type (WEEK_START, BLOCK_END, etc.)
        - pending_changes: Changes waiting for next checkpoint

    Example:
        status = await get_checkpoint_status_tool()

        if status.has_draft_state:
            print(f"{status.pending_changes} changes pending")
    """
    return await get_checkpoint_status(schedule_id=schedule_id)


@armory_tool("get_time_crystal_health_tool")
async def get_time_crystal_health_tool() -> TimeCrystalHealthResponse:
    """
    Get overall health of time crystal scheduling components.

    Monitors the three pillars of time-crystal-inspired scheduling:
    1. Periodicity: Are natural cycles being maintained?
    2. Rigidity: Is schedule appropriately stable?
    3. Checkpoints: Are stroboscopic checkpoints working?

    Returns:
        Health status with:
        - periodicity_healthy: Natural cycles intact
        - rigidity_healthy: Schedule stability acceptable
        - checkpoint_healthy: State management working
        - overall_health: healthy/degraded/critical
        - metrics: Key health indicators
        - issues: Detected problems
        - recommendations: Suggested fixes

    Example:
        health = await get_time_crystal_health_tool()

        if health.overall_health != "healthy":
            for issue in health.issues:
                print(f"Issue: {issue}")
            for rec in health.recommendations:
                print(f"Recommendation: {rec}")
    """
    return await get_time_crystal_health()


@armory_tool("get_fatigue_score_tool")
async def get_fatigue_score_tool(
    hours_awake: float,
    hours_worked_24h: float,
    consecutive_night_shifts: int = 0,
    time_of_day_hour: int = 12,
    prior_sleep_hours: float = 7.0,
) -> FatigueScoreResponse:
    """
    Calculate real-time fatigue score from objective factors.

    Uses the Samn-Perelli scale (1-7) adapted from USAF aviation
    with factors including hours awake, work intensity,
    circadian timing, and prior sleep.

    Args:
        hours_awake: Hours since last sleep period (0-48).
        hours_worked_24h: Work hours in last 24 hours (0-24).
        consecutive_night_shifts: Number of consecutive night shifts (0-7).
        time_of_day_hour: Current hour 0-23 (for circadian effects).
        prior_sleep_hours: Hours of sleep in prior sleep period (0-12).

    Returns:
        FatigueScoreResponse with fatigue level and safety assessment.

    Example:
        result = await get_fatigue_score_tool(
            hours_awake=18,
            hours_worked_24h=12,
            time_of_day_hour=4
        )

        if not result.is_safe_for_duty:
            print(f"Fatigue level {result.samn_perelli_level}")
    """
    return await get_fatigue_score(
        hours_awake=hours_awake,
        hours_worked_24h=hours_worked_24h,
        consecutive_night_shifts=consecutive_night_shifts,
        time_of_day_hour=time_of_day_hour,
        prior_sleep_hours=prior_sleep_hours,
    )


@armory_tool("analyze_sleep_debt_tool")
async def analyze_sleep_debt_tool(
    sleep_hours_per_day: list[float],
    baseline_sleep_need: float = 7.5,
) -> SleepDebtAnalysisResponse:
    """
    Analyze cumulative sleep debt with BAC equivalence mapping.

    Calculates accumulated sleep debt and cognitive impairment
    equivalence based on Van Dongen et al. (2003).

    Args:
        sleep_hours_per_day: List of sleep hours for each day.
        baseline_sleep_need: Individual's baseline sleep requirement.

    Returns:
        SleepDebtAnalysisResponse with debt analysis and recovery plan.

    Example:
        result = await analyze_sleep_debt_tool(
            sleep_hours_per_day=[6.0, 5.5, 7.0, 5.0, 6.5, 8.0, 6.0],
            baseline_sleep_need=7.5
        )

        print(f"Sleep debt: {result.current_debt_hours}h")
        print(f"BAC equivalent: {result.impairment_equivalent_bac:.3f}")
    """
    return await analyze_sleep_debt(
        sleep_hours_per_day=sleep_hours_per_day,
        baseline_sleep_need=baseline_sleep_need,
    )


@armory_tool("evaluate_fatigue_hazard_tool")
async def evaluate_fatigue_hazard_tool(
    alertness: float | None = None,
    sleep_debt: float | None = None,
    hours_awake: float | None = None,
    samn_perelli: int | None = None,
    consecutive_nights: int = 0,
    hours_worked_week: float = 0.0,
) -> FatigueHazardResponse:
    """
    Evaluate fatigue hazard level with mitigation requirements.

    Implements aviation FRMS 5-level hazard system:
    GREEN, YELLOW, ORANGE, RED, BLACK.

    Args:
        alertness: Current alertness score 0.0-1.0 (optional).
        sleep_debt: Current accumulated sleep debt in hours (optional).
        hours_awake: Hours since last sleep (optional).
        samn_perelli: Current Samn-Perelli level 1-7 (optional).
        consecutive_nights: Number of consecutive night shifts.
        hours_worked_week: Hours worked in current week.

    Returns:
        FatigueHazardResponse with hazard level and required mitigations.

    Example:
        result = await evaluate_fatigue_hazard_tool(
            alertness=0.4,
            sleep_debt=15.0,
            hours_awake=20
        )

        if result.is_critical:
            print(f"CRITICAL: {result.required_mitigations}")
    """
    return await evaluate_fatigue_hazard(
        alertness=alertness,
        sleep_debt=sleep_debt,
        hours_awake=hours_awake,
        samn_perelli=samn_perelli,
        consecutive_nights=consecutive_nights,
        hours_worked_week=hours_worked_week,
    )


@mcp.tool()
async def scan_team_fatigue_tool(
    hazard_threshold: str = "yellow",
) -> TeamFatigueScanResponse:
    """
    Scan all residents for fatigue risks.

    Returns fatigue profiles filtered to those at or above
    the specified hazard threshold.

    Args:
        hazard_threshold: Minimum hazard level to include.
                         Options: green, yellow, orange, red, black.

    Returns:
        TeamFatigueScanResponse with team fatigue summary.

    Example:
        result = await scan_team_fatigue_tool(hazard_threshold="orange")

        print(f"Critical: {result.residents_red + result.residents_black}")
    """
    return await scan_team_fatigue(hazard_threshold=hazard_threshold)


@mcp.tool()
async def assess_schedule_fatigue_risk_tool(
    resident_id: str,
    proposed_shifts: list[dict[str, Any]],
) -> ScheduleFatigueRiskResponse:
    """
    Assess fatigue risk for a proposed schedule.

    Evaluates how a proposed sequence of shifts would affect
    fatigue levels and identifies high-risk periods.

    Args:
        resident_id: UUID of the resident.
        proposed_shifts: List of shift dictionaries with start, end, type.

    Returns:
        ScheduleFatigueRiskResponse with risk assessment.

    Example:
        shifts = [
            {"start": "2025-01-15T07:00:00", "end": "2025-01-15T17:00:00", "type": "day"},
            {"start": "2025-01-16T19:00:00", "end": "2025-01-17T07:00:00", "type": "night"},
        ]

        result = await assess_schedule_fatigue_risk_tool(
            resident_id="550e8400-e29b-41d4-a716-446655440000",
            proposed_shifts=shifts
        )

        if result.overall_risk == "high":
            print(f"High risk periods: {result.high_risk_periods}")
    """
    return await assess_schedule_fatigue_risk(
        resident_id=resident_id,
        proposed_shifts=proposed_shifts,
    )


# ==================== RAG KNOWLEDGE BASE TOOLS ====================


@mcp.tool()
async def rag_search(
    query: str,
    top_k: int = 5,
    doc_type: str | None = None,
    min_similarity: float = 0.5,
) -> dict[str, Any]:
    """
    Search the RAG knowledge base for relevant documents.

    Performs semantic similarity search against indexed documentation
    including ACGME rules, scheduling policies, swap procedures, and more.

    Args:
        query: Natural language search query.
        top_k: Number of results to return (default: 5).
        doc_type: Optional filter by document type. Options:
                 acgme_rules, scheduling_policy, swap_system,
                 military_specific, resilience_concepts, user_guide_faq,
                 agent_spec, session_handoff, ai_patterns, ai_decisions.
        min_similarity: Minimum similarity threshold 0-1 (default: 0.5).

    Returns:
        Dict with:
        - query: Original query
        - documents: List of matching documents with content and similarity scores
        - total_results: Number of documents found
        - execution_time_ms: Query execution time

    Example:
        result = await rag_search(
            query="What are the ACGME work hour limits?",
            doc_type="acgme_rules"
        )

        for doc in result["documents"]:
            print(f"Score: {doc['similarity_score']:.2f}")
            print(f"Content: {doc['content'][:200]}...")
    """
    api_client = await get_api_client()
    return await api_client.rag_retrieve(
        query=query,
        top_k=top_k,
        doc_type=doc_type,
        min_similarity=min_similarity,
    )


@mcp.tool()
async def rag_context(
    query: str,
    max_tokens: int = 2000,
    doc_type: str | None = None,
) -> dict[str, Any]:
    """
    Build context from RAG knowledge base for LLM injection.

    Retrieves relevant documents and formats them into a context
    string suitable for injecting into LLM prompts.

    Args:
        query: Query to retrieve context for.
        max_tokens: Maximum tokens in context (default: 2000).
        doc_type: Optional filter by document type.

    Returns:
        Dict with:
        - query: Original query
        - context: Formatted context string ready for LLM
        - sources: Source documents used
        - token_count: Approximate token count
        - metadata: Context generation metadata

    Example:
        result = await rag_context(
            query="How do schedule swaps work?",
            max_tokens=1500
        )

        # Use result["context"] in your prompt
        prompt = f"Based on this context:\\n{result['context']}\\n\\nAnswer: ..."
    """
    api_client = await get_api_client()
    return await api_client.rag_build_context(
        query=query,
        max_tokens=max_tokens,
        doc_type=doc_type,
    )


@mcp.tool()
async def rag_health() -> dict[str, Any]:
    """
    Get health status of the RAG knowledge base system.

    Returns information about the RAG system including document counts,
    index status, and recommendations.

    Returns:
        Dict with:
        - status: "healthy" or "unhealthy"
        - total_documents: Total indexed chunks
        - documents_by_type: Breakdown by document type
        - embedding_model: Model used for embeddings
        - embedding_dimensions: Vector dimension size
        - vector_index_status: Index status (ready/building/missing)
        - recommendations: System improvement suggestions

    Example:
        health = await rag_health()

        print(f"Status: {health['status']}")
        print(f"Total chunks: {health['total_documents']}")
        for doc_type, count in health['documents_by_type'].items():
            print(f"  {doc_type}: {count}")
    """
    api_client = await get_api_client()
    return await api_client.rag_health()


@mcp.tool()
async def rag_ingest(
    content: str,
    doc_type: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Ingest a document into the RAG knowledge base.

    Chunks the content and stores with embeddings for later retrieval.
    Use this to add new documentation or update existing content.

    Args:
        content: Document text content to ingest.
        doc_type: Type of document. Suggested types:
                 acgme_rules, scheduling_policy, swap_system,
                 military_specific, resilience_concepts, user_guide_faq,
                 agent_spec, session_handoff, ai_patterns, ai_decisions.
        metadata: Optional metadata dict to store with chunks.

    Returns:
        Dict with:
        - status: "success" or "error"
        - chunks_created: Number of chunks created
        - chunk_ids: List of created chunk UUIDs
        - doc_type: Document type
        - message: Status message

    Example:
        result = await rag_ingest(
            content="# New Policy\\n\\nThis is the new scheduling policy...",
            doc_type="scheduling_policy",
            metadata={"source": "admin_update", "date": "2026-01-01"}
        )

        print(f"Created {result['chunks_created']} chunks")
    """
    api_client = await get_api_client()
    return await api_client.rag_ingest(
        content=content,
        doc_type=doc_type,
        metadata=metadata,
    )


# =============================================================================
# Schema Drift Detection Tool
# =============================================================================


@mcp.tool()
async def check_schema_drift_tool() -> dict[str, Any]:
    """
    Check for drift between SQLAlchemy models and database schema.

    Compares the SQLAlchemy model definitions in the codebase against
    the actual PostgreSQL database schema. Identifies:
    - Missing tables (in models but not DB)
    - Extra tables (in DB but not models)
    - Missing columns
    - Type mismatches
    - Index differences

    This tool helps prevent data corruption from schema drift.

    Returns:
        Dict with:
        - status: "ok" if no drift, "drift_detected" if differences found
        - model_tables: List of tables defined in SQLAlchemy models
        - db_tables: List of tables in actual database
        - missing_in_db: Tables in models but not in database
        - extra_in_db: Tables in database but not in models
        - column_diffs: Column-level differences per table
        - recommendations: Suggested actions to resolve drift

    Example:
        result = await check_schema_drift_tool()

        if result["status"] == "drift_detected":
            print(f"Missing tables: {result['missing_in_db']}")
            for rec in result["recommendations"]:
                print(f"  - {rec}")
    """
    try:
        api_client = await get_api_client()

        # Try to get schema info from API
        # If API has /schema/drift endpoint, use it
        try:
            response = await api_client._request_with_retry("GET", "/api/v1/schema/drift")
            return response
        except Exception:
            pass  # API endpoint doesn't exist, use fallback

        # Fallback: Compare known model tables vs information_schema
        # This is a simplified check that works without the full API endpoint

        # Known SQLAlchemy model tables from the codebase
        model_tables = [
            "persons",
            "assignments",
            "rotations",
            "schedules",
            "schedule_templates",
            "blocks",
            "leave_requests",
            "swap_requests",
            "activity_logs",
            "preferences",
            "constraints",
            "coverage_requirements",
            "supervision_ratios",
            "procedures",
            "procedure_logs",
            "users",
            "roles",
            "weekly_requirements",
            "resident_weekly_requirements",
            "alembic_version",
        ]

        # Try to query database for actual tables
        db_tables: list[str] = []
        try:
            # Use the API client to run a simple query
            # This endpoint may not exist, so we catch errors
            response = await api_client._request_with_retry("GET", "/api/v1/health/db")
            if "tables" in response:
                db_tables = response["tables"]
        except Exception:
            # Database not accessible or endpoint doesn't exist
            return {
                "status": "unknown",
                "error": "Could not connect to database to check schema",
                "model_tables": model_tables,
                "db_tables": [],
                "missing_in_db": [],
                "extra_in_db": [],
                "column_diffs": {},
                "recommendations": [
                    "Ensure DATABASE_URL is configured",
                    "Run: alembic upgrade head",
                    "Check database connectivity",
                ],
            }

        # Compare tables
        model_set = set(model_tables)
        db_set = set(db_tables)

        missing_in_db = list(model_set - db_set)
        extra_in_db = [t for t in (db_set - model_set) if not t.startswith("pg_")]

        # Determine status
        has_drift = bool(missing_in_db or extra_in_db)
        status = "drift_detected" if has_drift else "ok"

        # Generate recommendations
        recommendations = []
        if missing_in_db:
            recommendations.append(
                f"Run migrations: alembic upgrade head (missing: {', '.join(missing_in_db)})"
            )
        if extra_in_db:
            recommendations.append(
                f"Review extra tables (may need cleanup): {', '.join(extra_in_db)}"
            )
        if not has_drift:
            recommendations.append("Schema is in sync. No action needed.")

        return {
            "status": status,
            "model_tables": sorted(model_tables),
            "db_tables": sorted(db_tables),
            "missing_in_db": sorted(missing_in_db),
            "extra_in_db": sorted(extra_in_db),
            "column_diffs": {},  # Would require deeper introspection
            "recommendations": recommendations,
        }

    except Exception as e:
        logger.error(f"Schema drift check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "model_tables": [],
            "db_tables": [],
            "missing_in_db": [],
            "extra_in_db": [],
            "column_diffs": {},
            "recommendations": [
                "Schema drift check failed",
                f"Error: {e}",
                "Check MCP server logs for details",
            ],
        }


# Block Quality Report Tool
@mcp.tool()
async def generate_block_quality_report_tool(
    block_number: int,
    academic_year: int = 2025,
    output_format: str = "summary",
) -> dict[str, Any]:
    """
    Generate comprehensive quality report for a schedule block.

    Produces a detailed quality analysis including:
    - Section A: Preloaded data (block assignments, absences, call coverage)
    - Section B: Solved data (engine-generated assignments by rotation)
    - Section C: Combined gap analysis
    - Section D: Post-constraint verification (NF 1-in-7, post-call PCAT/DO)
    - Section E: Accountability (56 half-day accounting)

    Args:
        block_number: Block number (1-13)
        academic_year: Academic year (default: 2025)
        output_format: Output format:
            - "summary": Executive summary only (fast)
            - "full": Complete report data
            - "markdown": Full report as markdown string

    Returns:
        Dict with report data including executive summary, totals,
        and status checks. Format depends on output_format parameter.

    Example:
        # Quick summary check
        result = await generate_block_quality_report_tool(
            block_number=10,
            output_format="summary"
        )
        print(f"Total: {result['total_assignments']}")
        print(f"Status: {result['status']}")

        # Full report for analysis
        result = await generate_block_quality_report_tool(
            block_number=10,
            output_format="full"
        )
    """
    try:
        api_client = await get_api_client()

        # Call the backend API endpoint for the report
        # First try the dedicated endpoint
        try:
            response = await api_client._request_with_retry(
                "GET",
                "/api/v1/reports/block-quality",
                params={
                    "block_number": block_number,
                    "academic_year": academic_year,
                    "format": output_format,
                },
            )
            return response
        except Exception:
            pass  # Endpoint doesn't exist, use fallback

        # Fallback: Generate report using direct database queries
        # This requires the BlockQualityReportService to be available
        # For now, return a placeholder that indicates the tool exists
        # but needs the backend service to be running

        return {
            "status": "service_unavailable",
            "block_number": block_number,
            "academic_year": academic_year,
            "message": (
                "Block quality report API endpoint not available. "
                "Use the CLI script instead: "
                f"docker exec scheduler-local-backend python /app/scripts/generate_block_quality_report.py --block {block_number}"
            ),
            "fallback_command": (
                f"docker exec scheduler-local-backend python "
                f"/app/scripts/generate_block_quality_report.py --block {block_number}"
            ),
        }

    except Exception as e:
        logger.error(f"Block quality report generation failed: {e}")
        return {
            "status": "error",
            "block_number": block_number,
            "error": str(e),
            "message": "Failed to generate block quality report",
        }


@mcp.tool()
async def generate_multi_block_quality_report_tool(
    block_numbers: str,
    academic_year: int = 2025,
    include_summary: bool = True,
) -> dict[str, Any]:
    """
    Generate quality reports for multiple blocks with optional cross-block summary.

    Args:
        block_numbers: Block specification as comma-separated or range.
            Examples: "10,11,12" or "10-13"
        academic_year: Academic year (default: 2025)
        include_summary: Include cross-block summary report

    Returns:
        Dict with individual block summaries and optional combined summary.

    Example:
        result = await generate_multi_block_quality_report_tool(
            block_numbers="10-13",
            include_summary=True
        )
        print(f"Total across all blocks: {result['total_assignments']}")
        for block in result['blocks']:
            print(f"Block {block['block_number']}: {block['status']}")
    """
    try:
        # Parse block numbers
        blocks = []
        for part in block_numbers.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                blocks.extend(range(int(start), int(end) + 1))
            else:
                blocks.append(int(part))
        blocks = sorted(set(blocks))

        api_client = await get_api_client()

        # Try the API endpoint first
        try:
            response = await api_client._request_with_retry(
                "GET",
                "/api/v1/reports/block-quality/multi",
                params={
                    "blocks": ",".join(str(b) for b in blocks),
                    "academic_year": academic_year,
                    "include_summary": include_summary,
                },
            )
            return response
        except Exception:
            pass  # Fallback

        return {
            "status": "service_unavailable",
            "blocks": blocks,
            "academic_year": academic_year,
            "message": (
                "Multi-block report API endpoint not available. "
                "Use the CLI script instead."
            ),
            "fallback_command": (
                f"docker exec scheduler-local-backend python "
                f"/app/scripts/generate_block_quality_report.py "
                f"--blocks {block_numbers} {'--summary' if include_summary else ''}"
            ),
        }

    except Exception as e:
        logger.error(f"Multi-block quality report generation failed: {e}")
        return {
            "status": "error",
            "block_numbers": block_numbers,
            "error": str(e),
            "message": "Failed to generate multi-block quality report",
        }


# Server lifecycle functions (called by lifespan context manager)


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


async def on_shutdown() -> None:
    """
    Clean up server resources.

    Called when the server shuts down. Used for cleanup tasks like
    closing database connections.
    """
    logger.info("Shutting down Residency Scheduler MCP Server")

    # Close database connections
    if hasattr(mcp, "db_session") and mcp.db_session:
        try:
            await mcp.db_session.close()
            logger.info("Database session closed")
        except Exception as e:
            logger.warning(f"Error closing database session: {e}")

    # Close any open connections
    if hasattr(mcp, "connections"):
        for conn_id, conn in list(mcp.connections.items()):
            try:
                await conn.close()
                logger.debug(f"Closed connection: {conn_id}")
            except Exception as e:
                logger.warning(f"Error closing connection {conn_id}: {e}")
        mcp.connections.clear()

    # Flush any pending metrics
    if hasattr(mcp, "metrics"):
        try:
            await mcp.metrics.flush()
            logger.info("Metrics flushed")
        except Exception as e:
            logger.warning(f"Error flushing metrics: {e}")

    # Release any held resources
    if hasattr(mcp, "resource_locks"):
        for lock_name, lock in list(mcp.resource_locks.items()):
            try:
                if lock.locked():
                    lock.release()
                    logger.debug(f"Released lock: {lock_name}")
            except Exception as e:
                logger.warning(f"Error releasing lock {lock_name}: {e}")

    logger.info("Server shutdown complete")


# =============================================================================
# PAI Agent Spawning Tool
# =============================================================================


@mcp.tool()
async def spawn_agent_tool(
    agent_name: str,
    mission: str,
    context: dict[str, Any] | None = None,
    inject_rag: bool = True,
    inject_skills: list[str] | None = None,
    parent_agent: str | None = None,
) -> dict[str, Any]:
    """
    Prepare a PAI agent for spawning via Claude Code Task().

    This tool is a **factory** that prepares agent context. It loads the agent's
    identity card, injects relevant RAG context, matches skills, and returns
    a structured AgentSpec that Claude Code uses to spawn the agent.

    All execution happens in Claude Code - no API keys needed here.

    The spawned agent will have:
    - Full Claude Code capabilities (Edit, Write, Bash, MCP tools)
    - Tier-based iteration limits (Specialist=5, Coordinator=20, Deputy=50)
    - Checkpoint path for scratchpad state persistence
    - Escalation target for blocked situations

    Governance features:
    - Spawn chain validation (if parent_agent specified)
    - Identity-based tool access lists
    - Audit trail for all invocations
    - Escalation target from chain of command

    Args:
        agent_name: Agent identifier from .claude/agents.yaml registry.
                   Examples: "SCHEDULER", "COMPLIANCE_AUDITOR", "COORD_ENGINE",
                   "ARCHITECT", "G2_RECON"
        mission: Task description using Auftragstaktik (mission-type orders).
                Provide intent, not step-by-step recipe.
                Example: "Audit Block 10 for ACGME violations"
        context: Optional system state dict to inject.
                Example: {"block_number": 10, "academic_year": 2026}
        inject_rag: If True (default), query RAG for mission-relevant context.
        inject_skills: Optional list of skill names to inject.
                      If None, auto-matches based on mission + archetype.
        parent_agent: Optional name of invoking agent for spawn chain validation.
                     If specified, validates that parent can spawn this agent.

    Returns:
        AgentSpec dict with:
        - agent_name: Requested agent name
        - tier: Deputy/Coordinator/Specialist/G-Staff
        - model: opus/sonnet/haiku
        - full_prompt: Complete prompt with identity + RAG + skills + mission
        - max_turns: Tier-based iteration limit
        - subagent_type: "general-purpose" for Task()
        - checkpoint_path: Scratchpad path for state persistence
        - escalation_target: Who to escalate to when blocked
        - tools_access: List of MCP tools this agent can use
        - can_spawn: List of agents this agent can spawn (if any)

    Example:
        # Claude Code calls this tool
        spec = await spawn_agent_tool(
            agent_name="COMPLIANCE_AUDITOR",
            mission="Audit Block 10 for ACGME violations",
            context={"block_number": 10}
        )

        # Claude Code then spawns via Task()
        # Task(
        #     prompt=spec["full_prompt"],
        #     subagent_type=spec["subagent_type"],
        #     model=spec["model"],
        #     max_turns=spec["max_turns"]
        # )
    """
    import json
    from pathlib import Path

    logger.info(f"Preparing agent spawn: {agent_name} for mission: {mission[:50]}...")

    # Load agent registry
    project_root = Path(__file__).parent.parent.parent.parent
    registry_path = project_root / ".claude" / "agents.yaml"
    identities_path = project_root / ".claude" / "Identities"
    audit_path = project_root / ".claude" / "History" / "agent_invocations"

    # Ensure audit directory exists
    audit_path.mkdir(parents=True, exist_ok=True)

    # Try to load YAML registry
    agent_spec = None
    registry = None
    try:
        import yaml
        if registry_path.exists():
            with open(registry_path) as f:
                registry = yaml.safe_load(f)
                if registry and "agents" in registry:
                    agent_spec = registry["agents"].get(agent_name)
    except ImportError:
        logger.warning("PyYAML not available, using fallback agent spec")
    except Exception as e:
        logger.warning(f"Failed to load agent registry: {e}")

    # Fallback spec if not in registry
    if not agent_spec:
        agent_spec = {
            "tier": "Specialist",
            "model": "haiku",
            "archetype": "Generator",
            "role": f"{agent_name} agent",
            "reports_to": "ORCHESTRATOR",
            "can_spawn": [],
            "max_turns": 5,
            "tools_access": ["rag_search"],
            "relevant_doc_types": [],
        }
        logger.warning(f"Agent {agent_name} not in registry, using fallback spec")

    # Spawn chain validation
    spawn_chain_valid = True
    spawn_chain_error = None
    if parent_agent and registry:
        parent_spec = registry.get("agents", {}).get(parent_agent)
        if parent_spec:
            allowed_children = parent_spec.get("can_spawn", [])
            if agent_name not in allowed_children:
                spawn_chain_valid = False
                spawn_chain_error = (
                    f"Spawn chain violation: {parent_agent} cannot spawn {agent_name}. "
                    f"Allowed: {allowed_children}"
                )
                logger.warning(spawn_chain_error)
        else:
            logger.warning(f"Parent agent {parent_agent} not found in registry")

    # If spawn chain invalid, return error spec instead of proceeding
    if not spawn_chain_valid:
        return {
            "agent_name": agent_name,
            "status": "spawn_chain_violation",
            "error": spawn_chain_error,
            "parent_agent": parent_agent,
            "suggested_parent": agent_spec.get("reports_to", "ORCHESTRATOR"),
            "full_prompt": None,
            "audit_trail_path": None,
        }

    # Load identity card
    identity_content = ""
    identity_file = identities_path / f"{agent_name}.identity.md"
    if identity_file.exists():
        identity_content = identity_file.read_text()
    else:
        # Generate minimal identity
        identity_content = f"""# {agent_name} Identity Card

## Identity
- **Role:** {agent_spec.get('role', 'Specialist agent')}
- **Tier:** {agent_spec.get('tier', 'Specialist')}
- **Model:** {agent_spec.get('model', 'haiku')}

## Chain of Command
- **Reports To:** {agent_spec.get('reports_to', 'ORCHESTRATOR')}
- **Can Spawn:** {', '.join(agent_spec.get('can_spawn', [])) or 'None'}
- **Escalate To:** {agent_spec.get('reports_to', 'ORCHESTRATOR')}

## One-Line Charter
"Execute assigned mission with precision and report results."
"""
        logger.warning(f"Identity card not found for {agent_name}, using generated identity")

    # Build prompt parts
    prompt_parts = [identity_content]

    # Inject RAG context
    if inject_rag:
        try:
            api_client = await get_api_client()
            rag_results = await api_client.rag_retrieve(
                query=mission,
                top_k=5,
                min_similarity=0.5,
            )
            if rag_results.get("documents"):
                rag_section = "## RELEVANT KNOWLEDGE (from RAG)\n\n"
                for doc in rag_results["documents"][:5]:
                    content = doc.get("content", "")[:500]
                    score = doc.get("similarity_score", 0)
                    rag_section += f"**[Score: {score:.2f}]**\n{content}\n\n---\n\n"
                prompt_parts.append(rag_section)
                logger.info(f"Injected {len(rag_results['documents'])} RAG results")
        except Exception as e:
            logger.warning(f"RAG injection failed: {e}")

    # Inject skills (placeholder - skill matching not yet implemented)
    if inject_skills:
        skills_section = "## AVAILABLE SKILLS\n\n"
        for skill in inject_skills:
            skills_section += f"- /{skill}\n"
        prompt_parts.append(skills_section)

    # Add mission
    prompt_parts.append(f"## MISSION\n\n{mission}")

    # Add context if provided
    if context:
        prompt_parts.append(f"## CONTEXT\n\n```json\n{json.dumps(context, indent=2)}\n```")

    # Add checkpoint instruction
    checkpoint_path = f".claude/Scratchpad/AGENT_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    prompt_parts.append(f"""## CHECKPOINT PROTOCOL

Write your progress and findings to: `{checkpoint_path}`

Format:
```markdown
# {agent_name} Checkpoint

## Mission
{mission}

## Status
[in_progress | completed | escalated]

## Findings
[Your findings here]

## Next Steps
[If incomplete, what remains]

## Escalation
[If blocked, why and to whom]
```
""")

    # Tier-based max turns
    tier = agent_spec.get("tier", "Specialist")
    max_turns = {
        "Deputy": 50,
        "Coordinator": 20,
        "Specialist": 5,
        "G-Staff": 20,
        "Special": 15,
    }.get(tier, 10)

    # Override if specified in agent spec
    if "max_turns" in agent_spec:
        max_turns = agent_spec["max_turns"]

    full_prompt = "\n\n".join(prompt_parts)

    # Generate unique invocation ID for audit trail
    invocation_id = datetime.now().strftime('%Y%m%d_%H%M%S') + f"_{agent_name}"

    result = {
        "agent_name": agent_name,
        "tier": tier,
        "model": agent_spec.get("model", "haiku"),
        "archetype": agent_spec.get("archetype", "Generator"),
        "full_prompt": full_prompt,
        "max_turns": max_turns,
        "subagent_type": "general-purpose",
        "checkpoint_path": checkpoint_path,
        "escalation_target": agent_spec.get("reports_to", "ORCHESTRATOR"),
        "tools_access": agent_spec.get("tools_access", []),
        "can_spawn": agent_spec.get("can_spawn", []),
        "prompt_tokens_estimate": len(full_prompt) // 4,  # Rough estimate
        "invocation_id": invocation_id,
        "reports_to": agent_spec.get("reports_to", "ORCHESTRATOR"),
    }

    # Write audit trail
    audit_file = audit_path / f"{invocation_id}.json"
    audit_entry = {
        "invocation_id": invocation_id,
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name,
        "tier": tier,
        "model": result["model"],
        "mission": mission,
        "context": context,
        "rag_injected": inject_rag,
        "skills_injected": inject_skills or [],
        "tools_access": result["tools_access"],
        "can_spawn": result["can_spawn"],
        "checkpoint_path": checkpoint_path,
        "escalation_target": result["escalation_target"],
        "prompt_tokens_estimate": result["prompt_tokens_estimate"],
    }
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_entry, f, indent=2, default=str)
        result["audit_trail_path"] = str(audit_file)
        logger.info(f"Audit trail written: {audit_file}")
    except Exception as e:
        logger.warning(f"Failed to write audit trail: {e}")
        result["audit_trail_path"] = None

    logger.info(
        f"Agent spec prepared: {agent_name} (tier={tier}, model={result['model']}, "
        f"~{result['prompt_tokens_estimate']} tokens)"
    )

    return result


# =============================================================================
# Health Check Endpoint for HTTP Transport
# =============================================================================


def create_health_endpoint():
    """Create a health check endpoint handler for Render/load balancers."""
    if not STARLETTE_AVAILABLE:
        return None

    async def health_check(request):
        """Health check endpoint for monitoring."""
        api_key_configured = bool(os.environ.get("MCP_API_KEY"))
        api_credentials_configured = bool(
            os.environ.get("API_USERNAME") and os.environ.get("API_PASSWORD")
        )

        return JSONResponse({
            "status": "healthy",
            "service": "residency-scheduler-mcp",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {
                "mcp_server": "ok",
                "api_key_configured": api_key_configured,
                "api_credentials_configured": api_credentials_configured,
            }
        })

    return health_check


# =============================================================================
# API Key Authentication Middleware
# =============================================================================


class APIKeyAuthMiddleware:
    """
    ASGI middleware for API key authentication on HTTP transport.

    Validates the Authorization header against MCP_API_KEY environment variable.
    Health endpoint is excluded from authentication.
    """

    def __init__(self, app, api_key: str | None = None):
        self.app = app
        self.api_key = api_key or os.environ.get("MCP_API_KEY")
        self.exempt_paths = {"/health", "/health/", "/"}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Allow health checks without auth
        if path in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        # If no API key configured, allow all requests (dev mode)
        if not self.api_key:
            logger.warning("MCP_API_KEY not set - running without authentication")
            await self.app(scope, receive, send)
            return

        # Check Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        # Support both "Bearer <token>" and raw token
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif auth_header:
            token = auth_header

        if token != self.api_key:
            logger.warning(f"Unauthorized MCP request to {path}")
            response = JSONResponse(
                {"error": "Unauthorized", "message": "Invalid or missing API key"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """
    Run the MCP server.

    This is the main entry point when running as a script or via
    the scheduler-mcp command.

    For remote deployment (Render, etc.):
    - Set MCP_TRANSPORT=http
    - Set MCP_API_KEY for authentication
    - Health check available at /health
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
  MCP_TRANSPORT    Transport mode: http, sse, streamable-http (default: http)
  MCP_HOST         Host to bind for HTTP/SSE (default: 127.0.0.1)
  MCP_PORT         Port to bind for HTTP/SSE (default: 8080)
  MCP_API_KEY      API key for HTTP authentication (required for production)

Examples:
  # Run with HTTP transport (default)
  scheduler-mcp --host 0.0.0.0 --port 8080

  # Run with HTTP transport and authentication (for production)
  MCP_API_KEY=your-secret-key scheduler-mcp --host 0.0.0.0 --port 8080

  # Run with debug logging
  LOG_LEVEL=DEBUG scheduler-mcp
        """,
    )

    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "127.0.0.1"),
        help="Host to bind to for HTTP/SSE transport (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8080")),
        help="Port to bind to for HTTP/SSE transport (default: 8080)",
    )

    parser.add_argument(
        "--transport",
        default=os.getenv("MCP_TRANSPORT", "http"),
        choices=["http", "sse", "streamable-http"],
        help="Transport mode (default: http)",
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

    logger.info(f"Transport: {args.transport.upper()}")
    logger.info(f"Starting MCP server on {args.host}:{args.port}")

    # Check for API key in production
    api_key = os.environ.get("MCP_API_KEY")
    if api_key:
        logger.info("API key authentication enabled")
    else:
        logger.warning(
            "MCP_API_KEY not set - server running without authentication. "
            "This is insecure for production deployments!"
        )

    logger.info(f"Log level: {args.log_level}")

    # Run the server with HTTP transport
    try:
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        # Get the MCP ASGI app with stateless_http=True to disable session management
        # This is required because Claude Code's HTTP transport doesn't send
        # Mcp-Session-Id headers that FastMCP 2.x normally requires.
        mcp_app = mcp.http_app(stateless_http=True)

        # Create health endpoint
        health_handler = create_health_endpoint()
        routes = []
        if health_handler:
            routes.append(Route("/health", health_handler, methods=["GET"]))

        # Mount MCP app at /mcp and add health at root
        routes.append(Mount("/mcp", app=mcp_app))

        # Also mount at root for backwards compatibility
        routes.append(Mount("/", app=mcp_app))

        # Must use mcp_app.lifespan for FastMCP 2.x to initialize properly
        app = Starlette(routes=routes, lifespan=mcp_app.lifespan)

        # Wrap with auth middleware
        app = APIKeyAuthMiddleware(app)

        logger.info(f"Health check available at http://{args.host}:{args.port}/health")
        logger.info(f"MCP endpoint available at http://{args.host}:{args.port}/mcp")

        uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())

    except (ImportError, AttributeError) as e:
        logger.warning(f"Advanced HTTP features not available: {e}")
        logger.info("Falling back to basic FastMCP HTTP transport (SSE)")
        # FastMCP 1.x uses settings object for host/port configuration
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        # FastMCP 1.x uses 'sse' transport for HTTP
        transport = "sse" if args.transport in ("http", "streamable-http") else args.transport
        logger.info(f"Starting SSE server on {args.host}:{args.port}")
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
