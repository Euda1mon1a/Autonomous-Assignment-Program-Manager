# Skills Composition Patterns - Comprehensive Documentation

**SEARCH_PARTY Operation: SESSION_9_SKILLS**
*G2_RECON Investigation of Skill Composition Architecture*

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Perception: Current Skill Compositions](#perception-current-skill-compositions)
3. [Investigation: Skill Dependencies](#investigation-skill-dependencies)
4. [Arcana: Composition Patterns](#arcana-composition-patterns)
5. [History: Composition Evolution](#history-composition-evolution)
6. [Insight: Composability Philosophy](#insight-composability-philosophy)
7. [Religion: Compositions Documented](#religion-compositions-documented)
8. [Nature: Composition Complexity](#nature-composition-complexity)
9. [Medicine: Workflow Context](#medicine-workflow-context)
10. [Survival: Composition Failure Handling](#survival-composition-failure-handling)
11. [Stealth: Hidden Compositions](#stealth-hidden-compositions)
12. [Best Practices & Recommendations](#best-practices--recommendations)

---

## PERCEPTION: Current Skill Compositions

### Skill Inventory

**Total Skills Documented:** 96+ skill documentation files across 47 skill directories

**Primary Skill Categories:**

#### 1. Meta-Skills (Orchestration & Control)
- **MCP_ORCHESTRATION**: Coordinates 36+ MCP tools across 6 categories
- **ORCHESTRATION_DEBUGGING**: Root cause analysis for tool failures
- **CORE**: Agent protocols and delegation patterns
- **context-aware-delegation**: Multi-agent coordination with context isolation

#### 2. Scheduling Domain Skills
- **SCHEDULING**: Five-phase schedule generation workflow
- **SWAP_EXECUTION**: Five-phase swap execution with rollback
- **COMPLIANCE_VALIDATION**: ACGME compliance audits with violation remediation
- **RESILIENCE_SCORING**: Health metrics, N-1/N-2 contingency analysis
- **schedule-optimization**: Solver algorithms and multi-objective optimization
- **schedule-verification**: Human verification checklist for generated schedules

#### 3. Development/Quality Skills
- **automated-code-fixer**: Detects and fixes code issues
- **code-review**: Reviews generated code for bugs/security
- **test-writer**: Generates pytest/Jest tests
- **lint-monorepo**: Unified Python/TypeScript linting
- **pr-reviewer**: Pull request review with quality gates
- **code-quality-monitor**: Proactive code health monitoring

#### 4. Infrastructure & Deployment Skills
- **safe-schedule-generation**: Backup before write operations
- **docker-containerization**: Docker/Docker Compose expertise
- **database-migration**: Alembic migration expertise
- **fastapi-production**: Production FastAPI patterns
- **constraint-preflight**: Verifies constraints before schedule generation

#### 5. Specialized Domain Skills
- **acgme-compliance**: ACGME regulatory expertise
- **security-audit**: Healthcare/military security auditing
- **production-incident-responder**: Crisis response with MCP tools
- **swap-management**: Swap workflow expertise
- **test-scenario-framework**: End-to-end test scenarios

#### 6. Support & Documentation Skills
- **session-documentation**: Document sessions for context preservation
- **changelog-generator**: Generate user-friendly changelogs
- **pdf** / **xlsx**: Document generation (PDF, Excel)
- **startup** / **startupO**: Session initialization

#### 7. Frontend Skills
- **frontend-development**: Next.js 14, React 18, TailwindCSS
- **react-typescript**: TypeScript expertise for React/Next.js

#### 8. Advanced Frameworks
- **python-testing-patterns**: Advanced pytest patterns
- **systematic-debugger**: Four-phase debugging workflow
- **solver-control**: Solver kill-switch and progress monitoring
- **agent-factory**: Create new PAI agents from patterns
- **skill-factory**: Create new skills with proper structure

---

### Current Composition Statistics

| Metric | Value |
|--------|-------|
| Total Skill Files | 96+ |
| Skill Directories | 47 |
| Skills with Metadata | 10+ |
| Skills with Workflows | 12+ |
| Skills with Reference Docs | 8+ |
| Skills with Examples | 5+ |
| Average Documentation Per Skill | 3-5 files |

---

## INVESTIGATION: Skill Dependencies

### Explicit Dependencies (from SKILL.md metadata)

#### MCP_ORCHESTRATION Dependencies
```
MCP_ORCHESTRATION (Tier: haiku)
├── can_parallel_with: [code-review, test-writer, security-audit]
├── must_serialize_with: [database-migration]
└── preferred_batch_size: 5 tools/batch
```

**Interpretation:**
- Code review, test writing, and security audits can run in parallel with MCP tool orchestration
- Database migrations must be serialized (cannot parallelize)
- Optimal batch size for parallel tool execution is 5

#### Key Composition Rules
```yaml
docker-containerization:
  can_parallel_with: [frontend-development, python-testing-patterns]
  must_serialize_with: [database-migration, fastapi-production]

automated-code-fixer:
  can_parallel_with: [code-review, test-writer, security-audit]
  must_serialize_with: [database-migration, lint-monorepo]

lint-monorepo:
  can_parallel_with: [test-writer]
  must_serialize_with: [automated-code-fixer, code-review]
```

### Implicit Dependencies (from workflow documentation)

#### Scheduling Workflow Dependencies

**Phase 1-5 Sequence (strict ordering):**
```
SCHEDULING (Phase 1: Gather Requirements)
    ↓ (output: SchedulingContext)
SCHEDULING (Phase 2: Constraint Propagation)
    ↓ (output: Feasibility analysis)
schedule-optimization (Phase 3: Optimization)
    ↓ (output: Candidate schedules)
SCHEDULING (Phase 4: Conflict Resolution)
    ↓ (output: Exception documentation)
safe-schedule-generation (Phase 5: Validation & Deployment)
    ├─ depends_on: acgme-compliance (validation)
    ├─ depends_on: RESILIENCE_SCORING (health check)
    ├─ depends_on: constraint-preflight (new constraints)
    └─ output: Deployed schedule
```

#### Swap Execution Workflow Dependencies

**Phase 1-5 Sequence (strict ordering):**
```
SWAP_EXECUTION (Phase 1: Request Intake)
    ↓ (output: Normalized swap request)
SWAP_EXECUTION (Phase 2: Safety Checks)
    ├─ depends_on: acgme-compliance (tier 1 validation)
    ├─ depends_on: RESILIENCE_SCORING (tier 3 impact)
    └─ depends_on: swap-management (policy rules)
    ↓ (output: Safety decision)
SWAP_EXECUTION (Phase 3: Execution)
    ↓ (output: Updated database)
SWAP_EXECUTION (Phase 4: Verification)
    ├─ depends_on: acgme-compliance (re-validation)
    └─ depends_on: RESILIENCE_SCORING (health change)
    ↓ (output: Verified state)
SWAP_EXECUTION (Phase 5: Monitoring)
    ↓ (output: Rollback-eligible transaction)
```

#### Development Workflow Dependencies

**Quality Gate Pipeline:**
```
Code Changes
    ↓
automated-code-fixer (fix common issues)
    ↓
lint-monorepo (Python: ruff, TypeScript: ESLint)
    ↓ (parallel)
├── test-writer (generate/update tests)
├── code-review (audit generated code)
└── security-audit (check vulnerabilities)
    ↓
pr-reviewer (comprehensive review before merge)
    ↓
code-quality-monitor (gate enforcement)
    ↓
database-migration (if schema changed)
    ↓
safe-schedule-generation (if touching schedule generation)
```

#### Deployment Pipeline Dependencies

**Production Deployment Sequence:**
```
Code Commit (to feature branch)
    ↓
lint-monorepo + test-writer (pre-PR checks)
    ↓
pr-reviewer (approve PR)
    ↓ (on main merge)
docker-containerization (build containers)
    ↓
fastapi-production (API validation)
    ↓
automated-code-fixer (last-minute fixes)
    ↓
security-audit (final security check)
    ↓
MCP_ORCHESTRATION (orchestrate deployment tools)
    ├─ validate_deployment
    ├─ run_security_scan
    ├─ run_smoke_tests
    └─ promote_to_production
    ↓
RESILIENCE_SCORING (post-deployment health check)
```

### Dependency Matrix

```
Skills that DEPEND ON others:

SWAP_EXECUTION depends on:
  ✓ acgme-compliance (Tier 1 validation)
  ✓ RESILIENCE_SCORING (Impact assessment)
  ✓ swap-management (Policy rules)
  ✓ SCHEDULING (Schedule context)

SCHEDULING depends on:
  ✓ acgme-compliance (Phase 2, 5 validation)
  ✓ schedule-optimization (Phase 3 execution)
  ✓ safe-schedule-generation (Phase 5 safety)
  ✓ constraint-preflight (New constraints)
  ✓ RESILIENCE_SCORING (Phase 5 resilience check)

COMPLIANCE_VALIDATION depends on:
  ✓ acgme-compliance (Rules database)
  ✓ SCHEDULING (Schedule analysis)
  ✓ MCP_ORCHESTRATION (Multi-tool audits)

schedule-optimization depends on:
  ✓ SCHEDULING (Context + constraints)
  ✓ acgme-compliance (Rule definitions)

MCP_ORCHESTRATION depends on:
  - None (independent orchestrator)

automated-code-fixer depends on:
  ✓ code-quality-monitor (Quality gates)
  ✓ test-writer (Test verification)

All skills may depend on:
  ✓ CORE (protocols, delegation patterns)
  ✓ context-aware-delegation (Subagent spawning)
  ✓ startup (Session initialization)
```

---

## ARCANA: Composition Patterns

### Pattern 1: Sequential Chain (Linear Pipeline)

**Definition:** One skill's output becomes next skill's input. Total time = sum of all steps.

**Use Cases:**
- Schedule generation (5 phases, each must complete before next)
- Swap execution (5 phases, strict ordering)
- Deployment pipeline (validation → build → test → deploy)

**Example: Safe Schedule Generation**
```
Step 1: safe-schedule-generation.backup()
    ↓ (backup created)
Step 2: SCHEDULING.generate()
    ↓ (schedule assignments created)
Step 3: acgme-compliance.validate()
    ↓ (validation results)
Step 4: RESILIENCE_SCORING.check_health()
    ↓ (health score calculated)
Step 5: safe-schedule-generation.deploy()
    ↓ (schedule deployed)
Result: Deployed schedule with audit trail
```

**Failure Handling:**
- Step 1 fails: Abort (no backup, too risky)
- Step 2 fails: Rollback backup (if created)
- Step 3 fails: Record violations, may continue with warnings
- Step 4 fails: Flag as degraded health, continue
- Step 5 fails: Rollback entire operation

**From Documentation:**
> "Each step must validate before proceeding" - delegation-patterns.md

### Pattern 2: Parallel Fan-Out (Scatter-Gather)

**Definition:** Multiple independent skills execute in parallel, results merged. Total time = max(parallel steps).

**Use Cases:**
- Multi-perspective validation (ACGME + resilience + conflicts simultaneously)
- Comprehensive schedule analysis (validation, conflict detection, health scoring)
- Parallel code reviews (code review, security audit, test writer in parallel)

**Example: Comprehensive Resilience Analysis**
```
┌─ call_utilization_threshold()
├─ run_contingency_analysis()  ─→ All parallel
├─ analyze_hub_centrality()
├─ get_static_fallbacks()
└─ check_mtf_compliance()
    ↓
Results aggregated → Health score synthesized
```

**Failure Handling (from error-handling.md):**
- Use `asyncio.gather(..., return_exceptions=True)`
- Handle exceptions per result (don't fail entire batch)
- Missing data = penalize health score but don't fail
- Partial success acceptable for non-critical tools

**Synthesis Logic:**
```python
# All-or-nothing synthesis
if any([check failed]):
    overall_result = FAILED

# Best-effort synthesis
if any([check succeeded]):
    overall_result = SUCCEEDED

# Weighted synthesis
score = sum([check.score * weight for check, weight])
```

**From Documentation:**
> "Reduced wall-clock time (4x speedup) with parallelism" - delegation-patterns.md

### Pattern 3: Map-Reduce (Parallel + Aggregation)

**Definition:** Scatter identical task to multiple agents, reduce results into single output.

**Use Cases:**
- Batch validation (validate 100 schedules, 10 at a time)
- Multi-resident N-1 analysis (test absence of each resident)
- Multi-scenario performance benchmarking

**Example: Code Optimization Analysis**
```
Map Phase (Parallel):
  ├─ benchmark_solvers(20 scenarios)
  ├─ benchmark_constraints(historical data)
  ├─ benchmark_resilience(all modules)
  └─ module_usage_analysis(entry points)

Reduce Phase (Sequential):
  ├─ Aggregate results into removal candidates
  ├─ Rank by impact + safety
  └─ Verify with ablation studies

Output: Ranked list of safe removals
```

**Failure Handling:**
- Map failures: Continue with successful results
- Reduce failures: Report partial results

**From Documentation:**
> "Map: Run all benchmarks in parallel. Reduce: Aggregate removal candidates" - composition-examples.md

### Pattern 4: Conditional Routing (Decision Tree)

**Definition:** Skill executes, result determines which skill runs next.

**Use Cases:**
- Deployment pipeline (validation fails → rollback)
- Swap request processing (all checks pass → execute, else → reject/escalate)
- Schedule generation (no feasible solution → decompose problem)

**Example: Swap Execution with Conditional Routing**
```
SWAP_EXECUTION Phase 2: Safety Checks
    ↓
Decision Point:
  ├─ [REJECT] → Record reason + notify
  ├─ [FLAG] → Escalate to faculty for approval
  └─ [PROCEED] → Execute swap (Phase 3)
    ├─ [SUCCESS] → Monitoring (Phase 5)
    └─ [FAILURE] → Rollback + record
```

**From Documentation:**
> "Pattern 4: Conditional Routing - Tool A → Decision → Tool B (if condition) / Tool C (else)" - MCP_ORCHESTRATION SKILL.md

### Pattern 5: Hybrid Pipeline (Stages with Parallelism)

**Definition:** Sequential stages, parallel execution within each stage.

**Use Cases:**
- Multi-objective optimization (parallel objective functions → select best)
- Multi-level validation (parallel validators per level)

**Example: Schedule Optimization**
```
Stage 1: Pre-validation (Parallel)
  ├─ acgme-compliance.validate()
  ├─ resilience-framework.check()
  └─ conflict-detector.scan()
  └→ All must pass before Stage 2

Stage 2: Optimization (Parallel)
  ├─ optimize(fairness)
  ├─ optimize(coverage)
  └─ optimize(continuity)
  └→ Select Pareto-optimal result

Stage 3: Final Validation (Sequential)
  └─ acgme-compliance.comprehensive_validate()
  └→ Return best schedule
```

**From Documentation:**
> "Best of both worlds: Parallel execution within stages, sequential stages for dependencies" - delegation-patterns.md

### Pattern 6: Fire-and-Forget (Asynchronous Delegation)

**Definition:** Delegate task, don't wait for result. Retrieve later.

**Use Cases:**
- Background report generation
- Long-running N-1 analysis (2-5 minutes)
- Non-blocking analytics

**Example from composition-examples.md:**
```python
# Start background task
task_id = await delegate_async(
    agent="schedule-optimization",
    action="generate",
    params={"period": "Q2-2025"}
)

# Continue other work
await do_other_work()

# Later, retrieve result
result = await get_task_result(task_id, timeout=60)
```

**Mechanism:**
- Start background task, get task_id
- Poll task status every 5 seconds
- Continue after timeout or completion

---

## HISTORY: Composition Evolution

### Generation 1: Linear Workflows (Initial Design)

**Characteristics:**
- Sequential skill execution only
- No parallelism
- Simple error handling (fail-fast)
- Limited result synthesis

**Examples:**
- Schedule generation (basic 3-phase process)
- Swap execution (intake → validation → execution)

**Limitations:**
- Slow (sequential bottleneck)
- Inflexible (can't skip non-critical steps)
- Poor error recovery (fail-fast loses partial results)

### Generation 2: Multi-Skill Orchestration (Explicit Dependencies)

**Characteristics:**
- Added parallel execution (asyncio.gather)
- Explicit dependency metadata (SKILL.md)
- Result synthesis patterns (all-or-nothing, best-effort, majority vote)
- Retry logic with exponential backoff

**Examples:**
- Comprehensive resilience analysis (5 tools parallel)
- Deployment pipeline (parallel validation + sequential promotion)

**Improvements:**
- Wall-clock time: 4-5x speedup with parallelism
- Partial failure handling
- Structured result aggregation

### Generation 3: Complex Orchestration (MCP Tools + Delegation)

**Characteristics:**
- 36+ MCP tools for scheduling operations
- Multi-agent delegation with context isolation
- Subagent spawning for specialized work
- Circuit breakers and rate limiting

**Examples:**
- MCP_ORCHESTRATION skill (tool discovery, routing, chaining)
- production-incident-responder (crisis orchestration)
- Comprehensive schedule analysis (validate + detect conflicts + check utilization parallel)

**Advanced Features:**
- Tool discovery (find available tools matching requirements)
- DAG execution (directed acyclic graph planning)
- Error recovery (retry, fallback, escalation)
- Resource management (concurrency limits, timeouts)

### Generation 4: Resilience-Aware Composition (Current State)

**Characteristics:**
- Explicit failure mode handling
- Graceful degradation (partial success acceptable)
- Cascading failure prevention (circuit breakers)
- Health-aware tool selection

**Examples:**
- RESILIENCE_SCORING integration (pre-deployment health assessment)
- N-1/N-2 failure simulation before deployment
- Post-incident resilience analysis

**Key Innovation:**
- Don't just check if solution works
- Check how robust solution is under failure
- Identify critical residents/rotations before problem occurs

---

## INSIGHT: Composability Philosophy

### Core Principles

#### 1. Separation of Concerns
Each skill has a single, well-defined responsibility:

```
SCHEDULING: Generate schedule (business logic)
├── Does NOT validate compliance (→ acgme-compliance)
├── Does NOT assess health (→ RESILIENCE_SCORING)
└── Does NOT handle deployment (→ safe-schedule-generation)
```

**Benefit:** Skills are independently testable and reusable

#### 2. Clear Input/Output Contracts

Every skill defines explicit data contracts:

```python
# Input contract (Pydantic schema)
class ScheduleGenerationRequest(BaseModel):
    start_date: date
    end_date: date
    algorithm: str
    timeout_seconds: int
    objectives: dict[str, float]

# Output contract (Pydantic schema)
class ScheduleGenerationResponse(BaseModel):
    schedule_id: str
    status: str
    assignments_created: int
    validation: ValidationResult
    metrics: ScheduleMetrics
    alternatives: list[Alternative]
```

**Benefit:** Skills can be composed with confidence (type safety)

#### 3. Explicit Dependency Declaration

Skills declare their dependencies upfront in SKILL.md:

```yaml
# Declare what I can parallelize with
can_parallel_with: [code-review, test-writer, security-audit]

# Declare what must be serialized with
must_serialize_with: [database-migration]

# Declare my batch preferences
preferred_batch_size: 5
```

**Benefit:** Orchestrator can make intelligent scheduling decisions

#### 4. Failure Mode Documentation

Each skill documents expected failure modes:

```markdown
### Common Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| NO_FEASIBLE_SOLUTION | Over-constrained | Relax constraints |
| TIMEOUT | Complex problem | Increase timeout |
| ACGME_VIOLATION | Invalid config | Review parameters |
```

**Benefit:** Caller knows what to expect and how to handle it

#### 5. Result Synthesis Patterns

Standard synthesis patterns for combining results:

```python
# All-or-nothing (AND logic)
if any(check failed):
    return FAILED

# Best-effort (OR logic)
if any(check succeeded):
    return SUCCEEDED

# Majority vote (consensus)
if votes[decision] > total / 2:
    return decision

# Weighted aggregation
score = sum([result[i] * weight[i]])

# Merge-deduplicate
merged = combine(results).unique()
```

**Benefit:** Caller doesn't implement synthesis logic (reusable patterns)

#### 6. Idempotency Where Possible

Skills designed to be idempotent (safe to retry):

```python
# Idempotent: Same input → same output
def validate_schedule(start_date, end_date):
    return PASS/FAIL based on database state
    # Safe to call multiple times

# Non-idempotent: Side effects
def execute_swap(swap_id):
    update assignments
    # NOT safe to call multiple times (transaction already executed)
    # Compensated by: Explicit rollback window
```

**Benefit:** Can retry safely on transient failures

---

## RELIGION: Compositions Documented

### Documentation Structure (for Well-Documented Skills)

#### Level 1: SKILL.md (Metadata + Overview)
```yaml
name: [Skill Name]
description: [One-line purpose]
model_tier: [haiku/opus]
parallel_hints:
  can_parallel_with: [other skills]
  must_serialize_with: [other skills]
  preferred_batch_size: [N]
```

**Purpose:** Skill discovery and orchestration planning

**Examples:**
- MCP_ORCHESTRATION/SKILL.md
- SCHEDULING/SKILL.md
- SWAP_EXECUTION/SKILL.md

#### Level 2: Workflows/ (Step-by-Step Execution)
```
Workflows/
├── phase-1-requirements.md
├── phase-2-constraints.md
├── phase-3-optimization.md
├── phase-4-conflicts.md
└── phase-5-deployment.md
```

**Purpose:** Detailed walkthrough of each phase

**Content:**
- Step-by-step activities
- Inputs and outputs for each step
- Common failure points
- Decision trees for branches

#### Level 3: Reference/ (Deep Dives)
```
Reference/
├── constraint-index.md         (All constraints with priorities)
├── tool-error-patterns.md      (Known failures + workarounds)
├── escalation-matrix.md        (When to escalate)
├── composition-examples.md     (Real-world workflows)
└── thresholds.md              (Alert thresholds)
```

**Purpose:** Detailed reference material

**Content:**
- Exhaustive catalogs
- Known issues and solutions
- Escalation decision trees
- Worked examples with pseudocode

### Composition Documentation Status

#### Well-Documented Skills (4+ files each)

| Skill | Files | Metadata | Workflows | References | Examples |
|-------|-------|----------|-----------|-----------|----------|
| MCP_ORCHESTRATION | 7 | ✓ | 3 | 3 | ✓ |
| SCHEDULING | 6 | ✓ | 3 | 2 | ✓ |
| SWAP_EXECUTION | 6 | ✓ | 4 | 2 | ✓ |
| RESILIENCE_SCORING | 5 | ✓ | 4 | 1 | ✓ |
| COMPLIANCE_VALIDATION | 5 | ✓ | 3 | 2 | ✗ |
| ORCHESTRATION_DEBUGGING | 4 | ✓ | 2 | 2 | ✗ |

#### Under-Documented Skills (1-2 files each)

| Skill | Files | Issue |
|-------|-------|-------|
| acgme-compliance | 3 | No composition examples |
| code-review | 1 | Only SKILL.md, no workflows |
| test-writer | 1 | Only SKILL.md, no reference docs |
| automated-code-fixer | 3 | No workflow documentation |

### Composition Documentation Gaps

**Gap 1: Cross-Skill Workflow Documentation**

Missing: How to orchestrate multiple skills end-to-end

**Example Gap:** "How to safely generate and deploy a schedule"
- Currently: Each skill documents itself (SCHEDULING, safe-schedule-generation, acgme-compliance)
- Missing: Single doc showing all 5 skills working together

**Recommendation:** Create `cross-skill-workflows.md` documenting:
- Schedule generation pipeline (5 skills, dependency graph)
- Deployment pipeline (6 skills, failure paths)
- Development workflow (8 skills, quality gates)

**Gap 2: Composition Error Handling**

Missing: How errors in one skill affect downstream skills

**Example Gap:** "If schedule generation fails, what happens to validation?"
- Currently: Each skill documents its own error handling
- Missing: How to handle cascading failures across skill boundary

**Recommendation:** Create `composition-error-handling.md` documenting:
- Transient vs permanent error classification
- Circuit breaker behavior (when to stop retrying)
- Cascading failure prevention (how to isolate failures)
- Recovery strategies (rollback, fallback, escalation)

**Gap 3: Performance Composition**

Missing: How composition affects overall performance

**Example Gap:** "Is it faster to run all validators in parallel?"
- Currently: No documentation on latency/throughput trade-offs
- Missing: Performance benchmarks for different composition strategies

**Recommendation:** Create `performance-composition.md` documenting:
- Parallel vs sequential latency (wall-clock time comparison)
- Resource utilization (CPU, memory, database connections)
- Bottleneck identification (which skill is slowest)
- Scaling strategies (batch size, concurrency limits)

---

## NATURE: Composition Complexity

### Composition Complexity Spectrum

#### Complexity Level 1: Simple Chain (2-3 skills)

**Examples:**
- validate_schedule → detect_conflicts (2 skills)
- request_intake → safety_checks → execution (3 skills, linear)

**Characteristics:**
- Sequential execution
- Simple error handling (fail-fast)
- Easy to understand and debug
- Low implementation effort

**Typical Time:** 2-10 seconds

#### Complexity Level 2: Fan-Out (4-6 parallel skills)

**Examples:**
- Validate + detect_conflicts + check_utilization (3 parallel)
- Multi-perspective validation (4-5 parallel validators)

**Characteristics:**
- Parallel execution (asyncio.gather)
- Partial failure handling
- Result synthesis (combine parallel results)
- Moderate complexity

**Typical Time:** 2-10 seconds (max of parallel times)

**Parallel Speedup:** 3-5x vs sequential

#### Complexity Level 3: Hybrid Pipeline (6-8 skills)

**Examples:**
- Schedule generation (5 phases, some phases have parallel steps)
- Deployment pipeline (parallel validation, sequential promotion)

**Characteristics:**
- Sequential stages with parallel steps within stages
- Multiple failure points with different handling
- Result synthesis at stage boundaries
- Higher complexity

**Typical Time:** 10-60 seconds (sum of stages)

**Parallel Speedup:** 2-3x vs pure sequential

#### Complexity Level 4: Complex Orchestration (10+ skills)

**Examples:**
- Comprehensive schedule analysis + resilience check + deployment
- Crisis response workflow

**Characteristics:**
- Multiple decision points (conditional routing)
- Nested parallelism (parallel within parallel)
- Circuit breakers and rate limiting
- Extensive error recovery (retry, fallback, escalation)
- High complexity, hard to debug

**Typical Time:** 30 seconds - 10 minutes (depending on background tasks)

**Typical Parallelism:** 3-4 degrees (3-4 independent branches)

### Composition Complexity Drivers

#### 1. Number of Skills
```
1-2 skills:     Trivial (no composition needed)
3-5 skills:     Simple (linear or fan-out)
6-10 skills:    Moderate (hybrid pipeline)
10+ skills:     Complex (multiple phases)
```

#### 2. Dependency Structure
```
Linear (A→B→C→D):           Simple
Fan-out (A→[B,C,D]):        Moderate
Hybrid (A→[B,C]→D):         Moderate
DAG ([A,B]→C→[D,E,F]):      Complex
```

#### 3. Error Recovery Strategies
```
Fail-fast (abort on first error):          Simple
Best-effort (continue despite errors):     Moderate
Retry+fallback (circuit breaker):          Complex
Multi-level escalation (human involvement): Very complex
```

#### 4. Data Transformation Between Skills
```
Direct pass-through:                  Simple
Simple extraction (pluck field):       Moderate
Complex transformation (reshape):      Complex
Stateful aggregation (accumulate):    Very complex
```

### Composition Complexity Analysis Examples

#### Example 1: Safe Schedule Generation (Moderate Complexity)

```
Phases:    5 sequential
Skills:    5 (SCHEDULING × 3 + safe-schedule + acgme-compliance)
Parallel:  0 (fully sequential)
Errors:    Phase 1 fail → abort
           Phase 2 fail → continue with warning
           Phase 3 fail → rollback
           Phase 4 fail → report violations
           Phase 5 fail → escalate critical
Transforms: Each phase produces structured output → next phase input
Time:      ~60 seconds (validation can be slow)

Complexity Score: MODERATE (5 phases, 3+ error handling paths)
```

#### Example 2: Swap Execution (Moderate Complexity)

```
Phases:    5 sequential
Skills:    4 (SWAP_EXECUTION × 5 + acgme-compliance + RESILIENCE_SCORING)
Parallel:  Phases 2 & 4 have parallel sub-checks (tier 1 + tier 2 + tier 3)
Errors:    Phase 1 fail → abort (parsing error)
           Phase 2 fail → reject swap (soft escalation)
           Phase 3 fail → automatic rollback
           Phase 4 fail → flag for manual review
           Phase 5 fail → continue monitoring
Transforms: Request → normalized request → decision → executed record → monitored state
Time:      ~5 seconds (mostly validation)

Complexity Score: MODERATE (5 phases, parallel sub-checks, conditional routing)
```

#### Example 3: Comprehensive Resilience Analysis (Low-to-Moderate Complexity)

```
Phases:    1 (single parallel fan-out)
Skills:    5-6 (all parallel)
Parallel:  5 concurrent tool calls
Errors:    Per-tool error handling (continue if tool fails)
           Fallback to cached data if available
           Partial success acceptable
Transforms: Aggregate 5 results → health score calculation
Time:      ~15 seconds (max of 5 tools)

Complexity Score: LOW-MODERATE (simple parallel, partial failure OK)
```

#### Example 4: Production Deployment (High Complexity)

```
Phases:    6 sequential
Skills:    8+ (docker, fastapi, security, MCP_ORCHESTRATION, resilience)
Parallel:  Parallel within phases:
           - Phase 3: parallel validation checks
           - Phase 4: parallel deployment steps
Errors:    Phase 1 fail → block deployment
           Phase 2 fail → block deployment
           Phase 3 fail → block deployment
           Phase 4 fail → automatic rollback
           Phase 5 fail → continue monitoring (deployed)
           Phase 6 fail → escalate emergency
Transforms: Code → validated → secured → deployed → monitored
Time:      ~5 minutes (includes smoke tests, deployment)

Complexity Score: HIGH (6 phases, 2+ parallel stages, automatic rollback, escalation)
```

---

## MEDICINE: Workflow Context

### Resident Scheduling Domain Context

#### Key Workflows

**1. Annual Schedule Generation**
```
Frequency: Once per year (usually February for July-June AY)
Duration: 30-120 minutes (depending on complexity)
Complexity: HIGH (100+ residents, 10+ rotations, 365 days)
Teams: Program Director + Coordinator + Scheduling Officer

Skill Sequence:
  SCHEDULING.Phase 1 (2-5 min) → Requirements gathering
  SCHEDULING.Phase 2 (5 min) → Constraint propagation
  schedule-optimization.generate (10-30 min) → Solve
  SCHEDULING.Phase 4 (5-10 min) → Conflict resolution
  safe-schedule-generation.deploy (5 min) → Backup + deploy
  RESILIENCE_SCORING.health (5 min) → Health check
  COMPLIANCE_VALIDATION.audit (5 min) → Final audit

Success Criteria:
  ✓ 100% ACGME compliance
  ✓ >95% coverage
  ✓ Health score >0.70
  ✓ N-1 contingency passed
  ✓ All stakeholders notified
```

**2. Emergency Coverage Response**
```
Frequency: 2-3x per month (faculty absence, TDY, medical emergency)
Duration: 5-30 minutes (urgent)
Complexity: MODERATE (affect 1-5 residents/assignments)
Teams: Coordinator + On-call Architect

Skill Sequence:
  SWAP_EXECUTION.Phase 1 (30 sec) → Intake request
  SWAP_EXECUTION.Phase 2 (30 sec) → Safety checks (parallel: ACGME, resilience)
  SWAP_EXECUTION.Phase 3 (30 sec) → Execute swap
  SWAP_EXECUTION.Phase 4 (30 sec) → Verify state
  RESILIENCE_SCORING.health (2 min) → Check impact

Success Criteria:
  ✓ Swap executed within 5 minutes
  ✓ No ACGME violations introduced
  ✓ Health score degradation <5%
  ✓ All parties notified
```

**3. Monthly Resilience Health Check**
```
Frequency: Monthly (1st of month)
Duration: 10-30 minutes (non-urgent)
Complexity: MODERATE (comprehensive analysis)
Teams: Scheduling Officer + Architect

Skill Sequence:
  RESILIENCE_SCORING.health (2-5 min) → Compute score
  RESILIENCE_SCORING.n1_analysis (3-5 min) → Single-point failures
  RESILIENCE_SCORING.multi_failure (10-15 min) → Monte Carlo sim
  COMPLIANCE_VALIDATION.audit (2-5 min) → Compliance check

Output:
  ✓ Health score + trend analysis
  ✓ Critical residents identified
  ✓ Fragile rotations ranked
  ✓ Recommendations for mitigation
```

**4. Post-Incident Analysis**
```
Frequency: After major incidents (2-3x per year)
Duration: 60-180 minutes (thorough investigation)
Complexity: HIGH (root cause analysis)
Teams: Architect + Program Director + Coordinator

Skill Sequence:
  production-incident-responder.assess (10 min) → Immediate impact
  systematic-debugger.explore (20 min) → Understand what happened
  systematic-debugger.plan (10 min) → Hypothesis development
  RESILIENCE_SCORING.analysis (30 min) → Resilience assessment
  COMPLIANCE_VALIDATION.audit (20 min) → Check violations
  code-review/security-audit (20 min) → System health check

Output:
  ✓ Root cause identified
  ✓ Resilience vulnerabilities identified
  ✓ Preventive measures recommended
  ✓ Lessons learned documented
```

### Complexity Drivers in Scheduling Domain

#### 1. Scale
```
Small Program: 10-15 residents
  → Simpler constraints
  → Fewer coverage requirements
  → 10-30 second schedule generation

Large Program: 40+ residents
  → Complex constraints
  → Multiple specialties
  → 2-5 minute schedule generation (timeout risk)
```

#### 2. Institutional Policies
```
Flexible: Few hard policies beyond ACGME
  → Quick generation
  → High satisfaction possible

Restrictive: Many institutional constraints
  → Longer generation times
  → May have no feasible solution
  → Requires constraint relaxation
```

#### 3. Composition of Resident Cohorts
```
Simple: All residents similar training level
  → Easier constraint satisfaction

Complex: Mix of PGY-1/2/3, fellows, rotating attendings
  → Different supervision ratios
  → Different rotation requirements
  → Complex substitution rules
```

### Integration Points in Scheduling Context

**Skill Used By:** Whom and When?

```
Program Director:
  - SCHEDULING (annual generation)
  - RESILIENCE_SCORING (monthly health checks)
  - COMPLIANCE_VALIDATION (annual audit)

Scheduling Coordinator:
  - SWAP_EXECUTION (emergency coverage)
  - schedule-verification (human review of drafts)
  - SCHEDULING (regeneration requests)

Scheduling Architect (Technical):
  - MCP_ORCHESTRATION (all multi-tool workflows)
  - production-incident-responder (crisis response)
  - RESILIENCE_SCORING (deep analysis)
  - systematic-debugger (root cause investigation)

Resident/Faculty:
  - swap-management (request swaps)
  - (Limited visibility into skills)

System Administration:
  - docker-containerization (deployment)
  - database-migration (schema updates)
  - safe-schedule-generation (backup/restore)
```

---

## SURVIVAL: Composition Failure Handling

### Error Classification in Compositions

#### Transient Errors (Retry)

**Definition:** Temporary, likely to succeed on retry

**Types and Strategies:**

| Error Type | Cause | Retry Strategy |
|-----------|-------|----------------|
| Connection Timeout | Network latency | 3 retries, exponential backoff |
| Database Lock | Concurrent transaction | 3 retries, 100ms delay |
| Rate Limit | Too many requests | Retry with exponential backoff |
| Service Unavailable | Backend restarting | 3 retries, 2s delay |
| Temporary Resource | Celery queue full | 3 retries, 1s delay |

**From error-handling.md:**
```python
async def retry_with_backoff(
    func, max_retries=3, base_delay=1.0,
    exponential_base=2.0
):
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries:
                raise
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            await asyncio.sleep(delay)
```

#### Permanent Errors (Fail Fast)

**Definition:** Will not succeed on retry

**Types and Actions:**

| Error Type | Cause | Action |
|-----------|-------|--------|
| Invalid Input | Schema validation failure | Return error to caller |
| Resource Not Found | schedule_id doesn't exist | Return error |
| Authentication Failed | Invalid token | Escalate to human |
| Permission Denied | Insufficient privileges | Escalate to human |
| Data Constraint Violation | ACGME rule violated | Return error + suggestions |

#### Degraded Errors (Graceful Degradation)

**Definition:** Partial functionality acceptable

**Strategies:**

| Error Type | Fallback |
|-----------|----------|
| Backend API Down | Use cached data (e.g., compliance summary) |
| Celery Worker Offline | Synchronous execution if <30s, else fail gracefully |
| MCP Server Degraded | Skip non-critical tools, continue with essential |
| Partial Data Available | Return partial results with warning |

### Failure Handling in Compositions

#### Pattern 1: Fail-Fast Strategy

**Use When:** Safety-critical operations (schedule generation, deployment)

**Example from delegation-patterns.md:**
```python
async def execute_fail_fast(tasks):
    for task in tasks:
        result = await delegate_to_agent(**task)
        if not result.success:
            # Abort immediately
            return error(f"Task {task['agent']} failed")
    return success("All tasks completed")
```

**Failure Handling:**
```
Phase 1: backup()
  ├─ SUCCESS → Continue to Phase 2
  └─ FAILURE → Abort (too risky to continue)

Phase 2: generate()
  ├─ SUCCESS → Continue to Phase 3
  └─ FAILURE → Rollback backup, abort

Phase 3: validate()
  ├─ SUCCESS → Continue to Phase 4
  └─ FAILURE → Log violations, continue (non-blocking)

Phase 4: health_check()
  ├─ SUCCESS → Continue to Phase 5
  └─ FAILURE → Flag degraded, continue

Phase 5: deploy()
  ├─ SUCCESS → Done
  └─ FAILURE → Escalate critical (try rollback)
```

#### Pattern 2: Fail-Tolerant Strategy

**Use When:** Best-effort operations (multi-perspective validation)

**Example from delegation-patterns.md:**
```python
async def execute_fail_tolerant(tasks):
    results = []
    for task in tasks:
        try:
            result = await delegate_to_agent(**task)
            results.append({"success": True, "data": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    successes = [r for r in results if r["success"]]
    return {"success": len(successes) > 0, "results": successes}
```

**Failure Handling (Example: Parallel Validators):**
```
validator_1 (ACGME)
  ├─ SUCCESS → Add to results
  └─ FAILURE → Add to results with error, continue

validator_2 (Resilience)
  ├─ SUCCESS → Add to results
  └─ FAILURE → Add to results with error, continue

validator_3 (Conflicts)
  ├─ SUCCESS → Add to results
  └─ FAILURE → Add to results with error, continue

Synthesis:
  if all validators succeeded:
    overall = PASS
  elif majority succeeded:
    overall = PASS with warnings
  else:
    overall = FAIL
```

#### Pattern 3: Retry-with-Backoff Strategy

**Use When:** Transient failures expected (external APIs, database)

**Example from error-handling.md:**
```python
async def call_tool_with_retry(tool_name: str, **params):
    config = TOOL_RETRY_CONFIG[tool_name]

    for attempt in range(config["max_retries"]):
        try:
            return await tool_fn(**params)
        except config["retryable_errors"] as e:
            delay = config["base_delay"] * (2 ** attempt)
            await asyncio.sleep(delay)

    # All retries failed
    raise TimeoutError(f"All {config['max_retries']} retries failed")
```

**Retry Configuration (from error-handling.md):**
```python
TOOL_RETRY_CONFIG = {
    "validate_schedule_tool": {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, TimeoutError],
    },
    "promote_to_production_tool": {
        "max_retries": 1,  # Conservative - deployment should be idempotent
        "base_delay": 5.0,
        "retryable_errors": [ConnectionError],
    },
}
```

#### Pattern 4: Circuit Breaker Strategy

**Use When:** Preventing cascading failures (stop calling failing service)

**Example from delegation-patterns.md:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.opened_at = None

    async def execute(self, task):
        if self.state == "OPEN":
            if time.time() - self.opened_at > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError(f"Circuit breaker OPEN for {task['agent']}")

        try:
            result = await delegate_to_agent(**task)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"  # Recovered
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"  # Trip circuit
            raise
```

**States:**
```
CLOSED (normal):
  └─ Execute normally
  └─ On failure: Increment counter
  └─ If counter >= threshold: OPEN

OPEN (service down):
  └─ Reject all requests immediately (no call to service)
  └─ After timeout: HALF_OPEN

HALF_OPEN (testing recovery):
  └─ Allow single test request
  └─ If success: CLOSED (recovered!)
  └─ If failure: OPEN (still down)
```

### Escalation Triggers

**From error-handling.md:**

#### When to Escalate (Immediate)

```
1. Critical production error:
   ├─ promote_to_production_tool fails
   ├─ rollback_deployment_tool fails
   └─ execute_sacrifice_hierarchy_tool (non-simulation) fails

2. Security concern:
   ├─ run_security_scan_tool detects critical vulnerabilities
   ├─ Authentication/authorization errors
   └─ Data integrity risk

3. Data integrity risk:
   ├─ Database constraint violations
   ├─ Schedule generation produces invalid schedule
   └─ ACGME compliance violations detected

4. Repeated failures:
   ├─ Same tool fails >5 times in 5 minutes
   ├─ Error rate exceeds 50% for any tool
   └─ All fallbacks exhausted
```

#### Escalation Levels (from error-handling.md)

```python
class EscalationLevel(str, Enum):
    INFO = "info"           # Informational (log only)
    WARNING = "warning"     # Non-blocking issue (alert operator)
    CRITICAL = "critical"   # Blocking issue (escalate to team)
    EMERGENCY = "emergency" # System-level failure (escalate urgently)
```

**Escalation Routing:**
```
INFO:        Log to system, no alert
WARNING:     Alert operator (Slack, email)
CRITICAL:    Alert team lead, block operations
EMERGENCY:   Page on-call, incident created
```

### Error Handling in Real Workflows

#### Example 1: Schedule Generation Error Recovery

**Scenario:** schedule-optimization.generate() times out after 5 minutes

**Recovery:**
```
Timeout detected
  ↓
Escalate to CRITICAL (long solve time suspicious)
  ↓
Options:
  1. Increase timeout and retry (5 → 10 min)
  2. Use faster solver (cp_sat → greedy)
  3. Decompose problem (generate per-resident subproblems)
  4. Relax constraints (disable tier 3 objectives)

Decision: Try option 2 (faster solver)
  ↓
schedule-optimization.generate(algorithm="greedy", timeout=300)
  ↓
SUCCESS → Deploy with note about solver choice
FAILURE → Escalate to EMERGENCY (infeasible problem)
```

#### Example 2: Swap Execution Rollback

**Scenario:** Database transaction fails during swap.execute()

**Recovery:**
```
Execution fails
  ↓
Transaction automatically rolled back (implicit)
  ↓
Record failure in audit log
  ↓
Escalate to WARNING (data consistency risk)
  ↓
Retry Options:
  1. Retry swap immediately (retry-backoff)
  2. Suggest alternative candidate
  3. Escalate to coordinator

Decision: Retry with 1s delay
  ↓
SUCCESS → Notifyresidents, done
FAILURE → Escalate to coordinator (manual intervention needed)
```

#### Example 3: Deployment Failure with Rollback

**Scenario:** promote_to_production fails, trigger automatic rollback

**Recovery:**
```
Deployment fails
  ↓
Auto-rollback enabled
  ├─ Call rollback_deployment_tool()
  ├─ SUCCESS → Production restored, escalate WARNING
  └─ FAILURE → EMERGENCY (rollback failed, manual required)

If rollback succeeds:
  ├─ Notifyteam of deployment failure
  ├─ Log root cause for analysis
  └─ Re-plan deployment for next attempt

If rollback fails:
  ├─ Page on-call immediately (EMERGENCY)
  ├─ Manual investigation required
  └─ May require manual restoration from backup
```

---

## STEALTH: Hidden Compositions

### Implicit Compositions (Not Explicitly Documented)

#### 1. Validation Chains

Many skills implicitly compose validators:

**Example: Schedule Deployment**
```
Implicit validators called:
  1. ACGME rules (80-hour, 1-in-7, supervision)
  2. Coverage requirements (min residents per rotation)
  3. Credential requirements (qualified personnel)
  4. Temporal constraints (post-call relief, continuity)
  5. Absence handling (blocked dates excluded)
  6. Fairness metrics (workload distribution)

Not documented as separate "validation" skill
  → Each validator is part of SCHEDULING or acgme-compliance skill
  → Difficult to reuse validator in other contexts
```

**Recommendation:** Expose as explicit `ValidationComposition` pattern

#### 2. Decision Tree Embeddings

Skills embed decision trees rather than using separate "decision" skills:

**Example: Swap Execution Decision Logic**
```
Phase 2: Safety Checks embeds decision tree:
  if tier_1_violated:
    → REJECT
  elif tier_2_violated and not faculty_approval:
    → ESCALATE
  elif tier_3_degradation > threshold:
    → FLAG
  else:
    → PROCEED

Not documented as explicit composition
  → Decision tree is in swap_validation.py code
  → Difficult to modify decision logic
  → No way to reuse decision tree in other contexts
```

**Recommendation:** Extract decision trees as explicit `ConditionRoutingComposition`

#### 3. Transformation Pipelines

Data transformations between skills are implicit:

**Example: Schedule Generation Data Flow**
```
SchedulingContext (from Phase 1)
  ↓ extract constraints
FeasibilityAnalysis (from Phase 2)
  ↓ extract problem formulation
SchedulerInput (for Phase 3)
  ↓ solver produces
RawSchedule (unvalidated)
  ↓ validation converts
ValidatedSchedule (or ValidationIssues)
  ↓ conflict resolution transforms
FinalSchedule
  ↓ resilience assessment produces
HealthReport

Each transformation is implicit in skill implementation
  → Difficult to understand data flow
  → No schema documentation for intermediate formats
```

**Recommendation:** Document `DataTransformationComposition` pattern with schemas

#### 4. Cross-Cutting Concerns

Skills automatically handle cross-cutting concerns without explicit composition:

**Example: Audit Trail**
```
Every database write in any skill:
  1. Implicit: Create audit record
  2. Implicit: Record user ID + timestamp
  3. Implicit: Record action description
  4. Implicit: Store previous state

Not composed as separate "audit" skill
  → Audit is embedded in every skill
  → Difficult to audit or review
  → Difficult to modify audit strategy
```

**Recommendation:** Extract as explicit `AuditingComposition` mixin

#### 5. Caching Layers

Skills implicitly cache results:

**Example: Utilization Threshold Caching**
```
check_utilization_threshold called:
  1. Check cache (5-minute TTL)
  2. If cache miss:
     └─ Calculate from database
     └─ Store in cache
  3. Return (cached or fresh)

Not documented as separate "caching" composition
  → Difficult to understand when cache is valid
  → Difficult to invalidate cache strategically
  → No observability into cache effectiveness
```

**Recommendation:** Extract as explicit `CachingComposition` pattern

### Discovering Hidden Compositions

#### Method 1: Code Analysis

Scan skill implementations for:
```python
# Implicit validation composition
if not validate_X():
    return error()
if not validate_Y():
    return error()
if not validate_Z():
    return error()

# Implicit decision tree
if condition_a:
    return path_1()
elif condition_b:
    return path_2()
else:
    return path_3()

# Implicit data transformation
data = transform(input)
result = process(data)
output = extract(result)

# Implicit caching
if cache.has(key):
    return cache.get(key)
else:
    value = compute(key)
    cache.set(key, value)
    return value
```

#### Method 2: Dependency Analysis

Trace dependencies to find implicit compositions:
```
A calls B
B calls C
C calls D
  → Implicit composition: A → B → C → D
  → Not documented in A's SKILL.md
```

#### Method 3: State Machine Analysis

Look for implicit state machines:
```
Swap execution has implicit states:
  PENDING → INTAKE → SAFETY_CHECK → EXECUTION → VERIFICATION → MONITORED

Each state transition is implicit in execute_swap() method
  → Difficult to understand state flow
  → Difficult to add new states
  → No observability into state transitions
```

---

## Best Practices & Recommendations

### Best Practices for Skill Composition

#### 1. Explicit Dependency Declaration

**DO:**
```yaml
# In SKILL.md, declare dependencies
dependencies:
  required:
    - acgme-compliance
    - SCHEDULING
  optional:
    - RESILIENCE_SCORING

parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: [database-migration]
```

**DON'T:**
```python
# Don't hide dependencies in implementation
def execute_swap(swap_id):
    # Call dependency implicitly (not declared)
    acgme_result = validate_acgme(...)
    resilience_result = check_health(...)
```

#### 2. Clear Input/Output Contracts

**DO:**
```python
class SwapRequest(BaseModel):
    source_faculty_id: UUID
    source_week: date
    target_faculty_id: UUID
    target_week: date | None
    swap_type: Literal["one_to_one", "absorb"]
    reason: str

class SwapResponse(BaseModel):
    swap_id: UUID
    status: Literal["executed", "rejected", "escalated"]
    decision_rationale: str
    audit_trail: AuditRecord
```

**DON'T:**
```python
def execute_swap(request):
    # Implicit input structure (dict with undefined keys)
    # Implicit output structure (dict with optional keys)
    # No type safety
    pass
```

#### 3. Fail-Safe Defaults

**DO:**
```python
# Default to fail-fast for safety-critical operations
def validate_schedule(schedule):
    if not acgme_compliant:
        return FAIL  # Don't continue on ACGME violation
    if not coverage_adequate:
        return FAIL  # Don't continue on coverage failure
```

**DON'T:**
```python
# Don't silently continue on errors
def validate_schedule(schedule):
    try:
        acgme_compliant = check_acgme()
    except:
        pass  # Ignore error, continue
```

#### 4. Observable Compositions

**DO:**
```python
# Log each composition step
logger.info("Step 1/5: Backing up database...")
backup = await backup_database()

logger.info("Step 2/5: Generating schedule...")
schedule = await generate_schedule()

logger.info("Step 3/5: Validating ACGME compliance...")
validation = await validate_acgme(schedule)

# Emit metrics
metrics.composition_step_time("backup", backup.elapsed_ms)
metrics.composition_step_time("generate", generate.elapsed_ms)
```

**DON'T:**
```python
# Don't make compositions silent
schedule = await backup_database()
schedule = await generate_schedule()
schedule = await validate_acgme(schedule)
# No visibility into what happened or how long it took
```

#### 5. Testable Compositions

**DO:**
```python
# Mock dependencies for testing
@pytest.fixture
def mock_acgme_validator():
    validator = Mock()
    validator.validate.return_value = ValidationResult(is_valid=True)
    return validator

def test_schedule_generation_with_valid_acgme(mock_acgme_validator):
    # Test schedule generation in isolation
    # ACGME validation mocked
    pass

def test_schedule_generation_with_acgme_violation(mock_acgme_validator):
    mock_acgme_validator.validate.return_value = ValidationResult(is_valid=False)
    # Test error handling path
    pass
```

**DON'T:**
```python
# Don't test compositions against real dependencies
def test_schedule_generation():
    # Calls real database, real solver, real validation
    # Test is slow and fragile
    pass
```

### Recommendations for Better Compositions

#### Recommendation 1: Create Explicit Composition Documentation

**Current Gap:** No dedicated documentation for cross-skill workflows

**Proposed:** Create `docs/architecture/SKILL_COMPOSITIONS.md`

**Contents:**
- List all documented skill compositions (by use case)
- Dependency graphs (visual and textual)
- Data flow diagrams (input → transformations → output)
- Error handling strategy for each composition
- Performance characteristics (latency, throughput, resource usage)

**Example:**
```markdown
## Schedule Generation Composition

### Skills Involved
1. SCHEDULING (Phases 1-2, 4-5)
2. schedule-optimization (Phase 3)
3. acgme-compliance (Phase 5 validation)
4. safe-schedule-generation (Phase 5 safety)
5. RESILIENCE_SCORING (Phase 5 health check)

### Dependency Graph
[Visual DAG showing 5 phases and skill assignments]

### Data Flow
SchedulingContext → FeasibilityAnalysis → SchedulerInput →
RawSchedule → ValidatedSchedule → FinalSchedule

### Latency Breakdown
Phase 1: 2-5 min (requirements gathering)
Phase 2: 5 min (constraint propagation)
Phase 3: 10-30 min (schedule generation - slowest!)
Phase 4: 5-10 min (conflict resolution)
Phase 5: 5-15 min (validation + deployment)
Total: 27-65 minutes (depends on solver)

### Failure Handling
Phase 1 fails: Abort (data quality issue)
Phase 2 fails: Abort (constraint conflict)
Phase 3 fails: Rollback + escalate (solver issue)
Phase 4 fails: Continue (conflicts resolved manually)
Phase 5 fails: Rollback + critical escalation
```

#### Recommendation 2: Extract Implicit Compositions

**Current Gap:** Many compositions embedded in skill code

**Proposed:** Create explicit composition skills or patterns

**Examples:**

1. **ValidationComposition Skill**
   - Orchestrates multiple validators (ACGME, coverage, fairness, resilience)
   - Synthesis logic (all-or-nothing, best-effort, weighted)
   - Detailed error reporting per validator

2. **ConditionRoutingComposition Pattern**
   - Extract decision trees from skills
   - Document decision logic separately
   - Make routing logic testable and modifiable

3. **DataTransformationComposition Pattern**
   - Document intermediate data schemas
   - Make transformations explicit (not hidden in skill code)
   - Validate data at transformation boundaries

#### Recommendation 3: Add Observability to Compositions

**Current Gap:** Difficult to understand composition execution at runtime

**Proposed:** Add standardized observability

**Implementation:**
```python
class CompositionObserver:
    def on_step_start(self, step_name, step_number, total_steps):
        logger.info(f"Step {step_number}/{total_steps}: {step_name}")

    def on_step_success(self, step_name, result, elapsed_ms):
        logger.info(f"Step {step_name} completed in {elapsed_ms}ms")
        metrics.step_time.observe(elapsed_ms, labels={"step": step_name})

    def on_step_failure(self, step_name, error, elapsed_ms):
        logger.error(f"Step {step_name} failed after {elapsed_ms}ms: {error}")
        metrics.step_failure_count.inc(labels={"step": step_name})

    def on_composition_start(self, composition_name):
        logger.info(f"Starting composition: {composition_name}")

    def on_composition_complete(self, composition_name, status, elapsed_ms):
        logger.info(f"Composition {composition_name}: {status} ({elapsed_ms}ms)")
```

#### Recommendation 4: Performance Optimization Guide

**Current Gap:** No documentation on composition performance tuning

**Proposed:** Create `docs/development/COMPOSITION_PERFORMANCE.md`

**Contents:**
- Parallelism opportunities (which skills can run together)
- Bottleneck analysis (which skill is slowest)
- Caching strategies (what can be cached)
- Batch processing (how to process multiple items efficiently)
- Resource limits (CPU, memory, database connections)

**Example:**
```markdown
## Schedule Generation Performance Tuning

### Bottleneck Analysis
- Phase 1 (2-5 min): Requirements gathering (I/O bound)
- Phase 2 (5 min): Constraint propagation (CPU bound)
- **Phase 3 (10-30 min): Schedule generation (SOLVER - slowest!)**
- Phase 4 (5-10 min): Conflict resolution (I/O + CPU)
- Phase 5 (5-15 min): Validation + deployment (I/O bound)

### Optimization Strategy
1. **Reduce Phase 3 time:**
   - Use faster solver (greedy vs cp_sat)
   - Set tighter timeout (prefer feasible in 10 min vs optimal in 30 min)
   - Decompose problem (generate per-resident schedules)

2. **Parallelize Phase 5:**
   - ACGME validation + resilience check can run in parallel
   - Current: Sequential (5-15 min total)
   - Potential: Parallel (max 10 min, 2-3x speedup)

3. **Cache Phase 2:**
   - Constraint propagation is deterministic
   - If constraints haven't changed, reuse previous result
   - Potential: Skip Phase 2 entirely (5 min saved)
```

#### Recommendation 5: Composition Testing Framework

**Current Gap:** No systematic way to test compositions

**Proposed:** Create `backend/tests/test_compositions.py` with fixtures

**Implementation:**
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_skills():
    """Provide mocked skill results for composition testing"""
    return {
        "SCHEDULING": Mock(),
        "acgme-compliance": Mock(),
        "RESILIENCE_SCORING": Mock(),
    }

def test_schedule_generation_happy_path(mock_skills):
    """Test successful schedule generation composition"""
    # Mock each phase
    mock_skills["SCHEDULING"].phase1.return_value = scheduling_context
    mock_skills["SCHEDULING"].phase2.return_value = feasibility_analysis
    # ... etc

    # Run composition
    result = schedule_generation_composition(mock_skills)

    # Assert correct order
    assert mock_skills["SCHEDULING"].phase1.called_before(phase2)
    assert mock_skills["acgme-compliance"].validate.called
    assert result.status == "success"

def test_schedule_generation_acgme_violation(mock_skills):
    """Test error handling when ACGME validation fails"""
    mock_skills["acgme-compliance"].validate.return_value = ValidationResult(
        is_valid=False,
        critical_issues=5
    )

    # Run composition
    result = schedule_generation_composition(mock_skills)

    # Assert correct error handling
    assert result.status == "failed"
    assert "ACGME" in result.error_message
```

---

## Summary: Skill Composition Architecture

### Current State
- **96+ skills** documented across **47 directories**
- **10+ well-documented** meta-skills and domain skills
- **5 primary composition patterns** (sequential, parallel, map-reduce, conditional, hybrid)
- **3 levels of documentation** (SKILL.md metadata, workflow, reference)
- **Extensive error handling** (retry, fallback, escalation)

### Key Strengths
1. ✓ Clear separation of concerns (each skill has single responsibility)
2. ✓ Explicit dependency declaration in SKILL.md metadata
3. ✓ Comprehensive workflow documentation (5+ phase workflows)
4. ✓ Robust error handling strategies (retry, circuit breaker, escalation)
5. ✓ Real-world composition examples (schedule generation, deployment)

### Key Gaps
1. ✗ No cross-skill workflow documentation (how skills compose end-to-end)
2. ✗ Implicit compositions not documented (validators, decision trees, transformations)
3. ✗ No composition-level testing framework
4. ✗ Limited performance composition guidance
5. ✗ Observability could be improved (composition tracing)

### Recommendations (Priority Order)
1. **High Priority:** Create `docs/architecture/SKILL_COMPOSITIONS.md` (cross-skill workflows)
2. **High Priority:** Add observability to compositions (logging + metrics per step)
3. **Medium Priority:** Create composition testing framework (`tests/test_compositions.py`)
4. **Medium Priority:** Extract implicit compositions (make decision trees, validators explicit)
5. **Low Priority:** Add performance composition tuning guide (`docs/development/COMPOSITION_PERFORMANCE.md`)

---

**SEARCH_PARTY Operation Complete**

*G2_RECON Investigation of Skill Composition Patterns: CONCLUDED*
*Comprehensive documentation delivered to `.claude/Scratchpad/OVERNIGHT_BURN/SESSION_9_SKILLS/`*
