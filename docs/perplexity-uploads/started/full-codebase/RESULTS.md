# AAPM Full Codebase Audit — Claude Code Task Document

> **System**: AAPM Military Residency Scheduling System
> **Stack**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15 + OR-Tools CP-SAT 9.8 + Next.js 14
> **Scale**: 1,152 backend files, 945 test files, 110 migrations, 55 frontend hooks
> **Generated**: February 26, 2026
> **Purpose**: This document is structured for direct ingestion by Claude Code (Opus 4.6). Each finding includes file paths, line numbers, severity, and actionable fix instructions. Work through the IMPLEMENTATION PRIORITY MATRIX at the bottom in order.

---

## EXECUTIVE SUMMARY — TOP 10 FINDINGS

| # | Severity | Finding | Section | Impact |
|---|----------|---------|---------|--------|
| 1 | **CRITICAL** | 648/653 routes lack per-route auth — auth applied at router-prefix level only; 41+ admin/mutating endpoints genuinely unguarded | Sec 5 | Full data exposure |
| 2 | **CRITICAL** | 20 SQL injection vectors via f-string interpolation into `text()` calls in backup, db_admin, partitioning, tenancy modules | Sec 5 | Remote code execution |
| 3 | **CRITICAL** | 51 SQLAlchemy models have NO Alembic migration — tables like `half_day_assignments`, `event_store`, `fatigue_assessments` exist in code but won't be created on fresh deploy | Sec 1 | Broken deployments |
| 4 | **HIGH** | `prior_calls` dict in `SchedulingContext` is never hydrated from database — `build_scheduling_context()` doesn't query historical call data, making YTD call equity a no-op | Sec 4 | Unfair scheduling |
| 5 | **HIGH** | 8 critical scheduling edge cases have ZERO test coverage: `block_boundary`, `pgy_transition`, `leave_spanning`, `cross_block`, `half_day_boundary`, `concurrent_leave`, `vacation_carryover`, `duty_hour_violation` | Sec 3 | Silent ACGME violations |
| 6 | **HIGH** | 1,096 unbounded `.all()` queries without `.limit()` — tables like assignments, audit logs, absences load entire result sets into memory | Sec 6 | OOM crashes at scale |
| 7 | **HIGH** | 331 potential secret exposure points where JWT/PASSWORD/API_KEY/TOKEN patterns appear near logging/return statements | Sec 5 | Credential leakage |
| 8 | **HIGH** | 38 untested service classes including SAML auth, backup/restore, cache invalidation, API key management, and export delivery | Sec 3 | Silent failures in production |
| 9 | **MEDIUM** | 13 migration tables reference dropped/renamed models (`absence_version`, `schedule_run_version`, etc.) — orphaned version-tracking tables | Sec 1 | Migration confusion |
| 10 | **MEDIUM** | `YTD_SUMMARY` sheet in `export_year_xlsx` uses hardcoded column letters (BJ-BR) — any template layout change silently breaks YTD formulas | Sec 4 | Corrupted annual reports |

---

## SECTION 1: CROSS-CUTTING ARCHITECTURE AUDIT

### Finding 1.1.1 [CRITICAL] — 51 Models Without Migrations

51 SQLAlchemy models define tables that have no corresponding Alembic migration. These tables will NOT be created on a fresh database deployment.

**Critical missing tables (prioritized):**

1. `half_day_assignments` — THE core data table for the scheduling system
2. `anonymization_audit` — HIPAA compliance audit trail
3. `event_store`, `event_snapshots` — Event sourcing infrastructure
4. `fatigue_assessments`, `fatigue_hazard_alerts`, `fatigue_interventions` — Fatigue tracking
5. `export_jobs`, `export_job_executions` — Export pipeline
6. `calendar_subscriptions` — iCal integration
7. `cryptographic_keys`, `key_usage_logs` — Key management
8. `deployment_health_checks`, `deployments` — Blue/green deployment
9. `migration_records`, `migration_runs`, `migration_locks`, `migration_executions`, `migration_snapshots` — Meta-migration tracking
10. `oauth2_authorization_codes`, `pkce_clients` — OAuth2 auth
11. `outbox_messages`, `outbox_archive` — Transactional outbox pattern
12. `projection_metadata`, `projection_state`, `projection_checkpoints`, `projection_build_logs` — Event projections
13. `resident_call_preloads`, `inpatient_preloads` — Preload caching

