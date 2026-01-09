# Best Practices & Gotchas

> **Purpose:** Prevent common bugs and headaches. Read this before starting work.
> **Last Updated:** 2026-01-09

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

---

## 3. Database & Migrations

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

**All database operations MUST be async.** No exceptions.

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

### Integration vs Unit Tests

| Test Type | Uses Real DB | Uses Real API | Speed |
|-----------|--------------|---------------|-------|
| Unit | No (mocked) | No | Fast |
| Integration | Yes | No | Medium |
| E2E | Yes | Yes | Slow |

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

## Quick Checklist Before PR

- [ ] TypeScript interfaces use camelCase for API response fields
- [ ] All async functions have `await` on DB operations
- [ ] Migration name is ≤64 characters
- [ ] No secrets in code or logs
- [ ] Tests pass: `pytest` and `npm test`
- [ ] Linting passes: `ruff check` and `npm run lint`
- [ ] No `console.log` left in production code
- [ ] Error handling doesn't leak sensitive info

---

*This document should be updated whenever a new gotcha is discovered.*
