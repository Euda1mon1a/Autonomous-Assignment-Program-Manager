# 36-Hour Marathon: 9-Session Execution Plan

> **Purpose:** Maximize usage burn over 36 hours with 9 focused sessions
> **Sessions:** 9 (average 4 hours each, can overlap with CCW terminals)
> **Parallelism:** Each session can spawn 3-5 agents + 10 CCW terminals
> **Created:** 2025-12-30

---

## Session Overview

| Session | Focus | Est. Hours | Agents | CCW Tasks |
|---------|-------|------------|--------|-----------|
| 024 | MCP Tool Completion | 4 | 3 | 30 |
| 025 | Backend Service Tests | 4 | 3 | 25 |
| 026 | Frontend Test Coverage | 4 | 2 | 15 |
| 027 | E2E & Integration Tests | 4 | 3 | 10 |
| 028 | Security Hardening | 4 | 2 | 8 |
| 029 | Constraint System Audit | 3 | 3 | 5 |
| 030 | Database Optimization | 3 | 2 | 3 |
| 031 | Documentation Sync | 3 | 2 | 4 |
| 032 | Final Integration & PR | 3 | 5 | 0 |

**Total:** 36 hours, 25 agent spawns, 100 CCW tasks

---

## Session 024: MCP Tool Completion

**Duration:** 4 hours
**Branch:** `claude/session-024-mcp-tools`
**Agents:** 3 (ARCHITECT, TOOLSMITH, QA_TESTER)

### Objectives
1. Get all 81 MCP tools from 62% → 100% operational
2. Create missing backend endpoints for exotic frontier tools
3. Test MCP tool chain end-to-end

### CCW Terminal Allocation (30 tasks)
- **Terminals 1-3:** Core scheduling tools (tasks 1-10)
- **Terminals 4-6:** Exotic frontier tools (tasks 11-20)
- **Terminals 7-9:** Backend endpoints (tasks 21-30)

### Agent Work
```
ARCHITECT: Design backend endpoints for Hopfield, thermodynamics, game theory
TOOLSMITH: Implement MCP tool wiring to new endpoints
QA_TESTER: Create MCP integration test suite
```

### Success Criteria
- [ ] All 81 MCP tools return real data (no mocks)
- [ ] MCP integration tests pass
- [ ] Tool chain demo: generate schedule → validate → export

### Deliverables
- Updated `mcp-server/src/scheduler_mcp/server.py`
- New routes in `backend/app/api/routes/resilience.py`
- Test file: `mcp-server/tests/test_tool_chain.py`

---

## Session 025: Backend Service Tests

**Duration:** 4 hours
**Branch:** `claude/session-025-backend-tests`
**Agents:** 3 (QA_TESTER × 3, parallel)

### Objectives
1. Increase backend service test coverage from 21% → 80%+
2. Cover 37 untested services
3. Add edge case and error handling tests

### CCW Terminal Allocation (25 tasks)
- **Terminals 1-3:** Critical domain services (tasks 31-40)
- **Terminals 4-5:** Integration services (tasks 41-48)
- **Terminals 6-7:** Resilience & constraint tests (tasks 49-55)

### Agent Work (Parallel)
```
QA_TESTER_1: Services person_service through role_view_service (10)
QA_TESTER_2: Services xlsx_import through idempotency_service (8)
QA_TESTER_3: Resilience circuit_breaker, retry, constraints (7)
```

### Success Criteria
- [ ] 80%+ line coverage on backend/app/services/
- [ ] All constraint types have dedicated tests
- [ ] Circuit breaker and retry patterns tested

### Deliverables
- 25+ new test files in `backend/tests/services/`
- 7 new test files in `backend/tests/constraints/`
- Coverage report: `backend/htmlcov/`

---

## Session 026: Frontend Test Coverage

**Duration:** 4 hours
**Branch:** `claude/session-026-frontend-tests`
**Agents:** 2 (QA_TESTER × 2)

### Objectives
1. Increase frontend test coverage from 60% → 90%
2. Cover critical auth utilities (18K+ lines)
3. Test Templates feature (0% → 100%)

### CCW Terminal Allocation (15 tasks)
- **Terminals 1-2:** Critical features - auth, validation (tasks 56-63)
- **Terminals 3-4:** Feature components (tasks 64-70)

### Agent Work
```
QA_TESTER_1: auth.ts, validation.ts, hooks (8 tasks)
QA_TESTER_2: Templates, Conflicts, Import/Export components (7 tasks)
```

### Success Criteria
- [ ] auth.ts has comprehensive test coverage
- [ ] All 9 Templates components tested
- [ ] Login page and ProtectedRoute tested

### Deliverables
- `frontend/__tests__/lib/auth.test.ts`
- `frontend/__tests__/lib/validation.test.ts`
- `frontend/__tests__/features/templates/*.test.tsx`