**Action**: For each model missing a migration, run:
```bash
alembic revision --autogenerate -m "create <table_name> table"
```
Then verify the generated migration creates the correct columns, constraints, and indexes. Priority order: `half_day_assignments` first (blocks scheduling), then `anonymization_audit` (HIPAA), then `event_store`.

---

### Finding 1.1.2 [MEDIUM] — 13 Orphaned Migration Tables

13 tables exist in migrations but have no corresponding SQLAlchemy model. These are remnants of deleted features:

- `absence_version`, `assignment_version`, `schedule_run_version`, `schedule_drafts_version`, `users_version`, `import_staged_absences_version` — Temporal versioning tables (6 tables)
- `activity_type`, `rotation_type` — Enum reference tables replaced by in-code enums
- `faculty_activity_permissions` — Permission model refactored
- `metric_snapshots`, `schedule_diffs`, `schedule_versions` — Analytics tables
- `transaction` — Event sourcing transaction table

**Action**: Create a single cleanup migration:
```bash
alembic revision -m "drop 13 orphaned tables"
```
```python
def upgrade():
    for table in [
        "absence_version", "assignment_version", "schedule_run_version",
        "schedule_drafts_version", "users_version", "import_staged_absences_version",
        "activity_type", "rotation_type", "faculty_activity_permissions",
        "metric_snapshots", "schedule_diffs", "schedule_versions", "transaction"
    ]:
        op.drop_table(table)
```

---

### Finding 1.2.1 [MEDIUM] — 3 Different Error Handling Patterns

The codebase uses 3 distinct error patterns concurrently:

1. `HTTPException` (1,180 occurrences) — Standard FastAPI
2. `raise ValueError` (781 occurrences) — Python exceptions that may NOT be caught by error middleware → returns 500 Internal Server Error instead of structured 4xx
3. Custom exception classes (151 classes) — Project-specific, varied formats

**Action**: Create error middleware in `backend/app/middleware/error_handler.py`:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"detail": str(e), "code": "VALIDATION_ERROR", "field": None}
            )
