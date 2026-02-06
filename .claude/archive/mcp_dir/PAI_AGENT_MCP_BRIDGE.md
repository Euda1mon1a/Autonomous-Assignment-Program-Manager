# PAI Agent MCP Bridge Architecture

> **Purpose:** Enable PAI agents (SCHEDULER, SWAP_MANAGER, etc.) to be invoked as MCP tools
> **Status:** Design Document
> **Created:** 2026-01-16

---

## Executive Summary

This document describes the architecture for exposing PAI (Programmable AI) agents as Model Context Protocol (MCP) tools. This enables:

1. **External Systems** can invoke specialized agents via MCP protocol
2. **Agent Orchestration** can chain agent invocations like tool calls
3. **Context Isolation** - each agent invocation is self-contained
4. **Governance Enforcement** - identity cards control tool access
5. **Audit Trails** - all agent invocations are logged

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MCP Client (Claude Code, IDE, etc.)             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ MCP Protocol
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastMCP Server                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PAI Agent Bridge Tools                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │   │
│  │  │ invoke_scheduler│  │invoke_swap_mgr │  │ invoke_coord_ │ │   │
│  │  │     _agent      │  │    _agent      │  │  engine_agent │ │   │
│  │  └────────┬────────┘  └────────┬───────┘  └───────┬───────┘ │   │
│  └───────────┼────────────────────┼──────────────────┼─────────┘   │
│              │                    │                  │              │
│              ▼                    ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PAI Agent Executor                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │
│  │  │  Identity   │  │ Tool Access │  │  Agent Runtime      │   │   │
│  │  │   Loader    │  │  Validator  │  │    Manager          │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│              │                    │                  │              │
│              ▼                    ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Governance Layer                                             │   │
│  │  ├── Identity Cards (.claude/Identities/)                     │   │
│  │  ├── Spawn Chains (.claude/Governance/SPAWN_CHAINS.md)        │   │
│  │  ├── Tool Matrix (.claude/AGENT_MCP_MATRIX.md)                │   │
│  │  └── Capabilities (.claude/Governance/CAPABILITIES.md)        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│              │                    │                  │              │
│              ▼                    ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Existing MCP Tools (34+)                                     │   │
│  │  validate_schedule, generate_schedule, detect_conflicts, ...  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Identity Loader

**Purpose:** Load and parse agent identity cards from `.claude/Identities/`

```python
@dataclass
class AgentIdentity:
    """Parsed identity card for a PAI agent."""

    name: str                          # e.g., "SCHEDULER"
    role: str                          # e.g., "Schedule generation specialist"
    tier: str                          # "Deputy", "Coordinator", "Specialist"
    model: str                         # "opus", "sonnet", "haiku"
    reports_to: str                    # Parent agent
    can_spawn: list[str]               # Agents this one can spawn
    escalate_to: str                   # Escalation target
    standing_orders: list[str]         # Pre-authorized actions
    escalation_triggers: list[str]     # When to escalate
    constraints: list[str]             # What NOT to do
    charter: str                       # One-line philosophy
    allowed_tools: list[str]           # MCP tools accessible (derived)
```

### 2. Tool Access Validator

**Purpose:** Enforce identity-based access control for MCP tools

```python
class ToolAccessValidator:
    """Validates tool access based on agent identity."""

    def can_access_tool(self, agent: AgentIdentity, tool_name: str) -> bool:
        """Check if agent is authorized to use this tool."""

    def validate_preconditions(self, agent: AgentIdentity, tool_name: str, context: dict) -> bool:
        """Check tool-specific preconditions (backup, validation, etc.)."""

    def log_access_attempt(self, agent: AgentIdentity, tool_name: str, allowed: bool) -> None:
        """Audit trail for all access attempts."""
```

### 3. Agent Runtime Manager

**Purpose:** Execute PAI agents with proper context and tool access

```python
class AgentRuntimeManager:
    """Manages PAI agent execution lifecycle."""

    async def invoke_agent(
        self,
        agent_name: str,
        mission: str,
        context: dict,
        parent_agent: str | None = None
    ) -> AgentResult:
        """Invoke a PAI agent with mission and context."""

    async def build_agent_prompt(self, identity: AgentIdentity, mission: str, context: dict) -> str:
        """Build the full prompt including identity card."""

    async def execute_with_tools(self, identity: AgentIdentity, prompt: str, tools: list[str]) -> str:
        """Execute agent with restricted tool access."""
```

