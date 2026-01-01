---
name: pr-reviewer
description: Pull request review expertise with focus on context, quality gates, and team standards. Use when reviewing PRs, validating changes before merge, or generating PR descriptions. Works with gh CLI for GitHub integration.
model_tier: opus
parallel_hints:
  can_parallel_with:
    - code-review
    - security-audit
  must_serialize_with:
    - database-migration
  preferred_batch_size: 3
---

***REMOVED*** PR Reviewer Skill

Comprehensive pull request review skill that validates changes against project standards, runs quality gates, and provides structured feedback for merge decisions.

***REMOVED******REMOVED*** When This Skill Activates

- Reviewing open pull requests
- Creating PR descriptions
- Validating changes before merge
- Checking CI/CD status
- Generating review summaries
- Approving or requesting changes

***REMOVED******REMOVED*** PR Review Workflow

***REMOVED******REMOVED******REMOVED*** Step 1: Gather Context

```bash
***REMOVED*** Get PR details
gh pr view <PR_NUMBER> --json title,body,author,state,reviews,files,commits

***REMOVED*** View the diff
gh pr diff <PR_NUMBER>

***REMOVED*** Check CI status
gh pr checks <PR_NUMBER>

***REMOVED*** Get commits
gh pr view <PR_NUMBER> --json commits

***REMOVED*** List changed files
gh pr diff <PR_NUMBER> --name-only
```

***REMOVED******REMOVED******REMOVED*** Step 2: Understand the Change

Questions to answer:
- What problem does this PR solve?
- What is the approach taken?
- What are the key changes?
- What might break?
- What tests were added?

***REMOVED******REMOVED******REMOVED*** Step 3: Run Quality Gates

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Fetch and checkout PR
git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
git checkout pr-<PR_NUMBER>

***REMOVED*** Run quality checks
pytest --tb=short -q
ruff check app/ tests/
black --check app/ tests/
mypy app/ --python-version 3.11

***REMOVED*** Check test coverage
pytest --cov=app --cov-fail-under=70
```

***REMOVED******REMOVED******REMOVED*** Step 4: Review Categories

***REMOVED******REMOVED******REMOVED******REMOVED*** A. Code Quality
- [ ] Code follows layered architecture
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] No magic numbers/hardcoded values
- [ ] DRY principle followed
- [ ] Appropriate error handling

***REMOVED******REMOVED******REMOVED******REMOVED*** B. Testing
- [ ] Tests added for new code
- [ ] Tests cover edge cases
- [ ] Tests are readable and maintainable
- [ ] Coverage >= 70%
- [ ] No flaky tests

***REMOVED******REMOVED******REMOVED******REMOVED*** C. Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Auth checks in place
- [ ] No sensitive data in logs/errors
- [ ] SQL injection prevention

***REMOVED******REMOVED******REMOVED******REMOVED*** D. Architecture
- [ ] Follows project patterns
- [ ] Database changes have migrations
- [ ] Async/await used correctly
- [ ] Pydantic schemas for I/O
- [ ] No circular dependencies

***REMOVED******REMOVED******REMOVED******REMOVED*** E. Documentation
- [ ] PR description is clear
- [ ] Complex logic commented
- [ ] API docs updated if needed
- [ ] CHANGELOG updated for features
- [ ] **Code/comment consistency** - verify comments match actual behavior
- [ ] **Seed data alignment** - filter values match canonical data sources

***REMOVED******REMOVED*** Review Decision Matrix

| Gate | Pass | Block |
|------|------|-------|
| Tests | All pass | Any failure |
| Linting | 0 errors | Any error |
| Types | 0 errors | Critical types missing |
| Security | No issues | Any vulnerability |
| Coverage | >= 70% | < 60% |
| Architecture | Follows patterns | Major violation |

***REMOVED******REMOVED*** PR Feedback Format

***REMOVED******REMOVED******REMOVED*** Inline Comments

Use GitHub's suggestion format for fixes:

````markdown
```suggestion
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```
````

***REMOVED******REMOVED******REMOVED*** Review Summary

```markdown
***REMOVED******REMOVED*** Review Summary

