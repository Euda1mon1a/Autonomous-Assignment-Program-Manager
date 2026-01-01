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

# PR Reviewer Skill

Comprehensive pull request review skill that validates changes against project standards, runs quality gates, and provides structured feedback for merge decisions.

## When This Skill Activates

- Reviewing open pull requests
- Creating PR descriptions
- Validating changes before merge
- Checking CI/CD status
- Generating review summaries
- Approving or requesting changes

## PR Review Workflow

### Step 1: Gather Context

```bash
# Get PR details
gh pr view <PR_NUMBER> --json title,body,author,state,reviews,files,commits

# View the diff
gh pr diff <PR_NUMBER>

# Check CI status
gh pr checks <PR_NUMBER>

# Get commits
gh pr view <PR_NUMBER> --json commits

# List changed files
gh pr diff <PR_NUMBER> --name-only
```

### Step 2: Understand the Change

Questions to answer:
- What problem does this PR solve?
- What is the approach taken?
- What are the key changes?
- What might break?
- What tests were added?

### Step 3: Run Quality Gates

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Fetch and checkout PR
git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
git checkout pr-<PR_NUMBER>

# Run quality checks
pytest --tb=short -q
ruff check app/ tests/
black --check app/ tests/
mypy app/ --python-version 3.11

# Check test coverage
pytest --cov=app --cov-fail-under=70
```

### Step 4: Review Categories

#### A. Code Quality
- [ ] Code follows layered architecture
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] No magic numbers/hardcoded values
- [ ] DRY principle followed
- [ ] Appropriate error handling

#### B. Testing
- [ ] Tests added for new code
- [ ] Tests cover edge cases
- [ ] Tests are readable and maintainable
- [ ] Coverage >= 70%
- [ ] No flaky tests

#### C. Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Auth checks in place
- [ ] No sensitive data in logs/errors
- [ ] SQL injection prevention

#### D. Architecture
- [ ] Follows project patterns
- [ ] Database changes have migrations
- [ ] Async/await used correctly
- [ ] Pydantic schemas for I/O
- [ ] No circular dependencies

#### E. Documentation
- [ ] PR description is clear
- [ ] Complex logic commented
- [ ] API docs updated if needed
- [ ] CHANGELOG updated for features
- [ ] **Code/comment consistency** - verify comments match actual behavior
- [ ] **Seed data alignment** - filter values match canonical data sources

## Review Decision Matrix

| Gate | Pass | Block |
|------|------|-------|
| Tests | All pass | Any failure |
| Linting | 0 errors | Any error |
| Types | 0 errors | Critical types missing |
| Security | No issues | Any vulnerability |
| Coverage | >= 70% | < 60% |
| Architecture | Follows patterns | Major violation |

## PR Feedback Format

### Inline Comments

Use GitHub's suggestion format for fixes:

````markdown
```suggestion
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```
````

### Review Summary

```markdown
## Review Summary

**Decision:** APPROVE / REQUEST CHANGES / COMMENT

### What This PR Does
[One sentence summary]

### Quality Gate Results
| Gate | Status | Notes |
|------|--------|-------|
| Tests | :white_check_mark: | 47 passed |
| Linting | :white_check_mark: | 0 errors |
| Types | :white_check_mark: | 100% coverage |
| Security | :white_check_mark: | bandit clear |
| Coverage | :yellow_circle: | 72% (target 80%) |

### Changes Reviewed
- `app/services/new_feature.py` - New service implementation
- `tests/test_new_feature.py` - Test coverage

### Feedback

#### Required Changes (Blocking)
1. [file:line] - Description of issue
   - Impact: [what could go wrong]
   - Suggestion: [how to fix]

#### Suggestions (Non-blocking)
1. [file:line] - Description
   - Recommendation: [improvement]

#### Questions
1. [Question about the approach]

### Testing Notes
Tested locally:
- [x] Unit tests pass
- [x] Integration tests pass
- [ ] Manual testing [describe if done]

