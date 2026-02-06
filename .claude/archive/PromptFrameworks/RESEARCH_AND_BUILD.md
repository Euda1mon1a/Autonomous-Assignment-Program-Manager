# Research and Build Framework

> **Purpose:** Standard 5-phase workflow for building features, fixing bugs, and refactoring in the Residency Scheduler
> **Applies To:** Any task requiring code changes, database migrations, or architectural decisions

---

## Overview

This framework prevents **premature implementation** by enforcing a structured workflow:

```
Research → Plan → Execute → Verify → Reflect
```

**Key Principle:** Each phase must complete before moving to the next. If you discover new information in a later phase that invalidates earlier work, **loop back** to the appropriate phase.

---

## Phase 1: Research

**Goal:** Understand the problem, context, and constraints **before** planning a solution.

### Checklist

- [ ] **Understand the request fully**
  - What is the user asking for?
  - Why do they need this?
  - What are the success criteria?

- [ ] **Identify affected systems**
  - Which backend services are involved?
  - Which database models/tables?
  - Which frontend components?
  - Which external systems (Celery, Redis, MCP tools)?

- [ ] **Find relevant documentation**
  - Check `docs/architecture/` for system design
  - Review `CLAUDE.md` for patterns and constraints
  - Read API documentation for related endpoints
  - Search for ADRs (Architecture Decision Records)

- [ ] **Check for existing patterns**
  - Search codebase for similar features (`Grep` tool)
  - Review tests to understand expected behavior
  - Identify reusable components or services

- [ ] **Validate constraints**
  - Does this affect ACGME compliance?
  - Are there security implications (HIPAA, PERSEC, OPSEC)?
  - Will this require a database migration?
  - Are there performance considerations?

### Research Techniques

#### 1. Codebase Archaeology

```bash
# Find all swap-related code
Grep: pattern="swap" glob="**/*.py" output_mode="files_with_matches"

# Understand ACGME validation
Read: /home/user/.../backend/app/scheduling/acgme_validator.py

# Check existing tests for behavior
Glob: pattern="**/test_swap*.py"
```

#### 2. Dependency Mapping

Create a mental (or written) map:

```
User Request: "Implement auto-swap matcher"
    ↓
Affected Systems:
  - backend/app/services/swap_matcher.py (NEW)
  - backend/app/models/swap.py (MODIFY)
  - backend/app/api/routes/swaps.py (MODIFY)
  - frontend/app/swaps/page.tsx (MODIFY)
  - Database: swaps table (MIGRATE)
```

#### 3. Constraint Discovery

Ask yourself:

- **ACGME:** Do swaps need to maintain 80-hour rule compliance?
- **Security:** Can residents see other residents' swap requests?
- **Resilience:** Does this affect N-1 contingency staffing?
- **Data Integrity:** What happens if a swap is approved while a rotation is deleted?

### Example: Research Phase for Auto-Swap Matcher

```markdown
## Research Notes: Auto-Swap Matcher

### User Request
Implement automatic matching of compatible swap partners when a faculty member requests to give away a shift.

### Affected Systems
- **Backend:**
  - `backend/app/services/swap_matcher.py` (NEW)
  - `backend/app/services/swap_executor.py` (MODIFY - integration)
  - `backend/app/models/swap.py` (MODIFY - add matcher metadata)
- **Database:**
  - `swaps` table: Add `match_score`, `auto_matched` columns
- **API:**
  - `POST /swaps/{id}/find-matches` (NEW)
- **Frontend:**
  - Swap request form: Add "Auto-match" button

### Existing Patterns Found
- `backend/app/services/conflict_detector.py` has overlap detection logic (REUSE)
- Tests in `tests/test_swap_executor.py` show validation requirements (REFERENCE)
- `backend/app/scheduling/availability.py` has availability checking (REUSE)

### Constraints Identified
- ✅ ACGME: Swaps must maintain 80-hour rule for both parties
- ✅ Security: Only show matches to the requesting faculty member
- ✅ Resilience: Auto-match must not create N-1 violations
- ⚠️  Performance: Matching algorithm must run <2 seconds for 50 faculty

### Questions to Resolve
1. Should we allow cross-rotation swaps?
2. What's the scoring algorithm? (Preference rank, seniority, past swap history?)
3. Do we notify all matches or only the top-ranked?

### Documentation to Reference
- `docs/architecture/swap-workflow.md`
- `docs/api/swaps.md`
- ACGME 80-hour rule: `backend/app/scheduling/acgme_validator.py`
```

