# Architectural Disconnects & Hidden Issues

> **Document Created:** 2025-12-19
> **Purpose:** Document "needles in haystacks" - architectural disconnects, orphaned code, and critical issues discovered through deep cross-cutting analysis
> **Action Required:** These issues should be addressed in a separate session

---

## Executive Summary

Deep analysis of the codebase revealed multiple architectural disconnects where sophisticated systems are implemented but not connected, where critical functionality is stubbed but appears functional, and where security assumptions are not enforced.

**Critical Priority:**
1. **Security**: 4 API route files have NO authentication (HIPAA violation risk)
2. **Data Integrity**: Notification system doesn't actually send emails
3. **Safety**: Swap system appears functional but doesn't modify schedules

---

## NEEDLE #1: Email System Disconnect (HIGH)

### Problem
Two separate email implementations exist that are not connected:

**Stubbed Celery Tasks** (`backend/app/notifications/tasks.py`):
```python
def send_email(to, subject, body, html=None):
    logger.info("Sending email to %s: %s", to, subject)
    # NOTE: Implement email sending here...
    return {"timestamp": ..., "status": "queued"}  # NEVER ACTUALLY SENDS
```

**Functional EmailService** (`backend/app/services/email_service.py`):
- Full SMTP implementation with TLS, authentication
- HTML templates for certification reminders
- Used by SwapNotificationService directly

### Impact
- Main NotificationService uses stubbed tasks → emails never sent
- Users think notifications are working (status: "queued") but nothing arrives
- Certification expiration reminders SILENTLY FAIL

### Fix
Wire EmailService into notification Celery tasks, OR replace stubbed tasks with calls to EmailService.

---

## NEEDLE #2: Resilience Constraints Disabled by Default (MEDIUM)

### Problem
The entire resilience constraint system (5 sophisticated constraints) is implemented but **disabled by default**.

**Location:** `backend/app/scheduling/constraints/manager.py` (lines 291-295)

```python
# All these are added then immediately disabled:
manager.add(HubProtectionConstraint(weight=15.0))
manager.add(UtilizationBufferConstraint(weight=20.0))
manager.add(ZoneBoundaryConstraint(weight=12.0))
manager.add(PreferenceTrailConstraint(weight=8.0))
manager.add(N1VulnerabilityConstraint(weight=25.0))

# Disabled by default
manager.disable("HubProtection")
manager.disable("UtilizationBuffer")
manager.disable("ZoneBoundary")
manager.disable("PreferenceTrail")
manager.disable("N1Vulnerability")
```

### Impact
- Scheduling engine uses `create_default()` which has all resilience disabled
- `create_resilience_aware()` factory exists but is never called
- System advertises resilience features that are never active

### Fix
Either:
1. Enable resilience constraints by default in `create_default()`
2. Have scheduling engine call `create_resilience_aware()` instead
3. Add configuration option to enable resilience mode

---

## NEEDLE #3: ConflictAutoResolver - 1,440 Lines of Orphaned Code (MEDIUM)

### Problem
`backend/app/services/conflict_auto_resolver.py` is a sophisticated 1,440-line conflict resolution system that is **completely unreachable**.

**Only references:**
- `conflict_auto_resolver.py` (itself)
- `tests/test_conflict_auto_resolver.py` (tests)

**Never imported by:**
- Any API route
- Any controller
- Any other service

### Features Never Used:
- `analyze_conflict()` - Deep conflict analysis
- `generate_resolution_options()` - Multiple resolution strategies
- `auto_resolve_if_safe()` - Safe auto-resolution
- `batch_auto_resolve()` - Batch processing
- Safety checks, impact assessment, rollback support

### Impact
- Advertised conflict resolution capability doesn't exist in API
- 1,440 lines of tested, sophisticated code is dead weight
- Users cannot access auto-resolution features

### Fix
Wire ConflictAutoResolver into conflict alert endpoints or remove if not needed.

---

## NEEDLE #4: SwapExecutor is a Facade (HIGH)

