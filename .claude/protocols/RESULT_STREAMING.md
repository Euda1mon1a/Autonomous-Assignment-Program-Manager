***REMOVED*** Result Streaming Protocol

> **Purpose:** Enable ORCHESTRATOR to synthesize while agents still running
> **Status:** Proposed (from CCW Parallelization Analysis PR ***REMOVED***561)
> **Priority:** P1

---

***REMOVED******REMOVED*** Overview

Traditional agent execution is blocking: spawn → wait → receive full result. Result streaming enables partial progress visibility and early synthesis.

---

***REMOVED******REMOVED*** Signal Types

| Signal | Meaning | Receiver | When Emitted |
|--------|---------|----------|--------------|
| `STARTED` | Work begun | ORCHESTRATOR | Immediately on spawn |
| `PROGRESS(n%)` | Partial completion | Load balancer | At defined checkpoints |
| `PARTIAL_RESULT` | Early findings available | SYNTHESIZER | When subset complete |
| `BLOCKED` | Waiting on dependency | ORCHESTRATOR | When serialization needed |
| `COMPLETED` | Full results ready | ORCHESTRATOR | On completion |
| `FAILED` | Unrecoverable error | ORCHESTRATOR | On failure |

---

***REMOVED******REMOVED*** Benefits

***REMOVED******REMOVED******REMOVED*** For ORCHESTRATOR
- Begin synthesis before all agents complete
- Early failure detection (fail fast)
- Dynamic load balancing based on progress

***REMOVED******REMOVED******REMOVED*** For SYNTHESIZER
- Incremental integration of findings
- Conflict detection during execution
- Progressive refinement of output

***REMOVED******REMOVED******REMOVED*** For User Experience
- Visible progress indicators
- Reduced perceived latency
- Partial results available sooner

---

***REMOVED******REMOVED*** Implementation Pattern

***REMOVED******REMOVED******REMOVED*** Agent Output Structure

Agents emit structured signals in their output:

```json
{
  "signal": "PROGRESS",
  "percent": 50,
  "checkpoint": "files_analyzed",
  "partial": {
    "files_found": 12,
    "patterns_matched": 3
  },
  "next_checkpoint": "tests_verified"
}
```

***REMOVED******REMOVED******REMOVED*** Checkpoint Definition

Define meaningful checkpoints per task type:

| Task Type | Checkpoints |
|-----------|-------------|
| Code Review | `files_read` → `issues_found` → `recommendations_drafted` |
| Test Writing | `coverage_analyzed` → `tests_generated` → `tests_validated` |
| Exploration | `files_searched` → `patterns_found` → `synthesis_complete` |

---

***REMOVED******REMOVED*** Integration with TodoWrite

Streaming signals can update todo metadata:

```python
{
    "content": "Review auth module",
    "status": "in_progress",
    "activeForm": "Reviewing auth module",
    "progress_percent": 75,
    "last_signal": "PARTIAL_RESULT",
    "partial_findings": ["2 security issues", "1 performance concern"]
}
```

---

***REMOVED******REMOVED*** Adoption Path

***REMOVED******REMOVED******REMOVED*** Phase 1: Documentation (Current)
- Define signal types and semantics
- Establish checkpoint conventions

***REMOVED******REMOVED******REMOVED*** Phase 2: Convention-Based
- Agents voluntarily emit progress signals
- ORCHESTRATOR logs but doesn't require

***REMOVED******REMOVED******REMOVED*** Phase 3: Infrastructure
- Built-in progress tracking
- Automatic timeout based on progress
- Load balancing across streams

---

***REMOVED******REMOVED*** Related Protocols

- `SIGNAL_PROPAGATION.md` - Inter-agent signaling
- `MULTI_TERMINAL_HANDOFF.md` - Cross-session coordination
- `PARALLELISM_FRAMEWORK.md` - Parallelization decision rules

---

*Proposed in Session 025 based on CCW Parallelization Analysis*