### Merge Checklist
- [ ] All conversations resolved
- [ ] CI checks passing
- [ ] Required reviews obtained
- [ ] Documentation updated
```

## PR Description Template

When creating PRs:

```markdown
## Summary
[1-3 bullet points describing the change]

## Motivation
[Why this change is needed]

## Changes
- [List key changes]

## Testing
- [How was this tested?]

## Test Plan
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing done

## Screenshots
[If applicable]

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Closes #[issue number]
```

## GitHub CLI Commands

```bash
# List open PRs
gh pr list

# View specific PR
gh pr view <number>

# Check PR status
gh pr checks <number>

# Review PR
gh pr review <number> --approve -b "Looks good!"
gh pr review <number> --request-changes -b "See comments"
gh pr review <number> --comment -b "Questions inline"

# Add comment
gh pr comment <number> --body "Comment text"

# Merge PR
gh pr merge <number> --squash --delete-branch

# Get PR diff
gh pr diff <number>

# Create PR
gh pr create --title "Title" --body "Description"
```

## Automated PR Checks

### Pre-Review Automation

```bash
#!/bin/bash
# scripts/pr-review-prep.sh

PR_NUMBER=$1

# Fetch PR
git fetch origin pull/${PR_NUMBER}/head:pr-${PR_NUMBER}
git checkout pr-${PR_NUMBER}

# Run quality checks
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

## Common Review Patterns

### Missing Tests

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

### Architecture Violation

```markdown
This violates the layered architecture pattern.

**Issue:** Business logic in route handler

**Current:**
```python
@router.post("/items")
async def create_item(data: ItemCreate, db: Session):
    # Business logic here (violation)
    if data.value > 100:
        data.value = 100
    item = Item(**data.dict())
    db.add(item)
```

**Should be:**
```python
# In service layer
async def create_item(db: Session, data: ItemCreate) -> Item:
    if data.value > 100:
        data.value = 100
    item = Item(**data.dict())
    db.add(item)
    return item

# In route
@router.post("/items")
async def create_item_route(data: ItemCreate, db: Session):
    return await create_item(db, data)
```
```

### Missing Type Hints

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

## Examples

### Example 1: Standard PR Review (Feature Addition)

**Context:** PR #523 adds resident work hour summary endpoint

**Input:**
```bash
gh pr view 523 --json title,files,commits
```

**Process:**
1. **Gather context:**
   - Title: "feat: Add work hour summary endpoint"
   - Files changed: 3 (route, service, tests)
   - Commits: 2 commits
2. **Check CI status:**
   ```bash
   gh pr checks 523
   # ✓ Tests: passing
   # ✓ Lint: passing
   # ✗ Coverage: 65% (below 70% threshold)
   ```
3. **Review code:**
   - Route follows layered architecture ✓
   - Service has business logic ✓
   - Tests added but incomplete (missing edge cases)
4. **Run quality gates locally:**
   ```bash
   git fetch origin pull/523/head:pr-523
   git checkout pr-523
   pytest --cov=app.services.work_hour_service --cov-fail-under=70
   # FAIL: 65% coverage
   ```

**Output:**
```markdown
## PR Review: #523 - Add work hour summary endpoint

**Decision:** REQUEST CHANGES

### Quality Gate Results
| Gate | Status | Notes |
|------|--------|-------|
| Tests | ✓ | 12 tests pass |
| Linting | ✓ | No errors |
| Types | ✓ | No errors |
| Coverage | ✗ | 65% (target 70%) |

### Required Changes (Blocking)
1. **Insufficient test coverage** (app/services/work_hour_service.py:45-78)
   - Missing tests for edge cases:
     - Empty assignment list
     - Assignments spanning multiple weeks
     - Null duration handling
   - Add tests to bring coverage to 70%+

### Suggestions (Non-blocking)
1. Consider caching work hour calculations (line 56)
   - Reduces database load for frequently accessed residents
   - Use Redis with 15-minute TTL

### Approval Checklist
- [x] Architecture follows patterns
- [x] Tests exist
- [ ] Coverage >= 70% (BLOCKING)
- [x] Linting passes
- [x] Types valid

**Next Steps:** Add missing tests, push update, request re-review.
```

