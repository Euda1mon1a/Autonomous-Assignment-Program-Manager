# Coordinator Agent Patterns - Comprehensive Reconnaissance
## SESSION 025 SEARCH_PARTY: G2_RECON Agent Investigation

> **Mission:** Document coordinator agent patterns across the Autonomous Assignment Program Manager
> **Date:** 2025-12-30
> **Scope:** All 8 coordinators, delegation patterns, command structure, best practices
> **Authority:** G2_RECON Battlefield Awareness Mission

---

## EXECUTIVE SUMMARY

### Coordinator Inventory

The PAI (Parallel Agent Infrastructure) operates 8 domain-specialized coordinators reporting to ORCHESTRATOR:

| Coordinator | Domain | Created | Status | Agents | Scope |
|------------|--------|---------|--------|--------|-------|
| **COORD_ENGINE** | Scheduling Core | Session 001 | Active | SCHEDULER, OPTIMIZATION_SPECIALIST | Block generation, solver management, ACGME validation |
| **COORD_QUALITY** | Testing & Review | Session 001 | Active | QA_TESTER, CODE_REVIEWER, COMPLIANCE_AUDITOR | Tests, architecture, code review |
| **COORD_OPS** | Operations & Release | Session 001 | Active | RELEASE_MANAGER, TOOLSMITH, UX_SPECIALIST | Git, PRs, tools, deployments |
| **COORD_PLATFORM** | Backend Infrastructure | Session 005 | Active | BACKEND_ENGINEER, DBA, API_DEVELOPER | Database, APIs, services |
| **COORD_FRONTEND** | UI/UX | Session 005 | Active | FRONTEND_ENGINEER, UX_SPECIALIST | React components, forms, navigation |
| **COORD_RESILIENCE** | Safety & Compliance | Session 005 | Active | RESILIENCE_ENGINEER, BURNOUT_SENTINEL, SECURITY_AUDITOR | ACGME compliance, resilience, security |
| **COORD_INTEL** | Forensics & Investigation | Session 018 | Active | INTEL_FRONTEND, INTEL_BACKEND, INTEL_DBA, INTEL_INFRA, INTEL_QA, INTEL_DATA_VALIDATOR, G6_SIGNAL, HISTORIAN | Postmortems, bug reproduction, evidence preservation |
| **COORD_AAR** | Session Wrap-up | Session 016 | Active | DELEGATION_AUDITOR, HISTORIAN, G1_PERSONNEL | After-action reviews, metrics, handoff docs |

### Key Metrics

- **Total Lines of Coordinator Documentation:** 7,206 lines across 8 specifications
- **Agent Specifications:** 43 documented agents (coordinators + managed agents)
- **Coordination Patterns:** 12 distinct delegation workflows
- **Discovery Timeline:** Session 001 (3 coordinators) → Session 019 (8 coordinators)

---

## PART I: COORDINATOR INVENTORY & SPECIFICATIONS

### 1. COORD_ENGINE - Scheduling Domain Coordinator

**Purpose:** Manages scheduling core - block generation, rotation assignment, ACGME validation

**Managed Agents:**
- **SCHEDULER** - Generates schedules, respects constraints, solver orchestration
- **OPTIMIZATION_SPECIALIST** - Multi-objective schedule optimization (fairness, coverage, continuity)
- **CAPACITY_OPTIMIZER** - Staffing analysis, N-1/N-2 contingency

**Primary Workflows:**
1. **Schedule Generation Pipeline** - Backup → Generate → Validate → Optimize
2. **Conflict Detection & Resolution** - Parallel scan for time, ACGME, credential conflicts
3. **Emergency Coverage** - Handle deployments, TDY, medical leaves

**Decision Authority:**
- Can spawn managed agents independently
- Can modify schedule-related database state (with backup)
- Must escalate: ACGME violations, safety-critical decisions
- Coordinates with COORD_PLATFORM for database changes

**Key Pattern:** Scheduler-centric force multiplier - one SCHEDULER spawns multiple specialists for different optimization objectives

---

### 2. COORD_QUALITY - Testing & QA Domain Coordinator

**Purpose:** Manages testing, code review, architecture validation

**Managed Agents:**
- **QA_TESTER** - Unit, integration, E2E test execution
- **CODE_REVIEWER** - Code quality, security, performance review
- **COMPLIANCE_AUDITOR** - ACGME rule compliance verification

**Primary Workflows:**
1. **Pre-PR Quality Gate** - QA_TESTER (tests) + CODE_REVIEWER (review) + COMPLIANCE_AUDITOR (rules) in parallel
2. **Test Coverage Analysis** - Identify gaps, recommend new tests
3. **Regression Prevention** - Verify fixes don't break existing functionality

**Decision Authority:**
- Can run full test suite, spawn parallel test agents
- Can block PRs if quality gates fail
- Must escalate: Major test architecture changes, coverage targets >90%

