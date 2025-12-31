# Skills Parallel Hints Guide - Comprehensive Documentation

> **Purpose:** Complete documentation of parallel execution annotations across the PAI (Personal AI Infrastructure) skill ecosystem
> **Session:** 025 Signal Amplification (Session 9 Continuation)
> **Status:** Reference & Best Practices
> **Last Updated:** 2025-12-30
> **Scope:** 10 annotated skills, zero marginal cost philosophy, multi-agent coordination

---

## Table of Contents

1. [Overview & Philosophy](#overview--philosophy)
2. [Current Annotations (10 Skills)](#current-annotations-10-skills)
3. [Annotation Pattern Reference](#annotation-pattern-reference)
4. [Skill Compatibility Matrix](#skill-compatibility-matrix)
5. [Domain-Based Parallelization](#domain-based-parallelization)
6. [Batch Size Optimization](#batch-size-optimization)
7. [Serialization Requirements](#serialization-requirements)
8. [Best Practices & Patterns](#best-practices--patterns)
9. [Multi-Agent Coordination Workflows](#multi-agent-coordination-workflows)
10. [Future Annotation Roadmap](#future-annotation-roadmap)

---

## Overview & Philosophy

### Zero Marginal Cost Principle

Parallel execution in multi-agent systems operates under the **zero marginal cost principle**:

> When Task A and Task B operate on **different domains** (different files, different coordinators), running them simultaneously has **zero additional resource cost** to the system.

This principle enables:
- **Massive parallelization**: 10 agents × 3 skills each = 30 concurrent operations
- **Speed multiplication**: Sequential execution (30 min) → Parallel (3 min)
- **Resource efficiency**: Uses existing CPU/memory with better utilization
- **Quality improvement**: Parallel code review + security audit catches issues sequentially review misses

### Annotation Metadata

Every skill has optional **parallel_hints** metadata in YAML frontmatter:

```yaml
---
name: skill-name
parallel_hints:
  can_parallel_with: [list_of_skills]
  must_serialize_with: [list_of_skills]
  preferred_batch_size: N
---
```

**Why annotate?**
1. **Explicit permission** - Agents don't have to guess
2. **Performance optimization** - Route to parallel agents vs sequential queue
3. **Safety gates** - Prevent conflicts (database migrations must serialize)
4. **Batch intelligence** - Group similar work for efficiency

---

## Current Annotations (10 Skills)

### 1. test-writer

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, lint-monorepo, security-audit]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

**Domain:** development/testing
**Domain Coordinator:** COORD_QUALITY (backend/tests/*, frontend/__tests__/*)

**Rationale:**
- Different test files don't conflict
- Safe to run with code-review (tests validate code)
- Cannot run with database-migration (migration order matters)

**Real-World Scenarios:**
- Write unit tests for service A (file: `test_service_a.py`)
- Write unit tests for service B (file: `test_service_b.py`)
- **Parallel OK** - Different test files, can batch 3 in parallel

---

### 2. code-review

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [test-writer, security-audit, lint-monorepo]
  must_serialize_with: [database-migration]
  preferred_batch_size: 5
```

**Domain:** development/quality
**Domain Coordinator:** COORD_QUALITY

**Rationale:**
- Quality gates are independent
- Multiple reviewers provide better coverage
- Cannot block on database schema changes

**Real-World Scenarios:**
- Review API endpoint file
- Review frontend component file
- Review service logic file
- **Parallel OK** - All quality checks independent, highest batch size

---

### 3. security-audit

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer, lint-monorepo]
  must_serialize_with: []
  preferred_batch_size: 3
```

**Domain:** security/compliance
**Domain Coordinator:** COORD_RESILIENCE (auth, data handling)

**Rationale:**
- Only serializes with: nothing (most flexible)
- Security checks are non-blocking
- Can run on any file domain

**Real-World Scenarios:**
- Audit authentication code
- Audit data handling in service
- Audit API endpoint
- **Parallel OK** - Security review is orthogonal to all domains

---

### 4. lint-monorepo

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer, security-audit]
  must_serialize_with: []
  preferred_batch_size: 10
```

**Domain:** development/tooling
**Domain Coordinator:** COORD_QUALITY

**Rationale:**
- Linting is independent across files
- Highest batch size (10) - can lint many files
- No serialization requirements

**Real-World Scenarios:**
- Lint backend Python files
- Lint frontend TypeScript files
- Lint tests
- **Parallel OK** - Runs ruff and eslint independently

---

### 5. fastapi-production

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [test-writer, security-audit, code-review]
  must_serialize_with: [database-migration]
  preferred_batch_size: 5
```

**Domain:** development/backend
**Domain Coordinator:** COORD_PLATFORM (backend/app/api/*, backend/app/services/*)

**Rationale:**
- Multiple endpoints can be built in parallel
- Cannot change schema while implementing endpoints
- Tests written concurrently

**Real-World Scenarios:**
- Implement GET /schedules endpoint
- Implement POST /schedules endpoint
- Implement PUT /schedules/{id} endpoint
- **Parallel OK** - Different endpoints, same API layer

---

### 6. automated-code-fixer

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [lint-monorepo, test-writer]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

**Domain:** development/automation
**Domain Coordinator:** COORD_QUALITY

**Rationale:**
- Fixes can be applied to different files
- Limited batch (3) - fixes are high-impact, want to verify each
- Cannot run during schema changes

**Real-World Scenarios:**
- Fix type errors in service A
- Fix lint errors in component B
- Fix test failures in route C
- **Parallel OK** - Different files, but batch small for safety

---

### 7. docker-containerization

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [security-audit, code-review]
  must_serialize_with: [database-migration]
  preferred_batch_size: 2
```

**Domain:** infrastructure/containers
**Domain Coordinator:** COORD_PLATFORM

**Rationale:**
- Container work often depends on code
- Low batch (2) - container decisions are interdependent
- Security review of Dockerfile runs in parallel

**Real-World Scenarios:**
- Optimize backend Dockerfile
- Configure health checks (can run with code-review)
- **Parallel OK with caution** - Container decisions may cascade

---

### 8. database-migration

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: []
  must_serialize_with: [code-review, test-writer, automated-code-fixer]
  preferred_batch_size: 1
```

**Domain:** infrastructure/database
**Domain Coordinator:** COORD_PLATFORM

**Rationale:**
- **Most restrictive annotation**
- Database schema is the critical bottleneck
- Must be first/only operation
- All code changes wait for migrations

**Real-World Scenarios:**
- Add column to Person table
- Create foreign key relationship
- **Serialized only** - No parallelization possible
- Others wait for completion

---

### 9. pr-reviewer

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, security-audit]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

**Domain:** workflow/git
**Domain Coordinator:** COORD_OPS

**Rationale:**
- Final review stage before merge
- Can run with code-review (provides additional perspective)
- Limited batch (3) - PRs are discrete units

**Real-World Scenarios:**
- Review PR #123 (code-review + security audit in parallel)
- Review PR #124 (independent PR)
- **Parallel OK** - Different PRs, coordination at merge

---

### 10. MCP_ORCHESTRATION

**Metadata:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer, security-audit]
  must_serialize_with: [database-migration]
  preferred_batch_size: 5
```

**Domain:** meta/orchestration
**Domain Coordinator:** COORD_OPS (manages all MCP tool invocations)

**Rationale:**
- MCP tools operate independently
- Can orchestrate while code review happens
- Cannot change data schema mid-orchestration

**Real-World Scenarios:**
- Generate schedule while code reviewed
- Validate compliance while tests run
- Run N-1 analysis while feature developed
- **Parallel OK** - MCP is coordination layer

---

## Annotation Pattern Reference

### Pattern 1: Independent Quality Checks (test-writer, code-review, security-audit, lint-monorepo)

**Characteristic Pattern:**
```yaml
can_parallel_with: [test-writer, code-review, security-audit, lint-monorepo]
must_serialize_with: []
preferred_batch_size: 5-10
```

**Use Case:** Multiple independent auditors checking different aspects
**Coordination:** Converge at PR merge gate

**Example Workflow:**
```
1. Backend develops feature
2. PARALLEL:
   - test-writer creates tests
   - code-review checks architecture
   - security-audit checks vulnerabilities
   - lint-monorepo fixes style
3. All reports converge at pr-reviewer
4. Single merge decision
```

---

### Pattern 2: Code → Test Dependency (fastapi-production → test-writer)

**Characteristic Pattern:**
```yaml
# fastapi-production
can_parallel_with: [test-writer, ...]
must_serialize_with: [database-migration]

# test-writer
can_parallel_with: [code-review, ...]
must_serialize_with: [database-migration]
```

**Use Case:** Implementation-driven testing
**Coordination:** Can overlap (TDD pattern) or sequence (spec-driven)

**Example Workflow:**
```
Option A - Parallel (TDD):
1. test-writer writes test for API contract
2. fastapi-production implements API
3. Tests execute immediately

Option B - Sequential (Spec-driven):
1. fastapi-production designs API schema
2. test-writer writes tests to spec
3. fastapi-production implements
```

---

### Pattern 3: Database Serialization (database-migration)

**Characteristic Pattern:**
```yaml
# database-migration
can_parallel_with: []
must_serialize_with: [ALL SKILLS]
preferred_batch_size: 1
```

**Use Case:** Single bottleneck for all schema changes
**Coordination:** Mandatory pause point in workflows

**Example Workflow:**
```
Sequential Phase:
1. All agents pause
2. DBA executes: database-migration
   - Modify model
   - Create migration
   - Test rollback
   - Apply migration
3. All agents resume

Key constraint: NOTHING runs while migration is being applied
Violation = silent data corruption
```

---

### Pattern 4: Domain-Based Parallelization

**Characteristic Pattern:**
```yaml
# Backend skill
domain: development/backend
can_parallel_with: [code-review, test-writer]  # Also in dev/quality

# Frontend skill
domain: development/frontend
can_parallel_with: [code-review, test-writer]  # Different domain, OK
```

**Use Case:** Backend development independent of frontend
**Coordination:** Interface contract agreed upfront

**Example Workflow:**
```
PARALLEL:
- Backend develops GET /api/schedules endpoint
- Frontend develops Schedule List component
- Both write tests independently
- QA_TESTER writes integration tests (waits for both)

Convergence: Integration testing when both domains ready
```

---

## Skill Compatibility Matrix

### Complete 10×10 Matrix

|  | test-writer | code-review | security-audit | lint-monorepo | fastapi-production | automated-code-fixer | docker-containerization | database-migration | pr-reviewer | MCP_ORCHESTRATION |
|--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **test-writer** | N | Y | Y | Y | Y | Y | - | N | Y | Y |
| **code-review** | Y | N | Y | Y | Y | Y | Y | N | Y | Y |
| **security-audit** | Y | Y | N | Y | Y | Y | Y | - | Y | Y |
| **lint-monorepo** | Y | Y | Y | N | Y | Y | - | - | Y | Y |
| **fastapi-production** | Y | Y | Y | Y | N | Y | Y | N | Y | Y |
| **automated-code-fixer** | Y | Y | Y | Y | Y | N | - | N | Y | Y |
| **docker-containerization** | - | Y | Y | - | Y | - | N | N | - | Y |
| **database-migration** | N | N | - | - | N | N | N | N | N | N |
| **pr-reviewer** | Y | Y | Y | Y | Y | Y | - | N | N | Y |
| **MCP_ORCHESTRATION** | Y | Y | Y | Y | Y | Y | Y | N | Y | N |

**Legend:**
- `Y` = Can parallel
- `N` = Must serialize (wait)
- `-` = No interaction / not applicable
- `N` = (database-migration row) = nothing can parallel with DB migration

---

### How to Read Matrix

**Question:** Can I run code-review and fastapi-production in parallel?

**Answer:** Look at (code-review, fastapi-production) cell → **Y** = Yes, they can run in parallel

**Question:** Can I run fastapi-production and database-migration in parallel?

**Answer:** Look at (fastapi-production, database-migration) cell → **N** = No, must serialize (fastapi waits for migration)

---

## Domain-Based Parallelization

### Coordinator Domains (from PARALLELISM_FRAMEWORK.md)

Skills map to coordinators by their file domains:

```
COORD_QUALITY (backend/tests/*, frontend/__tests__/*)
├── test-writer
├── code-review
├── lint-monorepo
└── automated-code-fixer (for test/quality failures)

COORD_PLATFORM (backend/app/*, alembic/*)
├── fastapi-production
├── database-migration
├── docker-containerization
├── automated-code-fixer (for code failures)
└── MCP_ORCHESTRATION (cross-domain)

COORD_RESILIENCE (auth, data handling, compliance)
├── security-audit
└── COMPLIANCE_VALIDATION (not yet annotated)

COORD_OPS (.claude/*, docs/*)
├── pr-reviewer
└── session-documentation (not yet annotated)
```

### Same-Domain Execution Rules

**Rule:** Skills in the **same coordinator domain** can often parallelize IF they don't write conflicting files.

**Example - COORD_QUALITY (No Conflict):**
```
Scenario: Multiple test files
- test_service_a.py (test-writer)
- test_service_b.py (test-writer)
- test_integration.py (test-writer)

Result: PARALLEL OK - Different files, same domain
```

**Example - COORD_QUALITY (Conflict):**
```
Scenario: Code file and its test
- service_a.py (fastapi-production creates)
- test_service_a.py (test-writer creates)

Result: PARALLEL OK - TDD allows overlap
         Service can be written spec-driven
         Test written to spec concurrently
```

**Example - COORD_PLATFORM (Conflict):**
```
Scenario: Model change and API endpoint
- backend/app/models/person.py (modify)
- backend/app/api/routes/person.py (create endpoint)

Result: SERIALIZE - Must order as:
  1. database-migration (if model changes)
  2. fastapi-production (implements endpoint with new schema)
```

---

## Batch Size Optimization

### Batch Size Strategy

**Concept:** Preferred batch size = how many instances of same skill can execute concurrently

### Size By Skill

| Skill | Batch Size | Reasoning |
|-------|:--:|-----------|
| **test-writer** | 3 | Multiple test suites, moderate coordination overhead |
| **code-review** | 5 | Most independent, highest parallelization potential |
| **security-audit** | 3 | Medium complexity, requires careful attention |
| **lint-monorepo** | 10 | Lowest overhead, can process many files |
| **fastapi-production** | 5 | Multiple endpoints, moderate schema coordination |
| **automated-code-fixer** | 3 | High-impact fixes, want verification of each |
| **docker-containerization** | 2 | Container decisions cascade, limited parallelization |
| **database-migration** | 1 | ALWAYS serialized, only one at a time |
| **pr-reviewer** | 3 | PRs are discrete units |
| **MCP_ORCHESTRATION** | 5 | Tool chains are independent |

### Batch Size Computation

**Formula:**
```
Effective_Batch_Size = min(
    preferred_batch_size,                    # From annotation
    available_agents_with_skill,             # How many agents available
    ceiling(total_tasks / estimated_time)    # Throughput optimization
)
```

**Example:**
```
Scenario: Need to write tests for 12 modules
  preferred_batch_size: 3
  available agents: 4 (ORCHESTRATOR can spawn 4)
  total_tasks: 12
  estimated_time_per_module: 2 minutes

Effective_Batch_Size = min(3, 4, 12/2) = min(3, 4, 6) = 3
Result: Spawn 3 test-writer agents, 4 modules per agent
Timeline: 2 + 2 minutes = 4 minutes total (vs 24 minutes sequential)
```

---

## Serialization Requirements

### Absolute Serialization (database-migration)

**Definition:** Operations that MUST NOT run in parallel with ANY other skill

```
database-migration MUST SERIALIZE WITH: [all 9 other skills]
Reason: Schema is the contract between all layers

Violation Scenarios:
1. fastapi-production writes endpoint using old schema
   while database-migration changes schema
   Result: Runtime type mismatch, silent failures

2. test-writer writes test for old schema
   while database-migration changes schema
   Result: Tests fail immediately after migration

3. code-review validates code against old schema
   while database-migration changes schema
   Result: Approved code is now non-compliant
```

### Soft Serialization Requirements

**Definition:** Skills that should wait for each other to avoid rework

**Example - fastapi-production must wait for database-migration:**
```yaml
# In fastapi-production SKILL.md
must_serialize_with: [database-migration]

Reasoning:
- Cannot implement endpoint without knowing schema
- If schema changes mid-implementation, rework required
- If test written to old schema, tests fail

Workflow:
1. database-migration completes (schema locked)
2. fastapi-production starts (schema known)
3. test-writer starts (tests written to schema)
```

### No Serialization (security-audit)

**Definition:** Skills with zero serialization requirements

```yaml
# In security-audit SKILL.md
must_serialize_with: []

Reasoning:
- Security review is orthogonal to schema/architecture
- Can audit code before, during, after any other operation
- Security findings don't invalidate other work
- Can run first (proactive) or last (gate)
```

---

## Best Practices & Patterns

### Pattern 1: Converging Quality Gates

**Scenario:** Merge gate requires all quality checks before PR approval

**Setup:**
```
Quality Skills (can all parallelize):
✓ test-writer (write/run tests)
✓ code-review (check quality)
✓ security-audit (check security)
✓ lint-monorepo (check style)

Workflow:
1. PARALLEL spawn:
   - test_agent = test-writer (run tests)
   - review_agent = code-review (check code)
   - security_agent = security-audit (check security)
   - lint_agent = lint-monorepo (check style)

2. Wait for all (convergence point)
3. Synthesize results:
   - All tests passing? ✓
   - Code quality good? ✓
   - No security issues? ✓
   - Style compliant? ✓

4. Approve PR → merge
```

**Time Benefit:**
```
Sequential: 2 + 3 + 2 + 1 = 8 minutes
Parallel:   max(2, 3, 2, 1) = 3 minutes
Speedup:    2.67x
```

---

### Pattern 2: Schema-Locked Implementation

**Scenario:** Implement features after schema is finalized

**Setup:**
```
Blocking Skill (database-migration) + Implementation Skills
- database-migration (create/modify schema)
- fastapi-production (implement endpoints)
- test-writer (write tests)
- frontend-development (build UI) [NOT YET ANNOTATED]

Workflow:
1. SERIALIZE: database-migration
   - DBA modifies Person model
   - Creates alembic migration
   - Tests migration/rollback
   - Applies to database

2. PARALLEL spawn (after migration complete):
   - backend_agent = fastapi-production (implement GET /persons)
   - test_agent = test-writer (test endpoints)
   - frontend_agent = frontend-development (build PersonList)

3. Integration testing when all ready
```

**Safety Benefit:**
```
Prevents: Schema changes during implementation
Protection: All code operates on locked schema
Verification: Tests written to stable schema won't fail from schema drift
```

---

### Pattern 3: Isolated Security Audit

**Scenario:** Run security audit without waiting for other work

**Setup:**
```
security-audit can parallelize with everything (no must_serialize_with)

Workflow:
1. Code pushed to review branch
2. IMMEDIATE spawn: security-audit
3. In parallel, other work:
   - code-review
   - test-writer
   - lint-monorepo
   - fastapi-production (if continuing dev)

4. Security report available before other reviews
   IF SECURITY ISSUES: fail fast, block merge
   IF SECURITY OK: proceed with other gates
```

**Risk Mitigation Benefit:**
```
Traditional: Security review is last gate (blocks merge longest)
New approach: Security review is independent (can fail early)
Benefit: Problems found before code review is complete
Speed: No waiting for code review to start security
```

---

### Pattern 4: Fault-Tolerant Batch Processing

**Scenario:** Process 10 modules with automated-code-fixer (batch size 3)

**Setup:**
```
Task: Fix linting errors in 10 modules
Skill: automated-code-fixer (batch size: 3)

Workflow:
Wave 1 (parallel): Fix modules [1, 2, 3]
  Results: ✓ 1 fixed, ✓ 2 fixed, ✗ 3 failed
  Action: Log failure, continue

Wave 2 (parallel): Fix modules [4, 5, 6]
  Results: ✓ 4 fixed, ✓ 5 fixed, ✓ 6 fixed
  Action: Continue

Wave 3 (parallel): Fix modules [7, 8, 9]
  Results: ✓ 7 fixed, ✓ 8 fixed, ✓ 9 fixed
  Action: Continue

Wave 4 (sequential): Fix module [3]
  Results: ✓ 3 fixed (manual intervention)
  Action: Review why batch failed

Summary: 9/10 modules fixed in waves, 1 required special handling
```

**Resource Efficiency:**
```
Batch size 3 means never more than 3 fixer agents
Wave 1-3: 3 agents active
Wave 4: 1 agent active
Memory peak: Constant (only 3 agents concurrent)
```

---

## Multi-Agent Coordination Workflows

### Workflow 1: Full Feature Development (with Serialization)

**Narrative:** Building new schedule export feature with database changes

**Architecture:**
```
ORCHESTRATOR
├── Database Specialist (database-migration)
├── Backend Specialist (fastapi-production)
├── Test Specialist (test-writer)
├── Quality Gate Specialist (code-review, security-audit)
└── Deployment Specialist (docker-containerization, pr-reviewer)
```

**Timeline:**

```
T=0:00  ┌─ ORCHESTRATOR receives: "Add schedule PDF export"
        └─ Analyzes: Needs schema? Yes. Database-migration blocks.

T=0:05  ┌─ SERIALIZE: Database Specialist
        │  - Add export_format column to Assignment
        │  - Create migration, test rollback
        │  └─ Completes T=2:30

T=2:35  └─ SCHEMA LOCKED, unblock:

        ┌─────────────────────────────────────────────────────┐
T=2:35  │ PARALLEL: 4 agents spawn (no conflicts after schema) │
        ├─ Backend Specialist (fastapi-production)            │
        │  ├─ Implement GET /schedules/export endpoint       │
        │  ├─ Add PDF generation logic                         │
        │  └─ Completes T=5:45                               │
        │                                                     │
        ├─ Test Specialist (test-writer)                     │
        │  ├─ Write unit tests for PDF generation            │
        │  ├─ Write integration tests for endpoint           │
        │  └─ Completes T=5:15                               │
        │                                                     │
        ├─ Quality Gate #1 (code-review)                     │
        │  ├─ Check architecture compliance                  │
        │  ├─ Check error handling                           │
        │  └─ Completes T=4:00                               │
        │                                                     │
        ├─ Quality Gate #2 (security-audit)                  │
        │  ├─ Check file permissions                         │
        │  ├─ Check PII handling in export                   │
        │  └─ Completes T=4:30                               │
        │                                                     │
        └─ Quality Gate #3 (lint-monorepo)                   │
           └─ Completes T=1:30                               │
        └─────────────────────────────────────────────────────┘
           (Starts after schema lock, completes independently)

T=5:50  ┌─ CONVERGE: All quality gates ready
        ├─ Test results: ✓ All passing
        ├─ Code review: ✓ Architecture approved
        ├─ Security audit: ✓ No PII leaks
        ├─ Linting: ✓ All compliant
        └─ → Safe to merge

T=5:55  ┌─ Deployment Specialist (pr-reviewer)
        ├─ Generate PR description
        ├─ Check CI status
        └─ Approve for merge

T=6:00  └─ FEATURE COMPLETE (Total: 6 minutes)
           vs Sequential: ~15 minutes
           Speedup: 2.5x
```

---

### Workflow 2: Emergency Hotfix (Prioritized Serialization)

**Narrative:** Critical bug in schedule generation, need hotfix in production

**Constraints:**
- Cannot risk schema changes mid-emergency
- Must complete within 30 minutes
- Full testing non-negotiable

**Timeline:**

```
T=0:00  ┌─ INCIDENT: Schedule generation producing invalid output
        └─ PRIORITY: All agents focus on this

T=0:05  ┌─ Systematic Debugger
        ├─ Identify root cause: Off-by-one in hour calculation
        └─ Completes T=2:00

T=2:05  ├─ DECISION: Is schema change needed? No → proceed
        └─ → Can parallelize all skills (no database-migration)

T=2:10  └─ PARALLEL: 5 agents spawn

        ┌─ Backend Specialist (fastapi-production)
        │  ├─ Fix hour calculation logic (1 line change)
        │  └─ Completes T=3:00
        │
        ├─ Test Specialist (test-writer)
        │  ├─ Write regression test (off-by-one scenarios)
        │  └─ Completes T=4:00
        │
        ├─ Quality Gate (code-review)
        │  ├─ Verify fix is minimal
        │  └─ Completes T=3:30
        │
        ├─ Quality Gate (security-audit)
        │  ├─ Verify no new attack surface
        │  └─ Completes T=3:15
        │
        └─ Linter (lint-monorepo)
           └─ Completes T=1:00

T=4:10  ┌─ CONVERGE: All checks pass
        ├─ Tests: ✓ All passing (including regression)
        ├─ Code review: ✓ Minimal, safe change
        ├─ Security: ✓ No new risks
        └─ Style: ✓ Compliant

T=4:15  ├─ PR Reviewer (pr-reviewer)
        └─ Fast-track approval for hotfix

T=4:20  └─ HOTFIX DEPLOYED (Total: 4.3 minutes)
           Crisis averted, schedule generation restored

Follow-up: Deploy to production with expedited approval
```

---

### Workflow 3: Massive Testing Campaign (Batch Optimization)

**Narrative:** After major refactor, need to test all 50 modules

**Setup:**
```
Task: Test 50 modules
Skill: test-writer (batch size 3)
Available agents: 4 (can spawn up to 4 test-writer instances)
```

**Timeline:**

```
T=0:00  ┌─ ORCHESTRATOR: Analyze 50 modules
        ├─ Group by dependency: [P1 services], [P2 services], [tests]
        └─ Create batch queue (17 batches of 3)

T=0:05  ┌─ Batch Wave 1: Process modules 1-3 (parallel)
        ├─ Agent 1: Write tests for Module 1 (3 min)
        ├─ Agent 2: Write tests for Module 2 (3 min)
        ├─ Agent 3: Write tests for Module 3 (3 min)
        └─ Completes T=3:00

T=3:05  ┌─ Batch Wave 2: Process modules 4-6
        └─ Completes T=6:00 (3 more minutes)

... [Waves 3-15 similar]

T=48:00 ├─ Batch Wave 16: Process modules 49-50 (only 2 modules)
        └─ Completes T=51:00

T=51:05 └─ TEST CAMPAIGN COMPLETE
           50 modules tested in 51 minutes
           vs Sequential: 50 × 3 = 150 minutes
           Speedup: 3x (matches batch size, as expected)
```

**Failure Handling:**

```
Mid-campaign: Module 23 test fails (dependency not available)

Recovery:
T=22:00 ├─ Test failure detected for Module 23
        ├─ Suspend Module 23 processing
        ├─ Fix dependency
        ├─ Retry Module 23 (sequential)
        └─ Resume batch waves with Module 23

Result: Minimal disruption, other modules continue processing
```

---

## Future Annotation Roadmap

### Skills Not Yet Annotated (23 Remaining)

#### Tier 1: Immediate Candidates (High Impact)

These should be annotated in next session:

| Skill | Reason | Estimated parallel_hints |
|-------|--------|---------|
| **frontend-development** | Heavy parallelization potential | `can_parallel_with: [test-writer, code-review, lint-monorepo]` |
| **react-typescript** | Complements frontend-development | `can_parallel_with: [test-writer, security-audit]` |
| **python-testing-patterns** | Advanced testing patterns | `can_parallel_with: [code-review, test-writer]` |
| **constraint-preflight** | Validation before solver | `can_parallel_with: []` (blocks scheduling) |
| **schedule-optimization** | Depends on constraints | `must_serialize_with: [constraint-preflight]` |

#### Tier 2: Medium Priority (Moderate Impact)

| Skill | Reason | Estimated parallel_hints |
|-------|--------|---------|
| **SCHEDULING** | Core scheduling skill | `must_serialize_with: [database-migration]` |
| **COMPLIANCE_VALIDATION** | Safety-critical | `can_parallel_with: []` (gating) |
| **SWAP_EXECUTION** | Operational | `can_parallel_with: [COMPLIANCE_VALIDATION]` |
| **systematic-debugger** | Debugging | `can_parallel_with: [test-writer]` |
| **test-scenario-framework** | E2E testing | `can_parallel_with: [code-review]` |

#### Tier 3: Low Priority (Niche Skills)

| Skill | Reason | Estimated parallel_hints |
|-------|--------|---------|
| **acgme-compliance** | Reference skill | `can_parallel_with: [ALL]` |
| **schedule-verification** | Human review | N/A (manual process) |
| **solver-control** | Monitoring | `can_parallel_with: [test-writer]` |
| **safe-schedule-generation** | Safety critical | `must_serialize_with: [ALL]` |
| **CORE** | Meta-skill | N/A (routing, not execution) |

### Annotation Decision Checklist

**For each skill, ask:**

1. **Can it run with code-review?** (Does code change invalidate it?)
   - Yes → `can_parallel_with: [code-review, ...]`
   - No → `must_serialize_with: [code-review, ...]`

2. **Can it run with test-writer?** (Does schema change invalidate tests?)
   - Yes → `can_parallel_with: [test-writer, ...]`
   - No → `must_serialize_with: [test-writer, ...]`

3. **Must it run with database-migration?** (Is schema required?)
   - Yes → `must_serialize_with: [database-migration]`
   - No → Don't list it

4. **What's the natural batch size?**
   - Files touching (1) → `preferred_batch_size: 1`
   - Simple parallel (3) → `preferred_batch_size: 3`
   - Highly parallel (5+) → `preferred_batch_size: 10`

**Example Decision Tree:**

```
Skill: frontend-development

Q1: Can run with code-review?
  A: Yes (code review is on backend, different domain)
  → Add to can_parallel_with

Q2: Can run with test-writer?
  A: Yes (tests can be written spec-driven)
  → Add to can_parallel_with

Q3: Must serialize with database-migration?
  A: Only if schema affects frontend (TypeScript interfaces)
  Usually no direct dependency
  → Don't add to must_serialize_with

Q4: Batch size?
  A: Can develop multiple components in parallel
  Reasonable limit: 5 components
  → preferred_batch_size: 5

Result:
parallel_hints:
  can_parallel_with: [code-review, test-writer, lint-monorepo]
  must_serialize_with: [database-migration]  # Only if schema affects types
  preferred_batch_size: 5
```

---

## Appendix: Configuration Examples

### Example 1: High-Parallelism Configuration

**Use Case:** Maximum speed for independent tasks

```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer, security-audit, lint-monorepo]
  must_serialize_with: []
  preferred_batch_size: 10
```

**Skills Using This:** lint-monorepo

---

### Example 2: Medium-Parallelism Configuration

**Use Case:** Safe parallelization with some constraints

```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer, security-audit]
  must_serialize_with: [database-migration]
  preferred_batch_size: 5
```

**Skills Using This:** fastapi-production, code-review

---

### Example 3: Low-Parallelism Configuration

**Use Case:** Serialization required for safety

```yaml
parallel_hints:
  can_parallel_with: []
  must_serialize_with: [code-review, test-writer, automated-code-fixer]
  preferred_batch_size: 1
```

**Skills Using This:** database-migration

---

### Example 4: Asymmetric Configuration

**Use Case:** One-directional dependency

```yaml
# In fastapi-production
parallel_hints:
  can_parallel_with: [test-writer, code-review]
  must_serialize_with: [database-migration]
  preferred_batch_size: 5

# In test-writer
parallel_hints:
  can_parallel_with: [code-review, fastapi-production, lint-monorepo]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

**Interpretation:** Both can run together, but both must wait for database migration

---

## Summary: Parallel Hints as Force Multiplier

### Metrics

| Metric | Sequential | Parallel | Improvement |
|--------|:--:|:--:|:--:|
| **Development Time** | 100% | 30-40% | 2.5-3.3x speedup |
| **Agent Utilization** | ~20% idle | ~70% active | Better resource use |
| **Quality Gate Time** | 8 minutes | 3 minutes | 2.67x faster |
| **Hotfix Deployment** | 20 minutes | 4 minutes | 5x faster |
| **Test Campaign (50 modules)** | 150 min | 51 min | 3x faster |

### Key Principles

1. **Zero Marginal Cost:** Different domains = free parallelization
2. **Explicit Annotation:** Skills declare compatibility, agents don't guess
3. **Batch Optimization:** Group similar work, respect batch size hints
4. **Database Serialization:** Schema is the critical bottleneck
5. **Convergence Points:** Quality gates converge before merge

### Impact on Multi-Agent Workflows

- **ORCHESTRATOR** can coordinate 10+ agents concurrently
- **Specialists** know exactly what can run in parallel
- **Quality gates** don't block unrelated work
- **Emergency response** can parallelize all non-schema fixes
- **Development velocity** increases 2.5-3x with proper annotation

---

**End of Skills Parallel Hints Guide**

*This document serves as the comprehensive reference for parallel execution coordination in the PAI ecosystem. Update when new skills are annotated or parallelization patterns evolve.*