**Decision:** APPROVE / REQUEST CHANGES / COMMENT

***REMOVED******REMOVED******REMOVED*** What This PR Does
[One sentence summary]

***REMOVED******REMOVED******REMOVED*** Quality Gate Results
| Gate | Status | Notes |
|------|--------|-------|
| Tests | :white_check_mark: | 47 passed |
| Linting | :white_check_mark: | 0 errors |
| Types | :white_check_mark: | 100% coverage |
| Security | :white_check_mark: | bandit clear |
| Coverage | :yellow_circle: | 72% (target 80%) |

***REMOVED******REMOVED******REMOVED*** Changes Reviewed
- `app/services/new_feature.py` - New service implementation
- `tests/test_new_feature.py` - Test coverage

***REMOVED******REMOVED******REMOVED*** Feedback

***REMOVED******REMOVED******REMOVED******REMOVED*** Required Changes (Blocking)
1. [file:line] - Description of issue
   - Impact: [what could go wrong]
   - Suggestion: [how to fix]

***REMOVED******REMOVED******REMOVED******REMOVED*** Suggestions (Non-blocking)
1. [file:line] - Description
   - Recommendation: [improvement]

***REMOVED******REMOVED******REMOVED******REMOVED*** Questions
1. [Question about the approach]

***REMOVED******REMOVED******REMOVED*** Testing Notes
Tested locally:
- [x] Unit tests pass
- [x] Integration tests pass
- [ ] Manual testing [describe if done]

***REMOVED******REMOVED******REMOVED*** Merge Checklist
- [ ] All conversations resolved
- [ ] CI checks passing
- [ ] Required reviews obtained
- [ ] Documentation updated
```

***REMOVED******REMOVED*** PR Description Template

When creating PRs:

```markdown
***REMOVED******REMOVED*** Summary
[1-3 bullet points describing the change]

***REMOVED******REMOVED*** Motivation
[Why this change is needed]

***REMOVED******REMOVED*** Changes
- [List key changes]

***REMOVED******REMOVED*** Testing
- [How was this tested?]

***REMOVED******REMOVED*** Test Plan
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing done

***REMOVED******REMOVED*** Screenshots
[If applicable]

***REMOVED******REMOVED*** Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

***REMOVED******REMOVED*** Related Issues
Closes ***REMOVED***[issue number]
```

***REMOVED******REMOVED*** GitHub CLI Commands

```bash
***REMOVED*** List open PRs
gh pr list

***REMOVED*** View specific PR
gh pr view <number>

***REMOVED*** Check PR status
gh pr checks <number>

***REMOVED*** Review PR
gh pr review <number> --approve -b "Looks good!"
gh pr review <number> --request-changes -b "See comments"
gh pr review <number> --comment -b "Questions inline"

***REMOVED*** Add comment
gh pr comment <number> --body "Comment text"

***REMOVED*** Merge PR
gh pr merge <number> --squash --delete-branch

***REMOVED*** Get PR diff
gh pr diff <number>

***REMOVED*** Create PR
gh pr create --title "Title" --body "Description"
```

***REMOVED******REMOVED*** Automated PR Checks

***REMOVED******REMOVED******REMOVED*** Pre-Review Automation

```bash
***REMOVED***!/bin/bash
***REMOVED*** scripts/pr-review-prep.sh

PR_NUMBER=$1

***REMOVED*** Fetch PR
git fetch origin pull/${PR_NUMBER}/head:pr-${PR_NUMBER}
git checkout pr-${PR_NUMBER}

***REMOVED*** Run quality checks
echo "=== Running Tests ==="
pytest --tb=short -q

echo "=== Running Linting ==="
ruff check app/ tests/

echo "=== Running Type Check ==="
mypy app/ --python-version 3.11

