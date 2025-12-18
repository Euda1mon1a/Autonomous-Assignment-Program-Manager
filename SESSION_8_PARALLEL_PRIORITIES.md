# Session 8: Parallel 10-Terminal Priority Evaluation

> **Generated:** 2025-12-18
> **Branch:** `claude/parallel-work-setup-eHn0Z`
> **Status:** Ready for parallel execution

---

## Executive Summary

This document identifies **10 independent workstreams** for parallel terminal execution. All previous TODO items from the tracker have been **completed (100%)**. This session focuses on code quality improvements, v1.1.0 feature preparation, and test coverage expansion.

### Previous Session Accomplishments (Session 7)
- 7,941 lines of improvements added
- 10 parallel improvements completed
- All critical TODOs resolved

### Current Session Focus
- Code quality improvements (type safety, query optimization)
- v1.1.0 feature groundwork (email notifications, bulk import)
- Test coverage expansion
- Documentation updates

---

## 10-Terminal Workstream Assignments

| Terminal | Domain | Workstream | Priority | Est. Complexity |
|----------|--------|------------|----------|-----------------|
| T1 | MODELS | v1.1.0 Database Schema Preparation | Medium | Medium |
| T2 | API | Query Optimization (N+1 patterns) | High | Medium |
| T3 | SERVICES | Service Layer Caching | Medium | Medium |
| T4 | CORE | Type Safety - TypedDict Conversions | High | High |
| T5 | SCHEDULING | Constraints Module Modularization | High | High |
| T6 | OPS | MTF Compliance Type Safety | High | High |
| T7 | FE-CORE | Hook Documentation & JSDoc | Medium | Low |
| T8 | FE-APP | Keyboard Navigation & A11y | Medium | Medium |
| T9 | TESTS | Feature Test Coverage Expansion | High | High |
| T10 | DOCS | CHANGELOG & Documentation Sync | Low | Low |

---

## Detailed Workstream Specifications

### T1: MODELS - v1.1.0 Database Schema Preparation
**Domain:** `backend/app/models/`, `backend/app/schemas/`, `backend/app/db/`, `backend/alembic/`

**Objective:** Prepare database models and schemas for v1.1.0 features (email notifications, bulk import/export).

**Tasks:**
1. Create `EmailLog` model for email delivery tracking
   - Fields: id, notification_id, recipient_email, subject, status, error_message, sent_at, created_at
   - Status enum: queued, sent, failed, bounced
2. Create `ImportJob` model for bulk import tracking
   - Fields: id, user_id, file_name, file_size, import_type, status, total_rows, processed_rows, etc.
   - Import types: schedule, assignments, absences, certifications
3. Create `ExportTemplate` model for reusable export configurations
4. Create corresponding Pydantic schemas for API validation
5. Generate Alembic migrations

**Files to Create/Modify:**
- `backend/app/models/email_log.py` (new)
- `backend/app/models/import_job.py` (new)
- `backend/app/models/export_template.py` (new)
- `backend/app/schemas/email_log.py` (new)
- `backend/app/schemas/import_job.py` (new)
- `backend/app/schemas/export_template.py` (new)
- `backend/app/models/__init__.py` (update)
- `backend/app/schemas/__init__.py` (update)

**Success Criteria:**
- All models have proper SQLAlchemy relationships
- Schemas include validation for status enums
- Migrations are reversible
- Models follow existing patterns

**Commit Prefix:** `models:`

---

### T2: API - Query Optimization (N+1 Patterns)
**Domain:** `backend/app/api/routes/`, `backend/app/api/dependencies/`

**Objective:** Optimize database queries to eliminate N+1 patterns using eager loading.

**Current State:**
- 54 `.all()` queries identified across 12 route files
- Key files: portal.py (9), resilience.py (13), fmit_health.py (10), analytics.py (6)

**Tasks:**
1. Add `joinedload`/`selectinload` to queries that access relationships
2. Replace `.all()` with paginated queries where appropriate
3. Add query timeout limits for long-running operations
4. Implement query result caching for read-heavy endpoints
5. Add database query logging for development debugging

**Files to Modify:**
- `backend/app/api/routes/portal.py` - 9 queries to optimize
- `backend/app/api/routes/resilience.py` - 13 queries to optimize
- `backend/app/api/routes/fmit_health.py` - 10 queries to optimize
- `backend/app/api/routes/analytics.py` - 6 queries to optimize
- `backend/app/api/routes/fmit_timeline.py` - 4 queries to optimize

