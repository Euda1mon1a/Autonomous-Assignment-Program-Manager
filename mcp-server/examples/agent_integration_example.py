"""
Example: Integrating AgentMCPServer with FastMCP Server

This example demonstrates how to integrate the agentic tools
from AgentMCPServer with the existing FastMCP server.

Usage:
    python agent_integration_example.py
"""

import asyncio
import logging
from datetime import date, timedelta

from scheduler_mcp.agent_server import (
    AgentMCPServer,
    AnalyzeAndFixResult,
    OptimizeCoverageResult,
    ResolveConflictResult,
)
from scheduler_mcp.server import mcp  # The existing FastMCP instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================================
# Integration: Register Agentic Tools with FastMCP
# ============================================================================


def register_agentic_tools():
    """
    Register agentic tools from AgentMCPServer with the main FastMCP server.

    This allows the agentic tools to be called through the standard MCP protocol.
    """
    # Initialize the agent server
    agent = AgentMCPServer(llm_provider="claude-3-5-sonnet-20241022")

    # Register analyze_and_fix_schedule tool
    @mcp.tool()
    async def analyze_and_fix_schedule_agent(
        schedule_id: str | None = None,
        issue_description: str = "",
        auto_apply: bool = False,
    ) -> dict:
        """
        Agentic schedule analysis and repair.

        Uses multi-step reasoning to:
        1. Identify schedule problems
        2. Determine root causes
        3. Generate solution options
        4. Evaluate and recommend fixes
        5. Optionally apply fixes

        Args:
            schedule_id: ID of schedule to analyze (None = current)
            issue_description: Description of the issue to address
            auto_apply: Whether to automatically apply recommended fixes

        Returns:
            Analysis results with recommended/applied fixes
        """
        result = await agent.analyze_and_fix_schedule(
            schedule_id=schedule_id,
            issue_description=issue_description,
            auto_apply=auto_apply,
        )

        # Convert Pydantic model to dict for MCP response
        return result.model_dump()

    # Register optimize_coverage tool
    @mcp.tool()
    async def optimize_coverage_agent(
        start_date: str,
        end_date: str,
        optimization_goal: str = "maximize_coverage",
        constraints: dict | None = None,
    ) -> dict:
        """
        Agentic coverage optimization.

        Uses multi-step reasoning to:
        1. Analyze coverage gaps
        2. Generate optimization options
        3. Score options against criteria
        4. Recommend best approach

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            optimization_goal: What to optimize (coverage, cost, workload, etc.)
            constraints: Additional constraints to honor

        Returns:
            Optimization options with scores and recommendations
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        result = await agent.optimize_coverage(
            start_date=start,
            end_date=end,
            optimization_goal=optimization_goal,
            constraints=constraints or {},
        )

        return result.model_dump()

    # Register resolve_conflict tool
    @mcp.tool()
    async def resolve_conflict_agent(
        conflict_description: str,
        constraints: dict | None = None,
        require_approval: bool = True,
    ) -> dict:
        """
        Agentic conflict resolution.

        Uses multi-step reasoning to:
        1. Identify all stakeholders
        2. Generate resolution strategies
        3. Evaluate trade-offs and fairness
        4. Propose resolution with reasoning

        Args:
            conflict_description: Description of the conflict
            constraints: Constraints on resolution
            require_approval: Whether to require human approval

        Returns:
            Proposed resolutions with stakeholder analysis and approval status
        """
        result = await agent.resolve_conflict(
            conflict_description=conflict_description,
            constraints=constraints or {},
            require_approval=require_approval,
        )

        return result.model_dump()

    # Register goal status tool
    @mcp.tool()
    async def get_agentic_goal_status(goal_id: str) -> dict:
        """
        Get status of an agentic goal/workflow.

        Args:
            goal_id: UUID of the goal to check

        Returns:
            Goal status with task progress
        """
        from uuid import UUID

        status = agent.get_goal_status(UUID(goal_id))
        return status

    logger.info("Agentic tools registered with FastMCP server")

    return agent


# ============================================================================
# Example Usage
# ============================================================================


async def example_analyze_and_fix():
    """Example: Analyze and fix a schedule issue."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Analyze and Fix Schedule")
    print("=" * 70 + "\n")

    agent = AgentMCPServer()

    # Scenario: Coverage gap detected
    result = await agent.analyze_and_fix_schedule(
        schedule_id="sched-2025-01",
        issue_description="Coverage gap on 2025-01-15 PM shift due to unexpected absence",
        auto_apply=False,  # Don't auto-apply, just recommend
    )

    print("Analysis Results:")
    print(f"  Goal ID: {result.goal_id}")
    print(f"  Status: {result.status}")
    print(f"  Severity: {result.analysis.severity}")
    print(f"  Issues Found: {len(result.analysis.issues_found)}")

    print("\nIssues:")
    for issue in result.analysis.issues_found:
        print(f"  - {issue}")

    print("\nRoot Causes:")
    for cause in result.analysis.root_causes:
        print(f"  - {cause}")

    print(f"\nRecommended Fixes: {len(result.recommended_fixes)}")
    for fix in result.recommended_fixes:
        print(f"\n  Fix: {fix.description}")
        print(f"    Type: {fix.fix_type}")
        print(f"    Effort: {fix.estimated_effort}")
        print(f"    Success Probability: {fix.success_probability:.0%}")
        print(f"    Requires Approval: {fix.requires_approval}")

    print("\nExecution Log:")
    for log_entry in result.execution_log:
        print(f"  {log_entry}")

    print(f"\nCompleted {result.completed_tasks}/{result.total_tasks} tasks")