echo "=== Coverage Report ==="
pytest --cov=app --cov-report=term-missing --cov-fail-under=70

echo "=== Security Scan ==="
bandit -r app/ -ll

echo "=== PR Review Prep Complete ==="
```

***REMOVED******REMOVED*** Common Review Patterns

***REMOVED******REMOVED******REMOVED*** Missing Tests

```markdown
This new functionality needs test coverage.

**Files needing tests:**
- `app/services/new_service.py`

**Suggested test cases:**
1. Happy path - normal input
2. Edge case - empty input
3. Error case - invalid input
4. Integration - database operations
```

***REMOVED******REMOVED******REMOVED*** Architecture Violation

```markdown
This violates the layered architecture pattern.

**Issue:** Business logic in route handler

**Current:**
```python
@router.post("/items")
async def create_item(data: ItemCreate, db: Session):
    ***REMOVED*** Business logic here (violation)
    if data.value > 100:
        data.value = 100
    item = Item(**data.dict())
    db.add(item)
```

**Should be:**
```python
***REMOVED*** In service layer
async def create_item(db: Session, data: ItemCreate) -> Item:
    if data.value > 100:
        data.value = 100
    item = Item(**data.dict())
    db.add(item)
    return item

***REMOVED*** In route
@router.post("/items")
async def create_item_route(data: ItemCreate, db: Session):
    return await create_item(db, data)
```
```

***REMOVED******REMOVED******REMOVED*** Missing Type Hints

````markdown
Please add type hints to these functions:

```suggestion
async def get_schedule(
    db: AsyncSession,
    schedule_id: str
) -> Optional[Schedule]:
    """Retrieve a schedule by ID."""
    ...
```
````

***REMOVED******REMOVED*** Lesson Learned: PR ***REMOVED***442 (2025-12-26)

**What happened:** A fix changed a filter from one value to another, but the new value
was also incorrect because comments/docs said "outpatient" while code used "clinic".

**Prevention checklist for filter/constant changes:**
- [ ] Verify value against seed data (`scripts/seed_templates.py`)
- [ ] Check if comments describe different behavior than code implements
- [ ] Cross-reference with canonical data source (e.g., BLOCK_10_ROADMAP)
- [ ] Confirm the filter will actually find matching records

**Key insight:** Always ask "will this filter find what we expect?" and verify empirically.

***REMOVED******REMOVED*** Escalation Rules

**Request human review when:**

1. Changes touch authentication/authorization
2. Database migrations involved
3. ACGME compliance logic affected
4. Breaking API changes
5. Complex business logic unclear
6. Performance-critical code
7. Third-party integration changes
8. **Filter/constant value changes** - verify against canonical data sources

**Can approve automatically:**

1. Documentation-only changes
2. Test additions (without code changes)
3. Dependency updates (minor versions)
4. Code formatting fixes
5. Comment improvements

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With code-review
For detailed code analysis:
1. PR-reviewer handles workflow and gates
2. Code-review handles line-by-line analysis
3. Combine findings in final review

***REMOVED******REMOVED******REMOVED*** With security-audit
For security-sensitive PRs:
1. Detect sensitive file changes
2. Trigger security-audit skill
3. Include security findings in review

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer
For simple fixes:
1. Suggest fixes inline
2. If accepted, automated-code-fixer applies
3. Re-run quality gates
4. Update PR status

***REMOVED******REMOVED*** Workflow Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                   PR REVIEW WORKFLOW                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STEP 1: Gather Context                                           │
│  ┌──────────────────────────────────────────────────┐             │
│  │ gh pr view <number> --json ...                   │             │
│  │ gh pr diff <number>                              │             │
│  │ gh pr checks <number>                            │             │
│  │ Understand: What, Why, How                       │             │
│  └──────────────────────────────────────────────────┘             │
│                         ↓                                         │
│  STEP 2: Checkout and Test Locally                                │
│  ┌──────────────────────────────────────────────────┐             │
│  │ git fetch origin pull/<N>/head:pr-<N>            │             │
│  │ git checkout pr-<N>                              │             │
│  │ Run tests, linting, type checks                  │             │
│  └──────────────────────────────────────────────────┘             │
│                         ↓                                         │
│  STEP 3: Quality Gate Checks                                      │
│  ┌──────────────────────────────────────────────────┐             │
│  │ Tests: ALL PASS?                                 │             │
│  │ Linting: 0 errors?                               │             │
│  │ Types: No critical issues?                       │             │
│  │ Security: No vulnerabilities?                    │             │
│  │ Coverage: >= 70%?                                │             │
│  └──────────────────────────────────────────────────┘             │
│                         ↓                                         │
│  STEP 4: Code Review Categories                                   │
│  ┌──────────────────────────────────────────────────┐             │
│  │ A. Code Quality  B. Testing                      │             │
│  │ C. Security      D. Architecture                 │             │
│  │ E. Documentation                                 │             │
│  └──────────────────────────────────────────────────┘             │
│                         ↓                                         │
│  STEP 5: Make Decision                                            │
│  ┌──────────────────────────────────────────────────┐             │
│  │ All gates PASS → APPROVE                         │             │
│  │ Major issues   → REQUEST CHANGES                 │             │
│  │ Questions only → COMMENT                         │             │
│  └──────────────────────────────────────────────────┘             │
│                         ↓                                         │
│  STEP 6: Post Review                                              │
│  ┌──────────────────────────────────────────────────┐             │
│  │ gh pr review <number> --approve/--request-changes│             │
│  │ Include summary, gate results, feedback          │             │
│  └──────────────────────────────────────────────────┘             │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED*** Concrete Usage Example: Reviewing PR ***REMOVED***123

**Scenario:** Review PR that adds a new ACGME constraint for call spacing.

***REMOVED******REMOVED******REMOVED*** Complete Review Walkthrough

**Step 1: Gather Context**

```bash
***REMOVED*** View PR details
gh pr view 123 --json title,body,author,state,reviews,files,commits

