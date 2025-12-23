---
name: pr-reviewer
description: Pull request review expertise with focus on context, quality gates, and team standards. Use when reviewing PRs, validating changes before merge, or generating PR descriptions. Works with gh CLI for GitHub integration.
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

***REMOVED******REMOVED*** Escalation Rules

**Request human review when:**

1. Changes touch authentication/authorization
2. Database migrations involved
3. ACGME compliance logic affected
4. Breaking API changes
5. Complex business logic unclear
6. Performance-critical code
7. Third-party integration changes

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

***REMOVED******REMOVED*** References

- `/review-pr` slash command
- `.github/PULL_REQUEST_TEMPLATE.md` (if exists)
- `docs/development/AI_RULES_OF_ENGAGEMENT.md` - PR workflow rules
