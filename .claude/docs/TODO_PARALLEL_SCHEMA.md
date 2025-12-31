***REMOVED*** TodoWrite Parallel Execution Schema

> **Purpose:** Extend TodoWrite with parallel execution metadata
> **Status:** Proposed (from CCW Parallelization Analysis PR ***REMOVED***561)
> **Priority:** P2

---

***REMOVED******REMOVED*** Overview

The TodoWrite tool currently tracks task status but lacks parallelization awareness. This schema extends todo items with parallel execution metadata for better orchestration.

---

***REMOVED******REMOVED*** Current Schema

```python
{
    "content": str,       ***REMOVED*** Task description (imperative form)
    "status": str,        ***REMOVED*** "pending" | "in_progress" | "completed"
    "activeForm": str     ***REMOVED*** Present continuous form for display
}
```

---

***REMOVED******REMOVED*** Extended Schema (Proposed)

```python
{
    ***REMOVED*** Existing fields
    "content": str,
    "status": str,
    "activeForm": str,

    ***REMOVED*** NEW: Parallel execution metadata
    "parallel_group": str | None,      ***REMOVED*** Group ID for concurrent tasks
    "can_merge_after": list[str],      ***REMOVED*** Task IDs that must complete first
    "blocks": list[str],               ***REMOVED*** Task IDs waiting on this task
    "stream": str | None,              ***REMOVED*** Stream assignment (A, B, C...)
    "terminal": int | None,            ***REMOVED*** Terminal assignment (1-10)
    "progress_percent": int | None,    ***REMOVED*** 0-100 completion estimate
    "last_signal": str | None          ***REMOVED*** Last streaming signal received
}
```

---

***REMOVED******REMOVED*** Field Semantics

***REMOVED******REMOVED******REMOVED*** parallel_group

Tasks with the same `parallel_group` can execute concurrently:

```python
todos = [
    {"content": "Write auth tests", "parallel_group": "quality-checks", ...},
    {"content": "Write API tests", "parallel_group": "quality-checks", ...},
    {"content": "Run linter", "parallel_group": "quality-checks", ...},
]
***REMOVED*** All 3 can run in parallel
```

***REMOVED******REMOVED******REMOVED*** can_merge_after

Defines merge dependencies (this task's output depends on others):

```python
{
    "content": "Integration test",
    "can_merge_after": ["auth-tests", "api-tests"],
    ***REMOVED*** Cannot start until both complete
}
```

***REMOVED******REMOVED******REMOVED*** blocks

Identifies downstream tasks waiting on this one:

```python
{
    "content": "Database migration",
    "blocks": ["api-implementation", "test-execution"],
    ***REMOVED*** Two tasks are waiting for this to complete
}
```

---

***REMOVED******REMOVED*** Visualization

Enhanced todo list display:

```
***REMOVED******REMOVED*** Tasks

***REMOVED******REMOVED******REMOVED*** Stream A (Terminals 1-3)
- [=========>] 40% Write auth tests (parallel_group: quality)
- [============>] 60% Write API tests (parallel_group: quality)

***REMOVED******REMOVED******REMOVED*** Stream B (Terminals 4-6) - BLOCKED
- [----------] 0% Integration test
  Waiting on: auth-tests, api-tests

***REMOVED******REMOVED******REMOVED*** Stream C (Terminal 9)
- [==========] DONE Database migration
  Unblocks: api-implementation, test-execution
```

---

***REMOVED******REMOVED*** Usage Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Parallel Quality Checks

```python
TodoWrite([
    {"content": "Run pytest", "parallel_group": "ci", "stream": "A"},
    {"content": "Run eslint", "parallel_group": "ci", "stream": "B"},
    {"content": "Run mypy", "parallel_group": "ci", "stream": "C"},
    {"content": "Merge results", "can_merge_after": ["pytest", "eslint", "mypy"]},
])
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Phased Implementation

```python
TodoWrite([
    {"content": "Design schema", "blocks": ["implement-api", "write-tests"]},
    {"content": "Implement API", "can_merge_after": ["design-schema"], "parallel_group": "impl"},
    {"content": "Write tests", "can_merge_after": ["design-schema"], "parallel_group": "impl"},
    {"content": "Integration", "can_merge_after": ["implement-api", "write-tests"]},
])
```

---

***REMOVED******REMOVED*** Integration with Streams

Map parallel_group to work streams:

| parallel_group | Stream | Typical Tasks |
|---------------|--------|---------------|
| `mcp-tools` | A | MCP server, tool registration |
| `backend-tests` | B | pytest, coverage |
| `frontend` | C | jest, component tests |
| `integration` | D | e2e, cross-domain |
| `security` | E | audit, compliance |

---

***REMOVED******REMOVED*** Adoption Path

***REMOVED******REMOVED******REMOVED*** Phase 1: Convention (Current)
- Document the schema
- Agents voluntarily use metadata

***REMOVED******REMOVED******REMOVED*** Phase 2: Tooling
- ORCHESTRATOR reads parallel metadata
- Automatic dependency resolution

***REMOVED******REMOVED******REMOVED*** Phase 3: Enforcement
- TodoWrite validates parallel constraints
- Blocks invalid parallel assignments

---

***REMOVED******REMOVED*** Related Documents

- `PARALLELISM_FRAMEWORK.md` - Decision rules for parallelization
- `SIGNAL_PROPAGATION.md` - Inter-agent signaling
- `RESULT_STREAMING.md` - Progress visibility
- `MULTI_TERMINAL_HANDOFF.md` - Session coordination

---

*Proposed in Session 025 based on CCW Parallelization Analysis*