### Problem
SwapExecutor appears to work (creates swap records) but **doesn't actually modify schedules**.

**Location:** `backend/app/services/swap_executor.py`

```python
def _update_schedule_assignments(...):
    pass  # EMPTY - DOES NOTHING

def _update_call_cascade(...):
    pass  # EMPTY - DOES NOTHING

def rollback_swap(...):
    return RollbackResult(
        success=False,
        message="Rollback not yet implemented",
        error_code="NOT_IMPLEMENTED"
    )

def can_rollback(...):
    return False  # ALWAYS FALSE
```

**Tests confirm this** (`test_swap_executor.py`):
- 7 tests marked `@pytest.mark.skip(reason="Pending implementation")`
- Tests explicitly document "Pending schedule assignment update implementation"

### Impact
- Swaps are "executed" but schedule remains unchanged
- Users think swaps worked but assignments aren't modified
- 24-hour rollback window advertised but not functional

### Fix
Implement `_update_schedule_assignments()` and `_update_call_cascade()` or clearly mark swap feature as incomplete.

---

## NEEDLE #5: ACGME Validator Hides Violations (MEDIUM)

### Problem
ACGME validator only reports the **first violation** per resident, hiding additional violations.

**Location:** `backend/app/scheduling/validator.py` (line 226)

```python
if avg_weekly > self.MAX_WEEKLY_HOURS:
    violations.append(...)
    break  # <-- STOPS AFTER FIRST VIOLATION
```

### Impact
- Compliance reports undercount violations
- A resident with 5 80-hour violations only shows 1
- Creates false sense of compliance

### Fix
Remove `break` statement to report all violations.

---

## NEEDLE #6: Unauthenticated API Routes (CRITICAL)

### Problem
4 API route files have **NO AUTHENTICATION** in a HIPAA-sensitive healthcare application.

**Completely Unauthenticated Routes:**

1. **`absences.py`** - PHI EXPOSURE
   - `POST /absences` - Create absence records
   - `PUT /absences/{id}` - Modify absence records
   - `DELETE /absences/{id}` - Delete absence records
   - **Risk:** Anyone can view/modify who is sick/on leave

2. **`blocks.py`**
   - `POST /blocks` - Create schedule blocks
   - `POST /blocks/generate` - Generate 730+ blocks
   - `DELETE /blocks/{id}` - Delete schedule blocks
   - **Risk:** Anyone can corrupt scheduling data

3. **`academic_blocks.py`**
   - `GET /matrix/academic-blocks` - Full resident assignment matrix
   - **Risk:** Schedule data exposure without auth

4. **`rotation_templates.py`**
   - `POST`, `PUT`, `DELETE` on rotation templates
   - **Risk:** Anyone can modify rotation configuration

### Impact
- HIPAA violation risk (PHI exposure)
- Data integrity attacks possible
- No audit trail for unauthenticated actions

### Fix
Add `current_user: User = Depends(get_current_active_user)` to all endpoints.

---

## NEEDLE #7: Stubbed Webhook Delivery (LOW)

### Problem
Like email, webhook delivery in `notifications/tasks.py` is stubbed:

```python
def send_webhook(url, payload):
    logger.info("Sending webhook to %s", url)
    # NOTE: Implement HTTP POST here...
    return {"status": "queued"}  # NEVER SENDS
```

### Impact
- Webhook integrations configured but never fire
- External systems never receive notifications

---

## Priority Matrix

| Issue | Severity | Effort | Priority |
|-------|----------|--------|----------|
| #6 Unauthenticated Routes | CRITICAL | Low | **P0** |
| #4 SwapExecutor Facade | HIGH | Medium | P1 |
| #1 Email Disconnect | HIGH | Low | P1 |
| #5 ACGME Hides Violations | MEDIUM | Trivial | P2 |
| #2 Resilience Disabled | MEDIUM | Low | P2 |
| #3 Orphaned Resolver | MEDIUM | Medium | P3 |
| #7 Stubbed Webhooks | LOW | Low | P3 |

---

