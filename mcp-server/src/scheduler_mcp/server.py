"""
Main MCP server for the residency scheduler.

This module creates and configures the FastMCP server, registering all
tools and resources for AI assistant interaction.
"""

import logging
import os
import sys
from datetime import date

from fastmcp import FastMCP

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
