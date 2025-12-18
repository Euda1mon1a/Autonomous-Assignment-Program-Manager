# Session 9: Parallel 10-Terminal Priority Evaluation

> **Generated:** 2025-12-18
> **Branch:** `claude/plan-parallel-work-PjAdD`
> **Status:** Ready for parallel execution

---

## Executive Summary

This document identifies **10 independent workstreams** for parallel terminal execution. Building on Sessions 7 and 8 accomplishments, this session focuses on:

1. **Strategic Direction** (T1) - Human-in-the-loop decisions about project direction
2. **v1.1.0 Feature Preparation** - Email notifications, bulk import foundation
3. **Code Quality** - Query optimization, type safety, modularization
4. **Test Coverage** - Expanding test coverage to undertested areas
5. **Documentation** - Keeping docs in sync with code

### Previous Session Accomplishments

| Session | Focus | Outcome |
|---------|-------|---------|
| Session 7 | 10 parallel improvements | 7,941 lines added, 128+ tests |
| Session 8 | TODO completion & planning | All 13 backend TODOs resolved (100%) |

---

## What This Repository Does

**Residency Scheduler** is a **production-ready, full-stack medical residency program scheduling application** designed to:

- **Automate Schedule Generation** - Constraint-based algorithm with ACGME compliance
- **Monitor Compliance** - 80-hour rule, 1-in-7 rule, supervision ratios
- **Handle Emergencies** - Military deployments, TDY assignments, medical emergencies
- **Manage Swaps** - Auto-matching marketplace for shift exchanges
- **Track Credentials** - Procedure certifications with expiration alerts
- **Ensure Resilience** - 80% utilization threshold, N-1/N-2 contingency analysis

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL 15, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS, TanStack Query
- **Monitoring**: Prometheus, Grafana, Loki

---

## 10-Terminal Workstream Assignments

| Terminal | Domain | Workstream | Priority | Independence |
|----------|--------|------------|----------|--------------|
| T1 | STRATEGY | Strategic Direction Decisions | High | Full |
| T2 | MODELS | Email Notification Infrastructure | High | Full |
| T3 | API | N+1 Query Elimination | High | Full |
| T4 | SCHEDULING | Constraints Module Modularization | High | Full |
| T5 | CORE | TypedDict Type Safety | Medium | Full |
| T6 | OPS | MTF Compliance Type Safety | Medium | Full |
| T7 | FE-HOOKS | Hook JSDoc Documentation | Medium | Full |
| T8 | FE-A11Y | Keyboard Navigation Expansion | Medium | Full |
| T9 | TESTS | E2E Test Coverage Expansion | Medium | Full |
| T10 | DOCS | CHANGELOG & Session Documentation | Low | Full |

---

## Detailed Workstream Specifications

### T1: STRATEGY - Strategic Direction Decisions (REQUIRES HUMAN INPUT)

**Domain:** Project direction and roadmap decisions

**Objective:** Document strategic decisions that require human input to guide future development priorities.

**Current State Analysis:**

The Residency Scheduler is at **v1.0.0** (production-ready) with these capabilities:
- Complete scheduling engine with ACGME compliance validation
- Role-based access control (8 roles)
- Absence management with military-specific tracking
- Procedure credentialing and certification tracking
- 3-tier resilience framework
- Analytics dashboard with fairness metrics
- Swap marketplace with auto-matching
- Audit logging and export functionality

**Strategic Questions Requiring Decision:**

#### 1. Target User Base
- **Option A**: Single institution focus - Optimize for one residency program
- **Option B**: Multi-program within institution - Support multiple specialties
- **Option C**: Multi-institutional SaaS - Enterprise offering across hospitals
- **Impact**: Architecture decisions, pricing model, compliance scope

#### 2. Next Major Feature Priority
| Feature | Effort | Value | Dependencies |
|---------|--------|-------|--------------|
| Email Notifications (v1.1.0) | Medium | High | SMTP server |
| Bulk Import/Export (v1.1.0) | Medium | High | None |
| Mobile App (v1.2.0) | High | Medium | API versioning |
| AI/ML Optimization (v2.0+) | Very High | High | Data volume |
| SSO/LDAP Integration (v2.0+) | Medium | Medium | IT coordination |
| External API for 3rd parties | Medium | Medium | Security audit |

