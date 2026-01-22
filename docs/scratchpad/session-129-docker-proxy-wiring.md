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

### HIGH: WS Enum Values Still snake_case → DOCUMENTED AS CONVENTION
**Original problem:** `snakeToCamel()` converts keys but not values.

**Resolution:** This is INTENTIONAL behavior. Enum values MUST stay snake_case because:
1. Database stores snake_case values (`swap_records.swap_type = 'one_to_one'`)
2. Changing would require database migration to update existing data
3. Tests expect snake_case values (50+ test files affected)

**Fix Applied:** Documented in `BEST_PRACTICES_AND_GOTCHAS.md` section 8 under "Enum Values Stay snake_case (Keys Convert, Values Don't)".

**Frontend types should use snake_case for enum values:**
```typescript
type SwapType = 'one_to_one' | 'absorb';  // ✅ CORRECT
type SwapType = 'oneToOne' | 'absorb';    // ❌ WRONG
```

### MEDIUM: DefenseLevel Mismatch → FIXED
**Original problem:** Backend returns `PREVENTION/CONTROL/SAFETY_SYSTEMS/CONTAINMENT/EMERGENCY`, UI expects `GREEN/YELLOW/ORANGE/RED/BLACK`.

**Fix Applied:** Added `mapBackendDefenseLevel()` function in `frontend/src/components/resilience/DefenseLevel.tsx`:
```typescript
export const mapBackendDefenseLevel = (backendLevel: BackendDefenseLevel | string | undefined): DefenseLevelType => {
  const mapping: Record<BackendDefenseLevel, DefenseLevelType> = {
    PREVENTION: 'GREEN',
    CONTROL: 'YELLOW',
    SAFETY_SYSTEMS: 'ORANGE',
    CONTAINMENT: 'RED',
    EMERGENCY: 'BLACK',
  };
  if (!backendLevel) return 'GREEN';
  return mapping[backendLevel as BackendDefenseLevel] || 'GREEN';
};
```

Updated `resilience-hub/page.tsx` to use the mapping function instead of type casting.

### LOW: Burnout Rt Hardcoded → DOCUMENTED AS PLACEHOLDER
**Original problem:** Dashboard shows `0.85` hardcoded instead of real data.

**Resolution:** The `/resilience/burnout/rt` API requires `burned_out_provider_ids` which must come from a burnout tracking system (not yet implemented). Added TODO comment and "Placeholder value" indicator in UI.

**Future work:** Implement burnout detection system to provide provider IDs.

### MEDIUM: BACKEND_INTERNAL_URL vs BACKEND_URL → FIXED IN SESSION 129
**Resolution:** Fixed in earlier session. Dockerfile now sets `BACKEND_URL=http://backend:8000` at build time.

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

## Session 130 Resolution

1. [x] WS enum values → DOCUMENTED as staying snake_case (intentional, database constraint)
2. [x] DefenseLevel mapping → ADDED `mapBackendDefenseLevel()` function
3. [x] Verify `docker-compose.local.yml` → WORKS (fixed in session 129)
4. [x] Burnout Rt → DOCUMENTED as placeholder, added UI indicator
5. [ ] Create PR after fixes ← READY

---

## Standardization Rules (Reference) - UPDATED

| Convention | Rule | Where |
|------------|------|-------|
| API response **keys** | snake_case → camelCase | axios interceptor |
| API response **enum values** | snake_case (NO conversion) | Database/model constraint |
| WS message **keys** | camelCase | Pydantic alias_generator |
| WS message **enum values** | snake_case (NO conversion) | Database/model constraint |
| URL query params | snake_case | Manual (no auto-convert) |
| TypeScript interface **keys** | camelCase | All frontend types |
| TypeScript **enum values** | snake_case | Match API responses |
| Docker proxy | `BACKEND_URL` env var | Dockerfile + next.config.js |
| DefenseLevel | Backend → Frontend mapping | `mapBackendDefenseLevel()` |

**Key Insight:** The axios/WS interceptors convert **keys** only, never values. Enum values in the database are snake_case and must stay snake_case throughout the stack.