---

## Session 027: E2E & Integration Tests

**Duration:** 4 hours
**Branch:** `claude/session-027-e2e-tests`
**Agents:** 3 (QA_TESTER, SCHEDULER, RESILIENCE_ENGINEER)

### Objectives
1. Create 10 end-to-end test scenarios
2. Test critical user journeys
3. Verify resilience framework under stress

### CCW Terminal Allocation (10 tasks)
- **Terminals 1-3:** E2E scenarios (tasks 71-76)
- **Terminals 4-5:** Integration scenarios (tasks 77-80)

### Agent Work
```
SCHEDULER: E2E schedule generation workflow
QA_TESTER: User journey tests (login, swap, export)
RESILIENCE_ENGINEER: N-1/N-2 integration scenarios
```

### Success Criteria
- [ ] 10 E2E scenarios pass
- [ ] Schedule → ACGME → Export workflow verified
- [ ] Swap request lifecycle tested end-to-end

### Deliverables
- `backend/tests/e2e/test_schedule_workflow.py`
- `backend/tests/e2e/test_swap_lifecycle.py`
- `backend/tests/e2e/test_resilience_recovery.py`

---

## Session 028: Security Hardening

**Duration:** 4 hours
**Branch:** `claude/session-028-security`
**Agents:** 2 (SECURITY_AUDITOR, CODE_REVIEWER)

### Objectives
1. Complete OWASP Top 10 audit
2. HIPAA/PHI exposure scan
3. OPSEC compliance verification

### CCW Terminal Allocation (8 tasks)
- **Terminals 1-2:** OWASP audit (tasks 81-84)
- **Terminals 3-4:** PHI/OPSEC audit (tasks 85-88)

### Agent Work
```
SECURITY_AUDITOR: SQL injection, XSS, auth bypass testing
CODE_REVIEWER: Review fixes, verify no regressions
```

### Success Criteria
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] PHI not exposed in API responses
- [ ] OPSEC compliance in logging

### Deliverables
- `docs/security/OWASP_AUDIT_RESULTS.md`
- Security fixes in `backend/app/api/routes/`
- Updated rate limiting configuration

---

## Session 029: Constraint System Audit

**Duration:** 3 hours
**Branch:** `claude/session-029-constraints`
**Agents:** 3 (SCHEDULER, COMPLIANCE_AUDITOR, QA_TESTER)

### Objectives
1. Verify all 18 constraints are registered
2. Document constraint interaction matrix
3. Add preflight validation

### CCW Terminal Allocation (5 tasks)
- **Terminals 1-2:** Constraint registration (tasks 89-93)

### Agent Work
```
SCHEDULER: Verify constraint registration in manager.py
COMPLIANCE_AUDITOR: Audit ACGME constraint correctness
QA_TESTER: Create constraint interaction tests
```

### Success Criteria
- [ ] 18/18 constraints registered and tested
- [ ] Constraint interaction matrix documented
- [ ] Preflight validation catches conflicts

### Deliverables
- `docs/architecture/CONSTRAINT_INTERACTION_MATRIX.md`
- `backend/app/scheduling/constraints/preflight.py`
- `backend/tests/constraints/test_interactions.py`

---

## Session 030: Database Optimization

**Duration:** 3 hours
**Branch:** `claude/session-030-db-optimization`
**Agents:** 2 (DBA, ARCHITECT)

### Objectives
1. Identify and create missing indexes
2. Optimize slow queries
3. Benchmark performance improvements

### CCW Terminal Allocation (3 tasks)
- **Terminal 1:** Index identification (task 94)
- **Terminal 2:** Migration creation (task 95)
- **Terminal 3:** Benchmarking (task 96)

### Agent Work
```
DBA: Analyze query patterns, identify missing indexes
ARCHITECT: Create Alembic migration for indexes
```

### Success Criteria
- [ ] All slow queries identified
- [ ] Index migration created and tested
- [ ] 50%+ improvement on identified slow queries

### Deliverables
- `backend/alembic/versions/YYYYMMDD_add_performance_indexes.py`
- `docs/architecture/QUERY_OPTIMIZATION_REPORT.md`
- Benchmark results in scratchpad

---

## Session 031: Documentation Sync

**Duration:** 3 hours
**Branch:** `claude/session-031-docs`
**Agents:** 2 (META_UPDATER, HISTORIAN)

### Objectives
1. Sync OpenAPI spec with actual endpoints
2. Update API documentation
3. Create MCP tool usage guide

### CCW Terminal Allocation (4 tasks)
- **Terminal 1:** OpenAPI sync (task 97)
- **Terminal 2:** API docs (task 98)
- **Terminal 3:** MCP guide (task 99)
- **Terminal 4:** CHANGELOG (task 100)

### Agent Work
```
META_UPDATER: OpenAPI, API docs, MCP guide
HISTORIAN: CHANGELOG, session summaries
```