**Key Pattern:** All-or-nothing synthesis - all three agents must pass for PR approval

---

### 3. COORD_OPS - Operations & Release Domain Coordinator

**Purpose:** Manages releases, git operations, tools, deployments

**Managed Agents:**
- **RELEASE_MANAGER** - Creates PRs, manages merge workflows, release notes
- **TOOLSMITH** - Creates/updates agent specs and skills, CI/CD configuration
- **UX_SPECIALIST** - User documentation, onboarding, feedback loops

**Primary Workflows:**
1. **Release Workflow** - Verify tests → Create PR → Merge → Deploy
2. **Tool/Skill Creation** - Define → Implement → Validate → Document
3. **Deployment Pipeline** - Staging → Production validation

**Decision Authority:**
- Can create/push branches, manage PRs
- Can modify git workflows, CI/CD configuration
- Must escalate: Production deployments, breaking API changes

**Key Pattern:** Sequential dependency - tests must pass BEFORE Release_Manager creates PR

---

### 4. COORD_PLATFORM - Backend Infrastructure Coordinator

**Purpose:** Manages backend APIs, database, services, infrastructure

**Managed Agents:**
- **BACKEND_ENGINEER** - FastAPI endpoints, service logic, request/response handling
- **DBA** - Database schema, migrations, query optimization, forensics
- **API_DEVELOPER** - API documentation, endpoint specification, OpenAPI/Swagger

**Primary Workflows:**
1. **API Development Pipeline** - Schema → Migration → Endpoint → Tests → Documentation
2. **Database Maintenance** - Backup → Modify → Verify → Test
3. **Performance Optimization** - Query analysis, connection pooling, caching

**Decision Authority:**
- Can modify database schema (with migration)
- Can change API contracts (with backward compatibility analysis)
- Must escalate: Breaking API changes, production data modifications

**Key Pattern:** DBA-first validation - database changes must be verified safe before dependent code changes

---

### 5. COORD_FRONTEND - UI/UX Domain Coordinator

**Purpose:** Manages React components, forms, pages, user experience

**Managed Agents:**
- **FRONTEND_ENGINEER** - React/Next.js components, hooks, state management
- **UX_SPECIALIST** - User workflows, accessibility, design patterns

**Primary Workflows:**
1. **Feature Implementation** - Design → Component → Integration → Testing
2. **UX Improvement** - Research → Prototype → Test → Implement
3. **Accessibility Audit** - WCAG compliance, keyboard navigation, screen reader support

**Decision Authority:**
- Can modify frontend code, create new components
- Can change UI layouts, forms, navigation
- Must escalate: Breaking changes to public components, API contract changes

**Key Pattern:** User-centric validation - UX_SPECIALIST reviews usability before code review

---

### 6. COORD_RESILIENCE - Safety & Compliance Coordinator

**Purpose:** Manages ACGME compliance, safety, resilience frameworks, security

**Managed Agents:**
- **RESILIENCE_ENGINEER** - Resilience framework implementation (SIR models, homeostasis, etc.)
- **BURNOUT_SENTINEL** - Burnout prediction, early warning systems, resident wellness
- **SECURITY_AUDITOR** - Authentication, authorization, data protection, HIPAA/OPSEC

**Primary Workflows:**
1. **ACGME Validation** - 80-hour rule, 1-in-7 rule, supervision ratios, continuity
2. **Resilience Assessment** - N-1/N-2 contingency analysis, coverage verification
3. **Security Audit** - Auth mechanisms, data handling, compliance violations

**Decision Authority:**
- Can block features that violate ACGME rules
- Can enforce security requirements, request changes
- Can modify resilience thresholds (with user approval)

**Key Pattern:** Safety-critical veto - RESILIENCE_ENGINEER can block any work violating constraints

---

### 7. COORD_INTEL - Forensics & Investigation Coordinator

**Purpose:** Manages postmortems, bug investigations, evidence preservation, narratives

**Managed Agents:**
- **INTEL_FRONTEND** (Layer 1) - UI/component forensics, screenshot capture, state inspection
- **INTEL_BACKEND** (Layer 2) - API forensics, query tracing, middleware inspection
- **INTEL_DBA** (Layer 3) - Database forensics, migration analysis, schema inspection
- **INTEL_INFRA** (Layer 4) - Container health, network connectivity, environment validation
- **INTEL_QA** (Layer 5) - Bug reproduction, minimal repro case creation
- **INTEL_DATA_VALIDATOR** (Layer 6) - Cross-layer data flow verification
- **G6_SIGNAL** - Evidence collection, artifact preservation, metric aggregation
- **HISTORIAN** - Narrative documentation for significant discoveries

**Primary Workflows:**
1. **Full-Stack Investigation** - Parallel spawn all layers when bug location unknown
2. **Timeline Reconstruction** - Git archaeology, log correlation, event sequencing
3. **Bug Reproduction Protocol** - Preserve evidence → Attempt → Document variations
4. **Root Cause Analysis (5-Whys)** - Symptom → Why 1-5 → Actionable improvement

