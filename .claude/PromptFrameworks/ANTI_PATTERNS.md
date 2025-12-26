# Anti-Patterns for AI Agents

> **Purpose:** Common pitfalls and how to avoid them when working on the Residency Scheduler
> **Use this document:** Before committing, when uncertain, during code review

---

## Overview

Anti-patterns are **recurring solutions that appear helpful but cause problems**. This document catalogs common mistakes AI agents make when working on medical residency scheduling systems.

**How to Use:**

1. **Before committing:** Review relevant sections as a checklist
2. **When uncertain:** Search for similar situations in this doc
3. **After making a mistake:** Add it to this doc so others learn

---

## Safety Anti-Patterns

These anti-patterns can cause **ACGME violations, data loss, or security breaches**. Never do these.

### ❌ AP-S01: Silently Relaxing Safety Constraints

**What It Looks Like:**

```python
# BAD: Commenting out ACGME validation to make tests pass
async def create_assignment(db, assignment_data):
    # validation.validate_acgme_compliance(assignment_data)  # TODO: Fix later
    return await db.execute(insert(Assignment).values(**assignment_data))
```

**Why It's Dangerous:**

- ACGME violations can result in program accreditation loss
- "Fix later" often becomes "never fix"
- Silent failures hide regulatory violations

**Correct Approach:**

```python
# GOOD: Fix the root cause of validation failure
async def create_assignment(db, assignment_data):
    # Always validate before creating
    await validation.validate_acgme_compliance(db, assignment_data)
    return await db.execute(insert(Assignment).values(**assignment_data))
```

**Detection:** If you're tempted to comment out validation, **stop and loop back to Research phase**.

---

### ❌ AP-S02: Inventing Residents or Rotations

**What It Looks Like:**

```python
# BAD: Creating synthetic data to fill gaps
if not resident:
    resident = Person(
        id="PLACEHOLDER_001",
        name="TBD Resident",
        role="RESIDENT"
    )
    db.add(resident)
```

**Why It's Dangerous:**

- Schedule assignments must reference **real people**
- Placeholder data can be forgotten and cause production errors
- ACGME reporting requires accurate person records

**Correct Approach:**

```python
# GOOD: Fail loudly if data is missing
if not resident:
    raise ValueError(
        f"Resident {resident_id} not found. "
        "Cannot create assignment without valid resident record."
    )
```

**Detection:** Never use `PLACEHOLDER`, `TBD`, `DUMMY`, or `TEST` in production data.

---

### ❌ AP-S03: Skipping ACGME Validation

**What It Looks Like:**

```python
# BAD: Direct database insert without validation
swap = Swap(from_person=p1, to_person=p2, date=date)
db.add(swap)
await db.commit()
```

**Why It's Dangerous:**

- Swaps can violate 80-hour rule
- Can create N-1 contingency failures
- No audit trail of compliance checks

**Correct Approach:**

```python
# GOOD: Use service layer with built-in validation
swap_executor = SwapExecutor()
result = await swap_executor.execute_swap(
    db=db,
    swap_request=swap_request,
    validate_acgme=True  # Always True in production
)
```

**Detection:** If you're directly inserting into `assignments` or `swaps` tables, you're probably skipping validation.

---

### ❌ AP-S04: Bypassing Backup Requirements

**What It Looks Like:**

```python
# BAD: Modifying schedule without backup
async def regenerate_block_schedule(block_id: str):
    # Delete existing assignments
    await db.execute(delete(Assignment).where(Assignment.block_id == block_id))
    # Generate new assignments
    new_assignments = generate_assignments(block_id)
    db.add_all(new_assignments)
```

**Why It's Dangerous:**

- No rollback if generation fails mid-way
- Data loss if generation produces invalid schedule
- Violates `safe-schedule-generation` skill requirements

**Correct Approach:**

