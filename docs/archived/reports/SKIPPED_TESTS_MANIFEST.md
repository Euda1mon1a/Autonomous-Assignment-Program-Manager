# G2_RECON Intelligence Report: Skipped Test Analysis

**Mission Date:** 2025-12-31
**Classification:** Development Intelligence
**Total Tests Found:** 96 skip decorators across 11 files
**Status:** 3 Categories - HIGH priority unskip candidates identified

---

## Executive Summary

The codebase contains **96 skipped/skipif test decorators** organized into 7 categories by root cause:

| Category | Count | Severity | Action |
|----------|-------|----------|--------|
| **DEBT-016 Placeholders** | 38 | HIGH | Unskip immediately - services implemented |
| **Missing Dependencies** | 35 | LOW | Keep skipped - optional features |
| **Known Issues** | 1 | CRITICAL | Fix test isolation + unskip |
| **Not Implemented** | 8 | MEDIUM | Defer - feature in progress |
| **Vector DB (PostgreSQL)** | 9 | LOW | Keep skipped - environment-specific |
| **MCP Server Optional** | 1 | LOW | Keep skipped - optional integration |
| **Other/Misc** | 2 | MEDIUM | Implement fixtures + unskip |

---

## Category 1: DEBT-016 Placeholders - HIGHEST PRIORITY

**Impact:** 38 skipped tests
**Recommendation:** UNSKIP IMMEDIATELY
**Reason:** Services are already implemented; tests are waiting for fixtures

### Files Affected

#### 1. `tests/services/test_fmit_scheduler_service.py` - 14 skipped tests

**Reason:** All skip with "DEBT-016: Placeholder - needs fixtures and assertions"

**Status:** Service EXISTS at `app/services/fmit_scheduler_service.py`

**Skipped Methods:**
- `test_get_fmit_schedule_success`
- `test_get_fmit_schedule_empty_range`
- `test_generate_fair_schedule_success`
- `test_generate_fair_schedule_validates_acgme`
- `test_generate_fair_schedule_no_faculty`
- `test_validate_schedule_detects_conflicts`
- `test_validate_schedule_clean`
- `test_assign_fmit_week_success`
- `test_assign_fmit_week_already_assigned`
- `test_find_swap_candidates`
- `test_find_swap_candidates_no_matches`
- `test_full_schedule_generation_workflow`
- `test_schedule_recovery_after_failure`

**Unskip Procedure:**
1. Uncomment `from app.services.fmit_scheduler_service import FMITSchedulerService` (line 28)
2. Create fixtures in conftest.py or file (see `tests/conftest.py` patterns)
3. Replace `pass` statements with assertions
4. Remove `@pytest.mark.skip` decorators

**Estimated Effort:** 2-3 hours per test suite

---

#### 2. `tests/services/test_call_assignment_service.py` - 16 skipped tests

**Reason:** All skip with "DEBT-016: Placeholder - needs fixtures and assertions"

**Status:** Service EXISTS at `app/services/call_assignment_service.py`

**Skipped Methods:**
- `test_assign_call_by_rules` (and 14 more)
- Tests for: validation, eligibility, equity reporting, transaction handling

**Unskip Procedure:** Identical to FMIT scheduler (same debt ticket)

**Estimated Effort:** 2-3 hours per test suite

---

#### 3. `tests/test_schedule_routes.py` - 12 skipped tests

**Reason:** "DEBT-016: Placeholder - needs auth fixtures and test data"

**Status:** Routes EXISTS at `app/api/routes/schedule.py`

**Endpoints Being Tested:**
- `POST /api/schedule/generate` - Schedule generation
- `POST /api/schedule/validate` - Schedule validation
- `POST /api/schedule/emergency-coverage` - Emergency coverage
- `GET /api/schedule` - Schedule retrieval
- `DELETE /api/schedule` - Bulk deletion

