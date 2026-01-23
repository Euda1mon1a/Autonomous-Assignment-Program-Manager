# SEARCH_PARTY Intelligence Synthesis

> **Date:** 2025-12-31
> **Protocol:** 12 G-2 RECON agents x 10 probes = 120 parallel probes
> **Status:** Complete

---

## Executive Summary

120-probe reconnaissance complete across all codebase domains. Overall system health: **B+** with clear priorities for CCW next burn.

| Domain | Grade | Critical Issues |
|--------|-------|-----------------|
| Backend Core | C+ | Async violations, transaction leaks |
| Backend Models | B+ | UUID inconsistency, missing FK |
| Scheduling | B+ | Quantum solver crash, unused solvers |
| Resilience | B+ | Sync in async context, no tests |
| Frontend Core | C+ | 164 failing tests, mega-components |
| Frontend Hooks | A- | Minor type violations |
| Tests Backend | A- | Async fixture debt |
| Tests Frontend | C+ | Jest transform broken |
| MCP Server | A- | API client orphaned, placeholders |
| Docs | A | Well-organized |
| Infrastructure | A- | N8N password hardcoded |
| Security | B+ | OAuth2 auto_error concern |

---

## Cross-Domain Discrepancies (High-Signal Findings)

| G-2 | Finding | Discrepancy | Signal |
|-----|---------|-------------|--------|
| BACKEND-CORE vs MODELS | Routes sync, models async | Implementation drift | ACGME compliance at risk during concurrent swaps |
| SCHEDULING vs RESILIENCE | 7 constraints disabled | Missing enable logic | Schedule quality degradation possible |
| FRONTEND vs TESTS | Build passes (C+), tests fail (C+) | Jest transform broken | CI/CD blocked |
| MCP vs BACKEND | API client exists, unused | Orphaned infrastructure | Maintenance debt |
| SECURITY vs INFRASTRUCTURE | Strong auth, weak defaults | N8N password hardcoded | OPSEC risk |

---

## Top 10 Critical Issues for CCW

### BLOCKING (Must Fix First)

