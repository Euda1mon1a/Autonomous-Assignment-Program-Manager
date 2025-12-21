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
| Experimental Benchmarks | 9 | Low | 9/9 ✅ |
| **Completed Subtotal** | **22** | - | **22/22 ✅** |
| Portal Dashboard | 1 | Medium | 0/1 ⏳ |
| MCP Server | 2 | Low | 0/2 ⏳ |
| **Grand Total** | **25** | - | **22/25 (88%)** |

> **Status:** Core backend TODOs completed. New items identified in portal and MCP server.
> - Core backend TODOs: Completed 2025-12-18 (Session 8)
> - Experimental benchmarks: Completed 2025-12-20 (Session 11)
> - New items identified: 2025-12-21

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

## Low Priority - Experimental Benchmarks (Session 11)

### 13. Memory Tracking ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/solver_comparison.py:56`
**Status:** COMPLETED (2025-12-20)
**Description:** Implemented memory tracking for solver benchmarks using tracemalloc.
**Implementation:**
- Start tracemalloc before solver execution
- Capture peak memory usage after completion
- Convert bytes to MB for reporting
**Assignee:** Session 11

### 14. Violation Counting ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/solver_comparison.py:64`
**Status:** COMPLETED (2025-12-20)
**Description:** Implemented flexible constraint violation counting from solver results.
**Implementation:**
- Check multiple attributes (violations, constraint_violations, statistics)
- Handle both list and integer violation formats
- Default to 0 for successful results
**Assignee:** Session 11

### 15. Coverage Calculation ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/solver_comparison.py:69`
**Status:** COMPLETED (2025-12-20)
**Description:** Implemented coverage score calculation with multiple fallbacks.
**Implementation:**
- Check coverage_score, coverage, statistics dict
- Calculate from assignments/total_blocks if available
- Default to 1.0 for successful results
**Assignee:** Session 11

### 16. Pathway Validation Logic ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/pathway_validation.py:46`
**Status:** COMPLETED (2025-12-20)
**Description:** Implemented complete pathway validation for scheduling optimizations.
**Implementation:**
- Validate pathway structure and state transitions
- Compare initial and final states
- Return detailed validation results
**Assignee:** Session 11

### 17. Pathway Step Counting ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/pathway_validation.py:52`
**Status:** COMPLETED (2025-12-20)
**Description:** Count pathway steps from various result structures.
**Implementation:**
- Extract from pathway.steps, pathway.transitions, dict keys, or list length
- Handle both object and dict pathway representations
**Assignee:** Session 11

### 18. Barrier Counting ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/pathway_validation.py:53`
**Status:** COMPLETED (2025-12-20)
**Description:** Count barriers bypassed during pathway optimization.
**Implementation:**
- Extract from pathway.barriers_bypassed or pathway.barriers
- Handle various result structures
**Assignee:** Session 11

### 19. Catalyst Listing ✅ COMPLETED
**Location:** `backend/experimental/benchmarks/pathway_validation.py:54`
**Status:** COMPLETED (2025-12-20)
**Description:** List catalysts used in pathway optimization.
**Implementation:**
- Extract from pathway.catalysts_used or pathway.catalysts
- Return empty list if not found
**Assignee:** Session 11

### 20. Baseline Solver Invocation ✅ COMPLETED
**Location:** `backend/experimental/harness.py:188`
**Status:** COMPLETED (2025-12-20)
**Description:** Implement baseline solver invocation for benchmarking.
**Implementation:**
- Attempt to use SolverBenchmark with mock context
- Graceful fallback on import errors
- Return baseline results for comparison
**Assignee:** Session 11

### 21. Experimental Subprocess Execution ✅ COMPLETED
**Location:** `backend/experimental/harness.py:214`
**Status:** COMPLETED (2025-12-20)
**Description:** Implement isolated subprocess execution for experimental solvers.
**Implementation:**
- Create temp directory for isolated execution
- Run solver in subprocess with JSON input/output
- Parse and return experimental results
**Assignee:** Session 11

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
| #13 Memory Tracking | ✅ Completed | Session 11 | 2025-12-20 |
| #14 Violation Counting | ✅ Completed | Session 11 | 2025-12-20 |
| #15 Coverage Calculation | ✅ Completed | Session 11 | 2025-12-20 |
| #16 Pathway Validation | ✅ Completed | Session 11 | 2025-12-20 |
| #17 Step Counting | ✅ Completed | Session 11 | 2025-12-20 |
| #18 Barrier Counting | ✅ Completed | Session 11 | 2025-12-20 |
| #19 Catalyst Listing | ✅ Completed | Session 11 | 2025-12-20 |
| #20 Baseline Solver | ✅ Completed | Session 11 | 2025-12-20 |
| #21 Subprocess Execution | ✅ Completed | Session 11 | 2025-12-20 |
| #22 Faculty Dashboard Data | ⏳ Pending | - | - |
| #23 MCP Sampling Call | ⏳ Pending | - | - |
| #24 Server Cleanup Logic | ⏳ Pending | - | - |

