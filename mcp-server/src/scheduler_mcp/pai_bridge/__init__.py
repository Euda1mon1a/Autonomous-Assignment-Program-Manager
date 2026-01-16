"""
PAI Agent MCP Bridge - Expose PAI agents as MCP tools.

This module enables PAI (Programmable AI) agents to be invoked as MCP tools,
bridging the governance framework (identity cards, spawn chains) with the
MCP tool execution system.

Key Components:
- IdentityLoader: Parses agent identity cards from .claude/Identities/
- ToolAccessValidator: Enforces identity-based tool access control
- PAIAgentExecutor: Executes agents with proper context and audit trails
- Agent Tools: MCP tool definitions for invoking PAI agents

Usage:
    from scheduler_mcp.pai_bridge import PAIAgentExecutor, register_pai_tools

    # Initialize executor
    executor = PAIAgentExecutor()

    # Register PAI agent tools with FastMCP server
    register_pai_tools(mcp_server)
"""

from .models import AgentIdentity, AgentResult, AgentInvocationRequest
from .identity_loader import IdentityLoader
from .tool_validator import ToolAccessValidator, AGENT_TOOL_MATRIX, SPAWN_CHAINS
from .executor import PAIAgentExecutor

__all__ = [
    "AgentIdentity",
    "AgentResult",
    "AgentInvocationRequest",
    "IdentityLoader",
    "ToolAccessValidator",
    "PAIAgentExecutor",
    "AGENT_TOOL_MATRIX",
    "SPAWN_CHAINS",
]