---

## Phase 2: Plan

**Goal:** Design the solution with enough detail to execute confidently, but not so much that you're pre-coding.

### Checklist

- [ ] **Break down into tasks**
  - List all components to create/modify
  - Identify dependencies (what must happen first?)
  - Estimate complexity (simple, moderate, complex)

- [ ] **Define interfaces**
  - API endpoint signatures
  - Function signatures for new services
  - Database schema changes
  - Pydantic schemas (request/response)

- [ ] **Identify risks and mitigations**
  - What could go wrong?
  - How will you handle edge cases?
  - What's the rollback plan?

- [ ] **Define success criteria**
  - What tests must pass?
  - What metrics should improve?
  - What documentation must be updated?

- [ ] **Choose implementation approach**
  - Algorithm selection
  - Libraries to use
  - Design patterns to apply

### Planning Techniques

#### 1. Task Breakdown with Dependencies

Use `TodoWrite` to create a structured task list:

```markdown
1. Create database migration for swap matcher fields (BLOCKING)
2. Implement SwapMatcher service (DEPENDS ON 1)
3. Add API endpoint for find-matches (DEPENDS ON 2)
4. Write unit tests for matcher logic (PARALLEL WITH 2)
5. Add integration tests for API endpoint (DEPENDS ON 3)
6. Update frontend swap form (DEPENDS ON 3)
7. Update documentation (DEPENDS ON ALL)
```

#### 2. Interface Design

Define signatures **before** implementing:

```python
# backend/app/services/swap_matcher.py
class SwapMatcher:
    """Auto-match compatible swap partners."""

    async def find_matches(
        self,
        db: AsyncSession,
        swap_request_id: str,
        max_matches: int = 5
    ) -> list[SwapMatch]:
        """
        Find compatible swap partners for a request.

        Args:
            db: Database session
            swap_request_id: ID of swap request to match
            max_matches: Maximum number of matches to return

        Returns:
            List of SwapMatch objects, sorted by score (descending)

        Raises:
            SwapNotFoundError: If swap request doesn't exist
            ACGMEViolationError: If no matches maintain compliance
        """
        pass  # Implementation in Execute phase
```

#### 3. Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Matching algorithm too slow | Medium | High | Add indexes on person_id, date; limit search window |
| Cross-timezone conflicts | Low | Medium | Convert all dates to UTC in matcher |
| Race condition (two people swap same slot) | Medium | High | Use database row locking (`with_for_update()`) |

#### 4. Migration Planning

```bash
# Alembic migration plan
alembic revision --autogenerate -m "Add swap matcher fields"

# New columns:
# - swaps.match_score (Float, nullable)
# - swaps.auto_matched (Boolean, default False)
# - swaps.matcher_version (String, for A/B testing)

# Indexes to add:
# - ix_swaps_auto_matched (for filtering)
# - ix_swaps_match_score (for ranking)
```

### Example: Plan for Auto-Swap Matcher

```markdown
## Implementation Plan: Auto-Swap Matcher

### Task Breakdown
1. **Database Migration** (15 min, BLOCKING)
   - Add `match_score`, `auto_matched`, `matcher_version` to `swaps` table
   - Create indexes for query performance

2. **SwapMatcher Service** (2 hours, DEPENDS ON 1)
   - Implement `find_matches()` algorithm
   - Use conflict detector for overlap checking
   - Integrate ACGME validator for compliance
   - Score by: (1) rotation match, (2) seniority, (3) past swap history

3. **API Endpoint** (30 min, DEPENDS ON 2)
   - `POST /swaps/{id}/find-matches`
   - Request: `FindMatchesRequest(max_matches=5)`
   - Response: `list[SwapMatchResponse]`

4. **Testing** (1.5 hours, PARALLEL WITH 2-3)
   - Unit: SwapMatcher logic (12 test cases)
   - Integration: API endpoint (5 scenarios)
   - ACGME compliance tests (4 violation scenarios)

5. **Frontend** (1 hour, DEPENDS ON 3)
   - Add "Find Matches" button to swap form
   - Display match results with scores
   - Allow user to select top match

6. **Documentation** (30 min, DEPENDS ON ALL)
   - Update `docs/api/swaps.md`
   - Add docstrings to new functions
   - Update `CHANGELOG.md`

### Total Estimated Time: 5.5 hours

### Success Criteria
- ✅ All unit tests pass (100% coverage on new code)
- ✅ Integration tests pass
- ✅ No ACGME violations in test scenarios
- ✅ API responds <2s for 50 faculty search
- ✅ Frontend displays matches correctly
- ✅ Documentation updated

### Rollback Plan
If matcher causes issues:
1. Feature flag: `ENABLE_AUTO_MATCHER=false` in env
2. Revert migration if breaking (unlikely)
3. Fallback to manual swap selection
```

