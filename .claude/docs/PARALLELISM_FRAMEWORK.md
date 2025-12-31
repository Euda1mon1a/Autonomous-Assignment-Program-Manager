# PARALLELISM_FRAMEWORK - Decision Rules for Parallel Execution

> **Purpose:** Codified rules for determining parallel vs. serial execution in multi-agent workflows
> **Audience:** All PAI agents (ORCHESTRATOR, Coordinators, Specialists)
> **Authority:** Mandatory - agents MUST follow these rules
> **Version:** 1.0.0
> **Last Updated:** 2025-12-28

---

## Overview

This framework provides deterministic rules for agents to decide when tasks can run in parallel vs. when they must serialize. Following these rules prevents file conflicts, race conditions, and wasted rework.

**Core Principle:** "When in doubt, check the domain. Different domains can run parallel."

---

## Level 1: File Domain Check

### Domain-to-Coordinator Mapping

**Rule:** Specific file mappings take precedence over directory patterns.

```
File Path                                        → Coordinator         → Can Parallel With
────────────────────────────────────────────────────────────────────────────────────────────
# COMPLIANCE EXCEPTIONS (specific files → COORD_RESILIENCE)
backend/app/scheduling/acgme_validator.py        → COORD_RESILIENCE    → All except self
backend/app/scheduling/constraints/acgme*.py     → COORD_RESILIENCE    → All except self
backend/app/services/audit_service.py            → COORD_RESILIENCE    → All except self
backend/app/services/credential_service.py       → COORD_RESILIENCE    → All except self
backend/app/services/compliance*.py              → COORD_RESILIENCE    → All except self

# DIRECTORY PATTERNS (apply when no specific match above)
backend/app/scheduling/*                         → COORD_ENGINE        → All except self
backend/app/resilience/*                         → COORD_RESILIENCE    → All except self
backend/app/api/*                                → COORD_PLATFORM      → All except self
backend/app/services/*                           → COORD_PLATFORM      → All except self
backend/app/models/*                             → COORD_PLATFORM      → All except self
backend/alembic/*                                → COORD_PLATFORM      → NONE (serialized)
frontend/src/*                                   → COORD_FRONTEND      → All except self
backend/tests/*                                  → COORD_QUALITY       → All except self
frontend/__tests__/*                             → COORD_QUALITY       → All except self
.claude/*                                        → COORD_OPS           → All except self
docs/*                                           → COORD_OPS           → All except self
```

> **Why compliance exceptions?** ACGME validation, audit trails, and credential checking are safety-critical.
> These files MUST route to COORD_RESILIENCE regardless of their directory location to ensure the compliance
> gate is never bypassed.

### Decision Rule

```python
def can_run_parallel(task_a: Task, task_b: Task) -> bool:
    """Level 1: Check if tasks operate on different domains."""

    domain_a = get_coordinator_domain(task_a.files)
    domain_b = get_coordinator_domain(task_b.files)

    # Different domains = safe to parallel
    if domain_a != domain_b:
        return True

    # Same domain = proceed to Level 2 check
    return check_level_2_dependencies(task_a, task_b)
```

---

## Level 2: Dependency Graph Check

When tasks are in the same domain, check for output→input dependencies.

### Dependency Types

| Dependency Type | Description | Action |
|-----------------|-------------|--------|
| **Data Flow** | Task B needs Task A's output | SERIALIZE (A → B) |
| **Write-Read** | Task B reads files Task A writes | SERIALIZE (A → B) |
| **Write-Write** | Both tasks write same file | SERIALIZE (pick one) |
| **Read-Read** | Both tasks read same file | PARALLEL OK |
| **Independent** | No shared files or data | PARALLEL OK |

### Decision Rule

```python
def check_level_2_dependencies(task_a: Task, task_b: Task) -> bool:
    """Level 2: Check for output→input dependencies."""

    # Check if B needs A's output
    if task_b.inputs.intersection(task_a.outputs):
        return False  # Serialize: A before B

    # Check if A needs B's output
    if task_a.inputs.intersection(task_b.outputs):
        return False  # Serialize: B before A

    # Check write conflicts
    if task_a.writes.intersection(task_b.writes):
        return False  # Serialize: conflict

    # Check write-then-read
    if task_a.writes.intersection(task_b.reads):
        return False  # Serialize: A before B

    if task_b.writes.intersection(task_a.reads):
        return False  # Serialize: B before A

    # No dependencies found
    return True  # PARALLEL OK
```