---

## Data Flow

### Invocation Flow

```
1. MCP Client calls: invoke_scheduler_agent(mission="Generate Block 10 schedule")
                                    │
                                    ▼
2. PAI Agent Bridge receives request
   └── Validates caller authorization
   └── Creates execution context (correlation_id, timestamp)
                                    │
                                    ▼
3. Identity Loader loads: .claude/Identities/SCHEDULER.identity.md
   └── Parses identity card
   └── Resolves allowed tools from AGENT_MCP_MATRIX.md
                                    │
                                    ▼
4. Tool Access Validator checks:
   └── Is caller authorized to spawn SCHEDULER?
   └── What MCP tools can SCHEDULER access?
   └── Are preconditions met (backup, etc.)?
                                    │
                                    ▼
5. Agent Runtime Manager builds prompt:
   └── Identity card as boot context
   └── Mission description
   └── Relevant context from caller
   └── Available tools list
                                    │
                                    ▼
6. LLM Sampling (Claude API):
   └── Streaming response with tool use
   └── Tool calls routed to MCP Server
   └── Tool access validated per-call
                                    │
                                    ▼
7. Result aggregation:
   └── Collect tool outputs
   └── Format structured result
   └── Log audit trail
                                    │
                                    ▼
8. Return AgentResult to MCP Client
```

### Tool Call Flow (Within Agent Execution)

```
Agent Runtime → Tool Request → Tool Access Validator
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                    ALLOWED                    DENIED
                          │                       │
                          ▼                       ▼
              Execute MCP Tool           Log Violation
                          │               Return Error
                          │
                          ▼
              Return Tool Result
```

---

## Implementation

### PAI Agent as MCP Tool (Tool Definition)

```python
# mcp-server/src/scheduler_mcp/pai_bridge/agent_tools.py

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any
from .executor import PAIAgentExecutor

mcp = FastMCP("PAI Agent Bridge")

class AgentInvocationRequest(BaseModel):
    """Request to invoke a PAI agent."""

    mission: str = Field(..., description="Mission description for the agent")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    constraints: list[str] = Field(default_factory=list, description="Additional constraints")
    require_approval: bool = Field(default=False, description="Require human approval for actions")

class AgentInvocationResult(BaseModel):
    """Result from PAI agent invocation."""

    agent_name: str
    goal_id: str
    status: str  # "completed", "escalated", "failed", "awaiting_approval"
    result: dict[str, Any]
    tools_used: list[str]
    execution_log: list[str]
    escalations: list[dict[str, str]]
    audit_trail_path: str

# Initialize executor
executor = PAIAgentExecutor()

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

    MCP Tools Available to SCHEDULER:
    - validate_schedule
    - generate_schedule
    - detect_conflicts
    - analyze_swap_candidates
    - execute_swap

    Args:
        mission: What the scheduler should accomplish
        context: Additional context (dates, constraints, preferences)
        constraints: Additional constraints beyond identity card
        require_approval: Whether to pause for human approval

    Returns:
        AgentInvocationResult with schedule generation results
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
    require_approval: bool = True,  # Swaps default to requiring approval
) -> dict:
    """
    Invoke the SWAP_MANAGER specialist agent.

    The SWAP_MANAGER handles schedule swap requests with safety checks,
    constraint validation, and audit trails.

    MCP Tools Available to SWAP_MANAGER:
    - analyze_swap_candidates
    - validate_schedule
    - execute_swap
    - detect_conflicts

    Args:
        mission: What swap operation to perform
        context: Swap details (requester, assignment, preferences)
        constraints: Additional constraints
        require_approval: Whether to require human approval (default: True)

    Returns:
        AgentInvocationResult with swap analysis/execution results
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

    MCP Tools Available to COMPLIANCE_AUDITOR:
    - validate_schedule
    - detect_conflicts
    - check_work_hours (via rag_search)
    - check_supervision_ratio (via rag_search)

    Args:
        mission: What compliance check to perform
        context: Schedule IDs, date ranges, specific rules to check
        audit_scope: "full", "acgme_only", "institutional_only"

    Returns:
        AgentInvocationResult with compliance audit results
    """
    result = await executor.invoke(
        agent_name="COMPLIANCE_AUDITOR",
        mission=mission,
        context={**(context or {}), "audit_scope": audit_scope},
        additional_constraints=[],
        require_approval=False,  # Audits don't modify data
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

    Coordinators (COORD_ENGINE, COORD_PLATFORM, etc.) manage specialists
    and can spawn multiple sub-agents to accomplish complex tasks.

    Valid Coordinators:
    - COORD_ENGINE: Scheduling engine and optimization
    - COORD_PLATFORM: Backend, database, API
    - COORD_QUALITY: Testing, code review
    - COORD_FRONTEND: UI/UX development
    - COORD_OPS: Releases, documentation, CI/CD
    - COORD_RESILIENCE: Resilience engineering, compliance

    Args:
        coordinator_name: Which coordinator to invoke
        mission: What the coordinator should accomplish
        context: Additional context for the mission
        spawn_specialists: Whether coordinator can spawn specialist agents

    Returns:
        AgentInvocationResult with coordinated task results
    """
    valid_coordinators = [
        "COORD_ENGINE", "COORD_PLATFORM", "COORD_QUALITY",
        "COORD_FRONTEND", "COORD_OPS", "COORD_RESILIENCE"
    ]

    if coordinator_name not in valid_coordinators:
        return {
            "status": "error",
            "error": f"Invalid coordinator: {coordinator_name}. Valid: {valid_coordinators}"
        }

    result = await executor.invoke(
        agent_name=coordinator_name,
        mission=mission,
        context={**(context or {}), "spawn_specialists": spawn_specialists},
        additional_constraints=[],
        require_approval=False,
    )
    return result.model_dump()
```

