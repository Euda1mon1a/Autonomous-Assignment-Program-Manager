# TODO Tracker - Backend Implementation Items

This document tracks all TODO, FIXME, and HACK comments found in the codebase that require implementation or attention.

## Overview

| Category | Count | Priority |
|----------|-------|----------|
| Swap Service TODOs | 5 | High |
| Stability Metrics TODOs | 3 | Medium |
| Leave Routes TODOs | 2 | Medium |
| Portal Routes TODOs | 2 | Low |
| Other TODOs | 1 | Low |

---

## High Priority - Swap Service Implementation

### 1. Persist SwapRecord Model
**Location:** `backend/app/services/swap_executor.py:60`
```python
# TODO: Persist SwapRecord when model is wired
```
**Description:** The SwapRecord needs to be persisted to the database when the ORM model is properly configured.
**Dependencies:** SwapRecord SQLAlchemy model
**Assignee:** TBD

### 2. Update Schedule Assignments
**Location:** `backend/app/services/swap_executor.py:61`
```python
# TODO: Update schedule assignments
```
**Description:** After a swap is executed, the underlying schedule assignments need to be updated to reflect the exchange.
**Dependencies:** Schedule assignment update service
**Assignee:** TBD

### 3. Update Call Cascade
**Location:** `backend/app/services/swap_executor.py:62`
```python
# TODO: Update call cascade
```
**Description:** Call cascade information needs to be updated after swap execution to maintain accurate call schedules.
**Dependencies:** Call cascade update logic
**Assignee:** TBD

### 4. Implement SwapRecord Model Integration
**Location:** `backend/app/services/swap_executor.py:84`
```python
# TODO: Implement when SwapRecord model is wired
```
**Description:** Full implementation needed when the SwapRecord model is connected to the database.
**Dependencies:** Database migration for SwapRecord
**Assignee:** TBD

### 5. FMIT Week Verification
**Location:** `backend/app/services/swap_request_service.py:668`
```python
# TODO: Implement proper FMIT week verification
```
**Description:** Faculty Member In Training (FMIT) week verification needs proper implementation for swap eligibility.
**Dependencies:** FMIT schedule data
**Assignee:** TBD

---

## Medium Priority - Stability Metrics

### 6. Version History Lookup
**Location:** `backend/app/analytics/stability_metrics.py:222`
```python
# TODO: Implement version history lookup using SQLAlchemy-Continuum
```
**Description:** Implement schedule version history lookup for change tracking and rollback capabilities.
**Dependencies:** SQLAlchemy-Continuum integration
**Assignee:** TBD

### 7. ACGME Validator Integration
**Location:** `backend/app/analytics/stability_metrics.py:520`
```python
# TODO: Integrate with app.scheduling.validator.ACGMEValidator
```
**Description:** Connect stability metrics with the ACGME compliance validator for comprehensive compliance checking.
**Dependencies:** ACGMEValidator service
**Assignee:** TBD

### 8. Schedule Version History Query
**Location:** `backend/app/analytics/stability_metrics.py:544`
```python
# TODO: Implement by querying schedule version history
```
**Description:** Query historical schedule versions for analytics and reporting purposes.
**Dependencies:** Version history table
**Assignee:** TBD

---

## Medium Priority - Leave Routes

### 9. FMIT Conflict Checking
**Location:** `backend/app/api/routes/leave.py:180`
```python
# TODO: Check for FMIT conflicts when schedule data is available
```
**Description:** Implement conflict checking for Faculty Member In Training schedules when processing leave requests.
**Dependencies:** FMIT schedule integration
**Assignee:** TBD

### 10. Background Conflict Detection Trigger
**Location:** `backend/app/api/routes/leave.py:236`
```python
# TODO: Trigger conflict detection in background
```
**Description:** After leave is approved, trigger background task to detect and alert on any resulting conflicts.
**Dependencies:** Celery task integration
**Assignee:** TBD

---

## Low Priority - Portal Routes

### 11. Conflict Checking for Available Weeks
**Location:** `backend/app/api/routes/portal.py:102`
```python
has_conflict=False,  # TODO: Could check conflict_alerts table
```
**Description:** Enhancement to check the conflict_alerts table when returning available weeks.
**Dependencies:** conflict_alerts table query
**Assignee:** TBD

### 12. Candidate Notifications
**Location:** `backend/app/api/routes/portal.py:306`
```python
# TODO: Create notifications for candidates
```
**Description:** Create notification system to alert swap candidates when they match a swap request.
**Dependencies:** Notification service
**Assignee:** TBD

---

## Reference Documentation

### Related Files
- `backend/app/services/swap_executor.py` - Main swap execution logic
- `backend/app/services/swap_request_service.py` - Swap request handling
- `backend/app/analytics/stability_metrics.py` - Schedule stability analytics
- `backend/app/api/routes/leave.py` - Leave management endpoints
- `backend/app/api/routes/portal.py` - Faculty portal endpoints

### External Reference
- See `docs/TODO_RESILIENCE.md` for production resilience checklist
- Referenced in `backend/app/notifications/tasks.py:37`

---

## Completion Tracking

| TODO | Status | PR/Commit | Date |
|------|--------|-----------|------|
| #1 Persist SwapRecord | Pending | - | - |
| #2 Update Schedule | Pending | - | - |
| #3 Update Call Cascade | Pending | - | - |
| #4 SwapRecord Integration | Pending | - | - |
| #5 FMIT Verification | Pending | - | - |
| #6 Version History | Pending | - | - |
| #7 ACGME Integration | Pending | - | - |
| #8 Schedule History Query | Pending | - | - |
| #9 FMIT Conflict Check | Pending | - | - |
| #10 Background Conflicts | Pending | - | - |
| #11 Conflict Table Check | Pending | - | - |
| #12 Candidate Notifications | Pending | - | - |

---

*Last updated: 2025-12-18*
*Generated by automated TODO scanning*
