# Test Frame to Implementation Mapping

Quick reference showing how TEST_SCENARIO_FRAMES.md Section 5 maps to actual test implementations.

---

## Frame 5.1: Two Users Editing Same Assignment

**Source:** TEST_SCENARIO_FRAMES.md lines 1030-1093

**Implementations:**

### ✅ test_concurrent_assignment_edit_with_separate_sessions
- **File:** test_concurrent_operations.py:145
- **Scenario:** User A and User B edit assignment simultaneously
- **Pattern:** Separate sessions, threading
- **Assertions:**
  - Both operations complete
  - Database state is consistent
  - No exceptions raised

### ✅ test_concurrent_edit_with_explicit_locking
- **File:** test_concurrent_operations.py:235
- **Scenario:** Concurrent edits with SELECT ... FOR UPDATE
- **Pattern:** Pessimistic locking with `with_for_update()`
- **Assertions:**
  - Locks acquired sequentially
  - Update order tracked
  - No lost updates

---

## Frame 5.2: Swap Request During Schedule Generation

**Source:** TEST_SCENARIO_FRAMES.md lines 1095-1160

**Implementation:**

### ✅ test_swap_during_schedule_generation
- **File:** test_concurrent_operations.py:300
- **Scenario:** Swap submitted while optimizer generates next block
- **Pattern:** Background task + threading events
- **Assertions:**
  - Swap request created
  - Status is PENDING
  - Generation completes successfully
  - No database corruption

---

## Frame 5.3: Task Cancellation Mid-Execution

**Source:** TEST_SCENARIO_FRAMES.md lines 1162-1231

**Implementations:**

### ✅ test_task_cancellation_mid_execution
- **File:** test_concurrent_operations.py:377
- **Scenario:** Long-running task cancelled by user
- **Pattern:** Cancellation flag + rollback
- **Assertions:**
  - Task stops early (< 10 iterations)
  - Cleanup performed
  - Database rolled back

### ✅ test_task_cancellation_with_asyncio
- **File:** test_concurrent_operations.py:423
- **Scenario:** Async task handles CancelledError
- **Pattern:** asyncio.create_task() + task.cancel()
- **Assertions:**
  - Task cancelled mid-execution
  - CancelledError raised
  - Cleanup callback invoked

---

## Frame 5.4: Race Condition in Swap Auto-Matcher

**Source:** TEST_SCENARIO_FRAMES.md lines 1233-1322

**Implementations:**

### ✅ test_swap_race_condition_two_faculty_want_same_shift
- **File:** test_concurrent_operations.py:457
- **Scenario:** Faculty A and C both want to swap with Faculty B
- **Pattern:** Concurrent swap creation
- **Assertions:**
  - Both swap requests created
  - Status tracked per thread
  - Database consistent

### ✅ test_swap_auto_matcher_prevents_double_booking
- **File:** test_concurrent_operations.py:567
- **Scenario:** Prevent double-booking with locks
- **Pattern:** Row-level locking
- **Assertions:**
  - First swap succeeds
  - Second waits or fails gracefully
  - No double-booking

---

## Additional Test Coverage (Beyond Frames)

### test_concurrent_read_during_write
- **File:** test_concurrent_operations.py:652
- **Purpose:** Transaction isolation verification
- **Pattern:** Concurrent read/write

### test_deadlock_prevention
- **File:** test_concurrent_operations.py:694
- **Purpose:** Prevent deadlocks via lock ordering
- **Pattern:** Consistent resource locking

---

## Quick Test Execution

```bash
# Frame 5.1 tests
pytest tests/integration/test_concurrent_operations.py::TestConcurrentAssignmentEdit -v

# Frame 5.2 tests
pytest tests/integration/test_concurrent_operations.py::TestSwapDuringGeneration -v

# Frame 5.3 tests
pytest tests/integration/test_concurrent_operations.py::TestTaskCancellation -v

# Frame 5.4 tests
pytest tests/integration/test_concurrent_operations.py::TestSwapRaceCondition -v

# All frames
pytest tests/integration/test_concurrent_operations.py -v
```

---

## Test Class Organization

| Frame | Test Class | Test Count |
|-------|-----------|------------|
| 5.1 | `TestConcurrentAssignmentEdit` | 2 |
| 5.2 | `TestSwapDuringGeneration` | 1 |
| 5.3 | `TestTaskCancellation` | 2 |
| 5.4 | `TestSwapRaceCondition` | 2 |
| Extra | `TestConcurrentEdgeCases` | 2 |
| **Total** | **5 classes** | **9 tests** |

---

## Coverage Status

| Frame ID | Required Tests | Implemented | Status |
|----------|---------------|-------------|--------|
| Frame 5.1 | ≥1 | 2 | ✅ Complete |
| Frame 5.2 | ≥1 | 1 | ✅ Complete |
| Frame 5.3 | ≥1 | 2 | ✅ Complete |
| Frame 5.4 | ≥1 | 2 | ✅ Complete |

**Overall:** ✅ 100% Coverage (4/4 frames implemented)

---

**Last Updated:** 2025-12-26