---

## Phase 3: Execute

**Goal:** Implement the plan incrementally, testing after each step.

### Checklist

- [ ] **Implement incrementally**
  - Start with blocking tasks (migrations, models)
  - Build layer by layer (model → service → API → frontend)
  - Test each layer before moving to the next

- [ ] **Test after each step**
  - Run unit tests continuously
  - Verify integration points
  - Check for regressions

- [ ] **Document decisions**
  - Add docstrings to all new functions
  - Comment non-obvious logic
  - Update API documentation

- [ ] **Create checkpoints**
  - Commit working increments
  - Use meaningful commit messages
  - Tag points where you can safely roll back

### Execution Techniques

#### 1. Layered Implementation

Follow the architecture layers bottom-up:

```
1. Database (migrations, models)
   ↓
2. Service layer (business logic)
   ↓
3. API layer (routes, schemas)
   ↓
4. Frontend (components, pages)
```

**Example order for auto-swap matcher:**

```bash
# Step 1: Database
alembic revision --autogenerate -m "Add swap matcher fields"
alembic upgrade head
pytest tests/test_migrations.py  # Verify migration works

# Step 2: Service layer
# Write SwapMatcher.find_matches()
pytest tests/test_swap_matcher.py  # Test matching logic

# Step 3: API layer
# Add POST /swaps/{id}/find-matches endpoint
pytest tests/test_swaps_api.py::test_find_matches  # Test API

# Step 4: Frontend (parallel if backend is stable)
# Add "Find Matches" button
npm test -- swaps.test.tsx  # Test component
```

#### 2. Test-Driven Development (TDD)

For critical logic, write tests **before** implementation:

```python
# tests/test_swap_matcher.py - Write FIRST
async def test_find_matches_returns_compatible_partners():
    """Matcher should return only ACGME-compliant matches."""
    # Arrange
    swap_request = await create_swap_request(person="FAC-01", date="2024-01-15")
    await create_potential_match(person="FAC-02", available=True, compliant=True)
    await create_potential_match(person="FAC-03", available=True, compliant=False)

    # Act
    matcher = SwapMatcher()
    matches = await matcher.find_matches(db, swap_request.id)

    # Assert
    assert len(matches) == 1
    assert matches[0].person_id == "FAC-02"

# backend/app/services/swap_matcher.py - Implement SECOND
async def find_matches(self, db, swap_request_id):
    # Implementation that makes test pass
    pass
```

#### 3. Incremental Commits

```bash
# Commit 1: Migration
git add backend/alembic/versions/xxx_add_swap_matcher_fields.py
git commit -m "feat: Add swap matcher database fields

- Add match_score, auto_matched, matcher_version to swaps
- Add indexes for query performance"

# Commit 2: Service
git add backend/app/services/swap_matcher.py
git add tests/test_swap_matcher.py
git commit -m "feat: Implement SwapMatcher service

- Find compatible swap partners
- Score by rotation match, seniority, swap history
- Validate ACGME compliance for all matches"

# Commit 3: API
git add backend/app/api/routes/swaps.py
git add tests/test_swaps_api.py
git commit -m "feat: Add find-matches API endpoint

- POST /swaps/{id}/find-matches
- Returns top N matches sorted by score"
```

#### 4. Handle Roadblocks