***REMOVED*** Output:
***REMOVED*** {
***REMOVED***   "title": "feat: add minimum call spacing constraint",
***REMOVED***   "author": "developer",
***REMOVED***   "state": "OPEN",
***REMOVED***   "body": "Adds 72-hour minimum spacing between call shifts..."
***REMOVED***   "files": [
***REMOVED***     "backend/app/scheduling/constraints/call_spacing.py",
***REMOVED***     "backend/app/scheduling/constraints/__init__.py",
***REMOVED***     "backend/app/scheduling/constraints/manager.py",
***REMOVED***     "backend/tests/test_call_spacing_constraint.py"
***REMOVED***   ]
***REMOVED*** }

***REMOVED*** View the diff
gh pr diff 123 > pr123.diff

***REMOVED*** Check CI status
gh pr checks 123

***REMOVED*** Output:
***REMOVED*** ✓ Backend Tests   passed
***REMOVED*** ✓ Frontend Tests  passed
***REMOVED*** ✓ Lint Check      passed
***REMOVED*** ✗ Type Check      failed
```

**Analysis:**
- What: New constraint for call spacing
- Why: ACGME requirement for resident wellbeing
- How: Soft constraint with weight 8.0
- Issue: Type check failing ⚠️

**Step 2: Checkout and Test Locally**

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Fetch PR
git fetch origin pull/123/head:pr-123
git checkout pr-123

***REMOVED*** Run quality checks
cd backend

***REMOVED*** Tests
pytest
***REMOVED*** Output: 47 passed, 0 failed ✓

***REMOVED*** Linting
ruff check app/ tests/
***REMOVED*** Output: All clear ✓

***REMOVED*** Type check (this was failing in CI)
mypy app/ --python-version 3.11
***REMOVED*** Output:
***REMOVED*** app/scheduling/constraints/call_spacing.py:45: error: Incompatible return type
***REMOVED*** Expected "ConstraintResult", got "None"
```

