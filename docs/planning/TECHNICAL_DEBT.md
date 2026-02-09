# Technical Debt Tracker

> **Last Updated:** 2026-02-08
> **Source:** Full-Stack MVP Review (16-layer inspection) + 2026-02-08 Repo-Wide Scan

This document tracks identified technical debt, prioritized by severity and impact.

---

## Priority Legend

| Priority | Meaning | Timeline |
|----------|---------|----------|
| P0 | Critical - Blocks launch | Must fix immediately |
| P1 | High - Affects functionality | Fix this week |
| P2 | Medium - Quality/maintainability | Fix within month |
| P3 | Low - Nice to have | Backlog |

---

## P0: Critical Issues

### DEBT-001: Celery Worker Missing Queues
**Location:** `docker-compose.yml` (celery-worker service)
**Category:** Infrastructure
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (2025-12-30, PR #546)

**Resolution:** Updated celery-worker command to listen to all 6 queues:
```yaml
command: celery -A app.core.celery_app worker -Q default,resilience,notifications,metrics,exports,security
```

---

### DEBT-002: Security TODOs in Audience Tokens
**Location:** `/backend/app/api/routes/audience_tokens.py`
**Category:** Security
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (2025-12-30, PR #546)

**Resolution:**
1. Implemented AUDIENCE_REQUIREMENTS dict with 5-level role hierarchy (0=viewer, 4=admin)
2. Added check_audience_permission() function with proper 403 responses
3. Token ownership verification now checks current_user.id == owner OR is_admin

---

## P1: High Priority Issues

### DEBT-003: Frontend Environment Variable Mismatch
**Location:** `/frontend/src/hooks/useClaudeChat.ts`
**Category:** Configuration
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (2025-12-30, PR #546)

**Resolution:** Changed to `process.env.NEXT_PUBLIC_API_URL`.

---

### DEBT-004: Missing Database Indexes
**Location:** Database schema / Alembic migrations
**Category:** Performance
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (migration `20251230_add_critical_indexes.py`)

---

### DEBT-005: Admin Users Page API Not Wired
**Location:** `/frontend/src/app/admin/users/page.tsx`
**Category:** Feature Incomplete
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (backend CRUD in `admin_users.py`, frontend hooks wired)

---

### DEBT-006: Resilience API Response Model Coverage
**Location:** `/backend/app/api/routes/resilience.py`
**Category:** API Quality
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (59/59 endpoints now have `response_model`)

---

### DEBT-007: Token Refresh Not Implemented in Frontend
**Location:** `/frontend/src/hooks/useAuth.ts`, `/frontend/src/lib/auth.ts`
**Category:** Authentication
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (`performRefresh()` in auth.ts, 401 interceptor in api.ts)

---

## P2: Medium Priority Issues

### DEBT-008: Frontend Accessibility Gaps
**Location:** Various frontend components
**Category:** Accessibility
**Found:** 2025-12-30

**Issues:**
- Only 24/80 core components have ARIA attributes (30%)
- `ScheduleGrid` missing `<thead>` and scoped headers
- Icon-only buttons missing `aria-label`
- Missing `aria-live` regions for dynamic updates

**Fix:** Audit all components, add ARIA attributes following WCAG 2.1 guidelines.

---

### DEBT-009: MCP Placeholder Tools
**Location:** `/mcp-server/src/scheduler_mcp/`
**Category:** Feature Incomplete
**Found:** 2025-12-30

**Placeholder tools (11 total):**
- Hopfield networks (4): energy, attractors, basin depth
- Immune system (3): response, memory cells, antibodies
- Value-at-Risk (3): coverage, workload, conditional VaR
- Shapley value (1): returns uniform distribution

**Impact:** AI analysis features return synthetic/mock data.

**Fix:** Implement backend services for actual calculations.

---

### DEBT-010: Frontend WebSocket Client Missing
**Location:** Frontend
**Category:** Real-time Features
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (`useWebSocket.ts` with reconnection, JWT auth, typed events)

---

### DEBT-011: N+1 Query Patterns in Scheduling Engine
**Location:** `/backend/app/scheduling/engine.py`
**Category:** Performance
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (engine uses `selectinload()` extensively, pre-fetch confirmed)

---

### DEBT-012: Hardcoded API URLs in Frontend
**Location:** Multiple frontend files
**Category:** Configuration
**Found:** 2025-12-30

**Locations:**
- `/frontend/src/mocks/handlers.ts` - Missing `/v1` suffix
- `/frontend/src/lib/export.ts` - Missing `/api/v1` suffix
- `/frontend/src/hooks/useClaudeChat.ts` - Wrong env var

**Fix:** Centralize API configuration, use consistent env vars.

---

### DEBT-013: Duplicate Cache TTL Definitions
**Location:** `/backend/app/core/config.py`
**Category:** Code Quality
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (duplicates removed, single definition remains)

---

### DEBT-014: localStorage Usage in Swap Marketplace
**Location:** `/frontend/src/features/swap-marketplace/hooks.ts`
**Category:** Architecture
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (uses AuthContext, no localStorage for user data)

---

## P3: Low Priority Issues

### DEBT-015: Test Calibration Failures (45 tests)
**Location:** Backend resilience tests
**Category:** Testing
**Found:** 2025-12-29 (Session 020)

**Categories:**
- Burnout fire index: 9 (CFFDRS threshold calibration)
- Circadian model: 6 (phase drift precision)
- Creep fatigue: 7 (Larson-Miller boundaries)
- Erlang C: 2 (wait probability precision)
- Other: 21

**Impact:** Tests fail due to numeric precision, not bugs.

**Fix:** Recalibrate thresholds with domain expertise.

---

### DEBT-016: Skipped Tests (147 total)
**Location:** Backend tests
**Category:** Testing
**Found:** 2025-12-30

**Key files:**
- `test_call_assignment_service.py`: 15 skipped
- `test_fmit_scheduler_service.py`: 13 skipped
- `test_schedule_routes.py`: 12 skipped

**Fix:** Implement tests or remove skip markers.

---

### DEBT-017: LLM Router Placeholder
**Location:** `docker-compose.ollama.yml`
**Category:** Feature Incomplete
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (2025-12-30)

**Description:** LLM Router service used `alpine:latest` with `tail -f /dev/null`.

**Resolution:** Commented out Docker service with detailed documentation explaining:
- LLMRouter is fully implemented as Python library in `backend/app/services/llm_router.py`
- In-process usage (current) is more efficient than separate service
- Provided clear instructions for future HTTP API exposure if needed
- Links to implementation, usage, and future work steps in inline comments

---

### DEBT-018: OpenTelemetry Not Enabled
**Location:** Backend configuration
**Category:** Observability
**Found:** 2025-12-30

**Issue:** `TELEMETRY_ENABLED=false` by default. Distributed tracing not available.

**Fix:** Enable and configure for production monitoring.

---

### DEBT-019: Logout Error Swallowed
**Location:** `/frontend/src/lib/auth.ts`
**Category:** Error Handling
**Found:** 2025-12-30

**Issue:** Logout errors caught but not propagated.

```typescript
export async function logout(): Promise<void> {
  try {
    await post('/auth/logout', {})
  } catch (error) {
    console.error('Logout error:', error)
    // Silent failure - session might still be active
  }
}
```

**Fix:** Propagate error or retry logout.

---

### DEBT-020: No Global Unhandled Rejection Handler
**Location:** Frontend
**Category:** Error Handling
**Found:** 2025-12-30
**Status:** ✅ RESOLVED (`providers.tsx` has `handleUnhandledRejection` with window listener)

---

### DEBT-021: Hardcoded Faculty Clinic Caps
**Location:** `backend/app/scheduling/constraints/faculty_clinic.py` (lines 34-54)
**Category:** Data / OPSEC
**Found:** 2026-02-08

**Issue:** `FACULTY_CLINIC_CAPS` dict hardcodes min/max clinic half-days for 13 faculty members by last name. A `_get_caps()` fallback reads DB columns (`min_clinic_halfdays_per_week`, `max_clinic_halfdays_per_week`) first, but the hardcoded dict remains as a backstop.

**Risks:**
- Faculty names in source code (OPSEC concern)
- Values drift from DB if DB is populated but dict is stale

**Fix:** Verify all faculty have DB-stored values, then remove the hardcoded dict. Requires: DB audit + constraint test validation.

---

### DEBT-022: Index-Based React Keys (30+ instances)
**Location:** Multiple frontend components
**Category:** Frontend Quality
**Found:** 2026-02-08

**Issue:** 30+ instances of `key={index}` across the frontend. Index-based keys cause incorrect DOM reuse when list items reorder, insert, or delete.

**Partial fix in PR #847:** Fixed `error-toast.tsx` (most user-visible). Remaining instances need per-component audit to determine stable key sources.

**Files with known instances:**
- Various page components, hooks, and utility components
- Full grep: `grep -rn 'key={index}' frontend/src/`

**Fix:** Audit each instance; replace with content hash, ID, or unique field. Static lists with no reorder can keep index keys (suppress with comment).

---

### DEBT-023: N+1 Queries in Scheduling Engine
**Location:** `backend/app/scheduling/engine.py`
**Category:** Performance
**Found:** 2025-12-30 (DEBT-011), re-confirmed 2026-02-08
**Status:** ✅ RESOLVED (engine confirmed using `selectinload()` throughout; DEBT-011 closed)

---

### DEBT-024: MAX_FACULTY_IN_CLINIC Hardcoded
**Location:** `backend/app/scheduling/engine.py` (line ~2431)
**Category:** Configuration
**Found:** 2026-02-08

**Issue:** `MAX_FACULTY_IN_CLINIC = 6` is hardcoded as a physical facility limit. Should be configurable per clinic/site for multi-site deployments.

**Fix:** Move to config or per-clinic DB field.

---

## Summary by Category

| Category | Open | Resolved | Total |
|----------|------|----------|-------|
| Security | 0 | 1 | 1 |
| Infrastructure | 0 | 1 | 1 |
| Configuration | 1 | 1 | 2 |
| Performance | 0 | 2 | 2 |
| Feature Incomplete | 1 | 3 | 4 |
| API Quality | 0 | 1 | 1 |
| Authentication | 0 | 1 | 1 |
| Accessibility | 1 | 0 | 1 |
| Architecture | 0 | 1 | 1 |
| Code Quality | 0 | 1 | 1 |
| Data / OPSEC | 1 | 0 | 1 |
| Frontend Quality | 1 | 0 | 1 |
| Testing | 2 | 0 | 2 |
| Error Handling | 1 | 1 | 2 |
| Observability | 1 | 0 | 1 |
| Real-time Features | 0 | 1 | 1 |
| **Total** | **9** | **14** | **24** |

> 14 of 24 items resolved (58%). Remaining 9 open items are medium-to-large effort.

---

## Resolution Tracking

| ID | Status | Resolved Date | PR/Commit |
|----|--------|---------------|-----------|
| DEBT-001 | ✅ Resolved | 2025-12-30 | PR #546 |
| DEBT-002 | ✅ Resolved | 2025-12-30 | PR #546 |
| DEBT-003 | ✅ Resolved | 2025-12-30 | PR #546 |
| DEBT-004 | ✅ Resolved | pre-2026 | Migration `20251230_add_critical_indexes` |
| DEBT-005 | ✅ Resolved | pre-2026 | `admin_users.py` + frontend hooks |
| DEBT-006 | ✅ Resolved | pre-2026 | 59/59 response_model coverage |
| DEBT-007 | ✅ Resolved | pre-2026 | `performRefresh()` + 401 interceptor |
| DEBT-008 | Open | - | - |
| DEBT-009 | Open | - | - |
| DEBT-010 | ✅ Resolved | pre-2026 | `useWebSocket.ts` |
| DEBT-011 | ✅ Resolved | pre-2026 | selectinload in engine |
| DEBT-012 | Open | - | - |
| DEBT-013 | ✅ Resolved | pre-2026 | Duplicates removed |
| DEBT-014 | ✅ Resolved | pre-2026 | AuthContext, no localStorage |
| DEBT-015 | Open | - | - |
| DEBT-016 | Open | - | - |
| DEBT-017 | ✅ Closed | 2025-12-30 | Local changes |
| DEBT-018 | Open | - | - |
| DEBT-019 | Open | - | - |
| DEBT-020 | ✅ Resolved | pre-2026 | `providers.tsx` unhandled rejection |
| DEBT-021 | Open | - | - |
| DEBT-022 | Partial | 2026-02-08 | PR #847 (error-toast only) |
| DEBT-023 | ✅ Resolved | 2026-02-08 | Confirmed DEBT-011 resolved |
| DEBT-024 | Open | - | - |

---

*This document should be updated as debt items are resolved or new items are discovered.*