| # | Issue | Domain | Severity | File | Line |
|---|-------|--------|----------|------|------|
| 1 | **Jest transform broken** | Frontend Tests | BLOCKING | jest.config.js | babel-plugin-istanbul |
| 2 | **164 frontend tests failing** | Frontend Tests | BLOCKING | __tests__/* | systematic |
| 3 | **Async violations in routes** | Backend Core | CRITICAL | backend/app/api/routes/*.py | patterns |

### CRITICAL (High Impact)

| # | Issue | Domain | Severity | File | Line |
|---|-------|--------|----------|------|------|
| 4 | **Swap executor transaction leak** | Backend Core | CRITICAL | swap_executor.py | 78-92 |
| 5 | **Synchronous conflict resolver** | Backend Core | CRITICAL | conflict_auto_resolver.py | 68 |
| 6 | **Quantum solver fatal crash** | Scheduling | HIGH | qubo_solver.py | D-Wave |
| 7 | **Resilience tests = 0** | Resilience | HIGH | backend/app/resilience/ | all |
| 8 | **API client orphaned** | MCP | HIGH | api_client.py | unused |
| 9 | **OAuth2 auto_error=False** | Security | HIGH | security.py | 31 |
| 10 | **N8N password hardcoded** | Infrastructure | MEDIUM | docker-compose.yml | 248 |

---

## CCW Workstream Recommendations

### Stream 1: Frontend Test Infrastructure (BLOCKING)

**Estimated Tasks:** 50

**Files to Fix:**
- `frontend/jest.config.js` - babel-plugin-istanbul configuration
- `frontend/__tests__/setup.ts` - MSW v2 integration
- `frontend/package.json` - dependency versions

**Acceptance Criteria:**
```bash
cd frontend && npm test -- --passWithNoTests
# Should show 0 failing, X passing
```

### Stream 2: Backend Async Migration (CRITICAL)

**Estimated Tasks:** 100

**Files to Migrate:**
- All routes in `backend/app/api/routes/*.py` - change `def` to `async def`
- `backend/app/services/swap_executor.py` - add transaction boundaries
- `backend/app/services/conflict_auto_resolver.py` - add row locking

**Pattern:**
```python
# Before
def get_assignments(...):
    return db.query(Assignment).all()

# After
async def get_assignments(...):
    result = await db.execute(select(Assignment))
    return result.scalars().all()
```

**Acceptance Criteria:**
```bash
cd backend && pytest tests/test_routes_async.py
# All routes use async def
```

### Stream 3: Resilience Test Suite (CRITICAL)

**Estimated Tasks:** 80

**Create Tests For:**
- `backend/app/resilience/service.py` - ResilienceService
- `backend/app/resilience/unified_critical_index.py` - UnifiedCriticalIndex
- `backend/app/resilience/frms/*.py` - FRMS modules

**Test Template:**
```python
@pytest.mark.asyncio
async def test_resilience_service_health_check(db_session):
    service = ResilienceService(db_session)
    result = await service.check_health()
    assert result.defense_level in ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]
```

### Stream 4: MCP API Client Integration (HIGH)

**Estimated Tasks:** 40

**Refactor Pattern:**
```python
# Before (in server.py tools)
async def some_tool():
    # Direct logic or placeholder
    return {"status": "ok"}

# After
async def some_tool():
    client = SchedulerAPIClient()
    return await client.some_endpoint()
```

### Stream 5: Security Hardening (HIGH)

**Estimated Tasks:** 30

**Fixes:**
1. N8N password - remove default from docker-compose.yml
2. OAuth2 audit - verify all routes use `get_current_active_user`
3. Rate limit bypass - integration test

---

## LOCAL-Only Work (Cannot Delegate to CCW)

| Task | Why LOCAL | Command |
|------|-----------|---------|
| Run frontend build | Docker/npm access | `npm run build` |
| Run frontend tests | Docker/npm access | `npm test` |
| Run backend pytest | Docker/DB access | `pytest` |
| Validate MCP tools | Container access | `docker compose exec mcp-server ...` |
| API smoke tests | Live backend | `curl http://localhost:8000/health` |

---

## Health Grade Rollup

```
Overall: B+

BLOCKING ISSUES: 3
  - Jest transform broken
  - 164 frontend tests failing
  - Async route violations

CRITICAL ISSUES: 4
  - Swap executor transactions
  - Conflict resolver locking
  - Quantum solver crash
  - Resilience test coverage = 0

HIGH ISSUES: 4
  - API client orphaned
  - OAuth2 auto_error
  - N8N password
  - 7 constraints disabled

MEDIUM ISSUES: 8+
  - UUID inconsistency
  - Missing FK constraint
  - Mega-components (1700+ LOC)
  - Documentation redundancy
```

---

## Probe Agreement Matrix

| Probe | Backend | Frontend | MCP | Docs | Infra | Security |
|-------|---------|----------|-----|------|-------|----------|
| PERCEPTION | C | C+ | A | A | A | B+ |
| INVESTIGATION | C+ | B+ | A | A | A | A |
| ARCANA | B | B | A | A | A | A |
| HISTORY | B+ | B+ | A | A | A- | B+ |
| INSIGHT | C+ | B | A | A | A | A |
| RELIGION | C | A- | A | A | A | A |
| NATURE | C | C+ | A | A | A- | B+ |
| MEDICINE | C | C | A- | A | A- | B+ |
| SURVIVAL | D | A- | A | A | A | B+ |
| STEALTH | C | C | B+ | A | A- | B+ |

**Legend:**
- A: Excellent (no critical issues)
- B: Good (minor issues)
- C: Acceptable (needs attention)
- D: Poor (blocking issues)

---

## Next Steps

1. **CCW**: Execute 5 streams above (300+ tasks)
2. **LOCAL**: Run validation commands, report blockers
3. **Iterate**: CCW creates PRs, LOCAL validates
4. **Merge**: When acceptance criteria met

---

*Generated by SEARCH_PARTY protocol - 120 probes deployed*
*Synthesis time: 2025-12-31*