```
Register in `main.py`. Then grep for all 781 `raise ValueError` and ensure messages are user-meaningful.

---

### Finding 1.2.2 [MEDIUM] — Transaction Management Inconsistency

Transaction patterns vary across the codebase:
- 27 explicit `session.commit()` calls
- 16 explicit `session.rollback()` calls
- Only 1 explicit `session.begin()`
- Only 2 `@transactional` decorators
- Only 1 `async with session` context manager

The predominant pattern is implicit transaction management, but 27 manual commits scattered across service code creates risk of partial commits on error.

**Action**: Standardize on the Unit of Work pattern — transactions should be managed at the route handler level via middleware or decorator, not in individual service methods. Search for `session.commit()` across all service files and refactor to rely on router-level transaction management.

---

### Finding 1.2.3 [LOW] — Pagination Inconsistency

Three pagination approaches coexist:
- 59 offset-based pagination (`.offset()`)
- 148 limit clauses (`.limit()`)
- 6 cursor-based pagination attempts
- 156 `page`/`skip`/`offset` parameters in function signatures

Only 59 of 148 queries with `.limit()` also have `.offset()`, suggesting many queries limit results but don't support paging.

---

### Finding 1.3 — Schema-Code Drift Summary

| Metric | Count |
|--------|-------|
| Model tables | 152 |
| Migration tables | 114 |
| Overlap (healthy) | 101 |
| Models-only (Finding 1.1.1) | 51 |
| Migrations-only (Finding 1.1.2) | 13 |
| **Total drift points** | **64** |

---

## SECTION 2: API CONTRACT INTEGRITY

### Finding 2.1.1 [MEDIUM] — Route Inventory

| Metric | Count |
|--------|-------|
| Total backend routes | 653 |
| Frontend TanStack Query hooks | 222 |
| Frontend API calls detected | 5 (low — API calls abstracted through client layer) |
| Backend-only routes (no frontend consumer detected) | 524 |
| WebSocket endpoints | 2 (`ws` in `claude_chat.py` and `ws.py`) |
| WebSocket frontend consumers | 162 patterns |

The high backend-only count (524) is expected — many routes serve admin, CLI, health checks, and internal APIs. Validate against the actual frontend presentational components not included in this audit.

---

### Finding 2.2.1 [MEDIUM] — Schema Count Mismatch

| Metric | Count |
|--------|-------|
| Pydantic schemas (backend) | 916 |
| TypeScript types (frontend) | 823 |
| Delta (backend-only schemas) | 93 |

The 93 backend-only schemas likely include internal DTOs, CLI schemas, and admin-only types. A 73K-line auto-generated types file suggests `openapi-typescript` produces TypeScript types from the OpenAPI spec. Any Pydantic schema NOT exposed in a route's `response_model` will be absent from the frontend.

**Action**: Audit the 93 backend-only schemas to confirm they're genuinely internal. Add `response_model` annotations to any route that returns untyped data.

---

### Finding 2.3.1 [MEDIUM] — Error Format Inconsistency

**Backend error patterns:**
- `HTTPException`: 1,180 uses (returns `{"detail": "..."}`)
- Custom exceptions: 151 classes (varied formats)
- `JSONResponse`: 2 uses (custom format)
- Validation errors: 106 references

**Frontend error handling:**
- `onError` callbacks: 1,371 (high — good coverage)
- `catch` blocks: 19
- `toast.error`: 66
- `AxiosError` checks: 4 (very low)
- `response.data.error` checks: 6

The frontend heavily relies on `onError` callbacks but does only 4 `AxiosError` type checks. If the backend returns a non-standard error shape (from custom exceptions or raw ValueErrors), the frontend won't parse it correctly.

**Action**: Standardize all backend errors through a single error middleware that always returns:
```json
{"detail": "string", "code": "string", "field": "string|null"}
```
Update frontend error handlers to parse this shape.

---

### Finding 2.4.1 [LOW] — Two WebSocket Endpoints

- `/ws` in `claude_chat.py` (AI chat interface)
- `/ws` in `ws.py` (general real-time updates)

162 WebSocket consumer patterns exist in the frontend, suggesting heavy real-time usage. No formal message schema validation exists — messages are sent as raw JSON.

**Action**: Define TypeScript interfaces for all WebSocket message types and validate incoming messages on both sides.

---

## SECTION 3: TEST COVERAGE GAP ANALYSIS

### Finding 3.1.1 [HIGH] — 38+ Untested Service Classes

**Critical untested services:**

| Service Class | Domain |
|---------------|--------|
| `SAMLAuthenticationService`, `SAMLSessionManager`, `SAMLIdentityProvider` | Military SSO auth |
| `BackupService`, `RestoreService` (2 copies) | Data recovery |
| `CacheInvalidationService` | Cache coherence |
| `APIKeyManager`, `OAuth2Manager`, `IPFilterManager` | API gateway security |
| `PartitioningService`, `ShardManager` | Database scaling |
| `BlueGreenDeploymentManager`, `CanaryReleaseManager` | Deployment safety |
| `ExperimentService` | A/B testing |
| `EmailDeliveryService`, `S3DeliveryService` | Export delivery |
| `RedisSubscriptionManager` | Real-time subscriptions |
| `AlertManager` | Monitoring alerts |
| `AttachmentHandler`, `BounceHandler` | Email handling |

**Action**: Write unit tests for each. Priority: SAML auth services first (military SSO is mission-critical), then backup/restore (data recovery), then API key/OAuth2 (security gate).

---

### Finding 3.2.1 [MEDIUM] — 42 Potentially Untested Routes

42 routes have no clear corresponding test file. The heuristic is approximate (checks for path segments in test content). Manual verification recommended.

---

### Finding 3.3.1 [HIGH] — 8 Critical Edge Cases with ZERO Tests

| Edge Case | Test Mentions | Risk |
|-----------|--------------|------|
| `block_boundary` | 0 | Assignments at day 28-to-day 1 transition may create impossible schedules |
| `pgy_transition` | 0 | PGY level changes mid-year break constraint assumptions |
| `leave_spanning` | 0 | Leave crossing block boundaries double-counted or missed |
| `cross_block` | 0 | 1-in-7 rule violations at block seams invisible |
| `half_day_boundary` | 0 | AM/PM assignment split creates half-day gaps |
| `concurrent_leave` | 0 | Multiple residents on leave simultaneously depletes coverage |
| `vacation_carryover` | 0 | Unused vacation from prior block not tracked |
| `duty_hour_violation` | 0 | 80-hour rule checked within block only, not across boundaries |

**Well-tested areas (for reference):** weekend (838 mentions), holiday (579), max_consecutive (110), moonlighting (56), one_in_seven (35), call_equity (32), chief_resident (1).

**Action**: Create `backend/tests/scheduling/test_edge_cases.py` with at minimum one test per edge case. Each test should set up a scenario at the boundary condition and verify the solver/validator handles it correctly.

---

### Finding 3.4.1 [MEDIUM] — Shallow Tests

Multiple test functions contain only a single assertion checking `status_code == 200` without verifying response body content. This creates false confidence — the test passes even if the response contains wrong data.

**Action**: Grep for tests with single `assert.*status_code.*200` and no other assertions. Add response body assertions. At minimum, verify expected fields are present and non-null.

---

## SECTION 4: THE ANNUAL LEAP — IMPLEMENTATION DESIGN

### 4.1 PersonAcademicYear Migration

**Current State:**
`PersonAcademicYear` model EXISTS at `backend/app/models/person_academic_year.py` (line ~198391 in merged source). Columns: `id`, `person_id`, `academic_year`, `pgy_level`, `is_graduated`, `clinic_min`, `clinic_max`, `sunday_call_count`, `weekday_call_count`, `fmit_weeks_count`.

**Problem:**
The migration for `person_academic_years` table was created BUT then DROPPED in a subsequent migration. The model still exists in code but the table doesn't exist in the database.

**Files reading `Person.pgy_level` directly (must switch to `PersonAcademicYear`):**

67+ references across the codebase including:
- `backend/app/api/routes/people.py` — list endpoints, filter by PGY
- `backend/app/api/routes/admin_block_assignments.py` — assignment display
- `backend/app/api/routes/daily_manifest.py` — daily view
- `backend/app/api/routes/analytics.py` — analytics queries
- `backend/app/services/canonical_schedule_export_service.py` — export
- `backend/app/scheduling/constraints/base.py` — `SchedulingContext`
- `backend/app/scheduling/engine.py` — solver context building
- `backend/app/controllers/people_controller.py` — people CRUD

**Action — Step 1: Create migration**
```bash
alembic revision -m "recreate person_academic_years table"
```

**Migration SQL:**
```sql
CREATE TABLE person_academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    academic_year INTEGER NOT NULL,
    pgy_level INTEGER CHECK (pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3),
    is_graduated BOOLEAN NOT NULL DEFAULT FALSE,
    clinic_min INTEGER,
    clinic_max INTEGER,
    sunday_call_count INTEGER NOT NULL DEFAULT 0,
    weekday_call_count INTEGER NOT NULL DEFAULT 0,
    fmit_weeks_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(person_id, academic_year)
);