#### 3. Deployment Model
- **Option A**: Self-hosted only - Customers run their own infrastructure
- **Option B**: Cloud-hosted SaaS - Anthropic-managed infrastructure
- **Option C**: Hybrid - Both options with data portability
- **Impact**: Pricing, compliance (HIPAA), support model

#### 4. Integration Priorities
- MyEvaluations (resident evaluations)
- EMR Systems (Epic, Cerner)
- Time Tracking (Kronos, ADP)
- Learning Management Systems

#### 5. Open Source vs Commercial
- **Option A**: Keep fully open source (MIT license)
- **Option B**: Open core + commercial features
- **Option C**: Source-available with commercial license
- **Impact**: Community contributions, funding, enterprise sales

**Output Required:**
Create `STRATEGIC_DECISIONS.md` documenting:
1. Current capabilities summary
2. Decision matrix for each question
3. Recommended path with rationale
4. Dependencies and blockers
5. Questions for human stakeholder

**Files to Create:**
- `STRATEGIC_DECISIONS.md` (new)

**Commit Prefix:** `docs:`

---

### T2: MODELS - Email Notification Infrastructure

**Domain:** `backend/app/models/`, `backend/app/schemas/`

**Objective:** Create database models and Pydantic schemas for v1.1.0 email notification feature.

**Tasks:**
1. Create `EmailLog` model for tracking email delivery
2. Create `EmailTemplate` model for reusable templates
3. Create corresponding Pydantic schemas
4. Update model `__init__.py` exports
5. Generate Alembic migration (DO NOT RUN)

**Files to Create/Modify:**
- `backend/app/models/email_log.py` (new)
- `backend/app/models/email_template.py` (new)
- `backend/app/schemas/email.py` (new)
- `backend/app/models/__init__.py` (update exports)
- `backend/app/schemas/__init__.py` (update exports)
- `backend/alembic/versions/xxx_add_email_tables.py` (new migration)

**Model Specifications:**

```python
# EmailLog fields
class EmailLog(Base):
    id: UUID
    notification_id: UUID  # FK to notifications
    recipient_email: str
    subject: str
    body_html: str | None
    body_text: str | None
    status: EmailStatus  # queued, sent, failed, bounced
    error_message: str | None
    sent_at: datetime | None
    retry_count: int = 0
    created_at: datetime

# EmailTemplate fields
class EmailTemplate(Base):
    id: UUID
    name: str  # unique
    subject_template: str
    body_html_template: str
    body_text_template: str
    template_type: str  # certification_expiry, schedule_change, swap_notification
    is_active: bool = True
    created_by: UUID  # FK to users
    created_at: datetime
    updated_at: datetime
```

**Success Criteria:**
- Models follow existing patterns (mixins, relationships)
- Schemas include proper validation
- Migration is reversible
- Indexes on status and created_at

**Commit Prefix:** `models:`

---

### T3: API - N+1 Query Elimination

**Domain:** `backend/app/api/routes/`

**Objective:** Eliminate N+1 query patterns using eager loading in high-traffic routes.

**Target Files (54 `.all()` queries identified):**
| File | Queries | Priority |
|------|---------|----------|
| `portal.py` | 9 | High |
| `resilience.py` | 13 | High |
| `fmit_health.py` | 10 | Medium |
| `analytics.py` | 6 | Medium |
| `fmit_timeline.py` | 4 | Low |

**Tasks:**
1. Audit queries in portal.py and add `joinedload`/`selectinload`
2. Audit queries in resilience.py and add eager loading
3. Audit queries in fmit_health.py and add eager loading
4. Add pagination where appropriate (limit default to 100)
5. Verify no N+1 patterns remain

**Pattern to Apply:**
```python
# Before (N+1)
assignments = db.query(Assignment).all()
for a in assignments:
    print(a.block.date)  # Triggers N queries

# After (eager loaded)
assignments = db.query(Assignment).options(
    joinedload(Assignment.block),
    joinedload(Assignment.person)
).all()
```

**Files to Modify:**
- `backend/app/api/routes/portal.py`
- `backend/app/api/routes/resilience.py`
- `backend/app/api/routes/fmit_health.py`
- `backend/app/api/routes/analytics.py`
- `backend/app/api/routes/fmit_timeline.py`

**Success Criteria:**
- Zero lazy loading in modified routes
- No behavioral changes to API responses
- Add logging for query counts (dev only)