### Example 2: Security-Critical PR Review

**Context:** PR #478 modifies authentication middleware

**Input:**
```python
# Changed file: backend/app/api/deps.py
def get_current_user(token: str = Depends(oauth2_scheme)):
    # CHANGE: Removed JWT expiration check
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload.get("sub")
```

**Process:**
1. **Identify security-sensitive area:** Authentication code
2. **Compare with previous version:**
   ```diff
   - if payload.get("exp") < time.time():
   -     raise HTTPException(401, "Token expired")
   + # Expiration check removed
   ```
3. **Assess impact:** CRITICAL - allows expired tokens
4. **Trigger security-audit skill** for full analysis

**Output:**
```markdown
## PR Review: #478 - Update auth middleware

**Decision:** :red_circle: BLOCK MERGE - CRITICAL SECURITY ISSUE

### Security Finding

**Severity:** CRITICAL
**Issue:** JWT Expiration Check Removed

This change allows expired tokens to authenticate, violating authentication security.

**Security Impact:**
- Tokens never expire (OWASP A07:2021 - Authentication Failures)
- Compromised tokens remain valid indefinitely
- No mechanism to revoke access
- Violates standard JWT security practices

**Required Fix:**
1. Revert expiration check removal
2. Add explicit test for expired token rejection
3. Security review required before merge

**Escalation:** Triggered security-audit skill for full assessment.

### Action Required
- [ ] Revert to include expiration check
- [ ] Add test: `test_expired_token_rejected()`
- [ ] Human security review before re-submit
```

### Example 3: Database Migration PR Review

**Context:** PR #501 adds `email_verified` field to User model

**Input:**
```bash
gh pr diff 501 --name-only
# backend/app/models/user.py
# backend/alembic/versions/abc123_add_email_verified.py
```

**Process:**
1. **Check model and migration together:** ✓ Both files present
2. **Review migration:**
   ```python
   def upgrade() -> None:
       op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False))
   ```
3. **Identify issue:** Adding non-nullable column to table with existing rows will fail
4. **Verify locally:**
   ```bash
   alembic upgrade head
   # ERROR: column "email_verified" contains null values
   ```

**Output:**
```markdown
## PR Review: #501 - Add email_verified field

**Decision:** REQUEST CHANGES

### Database Migration Issue

**Problem:** Non-nullable column added to table with existing rows

This migration will fail in production because:
1. Existing users don't have `email_verified` value
2. Column is `nullable=False` (requires value)
3. No default provided

**Current Migration:**
```python
op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False))
```

**Required Fix - Three-Phase Migration:**
```python
# Migration 1: Add as nullable
op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

# Migration 2: Backfill
op.execute("UPDATE users SET email_verified = false WHERE email_verified IS NULL")

# Migration 3: Make non-nullable
op.alter_column('users', 'email_verified', nullable=False)
```

**Testing:**
- [ ] Test migration on database with existing data
- [ ] Verify downgrade path works
- [ ] Document rollback procedure

**Escalation:** Deferred to database-migration skill for implementation.
```

## Lesson Learned: PR #442 (2025-12-26)

**What happened:** A fix changed a filter from one value to another, but the new value
was also incorrect because comments/docs said "outpatient" while code used "clinic".

**Prevention checklist for filter/constant changes:**
- [ ] Verify value against seed data (`scripts/seed_templates.py`)
- [ ] Check if comments describe different behavior than code implements
- [ ] Cross-reference with canonical data source (e.g., BLOCK_10_ROADMAP)
- [ ] Confirm the filter will actually find matching records

**Key insight:** Always ask "will this filter find what we expect?" and verify empirically.

## Common Failure Modes

