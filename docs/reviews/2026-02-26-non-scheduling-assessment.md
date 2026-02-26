# AAPM Non-Scheduling Module Assessment

> **Date:** 2026-02-26
> **Scope:** All non-scheduling features across frontend and backend
> **Method:** Comprehensive codebase survey (frontend pages/hooks, backend routes/services/models)

---

## Summary

AAPM has significant non-scheduling capability that is either fully built but unwired, mock-first awaiting backend, or partially complete. This assessment catalogs everything outside the core scheduling engine and prioritizes by lift vs. yield.

---

## Tier 1: Wire Existing Code (Backend complete, needs route or migration)

### 1. Approval Chain — QUARANTINED

- **Route:** `backend/app/api/routes/approval_chain.py` (406 LOC, 8 endpoints)
- **Service:** `backend/app/services/approval_chain_service.py` (637 LOC, Merkle chain)
- **Model:** `backend/app/models/approval_record.py`
- **Schemas:** `backend/app/schemas/approval_chain.py` (Pydantic, camelCase aliases)
- **Tests:** 3 files (service, merkle, schemas)
- **Blocker:** `require_coordinator_or_above` RBAC dependency doesn't exist. Route uses `Depends(require_coordinator_or_above)` (not factory pattern) — needs careful implementation to match the non-factory call style vs. the existing `require_admin()` factory pattern.
- **Status:** Deferred — bigger lift than initially estimated due to RBAC pattern mismatch.

### 2. Pareto Optimization — WIRED (this session)

- **Service:** `backend/app/services/pareto_optimization_service.py` (725 LOC, NSGA-II via pymoo)
- **Schemas:** `backend/app/schemas/pareto.py` (complete Pydantic)
- **Tests:** 3 files
- **Route created:** `backend/app/api/routes/pareto.py` — POST `/pareto/optimize`, POST `/pareto/rank`
- **Registered in:** `backend/app/api/routes/__init__.py`

### 3. Agent Matcher — WIRED (this session)

- **Service:** `backend/app/services/agent_matcher.py` (346 LOC, semantic embeddings)
- **Tests:** 1 file
- **Route created:** `backend/app/api/routes/agent_matcher.py` — POST `/agent-matcher/match`, POST `/agent-matcher/explain`, GET `/agent-matcher/agents`
- **Registered in:** `backend/app/api/routes/__init__.py`

### 4. Fairness Audit — ALREADY WIRED

- **Route:** `backend/app/api/routes/fairness.py` (115 LOC, 3 endpoints)
- **Service:** `backend/app/services/fairness_audit_service.py` (369 LOC)
- **Status:** No action needed. Already registered at `__init__.py` line 228.

### 5. Workflow Engine — NOT WIRED

- **Service:** `backend/app/services/workflow_service.py`
- **Model:** `backend/app/models/workflow.py` + `state_machine.py`
- **Status:** Complete service + model, no route, no migration. Medium lift.

---

## Tier 2: Frontend Polish (Small fixes, big UX wins)

### 6. Export Tab — Returns Empty Array

- **Location:** `/hub/import-export` Export tab
- **Issue:** Export handler returns `[]`. Likely needs to call existing export service endpoint.
- **Lift:** ~30min

### 7. Scheduling Chart Placeholders

- **Location:** `/admin/scheduling`
- **Issue:** Two `<span>` placeholders where charts should render
- **Lift:** ~1hr to drop in lightweight chart components

### 8. Health Dashboard Mock Fallback

- **Location:** `/admin/health`
- **Issue:** Starts from `MOCK_HEALTH` then partially enriches from API
- **Lift:** ~1hr to wire remaining health endpoints

---

## Tier 3: Tech Debt & Cleanup

### 9. Duplicate N-1/N-2 Contingency Implementations

- **Issue:** 3 separate implementations of the same contingency logic
- **Recommendation:** Consolidate to one service, re-export from others
- **Lift:** ~2hr

### 10. Missing Alembic Migrations

- `backend/app/models/fatigue_risk.py` — 5 tables, no migration
- `backend/app/models/export_job.py` — 2 tables, no migration
- **Lift:** ~1hr (`alembic revision --autogenerate`)

### 11. Untested Route Modules

- 9 route modules with zero test coverage: `game_theory`, `proxy_coverage`, `impersonation`, `exotic_resilience`, `fatigue_risk`, `profiling`, `qubo_templates`, `scheduling_catalyst`, `unified_heatmap`
- **Lift:** ~3hr for basic smoke tests

---

## Tier 4: Mock→Real Graduation (Backend phase)

### 12. Audit Log

- **Frontend:** `/admin/audit` — fully hardcoded `MOCK_ENTRIES` / `MOCK_STATS`
- **Needs:** Backend model + route + frontend API calls
- **Lift:** ~3hr

### 13. PEC Backend

- **Frontend:** `/admin/pec` — mock-first UI complete, mutations throw "Not implemented"
- **Design doc:** `docs/design/PEC_OPERATIONS_DESIGN.md`
- **Needs:** Backend models/routes per existing design
- **Lift:** ~4hr

### 14. Board Review Backend

- **Frontend:** `/admin/board-review` — mock-first UI complete (built 2026-02-26)
- **Design doc:** `docs/design/BOARD_REVIEW_CURRICULUM_DESIGN.md`
- **Needs:** Backend models/routes per design doc
- **Lift:** ~4hr

---

## Sovereign Portal Notes

- `/sovereign-portal` solver/fairness panels use derived proxies, not real metrics
- Will improve automatically when fairness audit (already wired) and pareto (now wired) feed real data

---

## Actions Taken This Session

| Item | Action | Files |
|------|--------|-------|
| Pareto Optimization | Created route, registered | `backend/app/api/routes/pareto.py`, `__init__.py` |
| Agent Matcher | Created route, registered | `backend/app/api/routes/agent_matcher.py`, `__init__.py` |
| Approval Chain | Investigated, deferred (RBAC pattern mismatch) | No changes |
| Fairness Audit | Confirmed already wired | No changes |
| This document | Created | `docs/reviews/2026-02-26-non-scheduling-assessment.md` |
