<!--
Test-Driven Debugging workflow for reproducible bugs.
Usage: /project:debug-tdd [bug-description or issue-number]
Arguments: $ARGUMENTS
-->

# Test-Driven Debugging: $ARGUMENTS

Follow this TDD workflow for systematic bug fixing:

## Step 1: Write Failing Test FIRST

Create a test that reproduces the bug. Be explicit: **DO NOT write implementation code yet.**

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Create test file for this specific bug
# tests/regression/test_bug_[issue_number].py
```

Test template:
```python
"""Regression test for bug: $ARGUMENTS"""
import pytest
from datetime import date

# Import relevant modules based on bug type


class TestBugFix$ARGUMENTS:
    """Reproduce and verify fix for: $ARGUMENTS"""

    async def test_bug_reproduction(self, db):
        """This test should FAIL before the fix is applied."""
        # Setup: Create the exact conditions that trigger the bug

        # Action: Execute the operation that causes the bug

        # Assert: Verify the expected (correct) behavior
        # This assertion should FAIL initially
        pass

    async def test_acgme_compliance_maintained(self, db):
        """Verify ACGME compliance is not broken by the fix."""
        # Ensure fix doesn't introduce compliance violations
        pass
```

## Step 2: Confirm Test Fails

Run the test and verify it fails with the expected error:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend
pytest tests/regression/test_bug_*.py -v --tb=long
```

**STOP if test passes!** This means either:
- The bug is already fixed
- The test doesn't accurately reproduce the bug
- You need to adjust the test conditions

Document the failure:
- Error message
- Stack trace
- Relevant variable values

## Step 3: Implement Minimal Fix

Now write the code to make the test pass:

```bash
# Make targeted changes to fix the bug
# DO NOT modify the test to make it pass
# DO NOT add unrelated changes
```

Guidelines:
- Minimal changes only - fix the bug, nothing more
- Don't refactor unrelated code
- Don't add "improvements" beyond the fix
- Preserve existing behavior where not buggy

## Step 4: Verify Fix - All Green

Run the specific test:
```bash
pytest tests/regression/test_bug_*.py -v
```

If it passes, run related tests:
```bash
# Run tests for the affected module
pytest tests/scheduling/ -v  # if scheduling bug
pytest tests/services/ -v    # if service bug
pytest tests/api/ -v         # if API bug
```

Run full suite:
```bash
pytest --cov=app -v
```

## Step 5: Independent Verification (Optional but Recommended)

Use a fresh context to verify the fix:

```bash
# In a new terminal or after /clear
# Ask Claude to review the changes
```

Prompt: "Review the fix for bug $ARGUMENTS. Verify it:
1. Actually fixes the root cause
2. Doesn't overfit to the test case
3. Handles edge cases
4. Maintains ACGME compliance"

## Step 6: Commit with Traceability

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Commit the fix with the regression test
git add tests/regression/test_bug_*.py
git add [files_modified_for_fix]

git commit -m "$(cat <<'EOF'
fix: resolve $ARGUMENTS

Root cause: [explain what caused the bug]
Fix: [explain what the fix does]

Adds regression test to prevent recurrence.
EOF
)"
```

## Iteration Loop

If tests still fail after fix attempt:

1. **Analyze new failure** - Is it a different error?
2. **Refine hypothesis** - Was root cause misidentified?
3. **Add logging** - Inject diagnostics to understand runtime state
4. **Try alternative fix** - Consider different approach
5. **Return to Step 3**

Maximum 3 iterations before stepping back to reassess.

## Quick Reference: Test Commands

```bash
# Single test file
pytest tests/regression/test_bug_123.py -v

# Single test function
pytest tests/regression/test_bug_123.py::TestBugFix123::test_bug_reproduction -v

# With print statements visible
pytest -v -s

# With full traceback
pytest -v --tb=long

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# With coverage for specific module
pytest --cov=app/scheduling tests/regression/
```

## When to Escalate

If after 3 iterations the bug persists:
1. Document what was tried
2. Create `debug-session-notes.md` with findings
3. Use `/clear` and restart with fresh context
4. Consider using subagent for parallel investigation
