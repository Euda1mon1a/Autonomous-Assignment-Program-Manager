# TODO Tracker - Backend Implementation Items

This document tracks all TODO, FIXME, and HACK comments found in the codebase that require implementation or attention.

## Overview

| Category | Count | Priority | Completed |
|----------|-------|----------|-----------|
| Swap Service TODOs | 5 | High | 5/5 ✅ |
| Stability Metrics TODOs | 3 | Medium | 3/3 ✅ |
| Leave Routes TODOs | 2 | Medium | 2/2 ✅ |
| Portal Routes TODOs | 2 | Low | 2/2 ✅ |
| Other TODOs | 1 | Low | 1/1 ✅ |
| **Total** | **13** | - | **13/13 (100%)** ✅ |

> **Status:** All backend implementation TODOs have been resolved as of 2025-12-18.
> See `SESSION_8_PARALLEL_PRIORITIES.md` for next improvement priorities.

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

### 6. Version History Lookup ✅ COMPLETED
**Location:** `backend/app/analytics/stability_metrics.py:222`
**Status:** COMPLETED (2025-12-18)
**Description:** Implemented schedule version history lookup using SQLAlchemy-Continuum for change tracking.
**Implementation:**
- Added `_get_previous_assignments()` method using SQLAlchemy-Continuum version_class
- Queries assignment_version table for previous transaction states
- Handles edge cases for first version and missing history
**Assignee:** Terminal 6

### 7. ACGME Validator Integration ✅ COMPLETED
**Location:** `backend/app/analytics/stability_metrics.py:520`
**Status:** COMPLETED (2025-12-18)
**Description:** Integrated stability metrics with ACGME compliance validator.
**Implementation:**
- Integrated validation into stability analysis pipeline
- Compliance checks now factor into stability scores
- Added rotation coverage and N-1 vulnerability analysis
**Assignee:** Terminal 6

### 8. Schedule Version History Query ✅ COMPLETED
**Location:** `backend/app/analytics/stability_metrics.py:544`
**Status:** COMPLETED (2025-12-18)
**Description:** Implemented historical schedule version queries for analytics.
**Implementation:**
- Query infrastructure for schedule history now in place
- Used for change detection and stability trend analysis
- Supports person-level and rotation-level granularity
**Assignee:** Terminal 6

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

### 11. Conflict Checking for Available Weeks ✅ COMPLETED
**Location:** `backend/app/api/routes/portal.py:102`
**Status:** COMPLETED (2025-12-18)
**Description:** Added conflict_alerts table query when returning available weeks.
**Implementation:**
- Query ConflictAlert table for faculty_id and fmit_week
- Filter by NEW and ACKNOWLEDGED statuses
- Set has_conflict flag and conflict_description in FMITWeekInfo response
- Integrated into portal endpoint response
**Assignee:** Terminal 2

### 12. Candidate Notifications ✅ COMPLETED
**Location:** `backend/app/api/routes/portal.py:306`
**Status:** COMPLETED (2025-12-18)
**Description:** Implemented notification system for swap candidates.
**Implementation:**
- Created SwapNotificationService with notify_marketplace_match() method
- Triggered when auto_find_candidates is enabled in swap request
- Queries FacultyPreference for candidates with notify_swap_requests enabled
- Creates notifications for all matching candidates
**Assignee:** Terminal 2

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
| #6 Version History | ✅ Completed | Terminal 6 | 2025-12-18 |
| #7 ACGME Integration | ✅ Completed | Terminal 6 | 2025-12-18 |
| #8 Schedule History Query | ✅ Completed | Terminal 6 | 2025-12-18 |
| #9 FMIT Conflict Check | ✅ Completed | Terminal 3 | 2025-12-18 |
| #10 Background Conflicts | ✅ Completed | Terminal 3 | 2025-12-18 |
| #11 Conflict Table Check | ✅ Completed | Terminal 2 | 2025-12-18 |
| #12 Candidate Notifications | ✅ Completed | Terminal 2 | 2025-12-18 |

---

## Summary

**All 13 TODOs have been successfully completed as of 2025-12-18.**

The focus now shifts to:
- Code quality improvements (type safety, query optimization)
- v1.1.0 feature preparation (email notifications, bulk import)
- Test coverage expansion
- Documentation updates

See `SESSION_9_PARALLEL_PRIORITIES.md` in the repository root for the current set of 10 parallel workstreams.

---

## Session 9 Focus Areas

| Terminal | Workstream | Status |
|----------|------------|--------|
| T1 | Strategic Direction Decisions | Pending human input |
| T2 | Email Notification Infrastructure | Ready |
| T3 | N+1 Query Elimination | Ready |
| T4 | Constraints Module Modularization | Ready |
| T5 | TypedDict Type Safety | Ready |
| T6 | MTF Compliance Type Safety | Ready |
| T7 | Hook JSDoc Documentation | Ready |
| T8 | Keyboard Navigation Expansion | Ready |
| T9 | E2E Test Coverage Expansion | Ready |
| T10 | CHANGELOG & Session Documentation | Ready |

---

*Last updated: 2025-12-18*
*Status: 100% Previous TODOs Complete, Session 9 Ready*