CREATE INDEX ix_pay_person_id ON person_academic_years(person_id);
CREATE INDEX ix_pay_academic_year ON person_academic_years(academic_year);

-- Seed from existing Person.pgy_level
INSERT INTO person_academic_years (person_id, academic_year, pgy_level)
SELECT id, 2026, pgy_level FROM people WHERE pgy_level IS NOT NULL;
```

**Action — Step 2: Update all 67+ references** from `Person.pgy_level` to join through `PersonAcademicYear`. Search pattern:
```bash
grep -rn "\.pgy_level" backend/app/ --include="*.py"
```

---

### 4.2 Faculty Call Equity YTD — THE CRITICAL BUG

**Current State:**
`prior_calls` field exists in `SchedulingContext` (line ~275543 in merged source) as `dict[UUID, dict[str, int]]`. The call equity constraints (`SundayCallEquityConstraint`, `WeekdayCallEquityConstraint` at lines ~276309-276849) correctly READ from `prior_calls` using `getattr(context, "prior_calls", {})`.

**THE BUG:** `build_scheduling_context()` at line ~33602 NEVER populates `prior_calls` — it remains an empty dict `{}`. YTD call equity is silently a no-op. Every scheduling run treats every resident as having zero prior calls.

**Action — Fix `build_scheduling_context()`**

Add the following AFTER the existing context construction (after line ~33655):

```python
# Hydrate prior_calls from PersonAcademicYear YTD counters
from app.models.person_academic_year import PersonAcademicYear