---

## Medium Priority - Portal Dashboard Implementation

### 22. Faculty Dashboard Data ⏳ PENDING
**Location:** `backend/app/api/routes/portal.py:863`
**Status:** PENDING
**Priority:** Medium
**Description:** The faculty dashboard endpoint currently returns stub data with zeros. Needs implementation for:
- Actual week counts from assignments
- Upcoming weeks (next 4-8 weeks)
- Recent conflict alerts (last 30 days)
- Incoming swaps requiring response

**Implementation Notes:**
- Query Assignment table for weeks_assigned/completed/remaining
- Query Block table for upcoming_weeks
- Query ConflictAlert table for recent_alerts
- Query SwapRequest table for pending_swap_decisions

---

## Low Priority - MCP Server TODOs

### 23. MCP Sampling Call ⏳ PENDING
**Location:** `mcp-server/src/scheduler_mcp/agent_server.py:263`
**Status:** PENDING
**Priority:** Low
**Description:** Replace simulated LLM response with actual MCP sampling call.

**Implementation Notes:**
- Currently uses `_simulate_llm_response()` as placeholder
- In production, should call actual LLM via MCP protocol
- Part of agent-based architecture for AI-assisted scheduling

### 24. Server Cleanup Logic ⏳ PENDING
**Location:** `mcp-server/src/scheduler_mcp/server.py:1121`
**Status:** PENDING
**Priority:** Low
**Description:** Add cleanup logic for server shutdown (close DB connections, etc.)

**Implementation Notes:**
- Called when server shuts down
- Should close database connections gracefully
- Release any held resources

---

## Summary

**22 of 25 TODOs have been completed (88%).**

Session 12 completed 20 high-yield parallel improvements:
- 10 new test files (481 tests)
- N+1 query optimization (95-99% reduction)
- TypeScript type safety (30+ `any` removed)
- Documentation consolidation
- Code quality fixes

See `docs/sessions/SESSION_12_PARALLEL_HIGH_YIELD.md` for detailed breakdown.

---

## Session 12 Focus Areas (2025-12-20) - COMPLETED

| Terminal | Workstream | Status |
|----------|------------|--------|
| T1 | People + Calendar Route Tests | ✅ Complete (116 tests) |
| T2 | Certifications + Procedures Route Tests | ✅ Complete (98 tests) |
| T3 | Leave + Absences Route Tests | ✅ Complete (78 tests) |
| T4 | Conflict Resolution + Export Route Tests | ✅ Complete (81 tests) |
| T5 | Role Views + Resilience Route Tests | ✅ Complete (108 tests) |
| T6 | Frontend JSDoc Documentation | ✅ Already Complete |
| T7 | TypeScript Type Safety Fixes | ✅ Complete (30+ any removed) |
| T8 | Documentation Consolidation | ✅ Complete (4 files moved) |
| T9 | N+1 Query Optimization | ✅ Complete (7 patterns fixed) |
| T10 | Code Quality (catch blocks, TypedDicts) | ✅ Complete |

---

## Session 13 Focus Areas (2025-12-21) - COMPLETED

**Focus:** Comprehensive Frontend Test Coverage

| Terminal | Workstream | Status |
|----------|------------|--------|
| T1 | call-roster Feature Tests | ✅ Complete (123 tests) |
| T2 | daily-manifest Feature Tests | ✅ Complete (131 tests) |
| T3 | heatmap Feature Tests | ✅ Complete (144 tests) |
| T4 | my-dashboard Feature Tests | ✅ Complete (229 tests) |
| T5 | templates Feature Tests | ✅ Complete (400+ tests) |
| T6 | Modal Component Tests | ✅ Complete (210 tests) |
| T7 | Schedule Component Tests | ✅ Complete (268 tests) |
| T8 | Calendar/List Component Tests | ✅ Complete (217 tests) |
| T9 | Resilience Hub E2E Tests | ✅ Complete (80+ tests) |
| T10 | Templates/Heatmap E2E Tests | ✅ Complete (95+ tests) |

**Summary:**
- 61 new test files created
- ~29,785 lines added
- ~1,400+ new tests
- 3 new Playwright Page Objects

See `docs/sessions/SESSION_13_FRONTEND_TEST_COVERAGE.md` for detailed breakdown.

---

*Last updated: 2025-12-21*
*Status: 88% Complete (22/25) - 3 backend items pending*