### Success Criteria
- [ ] OpenAPI spec matches all endpoints
- [ ] MCP tool usage guide complete
- [ ] CHANGELOG updated with all sessions

### Deliverables
- Updated `backend/app/openapi.json`
- `docs/guides/MCP_TOOL_USAGE.md`
- Updated `CHANGELOG.md`

---

## Session 032: Final Integration & PR

**Duration:** 3 hours
**Branch:** Merge all session branches
**Agents:** 5 (RELEASE_MANAGER, QA_TESTER, CODE_REVIEWER, COORD_QUALITY, COORD_AAR)

### Objectives
1. Merge all 8 session branches
2. Run full test suite
3. Create comprehensive PR to main
4. After Action Review

### Agent Work
```
RELEASE_MANAGER: Merge branches, resolve conflicts
QA_TESTER: Run full backend + frontend test suites
CODE_REVIEWER: Final review of all changes
COORD_QUALITY: Quality gate verification
COORD_AAR: After Action Review for marathon
```

### Success Criteria
- [ ] All tests pass (backend + frontend)
- [ ] No merge conflicts
- [ ] PR created with comprehensive summary
- [ ] AAR document completed

### Deliverables
- PR #XXX to main with all marathon work
- `.claude/Scratchpad/MARATHON_AAR.md`
- Updated advisor notes

---

## Execution Timeline

```
Hour 0-4:   Session 024 (MCP Tools)
Hour 4-8:   Session 025 (Backend Tests)
Hour 8-12:  Session 026 (Frontend Tests)
Hour 12-16: Session 027 (E2E Tests)
Hour 16-20: Session 028 (Security)
Hour 20-23: Session 029 (Constraints)
Hour 23-26: Session 030 (DB Optimization)
Hour 26-29: Session 031 (Documentation)
Hour 29-32: Session 032 (Integration & PR)
Hour 32-36: Buffer for issues, Codex feedback
```

---

## Parallel Execution Strategy

### Each Session Can Run:
1. **ORCHESTRATOR** (main terminal) - coordinates agents
2. **3-5 Agents** (via Task tool) - domain specialists
3. **10 CCW Terminals** (parallel) - task execution

### Overlapping Sessions
Sessions can overlap if different domains:
- Session 025 (Backend) + Session 026 (Frontend) = No conflict
- Session 028 (Security) + Session 031 (Docs) = No conflict

### Context Handoff
Each session creates:
1. Handoff note in `.claude/Scratchpad/SESSION_XXX_HANDOFF.md`
2. Branch pushed to origin
3. PR created (if mergeable)

---

## Resource Allocation

### Agent Budget per Session

| Session | Opus | Sonnet | Haiku | Total |
|---------|------|--------|-------|-------|
| 024 | 1 | 2 | 0 | 3 |
| 025 | 0 | 3 | 0 | 3 |
| 026 | 0 | 2 | 0 | 2 |
| 027 | 1 | 2 | 0 | 3 |
| 028 | 1 | 1 | 0 | 2 |
| 029 | 0 | 2 | 1 | 3 |
| 030 | 0 | 2 | 0 | 2 |
| 031 | 0 | 1 | 1 | 2 |
| 032 | 1 | 3 | 1 | 5 |
| **Total** | **4** | **18** | **3** | **25** |

### CCW Terminal Budget

| Stream | Tasks | Terminals | Hours |
|--------|-------|-----------|-------|
| A (MCP) | 30 | 3 | 4 |
| B (Backend) | 25 | 3 | 4 |
| C (Frontend) | 15 | 2 | 4 |
| D (E2E) | 10 | 2 | 4 |
| E (Security) | 8 | 2 | 4 |
| F (Overflow) | 12 | 2 | 3 |
| **Total** | **100** | **14** | **23** |

---

## Risk Mitigation

### If Behind Schedule
1. **Drop Stream F** (overflow) - documentation can be deferred
2. **Merge early** - create PR with partial completion
3. **Parallel overlap** - run non-conflicting sessions concurrently

### If Tests Fail
1. **Isolate failures** - don't block other streams
2. **Create follow-up tasks** - document in HUMAN_TODO.md
3. **Mark as known issues** - proceed with PR

### If Merge Conflicts
1. **Resolve in integration session** (032)
2. **Use octopus merge** - merge multiple branches at once
3. **Escalate to human** - if structural conflict

---

## Post-Marathon

### Immediate
- [ ] PR merged to main
- [ ] All tests passing in CI
- [ ] Codex feedback addressed

### Follow-up (Next Week)
- [ ] Review marathon AAR
- [ ] Update standing orders based on learnings
- [ ] Plan next sprint based on remaining gaps

---

*Plan created by ORCHESTRATOR | Session 023*
*Ready for 36-hour marathon execution*
