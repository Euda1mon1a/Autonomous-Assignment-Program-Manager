# Round 10: Parallel Task Prompts

**Branch:** `claude/review-tasks-feedback-s6oJx`
**Focus:** Complete remaining GPT 5.2 Pro checklist items + UI polish

---

## TERMINAL 1: BACKEND CORE

```
You are the BACKEND CORE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/review-tasks-feedback-s6oJx

YOUR EXCLUSIVE DOMAIN:
- backend/app/models/
- backend/app/schemas/
- backend/app/db/
- backend/alembic/

OFF LIMITS: api/, services/, scheduling/, frontend/, tests/

YOUR TASK:
Review and enhance data models for better ACGME tracking:

1. READ current models to understand the structure:
   - backend/app/models/assignment.py
   - backend/app/models/person.py
   - backend/app/schemas/assignment.py

2. ADD `override_acknowledged_at` timestamp to Assignment model
   - When a user acknowledges an ACGME violation, record when
   - Helps audit trail

3. ADD `acgme_override_count` to ScheduleRun model (if not present)
   - Track how many overrides were needed for this schedule

4. ENSURE all schemas include the new fields in response models

5. CREATE migration file if needed: `003_add_acgme_audit_fields.py`

6. Commit with prefix "core: " and push to branch

REPORT when done:
- Files modified
- Migration created (yes/no)
- Handoffs needed for other domains
```

---

## TERMINAL 2: BACKEND API

```
You are the BACKEND API orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/review-tasks-feedback-s6oJx

YOUR EXCLUSIVE DOMAIN:
- backend/app/api/
- backend/app/services/
- backend/app/core/

OFF LIMITS: models/, schemas/, scheduling/, frontend/, tests/

YOUR TASK:
Improve API error handling and add infeasibility feedback:

1. READ current implementation:
   - backend/app/api/routes/schedule.py
   - backend/app/api/routes/assignments.py
   - backend/app/services/emergency_coverage.py

2. ENHANCE schedule generation error response:
   - When generation fails (422), include WHY it failed:
     - "No residents available for date range"
     - "Rotation X requires Y residents but only Z available"
     - "Constraint conflict: [details]"
   - Return these in a `failure_reasons: list[str]` field

3. ADD endpoint: GET /api/schedule/validate-preview
   - Accepts same params as generate
   - Returns what WOULD happen without actually generating
   - Useful for dry-run before commit

4. ENSURE all error responses have consistent structure:
   ```json
   {
     "detail": "Human readable message",
     "error_code": "GENERATION_FAILED",
     "failure_reasons": ["reason 1", "reason 2"]
   }
   ```

5. Commit with prefix "api: " and push to branch

REPORT when done:
- Files modified
- New endpoints added
- Handoffs needed
```

---

## TERMINAL 3: SCHEDULING ENGINE

```
You are the SCHEDULING ENGINE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/review-tasks-feedback-s6oJx

YOUR EXCLUSIVE DOMAIN:
- backend/app/scheduling/

OFF LIMITS: models/, schemas/, api/, frontend/, tests/

YOUR TASK:
Add solver diagnostics and infeasibility explanation:

1. READ current implementation:
   - backend/app/scheduling/solvers.py
   - backend/app/scheduling/engine.py
   - backend/app/scheduling/constraints.py

2. ADD diagnostic information when solver returns no solution:
   - ORToolsSolver: Capture which constraints are tight
   - PuLPSolver: Capture solver status details
   - GreedySolver: Track why each assignment attempt failed

3. CREATE a `SolverDiagnostics` class that collects:
   - `attempted_assignments: int`
   - `successful_assignments: int`
   - `blocked_by_availability: int`
   - `blocked_by_capacity: int`
   - `blocked_by_constraint: dict[str, int]` (constraint name → count)

4. MODIFY engine.generate() to return diagnostics in response:
   - Include diagnostics even on success (helps understand solver behavior)
   - On failure, diagnostics explain what went wrong

5. Commit with prefix "sched: " and push to branch

REPORT when done:
- Files modified
- New diagnostic capabilities added
- Handoffs needed (likely API needs to expose new diagnostics)
```

