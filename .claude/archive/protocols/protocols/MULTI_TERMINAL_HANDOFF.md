# Multi-Terminal Parallel Protocol

> **Purpose:** Coordinate parallel work across multiple Claude terminals
> **Status:** Proposed (from CCW Parallelization Analysis PR #561)
> **Priority:** P3

---

## Overview

For marathon sessions requiring 5-10 parallel terminals, this protocol defines:
- Terminal assignment strategy
- Handoff file format
- Synchronization points
- Cross-terminal communication

---

## Terminal Assignment Strategy

### Default 10-Terminal Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Stream A: MCP/Scheduling (Terminals 1-3)                    │
│   T1: Tool discovery and registration                       │
│   T2: Tool integration testing                              │
│   T3: Tool documentation                                    │
├─────────────────────────────────────────────────────────────┤
│ Stream B: Backend Tests (Terminals 4-6)                     │
│   T4: Unit tests - services                                 │
│   T5: Unit tests - routes                                   │
│   T6: Integration tests                                     │
├─────────────────────────────────────────────────────────────┤
│ Stream C: Frontend (Terminals 7-8)                          │
│   T7: Component tests                                       │
│   T8: E2E tests                                            │
├─────────────────────────────────────────────────────────────┤
│ Stream D: Integration (Terminal 9)                          │
│   T9: Cross-domain integration, conflict resolution         │
├─────────────────────────────────────────────────────────────┤
│ Stream E: Security/Performance (Terminal 10)                │
│   T10: Security audit, performance profiling                │
└─────────────────────────────────────────────────────────────┘
```

### Coordinator Assignment

| Stream | Coordinator | Authority |
|--------|-------------|-----------|
| A | COORD_ENGINE | Scheduling domain |
| B | COORD_QUALITY | Test quality gates |
| C | COORD_FRONTEND | UI/UX standards |
| D | COORD_OPS | Integration decisions |
| E | COORD_QUALITY | Security/performance |

---

## Handoff File Format

### Location

```
.claude/Scratchpad/PARALLEL_SESSION_[YYYYMMDD_HHMMSS].md
```

### Template

```markdown
# Parallel Session: [Session Name]

> **Started:** [ISO timestamp]
> **Terminals:** [count]
> **Streams:** [count]
> **Status:** [Active | Paused | Completed]

---

## Session Configuration

| Setting | Value |
|---------|-------|
| Branch | `[branch-name]` |
| Base Commit | `[sha]` |
| Estimated Duration | [hours] |
| Checkpoints Planned | [count] |

---

## Stream Status

### Stream A: [Domain] (Terminals [range])

| Field | Value |
|-------|-------|
| **Status** | [In Progress / Blocked / Completed] |
| **Progress** | [percent]% |
| **Last Commit** | `[sha]` |
| **Current Task** | [description] |
| **Blocked By** | [none / stream-id] |
| **Next Action** | [description] |

#### Terminal Details

| Terminal | Agent | Task | Status |
|----------|-------|------|--------|
| T1 | META_UPDATER | Tool docs | ✓ Complete |
| T2 | TOOLSMITH | Integration | In Progress |
| T3 | QA_TESTER | Test tools | Pending |

[Repeat for each stream]

---

## Checkpoints

| # | Description | Streams | Status | Time |
|---|-------------|---------|--------|------|
| 1 | Schema aligned | A, B | ✓ | 10:30 |
| 2 | Integration pass | A, B, D | ○ | - |
| 3 | Security review | E | ○ | - |

---

## Signal Log

| Time | Signal | Stream | Details |
|------|--------|--------|---------|
| 10:00 | STARTED | A, B, C | Session initialized |
| 10:15 | PROGRESS(40%) | A | Tool registration complete |
| 10:20 | BLOCKED | B | Waiting on Stream A schema |
| 10:25 | DEPENDENCY_RESOLVED | A | Schema available |
| 10:25 | (resume) | B | Auto-resumed |

---

## Blocking Issues

### Active Blockers

| ID | Stream | Description | Owner | ETA |
|----|--------|-------------|-------|-----|
| B1 | D | API contract mismatch | ARCHITECT | 30m |

### Resolved Blockers

| ID | Stream | Description | Resolution |
|----|--------|-------------|------------|
| B0 | B | Missing fixture | Added in commit abc123 |

---

## Handoff Notes

### For Next Session

- [ ] Stream A needs to complete tool registration before B can integrate
- [ ] Stream E security findings require triage before merge
- [ ] Frontend tests in Stream C have 3 flaky tests to investigate

### Key Decisions Made

1. Chose HTTP transport for MCP (rationale: concurrent connections, debugging)
2. Deferred performance optimization to next session

---

## Files Modified

| Stream | Files | Status |
|--------|-------|--------|
| A | `.claude/skills/MCP_*/SKILL.md` | Committed |
| B | `backend/tests/test_*.py` | Uncommitted |
| C | `frontend/__tests__/*.tsx` | Stashed |

---

*Last Updated: [timestamp]*
*Next Checkpoint: [description] at [time]*
```

---

## Synchronization Protocol

### Starting a Parallel Session

1. Create handoff file with initial assignment
2. Each terminal reads handoff file on start
3. Terminal announces `STARTED` signal
4. Work begins

### During Execution

1. Terminals update handoff file at checkpoints
2. Use file locking or append-only updates
3. Signal via file updates (polling) or explicit commands

### Checkpoint Synchronization

1. Stream lead calls checkpoint
2. All terminals in stream reach safe point
3. Update handoff file
4. Barrier released

### Ending a Session

1. All streams complete or reach checkpoint
2. Final handoff file update
3. Summary of completed/pending work
4. Clear next actions per terminal

---

## Best Practices

### DO

- Update handoff file frequently (every 15 min)
- Include specific file paths in status
- Note blocking dependencies explicitly
- Keep signal log for debugging

### DON'T

- Leave terminals idle without documentation
- Skip checkpoints to "save time"
- Modify files owned by other streams
- Ignore blocking signals

---

## Related Protocols

- `SIGNAL_PROPAGATION.md` - Inter-agent signaling
- `RESULT_STREAMING.md` - Progress visibility
- `TODO_PARALLEL_SCHEMA.md` - Task metadata
- `PARALLELISM_FRAMEWORK.md` - Decision rules

---

*Proposed in Session 025 based on CCW Parallelization Analysis*
