# MCP Subagent Inheritance Pattern

> **Session:** 039
> **Date:** 2026-01-01
> **Category:** MCP Architecture
> **Importance:** CRITICAL

## Core Discovery

Claude Code subagents inherit MCP tools automatically when spawned. They do NOT need to request ORCHESTRATOR to execute MCP operations.

## Correct Pattern

```xml
<!-- Direct tool invocation - subagents have direct access -->
<invoke name="mcp__rag_search">
  <parameter name="query">ACGME compliance constraints</parameter>
  <parameter name="top_k">5</parameter>
</invoke>
```

## Wrong Pattern (Fixed in Session 039)

```
"ORCHESTRATOR: Please execute MCP tool [tool_name] with parameters..."
```

This pattern was INCORRECT - subagents have direct access to inherited MCP tools.

## Architecture Summary

| Component | Description |
|-----------|-------------|
| Main Thread | Has all MCP tools configured via `claude mcp add` |
| Subagents | Inherit full MCP tool suite automatically (if tools field omitted) |
| Context | Subagents have isolated context but shared MCP access |
| Enterprise | `managed-mcp.json` controls available servers for all subagents |

## Source

Based on Perplexity research confirming Claude Code architecture documentation:
- Subagents inherit MCP tools by default
- Use `mcp__` prefixed tools directly
- Skill tool available for complex multi-tool workflows

## Impact

21 agent specs updated with correct direct access pattern in commit `02c556a2`.

## For Complex Workflows

Use Skill tool with `skill="MCP_ORCHESTRATION"` for multi-tool chains.

---

*Ingested to `.claude/dontreadme/` as fallback. Queue for pgvector ingestion when MCP server available.*
