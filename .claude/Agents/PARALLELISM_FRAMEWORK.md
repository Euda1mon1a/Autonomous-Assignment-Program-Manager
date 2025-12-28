***REMOVED*** PARALLELISM_FRAMEWORK - Decision Rules for Parallel Execution

> **Purpose:** Codified rules for determining parallel vs. serial execution in multi-agent workflows
> **Audience:** All PAI agents (ORCHESTRATOR, Coordinators, Specialists)
> **Authority:** Mandatory - agents MUST follow these rules
> **Version:** 1.0.0
> **Last Updated:** 2025-12-28

---

***REMOVED******REMOVED*** Overview

This framework provides deterministic rules for agents to decide when tasks can run in parallel vs. when they must serialize. Following these rules prevents file conflicts, race conditions, and wasted rework.

**Core Principle:** "When in doubt, check the domain. Different domains can run parallel."

---

***REMOVED******REMOVED*** Level 1: File Domain Check

***REMOVED******REMOVED******REMOVED*** Domain-to-Coordinator Mapping

```
File Path                           → Coordinator         → Can Parallel With
─────────────────────────────────────────────────────────────────────────────
backend/app/scheduling/*            → COORD_ENGINE        → All except self
backend/app/resilience/*            → COORD_RESILIENCE    → All except self
backend/app/api/*                   → COORD_PLATFORM      → All except self
backend/app/services/*              → COORD_PLATFORM      → All except self
backend/app/models/*                → COORD_PLATFORM      → All except self
backend/alembic/*                   → COORD_PLATFORM      → NONE (serialized)
frontend/src/*                      → COORD_FRONTEND      → All except self
backend/tests/*                     → COORD_QUALITY       → All except self
frontend/__tests__/*                → COORD_QUALITY       → All except self
.claude/*                           → COORD_OPS           → All except self
docs/*                              → COORD_OPS           → All except self
```

***REMOVED******REMOVED******REMOVED*** Decision Rule

```python
def can_run_parallel(task_a: Task, task_b: Task) -> bool:
    """Level 1: Check if tasks operate on different domains."""

    domain_a = get_coordinator_domain(task_a.files)
    domain_b = get_coordinator_domain(task_b.files)

    ***REMOVED*** Different domains = safe to parallel
    if domain_a != domain_b:
        return True

    ***REMOVED*** Same domain = proceed to Level 2 check
    return check_level_2_dependencies(task_a, task_b)
```

---

***REMOVED******REMOVED*** Level 2: Dependency Graph Check

When tasks are in the same domain, check for output→input dependencies.

***REMOVED******REMOVED******REMOVED*** Dependency Types

| Dependency Type | Description | Action |
|-----------------|-------------|--------|
| **Data Flow** | Task B needs Task A's output | SERIALIZE (A → B) |
| **Write-Read** | Task B reads files Task A writes | SERIALIZE (A → B) |
| **Write-Write** | Both tasks write same file | SERIALIZE (pick one) |
| **Read-Read** | Both tasks read same file | PARALLEL OK |
| **Independent** | No shared files or data | PARALLEL OK |

***REMOVED******REMOVED******REMOVED*** Decision Rule

```python
def check_level_2_dependencies(task_a: Task, task_b: Task) -> bool:
    """Level 2: Check for output→input dependencies."""

    ***REMOVED*** Check if B needs A's output
    if task_b.inputs.intersection(task_a.outputs):
        return False  ***REMOVED*** Serialize: A before B

    ***REMOVED*** Check if A needs B's output
    if task_a.inputs.intersection(task_b.outputs):
        return False  ***REMOVED*** Serialize: B before A

    ***REMOVED*** Check write conflicts
    if task_a.writes.intersection(task_b.writes):
        return False  ***REMOVED*** Serialize: conflict

    ***REMOVED*** Check write-then-read
    if task_a.writes.intersection(task_b.reads):
        return False  ***REMOVED*** Serialize: A before B

    if task_b.writes.intersection(task_a.reads):
        return False  ***REMOVED*** Serialize: B before A

    ***REMOVED*** No dependencies found
    return True  ***REMOVED*** PARALLEL OK
```

***REMOVED******REMOVED******REMOVED*** Common Dependency Patterns

```
Pattern: Schema → Implementation
  ARCHITECT creates model → BACKEND_ENGINEER implements service
  Action: SERIALIZE (ARCHITECT first)

Pattern: Implementation → Test
  BACKEND_ENGINEER writes code → QA_TESTER writes tests
  Action: Can PARALLEL (tests can be written to spec, not just code)

Pattern: Multiple Tests
  QA_TESTER unit tests → QA_TESTER integration tests
  Action: Can PARALLEL (different test files)

Pattern: Feature Development
  FRONTEND_ENGINEER UI → BACKEND_ENGINEER API
  Action: Can PARALLEL (interface agreed upfront)
```

