"""
PAI Agent Executor for MCP Bridge.

Executes PAI agents with identity-based tool access control and
proper governance enforcement.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .models import AgentIdentity, AgentResult
from .identity_loader import IdentityLoader
from .tool_validator import ToolAccessValidator

logger = logging.getLogger(__name__)


class PAIAgentExecutor:
    """
    Executes PAI agents with identity-based tool access control.

    Bridges PAI governance (identity cards, spawn chains) with
    MCP tool execution (agent_server, tool registry).

    Key responsibilities:
    - Load and parse agent identity cards
    - Validate spawn chains
    - Enforce tool access control
    - Build agent prompts with identity context
    - Execute via LLM with filtered tools
    - Maintain audit trails
    """

    def __init__(
        self,
        identities_path: Path | str | None = None,
        matrix_path: Path | str | None = None,
        audit_path: Path | str | None = None,
    ):
        """
        Initialize the executor.

        Args:
            identities_path: Path to .claude/Identities/
            matrix_path: Path to AGENT_MCP_MATRIX.md
            audit_path: Path for audit trail files
        """
        self.identities_path = Path(identities_path) if identities_path else Path(".claude/Identities")
        self.matrix_path = Path(matrix_path) if matrix_path else Path(".claude/AGENT_MCP_MATRIX.md")
        self.audit_path = Path(audit_path) if audit_path else Path(".claude/History/agent_invocations")

        # Initialize components
        self.identity_loader = IdentityLoader(self.identities_path)
        self.tool_validator = ToolAccessValidator(self.matrix_path)

        # Track active invocations
        self.active_invocations: dict[UUID, dict[str, Any]] = {}

        logger.info(
            f"PAIAgentExecutor initialized",
            extra={
                "identities_path": str(self.identities_path),
                "audit_path": str(self.audit_path),
            }
        )

    async def invoke(
        self,
        agent_name: str,
        mission: str,
        context: dict[str, Any] | None = None,
        additional_constraints: list[str] | None = None,
        require_approval: bool = False,
        parent_agent: str | None = None,
    ) -> AgentResult:
        """
        Invoke a PAI agent.

        Args:
            agent_name: Name of agent to invoke (e.g., "SCHEDULER")
            mission: Mission description
            context: Additional context for the mission
            additional_constraints: Extra constraints beyond identity card
            require_approval: Whether to require human approval
            parent_agent: Name of invoking agent (for spawn chain validation)

        Returns:
            AgentResult with execution results
        """
        invocation_id = uuid4()
        context = context or {}
        additional_constraints = additional_constraints or []
        execution_log: list[str] = []
        tools_used: list[str] = []
        escalations: list[dict[str, str]] = []

        timestamp = datetime.now().isoformat()
        execution_log.append(f"[{timestamp}] Invocation started: {agent_name}")

        try:
            # 1. Load identity card
            identity = await self.identity_loader.load(agent_name)
            if identity is None:
                execution_log.append(f"[{datetime.now().isoformat()}] ERROR: Identity card not found")
                return AgentResult(
                    agent_name=agent_name,
                    goal_id=str(invocation_id),
                    status="error",
                    result={"error": f"Identity card not found for {agent_name}"},
                    tools_used=[],
                    execution_log=execution_log,
                    escalations=[],
                    audit_trail_path="",
                )
            execution_log.append(f"[{datetime.now().isoformat()}] Identity loaded: {identity.role}")

            # 2. Validate spawn chain (if parent specified)
            if parent_agent:
                spawn_valid = await self.tool_validator.validate_spawn(
                    parent=parent_agent,
                    child=agent_name,
                    invocation_id=invocation_id,
                )
                if not spawn_valid:
                    execution_log.append(
                        f"[{datetime.now().isoformat()}] SPAWN VIOLATION: "
                        f"{parent_agent} cannot spawn {agent_name}"
                    )
                    return AgentResult(
                        agent_name=agent_name,
                        goal_id=str(invocation_id),
                        status="spawn_violation",
                        result={
                            "error": f"Spawn chain violation: {parent_agent} cannot spawn {agent_name}",
                            "suggested_parent": self._find_valid_parent(agent_name),
                        },
                        tools_used=[],
                        execution_log=execution_log,
                        escalations=[{
                            "type": "spawn_violation",
                            "details": f"{parent_agent} -> {agent_name}",
                        }],
                        audit_trail_path="",
                    )
                execution_log.append(
                    f"[{datetime.now().isoformat()}] Spawn chain validated: {parent_agent} -> {agent_name}"
                )

            # 3. Get allowed tools for this agent
            allowed_tools = await self.tool_validator.get_allowed_tools(agent_name)
            execution_log.append(f"[{datetime.now().isoformat()}] Allowed tools: {allowed_tools}")

            # 4. Build agent prompt
            prompt = self._build_prompt(
                identity=identity,
                mission=mission,
                context=context,
                additional_constraints=additional_constraints,
                allowed_tools=allowed_tools,
            )
            execution_log.append(
                f"[{datetime.now().isoformat()}] Prompt built ({len(prompt)} chars)"
            )

            # 5. Track invocation
            self.active_invocations[invocation_id] = {
                "agent_name": agent_name,
                "identity": identity,
                "allowed_tools": allowed_tools,
                "started_at": datetime.now(),
                "mission": mission,
            }

            # 6. Execute (in full implementation, calls AgentMCPServer)
            result = await self._execute_with_filtered_tools(
                invocation_id=invocation_id,
                identity=identity,
                prompt=prompt,
                allowed_tools=allowed_tools,
                context=context,
                require_approval=require_approval,
            )

            tools_used = result.get("tools_used", [])
            execution_log.extend(result.get("execution_log", []))

            # 7. Check for escalation triggers
            escalation_reason = self._check_escalation_triggers(
                identity=identity,
                result=result,
            )
            if escalation_reason:
                escalations.append({
                    "type": "escalation_trigger",
                    "target": identity.escalate_to,
                    "reason": escalation_reason,
                })
                execution_log.append(
                    f"[{datetime.now().isoformat()}] ESCALATION: {escalation_reason} -> {identity.escalate_to}"
                )

            # 8. Write audit trail
            audit_path = await self._write_audit_trail(
                invocation_id=invocation_id,
                agent_name=agent_name,
                identity=identity,
                mission=mission,
                context=context,
                result=result,
                tools_used=tools_used,
                execution_log=execution_log,
                escalations=escalations,
            )

            execution_log.append(f"[{datetime.now().isoformat()}] Invocation completed")

            return AgentResult(
                agent_name=agent_name,
                goal_id=str(invocation_id),
                status=result.get("status", "completed"),
                result=result.get("result", {}),
                tools_used=tools_used,
                execution_log=execution_log,
                escalations=escalations,
                audit_trail_path=str(audit_path),
            )

        except Exception as e:
            logger.exception(f"Error invoking agent {agent_name}")
            execution_log.append(f"[{datetime.now().isoformat()}] ERROR: {str(e)}")

            return AgentResult(
                agent_name=agent_name,
                goal_id=str(invocation_id),
                status="error",
                result={"error": str(e), "type": type(e).__name__},
                tools_used=tools_used,
                execution_log=execution_log,
                escalations=escalations,
                audit_trail_path="",
            )

        finally:
            # Cleanup
            if invocation_id in self.active_invocations:
                del self.active_invocations[invocation_id]

    def _build_prompt(
        self,
        identity: AgentIdentity,
        mission: str,
        context: dict[str, Any],
        additional_constraints: list[str],
        allowed_tools: list[str],
    ) -> str:
        """
        Build the full agent prompt with identity and mission.

        Args:
            identity: Agent identity card
            mission: Mission description
            context: Additional context
            additional_constraints: Extra constraints
            allowed_tools: List of allowed MCP tools

        Returns:
            Complete prompt string
        """
        # Format identity card as boot context
        identity_context = f"""# {identity.name} Identity Card