### PAI Agent Executor (Core Runtime)

```python
# mcp-server/src/scheduler_mcp/pai_bridge/executor.py

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel

from .identity_loader import IdentityLoader, AgentIdentity
from .tool_validator import ToolAccessValidator
from ..agent_server import AgentMCPServer

logger = logging.getLogger(__name__)

class AgentResult(BaseModel):
    """Result from PAI agent execution."""

    agent_name: str
    goal_id: str
    status: str
    result: dict[str, Any]
    tools_used: list[str]
    execution_log: list[str]
    escalations: list[dict[str, str]]
    audit_trail_path: str

class PAIAgentExecutor:
    """
    Executes PAI agents with identity-based tool access control.

    Bridges PAI governance (identity cards, spawn chains) with
    MCP tool execution (agent_server, tool registry).
    """

    def __init__(
        self,
        identities_path: Path | None = None,
        matrix_path: Path | None = None,
    ):
        """
        Initialize the executor.

        Args:
            identities_path: Path to .claude/Identities/
            matrix_path: Path to AGENT_MCP_MATRIX.md
        """
        self.identities_path = identities_path or Path(".claude/Identities")
        self.matrix_path = matrix_path or Path(".claude/AGENT_MCP_MATRIX.md")

        self.identity_loader = IdentityLoader(self.identities_path)
        self.tool_validator = ToolAccessValidator(self.matrix_path)
        self.agent_server = AgentMCPServer()

        # Track active invocations
        self.active_invocations: dict[UUID, dict] = {}

        logger.info("PAIAgentExecutor initialized")

    async def invoke(
        self,
        agent_name: str,
        mission: str,
        context: dict[str, Any],
        additional_constraints: list[str],
        require_approval: bool = False,
        parent_agent: str | None = None,
    ) -> AgentResult:
        """
        Invoke a PAI agent.

        Args:
            agent_name: Name of agent to invoke (e.g., "SCHEDULER")
            mission: Mission description
            context: Additional context
            additional_constraints: Extra constraints beyond identity card
            require_approval: Whether to require human approval
            parent_agent: Name of invoking agent (for spawn chain validation)

        Returns:
            AgentResult with execution results
        """
        invocation_id = uuid4()
        execution_log = []
        tools_used = []
        escalations = []

        execution_log.append(f"[{datetime.now().isoformat()}] Invocation started: {agent_name}")

        try:
            # 1. Load identity card
            identity = await self.identity_loader.load(agent_name)
            if identity is None:
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
            execution_log.append(f"Identity loaded: {identity.role}")

            # 2. Validate spawn chain (if parent specified)
            if parent_agent:
                spawn_valid = await self.tool_validator.validate_spawn(
                    parent=parent_agent,
                    child=agent_name,
                )
                if not spawn_valid:
                    execution_log.append(f"SPAWN VIOLATION: {parent_agent} cannot spawn {agent_name}")
                    return AgentResult(
                        agent_name=agent_name,
                        goal_id=str(invocation_id),
                        status="spawn_violation",
                        result={"error": f"Spawn chain violation: {parent_agent} cannot spawn {agent_name}"},
                        tools_used=[],
                        execution_log=execution_log,
                        escalations=[{"type": "spawn_violation", "details": f"{parent_agent} → {agent_name}"}],
                        audit_trail_path="",
                    )

            # 3. Get allowed tools for this agent
            allowed_tools = await self.tool_validator.get_allowed_tools(agent_name)
            execution_log.append(f"Allowed tools: {allowed_tools}")

            # 4. Build agent prompt
            prompt = self._build_prompt(identity, mission, context, additional_constraints)

            # 5. Track invocation
            self.active_invocations[invocation_id] = {
                "agent_name": agent_name,
                "identity": identity,
                "allowed_tools": allowed_tools,
                "started_at": datetime.now(),
                "mission": mission,
            }

            # 6. Execute via AgentMCPServer with tool filtering
            result = await self._execute_with_filtered_tools(
                invocation_id=invocation_id,
                identity=identity,
                prompt=prompt,
                allowed_tools=allowed_tools,
                require_approval=require_approval,
            )

            tools_used = result.get("tools_used", [])
            execution_log.extend(result.get("execution_log", []))

            # 7. Check for escalation triggers
            escalation_needed = self._check_escalation_triggers(
                identity=identity,
                result=result,
            )
            if escalation_needed:
                escalations.append({
                    "type": "escalation_trigger",
                    "target": identity.escalate_to,
                    "reason": escalation_needed,
                })
                execution_log.append(f"ESCALATION: {escalation_needed} → {identity.escalate_to}")

            # 8. Write audit trail
            audit_path = await self._write_audit_trail(
                invocation_id=invocation_id,
                agent_name=agent_name,
                identity=identity,
                mission=mission,
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
    ) -> str:
        """Build the full agent prompt with identity and mission."""

        # Format identity card as boot context
        identity_context = f"""# {identity.name} Identity Card

## Identity
- **Role:** {identity.role}
- **Tier:** {identity.tier}
- **Model:** {identity.model}

## Chain of Command
- **Reports To:** {identity.reports_to}
- **Can Spawn:** {', '.join(identity.can_spawn) if identity.can_spawn else 'None (terminal)'}
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
        context_str = "\n".join(f"- **{k}:** {v}" for k, v in context.items()) if context else "No additional context provided."

        # Format additional constraints
        constraints_str = "\n".join(f"- {c}" for c in additional_constraints) if additional_constraints else "No additional constraints."

        # Build full prompt
        prompt = f"""## BOOT CONTEXT
{identity_context}

## MISSION
{mission}

## CONTEXT
{context_str}

## ADDITIONAL CONSTRAINTS
{constraints_str}

## EXECUTION INSTRUCTIONS
1. Read and internalize your identity card above
2. Execute within your standing orders
3. Use only your authorized MCP tools
4. Escalate immediately if you hit an escalation trigger
5. Maintain audit trail for all actions
6. Report results in structured format
"""

        return prompt

    async def _execute_with_filtered_tools(
        self,
        invocation_id: UUID,
        identity: AgentIdentity,
        prompt: str,
        allowed_tools: list[str],
        require_approval: bool,
    ) -> dict[str, Any]:
        """
        Execute agent with filtered tool access.

        Uses AgentMCPServer but intercepts tool calls to enforce
        identity-based access control.
        """
        # This would integrate with the AgentMCPServer's LLM sampling
        # and tool execution, filtering tool calls through the validator

        # For now, return simulated result structure
        # In full implementation, this calls agent_server.sample_llm()
        # with a tool call interceptor

        return {
            "status": "completed",
            "result": {
                "message": f"Agent {identity.name} executed mission successfully",
                "identity_tier": identity.tier,
            },
            "tools_used": [],
            "execution_log": [
                f"Prompt built with {len(prompt)} characters",
                f"Tools available: {allowed_tools}",
            ],
        }

    def _check_escalation_triggers(
        self,
        identity: AgentIdentity,
        result: dict[str, Any],
    ) -> str | None:
        """Check if result matches any escalation triggers."""

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

        return None

    async def _write_audit_trail(
        self,
        invocation_id: UUID,
        agent_name: str,
        identity: AgentIdentity,
        mission: str,
        result: dict[str, Any],
        tools_used: list[str],
        execution_log: list[str],
        escalations: list[dict[str, str]],
    ) -> Path:
        """Write audit trail to structured log file."""

        import json

        audit_dir = Path(".claude/History/agent_invocations")
        audit_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_path = audit_dir / f"{agent_name}_{timestamp}_{invocation_id}.json"

        audit_record = {
            "invocation_id": str(invocation_id),
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "agent_tier": identity.tier,
            "reports_to": identity.reports_to,
            "mission": mission,
            "tools_used": tools_used,
            "tools_available": await self.tool_validator.get_allowed_tools(agent_name),
            "status": result.get("status"),
            "escalations": escalations,
            "execution_log": execution_log,
            "constraints_enforced": identity.constraints,
        }

        audit_path.write_text(json.dumps(audit_record, indent=2, default=str))
        logger.info(f"Audit trail written: {audit_path}")

        return audit_path
```