**Decision Authority:**
- Can read any file, query databases (read-only)
- Can run git commands (log, blame, bisect)
- Must escalate: Security incidents, compliance violations, evidence pointing outside scope

**Key Pattern:** Parallel layer investigation - spawn all 6 layers simultaneously to capture evidence before it changes

---

### 8. COORD_AAR - After Action Review Coordinator

**Purpose:** End-of-session wrap-up, metrics aggregation, handoff documentation

**Managed Agents:**
- **DELEGATION_AUDITOR** - Analyzes delegation ratio, patterns, anti-patterns
- **HISTORIAN** - Creates narratives for noteworthy sessions
- **G1_PERSONNEL** - Tracks agent utilization, capacity planning (future)

**Primary Workflows:**
1. **Session Close Workflow** - Collect XO reports → Audit metrics → Assess significance → Update scratchpad → Generate handoff
2. **XO Collection** - Request self-evaluations from all active coordinators
3. **Metrics Aggregation** - Delegation ratio, parallel factor, anti-patterns
4. **Handoff Generation** - Priority items, pending decisions, watch items, open PRs

**Decision Authority:**
- Can spawn DELEGATION_AUDITOR and HISTORIAN independently
- Can update Scratchpad files (ORCHESTRATOR_ADVISOR_NOTES.md, DELEGATION_METRICS.md)
- Must escalate: Process improvements, organizational structure changes

**Key Pattern:** Auto-trigger at session end (when user signs off or context limit approaches)

---

## PART II: COORDINATION PATTERNS & DELEGATION STRATEGIES

### Pattern 1: Sequential Pipeline (Dependencies)

**When to Use:** Tasks have dependencies - output of A is input to B

**Example:** COORD_PLATFORM database modification workflow
```
COORD_PLATFORM
├─ 1. DBA: Backup database
│   ↓ (confirms success)
├─ 2. BACKEND_ENGINEER: Modify schema via migration
│   ↓ (confirms migration applied)
├─ 3. DBA: Verify integrity
│   ↓ (confirms no corruption)
└─ 4. API_DEVELOPER: Update endpoint docs
```

**Key Characteristic:** Each step must complete and validate before next begins
**Failure Mode:** Fail-fast - abort remaining steps if any step fails
**Tools:** Alembic migrations, database transactions, rollback procedures

---

### Pattern 2: Parallel Scatter-Gather (Independence)

**When to Use:** Multiple independent tasks can run simultaneously

**Example:** COORD_QUALITY pre-PR gate
```
COORD_QUALITY
├─ QA_TESTER: Run full test suite ────┐
├─ CODE_REVIEWER: Audit code quality ──┼─→ Gather & synthesize
└─ COMPLIANCE_AUDITOR: Verify rules ───┘
```

**Key Characteristic:** All agents start at same time, gather results after
**Failure Mode:** All-or-nothing - if any fails, PR blocked
**Tools:** Asyncio gather, parallel Bash execution, result synthesis

---

### Pattern 3: Coordinator-Led Hierarchy (Force Multiplier)

**When to Use:** Many agents needed; prevent ORCHESTRATOR bottleneck

**Example:** COORD_ENGINE schedule generation with multiple optimization objectives
```
ORCHESTRATOR
├─ COORD_ENGINE (coordinator)
│  ├─ SCHEDULER (generation)
│  ├─ OPTIMIZATION_SPECIALIST (fairness objective)
│  ├─ OPTIMIZATION_SPECIALIST (coverage objective)
│  ├─ OPTIMIZATION_SPECIALIST (continuity objective)
│  └─ CAPACITY_OPTIMIZER (N-1/N-2 verification)
```

**Key Characteristic:** Coordinator spawns specialists, synthesizes results
**Benefit:** Scales to 5-6 agents per coordinator; ORCHESTRATOR manages 6-8 coordinators
**Pattern:** Each coordinator handles domain autonomously

**Discovery:** Session 020 - User feedback "don't forget your coordinators, they're force multipliers"

---

### Pattern 4: Full-Stack Investigation (Parallel Layers)

**When to Use:** Bug location unknown; must capture evidence at every layer

**Example:** COORD_INTEL full-stack investigation (Session 014 Block Revelation)
```
COORD_INTEL
├─ INTEL_FRONTEND ──┐
├─ INTEL_BACKEND ───┼─→ INTEL_DATA_VALIDATOR (identify divergence point)
├─ INTEL_DBA ───────┤
├─ INTEL_INFRA ─────┘
├─ INTEL_QA (create repro case)
└─ G6_SIGNAL (preserve evidence)
```

**Key Characteristic:** Spawn all layers in parallel BEFORE analyzing results
**Critical:** Evidence must be captured immediately; bugs change systems
**Synthesis:** Data validator identifies which layer data first diverges

---

### Pattern 5: Feedback-Loop Validation (Iterative)