## Identity
- **Role:** {identity.role}
- **Tier:** {identity.tier}
- **Model:** {identity.model}

## Chain of Command
- **Reports To:** {identity.reports_to}
- **Can Spawn:** {', '.join(identity.can_spawn) if identity.can_spawn else 'None (terminal specialist)'}
- **Escalate To:** {identity.escalate_to}

## Standing Orders (Execute Without Asking)
{chr(10).join(f'{i+1}. {order}' for i, order in enumerate(identity.standing_orders))}

## Escalation Triggers (MUST Escalate)
{chr(10).join(f'- {trigger}' for trigger in identity.escalation_triggers)}

## Key Constraints
{chr(10).join(f'- {constraint}' for constraint in identity.constraints)}

## One-Line Charter
"{identity.charter}"
"""

        # Format context
        context_str = "\n".join(
            f"- **{k}:** {v}" for k, v in context.items()
        ) if context else "No additional context provided."

        # Format additional constraints
        constraints_str = "\n".join(
            f"- {c}" for c in additional_constraints
        ) if additional_constraints else "No additional constraints."

        # Format allowed tools
        tools_str = "\n".join(
            f"- `{tool}`" for tool in allowed_tools
        ) if allowed_tools else "No MCP tools available (advisory role)."

        # Build full prompt
        prompt = f"""## BOOT CONTEXT
{identity_context}