**Found the issue!** Type check fails because `validate()` method doesn't return value in all code paths.

**Step 3: Quality Gate Results**

| Gate | Status | Notes |
|------|--------|-------|
| Tests | :white_check_mark: PASS | 47 passed |
| Linting | :white_check_mark: PASS | 0 errors |
| Types | :x: FAIL | Missing return in validate() |
| Security | :white_check_mark: PASS | No issues |
| Coverage | :white_check_mark: PASS | 85% (target 70%) |
| Architecture | :warning: NEEDS REVIEW | Constraint pattern followed |

**Decision:** REQUEST CHANGES (type error is blocking)

**Step 4: Code Review by Category**

**A. Code Quality**
```python
***REMOVED*** ❌ Issue found in call_spacing.py line 45
def validate(self, assignments, context):
    violations = []
    for person_id, person_assignments in group_by_person(assignments):
        ***REMOVED*** ... logic ...
        if spacing < self.min_hours:
            violations.append(...)
    ***REMOVED*** ❌ MISSING: return ConstraintResult(violations)
```

**Suggestion:**
```python
def validate(self, assignments, context) -> ConstraintResult:
    violations = []
    for person_id, person_assignments in group_by_person(assignments):
        ***REMOVED*** ... logic ...
        if spacing < self.min_hours:
            violations.append(...)
    ***REMOVED*** ✓ FIX: Add return statement
    return ConstraintResult(
        passed=len(violations) == 0,
        violations=violations,
        score=1.0 - (len(violations) * 0.1)
    )
```

**B. Testing**
- :white_check_mark: Unit tests added
- :white_check_mark: Registration test included
- :white_check_mark: Edge cases covered (24-hour call, overnight)
- :warning: Suggested: Add integration test with scheduler

**C. Security**
- :white_check_mark: No sensitive data in logs
- :white_check_mark: Input validation present
- :white_check_mark: No SQL injection risk

**D. Architecture**
- :white_check_mark: Follows SoftConstraint base class
- :white_check_mark: Exported in __init__.py
- :white_check_mark: Registered in manager.py
- :white_check_mark: Weight (8.0) positioned correctly in hierarchy

**E. Documentation**
- :white_check_mark: Docstring explains constraint purpose
- :white_check_mark: Clinical rationale documented
- :white_check_mark: ACGME rule cited
- :warning: Suggested: Add example to docstring

**Step 5: Generate Review Summary**

```markdown
***REMOVED******REMOVED*** Review Summary

**Decision:** REQUEST CHANGES

***REMOVED******REMOVED******REMOVED*** What This PR Does
Adds CallSpacingConstraint to enforce 72-hour minimum spacing between
inpatient call shifts, implementing ACGME burnout prevention guidelines.

***REMOVED******REMOVED******REMOVED*** Quality Gate Results
| Gate | Status | Notes |
|------|--------|-------|
| Tests | :white_check_mark: | 47 passed |
| Linting | :white_check_mark: | 0 errors |
| Types | :x: | **BLOCKING**: Missing return in validate() |
| Security | :white_check_mark: | bandit clear |
| Coverage | :white_check_mark: | 85% (target 70%) |

***REMOVED******REMOVED******REMOVED*** Changes Reviewed
- `app/scheduling/constraints/call_spacing.py` - New constraint implementation
- `app/scheduling/constraints/manager.py` - Registration (verified)
- `tests/test_call_spacing_constraint.py` - Test coverage

***REMOVED******REMOVED******REMOVED*** Required Changes (Blocking)

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. [call_spacing.py:45] Missing return statement
**Impact:** Type check fails, method returns None instead of ConstraintResult

**Fix:**
```python
def validate(self, assignments, context) -> ConstraintResult:
    violations = []
    ***REMOVED*** ... validation logic ...
    return ConstraintResult(  ***REMOVED*** ← Add this
        passed=len(violations) == 0,
        violations=violations,
        score=1.0 - (len(violations) * 0.1)
    )