---

***REMOVED******REMOVED*** Level 3: Integration Point Check

Certain milestones require all streams to converge before proceeding.

***REMOVED******REMOVED******REMOVED*** Integration Points (Serialize Here)

| Integration Point | Trigger | Required Coordination |
|-------------------|---------|----------------------|
| **Database Migration** | `alembic revision` or model changes | ALL agents pause, DBA executes |
| **API Contract Change** | Schema change affecting frontend | COORD_PLATFORM + COORD_FRONTEND sync |
| **Release Milestone** | PR merge, version bump | ALL streams converge via SYNTHESIZER |
| **Compliance Validation** | Before any schedule commit | COORD_RESILIENCE validates ALL changes |
| **Security Audit** | Before auth/data changes | COORD_RESILIENCE reviews ALL streams |

***REMOVED******REMOVED******REMOVED*** Decision Rule

```python
def is_integration_point(task: Task) -> bool:
    """Level 3: Check if this is an integration milestone."""

    INTEGRATION_TRIGGERS = [
        "alembic",           ***REMOVED*** Database migration
        "api_contract",      ***REMOVED*** API schema change
        "release",           ***REMOVED*** Version/deployment
        "schedule_commit",   ***REMOVED*** Schedule to production
        "auth_change",       ***REMOVED*** Authentication modification
        "model_change",      ***REMOVED*** SQLAlchemy model modification
    ]

    return any(trigger in task.tags for trigger in INTEGRATION_TRIGGERS)

def handle_integration_point(task: Task, active_streams: list) -> Action:
    """Coordinate integration point."""

    ***REMOVED*** Signal all active streams to pause at safe checkpoint
    for stream in active_streams:
        stream.signal_checkpoint()

    ***REMOVED*** Wait for all streams to reach checkpoint
    await asyncio.gather(*[s.await_checkpoint() for s in active_streams])

    ***REMOVED*** Execute integration task
    result = await execute_integration(task)

    ***REMOVED*** Signal all streams to resume
    for stream in active_streams:
        stream.signal_resume()

    return result
```

---

***REMOVED******REMOVED*** Decision Tree for All Agents

```
START: Can I run Task B while Task A is running?
  │
  ├─ Same file? ──YES──────────────────────────────────> SERIALIZE
  │                                                        │
  NO                                                       │
  │                                                        │
  ├─ Same coordinator domain? ──YES──┐                     │
  │                                  │                     │
  NO                                 ▼                     │
  │                     ┌─────────────────────────┐        │
  │                     │ Check Level 2:          │        │
  │                     │ - Data flow dependency? │        │
  │                     │ - Write-read conflict?  │        │
  │                     │ - Write-write conflict? │        │
  │                     └─────────────────────────┘        │
  │                                  │                     │
  │                     ┌────────────┴────────────┐        │
  │                     │                         │        │
  │                   YES                        NO        │
  │                     │                         │        │
  │                     ▼                         ▼        │
  │              SERIALIZE              PARALLEL OK        │
  │                     │                         │        │
  │                     └─────────────────────────┘        │
  │                                                        │
  ├─ Integration milestone? ──YES──────────────────────────┤
  │                                                        │
  NO                                                       │
  │                                                        │
  └─────────────────> PARALLEL OK <────────────────────────┘
```

---

***REMOVED******REMOVED*** Coordinator Internal Parallelism

Each coordinator manages parallelism within their domain.

***REMOVED******REMOVED******REMOVED*** COORD_ENGINE Example

```
Task: "Generate Q2 2025 schedule"

Internal Assessment:
  1. SCHEDULER needs constraint definitions
  2. OPTIMIZATION_SPECIALIST can prepare solver config in parallel
  3. SWAP_MANAGER waits for base schedule

Execution Plan:
  Phase 1 (PARALLEL):
    ├─ SCHEDULER: Load rotation templates, constraints
    └─ OPTIMIZATION_SPECIALIST: Configure solver parameters, objectives

  Phase 2 (SERIAL - depends on Phase 1):
    └─ SCHEDULER: Generate base schedule using Phase 1 outputs

  Phase 3 (PARALLEL - depends on Phase 2):
    ├─ OPTIMIZATION_SPECIALIST: Optimize preferences, soft constraints
    └─ SWAP_MANAGER: Identify swap opportunities in generated schedule
```

***REMOVED******REMOVED******REMOVED*** COORD_PLATFORM Example