**When to Use:** Solution quality depends on feedback from previous attempt

**Example:** COORD_ENGINE schedule generation with resilience feedback
```
Round 1: Generate schedule
   ↓ (COORD_RESILIENCE validates)
Round 2: Adjust parameters based on violations
   ↓ (COORD_RESILIENCE re-validates)
Round 3: Finalize if compliant
   ↓ (COORD_QUALITY tests)
Round 4: Deploy if tests pass
```

**Key Characteristic:** Loop until success criteria met or max iterations reached
**Failure Mode:** Fail-tolerant - document all attempts, select best result
**Tools:** Constraint propagation, optimization solvers, validation loops

---

### Pattern 6: Context Isolation (Parallel Safety)

**When to Use:** Always - spawned agents have isolated context windows

**Key Discovery:** Session 016 - "if there is literally no cost to parallelization, why wouldn't you launch all 25 at once"

**Implications:**
- Spawned agents DO NOT consume parent's context window
- Can spawn 20-25 agents without context penalty
- Each agent must receive complete, self-contained context
- No assumptions about prior conversation or file reads

**Pattern Application:**
```
Parent Agent (context: task planning)
├─ Spawn Agent A (context: complete copy of requirement + paths + decisions)
├─ Spawn Agent B (context: complete copy of requirement + paths + decisions)
├─ Spawn Agent C (context: complete copy of requirement + paths + decisions)
└─ Gather results (parent context unaffected by agent operations)
```

---

## PART III: DELEGATION AUTHORITY MATRICES

### COORD_ENGINE Authority

**Can Independently Execute:**
- Spawn SCHEDULER, OPTIMIZATION_SPECIALIST, CAPACITY_OPTIMIZER
- Modify schedule-related database state (assignments, blocks)
- Run scheduling validation queries
- Create fallback schedules
- Trigger emergency coverage procedures

**Requires Approval:**
- Changing ACGME thresholds
- Modifying constraint definitions
- Breaking changes to schedule schema
- Production schedule deployments

**Must Escalate To:**
- COORD_RESILIENCE: If ACGME violations detected
- COORD_QUALITY: If test coverage inadequate
- ORCHESTRATOR: Cross-domain conflicts (scheduling vs. resilience trade-offs)

---

### COORD_QUALITY Authority

**Can Independently Execute:**
- Spawn QA_TESTER, CODE_REVIEWER, COMPLIANCE_AUDITOR
- Run full test suite, collect coverage metrics
- Block PRs that fail quality gates
- Create new test files, modify test configuration
- Recommend test refactoring

**Requires Approval:**
- Changing test thresholds (coverage %, performance benchmarks)
- Disabling tests (even temporarily)
- Modifying core testing infrastructure

**Must Escalate To:**
- ORCHESTRATOR: If tests reveal architectural issues
- COORD_INTEL: If test failures suggest bugs requiring investigation

---

### COORD_OPS Authority

**Can Independently Execute:**
- Create branches, commit code, push to origin
- Create and manage PRs
- Merge to main (after quality gates pass)
- Generate release notes, deployment documentation
- Update CI/CD configuration
- Create/update agent specs and skills

**Requires Approval:**
- Force pushing to main/master
- Deleting branches, history modification
- Changing deployment procedures
- Breaking changes to shared infrastructure

**Must Escalate To:**
- ORCHESTRATOR: If deployment affects multiple systems
- COORD_RESILIENCE: If security implications detected

---

### COORD_PLATFORM Authority

**Can Independently Execute:**
- Spawn BACKEND_ENGINEER, DBA, API_DEVELOPER
- Run database migrations (with backup)
- Modify API endpoints (non-breaking)
- Optimize queries, add indexes
- Create database diagnostic reports

**Requires Approval:**
- Breaking API changes
- Schema changes affecting multiple services
- Production data modifications

**Must Escalate To:**
- COORD_RESILIENCE: If changes affect compliance
- COORD_QUALITY: If tests need new coverage

---

### COORD_RESILIENCE Authority

**Can Independently Execute:**
- Validate ACGME compliance
- Verify resilience thresholds
- Run security audits
- Recommend safety improvements
- Block features violating constraints

**Requires Approval:**
- Changing ACGME thresholds (regulatory)
- Disabling security checks
- Accepting technical debt with compliance implications

**Must Escalate To:**
- User: If compliance violations or security incidents
- ORCHESTRATOR: If architectural changes needed

---

### COORD_INTEL Authority

**Can Independently Execute:**
- Read any file (investigation access)
- Query databases (read-only)
- Run git commands (log, blame, bisect)
- Spawn all INTEL layers in parallel
- Create investigation reports, evidence inventory

**Requires Approval:**
- Database modifications
- File edits (solutions must be routed to appropriate coordinator)
- Access to sensitive data (PII/PHI/OPSEC)