### Identity Loader

```python
# mcp-server/src/scheduler_mcp/pai_bridge/identity_loader.py

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class AgentIdentity:
    """Parsed identity card for a PAI agent."""

    name: str
    role: str
    tier: str
    model: str
    reports_to: str
    can_spawn: list[str]
    escalate_to: str
    standing_orders: list[str]
    escalation_triggers: list[str]
    constraints: list[str]
    charter: str
    raw_content: str

class IdentityLoader:
    """Loads and parses PAI agent identity cards."""

    def __init__(self, identities_path: Path):
        """
        Initialize the loader.

        Args:
            identities_path: Path to .claude/Identities/
        """
        self.identities_path = identities_path
        self._cache: dict[str, AgentIdentity] = {}

    async def load(self, agent_name: str) -> AgentIdentity | None:
        """
        Load identity card for an agent.

        Args:
            agent_name: Agent name (e.g., "SCHEDULER")

        Returns:
            Parsed AgentIdentity or None if not found
        """
        # Check cache
        if agent_name in self._cache:
            return self._cache[agent_name]

        # Find identity file
        identity_file = self.identities_path / f"{agent_name}.identity.md"
        if not identity_file.exists():
            logger.warning(f"Identity file not found: {identity_file}")
            return None

        # Parse identity
        try:
            content = identity_file.read_text()
            identity = self._parse_identity(agent_name, content)
            self._cache[agent_name] = identity
            return identity
        except Exception as e:
            logger.error(f"Error parsing identity for {agent_name}: {e}")
            return None

    def _parse_identity(self, name: str, content: str) -> AgentIdentity:
        """Parse identity card markdown into AgentIdentity."""

        # Extract sections using regex
        role = self._extract_field(content, r"\*\*Role:\*\*\s*(.+)")
        tier = self._extract_field(content, r"\*\*Tier:\*\*\s*(\w+)")
        model = self._extract_field(content, r"\*\*Model:\*\*\s*(\w+)")
        reports_to = self._extract_field(content, r"\*\*Reports To:\*\*\s*(\w+)")
        escalate_to = self._extract_field(content, r"\*\*Escalate To:\*\*\s*(\w+)")

        # Parse Can Spawn (could be "None (terminal)" or list)
        can_spawn_raw = self._extract_field(content, r"\*\*Can Spawn:\*\*\s*(.+)")
        if "None" in can_spawn_raw or "terminal" in can_spawn_raw.lower():
            can_spawn = []
        else:
            can_spawn = [s.strip() for s in can_spawn_raw.split(",")]

        # Extract list sections
        standing_orders = self._extract_list(content, r"## Standing Orders.*?\n((?:\d+\..+\n?)+)")
        escalation_triggers = self._extract_list(content, r"## Escalation Triggers.*?\n((?:-.+\n?)+)")
        constraints = self._extract_list(content, r"## Key Constraints.*?\n((?:-.+\n?)+)")

        # Extract charter
        charter_match = re.search(r'## One-Line Charter\s*\n"(.+)"', content)
        charter = charter_match.group(1) if charter_match else ""

        return AgentIdentity(
            name=name,
            role=role,
            tier=tier,
            model=model,
            reports_to=reports_to,
            can_spawn=can_spawn,
            escalate_to=escalate_to,
            standing_orders=standing_orders,
            escalation_triggers=escalation_triggers,
            constraints=constraints,
            charter=charter,
            raw_content=content,
        )

    def _extract_field(self, content: str, pattern: str) -> str:
        """Extract a single field using regex."""
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    def _extract_list(self, content: str, pattern: str) -> list[str]:
        """Extract a list section using regex."""
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        items_text = match.group(1)
        # Parse numbered list (1. item) or bullet list (- item)
        items = re.findall(r"(?:\d+\.\s*|-\s*)(.+)", items_text)
        return [item.strip() for item in items]
```

