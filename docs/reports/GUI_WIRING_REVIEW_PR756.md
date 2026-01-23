# GUI + Wiring Review — PR 756 Verification

> **Date:** 2026-01-20  
> **Scope:** Frontend ↔ backend wiring, GUI integration points, WebSocket paths, query param casing, and enum drift.  
> **Focus Files:** `frontend/src/hooks/useBlocks.ts`, `frontend/src/hooks/useResilience.ts`, `frontend/src/hooks/useClaudeChat.ts`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/api/resilience.ts`.

---

## Verified Fixes Landed (PR 756 / local commit `541a201`)

1) **Claude Chat transport**  
   - Replaced HTTP stream call with WebSocket integration.  
   - File: `frontend/src/hooks/useClaudeChat.ts`

2) **AuthContext dead‑hang prevention**  
   - Added 5s timeout for auth init to avoid infinite loading.  
   - File: `frontend/src/contexts/AuthContext.tsx`

3) **DefenseLevel null guard**  
   - Safe fallback for undefined `level` to prevent crash.  
   - File: `frontend/src/components/resilience/DefenseLevel.tsx`

4) **Resilience Overseer error state**  
   - Breakers error is now captured and displayed.  
   - File: `frontend/src/components/scheduling/ResilienceOverseerDashboard.tsx`

5) **Block range robustness**  
   - Snake_case fallback for block fields inside block range aggregation.  
   - File: `frontend/src/hooks/useBlocks.ts`

6) **Absence types (backend)**  
   - Added `TRAINING` and `MILITARY_DUTY` in backend schema/model.  
   - Files: `backend/app/schemas/absence.py`, `backend/app/models/absence.py`

---

## Remaining Wiring Gaps (Still Broken)

### A) Endpoint mismatches (UI will 404)

These endpoints are called by the frontend but do not exist in FastAPI:

- `POST /resilience/defense-level`  
  - Caller: `frontend/src/hooks/useResilience.ts`  
  - Backend: no matching route under `backend/app/api/routes/resilience.py`

- `POST /resilience/utilization-threshold`  
  - Caller: `frontend/src/hooks/useResilience.ts`  
  - Backend: no matching route under `backend/app/api/routes/resilience.py`

- `GET /resilience/circuit-breakers`  
  - Caller: `frontend/src/hooks/useResilience.ts`  
  - Backend: no matching route under `backend/app/api/routes/resilience.py`

- `GET /resilience/circuit-breakers/health`  
  - Caller: `frontend/src/hooks/useResilience.ts`  
  - Backend: no matching route under `backend/app/api/routes/resilience.py`

- `POST /resilience/unified-critical-index`  
  - Caller: `frontend/src/hooks/useResilience.ts`  
  - Backend: actual endpoint is **feature‑flagged** at  
    `/resilience/exotic/composite/unified-critical-index`

**Impact:** Resilience dashboards relying on these hooks will fail to load data.

---

### B) WebSocket URL construction still fragile

`useClaudeChat` builds the WS URL from `NEXT_PUBLIC_API_URL`:

- If `NEXT_PUBLIC_API_URL=/api/v1`, `new URL()` throws (relative URL).
- If `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`, WS becomes  
  `ws://localhost:8000/api/v1/api/v1/claude-chat/ws` (double path).

**Impact:** Claude chat fails in Docker dev (relative API) and in direct API mode.

---

### C) Query param casing drift (filters ignored)

These APIs expect `snake_case`, but the frontend sends `camelCase`:

- Blocks filter: `startDate`, `endDate`, `blockNumber`  
  - Caller: `frontend/src/hooks/useBlocks.ts`  
  - Backend expects: `start_date`, `end_date`, `block_number`

- Vulnerability filter: `startDate`, `endDate`  
  - Caller: `frontend/src/api/resilience.ts`  
  - Backend expects: `start_date`, `end_date`

- Absence filters: `startDate`, `endDate`, `absenceType`  
  - Caller: `frontend/src/hooks/useAbsences.ts`  
  - Backend expects: `start_date`, `end_date`, `absence_type`

**Impact:** UI appears to work but ignores filters, leading to incorrect lists.

---

### D) Absence enum drift (frontend vs backend)

Backend now supports `training` and `military_duty`, but frontend enum is missing these values and uses camelCase for some types:

- Frontend: `frontend/src/types/api.ts`  
  - Examples: `familyEmergency`, `emergencyLeave`, `maternityPaternity`
- Backend: `backend/app/schemas/absence.py`  
  - Uses snake_case: `family_emergency`, `emergency_leave`, `maternity_paternity`, plus `training`, `military_duty`

**Impact:** Creating or rendering these values may fail validation or mis‑serialize.

---

## Recommendations

1) **Resilience endpoints**
   - Decide if these hooks should target `/resilience/exotic/*` (feature‑flagged)  
     or if non‑exotic endpoints should be added under `/resilience/*`.

2) **Normalize query params**
   - Use snake_case in all query strings for FastAPI `Query(...)` parameters.

3) **Claude chat WS base**
   - Mirror `useWebSocket`’s base derivation (support relative `/api/v1` and strip duplicate path).

4) **Absence enum sync**
   - Align frontend enum values to backend snake_case and add new types.

---

## Validation Checklist

- Claude Chat opens with `NEXT_PUBLIC_API_URL=/api/v1` and with `http://localhost:8000/api/v1`
- Resilience dashboards load without 404s
- Block/absence filters actually change returned data (verify via devtools)
- Absence creation accepts `training` and `military_duty`

---

## Related Docs

- `docs/guides/FULL_STACK_WIRING_RECOVERY.md` (stack wiring reference)