**Must Escalate To:**
- COORD_RESILIENCE: Security incidents, compliance violations
- COORD_OPS: Active incidents still causing harm
- ORCHESTRATOR: Legal/regulatory implications

---

### COORD_AAR Authority

**Can Independently Execute:**
- Spawn DELEGATION_AUDITOR, HISTORIAN
- Collect XO reports from coordinators
- Update Scratchpad files (advisor notes, metrics)
- Assess session significance, recommend HISTORIAN invocation
- Generate handoff notes

**Requires Approval:**
- HISTORIAN invocation (assessment is independent, narrative content reviewed)
- Changes to standing orders
- Organizational recommendations

**Must Escalate To:**
- ORCHESTRATOR: Metrics anomalies, HISTORIAN disagreements, process improvements

---

## PART IV: XO (Executive Officer) PATTERN

**Discovery:** Session 016 organizational expansion introduced XO duties to all coordinators

**Purpose:** Self-evaluation and reporting at session end for institutional memory

### XO Responsibilities

Each coordinator has implicit XO role with end-of-session duties:

| Duty | Report To | Content |
|------|-----------|---------|
| **Self-Evaluation** | COORD_AAR | Tasks completed, issues encountered, effectiveness |
| **Agent Effectiveness** | COORD_AAR | How well managed agents performed |
| **Knowledge Transfer** | HISTORIAN | Significant discoveries for narrative documentation |
| **Lessons Learned** | ORCHESTRATOR_ADVISOR_NOTES | Patterns to remember for future sessions |

### XO Report Format

```markdown
## COORD_[NAME] XO Report - [Date]

**Session Summary:** [1-2 sentences on work completed]

**Tasks Completed:**
- [Task 1]: [Outcome]
- [Task 2]: [Outcome]

**Agents Managed:**
| Agent | Tasks | Success Rate | Issues |
|-------|-------|--------------|--------|
| [Agent] | [N] | [%] | [any blockers] |

**Issues Encountered:**
1. [Issue]: [How resolved]
2. [Issue]: [How resolved]

**Lessons Learned:**
1. [Lesson]
2. [Lesson]

**Recommendations for Next Session:**
- [Suggestion]
- [Suggestion]
```

---

## PART V: COORDINATOR SIGNAL PATTERNS

### Broadcast Signals (From ORCHESTRATOR to Coordinators)

| Signal | Meaning | Coordinator Response | Typical Example |
|--------|---------|---------------------|-----------------|
| `TASK_ASSIGNED` | "You have work" | Accept task, spawn appropriate agents | "COORD_ENGINE: Generate Block 10" |
| `PRIORITY_ELEVATED` | "Escalate urgency" | Reorder work, spawn more agents, reduce scope | Production bug fix |
| `CONTEXT_LIMIT_WARNING` | "Approaching capacity" | Wrap up in progress, hand off to other coordinators | "80% context used; prioritize critical work" |
| `SESSION_CLOSE_IMMINENT` | "Prepare handoff" | COORD_AAR receives this at session end | Auto-triggers AAR workflow |

### Cascade Signals (From Coordinator to Managed Agents)

Coordinators use specific signal patterns when spawning:

**COORD_ENGINE → SCHEDULER:**
```yaml
signal: SCHEDULE_GENERATION_REQUESTED
context:
  period: "Q2 2025"
  constraints: ["ACGME", "N-1", "Supervision"]
  optimization_objectives: ["fairness", "coverage"]
expected_output: "Schedule with metadata"
```

**COORD_QUALITY → QA_TESTER:**
```yaml
signal: TEST_EXECUTION_REQUESTED
context:
  scope: "All tests in backend/"
  failure_tolerance: "None"
  report_format: "Structured (pass/fail/error counts)"
expected_output: "Test report with pass rate"
```

---

## PART VI: BEST PRACTICES & ANTI-PATTERNS

### Best Practices

#### 1. **Self-Contained Delegation**

Every coordinator-to-agent delegation must include:
- Complete mission statement (what needs doing)
- All file paths (absolute, not relative)
- Success criteria (measurable outcomes)
- Expected output format
- Escalation path (what to do if blocked)

```markdown
## Task for SCHEDULER

### Mission
Generate Block 10 assignment schedule respecting ACGME constraints.

### Inputs
- Period: Block 10 (2025-12-15 to 2025-12-21)
- Residents: [list]
- Faculty: [list]
- Constraint weights: [JSON]

### Success Criteria
- ✓ 80-hour rule satisfied
- ✓ 1-in-7 satisfied
- ✓ No hard credential conflicts

### Output Format
JSON with schedule + metadata

### Escalation
If infeasible → COORD_RESILIENCE assessment before declaring failure
```

#### 2. **Parallel Spawning for Independence**

When tasks are truly independent (no data flow between them), spawn in parallel:

```
Agent A (feature 1) ──┐
Agent B (feature 2) ──┼─→ Gather & verify
Agent C (tests)    ───┘
```

NOT sequentially (unless actual dependency).

