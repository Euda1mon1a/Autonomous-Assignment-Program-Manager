---
name: systematic-debugger
description: Systematic debugging skill for complex issues. Use when encountering bugs, test failures, or unexpected behavior. Enforces explore-plan-debug-fix workflow to prevent premature fixes.
model_tier: opus
parallel_hints:
  can_parallel_with: [search-party, code-review]
  must_serialize_with: [automated-code-fixer]
  preferred_batch_size: 1
context_hints:
  max_file_context: 100
  compression_level: 0
  requires_git_context: true
  requires_db_context: false
escalation_triggers:
  - pattern: "security.*vulnerability"
    reason: "Security issues require security-audit skill involvement"
  - pattern: "database.*corruption"
    reason: "Data corruption requires human intervention"
  - keyword: ["ACGME", "compliance", "violation"]
    reason: "Compliance issues require domain expert review"
---

# Systematic Debugger

A methodical debugging skill that prevents jumping to fixes and ensures thorough root cause analysis.

## When This Skill Activates

- Bug reports or issue investigations
- Test failures requiring debugging
- Unexpected behavior in scheduling logic
- ACGME compliance violations
- Data inconsistencies
- Performance issues requiring investigation

## Core Philosophy: NEVER Fix First

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

## Phase 1: Exploration (NO CHANGES)

**Goal:** Understand the problem without making any modifications.

### Prompt Template
```
Read the [component] logic and examine the error context.
Don't fix anything yet, just understand the system.
```

### What to Examine
1. **Error logs and stack traces**
   ```bash
   # Check recent logs
   grep -i "error\|exception" backend/logs/*.log | tail -50
   docker-compose logs backend --tail=100
   ```

2. **Relevant source code**
   - Read the actual implementation
   - Trace data flow through the system
   - Note boundary conditions

3. **Related tests**
   ```bash
   # Tests document expected behavior
   pytest tests/[relevant]/ --collect-only
   cat tests/[relevant]/test_*.py
   ```

4. **Recent changes**
   ```bash
   git log --oneline -20 -- [relevant_path]/
   git diff HEAD~5 -- [relevant_path]/
   ```

### Exploration Questions
- What is the expected behavior?
- What is the actual behavior?
- What data/conditions trigger the issue?
- What constraints should apply?

## Phase 2: Planning with Extended Thinking

**Goal:** Form hypotheses and design a debugging approach.

### Trigger Deeper Reasoning
Use these phrases (in order of computational budget):
- `"think"` - Light analysis
- `"think hard"` - Moderate analysis
- `"think harder"` - Deep analysis
- `"ultrathink"` - Maximum reasoning

### Prompt Template
```
Think hard about what could cause [symptom].
Create a hypothesis list with root cause analysis.
Propose diagnostics for each. Don't write code yet.
```

### Hypothesis Template

| # | Hypothesis | Evidence For | Evidence Against | Test Method |
|---|------------|--------------|------------------|-------------|
| 1 | [theory] | [supporting] | [contradicting] | [validation] |
| 2 | [theory] | [supporting] | [contradicting] | [validation] |

### Ranking Criteria
- **Likelihood** - Based on evidence
- **Impact** - Severity if true
- **Testability** - Ease of validation

## Phase 3: Debugging

**Goal:** Validate hypotheses and isolate root cause.

### TDD Approach
```bash
# Write failing test first
cd backend

# Create test that reproduces the bug
cat > tests/regression/test_bug_investigation.py << 'EOF'
"""Regression test for current investigation."""
import pytest

class TestCurrentBug:
    async def test_reproduces_issue(self, db):
        """This should FAIL before fix is applied."""
        # Setup conditions
        # Execute operation
        # Assert expected (correct) behavior
        pass
EOF

# Run and confirm failure
pytest tests/regression/test_bug_investigation.py -v
```

### Strategic Logging
```python
# Add temporarily to observe runtime
import logging
logger = logging.getLogger(__name__)

logger.info(f"DEBUG INPUT: {locals()}")
logger.info(f"DEBUG RESULT: {result}")
```

### Binary Search Isolation
```
1. Comment out half the logic
2. Run test
3. Based on pass/fail, narrow down
4. Repeat until isolated
```

## Phase 4: Fix and Verify

**Goal:** Implement minimal fix with comprehensive verification.

### Fix Guidelines
- Minimal changes only
- Don't refactor unrelated code
- Don't add "improvements"
- Preserve existing behavior

### Verification Checklist
```bash
cd backend

# 1. Failing test now passes
pytest tests/regression/test_bug_investigation.py -v

# 2. Related tests pass
pytest tests/[relevant]/ -v

# 3. ACGME compliance maintained
pytest -m acgme -v

# 4. Full suite passes
pytest --cov=app -v

# 5. No linting errors
ruff check app/ tests/
```

### Commit with Context
```bash
git commit -m "$(cat <<'EOF'
fix: [issue description]

Root cause: [what caused the bug]
Fix: [what the fix does]

Adds regression test to prevent recurrence.
EOF
)"
```

## Domain-Specific Debugging

### Scheduling Issues
| Issue | Check First |
|-------|-------------|
| Double-booking | `scheduling/conflicts/` |
| ACGME violation | `services/constraints/acgme.py` |
| Rotation overlap | `scheduling/engine.py` |
| Supervision gaps | `scheduling/constraints/faculty.py` |

### Known Gotchas
| Trap | Reality |
|------|---------|
| Timezone | Scheduler runs UTC, displays HST |
| Work hours | Reset at midnight LOCAL, not UTC |
| Race conditions | Need `with_for_update()` |
| Test isolation | Check conftest fixtures |
| activity_type mismatch | `"clinic"` ≠ `"outpatient"` - check seed data for canonical values |
| Doc/code mismatch | Comments may say "outpatient" while code uses "clinic" - verify both |

### Lesson Learned: PR #442 (2025-12-26)

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

## Context Management

When debugging spans multiple sessions:

### Document & Clear
```bash
# 1. Save state
cat > debug-session-notes.md << 'EOF'
# Debug Session: [Issue]
## Symptom: [what's happening]
## Hypotheses: [ranked list]
## Tried: [what we did]
## Findings: [what we learned]
## Next: [what to do]
EOF

# 2. /clear to reset context

# 3. Resume with:
# "Read debug-session-notes.md and continue debugging"
```

## Escalation Triggers

**STOP and escalate when:**
1. Root cause unclear after 3 iterations
2. Fix requires model/migration changes
3. ACGME compliance logic affected
4. Security-sensitive code involved
5. Multiple interconnected failures

## Integration with Commands

- `/project:debug-scheduling [issue]` - Scheduling-specific workflow
- `/project:debug-tdd [bug]` - Test-driven debugging
- `/project:debug-explore [symptom]` - Pure exploration mode

## Course Correction

| Action | How |
|--------|-----|
| Interrupt | **Escape** |
| Go back | **Double-tap Escape** |
| Revert | Say: `"Undo changes"` |
| Plan first | Say: `"Make a plan first"` |

## Example Session

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

## References

- [DEBUGGING_WORKFLOW.md](../../../docs/development/DEBUGGING_WORKFLOW.md) - Full methodology
- [CI_CD_TROUBLESHOOTING.md](../../../docs/development/CI_CD_TROUBLESHOOTING.md) - CI failure patterns