```python
# GOOD: Use safe-schedule-generation skill with mandatory backup
from app.services.schedule_backup import create_backup, restore_backup

async def regenerate_block_schedule(block_id: str):
    # MANDATORY: Backup before any write operation
    backup_id = await create_backup(db, scope="block", scope_id=block_id)

    try:
        # Delete and regenerate
        await db.execute(delete(Assignment).where(Assignment.block_id == block_id))
        new_assignments = generate_assignments(block_id)
        db.add_all(new_assignments)
        await db.commit()

        # Validate result
        await validate_schedule(db, block_id)

    except Exception as e:
        # Rollback to backup on any failure
        await restore_backup(db, backup_id)
        raise ScheduleGenerationError(f"Generation failed: {e}") from e
```

**Detection:** If modifying `assignments`, `swaps`, or `blocks` tables, **always create backup first**.

---

### ❌ AP-S05: Exposing Sensitive Data in Logs

**What It Looks Like:**

```python
# BAD: Logging full person records
logger.info(f"Processing swap for person: {person}")  # Logs name, email, SSN, etc.
```

**Why It's Dangerous:**

- HIPAA violation (if logs are stored or transmitted)
- PERSEC violation (military personnel data)
- Logs may be accessible to unauthorized users

**Correct Approach:**

```python
# GOOD: Log only non-sensitive identifiers
logger.info(f"Processing swap for person_id: {person.id}")

# If you need to debug, use sanitized representation
logger.debug(f"Swap details: person_id={person.id}, date={date}, rotation_type={rotation.type}")
```

**Detection:** Search for `logger.*f".*{person}.*"` or `logger.*f".*{resident}.*"` in code.

---

## Quality Anti-Patterns

These anti-patterns create **technical debt, bugs, or maintenance burdens**.

### ❌ AP-Q01: Committing Without Tests

**What It Looks Like:**

```bash
# BAD: Committing code without running tests
git add backend/app/services/new_feature.py
git commit -m "feat: Add new feature"
git push
```

**Why It's Bad:**

- Breaks CI/CD pipeline
- Introduces untested code to production
- Makes debugging harder (which commit broke it?)

**Correct Approach:**

```bash
# GOOD: Always test before committing
cd backend
pytest tests/test_new_feature.py  # Run relevant tests
pytest  # Run full test suite
git add backend/app/services/new_feature.py tests/test_new_feature.py
git commit -m "feat: Add new feature with tests"
```

**Checklist:**

- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Coverage >= 80% for new code
- [ ] `pytest` runs without errors

---

### ❌ AP-Q02: Ignoring Linter Warnings

**What It Looks Like:**

```python
# Code with linter warnings
def calculateHours(assignments):  # Naming violation
    total = 0
    for a in assignments:
        total += a.hours  # Unused variable
    return sum([a.hours for a in assignments])  # Duplication
```

**Why It's Bad:**

- Linter warnings indicate code smells
- Makes code harder to read and maintain
- Can hide actual bugs

**Correct Approach:**

```bash
# GOOD: Fix linter warnings before committing
cd backend
ruff check . --fix  # Auto-fix what's possible
ruff format .       # Format code

# Then review remaining warnings manually
```

```python
# Fixed code
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```

**Detection:** Run `ruff check .` before every commit.

---

### ❌ AP-Q03: Hardcoding Values

**What It Looks Like:**

```python
# BAD: Hardcoded URLs, limits, credentials
API_URL = "http://localhost:8000"
MAX_HOURS_PER_WEEK = 80
REDIS_PASSWORD = "my_secret_password"
```

**Why It's Bad:**

- Environment-specific values break in prod
- Constants scattered across codebase
- Security risk (hardcoded credentials)

**Correct Approach:**

```python
# GOOD: Use configuration and environment variables
from app.core.config import settings

API_URL = settings.API_BASE_URL  # From .env
MAX_HOURS_PER_WEEK = settings.ACGME_MAX_HOURS_PER_WEEK
REDIS_PASSWORD = settings.REDIS_PASSWORD  # From .env, never committed
```

**Detection:** Search for hardcoded IPs, ports, passwords, or magic numbers.

---

### ❌ AP-Q04: Duplicating Code Instead of Refactoring

**What It Looks Like:**

