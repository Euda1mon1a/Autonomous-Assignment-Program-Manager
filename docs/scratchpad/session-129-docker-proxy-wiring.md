# Session 129: Docker Proxy Fix + Wiring Standardization

**Date:** 2026-01-22
**Branch:** `feature/debugger-multi-inspector`
**Status:** Ready for follow-up fixes before PR merge

---

## What Was Fixed

### 1. Docker Proxy Routing (HTTP 500)
**Root cause:** `next.config.js` used `localhost:8000` inside Docker container, but `localhost` refers to the container itself.

**Fix:**
- `next.config.js`: Use `BACKEND_URL` env var with localhost default
- `Dockerfile`: Set `BACKEND_URL=http://backend:8000` at build time

### 2. Suspense Boundaries
**Root cause:** `/compliance` and `/my-schedule` use `useSearchParams()` without Suspense, breaking Next.js static generation.

**Fix:** Wrapped content in `<Suspense>` boundaries.

### 3. Documentation
Added to `BEST_PRACTICES_AND_GOTCHAS.md`:
- Docker networking (localhost vs service names)
- WebSocket conventions (camelCase keys)
- OpenAPI type contract (Hydra's Heads)
- URL query params (Couatl Killer - snake_case)
- SQLAlchemy boolean negation (Beholder Bane)
- Backup before destructive ops (Lich's Phylactery)

---

## Outstanding Issues (Codex Findings)

### HIGH: WS Enum Values Still snake_case
**Problem:** `snakeToCamel()` converts keys but not values.
- Backend sends: `"swapType": "one_to_one"`
- Frontend types expect: `"swapType": "oneToOne"`

**Files:**
- `frontend/src/hooks/useWebSocket.ts:85,111,124`
- `backend/app/websocket/events.py:88,109,122`

**Fix:** Change backend enum values to camelCase:
```python
class SwapType(str, Enum):
    ONE_TO_ONE = "oneToOne"  # NOT "one_to_one"
    ABSORB = "absorb"
```

### MEDIUM: DefenseLevel Mismatch
**Problem:** Backend returns `PREVENTION/CONTROL/MITIGATION/RECOVERY/SURVIVAL`, UI expects `GREEN/YELLOW/ORANGE/RED/BLACK`.

**Files:**
- `frontend/src/app/admin/resilience-hub/page.tsx:231`
- `backend/app/schemas/resilience.py:32`
- `frontend/src/components/resilience/DefenseLevel.tsx:11`

**Fix:** Create mapping function in frontend:
```typescript
const DEFENSE_LEVEL_MAP = {
  'PREVENTION': 'GREEN',
  'CONTROL': 'YELLOW',
  'MITIGATION': 'ORANGE',
  'RECOVERY': 'RED',
  'SURVIVAL': 'BLACK',
};
```

### LOW: Burnout Rt Hardcoded
**Problem:** Dashboard shows `0.85` hardcoded instead of real data.

**File:** `frontend/src/app/admin/resilience-hub/page.tsx:243`

**Fix:** Wire to actual resilience API data.

### MEDIUM: BACKEND_INTERNAL_URL vs BACKEND_URL
**Problem:** `docker-compose.local.yml` sets `BACKEND_INTERNAL_URL` but `next.config.js` reads `BACKEND_URL`.

**Verify:** Test that local Docker dev works with current setup (Dockerfile default should handle it).

---

## Commits on Branch (9 total)

```
32a1f75c fix(frontend): Docker proxy routing and Suspense boundaries
68a7748a docs: Add pre-commit hook failures to master priorities
be20b9ee fix(websocket): Automate snake_case to camelCase conversion
e4aa0657 fix(debugger): Address Codex review findings
b14a8ba9 fix(debugger): Hard-code /api/v1 to guarantee proxy+cookie behavior
08366702 feat(debugger): Extend Database Inspector with multi-data support
75b81d08 feat(activities): Wire FacultyWeeklyEditor into Faculty Activities tab
3424c659 docs: Add future enhancement for debugger multi-data support
b4e828ad fix(debugger): Use Next.js proxy instead of direct backend URL
```

---

## Next Session TODO

1. [ ] Fix WS enum values to camelCase in `backend/app/websocket/events.py`
2. [ ] Add DefenseLevel mapping in frontend
3. [ ] Verify `docker-compose.local.yml` proxy works
4. [ ] Wire Burnout Rt to real data (or mark as future)
5. [ ] Create PR after fixes

---

## Standardization Rules (Reference)

| Convention | Rule | Where |
|------------|------|-------|
| API response keys | snake_case → camelCase | axios interceptor |
| API response enum values | camelCase | Backend enum definitions |
| WS message keys | camelCase | Pydantic alias_generator |
| WS enum values | camelCase | Backend enum definitions |
| URL query params | snake_case | Manual (no auto-convert) |
| TypeScript interfaces | camelCase | All frontend types |
| Docker proxy | `BACKEND_URL` env var | Dockerfile + next.config.js |