| Failure Mode | Symptom | Root Cause | Recovery Steps |
|--------------|---------|------------|----------------|
| **CI Passes But Code Broken** | All checks green, but feature doesn't work | Insufficient test coverage or wrong tests | 1. Manual testing reveals issue<br>2. Add missing test cases<br>3. Re-run CI with new tests |
| **Merge Conflict During Review** | PR becomes outdated while under review | Long review cycle, active main branch | 1. Request author to rebase<br>2. Re-run quality gates after rebase<br>3. Re-review changed sections only |
| **False Positive Security Alert** | Bandit flags safe code as vulnerable | Static analysis limitation | 1. Manual review confirms false positive<br>2. Add `# nosec` comment with justification<br>3. Document in review |
| **Coverage Drops After Merge** | PR shows 80% coverage, but repo drops to 65% | Coverage calculated only for changed files | 1. Check overall repo coverage before approve<br>2. Require tests for affected areas, not just new code<br>3. Use `--cov=app` not `--cov=app.services.new_module` |
| **Database Migration Not Tested** | Migration file present but untested | CI doesn't run migrations in test environment | 1. Manually test migration locally<br>2. Request author to test `upgrade` and `downgrade`<br>3. Add migration testing to CI |
| **Breaking API Change Undetected** | Pydantic schema changed without version bump | No API contract testing | 1. Check schema diff against previous version<br>2. Determine if breaking (required field added, field removed)<br>3. Require API version bump or revert change |

## Validation Checklist

After reviewing a PR, verify:

- [ ] **PR Description:** Clear summary of what/why
- [ ] **Linked Issues:** References issue number or motivation
- [ ] **CI Checks:** All automated checks pass
- [ ] **Tests Added:** New code has corresponding tests
- [ ] **Coverage:** >= 70% for changed files
- [ ] **Linting:** No lint errors
- [ ] **Type Checking:** No type errors
- [ ] **Security:** No vulnerabilities detected
- [ ] **Architecture:** Follows layered pattern
- [ ] **Database Migrations:** If model changed, migration present and tested
- [ ] **Breaking Changes:** Documented or avoided
- [ ] **Documentation:** Updated if needed (README, API docs)
- [ ] **No Secrets:** No hardcoded credentials or sensitive data
- [ ] **Dependency Changes:** If `requirements.txt` changed, justified
- [ ] **Manual Testing:** For complex features, manually verified
- [ ] **Conflicts Resolved:** No merge conflicts present

## Escalation Rules

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

## Integration with Other Skills

### With code-review
For detailed code analysis:
1. PR-reviewer handles workflow and gates
2. Code-review handles line-by-line analysis
3. Combine findings in final review

### With security-audit
For security-sensitive PRs:
1. Detect sensitive file changes
2. Trigger security-audit skill
3. Include security findings in review

### With automated-code-fixer
For simple fixes:
1. Suggest fixes inline
2. If accepted, automated-code-fixer applies
3. Re-run quality gates
4. Update PR status

## Concrete Usage Example

### End-to-End: Reviewing PR #442 (Real Example)

**Scenario:** PR fixes template filtering in schedule solver. Change is small but critical.

**Step 1: Fetch and Understand**
```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Get PR details
gh pr view 442 --json title,body,files

# Output:
# Title: "Fix template filtering to use 'outpatient' activity type"
# Files: backend/app/scheduling/solvers.py (1 line changed)

# View the diff
gh pr diff 442

# Output shows:
# - activity_type="clinic"
# + activity_type="outpatient"
```

**Step 2: Check Context**
```bash
# Read the surrounding code
grep -B10 -A10 "activity_type" backend/app/scheduling/solvers.py

# Check seed data to verify which value is correct
grep "activity_type" scripts/seed_templates.py
```

**Finding:** Need to verify which activity_type value is correct for elective/selective templates.