### Tool Access Validator

```python
# mcp-server/src/scheduler_mcp/pai_bridge/tool_validator.py

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Tool-to-Agent mapping (derived from AGENT_MCP_MATRIX.md)
AGENT_TOOL_MATRIX = {
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
    ],
    "OPTIMIZATION_SPECIALIST": [
        "generate_schedule",
        "validate_schedule",
        "analyze_hub_centrality",
    ],
    "COMPLIANCE_AUDITOR": [
        "validate_schedule",
        "detect_conflicts",
        "rag_search",  # For policy lookups
    ],
    "RESILIENCE_ENGINEER": [
        "check_utilization_threshold",
        "run_contingency_analysis",
        "get_defense_level",
        "analyze_hub_centrality",
        "get_static_fallbacks",
        "execute_sacrifice_hierarchy",
    ],
    "G5_PLANNING": [
        "validate_schedule",
        "run_contingency_analysis",
        "rag_search",
    ],
}

# Spawn chain validation (who can spawn whom)
SPAWN_CHAINS = {
    "ORCHESTRATOR": ["ARCHITECT", "SYNTHESIZER"],
    "ARCHITECT": ["COORD_PLATFORM", "COORD_QUALITY", "COORD_ENGINE", "COORD_TOOLING"],
    "SYNTHESIZER": ["COORD_OPS", "COORD_RESILIENCE", "COORD_FRONTEND", "COORD_INTEL"],
    "COORD_ENGINE": ["SCHEDULER", "SWAP_MANAGER", "OPTIMIZATION_SPECIALIST"],
    "COORD_RESILIENCE": ["RESILIENCE_ENGINEER", "COMPLIANCE_AUDITOR"],
    "COORD_QUALITY": ["QA_TESTER", "CODE_REVIEWER"],
    # Terminal agents cannot spawn
    "SCHEDULER": [],
    "SWAP_MANAGER": [],
    "COMPLIANCE_AUDITOR": [],
}

class ToolAccessValidator:
    """Validates tool access based on agent identity."""

    def __init__(self, matrix_path: Path | None = None):
        """
        Initialize the validator.

        Args:
            matrix_path: Path to AGENT_MCP_MATRIX.md (optional)
        """
        self.matrix_path = matrix_path
        # In full implementation, this would parse the matrix file
        # For now, use hardcoded mapping
        self.agent_tools = AGENT_TOOL_MATRIX
        self.spawn_chains = SPAWN_CHAINS

    async def get_allowed_tools(self, agent_name: str) -> list[str]:
        """Get list of MCP tools allowed for an agent."""
        return self.agent_tools.get(agent_name, [])

    async def can_access_tool(self, agent_name: str, tool_name: str) -> bool:
        """Check if agent can access a specific tool."""
        allowed = self.agent_tools.get(agent_name, [])
        return tool_name in allowed

    async def validate_spawn(self, parent: str, child: str) -> bool:
        """Validate that parent can spawn child agent."""
        allowed_children = self.spawn_chains.get(parent, [])
        return child in allowed_children

    def log_access_attempt(
        self,
        agent_name: str,
        tool_name: str,
        allowed: bool,
        reason: str = "",
    ) -> None:
        """Log tool access attempt for audit."""
        status = "ALLOWED" if allowed else "DENIED"
        logger.info(
            f"Tool access {status}: {agent_name} -> {tool_name}",
            extra={
                "agent": agent_name,
                "tool": tool_name,
                "allowed": allowed,
                "reason": reason,
            }
        )
```

