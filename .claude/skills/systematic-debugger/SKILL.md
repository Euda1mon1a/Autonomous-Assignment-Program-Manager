---
name: systematic-debugger
description: Systematic debugging skill for complex issues. Use when encountering bugs, test failures, or unexpected behavior. Enforces explore-plan-debug-fix workflow to prevent premature fixes.
---

***REMOVED*** Systematic Debugger

A methodical debugging skill that prevents jumping to fixes and ensures thorough root cause analysis.

***REMOVED******REMOVED*** When This Skill Activates

- Bug reports or issue investigations
- Test failures requiring debugging
- Unexpected behavior in scheduling logic
- ACGME compliance violations
- Data inconsistencies
- Performance issues requiring investigation

***REMOVED******REMOVED*** Core Philosophy: NEVER Fix First

**CRITICAL: The most common debugging mistake is implementing a fix before understanding the problem.**

This skill enforces a strict four-phase workflow:

```
EXPLORE → PLAN → DEBUG → FIX
   ↓         ↓        ↓       ↓
 Read    Think    Test    Implement
 Observe  Hard   Reproduce  Minimal
 DON'T   Analyze  Validate  Verify
 CHANGE  Hypothesize        Commit
```

***REMOVED******REMOVED*** Phase 1: Exploration (NO CHANGES)

**Goal:** Understand the problem without making any modifications.

***REMOVED******REMOVED******REMOVED*** Prompt Template
```
Read the [component] logic and examine the error context.
Don't fix anything yet, just understand the system.
```

***REMOVED******REMOVED******REMOVED*** What to Examine
1. **Error logs and stack traces**
   ```bash
   ***REMOVED*** Check recent logs
   grep -i "error\|exception" backend/logs/*.log | tail -50
   docker-compose logs backend --tail=100
   ```

2. **Relevant source code**
   - Read the actual implementation
   - Trace data flow through the system
   - Note boundary conditions

3. **Related tests**
   ```bash
   ***REMOVED*** Tests document expected behavior
   pytest tests/[relevant]/ --collect-only
   cat tests/[relevant]/test_*.py
   ```

4. **Recent changes**
   ```bash
   git log --oneline -20 -- [relevant_path]/
   git diff HEAD~5 -- [relevant_path]/
   ```

***REMOVED******REMOVED******REMOVED*** Exploration Questions
- What is the expected behavior?
- What is the actual behavior?
- What data/conditions trigger the issue?
- What constraints should apply?

***REMOVED******REMOVED*** Phase 2: Planning with Extended Thinking

**Goal:** Form hypotheses and design a debugging approach.

***REMOVED******REMOVED******REMOVED*** Trigger Deeper Reasoning
Use these phrases (in order of computational budget):
- `"think"` - Light analysis
- `"think hard"` - Moderate analysis
- `"think harder"` - Deep analysis
- `"ultrathink"` - Maximum reasoning

***REMOVED******REMOVED******REMOVED*** Prompt Template
```
Think hard about what could cause [symptom].
Create a hypothesis list with root cause analysis.
Propose diagnostics for each. Don't write code yet.
```

***REMOVED******REMOVED******REMOVED*** Hypothesis Template

| ***REMOVED*** | Hypothesis | Evidence For | Evidence Against | Test Method |
|---|------------|--------------|------------------|-------------|
| 1 | [theory] | [supporting] | [contradicting] | [validation] |
| 2 | [theory] | [supporting] | [contradicting] | [validation] |

***REMOVED******REMOVED******REMOVED*** Ranking Criteria
- **Likelihood** - Based on evidence
- **Impact** - Severity if true
- **Testability** - Ease of validation

***REMOVED******REMOVED*** Phase 3: Debugging

**Goal:** Validate hypotheses and isolate root cause.

***REMOVED******REMOVED******REMOVED*** TDD Approach
```bash
***REMOVED*** Write failing test first
cd backend

***REMOVED*** Create test that reproduces the bug
cat > tests/regression/test_bug_investigation.py << 'EOF'
"""Regression test for current investigation."""
import pytest

class TestCurrentBug:
    async def test_reproduces_issue(self, db):
        """This should FAIL before fix is applied."""
        ***REMOVED*** Setup conditions
        ***REMOVED*** Execute operation
        ***REMOVED*** Assert expected (correct) behavior
        pass
EOF

***REMOVED*** Run and confirm failure
pytest tests/regression/test_bug_investigation.py -v
```

***REMOVED******REMOVED******REMOVED*** Strategic Logging
```python
***REMOVED*** Add temporarily to observe runtime
import logging
logger = logging.getLogger(__name__)

logger.info(f"DEBUG INPUT: {locals()}")
logger.info(f"DEBUG RESULT: {result}")
```

***REMOVED******REMOVED******REMOVED*** Binary Search Isolation
```
1. Comment out half the logic
2. Run test
3. Based on pass/fail, narrow down
4. Repeat until isolated
```

***REMOVED******REMOVED*** Phase 4: Fix and Verify

**Goal:** Implement minimal fix with comprehensive verification.

***REMOVED******REMOVED******REMOVED*** Fix Guidelines
- Minimal changes only
- Don't refactor unrelated code
- Don't add "improvements"
- Preserve existing behavior