If you encounter an unexpected issue:

1. **Document it:** Add a comment or note
2. **Assess impact:** Does this invalidate the plan?
3. **Loop back if needed:** Return to Research or Plan phase
4. **Don't hack around it:** Fix the root cause

**Example:**

```python
# If you discover a missing index during implementation:
# DON'T: Work around it with inefficient query
# DO: Loop back to Plan phase, add migration for index

# Create new migration
alembic revision -m "Add index on assignments.person_id for swap matcher"
```

### Example: Execution Log for Auto-Swap Matcher

```markdown
## Execution Log

### Step 1: Database Migration (15 min)
- ✅ Created migration `add_swap_matcher_fields`
- ✅ Added columns: match_score, auto_matched, matcher_version
- ✅ Added indexes: ix_swaps_auto_matched, ix_swaps_match_score
- ✅ Tested migration: `alembic upgrade head` succeeded
- ✅ Verified rollback: `alembic downgrade -1` succeeded
- 📝 Commit: `feat: Add swap matcher database fields`

### Step 2: SwapMatcher Service (2.5 hours - took longer than estimated)
- ✅ Implemented `find_matches()` algorithm
- ✅ Integrated conflict detector for overlap checking
- ✅ Integrated ACGME validator
- ⚠️  **Issue discovered:** Existing conflict detector doesn't handle cross-rotation swaps
  - **Resolution:** Added `allow_cross_rotation` parameter to conflict detector
  - **Impact:** Added 30 min to estimate
- ✅ Implemented scoring algorithm
- ✅ Added 12 unit tests (100% coverage)
- ✅ All tests pass
- 📝 Commit: `feat: Implement SwapMatcher service`

### Step 3: API Endpoint (30 min)
- ✅ Created `POST /swaps/{id}/find-matches` endpoint
- ✅ Defined Pydantic schemas: `FindMatchesRequest`, `SwapMatchResponse`
- ✅ Added rate limiting (max 10 requests/min per user)
- ✅ Added 5 integration tests
- ✅ All tests pass
- 📝 Commit: `feat: Add find-matches API endpoint`

### Step 4: Frontend (skipped for now)
- ⏸️  Paused - waiting for backend to stabilize in staging
- Will implement in separate PR

### Step 5: Documentation (30 min)
- ✅ Updated `docs/api/swaps.md` with new endpoint
- ✅ Added docstrings to all functions
- ✅ Updated `CHANGELOG.md`
- 📝 Commit: `docs: Document swap matcher feature`
```

---

## Phase 4: Verify

**Goal:** Ensure the implementation meets all success criteria and doesn't break anything.

### Checklist

- [ ] **Run all tests**
  - Unit tests: `pytest backend/tests/`
  - Integration tests: `pytest backend/tests/integration/`
  - Frontend tests: `npm test`
  - E2E tests (if applicable): `npm run test:e2e`

- [ ] **Check compliance**
  - ACGME compliance tests: `pytest -m acgme`
  - Security audit (if touching auth/data): Review with `security-audit` skill
  - Performance benchmarks (if critical path): Load tests

- [ ] **Review changes**
  - Self-review: Read your own diff
  - Check for code smells (duplication, long functions, missing types)
  - Verify error handling (no sensitive data leaks)
  - Confirm logging is appropriate

- [ ] **Update documentation**
  - API docs updated?
  - User guide updated?
  - CHANGELOG.md entry?
  - Inline comments for complex logic?

- [ ] **Verify no regressions**
  - Do existing features still work?
  - Did you break any existing tests?
  - Check related functionality manually

### Verification Techniques

#### 1. Comprehensive Test Run

```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing
# Verify coverage >= 80% for new code

# Frontend
cd frontend
npm run test:coverage
# Verify no uncovered branches in new components

# Linting
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint

# Type checking
cd frontend && npm run type-check
```

#### 2. ACGME Compliance Verification

```bash
# Run ACGME-specific tests
pytest -m acgme -v

# Check for violations in test scenarios
pytest tests/test_acgme_validator.py::test_swap_maintains_80_hour_rule
```

#### 3. Security Review Checklist

