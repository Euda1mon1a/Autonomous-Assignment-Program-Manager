<!--
Test-Driven Debugging workflow for reproducible bugs.
Usage: /project:debug-tdd [bug-description or issue-number]
Arguments: $ARGUMENTS
-->

***REMOVED*** Test-Driven Debugging: $ARGUMENTS

Follow this TDD workflow for systematic bug fixing:

***REMOVED******REMOVED*** Step 1: Write Failing Test FIRST

Create a test that reproduces the bug. Be explicit: **DO NOT write implementation code yet.**

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Create test file for this specific bug
***REMOVED*** tests/regression/test_bug_[issue_number].py
```

Test template:
```python
"""Regression test for bug: $ARGUMENTS"""
import pytest
from datetime import date

***REMOVED*** Import relevant modules based on bug type

***REMOVED*** Note: Replace [SLUG] with a valid Python identifier (e.g., issue_247, double_booking)
***REMOVED*** Create slug: echo "$ARGUMENTS" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g'

class TestBugFix_[SLUG]:
    """Reproduce and verify fix for: $ARGUMENTS"""

    async def test_bug_reproduction(self, db):
        """This test should FAIL before the fix is applied."""
        ***REMOVED*** Setup: Create the exact conditions that trigger the bug

        ***REMOVED*** Action: Execute the operation that causes the bug

        ***REMOVED*** Assert: Verify the expected (correct) behavior
        ***REMOVED*** This assertion should FAIL initially
        pass

    async def test_acgme_compliance_maintained(self, db):
        """Verify ACGME compliance is not broken by the fix."""
        ***REMOVED*** Ensure fix doesn't introduce compliance violations
        pass
```

***REMOVED******REMOVED*** Step 2: Confirm Test Fails

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

***REMOVED******REMOVED*** Step 3: Implement Minimal Fix

Now write the code to make the test pass:

```bash
***REMOVED*** Make targeted changes to fix the bug
***REMOVED*** DO NOT modify the test to make it pass
***REMOVED*** DO NOT add unrelated changes
```

Guidelines:
- Minimal changes only - fix the bug, nothing more
- Don't refactor unrelated code
- Don't add "improvements" beyond the fix
- Preserve existing behavior where not buggy

***REMOVED******REMOVED*** Step 4: Verify Fix - All Green

Run the specific test:
```bash
pytest tests/regression/test_bug_*.py -v
```

If it passes, run related tests:
```bash
***REMOVED*** Run tests for the affected module
pytest tests/scheduling/ -v  ***REMOVED*** if scheduling bug
pytest tests/services/ -v    ***REMOVED*** if service bug
pytest tests/api/ -v         ***REMOVED*** if API bug
```

Run full suite:
```bash
pytest --cov=app -v
```

***REMOVED******REMOVED*** Step 5: Independent Verification (Optional but Recommended)

Use a fresh context to verify the fix:

```bash
***REMOVED*** In a new terminal or after /clear
***REMOVED*** Ask Claude to review the changes
```

Prompt: "Review the fix for bug $ARGUMENTS. Verify it:
1. Actually fixes the root cause
2. Doesn't overfit to the test case
3. Handles edge cases
4. Maintains ACGME compliance"

***REMOVED******REMOVED*** Step 6: Commit with Traceability

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Commit the fix with the regression test
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

***REMOVED******REMOVED*** Iteration Loop

If tests still fail after fix attempt:

1. **Analyze new failure** - Is it a different error?
2. **Refine hypothesis** - Was root cause misidentified?
3. **Add logging** - Inject diagnostics to understand runtime state
4. **Try alternative fix** - Consider different approach
5. **Return to Step 3**

Maximum 3 iterations before stepping back to reassess.

***REMOVED******REMOVED*** Quick Reference: Test Commands

```bash
***REMOVED*** Single test file
pytest tests/regression/test_bug_123.py -v

***REMOVED*** Single test function
pytest tests/regression/test_bug_123.py::TestBugFix123::test_bug_reproduction -v

***REMOVED*** With print statements visible
pytest -v -s

***REMOVED*** With full traceback
pytest -v --tb=long

***REMOVED*** Stop on first failure
pytest -x

***REMOVED*** Run last failed tests only
pytest --lf

***REMOVED*** With coverage for specific module
pytest --cov=app/scheduling tests/regression/
```

***REMOVED******REMOVED*** When to Escalate

If after 3 iterations the bug persists:
1. Document what was tried
2. Create `debug-session-notes.md` with findings
3. Use `/clear` and restart with fresh context
4. Consider using subagent for parallel investigation