#### 3. **Force Multiplier Hierarchy**

For 5+ agents, use coordinator structure:
```
ORCHESTRATOR (1 agent)
├─ COORD_X (1 agent)
│  ├─ Agent 1
│  ├─ Agent 2
│  └─ Agent 3
└─ COORD_Y (1 agent)
   ├─ Agent 4
   ├─ Agent 5
   └─ Agent 6
```

This reduces ORCHESTRATOR's coordination load while enabling 6+ agents to work in parallel.

#### 4. **Result Synthesis Strategy**

Know which synthesis pattern fits before spawning:

| Pattern | When | Example |
|---------|------|---------|
| **All-or-Nothing** | Safety-critical (all must pass) | ACGME validation: all rules must pass |
| **Best-Effort** | Multiple fallbacks acceptable | Try swap with Faculty A, B, C - any works |
| **Majority Vote** | Ambiguous decisions | 3 code reviewers - 2/3 approve = PR approved |
| **Weighted Aggregation** | Multi-objective | Schedule scoring: fairness 0.4, coverage 0.3, continuity 0.3 |

#### 5. **Escalation Clarity**

Define escalation path BEFORE spawning:

```markdown
**Can Independently Execute:**
- [Decision 1]
- [Decision 2]

**Requires Approval:**
- [Decision 3]

**Must Escalate:**
- [Decision 4] → [To whom]
- [Decision 5] → [To whom]
```

---

### Anti-Patterns to Avoid

#### 1. **One-Man Army** (ORCHESTRATOR doing all work)

**Problem:** ORCHESTRATOR directly executes instead of delegating
**Signal:** ORCHESTRATOR commits code directly, manages git operations, runs tests
**Fix:** Spawn RELEASE_MANAGER for PRs, COORD_QUALITY for tests, COORD_OPS for git

**Lesson:** Session 004 - User asked "who wrote the PR?" - forcing acknowledgment that ORCHESTRATOR did work that should have been delegated

#### 2. **Over-Delegation** (Delegating for delegation's sake)

**Problem:** Delegating trivial tasks adds overhead without benefit
**Signal:** Spawning agent for 5-second task, multiple rounds of context passing
**Fix:** Execute directly if task takes <5 seconds AND doesn't require specialization

**Threshold:** Coordination overhead > task time = bad delegation

#### 3. **Context Loss** (Incomplete handoff)

**Problem:** Agent spawned without sufficient context; must ask parent for clarification
**Signal:** Agent reports "missing context" or asks for re-explanation
**Fix:** Always include complete, self-contained context in spawn prompt

**Lesson:** Session 016 - All 24 agents need complete copies of requirements, not "read the prior conversation"

#### 4. **Circular Dependencies** (Agent A → B → A)

**Problem:** Agents delegating back to each other in cycles
**Signal:** Slow execution, context accumulation, potential deadlock
**Fix:** Plan delegation graph before spawning; identify circular dependencies upfront

#### 5. **Unbounded Parallelism** (Spawn unlimited agents)

**Problem:** Resource exhaustion, coordination overhead overwhelms benefits
**Signal:** "Let's spawn 100 agents for 100 tasks" - practical limit ~20-25
**Fix:** Use coordinator hierarchy, batch large workloads with concurrency limits

**Lesson:** Session 020 - Spawn up to 16 agents; coordinators handle complexity; scaling rule: 1-4 direct, 5-12 with coordinators, 13+ full hierarchy

#### 6. **Late Escalation** (Discovering blocker after spawning)

**Problem:** Agent spawned, then discovers work requires escalation
**Signal:** Agent reports "blocked waiting for X approval"
**Fix:** Identify escalation requirements BEFORE delegating; escalate proactively

---

## PART VII: COORDINATOR COORDINATION PATTERNS

### Pattern 1: Handoff Between Coordinators

**Scenario:** Work completes in COORD_A; needs follow-up in COORD_B

```
COORD_ENGINE (scheduler)
└─ Generates schedule
   ↓ (passes to)
COORD_RESILIENCE (compliance check)
└─ Validates ACGME
   ↓ (passes to)
COORD_QUALITY (test coverage)
└─ Ensures tests exist
```