**Skipped Methods:**
- `test_generate_schedule_success`
- `test_validate_schedule_success`
- `test_generate_emergency_coverage_success`
- `test_get_schedule_by_id_success`
- `test_list_schedules_success`
- `test_delete_schedule_success`
- (and 6 more)

**Unskip Procedure:**
1. Use test client from `conftest.py`
2. Create auth headers fixture (see lines 36-45 for pattern)
3. Create sample data fixtures (rotation templates, persons, blocks)
4. Remove `@pytest.mark.skip` decorators
5. Add assertions to verify response structure and status codes

**Estimated Effort:** 3-4 hours

---

### Unskip Strategy for DEBT-016 Category

**Rationale:** These tests are STALLED because the implementation is COMPLETE but fixture setup is tedious. Unblocking these will:
- Reveal any recent regressions in implemented services
- Provide regression coverage going forward
- Unblock other dependent tests

**Parallel Implementation:**
Could assign 3 developers to each file simultaneously since they're independent.

---

## Category 2: Missing Dependencies - KEEP SKIPPED

**Impact:** 35 skipped tests
**Recommendation:** KEEP SKIPPED (make conditional in CI)
**Reason:** Optional dependencies not in base requirements

### Dependencies Not Installed

| Dependency | Count | Purpose | Status |
|------------|-------|---------|--------|
| **ndlib** | 30 tests | Burnout contagion modeling (epidemiology) | Optional |
| **PyQUBO** | 1 test | Quantum optimization | Optional |
| **dwave-samplers** | 1 test | D-Wave quantum annealing | Optional |
| **NetworkX** | 1 test | Graph analysis for hub detection | Optional |

### Files Affected

#### `tests/unit/test_contagion_model.py` - 30 skipped tests
- All skip with "ndlib not installed"
- These are Tier 4 resilience framework tests (burnout epidemiology)
- Part of cross-disciplinary resilience (optional advanced features)

#### `tests/scheduling/test_quantum_solver.py` - 2 skipped tests
- PyQUBO and dwave-samplers (quantum computing, exotic frontier)
- Cutting-edge research code

#### `tests/test_resilience_hub_analysis.py` - 1 skipped test
- NetworkX dependency
- Hub/centrality analysis using graph theory

#### `tests/unit/test_contagion_model.py` line 643
- Single unique skip: "ndlib has known issues with single-node networks"
- Can be unskipped when ndlib is available but test itself has known issue

---

## Category 3: CRITICAL - Known Issues / Test Isolation

**Impact:** 1 skipped test
**Recommendation:** URGENT FIX - Fix test isolation then unskip
**Severity:** CRITICAL

### File: `tests/resilience/test_resilience_load.py` line 646

**Skip Reason:** "SQLAlchemy object lifecycle issue in concurrent test fixture - requires test isolation fix"

**Test:** `test_concurrent_contingency_analyses()`

**Root Cause:** SQLAlchemy objects are being shared between concurrent test threads/tasks, causing object lifecycle issues (detached from session, reused across contexts).

**Current State:** Blocked on test isolation fix

**Unskip Strategy:**
1. Create isolated database sessions per concurrent task
2. Use `AsyncSession` with proper context management
3. Add fixture scope isolation (`function` scope for concurrent tests)
4. Consider using `pytest-asyncio` fixtures with proper cleanup

**Estimated Effort:** 1-2 hours diagnosis + 2-3 hours fix

**Priority:** HIGH - This is a resilience framework load test that could reveal real issues

---

## Category 4: Not Yet Implemented - DEFER UNSKIP

**Impact:** 8 skipped tests
**Recommendation:** DEFER - Feature in progress
**Status:** Feature incomplete but tests are written

### File: `tests/integration/bridges/test_kalman_workload_bridge.py` - 8 skipped tests

**Skip Reason:** "WorkloadKalmanFilter not yet implemented"