```

***REMOVED******REMOVED******REMOVED*** Suggestions (Non-blocking)

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Add integration test with scheduler
Suggested test:
```python
async def test_call_spacing_integration_with_scheduler(db):
    """Test call spacing is enforced during schedule generation."""
    ***REMOVED*** Generate schedule, verify no call shifts within 72 hours
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Add concrete example to docstring
```python
class CallSpacingConstraint(SoftConstraint):
    """
    Enforce minimum spacing between call shifts.

    Example:
        If resident has call Monday 5pm-Tuesday 5pm (24 hours),
        they cannot take another call until Thursday 5pm (72 hours later).
    """
```

***REMOVED******REMOVED******REMOVED*** Testing Notes
Tested locally:
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual verification: weight hierarchy correct

***REMOVED******REMOVED******REMOVED*** Merge Checklist
- [ ] Fix type error in validate()
- [ ] Type check passes (`mypy app/`)
- [ ] Re-run CI checks
- [ ] Address suggestions (optional)
```

**Step 6: Post Review**

```bash
***REMOVED*** Post review with feedback
gh pr review 123 --request-changes --body "$(cat <<'EOF'
***REMOVED******REMOVED*** Review Summary

**Decision:** REQUEST CHANGES

[... full review summary from above ...]

EOF
)"

***REMOVED*** Add inline comment on specific line
gh api repos/{owner}/{repo}/pulls/123/comments \
  -f body="Missing return statement here. See main review for fix." \
  -f commit_id="abc123" \
  -f path="backend/app/scheduling/constraints/call_spacing.py" \
  -f position=45
```

**Follow-up after fixes applied:**

```bash
***REMOVED*** Author pushes fix
***REMOVED*** Re-check the PR

gh pr checks 123
***REMOVED*** Output: All checks passing ✓

***REMOVED*** Re-review
gh pr review 123 --approve --body "$(cat <<'EOF'
***REMOVED******REMOVED*** Re-Review Summary

**Decision:** APPROVE ✓

***REMOVED******REMOVED******REMOVED*** Changes Verified
- ✓ Type error fixed - validate() now returns ConstraintResult
- ✓ All CI checks passing
- ✓ Type check passes

Ready to merge!
EOF
)"
```

***REMOVED******REMOVED*** Failure Mode Handling

***REMOVED******REMOVED******REMOVED*** Failure Mode 1: CI Checks Failing

**Symptom:**
```bash
$ gh pr checks 123

✗ Backend Tests   failed
✗ Type Check      failed
✓ Lint Check      passed
```

**Recovery:**

```bash
***REMOVED*** 1. Checkout PR locally
git fetch origin pull/123/head:pr-123
git checkout pr-123

***REMOVED*** 2. Run tests to see failures
cd backend
pytest -v

***REMOVED*** Output shows which tests failed

***REMOVED*** 3. Request changes with specific test failures
gh pr review 123 --request-changes --body "$(cat <<'EOF'
CI checks are failing. Please fix before re-review:

**Failed Tests:**
- test_call_spacing_overnight - AssertionError on line 45
- test_call_spacing_edge_case - Expected 2 violations, got 0

**Type Errors:**
- call_spacing.py:45 - Missing return type

Please address these issues and push updates.
EOF
)"
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 2: PR Changes Core Security Code

**Symptom:** PR modifies `backend/app/core/security.py`

**Recovery:**