## The Single Change to Prevent Production Incident

**If you could make ONE change:**

Add authentication to `backend/app/api/routes/absences.py`:

```python
# Add import
from app.core.security import get_current_active_user
from app.models.user import User

# Add to each endpoint
@router.post("", response_model=AbsenceResponse, status_code=201)
def create_absence(
    absence_in: AbsenceCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # ADD THIS
):
```

**Why this one:**
- Absence data is PHI (Protected Health Information)
- Currently allows unauthenticated CRUD operations
- Single change protects most sensitive data
- Pattern can then be copied to other unauthenticated routes

---

## Notes for Fix Session

1. Do NOT modify any code during discovery session per user request
2. All issues documented here should be addressed in a dedicated fix session
3. Tests exist for most systems but test the wrong behavior (test stubbed implementations)
4. Consider adding integration tests that verify end-to-end functionality

---

## NEEDLE #8: Inconsistent Foreign Key Cascades (MEDIUM)

### Problem
Database foreign key `ondelete` behavior is inconsistent across models.

**Models with proper CASCADE:**
- `assignment.py`: `block_id`, `person_id` have `ondelete="CASCADE"`
- `absence.py`: `person_id` has `ondelete="CASCADE"`

**Models MISSING cascade behavior:**
- `swap.py`: ALL foreign keys missing `ondelete`
  ```python
  source_faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"))  # NO ondelete
  target_faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"))  # NO ondelete
  ```
- `conflict_alert.py`: `faculty_id`, `leave_id`, etc. have no cascade
- `assignment.py`: `rotation_template_id` missing `ondelete`

### Impact
- Deleting a Person with swap records → FK constraint error
- Deleting a Person with conflict alerts → FK constraint error
- Database operations may fail unexpectedly
- Data cleanup becomes complex

### Fix
Add `ondelete="CASCADE"` or `ondelete="SET NULL"` to all foreign keys based on intended behavior.

---

## NEEDLE #9: Rate Limiting Only Protects Auth Routes (HIGH)

### Problem
Rate limiting is ONLY applied to authentication endpoints, not to critical data routes.

**Protected routes** (`auth.py`):
```python
rate_limit_login = create_rate_limit_dependency(max_requests=5, window_seconds=60)
rate_limit_register = create_rate_limit_dependency(max_requests=3, window_seconds=60)
```

**Unprotected critical routes:**
- `absences.py` - No rate limiting (and no auth!)
- `blocks.py` - No rate limiting (and no auth!)
- `schedule.py` - No rate limiting on generation endpoints
- `people.py` - No rate limiting

### Impact
- DoS attacks on data manipulation endpoints
- Brute force creation/deletion of records
- No throttling on expensive operations (schedule generation)
- Resource exhaustion attacks possible

### Fix
Add rate limiting to all data manipulation endpoints, especially:
1. All POST/PUT/DELETE endpoints
2. Expensive operations (schedule generation, analytics)
3. Any endpoint that writes to database

---

## NEEDLE #10: Celery Retry Configuration is Decorative (MEDIUM)

### Problem
Notification tasks have `max_retries=3` configured but **never call `self.retry()`**.

**Location:** `backend/app/notifications/tasks.py`

```python
@shared_task(
    name="app.notifications.tasks.send_email",
    max_retries=3,               # <- CONFIGURED
    default_retry_delay=60,
)
def send_email(to, subject, body, html=None):
    logger.info("Sending email to %s: %s", to, subject)
    return {"status": "queued"}  # <- NO self.retry() ON FAILURE
```

Compare to properly implemented retry in `cleanup_tasks.py`:
```python
except Exception as exc:
    logger.exception("Cleanup failed")
    raise self.retry(exc=exc)  # <- PROPER RETRY
```

### Impact
- Tasks fail permanently on first error
- No automatic retry despite configuration
- Transient failures (network blips) cause permanent failure
- False confidence in retry behavior

### Fix
Add `self.retry(exc=e)` in exception handlers, or use `autoretry_for` decorator parameter.

