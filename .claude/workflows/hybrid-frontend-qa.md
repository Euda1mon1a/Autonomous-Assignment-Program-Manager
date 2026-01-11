# Hybrid Frontend QA Workflow

> **Purpose:** Define when to use ASTRONAUT (AI exploratory) vs Playwright (deterministic E2E)
> **Version:** 1.0.0
> **Last Updated:** 2026-01-10

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND QA LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DEVELOPMENT          STABILIZATION           MAINTENANCE                 │
│   ────────────         ─────────────           ───────────                 │
│                                                                             │
│   ASTRONAUT            Playwright              Both                        │
│   explores             locks it down           monitors                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Philosophy:** ASTRONAUT finds issues that don't have tests yet. Playwright ensures those issues never return.

---

## Phase 1: Feature Development (ASTRONAUT-First)

**Trigger:** New feature branch created

**Why ASTRONAUT:** No test script exists yet. Adaptive exploration finds issues Playwright can't test for because you haven't written the test.

### Mission Template

Use `.claude/Missions/MISSION_EXPLORATION.md`

### Expected Outputs

- Screenshots of each state
- Console error log
- UX friction points identified
- Suggested test cases for Playwright
- Happy path documented

### Invocation

```markdown
## MISSION: Feature Exploration

**Target:** /admin/new-feature
**Objective:** Navigate to the new feature, interact with all controls,
report console errors, broken layouts, and document the happy path.

**Deliverables:**
- Screenshots of each state
- Console error log
- UX friction points
- Suggested Playwright test cases
```

---

## Phase 2: Stabilization (Convert to Playwright)

**Trigger:** Feature complete, ASTRONAUT validates it works

**Why Playwright:** Fast, free, deterministic. Runs in seconds, catches regressions.

### Workflow

1. **Use Playwright codegen to bootstrap:**
   ```bash
   npx playwright codegen http://localhost:3000/admin/new-feature
   ```

2. **Refine into a proper spec file:**
   ```typescript
   // e2e/tests/new-feature.spec.ts
   test('admin can configure new feature', async ({ page }) => {
     await page.goto('/admin/new-feature');
     await page.fill('#setting-name', 'Test Config');
     await page.click('button:has-text("Save")');
     await expect(page.locator('.toast-success')).toBeVisible();
   });
   ```

3. **Add to CI pipeline** (runs on every push)

### Organization

```
frontend/e2e/
├── tests/
│   ├── auth/           # Authentication flows
│   ├── schedule/       # Schedule management
│   ├── admin/          # Admin panel features
│   └── [new-feature]/  # New feature tests
├── pages/              # Page Object Models
└── fixtures/           # Test data and setup
```

---

## Phase 3: CI/CD Gate (Playwright Only)

**Trigger:** Every commit to feature branch

**Why Playwright:** Must be fast and deterministic. ASTRONAUT would be too slow/expensive for every commit.

### CI Configuration

```yaml
# .github/workflows/frontend-tests.yml
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - run: npx playwright test --project=chromium
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

### Quality Gates

- All tests must pass before merge
- Screenshots on failure uploaded as artifacts
- Trace recording on first retry

---

## Phase 4: Periodic Deep Audits (ASTRONAUT Sweeps)

**Trigger:** Weekly or pre-release

**Why ASTRONAUT:** Catches drift, new edge cases, visual regressions. Playwright tests pass but UX degrades? ASTRONAUT catches it.

### Mission Template

Use `.claude/Missions/MISSION_AUDIT.md`

### Routes to Verify

```markdown
## Full GUI Audit Routes

Core:
- /dashboard
- /schedule
- /my-schedule

Admin:
- /admin/users
- /admin/people
- /admin/templates
- /admin/scheduling

Features:
- /swaps
- /conflicts
- /compliance
- /resilience
- /heatmap
- /call-roster
```

### Checklist Per Route

1. Check page loads without crash
2. Log all console errors
3. Test primary user action
4. Screenshot final state
5. Rate UX 1-5

---

## Phase 5: Bug Triage (ASTRONAUT Investigation)

**Trigger:** Bug reported

**Why ASTRONAUT:** Can reason about unexpected states, describe what went wrong, suggest fixes. Playwright just says "test failed."

### Mission Template

Use `.claude/Missions/MISSION_BUG_INVESTIGATION.md`

### Example Mission

```markdown
## MISSION: Reproduce Bug #427