- [ ] No hardcoded secrets
- [ ] Input validation with Pydantic
- [ ] No SQL injection vectors (using ORM only)
- [ ] No sensitive data in error messages
- [ ] No sensitive data in logs
- [ ] Proper authorization checks (user can only see their own data)
- [ ] Rate limiting on new endpoints

#### 4. Performance Verification

```bash
# If the feature is performance-critical:
pytest tests/performance/test_swap_matcher_performance.py

# Expected: find_matches() < 2 seconds for 50 faculty
```

#### 5. Manual Testing Checklist

For user-facing features:

- [ ] Test happy path (feature works as expected)
- [ ] Test error conditions (invalid input, missing data)
- [ ] Test edge cases (empty results, maximum results)
- [ ] Test concurrent usage (if applicable)
- [ ] Test rollback scenarios (undo, cancel)

### Example: Verification Checklist for Auto-Swap Matcher

```markdown
## Verification Checklist

### Automated Tests
- ✅ Unit tests: 12/12 passing (100% coverage)
- ✅ Integration tests: 5/5 passing
- ✅ ACGME tests: 4/4 passing
- ✅ Performance test: find_matches() avg 1.2s (target: <2s) ✅

### Code Quality
- ✅ Linting: No issues (ruff)
- ✅ Type checking: No issues (mypy)
- ✅ Coverage: 98% (target: >=80%) ✅

### Security
- ✅ No hardcoded secrets
- ✅ Pydantic validation on all inputs
- ✅ Rate limiting: 10 req/min per user
- ✅ Authorization: Users can only see matches for their own requests
- ✅ No sensitive data in logs

### Compliance
- ✅ Swaps maintain 80-hour rule for both parties
- ✅ No N-1 contingency violations
- ✅ Audit trail: All matches logged

### Documentation
- ✅ API documentation updated (`docs/api/swaps.md`)
- ✅ Docstrings added to all functions
- ✅ CHANGELOG.md updated
- ✅ Inline comments for scoring algorithm

### Regression Testing
- ✅ Existing swap executor still works
- ✅ Manual swap creation unaffected
- ✅ Swap approval workflow unchanged
- ✅ All existing swap tests pass

### Manual Testing
- ✅ Happy path: Finds 5 compatible matches
- ✅ No matches found: Returns empty list with helpful message
- ✅ Invalid swap ID: Returns 404
- ✅ Cross-rotation swap: Correctly validates
- ✅ Concurrent requests: No race conditions observed
```

---

## Phase 5: Reflect

**Goal:** Capture learnings to improve future work and update frameworks.

### Checklist

- [ ] **What worked well?**
  - Which techniques were effective?
  - What helped you move quickly?
  - What would you repeat?

- [ ] **What could improve?**
  - Where did you get stuck?
  - What took longer than expected?
  - What would you do differently?

- [ ] **Capture learnings**
  - Document new patterns in `.claude/Scratchpad/`
  - Update frameworks if you discovered a better approach
  - Share insights with team (if human collaboration)

- [ ] **Update estimates**
  - How accurate were your time estimates?
  - Adjust future estimates based on actual time

### Reflection Techniques

#### 1. Structured Reflection Template

```markdown
## Reflection: Auto-Swap Matcher Implementation

### What Worked Well
- ✅ **TDD approach:** Writing tests first helped clarify requirements
- ✅ **Incremental commits:** Easy to trace progress and rollback if needed
- ✅ **Reusing conflict detector:** Saved 1 hour of implementation time
- ✅ **Clear plan:** Having task breakdown prevented scope creep

### What Could Improve
- ⚠️  **Estimate accuracy:** Service layer took 2.5h vs estimated 2h
  - **Why:** Didn't account for cross-rotation swap edge case
  - **Next time:** Add 20% buffer for "unknown unknowns"
- ⚠️  **Documentation delay:** Should have updated docs incrementally, not at end
  - **Next time:** Update docs immediately after each component

### Learnings
- 📚 **New pattern discovered:** Cross-rotation validation is reusable
  - Consider extracting to `CrossRotationValidator` service
- 📚 **Performance insight:** Indexes on `person_id + date` critical for matching speed
  - Document in `docs/architecture/database-optimization.md`

### Framework Updates
- ➕ **Add to ANTI_PATTERNS.md:** "Don't defer documentation until end"
- ➕ **Add to COMPLEX_TASK_DECOMPOSITION.md:** "Always add 20% buffer for unknowns"

### Actual vs Estimated Time
| Task | Estimated | Actual | Variance |
|------|-----------|--------|----------|
| Database Migration | 15 min | 15 min | 0% |
| SwapMatcher Service | 2 hours | 2.5 hours | +25% |
| API Endpoint | 30 min | 30 min | 0% |
| Testing | 1.5 hours | 1.5 hours | 0% |
| Documentation | 30 min | 30 min | 0% |
| **Total** | **5.5 hours** | **6 hours** | **+9%** |
```

