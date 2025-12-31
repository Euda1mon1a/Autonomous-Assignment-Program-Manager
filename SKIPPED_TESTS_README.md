# Skipped Tests Intelligence Report - Index

**Mission:** G2_RECON - Analyze 96 skipped backend tests
**Date:** 2025-12-31
**Status:** Complete

---

## Quick Start

Start here for a quick overview:
1. **Read this file** (you are here)
2. **Review** `SKIPPED_TESTS_QUICK_REFERENCE.md` (1-page summary)
3. **Reference** `SKIPPED_TESTS_STATUS.txt` (executive summary)
4. **Dive deep** into `SKIPPED_TESTS_MANIFEST.md` (detailed analysis)
5. **Track** using `SKIPPED_TESTS_INVENTORY.csv` (spreadsheet format)

---

## The Report Files

| File | Purpose | Audience | Time |
|------|---------|----------|------|
| **SKIPPED_TESTS_QUICK_REFERENCE.md** | Quick lookup table, checklists, CI config | Developers | 5 min |
| **SKIPPED_TESTS_STATUS.txt** | Executive summary, risk assessment, roadmap | Leads/PMs | 10 min |
| **SKIPPED_TESTS_MANIFEST.md** | Comprehensive analysis with procedures | Developers | 30 min |
| **SKIPPED_TESTS_INVENTORY.csv** | Spreadsheet for tracking/project tools | PMs/Tools | N/A |
| **This file** | Navigation and context | Everyone | 5 min |

---

## Key Findings

### By The Numbers

```
Total Skip Decorators: 96
Files Affected: 11
Regression Risk: MODERATE-HIGH

HIGH PRIORITY (Need Action):
  42 tests - DEBT-016 placeholders (ready to unskip)
   1 test  - Known issue (fix + unskip)
   2 tests - Need fixtures (implement + unskip)
          = 45 tests UNBLOCKED

KEEP SKIPPED (Conditional):
  35 tests - Optional dependencies (ndlib, quantum, etc.)
   8 tests - Not yet implemented (Kalman filter)
   9 tests - Vector DB only (PostgreSQL)
   1 test  - MCP server optional
```

### Action Items (Priority Order)

| Priority | Action | Effort | Status |
|----------|--------|--------|--------|
| **P1** | Fix SQLAlchemy test isolation (1 test) | 3-5h | Blocked |
| **P2** | Unskip DEBT-016 (42 tests, 3 files) | 8-10h | Ready |
| **P3** | Implement anti-churn fixtures (2 tests) | 1-2h | Ready |
| **P4** | Implement Kalman filter (8 tests) | 4-6h | Defer |
| **P0** | Keep optional skips conditional | 0h | Ongoing |

### Why This Matters

**DEBT-016 tests:** Services are already implemented but tests are waiting for fixtures. This is a regression coverage gap.

**Test isolation issue:** Critical resilience test blocked - can't verify N-1/N-2 contingency at scale.

**Optional skips:** OK to keep skipped - these are for advanced features with optional dependencies.

---

## Which File Should I Read?

### I'm a Developer

**Start with:** `SKIPPED_TESTS_QUICK_REFERENCE.md`
- Has unskip checklists you can follow
- Quick reference table of all files
- CI configuration examples

**Then read:** Specific section in `SKIPPED_TESTS_MANIFEST.md`
- Detailed unskip procedures for each file
- Implementation guidance
- Example patterns from conftest.py

### I'm a Tech Lead / PM

**Start with:** `SKIPPED_TESTS_STATUS.txt`
- Executive summary
- Risk assessment
- Effort estimation
- Roadmap recommendations

**Then review:** `SKIPPED_TESTS_INVENTORY.csv`
- Import into Jira/Linear for tracking
- Assign to team members
- Monitor progress

### I'm QA / Tester

**Start with:** `SKIPPED_TESTS_QUICK_REFERENCE.md`
- Understand what tests are skipped and why
- CI configuration for running tests

**Then check:** `SKIPPED_TESTS_MANIFEST.md` Category 1
- Understand DEBT-016 placeholders
- These are the highest priority regression tests