---

## Usage Examples

### Example 1: Invoke Scheduler from External System

```python
# External system invokes SCHEDULER via MCP
result = await mcp_client.call_tool(
    "invoke_scheduler_agent",
    mission="Generate a 4-week schedule for Block 10 (Feb 3 - Mar 2, 2025)",
    context={
        "block_number": 10,
        "start_date": "2025-02-03",
        "end_date": "2025-03-02",
        "residents_count": 12,
        "faculty_count": 8,
    },
    constraints=[
        "Prioritize Night Float coverage",
        "Minimize weekend assignments for PGY-3s",
    ],
    require_approval=False,
)

# Result:
# {
#     "agent_name": "SCHEDULER",
#     "goal_id": "abc123...",
#     "status": "completed",
#     "result": {
#         "schedule_id": "block_10_2025",
#         "assignments_created": 280,
#         "acgme_compliant": True,
#         "coverage_rate": 0.98,
#     },
#     "tools_used": ["validate_schedule", "generate_schedule", "detect_conflicts"],
#     "execution_log": [...],
#     "audit_trail_path": ".claude/History/agent_invocations/SCHEDULER_20260116_..."
# }
```

### Example 2: Coordinator Spawning Specialists

```python
# COORD_ENGINE invokes SCHEDULER as subagent
result = await mcp_client.call_tool(
    "invoke_coordinator_agent",
    coordinator_name="COORD_ENGINE",
    mission="Optimize coverage for Q1 2025 with emphasis on call equity",
    context={
        "quarter": "Q1",
        "year": 2025,
        "optimization_goal": "call_equity",
    },
    spawn_specialists=True,  # Allow spawning SCHEDULER, SWAP_MANAGER, etc.
)

# Internally, COORD_ENGINE may spawn:
# - SCHEDULER for initial schedule generation
# - OPTIMIZATION_SPECIALIST for equity analysis
# - SWAP_MANAGER for rebalancing swaps
```