```bash
***REMOVED*** 1. Immediately invoke security-audit skill
***REMOVED*** (Don't approve without security review)

***REMOVED*** 2. Flag for human review
gh pr comment 123 --body "$(cat <<'EOF'
⚠️ **SECURITY REVIEW REQUIRED**

This PR modifies core security code (`core/security.py`).
Flagging for human security review before approval.

@security-team please review authentication changes.
EOF
)"

***REMOVED*** 3. Mark as REQUEST CHANGES until security cleared
gh pr review 123 --request-changes --body "$(cat <<'EOF'
Holding for security review. See comment above.

Changes to security code require human approval.
EOF
)"
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 3: Database Migration Without Testing

**Symptom:** PR includes Alembic migration but no evidence of upgrade/downgrade testing

**Recovery:**

```bash
***REMOVED*** 1. Verify migration testing in PR description or commits
gh pr view 123 --json body | grep -i "alembic\|migration\|upgrade\|downgrade"

***REMOVED*** If no evidence found:

***REMOVED*** 2. Request testing evidence
gh pr review 123 --request-changes --body "$(cat <<'EOF'
⚠️ **Database Migration Detected**

This PR includes a database migration but doesn't show testing evidence.

**Required before approval:**
- [ ] Demonstrate `alembic upgrade head` succeeds
- [ ] Demonstrate `alembic downgrade -1` succeeds
- [ ] Demonstrate `alembic upgrade head` succeeds again
- [ ] Verify application starts with new schema
- [ ] Verify all tests pass

Please add this evidence to PR description or commit message.
EOF
)"
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 4: Coverage Drop Below Threshold

**Symptom:**
```bash
$ pytest --cov=app --cov-fail-under=70

FAILED: Coverage 65% is below threshold 70%
```

**Recovery:**

```bash
***REMOVED*** 1. Identify uncovered code
pytest --cov=app --cov-report=html
***REMOVED*** Open htmlcov/index.html

***REMOVED*** 2. Request additional tests
gh pr review 123 --request-changes --body "$(cat <<'EOF'
Test coverage dropped to 65% (below 70% threshold).

**Uncovered code:**
- `call_spacing.py` lines 45-52 (edge case handling)
- `call_spacing.py` lines 78-82 (error handling)

Please add tests for these code paths.
EOF
)"
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 5: Unclear PR Purpose

**Symptom:** PR description says "fixes stuff" with no details

**Recovery:**

```bash
***REMOVED*** Request clarification before reviewing
gh pr comment 123 --body "$(cat <<'EOF'
Could you please provide more context in the PR description?

**Helpful information:**
- What problem does this solve?
- What approach did you take?
- How was it tested?
- Are there any breaking changes?

This helps with review and serves as documentation for future reference.
EOF
)"

***REMOVED*** Don't approve until description is clear
```

***REMOVED******REMOVED*** Integration Examples (Extended)

***REMOVED******REMOVED******REMOVED*** With code-review (Detailed)

```
[PR ***REMOVED***123 opened]
[pr-reviewer activated]

Step 1: pr-reviewer gathers context
→ Identifies 4 files changed
→ Detects new constraint code

Step 2: Invoke code-review for line-by-line analysis
→ code-review examines call_spacing.py
→ Finds: Missing return statement, unclear variable name, missing type hint

Step 3: pr-reviewer synthesizes findings
→ Combines code-review findings with quality gates
→ Generates unified review with inline suggestions

Step 4: Post review
→ gh pr review 123 --request-changes
→ Includes both structural issues (gates) and code quality issues (code-review)
```

***REMOVED******REMOVED******REMOVED*** With security-audit (Detailed)

```
[PR ***REMOVED***456 modifies auth logic]
[pr-reviewer activated]

→ Detects security-sensitive file: backend/app/api/routes/auth.py
→ STOP: Do not auto-approve

[Invoke security-audit skill]
→ Checks for: password handling, token generation, SQL injection, XSS
→ Finds: Hardcoded secret key in test (violation)

[pr-reviewer includes security findings]
Review:
"🔒 Security Review Required

security-audit found:
- Hardcoded secret 'test123' in test_auth.py line 45
- Missing rate limiting on new endpoint
- No input validation on email parameter

