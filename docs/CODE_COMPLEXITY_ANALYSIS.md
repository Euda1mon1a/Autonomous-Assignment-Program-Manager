***REMOVED*** Code Complexity Analysis Report

This document provides an analysis of code complexity in the Residency Scheduler codebase, identifying areas that may benefit from refactoring.

***REMOVED******REMOVED*** Overview

| Metric | Backend (Python) | Frontend (TypeScript) |
|--------|------------------|----------------------|
| Total Files | ~220 | ~191 |
| Lines of Code | ~56,000 | ~6,000 |
| Test Files | 77 | Multiple (Jest + E2E) |
| Coverage Target | 70% | Variable |

---

***REMOVED******REMOVED*** Backend Complexity Analysis

***REMOVED******REMOVED******REMOVED*** High Complexity Files (Recommended for Refactoring)

These files have been identified as having high cyclomatic complexity and should be considered for decomposition:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. `backend/app/api/routes/resilience.py`
- **Status:** Listed in ROADMAP as high priority for refactoring
- **Issue:** Oversized route file with multiple responsibilities
- **Recommendation:** Split into focused modules:
  - `resilience_monitoring.py` - Health check and monitoring endpoints
  - `resilience_fallback.py` - Fallback schedule endpoints
  - `resilience_contingency.py` - Contingency planning endpoints

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. `backend/app/api/routes/constraints.py`
- **Status:** Listed in ROADMAP as high priority for refactoring
- **Issue:** Complex constraint handling logic mixed with route definitions
- **Recommendation:** Extract business logic to service layer:
  - Create `ConstraintValidationService`
  - Create `ConstraintRuleEngine`
  - Keep routes thin with minimal logic

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. `backend/app/scheduling/` Directory
- **Files:** Multiple scheduling-related modules
- **Issue:** Scheduling algorithm complexity
- **Recommendation:** Consider Strategy pattern for different scheduling algorithms

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. `backend/app/services/swap_executor.py`
- **Issue:** Multiple TODOs indicate incomplete implementation
- **Recommendation:** Complete TODOs before adding new features

***REMOVED******REMOVED******REMOVED*** Moderate Complexity Files

These files have moderate complexity but are manageable:

| File | Estimated Complexity | Notes |
|------|---------------------|-------|
| `backend/app/services/assignment_service.py` | Medium | Well-structured |
| `backend/app/services/audit_service.py` | Medium | Good separation |
| `backend/app/api/routes/assignments.py` | Medium | Could use pagination helper |
| `backend/app/core/security.py` | Medium | Security-critical, test thoroughly |

---

***REMOVED******REMOVED*** Frontend Complexity Analysis

***REMOVED******REMOVED******REMOVED*** Component Complexity

***REMOVED******REMOVED******REMOVED******REMOVED*** High Complexity Components

1. **`frontend/src/features/swap-marketplace/`**
   - Multiple hooks with similar patterns
   - **Recommendation:** Extract common logic into shared utilities

2. **`frontend/src/lib/hooks.ts`**
   - Listed in ROADMAP for splitting by domain
   - **Recommendation:** Create domain-specific hook files:
     - `hooks/useSchedule.ts`
     - `hooks/useAudit.ts`
     - `hooks/useSwap.ts`

***REMOVED******REMOVED******REMOVED******REMOVED*** Moderate Complexity Components

| Component | Complexity | Notes |
|-----------|-----------|-------|
| `src/components/schedule/` | Medium | Well-organized |
| `src/features/analytics/` | Medium | Good component structure |
| `src/features/audit/` | Medium | Comprehensive tests |

---

***REMOVED******REMOVED*** Cyclomatic Complexity Guidelines

***REMOVED******REMOVED******REMOVED*** Target Metrics

| Complexity Score | Risk Level | Action |
|-----------------|------------|--------|
| 1-10 | Low | Acceptable |
| 11-20 | Moderate | Consider simplification |
| 21-50 | High | Refactor recommended |
| 51+ | Very High | Refactor required |

***REMOVED******REMOVED******REMOVED*** How to Measure

**Backend (Python):**
```bash
***REMOVED*** Using radon
pip install radon
radon cc backend/app/ -a -s --total-average

***REMOVED*** Using xenon for thresholds
pip install xenon
xenon --max-average=B --max-modules=B --max-absolute=C backend/app/
```

**Frontend (TypeScript):**
```bash
***REMOVED*** Using complexity-report
npm install -g complexity-report
cr frontend/src/
```

---

***REMOVED******REMOVED*** Recommendations

***REMOVED******REMOVED******REMOVED*** Immediate Actions

1. **Refactor oversized route files** (resilience.py, constraints.py)
   - Extract business logic to service layer
   - Keep routes focused on HTTP concerns only
   - Target: < 300 lines per route file

2. **Split frontend hooks.ts**
   - Create domain-specific hook files
   - Improve code organization and discoverability
   - Target: < 200 lines per hook file

3. **Address swap service TODOs**
   - Complete pending implementations before adding features
   - Reduces technical debt accumulation

***REMOVED******REMOVED******REMOVED*** Long-term Goals

1. **Establish complexity budgets**
   - Add complexity checks to CI/CD
   - Fail builds exceeding thresholds

2. **Create refactoring playbook**
   - Document patterns for reducing complexity
   - Provide examples for common scenarios

3. **Regular complexity audits**
   - Monthly complexity reports
   - Track trends over time

---

***REMOVED******REMOVED*** Complexity Patterns Found

***REMOVED******REMOVED******REMOVED*** Good Patterns (Keep Using)

1. **Repository Pattern** - Clean data access separation
2. **Service Layer** - Business logic isolation
3. **Dependency Injection** - FastAPI dependencies
4. **React Query Hooks** - Consistent data fetching

***REMOVED******REMOVED******REMOVED*** Anti-patterns to Address

1. **Fat Controllers** - Route files with business logic
2. **God Functions** - Functions doing too many things
3. **Deep Nesting** - Multiple levels of conditionals
4. **Copy-Paste Code** - Duplicated logic across files

---

***REMOVED******REMOVED*** CI/CD Integration

Add to `.github/workflows/code-quality.yml`:

```yaml
- name: Check Cyclomatic Complexity
  run: |
    pip install radon xenon
    radon cc backend/app/ -a --json > complexity.json
    xenon --max-average=B --max-modules=B --max-absolute=C backend/app/
```

---

*Last updated: 2025-12-18*
*This analysis should be reviewed and updated quarterly.*
