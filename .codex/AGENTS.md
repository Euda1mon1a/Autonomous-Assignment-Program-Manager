# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## 🎯 ACTIVE TASK: Review Fairness GUI Frontend Code

**Priority:** Code review before merge
**Branch:** Check `main` (PR #692 merged) + this PR for useFairness.ts

**Files to review:**
1. `frontend/src/hooks/useFairness.ts` - NEW: React Query hooks (this PR)
2. `frontend/src/app/admin/fairness/page.tsx` - Admin fairness page (already in main)
3. `frontend/src/features/analytics/FacultyWorkloadTab.tsx` - Analytics tab (already in main)
4. `frontend/src/components/FacultyMatrixView.tsx` - Workload badges (already in main)

**Review focus:**
- React performance (memoization, unnecessary re-renders)
- Accessibility (ARIA, keyboard navigation)
- Edge cases (empty data, loading states, error handling)
- Type safety (proper TypeScript usage)
- API integration patterns (query keys, error handling)

---

## Project Context

**Residency Scheduler** - Military medical residency scheduling with ACGME compliance.

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **MCP Server**: 34+ AI tools for scheduling, validation, resilience

---

## Open Tasks

(none)

## Completed Tasks

### MCP Server Tests Failing in CI ✓

**Completed:** 2026-01-11
**Commit:** `c2e8ace8`

Mocked API client tests to avoid backend calls and added 401 refresh unit coverage.

### MCP API Client 401 Token Refresh (Tests) ✓

**Completed:** 2026-01-11
**Commit:** `c2e8ace8`

Added unit tests for token refresh, second-401 guard, and non-401 behavior.

### Seaborn Warning Cleanup ✓

**Completed:** 2026-01-11
**Commit:** `9200055e`

Removed unused seaborn import attempt from `spin_glass_visualizer.py`.
Warning no longer appears in container logs.

### MCP API Client 401 Token Refresh (Implementation) ✓

**Completed:** PR #608 (`e6c4440e`)

The 401 token refresh is implemented in `api_client.py` lines 113-121.
Tests added in `c2e8ace8`.

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection

---

## API Type Contract (CRITICAL)

### Naming Convention
- **Backend (Python):** snake_case everywhere
- **Frontend (TypeScript):** camelCase for interface properties
- **Axios interceptor converts automatically** (snake_case ↔ camelCase)

```typescript
// ✓ CORRECT - TypeScript interfaces use camelCase
interface Person {
  pgyLevel: number;
  createdAt: string;
  isActive: boolean;
}

// ✗ WRONG - will cause undefined at runtime
interface Person {
  pgy_level: number;  // Axios converts to pgyLevel, this won't match
}
```

### Enum Values Stay snake_case (Gorgon's Gaze)
Axios converts KEYS only, not VALUES. Database stores snake_case values.

```typescript
// ✓ CORRECT
type SwapType = 'one_to_one' | 'absorb';

// ✗ WRONG - will never match API responses
type SwapType = 'oneToOne' | 'absorb';
```

### URL Query Parameters Stay snake_case (Couatl Killer)
URL params go directly to API - interceptor doesn't convert them.

```typescript
// ✓ CORRECT
router.push(`/schedule?block_id=${id}&include_inactive=true`);

// ✗ WRONG
router.push(`/schedule?blockId=${id}&includeInactive=true`);
```

### Type Regeneration (STANDING ORDER)
After ANY backend schema change (`backend/app/schemas/*.py`):

```bash
cd frontend && npm run generate:types
git add frontend/src/types/api-generated.ts
```

Pre-commit hooks (`api-contract`, `modron-march`) will block if types drift.

---

## Full Guidelines

See `CLAUDE.md` in project root for complete project guidelines including:
- Architecture patterns
- Security requirements
- Testing requirements
- Git workflow