**Step 3: Verify Against Canonical Data**
```bash
# Check BLOCK_10_ROADMAP or seed data
grep -i "neurology\|palliative\|peds" scripts/seed_templates.py

# Output shows:
# Template("Neurology", activity_type="outpatient", ...)
# Template("Palliative Care", activity_type="outpatient", ...)
```

**Finding:** ✅ "outpatient" is correct! These electives use outpatient activity type.

**Step 4: Check Code Comments vs Implementation**
```bash
# Look for comments describing this filter
grep -B5 "activity_type" backend/app/scheduling/solvers.py
```

**Finding:** ⚠️ Comment says "filter to elective templates" but doesn't specify activity_type value. Could be clearer.

**Step 5: Run Quality Gates**
```bash
# Checkout the PR
git fetch origin pull/442/head:pr-442
git checkout pr-442

# Run tests
cd backend
pytest tests/test_scheduling_engine.py -v
# Result: All pass

# Check if change breaks anything else
pytest -k "template" -v
# Result: All pass
```

**Finding:** ✅ Tests pass, no regressions.

**Step 6: Check for Similar Issues**
```bash
# Search for other hardcoded activity_type filters
grep -n 'activity_type.*=.*"' backend/app/scheduling/*.py

# Output:
# solvers.py:145: activity_type="outpatient"  # Our fix
# engine.py:203: activity_type="clinic"      # Different context - FM Clinic capacity
```

**Finding:** ⚠️ Need to verify engine.py:203 is intentional (it is - different constraint).

**Step 7: Lessons Learned Check**

**Was this issue caused by a known pattern?**

Review pr-reviewer/SKILL.md "Lesson Learned: PR #442" section:
- This is the ORIGINAL PR #442 that caught the issue!
- The lesson: Always verify filter values against seed data
- This is a GOOD CATCH example, not a failure

**Step 8: Write Review**

```markdown
## PR Review: #442

**Decision:** APPROVE ✅

### What This PR Does
Fixes template filtering to use correct activity_type value for elective/selective rotations.

### Quality Gate Results
| Gate | Status | Notes |
|------|--------|-------|
| Tests | ✅ | All passing |
| Linting | ✅ | 0 errors |
| Correctness | ✅ | Verified against seed data |

### Verification Performed
1. ✅ Checked seed_templates.py - "outpatient" is correct for electives
2. ✅ Ran relevant tests - all pass
3. ✅ Verified comment/code consistency
4. ✅ Checked for similar issues elsewhere - found none

### What I Liked
- Small, focused change
- Caught before merge (good process!)
- Properly documented in commit message

### Suggestions (Non-blocking)
1. Consider adding a comment above the filter explaining why "outpatient":
   ```python
   # Filter to elective/selective templates (activity_type="outpatient")
   # FM Clinic uses "clinic" type and has separate capacity constraints
   templates = self._get_rotation_templates(activity_type="outpatient")
   ```

2. Add test case that verifies correct templates are loaded:
   ```python
   def test_get_rotation_templates_filters_to_outpatient():
       """Ensure elective templates use outpatient activity type."""
       templates = engine._get_rotation_templates(activity_type="outpatient")
       assert all(t.activity_type == "outpatient" for t in templates)
       assert "Neurology" in [t.name for t in templates]
       assert "Family Medicine Clinic" not in [t.name for t in templates]
   ```

### Merge Checklist
- [x] All conversations resolved
- [x] CI checks passing
- [x] Verified against canonical data
- [x] No similar issues found

**Recommendation:** Merge when ready. Suggestions are optional improvements.
```

**Step 9: Submit Review**
```bash
gh pr review 442 --approve --body "$(cat review.md)"
```

**Total Time:** ~10 minutes (small, focused PR)

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ PULL REQUEST REVIEW WORKFLOW                                │
└─────────────────────────────────────────────────────────────┘

1. FETCH PR CONTEXT
   ├─ gh pr view <number> --json title,body,files
   ├─ gh pr diff <number>
   └─ Understand the "why"
              ↓
