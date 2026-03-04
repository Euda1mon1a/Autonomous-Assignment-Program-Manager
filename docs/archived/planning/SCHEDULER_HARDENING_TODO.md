# Scheduler Hardening TODO

> **Created:** 2025-12-25
> **Status:** Active planning document
> **Source:** ChatGPT Pulse analysis - operational resilience recommendations

This document tracks future hardening work for the scheduler system. Items are prioritized by impact and implementation effort.

---

## Completed (2025-12-25)

### P0: Kill-Switch for Runaway Solver Jobs
- **Files created:**
  - `backend/app/scheduling/solver_control.py` - Redis-backed solver control
  - API endpoints in `backend/app/api/routes/scheduler_ops.py`:
    - `POST /scheduler/runs/{run_id}/abort` - Abort a running solver
    - `GET /scheduler/runs/{run_id}/progress` - Get solver progress
    - `GET /scheduler/runs/active` - List active solver runs
  - Schemas in `backend/app/schemas/scheduler_ops.py`

- **Features:**
  - Redis-backed abort signaling
  - Progress tracking for monitoring
  - Graceful shutdown with best-solution capture
  - TTL-based cleanup

### P1: Constraint-Level Violation Metrics
- **Files modified:**
  - `backend/app/core/metrics/prometheus.py`

- **Metrics added:**
  - `scheduler_constraint_violations_total` - By name, type, severity
  - `scheduler_constraint_evaluation_seconds` - Timing histogram
  - `scheduler_constraint_satisfaction_rate` - Satisfaction gauge
  - `scheduler_solver_iterations_total` - Iteration counter
  - `scheduler_solver_abort_total` - Abort counter by reason
  - `scheduler_solver_best_score` - Best score gauge

- **Helper methods:**
  - `record_constraint_violation()`
  - `time_constraint_evaluation()` - Context manager
  - `update_constraint_satisfaction()`
  - `record_solver_iteration()`
  - `record_solver_abort()`
  - `update_solver_best_score()`

---

## P2: Near-Term (Next Month)

### Deterministic Solver Checkpointing

**Why:** Long solver runs (15+ min) lose all progress on crash. System restarts from scratch.

**Implementation:**
```
backend/app/models/solver_snapshot.py (new)
backend/alembic/versions/xxx_add_solver_snapshots.py (new migration)
```

**Schema:**
```python
class SolverSnapshot(Base):
    __tablename__ = "solver_snapshots"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("schedule_runs.id"), index=True)
    iteration = Column(Integer, nullable=False)
    state_blob = Column(LargeBinary, nullable=False)
    best_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Checkpoint frequency:** Every 1000 iterations or 60 seconds.

**Effort:** Medium (requires migration, solver integration)

---

### Schedule Diff Guard Before Activation

**Why:** A constraint bug could radically reassign all residents. Version comparison exists but isn't enforced as a gate.

**Implementation:**
```
backend/app/scheduling/diff_guard.py (new)
```

**Key function:**
```python
def validate_diff(old, new, max_delta=0.20):
    """Compare schedules and enforce bounded change thresholds."""
    changes = diff_assignments(old, new)
    ratio = len(changes) / len(old.assignments)
    if ratio > max_delta:
        raise ValueError("Excessive schedule churn detected")
```

**Thresholds:**
- Global change ratio: 20% max
- Per-resident changes: 10 max

**Effort:** Low (no migration, pure Python)

---

### Write-Ahead Schedule Publish Staging

**Why:** Database crash between version write and activation leaves schedule in undefined state.

**Implementation:**
```
backend/app/models/schedule_publish_staging.py (new)
backend/alembic/versions/xxx_add_publish_staging.py (new migration)
```

**Schema:**
```python
class SchedulePublishStaging(Base):
    __tablename__ = "schedule_publish_staging"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("schedule_runs.id"))
    previous_active_id = Column(String, nullable=True)
    checksum = Column(String, nullable=False)
    initiated_by = Column(String, nullable=False)
    initiated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, committed, rolled_back
```

**Recovery logic:** On startup, check for pending staging records and either complete or rollback.

**Effort:** Medium (requires migration, startup hook)

---

### Schedule Correctness SLO

**Why:** Latent data integrity issues accumulate without visibility.

**Implementation:**
- Add to `backend/app/core/metrics/prometheus.py`:
```python
SCHEDULE_VALID_PUBLISH = Counter("scheduler_valid_publish_total", "")
SCHEDULE_ROLLBACK = Counter("scheduler_rollback_total", "", ["reason"])
```

- Add Prometheus alerting rule:
```yaml
- alert: ScheduleCorrectnessSLOBreach
  expr: rate(scheduler_rollback_total[1h]) / rate(scheduler_valid_publish_total[1h]) > 0.05
  for: 5m
  labels:
    severity: warning
```

**Effort:** Low (metrics only, no migration)

---

## P3: Longer-Term

### Solver Sandboxing with Resource Ceilings

**Why:** Crafted input can trigger pathological solver behavior, starving the host.

**Implementation:**
```
backend/app/scheduling/sandbox.py (new)
```

**Approach:**
```python
import resource
import subprocess

def run_solver_sandboxed(solver_func, *args, max_memory_mb=2000, max_cpu_seconds=900):
    """Run solver with resource constraints."""
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_mb * 1024 * 1024, -1))
    resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, max_cpu_seconds + 60))
    return solver_func(*args)