### Example 3: Compliance Audit

```python
# Invoke COMPLIANCE_AUDITOR for regulatory check
result = await mcp_client.call_tool(
    "invoke_compliance_auditor_agent",
    mission="Audit Block 10 schedule for ACGME violations before deployment",
    context={
        "schedule_id": "block_10_2025",
        "check_rules": ["80_hour", "1_in_7", "supervision_ratio"],
    },
    audit_scope="acgme_only",
)

# Result includes violations, recommendations, and compliance score
```

---

## Security Considerations

### 1. Tool Access Control

- **Whitelist enforcement:** Agents can only call tools in their identity card
- **Precondition validation:** Tools like `execute_swap` require backup verification
- **Rate limiting:** Agents have per-tool rate limits (configurable in identity)

### 2. Spawn Chain Enforcement

- **Hierarchical validation:** Spawn requests validated against SPAWN_CHAINS
- **Violation logging:** Invalid spawn attempts logged for IG audit
- **Escalation routing:** Invalid spawns routed to proper parent

### 3. Audit Trails

- **All invocations logged:** JSON audit files with full context
- **Tool usage tracking:** Every tool call recorded with agent identity
- **Escalation history:** All escalations captured for review

### 4. Data Protection

- **No PII in logs:** Agent invocations sanitize sensitive data
- **Context isolation:** Each invocation is self-contained
- **Credential handling:** No credentials passed through agent prompts

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (This PR)
- [ ] Identity Loader implementation
- [ ] Tool Access Validator implementation
- [ ] PAI Agent Executor implementation
- [ ] Basic agent tools (SCHEDULER, SWAP_MANAGER, COMPLIANCE_AUDITOR)

### Phase 2: Full Integration
- [ ] Integration with AgentMCPServer's LLM sampling
- [ ] Tool call interception for access control
- [ ] Real-time escalation routing

### Phase 3: Advanced Features
- [ ] Multi-agent orchestration (coordinator spawning specialists)
- [ ] Human-in-the-loop approval workflows
- [ ] Rate limiting and quota management

### Phase 4: Monitoring & Observability
- [ ] Prometheus metrics for agent invocations
- [ ] Grafana dashboards for agent health
- [ ] Alerting on constraint violations

---

## References

- `.claude/Identities/` - Agent identity cards
- `.claude/AGENT_MCP_MATRIX.md` - Agent-to-tool mapping
- `.claude/Governance/SPAWN_CHAINS.md` - Spawn authority matrix
- `mcp-server/src/scheduler_mcp/agent_server.py` - AgentMCPServer implementation
- `mcp-server/src/scheduler_mcp/tools/base.py` - Base tool abstraction