### Common Dependency Patterns

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

## Level 3: Integration Point Check

Certain milestones require all streams to converge before proceeding.

### Integration Points (Serialize Here)

| Integration Point | Trigger | Required Coordination |
|-------------------|---------|----------------------|
| **Database Migration** | `alembic revision` or model changes | ALL agents pause, DBA executes |
| **API Contract Change** | Schema change affecting frontend | COORD_PLATFORM + COORD_FRONTEND sync |
| **Release Milestone** | PR merge, version bump | ALL streams converge via SYNTHESIZER |
| **Compliance Validation** | Before any schedule commit | COORD_RESILIENCE validates ALL changes |
| **Security Audit** | Before auth/data changes | COORD_RESILIENCE reviews ALL streams |

### Decision Rule

```python
def is_integration_point(task: Task) -> bool:
    """Level 3: Check if this is an integration milestone."""

    INTEGRATION_TRIGGERS = [
        "alembic",           # Database migration
        "api_contract",      # API schema change
        "release",           # Version/deployment
        "schedule_commit",   # Schedule to production
        "auth_change",       # Authentication modification
        "model_change",      # SQLAlchemy model modification
    ]

    return any(trigger in task.tags for trigger in INTEGRATION_TRIGGERS)

def handle_integration_point(task: Task, active_streams: list) -> Action:
    """Coordinate integration point."""

    # Signal all active streams to pause at safe checkpoint
    for stream in active_streams:
        stream.signal_checkpoint()

    # Wait for all streams to reach checkpoint
    await asyncio.gather(*[s.await_checkpoint() for s in active_streams])

    # Execute integration task
    result = await execute_integration(task)

    # Signal all streams to resume
    for stream in active_streams:
        stream.signal_resume()

    return result
```

---

## Level 4: Speculative Parallelism (Read Optimization)

While Levels 1-3 focus on write conflict prevention, Level 4 optimizes read operations for maximum parallelism.

### When to Use Speculative Reads

Apply speculative parallelism when:
- Exploring a feature across multiple files
- Debugging interconnected components
- Initial research phase for new capability
- Uncertainty about which files are needed

### The Pattern