## MISSION
{mission}

## CONTEXT
{context_str}

## ADDITIONAL CONSTRAINTS
{constraints_str}

## AVAILABLE MCP TOOLS
You have access to ONLY the following MCP tools:
{tools_str}

**IMPORTANT:** Do NOT attempt to use tools not in this list. If you need a tool not available, escalate to {identity.escalate_to}.

## EXECUTION INSTRUCTIONS
1. Read and internalize your identity card above
2. Execute within your standing orders
3. Use only your authorized MCP tools listed above
4. Escalate immediately if you hit an escalation trigger
5. Maintain audit trail for all actions
6. Report results in structured format

Begin execution.
"""

        return prompt

    async def _execute_with_filtered_tools(
        self,
        invocation_id: UUID,
        identity: AgentIdentity,
        prompt: str,
        allowed_tools: list[str],
        context: dict[str, Any],
        require_approval: bool,
    ) -> dict[str, Any]:
        """
        Execute agent with filtered tool access.

        In full implementation, this:
        1. Calls AgentMCPServer.sample_llm() with the prompt
        2. Intercepts tool calls and validates against allowed_tools
        3. Routes allowed calls to MCP server
        4. Blocks disallowed calls with error messages
        5. Aggregates results

        Args:
            invocation_id: Unique invocation ID
            identity: Agent identity
            prompt: Full agent prompt
            allowed_tools: List of allowed tool names
            context: Execution context
            require_approval: Whether approval is required

        Returns:
            Execution result dictionary
        """
        # For now, return a structured result showing what would happen
        # In full implementation, integrate with AgentMCPServer

        execution_log = [
            f"Agent {identity.name} would execute with:",
            f"  - Model: {identity.model}",
            f"  - Tools: {len(allowed_tools)} available",
            f"  - Prompt length: {len(prompt)} chars",
        ]

        # Simulate result based on agent type
        result = self._simulate_agent_execution(identity, allowed_tools, context)

        return {
            "status": "completed" if not require_approval else "awaiting_approval",
            "result": result,
            "tools_used": [],  # Would be populated by actual execution
            "execution_log": execution_log,
        }

    def _simulate_agent_execution(
        self,
        identity: AgentIdentity,
        allowed_tools: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Simulate agent execution result based on agent type.

        This is a placeholder for actual LLM execution.

        Args:
            identity: Agent identity
            allowed_tools: Available tools
            context: Execution context

        Returns:
            Simulated result
        """
        agent_results = {
            "SCHEDULER": {
                "message": "Schedule generation completed",
                "schedule_id": context.get("schedule_id", "generated_schedule"),
                "acgme_compliant": True,
                "coverage_rate": 0.98,
            },
            "SWAP_MANAGER": {
                "message": "Swap analysis completed",
                "candidates_found": 5,
                "best_candidate_score": 0.92,
            },
            "COMPLIANCE_AUDITOR": {
                "message": "Compliance audit completed",
                "violations_found": 0,
                "compliance_score": 1.0,
            },
            "COORD_ENGINE": {
                "message": "Coordination completed",
                "specialists_dispatched": 3,
                "tasks_completed": 5,
            },
        }

        return agent_results.get(identity.name, {
            "message": f"Agent {identity.name} executed successfully",
            "identity_tier": identity.tier,
        })

    def _check_escalation_triggers(
        self,
        identity: AgentIdentity,
        result: dict[str, Any],
    ) -> str | None:
        """
        Check if result matches any escalation triggers.

        Args:
            identity: Agent identity with triggers
            result: Execution result

        Returns:
            Trigger reason if escalation needed, None otherwise
        """
        result_str = str(result).lower()

        for trigger in identity.escalation_triggers:
            trigger_lower = trigger.lower()

            # Check for common trigger patterns
            if "violation" in trigger_lower and "violation" in result_str:
                return trigger
            if "timeout" in trigger_lower and "timeout" in result_str:
                return trigger
            if "failure" in trigger_lower and ("error" in result_str or "failed" in result_str):
                return trigger
            if "conflict" in trigger_lower and "conflict" in result_str:
                return trigger
            if "exhaustion" in trigger_lower and ("exhausted" in result_str or "memory" in result_str):
                return trigger

        return None

    def _find_valid_parent(self, agent_name: str) -> str | None:
        """
        Find a valid parent for an agent based on spawn chains.

        Args:
            agent_name: Agent needing a parent

        Returns:
            Valid parent name or None
        """
        from .tool_validator import SPAWN_CHAINS

        for parent, children in SPAWN_CHAINS.items():
            if agent_name in children:
                return parent
        return None

    async def _write_audit_trail(
        self,
        invocation_id: UUID,
        agent_name: str,
        identity: AgentIdentity,
        mission: str,
        context: dict[str, Any],
        result: dict[str, Any],
        tools_used: list[str],
        execution_log: list[str],
        escalations: list[dict[str, str]],
    ) -> Path:
        """
        Write audit trail to JSON file.

        Args:
            invocation_id: Unique invocation ID
            agent_name: Agent name
            identity: Agent identity
            mission: Mission description
            context: Execution context
            result: Execution result
            tools_used: Tools that were used
            execution_log: Execution log entries
            escalations: Escalation events

        Returns:
            Path to audit trail file
        """
        # Ensure audit directory exists
        self.audit_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_file = self.audit_path / f"{agent_name}_{timestamp}_{invocation_id}.json"

        audit_record = {
            "invocation_id": str(invocation_id),
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "agent_tier": identity.tier,
            "agent_model": identity.model,
            "reports_to": identity.reports_to,
            "mission": mission,
            "context": context,
            "tools_available": await self.tool_validator.get_allowed_tools(agent_name),
            "tools_used": tools_used,
            "status": result.get("status"),
            "result_summary": result.get("result", {}),
            "escalations": escalations,
            "execution_log": execution_log,
            "constraints_enforced": identity.constraints,
            "standing_orders": identity.standing_orders,
        }

        audit_file.write_text(json.dumps(audit_record, indent=2, default=str))
        logger.info(f"Audit trail written: {audit_file}")

        return audit_file

    def get_active_invocations(self) -> dict[str, Any]:
        """Get summary of active invocations."""
        return {
            str(k): {
                "agent_name": v["agent_name"],
                "started_at": v["started_at"].isoformat(),
                "mission": v["mission"][:100] + "..." if len(v["mission"]) > 100 else v["mission"],
            }
            for k, v in self.active_invocations.items()
        }

    async def list_available_agents(self) -> list[dict[str, Any]]:
        """
        List all available PAI agents with their capabilities.

        Returns:
            List of agent capability summaries
        """
        agents = self.identity_loader.list_available_agents()
        summaries = []

        for agent_name in agents:
            identity = await self.identity_loader.load(agent_name)
            if identity:
                capabilities = self.tool_validator.get_agent_capabilities(agent_name)
                summaries.append({
                    "name": agent_name,
                    "role": identity.role,
                    "tier": identity.tier,
                    "model": identity.model,
                    "reports_to": identity.reports_to,
                    "tools_count": len(capabilities["allowed_tools"]),
                    "can_spawn_count": len(capabilities["can_spawn"]),
                    "is_terminal": capabilities["is_terminal"],
                })

        return summaries