**Title:** Schedule grid freezes on Block 10

**Steps to Reproduce:**
1. Login as admin
2. Navigate to /schedule
3. Set date range to Block 10 (Jan 6 - Feb 16)
4. Observe behavior

**Expected:** Grid renders correctly
**Actual:** Grid freezes

**Objectives:**
1. Reproduce the issue
2. Check console for errors
3. Identify root cause
4. Suggest fix
```

---

## Phase 6: Post-Fix Validation (ASTRONAUT Quick Check)

**Trigger:** Hotfix merged

**Why ASTRONAUT:** One-off validation, no need to update Playwright suite for every hotfix.

### Mission Template

Use `.claude/Missions/MISSION_VALIDATION.md`

### Example Mission

```markdown
## MISSION: Verify Fix for Bug #427

**Objective:** Confirm schedule grid loads correctly for Block 10

**Steps:**
1. Navigate to /schedule with Block 10 dates
2. Confirm grid loads
3. Screenshot the working state
4. Mark MISSION_COMPLETE
```

---

## Tool Selection Cheat Sheet

| Scenario | Playwright | ASTRONAUT | Notes |
|----------|:----------:|:---------:|-------|
| New feature exploration | | ✅ | No script exists yet |
| Encode stable happy path | ✅ | | After ASTRONAUT validates |
| Every-commit CI gate | ✅ | | Must be fast, deterministic |
| Visual/UX audit | | ✅ | Human-level reasoning |
| Bug investigation | | ✅ | Adaptive diagnosis |
| Quick validation | | ✅ | One-off, no script needed |
| Performance benchmarking | ✅ | | Consistent measurements |
| Accessibility testing | ✅ | | axe-core integration |
| Mobile viewport testing | Both | Both | Playwright for CI, ASTRONAUT for UX |

---

## Workflow Cadence

| Trigger | Tool | Action |
|---------|------|--------|
| New feature branch | ASTRONAUT | Explore, document, find issues |
| Feature complete | Playwright codegen | Encode happy path as tests |
| Every commit | Playwright CI | Regression gate |
| Weekly / Pre-release | ASTRONAUT sweep | Full GUI audit |
| Bug reported | ASTRONAUT | Investigate & document |
| Hotfix merged | ASTRONAUT | Quick validation |
| Quarterly | Review | Prune stale Playwright tests, add new coverage |

---

## Expected Outcomes

- **Playwright:** Catches 80% of regressions automatically, sub-minute feedback
- **ASTRONAUT:** Catches the 20% Playwright misses (UX drift, edge cases, visual bugs)
- **Combined:** Full-spectrum coverage from fast CI gates to intelligent exploration

---

## Related Resources

| Resource | Location |
|----------|----------|
| ASTRONAUT Skill | `.claude/skills/astronaut/SKILL.md` |
| Playwright Workflow | `.claude/skills/playwright-workflow/SKILL.md` |
| GUI Development | `.claude/workflows/gui-development.md` |
| Mission Templates | `.claude/Missions/MISSION_*.md` |
| Playwright Config | `frontend/playwright.config.ts` |
| E2E Tests | `frontend/e2e/` |

---

## Decision Tree

```
New Work Arrives
    |
    ├─ Is it a new feature? ──YES──> ASTRONAUT exploration first
    |                         |
    |                         └─> Then Playwright to lock it down
    |
    ├─ Is it a bug report? ──YES──> ASTRONAUT investigation
    |                         |
    |                         └─> Add Playwright test to prevent regression
    |
    ├─ Is it a hotfix? ──YES──> ASTRONAUT quick validation
    |
    ├─ Is it pre-release? ──YES──> ASTRONAUT full audit
    |
    └─ Is it a commit? ──YES──> Playwright CI gate only
```

---

*Hybrid QA: Let AI explore the unknown. Let automation guard the known.*
