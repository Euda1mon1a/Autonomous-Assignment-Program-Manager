# Signal Propagation Protocol

> **Purpose:** Enable real-time coordination between parallel agents
> **Status:** Proposed (from CCW Parallelization Analysis PR #561)
> **Priority:** P2

---

## Overview

When multiple agents work in parallel, they need a signaling mechanism to:
- Announce state changes
- Request serialization
- Signal dependency resolution
- Detect conflicts early

---

## Signal Types

| Signal | Meaning | Emitter | Receivers |
|--------|---------|---------|-----------|
| `CHECKPOINT_REACHED` | Safe pause point reached | Any agent | All parallel agents |
| `DEPENDENCY_RESOLVED` | Output available for consumption | Producer agent | Waiting agents |
| `CONFLICT_DETECTED` | Write collision imminent | Conflict detector | ORCHESTRATOR |
| `INTEGRATION_REQUIRED` | Milestone reached, sync needed | Stream lead | All agents |
| `EARLY_COMPLETION` | Finished ahead of schedule | Fast agent | Load balancer |
| `BLOCKED` | Cannot proceed, waiting | Blocked agent | ORCHESTRATOR |
| `ESCALATE` | Issue requires human/higher authority | Any agent | ORCHESTRATOR |

---

## Signal Structure

```json
{
  "signal_type": "DEPENDENCY_RESOLVED",
  "emitter": "ARCHITECT",
  "stream": "A",
  "timestamp": "2025-12-30T19:30:00Z",
  "payload": {
    "dependency_id": "schema-migration",
    "output_location": "alembic/versions/xyz.py",
    "consumers": ["SCHEDULER", "QA_TESTER"]
  }
}
```

---

## Propagation Rules

### Rule 1: ORCHESTRATOR Routes All Signals

All signals flow through ORCHESTRATOR for centralized coordination:

```
Agent A → ORCHESTRATOR → Agent B
                      → Agent C
                      → Agent D
```

### Rule 2: BLOCKED Triggers Investigation

When any agent emits `BLOCKED`:
1. ORCHESTRATOR identifies blocking dependency
2. Checks if blocker is aware
3. Escalates if deadlock detected

### Rule 3: CONFLICT_DETECTED Serializes

When `CONFLICT_DETECTED` emitted:
1. All agents in conflict domain pause
2. ORCHESTRATOR determines priority
3. Lower-priority agents wait
4. Higher-priority agent proceeds

### Rule 4: INTEGRATION_REQUIRED Synchronizes

When `INTEGRATION_REQUIRED` emitted (Level 3 integration point):
1. All active agents reach next checkpoint
2. Barrier synchronization
3. Integration proceeds
4. All agents resume

---

## Integration with PARALLELISM_FRAMEWORK

### Level 3 Integration Points Emit Signals

```markdown
Level 3 integration points automatically emit INTEGRATION_REQUIRED:

1. Database migrations complete → INTEGRATION_REQUIRED
2. API contract changes → INTEGRATION_REQUIRED
3. Release milestones → INTEGRATION_REQUIRED
```

### Level 2 Dependencies Emit Signals

```markdown
When producer completes:
  emit DEPENDENCY_RESOLVED(output_id, consumers)

When consumer receives:
  resume blocked task
```

---

## Conflict Detection

### Write-Write Conflict

```python
def detect_conflict(pending_writes: list[Write]) -> bool:
    """
    Check if multiple agents plan to write same file.
    """
    files = [w.file_path for w in pending_writes]
    return len(files) != len(set(files))  # Duplicates = conflict
```

### Read-Write Conflict

```python
def detect_stale_read(reads: list[Read], writes: list[Write]) -> bool:
    """
    Check if agent reading file another agent will modify.
    """
    read_files = {r.file_path for r in reads}
    write_files = {w.file_path for w in writes}
    return bool(read_files & write_files)  # Intersection = stale read risk
```

---

## Example: Parallel Implementation Session

```
Time  Signal                    Stream  Action
────  ────────────────────────  ──────  ─────────────────────────────
0:00  STARTED                   A, B    Both streams begin work
0:05  PROGRESS(25%)             A       Stream A reports progress
0:10  BLOCKED(schema-change)    B       Stream B needs Stream A output
0:15  DEPENDENCY_RESOLVED       A       Stream A completes schema
0:15  (auto-resume)             B       Stream B continues
0:20  CHECKPOINT_REACHED        A, B    Both reach safe point
0:25  CONFLICT_DETECTED         A, B    Both want to edit config.py
0:25  (serialize)               A       Stream A gets priority
0:30  DEPENDENCY_RESOLVED       A       Stream A done with config.py
0:30  (resume)                  B       Stream B edits config.py
0:35  INTEGRATION_REQUIRED      D       Integration stream signals
0:35  (barrier)                 A, B    Both reach next checkpoint
0:40  COMPLETED                 A, B    Both streams done
```

---

## Implementation Notes

### Current: Convention-Based

Agents voluntarily emit signals in structured output. No enforcement.

### Future: Infrastructure

Built-in signal routing through ORCHESTRATOR with automatic:
- Deadlock detection
- Priority arbitration
- Checkpoint enforcement

---

## Related Protocols

- `RESULT_STREAMING.md` - Progress visibility
- `TODO_PARALLEL_SCHEMA.md` - Task metadata
- `MULTI_TERMINAL_HANDOFF.md` - Session coordination
- `PARALLELISM_FRAMEWORK.md` - Decision rules

---

*Proposed in Session 025 based on CCW Parallelization Analysis*