**Commit Prefix:** `api:`

---

### T4: SCHEDULING - Constraints Module Modularization

**Domain:** `backend/app/scheduling/`

**Objective:** Refactor `constraints.py` (3016 lines) into modular, maintainable constraint files.

**Tasks:**
1. Analyze existing constraint types and group by domain
2. Create `constraints/` subdirectory structure
3. Extract constraints by type into separate files
4. Create constraint registry for dynamic loading
5. Update imports in `engine.py` and `solvers.py`
6. Maintain 100% backward compatibility

**Directory Structure to Create:**
```
backend/app/scheduling/constraints/
├── __init__.py        # Re-exports all constraints
├── base.py            # Abstract ConstraintBase class
├── acgme.py           # ACGME compliance constraints
├── faculty.py         # Faculty availability constraints
├── temporal.py        # Time-based constraints
├── capacity.py        # Load balancing constraints
├── custom.py          # Program-specific constraints
└── registry.py        # Constraint registration system
```

**Constraint Categories:**
- **ACGME**: 80-hour rule, 1-in-7 rule, supervision ratios
- **Faculty**: Availability, preferences, credentials
- **Temporal**: Consecutive days, block patterns, holiday rules
- **Capacity**: Room limits, procedure limits, patient ratios
- **Custom**: Program-specific rules (FMIT, call patterns)

**Success Criteria:**
- Each file < 500 lines
- All existing tests pass
- Clean import structure
- No functional changes

**Commit Prefix:** `sched:`

---

### T5: CORE - TypedDict Type Safety

**Domain:** `backend/app/core/`, `backend/app/validators/`

**Objective:** Replace `dict[str, Any]` patterns with TypedDict for improved type safety.

**Current State:** 28 files use `dict[str, Any]` patterns

**Tasks:**
1. Create `backend/app/core/types.py` with TypedDict definitions
2. Replace untyped dicts in config functions
3. Add TypedDict for validation results
4. Update function signatures
5. Verify mypy passes

**TypedDict Definitions to Create:**
```python
class ScheduleMetrics(TypedDict):
    total_assignments: int
    coverage_percentage: float
    violation_count: int
    fairness_score: NotRequired[float]

class ComplianceResult(TypedDict):
    is_compliant: bool
    violations: list[str]
    score: float
    severity: str

class ValidationContext(TypedDict):
    schedule_id: str
    person_id: NotRequired[str]
    date_range: tuple[date, date]
```

**Files to Create/Modify:**
- `backend/app/core/types.py` (new)
- `backend/app/core/config.py` (update)
- `backend/app/validators/acgme.py` (update)
- `backend/app/core/__init__.py` (update exports)

**Success Criteria:**
- No new `dict[str, Any]` in core module
- mypy passes with --strict on core/
- All public functions have type hints

**Commit Prefix:** `core:`

---

### T6: OPS - MTF Compliance Type Safety

**Domain:** `backend/app/resilience/`, `backend/app/analytics/`

**Objective:** Improve type safety in mtf_compliance.py and related modules.

**Current State:**
- `mtf_compliance.py`: 1435 lines, 40+ untyped dict usages
- Multiple `# type: ignore` comments in simulation modules

**Tasks:**
1. Create dataclasses for MTF compliance structures
2. Replace `dict[str, Any]` with proper types
3. Remove/resolve `# type: ignore` comments
4. Add comprehensive type hints
5. Create typed validation schemas

**Files to Modify:**
- `backend/app/resilience/mtf_compliance.py`
- `backend/app/resilience/simulation/base.py`
- `backend/app/resilience/simulation/__init__.py`
- `backend/app/analytics/stability_metrics.py`

**Dataclasses to Create:**
```python
@dataclass
class MTFComplianceResult:
    is_compliant: bool
    violations: list[MTFViolation]
    score: float
    recommendations: list[str]

@dataclass
class MTFViolation:
    rule_id: str
    severity: str
    description: str
    affected_items: list[str]
```

**Success Criteria:**
- No `dict[str, Any]` in mtf_compliance.py
- Zero `# type: ignore` comments
- mypy passes on all ops modules

**Commit Prefix:** `ops:`

---

### T7: FE-HOOKS - Hook JSDoc Documentation

**Domain:** `frontend/src/hooks/`

