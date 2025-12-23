<!--
Debug scheduling conflicts and assignment issues in the residency scheduler.
Usage: /project:debug-scheduling [issue-description or assignment-id]
Arguments: $ARGUMENTS
-->

# Debug Scheduling Issue: $ARGUMENTS

Follow this systematic debugging workflow:

## Phase 1: Exploration (DO NOT FIX YET)

Read and understand the problem without making any changes:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Check recent scheduler logs for errors
grep -i "error\|conflict\|violation" /var/log/aap/scheduler.log 2>/dev/null | tail -50 || \
  grep -ir "error\|conflict\|violation" app/scheduling/ | head -30

# Review scheduling-related test failures
pytest tests/scheduling/ -v --tb=short 2>&1 | tail -100
```

Examine the relevant code:
- `backend/app/scheduling/engine.py` - Main scheduler
- `backend/app/scheduling/constraints/` - Constraint validators
- `backend/app/services/constraints/acgme.py` - ACGME rules
- `backend/app/scheduling/conflicts/` - Conflict detection

**DO NOT WRITE CODE YET.** First understand:
1. What is the expected behavior?
2. What is the actual behavior?
3. What data is involved?
4. What constraints are being violated?

## Phase 2: Planning (Think Hard)

Before proposing fixes, think hard about:
1. List 3-5 possible root causes
2. Identify which hypothesis is most likely
3. Propose diagnostic steps for each hypothesis
4. Consider edge cases (overnight shifts, cross-site rotations, leave periods)

Create a hypothesis list with reasoning.

## Phase 3: Reproduce with Tests

Write a failing test that captures the bug:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Create test in tests/scheduling/test_debug_[issue].py
# The test should fail with the exact error being investigated
pytest tests/scheduling/test_debug_*.py -v --tb=long
```

**Requirements:**
- Test must fail before the fix
- Test must use realistic fixtures from `tests/fixtures/`
- Test must validate ACGME compliance after fix

## Phase 4: Add Diagnostic Logging

Inject temporary logging to observe runtime behavior:

```python
# Add to relevant function
import logging
logger = logging.getLogger(__name__)

logger.info(f"DEBUG: Input parameters: {locals()}")
logger.info(f"DEBUG: Constraint check result: {result}")
logger.info(f"DEBUG: Assignment decision: {decision}")
```

Run and collect logs:
```bash
LOG_LEVEL=DEBUG pytest tests/scheduling/test_debug_*.py -v -s 2>&1 | tee debug_output.log
```

## Phase 5: Implement Fix

Once root cause is confirmed:
1. Implement minimal fix addressing the root cause
2. Verify fix doesn't violate ACGME compliance
3. Run all scheduling tests: `pytest tests/scheduling/ -v`
4. Remove diagnostic logging

## Phase 6: Validate & Document

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Run full test suite
pytest --cov=app/scheduling -v

# Verify ACGME compliance
pytest -m acgme -v

# Check for regressions
pytest tests/integration/ -v
```

If all tests pass:
1. Commit with descriptive message explaining the root cause and fix
2. Update CHANGELOG.md if significant

## Checkpoint Commands

Create a checkpoint before attempting risky changes:
```bash
git stash push -m "WIP: before debugging: $ARGUMENTS"
```

Restore if needed:
```bash
git stash pop
```

## Common Scheduling Issues

| Issue | Likely Cause | Key Files |
|-------|--------------|-----------|
| Double-booking | Missing overlap check | `conflicts/analyzer.py` |
| ACGME violation | Work hour miscalculation | `constraints/acgme.py` |
| Rotation overlap | Date boundary issues | `engine.py` |
| Supervision gaps | Faculty assignment logic | `constraints/faculty.py` |
| Coverage failures | Block allocation | `constraints/capacity.py` |

## Important Reminders

- **Timezone**: Scheduler runs in UTC, displays in local time
- **Work hours**: Reset at midnight LOCAL time, not UTC
- **Database**: Use `with_for_update()` to prevent race conditions
- **Never skip ACGME tests**: These are regulatory requirements