---

## TERMINAL 4: FRONTEND

```
You are the FRONTEND orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/review-tasks-feedback-s6oJx

YOUR EXCLUSIVE DOMAIN:
- frontend/src/
- frontend/public/

OFF LIMITS: backend/, frontend/__tests__/, docs/

YOUR TASK:
Complete UI for ACGME warnings and conflict handling:

1. READ current implementation:
   - frontend/src/components/schedule/EditAssignmentModal.tsx
   - frontend/src/components/GenerateScheduleDialog.tsx
   - frontend/src/lib/api.ts
   - frontend/src/contexts/ToastContext.tsx

2. ENHANCE EditAssignmentModal:
   - When save returns `acgme_warnings`, display them in the modal
   - Add yellow warning banner with list of violations
   - Add "Override Reason" textarea when violations exist
   - Add "Acknowledge & Save Anyway" button

3. ENHANCE GenerateScheduleDialog:
   - Handle 207 Multi-Status: Show "Generated with warnings" message
   - Display violation count and severity breakdown
   - Handle 409 Conflict: Show "Generation already in progress" message
   - Handle 422: Show failure reasons from response

4. ADD cache invalidation:
   - After successful assignment edit, invalidate schedule query cache
   - Use react-query's invalidateQueries or refetch

5. ENSURE proper loading states:
   - Disable save button during API call
   - Show spinner during generation

6. Commit with prefix "fe: " and push to branch

REPORT when done:
- Components modified
- New UI features added
- Handoffs needed
```

---

## TERMINAL 5: TESTS & DOCS

```
You are the TESTS & DOCS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/review-tasks-feedback-s6oJx

YOUR EXCLUSIVE DOMAIN:
- backend/tests/
- frontend/__tests__/
- docs/
- Root *.md files (except HANDOFF_*.md)

OFF LIMITS: backend/app/, frontend/src/

YOUR TASK:
Add E2E tests for GPT 5.2 Pro checklist items and update docs:

1. READ the new code to understand what to test:
   - backend/app/api/routes/assignments.py (auth, ACGME validation)
   - backend/app/api/routes/schedule.py (409 conflict, 207 partial)
   - backend/app/scheduling/engine.py (atomic transactions)

2. ADD backend tests in backend/tests/:
   - test_assignment_auth.py: Test that unauthenticated requests are rejected
   - test_assignment_acgme.py: Test that ACGME warnings are returned
   - test_schedule_concurrency.py: Test double-submit returns 409
   - test_schedule_idempotency.py: Test regenerating deletes old assignments

3. ADD frontend tests in frontend/__tests__/:
   - EditAssignmentModal.test.tsx: Test warning display, override flow
   - GenerateScheduleDialog.test.tsx: Test 207/409/422 handling

4. UPDATE documentation:
   - docs/API_REFERENCE.md: Add new endpoints, status codes
   - docs/SCHEDULING_OPTIMIZATION.md: Add solver diagnostics section
   - CHANGELOG.md: Add Round 10 changes

5. Commit with prefix "test: " or "docs: " and push to branch

REPORT when done:
- Test files created
- Test count and pass/fail status
- Docs updated
```

---

## Execution Checklist

- [ ] T1 CORE launched
- [ ] T2 API launched
- [ ] T3 SCHED launched
- [ ] T4 FE launched
- [ ] T5 TEST launched
- [ ] All terminals complete
- [ ] Collect HANDOFF_*.md files
- [ ] Run `git log --oneline -10` to see all commits
- [ ] Run full test suite
- [ ] Resolve any conflicts
- [ ] Create PR or merge

---

## Expected Commits

| Terminal | Expected Commit Prefix | Expected Files |
|----------|------------------------|----------------|
| T1 | `core:` | models/, schemas/, alembic/ |
| T2 | `api:` | api/routes/, services/ |
| T3 | `sched:` | scheduling/ |
| T4 | `fe:` | frontend/src/components/, lib/ |
| T5 | `test:` / `docs:` | tests/, __tests__/, docs/, *.md |
