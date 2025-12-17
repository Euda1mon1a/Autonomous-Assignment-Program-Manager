# Terminal Capability Reference

Reference guide for what each terminal (T1-T5) can do in parallel orchestration sessions.

---

## T1: CORE - Backend Data Layer

**Domain:** Data models, schemas, persistence, migrations

**Exclusive Paths:**
- `backend/app/models/`
- `backend/app/schemas/`
- `backend/app/db/`
- `backend/alembic/`

**Commit Prefix:** `core:`

**Can Create/Modify:**
- SQLAlchemy models (tables, relationships, indexes)
- Pydantic schemas (request/response validation)
- Alembic migrations (schema changes)
- Database utilities and session management

**Common Tasks:**
- Add/modify database fields
- Create new entity types
- Add validation logic to schemas
- Create database migrations
- Optimize model queries
- Add computed properties to models

**Typical Parallelism:** 3-5 subagents
| Subagent | Focus Area |
|----------|------------|
| 1 | Models (SQLAlchemy) |
| 2 | Schemas (Pydantic) |
| 3 | Migrations (Alembic) |
| 4 | DB utilities |
| 5 | Cross-cutting model concerns |

**Dependencies:** Usually none - T1 work typically unblocks T2 and T3

---

## T2: API - HTTP Layer & Business Logic

**Domain:** Routes, services, middleware, core utilities

**Exclusive Paths:**
- `backend/app/api/`
- `backend/app/services/`
- `backend/app/core/`

**Commit Prefix:** `api:`

**Can Create/Modify:**
- FastAPI route handlers
- Service layer functions
- Middleware components
- Error handling utilities
- Authentication/authorization logic
- Config and core utilities

**Common Tasks:**
- Add new API endpoints
- Improve error responses
- Add rate limiting/auth
- Refactor service layer
- Add request validation
- Implement business logic

**Typical Parallelism:** 4-5 subagents
| Subagent | Focus Area |
|----------|------------|
| 1 | Routes file A (e.g., schedule.py) |
| 2 | Routes file B (e.g., assignments.py) |
| 3 | Services |
| 4 | Core/middleware |
| 5 | Integration/cross-cutting |

**Dependencies:** Often depends on T1 for schema changes

---

## T3: SCHED - Scheduling Engine

**Domain:** Optimization algorithms, constraint solving

**Exclusive Paths:**
- `backend/app/scheduling/`

**Commit Prefix:** `sched:`

**Can Create/Modify:**
- Solver implementations (OR-Tools, PuLP, Greedy)
- Constraint definitions
- Scheduling engine logic
- Optimization algorithms
- Solver diagnostics

**Common Tasks:**
- Add new constraints
- Improve solver performance
- Add diagnostic/explainability features
- Implement new solving strategies
- Add fallback mechanisms
- Optimize constraint handling

**Typical Parallelism:** 3-4 subagents
| Subagent | Focus Area |
|----------|------------|
| 1 | Solvers (OR-Tools, PuLP) |
| 2 | Constraints |
| 3 | Engine orchestration |
| 4 | Diagnostics/reporting |

**Dependencies:** May depend on T1 for model changes

---

## T4: FE - Frontend

**Domain:** React components, UI logic, styling

**Exclusive Paths:**
- `frontend/src/`
- `frontend/public/`

**Commit Prefix:** `fe:`

**Can Create/Modify:**
- React components
- Hooks and contexts
- API client functions
- Styles (CSS/Tailwind)
- Static assets
- Frontend utilities

**Common Tasks:**
- Build new UI components
- Handle API responses (success/error states)
- Add form validation
- Implement state management
- Add loading/error states
- Cache invalidation

**Typical Parallelism:** 4-5 subagents
| Subagent | Focus Area |
|----------|------------|
| 1 | Components (feature A) |
| 2 | Components (feature B) |
| 3 | Hooks/contexts |
| 4 | API client (lib/api.ts) |
| 5 | Styles/utilities |

**Dependencies:** Depends on T2 for API contracts

---

## T5: TEST - Tests & Documentation

**Domain:** Test suites, documentation, changelogs

**Exclusive Paths:**
- `backend/tests/`
- `frontend/__tests__/`
- `docs/`
- Root `*.md` files (README, CHANGELOG, etc.)
- **Except:** Do not modify `HANDOFF_*.md` files from other terminals

**Commit Prefix:** `test:` or `docs:`

**Can Create/Modify:**
- Backend unit/integration tests (pytest)
- Frontend tests (Jest/React Testing Library)
- API documentation
- User guides
- Architecture docs
- Changelogs

**Common Tasks:**
- Write tests for new features
- Update API documentation
- Add E2E test scenarios
- Update CHANGELOG
- Document new behaviors
- Create user guides

**Typical Parallelism:** 4-5 subagents
| Subagent | Focus Area |
|----------|------------|
| 1 | Backend tests (feature A) |
| 2 | Backend tests (feature B) |
| 3 | Frontend tests |
| 4 | Documentation |
| 5 | CHANGELOG/README |

**Dependencies:** Usually waits for T1-T4 to complete implementation

---

## Dependency Graph

```
T1 (CORE) ──────┬──────> T2 (API) ────────┐
                │                          │
                └──────> T3 (SCHED)        ├──> T4 (FE)
                                           │
                                           └──> T5 (TEST)
```

**Execution Order:**
1. **Phase 1:** T1, T2, T3 can start simultaneously (T2/T3 may need to wait for T1 schemas)
2. **Phase 2:** T4 starts after T2 defines API contracts
3. **Phase 3:** T5 runs after implementation is complete (or in parallel for doc-only changes)

---

## Cross-Domain Communication

When a terminal needs changes in another domain, create a `HANDOFF_FROM_[DOMAIN].md` file:

```markdown
# Handoff from [DOMAIN]

## Required Changes

### For [TARGET_DOMAIN]:
- [ ] File: `path/to/file.py`
- [ ] Change needed: Description
- [ ] Reason: Why this is needed
- [ ] Blocking: Yes/No
```

**Example:** T3 needs a new field on the Assignment model:
```markdown
# Handoff from SCHED

## Required Changes

### For CORE:
- [ ] File: `backend/app/models/assignment.py`
- [ ] Change needed: Add `solver_score: float` field
- [ ] Reason: Store optimization score for explainability
- [ ] Blocking: Yes (diagnostics feature depends on this)
```
