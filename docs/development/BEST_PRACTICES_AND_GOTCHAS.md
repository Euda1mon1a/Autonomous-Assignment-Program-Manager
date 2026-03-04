# Best Practices & Gotchas

> **Purpose:** Prevent common bugs and headaches. Read this before starting work.
> **Last Updated:** 2026-03-02

---

## Table of Contents

1. [API Type Naming (snake_case vs camelCase)](#1-api-type-naming-snake_case-vs-camelcase)
2. [Docker Environment Differences](#2-docker-environment-differences)
3. [Database & Migrations](#3-database--migrations)
4. [Async Patterns (FastAPI/SQLAlchemy)](#4-async-patterns-fastapisqlalchemy)
5. [Testing Gotchas](#5-testing-gotchas)
6. [Git Workflow Recovery](#6-git-workflow-recovery)
7. [Configuration & Secrets](#7-configuration--secrets)
8. [Frontend-Backend Integration](#8-frontend-backend-integration)
9. [Common CLI Tool Locations](#9-common-cli-tool-locations)
10. [Debugging Flowcharts](#10-debugging-flowcharts)
11. [CP-SAT Activity Solver Architecture (Two Grids)](#11-cp-sat-activity-solver-architecture-two-grids)
12. [Antipatterns - Things NOT to Do](#12-antipatterns---things-not-to-do)
13. [CI/CD in the Vibecoding Age](#13-cicd-in-the-vibecoding-age)
14. [Block Schedule Import Workflow](#14-block-schedule-import-workflow)
15. [Constraint Archetype Enforcement (Mind Flayer's Probe)](#15-constraint-archetype-enforcement-mind-flayers-probe)

---

## 1. API Type Naming (snake_case vs camelCase)

### The Rule

| Layer | Convention | Example |
|-------|------------|---------|
| Backend (Python) | snake_case | `pgy_level`, `created_at` |
| Frontend (TypeScript) | camelCase | `pgyLevel`, `createdAt` |
| API Wire Format | snake_case | `{"pgy_level": 1}` |

### How It Works

The axios client in `frontend/src/lib/api.ts` automatically converts:
- **Response:** snake_case → camelCase (for frontend use)
- **Request:** camelCase → snake_case (for API)

### The Bug Pattern

```typescript
// ❌ WRONG - Will cause runtime undefined errors
interface Person {
  pgy_level: number;      // TypeScript thinks this exists
  created_at: string;
}

// At runtime:
const person = await api.get('/people/1');
console.log(person.pgy_level);  // undefined! Axios converted to pgyLevel
```

```typescript
// ✓ CORRECT
interface Person {
  pgyLevel: number;       // Matches what axios returns
  createdAt: string;
}

// At runtime:
const person = await api.get('/people/1');
console.log(person.pgyLevel);  // Works!
```

### Debugging Tips

1. **Check actual response:** Open Network tab, view Response - you'll see snake_case
2. **Check what code receives:** Add `console.log(response.data)` - you'll see camelCase
3. **TypeScript won't catch this:** Types are erased at runtime

### Prevention

- Always use camelCase in TypeScript interfaces
- When adding new API fields, add them as camelCase in frontend types
- Mock data in tests should use camelCase (matches post-axios transformation)

### URL Query Parameters (Couatl Killer)

**Exception to the rule:** URL query params MUST use snake_case, even in frontend code.

```typescript
// ✅ CORRECT - backend expects snake_case
const params = new URLSearchParams({ block_id: '123', include_inactive: 'true' });
router.push(`/schedule?person_id=${id}`);

// ❌ WRONG - backend won't recognize these
const params = new URLSearchParams({ blockId: '123', includeInactive: 'true' });
router.push(`/schedule?personId=${id}`);
```

**Why:** Query params go directly to the API. The axios interceptor only converts request/response **bodies**, not URL parameters.

### SQLAlchemy Boolean Negation (Beholder Bane)

**Use `~column` not `not column`** for SQLAlchemy boolean filters:

```python
# ✅ CORRECT - SQLAlchemy __invert__ generates SQL NOT
query.filter(~Person.is_active)
query.filter(Person.is_deleted == False)  # noqa: E712

# ❌ WRONG - Python bool, returns True/False, not SQL expression
query.filter(not Person.is_active)  # Always True or False!
```

**Why:** `not` is Python's boolean operator and returns `True`/`False`. `~` invokes SQLAlchemy's `__invert__` to generate proper SQL `NOT` clause.

---

## 2. Docker Environment Differences

### Tool Availability

| Tool | Host Machine | Docker Container | How to Run from Host |
|------|--------------|------------------|---------------------|
| ruff | `brew install ruff` | Pre-installed | `ruff check backend/` |
| pytest | Needs venv | Pre-installed | `docker exec scheduler-local-backend pytest` |
| alembic | Needs venv | Pre-installed | `docker exec scheduler-local-backend alembic upgrade head` |
| npm | Pre-installed | Pre-installed | `cd frontend && npm run ...` |
| python | System python | Python 3.11 | Use Docker for consistency |

### Volume Mounts & Hot Reload

In `docker-compose.local.yml`:
- `./backend:/app` - Code changes reflected immediately (with `--reload`)
- `./frontend:/app` - Next.js hot reload works
- **Exception:** `node_modules` is NOT mounted (uses container's copy)

### "Works Locally, Fails in Docker" Checklist

1. **Different Python version?** Host might be 3.9, container is 3.11
2. **Missing dependency?** Check if it's in requirements.txt/package.json
3. **Environment variable missing?** Check docker-compose.local.yml
4. **File not synced?** Volume mount might be stale - run `docker compose restart`
5. **Port conflict?** Another service using the same port

### Container Debugging Commands

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View logs
docker logs scheduler-local-backend --tail 50

# Execute command in container
docker exec scheduler-local-backend python -c "import app; print('OK')"

# Check if file exists in container
docker exec scheduler-local-backend ls -la /app/path/to/file

# Rebuild specific service
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build backend
```

### Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js dev server |
| Backend | 8000 | FastAPI |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Cache/Celery broker |
| MCP | 8081 | AI tools (not 8080 to avoid Claude Code conflict) |

### Docker Networking: localhost vs Service Names

**The Problem:** Inside a Docker container, `localhost` refers to the container itself, NOT the host machine or other containers.

```
❌ WRONG (from inside frontend container):
   fetch('http://localhost:8000/api/...')
   → Tries to connect to frontend container's port 8000
   → Connection refused!

✅ CORRECT (from inside frontend container):
   fetch('http://backend:8000/api/...')
   → Docker DNS resolves 'backend' to the backend container
   → Works!
```

**Where This Bites You:**

| Scenario | Host Machine | Inside Container |
|----------|--------------|------------------|
| Browser → Backend | `localhost:8000` ✅ | N/A |
| Frontend SSR → Backend | N/A | `backend:8000` ✅ |
| Next.js Rewrites | `localhost:8000` ✅ (local dev) | `backend:8000` ✅ (Docker) |

**The Fix Pattern (next.config.js):**

```javascript
// Use env var with sensible default
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

// Then in rewrites:
{ source: '/api/:path*', destination: `${backendUrl}/api/:path*` }
```

**In Dockerfile (set at build time):**
```dockerfile
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
```

**Symptoms of This Bug:**
- `ECONNREFUSED 127.0.0.1:8000` in frontend container logs
- API calls work in browser but fail in SSR/rewrites
- "Works on my machine" but fails in Docker

**Quick Diagnosis:**
```bash
# Check what URL the frontend is using
docker compose logs frontend | grep -i "backend\|rewrite"

# Test connectivity from inside container
docker exec residency-scheduler-frontend wget -qO- http://backend:8000/api/v1/health
```

### Data Persistence: Bind Mounts vs Named Volumes

**Current Setup (Local Dev):** Bind mounts for postgres/redis
**Why:** Data visible on host, survives Docker resets, easy backup

| Volume Type | Where Data Lives | Survives `docker system prune`? | Easy to Inspect? |
|-------------|------------------|--------------------------------|------------------|
| Named Volume | `/var/lib/docker/volumes/` | ❌ No | ❌ Hidden |
| Bind Mount | `./data/postgres/`, `./data/redis/` | ✅ Yes | ✅ Visible |

**The Problem with Named Volumes:**
- Data hidden in Docker's internal storage
- `docker system prune -a --volumes` deletes everything
- Docker Desktop updates/resets can wipe data
- Can't easily verify data exists without running containers
- **Hours lost to "where did my data go?" debugging**

**Current Config (docker-compose.local.yml):**
```yaml
# Bind mounts - data on host filesystem
db:
  volumes:
    - ./data/postgres:/var/lib/postgresql/data
redis:
  volumes:
    - ./data/redis:/data
```

**Quick Verification:**
```bash
# Check data exists
ls -la data/postgres/   # Should see PG_VERSION, base/, etc.
ls -la data/redis/      # Should see dump.rdb, appendonlydir/

# Check database size
du -sh data/postgres/   # ~80MB typical
```

> **Multi-user/Production:** See [LOCAL_DEVELOPMENT_RECOVERY.md](LOCAL_DEVELOPMENT_RECOVERY.md#volume-strategy--multi-user-transition) for transitioning back to named volumes.

---

## 3. Database & Migrations

### Backup Before Destructive Operations (Lich's Phylactery)

**MUST create backup before:**
- Schedule generation (bulk writes)
- Swap execution (multi-table updates)
- Migration rollbacks
- Any `DELETE` or `TRUNCATE` operations

**MCP backup tools:**
```bash
# Before destructive operation
mcp__residency-scheduler__create_backup_tool(reason="Pre-generation backup")

# Verify backup exists
mcp__residency-scheduler__get_backup_status_tool()

# If something goes wrong
mcp__residency-scheduler__restore_backup_tool(backup_id="...")
```

**Skill shortcut:** Use `/safe-schedule-generation` which enforces backup-first workflow.

### Migration Naming Convention

**CRITICAL:** Migration names must be ≤64 characters.

```bash
# ✓ Good
20260109_add_person_pgy

# ❌ Bad (too long)
20260109_add_person_pgy_level_field_for_resident_tracking_purposes
```

### Common Migration Commands

```bash
# Create new migration
docker exec scheduler-local-backend alembic revision --autogenerate -m "20260109_short_name"

# Apply migrations
docker exec scheduler-local-backend alembic upgrade head

# Rollback one
docker exec scheduler-local-backend alembic downgrade -1

# Check current version
docker exec scheduler-local-backend alembic current
```

### Schema Sync Issues

If you see "column does not exist" errors:

1. **Check migration applied:** `alembic current`
2. **Check migration files exist:** `ls backend/alembic/versions/`
3. **Force re-apply:** `alembic stamp head && alembic upgrade head`

### SQLAlchemy 2.0 Patterns

```python
# ✓ Correct async query
async def get_person(db: AsyncSession, person_id: UUID) -> Person | None:
    result = await db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one_or_none()

# ❌ Wrong - sync operation in async context
def get_person(db: Session, person_id: UUID) -> Person | None:  # Don't use sync Session
    return db.query(Person).filter(Person.id == person_id).first()
```

---

## 4. Async Patterns (FastAPI/SQLAlchemy)

### Golden Rule

**All API layer database operations MUST be async.**

**Exception:** The scheduling engine (`engine.py`, `activity_solver.py`) intentionally uses sync sessions because:
1. Scheduler is **CPU-bound** (solving math), not I/O-bound (waiting for data)
2. Runs in **background tasks**, not blocking the API event loop
3. Async overhead provides **no benefit** for compute-intensive work

**Medical analogy:** API = ED attending (multitask, never wait). Scheduler = Surgeon (one procedure at a time, blocking is expected).

> **Reference:** [SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md](SOFTWARE_CONCEPTS_MEDICAL_ANALOGIES.md)

### Common Mistakes

```python
# ❌ Missing await
async def get_items(db: AsyncSession):
    result = db.execute(select(Item))  # Missing await!
    return result.scalars().all()

# ✓ Correct
async def get_items(db: AsyncSession):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

```python
# ❌ Sync function called from async context
def sync_helper(db: Session):  # This blocks the event loop!
    return db.query(Item).all()

# ✓ Make it async
async def async_helper(db: AsyncSession):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### Transaction Handling

```python
# ✓ Automatic transaction (recommended)
async def create_item(db: AsyncSession, item: ItemCreate):
    db_item = Item(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

# ✓ Explicit transaction for multiple operations
async def transfer_items(db: AsyncSession, from_id: UUID, to_id: UUID):
    async with db.begin():
        # All operations in this block are one transaction
        await db.execute(update(Item).where(...))
        await db.execute(update(Item).where(...))
    # Commits automatically, rolls back on exception
```

---

## 5. Testing Gotchas

### Mock Data Must Match Runtime Format

```typescript
// ❌ Wrong - mock uses snake_case but axios converts to camelCase
const mockPerson = {
  pgy_level: 2,        // Frontend code won't find this
  created_at: '2025-01-01'
};

// ✓ Correct - mock uses camelCase (what code actually receives)
const mockPerson = {
  pgyLevel: 2,
  createdAt: '2025-01-01'
};
```

### pytest-asyncio Requirements

```python
# ✓ Always use this decorator for async tests
@pytest.mark.asyncio
async def test_create_person(db: AsyncSession):
    person = await create_person(db, PersonCreate(name="Test"))
    assert person.id is not None
```

### Test Database Isolation

- Tests use a separate test database
- Each test gets a fresh transaction that's rolled back
- Don't rely on data from previous tests

### FastAPI TestClient: Query Params Stripped on Non-Versioned Routes

**Symptom:** Tests hitting `/api/admin/schedule-overrides?start_date=...` return 400 (missing required params), but identical tests hitting `/api/v1/admin/schedule-overrides?start_date=...` work fine.

**Root Cause:** FastAPI TestClient has undocumented behavior where query parameters are silently stripped when hitting unversioned `/api/*` routes. This appears to be related to how TestClient handles routing fallbacks.

**The Fix:** Always use versioned routes (`/api/v1/*`) in tests.

```python
# ❌ WRONG - query params silently dropped
response = client.get("/api/admin/schedule-overrides?start_date=2025-01-01")
# Status 400: required query param 'start_date' not provided

# ✅ CORRECT - versioned route preserves query params
response = client.get("/api/v1/admin/schedule-overrides?start_date=2025-01-01")
# Status 200: works as expected
```

**Action Item:** Audit all existing tests for this pattern and convert any non-versioned routes to `/api/v1/*`.

### Pure-Logic Test Isolation (No DB, No Redis)

Many backend modules contain pure logic (dataclasses, enums, validators, math, state machines) that can be tested without any infrastructure. This is the fastest and most reliable testing pattern.

**Command:**
```bash
cd backend && SECRET_KEY=$(python3.11 -c "import secrets; print(secrets.token_urlsafe(32))") \
  DATABASE_URL="postgresql://user:pass@localhost:5432/testdb" \
  python -m pytest tests/path/test_file.py -v --no-header --tb=short --noconftest
```

**Key flags:**
- `--noconftest` skips all conftest.py fixtures (DB sessions, Redis, etc.)
- Fake `SECRET_KEY` and `DATABASE_URL` satisfy import-time config validation
- Tests run in <1 second for most modules

**When to use:** Any module that doesn't call `db.execute()`, `redis.get()`, or make HTTP requests. Good candidates: schemas, validators, constraint logic, data transformations, enums, utility functions.

**Async helper pattern:**
```python
import asyncio

def _run(coro):
    """Run an async coroutine synchronously for pure-logic tests."""
    return asyncio.get_event_loop().run_until_complete(coro)

# Usage
def test_query_bus_execute():
    result = _run(bus.execute(query))
    assert result.success is True
```

**Ruff gotchas to watch for:**
- `E731`: Don't use `fn = lambda x: x` -- convert to `def fn(x): return x`
- `SIM300`: Don't use Yoda conditions like `"POST" == method` -- reverse to `method == "POST"`

### Integration vs Unit Tests

| Test Type | Uses Real DB | Uses Real API | Speed |
|-----------|--------------|---------------|-------|
| Unit | No (mocked) | No | Fast |
| Pure-Logic | No (--noconftest) | No | Very Fast |
| Integration | Yes | No | Medium |
| E2E | Yes | Yes | Slow |

### Scheduling Edge Cases with Zero Test Coverage (Audit Finding 3.3.1, Feb 2026)

The full-codebase audit identified 8 scheduling edge case categories with **zero** test mentions. These are known coverage gaps:

| Edge Case | Risk | Test Approach |
|-----------|------|---------------|
| `block_boundary` | Day 28→Day 1 transition creates impossible schedules | Set up assignment at block end, verify solver handles next block start |
| `pgy_transition` | PGY level changes mid-year break constraint assumptions | Simulate July 1 PGY advance, verify constraints use correct level |
| `leave_spanning` | Leave crossing block boundaries double-counted or missed | Create absence spanning two blocks, verify single date range |
| `cross_block` | 1-in-7 violations at block seams invisible | Create 6-day run ending Block N, verify Block N+1 flags it |
| `half_day_boundary` | AM/PM assignment split creates half-day gaps | Test AM-only and PM-only assignments at block transitions |
| `concurrent_leave` | Multiple residents on leave depletes coverage | Put 3+ residents on leave same week, verify coverage check fires |
| `vacation_carryover` | Unused vacation from prior block not tracked | Verify YTD leave tracking across blocks |
| `duty_hour_violation` | 80-hour rule checked within block only, not across boundaries | Create 79-hour block ending + 5-hour block start, verify violation |

**Well-tested areas (for reference):** weekend (838 mentions), holiday (579), max_consecutive (110), moonlighting (56), one_in_seven (35), call_equity (32).

See `docs/perplexity-uploads/started/full-codebase/RESULTS.md`, Finding 3.3.1.

---

## 6. Git Workflow Recovery

### Committed to Wrong Branch

```bash
# Save your changes
git stash

# Switch to correct branch
git checkout correct-branch

# Apply changes
git stash pop
```

### Need to Undo Last Commit (not pushed)

```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes entirely
git reset --hard HEAD~1
```

### Diverged from Main

```bash
# Rebase onto latest main (preferred)
git fetch origin main
git rebase origin/main

# If conflicts are too messy, merge instead
git merge origin/main
```

### NEVER Do These

- `git push --force` to main/master
- `git reset --hard` on shared branches
- `--allow-unrelated-histories` without explicit approval

---

## 7. Configuration & Secrets

### Environment Variables

| Variable | Required | Where Defined | Purpose |
|----------|----------|---------------|---------|
| `SECRET_KEY` | Yes | `.env` | JWT signing |
| `DATABASE_URL` | Yes | `.env` | PostgreSQL connection |
| `REDIS_URL` | Yes | `.env` | Cache/Celery broker |
| `NEXT_PUBLIC_API_URL` | Yes | `.env` | Frontend API base URL |

### .env Best Practices

1. **Never commit `.env`** - It's in .gitignore
2. **Use `.env.example`** - Template with dummy values
3. **Validate on startup** - App refuses to start with missing/weak secrets
4. **Generate strong secrets:**
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

### What NOT to Log

- Passwords
- JWT tokens
- API keys
- PII (names, emails, schedules)
- Full stack traces in production

---

## 8. Frontend-Backend Integration

### Axios Interceptor Behavior

Located in `frontend/src/lib/api.ts`:

```typescript
// Request interceptor: camelCase → snake_case
// Converts { pgyLevel: 2 } to { pgy_level: 2 }

// Response interceptor: snake_case → camelCase
// Converts { pgy_level: 2 } to { pgyLevel: 2 }
```

### TanStack Query Patterns

```typescript
// ✓ Correct query with proper typing
const { data: people } = useQuery({
  queryKey: ['people'],
  queryFn: () => api.get<Person[]>('/people'),
});

// Access with camelCase
people?.map(p => p.pgyLevel)  // Works!
```

### Error Handling at Boundaries

```typescript
// API errors are transformed by axios interceptor
try {
  await api.post('/people', newPerson);
} catch (error) {
  if (error instanceof ApiError) {
    // Structured error with code, message, details
    console.error(error.message);
  }
}
```

### Cookie/CORS Notes

- Authentication uses httpOnly cookies (XSS-resistant)
- API requests go through Next.js proxy (`/api/*` → backend)
- This makes requests same-origin, avoiding CORS issues
- SameSite=lax cookies work because of same-origin

### WebSocket Conventions

**Backend sends camelCase, frontend accepts both (belt + suspenders):**

**Backend (Pydantic):**
```python
from pydantic.alias_generators import to_camel

class WebSocketEventBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

**Frontend (defensive transform):**
```typescript
function snakeToCamel(obj: unknown): unknown {
  // Recursively converts snake_case keys to camelCase
  // Applied to all incoming WebSocket messages
}
```

**Why both?**
- Backend guarantees camelCase output
- Frontend transforms defensively (handles legacy/edge cases)
- TypeScript interfaces use camelCase (matches runtime)

### Enum Values Stay snake_case (Keys Convert, Values Don't)

**Critical distinction:** The axios interceptor and WebSocket transformer convert **keys** only, NOT **values**.

```json
// API Response (wire format)
{ "swap_type": "one_to_one", "status": "pending" }

// After axios interceptor (what frontend receives)
{ "swapType": "one_to_one", "status": "pending" }
//   ↑ key converted        ↑ value unchanged!
```

**Frontend TypeScript types MUST use snake_case for enum values:**
```typescript
// ✅ CORRECT
type SwapType = 'one_to_one' | 'absorb';
type ConflictType = 'leave_fmit_overlap' | 'back_to_back' | 'acgme_violation';

// ❌ WRONG (will never match API responses)
type SwapType = 'oneToOne' | 'absorb';
type ConflictType = 'leaveFmitOverlap' | 'backToBack' | 'acgmeViolation';
```

**Why not convert enum values?**
1. Database stores snake_case values (`swap_records.swap_type = 'one_to_one'`)
2. Changing would require database migration to update existing data
3. Enum values are stable identifiers, not display strings
4. Converting values would be error-prone (breaks round-trip)

**Summary Table:**

| Data Type | Wire Format | Frontend Receives | Frontend Type |
|-----------|-------------|-------------------|---------------|
| Object keys | snake_case | camelCase | camelCase |
| Enum values | snake_case | snake_case | snake_case |
| URL params | snake_case | N/A | snake_case |

**WebSocket URL must include `/api/v1`:**
```typescript
// ✅ CORRECT - goes through Next.js proxy, gets auth cookie
const wsUrl = `${window.location.origin}/api/v1/ws`

// ❌ WRONG - bypasses proxy, loses auth cookie
const wsUrl = `ws://localhost:8000/ws`
```

### OpenAPI Type Contract (Hydra's Heads)

**Generated types ARE the source of truth.** Schema drift is a critical bug.

```
backend/app/schemas/*.py (Pydantic)
         ↓ OpenAPI spec
frontend/src/types/api-generated.ts (auto-generated, camelCase)
         ↓ re-exported
frontend/src/types/api.ts (barrel export + utilities)
```

**Standing Orders:**

1. **Before frontend API work:** Run `cd frontend && npm run generate:types:check`
2. **After backend schema changes:** Run `cd frontend && npm run generate:types` and commit both
3. **Never manually edit `api-generated.ts`** - it's auto-generated
4. **Pre-commit hook enforces** - commits fail if types drift from backend

**Why this matters:** Manual types caused 47+ wiring disconnects (query params, enums, endpoints). Generated types eliminate drift at the source.

**Enforcement Layers (Belt & Suspenders):**

| Layer | Hook | When |
|-------|------|------|
| Pre-commit | `modron-march.sh` | Every commit |
| CI | `npm run generate:types:check` | Every PR |
| Startup | Type staleness check | Every session |

**If types are stale:**
```bash
cd frontend && npm run generate:types
git add src/types/api-generated.ts
```

---

## 9. Common CLI Tool Locations

### Tool Availability Matrix

| Tool | Run Locally? | Run via Docker? | Notes |
|------|--------------|-----------------|-------|
| `ruff` | ✅ Yes | ✅ Yes | Linting/formatting, no deps needed |
| `mypy` | ✅ Yes | ✅ Yes | Type checking, no deps needed |
| `pytest` | ❌ No | ✅ Yes | Needs FastAPI + all backend deps |
| `alembic` | ❌ No | ✅ Yes | Needs DB connection + models |
| `npm/node` | ✅ Yes | ✅ Yes | Frontend tools |
| `eslint` | ✅ Yes | ✅ Yes | Via `npm run lint` |

### Quick Reference

```bash
# Python linting (works locally!)
ruff check backend/
ruff check backend/ --fix
ruff format backend/

# Python type checking (works locally!)
mypy backend/app --ignore-missing-imports

# TypeScript linting
cd frontend && npm run lint
cd frontend && npm run lint:fix

# Run backend tests (USE DOCKER - needs all deps)
docker exec scheduler-local-backend pytest
docker exec scheduler-local-backend pytest tests/test_specific.py -v

# Run frontend tests
cd frontend && npm test

# Database migrations (USE DOCKER - needs DB)
docker exec scheduler-local-backend alembic upgrade head
docker exec scheduler-local-backend alembic revision --autogenerate -m "20260109_change"

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}" | grep scheduler
```

### Why Some Tools Need Docker

- **pytest**: Imports FastAPI, SQLAlchemy, all backend code - needs full environment
- **alembic**: Connects to database, imports models - needs running DB
- **ruff/mypy**: Just analyze code syntax/types - no runtime deps needed

### Pre-commit Checks

Before committing, run:
```bash
# Backend
ruff check backend/ --fix
ruff format backend/

# Frontend
cd frontend && npm run lint:fix

# Tests
cd backend && pytest
cd frontend && npm test
```

---

## 10. Debugging Flowcharts

### "API Returns Wrong Data"

```
1. Check Network tab - what does raw response show?
   └─> If snake_case: Backend is correct, check frontend type definitions
   └─> If wrong data: Backend bug, check service/repository layer

2. Check console.log(response.data) - what does axios return?
   └─> If camelCase: Interceptor working, check your property access
   └─> If snake_case: Interceptor not applied, check api.ts import

3. Check TypeScript interface - using camelCase?
   └─> If snake_case: BUG! Update interface to camelCase
   └─> If camelCase: Logic error elsewhere
```

### "Works Locally, Fails in Docker"

```
1. Same Python/Node version?
   └─> No: That's likely the issue
   └─> Yes: Continue

2. All dependencies installed?
   └─> Check requirements.txt/package.json match
   └─> Run: docker compose build --no-cache

3. Environment variables set?
   └─> Check docker-compose.local.yml
   └─> Run: docker exec [container] printenv | grep [VAR]

4. File changes synced?
   └─> Check volume mounts in docker-compose
   └─> Try: docker compose restart [service]

5. Port conflicts?
   └─> Run: lsof -i :[PORT]
   └─> Kill conflicting process or change port
```

### "Database Migration Failed"

```
1. Check migration name length (≤64 chars)
   └─> Too long: Rename migration file and update inside

2. Check current state
   └─> Run: docker exec scheduler-local-backend alembic current

3. Check migration syntax
   └─> Run: docker exec scheduler-local-backend alembic check

4. Force resync (last resort)
   └─> Run: docker exec scheduler-local-backend alembic stamp head
```

---

## 11. CP-SAT Activity Solver Architecture (Two Grids)

> **Why this matters:** The scheduling system uses two separate CP-SAT solvers, and understanding which "grid" a person is on determines what you can and can't do.

### The Two Grids

The system has two solvers that run in sequence:

1. **Main CP-SAT solver** (`solvers.py`) — assigns people to rotations and faculty to activities. Faculty decisions here are **authoritative**.
2. **Activity solver** (`activity_solver.py`) — assigns specific activities (C, AT, VAS, etc.) to half-day slots. By default, only residents are on this grid.

Think of it like two whiteboards:
- **Whiteboard 1 (main solver):** Both faculty and residents. Someone fills this in first.
- **Whiteboard 2 (activity solver):** Only residents. Faculty entries from Whiteboard 1 are photocopied onto Whiteboard 2 as read-only reference (baselines).

The flag `include_faculty_slots=False` (the default) is what keeps faculty off Whiteboard 2. This is intentional — if both solvers could move faculty around, they'd fight each other.

### SM vs VAS: Same Concept, Different Plumbing

**Sports Medicine (SM) alignment** works because SM faculty ARE on the activity solver's grid (when `include_faculty_slots=True`). The solver has a checkbox for "faculty does SM clinic" that it can freely toggle. So the rule "if SM resident is here, SM faculty must be here too" is straightforward — both checkboxes are on the same grid.

**Vasectomy (VAS) alignment** can't work that way because faculty are on the frozen grid. The solver can see that a faculty member exists on Thursday AM, but can't change what they're doing. So instead of giving the solver full control, we poke specific holes:

For each VAS-credentialed faculty on a VAS-eligible slot (Thu AM/PM, Fri AM only), we add a single override checkbox: "steal this faculty from whatever they're doing and reassign them to VAS." The solver can check that box if it needs to, but it can only touch those specific slots — nothing else about the faculty's schedule.

**This works elegantly because VAS is narrow.** Only 3 half-day slots per week are VAS-eligible, and only 2 faculty are VAS-credentialed. That's ~24 override checkboxes per block — tiny. If VAS could happen any day (like SM), you'd need dozens of overrides and it would get messy. The narrowness makes the "poke specific holes" approach cleaner than giving the solver full faculty control.

**Net effect is identical to SM:** resident gets VAS → solver ensures a credentialed faculty is there too. The plumbing is different, the outcome is the same.

### When Faculty Override Is Needed vs Post-Solve

| Approach | When to Use | Example |
|----------|-------------|---------|
| **In-solver override** | Activity competes for shared resources (AT coverage, physical capacity, other faculty) | VAS, PROC — pulling a faculty to VAS means one less AT preceptor |
| **Post-solve conversion** | Activity is a 1:1 relabel that doesn't affect anything else | C → CV — same room, same supervision, just a different activity code |

**Rule of thumb:** If reassigning a faculty changes what other people can do (fewer preceptors, less room capacity), it MUST be in the solver. If it's just relabeling with no side effects, post-solve is fine.

### Don't Touch These Without Understanding the Above

- `include_faculty_slots` flag — controls whether faculty are on the activity solver grid. Default `False` is correct. Setting to `True` requires `force_faculty_override=True` safety guard.
- `vas_override_candidates` / `vas_override_vars` — the "holes poked in the frozen grid" for VAS.
- `baseline_faculty_coverage` — how the activity solver accounts for faculty it can't move. VAS overrides subtract from this when activated.

### Penalty Hierarchy

The solver minimizes total penalty. Lower weight = "I'll accept this if needed." Higher weight = "Avoid at all costs."

| Penalty | Weight | What It Means |
|---------|--------|---------------|
| AT_COVERAGE_SHORTFALL | 50 | Not enough faculty supervising residents |
| CLINIC_OVERAGE | 40 | Faculty exceeding their clinic cap |
| VAS/SM_ALIGNMENT_SHORTFALL | 30 | Resident doing VAS/SM without matching faculty |
| CLINIC_MIN_SHORTFALL | 25 | Faculty not meeting minimum clinic requirement |
| OIC_CLINICAL_AVOID | 18 | OIC scheduled on dispreferred day |
| CREDENTIAL_MISMATCH | 15 | Faculty doing procedure they're not credentialed for |
| PHYSICAL_CAPACITY_SOFT | 10 | More than 6 clinical workers in one half-day |
| VAS_OVERRIDE | 8 | Cost of pulling faculty from AT/clinic to VAS |
| ADMIN/AT_EQUITY | 12 | Uneven distribution of admin or supervision time |

The solver will pull a faculty member to VAS supervision (cost 8) rather than leave a VAS shortfall (cost 30). But it won't pull faculty unnecessarily because there's still a cost.

---

## 12. Antipatterns - Things NOT to Do

> **These patterns have caused real bugs or wasted time. Learn from our pain.**

### Docker & Containers

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| `command: python -m module --args` when Dockerfile has ENTRYPOINT | Redundant, overrides ENTRYPOINT entirely | Use `command: ["--arg1", "--arg2"]` to pass args to ENTRYPOINT |
| `git reset --hard` without target | Resets to current HEAD (no change) | `git reset --hard origin/main` to reset to specific ref |
| Checking container name with `docker inspect scheduler-local-mcp` | Container might be named differently | Use `docker ps --filter name=mcp` or check actual names |

### React/Frontend

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| `useMemo(() => { setState(...) })` | Side effects in render cause warnings/loops | Use `useEffect` for side effects |
| `router.push(\`/page?blockId=\${id}\`)` | Query params bypass axios, backend expects snake_case | Use `block_id` in URL params |
| Manual types matching api-generated.ts | Types drift, runtime undefined errors | Import from `api-generated.ts`, run `generate:types` |

### Python/Backend

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| `start, end = get_block_dates(...)` | Returns dataclass, not tuple - TypeError | `dates = get_block_dates(...); dates.start_date` |
| `not column` in SQLAlchemy filter | Returns Python bool, not SQL expression | Use `~column` for SQLAlchemy NOT |
| `db.query(Model).filter(...)` | SQLAlchemy 1.x sync pattern | `await db.execute(select(Model).where(...))` |
| String interpolation into `text()` SQL | SQL injection — ~~20 vectors found~~ **FIXED** (Feb 26, PRs #1197, #1200, #1201) | Use `validate_identifier()` / `validate_search_path()` from `backend/app/db/sql_identifiers.py` |

**SQL Injection via `text()` — FIXED (Feb 26, 2026, PRs #1197, #1200, #1201):**

24 SQL injection vectors fixed. All dynamic SQL identifiers now pass through `validate_identifier()` (single identifiers) or `validate_search_path()` (multi-schema search paths) from `backend/app/db/sql_identifiers.py`. Dead code containing additional vectors removed in PR #1198 (27,598 lines of scaffolding deleted).

**Usage pattern:** See `backend/app/db/sql_identifiers.py` for `validate_identifier()` and `validate_search_path()`. Both validate via regex and return double-quoted identifiers safe for interpolation into DDL statements (VACUUM, SET search_path, etc.) where bind parameters are not supported.

**For asyncpg session variables**, use `set_config()` with bind parameters instead of `SET` statements. See `backend/app/tenancy/isolation.py` for the pattern.

### Call Equity — MAD Formulation (Feb 26, 2026, PRs #1199, #1201, #1202)

**MAD (Mean Absolute Deviation) replaced Min-Max** in `call_equity.py`. The old Chebyshev norm stopped caring about anyone below the max threshold. MAD via `AddAbsEquality` balances all faculty.

**FMIT Weekend Split Gotcha:** FMIT Saturday overnight calls must count toward **sunday** equity, not weekday. The `is_weekend` column on `CallAssignment` is used in a SQLAlchemy CASE expression to reclassify before GROUP BY. See `backend/app/scheduling/engine.py` (two locations: `_build_context()` and `_sync_academic_year_call_counts()`).

The hydration loop maps: `"weekend" -> "sunday"`, `"overnight" -> "weekday"`, `"holiday" -> "holiday"`.

**Post-solve write-back** (`_sync_academic_year_call_counts()`) is idempotent — recalculates from `call_assignments` source of truth. Never increments +1. Safe against re-generation.

### Git Workflow

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| Committing directly to local `main` | Local main diverges from origin/main | Always work on feature branches |
| `git commit --amend` after hook failure | Amends PREVIOUS commit, not failed one | Create NEW commit after fixing |
| Committing scratchpads with real names | PII hook blocks, OPSEC violation | Sanitize or gitignore PII files |

### MCP/API

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| Checking `host == "0.0.0.0"` for localhost | 0.0.0.0 is bind address, not client address | Check client IP from request scope |
| Hardcoding `localhost:8000` in containers | Containers use internal DNS | Use service name (`backend:8000`) |

### Documentation

| ❌ Antipattern | Why It's Bad | ✅ Do This Instead |
|----------------|--------------|-------------------|
| Multiple TODO/priority files | Contradictions, unclear source of truth | Single MASTER_PRIORITY_LIST.md |
| Session scratchpads referencing other scratchpads | Broken links when files move/delete | Reference committed docs or inline the info |

### Dependency Security (Feb 26, 2026 — Gemini Full-Stack Review)

Gemini 3 Pro's independent scan found 5 npm vulnerabilities across 1,186 frontend dependencies:
- **High:** `next` (DoS via insecure deserialization), `axios` (`__proto__` DoS in mergeConfig), `minimatch` (ReDoS)
- **Moderate:** `undici`, `ajv`

**Remediation:** Run `cd frontend && npm audit fix` periodically. Check `npm audit` output before releases.

---

## 13. CI/CD in the Vibecoding Age

### The Shift

Traditional CI pipelines were designed for a world where:
- Code was written by humans who make typos, forget imports, and skip tests
- PRs were reviewed by humans who miss things under time pressure
- Linting and testing happened "somewhere else" because local tooling was inconsistent

That world is changing. With LLM-assisted development, the quality gate has moved **left** — way left.

### Why CI Is Disabled (For Now)

This project runs **30+ pre-commit hooks** locally on every commit:

| Category | Hooks | What They Catch |
|----------|-------|-----------------|
| Security | PII scanner, Gitleaks, Bandit | Real names, secrets, vulnerabilities |
| Code quality | Ruff lint, Ruff format, ESLint, TSC | Style, bugs, type errors |
| Data integrity | ACGME compliance, schedule safety, swap validation | Domain rule violations |
| Contract enforcement | Modron March, D&D hooks, Gorgon's Gaze | Type drift, enum mismatches |
| Convention | Conventional commits, migration name length | Commit hygiene |

This is more thorough than most CI pipelines. CI was adding ~3 min of latency per push to re-run checks that already passed locally.

Additionally:
- **GitHub Codex** reviews PRs with full codebase context
- **Claude Code** catches bugs in real-time during development (F821, missing imports, type errors)
- **Pre-commit hooks are deterministic** — same environment as development, no "works on my machine" gap

### When to Turn CI Back On

CI becomes valuable again when any of these are true:

| Trigger | Why |
|---------|-----|
| **Multiple developers** | Can't enforce everyone's local hooks are configured identically |
| **Production deployment** | Need a clean-room build verification before release |
| **External contributors** | PRs from forks won't have your pre-commit hooks |
| **Compliance audit** | Auditors want CI logs as evidence, not "trust me, I ran hooks" |
| **CD pipeline** | Automated deployment needs a CI gate |

### Re-enabling

```bash
# GitHub Actions
gh api repos/OWNER/REPO/actions/permissions -X PUT -F enabled=true -f allowed_actions=all

# Dependabot (CVE alerts)
gh api repos/OWNER/REPO/vulnerability-alerts -X PUT
```

### The Broader Industry Trend

GitHub is exploring making PRs optional. Vercel ships from `main`. The ceremony around code review and CI was built for human-speed, human-accuracy development. When your development loop is:

1. LLM writes code with type awareness
2. 30+ hooks validate on commit
3. AI reviews the PR
4. Single developer with full context

...CI is checking homework that was already graded three times.

This is not an argument against CI in general. It's an argument that **the right quality gate depends on your team size, deployment target, and tooling maturity.** For a single-developer pre-production project with aggressive local gating, CI is overhead. For a 50-person team shipping to production, it's essential.

---

## 14. Block Schedule Import Workflow

> **Proven on:** Block 11 (Apr 9 – May 6, 2026), PR #1117
> **Reference:** [BLOCK11_SCHEDULE_LOAD.md](BLOCK11_SCHEDULE_LOAD.md)

### The Process

Loading a block schedule from an Excel handjam into the database is a multi-step pipeline. Block 11 established the canonical workflow:

```
1. Backup DB
2. Parse Excel → HDA records
3. Upsert HDAs (half_day_assignments)
4. Fix assignments table (delete stale solver records, rebuild from block_assignments)
5. Backfill block_assignment_id on HDAs
6. Populate faculty weekly templates
7. Sync absences from leave-type codes
8. Push to PR → Codex review → fix → iterate
```

### Import Templates

Sanitized, reusable templates live in `scripts/templates/`:

| Template | Purpose |
|----------|---------|
| `block_import_template.py` | Parse Excel + upsert HDAs + sync absences |
| `fix_assignments_template.py` | Delete stale assignments, rebuild from block_assignments, backfill HDA linkage |

Copy to `/tmp/import_blockNN.py`, fill in `BLOCK_CONFIG`, `NAME_MAP`, `CODE_MAP`, and run.

### Gotchas Discovered During Block 11

| Gotcha | Impact | Fix |
|--------|--------|-----|
| HDA `source` check constraint | DB rejects `excel_import` | Use `manual` (valid values: `preload\|manual\|solver\|template`) |
| Split-block residents | Engine/solver only checked primary rotation FK | Union query for both FKs, set-based template map |
| Class-level activity cache | Stale SQLAlchemy objects in ASGI server | Use instance-level `self._activity_cache` in `__init__` |
| Absence DELETE scope | `LIKE 'Block N%'` matches across academic years | Add `AND start_date >= %s AND start_date <= %s` |
| Archived rotation templates | Residents get zero solver variables | Intersect assigned IDs with active template set |
| Holiday vs weekend priority | Sunday holidays marked `W` instead of `HOL` | Check `is_holiday` before `is_weekend` |
| `get_block_dates` patch target | Mock patches wrong module, test passes vacuously | Patch where the function is *used*, not where it's *defined* |
| 4-column unpack | Adding a SELECT column without updating unpack | Always check all tuple unpacks when changing query columns |

### Codex Review Cycle Best Practice

The iterative Codex review pattern proved highly effective:

1. **Push commit** to feature branch
2. **Post `@codex review`** as PR comment
3. **Wait 2-5 min** for Codex analysis
4. **Run `/check-codex`** to fetch and parse findings
5. **Triage**: Classify P1 (must fix), P2 (should fix), P3 (nice to have), and false positives
6. **Fix and re-push** — each fix gets its own atomic commit
7. **Repeat** until clean

Block 11 went through 7 rounds. Key lesson: Codex false positives happen (e.g., constraint registered but disabled by default). Document them to prevent future churn.

### Pre-Import Checklist

- [ ] DB backup taken (`pg_dump -Fc`)
- [ ] Latest Excel version confirmed with coordinator
- [ ] `NAME_MAP` covers all Excel names (watch for asterisks, typos)
- [ ] `CODE_MAP` covers all activity codes (check for new rotation-specific codes)
- [ ] TAMC-LD vs KAP-LD distinguished per rotation site
- [ ] `block_assignments` table populated (from solver or manual entry)
- [ ] Split-block residents have `secondary_rotation_template_id` set

### Post-Import Checklist

- [ ] HDA count matches Excel (days x 2 x people)
- [ ] Activity codes 100% match between Excel and DB
- [ ] Assignments rebuilt with correct rotation templates
- [ ] HDA `block_assignment_id` populated for residents
- [ ] Faculty weekly templates have `activity_id` on all slots
- [ ] Absences match Excel leave/TDY/deployment data
- [ ] GUI renders the block schedule correctly
- [ ] PR passes Codex review (all P1/P2 addressed)

### Gotchas Discovered During Block 12

> **Block:** 12 (May 7 – Jun 3, 2026), AY 2025
> **Reference:** [BLOCK12_SCHEDULE_LOAD.md](../scheduling/BLOCK12_SCHEDULE_LOAD.md)

| Gotcha | Impact | Fix |
|--------|--------|-----|
| Celery `asyncio.run()` in forked worker → SIGSEGV on macOS | 705 crashes/day, worker restart loop | Set `--pool=solo` on macOS (celery_app.py auto-detects platform) |

---

## Quick Checklist Before PR

- [ ] TypeScript interfaces use camelCase for API response fields
- [ ] All async functions have `await` on DB operations
- [ ] Migration name is ≤64 characters
- [ ] No secrets in code or logs
- [ ] Pure-logic tests pass: `pytest <file> --noconftest` (if applicable)
- [ ] Tests pass: `pytest` and `npm test`
- [ ] Linting passes: `ruff check` and `npm run lint`
- [ ] No `console.log` left in production code
- [ ] Error handling doesn't leak sensitive info

---

## 15. Constraint Archetype Enforcement (Mind Flayer's Probe)

> **Added:** 2026-03-02, PR #1217
> **Pre-commit hook:** `scripts/archetype-check.py`
> **Archetype reference:** `.claude/archetypes/constraint.py`

### Why This Exists

LLM-generated constraint code introduced a dead-code bug where `context.resident_idx.get(faculty_uuid)` was used in a faculty constraint. Faculty UUIDs are never in `resident_idx` — the method always returned `None`, making the entire `OvernightCallGenerationConstraint` inert. The code passed linting, type checking, and even a Codex review. No existing tool catches semantic correctness at this level.

### The 6 Rules

| Rule | Name | Severity | Anti-Pattern |
|------|------|----------|-------------|
| ARCH-001 | Phantasm | **error** | `context.resident_idx` in a call-related constraint. Faculty UUIDs aren't in `resident_idx`. |
| ARCH-002 | Lich's Trap | **error** | `variables["call_assignments"] = {}` — erases solver-created variables. Constraints must READ, not initialize. |
| ARCH-003 | Doppelganger | **error** | `for x in context.faculty:` in a call constraint. Must use `call_eligible_faculty` (excludes adjuncts). |
| ARCH-004 | Silent Killer | **warning** | `add_to_cpsat()` with no `logger.info()` call. 0 constraints added = dead code, but invisible without logging. |
| ARCH-005 | Revenant's Memory | **warning** | Call coverage constraint without spacing guard. Back-to-back call nights violate ACGME if no min-spacing constraint exists. |
| ARCH-006 | Basilisk's Gaze | **warning** | Activity query ORs `code` with `display_abbreviation` — nondeterministic `.first()` when multiple activities share a display abbreviation (e.g., `C` and `fm_clinic` both display `'C'`). Use `code` only. |

### How It Works

The checker uses Python's `ast` module to parse constraint files and classify each class:
- A class is **call-related** if it has `constraint_type=ConstraintType.CALL` OR accesses `variables["call_assignments"]`
- ARCH-001/003/005 only fire on call-related classes, preventing false positives on `protected_slot.py`, `resilience.py`, etc. that correctly use `resident_idx`
- ARCH-006 scans any file under `scheduling/` for activity lookups that OR code with display_abbreviation

### Suppressing False Positives

Add `# @archetype-ok` on the flagged line:

```python
f_i = context.resident_idx.get(faculty.id)  # @archetype-ok — uses shared variable space
```

### Before Writing a New Constraint

Read `.claude/archetypes/constraint.py` — it contains annotated `# INVARIANT:` comments showing the correct patterns for:
- Faculty index lookups
- Reading solver variables
- Constraint count logging

### PR Checklist for Constraint Changes

When modifying or adding constraints, verify:
- [ ] `python3 scripts/archetype-check.py` passes with 0 errors
- [ ] Review ARCH-004 warnings — constraints without logging are harder to debug. Add `logger.info(f"Added {count} constraints")` to `add_to_cpsat()`.
- [ ] Read `.claude/archetypes/constraint.py` before writing new constraint classes

### Running Manually

```bash
# Check all constraint files
python3 scripts/archetype-check.py

# Check specific file
python3 scripts/archetype-check.py backend/app/scheduling/constraints/my_constraint.py

# Pre-commit mode (staged files only)
python3 scripts/archetype-check.py --staged
```

---

*This document should be updated whenever a new gotcha is discovered.*