---

## NEEDLE #11: Inconsistent Timezone Handling (LOW)

### Problem
Codebase mixes `datetime.now()` and `datetime.utcnow()`.

**Using `datetime.now()` (local timezone):**
- `notifications/tasks.py` (lines 40, 71, 123)

**Using `datetime.utcnow()` (correct for storage):**
- Most other files

### Impact
- Timestamp inconsistency if server timezone ≠ UTC
- Sorting by timestamp may be incorrect
- Cross-system comparisons may fail

### Fix
Replace all `datetime.now()` with `datetime.utcnow()` or use timezone-aware datetimes.

---

## NEEDLE #12: SECRET_KEY Auto-Generates on Restart (MEDIUM)

### Problem
If `SECRET_KEY` is not set in environment, a new random key is generated on each app restart.

**Location:** `backend/app/core/config.py` (line 49)

```python
SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
```

### Impact
- All JWT tokens invalidated on app restart
- All users logged out unexpectedly
- Session continuity broken in dev/staging
- Debugging auth issues becomes confusing

### Fix
1. Require explicit SECRET_KEY in all environments (not just production)
2. Or persist generated key to file on first run
3. Or fail fast if SECRET_KEY not set

---

## NEEDLE #13: Scheduler Dashboard Shows Synthetic Metrics (MEDIUM)

### Problem
The scheduler operations dashboard returns **placeholder/fake data** instead of real metrics.

**Location:** `backend/app/api/routes/scheduler_ops.py` (lines 68-112)

```python
def _calculate_task_metrics(db: Session) -> TaskMetrics:
    # TODO: Integrate with actual task tracking system (Celery, etc.)
    # For now, return synthetic metrics based on system state
    base_tasks = 100  # HARDCODED
    failed_rate = 0.05 if health_report.get("overall_status") == "healthy" else 0.15
    # ... returns fabricated numbers
```

Also `_get_recent_tasks()` (line 115+) returns placeholder data.

### Impact
- UI displays fake metrics as real
- Operators can't trust dashboard data
- Actual system problems hidden behind synthetic "healthy" metrics
- No visibility into real task execution

### Fix
Integrate with Celery's task result backend or implement proper task tracking.

---

## Updated Priority Matrix

| Issue | Severity | Effort | Priority |
|-------|----------|--------|----------|
| #6 Unauthenticated Routes | CRITICAL | Low | **P0** |
| #9 Rate Limiting Gaps | HIGH | Low | **P0** |
| #4 SwapExecutor Facade | HIGH | Medium | P1 |
| #1 Email Disconnect | HIGH | Low | P1 |
| #8 FK Cascade Issues | MEDIUM | Low | P2 |
| #10 Celery Retry Broken | MEDIUM | Low | P2 |
| #5 ACGME Hides Violations | MEDIUM | Trivial | P2 |
| #2 Resilience Disabled | MEDIUM | Low | P2 |
| #12 SECRET_KEY Issue | MEDIUM | Low | P2 |
| #13 Fake Dashboard Metrics | MEDIUM | Medium | P3 |
| #3 Orphaned Resolver | MEDIUM | Medium | P3 |
| #11 Timezone Issues | LOW | Low | P3 |
| #7 Stubbed Webhooks | LOW | Low | P3 |

---

## Summary of Systemic Patterns

### Pattern 1: "Configured but Not Wired"
Multiple features are fully implemented with tests but never connected to the API layer:
- ConflictAutoResolver (1,440 lines orphaned)
- Resilience constraints (disabled by default)
- Email service (exists but notification tasks use stubs)

### Pattern 2: "Looks Functional, Actually Stubbed"
Code paths that appear to work but do nothing:
- SwapExecutor's `_update_schedule_assignments()` is `pass`
- Notification tasks return "queued" but never send
- Scheduler dashboard shows fake metrics

### Pattern 3: "Security Assumed but Not Enforced"
Critical assumptions that aren't validated:
- Authentication assumed but not added to 4 route files
- Rate limiting configured but only on auth endpoints
- FK cascades expected but not defined