```python
# BAD: Copy-pasting similar logic
async def get_resident_hours_this_week(db, resident_id):
    assignments = await db.execute(
        select(Assignment)
        .where(Assignment.person_id == resident_id)
        .where(Assignment.date >= get_week_start())
        .where(Assignment.date <= get_week_end())
    )
    return sum(a.hours for a in assignments.scalars())

async def get_faculty_hours_this_week(db, faculty_id):
    assignments = await db.execute(
        select(Assignment)
        .where(Assignment.person_id == faculty_id)
        .where(Assignment.date >= get_week_start())
        .where(Assignment.date <= get_week_end())
    )
    return sum(a.hours for a in assignments.scalars())
```

**Why It's Bad:**

- Changes must be made in multiple places
- Increases bug surface area
- Makes testing harder

**Correct Approach:**

```python
# GOOD: Extract common logic
async def get_person_hours_this_week(db, person_id: str) -> float:
    """Get total hours for any person this week."""
    assignments = await db.execute(
        select(Assignment)
        .where(Assignment.person_id == person_id)
        .where(Assignment.date >= get_week_start())
        .where(Assignment.date <= get_week_end())
    )
    return sum(a.hours for a in assignments.scalars())

# Specialized versions just call the common function
async def get_resident_hours_this_week(db, resident_id):
    return await get_person_hours_this_week(db, resident_id)
```

**Detection:** If you're copy-pasting code, **extract a function instead**.

---

### ❌ AP-Q05: Missing Error Handling

**What It Looks Like:**

```python
# BAD: No error handling
async def get_person(db, person_id: str):
    result = await db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one()  # Raises if not found, but caller doesn't know
```

**Why It's Bad:**

- Unhandled exceptions propagate to API, leak details
- Callers don't know what exceptions to expect
- No graceful degradation

**Correct Approach:**

```python
# GOOD: Explicit error handling with custom exceptions
async def get_person(db, person_id: str) -> Person:
    """
    Get person by ID.

    Raises:
        PersonNotFoundError: If person doesn't exist
        DatabaseError: If database query fails
    """
    try:
        result = await db.execute(select(Person).where(Person.id == person_id))
        person = result.scalar_one_or_none()

        if not person:
            raise PersonNotFoundError(f"Person {person_id} not found")

        return person

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching person {person_id}", exc_info=True)
        raise DatabaseError("Failed to fetch person") from e
```

**Detection:** If function doesn't have `Raises:` section in docstring, add error handling.

---

## Process Anti-Patterns

These anti-patterns violate **workflow, git, or CI/CD best practices**.

### ❌ AP-P01: Pushing Directly to Main

**What It Looks Like:**

```bash
# BAD: Committing directly to main branch
git checkout main
git add .
git commit -m "fix: Quick bug fix"
git push origin main
```

**Why It's Bad:**

- Bypasses PR review process
- No CI checks before merge
- Breaks team workflow
- Violates AI Rules of Engagement

**Correct Approach:**

```bash
# GOOD: Create feature branch, PR workflow
git checkout -b fix/quick-bug-fix
git add .
git commit -m "fix: Quick bug fix"
git push origin fix/quick-bug-fix

# Then create PR via gh CLI
gh pr create --title "Fix quick bug" --body "Fixes issue #123"
```

**Detection:** Check current branch with `git branch --show-current` before committing.

---

### ❌ AP-P02: Force Pushing Without Confirmation

**What It Looks Like:**

```bash
# BAD: Force pushing without checking
git push --force origin main
```

**Why It's Bad:**

- Overwrites remote history
- Can delete others' work
- Breaks collaboration

**Correct Approach:**

```bash
# GOOD: Use force-with-lease and only on feature branches
git branch --show-current  # Confirm you're NOT on main
git push --force-with-lease origin feature-branch  # Safer than --force
```

**Rule:** NEVER force-push to `main` or `origin/main` unless explicitly approved.

---

### ❌ AP-P03: Skipping PR Review

**What It Looks Like:**