**Optimization Patterns:**
```python
# Before
assignments = db.query(Assignment).all()
for a in assignments:
    print(a.block.date)  # N+1 query!

# After
assignments = db.query(Assignment).options(
    joinedload(Assignment.block)
).all()
```

**Success Criteria:**
- Zero N+1 queries in modified routes
- Query performance improved by >50%
- No regression in API response format

**Commit Prefix:** `api:`

---

### T3: SERVICES - Service Layer Caching
**Domain:** `backend/app/services/`, `backend/app/repositories/`

**Objective:** Add caching layer to frequently-used service methods to reduce database load.

**Tasks:**
1. Identify high-frequency service calls (analytics, schedule lookups)
2. Implement Redis-based caching for read-heavy operations
3. Add cache invalidation on write operations
4. Create caching decorators for common patterns
5. Add cache hit/miss metrics for monitoring

**Files to Create/Modify:**
- `backend/app/services/cache_service.py` (new)
- `backend/app/services/schedule_service.py` (add caching)
- `backend/app/services/analytics_service.py` (add caching)
- `backend/app/repositories/assignment_repository.py` (add caching)

**Caching Patterns:**
```python
from functools import lru_cache
from app.core.cache import redis_cache

@redis_cache(ttl=300, key_prefix="schedule")
async def get_schedule_overview(schedule_id: UUID):
    # Expensive query here
    pass
```

**Success Criteria:**
- Cache hit rate >70% for repeated queries
- Cache invalidation properly triggers on updates
- TTL configured appropriately per data type

**Commit Prefix:** `svc:`

---

### T4: CORE - Type Safety (TypedDict Conversions)
**Domain:** `backend/app/core/`, `backend/app/middleware/`, `backend/app/validators/`

**Objective:** Replace `dict[str, Any]` patterns with TypedDict or Pydantic models for improved type safety.

**Current State:**
- 28 files use `dict[str, Any]` patterns
- Primary hotspots in analytics, resilience, and maintenance modules

**Tasks:**
1. Create TypedDict definitions for common data structures
2. Replace untyped dicts in core module functions
3. Add runtime type validation where needed
4. Update function signatures with proper type hints
5. Ensure mypy passes with strict mode

**Files to Create/Modify:**
- `backend/app/core/types.py` (new - centralized TypedDict definitions)
- `backend/app/core/config.py` (add typed settings)
- `backend/app/validators/acgme.py` (typed validation results)
- `backend/app/middleware/audit.py` (typed audit context)

**TypedDict Examples:**
```python
from typing import TypedDict, NotRequired

class ScheduleMetrics(TypedDict):
    total_assignments: int
    coverage_percentage: float
    violation_count: int
    fairness_score: NotRequired[float]
```

**Success Criteria:**
- No new `dict[str, Any]` in core module
- mypy passes with --strict flag
- All public functions have type hints

**Commit Prefix:** `core:`

---

### T5: SCHEDULING - Constraints Module Modularization
**Domain:** `backend/app/scheduling/`

**Objective:** Refactor the large constraints.py (3016 lines) into modular, maintainable constraint files.

**Tasks:**
1. Analyze existing constraint definitions and group by type
2. Create constraint subdirectory with separate files:
   - `acgme_constraints.py` - ACGME compliance rules
   - `faculty_constraints.py` - Faculty availability/preferences
   - `time_constraints.py` - Time-based constraints
   - `capacity_constraints.py` - Capacity/load balancing
   - `custom_constraints.py` - Program-specific rules
3. Create constraint registry/factory pattern
4. Update imports in engine.py and solvers.py
5. Maintain backward compatibility

**Files to Create:**
```
backend/app/scheduling/constraints/
├── __init__.py
├── base.py           # Abstract constraint class
├── acgme.py          # ACGME compliance constraints
├── faculty.py        ***REMOVED***-related constraints
├── temporal.py       # Time-based constraints
├── capacity.py       # Load/capacity constraints
├── custom.py         # Custom program constraints
└── registry.py       # Constraint registration system
```

**Success Criteria:**
- Each constraint file <500 lines
- All existing tests pass
- No behavior changes in constraint evaluation
- Clean import structure

**Commit Prefix:** `sched:`

---

### T6: OPS - MTF Compliance Type Safety
**Domain:** `backend/app/maintenance/`, `backend/app/resilience/`, `backend/app/notifications/`, `backend/app/analytics/`

**Objective:** Improve type safety in mtf_compliance.py and related resilience modules.

**Current State:**
- mtf_compliance.py: 1435 lines, 40+ untyped dict usages
- Multiple type: ignore comments in simulation modules