```
Task: "Add new API endpoint with database changes"

Internal Assessment:
  1. DBA must create migration first (others depend on schema)
  2. BACKEND_ENGINEER can implement service after migration
  3. API_DEVELOPER can design endpoint spec in parallel with DBA

Execution Plan:
  Phase 1 (PARALLEL):
    ├─ DBA: Design and create Alembic migration
    └─ API_DEVELOPER: Design OpenAPI spec (interface agreement)

  Phase 2 (SERIAL - depends on migration):
    └─ BACKEND_ENGINEER: Implement service using new model

  Phase 3 (PARALLEL - depends on Phase 2):
    ├─ API_DEVELOPER: Implement route using service
    └─ DBA: Add necessary indexes after seeing query patterns
```

***REMOVED******REMOVED******REMOVED*** COORD_QUALITY Example

```
Task: "Validate feature implementation"

Internal Assessment:
  1. Code review and test writing are independent
  2. Architecture review can happen in parallel
  3. Final approval depends on all reviews

Execution Plan:
  Phase 1 (PARALLEL):
    ├─ QA_TESTER: Write and run test suite
    ├─ CODE_REVIEWER: Review code quality, style
    └─ ARCHITECT: Review design decisions

  Phase 2 (SERIAL - synthesis):
    └─ COORD_QUALITY: Synthesize results, apply 80% gate
```

---

***REMOVED******REMOVED*** Stream Integration via SYNTHESIZER

When parallel streams complete, SYNTHESIZER integrates results.

***REMOVED******REMOVED******REMOVED*** Integration Protocol

```
ORCHESTRATOR spawns parallel work:
  │
  ├─ COORD_ENGINE ──────────┐
  │   └─ [specialists]      │
  │                         │
  ├─ COORD_RESILIENCE ──────┼────> SYNTHESIZER ───> Integration Report
  │   └─ [specialists]      │
  │                         │
  ├─ COORD_PLATFORM ────────┤
  │   └─ [specialists]      │
  │                         │
  └─ COORD_FRONTEND ────────┘
      └─ [specialists]
```

***REMOVED******REMOVED******REMOVED*** SYNTHESIZER Checklist

1. **Collect:** Receive completion signals from all active coordinators
2. **Validate:** Check for conflicts (same files modified, incompatible changes)
3. **Resolve:** If conflicts, escalate to ORCHESTRATOR with options
4. **Merge:** Create unified deliverable (PR, report, deployment package)
5. **Report:** Briefing to ORCHESTRATOR for final approval

---

***REMOVED******REMOVED*** Quick Reference Card

```
PARALLELISM RULES:
  Different domains?     → PARALLEL OK
  Same domain?           → Check dependencies
  Output→Input?          → SERIALIZE (producer first)
  Write conflict?        → SERIALIZE (one at a time)
  Integration milestone? → CONVERGE (all streams)

DOMAIN MAPPING:
  scheduling/*     → COORD_ENGINE
  resilience/*     → COORD_RESILIENCE
  api/services/*   → COORD_PLATFORM
  frontend/src/*   → COORD_FRONTEND
  tests/*          → COORD_QUALITY
  .claude/docs/*   → COORD_OPS

INTEGRATION POINTS (ALWAYS SERIALIZE):
  - Database migrations (alembic)
  - API contract changes
  - Release milestones
  - Security/compliance validation

COORDINATOR CAPACITY:
  ORCHESTRATOR → 6 coordinators max parallel
  Coordinator  → 3-8 specialists max parallel
  System-wide  → ~24-48 parallel streams
```

---

***REMOVED******REMOVED*** Anti-Patterns

***REMOVED******REMOVED******REMOVED*** 1. Premature Parallelism

```
❌ BAD: "Just run everything in parallel and merge"
   Result: Conflicts, rework, inconsistent state

✓ GOOD: Check dependency graph before parallelizing
   Result: Clean execution, no conflicts
```

***REMOVED******REMOVED******REMOVED*** 2. Over-Serialization

```
❌ BAD: "Wait for each task to complete before starting next"
   Result: 10 hours for 10 tasks that could parallel

✓ GOOD: Only serialize when dependency exists
   Result: 2 hours (5 parallel streams × 2 hours each)
```

***REMOVED******REMOVED******REMOVED*** 3. Ignoring Integration Points

```
❌ BAD: "Continue working while migration runs"
   Result: Code using old schema, conflicts

✓ GOOD: Pause all streams at integration point
   Result: Clean state after migration
```

***REMOVED******REMOVED******REMOVED*** 4. Domain Boundary Violations

```
❌ BAD: COORD_ENGINE modifies frontend/src/
   Result: Conflicts with COORD_FRONTEND

✓ GOOD: COORD_ENGINE signals ORCHESTRATOR for cross-domain work
   Result: Proper coordination via broadcast
```

---

***REMOVED******REMOVED*** Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-28 | Initial PARALLELISM_FRAMEWORK specification |

---

**Maintained By:** TOOLSMITH Agent

**Authority:** Mandatory for all PAI agents

---

*PARALLELISM_FRAMEWORK: Different domains can run parallel. Same domain? Check dependencies.*