```bash
# BAD: Merging PR immediately without review
gh pr create --title "Feature" --body "New feature"
gh pr merge --auto --merge  # Merges without approval
```

**Why It's Bad:**

- No code review
- No CI checks
- No opportunity to catch bugs

**Correct Approach:**

```bash
# GOOD: Wait for PR review and CI
gh pr create --title "Feature" --body "New feature"
# Wait for:
# - CI checks to pass
# - Human reviewer approval (if required)
# - Then merge
```

**Rule:** All PRs must pass CI before merging.

---

### ❌ AP-P04: Amending Others' Commits

**What It Looks Like:**

```bash
# BAD: Amending a commit you didn't create
git log -1 --format='%an %ae'
# Output: John Doe <john@example.com>  (not you!)

git commit --amend -m "Updated message"  # DON'T DO THIS
```

**Why It's Bad:**

- Changes authorship/timestamp
- Confuses git history
- Disrespectful to original author

**Correct Approach:**

```bash
# GOOD: Check authorship before amending
git log -1 --format='%an %ae'

# If not your commit, create new commit instead
git commit -m "fix: Address issue in previous commit"
```

**Rule:** Only amend your own commits, and only if not pushed to shared branch.

---

### ❌ AP-P05: Modifying Database Without Migration

**What It Looks Like:**

```python
# BAD: Changing model without migration
class Person(Base):
    __tablename__ = "persons"
    id = Column(String, primary_key=True)
    name = Column(String)
    middle_name = Column(String)  # ADDED - but no migration!
```

**Why It's Bad:**

- Database schema out of sync with code
- Production database breaks on deployment
- No rollback path

**Correct Approach:**

```bash
# GOOD: Always create migration for model changes
# 1. Modify model
# 2. Create migration
cd backend
alembic revision --autogenerate -m "Add middle_name to Person"

# 3. Review migration (autogenerate isn't perfect)
vim alembic/versions/xxx_add_middle_name_to_person.py

# 4. Test migration
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 5. Commit both model and migration
git add backend/app/models/person.py
git add backend/alembic/versions/xxx_add_middle_name_to_person.py
git commit -m "feat: Add middle_name to Person model"
```

**Detection:** If modifying a `models/*.py` file, **always create a migration**.

---

## Communication Anti-Patterns

These anti-patterns cause **confusion, miscommunication, or incomplete work**.

### ❌ AP-C01: Assuming Context

**What It Looks Like:**

Agent response:
> "I've updated the swap logic to fix the issue."

User:
> "What issue? Which swap logic?"

**Why It's Bad:**

- User doesn't know what changed
- No traceability
- Harder to debug later

**Correct Approach:**

Agent response:
> "I've updated the swap execution logic in `backend/app/services/swap_executor.py` to fix the race condition where two users could swap the same slot simultaneously. Added database row locking with `with_for_update()` to prevent concurrent modifications."

**Rule:** Always specify **what, where, why** in responses.

---

### ❌ AP-C02: Making Up Data

**What It Looks Like:**

User:
> "How many residents are assigned to inpatient this week?"

Agent (without checking):
> "There are 8 residents on inpatient this week."

**Why It's Bad:**

- Factually incorrect information
- User makes decisions based on false data
- Erodes trust

**Correct Approach:**

```python
# GOOD: Query database before answering
result = await db.execute(
    select(func.count(Assignment.id))
    .join(Rotation)
    .where(Rotation.type == "inpatient")
    .where(Assignment.date >= get_week_start())
    .where(Assignment.date <= get_week_end())
)
count = result.scalar()

# Then respond with actual data
```

Agent response:
> "I queried the database: there are 6 residents assigned to inpatient rotations this week (Dec 18-24, 2024)."

**Rule:** Never guess. If you don't know, query or say "I don't know."

---

### ❌ AP-C03: Hiding Errors

**What It Looks Like:**

```python
# BAD: Silently catching and ignoring errors
try:
    result = await validate_acgme_compliance(assignment)
except Exception:
    pass  # Hope it works out
```

Agent:
> "Assignment created successfully."

