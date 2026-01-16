"""
MCP Tool Definitions for PAI Agent Bridge.

This module registers PAI agents as MCP tools, enabling external systems
to invoke specialized agents via the MCP protocol.

Usage:
    from scheduler_mcp.pai_bridge.agent_tools import register_pai_agent_tools

    # Register with your FastMCP server
    register_pai_agent_tools(mcp)
"""

import logging
from typing import Any

from .executor import PAIAgentExecutor
from .models import AgentResult

logger = logging.getLogger(__name__)

# Global executor instance (initialized on first use)
_executor: PAIAgentExecutor | None = None


def get_executor() -> PAIAgentExecutor:
    """Get or create the global PAI agent executor."""
    global _executor
    if _executor is None:
        _executor = PAIAgentExecutor()
    return _executor


def register_pai_agent_tools(mcp) -> None:
    """
    Register PAI agent tools with a FastMCP server.

    Args:
        mcp: FastMCP server instance
    """
    executor = get_executor()

    @mcp.tool()
    async def invoke_scheduler_agent(
        mission: str,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
        require_approval: bool = False,
    ) -> dict:
        """
        Invoke the SCHEDULER specialist agent.

        The SCHEDULER generates compliant schedules using CP-SAT solver,
        validates ACGME compliance, and maintains audit trails.

        **Identity:**
        - Tier: Specialist
        - Reports To: COORD_ENGINE
        - Model: haiku

        **MCP Tools Available:**
        - validate_schedule
        - generate_schedule
        - detect_conflicts
        - analyze_swap_candidates
        - execute_swap

        **Standing Orders (autonomous):**
        1. Generate schedules using CP-SAT solver
        2. Validate against ACGME compliance rules
        3. Create database backups before writes
        4. Log solver metrics

        Args:
            mission: What the scheduler should accomplish
            context: Additional context (dates, constraints, preferences)
            constraints: Additional constraints beyond identity card
            require_approval: Whether to pause for human approval

        Returns:
            AgentResult with schedule generation results
        """
        result = await executor.invoke(
            agent_name="SCHEDULER",
            mission=mission,
            context=context or {},
            additional_constraints=constraints or [],
            require_approval=require_approval,
        )
        return result.model_dump()

    @mcp.tool()
    async def invoke_swap_manager_agent(
        mission: str,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
        require_approval: bool = True,
    ) -> dict:
        """
        Invoke the SWAP_MANAGER specialist agent.

        The SWAP_MANAGER handles schedule swap requests with safety checks,
        constraint validation, and audit trails.

        **Identity:**
        - Tier: Specialist
        - Reports To: COORD_ENGINE
        - Model: haiku

        **MCP Tools Available:**
        - analyze_swap_candidates
        - validate_schedule
        - execute_swap
        - detect_conflicts

        **Standing Orders (autonomous):**
        1. Analyze swap candidates for compatibility
        2. Validate swaps against ACGME constraints
        3. Maintain audit trail for all swap operations
        4. Check coverage impact before execution

        Args:
            mission: What swap operation to perform
            context: Swap details (requester, assignment, preferences)
            constraints: Additional constraints
            require_approval: Whether to require human approval (default: True)

        Returns:
            AgentResult with swap analysis/execution results
        """
        result = await executor.invoke(
            agent_name="SWAP_MANAGER",
            mission=mission,
            context=context or {},
            additional_constraints=constraints or [],
            require_approval=require_approval,
        )
        return result.model_dump()

    @mcp.tool()
    async def invoke_compliance_auditor_agent(
        mission: str,
        context: dict[str, Any] | None = None,
        audit_scope: str = "full",
    ) -> dict:
        """
        Invoke the COMPLIANCE_AUDITOR specialist agent.

        The COMPLIANCE_AUDITOR validates schedules against ACGME rules,
        institutional policies, and generates compliance reports.

        **Identity:**
        - Tier: Specialist
        - Reports To: COORD_RESILIENCE
        - Model: haiku

        **MCP Tools Available:**
        - validate_schedule
        - detect_conflicts
        - rag_search (for policy lookups)

        **Standing Orders (autonomous):**
        1. Audit schedules against ACGME rules
        2. Check institutional policy compliance
        3. Generate detailed compliance reports
        4. Flag violations with severity levels

        Args:
            mission: What compliance check to perform
            context: Schedule IDs, date ranges, specific rules to check
            audit_scope: "full", "acgme_only", "institutional_only"

        Returns:
            AgentResult with compliance audit results
        """
        result = await executor.invoke(
            agent_name="COMPLIANCE_AUDITOR",
            mission=mission,
            context={**(context or {}), "audit_scope": audit_scope},
            additional_constraints=[],
            require_approval=False,  # Audits are read-only
        )
        return result.model_dump()

    @mcp.tool()
    async def invoke_resilience_engineer_agent(
        mission: str,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
    ) -> dict:
        """
        Invoke the RESILIENCE_ENGINEER specialist agent.

        The RESILIENCE_ENGINEER analyzes system resilience, performs
        contingency analysis, and manages defense levels.

        **Identity:**
        - Tier: Specialist
        - Reports To: COORD_RESILIENCE
        - Model: sonnet

        **MCP Tools Available:**
        - check_utilization_threshold
        - run_contingency_analysis
        - get_defense_level
        - analyze_hub_centrality
        - get_static_fallbacks
        - execute_sacrifice_hierarchy

        **Standing Orders (autonomous):**
        1. Monitor utilization thresholds
        2. Run N-1/N-2 contingency analysis
        3. Recommend defense level adjustments
        4. Maintain resilience metrics

        Args:
            mission: What resilience analysis to perform
            context: Current state, scenario parameters
            constraints: Additional constraints

        Returns:
            AgentResult with resilience analysis results
        """
        result = await executor.invoke(
            agent_name="RESILIENCE_ENGINEER",
            mission=mission,
            context=context or {},
            additional_constraints=constraints or [],
            require_approval=False,
        )
        return result.model_dump()

    @mcp.tool()
    async def invoke_coordinator_agent(
        coordinator_name: str,
        mission: str,
        context: dict[str, Any] | None = None,
        spawn_specialists: bool = True,
    ) -> dict:
        """
        Invoke a COORD_* coordinator agent.

        Coordinators manage specialists and can spawn multiple sub-agents
        to accomplish complex tasks.

        **Valid Coordinators:**
        - COORD_ENGINE: Scheduling engine and optimization
        - COORD_PLATFORM: Backend, database, API
        - COORD_QUALITY: Testing, code review
        - COORD_FRONTEND: UI/UX development
        - COORD_OPS: Releases, documentation, CI/CD
        - COORD_RESILIENCE: Resilience engineering, compliance

        **Identity (typical):**
        - Tier: Coordinator
        - Reports To: ARCHITECT or SYNTHESIZER
        - Model: sonnet

        Args:
            coordinator_name: Which coordinator to invoke
            mission: What the coordinator should accomplish
            context: Additional context for the mission
            spawn_specialists: Whether coordinator can spawn specialist agents

        Returns:
            AgentResult with coordinated task results
        """
        valid_coordinators = [
            "COORD_ENGINE",
            "COORD_PLATFORM",
            "COORD_QUALITY",
            "COORD_FRONTEND",
            "COORD_OPS",
            "COORD_RESILIENCE",
            "COORD_TOOLING",
            "COORD_INTEL",
        ]

        if coordinator_name not in valid_coordinators:
            return {
                "agent_name": coordinator_name,
                "goal_id": "",
                "status": "error",
                "result": {
                    "error": f"Invalid coordinator: {coordinator_name}",
                    "valid_coordinators": valid_coordinators,
                },
                "tools_used": [],
                "execution_log": [f"Invalid coordinator name: {coordinator_name}"],
                "escalations": [],
                "audit_trail_path": "",
            }

        result = await executor.invoke(
            agent_name=coordinator_name,
            mission=mission,
            context={**(context or {}), "spawn_specialists": spawn_specialists},
            additional_constraints=[],
            require_approval=False,
        )
        return result.model_dump()

    @mcp.tool()
    async def invoke_g_staff_agent(
        staff_role: str,
        mission: str,
        context: dict[str, Any] | None = None,
        deploy_party: bool = False,
    ) -> dict:
        """
        Invoke a G-Staff (General Staff) advisory agent.

        G-Staff agents provide specialized advisory functions and can
        deploy "party" parallel probes for reconnaissance/planning.

        **Valid G-Staff:**
        - G1_PERSONNEL: Roster, staffing, team composition
        - G2_RECON: Intelligence, codebase reconnaissance
        - G3_OPERATIONS: Operational readiness, workflow validation
        - G4_CONTEXT: Historical context, continuity
        - G5_PLANNING: Strategic planning, risk assessment
        - G6_SIGNAL: Metrics, monitoring, communications

        **Identity:**
        - Tier: G-Staff (Advisory)
        - Reports To: ORCHESTRATOR (General Support)
        - Model: sonnet

        Args:
            staff_role: Which G-Staff to invoke (e.g., "G5_PLANNING")
            mission: Advisory question or planning task
            context: Relevant context
            deploy_party: Whether to deploy parallel probes

        Returns:
            AgentResult with advisory/planning results
        """
        valid_g_staff = [
            "G1_PERSONNEL",
            "G2_RECON",
            "G3_OPERATIONS",
            "G4_CONTEXT",
            "G5_PLANNING",
            "G6_SIGNAL",
        ]

        if staff_role not in valid_g_staff:
            return {
                "agent_name": staff_role,
                "goal_id": "",
                "status": "error",
                "result": {
                    "error": f"Invalid G-Staff role: {staff_role}",
                    "valid_roles": valid_g_staff,
                },
                "tools_used": [],
                "execution_log": [f"Invalid G-Staff role: {staff_role}"],
                "escalations": [],
                "audit_trail_path": "",
            }

        result = await executor.invoke(
            agent_name=staff_role,
            mission=mission,
            context={**(context or {}), "deploy_party": deploy_party},
            additional_constraints=[],
            require_approval=False,
        )
        return result.model_dump()

    @mcp.tool()
    async def list_pai_agents() -> dict:
        """
        List all available PAI agents and their capabilities.

        Returns a summary of all agents including:
        - Name and role
        - Tier and model assignment
        - Available MCP tools
        - Spawn authority

        Returns:
            Dictionary with agent summaries
        """
        agents = await executor.list_available_agents()

        # Group by tier
        by_tier = {
            "Deputy": [],
            "Coordinator": [],
            "Specialist": [],
            "G-Staff": [],
            "Other": [],
        }

        for agent in agents:
            tier = agent.get("tier", "Other")
            if tier in by_tier:
                by_tier[tier].append(agent)
            else:
                by_tier["Other"].append(agent)

        return {
            "total_agents": len(agents),
            "by_tier": by_tier,
            "agents": agents,
        }

    @mcp.tool()
    async def get_agent_capabilities(agent_name: str) -> dict:
        """
        Get detailed capabilities for a specific PAI agent.

        Returns:
        - Identity card details
        - Allowed MCP tools
        - Spawn authority
        - Standing orders
        - Constraints

        Args:
            agent_name: Agent name (e.g., "SCHEDULER")

        Returns:
            Detailed capability summary
        """
        identity = await executor.identity_loader.load(agent_name)

        if identity is None:
            return {
                "error": f"Agent not found: {agent_name}",
                "available_agents": executor.identity_loader.list_available_agents(),
            }

        capabilities = executor.tool_validator.get_agent_capabilities(agent_name)

        return {
            "name": identity.name,
            "role": identity.role,
            "tier": identity.tier,
            "model": identity.model,
            "chain_of_command": {
                "reports_to": identity.reports_to,
                "can_spawn": identity.can_spawn,
                "escalate_to": identity.escalate_to,
            },
            "standing_orders": identity.standing_orders,
            "escalation_triggers": identity.escalation_triggers,
            "constraints": identity.constraints,
            "charter": identity.charter,
            "mcp_tools": {
                "allowed": capabilities["allowed_tools"],
                "preconditions": capabilities["tool_preconditions"],
            },
            "is_terminal": capabilities["is_terminal"],
        }

    logger.info("PAI agent tools registered with MCP server")