***REMOVED******REMOVED******REMOVED*** Verification Checklist
```bash
cd backend

***REMOVED*** 1. Failing test now passes
pytest tests/regression/test_bug_investigation.py -v

***REMOVED*** 2. Related tests pass
pytest tests/[relevant]/ -v

***REMOVED*** 3. ACGME compliance maintained
pytest -m acgme -v

***REMOVED*** 4. Full suite passes
pytest --cov=app -v

***REMOVED*** 5. No linting errors
ruff check app/ tests/
```

***REMOVED******REMOVED******REMOVED*** Commit with Context
```bash
git commit -m "$(cat <<'EOF'
fix: [issue description]

Root cause: [what caused the bug]
Fix: [what the fix does]

Adds regression test to prevent recurrence.
EOF
)"
```

***REMOVED******REMOVED*** Domain-Specific Debugging

***REMOVED******REMOVED******REMOVED*** Scheduling Issues
| Issue | Check First |
|-------|-------------|
| Double-booking | `scheduling/conflicts/` |
| ACGME violation | `services/constraints/acgme.py` |
| Rotation overlap | `scheduling/engine.py` |
| Supervision gaps | `scheduling/constraints/faculty.py` |

***REMOVED******REMOVED******REMOVED*** Known Gotchas
| Trap | Reality |
|------|---------|
| Timezone | Scheduler runs UTC, displays HST |
| Work hours | Reset at midnight LOCAL, not UTC |
| Race conditions | Need `with_for_update()` |
| Test isolation | Check conftest fixtures |
| activity_type mismatch | `"clinic"` ≠ `"outpatient"` - check seed data for canonical values |
| Doc/code mismatch | Comments may say "outpatient" while code uses "clinic" - verify both |

***REMOVED******REMOVED******REMOVED*** Lesson Learned: PR ***REMOVED***442 (2025-12-26)

**Issue:** Code comment said "OUTPATIENT HALF-DAY OPTIMIZATION" but filter used `"clinic"`.

**Root cause:** The activity_type values in seed data distinguish:
- `"outpatient"` = elective/selective rotations (Neurology, ID, etc.)
- `"clinic"` = FM Clinic only (has separate capacity constraints)

**Prevention:** When fixing filters, always verify against:
1. Seed data (`scripts/seed_templates.py`)
2. Database model comments
3. BLOCK_10_ROADMAP canonical activity_type list

**Lesson:** Evaluate PRs fully before merging. This PR was caught during evaluation
and prevented a production bug where the solver would find zero templates.

***REMOVED******REMOVED*** Context Management

When debugging spans multiple sessions:

***REMOVED******REMOVED******REMOVED*** Document & Clear
```bash
***REMOVED*** 1. Save state
cat > debug-session-notes.md << 'EOF'
***REMOVED*** Debug Session: [Issue]
***REMOVED******REMOVED*** Symptom: [what's happening]
***REMOVED******REMOVED*** Hypotheses: [ranked list]
***REMOVED******REMOVED*** Tried: [what we did]
***REMOVED******REMOVED*** Findings: [what we learned]
***REMOVED******REMOVED*** Next: [what to do]
EOF

***REMOVED*** 2. /clear to reset context

***REMOVED*** 3. Resume with:
***REMOVED*** "Read debug-session-notes.md and continue debugging"
```

***REMOVED******REMOVED*** Escalation Triggers

**STOP and escalate when:**
1. Root cause unclear after 3 iterations
2. Fix requires model/migration changes
3. ACGME compliance logic affected
4. Security-sensitive code involved
5. Multiple interconnected failures

***REMOVED******REMOVED*** Integration with Commands

- `/project:debug-scheduling [issue]` - Scheduling-specific workflow
- `/project:debug-tdd [bug]` - Test-driven debugging
- `/project:debug-explore [symptom]` - Pure exploration mode

***REMOVED******REMOVED*** Course Correction

| Action | How |
|--------|-----|
| Interrupt | **Escape** |
| Go back | **Double-tap Escape** |
| Revert | Say: `"Undo changes"` |
| Plan first | Say: `"Make a plan first"` |

***REMOVED******REMOVED*** Example Session

```
User: "Residents are getting double-booked"

[Phase 1: Explore]
Claude: Let me examine the overlap detection logic without making changes...
        - Reading scheduling/conflicts/analyzer.py
        - Checking recent test failures
        - Examining error logs

[Phase 2: Plan]
Claude: Think hard about possible causes:
        1. Date boundary issue (70% likely) - Test with overnight rotation
        2. Missing overlap check (20% likely) - Review validator
        3. Race condition (10% likely) - Check locking

[Phase 3: Debug]
Claude: Writing failing test to reproduce...
        - Test created, confirmed failure
        - Adding logging to observe date handling
        - Root cause: exclusive vs inclusive end date comparison

[Phase 4: Fix]
Claude: Implementing fix for date comparison...
        - Changed `<` to `<=` for end date
        - All tests pass including regression test
        - ACGME tests pass
        - Committing with explanation
```

***REMOVED******REMOVED*** References

- [DEBUGGING_WORKFLOW.md](../../../docs/development/DEBUGGING_WORKFLOW.md) - Full methodology
- [CI_CD_TROUBLESHOOTING.md](../../../docs/development/CI_CD_TROUBLESHOOTING.md) - CI failure patterns