**Tasks:**
1. Create typed data classes for MTF compliance structures
2. Replace dict[str, Any] with proper types
3. Remove or resolve type: ignore comments
4. Add comprehensive type hints to all functions
5. Create validation schemas for compliance data

**Files to Modify:**
- `backend/app/resilience/mtf_compliance.py` - Main type safety improvements
- `backend/app/resilience/simulation/base.py` - Remove type ignores
- `backend/app/resilience/simulation/__init__.py` - Type improvements
- `backend/app/analytics/stability_metrics.py` - Type consistency

**Type Improvement Examples:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ComplianceResult:
    is_compliant: bool
    violations: list[str]
    score: float
    recommendations: Optional[list[str]] = None
```

**Success Criteria:**
- No dict[str, Any] in mtf_compliance.py
- Zero type: ignore comments
- mypy passes on all ops modules

**Commit Prefix:** `ops:`

---

### T7: FE-CORE - Hook Documentation & JSDoc
**Domain:** `frontend/src/components/`, `frontend/src/contexts/`, `frontend/src/lib/`, `frontend/src/types/`

**Objective:** Add comprehensive JSDoc documentation to all custom hooks for better developer experience.

**Current Hooks:**
- `frontend/src/hooks/index.ts`
- `frontend/src/hooks/useResilience.ts`
- `frontend/src/hooks/useSchedule.ts`
- `frontend/src/hooks/useAbsences.ts`
- `frontend/src/hooks/usePeople.ts`

**Tasks:**
1. Add JSDoc comments to all hook functions
2. Document parameters, return values, and usage examples
3. Add @example blocks for common use cases
4. Document error handling behavior
5. Add deprecation notices where applicable

**JSDoc Template:**
```typescript
/**
 * Hook for managing schedule data with React Query.
 *
 * @param scheduleId - The UUID of the schedule to fetch
 * @param options - Optional React Query configuration
 * @returns Query result with schedule data, loading state, and error
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useSchedule(scheduleId);
 * if (isLoading) return <Spinner />;
 * return <ScheduleView schedule={data} />;
 * ```
 */
export function useSchedule(scheduleId: string, options?: UseQueryOptions) {
  // ...
}
```

**Success Criteria:**
- 100% JSDoc coverage on public hooks
- Each hook has at least one example
- TypeDoc generates clean documentation

**Commit Prefix:** `fe-core:`

---

### T8: FE-APP - Keyboard Navigation & Accessibility
**Domain:** `frontend/src/app/`, `frontend/src/features/`, `frontend/public/`

**Objective:** Improve keyboard navigation and accessibility across all feature modules.

**Current Features (54 components across 15 feature areas):**
- swap-marketplace (5 components)
- conflicts (7 components)
- analytics (5 components)
- audit (6 components)
- templates (10 components)
- And more...

**Tasks:**
1. Add keyboard shortcuts for common actions
2. Ensure all interactive elements are focusable
3. Add ARIA labels to complex UI components
4. Implement skip links for main content
5. Add keyboard shortcut help dialog
6. Test with screen readers

**Focus Areas:**
- Swap marketplace: Add keyboard shortcuts for approve/reject
- Conflict dashboard: Navigate conflicts with arrow keys
- Analytics: Tab navigation through charts
- Template editor: Keyboard-driven pattern editing

**Accessibility Improvements:**
```tsx
// Add keyboard handler
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    handleAction();
  }
};

// Add ARIA labels
<button
  aria-label="Approve swap request"
  aria-describedby="swap-details"
  onKeyDown={handleKeyDown}
>
  Approve
</button>
```

**Success Criteria:**
- All features navigable via keyboard alone
- ARIA labels on all interactive elements
- Passes WAVE accessibility audit
- Keyboard shortcuts documented

**Commit Prefix:** `fe-app:`

---

### T9: TESTS - Feature Test Coverage Expansion
**Domain:** `backend/tests/`, `frontend/src/__tests__/`

**Objective:** Expand test coverage for undertested features and critical paths.

**Current State:**
- 40 frontend test files
- 17 E2E test files
- Coverage gaps in import/export, conflicts, analytics features

**Tasks:**
1. Add unit tests for import/export functionality
2. Add integration tests for conflict resolution flow
3. Add component tests for analytics visualizations
4. Add E2E tests for complete swap workflow
5. Add performance regression tests

**Test Files to Create:**
```
backend/tests/
├── routes/test_import_routes.py (new)
├── routes/test_export_routes.py (new)
├── services/test_conflict_service.py (expand)
├── services/test_analytics_service.py (expand)

frontend/__tests__/
├── features/import-export/ImportPreview.test.tsx (new)
├── features/import-export/ExportPanel.test.tsx (new)
├── features/conflicts/ConflictResolution.test.tsx (new)
├── features/analytics/AnalyticsDashboard.test.tsx (new)

