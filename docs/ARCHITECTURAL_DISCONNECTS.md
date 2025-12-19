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

*Document generated through deep cross-cutting analysis of codebase architecture.*
