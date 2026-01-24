# Session 138: Subagent Spawning Architecture Discovery

**Date:** 2026-01-23
**Branch:** `feature/rotation-faculty-templates`
**Status:** COMPLETE

---

## Critical Discovery

**Subagents spawned via Task() do NOT have Task() available.**

This was discovered while investigating why the 10x10 mypy force structure (Session 137) failed. The PAI governance system was designed with the assumption that Task() would propagate to subagents - it does not.

---

## Test Results

### Test 1: ARCHITECT Spawned via Task()

```
ORCHESTRATOR spawns ARCHITECT via Task()
ARCHITECT reports: "I do NOT have access to a Task() tool"
```

**Tools ARCHITECT has:**
- Bash, Glob, Grep, Read, Edit, Write, NotebookEdit
- WebFetch, WebSearch
- Skill, TaskCreate/Get/Update/List, ToolSearch
- MCP tools (mcp__*)

**Tools ARCHITECT does NOT have:**
- **Task()** - the subagent spawning function

### Test 2: MCP spawn_agent_tool

```python
spec = mcp__residency-scheduler__spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="test spawn"
)
# Returns valid spec with identity, RAG context, audit trail
# BUT requires Task() to execute - which subagents don't have
```

**Result:** Tool works correctly as a factory, but subagents can't execute the spec.

### Test 3: CLI Spawning Workaround

```bash
claude -p "You are SPECIALIST. Do X." --model haiku --max-budget-usd 1.00
```

**Result:** CLI-spawned agent **DOES have Task()** available!

---

## Architecture Gap

### Design (from party skills)

```
ORCHESTRATOR → 1 Commander (G2_RECON)
                    ↓
              Commander spawns 12 G-2 teams (via Task())
                    ↓
              Each team spawns 10 probes
```

### Reality

```
ORCHESTRATOR → 1 Commander (G2_RECON)
                    ↓
              Commander tries Task() → NOT AVAILABLE
              Commander can call spawn_agent_tool → gets spec but can't execute
```

---

## Working Patterns

### Pattern A: Flat Parallelism (Proven, Always Worked)

```
ORCHESTRATOR ──┬── Agent 1 (works directly, no Task())
               ├── Agent 2 (works directly, no Task())
               ├── Agent 3 (works directly, no Task())
               └── Agent N (works directly, no Task())
```

**This is what all past "cascades" actually used.**

### Pattern B: CLI Escape Hatch (New Discovery)

```
ORCHESTRATOR ──┬── Coordinator (via Task, no Task())
               │        │
               │        └── Bash: claude -p → Specialist (HAS Task())
               │                                    │
               │                                    └── Task() → Sub-specialist
```

**Trade-offs:**
- Pro: Enables true hierarchical spawning
- Con: Session isolation (no shared context)
- Con: Requires budget limits to prevent runaway
- Con: Spawn chain governance not enforced by code

---

## Why This Wasn't Discovered Earlier

1. **Flat parallelism worked fine** - ORCHESTRATOR spawning N agents directly always succeeded
2. **Party skills were designed but not fully executed** - The 12-team, 120-probe structure was documented but testing stopped at first level
3. **User visibility limitation** - Users see the first subagent spawn succeed, but can't observe what tools that subagent has
4. **MCP path bug masked testing** - Docker path resolution (`/.claude`) prevented MCP spawn_agent_tool testing until fixed

---

## Docker Fix Applied

Added `.claude` mount to MCP container in `docker-compose.dev.yml`:

```yaml
mcp-server:
  volumes:
    - ./mcp-server/src:/app/src
    - ./mcp-server/tests:/app/tests
    - ./.claude:/app/.claude  # Added for identity cards, registry, audit
  environment:
    PROJECT_ROOT: /app  # For spawn_agent_tool path resolution
```

Also updated `mcp-server/src/scheduler_mcp/server.py` to use `PROJECT_ROOT` env var when available.

---

## Documentation Updates

| File | Change |
|------|--------|
| `.claude/skills/spawn-agent/SKILL.md` | Add CLI workaround section |
| `.claude/skills/search-party/SKILL.md` | Add Task() limitation warning |
| `.claude/skills/qa-party/SKILL.md` | Add Task() limitation warning |
| `.claude/skills/plan-party/SKILL.md` | Add Task() limitation warning |
| `.claude/Governance/HIERARCHY.md` | Add spawning constraints table |
| `.claude/Governance/SPAWNING_CONSTRAINTS.md` | New file with full docs |

---

## Summary Table

| Spawner | Has Task()? | Can Spawn via Task()? | Can Spawn via CLI? |
|---------|-------------|----------------------|-------------------|
| ORCHESTRATOR (main session) | Yes | Yes | Yes |
| Deputy (via Task) | No | No | Yes |
| Coordinator (via Task) | No | No | Yes |
| Specialist (via Task) | No | No | Yes |
| Agent (via CLI) | Yes | Yes | Yes |

---

*Session 138 complete. Critical architecture constraint documented.*
