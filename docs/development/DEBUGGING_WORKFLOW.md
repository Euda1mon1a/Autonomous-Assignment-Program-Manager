# Debugging Workflow Guide

> **Purpose:** Comprehensive debugging methodology for the Residency Scheduler with Claude Code
> **Last Updated:** 2025-12-23

---

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Systematic Debugging Workflow](#systematic-debugging-workflow)
3. [Test-Driven Debugging (TDD)](#test-driven-debugging-tdd)
4. [Advanced Techniques](#advanced-techniques)
5. [Context Management](#context-management)
6. [Domain-Specific Debugging](#domain-specific-debugging)
7. [Database Debugging](#database-debugging)
8. [Logging Strategy](#logging-strategy)
9. [Multi-Session Workflows](#multi-session-workflows)
10. [Error-Driven Development](#error-driven-development)
11. [Preventive Practices](#preventive-practices)
12. [Quick Reference](#quick-reference)

---

## Core Philosophy

### The Explore → Plan → Debug → Fix Cycle

**Never jump straight to fixing.** The most common debugging mistake is implementing a fix before understanding the problem.

```
┌─────────────────────────────────────────────────────────────┐
│                    DEBUGGING CYCLE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. EXPLORE                    2. PLAN                     │
│   ┌─────────────────┐          ┌─────────────────┐          │
│   │ Read code       │    →     │ Think hard      │          │
│   │ Check logs      │          │ List hypotheses │          │
│   │ Understand flow │          │ Rank by likely  │          │
│   │ DON'T FIX YET   │          │ Design tests    │          │
│   └─────────────────┘          └─────────────────┘          │
│          ↑                            │                     │
│          │                            ↓                     │
│   4. FIX                       3. DEBUG                     │
│   ┌─────────────────┐          ┌─────────────────┐          │
│   │ Minimal changes │    ←     │ Add logging     │          │
│   │ Run tests       │          │ Write test case │          │
│   │ Commit + doc    │          │ Reproduce       │          │
│   │ Clean up        │          │ Validate theory │          │
│   └─────────────────┘          └─────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Claude can't run your code** - YOU must execute and paste results back
2. **Exploration before intervention** - Understand before changing
3. **Tests as targets** - Write failing tests that define "fixed"
4. **Minimal fixes** - Change only what's necessary
5. **Document everything** - Future-you will thank you

---

## Systematic Debugging Workflow

### Phase 1: Exploration

**Goal:** Understand the problem without making any changes.

**Prompt Pattern:**
```
Read the [component] logic in [file] and examine the error logs from [source].
Don't fix anything yet, just understand the system.
```

**Example:**
```
Read the scheduling conflict resolution logic in backend/app/scheduling/engine.py
and examine the recent test failures. Don't fix anything yet—just understand
what the expected behavior is and what's actually happening.
```

**What to examine:**
- Relevant source code (read the actual implementation)
- Related tests (they document expected behavior)
- Error logs and stack traces
- Recent git commits to the affected area
- Related configuration

### Phase 2: Planning with Extended Thinking

**Goal:** Form hypotheses and design a debugging approach.

**Trigger Phrases (in order of computational budget):**
- `"think"` - Light analysis
- `"think hard"` - Moderate analysis
- `"think harder"` - Deep analysis
- `"ultrathink"` - Maximum reasoning

**Prompt Pattern:**
```
Think hard about what could cause [symptom]. Create a hypothesis list
with root cause analysis. Propose diagnostics for each hypothesis.
Don't write code yet.
```

**Example:**
```
Think hard about what could cause residents to be double-booked in
overlapping rotations. Create a list of 5-7 possible causes, rank them
by likelihood, and propose specific tests or checks to validate each
hypothesis. Don't write any code yet.
```

**Output should include:**
- Numbered list of hypotheses
- Evidence for/against each
- Ranking by likelihood and testability
- Specific diagnostic steps

### Phase 3: Debugging

**Goal:** Validate hypotheses and isolate root cause.

**Techniques:**
1. **Write a failing test** that reproduces the bug
2. **Add strategic logging** to observe runtime behavior
3. **Binary search** - Comment out half the code, narrow down
4. **Data inspection** - Print relevant variable values

**Prompt Pattern:**
```
Write test cases that reproduce the [bug description]. Be explicit that
we're doing TDD—don't create mock implementations. The tests should
fail with the same error users are experiencing.
```

### Phase 4: Fix and Verify

**Goal:** Implement minimal fix and verify comprehensively.

**Prompt Pattern:**
```
Implement the fix for [issue]. After each major change:
1. Verify the logic handles edge cases like [examples]
2. Run related tests
3. Check ACGME compliance is maintained
```

**Verification checklist:**
- [ ] Failing test now passes
- [ ] All related tests still pass
- [ ] Full test suite passes: `pytest`
- [ ] ACGME tests pass: `pytest -m acgme`
- [ ] No new linting errors: `ruff check .`

---

## Test-Driven Debugging (TDD)

### Step 1: Write Failing Test First

```python
"""Regression test for: [issue description]"""
import pytest
from datetime import date


class TestBugFix:
    """Reproduce and verify fix for: [issue]"""

    async def test_bug_reproduction(self, db):
        """This test should FAIL before the fix is applied."""
        # Setup: Create exact conditions that trigger the bug
        # ...

        # Action: Execute the operation that causes the bug
        # ...

        # Assert: Verify expected (correct) behavior
        # This assertion should FAIL initially
        assert actual == expected

    async def test_acgme_compliance_maintained(self, db):
        """Verify fix doesn't break ACGME compliance."""
        # Ensure fix doesn't introduce compliance violations
        pass
```

### Step 2: Confirm Test Fails

```bash
cd backend
pytest tests/regression/test_bug_*.py -v --tb=long
```

**STOP if test passes!** Either:
- Bug is already fixed
- Test doesn't accurately reproduce the bug
- Adjust test conditions

### Step 3: Implement Minimal Fix

Guidelines:
- Fix the bug, nothing more
- Don't refactor unrelated code
- Don't add "improvements"
- Preserve existing behavior where not buggy

### Step 4: Verify - All Green

```bash
# Specific test
pytest tests/regression/test_bug_*.py -v

# Related module
pytest tests/scheduling/ -v

# Full suite
pytest --cov=app -v
```

### Step 5: Commit with Traceability

```bash
git add tests/regression/test_bug_*.py
git add [files_modified]

git commit -m "$(cat <<'EOF'
fix: resolve [issue description]

Root cause: [explain what caused the bug]
Fix: [explain what the fix does]

Adds regression test to prevent recurrence.
EOF
)"
```

---

## Advanced Techniques

### Reasoning-First Strategy

Prevent premature fixes by forcing analysis:

```
List 5-7 possible causes for [symptom]. Propose diagnostics for each.
Don't write code yet.
```

### Binary Search Debugging

For complex algorithms where bug location is unclear:

```
Use binary search to isolate the bug:
1. Comment out half the constraint checking logic
2. Run the test
3. Based on pass/fail, recursively narrow to the problematic section
```

### Root Cause Analysis (5 Whys)

For systemic issues:

```
Apply the 5 Whys technique to this double-booking bug:
- Why did resident Smith get double-booked?
- Why didn't the overlap checker catch it?
- Why was the overlap checker skipped?
- Continue until you reach the root cause...
```

### Incremental Query Building

For complex SQL/database debugging:

```
Debug this assignment query step-by-step:
1. Test just the resident selection logic
2. Add the rotation join, verify results
3. Add constraint checks one at a time
4. Add date filtering
5. Combine and test full query
```

---

## Context Management

### The Document & Clear Pattern

When context gets large (check with `/context`):

**Step 1: Document Current State**
```bash
cat > debug-session-notes.md << 'EOF'
# Debug Session: [Issue Description]
## Date: YYYY-MM-DD

## Symptom
[What's happening]

## Evidence Gathered
- Logs: [summary]
- System state: [summary]
- Recent changes: [summary]

## Hypotheses
1. [Most likely] - Confidence: X%
2. [Second] - Confidence: X%
3. [Third] - Confidence: X%

## What We Tried
- [Attempt 1]: [Result]
- [Attempt 2]: [Result]

## Current Understanding
[What we now know]

## Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Files to Modify
- `backend/app/...` - [reason]

## Tests to Add
- Test for edge case A
- Test for edge case B
EOF
```

**Step 2: Clear Context**
```
/clear
```

**Step 3: Resume**
```
Read debug-session-notes.md and continue debugging from where we left off.
```

### Why Avoid `/compact`

The automatic compaction is opaque and error-prone. Manual "Document & Clear":
- Preserves exactly what you want
- Forces you to summarize understanding
- Creates a permanent record
- More reliable for resumption

---

## Domain-Specific Debugging

### Scheduling Issues

| Issue | Likely Cause | Key Files |
|-------|--------------|-----------|
| Double-booking | Missing overlap check | `scheduling/conflicts/analyzer.py` |
| ACGME violation | Work hour miscalculation | `services/constraints/acgme.py` |
| Rotation overlap | Date boundary issues | `scheduling/engine.py` |
| Supervision gaps | Faculty assignment logic | `scheduling/constraints/faculty.py` |
| Coverage failures | Block allocation | `scheduling/constraints/capacity.py` |

**Common Timezone Trap:**
```python
# WRONG: Comparing without timezone awareness
if assignment.start_date == date.today():  # Server timezone!

# RIGHT: Explicit timezone handling
from datetime import timezone
local_tz = timezone(timedelta(hours=-10))  # HST
local_today = datetime.now(local_tz).date()
if assignment.start_date == local_today:
```

### ACGME Compliance Debugging

Key validation rules:
1. **80-Hour Rule**: Max 80 hours/week, averaged over rolling 4 weeks
2. **1-in-7 Rule**: One 24-hour period off every 7 days
3. **Supervision Ratios**: PGY-1: 1:2, PGY-2/3: 1:4

```bash
# Run ACGME-specific tests
pytest -m acgme -v

# Check specific compliance validator
pytest tests/services/test_acgme_validator.py -v
```

### Swap System Debugging

```bash
# Check swap execution logs
grep -i "swap" backend/logs/*.log | tail -50

# Test swap workflow
pytest tests/integration/test_swap_workflow.py -v
```

### Resilience Framework Debugging

```bash
# Run resilience tests
pytest tests/resilience/ -v

# Check circuit breaker states
curl http://localhost:8000/api/v1/resilience/status
```

---

## Database Debugging

### Query Performance Analysis

```sql
-- Explain slow query
EXPLAIN ANALYZE SELECT * FROM assignments
WHERE person_id = 'xxx' AND block_id IN (SELECT id FROM blocks WHERE date >= '2025-01-01');
```

### Common Issues

**N+1 Query Problem:**
```python
# BAD: N+1 queries
persons = await db.execute(select(Person))
for person in persons.scalars():
    assignments = await db.execute(
        select(Assignment).where(Assignment.person_id == person.id)
    )

# GOOD: Single query with eager loading
result = await db.execute(
    select(Person).options(selectinload(Person.assignments))
)
```

**Race Condition Prevention:**
```python
# Add row locking for concurrent operations
result = await db.execute(
    select(Assignment)
    .where(Assignment.id == assignment_id)
    .with_for_update()
)
```

### Database State Inspection

```bash
# Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Useful queries
\dt                              # List tables
\d persons                       # Describe table
SELECT COUNT(*) FROM assignments;
SELECT * FROM persons WHERE role = 'RESIDENT' LIMIT 10;
```

---

## Logging Strategy

### Structured Logging for Debugging

```python
import logging
import json

logger = logging.getLogger(__name__)

def assign_rotation(resident, rotation):
    log_data = {
        "event": "rotation_assignment_attempt",
        "resident_id": resident.id,
        "rotation_id": rotation.id,
        "timestamp": datetime.utcnow().isoformat(),
        "constraints": {
            "work_hours_remaining": resident.work_hours_available,
            "rotation_capacity": rotation.available_slots
        }
    }

    try:
        result = _perform_assignment(resident, rotation)
        log_data["status"] = "success"
        log_data["assignment_id"] = result.id
        logger.info(json.dumps(log_data))
        return result
    except Exception as e:
        log_data["status"] = "failed"
        log_data["error"] = str(e)
        log_data["error_type"] = type(e).__name__
        logger.error(json.dumps(log_data), exc_info=True)
        raise
```

### Log Levels for Healthcare Systems

| Level | Use For |
|-------|---------|
| DEBUG | Detailed algorithm decisions (dev only) |
| INFO | Successful assignments, schedule generations |
| WARNING | Constraint violations caught and handled, near-limit work hours |
| ERROR | Assignment failures, validation errors |
| CRITICAL | System failures, ACGME violations, data loss |

### Temporary Diagnostic Logging

```python
# Add temporarily during debugging
import logging
logger = logging.getLogger(__name__)

def debug_function(data):
    logger.info(f"DEBUG: Input: {data}")

    result = process(data)
    logger.info(f"DEBUG: Intermediate: {result}")

    final = finalize(result)
    logger.info(f"DEBUG: Output: {final}")

    return final
```

**Remember to remove before committing!**

---

## Multi-Session Workflows

### Parallel Investigation Pattern

For complex multi-faceted bugs, use multiple terminals:

**Terminal 1** (Root cause investigation):
```
Investigate why residents are being double-booked.
Focus on the overlap detection logic.
```

**Terminal 2** (Algorithm analysis):
```
Analyze the work hour calculation logic for off-by-one errors.
Focus on boundary conditions.
```

**Terminal 3** (Regression detection):
```
Review recent commits that touched the scheduler for regressions.
Check git log and diffs.
```

Cycle through terminals, approve permissions, synthesize findings.

### Verification Pattern

Have separate Claude instances review each other's work:

1. **Claude 1**: Fix the bug
2. `/clear` or start new terminal
3. **Claude 2**: Review the fix for correctness and edge cases
4. **Claude 3**: Synthesize feedback and update code

---

## Error-Driven Development

### The Error Recovery Cycle

```
1. CAPTURE    → Document error with full context
      ↓
2. CATEGORIZE → Logic? Data? Integration? Performance?
      ↓
3. ROOT CAUSE → 5 Whys or fishbone diagram
      ↓
4. FIX        → Minimal change addressing root cause
      ↓
5. PREVENT    → Add validation, monitoring, tests
      ↓
6. IMPROVE    → Refactor to make code less brittle
```

### Error Categorization

| Category | Examples | Typical Fix |
|----------|----------|-------------|
| Logic | Wrong calculation, incorrect condition | Fix algorithm |
| Data | Invalid input, missing field | Add validation |
| Integration | API mismatch, schema change | Update interface |
| Performance | Slow query, memory leak | Optimize |
| Concurrency | Race condition, deadlock | Add locking |

---

## Preventive Practices

### Checkpoint Commits

Before risky changes:
```bash
git stash push -m "WIP: before attempting [fix description]"
```

Restore if needed:
```bash
git stash pop
```

### Defensive Assertions

Have Claude add runtime checks:
```python
# Add to validate assumptions
assert all(r.start_date is not None for r in rotations), "All rotations must have start dates"
assert work_hours >= 0, "Work hours cannot be negative"
assert assignment.person_id in valid_person_ids, "Invalid person assignment"
```

### Pre-Fix Validation

Before attempting any fix:
```
Before implementing this fix:
1. Validate all ACGME work hour limits are still enforced
2. Verify duty hour tracking remains accurate
3. Ensure audit logs capture all assignment changes
4. Test with edge cases: overnight shifts, cross-site rotations, leave periods
```

---

## Quick Reference

### Debugging Slash Commands

| Command | Purpose |
|---------|---------|
| `/project:debug-scheduling [issue]` | Debug scheduling conflicts |
| `/project:debug-tdd [bug]` | Test-driven debugging |
| `/project:debug-explore [symptom]` | Exploration-first debugging |

### Common Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html -v

# ACGME tests only
pytest -m acgme -v

# Single test file
pytest tests/scheduling/test_engine.py -v

# With print statements visible
pytest -v -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf
```

### Course Correction Tools

| Action | How |
|--------|-----|
| Interrupt | **Escape** |
| Jump back & edit | **Double-tap Escape** |
| Revert changes | Say: `"Undo changes"` |
| Stop and plan | Say: `"Make a plan first"` |

### Known Gotchas

| Issue | Cause | Solution |
|-------|-------|----------|
| Timezone mismatch | UTC vs local | Convert explicitly |
| Work hour reset | Midnight local, not UTC | Check ACGME constraints |
| Race conditions | Missing locks | Use `with_for_update()` |
| Double-booking | Missing overlap check | Check conflicts module |
| Test isolation | Stale fixtures | Verify conftest setup |

### Key Files by Domain

| Domain | Files |
|--------|-------|
| Scheduling | `scheduling/engine.py`, `scheduling/constraints/` |
| ACGME | `services/constraints/acgme.py` |
| Swaps | `services/swap_*.py` |
| Resilience | `resilience/*.py` |
| Auth | `api/routes/auth.py`, `core/security.py` |

---

*This document should be updated as new debugging patterns emerge.*