2. VERIFY CORRECTNESS
   ├─ Check against canonical data sources
   ├─ Verify filter values will find expected records
   └─ Review comments match implementation
              ↓
3. CHECKOUT & TEST
   ├─ git fetch origin pull/<n>/head:pr-<n>
   ├─ git checkout pr-<n>
   ├─ Run: pytest (relevant tests)
   └─ Run: ruff check, mypy
              ↓
4. QUALITY GATES
   ├─ Tests: All must pass
   ├─ Linting: 0 errors
   ├─ Security: No vulnerabilities
   └─ Coverage: >= 70%
              ↓
5. CONTEXTUAL REVIEW
   ├─ Check for similar issues elsewhere
   ├─ Verify against lessons learned
   └─ Consider broader impact
              ↓
6. DECISION MATRIX
   ├─ Any gate failed? → REQUEST CHANGES
   ├─ Security/auth changes? → ESCALATE TO HUMAN
   ├─ Minor suggestions only? → APPROVE with comments
   └─ All perfect? → APPROVE
              ↓
7. SUBMIT REVIEW
   ├─ gh pr review <number> --approve/--request-changes
   └─ Include detailed feedback
```

## Common Failure Modes

### Failure Mode 1: Approving Without Testing
**Symptom:** PR looks good in diff but breaks when deployed

**Example:** PR changes database query but tests aren't run locally
```bash
# BAD - Just reading the diff
gh pr diff 123
# Looks good!
gh pr review 123 --approve

# GOOD - Actually test it
git fetch origin pull/123/head:pr-123
git checkout pr-123
pytest
# Oh, tests fail! Good thing we checked.
```

**Prevention:** Always checkout and run tests for non-trivial changes

### Failure Mode 2: Missing Broader Impact
**Symptom:** Change breaks something in unexpected area

**Example:** PR changes constraint weight, but doesn't check solver performance
```python
# PR changes:
- CallSpacingConstraint(weight=8.0)
+ CallSpacingConstraint(weight=15.0)  # Make it stronger

# Reviewer approves without checking impact
# Result: Solver now takes 10x longer because this constraint conflicts with others
```

**Detection:**
- Search for other usages: `grep -r "CallSpacing" backend/`
- Check if weight is referenced in docs
- Look for related tests

**Prevention:** For infrastructure changes, run performance tests

### Failure Mode 3: Trusting Comments Over Code
**Symptom:** Comments say one thing, code does another

**Example from PR #442:**
```python
# Comment says: "Filter to clinic templates"
# Code says: activity_type="outpatient"
# Actual data: Clinic uses "clinic", outpatient uses "outpatient"

# Which is right? Must verify against seed data!
```

**Detection:** Always verify claims against actual data/behavior

**Prevention:** Add to checklist: "Do comments match implementation?"

### Failure Mode 4: Not Checking Seed Data Alignment
**Symptom:** Filter values don't match canonical data sources

**Example:**
```python
# PR filters for:
templates = filter(lambda t: t.category == "elective", all_templates)

# But seed data uses:
Template("Neurology", type="selective", ...)  # Not "elective"!

# Filter will miss records!
```

**Detection:**
```bash
# Always check seed data
grep -i "neurology" scripts/seed_templates.py
grep -i "category\|type" scripts/seed_templates.py
```

**Prevention:** Add to review checklist: "Verify filter values against seed data"

### Failure Mode 5: Skipping Lessons Learned
**Symptom:** Same mistakes repeated across PRs

**Example:** PR #400 had auth issue. PR #450 has same auth issue because reviewer didn't check lessons learned.

**Detection:** Before each review:
```bash
# Check for relevant lessons
grep -i "lesson\|failure mode" .claude/skills/pr-reviewer/SKILL.md
```

**Prevention:** Maintain "Lesson Learned" section in this skill file

## References

- `/review-pr` slash command
- `.github/PULL_REQUEST_TEMPLATE.md` (if exists)
- `docs/development/AI_RULES_OF_ENGAGEMENT.md` - PR workflow rules