**Why It's Bad:**

- User thinks operation succeeded
- Error is hidden until production
- No debugging information

**Correct Approach:**

```python
# GOOD: Surface errors to user
try:
    result = await validate_acgme_compliance(assignment)
except ACGMEViolationError as e:
    logger.error(f"ACGME validation failed: {e}", exc_info=True)
    raise  # Re-raise to user
```

Agent:
> "Error: Assignment would violate ACGME 80-hour rule. Resident FAC-01 would have 85 hours this week. Please adjust the schedule."

**Rule:** Always surface errors to user with actionable information.

---

### ❌ AP-C04: Overcommitting Scope

**What It Looks Like:**

User:
> "Can you add a button to the swap page?"

Agent:
> "Sure! I'll add the button, refactor the entire swap component to use Zustand for state management, optimize the API endpoint, add caching, rewrite the tests, and update all documentation."

**Why It's Bad:**

- Scope creep
- Takes much longer than expected
- Introduces unnecessary changes and risk

**Correct Approach:**

Agent:
> "I can add a button to the swap page. This will require:
> 1. Adding button component to `SwapForm.tsx`
> 2. Wiring up click handler
> 3. Adding test for button behavior
>
> Should I also refactor the state management, or just add the button as-is?"

**Rule:** Do what's asked, nothing more. Ask before expanding scope.

---

### ❌ AP-C05: Vague Commit Messages

**What It Looks Like:**

```bash
# BAD: Vague or unhelpful commit messages
git commit -m "fix stuff"
git commit -m "update"
git commit -m "WIP"
git commit -m "changes"
```

**Why It's Bad:**

- Can't understand what changed without reading full diff
- Makes git history useless
- Hard to find specific changes later

**Correct Approach:**

```bash
# GOOD: Descriptive commit messages following conventional commits
git commit -m "feat: Add auto-matcher for swap requests

- Implement SwapMatcher.find_matches() algorithm
- Score by rotation match, seniority, swap history
- Validate ACGME compliance for all matches
- Add 12 unit tests with 100% coverage

Closes #247"
```

**Format:**

```
<type>: <short summary>

<optional detailed description>

<optional footer (issue references)>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## Detection Checklist

Before committing, review this checklist:

### Safety

- [ ] No commented-out ACGME validation
- [ ] No placeholder/dummy data in production code
- [ ] All schedule modifications validated
- [ ] Backup created before destructive operations
- [ ] No sensitive data in logs or error messages

### Quality

- [ ] All tests passing (`pytest`, `npm test`)
- [ ] Linter warnings fixed (`ruff check .`, `npm run lint`)
- [ ] No hardcoded values (use config/env vars)
- [ ] No duplicated code (extract common logic)
- [ ] Error handling added with descriptive messages

### Process

- [ ] On feature branch (not `main`)
- [ ] No force pushes to main
- [ ] PR created (not directly merged)
- [ ] Migration created for model changes
- [ ] CI checks passing

### Communication

- [ ] Commit message descriptive (what, why)
- [ ] No assumptions (explicitly state what changed)
- [ ] No made-up data (query before answering)
- [ ] Errors surfaced to user
- [ ] Scope appropriate (no unnecessary changes)

---

## When You Catch Yourself

If you realize you're about to commit an anti-pattern:

1. **Stop immediately**
2. **Loop back to appropriate phase** (Research/Plan/Execute)
3. **Fix the root cause**, not just the symptom
4. **Document the learning** (add to this file if new)

---

## Contributing New Anti-Patterns

If you discover a new anti-pattern:

```markdown
### ❌ AP-X0N: [Name of Anti-Pattern]

**What It Looks Like:**

```code
# Example of the anti-pattern
```

**Why It's Bad:**

- Reason 1
- Reason 2

**Correct Approach:**

```code
# Example of the correct way
```

**Detection:** How to identify this anti-pattern
```

Then submit as PR update to this file.

---

**Remember:** Anti-patterns are learning opportunities. Every mistake is a chance to improve the framework for future work.
