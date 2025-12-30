# Technical Debt Tracker

> **Last Updated:** 2025-12-30
> **Source:** Full-Stack MVP Review (16-layer inspection)

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

**Missing indexes:**
```sql
CREATE INDEX idx_block_date ON blocks(date);
CREATE INDEX idx_assignment_person_id ON assignments(person_id);
CREATE INDEX idx_assignment_block_id ON assignments(block_id);
CREATE INDEX idx_swap_source_faculty ON swap_records(source_faculty_id);
CREATE INDEX idx_swap_target_faculty ON swap_records(target_faculty_id);
```

**Impact:** Slow queries on schedule views, assignment lookups, and swap operations.

**Fix:** Create Alembic migration to add indexes.

---

### DEBT-005: Admin Users Page API Not Wired
**Location:** `/frontend/src/app/admin/users/page.tsx`
**Category:** Feature Incomplete
**Found:** 2025-12-30

**TODOs:**
- Line 662: `handleCreateUser` - API call not implemented
- Line 672: `handleDeleteUser` - API call not implemented
- Line 677: `handleToggleLock` - API call not implemented
- Line 682: `handleResendInvite` - API call not implemented

**Impact:** User management is non-functional (mock data only).

---

### DEBT-006: Resilience API Response Model Coverage
**Location:** `/backend/app/api/routes/resilience.py`
**Category:** API Quality
**Found:** 2025-12-30

**Issue:** Only 12/54 endpoints (22%) have `response_model` defined.

**Impact:** Poor OpenAPI documentation, inconsistent response formats.

**Fix:** Add Pydantic response models to all 54 endpoints.

---

### DEBT-007: Token Refresh Not Implemented in Frontend
**Location:** `/frontend/src/hooks/useAuth.ts`, `/frontend/src/lib/auth.ts`
**Category:** Authentication
**Found:** 2025-12-30

**Description:** Access tokens expire in 15 minutes. Backend supports refresh tokens, but frontend doesn't use them.

**Impact:** Users silently logged out after 15 minutes of inactivity.

**Fix:** Implement token refresh before expiry or on 401 response.

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

**Description:** Backend WebSocket fully implemented with 8 event types. Frontend only has SSE implementation (EventSource).

**Impact:** Real-time updates not leveraged on frontend.

**Fix:** Implement WebSocket client with reconnection logic.

---

### DEBT-011: N+1 Query Patterns in Scheduling Engine
**Location:** `/backend/app/scheduling/engine.py`
**Category:** Performance
**Found:** 2025-12-30

**Issues:**
```python
people = self.db.query(Person).all()  # No eager loading
# Later accesses: person.assignments -> N+1 per person
```

**Fix:** Use `selectinload()` or prefetch utilities from `/backend/app/db/optimization/`.

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

**Duplicates:**
- `CACHE_HEATMAP_TTL` defined at lines 82 and 122
- `CACHE_CALENDAR_TTL` defined at lines 83 and 123

**Fix:** Remove duplicate definitions.

---

### DEBT-014: localStorage Usage in Swap Marketplace
**Location:** `/frontend/src/features/swap-marketplace/hooks.ts`
**Category:** Architecture
**Found:** 2025-12-30

**Issue:** Reads user ID from `localStorage` instead of `AuthContext`.

```typescript
// Current (anti-pattern):
const userStr = localStorage.getItem('user');

// Should be:
const { user } = useAuth();
```

**Fix:** Use AuthContext for user data.

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

**Issue:** No `window.onunhandledrejection` handler to catch async errors outside React Query.

**Fix:** Add global handler in app layout.

---

## Summary by Category

| Category | P0 | P1 | P2 | P3 | Total |
|----------|----|----|----|----|-------|
| Security | 1 | 0 | 0 | 0 | 1 |
| Infrastructure | 1 | 0 | 0 | 0 | 1 |
| Configuration | 0 | 1 | 1 | 0 | 2 |
| Performance | 0 | 1 | 1 | 0 | 2 |
| Feature Incomplete | 0 | 2 | 2 | 1 | 5 |
| API Quality | 0 | 1 | 0 | 0 | 1 |
| Authentication | 0 | 1 | 0 | 0 | 1 |
| Accessibility | 0 | 0 | 1 | 0 | 1 |
| Architecture | 0 | 0 | 1 | 0 | 1 |
| Code Quality | 0 | 0 | 1 | 0 | 1 |
| Testing | 0 | 0 | 0 | 2 | 2 |
| Error Handling | 0 | 0 | 0 | 2 | 2 |
| Observability | 0 | 0 | 0 | 1 | 1 |
| **Total** | **2** | **6** | **7** | **6** | **21** |

---

## Resolution Tracking

| ID | Status | Resolved Date | PR/Commit |
|----|--------|---------------|-----------|
| DEBT-001 | Open | - | - |
| DEBT-002 | Open | - | - |
| DEBT-003 | Open | - | - |
| DEBT-004 | Open | - | - |
| DEBT-005 | Open | - | - |
| DEBT-006 | Open | - | - |
| DEBT-007 | Open | - | - |
| DEBT-008 | Open | - | - |
| DEBT-009 | Open | - | - |
| DEBT-010 | Open | - | - |
| DEBT-011 | Open | - | - |
| DEBT-012 | Open | - | - |
| DEBT-013 | Open | - | - |
| DEBT-014 | Open | - | - |
| DEBT-015 | Open | - | - |
| DEBT-016 | Open | - | - |
| DEBT-017 | ✅ Closed | 2025-12-30 | Local changes |
| DEBT-018 | Open | - | - |
| DEBT-019 | Open | - | - |
| DEBT-020 | Open | - | - |

---

*This document should be updated as debt items are resolved or new items are discovered.*
