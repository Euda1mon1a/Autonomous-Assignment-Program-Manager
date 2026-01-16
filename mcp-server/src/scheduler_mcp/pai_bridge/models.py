"""
Data models for PAI Agent MCP Bridge.

This module defines the Pydantic models and dataclasses used throughout
the PAI bridge system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class AgentIdentity:
    """
    Parsed identity card for a PAI agent.

    Identity cards define:
    - WHO the agent is (role, tier, model)
    - WHAT it can do (standing orders, allowed tools)
    - WHAT it cannot do (constraints)
    - HOW it fits in the hierarchy (chain of command, spawn authority)
    """

    name: str
    """Agent name (e.g., 'SCHEDULER')"""

    role: str
    """Role description (e.g., 'Schedule generation specialist')"""

    tier: str
    """Authority tier: 'Deputy', 'Coordinator', 'Specialist', 'G-Staff'"""

    model: str
    """LLM model to use: 'opus', 'sonnet', 'haiku'"""

    reports_to: str
    """Parent agent in chain of command"""

    can_spawn: list[str] = field(default_factory=list)
    """Agents this one can spawn (empty for terminal specialists)"""

    escalate_to: str = ""
    """Target for escalation (usually same as reports_to)"""

    standing_orders: list[str] = field(default_factory=list)
    """Pre-authorized actions (execute without asking)"""

    escalation_triggers: list[str] = field(default_factory=list)
    """Conditions that MUST trigger escalation"""

    constraints: list[str] = field(default_factory=list)
    """Hard boundaries (what NOT to do)"""

    charter: str = ""
    """One-line mission philosophy"""

    raw_content: str = ""
    """Original markdown content of identity card"""


class AgentInvocationRequest(BaseModel):
    """Request to invoke a PAI agent via MCP."""

    mission: str = Field(..., description="Mission description for the agent")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the mission"
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Additional constraints beyond identity card"
    )
    require_approval: bool = Field(
        default=False,
        description="Whether to require human approval for actions"
    )
    parent_agent: str | None = Field(
        default=None,
        description="Parent agent invoking this one (for spawn chain validation)"
    )


class AgentResult(BaseModel):
    """Result from PAI agent invocation."""

    agent_name: str = Field(..., description="Name of the invoked agent")
    goal_id: str = Field(..., description="Unique invocation ID")
    status: str = Field(
        ...,
        description="Execution status: 'completed', 'escalated', 'failed', 'awaiting_approval'"
    )
    result: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent execution result"
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="MCP tools invoked during execution"
    )
    execution_log: list[str] = Field(
        default_factory=list,
        description="Timestamped execution log entries"
    )
    escalations: list[dict[str, str]] = Field(
        default_factory=list,
        description="Escalation events that occurred"
    )
    audit_trail_path: str = Field(
        default="",
        description="Path to JSON audit trail file"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "agent_name": "SCHEDULER",
                "goal_id": "abc123-def456",
                "status": "completed",
                "result": {
                    "schedule_id": "block_10_2025",
                    "assignments_created": 280,
                    "acgme_compliant": True,
                },
                "tools_used": ["validate_schedule", "generate_schedule"],
                "execution_log": [
                    "[2026-01-16T10:00:00] Invocation started: SCHEDULER",
                    "[2026-01-16T10:00:01] Identity loaded: Schedule generation specialist",
                    "[2026-01-16T10:00:30] Invocation completed",
                ],
                "escalations": [],
                "audit_trail_path": ".claude/History/agent_invocations/SCHEDULER_20260116_100000_abc123.json",
            }
        }


@dataclass
class ToolAccessRecord:
    """Record of a tool access attempt (for audit)."""

    timestamp: datetime
    agent_name: str
    agent_tier: str
    tool_name: str
    allowed: bool
    reason: str
    invocation_id: UUID


@dataclass
class SpawnRecord:
    """Record of an agent spawn attempt (for audit)."""

    timestamp: datetime
    parent_agent: str
    child_agent: str
    allowed: bool
    reason: str
    invocation_id: UUID


class EscalationEvent(BaseModel):
    """An escalation event during agent execution."""

    timestamp: str
    agent_name: str
    escalate_to: str
    trigger: str
    context: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # "pending", "routed", "resolved"