frontend/e2e/
├── swap-workflow.spec.ts (expand)
├── bulk-operations.spec.ts (new)
```

**Coverage Targets:**
- Backend: 85% line coverage
- Frontend: 80% line coverage
- E2E: All critical user journeys

**Success Criteria:**
- All new tests pass
- Coverage increases by 5%+
- No flaky tests introduced

**Commit Prefix:** `test:`

---

### T10: DOCS - CHANGELOG & Documentation Sync
**Domain:** `docs/`, root `*.md` files

**Objective:** Update CHANGELOG with recent improvements and sync documentation with code changes.

**Tasks:**
1. Update CHANGELOG.md with Session 7 & 8 improvements
2. Update TODO_TRACKER.md to reflect completed items
3. Update AGENTS.md with resolved known issues
4. Sync API documentation with route changes
5. Update architecture diagrams if needed
6. Add keyboard shortcuts reference to user guide

**Files to Modify:**
- `CHANGELOG.md` - Add v1.0.1 entries
- `docs/planning/TODO_TRACKER.md` - Mark items complete
- `AGENTS.md` - Update known issues section
- `docs/planning/PARALLEL_PRIORITIES_EVALUATION.md` - Archive and update
- `docs/user-guide/keyboard-shortcuts.md` (new)

**CHANGELOG Format:**
```markdown
## [1.0.1] - 2025-12-18

### Added
- Email notification infrastructure (models, schemas)
- Query optimization with eager loading
- Comprehensive hook documentation

### Changed
- Modularized constraints module
- Improved type safety across codebase

### Fixed
- N+1 query patterns in API routes
```

**Success Criteria:**
- All recent changes documented
- No stale TODO references
- Documentation matches code

**Commit Prefix:** `docs:`

---

## Dependency Matrix

| Terminal | Dependencies | Blocks |
|----------|--------------|--------|
| T1: MODELS | None | T2 (schema refs) |
| T2: API | None | None |
| T3: SERVICES | None | None |
| T4: CORE | None | None |
| T5: SCHEDULING | None | None |
| T6: OPS | None | None |
| T7: FE-CORE | None | T8 (hook usage) |
| T8: FE-APP | None | None |
| T9: TESTS | None | None |
| T10: DOCS | All others | None |

**Note:** T10 (DOCS) should ideally run after others complete to capture all changes.

---

## File Isolation Verification

| Terminal | Exclusive Files | Potential Conflicts |
|----------|-----------------|---------------------|
| T1 | `models/`, `schemas/`, `db/`, `alembic/` | None |
| T2 | `api/routes/`, `api/dependencies/` | None |
| T3 | `services/`, `repositories/` | None |
| T4 | `core/`, `middleware/`, `validators/` | None |
| T5 | `scheduling/` | None |
| T6 | `maintenance/`, `resilience/`, `notifications/`, `analytics/` | None |
| T7 | `components/`, `contexts/`, `lib/`, `types/` | None |
| T8 | `app/`, `features/`, `public/` | None |
| T9 | `backend/tests/`, `frontend/__tests__/` | None |
| T10 | `docs/`, root `*.md` | None |

**Conclusion:** All 10 workstreams operate on exclusive file paths with zero overlap.

---

## Execution Protocol

### Pre-Flight Checklist
1. Verify branch: `git branch` should show `claude/parallel-work-setup-eHn0Z`
2. Pull latest: `git pull origin claude/parallel-work-setup-eHn0Z`
3. Check for uncommitted changes: `git status` should be clean

### Terminal Launch Commands
Each terminal receives its domain-specific prompt from `PARALLEL_10_TERMINAL_ORCHESTRATION.md` with the specific task from this document inserted.

### Merge Strategy
1. All terminals push to same branch
2. Sequential git pulls before each push
3. No merge conflicts expected (domains are exclusive)
4. Final verification: `pytest && npm test`

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Total files modified | 50-80 |
| Lines added | 3,000-5,000 |
| Test coverage increase | +5% |
| Type errors reduced | -50% |
| N+1 queries eliminated | 54 → 0 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Import cycles after modularization | Careful import planning in T5 |
| Cache invalidation bugs | Comprehensive cache testing in T3 |
| Breaking type changes | Run mypy before commits in T4, T6 |
| Test flakiness | Isolate tests, avoid shared state in T9 |
| Documentation drift | T10 runs last to capture all changes |

---

*Generated for Session 8 parallel execution planning*
*Ready for 10-terminal orchestration*