---

## The 7 Categories

### 1. DEBT-016 Placeholders (HIGH PRIORITY)
**42 tests** - Services implemented, tests need fixtures
- Files: 3
  - `test_fmit_scheduler_service.py` (14 tests)
  - `test_call_assignment_service.py` (16 tests)
  - `test_schedule_routes.py` (12 tests)
- Status: READY TO UNSKIP
- Effort: 8-10 hours
- Risk: HIGH (no regression coverage for 3 core services)

**Action:** See unskip checklists in SKIPPED_TESTS_QUICK_REFERENCE.md

### 2. Missing Optional Dependencies (KEEP SKIPPED)
**35 tests** - Optional advanced features
- ndlib: 30 tests (burnout epidemiology)
- PyQUBO: 1 test (quantum optimization)
- dwave-samplers: 1 test (quantum annealing)
- NetworkX: 1 test (graph analysis)
- Status: KEEP SKIPPED - make conditional in CI
- Risk: LOW (optional features)

**Action:** Make `test:optional` CI target for these

### 3. Known Issues - Test Isolation (CRITICAL)
**1 test** - SQLAlchemy object lifecycle issue
- File: `test_resilience_load.py`
- Test: `test_concurrent_contingency_analyses`
- Status: BLOCKED on isolation fix
- Effort: 3-5 hours
- Risk: CRITICAL (blocks N-1/N-2 testing)

**Action:** Fix test isolation, then unskip

### 4. Not Yet Implemented (DEFER)
**8 tests** - Feature incomplete
- File: `test_kalman_workload_bridge.py`
- Feature: Kalman filter for workload estimation
- Status: Stub exists (raises NotImplementedError)
- Effort: 4-6 hours (when ready)
- Risk: MEDIUM

**Action:** Defer until feature implementation

### 5. Vector Database (KEEP SKIPPED)
**9 tests** - PostgreSQL with pgvector only
- File: `test_rag_service.py`
- Status: Requires PostgreSQL extension
- Risk: LOW (environment-specific)

**Action:** Run in Docker-based integration tests only

### 6. Misc Fixtures (IMPLEMENT + UNSKIP)
**2 tests** - Need mock Assignment objects
- File: `test_anti_churn.py`
- Status: Needs fixture implementation
- Effort: 1-2 hours
- Risk: MEDIUM

**Action:** Implement mocks, remove skip decorators

### 7. MCP Server Optional (KEEP SKIPPED)
**1 test** - Optional integration
- File: `test_orchestration_e2e.py`
- Status: Requires MCP server (docker-compose up mcp-server)
- Risk: LOW (optional)

**Action:** Run in E2E integration test suite only

---

## Unskip Strategy

### Phase 1 (Immediate - 1 sprint)
```
P1: Fix test isolation in test_resilience_load.py (1 test)
    └─ 3-5 hours
    └─ BLOCKS critical resilience testing
    
P2: Unskip DEBT-016 placeholders (42 tests, 3 files)
    ├─ test_fmit_scheduler_service.py (2-3h)
    ├─ test_call_assignment_service.py (2-3h)
    └─ test_schedule_routes.py (3-4h)
    └─ Can be parallelized (3 developers)
```

### Phase 2 (Medium-term - 2-3 weeks)
```
P3: Anti-churn fixtures (2 tests)
    └─ 1-2 hours
    
P4: Monitor Kalman filter implementation
    └─ 4-6 hours when feature is ready
```

### Phase 3 (Ongoing)
```
P0: Conditional CI for optional dependencies
    ├─ ndlib: test:optional target
    ├─ quantum: test:optional target
    ├─ pgvector: Docker integration tests
    └─ MCP: E2E integration tests
```

---

## Regression Risk Assessment

### HIGH RISK (Missing Coverage)
- FMITSchedulerService: No test coverage (service implemented)
- CallAssignmentService: No test coverage (service implemented)
- Schedule routes: No test coverage (API implemented)
- Concurrent N-1/N-2 analysis: Can't test at scale (isolation issue)