### Pattern 4: "Tests Validate the Wrong Thing"
Tests exist but validate stubbed behavior:
- SwapExecutor tests skip actual functionality
- Notification tests verify log messages, not delivery

---

## Notes for Fix Session

1. Do NOT modify any code during discovery session per user request
2. All issues documented here should be addressed in a dedicated fix session
3. Tests exist for most systems but test the wrong behavior (test stubbed implementations)
4. Consider adding integration tests that verify end-to-end functionality

---

---

## NEEDLE #14: API Session Manager Missing Rollback (HIGH)

### Problem
The `get_db()` dependency used by all API routes doesn't rollback on exception.

**Location:** `backend/app/db/session.py` (lines 38-44)

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ONLY CLOSES - NO ROLLBACK!
```

Compare to `task_session_scope()` in same file which properly handles transactions:
```python
@contextmanager
def task_session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Commit on success
    except Exception:
        session.rollback()  # Rollback on error
        raise
    finally:
        session.close()
```

### Impact
- If exception occurs after db writes but before commit → session closed without rollback
- Dirty session state may leak into connection pool
- Next request may see uncommitted changes
- Potential data inconsistency

### Fix
Update `get_db()` to match `task_session_scope()` pattern:
```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Add explicit commit
    except Exception:
        db.rollback()  # Add rollback on error
        raise
    finally:
        db.close()
```

---

## NEEDLE #15: User Input Reflected in Error Messages (LOW)

### Problem
Some HTTPException messages include user input directly, potentially leaking information.

**Examples from `resilience.py`:**
```python
raise HTTPException(status_code=400, detail=f"Unknown scenario: {request.scenario}")
raise HTTPException(status_code=400, detail=f"Invalid containment level: {level}")
raise HTTPException(status_code=400, detail=f"Invalid stress type: {stress_type}")
```

### Impact
- User input reflected back in responses
- Could assist in enumeration attacks
- Verbose error messages aid attackers

### Fix
Use generic error messages:
```python
raise HTTPException(status_code=400, detail="Invalid scenario type")
```

---

## Final Updated Priority Matrix

| # | Issue | Severity | Priority |
|---|-------|----------|----------|
| 6 | Unauthenticated Routes | CRITICAL | **P0** |
| 9 | Rate Limiting Gaps | HIGH | **P0** |
| 14 | API Session No Rollback | HIGH | **P0** |
| 4 | SwapExecutor Facade | HIGH | P1 |
| 1 | Email Disconnect | HIGH | P1 |
| 8 | FK Cascade Issues | MEDIUM | P2 |
| 10 | Celery Retry Broken | MEDIUM | P2 |
| 5 | ACGME Hides Violations | MEDIUM | P2 |
| 2 | Resilience Disabled | MEDIUM | P2 |
| 12 | SECRET_KEY Issue | MEDIUM | P2 |
| 13 | Fake Dashboard Metrics | MEDIUM | P3 |
| 3 | Orphaned Resolver | MEDIUM | P3 |
| 11 | Timezone Issues | LOW | P3 |
| 7 | Stubbed Webhooks | LOW | P3 |
| 15 | Input in Errors | LOW | P4 |

---

## Total Issues Discovered: 15

### By Category:
- **Security**: 4 issues (#6, #9, #14, #15)
- **Data Integrity**: 3 issues (#1, #4, #8)
- **Feature Completeness**: 4 issues (#2, #3, #7, #13)
- **Reliability**: 3 issues (#10, #11, #12)
- **Compliance**: 1 issue (#5)

### By Effort to Fix:
- **Trivial** (< 1 hour): #5, #11, #15
- **Low** (1-4 hours): #1, #6, #8, #9, #10, #12, #14
- **Medium** (4-16 hours): #2, #3, #4, #7, #13

---

*Document generated through deep cross-cutting analysis of codebase architecture.*
*Updated with additional findings from intersection point analysis.*
*Final count: 15 architectural disconnects identified.*