**Implementation Status:** Stub exists at `app/resilience/workload_kalman_filter.py` (raises NotImplementedError)

**Purpose:** Kalman filtering for workload estimation (Tier 3+ resilience framework - materials science creep/fatigue modeling)

**Tests Cover:**
- Convergence with consistent measurements
- Filter behavior with measurement conflicts
- Filter adaptation to regime changes
- Outlier handling
- Burnout state prediction
- (and 3 more)

**Unskip Condition:** When `WorkloadKalmanFilter.__init__()` no longer raises NotImplementedError

**Estimated Implementation Effort:** 4-6 hours (advanced signal processing)

---

## Category 5: Vector Database - Keep Skipped (Environment-Specific)

**Impact:** 9 skipped tests
**Recommendation:** KEEP SKIPPED (requires PostgreSQL with pgvector)
**Reason:** SQLite used in CI/testing; pgvector only in production

### File: `tests/services/test_rag_service.py` - 9 skipped tests

**Skip Reason:** "Requires PostgreSQL with pgvector extension"

**Tests Affected:**
- `test_ingest_document_success` - Document embedding + storage
- `test_ingest_document_with_chunking` - Large document splitting
- `test_search_documents_semantic_similarity` - Vector similarity search
- `test_search_documents_hybrid_search` - Keyword + vector hybrid
- `test_delete_document_success` - Document removal + cascade
- `test_update_document_success` - Document re-embedding
- `test_generate_qa_pairs_from_document` - QA generation
- `test_semantic_search_ranking` - Ranking by relevance
- `test_llm_qa_generation` - LLM-based Q&A

**Note:** RAG service itself (chunking, basic ingestion) CAN be tested with SQLite - these tests should remain skipped

**Why:** pgvector is a PostgreSQL extension that requires:
- Full PostgreSQL instance (not SQLite)
- pgvector extension compiled and installed
- Vector similarity functions

**CI Strategy:** Run vector DB tests in separate Docker-based integration test suite (not main CI)

---

## Category 6: MCP Server Optional - Keep Skipped

**Impact:** 1 skipped test
**Recommendation:** KEEP SKIPPED (requires MCP server running)

### File: `tests/integration/test_orchestration_e2e.py` line 1164

**Skip Reason:** "MCP server not enabled in configuration"

**Test:** `test_real_mcp_tool_execution()`

**Status:** Requires:
- MCP server running (docker-compose up mcp-server)
- Backend API accessible from MCP container
- Test database populated

**Why Skipped:** Optional integration - not required for core functionality

**When to Run:** In end-to-end integration test suite (not main unit tests)

---

## Category 7: Other / Miscellaneous

**Impact:** 2 skipped tests
**Recommendation:** Implement fixtures and unskip

### File: `tests/scheduling/periodicity/test_anti_churn.py` lines 392-404

**Skip Reason:** "Requires mock Assignment objects with block.date"

**Tests:**
- `test_detect_weekly_pattern` - Detect 7-day patterns
- `test_detect_subharmonics` - Detect 14d/28d patterns

**Issue:** Tests need Assignment mock objects with actual date data, not just stubs

**Unskip Strategy:**
1. Create fixtures that generate mock Assignment objects with block.date
2. Mock Block objects with various date values
3. Replace `pass` with actual assertions

**Estimated Effort:** 1-2 hours

---

## Recommendations Summary

### Immediate Actions (Next Sprint)

| Priority | Action | File | Count | Est. Hours |
|----------|--------|------|-------|-----------|
| **P1** | Fix test isolation + unskip | `test_resilience_load.py` | 1 | 3-5 |
| **P2** | Unskip DEBT-016 placeholders | 3 files | 42 | 8-10 |
| **P3** | Implement anti-churn fixtures | `test_anti_churn.py` | 2 | 1-2 |

### Medium-Term (When Features Ready)