**Mitigation:** Unskip 42 DEBT-016 tests + fix 1 isolation issue

### MEDIUM RISK (Incomplete)
- Kalman filter: Feature not yet implemented (8 tests deferred)
- Anti-churn detection: Missing mock fixtures (2 tests deferred)

**Mitigation:** Implement fixtures for anti-churn, monitor Kalman

### LOW RISK (OK to Skip)
- Burnout contagion: Optional advanced feature (30 tests)
- Quantum solvers: Experimental research code (3 tests)
- Vector search: Production PostgreSQL only (9 tests)
- MCP integration: Optional integration (1 test)

**Mitigation:** Conditional CI, keep skipped normally

---

## Implementation Tips

### For DEBT-016 Unskip

**Checklist:**
```
[ ] Uncomment service import (if commented)
[ ] Create fixtures using conftest.py patterns
[ ] Replace pass statements with assertions
[ ] Remove @pytest.mark.skip decorators
[ ] Run tests locally: pytest tests/services/test_*.py -v
[ ] All green? Commit!
```

**Common Fixture Patterns:**
See examples in `SKIPPED_TESTS_MANIFEST.md` "Unskip Procedure"

### For Test Isolation Fix

**Common Issue:** SQLAlchemy objects detached from session in concurrent tests

**Solution:** 
1. Create isolated db sessions per async task
2. Use `AsyncSession` with proper context management
3. Ensure fixture scope is `function` (not `module`)

### For Optional Dependencies

**Python Install:**
```bash
pip install ndlib networkx scikit-learn  # For optional tests
```

**CI Config:**
```bash
pytest tests/unit/test_contagion_model.py  # Optional tests
```

---

## Related Documentation

- **CLAUDE.md** - Project guidelines (test requirements section)
- **tests/conftest.py** - Pytest fixtures and patterns
- **backend/tests/** - All test files with skip decorators
- **docs/development/TESTING.md** - Testing best practices

---

## Quick Links to File Locations

All skip decorators are in:
- `backend/tests/services/test_fmit_scheduler_service.py` (14)
- `backend/tests/services/test_call_assignment_service.py` (16)
- `backend/tests/test_schedule_routes.py` (12)
- `backend/tests/resilience/test_resilience_load.py` (1)
- `backend/tests/scheduling/periodicity/test_anti_churn.py` (2)
- `backend/tests/unit/test_contagion_model.py` (30)
- `backend/tests/services/test_rag_service.py` (9)
- `backend/tests/scheduling/test_quantum_solver.py` (3)
- `backend/tests/test_resilience_hub_analysis.py` (1)
- `backend/tests/integration/bridges/test_kalman_workload_bridge.py` (8)
- `backend/tests/integration/test_orchestration_e2e.py` (1)

---

## FAQ

**Q: Why are DEBT-016 tests skipped if the services are implemented?**
A: Fixture setup is tedious. Tests are stubs waiting for fixtures. The services are done; the tests just need setup.

**Q: Can I unskip the quantum solver tests?**
A: Yes, but only if you install PyQUBO and dwave-samplers. These are optional dependencies.

**Q: Should I unskip the ndlib tests?**
A: Keep them skipped by default. Make a conditional `test:optional` target that requires `pip install ndlib`.

**Q: What's the test isolation issue?**
A: SQLAlchemy objects are being shared between concurrent test threads, causing "detached from session" errors.

**Q: How long will it take to unskip everything?**
A: 12-17 hours if you prioritize P1-P3. P4 can wait until Kalman filter is implemented.

---

## Contact / Questions

If you have questions about specific skipped tests:
1. Check `SKIPPED_TESTS_QUICK_REFERENCE.md` for quick lookup
2. See `SKIPPED_TESTS_MANIFEST.md` for detailed analysis
3. Review `SKIPPED_TESTS_INVENTORY.csv` for test-by-test breakdown

---

**Report Generated:** 2025-12-31
**Classification:** Development Intelligence
**Mission:** G2_RECON Analysis Complete

Generated by G2_RECON Intelligence Probe
