# L3 Minimal Context Pattern

> **Purpose:** Codify minimum viable context for subagent MCP tool usage
> **Category:** `delegation_patterns`
> **Validated:** 2026-01-10 (parallel probe test)

---

## Overview

The L3 pattern represents the minimum viable context required for subagents to autonomously invoke MCP tools. Testing confirmed that agents can operate effectively with just mission intent and parameters, without explicit tool names or identity cards.

---

## The L3 Pattern

Subagents can autonomously invoke MCP tools with ONLY:

1. **Mission intent** - What to accomplish (1-2 sentences)
2. **Key parameters** - Dates, IDs, constraints
3. **Output format** - Expected response structure

**NOT required:**
- Identity card
- Explicit tool names
- Full context transfer
- Chain of command details

---

## Context Levels Comparison

| Level | Identity | Mission | Explicit Tools | Parameters | Use Case |
|-------|----------|---------|----------------|------------|----------|
| L1 | Yes | Yes | Yes | Yes | New agent, uncertain task |
| L2 | Yes | Yes | No | Yes | Known domain, some context |
| **L3** | No | Yes | No | Yes | **Clear mission, MCP available** |
| L4 | No | Minimal | No | No | Does not work reliably |

---

## When to Use L3

| Scenario | Use L3? | Reasoning |
|----------|---------|-----------|
| Clear mission, known domain | Yes | Agent can infer appropriate tools |
| MCP tools available for task | Yes | Tools discoverable from context |
| Agent has standing orders | Yes | Pre-authorized patterns apply |
| Uncertain requirements | No | Use L2 with identity card |
| Novel task, no tools | No | Use L1 with full context |
| Need specific tool sequence | No | Use L1 with explicit instructions |

---

## L3 Prompt Template

```markdown
## MISSION
[Clear objective in 1-2 sentences]
[Domain context if needed: "You are assessing a medical residency schedule"]

[Key parameters]
- Dates: [start] to [end]
- Target: [block/schedule/entity ID]
- Constraints: [any specific requirements]

## OUTPUT
[Expected JSON/markdown structure]
```

---

## Evidence: Test Results (2026-01-10)

### Test Design

Four parallel probes with decreasing context:
- L1: Identity card + explicit MCP tool names
- L2: Identity card + mission intent (no tool names)
- L3: Mission intent + parameters only
- L4: Just the question

### L3 Probe - What Was Sent

```
## MISSION
You are assessing a medical residency schedule.

Assess how the schedule for Block 10 (January 2026) looks.
Check for ACGME compliance and any scheduling issues.

Block 10 dates: 2026-01-06 to 2026-01-31

## OUTPUT
Report JSON:
{
  "level": "L3",
  "mcp_tools_invoked": ["<list of tools called, or empty if none>"],
  "schedule_status": "<your assessment>",
  "approach": "<what you did>"
}
```

### L3 Probe - What It Did

The agent autonomously invoked **3 MCP tools** without being told which to use:
- `validate_schedule_tool` - ACGME compliance check
- `detect_conflicts_tool` - Scheduling conflict detection
- `get_defense_level_tool` - Resilience assessment

### Results Summary

| Level | MCP Tools Invoked | Result |
|-------|-------------------|--------|
| L1 | Yes (1 tool) | Expected - explicit instructions |
| L2 | Yes (1 tool + RAG) | Exceeded expectations |
| **L3** | **Yes (3 tools)** | **Autonomously selected appropriate tools** |
| L4 | No | Fell back to file search |

---

## Why L3 Works

1. **Tool Discovery**: MCP tools are visible to agents via their tool definitions
2. **Semantic Understanding**: Mission intent provides enough context to select tools
3. **Domain Knowledge**: Agents understand ACGME, schedules, compliance from training
4. **Structured Output**: JSON format anchors agent behavior

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Over-contextualizing | 2000 tokens when 100 suffice | Use L3 for clear missions |
| Explicit tool mandates | Limits agent judgment | Let agent discover tools |
| Identity card cargo-cult | Overhead without benefit | Only include when needed |
| Missing parameters | Agent can't execute | Always include key parameters |

---

## Implementation Guidance

### For ORCHESTRATOR
```
Spawn SYNTHESIZER with:
- Mission: "Assess Block 10 operational readiness"
- Parameters: Block 10 dates, compliance requirements
- Output: Summary with recommendations
```

### For Deputies (ARCHITECT, SYNTHESIZER)
```
Spawn COORD_ENGINE with:
- Mission: "Validate schedule compliance"
- Parameters: Date range, constraint set
- Output: Compliance report
```

### For Coordinators
```
Spawn SCHEDULER with:
- Mission: "Run ACGME validation"
- Parameters: start_date, end_date
- Output: Validation result JSON
```

---

## Key Insight

> **Auftragstaktik works at L3.** Provide mission intent and parameters. Let agents decide which tools to use. This reduces token overhead by ~90% while maintaining effectiveness.

---

## Supporting Infrastructure

The L3 pattern works because of the **4-layer MCP enforcement mechanism** (commit f63e7049):

### Layer A: Documentation
- **`CLAUDE.md`** (lines 264-293) - MCP Tool Requirements section
- Defines MUST-USE tools for schedule work, domain questions, resilience changes

### Layer B: Skills with MCP Requirements
- **`.claude/skills/SCHEDULING/SKILL.md`** (lines 36-54) - Required tools for schedule generation
- **`.claude/skills/acgme-compliance/SKILL.md`** (lines 36-64) - Compliance validation workflow
- **`.claude/skills/swap-management/SKILL.md`** (lines 36-64) - Swap analysis requirements
- **`.claude/skills/startup/SKILL.md`** (lines 133-144) - Resilience check on session start

### Layer C: Hooks
- **`.claude/settings.json`** (lines 52-117) - Hook definitions
  - `enableAllProjectMcpServers: true` (line 136) - Activates all MCP tools
- **`.claude/hooks/pre-schedule-warning.sh`** - Warning before schedule edits

### Layer D: MCP Server Prompt Injection
- **`mcp-server/src/scheduler_mcp/server.py`** (lines 441-506)
  - `@mcp.prompt() tool_usage_requirements()` - Injects requirements into ALL LLM connections
  - 5 mandatory tool categories automatically available to subagents

### Key Configuration
```json
// .claude/settings.json
{
  "enableAllProjectMcpServers": true,  // Line 136 - critical for subagent access
  "hooks": [
    { "matcher": "Edit", "hooks": [{"command": ".claude/hooks/pre-schedule-warning.sh"}] }
  ]
}
```

### Related Documentation
- **`.claude/Governance/HIERARCHY.md`** - L3 Standing Order (lines 135-146)
- **`.claude/skills/CORE/delegation-patterns.md`** - L3 section (lines 21-58)
- **`.claude/skills/context-aware-delegation/SKILL.md`** - Context levels table (lines 57-99)
- **`docs/rag-knowledge/delegation-patterns.md`** - RAG-indexed L3 summary

---

*Document prepared for RAG ingestion*
*Category: `delegation_patterns`*
*Last validated: 2026-01-10*
