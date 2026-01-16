"""
Tool Access Validator for PAI Agent MCP Bridge.

Enforces identity-based access control for MCP tools and validates
spawn chains according to the PAI governance framework.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from .models import AgentIdentity, ToolAccessRecord, SpawnRecord

logger = logging.getLogger(__name__)


# =============================================================================
# Agent-to-Tool Mapping (from AGENT_MCP_MATRIX.md)
# =============================================================================

AGENT_TOOL_MATRIX: dict[str, list[str]] = {
    # P0 Mission-Critical: Scheduling Core
    "SCHEDULER": [
        "validate_schedule",
        "generate_schedule",
        "detect_conflicts",
        "analyze_swap_candidates",
        "execute_swap",
    ],
    "SWAP_MANAGER": [
        "analyze_swap_candidates",
        "validate_schedule",
        "execute_swap",
        "detect_conflicts",
    ],
    "COORD_ENGINE": [
        "validate_schedule",
        "generate_schedule",
        "detect_conflicts",
        "analyze_swap_candidates",
        "execute_swap",
        "run_contingency_analysis",
        "check_utilization_threshold",
    ],
    "OPTIMIZATION_SPECIALIST": [
        "generate_schedule",
        "validate_schedule",
        "analyze_hub_centrality",
        "detect_conflicts",
    ],

    # P0 Regulatory
    "COMPLIANCE_AUDITOR": [
        "validate_schedule",
        "detect_conflicts",
        "rag_search",
    ],
    "SECURITY_AUDITOR": [
        "validate_schedule",
        "detect_conflicts",
        "rag_search",
    ],

    # P1 Resilience
    "RESILIENCE_ENGINEER": [
        "check_utilization_threshold",
        "run_contingency_analysis",
        "get_defense_level",
        "analyze_hub_centrality",
        "get_static_fallbacks",
        "execute_sacrifice_hierarchy",
    ],
    "BURNOUT_SENTINEL": [
        "check_utilization_threshold",
        "get_defense_level",
        "detect_burnout_precursors",
        "run_spc_analysis",
        "calculate_burnout_rt",
    ],
    "CAPACITY_OPTIMIZER": [
        "check_utilization_threshold",
        "run_contingency_analysis",
        "calculate_erlang_coverage",
        "analyze_hub_centrality",
    ],
    "EPIDEMIC_ANALYST": [
        "calculate_burnout_rt",
        "run_spc_analysis",
        "get_defense_level",
    ],

    # P1 Operations
    "G3_OPERATIONS": [
        "detect_conflicts",
        "get_task_status",
        "list_active_tasks",
    ],
    "G5_PLANNING": [
        "validate_schedule",
        "run_contingency_analysis",
        "rag_search",
        "get_defense_level",
    ],
    "CI_LIAISON": [
        "start_background_task",
        "get_task_status",
        "cancel_task",
        "list_active_tasks",
    ],

    # P2 Infrastructure / RAG
    "KNOWLEDGE_CURATOR": [
        "rag_search",
        "rag_ingest",
        "rag_context",
        "rag_health",
    ],
    "TOOL_QA": [
        "rag_search",
        "rag_context",
    ],
    "TOOL_REVIEWER": [
        "rag_search",
        "rag_context",
    ],
    "AGENT_FACTORY": [
        "rag_search",
        "rag_ingest",
        "rag_context",
    ],
    "COORD_TOOLING": [
        "rag_search",
        "rag_ingest",
        "rag_context",
        "rag_health",
    ],

    # Coordinators (delegate to specialists)
    "COORD_PLATFORM": [],  # Delegates to DBA, BACKEND_ENGINEER
    "COORD_QUALITY": [],   # Delegates to QA_TESTER, CODE_REVIEWER
    "COORD_FRONTEND": [],  # Delegates to FRONTEND_ENGINEER
    "COORD_OPS": [],       # Delegates to RELEASE_MANAGER
    "COORD_RESILIENCE": [
        "get_defense_level",
        "check_utilization_threshold",
    ],
    "COORD_INTEL": [
        "rag_search",
    ],

    # Deputies (strategic, minimal direct tool use)
    "ARCHITECT": [],
    "SYNTHESIZER": [],
    "ORCHESTRATOR": [],

    # G-Staff (advisory)
    "G1_PERSONNEL": [],
    "G2_RECON": ["rag_search"],
    "G4_CONTEXT": ["rag_search", "rag_context"],
    "G6_SIGNAL": [],
}


# =============================================================================
# Spawn Chain Matrix (from SPAWN_CHAINS.md)
# =============================================================================

SPAWN_CHAINS: dict[str, list[str]] = {
    # Command Level
    "ORCHESTRATOR": ["ARCHITECT", "SYNTHESIZER", "USASOC"],

    # Deputy Level
    "ARCHITECT": [
        "COORD_PLATFORM", "COORD_QUALITY", "COORD_ENGINE", "COORD_TOOLING",
        "G6_SIGNAL", "G2_RECON", "G5_PLANNING", "DEVCOM_RESEARCH",
    ],
    "SYNTHESIZER": [
        "COORD_OPS", "COORD_RESILIENCE", "COORD_FRONTEND", "COORD_INTEL",
        "G1_PERSONNEL", "G3_OPERATIONS", "G4_CONTEXT",
        "G2_RECON", "G5_PLANNING",
    ],

    # Coordinator Level
    "COORD_ENGINE": ["SCHEDULER", "SWAP_MANAGER", "OPTIMIZATION_SPECIALIST"],
    "COORD_PLATFORM": ["DBA", "BACKEND_ENGINEER", "API_DEVELOPER"],
    "COORD_QUALITY": ["QA_TESTER", "CODE_REVIEWER"],
    "COORD_FRONTEND": ["FRONTEND_ENGINEER", "UX_SPECIALIST"],
    "COORD_OPS": ["RELEASE_MANAGER", "META_UPDATER", "CI_LIAISON"],
    "COORD_RESILIENCE": ["RESILIENCE_ENGINEER", "COMPLIANCE_AUDITOR", "BURNOUT_SENTINEL"],
    "COORD_TOOLING": ["TOOLSMITH", "TOOL_QA", "TOOL_REVIEWER", "SKILL_FACTORY"],
    "COORD_INTEL": ["KNOWLEDGE_CURATOR", "SECURITY_AUDITOR"],

    # G-Staff (advisory, can spawn party probes)
    "G1_PERSONNEL": ["roster-party-probe"],
    "G2_RECON": ["search-party-probe"],
    "G3_OPERATIONS": ["ops-party-probe"],
    "G4_CONTEXT": ["context-party-probe"],
    "G5_PLANNING": ["plan-party-probe"],
    "G6_SIGNAL": ["signal-party-probe"],

    # Terminal Specialists (cannot spawn)
    "SCHEDULER": [],
    "SWAP_MANAGER": [],
    "OPTIMIZATION_SPECIALIST": [],
    "DBA": [],
    "BACKEND_ENGINEER": [],
    "API_DEVELOPER": [],
    "QA_TESTER": [],
    "CODE_REVIEWER": [],
    "FRONTEND_ENGINEER": [],
    "UX_SPECIALIST": [],
    "RELEASE_MANAGER": [],
    "RESILIENCE_ENGINEER": [],
    "COMPLIANCE_AUDITOR": [],
    "SECURITY_AUDITOR": [],
    "KNOWLEDGE_CURATOR": [],
    "TOOLSMITH": [],
    "TOOL_QA": [],
    "TOOL_REVIEWER": [],
}


# =============================================================================
# Tool Preconditions (safety gates)
# =============================================================================

TOOL_PRECONDITIONS: dict[str, list[str]] = {
    "execute_swap": [
        "backup_verified",      # Database backup must exist
        "validate_called",      # validate_schedule must be called first
    ],
    "generate_schedule": [
        "backup_verified",      # Database backup must exist
    ],
    "execute_sacrifice_hierarchy": [
        "defense_level_checked",  # get_defense_level must be called first
        "requires_approval",      # Human approval required
    ],
}


class ToolAccessValidator:
    """
    Validates tool access based on agent identity.

    Enforces:
    - Agent-to-tool whitelist (AGENT_TOOL_MATRIX)
    - Spawn chain hierarchy (SPAWN_CHAINS)
    - Tool preconditions (TOOL_PRECONDITIONS)
    - Audit logging for all access attempts
    """

    def __init__(
        self,
        matrix_path: Path | str | None = None,
        spawn_chains_path: Path | str | None = None,
    ):
        """
        Initialize the validator.

        Args:
            matrix_path: Path to AGENT_MCP_MATRIX.md (optional, uses hardcoded)
            spawn_chains_path: Path to SPAWN_CHAINS.md (optional, uses hardcoded)
        """
        self.matrix_path = Path(matrix_path) if matrix_path else None
        self.spawn_chains_path = Path(spawn_chains_path) if spawn_chains_path else None

        # Use hardcoded mappings (could be extended to parse files)
        self.agent_tools = AGENT_TOOL_MATRIX.copy()
        self.spawn_chains = SPAWN_CHAINS.copy()
        self.preconditions = TOOL_PRECONDITIONS.copy()

        # Audit trail
        self._access_log: list[ToolAccessRecord] = []
        self._spawn_log: list[SpawnRecord] = []

        logger.info("ToolAccessValidator initialized")

    async def get_allowed_tools(self, agent_name: str) -> list[str]:
        """
        Get list of MCP tools allowed for an agent.

        Args:
            agent_name: Agent name (e.g., "SCHEDULER")

        Returns:
            List of allowed tool names
        """
        return self.agent_tools.get(agent_name, [])

    async def can_access_tool(
        self,
        agent_name: str,
        tool_name: str,
        invocation_id: UUID | None = None,
    ) -> bool:
        """
        Check if agent can access a specific tool.

        Args:
            agent_name: Agent name
            tool_name: MCP tool name
            invocation_id: Optional invocation ID for audit

        Returns:
            True if access allowed, False otherwise
        """
        allowed_tools = self.agent_tools.get(agent_name, [])
        allowed = tool_name in allowed_tools

        # Log access attempt
        self.log_access_attempt(
            agent_name=agent_name,
            tool_name=tool_name,
            allowed=allowed,
            reason="in_whitelist" if allowed else "not_in_whitelist",
            invocation_id=invocation_id,
        )

        return allowed

    async def validate_spawn(
        self,
        parent: str,
        child: str,
        invocation_id: UUID | None = None,
    ) -> bool:
        """
        Validate that parent can spawn child agent.

        Args:
            parent: Parent agent name
            child: Child agent name
            invocation_id: Optional invocation ID for audit

        Returns:
            True if spawn allowed, False otherwise
        """
        allowed_children = self.spawn_chains.get(parent, [])
        allowed = child in allowed_children

        # Log spawn attempt
        self.log_spawn_attempt(
            parent=parent,
            child=child,
            allowed=allowed,
            reason="in_spawn_chain" if allowed else "not_in_spawn_chain",
            invocation_id=invocation_id,
        )

        if not allowed:
            logger.warning(
                f"Spawn chain violation: {parent} cannot spawn {child}",
                extra={"parent": parent, "child": child},
            )

        return allowed

    async def check_preconditions(
        self,
        agent_name: str,
        tool_name: str,
        context: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Check tool-specific preconditions.

        Args:
            agent_name: Agent name
            tool_name: Tool being called
            context: Execution context with flags

        Returns:
            Tuple of (preconditions_met, reason)
        """
        required = self.preconditions.get(tool_name, [])

        for precondition in required:
            if precondition == "backup_verified":
                if not context.get("backup_verified", False):
                    return False, "Database backup not verified"

            elif precondition == "validate_called":
                if "validate_schedule" not in context.get("tools_called", []):
                    return False, "validate_schedule must be called first"

            elif precondition == "defense_level_checked":
                if "get_defense_level" not in context.get("tools_called", []):
                    return False, "get_defense_level must be called first"

            elif precondition == "requires_approval":
                if not context.get("human_approved", False):
                    return False, "Human approval required"

        return True, "all_preconditions_met"

    def log_access_attempt(
        self,
        agent_name: str,
        tool_name: str,
        allowed: bool,
        reason: str = "",
        invocation_id: UUID | None = None,
        agent_tier: str = "",
    ) -> None:
        """
        Log tool access attempt for audit.

        Args:
            agent_name: Agent attempting access
            tool_name: Tool being accessed
            allowed: Whether access was allowed
            reason: Reason for decision
            invocation_id: Invocation ID
            agent_tier: Agent tier
        """
        from uuid import uuid4

        record = ToolAccessRecord(
            timestamp=datetime.now(),
            agent_name=agent_name,
            agent_tier=agent_tier,
            tool_name=tool_name,
            allowed=allowed,
            reason=reason,
            invocation_id=invocation_id or uuid4(),
        )

        self._access_log.append(record)

        status = "ALLOWED" if allowed else "DENIED"
        logger.info(
            f"Tool access {status}: {agent_name} -> {tool_name} ({reason})",
            extra={
                "agent": agent_name,
                "tool": tool_name,
                "allowed": allowed,
                "reason": reason,
            }
        )

    def log_spawn_attempt(
        self,
        parent: str,
        child: str,
        allowed: bool,
        reason: str = "",
        invocation_id: UUID | None = None,
    ) -> None:
        """
        Log spawn attempt for audit.

        Args:
            parent: Parent agent
            child: Child agent
            allowed: Whether spawn was allowed
            reason: Reason for decision
            invocation_id: Invocation ID
        """
        from uuid import uuid4

        record = SpawnRecord(
            timestamp=datetime.now(),
            parent_agent=parent,
            child_agent=child,
            allowed=allowed,
            reason=reason,
            invocation_id=invocation_id or uuid4(),
        )

        self._spawn_log.append(record)

        status = "ALLOWED" if allowed else "DENIED"
        logger.info(
            f"Spawn {status}: {parent} -> {child} ({reason})",
            extra={
                "parent": parent,
                "child": child,
                "allowed": allowed,
                "reason": reason,
            }
        )

    def get_access_log(self) -> list[ToolAccessRecord]:
        """Get tool access audit log."""
        return self._access_log.copy()

    def get_spawn_log(self) -> list[SpawnRecord]:
        """Get spawn audit log."""
        return self._spawn_log.copy()

    def clear_logs(self) -> None:
        """Clear audit logs (use carefully)."""
        self._access_log.clear()
        self._spawn_log.clear()
        logger.info("Audit logs cleared")

    def get_agent_capabilities(self, agent_name: str) -> dict[str, Any]:
        """
        Get complete capabilities summary for an agent.

        Args:
            agent_name: Agent name

        Returns:
            Dictionary with tools, spawn authority, and preconditions
        """
        allowed_tools = self.agent_tools.get(agent_name, [])
        can_spawn = self.spawn_chains.get(agent_name, [])

        # Get preconditions for allowed tools
        tool_preconditions = {}
        for tool in allowed_tools:
            if tool in self.preconditions:
                tool_preconditions[tool] = self.preconditions[tool]

        return {
            "agent_name": agent_name,
            "allowed_tools": allowed_tools,
            "can_spawn": can_spawn,
            "tool_preconditions": tool_preconditions,
            "is_terminal": len(can_spawn) == 0,
        }