async def example_optimize_coverage():
    """Example: Optimize coverage for a date range."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Optimize Coverage")
    print("=" * 70 + "\n")

    agent = AgentMCPServer()

    # Scenario: Optimize coverage for next month
    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=30)

    result = await agent.optimize_coverage(
        start_date=start,
        end_date=end,
        optimization_goal="maximize_coverage_minimize_cost",
        constraints={"max_overtime_hours": 20, "maintain_acgme_compliance": True},
    )

    print("Optimization Results:")
    print(f"  Goal ID: {result.goal_id}")
    print(f"  Status: {result.status}")
    print(f"  Date Range: {result.date_range[0]} to {result.date_range[1]}")
    print(f"  Current Coverage: {result.current_coverage_rate:.0%}")
    print(f"  Gaps Identified: {result.gaps_identified}")

    print(f"\nGenerated {len(result.options_generated)} optimization options:")
    for i, option in enumerate(result.options_generated, 1):
        print(f"\n  Option {i}: {option.strategy}")
        print(f"    Description: {option.description}")
        print(f"    Coverage Improvement: +{option.expected_coverage_improvement:.0%}")
        print(f"    Workload Impact: {option.workload_impact}")
        print(f"    Compliance Maintained: {option.compliance_maintained}")
        print(f"    Cost: ${option.estimated_cost:.2f}")
        print(f"    Score: {option.score:.2f}")
        print(f"    Reasoning: {option.reasoning}")

    if result.recommended_option_id:
        print(f"\n  ⭐ Recommended: {result.recommended_option_id}")

    print("\nExecution Log:")
    for log_entry in result.execution_log:
        print(f"  {log_entry}")


async def example_resolve_conflict():
    """Example: Resolve a scheduling conflict."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Resolve Conflict")
    print("=" * 70 + "\n")

    agent = AgentMCPServer()

    # Scenario: Two faculty want the same shift off
    result = await agent.resolve_conflict(
        conflict_description=(
            "Dr. Smith and Dr. Martinez both requested 2025-01-20 off for "
            "personal reasons. Only one can be granted leave without "
            "violating coverage requirements."
        ),
        constraints={"must_maintain_supervision_ratio": True, "acgme_compliant": True},
        require_approval=True,
    )

    print("Conflict Resolution Results:")
    print(f"  Goal ID: {result.goal_id}")
    print(f"  Status: {result.status}")

    print("\nStakeholders Identified:")
    for stakeholder in result.stakeholders_identified:
        print(f"  - {stakeholder}")

    print(f"\nProposed Resolutions: {len(result.resolutions_proposed)}")
    for i, resolution in enumerate(result.resolutions_proposed, 1):
        print(f"\n  Resolution {i}: {resolution.strategy}")
        print(f"    Description: {resolution.description}")
        print(f"    Fairness Score: {resolution.fairness_score:.2f}")
        print(f"    Requires Approval: {resolution.requires_approval}")

        print(f"    Trade-offs:")
        for stakeholder, tradeoff in resolution.trade_offs.items():
            print(f"      - {stakeholder}: {tradeoff}")

        print(f"    Implementation Steps:")
        for step in resolution.implementation_steps:
            print(f"      {step}")

    if result.recommended_resolution_id:
        print(f"\n  ⭐ Recommended: {result.recommended_resolution_id}")

    if result.awaiting_approval:
        print("\n  ⏸ Awaiting human approval before proceeding")

    print("\nExecution Log:")
    for log_entry in result.execution_log:
        print(f"  {log_entry}")


async def example_goal_tracking():
    """Example: Track an agentic goal's progress."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Goal Tracking")
    print("=" * 70 + "\n")

    agent = AgentMCPServer()

    # Start a goal
    result = await agent.analyze_and_fix_schedule(
        issue_description="Test issue for tracking",
        auto_apply=False,
    )

    # Get goal status
    status = agent.get_goal_status(result.goal_id)

    print("Goal Status:")
    print(f"  ID: {status['goal_id']}")
    print(f"  Description: {status['description']}")
    print(f"  Status: {status['status']}")
    print(f"  Success: {status['success']}")
    print(f"  Progress: {status['progress']}")

    print("\nTasks:")
    for task in status["tasks"]:
        icon = "✓" if task["status"] == "completed" else "○"
        llm = "🧠" if task["requires_llm"] else "  "
        human = "👤" if task["requires_human"] else "  "
        print(f"  {icon} {llm}{human} {task['name']} - {task['status']}")

    print(f"\n  Created: {status['created_at']}")
    if status["completed_at"]:
        print(f"  Completed: {status['completed_at']}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MCP AGENT SERVER - EXAMPLES")
    print("=" * 70)

    await example_analyze_and_fix()
    await example_optimize_coverage()
    await example_resolve_conflict()
    await example_goal_tracking()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