```

**Alternative:** Use cgroups/Docker for isolation.

**Effort:** Medium (requires testing, may affect solver behavior)

---

### Field-Level Encryption for Sensitive Data

**Why:** Database compromise could expose military status, leave, accommodations.

**Fields to encrypt:**
- `leave_type` on Absence model
- `accommodation_notes` on Person model
- `military_status` on Person model

**Implementation options:**
1. **Application-level:** `cryptography.fernet` with key from env var
2. **Database-level:** PostgreSQL TDE (Transparent Data Encryption)

**Schema (Option 1):**
```python
class EncryptedJSON(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return fernet.encrypt(json.dumps(value).encode())

    def process_result_value(self, value, dialect):
        return json.loads(fernet.decrypt(value))
```

**Effort:** High (key management, migration, testing)

---

### One-Time Publish Tokens to Prevent Replay

**Why:** A captured publish request could be replayed later, overwriting a newer schedule.

**Implementation:**
```
backend/app/security/publish_token.py (new)
```

**Key function:**
```python
def verify_publish_token(job_id: str, token: str) -> bool:
    """Verify and consume one-time publish token."""
    key = f"publish_token:{job_id}"
    if redis.get(key) != token:
        raise HTTPException(403, "Invalid or expired publish token")
    redis.delete(key)  # Consume token
    return True
```

**Effort:** Low-Medium (Redis-backed, API changes)

---

## Integration Points

### Where to Hook Kill-Switch in Solvers

The `SolverControl.should_abort()` check should be added to:

1. **CP-SAT Solver** (`backend/app/scheduling/solvers.py`):
   - In the solution callback
   - Before each optimization round

2. **Greedy Solver** (`backend/app/scheduling/solvers.py`):
   - After each block assignment iteration

3. **PuLP Solver** (`backend/app/scheduling/solvers.py`):
   - After solve() returns, before result processing

### Example Integration (CP-SAT):

```python
from app.scheduling.solver_control import SolverControl

class ScheduleSolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, run_id: str, ...):
        self.run_id = run_id
        ...

    def on_solution_callback(self):
        # Check for abort signal
        if abort_reason := SolverControl.should_abort(self.run_id):
            self.StopSearch()
            return

        # Update progress
        SolverControl.update_progress(
            self.run_id,
            iteration=self.num_solutions,
            best_score=self.ObjectiveValue(),
            assignments_count=self._count_assignments()
        )
```

---

## MCP Server Integration

### MCP Tool: Solver Abort

**Why:** AI agents need ability to abort runaway solvers via MCP tools.

**Implementation:**
```
mcp-server/scheduler_mcp/tools/solver_control.py (new)
```

**Tool definition:**
```python
@mcp.tool()
async def abort_solver(
    run_id: str,
    reason: str = "AI agent request"
) -> dict:
    """
    Abort a running solver job.

    Args:
        run_id: Schedule run ID to abort
        reason: Reason for abort (logged for audit)

    Returns:
        Status of abort request
    """
    response = await api_client.post(
        f"/scheduler/runs/{run_id}/abort",
        json={"reason": reason, "requested_by": "mcp-agent"}
    )
    return response.json()
```

**Effort:** Low (thin wrapper over existing API)

---

### MCP Tool: Solver Progress

**Why:** AI agents monitoring long solves need real-time progress.

**Implementation:**
```python
@mcp.tool()
async def get_solver_progress(run_id: str) -> dict:
    """Get progress for a running solver."""
    response = await api_client.get(f"/scheduler/runs/{run_id}/progress")
    return response.json()

@mcp.tool()
async def list_active_solvers() -> dict:
    """List all currently running solver jobs."""
    response = await api_client.get("/scheduler/runs/active")
    return response.json()
```

**Effort:** Low (thin wrapper over existing API)

---

### MCP Tool: Constraint Diagnostics

**Why:** AI agents need visibility into constraint violation patterns for debugging.

**Implementation:**
```python
@mcp.tool()
async def get_constraint_metrics() -> dict:
    """
    Get constraint violation metrics.

    Returns breakdown of violations by constraint name,
    type, and severity for the last solve.
    """
    # Query Prometheus metrics or Redis cache
    return {
        "violations_by_constraint": {...},
        "evaluation_times": {...},
        "satisfaction_rates": {...}
    }
```

**Effort:** Medium (needs metrics aggregation endpoint)

---

### MCP Resource: Solver Status (SSE)

**Why:** Real-time progress streaming for long solver runs.

**Implementation:**
```python
@mcp.resource("solver://runs/{run_id}/stream")
async def solver_stream(run_id: str):
    """Server-sent events for solver progress."""
    while True:
        progress = await get_progress(run_id)
        yield json.dumps(progress)
        if progress["status"] != "running":
            break
        await asyncio.sleep(1)
```

**Effort:** Medium (requires SSE support in MCP)

---

### Integration with Safe Schedule Generation Skill

**Current skill:** `.claude/skills/safe-schedule-generation/SKILL.md`

**Enhancement needed:**
1. Before calling `generate_schedule` MCP tool, check for active solvers
2. After generation starts, provide abort capability
3. Stream progress during long solves

**Code path:**
```
AI Agent → Skill activation → Backup check → generate_schedule MCP tool
                                          → abort_solver if needed
                                          → get_solver_progress for monitoring
```

**Effort:** Low (skill documentation update)

---

## References

- [ChatGPT Pulse 2025-12-25](../references/chatgpt-pulse-2025-12-25.md) - Source recommendations
- [Cross-Disciplinary Resilience](../architecture/cross-disciplinary-resilience.md) - Resilience concepts
- [Solver Algorithm](../architecture/SOLVER_ALGORITHM.md) - Solver internals
- [MCP Server README](../../mcp-server/README.md) - MCP tool documentation