| Priority | Action | File | Count | Status |
|----------|--------|------|-------|--------|
| **P4** | Implement Kalman filter | `test_kalman_workload_bridge.py` | 8 | In progress |

### Keep Skipped (Conditional CI)

| Category | Count | Condition |
|----------|-------|-----------|
| Optional dependencies | 35 | Run in `test:optional` target only |
| Vector DB | 9 | Run in Docker integration suite |
| MCP server | 1 | Run in E2E integration suite |

---

## Test Execution Recommendations

### Current CI (Main Tests)
```bash
pytest tests/ \
  --ignore=tests/unit/test_contagion_model.py \
  --ignore=tests/scheduling/test_quantum_solver.py \
  --ignore=tests/test_resilience_hub_analysis.py \
  --ignore=tests/services/test_rag_service.py \
  --ignore=tests/integration/test_orchestration_e2e.py \
  --ignore=tests/integration/bridges/test_kalman_workload_bridge.py
```

### With Optional Dependencies
```bash
pytest tests/ \
  --ignore=tests/services/test_rag_service.py \
  --ignore=tests/integration/test_orchestration_e2e.py \
  --ignore=tests/integration/bridges/test_kalman_workload_bridge.py
```

### E2E/Integration (Requires Docker)
```bash
pytest tests/integration/ \
  tests/services/test_rag_service.py \
  tests/integration/bridges/test_kalman_workload_bridge.py
```

---

## Regression Risk Assessment

### HIGH RISK (Missing Tests)
- **DEBT-016 services** - 3 services with NO test coverage
  - FMITSchedulerService (fair FMIT scheduling)
  - CallAssignmentService (on-call assignment)
  - Schedule routes (core API endpoints)
  - **Risk:** Recent regressions not detected
  - **Mitigation:** Unskip immediately

### MEDIUM RISK (Known Issues)
- **Concurrent resilience test** - 1 test blocking load testing
  - **Risk:** Can't verify N-1/N-2 contingency at scale
  - **Mitigation:** Fix test isolation, unskip

### LOW RISK (Optional Features)
- Quantum solver tests (cutting-edge feature)
- Contagion model tests (advanced resilience)
- Kalman filter tests (signal processing)

---

## Appendix: Quick Reference

### Files by Unskip Priority

1. **Highest Priority:**
   - `tests/resilience/test_resilience_load.py` (1 test - fix + unskip)
   - `tests/services/test_fmit_scheduler_service.py` (14 tests - unskip)
   - `tests/services/test_call_assignment_service.py` (16 tests - unskip)
   - `tests/test_schedule_routes.py` (12 tests - unskip)

2. **Medium Priority:**
   - `tests/scheduling/periodicity/test_anti_churn.py` (2 tests - add fixtures)

3. **Keep Skipped (Conditional):**
   - `tests/unit/test_contagion_model.py` (30 tests - ndlib dependency)
   - `tests/services/test_rag_service.py` (9 tests - pgvector dependency)
   - `tests/scheduling/test_quantum_solver.py` (3 tests - quantum dependencies)
   - `tests/test_resilience_hub_analysis.py` (1 test - NetworkX dependency)
   - `tests/integration/test_orchestration_e2e.py` (1 test - MCP server)
   - `tests/integration/bridges/test_kalman_workload_bridge.py` (8 tests - not implemented)

### Skip Decorator Patterns in Codebase

```python
# Placeholder waiting for fixtures
@pytest.mark.skip(reason="DEBT-016: Placeholder - needs fixtures and assertions")
def test_something(self):
    pass

# Optional dependency
@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_something(simple_network):
    ...

# Feature not yet implemented
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
def test_something(self):
    ...

# Environment-specific (PostgreSQL)
@pytest.mark.skipif(True, reason="Requires PostgreSQL with pgvector extension")
async def test_something(self, db):
    ...
```

---

**Report Generated:** 2025-12-31
**Classification:** Development Intelligence
**Confidence:** High (parsed all skip decorators)
