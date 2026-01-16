# Session Checkpoint: MCP Agent Spawning Implementation

**Date:** 2026-01-15
**Context Used:** 92% → 8% remaining
**Status:** In Progress

---

## What We Built Tonight

### 1. Hopfield Energy Landscape Visualization (DONE - PR #723)
- Single-file HTML with Three.js
- Military traffic-light colors (White/Green/Amber/Red/Black)
- Ball rolls toward attractors via gradient descent
- Fixed Z-axis bug where ball fell through floor
- Location: `frontend/public/hopfield-energy-landscape.html`

### 2. MCP Agent Spawning Tool (IN PROGRESS)
- `spawn_agent_tool` in `mcp-server/src/scheduler_mcp/server.py`
- Lines ~4925-5220

**Key Features Implemented:**
- Loads agent identity cards from `.claude/Identities/`
- Loads agent metadata from `.claude/agents.yaml` (54 agents)
- Injects RAG context based on mission
- Tier-based max_turns (Specialist=5, Coordinator=20, Deputy=50)
- Spawn chain validation (parent→child authority)
- Audit trail writing to `.claude/History/agent_invocations/`
- Checkpoint protocol for scratchpad continuity

**Still TODO:**
- [ ] Create spawn-agent skill for Claude Code
- [ ] Define scratchpad checkpoint protocol
- [ ] Add tests for spawn_agent_tool
- [ ] Consider merging with PR #724 governance patterns

---

## Key Files Modified

1. **`.claude/agents.yaml`** - NEW
   - 54 agents with metadata
   - Tiers: Deputy, Coordinator, Specialist, G-Staff, SOF, Special, Oversight
   - Each has: role, model, archetype, can_spawn, tools_access, max_turns

2. **`mcp-server/src/scheduler_mcp/server.py`** - MODIFIED
   - Added `spawn_agent_tool` MCP tool (~200 lines)
   - Factory pattern: returns AgentSpec for Claude Code to execute via Task()

3. **`frontend/public/hopfield-energy-landscape.html`** - NEW
   - 3D visualization of schedule stability
   - Military color scheme

---

## Architecture Decision: Claude Code Native Execution

**Rejected Option:** MCP server calls Claude API directly (needs API keys)

**Adopted Option:** MCP tool is a factory that:
1. Loads identity card
2. Queries RAG for context
3. Validates spawn chain
4. Returns AgentSpec

Claude Code then spawns via `Task(prompt=spec.full_prompt, ...)`

**Benefits:**
- No API keys in MCP server
- Full Claude Code capabilities for spawned agents
- Simpler infrastructure

---

## Parallel Work: PR #724

Web session created comprehensive `pai_bridge` package with:
- IdentityLoader
- ToolAccessValidator
- PAIAgentExecutor
- 50 tests

**Their blind spot:** Mock LLM execution (doesn't actually work)
**Our blind spot:** No tests, less structured

**Merge strategy:** Adopt their governance patterns, keep our execution model.

---

## Next Session Priorities

1. Create spawn-agent skill for Claude Code integration
2. Add tests for spawn_agent_tool
3. Review/merge PR #724 governance patterns
4. Test end-to-end agent spawning

---

## Code Locations

```
.claude/agents.yaml                    # Agent registry (54 agents)
mcp-server/src/scheduler_mcp/server.py # spawn_agent_tool at ~line 4925
.claude/Identities/*.identity.md       # 55 identity cards
.claude/History/agent_invocations/     # Audit trail directory
frontend/public/hopfield-energy-landscape.html  # Viz prototype
```

---

## Design Insight: Agents That Don't Think Are Just Tools

Tier-based execution model:
- **Specialist (haiku, 5 turns)**: Single-shot, focused task
- **Coordinator (sonnet, 20 turns)**: Bounded agentic loop, domain tools
- **Deputy (opus, 50 turns)**: Full autonomy, can spawn sub-agents

Execution model must match cognitive tier.
