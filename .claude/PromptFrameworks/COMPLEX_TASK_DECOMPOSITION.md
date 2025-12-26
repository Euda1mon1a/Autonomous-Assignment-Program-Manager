***REMOVED*** Complex Task Decomposition Framework

> **Purpose:** Break down large, ambiguous, or multi-phase tasks into manageable pieces
> **Applies To:** Multi-day projects, features with unclear requirements, cross-system changes

---

***REMOVED******REMOVED*** Overview

Complex tasks can be overwhelming and lead to **analysis paralysis** or **premature implementation**. This framework helps AI agents decompose large tasks into:

- **Atomic units** (single-responsibility tasks)
- **Dependency chains** (what must happen before what)
- **Parallel workstreams** (what can happen simultaneously)
- **Verification checkpoints** (how to know you're on track)

**Key Principle:** Break tasks down until each piece can be completed in **<2 hours** and verified independently.

---

***REMOVED******REMOVED*** Phase 1: Task Analysis

Before decomposing, understand the task holistically.

***REMOVED******REMOVED******REMOVED*** 1.1: Identify Task Type

| Task Type | Characteristics | Decomposition Strategy |
|-----------|-----------------|------------------------|
| **Feature** | Adds new capability | Layered (DB → Service → API → UI) |
| **Bug Fix** | Fixes broken behavior | Root cause → Fix → Regression tests |
| **Refactor** | Improves structure | Extract → Migrate → Cleanup |
| **Migration** | Changes infrastructure | Backup → Migrate → Validate → Rollback plan |
| **Integration** | Connects systems | Interface → Adapter → Tests → Monitoring |

**Example:** "Implement N-1 contingency analysis"
- **Type:** Feature (new capability)
- **Strategy:** Layered decomposition

---

***REMOVED******REMOVED******REMOVED*** 1.2: Define Boundaries

Answer these questions:

1. **What's in scope?**
   - What must be delivered?
   - What are the must-have features?

2. **What's out of scope?**
   - What can wait for later?
   - What are the nice-to-haves?

3. **What are the constraints?**
   - Time limits?
   - Compliance requirements (ACGME)?
   - Performance requirements?

4. **What are the unknowns?**
   - What needs research?
   - What assumptions need validation?

**Example: N-1 Contingency Analysis**

**In Scope:**
- Detect when loss of 1 person breaks coverage
- Calculate coverage metrics (% staffed)
- Flag N-1 violations in dashboard

**Out of Scope:**
- Auto-healing (generating replacement schedules)
- N-2 analysis (loss of 2 people)
- Historical trend analysis

**Constraints:**
- Must run in <5 seconds for 50-person schedule
- ACGME compliance must be maintained

**Unknowns:**
- Which algorithm? (Graph analysis? Brute force?)
- How to visualize results?

---

***REMOVED******REMOVED******REMOVED*** 1.3: Identify Affected Systems

Map all systems touched by this task:

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend                                                     │
│ - Dashboard widget (N-1 violations)                          │
│ - Schedule editor (warnings on N-1 risks)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│ Backend API                                                  │
│ - GET /resilience/n-minus-1                                  │
│ - POST /resilience/n-minus-1/analyze                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Service Layer                                                │
│ - NMinusOneAnalyzer (NEW)                                    │
│ - CoverageCalculator (MODIFY)                                │
│ - ACGMEValidator (USE)                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Database                                                     │
│ - resilience_metrics table (NEW)                             │
│ - assignments table (READ)                                   │
│ - persons table (READ)                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Background Tasks                                             │
│ - Celery task: Nightly N-1 analysis                          │
│ - Alert: Send notification if violations found               │
└─────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Phase 2: Decomposition Strategies

***REMOVED******REMOVED******REMOVED*** 2.1: Layered Decomposition (Bottom-Up)

For features that touch multiple architectural layers, decompose bottom-up:

```
Layer 1: Database
  ├─ Create migrations
  └─ Define models

Layer 2: Service Logic
  ├─ Implement business logic
  └─ Unit tests

Layer 3: API
  ├─ Define routes and schemas
  └─ Integration tests

Layer 4: Frontend
  ├─ Build components
  └─ Component tests

Layer 5: Integration
  ├─ End-to-end tests
  └─ Documentation
```

**Example: N-1 Contingency Analysis**

```markdown
1. **Database Layer** (30 min)
   - Create `resilience_metrics` table
   - Migration: Add columns for N-1 data
   - Test: Migration up/down

2. **Service Layer** (3 hours)
   - Implement `NMinusOneAnalyzer.analyze()`
   - Algorithm: For each person, simulate removal → check coverage
   - Unit tests: 10 test cases (happy path, edge cases)

3. **API Layer** (1 hour)
   - `GET /resilience/n-minus-1` (fetch latest results)
   - `POST /resilience/n-minus-1/analyze` (trigger analysis)
   - Integration tests: 5 scenarios

4. **Frontend Layer** (2 hours)
   - Dashboard widget showing N-1 violations
   - Color coding: GREEN (no violations), RED (violations)
   - Tests: Render tests + mock API

5. **Background Tasks** (1 hour)
   - Celery task: Nightly N-1 analysis
   - Alert: Email if violations found
   - Tests: Task execution + alerting

6. **Documentation** (30 min)
   - API docs
   - User guide: "Understanding N-1 Contingency"
```

**Total: ~8 hours, broken into 6 tasks (<2 hours each)**

---

***REMOVED******REMOVED******REMOVED*** 2.2: Dependency Decomposition (Critical Path)

Identify dependencies and create a task graph:

```
Task Graph for N-1 Analysis:

   ┌──────────────────┐
   │ 1. DB Migration  │ (BLOCKING)
   └────────┬─────────┘
            │
            ↓
   ┌──────────────────────────────┐
   │ 2. NMinusOneAnalyzer Service │
   └────────┬─────────────────────┘
            │
            ├─────────────────┬──────────────────┐
            ↓                 ↓                  ↓
   ┌────────────────┐  ┌──────────────┐  ┌─────────────┐
   │ 3a. API Routes │  │ 3b. Unit Tests│  │ 3c. Celery  │ (PARALLEL)
   └────────┬───────┘  └──────────────┘  └─────┬───────┘
            │                                   │
            ├───────────────────────────────────┘
            ↓
   ┌──────────────────┐
   │ 4. Frontend      │
   └────────┬─────────┘
            │
            ↓
   ┌──────────────────┐
   │ 5. E2E Tests     │
   └────────┬─────────┘
            │
            ↓
   ┌──────────────────┐
   │ 6. Documentation │
   └──────────────────┘
```

**Critical Path:** 1 → 2 → 3a → 4 → 5 → 6

**Parallel Work:** Tasks 3a, 3b, 3c can run in parallel after Task 2

---

***REMOVED******REMOVED******REMOVED*** 2.3: Vertical Slicing (End-to-End MVP)

For complex features, deliver a **minimal viable slice** first, then iterate:

**Slice 1 (MVP):** Basic N-1 detection for single day

```markdown
1. Service: Detect N-1 violations for single day
2. API: GET /resilience/n-minus-1/check?date=2024-01-15
3. Frontend: Simple table showing violations
4. Tests: Basic happy path

**Deliverable:** Users can check N-1 status for a specific day
```

**Slice 2:** Full week analysis

```markdown
1. Service: Extend to analyze full week
2. API: Add date range parameter
3. Frontend: Week view with violation counts
4. Tests: Multi-day scenarios

**Deliverable:** Users can analyze N-1 for a week
```

**Slice 3:** Automation and alerts

```markdown
1. Celery: Nightly analysis
2. Alerts: Email notifications
3. Dashboard: Real-time widget
4. Tests: Background task tests

**Deliverable:** Automated monitoring with proactive alerts
```

**Benefit:** Each slice is shippable and provides value incrementally.

---

***REMOVED******REMOVED******REMOVED*** 2.4: Risk-First Decomposition

For high-risk tasks, tackle the **riskiest unknowns first**:

**Example:** "Integrate with external credentialing API"

**Risks:**
1. API may be unreliable (downtime)
2. API may have rate limits
3. Data format may not match our schema
4. Authentication may be complex

**Risk-First Task Order:**

```markdown
1. **Spike: Test API reliability** (2 hours)
   - Make test calls to API
   - Measure uptime, latency, error rates
   - **Decision:** Can we depend on this API?

2. **Spike: Understand rate limits** (1 hour)
   - Test rate limits
   - **Decision:** Do we need request throttling?

3. **Spike: Map data schemas** (1 hour)
   - Fetch sample data
   - Compare to our `Person` model
   - **Decision:** What transformations are needed?

4. **Implement adapter** (2 hours)
   - Only after risks are understood

5. **Add error handling** (1 hour)
   - Retry logic, circuit breaker

6. **Tests** (2 hours)
   - Mock API responses
   - Test error scenarios
```

**Benefit:** De-risk early, pivot if necessary.

---

***REMOVED******REMOVED*** Phase 3: Parallel vs Sequential Execution

***REMOVED******REMOVED******REMOVED*** 3.1: Identifying Parallel Tasks

Tasks can run in parallel if:

- ✅ No data dependencies (Task B doesn't need Task A's output)
- ✅ No ordering requirements (can be done in any order)
- ✅ Different files/systems (no merge conflicts)

**Example: Parallel Tasks for N-1 Analysis**

After implementing `NMinusOneAnalyzer` service, these can run in parallel:

```markdown
Team Member A (or Agent 1):
- Implement API endpoint
- Write integration tests
- Update API documentation

Team Member B (or Agent 2):
- Create Celery task
- Configure scheduling
- Write Celery tests

Team Member C (or Agent 3):
- Build frontend widget
- Add to dashboard
- Write component tests
```

**Coordination:** Each team member works on different files, no conflicts.

---

***REMOVED******REMOVED******REMOVED*** 3.2: Identifying Sequential Tasks (Blocking)

Tasks must be sequential if:

- ❌ Data dependency (Task B needs Task A's output)
- ❌ Build dependency (Task B imports Task A's code)
- ❌ Testing dependency (Task B tests Task A's behavior)

**Example: Sequential Tasks for N-1 Analysis**

```markdown
1. Database migration (MUST BE FIRST)
   ↓
2. Service implementation (DEPENDS ON 1)
   ↓
3. API endpoint (DEPENDS ON 2)
   ↓
4. Frontend widget (DEPENDS ON 3)
```

You **cannot** build the frontend widget before the API endpoint exists.

---

***REMOVED******REMOVED******REMOVED*** 3.3: Using TodoWrite for Task Tracking

For complex tasks, use `TodoWrite` to track parallel and sequential work:

```markdown
todos:
  - content: "Create database migration for resilience_metrics"
    status: "completed"
    activeForm: "Creating database migration"

  - content: "Implement NMinusOneAnalyzer.analyze() service method"
    status: "completed"
    activeForm: "Implementing NMinusOneAnalyzer service"

  ***REMOVED*** These three can run in parallel
  - content: "Create API endpoint GET /resilience/n-minus-1"
    status: "in_progress"
    activeForm: "Creating API endpoint"

  - content: "Write unit tests for NMinusOneAnalyzer (12 test cases)"
    status: "pending"
    activeForm: "Writing unit tests"

  - content: "Create Celery task for nightly N-1 analysis"
    status: "pending"
    activeForm: "Creating Celery task"

  ***REMOVED*** Frontend depends on API being done
  - content: "Build dashboard widget for N-1 violations"
    status: "pending"
    activeForm: "Building dashboard widget"
```

---

***REMOVED******REMOVED*** Phase 4: Checkpoint Creation

Checkpoints are **verification points** where you confirm progress before continuing.

***REMOVED******REMOVED******REMOVED*** 4.1: Types of Checkpoints

| Checkpoint Type | Purpose | How to Verify |
|-----------------|---------|---------------|
| **Compilation** | Code compiles/runs | `pytest` or `npm run build` |
| **Test** | Functionality works | Unit/integration tests pass |
| **Integration** | Components connect | E2E tests pass |
| **Performance** | Meets speed requirements | Load tests, profiling |
| **Compliance** | Meets regulatory requirements | ACGME validation tests |
| **Review** | Code quality acceptable | Self-review, linter, skill review |

***REMOVED******REMOVED******REMOVED*** 4.2: Checkpoint Placement

Place checkpoints at:

1. **After each layer** (DB → Service → API → UI)
2. **Before merging** (all tests pass, docs updated)
3. **After risky tasks** (external API integration, algorithm change)
4. **Before destructive operations** (database migration, schedule regeneration)

**Example: Checkpoints for N-1 Analysis**

```markdown
Checkpoint 1: After Database Migration
- ✅ Migration runs successfully
- ✅ Migration rollback works
- ✅ No data loss in test database

Checkpoint 2: After Service Implementation
- ✅ Unit tests pass (12/12)
- ✅ Algorithm correctly identifies N-1 violations
- ✅ Performance: Analyzes 50-person schedule in <5 seconds

Checkpoint 3: After API Implementation
- ✅ Integration tests pass (5/5)
- ✅ API returns correct data format
- ✅ Error handling works (404, 500 scenarios)

Checkpoint 4: After Frontend Implementation
- ✅ Component tests pass
- ✅ Widget displays correctly in dashboard
- ✅ Color coding (GREEN/RED) works

Checkpoint 5: Before Merging
- ✅ All tests pass (unit + integration + E2E)
- ✅ Linter warnings fixed
- ✅ Documentation updated
- ✅ Code reviewed (self or peer)
- ✅ CHANGELOG.md updated
```

***REMOVED******REMOVED******REMOVED*** 4.3: Checkpoint Automation

Automate checkpoints with scripts:

```bash
***REMOVED***!/bin/bash
***REMOVED*** scripts/checkpoint.sh - Run before committing

echo "🔍 Running checkpoint verification..."

***REMOVED*** 1. Tests
echo "✅ Running tests..."
cd backend && pytest || exit 1

***REMOVED*** 2. Linting
echo "✅ Running linter..."
ruff check . || exit 1

***REMOVED*** 3. Type checking
echo "✅ Type checking..."
cd ../frontend && npm run type-check || exit 1

***REMOVED*** 4. ACGME compliance
echo "✅ ACGME compliance..."
cd ../backend && pytest -m acgme || exit 1

echo "✅ All checkpoints passed!"
```

Usage:

```bash
./scripts/checkpoint.sh
***REMOVED*** If passes, safe to commit
***REMOVED*** If fails, fix issues before committing
```

---

***REMOVED******REMOVED*** Phase 5: Handling Ambiguity

Complex tasks often have **unclear requirements**. Use these strategies:

***REMOVED******REMOVED******REMOVED*** 5.1: Spike Solutions (Time-Boxed Research)

When requirements are unclear, do a **spike** (time-boxed investigation):

```markdown
***REMOVED******REMOVED*** Spike: Determine best algorithm for N-1 analysis

**Time Box:** 2 hours

**Questions to Answer:**
1. What algorithms exist for this problem?
2. What are the trade-offs (speed, accuracy, complexity)?
3. Which algorithm fits our constraints (<5 seconds for 50 people)?

**Approach:**
- Research graph algorithms (NetworkX)
- Prototype 2-3 approaches
- Benchmark with sample data

**Deliverable:**
- Decision document: "We should use X algorithm because Y"
- Prototype code (throwaway, not production)

**Outcome:**
- If successful: Proceed with chosen algorithm
- If unsuccessful: Extend spike by 1 hour or escalate to human
```

***REMOVED******REMOVED******REMOVED*** 5.2: Progressive Refinement

If requirements are vague, start broad and narrow down:

**Iteration 1: Proof of Concept**
- Simplest possible implementation
- No error handling, no optimization
- **Goal:** Does this approach work at all?

**Iteration 2: Happy Path**
- Implement core functionality
- Basic error handling
- **Goal:** Can users complete the main task?

**Iteration 3: Edge Cases**
- Handle errors, edge cases
- Optimize performance
- **Goal:** Production-ready

**Iteration 4: Polish**
- Better UX, documentation
- Advanced features
- **Goal:** Delightful experience

***REMOVED******REMOVED******REMOVED*** 5.3: Decision Trees for Ambiguity

When faced with ambiguous choices, create decision trees:

```
Should we support cross-rotation swaps?
├─ YES
│  ├─ Pros: More flexibility, happier users
│  ├─ Cons: More complex validation, ACGME risk
│  └─ Decision: Only if ACGME validator can handle it
│
└─ NO
   ├─ Pros: Simpler code, lower risk
   ├─ Cons: Less flexible for users
   └─ Decision: Start with NO, add later if requested
```

**Document the decision** in code or ADR:

```python
***REMOVED*** backend/app/services/swap_executor.py

***REMOVED*** Decision: Do not support cross-rotation swaps in v1
***REMOVED*** Reason: ACGME validation complexity too high for initial release
***REMOVED*** Future: Can add in v2 if users request it
ALLOW_CROSS_ROTATION_SWAPS = False
```

---

***REMOVED******REMOVED*** Example: Full Decomposition for "Implement Schedule Optimizer"

***REMOVED******REMOVED******REMOVED*** Task Analysis

**Type:** Feature (new capability)

**In Scope:**
- Optimize existing schedules to reduce 80-hour violations
- Use OR-Tools constraint solver
- Preserve as many existing assignments as possible

**Out of Scope:**
- Generating schedules from scratch
- Multi-objective optimization (just minimize violations)

**Constraints:**
- Must maintain ACGME compliance
- Must run in <2 minutes for 50-person schedule

**Unknowns:**
- Which solver algorithm? (CP-SAT, GLOP, SCIP?)
- How to model constraints in OR-Tools?

---

***REMOVED******REMOVED******REMOVED*** Task Breakdown

```markdown
***REMOVED******REMOVED*** Phase 1: Research & Spike (4 hours)

***REMOVED******REMOVED******REMOVED*** Spike 1: OR-Tools Algorithm Selection (2 hours)
- Research CP-SAT, GLOP, SCIP solvers
- Prototype simple schedule optimization
- Benchmark: Which is fastest?
- **Checkpoint:** Decision doc on algorithm choice

***REMOVED******REMOVED******REMOVED*** Spike 2: Constraint Modeling (2 hours)
- Model 80-hour rule as constraint
- Model supervision ratios as constraint
- Test with sample data
- **Checkpoint:** Validated constraint model

---

***REMOVED******REMOVED*** Phase 2: Database Layer (1 hour)

***REMOVED******REMOVED******REMOVED*** Task 2.1: Create `optimizer_runs` table (30 min)
- Migration: Add table for optimization run history
- Columns: id, started_at, completed_at, violations_before, violations_after

***REMOVED******REMOVED******REMOVED*** Task 2.2: Test migration (30 min)
- Test up/down migrations
- **Checkpoint:** Migration works

---

***REMOVED******REMOVED*** Phase 3: Service Layer (6 hours)

***REMOVED******REMOVED******REMOVED*** Task 3.1: Implement `ScheduleOptimizer.optimize()` (3 hours)
- Load existing assignments
- Model constraints in OR-Tools
- Run solver
- Return optimized assignments

***REMOVED******REMOVED******REMOVED*** Task 3.2: Write unit tests (2 hours)
- Happy path: Optimization reduces violations
- Edge case: No violations to optimize
- Edge case: Unsolvable (no valid solution)
- **Checkpoint:** 10/10 tests passing

***REMOVED******REMOVED******REMOVED*** Task 3.3: Add ACGME validation (1 hour)
- Validate optimized schedule maintains compliance
- Rollback if validation fails
- **Checkpoint:** All optimized schedules pass ACGME validation

---

***REMOVED******REMOVED*** Phase 4: API Layer (2 hours)

***REMOVED******REMOVED******REMOVED*** Task 4.1: Create `POST /schedules/{id}/optimize` endpoint (1 hour)
- Request: `OptimizeRequest(preserve_existing=True)`
- Response: `OptimizeResponse(violations_reduced=5)`

***REMOVED******REMOVED******REMOVED*** Task 4.2: Integration tests (1 hour)
- Test: Successful optimization
- Test: No changes needed (already optimal)
- Test: Optimization timeout
- **Checkpoint:** 5/5 integration tests passing

---

***REMOVED******REMOVED*** Phase 5: Frontend (3 hours)

***REMOVED******REMOVED******REMOVED*** Task 5.1: Add "Optimize" button to schedule editor (1 hour)
- Button triggers API call
- Show loading state during optimization

***REMOVED******REMOVED******REMOVED*** Task 5.2: Display optimization results (1 hour)
- Show: "Reduced violations from 8 to 3"
- Allow user to accept or reject changes

***REMOVED******REMOVED******REMOVED*** Task 5.3: Component tests (1 hour)
- Test button click
- Test loading state
- Test result display
- **Checkpoint:** Component tests passing

---

***REMOVED******REMOVED*** Phase 6: Background Tasks (2 hours)

***REMOVED******REMOVED******REMOVED*** Task 6.1: Create Celery task for scheduled optimization (1 hour)
- Weekly task: Optimize all schedules
- Email results to admin

***REMOVED******REMOVED******REMOVED*** Task 6.2: Celery tests (1 hour)
- Test task execution
- Test email sending
- **Checkpoint:** Celery tests passing

---

***REMOVED******REMOVED*** Phase 7: Documentation (1 hour)

***REMOVED******REMOVED******REMOVED*** Task 7.1: Update API docs (30 min)
- Document `/schedules/{id}/optimize` endpoint

***REMOVED******REMOVED******REMOVED*** Task 7.2: Update user guide (30 min)
- "How to Optimize Your Schedule" section
- **Checkpoint:** Docs reviewed and accurate

---

***REMOVED******REMOVED*** Total Estimated Time: 19 hours
```

---

***REMOVED******REMOVED******REMOVED*** Dependency Graph

```
Spike 1 & 2 (PARALLEL)
    ↓
Database Migration
    ↓
ScheduleOptimizer Service
    ↓
    ├─────────────┬─────────────┐
    ↓             ↓             ↓
API Endpoint   Celery Task   Unit Tests (PARALLEL)
    ↓             ↓
    └──────┬──────┘
           ↓
    Frontend Component
           ↓
    Documentation
```

---

***REMOVED******REMOVED*** Summary: Decomposition Checklist

Before starting a complex task:

- [ ] **Analyze task type** (feature, bug, refactor, migration)
- [ ] **Define scope** (what's in, what's out, constraints, unknowns)
- [ ] **Identify affected systems** (DB, service, API, frontend, background)
- [ ] **Choose decomposition strategy** (layered, dependency, vertical slice, risk-first)
- [ ] **Break into <2-hour tasks**
- [ ] **Map dependencies** (what blocks what)
- [ ] **Identify parallel work** (what can run concurrently)
- [ ] **Place checkpoints** (how to verify progress)
- [ ] **Handle ambiguity** (spikes, progressive refinement, decision trees)
- [ ] **Track with TodoWrite** (if multi-phase project)

---

**Remember:** The goal of decomposition is to **reduce cognitive load** and make progress **verifiable at every step**. Break it down, execute incrementally, verify continuously.
