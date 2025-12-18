# TODO Tracker - Backend Implementation Items

This document tracks all TODO, FIXME, and HACK comments found in the codebase that require implementation or attention.

## Overview

| Category | Count | Priority | Completed |
|----------|-------|----------|-----------|
| Swap Service TODOs | 5 | High | 5/5 ✅ |
| Stability Metrics TODOs | 3 | Medium | 0/3 |
| Leave Routes TODOs | 2 | Medium | 2/2 ✅ |
| Portal Routes TODOs | 2 | Low | 0/2 |
| Other TODOs | 1 | Low | 0/1 |
| **Total** | **13** | - | **7/13 (54%)** |

---

## High Priority - Swap Service Implementation

### 1. Persist SwapRecord Model ✅ COMPLETED
**Location:** `backend/app/services/swap_executor.py:60`
**Status:** COMPLETED (2025-12-18)
**Description:** SwapRecord is now persisted to the database with all relevant fields including status, timestamps, and user tracking.
**Implementation:**
- Added database persistence in `execute_swap()` method
- SwapRecord includes source/target faculty IDs, weeks, swap type, status, reason, execution timestamp, and executed_by_id
- Proper transaction handling with commit/rollback
**Assignee:** Terminal 1

### 2. Update Schedule Assignments ✅ COMPLETED
**Location:** `backend/app/services/swap_executor.py:61`
**Status:** COMPLETED (2025-12-18)
**Description:** Schedule assignments are now properly updated during swap execution to transfer assignments between faculty members.
**Implementation:**
- Implemented `_update_schedule_assignments()` method
- Queries all blocks in the specified week(s)
- Updates assignment person_id to reflect the swap
- Handles both one-to-one swaps and absorb swaps
- Adds audit notes to assignments indicating swap execution
**Assignee:** Terminal 1

### 3. Update Call Cascade ✅ COMPLETED
**Location:** `backend/app/services/swap_executor.py:62`
**Status:** COMPLETED (2025-12-18)
**Description:** Call cascade (Fri/Sat call assignments) are now updated during swap execution.
**Implementation:**
- Implemented `_update_call_cascade()` method
- Identifies Friday and Saturday dates within the swapped week
- Updates CallAssignment records to reflect new faculty assignments
- Handles both forward swaps and rollback operations
**Assignee:** Terminal 1

### 4. Implement SwapRecord Model Integration ✅ COMPLETED
**Location:** `backend/app/services/swap_executor.py:84`
**Status:** COMPLETED (2025-12-18)
**Description:** Full implementation of rollback functionality using SwapRecord model.
**Implementation:**
- Implemented `rollback_swap()` method with 24-hour window enforcement
- Implemented `can_rollback()` method to check eligibility
- Reverses schedule assignments and call cascade changes
- Updates SwapRecord status to ROLLED_BACK with timestamp and reason
- Comprehensive error handling and validation
**Assignee:** Terminal 1

### 5. FMIT Week Verification ✅ COMPLETED
**Location:** `backend/app/services/swap_request_service.py:668`
**Status:** COMPLETED (2025-12-18)
**Description:** Faculty Member In Training (FMIT) week verification is now properly implemented for swap eligibility.
**Implementation:**
- Implemented `_is_week_assigned_to_faculty()` method to verify FMIT assignments
- Queries RotationTemplate with name "FMIT" to identify FMIT rotations
- Joins Assignment and Block tables to check faculty assignments within the week date range
- Returns True if faculty has FMIT assignments in the specified week, False otherwise
- Added comprehensive test coverage in `tests/services/test_swap_request_service.py`
- Tests cover: assigned weeks, unassigned weeks, missing FMIT template, non-FMIT assignments, multiple blocks, different faculty, and week boundaries
**Assignee:** Terminal 5

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

### 9. FMIT Conflict Checking ✅ COMPLETED
**Location:** `backend/app/api/routes/leave.py:180`
**Status:** COMPLETED (2025-12-18)
**Description:** Implemented conflict checking for Faculty Member In Training schedules when processing leave requests.
**Implementation:**
- Integrated ConflictAutoDetector service into get_leave_calendar endpoint
- Calendar now detects and flags leave records that conflict with FMIT assignments
- Conflict count is included in calendar response
**Assignee:** Terminal 3

### 10. Background Conflict Detection Trigger ✅ COMPLETED
**Location:** `backend/app/api/routes/leave.py:236`
**Status:** COMPLETED (2025-12-18)
**Description:** Background task now triggers after leave creation to detect and alert on any resulting conflicts.
**Implementation:**
- Created detect_leave_conflicts Celery task in backend/app/notifications/tasks.py
- Task uses ConflictAutoDetector to find conflicts and create alerts
- Wired up task trigger in create_leave route using background_tasks
- Added comprehensive test coverage for both unit and integration scenarios
**Assignee:** Terminal 3

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
| #1 Persist SwapRecord | ✅ Completed | Terminal 1 | 2025-12-18 |
| #2 Update Schedule | ✅ Completed | Terminal 1 | 2025-12-18 |
| #3 Update Call Cascade | ✅ Completed | Terminal 1 | 2025-12-18 |
| #4 SwapRecord Integration | ✅ Completed | Terminal 1 | 2025-12-18 |
| #5 FMIT Verification | ✅ Completed | Terminal 5 | 2025-12-18 |
| #6 Version History | Pending | - | - |
| #7 ACGME Integration | Pending | - | - |
| #8 Schedule History Query | Pending | - | - |
| #9 FMIT Conflict Check | ✅ Completed | Terminal 3 | 2025-12-18 |
| #10 Background Conflicts | ✅ Completed | Terminal 3 | 2025-12-18 |
| #11 Conflict Table Check | Pending | - | - |
| #12 Candidate Notifications | Pending | - | - |

---

*Last updated: 2025-12-18*
*Generated by automated TODO scanning*