1. **Identify candidates** - List 5-10 likely-needed files (don't overthink)
2. **Batch read** - Read ALL in single parallel request
3. **Process together** - Analyze results in unified context
4. **No penalty** - Extra reads have negligible latency cost

### Example: Understanding Swap Feature

Instead of reading sequentially:
```
Read swap_service.py
→ "Ah, I need the models"
Read swap_models.py
→ "Ah, I need the routes"
Read swap_routes.py
→ "Ah, I need the tests"
```

Speculative parallel read:
```
Read in parallel:
├── swap_service.py      (core logic)
├── swap_models.py       (data structures)
├── swap_routes.py       (API interface)
├── swap_auto_matcher.py (matching algorithm)
└── test_swap*.py        (tests reveal intent)
```

### Decision Rule

```python
def use_speculative_reads(task: Task) -> bool:
    """Should we speculatively read multiple files?"""

    SPECULATIVE_TRIGGERS = [
        task.phase == "exploration",
        "understand" in task.goal.lower(),
        "debug" in task.goal.lower(),
        "investigate" in task.goal.lower(),
        not task.exact_files_known,
    ]

    return any(SPECULATIVE_TRIGGERS)
```

### Anti-Pattern

| BAD | GOOD |
|--------|---------|
| Read A, then decide to read B, then C | Batch read [A, B, C, D, E] upfront |
| 3 sequential round trips | 1 parallel round trip |
| ~3x latency | ~1x latency |

### Integration with Explore Subagent

The `Explore` subagent type is optimized for speculative reads:
- Fast model (haiku/sonnet)
- Context-aware (sees prior conversation)
- Pattern: Spawn multiple Explore agents with different search foci

---

## Decision Tree for All Agents

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

## Coordinator Internal Parallelism

Each coordinator manages parallelism within their domain.

### COORD_ENGINE Example

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

### COORD_PLATFORM Example

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

### COORD_QUALITY Example

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

## Stream Integration via SYNTHESIZER

When parallel streams complete, SYNTHESIZER integrates results.

### Integration Protocol

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

### SYNTHESIZER Checklist

1. **Collect:** Receive completion signals from all active coordinators
2. **Validate:** Check for conflicts (same files modified, incompatible changes)
3. **Resolve:** If conflicts, escalate to ORCHESTRATOR with options
4. **Merge:** Create unified deliverable (PR, report, deployment package)
5. **Report:** Briefing to ORCHESTRATOR for final approval

---

## Quick Reference Card

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

## Anti-Patterns

### 1. Premature Parallelism

```
❌ BAD: "Just run everything in parallel and merge"
   Result: Conflicts, rework, inconsistent state

✓ GOOD: Check dependency graph before parallelizing
   Result: Clean execution, no conflicts
```

### 2. Over-Serialization

```
❌ BAD: "Wait for each task to complete before starting next"
   Result: 10 hours for 10 tasks that could parallel

✓ GOOD: Only serialize when dependency exists
   Result: 2 hours (5 parallel streams × 2 hours each)
```

### 3. Ignoring Integration Points

```
❌ BAD: "Continue working while migration runs"
   Result: Code using old schema, conflicts

✓ GOOD: Pause all streams at integration point
   Result: Clean state after migration
```

### 4. Domain Boundary Violations

```
❌ BAD: COORD_ENGINE modifies frontend/src/
   Result: Conflicts with COORD_FRONTEND

✓ GOOD: COORD_ENGINE signals ORCHESTRATOR for cross-domain work
   Result: Proper coordination via broadcast
```

### 5. Single Validator Bottleneck

```
❌ BAD: N × TOOLSMITH parallel → 1 × COORD_QUALITY validates all
   Result: Validation bottleneck, not tailored per artifact

✓ GOOD: N × COORD_QUALITY parallel (each managing own team)
   Result: Maximum parallelism with quality gates preserved
```

---

## Agent Modification Patterns

Two patterns for agent creation/modification work:

| Pattern | Use When | Key Characteristic |
|---------|----------|-------------------|
| **Team Lead** | Creating NEW agents | One COORD_QUALITY per agent (full lifecycle) |
| **Batch Augmentation** | Updating EXISTING agents | Parallel TOOLSMITH, single COORD_QUALITY validation |

---

### Pattern 1: Team Lead (New Agent Creation)

**Use when:** Creating multiple NEW agents from scratch.

**Why:** Each new agent is a distinct deliverable needing full lifecycle management.

```
G4_LIBRARIAN (advisor - inventory of existing agents, patterns, gaps)
    ↓
AGENT_FACTORY (executive - designs N specs, informed by LIBRARIAN)
    ↓
N × COORD_QUALITY (parallel middle managers - one per agent)
    │
    ├── COORD_QUALITY_1 → TOOLSMITH_1 → QA_TESTER_1 → CODE_REVIEWER_1 → report
    ├── COORD_QUALITY_2 → TOOLSMITH_2 → QA_TESTER_2 → CODE_REVIEWER_2 → report
    ├── COORD_QUALITY_3 → TOOLSMITH_3 → QA_TESTER_3 → CODE_REVIEWER_3 → report
    └── ... (all teams run in parallel)
    ↓
AGENT_FACTORY (collects reports from all middle managers)
    ↓
G4_LIBRARIAN (post-creation inventory update, reference verification)
```

**G4_LIBRARIAN's Role:**

| Phase | G4_LIBRARIAN Contribution |
|-------|--------------------------|
| **Pre-creation** | Advise on existing patterns, naming conventions, capability gaps |
| **Design review** | Flag potential duplicates or overlaps with existing agents |
| **Post-creation** | Update FILE_INVENTORY_REPORT, verify all references valid |

**Principles:**

| Principle | Description |
|-----------|-------------|
| **COORD_QUALITY = Middle Management** | Each instance oversees ONE team of 3 |
| **Teams Run in Parallel** | Spawn as many COORD_QUALITY as you have new agents |
| **Sequential Within Team** | TOOLSMITH → QA_TESTER → CODE_REVIEWER (quality gates) |
| **Tailor-Made Teams** | Each COORD_QUALITY customizes pipeline for their agent |

**Example: Creating 3 New Agents**

```python
# AGENT_FACTORY spawns 3 parallel COORD_QUALITY teams
for agent_spec in [CI_LIAISON, DOMAIN_ANALYST, CRASH_RECOVERY_SPECIALIST]:
    Task(
        description=f"COORD_QUALITY: Team Lead for {agent_spec.name}",
        prompt=f"""
        ## Agent: COORD_QUALITY (Team Lead)

        You own the full lifecycle for creating {agent_spec.name}.

        Run this pipeline SEQUENTIALLY within your team:
        1. Spawn TOOLSMITH to create the agent spec
        2. After TOOLSMITH completes, spawn QA_TESTER to validate
        3. After QA_TESTER passes, spawn CODE_REVIEWER for quality

        Report back to AGENT_FACTORY with: APPROVED or NEEDS_REVISION

        Spec to implement:
        {agent_spec.details}
        """,
        subagent_type="general-purpose"
    )
# All 3 COORD_QUALITY teams run in PARALLEL
# Each team runs TOOLSMITH → QA → REVIEW sequentially
```

---

### Pattern 2: Batch Augmentation (Existing Agent Updates)

**Use when:** Augmenting/updating multiple EXISTING agents with similar changes.

**Why:** Changes are uniform, same validation criteria, cross-artifact consistency matters.

```
G4_LIBRARIAN (advisor - current state of agents to be modified)
    ↓
FORCE_MANAGER (defines augmentation specs, informed by LIBRARIAN)
    ↓
N × TOOLSMITH (parallel - each updates one agent)
    ↓
1 × COORD_QUALITY (validates entire batch)
    │
    ├── QA_TESTER: Structural validation across all N
    └── CODE_REVIEWER: Quality review across all N (can run parallel with QA)
    ↓
G4_LIBRARIAN (post-augmentation inventory update, reference verification)
```

**G4_LIBRARIAN's Role (Augmentation):**

| Phase | G4_LIBRARIAN Contribution |
|-------|--------------------------|
| **Pre-augmentation** | Provide current state of target agents, existing references |
| **Conflict detection** | Flag if augmentations might break existing references |
| **Post-augmentation** | Update inventory, verify no broken references introduced |

**Principles:**

| Principle | Description |
|-----------|-------------|
| **Parallel Creation** | N TOOLSMITH agents run simultaneously |
| **Batch Validation** | Single COORD_QUALITY validates all changes together |
| **Cross-Artifact Consistency** | Validator can check for conflicts between changes |
| **Efficient for Homogeneous Work** | Same validation checklist applies to all |

**Example: Augmenting 4 Existing Agents (Session 023)**

```python
# Spawn TOOLSMITH agents in parallel for each augmentation
augmentations = [
    ("COORD_AAR", "Add auto-trigger mechanism"),
    ("FORCE_MANAGER", "Add Workflow 5: Parallelization Scoring"),
    ("G2_RECON", "Add domain mapping to reconnaissance"),
    ("DELEGATION_AUDITOR", "Add real-time proactive mode"),
]

for agent, change in augmentations:
    Task(
        description=f"TOOLSMITH: Augment {agent}",
        prompt=f"Add {change} to {agent}.md",
        subagent_type="general-purpose"
    )
# All 4 TOOLSMITH run in PARALLEL

# After all complete, single COORD_QUALITY validates batch
Task(
    description="COORD_QUALITY: Validate all augmentations",
    prompt="""
    Validate all 4 augmentations for:
    - Markdown integrity (no duplicates, proper formatting)
    - Section placement (logical location)
    - Cross-artifact consistency (no conflicts)
    - Pattern compliance
    """,
    subagent_type="general-purpose"
)
```

---

### Decision Guide: Which Pattern?

```
Are you creating NEW agents from scratch?
    │
    YES → Team Lead Pattern (N × COORD_QUALITY teams)
    │
    NO
    │
    ▼
Are you augmenting EXISTING agents with similar changes?
    │
    YES → Batch Augmentation Pattern (N × TOOLSMITH → 1 × COORD_QUALITY)
    │
    NO
    │
    ▼
Mixed (some new, some augmentations)?
    │
    → Split into two parallel workstreams:
        ├── Stream A: Team Lead for new agents
        └── Stream B: Batch Augmentation for updates
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 2025-12-30 | Added G4_LIBRARIAN as advisor to both patterns (pre/post creation) |
| 1.2.0 | 2025-12-30 | Split into Team Lead (new) vs Batch Augmentation (existing) patterns with decision guide |
| 1.1.0 | 2025-12-30 | Added Team Lead Pattern, Anti-Pattern #5 (Single Validator Bottleneck) |
| 1.0.0 | 2025-12-28 | Initial PARALLELISM_FRAMEWORK specification |

---

**Maintained By:** TOOLSMITH Agent

**Authority:** Mandatory for all PAI agents

---

*PARALLELISM_FRAMEWORK: Different domains can run parallel. Same domain? Check dependencies.*