**Objective:** Add comprehensive JSDoc documentation to all custom hooks.

**Target Files:**
- `frontend/src/hooks/index.ts`
- `frontend/src/hooks/useResilience.ts`
- `frontend/src/hooks/useSchedule.ts`
- `frontend/src/hooks/useAbsences.ts`
- `frontend/src/hooks/usePeople.ts`

**Tasks:**
1. Add JSDoc to all hook functions
2. Document parameters with `@param`
3. Document return values with `@returns`
4. Add `@example` blocks for each hook
5. Document error handling behavior
6. Add `@see` links to related hooks

**JSDoc Template:**
```typescript
/**
 * Fetches schedule data for a specific schedule ID.
 *
 * @param scheduleId - The UUID of the schedule to fetch
 * @param options - Optional React Query configuration
 * @returns Query result containing schedule data, loading state, and error
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useSchedule('uuid-here');
 * if (isLoading) return <Spinner />;
 * if (error) return <ErrorMessage error={error} />;
 * return <ScheduleView schedule={data} />;
 * ```
 *
 * @see useScheduleList - For fetching multiple schedules
 * @see useScheduleMutation - For updating schedules
 */
```

**Success Criteria:**
- 100% JSDoc coverage on exported hooks
- Each hook has at least one @example
- TypeDoc generates clean output

**Commit Prefix:** `fe-hooks:`

---

### T8: FE-A11Y - Keyboard Navigation Expansion

**Domain:** `frontend/src/features/`, `frontend/src/app/`

**Objective:** Expand keyboard navigation across all feature modules.

**Focus Areas:**
| Feature | Components | Keyboard Needs |
|---------|------------|----------------|
| Swap Marketplace | 5 | Approve/reject shortcuts |
| Conflicts | 7 | Arrow key navigation |
| Analytics | 5 | Tab through charts |
| Templates | 10 | Pattern editing |

**Tasks:**
1. Add keyboard shortcuts for swap marketplace actions
2. Implement arrow key navigation for conflict list
3. Add tab navigation for analytics charts
4. Create keyboard shortcut help dialog component
5. Add skip links for main content areas
6. Ensure all interactive elements are focusable

**Implementation Pattern:**
```tsx
// Keyboard handler
const handleKeyDown = useCallback((e: KeyboardEvent) => {
  if (e.key === 'j') selectNext();
  if (e.key === 'k') selectPrevious();
  if (e.key === 'Enter') activateSelected();
  if (e.key === '?') openShortcutHelp();
}, [selectNext, selectPrevious]);