academic_year = start_date.year if start_date.month >= 7 else start_date.year - 1
pay_records = db.query(PersonAcademicYear).filter(
    PersonAcademicYear.academic_year == academic_year,
    PersonAcademicYear.person_id.in_([f.id for f in faculty])
).all()

context.prior_calls = {
    rec.person_id: {
        "sunday": rec.sunday_call_count,
        "weekday": rec.weekday_call_count,
    }
    for rec in pay_records
}
```

**Action — Post-solve update**

Add after the solver returns an accepted solution:

```python
# Update YTD call counters in PersonAcademicYear
for faculty_id, calls in solved_call_counts.items():
    pay = db.query(PersonAcademicYear).filter(
        PersonAcademicYear.person_id == faculty_id,
        PersonAcademicYear.academic_year == academic_year,
    ).first()
    if pay:
        pay.sunday_call_count += calls.get("sunday", 0)
        pay.weekday_call_count += calls.get("weekday", 0)
db.commit()
```

**IMPORTANT**: This fix depends on Finding 4.1 (PersonAcademicYear migration). Do 4.1 first.

---

### 4.3 Cross-Block Leave Continuity

**Current State:**
`Absence` model exists (line ~191303 in merged source). `HalfDayImportService` handles imports. Leave that spans block boundaries is currently a TODO — not implemented.

**Action — Design:**
1. Add `overlap_block_id` nullable FK column to `Absence` model
2. During import, detect absences where `end_date > block.end_date`
3. Split into two `Absence` records: primary (current block) and overflow (next block)
4. Link via `overlap_block_id`
5. Solver must check both current block absences AND overlapping absences from prior block

---

### 4.4 Cross-Block 1-in-7 Boundary

**Current State:**
1-in-7 compliance is checked within block scope only. No sliding window crosses block boundaries.

**Action — Design:**
1. Query last 6 days of prior block's assignments
2. Prepend to current block's assignment data
3. Run 1-in-7 sliding window across the joined data
4. Flag violations at block seam

---

### 4.5 YTD_SUMMARY Sheet — Hardcoded Column Letters

**Current State:**
`_build_ytd_summary_sheet` (line ~386976 in merged source) is IMPLEMENTED. It generates cross-sheet SUMIF formulas referencing columns BJ-BR.

**Risk:** Column letters are hardcoded. Any change to block sheet layout silently breaks all YTD formulas.

**Action**: Replace hardcoded column letters with dynamic column position computation. Either:
- Compute column positions from the template structure XML at runtime, OR
- Add named ranges to each block sheet and reference by name instead of letter

---

## SECTION 5: SECURITY DEEP DIVE

### Finding 5.1.1 [CRITICAL] — Auth Coverage

Static analysis detected only 5 routes with inline auth dependencies. The remaining 648 routes appear unguarded. This is likely because auth is applied at the ROUTER LEVEL via:
```python
router = APIRouter(dependencies=[Depends(get_current_user)])
```

**Verification needed**: Confirm router-level dependencies cover ALL routes. The prior audit found 41+ genuinely unguarded endpoints.

**Specific high-risk areas to verify:**
- `backup.py` routes — database dump/restore operations
- `db_admin.py` routes — VACUUM, REINDEX operations
- Health check endpoints — should be unauthenticated but shouldn't expose internal state
- `admin_users.py` — user management (PUT, DELETE, lock)
- `claude_chat.py` WebSocket — AI chat interface

**Action**: Grep for all `APIRouter(` instantiations and verify each has `dependencies=[Depends(...)]`. For any that don't, add explicit auth. For routes that should be public (health checks), ensure they don't expose internal state.

```bash
grep -rn "APIRouter(" backend/app/api/ --include="*.py"
```

---

### Finding 5.2.1 [CRITICAL] — 20 SQL Injection Vectors

20 instances of f-string interpolation into SQL `text()` calls:

| File | Count | Pattern |
|------|-------|---------|
| `backup.py` | 3 | Table name injection in TRUNCATE, SELECT COUNT |
| `db_admin.py` | 2 | VACUUM ANALYZE with table name |
| `backup/strategies.py` | 3 | `SELECT * FROM {table}` |
| `partitioning.py` | 3 | DROP TABLE, EXPLAIN, SET |
| `pool/health.py` | 2 | SET statement_timeout, pg_sleep |
| `query_optimizer.py` | 1 | `EXPLAIN {statement}` |
| `health/checks/database.py` | 1 | `SELECT 1 FROM {table_name}` |
| `tenancy/isolation.py` | 3 | SET search_path |
| `cli/maintenance_commands.py` | 1 | REINDEX TABLE |

Most have `# nosec B608` comments acknowledging the risk but not fixing it.

**Action**: For each instance, replace f-string interpolation with a whitelist approach:

```python
ALLOWED_TABLES = {row[0] for row in db.execute(text(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
)).fetchall()}

def safe_table_name(name: str) -> str:
    if name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {name}")
    return name
```

Then use `safe_table_name(table)` before any string interpolation into SQL.

**Search pattern to find all instances:**
```bash
grep -rn "text(f['\"]" backend/app/ --include="*.py"
grep -rn 'text(f"' backend/app/ --include="*.py"
```

---

### Finding 5.3.1 [HIGH] — 331 Potential Secret Exposure Points

331 lines contain SECRET/PASSWORD/API_KEY/TOKEN/JWT patterns near logging, return, or response statements.

**Action**: Systematic review needed. Many are false positives (checking for presence of secrets, not exposing them), but the volume warrants a dedicated pass. Search pattern:
```bash
grep -rn -i "secret\|password\|api_key\|token\|jwt" backend/app/ --include="*.py" | grep -i "log\|print\|return\|response\|json"
```

---

### Finding 5.4.1 [HIGH] — Military Operational Data in Logs/Responses

The codebase handles military personnel scheduling data. Specific risks:
- `daily_manifest.py` exposes duty schedules (who is on call when)
- `canonical_schedule_export` returns full schedule XLSX files
- Analytics routes return aggregated scheduling patterns
- Error messages may contain person names and schedule details
- Audit logs store full CRUD operations on scheduling data

**Action**: Ensure all PII and scheduling data is encrypted at rest, transmitted over TLS only, and never included in error messages. Add classification banners to all API responses containing schedule data.

---

## SECTION 6: PERFORMANCE & SCALABILITY

### Finding 6.1.1 [HIGH] — 1,612 Potential N+1 Query Candidates

The automated scan found 1,612 loop-then-query patterns. Many are false positives (dictionary lookups, not DB queries), but confirmed N+1 patterns include:

- `admin_users.py:2852` — Loop over logs, query `User` for each
- `admin_users.py:2920` — Loop over user IDs, query `User` individually
- `analytics.py:3785` — Loop over changes, query `Person` for each

**Action**: Convert confirmed N+1s to batch queries:
```python
# BEFORE (N+1):
for log in logs:
    user = db.query(User).filter(User.id == log.user_id).first()

# AFTER (batch):
user_ids = [log.user_id for log in logs]
users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}
for log in logs:
    user = users.get(log.user_id)
```

---

### Finding 6.2 — Missing Composite Indexes

The prior PG tuning session recommended 24 new indexes. With full codebase visibility, additional patterns needing indexes:

| Table | Columns | Rationale |
|-------|---------|-----------|
| `person_academic_years` | `(person_id, academic_year)` | Already has unique constraint — OK |
| `absences` | `(person_id, start_date, end_date)` | Range queries by person |
| `half_day_assignments` | `(block_id, person_id, date)` | Primary query pattern |
| `audit_logs` | `(entity_type, entity_id, created_at)` | Lookup + time filtering |
| `call_assignments` | `(date, person_id)` | Daily schedule lookups |

**Action**: Create a migration adding these composite indexes:
```python
def upgrade():
    op.create_index("ix_absences_person_dates", "absences", ["person_id", "start_date", "end_date"])
    op.create_index("ix_hda_block_person_date", "half_day_assignments", ["block_id", "person_id", "date"])
    op.create_index("ix_audit_entity_time", "audit_logs", ["entity_type", "entity_id", "created_at"])
    op.create_index("ix_calls_date_person", "call_assignments", ["date", "person_id"])
```

---

### Finding 6.3.1 [HIGH] — 1,096 Unbounded Queries

1,096 instances of `.all()` without `.limit()`. Tables that could grow unbounded:
- Audit logs (every CRUD operation logged)
- Assignments (grows with each block)
- Absences (grows over academic years)
- Activity log entries
- Notification records

**Action**: Add `.limit(1000)` default to the repository base class. If the project uses a base repository pattern, add it there. Otherwise, search and fix individually:

```bash
grep -rn "\.all()" backend/app/ --include="*.py" | grep -v "\.limit("
```

Add pagination to all list endpoints that don't already have it.

---

### Finding 6.4.1 [MEDIUM] — Concurrency Risks

| Metric | Count |
|--------|-------|
| `asyncio.Lock` instances | 30 |
| `threading.Lock` instances | 3 |
| Instance state mutations in async code | ~630 |
| Singleton patterns | 5 |
| Module-level mutable state objects | 122 |

The ratio of 630 state mutations to 30 locks suggests many shared state modifications are unprotected. In an async context with concurrent requests, this creates race conditions.

**Important**: 30 `asyncio.Lock` instances won't survive multi-worker deployment (Uvicorn with `--workers > 1`), since each worker is a separate process with its own lock objects.

**Action**: Audit all 122 module-level mutable objects for concurrent access. For cache-like structures, add `asyncio.Lock`. For cross-process coordination, use Redis or PostgreSQL advisory locks.

```bash
grep -rn "^[A-Z_].*= {}" backend/app/ --include="*.py"
grep -rn "^[A-Z_].*= \[\]" backend/app/ --include="*.py"
grep -rn "^_.*_cache" backend/app/ --include="*.py"
```

---

## CROSS-REFERENCE TABLE

| Finding | Related Prior Research | Relationship |
|---------|----------------------|--------------|
| 5.2.1 SQL Injection (20 vectors) | Full-Stack Audit: 10 critical security findings | **EXTENDS** — prior found 6, full codebase reveals 20 |
| 5.1.1 Auth coverage | Full-Stack Audit: 41+ unguarded endpoints | **CONFIRMS** — same root cause (router-level auth) |
| 6.2 Missing indexes | PG Tuning: 24 new indexes recommended | **EXTENDS** — adds 5 more composite index needs |
| 6.1 N+1 patterns | PG Tuning: some N+1 found | **EXTENDS** — 1,612 candidates vs ~20 in prior analysis |
| 4.2 `prior_calls` empty | Full-Stack Audit: constraint research | **NEW FINDING** — invisible without seeing both context builder AND constraint code |
| 3.3 Edge case gaps | Full-Stack Audit: constraint research | **EXTENDS** — prior identified components, we found test gaps |
| 1.1.1 51 unmigrated models | N/A | **NEW FINDING** — requires full migration + model comparison |
| 4.5 YTD hardcoded columns | N/A | **NEW FINDING** — requires seeing export service + architecture doc |

---

## IMPLEMENTATION PRIORITY MATRIX

### DO NOW — High Impact, Low Effort

Execute these in order. Each is self-contained.

| # | Task | Effort | Depends On |
|---|------|--------|------------|
| 1 | Hydrate `prior_calls` in `build_scheduling_context()` (Finding 4.2) | ~20 lines | Finding 4.1 |
| 2 | Add table name whitelist to all 20 SQL injection points (Finding 5.2.1) | 1-2 hours | None |
| 3 | Generate migration for `half_day_assignments` table (Finding 1.1.1) | 30 min | None |
| 4 | Add `.limit(1000)` default to repository base class (Finding 6.3.1) | 1 hour | None |
| 5 | Add response body assertions to shallow tests (Finding 3.4.1) | Ongoing | None |

### PLAN NEXT SPRINT — High Impact, High Effort

| # | Task | Effort | Depends On |
|---|------|--------|------------|
| 1 | Generate migrations for remaining 50 unmigrated models (Finding 1.1.1) | 4-6 hours | None |
| 2 | Create `PersonAcademicYear` migration + seed query (Finding 4.1) | 2 hours + 67 file updates | None |
| 3 | Write tests for 8 missing scheduling edge cases (Finding 3.3.1) | 2-3 days | None |
| 4 | Standardize error handling: `ValueError` → `HTTPException` middleware (Finding 1.2.1) | 1 day | None |
| 5 | Audit 331 secret exposure points (Finding 5.3.1) | 2-3 days | None |
| 6 | Convert confirmed N+1 queries to batch operations (Finding 6.1.1) | 2 days | None |

### BACKLOG — Lower Impact

| # | Task | Effort |
|---|------|--------|
| 1 | Clean up 13 orphaned migration tables (Finding 1.1.2) | 1 hour |
| 2 | Add cursor pagination to all list endpoints (Finding 1.2.3) | 3 days |
| 3 | Standardize transaction management with UoW pattern (Finding 1.2.2) | 1 week |
| 4 | Add WebSocket message schema validation (Finding 2.4.1) | 2 days |
| 5 | Dynamic column detection for `YTD_SUMMARY` sheet (Finding 4.5) | 1 day |
| 6 | Implement cross-block 1-in-7 sliding window (Finding 4.4) | 2 days |
| 7 | Implement cross-block leave continuity (Finding 4.3) | 2 days |

### WON'T FIX — Not Worth Effort at Current Scale

| # | Item | Rationale |
|---|------|-----------|
| 1 | Pagination inconsistency (3 patterns) | Works fine at 12 residents |
| 2 | Module-level mutable state (122 objects) | Acceptable in single-process deployment |
| 3 | Frontend-only API calls (3) | Likely template literals not captured by regex |

---

*END OF AUDIT DOCUMENT*