These must be addressed before approval."
```

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer (Detailed)

```
[PR ***REMOVED***789 has simple linting errors]
[pr-reviewer activated]

→ Runs quality gates
→ Linting: 5 errors (missing imports, unused variables, formatting)

Instead of requesting changes:

[Invoke automated-code-fixer]
→ automated-code-fixer runs ruff check --fix
→ All 5 errors auto-fixed
→ Push fixes to PR branch

[pr-reviewer re-runs gates]
→ All gates now PASS
→ Post review: "Auto-fixed linting errors. Approved after fixes."
```

***REMOVED******REMOVED*** Validation Checklist (Extended)

***REMOVED******REMOVED******REMOVED*** Pre-Review Checklist
- [ ] PR has clear description
- [ ] PR is not too large (< 500 lines ideal)
- [ ] PR targets correct base branch
- [ ] PR has been rebased on latest main (no conflicts)
- [ ] Author has reviewed own code first

***REMOVED******REMOVED******REMOVED*** Context Gathering Checklist
- [ ] Read PR title and description
- [ ] View changed files list
- [ ] Check commit history
- [ ] Review CI check status
- [ ] Read any linked issues

***REMOVED******REMOVED******REMOVED*** Local Testing Checklist
- [ ] Successfully checked out PR branch
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Application runs without errors
- [ ] No obvious regressions observed

***REMOVED******REMOVED******REMOVED*** Code Quality Review Checklist
- [ ] Code follows project architecture
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] No hardcoded values
- [ ] DRY principle followed
- [ ] Error handling appropriate
- [ ] No obvious performance issues

***REMOVED******REMOVED******REMOVED*** Security Review Checklist
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Auth checks in place
- [ ] No sensitive data in logs
- [ ] SQL injection prevented
- [ ] XSS vulnerabilities prevented
- [ ] Rate limiting on new endpoints

***REMOVED******REMOVED******REMOVED*** Testing Review Checklist
- [ ] Tests added for new code
- [ ] Tests cover edge cases
- [ ] Tests are readable
- [ ] Coverage >= 70%
- [ ] No flaky tests
- [ ] Tests document expected behavior

***REMOVED******REMOVED******REMOVED*** Architecture Review Checklist
- [ ] Follows layered architecture
- [ ] Database changes have migrations
- [ ] Async/await used correctly
- [ ] Pydantic schemas for I/O
- [ ] No circular dependencies
- [ ] Integration points documented

***REMOVED******REMOVED******REMOVED*** Documentation Review Checklist
- [ ] PR description is clear
- [ ] Complex logic commented
- [ ] API docs updated if needed
- [ ] CHANGELOG updated for features
- [ ] Breaking changes documented
- [ ] Code/comment consistency verified

***REMOVED******REMOVED******REMOVED*** Special Cases Checklist

**If PR includes database migration:**
- [ ] Model and migration committed together
- [ ] Upgrade tested
- [ ] Downgrade tested
- [ ] Data safety verified
- [ ] Backup plan documented

**If PR modifies security code:**
- [ ] Security-audit skill invoked
- [ ] Human review requested
- [ ] No obvious vulnerabilities
- [ ] Authentication not weakened
- [ ] Authorization maintained

**If PR adds constraint:**
- [ ] Constraint-preflight skill invoked
- [ ] Registration verified
- [ ] Weight hierarchy correct
- [ ] Clinical rationale documented

***REMOVED******REMOVED******REMOVED*** Post-Review Checklist
- [ ] Decision made (approve/request-changes/comment)
- [ ] Review summary posted
- [ ] Inline comments added
- [ ] Blocking vs. non-blocking issues clear
- [ ] Follow-up actions specified

***REMOVED******REMOVED*** References

- `/review-pr` slash command
- `.github/PULL_REQUEST_TEMPLATE.md` (if exists)
- `docs/development/AI_RULES_OF_ENGAGEMENT.md` - PR workflow rules