useEffect(() => {
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [handleKeyDown]);
```

**Files to Modify:**
- `frontend/src/features/swap-marketplace/*.tsx`
- `frontend/src/features/conflicts/*.tsx`
- `frontend/src/features/analytics/*.tsx`
- `frontend/src/components/common/KeyboardShortcutHelp.tsx` (new)

**Success Criteria:**
- All features navigable via keyboard
- ARIA labels on interactive elements
- Keyboard shortcuts documented in UI

**Commit Prefix:** `fe-a11y:`

---

### T9: TESTS - E2E Test Coverage Expansion

**Domain:** `frontend/e2e/`

**Objective:** Expand Playwright E2E tests for critical user journeys.

**Target Scenarios:**
1. Complete swap workflow (request → approval → execution)
2. Bulk absence creation flow
3. Schedule generation with compliance validation
4. Login → Dashboard → Logout journey
5. Mobile viewport testing (critical flows)

**Tasks:**
1. Create Page Object Model structure
2. Write E2E tests for swap workflow
3. Write E2E tests for absence management
4. Add mobile viewport configurations
5. Add visual regression baseline snapshots

**Directory Structure:**
```
frontend/e2e/
├── fixtures/
│   ├── test-data.ts
│   └── auth.setup.ts
├── pages/
│   ├── login.page.ts
│   ├── dashboard.page.ts
│   ├── schedule.page.ts
│   └── swap.page.ts
├── tests/
│   ├── auth.spec.ts
│   ├── swap-workflow.spec.ts (new)
│   ├── absence-management.spec.ts (new)
│   └── mobile-responsive.spec.ts (new)
└── playwright.config.ts
```

**Test Example:**
```typescript
test.describe('Swap Workflow', () => {
  test('complete swap request to approval', async ({ page }) => {
    const swapPage = new SwapPage(page);
    await swapPage.goto();
    await swapPage.createSwapRequest({
      week: 'Week 5',
      reason: 'Conference attendance'
    });
    await expect(swapPage.successMessage).toBeVisible();
    // Switch to approver
    await swapPage.loginAsCoordinator();
    await swapPage.approveRequest();
    await expect(swapPage.approvedBadge).toBeVisible();
  });
});
```

**Success Criteria:**
- All critical paths have E2E coverage
- Tests pass on CI (headless)
- Mobile breakpoints tested
- < 5% flaky test rate

**Commit Prefix:** `test:`

---

### T10: DOCS - CHANGELOG & Session Documentation

**Domain:** `docs/`, root `*.md` files

**Objective:** Update documentation with Session 9 changes and improvements.

**Tasks:**
1. Update `CHANGELOG.md` with Session 9 entries
2. Archive `SESSION_8_PARALLEL_PRIORITIES.md` to docs/sessions/
3. Update `docs/planning/TODO_TRACKER.md` status
4. Update `docs/planning/PARALLEL_PRIORITIES_EVALUATION.md`
5. Sync `AGENTS.md` known issues section
6. Create `docs/sessions/` archive directory

**Files to Modify:**
- `CHANGELOG.md` - Add Session 9 [Unreleased] entries
- `AGENTS.md` - Update known issues
- `docs/planning/TODO_TRACKER.md` - Update completion status
- `docs/planning/PARALLEL_PRIORITIES_EVALUATION.md` - Mark deferred items

**Files to Create:**
- `docs/sessions/SESSION_8_ARCHIVED.md` (move existing)
- `docs/sessions/README.md` (session index)

**CHANGELOG Entry Format:**
```markdown
#### Session 9 Improvements (2025-12-18)
- **Strategic Direction Document**: Documented decision points requiring human input
- **Email Infrastructure**: EmailLog and EmailTemplate models for v1.1.0
- **Query Optimization**: Eliminated N+1 patterns in 5 API route files
- **Type Safety**: TypedDict conversions in core and ops modules
- **Test Expansion**: E2E tests for swap workflow and absence management
```

**Success Criteria:**
- All Session 9 changes documented
- No stale TODO references
- Session archive created
- Documentation matches code

**Commit Prefix:** `docs:`

---

## Dependency Matrix

| Terminal | Dependencies | Blocks |
|----------|--------------|--------|
| T1: STRATEGY | None | None (human input) |
| T2: MODELS | None | None |
| T3: API | None | None |
| T4: SCHEDULING | None | None |
| T5: CORE | None | None |
| T6: OPS | None | None |
| T7: FE-HOOKS | None | None |
| T8: FE-A11Y | None | None |
| T9: TESTS | None | None |
| T10: DOCS | All others (ideally) | None |

**Note:** T10 (DOCS) should ideally run last to capture all changes, but can run in parallel and update later.

---

## File Isolation Verification

| Terminal | Exclusive Domains | Conflict Risk |
|----------|-------------------|---------------|
| T1 | `STRATEGIC_DECISIONS.md` | None |
| T2 | `models/email*.py`, `schemas/email.py` | None |
| T3 | `api/routes/` | None |
| T4 | `scheduling/constraints/` | None |
| T5 | `core/types.py`, `core/config.py` | None |
| T6 | `resilience/mtf_compliance.py` | None |
| T7 | `hooks/*.ts` (JSDoc only) | None |
| T8 | `features/*/` (keyboard) | None |
| T9 | `e2e/` | None |
| T10 | `docs/`, `*.md` | None |

**Conclusion:** All 10 workstreams operate on exclusive file paths.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Strategic decisions documented | 5 questions |
| N+1 queries eliminated | 42 → 0 |
| TypedDict definitions added | 10+ |
| Hook JSDoc coverage | 100% |
| E2E test scenarios added | 5+ |
| Type ignore comments removed | 10+ |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Constraint modularization breaks solver | Incremental extraction, run tests after each |
| Eager loading changes response shape | Verify API contracts unchanged |
| E2E tests flaky | Use explicit waits, retry on failure |
| Type changes break runtime | Use TypedDict (no runtime overhead) |

---

*Generated for Session 9 parallel execution planning*
*Ready for 10-terminal orchestration*