**Handoff Protocol:**
1. Sender coordinator completes work
2. Sends complete status (what was done, what's ready)
3. Recipient coordinator receives context
4. Recipient spawns agents to continue

---

### Pattern 2: Parallel Coordinator Operations

**Scenario:** Multiple coordinators working on independent domains simultaneously

```
ORCHESTRATOR
├─ COORD_ENGINE (schedule generation) ──┐
├─ COORD_PLATFORM (database prep)     ──┼─→ Coordinate results
├─ COORD_FRONTEND (UI updates)        ──┤
└─ COORD_QUALITY (test creation)      ──┘
```

**Key:** No dependencies between coordinators; all run in parallel

**Coordination:** ORCHESTRATOR gathers results, verifies compatibility, synthesizes

---

### Pattern 3: Coordinator Escalation

**Scenario:** COORD_A needs approval/input from COORD_B or user

```
COORD_ENGINE (scheduling) discovers ACGME violation
   ↓
Escalates to COORD_RESILIENCE
   ↓ (RESILIENCE_ENGINEER analyzes)
Recommends solution: "Increase supervision ratio in Block 5"
   ↓
Returns to COORD_ENGINE with recommendation
   ↓
COORD_ENGINE regenerates with new constraint
```

---

### Pattern 4: XO Cross-Reporting

**Scenario:** End-of-session - all coordinators report to COORD_AAR

```
COORD_ENGINE (XO self-evaluation)     ─┐
COORD_QUALITY (XO self-evaluation)    ─┤
COORD_OPS (XO self-evaluation)        ─┤
... (all 6 coordinators)               ┤
                                        ↓
                                    COORD_AAR
                                    (aggregates)
                                        ↓
                                    Handoff summary
                                    + Metrics
                                    + Recommendations
```

---

## PART VIII: SESSION LIFECYCLE WITH COORDINATORS

### Session Startup

```
/startupO invoked
    ↓
ORCHESTRATOR initializes
    ↓
Load ORCHESTRATOR_ADVISOR_NOTES.md (prior session context)
    ↓
DELEGATION_AUDITOR spawned (capture session metrics)
    ↓
Check HUMAN_TODO.md for priorities
    ↓
FORCE_MANAGER assembles task forces
    ↓
Assign to coordinators based on domain
    ↓
Coordinators spawn agents in parallel
```

### During Session (Steady State)

```
User provides input/feedback
    ↓
ORCHESTRATOR evaluates
    ↓
Determines affected coordinators
    ↓
Spawn/update coordinators with new context
    ↓
Coordinators spawn specialists in parallel
    ↓
Parallel execution (context isolation = free)
    ↓
Result synthesis
    ↓
User feedback loop
```

### Session Closure

```
User indicates session ending
    ↓
COORD_AAR auto-triggers
    ↓
Collect XO reports from all coordinators
    ↓
DELEGATION_AUDITOR metrics
    ↓
HISTORIAN assessment (noteworthy sessions)
    ↓
Update ORCHESTRATOR_ADVISOR_NOTES.md
    ↓
Generate handoff for next session
    ↓
Commit incremental changes
    ↓
Session complete
```

---

## PART IX: COORDINATION DISCOVERY TIMELINE

### Session 001-004: Foundation (3 Coordinators)
- **Created:** COORD_ENGINE, COORD_QUALITY, COORD_OPS
- **Key Pattern:** Sequential handoff (Generation → Testing → Release)
- **Lesson:** Hierarchy prevents single point of failure (ORCHESTRATOR bottleneck)

### Session 005: Platform Expansion (6 Coordinators)
- **Created:** COORD_PLATFORM, COORD_FRONTEND, COORD_RESILIENCE
- **Key Pattern:** Parallel coordinators operate independently
- **Lesson:** Can scale to 6+ coordinators with zero coordination overhead

### Session 016: Force Multiplier Pattern
- **Insight:** User observed "don't forget your coordinators, they're force multipliers"
- **Key Pattern:** Coordinator hierarchy (ORCHESTRATOR → Coordinators → Agents)
- **Lesson:** Reduces ORCHESTRATOR coordination load; enables 20+ agent parallelism

### Session 018: COORD_INTEL (Forensics)
- **Created:** COORD_INTEL with 8-layer investigation team
- **Key Pattern:** Full-stack parallel investigation (all layers simultaneous)
- **Lesson:** Evidence capture requires parallel spawn before analysis

### Session 019: G-Staff Organizational Expansion
- **Added:** G-2 RECON, renamed G6_SIGNAL, added DEVCOM and MEDCOM
- **Key Pattern:** Military doctrine structure aligns with AI organizational needs
- **Lesson:** Metaphor became implementation; organizations mimic biological systems

---

## PART X: COORDINATOR SPAN OF CONTROL

### Recommended Agent Allocation

| Coordinator | Ideal Span | Min | Max | Rationale |
|------------|------------|-----|-----|-----------|
| COORD_ENGINE | 3-5 agents | 2 | 6 | Scheduling complexity demands diversity |
| COORD_QUALITY | 3 agents | 3 | 4 | Testing/review/compliance (fixed set) |
| COORD_OPS | 3-4 agents | 2 | 5 | Release management (variable scope) |
| COORD_PLATFORM | 3-4 agents | 3 | 5 | Backend complexity |
| COORD_FRONTEND | 2-3 agents | 2 | 4 | UI typically serial (one flow at a time) |
| COORD_RESILIENCE | 3 agents | 3 | 4 | Safety-critical (can't cut scope) |
| COORD_INTEL | 6-8 agents | 6 | 8 | Investigation layers (all parallel) |
| COORD_AAR | 2-3 agents | 2 | 3 | Session wrap-up (fixed workflow) |

**Total Practical Capacity:**
- 3 coordinators × 4 agents = 12 agents + ORCHESTRATOR = 13 total
- 6 coordinators × 4 agents = 24 agents + ORCHESTRATOR = 25 total

---

## PART XI: CRITICAL INSIGHTS

### Context Isolation Revelation (Session 016)

**Discovery:** Spawned agents have isolated context windows; they don't consume parent's context.

**Implications:**
1. Parallelism is essentially "free" from context perspective
2. Old 5-agent batching habit was based on false constraints
3. Can spawn 20-25 agents without context overhead
4. Each agent needs complete, self-contained prompt

**Before Session 016:** Conservative batching, sequential phases
**After Session 016:** Aggressive parallelism, maximum concurrency

### Force Multiplier Pattern (Session 020)

**Discovery:** User's observation "don't forget your coordinators, they're force multipliers"

**Impact:**
- ORCHESTRATOR stops trying to manage 15 agents directly
- Instead: Manage 6-8 coordinators, they manage agents
- Result: 85% delegation ratio, reduced ORCHESTRATOR bottleneck

**Scaling Rule:**
- 1-4 agents: Spawn directly from ORCHESTRATOR
- 5-12 agents: Use 1-2 coordinators
- 13+: Full 6-8 coordinator hierarchy

### Crash Resilience Pattern (Session 022)

**Discovery:** Sessions that write to disk incrementally survive crashes better

**Pattern:**
- Commit incrementally (~30 min or after major artifact)
- Save working state to Scratchpad files
- Use absolute file paths (survives context reset)
- Leave breadcrumbs for session continuity

**Result:** Session 022 recovered 2,614 lines despite IDE crash

---

## PART XII: HANDOFF CONTINUITY

### Scratchpad Files as Institutional Memory

| File | Purpose | Updated By |
|------|---------|------------|
| `ORCHESTRATOR_ADVISOR_NOTES.md` | Cross-session context, user profile, standing orders | ORCHESTRATOR + COORD_AAR |
| `DELEGATION_METRICS.md` | Running delegation statistics, trends | DELEGATION_AUDITOR + COORD_AAR |
| `.claude/plans/` | Current session plans, recovery points | ORCHESTRATOR at session start |
| `.claude/Scratchpad/` | Working notes, temporary analysis, breadcrumbs | All agents |
| `docs/sessions/` | Historical narratives (via HISTORIAN) | HISTORIAN |

### Handoff Prompt Components

Every session handoff should include:

```markdown
## Session Handoff Summary

**Session ID:** [XXX]
**Date:** [ISO date]
**Work Completed:** [1-3 sentences]

### Key Accomplishments
- [Accomplishment 1]
- [Accomplishment 2]

### Open PRs
- PR #XXX: [title] - [status]

### Uncommitted Changes
- [File 1]: [summary]

### Priority for Next Session
1. [P0 item]
2. [P1 item]

### Context for Next ORCHESTRATOR
- [Key insight 1]
- [Key insight 2]

### Files to Read
- [Relevant file 1]
- [Relevant file 2]
```

---

## SUMMARY & QUICK REFERENCE

### Coordinator Inventory (8 Total)

```
ORCHESTRATOR
├─ COORD_ENGINE (Scheduling)
├─ COORD_QUALITY (Testing)
├─ COORD_OPS (Release Management)
├─ COORD_PLATFORM (Backend)
├─ COORD_FRONTEND (UI/UX)
├─ COORD_RESILIENCE (Safety & Compliance)
├─ COORD_INTEL (Forensics & Investigation)
└─ COORD_AAR (Session Wrap-up)
```

### Key Patterns (5 Total)

1. **Sequential Pipeline** - Dependencies between steps
2. **Parallel Scatter-Gather** - Independent tasks
3. **Coordinator Force Multiplier** - Hierarchy for scale
4. **Full-Stack Investigation** - Parallel layer analysis
5. **Feedback Loop Validation** - Iterative refinement

### Best Practices (6 Total)

1. Self-contained delegation (complete context)
2. Parallel spawning for independence
3. Force multiplier hierarchy for 5+ agents
4. Clear result synthesis strategy
5. Define escalation paths upfront
6. Commit incrementally, write to disk frequently

### Anti-Patterns (6 Total)

1. One-man army (ORCHESTRATOR doing all work)
2. Over-delegation (delegating trivial tasks)
3. Context loss (incomplete handoff)
4. Circular dependencies (A → B → A)
5. Unbounded parallelism (spawn unlimited agents)
6. Late escalation (discovering blocker after spawn)

---

**END OF RECONNAISSANCE**

*This document captured coordinator patterns across 22+ sessions of autonomous development. Coordinators proved to be the scaling mechanism enabling 20+ parallel agents without bottleneck. Future sessions should leverage this architecture.*

*G2_RECON Out*