#### 2. Pattern Extraction

If you discover a reusable pattern, document it:

```markdown
## New Pattern: Cross-Rotation Swap Validation

### Problem
Swaps can occur within same rotation or across rotations, but validation differs.

### Solution
Created `allow_cross_rotation` parameter in conflict detector:

```python
def detect_conflicts(
    assignments: list[Assignment],
    allow_cross_rotation: bool = False
) -> list[Conflict]:
    if allow_cross_rotation:
        # Only check time overlap, not rotation match
        conflicts = check_time_overlap(assignments)
    else:
        # Check both time and rotation
        conflicts = check_time_and_rotation_overlap(assignments)
    return conflicts
```

### When to Use
- Swap matching: `allow_cross_rotation=True`
- Regular assignment: `allow_cross_rotation=False`

### Where to Reuse
- N-1 contingency planning (might allow cross-rotation coverage)
- Emergency coverage (definitely needs cross-rotation flexibility)
```

#### 3. Anti-Pattern Discovery

If you made a mistake, add it to `ANTI_PATTERNS.md`:

```markdown
## Anti-Pattern: Deferring Documentation Until End

### What Happened
I updated API documentation after implementing all code, which meant:
- Documentation didn't match intermediate states (confusion)
- Had to context-switch back to "remember" what each endpoint does
- Risk of forgetting to document something

### Why It's Bad
- Documentation is most accurate when written alongside code
- Deferring creates cognitive overhead
- Increases risk of outdated/incomplete docs

### Correct Approach
Update documentation immediately after each component:
1. Implement API endpoint → Update `docs/api/` immediately
2. Add service method → Update docstrings immediately
3. Create database migration → Update schema docs immediately

### Detection
If you find yourself thinking "I'll document this later," stop and document now.
```

---

## Quick Reference: 5-Phase Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 1: RESEARCH                                                   │
│ ✓ Understand request, context, constraints                          │
│ ✓ Find existing patterns, documentation                             │
│ ✓ Identify affected systems                                         │
│ → Output: Research notes, constraint list                           │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 2: PLAN                                                       │
│ ✓ Break down into tasks with dependencies                           │
│ ✓ Define interfaces (APIs, functions, schemas)                      │
│ ✓ Identify risks and mitigations                                    │
│ → Output: Implementation plan, task breakdown                       │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 3: EXECUTE                                                    │
│ ✓ Implement incrementally (model → service → API → frontend)        │
│ ✓ Test after each step                                              │
│ ✓ Commit working increments                                         │
│ → Output: Working code, passing tests, commits                      │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 4: VERIFY                                                     │
│ ✓ Run all tests (unit, integration, ACGME, performance)             │
│ ✓ Check compliance, security, documentation                         │
│ ✓ Verify no regressions                                             │
│ → Output: Verified, tested, documented feature                      │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 5: REFLECT                                                    │
│ ✓ What worked well? What could improve?                             │
│ ✓ Capture learnings, update frameworks                              │
│ ✓ Adjust future estimates                                           │
│ → Output: Reflection notes, framework updates                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## When to Loop Back

If you discover:

- **New constraints in Execute phase** → Loop back to Plan (or Research if fundamental)
- **Missing information in Plan phase** → Loop back to Research
- **Test failures in Verify phase** → Loop back to Execute (or Plan if design issue)
- **Better approach in Reflect phase** → Document for next feature, don't refactor now

---

**Remember:** The goal is not to be rigid, but to **think before acting** and **reflect after completing**. Use this framework as a guide, not a straitjacket.
