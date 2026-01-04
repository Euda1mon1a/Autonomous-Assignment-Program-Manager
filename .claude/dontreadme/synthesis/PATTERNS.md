# Recurring Implementation Patterns

**Purpose:** Document recurring patterns identified across development sessions to accelerate future implementations and avoid reinventing solutions.

**Last Updated:** 2026-01-03 (Session 47 - Unified Backup)

---

## Table of Contents

1. [Architectural Patterns](#architectural-patterns)
2. [Testing Patterns](#testing-patterns)
3. [Performance Patterns](#performance-patterns)
4. [Security Patterns](#security-patterns)
5. [Database Patterns](#database-patterns)
6. [Frontend Patterns](#frontend-patterns)
7. [Multi-Agent Patterns](#multi-agent-patterns)
8. [Known Gotchas](#known-gotchas)

---

## Architectural Patterns

### Layered Architecture Enforcement

**Pattern:** Strict separation of concerns across layers
```
Route → Controller → Service → Repository → Model
```

**Why:** Prevents business logic leakage into routes, improves testability

**Example Violations Found:**
- Session 14: Business logic in `/api/routes/swaps.py` - Refactored to `SwapService`
- Session 20: ACGME validation in controller - Moved to `ACGMEValidator` service

### Constraint Preflight Checks

**Pattern:** Validate constraints are properly registered before commit

**Implementation:**
1. Check constraint exports from module
2. Verify registration in constraint registry
3. Ensure tests exist for each constraint
4. Run tests before commit

**Skill:** `constraint-preflight`

### Resilience Framework Integration

**Pattern:** All schedule operations integrate resilience checks

**Checkpoints:**
1. Pre-solver validation (constraint feasibility)
2. Post-generation validation (ACGME compliance, coverage, utilization)
3. N-1/N-2 contingency analysis
4. Burnout risk scoring

**Reference:** `docs/architecture/cross-disciplinary-resilience.md`

---

## Testing Patterns

### Test-Driven Debugging (TDD)

**Pattern:** Write failing test first, then fix code

**Workflow:**
1. Write test that reproduces bug
2. Confirm test fails with expected error
3. Fix implementation
4. Verify test passes
5. No test modification during fix

**Sessions Used:** 15, 19, 26, 29

### Async Test Fixtures

**Pattern:** Use async fixtures for database operations

```python
@pytest_asyncio.fixture
async def db_session():
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

**Gotcha:** Use `pytest-asyncio` decorator, not plain `pytest.fixture`

### Coverage-Driven Test Writing

**Pattern:** Identify gaps with coverage reports, write tests to fill

**Command:**
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
# Find red (uncovered) lines
# Write tests for uncovered paths
```

**Target:** 80% coverage minimum (90%+ for critical paths)

---

## Performance Patterns

### N+1 Query Prevention

**Anti-Pattern:**
```python
persons = await db.execute(select(Person))
for person in persons.scalars():
    assignments = await db.execute(
        select(Assignment).where(Assignment.person_id == person.id)
    )
```

**Solution:**
```python
result = await db.execute(
    select(Person).options(selectinload(Person.assignments))
)
persons = result.scalars().all()
```

**Tool:** SQLAlchemy `selectinload()` or `joinedload()`

### Connection Pool Tuning

**Pattern:** Match pool size to expected load

**Settings:**
- Development: `pool_size=5, max_overflow=10`
- Production: `pool_size=20, max_overflow=40`
- Load testing: Monitor pool exhaustion with Prometheus

**Reference:** `backend/app/core/config.py`

### Query Result Caching

**Pattern:** Cache expensive queries with TTL

**Implementation:**
```python
@lru_cache(maxsize=128)
def get_rotation_templates():
    # Expensive query
    return templates
```

**Gotcha:** Invalidate cache when data changes

---

## Security Patterns

### Input Validation with Pydantic

**Pattern:** All API inputs validated through Pydantic schemas

```python
class SwapRequestCreate(BaseModel):
    requester_id: str
    shift_date: date
    swap_type: SwapType

    @validator('requester_id')
    def validate_requester(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Invalid requester ID")
        return v
```

**Enforcement:** No raw dict inputs in services

### Secret Validation at Startup

**Pattern:** Validate secrets before app starts

```python
# In backend/app/main.py
if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters")
```

**Benefit:** Fail fast, not in production

### Error Message Sanitization

**Pattern:** Never leak sensitive data in errors

**Bad:**
```python
raise HTTPException(400, f"Person {person.email} not found")
```

**Good:**
```python
logger.error(f"Person lookup failed: {person.email}")
raise HTTPException(400, "Invalid person identifier")
```

---

## Database Patterns

### Alembic Migration Workflow

**Pattern:** Every model change requires migration

**Workflow:**
1. Modify SQLAlchemy model
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration (autogenerate isn't perfect)
4. Test upgrade: `alembic upgrade head`
5. Test downgrade: `alembic downgrade -1`
6. Commit model + migration together

**Gotcha:** Never edit existing migrations in production

### Row Locking for Concurrency

**Pattern:** Use `with_for_update()` for concurrent writes

```python
assignment = await db.execute(
    select(Assignment)
    .where(Assignment.id == assignment_id)
    .with_for_update()
)
```

**Use Cases:** Swap execution, schedule generation, conflict resolution

### Soft Deletes for Audit Trails

**Pattern:** Mark deleted, don't actually delete

```python
class Assignment(Base):
    deleted_at: datetime = Column(DateTime, nullable=True)
    deleted_by: str = Column(String, nullable=True)
```

**Queries:** Always filter `deleted_at IS NULL`

---

## Frontend Patterns

### TanStack Query for Server State

**Pattern:** Use TanStack Query for all API calls

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['schedule', blockId],
  queryFn: () => fetchSchedule(blockId),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

**Benefits:** Caching, automatic refetch, loading states

### Optimistic Updates

**Pattern:** Update UI immediately, rollback on error

```typescript
const mutation = useMutation({
  mutationFn: executeSwap,
  onMutate: async (newSwap) => {
    await queryClient.cancelQueries(['swaps']);
    const previous = queryClient.getQueryData(['swaps']);
    queryClient.setQueryData(['swaps'], (old) => [...old, newSwap]);
    return { previous };
  },
  onError: (err, newSwap, context) => {
    queryClient.setQueryData(['swaps'], context.previous);
  },
});
```

### Type-Safe API Client

**Pattern:** Share types between frontend and backend

**Approach:** Generate TypeScript types from Pydantic schemas

**Tool:** `openapi-typescript` or manual type definitions in `frontend/src/types/`

---

## Multi-Agent Patterns

### SEARCH_PARTY Protocol

**Pattern:** Spawn 10 specialized reconnaissance agents

**Archetypes:** Explorer, Historian, Auditor, Synthesizer, etc.

**Use Case:** Large codebase exploration, issue diagnosis

**Session:** 36 (SEARCH_PARTY implementation)

### Embarrassingly Parallel = N Agents for N Tasks

**Pattern:** For N independent tasks, spawn N agents (not 1 agent doing N tasks)

**Discovery:** Session mcp-refinement (2026-01-01)

**Anti-Pattern (Context Collapse):**
```
# BAD: 1 agent for 25 files
Agent reads file_1 → context grows
Agent reads file_2 → context grows more
...
Agent reads file_15 → CONTEXT LIMIT HIT
Result: 0 files edited, session failed
```

**Correct Pattern (Parallel Isolation):**
```
# GOOD: 25 agents for 25 files
Agent_1 reads file_1 only → small context → SUCCESS
Agent_2 reads file_2 only → small context → SUCCESS
...
Agent_25 reads file_25 only → small context → SUCCESS
Result: 25/25 files edited
```

**Formula:** `if tasks_are_independent: parallelism = free()`

**Cost Analysis:**
| Approach | Token Cost | Wall Clock | Success Rate |
|----------|------------|------------|--------------|
| 1 agent, N tasks | N files processed | Time(N) | ~60% (context limited) |
| N agents, 1 task each | N files processed | Time(1) | ~100% (context isolated) |

**When to Apply:**
- Updating multiple files with similar changes
- Running validation across many files
- Any "for each file, do X" operation
- Search/reconnaissance across directories

**Related Skills:**
- `/search-party`: 120 parallel probes (12 G-2s x 10 probes each)
- `/qa-party`: 8+ parallel QA agents
- `/plan-party`: 10 parallel planning probes

**Priority:** HIGH - This is a fundamental multi-agent orchestration principle

### Parallel Terminal Orchestration

**Pattern:** Run independent tasks in parallel terminals

**Example:**
- Terminal 1: Backend tests
- Terminal 2: Frontend tests
- Terminal 3: Documentation updates

**Benefit:** 3x speedup for independent tasks

**Gotcha:** Ensure tasks are truly independent (no shared state)

### Context Handoff Protocol

**Pattern:** Serialize context for next agent

**Format:**
```markdown
# Handoff Context

## Current State
- Task: [what was being worked on]
- Progress: [what's complete]
- Blockers: [what's blocking progress]

## Next Steps
1. [specific action]
2. [specific action]
```

**Storage:** `.claude/Scratchpad/SESSION_XX_HANDOFF.md`

---

## Known Gotchas

### Timezone Handling

**Issue:** Scheduler runs in UTC, displays in HST (Hawaii)

**Solution:** Always convert explicitly
```python
from zoneinfo import ZoneInfo
hawaii_tz = ZoneInfo("Pacific/Honolulu")
local_time = utc_time.astimezone(hawaii_tz)
```

**Affected:** Work hour calculations, midnight resets

### ACGME Work Hour Reset

**Issue:** Limits reset at midnight local time, not UTC

**Location:** `backend/app/services/constraints/acgme.py`

**Test:** Always test around midnight boundary

### Test Isolation

**Issue:** Tests not using fresh fixtures, state leaks

**Solution:** Always use `pytest` fixtures, never shared globals

```python
@pytest.fixture
def clean_db():
    # Setup
    yield db
    # Teardown - rollback all changes
```

### Double-Booking Check

**Issue:** Missing overlap validation

**Solution:** Check `backend/app/scheduling/conflicts/overlap_detector.py`

**Validation:** Ensure all assignment creation validates overlap

### Solver Timeout

**Issue:** OR-Tools solver runs indefinitely

**Solution:** Set time limits
```python
solver.parameters.max_time_in_seconds = 300
```

**Monitoring:** Use `solver-control` skill for kill-switch

---

## Infrastructure Patterns

### Emergency Restore Safety Chain

**Pattern:** Multi-gate safety chain for critical restore operations

```
Disk Check → Immaculate Verify → Pre-Snapshot → Restore → Verify
```

**Why:** Each gate must pass before proceeding. Pre-snapshot ensures recovery even from failed restore.

**Implementation:** `scripts/stack-backup.sh emergency --confirm`

**Session 47 Discovery**

### Tiered Backup System

**Pattern:** Four-tier backup hierarchy for escalating recovery scenarios

| Tier | Location | Purpose | When to Use |
|------|----------|---------|-------------|
| 1 | `data/` | Quick SQL dumps | Daily snapshots |
| 2 | `backups/` | Named backup sets | Before risky ops |
| 3 | `immaculate/` | Frozen verified baseline | "Break glass" |
| 4 | `sacred/` | PR milestone tags | Rollback points |

**Key Rule:** Immaculate is never modified - create new immaculate baselines.

**User Philosophy:** "immaculate will usually be called on by me when things are fucky"

### Self-Documenting Backups

**Pattern:** Embed restore instructions in backup manifest

```markdown
# MANIFEST.md
**Restore Command:**
./scripts/stack-backup.sh restore backup_name

**Contents:**
- database/dump.sql.gz
- docker/images/*.tar.gz
- CHECKSUM.sha256
```

**Why:** Future-you doesn't remember which script to use

### Script Deprecation via Warning

**Pattern:** Add 5-second warning before legacy script execution

```bash
echo "⚠️  DEPRECATED: Use stack-backup.sh instead"
sleep 5
# ... continue with legacy behavior
```

**Why:** No breaking changes, clear migration path, muscle memory preserved

---

## Pattern Evolution

This document evolves as new patterns emerge. When you identify a new recurring pattern:

1. Document it here with concrete examples
2. Create a skill if automation is possible
3. Update CLAUDE.md if it affects project guidelines
4. Reference in relevant technical docs

---

**Contributors:** Sessions 1-37 collective learnings

**See Also:**
- `.claude/dontreadme/synthesis/DECISIONS.md` - Architectural decisions
- `.claude/dontreadme/synthesis/LESSONS_LEARNED.md` - Session insights
- `CLAUDE.md` - Project guidelines
